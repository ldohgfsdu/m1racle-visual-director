#!/usr/bin/env python3
"""Synthetic evaluator unit tests. This does not assert image quality or agent success."""
import importlib.util
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("eval_checker", ROOT / "scripts/check_eval_trace.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)
cases = json.loads((ROOT / "evals/cases.json").read_text("utf-8"))["cases"]
records = []
for case in cases:
    records.append({
        "id": case["id"], "route": case["expected_route"], "style": case["expected_style"],
        "invoked": case["expected_active"], "status": case["expected_status"],
        "tool_called": case["expected_status"] == "GENERATED_AND_REVIEWED",
        "tool_call_count": 2 if case["id"] == "E32" else 1 if case["expected_status"] == "GENERATED_AND_REVIEWED" else 0,
        "used_fixtures": [f["path"] for f in case["fixture"]] if case["expected_active"] else [],
        "evidence": {e: True for e in case["required_evidence"]},
        "quality_checks": {e: True for e in case["quality_gate"]},
    })
assert checker.check(records, cases) == [], "synthetic valid format rejected"
records[0]["route"] = "NONE"
assert checker.check(records, cases), "wrong route accepted"
records[0]["route"] = cases[0]["expected_route"]
records[0]["evidence"].pop(cases[0]["required_evidence"][0])
assert checker.check(records, cases), "missing evidence accepted"
records[0]["evidence"][cases[0]["required_evidence"][0]] = True
records[0]["quality_checks"].pop(cases[0]["quality_gate"][0])
assert checker.check(records, cases), "missing visual review accepted"
records[0]["quality_checks"][cases[0]["quality_gate"][0]] = True
retry = next(r for r in records if r["id"] == "E32")
retry["tool_call_count"] = 3
assert checker.check(records, cases), "unbounded retry count was accepted"
print("EVAL CONTRACT UNIT TESTS: PASS (synthetic only; real E2E untested)")
