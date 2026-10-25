#!/usr/bin/env python3
"""Quick install without git/Node: bounded ZIP fetch; standard-library only (Python 3.9+)."""
from __future__ import annotations
import argparse
import io
import hashlib
import ntpath
import os
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
    "codex": (".codex/skills", ".agents/skills"),
    "claude-code": (".claude/skills", ".claude/skills"),
    "opencode": (".config/opencode/skills", ".opencode/skills"),
    "cursor": (".cursor/skills", ".cursor/skills"),
    "codebuddy": (".codebuddy/skills", ".codebuddy/skills"),
    "workbuddy": (".workbuddy/skills", ".workbuddy/skills"),
    "gemini-cli": (".gemini/skills", ".gemini/skills"),
    "github-copilot": (".copilot/skills", ".agents/skills"),
}
REQUIRED = (
    "SKILL.md", "README.md", "INSTALL.md", "AGENTS.md", "使用指南.md",
    "index.html", "gallery/index.html", "gallery/samples/blue.svg",
    "gallery/samples/mono.svg", "references/banknote-engraving.md",
    "references/reference-selection.md", "references/quality-gates.md",
    "references/model_capabilities.json", "evals/cases.json",
    "evals/how-to-test.md", "scripts/validate_skill.py",
    "scripts/verify_gallery.py",
)
MAX_ZIP = 8 * 1024 * 1024
MAX_EXPANDED = 24 * 1024 * 1024

def valid(root: Path) -> bool:
    """Structural verification only. NEVER execute code from a downloaded ZIP."""
    try:
        if not all((root / file).is_file() for file in REQUIRED):
            return False
        raw = (root / "SKILL.md").read_text(encoding="utf-8")
        front = re.match(r"\A---\n(.*?)\n---\n", raw, re.S)
        if not front or not re.search(r"(?m)^name:\s*m1racle-visual-director\s*$", front[1]):
            return False
        if not re.search(r"(?m)^disable-model-invocation:\s*true\s*$", front[1]):
            return False
        import json
        data = json.loads((root / "evals/cases.json").read_text(encoding="utf-8"))
        if not isinstance(data.get("cases"), list) or len(data["cases"]) < 24:
            return False
        manifest = json.loads((root / "references/model_capabilities.json").read_text("utf-8"))
        if manifest["default"]["status"] != "unverified":
            return False
        for rel in re.findall(r"\]\((references/[^)#]+|evals/[^)#]+|gallery/[^)#]+)\)", raw):
            if not (root / rel).is_file():
                return False
        return True
    except (OSError, UnicodeError, ValueError, KeyError, TypeError):
        return False

def unpack(data: bytes, dest: Path) -> None:
    if len(data) > MAX_ZIP:
        raise ValueError("ZIP larger than 8 MiB")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        items = z.infolist()
        if len(items) > 250 or sum(i.file_size for i in items) > MAX_EXPANDED:
            raise ValueError("ZIP size or entry count exceeds limits")
        roots, seen = set(), set()
        for i in items:
            value = i.filename
            parts = value.split("/")
            # Reject Windows drive-relative/absolute, ADS and ambiguous NTFS names
            # even when running the installer on Linux.
            if (not value or value.startswith(("/", "\\\\")) or "\\\\" in value
                or ntpath.splitdrive(value)[0]
                or any(not part or part in (".", "..") or ":" in part
                       or part.rstrip(" .") != part
                       or part.split(".")[0].upper() in
                       {"CON", "PRN", "AUX", "NUL", "COM1", "COM2", "LPT1", "LPT2"}
                       for part in (parts[:-1] if i.is_dir() else parts))):
                raise ValueError("Unsafe ZIP path: " + value)
            mode = (i.external_attr >> 16) & 0o170000
            if mode not in (0, 0o040000, 0o100000):
                raise ValueError("ZIP contains special file")
            if not i.is_dir():
                if len(parts) < 2:
                    raise ValueError("ZIP must contain enclosing root folder")
                roots.add(parts[0])
                key = "/".join(parts[1:]).casefold()
                if key in seen:
                    raise ValueError("Duplicate ZIP path: " + value)
                seen.add(key)
        if len(roots) != 1:
            raise ValueError("ZIP must contain one root directory")
        destination = dest.resolve()
        for i in items:
            if i.is_dir():
                continue
            rel = i.filename.split("/")[1:]
            if any(part.startswith(".") or part == "__pycache__" for part in rel):
                continue
            target = dest.joinpath(*rel).resolve()
            if destination not in target.parents:
                raise ValueError("ZIP target escapes destination: " + i.filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(i) as inp, target.open("wb") as out:
                shutil.copyfileobj(inp, out)
    if not valid(dest):
        raise ValueError("Skill validation failed after download")

class HTTPSRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlsplit(newurl).scheme.lower() != "https":
            raise ValueError("HTTPS redirect downgrade refused")
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def fetch(url: str, timeout: float, proxy: str | None) -> bytes:
    if urllib.parse.urlsplit(url).scheme.lower() != "https":
        raise ValueError("Archive source must be HTTPS")

    if proxy is not None:
        if not proxy.startswith(("http://", "https://")):
            raise ValueError("Proxy must be HTTP or HTTPS; stdlib cannot tunnel SOCKS5")
        handler = urllib.request.ProxyHandler({"https": proxy, "http": proxy})
        client = urllib.request.build_opener(handler, HTTPSRedirect())
    else:
        # Standard urllib ProxyHandler automatically uses HTTPS_PROXY / HTTP_PROXY.
        client = urllib.request.build_opener(HTTPSRedirect())
    request = urllib.request.Request(
        url, headers={"User-Agent": "M1racle-Quick-Installer/1.0"})
    until = time.monotonic() + timeout
    with client.open(request, timeout=timeout) as response:
        if urllib.parse.urlsplit(response.geturl()).scheme.lower() != "https":
            raise ValueError("Archive download redirected to non-HTTPS")
        result = bytearray()
        while True:
            remaining = until - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Download exceeds source deadline")
            # HTTPResponse.read(65536) waits to fill its buffer on slow servers.
            # read1 returns currently available bytes; cap each socket wait.
            sock = getattr(getattr(getattr(response, "fp", None), "raw", None), "_sock", None)
            if sock is not None:
                sock.settimeout(min(0.25, max(0.01, remaining)))
            chunk = response.read1(min(16384, MAX_ZIP + 1 - len(result)))
            if not chunk:
                break
            result.extend(chunk)
            if len(result) > MAX_ZIP:
                raise ValueError("ZIP too large")
        if time.monotonic() > until:
            raise TimeoutError("Download exceeds source deadline")
        return bytes(result)

def put(source: Path, target: Path, force: bool) -> str:
    target.parent.mkdir(parents=True, exist_ok=True)
    exists = target.exists() or target.is_symlink()
    if exists and not force:
        return "already-installed" if valid(target) else "blocked-existing"
    new = target.parent / (".m1racle-new-" + uuid.uuid4().hex)
    old = target.parent / (".m1racle-old-" + target.name + "-" + uuid.uuid4().hex)
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
    p.add_argument("--expected-sha256", help="Trusted SHA-256; REQUIRED for --archive-file or --mirror-url")
    p.add_argument("--timeout", type=float, default=8, help="Per-URL timeout, default 8s")
    p.add_argument("--max-seconds", type=float, default=24, help="Download time budget, default 24s")
    o = p.parse_args(argv)
    if not .5 <= o.timeout <= 60 or not 1 <= o.max_seconds <= 180:
        p.error("Invalid timeout or budget")
    if o.mirror_url and not o.mirror_url.startswith("https://"):
        p.error("Mirror must be HTTPS")
    if o.archive_file and o.mirror_url:
        p.error("Choose --archive-file or --mirror-url")
    if o.expected_sha256 and not re.fullmatch(r"[0-9a-fA-F]{64}", o.expected_sha256):
        p.error("--expected-sha256 must contain exactly 64 hex characters")
    if (o.archive_file or o.mirror_url) and not o.expected_sha256:
        p.error("Untrusted ZIP source requires --expected-sha256 from an independent trusted channel")
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
            if o.archive_file.stat().st_size > MAX_ZIP:
                raise ValueError("Offline ZIP larger than 8 MiB")
            with o.archive_file.open("rb") as handle:
                data = handle.read(MAX_ZIP + 1)
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
        if o.expected_sha256 and hashlib.sha256(data).hexdigest() != o.expected_sha256.lower():
            raise ValueError("SHA-256 mismatch: ZIP content rejected")
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
