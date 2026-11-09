"""Transport-level tests; never claim they are live model generations."""
import base64
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_source_bound_edit as edit


def png(w, h, color=(0x20, 0x40, 0x60)):
    def chunk(name, content):
        return struct.pack('>I', len(content)) + name + content + struct.pack('>I', zlib.crc32(name + content) & 0xffffffff)
    pixels = (b'\x00' + bytes(color) * w) * h
    return edit.PNG_MAGIC + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(pixels)) + chunk(b'IEND', b'')


class SourceBoundEditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'source.png'
        self.style = self.root / 'style.png'
        self.output = self.root / 'out.png'
        self.source.write_bytes(png(256, 384))
        self.style.write_bytes(png(384, 256, color=(4, 5, 6)))

    def test_payload_carries_actual_two_image_bytes_and_roles(self):
        payload, proof = edit.build_payload(self.source, self.style, 'Blue engraved linework')
        self.assertEqual(payload['size'], '256x384')
        self.assertEqual(len(payload['images']), 2)
        for i, path in enumerate((self.source, self.style)):
            uri = payload['images'][i]['image_url']
            self.assertTrue(uri.startswith('data:image/png;base64,'))
            self.assertEqual(base64.b64decode(uri.split(',', 1)[1]), path.read_bytes())
        self.assertEqual(proof['roles'], {'images[0]': 'content_source', 'images[1]': 'style_reference'})
        self.assertEqual(proof['source_sha256'], hashlib.sha256(self.source.read_bytes()).hexdigest())
        self.assertIn('IMAGE 1', payload['prompt'])
        self.assertIn('IMAGE 2', payload['prompt'])

    def test_response_saved_only_after_real_bytes_and_size_validation(self):
        delivered = png(256, 384, color=(10, 20, 30))
        def transport(req):
            self.assertEqual(req.get_method(), 'POST')
            self.assertEqual(req.full_url, edit.API_URL)
            self.assertEqual(req.get_header('Authorization'), 'Bearer local-test-key')
            body = json.loads(req.data)
            self.assertEqual(body['size'], '256x384')
            self.assertEqual(len(body['images']), 2)
            return json.dumps({'data':[{'b64_json':base64.b64encode(delivered).decode('ascii')}]}).encode(), 'req-test-123'
        proof = edit.run_edit(self.source, self.style, self.output, 'I01', api_key='local-test-key', transport=transport)
        self.assertEqual(self.output.read_bytes(), delivered)
        self.assertEqual(proof['status'], 'GENERATED_UNREVIEWED')
        self.assertEqual(proof['source_binding']['status'], 'documented')
        self.assertEqual(proof['request_id'], 'req-test-123')
        self.assertEqual(proof['output_dimensions'], [256,384])
        self.assertTrue((self.root/'out.png.provenance.json').exists())
        self.assertNotIn('local-test-key', (self.root/'out.png.provenance.json').read_text())

    def test_without_server_request_id_cannot_claim_documented(self):
        def transport(_req):
            return json.dumps({'data':[{'b64_json':base64.b64encode(png(256,384,(1,4,2))).decode()}]}).encode(), None
        proof = edit.run_edit(self.source,self.style,self.output,'I01',api_key='dummy',transport=transport)
        self.assertEqual(proof['source_binding']['status'], 'unverified')
        self.assertEqual(proof['status'], 'GENERATED_UNREVIEWED')

    def test_wrong_shape_and_invalid_payload_leave_no_output(self):
        for bad in (png(384, 256), b'not an image'):
            def transport(_req, bad=bad):
                return json.dumps({'data':[{'b64_json':base64.b64encode(bad).decode()}]}).encode(),'req-fail'
            with self.assertRaises(ValueError):
                edit.run_edit(self.source,self.style,self.output,'I01',api_key='dummy',transport=transport)
            self.assertFalse(self.output.exists())
            self.assertFalse((self.root/'out.png.provenance.json').exists())

    def test_no_api_key_never_sends(self):
        def transport(_req):
            self.fail('Transport should never be invoked')
        with self.assertRaisesRegex(ValueError,'OPENAI_API_KEY'):
            edit.run_edit(self.source,self.style,self.output,'I01',api_key='',transport=transport)

    def test_unsafe_request_ratios_rejected_without_network(self):
        with self.assertRaisesRegex(ValueError,'more than 1%'):
            edit.build_payload(self.source,self.style,'I01',size='384x256')
        with self.assertRaisesRegex(ValueError,'multiples of 16'):
            edit.build_payload(self.source,self.style,'I01',size='257x384')
        with self.assertRaisesRegex(ValueError,'distinct'):
            edit.build_payload(self.source,self.source,'I01')

    def test_model_report_payload_is_never_auto_marked_pass(self):
        mock_report_bytes=png(256,384, color=(100,100,100))
        def transport(_req):
            return json.dumps({'data':[{'b64_json':base64.b64encode(mock_report_bytes).decode()}]}).encode(),'req-report'
        receipt=edit.run_edit(self.source,self.style,self.output,'I01',api_key='dummy',transport=transport)
        self.assertEqual(receipt['status'],'GENERATED_UNREVIEWED')
        self.assertNotIn('visual_score',receipt)
        self.assertNotIn('PASS',json.dumps(receipt))


if __name__=='__main__':
    unittest.main()
