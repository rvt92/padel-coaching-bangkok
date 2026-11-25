# KROSS Padel Coaching

Interactive coaching page for KROSS Padel, Bangkok: https://rvt92.github.io/padel-coaching-bangkok/

- Court mini game, 3D shot library, level finder on the 0–7 scale
- Coached sessions timetable, coaches and level matching, pulled from the Book&Go booking system
- Contact: LINE Official @krosspadel, info@krosspadel.com, KROSS app

## How the data gets in

The page is static. It never talks to Book&Go and holds no credentials.
`scripts/build_sessions.py` logs in to Book&Go **read-only** (only `POST /login` and `GET`; anything else is blocked in code before it is sent), and writes `data/sessions.js` with public session info only: name, venue, date, time, coach first names and a level range. Private lessons, customer data and player counts are left out.

Refresh the timetable:

```
python scripts/build_sessions.py
git add data/sessions.js && git commit -m "Refresh sessions" && git push
```

Credentials live in `.env` (git-ignored) as `username=` / `password=`, or in `BOOKANDGO_EMAIL` / `BOOKANDGO_PASSWORD`.

Book&Go has no level field, so levels come from session names. To change how a session is labelled, or to add a new session name the build reports as UNMAPPED, edit `scripts/session_catalog.py`.
