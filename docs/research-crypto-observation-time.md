# Calendar checks for terminal crypto observations

## Listing end is not the observation time

A market can still be listed as open after its relevant price observation. The
recent-hourly crypto launcher now requires a computable FUTURE observation,
separately from PR19's contract-shape gate and the existing operator approval.
This is a bounded calendar/template check, not general natural-language or
settlement-source verification. It does not infer probabilities or outcomes.

A successful input preview still has `status=prepared`. It also includes
`observation_schedule` and one of these `forecast_start_status` values:

- `blocked_by_contract_scope`: prior path/aggregate/unknown-shape restriction.
- `blocked_by_observation_time`: missing, ambiguous, inconsistent or elapsed time.
- `requires_operator_approval`: both mechanical checks pass; approval is NOT given.

Zero preview exit status remains input-readiness only. Both existing public
preview/discovery CLIs pass through the additional fields without changing their
network budget, retries or source selection. No database or model is opened.

## Supported date/clock forms

The existing terminal-price shape must pass first. The question must end in an
English named month/day, optionally with an explicit 20xx year. The year must be
present in that question or in a matching market slug suffix such as
`-on-september-13-2026`. If both supply dates they must agree. No year is taken
from today's clock, scheduled listing end or an operator-supplied verdict.
Invalid calendar dates are rejected, not rolled into a later month.

The Yes-condition must explicitly link its candle to the date in the title or
question. Supported clocks are `at 12:00 PM ET` (also other valid AM/PM times with
ET or UTC) and `12:00 in the ET timezone (noon)`. Multiple clock mentions,
unsupported date wording, conflicting named dates or relative-day overrides are
blocked. These deliberate restrictions can reject valid real-world descriptions.
Read the complete rules; this parser cannot authenticate their interpretation.

ET is interpreted as `America/New_York`, not a fixed UTC offset. The first-party
`tzdata` package is loaded directly through `importlib.resources` and
`ZoneInfo.from_file`, without host TZPATH or user timezone overrides. UTC uses
Python's fixed UTC zone. Summer/winter dates convert accordingly; nonexistent
spring-forward times and ambiguous fall-back times are blocked, never guessed.
The report identifies both package and IANA versions used for ET conversions.

`tzdata>=2026.2` is now a direct runtime dependency so Windows previews work even
without the postgres extra. The package/version/artifact hashes were already in
the lockfile through psycopg's Windows dependency; no existing package version
is upgraded. Normal `uv sync --locked` installs the now-required package.
No timezone data files or database engines are copied into Git. Missing/broken
package data blocks ET interpretation rather than silently using a different
host database. Source installations outside the lock may have different data;
reported version information is not a persistent certification record.

## Conservative pre-candle boundary

For a rule referencing the Close of the minute candle labeled noon, the derived
window opens at noon and its closing value is not available before the next
minute. This launcher conservatively requires:

`preview.as_of < forecast_cutoff_at < candle_open_at`

It does NOT wait until the minute has partly elapsed. Scheduled listing end must
not precede candle open, but may equal it; it does not become a final resolution
time. `candle_close_not_before` is simply one minute after the computed open,
not evidence that the source published the value or the event resolved then.

For example, a supported September 13, 2026 noon-ET expression yields open
16:00 UTC and close-not-before 16:01 UTC. A forecast cutoff at 16:00 is refused,
even if Gamma's listing end is later. A winter noon-ET expression uses 17:00 UTC.
An explicit missing/invalid year cannot be repaired using the later listing end.

`CryptoResearchPreview.request()` recomputes the schedule from the original
validated terms. Mutating the diagnostic JSON or approving the terms hash cannot
bypass a time rejection. Failure occurs before the normal captured runner can
register a market, claim the task or construct the model client. The same cutoff
is passed unchanged to the existing database-clock guard, so a delayed preview
cannot backdate a claim. This is not a wall-clock cancellation mechanism for a
model loop that runs past its cutoff; late-report evaluation remains unchanged.

## Compatibility and limits

There is no SQL migration, stored request/receipt rewrite, new evidence store,
model selection or token access. Original terms, hashes, cohorts and required
citations are retained. Existing task replay returns original captured/incomplete
state without a new forecast or retrospective time certification. Generic
multi-domain runners are not represented as enforcing this high-level policy;
do not use them to route around it.

`timestamp_computed=true` means this limited template was converted. Both
`observation_time_independently_verified` and `settlement_source_verified` remain
false. PR19's separate shape metadata still has `observation_time_verified=false`:
shape matching itself does not verify time. Sources, clarifications, comparison
semantics and actual authority still require operator review. USD hourly reference
feeds are not Binance USDT minute settlement data. Path-dependent/full-period
contracts remain unsupported and cannot be fixed by this calendar check.

Tests cover past observations with future listings, pre-open microsecond bounds,
missing/conflicting years, midnight, leap dates, summer/winter/DST folds and gaps,
missing timezone data, host-environment independence, mutated output and unchanged
legacy replay. Native Windows proof asserts a rejected past observation creates
zero market/claim/attempt rows, then retains the normal prospective capture flow.
The extracted Windows kit additionally computes an ET time using its own installed
dependency without source-tree or host timezone fallback. Actual results/revisions
are recorded in the PR; no user's database or paid model is needed for these tests.

Primary references checked 2026-09-14:
- https://docs.python.org/3/library/zoneinfo.html
- https://tzdata.readthedocs.io/en/latest/
- https://docs.polymarket.com/concepts/resolution
