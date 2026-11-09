#!/usr/bin/env python3
"""Build a deterministic verified source ZIP and companion SHA-256 file."""
from __future__ import annotations

import argparse
import hashlib
import json
import stat
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "m1racle-intaglio-director/"
STAMP = (1980, 1, 1, 0, 0, 0)


def build(root: Path, destination: Path) -> tuple[Path, Path]:
    from validate_skill import check_package

    errors = check_package(root)
    if errors:
        raise ValueError("Package validation failed: " + "; ".join(errors))
    manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    version = manifest["version"]
    if not isinstance(version, str) or not version or "/" in version:
        raise ValueError("Invalid package version")
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination / f"m1racle-intaglio-director-v{version}.zip"
    checksum = destination / (archive.name + ".sha256")
    paths = ["MANIFEST.json", *[x["path"] for x in manifest["files"]]]
    with ZipFile(archive, "w", compression=ZIP_DEFLATED, compresslevel=9) as out:
        for rel in sorted(paths):
            name = PREFIX + rel
            info = ZipInfo(name, date_time=STAMP)
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.compress_type = ZIP_DEFLATED
            out.writestr(info, (root / rel).read_bytes(), compress_type=ZIP_DEFLATED, compresslevel=9)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum.write_text(digest + "  " + archive.name + "\n", encoding="ascii")
    with ZipFile(archive) as uploaded:
        if sorted(uploaded.namelist()) != sorted(PREFIX + p for p in paths):
            raise ValueError("Archive contents mismatch manifest")
        for rel in paths:
            if uploaded.read(PREFIX + rel) != (root / rel).read_bytes():
                raise ValueError("Archive byte mismatch for " + rel)
    return archive, checksum


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args(argv)
    archive, checksum = build(ROOT, args.output_dir)
    print("Verified", archive.name, hashlib.sha256(archive.read_bytes()).hexdigest())
    print("Checksum", checksum.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
