# Runtimes

Pass the brief on stdin, never in shell source, from the member's directory, under its timeout (default 900 s; on macOS `perl -e 'alarm shift; exec @ARGV or exit 127' <seconds> <command>`, exit 142 on expiry). A field the output lacks is `unreported`.

## claude

```
claude -p --model <model> --setting-sources "" --strict-mcp-config --tools "<tools>" --output-format json [--effort <effort>] < <brief-file>
```

`checkout` uses `--setting-sources "project,local"`. `<tools>` is `""` for `sealed`, else `Read,Grep,Glob`, plus `WebSearch,WebFetch` for `web`. Read the answer from `result`, the model from the `modelUsage` key (an alias resolves to the newest version), the session from `session_id`. Continue with `--resume <session_id>`.

## codex

```
codex exec --skip-git-repo-check --sandbox read-only --ephemeral -c model_reasoning_effort=<effort> [-m <model>] < <brief-file>
```

Without `-m` the default model runs. Read `model:` and `session id:` from the stderr header, the answer from stdout. Codex loads `AGENTS.md` from the directory and `~/.codex/AGENTS.md`; while the latter exists the level carries `user instructions loaded`. Web access is unverified. To continue a session, omit `--ephemeral`, then `codex exec resume <session id>`.

## cursor-agent

```
cursor-agent -p --trust --mode ask --model <id> --output-format text "$(cat <brief-file>)"
```

`--mode ask` is read-only. Ids embed a version and end in an effort (`gpt-5.6-sol-high`); a family with an effort resolves to the highest version among `cursor-agent --list-models` ids containing the family as a hyphen-separated segment and ending in that effort. It cannot suppress Cursor's user rules, so its level carries `user instructions unconfirmed` unless the operator says they are empty. It reports no session and cannot be continued. `web` needs `--force`, leaving it read-only by instruction only, which the report says.

## subagent

The host's subagent, without the driver's transcript, read-only by its tool list. A Claude Code subagent loads CLAUDE.md, so it is `checkout` only, and reports no model or session; record its alias as unverified.
