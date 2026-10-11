# graphics-02 — report for the human brake

**Reference:** BrowserQuest (`.gauntlet-ref/browserquest`, shots under `docs/gauntlet/reference/browserquest/`).
**Pieces:** hud only (labels: city, dungeon). **Win rule:** majority (overall pick -> mh AND >1/2 labels -> mh).
**Rounds run:** 2 of 3. **Open pieces:** none.

## hud

| Round | Result | Labels | Overall | Confidence | Committed |
|---|---|---|---|---|---|
| 1 | LOSS | 0/2 (city ref, dungeon ref) | A -> ref | high | none (code left in tree) |
| 2 | WIN | 2/2 (city A -> mh, dungeon B -> mh) | B -> mh | low | `d648ea1` |

**Final result:** WIN in round 2 under the majority rule.

**Most repeated complaint (both rounds):** the HUD's secondary tier is too small to read. Round 1: "three ~4px-tall slivers with 7px numerals" and "Lv 30 Warrior 0% xp 2875 gold in near-illegible micro text." Round 2, even while picking us: MP/MV sub-bars, the level/xp/gold line and hotbar skill names "rendered so small they are unreadable at a glance ... ~8px grey text." Both times the builder reported an 11-13px floor, so there is a persistent builder/critic size mismatch — likely the montage downscale in `tools/gauntlet/capture.js`. Nobody has checked capture output at montage scale.

Round 1's other complaints (prose floated over the playfield; six HUD zones) did not recur. Round 2's fixes all target the reference side; none apply to Misthollow.

**Caveat on the win:** the round-2 key differs per label, so the critic's single overall letter `B` decodes to ref on city and mh on dungeon. Decoded as mh because the critic's prose names "city A / dungeon B" (mh on both) and per-label picks are 2/2. A strict reading calls this a loss and requires round 3.

## Commits (`git log --oneline -12`)

```
25597a7 gauntlet(graphics-02): status after round 2
d648ea1 gauntlet(graphics-02): hud won round 2
f8277de gauntlet(graphics-02): status after round 1
abca337 gauntlet(graphics-02): round 1 records
556c074 gauntlet: per-piece label override and majority win rule
1b09dcf gauntlet(graphics-01): report and final records
4a29fb8 gauntlet(graphics-01): hud won round 3
db5f270 gauntlet(graphics-01): round 2 records
d73fac7 gauntlet(graphics-01): actors won round 1
fead991 gauntlet(graphics-01): atmosphere won round 1
eafdbd8 gauntlet(graphics-01): round 1-2 records for actors and hud
e85ae11 gauntlet(graphics-01): actors won round 2
```

Uncommitted: `logs/tests.log`. Pre-existing smoke-test telnet login failure is not a gauntlet regression.

## Options

1. **Continue another run against BrowserQuest.** Recommended only after a manual look at the montage scale in `tools/gauntlet/capture.js` — otherwise the small-text complaint will recur regardless of what the builder does. Could also run round 3 now if you take the strict reading of the overall pick.
2. **Change the reference.** hud has now beaten BrowserQuest twice (graphics-01 r3, graphics-02 r2), both on low confidence. A denser reference (e.g. a game whose HUD has hotbars and sub-bars, not a single HP strip) would test the secondary-tier hierarchy the critic keeps flagging.
3. **Stop.** All pieces in this run have won; `d648ea1` is committed on `claude/nice-johnson-slpinu`. Size-mismatch note stays in STATUS.md.
