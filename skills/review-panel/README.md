# review-panel

An agent skill for adversarial review by a panel of other models. The session driving your work (the driver) writes a question, sends the same brief to every panel member in parallel, each in a fresh read-only session, then judges their findings: it adopts what it agrees with, rejects what it does not, and needs no consensus. You see its conclusions beside each member's position, and which members ran the driver's own model or vendor.

Three modes:

- **opinion**: one cold review of an artifact or a question. Findings must name a concrete failure, and a "major" must be a material failure of what the request asks for, or a break of something a real consumer relies on, not a literal mismatch.
- **verify**: one follow-up after an opinion: the panel gets the dispositions and the diff since (a repair, or an implementation built from a reviewed specification), and checks that each adopted finding is resolved and nothing the diff touches broke. It is verification, not a fresh hunt for defects.
- **research**: one round on a problem rather than an artifact; each member researches it with web access and proposes a design, citing a source for every claim about external behaviour. The driver verifies the load-bearing claims and synthesises.

A piece of work gets one opinion and at most one verify; an existing independent review you accept, such as a pull-request review, counts as the opinion. Revising the material, renaming the phase or swapping members does not reset that; more review is your call. (0.4.x had a `converge` mode that re-reviewed each revision for up to three rounds; 0.5.0 drops it.)

Each member gets the least context its review needs: `sealed` (the brief alone), `briefed` (plus chosen files) or `checkout` (a read-only copy of the repository), with `web` added where the material makes claims about the outside world. `runtimes.md` says how each runtime is run and what it reports.

## Install

Install as described in the [dev-knacks README](https://github.com/ivan-avramov/dev-knacks#install). The skill folder holds `SKILL.md`, `runtimes.md` and `panel.example.toml`. Cursor also reads `.claude/skills` and `.codex/skills`; to track `git pull`, symlink from the clone's root instead of copying: `mkdir -p ~/.agents/skills && ln -s "$PWD/skills/review-panel" ~/.agents/skills/review-panel`.

Claude Code resolves a skill present at both levels (user-wide and per-repo, see the [install table](https://github.com/ivan-avramov/dev-knacks#manual-copy)) in favour of the user-level copy; most other clients prefer the project copy. The roster line printed before each review names the version that ran.

## Configure your panel

Copy `panel.example.toml` from this folder to `~/.config/review-panel/panel.toml` and list the members this machine can run: a runtime, a model (unversioned names such as `opus` or a family such as `sol` pick up new releases; a full id pins one), and optionally an effort and a timeout. During a session, amend the panel in plain words. With no file, the driver uses one fresh session of a model other than its own.

## Why the driver is the judge

The panel exists to generate adversarial pressure, not agreement. Reviewers always find something, and requiring consensus would let the most contrarian member set the outcome. The driver weighs each finding, and you see both its reasoning and the members' raw output, so you can overrule either.

## History

The earlier history, including 0.4.x, lives in the archived `ivan-avramov/review-panel` repository.
