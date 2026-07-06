"""Pure Phase 1 research packet source-chain integrity gate."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

DEFAULT_CONFIG_VERSION = "research-packet-source-chain-integrity-gate-v2"

SOURCE_KINDS = (
    "official_anchor",
    "independent_source",
    "contradiction_review",
    "probability_move_attribution",
    "resolution_evidence",
    "rule_clarity",
)
GATE_STATUSES = ("pass", "watch", "blocked")
ROW_STATUSES = ("pass", "blocked")

PASS_REASON = "source_chain_integrity_pass"
EMPTY_REASON = "empty_evidence"
MISSING_OFFICIAL_REASON = "missing_official_anchor"
INSUFFICIENT_FAMILY_REASON = "insufficient_independent_source_family"
STALE_REASON = "stale_source_evidence"
CONTRADICTION_REASON = "contradiction_review_incomplete"
PROBABILITY_MOVE_REASON = "probability_move_unattributed"
RESOLUTION_REASON = "resolution_evidence_insufficient"
RULE_CLARITY_REASON = "rule_clarity_below_floor"

REASON_CODE_PRIORITY = (
    PASS_REASON,
    EMPTY_REASON,
    MISSING_OFFICIAL_REASON,
    INSUFFICIENT_FAMILY_REASON,
    STALE_REASON,
    CONTRADICTION_REASON,
    PROBABILITY_MOVE_REASON,
    RESOLUTION_REASON,
    RULE_CLARITY_REASON,
)
REASON_CODES = frozenset(REASON_CODE_PRIORITY)

UNSAFE_PUBLIC_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)


@dataclass(frozen=True)
class ResearchPacketSourceChainIntegrityGateV2Config:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_official_anchor_count: Decimal = Decimal("1")
    min_independent_source_family_count: Decimal = Decimal("2")
    max_source_age_seconds: Decimal = Decimal("86400.000000")
    min_contradiction_review_count: Decimal = Decimal("1")
    max_unattributed_probability_move: Decimal = Decimal("0.010000")
    min_resolution_evidence_count: Decimal = Decimal("1")
    min_rule_clarity_score: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "min_official_anchor_count",
            "min_independent_source_family_count",
            "min_contradiction_review_count",
            "min_resolution_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _normalize_nonnegative_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "max_unattributed_probability_move",
            _normalize_probability(
                "max_unattributed_probability_move",
                self.max_unattributed_probability_move,
            ),
        )
        object.__setattr__(
            self,
            "min_rule_clarity_score",
            _normalize_probability(
                "min_rule_clarity_score",
                self.min_rule_clarity_score,
            ),
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class ResearchPacketSourceChainEvidence:
    evidence_id: str
    source_family: str
    source_kind: str
    observed_at: datetime
    probability_move_attribution: Decimal = ZERO
    rule_clarity_score: Decimal = ZERO
    resolution_evidence_score: Decimal = ZERO
    contradiction_review_complete: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("evidence_id", "source_family", "source_kind"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("source_kind", self.source_kind, SOURCE_KINDS)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "probability_move_attribution",
            "rule_clarity_score",
            "resolution_evidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if type(self.contradiction_review_complete) is not bool:
            raise ValueError("contradiction_review_complete must be a bool")
        _require_hard_flags("evidence", self)
        _reject_unsafe_public_payload("evidence", _payload_value(self))


@dataclass(frozen=True)
class ResearchPacketSourceChainIntegrityGateV2Row:
    evidence_id: str
    source_family: str
    source_kind: str
    observed_at: datetime
    source_age_seconds: Decimal
    probability_move_attribution: Decimal
    rule_clarity_score: Decimal
    resolution_evidence_score: Decimal
    contradiction_review_complete: bool
    evidence_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("evidence_id", "source_family", "source_kind"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("source_kind", self.source_kind, SOURCE_KINDS)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        for field_name in (
            "probability_move_attribution",
            "rule_clarity_score",
            "resolution_evidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if type(self.contradiction_review_complete) is not bool:
            raise ValueError("contradiction_review_complete must be a bool")
        _require_member("evidence_status", self.evidence_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.evidence_status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("evidence_status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _payload_value(self))


@dataclass(frozen=True)
class ResearchPacketSourceChainIntegrityGateV2Report:
    generated_at: datetime
    config_version: str
    source_count: Decimal
    official_anchor_count: Decimal
    independent_source_family_count: Decimal
    fresh_source_count: Decimal
    stale_source_count: Decimal
    contradiction_review_count: Decimal
    probability_move_since_prior_packet: Decimal
    probability_move_attributed: Decimal
    probability_move_unattributed: Decimal
    resolution_evidence_count: Decimal
    rule_clarity_score: Decimal
    max_source_age_seconds: Decimal
    gate_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    evidence_rows: tuple[ResearchPacketSourceChainIntegrityGateV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "source_count",
            "official_anchor_count",
            "independent_source_family_count",
            "fresh_source_count",
            "stale_source_count",
            "contradiction_review_count",
            "resolution_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "probability_move_since_prior_packet",
            "probability_move_attributed",
            "probability_move_unattributed",
            "rule_clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _normalize_nonnegative_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        _require_member("gate_status", self.gate_status, GATE_STATUSES)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "evidence_rows", _normalize_rows(self.evidence_rows))
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", _payload_value(self))
        _set_or_validate_derived_validation_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_packet_source_chain_integrity_gate_v2_public_payload(self)


def build_research_packet_source_chain_integrity_gate_v2(
    evidence_sources: Iterable[ResearchPacketSourceChainEvidence],
    *,
    config: ResearchPacketSourceChainIntegrityGateV2Config,
    generated_at: datetime,
    probability_move_since_prior_packet: Decimal,
) -> ResearchPacketSourceChainIntegrityGateV2Report:
    if type(config) is not ResearchPacketSourceChainIntegrityGateV2Config:
        raise ValueError(
            "config must be a ResearchPacketSourceChainIntegrityGateV2Config",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    probability_move = _normalize_probability(
        "probability_move_since_prior_packet",
        probability_move_since_prior_packet,
    )
    normalized_sources = _normalize_evidence_sources(
        evidence_sources,
        generated_at=generated_at_utc,
    )
    evidence_rows = tuple(
        sorted(
            (
                _row_for_evidence(
                    evidence,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for evidence in normalized_sources
            ),
            key=_row_sort_key,
        ),
    )
    probability_move_attributed = _sum_probabilities(
        row.probability_move_attribution for row in evidence_rows
    )
    probability_move_unattributed = _nonnegative_probability_delta(
        probability_move,
        probability_move_attributed,
    )
    reason_codes = _report_reason_codes(
        rows=evidence_rows,
        config=config,
        probability_move_unattributed=probability_move_unattributed,
    )
    gate_status = _gate_status_from_reason_codes(reason_codes)
    return ResearchPacketSourceChainIntegrityGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_count=_count(len(evidence_rows)),
        official_anchor_count=_count(
            sum(1 for row in evidence_rows if row.source_kind == "official_anchor"),
        ),
        independent_source_family_count=_count(
            len(
                {
                    row.source_family
                    for row in evidence_rows
                    if row.source_kind != "official_anchor"
                },
            ),
        ),
        fresh_source_count=_count(
            sum(
                1
                for row in evidence_rows
                if row.source_age_seconds <= config.max_source_age_seconds
            ),
        ),
        stale_source_count=_count(
            sum(
                1
                for row in evidence_rows
                if row.source_age_seconds > config.max_source_age_seconds
            ),
        ),
        contradiction_review_count=_count(
            sum(
                1
                for row in evidence_rows
                if row.source_kind == "contradiction_review"
                and row.contradiction_review_complete
            ),
        ),
        probability_move_since_prior_packet=probability_move,
        probability_move_attributed=probability_move_attributed,
        probability_move_unattributed=probability_move_unattributed,
        resolution_evidence_count=_count(
            sum(1 for row in evidence_rows if row.source_kind == "resolution_evidence"),
        ),
        rule_clarity_score=_max_probability(
            row.rule_clarity_score
            for row in evidence_rows
            if row.source_kind in ("official_anchor", "rule_clarity")
        ),
        max_source_age_seconds=_max_decimal(row.source_age_seconds for row in evidence_rows),
        gate_status=gate_status,
        recommended_next_step=_recommended_next_step(gate_status),
        reason_codes=reason_codes,
        evidence_rows=evidence_rows,
    )


def research_packet_source_chain_integrity_gate_v2_public_payload(
    value: ResearchPacketSourceChainIntegrityGateV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchPacketSourceChainIntegrityGateV2Report:
        _validate_report(value)
        _validate_derived_validation_digest(value)
        payload = _payload_value(value)
    elif type(value) is dict:
        payload = value
    else:
        raise ValueError(
            "value must be a ResearchPacketSourceChainIntegrityGateV2Report or dict",
        )
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    validate_research_packet_source_chain_integrity_gate_v2_public_payload(payload)
    return dict(payload)


def validate_research_packet_source_chain_integrity_gate_v2_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("public payload", payload)
    _require_public_payload_flags(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _row_for_evidence(
    evidence: ResearchPacketSourceChainEvidence,
    *,
    config: ResearchPacketSourceChainIntegrityGateV2Config,
    generated_at: datetime,
) -> ResearchPacketSourceChainIntegrityGateV2Row:
    source_age_seconds = _seconds_between(evidence.observed_at, generated_at)
    reason_codes = _row_reason_codes(
        evidence,
        source_age_seconds=source_age_seconds,
        config=config,
    )
    return ResearchPacketSourceChainIntegrityGateV2Row(
        evidence_id=evidence.evidence_id,
        source_family=evidence.source_family,
        source_kind=evidence.source_kind,
        observed_at=evidence.observed_at,
        source_age_seconds=source_age_seconds,
        probability_move_attribution=evidence.probability_move_attribution,
        rule_clarity_score=evidence.rule_clarity_score,
        resolution_evidence_score=evidence.resolution_evidence_score,
        contradiction_review_complete=evidence.contradiction_review_complete,
        evidence_status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    evidence: ResearchPacketSourceChainEvidence,
    *,
    source_age_seconds: Decimal,
    config: ResearchPacketSourceChainIntegrityGateV2Config,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if source_age_seconds > config.max_source_age_seconds:
        reasons.append(STALE_REASON)
    if (
        evidence.source_kind == "contradiction_review"
        and not evidence.contradiction_review_complete
    ):
        reasons.append(CONTRADICTION_REASON)
    if not reasons:
        return (PASS_REASON,)
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _report_reason_codes(
    *,
    rows: tuple[ResearchPacketSourceChainIntegrityGateV2Row, ...],
    config: ResearchPacketSourceChainIntegrityGateV2Config,
    probability_move_unattributed: Decimal,
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons: list[str] = []
    official_anchor_count = _count(
        sum(1 for row in rows if row.source_kind == "official_anchor"),
    )
    independent_family_count = _count(
        len({row.source_family for row in rows if row.source_kind != "official_anchor"}),
    )
    stale_source_count = _count(
        sum(1 for row in rows if row.source_age_seconds > config.max_source_age_seconds),
    )
    contradiction_review_count = _count(
        sum(
            1
            for row in rows
            if row.source_kind == "contradiction_review"
            and row.contradiction_review_complete
        ),
    )
    resolution_evidence_count = _count(
        sum(1 for row in rows if row.source_kind == "resolution_evidence"),
    )
    rule_clarity_score = _max_probability(
        row.rule_clarity_score
        for row in rows
        if row.source_kind in ("official_anchor", "rule_clarity")
    )
    if official_anchor_count < config.min_official_anchor_count:
        reasons.append(MISSING_OFFICIAL_REASON)
    if independent_family_count < config.min_independent_source_family_count:
        reasons.append(INSUFFICIENT_FAMILY_REASON)
    if stale_source_count > ZERO:
        reasons.append(STALE_REASON)
    if contradiction_review_count < config.min_contradiction_review_count:
        reasons.append(CONTRADICTION_REASON)
    if probability_move_unattributed > config.max_unattributed_probability_move:
        reasons.append(PROBABILITY_MOVE_REASON)
    if resolution_evidence_count < config.min_resolution_evidence_count:
        reasons.append(RESOLUTION_REASON)
    if rule_clarity_score < config.min_rule_clarity_score:
        reasons.append(RULE_CLARITY_REASON)
    if not reasons:
        return (PASS_REASON,)
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _normalize_evidence_sources(
    value: Iterable[ResearchPacketSourceChainEvidence],
    *,
    generated_at: datetime,
) -> tuple[ResearchPacketSourceChainEvidence, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("evidence_sources must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("evidence_sources must be an iterable") from exc
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketSourceChainEvidence:
            raise ValueError(
                "evidence_sources must contain ResearchPacketSourceChainEvidence values",
            )
        _require_hard_flags("evidence", row)
        if row.evidence_id in seen_ids:
            raise ValueError("evidence_id values must be unique")
        seen_ids.add(row.evidence_id)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    return tuple(sorted(rows, key=_evidence_sort_key))


def _normalize_rows(
    value: Iterable[ResearchPacketSourceChainIntegrityGateV2Row],
) -> tuple[ResearchPacketSourceChainIntegrityGateV2Row, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("evidence_rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("evidence_rows must be an iterable") from exc
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketSourceChainIntegrityGateV2Row:
            raise ValueError(
                "evidence_rows must contain ResearchPacketSourceChainIntegrityGateV2Row values",
            )
        _require_hard_flags("row", row)
        if row.evidence_id in seen_ids:
            raise ValueError("evidence_rows evidence_id values must be unique")
        seen_ids.add(row.evidence_id)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != sorted_rows:
        raise ValueError("evidence_rows must be sorted deterministically")
    return rows


def _validate_report(report: ResearchPacketSourceChainIntegrityGateV2Report) -> None:
    rows = report.evidence_rows
    if report.source_count != _count(len(rows)):
        raise ValueError("source_count must match evidence_rows")
    if report.official_anchor_count != _count(
        sum(1 for row in rows if row.source_kind == "official_anchor"),
    ):
        raise ValueError("official_anchor_count must match evidence_rows")
    if report.independent_source_family_count != _count(
        len({row.source_family for row in rows if row.source_kind != "official_anchor"}),
    ):
        raise ValueError("independent_source_family_count must match evidence_rows")
    if report.fresh_source_count != _count(
        sum(1 for row in rows if STALE_REASON not in row.reason_codes),
    ):
        raise ValueError("fresh_source_count must match evidence_rows")
    if report.stale_source_count != _count(
        sum(1 for row in rows if STALE_REASON in row.reason_codes),
    ):
        raise ValueError("stale_source_count must match evidence_rows")
    if report.contradiction_review_count != _count(
        sum(
            1
            for row in rows
            if row.source_kind == "contradiction_review"
            and row.contradiction_review_complete
        ),
    ):
        raise ValueError("contradiction_review_count must match evidence_rows")
    if report.probability_move_attributed != _sum_probabilities(
        row.probability_move_attribution for row in rows
    ):
        raise ValueError("probability_move_attributed must match evidence_rows")
    if report.probability_move_unattributed != _nonnegative_probability_delta(
        report.probability_move_since_prior_packet,
        report.probability_move_attributed,
    ):
        raise ValueError("probability_move_unattributed must match probability move")
    if report.resolution_evidence_count != _count(
        sum(1 for row in rows if row.source_kind == "resolution_evidence"),
    ):
        raise ValueError("resolution_evidence_count must match evidence_rows")
    if report.rule_clarity_score != _max_probability(
        row.rule_clarity_score
        for row in rows
        if row.source_kind in ("official_anchor", "rule_clarity")
    ):
        raise ValueError("rule_clarity_score must match evidence_rows")
    if report.max_source_age_seconds != _max_decimal(
        row.source_age_seconds for row in rows
    ):
        raise ValueError("max_source_age_seconds must match evidence_rows")
    if report.gate_status != _gate_status_from_reason_codes(report.reason_codes):
        raise ValueError("gate_status must match reason_codes")
    if report.recommended_next_step != _recommended_next_step(report.gate_status):
        raise ValueError("recommended_next_step must match gate_status")


def _set_or_validate_derived_validation_digest(
    report: ResearchPacketSourceChainIntegrityGateV2Report,
) -> None:
    current = report.derived_validation_digest
    expected = _derived_validation_digest(report)
    if current == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    _require_sha256_digest("derived_validation_digest", current)
    if current != expected:
        raise ValueError("derived_validation_digest must match report fields")


def _validate_derived_validation_digest(
    report: ResearchPacketSourceChainIntegrityGateV2Report,
) -> None:
    current = _require_sha256_digest(
        "derived_validation_digest",
        report.derived_validation_digest,
    )
    if current != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(value: object) -> str:
    payload = _without_derived_validation_digest(_payload_value(value))
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _without_derived_validation_digest(value: object) -> object:
    if type(value) is dict:
        return {
            key: _without_derived_validation_digest(item)
            for key, item in value.items()
            if key != "derived_validation_digest"
        }
    if type(value) is list:
        return [_without_derived_validation_digest(item) for item in value]
    return value


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple or type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    return value


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public payload value in {path or label}")
        return
    if isinstance(value, (Decimal, int, float)):
        raise ValueError(f"{path or label} must use Decimal strings, not numeric values")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public payload key in {label}: {key}")
            item_path = key if not path else f"{path}.{key}"
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not public JSON serializable")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    return _normalize_nonnegative_decimal(
        "source_age_seconds",
        Decimal(str((end - start).total_seconds())),
    )


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    normalized = value.quantize(COUNT_QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _sum_probabilities(values: Iterable[Decimal]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = sum(values, ZERO)
    return min(_normalize_probability("probability_move_attributed", total), ONE)


def _nonnegative_probability_delta(value: Decimal, offset: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        result = value - offset
    if result <= ZERO:
        return ZERO
    return _normalize_probability("probability_move_unattributed", result)


def _max_probability(values: Iterable[Decimal]) -> Decimal:
    return max(tuple(values), default=ZERO)


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    return max(tuple(values), default=ZERO)


def _normalize_reason_codes(field_name: str, value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of reason codes")
    try:
        codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of reason codes") from exc
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        if type(code) is not str or not code:
            raise ValueError(f"{field_name} must contain non-empty strings")
        if code not in REASON_CODES:
            raise ValueError(f"{field_name} contains an unknown reason code")
    active_codes = [code for code in codes if code != PASS_REASON]
    if PASS_REASON in codes and active_codes:
        raise ValueError(f"{field_name} pass reason must stand alone")
    if EMPTY_REASON in codes and len(codes) != 1:
        raise ValueError(f"{field_name} empty reason must stand alone")
    return tuple(sorted(set(codes), key=REASON_CODE_PRIORITY.index))


def _gate_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return "pass"
    return "blocked"


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return "pass"
    return "blocked"


def _recommended_next_step(gate_status: str) -> str:
    if gate_status == "pass":
        return "continue_research_review"
    if gate_status == "watch":
        return "refresh_source_evidence"
    return "repair_source_chain_evidence"


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be one of {members}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip() or "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a canonical string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public content")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _evidence_sort_key(
    evidence: ResearchPacketSourceChainEvidence,
) -> tuple[str, str, str]:
    return (evidence.source_family, evidence.source_kind, evidence.evidence_id)


def _row_sort_key(
    row: ResearchPacketSourceChainIntegrityGateV2Row,
) -> tuple[str, str, str]:
    return (row.source_family, row.source_kind, row.evidence_id)


__all__ = (
    "ResearchPacketSourceChainEvidence",
    "ResearchPacketSourceChainIntegrityGateV2Config",
    "ResearchPacketSourceChainIntegrityGateV2Report",
    "ResearchPacketSourceChainIntegrityGateV2Row",
    "build_research_packet_source_chain_integrity_gate_v2",
    "research_packet_source_chain_integrity_gate_v2_public_payload",
    "validate_research_packet_source_chain_integrity_gate_v2_public_payload",
)
