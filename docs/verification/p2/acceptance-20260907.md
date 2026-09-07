# P2 Genuine Settlement Evaluation Acceptance

Date: 2026-09-07
Cohort: `p2-crypto-control-20260907`
Plan: `docs/superpowers/plans/2026-09-07-p2-real-evaluation-gate.md`
Outcome: constrained closure (N=0; no predictive verdict)

## Command Sequence

1. Inventory (no outcome inspection), pinned first page per team:
   `GET /markets?tag_id={235|39}&closed=false&limit=100&offset=0` via the
   registered `SafeGETTransport`; persisted projection only (identity, end
   time, lineage, exclusions). Outcome prices were neither requested nor
   parsed.
2. One single-market cycle per eligible candidate through the existing
   pipeline (slug identity check, CLOB YES book, Kraken spot, forecast +
   evidence + lineage persistence).
3. Strict `p2-settlement-checkpoint-v1` frozen before any outcome refresh.
4. Post-resolution: 55 audited import attempts against exactly the 7
   checkpoint conditions (log:
   `docs/verification/p2/settlement-attempts-20260907.log`); no verifiable
   settlement occurred within the operating window; constrained closure
   evidence at `docs/verification/p2/constrained-closure-20260907.md`.

## Frozen Artifacts

- `inventory-p2-crypto-control-20260907.json`
  SHA-256 `b0d29387adf9816bb70137fc48c75777dfa2f24c5f3c0cfc40331e6031eafab4`
  — 34 eligible candidates (BTC 2, ETH 32), verified lineage only, 8 event
  groups, per-row exclusion reasons, `outcome_inspection: not_performed`.
- `collection-p2-crypto-control-20260907.json`
  SHA-256 `dea9b60765f228e7fda3b1d0f5907c1e1ede472757346b94fd72b23cd5843397`
  — 34 attempts: 7 ready (BTC 1, ETH 6) with lineage persisted, 16
  evidence-blocked, 11 response-body policy refusals (fail-closed by
  design, disjoint from the selected seven). No retries.
- `checkpoint-p2-crypto-control-20260907.json`
  SHA-256 `a7111d0546468f8b568d5a58ff180752c4eac556cff8a4f94c30705b8a403c8d`,
  cutoff `2026-09-07T00:22:35.802567+00:00`, 7 forecasts, 4 verified event
  groups, cohorts `crypto_btc:p1-crypto_btc-v1`,
  `crypto_eth:p1-crypto_eth-v1`, `outcome_refresh: not_performed`. The
  superseded schema-light freeze (`bece6e11...`) is recorded in the stage
  plan; regeneration happened while the database held zero settled
  outcomes, before any outcome refresh.
- `constrained-closure-20260907.md` and
  `settlement-attempts-20260907.log` — closure evidence.

## Hardening Review (independently reviewed; all five findings accepted)

1. Strict checkpoint contract (`settlement_checkpoint.py`): frozen
   constants, per-forecast detail cross-checked against parallel arrays,
   recomputed lead/horizon/temporal bounds, and exact-byte sibling artifact
   hashes; minimal fabricated documents are rejected.
2. Export reconstructs each forecast through the validated
   `TeamForecastDbRow` contract before scoring; tampered rows fail closed.
3. Lineage and outcome queries are scoped to the checkpoint cohort.
4. Malformed DB shapes are counted or fail closed; no crash path.
5. `--checkpoint` is a required CLI argument; the repository-wide export
   fallback no longer exists.

## Verification

- Focused strict-checkpoint/export/report regression: `136 passed`.
- Full Python 3.11.15 regression: `34,375 passed, 10 skipped` in 468.29s
  (xdist `-n 8`: identical counts in 128.55s).
- Real pre-closure dry export through the strict path:
  `included=0 pending=7 input_forecast_rows=7`, manifest identities equal
  to the checkpoint; evaluator replay `insufficient_sample` with all
  metrics undefined at N=0.
- compileall and `git diff --check`: passed.

## Result

P2 closes as constrained: infrastructure fully verified, prospective
cohort genuinely frozen and audited, N=0 settled samples, no predictive
verdict established for `zero_impact_market_control`. The resume path
against the same frozen checkpoint is documented in the closure evidence.

## Scope Boundary

Paper-only, report-only, readonly throughout. Local PostgreSQL only. No
trading, order, wallet, account, private-key or credential surface.
