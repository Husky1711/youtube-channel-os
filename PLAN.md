# The 4-week test

These skills are a process, not an autopilot. This plan decides, with numbers, which of them earn a
place in how the channel is run. Fill in `templates/tracker.csv` as you go.

## Week 0 - baseline (before using any skill)

From YouTube Studio, for your last 5 videos (or your first 2 if the channel is new), record:

| metric | where in Studio |
| --- | --- |
| Impressions click-through rate | Analytics -> Reach |
| Retention at 0:30 (%) | Video -> Engagement -> Audience retention |
| Average view duration | Analytics -> Engagement |
| Views after 7 days | Video -> Analytics |
| Hours spent making the video | your own log - be honest |

Then fill in `templates/voice.md` and copy it to `~/.claude/youtube/voice.md`. Do not skip this.

## Weeks 1-4 - one fixed pipeline per video

1. `/yt-viral` - collect 4+ videos from 5-8 channels in your niche, pick an idea that beat its
   channel by 2x or more and that you can actually make this week.
2. `/yt-script` - five hooks, keep the best two, YOU pick the final one.
3. `/yt-package` - title and thumbnail linted together.
4. Record and edit. `/yt-edit` on the transcript if you edit yourself.
5. `/yt-seo` and `/yt-chapters` before upload.
6. 48 hours after upload: `/yt-comment`.
7. 7 days after upload: `/yt-retention` on the export, log the numbers in the tracker.

From video 5 onward, run `python3 skills/yt-script/hookscore.py --calibrate mine.csv` with your own
hooks and their 30-second retention. If the score does not track your results, stop using it to
pick hooks.

## Week 4 - the decision

Keep a skill only if it moved a number:

| skill | keep if |
| --- | --- |
| `/yt-viral` | ideas from it beat your baseline views |
| `/yt-script` | 0:30 retention held or rose, and scripting time fell |
| `/yt-package` | click-through rate held or rose |
| `/yt-edit`, `/yt-chapters`, `/yt-seo` | they saved time without hurting retention |
| `/yt-retention` | it named a cliff you then fixed in the next video |

The judgement stays yours: the topic, the final hook, the thumbnail and the delivery. Four weeks is
a small sample - treat the result as direction, not proof.
