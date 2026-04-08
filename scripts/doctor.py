#!/usr/bin/env python3
import json
import os
import shutil
from pathlib import Path

checks = []

def add(name, ok, detail):
    checks.append({"name": name, "ok": ok, "detail": detail})

openclaw_bin = shutil.which('openclaw')
add('openclaw_cli', bool(openclaw_bin), openclaw_bin or 'not found')

home = Path(os.environ.get('HOME', str(Path.home())))
session_candidates = [
    Path(os.environ.get('TOKEN_GUARDIAN_SESSION_STORE', '')) if os.environ.get('TOKEN_GUARDIAN_SESSION_STORE') else None,
    home / '.openclaw/agents/main/sessions/sessions.json',
]
session_candidates = [p for p in session_candidates if p]
found = None
for p in session_candidates:
    if p.exists():
        found = str(p)
        break
add('session_store', bool(found), found or 'not found')

cron_candidates = [
    home / '.openclaw/cron/jobs.json',
    home / '.openclaw/cron/jobs.json.bak',
]
cron_found = None
for p in cron_candidates:
    if p.exists():
        cron_found = str(p)
        break
add('cron_store', bool(cron_found), cron_found or 'not found')

policy = Path(__file__).resolve().parents[1] / 'references' / 'guardian-policy.json'
add('guardian_policy', policy.exists(), str(policy))

print(json.dumps({
    'status': 'ok' if all(c['ok'] for c in checks if c['name'] != 'cron_store') else 'degraded',
    'checks': checks,
}, ensure_ascii=False, indent=2))
