# docs

The design is in `~/quant/notes/SCRIBE.md`. The milestones are kept here.

## Milestones

- [x] ~~0. Repo. Done when `scribe --help` runs.~~
    - [x] ~~`darkskele/scribe` on GitHub, `~/quant/scribe` as a bare repo with worktrees, devenv VS Code config.~~
    - [x] ~~`pyproject.toml` with its dependencies pinned, the `scribe` conda env with an editable install, `CLAUDE.md`, `README.md`.~~
- [ ] 1. Objects and check. Done when the spike's `docs/queue` passes and a duplicate or malformed ID fails with its file and line.
    - [ ] The bundled sphinx-needs configuration: types, kinds, fields, ID pattern, states, schema version.
    - [ ] `scribe.toml`.
    - [ ] `scribe check`: forms per kind, IDs, links and refinements, layout.
- [ ] 2. Site. Done when the spike's site is rebuilt by scribe from a repo with nothing but MyST and `scribe.toml`.
    - [ ] `scribe build` and `scribe serve`. Top page with the work list, a page per module, milestones expanding to their requirements and claims.
- [ ] 3. TODO. Done when a commit in the pilot repo regenerates and stages `TODO.md`.
    - [ ] `scribe todo`, milestones and code `@todo`s.
    - [ ] devenv's pre-commit hook runs it in place of `collect_todo` for a repo with a `scribe.toml`.
- [ ] 4. Pilot, cds. Done when cds's site and `TODO.md` show what its READMEs did, and nothing is lost.
    - [ ] `docs/queue`, `docs/buffer` and the top page in MyST, their current milestones, requirements and claims given IDs, states by hand.
    - [ ] Their `README.md` and `DECISIONS.md` replaced.
- [ ] 5. Context. Done when a chat started from a cds milestone's bundle can code it without reading anything else first.
    - [ ] `scribe context <module> [milestone]`.
- [ ] 6. Plugin. Done when a new module is taken from an idea to a published design in one session, each stage passing `scribe check`.
    - [ ] A skill per stage, a slash command to enter each, the check hook. A local marketplace in the repo.
    - [ ] The root skill, to start a repo, and the adopt skill, to document one from its code.
- [ ] 7. Ledger. Done when changing a published requirement without a decision is refused at commit.
    - [ ] Publish, and the decision-per-change rule in `scribe check`.
- [ ] 8. Rollout
    - [ ] halln, then quant-platform.
    - [ ] plumb, its docs written after the fact, before its release.
    - [ ] devenv's `collect_todo` retired.
- [ ] With square
    - [ ] `scribe export`.
    - [ ] States from evidence.
- [ ] Stretch, header checks. Done when a renamed declaration, a missing `static_assert` and a published header changed without a decision each fail `scribe check`.
    - [ ] A deterministic reader for C++ declarations, pinned.
    - [ ] Interface, variation and change-without-design checks.
