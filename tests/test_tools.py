#!/usr/bin/env python3
"""End-to-end tests for the six tools plus scriptlint. Standard library only.

    python3 -m unittest discover -s tests -v
"""
import json, os, subprocess, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SK = os.path.join(ROOT, "skills")

def run(tool, *args):
    p = subprocess.run([sys.executable, "-I", os.path.join(SK, tool), *args],
                       capture_output=True, text=True, timeout=30)
    return p.returncode, p.stdout + p.stderr

def jrun(tool, *args):
    code, out = run(tool, *args, "--json")
    assert code == 0, out
    return json.loads(out)

def srt(cues):
    def ts(t):
        h, r = divmod(t, 3600); m, s = divmod(r, 60)
        return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".", ",")
    return "\n".join(f"{i+1}\n{ts(a)} --> {ts(b)}\n{t}\n" for i, (a, b, t) in enumerate(cues))

class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
    def f(self, name, text):
        p = os.path.join(self.d, name)
        with open(p, "w", encoding="utf-8") as fh: fh.write(text)
        return p

    # ---------- deadair ----------
    def test_deadair_finds_dead_filler_repeat(self):
        p = self.f("t.srt", srt([(0, 3, "So the first thing about this mat"), (3.2, 4, "um"),
                                 (4.2, 8, "So the first thing about this mat is the smell"),
                                 (12, 15, "and then day three changed everything")]))
        kinds = sorted({c["kind"] for c in jrun("yt-edit/deadair.py", p)["cuts"]})
        self.assertEqual(kinds, ["DEAD", "FILLER", "REPEAT"])

    def test_deadair_vtt_and_whisper_json(self):
        v = self.f("t.vtt", "WEBVTT\n\n00:00.000 --> 00:03.000\nhello there friends\n\n"
                            "00:05.000 --> 00:08.000\nsecond line here\n")
        self.assertEqual(len(jrun("yt-edit/deadair.py", v)["cuts"]), 1)
        j = self.f("w.json", json.dumps({"segments": [{"start": 0, "end": 2, "text": "a b c"},
                                                      {"start": 4, "end": 6, "text": "d e f"}]}))
        self.assertEqual(len(jrun("yt-edit/deadair.py", j)["cuts"]), 1)

    def test_deadair_empty_file_fails_cleanly(self):
        code, out = run("yt-edit/deadair.py", self.f("e.srt", ""))
        self.assertEqual(code, 1); self.assertIn("no cues", out)

    def test_deadair_zero_duration_no_crash(self):
        code, out = run("yt-edit/deadair.py", self.f("z.srt", srt([(0, 0, "um")])))
        self.assertNotIn("Traceback", out)

    # ---------- chapters ----------
    def long_transcript(self):
        cues, t = [], 0.0
        for topic in ["keyboard switches typing sound", "desk mat thickness smell", "monitor arm height posture"]:
            for i in range(10):
                cues.append((t, t + 4, f"talking about {topic} detail {i}")); t += 4.2
            t += 3.0  # a real pause between sections
        return self.f("long.srt", srt(cues))

    def test_chapters_valid_on_three_topics(self):
        r = jrun("yt-chapters/chapters.py", self.long_transcript(), "--target", "3")
        self.assertTrue(r["valid"]); self.assertEqual(r["chapters"][0]["start"], 0.0)
        self.assertTrue(all(c["seconds"] >= 10 for c in r["chapters"]))

    def test_chapters_refuses_short(self):
        code, out = run("yt-chapters/chapters.py", self.f("s.srt", srt([(0, 2, "hi"), (3, 5, "bye")])))
        self.assertEqual(code, 1)

    # ---------- retention ----------
    def ret_csv(self, xs, ys, header="Video position (%),Audience retention (%)"):
        return self.f("r.csv", header + "\n" + "\n".join(f"{x},{y}" for x, y in zip(xs, ys)))

    def test_retention_percent_axis_with_duration(self):
        xs = list(range(0, 101)); ys = [100 - x * 0.3 - (30 if x >= 5 else 0) for x in xs]
        r = jrun("yt-retention/retention.py", self.ret_csv(xs, ys), "--duration", "600")
        self.assertAlmostEqual(r["hook_leak"], 31.5, delta=0.6)
        self.assertEqual(r["cliffs"][0]["at_seconds"], 24.0)

    def test_retention_flag_before_file(self):
        xs = list(range(0, 101)); ys = [100 - x * 0.5 for x in xs]
        code, out = run("yt-retention/retention.py", "--duration", "600", self.ret_csv(xs, ys))
        self.assertEqual(code, 0, out)
        self.assertIn("lost in the opening", out, "argument order should not matter")

    def test_retention_seconds_axis_short_video(self):
        # A 60-second Short exported in SECONDS must not be read as a percentage axis.
        xs = list(range(0, 61)); ys = [100 - x * 0.5 - (20 if x >= 3 else 0) for x in xs]
        r = jrun("yt-retention/retention.py", self.ret_csv(xs, ys, "Video position (seconds),Audience retention (%)"))
        self.assertIsNotNone(r["cliffs"][0]["at_seconds"])
        self.assertEqual(r["cliffs"][0]["at_seconds"], 2.0)

    def test_retention_too_few_points(self):
        code, out = run("yt-retention/retention.py", self.ret_csv([0, 1], [100, 90]))
        self.assertEqual(code, 1)

    # ---------- swipe ----------
    def test_swipe_outlier_and_thin_channel(self):
        rows = [{"channel": "A", "title": f"I tried {i}", "views": 1000 * (5 if i == 0 else 1)} for i in range(5)]
        rows.append({"channel": "B", "title": "x", "views": 9})
        r = jrun("yt-viral/swipe.py", self.f("c.json", json.dumps(rows)), "--min", "2")
        self.assertEqual(len(r["outliers"]), 1); self.assertEqual(r["skipped_thin_channels"], [["B", 1]])

    def test_swipe_reads_ytdlp_flat_playlist(self):
        # The SKILL.md recommends `yt-dlp --flat-playlist -J`; its shape is {"channel":..,"entries":[..]}.
        d = {"channel": "Chan", "entries": [{"title": f"v{i}", "view_count": 100 * (6 if i == 0 else 1),
                                             "url": "u", "duration": 60} for i in range(5)]}
        r = jrun("yt-viral/swipe.py", self.f("y.json", json.dumps(d)), "--min", "2")
        self.assertEqual(len(r["outliers"]), 1)

    # ---------- title ----------
    def test_title_duplicate_and_shouting(self):
        r = jrun("yt-package/title.py", "--title", "INSANE DESK MAT SECRET REVEALED", "--thumb", "DESK MAT")
        kinds = {k for k, _ in r[0]["issues"]}
        self.assertTrue({"shouting", "duplicate", "vague"} <= kinds)

    # ---------- hookscore ----------
    def test_hook_stuffing_docked(self):
        soup = jrun("yt-script/hookscore.py", "--hook", "You will never believe why you lose 3 hours before you quit, but nobody knows how")[0]
        real = jrun("yt-script/hookscore.py", "--hook", "I almost returned this $40 desk mat. On day 3, my wrist pain was gone.")[0]
        self.assertLessEqual(soup["verdict"], real["verdict"] + 5)

    def test_hook_summary_line_ranks_last(self):
        p = self.f("h.txt", "I almost returned this $40 desk mat. On day 3, my wrist pain was gone.\n"
                            "Here is my review of the desk mat everyone is talking about.\n"
                            "This $40 mat did what my $300 wrist brace never did.\n")
        r = jrun("yt-script/hookscore.py", p)
        self.assertTrue(r[-1]["hook"].startswith("Here is my review"))

    def test_calibrate_small_sample_no_verdict(self):
        p = self.f("m.csv", "hook,views\n" + "\n".join(f"hook number {i} about you,{i * 10}" for i in range(9)))
        code, out = run("yt-script/hookscore.py", "--calibrate", p)
        self.assertEqual(code, 0); self.assertIn("rho", out)

    # ---------- scriptlint ----------
    def test_scriptlint_flags_control(self):
        r = jrun("yt-script/scriptlint.py", os.path.join(ROOT, "samples", "05-control-bad", "script.md"))
        kinds = {k for k, _ in r["issues"]}
        self.assertTrue({"on-screen", "early-ask", "one-ask", "filler"} <= kinds)

    def test_scriptlint_passes_good_samples(self):
        for s in ("02-sip-mistakes-india", "03-ai-youtube-pack-test"):
            r = jrun("yt-script/scriptlint.py", os.path.join(ROOT, "samples", s, "script.md"))
            self.assertEqual(r["issues"], [], s)

if __name__ == "__main__":
    unittest.main()
