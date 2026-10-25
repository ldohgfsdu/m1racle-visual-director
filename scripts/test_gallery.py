#!/usr/bin/env python3
"""Regression tests for missing landing page, CDN injection, and malformed SVG."""
import importlib.util
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("verify_gallery", ROOT / "scripts/verify_gallery.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory(prefix="m1racle-gallery-") as tmp:
    dest = Path(tmp)
    for folder in ("gallery", "references"):
        shutil.copytree(ROOT / folder, dest / folder)
    shutil.copy2(ROOT / "index.html", dest / "index.html")
    module.ROOT = dest
    assert module.verify()[0] == [], module.verify()
    (dest / "index.html").unlink()
    assert module.verify()[0], "Missing landing page was accepted"
    shutil.copy2(ROOT / "index.html", dest / "index.html")
    page = dest / "gallery/index.html"
    original = page.read_text("utf-8")
    page.write_text(original.replace("</head>", '<script src="https://cdn.example/x.js"></script></head>'), encoding="utf-8")
    assert module.verify()[0], "Remote script injection was accepted"
    page.write_text(original.replace("</head>", '<link rel="stylesheet" href="https://cdn.example/x.css"></head>'), encoding="utf-8")
    assert module.verify()[0], "Remote CSS injection was accepted"
    page.write_text(original, encoding="utf-8")
    (dest / "gallery/samples/blue.svg").write_text("<svg><oops>", encoding="utf-8")
    assert module.verify()[0], "Malformed SVG was accepted"
print("GALLERY REGRESSION TESTS: PASS")
