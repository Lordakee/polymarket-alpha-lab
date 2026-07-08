"""Pure report-only aggregate source-claim consistency gate."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_SOURCE_CLAIM_CONSISTENCY_GATE_REPORT_CONFIG_VERSION = (
    "research-source-claim-consistency-gate-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_GATE_STATUSES = frozenset(("pass", "watch", "block"))
_CLAIM_STATES = ("supports", "contradicts", "neutral")
_CLAIM_STATE_RANK = {claim_state: index for index, claim_state in enumerate(_CLAIM_STATES)}
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_REASON_CODE_SEQUENCE = (
    "source_claim_class_agreement_block",
    "source_claim_class_agreement_watch",
    "stale_contradictory_claims",
    "unresolved_conflict_pressure_watch",
    "unresolved_conflict_pressure_block",
    "recheck_due",
    "recheck_urgency_watch",
    "recheck_urgency_block",
    "source_claim_consistency_pass",
)
_DERIVED_DIGEST_FIELD = "derived_validation_digest"
_FLAG_FIELDS = ("paper_only", "report_only", "readonly")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_PUBLIC_TERMS = (
    "credential",
    "secret",
    "private",
    "private_key",
    _join_parts("li", "ve"),
    _join_parts("tra", "ding"),
    _join_parts("au", "th"),
    _join_parts("wal", "let"),
    _join_parts("acc", "ount"),
    _join_parts("bro", "ker"),
    _join_parts("or", "der"),
    _join_parts("sub", "mit"),
    _join_parts("can", "cel"),
    _join_parts("re", "place"),
    _join_parts("sig", "ning"),
    _join_parts("net", "work"),
    _join_parts("data", "base"),
    _join_parts("data", "base", "_", "url"),
    _join_parts("candidate", "_", "id"),
    _join_parts("mar", "ket", "_", "id"),
    _join_parts("mar", "ket", "_", "slug"),
    _join_parts("que", "stion"),
    _join_parts("source", "_", "url"),
    _join_parts("source", "_", "text"),
    _join_parts("raw", "_", "source"),
    "recommend",
)
_UNSAFE_PUBLIC_TOKENS = frozenset(
    (
        "candidate",
        "dsn",
        "http",
        "https",
        "table",
        "token",
        "url",
        "www",
    ),
)


@dataclass(frozen=True)
class ResearchSourceClaimConsistencyGateConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_CLAIM_CONSISTENCY_GATE_REPORT_CONFIG_VERSION
    )
    watch_agreement_threshold: Decimal = Decimal("0.600000")
    pass_agreement_threshold: Decimal = Decimal("0.800000")
    stale_claim_age_seconds: Decimal = Decimal("86400.000000")
    unresolved_conflict_watch_threshold: Decimal = Decimal("0.250000")
    unresolved_conflict_block_threshold: Decimal = Decimal("0.500000")
    recheck_urgency_watch_threshold: Decimal = Decimal("0.300000")
    recheck_urgency_block_threshold: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimConsistencyGateConfig:
            raise TypeError(
                "ResearchSourceClaimConsistencyGateConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimConsistencyGateConfig:
            raise ValueError(
                "config must be exactly ResearchSourceClaimConsistencyGateConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CLAIM_CONSISTENCY_GATE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "stale_claim_age_seconds",
            _require_positive_decimal(
                "stale_claim_age_seconds",
                self.stale_claim_age_seconds,
            ),
        )
        for field_name in (
            "watch_agreement_threshold",
            "pass_agreement_threshold",
            "unresolved_conflict_watch_threshold",
            "unresolved_conflict_block_threshold",
            "recheck_urgency_watch_threshold",
            "recheck_urgency_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_agreement_threshold <= self.watch_agreement_threshold:
            raise ValueError(
                "watch_agreement_threshold must be less than pass_agreement_threshold",
            )
        if (
            self.unresolved_conflict_block_threshold
            <= self.unresolved_conflict_watch_threshold
        ):
            raise ValueError(
                "unresolved_conflict_watch_threshold must be less than "
                "unresolved_conflict_block_threshold",
            )
        if self.recheck_urgency_block_threshold <= self.recheck_urgency_watch_threshold:
            raise ValueError(
                "recheck_urgency_watch_threshold must be less than "
                "recheck_urgency_block_threshold",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceClaimConsistencyGateInputRow:
    aggregate_label: str
    source_class: str
    claim_state: str
    observed_at: datetime
    unresolved_conflict_count: Decimal = Decimal("0.000000")
    recheck_due_at: datetime | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimConsistencyGateInputRow:
            raise TypeError(
                "ResearchSourceClaimConsistencyGateInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimConsistencyGateInputRow:
            raise ValueError(
                "input row must be exactly ResearchSourceClaimConsistencyGateInputRow",
            )
        _require_public_identifier("aggregate_label", self.aggregate_label)
        _require_public_identifier("source_class", self.source_class)
        _require_claim_state("claim_state", self.claim_state)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "unresolved_conflict_count",
            _require_nonnegative_decimal(
                "unresolved_conflict_count",
                self.unresolved_conflict_count,
            ),
        )
        if self.recheck_due_at is not None:
            object.__setattr__(
                self,
                "recheck_due_at",
                _as_utc("recheck_due_at", self.recheck_due_at),
            )
            if self.recheck_due_at < self.observed_at:
                raise ValueError("recheck_due_at must not be before observed_at")
        _require_hard_flags("input row", self)
        _reject_unsafe_public_payload("input row", self)


@dataclass(frozen=True)
class ResearchSourceClaimConsistencyPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimConsistencyPublicPayloadItem:
            raise TypeError(
                "ResearchSourceClaimConsistencyPublicPayloadItem does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimConsistencyPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchSourceClaimConsistencyPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchSourceClaimConsistencyGateRow:
    aggregate_label: str
    source_class_count: Decimal
    claim_summary_count: Decimal
    majority_claim_state: str
    majority_source_class_count: Decimal
    source_class_agreement_score: Decimal
    stale_contradictory_claim_count: Decimal
    unresolved_conflict_count: Decimal
    unresolved_conflict_pressure_score: Decimal
    recheck_due_count: Decimal
    recheck_urgency_score: Decimal
    gate_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimConsistencyGateRow:
            raise TypeError(
                "ResearchSourceClaimConsistencyGateRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimConsistencyGateRow:
            raise ValueError("row must be exactly ResearchSourceClaimConsistencyGateRow")
        _require_public_identifier("aggregate_label", self.aggregate_label)
        for field_name in (
            "source_class_count",
            "claim_summary_count",
            "majority_source_class_count",
            "stale_contradictory_claim_count",
            "unresolved_conflict_count",
            "recheck_due_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_class_agreement_score",
            "unresolved_conflict_pressure_score",
            "recheck_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_claim_state("majority_claim_state", self.majority_claim_state)
        _require_gate_status("gate_status", self.gate_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceClaimConsistencyGateReport:
    generated_at: datetime
    config_version: str
    gate_status: str
    aggregate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    claim_summary_count: Decimal
    stale_contradictory_claim_count: Decimal
    average_source_class_agreement_score: Decimal
    max_unresolved_conflict_pressure_score: Decimal
    max_recheck_urgency_score: Decimal
    rows: tuple[ResearchSourceClaimConsistencyGateRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchSourceClaimConsistencyPublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimConsistencyGateReport:
            raise TypeError(
                "ResearchSourceClaimConsistencyGateReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceClaimConsistencyGateReport:
            raise ValueError(
                "report must be exactly ResearchSourceClaimConsistencyGateReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CLAIM_CONSISTENCY_GATE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_gate_status("gate_status", self.gate_status)
        for field_name in (
            "aggregate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "claim_summary_count",
            "stale_contradictory_claim_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_source_class_agreement_score",
            "max_unresolved_conflict_pressure_score",
            "max_recheck_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest != _report_digest(self):
            raise ValueError("derived_validation_digest mismatch")

    @property
    def payload(self) -> dict[str, object]:
        return research_source_claim_consistency_gate_report_payload(self)


def build_research_source_claim_consistency_gate_report(
    input_rows: Sequence[ResearchSourceClaimConsistencyGateInputRow],
    *,
    generated_at: datetime,
    config: ResearchSourceClaimConsistencyGateConfig | None = None,
    public_payload: Sequence[ResearchSourceClaimConsistencyPublicPayloadItem] = (),
) -> ResearchSourceClaimConsistencyGateReport:
    """Build a deterministic local aggregate consistency report."""

    if config is None:
        config = ResearchSourceClaimConsistencyGateConfig()
    if type(config) is not ResearchSourceClaimConsistencyGateConfig:
        raise ValueError("config must be a ResearchSourceClaimConsistencyGateConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, generated_at=generated_at)
    payload_items = _normalize_public_payload(public_payload)
    gate_rows = _sort_rows(
        tuple(
            _row_for_aggregate(
                aggregate_label,
                tuple(group_rows),
                generated_at=generated_at,
                config=config,
            )
            for aggregate_label, group_rows in _group_rows(rows).items()
        ),
    )
    gate_status = _report_status(gate_rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "gate_status": gate_status,
        "aggregate_count": _decimal_count(len(gate_rows)),
        "pass_count": _decimal_count(_status_count(gate_rows, "pass")),
        "watch_count": _decimal_count(_status_count(gate_rows, "watch")),
        "block_count": _decimal_count(_status_count(gate_rows, "block")),
        "claim_summary_count": _decimal_count(len(rows)),
        "stale_contradictory_claim_count": _decimal_sum(
            tuple(row.stale_contradictory_claim_count for row in gate_rows),
        ),
        "average_source_class_agreement_score": _average_ratio(
            tuple(row.source_class_agreement_score for row in gate_rows),
            empty_value=_ONE,
        ),
        "max_unresolved_conflict_pressure_score": max(
            (row.unresolved_conflict_pressure_score for row in gate_rows),
            default=_ZERO,
        ),
        "max_recheck_urgency_score": max(
            (row.recheck_urgency_score for row in gate_rows),
            default=_ZERO,
        ),
        "rows": gate_rows,
        "reason_codes": _report_reason_codes(gate_rows),
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceClaimConsistencyGateReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_claim_consistency_gate_report_payload(
    value: ResearchSourceClaimConsistencyGateReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchSourceClaimConsistencyGateReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchSourceClaimConsistencyGateReport or dict",
        )
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_public_payload_digest(payload)
    return payload


def _row_for_aggregate(
    aggregate_label: str,
    rows: tuple[ResearchSourceClaimConsistencyGateInputRow, ...],
    *,
    generated_at: datetime,
    config: ResearchSourceClaimConsistencyGateConfig,
) -> ResearchSourceClaimConsistencyGateRow:
    source_class_count = _decimal_count(len({row.source_class for row in rows}))
    claim_summary_count = _decimal_count(len(rows))
    majority_claim_state, majority_count = _majority_claim_state(rows)
    agreement_score = _ratio(majority_count, source_class_count)
    stale_count = _decimal_count(
        sum(
            1
            for row in rows
            if row.claim_state == "contradicts"
            and _age_seconds(generated_at, row.observed_at) >= config.stale_claim_age_seconds
        ),
    )
    unresolved_count = _decimal_sum(tuple(row.unresolved_conflict_count for row in rows))
    pressure_score = _clamp_ratio(_ratio(unresolved_count, source_class_count))
    recheck_due_count = _decimal_count(
        sum(1 for row in rows if row.recheck_due_at is not None and row.recheck_due_at <= generated_at),
    )
    recheck_urgency_score = _ONE if recheck_due_count > _ZERO else _ZERO
    reason_codes = _row_reason_codes(
        agreement_score=agreement_score,
        stale_count=stale_count,
        pressure_score=pressure_score,
        recheck_due_count=recheck_due_count,
        recheck_urgency_score=recheck_urgency_score,
        config=config,
    )
    gate_status = _row_status(reason_codes)
    return ResearchSourceClaimConsistencyGateRow(
        aggregate_label=aggregate_label,
        source_class_count=source_class_count,
        claim_summary_count=claim_summary_count,
        majority_claim_state=majority_claim_state,
        majority_source_class_count=majority_count,
        source_class_agreement_score=agreement_score,
        stale_contradictory_claim_count=stale_count,
        unresolved_conflict_count=unresolved_count,
        unresolved_conflict_pressure_score=pressure_score,
        recheck_due_count=recheck_due_count,
        recheck_urgency_score=recheck_urgency_score,
        gate_status=gate_status,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    agreement_score: Decimal,
    stale_count: Decimal,
    pressure_score: Decimal,
    recheck_due_count: Decimal,
    recheck_urgency_score: Decimal,
    config: ResearchSourceClaimConsistencyGateConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if agreement_score < config.watch_agreement_threshold:
        reasons.append("source_claim_class_agreement_block")
    elif agreement_score < config.pass_agreement_threshold:
        reasons.append("source_claim_class_agreement_watch")
    if stale_count > _ZERO:
        reasons.append("stale_contradictory_claims")
    if pressure_score >= config.unresolved_conflict_block_threshold:
        reasons.append("unresolved_conflict_pressure_block")
    elif pressure_score >= config.unresolved_conflict_watch_threshold:
        reasons.append("unresolved_conflict_pressure_watch")
    if recheck_due_count > _ZERO:
        reasons.append("recheck_due")
    if recheck_urgency_score >= config.recheck_urgency_block_threshold:
        reasons.append("recheck_urgency_block")
    elif recheck_urgency_score >= config.recheck_urgency_watch_threshold:
        reasons.append("recheck_urgency_watch")
    if not reasons:
        reasons.append("source_claim_consistency_pass")
    return tuple(code for code in _REASON_CODE_SEQUENCE if code in reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        "source_claim_class_agreement_block" in reason_codes
        or "unresolved_conflict_pressure_block" in reason_codes
        or "recheck_urgency_block" in reason_codes
    ):
        return "block"
    if reason_codes != ("source_claim_consistency_pass",):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchSourceClaimConsistencyGateRow, ...]) -> str:
    if any(row.gate_status == "block" for row in rows):
        return "block"
    if any(row.gate_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceClaimConsistencyGateRow, ...],
) -> tuple[str, ...]:
    reasons: list[str] = []
    for reason_code in _REASON_CODE_SEQUENCE:
        if any(reason_code in row.reason_codes for row in rows):
            reasons.append(reason_code)
    if not reasons:
        reasons.append("source_claim_consistency_pass")
    return tuple(reasons)


def _majority_claim_state(
    rows: tuple[ResearchSourceClaimConsistencyGateInputRow, ...],
) -> tuple[str, Decimal]:
    counts = {
        claim_state: sum(1 for row in rows if row.claim_state == claim_state)
        for claim_state in _CLAIM_STATES
    }
    claim_state = min(
        _CLAIM_STATES,
        key=lambda state: (-counts[state], _CLAIM_STATE_RANK[state]),
    )
    return claim_state, _decimal_count(counts[claim_state])


def _group_rows(
    rows: tuple[ResearchSourceClaimConsistencyGateInputRow, ...],
) -> dict[str, tuple[ResearchSourceClaimConsistencyGateInputRow, ...]]:
    grouped: dict[str, list[ResearchSourceClaimConsistencyGateInputRow]] = {}
    for row in rows:
        grouped.setdefault(row.aggregate_label, []).append(row)
    return {
        aggregate_label: tuple(group_rows)
        for aggregate_label, group_rows in sorted(grouped.items())
    }


def _validate_row_consistency(row: ResearchSourceClaimConsistencyGateRow) -> None:
    if row.source_class_count <= _ZERO:
        raise ValueError("source_class_count must be positive")
    if row.claim_summary_count < row.source_class_count:
        raise ValueError("claim_summary_count must cover source_class_count")
    if row.majority_source_class_count > row.source_class_count:
        raise ValueError("majority_source_class_count cannot exceed source_class_count")
    if row.source_class_agreement_score != _ratio(
        row.majority_source_class_count,
        row.source_class_count,
    ):
        raise ValueError("source_class_agreement_score must match majority count")
    if row.unresolved_conflict_pressure_score != _clamp_ratio(
        _ratio(row.unresolved_conflict_count, row.source_class_count),
    ):
        raise ValueError(
            "unresolved_conflict_pressure_score must match unresolved conflicts",
        )
    expected_urgency = _ONE if row.recheck_due_count > _ZERO else _ZERO
    if row.recheck_urgency_score != expected_urgency:
        raise ValueError("recheck_urgency_score must match due count")
    if row.gate_status != _row_status(row.reason_codes):
        raise ValueError("gate_status must match reason_codes")
    if row.gate_status == "pass" and row.reason_codes != ("source_claim_consistency_pass",):
        raise ValueError("pass rows require pass reason")


def _validate_report_consistency(report: ResearchSourceClaimConsistencyGateReport) -> None:
    if report.aggregate_count != _decimal_count(len(report.rows)):
        raise ValueError("aggregate_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.aggregate_count:
        raise ValueError("status counts must match aggregate_count")
    if report.claim_summary_count != _decimal_sum(
        tuple(row.claim_summary_count for row in report.rows),
    ):
        raise ValueError("claim_summary_count must match rows")
    if report.stale_contradictory_claim_count != _decimal_sum(
        tuple(row.stale_contradictory_claim_count for row in report.rows),
    ):
        raise ValueError("stale_contradictory_claim_count must match rows")
    if report.average_source_class_agreement_score != _average_ratio(
        tuple(row.source_class_agreement_score for row in report.rows),
        empty_value=_ONE,
    ):
        raise ValueError("average_source_class_agreement_score must match rows")
    if report.max_unresolved_conflict_pressure_score != max(
        (row.unresolved_conflict_pressure_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_unresolved_conflict_pressure_score must match rows")
    if report.max_recheck_urgency_score != max(
        (row.recheck_urgency_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_recheck_urgency_score must match rows")
    if report.gate_status != _report_status(report.rows):
        raise ValueError("gate_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_input_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchSourceClaimConsistencyGateInputRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchSourceClaimConsistencyGateInputRow:
            raise ValueError("input rows must contain source claim consistency rows")
        _require_hard_flags("input row", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")
        key = (row.aggregate_label, row.source_class)
        if key in seen:
            raise ValueError("duplicate source_class for aggregate_label")
        seen.add(key)
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.aggregate_label,
                row.source_class,
                row.claim_state,
            ),
        ),
    )


def _normalize_rows(value: object) -> tuple[ResearchSourceClaimConsistencyGateRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceClaimConsistencyGateRow:
            raise ValueError("rows must contain source claim consistency gate rows")
        _require_hard_flags("row", row)
        if row.aggregate_label in seen:
            raise ValueError("rows must be unique by aggregate_label")
        seen.add(row.aggregate_label)
    expected = _sort_rows(rows)
    if rows != expected:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _sort_rows(
    rows: tuple[ResearchSourceClaimConsistencyGateRow, ...],
) -> tuple[ResearchSourceClaimConsistencyGateRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _STATUS_RANK[row.gate_status],
                row.aggregate_label,
            ),
        ),
    )


def _normalize_public_payload(
    value: object,
) -> tuple[ResearchSourceClaimConsistencyPublicPayloadItem, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("public_payload must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceClaimConsistencyPublicPayloadItem:
            raise ValueError("public_payload must contain public payload items")
        _require_hard_flags("public payload item", row)
        if row.key in seen:
            raise ValueError("public_payload keys must be unique")
        seen.add(row.key)
    return tuple(sorted(rows, key=lambda row: row.key))


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be known")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in _REASON_CODE_SEQUENCE if code in reason_codes) != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _status_count(
    rows: tuple[ResearchSourceClaimConsistencyGateRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.gate_status == status)


def _average_ratio(values: tuple[Decimal, ...], *, empty_value: Decimal = _ZERO) -> Decimal:
    if not values:
        return empty_value
    return _ratio(_decimal_sum(values), _decimal_count(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(_QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value <= _ZERO:
        return _ZERO
    if value >= _ONE:
        return _ONE
    return value.quantize(_QUANT)


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(_QUANT)


def _decimal_sum(values: tuple[Decimal, ...]) -> Decimal:
    total = _ZERO
    for value in values:
        total += value
    return total.quantize(_QUANT)


def _age_seconds(end_at: datetime, start_at: datetime) -> Decimal:
    delta = _as_utc("end_at", end_at) - _as_utc("start_at", start_at)
    value = (
        Decimal(delta.days) * _SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND)
    )
    if value < _ZERO:
        raise ValueError("age_seconds must be nonnegative")
    return value.quantize(_QUANT)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(_QUANT)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > _ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_gate_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_claim_state(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _CLAIM_STATES:
        raise ValueError(f"{field_name} must be supports, contradicts, or neutral")


def _require_public_identifier(field_name: str, value: object) -> None:
    _require_public_text(field_name, value)
    if _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    if _has_unsafe_text(value):
        raise ValueError(f"{field_name} contains unsafe public text")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest")


def _has_unsafe_text(value: str) -> bool:
    lowered = value.lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    compact = re.sub(r"[^a-z0-9]+", "", lowered)
    tokens = frozenset(token for token in normalized.split("_") if token)
    if "://" in lowered or "?" in lowered:
        return True
    return any(
        term in normalized or term in compact for term in _UNSAFE_PUBLIC_TERMS
    ) or any(token in tokens for token in _UNSAFE_PUBLIC_TOKENS)


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=allow_json_containers,
        )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers and type(value) is not dict:
            raise ValueError(f"{label} must use plain dict containers")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_text(key):
                raise ValueError(f"unsafe public key in {label}")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str and _has_unsafe_text(value):
        raise ValueError(f"unsafe public text in {label}")


def _report_payload(report: ResearchSourceClaimConsistencyGateReport) -> dict[str, object]:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _report_digest(report: ResearchSourceClaimConsistencyGateReport) -> str:
    return _report_digest_from_values(_report_values_without_digest(report))


def _report_values_without_digest(
    report: ResearchSourceClaimConsistencyGateReport,
) -> dict[str, object]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != _DERIVED_DIGEST_FIELD
    }


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _validate_public_payload_digest(payload: dict[str, object]) -> None:
    digest = payload.get(_DERIVED_DIGEST_FIELD)
    if digest is None:
        return
    _require_digest(_DERIVED_DIGEST_FIELD, digest)
    values = {key: item for key, item in payload.items() if key != _DERIVED_DIGEST_FIELD}
    if digest != _report_digest_from_values(values):
        raise ValueError("derived_validation_digest mismatch")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, bool):
        return value
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal-derived strings")
    if isinstance(value, str):
        if _has_unsafe_text(value):
            raise ValueError("JSON string contains unsafe public text")
        return value
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied = _copy_json_value(value)
    if type(copied) is not dict:
        raise ValueError("payload must be a dict")
    return copied


def _copy_json_value(value: object) -> object:
    if value is None or type(value) is bool or type(value) is str:
        if type(value) is str and _has_unsafe_text(value):
            raise ValueError("payload contains unsafe public text")
        return value
    if type(value) is int or isinstance(value, Decimal):
        raise ValueError("payload numeric values must be Decimal-derived strings")
    if isinstance(value, Mapping):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_text(key):
                raise ValueError("payload contains unsafe public key")
            ready[key] = _copy_json_value(item)
        return ready
    if isinstance(value, list):
        return [_copy_json_value(item) for item in value]
    raise ValueError("payload is not JSON serializable")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_CLAIM_CONSISTENCY_GATE_REPORT_CONFIG_VERSION",
    "ResearchSourceClaimConsistencyGateConfig",
    "ResearchSourceClaimConsistencyGateInputRow",
    "ResearchSourceClaimConsistencyGateReport",
    "ResearchSourceClaimConsistencyGateRow",
    "ResearchSourceClaimConsistencyPublicPayloadItem",
    "build_research_source_claim_consistency_gate_report",
    "research_source_claim_consistency_gate_report_payload",
)
