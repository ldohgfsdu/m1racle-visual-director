#!/usr/bin/env python3
"""Build a self-contained WorkBuddy import ZIP with skill-name/SKILL.md."""
from __future__ import annotations
import re
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "m1racle-visual-director"
INCLUDE = (
    "SKILL.md", "README.md", "使用指南.md",
    "references", "gallery", "evals",
    "scripts/validate_skill.py", "scripts/verify_gallery.py",
)

def files():
    paths = []
    for item in INCLUDE:
        p = ROOT / item
        if not p.exists():
            raise FileNotFoundError(item)
        if p.is_dir():
            paths.extend(x for x in p.rglob("*") if x.is_file() and not x.is_symlink()
                         and "__pycache__" not in x.parts)
        elif p.is_file() and not p.is_symlink():
            paths.append(p)
    return sorted(paths)

def build():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r"(?m)^version:\s*(\d+\.\d+\.\d+)\s*$", skill)
    if not match:
        raise ValueError("Top-level WorkBuddy version is missing")
    version = match.group(1)
    for field in ("name", "display_name", "display_name_en", "description",
                  "description_zh", "description_en", "author"):
        if not re.search(r"(?m)^" + field + r":\s*\S", skill):
            raise ValueError("Missing WorkBuddy metadata: " + field)
    output = ROOT / "dist" / (NAME + "-workbuddy-v" + version + ".zip")
    output.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in files():
            rel = p.relative_to(ROOT).as_posix()
            z.write(p, NAME + "/" + rel)
    with zipfile.ZipFile(output) as z:
        members = z.namelist()
        assert len(members) == len(set(members))
        assert NAME + "/SKILL.md" in members
        assert NAME + "/gallery/index.html" in members
        assert NAME + "/gallery/samples/blue.svg" in members
        assert NAME + "/gallery/samples/mono.svg" in members
        for member in members:
            assert member.startswith(NAME + "/") and ".." not in Path(member).parts
        with tempfile.TemporaryDirectory(prefix="m1racle-wb-") as tmp:
            z.extractall(tmp)
            sys.path.insert(0, str(Path(tmp) / NAME / "scripts"))
            import validate_skill
            import verify_gallery
            assert not validate_skill.verify(), "Packed Skill failed static checks"
            source_root = verify_gallery.ROOT
            source_gallery = verify_gallery.GALLERY
            try:
                verify_gallery.ROOT = Path(tmp) / NAME
                verify_gallery.GALLERY = verify_gallery.ROOT / "gallery/index.html"
                assert not verify_gallery.verify(), "Packed gallery failed integrity"
            finally:
                verify_gallery.ROOT = source_root
                verify_gallery.GALLERY = source_gallery
    print("WORKBUDDY PACKAGE CHECK: PASS")
    print(output.relative_to(ROOT).as_posix())
    print("files:", len(members))
    return output

if __name__ == "__main__":
    try:
        build()
    except (AssertionError, ValueError, OSError) as exc:
        print("WORKBUDDY PACKAGE CHECK: FAIL:", exc, file=sys.stderr)
        sys.exit(1)
