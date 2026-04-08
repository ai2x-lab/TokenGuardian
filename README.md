# Token Guardian

Token Guardian 是一個給 OpenClaw 使用的監控型 skill，用來檢查 token / context 使用風險、盤點高風險 cron，並提供 skip/allow 管理。

## 適用場景
- 想知道目前 session token / context 是否偏高
- 想盤點哪些 cron 容易偷偷吃上下文
- 想建立高風險 cron 的 skip/allow 規則
- 想要每日摘要或定期巡檢

## 內容
- `SKILL.md`：給 agent 的使用規則
- `scripts/audit_cron.py`：盤點 cron 風險
- `scripts/skip_manager.py`：管理 skip 規則
- `references/guardian-policy.json`：風險門檻與 skip 設定
- `references/alert-templates.md`：訊息模板

## 安裝到 OpenClaw
如果這個 repo 已 clone 到你的 workspace，可直接作為本地 skill 使用。

建議路徑：
```bash
mkdir -p ~/clawd/skills
cd ~/clawd/skills
git clone https://github.com/ai2x-lab/TokenGuardian.git token-guardian
```

確認 skill 可被 OpenClaw 看見：
```bash
openclaw skills list | grep -i token-guardian
openclaw skills info token-guardian
```

## 最小使用方式

### 1) 盤點 cron 風險
```bash
python3 ~/clawd/skills/token-guardian/scripts/audit_cron.py
```

### 2) 管理 skip 規則
```bash
python3 ~/clawd/skills/token-guardian/scripts/skip_manager.py list
python3 ~/clawd/skills/token-guardian/scripts/skip_manager.py add <cron_id> --reason "customer accepted" --expires-at "2026-12-31T23:59:59+08:00"
python3 ~/clawd/skills/token-guardian/scripts/skip_manager.py remove <cron_id>
```

## Requirements
- OpenClaw 2026.4.x+
- Agent/tool access to `session_status`, `sessions_list`, `exec`
- Runtime can run `openclaw cron list --json`

## OpenClaw 整合前提
這個 skill 預設依賴以下 OpenClaw 能力：
- `session_status`
- `sessions_list`
- `exec`（用於 `openclaw cron list`）

若 agent 無法使用這些能力，請確認：
- tool allowlist / profile 是否允許
- 目前會話是否能執行 `openclaw cron list`

## 設定檔
策略檔位置：
```text
references/guardian-policy.json
```

主要欄位：
- `safetyLevel`: `strict` / `balanced` / `relaxed`
- `thresholds`: 風險門檻
- `skipCronIds`: 永久略過
- `skipRules`: 含原因/到期時間的規則

## 開源使用注意事項
- 不要把你自己的 cron id、token、內部路徑硬寫進 repo。
- 若要對外發布，請先確認 `guardian-policy.json` 沒有帶私人資料。
- `__pycache__` 不需要納入 repo。

## 建議下一步
- 補 `.gitignore`（忽略 `__pycache__` / 本機輸出）
- 補範例輸出與 doctor/check 模式
- 若要讓其他人更容易部署，可再補一份 `docs/INSTALL.md`


## Post-install check
安裝完成後可用以下方式確認：

```bash
openclaw skills info token-guardian
python3 ~/clawd/skills/token-guardian/scripts/audit_cron.py
python3 ~/clawd/skills/token-guardian/scripts/skip_manager.py list
```

預期：
- skill 能被 OpenClaw 辨識
- `audit_cron.py` 可輸出 JSON 結果
- `skip_manager.py list` 可正常列出規則


## 報告解讀
- `total` / `enabled` / `disabled` 指的是 **cron job 筆數**，不是執行次數。
- 一個每小時執行一次的 cron，仍然只算 1 個 job。
- `info` 代表資訊級提醒，不等於高風險。


## 建議排程

### 2H 巡檢（只在高風險時提醒）
建議使用 isolated cron，每 2 小時跑一次 Token Guardian。若結果只有資訊級提醒，則不主動通知；只有在出現高風險項目時才提醒使用者。

### 夜間摘要（每日一次）
建議每天 22:30 執行一次摘要，回報：
- 高風險 cron
- 資訊級提醒
- 啟用/停用 job 統計
- 建議隔天優先處理項目
