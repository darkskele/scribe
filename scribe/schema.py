"""scribe's schema: the object types, page kinds, front matter and states every repo's docs are written in.

A repo cannot redefine any of it. A change here that a repo's docs must follow is a new SCHEMA.
"""

SCHEMA = 1

# A repo's or module's name. No `-`, which separates the parts of an ID.
NAME = r"[a-z][a-z0-9_]*"

# Directive to the letter its IDs carry.
TYPES = {"milestone": "m", "req": "r", "claim": "c", "decision": "d"}
TITLES = {"milestone": "milestone", "req": "requirement", "claim": "claim", "decision": "decision"}

# Types that carry a state. A decision is the ledger and takes none.
STATED = ("milestone", "req", "claim")
STATES = ("open", "underway", "done", "dropped")

# Front matter a page may set.
FRONT_MATTER = ("kind", "name", "stub")

# A module's directory holds its page and, beside it, its decisions, the ledger agents read.
PAGE = "index"
LEDGER = "decisions"

# Kind to the level-2 headings its page may hold, in the order they must appear.
KINDS = {
    "area": ("Diagram", "Description", "Interface", "Milestones"),
    "concept": ("Diagram", "Description", "Variation points", "Interface", "Milestones"),
    "variation": ("Diagram", "Description", "Milestones"),
}
# The root is an area that also holds the repo-wide claims and no interface.
ROOT = ("Diagram", "Description", "Claims", "Milestones")
