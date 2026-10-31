# Products, companies and vendors (including internal launch-readiness)

Always ask: what is actually there, does it work, how mature? Not whether the pitch is good.

## Context to establish
- Decision: adopt, partner, acquire, compete, launch or hold GA, use as platform. An internal product often carries two questions (e.g. "ready to launch?", "can we build on it?"): keep separate.
- Scope: default technology and production-readiness; financials, contracting, ownership, acquisition framing out unless asked. Reviewer narrows scope: mark dropped work deferred, don't delete.
- What is under review, including controls the vendor didn't pitch. Examine their mature product, absent from the deck, as evidence of whether they can ship and support anything.

## Pass 0: problem map
- Per product, one or two plain lines: what it actually is, the customer problem it solves, marketing removed.
- Persona check: read named use cases carefully. Do they serve the persona the pitch claims, or collapse into another?
- Charter fit: does any gap it fills fall within what we are chartered to build or need? A negative case on scope is stronger than one on a defect list.

## Pass 1: structure and positioning
- Strip the label ("remove *agent* from this; what's left?"); map the rest to known patterns; say plainly when it is an old idea relabeled.
- Boundaries: does the product's boundary address the problem?
- Commodity or advantage? Split what could be built quickly on off-the-shelf parts from real IP or execution advantage; say why for each.
- Where do we win? Compare against incumbents on their terms, then name where the subject, or we, have a defensible position.
- Architecture signals: duplicate tools in the dependency stack; end-to-end pipeline ownership vs composed specialists; licenses in the critical path; deployment reality (hosted, in-environment, air-gapped) vs pitch.
- Internal launch-readiness: walk the object or resource graph in dependency order. At each node ask what problem it exists to solve, what was chosen over the obvious alternative, whether its known-issues or in-progress entry breaks a deck claim.

## Claims and findings kept apart
- Claims baseline: what the subject says about itself (deck, site, white papers, calls), attributed, quoted. Freeze once findings start; mark frozen.
- Findings: separate record citing into the baseline.
- Contradictions (C IDs), both sides sourced; the list becomes the vendor question list.
- Attribute vendor numbers as vendor claims ("X states 17x ..."), never fact.
- Call transcripts: check each rep's claim against docs and outside sources. Reps contradicting each other on one call is its own finding.
- Keep internal wording separate from external (e.g. "fake" vs "unsubstantiated").

## Grading
- Customer and deployment evidence, by who speaks: INDEPENDENT (trade press, analyst, named customer employee on record); CO-MARKETING (partner page); VENDOR-SOURCED (their site, deck, wire release); LOGO ONLY. Keep distinct: named customer in production, trial, POC, logo, unattributed "a Fortune 500 retailer".
- Capability evidence: OBSERVED (we used or measured it); VENDOR-DOC (their docs, changelog, audit logs); VENDOR-CLAIM (deck or marketing only); INDEPENDENT.
- Maturity: M5 production-proven (shipping, independently corroborated use); M4 shipping; M3 shipping-young (under about six months, rapid churn, or labelled beta); M2 demo-only (seen only in a vendor-built environment); M1 announced (named and sold, no working artifact); M0 asserted (claim only).
- Standing deliverable: per-product, per-feature matrix: what it actually is, phase, evidence strength, note, what would move the rating. Update after each phase.
- Blind spots to name: non-English markets, login-walled sources, customers under NDA; close gaps that could flip a negative before treating it as settled.

## Sources, in rough order of value
1. Docs site, changelogs, release notes. 2. Audit and activity logs. 3. Public repos (see `repo-code.md`). 4. Patents (see `patent-portfolio.md`). 5. The product itself. 6. Independent press. 7. Deck and site, last.

Date when a feature first shipped, when a demo environment was created. The material contradicting itself (customer counts, sizes, GA dates differing across FAQ and deck) is among the strongest findings.

## Planning beyond the desk
If the review continues, plan phases cheapest and most falsifiable first, vendor-attended work late: 0 desk verification; 1 hands-on, unattended; 2 the one test central to our interest a slide can't fake, pushed past their script; 3 vendor-attended, adversarial; 4 references and commercial, only if in scope; 5 bounded pilot on our own data. Each phase: cost, what done looks like, pass and kill criteria. Results via a remote or isolated browser path are not performance numbers; write that down.

## Workspace (when files persist)
Folder per subject; keep raw sources, digests and derived files apart, never citing a derived file; check new material against the record and flag changes, don't overwrite.
