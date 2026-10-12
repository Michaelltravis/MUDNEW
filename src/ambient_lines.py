"""What the world murmurs, and where (ambient.py picks; ambient_place.py says where you are).

Each line is (text, sound) under a key of place tags joined by '+': a line fits only where
EVERY tag holds (a blacksmith's hammer only beside a smithy, haggling only beside a shop, cart
wheels only on a street, never in a castle hall). `sound` is the /play client's ambient sound
(soundtable.js amb_*), or None for a line that is only a thing seen or felt.

Creatures are not narrated from a list: what is really next door makes the sound
(ambient.py presence_line).
"""

LINES = {
    # ---- towns: only where the town really is ----
    'smithy': [
        ("You hear the rhythmic hammering of a blacksmith at work.", 'amb_anvil'),
        ("Hammer rings on anvil close by.", 'amb_anvil'),
        ("A forge bellows wheezes, and sparks hiss in a quench.", 'amb_anvil'),
    ],
    'market': [
        ("A merchant calls out, hawking their wares.", 'amb_crowd'),
        ("Merchants haggle loudly in a nearby stall.", 'amb_crowd'),
        ("Two shoppers argue over a price.", 'amb_crowd'),
        ("Coins clink on a counter nearby.", 'amb_coins'),
    ],
    'bakery': [
        ("The smell of fresh bread wafts from a nearby bakery.", None),
    ],
    'tavern': [
        ("Laughter and the clink of tankards carry from the taproom.", 'amb_crowd'),
        ("Someone strikes up a tune on a battered lute.", None),
        ("A chair scrapes and a door bangs somewhere in the inn.", 'amb_door'),
    ],
    'street': [
        ("You hear the clatter of cart wheels on cobblestones.", 'amb_cart'),
        ("A dog barks somewhere down the street.", None),
        ("Children's laughter echoes from a nearby alley.", None),
        ("A cat darts across the street and disappears into shadows.", None),
        ("A town crier calls the hour.", 'amb_bell'),
    ],
    'street+day': [
        ("A bell tolls the hour from a distant tower.", 'amb_bell'),
    ],
    'building': [
        ("Dust motes dance in a shaft of light.", None),
        ("A floorboard creaks somewhere in the building.", 'amb_creak'),
        ("You hear muffled voices through the walls.", None),
        ("A candle flickers, casting dancing shadows.", None),
        ("The building settles with a soft groan.", 'amb_creak'),
        ("A mouse scurries along the baseboard.", None),
    ],

    # ---- castles and keeps ----
    'castle': [
        ("Wind moans through an arrow slit.", 'amb_wind'),
        ("Somewhere above, a chain shifts against stone.", 'amb_chain'),
        ("A heavy door booms shut far off in the castle.", 'amb_door'),
        ("Your footsteps ring back from the cold stone.", 'amb_steps'),
        ("A tattered banner stirs in a draught.", None),
        ("Dust sifts down from the old vaulting.", None),
    ],

    # ---- under the earth ----
    'cave': [
        ("Water drips from the ceiling somewhere ahead.", 'amb_drip'),
        ("Your footsteps echo off the stone walls.", 'amb_steps'),
        ("You hear a distant rumble deep in the earth.", None),
        ("A cold draft brushes past you.", 'amb_wind'),
        ("A bat flutters past in the darkness.", None),
        ("The rock groans as if under great pressure.", None),
        ("Phosphorescent fungi pulse with a faint glow.", None),
    ],
    'mine': [
        ("A pick rings against rock somewhere deep in the workings.", 'amb_anvil'),
        ("Old timbers creak under the weight of the mountain.", 'amb_creak'),
        ("Water drips steadily into a rusted cart.", 'amb_drip'),
    ],
    'crypt': [
        ("Bones shift somewhere in the dark.", None),
        ("A cold breath of air carries the smell of old tombs.", 'amb_wind'),
        ("Something scrapes behind a sealed slab.", 'amb_chain'),
        ("Water drips onto stone in the silence.", 'amb_drip'),
    ],
    'sewer': [
        ("Water gurgles through the channel.", 'amb_drip'),
        ("Rats squeal somewhere in the dark.", None),
        ("The stench of the sewer catches in your throat.", None),
    ],
    'dungeon': [
        ("Chains rattle somewhere down the passage.", 'amb_chain'),
        ("A distant moan drifts through the stone.", None),
        ("Water drips steadily somewhere in the darkness.", 'amb_drip'),
    ],

    # ---- the wilds ----
    'forest': [
        ("Leaves rustle in the breeze above you.", 'amb_wind'),
        ("A bird calls out from the treetops.", None),
        ("Something small scurries through the underbrush.", None),
        ("Sunlight filters through the canopy, dappling the forest floor.", None),
        ("A woodpecker drums on a distant tree.", None),
        ("Branches creak and sway overhead.", 'amb_creak'),
        ("You catch a glimpse of a deer through the trees.", None),
    ],
    'field': [
        ("Tall grass sways in the wind.", 'amb_wind'),
        ("A hawk circles lazily overhead.", None),
        ("Insects buzz and hum around you.", None),
        ("The wind carries the scent of wildflowers.", None),
        ("A rabbit darts across your path and disappears.", None),
    ],
    'hills': [
        ("The wind whistles across the rocky terrain.", 'amb_wind'),
        ("Small stones clatter down a nearby slope.", None),
        ("An eagle cries out as it soars above.", None),
    ],
    'mountain': [
        ("The cold wind bites at exposed skin.", 'amb_wind'),
        ("Loose rocks clatter down a nearby slope.", None),
        ("An avalanche rumbles in the distance.", None),
        ("Mountain goats scramble across distant ledges.", None),
    ],
    'snow': [
        ("Snow hisses across the drifts on the wind.", 'amb_wind'),
        ("Ice cracks somewhere with a sharp report.", None),
        ("The world is hushed under a blanket of white.", None),
    ],
    'swamp': [
        ("Something splashes in the murky water nearby.", 'amb_drip'),
        ("A frog croaks from somewhere in the muck.", None),
        ("Bubbles rise from the stagnant water with a soft plop.", None),
        ("The smell of decay hangs heavy in the air.", None),
        ("A snake slithers through the reeds.", None),
    ],
    'water': [
        ("Fish dart away as you move through the water.", None),
        ("Ripples spread across the water's surface.", None),
        ("A fish jumps, splashing back into the water.", 'amb_drip'),
    ],
    'shore': [
        ("Waves lap gently at the shore.", 'amb_wind'),
        ("A seabird calls out as it glides overhead.", None),
        ("The smell of salt and seaweed fills the air.", None),
    ],
    'desert': [
        ("Heat shimmers off the sand in the distance.", None),
        ("A scorpion scuttles behind a rock.", None),
        ("The wind kicks up a small dust devil.", 'amb_wind'),
        ("The sand shifts beneath your feet.", None),
    ],
    'volcanic': [
        ("The ground trembles, and vents hiss steam.", None),
        ("Ash drifts down like grey snow.", None),
    ],

    # ---- the sky (only under it) ----
    'outdoors+dawn': [
        ("The first rays of sunlight peek over the horizon.", None),
        ("Birds begin their morning chorus.", None),
    ],
    'outdoors+dusk': [
        ("The sky blazes with oranges and reds as the sun sets.", None),
        ("Long shadows stretch across the land.", None),
    ],
    'outdoors+night': [
        ("Stars twinkle in the vast darkness overhead.", None),
        ("The moon casts silver light across the land.", None),
        ("An owl hoots somewhere in the darkness.", None),
    ],
    'outdoors+rain': [
        ("Rain patters steadily on everything around you.", None),
        ("Puddles are forming on the ground.", None),
    ],
    'outdoors+storm': [
        ("Lightning flashes across the sky!", None),
        ("Thunder crashes, making you jump.", None),
        ("The wind howls and rain lashes at you.", 'amb_wind'),
    ],

    # ---- a place of peace ----
    'peaceful': [
        ("A sense of calm washes over you in this place.", None),
        ("You feel safe here, at least for now.", None),
    ],
}

# lines that say where you are most strongly are picked more often
WEIGHT = {'smithy': 2.0, 'market': 1.6, 'tavern': 1.6, 'bakery': 1.2, 'castle': 1.4, 'peaceful': 0.8}

# a creature really next door: what it sounds like, by what it is ({where}: 'to the south',
# 'above you'; ambient.py presence_line)
PRESENCE = {
    'heavy': ["Heavy footsteps sound {where}.", "Something big shifts its weight {where}."],
    'beast': ["Claws scrape on stone {where}.", "You hear heavy breathing {where}."],
    'undead': ["A chill runs down your spine: something dead walks {where}.", "Bones rattle {where}."],
    'person': ["Boots scuff the ground {where}.", "Someone moves about {where}."],
}
