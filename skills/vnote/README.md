# vnote

An agent skill with the conventions for writing notes into a knowledge vault through Basic Memory: the fixed frontmatter schema (creation date, source path or URL, optional source dates, tags), the fixed relation vocabulary (`relates_to`, `extends`, `contradicts`, `supersedes`), searching before writing so notes aren't duplicated, and what to do with large source files. The agent reads it before creating or editing a note, so every note carries the same fields and provenance.

## Requirements

- The [Basic Memory](https://github.com/basicmachines-co/basic-memory) MCP server, connected to the agent; the skill drives its `search_notes`, `write_note` and `edit_note` tools.
- A vault laid out with one `Sources/<slug>/` directory per note, where `<slug>` is a short kebab-case slug of the note's title; a raw source file kept with a note sits in the same directory.

## Install

Install as described in the [dev-knacks README](https://github.com/ivan-avramov/dev-knacks#install). The skill folder holds `SKILL.md`. Cursor also reads `.claude/skills` and `.codex/skills`; to track `git pull`, symlink from the clone's root instead of copying: `mkdir -p ~/.agents/skills && ln -s "$PWD/skills/vnote" ~/.agents/skills/vnote`.
