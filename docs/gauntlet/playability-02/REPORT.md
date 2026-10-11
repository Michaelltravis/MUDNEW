# playability-02 — report for the human brake

**Run:** playability-02 on branch `claude/nice-johnson-slpinu`. **Reference:** BrowserQuest (local clone `.gauntlet-ref/browserquest`). **Rounds fought:** 1 of 2 planned. **Pieces:** feel (pacing closed in playability-01, `cf2a4c4`).

## Per piece

### feel — WIN, round 1 (1 round fought)
- **Result:** overall pick B -> Misthollow; labels 2/2 -> Misthollow (fight B, combat B); critic confidence high. Committed `cf05cb3`.
- **Key seed:** `2026-09-03T20:10:00Z:1` (A = reference, B = Misthollow on both labels).
- **Critic's most repeated complaint:** legibility of the fight without prose. Across both labels the critic hit the same point three times: the losing side's frames are "visually indistinguishable" static sprites with "pinprick-sized" damage numerals, no enemy HP bar, no wind-up, and no in-world prompt for the next action. All three fixes (enemy nameplate + large damage numbers; ~300 ms wind-up and impact flash; in-world LOOT/attack prompt with a moving player HP bar) are addressed to A, which decodes to BrowserQuest — not Misthollow. Nothing carries forward into a round 2.
- **Why it won:** Misthollow's frames read fighting -> SLAIN -> LOOT without text: damage numbers, enemy HP bar, YOU/KEEPER winning bar, swing ring, numbered action bar.
- **Context:** feel lost 3/3 in playability-01 against a dead-keeper capture; capture fixes `3c9d92e`/`bc8d845` gave the critic a live fight and the same code won.

## Commits (`git log --oneline -12`)
```
8372ba7 gauntlet(playability-02): status after round 1
cf05cb3 gauntlet(playability-02): feel won round 1
bc8d845 gauntlet: 1 s storyboard frames; playability baseline points at the fixed capture
3c9d92e gauntlet: zreset before scripted fights so the storyboard films a live mob
0d136cc gauntlet(playability-01): report; ignore builder scratch evidence
7ec3cb4 gauntlet(playability-01): round 3 records
724eb2e gauntlet(playability-01): round 2 records
5614d07 gauntlet(playability-01): status after round 1 (feel records)
cf2a4c4 gauntlet(playability-01): pacing won round 1
2e584aa gauntlet: playability dimension - fight transcripts, storyboards, workflow
34256d8 gauntlet(graphics-02): report; montage uses one A/B order per round at full scale
25597a7 gauntlet(graphics-02): status after round 2
```

## Open notes
- Fight stats consistent (keeper 7/7, bear 11/11 decision rounds); the decision_rounds > rounds bug did not reproduce.
- `python3 tests/test_suite.py --smoke` still fails at login for account characters (known); `node tools/qc_platformer_rooms.js` passes.
- Carried pacing minor: boss crits equal non-crit hits under the 10% swing cap; Q6 low-HP-warning rule untested. `logs/tests.log` modified, not committed.

## Options
1. **Continue** — `gauntlet playability-02 round 2 (piece: feel)`. Only worthwhile with a new label or bar; a rerun on the same labels re-tests the same code.
2. **Change the reference / answer key** — BrowserQuest lost on every label with fixes aimed at it, which suggests it is no longer a bar for feel. Pick a stronger reference (or add labels such as hit-feedback or camera) and run a fresh playability-03.
3. **Stop** — close playability-02 as complete (all pieces won, round 2 unused). Merge `claude/nice-johnson-slpinu`, and park the carried pacing minor and the smoke-test login failure as ordinary issues.

Recommendation: option 3, with option 2 as the next run if feel is to be pushed further.
