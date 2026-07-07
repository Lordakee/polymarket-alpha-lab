"""Pure report reducer for decision block reason coverage."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "ResearchDecisionBlockReasonCatalogReport",
    "ResearchDecisionBlockReasonCatalogRow",
    "ResearchDecisionBlockReasonObservation",
    "build_research_decision_block_reason_catalog_report",
    "research_decision_block_reason_catalog_payload",
)


REASON_FAMILIES = (
    "cost_too_high",
    "evidence_insufficient",
    "memory_gap",
    "settlement_ambiguity",
    "source_conflict",
)
COVERAGE_STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
ZERO_SCORE = Decimal("0.000000")
ONE_SCORE = Decimal("1.000000")
SCORE_QUANTUM = Decimal("0.000001")
PUBLIC_TEXT_DENY_FRAGMENTS = (
    "raw_",
    "_id",
    "id_",
    "market_slug",
    "market_id",
    "source_id",
    "dsn",
    "table",
    "token",
    "://",
    "@",
)


class _Missing:
    pass


_MISSING = _Missing()
_STATUS_SEVERITY = {"pass": 0, "watch": 1, "block": 2}


@dataclass(frozen=True)
class ResearchDecisionBlockReasonObservation:
    reason_family: str
    coverage_status: str
    severity_score: Decimal
    confidence_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_family("reason_family", self.reason_family)
        _require_coverage_status("coverage_status", self.coverage_status)
        object.__setattr__(
            self,
            "severity_score",
            _require_probability_decimal("severity_score", self.severity_score),
        )
        object.__setattr__(
            self,
            "confidence_score",
            _require_probability_decimal("confidence_score", self.confidence_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchDecisionBlockReasonCatalogRow:
    reason_family: str
    coverage_status: str
    observation_count: Decimal
    max_severity_score: Decimal
    average_confidence_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_family("reason_family", self.reason_family)
        _require_coverage_status("coverage_status", self.coverage_status)
        object.__setattr__(
            self,
            "observation_count",
            _require_nonnegative_whole_decimal(
                "observation_count",
                self.observation_count,
            ),
        )
        object.__setattr__(
            self,
            "max_severity_score",
            _require_probability_decimal("max_severity_score", self.max_severity_score),
        )
        object.__setattr__(
            self,
            "average_confidence_score",
            _require_probability_decimal(
                "average_confidence_score",
                self.average_confidence_score,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("catalog_row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchDecisionBlockReasonCatalogReport:
    generated_at: datetime
    observation_count: Decimal
    reason_family_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    coverage_status: str
    rows: tuple[ResearchDecisionBlockReasonCatalogRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        for name in (
            "observation_count",
            "reason_family_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_whole_decimal(name, getattr(self, name)),
            )
        _require_coverage_status("coverage_status", self.coverage_status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("catalog_report", self)
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_decision_block_reason_catalog_payload(self)


def build_research_decision_block_reason_catalog_report(
    observations: Iterable[object],
    *,
    generated_at: datetime,
) -> ResearchDecisionBlockReasonCatalogReport:
    generated_at_utc = _as_utc("generated_at", generated_at)
    observation_items = _normalize_observations(observations)
    grouped: dict[str, list[ResearchDecisionBlockReasonObservation]] = {
        family: [] for family in REASON_FAMILIES
    }
    for item in observation_items:
        grouped[item.reason_family].append(item)

    rows = tuple(_row_from_family(family, tuple(grouped[family])) for family in REASON_FAMILIES)
    reason_codes = _summary_reason_codes(rows)
    return ResearchDecisionBlockReasonCatalogReport(
        generated_at=generated_at_utc,
        observation_count=_decimal_count(len(observation_items)),
        reason_family_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        coverage_status=_summary_coverage_status(rows),
        rows=rows,
        reason_codes=reason_codes,
    )


def research_decision_block_reason_catalog_payload(
    report: ResearchDecisionBlockReasonCatalogReport,
) -> dict[str, Any]:
    if type(report) is not ResearchDecisionBlockReasonCatalogReport:
        raise ValueError("report must be a ResearchDecisionBlockReasonCatalogReport")
    _require_hard_flags("catalog_report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_public_payload(payload)
    return payload


def _row_from_family(
    reason_family: str,
    observations: tuple[ResearchDecisionBlockReasonObservation, ...],
) -> ResearchDecisionBlockReasonCatalogRow:
    if not observations:
        return ResearchDecisionBlockReasonCatalogRow(
            reason_family=reason_family,
            coverage_status="block",
            observation_count=ZERO,
            max_severity_score=ONE_SCORE,
            average_confidence_score=ZERO_SCORE,
            reason_codes=(f"missing_{reason_family}_reason_coverage",),
        )
    coverage_status = max(
        (item.coverage_status for item in observations),
        key=lambda value: _STATUS_SEVERITY[value],
    )
    input_reason_codes = tuple(code for item in observations for code in item.reason_codes)
    return ResearchDecisionBlockReasonCatalogRow(
        reason_family=reason_family,
        coverage_status=coverage_status,
        observation_count=_decimal_count(len(observations)),
        max_severity_score=max(item.severity_score for item in observations),
        average_confidence_score=_average_score(
            tuple(item.confidence_score for item in observations),
        ),
        reason_codes=(
            f"{reason_family}_{coverage_status}_coverage",
            *input_reason_codes,
        ),
    )


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchDecisionBlockReasonObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    return tuple(_coerce_observation(value) for value in values)


def _coerce_observation(value: object) -> ResearchDecisionBlockReasonObservation:
    if type(value) is ResearchDecisionBlockReasonObservation:
        _require_hard_flags("observation", value)
        return value
    _require_hard_flags("observation", value)
    return ResearchDecisionBlockReasonObservation(
        reason_family=_field_value(value, "reason_family"),
        coverage_status=_field_value(value, "coverage_status"),
        severity_score=_field_value(value, "severity_score"),
        confidence_score=_field_value(value, "confidence_score"),
        reason_codes=_field_value(value, "reason_codes"),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _normalize_rows(
    rows: tuple[ResearchDecisionBlockReasonCatalogRow, ...],
) -> tuple[ResearchDecisionBlockReasonCatalogRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchDecisionBlockReasonCatalogRow:
            raise ValueError("rows must contain ResearchDecisionBlockReasonCatalogRow values")
        _require_hard_flags("catalog_row", row)
    expected = tuple(REASON_FAMILIES)
    actual = tuple(row.reason_family for row in rows)
    if actual != expected:
        raise ValueError("rows must cover the required reason families")
    return rows


def _summary_coverage_status(
    rows: tuple[ResearchDecisionBlockReasonCatalogRow, ...],
) -> str:
    if any(row.coverage_status == "block" for row in rows):
        return "block"
    if any(row.coverage_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _summary_reason_codes(
    rows: tuple[ResearchDecisionBlockReasonCatalogRow, ...],
) -> tuple[str, ...]:
    summary_status = _summary_coverage_status(rows)
    if summary_status == "pass":
        return ("reason_catalog_pass",)
    codes = {f"reason_catalog_{summary_status}"}
    for row in rows:
        codes.update(row.reason_codes)
    return tuple(sorted(codes))


def _status_count(rows: tuple[ResearchDecisionBlockReasonCatalogRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.coverage_status == status)


def _average_score(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must be nonempty")
    return _quantize(sum(values, ZERO_SCORE) / Decimal(len(values)))


def _validate_row_consistency(row: ResearchDecisionBlockReasonCatalogRow) -> None:
    missing_code = f"missing_{row.reason_family}_reason_coverage"
    status_code = f"{row.reason_family}_{row.coverage_status}_coverage"
    if row.observation_count == ZERO:
        if row.coverage_status != "block":
            raise ValueError("coverage_status must be block when observation_count is zero")
        if row.max_severity_score != ONE_SCORE:
            raise ValueError("max_severity_score must be 1 when observation_count is zero")
        if row.average_confidence_score != ZERO_SCORE:
            raise ValueError("average_confidence_score must be 0 when observation_count is zero")
        if row.reason_codes != (missing_code,):
            raise ValueError("observation_count must match missing coverage reason")
        return
    if missing_code in row.reason_codes:
        raise ValueError("observation_count must match present coverage reason")
    if status_code not in row.reason_codes:
        raise ValueError("reason_codes must include coverage status")


def _validate_report_consistency(report: ResearchDecisionBlockReasonCatalogReport) -> None:
    if report.reason_family_count != _decimal_count(len(report.rows)):
        raise ValueError("reason_family_count must match rows")
    if report.observation_count != sum((row.observation_count for row in report.rows), ZERO):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.coverage_status != _summary_coverage_status(report.rows):
        raise ValueError("coverage_status must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _field_value(value: object, name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == name:
                return getattr(value, name)
    if hasattr(value, name):
        return getattr(value, name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{name} is required")


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be finite") from exc


def _require_probability_decimal(name: str, value: object) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    if normalized.as_tuple().exponent != SCORE_QUANTUM.as_tuple().exponent:
        raise ValueError(f"{name} must use six decimal places")
    return normalized


def _require_nonnegative_whole_decimal(name: str, value: object) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count input must be an int")
    if value < 0:
        raise ValueError("count input must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(SCORE_QUANTUM)


def _require_reason_family(name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_FAMILIES:
        raise ValueError(f"{name} must be a known reason family")


def _require_coverage_status(name: str, value: object) -> None:
    if type(value) is not str or value not in COVERAGE_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _normalize_reason_codes(
    name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_public_reason_code(name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_public_reason_code(name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{name} must contain public reason codes")
    if not all(char.islower() or char.isdigit() or char == "_" for char in value):
        raise ValueError(f"{name} must contain public reason codes")
    _reject_unsafe_public_text(name, value)


def _require_hard_flags(label: str, value: object) -> None:
    for name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, name):
            raise ValueError(f"{label} must expose {name}")
        if getattr(value, name) is not True:
            raise ValueError(f"{name} must be True")


def _reject_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_public_text("payload", key)
            _reject_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_payload(item)
        return
    if type(value) is str:
        _reject_unsafe_public_text("payload", value)


def _reject_unsafe_public_text(name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in PUBLIC_TEXT_DENY_FRAGMENTS):
        raise ValueError(f"{name} must not contain raw private references")
