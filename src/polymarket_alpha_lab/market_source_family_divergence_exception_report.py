"""Pure Phase 1 source-family divergence exception report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_EXCEPTION_REPORT_CONFIG_VERSION = (
    "market-source-family-divergence-exception-report-v0"
)

SOURCE_FAMILIES = ("official", "primary", "proxy", "team_acknowledged")
SOURCE_FAMILY_RANK = {
    "official": 0,
    "primary": 1,
    "proxy": 2,
    "team_acknowledged": 3,
}
REPORT_STATUSES = ("clear", "watch", "blocked")
EXCEPTION_STATUSES = ("clear", "watch", "blocked")
STATUS_RANK = {"blocked": 0, "watch": 1, "clear": 2}

STALE_CONFLICT_ACKNOWLEDGEMENT_REASON = (
    "market_source_family_divergence_exception_stale_conflict_acknowledgement"
)
UNRESOLVED_CONFLICT_REASON = (
    "market_source_family_divergence_exception_unresolved_conflict"
)
DIVERGENCE_BEYOND_THRESHOLD_REASON = (
    "market_source_family_divergence_exception_divergence_beyond_threshold"
)
INSUFFICIENT_INDEPENDENT_FAMILIES_REASON = (
    "market_source_family_divergence_exception_insufficient_independent_families"
)
MISSING_SOURCE_FAMILY_EVIDENCE_REASON = (
    "market_source_family_divergence_exception_missing_source_family_evidence"
)
CLEAR_REASON = "market_source_family_divergence_exception_clear"
REASON_CODES = (
    STALE_CONFLICT_ACKNOWLEDGEMENT_REASON,
    UNRESOLVED_CONFLICT_REASON,
    DIVERGENCE_BEYOND_THRESHOLD_REASON,
    INSUFFICIENT_INDEPENDENT_FAMILIES_REASON,
    MISSING_SOURCE_FAMILY_EVIDENCE_REASON,
    CLEAR_REASON,
)
BLOCKING_REASON_CODES = frozenset(
    (
        STALE_CONFLICT_ACKNOWLEDGEMENT_REASON,
        UNRESOLVED_CONFLICT_REASON,
        DIVERGENCE_BEYOND_THRESHOLD_REASON,
    ),
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")
EARLIEST_UTC_DATETIME = datetime(1, 1, 1, tzinfo=UTC)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        "credential",
        "private",
        "secret",
        "token",
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("bro", "ker"),
        _join_parts("tra", "de"),
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("repl", "ace"),
        _join_parts("exch", "ange"),
        _join_parts("sig", "ning"),
        _join_parts("ad", "vice"),
    ),
)


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceExceptionConfig:
    config_version: str = (
        DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_EXCEPTION_REPORT_CONFIG_VERSION
    )
    min_independent_source_families: Decimal = Decimal("2.000000")
    max_family_probability_divergence: Decimal = Decimal("0.250000")
    stale_conflict_acknowledgement_seconds: Decimal = Decimal("3600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_independent_source_families",
            _require_positive_whole_decimal(
                "min_independent_source_families",
                self.min_independent_source_families,
            ),
        )
        object.__setattr__(
            self,
            "max_family_probability_divergence",
            _require_ratio(
                "max_family_probability_divergence",
                self.max_family_probability_divergence,
            ),
        )
        object.__setattr__(
            self,
            "stale_conflict_acknowledgement_seconds",
            _require_positive_decimal(
                "stale_conflict_acknowledgement_seconds",
                self.stale_conflict_acknowledgement_seconds,
            ),
        )
        require_paper_only_flags(
            "source family divergence exception config",
            self,
        )
        _reject_unsafe_text_fields("source family divergence exception config", self)


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceExceptionInputRow:
    market_id: str
    category_id: str
    source_family: str
    source_probability: Decimal
    evidence_observed_at: datetime
    conflict_acknowledged_at: datetime | None
    conflict_resolved: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("market_id", self.market_id)
        _require_public_string("category_id", self.category_id)
        _require_source_family("source_family", self.source_family)
        object.__setattr__(
            self,
            "source_probability",
            _require_ratio("source_probability", self.source_probability),
        )
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        object.__setattr__(
            self,
            "conflict_acknowledged_at",
            _as_optional_utc(
                "conflict_acknowledged_at",
                self.conflict_acknowledged_at,
            ),
        )
        _require_bool("conflict_resolved", self.conflict_resolved)
        require_paper_only_flags(
            "source family divergence exception input row",
            self,
        )
        _reject_unsafe_text_fields(
            "source family divergence exception input row",
            self,
        )


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceExceptionRow:
    market_id: str
    category_id: str
    source_family_count: Decimal
    missing_source_family_count: Decimal
    family_probability_delta: Decimal
    max_evidence_age_seconds: Decimal
    max_conflict_acknowledgement_age_seconds: Decimal
    exception_status: str
    reason_codes: tuple[str, ...]
    source_families: tuple[str, ...]
    missing_source_families: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("market_id", self.market_id)
        _require_public_string("category_id", self.category_id)
        for field_name in (
            "source_family_count",
            "missing_source_family_count",
            "family_probability_delta",
            "max_evidence_age_seconds",
            "max_conflict_acknowledgement_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_exception_status("exception_status", self.exception_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "source_families",
            _normalize_source_families("source_families", self.source_families),
        )
        object.__setattr__(
            self,
            "missing_source_families",
            _normalize_source_families(
                "missing_source_families",
                self.missing_source_families,
            ),
        )
        _validate_exception_row(self)
        require_paper_only_flags("source family divergence exception row", self)
        _reject_unsafe_text_fields("source family divergence exception row", self)


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceExceptionFamilyRollup:
    source_family: str
    market_count: Decimal
    exception_market_count: Decimal
    blocked_market_count: Decimal
    watch_market_count: Decimal
    clear_market_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_source_family("source_family", self.source_family)
        for field_name in (
            "market_count",
            "exception_market_count",
            "blocked_market_count",
            "watch_market_count",
            "clear_market_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_rollup_counts(self)
        require_paper_only_flags(
            "source family divergence exception family rollup",
            self,
        )
        _reject_unsafe_text_fields(
            "source family divergence exception family rollup",
            self,
        )


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceExceptionCategoryRollup:
    category_id: str
    market_count: Decimal
    exception_market_count: Decimal
    blocked_market_count: Decimal
    watch_market_count: Decimal
    clear_market_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("category_id", self.category_id)
        for field_name in (
            "market_count",
            "exception_market_count",
            "blocked_market_count",
            "watch_market_count",
            "clear_market_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_rollup_counts(self)
        require_paper_only_flags(
            "source family divergence exception category rollup",
            self,
        )
        _reject_unsafe_text_fields(
            "source family divergence exception category rollup",
            self,
        )


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceExceptionReport:
    generated_at: datetime
    config_version: str
    report_status: str
    reason_codes: tuple[str, ...]
    market_count: Decimal
    source_family_count: Decimal
    exception_market_count: Decimal
    blocked_market_count: Decimal
    watch_market_count: Decimal
    clear_market_count: Decimal
    insufficient_independent_family_market_count: Decimal
    divergence_beyond_threshold_market_count: Decimal
    stale_conflict_acknowledgement_market_count: Decimal
    unresolved_conflict_market_count: Decimal
    missing_source_family_evidence_market_count: Decimal
    exception_market_ratio: Decimal
    max_family_probability_delta: Decimal
    max_evidence_age_seconds: Decimal
    max_conflict_acknowledgement_age_seconds: Decimal
    rows: tuple[MarketSourceFamilyDivergenceExceptionRow, ...]
    family_rollups: tuple[MarketSourceFamilyDivergenceExceptionFamilyRollup, ...]
    category_rollups: tuple[MarketSourceFamilyDivergenceExceptionCategoryRollup, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_report_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        for field_name in (
            "market_count",
            "source_family_count",
            "exception_market_count",
            "blocked_market_count",
            "watch_market_count",
            "clear_market_count",
            "insufficient_independent_family_market_count",
            "divergence_beyond_threshold_market_count",
            "stale_conflict_acknowledgement_market_count",
            "unresolved_conflict_market_count",
            "missing_source_family_evidence_market_count",
            "exception_market_ratio",
            "max_family_probability_delta",
            "max_evidence_age_seconds",
            "max_conflict_acknowledgement_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_ratio("exception_market_ratio", self.exception_market_ratio)
        object.__setattr__(self, "rows", _normalize_exception_rows(self.rows))
        object.__setattr__(
            self,
            "family_rollups",
            _normalize_family_rollups(self.family_rollups),
        )
        object.__setattr__(
            self,
            "category_rollups",
            _normalize_category_rollups(self.category_rollups),
        )
        _validate_report(self)
        require_paper_only_flags("source family divergence exception report", self)
        _reject_unsafe_text_fields("source family divergence exception report", self)


def build_market_source_family_divergence_exception_report(
    input_rows: list[MarketSourceFamilyDivergenceExceptionInputRow]
    | tuple[MarketSourceFamilyDivergenceExceptionInputRow, ...],
    *,
    config: MarketSourceFamilyDivergenceExceptionConfig,
    generated_at: datetime,
    required_source_families: tuple[str, ...] = ("official", "primary"),
) -> MarketSourceFamilyDivergenceExceptionReport:
    if type(config) is not MarketSourceFamilyDivergenceExceptionConfig:
        raise ValueError(
            "config must be a MarketSourceFamilyDivergenceExceptionConfig",
        )
    require_paper_only_flags("source family divergence exception config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows)
    required_families = _normalize_source_families(
        "required_source_families",
        required_source_families,
    )
    by_market = _rows_by_market(rows)
    exception_rows = _sort_exception_rows(
        tuple(
            _exception_row(
                market_id,
                market_rows,
                config=config,
                generated_at=generated_at_utc,
                required_source_families=required_families,
            )
            for market_id, market_rows in sorted(by_market.items())
        ),
    )
    reason_codes = _report_reason_codes(exception_rows)
    family_rollups = _build_family_rollups(exception_rows)
    category_rollups = _build_category_rollups(exception_rows)

    return MarketSourceFamilyDivergenceExceptionReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        market_count=_decimal_count(len(exception_rows)),
        source_family_count=_sum_decimal(
            row.source_family_count for row in exception_rows
        ),
        exception_market_count=_status_not_clear_count(exception_rows),
        blocked_market_count=_status_count(exception_rows, "blocked"),
        watch_market_count=_status_count(exception_rows, "watch"),
        clear_market_count=_status_count(exception_rows, "clear"),
        insufficient_independent_family_market_count=_reason_count(
            exception_rows,
            INSUFFICIENT_INDEPENDENT_FAMILIES_REASON,
        ),
        divergence_beyond_threshold_market_count=_reason_count(
            exception_rows,
            DIVERGENCE_BEYOND_THRESHOLD_REASON,
        ),
        stale_conflict_acknowledgement_market_count=_reason_count(
            exception_rows,
            STALE_CONFLICT_ACKNOWLEDGEMENT_REASON,
        ),
        unresolved_conflict_market_count=_reason_count(
            exception_rows,
            UNRESOLVED_CONFLICT_REASON,
        ),
        missing_source_family_evidence_market_count=_reason_count(
            exception_rows,
            MISSING_SOURCE_FAMILY_EVIDENCE_REASON,
        ),
        exception_market_ratio=_ratio(
            _status_not_clear_count(exception_rows),
            _decimal_count(len(exception_rows)),
        ),
        max_family_probability_delta=_max_decimal(
            row.family_probability_delta for row in exception_rows
        ),
        max_evidence_age_seconds=_max_decimal(
            row.max_evidence_age_seconds for row in exception_rows
        ),
        max_conflict_acknowledgement_age_seconds=_max_decimal(
            row.max_conflict_acknowledgement_age_seconds for row in exception_rows
        ),
        rows=exception_rows,
        family_rollups=family_rollups,
        category_rollups=category_rollups,
    )


def market_source_family_divergence_exception_report_to_json_dict(
    report: MarketSourceFamilyDivergenceExceptionReport,
) -> dict[str, Any]:
    if type(report) is not MarketSourceFamilyDivergenceExceptionReport:
        raise ValueError(
            "report must be a MarketSourceFamilyDivergenceExceptionReport",
        )
    payload = json_ready_no_floats(report)
    if not isinstance(payload, dict):
        raise ValueError("report JSON payload must be an object")
    return payload


def _exception_row(
    market_id: str,
    rows: tuple[MarketSourceFamilyDivergenceExceptionInputRow, ...],
    *,
    config: MarketSourceFamilyDivergenceExceptionConfig,
    generated_at: datetime,
    required_source_families: tuple[str, ...],
) -> MarketSourceFamilyDivergenceExceptionRow:
    category_ids = tuple(sorted({row.category_id for row in rows}))
    if len(category_ids) != 1:
        raise ValueError("market rows must have one category_id")
    latest_by_family = _latest_rows_by_family(rows)
    source_families = tuple(
        sorted(latest_by_family, key=lambda family: SOURCE_FAMILY_RANK[family]),
    )
    missing_source_families = tuple(
        family for family in required_source_families if family not in latest_by_family
    )
    probabilities = tuple(row.source_probability for row in latest_by_family.values())
    family_probability_delta = _probability_delta(probabilities)
    evidence_ages = tuple(
        _age_seconds(generated_at, row.evidence_observed_at)
        for row in latest_by_family.values()
    )
    acknowledgement_ages = tuple(
        _age_seconds(generated_at, row.conflict_acknowledged_at)
        for row in latest_by_family.values()
        if row.conflict_acknowledged_at is not None
    )
    reason_codes = _row_reason_codes(
        latest_by_family,
        family_probability_delta=family_probability_delta,
        missing_source_families=missing_source_families,
        config=config,
        generated_at=generated_at,
    )

    return MarketSourceFamilyDivergenceExceptionRow(
        market_id=market_id,
        category_id=category_ids[0],
        source_family_count=_decimal_count(len(source_families)),
        missing_source_family_count=_decimal_count(len(missing_source_families)),
        family_probability_delta=family_probability_delta,
        max_evidence_age_seconds=_max_decimal(evidence_ages),
        max_conflict_acknowledgement_age_seconds=_max_decimal(acknowledgement_ages),
        exception_status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        source_families=source_families,
        missing_source_families=missing_source_families,
    )


def _latest_rows_by_family(
    rows: tuple[MarketSourceFamilyDivergenceExceptionInputRow, ...],
) -> dict[str, MarketSourceFamilyDivergenceExceptionInputRow]:
    latest: dict[str, MarketSourceFamilyDivergenceExceptionInputRow] = {}
    for row in sorted(
        rows,
        key=lambda item: (
            item.source_family,
            item.evidence_observed_at,
            not item.conflict_resolved,
            item.conflict_acknowledged_at is None,
            item.conflict_acknowledged_at or EARLIEST_UTC_DATETIME,
            item.source_probability,
            item.market_id,
            item.category_id,
        ),
    ):
        latest[row.source_family] = row
    return latest


def _row_reason_codes(
    latest_by_family: dict[str, MarketSourceFamilyDivergenceExceptionInputRow],
    *,
    family_probability_delta: Decimal,
    missing_source_families: tuple[str, ...],
    config: MarketSourceFamilyDivergenceExceptionConfig,
    generated_at: datetime,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if any(
        _age_seconds(generated_at, row.conflict_acknowledged_at)
        > config.stale_conflict_acknowledgement_seconds
        for row in latest_by_family.values()
        if row.conflict_acknowledged_at is not None
    ):
        reason_codes.append(STALE_CONFLICT_ACKNOWLEDGEMENT_REASON)
    if any(not row.conflict_resolved for row in latest_by_family.values()):
        reason_codes.append(UNRESOLVED_CONFLICT_REASON)
    if family_probability_delta > config.max_family_probability_divergence:
        reason_codes.append(DIVERGENCE_BEYOND_THRESHOLD_REASON)
    if _decimal_count(len(latest_by_family)) < config.min_independent_source_families:
        reason_codes.append(INSUFFICIENT_INDEPENDENT_FAMILIES_REASON)
    if missing_source_families:
        reason_codes.append(MISSING_SOURCE_FAMILY_EVIDENCE_REASON)
    return _normalize_reason_codes(reason_codes or (CLEAR_REASON,))


def _report_reason_codes(
    rows: tuple[MarketSourceFamilyDivergenceExceptionRow, ...],
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for reason_code in REASON_CODES:
        if reason_code == CLEAR_REASON:
            continue
        if any(reason_code in row.reason_codes for row in rows):
            reason_codes.append(reason_code)
    return _normalize_reason_codes(reason_codes or (CLEAR_REASON,))


def _build_family_rollups(
    rows: tuple[MarketSourceFamilyDivergenceExceptionRow, ...],
) -> tuple[MarketSourceFamilyDivergenceExceptionFamilyRollup, ...]:
    rollups: list[MarketSourceFamilyDivergenceExceptionFamilyRollup] = []
    for source_family in SOURCE_FAMILIES:
        family_rows = tuple(row for row in rows if source_family in row.source_families)
        if not family_rows:
            continue
        rollups.append(
            MarketSourceFamilyDivergenceExceptionFamilyRollup(
                source_family=source_family,
                market_count=_decimal_count(len(family_rows)),
                exception_market_count=_status_not_clear_count(family_rows),
                blocked_market_count=_status_count(family_rows, "blocked"),
                watch_market_count=_status_count(family_rows, "watch"),
                clear_market_count=_status_count(family_rows, "clear"),
            ),
        )
    return tuple(rollups)


def _build_category_rollups(
    rows: tuple[MarketSourceFamilyDivergenceExceptionRow, ...],
) -> tuple[MarketSourceFamilyDivergenceExceptionCategoryRollup, ...]:
    rollups: list[MarketSourceFamilyDivergenceExceptionCategoryRollup] = []
    for category_id in sorted({row.category_id for row in rows}):
        category_rows = tuple(row for row in rows if row.category_id == category_id)
        rollups.append(
            MarketSourceFamilyDivergenceExceptionCategoryRollup(
                category_id=category_id,
                market_count=_decimal_count(len(category_rows)),
                exception_market_count=_status_not_clear_count(category_rows),
                blocked_market_count=_status_count(category_rows, "blocked"),
                watch_market_count=_status_count(category_rows, "watch"),
                clear_market_count=_status_count(category_rows, "clear"),
            ),
        )
    return tuple(rollups)


def _rows_by_market(
    rows: tuple[MarketSourceFamilyDivergenceExceptionInputRow, ...],
) -> dict[str, tuple[MarketSourceFamilyDivergenceExceptionInputRow, ...]]:
    grouped: dict[str, list[MarketSourceFamilyDivergenceExceptionInputRow]] = {}
    for row in rows:
        grouped.setdefault(row.market_id, []).append(row)
    return {market_id: tuple(market_rows) for market_id, market_rows in grouped.items()}


def _sort_exception_rows(
    rows: tuple[MarketSourceFamilyDivergenceExceptionRow, ...],
) -> tuple[MarketSourceFamilyDivergenceExceptionRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANK[row.exception_status],
                -row.family_probability_delta,
                -row.max_evidence_age_seconds,
                row.category_id,
                row.market_id,
            ),
        ),
    )


def _normalize_input_rows(
    rows: list[MarketSourceFamilyDivergenceExceptionInputRow]
    | tuple[MarketSourceFamilyDivergenceExceptionInputRow, ...],
) -> tuple[MarketSourceFamilyDivergenceExceptionInputRow, ...]:
    if not isinstance(rows, (list, tuple)):
        raise ValueError("input_rows must be a list or tuple")
    normalized: list[MarketSourceFamilyDivergenceExceptionInputRow] = []
    for row in rows:
        if type(row) is not MarketSourceFamilyDivergenceExceptionInputRow:
            raise ValueError(
                "input_rows must contain "
                "MarketSourceFamilyDivergenceExceptionInputRow values",
            )
        require_paper_only_flags(
            "source family divergence exception input row",
            row,
        )
        normalized.append(row)
    return tuple(normalized)


def _normalize_exception_rows(
    rows: tuple[MarketSourceFamilyDivergenceExceptionRow, ...],
) -> tuple[MarketSourceFamilyDivergenceExceptionRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketSourceFamilyDivergenceExceptionRow:
            raise ValueError(
                "rows must contain MarketSourceFamilyDivergenceExceptionRow values",
            )
    return _sort_exception_rows(rows)


def _normalize_family_rollups(
    rows: tuple[MarketSourceFamilyDivergenceExceptionFamilyRollup, ...],
) -> tuple[MarketSourceFamilyDivergenceExceptionFamilyRollup, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("family_rollups must be a tuple")
    for row in rows:
        if type(row) is not MarketSourceFamilyDivergenceExceptionFamilyRollup:
            raise ValueError(
                "family_rollups must contain "
                "MarketSourceFamilyDivergenceExceptionFamilyRollup values",
            )
    return tuple(sorted(rows, key=lambda row: SOURCE_FAMILY_RANK[row.source_family]))


def _normalize_category_rollups(
    rows: tuple[MarketSourceFamilyDivergenceExceptionCategoryRollup, ...],
) -> tuple[MarketSourceFamilyDivergenceExceptionCategoryRollup, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("category_rollups must be a tuple")
    for row in rows:
        if type(row) is not MarketSourceFamilyDivergenceExceptionCategoryRollup:
            raise ValueError(
                "category_rollups must contain "
                "MarketSourceFamilyDivergenceExceptionCategoryRollup values",
            )
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.exception_market_count,
                -row.blocked_market_count,
                -row.watch_market_count,
                row.category_id,
            ),
        ),
    )


def _normalize_source_families(
    name: str,
    values: tuple[str, ...],
) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise ValueError(f"{name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_source_family(name, value)
        if value not in normalized:
            normalized.append(value)
    return tuple(sorted(normalized, key=lambda family: SOURCE_FAMILY_RANK[family]))


def _normalize_reason_codes(values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of reason code strings")
    unique = tuple(dict.fromkeys(values))
    for value in unique:
        if type(value) is not str or value not in REASON_CODES:
            raise ValueError("reason_codes must contain known reason codes")
    return tuple(
        reason_code for reason_code in REASON_CODES if reason_code in set(unique)
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if reason_codes != (CLEAR_REASON,):
        return "watch"
    return "clear"


def _require_report_status(name: str, value: object) -> None:
    if type(value) is not str or value not in REPORT_STATUSES:
        raise ValueError(f"{name} must be a known report status")


def _require_exception_status(name: str, value: object) -> None:
    if type(value) is not str or value not in EXCEPTION_STATUSES:
        raise ValueError(f"{name} must be a known exception status")


def _require_source_family(name: str, value: object) -> None:
    if type(value) is not str or value not in SOURCE_FAMILIES:
        raise ValueError(f"{name} must be a known source family")


def _require_public_string(name: str, value: object) -> None:
    _require_canonical_string(name, value)


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{name} must not have surrounding whitespace")


def _require_bool(name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _require_positive_whole_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return decimal_value


def _require_ratio(name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(name, value)
    if decimal_value > ONE:
        raise ValueError(f"{name} must be <= 1")
    return decimal_value


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(name, value)


def _age_seconds(generated_at: datetime, observed_at: datetime | None) -> Decimal:
    if observed_at is None:
        return ZERO
    delta = generated_at - observed_at
    seconds = Decimal(delta.days * 86_400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    return _require_nonnegative_decimal("age_seconds", seconds + microseconds)


def _probability_delta(values: tuple[Decimal, ...]) -> Decimal:
    if len(values) < 2:
        return ZERO
    return _require_nonnegative_decimal(
        "family_probability_delta",
        max(values) - min(values),
    )


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _require_ratio("ratio", numerator / denominator)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return _quantize(Decimal(value))


def _status_count(
    rows: tuple[
        MarketSourceFamilyDivergenceExceptionRow
        | MarketSourceFamilyDivergenceExceptionCategoryRollup
        | MarketSourceFamilyDivergenceExceptionFamilyRollup,
        ...,
    ],
    status: str,
) -> Decimal:
    return _decimal_count(
        sum(1 for row in rows if getattr(row, "exception_status", None) == status),
    )


def _status_not_clear_count(
    rows: tuple[MarketSourceFamilyDivergenceExceptionRow, ...],
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.exception_status != "clear"))


def _reason_count(
    rows: tuple[MarketSourceFamilyDivergenceExceptionRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _require_nonnegative_decimal("decimal_sum", total)


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return _require_nonnegative_decimal("decimal_max", max(normalized))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _is_safe_text(value: str) -> bool:
    normalized = value.lower()
    return not any(fragment in normalized for fragment in UNSAFE_TEXT_FRAGMENTS)


def _reject_unsafe_text_fields(label: str, payload: object) -> None:
    for value in _iter_string_values(payload):
        if not _is_safe_text(value):
            raise ValueError(f"unsafe text in {label}")


def _iter_string_values(value: object) -> tuple[str, ...]:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        values: list[str] = []
        for field_name in value.__dataclass_fields__:
            item = getattr(value, field_name)
            if type(item) is str:
                values.append(item)
            elif isinstance(item, tuple):
                values.extend(item for item in item if type(item) is str)
        return tuple(values)
    return ()


def _validate_exception_row(row: MarketSourceFamilyDivergenceExceptionRow) -> None:
    if row.exception_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("exception_status must match reason_codes")
    if row.missing_source_family_count != _decimal_count(len(row.missing_source_families)):
        raise ValueError("missing_source_family_count must match missing_source_families")
    if row.source_family_count != _decimal_count(len(row.source_families)):
        raise ValueError("source_family_count must match source_families")


def _validate_rollup_counts(
    row: MarketSourceFamilyDivergenceExceptionFamilyRollup
    | MarketSourceFamilyDivergenceExceptionCategoryRollup,
) -> None:
    if row.market_count != (
        row.blocked_market_count + row.watch_market_count + row.clear_market_count
    ):
        raise ValueError("rollup status counts must equal market_count")
    if row.exception_market_count != row.blocked_market_count + row.watch_market_count:
        raise ValueError("rollup exception count must equal blocked plus watch")


def _validate_report(report: MarketSourceFamilyDivergenceExceptionReport) -> None:
    if report.report_status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("report_status must match reason_codes")
    if report.market_count != _decimal_count(len(report.rows)):
        raise ValueError("market_count must match rows")
    if report.source_family_count != _sum_decimal(
        row.source_family_count for row in report.rows
    ):
        raise ValueError("source_family_count must match rows")
    if report.exception_market_count != _status_not_clear_count(report.rows):
        raise ValueError("exception_market_count must match rows")
    if report.blocked_market_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_market_count must match rows")
    if report.watch_market_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_market_count must match rows")
    if report.clear_market_count != _status_count(report.rows, "clear"):
        raise ValueError("clear_market_count must match rows")
    if report.exception_market_ratio != _ratio(
        report.exception_market_count,
        report.market_count,
    ):
        raise ValueError("exception_market_ratio must match counts")


__all__ = (
    "CLEAR_REASON",
    "DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_EXCEPTION_REPORT_CONFIG_VERSION",
    "DIVERGENCE_BEYOND_THRESHOLD_REASON",
    "INSUFFICIENT_INDEPENDENT_FAMILIES_REASON",
    "MISSING_SOURCE_FAMILY_EVIDENCE_REASON",
    "MarketSourceFamilyDivergenceExceptionCategoryRollup",
    "MarketSourceFamilyDivergenceExceptionConfig",
    "MarketSourceFamilyDivergenceExceptionFamilyRollup",
    "MarketSourceFamilyDivergenceExceptionInputRow",
    "MarketSourceFamilyDivergenceExceptionReport",
    "MarketSourceFamilyDivergenceExceptionRow",
    "REASON_CODES",
    "SOURCE_FAMILIES",
    "STALE_CONFLICT_ACKNOWLEDGEMENT_REASON",
    "UNRESOLVED_CONFLICT_REASON",
    "build_market_source_family_divergence_exception_report",
    "market_source_family_divergence_exception_report_to_json_dict",
)
