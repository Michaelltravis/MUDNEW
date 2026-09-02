# Gauntlet evidence tooling

Screenshots for the Gauntlet Loop (see `.claude/skills/gauntlet-loop/SKILL.md`).

| Script | Does |
|---|---|
| `capture.js` | logs the `Gauntlet` character into the Phaser client, fixes hour/weather, visits `rooms.json`, screenshots each label |
| `capture-ref.js` | `--setup` clones + patches BrowserQuest for node 22; `--serve` starts it (:8000 game, :8001 static); default captures the same labels |
| `montage.js` | blind A/B pairs (`--run`, `--round`, `--seed`) or a `--sheet` contact sheet |
| `rooms.json` | label → Misthollow room vnum (+ commands) and reference camera spot |
| `config.json` | ports, capture character, viewport, setup commands |

## One-time setup
```
pip install aiohttp                     # :4003 command bridge used by the client
./run.sh &                              # MUD :4000, web map :4001, web client :4003
python3 - <<'EOF2'                      # capture character + admin account (goto/settime/setweather/advance)
import sys, json, time; sys.path.insert(0, 'tests'); sys.path.insert(0, 'src')
from test_suite import MUDClient; from accounts import Account
c = MUDClient('localhost', 4000); c.connect(); c.login('Gauntlet', 'gauntlet1'); c.send_and_receive('quit', 1)
a = Account('gauntlet'); a.password_hash = Account.hash_password('gauntlet1'); a.characters = ['Gauntlet']; a.is_admin = True; a.save()
p = json.load(open('lib/players/gauntlet.json')); p['account_name'] = 'gauntlet'; json.dump(p, open('lib/players/gauntlet.json', 'w'), indent=2)
EOF2
NODE_PATH=/opt/node22/lib/node_modules node tools/gauntlet/capture-ref.js --setup
NODE_PATH=/opt/node22/lib/node_modules xvfb-run -a node tools/gauntlet/capture-ref.js
```

## Per round
```
NODE_PATH=/opt/node22/lib/node_modules xvfb-run -a node tools/gauntlet/capture.js --run graphics-01 --round 1
NODE_PATH=/opt/node22/lib/node_modules node tools/gauntlet/montage.js --run graphics-01 --round 1
```
Determinism: `settime 14` + `setweather clear` (immortal commands added for this), seeded
`Math.random` in the page, first-run tips silenced via localStorage, vnum-seeded room layouts.
Remaining nondeterminism: mob wander/spawn state and combat timing (the combat label is a
snapshot ~6.5 s into a fight with the grave keeper in 14002).
