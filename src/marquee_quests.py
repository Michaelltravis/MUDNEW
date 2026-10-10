"""What each class's marquee quest asks (the engine is marquee.py).

A quest is offered by the class's guildmaster from level 45 and teaches the class's marquee
ability (marquee_abilities.py). It is a chain of stages through the endgame zones, ending in a
private trial; alone it takes about two hours, and a group that embarks with the hero makes
its foes harder by how many joined (marquee_scale.py).

Stage kinds:
  talk     speak with `npc` (in `room`; the engine places a copy there if none stands there)
  kill     slay the quest's own foes: `spawns` [{vnum, room, kind, label}], each placed when the
           party comes near; `adds` (a vnum) joins each one, one more for every two heroes
  collect  slay `mob` (kept at `per_room` in each of `rooms` while the party is there) until
           `need` (+1 per two extra heroes) `item`s were taken, each kill yielding one at `chance`%
  ritual   `verb` in `room` starts it: hold there for `seconds` while `waves` [{at, vnum, count,
           text}] come, and slay them all
  trial    `trial enter` in `room` opens the private trial (world/marquee/trials/<trial>.json)
  return   speak with the giver again: the ability is taught

Mob vnums 9700-9799 are the quests' own creatures (world/zones/zone_097.json; never reset):
the warrior's are 9700-9709. `kind` picks how much health a foe gets (marquee_scale.ROUNDS).
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
