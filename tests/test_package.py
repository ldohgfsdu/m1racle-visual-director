import hashlib
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import validate_skill as v


def manifest(files):
    return {'files':[{'path':k,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()} for k,data in files.items()]}


class IntegrityTests(unittest.TestCase):
    def test_complete_manifest(self):
        files={'SKILL.md':b'content','references/profiles.json':b'{}'}
        self.assertEqual(v.check_manifest_data(manifest(files),files),[])

    def test_tampered_bytes_detected_even_at_same_size(self):
        files={'SKILL.md':b'abcd'}
        m=manifest(files)
        self.assertTrue(any('hash mismatch' in x for x in v.check_manifest_data(m,{'SKILL.md':b'abce'})))

    def test_truncation_detected(self):
        files={'SKILL.md':b'abcd'}
        self.assertTrue(any('size mismatch' in x for x in v.check_manifest_data(manifest(files),{'SKILL.md':b'abc'})))

    def test_missing_file_detected(self):
        files={'SKILL.md':b'abc'}
        self.assertTrue(any('missing file' in x for x in v.check_manifest_data(manifest(files),{})))

    def test_unlisted_file_detected(self):
        files={'SKILL.md':b'abc'}
        self.assertTrue(any('coverage mismatch' in x for x in v.check_manifest_data(manifest(files),{**files,'extra.py':b'x'})))

    def test_duplicate_manifest_entry_detected(self):
        files={'SKILL.md':b'abc'}
        m=manifest(files);m['files']*=2
        self.assertTrue(any('duplicate' in x for x in v.check_manifest_data(m,files)))

    def test_traversal_rejected(self):
        files={'../escape':b'abc'}
        self.assertTrue(any('unsafe' in x for x in v.check_manifest_data(manifest(files),files)))

    def test_malformed_manifest_is_a_failure_not_a_crash(self):
        self.assertTrue(v.check_manifest_data({},{}))
        self.assertTrue(v.check_manifest_data({'files':[None]},{}))


class CheckoutIntegrityTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / 'package'
        shutil.copytree(ROOT, self.root,
                        ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc'))

    def test_git_checkout_metadata_is_not_release_content(self):
        metadata = self.root / '.git'
        (metadata / 'hooks').mkdir(parents=True)
        (metadata / 'HEAD').write_text('ref: refs/heads/main\n', encoding='utf-8')
        (metadata / 'hooks' / 'README.md').write_text(
            '[Git-only link](not-a-release-file.md)\n', encoding='utf-8')
        self.assertEqual(v.check_package(self.root), [])

    def test_git_worktree_pointer_is_not_release_content(self):
        (self.root / '.git').write_text('gitdir: ../worktrees/review\n', encoding='utf-8')
        self.assertEqual(v.check_package(self.root), [])

    def test_unlisted_hidden_release_file_is_still_rejected(self):
        hidden = self.root / '.extra'
        hidden.mkdir()
        (hidden / 'payload.txt').write_text('unlisted', encoding='utf-8')
        errors = v.check_package(self.root)
        self.assertTrue(any('manifest coverage mismatch: .extra/payload.txt' in e
                            for e in errors), errors)


if __name__=='__main__':
    unittest.main()
