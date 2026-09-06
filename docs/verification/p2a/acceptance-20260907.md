# P2a Evaluation Infrastructure Acceptance

Date: 2026-09-07
Node: P2a evaluation infrastructure
Status: accepted; Claude hard review and follow-up PASS

## Outcome

P2a infrastructure is implemented and locally accepted. P2 remains open: this
replay contains zero settled samples and establishes no predictive verdict.

- Engineering acceptance: verified.
- Control behavior: undefined because settled N=0.
- Independent-hypothesis evidence: none; status `not_implemented`.
- Evaluator verdict: `insufficient_sample`.
- Disposition: `continue_bounded_collection`.

## Real Replay

The replay used the two earliest genuine P1 forecast snapshots, one BTC and one
ETH. Existing P1 forecasts predate event-lineage persistence and therefore keep
`null` event lineage; no later Gamma metadata was backdated. The local
settlement table contained zero outcome rows. No outcome refresh was performed
before the checkpoint.

- Forecast cutoff: `2026-09-06T16:00:00+00:00`.
- Outcome cutoff: `2026-09-07T00:00:00+00:00`.
- Input forecast snapshots: 4.
- Selected earliest forecasts: 2.
- Included settled samples: 0.
- Pending: 2.
- Excluded later snapshots: `not_earliest_forecast=2`.
- Unknown event lineage: 2 selected forecasts.
- All Brier, clipped log-loss, coverage, event concentration, and settlement-lag metrics: undefined.

Artifacts:

- `checkpoint-p2a-infrastructure-replay-20260907.json`
- `samples-p2a-infrastructure-replay-20260907.json`
- `samples-p2a-infrastructure-replay-20260907.json.manifest.json`
- `report-p2a-infrastructure-replay-20260907.json`
- `report-p2a-infrastructure-replay-20260907.md`
- `report-p2a-infrastructure-replay-20260907.manifest.json`

The sample export SHA-256 is
`553e7975a06cfb399b276829d5c241251073d00cd81c068b7be1707a934126b5`.
The report JSON SHA-256 is
`11289e1edf9c722abe8975714d5becca4a48766bffabb7023157edf23afe6d6e`.
The report Markdown SHA-256 is
`5de5746ba1a0beb6fd38de7d9363357ad286a47d3e9766b6f79db3f77431eb05`.

## Verification

- Python 3.11.15 focused P2a regression before hard review: `459 passed`.
- Full Python 3.11.15 regression before the two narrow hard-review fixes:
  `34,341 passed, 10 skipped` in 466.42 seconds.
- Post-review chronology/manifest focused regression: `53 passed`; compileall
  and `git diff --check` also passed after those fixes.
- Real local PostgreSQL lifecycle, including additive migrations, lineage
  insert, exact replay, identity collision, RLS/privileges and rollback cleanup:
  `5 passed`.
- CLI inventory measured on Python 3.11.15: exactly 85 sorted commands.
- Compileall, credential scan and `git diff --check`: passed.
- Six replay artifacts reproduced byte-for-byte from the unchanged local DB.
- Claude hard review: `VERDICT: PASS`; no blocking findings. The reviewer noted
  missing `checkpoint.generated_at <= outcome_cutoff` enforcement and one
  duplicate manifest key. Both were accepted and fixed. Follow-up hard review:
  `VERDICT: PASS`.

## Scope Boundary

All implemented and exercised paths remain paper-only, report-only and
readonly. Persistence is local PostgreSQL only. No live trading, order, wallet,
account, private-key or credential surface was added. P2 can close only after at
least one genuine prospectively checkpointed settlement, or an explicit
constrained-closure disposition under the project completion plan.
