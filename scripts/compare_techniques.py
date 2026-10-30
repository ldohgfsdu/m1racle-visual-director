#!/usr/bin/env python3
"""Emit five fixed-variable text prompts. NEVER generates images or uploads references."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from prompt_builder import TECHNIQUES, VERSION, image_info, make_prompts


def build_matrix(subject: str, mode: str = 'redraw', palette: str = '石墨黑与纸白',
                 background: str = 'none', ratio: str = '', fidelity: str = 'strict',
                 preserve: str = '', image: str | None = None) -> dict:
    if mode not in {'redraw','generate'}:
        raise ValueError('A/B compares redraw or generate, not inherit-only refinement')
    if image: image_info(image)  # metadata probe only, not upload or perception
    rows = []
    for t in sorted(TECHNIQUES):
        d = make_prompts(subject, 'BASE', mode, 'source' if mode == 'redraw' else 'none',
                         ratio, palette, preserve, background=background,
                         fidelity=fidelity, technique_id=t)
        rows.append({'technique_id':t,'name_zh':TECHNIQUES[t]['name_zh'],
                     'palette_source':d['palette_source'], 'zh':d['zh'], 'en':d['en']})
    return {'version':VERSION,'comparison':'five techniques; fixed recipe BASE and fixed palette',
            'mode':mode,'content_image':str(Path(image).name) if image else None,
            'image_inspected':False,'uploaded':False,'rendered':False,
            'warning': 'Text prompts only. Attach the SAME source image separately for every redraw call; real A/B remains UNVERIFIED.',
            'rows':rows}


def main(argv=None) -> int:
    for s in (sys.stdout,sys.stderr):
        if hasattr(s,'reconfigure'): s.reconfigure(encoding='utf-8')
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--subject',required=True)
    ap.add_argument('--mode',choices=['generate','redraw'],default='redraw')
    ap.add_argument('--palette',default='石墨黑与纸白')
    ap.add_argument('--background',choices=['auto','none','guilloche'],default='none')
    ap.add_argument('--ratio',default='')
    ap.add_argument('--fidelity',choices=['strict','balanced','free'],default='strict')
    ap.add_argument('--preserve',default='')
    ap.add_argument('--image',help='Source file for metadata validation only (not passed into a model)')
    ap.add_argument('--json',action='store_true')
    args=ap.parse_args(argv)
    try:
        data=build_matrix(args.subject, mode=args.mode, palette=args.palette,
                          background=args.background, ratio=args.ratio, fidelity=args.fidelity,
                          preserve=args.preserve, image=args.image)
    except ValueError as exc: ap.error(str(exc))
    if args.json:
        print(json.dumps(data,ensure_ascii=False,indent=2))
    else:
        print('WARNING: Five text prompts, zero generated images. Use the same actual input image for each output.')
        for d in data['rows']:
            print(f"\n====== {d['technique_id']} {d['name_zh']} ======\n{d['zh']}")
    return 0

if __name__=='__main__':sys.exit(main())
