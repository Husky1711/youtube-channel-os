#!/usr/bin/env python3
"""scriptlint.py - check a finished script against the rules in yt-script/SKILL.md.

    python3 scriptlint.py script.md
    python3 scriptlint.py script.md --json

The script is markdown with one "## SECTION" heading per beat (HOOK, TURN, BEAT..., PAYOFF, CLOSE)
and an [ON SCREEN: ...] line in each. Spoken words are everything else that is not a heading, a
note line or an [ON SCREEN] line.

Checks, each tied to a rule in SKILL.md:
  structure   HOOK, TURN, PAYOFF and CLOSE all present
  on-screen   every spoken section has an [ON SCREEN: ...] line
  early-ask   no subscribe/like/bell/"welcome back"/"before we get started" before the body
  one-ask     the CLOSE asks for one thing, not several
  filler      filler and hype words across the whole script
  unfilled    [YOUR FIGURE]-style placeholders still in the text - do not record yet
  runtime     spoken words at 150 words per minute
"""
import json, re, sys

WPM = 150
EARLY = re.compile(r"\b(subscribe|hit the bell|like the video|smash|welcome back|before we get started|"
                   r"second channel)\b", re.I)
ASKS = re.compile(r"\b(subscribe|like|comment|share|follow|join|check out|click|watch|download|bell)\b", re.I)
FILLER = re.compile(r"\b(basically|literally|super|insane|amazing|game.?changer|crazy|so yeah|"
                    r"you guys|hey guys)\b", re.I)
PLACEHOLDER = re.compile(r"\[(YOUR [A-Z ]+|TODO|TK|XX+)\]")

def parse(text):
    secs, cur = [], None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+)", line)
        if m:
            cur = {"name": m.group(1).strip(), "spoken": [], "screen": 0}
            secs.append(cur)
        elif cur is not None and line.strip():
            if re.match(r"^\s*\[ON SCREEN", line, re.I): cur["screen"] += 1
            else: cur["spoken"].append(line.strip())
    return secs

def kind(name):
    n = name.upper()
    for k in ("HOOK", "TURN", "PAYOFF", "CLOSE", "LOOP"):
        if n.startswith(k): return k
    return "BODY"

def lint(text):
    secs = parse(text)
    issues, good = [], []
    kinds = [kind(s["name"]) for s in secs]
    missing = [k for k in ("HOOK", "PAYOFF") if k not in kinds]
    if "TURN" not in kinds and "BODY" not in kinds: missing.append("TURN/BODY")
    if "CLOSE" not in kinds and "LOOP" not in kinds: missing.append("CLOSE")
    if missing: issues.append(("structure", "missing " + ", ".join(missing)))
    else: good.append("hook, turn, payoff and close all present")
    blind = [s["name"] for s in secs if s["spoken"] and not s["screen"]]
    if blind: issues.append(("on-screen", f"{len(blind)} section(s) with nothing on screen: " + "; ".join(blind[:4])))
    else: good.append("every section has an [ON SCREEN] line")
    early = " ".join(" ".join(s["spoken"]) for s in secs if kind(s["name"]) in ("HOOK", "TURN"))
    hits = sorted({m.group(0).lower() for m in EARLY.finditer(early)})
    if hits: issues.append(("early-ask", "before the body: " + ", ".join(hits) + " - the 0:30 cliff"))
    else: good.append("no channel intro or subscribe pitch before the body")
    close = " ".join(" ".join(s["spoken"]) for s in secs if kind(s["name"]) == "CLOSE")
    asks = sorted({m.group(0).lower() for m in ASKS.finditer(close)})
    if len(asks) > 1: issues.append(("one-ask", f"{len(asks)} asks in the close ({', '.join(asks)}) - keep one"))
    elif close: good.append("one ask in the close")
    spoken = " ".join(" ".join(s["spoken"]) for s in secs)
    fill = [m.group(0).lower() for m in FILLER.finditer(spoken)]
    if len(fill) >= 3: issues.append(("filler", f"{len(fill)} filler/hype words: " + ", ".join(sorted(set(fill)))))
    elif fill: good.append(f"only {len(fill)} filler word(s)")
    else: good.append("no filler or hype words")
    ph = PLACEHOLDER.findall(text)
    if ph: issues.append(("unfilled", f"{len(ph)} placeholder(s) to fill before recording: " + ", ".join(sorted(set(ph)))))
    nwords = len(re.findall(r"[A-Za-z0-9'$%.,]+", spoken))
    secs_rt = nwords / WPM * 60
    score = max(0, min(100, 100 - 15 * len([i for i in issues if i[0] != "unfilled"]) - (5 if ph else 0)))
    return {"score": score, "words": nwords, "runtime_sec": round(secs_rt), "issues": issues, "good": good}

def main():
    a = sys.argv[1:]
    as_json = "--json" in a; a = [x for x in a if x != "--json"]
    if not a: print(__doc__); sys.exit(1)
    r = lint(open(a[0], encoding="utf-8").read())
    if as_json: print(json.dumps(r, indent=1)); return
    m, s = divmod(r["runtime_sec"], 60)
    print(f"\n  {a[0]}   {r['words']} spoken words, ~{m}:{s:02d} at {WPM} wpm   score {r['score']}/100")
    for k, msg in r["issues"]: print(f"    x  {k:<10} {msg}")
    for msg in r["good"]:      print(f"    ok            {msg}")
    print()

if __name__ == "__main__":
    main()
