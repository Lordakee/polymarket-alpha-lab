# Prospective crypto research launch

## Why this entry exists

An empty resolution worklist is normal for a new private database. Do not add
synthetic markets to the user's database to make it look active. This node connects
real caller-selected BTC/ETH tasks to the already existing captured researcher:

**Explicit market + future forecast cutoff -> Gamma eligibility -> matching
Coinbase/Kraken observations -> operator review of terms -> committed prospective
market registration/claim -> bounded model/tools loop -> captured result -> worklist.**

The new launch service uses existing readers, input gates, DSN/instance guard,
claim/capture transactions, evaluation and resolution worklist. It adds no database,
SQL migration, file journal, secret reader, model default, trading or autonomous
schedule. The existing 63 migrations and their manifest are unchanged.

## Public preview (no database, no model)

Use a real canonical Yes/No market selected by the operator, its exact condition
ID, a timezone-aware future forecast cutoff strictly BEFORE its scheduled end,
and a record ID reserved for this task. Team/source relevance requires manual
review: a BTC price feed is not automatically relevant to every BTC-related event.

```powershell
.\.venv\Scripts\python.exe scripts/preview_crypto_research.py --record-id YOUR_TASK_ID --team crypto_btc --condition-id YOUR_CONDITION_ID --market-slug YOUR_MARKET_SLUG --forecast-cutoff YOUR_AWARE_ISO_CUTOFF --model YOUR_MODEL_LABEL --allow-public-fetch
```

Omit `--allow-public-fetch` for configuration-only validation with no network. It
does not take `--root`, discover databases, read credentials or invoke a model.
For an unexecuted preview, an explicit label such as `operator-model-not-selected`
is acceptable; replace it with the actual caller-selected model label before
launch. This label is not a model request and no synthetic forecast is produced.

On opt-in, the preview attempts at most three public GETs through the existing
fixed-origin readers. Gamma is checked first so a closed/wrong/malformed market
stops before fetching venues. Source windows use three hourly bars by default
(`--lookback-hours` 1..24), ending one hour before the current UTC hour, avoiding
the newest uncommitted bar. No arbitrary URL, date backfill or source fallback.
Existing cross-source policy defaults (including 100 basis point tolerance) apply;
these are engineering checks, not calibrated trading or confidence parameters.

A successful JSON report has `status=prepared`, `readiness_only=true`,
`model_called=false`, `database_written=false`. It displays the untrusted market
question/rules for operator inspection, source capture hashes, time window,
required source IDs, comparison count, limits and `terms_sha256`. It contains no
probability or evidence of model quality. Raw snapshots are retained in the Python
preview object in memory before normalization, not written to a new file store.
Errors return fixed codes and stop, not fake observations or a default 50% forecast.

The approval hash binds condition/slug/team/question/rules/forecast cutoff. It does
NOT bind moving quotes, volume or scheduled-end metadata. Scheduled end is displayed
and independently revalidated to remain after the explicit cutoff on each new
preparation. End date is not a verified resolution timestamp. Approval is a caller
assertion, not an authenticated identity, signature or truth check.

## Explicit captured execution (Python API)

This node deliberately adds no CLI key prompt, environment token discovery or paid
model default. The application must already have an approved model factory. No
live model call was necessary to develop/test this code. Operator opt-in and
model-provider data/cost approval remain separate from a public preview.

```python
from pathlib import Path
from polymarket_alpha_lab.research_crypto_launch import CryptoResearchSpec
from polymarket_alpha_lab.research_crypto_launch_service import fetch_crypto_research_preview
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres

# Use actual operator-selected identifiers, aware cutoff and actual model label.
spec = CryptoResearchSpec(
    record_id=record_id, team_id=team_id, condition_id=condition_id,
    market_slug=market_slug, forecast_cutoff_at=forecast_cutoff, model_id=model_id,
)
preview = fetch_crypto_research_preview(spec, allow_public_fetch=True)
metadata = preview.to_dict()
# Present question/rules/cutoff/source applicability and model limits to operator.
# reviewed_terms_hash is approved by the operator; do not auto-approve this output.
with ProjectPostgres(Path(actual_database_project_root)).session() as session:
    receipt = session.launch_crypto_research(
        spec=spec, preview=preview, approved_terms_sha256=reviewed_terms_hash,
        model_factory=approved_model_factory,
        allow_public_fetch=True, allow_model_calls=True,
    )
    metadata = receipt.to_dict()
    worklist = session.resolution_worklist().to_dict()
```

The explicit database root must be the actual directory containing the original
`pyproject.toml`, `database/migrations.lock.json` and initialized `.local/postgres`.
A download/acceptance wrapper directory containing `kit/` is NOT that root. Do
not initialize the wrapper or silently search for an unrelated database. A new
source checkout can use an original initialized root without copying its `.local`
or overlaying its immutable application bundle.

Before fetching data, the launch service reads an existing record ID through the
current managed connection. Matching scope, cutoff, model/configuration and approved
terms return the original captured/incomplete state without fresh public/model
requests. Changed scope/configuration/approval conflicts. Stored database times
are never regenerated. Supply the same spec/approval to inspect or replay; changing
task IDs is not a recovery mechanism.

A new valid request reuses the existing execution runner. It atomically registers
the previously absent market and claims the task, commits, then starts the model.
The database clock enforces prospective registration and maximum data age (300s
start-delay default). A late preview cannot backdate a prediction. The model must
actually read/cite BOTH approved sources. Normal factory/model failures and blocked
model results are saved as failed/blocked attempts, not discarded.

Research configuration determines protocol cohort: lookback, limits and comparison
policy, not task ID, market, outcome, cutoff or approval digest. Team/model remain
separate evaluator grouping keys. This keeps like-for-like observations together
and prevents a new task ID alone bypassing the prior-incomplete guard. The injected
factory's actual model identity is still caller-asserted, not authenticated by a
model label. Do not change configuration just to hide an incomplete attempt.

## Failure and audit limits

Input/transport/source/approval failures occur BEFORE any research claim. They
raise and are not durable research attempts; this is not a complete audit of all
abandoned preflights. Full original Gamma/Coinbase/Kraken byte bodies are held only
in the preview's memory; existing captured requests retain normalized question,
rules, eligible evidence, source hashes and budgets, not a new raw-snapshot table.
Do not claim raw bytes can all be reconstructed from that database receipt.

If capture fails after research, the existing execution result retains `pending_run`
in memory for existing capture-only retry, without refetching or recalling a model.
If an incomplete claim has lost its result, it remains incomplete and blocks complete
history evaluation. There is no automatic model retry or crash reset. Concurrent
callers may duplicate public preflight GETs; the existing claim still permits at
most one research loop per task, not exactly-once HTTP. Provider token limits are
accounted after replies and are not hard spending or wall-clock ceilings.

A completed uncalibrated report is not an approved forecast or a trade. No account,
wallet, order mutation, automatic outcome, new release/update mechanism, migration
or backup operation is introduced here. Real public data and live model quality
must be reported separately from synthetic test results.

## Acceptance

The new focused tests exercise pure gates and scripted public readers without
live I/O. The optional native Windows proof runs the production managed API from
an EMPTY temporary database, captures a synthetic model report, replays eight
concurrent duplicate requests without refetch/model work, captures factory failure,
retains an incomplete claim, rejects changed-task-ID bypass, and checks worklist
and restart readback. It uses isolated project-native PostgreSQL, not a user DB.
Final head, tree, exact counts and CI evidence are recorded in the PR.

Protocol references checked 2026-09-13:
- https://docs.polymarket.com/api-reference/markets/get-market-by-slug
- https://www.postgresql.org/docs/current/transaction-iso.html
