import copy
import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from visual_director import rank_profiles, RULES
import prompt_builder


def analysis(profile='I01'):
    keys = [k for group in RULES['groups'].values() for k in group]
    return {'image_sha256':'0'*64, 'observations':{
        k:{'value':v, 'evidence':'Observed region for '+k}
        for k,v in zip(keys, {'I01':[.95,.85,.1,.35,.35,.15,.9,.55,.2,.8], 'I03':[.3,.4,.95,.95,.75,.25,.05,.65,.85,.1], 'I08':[.6,.4,.5,.6,1,.2,.1,.8,.5,.3]}[profile])}}


class VisualDirectorTests(unittest.TestCase):
    def test_manual_and_refine_do_not_read_selection_files_or_call_rankers(self):
        for extra in (['--style','I01'], ['--mode','refine','--role','source']):
            output = io.StringIO()
            with patch.object(prompt_builder, 'select_profile', side_effect=AssertionError('Unexpected keyword ranking')), \
                 patch('visual_director.rank_profiles', side_effect=AssertionError('Unexpected visual ranking')), \
                 contextlib.redirect_stdout(output):
                code = prompt_builder.main(extra+['--visual-analysis','missing-analysis.json',
                                                   '--preferences','missing-preferences.json','--json'])
            self.assertEqual(code,0)
            result = json.loads(output.getvalue())
            self.assertIsNone(result['visual_recommendation'])
            self.assertIsNone(result['selection_scores'])
            self.assertTrue(any('were not read' in warning for warning in result['warnings']))
            self.assertEqual(result['style'],'I01' if '--style' in extra else 'BASE')
            if '--mode' in extra: self.assertEqual(result['technique_id'],'INHERIT')

    def test_geometry_not_subject_names_selects_recipe(self):
        self.assertEqual(rank_profiles(analysis())['recommended'], 'I01')
        self.assertEqual(rank_profiles(analysis('I03'))['recommended'], 'I03')

    def test_partial_information_uses_base(self):
        a = analysis()
        a['observations'] = {'curvature': a['observations']['curvature']}
        self.assertEqual(rank_profiles(a)['recommended'], 'BASE')

    def test_invalid_evidence_is_rejected(self):
        for value in [float('nan'), -1, 2, True, 'high']:
            a = analysis()
            a['observations']['regularity']['value'] = value
            with self.assertRaises(ValueError): rank_profiles(a)
        a = analysis()
        a['observations']['regularity']['evidence'] = ''
        with self.assertRaises(ValueError): rank_profiles(a)

    def test_preferences_require_space_and_never_persist(self):
        prefs = {'guilloche':'preferred_when_compatible'}
        before = copy.deepcopy(prefs)
        self.assertEqual(rank_profiles(analysis(), prefs)['ornament'], 'guilloche')
        self.assertEqual(rank_profiles(analysis('I08'), prefs)['ornament'], 'none')
        self.assertEqual(rank_profiles(analysis())['ornament'], 'none')
        self.assertEqual(prefs, before)

    def test_explicit_project_aesthetic_configuration(self):
        prefs = {'style_selection':'auto', 'aesthetic_preference':{'detail':'high', 'geometry_fidelity':'strict', 'engraving_character':'precise', 'preferred_visual_identity':['banknote_engraving','classical_intaglio'], 'guilloche':'preferred_when_compatible', 'color':'adaptive', 'atmosphere':'elegant_and_detailed'}}
        result = rank_profiles(analysis(), prefs)
        self.assertEqual(result['recommended'], 'I01')
        self.assertEqual(result['ornament'], 'guilloche')
        self.assertEqual(result['candidates'][0]['preference_bonus'], 5)

    def test_count_and_scores_are_not_probabilities(self):
        result = rank_profiles(analysis(), {'recommendation_count':2})
        self.assertEqual(len(result['candidates']), 2)
        self.assertTrue(result['requires_visual_validation'])
        self.assertFalse(result['rendered'])
        for bad in [{'recommendation_count':8}, {'unknown':True}]:
            with self.assertRaises(ValueError): rank_profiles(analysis(), bad)

    def test_cli_binds_source_and_preserves_explicit_and_refine_choices(self):
        image = ROOT/'assets/examples/I01_blue_coastal_architecture.jpg'
        a = analysis()
        a['image_sha256'] = hashlib.sha256(image.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'analysis.json'
            path.write_text(json.dumps(a), encoding='utf-8')
            base = [sys.executable, '-B', str(ROOT/'scripts/prompt_builder.py'), '--image',str(image),'--visual-analysis',str(path),'--json']
            def run(*extra):
                return subprocess.run(base+list(extra),capture_output=True,encoding='utf-8')
            result = json.loads(run().stdout)
            self.assertEqual(result['style'], 'I01')
            self.assertEqual(result['palette_source'], 'source_image')
            self.assertEqual(json.loads(run('--style','I06').stdout)['style'], 'I06')
            refined = json.loads(run('--mode','refine').stdout)
            self.assertEqual(refined['technique_id'], 'INHERIT')
            a['image_sha256'] = '0'*64
            path.write_text(json.dumps(a), encoding='utf-8')
            self.assertEqual(run().returncode, 2)
