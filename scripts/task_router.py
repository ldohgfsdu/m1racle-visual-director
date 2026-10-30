#!/usr/bin/env python3
"""Deterministic intent/capability gate; tool availability is passed in, never auto-detected.

This script neither renders pixels nor probes any local model, GUI, or Harness installation.
"""
from __future__ import annotations
import argparse
import json
import sys


def route(intent: str, image_backend: str, procedural_authorized: bool = False) -> dict:
    if intent not in {'image', 'prompt', 'procedural'}:
        raise ValueError('intent must be image, prompt or procedural')
    if image_backend not in {'present', 'none', 'unknown'}:
        raise ValueError('image_backend must be present, none or unknown')
    if intent == 'prompt':
        return dict(status='prompt_only', action='produce_prompt', may_render=False,
                    max_image_generations=0, max_procedural_previews=0,
                    message='Only a production prompt was requested. No image output or raster script is authorized.')
    if intent == 'procedural':
        if not procedural_authorized:
            return dict(status='needs_explicit_authorization', action='explain_algorithmic_limitations', may_render=False,
                        max_image_generations=0, max_procedural_previews=0,
                        message='Require explicit user acceptance that a procedural preview is not model-redrawn engraving.')
        return dict(status='procedural_authorized', action='procedural_preview', may_render=True,
                    max_image_generations=0, max_procedural_previews=2,
                    message='Only procedural approximation: one preview plus at most one defect-directed revision.')
    if image_backend == 'present':
        return dict(status='ready', action='call_image_generation_or_edit_tool', may_render=True,
                    max_image_generations=3, max_procedural_previews=0,
                    message='One initial generation plus at most two targeted corrections; inspect each output.')
    if procedural_authorized:
        return dict(status='procedural_authorized', action='procedural_preview', may_render=True,
                    max_image_generations=0, max_procedural_previews=2,
                    message='User accepted algorithmic approximation; label output as procedural, not AI redraw.')
    if image_backend == 'unknown':
        return dict(status='verify_once', action='check_registered_image_tools_once', may_render=False,
                    max_image_generations=0, max_procedural_previews=0,
                    message='Check the exposed tool list once. Filesystem/shell/read_image are NOT image generation tools.')
    return dict(status='blocked', action='disclose_no_image_tool_and_offer_prompt', may_render=False,
                max_image_generations=0, max_procedural_previews=0,
                message='No image output. Do not invent local Python/PowerShell engraving renderer or claim success.')


def main(argv: list[str] | None = None) -> int:
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('--intent', required=True, choices=['image', 'prompt', 'procedural'])
    a.add_argument('--image-backend', default='unknown', choices=['present', 'none', 'unknown'],
                   help='Agent must verify this from actual callable tools, not local filesystem probing')
    a.add_argument('--procedural-authorized', action='store_true',
                   help='Set only when the user explicitly agreed to algorithmic approximation')
    a.add_argument('--json', action='store_true')
    args = a.parse_args(argv)
    v = route(args.intent, args.image_backend, args.procedural_authorized)
    if args.json:
        print(json.dumps(v, ensure_ascii=False, indent=2))
    else:
        print(f"{v['status']}: {v['action']}; may_render={v['may_render']}\n{v['message']}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
