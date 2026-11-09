#!/usr/bin/env python3
"""Weighted calculator for documented human visual review; does not inspect images."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUBRIC = json.loads((ROOT / "references/visual_scorecard.json").read_text(encoding="utf-8"))


def score_record(record: dict, rubric: dict = RUBRIC) -> dict:
    categories = rubric["categories"]
    scores = record.get("scores", {})
    flags = record.get("flags", {})
    missing, invalid, gate_failures = [], [], []
    weighted = 0.0
    for category in categories:
        ident = category["id"]
        item = scores.get(ident)
        if not isinstance(item, dict) or "score" not in item or not str(item.get("evidence", "")).strip():
            missing.append(ident)
            continue
        value = item["score"]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 5:
            invalid.append(ident)
            continue
        weighted += float(value) / 5 * category["weight"]
        if "gate_min" in category and value < category["gate_min"]:
            gate_failures.append({"id": ident, "score": value, "minimum": category["gate_min"]})
    missing_flags = [name for name in rubric["hard_fail_flags"] if name not in flags]
    active_flags = [name for name in rubric["hard_fail_flags"] if flags.get(name) is True]
    if missing or invalid or missing_flags:
        status, total = "UNVERIFIED", None
    else:
        total = round(weighted, 1)
        if active_flags or gate_failures or total < rubric["thresholds"]["conditional"]:
            status = "REJECTED"
        elif total < rubric["thresholds"]["pass"]:
            status = "CONDITIONAL"
        else:
            status = "PASS"
    return {
        "score": total, "status": status, "gate_failures": gate_failures,
        "hard_fail_flags": active_flags, "missing_categories": missing,
        "invalid_categories": invalid, "missing_flags": missing_flags,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", required=True, help="JSON record with scores, evidence and hard-fail flags")
    args = parser.parse_args(argv)
    try:
        record = json.loads(Path(args.record).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    result = score_record(record)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"PASS", "CONDITIONAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
