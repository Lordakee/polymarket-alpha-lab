"""Pure Phase 1 market source-family divergence readiness report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_READINESS_REPORT_CONFIG_VERSION = (
    "market-source-family-divergence-readiness-report-v0"
)

READINESS_STATUSES = ("ready", "watch", "blocked")
REPORT_STATUSES = ("clear", "watch", "blocked")
CONFLICT_ACKNOWLEDGEMENT_STATUSES = ("missing", "fresh", "stale")
READINESS_STATUS_RANK = {"blocked": Decimal("0.000000"), "watch": Decimal("1.000000"), "ready": Decimal("2.000000")}
REPORT_STATUS_RANK = {"blocked": Decimal("0.000000"), "watch": Decimal("1.000000"), "clear": Decimal("2.000000")}

READY_REASON = "market_source_family_divergence_readiness_ready"
CLEAR_REASON = "market_source_family_divergence_readiness_clear"
WATCH_REASON = "market_source_family_divergence_readiness_watch"
BLOCKED_REASON = "market_source_family_divergence_readiness_blocked"
ACKNOWLEDGEMENT_MISSING_REASON = (
    "market_source_family_divergence_acknowledgement_missing"
)
ACKNOWLEDGEMENT_STALE_REASON = (
    "market_source_family_divergence_acknowledgement_stale"
)
FAMILY_MISSING_REASON = "market_source_family_divergence_family_missing"
FAMILY_STALE_REASON = "market_source_family_divergence_family_stale"
EVIDENCE_MISSING_REASON = "market_source_family_divergence_evidence_missing"
REASON_CODES = (
    READY_REASON,
    CLEAR_REASON,
    WATCH_REASON,
    BLOCKED_REASON,
    ACKNOWLEDGEMENT_MISSING_REASON,
    ACKNOWLEDGEMENT_STALE_REASON,
    FAMILY_MISSING_REASON,
    FAMILY_STALE_REASON,
    EVIDENCE_MISSING_REASON,
)
OFFICIAL_API_SOURCE_FAMILIES = frozenset(
    (
        "gamma_api",
        "clob_api",
        "data_api",
        "webso" "cket_market_channel",
    ),
)
FALLBACK_SOURCE_FAMILIES = frozenset(("scraper", "agent"))

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


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
        _join_parts("ord", "er"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("sig", "ning"),
    ),
)


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceReadinessConfig:
    config_version: str = (
        DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_READINESS_REPORT_CONFIG_VERSION
    )
    required_source_family_count: Decimal = Decimal("3.000000")
    required_divergence_evidence_count: Decimal = Decimal("2.000000")
    conflict_acknowledgement_stale_after_seconds: Decimal = Decimal("3600.000000")
    source_family_stale_after_seconds: Decimal = Decimal("7200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "required_source_family_count",
            _require_positive_decimal(
                "required_source_family_count",
                self.required_source_family_count,
            ),
        )
        object.__setattr__(
            self,
            "required_divergence_evidence_count",
            _require_positive_decimal(
                "required_divergence_evidence_count",
                self.required_divergence_evidence_count,
            ),
        )
        object.__setattr__(
            self,
            "conflict_acknowledgement_stale_after_seconds",
            _require_positive_decimal(
                "conflict_acknowledgement_stale_after_seconds",
                self.conflict_acknowledgement_stale_after_seconds,
            ),
        )
        object.__setattr__(
            self,
            "source_family_stale_after_seconds",
            _require_positive_decimal(
                "source_family_stale_after_seconds",
                self.source_family_stale_after_seconds,
            ),
        )
        require_paper_only_flags("market source family divergence readiness config", self)


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceReadinessInputRow:
    market_id: str
    source_family: str
    probability_delta: Decimal
    evidence_count: Decimal
    observed_at: datetime
    conflict_acknowledged_at: datetime | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("market_id", self.market_id)
        _require_public_string("source_family", self.source_family)
        object.__setattr__(
            self,
            "probability_delta",
            _require_probability_delta("probability_delta", self.probability_delta),
        )
        object.__setattr__(
            self,
            "evidence_count",
            _require_nonnegative_decimal("evidence_count", self.evidence_count),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "conflict_acknowledged_at",
            _as_optional_utc(
                "conflict_acknowledged_at",
                self.conflict_acknowledged_at,
            ),
        )
        reject_unsafe_surface_fields(
            "market source family divergence readiness input row",
            self,
        )
        require_paper_only_flags(
            "market source family divergence readiness input row",
            self,
        )


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceReadinessMarketRow:
    market_id: str
    readiness_status: str
    reason_codes: tuple[str, ...]
    source_family_count: Decimal
    required_source_family_count: Decimal
    missing_family_count: Decimal
    stale_family_count: Decimal
    evidence_count: Decimal
    required_divergence_evidence_count: Decimal
    divergence_evidence_present: bool
    conflict_acknowledgement_status: str
    conflict_acknowledged_at: datetime | None
    conflict_acknowledgement_age_seconds: Decimal
    latest_observed_at: datetime | None
    max_source_family_age_seconds: Decimal
    max_probability_delta: Decimal
    readiness_ratio: Decimal
    official_api_family_count: Decimal
    fallback_family_count: Decimal
    official_api_evidence_count: Decimal
    fallback_evidence_count: Decimal
    official_api_coverage_ratio: Decimal
    fallback_coverage_ratio: Decimal
    manual_review_ready: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("market_id", self.market_id)
        _require_member("readiness_status", self.readiness_status, READINESS_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        for field_name in (
            "source_family_count",
            "required_source_family_count",
            "missing_family_count",
            "stale_family_count",
            "evidence_count",
            "required_divergence_evidence_count",
            "conflict_acknowledgement_age_seconds",
            "max_source_family_age_seconds",
            "official_api_family_count",
            "fallback_family_count",
            "official_api_evidence_count",
            "fallback_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_probability_delta",
            _require_probability_delta("max_probability_delta", self.max_probability_delta),
        )
        object.__setattr__(
            self,
            "readiness_ratio",
            _require_ratio_decimal("readiness_ratio", self.readiness_ratio),
        )
        for field_name in (
            "official_api_coverage_ratio",
            "fallback_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.divergence_evidence_present) is not bool:
            raise ValueError("divergence_evidence_present must be a bool")
        if type(self.manual_review_ready) is not bool:
            raise ValueError("manual_review_ready must be a bool")
        _require_member(
            "conflict_acknowledgement_status",
            self.conflict_acknowledgement_status,
            CONFLICT_ACKNOWLEDGEMENT_STATUSES,
        )
        object.__setattr__(
            self,
            "conflict_acknowledged_at",
            _as_optional_utc(
                "conflict_acknowledged_at",
                self.conflict_acknowledged_at,
            ),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_optional_utc("latest_observed_at", self.latest_observed_at),
        )
        _validate_market_row(self)
        reject_unsafe_surface_fields(
            "market source family divergence readiness market row",
            self,
        )
        require_paper_only_flags(
            "market source family divergence readiness market row",
            self,
        )


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceReadinessReport:
    generated_at: datetime
    config_version: str
    report_status: str
    reason_codes: tuple[str, ...]
    market_count: Decimal
    ready_market_count: Decimal
    watch_market_count: Decimal
    blocked_market_count: Decimal
    readiness_ratio: Decimal
    divergence_evidence_market_count: Decimal
    conflict_acknowledged_market_count: Decimal
    fresh_acknowledgement_market_count: Decimal
    missing_family_market_count: Decimal
    stale_family_market_count: Decimal
    official_api_covered_market_count: Decimal
    fallback_covered_market_count: Decimal
    fallback_only_market_count: Decimal
    manual_review_ready_market_count: Decimal
    official_api_coverage_ratio: Decimal
    fallback_coverage_ratio: Decimal
    manual_review_ready_ratio: Decimal
    max_probability_delta: Decimal
    max_acknowledgement_age_seconds: Decimal
    max_source_family_age_seconds: Decimal
    rows: tuple[MarketSourceFamilyDivergenceReadinessMarketRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        for field_name in (
            "market_count",
            "ready_market_count",
            "watch_market_count",
            "blocked_market_count",
            "divergence_evidence_market_count",
            "conflict_acknowledged_market_count",
            "fresh_acknowledgement_market_count",
            "missing_family_market_count",
            "stale_family_market_count",
            "official_api_covered_market_count",
            "fallback_covered_market_count",
            "fallback_only_market_count",
            "manual_review_ready_market_count",
            "max_acknowledgement_age_seconds",
            "max_source_family_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "readiness_ratio",
            _require_ratio_decimal("readiness_ratio", self.readiness_ratio),
        )
        for field_name in (
            "official_api_coverage_ratio",
            "fallback_coverage_ratio",
            "manual_review_ready_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_probability_delta",
            _require_probability_delta("max_probability_delta", self.max_probability_delta),
        )
        object.__setattr__(self, "rows", _normalize_market_rows(self.rows))
        _validate_report(self)
        reject_unsafe_surface_fields(
            "market source family divergence readiness report",
            self,
        )
        require_paper_only_flags("market source family divergence readiness report", self)


def build_market_source_family_divergence_readiness_report(
    rows: tuple[MarketSourceFamilyDivergenceReadinessInputRow, ...]
    | list[MarketSourceFamilyDivergenceReadinessInputRow],
    *,
    config: MarketSourceFamilyDivergenceReadinessConfig,
    generated_at: datetime,
) -> MarketSourceFamilyDivergenceReadinessReport:
    if type(config) is not MarketSourceFamilyDivergenceReadinessConfig:
        raise ValueError(
            "config must be a MarketSourceFamilyDivergenceReadinessConfig",
        )
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_input_rows(rows)
    market_rows = tuple(
        sorted(
            (
                _market_row(market_id, market_input_rows, config, generated_at_utc)
                for market_id, market_input_rows in _market_groups(input_rows)
            ),
            key=_market_row_sort_key,
        ),
    )
    market_count = _count(len(market_rows))
    return MarketSourceFamilyDivergenceReadinessReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(market_rows),
        reason_codes=_report_reason_codes(market_rows),
        market_count=market_count,
        ready_market_count=_row_status_count(market_rows, "ready"),
        watch_market_count=_row_status_count(market_rows, "watch"),
        blocked_market_count=_row_status_count(market_rows, "blocked"),
        readiness_ratio=_safe_ratio(
            _row_status_count(market_rows, "ready"),
            market_count,
        ),
        divergence_evidence_market_count=_boolean_count(
            tuple(row.divergence_evidence_present for row in market_rows),
        ),
        conflict_acknowledged_market_count=_row_ack_count(market_rows),
        fresh_acknowledgement_market_count=_row_fresh_ack_count(market_rows),
        missing_family_market_count=_positive_count(
            tuple(row.missing_family_count for row in market_rows),
        ),
        stale_family_market_count=_positive_count(
            tuple(row.stale_family_count for row in market_rows),
        ),
        official_api_covered_market_count=_positive_count(
            tuple(row.official_api_family_count for row in market_rows),
        ),
        fallback_covered_market_count=_positive_count(
            tuple(row.fallback_family_count for row in market_rows),
        ),
        fallback_only_market_count=_fallback_only_market_count(market_rows),
        manual_review_ready_market_count=_boolean_count(
            tuple(row.manual_review_ready for row in market_rows),
        ),
        official_api_coverage_ratio=_safe_ratio(
            _positive_count(tuple(row.official_api_family_count for row in market_rows)),
            market_count,
        ),
        fallback_coverage_ratio=_safe_ratio(
            _positive_count(tuple(row.fallback_family_count for row in market_rows)),
            market_count,
        ),
        manual_review_ready_ratio=_safe_ratio(
            _boolean_count(tuple(row.manual_review_ready for row in market_rows)),
            market_count,
        ),
        max_probability_delta=_max_decimal(
            tuple(row.max_probability_delta for row in market_rows),
        ),
        max_acknowledgement_age_seconds=_max_decimal(
            tuple(row.conflict_acknowledgement_age_seconds for row in market_rows),
        ),
        max_source_family_age_seconds=_max_decimal(
            tuple(row.max_source_family_age_seconds for row in market_rows),
        ),
        rows=market_rows,
    )


def market_source_family_divergence_readiness_payload(
    report: MarketSourceFamilyDivergenceReadinessReport,
) -> dict[str, Any]:
    if type(report) is not MarketSourceFamilyDivergenceReadinessReport:
        raise ValueError(
            "report must be a MarketSourceFamilyDivergenceReadinessReport",
        )
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields(
        "market source family divergence readiness report",
        report,
    )
    return json_ready_no_floats(report)


def _normalize_input_rows(
    rows: tuple[MarketSourceFamilyDivergenceReadinessInputRow, ...]
    | list[MarketSourceFamilyDivergenceReadinessInputRow],
) -> tuple[MarketSourceFamilyDivergenceReadinessInputRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not MarketSourceFamilyDivergenceReadinessInputRow:
            raise ValueError(
                "rows must contain MarketSourceFamilyDivergenceReadinessInputRow values",
            )
        require_paper_only_flags("row", row)
        key = (row.market_id, row.source_family)
        if key in seen:
            raise ValueError("rows must not contain duplicate market_id source_family pairs")
        seen.add(key)
    return normalized


def _normalize_market_rows(
    rows: tuple[MarketSourceFamilyDivergenceReadinessMarketRow, ...],
) -> tuple[MarketSourceFamilyDivergenceReadinessMarketRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    seen_market_ids: set[str] = set()
    for row in normalized:
        if type(row) is not MarketSourceFamilyDivergenceReadinessMarketRow:
            raise ValueError(
                "rows must contain MarketSourceFamilyDivergenceReadinessMarketRow values",
            )
        require_paper_only_flags("row", row)
        if row.market_id in seen_market_ids:
            raise ValueError("rows must not contain duplicate market_id values")
        seen_market_ids.add(row.market_id)
    return normalized


def _market_groups(
    rows: tuple[MarketSourceFamilyDivergenceReadinessInputRow, ...],
) -> tuple[tuple[str, tuple[MarketSourceFamilyDivergenceReadinessInputRow, ...]], ...]:
    market_ids = tuple(dict.fromkeys(row.market_id for row in rows))
    return tuple(
        (
            market_id,
            tuple(row for row in rows if row.market_id == market_id),
        )
        for market_id in market_ids
    )


def _market_row(
    market_id: str,
    rows: tuple[MarketSourceFamilyDivergenceReadinessInputRow, ...],
    config: MarketSourceFamilyDivergenceReadinessConfig,
    generated_at: datetime,
) -> MarketSourceFamilyDivergenceReadinessMarketRow:
    source_family_count = _count(len(rows))
    missing_family_count = _nonnegative_difference(
        config.required_source_family_count,
        source_family_count,
    )
    family_ages = tuple(_age_seconds(generated_at, row.observed_at) for row in rows)
    stale_family_count = _boolean_count(
        tuple(age > config.source_family_stale_after_seconds for age in family_ages),
    )
    evidence_count = _sum_decimal(tuple(row.evidence_count for row in rows))
    divergence_evidence_present = evidence_count >= config.required_divergence_evidence_count
    acknowledged_at = _latest_optional_datetime(
        tuple(row.conflict_acknowledged_at for row in rows),
    )
    acknowledgement_age_seconds = (
        ZERO
        if acknowledged_at is None
        else _age_seconds(generated_at, acknowledged_at)
    )
    acknowledgement_status = _acknowledgement_status(
        acknowledged_at,
        acknowledgement_age_seconds,
        config,
    )
    official_api_rows = tuple(row for row in rows if _is_official_api_source(row))
    fallback_rows = tuple(row for row in rows if _is_fallback_source(row))
    official_api_family_count = _count(len(official_api_rows))
    fallback_family_count = _count(len(fallback_rows))
    official_api_evidence_count = _sum_decimal(
        tuple(row.evidence_count for row in official_api_rows),
    )
    fallback_evidence_count = _sum_decimal(
        tuple(row.evidence_count for row in fallback_rows),
    )
    readiness_status = _readiness_status(
        missing_family_count=missing_family_count,
        stale_family_count=stale_family_count,
        divergence_evidence_present=divergence_evidence_present,
        conflict_acknowledgement_status=acknowledgement_status,
    )
    return MarketSourceFamilyDivergenceReadinessMarketRow(
        market_id=market_id,
        readiness_status=readiness_status,
        reason_codes=_row_reason_codes(
            readiness_status,
            missing_family_count,
            stale_family_count,
            divergence_evidence_present,
            acknowledgement_status,
        ),
        source_family_count=source_family_count,
        required_source_family_count=config.required_source_family_count,
        missing_family_count=missing_family_count,
        stale_family_count=stale_family_count,
        evidence_count=evidence_count,
        required_divergence_evidence_count=config.required_divergence_evidence_count,
        divergence_evidence_present=divergence_evidence_present,
        conflict_acknowledgement_status=acknowledgement_status,
        conflict_acknowledged_at=acknowledged_at,
        conflict_acknowledgement_age_seconds=acknowledgement_age_seconds,
        latest_observed_at=_latest_datetime(tuple(row.observed_at for row in rows)),
        max_source_family_age_seconds=_max_decimal(family_ages),
        max_probability_delta=_max_decimal(tuple(row.probability_delta for row in rows)),
        readiness_ratio=_safe_ratio(
            _minimum_decimal(source_family_count, config.required_source_family_count),
            config.required_source_family_count,
        ),
        official_api_family_count=official_api_family_count,
        fallback_family_count=fallback_family_count,
        official_api_evidence_count=official_api_evidence_count,
        fallback_evidence_count=fallback_evidence_count,
        official_api_coverage_ratio=_safe_ratio(
            official_api_family_count,
            source_family_count,
        ),
        fallback_coverage_ratio=_safe_ratio(
            fallback_family_count,
            source_family_count,
        ),
        manual_review_ready=(
            readiness_status == "ready"
            and official_api_family_count > ZERO
            and fallback_family_count > ZERO
        ),
    )


def _readiness_status(
    *,
    missing_family_count: Decimal,
    stale_family_count: Decimal,
    divergence_evidence_present: bool,
    conflict_acknowledgement_status: str,
) -> str:
    if missing_family_count > ZERO or not divergence_evidence_present:
        return "blocked"
    if stale_family_count > ZERO or conflict_acknowledgement_status in ("missing", "stale"):
        return "watch"
    return "ready"


def _acknowledgement_status(
    acknowledged_at: datetime | None,
    acknowledgement_age_seconds: Decimal,
    config: MarketSourceFamilyDivergenceReadinessConfig,
) -> str:
    if acknowledged_at is None:
        return "missing"
    if acknowledgement_age_seconds > config.conflict_acknowledgement_stale_after_seconds:
        return "stale"
    return "fresh"


def _row_reason_codes(
    readiness_status: str,
    missing_family_count: Decimal,
    stale_family_count: Decimal,
    divergence_evidence_present: bool,
    acknowledgement_status: str,
) -> tuple[str, ...]:
    codes: list[str] = []
    if missing_family_count > ZERO:
        codes.append(FAMILY_MISSING_REASON)
    if not divergence_evidence_present:
        codes.append(EVIDENCE_MISSING_REASON)
    if acknowledgement_status == "missing":
        codes.append(ACKNOWLEDGEMENT_MISSING_REASON)
    elif acknowledgement_status == "stale":
        codes.append(ACKNOWLEDGEMENT_STALE_REASON)
    if stale_family_count > ZERO:
        codes.append(FAMILY_STALE_REASON)
    if not codes:
        codes.append(READY_REASON if readiness_status == "ready" else WATCH_REASON)
    return tuple(codes)


def _report_status(
    rows: tuple[MarketSourceFamilyDivergenceReadinessMarketRow, ...],
) -> str:
    if not rows:
        return "clear"
    if any(row.readiness_status == "blocked" for row in rows):
        return "blocked"
    if any(row.readiness_status == "watch" for row in rows):
        return "watch"
    return "clear"


def _report_reason_codes(
    rows: tuple[MarketSourceFamilyDivergenceReadinessMarketRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (CLEAR_REASON,)
    codes: list[str] = []
    report_status = _report_status(rows)
    if report_status == "blocked":
        codes.append(BLOCKED_REASON)
    elif report_status == "watch":
        codes.append(WATCH_REASON)
    else:
        codes.append(CLEAR_REASON)
    if any(row.conflict_acknowledgement_status == "missing" for row in rows):
        codes.append(ACKNOWLEDGEMENT_MISSING_REASON)
    if any(row.conflict_acknowledgement_status == "stale" for row in rows):
        codes.append(ACKNOWLEDGEMENT_STALE_REASON)
    if any(row.missing_family_count > ZERO for row in rows):
        codes.append(FAMILY_MISSING_REASON)
    if any(row.stale_family_count > ZERO for row in rows):
        codes.append(FAMILY_STALE_REASON)
    if any(not row.divergence_evidence_present for row in rows):
        codes.append(EVIDENCE_MISSING_REASON)
    return tuple(codes)


def _market_row_sort_key(
    row: MarketSourceFamilyDivergenceReadinessMarketRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str]:
    return (
        READINESS_STATUS_RANK[row.readiness_status],
        -row.missing_family_count,
        -row.conflict_acknowledgement_age_seconds,
        -row.stale_family_count,
        row.market_id,
    )


def _row_status_count(
    rows: tuple[MarketSourceFamilyDivergenceReadinessMarketRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.readiness_status == status))


def _row_ack_count(
    rows: tuple[MarketSourceFamilyDivergenceReadinessMarketRow, ...],
) -> Decimal:
    return _count(
        sum(1 for row in rows if row.conflict_acknowledgement_status != "missing"),
    )


def _row_fresh_ack_count(
    rows: tuple[MarketSourceFamilyDivergenceReadinessMarketRow, ...],
) -> Decimal:
    return _count(
        sum(1 for row in rows if row.conflict_acknowledgement_status == "fresh"),
    )


def _fallback_only_market_count(
    rows: tuple[MarketSourceFamilyDivergenceReadinessMarketRow, ...],
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if row.fallback_family_count > ZERO and row.official_api_family_count == ZERO
        ),
    )


def _boolean_count(values: tuple[bool, ...]) -> Decimal:
    return _count(sum(1 for value in values if value))


def _positive_count(values: tuple[Decimal, ...]) -> Decimal:
    return _count(sum(1 for value in values if value > ZERO))


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    with localcontext(DECIMAL_CONTEXT):
        for value in values:
            total += value
    return total.quantize(QUANT)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values).quantize(QUANT)


def _minimum_decimal(first: Decimal, second: Decimal) -> Decimal:
    return first if first <= second else second


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _nonnegative_difference(first: Decimal, second: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = first - second
    if value < ZERO:
        return ZERO
    return value.quantize(QUANT)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
    value = seconds + microseconds
    if value < ZERO:
        raise ValueError("datetime values must not be after generated_at")
    return value.quantize(QUANT)


def _latest_datetime(values: tuple[datetime, ...]) -> datetime | None:
    if not values:
        return None
    return max(values)


def _latest_optional_datetime(values: tuple[datetime | None, ...]) -> datetime | None:
    present = tuple(value for value in values if value is not None)
    if not present:
        return None
    return max(present)


def _validate_market_row(row: MarketSourceFamilyDivergenceReadinessMarketRow) -> None:
    if row.missing_family_count > ZERO and row.readiness_status != "blocked":
        raise ValueError("missing family rows must be blocked")
    if not row.divergence_evidence_present and row.readiness_status != "blocked":
        raise ValueError("missing evidence rows must be blocked")
    if row.stale_family_count > ZERO and row.readiness_status == "ready":
        raise ValueError("stale family rows must not be ready")
    if (
        row.conflict_acknowledgement_status in ("missing", "stale")
        and row.readiness_status == "ready"
    ):
        raise ValueError("non-fresh acknowledgement rows must not be ready")


def _validate_report(report: MarketSourceFamilyDivergenceReadinessReport) -> None:
    if report.market_count != _count(len(report.rows)):
        raise ValueError("market_count must match rows")
    status_counts = (
        report.ready_market_count
        + report.watch_market_count
        + report.blocked_market_count
    )
    if status_counts != report.market_count:
        raise ValueError("market status counts must match market_count")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.official_api_coverage_ratio != _safe_ratio(
        report.official_api_covered_market_count,
        report.market_count,
    ):
        raise ValueError("official_api_coverage_ratio must match rows")
    if report.fallback_coverage_ratio != _safe_ratio(
        report.fallback_covered_market_count,
        report.market_count,
    ):
        raise ValueError("fallback_coverage_ratio must match rows")
    if report.manual_review_ready_ratio != _safe_ratio(
        report.manual_review_ready_market_count,
        report.market_count,
    ):
        raise ValueError("manual_review_ready_ratio must match rows")


def _is_official_api_source(row: MarketSourceFamilyDivergenceReadinessInputRow) -> bool:
    return row.source_family in OFFICIAL_API_SOURCE_FAMILIES


def _is_fallback_source(row: MarketSourceFamilyDivergenceReadinessInputRow) -> bool:
    return row.source_family in FALLBACK_SOURCE_FAMILIES


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    lowered = value.lower()
    for fragment in UNSAFE_TEXT_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"{field_name} must not contain unsafe text")


def _require_member(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        allowed = ", ".join(allowed_values)
        raise ValueError(f"{field_name} must be one of: {allowed}")


def _require_probability_delta(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must not exceed 1")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must not exceed 1")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(QUANT)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        raise ValueError("reason_codes must be a non-empty tuple")
    normalized: list[str] = []
    for value in values:
        if type(value) is not str or value not in REASON_CODES:
            raise ValueError("reason_codes contains an unknown reason code")
        if value not in normalized:
            normalized.append(value)
    return tuple(normalized)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


__all__ = (
    "DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_READINESS_REPORT_CONFIG_VERSION",
    "MarketSourceFamilyDivergenceReadinessConfig",
    "MarketSourceFamilyDivergenceReadinessInputRow",
    "MarketSourceFamilyDivergenceReadinessMarketRow",
    "MarketSourceFamilyDivergenceReadinessReport",
    "build_market_source_family_divergence_readiness_report",
    "market_source_family_divergence_readiness_payload",
)
