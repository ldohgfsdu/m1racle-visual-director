"""Synthetic score math and real-byte provenance regressions (not visual model tests)."""
import hashlib
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import visual_scorecard as s


def make_record(score=5, overrides=None, flags=None):
    values = {}
    for category in s.RUBRIC["categories"]:
        values[category["id"]] = {"score": score, "evidence": "对应区域的可见结构与纹理由人工检查"}
    values.update(overrides or {})
    return {
        "run_id": "test-case-001", "technique": "T01",
        "output_kind": "single_image_edit", "model_or_tool": "synthetic-unit-test",
        "scores": values,
        "flags": {name: False for name in s.RUBRIC["hard_fail_flags"]} | (flags or {}),
    }


MATH_EVIDENCE = {"verified": True, "aspect_ratio_drift_pct": 0.0,
                 "geometry_ratio_gate_failed": False, "source_binding_documented": True,
                 "source_dimensions": [8, 4], "output_dimensions": [8, 4]}


def attach_binding(record):
    record["source_binding"] = {
        "status": "documented", "role": "content_source",
        "source_sha256": record["source_sha256"], "run_id": record["run_id"],
        "tool_input_trace": "SYNTHETIC test invocation, not evidence of a real model call",
    }



def image(w, h, color=(1, 2, 3)):
    def chunk(kind, payload):
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)
    raw = (b"\x00" + bytes(color) * w) * h
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


class VisualScorecardTests(unittest.TestCase):
    def test_weights_sum_to_one_hundred(self):
        self.assertEqual(sum(x["weight"] for x in s.RUBRIC["categories"]), 100)

    def test_unbound_perfect_human_scores_are_unverified(self):
        result = s.score_record(make_record())
        self.assertEqual(result["status"], "UNVERIFIED")
        self.assertIsNone(result["score"])

    def test_mathematically_perfect_bound_score(self):
        result = s.score_record(make_record(), bound_evidence=MATH_EVIDENCE)
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["status"], "PASS")

    def test_gate_failure_rejects_even_when_weighted_score_is_high(self):
        row = {"score": 3, "evidence": "田埂线有局部变形"}
        result = s.score_record(make_record(overrides={"geometry_composition": row}), bound_evidence=MATH_EVIDENCE)
        self.assertGreaterEqual(result["score"], 85)
        self.assertEqual(result["status"], "REJECTED")

    def test_unauthorized_frame_is_hard_rejection(self):
        result = s.score_record(make_record(flags={"unauthorized_frame": True}), bound_evidence=MATH_EVIDENCE)
        self.assertEqual(result["status"], "REJECTED")

    def test_report_output_is_hard_rejected_even_with_perfect_score_and_matching_dimensions(self):
        for flag in ('wrong_output_type', 'unauthorized_report_layout'):
            with self.subTest(flag=flag):
                result = s.score_record(make_record(flags={flag: True}), bound_evidence=MATH_EVIDENCE)
                self.assertEqual(result['score'], 100)
                self.assertEqual(result['status'], 'REJECTED')
                self.assertIn(flag, result['hard_fail_flags'])

    def test_report_flags_must_be_reviewed_not_omitted(self):
        record = make_record()
        del record['flags']['wrong_output_type']
        result = s.score_record(record, bound_evidence=MATH_EVIDENCE)
        self.assertEqual(result['status'], 'UNVERIFIED')
        self.assertIn('wrong_output_type', result['missing_flags'])

    def test_eighty_points_is_conditional(self):
        result = s.score_record(make_record(score=4), bound_evidence=MATH_EVIDENCE)
        self.assertEqual(result["score"], 80)
        self.assertEqual(result["status"], "CONDITIONAL")

    def test_missing_evidence_is_unverified_not_zero(self):
        record = make_record()
        record["scores"]["source_color_fidelity"]["evidence"] = ""
        result = s.score_record(record, bound_evidence=MATH_EVIDENCE)
        self.assertIsNone(result["score"])
        self.assertEqual(result["status"], "UNVERIFIED")

    def test_missing_or_fake_flags_are_unverified(self):
        record = make_record()
        record["flags"]["unauthorized_frame"] = "false"
        result = s.score_record(record, bound_evidence=MATH_EVIDENCE)
        self.assertEqual(result["status"], "UNVERIFIED")
        self.assertIn("unauthorized_frame", result["invalid_flags"])
        del record["flags"]["unauthorized_frame"]
        result = s.score_record(record, bound_evidence=MATH_EVIDENCE)
        self.assertIn("unauthorized_frame", result["missing_flags"])

    def test_nonfinite_and_unknown_score_rejected(self):
        record = make_record()
        record["scores"]["geometry_composition"]["score"] = float("nan")
        record["scores"]["invented"] = {"score": 5, "evidence": "fake"}
        result = s.score_record(record, bound_evidence=MATH_EVIDENCE)
        self.assertEqual(result["status"], "UNVERIFIED")
        self.assertIn("geometry_composition", result["invalid_categories"])
        self.assertIn("invented", result["unknown_categories"])

    def test_real_png_hash_binding(self):
        with tempfile.TemporaryDirectory() as td:
            src, out = Path(td) / "source.png", Path(td) / "output.png"
            src.write_bytes(image(128, 64))
            out.write_bytes(image(256, 128, (4, 5, 6)))
            record = make_record()
            record["source_sha256"] = hashlib.sha256(src.read_bytes()).hexdigest()
            record["output_sha256"] = hashlib.sha256(out.read_bytes()).hexdigest()
            attach_binding(record)
            evidence = s.verify_evidence(record, src, out)
            self.assertTrue(evidence["verified"])
            self.assertEqual(evidence["source_dimensions"], [128, 64])
            self.assertFalse(evidence["geometry_ratio_gate_failed"])
            self.assertEqual(s.score_record(record, bound_evidence=evidence)["status"], "PASS")

    def test_missing_source_binding_blocks_pass_even_with_perfect_scores(self):
        with tempfile.TemporaryDirectory() as td:
            src, out = Path(td) / "source.png", Path(td) / "output.png"
            src.write_bytes(image(128, 64))
            out.write_bytes(image(128, 64, (4, 5, 6)))
            record = make_record()
            record["source_sha256"] = hashlib.sha256(src.read_bytes()).hexdigest()
            record["output_sha256"] = hashlib.sha256(out.read_bytes()).hexdigest()
            evidence = s.verify_evidence(record, src, out)
            self.assertFalse(evidence["source_binding_documented"])
            result = s.score_record(record, bound_evidence=evidence)
            self.assertEqual(result["status"], "UNVERIFIED")
            self.assertIsNone(result["score"])
            attach_binding(record)
            record["source_binding"]["source_sha256"] = "0" * 64
            evidence = s.verify_evidence(record, src, out)
            self.assertFalse(evidence["source_binding_documented"])
            self.assertEqual(s.score_record(record, bound_evidence=evidence)["status"], "UNVERIFIED")
            record["source_binding"]["source_sha256"] = record["source_sha256"]
            evidence = s.verify_evidence(record, src, out)
            self.assertTrue(evidence["source_binding_documented"])
            self.assertEqual(s.score_record(record, bound_evidence=evidence)["status"], "PASS")

    def test_binding_claim_for_different_run_does_not_pass(self):
        record = make_record()
        record["source_sha256"] = "a" * 64
        attach_binding(record)
        record["source_binding"]["run_id"] = "different-run"
        self.assertFalse(s.documented_source_binding(record, record["source_sha256"]))

    def test_bad_ratio_fails_even_without_tool_binding_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            src, out = Path(td) / "source.png", Path(td) / "output.png"
            src.write_bytes(image(96, 128))
            out.write_bytes(image(128, 96, (4, 5, 6)))
            record = make_record()
            record["source_sha256"] = hashlib.sha256(src.read_bytes()).hexdigest()
            record["output_sha256"] = hashlib.sha256(out.read_bytes()).hexdigest()
            evidence = s.verify_evidence(record, src, out)
            result = s.score_record(record, bound_evidence=evidence)
            self.assertEqual(result["status"], "REJECTED")
            self.assertTrue(result["geometry_ratio_gate_failed"])
            self.assertFalse(result["source_binding_documented"])

    def test_real_bytes_mismatch_is_not_scored(self):
        with tempfile.TemporaryDirectory() as td:
            src, out = Path(td) / "source.png", Path(td) / "output.png"
            src.write_bytes(image(128, 64))
            out.write_bytes(image(128, 64, (4, 5, 6)))
            record = make_record()
            record["source_sha256"] = hashlib.sha256(src.read_bytes()).hexdigest()
            record["output_sha256"] = "0" * 64
            with self.assertRaisesRegex(ValueError, "output_sha256"):
                s.verify_evidence(record, src, out)

    def test_same_image_bytes_do_not_verify(self):
        with tempfile.TemporaryDirectory() as td:
            src, out = Path(td) / "source.png", Path(td) / "output.png"
            src.write_bytes(image(128, 64))
            out.write_bytes(src.read_bytes())
            record = make_record()
            record["source_sha256"] = record["output_sha256"] = hashlib.sha256(src.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError, "Unchanged"):
                s.verify_evidence(record, src, out)

    def test_wrong_aspect_ratio_rejects_despite_five_stars(self):
        with tempfile.TemporaryDirectory() as td:
            src, out = Path(td) / "source.png", Path(td) / "report.png"
            src.write_bytes(image(128, 68))
            out.write_bytes(image(150, 100, (4, 5, 6)))
            record = make_record()
            record["source_sha256"] = hashlib.sha256(src.read_bytes()).hexdigest()
            record["output_sha256"] = hashlib.sha256(out.read_bytes()).hexdigest()
            attach_binding(record)
            evidence = s.verify_evidence(record, src, out)
            self.assertTrue(evidence["geometry_ratio_gate_failed"])
            result = s.score_record(record, bound_evidence=evidence)
            self.assertEqual(result["score"], 100)
            self.assertEqual(result["status"], "REJECTED")
            self.assertIn("major_geometry_or_crop_change", result["hard_fail_flags"])

    def test_missing_provenance_and_collage_cannot_be_verified(self):
        with tempfile.TemporaryDirectory() as td:
            src, out = Path(td) / "source.png", Path(td) / "output.png"
            src.write_bytes(image(128, 64))
            out.write_bytes(image(128, 64, (4, 5, 6)))
            record = make_record()
            record["source_sha256"] = hashlib.sha256(src.read_bytes()).hexdigest()
            record["output_sha256"] = hashlib.sha256(out.read_bytes()).hexdigest()
            record["output_kind"] = "infographic_report"
            with self.assertRaisesRegex(ValueError, "single_image_edit"):
                s.verify_evidence(record, src, out)
            record["output_kind"] = "single_image_edit"
            record["run_id"] = ""
            with self.assertRaisesRegex(ValueError, "run_id"):
                s.verify_evidence(record, src, out)

    def test_repo_jpeg_header_is_supported(self):
        path = ROOT / "assets/examples/I01_blue_coastal_architecture.jpg"
        width, height = s.image_dimensions(path)
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)


if __name__ == "__main__":
    unittest.main()
