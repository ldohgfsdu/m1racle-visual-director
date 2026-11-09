import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import visual_scorecard as s


def make_record(score=5, overrides=None, flags=None):
    values = {}
    for category in s.RUBRIC["categories"]:
        values[category["id"]] = {"score": score, "evidence": "直接观察并记录了对应区域"}
    values.update(overrides or {})
    return {
        "scores": values,
        "flags": {name: False for name in s.RUBRIC["hard_fail_flags"]} | (flags or {}),
    }


class VisualScorecardTests(unittest.TestCase):
    def test_weights_sum_to_one_hundred(self):
        self.assertEqual(sum(x["weight"] for x in s.RUBRIC["categories"]), 100)

    def test_perfect_evidence_scores_one_hundred_and_passes(self):
        result = s.score_record(make_record())
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["status"], "PASS")

    def test_gate_failure_rejects_even_when_weighted_score_is_high(self):
        result = s.score_record(make_record(overrides={"geometry_composition": {"score": 3, "evidence": "屋顶轮廓明显改变"}}))
        self.assertGreaterEqual(result["score"], 85)
        self.assertEqual(result["status"], "REJECTED")
        self.assertEqual(result["gate_failures"][0]["id"], "geometry_composition")

    def test_unauthorized_frame_is_hard_rejection(self):
        result = s.score_record(make_record(flags={"unauthorized_frame": True}))
        self.assertEqual(result["status"], "REJECTED")
        self.assertIn("unauthorized_frame", result["hard_fail_flags"])

    def test_eighty_points_is_conditional(self):
        result = s.score_record(make_record(score=4))
        self.assertEqual(result["score"], 80)
        self.assertEqual(result["status"], "CONDITIONAL")

    def test_missing_evidence_is_unverified_not_zero(self):
        data = make_record()
        data["scores"]["source_color_fidelity"]["evidence"] = ""
        result = s.score_record(data)
        self.assertIsNone(result["score"])
        self.assertEqual(result["status"], "UNVERIFIED")
        self.assertIn("source_color_fidelity", result["missing_categories"])

    def test_missing_hard_fail_flag_is_unverified(self):
        data = make_record()
        del data["flags"]["unauthorized_recoloring"]
        result = s.score_record(data)
        self.assertEqual(result["status"], "UNVERIFIED")
        self.assertIn("unauthorized_recoloring", result["missing_flags"])

    def test_invalid_scores_are_unverified(self):
        data = make_record()
        data["scores"]["geometry_composition"]["score"] = 6
        result = s.score_record(data)
        self.assertEqual(result["status"], "UNVERIFIED")
        self.assertIn("geometry_composition", result["invalid_categories"])


if __name__ == "__main__":
    unittest.main()
