# AGENTS.md

## What this is

`dev-knacks`: a marketplace of agent skills (review-assistant, four-eyes, review-panel, vnote). Each skill installs on its own: Claude Code plugin from `.claude-plugin/marketplace.json`; Codex and Cursor via `npx skills` or folder copy. Markdown plus stdlib unittest files; no build or lint.

## Layout

- `.claude-plugin/marketplace.json`: one plugin entry per skill folder (`source` `./`, `strict` false, `skills` `["./skills/<name>"]`, `version`, `description`); four-eyes declares `dependencies` `["review-panel"]`.
- `skills/<name>/`: `SKILL.md`, support files, human `README.md`.
- `extras/four-eyes/`: CLAUDE/AGENTS instruction snippets for four-eyes.
- `tests/`: flat test files. `test_catalog.py`: catalog-wide checks. `test_review_assistant.py`: review-assistant structural checks.
- `README.md`: human-facing catalog, install, layout, license.

## Check

`python3 -m unittest discover -s tests`; `claude plugin validate .` for the manifest.

## Rules

- One folder per skill under `skills/`. Folder name = frontmatter `name` = marketplace entry `name`.
- Marketplace entry `version` = frontmatter `metadata.version`. Bump both together on any change to a skill.
- Frontmatter keys: `name`, `description`, `metadata`; `metadata.source` is `https://github.com/ivan-avramov/dev-knacks`. `description` is the trigger; change it when scope changes; max 1024 characters.
- Agent-facing files (`SKILL.md`, support files, this file) are terse directives. Rationale goes in that skill's `README.md`.
- Skill instructions name no agent-specific tool (no `TodoWrite`, `AskUserQuestion`, `Task`, slash commands, Claude-only skill names); name capabilities generically. Exception: runtime dispatch recipes (`skills/review-panel/runtimes.md`, `skills/four-eyes/briefs.md`) name each CLI's own flags and tools.
- Commit no specs, run records or session links; no `docs/`.

## Versions and pinned tests

- Tests pin each skill: `tests/test_catalog.py` `VERSIONS` (version), `SOURCE_DIGESTS` (sha256 of each support file, and of each `SKILL.md` after `without_metadata()` strips its frontmatter `metadata`), `BODY_DIGESTS` (sha256 of each `SKILL.md` body below the frontmatter); `tests/test_review_assistant.py` version and word ceilings. An intended skill change updates them in the same commit as the version bump.
- A skill's version appears in: marketplace entry `version`; `SKILL.md` `metadata.version`; root `README.md` catalog row; any version in the skill's `README.md` heading or `SKILL.md` body (e.g. four-eyes' `[four-eyes x.y.z]` report line). Update all together.
- Add a skill: create `skills/<name>/` with `SKILL.md` (frontmatter `name`, `description`, `metadata.version`, `metadata.source`); add the marketplace entry; add the root `README.md` catalog row; write `skills/<name>/README.md` linking the root install section; add the skill to the test constants above.

## review-assistant contracts

- `skills/review-assistant/SKILL.md`: the interactive, reviewer-driven protocol shared by all material types. `description` triggers and exclusions: unattended reviews → `review-panel`; line-by-line PR review.
- `skills/review-assistant/references/*.md`: per-type checklists loaded on demand via the §1 routing table. Pass structure per `SKILL.md` §2–3; each file has sections drawn from: `Context to establish`, `Pass 0`, `Pass 1`, `Pass 2`, `Record notes`.
- Every file in `references/` appears in the §1 routing table, and vice versa. Every `references/<x>.md` mention resolves.
- Shared vocabulary is defined once in `SKILL.md`; references use it, never redefine: ID sequences (P, Q, T, F, C), basis tags and verdicts (§5), node status/origin (§6), severities and entry origins (§7).
- Operational probes shared by all types are listed once in `SKILL.md` §9 ("Operational probes (all types)"); `design-doc.md` and `patent-disclosure.md` point to it, never restate it. If §9 is renumbered, update those pointers.
- Grading scales (INDEPENDENT/VENDOR-*, OBSERVED/VENDOR-DOC/VENDOR-CLAIM, M0–M5) are defined in `references/product-vendor.md` `## Grading`; `patent-portfolio.md` points there. Other cross-links: `repo-code.md` → `design-doc.md` (Correctness); `product-vendor.md` → `repo-code.md`, `patent-portfolio.md` (Sources). Keep them.
- `SKILL.md` cross-references sections by number ("section 6", "§7"). After renumbering or reordering, update them; grep `section [0-9]` and `§`.
