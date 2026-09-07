# P2 Constrained Closure Evidence

Cohort: `p2-crypto-control-20260907`
Date: 2026-09-07
Plan basis: `docs/superpowers/plans/2026-09-07-p2-real-evaluation-gate.md`
P2 Acceptance clause: "If qualifying collection or settlement cannot occur
within the frozen operating scope, produce the completion plan's
constrained-closure evidence instead of a sample."

## Facts

1. **Prospective freeze integrity.** Inventory (34 candidates, zero outcome
   inspection; SHA `b0d29387...`) -> collection (7 ready forecasts with
   lineage; SHA `dea9b607...`) -> strict `p2-settlement-checkpoint-v1`
   (SHA `a7111d05...`) frozen at `2026-09-07T00:22:35.802567Z` with
   `outcome_refresh: not_performed`, while the database held zero settled
   outcomes. An earlier schema-light freeze (`bece6e11...`) with identical
   forecast identities was superseded pre-outcome and is recorded in the
   stage plan. Chronology is auditable end-to-end from artifact hashes.
2. **Outcome import attempts.** 55 attempts querying exactly the 7
   checkpoint conditions through the audited importer (requires
   `closed=true` AND final prices exactly `1`/`0` with an explicit YES
   label), from `2026-09-07T04:05:01Z` through `2026-09-07T19:28Z`:
   - 04:05-06:32Z: 30 automated attempts (5-minute interval), all 7
     conditions refused `not_settled_or_ambiguous`.
   - 06:34-08:05Z: 4 automated attempts (30-minute interval), same result.
   - 08:36-18:07Z: 20 automated attempts (30-minute interval), same result.
   - 18:07-19:28Z gap: the cron supervisor's liveness check matched a
     stale monitor process by command-line substring and stopped
     relaunching; remediated by killing the stale processes and running a
     manual confirmation attempt.
   - 19:28Z manual final confirmation: all 7 refused; settled rows = 0.
   Total: imported=0, refused=55x7 condition-probes, identity collisions=0.
   Full attempt log preserved at `docs/verification/p2/settlement-attempts-20260907.log`.
3. **Market-side lag evidence.** The `2026-09-07T04:00:00Z` market
   (`0x50a3b9cc...`) remained `closed=false` in persisted Gamma metadata
   for 15.5+ hours past its end time (last distinct observation
   `04:15:14Z`, byte-identical bodies thereafter). The four
   `2026-09-07T16:00:00Z` markets were 3.5 hours past end at the final
   attempt with no resolution. The `2026-10-01` fallback markets lie
   outside the project's remaining operating window (stop directive).
4. **No substitution.** No synthetic or expired-resolved sample was used;
   no cohort rule, tag, page bound, or selection rule changed after the
   freeze; no long-duration market was added after seeing outcomes; the
   control model was never tuned.

## Disposition

P2 closes as **constrained**: P2a infrastructure is fully verified, the
prospective cohort is genuinely frozen and audited (7 forecasts, 4 verified
event groups, 2 team/config cohorts), but N=0 settled samples exist, so no
predictive verdict of any kind is established for
`zero_impact_market_control`. Consistent with the frozen verdict rules, the
state is `insufficient_sample` at N=0 with all metrics undefined; the
disposition recorded here is constrained closure under the completion plan,
not `continue_bounded_collection`, because the project's operating window
ends with this push per the operator's stop directive.

## Resume Path (zero re-freeze required)

The frozen checkpoint remains valid. Any future operator can produce the
genuine report against the SAME cohort by running, after these markets
finally resolve:

```bash
# forward + env gates as in docs/runbooks/research-cycle-operations.md
python -m polymarket_alpha_lab import-settled-outcomes \
  --condition-id <each of the 7 checkpoint conditions>
python -m polymarket_alpha_lab export-settlement-samples \
  --cutoff 2026-09-07T00:22:35.802567+00:00 \
  --outcome-cutoff <refresh time> \
  --checkpoint docs/verification/p2/checkpoint-p2-crypto-control-20260907.json \
  --out docs/verification/p2/samples-p2-crypto-control-20260907.json
python -m polymarket_alpha_lab evaluate-settlement-cohort \
  --samples docs/verification/p2/samples-p2-crypto-control-20260907.json \
  --manifest docs/verification/p2/samples-p2-crypto-control-20260907.json.manifest.json \
  --checkpoint docs/verification/p2/checkpoint-p2-crypto-control-20260907.json \
  --out docs/verification/p2/report-p2-crypto-control-20260907
```

The strict checkpoint contract guarantees no other forecasts can enter that
future report, and the prospective chronology remains provable from the
committed artifacts.

## Verification

- Full Python 3.11.15 regression: `34,375 passed, 10 skipped`
  (single-process 468.29s; `pytest-xdist -n 8` reproduces identical counts
  in 128.55s — 3.6x).
- Strict checkpoint-bound export verified against the real database
  pre-closure: `included=0 pending=7 input_forecast_rows=7`, manifest
  identities equal to the checkpoint; `evaluate-settlement-cohort` replay
  renders `insufficient_sample` with all metrics undefined at N=0.
- compileall and `git diff --check`: pass.
