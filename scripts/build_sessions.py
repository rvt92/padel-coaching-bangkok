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
AHEAD_DAYS = 21      # timetable window
HISTORY_DAYS = 56    # used only for coach profiles


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

    by_cat = collections.Counter(s["cat"] for s in out_sessions)
    print(f"Wrote {OUT.relative_to(ROOT)}: {len(out_sessions)} sessions {today}..{last} {dict(by_cat)}, {len(coaches_out)} coaches")
    if unmapped:
        print("UNMAPPED names (add a rule in scripts/session_catalog.py):")
        for n, k in unmapped.most_common():
            print(f"  {k:3d}  {n}")


if __name__ == "__main__":
    main()
