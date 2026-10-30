import contextlib
import io
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import prompt_builder as p


def cli(*args):
    return subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/prompt_builder.py'), *args],
                          cwd=ROOT, capture_output=True, text=True, encoding='utf-8')


class PromptTests(unittest.TestCase):
    def test_eight_profiles_and_neutral_base(self):
        self.assertEqual(set(p.PROFILES), {f'I{i:02d}' for i in range(1, 9)})
        self.assertEqual(p.select_profile('未知物体')[0], 'BASE')

    def test_great_wall_positive_evidence(self):
        self.assertEqual(p.select_profile('长城横卧山脊')[0], 'I04')

    def test_portrait_positive_evidence(self):
        self.assertEqual(p.select_profile('学者肖像 portrait of an old man')[0], 'I05')

    def test_port_word_is_still_recognized(self):
        self.assertEqual(p.select_profile('historic port')[0], 'I08')

    def test_negative_enumeration_does_not_erase_positive_clause(self):
        self.assertEqual(p.select_profile('不要人物、肖像，长城横卧山脊')[0], 'I04')

    def test_positive_after_conjunction_is_retained(self):
        self.assertEqual(p.select_profile('不要樱花但要肖像')[0], 'I05')
        self.assertEqual(p.select_profile('no blossoms but a portrait')[0], 'I05')

    def test_city_name_is_not_generic_negation(self):
        self.assertEqual(p.select_profile('无锡港口')[0], 'I08')

    def test_full_negative_constraints_remain_in_prompt(self):
        d = p.make_prompts('古寺，不要樱花', 'I07', 'generate', 'none', '', '', '')
        self.assertIn('古寺，不要樱花', d['zh'])

    def test_theme_color_instruction_overrides_preset(self):
        for subject in ('杯子，只用黑白', 'a cup, use graphite gray only', '古寺，禁止粉色'):
            with self.subTest(subject=subject):
                d = p.make_prompts(subject, 'I07', 'generate', 'none', '', '', '')
                self.assertEqual(d['palette_source'], 'subject')
                self.assertNotIn('靛蓝', d['zh'])
                self.assertNotIn('blush', d['en'])

    def test_color_word_without_instruction_is_not_global_palette(self):
        d = p.make_prompts('a red ceramic cup', 'I07', 'generate', 'none', '', '', '')
        self.assertEqual(d['palette_source'], 'preset')

    def test_color_detection_respects_english_word_boundaries(self):
        self.assertFalse(p.theme_has_color_instruction('a user prepared a ceramic cup'))
        self.assertTrue(p.theme_has_color_instruction('use red and black ink'))

    def test_color_in_preserve_clause_overrides_preset(self):
        d=p.make_prompts('cup','I07','generate','none','','','原有红黑配色')
        self.assertEqual(d['palette_source'],'subject')
        self.assertNotIn('blush',d['en'])

    def test_background_exclusion_overrides_auto_suggestion(self):
        for subject in ('杯子，不要装饰底纹','a cup, without decorative filigree'):
            d=p.make_prompts(subject,'I07','generate','none','','','')
            self.assertEqual(d['background'],'none')
            self.assertNotIn('Optional restrained',d['en'])

    def test_source_and_style_roles_have_distinct_invariants(self):
        src = p.make_prompts('城堡', 'I01', 'redraw', 'source', '', '', '')
        ref = p.make_prompts('城堡', 'I01', 'generate', 'style', '', '', '')
        self.assertIn('严格保真', src['zh'])
        self.assertNotIn('严格保真', ref['zh'])
        self.assertIn('风格参考图', ref['zh'])
        self.assertNotIn('风格参考图', src['zh'])

    def test_explicit_palette_has_single_authority_for_all_presets(self):
        for ident in ['BASE', *p.PROFILES]:
            d = p.make_prompts('cup', ident, 'generate', 'none', '3:2', 'red and black only', 'handle shape')
            self.assertEqual(d['palette_source'], 'user')
            self.assertNotIn('blush', d['en'])
            self.assertNotIn('sage', d['en'])
            self.assertIn('3:2', d['en'])
            self.assertIn('handle shape', d['en'])

    def test_redraw_and_refine_inherit_source_colors(self):
        for mode in ('redraw', 'refine'):
            for ident in p.PROFILES:
                d = p.make_prompts('cup', ident, mode, 'source', '', '', '')
                self.assertEqual(d['palette_source'], 'source_image')
                self.assertEqual(d['fidelity'], 'strict')
                self.assertNotIn('blush', d['en'])
                self.assertIn('original aspect ratio', d['en'])

    def test_explicit_recoloring_does_not_also_lock_original_palette(self):
        d = p.make_prompts('cup', 'I07', 'refine', 'source', '', 'red and black only', '')
        self.assertEqual(d['palette_source'], 'user')
        self.assertNotIn('Inherit the content image', d['en'])
        self.assertNotIn('preserve composition and palette', d['en'])

    def test_background_none_does_not_demand_decorative_filigree(self):
        d = p.make_prompts('cup', 'I07', 'generate', 'none', '', '', '', background='none')
        self.assertIn('Use no decorative', d['en'])
        self.assertNotIn('Add restrained', d['en'])
        self.assertNotIn('Optional restrained', d['en'])

    def test_edit_auto_does_not_add_new_filigree(self):
        d = p.make_prompts('cup', 'I07', 'refine', 'source', '', '', '')
        self.assertIn('introduce no new decorative', d['en'])

    def test_explicit_filigree_does_not_move_objects(self):
        d = p.make_prompts('cup', 'BASE', 'generate', 'none', '', '', '', background='guilloche')
        self.assertIn('do not cover or move', d['en'])

    def test_balanced_and_free_do_not_keep_strict_lock(self):
        for fidelity in ('balanced', 'free'):
            d = p.make_prompts('cup', 'BASE', 'redraw', 'source', '', '', '', fidelity=fidelity)
            self.assertEqual(d['fidelity'], fidelity)
            self.assertNotIn('Strict fidelity', d['en'])

    def test_observations_are_included_and_not_claimed_as_cli_vision(self):
        d = p.make_prompts('保留原图', 'BASE', 'refine', 'source', '', '', '', visual_notes='两个把手')
        self.assertIn('两个把手', d['zh'])
        self.assertIn('非 CLI 识图', d['zh'])

    def test_both_roles_are_separately_labeled_for_edit(self):
        d = p.make_prompts('cup', 'I08', 'redraw', 'source', '', '', '', style_reference=True)
        self.assertIn('Strict fidelity', d['en'])
        self.assertIn('Label edit targets and style references separately', d['en'])

    def test_invalid_profile_and_modes_fail(self):
        for profile,mode,role in [('I99','generate','none'),('I01','auto','none'),('I01','refine','style')]:
            with self.subTest(profile=profile,mode=mode,role=role), self.assertRaises(ValueError):
                p.make_prompts('cup', profile, mode, role, '', '', '')

    def test_ratio_validation(self):
        for ratio in ('0:1','-1:1','nan','16/9','1:0'):
            with self.subTest(ratio=ratio), self.assertRaises(ValueError):
                p.checked_ratio(ratio)
        self.assertEqual(p.checked_ratio(' 16:9 '), '16:9')

    def test_original_samples_retained(self):
        self.assertEqual(len(list((ROOT / 'assets/examples').glob('*.jpg'))), 8)
        self.assertTrue((ROOT / 'assets/style-contact-sheet.jpg').is_file())

    def test_cli_json_never_claims_rendering_or_upload(self):
        r = cli('--subject','长城','--json')
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)
        self.assertEqual(d['style'], 'I04')
        self.assertFalse(d['rendered'])
        self.assertFalse(d['references_uploaded'])

    def test_cli_json_obeys_language_selection(self):
        for lang,absent in [('zh','en'),('en','zh')]:
            d=json.loads(cli('--subject','cup','--lang',lang,'--json').stdout)
            self.assertIn(lang,d)
            self.assertNotIn(absent,d)

    def test_cli_source_template_is_explicitly_uninspected(self):
        d=json.loads(cli('--subject','人物','--mode','redraw','--role','source','--json').stdout)
        self.assertEqual(d['image_probe'],'')
        self.assertTrue(any('no source image was inspected' in s for s in d['warnings']))

    def test_cli_edit_without_source_errors(self):
        self.assertNotEqual(cli('--mode','redraw').returncode,0)

    def test_cli_generate_with_source_errors(self):
        self.assertNotEqual(cli('--mode','generate','--role','source').returncode,0)

    def test_cli_style_role_requires_image(self):
        self.assertNotEqual(cli('--role','style').returncode,0)

    def test_cli_local_style_reference_is_generation(self):
        sample=next((ROOT/'assets/examples').glob('*.jpg'))
        r=cli('--subject','杯子','--image',str(sample),'--role','style','--json')
        self.assertEqual(r.returncode,0,r.stderr)
        d=json.loads(r.stdout)
        self.assertEqual(d['task_mode'],'generate')
        self.assertEqual(d['image_inputs'][0]['role'],'style')
        self.assertFalse(d['references_uploaded'])

    def test_cli_two_local_image_roles(self):
        samples=list((ROOT/'assets/examples').glob('*.jpg'))
        r=cli('--subject','保留主体','--image',str(samples[0]),'--style-image',str(samples[1]),'--json')
        self.assertEqual(r.returncode,0,r.stderr)
        d=json.loads(r.stdout)
        self.assertEqual([v['role'] for v in d['image_inputs']],['source','style'])
        self.assertEqual(d['palette_source'],'source_image')

    def test_cli_duplicate_roles_for_same_file_rejected(self):
        sample=next((ROOT/'assets/examples').glob('*.jpg'))
        self.assertNotEqual(cli('--image',str(sample),'--style-image',str(sample)).returncode,0)

    def test_cli_refine_auto_inherits_style(self):
        r=cli('--subject','樱花全景，只修线条','--mode','refine','--role','source','--json')
        d=json.loads(r.stdout)
        self.assertEqual(d['style'],'BASE')
        self.assertEqual(d['palette_source'],'source_image')
        self.assertIsNone(d['selection_scores'])

    def test_cli_palette_does_not_select_scene(self):
        d=json.loads(cli('--subject','cup','--palette','blush','--json').stdout)
        self.assertEqual(d['style'],'BASE')
        self.assertEqual(d['palette_source'],'user')

    def test_cli_missing_image_and_bad_ratio_have_no_traceback(self):
        for args in [('--image','not-a-real-image.jpg'),('--ratio','0:1')]:
            r=cli(*args)
            self.assertEqual(r.returncode,2)
            self.assertNotIn('Traceback',r.stderr)

    def test_unreadable_image_error_is_useful(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest('Pillow optional')
        with tempfile.NamedTemporaryFile(suffix='.jpg') as f:
            f.write(b'not an image');f.flush()
            with self.assertRaisesRegex(ValueError,'Cannot parse image'):
                p.image_info(f.name)

    def test_readme_commands_are_executable(self):
        text=(ROOT/'README.md').read_text(encoding='utf-8')
        commands=[line for line in text.splitlines() if line.startswith('python scripts/prompt_builder.py ')]
        self.assertGreaterEqual(len(commands),4)
        for command in commands:
            args=shlex.split(command)
            r=cli(*args[2:])
            self.assertEqual(r.returncode,0,command+'\n'+r.stderr)

    def test_preset_documentation_matches_data(self):
        text=(ROOT/'references/profiles.md').read_text(encoding='utf-8')
        for ident,profile in p.PROFILES.items():
            for value in (ident,profile['name'],profile['technique_id'],profile['palette_id'],profile['recipe_zh']):
                self.assertIn(value,text)

    def test_cli_emits_utf8_in_ascii_locale(self):
        env=dict(os.environ,LC_ALL='C',PYTHONCOERCECLOCALE='0',PYTHONUTF8='0',PYTHONIOENCODING='ascii')
        r=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/prompt_builder.py'),'--subject','cup','--json'],
                         env=env,capture_output=True,encoding='utf-8')
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)['style_name_zh'],'中性母风格')

    def test_package_readable_in_ascii_locale(self):
        env=dict(os.environ,LC_ALL='C',PYTHONCOERCECLOCALE='0',PYTHONUTF8='0',PYTHONIOENCODING='ascii')
        r=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/validate_skill.py'),'--structure-only'],
                         env=env,capture_output=True,encoding='utf-8')
        self.assertEqual(r.returncode,0,r.stderr)


if __name__ == '__main__':
    unittest.main()
