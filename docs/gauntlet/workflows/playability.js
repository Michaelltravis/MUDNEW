export const meta = {
  name: 'gauntlet-playability',
  description: 'Gauntlet Loop, playability and combat feel: feel (blind A/B storyboard vs BrowserQuest) + pacing (transcript vs answer key), max 3 rounds',
  whenToUse: 'Run with the Workflow tool: args {run: "playability-01", timestamp: "<iso>", rounds?: 3, pieces?: ["feel","pacing"], prior?: {feel: "<critic json path>"}}',
  phases: [
    { title: 'Reference gate', detail: 'reference storyboard + servers present' },
    { title: 'Build', detail: 'one fresh builder per open piece' },
    { title: 'Capture', detail: 'fight transcripts + storyboards + blind pairs (serialized: one capture account)' },
    { title: 'Judge', detail: 'blind A/B critic for feel; answer-key critic for pacing' },
    { title: 'Decode', detail: 'lead decodes key.json, records, commits winners' },
    { title: 'Report', detail: 'REPORT.md for the human brake' },
  ],
}

// ---------------------------------------------------------------- pieces
// feel: judged blind A/B on the 8-frame fight storyboard (label "fight") and the mid-fight still ("combat").
// pacing: no runnable reference has comparable text combat, so it is judged against a written answer key
//         (Wayfinder variant): the critic reads our transcript + stats and answers pass/fail per question.
const ALL_PIECES = [
  {
    id: 'feel', kind: 'ab', title: 'Combat feel: moment-to-moment readability, feedback and rhythm on screen',
    goal: 'Across a 12-second storyboard a viewer can tell at every frame who is winning, what the enemy is about to do, what the player just did, and what the player should do next. Hits land with weight (flash, knockback, numbers that read), telegraphs are unmistakable, and the reaction prompts (brace / sidestep / interrupt) read as an invitation, not clutter.',
    files: ['src/web_isometric/platformer/scene-topdown.js', 'src/web_isometric/platformer/fx-abilities.js', 'src/web_isometric/platformer/ui.js', 'src/web_isometric/platformer/ui-arpg.js'],
    labels: ['fight', 'combat'],
    questions: ['In which storyboard can you tell, frame by frame, who is winning without reading prose?', 'Which shows the enemy attack coming before it lands (telegraph) and the result after (hit, miss, stagger)?', 'Which makes hits feel weighty (impact flash, recoil, legible damage numbers) rather than a static sprite?', 'Which tells the player what to do next at the moment it matters, without covering the action?'],
  },
  {
    id: 'pacing', kind: 'key', title: 'Fight pacing and decision density (server): telegraph cadence, reaction windows, fight length, message quality',
    goal: 'A fair fight for a geared level-30 warrior lasts 30-90 seconds and ends in a kill or a clear retreat, never a 10-minute slog; at least one telegraphed wind-up appears in the first 12 seconds and roughly every 3-4 rounds after; staggers are reachable; combat text has no grammar bugs ("Your barely scratch slashes") and does not repeat the same line more than three rounds running.',
    files: ['src/combat.py', 'src/mob_ai.py', 'src/config.py'],
    labels: ['fight_keeper', 'fight_bear'],
    questions: [
      'Q1 Fight length: does each fight end (mob_killed or player_died or a deliberate retreat) within 30-90 s, with rounds >= 6? (A fight that times out at 90 s with the mob above 90% HP FAILS.)',
      'Q2 Telegraph cadence: is telegraph >= 1 within the first 12 s AND telegraphs >= rounds/4 overall?',
      'Q3 Decisions: is rounds_without_decision_pct <= 60, i.e. at least 4 in 10 rounds contain a telegraph or stagger the player can act on?',
      'Q4 Player agency: does player_hit >= player_miss, and does the transcript show at least one player action other than the auto-attack landing (a skill, a brace/sidestep/interrupt line, a perfect strike, or a stagger exploited)?',
      'Q5 Text quality: are there zero grammar bugs of the form "Your <adjective> <verb>s" (e.g. "Your barely scratch slashes"), and no identical non-prompt line repeated in 3+ consecutive rounds?',
      'Q6 Feedback: when player HP crosses 25%, is there exactly one warning (not nagging every round), and does the mob HP bar move visibly (>= 10% total) by the end of a 60 s fight?',
    ],
  },
]

const RUN = (args && args.run) || 'playability-01'
const STAMP = (args && args.timestamp) || 'unstamped'
const ROUNDS = Math.min(3, (args && args.rounds) || 3)
const PIECES = ALL_PIECES.filter(p => !(args && args.pieces) || args.pieces.includes(p.id))
const ENV = 'NODE_PATH=/opt/node22/lib/node_modules'
const REF_DIR = 'docs/gauntlet/reference/browserquest'
const runDir = `docs/gauntlet/${RUN}`
const roundDir = n => `${runDir}/round-${n}`

// ---------------------------------------------------------------- schemas
const GATE = { type: 'object', required: ['ok', 'missing'], properties: { ok: { type: 'boolean' }, missing: { type: 'array', items: { type: 'string' } } } }
const BUILD = { type: 'object', required: ['piece', 'files', 'summary', 'self_check'], properties: {
  piece: { type: 'string' }, files: { type: 'array', items: { type: 'string' } }, summary: { type: 'string' },
  self_check: { type: 'object', required: ['qc_rooms', 'smoke'], properties: { qc_rooms: { type: 'string' }, smoke: { type: 'string' } } } } }
const CAPTURE = { type: 'object', required: ['ok', 'shots', 'pairs', 'fights', 'problems'], properties: { ok: { type: 'boolean' }, shots: { type: 'integer' }, pairs: { type: 'integer' }, fights: { type: 'integer' }, problems: { type: 'array', items: { type: 'string' } } } }
const VERDICT_AB = { type: 'object', required: ['piece', 'pick', 'per_label', 'reasons', 'fixes', 'confidence'], properties: {
  piece: { type: 'string' }, pick: { type: 'string', enum: ['A', 'B'] },
  per_label: { type: 'object', additionalProperties: { type: 'string', enum: ['A', 'B'] } },
  reasons: { type: 'array', minItems: 3, maxItems: 3, items: { type: 'string' } },
  fixes: { type: 'array', minItems: 1, maxItems: 3, items: { type: 'object', required: ['what', 'file_hint'], properties: { what: { type: 'string' }, file_hint: { type: 'string' } } } },
  confidence: { type: 'string', enum: ['low', 'high'] } } }
const VERDICT_KEY = { type: 'object', required: ['piece', 'pass', 'per_question', 'evidence', 'fixes'], properties: {
  piece: { type: 'string' }, pass: { type: 'boolean' },
  per_question: { type: 'object', additionalProperties: { type: 'string', enum: ['pass', 'fail'] } },
  evidence: { type: 'array', minItems: 3, items: { type: 'string' } },
  fixes: { type: 'array', maxItems: 3, items: { type: 'object', required: ['what', 'file_hint'], properties: { what: { type: 'string' }, file_hint: { type: 'string' } } } } } }
const DECODE = { type: 'object', required: ['results'], properties: { results: { type: 'array', items: { type: 'object', required: ['piece', 'won', 'committed'], properties: { piece: { type: 'string' }, won: { type: 'boolean' }, committed: { type: 'string' } } } } } }

// ---------------------------------------------------------------- prompts
const builderPrompt = (p, n, verdict) => `You are a BUILDER in a Gauntlet Loop for Misthollow (Python asyncio MUD in src/, Phaser top-down web client in src/web_isometric/platformer/). Read .claude/skills/gauntlet-loop/SKILL.md section 4 first.
Run: ${RUN}, round ${n}. Piece: ${p.title}.
Goal: ${p.goal}
You may ONLY edit these files: ${p.files.join(', ')}. Do not touch any other file (no zone JSON, no mob stats files). Another builder is editing other files concurrently in this same working tree; never run git checkout/stash/reset.
Evidence from the last round is in ${n > 1 ? roundDir(n - 1) : ((args && args.baseline) || 'docs/gauntlet/smoke/round-2')}/: ${p.kind === 'ab' ? `mh/fight.png (our 8-frame storyboard) and ${REF_DIR}/fight.png (the reference storyboard). Read both PNGs before coding.` : 'fight/fight_keeper.txt, fight/fight_bear.txt (timestamped transcripts of a geared level-30 warrior fighting the grave keeper in room 14002 and Grimclaw the bear in 27021) and the matching .json stats. Read them before coding.'}
${verdict ? `Previous critic verdict for this piece (fix these FIRST):\n${JSON.stringify(verdict, null, 2)}` : (args && args.prior && args.prior[p.id]) ? `No verdict in this run yet, but an earlier run judged this piece: Read ${args.prior[p.id]} first.` : 'First round: no verdict yet.'}
The critic will judge ${p.kind === 'ab' ? `blind A/B against the reference on labels ${p.labels.join(', ')}` : `PASS/FAIL against this answer key, using fresh transcripts produced by tools/gauntlet/fight.py`}: ${p.questions.map((q, i) => `(${i + 1}) ${q}`).join(' ')}
${p.kind === 'key' ? 'You can reproduce the evidence yourself: python3 tools/gauntlet/fight.py --run scratch --round ' + n + ' --max 90  (writes docs/gauntlet/scratch/...; the MUD must be running on :4000 and you must RESTART it (kill python3 src/main.py, then ./run.sh in the background) after changing server code). Balance by changing rules and formulas in your files, not by editing mob data.' : 'The web client is served from files on disk; reload is enough, no server restart needed.'}
Hard rules: keep the game playable; no new external assets; valid syntax (python3 -m py_compile for .py; node -e "new Function(require('fs').readFileSync('<file>','utf8'))" for .js). Before finishing run BOTH checks and paste their last lines verbatim into self_check: (a) node tools/qc_platformer_rooms.js  (b) python3 tests/test_suite.py localhost 4000 --smoke  (known: the smoke login step fails for account characters; report it as-is).
Do not judge your own work; describe what changed and why in at most 8 bullets. Write those bullets to ${roundDir(n)}/builder-${p.id}.md (create dirs). Return {piece:"${p.id}", files, summary, self_check:{qc_rooms, smoke}}.`

const capturePrompt = n => `You run the evidence step of a Gauntlet Loop round. Do exactly this, in order, from /home/user/MUDNEW:
1. Server code may have changed this round: RESTART the MUD. Kill any running "python3 main.py" (python3 -c "import os,signal;[os.kill(int(p),signal.SIGTERM) for p in os.listdir('/proc') if p.isdigit() and open(f'/proc/{p}/cmdline','rb').read().replace(b'\\0',b' ').decode().strip()=='python3 main.py']"), then (./run.sh > log/gauntlet_server.log 2>&1 &) and wait until log/gauntlet_server.log contains "Server listening on 0.0.0.0:4000". If it never does, paste the last 20 log lines into problems and stop with ok=false.
2. python3 tools/gauntlet/fight.py --run ${RUN} --round ${n} --max 90
3. ${ENV} xvfb-run -a node tools/gauntlet/capture.js --run ${RUN} --round ${n} --only fight,combat
4. ${ENV} node tools/gauntlet/montage.js --run ${RUN} --round ${n} --seed "${STAMP}:${n}" --only fight,combat
5. Verify ${roundDir(n)}/fight/ has fight_keeper.txt/.json, fight_bear.txt/.json, summary.json; ${roundDir(n)}/pairs/ has fight.png, combat.png and key.json. Do NOT read key.json. Do not open the images.
Report {ok, shots, pairs, fights, problems[]}. On any non-zero exit put the last 15 lines of output into problems and set ok=false.`

const criticAbPrompt = (p, n) => `You are a HARSH CRITIC in a Gauntlet Loop. Read .claude/skills/gauntlet-loop/SKILL.md section 4 (Critic) and section 5, then judge ONE piece: ${p.title}.
Labels: ${p.labels.join(', ')}. Open ONLY these images with the Read tool: ${p.labels.map(l => `${roundDir(n)}/pairs/${l}.png`).join(', ')}. "fight" is an 8-frame storyboard (1.5 s apart) of one fight from each of two games, side by side as "A" and "B" in random order; "combat" is a single mid-fight frame. You do not know which is ours. FORBIDDEN: key.json, git diff/log, source files, other screenshots.
Questions: ${p.questions.map((q, i) => `(${i + 1}) ${q}`).join(' ')}
For each label pick A or B, then an overall pick. Binary picks only, no scores, never "both". Exactly 3 concrete OBSERVED reasons citing frames/labels. Then 1-3 fixes the LOSING side needs, each with a file_hint from: ${p.files.join(', ')}. confidence "high" only if every label agrees with the overall pick.
Write the verdict JSON to ${roundDir(n)}/critic-${p.id}.json. Return {piece:"${p.id}", pick, per_label, reasons, fixes, confidence}.`

const criticKeyPrompt = (p, n) => `You are a HARSH CRITIC in a Gauntlet Loop judging against a written answer key (no reference game has comparable text combat). Piece: ${p.title}.
Read ONLY: ${roundDir(n)}/fight/fight_keeper.txt, fight_keeper.json, fight_bear.txt, fight_bear.json, summary.json. FORBIDDEN: source files, git diff, builder notes.
Answer each question strictly from the transcripts and stats; a question FAILS if either fight fails it. Quote the exact lines or numbers you relied on.
${p.questions.map(q => `- ${q}`).join('\n')}
pass = true only if EVERY question passes. Give >= 3 evidence strings (quoted lines/numbers with the fight label) and up to 3 fixes for the failing questions, each with a file_hint from: ${p.files.join(', ')}. Never soften a fail because the game is "close".
Write the verdict JSON to ${roundDir(n)}/critic-${p.id}.json. Return {piece:"${p.id}", pass, per_question, evidence, fixes}.`

const decodePrompt = (n, verdicts) => `You are the LEAD's clerk in a Gauntlet Loop (read .claude/skills/gauntlet-loop/SKILL.md sections 2, 5, 6). Run ${RUN}, round ${n}. Working branch: claude/nice-johnson-slpinu (do not switch branches).
Critic verdicts: ${JSON.stringify(verdicts)}
Piece file ownership: ${JSON.stringify(PIECES.map(p => ({ id: p.id, kind: p.kind, files: p.files })))}
Do:
1. For "ab" pieces read ${roundDir(n)}/pairs/key.json and decode: a piece WINS only when its overall pick decodes to "mh" AND more than half of its judged labels decode to "mh". For "key" pieces a piece WINS when pass === true.
2. Write ${roundDir(n)}/verdicts.md: per piece a table (label or question, pick/result, decoded), overall win/loss, the critic's reasons/evidence and fixes verbatim.
3. For each WINNING piece: git add exactly its owned files plus ${roundDir(n)}/builder-<piece>.md, critic-<piece>.json and verdicts.md and the fight/*.txt and fight/*.json files, then commit:
   gauntlet(${RUN}): <piece> won round ${n}

   <one line: what the builder changed>
   <one line: what the critic saw>

   Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
   Claude-Session: https://claude.ai/code/session_01ERYCY5g4tQeMFvL281gKTs
   Losing pieces: leave their code uncommitted (do NOT revert). If no piece won, commit only the round's md/json/txt records as "gauntlet(${RUN}): round ${n} records".
4. Rewrite docs/gauntlet/STATUS.md: run, round ${n} of ${ROUNDS}, per-piece history, open pieces, blockers, and a final line "Next command: ...".
Return {results:[{piece, won, committed:"<sha or none>"}]}.`

const reportPrompt = history => `Write ${runDir}/REPORT.md for the human brake of a Gauntlet Loop. Read docs/gauntlet/STATUS.md and every ${runDir}/round-*/verdicts.md. Per piece: rounds fought, final result, the critic's most repeated complaint, commits (git log --oneline -12). End with three options: continue, change the reference/answer key, or stop. Round history: ${JSON.stringify(history)}. Under 500 words. Return the path.`

// ---------------------------------------------------------------- run
phase('Reference gate')
const gate = await agent(`Check the Gauntlet reference gate. Required files: ${REF_DIR}/fight.png, ${REF_DIR}/combat.png, tools/gauntlet/capture.js, tools/gauntlet/montage.js, tools/gauntlet/fight.py, docs/gauntlet/smoke/round-1/fight/summary.json, docs/gauntlet/smoke/round-2/mh/fight.png. Also check the MUD is reachable: python3 -c "import socket;socket.create_connection(('localhost',4000),3)" (if down, start it with (./run.sh > log/gauntlet_server.log 2>&1 &) and wait for "Server listening on 0.0.0.0:4000" in log/gauntlet_server.log). Return {ok, missing[]}.`, { phase: 'Reference gate', effort: 'low', schema: GATE })
if (!gate || !gate.ok) { log(`reference gate failed: ${gate ? gate.missing.join(', ') : 'no result'}`); return { run: RUN, aborted: 'reference gate', gate } }

let open = PIECES
const lastVerdict = {}
const history = []
for (let n = 1; n <= ROUNDS && open.length; n++) {
  log(`round ${n}/${ROUNDS}: ${open.map(p => p.id).join(', ')}`)
  // Barrier is deliberate: builders share one working tree and the capture step
  // restarts the server and logs in as the single capture character.
  const builds = await parallel(open.map(p => () => agent(builderPrompt(p, n, lastVerdict[p.id]), { label: `build:${p.id}`, phase: 'Build', schema: BUILD })))
  const built = open.filter((p, i) => builds[i])
  if (!built.length) { log('no builder finished; stopping'); break }
  const cap = await agent(capturePrompt(n), { label: `capture:r${n}`, phase: 'Capture', effort: 'low', schema: CAPTURE })
  if (!cap || !cap.ok) { log(`capture failed round ${n}: ${cap ? cap.problems.join(' | ') : 'no result'}`); history.push({ round: n, capture: cap }); break }
  const verdicts = (await parallel(built.map(p => () => agent(p.kind === 'ab' ? criticAbPrompt(p, n) : criticKeyPrompt(p, n), { label: `judge:${p.id}`, phase: 'Judge', schema: p.kind === 'ab' ? VERDICT_AB : VERDICT_KEY })))).filter(Boolean)
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
