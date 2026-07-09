"""Report-only source information recency decay scoring."""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_INFORMATION_RECENCY_DECAY_REPORT_CONFIG_VERSION = (
    "research-source-information-recency-decay-report-v1"
)

_COUNT_QUANTUM = Decimal("1")
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_FIVE = Decimal("5.000000")
_DEFAULT_MAX_EVIDENCE_AGE_MINUTES = Decimal("180.000000")
_DEFAULT_STALE_EVIDENCE_AGE_MINUTES = Decimal("90.000000")
_DEFAULT_CORROBORATION_PASS_COUNT = Decimal("3")
_DEFAULT_DEADLINE_PROXIMITY_WINDOW_MINUTES = Decimal("60.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_HEX_CHARS = frozenset("0123456789abcdef")
_STATUSES = ("pass", "watch", "block")
_STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_BLOCK_REASONS = frozenset(
    (
        "evidence_age_block",
        "authority_weight_weak",
        "contradiction_pressure_block",
        "deadline_proximity_block",
    ),
)
_PASS_REASONS = frozenset(("source_information_recency_decay_pass",))
_REASON_PRIORITY = (
    "evidence_age_block",
    "evidence_age_stale",
    "authority_weight_weak",
    "corroboration_gap",
    "contradiction_pressure_block",
    "contradiction_pressure_watch",
    "deadline_proximity_block",
    "deadline_proximity_watch",
    "source_information_recency_decay_pass",
    "source_information_recency_decay_empty",
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "url",
    "source_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
    "://",
    "http",
    "www.",
)


@dataclass(frozen=True)
class ResearchSourceInformationRecencyDecayConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_INFORMATION_RECENCY_DECAY_REPORT_CONFIG_VERSION
    )
    max_evidence_age_minutes: Decimal = _DEFAULT_MAX_EVIDENCE_AGE_MINUTES
    stale_evidence_age_minutes: Decimal = _DEFAULT_STALE_EVIDENCE_AGE_MINUTES
    corroboration_pass_count: Decimal = _DEFAULT_CORROBORATION_PASS_COUNT
    weak_authority_threshold: Decimal = Decimal("0.500000")
    contradiction_watch_threshold: Decimal = Decimal("0.250000")
    contradiction_block_threshold: Decimal = Decimal("0.600000")
    deadline_proximity_window_minutes: Decimal = (
        _DEFAULT_DEADLINE_PROXIMITY_WINDOW_MINUTES
    )
    deadline_block_minutes: Decimal = Decimal("30.000000")
    pass_decay_score_min: Decimal = Decimal("0.750000")
    watch_decay_score_min: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceInformationRecencyDecayConfig:
            raise TypeError(
                "ResearchSourceInformationRecencyDecayConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceInformationRecencyDecayConfig:
            raise ValueError(
                "config must be exactly ResearchSourceInformationRecencyDecayConfig",
            )
        _require_config_version(self.config_version)
        for field_name in (
            "max_evidence_age_minutes",
            "stale_evidence_age_minutes",
            "deadline_proximity_window_minutes",
            "deadline_block_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "corroboration_pass_count",
            _normalize_positive_count(
                "corroboration_pass_count",
                self.corroboration_pass_count,
            ),
        )
        for field_name in (
            "weak_authority_threshold",
            "contradiction_watch_threshold",
            "contradiction_block_threshold",
            "pass_decay_score_min",
            "watch_decay_score_min",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_evidence_age_minutes >= self.max_evidence_age_minutes:
            raise ValueError(
                "stale_evidence_age_minutes must be below max_evidence_age_minutes",
            )
        if self.contradiction_watch_threshold > self.contradiction_block_threshold:
            raise ValueError(
                "contradiction_watch_threshold must not exceed "
                "contradiction_block_threshold",
            )
        if self.watch_decay_score_min >= self.pass_decay_score_min:
            raise ValueError("watch_decay_score_min must be below pass_decay_score_min")
        if self.deadline_block_minutes >= self.deadline_proximity_window_minutes:
            raise ValueError(
                "deadline_block_minutes must be below "
                "deadline_proximity_window_minutes",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceInformationRecencyEvidence:
    research_key: str
    evidence_family: str
    evidence_age_minutes: Decimal
    authority_score: Decimal
    corroboration_count: Decimal
    contradiction_pressure: Decimal
    minutes_until_deadline: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceInformationRecencyEvidence:
            raise TypeError(
                "ResearchSourceInformationRecencyEvidence does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceInformationRecencyEvidence:
            raise ValueError(
                "evidence must be exactly ResearchSourceInformationRecencyEvidence",
            )
        _require_public_identifier("research_key", self.research_key)
        _require_public_identifier("evidence_family", self.evidence_family)
        for field_name in ("evidence_age_minutes", "minutes_until_deadline"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "corroboration_count",
            _normalize_nonnegative_count(
                "corroboration_count",
                self.corroboration_count,
            ),
        )
        for field_name in ("authority_score", "contradiction_pressure"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("evidence", self)
        _reject_unsafe_public_payload("evidence", self)


@dataclass(frozen=True)
class ResearchSourceInformationRecencyDecayRow:
    research_key: str
    evidence_family: str
    evidence_age_minutes: Decimal
    authority_score: Decimal
    corroboration_count: Decimal
    contradiction_pressure: Decimal
    minutes_until_deadline: Decimal
    age_decay_score: Decimal
    corroboration_score: Decimal
    contradiction_score: Decimal
    deadline_proximity_score: Decimal
    evidence_decay_score: Decimal
    staleness_pressure: Decimal
    decay_status: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceInformationRecencyDecayRow:
            raise TypeError(
                "ResearchSourceInformationRecencyDecayRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceInformationRecencyDecayRow:
            raise ValueError("row must be exactly ResearchSourceInformationRecencyDecayRow")
        _require_public_identifier("research_key", self.research_key)
        _require_public_identifier("evidence_family", self.evidence_family)
        for field_name in ("evidence_age_minutes", "minutes_until_deadline"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "corroboration_count",
            _normalize_nonnegative_count(
                "corroboration_count",
                self.corroboration_count,
            ),
        )
        for field_name in (
            "authority_score",
            "contradiction_pressure",
            "age_decay_score",
            "corroboration_score",
            "contradiction_score",
            "deadline_proximity_score",
            "evidence_decay_score",
            "staleness_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("decay_status", self.decay_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _require_digest("validation_digest", self.validation_digest)
        _validate_row(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceInformationRecencyDecayReport:
    generated_at: datetime
    config_version: str
    report_status: str
    evidence_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    min_decay_score: Decimal | None
    max_staleness_pressure: Decimal
    rows: tuple[ResearchSourceInformationRecencyDecayRow, ...]
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceInformationRecencyDecayReport:
            raise TypeError(
                "ResearchSourceInformationRecencyDecayReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceInformationRecencyDecayReport:
            raise ValueError(
                "report must be exactly ResearchSourceInformationRecencyDecayReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_config_version(self.config_version)
        _require_status("report_status", self.report_status)
        for field_name in ("evidence_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.min_decay_score is not None:
            object.__setattr__(
                self,
                "min_decay_score",
                _normalize_unit_decimal("min_decay_score", self.min_decay_score),
            )
        object.__setattr__(
            self,
            "max_staleness_pressure",
            _normalize_unit_decimal(
                "max_staleness_pressure",
                self.max_staleness_pressure,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _require_digest("validation_digest", self.validation_digest)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_information_recency_decay_report_payload(self)


def build_research_source_information_recency_decay_report(
    evidence_items: Iterable[ResearchSourceInformationRecencyEvidence],
    *,
    generated_at: datetime,
    config: ResearchSourceInformationRecencyDecayConfig | None = None,
) -> ResearchSourceInformationRecencyDecayReport:
    if config is None:
        config = ResearchSourceInformationRecencyDecayConfig()
    if type(config) is not ResearchSourceInformationRecencyDecayConfig:
        raise ValueError("config must be a ResearchSourceInformationRecencyDecayConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_evidence = _normalize_evidence_items(evidence_items)
    rows = _normalize_rows(tuple(_row_for_evidence(item, config) for item in normalized_evidence))
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "report_status": _report_status(rows),
        "evidence_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "min_decay_score": (
            None if not rows else min(row.evidence_decay_score for row in rows)
        ),
        "max_staleness_pressure": max(
            (row.staleness_pressure for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceInformationRecencyDecayReport(
        **report_values,
        validation_digest=_validation_digest(report_values),
    )


def research_source_information_recency_decay_report_payload(
    report: ResearchSourceInformationRecencyDecayReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSourceInformationRecencyDecayReport:
        _require_hard_flags("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchSourceInformationRecencyDecayReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_public_payload_digest(payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_for_evidence(
    evidence: ResearchSourceInformationRecencyEvidence,
    config: ResearchSourceInformationRecencyDecayConfig,
) -> ResearchSourceInformationRecencyDecayRow:
    age_decay_score = _age_decay_score(evidence.evidence_age_minutes, config)
    corroboration_score = _capped_ratio(
        evidence.corroboration_count,
        config.corroboration_pass_count,
    )
    contradiction_score = _quantize(_ONE - evidence.contradiction_pressure)
    deadline_proximity_score = _deadline_proximity_score(
        evidence.minutes_until_deadline,
        config,
    )
    component_values = (
        age_decay_score,
        evidence.authority_score,
        corroboration_score,
        contradiction_score,
        deadline_proximity_score,
    )
    evidence_decay_score = _evidence_decay_score(component_values)
    reason_codes = _row_reason_codes(
        evidence,
        evidence_decay_score=evidence_decay_score,
        config=config,
    )
    row_values = {
        "research_key": evidence.research_key,
        "evidence_family": evidence.evidence_family,
        "evidence_age_minutes": evidence.evidence_age_minutes,
        "authority_score": evidence.authority_score,
        "corroboration_count": evidence.corroboration_count,
        "contradiction_pressure": evidence.contradiction_pressure,
        "minutes_until_deadline": evidence.minutes_until_deadline,
        "age_decay_score": age_decay_score,
        "corroboration_score": corroboration_score,
        "contradiction_score": contradiction_score,
        "deadline_proximity_score": deadline_proximity_score,
        "evidence_decay_score": evidence_decay_score,
        "staleness_pressure": _quantize(_ONE - age_decay_score),
        "decay_status": _status_from_reason_codes(reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceInformationRecencyDecayRow(
        **row_values,
        validation_digest=_validation_digest(row_values),
    )


def _age_decay_score(
    age_minutes: Decimal,
    config: ResearchSourceInformationRecencyDecayConfig,
) -> Decimal:
    return _clamp_ratio(_ONE - _ratio(age_minutes, config.max_evidence_age_minutes))


def _deadline_proximity_score(
    minutes_until_deadline: Decimal,
    config: ResearchSourceInformationRecencyDecayConfig,
) -> Decimal:
    return _capped_ratio(minutes_until_deadline, config.deadline_proximity_window_minutes)


def _evidence_decay_score(component_values: tuple[Decimal, ...]) -> Decimal:
    return _ratio(_sum_decimal(component_values), _FIVE)


def _row_reason_codes(
    evidence: ResearchSourceInformationRecencyEvidence,
    *,
    evidence_decay_score: Decimal,
    config: ResearchSourceInformationRecencyDecayConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if evidence.evidence_age_minutes > config.max_evidence_age_minutes:
        reason_codes.append("evidence_age_block")
    elif evidence.evidence_age_minutes > config.stale_evidence_age_minutes:
        reason_codes.append("evidence_age_stale")
    if evidence.authority_score < config.weak_authority_threshold:
        reason_codes.append("authority_weight_weak")
    if evidence.corroboration_count < config.corroboration_pass_count:
        reason_codes.append("corroboration_gap")
    if evidence.contradiction_pressure >= config.contradiction_block_threshold:
        reason_codes.append("contradiction_pressure_block")
    elif evidence.contradiction_pressure >= config.contradiction_watch_threshold:
        reason_codes.append("contradiction_pressure_watch")
    if evidence.minutes_until_deadline <= config.deadline_block_minutes:
        reason_codes.append("deadline_proximity_block")
    elif evidence.minutes_until_deadline <= config.deadline_proximity_window_minutes:
        reason_codes.append("deadline_proximity_watch")
    if not reason_codes and evidence_decay_score >= config.pass_decay_score_min:
        reason_codes.append("source_information_recency_decay_pass")
    if not reason_codes:
        reason_codes.append("evidence_age_stale")
    return _normalize_row_reason_codes("reason_codes", tuple(reason_codes))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason in _BLOCK_REASONS for reason in reason_codes):
        return "block"
    if reason_codes == ("source_information_recency_decay_pass",):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchSourceInformationRecencyDecayRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.decay_status == "block" for row in rows):
        return "block"
    if any(row.decay_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceInformationRecencyDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("source_information_recency_decay_empty",)
    return _normalize_report_reason_codes(
        "reason_codes",
        tuple(reason for row in rows for reason in row.reason_codes),
    )


def _status_count(
    rows: tuple[ResearchSourceInformationRecencyDecayRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.decay_status == status))


def _normalize_evidence_items(
    items: Iterable[ResearchSourceInformationRecencyEvidence],
) -> tuple[ResearchSourceInformationRecencyEvidence, ...]:
    if isinstance(items, (str, bytes)):
        raise ValueError("evidence_items must be an iterable")
    try:
        normalized = tuple(items)
    except TypeError as exc:
        raise ValueError("evidence_items must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for item in normalized:
        if type(item) is not ResearchSourceInformationRecencyEvidence:
            raise ValueError(
                "evidence_items must contain ResearchSourceInformationRecencyEvidence",
            )
        _require_hard_flags("evidence", item)
        key = (item.research_key, item.evidence_family)
        if key in seen:
            raise ValueError("research_key and evidence_family values must be unique")
        seen.add(key)
    return tuple(sorted(normalized, key=lambda item: (item.research_key, item.evidence_family)))


def _normalize_rows(
    rows: Sequence[ResearchSourceInformationRecencyDecayRow],
) -> tuple[ResearchSourceInformationRecencyDecayRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchSourceInformationRecencyDecayRow] = []
    for row in rows:
        if type(row) is not ResearchSourceInformationRecencyDecayRow:
            raise ValueError("rows must contain ResearchSourceInformationRecencyDecayRow")
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _row_sort_key(row: ResearchSourceInformationRecencyDecayRow) -> tuple[int, Decimal, str, str]:
    return (
        _STATUS_WEIGHT[row.decay_status],
        row.evidence_decay_score,
        row.research_key,
        row.evidence_family,
    )


def _validate_row(row: ResearchSourceInformationRecencyDecayRow) -> None:
    expected_score = _evidence_decay_score(
        (
            row.age_decay_score,
            row.authority_score,
            row.corroboration_score,
            row.contradiction_score,
            row.deadline_proximity_score,
        ),
    )
    if row.evidence_decay_score != expected_score:
        raise ValueError("evidence_decay_score must match component scores")
    if row.staleness_pressure != _quantize(_ONE - row.age_decay_score):
        raise ValueError("staleness_pressure must match age_decay_score")
    if row.decay_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("decay_status must match reason_codes")
    if row.validation_digest != _validation_digest(_row_digest_values(row)):
        raise ValueError("validation_digest must match row payload")


def _validate_report(report: ResearchSourceInformationRecencyDecayReport) -> None:
    if report.evidence_count != _count(len(report.rows)):
        raise ValueError("evidence_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    expected_min = None if not report.rows else min(row.evidence_decay_score for row in report.rows)
    if report.min_decay_score != expected_min:
        raise ValueError("min_decay_score must match rows")
    expected_max = max((row.staleness_pressure for row in report.rows), default=_ZERO)
    if report.max_staleness_pressure != expected_max:
        raise ValueError("max_staleness_pressure must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.validation_digest != _validation_digest(_report_digest_values(report)):
        raise ValueError("validation_digest must match report payload")


def _row_digest_values(row: ResearchSourceInformationRecencyDecayRow) -> dict[str, Any]:
    return {
        "research_key": row.research_key,
        "evidence_family": row.evidence_family,
        "evidence_age_minutes": row.evidence_age_minutes,
        "authority_score": row.authority_score,
        "corroboration_count": row.corroboration_count,
        "contradiction_pressure": row.contradiction_pressure,
        "minutes_until_deadline": row.minutes_until_deadline,
        "age_decay_score": row.age_decay_score,
        "corroboration_score": row.corroboration_score,
        "contradiction_score": row.contradiction_score,
        "deadline_proximity_score": row.deadline_proximity_score,
        "evidence_decay_score": row.evidence_decay_score,
        "staleness_pressure": row.staleness_pressure,
        "decay_status": row.decay_status,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_digest_values(report: ResearchSourceInformationRecencyDecayReport) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "report_status": report.report_status,
        "evidence_count": report.evidence_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "min_decay_score": report.min_decay_score,
        "max_staleness_pressure": report.max_staleness_pressure,
        "rows": report.rows,
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _normalize_row_reason_codes(name: str, values: object) -> tuple[str, ...]:
    codes = _normalize_reason_codes(name, values)
    if not codes:
        raise ValueError(f"{name} must not be empty")
    if "source_information_recency_decay_pass" in codes and len(codes) != 1:
        raise ValueError(f"{name} pass reason must stand alone")
    if codes != ("source_information_recency_decay_pass",) and any(
        code in _PASS_REASONS for code in codes
    ):
        raise ValueError(f"{name} pass reason must stand alone")
    if "source_information_recency_decay_empty" in codes:
        raise ValueError(f"{name} empty reason is report-only")
    return codes


def _normalize_report_reason_codes(name: str, values: object) -> tuple[str, ...]:
    codes = _normalize_reason_codes(name, values)
    if not codes:
        raise ValueError(f"{name} must not be empty")
    if codes == ("source_information_recency_decay_empty",):
        return codes
    if "source_information_recency_decay_empty" in codes:
        raise ValueError(f"{name} empty reason must stand alone")
    return codes


def _normalize_reason_codes(name: str, values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be an iterable")
    try:
        codes = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable") from exc
    for code in codes:
        _require_public_identifier(name, code)
        if code.lower() != code:
            raise ValueError(f"{name} must contain lowercase snake case values")
    return tuple(sorted(dict.fromkeys(codes), key=_reason_sort_key))


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    if reason_code in _REASON_PRIORITY:
        return (_REASON_PRIORITY.index(reason_code), reason_code)
    return (len(_REASON_PRIORITY), reason_code)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = _ZERO
    for value in values:
        total += _normalize_decimal("sum value", value)
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    denominator = _normalize_decimal("denominator", denominator)
    if denominator <= _ZERO:
        raise ValueError("denominator must be positive")
    numerator = _normalize_decimal("numerator", numerator)
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    value = _ratio(numerator, denominator)
    if value > _ONE:
        return _ONE
    return value


def _clamp_ratio(value: Decimal) -> Decimal:
    value = _quantize(_normalize_decimal("ratio value", value))
    if value < _ZERO:
        return _ZERO
    if value > _ONE:
        return _ONE
    return value


def _normalize_positive_count(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be an integer")
    return normalized.quantize(_COUNT_QUANTUM)


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return _quantize(normalized)


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(normalized)


def _normalize_unit_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between zero and one")
    return _quantize(normalized)


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be pass, watch, or block")
    if value not in _STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_NAMES:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_string(field_name, value)
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")


def _require_config_version(value: object) -> None:
    _require_public_identifier("config_version", value)
    if value != DEFAULT_RESEARCH_SOURCE_INFORMATION_RECENCY_DECAY_REPORT_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a sha256 hex digest")
    if len(value) != 64 or any(char not in _HEX_CHARS for char in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _validate_public_payload_digest(payload: dict[str, Any]) -> None:
    _require_status("report_status", payload.get("report_status"))
    validation_digest = payload.get("validation_digest")
    _require_digest("validation_digest", validation_digest)

    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a JSON array")
    for row_payload in rows:
        if type(row_payload) is not dict:
            raise ValueError("rows must contain JSON objects")
        _require_hard_flags("row payload", _DictFlags(row_payload))
        _require_status("decay_status", row_payload.get("decay_status"))
        row_validation_digest = row_payload.get("validation_digest")
        _require_digest("validation_digest", row_validation_digest)
        if row_validation_digest != _validation_digest(
            _without_validation_digest(row_payload),
        ):
            raise ValueError("validation_digest must match row payload")

    if validation_digest != _validation_digest(_without_validation_digest(payload)):
        raise ValueError("validation_digest must match report payload")


def _without_validation_digest(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key != "validation_digest"}


def _validation_digest(values: dict[str, Any]) -> str:
    ready = _json_ready(values)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool:
        return value
    if type(value) in (int, float):
        raise ValueError("numeric payload values must use Decimal")
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is str:
        _reject_unsafe_public_string("JSON value", value)
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_string("JSON object key", key)
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), allow_json_containers=True)
        return
    if isinstance(value, dict):
        if not allow_json_containers:
            raise ValueError(f"{label} must not be a raw dict")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_string(f"{label} key", key)
            _reject_unsafe_public_payload(label, item, allow_json_containers=True)
        return
    if isinstance(value, (list, tuple)):
        if not allow_json_containers:
            raise ValueError(f"{label} must not be a raw sequence")
        for item in value:
            _reject_unsafe_public_payload(label, item, allow_json_containers=True)
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)


def _reject_unsafe_public_string(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_INFORMATION_RECENCY_DECAY_REPORT_CONFIG_VERSION",
    "ResearchSourceInformationRecencyDecayConfig",
    "ResearchSourceInformationRecencyEvidence",
    "ResearchSourceInformationRecencyDecayRow",
    "ResearchSourceInformationRecencyDecayReport",
    "build_research_source_information_recency_decay_report",
    "research_source_information_recency_decay_report_payload",
)
