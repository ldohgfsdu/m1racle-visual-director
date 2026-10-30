#!/usr/bin/env python3
"""Offline prompt templates; no rendering, vision or automatic translation."""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = '1.3.0'
PROFILES = json.loads((ROOT / 'references/profiles.json').read_text(encoding='utf-8'))['profiles']
TECHNIQUES = json.loads((ROOT / 'references/techniques.json').read_text(encoding='utf-8'))['techniques']
PALETTES = json.loads((ROOT / 'references/palettes.json').read_text(encoding='utf-8'))['palettes']
BASE = {
    'name': '中性母风格', 'en': 'Neutral engraving foundation',
    'technique_id': 'T01', 'palette_id': 'P00',
    'recipe_zh': '只围绕主体结构安排主技法，不带入任何场景、情绪或配色预设。',
    'recipe_en': 'Let the main technique serve subject geometry; add no scene, mood or color recipe.',
}
DNA_ZH = ('将内容转为可辨的凹版印痕视觉：先识别主体体积、材质、转折和透视，再完全交由当前唯一主技法建调子。'
          '局部痕迹须贴合对应形体；焦点清楚，缩略图轮廓可读。'
          '只模拟纸面与油墨的视觉质感，不声称真实印版或真实分色印刷。'
          '禁止摄影底图叠纹、整幅同向条纹、摩尔纹、无根据的噪点、文字水印及新增物体。')
DNA_EN = ('Interpret visible form in an intaglio-print aesthetic: first identify volume, material, contours and perspective, '
          'then rely on exactly ONE chosen dominant mark-making method for all tone construction. '
          'Local marks must belong to the corresponding form; keep focal details and thumbnail silhouettes legible. '
          'Suggest ink and paper without claiming physical plates or separations. '
          'No photographic texture overlays, picture-wide stripes, moire, unmotivated noise, watermarks, lettering or new objects.')


def positive_selection_text(text: str) -> str:
    """Remove common negative clauses for selection only; retain full prompt input."""
    s = text.casefold()
    stop = r'[，,。.;；!！?？\n]'
    zh = r'(?:不要|不画|不加|不添加|不需要|无需|没有|禁止|避免|去掉|删除|移除|不含|无(?=人物|文字|花|樱|装饰|底纹|船|港口|人像|肖像))'
    s = re.sub(zh + r'.*?(?=' + stop + r'|但|而是|只(?:画|保留|要|用)|改为|$)', ' ', s)
    en = r'\b(?:no|without|exclude|excluding|avoid|not(?!\s+only\b))\b'
    return re.sub(en + r'.*?(?=' + stop + r'|\bbut\b|\binstead\b|\bonly\b|$)', ' ', s)


def select_profile(text: str) -> tuple[str, dict[str, int]]:
    """Text hints, never semantic/visual confidence scores. Unknown -> neutral base."""
    positive = positive_selection_text(text)
    scores = {ident: 0 for ident in PROFILES}
    for ident, p in PROFILES.items():
        for term in p['terms']:
            pattern = re.escape(term.casefold())
            if re.search(r'[a-z]', term, re.I):
                pattern = r'(?<![a-z0-9])' + pattern + r'(?![a-z0-9])'
            if re.search(pattern, positive):
                scores[ident] += 1
    best = max(scores, key=scores.get)
    return (best if scores[best] else 'BASE'), scores


def image_info(path: str) -> str:
    p = Path(path)
    if not p.is_file():
        raise ValueError(f'Image not found: {path}')
    try:
        from PIL import Image
        with Image.open(p) as im:
            im.verify()
        with Image.open(p) as im:
            return f'image={p.name}; size={im.width}x{im.height}; format={im.format}; semantic content NOT evaluated'
    except ImportError:
        return f'image={p.name}; exists; Pillow unavailable; file content and dimensions NOT verified'
    except Exception as exc:
        raise ValueError(f'Cannot parse image: {path}: {exc}') from exc


def checked_ratio(ratio: str) -> str:
    ratio = ratio.strip()
    if ratio and not re.fullmatch(r'[1-9][0-9]{0,3}:[1-9][0-9]{0,3}', ratio):
        raise ValueError('--ratio must be positive integers such as 1:1 or 16:9')
    return ratio


def theme_has_color_instruction(subject: str) -> bool:
    """Common explicit color clauses only; not a general language parser."""
    zhcolors = r'(?:黑白|单色|灰度|石墨灰|红黑|黑红|[蓝粉红绿青紫黄黑白灰赭]色)'
    zhdir = r'(?:只用|仅用|仅限|只使用|使用|采用|保持|保留|不要|禁止|避免|不使用|不用)'
    encolors = r'\b(?:monochrome|grayscale|greyscale|black\s*(?:and|&)\s*white|red|blue|pink|green|gray|grey|black|white)\b'
    endir = r'\b(?:only|use|preserve|retain|keep|no|without|avoid)\b'
    return any(re.search(d+r'[^，,。.;；\n]{0,48}?'+c, subject, re.I)
               for d,c in ((zhdir,zhcolors),(endir,encolors)))


def theme_forbids_filigree(subject: str) -> bool:
    zh = r'(?:不要|禁止|不加|不添加|无|避免)[^，,。.;；\n]{0,24}(?:底纹|装饰纹)'
    en = r'\b(?:no|without|avoid)\b[^,.;\n]{0,32}\b(?:filigree|guilloche|decoration)\b'
    return bool(re.search(zh, subject) or re.search(en, subject, re.I))


def resolve_palette(p: dict, mode: str, palette: str, subject: str = '', palette_id: str = 'auto') -> dict:
    # An explicit palette in the text is allowed to override a selected default palette ID.
    if palette_id != 'auto' and palette_id not in PALETTES:
        raise ValueError('Unknown --palette-id: ' + palette_id)
    if palette.strip():
        return {'source': 'user', 'id': None, 'zh': palette.strip(), 'en': palette.strip()}
    if theme_has_color_instruction(subject):
        return {'source': 'subject', 'id': None,
                'zh': '严格遵守主题中的明确颜色、保色和禁用色要求，不使用任何预设配色。',
                'en': 'Follow explicit color, color-preservation, and exclusion instructions in the theme; use no preset palette.'}
    if palette_id == 'auto' and mode in {'redraw', 'refine'}:
        return {'source': 'source_image', 'id': None,
                'zh': '继承内容原图的现有配色、纸底和大色块关系。',
                'en': "Inherit the content image's existing palette, paper tone and major color relationships."}
    actual_id = palette_id if palette_id != 'auto' else p['palette_id']
    entry = PALETTES[actual_id]
    return {'source': ('palette_id' if palette_id != 'auto' else ('preset' if p is not BASE else 'neutral')),
            'id': actual_id, 'zh': entry['palette_zh'], 'en': entry['palette_en']}


def resolve_technique(profile: str, mode: str, technique_id: str = 'auto') -> tuple[str, dict | None]:
    if technique_id != 'auto' and technique_id not in TECHNIQUES and technique_id != 'INHERIT':
        raise ValueError('Unknown technique: ' + technique_id)
    if technique_id == 'INHERIT' and mode != 'refine':
        raise ValueError('INHERIT is for existing engraving refinement only')
    if technique_id == 'auto':
        # BASE + refine inherits; if a user explicitly chooses a recipe, that recipe remains decisive.
        actual = 'INHERIT' if mode == 'refine' and profile == 'BASE' else PROFILES.get(profile, BASE)['technique_id']
    else:
        actual = technique_id
    return actual, TECHNIQUES.get(actual)


def background_prompts(policy: str, editing: bool) -> tuple[str, str]:
    if policy == 'none':
        return ('不使用装饰性 guilloché 扭索底纹；保留主题需要的背景内容。',
                'Use no decorative guilloche filigree; retain background content required by the theme.')
    if policy == 'guilloche':
        return ('仅在可用背景留白中加入规则而克制的 guilloché 扭索曲线，靠近主体时减弱；不得遮挡或移动原有物体。',
                'Add restrained cyclic guilloche curves only in available background negative space, fading near subjects; do not cover or move existing objects.')
    if editing:
        return ('继承原背景及其装饰程度，不新增原图没有的装饰底纹。',
                'Preserve the original background and its existing degree of decoration; introduce no new decorative filigree.')
    return ('背景服从主题与留白需求；仅在确有空间且有助于构图时可少量使用 guilloché 扭索纹，简洁画面可完全省略。',
            'Let the theme and negative space determine the background. Optional restrained guilloche is allowed only where useful; omit it entirely for a clean composition.')


def make_prompts(subject: str, profile: str, mode: str, role: str,
                 ratio: str, palette: str, preserve: str, *, background: str = 'auto',
                 fidelity: str = 'auto', visual_notes: str = '', style_reference: bool = False,
                 technique_id: str = 'auto', palette_id: str = 'auto') -> dict:
    if profile not in PROFILES and profile != 'BASE':
        raise ValueError(f'Unknown profile: {profile}')
    if mode not in {'generate', 'redraw', 'refine'} or role not in {'source', 'style', 'none'}:
        raise ValueError('Resolve mode and image role before building prompts')
    editing = mode != 'generate'
    if editing and role != 'source':
        raise ValueError('Editing requires a content-source image role')
    if not editing and role == 'source':
        raise ValueError('A content-source image is an edit target; choose redraw/refine or role style')
    if background not in {'auto', 'none', 'guilloche'} or fidelity not in {'auto', 'strict', 'balanced', 'free'}:
        raise ValueError('Invalid background or fidelity policy')
    ratio = checked_ratio(ratio)
    p = PROFILES.get(profile, BASE)
    requirements = subject + ('；保留' + preserve if preserve.strip() else '')
    colors = resolve_palette(p, mode, palette, requirements, palette_id=palette_id)
    actual_technique, technique = resolve_technique(profile, mode, technique_id)
    if background == 'auto' and theme_forbids_filigree(requirements):
        background = 'none'
    fidelity = ('strict' if editing else 'balanced') if fidelity == 'auto' else fidelity
    s = subject.strip() or '[填入主题，或描述内容原图与本次修改]'
    leads = {
        'generate': ('依据主题原创构图；风格资料只提供表现技法，不提供场景内容。',
                     'Compose the requested theme independently; style material supplies technique, never scene content.'),
        'redraw': ('以上传图为内容源，从零用版刻线条重建画面，不在照片表面叠纹。',
                   'Treat the upload as the content source and redraw in engraved linework rather than overlaying a photograph.'),
        'refine': ('精修上传的既有版画，仅处理可见断线、脏污、摩尔纹或失真，未要求修改的区域和设计保持稳定。',
                   'Refine the existing engraving only where visible broken lines, artifacts, moire or distortions require repair; keep other regions and design stable.'),
    }
    zh = [f'主题与用户要求：{s}', leads[mode][0]]
    en = [f'Theme and user requirements (verbatim): {s}', leads[mode][1]]
    if editing:
        locks = {
            'strict': ('严格保真：保留主体身份、数量、轮廓、姿态、比例、位置、视点、构图及识别性细节；不得增加或删除场景物体。',
                       'Strict fidelity: preserve subject identity, count, silhouette, pose, proportions, position, viewpoint, composition and distinctive details; add or remove no scene objects.'),
            'balanced': ('平衡改绘：保留主体身份、数量、姿态与空间关系，可简化次要肌理；不得添加无关物体。',
                         'Balanced redraw: preserve identity, count, pose and spatial relationships; simplify secondary texture without adding unrelated objects.'),
            'free': ('自由改绘：允许重新组织构图与次要细节，仍遵守主题、明确保留项和禁止项，不添加无关物体。',
                     'Free reinterpretation: composition and secondary detail may change within the requested theme, explicit invariants and exclusions; add no unrelated objects.'),
        }
        zh.append(locks[fidelity][0]); en.append(locks[fidelity][1])
    if role == 'style' or style_reference:
        zh.append('风格参考图只提供刻线、印刷质感与经用户允许的色彩；不得继承其中的物体、布局、透视、文字或故事。内容原图与风格参考须分别标记。')
        en.append('Style references supply line technique, print texture and only colors permitted by the user; never inherit their objects, layout, perspective, lettering or narrative. Label edit targets and style references separately.')
    if visual_notes.strip():
        zh.append('用户或视觉助手提供的观察记录（非 CLI 识图结论）：' + visual_notes.strip())
        en.append('Observations supplied by the user or a vision agent, not inferred by this CLI: ' + visual_notes.strip())
    zh.append(DNA_ZH); en.append(DNA_EN)
    if technique:
        zh.append(f"主雕刻技法 {actual_technique}：{technique['name_zh']}。主导痕迹：{technique['primary_zh']} 调子构成：{technique['tone_zh']} 边缘：{technique['edge_zh']} 排除：{technique['avoid_zh']}")
        en.append(f"Dominant engraving technique {actual_technique}: {technique['name_en']}. Primary marks: {technique['primary_en']} Tone construction: {technique['tone_en']} Edges: {technique['edge_en']} Exclusions: {technique['avoid_en']}")
        if technique.get('application_zh'):
            zh.append(technique['application_zh'])
            en.append(technique['application_en'])
    else:
        zh.append('主技法继承：保留原有版画的主要调子构成、线条或点刻性质与边缘质感，仅修复用户授权的区域。')
        en.append("Inherit existing dominant mark-making: retain the source print's tonal mechanism and edge character; repair authorized regions only.")
    recipe_applied = profile != 'BASE' and actual_technique == p['technique_id']
    if recipe_applied:
        zh.append(f"视觉配方 {profile}（只改变同一技法内部的节奏）：{p['recipe_zh']}")
        en.append(f"Visual recipe {profile} (rhythm within the dominant technique): {p['recipe_en']}")
    zh.append('最终配色（已解析优先级）：' + colors['zh'])
    en.append('Resolved final palette: ' + colors['en'])
    bg_zh, bg_en = background_prompts(background, editing)
    zh.append(bg_zh); en.append(bg_en)
    if preserve.strip():
        zh.append('必须保留：' + preserve.strip()); en.append('Must preserve (verbatim): ' + preserve.strip())
    if ratio:
        zh.append('画面比例：' + ratio); en.append('Aspect ratio: ' + ratio)
    elif editing:
        zh.append('沿用内容原图的画面比例，不自行裁切。')
        en.append("Keep the content image's original aspect ratio without unrequested cropping.")
    return {'style': profile, 'style_name_zh': p['name'], 'style_name_en': p['en'],
            'technique_id': actual_technique, 'technique_name_zh': technique['name_zh'] if technique else '继承原技法',
            'palette_id': colors['id'], 'palette_source': colors['source'],
            'recipe_applied': recipe_applied, 'fidelity': fidelity, 'background': background,
            'zh': '\n\n'.join(zh), 'en': '\n\n'.join(en)}


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    a = argparse.ArgumentParser(description='M1racle Intaglio 1.3.0: five techniques, eight recipes, independent palettes; prompts only')
    a.add_argument('--subject', default='', help='Theme / requirements; variables are preserved, not translated')
    a.add_argument('--visual-analysis', help='Auto selection only: observations bound to --image SHA-256; unused for explicit style or refinement')
    a.add_argument('--preferences', help='Auto selection preferences JSON; never written automatically')
    a.add_argument('--visual-notes', default='', help='Observations supplied by a person or vision-capable assistant')
    a.add_argument('--mode', choices=['auto', 'generate', 'redraw', 'refine'], default='auto')
    a.add_argument('--style', choices=['auto', 'BASE', *PROFILES], default='auto', help='Visual recipe ID (legacy I01-I08)')
    a.add_argument('--technique', choices=['auto', *TECHNIQUES, 'INHERIT'], default='auto', help='Override dominant technique; INHERIT only for refine')
    a.add_argument('--palette-id', choices=['auto', *PALETTES], default='auto', help='Independent preset palette ID; explicitly selecting one recolors even edits')
    a.add_argument('--image', help='Local content image, or sole style reference when --role style')
    a.add_argument('--style-image', help='Optional separate local style reference')
    a.add_argument('--role', choices=['auto', 'source', 'style', 'none'], default='auto')
    a.add_argument('--ratio', default='')
    a.add_argument('--palette', default='', help='Explicit final palette; replaces preset colors')
    a.add_argument('--preserve', default='')
    a.add_argument('--background', choices=['auto', 'none', 'guilloche'], default='auto')
    a.add_argument('--fidelity', choices=['auto', 'strict', 'balanced', 'free'], default='auto')
    a.add_argument('--lang', choices=['zh', 'en', 'both'], default='both')
    a.add_argument('--json', action='store_true')
    args = a.parse_args(argv)
    try:
        role = args.role if args.role != 'auto' else ('source' if args.image else 'none')
        mode = args.mode if args.mode != 'auto' else ('redraw' if role == 'source' else 'generate')
        if args.image and role == 'none':
            raise ValueError('--image requires a source or style role, not none')
        if role == 'style' and not args.image:
            raise ValueError('--role style requires --image; use --style-image for a separate reference')
        probes = []
        if args.image:
            probes.append({'path': args.image, 'role': role, 'probe': image_info(args.image)})
        if args.style_image:
            if args.image and Path(args.image).resolve() == Path(args.style_image).resolve():
                raise ValueError('The same image cannot be both a content source and a separate style reference')
            probes.append({'path': args.style_image, 'role': 'style', 'probe': image_info(args.style_image)})
        ranking = None
        needs_selection = args.style == 'auto' and mode != 'refine'
        if needs_selection and args.preferences and not args.visual_analysis:
            raise ValueError('--preferences requires --visual-analysis')
        if needs_selection and args.visual_analysis:
            from visual_director import load_analysis, rank_profiles
            if role != 'source':
                raise ValueError('Visual matching requires a content-source image')
            preferences = json.loads(Path(args.preferences).read_text(encoding='utf-8')) if args.preferences else None
            ranking = rank_profiles(load_analysis(args.visual_analysis, args.image), preferences)
        selected, scores = 'BASE', {}
        if args.style != 'auto':
            selected = args.style
        elif mode == 'refine':
            selected = 'BASE'
        elif ranking:
            selected = ranking['recommended']
        else:
            selected, scores = select_profile(' '.join([args.subject, args.visual_notes]))
        prompts = make_prompts(args.subject, selected, mode, role, args.ratio, args.palette, args.preserve,
                               background=('guilloche' if ranking and args.background == 'auto' and mode != 'refine' and ranking['ornament'] == 'guilloche' and not theme_forbids_filigree(args.subject + args.preserve) else args.background), fidelity=args.fidelity,
                               visual_notes=args.visual_notes, style_reference=bool(args.style_image),
                               technique_id=args.technique, palette_id=args.palette_id)
    except (ValueError, OSError) as exc:
        a.error(str(exc))
    warnings = ['No image generated or uploaded. User-supplied variables are not automatically translated.']
    if not needs_selection and (args.visual_analysis or args.preferences):
        warnings.append('Selection-only analysis/preferences were not read: explicit style or refinement bypasses selection. Set --background and --palette explicitly when needed.')
    if role == 'source' and not args.image:
        warnings.append('Content-source prompt template only: attach the actual content image in the image tool; no source image was inspected.')
    active = [k for k, value in scores.items() if value and value == max(scores.values())]
    if not ranking and args.style == 'auto' and len(active) > 1 and mode != 'refine':
        warnings.append('Text hints tie: ' + ', '.join(active) + '; let a vision-capable assistant decide.')
    info = {'version': VERSION, 'task_mode': mode, 'image_role': role,
            'auto_style': args.style == 'auto', 'selection_basis': 'explicit style' if args.style != 'auto' else
            ('preserve existing engraving' if mode == 'refine' else 'supplied visual observations' if ranking else 'limited positive-text hints; not visual analysis'),
            'selection_scores': scores if not ranking and args.style == 'auto' and mode != 'refine' else None,
            'visual_recommendation': ranking,
            'image_probe': '; '.join(p['probe'] for p in probes), 'image_inputs': probes,
            'rendered': False, 'references_uploaded': False, 'warnings': warnings}
    if not prompts['recipe_applied'] and selected != 'BASE':
        info['warnings'].append('Recipe rhythm skipped because selected dominant technique differs from the legacy recipe mapping.')
    if args.lang != 'both':
        prompts.pop('en' if args.lang == 'zh' else 'zh')
    if args.json:
        print(json.dumps({**info, **prompts}, ensure_ascii=False, indent=2))
    else:
        print(f"Recipe: {selected} | technique: {prompts['technique_id']} | mode: {mode} | image-role: {role} | palette: {prompts['palette_source']} ({prompts['palette_id']})")
        for warning in warnings:
            print('[Note] ' + warning)
        for lang in ('zh', 'en'):
            if lang in prompts:
                print('\n--- ' + lang + ' ---\n' + prompts[lang])
    return 0


if __name__ == '__main__':
    sys.exit(main())
