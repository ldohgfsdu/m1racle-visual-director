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
# Schematic variants must have materially distinct geometry, not just recoloring.
import xml.etree.ElementTree as ET
def paths(file):
    tree = ET.parse(file)
    return {element.attrib["d"] for element in tree.iter() if element.tag.endswith("}path") and "d" in element.attrib}
blue = paths(ROOT / "gallery/samples/blue.svg")
mono = paths(ROOT / "gallery/samples/mono.svg")
assert len(blue) > 30 and len(mono) > 30
assert len(blue & mono) / min(len(blue), len(mono)) < .3, "Same geometry, different ink color"
for file in ("blue.svg", "mono.svg"):
    txt = (ROOT / "gallery/samples" / file).read_text("utf-8")
    assert "<circle" in txt and " A" in txt, "Need curved Guilloché, not a rectilinear grid"
print("GALLERY REGRESSION TESTS: PASS")
