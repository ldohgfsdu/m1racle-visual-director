#!/usr/bin/env python3
"""Quick install without git/Node: bounded ZIP fetch; standard-library only (Python 3.9+)."""
from __future__ import annotations
import argparse
import io
import re
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile
from pathlib import Path

NAME = "m1racle-visual-director"
REPO = "ldohgfsdu/m1racle-visual-director"
SOURCES = (
    "https://codeload.github.com/" + REPO + "/zip/refs/heads/main",
    "https://api.github.com/repos/" + REPO + "/zipball/main",
)
AGENTS = {
    "codex": (".agents/skills", ".agents/skills"),
    "claude-code": (".claude/skills", ".claude/skills"),
    "opencode": (".config/opencode/skills", ".opencode/skills"),
    "cursor": (".cursor/skills", ".cursor/skills"),
    "codebuddy": (".codebuddy/skills", ".codebuddy/skills"),
    "workbuddy": (".workbuddy/skills", ".workbuddy/skills"),
    "gemini-cli": (".gemini/skills", ".gemini/skills"),
    "github-copilot": (".copilot/skills", ".agents/skills"),
}
REQUIRED = (
    "SKILL.md", "gallery/index.html", "gallery/samples/blue.svg",
    "gallery/samples/mono.svg", "references/banknote-engraving.md",
    "references/reference-selection.md", "scripts/validate_skill.py",
)
MAX_ZIP = 8 * 1024 * 1024
MAX_EXPANDED = 24 * 1024 * 1024

def valid(root: Path) -> bool:
    try:
        return (
            all((root / file).is_file() for file in REQUIRED)
            and re.search(r"(?m)^name:\s*m1racle-visual-director\s*$",
                          (root / "SKILL.md").read_text("utf-8")) is not None
        )
    except (OSError, UnicodeError):
        return False

def unpack(data: bytes, dest: Path) -> None:
    if len(data) > MAX_ZIP:
        raise ValueError("ZIP larger than 8 MiB")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        items = z.infolist()
        if len(items) > 250 or sum(i.file_size for i in items) > MAX_EXPANDED:
            raise ValueError("ZIP size or entry count exceeds limits")
        roots = set()
        for i in items:
            value = i.filename
            parts = value.split("/")
            if value.startswith(("/", "\\")) or "\\" in value or "." in parts or ".." in parts:
                raise ValueError("Unsafe ZIP path: " + value)
            if (i.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("ZIP contains symlink")
            if not i.is_dir():
                if len(parts) < 2:
                    raise ValueError("ZIP must contain enclosing root folder")
                roots.add(parts[0])
        if len(roots) != 1:
            raise ValueError("ZIP must contain one root directory")
        for i in items:
            if i.is_dir():
                continue
            rel = i.filename.split("/")[1:]
            if any(part.startswith(".") or part == "__pycache__" for part in rel):
                continue
            target = dest.joinpath(*rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(i) as inp, target.open("wb") as out:
                shutil.copyfileobj(inp, out)
    if not valid(dest):
        raise ValueError("Skill validation failed after download")

def fetch(url: str, timeout: float, proxy: str | None) -> bytes:
    if proxy is not None:
        if not proxy.startswith(("http://", "https://")):
            raise ValueError("Proxy must be HTTP or HTTPS; stdlib cannot tunnel SOCKS5")
        handler = urllib.request.ProxyHandler({"https": proxy, "http": proxy})
        client = urllib.request.build_opener(handler)
    else:
        # Standard urllib ProxyHandler automatically uses HTTPS_PROXY / HTTP_PROXY.
        client = urllib.request.build_opener()
    request = urllib.request.Request(
        url, headers={"User-Agent": "M1racle-Quick-Installer/1.0"})
    with client.open(request, timeout=timeout) as response:
        result = bytearray()
        until = time.monotonic() + timeout
        while True:
            if time.monotonic() >= until:
                raise TimeoutError("Download exceeds source deadline")
            chunk = response.read(min(65536, MAX_ZIP + 1 - len(result)))
            if not chunk:
                break
            result.extend(chunk)
            if len(result) > MAX_ZIP:
                raise ValueError("ZIP too large")
        return bytes(result)

def put(source: Path, target: Path, force: bool) -> str:
    target.parent.mkdir(parents=True, exist_ok=True)
    exists = target.exists() or target.is_symlink()
    if exists and not force:
        return "already-installed" if valid(target) else "blocked-existing"
    new = target.parent / (".m1racle-new-" + uuid.uuid4().hex)
    old = target.parent / (".m1racle-old-" + uuid.uuid4().hex)
    try:
        shutil.copytree(source, new)
        if not valid(new):
            raise ValueError("Copy invalid")
        if exists:
            target.rename(old)
        try:
            new.rename(target)
        except BaseException:
            if old.exists() or old.is_symlink():
                old.rename(target)
            raise
        if old.is_symlink() or old.is_file():
            old.unlink()
        elif old.exists():
            shutil.rmtree(old)
        return "updated" if exists else "installed"
    finally:
        if new.exists():
            shutil.rmtree(new)

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Fast installation via bounded GitHub archive, no git required")
    p.add_argument("--agent", action="append", required=True, help="Agent name or 'all'")
    p.add_argument("--scope", choices=("global", "project"), default="global")
    p.add_argument("--home", type=Path, default=Path.home())
    p.add_argument("--project-dir", type=Path, default=Path.cwd())
    p.add_argument("--force", action="store_true", help="Update, replacing the old skill")
    p.add_argument("--doctor", action="store_true", help="Only inspect installed files; no network")
    p.add_argument("--dry-run", action="store_true", help="Show target paths; no network")
    p.add_argument("--proxy", help="Trusted HTTP(S) proxy, otherwise inherit HTTPS_PROXY")
    p.add_argument("--mirror-url", help="Explicitly trusted HTTPS ZIP mirror to try first")
    p.add_argument("--archive-file", type=Path, help="Use local ZIP for offline installation")
    p.add_argument("--timeout", type=float, default=8, help="Per-URL timeout, default 8s")
    p.add_argument("--max-seconds", type=float, default=24, help="Download time budget, default 24s")
    o = p.parse_args(argv)
    if not .5 <= o.timeout <= 60 or not 1 <= o.max_seconds <= 180:
        p.error("Invalid timeout or budget")
    if o.mirror_url and not o.mirror_url.startswith("https://"):
        p.error("Mirror must be HTTPS")
    if o.archive_file and o.mirror_url:
        p.error("Choose --archive-file or --mirror-url")
    agents = []
    for agent in o.agent:
        if agent == "all":
            agents.extend(AGENTS)
        elif agent in AGENTS:
            agents.append(agent)
        else:
            p.error("Unsupported agent: " + agent)
    targets = []
    for agent in dict.fromkeys(agents):
        rel = AGENTS[agent][0 if o.scope == "global" else 1]
        base = o.home.expanduser() if o.scope == "global" else o.project_dir.expanduser()
        targets.append((agent, base / rel / NAME))
    if o.doctor or o.dry_run:
        failed = False
        for agent, target in targets:
            state = ("PASS" if valid(target) else "MISSING_OR_INVALID") if o.doctor else (
                "would-update" if target.exists() else "would-install")
            print("%s: %s -> %s" % (agent, state, target))
            failed |= state == "MISSING_OR_INVALID"
        return int(failed)
    if not o.force and all(valid(target) for _, target in targets):
        print("INSTALL CHECK: PASS (already installed; --force requests an update)")
        return 0
    try:
        if o.archive_file:
            data = o.archive_file.read_bytes()
            print("Offline archive:", o.archive_file)
        else:
            data = None
            errors = []
            started = time.monotonic()
            for url in ([o.mirror_url] if o.mirror_url else []) + list(SOURCES):
                remaining = o.max_seconds - (time.monotonic() - started)
                if remaining <= 0:
                    break
                host = urllib.parse.urlsplit(url).hostname
                print("Downloading from:", host, flush=True)
                try:
                    data = fetch(url, min(o.timeout, remaining), o.proxy)
                    break
                except (OSError, ValueError, TimeoutError, urllib.error.URLError) as exc:
                    errors.append("%s:%s" % (host, type(exc).__name__))
            if data is None:
                raise RuntimeError("Could not download promptly (%s). Configure HTTPS_PROXY / --proxy or provide --mirror-url / --archive-file." % ", ".join(errors))
        with tempfile.TemporaryDirectory(prefix="m1racle-zip-") as temp:
            stage = Path(temp) / NAME
            stage.mkdir()
            unpack(data, stage)
            failed = False
            for agent, target in targets:
                try:
                    status = put(stage, target, o.force)
                except (OSError, ValueError) as exc:
                    status = "ERROR: %s" % exc
                print("%s: %s -> %s" % (agent, status, target))
                failed |= status.startswith("ERROR") or status == "blocked-existing"
            print("INSTALL CHECK:", "FAIL" if failed else "PASS")
            return int(failed)
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
        print("INSTALL CHECK: FAIL:", exc, file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
