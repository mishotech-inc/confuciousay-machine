#!/usr/bin/env python3
"""One-shot: generate the 8 Confucius motion clips via fal.ai (Kling image-to-video),
using the locked reference portrait so the face stays consistent. ~$5-10 total.
Env: FAL_KEY, REPO. Model override: KLING_MODEL (default Kling v2.6 standard).
Idempotent: skips clips already in kling-clips/."""
import os, json, time, sys
import requests

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "kling-clips")
os.makedirs(OUT, exist_ok=True)
FAL_KEY = os.environ["FAL_KEY"]
REPO = os.environ.get("REPO", "")
MODEL = os.environ.get("KLING_MODEL", "fal-ai/kling-video/v2.6/standard/image-to-video")
HDRS = {"Authorization": f"Key {FAL_KEY}", "Content-Type": "application/json"}
REF_URL = f"https://cdn.jsdelivr.net/gh/{REPO}@main/confucius-reference.png"
NEGATIVE = "distorted face, face morphing, extra fingers, wrong hands, jerky motion, fast movement, text, watermark, low quality"

def generate(name, prompt):
    dest = os.path.join(OUT, name)
    if os.path.exists(dest):
        print(f"skip {name} (exists)"); return
    body = {"prompt": prompt, "image_url": REF_URL, "duration": "5",
            "aspect_ratio": "9:16", "negative_prompt": NEGATIVE}
    r = requests.post(f"https://queue.fal.run/{MODEL}", headers=HDRS, json=body, timeout=60)
    r.raise_for_status()
    req = r.json()
    status_url, response_url = req["status_url"], req["response_url"]
    for _ in range(120):  # up to ~20 min
        s = requests.get(status_url, headers=HDRS, timeout=30).json()
        if s.get("status") == "COMPLETED": break
        if s.get("status") in ("FAILED", "ERROR"):
            raise RuntimeError(f"{name} failed: {s}")
        time.sleep(10)
    res = requests.get(response_url, headers=HDRS, timeout=60).json()
    video_url = res["video"]["url"] if "video" in res else res["response"]["video"]["url"]
    data = requests.get(video_url, timeout=300)
    open(dest, "wb").write(data.content)
    print(f"generated {name} ({len(data.content)//1024} KB)")

def main():
    prompts = json.load(open(os.path.join(ROOT, "kling-prompts.json")))
    failures = []
    for p in prompts:
        try:
            generate(p["name"], p["prompt"])
        except Exception as e:
            print(f"FAIL {p['name']}: {e}", file=sys.stderr); failures.append(p["name"])
    if failures:
        print(f"failed clips (rerun the workflow to retry just these): {failures}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
