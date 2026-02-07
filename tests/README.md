# RealmsMUD Testing Tools

## 1) Automated Test Suite
Runs core command checks via socket.

```bash
python3 tests/test_suite.py localhost 4000
```

Smoke test (quick):
```bash
python3 tests/test_suite.py --smoke localhost 4000
```

Results logged to: `logs/tests.log`

## 2) AI Player Agent (LM Studio)
Uses local LLM to explore and test.

**Requirements:**
- LM Studio running at `http://127.0.0.1:1234`
- Model loaded (Qwen 2.5 7B recommended)

```bash
python3 tests/ai_player.py localhost 4000 50
```

## 3) Manual Quick Test
```bash
nc 127.0.0.1 4000
```

Suggested manual checklist:
- login
- look / exits / score
- move north/south
- fight a low-level mob
- test bank (deposit/withdraw)
- drink from fountain
- talk/chat to NPC
