# CHANGELOG — 2026-02-12

## Warrior Doctrine + Evolution System
- Confirmed doctrine/evolution system in `warrior_abilities.py` and wired commands (`doctrine`, `swear`, `evolve`, `strike`, `rally`, `execute`).
- Removed remaining combo-chain remnants from commands and legacy abilities; legacy skills now report they’re replaced by doctrines.
- Fixed `battleshout` referencing undefined `buffed`.
- Added combat integration: momentum damage bonus, rally damage buff, berserker momentum lifesteal, and unstoppable stun immunity.
- Prompt shows momentum + UNSTOPPABLE indicator for warriors.

## Ops
- Restarted server cleanly on ports 4000/4001/4003.
