"""`scribe check`: refuses docs that do not match scribe's schema, each finding at its file and line.

Sphinx with sphinx-needs reads the docs, the same reading the site is built from, so the check and the
site never disagree. scribe then checks what was read: IDs, states, placement, refinements, page forms
and the layout against the code.
"""

import io
import json
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.util.console import nocolor

from scribe import config, schema, sphinx_config
from scribe.sphinx_ext import module_name, page_dir

DOCS = "docs"
PAGE, LEDGER = schema.PAGE, schema.LEDGER


@dataclass(frozen=True, order=True)
class Finding:
    path: str  # relative to the repo, posix form
    line: int  # 0 when the finding is about the file as a whole
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.message}" if self.line else f"{self.path}: {self.message}"


@dataclass
class Page:
    docname: str
    path: str  # docs/<dir>/index.md
    dir: str  # the module's directory under docs/ and the code root, "" for the root
    meta: dict
    titles: list[int] = field(default_factory=list)  # the line of each level-1 heading
    brief: bool = False  # the first level-1 section opens with a paragraph
    sections: list[tuple[str, int]] = field(default_factory=list)  # level-2 headings and lines

    @property
    def file(self) -> str:
        """index for a module's page, decisions for its ledger, anything else is misplaced."""
        return PurePosixPath(self.docname).name

    @property
    def root(self) -> bool:
        return self.dir == ""

    @property
    def stub(self) -> bool:
        return self.meta.get("stub") in (True, "true", "True")


@dataclass
class Read:
    """What Sphinx read: its warnings, the documents by docname, the needs by ID."""

    found: list[Finding]
    docs: dict[str, Page]
    needs: dict[str, dict]
    lines: set[str]  # the requirements and claims written as lines of a block

    def page(self, dir: str) -> Page | None:
        """The module's page for a directory, its index.md."""
        return self.docs.get(f"{dir}/{PAGE}" if dir else PAGE)


def check(root: Path) -> list[Finding]:
    try:
        cfg = config.load(root)
    except config.ConfigError as e:
        return [Finding(config.FILE, 0, str(e))]
    if not (root / DOCS).is_dir():
        return [Finding(DOCS, 0, "missing, the docs live here")]

    read = _read(root, cfg)
    found = read.found
    names = _names(read, found)
    found += _layout(root, cfg, read)
    found += _forms(read)
    found += _needs(cfg, read, names)
    return sorted(set(found))


def _read(root: Path, cfg: config.Config) -> Read:
    nocolor()
    warnings = io.StringIO()
    with tempfile.TemporaryDirectory() as tmp:
        app = Sphinx(
            str(root / DOCS),
            None,
            f"{tmp}/out",
            f"{tmp}/doctrees",
            "needs",
            confoverrides=sphinx_config.config(cfg.repo),
            status=None,
            warning=warnings,
            freshenv=True,
        )
        app.build()
        env = app.env
        docs = {}
        for docname in sorted(env.found_docs):
            path = Path(env.doc2path(docname)).relative_to(root).as_posix()
            name = PurePosixPath(docname).name
            dir = page_dir(docname) if name in (PAGE, LEDGER) else docname
            meta = {k: v for k, v in env.metadata.get(docname, {}).items() if k != "wordcount"}
            doc = Page(docname, path, dir, meta)
            _outline(doc, env.get_doctree(docname))
            docs[docname] = doc
        lines = set(getattr(env, "scribe_lines", ()))
        data = json.loads(Path(f"{tmp}/out/needs.json").read_text())
    needs = data["versions"][data["current_version"]]["needs"]
    return Read(_warnings(root, warnings.getvalue()), docs, needs, lines)


def _outline(page: Page, doctree: nodes.document) -> None:
    for top in doctree.children:
        if not isinstance(top, nodes.section):
            continue
        page.titles.append(top.line or 1)
        if len(page.titles) > 1:
            continue
        body = [c for c in top.children if not isinstance(c, (nodes.title, nodes.target))]
        page.brief = bool(body) and isinstance(body[0], nodes.paragraph)
        for sub in top.children:
            if isinstance(sub, nodes.section):
                page.sections.append((sub[0].astext(), sub.line or page.titles[0]))


_WARNING = re.compile(r"^(?P<loc>.*?): (?:WARNING|ERROR|CRITICAL|SEVERE): (?P<msg>.*?)(?: \[[\w.]+\])?$")
_AT = re.compile(r"^(?P<path>.*?)(?::(?P<line>\d+))?$")
_DUPLICATE = re.compile(r"Need could not be created: A need with ID '(?P<id>[^']+)' already exists "
                        r"\(defined at (?P<doc>[^:]+):(?P<line>\d+)\)\.")


def _warnings(root: Path, text: str) -> list[Finding]:
    found = []
    for raw in text.splitlines():
        m = _WARNING.match(raw)
        if not m:
            continue
        at = _AT.match(m["loc"])
        path, line = at["path"], int(at["line"] or 0)
        try:
            path = Path(path).relative_to(root).as_posix()
        except ValueError:
            pass
        msg = m["msg"]
        if d := _DUPLICATE.match(msg):
            msg = f"duplicate ID {d['id']}, first at {DOCS}/{d['doc']}.md:{d['line']}"
        found.append(Finding(path, line, msg))
    return found


def _names(read: Read, found: list[Finding]) -> dict[str, str]:
    """Each module's name by its directory, the root's "". Appends a finding for a bad or shared name."""
    names, seen = {}, {}
    for page in read.docs.values():
        if page.file != PAGE:
            continue
        name = module_name(page.dir, page.meta)
        names[page.dir] = name
        if page.root:
            continue
        if not re.fullmatch(schema.NAME, name):
            found.append(Finding(page.path, 1, f"module name {name!r} is not {schema.NAME}, set name: in the front matter"))
        elif name in seen:
            found.append(Finding(page.path, 1, f"module name {name!r} is taken by {seen[name]}"))
        else:
            seen[name] = page.path
    return names


def _layout(root: Path, cfg: config.Config, read: Read) -> list[Finding]:
    """docs/ mirrors the directories under the code root: a page per directory, and its decisions beside it."""
    found = []
    have = set()
    for doc in read.docs.values():
        if doc.file == PAGE:
            have.add(doc.dir)
        elif doc.file == LEDGER:
            if read.page(doc.dir) is None:
                found.append(Finding(doc.path, 0, f"no {PAGE}.md beside these decisions"))
        else:
            found.append(Finding(doc.path, 0, f"a directory holds its page, {PAGE}.md, and its {LEDGER}.md, nothing else"))
    code = root / cfg.code
    dirs = {""} | {
        p.relative_to(code).as_posix()
        for p in code.rglob("*")
        if p.is_dir() and not any(part.startswith(".") for part in p.relative_to(code).parts)
    }
    for d in sorted(dirs - have):
        where = f"{cfg.code}/{d}" if d else cfg.code
        found.append(Finding(where, 0, f"no page, expected {DOCS}/{d + '/' if d else ''}{PAGE}.md"))
    for d in sorted(have - dirs):
        found.append(Finding(read.page(d).path, 0, f"no directory {cfg.code}/{d} for this page"))
    return found


def _forms(read: Read) -> list[Finding]:
    """Each page's front matter, title, brief and headings, by its kind. A ledger's title."""
    found = []
    for doc in read.docs.values():
        at = doc.path
        if doc.file == LEDGER:
            for key in sorted(doc.meta):
                found.append(Finding(at, 1, f"{LEDGER}.md takes no front matter, {key} belongs on {PAGE}.md"))
            if not doc.titles:
                found.append(Finding(at, 1, "no title"))
            continue
        page = doc
        for key in sorted(set(page.meta) - set(schema.FRONT_MATTER)):
            found.append(Finding(at, 1, f"unknown front matter {key}"))
        kind = page.meta.get("kind")
        if kind is None:
            found.append(Finding(at, 1, f"no kind, set kind: to one of {', '.join(schema.KINDS)}"))
        elif kind not in schema.KINDS:
            found.append(Finding(at, 1, f"kind {kind!r} is not one of {', '.join(schema.KINDS)}"))
        elif page.root and kind != "area":
            found.append(Finding(at, 1, f"the root is an area, not a {kind}"))
        elif kind == "variation" and not page.root:
            parent = read.page(page.dir.rpartition("/")[0])
            if parent is not None and parent.meta.get("kind") != "concept":
                found.append(Finding(at, 1, f"a variation sits under a concept, {parent.path} is not one"))

        if not page.titles:
            found.append(Finding(at, 1, "no title"))
            continue
        for line in page.titles[1:]:
            found.append(Finding(at, line, "one title per page"))
        if not page.brief:
            found.append(Finding(at, page.titles[0], "no brief, a paragraph under the title"))

        if page.stub:
            for title, line in page.sections:
                found.append(Finding(at, line, f"a stub holds a title and a brief only, not {title!r}"))
            continue
        allowed = schema.ROOT if page.root else schema.KINDS.get(kind)
        if allowed is None:
            continue
        last = -1
        for title, line in page.sections:
            if title not in allowed:
                found.append(Finding(at, line, f"heading {title!r} is not one of {', '.join(allowed)}"))
                continue
            i = allowed.index(title)
            if i <= last:
                found.append(Finding(at, line, f"heading {title!r} out of order, the order is {', '.join(allowed)}"))
            last = max(last, i)
    return found


def _needs(cfg: config.Config, read: Read, names: dict[str, str]) -> list[Finding]:
    """Each need's ID, state, placement and refinements."""
    found = []
    needs = read.needs
    for id, need in sorted(needs.items()):
        doc = read.docs[need["docname"]]
        page = read.page(doc.dir)
        at = doc.path
        line = need.get("lineno") or 1
        kind = need["type"]
        what = schema.TITLES[kind]

        name = names.get(doc.dir, "")
        prefix = f"{cfg.repo}-{name}-" if name else f"{cfg.repo}-"
        expected = f"{prefix}{schema.TYPES[kind]}"
        if not re.fullmatch(rf"{re.escape(expected)}[1-9][0-9]*", id):
            found.append(Finding(at, line, f"ID {id} is not {expected}<n>, a {what} on this page"))

        status = need.get("status")
        if kind in schema.STATED:
            if status is None:
                found.append(Finding(at, line, f"{what} {id} has no state, one of {', '.join(schema.STATES)}"))
            elif status not in schema.STATES:
                found.append(Finding(at, line, f"state {status!r} is not one of {', '.join(schema.STATES)}"))
        elif status is not None:
            found.append(Finding(at, line, f"{what} {id} takes no state"))

        if page is not None and page.stub:
            found.append(Finding(at, line, f"a stub holds no {what}"))
            continue

        parent = need.get("parent_need")
        if kind == "decision":
            if doc.file != LEDGER:
                found.append(Finding(at, line, f"decision {id} belongs in {LEDGER}.md beside the page"))
            elif parent:
                found.append(Finding(at, line, f"decision {id} sits inside no other object"))
            continue
        if doc.file == LEDGER:
            found.append(Finding(at, line, f"{LEDGER}.md holds decisions only, {what} {id} belongs on {PAGE}.md"))
            continue

        if kind in ("req", "claim") and id not in read.lines:
            block = "reqs" if kind == "req" else "claims"
            found.append(Finding(at, line, f"{what} {id} is written as a line of a {{{block}}} block"))

        sections = need.get("sections") or []
        heading = sections[-2] if len(sections) >= 2 else None
        parent_kind = needs[parent]["type"] if parent in needs else None
        if kind == "milestone":
            if parent or heading != "Milestones":
                found.append(Finding(at, line, f"milestone {id} sits under Milestones, not inside another object"))
        elif kind == "req" and doc.root:
            found.append(Finding(at, line, f"requirement {id} belongs to a module, the root holds none"))
        elif kind == "claim" and doc.root and not parent:
            if heading != "Claims":
                found.append(Finding(at, line, f"repo-wide claim {id} sits under Claims"))
        elif parent_kind != "milestone":
            found.append(Finding(at, line, f"{what} {id} sits inside the milestone that introduces it"))

        for target in need.get("refines") or []:
            if kind not in ("req", "claim"):
                found.append(Finding(at, line, f"{what} {id} cannot refine, only a requirement or claim does"))
                break
            other = needs.get(target)
            if other is None:
                found.append(Finding(at, line, f"{id} refines {target}, which does not exist"))
                continue
            if other["type"] != kind:
                found.append(Finding(at, line, f"{id} refines {target}, a {schema.TITLES[other['type']]}, not a {what}"))
            above = read.docs[other["docname"]].dir
            if not _ancestor(above, doc.dir):
                found.append(Finding(at, line, f"{id} refines {target}, which is not on a page above this one"))
    return found


def _ancestor(above: str, below: str) -> bool:
    """Whether directory `above` strictly contains `below`, the root "" containing every other."""
    if above == below:
        return False
    return above == "" or below.startswith(above + "/")
