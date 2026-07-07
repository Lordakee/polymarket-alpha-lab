"""Deterministic report-only research operational readiness rollup."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_OPERATIONAL_READINESS_CONFIG_VERSION = (
    "research-operational-readiness-report-v1"
)

MANUAL_REVIEW_CHECKLIST_SURFACE = "manual_review_checklist"
EXECUTION_BOUNDARY_GUARD_SURFACE = "execution_boundary_guard"
TEAM_CAPACITY_SURFACE = "team_capacity"
INFORMATION_COLLECTION_PLAN_SURFACE = "information_collection_plan"

REQUIRED_OPERATIONAL_READINESS_SURFACES = (
    MANUAL_REVIEW_CHECKLIST_SURFACE,
    EXECUTION_BOUNDARY_GUARD_SURFACE,
    TEAM_CAPACITY_SURFACE,
    INFORMATION_COLLECTION_PLAN_SURFACE,
)

_SURFACE_SET = frozenset(REQUIRED_OPERATIONAL_READINESS_SURFACES)
_STATUSES = ("pass", "watch", "block")
_STATUS_ORDER = {"pass": 0, "watch": 1, "block": 2}
_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))

_FORBIDDEN_PUBLIC_FRAGMENTS = frozenset(
    (
        "raw_candidate",
        "candidate_id",
        "candidate",
        "market_id",
        "market_slug",
        "market",
        "slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "source ref",
        "source url",
        "source text",
        "url",
        "http://",
        "https://",
        "dsn",
        "database",
        "table",
        "token",
        "wallet",
        "auth",
        "credential",
        "secret",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    ),
)

_REASON_CODE_SEQUENCE = (
    "missing_manual_review_checklist",
    "missing_execution_boundary_guard",
    "missing_team_capacity",
    "missing_information_collection_plan",
    "manual_review_checklist_watch",
    "manual_review_checklist_block",
    "execution_boundary_guard_watch",
    "execution_boundary_guard_block",
    "team_capacity_watch",
    "team_capacity_block",
    "information_collection_plan_watch",
    "information_collection_plan_block",
    "pending_items_watch",
    "pending_items_block",
    "blocked_items_block",
    "coverage_incomplete_watch",
    "coverage_incomplete_block",
    "operational_readiness_watch",
    "operational_readiness_block",
    "operational_readiness_pass",
)
_REASON_CODE_SET = frozenset(_REASON_CODE_SEQUENCE)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class ResearchOperationalReadinessConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_OPERATIONAL_READINESS_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchOperationalReadinessConfig, "config")
        _require_supported_config_version(self.config_version)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchOperationalReadinessSignal(_FinalPublicDataclass):
    surface_code: str
    status: str
    coverage_score: Decimal
    pending_item_count: Decimal
    block_item_count: Decimal
    public_note: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchOperationalReadinessSignal, "signal")
        _require_surface_code("surface_code", self.surface_code)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "coverage_score",
            _require_ratio_decimal("coverage_score", self.coverage_score),
        )
        object.__setattr__(
            self,
            "pending_item_count",
            _require_nonnegative_count_decimal(
                "pending_item_count",
                self.pending_item_count,
            ),
        )
        object.__setattr__(
            self,
            "block_item_count",
            _require_nonnegative_count_decimal(
                "block_item_count",
                self.block_item_count,
            ),
        )
        object.__setattr__(
            self,
            "public_note",
            _normalize_optional_public_text("public_note", self.public_note),
        )
        _require_hard_flags("signal", self)
        _reject_unsafe_public_payload("signal", self)


@dataclass(frozen=True)
class ResearchOperationalReadinessRow(_FinalPublicDataclass):
    surface_code: str
    status: str
    coverage_score: Decimal
    pending_item_count: Decimal
    block_item_count: Decimal
    reason_codes: tuple[str, ...]
    public_note: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchOperationalReadinessRow, "row")
        _require_surface_code("surface_code", self.surface_code)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "coverage_score",
            _require_ratio_decimal("coverage_score", self.coverage_score),
        )
        object.__setattr__(
            self,
            "pending_item_count",
            _require_nonnegative_count_decimal(
                "pending_item_count",
                self.pending_item_count,
            ),
        )
        object.__setattr__(
            self,
            "block_item_count",
            _require_nonnegative_count_decimal(
                "block_item_count",
                self.block_item_count,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "public_note",
            _normalize_optional_public_text("public_note", self.public_note),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchOperationalReadinessReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchOperationalReadinessReasonCodeCount,
            "reason code count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchOperationalReadinessReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    report_status: str
    surface_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    min_coverage_score: Decimal
    total_pending_item_count: Decimal
    total_block_item_count: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchOperationalReadinessReasonCodeCount, ...]
    rows: tuple[ResearchOperationalReadinessRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchOperationalReadinessReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_supported_config_version(self.config_version)
        _require_status("report_status", self.report_status)
        for field_name in (
            "surface_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_pending_item_count",
            "total_block_item_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "min_coverage_score",
            _require_ratio_decimal("min_coverage_score", self.min_coverage_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        return research_operational_readiness_report_payload(self)


def build_research_operational_readiness_report(
    signals: Sequence[ResearchOperationalReadinessSignal],
    *,
    generated_at: datetime,
    config: ResearchOperationalReadinessConfig | None = None,
) -> ResearchOperationalReadinessReport:
    """Build a local paper-only operational readiness report."""

    if config is None:
        config = ResearchOperationalReadinessConfig()
    if type(config) is not ResearchOperationalReadinessConfig:
        raise ValueError("config must be exactly ResearchOperationalReadinessConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    rows = _build_rows(normalized_signals)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "report_status": _report_status(rows),
        "surface_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "min_coverage_score": _min_coverage_score(rows),
        "total_pending_item_count": _sum_decimals(
            row.pending_item_count for row in rows
        ),
        "total_block_item_count": _sum_decimals(row.block_item_count for row in rows),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchOperationalReadinessReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_operational_readiness_report_payload(
    report: ResearchOperationalReadinessReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchOperationalReadinessReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _require_hard_flags("payload", _DictFlags(report))
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchOperationalReadinessReport or payload")
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    if "derived_validation_digest" in payload:
        _require_sha256_digest(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        )
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


def _build_rows(
    signals: tuple[ResearchOperationalReadinessSignal, ...],
) -> tuple[ResearchOperationalReadinessRow, ...]:
    by_surface = {signal.surface_code: signal for signal in signals}
    return tuple(
        _row_from_signal(by_surface[surface_code])
        if surface_code in by_surface
        else _missing_row(surface_code)
        for surface_code in REQUIRED_OPERATIONAL_READINESS_SURFACES
    )


def _row_from_signal(
    signal: ResearchOperationalReadinessSignal,
) -> ResearchOperationalReadinessRow:
    _require_hard_flags("signal", signal)
    status = _effective_status(
        signal.status,
        signal.coverage_score,
        signal.pending_item_count,
        signal.block_item_count,
    )
    return ResearchOperationalReadinessRow(
        surface_code=signal.surface_code,
        status=status,
        coverage_score=signal.coverage_score,
        pending_item_count=signal.pending_item_count,
        block_item_count=signal.block_item_count,
        reason_codes=_row_reason_codes(
            surface_code=signal.surface_code,
            status=status,
            coverage_score=signal.coverage_score,
            pending_item_count=signal.pending_item_count,
            block_item_count=signal.block_item_count,
            missing=False,
        ),
        public_note=signal.public_note,
    )


def _missing_row(surface_code: str) -> ResearchOperationalReadinessRow:
    return ResearchOperationalReadinessRow(
        surface_code=surface_code,
        status="block",
        coverage_score=_ZERO,
        pending_item_count=_ZERO,
        block_item_count=_ONE,
        reason_codes=_row_reason_codes(
            surface_code=surface_code,
            status="block",
            coverage_score=_ZERO,
            pending_item_count=_ZERO,
            block_item_count=_ONE,
            missing=True,
        ),
    )


def _effective_status(
    requested_status: str,
    coverage_score: Decimal,
    pending_item_count: Decimal,
    block_item_count: Decimal,
) -> str:
    if requested_status == "block" or block_item_count > _ZERO:
        return "block"
    if requested_status == "watch" or pending_item_count > _ZERO or coverage_score < _ONE:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    surface_code: str,
    status: str,
    coverage_score: Decimal,
    pending_item_count: Decimal,
    block_item_count: Decimal,
    missing: bool,
) -> tuple[str, ...]:
    codes: list[str] = []
    if missing:
        codes.append(f"missing_{surface_code}")
    elif status != "pass":
        codes.append(f"{surface_code}_{status}")
    if block_item_count > _ZERO and not missing:
        codes.append("blocked_items_block")
    if pending_item_count > _ZERO:
        codes.append("pending_items_block" if status == "block" else "pending_items_watch")
    if coverage_score < _ONE and not missing:
        codes.append(
            "coverage_incomplete_block"
            if status == "block"
            else "coverage_incomplete_watch",
        )
    return _normalize_reason_codes(tuple(codes))


def _report_status(rows: tuple[ResearchOperationalReadinessRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchOperationalReadinessRow, ...],
) -> tuple[str, ...]:
    status = _report_status(rows)
    if status == "pass":
        return ("operational_readiness_pass",)
    codes = [
        reason_code
        for row in rows
        for reason_code in row.reason_codes
    ]
    codes.append(f"operational_readiness_{status}")
    return _normalize_reason_codes(tuple(codes))


def _status_count(
    rows: tuple[ResearchOperationalReadinessRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _reason_code_counts(
    rows: tuple[ResearchOperationalReadinessRow, ...],
) -> tuple[ResearchOperationalReadinessReasonCodeCount, ...]:
    report_codes = _report_reason_codes(rows)
    return tuple(
        ResearchOperationalReadinessReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(
                sum(
                    1
                    for row in rows
                    if reason_code in row.reason_codes
                )
                or 1,
            ),
        )
        for reason_code in report_codes
    )


def _min_coverage_score(rows: tuple[ResearchOperationalReadinessRow, ...]) -> Decimal:
    if not rows:
        return _ZERO
    return min(row.coverage_score for row in rows)


def _validate_row_consistency(row: ResearchOperationalReadinessRow) -> None:
    expected_status = _effective_status(
        row.status,
        row.coverage_score,
        row.pending_item_count,
        row.block_item_count,
    )
    if row.status != expected_status:
        raise ValueError("row status must match coverage and item counts")
    expected_reason_codes = _row_reason_codes(
        surface_code=row.surface_code,
        status=row.status,
        coverage_score=row.coverage_score,
        pending_item_count=row.pending_item_count,
        block_item_count=row.block_item_count,
        missing=_is_missing_row(row),
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("row reason_codes must match row status")
    if row.status == "pass" and row.reason_codes:
        raise ValueError("pass row reason_codes must be empty")


def _validate_report_consistency(report: ResearchOperationalReadinessReport) -> None:
    if tuple(row.surface_code for row in report.rows) != REQUIRED_OPERATIONAL_READINESS_SURFACES:
        raise ValueError("rows must cover required operational surfaces")
    if report.surface_count != _decimal_count(len(report.rows)):
        raise ValueError("surface_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.min_coverage_score != _min_coverage_score(report.rows):
        raise ValueError("min_coverage_score must match rows")
    if report.total_pending_item_count != _sum_decimals(
        row.pending_item_count for row in report.rows
    ):
        raise ValueError("total_pending_item_count must match rows")
    if report.total_block_item_count != _sum_decimals(
        row.block_item_count for row in report.rows
    ):
        raise ValueError("total_block_item_count must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_signals(
    signals: Sequence[ResearchOperationalReadinessSignal],
) -> tuple[ResearchOperationalReadinessSignal, ...]:
    if isinstance(signals, (str, bytes)) or not isinstance(signals, Sequence):
        raise ValueError("signals must be a sequence")
    normalized: list[ResearchOperationalReadinessSignal] = []
    seen: set[str] = set()
    for signal in signals:
        if type(signal) is not ResearchOperationalReadinessSignal:
            raise ValueError("signals must contain ResearchOperationalReadinessSignal")
        _require_hard_flags("signal", signal)
        if signal.surface_code in seen:
            raise ValueError("signals must contain unique surface_code values")
        seen.add(signal.surface_code)
        normalized.append(signal)
    return tuple(sorted(normalized, key=lambda signal: _surface_index(signal.surface_code)))


def _normalize_rows(
    rows: Sequence[ResearchOperationalReadinessRow],
) -> tuple[ResearchOperationalReadinessRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchOperationalReadinessRow] = []
    for row in rows:
        if type(row) is not ResearchOperationalReadinessRow:
            raise ValueError("rows must contain ResearchOperationalReadinessRow")
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: _surface_index(row.surface_code)))


def _normalize_reason_code_counts(
    counts: Sequence[ResearchOperationalReadinessReasonCodeCount],
) -> tuple[ResearchOperationalReadinessReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    normalized: list[ResearchOperationalReadinessReasonCodeCount] = []
    for count in counts:
        if type(count) is not ResearchOperationalReadinessReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchOperationalReadinessReasonCodeCount",
            )
        _require_hard_flags("reason code count", count)
        normalized.append(count)
    return tuple(sorted(normalized, key=lambda item: _reason_index(item.reason_code)))


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _is_missing_row(row: ResearchOperationalReadinessRow) -> bool:
    return row.reason_codes == (f"missing_{row.surface_code}",)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_supported_config_version(value: object) -> str:
    config_version = _require_public_identifier("config_version", value)
    if config_version != DEFAULT_RESEARCH_OPERATIONAL_READINESS_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    return config_version


def _require_surface_code(field_name: str, value: object) -> str:
    surface_code = _require_public_identifier(field_name, value)
    if surface_code not in _SURFACE_SET:
        raise ValueError(f"{field_name} must be a supported operational surface")
    return surface_code


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    reason_code = _require_public_identifier(field_name, value)
    if reason_code not in _REASON_CODE_SET:
        raise ValueError(f"{field_name} must be a supported reason code")
    return reason_code


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical public text")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _normalize_optional_public_text(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _require_public_text(field_name, value)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(field_name, value)


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _sum_decimals(values: Sequence[Decimal] | Any) -> Decimal:
    total = _ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("sum values must be Decimal")
        total = _quantize(total + value)
    return total


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _surface_index(surface_code: str) -> int:
    return REQUIRED_OPERATIONAL_READINESS_SURFACES.index(surface_code)


def _reason_index(reason_code: str) -> int:
    return _REASON_CODE_SEQUENCE.index(reason_code)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        _reject_unsafe_public_string(path or label, value)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_string(nested_path, key)
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _FORBIDDEN_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")


def _report_values_without_digest(
    report: ResearchOperationalReadinessReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _report_digest_from_values(values: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(
            _json_ready(values),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


__all__ = (
    "DEFAULT_RESEARCH_OPERATIONAL_READINESS_CONFIG_VERSION",
    "EXECUTION_BOUNDARY_GUARD_SURFACE",
    "INFORMATION_COLLECTION_PLAN_SURFACE",
    "MANUAL_REVIEW_CHECKLIST_SURFACE",
    "REQUIRED_OPERATIONAL_READINESS_SURFACES",
    "TEAM_CAPACITY_SURFACE",
    "ResearchOperationalReadinessConfig",
    "ResearchOperationalReadinessReasonCodeCount",
    "ResearchOperationalReadinessReport",
    "ResearchOperationalReadinessRow",
    "ResearchOperationalReadinessSignal",
    "build_research_operational_readiness_report",
    "research_operational_readiness_report_payload",
)
