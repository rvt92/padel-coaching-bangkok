"""Pull KROSS coaching sessions from Book&Go (read-only) into data/sessions.js.

Run from the repo root:  python scripts/build_sessions.py
The output holds no credentials, no customer data and no player counts:
only public session names, venues, times, coach first names and level ranges.
"""
import collections, datetime as dt, json, re, sys, unicodedata
from pathlib import Path
BKK = dt.timezone(dt.timedelta(hours=7))  # Bangkok, no DST

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bookandgo import Client, LOCATIONS  # noqa: E402
import session_catalog as cat  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "sessions.js"
INDEX = ROOT / "index.html"
AHEAD_DAYS = 21      # timetable window
HISTORY_DAYS = 56    # used only for coach profiles
STATIC_DAYS = 7      # sessions pre-rendered into index.html for search engines
EVENT_DAYS = 14      # sessions published as schema.org Events

# The public address of the site. Change this one line when the custom domain is live,
# then re-run the build: canonical URL, social tags, sitemap and robots.txt follow it.
SITE_URL = "https://rvt92.github.io/padel-coaching-bangkok/"

CATN = {"class": "Group class", "clinic": "Clinic", "play": "Play with a coach", "social": "Americano & league"}
VENUES = {
    "On Nut": ("89 Soi Chinnamat", "Phra Khanong, Bangkok"),
    "Asoke": ("30 Sukhumvit 21 Road, 8th floor", "Bangkok"),
    "Sky Club": ("88 Soi Sukhumvit 49", "Bangkok"),
    "Indoor": ("135 Ardnarong Road", "Khlong Toei, Bangkok"),
    "Kross Park": (None, "Bangkok"),
}


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = s.replace("intermidiate", "intermediate").replace("beginers", "beginners").replace("trainig", "training")
    return re.sub(r"\s+", " ", s).strip()


def display(name):
    name = re.sub(r"\s+", " ", (name or "").strip())
    if name.isupper():
        name = name.title()
    for bad, good in cat.TYPO_FIXES.items():
        name = re.sub(bad, good, name, flags=re.I)
    return name


def classify(name):
    n = norm(name)
    if not n or any(x in n for x in cat.EXCLUDE):
        return None
    for kw, c, lo, hi in cat.RULES:
        if kw in n:
            return {"cat": c, "lo": lo, "hi": hi}
    return "UNMAPPED"


def coach_name(c):
    return c.strip().capitalize() if isinstance(c, str) else str(c)


def chunks(start, end, days=31):
    s = start
    while s <= end:
        e = min(s + dt.timedelta(days=days - 1), end)
        yield s, e
        s = e + dt.timedelta(days=1)


def main():
    today = dt.datetime.now(BKK).date()
    first, last = today - dt.timedelta(days=HISTORY_DAYS), today + dt.timedelta(days=AHEAD_DAYS)
    c = Client(); c.login()

    sessions = {}
    unmapped = collections.Counter()
    coach = collections.defaultdict(lambda: {"locs": collections.Counter(), "public": collections.Counter(), "private": 0})

    for loc_id, loc in LOCATIONS.items():
        for a, b in chunks(first, last):
            res = c.bookings(a.isoformat(), b.isoformat(), loc_id)
            for court in res.get("courts", []):
                if "court" not in (court.get("name") or "").lower() or court.get("location_id") != loc_id:
                    continue
                for bk in court.get("bookings", []):
                    if bk.get("type") not in ("Lesson", "Event"):
                        continue
                    raw = bk.get("event_name") or ""
                    day = dt.date.fromisoformat(bk["date"][:10])
                    coaches = sorted({coach_name(x) for x in (bk.get("coaches") or []) if norm(str(x)) not in cat.COACH_IGNORE})
                    info = classify(raw)
                    for co in coaches:
                        coach[co]["locs"][loc] += 1
                        if info is None and norm(raw):
                            coach[co]["private"] += 1
                        elif isinstance(info, dict):
                            coach[co]["public"][display(raw)] += 1
                    if day < today or info is None:
                        continue
                    if info == "UNMAPPED":
                        unmapped[raw.strip()] += 1
                        continue
                    end = bk["end_time_local"]
                    if end <= bk["start_time_local"]:
                        end = "24:00"
                    key = (day.isoformat(), bk["start_time_local"], end, norm(raw), loc)
                    s = sessions.setdefault(key, {"d": key[0], "s": key[1], "e": end, "n": display(raw), "loc": loc,
                                                  "c": [], **info})
                    s["c"] = sorted(set(s["c"]) | set(coaches))

    out_sessions = sorted(sessions.values(), key=lambda x: (x["d"], x["s"], x["loc"], x["n"]))

    coaches_out = []
    for name, v in coach.items():
        total = sum(v["public"].values()) + v["private"]
        if total < 5:
            continue
        coaches_out.append({
            "name": name,
            "locs": [l for l, _ in v["locs"].most_common()],
            "runs": [n for n, _ in v["public"].most_common(4)],
            "private": v["private"] > 0,
            "sessions": total,
        })
    coaches_out.sort(key=lambda x: -x["sessions"])
    for co in coaches_out:
        del co["sessions"]

    shot_skills = {}
    for shot, kws in cat.SHOT_SKILLS.items():
        shot_skills[shot] = kws

    data = {
        "generated": dt.datetime.now(BKK).isoformat(timespec="minutes"),
        "from": today.isoformat(), "to": last.isoformat(),
        "locations": list(LOCATIONS.values()),
        "sessions": out_sessions,
        "coaches": coaches_out,
        "shotSkills": shot_skills,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("/* Generated by scripts/build_sessions.py. Do not edit by hand. */\nwindow.KROSS = "
                   + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")

    write_site_files(out_sessions, today)

    by_cat = collections.Counter(s["cat"] for s in out_sessions)
    print(f"Wrote {OUT.relative_to(ROOT)}: {len(out_sessions)} sessions {today}..{last} {dict(by_cat)}, {len(coaches_out)} coaches")
    if unmapped:
        print("UNMAPPED names (add a rule in scripts/session_catalog.py):")
        for n, k in unmapped.most_common():
            print(f"  {k:3d}  {n}")


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def lv_range(s):
    return "All levels" if (s["lo"] == 0 and s["hi"] == 7) else f"Lv {s['lo']:g}–{s['hi']:g}"


def fmt_day(d):
    return dt.date.fromisoformat(d).strftime("%a %-d %b") if sys.platform != "win32" else dt.date.fromisoformat(d).strftime("%a %#d %b")


def inject(html, marker, content):
    start, end = f"<!--{marker}-->", f"<!--/{marker}-->"
    i, j = html.index(start) + len(start), html.index(end)
    return html[:i] + content + html[j:]


def iso(d, hm):
    if hm == "24:00":
        return (dt.date.fromisoformat(d) + dt.timedelta(days=1)).isoformat() + "T00:00:00+07:00"
    return f"{d}T{hm}:00+07:00"


def write_site_files(sessions, today):
    """Pre-render sessions + Event markup into index.html and refresh sitemap/robots/canonical."""
    html = INDEX.read_text(encoding="utf-8")
    now = dt.datetime.now(BKK).strftime("%H:%M")
    sessions = [s for s in sessions if s["d"] > today.isoformat() or s["s"] >= now]

    days = sorted({s["d"] for s in sessions})[:STATIC_DAYS]
    blocks = []
    for d in days:
        rows = "".join(
            f'<div class="srow"><span class="st">{s["s"]}–{s["e"]}</span><div class="sn"><b>{esc(s["n"])}</b>'
            f'<span class="tags"><span class="lvl">{lv_range(s)}</span><span>{CATN[s["cat"]]}</span></span></div>'
            f'<span class="sv">{esc(s["loc"])}</span><span class="sc">{esc(", ".join(s["c"])) if s["c"] else "—"}</span></div>'
            for s in sessions if s["d"] == d)
        blocks.append(f'<div class="sday"><h3>{fmt_day(d)}</h3>{rows}</div>')
    html = inject(html, "STATIC-SESSIONS", "".join(blocks))

    cutoff = (today + dt.timedelta(days=EVENT_DAYS)).isoformat()
    events = []
    for s in sessions:
        if s["d"] > cutoff:
            continue
        street, locality = VENUES.get(s["loc"], (None, "Bangkok"))
        addr = {"@type": "PostalAddress", "addressLocality": locality, "addressCountry": "TH"}
        if street:
            addr["streetAddress"] = street
        coach = f" Coach: {', '.join(s['c'])}." if s["c"] else ""
        events.append({
            "@type": "Event",
            "name": f"{s['n']} at KROSS {s['loc']}",
            "description": f"{CATN[s['cat']]} for padel players, level {lv_range(s).replace('Lv ', '')}.{coach}",
            "startDate": iso(s["d"], s["s"]), "endDate": iso(s["d"], s["e"]),
            "eventStatus": "https://schema.org/EventScheduled",
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "location": {"@type": "Place", "name": f"KROSS Padel {s['loc']}", "address": addr},
            "organizer": {"@type": "Organization", "name": "KROSS Padel", "url": "https://krosspadel.com"},
            "image": [SITE_URL + "og.png"],
        })
    ld = json.dumps({"@context": "https://schema.org", "@graph": events}, ensure_ascii=False, separators=(",", ":"))
    html = inject(html, "EVENTS-JSONLD", f'<script type="application/ld+json">{ld}</script>')

    # Point canonical, social tags and JSON-LD at SITE_URL: every use of the old site address is replaced.
    old = re.search(r'<link rel="canonical" href="([^"]+)"', html).group(1)
    if old != SITE_URL:
        html = html.replace(old, SITE_URL)
    INDEX.write_text(html, encoding="utf-8")

    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{SITE_URL}</loc><lastmod>{today.isoformat()}</lastmod><changefreq>daily</changefreq></url>\n</urlset>\n",
        encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n", encoding="utf-8")
    print(f"index.html: {len(days)} days pre-rendered, {len(events)} Event entries; sitemap.xml + robots.txt -> {SITE_URL}")


if __name__ == "__main__":
    main()
