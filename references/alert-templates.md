# Token Guardian Alert Templates

## WARN

🟡 Token Guardian：用量偏高（Context {{context_pct}}%）
- 目前 tokens: in {{tokens_in}}, out {{tokens_out}}
- 安全層級：{{safety_level}}
- 建議（溫和）：先縮短回覆、確認非 isolated 的高頻 cron 是否必要

## DANGER

🟠 Token Guardian：高風險（Context {{context_pct}}%）
- 可能來源：{{top_risk_sources}}
- 安全層級：{{safety_level}}
- 建議：
  - 優先處理 non-isolated + 高頻任務
  - isolated 高頻任務預設視為可接受（除非你指定要更嚴）
  - 提示詞改短摘要模式

## CRITICAL

🔴 Token Guardian：接近爆量（Context {{context_pct}}%）
- 請立即處理高風險 cron：{{top_risk_sources}}
- 建議先停用非必要 cron，待用量回落後再恢復

## NIGHTLY SUMMARY

🌙 Token Guardian 每日摘要 {{traffic_emoji}} {{traffic_label}}
- 今日使用：in {{tokens_in_total}} / out {{tokens_out_total}}
- 最高 context：{{peak_context_pct}}%
- 高風險 cron：{{high_risk_count}} 個
- 已 Skip 高風險項：{{skipped_count}} 個
- 安全層級：{{safety_level}}
- 明日建議：{{next_actions}}
