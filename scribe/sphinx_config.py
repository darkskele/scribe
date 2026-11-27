"""The Sphinx configuration every repo's docs are built with, from scribe's schema. A repo holds no conf.py."""

from scribe import schema

COLORS = {"milestone": "#E8EEF7", "req": "#E9F5E9", "claim": "#FBEFE3", "decision": "#EEEEEE"}


def config(repo: str) -> dict:
    return {
        "project": repo,
        "extensions": ["myst_parser", "sphinx_needs", "sphinx_design", "scribe.sphinx_ext"],
        "html_theme": "furo",
        "html_title": repo,
        "myst_enable_extensions": ["colon_fence"],
        # The site's navigation is generated from the tree, so no page lists the others.
        "suppress_warnings": ["toc.not_included"],
        "needs_id_required": True,
        # scribe checks IDs against the page they sit on, with its own messages.
        "needs_id_regex": r".*",
        "needs_types": [
            {
                "directive": d,
                "title": schema.TITLES[d].capitalize(),
                "prefix": "",
                "color": COLORS[d],
                "style": "node",
            }
            for d in schema.TYPES
        ],
        "needs_links": {"refines": {"incoming": "refined by", "outgoing": "refines"}},
        "needs_build_json": True,
    }
