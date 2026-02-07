"""
Crafting System

Provides gathering and crafting skills with recipes and materials.
"""

import logging
import random
from dataclasses import dataclass
from typing import Dict, Optional, Any

from objects import Object

logger = logging.getLogger(__name__)

GATHERING_SKILLS = ['mining', 'herbalism', 'skinning']
CRAFTING_SKILLS = ['blacksmithing', 'alchemy', 'leatherworking']


@dataclass
class Recipe:
    """Defines a crafting recipe."""
    recipe_id: str
    name: str
    skill: str
    skill_required: int
    ingredients: Dict[str, int]  # material_id -> count
    output: Dict[str, Any]  # object definition
    exp_reward: int = 0


MATERIALS = {
    'copper_ore': {
        'vnum': 9001,
        'name': 'copper ore',
        'short_desc': 'a chunk of copper ore',
        'room_desc': 'A chunk of copper ore lies here.',
        'description': 'A rough chunk of copper ore, ready to be smelted.',
        'item_type': 'material',
        'weight': 2,
        'cost': 5,
    },
    'iron_ore': {
        'vnum': 9002,
        'name': 'iron ore',
        'short_desc': 'a chunk of iron ore',
        'room_desc': 'A chunk of iron ore lies here.',
        'description': 'A heavy chunk of iron ore.',
        'item_type': 'material',
        'weight': 3,
        'cost': 8,
    },
    'silver_ore': {
        'vnum': 9003,
        'name': 'silver ore',
        'short_desc': 'a nugget of silver ore',
        'room_desc': 'A nugget of silver ore glints here.',
        'description': 'A shimmering nugget of silver ore.',
        'item_type': 'material',
        'weight': 2,
        'cost': 12,
    },
    'healing_herb': {
        'vnum': 9004,
        'name': 'healing herb',
        'short_desc': 'a bundle of healing herbs',
        'room_desc': 'A bundle of healing herbs lies here.',
        'description': 'A fragrant bundle of herbs used in healing remedies.',
        'item_type': 'material',
        'weight': 1,
        'cost': 6,
    },
    'mana_leaf': {
        'vnum': 9005,
        'name': 'mana leaf',
        'short_desc': 'a shimmering mana leaf',
        'room_desc': 'A shimmering leaf rests on the ground.',
        'description': 'A leaf that hums faintly with magical energy.',
        'item_type': 'material',
        'weight': 1,
        'cost': 10,
    },
    'sturdy_hide': {
        'vnum': 9006,
        'name': 'sturdy hide',
        'short_desc': 'a sturdy animal hide',
        'room_desc': 'A sturdy animal hide lies here.',
        'description': 'A thick hide suitable for leatherworking.',
        'item_type': 'material',
        'weight': 3,
        'cost': 9,
    },
    'thick_hide': {
        'vnum': 9007,
        'name': 'thick hide',
        'short_desc': 'a thick animal hide',
        'room_desc': 'A thick animal hide lies here.',
        'description': 'A heavy hide from a large beast.',
        'item_type': 'material',
        'weight': 4,
        'cost': 12,
    },
}


RECIPES = {
    'copper_dagger': Recipe(
        recipe_id='copper_dagger',
        name='Copper Dagger',
        skill='blacksmithing',
        skill_required=5,
        ingredients={'copper_ore': 2, 'iron_ore': 1},
        output={
            'vnum': 9101,
            'name': 'copper dagger',
            'short_desc': 'a copper dagger',
            'room_desc': 'A copper dagger has been left here.',
            'description': 'A simple dagger forged from copper and iron.',
            'item_type': 'weapon',
            'weapon_type': 'pierce',
            'damage_dice': '1d4',
            'weight': 2,
            'cost': 25,
        },
        exp_reward=50,
    ),
    'healing_potion': Recipe(
        recipe_id='healing_potion',
        name='Minor Healing Potion',
        skill='alchemy',
        skill_required=5,
        ingredients={'healing_herb': 2, 'mana_leaf': 1},
        output={
            'vnum': 9102,
            'name': 'minor healing potion',
            'short_desc': 'a minor healing potion',
            'room_desc': 'A small vial of red liquid rests here.',
            'description': 'A potion brewed to mend minor wounds.',
            'item_type': 'potion',
            'weight': 1,
            'cost': 35,
        },
        exp_reward=60,
    ),
    'leather_vest': Recipe(
        recipe_id='leather_vest',
        name='Leather Vest',
        skill='leatherworking',
        skill_required=5,
        ingredients={'sturdy_hide': 2, 'thick_hide': 1},
        output={
            'vnum': 9103,
            'name': 'leather vest',
            'short_desc': 'a leather vest',
            'room_desc': 'A leather vest lies here.',
            'description': 'A reinforced leather vest for basic protection.',
            'item_type': 'armor',
            'armor': 8,
            'wear_slot': 'body',
            'weight': 4,
            'cost': 45,
        },
        exp_reward=70,
    ),
}


def _ensure_skill(player, skill_name: str):
    if skill_name not in player.skills:
        player.skills[skill_name] = 1


def _create_object_from_def(obj_def: Dict[str, Any], world=None) -> Object:
    obj = Object(obj_def.get('vnum', 0), world)
    obj.name = obj_def.get('name', obj.name)
    obj.short_desc = obj_def.get('short_desc', obj.short_desc)
    obj.room_desc = obj_def.get('room_desc', obj.room_desc)
    obj.description = obj_def.get('description', obj.description)
    obj.item_type = obj_def.get('item_type', obj.item_type)
    obj.wear_slot = obj_def.get('wear_slot', obj.wear_slot)
    obj.weight = obj_def.get('weight', obj.weight)
    obj.cost = obj_def.get('cost', obj.cost)
    obj.damage_dice = obj_def.get('damage_dice', obj.damage_dice)
    obj.weapon_type = obj_def.get('weapon_type', obj.weapon_type)
    obj.armor = obj_def.get('armor', obj.armor)
    obj.food_value = obj_def.get('food_value', obj.food_value)
    obj.drinks = obj_def.get('drinks', obj.drinks)
    obj.liquid = obj_def.get('liquid', obj.liquid)
    return obj


def create_material(material_id: str, world=None) -> Optional[Object]:
    material_def = MATERIALS.get(material_id)
    if not material_def:
        return None
    obj = _create_object_from_def(material_def, world)
    obj.material_id = material_id
    return obj


def create_crafted_item(recipe: Recipe, world=None) -> Object:
    obj = _create_object_from_def(recipe.output, world)
    obj.crafted_from = recipe.recipe_id
    return obj


def list_recipes() -> Dict[str, Recipe]:
    return RECIPES


def _count_materials(player, material_id: str) -> int:
    count = 0
    for item in player.inventory:
        if getattr(item, 'material_id', None) == material_id:
            count += 1
        elif material_id.replace('_', ' ') in item.name.lower():
            count += 1
    return count


def _consume_materials(player, material_id: str, amount: int):
    removed = 0
    for item in list(player.inventory):
        if removed >= amount:
            break
        if getattr(item, 'material_id', None) == material_id or material_id.replace('_', ' ') in item.name.lower():
            player.inventory.remove(item)
            removed += 1


def _skill_check(skill_level: int, base: int = 40) -> bool:
    chance = min(95, base + skill_level)
    roll = random.randint(1, 100)
    return roll <= chance


async def gather(player):
    """Gather materials based on environment or available corpses."""
    if not player.room:
        await player.send("You are nowhere and cannot gather anything.")
        return

    c = player.config.COLORS
    sector = player.room.sector_type

    # Skinning requires a corpse in the room
    corpse = None
    for item in player.room.items:
        if getattr(item, 'item_type', None) == 'container' and 'corpse' in item.name.lower():
            if not getattr(item, 'skinned', False):
                corpse = item
                break

    if corpse:
        skill = 'skinning'
        _ensure_skill(player, skill)
        success = _skill_check(player.skills.get(skill, 0), base=35)
        if success:
            material_id = random.choice(['sturdy_hide', 'thick_hide'])
            material = create_material(material_id, player.world)
            if material:
                player.inventory.append(material)
                corpse.skinned = True
                await player.send(f"{c['bright_cyan']}You skin {corpse.short_desc} and obtain {material.short_desc}.{c['reset']}")
                from quests import QuestManager
                await QuestManager.check_quest_progress(
                    player, 'collect', {'item_vnum': material.vnum, 'item_name': material.name}
                )
                await player.improve_skill(skill, difficulty=5)
        else:
            await player.send(f"{c['yellow']}You fail to properly skin the corpse.{c['reset']}")
        return

    # No corpse: check terrain for mining/herbalism
    if sector in ['mountain', 'hills', 'dungeon']:
        skill = 'mining'
        options = ['copper_ore', 'iron_ore', 'silver_ore']
    elif sector in ['forest', 'field', 'swamp']:
        skill = 'herbalism'
        options = ['healing_herb', 'mana_leaf']
    else:
        await player.send(f"{c['yellow']}You can't find anything to gather here.{c['reset']}")
        return

    _ensure_skill(player, skill)
    success = _skill_check(player.skills.get(skill, 0), base=40)
    if success:
        material_id = random.choice(options)
        material = create_material(material_id, player.world)
        if material:
            player.inventory.append(material)
            await player.send(f"{c['bright_cyan']}You gather {material.short_desc}.{c['reset']}")
            from quests import QuestManager
            await QuestManager.check_quest_progress(
                player, 'collect', {'item_vnum': material.vnum, 'item_name': material.name}
            )
            await player.improve_skill(skill, difficulty=4)
    else:
        await player.send(f"{c['yellow']}You search for a while but find nothing useful.{c['reset']}")


async def craft(player, recipe_id: str):
    """Craft an item from a recipe."""
    recipe = RECIPES.get(recipe_id)
    c = player.config.COLORS

    if not recipe:
        await player.send(f"{c['yellow']}Unknown recipe '{recipe_id}'.{c['reset']}")
        return

    _ensure_skill(player, recipe.skill)
    skill_level = player.skills.get(recipe.skill, 0)

    if skill_level < recipe.skill_required:
        await player.send(f"{c['yellow']}Your {recipe.skill} skill is too low to craft this recipe.{c['reset']}")
        return

    # Check ingredients
    missing = []
    for material_id, amount in recipe.ingredients.items():
        if _count_materials(player, material_id) < amount:
            missing.append(f"{amount}x {material_id.replace('_', ' ')}")

    if missing:
        await player.send(f"{c['yellow']}You lack the required materials: {', '.join(missing)}.{c['reset']}")
        return

    # Attempt craft
    success = _skill_check(skill_level, base=45)

    # Consume materials
    for material_id, amount in recipe.ingredients.items():
        _consume_materials(player, material_id, amount)

    if success:
        item = create_crafted_item(recipe, player.world)
        player.inventory.append(item)
        await player.send(f"{c['bright_green']}You craft {item.short_desc}!{c['reset']}")
        if recipe.exp_reward:
            player.exp += recipe.exp_reward
            await player.send(f"{c['bright_yellow']}You gain {recipe.exp_reward} experience.{c['reset']}")
        await player.improve_skill(recipe.skill, difficulty=6)
    else:
        await player.send(f"{c['red']}Your crafting attempt fails, wasting the materials.{c['reset']}")

    logger.info(f"{player.name} attempted recipe {recipe_id} (success={success})")
