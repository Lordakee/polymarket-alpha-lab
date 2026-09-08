"""Review-pinned pure BTC evidence policy adapter (Node 6).

This module owns the pinned BTC aggregation configuration, the caller
evidence-input wrapper, and the pure policy evaluator.  The evaluator
validates every submitted source against the approved BTC registry,
resolves every trusted catalog record, runs the identity-bound BTC
resolution checker, then constructs and validates one temporary Node 2A
``TeamEvidenceAggregationInput`` to project canonical records and
current-revision selections.

It never builds a Node 2C aggregation result, a Node 3 envelope, any
forecast container, a database row, or a service.  A policy-gate status of
``ready``/``watch``/``blocked`` is not an aggregation status; Node 7 owns
composition.  Everything here is paper-only, report-only, and readonly
with no network, filesystem, clock, randomness, environment, or
persistence surface, and no live trading, authentication, credential,
wallet, signing, order, execution, exchange mutation, or account access.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Final, final

from polymarket_alpha_lab.crypto_btc_evidence_catalog import (
    CryptoBtcTrustedSourceRecord,
    resolve_trusted_crypto_btc_source_record,
)
from polymarket_alpha_lab.crypto_btc_evidence_registry import (
    CryptoBtcApprovedSource,
    require_approved_crypto_btc_source,
)
from polymarket_alpha_lab.crypto_btc_evidence_resolution import (
    CryptoBtcIncidentGates,
    CryptoBtcResolutionAssessment,
    CryptoBtcResolutionContract,
    check_crypto_btc_resolution_contract,
)
from polymarket_alpha_lab.team_evidence_aggregation_types import (
    TeamEvidenceAggregationConfig,
    TeamEvidenceAggregationInput,
    TeamEvidenceAggregationRecord,
    TeamEvidenceCurrentRevisionSelection,
    TeamEvidenceRequirement,
    validate_team_evidence_aggregation_input_contract,
)

__all__ = (
    "CryptoBtcEvidenceInput",
    "CryptoBtcEvidenceEvaluation",
    "build_crypto_btc_evidence_policy_config",
    "evaluate_crypto_btc_evidence",
)

CRYPTO_BTC_EVIDENCE_POLICY_CONFIG_VERSION: Final = "crypto-btc-evidence-policy-v0"
POLICY_GATE_STATUSES: Final = ("blocked", "ready", "watch")
POLICY_REQUIREMENT_IDS: Final = ("btc_derivatives", "btc_onchain", "btc_spot")
HARD_FLAG_NAMES: Final = ("paper_only", "report_only", "readonly")

REASON_CODE_INPUT_INVALID: Final = "evidence.input.invalid"
REASON_CODE_SOURCE_UNAPPROVED: Final = "evidence.source.unapproved"
REASON_CODE_SOURCE_FAMILY_MISMATCH: Final = "evidence.source_family.mismatch"
REASON_CODE_REGISTRY_VERSION_MISMATCH: Final = "evidence.registry_version.mismatch"
REASON_CODE_CATALOG_VERSION_MISMATCH: Final = "evidence.catalog_version.mismatch"
REASON_CODE_RECORD_UNRESOLVED: Final = "evidence.record.unresolved"
REASON_CODE_RECORD_DUPLICATE: Final = "evidence.record.duplicate"
REASON_CODE_RECORD_DIGEST_DUPLICATE: Final = "evidence.record_digest.duplicate"
REASON_CODE_NODE2A_CONTRACT_VIOLATION: Final = "evidence.node2a_contract.violation"
REASON_CODE_RESOLUTION_STATUS_INVALID: Final = "resolution.status.invalid"
REASON_CODE_EVIDENCE_INPUTS_EMPTY: Final = "evidence.inputs.empty"
REASON_CODE_POLICY_BLOCKED: Final = "policy.blocked"
REASON_CODE_POLICY_WATCH: Final = "policy.watch"
REASON_CODE_POLICY_READY: Final = "policy.ready"

FAILURE_REASON_CODES: Final = (
    REASON_CODE_INPUT_INVALID,
    REASON_CODE_SOURCE_UNAPPROVED,
    REASON_CODE_SOURCE_FAMILY_MISMATCH,
    REASON_CODE_REGISTRY_VERSION_MISMATCH,
    REASON_CODE_CATALOG_VERSION_MISMATCH,
    REASON_CODE_RECORD_UNRESOLVED,
    REASON_CODE_RECORD_DUPLICATE,
    REASON_CODE_RECORD_DIGEST_DUPLICATE,
    REASON_CODE_NODE2A_CONTRACT_VIOLATION,
    REASON_CODE_RESOLUTION_STATUS_INVALID,
)
_REASON_CODE_RANK: Final = (
    REASON_CODE_INPUT_INVALID,
    REASON_CODE_SOURCE_UNAPPROVED,
    REASON_CODE_SOURCE_FAMILY_MISMATCH,
    REASON_CODE_REGISTRY_VERSION_MISMATCH,
    REASON_CODE_CATALOG_VERSION_MISMATCH,
    REASON_CODE_RECORD_UNRESOLVED,
    REASON_CODE_RECORD_DUPLICATE,
    REASON_CODE_RECORD_DIGEST_DUPLICATE,
    REASON_CODE_NODE2A_CONTRACT_VIOLATION,
    REASON_CODE_EVIDENCE_INPUTS_EMPTY,
    REASON_CODE_RESOLUTION_STATUS_INVALID,
    REASON_CODE_POLICY_BLOCKED,
    REASON_CODE_POLICY_WATCH,
    REASON_CODE_POLICY_READY,
)
RESOLUTION_REASON_CODE_PREFIX: Final = "resolution."

_IDENTIFIER_RE: Final = re.compile(r"[a-z0-9](?:[a-z0-9._:-]*[a-z0-9])?", re.ASCII)
_DIGEST_RE: Final = re.compile(r"[0-9a-f]{64}", re.ASCII)
_PUBLIC_CLASS_NAMES: Final = ("CryptoBtcEvidenceInput", "CryptoBtcEvidenceEvaluation")


def _policy_decimal_context() -> Context:
    return Context(prec=64, rounding=ROUND_HALF_EVEN)


class _ExactPublicDataclass:
    __slots__ = ()

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if cls.__bases__ != (_ExactPublicDataclass,) or cls.__name__ not in _PUBLIC_CLASS_NAMES:
            raise TypeError("public crypto BTC policy dataclasses do not support subclassing")


def _identifier(path: str, value: object) -> str:
    if type(value) is not str or len(value.encode("utf-8")) > 160 or _IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{path} must be an exact canonical identifier")
    return value


def _digest(path: str, value: object) -> str:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{path} must be an exact lowercase SHA-256 digest")
    return value


def _canonical_string(path: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{path} must be a canonical nonblank string")
    return value


def _bool(path: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{path} must be an exact bool")
    return value


def _datetime(path: str, value: object) -> datetime:
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{path} must be an exact aware datetime")
    return value.astimezone(UTC)


def _hard_flags(path: str, value: object) -> None:
    for name in HARD_FLAG_NAMES:
        try:
            flag = getattr(value, name)
        except AttributeError as error:
            raise ValueError(f"{path}.{name} must be exact True") from error
        if flag is not True:
            raise ValueError(f"{path}.{name} must be exact True")


def _record_key(record: TeamEvidenceAggregationRecord) -> tuple[object, ...]:
    return (
        record.assessment_revision.assessment_revision_id,
        record.evidence_revision.evidence_revision_id,
        record.capture.captured_at,
        record.capture.capture_id,
        record.source_lineage.source_lineage_id,
    )


def _selection_key(selection: TeamEvidenceCurrentRevisionSelection) -> tuple[str, str]:
    return selection.evidence_revision_id, selection.assessment_revision_id


@final
@dataclass(frozen=True, slots=True)
class CryptoBtcEvidenceInput(_ExactPublicDataclass):
    """Caller evidence claim bound to one approved BTC source.

    There is no release-vintage or trust-tier override: vintage metadata
    lives only in the trusted catalog and trust tiers only in the
    approved registry.
    """

    source_id: str
    record_id: str
    record_digest: str
    record: TeamEvidenceAggregationRecord
    selected_current: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CryptoBtcEvidenceInput:
            raise ValueError("crypto_btc_evidence_input must be exactly CryptoBtcEvidenceInput")
        object.__setattr__(self, "source_id", _identifier("source_id", self.source_id))
        object.__setattr__(self, "record_id", _identifier("record_id", self.record_id))
        object.__setattr__(self, "record_digest", _digest("record_digest", self.record_digest))
        if type(self.record) is not TeamEvidenceAggregationRecord:
            raise ValueError("record must be exactly TeamEvidenceAggregationRecord")
        _hard_flags("record", self.record)
        _bool("selected_current", self.selected_current)
        _hard_flags("crypto_btc_evidence_input", self)


@final
@dataclass(frozen=True, slots=True)
class CryptoBtcEvidenceEvaluation(_ExactPublicDataclass):
    """Pure policy-gate evaluation output.

    ``status`` is a BTC policy gate, not an aggregation result status:
    ``ready`` only means the BTC policy and incident gates pass with all
    submitted evidence inputs valid; Node 7 must still combine it with
    the Node 2 aggregation status.
    """

    evaluated_at: datetime
    status: str
    records: tuple[TeamEvidenceAggregationRecord, ...]
    current_selections: tuple[TeamEvidenceCurrentRevisionSelection, ...]
    config: TeamEvidenceAggregationConfig
    resolution_assessment: CryptoBtcResolutionAssessment
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not CryptoBtcEvidenceEvaluation:
            raise ValueError("crypto_btc_evidence_evaluation must be exactly CryptoBtcEvidenceEvaluation")
        object.__setattr__(self, "evaluated_at", _datetime("evaluated_at", self.evaluated_at))
        if type(self.status) is not str or self.status not in POLICY_GATE_STATUSES:
            raise ValueError("status must be one of the closed policy gate statuses")
        records = self.records
        if type(records) is not tuple:
            raise ValueError("records must be an exact tuple")
        for index, record in enumerate(records):
            if type(record) is not TeamEvidenceAggregationRecord:
                raise ValueError(f"records[{index}] must be exactly TeamEvidenceAggregationRecord")
            _hard_flags(f"records[{index}]", record)
        keys = tuple(_record_key(record) for record in records)
        if len(set(keys)) != len(keys):
            raise ValueError("records contains duplicate canonical record key")
        if records != tuple(sorted(records, key=_record_key)):
            raise ValueError("records must be sorted by the canonical record key")
        selections = self.current_selections
        if type(selections) is not tuple:
            raise ValueError("current_selections must be an exact tuple")
        for index, selection in enumerate(selections):
            if type(selection) is not TeamEvidenceCurrentRevisionSelection:
                raise ValueError(f"current_selections[{index}] must be exactly TeamEvidenceCurrentRevisionSelection")
            _hard_flags(f"current_selections[{index}]", selection)
        selection_keys = tuple(_selection_key(selection) for selection in selections)
        if len(set(selection_keys)) != len(selection_keys):
            raise ValueError("current_selections contains duplicate selected pair")
        if selections != tuple(sorted(selections, key=_selection_key)):
            raise ValueError("current_selections must be sorted by the canonical selection key")
        resolvable = tuple(
            (record.evidence_revision.evidence_revision_id, record.assessment_revision.assessment_revision_id)
            for record in records
        )
        for selection in selections:
            if _selection_key(selection) not in resolvable:
                raise ValueError("current_selections must resolve against records")
        config = self.config
        if type(config) is not TeamEvidenceAggregationConfig:
            raise ValueError("config must be exactly TeamEvidenceAggregationConfig")
        _hard_flags("config", config)
        if config.config_version != CRYPTO_BTC_EVIDENCE_POLICY_CONFIG_VERSION:
            raise ValueError("config.config_version must be the pinned BTC policy version")
        if tuple(requirement.requirement_id for requirement in config.requirements) != POLICY_REQUIREMENT_IDS:
            raise ValueError("config.requirements must be the pinned BTC requirement tuple")
        if len(records) > config.maximum_records:
            raise ValueError("records exceeds config.maximum_records")
        assessment = self.resolution_assessment
        if type(assessment) is not CryptoBtcResolutionAssessment:
            raise ValueError("resolution_assessment must be exactly CryptoBtcResolutionAssessment")
        _hard_flags("resolution_assessment", assessment)
        object.__setattr__(self, "reason_codes", _validated_reason_codes(self.status, self.reason_codes))
        _hard_flags("crypto_btc_evidence_evaluation", self)


def _validated_reason_codes(status: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError("reason_codes must be a nonempty exact tuple")
    seen: set[str] = set()
    for code in value:
        if type(code) is not str or code in seen:
            raise ValueError("reason_codes must be unique canonical strings")
        seen.add(code)
        if code in _REASON_CODE_RANK:
            continue
        if code.startswith(RESOLUTION_REASON_CODE_PREFIX):
            suffix = code[len(RESOLUTION_REASON_CODE_PREFIX):]
            if _IDENTIFIER_RE.fullmatch(suffix) is None:
                raise ValueError("resolution passthrough reason codes must be canonical identifiers")
            continue
        raise ValueError("reason_codes must come from the closed policy set or the resolution passthrough")
    terminal = value[-1]
    if terminal not in (REASON_CODE_POLICY_BLOCKED, REASON_CODE_POLICY_WATCH, REASON_CODE_POLICY_READY):
        raise ValueError("reason_codes must end with exactly one policy status code")
    if tuple(code for code in value if code in (REASON_CODE_POLICY_BLOCKED, REASON_CODE_POLICY_WATCH, REASON_CODE_POLICY_READY)) != (terminal,):
        raise ValueError("reason_codes must contain exactly one policy status code")
    expected_terminal = {
        "ready": REASON_CODE_POLICY_READY,
        "watch": REASON_CODE_POLICY_WATCH,
        "blocked": REASON_CODE_POLICY_BLOCKED,
    }[status]
    if terminal != expected_terminal:
        raise ValueError("reason_codes terminal status must match status")
    if status in ("ready", "watch") and any(code in FAILURE_REASON_CODES for code in value):
        raise ValueError("ready and watch policy gates cannot carry failure reason codes")
    ordered_policy = [code for code in _REASON_CODE_RANK if code in seen and code != terminal]
    passthrough = sorted(code for code in seen if code.startswith(RESOLUTION_REASON_CODE_PREFIX))
    if value != tuple(ordered_policy + passthrough + [terminal]):
        raise ValueError("reason_codes must follow the deterministic closed ordering")
    return value


def build_crypto_btc_evidence_policy_config() -> TeamEvidenceAggregationConfig:
    """Return the immutable review-pinned BTC aggregation configuration."""
    with localcontext(_policy_decimal_context()):
        return TeamEvidenceAggregationConfig(
            config_version=CRYPTO_BTC_EVIDENCE_POLICY_CONFIG_VERSION,
            max_evidence_age_seconds=Decimal("900.000000"),
            max_capture_lag_seconds=Decimal("120.000000"),
            independence_group_weight_cap=Decimal("0.600000"),
            correlation_group_weight_cap=Decimal("0.750000"),
            max_requirement_assignments_per_evidence=4,
            contradiction_no_probability_max=Decimal("0.350000"),
            contradiction_yes_probability_min=Decimal("0.650000"),
            contradiction_watch_score=Decimal("0.250000"),
            contradiction_block_score=Decimal("0.500000"),
            publish_probability_floor=Decimal("0.020000"),
            publish_probability_ceiling=Decimal("0.980000"),
            maximum_records=64,
            maximum_requirements=3,
            maximum_requirement_memberships=12,
            maximum_witness_edges=64,
            requirements=(
                TeamEvidenceRequirement(
                    requirement_id="btc_derivatives",
                    minimum_witness_count=1,
                    minimum_effective_weight=Decimal("0.200000"),
                    unmet_status="watch",
                ),
                TeamEvidenceRequirement(
                    requirement_id="btc_onchain",
                    minimum_witness_count=1,
                    minimum_effective_weight=Decimal("0.150000"),
                    unmet_status="watch",
                ),
                TeamEvidenceRequirement(
                    requirement_id="btc_spot",
                    minimum_witness_count=1,
                    minimum_effective_weight=Decimal("0.300000"),
                    unmet_status="blocked",
                ),
            ),
        )


def _input_shape_failure(item: CryptoBtcEvidenceInput) -> bool:
    try:
        _identifier("source_id", item.source_id)
        _identifier("record_id", item.record_id)
        _digest("record_digest", item.record_digest)
        _bool("selected_current", item.selected_current)
        _hard_flags("crypto_btc_evidence_input", item)
        if type(item.record) is not TeamEvidenceAggregationRecord:
            return True
        _hard_flags("record", item.record)
        for layer in (item.record.source_lineage, item.record.capture, item.record.evidence_revision, item.record.assessment_revision):
            _hard_flags("record_layer", layer)
    except (ValueError, TypeError, AttributeError):
        return True
    return False


def _evidence_failures(
    evidence_inputs: tuple[CryptoBtcEvidenceInput, ...],
    *,
    evaluated_at: datetime,
) -> set[str]:
    failures: set[str] = set()
    seen_record_pairs: set[tuple[str, str]] = set()
    seen_record_digests: set[str] = set()
    registry_versions: set[str] = set()
    catalog_versions: set[str] = set()
    for item in evidence_inputs:
        if _input_shape_failure(item):
            failures.add(REASON_CODE_INPUT_INVALID)
            continue
        try:
            entry = require_approved_crypto_btc_source(item.source_id)
            if type(entry) is not CryptoBtcApprovedSource:
                failures.add(REASON_CODE_SOURCE_UNAPPROVED)
                continue
            _hard_flags("approved_source", entry)
            registry_versions.add(_canonical_string("registry_version", entry.registry_version))
        except ValueError:
            failures.add(REASON_CODE_SOURCE_UNAPPROVED)
            continue
        try:
            trusted = resolve_trusted_crypto_btc_source_record(
                item.source_id,
                item.record_id,
                item.record_digest,
                evaluated_at=evaluated_at,
            )
            if type(trusted) is not CryptoBtcTrustedSourceRecord:
                failures.add(REASON_CODE_RECORD_UNRESOLVED)
                continue
            _hard_flags("trusted_source_record", trusted)
            catalog_versions.add(_canonical_string("catalog_version", trusted.catalog_version))
        except ValueError:
            failures.add(REASON_CODE_RECORD_UNRESOLVED)
            continue
        if _canonical_string("source_family", entry.source_family) != _canonical_string("source_family", trusted.source_family):
            failures.add(REASON_CODE_SOURCE_FAMILY_MISMATCH)
        pair = (item.source_id, item.record_id)
        if pair in seen_record_pairs:
            failures.add(REASON_CODE_RECORD_DUPLICATE)
        else:
            seen_record_pairs.add(pair)
        if item.record_digest in seen_record_digests:
            failures.add(REASON_CODE_RECORD_DIGEST_DUPLICATE)
        else:
            seen_record_digests.add(item.record_digest)
    if len(registry_versions) > 1:
        failures.add(REASON_CODE_REGISTRY_VERSION_MISMATCH)
    if len(catalog_versions) > 1:
        failures.add(REASON_CODE_CATALOG_VERSION_MISMATCH)
    return failures


def _policy_gate(assessment: CryptoBtcResolutionAssessment) -> tuple[str, set[str]]:
    resolution_status = getattr(assessment, "resolution_contract_status", None)
    if resolution_status == "pass":
        return "ready", set()
    if resolution_status == "watch":
        return "watch", set()
    if resolution_status == "blocked":
        return "blocked", set()
    return "blocked", {REASON_CODE_RESOLUTION_STATUS_INVALID}


def _compose_reason_codes(
    assessment: CryptoBtcResolutionAssessment,
    *,
    failures: set[str],
    notes: set[str],
    terminal: str,
) -> tuple[str, ...]:
    present = set(failures) | set(notes)
    present.discard(terminal)
    ordered = [code for code in _REASON_CODE_RANK if code in present and code != terminal]
    passthrough = sorted(
        {
            f"{RESOLUTION_REASON_CODE_PREFIX}{code}"
            for code in assessment.reason_codes
            if type(code) is str and _IDENTIFIER_RE.fullmatch(code) is not None
        }
    )
    merged: list[str] = []
    for code in ordered + passthrough + [terminal]:
        if code not in merged:
            merged.append(code)
    return tuple(merged)


def evaluate_crypto_btc_evidence(
    *,
    condition_id: str,
    market_slug: str,
    event_template: str,
    resolution_contract: CryptoBtcResolutionContract,
    incident_gates: CryptoBtcIncidentGates,
    evidence_inputs: tuple[CryptoBtcEvidenceInput, ...],
    evaluated_at: datetime,
) -> CryptoBtcEvidenceEvaluation:
    """Evaluate the BTC evidence policy gate as a pure adapter.

    Unknown sources, unresolved or expired catalog records, digest and
    source-family mismatches, registry/catalog version mismatches,
    duplicate records or digests, and Node 2A input-contract violations
    fail closed to a ``blocked`` policy gate with deterministic reason
    codes.  Structural misuse of this function's own arguments raises.
    """
    _canonical_string("condition_id", condition_id)
    _canonical_string("market_slug", market_slug)
    _canonical_string("event_template", event_template)
    if type(resolution_contract) is not CryptoBtcResolutionContract:
        raise ValueError("resolution_contract must be exactly CryptoBtcResolutionContract")
    _hard_flags("resolution_contract", resolution_contract)
    if type(incident_gates) is not CryptoBtcIncidentGates:
        raise ValueError("incident_gates must be exactly CryptoBtcIncidentGates")
    _hard_flags("incident_gates", incident_gates)
    if type(evidence_inputs) is not tuple:
        raise ValueError("evidence_inputs must be an exact tuple")
    for index, item in enumerate(evidence_inputs):
        if type(item) is not CryptoBtcEvidenceInput:
            raise ValueError(f"evidence_inputs[{index}] must be exactly CryptoBtcEvidenceInput")
    evaluated_at_utc = _datetime("evaluated_at", evaluated_at)
    config = build_crypto_btc_evidence_policy_config()
    with localcontext(_policy_decimal_context()):
        failures = _evidence_failures(evidence_inputs, evaluated_at=evaluated_at_utc)
        assessment = check_crypto_btc_resolution_contract(
            resolution_contract,
            condition_id=condition_id,
            market_slug=market_slug,
            event_template=event_template,
            incident_gates=incident_gates,
            evaluated_at=evaluated_at_utc,
        )
        if type(assessment) is not CryptoBtcResolutionAssessment:
            raise ValueError("resolution checker must return exactly CryptoBtcResolutionAssessment")
        _hard_flags("resolution_assessment", assessment)
        if type(assessment.reason_codes) is not tuple:
            raise ValueError("resolution assessment reason_codes must be an exact tuple")
        status, status_failures = _policy_gate(assessment)
        failures |= status_failures
        if failures:
            status = "blocked"
        notes: set[str] = set()
        records: tuple[TeamEvidenceAggregationRecord, ...] = ()
        selections: tuple[TeamEvidenceCurrentRevisionSelection, ...] = ()
        if not failures:
            try:
                current_revisions = tuple(
                    TeamEvidenceCurrentRevisionSelection(
                        evidence_revision_id=item.record.evidence_revision.evidence_revision_id,
                        evidence_revision_digest=item.record.evidence_revision.evidence_revision_digest,
                        assessment_revision_id=item.record.assessment_revision.assessment_revision_id,
                        assessment_revision_digest=item.record.assessment_revision.assessment_revision_digest,
                    )
                    for item in evidence_inputs
                    if item.selected_current
                )
                aggregation_input = TeamEvidenceAggregationInput(
                    evaluated_at=evaluated_at_utc,
                    records=tuple(item.record for item in evidence_inputs),
                    current_revisions=current_revisions,
                )
                validate_team_evidence_aggregation_input_contract(aggregation_input, config=config)
                records = aggregation_input.records
                selections = aggregation_input.current_revisions
            except (ValueError, TypeError):
                failures.add(REASON_CODE_NODE2A_CONTRACT_VIOLATION)
                status = "blocked"
                records = ()
                selections = ()
        if not evidence_inputs:
            notes.add(REASON_CODE_EVIDENCE_INPUTS_EMPTY)
        terminal = {
            "ready": REASON_CODE_POLICY_READY,
            "watch": REASON_CODE_POLICY_WATCH,
            "blocked": REASON_CODE_POLICY_BLOCKED,
        }[status]
        return CryptoBtcEvidenceEvaluation(
            evaluated_at=evaluated_at_utc,
            status=status,
            records=records,
            current_selections=selections,
            config=config,
            resolution_assessment=assessment,
            reason_codes=_compose_reason_codes(
                assessment,
                failures=failures,
                notes=notes,
                terminal=terminal,
            ),
        )
