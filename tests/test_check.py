import shutil
from pathlib import Path

import pytest

from scribe.check import check
from scribe.cli import main

FIXTURE = Path(__file__).parent / "fixtures" / "cds"
QUEUE = "docs/queue/index.md"
LEDGER = "docs/queue/decisions.md"
ROOT = "docs/index.md"
PAGE = "---\nkind: {kind}\n---\n\n# {title}\n\nBrief.\n"
ROOT_MILESTONE = "\n## Milestones\n\n````{{milestone}} M\n:id: cds-m1\n:status: open\n{body}````\n"


@pytest.fixture
def repo(tmp_path):
    shutil.copytree(FIXTURE, tmp_path / "cds")
    return tmp_path / "cds"


def edit(repo, path, old, new):
    f = repo / path
    text = f.read_text()
    assert old in text, f"{old!r} not in {path}"
    f.write_text(text.replace(old, new, 1))


def append(repo, path, text):
    f = repo / path
    f.write_text(f.read_text() + text)


def write(repo, path, text):
    f = repo / path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text)


def line_of(repo, path, text):
    return next(i for i, l in enumerate((repo / path).read_text().splitlines(), 1) if text in l)


def findings(repo):
    return [str(f) for f in check(repo)]


def only(repo, expected):
    assert findings(repo) == [expected]


# The fixture and the command.


def test_the_spike_passes(repo):
    assert findings(repo) == []


def test_check_exits_1_and_prints_each_finding(repo, capsys):
    edit(repo, QUEUE, "r2  done", "r1  done")
    assert main(["check", str(repo)]) == 1
    assert "duplicate ID cds-queue-r1" in capsys.readouterr().out


def test_check_exits_0_on_clean_docs(repo, capsys):
    assert main(["check", str(repo)]) == 0
    assert capsys.readouterr().out == ""


def test_output_is_the_same_each_run(repo):
    edit(repo, QUEUE, ":status: done", ":status: wip")
    edit(repo, LEDGER, ":id: cds-queue-d4", ":id: cds-queue-x4")
    assert findings(repo) == findings(repo)


# Requirements and claims, one per line.


def test_a_line_gets_its_full_id_and_line(repo):
    edit(repo, QUEUE, "r2  done", "r2  wip")
    line = line_of(repo, QUEUE, "r2  wip")
    only(repo, f"{QUEUE}:{line}: state 'wip' is not one of open, underway, done, dropped")


def test_duplicate_id_names_both_places(repo):
    first = line_of(repo, QUEUE, "r1  done")
    edit(repo, QUEUE, "r2  done", "r1  done")
    second = line_of(repo, QUEUE, "Elements leave in the order")
    only(repo, f"{QUEUE}:{second}: duplicate ID cds-queue-r1, first at {QUEUE}:{first}")


def test_short_id_carries_its_type_letter(repo):
    edit(repo, QUEUE, "r2  done", "c9  done")
    only(repo, f"{QUEUE}:{line_of(repo, QUEUE, 'c9  done')}: requirement 'c9' is not r<n>")


def test_malformed_line(repo):
    edit(repo, QUEUE, "r2  done  Elements leave in the order they entered, per producer", "r2  done")
    only(repo, f"{QUEUE}:{line_of(repo, QUEUE, 'r2  done')}: a requirement line is: ID, state, ^refines if any, text")


def test_requirement_written_as_a_directive(repo):
    edit(repo, QUEUE, "per producer\n```\n", "per producer\n```\n\n```{req} Direct\n:id: cds-queue-r9\n:status: open\n```\n")
    line = line_of(repo, QUEUE, "{req} Direct")
    only(repo, f"{QUEUE}:{line}: requirement cds-queue-r9 is written as a line of a {{reqs}} block")


# IDs written in full, on milestones and decisions.


def test_malformed_id_names_its_file_and_line(repo):
    edit(repo, LEDGER, ":id: cds-queue-d4", ":id: Cds.Queue.D4")
    line = line_of(repo, LEDGER, "SlotRing is addressed by absolute position")
    only(repo, f"{LEDGER}:{line}: ID Cds.Queue.D4 is not cds-queue-d<n>, a decision on this page")


@pytest.mark.parametrize("bad", ["halln-queue-m1", "cds-buffer-m1", "cds-queue-c9", "cds-queue-m0", "cds-m1"])
def test_id_must_carry_repo_module_and_type(repo, bad):
    edit(repo, QUEUE, ":id: cds-queue-m1", f":id: {bad}")
    line = line_of(repo, QUEUE, "{milestone} A queue for every")
    only(repo, f"{QUEUE}:{line}: ID {bad} is not cds-queue-m<n>, a milestone on this page")


def test_root_ids_carry_no_module(repo):
    append(repo, ROOT, ROOT_MILESTONE.format(body="").replace("cds-m1", "cds-queue-m9"))
    line = line_of(repo, ROOT, "{milestone} M")
    only(repo, f"{ROOT}:{line}: ID cds-queue-m9 is not cds-m<n>, a milestone on this page")


def test_module_name_set_in_front_matter(repo):
    (repo / "include/cds/queue").rename(repo / "include/cds/Queues")
    (repo / "docs/queue").rename(repo / "docs/Queues")
    edit(repo, "docs/Queues/index.md", "kind: area", "kind: area\nname: queue")
    assert findings(repo) == []


def test_module_name_must_be_well_formed(repo):
    (repo / "include/cds/queue").rename(repo / "include/cds/Queues")
    (repo / "docs/queue").rename(repo / "docs/Queues")
    assert "docs/Queues/index.md:1: module name 'Queues' is not [a-z][a-z0-9_]*, set name: in the front matter" in findings(repo)


def test_module_names_are_unique(repo):
    (repo / "include/cds/queue/queue").mkdir()
    write(repo, "docs/queue/queue/index.md", PAGE.format(kind="area", title="inner"))
    only(repo, "docs/queue/queue/index.md:1: module name 'queue' is taken by docs/queue/index.md")


# States.


def test_underway_is_a_state(repo):
    edit(repo, QUEUE, "r1  done", "r1  underway")
    assert findings(repo) == []


def test_unknown_state(repo):
    edit(repo, QUEUE, ":status: done", ":status: wip")
    line = line_of(repo, QUEUE, ":id: cds-queue-m1") - 1
    only(repo, f"{QUEUE}:{line}: state 'wip' is not one of open, underway, done, dropped")


def test_missing_state(repo):
    edit(repo, QUEUE, ":id: cds-queue-m6\n:status: open", ":id: cds-queue-m6")
    line = line_of(repo, QUEUE, ":id: cds-queue-m6") - 1
    only(repo, f"{QUEUE}:{line}: milestone cds-queue-m6 has no state, one of open, underway, done, dropped")


def test_decision_takes_no_state(repo):
    edit(repo, LEDGER, ":id: cds-queue-d2", ":id: cds-queue-d2\n:status: done")
    line = line_of(repo, LEDGER, ":id: cds-queue-d2") - 1
    only(repo, f"{LEDGER}:{line}: decision cds-queue-d2 takes no state")


# Placement.


def test_requirement_sits_inside_a_milestone(repo):
    edit(repo, QUEUE, "## Milestones\n", "## Milestones\n\n```{reqs}\nr9  open  Loose\n```\n")
    only(repo, f"{QUEUE}:{line_of(repo, QUEUE, 'r9  open  Loose')}: requirement cds-queue-r9 sits inside the milestone that introduces it")


def test_root_holds_no_requirement(repo):
    append(repo, ROOT, ROOT_MILESTONE.format(body="\n```{reqs}\nr1  open  R\n```\n"))
    only(repo, f"{ROOT}:{line_of(repo, ROOT, 'r1  open  R')}: requirement cds-r1 belongs to a module, the root holds none")


# Decisions, beside the page.


def test_decision_belongs_in_the_ledger(repo):
    edit(repo, QUEUE, "## Milestones\n", "## Milestones\n\n```{decision} Misplaced\n:id: cds-queue-d9\n```\n")
    line = line_of(repo, QUEUE, "{decision} Misplaced")
    only(repo, f"{QUEUE}:{line}: decision cds-queue-d9 belongs in decisions.md beside the page")


def test_ledger_holds_decisions_only(repo):
    append(repo, LEDGER, "\n```{milestone} Misplaced\n:id: cds-queue-m9\n:status: open\n```\n")
    line = line_of(repo, LEDGER, "{milestone} Misplaced")
    only(repo, f"{LEDGER}:{line}: decisions.md holds decisions only, milestone cds-queue-m9 belongs on index.md")


def test_ledger_takes_no_front_matter(repo):
    edit(repo, LEDGER, "# queue decisions", "---\nkind: area\n---\n\n# queue decisions")
    only(repo, f"{LEDGER}:1: decisions.md takes no front matter, kind belongs on index.md")


def test_ledger_needs_its_page(repo):
    write(repo, "docs/buffer/decisions.md", "# buffer decisions\n")
    assert "docs/buffer/decisions.md: no index.md beside these decisions" in findings(repo)


def test_page_holds_no_decisions_heading(repo):
    append(repo, QUEUE, "\n## Decisions\n\nNone.\n")
    line = line_of(repo, QUEUE, "## Decisions")
    only(repo, f"{QUEUE}:{line}: heading 'Decisions' is not one of Diagram, Description, Interface, Milestones")


# Refinements.


def test_refines_an_unknown_need(repo):
    edit(repo, QUEUE, "^cds-c1", "^cds-c7")
    line = line_of(repo, QUEUE, "Push and pop make no system call")
    assert f"{QUEUE}:{line}: cds-queue-c1 refines cds-c7, which does not exist" in findings(repo)


def test_refines_only_a_need_above(repo):
    edit(repo, QUEUE, "^cds-c1", "^cds-queue-c2")
    line = line_of(repo, QUEUE, "Push and pop make no system call")
    only(repo, f"{QUEUE}:{line}: cds-queue-c1 refines cds-queue-c2, which is not on a page above this one")


def test_refines_its_own_type(repo):
    append(repo, ROOT, ROOT_MILESTONE.format(body=""))
    edit(repo, QUEUE, "^cds-c1", "^cds-m1")
    line = line_of(repo, QUEUE, "Push and pop make no system call")
    only(repo, f"{QUEUE}:{line}: cds-queue-c1 refines cds-m1, a milestone, not a claim")


# Layout.


def test_code_directory_without_a_page(repo):
    (repo / "include/cds/buffer").mkdir()
    only(repo, "include/cds/buffer: no page, expected docs/buffer/index.md")


def test_page_without_a_code_directory(repo):
    write(repo, "docs/buffer/index.md", PAGE.format(kind="area", title="buffer"))
    only(repo, "docs/buffer/index.md: no directory include/cds/buffer for this page")


def test_a_directory_holds_its_page_and_ledger_only(repo):
    write(repo, "docs/queue/notes.md", PAGE.format(kind="area", title="notes"))
    assert "docs/queue/notes.md: a directory holds its page, index.md, and its decisions.md, nothing else" in findings(repo)


def test_hidden_code_directories_are_not_modules(repo):
    (repo / "include/cds/.cache").mkdir()
    assert findings(repo) == []


# Kinds and forms.


def test_page_needs_a_kind(repo):
    edit(repo, QUEUE, "---\nkind: area\n---\n\n", "")
    only(repo, f"{QUEUE}:1: no kind, set kind: to one of area, concept, variation")


def test_unknown_kind(repo):
    edit(repo, QUEUE, "kind: area", "kind: town")
    only(repo, f"{QUEUE}:1: kind 'town' is not one of area, concept, variation")


def test_unknown_front_matter(repo):
    edit(repo, QUEUE, "kind: area", "kind: area\nowner: me")
    only(repo, f"{QUEUE}:1: unknown front matter owner")


def test_root_is_an_area(repo):
    edit(repo, ROOT, "kind: area", "kind: concept")
    only(repo, f"{ROOT}:1: the root is an area, not a concept")


def test_variation_sits_under_a_concept(repo):
    (repo / "include/cds/queue/spsc").mkdir()
    write(repo, "docs/queue/spsc/index.md", PAGE.format(kind="variation", title="spsc"))
    only(repo, "docs/queue/spsc/index.md:1: a variation sits under a concept, docs/queue/index.md is not one")


def test_variation_under_a_concept_passes(repo):
    edit(repo, QUEUE, "kind: area", "kind: concept")
    (repo / "include/cds/queue/spsc").mkdir()
    write(repo, "docs/queue/spsc/index.md", PAGE.format(kind="variation", title="spsc"))
    assert findings(repo) == []


def test_heading_the_kind_does_not_hold(repo):
    edit(repo, QUEUE, "## Diagram", "## Variation points\n\nNone.\n\n## Diagram")
    line = line_of(repo, QUEUE, "## Variation points")
    only(repo, f"{QUEUE}:{line}: heading 'Variation points' is not one of Diagram, Description, Interface, Milestones")


def test_headings_in_order(repo):
    edit(repo, QUEUE, "## Diagram", "## Interface\n\nNone yet.\n\n## Diagram")
    line = line_of(repo, QUEUE, "## Diagram")
    assert f"{QUEUE}:{line}: heading 'Diagram' out of order, the order is Diagram, Description, Interface, Milestones" in findings(repo)


def test_page_needs_a_brief(repo):
    edit(repo, QUEUE, "Bounded lock-free queues, one per shape of producers and consumers. Each moves elements between threads with no lock and no allocation after construction.\n\n", "")
    only(repo, f"{QUEUE}:{line_of(repo, QUEUE, '# queue')}: no brief, a paragraph under the title")


def test_stub_holds_a_title_and_brief_only(repo):
    (repo / "include/cds/buffer").mkdir()
    write(repo, "docs/buffer/index.md", "---\nkind: area\nstub: true\n---\n\n# buffer\n\nFixed buffers.\n")
    assert findings(repo) == []
    write(repo, "docs/buffer/index.md", "---\nkind: area\nstub: true\n---\n\n# buffer\n\nFixed buffers.\n\n## Description\n\nMore.\n")
    line = line_of(repo, "docs/buffer/index.md", "## Description")
    only(repo, f"docs/buffer/index.md:{line}: a stub holds a title and a brief only, not 'Description'")


# scribe.toml.


def test_missing_config(repo):
    (repo / "scribe.toml").unlink()
    only(repo, "scribe.toml: missing")


def test_schema_version_must_match(repo):
    edit(repo, "scribe.toml", "schema = 1", "schema = 2")
    only(repo, "scribe.toml: schema 2, this scribe checks schema 1")


def test_unknown_config_key(repo):
    edit(repo, "scribe.toml", "schema = 1", "schema = 1\ntheme = \"dark\"")
    only(repo, "scribe.toml: unknown key theme")


def test_code_root_must_exist(repo):
    edit(repo, "scribe.toml", 'code = "include/cds"', 'code = "src"')
    only(repo, "scribe.toml: code 'src' is not a directory")


# Sphinx's own warnings.


def test_sphinx_warnings_are_findings(repo):
    edit(repo, QUEUE, "## Description", "## Description\n\n```{nosuchdirective}\n```\n")
    out = findings(repo)
    assert len(out) == 1 and out[0].startswith(f"{QUEUE}:") and "nosuchdirective" in out[0]
