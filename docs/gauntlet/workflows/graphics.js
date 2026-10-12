export const meta = {
  name: 'gauntlet-graphics',
  description: 'Gauntlet Loop, graphics dimension: 3 builders, blind critic vs BrowserQuest, max 3 rounds',
  whenToUse: 'Run with the Workflow tool: args {run: "graphics-01", timestamp: "<iso>", rounds?: 3, pieces?: ["atmosphere","actors","hud"], prior?: {atmosphere: "docs/gauntlet/dry-01/round-1/critic-atmosphere.json"}}',
  phases: [
    { title: 'Reference gate', detail: 'reference shots + servers present' },
    { title: 'Build', detail: 'one fresh builder per open piece' },
    { title: 'Capture', detail: 'Misthollow shots + blind pairs (serialized: one capture account)' },
    { title: 'Judge', detail: 'one fresh critic per piece, blind A/B' },
    { title: 'Decode', detail: 'lead decodes key.json, records, commits winners' },
    { title: 'Report', detail: 'REPORT.md for the human brake' },
  ],
}

// ---------------------------------------------------------------- pieces
const ALL_PIECES = [
  {
    id: 'atmosphere', title: 'Atmosphere: biome palette, lighting falloff, fog and particles',
    goal: 'Each biome reads as a distinct, lit place at a glance: warm city, green forest, cold bone-white dungeon, dark cave with warm pools of light, clear shallow water. Light sources cast visible falloff; the room is not a flat tile field.',
    files: ['src/web_isometric/platformer/painter.js', 'src/web_isometric/platformer/themes-zones.js', 'src/web_isometric/platformer/immersion.js'],
    labels: ['city', 'forest', 'dungeon', 'cave', 'water'],
    questions: ['Which screen has a clearer sense of place (you can name the biome without reading text)?', 'Which has light that falls off from sources instead of uniform brightness?', 'Which ground reads as painted terrain rather than a visible tile grid?', 'Which has a palette that stays readable (actors and exits stand out from the floor)?'],
  },
  {
    id: 'actors', title: 'Actor readability: sprites, hit flash, wind-up telegraph, death',
    goal: 'The player, NPCs and enemies are instantly readable as characters with a clear facing and silhouette; enemy wind-ups are visible at a glance; hits flash; enemies are visibly hostile.',
    files: ['src/web_isometric/platformer/scene-topdown.js', 'src/web_isometric/platformer/fx-abilities.js', 'src/web_isometric/platformer/lpc.js', 'src/web_isometric/platformer/dcss.js'],
    labels: ['city', 'combat', 'cave'],
    questions: ['Which screen lets you find the player character within one second?', 'Which shows enemies as clearly hostile and distinct from bystanders?', 'In the combat shot, which makes the attack/wind-up/hit state readable without reading text?', 'Which actors have a clean silhouette at this zoom (no mush, no floating)?'],
  },
  {
    id: 'hud', title: 'HUD and feed: typography, contrast, information hierarchy, combat feed rhythm',
    goal: 'The HUD frames the world instead of crowding it: the play area dominates, vitals are glanceable, text is legible at 1280x720, the combat feed reads as rhythm not spam, panels do not overlap the room.',
    files: ['src/web_isometric/platformer/ui.js', 'src/web_isometric/platformer/ui-arpg.js', 'src/web_isometric/platformer.html'],
    labels: ['city', 'combat', 'dungeon'],
    questions: ['Which screen gives the world more of the screen while keeping vitals glanceable?', 'Which has clearer information hierarchy (one obvious focal point, then secondary info)?', 'Which text stays legible at a glance (size, contrast, no wall of prose over the scene)?', 'In combat, which HUD tells you the fight state (health, threat, what to do) faster?'],
  },
]

const RUN = (args && args.run) || 'graphics-01'
const STAMP = (args && args.timestamp) || 'unstamped'
const ROUNDS = Math.min(3, (args && args.rounds) || 3)
const PIECES = ALL_PIECES.filter(p => !(args && args.pieces) || args.pieces.includes(p.id))
  .map(p => (args && args.labels && args.labels[p.id]) ? { ...p, labels: args.labels[p.id] } : p)
// win rule: 'overall' (critic's overall pick) or 'majority' (overall pick AND more than half the labels)
const WIN_RULE = (args && args.winRule) || 'overall'
const ENV = 'NODE_PATH=/opt/node22/lib/node_modules'
const REF_DIR = 'docs/gauntlet/reference/browserquest'
const runDir = `docs/gauntlet/${RUN}`
const roundDir = n => `${runDir}/round-${n}`

// ---------------------------------------------------------------- schemas
const GATE = { type: 'object', required: ['ok', 'missing'], properties: { ok: { type: 'boolean' }, missing: { type: 'array', items: { type: 'string' } } } }
const BUILD = { type: 'object', required: ['piece', 'files', 'summary', 'self_check'], properties: {
  piece: { type: 'string' }, files: { type: 'array', items: { type: 'string' } }, summary: { type: 'string' },
  self_check: { type: 'object', required: ['qc_rooms', 'smoke'], properties: { qc_rooms: { type: 'string' }, smoke: { type: 'string' } } } } }
const CAPTURE = { type: 'object', required: ['ok', 'shots', 'pairs', 'problems'], properties: { ok: { type: 'boolean' }, shots: { type: 'integer' }, pairs: { type: 'integer' }, problems: { type: 'array', items: { type: 'string' } } } }
const VERDICT = { type: 'object', required: ['piece', 'pick', 'per_label', 'reasons', 'fixes', 'confidence'], properties: {
  piece: { type: 'string' }, pick: { type: 'string', enum: ['A', 'B'] },
  per_label: { type: 'object', additionalProperties: { type: 'string', enum: ['A', 'B'] } },
  reasons: { type: 'array', minItems: 3, maxItems: 3, items: { type: 'string' } },
  fixes: { type: 'array', minItems: 1, maxItems: 3, items: { type: 'object', required: ['what', 'file_hint'], properties: { what: { type: 'string' }, file_hint: { type: 'string' } } } },
  confidence: { type: 'string', enum: ['low', 'high'] } } }
const DECODE = { type: 'object', required: ['results'], properties: { results: { type: 'array', items: { type: 'object', required: ['piece', 'won', 'committed'], properties: { piece: { type: 'string' }, won: { type: 'boolean' }, committed: { type: 'string' } } } } } }

// ---------------------------------------------------------------- prompts
const builderPrompt = (p, n, verdict) => `You are a BUILDER in a Gauntlet Loop for Misthollow (Python MUD + Phaser top-down web client in src/web_isometric/platformer/). Read .claude/skills/gauntlet-loop/SKILL.md section 4 first.
Run: ${RUN}, round ${n}. Piece: ${p.title}.
Goal: ${p.goal}
You may ONLY edit these files: ${p.files.join(', ')}. Do not touch any other file. Other builders are editing other files concurrently in this same working tree; never run git checkout/stash/reset.
Reference bar: BrowserQuest. Its screenshots are in ${REF_DIR}/ (labels: ${p.labels.join(', ')}). Our latest screenshots are in ${n > 1 ? roundDir(n - 1) : 'docs/gauntlet/smoke/round-0'}/mh/. LOOK at both (Read the PNGs) before coding and decide what specifically makes theirs read better; fix that, in our painterly style, not by copying pixel art.
${verdict ? `Previous critic verdict for this piece (fix these FIRST):\n${JSON.stringify(verdict, null, 2)}` : (args && args.prior && args.prior[p.id]) ? `No verdict in this run yet, but an earlier run judged this piece: Read ${args.prior[p.id]} and its sibling verdicts.md first and fix those points FIRST. The working tree may already contain that run's uncommitted edits to your files; build on them.` : 'First round: no verdict yet.'}
The critic will judge only these labels ${p.labels.join(', ')} on these questions: ${p.questions.map((q, i) => `(${i + 1}) ${q}`).join(' ')}
Hard rules: keep the game playable at every commit; no new external assets or CDN loads; keep the file syntax valid (run: node -e "new Function(require('fs').readFileSync('<file>','utf8'))" for each JS file you touched; for platformer.html only edit CSS/markup). Before finishing run BOTH checks and paste their last lines verbatim into self_check: (a) node tools/qc_platformer_rooms.js  (b) python3 tests/test_suite.py localhost 4000 --smoke  (the MUD is running on :4000; if it is not, start it with ./run.sh in the background and wait for "Server listening").
Do not judge your own work; describe what changed and why in at most 8 bullets. Write those bullets to ${roundDir(n)}/builder-${p.id}.md (create dirs). Return {piece:"${p.id}", files, summary, self_check:{qc_rooms, smoke}}.`

const capturePrompt = n => `You run the evidence step of a Gauntlet Loop round. Do exactly this, in order, from the repo root /home/user/MUDNEW:
1. The web client is served from files on disk, so a restart is NOT needed for client-only changes; but verify the MUD is up: python3 -c "import socket;socket.create_connection(('localhost',4000),3)". If it is down, start it: (./run.sh > log/gauntlet_server.log 2>&1 &) and wait until log/gauntlet_server.log contains "Server listening on 0.0.0.0:4000".
2. ${ENV} xvfb-run -a node tools/gauntlet/capture.js --run ${RUN} --round ${n}
3. ${ENV} node tools/gauntlet/montage.js --run ${RUN} --round ${n} --seed "${STAMP}:${n}"
4. Verify ${roundDir(n)}/pairs/ has one PNG per label (city, forest, dungeon, cave, water, combat) and key.json. Do NOT read key.json contents. Do not open the images.
Report {ok, shots, pairs, problems[]}. If capture.js exits non-zero, put its last 15 lines of output into problems and set ok=false.`

const criticPrompt = (p, n) => `You are a HARSH CRITIC in a Gauntlet Loop. Read .claude/skills/gauntlet-loop/SKILL.md section 4 (Critic) and section 5, then judge ONE piece: ${p.title}.
Labels to judge: ${p.labels.join(', ')}. Open ONLY these images with the Read tool: ${p.labels.map(l => `${roundDir(n)}/pairs/${l}.png`).join(', ')}. Each image shows two screenshots, "A" and "B", from two different games in random order; you do not know which is ours. FORBIDDEN: opening key.json, git diff/log, source files, any other screenshot, or asking which is which.
Questions: ${p.questions.map((q, i) => `(${i + 1}) ${q}`).join(' ')}
For each label pick A or B (the one that better answers the questions overall), then an overall pick. Binary picks only, no scores, never "both". Exactly 3 concrete OBSERVED reasons that cite what you saw in specific labels. Then the top 1-3 fixes the LOSING side needs, each with a file_hint chosen from: ${p.files.join(', ')}. confidence is "high" only when every label agrees with the overall pick.
Also write your verdict as JSON to ${roundDir(n)}/critic-${p.id}.json. Return {piece:"${p.id}", pick, per_label, reasons, fixes, confidence}.`

const decodePrompt = (n, verdicts) => `You are the LEAD's clerk in a Gauntlet Loop (read .claude/skills/gauntlet-loop/SKILL.md sections 2, 5, 6). Run ${RUN}, round ${n}. Working branch: claude/nice-johnson-slpinu (do not switch branches).
Critic verdicts (JSON, one per piece): ${JSON.stringify(verdicts)}
Piece file ownership: ${JSON.stringify(PIECES.map(p => ({ id: p.id, files: p.files })))}
Do:
1. Read ${roundDir(n)}/pairs/key.json. Decode the overall pick and every per-label pick through the key. Win rule "${WIN_RULE}": ${WIN_RULE === 'majority' ? 'a piece WINS only when its overall pick decodes to "mh" AND more than half of its judged labels decode to "mh"' : 'a piece WINS when its overall pick decodes to "mh"'}. Report the per-label table either way.
2. Write ${roundDir(n)}/verdicts.md: a table per piece (label, pick, decoded winner), overall win/loss, the critic's 3 reasons and fixes verbatim.
3. For each WINNING piece: git add exactly its owned files plus ${roundDir(n)}/builder-<piece>.md, critic-<piece>.json and verdicts.md, then commit with message:
   gauntlet(${RUN}): <piece> won round ${n}

   <one line: what the builder changed>
   <one line: what the critic saw>

   Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
   Claude-Session: https://claude.ai/code/session_01ERYCY5g4tQeMFvL281gKTs
   Losing pieces: leave their files uncommitted (do NOT revert them). If no piece won, commit only the round's md/json records with message "gauntlet(${RUN}): round ${n} records".
4. Rewrite docs/gauntlet/STATUS.md: run, round ${n} of ${ROUNDS}, per-piece win/loss history, open pieces, blockers, and a final line "Next command: ..." (either the Workflow resume for round ${n + 1}, or "human decision: run complete" if all pieces won or this was round ${ROUNDS}).
Return {results:[{piece, won, committed:"<sha or none>"}]}.`

const reportPrompt = history => `Write ${runDir}/REPORT.md for the human brake of a Gauntlet Loop. Read docs/gauntlet/STATUS.md and every ${runDir}/round-*/verdicts.md. Summarize per piece: rounds fought, final result, the critic's most repeated complaint, the commits made (git log --oneline -12). End with three options for the human: continue another run with the same reference, change the reference, or stop. Round history: ${JSON.stringify(history)}. Keep it under 500 words. Return the path.`

// ---------------------------------------------------------------- run
phase('Reference gate')
const gate = await agent(`Check the Gauntlet reference gate. Required files: ${['city', 'forest', 'dungeon', 'cave', 'water', 'combat'].map(l => `${REF_DIR}/${l}.png`).join(', ')} and tools/gauntlet/capture.js, tools/gauntlet/montage.js. Also check the MUD is reachable: python3 -c "import socket;socket.create_connection(('localhost',4000),3)" (if it is down, start it with (./run.sh > log/gauntlet_server.log 2>&1 &) and wait for "Server listening on 0.0.0.0:4000" in log/gauntlet_server.log). Return {ok, missing[]}.`, { phase: 'Reference gate', effort: 'low', schema: GATE })
if (!gate || !gate.ok) { log(`reference gate failed: ${gate ? gate.missing.join(', ') : 'no result'}`); return { run: RUN, aborted: 'reference gate', gate } }

let open = PIECES
const lastVerdict = {}
const history = []
for (let n = 1; n <= ROUNDS && open.length; n++) {
  log(`round ${n}/${ROUNDS}: ${open.map(p => p.id).join(', ')}`)
  // Barrier is deliberate: builders share one working tree and the capture
  // step logs in as the single capture character, so captures cannot overlap.
  const builds = await parallel(open.map(p => () => agent(builderPrompt(p, n, lastVerdict[p.id]), { label: `build:${p.id}`, phase: 'Build', schema: BUILD })))
  const built = open.filter((p, i) => builds[i])
  if (!built.length) { log('no builder finished; stopping'); break }
  const cap = await agent(capturePrompt(n), { label: `capture:r${n}`, phase: 'Capture', effort: 'low', schema: CAPTURE })
  if (!cap || !cap.ok) { log(`capture failed round ${n}: ${cap ? cap.problems.join(' | ') : 'no result'}`); history.push({ round: n, capture: cap }); break }
  const verdicts = (await parallel(built.map(p => () => agent(criticPrompt(p, n), { label: `judge:${p.id}`, phase: 'Judge', schema: VERDICT })))).filter(Boolean)
  const decoded = await agent(decodePrompt(n, verdicts), { label: `decode:r${n}`, phase: 'Decode', effort: 'low', schema: DECODE })
  const results = (decoded && decoded.results) || []
  history.push({ round: n, results })
  for (const v of verdicts) lastVerdict[v.piece] = v
  const winners = new Set(results.filter(r => r.won).map(r => r.piece))
  open = built.filter(p => !winners.has(p.id))
  log(`round ${n}: won ${[...winners].join(', ') || 'none'}; still open ${open.map(p => p.id).join(', ') || 'none'}`)
}

phase('Report')
const report = await agent(reportPrompt(history), { label: 'report', phase: 'Report', effort: 'low' })
return { run: RUN, rounds: history.length, open: open.map(p => p.id), history, report }
