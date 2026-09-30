#!/usr/bin/env python3
"""Valida docs/spec contra os schemas do kit. Uso: check_spec.py <spec-dir> <schemas-dir>

Com pyyaml+jsonschema: validacao completa. Sem eles: parser YAML minimo
(frontmatter plano) + checagem estrutural (required, enums, id pattern).
"""
import re
import sys
from pathlib import Path

try:
    import yaml
    from jsonschema import validate as js_validate
    FULL = True
except ImportError:
    FULL = False

failures = []


def fail(msg):
    failures.append(msg)
    print(f"FALHA: {msg}", file=sys.stderr)


def mini_yaml(text):
    """Parser minimo: 'k: v', 'k: [a,b]', 'k:' + linhas '- item', ints, null, strings com aspas."""
    data, key = {}, None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        m = re.match(r"^-\s+(.*)$", line.strip())
        if m and key is not None:
            data.setdefault(key, []).append(m.group(1).strip().strip('"\''))
            continue
        m = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if not m:
            raise ValueError(f"linha fora do formato: {line!r}")
        key, val = m.group(1), m.group(2).strip()
        if val == "":
            data[key] = []  # pode virar lista ou ficar vazio
        elif val in ("null", "~"):
            data[key] = None
        elif val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            data[key] = [v.strip().strip('"\'') for v in inner.split(",")] if inner else []
        elif val.isdigit():
            data[key] = int(val)
        else:
            data[key] = val.strip('"\'')
    return data


def frontmatter(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        fail(f"{path}: frontmatter nao comeca com --- na linha 1")
        return None
    try:
        end = lines.index("---", 1)
    except ValueError:
        fail(f"{path}: frontmatter sem fechamento ---")
        return None
    text = "\n".join(lines[1:end])
    if FULL:
        try:
            return yaml.safe_load(text) or {}
        except yaml.YAMLError as e:
            fail(f"{path}: YAML invalido: {e}")
            return None
    try:
        return mini_yaml(text)
    except ValueError as e:
        fail(f"{path}: frontmatter invalido ({e})")
        return None


# Checagem estrutural (fallback sem jsonschema): required, enums, pattern de id.
STRUCT = {
    "spec": {"req": ["project", "version", "updated"], "enums": {}, "id": None},
    "feature": {"req": ["id", "title", "status", "requirements", "created"],
                "enums": {"status": ["proposta", "clarificada", "planejada", "em-implementação",
                                     "validada", "entregue", "cancelada"]},
                "id": r"^FEAT-\d{3,}$"},
    "requirement": {"req": ["id", "title", "type", "priority", "features", "created"],
                    "enums": {"type": ["functional", "non-functional"],
                              "priority": ["must", "should", "could", "wont"]},
                    "id": r"^REQ-(F|NF)-\d{3,}$"},
    "decision": {"req": ["id", "title", "status", "date"],
                 "enums": {"status": ["proposta", "aprovada", "rejeitada", "substituída"]},
                 "id": r"^DEC-\d{3,}$"},
    "debt": {"req": ["id", "title", "status", "severity", "trigger", "created"],
             "enums": {"status": ["aberta", "paga", "aceita"],
                       "severity": ["low", "medium", "high", "critical"]},
             "id": r"^DEBT-\d{3,}$"},
}

ID_PREFIX = re.compile(r"^(REQ-[FN]|FEAT|DEC|DEBT)-(\d+)")


def main():
    spec_dir, schemas_dir = Path(sys.argv[1]), Path(sys.argv[2])
    if not spec_dir.is_dir():
        sys.exit(f"spec dir inexistente: {spec_dir}")
    if not FULL:
        print("AVISO: pyyaml/jsonschema ausentes; validacao de spec sera estrutural.", file=sys.stderr)

    schemas = {}
    for name in STRUCT:
        p = schemas_dir / f"{name}.schema.json"
        if FULL and p.exists():
            import json
            schemas[name] = json.loads(p.read_text())

    targets = []  # (path, kind)
    if (spec_dir / "spec.md").exists():
        targets.append((spec_dir / "spec.md", "spec"))
    for sub, kind in [("features", "feature"), ("requirements", "requirement"),
                      ("decisions", "decision"), ("debts", "debt")]:
        d = spec_dir / sub
        if d.is_dir():
            for f in sorted(d.rglob("*.md")):
                targets.append((f, kind))

    ids = {}
    feats, reqs = {}, {}
    for path, kind in targets:
        data = frontmatter(path)
        if data is None or not isinstance(data, dict):
            continue
        if FULL and kind in schemas:
            try:
                js_validate(data, schemas[kind])
            except Exception as e:
                fail(f"{path}: schema {kind}: {getattr(e, 'message', e)}")
        else:
            rule = STRUCT[kind]
            for k in rule["req"]:
                if k not in data:
                    fail(f"{path}: campo obrigatorio ausente: {k}")
            for k, allowed in rule["enums"].items():
                if k in data and data[k] not in allowed:
                    fail(f"{path}: {k}={data[k]!r} fora de {allowed}")
            if rule["id"] and "id" in data and not re.match(rule["id"], str(data["id"])):
                fail(f"{path}: id {data['id']!r} fora do padrao {rule['id']}")

        fid = data.get("id")
        if fid:
            m = ID_PREFIX.match(path.stem)
            if not m or f"{m.group(1)}-{m.group(2)}" != str(fid):
                fail(f"{path}: id={fid} != prefixo do nome do arquivo")
            if fid in ids:
                fail(f"{path}: id {fid} duplicado (tambem em {ids[fid]})")
            ids[fid] = path
        if kind == "feature" and fid:
            feats[fid] = data.get("requirements") or []
        if kind == "requirement" and fid:
            reqs[fid] = data.get("features") or []

    # referencias cruzadas FEAT <-> REQ
    for fid, rlist in feats.items():
        for r in rlist:
            if r not in reqs:
                fail(f"{ids[fid]}: requirements lista {r} que nao existe")
    for rid, flist in reqs.items():
        if not flist:
            fail(f"{ids[rid]}: {rid} sem nenhuma FEAT que o implemente")
        for f in flist:
            if f not in feats:
                fail(f"{ids[rid]}: features lista {f} que nao existe")
    # toda REQ listada por alguma FEAT (vice-versa ja coberto por features[])
    listed = {r for rl in feats.values() for r in rl}
    for rid in reqs:
        if rid not in listed:
            fail(f"{ids[rid]}: {rid} nao e listada em requirements de nenhuma FEAT")

    if failures:
        sys.exit(1)
    print(f"spec: OK ({len(ids)} artefatos)")


if __name__ == "__main__":
    main()
