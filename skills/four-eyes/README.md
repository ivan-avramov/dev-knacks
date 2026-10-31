# four-eyes 0.7.0

An agent skill that puts the stages of a non-trivial change into separate hands: the session you talk to designs the change and judges the findings; a capable model implements it from the approved specification; a different model writes tests before it sees the implementation; and a panel of other models reviews the work once and verifies once. It runs on whatever models you have, down to one subscription with two models, and its report says which roles shared a model or a vendor, so you know what the configuration could not have caught.

The method is cooperative, not enforced. Helpers work in a copy of the repository with your normal CLI configuration; review members get read-only tools; nothing is committed without your word and nothing is pushed unless you say so in that turn. It is built for your own work on your own machine.

## What a run looks like

1. The session writes a specification: the goal, the conditions it must hold under, and acceptance criteria.
2. You see it, the planned cast and which roles share a model or vendor, and say go.
3. One model implements it in a copy while another writes tests from the specification alone.
4. The test-writer runs its tests on the candidate and reviews it.
5. The panel reviews once: the finished change by default, or the specification first for security and architecture work. The session adopts only findings that show the goal failing under its conditions, or a hazard the change introduces.
6. One fix round, checked by a test of each adopted finding and, where the budget still allows, by the panel; then you see the final diff and accept it. The commit follows your standing instructions; a push happens only when you say so.

Review is bounded: one cold pass per piece of work, plus at most one verification. If a real failure remains when that is spent, the run stops and tells you, with the smallest choice: repair it, cut scope, defer or drop it. It never ships the failure, and never asks for another open-ended round on its own.

## Install

Requires review-panel 0.5.0 or later, from this marketplace. Install as described in the [dev-knacks README](https://github.com/ivan-avramov/dev-knacks#install): the Claude Code plugin pulls in review-panel automatically; with `npx skills` or a copy, install review-panel too. The skill folder holds `SKILL.md` and `briefs.md`. Cursor also reads `.claude/skills` and `.codex/skills`; to track `git pull`, symlink from the clone's root instead of copying: `mkdir -p ~/.agents/skills && ln -s "$PWD/skills/four-eyes" ~/.agents/skills/four-eyes`.

Under the Claude Code plugin install the skill is listed as `four-eyes:four-eyes` (and review-panel as `review-panel:review-panel`); the snippet's "four-eyes skill" refers to it.

To make qualifying work invoke the skill rather than rely on automatic selection, append [`extras/four-eyes/CLAUDE.snippet.md`](https://github.com/ivan-avramov/dev-knacks/blob/main/extras/four-eyes/CLAUDE.snippet.md) to `~/.claude/CLAUDE.md` and [`extras/four-eyes/AGENTS.snippet.md`](https://github.com/ivan-avramov/dev-knacks/blob/main/extras/four-eyes/AGENTS.snippet.md) to `~/.codex/AGENTS.md`. These snippets are repository extras, fetched separately; they are not part of the installed skill folder. The models come from review-panel's `~/.config/review-panel/panel.toml`, in its order.

## History

0.4.0 and 0.5.0 enforced isolation with sandbox profiles, run-scoped configuration directories, tiers and a cost ledger; 0.6.0 dropped the enforcement and kept the roles. Up to 0.6.x, design review ran until the panel could suggest nothing better; 0.7.0 replaces that with a fixed review budget and a bar of the goal met under its supported conditions. The earlier history, including the heavier designs and earlier proposals and run records, lives in the archived `ivan-avramov/four-eyes` repository.
