"""Report-only event resolution evidence quorum tail reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_EVENT_RESOLUTION_EVIDENCE_QUORUM_TAIL_REPORT_CONFIG_VERSION = (
    "research-event-resolution-evidence-quorum-tail-report-v0"
)

SIX = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SHA256_HEX_LENGTH = 64

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

EMPTY_REASON = "research_event_resolution_evidence_quorum_tail_empty"
PASS_REASON = "evidence_quorum_tail_pass"
WATCH_REASON = "evidence_quorum_tail_watch"
BLOCK_REASON = "evidence_quorum_tail_block"
LOW_QUORUM_WATCH_REASON = "low_quorum_score_watch"
LOW_QUORUM_BLOCK_REASON = "low_quorum_score_block"
LOW_FAMILY_WATCH_REASON = "insufficient_independent_family_watch"
LOW_FAMILY_BLOCK_REASON = "insufficient_independent_family_block"
OPPOSITION_WATCH_REASON = "opposition_pressure_watch"
OPPOSITION_BLOCK_REASON = "opposition_pressure_block"
STALE_WATCH_REASON = "stale_evidence_pressure_watch"
STALE_BLOCK_REASON = "stale_evidence_pressure_block"
REPORT_REASON_CODES = (EMPTY_REASON, BLOCK_REASON, WATCH_REASON, PASS_REASON)
ROW_REASON_CODES = (
    PASS_REASON,
    WATCH_REASON,
    BLOCK_REASON,
    LOW_QUORUM_WATCH_REASON,
    LOW_QUORUM_BLOCK_REASON,
    LOW_FAMILY_WATCH_REASON,
    LOW_FAMILY_BLOCK_REASON,
    OPPOSITION_WATCH_REASON,
    OPPOSITION_BLOCK_REASON,
    STALE_WATCH_REASON,
    STALE_BLOCK_REASON,
)


def _j(*parts: str) -> str:
    return "".join(parts)


BAD_PUBLIC_FRAGMENTS = (
    _j("cand", "idate"),
    _j("mark", "et"),
    _j("sl", "ug"),
    _j("que", "stion"),
    _j("sour", "ce"),
    _j("ur", "l"),
    _j("te", "xt"),
    _j("d", "sn"),
    _j("ta", "ble"),
    _j("to", "ken"),
    _j("wal", "let"),
    _j("ord", "er"),
    _j("tra", "de"),
    _j("li", "ve"),
    _j("siz", "ing"),
    _j("recomm", "endation"),
    "://",
    "http",
    "www.",
    "postgres://",
    "mysql://",
    "jdbc:",
)

__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_EVIDENCE_QUORUM_TAIL_REPORT_CONFIG_VERSION",
    "ResearchEventResolutionEvidenceQuorumTailConfig",
    "ResearchEventResolutionEvidenceQuorumTailObservation",
    "ResearchEventResolutionEvidenceQuorumTailRow",
    "ResearchEventResolutionEvidenceQuorumTailReport",
    "build_research_event_resolution_evidence_quorum_tail_report",
    "research_event_resolution_evidence_quorum_tail_report_digest",
    "research_event_resolution_evidence_quorum_tail_report_payload",
    "validate_research_event_resolution_evidence_quorum_tail_report_digest",
    "validate_research_event_resolution_evidence_quorum_tail_report_payload",
)


@dataclass(frozen=True)
class ResearchEventResolutionEvidenceQuorumTailConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_EVIDENCE_QUORUM_TAIL_REPORT_CONFIG_VERSION
    )
    pass_quorum_score_floor: Decimal = Decimal("0.750000")
    block_quorum_score_floor: Decimal = Decimal("0.500000")
    pass_independent_family_count: Decimal = Decimal("2.000000")
    watch_independent_family_count: Decimal = Decimal("1.000000")
    watch_opposition_pressure: Decimal = Decimal("0.250000")
    block_opposition_pressure: Decimal = Decimal("0.500000")
    watch_stale_pressure: Decimal = Decimal("0.250000")
    block_stale_pressure: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionEvidenceQuorumTailConfig:
            raise TypeError(
                "ResearchEventResolutionEvidenceQuorumTailConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionEvidenceQuorumTailConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_EVIDENCE_QUORUM_TAIL_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_quorum_score_floor",
            "block_quorum_score_floor",
            "watch_opposition_pressure",
            "block_opposition_pressure",
            "watch_stale_pressure",
            "block_stale_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_quorum_score_floor >= self.pass_quorum_score_floor:
            raise ValueError(
                "block_quorum_score_floor must be less than "
                "pass_quorum_score_floor",
            )
        object.__setattr__(
            self,
            "pass_independent_family_count",
            _require_positive_decimal(
                "pass_independent_family_count",
                self.pass_independent_family_count,
            ),
        )
        object.__setattr__(
            self,
            "watch_independent_family_count",
            _require_positive_decimal(
                "watch_independent_family_count",
                self.watch_independent_family_count,
            ),
        )
        if self.watch_independent_family_count > self.pass_independent_family_count:
            raise ValueError(
                "watch_independent_family_count must not exceed "
                "pass_independent_family_count",
            )
        if self.watch_opposition_pressure > self.block_opposition_pressure:
            raise ValueError(
                "watch_opposition_pressure must not exceed "
                "block_opposition_pressure",
            )
        if self.watch_stale_pressure > self.block_stale_pressure:
            raise ValueError(
                "watch_stale_pressure must not exceed block_stale_pressure",
            )
        _require_hard_flags("config", self)
        _reject_bad_public("config", _payload_value(self))


@dataclass(frozen=True)
class ResearchEventResolutionEvidenceQuorumTailObservation:
    event_digest: str
    resolution_digest: str
    evidence_packet_digest: str
    evidence_count: Decimal
    independent_family_count: Decimal
    affirming_evidence_count: Decimal
    opposing_evidence_count: Decimal
    stale_evidence_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionEvidenceQuorumTailObservation:
            raise TypeError(
                "ResearchEventResolutionEvidenceQuorumTailObservation does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventResolutionEvidenceQuorumTailObservation,
            "observation",
        )
        for field_name in (
            "event_digest",
            "resolution_digest",
            "evidence_packet_digest",
        ):
            _require_sha256(field_name, getattr(self, field_name))
        for field_name in (
            "evidence_count",
            "independent_family_count",
            "affirming_evidence_count",
            "opposing_evidence_count",
            "stale_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.affirming_evidence_count > self.evidence_count:
            raise ValueError("affirming_evidence_count must not exceed evidence_count")
        if self.opposing_evidence_count > self.evidence_count:
            raise ValueError("opposing_evidence_count must not exceed evidence_count")
        if self.stale_evidence_count > self.evidence_count:
            raise ValueError("stale_evidence_count must not exceed evidence_count")
        if self.affirming_evidence_count + self.opposing_evidence_count > self.evidence_count:
            raise ValueError(
                "affirming_evidence_count plus opposing_evidence_count must not "
                "exceed evidence_count",
            )
        _require_hard_flags("observation", self)
        _reject_bad_public("observation", _payload_value(self))


@dataclass(frozen=True)
class ResearchEventResolutionEvidenceQuorumTailRow:
    rank: Decimal
    event_digest: str
    resolution_digest: str
    evidence_packet_digest: str
    evidence_count: Decimal
    independent_family_count: Decimal
    affirming_evidence_count: Decimal
    opposing_evidence_count: Decimal
    stale_evidence_count: Decimal
    quorum_score: Decimal
    independence_score: Decimal
    opposition_pressure: Decimal
    stale_pressure: Decimal
    tail_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionEvidenceQuorumTailRow:
            raise TypeError(
                "ResearchEventResolutionEvidenceQuorumTailRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionEvidenceQuorumTailRow, "row")
        object.__setattr__(self, "rank", _require_positive_decimal("rank", self.rank))
        for field_name in (
            "event_digest",
            "resolution_digest",
            "evidence_packet_digest",
        ):
            _require_sha256(field_name, getattr(self, field_name))
        for field_name in (
            "evidence_count",
            "independent_family_count",
            "affirming_evidence_count",
            "opposing_evidence_count",
            "stale_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "quorum_score",
            "independence_score",
            "opposition_pressure",
            "stale_pressure",
            "tail_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.affirming_evidence_count > self.evidence_count:
            raise ValueError("affirming_evidence_count must not exceed evidence_count")
        if self.opposing_evidence_count > self.evidence_count:
            raise ValueError("opposing_evidence_count must not exceed evidence_count")
        if self.stale_evidence_count > self.evidence_count:
            raise ValueError("stale_evidence_count must not exceed evidence_count")
        _require_status(self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        if self.status != _row_status_from_reasons(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_bad_public("row", _payload_value(self))


@dataclass(frozen=True)
class ResearchEventResolutionEvidenceQuorumTailReport:
    generated_at: datetime
    config_version: str
    status: str
    event_count: Decimal
    pass_event_count: Decimal
    watch_event_count: Decimal
    block_event_count: Decimal
    quorum_tail_event_count: Decimal
    maximum_tail_risk_score: Decimal
    average_quorum_score: Decimal
    average_tail_risk_score: Decimal
    rows: tuple[ResearchEventResolutionEvidenceQuorumTailRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionEvidenceQuorumTailReport:
            raise TypeError(
                "ResearchEventResolutionEvidenceQuorumTailReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventResolutionEvidenceQuorumTailReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        _require_status(self.status)
        for field_name in (
            "event_count",
            "pass_event_count",
            "watch_event_count",
            "block_event_count",
            "quorum_tail_event_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "maximum_tail_risk_score",
            "average_quorum_score",
            "average_tail_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_sha256("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_bad_public("report", _payload_value(self))
        _require_matching_digest(_payload_value(self))

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_resolution_evidence_quorum_tail_report_payload(self)


def build_research_event_resolution_evidence_quorum_tail_report(
    observations: Iterable[ResearchEventResolutionEvidenceQuorumTailObservation],
    *,
    config: ResearchEventResolutionEvidenceQuorumTailConfig | None = None,
    generated_at: datetime,
) -> ResearchEventResolutionEvidenceQuorumTailReport:
    cfg = config or ResearchEventResolutionEvidenceQuorumTailConfig()
    _require_exact_type(cfg, ResearchEventResolutionEvidenceQuorumTailConfig, "config")
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    rows = tuple(
        _row_for_observation(observation=item, config=cfg)
        for item in _sorted_observations(normalized, cfg)
    )
    ranked_rows = tuple(
        _ranked_row(index=index, row=row) for index, row in enumerate(rows, start=1)
    )
    values: dict[str, Any] = {
        "generated_at": generated_at_utc,
        "config_version": cfg.config_version,
        "status": _report_status(ranked_rows),
        "event_count": _count_decimal(len(ranked_rows)),
        "pass_event_count": _status_count(ranked_rows, STATUS_PASS),
        "watch_event_count": _status_count(ranked_rows, STATUS_WATCH),
        "block_event_count": _status_count(ranked_rows, STATUS_BLOCK),
        "quorum_tail_event_count": _tail_count(ranked_rows),
        "maximum_tail_risk_score": max(
            (row.tail_risk_score for row in ranked_rows),
            default=ZERO,
        ),
        "average_quorum_score": _average(row.quorum_score for row in ranked_rows),
        "average_tail_risk_score": _average(
            (row.tail_risk_score for row in ranked_rows),
        ),
        "rows": ranked_rows,
        "reason_codes": _report_reason_codes(ranked_rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    payload = _payload_value(values)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    values["derived_validation_digest"] = _derived_validation_digest(payload)
    return ResearchEventResolutionEvidenceQuorumTailReport(**values)


def research_event_resolution_evidence_quorum_tail_report_digest(
    report: ResearchEventResolutionEvidenceQuorumTailReport,
) -> str:
    _require_exact_type(
        report,
        ResearchEventResolutionEvidenceQuorumTailReport,
        "report",
    )
    _require_hard_flags("report", report)
    return _derived_validation_digest(_payload_value(report))


def validate_research_event_resolution_evidence_quorum_tail_report_digest(
    report: ResearchEventResolutionEvidenceQuorumTailReport,
) -> bool:
    _require_exact_type(
        report,
        ResearchEventResolutionEvidenceQuorumTailReport,
        "report",
    )
    _require_hard_flags("report", report)
    _require_matching_digest(_payload_value(report))
    return True


def research_event_resolution_evidence_quorum_tail_report_payload(
    report: ResearchEventResolutionEvidenceQuorumTailReport,
) -> dict[str, Any]:
    _require_exact_type(
        report,
        ResearchEventResolutionEvidenceQuorumTailReport,
        "report",
    )
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_bad_public("payload", payload)
    _require_matching_digest(payload)
    return payload


def validate_research_event_resolution_evidence_quorum_tail_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_bad_public("payload", payload)
    _require_payload_statuses(payload)
    _require_payload_hard_flags(payload)
    _require_matching_digest(payload)
    return True


def _row_for_observation(
    *,
    observation: ResearchEventResolutionEvidenceQuorumTailObservation,
    config: ResearchEventResolutionEvidenceQuorumTailConfig,
) -> ResearchEventResolutionEvidenceQuorumTailRow:
    quorum_score = _pressure(observation.affirming_evidence_count, observation.evidence_count)
    independence_score = _clamp_ratio(
        observation.independent_family_count / config.pass_independent_family_count,
    )
    opposition_pressure = _pressure(
        observation.opposing_evidence_count,
        observation.evidence_count,
    )
    stale_pressure = _pressure(observation.stale_evidence_count, observation.evidence_count)
    reason_codes = _row_reason_codes(
        quorum_score=quorum_score,
        independent_family_count=observation.independent_family_count,
        opposition_pressure=opposition_pressure,
        stale_pressure=stale_pressure,
        config=config,
    )
    return ResearchEventResolutionEvidenceQuorumTailRow(
        rank=ONE,
        event_digest=observation.event_digest,
        resolution_digest=observation.resolution_digest,
        evidence_packet_digest=observation.evidence_packet_digest,
        evidence_count=observation.evidence_count,
        independent_family_count=observation.independent_family_count,
        affirming_evidence_count=observation.affirming_evidence_count,
        opposing_evidence_count=observation.opposing_evidence_count,
        stale_evidence_count=observation.stale_evidence_count,
        quorum_score=quorum_score,
        independence_score=independence_score,
        opposition_pressure=opposition_pressure,
        stale_pressure=stale_pressure,
        tail_risk_score=_tail_risk_score(reason_codes),
        status=_row_status_from_reasons(reason_codes),
        reason_codes=reason_codes,
    )


def _ranked_row(
    *,
    index: int,
    row: ResearchEventResolutionEvidenceQuorumTailRow,
) -> ResearchEventResolutionEvidenceQuorumTailRow:
    return ResearchEventResolutionEvidenceQuorumTailRow(
        rank=_count_decimal(index),
        event_digest=row.event_digest,
        resolution_digest=row.resolution_digest,
        evidence_packet_digest=row.evidence_packet_digest,
        evidence_count=row.evidence_count,
        independent_family_count=row.independent_family_count,
        affirming_evidence_count=row.affirming_evidence_count,
        opposing_evidence_count=row.opposing_evidence_count,
        stale_evidence_count=row.stale_evidence_count,
        quorum_score=row.quorum_score,
        independence_score=row.independence_score,
        opposition_pressure=row.opposition_pressure,
        stale_pressure=row.stale_pressure,
        tail_risk_score=row.tail_risk_score,
        status=row.status,
        reason_codes=row.reason_codes,
    )


def _row_reason_codes(
    *,
    quorum_score: Decimal,
    independent_family_count: Decimal,
    opposition_pressure: Decimal,
    stale_pressure: Decimal,
    config: ResearchEventResolutionEvidenceQuorumTailConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if quorum_score < config.block_quorum_score_floor:
        reasons.append(LOW_QUORUM_BLOCK_REASON)
    elif quorum_score < config.pass_quorum_score_floor:
        reasons.append(LOW_QUORUM_WATCH_REASON)
    if independent_family_count < config.watch_independent_family_count:
        reasons.append(LOW_FAMILY_BLOCK_REASON)
    elif independent_family_count < config.pass_independent_family_count:
        reasons.append(LOW_FAMILY_WATCH_REASON)
    if opposition_pressure >= config.block_opposition_pressure:
        reasons.append(OPPOSITION_BLOCK_REASON)
    elif opposition_pressure >= config.watch_opposition_pressure:
        reasons.append(OPPOSITION_WATCH_REASON)
    if stale_pressure >= config.block_stale_pressure:
        reasons.append(STALE_BLOCK_REASON)
    elif stale_pressure >= config.watch_stale_pressure:
        reasons.append(STALE_WATCH_REASON)
    if any(item.endswith("_block") for item in reasons):
        return (BLOCK_REASON, *tuple(reasons))
    if reasons:
        return (WATCH_REASON, *tuple(reasons))
    return (PASS_REASON,)


def _tail_risk_score(reason_codes: tuple[str, ...]) -> Decimal:
    if reason_codes[0] == BLOCK_REASON:
        return ONE
    if reason_codes[0] == WATCH_REASON:
        return Decimal("0.500000")
    return ZERO


def _pressure(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _clamp_ratio(numerator / denominator)


def _normalize_observations(
    observations: Iterable[ResearchEventResolutionEvidenceQuorumTailObservation],
) -> tuple[ResearchEventResolutionEvidenceQuorumTailObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable of observations")
    try:
        normalized = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable of observations") from exc
    for item in normalized:
        _require_exact_type(
            item,
            ResearchEventResolutionEvidenceQuorumTailObservation,
            "observation",
        )
        _require_hard_flags("observation", item)
    keys = tuple(
        (item.event_digest, item.resolution_digest, item.evidence_packet_digest)
        for item in normalized
    )
    if len(set(keys)) != len(keys):
        raise ValueError("observations must not contain duplicate digests")
    return normalized


def _sorted_observations(
    observations: tuple[ResearchEventResolutionEvidenceQuorumTailObservation, ...],
    config: ResearchEventResolutionEvidenceQuorumTailConfig,
) -> tuple[ResearchEventResolutionEvidenceQuorumTailObservation, ...]:
    return tuple(
        sorted(
            observations,
            key=lambda item: _row_sort_key(_row_for_observation(observation=item, config=config)),
        ),
    )


def _row_sort_key(row: ResearchEventResolutionEvidenceQuorumTailRow) -> tuple[object, ...]:
    return (
        _status_rank(row.status),
        -row.tail_risk_score,
        -row.quorum_score,
        row.event_digest,
        row.resolution_digest,
        row.evidence_packet_digest,
    )


def _require_rows(
    rows: tuple[ResearchEventResolutionEvidenceQuorumTailRow, ...],
) -> tuple[ResearchEventResolutionEvidenceQuorumTailRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for index, row in enumerate(rows, start=1):
        _require_exact_type(row, ResearchEventResolutionEvidenceQuorumTailRow, "row")
        _require_hard_flags("row", row)
        if row.rank != _count_decimal(index):
            raise ValueError("row ranks must be sequential")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and tail risk")
    return rows


def _row_status_from_reasons(reason_codes: tuple[str, ...]) -> str:
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if reason_codes[0] == BLOCK_REASON:
        return STATUS_BLOCK
    if reason_codes[0] == WATCH_REASON:
        return STATUS_WATCH
    if reason_codes[0] == PASS_REASON:
        return STATUS_PASS
    raise ValueError("reason_codes must start with pass, watch, or block reason")


def _status_rank(status: str) -> int:
    if status == STATUS_BLOCK:
        return 0
    if status == STATUS_WATCH:
        return 1
    if status == STATUS_PASS:
        return 2
    raise ValueError("status must be one of pass, watch, block")


def _status_count(
    rows: tuple[ResearchEventResolutionEvidenceQuorumTailRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _tail_count(rows: tuple[ResearchEventResolutionEvidenceQuorumTailRow, ...]) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status != STATUS_PASS))


def _report_status(rows: tuple[ResearchEventResolutionEvidenceQuorumTailRow, ...]) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionEvidenceQuorumTailRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    present = {row.reason_codes[0] for row in rows}
    return tuple(code for code in (BLOCK_REASON, WATCH_REASON, PASS_REASON) if code in present)


def _average(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _six(sum(items, ZERO) / Decimal(len(items)))


def _validate_report(report: ResearchEventResolutionEvidenceQuorumTailReport) -> None:
    rows = report.rows
    _require_decimal_equal("event_count", report.event_count, _count_decimal(len(rows)))
    _require_decimal_equal(
        "pass_event_count",
        report.pass_event_count,
        _status_count(rows, STATUS_PASS),
    )
    _require_decimal_equal(
        "watch_event_count",
        report.watch_event_count,
        _status_count(rows, STATUS_WATCH),
    )
    _require_decimal_equal(
        "block_event_count",
        report.block_event_count,
        _status_count(rows, STATUS_BLOCK),
    )
    _require_decimal_equal(
        "quorum_tail_event_count",
        report.quorum_tail_event_count,
        _tail_count(rows),
    )
    _require_decimal_equal(
        "maximum_tail_risk_score",
        report.maximum_tail_risk_score,
        max((row.tail_risk_score for row in rows), default=ZERO),
    )
    _require_decimal_equal(
        "average_quorum_score",
        report.average_quorum_score,
        _average(row.quorum_score for row in rows),
    )
    _require_decimal_equal(
        "average_tail_risk_score",
        report.average_tail_risk_score,
        _average(row.tail_risk_score for row in rows),
    )
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _require_decimal_equal(field_name: str, actual: Decimal, expected: Decimal) -> None:
    if actual != expected:
        raise ValueError(f"{field_name} must match rows")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _six(value)


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _count_decimal(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _six(Decimal(value))


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(ONE, max(ZERO, _six(value)))


def _six(value: Decimal) -> Decimal:
    return value.quantize(SIX, rounding=ROUND_HALF_UP)


def _require_status(value: str) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError("status must be one of pass, watch, block")


def _require_reason_codes(
    field_name: str,
    value: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a nonempty tuple")
    allowed_set = frozenset(allowed)
    for item in value:
        if type(item) is not str or item not in allowed_set:
            raise ValueError(f"{field_name} contains an unsupported reason code")
    if tuple(dict.fromkeys(value)) != value:
        raise ValueError(f"{field_name} must not contain duplicates")
    return value


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a sha256 hex digest") from exc
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a nonempty string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in BAD_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public surface")
    return value


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"payload {field_name} must be True")


def _require_payload_statuses(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "status":
                _require_status(item)
            _require_payload_statuses(item)
        return
    if isinstance(value, list):
        for item in value:
            _require_payload_statuses(item)


def _payload_value(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if type(value) is Decimal:
        return str(_six(value))
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("public payload contains unsupported value")


def _reject_bad_public(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} public payload contains non-string key")
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in BAD_PUBLIC_FRAGMENTS):
                raise ValueError(f"{label} contains unsafe public surface")
            _reject_bad_public(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_bad_public(label, item)
        return
    if type(value) in (Decimal, int, float):
        raise ValueError(f"{label} public payload must not contain numeric objects")
    if type(value) is str:
        lowered_value = value.lower()
        if any(fragment in lowered_value for fragment in BAD_PUBLIC_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe public surface")


def _derived_validation_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _require_matching_digest(payload: object) -> None:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    digest = payload.get("derived_validation_digest")
    _require_sha256("derived_validation_digest", digest)
    expected = _derived_validation_digest(payload)
    if digest != expected:
        raise ValueError("derived_validation_digest does not match public payload")
