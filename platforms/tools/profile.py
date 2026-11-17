#!/usr/bin/env python3
"""The project profile resolver (KIT-087 P1): one resolved view of a project's kit parameters.

Usage: profile.py resolve [--section S] [--json] [--file F] [ROOT]

A project keeps its kit parameters in `.ai-kit.yaml` at its git top level, validated by
platforms/ci/schemas/profile.schema.json: every key has a default and one reader phase (`x-read-by`), an unknown key
fails, and an `x-<name>` key at the top level or directly in a section is the project's own and is ignored. Only the
kit's skills, hooks, sync-project.sh and the spec-tools action call this tool; a project never does.

Kind presets (KIT-088): `project.kind` (business, game, tooling; default business) is a preset of defaults that no
skill reads. A key resolves to the value the project sets in `.ai-kit.yaml`, else the value the kind's preset gives
(the schema's `project.kind` `x-presets`), else its schema default.

One home (KIT-087 P4): `.ai-kit.yaml` is the only source. The legacy homes of kit 16 and earlier (the `sdd:` block
of spec.md, the profile list of the CLAUDE.md sync marker, the gates JSON `sdd.row_checks.gates` names as a source
of `gates`, and the aliases `sdd.review_rounds` and `sdd.visual_approval`) are no longer read; check_spec.py fails
on an `sdd:` block left in spec.md. A missing `.ai-kit.yaml` prints one warning line and resolves every key to its
preset or default. `kit: ">=X.Y"` fails on an older kit.

resolve prints the resolved view (`--section` one section) as YAML in the subset check_spec.py's fallback parser
reads, or as JSON with `--json`; ROOT defaults to the current folder, and its git top level is used. `--file` names
the profile file relative to ROOT (default `.ai-kit.yaml`) and must stay under it, links resolved. `spec_root` must
also resolve under the root.

Exit 0 on success, 1 on an invalid profile, 2 on a usage error. Standard library only
and Python 3.9 compatible: hooks and sync-project.sh run the system python3. The YAML parser and the schema checks
are check_spec.py's (pyyaml when it is installed with jsonschema, else its fallback parser), loaded from beside it.
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
VALIDATIONS = KIT / "platforms" / "ci" / "validations"
SCHEMAS = KIT / "platforms" / "ci" / "schemas"
FILE = ".ai-kit.yaml"
SPEC_DIR = Path("docs") / "spec"
PLAIN_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")
USAGE = "usage: profile.py resolve [--section S] [--json] [--file F] [ROOT]"


def check_spec():
    """check_spec.py as a module: the copy already loaded (check_spec.py --params registers itself), else the file
    beside the validators."""
    module = sys.modules.get("check_spec")
    if module is None:
        spec = importlib.util.spec_from_file_location("check_spec", VALIDATIONS / "check_spec.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules["check_spec"] = module
        spec.loader.exec_module(module)
    return module


def private(key) -> bool:
    return isinstance(key, str) and key.startswith("x-")


def default_of(rule):
    if "default" in rule:
        return json.loads(json.dumps(rule["default"]))
    if "properties" in rule:
        return {key: default_of(prop) for key, prop in rule["properties"].items()}
    return None


def fill(rule, value):
    """A key's value with the defaults of an object's absent sub-keys filled one level deep, as check_spec.py's sdd
    block always was."""
    default = default_of(rule)
    if "properties" in rule and isinstance(value, dict) and isinstance(default, dict):
        return {**default, **{k: v for k, v in value.items() if not private(k)}}
    return value


def resolve_map(rule, given, journeys_dir=None, preset=None):
    """A section resolved: every schema key at its given value, else its kind preset (KIT-088), else its default,
    then the free keys (a map section's entries) as given; x- keys dropped."""
    out, preset = {}, preset or {}
    for key, prop in rule.get("properties", {}).items():
        if key in given:
            value = fill(prop, given[key])
        elif key in preset:
            value = fill(prop, json.loads(json.dumps(preset[key])))
        else:
            value = default_of(prop)
        if key == "journeys" and value is None:
            value = journeys_dir is not None and journeys_dir.is_dir()
        out[key] = value
    for key, value in given.items():
        if key not in out and not private(key):
            out[key] = value
    return out


def shown(path, root):
    if root is not None:
        try:
            return Path(path).resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            pass
    return str(path)


class Resolver:
    """One resolution: the values, the stderr notes and the errors. check_value's failures land in check_spec.py's
    failure list, which `checked` moves into this resolver's errors."""

    def __init__(self, root, spec_dir=None, schemas_dir=None, profile_file=FILE):
        self.cs = check_spec()
        self.root = root
        self.spec_dir_given = spec_dir is not None
        self.spec_dir = spec_dir if spec_dir is not None else (root / SPEC_DIR if root is not None else None)
        self.schemas = schemas_dir if schemas_dir is not None else SCHEMAS
        self.schema = json.loads((self.schemas / "profile.schema.json").read_text(encoding="utf-8"))
        self.profile_file = profile_file
        self.notes, self.errors = [], []
        self.new, self.new_path = {}, None

    def checked(self, fn, *args):
        start = len(self.cs.failures)
        result = fn(*args)
        self.errors.extend(msg for _, _, msg, *_ in self.cs.failures[start:])
        del self.cs.failures[start:]
        return result

    # --- the new file
    def read_new(self):
        if self.root is None:
            return
        path = self.root / self.profile_file
        self.new_path = shown(path, self.root)
        if not path.is_file():
            self.notes.append(f"profile: warning: no {self.new_path} at {self.root}; every key takes its default")
            return
        try:
            data = self.cs.load_yaml(path.read_text(encoding="utf-8"))
        except ValueError as e:
            self.errors.append(f"{self.new_path}: invalid YAML ({e})")
            return
        if data is None:
            data = {}
        if not isinstance(data, dict):
            self.errors.append(f"{self.new_path}: the profile must be a map of sections, not {type(data).__name__}")
            return
        props = self.schema["properties"]
        for key, value in data.items():
            key = str(key)
            if private(key):
                continue
            if key not in props:
                self.errors.append(f"{self.new_path}: {key} is not a known key; known: {sorted(props)}")
                continue
            if self.checked(self.cs.check_value, self.new_path, key, value, props[key]):
                self.new[key] = {k: v for k, v in value.items() if not private(k)} if isinstance(value, dict) else value
        if "spec_root" in self.new:
            spec_dir = self.root / self.new["spec_root"]
            try:
                spec_dir.resolve().relative_to(self.root.resolve())
            except ValueError:
                self.errors.append(f"{self.new_path}: spec_root {self.new['spec_root']} resolves outside {self.root}")
                del self.new["spec_root"]
            else:
                if not self.spec_dir_given:
                    self.spec_dir = spec_dir
        self.check_pin()

    def preset(self, section):
        """The values the project's kind presets in a section (KIT-088): {} for business or a section it leaves
        alone. An invalid kind already failed in read_new, so it falls back to the default kind here."""
        rule = self.schema["properties"]["project"]["properties"]["kind"]
        kind = (self.new.get("project") or {}).get("kind", rule["default"])
        return rule.get("x-presets", {}).get(kind, {}).get(section, {})

    def check_pin(self):
        pin = self.new.get("kit")
        if not pin:
            return
        need = tuple(int(n) for n in pin[2:].split("."))
        try:
            have = tuple(int(n) for n in (KIT / "VERSION").read_text(encoding="utf-8").strip().split("-")[0].split("."))
        except (OSError, ValueError):
            return
        if have[:len(need)] < need:
            self.errors.append(f"{self.new_path}: kit {pin} is required, this kit is "
                               f"{'.'.join(str(n) for n in have)}; update the kit (refresh.sh)")

    # --- resolution
    def resolve_section(self, section):
        rule = self.schema["properties"][section]
        if rule.get("type") != "object":  # a top-level scalar: kit, spec_root
            return self.new.get(section, default_of(rule))
        journeys = self.spec_dir / "journeys" if section == "sdd" and self.spec_dir is not None else None
        return resolve_map(rule, self.new.get(section) or {}, journeys, self.preset(section))

    def resolve(self, sections=None):
        self.read_new()
        names = list(self.schema["properties"]) if sections is None else list(sections)
        return {name: self.resolve_section(name) for name in names}

    def defaults(self, section):
        """A section's values when the project sets none of its keys: its kind preset, else the schema defaults."""
        rule = self.schema["properties"][section]
        if rule.get("type") != "object":
            return default_of(rule)
        journeys = self.spec_dir / "journeys" if section == "sdd" and self.spec_dir is not None else None
        return resolve_map(rule, {}, journeys, self.preset(section))


def resolve(root, sections=None, spec_dir=None, schemas_dir=None, profile_file=FILE):
    """(resolved view, notes, errors) for another kit tool; nothing is printed."""
    resolver = Resolver(root, spec_dir, schemas_dir, profile_file)
    resolved = resolver.resolve(sections)
    return resolved, resolver.notes, resolver.errors


# --- the YAML subset writer: block maps, flow lists and maps, quoted strings (check_spec.py's parser reads it)
def quote(text):
    if "\n" in text or "\r" in text:
        raise ValueError(f"a string with a line break cannot be written: {text!r}")
    if "'" not in text:
        return f"'{text}'"
    if '"' not in text and "\\" not in text:
        return f'"{text}"'
    raise ValueError(f"a string with both quote kinds cannot be written: {text!r}")


def key_text(key):
    key = str(key)
    words = {"null", "true", "false", "yes", "no", "on", "off", "y", "n"}
    return key if PLAIN_KEY.match(key) and key.lower() not in words else quote(key)


def flow(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return quote(value)
    if isinstance(value, list):
        return "[" + ", ".join(flow(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{" + ", ".join(f"{key_text(k)}: {flow(v)}" for k, v in value.items()) + "}"
    raise ValueError(f"a value of type {type(value).__name__} cannot be written: {value!r}")


def dump(data, indent=0):
    lines, pad = [], " " * indent
    for key, value in data.items():
        if isinstance(value, dict) and value:
            lines.append(f"{pad}{key_text(key)}:")
            lines.extend(dump(value, indent + 2))
        else:
            lines.append(f"{pad}{key_text(key)}: {flow(value)}")
    return lines


# --- command line
def toplevel(path):
    result = subprocess.run(["git", "-C", str(path), "rev-parse", "--show-toplevel"], capture_output=True, text=True,
                            check=False)
    return Path(result.stdout.strip()) if result.returncode == 0 and result.stdout.strip() else path


def usage():
    print(USAGE, file=sys.stderr)
    raise SystemExit(2)


def parse_args(argv):
    if not argv or argv[0] != "resolve":
        usage()
    opts, args, rest = {"command": argv[0], "section": None, "json": False, "file": FILE}, [], list(argv[1:])
    while rest:
        arg = rest.pop(0)
        if arg == "--json":
            opts["json"] = True
        elif arg in ("--section", "--file") and rest:
            opts[arg[2:]] = rest.pop(0)
        elif arg.startswith("-"):
            usage()
        else:
            args.append(arg)
    if len(args) > 1:
        usage()
    opts["root"] = Path(args[0]) if args else Path.cwd()
    return opts


def report(notes, errors):
    for note in notes:
        print(note, file=sys.stderr)
    for error in errors:
        print(f"FAIL: {error}", file=sys.stderr)


def main(argv=None):
    opts = parse_args(sys.argv[1:] if argv is None else argv)
    if not opts["root"].is_dir():
        print(f"profile: {opts['root']} is not a folder", file=sys.stderr)
        return 2
    root = toplevel(opts["root"])
    try:
        if Path(opts["file"]).is_absolute():
            raise ValueError
        (root / opts["file"]).resolve().relative_to(root.resolve())
    except ValueError:
        print(f"profile: --file must name a file under {root}, not {opts['file']}", file=sys.stderr)
        return 2
    resolver = Resolver(root, profile_file=opts["file"])
    if opts["section"] is not None and opts["section"] not in resolver.schema["properties"]:
        print(f"profile: unknown section {opts['section']!r}; known: {sorted(resolver.schema['properties'])}",
              file=sys.stderr)
        return 2
    sections = [opts["section"]] if opts["section"] else None
    resolved = resolver.resolve(sections)
    report(resolver.notes, resolver.errors)
    if resolver.errors:
        return 1
    if opts["json"]:
        value = resolved[opts["section"]] if opts["section"] else resolved
        print(json.dumps(value, indent=2, sort_keys=True))
    else:
        print("\n".join(dump(resolved)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
