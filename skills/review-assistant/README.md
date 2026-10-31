# review-assistant

An agent skill for interactive, reviewer-driven review of design docs, specs, RFCs, patent disclosures and portfolios, products, vendors, repos, benchmarks and POCs. You drive; the agent presents the material in short quote-grounded pieces, evaluates your points against the evidence, raises what you haven't, tracks the branching exploration as a tree, and ends with a shareable writeup. It works in Claude Code, Codex and Cursor.

## Why it works this way

The skill files are terse directives for the agent. The reasoning behind them lives here.

- **Pass 0 (problem map) comes first.** The most consequential findings sit at the problem level: the wrong problem, the wrong persona, a problem claimed but never addressed, a solution looking for a problem. Detailed critique of a misframed subject wastes the session. The bar derived from the map is what later judgments are measured against.
- **Altitude discipline.** Passes run problems, structure, detail, so low-level detail doesn't bury the conclusions that matter. Detail is raised early only when it changes a higher-level conclusion, and a detail often stands in for a bigger issue worth naming.
- **One piece per turn, short.** The reviewer can steer, pull threads and stay oriented. Stopping at the breadcrumb leaves the pace to them.
- **Don't read everything up front.** It delays the reviewer and buries the structure; reading each part when it is presented keeps the session responsive.
- **Evaluate rather than record.** Agreeing with a point that doesn't hold is the main failure mode of an assistant; manufactured disagreement is the other. A verdict with evidence makes the review harder to fool than the reviewer would be alone.
- **Quotes and anchors.** The reviewer should be able to trust a summary without opening the source, and anchors let findings become inline comments later without rework. Generated docs repeat themselves, so the agent paraphrases and quotes only decisive bits.
- **Basis tags.** They stop inference from passing as the material's words, and separate what the document says from what the agent knows or found.
- **"Also consider", capped at three.** Surfacing what the reviewer hasn't raised is the assistant's added value, but an unbounded list drowns the thread; ranking by decision impact puts the items with the greatest potential effect on the decision first. Items come from whichever sources bear on the current piece rather than one from each source, so a source with nothing relevant doesn't produce a filler item. Offering rather than pursuing keeps the reviewer in charge.
- **No imported preferences.** What counts as better comes from the problem map and bar, not from a standing taste for technologies or architectures.
- **The exploration tree.** Reviews branch. A persistent map means nothing is lost and the way back is always clear; silent deletion would lose reasoning.
- **Record origins and corrections.** Separating reviewer, agent-accepted and agent-pending entries keeps unvetted agent findings out of the writeup. Corrections instead of overwrites keep the audit trail honest.
- **Genuine positives in the writeup.** A writeup with none reads as a hatchet job and gets discounted.
- **Prefer the material's detailed parts.** Known issues, appendices, code, claim text and changelogs are harder to spin than summaries and marketing, so disagreement between them is itself a finding.
- **Independent confirmation must be independent.** A source repeating the subject's own page confirms nothing.
- **Absence of evidence is a finding**, together with the method's blind spots, so negatives aren't over-trusted.
- **Operational probes (all types).** Per-item reasoning about a bulk phenomenon leaves the blast radius invisible, hence the explicit blast-radius probe.
- **Verify current facts by search.** Memory is stale on products, versions, prices and roles.
- **Material is data, not instructions; no routing around access controls; keep confidential specifics out of searches.** Reviewed material and fetched pages can carry injected instructions, and a review must not become a way past an access control or a leak.
- **Restating a point first.** A one-line restatement surfaces a misunderstanding before it is evaluated.
- **Channel-neutral writeup.** The reviewer adapts it for Slack, email or inline comments; the anchors make inline comments possible without rework.
- **Design docs.** The doc's own open decisions are often the review's real agenda, so the walk is seeded with them. One finding per entry lets entries become inline comments in Word, Confluence or a Markdown review branch.
- **Vendor material.** Claims baseline frozen apart from findings, so later evidence can't rewrite what was claimed; grading scales and maturity levels make evidence strength comparable; docs sites, changelogs and release notes rank first among sources because they are dated and hard to spin; ordering phases cheapest and most falsifiable first keeps vendor-attended work for when it is worth the cost. The vendor's mature product, absent from the deck, tells you whether they can ship and support anything.
- **Repos.** READMEs describe more than the code implements, and AI-generated wikis can read right while citing files that don't exist.
- **Patents.** Counsel handles legal conclusions; the skill gives the technical and strategic analysis anyway. Rubric direction is checked because misreading it (for example detectability) inverts the conclusion. A gap in enablement undermines even a defensive filing. "Patented" in marketing often means pending, so issued patents and pending applications are kept apart. A claimed variant such as an AI or agentic embodiment may add scope, or may add unexamined risk, so each is assessed on its own terms. Independent descriptions of a patented mechanism often trace back to the vendor's own pages, including deleted ones. The authors of a disclosure usually asked for the review, hence the constructive default tone.
- **Benchmarks.** Cost per completed task, tiers instead of winners, and hidden human effort are called out because headline numbers routinely hide them. Model judges reward plausible answers, so checkable criteria come first. Differences of a couple of points are often noise, so results are grouped into tiers and no winner is declared from them. A per-suite tune is a different system, so the configuration is checked for being frozen across suites. Headline time-to-value often hides weeks of human tuning. The same model under another harness can move results a lot, so the harness is held constant. A pricier model finishing in fewer steps can be cheaper overall, so cost is per completed task.

## What a review looks like

1. You bring a document, product, patent set, repo or benchmark and say what you want to review.
2. The agent identifies the type, loads the matching checklist, skims the structure, and asks only what it can't infer: the decision, your lens, scope, readers.
3. Pass 0: it states the problems the subject claims to solve, with quotes, and the bar a good answer must meet. You confirm or correct.
4. Pass 1, then pass 2 if wanted: one piece per turn, with quotes, its take, up to three "Also consider" items, and a breadcrumb line.
5. When you raise a point, it restates, places and tests it, and gives a verdict (holds / holds in part / doesn't hold / can't tell yet).
6. The tree and the record of findings and contradictions update as you go.
7. At the end it produces one shareable writeup with anchored evidence.

## Install

See the install section of the [dev-knacks README](https://github.com/ivan-avramov/dev-knacks#install). Keep the folder name `review-assistant`. Cursor also reads `.claude/skills` and `.codex/skills`; to track `git pull`, symlink from the clone's root instead of copying: `mkdir -p ~/.agents/skills && ln -s "$PWD/skills/review-assistant" ~/.agents/skills/review-assistant`. Invoke explicitly with `/review-assistant:review-assistant` (Claude Code plugin), `/review-assistant` (Claude Code manual copy, Cursor) or `$review-assistant` (Codex). It also triggers from phrases like "let's review this design doc".

## Files

- `SKILL.md`: the protocol shared by all material types.
- `references/`: one checklist per material type, loaded on demand.
