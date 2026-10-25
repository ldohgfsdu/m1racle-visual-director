# Agent instructions for M1racle Visual Director v1.4.2

This is a **fixed-style** engraved-image Agent Skill and is **explicitly invoked**, not a universal image style router.

## Installation and updating

**MANDATORY:** Read [INSTALL.md](INSTALL.md) fully and follow its single short-bounded ZIP path. Do **not** use `git clone` in any form as automatic fallback, even if a third-party proxy works; do not run the old `scripts/install.py` on a freshly cloned repository. Do not wait 150 seconds, repeatedly retry dead endpoints, run redundant development test suites on user install, or recommend `scripts/package_workbuddy.py` (removed). Third-party mirrors require explicit user trust, and raw-file availability does not prove archive availability. A cloud Skill installation does not imply mobile account-level Skill registration.

## Runtime use

Only apply this Skill when user explicitly names `$m1racle-visual-director` or selects M1racle Visual Director. A generic image request is **not** consent to apply the fixed engraving style. Do not recommend or choose from watercolor, ink-wash, 3D, cinematic, etc. The default style is blue steel-plate/intaglio engraving with Guilloché; black-and-white is a variant of the same style family.

If the user explicitly requests an image, **call an available image generation tool directly** and return the output. Do not stop after a written art-direction plan, unless user requested planning or actual platform/tool requirements mandate authorization. Preserve user-specified image content and edit boundaries. Don't invent credits, tools, arguments, generated files or successes.

## Development

The installed skill folder must match metadata `name`; arbitrary staging/checkout directory names are valid and must not fail static validation. Run `python scripts/validate_skill.py` and `python scripts/test_install.py`. Static file checks are not live agent behavior/image-quality tests.
## Gallery and model references

`gallery/index.html` is offline and self-contained; sample SVGs are schematic previews, **not calibrated model-reference assets**. Read `references/reference-selection.md` before passing references. Never infer model capabilities from marketing claims. Gallery should open only when explicitly requested. Validate links with `python scripts/verify_gallery.py`. Preserve explicit-only activation; do not turn this Skill into a general style chooser. Update an existing installation only on user request, via the bounded `quick_install.py` flow and `--force` if needed.

## Network/install boundary

A proxy on the user's phone or desktop is NOT automatically accessible from cloud Agent sandboxes; 127.0.0.1 inside a cloud VM does not mean the user's computer. Installing into `~/.codebuddy/skills` does not prove mobile account-level registration. On installation verify the active Agent scan path using the previously trusted installer `--doctor`. NEVER execute `scripts/validate_skill.py` from the newly downloaded archive; a pre-existing trusted validator can use `--root` for offline analysis. Never claim mobile Skill Market registration.
