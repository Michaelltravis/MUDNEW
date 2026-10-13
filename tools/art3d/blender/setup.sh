#!/usr/bin/env bash
# Headless Blender for the 3D art pipeline: the bpy module (Blender 4.2 LTS as a Python package) in a
# venv beside the Node build. Run once per machine or cloud session:   tools/art3d/blender/setup.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
VENV="$HERE/../.venv"
if [ -x "$VENV/bin/python" ] && "$VENV/bin/python" -c 'import bpy' 2>/dev/null; then
  echo "bpy ready: $("$VENV/bin/python" -c 'import bpy; print(bpy.app.version_string)')"; exit 0
fi
python3.11 -m venv "$VENV" 2>/dev/null || python3 -m venv "$VENV"
"$VENV/bin/pip" install -q "bpy==4.2.*"
echo "bpy ready: $("$VENV/bin/python" -c 'import bpy; print(bpy.app.version_string)')"
