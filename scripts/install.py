#!/usr/bin/env python3
"""Optional cross-agent installer. Python 3.9+ standard library only."""
from __future__ import annotations

import argparse
import os
import shutil
import uuid
from pathlib import Path
from quick_install import valid as has_skill, recover_backup, cleanup_backups

NAME = "m1racle-visual-director"
ROOT = Path(__file__).resolve().parents[1]
AGENTS = {
    "codex": (".codex/skills", ".agents/skills"),
    "claude-code": (".claude/skills", ".claude/skills"),
    "opencode": (".config/opencode/skills", ".opencode/skills"),
    "cursor": (".cursor/skills", ".cursor/skills"),
    "codebuddy": (".codebuddy/skills", ".codebuddy/skills"),
    "workbuddy": (".workbuddy/skills", ".workbuddy/skills"),
    "gemini-cli": (".gemini/skills", ".gemini/skills"),
    "github-copilot": (".copilot/skills", ".agents/skills"),
}

def install(target: Path, force: bool) -> str:
    if target.resolve() == ROOT.resolve():
        raise RuntimeError("Cannot install over source checkout")
    target.parent.mkdir(parents=True, exist_ok=True)
    recover_backup(target, prefix=".m1racle-backup-")
    cleanup_backups(target, prefix=".m1racle-backup-")
    exists = target.exists() or target.is_symlink()
    if exists and not force:
        return "already-installed" if has_skill(target) else "blocked-existing"
    tmp = target.parent / (".m1racle-install-" + uuid.uuid4().hex)
    bak = target.parent / (".m1racle-backup-" + target.name + "-" + uuid.uuid4().hex)
    try:
        shutil.copytree(ROOT, tmp, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".pytest_cache"))
        if not has_skill(tmp):
            raise RuntimeError("Copied skill failed basic integrity check")
        if exists:
            target.rename(bak)
        try:
            tmp.rename(target)
        except BaseException:
            if bak.exists() or bak.is_symlink():
                bak.rename(target)
            raise
        if bak.is_symlink() or bak.is_file():
            bak.unlink()
        elif bak.exists():
            shutil.rmtree(bak)
        return "updated" if exists else "installed"
    finally:
        if tmp.is_dir():
            shutil.rmtree(tmp)

def main() -> int:
    p = argparse.ArgumentParser(description="Install M1racle Visual Director into Agent Skills directories")
    p.add_argument("--agent", action="append", required=True, help="Agent ID: " + ", ".join(AGENTS) + " or all")
    p.add_argument("--scope", choices=("global", "project"), default="global")
    p.add_argument("--home", type=Path, default=Path.home(), help="Global installation home")
    p.add_argument("--project-dir", type=Path, default=Path.cwd(), help="Project directory for project scope")
    p.add_argument("--force", action="store_true", help="Explicitly replace existing installation")
    p.add_argument("--doctor", action="store_true", help="Check installation without changing files")
    p.add_argument("--dry-run", action="store_true", help="Preview intended changes")
    opts = p.parse_args()
    if not has_skill(ROOT):
        p.error("Source checkout has no valid SKILL.md and bundled directories")
    ids = []
    for agent in opts.agent:
        if agent == "all":
            ids.extend(AGENTS)
        elif agent in AGENTS:
            ids.append(agent)
        else:
            p.error(f"Unsupported --agent {agent!r}")
    errors = 0
    for agent in dict.fromkeys(ids):
        dir_path = AGENTS[agent][0 if opts.scope == "global" else 1]
        base = opts.home.expanduser() if opts.scope == "global" else opts.project_dir.expanduser()
        target = (Path(os.environ["CODEX_HOME"]).expanduser() / "skills" / NAME
                  if agent == "codex" and opts.scope == "global" and opts.home == Path.home() and os.environ.get("CODEX_HOME")
                  else base / dir_path / NAME)
        if opts.doctor:
            state = "PASS" if has_skill(target) else "MISSING_OR_INVALID"
        elif opts.dry_run:
            state = "would-replace" if (target.exists() or target.is_symlink()) else "would-install"
        else:
            try:
                state = install(target, opts.force)
            except (RuntimeError, OSError) as exc:
                state = f"ERROR: {exc}"
        print(f"{agent}: {state} -> {target}")
        if state in ("blocked-existing", "MISSING_OR_INVALID") or state.startswith("ERROR"):
            errors += 1
    print("INSTALL CHECK: FAIL" if errors else "INSTALL CHECK: PASS")
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
