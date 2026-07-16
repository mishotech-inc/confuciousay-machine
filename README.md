# confuciousay-machine

Self-running content machine for the @confuciousay Instagram brand. Renders, publishes, and measures 3 posts/day with zero manual steps. Full runbook: `confuciousay_automation_v2.md` in the Cowork project folder (PROJECTS/Confucious Brand/).

## How it runs

- `plan.csv` is the single source of truth: one row per slot (date, time, type, quote, caption, hashtags, variant, media key). Claude extends and reweights it weekly.
- `stage.yml` (Sun 3am PT + manual): renders the coming week from plan.csv into `media/` (reels as 7s slow-zoom MP4s with audio from `audio/`, carousels as slide PNGs), then pins `manifest.json` to the media commit SHA so CDN URLs are immediate.
- `publish.yml` (8am / 12pm / 6pm PT): posts the due slot via the Instagram API, logs to `logs/posted.json`. Idempotent, one slot per run, missed slots recycle instead of back-posting.
- `insights.yml` (Sun 6am PT): pulls reach / saves / shares per post into `logs/insights.json` for the A/B scoreboard.
- `refresh-token.yml` (monthly): rotates the 60-day Instagram token using `GH_PAT`.
- `kling.yml` (manual): one-shot generation of the 8 Confucius motion clips via fal.ai into `kling-clips/`. Once present, plan rows with a `kling_clip` value render as cinematic reels automatically.

## Secrets

`IG_USER_ID`, `IG_ACCESS_TOKEN` (60-day, auto-rotated), `GH_PAT` (repo-scoped, secrets:write), `FAL_KEY`.

## Maintenance

November 1: publish crons shift one hour for PST (see comments in publish.yml). If a publish run fails, the red workflow email is the alert; the weekly Claude pass reconciles missed slots.
