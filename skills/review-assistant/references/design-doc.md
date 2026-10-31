# Design docs: design doc, tech spec, RFC, architecture proposal

## Context to establish
- Version: if short (human-read) and full versions exist, review the full one.
- Place in the larger system: what it owns, depends on.
- Ship commitment (demo, preview, production), deployment models (cloud, on-prem, air-gapped, hybrid). The commitment sets how much non-functional coverage is owed.
- Reviewer's lens: security, operations, platform fit, product or cost.
- The doc's own open decisions: seed the walk with them.

## Pass 0: problem map
Sources: summary, context and problem, goals and non-goals.
- What problems does it address, under what constraints?
- Does each goal follow from the problem, and is it measurable (each with a way to tell it is met)?
- Do non-goals quietly come back later?
- Was not building, or buying, considered?

## Pass 1: structure
Sources: architecture overview, components, workflows, decisions and alternatives, phases, dependencies, risks.
- Map goals to components: for each problem in the map, find what addresses it. A component serving no goal, or a goal no component serves, is a finding.
- Boundaries and ownership: what should this design build, what be shared across the larger system? List dependencies on other teams, organizations, customers.
- Decisions: alternatives considered? Trade-offs stated? Rejected options dismissed for real reasons?
- Settled or assembled? Two or three tools doing one job usually means merged prototypes, not a settled architecture.
- Phases: does phase 1 deliver something coherent alone? Do later phases depend on undecided things?

## Coverage check (one turn, early in pass 1)
List standard dimensions covered, marked not applicable by the doc (with its reason), and missed. Missing ones that matter for the ship commitment become tree nodes. A demo owes little of the non-functional list; production most.
- Functional: problem, goals, non-goals; architecture, components; workflows; decisions, alternatives; interfaces, contracts; data model, storage, retention, schema evolution; phases.
- Non-functional: identity and access; tenancy and isolation; security and compliance; AI and agent behavior, when applicable; scale, performance, capacity, cost; availability, failure modes, business continuity; observability; incident handling; testing; CI/CD, rollout, migration, rollback; maintainability and evolution; dependencies; risks, open questions.

## Probes, by lens
Use those the lens and ship commitment call for.
- Security and trust. Probe: identity reaching each system, carried (signed, delegated) or asserted by an intermediary; trust: what each component trusts and why; what enforces each rule, and what if it has a bug or another client bypasses it; controls on every entry path (agent, direct, batch, interactive); credentials: which exist, breadth, lifetime, who can mint; principals acting for many users, whether removable or containable; derived data (results, copies, caches, indices): where it lands, who can read it, whether it keeps the source's protection; leaks via errors, metadata, timing; what is knowingly left open.
- Operations. Probe: what breaks at 3 a.m.; numbers that don't add up (timeouts vs retry budgets, recovery time vs target); what fills up or saturates first; what upgrades or maintenance windows do to customers.
- Aggregate behavior, AI and agent behavior, other operations: see SKILL §9, Operational probes (all types).
- Correctness. Check: workflows step by step; doc vs code, if any; claims about other systems, true today per current docs, not memory.
- Consistency. Check: same fact stated differently in two places, drifting names, wrong cross-references, interfaces named in prose but absent from the interface list. Offer a contradiction-check pass listing each pair with both quotes.
- Readability: can a senior reader tell in five minutes what is built, risky, asked?

## Pass 2: detail
Interfaces, field shapes, limits, wording; after pass 1, or earlier on request. Interfaces: list complete, error and retry semantics defined, versioning defined, examples match contracts.

## Reading
- Core path first (summary, context, goals, decisions, phases, risks), then the lens's specialty sections.
- Label a faithful redraw as a redraw. At pass 1's end, an architecture sketch with agreed feedback applied, labeled as yours, often helps.

## Record notes
Anchor span: a few words, a sentence, or a heading for a whole-section point; with section number, title and page; one finding per entry.
