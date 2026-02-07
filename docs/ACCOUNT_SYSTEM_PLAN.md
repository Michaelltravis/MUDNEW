# Account System Plan (Multi-Character)

## Goals
- Allow one player account to manage multiple characters
- Preserve existing single-character files via migration
- Keep login flow simple and MUD-friendly

## Proposed Login Flow
1. Prompt: `Account name:`
2. Prompt: `Password:`
3. If account exists and password matches:
   - Show list of characters (name, class, level, last login)
   - Options: `play <name>` | `create` | `delete` | `rename`
4. If account does not exist:
   - Prompt: `Create new account? (Y/N)`
   - Create account and then go to character list/create flow

## Data Model
**New file:** `lib/accounts/<account>.json`
```json
{
  "account_name": "michael",
  "password_hash": "...",
  "created_at": "...",
  "last_login": "...",
  "characters": ["Achtest", "Deckard"],
  "settings": {
    "email": null,
    "max_chars": 8
  },
  "shared": {
    "bank_gold": 0,
    "storage": []
  }
}
```

**Existing file (unchanged):** `lib/players/<name>.json`
- Add `account_name` field once migrated

## Migration Strategy
- On login with character name (legacy flow):
  - Offer to create an account and link that character
  - Auto-create account named after the character (lowercase)
- Add `account_name` to player file on first successful account login

## Shared vs Per-Character
- Per-character: stats, inventory, quests, explored rooms
- Shared (optional): bank gold, storage (stash), achievements meta

## Admin / Immortal
- Account can be flagged `is_admin: true`
- Character uses account admin status to unlock admin commands

## Edge Cases
- Character rename should update account list + player file
- Character delete should remove player file + unlink from account
- Password reset requires admin or file edit

## Commands Needed
- `account` (shows account info)
- `account chars` (list)
- `account create` (new character)
- `account delete <name>`
- `account rename <old> <new>`

## UI Output (Example)
```
Welcome back, michael.
Characters:
  1) Deckard  - Lvl 12 Paladin (last: 2026-02-03)
  2) Achtest  - Lvl 1  Warrior (last: 2026-02-03)
Type: play <name> | create | delete <name>
```
