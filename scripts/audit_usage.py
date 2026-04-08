#!/usr/bin/env python3
import argparse
import json
import subprocess


def run(cmd: str, timeout: int = 30) -> str:
    return subprocess.check_output(cmd, shell=True, text=True, timeout=timeout, stderr=subprocess.STDOUT)


def parse_json_with_noise(raw: str):
    raw = raw.strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        pass
    idx_obj = raw.find('{')
    idx_arr = raw.find('[')
    candidates = [i for i in [idx_obj, idx_arr] if i >= 0]
    if not candidates:
        return None
    start = min(candidates)
    try:
        return json.loads(raw[start:])
    except Exception:
        return None


def load_sessions():
    try:
        out = run('openclaw sessions --json', timeout=30)
        data = parse_json_with_noise(out)
        if isinstance(data, dict) and isinstance(data.get('sessions'), list):
            return data['sessions']
        if isinstance(data, list):
            return data
    except Exception:
        pass

    try:
        local = '/home/ubuntu/.openclaw/agents/main/sessions/sessions.json'
        with open(local, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict):
            return list(data.values())
    except Exception:
        return []
    return []


def context_pct(session):
    total = session.get('totalTokens')
    cap = session.get('contextTokens')
    try:
        if total is None or cap in (None, 0):
            return None
        return round(float(total) / float(cap) * 100, 1)
    except Exception:
        return None


def render_human(out):
    c = out['counts']
    lines = []
    lines.append('🧠 Token / Context 使用概況')
    lines.append(f"- 掃描到的 session：{c['totalSessionsSeen']}")
    lines.append(f"- 高風險 session：{c['highRiskSessions']}")
    lines.append(f"- 注意中 session：{c['infoSessions']}")
    if out['highRiskSessions']:
        lines.append('')
        lines.append('高風險 session：')
        for s in out['highRiskSessions'][:5]:
            lines.append(f"- {s['label']} ({s['sessionKey']}): context 約 {s['contextPercent']}%")
    elif out['infoSessions']:
        lines.append('')
        lines.append('目前沒有高風險 session，但以下值得注意：')
        for s in out['infoSessions'][:5]:
            lines.append(f"- {s['label']} ({s['sessionKey']}): context 約 {s['contextPercent']}%")
    else:
        lines.append('')
        lines.append('目前沒有明顯偏高的 session context 使用。')
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Audit OpenClaw session usage risk')
    parser.add_argument('--json', action='store_true', dest='as_json', help='Output raw JSON')
    args = parser.parse_args()

    sessions = load_sessions()
    risky = []
    info = []
    for s in sessions:
        pct = context_pct(s)
        item = {
            'sessionKey': s.get('key') or s.get('sessionKey') or s.get('id') or s.get('sessionId'),
            'label': s.get('key') or s.get('agentId') or s.get('sessionId') or 'unknown',
            'contextPercent': pct,
            'totalTokens': s.get('totalTokens'),
            'contextTokens': s.get('contextTokens'),
        }
        if pct is None:
            continue
        if pct >= 80:
            risky.append(item)
        elif pct >= 60:
            info.append(item)

    out = {
        'status': 'ok',
        'highRiskSessions': risky,
        'infoSessions': info,
        'counts': {
            'highRiskSessions': len(risky),
            'infoSessions': len(info),
            'totalSessionsSeen': len(sessions),
        }
    }
    if args.as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(render_human(out))


if __name__ == '__main__':
    main()
