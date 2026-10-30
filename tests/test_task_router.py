"""Regression tests: a missing image model must never trigger procedural redraw implicitly."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('task_router', Path(__file__).resolve().parents[1] / 'scripts' / 'task_router.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class RuntimeGateTests(unittest.TestCase):
    def test_image_request_without_backend_is_blocked(self):
        x = mod.route('image', 'none')
        self.assertEqual(x['status'], 'blocked')
        self.assertFalse(x['may_render'])
        self.assertEqual(x['max_procedural_previews'], 0)
    def test_no_backend_does_not_infer_python_as_image_model(self):
        x = mod.route('image', 'none')
        self.assertNotIn('procedural', x['action'])
    def test_unknown_backend_only_checks_tools_once(self):
        x = mod.route('image', 'unknown')
        self.assertEqual(x['status'], 'verify_once')
        self.assertFalse(x['may_render'])
    def test_real_backend_has_three_image_output_limit(self):
        x = mod.route('image', 'present')
        self.assertEqual(x['max_image_generations'], 3)
        self.assertEqual(x['max_procedural_previews'], 0)
    def test_prompt_intent_never_generates(self):
        x = mod.route('prompt', 'present')
        self.assertFalse(x['may_render'])
    def test_procedural_requires_user_consent(self):
        x = mod.route('procedural', 'none')
        self.assertEqual(x['status'], 'needs_explicit_authorization')
    def test_procedural_authorized_is_bounded(self):
        x = mod.route('image', 'none', procedural_authorized=True)
        self.assertTrue(x['may_render'])
        self.assertEqual(x['max_procedural_previews'], 2)
        self.assertEqual(x['max_image_generations'], 0)
    def test_invalid_mode_rejected(self):
        with self.assertRaises(ValueError): mod.route('impossible', 'present')
