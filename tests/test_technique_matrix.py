"""5+8+9 orthogonality: these are prompt-structure tests, not generated-image tests."""
import json
import subprocess
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import prompt_builder as p
import compare_techniques as m

class TechniqueMatrixTests(unittest.TestCase):
    def test_five_named_technique_families_and_distinct_primary_mechanisms(self):
        self.assertEqual(set(p.TECHNIQUES),{f'T{i:02d}' for i in range(1,6)})
        self.assertEqual(len({t['primary_zh'] for t in p.TECHNIQUES.values()}),5)
        self.assertEqual(len({t['tone_en'] for t in p.TECHNIQUES.values()}),5)

    def test_eight_recipes_map_to_valid_techniques_and_palettes(self):
        self.assertEqual(len(p.PROFILES),8)
        self.assertEqual(set(p.PALETTES),{f'P{i:02d}' for i in range(9)})
        for prof in p.PROFILES.values():
            self.assertIn(prof['technique_id'],p.TECHNIQUES)
            self.assertIn(prof['palette_id'],p.PALETTES)
        self.assertEqual({x['technique_id'] for x in p.PROFILES.values()},set(p.TECHNIQUES))

    def test_same_theme_fixed_color_content_five_different_main_mark_prompts(self):
        data=m.build_matrix('保留桥塔和驳船数量、位置与透视',palette='石墨灰与纸白')
        self.assertFalse(data['rendered'])
        self.assertEqual(len(data['rows']),5)
        for row in data['rows']:
            self.assertIn('保留桥塔和驳船',row['zh'])
            self.assertIn('石墨灰与纸白',row['zh'])
            self.assertIn('严格保真',row['zh'])
            self.assertNotIn('视觉配方',row['zh'])
        self.assertEqual(len({x['zh'] for x in data['rows']}),5)

    def test_mezzotint_cannot_import_mandatory_stipple_or_hatch_instruction(self):
        x=p.make_prompts('杯子','BASE','generate','none','','石墨灰','',technique_id='T05')
        self.assertIn('美柔汀',x['zh'])
        self.assertNotIn('由平行排线、交叉排线、点刻',x['zh'])
        self.assertIn('mezzotint',x['en'].lower())

    def test_stipple_has_dot_dominance_and_no_alien_recipe(self):
        x=p.make_prompts('杯子','I03','generate','none','','仅黑白','',technique_id='T04')
        self.assertEqual(x['technique_id'],'T04')
        self.assertFalse(x['recipe_applied'])
        self.assertNotIn('dramatic',x['en'].lower())
        self.assertIn('separated engraved dots',x['en'])

    def test_color_families_are_orthogonal_to_technique(self):
        a=p.make_prompts('杯子','BASE','generate','none','','','',technique_id='T04',palette_id='P07')
        b=p.make_prompts('杯子','BASE','generate','none','','','',technique_id='T05',palette_id='P07')
        self.assertEqual(a['palette_id'],b['palette_id'])
        self.assertEqual(a['palette_source'],'palette_id')
        self.assertIn('靛蓝',a['zh'])
        self.assertIn('靛蓝',b['zh'])
        self.assertNotEqual(a['technique_id'],b['technique_id'])

    def test_edit_inherits_source_colors_unless_palette_id_is_explicit(self):
        x=p.make_prompts('桥梁','I07','redraw','source','','','',technique_id='T03')
        y=p.make_prompts('桥梁','I07','redraw','source','','','',technique_id='T03',palette_id='P00')
        self.assertEqual(x['palette_source'],'source_image')
        self.assertEqual(y['palette_source'],'palette_id')
        self.assertNotIn('靛蓝',x['zh'])

    def test_user_custom_palette_wins_over_palette_id(self):
        x=p.make_prompts('杯子','I07','generate','none','','红黑仅两色','',palette_id='P07')
        self.assertEqual(x['palette_source'],'user')
        self.assertNotIn('靛蓝',x['zh'])

    def test_refine_base_inherits_existing_mark_making(self):
        d=p.make_prompts('仅修破损线','BASE','refine','source','','','')
        self.assertEqual(d['technique_id'],'INHERIT')
        self.assertIn('主技法继承',d['zh'])
        with self.assertRaises(ValueError):p.make_prompts('杯子','BASE','generate','none','','','',technique_id='INHERIT')

    def test_comparison_never_claims_upload_or_render_and_rejects_refine(self):
        x=m.build_matrix('the same bridge')
        self.assertFalse(x['uploaded']);self.assertFalse(x['image_inspected']);self.assertFalse(x['rendered'])
        with self.assertRaises(ValueError):m.build_matrix('a cup',mode='refine')

    def test_legacy_technique_map_change_is_explicit(self):
        self.assertEqual(p.PROFILES['I03']['technique_id'],'T05')
        self.assertEqual(p.PROFILES['I05']['technique_id'],'T04')
        self.assertEqual(p.PROFILES['I07']['technique_id'],'T03')

    def test_cli_technique_color_independence_and_valid_json(self):
        proc=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/prompt_builder.py'),
                    '--subject','一座桥','--style','I03','--technique','T04','--palette-id','P01','--json'],
                    capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(proc.returncode,0,proc.stderr)
        d=json.loads(proc.stdout)
        self.assertEqual(d['technique_id'],'T04')
        self.assertEqual(d['palette_id'],'P01')
        self.assertFalse(d['recipe_applied'])
        self.assertFalse(d['rendered'])

if __name__=='__main__':unittest.main()
