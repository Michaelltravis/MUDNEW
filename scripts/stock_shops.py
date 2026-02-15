#!/usr/bin/env python3
"""Stock all shops, add pets, configure pet shop, add innkeeper for rent system."""
import json
import copy

ZONE_FILE = '../world/zones/zone_030.json'

with open(ZONE_FILE) as f:
    zone = json.load(f)

objs = zone['objects']
mobs = zone['mobs']
rooms = zone['rooms']

# ============================================================
# NEW OBJECTS - Starting from vnum 3300
# ============================================================

new_objects = {
    # ---- WEAPONS BY LEVEL TIER ----
    # Tier 1: Level 1-10
    "3300": {"vnum": 3300, "name": "rusty dagger", "short_desc": "a rusty dagger", "room_desc": "A rusty dagger lies here.", "item_type": "weapon", "weight": 2, "value": 15, "damage_dice": "1d4", "weapon_type": "pierce", "level": 1},
    "3301": {"vnum": 3301, "name": "wooden staff", "short_desc": "a wooden staff", "room_desc": "A simple wooden staff lies here.", "item_type": "weapon", "weight": 4, "value": 25, "damage_dice": "1d6", "weapon_type": "bludgeon", "level": 3},
    "3302": {"vnum": 3302, "name": "short sword", "short_desc": "a short sword", "room_desc": "A short sword lies here.", "item_type": "weapon", "weight": 5, "value": 50, "damage_dice": "1d6+1", "weapon_type": "slash", "level": 5},
    "3303": {"vnum": 3303, "name": "hand axe", "short_desc": "a hand axe", "room_desc": "A hand axe lies here.", "item_type": "weapon", "weight": 6, "value": 75, "damage_dice": "1d8", "weapon_type": "slash", "level": 7},
    "3304": {"vnum": 3304, "name": "spiked mace", "short_desc": "a spiked mace", "room_desc": "A spiked mace lies here.", "item_type": "weapon", "weight": 8, "value": 100, "damage_dice": "2d4", "weapon_type": "bludgeon", "level": 10},
    
    # Tier 2: Level 10-20
    "3305": {"vnum": 3305, "name": "broad sword", "short_desc": "a broad sword", "room_desc": "A broad sword lies here.", "item_type": "weapon", "weight": 8, "value": 200, "damage_dice": "2d5", "weapon_type": "slash", "level": 12},
    "3306": {"vnum": 3306, "name": "battle axe", "short_desc": "a battle axe", "room_desc": "A battle axe lies here.", "item_type": "weapon", "weight": 10, "value": 350, "damage_dice": "2d6", "weapon_type": "slash", "level": 15},
    "3307": {"vnum": 3307, "name": "morning star", "short_desc": "a morning star", "room_desc": "A morning star lies here.", "item_type": "weapon", "weight": 9, "value": 400, "damage_dice": "2d6+1", "weapon_type": "bludgeon", "level": 17},
    "3308": {"vnum": 3308, "name": "bastard sword", "short_desc": "a bastard sword", "room_desc": "A bastard sword lies here.", "item_type": "weapon", "weight": 10, "value": 500, "damage_dice": "2d7", "weapon_type": "slash", "level": 20},
    
    # Tier 3: Level 20-30
    "3309": {"vnum": 3309, "name": "steel claymore", "short_desc": "a steel claymore", "room_desc": "A gleaming steel claymore lies here.", "item_type": "weapon", "weight": 12, "value": 800, "damage_dice": "3d5", "weapon_type": "slash", "level": 22},
    "3310": {"vnum": 3310, "name": "war hammer", "short_desc": "a heavy war hammer", "room_desc": "A heavy war hammer lies here.", "item_type": "weapon", "weight": 14, "value": 1000, "damage_dice": "3d6", "weapon_type": "bludgeon", "level": 25},
    "3311": {"vnum": 3311, "name": "trident", "short_desc": "a steel trident", "room_desc": "A steel trident lies here.", "item_type": "weapon", "weight": 10, "value": 1200, "damage_dice": "3d6+1", "weapon_type": "pierce", "level": 28},
    "3312": {"vnum": 3312, "name": "halberd", "short_desc": "a halberd", "room_desc": "A halberd lies here.", "item_type": "weapon", "weight": 15, "value": 1500, "damage_dice": "3d7", "weapon_type": "slash", "level": 30},
    
    # Tier 4: Level 30-40
    "3313": {"vnum": 3313, "name": "tempered longsword", "short_desc": "a tempered longsword", "room_desc": "A tempered longsword gleams here.", "item_type": "weapon", "weight": 10, "value": 2500, "damage_dice": "4d5", "weapon_type": "slash", "level": 33},
    "3314": {"vnum": 3314, "name": "spiked flail", "short_desc": "a spiked flail", "room_desc": "A spiked flail lies here.", "item_type": "weapon", "weight": 12, "value": 3000, "damage_dice": "4d6", "weapon_type": "bludgeon", "level": 36},
    "3315": {"vnum": 3315, "name": "composite bow", "short_desc": "a composite bow", "room_desc": "A composite bow lies here.", "item_type": "weapon", "weight": 6, "value": 3500, "damage_dice": "4d6+1", "weapon_type": "pierce", "level": 40},
    
    # Tier 5: Level 40-50
    "3316": {"vnum": 3316, "name": "hardened steel greatsword", "short_desc": "a hardened steel greatsword", "room_desc": "A massive hardened steel greatsword lies here.", "item_type": "weapon", "weight": 14, "value": 5000, "damage_dice": "5d5", "weapon_type": "slash", "level": 43},
    "3317": {"vnum": 3317, "name": "runic war axe", "short_desc": "a runic war axe", "room_desc": "A war axe etched with runes lies here.", "item_type": "weapon", "weight": 12, "value": 7000, "damage_dice": "5d6", "weapon_type": "slash", "level": 47},
    "3318": {"vnum": 3318, "name": "mithril rapier", "short_desc": "a mithril rapier", "room_desc": "A gleaming mithril rapier lies here.", "item_type": "weapon", "weight": 5, "value": 8000, "damage_dice": "5d6+2", "weapon_type": "pierce", "level": 50},
    
    # Tier 6: Level 50-60
    "3319": {"vnum": 3319, "name": "adamantine blade", "short_desc": "an adamantine blade", "room_desc": "A dark adamantine blade lies here.", "item_type": "weapon", "weight": 10, "value": 12000, "damage_dice": "6d6", "weapon_type": "slash", "level": 53},
    "3320": {"vnum": 3320, "name": "enchanted maul", "short_desc": "an enchanted maul", "room_desc": "An enchanted maul pulses with energy here.", "item_type": "weapon", "weight": 16, "value": 15000, "damage_dice": "6d7", "weapon_type": "bludgeon", "level": 57},
    "3321": {"vnum": 3321, "name": "dragonbone lance", "short_desc": "a dragonbone lance", "room_desc": "A lance carved from dragon bone lies here.", "item_type": "weapon", "weight": 12, "value": 20000, "damage_dice": "7d6", "weapon_type": "pierce", "level": 60},

    # ---- ARMOR BY LEVEL TIER ----
    # Tier 1: Level 1-10 (body, head, legs, arms, hands, feet, shield)
    "3330": {"vnum": 3330, "name": "padded vest", "short_desc": "a padded vest", "room_desc": "A padded vest lies here.", "item_type": "armor", "wear_slot": "body", "weight": 5, "value": 30, "armor_bonus": 1, "level": 1},
    "3331": {"vnum": 3331, "name": "cloth cap", "short_desc": "a cloth cap", "room_desc": "A cloth cap lies here.", "item_type": "armor", "wear_slot": "head", "weight": 1, "value": 15, "armor_bonus": 1, "level": 1},
    "3332": {"vnum": 3332, "name": "leather boots", "short_desc": "a pair of leather boots", "room_desc": "A pair of leather boots lies here.", "item_type": "armor", "wear_slot": "feet", "weight": 3, "value": 20, "armor_bonus": 1, "level": 1},
    "3333": {"vnum": 3333, "name": "wooden buckler", "short_desc": "a wooden buckler", "room_desc": "A wooden buckler lies here.", "item_type": "armor", "wear_slot": "shield", "weight": 5, "value": 25, "armor_bonus": 1, "level": 3},

    # Tier 2: Level 10-20
    "3334": {"vnum": 3334, "name": "reinforced leather armor", "short_desc": "reinforced leather armor", "room_desc": "A suit of reinforced leather armor lies here.", "item_type": "armor", "wear_slot": "body", "weight": 12, "value": 250, "armor_bonus": 3, "level": 12},
    "3335": {"vnum": 3335, "name": "iron helm", "short_desc": "an iron helm", "room_desc": "An iron helm lies here.", "item_type": "armor", "wear_slot": "head", "weight": 5, "value": 150, "armor_bonus": 2, "level": 12},
    "3336": {"vnum": 3336, "name": "iron greaves", "short_desc": "a pair of iron greaves", "room_desc": "A pair of iron greaves lies here.", "item_type": "armor", "wear_slot": "legs", "weight": 8, "value": 200, "armor_bonus": 2, "level": 12},
    "3337": {"vnum": 3337, "name": "iron gauntlets", "short_desc": "a pair of iron gauntlets", "room_desc": "A pair of iron gauntlets lies here.", "item_type": "armor", "wear_slot": "hands", "weight": 4, "value": 120, "armor_bonus": 2, "level": 12},
    "3338": {"vnum": 3338, "name": "iron shield", "short_desc": "an iron shield", "room_desc": "An iron shield lies here.", "item_type": "armor", "wear_slot": "shield", "weight": 10, "value": 200, "armor_bonus": 3, "level": 15},

    # Tier 3: Level 20-30
    "3339": {"vnum": 3339, "name": "steel chain mail", "short_desc": "a suit of steel chain mail", "room_desc": "A suit of steel chain mail lies here.", "item_type": "armor", "wear_slot": "body", "weight": 20, "value": 800, "armor_bonus": 5, "level": 22},
    "3340": {"vnum": 3340, "name": "steel helm", "short_desc": "a steel helm", "room_desc": "A steel helm lies here.", "item_type": "armor", "wear_slot": "head", "weight": 6, "value": 500, "armor_bonus": 3, "level": 22},
    "3341": {"vnum": 3341, "name": "steel leggings", "short_desc": "a pair of steel leggings", "room_desc": "A pair of steel leggings lies here.", "item_type": "armor", "wear_slot": "legs", "weight": 10, "value": 600, "armor_bonus": 4, "level": 25},
    "3342": {"vnum": 3342, "name": "steel tower shield", "short_desc": "a steel tower shield", "room_desc": "A steel tower shield lies here.", "item_type": "armor", "wear_slot": "shield", "weight": 15, "value": 700, "armor_bonus": 5, "level": 28},

    # Tier 4: Level 30-40
    "3343": {"vnum": 3343, "name": "banded mail", "short_desc": "a suit of banded mail", "room_desc": "A suit of banded mail lies here.", "item_type": "armor", "wear_slot": "body", "weight": 25, "value": 2000, "armor_bonus": 7, "level": 33},
    "3344": {"vnum": 3344, "name": "great helm", "short_desc": "a great helm", "room_desc": "A great helm lies here.", "item_type": "armor", "wear_slot": "head", "weight": 8, "value": 1200, "armor_bonus": 5, "level": 35},
    "3345": {"vnum": 3345, "name": "plated leggings", "short_desc": "a pair of plated leggings", "room_desc": "A pair of plated leggings lies here.", "item_type": "armor", "wear_slot": "legs", "weight": 14, "value": 1500, "armor_bonus": 5, "level": 37},
    "3346": {"vnum": 3346, "name": "plated gauntlets", "short_desc": "a pair of plated gauntlets", "room_desc": "A pair of plated gauntlets lies here.", "item_type": "armor", "wear_slot": "hands", "weight": 5, "value": 1000, "armor_bonus": 4, "level": 35},

    # Tier 5: Level 40-50
    "3347": {"vnum": 3347, "name": "mithril chain shirt", "short_desc": "a mithril chain shirt", "room_desc": "A shimmering mithril chain shirt lies here.", "item_type": "armor", "wear_slot": "body", "weight": 15, "value": 5000, "armor_bonus": 9, "level": 43},
    "3348": {"vnum": 3348, "name": "mithril helm", "short_desc": "a mithril helm", "room_desc": "A mithril helm lies here.", "item_type": "armor", "wear_slot": "head", "weight": 4, "value": 3000, "armor_bonus": 6, "level": 45},
    "3349": {"vnum": 3349, "name": "mithril greaves", "short_desc": "a pair of mithril greaves", "room_desc": "A pair of mithril greaves lies here.", "item_type": "armor", "wear_slot": "legs", "weight": 8, "value": 3500, "armor_bonus": 7, "level": 47},

    # Tier 6: Level 50-60
    "3350": {"vnum": 3350, "name": "adamantine plate armor", "short_desc": "a suit of adamantine plate armor", "room_desc": "A dark suit of adamantine plate armor lies here.", "item_type": "armor", "wear_slot": "body", "weight": 30, "value": 12000, "armor_bonus": 12, "level": 53},
    "3351": {"vnum": 3351, "name": "adamantine helm", "short_desc": "an adamantine helm", "room_desc": "An adamantine helm lies here.", "item_type": "armor", "wear_slot": "head", "weight": 6, "value": 7000, "armor_bonus": 8, "level": 55},
    "3352": {"vnum": 3352, "name": "adamantine greaves", "short_desc": "a pair of adamantine greaves", "room_desc": "A pair of adamantine greaves lies here.", "item_type": "armor", "wear_slot": "legs", "weight": 12, "value": 8000, "armor_bonus": 9, "level": 57},
    "3353": {"vnum": 3353, "name": "dragonscale shield", "short_desc": "a dragonscale shield", "room_desc": "A shield made of dragon scales lies here.", "item_type": "armor", "wear_slot": "shield", "weight": 12, "value": 15000, "armor_bonus": 10, "level": 60},

    # ---- MAGIC SHOP ITEMS ----
    # Potions
    "3360": {"vnum": 3360, "name": "minor healing potion", "short_desc": "a minor healing potion", "room_desc": "A small red potion sits here.", "item_type": "potion", "weight": 1, "value": 50, "level": 1, "spell": "cure light", "spell_level": 5},
    "3361": {"vnum": 3361, "name": "healing potion", "short_desc": "a healing potion", "room_desc": "A red potion sits here.", "item_type": "potion", "weight": 1, "value": 150, "level": 10, "spell": "cure serious", "spell_level": 15},
    "3362": {"vnum": 3362, "name": "greater healing potion", "short_desc": "a greater healing potion", "room_desc": "A glowing red potion sits here.", "item_type": "potion", "weight": 1, "value": 400, "level": 20, "spell": "cure critical", "spell_level": 25},
    "3363": {"vnum": 3363, "name": "minor mana potion", "short_desc": "a minor mana potion", "room_desc": "A small blue potion sits here.", "item_type": "potion", "weight": 1, "value": 50, "level": 1, "spell": "restore mana", "spell_level": 5},
    "3364": {"vnum": 3364, "name": "mana potion", "short_desc": "a mana potion", "room_desc": "A blue potion sits here.", "item_type": "potion", "weight": 1, "value": 150, "level": 10, "spell": "restore mana", "spell_level": 15},
    "3365": {"vnum": 3365, "name": "greater mana potion", "short_desc": "a greater mana potion", "room_desc": "A glowing blue potion sits here.", "item_type": "potion", "weight": 1, "value": 400, "level": 20, "spell": "restore mana", "spell_level": 25},
    "3366": {"vnum": 3366, "name": "potion of strength", "short_desc": "a potion of strength", "room_desc": "An orange potion sits here.", "item_type": "potion", "weight": 1, "value": 300, "level": 15, "spell": "strength", "spell_level": 15},
    "3367": {"vnum": 3367, "name": "potion of armor", "short_desc": "a potion of armor", "room_desc": "A silver potion sits here.", "item_type": "potion", "weight": 1, "value": 250, "level": 10, "spell": "armor", "spell_level": 10},
    "3368": {"vnum": 3368, "name": "antidote", "short_desc": "a vial of antidote", "room_desc": "A green vial sits here.", "item_type": "potion", "weight": 1, "value": 100, "level": 5, "spell": "cure poison", "spell_level": 10},
    "3369": {"vnum": 3369, "name": "potion of sanctuary", "short_desc": "a potion of sanctuary", "room_desc": "A white glowing potion sits here.", "item_type": "potion", "weight": 1, "value": 1000, "level": 30, "spell": "sanctuary", "spell_level": 30},

    # Scrolls
    "3370": {"vnum": 3370, "name": "scroll of recall", "short_desc": "a scroll of recall", "room_desc": "A glowing scroll lies here.", "item_type": "scroll", "weight": 1, "value": 100, "level": 1, "spell": "word of recall", "spell_level": 10},
    "3371": {"vnum": 3371, "name": "scroll of identify", "short_desc": "a scroll of identify", "room_desc": "A scroll covered in tiny runes lies here.", "item_type": "scroll", "weight": 1, "value": 200, "level": 5, "spell": "identify", "spell_level": 15},
    "3372": {"vnum": 3372, "name": "scroll of teleport", "short_desc": "a scroll of teleport", "room_desc": "A shimmering scroll lies here.", "item_type": "scroll", "weight": 1, "value": 500, "level": 20, "spell": "teleport", "spell_level": 25},
    "3373": {"vnum": 3373, "name": "scroll of remove curse", "short_desc": "a scroll of remove curse", "room_desc": "A holy scroll lies here.", "item_type": "scroll", "weight": 1, "value": 350, "level": 15, "spell": "remove curse", "spell_level": 20},
    "3374": {"vnum": 3374, "name": "scroll of enchant weapon", "short_desc": "a scroll of enchant weapon", "room_desc": "A mystic scroll lies here.", "item_type": "scroll", "weight": 1, "value": 800, "level": 25, "spell": "enchant weapon", "spell_level": 25},

    # Wands & Staves
    "3375": {"vnum": 3375, "name": "wand of magic missile", "short_desc": "a wand of magic missile", "room_desc": "A thin wand lies here.", "item_type": "wand", "weight": 2, "value": 500, "level": 5, "spell": "magic missile", "charges": 10},
    "3376": {"vnum": 3376, "name": "wand of lightning", "short_desc": "a wand of lightning", "room_desc": "A crackling wand lies here.", "item_type": "wand", "weight": 2, "value": 1500, "level": 20, "spell": "lightning bolt", "charges": 8},
    "3377": {"vnum": 3377, "name": "staff of healing", "short_desc": "a staff of healing", "room_desc": "A white staff radiates warmth here.", "item_type": "staff", "weight": 5, "value": 2000, "level": 15, "spell": "cure serious", "charges": 12},

    # ---- GENERAL STORE ITEMS ----
    "3380": {"vnum": 3380, "name": "backpack", "short_desc": "a leather backpack", "room_desc": "A leather backpack lies here.", "item_type": "container", "weight": 3, "value": 50, "capacity": 100},
    "3381": {"vnum": 3381, "name": "rope", "short_desc": "a coil of rope", "room_desc": "A coil of rope lies here.", "item_type": "other", "weight": 5, "value": 20},
    "3382": {"vnum": 3382, "name": "waterskin", "short_desc": "a waterskin of fresh water", "room_desc": "A waterskin lies here.", "item_type": "drink", "weight": 3, "value": 15, "capacity": 12, "current": 12},
    "3383": {"vnum": 3383, "name": "rations", "short_desc": "a pack of trail rations", "room_desc": "A pack of trail rations lies here.", "item_type": "food", "weight": 2, "value": 10, "nutrition": 20, "food_value": 25},
    "3384": {"vnum": 3384, "name": "bandages", "short_desc": "a roll of bandages", "room_desc": "A roll of bandages lies here.", "item_type": "other", "weight": 1, "value": 10},
    "3385": {"vnum": 3385, "name": "oil flask", "short_desc": "a flask of oil", "room_desc": "A flask of oil lies here.", "item_type": "light", "weight": 2, "value": 15, "light_hours": 48},
    "3386": {"vnum": 3386, "name": "large sack", "short_desc": "a large sack", "room_desc": "A large sack lies here.", "item_type": "container", "weight": 2, "value": 30, "capacity": 75},

    # ---- BAKER EXTRA ITEMS ----
    "3390": {"vnum": 3390, "name": "cinnamon roll", "short_desc": "a warm cinnamon roll", "room_desc": "A warm cinnamon roll sits here.", "item_type": "food", "weight": 1, "value": 15, "nutrition": 15, "food_value": 18},
    "3391": {"vnum": 3391, "name": "honey cake", "short_desc": "a honey cake", "room_desc": "A golden honey cake sits here.", "item_type": "food", "weight": 1, "value": 25, "nutrition": 20, "food_value": 22},
    "3392": {"vnum": 3392, "name": "meat pie", "short_desc": "a hearty meat pie", "room_desc": "A steaming meat pie sits here.", "item_type": "food", "weight": 2, "value": 30, "nutrition": 30, "food_value": 35},
    "3393": {"vnum": 3393, "name": "elven bread", "short_desc": "a loaf of elven bread", "room_desc": "A fragrant loaf of elven bread sits here.", "item_type": "food", "weight": 1, "value": 50, "nutrition": 40, "food_value": 45},
    "3394": {"vnum": 3394, "name": "sweet berry tart", "short_desc": "a sweet berry tart", "room_desc": "A sweet berry tart sits here.", "item_type": "food", "weight": 1, "value": 20, "nutrition": 12, "food_value": 15},
    "3395": {"vnum": 3395, "name": "rye bread", "short_desc": "a loaf of rye bread", "room_desc": "A dark loaf of rye bread sits here.", "item_type": "food", "weight": 1, "value": 8, "nutrition": 18, "food_value": 20},
}

# Add all new objects to zone
for k, v in new_objects.items():
    objs[k] = v

# ============================================================
# UPDATE SHOP CONFIGS
# ============================================================

# Wizard (Magic Shop) - vnum 3000
mobs['3000']['gold'] = 200000
mobs['3000']['shop_config'] = {
    "sells": [3050, 3051, 3134, 3135, 3136, 3360, 3361, 3362, 3363, 3364, 3365, 3366, 3367, 3368, 3369, 3370, 3371, 3372, 3373, 3374, 3375, 3376, 3377],
    "buys": ["scroll", "potion", "wand", "staff"],
    "markup": 1.8,
    "markdown": 0.4
}
mobs['3000']['inventory'] = [3050, 3051, 3134, 3135, 3136, 3360, 3361, 3362, 3363, 3364, 3365, 3366, 3367, 3368, 3369, 3370, 3371, 3372, 3373, 3374, 3375, 3376, 3377]

# Baker - vnum 3001
mobs['3001']['gold'] = 100000
mobs['3001']['shop_config'] = {
    "sells": [3009, 3010, 3011, 3101, 3130, 3131, 3132, 3390, 3391, 3392, 3393, 3394, 3395],
    "buys": ["food"],
    "markup": 1.3,
    "markdown": 0.5
}
mobs['3001']['inventory'] = [3009, 3010, 3011, 3101, 3130, 3131, 3132, 3390, 3391, 3392, 3393, 3394, 3395]

# Grocer (General Store) - vnum 3002
mobs['3002']['gold'] = 150000
mobs['3002']['shop_config'] = {
    "sells": [3030, 3031, 3032, 3033, 3036, 3102, 3133, 3137, 3138, 3380, 3381, 3382, 3383, 3384, 3385, 3386],
    "buys": ["food", "drinkcon", "drink", "light", "container", "other"],
    "markup": 1.5,
    "markdown": 0.5
}
mobs['3002']['inventory'] = [3030, 3031, 3032, 3033, 3036, 3102, 3133, 3137, 3138, 3380, 3381, 3382, 3383, 3384, 3385, 3386]

# Weaponsmith - vnum 3003
mobs['3003']['gold'] = 500000
mobs['3003']['shop_config'] = {
    "sells": [3020, 3021, 3022, 3023, 3024, 3025, 3300, 3301, 3302, 3303, 3304, 3305, 3306, 3307, 3308, 3309, 3310, 3311, 3312, 3313, 3314, 3315, 3316, 3317, 3318, 3319, 3320, 3321],
    "buys": ["weapon"],
    "markup": 1.15,
    "markdown": 0.25,
    "starting_gold": 500000
}
mobs['3003']['inventory'] = [3020, 3021, 3022, 3023, 3024, 3025, 3300, 3301, 3302, 3303, 3304, 3305, 3306, 3307, 3308, 3309, 3310, 3311, 3312, 3313, 3314, 3315, 3316, 3317, 3318, 3319, 3320, 3321]

# Armourer - vnum 3004
mobs['3004']['gold'] = 500000
mobs['3004']['shop_config'] = {
    "sells": [3040, 3041, 3042, 3043, 3044, 3045, 3046, 3070, 3071, 3075, 3076, 3080, 3081, 3085, 3086, 3330, 3331, 3332, 3333, 3334, 3335, 3336, 3337, 3338, 3339, 3340, 3341, 3342, 3343, 3344, 3345, 3346, 3347, 3348, 3349, 3350, 3351, 3352, 3353],
    "buys": ["armor"],
    "markup": 1.2,
    "markdown": 0.3,
    "starting_gold": 500000
}
mobs['3004']['inventory'] = [3040, 3041, 3042, 3043, 3044, 3045, 3046, 3070, 3071, 3075, 3076, 3080, 3081, 3085, 3086, 3330, 3331, 3332, 3333, 3334, 3335, 3336, 3337, 3338, 3339, 3340, 3341, 3342, 3343, 3344, 3345, 3346, 3347, 3348, 3349, 3350, 3351, 3352, 3353]

# ============================================================
# PET SHOP - Add more pets (room 3032 holds pet mobs)
# ============================================================

# Make Pet Shop Boy a shopkeeper
mobs['3089']['special'] = 'shopkeeper'
mobs['3089']['gold'] = 100000
mobs['3089']['flags'] = ["special", "sentinel", "memory", "no_charm", "no_summmon"]

# Add new pet mobs
new_pet_mobs = {
    "3096": {
        "vnum": 3096, "name": "tabby cat", "short_desc": "a tabby cat",
        "long_desc": "A tabby cat purrs contentedly here.",
        "level": 2, "alignment": 500, "hp_dice": "3d6+10", "damage_dice": "1d3",
        "gold": 100, "exp": 20, "armor_class": 8,
        "flags": ["sentinel"], "description": "A friendly tabby cat with green eyes."
    },
    "3097": {
        "vnum": 3097, "name": "war dog", "short_desc": "a trained war dog",
        "long_desc": "A large trained war dog stands alert here.",
        "level": 8, "alignment": 500, "hp_dice": "8d8+40", "damage_dice": "2d4+2",
        "gold": 800, "exp": 150, "armor_class": 4,
        "flags": ["sentinel"], "description": "A muscular war dog with a spiked collar."
    },
    "3098": {
        "vnum": 3098, "name": "snake", "short_desc": "a green snake",
        "long_desc": "A green snake coils here, watching you.",
        "level": 4, "alignment": 0, "hp_dice": "4d6+15", "damage_dice": "1d4+1",
        "gold": 200, "exp": 50, "armor_class": 6,
        "flags": ["sentinel"], "description": "A sleek green snake with gleaming scales."
    },
    "3099": {
        "vnum": 3099, "name": "hawk", "short_desc": "a trained hawk",
        "long_desc": "A trained hawk perches here, scanning the area.",
        "level": 6, "alignment": 500, "hp_dice": "5d6+20", "damage_dice": "1d6+1",
        "gold": 500, "exp": 80, "armor_class": 5,
        "flags": ["sentinel"], "description": "A magnificent hawk with sharp talons."
    },
    "3100": {
        "vnum": 3100, "name": "black bear", "short_desc": "a black bear",
        "long_desc": "A large black bear lumbers around here.",
        "level": 12, "alignment": 0, "hp_dice": "12d10+60", "damage_dice": "2d6+3",
        "gold": 2000, "exp": 400, "armor_class": 2,
        "flags": ["sentinel"], "description": "A powerful black bear with thick fur."
    },
    "3101": {
        "vnum": 3101, "name": "raven", "short_desc": "a sleek raven",
        "long_desc": "A sleek black raven caws softly here.",
        "level": 3, "alignment": 0, "hp_dice": "3d4+8", "damage_dice": "1d3",
        "gold": 150, "exp": 30, "armor_class": 7,
        "flags": ["sentinel"], "description": "An intelligent-looking black raven."
    },
    "3102": {
        "vnum": 3102, "name": "dire wolf", "short_desc": "a dire wolf",
        "long_desc": "A massive dire wolf growls softly here.",
        "level": 15, "alignment": 0, "hp_dice": "15d10+80", "damage_dice": "3d4+4",
        "gold": 3500, "exp": 600, "armor_class": 1,
        "flags": ["sentinel"], "description": "An enormous grey wolf, far larger than normal."
    },
}

# Check for conflicts with existing mobs (3096-3102)
# 3095=cryogenicist exists, 3096=bulletin board obj, but mob vnums separate
# Actually 3096-3099 in objs are bulletin boards, but mob namespace is separate
for k, v in new_pet_mobs.items():
    if k not in mobs:
        mobs[k] = v

# Add pet mobs to room 3032 (pet store back room)
existing_resets = rooms['3032'].get('mob_resets', [])
existing_vnums = {r['vnum'] for r in existing_resets}
for vnum in [3096, 3097, 3098, 3099, 3100, 3101, 3102]:
    if vnum not in existing_vnums:
        existing_resets.append({"vnum": vnum, "max": 1})
rooms['3032']['mob_resets'] = existing_resets

# Pet shop sells pets by gold cost on the mob itself - check how pet purchase works
# The traditional CircleMUD pet shop: room N is the shop, room N+1 has the pets
# Player types "buy <pet>" and it clones from N+1
# We need to check if this is implemented...

# ============================================================
# INNKEEPER FOR RENT - vnum 3005 (receptionist) already exists at room 3008
# ============================================================

# Update receptionist to be the innkeeper
mobs['3005']['special'] = 'innkeeper'
mobs['3005']['gold'] = 0  # doesn't need gold, collects rent

# ============================================================
# SAVE ZONE FILE
# ============================================================

with open(ZONE_FILE, 'w') as f:
    json.dump(zone, f, indent=2)

print("Zone file updated successfully!")
print(f"  Added {len(new_objects)} new objects")
print(f"  Added {len(new_pet_mobs)} new pet mobs")
print("  Updated 5 shopkeeper configs (wizard, baker, grocer, weaponsmith, armourer)")
print("  Configured pet shop boy as shopkeeper")
print("  Configured receptionist as innkeeper")
