#!/usr/bin/env bash
# Download the CC0 sound packs and music for the 3D client into a cache dir (default .cache,
# git-ignored). Files already there are skipped. Then run build.py on it.
# Sources and licences: src/web_isometric/world3d/audio/CREDITS.md (from manifest.json).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
CACHE="${1:-$HERE/.cache}"
mkdir -p "$CACHE"
python3 - "$HERE/manifest.json" "$CACHE" <<'PY'
import json, os, subprocess, sys
man = json.load(open(sys.argv[1]))
cache = sys.argv[2]
want = [(p['url'], os.path.join(cache, 'packs', name + '.zip')) for name, p in man['packs'].items()]
want += [(m['url'], os.path.join(cache, 'music', key + os.path.splitext(m['url'])[1].lower())) for key, m in man['music'].items()]
for url, dest in want:
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        continue
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print('get', url)
    subprocess.run(['curl', '-fsSL', '--retry', '3', '-m', '600', '-o', dest, url], check=True)
PY
echo "cached in $CACHE"
