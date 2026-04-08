# Token Guardian

Token Guardian 是 OpenClaw 的 token 風險守門員，重點在「防止背景 cron 偷吃上下文」。

## 你可以做什麼

- 稽核高風險 cron（非 isolated、或非 isolated 且高頻）
- 長提示詞列為資訊級（info），不觸發高風險告警
- 設定 skip 清單（已知可接受的高頻任務）
- 產出晚間摘要（高風險 + 已豁免項目）

> 規則重點：**高頻 + isolated 預設視為安全，不會因高頻單獨告警**。
> 另可用 `safetyLevel`（strict / balanced / relaxed）調整告警嚴格度，避免過度打擾。

## 指令（MVP）

### 稽核 cron

```bash
python3 /home/ubuntu/clawd/skills/token-guardian/scripts/audit_cron.py
```

### Skip 管理

```bash
python3 /home/ubuntu/clawd/skills/token-guardian/scripts/skip_manager.py list
python3 /home/ubuntu/clawd/skills/token-guardian/scripts/skip_manager.py add <cron_id> --reason "customer accepted" --expires-at "2026-12-31T23:59:59+08:00"
python3 /home/ubuntu/clawd/skills/token-guardian/scripts/skip_manager.py remove <cron_id>
```

## 規則檔

`/home/ubuntu/clawd/skills/token-guardian/references/guardian-policy.json`

- `safetyLevel`：`strict` / `balanced` / `relaxed`
- `thresholds`：警戒門檻
- `skipCronIds`：永久 skip id
- `skipRules`：可帶原因/到期時間的 skip 規則
