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


    def test_all_redraw_techniques_protect_mist_and_prohibit_unrequested_frames(self):
        for ident in ('T01', 'T02', 'T03', 'T04', 'T05'):
            with self.subTest(ident=ident):
                d=p.make_prompts('梯田、行人、木屋、远山和雾气','BASE','redraw','source',
                                 '16:9','','',technique_id=ident)
                self.assertEqual(d['palette_source'],'source_image')
                self.assertEqual(d['fidelity'],'strict')
                self.assertIn('天空、云雾、远山',d['zh'])
                self.assertIn('画框、印版边框',d['zh'])
                self.assertIn('sky, mist, distant mountains',d['en'])
                self.assertIn('Do not add ornamental frames',d['en'])
                self.assertIn('16:9',d['en'])

    def test_t02_t03_t05_have_distinct_mechanisms(self):
        etch=p.make_prompts('梯田','BASE','redraw','source','','','',technique_id='T02')
        dry=p.make_prompts('梯田','BASE','redraw','source','','','',technique_id='T03')
        mezz=p.make_prompts('梯田','BASE','redraw','source','','','',technique_id='T05')
        self.assertIn('only where local shadows require',etch['en'])
        self.assertIn('localized ink burr attached to individual scratches',dry['en'])
        self.assertIn('Gaussian blur',mezz['en'])
        self.assertEqual(len({etch['en'],dry['en'],mezz['en']}),3)

    def test_region_guard_edit_only_preserves_palette(self):
        generated=p.make_prompts('古桥','BASE','generate','none','','','')
        edited=p.make_prompts('古桥','BASE','redraw','source','','','')
        self.assertNotIn('Do not add ornamental frames',generated['en'])
        self.assertEqual(edited['palette_source'],'source_image')


if __name__ == "__main__":
    unittest.main()
