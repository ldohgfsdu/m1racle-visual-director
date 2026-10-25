# Instructions to coding Agents: M1racle Visual Director repository

This repository itself is a single, root-level Agent Skill, not an image-generation API.

When the user supplies its GitHub URL and asks you to install it:

1. Confirm source: https://github.com/ldohgfsdu/m1racle-visual-director
2. Install **for the running Agent** at user scope with `npx skills add https://github.com/ldohgfsdu/m1racle-visual-director -g -y`. Add `-a codex`, `-a claude-code`, `-a opencode`, `-a cursor`, or `-a codebuddy` if detection is ambiguous.
3. When Node.js is unavailable, clone/download the repository, then run `python scripts/install.py --agent <agent> --scope global`. WorkBuddy uses `--agent workbuddy`.
4. Verify that the installed directory contains `SKILL.md`, `references/`, `evals/` and `scripts/`; run the installed `scripts/validate_skill.py`. Confirm Agent discovery where possible.
5. Install only for the Agent(s) the user requests. Do not silently replace unrelated user files or enable paid API services.
6. This skill does not include an image-generation model. Check for actual available image tools; never claim an image was generated unless it was.

When modifying this repository: `name: m1racle-visual-director` must agree with the default checkout folder. Run `python scripts/validate_skill.py` and `python scripts/test_install.py` before publishing.
