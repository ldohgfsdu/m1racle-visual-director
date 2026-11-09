#!/usr/bin/env python3
"""Evidence-bound human visual score calculator, not an image quality model."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUBRIC = json.loads((ROOT / "references/visual_scorecard.json").read_text(encoding="utf-8"))
TECHNIQUES = {"T01", "T02", "T03", "T04", "T05"}
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_SOF = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}


def image_dimensions(path: Path) -> tuple[int, int]:
    """Read PNG/JPEG intrinsic dimensions without a third-party dependency."""
    with path.open("rb") as handle:
        data = handle.read()
    if data.startswith(PNG_MAGIC):
        if len(data) < 24 or data[12:16] != b"IHDR":
            raise ValueError("Invalid PNG header: " + str(path))
        width, height = struct.unpack(">II", data[16:24])
    elif data.startswith(b"\xff\xd8"):
        pos = 2
        width = height = 0
        while pos + 4 <= len(data):
            if data[pos] != 0xFF:
                raise ValueError("Malformed JPEG marker: " + str(path))
            while pos < len(data) and data[pos] == 0xFF:
                pos += 1
            if pos >= len(data):
                break
            marker = data[pos]
            pos += 1
            if marker in {0x01, *range(0xD0, 0xDA)}:
                continue
            if marker == 0xDA:
                break
            if pos + 2 > len(data):
                break
            length = int.from_bytes(data[pos:pos + 2], "big")
            if length < 2 or pos + length > len(data):
                break
            if marker in JPEG_SOF and length >= 7:
                height = int.from_bytes(data[pos + 3:pos + 5], "big")
                width = int.from_bytes(data[pos + 5:pos + 7], "big")
                break
            pos += length
        if not width or not height:
            raise ValueError("JPEG dimensions missing: " + str(path))
    else:
        raise ValueError("Unsupported image type; expected PNG or JPEG: " + str(path))
    if not 1 <= width <= 30000 or not 1 <= height <= 30000:
        raise ValueError("Invalid intrinsic image dimensions: " + str(path))
    return width, height


def verify_evidence(record: dict, source: Path, output: Path) -> dict:
    """Bind review claims to real, distinct source and output image bytes."""
    if not isinstance(record, dict):
        raise ValueError("Score record must be a JSON object")
    if not isinstance(record.get("run_id"), str) or not record["run_id"].strip():
        raise ValueError("Missing nonempty run_id")
    if record.get("technique") not in TECHNIQUES:
        raise ValueError("Unknown or missing technique")
    if record.get("output_kind") != "single_image_edit":
        raise ValueError("Only single_image_edit outputs can be scored")
    if not isinstance(record.get("model_or_tool"), str) or not record["model_or_tool"].strip():
        raise ValueError("Missing model_or_tool provenance")
    if source.resolve() == output.resolve():
        raise ValueError("Source and output paths must differ")
    dims = []
    hashes = []
    for key, path in (("source_sha256", source), ("output_sha256", output)):
        if not path.is_file():
            raise ValueError("Missing image: " + str(path))
        data = path.read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        if actual != record.get(key):
            raise ValueError("Image bytes do not match " + key)
        dims.append(image_dimensions(path))
        hashes.append(actual)
    if hashes[0] == hashes[1]:
        raise ValueError("Unchanged input is not a valid edited output")
    (sw, sh), (ow, oh) = dims
    drift = abs((ow / oh) / (sw / sh) - 1) * 100
    return {
        "verified": True, "source_dimensions": [sw, sh], "output_dimensions": [ow, oh],
        "aspect_ratio_drift_pct": round(drift, 3),
        "geometry_ratio_gate_failed": drift > 1.0,
        "basis": "Actual image byte hashes and file headers; visual semantics remain human-reviewed",
    }


def score_record(record: dict, rubric: dict = RUBRIC, *, bound_evidence: dict | None = None) -> dict:
    """Calculate only documented human scores; unbound inputs cannot PASS."""
    categories = rubric["categories"]
    scores = record.get("scores", {})
    flags = record.get("flags", {})
    if not isinstance(scores, dict):
        scores = {}
    if not isinstance(flags, dict):
        flags = {}
    missing, invalid, gate_failures = [], [], []
    weighted = 0.0
    for category in categories:
        ident = category["id"]
        item = scores.get(ident)
        if not isinstance(item, dict) or "score" not in item or not isinstance(item.get("evidence"), str) or not item["evidence"].strip():
            missing.append(ident)
            continue
        value = item["score"]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 5:
            invalid.append(ident)
            continue
        weighted += float(value) / 5 * category["weight"]
        if "gate_min" in category and value < category["gate_min"]:
            gate_failures.append({"id": ident, "score": value, "minimum": category["gate_min"]})
    missing_flags = [name for name in rubric["hard_fail_flags"] if name not in flags]
    invalid_flags = [name for name in flags if name not in rubric["hard_fail_flags"] or type(flags[name]) is not bool]
    active_flags = [name for name in rubric["hard_fail_flags"] if flags.get(name) is True]
    metadata_verified = bound_evidence is not None and bound_evidence.get("verified") is True
    geometry_ratio_gate_failed = bool(metadata_verified and bound_evidence.get("geometry_ratio_gate_failed"))
    if geometry_ratio_gate_failed:
        active_flags = list(dict.fromkeys(active_flags + ["major_geometry_or_crop_change"]))
    unknown_categories = sorted(set(scores) - {x["id"] for x in categories})
    if missing or invalid or missing_flags or invalid_flags or unknown_categories or not metadata_verified:
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
        "invalid_categories": invalid, "unknown_categories": unknown_categories,
        "missing_flags": missing_flags, "invalid_flags": invalid_flags,
        "evidence_verified": metadata_verified,
        "geometry_ratio_gate_failed": geometry_ratio_gate_failed,
        "source_dimensions": bound_evidence.get("source_dimensions") if metadata_verified else None,
        "output_dimensions": bound_evidence.get("output_dimensions") if metadata_verified else None,
        "aspect_ratio_drift_pct": bound_evidence.get("aspect_ratio_drift_pct") if metadata_verified else None,
        "disclaimer": "Human observations are not independently proven by file hashes or by this calculator.",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", required=True, help="Human review JSON with source/output SHA-256")
    parser.add_argument("--source", required=True, type=Path, help="Actual content-source PNG/JPEG")
    parser.add_argument("--output", required=True, type=Path, help="Actual single edited PNG/JPEG")
    args = parser.parse_args(argv)
    try:
        record = json.loads(Path(args.record).read_text(encoding="utf-8"))
        evidence = verify_evidence(record, args.source, args.output)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.error(str(exc))
    result = score_record(record, bound_evidence=evidence)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"PASS", "CONDITIONAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
