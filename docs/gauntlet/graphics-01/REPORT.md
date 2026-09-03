# graphics-01 — Report for the human brake

**Run:** graphics-01 (restart, seed `2026-09-02T23:35:00Z`). **Reference:** BrowserQuest. **Status:** complete, 3 of 3 rounds. All three pieces won a round.

## Per piece

### atmosphere — WIN, round 1 (1 round fought) — `fead991`
Per-label 5/5 for mh (city, forest, dungeon, cave, water); critic confidence low. Most repeated complaint: the biome tint flattens readability — forest actors are "green-on-green smudges" and water rocks "nearly vanish", so actors, exits and rocks need a separate value/hue from the floor.

### actors — WIN, round 1 (1 round fought) — `d73fac7`
Per-label 3/3 for mh; critic confidence high. Most repeated complaint: hostile vs neutral is not distinguished — city NPCs (stray dog, cityguards) carry the same green bar as enemies.

### hud — WIN, round 3 (3 rounds fought) — `4a29fb8`
- Round 1: LOSS (1/3 — combat won; city, dungeon lost).
- Round 2: LOSS (1/3 — same split). Records committed in `db5f270`; code left uncommitted.
- Round 3: WIN on the overall pick, but per-label still 1/3 (combat mh; city, dungeon ref). Confidence low in every round.

Most repeated complaint (all three rounds): **too much chrome and too-small text outside combat.** The sidebar / top banner / clock / compass / PANELS button / multi-row bottom bar squeeze the world to ~60% of the frame while the reference gives it ~90%, and the secondary text (hotkey labels, "Lv 30 Warrior - 0% xp - 2075 gold") is ~6-8px grey-on-black. Combat, by contrast, wins every round on the boss frame, "Crushing Blow" telegraph, Q/E/F prompts and colour-coded feed.

Caveat: the round-3 win may be a rubric artefact. Per-label it matches the two losses, and the critic's round-3 fixes describe features mh already has. Honest read: combat HUD beats the bar; city/dungeon HUD still does not.

## Commits (git log --oneline -12)
```
4a29fb8 gauntlet(graphics-01): hud won round 3
db5f270 gauntlet(graphics-01): round 2 records
d73fac7 gauntlet(graphics-01): actors won round 1
fead991 gauntlet(graphics-01): atmosphere won round 1
eafdbd8 gauntlet(graphics-01): round 1-2 records for actors and hud
e85ae11 gauntlet(graphics-01): actors won round 2
1fc1d4f gauntlet(graphics-01): atmosphere won round 1
3ba9f63 gauntlet: carry prior verdicts into a new run; resolve dry-01 blocker
5ad9936 gauntlet(dry-01): report
a6013e4 gauntlet(dry-01): round 1 records
6c40a53 Gauntlet loop: evidence pipeline, skill, and graphics workflow
5168a8c Mob variety & tactics: trapsmiths, pack hunting, ambushers, cowards, terrain casters
```
`eafdbd8`, `e85ae11`, `1fc1d4f` are from an earlier graphics-01 pass; only the restart's rounds count.

## Loose ends
- `round-1/builder-hud.md` and `round-1/critic-hud.json` are modified and uncommitted; commit them with this report.
- `logs/tests.log` is dirty; do not commit.

## Your call
1. **Continue** — another run against BrowserQuest, hud-only, scoped to city/dungeon chrome and text size (the one complaint that never cleared). Consider requiring per-label majority, not just the overall pick, to close.
2. **Change the reference** — BrowserQuest's single-bar HUD may be the wrong bar for an ARPG-style client; pick a reference with a comparable chrome budget and re-run hud.
3. **Stop** — accept the three wins as-is, merge `claude/nice-johnson-slpinu`, and revisit hud chrome as ordinary product work.
