# CLAUDE.md — project context for Claude Code

## What this is
A Python tool, with a Claude Code plugin, for every repo under `~/quant`. It takes a module from idea to published design in fixed stages, tracks the work the design turns into, presents the system as a site, and sets up each coding chat with exactly the context one milestone needs. See `README.md` and `docs/README.md` (the milestones). The design is in `~/quant/notes/SCRIBE.md`, the principles it shares with plumb and square in `~/quant/notes/TOOLS.md`.

## Non-negotiables
- **Intent is written, facts are generated.** A repo's MyST docs are the only source. The site, `TODO.md` and every context bundle are generated from them, never edited.
- **The tool enforces form, not the prompt.** A skill states a stage's form. `scribe check` refuses what does not match, and a stage is done only when it passes.
- **One tool, nothing copied into a repo.** Object types, fields, ID pattern, states, the Sphinx configuration and the site's templates are scribe's. A repo holds its MyST and `scribe.toml` only.
- **Deterministic.** Same docs and code, same output, byte for byte. Sorted, nothing time-dependent, nothing from the machine it runs on.
- **A person stays in the implementation loop.** scribe never writes a module's code. It fixes the design and sets up the chat that codes one milestone.
- **IDs are never reused.** A dropped object keeps its ID and stays in the docs as `dropped`.
- **No domain knowledge.** scribe knows nothing of queues, networks or any consumer. Those are its users' docs.
- **Seams first, generality later.** Build concretely; abstract on the second implementation.

## Toolchain
Python 3.15, the `scribe` conda env built by `setup.sh` from `environment.yml` (Python and pytest). scribe's own dependencies (Sphinx, myst-parser, sphinx-needs, sphinx-design, furo) are pinned exactly in `pyproject.toml` and installed from it, editable. sphinx-needs renames its configuration between releases, so a version bump is its own change, with the deprecation warnings cleared. Everything runs in WSL, nothing on the box.

## Docs and comments
Follow the `writing` skill for every comment and doc. In short: terse, self-contained, single-source, no em dashes. Goals live as `## Milestones` checklists in `docs/README.md`. `TODO.md` is generated from them and the code `@todo`s by the pre-commit hook, so never edit it by hand.

## Working style
- Terse. State what changed; don't re-narrate.
- Smallest correct diff. No drive-by cleanup, no speculative abstraction.
- Don't volunteer what was deliberately deferred unless asked.
- Don't caveat with "not built/verified" — the user runs it.
- A new command or test entry point? Add it to the shared VS Code config in `~/quant/devenv/vscode/scribe/` in the same change, unless a wildcard task covers it.

## Git
- **Never `git commit` in this repo**, however the request is phrased. Propose a message, leave the change for the user.
- **Never `git add`, stage, or touch the index** unless staging was explicitly asked. The user works out of staged changes as pre-commit review.
- Branching and pull/rebase only when directly prompted for that action.

## Tests
- **Don't run tests unless explicitly asked.** The user runs those. Exception: an iterative "fix X and verify it" step.
- `~/miniconda3/envs/scribe/bin/python -m pytest` from the repo root.
