"""
RealmsMUD Puzzle System
=======================
Room-based puzzles: riddles, levers, symbol matching, environmental sequences.
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger('RealmsMUD.Puzzles')


class PuzzleManager:
    """Utilities for handling room puzzles."""

    @staticmethod
    def _ensure_player_fields(player):
        if not hasattr(player, 'puzzle_state') or player.puzzle_state is None:
            player.puzzle_state = {}

    @staticmethod
    def room_puzzles(room) -> List[dict]:
        if not room:
            return []
        return list(getattr(room, 'puzzles', []) or [])

    @staticmethod
    def get_state(player, puzzle_id: str) -> dict:
        PuzzleManager._ensure_player_fields(player)
        state = player.puzzle_state.get(puzzle_id)
        if state is None:
            state = {'solved': False, 'progress': []}
            player.puzzle_state[puzzle_id] = state
        return state

    @staticmethod
    def is_solved(player, puzzle_id: str) -> bool:
        state = PuzzleManager.get_state(player, puzzle_id)
        return bool(state.get('solved'))

    @staticmethod
    def get_prompt(puzzle: dict) -> Optional[str]:
        return puzzle.get('prompt') or puzzle.get('question') or puzzle.get('description')

    @staticmethod
    def _find_unsolved_puzzles(player, room, puzzle_type: Optional[str] = None) -> List[dict]:
        puzzles = []
        for puzzle in PuzzleManager.room_puzzles(room):
            if puzzle_type and puzzle.get('type') != puzzle_type:
                continue
            if not PuzzleManager.is_solved(player, puzzle.get('id')):
                puzzles.append(puzzle)
        return puzzles

    @staticmethod
    async def _apply_hint_cost(player, puzzle: dict) -> bool:
        c = player.config.COLORS
        cost = puzzle.get('hint_cost') or {}
        gold_cost = cost.get('gold', 0)
        move_cost = cost.get('move', cost.get('time', 0))

        if gold_cost and player.gold < gold_cost:
            await player.send(f"{c['red']}You need {gold_cost} gold for a hint.{c['reset']}")
            return False
        if move_cost and player.move < move_cost:
            await player.send(f"{c['red']}You are too exhausted to focus for a hint.{c['reset']}")
            return False

        if gold_cost:
            player.gold -= gold_cost
        if move_cost:
            player.move = max(0, player.move - move_cost)
        return True

    @staticmethod
    async def request_hint(player) -> bool:
        """Provide a hint for the first unsolved puzzle in the room."""
        if not player.room:
            await player.send("You are nowhere!")
            return False

        puzzles = PuzzleManager._find_unsolved_puzzles(player, player.room)
        if not puzzles:
            await player.send("There is nothing here that needs a hint.")
            return False

        puzzle = puzzles[0]
        hint = puzzle.get('hint')
        if not hint:
            await player.send("No hints are available for that puzzle.")
            return False

        if not await PuzzleManager._apply_hint_cost(player, puzzle):
            return False

        c = player.config.COLORS
        await player.send(f"{c['bright_cyan']}Hint:{c['reset']} {hint}")
        return True

    @staticmethod
    async def handle_answer(player, text: str) -> bool:
        """Handle answering a riddle puzzle in the room."""
        if not player.room:
            await player.send("You are nowhere!")
            return False

        puzzles = PuzzleManager._find_unsolved_puzzles(player, player.room, 'riddle')
        if not puzzles:
            await player.send("There is no riddle to answer here.")
            return False

        puzzle = puzzles[0]
        answers = [a.lower().strip() for a in puzzle.get('answers', [])]
        response = text.lower().strip()
        if response in answers:
            await PuzzleManager.solve(player, puzzle)
            return True

        c = player.config.COLORS
        await player.send(f"{c['yellow']}That doesn't seem to be correct.{c['reset']}")
        return False

    @staticmethod
    async def handle_pull(player, lever_name: str) -> bool:
        """Handle pulling a lever for lever puzzles."""
        if not player.room:
            await player.send("You are nowhere!")
            return False

        lever_name = lever_name.lower().strip()
        puzzles = PuzzleManager._find_unsolved_puzzles(player, player.room, 'lever')
        if not puzzles:
            await player.send("There are no levers to pull here.")
            return False

        for puzzle in puzzles:
            levers = [l.lower() for l in puzzle.get('levers', [])]
            if lever_name not in levers:
                continue

            sequence = [s.lower() for s in puzzle.get('sequence', [])]
            state = PuzzleManager.get_state(player, puzzle.get('id'))
            progress = state.get('progress', [])
            progress.append(lever_name)
            state['progress'] = progress

            if sequence[:len(progress)] != progress:
                state['progress'] = []
                c = player.config.COLORS
                await player.send(f"{c['red']}A grinding sound resets the mechanism.{c['reset']}")
                return True

            if len(progress) == len(sequence):
                await PuzzleManager.solve(player, puzzle)
                return True

            c = player.config.COLORS
            await player.send(f"{c['cyan']}You hear distant clicks as the mechanism aligns.{c['reset']}")
            return True

        await player.send("That lever doesn't seem to do anything.")
        return False

    @staticmethod
    async def handle_push(player, obj_name: str) -> bool:
        """Handle pushing symbols or environmental objects."""
        if not player.room:
            await player.send("You are nowhere!")
            return False

        obj_name = obj_name.lower().strip()
        puzzles = PuzzleManager._find_unsolved_puzzles(player, player.room)
        if not puzzles:
            await player.send("There is nothing here to push like that.")
            return False

        for puzzle in puzzles:
            if puzzle.get('type') not in ('symbols', 'environmental'):
                continue

            targets = puzzle.get('symbols') or puzzle.get('objects') or []
            targets = [t.lower() for t in targets]
            if obj_name not in targets:
                continue

            sequence = [s.lower() for s in puzzle.get('sequence', targets)]
            state = PuzzleManager.get_state(player, puzzle.get('id'))
            progress = state.get('progress', [])
            progress.append(obj_name)
            state['progress'] = progress

            if sequence[:len(progress)] != progress:
                state['progress'] = []
                c = player.config.COLORS
                await player.send(f"{c['red']}The mechanism resets with a dull thud.{c['reset']}")
                return True

            if len(progress) == len(sequence):
                await PuzzleManager.solve(player, puzzle)
                return True

            c = player.config.COLORS
            await player.send(f"{c['cyan']}Something shifts within the walls.{c['reset']}")
            return True

        await player.send("That doesn't seem to be part of any mechanism.")
        return False

    @staticmethod
    async def solve(player, puzzle: dict):
        """Mark a puzzle solved and apply rewards."""
        puzzle_id = puzzle.get('id')
        if not puzzle_id:
            return

        state = PuzzleManager.get_state(player, puzzle_id)
        if state.get('solved'):
            return
        state['solved'] = True
        state['progress'] = []

        c = player.config.COLORS
        await player.send(f"{c['bright_green']}You solve the puzzle!{c['reset']}")

        await PuzzleManager._apply_rewards(player, puzzle)

    @staticmethod
    async def _apply_rewards(player, puzzle: dict):
        room = player.room
        reward = puzzle.get('reward') or {}
        if not reward or not room:
            return

        # Reveal hidden exit for this player
        reveal_exit = reward.get('reveal_exit')
        if reveal_exit:
            direction = reveal_exit.get('direction')
            if direction and room.exits.get(direction):
                if hasattr(player, 'discovered_exits'):
                    player.discovered_exits.add((room.vnum, direction))
                message = reveal_exit.get('message') or f"A hidden way opens to the {direction}!"
                await player.send(message)

        # Grant gold
        gold = reward.get('gold')
        if gold:
            player.gold += gold
            await player.send(f"You receive {gold} gold.")

        # Grant item
        item_vnum = reward.get('item_vnum')
        if item_vnum:
            from objects import create_object, create_preset_object
            obj = create_object(item_vnum, player.world) or create_preset_object(item_vnum)
            if obj:
                player.inventory.append(obj)
                await player.send(f"You receive {obj.short_desc}.")
                from collection_system import CollectionManager
                await CollectionManager.record_item(player, obj)

        # Grant experience
        exp = reward.get('exp')
        if exp:
            player.exp += exp
            await player.send(f"You gain {exp} experience.")

        # Set flag
        flag = reward.get('flag')
        if flag:
            player.flags.add(flag)

    @staticmethod
    async def announce_room_puzzles(player):
        """Show puzzle prompts when entering a room."""
        if not player.room:
            return

        puzzles = PuzzleManager._find_unsolved_puzzles(player, player.room)
        if not puzzles:
            return

        c = player.config.COLORS
        for puzzle in puzzles:
            prompt = PuzzleManager.get_prompt(puzzle)
            if prompt:
                await player.send(f"{c['bright_magenta']}{prompt}{c['reset']}")

    @staticmethod
    def seed_world(world):
        """Attach default puzzle definitions to rooms."""
        for vnum, puzzles in DEFAULT_PUZZLES.items():
            room = world.get_room(vnum)
            if not room:
                continue
            if not hasattr(room, 'puzzles') or room.puzzles is None:
                room.puzzles = []
            # Avoid duplicate seeds
            existing_ids = {p.get('id') for p in room.puzzles}
            for puzzle in puzzles:
                if puzzle.get('id') not in existing_ids:
                    room.puzzles.append(puzzle)


DEFAULT_PUZZLES = {
    3000: [
        {
            'id': 'midgaard_echo_gate',
            'type': 'riddle',
            'prompt': 'A stone plaque asks: "I speak without a mouth and hear without ears. What am I?"',
            'question': 'I speak without a mouth and hear without ears. What am I?',
            'answers': ['echo', 'an echo'],
            'hint': 'It answers when you call out in a canyon.',
            'hint_cost': {'gold': 25},
            'reward': {
                'reveal_exit': {
                    'direction': 'north',
                    'message': 'The plaque slides aside, revealing a passage to the north.'
                },
                'gold': 50
            }
        }
    ],
    3005: [
        {
            'id': 'midgaard_lever_triad',
            'type': 'lever',
            'prompt': 'Three levers jut from the wall, each etched with a metal sigil.',
            'levers': ['bronze', 'silver', 'gold'],
            'sequence': ['bronze', 'silver', 'gold'],
            'hint': 'The metals rise in value.',
            'hint_cost': {'move': 3},
            'reward': {
                'reveal_exit': {
                    'direction': 'down',
                    'message': 'The floor grinds open, revealing a descent.'
                },
                'item_vnum': 9300
            }
        }
    ],
    3014: [
        {
            'id': 'midgaard_symbol_night',
            'type': 'symbols',
            'prompt': 'A ring of symbols glows faintly on the wall.',
            'symbols': ['sun', 'moon', 'star'],
            'sequence': ['sun', 'moon', 'star'],
            'hint': 'Day gives way to night, then the heavens.',
            'hint_cost': {'gold': 30},
            'reward': {
                'reveal_exit': {
                    'direction': 'west',
                    'message': 'A hidden passage opens to the west.'
                },
                'gold': 75
            }
        }
    ],
    3040: [
        {
            'id': 'midgaard_torch_trial',
            'type': 'environmental',
            'prompt': 'Cold braziers and a heavy statue suggest a ritual sequence.',
            'objects': ['statue', 'torch', 'altar'],
            'sequence': ['statue', 'torch', 'altar'],
            'hint': 'Honor the guardian, kindle the flame, offer tribute.',
            'hint_cost': {'move': 4},
            'reward': {
                'reveal_exit': {
                    'direction': 'up',
                    'message': 'Warm light floods in as a stairwell opens above.'
                }
            }
        }
    ],
    4050: [
        {
            'id': 'moria_riddle_stone',
            'type': 'riddle',
            'prompt': 'A dwarven rune reads: "What has roots as nobody sees..."',
            'question': 'What has roots as nobody sees, is taller than trees, up, up it goes, and yet it never grows?',
            'answers': ['mountain', 'a mountain'],
            'hint': 'It towers but never grows.',
            'hint_cost': {'gold': 35},
            'reward': {
                'reveal_exit': {
                    'direction': 'north',
                    'message': 'The rune flares, revealing a northern tunnel.'
                },
                'item_vnum': 9200
            }
        }
    ],
    4070: [
        {
            'id': 'moria_lever_echoes',
            'type': 'lever',
            'prompt': 'Four levers line the wall, each labeled with a cavern chant.',
            'levers': ['drum', 'chant', 'echo'],
            'sequence': ['chant', 'drum', 'echo'],
            'hint': 'The ritual begins with voice, then thunder, then resonance.',
            'hint_cost': {'move': 4},
            'reward': {
                'reveal_exit': {
                    'direction': 'east',
                    'message': 'A stone slab pivots, revealing a hidden eastward route.'
                },
                'gold': 90
            }
        }
    ],
    5020: [
        {
            'id': 'fungus_pressure_path',
            'type': 'environmental',
            'prompt': 'The ground feels hollow in three distinct spots.',
            'objects': ['west', 'center', 'east'],
            'sequence': ['west', 'center', 'east'],
            'hint': 'Cross the path as the spores drift from left to right.',
            'hint_cost': {'move': 3},
            'reward': {
                'reveal_exit': {
                    'direction': 'down',
                    'message': 'The hollow stones shift, revealing a sinkhole.'
                }
            }
        }
    ],
    5030: [
        {
            'id': 'oasis_symbol_swell',
            'type': 'symbols',
            'prompt': 'Ripples form symbols in the oasis water.',
            'symbols': ['water', 'sand', 'wind'],
            'sequence': ['water', 'sand', 'wind'],
            'hint': 'The desert is born of water, claimed by sand, then scattered by wind.',
            'hint_cost': {'gold': 40},
            'reward': {
                'reveal_exit': {
                    'direction': 'down',
                    'message': 'The water parts, revealing a hidden hatch.'
                },
                'item_vnum': 9201
            }
        }
    ],
    5040: [
        {
            'id': 'sandfall_lever',
            'type': 'lever',
            'prompt': 'A trio of levers sits beneath a sand-worn arch.',
            'levers': ['left', 'middle', 'right'],
            'sequence': ['right', 'middle', 'left'],
            'hint': 'The wind shifts from the far horizon back to you.',
            'hint_cost': {'move': 3},
            'reward': {
                'reveal_exit': {
                    'direction': 'down',
                    'message': 'A rumble opens a stairwell beneath the sands.'
                },
                'item_vnum': 9301
            }
        }
    ],
    5050: [
        {
            'id': 'desert_riddle_gate',
            'type': 'riddle',
            'prompt': 'A sand-swept archway bears a question in ancient script.',
            'question': 'I have cities but no houses, mountains but no trees, and water but no fish. What am I?',
            'answers': ['map', 'a map'],
            'hint': 'You unfold it when you are lost.',
            'hint_cost': {'gold': 30},
            'reward': {
                'reveal_exit': {
                    'direction': 'west',
                    'message': 'The archway shimmers, revealing a hidden passage.'
                },
                'item_vnum': 9302
            }
        }
    ],
    6005: [
        {
            'id': 'haondor_grove_sequence',
            'type': 'environmental',
            'prompt': 'Three stones in the grove look recently disturbed.',
            'objects': ['stone', 'root', 'bloom'],
            'sequence': ['root', 'stone', 'bloom'],
            'hint': 'Life begins below, rises, then flowers.',
            'hint_cost': {'move': 4},
            'reward': {
                'reveal_exit': {
                    'direction': 'west',
                    'message': 'Vines pull aside, revealing a hidden trail.'
                },
                'item_vnum': 9202
            }
        }
    ],
    6070: [
        {
            'id': 'haondor_lever_lights',
            'type': 'lever',
            'prompt': 'Crystal levers pulse with forest light.',
            'levers': ['emerald', 'azure', 'amber'],
            'sequence': ['emerald', 'amber', 'azure'],
            'hint': 'Spring, autumn, winter.',
            'hint_cost': {'gold': 35},
            'reward': {
                'reveal_exit': {
                    'direction': 'north',
                    'message': 'The crystals hum, opening a path north.'
                },
                'item_vnum': 9303
            }
        }
    ],
    7010: [
        {
            'id': 'sewer_symbol_flow',
            'type': 'symbols',
            'prompt': 'Sewer grates display three grimy symbols.',
            'symbols': ['rat', 'water', 'stone'],
            'sequence': ['rat', 'water', 'stone'],
            'hint': 'The vermin lead you to the flow, which carves the way.',
            'hint_cost': {'move': 3},
            'reward': {
                'reveal_exit': {
                    'direction': 'north',
                    'message': 'The grate swings open to the north.'
                },
                'gold': 60
            }
        }
    ],
    7030: [
        {
            'id': 'sewer_riddle_lock',
            'type': 'riddle',
            'prompt': 'A dripping inscription reads: "The more you take, the more you leave behind."',
            'question': 'The more you take, the more you leave behind. What am I?',
            'answers': ['footsteps', 'footstep', 'steps'],
            'hint': 'Think of a traveler in the mud.',
            'hint_cost': {'gold': 20},
            'reward': {
                'reveal_exit': {
                    'direction': 'west',
                    'message': 'A hidden sluice gate unlocks to the west.'
                },
                'item_vnum': 9203
            }
        }
    ]
}
