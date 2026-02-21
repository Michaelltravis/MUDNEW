# MUME → Misthollow Combat Mapping (First-Pass)

## Goal
Adopt MUME's combat clarity and tactical depth **without** flattening Misthollow's class identity.

## 1) OB / DB / PB Core

### MUME principle
- OB = offensive pressure
- DB = dodge/avoidance
- PB = parry/block mitigation
- Players can read these quickly and make tactical decisions.

### Misthollow current
- OB/DB/PB telemetry exists.
- DB/PB now include stance, shield effects, and armor-weight penalties.

### Tuning target
- Keep OB/DB/PB visible in `score` + `tactical`.
- Keep DB/PB component breakdown lines (base + stance + shield/skill - weight).

### Risk notes
- Overly volatile OB/DB/PB values can feel random; keep per-source modifiers small.

---

## 2) Stance (Mood) System

### MUME principle
- Mood trades offense vs defense.

### Misthollow current
- aggressive/normal/defensive exist and affect hit/dam/ac/db/pb.

### Tuning target
- Aggressive: +OB, -PB/-DB
- Defensive: -OB, +PB/+DB
- Keep spread moderate to avoid forcing one best stance.

### Suggested numeric band
- OB swing: ±2 to ±4
- DB swing: ±3 to ±6
- PB swing: ±4% to ±10%

---

## 3) Shield + Armor Weight Interactions

### MUME principle
- Shield magic improves dodge/defense.
- Heavy armor reduces agility-driven defense.

### Misthollow current
- Shield affects DB.
- Armor weight penalizes DB/PB after softcaps.

### Tuning target
- Keep weight penalties as post-softcap curves (not binary).
- Preserve heavy-armor viability via PB but reduce DB.

### Suggested shape
- DB penalty: stronger than PB penalty after softcap.
- PB penalty: gentler curve so tanks still function.

---

## 4) Stat → Skill/Combat Interaction

### MUME principle
- Stats meaningfully gate/boost archetypes.

### Misthollow mapping targets
- STR: weapon pressure + physical damage floor
- DEX: DB, dodge reliability, flee success
- CON: HP/move sustain + regen stability
- INT: caster offense scaling + tactical precision features
- WIS: divine efficacy + support consistency
- WIL: spell resistance + escape composure
- PER: track/acquisition precision + thief utility support

### Risk notes
- Avoid overstacking one stat for every role.

---

## 5) Escape Stack

### MUME principle
- Flee (panic), escape (controlled), disengage (conditional) are distinct.

### Misthollow current
- Distinct commands exist with cooldown/risk messaging.

### Tuning target
- Preserve identity:
  - flee = fastest, least reliable
  - escape = slower, more reliable, skill/stat-influenced
  - disengage = tactical if not hard-locked

---

## 6) Move Economy (Sacred Moves)

### MUME principle
- Moves are strategic; mobility management is core combat skill.

### Misthollow current
- Combat/escape move costs exist.
- Second Wind + Briskness recovery exists.

### Tuning target
- Keep mobility meaningful without making traversal tedious.
- Ensure move-cost applies only to viable actions.

---

## 7) Group Control Triangle

### MUME principle
- assist/rescue/protect creates role skill expression.

### Misthollow current
- protect/rescue/assist implemented with messaging and progression hooks.

### Tuning target
- Keep anti-abuse gates (cooldowns, state checks).
- Make outcomes clear but low-spam.

---

## 8) Immediate Next Tuning Pass (Recommended)
1. Normalize DB/PB contribution ceilings per source.
2. Add explicit WIL impact to escape stability and panic reduction.
3. Slightly increase DEX contribution to flee/escape success (cap-safe).
4. Keep CON influence strongest on sustained movement recovery.
5. Add a concise `help tactical` formula summary for transparency.

---

## Success Criteria
- Players can explain why they lived/died using telemetry alone.
- Stance choice changes outcomes but doesn't hard-force one mode.
- Heavy vs light armor creates real, predictable DB/PB tradeoffs.
- Escape outcomes feel fair and learnable.
