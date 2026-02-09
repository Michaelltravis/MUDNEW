# Changelog — 2026-02-09

## Zone Reset Timing Fix + Mob Respawn Improvements

### Critical Bug Fixed
- **Zone reset timing was broken for fresh-built zones.** `world_builder.py` set `lifespan` in minutes (e.g., 30), but `zone_reset_tick()` treated it as 15-minute ticks. Result: zones built fresh reset every **7.5 hours** instead of 30 minutes. Only saved/loaded zones worked correctly because `from_dict()` converted minutes→ticks.

### Fix
- All `world_builder.py` lifespan values now in ticks (e.g., `2` = 30 min, `1` = 15 min, `4` = 60 min)
- `Zone.__init__` default lifespan changed from 30 to 2 (30 minutes)
- `to_dict()` now saves `reset_time` in seconds (new format) for unambiguous save/load
- `from_dict()` still handles old `lifespan` (minutes) format for backward compat

### Mob Respawn Improvements (from Codex)
- Mob count now checks `home_room` so wandering mobs don't cause duplicate spawns at origin
- Added `max_existing` zone-wide cap (matches CircleMUD M command behavior)
- Zones now track `last_reset_at` and `next_reset_at` timestamps
- Added `reset_interval_seconds` field for informational tracking

### Files Changed
- `src/world.py` — Zone init, from_dict, to_dict, reset_zone, mob counting
- `src/world_builder.py` — All lifespan values converted to tick units
