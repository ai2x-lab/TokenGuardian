#!/usr/bin/env python3
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

POLICY = Path(__file__).resolve().parents[1] / "references" / "guardian-policy.json"
CRON_JOBS_PATHS = [
    Path.home() / ".openclaw/cron/jobs.json",
    Path.home() / ".openclaw/cron/jobs.json.bak",
]


def run(cmd: str, timeout: int = 20) -> str:
    return subprocess.check_output(cmd, shell=True, text=True, timeout=timeout, stderr=subprocess.STDOUT)


def load_policy():
    if not POLICY.exists():
        return {"skipCronIds": [], "skipRules": [], "safetyLevel": "balanced"}
    data = json.loads(POLICY.read_text(encoding="utf-8"))
    if not data.get("safetyLevel"):
        data["safetyLevel"] = "balanced"
    return data


def parse_json_with_noise(raw: str):
    raw = raw.strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        pass

    # OpenClaw CLI sometimes prepends warnings before JSON.
    idx_obj = raw.find("{")
    idx_arr = raw.find("[")
    candidates = [i for i in [idx_obj, idx_arr] if i >= 0]
    if not candidates:
        return None
    start = min(candidates)
    try:
        return json.loads(raw[start:])
    except Exception:
        return None


def load_jobs_from_local_file():
    for p in CRON_JOBS_PATHS:
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            jobs = data.get("jobs", []) if isinstance(data, dict) else []
            if isinstance(jobs, list):
                return jobs, f"file:{p}", None
        except Exception as e:
            return [], f"file:{p}", f"parse_error:{e}"
    return [], "file:none", "not_found"


def load_jobs_from_cli():
    try:
        out = run("openclaw cron list --json", timeout=25)
        data = parse_json_with_noise(out)
        if isinstance(data, dict) and isinstance(data.get("jobs"), list):
            return data.get("jobs", []), "cli:openclaw", None
        return [], "cli:openclaw", "invalid_json"
    except subprocess.CalledProcessError as e:
        return [], "cli:openclaw", f"called_process_error:{e.output[:300]}"
    except Exception as e:
        return [], "cli:openclaw", f"error:{e}"


def load_cron_jobs():
    # Prefer local file for stability; fallback to CLI.
    jobs, source, err = load_jobs_from_local_file()
    if jobs:
        return jobs, source, err

    jobs2, source2, err2 = load_jobs_from_cli()
    if jobs2:
        return jobs2, source2, err2

    # Return graceful degraded mode, never crash.
    return [], "degraded", f"file_err={err}; cli_err={err2}"


def cron_is_high_freq(expr: str) -> bool:
    """True when schedule is hourly or more frequent."""
    expr = (expr or "").strip()
    parts = expr.split()
    if len(parts) != 5:
        return False

    minute, hour, *_ = parts

    if minute == "*":
        return True

    if minute.startswith("*/"):
        try:
            n = int(minute[2:])
            return n <= 60
        except ValueError:
            return True

    if hour == "*":
        return True

    if hour.startswith("*/"):
        try:
            h = int(hour[2:])
            return h <= 1
        except ValueError:
            return False

    if "/" in hour:
        try:
            step = int(hour.split("/")[-1])
            return step <= 1
        except ValueError:
            return False

    return False


def is_expired(ts: str) -> bool:
    if not ts:
        return False
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")) < datetime.now().astimezone()
    except Exception:
        return False


def evaluate_risk(expr: str, session_target: str, safety_level: str, message_len: int):
    high_reasons = []
    info_reasons = []
    is_high_freq = cron_is_high_freq(expr)
    is_non_isolated = session_target != "isolated"
    is_long_prompt = message_len > 500

    if is_non_isolated and is_high_freq:
        high_reasons.append("high-frequency-non-isolated")

    if is_non_isolated and is_long_prompt:
        high_reasons.append("non-isolated-long-prompt")

    if safety_level == "strict" and is_non_isolated and "non-isolated" not in high_reasons:
        high_reasons.append("non-isolated")

    if is_long_prompt and not is_non_isolated:
        info_reasons.append("long-prompt")

    return high_reasons, info_reasons


def resolve_traffic_light(high_count: int, info_count: int, skipped_count: int, safety_level: str):
    if high_count > 0:
        return {"emoji": "🔴", "label": "RED"}
    # In balanced/relaxed mode, info-only should not look alarming.
    if info_count > 0 and safety_level == "strict":
        return {"emoji": "🟡", "label": "YELLOW"}
    if skipped_count > 0:
        return {"emoji": "🟢", "label": "GREEN(SKIPPED)"}
    return {"emoji": "🟢", "label": "GREEN"}




def render_human_report(out):
    light = out.get("trafficLight", {})
    emoji = light.get("emoji", "ℹ️")
    label = light.get("label", "UNKNOWN")
    counts = out.get("counts", {})
    lines = []
    lines.append(f"{emoji} Token Guardian 狀態：{label}")
    lines.append(f"- 總 cron job 數：{counts.get('total', 0)}")
    lines.append(f"- 啟用中：{counts.get('enabled', 0)}")
    lines.append(f"- 停用中：{counts.get('disabled', 0)}")
    lines.append(f"- 高風險：{counts.get('highRisk', 0)}")
    lines.append(f"- 資訊級提醒：{counts.get('info', 0)}")
    lines.append(f"- 已略過：{counts.get('skipped', 0)}")
    lines.append("- 說明：以上是 cron job 筆數，不是執行次數。")

    risky = out.get('highRisk', [])
    info = out.get('info', [])
    skipped = out.get('skipped', [])

    if risky:
        lines.append('')
        lines.append('需要優先注意：')
        for item in risky[:5]:
            reason_map = {
                'high-frequency-non-isolated': '非 isolated 且高頻',
                'non-isolated-long-prompt': '非 isolated 且提示詞偏長，會受當下 session content 影響',
                'non-isolated': '非 isolated'
            }
            reasons = '、'.join(reason_map.get(r, r) for r in item.get('highRiskReasons', [])) or 'high-risk'
            lines.append(f"- {item.get('name') or item.get('id')}: {reasons}")
    elif info:
        lines.append('')
        lines.append('目前沒有高風險項目。以下是資訊級提醒：')
        for item in info[:5]:
            info_map = {
                'long-prompt': '提示詞偏長（但為 isolated，風險可控）'
            }
            reasons = '、'.join(info_map.get(r, r) for r in item.get('infoReasons', [])) or 'info'
            lines.append(f"- {item.get('name') or item.get('id')}: {reasons}")
    else:
        lines.append('')
        lines.append('目前沒有需要特別處理的 cron 風險。')

    if skipped:
        lines.append('')
        lines.append(f"已略過項目：{len(skipped)}")

    if counts.get('highRisk', 0) > 0:
        lines.append('')
        lines.append('建議：優先把高風險 cron 改為 isolated，或降低頻率。')
    elif counts.get('info', 0) > 0:
        lines.append('')
        lines.append('建議：這些項目目前可接受，但可以考慮縮短提示詞。')
    else:
        lines.append('')
        lines.append('建議：目前不需要立即調整。')

    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Audit OpenClaw cron risk")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Output raw JSON")
    args = parser.parse_args()
    jobs, jobs_source, jobs_error = load_cron_jobs()
    policy = load_policy()
    safety_level = (policy.get("safetyLevel") or "balanced").strip().lower()
    if safety_level not in {"strict", "balanced", "relaxed"}:
        safety_level = "balanced"

    skip_ids = set(policy.get("skipCronIds", []))
    for r in policy.get("skipRules", []):
        if r.get("enabled") and not is_expired(r.get("expiresAt", "")):
            skip_ids.add(r.get("cronId"))

    risky = []
    info_only = []
    skipped = []
    for j in jobs:
        sched = j.get("schedule", {})
        expr = sched.get("expr", "")
        session_target = j.get("sessionTarget")

        msg = ((j.get("payload") or {}).get("message") or "")
        high_reasons, info_reasons = evaluate_risk(expr, session_target, safety_level, len(msg))

        if not high_reasons and not info_reasons:
            continue

        item = {
            "id": j.get("id"),
            "name": j.get("name"),
            "expr": expr,
            "sessionTarget": session_target,
            "highRiskReasons": high_reasons,
            "infoReasons": info_reasons,
        }

        if j.get("id") in skip_ids:
            skipped.append(item)
        elif high_reasons:
            risky.append(item)
        else:
            info_only.append(item)

    enabled_jobs = [j for j in jobs if j.get("enabled", True) is True]
    disabled_jobs = [j for j in jobs if j.get("enabled", True) is False]

    light = resolve_traffic_light(len(risky), len(info_only), len(skipped), safety_level)
    out = {
        "status": "ok" if jobs_source != "degraded" else "degraded",
        "jobsSource": jobs_source,
        "jobsSourceError": jobs_error,
        "safetyLevel": safety_level,
        "trafficLight": light,
        "highRisk": risky,
        "info": info_only,
        "skipped": skipped,
        "counts": {
            "highRisk": len(risky),
            "info": len(info_only),
            "skipped": len(skipped),
            "total": len(jobs),
            "enabled": len(enabled_jobs),
            "disabled": len(disabled_jobs),
        },
    }
    if args.as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(render_human_report(out))


if __name__ == "__main__":
    main()
