#!/usr/bin/env python3
"""Compare externally supplied, actual Agent trace evidence against eval contracts."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def check(records, cases):
    issues = []
    indexed = {}
    for r in records:
        if r.get("id") in indexed:
            issues.append("duplicate result: " + str(r.get("id")))
        indexed[r.get("id")] = r
    for case in cases:
        ident = case["id"]
        r = indexed.get(ident)
        if not isinstance(r, dict):
            issues.append(ident + ": missing real run record")
            continue
        for key in ("route", "style"):
            if r.get(key) != case["expected_" + key]:
                issues.append(ident + ": wrong " + key)
        if bool(r.get("invoked")) != case["expected_active"]:
            issues.append(ident + ": invocation mismatch")
        if r.get("status") != case["expected_status"]:
            issues.append(ident + ": wrong status")
        want_tool = case["expected_status"] == "GENERATED_AND_REVIEWED"
        if bool(r.get("tool_called")) != want_tool:
            issues.append(ident + ": image tool call mismatch")
        expected_files = sorted(f["path"] for f in case.get("fixture", []))
        actual_files = sorted(r.get("used_fixtures", []))
        if case["expected_active"] and expected_files != actual_files:
            issues.append(ident + ": missing/mismatched input fixtures")
        if "exactly_one_targeted_retry" in case["required_evidence"] and r.get("tool_call_count") != 2:
            issues.append(ident + ": retry count must be exactly two tool calls")
        if r.get("tool_call_count", 0) > 0 and not r.get("tool_called"):
            issues.append(ident + ": contradictory tool trace")
        for criterion in case["required_evidence"]:
            if criterion == "engraving_style":
                if not all(r.get("quality_checks", {}).get(key) is True for key in ("linework","contour_hatching","cross_hatching","guilloche","limited_inks")):
                    issues.append(ident + ": engraving style evidence not supported by quality checks")
            elif r.get("evidence", {}).get(criterion) is not True:
                issues.append(ident + ": missing evidence " + criterion)
        for check_id in case.get("quality_gate", []):
            if r.get("quality_checks", {}).get(check_id) is not True:
                issues.append(ident + ": quality gate not proven " + check_id)
    for ident in indexed:
        if not any(c["id"] == ident for c in cases):
            issues.append("unknown result id: " + str(ident))
    return issues

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--results", required=True, type=Path, help="Actual recorded Agent executions, JSON with results[]")
    p.add_argument("--cases", type=Path, default=ROOT / "evals/cases.json")
    args = p.parse_args()
    cases = json.loads(args.cases.read_text("utf-8"))["cases"]
    records = json.loads(args.results.read_text("utf-8"))["results"]
    issues = check(records, cases)
    if issues:
        print("EVAL TRACE CHECK: FAIL")
        for issue in issues:
            print(" -", issue)
        return 1
    print("EVAL TRACE CHECK: PASS (%s actual cases supplied; visual checks reviewer-attested)" % len(records))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
