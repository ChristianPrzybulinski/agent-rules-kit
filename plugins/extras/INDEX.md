# extras/ — ai-kit extras — opt-in skills

Opt-in plugin: not required by the `all` bundle; install it explicitly (see README).

## `skills/`

| Skill | Description |
|---|---|
| `dbeaver` | DBeaver GUI inspection. Use when inspecting a database, exporting test data or drawing an ER diagram. Not for schema changes (skill postgresql). |
| `find-skills` | Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skill that can...", or express interest in extending capabilities. This skill should be used when the user is looking for functionality that might exist as an installable skill. |
| `frontend-design` | Guidance for distinctive, intentional visual design when building new UI or reshaping an existing one. Helps with aesthetic direction, typography, and making choices that don't read as templated defaults. |
| `krita` | Krita pixel-art workflow. Use when editing pixel art, retouching sprites or defining sprite export. Not for Godot import (skill asset-import). |
| `skill-creator` | Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy. |

Manifests: `.devin-plugin/plugin.json` (Devin) · `.claude-plugin/plugin.json` (Claude) · `plugin.json` (Codex).
