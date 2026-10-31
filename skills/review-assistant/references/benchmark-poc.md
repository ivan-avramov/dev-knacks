# Benchmarks, POCs and bake-off results

## Pass 0: problem map
What decision is the benchmark meant to inform? What workload and question does it claim to represent; does that match ours?

## Pass 1: validity
Check:
- baseline: what it is; a straw man (untuned competitor, old version, wrong configuration);
- data: who wrote the tuning and held-out sets, their overlap, learning or tuning frozen during evaluation;
- leakage: the system under test's side doors to answers (version history, cached sources, shared index built from test material);
- excluded runs: timeouts, failures, retries dropped from the headline;
- judging: who decided correctness; prefer checkable pass/fail criteria over a model judge, expert human grading only where nothing checkable exists;
- ablation: anything isolating the vendor's contribution (e.g. bootstrap-only vs after human tuning);
- hidden human effort: label each step Human, Tooling or AI, mark inferred labels *(inferred)*; headline time-to-value hiding human tuning;
- variance: repeat runs, a stated minimum detectable difference; group results into tiers rather than declaring a winner;
- configuration of the system under test: frozen across suites;
- harness sensitivity: what was held constant.

## Cost and mix
- Cost per completed task, not per token.
- Routers or tiered systems: does the task mix match the production distribution, or are results reported per complexity band?

## Record notes
Per headline number: source, what it measures, whether we can reproduce it, the single test that would confirm or kill it on our own data.
