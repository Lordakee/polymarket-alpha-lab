# Supplied-input team forecast batches

## Current capability, not the historical first slice

The current source tree contains minimal supplied-input builders for all ten
teams: `politics`, `crypto_btc`, `crypto_eth`, `macro_rates`, `equity_indices`,
`commodities_gold`, `commodities_oil`, `sports_soccer`, `sports_basketball`, and
`sports_other`. They are already exported from the package root. The original
`team-agent-framework.md` first-slice taxonomy table is historical; its
"only crypto_btc is runnable" statement is not a current inventory of these
minimal builders.

These are not ten autonomous research agents. The builders accept evidence
and probability impacts supplied by a caller. They do not collect evidence,
call language models, schedule recurring work, or independently research
markets. BTC additionally has a separate evidence-policy, aggregation,
envelope and atomic-persistence service. That advanced service is **not** the
minimal BTC builder used here; batch construction never replaces its gates.

## New batch API

Import from `polymarket_alpha_lab.team_forecast_batch`:

- `SUPPORTED_TEAM_IDS`: immutable tuple covering the ten-team taxonomy.
- `TeamForecastBatchRequest`: one team, one market, typed config and evidence,
  caller-supplied aware timestamp and canonical Decimal P(YES).
- `run_team_forecast_batch(requests, max_workers=4)`: synchronous bounded
  in-process concurrency using only the fixed existing local builders.
- `TeamForecastBatchOutcome`: `built` with validated packets, or `failed`
  with a fixed reason code and no packets. `built` is not a quality, risk,
  publication, recommendation, allocation, or execution approval.

Requests and evidence must be tuples. IDs must be unique within a batch;
source IDs must be unique within each request. Config and evidence must use
the exact classes corresponding to the selected team. All requests and nested
inputs are validated and reconstructed before any builder starts, so a
malformed later input does not leave an earlier task partially processed.

A worker failure does not discard another team's successful result. Exceptions
are never copied to outcomes or printed. Every outcome remains in input order
regardless of completion order. The executor is joined before returning;
there is no background work after the call. `max_workers=1` is serial;
positive integer values bound simultaneous workers and are capped at batch
size. Threads permit overlapping invocations, not a promise of CPU speedup.

## Example: ETH and macro in the same batch

```python
from datetime import UTC, datetime
from decimal import Decimal
from polymarket_alpha_lab.crypto_eth_team import CryptoEthEvidenceInput, CryptoEthTeamConfig
from polymarket_alpha_lab.macro_rates_team import MacroRatesEvidenceInput, MacroRatesTeamConfig
from polymarket_alpha_lab.team_forecast_batch import TeamForecastBatchRequest, run_team_forecast_batch

now = datetime.now(UTC)
requests = []
for team, config_type, evidence_type in (
    ("crypto_eth", CryptoEthTeamConfig, CryptoEthEvidenceInput),
    ("macro_rates", MacroRatesTeamConfig, MacroRatesEvidenceInput),
):
    evidence = evidence_type(
        source_id="synthetic-source", source_type="supplied",
        evidence_text="Synthetic example; not market evidence",
        data_timestamp=now, data_freshness_seconds=0,
        evidence_type="supplied_probability_delta", weight=Decimal("0.8"),
        probability_impact=Decimal("0.05"), reason_codes=("synthetic_example",),
    )
    requests.append(TeamForecastBatchRequest(
        request_id=f"demo-{team}", team_id=team,
        condition_id=f"synthetic-{team}", market_slug=f"synthetic-{team}",
        question="Synthetic example?", event_template="synthetic",
        base_probability=Decimal("0.5"), config=config_type(config_version="demo-v0"),
        evidence=(evidence,), generated_at=now,
    ))
results = run_team_forecast_batch(tuple(requests), max_workers=2)
assert [result.status for result in results] == ["built", "built"]
```

## Validation and boundaries

`tests/test_team_forecast_batch.py` exercises every real registered builder,
serial/parallel equality, simultaneous-worker bounds, completion-order
inversion, per-job failure isolation, redaction, corrupted output suppression,
input snapshots, exact types, and hard flags. Run that file plus
`scripts/verify_local.py --full`; actual CI results are recorded in the PR.

No live trading, auth, wallet, account, order, side-selection logic, cost
calculation, strategy-cycle wiring, database connection or persistence is
added. Existing builder probabilities and legacy paper-review side fields
are preserved, not interpreted as new recommendations. All objects retain
`paper_only=True`, `report_only=True`, `readonly=True`. No new storage backend,
file journal, hosted database, or credential access exists. Future durable
integration must use the approved local Supabase/Postgres path and must not
persist these raw batch outputs by bypassing publication gates.

For this development session the owner authorized self-review and merge
without external-review or CodeGraph gates. No external PASS is claimed.
