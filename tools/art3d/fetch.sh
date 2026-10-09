#!/usr/bin/env bash
# Download the CC0 source packs for the 3D client into a cache dir (default .cache,
# git-ignored). Files that are already there are skipped. Then run build.mjs on it.
# Sources and licences: docs/art/SOURCES.md
set -euo pipefail
CACHE="${1:-$(dirname "$0")/.cache}"
mkdir -p "$CACHE"
CACHE="$(cd "$CACHE" && pwd)"

get() {  # get <url> <dest>
  [ -s "$2" ] && return 0
  mkdir -p "$(dirname "$2")"
  curl -fsSL --retry 3 -m 600 -o "$2" "$1"
}

# KayKit packs (Kay Lousberg, CC0) are mirrored on GitHub; jsDelivr serves the files.
kaykit() {  # kaykit <repo> <local dir> <path>...
  local repo="$1" dir="$2"; shift 2
  for p in "$@"; do get "https://cdn.jsdelivr.net/gh/KayKit-Game-Assets/$repo@main/$p" "$CACHE/$dir/$p"; done
}

A=addons/kaykit_character_pack_adventures
kaykit KayKit-Character-Pack-Adventures-1.0 kaykit-adventurers "$A/LICENSE.txt" \
  $(for n in Knight Barbarian Mage Rogue Rogue_Hooded; do echo "$A/Characters/gltf/$n.glb"; done)

S=addons/kaykit_character_pack_skeletons
kaykit KayKit-Character-Pack-Skeletons-1.0 kaykit-skeletons "$S/LICENSE.txt" \
  $(for n in Skeleton_Warrior Skeleton_Minion Skeleton_Mage Skeleton_Rogue; do echo "$S/Characters/gltf/$n.glb"; done)

D=addons/kaykit_dungeon_remastered/Assets
listing=$(curl -fsSL "https://data.jsdelivr.com/v1/packages/gh/KayKit-Game-Assets/KayKit-Dungeon-Remastered-1.0@main?structure=flat")
kaykit KayKit-Dungeon-Remastered-1.0 kaykit-dungeon "$D/LICENSE.txt" \
  $(printf '%s' "$listing" | python3 -c "import sys,json; [print(f['name'][1:]) for f in json.load(sys.stdin)['files'] if '/Assets/gltf/' in f['name'] and f['name'].endswith('.glb')]")

# Quaternius Stylized Nature MegaKit (standard, CC0) from OpenGameArt
N="$CACHE/quaternius-nature"
get "https://opengameart.org/sites/default/files/stylized_nature_megakitstandard.zip" "$N/nature.zip"
[ -d "$N/glTF" ] || (cd "$N" && unzip -q -o nature.zip 'glTF/*' License_Standard.txt)

# Quaternius animated creatures (CC0) from OpenGameArt: FBX + textures, converted by build.mjs
oga() {  # oga <zip file name on OGA> <local dir>
  local d="$CACHE/$2"
  get "https://opengameart.org/sites/default/files/$1" "$d/pack.zip"
  [ -f "$d/.unzipped" ] || (cd "$d" && unzip -q -o pack.zip && touch .unzipped)
}
oga "cute_animated_monsters_-_aug_2020.zip" quaternius-cute-monsters
oga "Animal%20Pack%20Vol.2%20by%20%40Quaternius.zip" quaternius-animals-2
oga "Animals%20Pack%20by%20Quaternius.zip" quaternius-animals
oga "Farm%20Animals%20by%20%40Quaternius.zip" quaternius-farm

echo "cache ready: $CACHE"
