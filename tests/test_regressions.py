"""Behavior regressions for user constraints, not checks for decorative wording."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import prompt_builder as p


class ConstraintRegressions(unittest.TestCase):
    def test_negated_blossoms_do_not_select_blossom_profile(self):
        self.assertNotEqual(p.select_profile("冬天的古寺，不要樱花")[0], "I07")

    def test_negated_people_do_not_select_portrait(self):
        self.assertNotEqual(p.select_profile("不要人物、肖像、学者，只画一只猫")[0], "I05")

    def test_english_negation(self):
        self.assertNotEqual(p.select_profile("a ceramic cup, without cherry blossoms")[0], "I07")

    def test_english_substring_is_not_a_word(self):
        self.assertNotEqual(p.select_profile("airport")[0], "I08")
        self.assertEqual(p.select_profile("portrait")[1]["I08"], 0)

    def test_unknown_subject_uses_neutral_base(self):
        self.assertEqual(p.select_profile("一只猫")[0], "BASE")

    def test_custom_palette_replaces_preset_palette_in_both_languages(self):
        d = p.make_prompts("一只陶瓷杯", "I07", "generate", "none", "", "graphite only", "")
        self.assertNotIn("靛蓝", d["zh"])
        self.assertNotIn("樱粉", d["zh"])
        self.assertNotIn("Indigo", d["en"])
        self.assertNotIn("blush", d["en"].lower())

    def test_refine_inherits_source_palette_even_with_manual_profile(self):
        d = p.make_prompts("一只陶瓷杯", "I04", "refine", "source", "", "", "")
        self.assertNotIn("灰绿", d["zh"])
        self.assertNotIn("sage", d["en"].lower())

    def test_presets_do_not_inject_unrequested_scene_objects(self):
        forbidden = ("花枝", "山体", "群山", "船帆", "防波堤", "港口", "blossoms", "mountains", "boats", "piers")
        for ident in p.PROFILES:
            with self.subTest(profile=ident):
                d = p.make_prompts("一只陶瓷杯", ident, "generate", "none", "", "", "")
                combined = d["zh"] + d["en"]
                for token in forbidden:
                    self.assertNotIn(token, combined)

    def test_generate_cannot_treat_upload_as_edit_target(self):
        with self.assertRaises(ValueError):
            p.make_prompts("一只杯子", "I04", "generate", "source", "", "", "")

    def test_invalid_ratio_rejected(self):
        with self.assertRaises(ValueError):
            p.make_prompts("一只杯子", "I04", "generate", "none", "0:1", "", "")


if __name__ == "__main__":
    unittest.main()
