"""How Book&Go session names map to what the website shows.

Book&Go has no level field, so the level comes from the session name.
Rules are checked top to bottom on the lowercased, accent-free name; the first
keyword that appears in the name wins. Edit this file to fix a mapping, then
re-run scripts/build_sessions.py. Names that match nothing are printed by the
build so you can add them here.

cat: class (group class), clinic (one skill), play (match play with a coach),
     social (americanos, leagues, tournaments)
lo / hi: level range on the 0-7 scale
"""

# Never shown publicly: individual customers' lessons, staff, other sports.
EXCLUDE = [
    "private", "one to one", "one on one", "1 to 1", "staff", "pickleball",
    "third shot", "ball machine", "bangkok event", "golf",
]

# (keyword, category, level_lo, level_hi)
RULES = [
    ("padel&drink - starter", "social", 0, 1.5),
    ("padel&drink - low", "social", 2, 3),
    ("padel&drink-low", "social", 2, 3),
    ("padel&drink - high", "social", 4, 5),
    ("padel&drink-high", "social", 4, 5),
    ("padel&drink", "social", 1, 5),
    ("high intermediate", "class", 4, 5),
    ("low intermediate americano", "social", 2, 3),
    ("low intermediate", "class", 2, 3),
    ("intermediate americano", "social", 3, 4),
    ("intermediate", "class", 3, 4),
    ("advanced", "class", 4.5, 6),
    ("beginner americano", "social", 0.5, 2),
    ("beginner", "class", 1, 2),
    ("starter", "class", 0, 1),
    ("padel 101", "class", 0, 1),
    ("learn & play", "class", 0, 1.5),
    ("road to level 3", "class", 2, 3),
    ("ladies competition", "class", 3.5, 5),
    ("ladies", "class", 1, 3),
    ("bandeja & vibora", "clinic", 2.5, 4),
    ("bandeja", "clinic", 2.5, 4),
    ("glass wall", "clinic", 1.5, 3),
    ("master the glass", "clinic", 4, 5.5),
    ("smash", "clinic", 3.5, 5),
    ("attack", "clinic", 3.5, 5),
    ("tactical", "clinic", 3, 5),
    ("defen", "clinic", 2, 3.5),
    ("volley", "clinic", 2.5, 4),
    ("level up", "clinic", 2, 4),
    ("train & coffee", "clinic", 1.5, 4),
    ("training club", "clinic", 2, 4),
    ("match with coach", "play", 2.5, 5),
    ("late night coach", "play", 2, 4.5),
    ("coach & play", "play", 1.5, 4.5),
    ("play with coach", "play", 1.5, 4.5),
    ("mexicano", "play", 2, 4.5),
    ("king of the court", "social", 3, 5),
    ("women's league", "social", 2, 4.5),
    ("girlies", "social", 1.5, 4),
    ("tps tournament", "social", 3, 6),
    ("tournament", "social", 2.5, 5),
    ("americano", "social", 1.5, 4.5),
    ("open play", "social", 0, 7),
]

# Display clean-ups for typos in Book&Go names.
TYPO_FIXES = {"Beginers": "Beginners", "Intermidiate": "Intermediate", "Trainig": "Training"}

# Which sessions train each shot in the 3D shot library (keywords, same matching).
SHOT_SKILLS = {
    "bandeja": ["bandeja", "smash"],
    "vibora": ["bandeja & vibora", "bandeja", "smash"],
    "bajada": ["master the glass", "glass wall"],
    "chiquita": ["master the glass", "volley", "tactical"],
    "globo": ["defen", "glass wall"],
    "portres": ["smash", "attack"],
    "porcuatro": ["smash", "attack"],
}

# Coach records to ignore (rentals, one-off entries).
COACH_IGNORE = {"ball machine rental", "golf"}
