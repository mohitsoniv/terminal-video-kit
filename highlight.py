#!/usr/bin/env python3
"""
terminal-video-kit engine
  python3 highlight.py calibrate
  python3 highlight.py check <topic_dir>
  python3 highlight.py step  <topic_dir> <NN>
"""
import json, math, os, re, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

KIT = os.path.dirname(os.path.abspath(__file__))
CALIB = os.path.join(KIT, "calib", "calib.json")
W, H = 1280, 720
VOICE = os.environ.get("VOICE", "hi-IN-MadhurNeural")
PROMPT = os.environ.get("PROMPT_TEXT", "$ ")
FONT = os.environ.get("POPUP_FONT", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf")
GAP = 0.35

def run(cmd, **kw): return subprocess.run(cmd, check=True, **kw)

def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())

# ---------------- calibration ----------------
def calibrate():
    mp4 = os.path.join(KIT, "calib", "calib-term.mp4")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-sseof", "-0.2", "-i", mp4, "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    if len(raw) < W * H: sys.exit("Calibration frame nahi mila")
    img = raw[:W * H]
    bands, cur = [], None
    for y in range(H):
        row = img[y * W:(y + 1) * W]
        xs = [x for x in range(W) if row[x] > 140]
        if len(xs) > 8:
            if cur is None: cur = [y, y, min(xs), max(xs)]
            else: cur[1] = y; cur[2] = min(cur[2], min(xs)); cur[3] = max(cur[3], max(xs))
        elif cur is not None:
            bands.append(cur); cur = None
    if cur: bands.append(cur)
    if len(bands) < 5: sys.exit(f"Calibration fail: sirf {len(bands)} bands mile")
    hs = sorted(b[1] - b[0] + 1 for b in bands); mh = hs[len(hs) // 2]
    bands = [b for b in bands if abs((b[1] - b[0] + 1) - mh) <= 2]
    widths = [b[3] - b[2] + 1 for b in bands]
    short = sorted(w for w in widths if w <= min(widths) * 1.15)
    long_ = sorted(w for w in widths if w >= max(widths) * 0.95)
    cw = short[len(short) // 2] / 10.0
    cols = round(long_[len(long_) // 2] / cw)
    tops = [b[0] for b in bands]
    diffs = sorted(tops[i + 1] - tops[i] for i in range(len(tops) - 1))
    pitch = diffs[len(diffs) // 2]
    cal = dict(cw=cw, cols=cols, pitch=pitch, top0=tops[0],
               x0=sorted(b[2] for b in bands)[len(bands) // 2],
               rows=round((tops[-1] - tops[0]) / pitch) + 2)
    json.dump(cal, open(CALIB, "w"), indent=1)
    print("  Calibration:", cal)

# ---------------- step files ----------------
def read_step(topic, st):
    """returns dict(kind, cmd|lines, wait)"""
    for kind, ext in (("session", ".session"), ("cmd", ".cmd")):
        p = os.path.join(topic, "steps", st + ext)
        if not os.path.exists(p): continue
        wait, body = 3.0, []
        for ln in open(p, encoding="utf-8"):
            s = ln.rstrip("\n")
            if not s.strip(): continue
            m = re.match(r"#\s*wait\s+([\d.]+)", s.strip())
            if m: wait = float(m.group(1)); continue
            if s.lstrip().startswith("#"): continue
            body.append(s.strip())
        if not body: sys.exit(f"steps/{st}{ext} khaali hai")
        if kind == "cmd" and len(body) > 1:
            sys.exit(f"steps/{st}.cmd mein sirf EK command honi chahiye (kai lines ke liye .session use karo)")
        return dict(kind=kind, wait=wait, cmd=body[0], lines=body)
    sys.exit(f"steps/{st}.cmd ya steps/{st}.session nahi mili")

def _clean(raw):
    text = raw.decode("utf-8", "replace").replace("\r\n", "\n").replace("\r", "")
    text = re.sub(r"\x1b\][0-9];[^\x07]*\x07", "", text)
    text = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text)
    lines = text.split("\n")
    while lines and lines[-1] == "": lines.pop()
    return lines

def run_pre(topic, st):
    pre = os.path.join(topic, "steps", f"{st}.pre")
    if os.path.exists(pre):
        r = subprocess.run(["bash", pre], cwd=topic, capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(f"steps/{st}.pre fail hui:\n{r.stdout}\n{r.stderr}")

def capture(topic, step, cal, timeout):
    env = dict(os.environ, PAGER="cat", PSQL_PAGER="cat", GIT_PAGER="cat", LESS="-FRX")
    cols, rows = cal["cols"], max(cal["rows"], 40)
    with tempfile.TemporaryDirectory() as td:
        inner = os.path.join(td, "inner.sh")
        if step["kind"] == "cmd":
            open(inner, "w").write(step["cmd"] + "\n")
            drive = f"script -qfc \"stty cols {cols} rows {rows}; bash {inner}\" /dev/null"
        else:
            open(inner, "w").write(step["lines"][0] + "\n")
            feed = "".join("sleep 0.7; cat %s;" % os.path.join(td, f"l{i}")
                           for i in range(1, len(step["lines"])))
            for i, ln in enumerate(step["lines"][1:], 1):
                open(os.path.join(td, f"l{i}"), "w").write(ln + "\n")
            drive = (f"{{ sleep 0.8; {feed} sleep 1.2; }} | "
                     f"script -qfc \"stty cols {cols} rows {rows}; bash {inner}\" /dev/null")
        try:
            out = subprocess.run(["bash", "-c", drive], capture_output=True,
                                 cwd=topic, timeout=timeout, env=env).stdout
        except subprocess.TimeoutExpired:
            sys.exit(f"Step {timeout}s mein khatam nahi hua (interactive/lambi command?)")
    return _clean(out)

def screen_rows(step, out_lines, cols):
    logical = [PROMPT + step["cmd"]] + out_lines   # screen par pehli line hamesha prompt + command
    mapping, r = [], 0
    for ln in logical:
        n = max(1, math.ceil(len(ln) / cols)) if len(ln) > cols else 1
        mapping.append((ln, list(range(r, r + n)))); r += n
    return mapping, r + 1

def read_narration(topic, st):
    items = []
    for raw in open(os.path.join(topic, "narration", f"{st}.txt"), encoding="utf-8"):
        raw = raw.rstrip("\n")
        if not raw.strip() or raw.lstrip().startswith("#"): continue
        parts = raw.split("|||")
        pat = parts[0].strip()
        sent = parts[1].strip() if len(parts) > 1 else ""
        popup = parts[2].strip() if len(parts) > 2 else ""
        items.append((pat, sent, popup))
    return items

def match_rows(pat, mapping):
    rows = []
    if pat:
        rx = re.compile(pat)
        for ln, rs in mapping:
            if rx.search(ln): rows += rs
    return rows

def steps_of(topic):
    d = os.path.join(topic, "steps")
    return sorted({f.rsplit(".", 1)[0] for f in os.listdir(d) if f.endswith((".cmd", ".session"))})

# ---------------- check ----------------
def check(topic):
    cal = json.load(open(CALIB)) if os.path.exists(CALIB) else {"cols": 91, "rows": 27}
    bad = 0
    for st in steps_of(topic):
        step = read_step(topic, st)
        run_pre(topic, st)
        mapping, total = screen_rows(step, capture(topic, step, cal, step["wait"] + 40), cal["cols"])
        head = step["cmd"] if step["kind"] == "cmd" else " / ".join(step["lines"])
        print(f"\n=== Step {st} [{step['kind']}]: {head[:90]}")
        if total > cal["rows"]:
            print(f"  NOTE: {total} rows ka output, screen {cal['rows']} rows ki -> upar ki lines scroll ho jayengi")
        npath = os.path.join(topic, "narration", f"{st}.txt")
        if not os.path.exists(npath):
            print("  narration file nahi hai"); bad += 1; continue
        for i, (pat, sent, popup) in enumerate(read_narration(topic, st), 1):
            if not pat: continue
            rows = match_rows(pat, mapping)
            if rows: print(f"  OK   {i:>2}  {pat!r:36} -> rows {rows}")
            else:    print(f"  MISS {i:>2}  {pat!r:36} -> koi line match nahi"); bad += 1
    print(f"\n{'Sab patterns match hue.' if not bad else f'{bad} problem(s) mili.'}")
    sys.exit(1 if bad else 0)

# ---------------- render ----------------
def tts(text, path):
    if os.environ.get("TTS_FAKE"):
        run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
             f"sine=f=300:d={max(1.0, len(text) * 0.06)}", "-ac", "1", path])
    else:
        run(["edge-tts", "--voice", VOICE, "--text", text, "--write-media", path])

def boxes_for(rows, cal, offset, t0, t1):
    rows = sorted(r - offset for r in rows if 0 <= r - offset < cal["rows"])
    groups, cur = [], []
    for r in rows:
        if cur and r != cur[-1] + 1: groups.append(cur); cur = []
        cur.append(r)
    if cur: groups.append(cur)
    x = max(0, int(cal["x0"] - 10)); w = min(W - x, int(cal["cols"] * cal["cw"] + 20))
    f = []
    for g in groups:
        y = max(0, int(cal["top0"] + g[0] * cal["pitch"] - 2)); h = int(len(g) * cal["pitch"] + 2)
        en = f"enable='between(t,{t0:.2f},{t1:.2f})'"
        f.append(f"drawbox=x={x}:y={y}:w={w}:h={h}:color=0xF1FA8C@0.18:t=fill:{en}")
        f.append(f"drawbox=x={x}:y={y}:w={w}:h={h}:color=0xF1FA8C@0.9:t=2:{en}")
    return f

def popup_filter(text, path, t0, t1):
    open(path, "w", encoding="utf-8").write(text)
    en = f"enable='between(t,{t0:.2f},{t1:.2f})'"
    return [f"drawtext=fontfile='{FONT}':textfile='{path}':fontsize=28:fontcolor=0x282A36:"
            f"box=1:boxcolor=0xF1FA8C@0.95:boxborderw=22:x=(w-text_w)/2:y=h-130:{en}"]

def step(topic, st):
    cal = json.load(open(CALIB))
    build = os.path.join(topic, "build")
    s = read_step(topic, st)
    run_pre(topic, st)
    mapping, total_rows = screen_rows(s, capture(topic, s, cal, s["wait"] + 40), cal["cols"])
    offset = max(0, total_rows - cal["rows"])
    term = os.path.join(build, f"{st}-term.mp4")
    v = duration(term)
    appear = max(0.0, v - s["wait"] + 0.6)

    items = read_narration(topic, st)
    audio_paths = [os.path.join(build, f"{st}-s{i+1:02d}.mp3") for i in range(len(items))]
    with ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(lambda x: tts(x[0][1], x[1]), zip(items, audio_paths)))

    t, filters, delays = 0.3, [], []
    for i, (pat, sent, popup) in enumerate(items):
        rows = match_rows(pat, mapping)
        if pat and not rows:
            print(f"  WARNING step {st} sentence {i+1}: pattern '{pat}' match nahi hua")
        if rows and max(rows) > 0 and t < appear: t = appear
        d = duration(audio_paths[i])
        if rows: filters += boxes_for(rows, cal, offset, t, t + d)
        if popup:
            filters += popup_filter(popup, os.path.join(build, f"{st}-p{i+1:02d}.txt"), t, t + d)
        delays.append(t); t += d + GAP
    total = round(max(v, t) + 1.0, 2)

    c = ["ffmpeg", "-y", "-v", "error", "-i", term]
    for a in audio_paths: c += ["-i", a]
    vchain = f"[0:v]tpad=stop_mode=clone:stop_duration={total},fps=30"
    if filters: vchain += "," + ",".join(filters)
    parts = [vchain + ",format=yuv420p[v]"]
    for i, dl in enumerate(delays):
        ms = int(dl * 1000)
        parts.append(f"[{i+1}:a]aresample=44100,aformat=channel_layouts=mono,adelay={ms}|{ms}[a{i}]")
    parts.append("".join(f"[a{i}]" for i in range(len(delays))) +
                 f"amix=inputs={len(delays)}:normalize=0,apad[a]")
    c += ["-filter_complex", ";".join(parts), "-map", "[v]", "-map", "[a]", "-t", str(total),
          "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage", "-crf", "21",
          "-c:a", "aac", "-b:a", "160k", os.path.join(build, f"{st}.mp4")]
    run(c)
    print(f"  {st}.mp4 ready ({total}s, {len([f for f in filters if f.startswith('drawbox') ])//2} highlights)")

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    if a[0] == "calibrate": calibrate()
    elif a[0] == "check": check(os.path.abspath(a[1]))
    elif a[0] == "step": step(os.path.abspath(a[1]), a[2])
    else: sys.exit(__doc__)
