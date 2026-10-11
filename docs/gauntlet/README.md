# docs/gauntlet

Records of Gauntlet Loop runs (builder vs blind critic against a runnable reference).
Start with `STATUS.md`, then `.claude/skills/gauntlet-loop/SKILL.md`.

- `reference/<name>/` committed reference screenshots (the bar)
- `<run>/PLAN.md` pieces, owned files, answer-key questions
- `<run>/round-N/` `builder-*.md`, `critic-*.json`, `verdicts.md` (committed); `mh/`, `pairs/` (regenerated, gitignored)
- `<run>/REPORT.md` end-of-run summary for the human brake
- `workflows/*.js` Workflow-tool scripts, one per dimension
