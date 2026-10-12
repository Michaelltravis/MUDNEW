#!/usr/bin/env python3
"""Scan src/web_isometric/art/ and emit src/web_isometric/art/manifest.json.

Foozle character packs ship one strip per animation per direction
(<Dir>/Png/<Name><Dir><Anim>.png, 48px frames); tilesets ship a single atlas.
The client loads this manifest instead of hard-coding sheet geometry.
"""
import json, os, re, struct, sys
ROOT = os.path.join(os.path.dirname(__file__), '..', 'src', 'web_isometric', 'art')
DIRS = ('Down', 'Up', 'Left', 'Right')

def dim(p):
    with open(p, 'rb') as f:
        f.seek(16); return struct.unpack('>II', f.read(8))

def rel(p): return os.path.relpath(p, ROOT).replace(os.sep, '/')

manifest = {'tile': 32, 'actors': {}, 'tilesets': {}, 'sheets': {}}
for pack in sorted(os.listdir(ROOT)):
    pdir = os.path.join(ROOT, pack)
    if not os.path.isdir(pdir): continue
    pngs = []
    for base, _, files in os.walk(pdir):
        pngs += [os.path.join(base, f) for f in files if f.lower().endswith('.png')]
    # character strips: .../<Dir>/Png/<Name><Dir><Anim>.png
    strips = [p for p in pngs if '/Png/' in p.replace(os.sep, '/') and any(f'/{d}/' in p.replace(os.sep, '/') for d in DIRS)]
    if strips:
        actor = {'pack': pack, 'frame': None, 'anims': {}}
        for p in strips:
            w, h = dim(p)
            d = next(dd for dd in DIRS if f'/{dd}/' in p.replace(os.sep, '/'))
            name = os.path.splitext(os.path.basename(p))[0]
            m = re.search(rf'{d}t?(?P<anim>[A-Za-z]+?\d*)$', name)   # tolerate the "Leftt" typo in some packs
            anim = (m.group('anim') if m else name).lower()
            actor['frame'] = actor['frame'] or h
            actor['anims'].setdefault(anim, {})[d.lower()] = {'file': rel(p), 'frames': w // h, 'w': h, 'h': h}
        manifest['actors'][pack] = actor
        continue
    atlas = [p for p in pngs if re.search(r'tileset|spritesheet|_all_', p, re.I)]
    for p in atlas:
        w, h = dim(p)
        manifest['tilesets'][f'{pack}:{os.path.splitext(os.path.basename(p))[0]}'] = {'file': rel(p), 'w': w, 'h': h, 'cols': w // 32, 'rows': h // 32}
    manifest['sheets'][pack] = [{'file': rel(p), 'w': dim(p)[0], 'h': dim(p)[1]} for p in sorted(pngs) if p not in atlas]

out = os.path.join(ROOT, 'manifest.json')
json.dump(manifest, open(out, 'w'), indent=1)
print(f"actors={len(manifest['actors'])} tilesets={len(manifest['tilesets'])} sheet-packs={len(manifest['sheets'])} -> {rel(out)}")
for k, a in manifest['actors'].items():
    print(f"  {k:34} frame={a['frame']} anims={','.join(sorted(a['anims']))}")
