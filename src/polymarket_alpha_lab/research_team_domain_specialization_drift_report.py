"""Pure public-safe report-only team domain specialization drift reducer."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIZATION_DRIFT_REPORT_CONFIG_VERSION = (
    "research-team-domain-specialization-drift-report-v1"
)
DOMAIN_SPECIALIZATION_DRIFT_STATUSES = ("pass", "watch", "block")
RESEARCH_TEAM_DOMAIN_SPECIALIZATION_DOMAINS = (
    "politics",
    "crypto",
    "equities",
    "gold",
    "soccer",
    "basketball",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

_PUBLIC_CODE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
_DIGEST_LENGTH = 64
_UNSAFE_TEXT_FRAGMENTS = (
    "://",
    "@",
    "secret",
    "password",
    "passwd",
    "api_key",
    "apikey",
    "private_key",
    "access_token",
    "bearer ",
    "au" + "th",
    "wal" + "let",
    "ord" + "er",
    "tra" + "de",
    "live",
    "exec" + "ution",
    "event_" + "id",
    "market_" + "id",
    "market_" + "slug",
    "source_" + "id",
    "source_" + "url",
    "source_" + "name",
    "source_" + "text",
    "raw_" + "source",
    "data" + "base",
    "net" + "work",
    "req" + "uests",
    "url" + "lib",
    "sock" + "et",
    "sql" + "ite",
    "reco" + "mmend",
    "siz" + "ing",
)
_DOMAIN_INDEX = {
    domain: index for index, domain in enumerate(RESEARCH_TEAM_DOMAIN_SPECIALIZATION_DOMAINS)
}


@dataclass(frozen=True)
class ResearchTeamDomainSpecializationDriftConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIZATION_DRIFT_REPORT_CONFIG_VERSION
    )
    watch_drift_score: Decimal = Decimal("0.300000")
    block_drift_score: Decimal = Decimal("0.650000")
    watch_readiness_floor: Decimal = Decimal("0.700000")
    block_readiness_floor: Decimal = Decimal("0.450000")
    watch_capacity_pressure: Decimal = Decimal("0.600000")
    block_capacity_pressure: Decimal = Decimal("0.850000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainSpecializationDriftConfig, "config")
        _require_config_version(self.config_version)
        for field_name in (
            "watch_drift_score",
            "block_drift_score",
            "watch_readiness_floor",
            "block_readiness_floor",
            "watch_capacity_pressure",
            "block_capacity_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_drift_score > self.block_drift_score:
            raise ValueError("watch_drift_score must not exceed block_drift_score")
        if self.block_readiness_floor > self.watch_readiness_floor:
            raise ValueError("block_readiness_floor must not exceed watch_readiness_floor")
        if self.watch_capacity_pressure > self.block_capacity_pressure:
            raise ValueError(
                "watch_capacity_pressure must not exceed block_capacity_pressure",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainSpecializationSignal:
    team_code: str
    domain: str
    aggregate_expertise_fit: Decimal
    calibration_score: Decimal
    memory_freshness: Decimal
    source_coverage: Decimal
    capacity_pressure: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainSpecializationSignal, "signal")
        _require_public_code("team_code", self.team_code)
        _require_domain(self.domain)
        for field_name in (
            "aggregate_expertise_fit",
            "calibration_score",
            "memory_freshness",
            "source_coverage",
            "capacity_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class ResearchTeamDomainSpecializationDriftRow:
    team_code: str
    domain: str
    aggregate_expertise_fit: Decimal
    calibration_score: Decimal
    memory_freshness: Decimal
    source_coverage: Decimal
    capacity_pressure: Decimal
    aggregate_readiness_score: Decimal
    drift_score: Decimal
    drift_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainSpecializationDriftRow, "row")
        _require_public_code("team_code", self.team_code)
        _require_domain(self.domain)
        for field_name in (
            "aggregate_expertise_fit",
            "calibration_score",
            "memory_freshness",
            "source_coverage",
            "capacity_pressure",
            "aggregate_readiness_score",
            "drift_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("drift_status", self.drift_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamDomainSpecializationDriftReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainSpecializationDriftReasonCodeCount,
            "reason_code_count",
        )
        _require_public_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamDomainSpecializationDriftReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    domain_count: Decimal
    team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_specialization_fit: Decimal
    average_calibration_score: Decimal
    average_memory_freshness: Decimal
    average_source_coverage: Decimal
    average_capacity_pressure: Decimal
    max_drift_score: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamDomainSpecializationDriftReasonCodeCount, ...]
    rows: tuple[ResearchTeamDomainSpecializationDriftRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainSpecializationDriftReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_config_version(self.config_version)
        for field_name in (
            "row_count",
            "domain_count",
            "team_count",
            "pass_count",
            "watch_count",
            "block_count",
            "average_specialization_fit",
            "average_calibration_score",
            "average_memory_freshness",
            "average_source_coverage",
            "average_capacity_pressure",
            "max_drift_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_specialization_fit",
            "average_calibration_score",
            "average_memory_freshness",
            "average_source_coverage",
            "average_capacity_pressure",
            "max_drift_score",
        ):
            _require_unit_decimal(field_name, getattr(self, field_name))
        _require_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_team_domain_specialization_drift_report_payload(self)


def build_research_team_domain_specialization_drift_report(
    signals: object,
    *,
    config: ResearchTeamDomainSpecializationDriftConfig,
    generated_at: datetime,
) -> ResearchTeamDomainSpecializationDriftReport:
    if type(config) is not ResearchTeamDomainSpecializationDriftConfig:
        raise ValueError("config must be a ResearchTeamDomainSpecializationDriftConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    _validate_unique_signals(normalized_signals)
    rows = tuple(
        sorted(
            (
                _row_for_signal(signal, config=config)
                for signal in normalized_signals
            ),
            key=_row_key,
        ),
    )
    report_reason_codes = _report_reason_codes(rows)
    return ResearchTeamDomainSpecializationDriftReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        row_count=_count(len(rows)),
        domain_count=_count(len({row.domain for row in rows})),
        team_count=_count(len({row.team_code for row in rows})),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        average_specialization_fit=_average_or_zero(
            tuple(row.aggregate_expertise_fit for row in rows),
        ),
        average_calibration_score=_average_or_zero(
            tuple(row.calibration_score for row in rows),
        ),
        average_memory_freshness=_average_or_zero(
            tuple(row.memory_freshness for row in rows),
        ),
        average_source_coverage=_average_or_zero(
            tuple(row.source_coverage for row in rows),
        ),
        average_capacity_pressure=_average_or_zero(
            tuple(row.capacity_pressure for row in rows),
        ),
        max_drift_score=max((row.drift_score for row in rows), default=ZERO),
        report_status=_report_status(rows),
        reason_codes=report_reason_codes,
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_team_domain_specialization_drift_report_payload(
    report: ResearchTeamDomainSpecializationDriftReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamDomainSpecializationDriftReport:
        raise ValueError("report must be a ResearchTeamDomainSpecializationDriftReport")
    _validate_report(report)
    payload = _report_public_payload_for_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    validate_research_team_domain_specialization_drift_report_payload(payload)
    return payload


def validate_research_team_domain_specialization_drift_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload("payload", payload)
    _reject_public_numeric_values(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match payload")
    return True


def _row_for_signal(
    signal: ResearchTeamDomainSpecializationSignal,
    *,
    config: ResearchTeamDomainSpecializationDriftConfig,
) -> ResearchTeamDomainSpecializationDriftRow:
    aggregate_readiness_score = _aggregate_readiness_score(signal)
    drift_score = _drift_score(
        aggregate_readiness_score=aggregate_readiness_score,
        capacity_pressure=signal.capacity_pressure,
    )
    drift_status = _drift_status(
        aggregate_readiness_score=aggregate_readiness_score,
        drift_score=drift_score,
        capacity_pressure=signal.capacity_pressure,
        config=config,
    )
    return ResearchTeamDomainSpecializationDriftRow(
        team_code=signal.team_code,
        domain=signal.domain,
        aggregate_expertise_fit=signal.aggregate_expertise_fit,
        calibration_score=signal.calibration_score,
        memory_freshness=signal.memory_freshness,
        source_coverage=signal.source_coverage,
        capacity_pressure=signal.capacity_pressure,
        aggregate_readiness_score=aggregate_readiness_score,
        drift_score=drift_score,
        drift_status=drift_status,
        reason_codes=_row_reason_codes(
            aggregate_expertise_fit=signal.aggregate_expertise_fit,
            calibration_score=signal.calibration_score,
            memory_freshness=signal.memory_freshness,
            source_coverage=signal.source_coverage,
            capacity_pressure=signal.capacity_pressure,
            aggregate_readiness_score=aggregate_readiness_score,
            drift_score=drift_score,
            drift_status=drift_status,
            config=config,
        ),
    )


def _aggregate_readiness_score(signal: ResearchTeamDomainSpecializationSignal) -> Decimal:
    return _average_or_zero(
        (
            signal.aggregate_expertise_fit,
            signal.calibration_score,
            signal.memory_freshness,
            signal.source_coverage,
        ),
    )


def _drift_score(
    *,
    aggregate_readiness_score: Decimal,
    capacity_pressure: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        readiness_gap = ONE - aggregate_readiness_score
        value = readiness_gap * Decimal("0.650000") + capacity_pressure * Decimal("0.350000")
    return _clamp_unit(_quantize(value))


def _drift_status(
    *,
    aggregate_readiness_score: Decimal,
    drift_score: Decimal,
    capacity_pressure: Decimal,
    config: ResearchTeamDomainSpecializationDriftConfig,
) -> str:
    if (
        drift_score >= config.block_drift_score
        or aggregate_readiness_score <= config.block_readiness_floor
        or capacity_pressure >= config.block_capacity_pressure
    ):
        return "block"
    if (
        drift_score >= config.watch_drift_score
        or aggregate_readiness_score <= config.watch_readiness_floor
        or capacity_pressure >= config.watch_capacity_pressure
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    aggregate_expertise_fit: Decimal,
    calibration_score: Decimal,
    memory_freshness: Decimal,
    source_coverage: Decimal,
    capacity_pressure: Decimal,
    aggregate_readiness_score: Decimal,
    drift_score: Decimal,
    drift_status: str,
    config: ResearchTeamDomainSpecializationDriftConfig,
) -> tuple[str, ...]:
    reason_codes = [f"domain_specialization_{drift_status}"]
    if drift_score >= config.block_drift_score:
        reason_codes.append("drift_score_block")
    elif drift_score >= config.watch_drift_score:
        reason_codes.append("drift_score_watch")
    if aggregate_readiness_score <= config.block_readiness_floor:
        reason_codes.append("aggregate_readiness_block")
    elif aggregate_readiness_score <= config.watch_readiness_floor:
        reason_codes.append("aggregate_readiness_watch")
    if capacity_pressure >= config.block_capacity_pressure:
        reason_codes.append("capacity_pressure_block")
    elif capacity_pressure >= config.watch_capacity_pressure:
        reason_codes.append("capacity_pressure_watch")
    if aggregate_expertise_fit <= config.watch_readiness_floor:
        reason_codes.append("aggregate_expertise_fit_watch")
    if calibration_score <= config.watch_readiness_floor:
        reason_codes.append("calibration_watch")
    if memory_freshness <= config.watch_readiness_floor:
        reason_codes.append("memory_freshness_watch")
    if source_coverage <= config.watch_readiness_floor:
        reason_codes.append("source_coverage_watch")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainSpecializationDriftRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("domain_specialization_empty",)
    report_status = _report_status(rows)
    reason_codes = [f"domain_specialization_report_{report_status}"]
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code not in reason_codes:
                reason_codes.append(reason_code)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_status(rows: tuple[ResearchTeamDomainSpecializationDriftRow, ...]) -> str:
    if any(row.drift_status == "block" for row in rows):
        return "block"
    if any(row.drift_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchTeamDomainSpecializationDriftRow, ...],
) -> tuple[ResearchTeamDomainSpecializationDriftReasonCodeCount, ...]:
    reason_codes = sorted({reason_code for row in rows for reason_code in row.reason_codes})
    return tuple(
        ResearchTeamDomainSpecializationDriftReasonCodeCount(
            reason_code=reason_code,
            count=_count(sum(1 for row in rows if reason_code in row.reason_codes)),
        )
        for reason_code in reason_codes
    )


def _normalize_signals(value: object) -> tuple[ResearchTeamDomainSpecializationSignal, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        signals = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    for item in signals:
        if type(item) is not ResearchTeamDomainSpecializationSignal:
            raise ValueError(
                "signals must contain ResearchTeamDomainSpecializationSignal values",
            )
        _require_hard_flags("signal", item)
    return signals


def _normalize_rows(
    value: object,
) -> tuple[ResearchTeamDomainSpecializationDriftRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchTeamDomainSpecializationDriftRow:
            raise ValueError("rows must contain ResearchTeamDomainSpecializationDriftRow values")
        _require_hard_flags("row", row)
    normalized = tuple(sorted(rows, key=_row_key))
    if rows != normalized:
        raise ValueError("rows must use deterministic sequence")
    _validate_unique_rows(rows)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchTeamDomainSpecializationDriftReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for count in counts:
        if type(count) is not ResearchTeamDomainSpecializationDriftReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamDomainSpecializationDriftReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
        if count.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(count.reason_code)
    normalized = tuple(sorted(counts, key=lambda item: item.reason_code))
    if counts != normalized:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return counts


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_public_code(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    return reason_codes


def _validate_unique_signals(
    signals: tuple[ResearchTeamDomainSpecializationSignal, ...],
) -> None:
    seen: set[tuple[str, str]] = set()
    for signal in signals:
        key = (signal.domain, signal.team_code)
        if key in seen:
            raise ValueError("signals must be unique by team and domain")
        seen.add(key)


def _validate_unique_rows(
    rows: tuple[ResearchTeamDomainSpecializationDriftRow, ...],
) -> None:
    seen: set[tuple[int, str]] = set()
    for row in rows:
        key = _row_key(row)
        if key in seen:
            raise ValueError("rows must be unique by team and domain")
        seen.add(key)


def _validate_report(report: ResearchTeamDomainSpecializationDriftReport) -> None:
    _require_hard_flags("report", report)
    _validate_unique_rows(report.rows)
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.domain_count != _count(len({row.domain for row in report.rows})):
        raise ValueError("domain_count must match rows")
    if report.team_count != _count(len({row.team_code for row in report.rows})):
        raise ValueError("team_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.average_specialization_fit != _average_or_zero(
        tuple(row.aggregate_expertise_fit for row in report.rows),
    ):
        raise ValueError("average_specialization_fit must match rows")
    if report.average_calibration_score != _average_or_zero(
        tuple(row.calibration_score for row in report.rows),
    ):
        raise ValueError("average_calibration_score must match rows")
    if report.average_memory_freshness != _average_or_zero(
        tuple(row.memory_freshness for row in report.rows),
    ):
        raise ValueError("average_memory_freshness must match rows")
    if report.average_source_coverage != _average_or_zero(
        tuple(row.source_coverage for row in report.rows),
    ):
        raise ValueError("average_source_coverage must match rows")
    if report.average_capacity_pressure != _average_or_zero(
        tuple(row.capacity_pressure for row in report.rows),
    ):
        raise ValueError("average_capacity_pressure must match rows")
    expected_max_drift = max((row.drift_score for row in report.rows), default=ZERO)
    if report.max_drift_score != expected_max_drift:
        raise ValueError("max_drift_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report")


def _row_key(row: ResearchTeamDomainSpecializationDriftRow) -> tuple[int, str]:
    return (_DOMAIN_INDEX[row.domain], row.team_code)


def _status_count(
    rows: tuple[ResearchTeamDomainSpecializationDriftRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.drift_status == status))


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _average_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    _require_unit_decimal(field_name, decimal_value)
    return decimal_value


def _require_unit_decimal(field_name: str, value: Decimal) -> None:
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _clamp_unit(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be {expected_type.__name__}")


def _require_config_version(value: object) -> None:
    if type(value) is not str:
        raise ValueError("config_version must be a string")
    if value != DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIZATION_DRIFT_REPORT_CONFIG_VERSION:
        raise ValueError("config_version is not supported")


def _require_domain(value: object) -> None:
    if type(value) is not str or value not in RESEARCH_TEAM_DOMAIN_SPECIALIZATION_DOMAINS:
        raise ValueError("domain must be supported")


def _require_public_code(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a public code")
    if not value:
        raise ValueError(f"{field_name} must be a public code")
    if any(fragment in value.lower() for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be a public code")
    if any(character not in _PUBLIC_CODE_CHARS for character in value):
        raise ValueError(f"{field_name} must be a public code")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in DOMAIN_SPECIALIZATION_DRIFT_STATUSES:
        raise ValueError(f"{field_name} must be supported")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    if payload.get("paper_only") is not True:
        raise ValueError("payload must be paper_only")
    if payload.get("report_only") is not True:
        raise ValueError("payload must be report_only")
    if payload.get("readonly") is not True:
        raise ValueError("payload must be readonly")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if len(value) != _DIGEST_LENGTH:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _report_public_payload_for_digest(
    report: ResearchTeamDomainSpecializationDriftReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _report_derived_validation_digest(
    report: ResearchTeamDomainSpecializationDriftReport,
) -> str:
    return _public_payload_derived_validation_digest(_report_public_payload_for_digest(report))


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        return _as_utc("datetime", value).isoformat()
    if type(value) is bool or value is None:
        return value
    if type(value) is str:
        return value
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    if isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe public payload text")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in _UNSAFE_TEXT_FRAGMENTS):
                raise ValueError(f"{label} contains unsafe public payload field")
            _reject_unsafe_public_payload(key, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)


__all__ = (
    "DOMAIN_SPECIALIZATION_DRIFT_STATUSES",
    "DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIZATION_DRIFT_REPORT_CONFIG_VERSION",
    "RESEARCH_TEAM_DOMAIN_SPECIALIZATION_DOMAINS",
    "ResearchTeamDomainSpecializationDriftConfig",
    "ResearchTeamDomainSpecializationDriftReasonCodeCount",
    "ResearchTeamDomainSpecializationDriftReport",
    "ResearchTeamDomainSpecializationDriftRow",
    "ResearchTeamDomainSpecializationSignal",
    "build_research_team_domain_specialization_drift_report",
    "research_team_domain_specialization_drift_report_payload",
    "validate_research_team_domain_specialization_drift_report_payload",
)
