"""What each class's marquee quest asks (the engine is marquee.py).

A quest is offered by the class's guildmaster from level 45 and teaches the class's marquee
ability (marquee_abilities.py). It is a chain of stages through the endgame zones, ending in a
private trial; alone it takes about two hours, and a group that embarks with the hero makes
its foes harder by how many joined (marquee_scale.py).

Stage kinds:
  talk     speak with `npc` (in `room`; the engine places a copy there if none stands there)
  visit    reach places: `visits` [{room, label, text}] (in order unless `ordered` is False) — a
           trail to follow, a building to case, verses to hear
  kill     slay the quest's own foes: `spawns` [{vnum, room, kind, label}], each placed when the
           party comes near; `adds` (a vnum) joins each one, one more for every two heroes
  collect  slay `mob` (kept at `per_room` in each of `rooms` while the party is there) until
           `need` (+1 per two extra heroes) `item`s were taken, each kill yielding one at `chance`%
  ritual   `verb` in `room` starts it: hold there for `seconds` while `waves` [{at, vnum, count,
           text}] come, and slay them all
  trial    `trial enter` in `room` opens the private trial (world/marquee/trials/<trial>.json)
  return   speak with the giver again: the ability is taught

Mob vnums 9700-9799 are the quests' own creatures (world/zones/zone_097.json; never reset), ten
a class: warrior 9700, mage 9710, cleric 9720, thief 9730, ranger 9740, paladin 9750,
necromancer 9760, bard 9770, assassin 9780 (elite, gatherer, warden, ritual wave, two trial foes,
trial boss, escort, and a figure to speak with where the world has none). `kind` picks how much
health a foe gets (marquee_scale.ROUNDS).
"""

QUESTS = {
    'warrior': {
        'id': 'marquee_warrior',
        'name': 'The Unbroken Banner',
        'ability': 'unbroken_banner',
        'giver': 3023,                      # the fighters' guildmaster
        'giver_room': 3023,
        'giver_name': "the fighters' guildmaster",
        'offer': ("The guildmaster sets the axe down and studies you for a long moment. 'You fight like someone who "
                  "has never watched a standard fall. I have. Fifty of us rode to Castle Apocalypse under the Unbroken "
                  "Banner, and the Banner-Reavers tore it down on the West Wall. One of ours may still be breathing "
                  "there. Find him. Carry the banner home, whole — and I will teach you the last thing I know: how "
                  "to plant a banner that does not fall.'"),
        'teaches': ("Unbroken Banner — plant a war banner: foes beside you reel and every foe turns on you; you and "
                    "your allies strike harder, shake off stuns and fear and mend for five rounds."),
        'stages': [
            {'kind': 'talk', 'title': 'The Fallen Standard', 'npc': 22098, 'room': 22005,
             'text': ("A crusader of the old company lies dying on the West Wall Path of Castle Apocalypse. "
                      "The castle lies past the Tunnel of Sticks — bring a light."),
             'objective': 'Speak with the dying crusader',
             'say': ("The knight's eyes find you through the blood. 'You wear the guild's colours... then listen. "
                     "They tore the banner in three. Three war-chiefs carry the pieces — the Hall of War, the Inner "
                     "Gate, the Courtyard. Take them back.' He grips your arm. 'And the cloth... they burned it. "
                     "Only living ember can weave it whole again. Go.'")},
            {'kind': 'kill', 'title': 'The Banner-Reavers',
             'text': ("Three Banner-Reaver war-chiefs carry the pieces of the banner through Castle Apocalypse's "
                      "dark halls."),
             'spawns': [
                 {'vnum': 9700, 'room': 22030, 'kind': 'elite', 'label': 'Slay the war-chief in the Hall of War'},
                 {'vnum': 9700, 'room': 22024, 'kind': 'elite', 'label': 'Slay the war-chief at the Inner Gate'},
                 {'vnum': 9700, 'room': 22025, 'kind': 'elite', 'label': 'Slay the war-chief in the Castle Courtyard'},
             ],
             'adds': 9707,
             'done': "The last piece of the banner is yours — but its cloth is ash and tatters."},
            {'kind': 'collect', 'title': 'Embers for the Cloth', 'mob': 9701, 'rooms': [6906, 6907, 6910],
             'per_room': 2, 'need': 5, 'chance': 55, 'item': 'ember core',
             'text': ("Ember shades drift through the Ashlands — Steam Vent Valley, the Magma Flows, the Scorched "
                      "Wasteland. The living ember in their chests can re-weave the cloth."),
             'objective': 'Gather ember cores',
             'done': "The ember cores pulse together like one heart. Now they need a forge."},
            {'kind': 'kill', 'title': 'The Cinder Smith',
             'text': ("The Cinder Smith keeps the only forge hot enough, on the Burning Bridge. He will not mend the "
                      "banner willingly."),
             'spawns': [{'vnum': 9702, 'room': 6908, 'kind': 'warden', 'label': 'Defeat the Cinder Smith'}],
             'done': "In the dying forge the banner's cloth glows whole, bright as the day it was sewn."},
            {'kind': 'ritual', 'title': "The Dragon's Gate", 'room': 8002, 'verb': 'plant', 'seconds': 30,
             'waves': [{'at': 0, 'vnum': 9703, 'count': 2, 'text': 'Ashen drakelings drop out of the smoke above the gate!'},
                       {'at': 10, 'vnum': 9703, 'count': 2, 'text': 'More drakelings come shrieking down the pass!'},
                       {'at': 20, 'vnum': 9703, 'count': 3, 'text': 'The mountain roars — a last flight of drakelings dives at the banner!'}],
             'text': ("Raise the banner where the old line once held: the Dragon's Gate, in the Dragon's Domain. "
                      "Plant it, and hold it."),
             'objective': 'Plant the banner at the Dragon\'s Gate and hold it',
             'action': 'Plant the banner',
             'start': ("You drive the banner into the stone of the Dragon's Gate. The cloth catches a wind that is "
                       "not there — and something in the mountain answers. HOLD!"),
             'done': ("The last drakeling falls. The banner stands, and through it you see a wall that is not here: "
                      "the Last Bastion, where it fell the first time.")},
            {'kind': 'trial', 'title': 'The Last Bastion', 'room': 8002, 'trial': 'warrior',
             'text': ("The banner opens the way to the Last Bastion, as it was on the day of the siege. Enter it "
                      "and break the siege the old company could not."),
             'objective': 'Enter the trial and break the siege',
             'action': 'Enter the trial',
             'done': "Gorrund falls, and the siege of the Last Bastion is broken at last."},
            {'kind': 'return', 'title': 'The Last Lesson',
             'text': "Carry the banner home to the fighters' guildmaster.",
             'objective': "Return to the fighters' guildmaster",
             'say': ("The guildmaster takes the banner in both hands and is quiet a long time. Then they plant it in "
                     "the yard, hard, and the pole does not even shiver. 'Again,' they say, handing it back. 'Plant "
                     "it like the ground owes you. Like nothing that stands against you will stand long.'")},
        ],
    },
    'mage': {
        'id': 'marquee_mage',
        'name': 'The Heart of the Void',
        'ability': 'singularity',
        'giver': 3020,                      # the mages' guildmaster
        'giver_room': 3019,
        'giver_name': "the mages' guildmaster",
        'offer': ("The guildmaster does not look up from the orrery on the bench, where a bead of black glass hangs where "
                  "the sun should be. 'You have learned to throw fire. Anyone can throw fire. Long ago a mage of this guild "
                  "learned to fold the world shut — and the fold ate her. Something of her work still burns in the Plane of "
                  "Chaos, and her echo still walks the High Tower. Bring me the Heart of the Void, and I will teach you to "
                  "close your hand on nothing and make the nothing close.'"),
        'teaches': ("Singularity — every foe is dragged to one point and crushed there for two rounds, then it implodes "
                    "and leaves them slowed."),
        'stages': [
            {'kind': 'talk', 'title': 'The Planar Traveller', 'npc': 16098, 'room': 16005,
             'text': ("A traveller lost in the Plane of Chaos saw where the Heart's pieces fell. The Plane opens up from "
                      "the Mountain Pass in the Dragon's Domain."),
             'objective': 'Speak with the planar traveller',
             'say': ("The traveller laughs and weeps at once. 'The black bead! Yes — I saw where it broke. Three rift-wardens "
                     "stand on its pieces: at the Demon Gate, the Reality Anchor, the Time Storm. Kill them and the pieces "
                     "are yours. But the pieces are dead without star-glass — and the last star-glass in your world is in "
                     "the High Tower of Magic.'")},
            {'kind': 'kill', 'title': 'The Rift-Wardens',
             'text': "Three rift-wardens stand on the pieces of the Heart, scattered across the Plane of Chaos.",
             'spawns': [
                 {'vnum': 9710, 'room': 16013, 'kind': 'elite', 'label': 'Slay the rift-warden at the Demon Gate'},
                 {'vnum': 9710, 'room': 16015, 'kind': 'elite', 'label': 'Slay the rift-warden at the Reality Anchor'},
                 {'vnum': 9710, 'room': 16018, 'kind': 'elite', 'label': 'Slay the rift-warden in the Time Storm'},
             ],
             'adds': 9717,
             'done': "Three shards of black glass lie in your palm, cold as the space between stars."},
            {'kind': 'collect', 'title': 'Star-Glass', 'mob': 9711, 'rooms': [2638, 2635, 2669],
             'per_room': 2, 'need': 5, 'chance': 55, 'item': 'star-glass shard',
             'text': ("Arcane wraiths haunt the High Tower of Magic, north of Moria, their bodies veined with star-glass — "
                      "the Library, the Scrying Chamber, the Chamber of the White Light. Bring a light."),
             'objective': 'Gather star-glass',
             'done': "The star-glass hums against the black shards. Something in the Tower has noticed."},
            {'kind': 'kill', 'title': 'The Echo of the Archmage',
             'text': ("The echo of the mage who made the Heart still walks the Tower's dark Inner Chamber, and it wants "
                      "its work back."),
             'spawns': [{'vnum': 9712, 'room': 2664, 'kind': 'warden', 'label': 'Defeat the Echo of the Archmage'}],
             'done': "The Echo unravels into lamplight — and the last of her knowledge pours into the shards."},
            {'kind': 'ritual', 'title': 'The Pentagram Chamber', 'room': 2590, 'verb': 'attune', 'seconds': 30,
             'waves': [{'at': 0, 'vnum': 9713, 'count': 2, 'text': 'The air goes thin — void spawn claw their way in through the pentagram!'},
                       {'at': 10, 'vnum': 9713, 'count': 2, 'text': 'More of them fall IN from nowhere!'},
                       {'at': 20, 'vnum': 9713, 'count': 3, 'text': 'The void pushes back with everything it has!'}],
             'text': ("Bind the shards in the Pentagram Chamber of the High Tower, and hold the circle while the void "
                      "pushes back."),
             'objective': 'Attune the shards in the Pentagram Chamber and hold the circle',
             'action': 'Attune the shards',
             'start': ("You set the shards in the pentagram and speak the words of binding. The air goes thin — and things "
                       "begin to fall IN."),
             'done': ("The pentagram blazes and the shards fuse into a bead of perfect black. Inside it, a dying star is "
                      "waiting.")},
            {'kind': 'trial', 'title': 'The Collapsing Star', 'room': 2590, 'trial': 'mage',
             'text': ("Look into the bead and you are inside it: the last moments of a star, and the thing that is "
                      "eating it."),
             'objective': 'Enter the bead and face the Star-Eater',
             'action': 'Enter the trial',
             'done': "Vaelith comes apart in silence, and the star inside the bead goes still."},
            {'kind': 'return', 'title': 'The Last Lesson',
             'text': "Bring the Heart of the Void home to the mages' guildmaster.",
             'objective': "Return to the mages' guildmaster",
             'say': ("The guildmaster turns the bead over in their fingers for a long time. Then they set it on your palm "
                     "and close your fingers over it. 'Close your hand,' they say. 'No — not like that. Like the world owes "
                     "you the space it takes up.'")},
        ],
    },
    'cleric': {
        'id': 'marquee_cleric',
        'name': 'The Lost Choir',
        'ability': 'seraphs_vigil',
        'giver': 3021,                      # the priests' guildmaster
        'giver_room': 3002,
        'giver_name': "the priests' guildmaster",
        'offer': ("The guildmaster's hands are folded, but their knuckles are white. 'There was a choir once, at Nereus, "
                  "that sang a seraph down to keep a drowning city. The sea took the city anyway, and the seraph fell with "
                  "its singers. One of the choir still lingers in the Sunken Temple. Find her. Learn the hymn, raise the "
                  "seraph that fell — and I will teach you the vigil it kept.'"),
        'teaches': ("Seraph's Vigil — a seraph heals the most wounded beside you each round for six rounds, and while it "
                    "stands each of you survives one killing blow."),
        'stages': [
            {'kind': 'talk', 'title': 'The Drowned Choir', 'npc': 9728, 'room': 24009,
             'text': ("A priestess of the lost choir lingers in the Sunken Reliquary of the Temple of Nereus — down "
                      "through the Flooded Passage off the Sunken Coast."),
             'objective': 'Speak with the drowned priestess',
             'say': ("The priestess's voice is the sound of water in a bell. 'You came to hear the hymn? Then hear it — if "
                     "you can make the zealots stop shouting. Three of them keep the old rites wrong: in the Grand Hall, the "
                     "Hall of the Tides, the merfolk graveyard. While they rave, the seraph cannot hear us.'")},
            {'kind': 'kill', 'title': 'The Drowned Zealots',
             'text': "Three drowned zealots rave the old rites wrong through the Temple of Nereus.",
             'spawns': [
                 {'vnum': 9720, 'room': 24001, 'kind': 'elite', 'label': 'Silence the zealot in the Flooded Grand Hall'},
                 {'vnum': 9720, 'room': 24015, 'kind': 'elite', 'label': 'Silence the zealot in the Hall of the Tides'},
                 {'vnum': 9720, 'room': 24014, 'kind': 'elite', 'label': 'Silence the zealot in the Merfolk Graveyard'},
             ],
             'adds': 9727,
             'done': "The temple falls silent. Far away, something answers the silence with a single broken note."},
            {'kind': 'collect', 'title': 'Feathers of the Fallen', 'mob': 9721, 'rooms': [5301, 5358, 5347],
             'per_room': 2, 'need': 5, 'chance': 55, 'item': 'seraph feather',
             'text': ("When the seraph fell, gilded harpies stole its feathers away to the Great Pyramid in the eastern "
                      "desert — its base, the great dune, the sandstone crypt."),
             'objective': 'Gather the seraph feathers',
             'done': "The feathers burn gold in your hands. They remember being a wing."},
            {'kind': 'kill', 'title': 'The Gilded Hierophant',
             'text': ("The harpies serve the Gilded Hierophant, who keeps the seraph's heart caged in the Pyramid's "
                      "Shining Vault."),
             'spawns': [{'vnum': 9722, 'room': 5352, 'kind': 'warden', 'label': 'Defeat the Gilded Hierophant'}],
             'done': "The cage breaks. Inside, a light no larger than a candle flame is still singing."},
            {'kind': 'ritual', 'title': 'The Apex', 'room': 5306, 'verb': 'consecrate', 'seconds': 30,
             'waves': [{'at': 0, 'vnum': 9723, 'count': 2, 'text': 'Hollow choristers climb over the edge of the apex, singing nothing!'},
                       {'at': 10, 'vnum': 9723, 'count': 2, 'text': 'More of the hollow choir climb toward the light!'},
                       {'at': 20, 'vnum': 9723, 'count': 3, 'text': 'The whole hollow choir comes to drown out the hymn!'}],
             'text': ("Carry the light to the apex of the Great Pyramid, consecrate the stone, and keep singing while the "
                      "hollow choir comes to silence you."),
             'objective': 'Consecrate the apex and hold the hymn',
             'action': 'Consecrate the apex',
             'start': ("You lay the feathers on the apex stone and begin the hymn. The wind stops. Far below, something that "
                       "used to be a choir starts to climb."),
             'done': ("The last hollow voice breaks. The seraph's light lifts from the feathers — and opens a door in the "
                      "sky.")},
            {'kind': 'trial', 'title': 'The Silent Choir', 'room': 5306, 'trial': 'cleric',
             'text': "Through the door is the cathedral where the choir fell, and the one who silenced it.",
             'objective': 'Enter the cathedral and finish the hymn',
             'action': 'Enter the trial',
             'done': "Serathiel falls, and for the first time in a hundred years the choir's hymn is finished."},
            {'kind': 'return', 'title': 'The Last Lesson',
             'text': "Carry the finished hymn home to the priests' guildmaster.",
             'objective': "Return to the priests' guildmaster",
             'say': ("The guildmaster listens to you hum the hymn — badly — and laughs for the first time you have ever "
                     "heard. 'Again,' they say, 'and this time believe someone is listening.' Above you both, very faintly, "
                     "something unfolds its wings.")},
        ],
    },
    'paladin': {
        'id': 'marquee_paladin',
        'name': 'The Dawnless Chapel',
        'ability': 'wings_of_dawn',
        'giver': 3031,                      # the paladins' guildmaster
        'giver_room': 3086,
        'giver_name': "the paladins' guildmaster",
        'offer': ("The guildmaster stands before the order's window, where the dawn is painted in glass that has never been "
                  "lit. 'There is a chapel in the Necropolis where the sun has not risen in three hundred years. The Eclipse "
                  "took it — and the knight who held it for us. His ghost still walks there. Go to him. Bring the dawn back "
                  "into that chapel, and I will teach you to carry it on your back.'"),
        'teaches': ("Wings of Dawn — rise on wings of light and crash down: radiant damage to every foe around you, every "
                    "ally beside you healed and shielded."),
        'stages': [
            {'kind': 'talk', 'title': 'The Knight Who Waits', 'npc': 14098, 'room': 14005,
             'text': ("The ghost of the order's knight waits in the Temple of the Death God, in the Necropolis beneath "
                      "the city — down through the sewers' far threshold."),
             'objective': 'Speak with the restless ghost',
             'say': ("The restless ghost straightens, and for a moment you see the knight he was. 'The order sent someone at "
                     "last. Hear me: three of the Eclipse's knights hold this place — in the Graveyard of Heroes, the Chapel "
                     "of Lost Hope, the Ossuary. Break them. And then find fire that remembers the sun.'")},
            {'kind': 'kill', 'title': 'The Eclipse Knights',
             'text': "Three eclipse knights hold the Necropolis for their dark master.",
             'spawns': [
                 {'vnum': 9750, 'room': 14025, 'kind': 'elite', 'label': 'Break the eclipse knight in the Graveyard of Heroes'},
                 {'vnum': 9750, 'room': 14026, 'kind': 'elite', 'label': 'Break the eclipse knight in the Chapel of Lost Hope'},
                 {'vnum': 9750, 'room': 14012, 'kind': 'elite', 'label': 'Break the eclipse knight in the Ossuary'},
             ],
             'adds': 9757,
             'done': "The last eclipse knight falls, and the dark in the Necropolis thins — a little."},
            {'kind': 'collect', 'title': 'Embers of the First Dawn', 'mob': 9751, 'rooms': [6900, 6903, 6911],
             'per_room': 2, 'need': 5, 'chance': 55, 'item': 'dawn ember',
             'text': ("In the Ashlands, east along the reef from the Sunken Coast, ember wisps still carry sparks of the "
                      "first dawn — on the Scorched Shore, the Obsidian Spire Field, the Sheltered Hollow."),
             'objective': 'Gather the dawn embers',
             'done': "The dawn embers glow in your hands like a promise."},
            {'kind': 'kill', 'title': 'The Ashen Templar',
             'text': ("An Ashen Templar of the Eclipse hunts the wisps to snuff them out, on the Apocalypse Approach. It "
                      "will come for the embers you carry."),
             'spawns': [{'vnum': 9752, 'room': 6909, 'kind': 'warden', 'label': 'Defeat the Ashen Templar'}],
             'done': "The Templar's ashes scatter on the wind, and the embers burn brighter for it."},
            {'kind': 'ritual', 'title': 'The Dawn Vigil', 'room': 8001, 'verb': 'vigil', 'seconds': 30,
             'waves': [{'at': 0, 'vnum': 9753, 'count': 2, 'text': 'Shades of the eclipse slide down the mountainside toward the light!'},
                       {'at': 10, 'vnum': 9753, 'count': 2, 'text': 'More shades pour out of the shadows of the peaks!'},
                       {'at': 20, 'vnum': 9753, 'count': 3, 'text': 'The Eclipse throws every shadow it has at the dawn!'}],
             'text': ("Keep vigil in the Mountain Pass of the Dragon's Domain, where the first light touches the world, and "
                      "hold the embers up to it while the Eclipse sends its shades."),
             'objective': 'Keep the dawn vigil in the Mountain Pass',
             'action': 'Begin the vigil',
             'start': ("You kneel in the pass and raise the embers to the east. The sky greys — and the shadows on the "
                       "mountainside begin to move."),
             'done': ("The sun clears the peaks and floods the embers with light. In their glow you see a chapel that has "
                      "not seen dawn in three hundred years.")},
            {'kind': 'trial', 'title': 'The Dawnless Chapel', 'room': 8001, 'trial': 'paladin',
             'text': ("The embers open a way into the Dawnless Chapel as it was on the day of the Eclipse. Bring the dawn "
                      "into it."),
             'objective': 'Enter the chapel and bring the dawn',
             'action': 'Enter the trial',
             'done': "Morvane falls, and dawn light pours through the chapel windows for the first time in three centuries."},
            {'kind': 'return', 'title': 'The Last Lesson',
             'text': "Bring the last dawn ember home to the paladins' guildmaster.",
             'objective': "Return to the paladins' guildmaster",
             'say': ("The guildmaster takes the last ember and sets it into the painted window. The glass catches fire with "
                     "light. 'There,' they say quietly. 'That is how it is done. Now do it without the window.'")},
        ],
    },
    'necromancer': {
        'id': 'marquee_necromancer',
        'name': 'The First Phylactery',
        'ability': 'lich_ascension',
        'giver': 3033,                      # the necromancers' guildmaster
        'giver_room': 3082,
        'giver_name': "the necromancers' guildmaster",
        'offer': ("The guildmaster smiles without warmth. 'Every one of us dreams of it. Few are fool enough to try. "
                  "Xal'thar was the first — the first to put his soul in a jar and walk on without it. His phylactery is "
                  "still out there, and so, after a fashion, is he. The grave keeper of the Necropolis knows the way. Bring "
                  "me the First Phylactery, and I will teach you to wear death like a crown — for a little while.'"),
        'teaches': ("Lich Ascension — six rounds as a lich: spells cost half, soul bolts split to a second foe, what you "
                    "deal drains back to you, and death is turned away once."),
        'stages': [
            {'kind': 'talk', 'title': 'The Grave Keeper', 'npc': 14099, 'room': 14002,
             'text': ("The grave keeper of the Necropolis knows where the First Lich kept his secrets. The Plaza of Bones "
                      "lies past the sewers' far threshold, beneath the city."),
             'objective': 'Speak with the morose grave keeper',
             'say': ("The grave keeper squints at you. 'Xal'thar's jar? Hah. Three colossi of bone guard what's left of his "
                     "library — the Sanctum of Dark Rites, the Black Library, the Library of the Damned. His notes are in "
                     "their ribs. And the soul he kept in the jar? It leaked. You'll find it screaming in the "
                     "Shadowspire.'")},
            {'kind': 'kill', 'title': 'The Bone Colossi',
             'text': "Three colossi of bone guard the First Lich's notes in the libraries of the Necropolis.",
             'spawns': [
                 {'vnum': 9760, 'room': 14008, 'kind': 'elite', 'label': 'Fell the colossus in the Sanctum of Dark Rites'},
                 {'vnum': 9760, 'room': 14017, 'kind': 'elite', 'label': 'Fell the colossus in the Black Library'},
                 {'vnum': 9760, 'room': 14022, 'kind': 'elite', 'label': 'Fell the colossus in the Library of the Damned'},
             ],
             'adds': 9767,
             'done': ("Three pages of bone-script, pulled from three cracked ribcages. The writing moves when you are not "
                      "looking at it.")},
            {'kind': 'collect', 'title': 'The Leaking Soul', 'mob': 9761, 'rooms': [24524, 24512, 24516],
             'per_room': 2, 'need': 5, 'chance': 55, 'item': 'soul shard',
             'text': ("Xal'thar's soul leaked from its jar into the Shadowspire Citadel, north of the eastern road, where "
                      "wailing shades carry its shards — the Soul Prison, the Shadow Library, the Tower of Whispers."),
             'objective': 'Gather the soul shards',
             'done': "The soul shards whisper to each other in a dead man's voice. They want to go home."},
            {'kind': 'kill', 'title': 'The Soulbinder',
             'text': ("The Soulbinder of the Shadowspire has been gathering the shards for itself in its Ritual Chamber. "
                      "It will not give them up."),
             'spawns': [{'vnum': 9762, 'room': 24526, 'kind': 'warden', 'label': 'Defeat the Soulbinder'}],
             'done': "The Soulbinder's chains fall slack. Every shard it held is yours."},
            {'kind': 'ritual', 'title': 'The Phylactery Chamber', 'room': 14024, 'verb': 'bind', 'seconds': 30,
             'waves': [{'at': 0, 'vnum': 9763, 'count': 2, 'text': 'The jealous dead claw their way out of the walls toward the jar!'},
                       {'at': 10, 'vnum': 9763, 'count': 2, 'text': 'More of the dead come, drawn by the screaming soul!'},
                       {'at': 20, 'vnum': 9763, 'count': 3, 'text': 'Every corpse in the Necropolis wants that soul!'}],
             'text': ("Return to the Phylactery Chamber of the Necropolis and bind the shards back into the jar — while the "
                      "jealous dead try to take the soul for themselves."),
             'objective': 'Bind the soul in the Phylactery Chamber and hold it',
             'action': 'Bind the soul',
             'start': ("You set the empty jar on the altar and begin to bind. The shards scream — and every corpse in the "
                       "Necropolis hears them."),
             'done': "The jar fills with cold green fire. Inside it, something opens its eyes and looks at you."},
            {'kind': 'trial', 'title': 'The Phylactery Vault', 'room': 14024, 'trial': 'necromancer',
             'text': "The jar knows the way to its master's vault. Go in, and take what he never meant to give.",
             'objective': 'Enter the vault and take the First Phylactery',
             'action': 'Enter the trial',
             'done': "Xal'thar crumbles, and the First Phylactery goes quiet in your hands."},
            {'kind': 'return', 'title': 'The Last Lesson',
             'text': "Bring the First Phylactery home to the necromancers' guildmaster.",
             'objective': "Return to the necromancers' guildmaster",
             'say': ("The guildmaster holds the jar up to the light and watches the green fire move. 'You could have kept "
                     "it,' they say. 'Most would. That is why I teach you, and not them.' They press a cold hand to your "
                     "chest. 'Now. Feel where the jar would go.'")},
        ],
    },
    'thief': {
        'id': 'marquee_thief',
        'name': 'The Last Score',
        'ability': 'heist',
        'giver': 3022,                      # the thieves' guildmaster (the assassins' too: the class decides)
        'giver_room': 3029,
        'giver_name': "the thieves' guildmaster",
        'offer': ("The guildmaster counts coins without looking at them. 'Every thief has a last score. Mine was the Vault "
                  "of Ages — and I never got past the door. There's a fence in Thalos who knows the way in. Case the place, "
                  "get the keys, crack the vault the old priests of Nereus built to hide its door. Bring me back so much as "
                  "a coin from the Vault of Ages, and I'll teach you the trick I was saving for it.'"),
        'teaches': ("The Heist of Ages — gone in smoke and behind every foe at once: each is struck and relieved of half "
                    "its gold, and your next three swings land as criticals."),
        'stages': [
            {'kind': 'talk', 'title': 'The Fence', 'npc': 5298, 'room': 5201,
             'text': ("A street vendor in Thalos fences for the guild and knows the way into the Vault of Ages. Thalos "
                      "lies west across the Great Eastern Desert."),
             'objective': 'Speak with the street vendor',
             'say': ("The vendor's grin doesn't reach his eyes. 'The Vault? Plenty have tried. Case the city first — the "
                     "City Hall, the Guild House, the old north-west watchtower. That's where the Auditor's people meet. "
                     "Then you'll want keys, and the only keys that fit are buried in the Great Pyramid.'")},
            {'kind': 'visit', 'title': 'Casing the Job', 'ordered': True,
             'text': "Case Thalos for the Auditor's people: the City Hall, the Guild House, the north-west watchtower.",
             'visits': [
                 {'room': 5232, 'label': 'Case the City Hall',
                  'text': ("Behind the City Hall's counting room you find a ledger page with the Vault's seal — and a list "
                           "of names. One of them is the Keeper of Keys.")},
                 {'room': 5219, 'label': 'Case the Guild House',
                  'text': ("In the Guild House two of the Auditor's men argue over a map of the Pyramid's lower tombs. You "
                           "memorise it.")},
                 {'room': 5246, 'label': 'Case the north-west watchtower',
                  'text': ("From the top of the watchtower you see it: a glint of gold far out over the sea, where the "
                           "Temple of Nereus sank. The Vault's door is under the water.")},
             ],
             'done': "You know the shape of the job now. All you need are the keys."},
            {'kind': 'collect', 'title': 'The Tomb Keys', 'mob': 9731, 'rooms': [5330, 5345, 5323],
             'per_room': 2, 'need': 5, 'chance': 55, 'item': 'bronze key',
             'text': ("The tomb wardens of the Great Pyramid carry the bronze keys the Vault was locked with — in the "
                      "Ancient Hall, the Tomb of the Pharoahs and the Vault of the Lamp. Bring a light."),
             'objective': 'Take the bronze keys',
             'done': "Five bronze keys, each stamped with the Auditor's seal. One lock left: the Keeper's."},
            {'kind': 'kill', 'title': 'The Keeper of Keys',
             'text': ("The Keeper of Keys holds the master key in the Tomb of Ramses, and it has never once been robbed. "
                      "Bring a light."),
             'spawns': [{'vnum': 9732, 'room': 5332, 'kind': 'warden', 'label': 'Rob the Keeper of Keys'}],
             'done': "The Keeper falls in a jangle of bronze. The master key is warm in your hand."},
            {'kind': 'ritual', 'title': 'Cracking the Vault', 'room': 24020, 'verb': 'crack', 'seconds': 30,
             'waves': [{'at': 0, 'vnum': 9733, 'count': 2, 'text': 'Vault sentinels clank out of the walls!'},
                       {'at': 10, 'vnum': 9733, 'count': 2, 'text': 'More sentinels wake as the tumblers turn!'},
                       {'at': 20, 'vnum': 9733, 'count': 3, 'text': 'Every guardian of Nereus comes for the thief at its door!'}],
             'text': ("Crack the treasure vault of the Sunken Temple, where the door to the Vault of Ages is hidden — and "
                      "keep your nerve while its sentinels come for you."),
             'objective': 'Crack the vault and keep your nerve',
             'action': 'Crack the vault',
             'start': ("You set the master key in a lock older than the city and begin, very carefully, to turn it. "
                       "Somewhere in the walls, something old wakes up."),
             'done': "The last tumbler falls. The vault swings open — on a stair going down into lamplight."},
            {'kind': 'trial', 'title': 'The Vault of Ages', 'room': 24020, 'trial': 'thief',
             'text': "The stair leads down into the Vault of Ages itself — and the Auditor who keeps it.",
             'objective': 'Enter the Vault of Ages and settle with the Auditor',
             'action': 'Enter the trial',
             'done': "Mordessa's ledger falls shut for good. The Vault of Ages is yours — for as long as you can carry it."},
            {'kind': 'return', 'title': 'The Last Lesson',
             'text': "Bring a coin from the Vault of Ages home to the thieves' guildmaster.",
             'objective': "Return to the thieves' guildmaster",
             'say': ("The guildmaster turns the gold coin over and over, and then bites it. 'Real,' they say, and laugh "
                     "until they have to sit down. 'All right. Here is the trick. You don't take the money from them — you "
                     "take them from the money.'")},
        ],
    },
    'ranger': {
        'id': 'marquee_ranger',
        'name': 'The Last Wyvern',
        'ability': 'heartseeker',
        'giver': 3030,                      # the rangers' guildmaster
        'giver_room': 3041,
        'giver_name': "the rangers' guildmaster",
        'offer': ("The guildmaster unrolls a hide marked with a hundred tally-scratches and a single drawing: a black wyvern "
                  "with a torn wing. 'Gloomfang. The last of them. Every ranger who ever wore this badge has tracked her, "
                  "and every one came back without her. The old trapper in the Northern Forest has seen her sign again. "
                  "Find the trail. Make the arrow. Bring her down — and I'll show you how to put an arrow through a heart "
                  "that has stopped a hundred others.'"),
        'teaches': ("Heartseeker — a breath to draw, then one arrow through every foe on its line: a deep wound, marked to "
                    "take more, and held where they stand."),
        'stages': [
            {'kind': 'talk', 'title': 'The Old Trapper', 'npc': 18098, 'room': 18003,
             'text': "The grizzled trapper of the Great Northern Forest has seen Gloomfang's sign again.",
             'objective': 'Speak with the grizzled trapper',
             'say': ("The trapper spits into the snow. 'She's back. Tracks by the moonlit clearing, the standing stones, the "
                     "wolf den, out past the forest's end. Follow them — and watch the alphas. They've been feeding on what "
                     "she leaves.'")},
            {'kind': 'visit', 'title': 'The Trail', 'ordered': True,
             'text': "Follow Gloomfang's trail through the Great Northern Forest.",
             'visits': [
                 {'room': 18016, 'label': 'Find the tracks in the moonlit clearing',
                  'text': ("In the moonlit clearing: a print in the frost as long as your arm, three-toed, the snow around "
                           "it burned black by venom.")},
                 {'room': 18009, 'label': 'Read the sign at the standing stones',
                  'text': "At the standing stones a scale as big as a shield lies in the grass, still warm. She was here today."},
                 {'room': 18024, 'label': 'Follow the trail past the wolf den',
                  'text': "The wolf den is empty but for bones — wyvern-chewed bones. The trail turns north."},
                 {'room': 18025, 'label': "Track her to the forest's end",
                  'text': ("At the forest's end the trail goes up into the sky. She flies for the coast — and the alphas "
                           "follow her leavings.")},
             ],
             'done': "You have her trail. The alphas that feed on it stand in your way."},
            {'kind': 'kill', 'title': 'The Dire Alphas',
             'text': "Three dire alphas have grown fat on Gloomfang's leavings and will not give up the hunt.",
             'spawns': [
                 {'vnum': 9740, 'room': 18017, 'kind': 'elite', 'label': 'Bring down the alpha in Bear Territory'},
                 {'vnum': 9740, 'room': 18022, 'kind': 'elite', 'label': 'Bring down the alpha at the Bandit Camp'},
                 {'vnum': 9740, 'room': 18012, 'kind': 'elite', 'label': "Bring down the alpha at the Bandit's Ambush Point"},
             ],
             'adds': 9747,
             'done': "The alphas are down. The forest is quieter — and the trail leads to the sea cliffs."},
            {'kind': 'collect', 'title': 'Storm-Feathers', 'mob': 9741, 'rooms': [6800, 6803, 6804],
             'per_room': 2, 'need': 5, 'chance': 55, 'item': 'storm feather',
             'text': ("An arrow for a wyvern needs fletching that has flown through storms: the cliff rocs of the Sunken "
                      "Coast carry it — on the Coastal Bluffs, the Coastal Path and Driftwood Beach."),
             'objective': 'Take the storm feathers',
             'done': "The storm feathers crackle when you bind them to the shaft. Now for a head that will bite."},
            {'kind': 'kill', 'title': 'The Roc Matriarch',
             'text': ("The Roc Matriarch on the Rocky Shoreline has torn the head off every arrow ever loosed at her. Her "
                      "talon is the only point that will take Gloomfang's heart."),
             'spawns': [{'vnum': 9742, 'room': 6801, 'kind': 'warden', 'label': 'Bring down the Roc Matriarch'}],
             'done': "The Matriarch falls into the surf. Her talon makes a head for the arrow: the Heartseeker is finished."},
            {'kind': 'ritual', 'title': 'The Blind', 'room': 8000, 'verb': 'stalk', 'seconds': 30,
             'waves': [{'at': 0, 'vnum': 9743, 'count': 2, 'text': 'Wyvern broodlings drop out of the sky, hunting!'},
                       {'at': 10, 'vnum': 9743, 'count': 2, 'text': 'More broodlings have caught your scent!'},
                       {'at': 20, 'vnum': 9743, 'count': 3, 'text': "The whole brood comes screaming down on the blind!"}],
             'text': ("Wait in a blind at the Edge of Chaos in the Dragon's Domain, where Gloomfang's brood hunts, until she "
                      "shows herself — and hold your nerve while her broodlings find you."),
             'objective': 'Wait in the blind at the Edge of Chaos',
             'action': 'Wait in the blind',
             'start': ("You settle into the rocks, arrow on the string, and go still. The wind shifts. Something with "
                       "wings is coming."),
             'done': ("The last broodling falls, and far off a great shape lifts from the peaks and turns toward the old "
                      "hunting grounds. You follow.")},
            {'kind': 'trial', 'title': 'The Hunting Grounds', 'room': 8000, 'trial': 'ranger',
             'text': "Follow Gloomfang into the old hunting grounds, where the first rangers hunted her kind, and end the hunt.",
             'objective': 'Enter the hunting grounds and bring down the last wyvern',
             'action': 'Enter the trial',
             'done': "Gloomfang crashes down with the Heartseeker through her heart. The last wyvern is gone."},
            {'kind': 'return', 'title': 'The Last Lesson',
             'text': "Bring the Heartseeker home to the rangers' guildmaster.",
             'objective': "Return to the rangers' guildmaster",
             'say': ("The guildmaster takes the black arrow and lays it on the hide beside the drawing of the wyvern. For a "
                     "long moment they say nothing at all. Then: 'Now you'll learn to loose it so it never stops.'")},
        ],
    },
    'bard': {
        'id': 'marquee_bard',
        'name': 'The Unsung Verse',
        'ability': 'song_of_the_ages',
        'giver': 3032,                      # the bards' guildmaster
        'giver_room': 3007,
        'giver_name': "the bards' guildmaster",
        'offer': ("The guildmaster sets down a lute with a string missing. 'There was a song once that kept a kingdom "
                  "alive — the Song of the Ages. Nobody sings it any more, and the kingdom is gone, and its king sits in the "
                  "silence it left. Four verses survive, scattered across the world; the elven bard of Silversong knows "
                  "where. Find them, find something that can hold them, and sing it where the world can hear. Then I'll "
                  "teach you to sing it so the world listens.'"),
        'teaches': ("Song of the Ages — five rounds in which your allies' abilities come back twice as fast and they deal "
                    "and heal a fifth more, while your foes slow; the last note stuns them."),
        'stages': [
            {'kind': 'talk', 'title': 'The Elven Bard', 'npc': 11098, 'room': 11005,
             'text': ("The elven bard of Silversong remembers where the four lost verses went. Silversong lies north of the "
                      "Edge of the Forest."),
             'objective': 'Speak with the elven bard',
             'say': ("The elven bard's fingers stop on the harp. 'The Song of the Ages? Four verses survive, and none of them "
                     "where it should be — one in a tavern in Thalos, one in a cliff tavern by the sea, one with the refugees "
                     "in the Plane of Chaos, and the last here, in our Ancient Grove. Go and hear them. Then find something "
                     "that can remember all four at once.'")},
            {'kind': 'visit', 'title': 'The Four Lost Verses', 'ordered': False,
             'text': "Hear the four lost verses of the Song of the Ages, wherever they ended up.",
             'visits': [
                 {'room': 5230, 'label': 'Hear the verse in the Tavern of the Sun (Thalos)',
                  'text': "In the Tavern of the Sun an old drunk sings you the first verse, and weeps, and does not know why."},
                 {'room': 6811, 'label': 'Hear the verse in the Cliff Tavern (Sunken Coast)',
                  'text': "In the Cliff Tavern the second verse is carved into a beam, in a hand older than the building."},
                 {'room': 16021, 'label': 'Hear the verse in the Refugee Sanctuary (Plane of Chaos)',
                  'text': ("In the Refugee Sanctuary a child hums the third verse while the planes shift outside. Her mother "
                           "says she was born knowing it.")},
                 {'room': 11004, 'label': 'Hear the verse in the Ancient Grove (Silversong)',
                  'text': "In the Ancient Grove the last verse is in the wind through the leaves. You have to stand very still to hear it."},
             ],
             'done': "You have all four verses — but they will not stay in your head together. You need something to hold them."},
            {'kind': 'collect', 'title': 'Resonant Gears', 'mob': 9771, 'rooms': [24806, 24814, 24816],
             'per_room': 2, 'need': 5, 'chance': 55, 'item': 'resonant gear',
             'text': ("The chime automatons of the Clockwork Foundry, north of the Ashlands, were built around gears that "
                      "remember music — in Lever Room Alpha, the Power Core Observation room and the Pneumatic Shortcut."),
             'objective': 'Take the resonant gears',
             'done': "The gears tick together in your pack, humming all four verses at once. They want a bell."},
            {'kind': 'kill', 'title': 'The Carillon Engine',
             'text': ("The Carillon Engine in the Foundry's Prototype Laboratory holds the one bell that can ring all four "
                      "verses as one."),
             'spawns': [{'vnum': 9772, 'room': 24825, 'kind': 'warden', 'label': 'Silence the Carillon Engine'}],
             'done': "The Engine falls silent. Its great bell, cut free, rings all four verses at once."},
            {'kind': 'ritual', 'title': 'The Elemental Nexus', 'room': 16010, 'verb': 'play', 'seconds': 30,
             'waves': [{'at': 0, 'vnum': 9773, 'count': 2, 'text': 'Knots of discord tear out of the clashing elements!'},
                       {'at': 10, 'vnum': 9773, 'count': 2, 'text': 'More discord comes, howling the wrong notes!'},
                       {'at': 20, 'vnum': 9773, 'count': 3, 'text': 'All the chaos of the planes tries to drown the Song out!'}],
             'text': ("Play the Song of the Ages at the Elemental Nexus in the Plane of Chaos, where the four elements meet, "
                      "and keep playing while the discord of chaos tries to drown you out."),
             'objective': 'Play the Song at the Elemental Nexus',
             'action': 'Play the Song',
             'start': ("You strike the bell and begin the Song of the Ages. The four elements fall still to listen — and "
                       "everything in the chaos that hates music turns toward you."),
             'done': "The Song holds. As its last note fades, a door opens in the silence it leaves behind."},
            {'kind': 'trial', 'title': 'The Hall of Unsung Kings', 'room': 16010, 'trial': 'bard',
             'text': ("Through the door is the hall where the Song was last sung, and the king who has waited a thousand "
                      "years in its silence."),
             'objective': 'Enter the hall and sing for the Mute King',
             'action': 'Enter the trial',
             'done': "The Mute King falls, and with his last breath — for the first time in a thousand years — he sings."},
            {'kind': 'return', 'title': 'The Last Lesson',
             'text': "Bring the Song of the Ages home to the bards' guildmaster.",
             'objective': "Return to the bards' guildmaster",
             'say': ("The guildmaster listens to all four verses with their eyes closed. When you finish they restring the "
                     "lute and hand it to you. 'Again,' they say. 'All of it. And this time sing it like the world is "
                     "listening — because it will be.'")},
        ],
    },
    'assassin': {
        'id': 'marquee_assassin',
        'name': 'The Contract of Mirrors',
        'ability': 'thousand_shadows',
        'giver': 3022,                      # the thieves' guildmaster, who also keeps the assassins' contracts
        'giver_room': 3029,
        'giver_name': "the thieves' guildmaster",
        'offer': ("The guildmaster slides a folded paper across the table without looking at you. Three names on it, and a "
                  "fourth — crossed out, written again, crossed out again. 'The guild's oldest contract. The first three "
                  "are its guard. The fourth is the reason the guild was founded. A veiled informant in the Shadowspire "
                  "sells the rest. Finish it, and I'll teach you what the last one who tried learned too late.'"),
        'teaches': ("Thousand Shadows — for three rounds your shadows strike every foe around you, and the last of them "
                    "finishes the weakest."),
        'stages': [
            {'kind': 'talk', 'title': 'The Informant', 'npc': 9788, 'room': 24502,
             'text': ("A veiled informant sells names in the Shadowspire Citadel, north of the eastern road past the "
                      "Sunken Coast."),
             'objective': 'Speak with the veiled informant',
             'say': ("The informant's voice is a woman's, then an old man's. 'Three mirror-blades guard the fourth name — "
                     "in the Mirror Chamber, the Hall of Eclipsed Light, the Throne of Reflections. Kill them, and the fourth "
                     "will come looking for you. But you will need a poison it has never tasted: black lotus, from the "
                     "Sunken Coast.'")},
            {'kind': 'kill', 'title': 'The Three Names',
             'text': "Three mirror-blades, the guard of the guild's oldest contract, wait in the Shadowspire's halls of glass.",
             'spawns': [
                 {'vnum': 9780, 'room': 24505, 'kind': 'elite', 'label': 'Strike the first name, in the Mirror Chamber'},
                 {'vnum': 9780, 'room': 24510, 'kind': 'elite', 'label': 'Strike the second name, in the Hall of Eclipsed Light'},
                 {'vnum': 9780, 'room': 24518, 'kind': 'elite', 'label': 'Strike the third name, on the Throne of Reflections'},
             ],
             'adds': 9787,
             'done': "Three names crossed out. Somewhere, the fourth knows."},
            {'kind': 'collect', 'title': 'Black Lotus', 'mob': 9781, 'rooms': [6802, 6805, 6806],
             'per_room': 2, 'need': 5, 'chance': 55, 'item': 'black lotus',
             'text': ("Cutthroats of the Sunken Coast smuggle black lotus for the Poisoner — on the Smuggler's Dock, the "
                      "Outer Pier and in the Tidal Cave (bring a light)."),
             'objective': 'Take the black lotus',
             'done': "The black lotus smells of nothing at all. The Poisoner will want it back."},
            {'kind': 'kill', 'title': 'The Poisoner',
             'text': ("The Poisoner brews in the dark grotto of the Tidal Cave, and only he knows how to make black lotus "
                      "kill a thing that has no face."),
             'spawns': [{'vnum': 9782, 'room': 6807, 'kind': 'warden', 'label': 'Kill the Poisoner'}],
             'done': "The Poisoner dies in his own miasma. His last brew, finished, is yours: a poison for the faceless."},
            {'kind': 'ritual', 'title': 'The Ambush', 'room': 24519, 'verb': 'wait', 'seconds': 30,
             'waves': [{'at': 0, 'vnum': 9783, 'count': 2, 'text': "The marks' bodyguards come into the Sanctum, searching!"},
                       {'at': 10, 'vnum': 9783, 'count': 2, 'text': 'More bodyguards come, sweeping every shadow!'},
                       {'at': 20, 'vnum': 9783, 'count': 3, 'text': 'They know you are here — every last one of them comes!'}],
             'text': ("Wait in the Sanctum of Light in the Shadowspire, where the light dies, for the fourth name to come "
                      "to you — and hold your ground while its bodyguards hunt for you."),
             'objective': 'Wait in ambush in the Sanctum of Light',
             'action': 'Wait in ambush',
             'start': ("You coat your blades, step into the one shadow in the Sanctum of Light, and wait. Footsteps — many "
                       "footsteps — begin to search the halls."),
             'done': ("The last bodyguard falls. In the mirror on the far wall, someone who is not you is wearing your face. "
                      "It beckons.")},
            {'kind': 'trial', 'title': 'The Hall of a Thousand Mirrors', 'room': 24519, 'trial': 'assassin',
             'text': ("Step through the mirror into the hall of a thousand mirrors, where the guild's oldest contract has "
                      "waited for you."),
             'objective': 'Step through the mirror and fulfil the contract',
             'action': 'Enter the trial',
             'done': "The Faceless One shatters like glass. The contract is fulfilled."},
            {'kind': 'return', 'title': 'The Last Lesson',
             'text': "Bring the fulfilled contract home to the thieves' guildmaster.",
             'objective': "Return to the thieves' guildmaster",
             'say': ("The guildmaster reads the paper with the fourth name crossed out for the last time, then holds it to "
                     "the candle. 'The last one who tried learned too late that there are always more of you than there "
                     "are of them,' they say, watching it burn. 'Let me show you how to be a thousand.'")},
        ],
    },
}

# where each class finds its quest (several classes may share a guildmaster)
GIVERS = {}
for _cls, _q in QUESTS.items():
    GIVERS.setdefault(_q['giver'], []).append(_cls)


def quest_for(cls):
    return QUESTS.get(str(cls or '').lower())


def by_id(qid):
    for cls, q in QUESTS.items():
        if q['id'] == qid:
            return cls, q
    return None, None
