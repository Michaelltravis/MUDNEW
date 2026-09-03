#!/usr/bin/env python3
"""Ability QA harness: boots the world in-process, builds one character per
class, and fires every spell and active skill at a training dummy. Reports
exceptions, silent no-ops and refusals so broken abilities can't hide.

Usage: python3 tools/test_abilities.py [class ...]
"""
import asyncio
import os
import sys
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import Config
from world import World
from player import Player
from mobs import Mobile
from commands import CommandHandler
from spells import SpellHandler, SPELLS

ARENA_VNUM = 3060          # Great Field: outdoors, no peaceful flag
LEVEL = 35

# passive skills: no command expected, exercised by the combat engine
PASSIVES = {
    'parry', 'dodge', 'second_attack', 'third_attack', 'shield_block',
    'dual_wield', 'enhanced_damage', 'fast_healing', 'meditation',
    'sneak', 'evasion', 'riposte', 'counter',
}
# skills whose command name differs from the skill id
SKILL_CMD = {
    'pick_lock': 'pick',
    'holy_smite': 'holysmite',
    'shadow_step': 'shadowstep',
    'first_aid': 'firstaid',
}
# skills that operate on self / no target
NO_TARGET = {
    'hide', 'meditate', 'berserk', 'war_cry', 'battle_focus', 'sing',
    'whirlwind', 'stance', 'camp', 'forage', 'track',
}

class Sink:
    def __init__(self):
        self.lines = []
    async def send(self, message, newline=True):
        self.lines.append(str(message))

async def build_player(world, cls_name):
    p = Player(world)
    p.name = f'Test{cls_name[:6].title()}'
    p.char_class = cls_name
    p.level = LEVEL
    p.connection = Sink()
    cfg = Config()
    cd = cfg.CLASSES[cls_name]
    p.max_hp = p.hp = 4000
    p.max_mana = p.mana = 9000
    p.max_move = p.move = 2000
    for st in ('str', 'dex', 'con', 'wis', 'int', 'cha'):
        setattr(p, st, 18)
    p.skills = {s: 95 for s in cd.get('skills', [])}
    p.spells = {s: 95 for s in cd.get('spells', [])}
    p.gold = 10000
    room = world.rooms[ARENA_VNUM]
    p.room = room
    room.characters.append(p)
    world.players[p.name.lower()] = p
    return p

def make_dummy(world, room):
    m = Mobile(99999, world)
    m.name = 'dummy'
    m.keywords = ['dummy']
    m.short_desc = 'a training dummy'
    m.long_desc = 'A training dummy stands here.'
    m.level = LEVEL
    m.max_hp = m.hp = 800000
    m.room = room
    room.characters.append(m)
    world.npcs.append(m)
    return m

def out_of(p):
    lines = p.connection.lines
    p.connection.lines = []
    return [l for l in lines if l.strip()]

REFUSAL = (
    "you don't know", "you can't", "huh?", "what?", "you fail to",
    "cast what", "use what", "not while", "you need", "requires",
    "no such", "nothing happens",
)

def classify(lines, exc):
    if exc:
        return 'EXC', exc
    if not lines:
        return 'SILENT', ''
    low = ' | '.join(lines).lower()
    for r in REFUSAL:
        if r in low:
            return 'REFUSED', lines[0][:90]
    return 'OK', lines[0][:70]

async def reset(p, dummy):
    p.hp = p.max_hp; p.mana = p.max_mana; p.move = p.max_move
    p.fighting = None
    p.affects = []
    p.position = 'standing'
    dummy.hp = dummy.max_hp
    dummy.fighting = None
    dummy.affects = []
    if dummy.room is None:        # spell may have killed/moved it
        dummy.room = p.room
        if dummy not in p.room.characters:
            p.room.characters.append(dummy)

async def run_class(world, cls_name, results):
    p = await build_player(world, cls_name)
    dummy = make_dummy(world, p.room)
    cfg = Config().CLASSES[cls_name]

    for spell in cfg.get('spells', []):
        await reset(p, dummy)
        info = SPELLS.get(spell, {})
        tgt = 'dummy' if info.get('target') in ('offensive', None) else None
        exc = None
        try:
            await asyncio.wait_for(SpellHandler.cast_spell(p, spell, tgt), 6)
        except Exception:
            exc = traceback.format_exc().strip().split('\n')[-1][:110]
        status, detail = classify(out_of(p), exc)
        if status in ('REFUSED',) and tgt:
            # retry self-targeted (some 'offensive' labels lie)
            await reset(p, dummy)
            exc = None
            try:
                await asyncio.wait_for(SpellHandler.cast_spell(p, spell, None), 6)
            except Exception:
                exc = traceback.format_exc().strip().split('\n')[-1][:110]
            s2, d2 = classify(out_of(p), exc)
            if s2 == 'OK':
                status, detail = s2, d2
        results.append((cls_name, 'spell', spell, status, detail))

    for skill in cfg.get('skills', []):
        if skill in PASSIVES:
            results.append((cls_name, 'skill', skill, 'PASSIVE', ''))
            continue
        cmd = SKILL_CMD.get(skill, skill)
        parts = cmd.split('_')
        cmd_word = parts[0] if len(parts) > 1 and not hasattr(CommandHandler, f'cmd_{cmd}') else cmd
        attempts = []
        if skill in NO_TARGET:
            attempts = [(cmd_word, [])]
        else:
            attempts = [(cmd_word, ['dummy']), (cmd_word, [])]
        best = None
        for (cw, args) in attempts:
            await reset(p, dummy)
            # combat skills usually need a fight going
            p.fighting = dummy
            dummy.fighting = p
            exc = None
            try:
                await asyncio.wait_for(CommandHandler.execute(p, cw, args), 6)
            except Exception:
                exc = traceback.format_exc().strip().split('\n')[-1][:110]
            status, detail = classify(out_of(p), exc)
            best = (status, detail) if best is None or status == 'OK' else best
            if status == 'OK':
                break
        results.append((cls_name, 'skill', skill, best[0], best[1]))

    # cleanup
    p.room.characters.remove(p)
    if dummy in p.room.characters:
        p.room.characters.remove(dummy)
    if dummy in world.npcs:
        world.npcs.remove(dummy)
    world.players.pop(p.name.lower(), None)

async def main():
    # cast lag must not slow 219 abilities: stub the module-level sleeps
    real_sleep = asyncio.sleep
    async def fast_sleep(t, *a, **k):
        await real_sleep(min(t, 0.01))
    asyncio.sleep = fast_sleep

    world = World(Config())
    await world.load()

    classes = sys.argv[1:] or list(Config().CLASSES.keys())
    results = []
    for cls_name in classes:
        await run_class(world, cls_name, results)

    by = {}
    for cls_name, kind, name, status, detail in results:
        by.setdefault(status, []).append((cls_name, kind, name, detail))
    print('\n========== SUMMARY ==========')
    for status in ('EXC', 'SILENT', 'REFUSED', 'OK', 'PASSIVE'):
        print(f'{status:8s}: {len(by.get(status, []))}')
    for status in ('EXC', 'SILENT', 'REFUSED'):
        if by.get(status):
            print(f'\n---- {status} ----')
            for cls_name, kind, name, detail in by[status]:
                print(f'  [{cls_name:11s}] {kind:5s} {name:24s} {detail}')

asyncio.run(main())
