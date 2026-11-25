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

The build also writes the SEO files: it pre-renders the next 7 days of sessions into `index.html` (so search engines see them without JavaScript), adds the next 14 days as schema.org `Event` markup, and refreshes `sitemap.xml` and `robots.txt`.

## Custom domain

Set `SITE_URL` at the top of `scripts/build_sessions.py` to the new address and re-run the build. Canonical URL, social tags, structured data, sitemap and robots.txt all follow it.

## Coach photos

Book&Go has no coach photos. Put one file per coach in `img/coaches/`, named after the coach in lowercase
(`stefano.jpg`, `aram.webp`, ...), ideally 800×600 or larger, face in the upper third. Re-run the build.
Coaches without a photo show their initial.

## Running on your own server

Copy the folder to the server (e.g. `/var/www/padel`), put `.env` next to `index.html` (`chmod 600 .env`),
serve the folder with nginx/Apache, and block web access to `.env`, `scripts/` and `logs/`.
Then add a daily cron job (Python 3.9+, no extra packages):

```
15 5 * * *  /var/www/padel/scripts/refresh.sh
```

If Book&Go is down, the build stops before writing anything, so the site keeps the previous day's data.

## WhatsApp

Set `const WHATSAPP = '66XXXXXXXXX'` in `index.html` (digits only, with country code) to show the WhatsApp buttons.

Book&Go has no level field, so levels come from session names. To change how a session is labelled, or to add a new session name the build reports as UNMAPPED, edit `scripts/session_catalog.py`.
