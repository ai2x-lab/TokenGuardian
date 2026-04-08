#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from datetime import datetime

POLICY = Path(__file__).resolve().parents[1] / "references" / "guardian-policy.json"


def load_policy():
    if not POLICY.exists():
        return {"thresholds": {"info": 50, "warn": 60, "danger": 80, "critical": 90}, "skipCronIds": [], "skipRules": []}
    return json.loads(POLICY.read_text(encoding="utf-8"))


def save_policy(data):
    POLICY.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cmd_list(_args):
    data = load_policy()
    print(json.dumps(data.get("skipRules", []), ensure_ascii=False, indent=2))


def cmd_add(args):
    data = load_policy()
    rules = data.setdefault("skipRules", [])
    rules = [r for r in rules if r.get("cronId") != args.cron_id]
    rules.append(
        {
            "cronId": args.cron_id,
            "reason": args.reason,
            "expiresAt": args.expires_at,
            "enabled": True,
        }
    )
    data["skipRules"] = rules
    if args.cron_id not in data.setdefault("skipCronIds", []):
        data["skipCronIds"].append(args.cron_id)
    save_policy(data)
    print(f"added skip: {args.cron_id}")


def cmd_remove(args):
    data = load_policy()
    data["skipCronIds"] = [i for i in data.get("skipCronIds", []) if i != args.cron_id]
    data["skipRules"] = [r for r in data.get("skipRules", []) if r.get("cronId") != args.cron_id]
    save_policy(data)
    print(f"removed skip: {args.cron_id}")


def main():
    p = argparse.ArgumentParser(description="Token Guardian skip-list manager")
    sub = p.add_subparsers(dest="cmd", required=True)

    l = sub.add_parser("list")
    l.set_defaults(func=cmd_list)

    a = sub.add_parser("add")
    a.add_argument("cron_id")
    a.add_argument("--reason", default="user approved")
    a.add_argument("--expires-at", default="")
    a.set_defaults(func=cmd_add)

    r = sub.add_parser("remove")
    r.add_argument("cron_id")
    r.set_defaults(func=cmd_remove)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
