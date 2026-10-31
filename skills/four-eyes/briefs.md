# Briefs

Panel briefs follow review-panel; implementer and test-writer briefs end with the constraint block from `SKILL.md`.

## Panel

- **Design review** (strict `opinion`): the operator's request in their words or a faithful paraphrase, the specification as material, and a question: where it fails the goal under the supported conditions, where a helper following it literally would fail, what it requires beyond the goal or could drop, what is ambiguous.
- **Change review** (light `opinion`, strict `verify`): the candidate diff, the frozen tests, both reports and the specification; in strict mode the sensitive hunks and the design dispositions; and a question: what fails in use under the supported conditions, what the tests miss, what the candidate does beyond the specification.

## Implementer

The specification or its path in the copy, the files in scope, the test directory named read-only, the copy's path, the test command, what is stubbed and what done means. Report, as facts: each file added, changed or deleted, one line each; the commands run and their results; what in the specification it could not satisfy, and why. In a fix round it also gets the candidate, the adopted findings and the frozen tests, read-only; it satisfies the specification, not the tests, and reports a test the specification does not support instead of satisfying it.

## Test-writer

First delivery, from the specification and the baseline only: tests of behaviour, not source structure, against the acceptance criteria and interfaces, using the data formats the application actually emits and accepts, their boundaries and failure paths, and the threats the change touches. Each test is classed as reproducing a failure the specification fixes, preserving an invariant, or exercising new behaviour. Run them on the baseline and report the outcomes as they are.

Second delivery, same session: the candidate and the implementer's report. Apply the candidate to a clean copy with the frozen tests, run them and the full suite, check the same named tests ran, and review the candidate against the specification for correctness and the threats it touches. Report the tests with class and outcomes on baseline and candidate, the suite result verbatim, findings with file and line, deviations from the specification, and a verdict: merge, fix then merge with the fixes listed, or reject with the reason. Do not fix.

Later deliveries, the same session or a replacement given the frozen tests: the fix diff and the adopted findings, or the test to amend. Write a test for each adopted defect's reproducible failing case, run all tests on baseline and candidate, and report as in the second delivery.

## Starting a write-capable helper

Panel members use review-panel's `runtimes.md`. The implementer and test-writer run from the copy with its project instructions, able to edit and run the test command:

- Claude CLI: `claude -p --model <model> --setting-sources "project,local" --strict-mcp-config --tools "Read,Edit,Write,Grep,Glob,Bash" --permission-mode acceptEdits --allowedTools "Bash(<test command>:*)" --output-format json < <brief-file>`; the second delivery adds `--resume <session_id>`.
- Codex: `codex exec --skip-git-repo-check --sandbox workspace-write -c model_reasoning_effort=<effort> [-m <model>] < <brief-file>`, without `--ephemeral`; the second delivery is `codex exec resume <session id>`.
- cursor-agent and a host subagent cannot be continued, so they can implement but not write tests.
