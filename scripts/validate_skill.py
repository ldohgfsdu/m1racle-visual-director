#!/usr/bin/env python3
"""Check this package's schema, complete byte manifest and behavior tests."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REQUIRED={
    'SKILL.md','README.md','agents/openai.yaml','references/style_dna.md',
    'references/profiles.md','references/profiles.json','references/decision_policy.md',
    'references/quality_checks.md','references/master_prompt_zh.md','references/master_prompt_en.md',
    'references/sample_map.md','references/runtime_policy.md','references/ab_protocol.md',
    'references/techniques.md','references/techniques.json','references/palettes.json',
    'examples/bridge_ab_prompts_zh.md',
    'assets/style-contact-sheet.jpg','scripts/prompt_builder.py','scripts/compare_techniques.py','scripts/task_router.py','tests/test_task_router.py',
    'scripts/validate_skill.py','tests/test_prompt_builder.py','tests/test_regressions.py',
    'tests/test_package.py','tests/test_technique_matrix.py','tests/ab_results_template.json',
    'tests/visual_results_v1.2.0_legacy.json','tests/visual_cases.json','tests/visual_results.json','MANIFEST.json',
}


def check_manifest_data(manifest: dict, files: dict[str,bytes]) -> list[str]:
    """Pure byte-map check, also usable in tampering regression tests."""
    errors=[]
    entries=manifest.get('files')
    if not isinstance(entries,list):
        return ['manifest files must be a list']
    seen=set()
    for item in entries:
        if not isinstance(item,dict) or not isinstance(item.get('path'),str):
            errors.append('invalid manifest entry');continue
        name=item['path']
        if name in seen:
            errors.append('duplicate manifest path: '+name)
        seen.add(name)
        if Path(name).is_absolute() or '..' in Path(name).parts or '\\' in name:
            errors.append('unsafe manifest path: '+name);continue
        if name not in files:
            errors.append('missing file: '+name);continue
        data=files[name]
        if len(data)!=item.get('bytes'):
            errors.append('size mismatch: '+name)
        if hashlib.sha256(data).hexdigest()!=item.get('sha256'):
            errors.append('hash mismatch: '+name)
    if seen!=set(files):
        errors.append('manifest coverage mismatch: '+', '.join(sorted(seen ^ set(files))))
    return errors


def check_package(root: Path) -> list[str]:
    errors=[]
    for name in sorted(REQUIRED):
        path=root/name
        if not path.is_file() or not path.stat().st_size:
            errors.append('missing or empty: '+name)
    examples=sorted((root/'assets/examples').glob('*.jpg'))
    if len(examples)!=8 or {p.name.split('_')[0] for p in examples}!={f'I{i:02d}' for i in range(1,9)}:
        errors.append('expected exactly the eight I01-I08 sample images')
    files={}
    for path in root.rglob('*'):
        if path.relative_to(root).parts[0] == '.git':
            continue
        if path.is_symlink():
            errors.append('nonportable symbolic link: '+str(path.relative_to(root)))
            continue
        if path.is_file() and '__pycache__' not in path.parts and path.suffix!='.pyc':
            name=path.relative_to(root).as_posix()
            if name!='MANIFEST.json': files[name]=path.read_bytes()
    try:
        text=(root/'SKILL.md').read_text(encoding='utf-8')
        # Validate the deliberately small YAML subset used by this package.
        if not re.match(r'\A---\nname: m1racle-intaglio-director\ndescription: >-\n(?:  .+\n)+---\n',text):
            errors.append('invalid SKILL.md frontmatter')
        data=json.loads((root/'references/profiles.json').read_text(encoding='utf-8'))
        techdata=json.loads((root/'references/techniques.json').read_text(encoding='utf-8'))
        paldata=json.loads((root/'references/palettes.json').read_text(encoding='utf-8'))
        if data.get('schema_version')!=2 or data.get('version')!='1.3.0':
            errors.append('invalid profile schema/version')
        if techdata.get('schema_version')!=1 or techdata.get('version')!='1.3.0':
            errors.append('invalid technique schema/version')
        if paldata.get('schema_version')!=1 or paldata.get('version')!='1.3.0':
            errors.append('invalid palette schema/version')
        profiles=data['profiles'];tech=techdata['techniques'];pal=paldata['palettes']
        if set(profiles)!={f'I{i:02d}' for i in range(1,9)}:
            errors.append('incomplete preset IDs')
        if set(tech)!={f'T{i:02d}' for i in range(1,6)}:
            errors.append('incomplete five technique families')
        if set(pal)!={f'P{i:02d}' for i in range(9)}:
            errors.append('incomplete palette IDs')
        doc=(root/'references/profiles.md').read_text(encoding='utf-8')
        tdoc=(root/'references/techniques.md').read_text(encoding='utf-8')
        for ident,t in tech.items():
            for field in ('name_zh','name_en','primary_zh','primary_en','tone_zh','tone_en','edge_zh','edge_en','avoid_zh','avoid_en'):
                if not t.get(field):errors.append(f'{ident}: missing {field}')
            for x in (ident,t.get('name_zh',''),t.get('primary_zh','')):
                if x and x not in tdoc: errors.append(f'{ident}: stale technique documentation')
        for ident,q in pal.items():
            for field in ('name_zh','name_en','palette_zh','palette_en'):
                if not q.get(field):errors.append(f'{ident}: missing {field}')
            for x in (ident,q.get('name_zh',''),q.get('palette_zh','')):
                if x and x not in doc:errors.append(f'{ident}: stale palette documentation')
        for ident,p in profiles.items():
            for key in ('name','en','technique_id','palette_id','recipe_zh','recipe_en','terms'):
                if not p.get(key):errors.append(f'{ident}: missing {key}')
            if not isinstance(p.get('terms'),list): errors.append(ident+': terms must be a list')
            if p.get('technique_id') not in tech: errors.append(ident+': missing referenced technique')
            if p.get('palette_id') not in pal: errors.append(ident+': missing referenced palette')
            for key in ('name','recipe_zh'):
                if p.get(key,'') not in doc:errors.append(ident+': stale profile documentation '+key)
            if ident not in doc:errors.append(ident+': missing recipe documentation')
        meta=(root/'agents/openai.yaml').read_text(encoding='utf-8')
        if '$m1racle-intaglio-director' not in meta:
            errors.append('missing skill name in default invocation')
        for path in root.rglob('*.md'):
            if path.relative_to(root).parts[0] == '.git':
                continue
            for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
                if '://' not in target and not target.startswith('#'):
                    linked=(path.parent/target.split('#')[0]).resolve()
                    if not linked.is_relative_to(root.resolve()) or not linked.is_file():
                        errors.append('broken/local escaping link: '+str(path.relative_to(root))+' -> '+target)
        manifest=json.loads((root/'MANIFEST.json').read_text(encoding='utf-8'))
        if manifest.get('name')!='m1racle-intaglio-director' or manifest.get('version')!='1.3.0':
            errors.append('manifest identity/version mismatch')
        errors.extend(check_manifest_data(manifest,files))
        cases=json.loads((root/'tests/visual_cases.json').read_text(encoding='utf-8'))['cases']
        results=json.loads((root/'tests/visual_results.json').read_text(encoding='utf-8'))
        if len({c['id'] for c in cases})!=len(cases): errors.append('duplicate visual case ID')
        if len([c for c in cases if c['id'].startswith('AB-')])!=15:
            errors.append('expected 15 fixed-variable A/B cases')
        if results.get('version')!='1.3.0':errors.append('visual results must be v1.3')
        if any(r.get('status')!='UNVERIFIED' for r in results['results']):
            errors.append('unexecuted v1.3 trials must be UNVERIFIED')
        if any(r['id'] not in {c['id'] for c in cases} for r in results['results']):
            errors.append('visual result references an unknown case')
    except (OSError,ValueError,KeyError,TypeError) as exc:
        errors.append('invalid package data: '+str(exc))
    return errors


def main(argv=None) -> int:
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--structure-only',action='store_true',help='Skip behavior tests')
    args=a.parse_args(argv)
    errors=check_package(ROOT)
    if errors:
        print('PACKAGE CHECK FAILED:\n'+'\n'.join(errors),file=sys.stderr)
        return 1
    print('PASS: structure, preset consistency, links and complete file hashes',flush=True)
    if not args.structure_only:
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
        result=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(ROOT/'tests'),'-v'],cwd=ROOT,env=env)
        if result.returncode: return result.returncode
    print('PASS: package checks complete. Visual quality is not inferred from unit tests.')
    return 0


if __name__=='__main__':
    sys.exit(main())
