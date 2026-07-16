#!/usr/bin/env python3
"""Confuciousay publisher: posts the slot that is due right now via the Instagram API
(Instagram Login flavor, graph.instagram.com). Runs on GitHub Actions cron at
15:00 / 19:00 / 01:00 UTC (8am / 12pm / 6pm Pacific in summer).

Idempotent: checks logs/posted.json before posting. One slot per run, most recent due
slot today wins (a missed earlier slot is NOT back-posted; it gets recycled by the
weekly reconciliation instead, so the feed never bursts).

Env: IG_USER_ID, IG_ACCESS_TOKEN, REPO (owner/name). Media URLs come from manifest.json.
"""
import os, csv, json, time, sys, urllib.parse
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

ROOT = os.path.dirname(os.path.abspath(__file__))
API = "https://graph.instagram.com/v23.0"
IG_ID = os.environ["IG_USER_ID"]
TOKEN = os.environ["IG_ACCESS_TOKEN"]
REPO = os.environ.get("REPO", "")
SLOT_HOURS = {1: 8, 2: 12, 3: 18}

def media_base():
    man = json.load(open(os.path.join(ROOT, "manifest.json")))
    sha = man.get("media_sha", "main")
    return f"https://cdn.jsdelivr.net/gh/{REPO}@{sha}"

def api(method, path, retries=2, **params):
    params["access_token"] = TOKEN
    for attempt in range(retries + 1):
        try:
            r = requests.request(method, f"{API}/{path}", params=params if method == "GET" else None,
                                 data=None if method == "GET" else params, timeout=60)
            j = r.json()
            if r.status_code < 400: return j
            print(f"API {r.status_code} on {path}: {json.dumps(j)[:400]}", file=sys.stderr)
        except Exception as e:
            print(f"API exception on {path}: {e}", file=sys.stderr)
        if attempt < retries: time.sleep(30)
    raise RuntimeError(f"API call failed after retries: {path}")

def wait_ready(container_id, max_wait=420):
    waited = 0
    while waited < max_wait:
        j = api("GET", container_id, **{"fields": "status_code"})
        sc = j.get("status_code")
        if sc == "FINISHED": return
        if sc == "ERROR": raise RuntimeError(f"container {container_id} ERROR: {j}")
        time.sleep(15); waited += 15
    raise RuntimeError(f"container {container_id} not ready after {max_wait}s")

def main():
    dry = "--dry-run" in sys.argv
    now = datetime.now(ZoneInfo("America/Los_Angeles"))
    today = now.date().isoformat()
    due = [s for s, h in SLOT_HOURS.items() if now.hour >= h - 1]  # slot opens 1h early to absorb cron drift
    if not due:
        print("no slot due"); return
    slot = max(due)

    posted = json.load(open(os.path.join(ROOT, "logs", "posted.json")))
    key = f"{today}_s{slot}"
    if any(p["key"] == key for p in posted):
        print(f"{key} already posted"); return

    rows = {(r["date"], int(r["slot"])): r for r in csv.DictReader(open(os.path.join(ROOT, "plan.csv")))}
    r = rows.get((today, slot))
    if not r:
        print(f"no plan row for {key} (plan may need extending)"); return

    base = media_base()
    caption = (r["caption"].strip() + "\n\n" + r["hashtags"].strip())[:2150]

    if dry:
        print(f"DRY RUN {key}: type={r['type']} media={base}/media/{r['media_key']} caption[:120]={caption[:120]!r}")
        return

    if r["type"] == "carousel":
        slides = sorted(f for f in os.listdir(os.path.join(ROOT, "media", r["media_key"])) if f.endswith(".png"))
        children = []
        for s in slides:
            url = f"{base}/media/{r['media_key']}/{s}"
            c = api("POST", f"{IG_ID}/media", image_url=url, is_carousel_item="true")
            children.append(c["id"]); time.sleep(2)
        parent = api("POST", f"{IG_ID}/media", media_type="CAROUSEL",
                     children=",".join(children), caption=caption)
        wait_ready(parent["id"])
        pub = api("POST", f"{IG_ID}/media_publish", creation_id=parent["id"])
    else:
        url = f"{base}/media/{r['media_key']}.mp4"
        cont = api("POST", f"{IG_ID}/media", media_type="REELS", video_url=url,
                   caption=caption, share_to_feed="true")
        wait_ready(cont["id"])
        pub = api("POST", f"{IG_ID}/media_publish", creation_id=cont["id"])

    media_id = pub["id"]
    perma = api("GET", media_id, **{"fields": "permalink"}).get("permalink", "")
    posted.append({"key": key, "date": today, "slot": slot, "type": r["type"],
                   "bucket": r["bucket"], "hook_formula": r["hook_formula"], "variant": r["variant"],
                   "media_id": media_id, "permalink": perma, "ts": datetime.utcnow().isoformat() + "Z"})
    json.dump(posted, open(os.path.join(ROOT, "logs", "posted.json"), "w"), indent=1)
    print(f"published {key} -> {perma}")

if __name__ == "__main__":
    main()
