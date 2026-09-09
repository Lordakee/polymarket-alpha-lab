"""Node 3 team forecast build envelope (pure, paper-only, readonly).

Binds exactly one validated Node 2 team evidence aggregation to a complete
canonical evaluation scope: domain context, provenance, run metadata, one
canonical receipt for every accepted or rejected evaluator input, and the
three separate Node 2 config, input, and full validated-result fragments.
Identifiers are domain-separated ``tea:v1``/``tfr:v1``/``tfe:v1`` values
computed from complete canonical preimages, never from the Node 2
``core_digest``. Ready results additionally project onto the existing
legacy forecast and forecast-evidence packets through their public
constructors and payload projection; watch and blocked results produce no
packets and no replay records. An optional immutable
``TeamForecastPolicyPublicationGate`` applies the same packet suppression for
a non-ready policy status, serializing only as the reserved nested
``run_metadata`` ``external_publication_gate`` entry that joins the complete
identifier preimages. The module performs no persistence,
filesystem, network, environment, process, logging, clock, or randomness
operation, and every hard flag is a literal ``True``.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
import json
import re
from typing import Any, Final, final

from polymarket_alpha_lab.team_evidence_aggregation import (
    validate_team_evidence_aggregation_result,
)
from polymarket_alpha_lab.team_evidence_aggregation_types import (
    TeamEvidenceAggregationConfig,
    TeamEvidenceAggregationInput,
    TeamEvidenceAggregationRecord,
    TeamEvidenceAggregationResult,
)
from polymarket_alpha_lab.team_evidence_aggregation_codec import (
    team_evidence_aggregation_config_digest,
    team_evidence_aggregation_config_payload,
    team_evidence_aggregation_input_payload,
    team_evidence_aggregation_payload,
)
from polymarket_alpha_lab.team_forecast_packet import (
    TeamForecastEvidencePacket,
    TeamForecastPacket,
    team_forecast_packet_payload,
)

_IDENTIFIER_PATTERN: Final = re.compile(
    r"[a-z0-9](?:[a-z0-9._:-]*[a-z0-9])?", re.ASCII
)
_DIGEST_PATTERN: Final = re.compile(r"[0-9a-f]{64}", re.ASCII)
_IDENTIFIER_LENGTH_MAXIMUM: Final = 160
_HARD_FLAG_NAMES: Final = ("paper_only", "report_only", "readonly")
_CLASSIFICATIONS: Final = frozenset(("accepted", "rejected"))
_PUBLIC_CLASS_NAMES: Final = frozenset((
    "TeamForecastEvaluationScope",
    "TeamForecastRunMetadata",
    "TeamForecastEvaluatorReceipt",
    "TeamForecastEvidenceReplayRecord",
    "TeamForecastBuildEnvelope",
    "TeamForecastPolicyPublicationGate",
))
_GATE_STATUS_VALUES: Final = frozenset(("ready", "watch", "blocked"))
_GATE_PAYLOAD_KEY: Final = "external_publication_gate"
_ZERO_OFFSET: Final = timedelta(0)
_AGGREGATION_DOMAIN: Final = b"tea:v1\x00"
_RUN_DOMAIN: Final = b"tfr:v1\x00"
_EVIDENCE_DOMAIN: Final = b"tfe:v1\x00"
_AGGREGATION_ID_PREFIX: Final = "tea:v1:"
_RUN_ID_PREFIX: Final = "tfr:v1:"
_EVIDENCE_ID_PREFIX: Final = "tfe:v1:"


def _identifier(path: str, value: object) -> str:
    if (
        type(value) is not str
        or len(value.encode("utf-8")) > _IDENTIFIER_LENGTH_MAXIMUM
        or _IDENTIFIER_PATTERN.fullmatch(value) is None
    ):
        raise ValueError(f"{path} must be a canonical identifier")
    return value


def _digest(path: str, value: object) -> str:
    if type(value) is not str or _DIGEST_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{path} must be an exact lowercase sha-256 digest")
    return value


def _prefixed_id(path: str, prefix: str, value: object) -> str:
    if (
        type(value) is not str
        or not value.startswith(prefix)
        or _DIGEST_PATTERN.fullmatch(value[len(prefix):]) is None
    ):
        raise ValueError(f"{path} must be an exact {prefix} identifier")
    return value


def _canonical_string(path: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{path} must be a canonical nonblank string")
    return value


def _utc_datetime(path: str, value: object) -> datetime:
    if (
        type(value) is not datetime
        or value.tzinfo is None
        or value.utcoffset() != _ZERO_OFFSET
    ):
        raise ValueError(f"{path} must be an exact aware UTC datetime")
    return value if value.tzinfo is UTC else value.astimezone(UTC)


def _utc_datetime_text(value: datetime) -> str:
    return (
        f"{value.year:04d}-{value.month:02d}-{value.day:02d}T"
        f"{value.hour:02d}:{value.minute:02d}:{value.second:02d}."
        f"{value.microsecond:06d}+00:00"
    )


def _hard_flags(path: str, value: object) -> None:
    for flag_name in _HARD_FLAG_NAMES:
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{path}.{flag_name} must be exact True")
    return None


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _fresh_value(value: object) -> object:
    if type(value) is dict:
        return {key: _fresh_value(item) for key, item in value.items()}
    if type(value) is list:
        return [_fresh_value(item) for item in value]
    if type(value) is tuple:
        return tuple(_fresh_value(item) for item in value)
    return value


def _record_identity(
    record: TeamEvidenceAggregationRecord,
) -> tuple[str, str, str, str]:
    return (
        record.source_lineage.source_lineage_id,
        record.capture.capture_id,
        record.evidence_revision.evidence_revision_id,
        record.assessment_revision.assessment_revision_id,
    )


def _receipt_sort_key(receipt: TeamForecastEvaluatorReceipt) -> str:
    return receipt.evaluator_input_id


def _canonical_domain_context(
    value: object,
) -> tuple[tuple[str, str], ...]:
    if type(value) is not tuple:
        raise ValueError("scope.domain_context must be an exact tuple")
    entries: list[tuple[str, str]] = []
    for index, pair in enumerate(value):
        if type(pair) is not tuple or len(pair) != 2:
            raise ValueError(
                f"scope.domain_context[{index}] must be an exact two-string "
                "tuple"
            )
        key = _identifier(f"scope.domain_context[{index}][0]", pair[0])
        item = _canonical_string(f"scope.domain_context[{index}][1]", pair[1])
        entries.append((key, item))
    keys = tuple(key for key, _item in entries)
    if len(set(keys)) != len(keys):
        raise ValueError("scope.domain_context keys must be unique")
    return tuple(sorted(entries))


def _canonical_provenance(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("scope.provenance must be an exact tuple")
    entries = tuple(
        _canonical_string(f"scope.provenance[{index}]", item)
        for index, item in enumerate(value)
    )
    if len(set(entries)) != len(entries):
        raise ValueError("scope.provenance entries must be unique")
    return tuple(sorted(entries))


class _SealedNode3Dataclass:
    """Reject every subclass of the public Node 3 dataclasses."""

    __slots__ = ()

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if (
            cls.__bases__ != (_SealedNode3Dataclass,)
            or cls.__name__ not in _PUBLIC_CLASS_NAMES
        ):
            raise TypeError(
                "public team forecast envelope dataclasses do not support "
                "subclassing"
            )


@final
@dataclass(frozen=True, slots=True)
class TeamForecastEvaluationScope(_SealedNode3Dataclass):
    scope_version: str
    domain_context: tuple[tuple[str, str], ...]
    provenance: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "scope_version",
            _identifier("scope.scope_version", self.scope_version),
        )
        object.__setattr__(
            self,
            "domain_context",
            _canonical_domain_context(self.domain_context),
        )
        object.__setattr__(
            self, "provenance", _canonical_provenance(self.provenance)
        )
        _hard_flags("scope", self)


@final
@dataclass(frozen=True, slots=True)
class TeamForecastRunMetadata(_SealedNode3Dataclass):
    run_label: str
    generator_version: str
    prompt_version: str
    started_at: datetime
    completed_at: datetime | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "run_label",
            _identifier("run_metadata.run_label", self.run_label),
        )
        object.__setattr__(
            self,
            "generator_version",
            _identifier("run_metadata.generator_version", self.generator_version),
        )
        object.__setattr__(
            self,
            "prompt_version",
            _identifier("run_metadata.prompt_version", self.prompt_version),
        )
        object.__setattr__(
            self,
            "started_at",
            _utc_datetime("run_metadata.started_at", self.started_at),
        )
        if self.completed_at is not None:
            object.__setattr__(
                self,
                "completed_at",
                _utc_datetime("run_metadata.completed_at", self.completed_at),
            )
        _hard_flags("run_metadata", self)


@final
@dataclass(frozen=True, slots=True)
class TeamForecastEvaluatorReceipt(_SealedNode3Dataclass):
    evaluator_input_id: str
    input_digest: str
    receipt_time: datetime
    classification: str
    accepted_record_identity: tuple[str, str, str, str] | None
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "evaluator_input_id",
            _identifier(
                "evaluator_receipt.evaluator_input_id", self.evaluator_input_id
            ),
        )
        object.__setattr__(
            self,
            "input_digest",
            _digest("evaluator_receipt.input_digest", self.input_digest),
        )
        object.__setattr__(
            self,
            "receipt_time",
            _utc_datetime(
                "evaluator_receipt.receipt_time", self.receipt_time
            ),
        )
        classification = self.classification
        if (
            type(classification) is not str
            or classification not in _CLASSIFICATIONS
        ):
            raise ValueError(
                "evaluator_receipt.classification must be accepted or rejected"
            )
        identity = self.accepted_record_identity
        if identity is not None:
            if type(identity) is not tuple or len(identity) != 4:
                raise ValueError(
                    "evaluator_receipt.accepted_record_identity must be an "
                    "exact four-string tuple"
                )
            object.__setattr__(
                self,
                "accepted_record_identity",
                tuple(
                    _identifier(
                        f"evaluator_receipt.accepted_record_identity[{index}]",
                        part,
                    )
                    for index, part in enumerate(identity)
                ),
            )
        codes = self.reason_codes
        if type(codes) is not tuple:
            raise ValueError("evaluator_receipt.reason_codes must be an exact tuple")
        object.__setattr__(
            self,
            "reason_codes",
            tuple(
                sorted(
                    {
                        _identifier(
                            f"evaluator_receipt.reason_codes[{index}]", item
                        )
                        for index, item in enumerate(codes)
                    }
                )
            ),
        )
        _hard_flags("evaluator_receipt", self)


@final
@dataclass(frozen=True, slots=True)
class TeamForecastEvidenceReplayRecord(_SealedNode3Dataclass):
    evidence_id: str
    accepted_record_identity: tuple[str, str, str, str]
    legacy_payload: dict[str, Any]
    legacy_payload_sha256: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "evidence_id",
            _prefixed_id(
                "evidence_replay_record.evidence_id",
                _EVIDENCE_ID_PREFIX,
                self.evidence_id,
            ),
        )
        identity = self.accepted_record_identity
        if type(identity) is not tuple or len(identity) != 4:
            raise ValueError(
                "evidence_replay_record.accepted_record_identity must be an "
                "exact four-string tuple"
            )
        object.__setattr__(
            self,
            "accepted_record_identity",
            tuple(
                _identifier(
                    f"evidence_replay_record.accepted_record_identity[{index}]",
                    part,
                )
                for index, part in enumerate(identity)
            ),
        )
        projection = self.legacy_payload
        if type(projection) is not dict:
            raise ValueError(
                "evidence_replay_record.legacy_payload must be an exact dict"
            )
        payload_sha256 = _digest(
            "evidence_replay_record.legacy_payload_sha256",
            self.legacy_payload_sha256,
        )
        if payload_sha256 != team_forecast_legacy_payload_sha256(projection):
            raise ValueError(
                "evidence_replay_record.legacy_payload_sha256 must hash "
                "legacy_payload with the historical encoding"
            )
        object.__setattr__(
            self, "legacy_payload_sha256", payload_sha256
        )
        _hard_flags("evidence_replay_record", self)


@final
@dataclass(frozen=True, slots=True)
class TeamForecastPolicyPublicationGate(_SealedNode3Dataclass):
    """Immutable policy gate over legacy packet projection."""

    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if (
            type(self.status) is not str
            or self.status not in _GATE_STATUS_VALUES
        ):
            raise ValueError(
                "publication_gate.status must be ready, watch, or blocked"
            )
        codes = self.reason_codes
        if type(codes) is not tuple:
            raise ValueError(
                "publication_gate.reason_codes must be an exact tuple"
            )
        object.__setattr__(
            self,
            "reason_codes",
            tuple(
                sorted(
                    {
                        _identifier(
                            f"publication_gate.reason_codes[{index}]", item
                        )
                        for index, item in enumerate(codes)
                    }
                )
            ),
        )
        _hard_flags("publication_gate", self)


@final
@dataclass(frozen=True, slots=True)
class TeamForecastBuildEnvelope(_SealedNode3Dataclass):
    tea_id: str
    tfr_id: str
    evaluation_scope_payload: dict[str, object]
    legacy_forecast_packet: TeamForecastPacket | None
    legacy_evidence_packets: tuple[TeamForecastEvidencePacket, ...]
    evidence_replay_records: tuple[TeamForecastEvidenceReplayRecord, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "tea_id",
            _prefixed_id("envelope.tea_id", _AGGREGATION_ID_PREFIX, self.tea_id),
        )
        object.__setattr__(
            self,
            "tfr_id",
            _prefixed_id("envelope.tfr_id", _RUN_ID_PREFIX, self.tfr_id),
        )
        if type(self.evaluation_scope_payload) is not dict:
            raise ValueError(
                "envelope.evaluation_scope_payload must be an exact dict"
            )
        if (
            self.legacy_forecast_packet is not None
            and type(self.legacy_forecast_packet) is not TeamForecastPacket
        ):
            raise ValueError(
                "envelope.legacy_forecast_packet must be exactly "
                "TeamForecastPacket"
            )
        packets_value = self.legacy_evidence_packets
        if type(packets_value) is not tuple:
            raise ValueError(
                "envelope.legacy_evidence_packets must be an exact tuple"
            )
        for index, item in enumerate(packets_value):
            if type(item) is not TeamForecastEvidencePacket:
                raise ValueError(
                    f"envelope.legacy_evidence_packets[{index}] must be "
                    "exactly TeamForecastEvidencePacket"
                )
        replays_value = self.evidence_replay_records
        if type(replays_value) is not tuple:
            raise ValueError(
                "envelope.evidence_replay_records must be an exact tuple"
            )
        for index, item in enumerate(replays_value):
            if type(item) is not TeamForecastEvidenceReplayRecord:
                raise ValueError(
                    f"envelope.evidence_replay_records[{index}] must be "
                    "exactly TeamForecastEvidenceReplayRecord"
                )
        if len(packets_value) != len(replays_value):
            raise ValueError(
                "envelope.legacy_evidence_packets must match "
                "envelope.evidence_replay_records"
            )
        _hard_flags("envelope", self)


def team_evidence_aggregation_id(
    evaluation_scope_payload: dict[str, object],
) -> str:
    """Derive the tea:v1 identifier from the complete canonical scope bytes."""
    if type(evaluation_scope_payload) is not dict:
        raise ValueError("evaluation_scope_payload must be an exact dict")
    return _AGGREGATION_ID_PREFIX + sha256(
        _AGGREGATION_DOMAIN + _canonical_bytes(evaluation_scope_payload)
    ).hexdigest()


def team_forecast_run_id(
    tea_id: str,
    run_metadata_payload: dict[str, object],
) -> str:
    """Derive the tfr:v1 identifier from the tea and run-metadata preimage."""
    _prefixed_id("tea_id", _AGGREGATION_ID_PREFIX, tea_id)
    if type(run_metadata_payload) is not dict:
        raise ValueError("run_metadata_payload must be an exact dict")
    preimage = {"tea_id": tea_id, "run_metadata": run_metadata_payload}
    return _RUN_ID_PREFIX + sha256(
        _RUN_DOMAIN + _canonical_bytes(preimage)
    ).hexdigest()


def team_forecast_evidence_id(
    tea_id: str,
    receipt_payload: dict[str, object],
    payload_sha256: str,
) -> str:
    """Derive the tfe:v1 identifier from the tea, receipt, and legacy hash."""
    _prefixed_id("tea_id", _AGGREGATION_ID_PREFIX, tea_id)
    if type(receipt_payload) is not dict:
        raise ValueError("receipt_payload must be an exact dict")
    _digest("legacy_payload_sha256", payload_sha256)
    preimage = {
        "tea_id": tea_id,
        "receipt": receipt_payload,
        "legacy_payload_sha256": payload_sha256,
    }
    return _EVIDENCE_ID_PREFIX + sha256(
        _EVIDENCE_DOMAIN + _canonical_bytes(preimage)
    ).hexdigest()


def team_forecast_legacy_payload_sha256(legacy_payload: dict[str, Any]) -> str:
    """Hash a legacy packet payload with the exact historical JSON encoding."""
    if type(legacy_payload) is not dict:
        raise ValueError("legacy_payload must be an exact dict")
    encoded = json.dumps(
        legacy_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def team_forecast_evaluation_scope_payload(
    envelope: TeamForecastBuildEnvelope,
) -> dict[str, object]:
    """Re-surface a fresh copy of the envelope's evaluation-scope payload."""
    if type(envelope) is not TeamForecastBuildEnvelope:
        raise ValueError("envelope must be exactly TeamForecastBuildEnvelope")
    scope_payload = _fresh_value(envelope.evaluation_scope_payload)
    if type(scope_payload) is not dict:
        raise ValueError(
            "envelope.evaluation_scope_payload must be an exact dict"
        )
    return scope_payload


def _receipt_entry(
    receipt: TeamForecastEvaluatorReceipt,
) -> dict[str, object]:
    identity = receipt.accepted_record_identity
    return {
        "evaluator_input_id": receipt.evaluator_input_id,
        "input_digest": receipt.input_digest,
        "receipt_time": _utc_datetime_text(receipt.receipt_time),
        "classification": receipt.classification,
        "accepted_record_identity": (
            None if identity is None else [part for part in identity]
        ),
        "reason_codes": [code for code in receipt.reason_codes],
        "paper_only": receipt.paper_only,
        "report_only": receipt.report_only,
        "readonly": receipt.readonly,
    }


def _run_metadata_entry(
    run_metadata: TeamForecastRunMetadata,
    policy_publication_gate: TeamForecastPolicyPublicationGate | None,
) -> dict[str, object]:
    completed_at = run_metadata.completed_at
    entry: dict[str, object] = {
        "run_label": run_metadata.run_label,
        "generator_version": run_metadata.generator_version,
        "prompt_version": run_metadata.prompt_version,
        "started_at": _utc_datetime_text(run_metadata.started_at),
        "completed_at": (
            None if completed_at is None else _utc_datetime_text(completed_at)
        ),
        "paper_only": run_metadata.paper_only,
        "report_only": run_metadata.report_only,
        "readonly": run_metadata.readonly,
    }
    if policy_publication_gate is not None:
        entry[_GATE_PAYLOAD_KEY] = _publication_gate_entry(
            policy_publication_gate
        )
    return entry


def _publication_gate_entry(
    policy_publication_gate: TeamForecastPolicyPublicationGate,
) -> dict[str, object]:
    """Rebuild the gate fail-closed, then project its direct field map."""
    rebuilt = TeamForecastPolicyPublicationGate(
        status=policy_publication_gate.status,
        reason_codes=policy_publication_gate.reason_codes,
        paper_only=policy_publication_gate.paper_only,
        report_only=policy_publication_gate.report_only,
        readonly=policy_publication_gate.readonly,
    )
    if rebuilt != policy_publication_gate:
        raise ValueError(
            "publication_gate must already carry canonical status, reason "
            "codes, and hard flags"
        )
    return {
        "status": rebuilt.status,
        "reason_codes": [code for code in rebuilt.reason_codes],
        "paper_only": rebuilt.paper_only,
        "report_only": rebuilt.report_only,
        "readonly": rebuilt.readonly,
    }


def _validate_receipt_contract(
    receipts: tuple[TeamForecastEvaluatorReceipt, ...],
    *,
    aggregation_input: TeamEvidenceAggregationInput,
) -> None:
    identifiers_seen: set[str] = set()
    digests_seen: set[str] = set()
    accepted_identities: list[tuple[str, str, str, str]] = []
    for receipt in receipts:
        identifier_value = receipt.evaluator_input_id
        if identifier_value in identifiers_seen:
            raise ValueError(
                "evaluator_receipts.evaluator_input_id values must be unique"
            )
        identifiers_seen.add(identifier_value)
        if receipt.input_digest in digests_seen:
            raise ValueError(
                "evaluator_receipts.input_digest values must be unique"
            )
        digests_seen.add(receipt.input_digest)
        identity = receipt.accepted_record_identity
        if receipt.classification == "accepted":
            if identity is None:
                raise ValueError(
                    "accepted evaluator_receipt requires "
                    "accepted_record_identity"
                )
            accepted_identities.append(identity)
        elif identity is not None:
            raise ValueError(
                "rejected evaluator_receipt must not carry "
                "accepted_record_identity"
            )
    if len(set(accepted_identities)) != len(accepted_identities):
        raise ValueError(
            "accepted evaluator_receipt accepted_record_identity values "
            "must be unique"
        )
    record_identities = {
        _record_identity(record) for record in aggregation_input.records
    }
    for identity in accepted_identities:
        if identity not in record_identities:
            raise ValueError(
                "accepted evaluator_receipt.accepted_record_identity must "
                "match a supplied aggregation record"
            )
    if len(accepted_identities) != len(record_identities):
        raise ValueError(
            "every aggregation record requires one accepted "
            "evaluator_receipt"
        )
    return None


def _materialize_envelope(
    result: TeamEvidenceAggregationResult,
    *,
    aggregation_input: TeamEvidenceAggregationInput,
    config: TeamEvidenceAggregationConfig,
    scope: TeamForecastEvaluationScope,
    run_metadata: TeamForecastRunMetadata,
    evaluator_receipts: tuple[TeamForecastEvaluatorReceipt, ...],
    legacy_forecast_packet: TeamForecastPacket | None,
    legacy_evidence_packets: tuple[TeamForecastEvidencePacket, ...],
    policy_publication_gate: TeamForecastPolicyPublicationGate | None = None,
) -> TeamForecastBuildEnvelope:
    """Validate first, then bind fragments, receipts, IDs, and packets."""
    validate_team_evidence_aggregation_result(
        result,
        aggregation_input=aggregation_input,
        config=config,
    )
    if result.config_digest != team_evidence_aggregation_config_digest(config):
        raise ValueError(
            "result.config_digest must equal "
            "team_evidence_aggregation_config_digest(config)"
        )
    if type(scope) is not TeamForecastEvaluationScope:
        raise ValueError("scope must be exactly TeamForecastEvaluationScope")
    if type(run_metadata) is not TeamForecastRunMetadata:
        raise ValueError(
            "run_metadata must be exactly TeamForecastRunMetadata"
        )
    if policy_publication_gate is not None and (
        type(policy_publication_gate) is not TeamForecastPolicyPublicationGate
    ):
        raise ValueError(
            "policy_publication_gate must be exactly "
            "TeamForecastPolicyPublicationGate"
        )
    if type(evaluator_receipts) is not tuple:
        raise ValueError("evaluator_receipts must be an exact tuple")
    for index, receipt in enumerate(evaluator_receipts):
        if type(receipt) is not TeamForecastEvaluatorReceipt:
            raise ValueError(
                f"evaluator_receipts[{index}] must be exactly "
                "TeamForecastEvaluatorReceipt"
            )
    if (
        legacy_forecast_packet is not None
        and type(legacy_forecast_packet) is not TeamForecastPacket
    ):
        raise ValueError(
            "legacy_forecast_packet must be exactly TeamForecastPacket"
        )
    if type(legacy_evidence_packets) is not tuple:
        raise ValueError("legacy_evidence_packets must be an exact tuple")
    for index, evidence_template in enumerate(legacy_evidence_packets):
        if type(evidence_template) is not TeamForecastEvidencePacket:
            raise ValueError(
                f"legacy_evidence_packets[{index}] must be exactly "
                "TeamForecastEvidencePacket"
            )
    node2_config = _fresh_value(team_evidence_aggregation_config_payload(config))
    node2_input = _fresh_value(
        team_evidence_aggregation_input_payload(aggregation_input)
    )
    node2_result = _fresh_value(team_evidence_aggregation_payload(result))
    canonical_receipts = tuple(sorted(evaluator_receipts, key=_receipt_sort_key))
    _validate_receipt_contract(
        canonical_receipts, aggregation_input=aggregation_input
    )
    receipt_entries = [_receipt_entry(receipt) for receipt in canonical_receipts]
    run_metadata_payload = _run_metadata_entry(
        run_metadata, policy_publication_gate
    )
    evaluation_scope_payload: dict[str, object] = {
        "scope_version": scope.scope_version,
        "domain_context": {key: item for key, item in scope.domain_context},
        "provenance": [entry for entry in scope.provenance],
        "run_metadata": run_metadata_payload,
        "evaluator_receipts": receipt_entries,
        "node2_config": node2_config,
        "node2_input": node2_input,
        "node2_result": node2_result,
    }
    tea_id = team_evidence_aggregation_id(evaluation_scope_payload)
    tfr_id = team_forecast_run_id(tea_id, run_metadata_payload)
    effective_ready = result.status == "ready" and (
        policy_publication_gate is None
        or policy_publication_gate.status == "ready"
    )
    if not effective_ready:
        if legacy_forecast_packet is not None:
            raise ValueError(
                "an effectively non-ready build must not receive "
                "legacy_forecast_packet"
            )
        if legacy_evidence_packets:
            raise ValueError(
                "an effectively non-ready build must not receive "
                "legacy_evidence_packets"
            )
        return TeamForecastBuildEnvelope(
            tea_id=tea_id,
            tfr_id=tfr_id,
            evaluation_scope_payload=evaluation_scope_payload,
            legacy_forecast_packet=None,
            legacy_evidence_packets=(),
            evidence_replay_records=(),
        )
    if legacy_forecast_packet is None:
        raise ValueError("ready result requires legacy_forecast_packet")
    publishable_probability = result.publishable_probability_yes
    if publishable_probability is None:
        raise ValueError(
            "ready result must carry publishable_probability_yes"
        )
    output_forecast_packet = replace(
        legacy_forecast_packet,
        forecast_id=tfr_id,
        forecast_probability=publishable_probability,
    )
    accepted_receipts = tuple(
        receipt
        for receipt in canonical_receipts
        if receipt.classification == "accepted"
    )
    if len(legacy_evidence_packets) != len(accepted_receipts):
        raise ValueError(
            "legacy_evidence_packets must match the accepted evaluator "
            "receipt count"
        )
    output_evidence_packets: list[TeamForecastEvidencePacket] = []
    replay_records: list[TeamForecastEvidenceReplayRecord] = []
    for receipt, evidence_template in zip(
        accepted_receipts, legacy_evidence_packets, strict=True
    ):
        projection = team_forecast_packet_payload(evidence_template)
        payload_sha256 = team_forecast_legacy_payload_sha256(projection)
        receipt_entry = _receipt_entry(receipt)
        evidence_id = team_forecast_evidence_id(
            tea_id, receipt_entry, payload_sha256
        )
        output_evidence_packets.append(
            replace(evidence_template, evidence_id=evidence_id)
        )
        replay_records.append(
            TeamForecastEvidenceReplayRecord(
                evidence_id=evidence_id,
                accepted_record_identity=receipt.accepted_record_identity,
                legacy_payload=projection,
                legacy_payload_sha256=payload_sha256,
            )
        )
    return TeamForecastBuildEnvelope(
        tea_id=tea_id,
        tfr_id=tfr_id,
        evaluation_scope_payload=evaluation_scope_payload,
        legacy_forecast_packet=output_forecast_packet,
        legacy_evidence_packets=tuple(output_evidence_packets),
        evidence_replay_records=tuple(replay_records),
    )


def build_team_forecast_build_envelope(
    result: TeamEvidenceAggregationResult,
    *,
    aggregation_input: TeamEvidenceAggregationInput,
    config: TeamEvidenceAggregationConfig,
    scope: TeamForecastEvaluationScope,
    run_metadata: TeamForecastRunMetadata,
    evaluator_receipts: tuple[TeamForecastEvaluatorReceipt, ...],
    legacy_forecast_packet: TeamForecastPacket | None,
    legacy_evidence_packets: tuple[TeamForecastEvidencePacket, ...],
    policy_publication_gate: TeamForecastPolicyPublicationGate | None = None,
) -> TeamForecastBuildEnvelope:
    """Build the one canonical envelope from exact validated inputs."""
    return _materialize_envelope(
        result,
        aggregation_input=aggregation_input,
        config=config,
        scope=scope,
        run_metadata=run_metadata,
        evaluator_receipts=evaluator_receipts,
        legacy_forecast_packet=legacy_forecast_packet,
        legacy_evidence_packets=legacy_evidence_packets,
        policy_publication_gate=policy_publication_gate,
    )


def validate_team_forecast_build_envelope(
    envelope: TeamForecastBuildEnvelope,
    *,
    result: TeamEvidenceAggregationResult,
    aggregation_input: TeamEvidenceAggregationInput,
    config: TeamEvidenceAggregationConfig,
    scope: TeamForecastEvaluationScope,
    run_metadata: TeamForecastRunMetadata,
    evaluator_receipts: tuple[TeamForecastEvaluatorReceipt, ...],
    legacy_forecast_packet: TeamForecastPacket | None,
    legacy_evidence_packets: tuple[TeamForecastEvidencePacket, ...],
    policy_publication_gate: TeamForecastPolicyPublicationGate | None = None,
) -> None:
    """Validate by rematerializing from the same exact inputs."""
    if type(envelope) is not TeamForecastBuildEnvelope:
        raise ValueError("envelope must be exactly TeamForecastBuildEnvelope")
    expected = _materialize_envelope(
        result,
        aggregation_input=aggregation_input,
        config=config,
        scope=scope,
        run_metadata=run_metadata,
        evaluator_receipts=evaluator_receipts,
        legacy_forecast_packet=legacy_forecast_packet,
        legacy_evidence_packets=legacy_evidence_packets,
        policy_publication_gate=policy_publication_gate,
    )
    if envelope != expected:
        raise ValueError("envelope must equal the rematerialized envelope")
    return None


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
