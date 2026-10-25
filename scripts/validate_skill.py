#!/usr/bin/env python3
"""Dependency-free validation: explicit invocation, fixed engraving style."""
import argparse
from collections import Counter
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
NAME = "m1racle-visual-director"
ROUTES = {"NONE", "T2I", "REF-CREATE", "TRANSFORM", "LOCAL-EDIT", "COMPOSITE"}
STYLES = {None, "banknote-intaglio", "steel-engraving-mono"}

def verify():
    errors = []
    skill = ROOT / "SKILL.md"
    if not skill.is_file():
        return ["SKILL.md missing"]
    raw = skill.read_text(encoding="utf-8")
    header = re.match(r"\A---\n(.*?)\n---\n", raw, re.S)
    if not header:
        return ["YAML frontmatter missing"]
    match = re.search(r"^name:\s*(\S+)", header[1], re.M)
    name = match[1] if match else None
    desc = re.search(r"^description:\s*(.+)", header[1], re.M)
    if name != NAME:
        errors.append("Expected name %s, got %s" % (NAME, name))
    # The bundle can be checked in any staging directory; metadata name is authoritative.
    if not desc or not 1 <= len(desc[1]) <= 1024:
        errors.append("Missing/invalid description")
    if not re.search(r"^disable-model-invocation:\s*true\s*$", header[1], re.M):
        errors.append("Explicit-only frontmatter flag missing")
    for rel in re.findall(r"\]\((references/[^)#]+|evals/[^)#]+|gallery/[^)#]+)\)", raw):
        if not (ROOT / rel).is_file():
            errors.append("Broken link: " + rel)
    for term in ("显式", "不自动", "T2I", "REF-CREATE", "TRANSFORM", "LOCAL-EDIT", "COMPOSITE", "Guilloché", "直接"):
        if term not in raw:
            errors.append("Missing policy token: " + term)
    try:
        cases = json.loads((ROOT / "evals/cases.json").read_text(encoding="utf-8"))["cases"]
    except (ValueError, KeyError, OSError) as exc:
        return errors + ["Invalid cases: %s" % exc]
    counts = Counter()
    used = set()
    for case in cases:
        identity = case.get("id")
        active, route, style = case.get("expected_active"), case.get("expected_route"), case.get("expected_style")
        if not identity or identity in used:
            errors.append("Invalid ID: %s" % identity)
        used.add(identity)
        if not isinstance(active, bool):
            errors.append("%s: active flag missing" % identity)
        if route not in ROUTES:
            errors.append("%s: invalid route %s" % (identity, route))
        if style not in STYLES:
            errors.append("%s: non-engraving style %s" % (identity, style))
        if not case.get("request") or not case.get("guardrail") or not case.get("required_evidence"):
            errors.append("%s: incomplete case" % identity)
        if active and (route == "NONE" or not style):
            errors.append("%s: active but no engraving route/style" % identity)
        if active is False and (route != "NONE" or style is not None):
            errors.append("%s: inactive but routed" % identity)
        counts[route] += 1
    for route in ROUTES:
        if counts[route] < 2:
            errors.append("Route coverage too low: %s (%d)" % (route, counts[route]))
    if len(cases) < 24:
        errors.append("Expected at least 24 fixtures")
    return errors

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate skill data without running target code")
    parser.add_argument("--root", type=Path, default=ROOT)
    ROOT = parser.parse_args().root.resolve()
    errors = verify()
    if errors:
        print("STATIC CHECK: FAIL")
        for error in errors:
            print(" -", error)
        sys.exit(1)
    print("STATIC CHECK: PASS")
    print("Skill:", NAME)
    print("Evaluation fixtures:", len(json.loads((ROOT / "evals/cases.json").read_text(encoding="utf-8"))["cases"]))
    print("Contract: explicit invocation, fixed engraving style")
    print("NOTE: actual image generation is not tested")
