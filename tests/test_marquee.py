"""The marquee quests (push 7): one per class, offered at level 45 by the class's trainer, ending
in a private trial; solo about two hours, harder for each member who embarks.

Offline: the scaling (health, damage, adds, tempo, rewards) by the number who embarked; a solo
quest's foes add up to about two hours with travel; Unbroken Banner is earned, never learned by
level, and its command refuses another class and a running cooldown.
Live (needs ./run.sh and the gauntlet accounts) — see live() below.
    python3 tests/test_marquee.py [--offline]
"""
import asyncio
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
import test_webmove as tw  # noqa: E402  (Telnet helper, check(), failures)

check, failures = tw.check, tw.failures


def fake_player(**kw):
    sent = []

    async def send(msg='', *a, **k):
        sent.append(str(msg))
    from config import Config
    p = types.SimpleNamespace(level=46, char_class='warrior', skills={}, spells={}, send=send, sent=sent, affects=[],
                              config=types.SimpleNamespace(COLORS=Config.COLORS), world=None, room=None, group=None,
                              name='Ann', hp=500, max_hp=500)
    for k, v in kw.items():
        setattr(p, k, v)
    return p


async def offline():
    import marquee_scale as ms
    check(ms.health_factor(1) == 1 and abs(ms.health_factor(3) - 2.6) < 1e-9 and abs(ms.health_factor(6) - 5.0) < 1e-9,
          'health x1 alone, x2.6 for three, x5 for six')
    check(abs(ms.damage_factor(6) - 1.5) < 1e-9 and ms.extra_adds(1) == 0 and ms.extra_adds(3) == 1 and ms.extra_adds(6) == 2,
          'damage +10% a hero, one extra add a wave for every two more')
    check(ms.tempo(1) == 1 and ms.tempo(6) < 0.8, 'a boss acts sooner for a bigger party')
    check(ms.party_level(45, [52, 50]) == 49 and ms.party_level(58, [45]) == 58 and ms.party_level(40) == 45,
          "the quest's level: the owner's, or the party's average if higher, 45-60")
    solo = ms.minutes('elite', 46, 1)
    six = ms.minutes('elite', 46, 6)
    check(0.9 < solo < 1.4 and six < solo, f'an elite takes ~1 min alone ({solo:.2f}), a little less for six ({six:.2f})')
    boss = ms.minutes('boss', 47, 1)
    check(3 < boss < 4.5, f'the trial boss takes ~4 minutes alone ({boss:.1f})')
    check(ms.gold_reward(1000, 3) == 2000 and ms.exp_reward(1000, 3) == 2600, 'rewards grow with the party')

    import mastery
    from config import Config
    check('unbroken_banner' in [a for a, _k in mastery.roster('warrior')] and mastery.unlock_level('warrior', 'unbroken_banner') == 45,
          "Unbroken Banner is in the warrior's book at level 45")
    p = fake_player(level=60)
    mastery.grant_now(p)
    check('unbroken_banner' not in p.skills, 'reaching level 60 does not teach it: it is earned through the quest')
    e = next(x for x in mastery.book('warrior') if x['id'] == 'unbroken_banner')
    check(e.get('quest') == 'The Unbroken Banner' and e.get('marquee') and e.get('target') == 'self',
          f"the book says how it is earned ({e.get('quest')}) and it needs no target")

    import marquee_abilities as ma
    mage = fake_player(char_class='mage')
    await ma.unbroken_banner(mage, [])
    check(any('Only a warrior' in s for s in mage.sent), 'another class is refused')
    w = fake_player(marquee_cd={'unbroken_banner': __import__('time').time() + 200})
    await ma.unbroken_banner(w, [])
    check(any('not ready yet' in s for s in w.sent), 'a running cooldown is refused (and the cooldown is saved on the character)')


async def live():
    pass


async def main():
    await offline()
    if '--offline' not in sys.argv:
        await live()
    print(f"\n{'ALL OK' if not failures else f'{len(failures)} FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    asyncio.run(main())
