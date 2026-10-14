# Class gear: each class looks like its class

The owner's mage wore a knight's helmet and a sword. It wasn't a model fault:
- the `gearup` kit (also a login gift) gave every class the same warrior kit: a war helm, black plate, a legendary greatsword and a shield (a two-hander with a shield);
- nothing stopped a mage wearing plate or swinging a greatsword;
- above level 60 the world had no cloth armour and no hats at all.

## The rules (`src/class_gear.py`)
D&D style: the heaviest armour a class is trained in, whether it takes a shield, and the kinds of weapon it knows.

| Class | Armour | Shield | Weapons |
|---|---|---|---|
| Mage | cloth | no | staff, wand, dagger, darts |
| Necromancer | cloth | no | staff, wand, dagger, darts, scythe |
| Thief, assassin | leather | no | dagger, one-handed sword, club or mace, whip, claws, bow, crossbow, darts |
| Bard | leather | no | one-handed sword, dagger, staff, whip, crossbow, darts, instrument, mace |
| Ranger | up to mail | yes | any but a wand, an instrument or a scythe |
| Cleric | up to mail | yes | mace, hammer, staff, wand |
| Warrior, paladin | any | yes | any but a wand or an instrument |

- Armour weight and weapon kind come from `gear_look.py`, the same reading that draws the item.
- A head piece weighs what it looks like: a helm is mail, a horned or fur helm leather, a hat, hood, circlet or mask cloth.
- Leather boots, gloves and bracers suit anyone. Only metal ones (gauntlets, sabatons, vambraces) count as armour.
- Every player is held to the rules, immortals too. Creatures are not.

**Where they apply:**
- `wear`, `wield`, `hold`, the off hand and `wear all` refuse with the reason ("a mage is trained in cloth at most"), and nothing moves.
- **Logging in:** an older character puts away what its class can't use, into the pack, and is told why.
- **/play:** the player payload carries `gear_rules` and each item a key (`gk`: `w:sword:2`, `s`, `a:3`). The inventory greys out what the class can't use, offers no slot to drop it in, and the tooltip says "Not for your class".

## gearup
`gearup` (and the login gift) dresses each class in its own kind:
- the best piece in each slot that the class may wear, of the weight it is trained in (a warrior's plate, a mage's robes) and its favourite weapons (`class_gear.PREFERRED`);
- the strongest named set made for the class (`"classes"` in `sets.py`), else one it can wear whole, within one step of its weight, and never another class's set;
- a legendary of its kind: Synapse (a staff) for a mage, Famine's Needle (a scythe) for a necromancer, Skyrend (a bow) for a ranger;
- no shield with a two-handed weapon.

To re-kit a character that already has the old kit, run `gearup <name>` again.

**A whole mage, to see:** the Archmage's Vestments is a full eight-piece set, with bonuses at 2, 4, 6 and 8 pieces (`sets.py` counts any tier now, not only 2 and 4). With the legendary crystal staff Synapse in the hand, a gearup mage wears nothing outside it. Deckard has `"gearup": true` in `world/grants.json`, so their next login gives them the whole kit. Their class decides which kit; a mage gets the Archmage's.

## New gear
| Set | For | Where | Pieces |
|---|---|---|---|
| Archmage's Vestments (60-66), head to toe | mage | the Eclipse Regent, the Black Observatory | starwoven robe, pointed wizard hat, silk gloves, star-silk slippers, starfall mantle, starwoven leggings, silk sleeves, star orb (held) |
| Lich-Lord's Shroud (60-68) | necromancer | the Thalassine Lich (robe, cowl); the Bone-Crowned Sovereign (wraps, shoes) | grave-silk robe, cowl, bone-knuckled wraps, grave-walker shoes |
| Nightblade's Leathers (55-60) | thief, assassin, bard | Shadow Lord Malachar, Shadowspire Citadel | leather jerkin, hood, gloves, breeches |

Also:
- caster leggings: spellwoven trousers (the Ember Sovereign) and grave-silk leggings (the Bone-Crowned Sovereign);
- a legendary longbow for rangers, **Skyrend, the Sundering Longbow** (the Ember Sovereign, 4%);
- the Necromancer's Regalia's "bone plate armor" is now **bone-stitched robes**, so a necromancer can wear its own set.

## The look (`world3d/gearlook.js`, `procgear.js`)
- **Staves are drawn by their head** (`gear_look.STAFF_HEADS` reads it from the item's words):
  - crystal: a wizard's;
  - skull: a necromancer's;
  - gnarled root: a druid's or a hedge wizard's;
  - plain: a pilgrim's.

  With no head named, a mage's staff is crystal, a necromancer's a skull, anyone else's plain.
- **Hats by their shape** (`gear_look.HATS`):
  - the pack's wizard hat;
  - a wide brim with a feather in the class's colour;
  - a soft cap;
  - a bishop's mitre.

  With no shape named, a caster's hat is a wizard's and anyone else's a brimmed one.
- **New sets have their own colours** in the equipment kit's palette (`tools/art3d/ramps.json`, rebuilt with `node build.mjs .cache equip`):
  - deep indigo with starlight for the Archmage;
  - grave-black with a ghostly green for the Lich-Lord;
  - black with blood red for the Nightblade.
- **Gallery:** `/play?demo&gallery=gear&only=endgame` shows each class as gearup dresses it, and `only=classgear` every hat and staff.

## Tests
- `tests/test_class_gear.py`:
  - the rules;
  - the commands refuse;
  - the login check;
  - every starting kit;
  - gearup for every class;
  - the new gear exists and drops;
  - the payload;
  - the gallery's ENDGAME is current.
- `tests/web/gearlook.test.mjs`: the hats and staves are planned, whole and drawn as their class.
- `tests/web/inventory.test.mjs`: barred gear is greyed, has no slot, and says why.
