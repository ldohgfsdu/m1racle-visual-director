"""Check completeness and decisions of supplied visual reviews, not image quality itself."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
STYLES = json.loads((ROOT/'references/style_acceptance.json').read_text(encoding='utf-8'))['profiles']
HARD = ('identity', 'count', 'geometry', 'composition', 'color', 'role_isolation',
        'aspect_ratio', 'transparency', 'ornament_policy')
GENERAL = ('technique', 'form_following_marks', 'thumbnail_readability', 'moire')


def review(record, source, output):
    if not isinstance(record, dict):
        raise ValueError('Review must be an object')
    for key, path in (('source_sha256', source), ('output_sha256', output)):
        if record.get(key) != hashlib.sha256(Path(path).read_bytes()).hexdigest():
            raise ValueError('Review evidence does not match '+key)
    if Path(source).resolve() == Path(output).resolve():
        raise ValueError('Source and generated output must be separate files')
    if record['source_sha256'] == record['output_sha256']:
        raise ValueError('Unchanged source cannot verify a generated engraving')
    profile = record.get('profile')
    if not isinstance(profile, str) or (profile not in STYLES and profile != 'BASE'):
        raise ValueError('Unknown review profile')
    technique = record.get('technique')
    if not isinstance(technique, str) or technique not in {'T01','T02','T03','T04','T05','INHERIT'}:
        raise ValueError('Unknown review technique')
    # A conflicting T override cannot be represented as preserved I recipe.
    compatible = profile == 'BASE' or technique == STYLES[profile]['technique_id']
    required = list(HARD)+list(GENERAL)
    if profile != 'BASE' and compatible:
        required += list(STYLES[profile]['required'])
    checks = record.get('checks', {})
    if not isinstance(checks, dict) or set(checks)-set(required):
        raise ValueError('Unknown review checks')
    issues, pending = [], []
    for name in required:
        item = checks.get(name, {'status':'UNVERIFIED'})
        if not isinstance(item, dict) or not isinstance(item.get('status'), str) or item.get('status') not in {'PASS','ISSUE','UNVERIFIED'}:
            raise ValueError('Invalid review status: '+name)
        status = item['status']
        if status != 'UNVERIFIED':
            for field in ('evidence','region'):
                if not isinstance(item.get(field), str) or not item[field].strip():
                    raise ValueError('Reviewed check requires '+field+': '+name)
        if status == 'ISSUE': issues.append(name)
        if status == 'UNVERIFIED': pending.append(name)
    hard_issues = [name for name in issues if name in HARD]
    hard_pending = [name for name in pending if name in HARD]
    status = ('REJECTED' if hard_issues else 'UNVERIFIED' if hard_pending else
              'REPAIR_REQUIRED' if issues else 'UNVERIFIED' if pending else
              'RECIPE_NOT_APPLIED' if not compatible else 'PASS')
    return {'status':status, 'hard_failures':hard_issues, 'issues':issues,
            'pending':pending, 'recipe_applied':compatible,
            'may_claim_success':status == 'PASS',
            'review_basis':'Supplied visual observations bound to file hashes; not independent automated perception',
            'repairs':[{'check':name, 'region':checks[name]['region'],
                        'observed_problem':checks[name]['evidence'],
                        'instruction':'Repair only this observed defect; preserve all approved content, palette and other regions.'}
                       for name in (hard_issues or issues)]}


def summarize_benchmark(records):
    """Keep failed and unverified attempts in the denominator; no aesthetic win-rate inference."""
    if not isinstance(records, list):
        raise ValueError('Benchmark results must be a list')
    statuses = {'PASS':0,'REJECTED':0,'REPAIR_REQUIRED':0,'UNVERIFIED':0,'RECIPE_NOT_APPLIED':0}
    seen = set()
    for item in records:
        if not isinstance(item, dict) or not isinstance(item.get('run_id'), str) or not item['run_id'].strip():
            raise ValueError('Each attempt needs a run_id')
        if item['run_id'] in seen or not isinstance(item.get('status'), str) or item.get('status') not in statuses:
            raise ValueError('Duplicate attempt or invalid result')
        seen.add(item['run_id'])
        statuses[item['status']] += 1
    return {'attempts':len(records),'statuses':statuses,
            'quality_claim':'Counts of supplied reviews only; no visual quality or aesthetic win rate inferred'}


def feedback_patch(feedback, consent=False):
    """Return an explicit preference proposal; never writes user configuration."""
    labels = {'insufficient_ornament', 'too_much_ornament', 'prefer_source_colors',
              'geometry_changed', 'looks_like_filter'}
    if type(consent) is not bool or not isinstance(feedback, list) or any(not isinstance(x, str) or x not in labels for x in feedback):
        raise ValueError('Invalid feedback or consent')
    if 'insufficient_ornament' in feedback and 'too_much_ornament' in feedback:
        raise ValueError('Conflicting ornament feedback needs clarification')
    proposal = {}
    if 'insufficient_ornament' in feedback:
        proposal['guilloche'] = 'preferred_when_compatible'
    if 'too_much_ornament' in feedback: proposal['guilloche'] = 'never'
    # Source color and geometry are existing edit defaults, not permission to rewrite preferences.
    return {'status':'APPROVED_PROPOSAL' if consent else 'NEEDS_CONSENT',
            'preference_patch':proposal if consent else {}, 'saved':False,
            'repair_feedback':[x for x in feedback if x in {'geometry_changed','looks_like_filter'}]}


def main():
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'): stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', required=True, type=Path)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        result = review(json.loads(args.record.read_text(encoding='utf-8')),args.source,args.output)
    except (ValueError,OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['may_claim_success'] else 1


if __name__ == '__main__':
    sys.exit(main())
