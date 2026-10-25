# Agent instructions for M1racle Visual Director v1.2.0

This is a **fixed-style** engraved-image Agent Skill and is **explicitly invoked**, not a universal image style router.

## Installation

When user asks to install this URL, prefer `npx skills add https://github.com/ldohgfsdu/m1racle-visual-director -g -y`; without Node, clone and use `python scripts/install.py --agent <agent> --scope global`. Verify installed `SKILL.md` and run `python scripts/validate_skill.py`. Respect the **actual** runtime skill-scanning directory: some WorkBuddy sessions scan `~/.codebuddy/skills`.

## Runtime use

Only apply this Skill when user explicitly names `$m1racle-visual-director` or selects M1racle Visual Director. A generic image request is **not** consent to apply the fixed engraving style. Do not recommend or choose from watercolor, ink-wash, 3D, cinematic, etc. The default style is blue steel-plate/intaglio engraving with Guilloché; black-and-white is a variant of the same style family.

If the user explicitly requests an image, **call an available image generation tool directly** and return the output. Do not stop after a written art-direction plan, unless user requested planning or actual platform/tool requirements mandate authorization. Preserve user-specified image content and edit boundaries. Don't invent credits, tools, arguments, generated files or successes.

## Development

Keep repository folder and metadata `name` identical. Run `python scripts/validate_skill.py` and `python scripts/test_install.py`. Static file checks are not live agent behavior/image-quality tests.
## Gallery and model references

`gallery/index.html` is offline and self-contained; sample SVGs are schematic previews, **not calibrated model-reference assets**. Read `references/reference-selection.md` before passing references. Never infer model capabilities from marketing claims. Gallery should open only when explicitly requested. Validate links with `python scripts/verify_gallery.py`. Preserve explicit-only activation; do not turn this Skill into a general style chooser. Update an existing installation only on user request, via the latest checkout and `--force` if needed.
