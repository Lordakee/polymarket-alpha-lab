# Gamma context and scoped evidence intake

## What this node connects

This adds an application-facing path from an explicit public Gamma market GET
and an existing approved `ResearchEvidence` collection to the bounded research
Agent introduced in PR #3:

```text
explicit Gamma GET -> raw in-memory snapshot
                             |
caller-approved evidence -> identity/time/binary-market/rules intake
                             |
                 prepared TeamResearchTask
                             |
                 model -> tools -> cited report
```

The collector uses the official `GET /markets/slug/{slug}` endpoint. Market
questions and `description` come from that response rather than manual task
re-entry. **The description is resolution context, not independent evidence.**
No Gamma metadata, prices, nested event payloads or resolution-source links
are automatically turned into research sources. At least one eligible evidence
record must be separately supplied. The intake cannot prove that a caller's
record is independent or truthful; it enforces structural identity and time.

The source may be a previously collected public record or an approved local
Supabase/Postgres readback converted by the application into `ResearchEvidence`.
This node does not implement additional domain source collectors or DB readback
adapters. No database, cache, journal, new durable backend or file input loader
is introduced. All raw/normalized objects and receipts exist in memory only.

## Modules

- `team_research_gamma.GammaResearchReader`: explicit opt-in public GET.
- `team_research_intake.GammaMarketSnapshot`: exact raw response bytes, slug
  and retrieval time; SHA256 and fixed source reference are derived properties.
- `prepare_team_research_from_gamma`: pure intake; returns `prepared` or
  `blocked` with a closed reason code. It never contacts a model or network.
- `ResearchSourceReceipt`: full-record canonical SHA256, source ID, reference
  and observation time, bound to the exact prepared evidence.
- `team_research_market_pipeline.run_team_research_from_market_snapshot`:
  intake followed by the existing Agent, constructing a caller-supplied model
  client **only after** intake succeeds.

Existing package-root exports, legacy client, CLI, builders, BTC publication
service, strategy cycle, dependencies, lockfile and persistence are unchanged.
The generic public client remains intact; the new reader is intentionally
narrow and bounded rather than inheriting its configurable origins/unbounded
response handling. It has no endpoint override and does not follow any URL
returned in a market description or `resolutionSource` field.

## Intake policy

The application's expected condition ID and snapshot slug must exactly match
Gamma's `conditionId` and `slug`. The selected team remains an application/router
assignment; this node does not infer it from a question or reassign research.
All evidence must match both team and condition, have unique source IDs, and
preserve the hard `paper_only/report_only/readonly` flags.

`active` must be exact `true`, `closed` exact `false`, and `archived`, when
present, exact `false`. Unknown or stringified booleans do not pass. Only an
exact two-outcome YES/NO market is supported, case-insensitively, in either
array order. JSON-encoded outcome strings and arrays are accepted; Up/Down,
multi-outcome and ambiguous labels are blocked, not guessed or remapped.

Question and description must be nonblank and fit the existing Agent limits
(2,000 and 4,000 characters). Missing or oversized rules block the intake;
there is no silent truncation and no fallback to a nested event's description.
Treating `description` as resolution context does not prove that it completely
captures all settlement conditions. Semantic/operator review is still needed.

`endDate` must be an explicit timezone-aware timestamp strictly after `as_of`.
A present/non-null `updatedAt` must also be aware and no later than retrieval.
Its age is not used as retrieval freshness: unchanged rules may have an old
update time. Missing/null `updatedAt` remains unknown and is not invented.
Retrieval itself must be at or before `as_of`, and at most 300 seconds old by
default (configurable 0–86,400). Newly fetched data cannot pass an earlier
as-of check. A caller reconstructing a historical snapshot is responsible for
providing a genuine capture time; the hash is not an authenticity signature.

Evidence freshness uses the same `ResearchAgentLimits` as the Agent runtime,
not a second inconsistent default. Future and stale records are omitted and
their IDs recorded; the inclusive age boundary remains usable. If no eligible
source remains, intake blocks. Cross-scope or malformed caller inputs raise
before model construction rather than being partially processed.

`prepared` means the input contract passed, **not** that a forecast is ready.
A completed Agent result is still an uncalibrated research candidate. No
conversion to approved `TeamForecastPacket`, allocation, publication, cost,
risk or execution authorization is added. Every output remains paper-only,
report-only and readonly.

## Explicit application use

```python
from datetime import UTC, datetime
from polymarket_alpha_lab.team_research_gamma import GammaResearchReader
from polymarket_alpha_lab.team_research_market_pipeline import run_team_research_from_market_snapshot

# market_slug, expected_condition_id and team_id come from your approved router.
# approved_evidence is a tuple of already collected, scoped ResearchEvidence.
# model_factory returns your explicitly configured ResearchModel client.
snapshot = GammaResearchReader(allow_public_fetch=True).fetch(market_slug=market_slug)
run = run_team_research_from_market_snapshot(
    snapshot,
    task_id=task_id,
    team_id=team_id,
    condition_id=expected_condition_id,
    as_of=datetime.now(UTC),
    evidence=approved_evidence,
    model_factory=model_factory,
)
if run.research is None:
    print(run.intake.reason_code)  # No model client was constructed.
else:
    print(run.research.status, run.research.reason_code)
```

The public reader is inert until enabled and `fetch()` is called. It uses one
GET to a fixed HTTPS origin, TLS verification defaults, no cookies or auth,
no redirect or environment-proxy discovery, a 1 MiB raw-body limit, a bounded
network timeout (default 15 seconds), and no retries. Current reader timestamps
are taken after the response body is read, not supplied by a model. Reader
exceptions expose only a fixed failure code. Network timeouts are per blocking
operation, not an absolute deadline against a slow streaming peer.

The response body remains untrusted even after successful retrieval: intake
still validates JSON (including duplicate keys/nonfinite constants), scope,
market state and timestamps. Receiving a snapshot is not intake success.
Unselected raw fields remain in the in-memory snapshot but never enter model
messages. No raw response or evidence text is printed by this pipeline.
Caller-provided evidence and references must already be public/redacted and
approved for the chosen model provider; automatic sensitive-content redaction
is not implemented. Neither the collector nor intake accesses model credentials.

## Reproduction and verification

After a normal editable project installation:

```bash
python scripts/run_market_research_demo.py
python -m pytest -q tests/test_team_research_intake.py tests/test_team_research_gamma.py
python scripts/verify_local.py --full
```

The demonstration is fully synthetic and uses a scripted model. Its output
explicitly reports `synthetic_demo=true`, `public_network_called=false` and
`live_model_called=false`. It exercises intake, evidence receipts and the real
three-step tool loop, not a paid model or live Gamma data. The test suite uses
fake HTTP responses; no successful live Gamma or model request is claimed.

Tests cover all ten teams, reversed YES/NO labels, missing/invalid market fields,
exact boundary timestamps, cross-scope sources, no-evidence model suppression,
receipt/content binding, snapshot copies, raw-field isolation, transport origin,
redirect/proxy policy, size/status/MIME rejection and error-response cleanup.
Final focused/full totals, self-review findings, Git revisions and tree equality
belong in the PR acceptance record. The owner authorized self-review and merge
without external review/CodeGraph gates; no external PASS is implied.

Official source contract:
https://docs.polymarket.com/api-reference/markets/get-market-by-slug


## Absolute-time freshness across timezone changes

Market-snapshot age and evidence age are measured between UTC instants, not
between local wall-clock labels. The direct team agent applies the same rule
when building its evidence catalog; bypassing the intake helper does not bypass
freshness filtering. At a fall-back transition, a later instant can have an
earlier (or identical) local clock reading. At spring-forward, a two-minute
observation can appear more than an hour old in local-clock subtraction.

Future evidence is excluded. Exactly-at-the-age-limit evidence stays eligible;
one microsecond older is excluded. If no usable evidence remains, intake does
not construct the model factory, and the direct agent does not call its supplied
model. No budget, tool, persistence or source-selection policy is changed.

Conversions are calculation-only: the original source times, offsets, fold,
raw payload, task/result timestamps and receipt fields remain unchanged. Evidence
hashes retain the existing UTC canonical JSON format. UTC conversion happens
before dataclass copying in the hash helper, so valid non-picklable timezone
objects (including `ZoneInfo.from_file`) do not fail during deepcopy. This does
not rewrite stored records or retroactively certify old results.

Tests use synthetic UTC pairs across New York one-hour and Lord Howe half-hour
transitions, UTC/mixed-zone representations, exact age boundaries and scripted
models. The runtime `tzdata` dependency supplies test zones; no public provider,
user database or paid model is needed. The staged, unpublished candidate-selector
implementation is not part of this correction.

Python behavior reference (checked 2026-09-14):
https://docs.python.org/3/library/datetime.html#datetime-objects

### Complete report serialization

The capture codec, prospective request copier and evaluation-record fingerprint
also project validated dataclass values without deep-copying timezone objects.
Their existing canonical JSON/UTC field format and closed decoder schemas remain
unchanged. A source run is not mutated: copied database request/record values
normalize to UTC as before. The private value projection is not a database layer
or payload decoder and never constructs a class selected by serialized input.
Unsupported value types still fail closed; flags, receipt binding, canonical
round-trip and size checks remain in the existing validation/codec boundaries.

Regression checks compare identical original payloads represented using stream
zones versus ordinary fixed offsets across both folds, through completed, failed
and intake-blocked runs. Their capture payloads, request hashes and evaluation
results must match byte-for-byte. The native lifecycle proof additionally creates
its first research request with a stream-loaded timezone, then uses the normal
prospective claim, persistence, replay and restart path. No stored history is
rewritten and no independent source-truth claim is added.
