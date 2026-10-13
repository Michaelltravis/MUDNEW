"""Male or female, offline: asked at creation (telnet, and the 3D client's wizard answers the same
prompt), kept with the character, sent in the look (the 3D face and build, gearlook.js), and
chosen once by a character made before it was asked (`gender`).

    python3 tests/test_gender.py
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
    from server import Connection
    from commands import CommandHandler
    import gear_look
    import test_atlas_engine as tae
    world = World(Config())
    await world.load()

    # ---- creation: race, then male or female, then class
    conn = Connection.__new__(Connection)
    conn.config, conn.world, conn.account, conn.player = world.config, world, None, None
    conn.temp_name, conn.temp_password, conn.temp_race, conn.temp_sex, conn.temp_class = 'Wren', None, None, None, None
    out = []

    async def send(message='', newline=True):
        out.append(str(message))
    conn.send = send
    conn.state = conn.STATE_GET_RACE
    await conn.handle_input('elf')
    check(conn.state == conn.STATE_GET_SEX and 'male or female' in ' '.join(out[-3:]).lower(), 'after the race: male or female?')
    out.clear()
    await conn.handle_input('dunno')
    check(conn.state == conn.STATE_GET_SEX and 'male or female' in ' '.join(out).lower(), 'anything else asks again')
    await conn.handle_input('2')
    check(conn.temp_sex == 'female' and conn.state == conn.STATE_GET_CLASS, 'then the class (2 is female)')
    await conn.handle_input('ranger')
    check(conn.state == conn.STATE_ROLLING_STATS, 'and the stats')

    # ---- kept with the character, and in the look
    wren = Player.create_new(name='Wren', password=None, race='elf', char_class='ranger', world=world,
                             stats={s: 13 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, sex=conn.temp_sex)
    await wren.save()
    back = Player.load('Wren', world)
    check(back is not None and back.sex == 'female', f'saved and loaded ({getattr(back, "sex", None)})')
    look = gear_look.look_of(back)
    check(look.get('sex') == 'female', 'the look carries it (the 3D face and build)')
    odd = Player.create_new(name='Odd', password=None, race='human', char_class='mage', world=world,
                            stats={s: 13 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, sex='robot')
    check(odd.sex == 'neutral' and 'sex' not in gear_look.look_of(odd), 'anything but male or female is unsaid')

    # ---- a character made before it was asked chooses once
    old = Player.create_new(name='Elder', password=None, race='dwarf', char_class='warrior', world=world,
                            stats={s: 13 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')})
    old.connection = tae.Conn()
    old.room = world.rooms.get(3001)
    sig = gear_look.look_of(old)['sig']
    await CommandHandler.cmd_gender(old, [])
    check(old.sex == 'neutral' and 'not said' in tae.said(old, 1), 'an older character has not said')
    await CommandHandler.cmd_gender(old, ['male'])
    check(old.sex == 'male' and gear_look.look_of(old)['sig'] != sig, 'gender male: chosen, and the look changes')
    await CommandHandler.cmd_gender(old, ['female'])
    check(old.sex == 'male', 'once only')
    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    asyncio.run(main())
