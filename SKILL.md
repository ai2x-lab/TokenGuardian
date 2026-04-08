---
name: token-guardian
description: Monitor OpenClaw token/context usage and guard against runaway cron costs. Use when users ask to check token burn, set warning thresholds, audit cron risk (especially high-frequency non-isolated jobs), create daily usage summaries, or maintain skip/allow lists for known high-frequency cron jobs.
---

# Token Guardian

Implement a lightweight guardrail layer on top of OpenClaw built-in usage metrics.

## Core Goals

1. Detect token/context risk early.
2. Audit cron patterns that silently burn context.
3. Support skip/allow list for known intentional high-frequency cron jobs.
4. Provide concise alerts and daily summary.

## Data Sources

- Session usage: `session_status`
- Runtime sessions: `sessions_list`
- Cron configuration/status: `openclaw cron list` (via `exec`)

## Default Risk Thresholds

- **INFO**: context >= 50%
- **WARN**: context >= 60%
- **DANGER**: context >= 80%
- **CRITICAL**: context >= 90% or rapid growth pattern

## Cron Risk Rules

預設（balanced）下，僅將 **non-isolated + 高頻** 視為高風險。

- `strict`：任何 non-isolated 都列高風險
- `balanced`：只抓 non-isolated + 高頻
- `relaxed`：同 balanced，但建議語氣更溫和、以提示為主

補充：
- isolated 高頻預設可接受（不單獨告警）
- long prompt 只列資訊級（info-only）

## Skip / Allow List

Store policy in:

`skills/token-guardian/references/guardian-policy.json`

Supported fields:

- `safetyLevel`: `strict` / `balanced` / `relaxed`
- `thresholds`: custom level boundaries
- `skipCronIds`: cron ids intentionally ignored for alerting
- `skipRules`: optional reason + expiry

When a cron is skipped:

- Do not fire urgent alert for that item
- Still include it in daily report under “Skipped High-Risk Items”

## Operational Workflow

### 1) Instant Check (`meter now` style)

- Call `session_status`
- Parse context %, token in/out
- Return one-line status + 1-3 concrete actions

### 2) Cron Audit (`meter audit-cron` style)

- Run `openclaw cron list`
- Classify each job by risk rules
- Apply skip list
- Output: high-risk list + fixes

### 3) Alert Check (2-hour isolated cron)

- Reuse instant + cron audit
- Only alert user when WARN or above
- Keep message short and actionable

### 4) Nightly Summary (22:30 suggested)

Include:

- Daily usage headline
- Worst offenders (cron/session)
- Skipped high-risk items
- Recommended fixes for tomorrow

## Message Templates

Read templates from:

`references/alert-templates.md`

## Safety / Noise Control

- Avoid alert spam: one alert per risk tier change unless user requests full stream.
- Prefer short bullet output over long prose.
- Do not auto-edit cron jobs unless explicitly asked.
