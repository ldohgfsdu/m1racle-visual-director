# M1racle Visual Director

[中文使用指南](使用指南.md) · [Agent Skills 规范](https://agentskills.io/specification) · **v1.1.0**

A portable AI image-art-direction skill: automatically choose text-to-image, reference-based generation, full-image transformation, local editing, or multi-image composition. Select visual styles based on the user's actual goal instead of applying one fixed aesthetic.

**Includes:** 5 routes · 17 style families · L0–L3 preservation · 24 behavior fixtures · Guilloché / steel-plate banknote engraving.

## Give the repository URL to your Agent

Send this sentence to a coding Agent with terminal/repository access:

> Install https://github.com/ldohgfsdu/m1racle-visual-director as a user-level Agent Skill for your own Agent. Use the standard Skills CLI when available. Verify the installed SKILL.md and run the validator. Then tell me which image-generation/editing tools you can actually use.

### One-line install (Node.js 22.20+)

```bash
npx skills add https://github.com/ldohgfsdu/m1racle-visual-director -g -y
```

Specify an Agent as needed, e.g.:

```bash
npx skills add https://github.com/ldohgfsdu/m1racle-visual-director -g -a codex -y
npx skills add https://github.com/ldohgfsdu/m1racle-visual-director -g -a claude-code -y
npx skills add https://github.com/ldohgfsdu/m1racle-visual-director -g -a opencode -y
npx skills add https://github.com/ldohgfsdu/m1racle-visual-director -g -a cursor -y
npx skills add https://github.com/ldohgfsdu/m1racle-visual-director -g -a codebuddy -y
```

Pass multiple `-a` switches for more than one Agent. Without `-g`, installation is project-local. No renaming after cloning: repository folder and SKILL.md name are both **m1racle-visual-director**.

### Python fallback (no Node.js, including WorkBuddy)

Clone/download this repository and, from its root, run:

```bash
python scripts/install.py --agent workbuddy --scope global
python scripts/install.py --agent codex --agent claude-code --agent codebuddy --scope global
python scripts/install.py --agent opencode --scope global --doctor
```

Python 3.9+ standard library only. For project-level installs: `--scope project --project-dir /path/to/project`. Existing installations are preserved unless `--force` is given. Inspect options with `python scripts/install.py --help`.

## Installation directories (fallback script)

| Agent | Global destination |
|---|---|
| Codex | `~/.agents/skills/m1racle-visual-director` |
| Claude Code | `~/.claude/skills/m1racle-visual-director` |
| OpenCode | `~/.config/opencode/skills/m1racle-visual-director` |
| Cursor | `~/.cursor/skills/m1racle-visual-director` |
| CodeBuddy | `~/.codebuddy/skills/m1racle-visual-director` |
| WorkBuddy | `~/.workbuddy/skills/m1racle-visual-director` |
| Gemini CLI | `~/.gemini/skills/m1racle-visual-director` |
| GitHub Copilot | `~/.copilot/skills/m1racle-visual-director` |

The Skills CLI maintains its own supported Agent list and paths; these paths describe the Python fallback.

## Validation

```bash
python scripts/validate_skill.py
python scripts/test_install.py
```

Expected: `STATIC CHECK: PASS` and `INSTALL SMOKE TESTS: PASS`. Static fixtures do **not** exercise Agent judgment or image quality. Confirm the Agent discovers the installed skill (CodeBuddy: `/skills`) and has a connected image-generation tool before expecting real images.

## Usage

> Use m1racle-visual-director to create a 16:9 ancient Chinese mountain city; choose an appropriate style automatically.

> Treat my uploaded images only as style references; make a new scene rather than copying the landmarks.

> Turn this exact photo into banknote intaglio engraving while preserving its architecture and composition.

## Scope and limitations

This repository supplies **routing, style selection, prompt design, and visual QA instructions**. It does not bundle an image model, image API key, or paid generation service. A bare URL cannot install software by itself in an Agent without network/filesystem/terminal permissions. Do not claim actual generation or successful installation unless verified.
