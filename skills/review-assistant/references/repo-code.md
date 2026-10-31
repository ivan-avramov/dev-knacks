# Repositories, codebases and open-source projects

Judge against the bar from the problem map using the code, not the README.

## Pass 0: problem map
- What does the repo say it solves; what does the reviewer need it for (adopt, reuse, learn from, compete with)?
- The bar is the reviewer's need, not the repo's ambitions.

## Pass 1: requirement by requirement
- Table: each bar requirement, what the code actually does (file and line anchors), rating with short note.
- Name the gap between documentation and code.
- Borrowed claims: quality numbers belonging to a cited paper or upstream project, not this code.
- Name the patterns: what is the repo, plainly, label removed (e.g. "keyword overlap with provenance logging, presented as a knowledge graph")?
- What survives? Ideas worth keeping, redesigned for our bar, even if no code is worth adopting.

## Repo health signals
Check:
- activity in the last 30 days, author concentration, bus factor;
- CI on pull requests; test suite: what it covers, especially any quality or behavior evaluation beyond unit tests;
- integrations and backends in the repo vs on the roadmap;
- builds outside the company; license; undisclosed upstreams and forks;
- interfaces actually exposed (endpoints, APIs) vs described.

## Cross-checks
- Check AI-generated wikis and summaries (e.g. DeepWiki) against source, including that cited files exist.
- Repo behind a design doc: compare doc and code directly (see `design-doc.md`, Correctness).
