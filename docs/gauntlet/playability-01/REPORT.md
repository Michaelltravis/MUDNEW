# playability-01 — report for the human brake

Run of 3 rounds against reference BrowserQuest (`.gauntlet-ref/browserquest`). Budget exhausted. Working branch `claude/nice-johnson-slpinu`.

## feel (ab; labels fight, combat)

- **Rounds fought:** 3 (rounds 1, 2, 3).
- **Final result:** LOSS, 0/2 labels and overall -> ref in every round, critic confidence high each time. Code left uncommitted in the working tree all three rounds (`scene-topdown.js` +388, `ui.js` +257, `ui-arpg.js` +31; `fx-abilities.js` untouched).
- **Most repeated complaint:** the mh storyboard shows a static knight with no enemy on screen, HP 207/207 across all 8 frames, a "corpse of ..." label, no damage numbers, flash, or recoil — "nothing tells you a fight is even happening." Secondary: static hotbar, no highlighted key or reticle.
- **Why this is not evidence about the code:** all three clerk notes agree `tools/gauntlet/capture.js` filmed an already-dead keeper (no `zreset` before `kill keeper`; screenshots take ~6-7 s). The round-3 builder reproduced it and showed a live fight with `zreset` first. Flagged after rounds 1 and 2, never fixed: the critic has never seen the feel code, which already implements most of the requested fixes.
- **Commits:** none for code. Records: `5614d07` (round 1 status), `724eb2e` (round 2), `7ec3cb4` (round 3).

## pacing (key; six-question pass/fail)

- **Rounds fought:** 1 (closed after winning; not judged in rounds 2-3).
- **Final result:** WIN, 6/6 pass.
- **Most repeated complaint:** none blocking. Minor: boss crits deal the same as non-crits (swing cap); Q6 low-HP rule untested; `fight/*.json` stats counter broken (decision_rounds > rounds).
- **Commits:** `cf2a4c4` (code + records).

## Recent commits (`git log --oneline -12`)

```
7ec3cb4 gauntlet(playability-01): round 3 records
724eb2e gauntlet(playability-01): round 2 records
5614d07 gauntlet(playability-01): status after round 1 (feel records)
cf2a4c4 gauntlet(playability-01): pacing won round 1
2e584aa gauntlet: playability dimension - fight transcripts, storyboards, workflow
34256d8 gauntlet(graphics-02): report; montage uses one A/B order per round at full scale
25597a7 gauntlet(graphics-02): status after round 2
d648ea1 gauntlet(graphics-02): hud won round 2
f8277de gauntlet(graphics-02): status after round 1
abca337 gauntlet(graphics-02): round 1 records
556c074 gauntlet: per-piece label override and majority win rule
1b09dcf gauntlet(graphics-01): report and final records
```

## Options

1. **Continue:** fix `capture.js` first (`zreset` before the kill, frames after the first round payload, cheaper frames, verify a damage number is on film), then `gauntlet playability-01 round 4 (piece: feel, budget extension)`. Judge the existing uncommitted code before rewriting it.
2. **Change the reference/answer key:** keep BrowserQuest but replace the ab storyboard with a key-style checklist for feel (enemy visible, damage number, hit flash, hotbar highlight) verifiable from a single frame.
3. **Stop:** `git checkout -- src/web_isometric/platformer/` to drop the feel code, keep pacing (`cf2a4c4`), close the run with feel recorded as lost on a broken capture.
