#!/usr/bin/env python3
"""Dependency-free validation for the explicitly invoked, fixed-style engraving skill."""
from pathlib import Path
from collections import Counter
import json,re,sys

ROOT=Path(__file__).resolve().parents[1]
NAME='m1racle-visual-director'
ROUTES={'NONE','T2I','REF-CREATE','TRANSFORM','LOCAL-EDIT','COMPOSITE'}
STYLES={None,'banknote-intaglio','steel-engraving-mono'}

def verify():
    errors=[]
    path=ROOT/'SKILL.md'
    if not path.exists(): return ['SKILL.md missing']
    raw=path.read_text('utf-8')
    fm=re.match(r'\A---\n(.*?)\n---\n',raw,re.S)
    if not fm:return ['YAML frontmatter missing']
    match=re.search(r'^name:\s*(\S+)',fm[1],re.M)
    name=match[1] if match else None
    desc=re.search(r'^description:\s*(.+)',fm[1],re.M)
    if name!=NAME:errors.append(f'Expected name {NAME}, got {name}')
    suffix=bool(re.fullmatch(re.escape(NAME)+r'-(?:main|master|[0-9a-f]{7,40})',ROOT.name))
    if ROOT.name!=NAME and not suffix:errors.append(f'Directory/name mismatch: {ROOT.name} != {NAME}')
    if not desc or not 1<=len(desc[1])<=1024:errors.append('Missing/invalid description')
    if not re.search(r'^disable-model-invocation:\s*true
    for path in re.findall(r'\]\((references/[^)#]+|evals/[^)#]+)\)',raw):
        if not (ROOT/path).is_file():errors.append(f'Broken link: {path}')
    for term in ['显式','不自动','T2I','REF-CREATE','TRANSFORM','LOCAL-EDIT','COMPOSITE','Guilloché','直接']:
        if term not in raw:errors.append(f'Missing policy token: {term}')
    try:cases=json.loads((ROOT/'evals/cases.json').read_text('utf-8'))['cases']
    except (ValueError,KeyError,FileNotFoundError) as exc:return errors+[f'No valid eval cases: {exc}']
    counts=Counter();ids=set()
    for case in cases:
        ident=case.get('id');active=case.get('expected_active');route=case.get('expected_route');style=case.get('expected_style')
        if not ident or ident in ids:errors.append(f'Invalid ID: {ident}')
        ids.add(ident)
        if not isinstance(active,bool):errors.append(f'{ident}: active flag missing')
        if route not in ROUTES:errors.append(f'{ident}: unexpected route {route}')
        if style not in STYLES:errors.append(f'{ident}: style not part of engraving family: {style}')
        if not case.get('request') or not case.get('guardrail') or not case.get('required_evidence'):errors.append(f'{ident}: incomplete case')
        if active and (route=='NONE' or not style):errors.append(f'{ident}: active must have engraving route and style')
        if active is False and (route!='NONE' or style is not None):errors.append(f'{ident}: inactive must not route')
        counts[route]+=1
    for r in ROUTES:
        if counts[r]<2:errors.append(f'Route coverage too low: {r} ({counts[r]})')
    if len(cases)<24:errors.append('Expected at least 24 fixtures')
    return errors

if __name__=='__main__':
    errs=verify()
    if errs:
        print('STATIC CHECK: FAIL')
        for x in errs:print(' -',x)
        sys.exit(1)
    print('STATIC CHECK: PASS')
    print('Skill:',NAME)
    print('Evaluation fixtures:',len(json.loads((ROOT/'evals/cases.json').read_text('utf-8'))['cases']))
    print('Contract: explicit invocation, fixed engraving style')
    print('NOTE: agent invocation and actual image generation not tested')
,fm[1],re.M):errors.append('Explicit-only frontmatter flag missing')
    for path in re.findall(r'\]\((references/[^)#]+|evals/[^)#]+)\)',raw):
        if not (ROOT/path).is_file():errors.append(f'Broken link: {path}')
    for term in ['显式','不自动','T2I','REF-CREATE','TRANSFORM','LOCAL-EDIT','COMPOSITE','Guilloché','直接']:
        if term not in raw:errors.append(f'Missing policy token: {term}')
    try:cases=json.loads((ROOT/'evals/cases.json').read_text('utf-8'))['cases']
    except (ValueError,KeyError,FileNotFoundError) as exc:return errors+[f'No valid eval cases: {exc}']
    counts=Counter();ids=set()
    for case in cases:
        ident=case.get('id');active=case.get('expected_active');route=case.get('expected_route');style=case.get('expected_style')
        if not ident or ident in ids:errors.append(f'Invalid ID: {ident}')
        ids.add(ident)
        if not isinstance(active,bool):errors.append(f'{ident}: active flag missing')
        if route not in ROUTES:errors.append(f'{ident}: unexpected route {route}')
        if style not in STYLES:errors.append(f'{ident}: style not part of engraving family: {style}')
        if not case.get('request') or not case.get('guardrail') or not case.get('required_evidence'):errors.append(f'{ident}: incomplete case')
        if active and (route=='NONE' or not style):errors.append(f'{ident}: active must have engraving route and style')
        if active is False and (route!='NONE' or style is not None):errors.append(f'{ident}: inactive must not route')
        counts[route]+=1
    for r in ROUTES:
        if counts[r]<2:errors.append(f'Route coverage too low: {r} ({counts[r]})')
    if len(cases)<24:errors.append('Expected at least 24 fixtures')
    return errors

if __name__=='__main__':
    errs=verify()
    if errs:
        print('STATIC CHECK: FAIL')
        for x in errs:print(' -',x)
        sys.exit(1)
    print('STATIC CHECK: PASS')
    print('Skill:',NAME)
    print('Evaluation fixtures:',len(json.loads((ROOT/'evals/cases.json').read_text('utf-8'))['cases']))
    print('Contract: explicit invocation, fixed engraving style')
    print('NOTE: agent invocation and actual image generation not tested')
