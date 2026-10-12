"""The /play action bars are kept with the character, offline: `webbar` holds the main bar and the
three extra bars (40 slots), only abilities the character knows, each once.

    python3 tests/test_webbar.py
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
    from commands import CommandHandler
    from map_system import build_map_payload
    import test_atlas_engine as tae
    world = World(Config())
    await world.load()
    h = Player.create_new(name='Barkeep', password=None, race='human', char_class='warrior',
                          stats={s: 13 for s in ('str', 'int', 'wis', 'dex', 'con', 'cha')}, world=world)
    h.connection = tae.Conn()
    h.room = world.rooms[3001]
    world.rooms[3001].characters.append(h)
    h.skills = {'bash': 60, 'kick': 55, 'rescue': 50}
    words = ['bash'] + ['-'] * 15 + ['kick', 'ghost', 'bash'] + ['-'] * 14 + ['-'] * 6 + ['rescue', 'extra']
    await CommandHandler.cmd_webbar(h, words)
    bar = h.web_bar
    check(len(bar) == CommandHandler.WEB_BAR_SLOTS == 40, f'the bars hold 40 slots ({len(bar)})')
    check(bar[0] == 'bash' and bar[16] == 'kick' and bar[39] == 'rescue', 'the main bar, bar 3 and bar 5 are kept where they were put')
    check(bar[17] is None and bar[18] is None, 'an unknown ability, and one already on a bar, are dropped')
    h.explored_rooms = {3001}
    check((build_map_payload(h).get('player') or {}).get('bar') == bar, 'the payload sends the bars back')
    await CommandHandler.cmd_webbar(h, ['kick'] * 60)
    check(len(h.web_bar) == 40 and h.web_bar.count('kick') == 1, 'more than 40 words: the rest are ignored')
    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    asyncio.run(main())
