# Code review and test report

Reviewed: all 11 `SKILL.md` files, `hooks.json`, `voice.md`, the plugin config and all 6 Python tools,
read line by line, plus 5 sample scripts run through the tools. Date: 2026-11-27.

## Verdict

**GO as a workflow toolkit. NO-GO as an autonomous agent.** It does not, and is not built to, run a
channel: nothing connects to YouTube, and every skill ends with the user deciding. With the fixes
below, the tools are safe to use daily. The decisions that move views (the topic, the final hook, the
thumbnail and the delivery) stay human.

## Bugs found and fixed

| # | Where | Bug | Severity | Status |
| --- | --- | --- | --- | --- |
| 1 | `hookscore.py` | Keyword stuffing scored STRONG (77) and beat real hooks | High | Fixed: diminishing returns plus a stuffing penalty (now 40) |
| 2 | `retention.py` | A Short under 100s exported in seconds was misread as a percent axis, so the cliff timestamps were lost | High for Shorts | Fixed: reads the csv header, adds `--axis`, warns when it has to guess |
| 3 | `swipe.py` | SKILL.md says to collect with `yt-dlp --flat-playlist -J`, but the tool could not read that output (0 videos, silently) | High | Fixed: reads the yt-dlp shape (`entries`, `view_count`, channel on the playlist) |
| 4 | `retention.py` | `--duration 600 file.csv` (flag first) printed the help text instead of running | Medium | Fixed: arguments work in any order |
| 5 | `deadair.py` | A zero-length transcript crashed (division by zero) | Low | Fixed |
| 6 | plugin config, README | The install steps pointed at the original repo, so installing would have pulled the unfixed code | Medium | Fixed: they point at this fork, with credit kept |

## Skill-file review

- **Good:** consistent rules across all 11: never publish, never invent a number, read the voice
  file, end with "ship it, or change it?". `/yt-plan`, `/yt-audit` and `/yt-retention` each insist on
  ONE fix, which is the right discipline.
- **Fixed:** `/yt-shorts` writes spoken first lines but did not read `voice.md`. It does now.
- **Fixed:** `/yt-viral` depends on `../yt-script/hooks.json`, so installing one folder alone breaks
  it. This is now documented.
- **Limit:** the voice file lives at `~/.claude/youtube/voice.md`. It works in Claude Code. In a
  plain chat, paste the file's contents into the conversation instead.
- **Limit:** `/yt-audit` asks Claude to look at thumbnails at feed size, which needs the images
  supplied. No tool checks thumbnails.
- **Gap, now covered:** nothing checked the script body against the `/yt-script` rules. The new
  `scriptlint.py` checks the structure, on-screen notes, early subscribe pitches, one call to action,
  filler, unfilled figures and runtime.

## Sample scripts: tool scores and editor's rating

The tools check rules. The editor's rating is a human judgement of whether the video would hold a
viewer.

| Sample | Best hook (tool rank) | Best title (title.py) | scriptlint | Editor's rating |
| --- | --- | --- | --- | --- |
| 01 Desk mat review | "I almost returned..." ranked 3rd of 5 (45) | "The $40 Desk Mat I Almost Sent Back" 100 | 95, 2 figures to fill | **8/10**: strong before/after and an honest limits beat. Runs only 1:34; needs B-roll and depth to reach 6-8 min |
| 02 SIP mistakes (India) | "If you stopped your SIP..." ranked 3rd (43) | "3 SIP Mistakes That Cost You Lakhs" 100 | 100 | **8/10**: clear, useful, compliant framing. Keep it education-only (SEBI rules for finfluencers) |
| 03 AI pack teardown | "You have seen the reel..." ranked 1st (55) | "AI Scored Clickbait 77 and My Real Hook 39" 94 | 100 | **8.5/10**: best of the set, because it rests on our own data that nobody else has |
| 04 Short (44s) | "An AI tool rated clickbait 77..." (43) | "AI Scored Clickbait 77. My Hook Got 39." 100 | 100 | **7.5/10**: clean loop, but it depends on clear on-screen numbers |
| 05 Control (bad on purpose) | all 3 hooks WEAK (23-40) | 30 and 62 | **40**, with 4 rule failures | **2/10**. The tools caught every planted problem |

### What the tests say about the tools

- **The hook scorer ranks, it doesn't judge.** In 3 of 3 sets, the deliberately flat "summary" hook
  ("Here is my review...") ranked last: that is the reliable signal. But all the good hand-written
  hooks scored 36-55 and were labelled WEAK, and the hook an editor would pick ranked 3rd twice. Use
  it to catch weak lines, never to choose the winner. `--calibrate` decides whether to trust it on
  your own channel.
- **The title checker is useful but strict.** It flags every title over 40 characters as a "mobile"
  issue, which is most good titles. Read it as a reminder that the subject must come first, not as a
  failure.
- **The script checker caught 4 of 4 planted faults** in the control and passed the good scripts
  cleanly.
- **The data tools** (silence cutter, chapter maker, retention reader, outlier finder) all handle
  normal input, alternative formats and bad input after the fixes. They are covered by 18 automated
  tests.

## How to run the checks

```bash
python3 -m unittest discover -s tests -v                    # 18 tests, standard library only
python3 skills/yt-script/scriptlint.py samples/03-ai-youtube-pack-test/script.md
python3 skills/yt-script/hookscore.py samples/01-desk-mat-review/hooks.txt
python3 skills/yt-package/title.py samples/01-desk-mat-review/titles.txt
```

GitHub Actions runs the test suite on every push (`.github/workflows/tests.yml`).

## Recommendation

Proceed with `PLAN.md`. Start with sample 03 as the first video: it has the strongest angle and every
figure in it comes from our own tests. Fill in `voice.md` before scripting anything else.
