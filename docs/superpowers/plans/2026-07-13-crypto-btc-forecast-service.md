# Crypto BTC Forecast Service Implementation Plan

**Status:** Node 7, final program node. Plan authored before implementation. Node 5 is present only as a local uncommitted candidate; its landing commit and review verdict are pending at plan-authoring time.

**Goal:** Add one paper-only, report-only, readonly BTC forecast service that evaluates Node 6 policy evidence, reduces it through Node 2C, applies the combined BTC-policy and aggregation readiness gate, builds the Node 3 envelope, and persists every representable validated attempt through Node 5's sole atomic local-Supabase/Postgres writer. Add the service exports, final documentation, and fake-backed integration coverage. Strategy-cycle consumption remains a separately reviewed future node.

## Architecture And Handoff

Use one production module:

```text
src/polymarket_alpha_lab/crypto_btc_forecast_service.py
```

The module is orchestration only. It must not contain SQL, psycopg connection logic, environment reads, loaders, latest-attempt selection, strategy-cycle wiring, or side-selection logic. The default persistence binding is Node 5's primary writer:

```python
insert_team_evaluation_attempts_with_psycopg(
    dsn: str,
    envelopes: tuple[TeamForecastBuildEnvelope, ...],
    *,
    table_name: str = "team_evaluation_attempts",
) -> tuple[Any, ...]
```

`persist_team_evaluation_attempts_with_psycopg` remains the reviewed alias but is not the service default. The service accepts an injected writer for tests and forwards only `config.dsn`, a one-envelope tuple, and `config.table_name`.

Node 7 must begin from the clean commit that lands the current Node 5 implementation:

```text
NODE_BASE=NODE5_LANDED_COMMIT
```

`NODE5_LANDED_COMMIT` is an operational placeholder, not a guessed SHA. It is resolved only after Node 5's implementation commit, focused tests, full-suite verification, Codex review, and clean-worktree gate pass. Current `HEAD=42614e5b` is the Node 5 plan commit and is not a valid Node 7 implementation base. Any Node 5 interface drift, review-requested change, or failed gate requires the Node 7 plan and handoff to be amended before implementation.

## Fixed Public Service Surface

Define exactly three new names in the service module and package root:

```python
CryptoBtcForecastServiceInput
CryptoBtcForecastServiceResult
evaluate_and_persist_crypto_btc_forecast
```

The input dataclass is frozen, slotted, and hard-flagged:

```python
@dataclass(frozen=True, slots=True)
class CryptoBtcForecastServiceInput:
    condition_id: str
    market_slug: str
    event_template: str
    resolution_contract: CryptoBtcResolutionContract
    incident_gates: CryptoBtcIncidentGates
    evidence_inputs: tuple[CryptoBtcEvidenceInput, ...]
    evaluated_at: datetime
    scope: TeamForecastEvaluationScope
    run_metadata: TeamForecastRunMetadata
    evaluator_receipts: tuple[TeamForecastEvaluatorReceipt, ...]
    legacy_forecast_packet: TeamForecastPacket | None
    legacy_evidence_packets: tuple[TeamForecastEvidencePacket, ...]
    persistence_config: SupabaseTeamEvidenceAggregationConfig
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
```

The successful result is also frozen, slotted, and hard-flagged:

```python
@dataclass(frozen=True, slots=True)
class CryptoBtcForecastServiceResult:
    policy_evaluation: CryptoBtcEvidenceEvaluation
    aggregation_result: TeamEvidenceAggregationResult
    publication_status: str
    reason_codes: tuple[str, ...]
    envelope: TeamForecastBuildEnvelope
    write_results: tuple[object, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
```

The callable signature is:

```python
def evaluate_and_persist_crypto_btc_forecast(
    service_input: CryptoBtcForecastServiceInput,
    *,
    evaluator: Callable[..., CryptoBtcEvidenceEvaluation] | None = None,
    writer: Callable[..., tuple[object, ...]] | None = None,
) -> CryptoBtcForecastServiceResult
```

`evaluator=None` binds to `evaluate_crypto_btc_evidence`. `writer=None` binds to `insert_team_evaluation_attempts_with_psycopg`. Injection is for deterministic tests; it must not create an alternate production persistence path.

## Exact Predecessor Interfaces

Node 6:

```python
evaluate_crypto_btc_evidence(
    *,
    condition_id: str,
    market_slug: str,
    event_template: str,
    resolution_contract: CryptoBtcResolutionContract,
    incident_gates: CryptoBtcIncidentGates,
    evidence_inputs: tuple[CryptoBtcEvidenceInput, ...],
    evaluated_at: datetime,
) -> CryptoBtcEvidenceEvaluation
```

The evaluation exposes `evaluated_at`, policy `status`, canonical `records`, `current_selections`, Node 2 `config`, resolution assessment, and deterministic policy `reason_codes`. Its `ready` status is only the BTC policy gate.

Node 2C:

```python
build_team_evidence_aggregation_result(
    aggregation_input: TeamEvidenceAggregationInput,
    *,
    config: TeamEvidenceAggregationConfig,
) -> TeamEvidenceAggregationResult

validate_team_evidence_aggregation_result(
    result: TeamEvidenceAggregationResult,
    *,
    aggregation_input: TeamEvidenceAggregationInput,
    config: TeamEvidenceAggregationConfig,
) -> None
```

The service constructs `TeamEvidenceAggregationInput` from the Node 6 evaluation's `evaluated_at`, `records`, and `current_selections`, then uses the evaluation's exact `config`.

Node 3:

```python
build_team_forecast_build_envelope(
    result,
    *,
    aggregation_input,
    config,
    scope,
    run_metadata,
    evaluator_receipts,
    legacy_forecast_packet,
    legacy_evidence_packets,
) -> TeamForecastBuildEnvelope
```

The same arguments must be supplied to `validate_team_forecast_build_envelope` before persistence. For a non-ready Node 2 result, Node 3 requires `legacy_forecast_packet=None` and `legacy_evidence_packets=()`. For a ready result it requires a forecast template and one evidence template per accepted receipt.

Node 4 configuration is:

```python
SupabaseTeamEvidenceAggregationConfig(
    enabled: bool,
    dsn: str | None,
    table_name: str = "team_evaluation_attempts",
)
```

The service accepts this object and does not read environment variables. The supported environment family remains:

```text
POLYMARKET_ALPHA_LAB_TEAM_EVIDENCE_AGGREGATION_DB_ENABLED
POLYMARKET_ALPHA_LAB_TEAM_EVIDENCE_AGGREGATION_DB_DSN
POLYMARKET_ALPHA_LAB_TEAM_EVIDENCE_AGGREGATION_DB_TABLE
```

The service requires `enabled is True` and a non-`None` DSN. Node 5 remains responsible for final DSN validation and connection ownership.

## Locked Service Flow

- [ ] **RED — Input and boundary tests:** Prove exact input types, canonical strings, aware UTC time, tuple shapes, hard flags, packet-template types, exact Node 4 config, enabled persistence, and no writer call for any invalid input. Prove malformed evaluator output fails before the writer.

- [ ] **GREEN — Input/result implementation:** Implement the two exact dataclasses and callable defaults. Preserve all predecessor objects without mutation. Do not read the environment or construct a database adapter directly.

- [ ] **RED — Evaluation and aggregation tests:** Fake the evaluator with ready, watch, and blocked `CryptoBtcEvidenceEvaluation` values. Assert the exact Node 6 keyword call. Construct Node 2 input from evaluation records/selections, call `build_team_evidence_aggregation_result`, then call `validate_team_evidence_aggregation_result` before any writer activity.

- [ ] **GREEN — Status and reason composition:** Define the service-level `publication_status` with exact precedence:

  ```text
  blocked if either policy or aggregation status is blocked
  watch if neither is blocked and either status is watch
  ready only when both statuses are ready
  ```

  Define service-level `reason_codes` as the sorted, duplicate-free union of the Node 6 policy reason codes and Node 2 aggregation reason codes. Do not rewrite either predecessor tuple, inject service codes into Node 2, or mutate Node 3 receipts. The persisted Node 5 row continues to expose the canonical Node 2 aggregation status; the service-level combined status is returned separately.

- [ ] **RED — Packet and persistence matrix:** Cover every representable combination:

  | Policy | Aggregation | Packets | Envelope | Writer |
  | --- | --- | --- | --- | --- |
  | ready | ready | forecast plus evidence | packeted | exactly once |
  | ready | watch/blocked | none | packetless | exactly once |
  | watch/blocked | watch/blocked | none | packetless | exactly once |
  | watch/blocked | ready | none required | currently unrepresentable | zero calls |

  For every non-ready aggregation, call Node 3 with `None` and `()`. Persist one packetless attempt through Node 5. For both-ready input, pass the caller's legacy templates unchanged except for Node 3's reviewed V1 ID projection. Never select or reorient a side; the central cost engine remains the future owner of final YES/NO/none selection.

- [ ] **GREEN — Orchestration implementation:** Validate the Node 3 envelope by rematerialization, then call exactly:

  ```python
  writer(
      service_input.persistence_config.dsn,
      (envelope,),
      table_name=service_input.persistence_config.table_name,
  )
  ```

  Require one returned write result and preserve it in `write_results`. No direct store call, loader call, SQL, psycopg import, or alternate persistence path is allowed.

## Required Contract Amendment Gate

The combination `policy status in {watch, blocked}` with `aggregation status == "ready"` cannot currently be represented safely. Node 3 decides packet construction from `result.status`; a ready result rejects empty packet templates, while a non-ready envelope requires a non-ready result. Node 7 must not forge or mutate a Node 2 result, bypass Node 3 validation, or silently drop the attempt.

This is a hard pre-implementation stop. A separate reviewed Node 3 amendment must define the canonical external-policy gate representation, envelope identity implications, validation behavior, and persistence semantics. After that amendment, Node 3 and Node 5 reviews and the `NODE5_LANDED_COMMIT` handoff must be refreshed. Until then, Node 7 implementation does not begin; integration tests must retain a regression proving zero writer calls for this combination.

## Exports, CLI, And Documentation

- [ ] **RED/GREEN — Exports:** Set the service module `__all__` exactly to the three service names above. Add exactly those three names to `src/polymarket_alpha_lab/__init__.py` and no Node 2, 3, 5, or 6 names. Update `tests/test_init.py` with import identity assertions and negative assertions for predecessor names. Do not modify `tests/test_team_evidence_aggregation_scope.py`; the service-only root names avoid its Node 2 allowlist.

- [ ] **RED/GREEN — Documentation:** Add one module/test row to `docs/index/phase1-module-index.md`, update `tests/test_phase1_docs_module_index_matches_files.py` to require that pair, and add a README Node 7 status/API section describing local paper-attempt persistence and the combined gate. Do not add a CLI command or modify `team_cli_wiring.py`; strategy-cycle CLI wiring is deferred.

## Exact Sorted Allowlist

Only these paths may change:

```text
README.md
docs/index/phase1-module-index.md
src/polymarket_alpha_lab/__init__.py
src/polymarket_alpha_lab/crypto_btc_forecast_service.py
tests/test_crypto_btc_forecast_service.py
tests/test_crypto_btc_forecast_service_integration.py
tests/test_crypto_btc_forecast_service_scope.py
tests/test_init.py
tests/test_phase1_docs_module_index_matches_files.py
```

Physical ceilings:

```text
crypto_btc_forecast_service.py                         <= 700
test_crypto_btc_forecast_service.py                    <= 900
test_crypto_btc_forecast_service_integration.py       <= 950
test_crypto_btc_forecast_service_scope.py             <= 550
new Node 7 test aggregate                             <= 2,400
README.md targeted addition                            <= 70 lines
phase1-module-index.md targeted addition               <= 8 lines
tests/test_init.py targeted addition                   <= 45 lines
tests/test_phase1_docs_module_index_matches_files.py   <= 8 added lines
```

No Node 2, Node 3, Node 5, Node 6, migration, CLI, or strategy-cycle file belongs to this allowlist.

## Verification And Stop Conditions

- [ ] Run focused service, integration, scope, package-root, and module-index tests with the sanitized environment.
- [ ] Run `compileall`, sanitized full pytest, `scripts/verify_local.py --full`, `git diff --check`, secret scans, and Phase 1 boundary scans.
- [ ] Record CodeGraph as `pass` only if synchronization succeeds; otherwise record `documented-unavailable` and make no synchronization claim.
- [ ] Submit the complete Node 7 range to the authorized read-only Codex review using `gpt-6-astra` with reasoning effort `max`; require final nonblank line `VERDICT: PASS`.

Stop for Node 5 not landing cleanly, a pending or non-PASS Node 5 review, any predecessor signature drift, unresolved Node 3 gate conflict, writer activity before validation, packet leakage, mutation of Node 2 results, policy reason loss, direct persistence bypass, non-Node-7 package-root exports, line/import/scope violations, failed focused or full tests, compile failure, secret leakage, or non-PASS review.

## Final Program Closure Evidence

The completion record must list:

- resolved `NODE5_LANDED_COMMIT` and the Node 5 review verdict;
- Node 6 reviewed-PASS handoff and all fixed predecessor signatures;
- exact sorted Node 7 allowlist and clean worktree;
- focused tests, fake-writer call-order proofs, combined-status matrix, compile, full suite, local verifier, diff, secret, and Phase 1 boundary results;
- package-root export, README, module-index, and module-index matcher updates;
- CodeGraph status as `pass` or `documented-unavailable`;
- explicit proof that all durable attempts use Node 5's local Supabase/Postgres writer.

Strategy-cycle consumption, latest-attempt reading, central cost-engine side selection, live execution, account/authentication work, and push/remote publication gates remain explicitly outside Node 7. Local Node 7 completion must not be reported as remote publication or full program release closure.
