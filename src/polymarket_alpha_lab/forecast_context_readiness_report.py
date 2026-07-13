"""Read-only forecast input-context readiness reports.

This module is a Phase 1 pure transform. It checks whether forecast inputs have
enough public context before naive, book-imbalance, LLM, or superforecaster
forecast generation proceeds. It does not fetch, persist, rank, recommend,
execute, or mutate any upstream forecast state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


ZERO = Decimal("0")
ONE = Decimal("1")
COUNT_QUANT = Decimal("1")
DECIMAL_QUANT = Decimal("0.000001")
MASK = "<redacted>"
DEFAULT_MINIMUM_COUNTS = (Decimal("2"), Decimal("2"))
MICROSTRUCTURE_MINIMUM_COUNTS = (Decimal("1"), Decimal("1"))
SUPERFORECASTER_MINIMUM_COUNTS = (Decimal("3"), Decimal("3"))
CONFIG_MINIMUM_COUNTS = (
    ("default_min_source_count", DEFAULT_MINIMUM_COUNTS[0]),
    ("default_min_source_family_count", DEFAULT_MINIMUM_COUNTS[1]),
    ("microstructure_min_source_count", MICROSTRUCTURE_MINIMUM_COUNTS[0]),
    ("microstructure_min_source_family_count", MICROSTRUCTURE_MINIMUM_COUNTS[1]),
    ("superforecaster_min_source_count", SUPERFORECASTER_MINIMUM_COUNTS[0]),
    ("superforecaster_min_source_family_count", SUPERFORECASTER_MINIMUM_COUNTS[1]),
)

SUPPORTED_MODEL_BASIS = (
    "yes_ask_naive_v0",
    "book_imbalance_v0",
    "llm_glm_v0",
    "superforecaster_prompt_v0",
)
PUBLIC_STATUSES = ("pass", "watch", "block")
STANCE_VALUES = ("neutral", "market_data", "supports_yes", "supports_no")
REASON_CODES = (
    "context_complete",
    "source_count_below_minimum",
    "source_family_count_below_minimum",
    "source_citations_ready",
    "source_citation_missing",
    "source_timestamps_ready",
    "source_timestamp_missing",
    "context_timestamp_missing",
    "fallback_path_ready",
    "fallback_path_missing",
    "conflicting_evidence_resolved",
    "conflicting_evidence_unresolved",
    "unsafe_public_content_redacted",
    "public_status_pass",
    "public_status_watch",
    "public_status_block",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "api_token",
    "auth",
    "bearer",
    "credential",
    "password",
    "private_key",
    "secret",
    "token=",
    "wallet",
)
_PUBLIC_DATACLASS_NAMES = frozenset(
    {
        "ForecastContextReadinessConfig",
        "ForecastContextSource",
        "ForecastContextReadinessInput",
        "ForecastContextReadinessRow",
        "ForecastContextReadinessReport",
    },
)
_PUBLIC_DATACLASS_REGISTRY: set[str] = set()


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__bases__ != (_FinalPublicDataclass,):
            raise TypeError("subclassing is not allowed")
        if cls.__module__ != __name__ or cls.__name__ not in _PUBLIC_DATACLASS_NAMES:
            raise TypeError("subclassing is not allowed")
        if cls.__name__ in _PUBLIC_DATACLASS_REGISTRY:
            raise TypeError("public dataclass is already registered")
        _PUBLIC_DATACLASS_REGISTRY.add(cls.__name__)


@dataclass(frozen=True)
class ForecastContextReadinessConfig(_FinalPublicDataclass):
    config_version: str = "forecast-context-readiness-v1"
    default_min_source_count: Decimal = DEFAULT_MINIMUM_COUNTS[0]
    default_min_source_family_count: Decimal = DEFAULT_MINIMUM_COUNTS[1]
    microstructure_min_source_count: Decimal = MICROSTRUCTURE_MINIMUM_COUNTS[0]
    microstructure_min_source_family_count: Decimal = MICROSTRUCTURE_MINIMUM_COUNTS[1]
    superforecaster_min_source_count: Decimal = SUPERFORECASTER_MINIMUM_COUNTS[0]
    superforecaster_min_source_family_count: Decimal = SUPERFORECASTER_MINIMUM_COUNTS[1]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ForecastContextReadinessConfig)
        object.__setattr__(
            self,
            "config_version",
            _normalize_public_string("config_version", self.config_version),
        )
        for field_name in (
            "default_min_source_count",
            "default_min_source_family_count",
            "microstructure_min_source_count",
            "microstructure_min_source_family_count",
            "superforecaster_min_source_count",
            "superforecaster_min_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name, minimum in CONFIG_MINIMUM_COUNTS:
            if getattr(self, field_name) < minimum:
                raise ValueError(f"{field_name} must be at least {minimum:f}")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ForecastContextSource(_FinalPublicDataclass):
    source_label: str
    source_family: str
    citation: str | None
    published_at: datetime | None
    captured_at: datetime | None
    stance: str = "neutral"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("source", self, ForecastContextSource)
        object.__setattr__(
            self,
            "source_label",
            _normalize_public_string("source_label", self.source_label),
        )
        object.__setattr__(
            self,
            "source_family",
            _normalize_public_string("source_family", self.source_family),
        )
        if self.citation is not None:
            object.__setattr__(
                self,
                "citation",
                _normalize_public_string("citation", self.citation),
            )
        object.__setattr__(
            self,
            "published_at",
            _normalize_optional_datetime("published_at", self.published_at),
        )
        object.__setattr__(
            self,
            "captured_at",
            _normalize_optional_datetime("captured_at", self.captured_at),
        )
        _require_not_after(
            "published_at",
            self.published_at,
            "captured_at",
            self.captured_at,
        )
        _require_member("stance", self.stance, STANCE_VALUES)
        _require_hard_flags("source", self)


@dataclass(frozen=True)
class ForecastContextReadinessInput(_FinalPublicDataclass):
    model_basis: str
    market_slug: str
    question: str
    context_captured_at: datetime | None
    sources: tuple[ForecastContextSource, ...]
    fallback_path: str | None
    conflict_resolution: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("input", self, ForecastContextReadinessInput)
        _require_model_basis(self.model_basis)
        object.__setattr__(
            self,
            "market_slug",
            _normalize_public_string("market_slug", self.market_slug),
        )
        object.__setattr__(
            self,
            "question",
            _normalize_public_string("question", self.question),
        )
        object.__setattr__(
            self,
            "context_captured_at",
            _normalize_optional_datetime(
                "context_captured_at",
                self.context_captured_at,
            ),
        )
        object.__setattr__(self, "sources", _normalize_sources(self.sources))
        _require_source_times_not_after(
            self.sources,
            boundary_name="context_captured_at",
            boundary=self.context_captured_at,
        )
        if self.fallback_path is not None:
            object.__setattr__(
                self,
                "fallback_path",
                _normalize_public_string("fallback_path", self.fallback_path),
            )
        if self.conflict_resolution is not None:
            object.__setattr__(
                self,
                "conflict_resolution",
                _normalize_public_string(
                    "conflict_resolution",
                    self.conflict_resolution,
                ),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ForecastContextReadinessRow(_FinalPublicDataclass):
    model_basis: str
    market_slug: str
    question: str
    context_captured_at: datetime | None
    status: str
    readiness_score: Decimal
    minimum_source_count: Decimal
    minimum_source_family_count: Decimal
    source_count: Decimal
    cited_source_count: Decimal
    timestamped_source_count: Decimal
    source_family_count: Decimal
    conflicting_evidence_count: Decimal
    fallback_path: str | None
    conflict_resolution: str | None
    sources: tuple[ForecastContextSource, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ForecastContextReadinessRow)
        _require_model_basis(self.model_basis)
        object.__setattr__(
            self,
            "market_slug",
            _normalize_public_string("market_slug", self.market_slug),
        )
        object.__setattr__(
            self,
            "question",
            _normalize_public_string("question", self.question),
        )
        object.__setattr__(
            self,
            "context_captured_at",
            _normalize_optional_datetime(
                "context_captured_at",
                self.context_captured_at,
            ),
        )
        _require_member("status", self.status, PUBLIC_STATUSES)
        object.__setattr__(
            self,
            "readiness_score",
            _normalize_probability("readiness_score", self.readiness_score),
        )
        for field_name in (
            "minimum_source_count",
            "minimum_source_family_count",
            "source_count",
            "cited_source_count",
            "timestamped_source_count",
            "source_family_count",
            "conflicting_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.fallback_path is not None:
            object.__setattr__(
                self,
                "fallback_path",
                _normalize_public_string("fallback_path", self.fallback_path),
            )
        if self.conflict_resolution is not None:
            object.__setattr__(
                self,
                "conflict_resolution",
                _normalize_public_string(
                    "conflict_resolution",
                    self.conflict_resolution,
                ),
            )
        object.__setattr__(self, "sources", _normalize_sources(self.sources))
        _require_source_times_not_after(
            self.sources,
            boundary_name="context_captured_at",
            boundary=self.context_captured_at,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row_derivations(self)

    @property
    def payload(self) -> dict[str, Any]:
        return _row_payload(self)


@dataclass(frozen=True)
class ForecastContextReadinessReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    rows: tuple[ForecastContextReadinessRow, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ForecastContextReadinessReport)
        object.__setattr__(
            self,
            "generated_at",
            _normalize_datetime("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "config_version",
            _normalize_public_string("config_version", self.config_version),
        )
        _require_member("status", self.status, PUBLIC_STATUSES)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_row_times_not_after_generated_at(self.rows, self.generated_at)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report_derivations(self)

    @property
    def payload(self) -> dict[str, Any]:
        _validate_report_for_output(self)
        _require_row_times_not_after_generated_at(self.rows, self.generated_at)
        return {
            "generated_at": self.generated_at.isoformat(),
            "config_version": self.config_version,
            "status": self.status,
            "rows": [_row_payload(row) for row in self.rows],
            "reason_codes": list(self.reason_codes),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }


def build_forecast_context_readiness_report(
    inputs: tuple[ForecastContextReadinessInput, ...],
    *,
    generated_at: datetime,
    config: ForecastContextReadinessConfig,
) -> ForecastContextReadinessReport:
    normalized_generated_at = _normalize_datetime("generated_at", generated_at)
    _require_exact_type("config", config, ForecastContextReadinessConfig)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(_row_for_input(value, config) for value in normalized_inputs)
    status = _aggregate_status(tuple(row.status for row in rows))
    reason_codes = _report_reason_codes(rows, status)
    return ForecastContextReadinessReport(
        generated_at=normalized_generated_at,
        config_version=config.config_version,
        status=status,
        rows=rows,
        reason_codes=reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def forecast_context_readiness_report_payload(
    report: ForecastContextReadinessReport,
) -> dict[str, Any]:
    _require_exact_type("report", report, ForecastContextReadinessReport)
    return report.payload


def _row_for_input(
    value: ForecastContextReadinessInput,
    config: ForecastContextReadinessConfig,
) -> ForecastContextReadinessRow:
    min_source_count, min_family_count = _thresholds(value.model_basis, config)
    derived = _derive_row_context(
        market_slug=value.market_slug,
        question=value.question,
        context_captured_at=value.context_captured_at,
        sources=value.sources,
        fallback_path=value.fallback_path,
        conflict_resolution=value.conflict_resolution,
        minimum_source_count=min_source_count,
        minimum_source_family_count=min_family_count,
    )
    return ForecastContextReadinessRow(
        model_basis=value.model_basis,
        market_slug=value.market_slug,
        question=value.question,
        context_captured_at=value.context_captured_at,
        status=derived.status,
        readiness_score=derived.readiness_score,
        minimum_source_count=min_source_count,
        minimum_source_family_count=min_family_count,
        source_count=derived.source_count,
        cited_source_count=derived.cited_source_count,
        timestamped_source_count=derived.timestamped_source_count,
        source_family_count=derived.source_family_count,
        conflicting_evidence_count=derived.conflicting_evidence_count,
        fallback_path=value.fallback_path,
        conflict_resolution=value.conflict_resolution,
        sources=value.sources,
        reason_codes=derived.reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


@dataclass(frozen=True)
class _DerivedRowContext:
    source_count: Decimal
    cited_source_count: Decimal
    timestamped_source_count: Decimal
    source_family_count: Decimal
    conflicting_evidence_count: Decimal
    status: str
    readiness_score: Decimal
    reason_codes: tuple[str, ...]


def _derive_row_context(
    *,
    market_slug: str,
    question: str,
    context_captured_at: datetime | None,
    sources: tuple[ForecastContextSource, ...],
    fallback_path: str | None,
    conflict_resolution: str | None,
    minimum_source_count: Decimal,
    minimum_source_family_count: Decimal,
) -> _DerivedRowContext:
    source_count = Decimal(len(sources)).quantize(COUNT_QUANT)
    cited_source_count = Decimal(
        sum(1 for source in sources if source.citation is not None),
    ).quantize(COUNT_QUANT)
    timestamped_source_count = Decimal(
        sum(
            1
            for source in sources
            if source.published_at is not None or source.captured_at is not None
        ),
    ).quantize(COUNT_QUANT)
    source_family_count = Decimal(
        len({source.source_family for source in sources}),
    ).quantize(COUNT_QUANT)
    conflicting_evidence_count = Decimal(
        _conflicting_evidence_count(sources),
    ).quantize(COUNT_QUANT)
    has_unresolved_conflict = (
        conflicting_evidence_count > ZERO and conflict_resolution is None
    )
    has_resolved_conflict = (
        conflicting_evidence_count > ZERO and conflict_resolution is not None
    )
    has_unsafe_public_content = _has_redacted_public_value(
        (market_slug, question, sources, fallback_path, conflict_resolution),
    )

    reason_codes: list[str] = []
    blocking_codes: list[str] = []
    watch_codes: list[str] = []

    if source_count < minimum_source_count:
        code = "source_count_below_minimum"
        reason_codes.append(code)
        blocking_codes.append(code)
    if source_family_count < minimum_source_family_count:
        code = "source_family_count_below_minimum"
        reason_codes.append(code)
        blocking_codes.append(code)
    if cited_source_count < source_count:
        code = "source_citation_missing"
        reason_codes.append(code)
        blocking_codes.append(code)
    elif source_count > ZERO:
        reason_codes.append("source_citations_ready")
    if timestamped_source_count < source_count:
        code = "source_timestamp_missing"
        reason_codes.append(code)
        blocking_codes.append(code)
    elif source_count > ZERO:
        reason_codes.append("source_timestamps_ready")
    if context_captured_at is None:
        code = "context_timestamp_missing"
        reason_codes.append(code)
        blocking_codes.append(code)
    if fallback_path is None:
        code = "fallback_path_missing"
        reason_codes.append(code)
        blocking_codes.append(code)
    else:
        reason_codes.append("fallback_path_ready")
    if has_unresolved_conflict:
        code = "conflicting_evidence_unresolved"
        reason_codes.append(code)
        blocking_codes.append(code)
    elif has_resolved_conflict:
        code = "conflicting_evidence_resolved"
        reason_codes.append(code)
        watch_codes.append(code)
    if has_unsafe_public_content:
        code = "unsafe_public_content_redacted"
        reason_codes.append(code)
        blocking_codes.append(code)
    if not blocking_codes and not watch_codes:
        reason_codes.insert(0, "context_complete")

    status = "block" if blocking_codes else "watch" if watch_codes else "pass"
    reason_codes.append(f"public_status_{status}")
    return _DerivedRowContext(
        source_count=source_count,
        cited_source_count=cited_source_count,
        timestamped_source_count=timestamped_source_count,
        source_family_count=source_family_count,
        conflicting_evidence_count=conflicting_evidence_count,
        status=status,
        readiness_score=_readiness_score(status),
        reason_codes=tuple(reason_codes),
    )


def _validate_row_derivations(row: ForecastContextReadinessRow) -> None:
    _require_member("status", row.status, PUBLIC_STATUSES)
    _normalize_probability("readiness_score", row.readiness_score)
    for field_name in (
        "minimum_source_count",
        "minimum_source_family_count",
        "source_count",
        "cited_source_count",
        "timestamped_source_count",
        "source_family_count",
        "conflicting_evidence_count",
    ):
        _normalize_nonnegative_count(field_name, getattr(row, field_name))
    _require_model_basis_threshold_floors(
        row.model_basis,
        minimum_source_count=row.minimum_source_count,
        minimum_source_family_count=row.minimum_source_family_count,
    )
    _normalize_reason_codes(row.reason_codes)

    derived = _derive_row_context(
        market_slug=row.market_slug,
        question=row.question,
        context_captured_at=row.context_captured_at,
        sources=row.sources,
        fallback_path=row.fallback_path,
        conflict_resolution=row.conflict_resolution,
        minimum_source_count=row.minimum_source_count,
        minimum_source_family_count=row.minimum_source_family_count,
    )
    for field_name in (
        "source_count",
        "cited_source_count",
        "timestamped_source_count",
        "source_family_count",
        "conflicting_evidence_count",
    ):
        if getattr(row, field_name) != getattr(derived, field_name):
            raise ValueError(f"{field_name} must match row context")
    if row.status != derived.status:
        raise ValueError("status must match row context")
    if row.readiness_score != derived.readiness_score:
        raise ValueError("readiness_score must match row context")
    if row.reason_codes != derived.reason_codes:
        raise ValueError("reason_codes must match row context")


def _validate_row_for_output(row: ForecastContextReadinessRow) -> None:
    _require_exact_type("row", row, ForecastContextReadinessRow)
    _require_model_basis(row.model_basis)
    _normalize_public_string("market_slug", row.market_slug)
    _normalize_public_string("question", row.question)
    _normalize_optional_datetime("context_captured_at", row.context_captured_at)
    _normalize_sources(row.sources)
    for source in row.sources:
        _validate_source_for_output(source)
    _require_source_times_not_after(
        row.sources,
        boundary_name="context_captured_at",
        boundary=row.context_captured_at,
    )
    if row.fallback_path is not None:
        _normalize_public_string("fallback_path", row.fallback_path)
    if row.conflict_resolution is not None:
        _normalize_public_string("conflict_resolution", row.conflict_resolution)
    _require_hard_flags("row", row)
    _validate_row_derivations(row)


def _validate_source_for_output(source: ForecastContextSource) -> None:
    _require_exact_type("source", source, ForecastContextSource)
    _require_normalized_public_string_for_output(
        "source_label",
        source.source_label,
    )
    _require_normalized_public_string_for_output(
        "source_family",
        source.source_family,
    )
    if source.citation is not None:
        _require_normalized_public_string_for_output("citation", source.citation)
    _require_normalized_optional_datetime_for_output(
        "published_at",
        source.published_at,
    )
    _require_normalized_optional_datetime_for_output(
        "captured_at",
        source.captured_at,
    )
    _require_not_after(
        "published_at",
        source.published_at,
        "captured_at",
        source.captured_at,
    )
    _require_member("stance", source.stance, STANCE_VALUES)
    _require_hard_flags("source", source)


def _require_normalized_public_string_for_output(
    field_name: str,
    value: object,
) -> None:
    normalized = _normalize_public_string(field_name, value)
    if value != normalized:
        raise ValueError(f"{field_name} must already be normalized public text")


def _require_normalized_optional_datetime_for_output(
    field_name: str,
    value: object,
) -> None:
    normalized = _normalize_optional_datetime(field_name, value)
    if normalized is not None and value.tzinfo is not UTC:
        raise ValueError(f"{field_name} must already be normalized to UTC")


def _validate_report_derivations(report: ForecastContextReadinessReport) -> None:
    for row in report.rows:
        _validate_row_derivations(row)
    expected_status = _aggregate_status(tuple(row.status for row in report.rows))
    if report.status != expected_status:
        raise ValueError("status must match rows")
    expected_reason_codes = _report_reason_codes(report.rows, expected_status)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")


def _validate_report_for_output(report: ForecastContextReadinessReport) -> None:
    _require_exact_type("report", report, ForecastContextReadinessReport)
    _normalize_datetime("generated_at", report.generated_at)
    _normalize_public_string("config_version", report.config_version)
    _require_member("status", report.status, PUBLIC_STATUSES)
    _normalize_rows(report.rows)
    _normalize_reason_codes(report.reason_codes)
    _require_hard_flags("report", report)
    for row in report.rows:
        _validate_row_for_output(row)
    _require_row_times_not_after_generated_at(report.rows, report.generated_at)
    _validate_report_derivations(report)


def _thresholds(
    model_basis: str,
    config: ForecastContextReadinessConfig,
) -> tuple[Decimal, Decimal]:
    if model_basis in ("yes_ask_naive_v0", "book_imbalance_v0"):
        return (
            config.microstructure_min_source_count,
            config.microstructure_min_source_family_count,
        )
    if model_basis == "superforecaster_prompt_v0":
        return (
            config.superforecaster_min_source_count,
            config.superforecaster_min_source_family_count,
        )
    return (config.default_min_source_count, config.default_min_source_family_count)


def _require_model_basis_threshold_floors(
    model_basis: str,
    *,
    minimum_source_count: Decimal,
    minimum_source_family_count: Decimal,
) -> None:
    if model_basis in ("yes_ask_naive_v0", "book_imbalance_v0"):
        floors = MICROSTRUCTURE_MINIMUM_COUNTS
    elif model_basis == "superforecaster_prompt_v0":
        floors = SUPERFORECASTER_MINIMUM_COUNTS
    else:
        floors = DEFAULT_MINIMUM_COUNTS
    for field_name, value, floor in (
        ("minimum_source_count", minimum_source_count, floors[0]),
        ("minimum_source_family_count", minimum_source_family_count, floors[1]),
    ):
        if value < floor:
            raise ValueError(
                f"{field_name} must be at least {floor:f} for model_basis {model_basis}",
            )


def _conflicting_evidence_count(
    sources: tuple[ForecastContextSource, ...],
) -> int:
    stances = {source.stance for source in sources}
    if "supports_yes" in stances and "supports_no" in stances:
        return 1
    return 0


def _readiness_score(status: str) -> Decimal:
    if status == "pass":
        return Decimal("1.000000")
    if status == "watch":
        return Decimal("0.500000")
    return Decimal("0.000000")


def _aggregate_status(statuses: tuple[str, ...]) -> str:
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ForecastContextReadinessRow, ...],
    status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for row in rows:
        for code in row.reason_codes:
            if code not in reason_codes and not code.startswith("public_status_"):
                reason_codes.append(code)
    reason_codes.append(f"public_status_{status}")
    return tuple(reason_codes)


def _row_payload(row: ForecastContextReadinessRow) -> dict[str, Any]:
    _validate_row_for_output(row)
    return {
        "model_basis": row.model_basis,
        "market_slug": row.market_slug,
        "question": row.question,
        "context_captured_at": (
            row.context_captured_at.isoformat()
            if row.context_captured_at is not None
            else None
        ),
        "status": row.status,
        "readiness_score": str(row.readiness_score),
        "minimum_source_count": str(row.minimum_source_count),
        "minimum_source_family_count": str(row.minimum_source_family_count),
        "source_count": str(row.source_count),
        "cited_source_count": str(row.cited_source_count),
        "timestamped_source_count": str(row.timestamped_source_count),
        "source_family_count": str(row.source_family_count),
        "conflicting_evidence_count": str(row.conflicting_evidence_count),
        "fallback_path": row.fallback_path,
        "conflict_resolution": row.conflict_resolution,
        "sources": [_source_payload(source) for source in row.sources],
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _source_payload(source: ForecastContextSource) -> dict[str, Any]:
    _validate_source_for_output(source)
    return {
        "source_label": source.source_label,
        "source_family": source.source_family,
        "citation": source.citation,
        "published_at": (
            source.published_at.isoformat() if source.published_at is not None else None
        ),
        "captured_at": (
            source.captured_at.isoformat() if source.captured_at is not None else None
        ),
        "stance": source.stance,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _normalize_inputs(
    values: tuple[ForecastContextReadinessInput, ...],
) -> tuple[ForecastContextReadinessInput, ...]:
    if type(values) is not tuple:
        raise ValueError("inputs must be a tuple")
    if not values:
        raise ValueError("inputs must not be empty")
    for value in values:
        _require_exact_type("inputs", value, ForecastContextReadinessInput)
    return values


def _normalize_rows(
    values: tuple[ForecastContextReadinessRow, ...],
) -> tuple[ForecastContextReadinessRow, ...]:
    if type(values) is not tuple:
        raise ValueError("rows must be a tuple")
    if not values:
        raise ValueError("rows must not be empty")
    for value in values:
        _require_exact_type("rows", value, ForecastContextReadinessRow)
    return values


def _normalize_sources(values: object) -> tuple[ForecastContextSource, ...]:
    if type(values) is not tuple:
        raise ValueError("sources must be a tuple")
    for value in values:
        _require_exact_type("sources", value, ForecastContextSource)
    return values


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must not be empty")
    normalized = tuple(_normalize_public_string("reason_codes", value) for value in values)
    for value in normalized:
        if value not in REASON_CODES:
            raise ValueError("reason_codes contains unsupported value")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes contains duplicate value")
    return normalized


def _normalize_optional_datetime(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _normalize_datetime(field_name, value)


def _normalize_datetime(field_name: str, value: object) -> datetime:
    error_message = f"{field_name} must be an exact timezone-aware datetime"
    if type(value) is not datetime or value.tzinfo is None:
        raise ValueError(error_message)
    try:
        offset = value.utcoffset()
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValueError(error_message) from exc
    if offset is None:
        raise ValueError(error_message)
    try:
        return value.astimezone(UTC)
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValueError(error_message) from exc


def _require_not_after(
    value_name: str,
    value: datetime | None,
    boundary_name: str,
    boundary: datetime | None,
) -> None:
    if value is not None and boundary is not None and value > boundary:
        raise ValueError(f"{value_name} must not be later than {boundary_name}")


def _require_source_times_not_after(
    sources: tuple[ForecastContextSource, ...],
    *,
    boundary_name: str,
    boundary: datetime | None,
) -> None:
    for source in sources:
        _require_not_after(
            "published_at",
            source.published_at,
            boundary_name,
            boundary,
        )
        _require_not_after(
            "captured_at",
            source.captured_at,
            boundary_name,
            boundary,
        )


def _require_row_times_not_after_generated_at(
    rows: tuple[ForecastContextReadinessRow, ...],
    generated_at: datetime,
) -> None:
    for row in rows:
        _require_not_after(
            "context_captured_at",
            row.context_captured_at,
            "generated_at",
            generated_at,
        )
        _require_source_times_not_after(
            row.sources,
            boundary_name="generated_at",
            boundary=generated_at,
        )


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    normalized = decimal_value.quantize(COUNT_QUANT)
    if normalized != decimal_value:
        raise ValueError(f"{field_name} must be a whole Decimal count")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    return _require_decimal(field_name, value).quantize(DECIMAL_QUANT)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_model_basis(value: object) -> None:
    if type(value) is not str or value not in SUPPORTED_MODEL_BASIS:
        raise ValueError("model_basis must be a supported forecast basis")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _normalize_public_string(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if _contains_unsafe_public_text(value):
        return MASK
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or not value
        or value.strip() != value
        or "\n" in value
        or "\r" in value
        or "\t" in value
    ):
        raise ValueError(f"{field_name} must contain canonical strings")


def _require_exact_type(
    field_name: str,
    value: object,
    expected_type: type[object],
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _has_redacted_public_value(value: object) -> bool:
    if isinstance(value, str):
        return value == MASK
    if isinstance(value, Decimal):
        return False
    if isinstance(value, datetime):
        return False
    if isinstance(value, bool):
        return False
    if value is None:
        return False
    if isinstance(value, tuple):
        return any(_has_redacted_public_value(item) for item in value)
    if hasattr(value, "__dataclass_fields__"):
        return any(
            _has_redacted_public_value(getattr(value, field_name))
            for field_name in value.__dataclass_fields__
        )
    return False


def _contains_unsafe_public_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS)


__all__ = (
    "MASK",
    "PUBLIC_STATUSES",
    "REASON_CODES",
    "SUPPORTED_MODEL_BASIS",
    "ForecastContextReadinessConfig",
    "ForecastContextReadinessInput",
    "ForecastContextReadinessReport",
    "ForecastContextReadinessRow",
    "ForecastContextSource",
    "build_forecast_context_readiness_report",
    "forecast_context_readiness_report_payload",
)
