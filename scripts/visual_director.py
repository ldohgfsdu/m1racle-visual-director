"""Rank supplied visual observations; never performs image perception or rendering."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = json.loads((ROOT/'references/visual_matching.json').read_text(encoding='utf-8'))
PROFILES = json.loads((ROOT/'references/profiles.json').read_text(encoding='utf-8'))['profiles']


def rank_profiles(analysis, preferences=None):
    if not isinstance(analysis, dict) or set(analysis) != {'image_sha256', 'observations'}:
        raise ValueError('Visual analysis requires image_sha256 and observations')
    digest = analysis['image_sha256']
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
        raise ValueError('Invalid image_sha256')
    observations = analysis['observations']
    keys = [key for group in RULES['groups'].values() for key in group]
    if not isinstance(observations, dict) or not observations or set(observations) - set(keys):
        raise ValueError('Unknown or empty visual observations')
    for key, observation in observations.items():
        if not isinstance(observation, dict) or set(observation) != {'value', 'evidence'}:
            raise ValueError('Each observation requires value and evidence')
        value = observation['value']
        if type(value) not in (float, int) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError('Observation values must be finite numbers from 0 to 1')
        if not isinstance(observation['evidence'], str) or not observation['evidence'].strip():
            raise ValueError('Visual evidence must be nonempty text')
    preferences = {} if preferences is None else preferences
    if not isinstance(preferences, dict) or set(preferences) - {'recommendation_count', 'guilloche', 'render_strategy', 'style_selection', 'aesthetic_preference'}:
        raise ValueError('Unknown preferences; only explicit supported settings are accepted')
    count = preferences.get('recommendation_count', 3)
    ornament = preferences.get('guilloche', 'never')
    if type(count) is not int or not 1 <= count <= 3 or ornament not in ('never', 'preferred_when_compatible'):
        raise ValueError('Invalid recommendation count or guilloche preference')
    if preferences.get('render_strategy', 'best_first') != 'best_first':
        raise ValueError('Only best_first rendering is supported')
    if preferences.get('style_selection', 'auto') != 'auto':
        raise ValueError('Use --style for explicit selection')
    aesthetic = preferences.get('aesthetic_preference', {})
    allowed = {'detail':('high','adaptive'), 'geometry_fidelity':('strict',), 'engraving_character':('precise','adaptive'), 'guilloche':('never','preferred_when_compatible'), 'color':('adaptive',), 'atmosphere':('elegant_and_detailed','adaptive')}
    if not isinstance(aesthetic, dict) or set(aesthetic)-set(allowed)-{'preferred_visual_identity'}:
        raise ValueError('Unsupported aesthetic preference')
    for key, value in aesthetic.items():
        if key == 'preferred_visual_identity':
            if not isinstance(value, list) or any(x not in ('banknote_engraving','classical_intaglio') for x in value):
                raise ValueError('Unsupported visual identity')
        elif value not in allowed[key]:
            raise ValueError('Unsupported aesthetic value: '+key)
    ornament = preferences.get('guilloche', aesthetic.get('guilloche', 'never'))
    rows = []
    for ident, targets in RULES['targets'].items():
        parts = {}
        reasons = []
        for group, fields in RULES['groups'].items():
            # Missing observations contribute no positive evidence, rather than guessed values.
            parts[group] = sum(1-abs(observations[k]['value']-targets[keys.index(k)])
                               for k in fields if k in observations)/len(fields)
        score = round(100*sum(parts[g]*w for g,w in RULES['weights'].items()), 2)
        # Explicit preferences are a bounded tie-breaker, never an image-quality claim.
        bonus = 0
        if aesthetic.get('engraving_character') == 'precise' and ident in ('I01','I06'):
            bonus += 2
        if aesthetic.get('detail') == 'high' and ident == 'I08':
            bonus += 2
        if 'banknote_engraving' in aesthetic.get('preferred_visual_identity', []) and ident in ('I01','I06'):
            bonus += 2
        if aesthetic.get('atmosphere') == 'elegant_and_detailed' and ident in ('I01','I05','I07'):
            bonus += 1
        score = round(min(100, score + bonus), 2)
        for k in observations:
            if abs(observations[k]['value']-targets[keys.index(k)]) <= .25:
                reasons.append(k + ': ' + observations[k]['evidence'])
        rows.append({'profile': ident, 'score': score, 'components': parts, 'preference_bonus':bonus, 'reasons': reasons})
    rows.sort(key=lambda row: (-row['score'], row['profile']))
    coverage = len(observations)/len(keys)
    if coverage < .6 or rows[0]['score'] < 60:
        rows.insert(0, {'profile':'BASE', 'score':None, 'components':{},
                       'reasons':['Insufficient evidence or poor recipe fit; use neutral foundation.']})
    winner = rows[0]['profile']
    compatible = (observations.get('negative_space', {}).get('value', 0) >= .65 and
                  observations.get('density', {}).get('value', 1) <= .6)
    return {'recommended':winner, 'technique':PROFILES.get(winner, {}).get('technique_id', 'T01'),
            'palette':PROFILES.get(winner, {}).get('palette_id', 'P00'),
            'ornament':'guilloche' if compatible and ornament == 'preferred_when_compatible' else 'none',
            'candidates':rows[:count], 'alternatives':[x['profile'] for x in rows[1:count]],
            'confidence':'medium' if coverage >= .8 and winner != 'BASE' and rows[0]['score']-rows[1]['score'] >= 5 else 'low',
            'evidence_coverage':coverage, 'requires_visual_validation':True,
            'score_meaning':'Uncalibrated rule fit, not aesthetic quality or success probability',
            'render_strategy':'best_first', 'rendered':False}


def load_analysis(path, image):
    analysis = json.loads(Path(path).read_text(encoding='utf-8'))
    if not image or not isinstance(analysis, dict) or analysis.get('image_sha256') != hashlib.sha256(Path(image).read_bytes()).hexdigest():
        raise ValueError('Visual analysis must match the actual --image SHA-256')
    return analysis
