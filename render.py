#!/usr/bin/env python3
"""Confuciousay renderer: plan.csv rows -> ready-to-publish media.
Reels: branded frame (safe-zone template ported from make_reels.py) -> 7s slow-zoom MP4 with baked audio.
Carousels: generated slide PNGs copied into media/.
Idempotent: skips media that already exists. Runs in GitHub Actions (ubuntu, ffmpeg, pillow, matplotlib).

Usage: python3 scripts/render.py --start 2026-07-16 --days 8
"""
import os, csv, sys, glob, argparse, subprocess, shutil, tempfile
from datetime import date, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
MEDIA = os.path.join(ROOT, "media")
AUDIO = os.path.join(ROOT, "audio")
os.makedirs(MEDIA, exist_ok=True)

import matplotlib
MPL = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")
def font(name, size): return ImageFont.truetype(os.path.join(MPL, name), size)

SERIF, SERIF_B, SANS_B, SANS = "STIXGeneral.ttf", "STIXGeneralBol.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf"
W, H = 1080, 1920
PARCHMENT, PARCH_EDGE = (243,233,210), (224,210,181)
GOLD, INK, JADE, MIST = (199,163,90), (28,28,28), (47,74,63), (107,123,130)
CHARCOAL, CHARC_EDGE, CREAMTEXT, GOLD_BR = (26,24,20), (16,14,11), (240,231,211), (212,178,108)
BAND_TOP, BAND_BOT, SEAL_Y, HANDLE_Y = 250, 1500, 1360, 1430

def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= max_w: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def fit(draw, text, fontfile, max_w, max_lines, start, floor, max_block_h):
    s = start
    while s > floor:
        f = font(fontfile, s); lines = wrap(draw, text, f, max_w)
        asc, desc = f.getmetrics(); bh = int((asc+desc)*1.2)*len(lines)
        if len(lines) <= max_lines and bh <= max_block_h: return f, lines
        s -= 3
    f = font(fontfile, floor); return f, wrap(draw, text, f, max_w)

def block(draw, lines, f, y, fill, gap=1.2, shadow=None):
    asc, desc = f.getmetrics(); lh = int((asc+desc)*gap)
    for ln in lines:
        tw = draw.textlength(ln, font=f); x = (W-tw)/2
        if shadow: draw.text((x+2, y+2), ln, font=f, fill=shadow)
        draw.text((x, y), ln, font=f, fill=fill); y += lh
    return y

def seal(d, cx, cy, r, col):
    d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=col, width=4)
    d.ellipse([cx-r+12, cy-r+12, cx+r-12, cy+r-12], outline=col, width=1)
    d.ellipse([cx-6, cy-6, cx+6, cy+6], fill=col)

def parchment_bg():
    img = Image.new("RGB", (W,H), PARCHMENT)
    mask = Image.new("L", (W,H), 0)
    ImageDraw.Draw(mask).ellipse([int(W*0.04), int(H*0.03), int(W*0.96), int(H*0.97)], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(150))
    return Image.composite(img, Image.new("RGB", (W,H), PARCH_EDGE), mask)

def charcoal_bg():
    img = Image.new("RGB", (W,H), CHARCOAL)
    glow = Image.new("L", (W,H), 0)
    ImageDraw.Draw(glow).ellipse([W*0.12, H*0.32, W*0.88, H*0.9], fill=55)
    glow = glow.filter(ImageFilter.GaussianBlur(170))
    img = Image.composite(Image.new("RGB", (W,H), (54,44,26)), img, glow)
    v = Image.new("L", (W,H), 0)
    ImageDraw.Draw(v).ellipse([int(W*0.05), int(H*0.04), int(W*0.95), int(H*0.96)], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(140))
    return Image.composite(img, Image.new("RGB", (W,H), CHARC_EDGE), v)

def compose(img, quote, source, dark=False, transparent=False):
    d = ImageDraw.Draw(img)
    txt = CREAMTEXT if dark else INK
    gold = GOLD_BR if dark else GOLD
    attrc = (200,190,168) if dark else JADE
    srcc = (150,140,118) if dark else MIST
    shadow = (0,0,0) if (dark or transparent) else None
    if not transparent:
        d.rectangle([56, BAND_TOP, W-56, BAND_BOT], outline=gold, width=2)
    kf = font(SANS_B, 30); k = " ".join(list("CONFUCIUS")); kw = d.textlength(k, font=kf)
    ky = BAND_TOP + 50
    if shadow: d.text(((W-kw)/2+2, ky+2), k, font=kf, fill=(0,0,0))
    d.text(((W-kw)/2, ky), k, font=kf, fill=gold)
    d.line([(W/2-90, ky+58), (W/2+90, ky+58)], fill=gold, width=2)
    qm = font(SERIF_B, 150); qmy = ky + 110
    if shadow: d.text((W/2 - d.textlength('“', font=qm)/2+2, qmy+2), '“', font=qm, fill=(0,0,0))
    d.text((W/2 - d.textlength('“', font=qm)/2, qmy), '“', font=qm, fill=gold)
    f, lines = fit(d, quote, SERIF, W-180, 6, 92, 50, 520)
    asc, desc = f.getmetrics(); bh = int((asc+desc)*1.2)*len(lines)
    y = 560 + max(0, (1120-560-bh)//2)
    end = block(d, lines, f, y, txt, 1.2, shadow=shadow)
    af = font(SANS_B, 38); a = " ".join(list("CONFUCIUS")); aw = d.textlength(a, font=af)
    ay = min(end+46, 1150)
    if shadow: d.text(((W-aw)/2+2, ay+2), a, font=af, fill=(0,0,0))
    d.text(((W-aw)/2, ay), a, font=af, fill=attrc)
    sf = font(SANS, 28); sw = d.textlength(source, font=sf)
    if shadow: d.text(((W-sw)/2+2, ay+52+2), source, font=sf, fill=(0,0,0))
    d.text(((W-sw)/2, ay+52), source, font=sf, fill=srcc)
    seal(d, W/2, SEAL_Y, 32, gold)
    hf = font(SANS_B, 28); h = "@confuciousay"; hw = d.textlength(h, font=hf)
    if shadow: d.text(((W-hw)/2+2, HANDLE_Y+2), h, font=hf, fill=(0,0,0))
    d.text(((W-hw)/2, HANDLE_Y), h, font=hf, fill=gold)
    return img

def pick_audio(index):
    tracks = sorted(glob.glob(os.path.join(AUDIO, "*.mp3")) + glob.glob(os.path.join(AUDIO, "*.m4a")) + glob.glob(os.path.join(AUDIO, "*.wav")))
    if not tracks: return None
    return tracks[index % len(tracks)]

def frame_to_reel(frame_png, out_mp4, audio_file, kling_clip=None, overlay_png=None):
    """7s vertical MP4. Default: slow zoom on the frame. If a Kling clip is given: clip as bg, overlay on top."""
    dur, fps = 7, 30
    if kling_clip and overlay_png and os.path.exists(kling_clip):
        vf = "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[bg];[bg][1:v]overlay=0:0[v]"
        cmd = ["ffmpeg", "-y", "-stream_loop", "-1", "-i", kling_clip, "-loop", "1", "-i", overlay_png]
        if audio_file: cmd += ["-i", audio_file]
        cmd += ["-filter_complex", vf, "-map", "[v]"]
        cmd += (["-map", "2:a", "-af", f"afade=t=out:st={dur-1}:d=1", "-c:a", "aac", "-b:a", "128k"] if audio_file else ["-an"])
        cmd += ["-t", str(dur), "-r", str(fps), "-c:v", "libx264", "-crf", "22", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out_mp4]
    else:
        vf = (f"scale={W*2}:{H*2},zoompan=z='min(zoom+0.0004,1.08)':d={dur*fps}"
              f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={fps},format=yuv420p")
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", frame_png]
        if audio_file: cmd += ["-i", audio_file]
        cmd += ["-vf", vf]
        cmd += (["-map", "0:v", "-map", "1:a", "-af", f"afade=t=out:st={dur-1}:d=1", "-c:a", "aac", "-b:a", "128k"] if audio_file else ["-an"])
        cmd += ["-t", str(dur), "-c:v", "libx264", "-crf", "22", "-movflags", "+faststart", out_mp4]
    subprocess.run(cmd, check=True, capture_output=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default=date.today().isoformat())
    ap.add_argument("--days", type=int, default=8)
    args = ap.parse_args()
    end = (date.fromisoformat(args.start) + timedelta(days=args.days - 1)).isoformat()

    rows = [r for r in csv.DictReader(open(os.path.join(ROOT, "plan.csv"))) if args.start <= r["date"] <= end]
    made, skipped, carousels_needed = 0, 0, set()
    for i, r in enumerate(rows):
        if r["type"] == "carousel":
            carousels_needed.add(r["carousel_id"]); continue
        out = os.path.join(MEDIA, r["media_key"] + ".mp4")
        if os.path.exists(out): skipped += 1; continue
        with tempfile.TemporaryDirectory() as td:
            frame = os.path.join(td, "frame.png")
            dark = r["variant"].strip().lower().startswith("b")
            img = charcoal_bg() if dark else parchment_bg()
            compose(img, r["quote_modernized"].strip().strip('"'), r["source"].strip(), dark=dark)
            img.save(frame)
            kling = None; overlay = None
            if r.get("kling_clip"):
                kc = os.path.join(ROOT, "kling-clips", r["kling_clip"])
                if os.path.exists(kc):
                    kling = kc
                    ov = Image.new("RGBA", (W, H), (0,0,0,0))
                    compose(ov, r["quote_modernized"].strip().strip('"'), r["source"].strip(), dark=True, transparent=True)
                    overlay = os.path.join(td, "overlay.png"); ov.save(overlay)
            frame_to_reel(frame, out, pick_audio(i), kling, overlay)
        made += 1
    # carousels: generate slides if missing, then copy into media/
    if carousels_needed:
        gen_dir = os.path.join(ROOT, "launch-carousels")
        if not all(os.path.isdir(os.path.join(gen_dir, f"carousel_{n}")) for n in carousels_needed):
            subprocess.run([sys.executable, os.path.join(ROOT, "carousels.py")], check=True, cwd=ROOT, capture_output=True)
        for n in sorted(carousels_needed):
            dst = os.path.join(MEDIA, f"carousel_{n}")
            if not os.path.isdir(dst):
                shutil.copytree(os.path.join(gen_dir, f"carousel_{n}"), dst); made += 1
    print(f"rendered={made} skipped={skipped} window={args.start}..{end}")

if __name__ == "__main__":
    main()
