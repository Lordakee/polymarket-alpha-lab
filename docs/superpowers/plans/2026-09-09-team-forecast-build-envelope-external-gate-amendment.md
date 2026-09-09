# Node 3 Contract Amendment: External Publication Gate

**Status:** Contract amendment plan only. Implementation starts after the Node 5 landing commit, its focused/full verification, and its required review gate. The current Node 5 changes are still an uncommitted candidate and are not a valid base.

## Spec and consumer decision

The core specification does not forbid this representation. Node 2 continues to own aggregation status and ready-only `publishable_probability_yes`; Node 3 owns the complete evaluation scope and legacy packet projections. The amendment adds a Node 3 projection gate without changing or mutating the Node 2 result.

Node 4 currently rejects any ninth top-level evaluation-scope key. Therefore the gate must not be added as a new top-level payload key. The typed gate is serialized only when supplied as the reserved nested field:

```text
evaluation_scope_payload["run_metadata"]["external_publication_gate"]
```

The value is a canonical direct field map containing `status`, `reason_codes`, `paper_only`, `report_only`, and `readonly`. This preserves Node 4’s exact eight-key top-level contract. Node 4’s full-payload hash changes for gated envelopes, while its promoted `status` remains the Node 2 aggregation status. Node 5 is agnostic because it receives the unchanged envelope and row interfaces.

The existing scope guard rejects the identifier component `external`. The public Python names therefore use `TeamForecastPolicyPublicationGate` and `policy_publication_gate`; the serialized JSON key remains `external_publication_gate` for audit clarity.

If a review determines that `run_metadata` is itself a closed contract and cannot carry this Node 3-owned extension, stop this amendment and request a separately reviewed Node 4/spec amendment. Do not move packet fabrication or suppression into Node 7.

## Contract to add

Add one exact public immutable type:

```python
@final
@dataclass(frozen=True, slots=True)
class TeamForecastPolicyPublicationGate:
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
```

The type must:

- accept only `ready`, `watch`, or `blocked`;
- canonicalize `reason_codes` to a sorted, duplicate-free tuple of canonical identifiers;
- preserve an empty reason-code tuple as valid because the external policy owns its vocabulary;
- require all three hard flags to be literal `True`;
- reject wrong exact types, invalid status values, malformed reason codes, and constructor-bypassed noncanonical values through the same fail-closed reconstruction pattern used by the amendment validator.

Extend both public callables with the same final keyword-only parameter:

```python
policy_publication_gate: TeamForecastPolicyPublicationGate | None = None
```

The exact builder parameter order is the current eight parameters followed by `policy_publication_gate`. The validator receives the same parameter in the same position and rematerializes with it.

The gate is not added as a field on `TeamForecastBuildEnvelope`; it is represented in the canonical scope payload and recovered through validator rematerialization.

## Semantics

Define:

```text
effective_ready =
    result.status == "ready"
    and (policy_publication_gate is None
         or policy_publication_gate.status == "ready")
```

When `policy_publication_gate is None`, the builder must remain byte-for-byte compatible with the current implementation. The scope payload has the current eight top-level keys, every existing `tea_id`, `tfr_id`, and `tfe_id` remains identical, and packet projections remain unchanged.

When a gate is supplied, add exactly this nested map to the fresh run-metadata payload:

```json
{
  "external_publication_gate": {
    "status": "watch",
    "reason_codes": ["policy_watch"],
    "paper_only": true,
    "report_only": true,
    "readonly": true
  }
}
```

The gate entry participates in the complete evaluation-scope preimage. Consequently, every supplied gate, including a `ready` gate, changes `tea_id`; `tfr_id` changes through both the tea identity and the run-metadata preimage; any emitted `tfe_id` changes through the new tea identity. Explicit `None` omits the nested field and preserves all legacy IDs.

If either the aggregation result or the supplied gate is non-ready, packet construction is suppressed:

```text
legacy_forecast_packet is None
legacy_evidence_packets == ()
evidence_replay_records == ()
```

The caller must provide `None` and `()` in that effective non-ready case. Nonempty templates fail closed, preserving the existing non-ready packet-argument rule and preventing silently discarded packet input.

A supplied ready gate plus a ready aggregation result follows the current ready projection: the forecast template is required, one evidence template is required per accepted receipt, the forecast probability is replaced with `publishable_probability_yes`, and replay records are created from the legacy evidence payloads.

This parallel rule does not contradict the specification’s ready-only publication section. Node 2 still exposes a publishable probability exactly according to its own `result.status`. The external gate controls whether Node 3 projects that already-valid result into legacy forecast/evidence packets. It never rewrites `result.status`, `publishable_probability_yes`, `reason_codes`, `core_digest`, or any Node 2 fragment.

## Red/green implementation and tests

- [ ] **RED — Public contract:** Extend the behavior tests with the new type, exact `__all__`, and the appended builder/validator parameter. Add invalid status, invalid reason-code tuple, false hard-flag, and constructor-bypass rejection cases.

- [ ] **GREEN — Type and serialization:** Implement `TeamForecastPolicyPublicationGate`, a private canonical entry helper, and conditional insertion into a fresh `run_metadata` payload. Keep the Node 2 validator as the first operation in every materialization path. Do not mutate `scope`, `run_metadata`, receipts, result, or predecessor payloads.

- [ ] **RED — Gate behavior matrix:** Add tests covering:
  - policy `watch` + aggregation `ready` with `None`/`()`: packetless envelope builds and validates;
  - policy `blocked` + aggregation `ready`: same packetless behavior;
  - policy `ready` + aggregation `ready`: packets are projected as today, while IDs differ from the gate-`None` envelope;
  - aggregation `watch`/`blocked` with any gate: existing packetless behavior remains intact;
  - non-ready effective status with packet templates: fail closed;
  - gate `None` versus omitted gate: equal scope payload bytes, equal envelope, and equal all IDs;
  - supplied gate versus `None`: canonical nested gate entry, changed tea/tfr IDs, and no gate-induced change to Node 2 fragments;
  - validator rematerialization rejects a tampered gate payload, mismatched gate argument, packet leakage, replay leakage, or hard-flag tampering.

- [ ] **GREEN — Validator symmetry:** Pass the exact gate argument through validator rematerialization. A valid gated envelope returns `None`; every gate, payload, packet, replay, or identity mismatch raises `ValueError`.

Existing pinned behavior tests that require expectation updates are exactly:

1. `test_locked_public_surface_is_exact`: append `TeamForecastPolicyPublicationGate` to `LOCKED_ALL` and append `policy_publication_gate` to the builder and validator parameter lists. This is a narrow additive API change with a default of `None`; all existing calls remain valid.
2. `test_node_3_ast_import_export_forbidden_surface_and_line_size_gate`: update the synthetic builder/validator signatures, exact export tuple, class-export set, and ceilings. The forbidden-surface rules remain unchanged.
3. `test_node_3_public_dataclasses_are_frozen_slotted_and_hard_flagged`: include the sixth public class in the explicit class-export set. Existing five classes retain their exact checks.
4. `test_node_3_package_root_has_no_node_3_exports`: derive the forbidden set from the expanded export tuple; no package-root export is added.
5. The behavior-module and scope-module contract docstrings must change `12-name` to `13-name` and document the optional gate.

No existing packet, receipt, fragment, legacy-hash, or tamper test is relaxed. `test_three_node2_fragments_are_bound_once_and_separately` keeps the same eight-key scope assertion because the gate is nested under `run_metadata`, not added at the top level. All current cases omit the parameter and therefore retain the legacy contract.

## Node 4 and Node 5 compatibility check

No Node 4 or Node 5 file may change in this amendment. After implementation, run the existing Node 4 row-codec tests and perform an in-memory gated-payload conversion proving:

- the eight top-level keys remain exact;
- the nested gate survives normalization;
- `payload_sha256` differs from the gate-`None` payload;
- `scope_key` remains derived from the unchanged domain context;
- the promoted row `status` remains the Node 2 result status;
- Node 5 accepts the resulting `TeamForecastBuildEnvelope` through its existing writer interface.

## Exact sorted allowlist

Only these paths may change, in literal sorted order:

```text
src/polymarket_alpha_lab/team_forecast_build_envelope.py
tests/test_team_forecast_build_envelope.py
tests/test_team_forecast_build_envelope_scope.py
```

No Node 2, Node 4, Node 5, Node 6, Node 7, package-root, migration, schema, or documentation implementation file belongs to this amendment.

## Locked public export tuple

Preserve the current twelve-name order and append the new type:

```python
__all__ = (
    "TeamForecastEvaluationScope",
    "TeamForecastRunMetadata",
    "TeamForecastEvaluatorReceipt",
    "TeamForecastEvidenceReplayRecord",
    "TeamForecastBuildEnvelope",
    "build_team_forecast_build_envelope",
    "validate_team_forecast_build_envelope",
    "team_forecast_evaluation_scope_payload",
    "team_evidence_aggregation_id",
    "team_forecast_run_id",
    "team_forecast_evidence_id",
    "team_forecast_legacy_payload_sha256",
    "TeamForecastPolicyPublicationGate",
)
```

The scope guard must explicitly classify all six public dataclasses as class exports.

## Physical ceilings

The current files are approximately 860, 1,075, and 497 lines against ceilings of 900, 1,100, and 500. Increase only the Node 3 ceilings needed for the additive contract:

```text
team_forecast_build_envelope.py          <= 980
test_team_forecast_build_envelope.py     <= 1,250
test_team_forecast_build_envelope_scope.py <= 550
Node 3 test aggregate                       <= 1,800
```

The increases provide bounded room for one immutable type, canonical gate serialization, matrix coverage, and updated synthetic signatures. Node 2 and Node 4 ceilings remain unchanged.

## Sequencing and stop conditions

- [ ] Set `NODE_BASE=NODE5_LANDED_COMMIT`, resolved only after Node 5 lands cleanly. Do not rebase or modify Node 5 files.
- [ ] Run focused Node 3 tests, Node 4 row-codec tests, the sanitized full suite, compile verification, diff hygiene, secret scans, and Phase 1 boundary scans.
- [ ] Synchronize CodeGraph if available; otherwise record `documented-unavailable`.
- [ ] Obtain the required read-only Codex review with `gpt-6-astra`, reasoning effort `max`, ending with `VERDICT: PASS`.

Stop immediately for a Node 2 signature or payload drift, any changed gate-`None` byte or ID, a ninth top-level payload key, Node 4 rejection of the nested gate, packet or replay leakage, mutation of a predecessor result, missing gate reason/hard-flag evidence, first-operation ordering failure, export/import/scope/line violations, failed focused/full gates, an unresolved Node 5 landing, or a non-PASS review.

## Completion evidence

The completion record must include the resolved Node 5 landing commit, exact sorted allowlist, clean worktree, six-class export proof, gate type validation proof, full status matrix, gate-`None` byte/ID equality fixtures, gated ID-change fixtures, packetless build-and-validate proof, Node 4 compatibility evidence, focused/full test results, compile/diff/secret/Phase 1 scans, CodeGraph status, and the final Codex review verdict.
