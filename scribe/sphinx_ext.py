"""scribe's Sphinx extension: requirements and claims written one per line.

```{claims}
c1  open      ^cds-c1  Push and pop make no system call on any path
c2  open               No page fault after construction
```

Each line is a short ID, a state, optionally `^` and the IDs it refines, then the text. The full ID
is the short one behind the page's prefix, `cds-queue-c1`. Each line becomes a hidden need, and the
block renders as one compact table.
"""

import re

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective
from sphinx_needs.api import InvalidNeedException, NeedItemSource, create_need

from scribe import schema

logger = logging.getLogger(__name__)

LINE = re.compile(r"(?P<id>\S+)\s+(?P<state>\S+)\s+(?:\^(?P<refines>\S+)\s+)?(?P<text>\S.*)")


def module_name(dir: str, front_matter: dict) -> str:
    """A module's name: its front matter's `name`, else its directory's, "" for the root."""
    if dir == "":
        return ""
    return str(front_matter.get("name") or dir.rpartition("/")[2])


def id_prefix(repo: str, dir: str, front_matter: dict) -> str:
    """What every ID on the page starts with: `cds-queue-`, or `cds-` on the root."""
    name = module_name(dir, front_matter)
    return f"{repo}-{name}-" if name else f"{repo}-"


def page_dir(docname: str) -> str:
    """The module's directory a document belongs to, "" for the root."""
    return docname.rpartition("/")[0]


def _front_matter(document: nodes.document) -> dict:
    """The page's front matter, which MyST leaves as the document's first field list."""
    for child in document.children:
        if isinstance(child, nodes.field_list):
            return {f[0].astext(): f[1].astext() for f in child.children}
        if not isinstance(child, (nodes.target, nodes.comment)):
            break
    return {}


class Lines(SphinxDirective):
    has_content = True
    need_type = ""
    app: Sphinx

    def run(self) -> list[nodes.Node]:
        env = self.env
        docname = env.docname
        what = schema.TITLES[self.need_type]
        letter = schema.TYPES[self.need_type]
        prefix = id_prefix(env.config.project, page_dir(docname), _front_matter(self.state.document))
        made = env.__dict__.setdefault("scribe_lines", set())

        # The directive's line is its opening fence, and its content starts on the next.
        fence = self.get_source_info()[1]
        out: list[nodes.Node] = []
        rows = []
        for i, raw in enumerate(self.content):
            if not raw.strip():
                continue
            line = fence + 1 + self.content.offset(i)
            m = LINE.fullmatch(raw.strip())
            if not m:
                self._warn(f"a {what} line is: ID, state, ^refines if any, text", line)
                continue
            short = m["id"]
            if not re.fullmatch(rf"{letter}[1-9][0-9]*", short):
                self._warn(f"{what} {short!r} is not {letter}<n>", line)
                continue
            refines = m["refines"].split(",") if m["refines"] else []
            try:
                need, need_nodes = create_need(
                    self.app,
                    self.state,
                    NeedItemSource.on_page(docname, lineno=line),
                    self.need_type,
                    m["text"],
                    id=prefix + short,
                    fields={"status": m["state"], "hide": True},
                    links={"refines": refines},
                )
            except InvalidNeedException as e:
                self._warn(f"Need could not be created: {e.message}", line)
                continue
            made.add(need["id"])
            out += need_nodes
            text, _ = self.parse_inline(m["text"], lineno=line)
            rows.append((need["id"], m["state"], ", ".join(refines), text))
        if rows:
            out.append(_table(rows))
        return out

    def _warn(self, message: str, line: int) -> None:
        logger.warning(message, location=(self.env.docname, line), type="scribe", subtype="line")


def _table(rows: list[tuple[str, str, str, list[nodes.Node]]]) -> nodes.table:
    """ID, state, what it refines, text: one row per requirement or claim."""
    refines = any(r[2] for r in rows)
    table = nodes.table(classes=["scribe-lines"])
    group = nodes.tgroup(cols=4 if refines else 3)
    table += group
    for width in ((14, 8, 14, 64) if refines else (14, 8, 78)):
        group += nodes.colspec(colwidth=width)
    body = nodes.tbody()
    group += body
    for id, state, refined, text in rows:
        row = nodes.row()
        cells = [[nodes.literal(text=id)], [nodes.Text(state)]]
        if refines:
            cells.append([nodes.literal(text=refined)] if refined else [])
        cells.append(text)
        for cell in cells:
            row += nodes.entry("", nodes.paragraph("", "", *cell))
        body += row
    return table


def setup(app: Sphinx) -> dict:
    for directive, need_type in (("reqs", "req"), ("claims", "claim")):
        app.add_directive(directive, type(f"Lines_{need_type}", (Lines,), {"need_type": need_type, "app": app}))
    return {"parallel_read_safe": False, "parallel_write_safe": True}
