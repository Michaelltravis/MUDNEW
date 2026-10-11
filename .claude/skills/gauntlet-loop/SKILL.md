---
name: gauntlet-loop
description: Run a Gauntlet Loop on Misthollow - fresh-context builders make small pieces, a separate harsh critic picks blind A/B against a named, runnable reference, losers loop with concrete verdicts, the human is the brake. Use when asked to "run the gauntlet", "gauntlet <dimension>", or to raise the client/combat/spells/world to a reference bar. Records live in docs/gauntlet/.
---

# Gauntlet Loop (Misthollow)

The pattern (Matt Shumer; packaged as `robonuggets/gauntlet-loop`): split a goal into the
smallest independently judgeable pieces, fan out **builders**, then a **separate critic** with
fresh context compares the *real output* against a concrete reference **blind, labels stripped,
binary pick**. Losers go back with the critic's specific verdict. The exit is winning or the
human calling it. Never let a builder judge its own work. Never use numeric scores (they drift
upward every round).

## 1. Reference gate (run must not start until all three are filled)
| Field | Meaning | Graphics run value |
|---|---|---|
| `name` | a specific thing, not a category | BrowserQuest (mozilla/BrowserQuest), local clone in `.gauntlet-ref/browserquest` |
| `fetch` | command that produces the reference evidence | `node tools/gauntlet/capture-ref.js --setup` once, then `xvfb-run -a node tools/gauntlet/capture-ref.js` |
| `compare` | command that puts ours and theirs side by side, labels stripped | `node tools/gauntlet/montage.js --run <run> --round <n>` |

A vague bar ("modern-looking", "AAA quality") is the number one failure: the critic invents its
own standard and approves everything. If no runnable reference exists for a dimension, first run
a planning Q&A that settles a written spec plus a pass/fail answer key in `PLAN.md`, and judge
against that (the "Wayfinder" variant).

## 2. Budget and stop rule
- Per run: **3 builders, 1 critic, max 3 rounds.** Stop early when every piece wins.
- After round 3 (or on any blocker) write `docs/gauntlet/<run>/REPORT.md` and stop. The human
  decides whether to continue. Do not extend the budget on your own.
- Winning pieces get one commit each on the working branch:
  `gauntlet(<run>): <piece> won round <n>`. Losing pieces stay uncommitted (they are reworked
  next round or reverted at the end). Pieces own disjoint files, so one working tree is enough.

## 3. Evidence commands
```
# Misthollow shots -> docs/gauntlet/<run>/round-<n>/mh/<label>.png  (+ capture.json)
NODE_PATH=/opt/node22/lib/node_modules xvfb-run -a node tools/gauntlet/capture.js --run <run> --round <n> [--only city,combat]
# reference shots (once) -> docs/gauntlet/reference/browserquest/<label>.png
NODE_PATH=/opt/node22/lib/node_modules xvfb-run -a node tools/gauntlet/capture-ref.js
# blind pairs -> docs/gauntlet/<run>/round-<n>/pairs/<label>.png + key.json (lead only)
NODE_PATH=/opt/node22/lib/node_modules node tools/gauntlet/montage.js --run <run> --round <n>
```
Preconditions: MUD running (`./run.sh`; needs `pip install aiohttp` for the :4003 command
bridge), admin capture account `Gauntlet` (created by `tools/gauntlet/README.md` steps),
labels and rooms in `tools/gauntlet/rooms.json`. Capture is deterministic where the game allows:
fixed hour/weather via `settime`/`setweather`, seeded `Math.random`, teaching tips silenced.

## 4. Roles (prompt templates)

### Lead (you, in the main context)
1. Fill the reference gate. 2. Split the goal into at most 3 pieces, each judgeable from the
montage labels (say which labels each piece is judged on). 3. Write
`docs/gauntlet/<run>/PLAN.md`: pieces, owned files (disjoint), answer-key questions per piece
(concrete, observable: "do torches cast falloff?", "is the enemy wind-up readable at a glance?").
4. Run the workflow. 5. Decode verdicts with `key.json`, write `verdicts.md` and `STATUS.md`,
commit winners. You are the only role that reads `key.json`.

### Builder (fresh context, one piece)
```
You are a builder in a Gauntlet Loop for Misthollow (Python MUD + Phaser top-down web client
in src/web_isometric/platformer/). Piece: {piece.title}. Goal: {piece.goal}.
You may ONLY edit these files: {piece.files}. Do not touch anything else.
Reference bar: {reference.name}. Its screenshots are in docs/gauntlet/reference/browserquest/;
ours from the last round are in docs/gauntlet/{run}/round-{n-1}/mh/. Look at both before coding.
Previous critic verdict for this piece (fix these first): {verdict or "none, first round"}.
Answer-key questions the critic will ask: {piece.questions}.
Hard rules: keep the game playable; run `node tools/qc_platformer_rooms.js` and
`python3 tests/test_suite.py localhost 4000 --smoke` before finishing (start ./run.sh if
needed) and report their results verbatim. Do not judge your own work and do not write
"looks great"; describe what changed and why in <= 8 bullets. Write that summary to
docs/gauntlet/{run}/round-{n}/builder-{piece.id}.md. Return {piece, files, summary, self_check}.
```

### Critic (fresh context, one piece, sees only the pairs)
```
You are a harsh critic in a Gauntlet Loop. You judge ONE piece: {piece.title}, on these
labels: {piece.labels}. Open ONLY these images: docs/gauntlet/{run}/round-{n}/pairs/<label>.png.
Each shows two screenshots, "A" and "B", from two different games, in random order. You do not
know which is ours. Do NOT open key.json, git diff, source files, or any other screenshot.
For each label pick A or B: which one better answers these questions: {piece.questions}.
Then give an overall pick. Rules: binary picks only, never scores, never "both are good".
Give exactly 3 concrete OBSERVED reasons ("B's torches have no falloff, A's pool light on the
floor"), and the top 3 fixes the losing side needs, each with a file hint from this list:
{piece.files}. Confidence is "high" only if every label agrees.
Return JSON: {piece, pick, per_label, reasons, fixes, confidence}.
```

## 5. Verdict JSON (critic output, schema-enforced in the workflow)
```json
{ "piece": "atmosphere", "pick": "A", "per_label": { "city": "A", "forest": "B" },
  "reasons": ["...", "...", "..."], "fixes": [{ "what": "...", "file_hint": "painter.js" }],
  "confidence": "high" }
```
Decode: the lead maps `pick` through `pairs/key.json`; the piece **wins** when the pick resolves
to `mh`.

## 6. Round record (`docs/gauntlet/<run>/round-<n>/`)
`mh/` (our shots, gitignored) · `pairs/` + `key.json` (gitignored) · `builder-<piece>.md` ·
`critic-<piece>.json` · `verdicts.md` (decoded, committed). After every round rewrite
`docs/gauntlet/STATUS.md`: run, round, wins/losses per piece, blockers, and a final
**Next command** line so a fresh context can resume. Keep the Workflow run id there for resume.

## 7. Handoff for a fresh context window
Read in order: `docs/gauntlet/STATUS.md` → this skill → the run's `PLAN.md` → the latest
`verdicts.md`. Then run the Next command. Nothing else in the old conversation is required.
