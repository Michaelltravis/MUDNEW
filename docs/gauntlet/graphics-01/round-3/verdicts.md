# graphics-01 / round 3 / verdicts

Key: `docs/gauntlet/graphics-01/round-3/pairs/key.json` (seed `2026-09-02T23:35:00Z:3`). A piece wins when its overall pick decodes to `mh`.

## hud — WIN (overall pick A -> mh; confidence low)

| label | pick | decoded |
|---|---|---|
| overall | A | mh (city A=mh, combat A=mh, dungeon A=mh) |
| city | B | ref |
| combat | A | mh |
| dungeon | B | ref |

Per-label: 1/3 (combat mh; city, dungeon ref). Overall pick A maps to mh on every label in this round's key, so by the round rule the piece wins. The split between the overall pick and the per-label picks, plus `confidence: low`, is recorded as a blocker in STATUS.md.

### Critic reasons (verbatim)
1. combat: A shows a boss frame (GRAVE KEEPER, Lv 35, 764/768 bar), a red 'Crushing Blow' telegraph with Q BRACE / E SIDESTEP / INTERRUPT prompts, floating damage numbers and a three-line colour-coded feed ('grave keeper hit YOU for 16' in red); B shows only the player swinging at a rat with one health bar and zero fight-state text, so A answers 'what is the fight state and what do I do' immediately and B never does.
2. city and dungeon: B keeps the HUD to one bottom strip with a single large red health bar and a handful of icons, leaving nearly the whole viewport to the world; A stacks a top location banner (Market Square / Plaza of Bones), a clock, WASD/compass glyphs, a PANELS button and a full-width bottom bar of five hotkeys plus three vitals bars and a text line, so A gives up more screen and has no single focal point.
3. legibility: A's bottom text line ('Lv 30 Warrior - 0% xp - 2075 gold') and the hotkey labels are roughly 8px and grey-on-black, unreadable at a glance, and in dungeon the 'grave keeper' name tag is partly hidden behind the player sprite; B's 'Welcome to BrowserQuest!' / '1 player' text is larger and high-contrast against the dark strip.

### Critic fixes (verbatim)
1. Add a target frame during combat: enemy name, level and a health bar anchored near the top of the screen, plus a telegraph/threat line so the player knows what the enemy is winding up. — `src/web_isometric/platformer/ui-arpg.js`
2. Add a short colour-coded combat feed (2-3 lines, outgoing/incoming distinguished) that fades per line instead of piling up, positioned above the vitals bar rather than over the player. — `src/web_isometric/platformer/ui.js`
3. Show numeric HP on the health bar and a player-level/xp readout in the bottom strip at a size of at least 12px so vitals are glanceable without opening a panel. — `src/web_isometric/platformer.html`

Note: fixes 1 and 2 describe features the critic itself credits to A in reason 1 (target frame, telegraph, colour-coded feed), and fix 3 is what the round-3 builder shipped (15px HP numerals, 12.5px level/xp/gold line); the critic's fixes appear to be written against B/ref's shot rather than A's.
