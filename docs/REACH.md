# Reaching into the next room (/play)

The owner: "I want to explore spells and skills reaching to adjacent rooms. I know this is a MUD
limitation, but shouldn't that be possible in the UI?"

A MUD fights room by room. `/play` draws a zone's rooms as one place, so a creature a few metres
past the edge of your room is plainly within bow shot. For players with a position (the 3D client;
telnet players have none and keep the classic rules):

1. **Ranged reach.** A shot, a bolt, or a ranged or aimed spell (combat_range shapes `ranged` and
   `blast`) can strike a creature in a neighbouring room. Distance is measured in metres across
   the edge, from where you stand. The creature is *pulled*: struck, it charges into your room,
   stepping in at the nearest point, and the fight goes on there as any other. The client sends
   `webpull #id <ability>` and then the ordinary command; the server (`reach.py`) checks every
   rule itself.
2. **Area spells spill over.** An aimed circle on the ground that crosses the edge also catches
   the creatures inside it next door, and pulls them in (`Spells.foes_in_room`). So does the
   paladin's Halo of Reckoning, within 5 m.
3. **What reaches shows.** With a creature targeted next door, the target panel says "next room".
   The action-bar slots that can strike it from where you stand stay lit; melee ones dim (your hero
   walks in for those, as before).

The rules: only rooms joined by an open way (side by side on the zone map, no closed door); never
into or out of a peaceful room, across a zone's border, or into a room you may not enter; never a
shopkeeper, trainer or other servant, anyone's pet, or a quest's figure. A creature that keeps its
post (sentinels, bosses) is never pulled: struck from safety it could not answer. A creature's
own spells pull no one.

Checks: `python3 tests/test_polish.py` (the reach section).
