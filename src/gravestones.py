"""Server-side gravestone registry for player deaths.

Records where players fall so graphical clients can render memorials
visible to everyone. Persisted to data/gravestones.json.
"""
import json
import os
import time
import logging

logger = logging.getLogger('Misthollow.Gravestones')

_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'gravestones.json')
_MAX_PER_ROOM = 5
_MAX_TOTAL = 500


class GravestoneRegistry:
    _stones = None  # vnum(str) -> [{name, killer, ts}]

    @classmethod
    def _load(cls):
        if cls._stones is not None:
            return
        try:
            with open(_DATA_PATH, 'r', encoding='utf-8') as f:
                cls._stones = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            cls._stones = {}

    @classmethod
    def _save(cls):
        try:
            os.makedirs(os.path.dirname(_DATA_PATH), exist_ok=True)
            with open(_DATA_PATH, 'w', encoding='utf-8') as f:
                json.dump(cls._stones, f)
        except Exception as e:
            logger.warning(f"Could not persist gravestones: {e}")

    @classmethod
    def record(cls, vnum, player_name, killer_name):
        cls._load()
        key = str(vnum)
        stones = cls._stones.setdefault(key, [])
        stones.append({'name': player_name, 'killer': killer_name, 'ts': int(time.time())})
        if len(stones) > _MAX_PER_ROOM:
            del stones[0:len(stones) - _MAX_PER_ROOM]
        # global cap: drop the oldest stones across all rooms
        total = sum(len(v) for v in cls._stones.values())
        if total > _MAX_TOTAL:
            oldest_key = min(cls._stones, key=lambda k: cls._stones[k][0]['ts'] if cls._stones[k] else 1 << 62)
            if cls._stones.get(oldest_key):
                cls._stones[oldest_key].pop(0)
                if not cls._stones[oldest_key]:
                    del cls._stones[oldest_key]
        cls._save()

    @classmethod
    def for_room(cls, vnum):
        cls._load()
        return list(cls._stones.get(str(vnum), []))
