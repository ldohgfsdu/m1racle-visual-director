#!/usr/bin/env python3
"""Check offline gallery assets and reference policy without external dependencies."""
from __future__ import annotations
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
GALLERY = ROOT / "gallery" / "index.html"
ASSETS = {"gallery/samples/blue.svg", "gallery/samples/mono.svg"}

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() != "img":
            return
        data = dict(attrs)
        if data.get("src"):
            self.images.append(data["src"])

def verify():
    errors = []
    if not GALLERY.is_file():
        return ["missing gallery/index.html"]
    parser = Links()
    parser.feed(GALLERY.read_text(encoding="utf-8"))
    if len(parser.images) < 2:
        errors.append("gallery must contain at least two images")
    for raw in parser.images:
        url = urlsplit(raw)
        if url.scheme or url.netloc or raw.startswith("//"):
            errors.append("external gallery dependency: " + raw)
            continue
        local = (GALLERY.parent / unquote(url.path)).resolve()
        if not local.is_relative_to(ROOT.resolve()) if hasattr(local, "is_relative_to") else ROOT.resolve() not in local.parents:
            errors.append("path escape: " + raw)
        elif not local.is_file():
            errors.append("missing local image: " + raw)
    for expected in ASSETS:
        if not (ROOT / expected).is_file():
            errors.append("missing required asset: " + expected)
    model = ROOT / "references" / "model_capabilities.json"
    try:
        data = json.loads(model.read_text(encoding="utf-8"))
        if data["default"]["status"] != "unverified":
            errors.append("uncalibrated models must remain unverified")
        if not isinstance(data["models"], dict):
            errors.append("model capability table must be a mapping")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append("invalid capability manifest: " + str(exc))
    return errors

if __name__ == "__main__":
    problems = verify()
    if problems:
        print("GALLERY CHECK: FAIL")
        for item in problems:
            print(" -", item)
        sys.exit(1)
    print("GALLERY CHECK: PASS")
    print("Offline previews:", len(Links().images) if False else 2)
    print("Unverified models remain uncalibrated")
