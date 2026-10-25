#!/usr/bin/env python3
"""No-network smoke test for the portable installer."""
from pathlib import Path
import subprocess
import sys
import tempfile

INSTALL = Path(__file__).resolve().parent / "install.py"
NAME = "m1racle-visual-director"
PATHS = {
    "codex": ".agents/skills",
    "claude-code": ".claude/skills",
    "opencode": ".config/opencode/skills",
    "cursor": ".cursor/skills",
    "codebuddy": ".codebuddy/skills",
    "workbuddy": ".workbuddy/skills",
    "gemini-cli": ".gemini/skills",
    "github-copilot": ".copilot/skills",
}

def run(*args, exit_code=0):
    p = subprocess.run([sys.executable, str(INSTALL), *args], text=True, capture_output=True, timeout=35)
    assert p.returncode == exit_code, f"{p.returncode} != {exit_code}: {p.stdout} {p.stderr}"
    return p.stdout

def test():
    with tempfile.TemporaryDirectory(prefix="m1racle-skill-") as temp:
        home = Path(temp) / "home"
        project = Path(temp) / "project"
        home.mkdir()
        project.mkdir()
        args = [word for agent in PATHS for word in ("--agent", agent)]
        run(*args, "--home", str(home))
        for agent, folder in PATHS.items():
            assert (home / folder / NAME / "SKILL.md").is_file(), agent
            assert (home / folder / NAME / "references" / "banknote-engraving.md").is_file(), agent
            assert (home / folder / NAME / "references" / "reference-selection.md").is_file(), agent
            assert (home / folder / NAME / "gallery" / "index.html").is_file(), agent
            assert (home / folder / NAME / "gallery" / "samples" / "blue.svg").is_file(), agent
            assert (home / folder / NAME / "gallery" / "samples" / "mono.svg").is_file(), agent
        run(*args, "--home", str(home), "--doctor")
        run(*args, "--home", str(home))
        sentinel = home / PATHS["codex"] / NAME / "user-file.txt"
        sentinel.write_text("preserve", encoding="utf-8")
        run("--agent", "codex", "--home", str(home))
        assert sentinel.is_file(), "Non-force install erased user content"
        run("--agent", "codex", "--home", str(home), "--force")
        assert not sentinel.exists(), "Explicit force failed to replace"
        run("--agent", "workbuddy", "--scope", "project", "--project-dir", str(project))
        assert (project / ".workbuddy/skills" / NAME / "SKILL.md").is_file()
        run("--agent", "invalid-agent", exit_code=2)

if __name__ == "__main__":
    test()
    print("INSTALL SMOKE TESTS: PASS (8 targets, idempotency, force update, project scope, invalid agent)")
