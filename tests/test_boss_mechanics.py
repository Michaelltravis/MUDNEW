"""The Castle of the Apocalypse's boss fights, offline (src/boss_mechanics.py).

    python3 tests/test_boss_mechanics.py

Pestilence drops plague pools (standing in one sickens you; stepping out spares you); War calls
the castle's guards at 75% and 40%; Famine starves whoever stands still; Death raises servants
at 75/50/25% and the room darkens as he weakens (the 3D client is told how dark).
"""
import asyncio
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
import test_webmove as tw  # noqa: E402

check, failures = tw.check, tw.failures


async def main():
    import logging
    logging.disable(logging.WARNING)
    from config import Config
    Config.PLAYER_DIR = tempfile.mkdtemp()
    from world import World
    from player import Player
    import combat_events
    import combat_range as cr
    import test_atlas_engine as tae
    world = World(Config())
    await world.load()
    events = []
    real_emit = combat_events.emit
    combat_events.emit = lambda room, k, src=None, dst=None, **f: events.append((k, f)) or None

    def boss_of(vnum):
        return next(m for m in world.npcs if getattr(m, 'vnum', None) == vnum)

    def hero(name, room):
        h = Player.create_new(name=name, password=None, race='human', char_class='warrior',
                              stats={s: 13 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
        h.connection = tae.Conn()
        h.room = room
        room.characters.append(h)
        h.level = 60
        h.max_hp = h.hp = 20000
        h.max_move = h.move = 500
        return h

    def fight(b, h):
        b.fighting, h.fighting = h, b
        b.position = h.position = 'fighting'

    # ---- Pestilence: a pool where you stand; out of it, you are spared
    pest = boss_of(22070)
    check([m.spec['type'] for m in pest.mechanics] == ['plague_pools'], 'Pestilence has her plague pools')
    a, b = hero('Stander', pest.room), hero('Mover', pest.room)
    cr.set_pos(a, 5, 5)
    cr.set_pos(b, 15, 10)
    fight(pest, a)
    pools = pest.mechanics[0]
    pools.reset(pest)
    import random
    real = random.choice
    random.choice = lambda seq: a if a in seq else real(seq)
    await pools.tick(pest, 100.0)
    random.choice = real
    check(any(k == 'hazard' and f.get('area', {}).get('x') == 5 for k, f in events), 'a pool is marked where Stander stands (the 3D client draws it)')
    hp_a, hp_b = a.hp, b.hp
    await pools.tick(pest, 103.0)
    check(a.hp < hp_a and b.hp == hp_b, f'standing in it burns; out of it, nothing ({hp_a - a.hp}, {hp_b - b.hp})')
    cr.set_pos(a, 12, 12)
    hp_a = a.hp
    await pools.tick(pest, 106.0)
    check(a.hp == hp_a, 'stepping out of it spares you')
    await pools.tick(pest, 140.0)
    check(not [p for p in pools.pools if p['x'] == 5], 'and a pool dries up in time (new ones keep coming)')

    # ---- War: the castle's guards come at 75% and 40%
    war = boss_of(22071)
    w = hero('Duelist', war.room)
    fight(war, w)
    guards = war.mechanics[0]
    guards.reset(war)
    before = len([c for c in war.room.characters if not hasattr(c, 'connection')])
    war.hp = int(war.max_hp * 0.7)
    await guards.tick(war, 0)
    after = [c for c in war.room.characters if not hasattr(c, 'connection') and c is not war]
    check(len(after) >= before and any(getattr(c, 'fighting', None) is w for c in after),
          f'at 70%: guards rush in and fight ({len(after)} at his side)')
    n = len(after)
    await guards.tick(war, 0)
    check(len([c for c in war.room.characters if not hasattr(c, 'connection') and c is not war]) == n, 'once per threshold')
    war.hp = int(war.max_hp * 0.3)
    await guards.tick(war, 0)
    check(len([c for c in war.room.characters if not hasattr(c, 'connection') and c is not war]) > n, 'and again at 40%')

    # ---- Famine: standing still starves; moving spares
    fam = boss_of(22072)
    s1, s2 = hero('Statue', fam.room), hero('Dancer', fam.room)
    cr.set_pos(s1, 6, 6)
    cr.set_pos(s2, 8, 8)
    fight(fam, s1)
    hunger = fam.mechanics[0]
    hunger.reset(fam)
    await hunger.tick(fam, 10.0)
    hp1, hp2, mv1 = s1.hp, s2.hp, s1.move
    cr.set_pos(s2, 12, 9)
    await hunger.tick(fam, 14.0)
    check(s1.hp < hp1 and s1.move < mv1, f'standing still starves you ({hp1 - s1.hp} health, {mv1 - s1.move} stamina)')
    check(s2.hp == hp2, 'moving spares you')

    # ---- Death: waves of servants; the room darkens
    death = boss_of(22073)
    d = hero('Reaper', death.room)
    fight(death, d)
    waves, gloom = death.mechanics
    waves.reset(death)
    gloom.reset(death)
    events.clear()
    count = lambda: len([c for c in death.room.characters if getattr(c, 'vnum', None) == 22040])
    c0 = count()
    death.hp = int(death.max_hp * 0.7)
    await waves.tick(death, 0)
    await gloom.tick(death, 0)
    check(count() == c0 + 2, f'at 70%: a wave of two servants ({count() - c0})')
    death.hp = int(death.max_hp * 0.2)
    await waves.tick(death, 0)
    await gloom.tick(death, 0)
    check(count() == c0 + 6, f'at 20%: two more waves ({count() - c0})')
    levels = [f['level'] for k, f in events if k == 'gloom']
    check(levels and levels == sorted(levels) and levels[-1] >= 0.6, f'the room darkens as he weakens ({levels})')
    gloom.reset(death)
    check(events[-1][0] == 'gloom' and events[-1][1]['level'] == 0, 'and the light returns when the fight ends')
    combat_events.emit = real_emit
    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    asyncio.run(main())
