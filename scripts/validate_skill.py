#!/usr/bin/env python3
"""Static, dependency-free validation of the m1racle-visual-director Skill.

This does not test agent intelligence or generated image fidelity.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_ROUTES = {None, 'T2I', 'REF-CREATE', 'TRANSFORM', 'LOCAL-EDIT', 'COMPOSITE'}
STYLE_IDS = {
    'photo-documentary', 'photo-studio-product', 'photo-cinematic', 'archviz',
    'editorial-vector', 'editorial-ink', 'soft-3d', 'isometric',
    'watercolor-gouache', 'ink-wash', 'gongbi', 'banknote-intaglio',
    'steel-engraving-mono', 'woodcut', 'scientific-plate', 'pixel-art',
    'typographic-poster',
}

def verify():
    errors = []
    manifest = ROOT / 'SKILL.md'
    if not manifest.is_file():
        return ['Missing SKILL.md']
    raw = manifest.read_text(encoding='utf-8')
    fm = re.match(r'\A---\n(.*?)\n---\n', raw, re.S)
    if not fm:
        return ['Missing YAML frontmatter']
    name_match = re.search(r'^name:\s*(.+)$', fm[1], re.M)
    desc_match = re.search(r'^description:\s*(.*)$', fm[1], re.M)
    name = name_match[1].strip() if name_match else None
    desc = desc_match[1].strip() if desc_match else ''
    if not name or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name):
        errors.append(f'Invalid name: {name}')
    if name != ROOT.name:
        errors.append(f'Directory/name mismatch: {ROOT.name} != {name}')
    if not 1 <= len(desc) <= 1024:
        errors.append(f'Description length invalid: {len(desc)}')
    # Verify references declared in main skill point to on-disk files.
    for href in re.findall(r'\]\((references/[^)#]+|evals/[^)#]+)\)', raw):
        if not (ROOT / href).is_file():
            errors.append(f'Broken link: {href}')
    tests = ROOT / 'evals/cases.json'
    if not tests.is_file():
        return errors + ['Missing cases.json']
    try:
        data = json.loads(tests.read_text(encoding='utf-8'))
        cases = data['cases']
    except (ValueError, KeyError) as exc:
        return errors + [f'Invalid cases JSON: {exc}']
    ids = set()
    counts = Counter()
    for case in cases:
        ident = case.get('id')
        if ident in ids:
            errors.append(f'Duplicate test id: {ident}')
        ids.add(ident)
        route = case.get('expected_route')
        style = case.get('expected_style')
        if route not in ALLOWED_ROUTES:
            errors.append(f'{ident} unknown route: {route}')
        if style is not None and style not in STYLE_IDS:
            errors.append(f'{ident} unknown style: {style}')
        if not case.get('request') or not case.get('guardrail'):
            errors.append(f'{ident} missing request or guardrail')
        if not isinstance(case.get('required_evidence'), list) or not case['required_evidence']:
            errors.append(f'{ident} missing required_evidence')
        counts[route] += 1
    for route in ALLOWED_ROUTES:
        if counts[route] < 2:
            errors.append(f'Insufficient examples for {route}: {counts[route]} (need >=2)')
    # Check that all primary mode names and all important rules appear in the core instruction.
    for token in ('T2I', 'REF-CREATE', 'TRANSFORM', 'LOCAL-EDIT', 'COMPOSITE', '保留', '风格', '工具', '验证'):
        if token not in raw:
            errors.append(f'Missing critical contract token: {token}')
    return errors

if __name__ == '__main__':
    failures = verify()
    if failures:
        print('STATIC CHECK: FAIL')
        for failure in failures:
            print(' -', failure)
        sys.exit(1)
    print('STATIC CHECK: PASS')
    print('Skill: m1racle-visual-director')
    print('Evaluation fixtures:', len(json.loads((ROOT / 'evals/cases.json').read_text(encoding='utf-8'))['cases']))
    print('NOTE: agent behavior and image quality NOT evaluated by this static check.')
