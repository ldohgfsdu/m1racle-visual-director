#!/usr/bin/env python3
"""Dependency-free validation: explicit invocation, fixed engraving style."""
import argparse
from collections import Counter
from pathlib import Path
import json
import re
import sys
import xml.etree.ElementTree as ET

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
    if not re.search(r'^  version: "?' + re.escape("1.4.2") + r'"?\s*
    used = set()
    evidence_signatures = set()
    near_misses = 0
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
        if not case.get("request") or not case.get("guardrail") or not case.get("required_evidence") or not case.get("pass_criteria"):
            errors.append("%s: incomplete case" % identity)
        signature = tuple(case.get("required_evidence", []))
        if signature in evidence_signatures:
            errors.append("%s: duplicate evidence criteria" % identity)
        evidence_signatures.add(signature)
        if case.get("eval_tag") == "near-miss":
            near_misses += 1
        if case.get("expected_status") != ("NOT_INVOKED" if not active else "PROMPT_ONLY" if identity == "E05" else "GENERATED_AND_REVIEWED"):
            errors.append("%s: invalid expected status" % identity)
        fixture = case.get("fixture")
        if not isinstance(fixture, list):
            errors.append("%s: fixture list missing" % identity)
            fixture = []
        if active and route in ("REF-CREATE", "TRANSFORM", "LOCAL-EDIT", "COMPOSITE") and not fixture:
            errors.append("%s: missing image fixture" % identity)
        if route == "COMPOSITE" and len(fixture) < 2:
            errors.append("%s: composite requires two image fixtures" % identity)
        for image in fixture:
            if not isinstance(image, dict) or not image.get("role") or not image.get("path"):
                errors.append("%s: invalid fixture entry" % identity)
                continue
            path = image["path"]
            if not path.startswith("evals/fixtures/") or ".." in Path(path).parts:
                errors.append("%s: unsafe fixture path" % identity)
                continue
            try:
                xml = ET.parse(ROOT / path).getroot()
                if xml.tag != "{http://www.w3.org/2000/svg}svg":
                    errors.append("%s: invalid SVG fixture" % identity)
            except (ET.ParseError, OSError):
                errors.append("%s: unreadable SVG fixture %s" % (identity, path))
        if active and identity != "E05" and len(case.get("quality_gate", [])) < 5:
            errors.append("%s: missing quality gates" % identity)
        if active and (route == "NONE" or not style):
            errors.append("%s: active but no engraving route/style" % identity)
        if active is False and (route != "NONE" or style is not None):
            errors.append("%s: inactive but routed" % identity)
        counts[route] += 1
    for route in ROUTES:
        if counts[route] < 2:
            errors.append("Route coverage too low: %s (%d)" % (route, counts[route]))
    if len(cases) < 30:
        errors.append("Expected 30 contract cases including near-miss negatives")
    if near_misses < 6:
        errors.append("Expected at least six near-miss negative cases")
    try:
        payload = json.loads((ROOT / "evals/cases.json").read_text("utf-8"))
        if payload.get("schema_version") != "1.4.2":
            errors.append("cases.json schema_version does not match SKILL.md")
    except (OSError, ValueError):
        errors.append("cases.json unreadable")
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
, header[1], re.M):
        errors.append("SKILL.md version does not match eval schema 1.4.2")
    rubric = ROOT / "evals/rubric.json"
    try:
        rubric_data = json.loads(rubric.read_text(encoding="utf-8"))
        if not all(key in rubric_data["style_checks"] for key in ("linework","contour_hatching","cross_hatching","guilloche","limited_inks")):
            errors.append("style rubric has missing engraving checks")
    except (OSError, ValueError, KeyError, TypeError):
        errors.append("missing or invalid evaluation rubric")
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
