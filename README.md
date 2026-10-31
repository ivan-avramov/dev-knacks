# dev-knacks

Agent skills for reviewing material, running development work across several models, and writing knowledge-vault notes. Each skill is a folder of Markdown under `skills/` that installs on its own: in Claude Code as a plugin from the `dev-knacks` marketplace, in Codex and Cursor with `npx skills` or by copying the folder. Each skill's README explains what it does and why it works the way it does.

## Catalog

| Skill | Purpose | Version | Requires |
|---|---|---|---|
| [review-assistant](skills/review-assistant/) | Interactive, reviewer-driven review of design docs, products, vendors, patents, repos and benchmarks, ending in a shareable writeup. | 0.1.0 | none |
| [four-eyes](skills/four-eyes/) | Non-trivial development work in separated roles: the session designs and judges, one model implements, another writes tests, a panel reviews once. | 0.7.0 | review-panel 0.5.0 or later |
| [review-panel](skills/review-panel/) | A cold review, verification or research round by a panel of other models, judged by the driving session. | 0.5.0 | none |
| [vnote](skills/vnote/) | Frontmatter schema, relation vocabulary and provenance rules for writing Basic Memory vault notes. | 0.1.0 | Basic Memory MCP server |

## Install

Install only the skills you want. Keep each skill's folder name; Cursor requires the name to match the folder.

### Claude Code

```
/plugin marketplace add ivan-avramov/dev-knacks
/plugin install <skill>@dev-knacks
```

A plugin skill runs as `/<skill>:<skill>`, for example `/review-assistant:review-assistant`, and also triggers from its description. Installing `four-eyes` pulls in `review-panel` automatically.

### Codex and Cursor

```
npx skills add ivan-avramov/dev-knacks --skill <skill>
```

By default this installs into the current project. Add `-g` for a user-wide install:

```
npx skills add ivan-avramov/dev-knacks --skill <skill> -g -a codex
```

Add `-a codex` or `-a cursor` to target one agent. Or copy `skills/<skill>/` into `~/.agents/skills/` (Codex, Cursor) or `~/.cursor/skills/` (Cursor), keeping the folder name. Example: `mkdir -p ~/.agents/skills && cp -R skills/review-assistant ~/.agents/skills/review-assistant`. To track `git pull` instead, symlink from a clone's root: `mkdir -p ~/.agents/skills && ln -s "$PWD/skills/<skill>" ~/.agents/skills/<skill>`. For `four-eyes`, install `review-panel` the same way.

### Manual copy

Copying `skills/<skill>/` into `~/.claude/skills/` also works in Claude Code; the skill then runs as `/<skill>`. Copy or symlink paths per agent:

| Agent | User-wide | Per-repo | Invoke |
|---|---|---|---|
| Claude Code | `~/.claude/skills/` | `<repo>/.claude/skills/` | `/<skill>` |
| Codex | `~/.agents/skills/` | `<repo>/.agents/skills/` | `$<skill>` |
| Cursor | `~/.cursor/skills/`, `~/.agents/skills/` | `<repo>/.cursor/skills/`, `<repo>/.agents/skills/` | `/<skill>` |

Cursor also reads the `.claude/skills` and `.codex/skills` paths.

## Update

Installs don't follow new releases on their own. Each skill's version is pinned, so an update arrives only when that skill's version is bumped.

- **Claude Code:** auto-update is off by default for marketplaces outside Anthropic's. Refresh the catalog with `/plugin marketplace update dev-knacks`, then update a skill with `claude plugin update <skill>@dev-knacks` and restart the session. Or turn on auto-update under `/plugin` → Marketplaces → dev-knacks.
- **Codex and Cursor (`npx skills`):** `npx skills update -g` updates user-wide installs, and `npx skills update -p` updates the current project's. Add skill names to update only those.
- **Copy:** copy the folder again after `git pull`. **Symlink:** `git pull` is enough, but the agent then runs whatever is in your clone, including uncommitted edits.

## Repository layout

- `.claude-plugin/marketplace.json`: the marketplace; one plugin entry per skill, with its version.
- `skills/<skill>/`: the skill (`SKILL.md` and its support files) and its human `README.md`. For example `skills/review-assistant/` holds `SKILL.md`, `references/` and `README.md`.
- `extras/four-eyes/`: instruction snippets that make qualifying work invoke four-eyes.
- `tests/`: catalog-wide checks and the review-assistant suite.
- `AGENTS.md`: guidance for agents working on this repository (`CLAUDE.md` imports it).

## Check

```
python3 -m unittest discover -s tests
```

`claude plugin validate .` checks the marketplace manifest.

## License

MIT; see [LICENSE](LICENSE).
