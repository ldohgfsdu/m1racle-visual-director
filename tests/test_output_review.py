"""Synthetic review records verify gate behavior, never generated-image quality."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from output_review import HARD, GENERAL, STYLES, review, feedback_patch, summarize_benchmark


class OutputReviewTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.source = Path(temp.name)/'source'
        self.output = Path(temp.name)/'output'
        self.source.write_bytes(b'synthetic source fixture')
        self.output.write_bytes(b'synthetic output fixture')
        self.record = {'source_sha256':hashlib.sha256(self.source.read_bytes()).hexdigest(),
                       'output_sha256':hashlib.sha256(self.output.read_bytes()).hexdigest(),
                       'profile':'I01','technique':'T01','checks':{}}
        for name in list(HARD)+list(GENERAL)+list(STYLES['I01']['required']):
            self.record['checks'][name] = {'status':'PASS','evidence':'synthetic observation','region':'whole frame'}

    def run_review(self):
        return review(self.record,self.source,self.output)

    def test_complete_supplied_review_can_pass(self):
        self.assertEqual(self.run_review()['status'],'PASS')

    def test_beautiful_style_cannot_override_geometry_failure(self):
        self.record['checks']['geometry']['status'] = 'ISSUE'
        result = self.run_review()
        self.assertEqual(result['status'],'REJECTED')
        self.assertFalse(result['may_claim_success'])
        self.assertEqual(result['repairs'][0]['check'],'geometry')

    def test_missing_content_evidence_blocks_style_acceptance(self):
        del self.record['checks']['identity']
        self.assertEqual(self.run_review()['status'],'UNVERIFIED')

    def test_missing_style_evidence_is_not_success(self):
        del self.record['checks']['I01.1']
        self.assertFalse(self.run_review()['may_claim_success'])

    def test_style_defect_needs_repair(self):
        self.record['checks']['I01.2']['status'] = 'ISSUE'
        self.assertEqual(self.run_review()['status'],'REPAIR_REQUIRED')

    def test_pass_requires_region_and_observation(self):
        self.record['checks']['count']['evidence'] = ''
        with self.assertRaises(ValueError): self.run_review()

    def test_stale_output_or_original_as_output_cannot_pass(self):
        self.output.write_bytes(b'changed')
        with self.assertRaises(ValueError): self.run_review()
        self.output.write_bytes(self.source.read_bytes())
        self.record['output_sha256'] = self.record['source_sha256']
        with self.assertRaises(ValueError): self.run_review()

    def test_conflicting_technique_cannot_claim_recipe_preservation(self):
        self.record['technique'] = 'T04'
        for name in STYLES['I01']['required']: del self.record['checks'][name]
        self.assertEqual(self.run_review()['status'],'RECIPE_NOT_APPLIED')

    def test_every_recipe_has_distinct_checks_and_existing_reference(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(set(STYLES),{'I%02d'%i for i in range(1,9)})
        for entry in STYLES.values():
            self.assertTrue((root/entry['reference']).is_file())
            self.assertEqual(len(entry['required']),3)

    def test_feedback_never_saves_or_infers_consent(self):
        self.assertEqual(feedback_patch(['insufficient_ornament'])['preference_patch'],{})
        result = feedback_patch(['insufficient_ornament'],consent=True)
        self.assertEqual(result['preference_patch'],{'guilloche':'preferred_when_compatible'})
        self.assertFalse(result['saved'])
        with self.assertRaises(ValueError): feedback_patch(['too_much_ornament','insufficient_ornament'],True)

    def test_benchmark_keeps_failed_and_pending_attempts(self):
        rows=[{'run_id':'a','status':'PASS'},{'run_id':'b','status':'REJECTED'},
              {'run_id':'c','status':'UNVERIFIED'}]
        self.assertEqual(summarize_benchmark(rows)['attempts'],3)
        with self.assertRaises(ValueError): summarize_benchmark(rows+[copy.deepcopy(rows[0])])

    def test_benchmark_plan_has_no_fabricated_results(self):
        plan = json.loads((Path(__file__).with_name('benchmark_plan.json')).read_text(encoding='utf-8'))
        self.assertEqual(len(plan['cases']),24)
        self.assertEqual(len({case['id'] for case in plan['cases']}),24)
        for case in plan['cases']:
            self.assertEqual(case['status'],'UNVERIFIED')
            self.assertEqual(case['runs'],[])
            self.assertIsNone(case['source'])

    def test_malformed_review_has_actionable_validation_errors(self):
        self.record['checks']['identity']['status'] = []
        with self.assertRaises(ValueError): self.run_review()
        with self.assertRaises(ValueError): feedback_patch([{}],True)
