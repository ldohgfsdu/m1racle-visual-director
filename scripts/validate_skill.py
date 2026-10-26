#!/usr/bin/env python3
"""Validate the static Skill and evaluation contract; never execute target scripts."""
from __future__ import annotations

import argparse
import json
import re
import sys
import struct
import zlib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "m1racle-visual-director"
VERSION = "1.4.2"
ROUTES = {"NONE", "T2I", "REF-CREATE", "TRANSFORM", "LOCAL-EDIT", "COMPOSITE"}
STYLES = {None, "banknote-intaglio", "steel-engraving-mono"}
QUALITY = {"linework", "contour_hatching", "cross_hatching", "guilloche",
           "limited_inks", "subject_integrity", "no_unrequested_text"}

def verify(root: Path = None):
    root = (root or ROOT).resolve()
    errors = []
    skill = root / "SKILL.md"
    if not skill.is_file():
        return ["SKILL.md missing"]
    raw = skill.read_text(encoding="utf-8")
    head = re.match(r"\A---\n(.*?)\n---\n", raw, re.S)
    if not head:
        return ["YAML frontmatter missing"]
    front = head.group(1)
    if not re.search(r"(?m)^name:\s*" + re.escape(NAME) + r"\s*$", front):
        errors.append("SKILL metadata.name mismatch")
    if 'version: "' + VERSION + '"' not in front:
        errors.append("SKILL metadata.version mismatch")
    if not re.search(r"(?m)^disable-model-invocation:\s*true\s*$", front):
        errors.append("explicit-only activation flag missing")
    desc = re.search(r"(?m)^description:\s*(.+)$", front)
    if not desc or not 1 <= len(desc.group(1)) <= 1024:
        errors.append("missing or invalid description")
    for rel in re.findall(r"\]\((references/[^)#]+|evals/[^)#]+|gallery/[^)#]+)\)", raw):
        if not (root / rel).is_file():
            errors.append("broken Skill link: " + rel)
    for word in ("显式", "不自动", "T2I", "REF-CREATE", "TRANSFORM",
                 "LOCAL-EDIT", "COMPOSITE", "Guilloché", "直接"):
        if word not in raw:
            errors.append("missing policy token: " + word)
    try:
        payload = json.loads((root / "evals/cases.json").read_text("utf-8"))
        cases = payload["cases"]
        if payload.get("schema_version") != VERSION or not isinstance(cases, list):
            return errors + ["eval schema/version mismatch"]
        rubric = json.loads((root / "evals/rubric.json").read_text("utf-8"))
        if rubric.get("schema_version") != VERSION or not QUALITY.issubset(rubric["style_checks"]):
            errors.append("eval rubric incomplete")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return errors + ["evaluation data missing or invalid: " + str(exc)]
    if len(cases) < 30:
        errors.append("expected >= 30 eval scenarios")
    ids, signatures = set(), set()
    routes = Counter()
    near = 0
    for case in cases:
        ident = case.get("id")
        if not ident or ident in ids:
            errors.append("duplicate or empty ID: " + str(ident))
        ids.add(ident)
        active = case.get("expected_active")
        route = case.get("expected_route")
        style = case.get("expected_style")
        if not isinstance(active, bool):
            errors.append(str(ident) + ": expected_active must be boolean")
        if route not in ROUTES:
            errors.append(str(ident) + ": invalid route")
        if style not in STYLES:
            errors.append(str(ident) + ": invalid style")
        if active and (route == "NONE" or style is None):
            errors.append(str(ident) + ": active route/style mismatch")
        if active is False and (route != "NONE" or style is not None):
            errors.append(str(ident) + ": inactive route/style mismatch")
        if not case.get("request") or not case.get("guardrail") or not case.get("pass_criteria"):
            errors.append(str(ident) + ": incomplete scenario")
        evidence = case.get("required_evidence")
        if not isinstance(evidence, list) or len(evidence) < 3 or not all(isinstance(s, str) for s in evidence):
            errors.append(str(ident) + ": missing evidence")
            evidence = []
        signature = tuple(evidence)
        if signature in signatures:
            errors.append(str(ident) + ": duplicated evidence signature")
        signatures.add(signature)
        expected_status = "NOT_INVOKED" if not active else "PROMPT_ONLY" if ident == "E05" else "GENERATED_AND_REVIEWED"
        if case.get("expected_status") != expected_status:
            errors.append(str(ident) + ": incorrect expected_status")
        if case.get("eval_tag") == "near-miss":
            near += 1
            if active:
                errors.append(str(ident) + ": near-miss activated")
        fixtures = case.get("fixture")
        if not isinstance(fixtures, list):
            errors.append(str(ident) + ": fixture field must be array")
            fixtures = []
        if active and route in {"REF-CREATE", "TRANSFORM", "LOCAL-EDIT", "COMPOSITE"} and not fixtures:
            errors.append(str(ident) + ": missing image fixture")
        if route == "COMPOSITE" and len(fixtures) < 2:
            errors.append(str(ident) + ": COMPOSITE needs two image sources")
        for attachment in fixtures:
            if not isinstance(attachment, dict) or not attachment.get("role") or not isinstance(attachment.get("path"), str):
                errors.append(str(ident) + ": invalid fixture record")
                continue
            rel = attachment["path"]
            if not rel.startswith("evals/fixtures/") or ".." in Path(rel).parts:
                errors.append(str(ident) + ": unsafe fixture path")
                continue
            try:
                if not rel.endswith(".png"):
                    errors.append(str(ident) + ": fixture must be PNG bitmap")
                    continue
                content = (root / rel).read_bytes()
                if not content.startswith(b"\x89PNG\r\n\x1a\n") or len(content) < 45:
                    errors.append(str(ident) + ": invalid PNG signature")
                    continue
                pos = 8
                png_chunks = []
                while pos + 12 <= len(content):
                    length = struct.unpack_from(">I", content, pos)[0]
                    tag = content[pos + 4:pos + 8]
                    if length > len(content) - pos - 12:
                        raise ValueError("truncated PNG chunk")
                    body = content[pos + 8:pos + 8 + length]
                    digest = struct.unpack_from(">I", content, pos + 8 + length)[0]
                    if (zlib.crc32(tag + body) & 0xffffffff) != digest:
                        raise ValueError("PNG CRC mismatch")
                    png_chunks.append(tag)
                    pos += 12 + length
                    if tag == b"IEND":
                        break
                if png_chunks[:2] != [b"IHDR", b"IDAT"] or png_chunks[-1:] != [b"IEND"] or pos != len(content):
                    raise ValueError("PNG missing required chunks")
                width, height = struct.unpack_from(">II", content, 16)
                if not (64 <= width <= 4096 and 64 <= height <= 4096):
                    raise ValueError("fixture dimensions invalid")
            except (OSError, ValueError, struct.error) as exc:
                errors.append(str(ident) + ": damaged PNG fixture " + rel + ": " + str(exc))
        checks = case.get("quality_gate")
        if not isinstance(checks, list):
            errors.append(str(ident) + ": missing quality_gate array")
        elif active and ident != "E05" and not QUALITY.issubset(checks):
            errors.append(str(ident) + ": missing image quality checks")
        routes[route] += 1
    for route in ROUTES:
        if routes[route] < 2:
            errors.append("insufficient route coverage: " + route)
    if near < 6:
        errors.append("requires >= 6 semantically near negative examples")
    return errors

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Static safe verifier for M1racle Visual Director")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    issues = verify(args.root)
    if issues:
        print("STATIC CHECK: FAIL")
        for issue in issues:
            print(" -", issue)
        sys.exit(1)
    cases = json.loads((args.root / "evals/cases.json").read_text("utf-8"))["cases"]
    print("STATIC CHECK: PASS")
    print("Skill:", NAME, "version:", VERSION)
    print("Evaluation cases:", len(cases))
    print("NOTE: actual image generation remains untested by this validator")
