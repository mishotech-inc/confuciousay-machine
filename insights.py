#!/usr/bin/env python3
"""Pull per-post metrics (the ones the A/B system scores on) into logs/insights.json.
Runs weekly. Saves + shares per reach decide the bucket rotation, per revision_v2.
Defensive: requests metrics one at a time, keeps whatever the API grants."""
import os, json, sys
from datetime import datetime
import requests

ROOT = os.path.dirname(os.path.abspath(__file__))
API = "https://graph.instagram.com/v23.0"
TOKEN = os.environ["IG_ACCESS_TOKEN"]
METRICS = ["reach", "views", "saved", "shares", "likes", "comments", "total_interactions"]

def fetch(media_id):
    out = {}
    for m in METRICS:
        try:
            r = requests.get(f"{API}/{media_id}/insights",
                             params={"metric": m, "access_token": TOKEN}, timeout=30)
            j = r.json()
            if r.status_code < 400 and j.get("data"):
                vals = j["data"][0].get("values", [{}])
                out[m] = vals[0].get("value", 0)
        except Exception as e:
            print(f"{media_id}/{m}: {e}", file=sys.stderr)
    return out

def main():
    posted = json.load(open(os.path.join(ROOT, "logs", "posted.json")))
    path = os.path.join(ROOT, "logs", "insights.json")
    ins = json.load(open(path)) if os.path.exists(path) else {}
    for p in posted:
        m = fetch(p["media_id"])
        if not m: continue
        reach = m.get("reach") or 0
        ins[p["key"]] = {**{k: p[k] for k in ("date", "slot", "type", "bucket", "hook_formula", "variant", "permalink")},
                         "metrics": m,
                         "saves_per_reach": round(m.get("saved", 0) / reach, 5) if reach else None,
                         "sends_per_reach": round(m.get("shares", 0) / reach, 5) if reach else None,
                         "pulled_at": datetime.utcnow().isoformat() + "Z"}
    json.dump(ins, open(path, "w"), indent=1)
    print(f"insights for {len(ins)} posts")

if __name__ == "__main__":
    main()
