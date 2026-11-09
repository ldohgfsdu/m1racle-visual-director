#!/usr/bin/env python3
"""Source-bound GPT Image edit: explicit image bytes, dimensions and audit trail.

Does not score aesthetics, visually check content, or infer that a model complied.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import struct
import urllib.error
import urllib.request
import uuid

def image_dimensions(path: Path) -> tuple[int, int]:
    """PNG/JPEG dimensions from real header bytes, independent of Pillow."""
    data = path.read_bytes()
    if data.startswith(b'\x89PNG\r\n\x1a\n') and len(data) >= 24 and data[12:16] == b'IHDR':
        w, h = struct.unpack('>II', data[16:24])
    elif data.startswith(b'\xff\xd8'):
        w = h = 0
        pos = 2
        while pos + 4 <= len(data):
            if data[pos] != 0xff:
                raise ValueError('Malformed JPEG image')
            while pos < len(data) and data[pos] == 0xff:
                pos += 1
            if pos >= len(data):
                break
            marker = data[pos]
            pos += 1
            if marker in (0x01, *range(0xd0, 0xda)):
                continue
            if marker == 0xda or pos + 2 > len(data):
                break
            length = int.from_bytes(data[pos:pos + 2], 'big')
            if length < 2 or pos + length > len(data):
                break
            if marker in (0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf) and length >= 7:
                h = int.from_bytes(data[pos + 3:pos + 5], 'big')
                w = int.from_bytes(data[pos + 5:pos + 7], 'big')
                break
            pos += length
    else:
        raise ValueError('Unsupported PNG/JPEG header')
    if not (1 <= w <= 30000 and 1 <= h <= 30000):
        raise ValueError('Invalid image dimensions')
    return w, h

API_URL = 'https://api.openai.com/v1/images/edits'
DEFAULT_MODEL = 'gpt-image-2.5-sunburst'
MAX_INPUT_BYTES = 14_000_000  # data-URI encoded size stays below 20 MB per image
PNG_MAGIC = b'\x89PNG\r\n\x1a\n'


def inspect_image(path: Path) -> dict:
    if not path.is_file():
        raise ValueError('Image missing: ' + str(path))
    raw = path.read_bytes()
    if not raw or len(raw) > MAX_INPUT_BYTES:
        raise ValueError('Image must be nonempty and <= 14 MB: ' + str(path))
    if raw.startswith(PNG_MAGIC):
        mime = 'image/png'
    elif raw.startswith(b'\xff\xd8'):
        mime = 'image/jpeg'
    else:
        raise ValueError('Only JPEG and PNG source images are currently supported')
    w, h = image_dimensions(path)
    return {'path': str(path), 'width': w, 'height': h,
            'mime': mime, 'sha256': hashlib.sha256(raw).hexdigest(), 'raw': raw}


def requested_size(source: dict, size: str = '') -> tuple[int, int]:
    if size:
        if not re.fullmatch(r'[1-9][0-9]{1,3}x[1-9][0-9]{1,3}', size):
            raise ValueError('size must be WIDTHxHEIGHT')
        w, h = (int(v) for v in size.split('x'))
    else:
        w, h = source['width'], source['height']
    if w % 16 or h % 16 or not (256 <= w <= 3840 and 256 <= h <= 3840):
        raise ValueError('GPT Image 2.5 custom dimensions require multiples of 16 and supported bounds')
    if not 1 / 3 <= w / h <= 3:
        raise ValueError('Unsupported aspect ratio')
    relative_drift = abs((w / h) / (source['width'] / source['height']) - 1)
    if relative_drift > 0.01:
        raise ValueError('Requested output ratio changes the source by more than 1%')
    return w, h


def build_payload(source: Path, style: Path, prompt: str,
                  size: str = '', model: str = DEFAULT_MODEL) -> tuple[dict, dict]:
    if not prompt.strip():
        raise ValueError('A nonempty artwork-only edit prompt is required')
    if model not in {'gpt-image-2.5-sunburst', 'gpt-image-2.5-flare'}:
        raise ValueError('Choose a verified model with custom resolution editing support')
    if source.resolve() == style.resolve():
        raise ValueError('Content and style must be distinct images')
    a, b = inspect_image(source), inspect_image(style)
    w, h = requested_size(a, size)
    content = (
        'Produce ONE standalone artwork (never a report, infographic, scorecard or multi-panel image). '
        'IMAGE 1 is the binding CONTENT SOURCE: preserve its object count, viewpoint, building geometry, '
        'position of people, cables, skyline, canal, reflections, border and any existing photographic labels. '
        'IMAGE 2 is STYLE ONLY: borrow fine banknote engraving, controlled guilloche and blue ink on pale paper, '
        'but NEVER borrow its landscape, buildings, boats, mountains or people. '
        'Do not crop, rotate or change the orientation. Never generate self-assigned scores or approval claims. '
        'Requested artwork details: ' + prompt.strip()
    )
    def image_entry(item):
        return {'image_url': 'data:' + item['mime'] + ';base64,' + base64.b64encode(item['raw']).decode('ascii')}
    payload = {'images': [image_entry(a), image_entry(b)], 'prompt': content,
               'model': model, 'size': f'{w}x{h}', 'quality': 'high',
               'output_format': 'png', 'n': 1}
    details = {'source_sha256': a['sha256'], 'style_sha256': b['sha256'],
               'source_dimensions': [a['width'], a['height']],
               'style_dimensions': [b['width'], b['height']],
               'requested_dimensions': [w, h], 'model': model,
               'prompt_sha256': hashlib.sha256(content.encode('utf-8')).hexdigest(),
               'roles': {'images[0]': 'content_source', 'images[1]': 'style_reference'}}
    return payload, details


def default_transport(request: urllib.request.Request) -> tuple[bytes, str | None]:
    try:
        with urllib.request.urlopen(request, timeout=240) as response:
            return response.read(), response.headers.get('x-request-id')
    except urllib.error.HTTPError as exc:
        # Do not log submitted source data or bearer token.
        raise RuntimeError(f'Image edits endpoint failed: HTTP {exc.code}') from exc


def run_edit(source: Path, style: Path, output: Path, prompt: str, *,
             api_key: str, size: str = '', model: str = DEFAULT_MODEL,
             transport=default_transport) -> dict:
    if not api_key.strip():
        raise ValueError('OPENAI_API_KEY is required for a real edit; no mock image will be emitted')
    output = output.resolve()
    record = output.with_name(output.name + '.provenance.json')
    if output.exists() or record.exists():
        raise FileExistsError('Output/provenance already exists; never overwrite prior test evidence')
    payload, details = build_payload(source, style, prompt, size, model)
    request_bytes = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    req = urllib.request.Request(API_URL, data=request_bytes,
                                 headers={'Authorization': 'Bearer ' + api_key,
                                          'Content-Type': 'application/json'},
                                 method='POST')
    response_body, request_id = transport(req)
    response = json.loads(response_body)
    data = response.get('data')
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        raise ValueError('Image edits response must contain exactly one output')
    encoded = data[0].get('b64_json')
    if not isinstance(encoded, str):
        raise ValueError('Response lacks a base64 image')
    image = base64.b64decode(encoded, validate=True)
    if not image.startswith(PNG_MAGIC):
        raise ValueError('Image edits endpoint did not return requested PNG')
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_name('.' + output.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        tmp.write_bytes(image)
        dimensions = image_dimensions(tmp)
        if list(dimensions) != details['requested_dimensions']:
            raise ValueError('Returned image dimensions mismatch requested size: ' + str(dimensions))
        if abs((dimensions[0] / dimensions[1]) / (details['source_dimensions'][0] / details['source_dimensions'][1]) - 1) > .01:
            raise ValueError('Output violates original aspect-ratio gate')
        output_digest = hashlib.sha256(image).hexdigest()
        run_id = request_id or 'no-server-request-id-' + uuid.uuid4().hex
        receipt = {**details, 'run_id': run_id, 'request_id': request_id,
                   'endpoint': API_URL, 'method': 'POST',
                   'request_body_sha256': hashlib.sha256(request_bytes).hexdigest(),
                   'output_sha256': output_digest,
                   'output_dimensions': list(dimensions), 'output_path': str(output),
                   'status': 'GENERATED_UNREVIEWED',
                   'source_binding': {
                       'status': 'documented' if request_id else 'unverified',
                       'role': 'content_source', 'source_sha256': details['source_sha256'],
                       'run_id': run_id,
                       'tool_input_trace': str(record) + ' request_body_sha256=' + hashlib.sha256(request_bytes).hexdigest(),
                   },
                   'warning': 'This receipt records input bytes and an HTTP edit request. It does not prove visual fidelity, model compliance, or user approval.'}
        record_tmp = tmp.with_name(tmp.name + '.json')
        record_tmp.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        try:
            tmp.replace(output)
            record_tmp.replace(record)
        except Exception:
            output.unlink(missing_ok=True)
            raise
        return receipt
    finally:
        tmp.unlink(missing_ok=True)
        tmp.with_name(tmp.name + '.json').unlink(missing_ok=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description='Real source-bound GPT Image edit; not a picture filter or a visual scorer')
    ap.add_argument('--source', required=True, type=Path)
    ap.add_argument('--style-image', required=True, type=Path)
    ap.add_argument('--output', required=True, type=Path)
    ap.add_argument('--prompt', required=True)
    ap.add_argument('--size', default='', help='Default: exact source image dimensions, if supported')
    ap.add_argument('--model', default=DEFAULT_MODEL)
    ap.add_argument('--dry-run', action='store_true', help='Validate dimensions and bytes without network or output')
    args = ap.parse_args(argv)
    try:
        if args.dry_run:
            _, details = build_payload(args.source, args.style_image, args.prompt, args.size, args.model)
            print(json.dumps({**details, 'status': 'NOT_RENDERED_DRY_RUN'}, ensure_ascii=False, indent=2))
        else:
            receipt = run_edit(args.source, args.style_image, args.output, args.prompt,
                               api_key=os.environ.get('OPENAI_API_KEY', ''), size=args.size, model=args.model)
            print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, RuntimeError, KeyError, TypeError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
