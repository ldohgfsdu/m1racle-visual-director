#!/usr/bin/env python3
"""Pure-data validation of offline gallery, landing page and SVG assets."""
from __future__ import annotations
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ("gallery/samples/blue.svg", "gallery/samples/mono.svg")

class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.references = []
        self.images = []
    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        tag = tag.lower()
        if tag == "img" and data.get("src"):
            self.images.append(data["src"])
        for name in ("src", "poster", "data"):
            if data.get(name) and tag in ("img", "script", "source", "video", "audio", "iframe", "embed", "object"):
                self.references.append(data[name])
        if tag == "link" and data.get("href"):
            self.references.append(data["href"])
        if data.get("srcset"):
            for item in data["srcset"].split(","):
                self.references.append(item.strip().split()[0])
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

def verify():
    errors = []
    pages = (ROOT / "index.html", ROOT / "gallery/index.html")
    root = ROOT.resolve()
    count = 0
    for page in pages:
        if not page.is_file():
            errors.append("missing " + page.relative_to(ROOT).as_posix())
            continue
        raw = page.read_text(encoding="utf-8")
        parser = Links()
        parser.feed(raw)
        if page.name == "index.html" and page.parent == ROOT:
            if "gallery/index.html" not in raw:
                errors.append("landing page does not link to gallery/index.html")
        else:
            count = len(parser.images)
            if count < 2:
                errors.append("gallery must contain at least two images")
        # A dependency can hide in a CSS import or inline JS as well as in <img>.
        if re.search(r"https?://|(?<!:)//[a-z\d]", raw, re.I):
            errors.append("remote URL in self-contained HTML: " + page.name)
        for rawurl in parser.references:
            parsed = urlsplit(rawurl)
            if parsed.scheme or parsed.netloc or rawurl.startswith("//"):
                errors.append("external gallery dependency: " + rawurl)
                continue
            relative = unquote(parsed.path)
            local = (page.parent / relative).resolve()
            if local != root and root not in local.parents:
                errors.append("gallery path escape: " + rawurl)
            elif not local.is_file():
                errors.append("missing gallery asset: " + rawurl)
    for expected in ASSETS:
        path = ROOT / expected
        if not path.is_file():
            errors.append("missing required asset: " + expected)
            continue
        try:
            xml = ET.parse(path).getroot()
            if xml.tag != "{http://www.w3.org/2000/svg}svg":
                errors.append("not an SVG: " + expected)
            raw = path.read_text(encoding="utf-8")
            if re.search(r"https?://(?!www\\.w3\\.org/2000/svg)", raw, re.I):
                errors.append("external SVG dependency: " + expected)
        except (ET.ParseError, OSError, UnicodeError) as exc:
            errors.append("malformed SVG " + expected + ": " + str(exc))
    model = ROOT / "references/model_capabilities.json"
    try:
        data = json.loads(model.read_text(encoding="utf-8"))
        if data["default"]["status"] != "unverified":
            errors.append("uncalibrated models must remain unverified")
        if not isinstance(data["models"], dict):
            errors.append("model capability table must be a mapping")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append("invalid capability manifest: " + str(exc))
    return errors, count

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    ROOT = parser.parse_args().root.resolve()
    problems, count = verify()
    if problems:
        print("GALLERY CHECK: FAIL")
        for item in problems:
            print(" -", item)
        sys.exit(1)
    print("GALLERY CHECK: PASS")
    print("Offline previews:", count)
    print("Unverified models remain uncalibrated")
