# Token Guardian Checklist (Ops)

## 2-hour Guard Check

1. Read policy file: `guardian-policy.json`
2. Inspect current session usage via `session_status`
3. Inspect cron jobs via `openclaw cron list --json`
4. Flag high-risk jobs (by safetyLevel; default抓 non-isolated+高頻，isolated高頻不單獨告警)
5. Apply skip rules (`skipCronIds`, `skipRules` enabled and not expired)
6. If risk >= WARN, notify user with concise actions

## Nightly Summary

1. Summarize today's token/context health
2. List high-risk cron jobs
3. List skipped high-risk jobs with reasons/expiry
4. Provide top 3 next-day optimizations
