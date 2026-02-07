## [ERR-20260206-004] cron_model_unknown

**Logged**: 2026-02-06T14:12:00-08:00
**Priority**: medium
**Status**: pending
**Area**: infra

### Summary
Cron failed due to unknown model alias.

### Error
```
Error: Unknown model: anthropic/claude-opus-4-6
```

### Context
- Cron job attempted to use opus4.6 alias but model unavailable.

### Suggested Fix
Use a supported model alias or update cron config to match available models.

### Metadata
- Reproducible: yes
- Related Files: (cron job config)

---
