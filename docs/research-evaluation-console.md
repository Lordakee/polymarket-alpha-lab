# Read-only project research evaluation console

## Purpose and use

Run the existing captured-history evaluator without writing Python glue. This
is a view of research already in the project-private native PostgreSQL instance,
not a research launcher, model selector, new storage layer or trading dashboard.
No public API, model, operator confirmation, outcome fetch or business write is
performed. No SQL migration or dependency change is required for this feature.

Install the existing locked project environment with `uv sync --locked --extra
postgres`, then run from an already initialized source or newly built kit:

```powershell
.\.venv\Scripts\python.exe scripts/evaluate_project_research.py
```

A new source checkout can explicitly point at an original initialized project:

```powershell
.\.venv\Scripts\python.exe scripts/evaluate_project_research.py --root "C:\path\to\actual-project"
```

Use the actual root containing `pyproject.toml`, `database/migrations.lock.json`
and `.local/postgres`, not an extraction wrapper. This command does not initialize,
import, migrate, restore or reset a database. Do not copy `.local` or overlay a new
kit on an existing installation. Existing downloaded kits are not automatically
updated. `--help` needs no database. There is no caller DSN option or cloud fallback.

The managed session can start an initialized stopped private instance, and stops
only one it started itself. A previously running managed instance remains running.
Normal database runtime logs/WAL may change; **read-only means no application
business writes**, not a byte-frozen server directory. Existing path/instance/
role/migration/environment checks remain active; the console cannot bypass them.

## Historical views and configuration

```powershell
.\.venv\Scripts\python.exe scripts/evaluate_project_research.py --as-of "2026-09-12T12:00:00+08:00" --include-decisions
```

The timestamp is an explicitly zoned ISO value; a missing timezone or invalid
configuration fails before a manager is constructed. The existing database clock
rejects future report times. Historical visibility is based on recorded/claimed
receipt time, not a model-supplied date. A later outcome is not included in an
older snapshot. `--as-of` is a historical view, not an authorization to backfill.

The console calls **ProjectResearchSession.evaluate()**, which invokes the strict
existing complete-execution loader in one read-only repeatable-read snapshot.
There is no fallback to the legacy non-strict evaluator, skip-incomplete option,
success-only filter, group filter or recent-record truncation.

`--max-records` defaults to 10,000, range 1..10,000. The loader applies this to
attempts and outcomes separately; its existing 32 MiB payload cap also applies.
Exceeding a cap returns a block, never a score computed from truncated history.
`--buckets` accepts 2, 5, 10 or 20. `--min-sample-count` defaults to 30 and
`--min-bin-count` to 5, each 1..10,000. These are descriptive diagnostic settings,
not confidence levels, fitted calibration or forecast approval thresholds.

## Output and interpretation

On a completed read, exit code 0 and `status=evaluated` mean the query and
serialization completed. They do NOT imply good forecasts or approval. The
nested `evaluation_status` distinguishes:

| Status | Interpretation |
| --- | --- |
| `no_visible_attempts` | No captured attempts visible at this time. This does not say there are no registered markets or outcomes; orphan outcomes have a separate count. |
| `no_scored_forecasts` | Attempts exist, but none is currently scorable. Decision counts explain pending outcomes, failed/blocked research, late reports or subsequent attempts. |
| `diagnostics_available` | At least one decision was scored. Per-group sample warnings and other limitations still apply. |

Each group's original Brier score, log loss, neutral baseline, reliability bins
and sample status are preserved exactly. Empty scores remain null. An erroneous
certainty retains `log_loss_status=infinite`, a null numeric mean and its explicit
infinite-loss count; it is not clipped to a finite score or printed as JSON NaN.
Small samples remain `insufficient_sample`. No pooled score or model ranking is
computed, and `forecast_approval_performed` always remains false.

`scored_decision_count` can include the same event in different team/model/protocol
groups. `scored_condition_count` counts distinct scored event IDs, so repetitions
are not labeled additional independent events. Neither count measures statistical
independence between different events. The first recorded attempt per group/event
remains selected even if a later retry is better; failures are not removed.

Default output includes group IDs/configuration, aggregate decision counts and the
existing input digest, but no per-record decision list. `--include-decisions`
adds the existing canonical per-record IDs, reasons, probabilities and hashes.
Neither mode exports evidence text, model summaries, prompts, raw API bodies or
source URLs. Identity labels and probabilities may still be business-sensitive;
this is local diagnostic output, not an anonymization guarantee or public upload.
The console prints JSON to stdout and does not persist a new report file/journal.

## Failures and completion boundaries

Exit 1 with `status=blocked` and `evaluation=null` exposes only these exact known
reasons: `research_execution_history_incomplete`, `research_capture_history_limit`,
`research_evaluation_from_future`. An incomplete claim anywhere in the visible
execution history blocks the whole read, including claims for settled events.
It is NOT interpreted as empty history and cannot produce partial group scores.

Other exceptions use the fixed `research_evaluation_operation_failed` code with
no raw database error, DSN or filesystem path. A session-close failure suppresses
an otherwise computed success report. There is no automatic retry, partial result
fallback or automatic repair. Interrupts are not disguised as normal DB failures.
Argument errors exit 2. Do not delete claims/data or relax checks to get exit 0.

A successful history gate establishes only the existing visible claim/result
completeness check in that database snapshot. It does not authenticate external
sources, audit every historical operator decision, prove no unregistered work was
omitted or independently certify old outcomes. Older records and all scoring
formulas remain unchanged. Use the separate resolution worklist for registered
markets that do not yet have captured attempts/outcomes.

## Acceptance scope

Offline tests cover output distinctions, exact existing scores, privacy of raw
content, later-attempt exclusion, per-group counts, historical visibility, invalid
arguments, fixed errors, interruptions and cleanup failure. An extended native
resolution test invokes the actual CLI against a fresh private instance for
empty/pending/scored/future/incomplete views and checks readback/row counts. The
actual kit test checks help without a cluster and evaluates one pending record
from the extracted kit's own Python environment. These use synthetic business
inputs, not a user's database or paid model. Final revision/counts belong in the PR.
