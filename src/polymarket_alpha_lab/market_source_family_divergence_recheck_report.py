"""Pure Phase 1 source-family divergence recheck report."""

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


DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_RECHECK_REPORT_CONFIG_VERSION = (
    "market-source-family-divergence-recheck-report-v0"
)

SOURCE_FAMILIES = ("official", "primary", "proxy", "team_acknowledged")
EVIDENCE_SOURCE_FAMILIES = ("official", "primary", "proxy")
SOURCE_FAMILY_RANK = {
    "official": 0,
    "primary": 1,
    "proxy": 2,
    "team_acknowledged": 3,
}
REPORT_STATUSES = ("clear", "watch", "blocked")
RECHECK_STATUSES = ("clear", "watch", "blocked")
STATUS_RANK = {"blocked": 0, "watch": 1, "clear": 2}

CLEAR_REASON = "market_source_family_divergence_recheck_clear"
UNRESOLVED_DIVERGENCE_REASON = (
    "market_source_family_divergence_recheck_unresolved_divergence"
)
STALE_OFFICIAL_SOURCE_REASON = (
    "market_source_family_divergence_recheck_stale_official_source"
)
PROXY_ONLY_CONFIRMATION_REASON = (
    "market_source_family_divergence_recheck_proxy_only_confirmation"
)
MISSING_TEAM_ACKNOWLEDGEMENT_REASON = (
    "market_source_family_divergence_recheck_missing_team_acknowledgement"
)
REASON_CODES = (
    UNRESOLVED_DIVERGENCE_REASON,
    STALE_OFFICIAL_SOURCE_REASON,
    PROXY_ONLY_CONFIRMATION_REASON,
    MISSING_TEAM_ACKNOWLEDGEMENT_REASON,
    CLEAR_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
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
        _join_parts("ad", "vice"),
    ),
)


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceRecheckConfig:
    config_version: str = (
        DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_RECHECK_REPORT_CONFIG_VERSION
    )
    official_stale_after_seconds: Decimal = Decimal("3600.000000")
    acknowledgement_required_after_seconds: Decimal = Decimal("600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "official_stale_after_seconds",
            _require_positive_decimal(
                "official_stale_after_seconds",
                self.official_stale_after_seconds,
            ),
        )
        object.__setattr__(
            self,
            "acknowledgement_required_after_seconds",
            _require_positive_decimal(
                "acknowledgement_required_after_seconds",
                self.acknowledgement_required_after_seconds,
            ),
        )
        require_paper_only_flags(
            "market source family divergence recheck config",
            self,
        )


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceRecheckInputRow:
    market_id: str
    source_family: str
    observed_value: str
    source_updated_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("market_id", self.market_id)
        _require_source_family("source_family", self.source_family)
        _require_public_string("observed_value", self.observed_value)
        object.__setattr__(
            self,
            "source_updated_at",
            _as_utc("source_updated_at", self.source_updated_at),
        )
        require_paper_only_flags(
            "market source family divergence recheck input row",
            self,
        )


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceRecheckRow:
    market_id: str
    official_value: str | None
    primary_value: str | None
    proxy_value: str | None
    team_acknowledged_value: str | None
    source_update_count: Decimal
    divergent_source_family_count: Decimal
    unresolved_divergence_count: Decimal
    stale_official_source_count: Decimal
    proxy_only_confirmation_count: Decimal
    missing_team_acknowledgement_count: Decimal
    official_age_seconds: Decimal
    max_source_age_seconds: Decimal
    divergence_ratio: Decimal
    recheck_status: str
    recheck_required: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("market_id", self.market_id)
        for field_name in (
            "official_value",
            "primary_value",
            "proxy_value",
            "team_acknowledged_value",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_public_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_update_count",
            "divergent_source_family_count",
            "unresolved_divergence_count",
            "stale_official_source_count",
            "proxy_only_confirmation_count",
            "missing_team_acknowledgement_count",
            "official_age_seconds",
            "max_source_age_seconds",
            "divergence_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_recheck_status("recheck_status", self.recheck_status)
        _require_bool("recheck_required", self.recheck_required)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_recheck_row(self)
        reject_unsafe_surface_fields(
            "market source family divergence recheck row",
            self,
        )
        require_paper_only_flags(
            "market source family divergence recheck row",
            self,
        )


@dataclass(frozen=True)
class MarketSourceFamilyDivergenceRecheckReport:
    generated_at: datetime
    config_version: str
    report_status: str
    reason_codes: tuple[str, ...]
    market_count: Decimal
    source_update_count: Decimal
    clear_market_count: Decimal
    watch_market_count: Decimal
    blocked_market_count: Decimal
    recheck_required_market_count: Decimal
    unresolved_divergence_market_count: Decimal
    stale_official_market_count: Decimal
    proxy_only_confirmation_market_count: Decimal
    missing_team_acknowledgement_market_count: Decimal
    recheck_required_ratio: Decimal
    unresolved_divergence_ratio: Decimal
    stale_official_ratio: Decimal
    proxy_only_confirmation_ratio: Decimal
    missing_team_acknowledgement_ratio: Decimal
    max_official_age_seconds: Decimal
    max_source_age_seconds: Decimal
    rows: tuple[MarketSourceFamilyDivergenceRecheckRow, ...]
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
            "source_update_count",
            "clear_market_count",
            "watch_market_count",
            "blocked_market_count",
            "recheck_required_market_count",
            "unresolved_divergence_market_count",
            "stale_official_market_count",
            "proxy_only_confirmation_market_count",
            "missing_team_acknowledgement_market_count",
            "recheck_required_ratio",
            "unresolved_divergence_ratio",
            "stale_official_ratio",
            "proxy_only_confirmation_ratio",
            "missing_team_acknowledgement_ratio",
            "max_official_age_seconds",
            "max_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        reject_unsafe_surface_fields(
            "market source family divergence recheck report",
            self,
        )
        require_paper_only_flags(
            "market source family divergence recheck report",
            self,
        )


def build_market_source_family_divergence_recheck_report(
    input_rows: list[MarketSourceFamilyDivergenceRecheckInputRow]
    | tuple[MarketSourceFamilyDivergenceRecheckInputRow, ...],
    *,
    config: MarketSourceFamilyDivergenceRecheckConfig,
    generated_at: datetime,
) -> MarketSourceFamilyDivergenceRecheckReport:
    if type(config) is not MarketSourceFamilyDivergenceRecheckConfig:
        raise ValueError(
            "config must be a MarketSourceFamilyDivergenceRecheckConfig",
        )
    require_paper_only_flags(
        "market source family divergence recheck config",
        config,
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows, generated_at=generated_at_utc)

    by_market: dict[str, list[MarketSourceFamilyDivergenceRecheckInputRow]] = {}
    for row in rows:
        by_market.setdefault(row.market_id, []).append(row)

    report_rows = _sort_rows(
        tuple(
            _market_row(
                market_id,
                tuple(market_rows),
                config=config,
                generated_at=generated_at_utc,
            )
            for market_id, market_rows in sorted(by_market.items())
        ),
    )
    reason_codes = _report_reason_codes(report_rows)
    market_count = _decimal_count(len(report_rows))

    return MarketSourceFamilyDivergenceRecheckReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        market_count=market_count,
        source_update_count=_sum_decimal(row.source_update_count for row in report_rows),
        clear_market_count=_status_count(report_rows, "clear"),
        watch_market_count=_status_count(report_rows, "watch"),
        blocked_market_count=_status_count(report_rows, "blocked"),
        recheck_required_market_count=_positive_metric_count(
            report_rows,
            "recheck_required",
        ),
        unresolved_divergence_market_count=_positive_metric_count(
            report_rows,
            "unresolved_divergence_count",
        ),
        stale_official_market_count=_positive_metric_count(
            report_rows,
            "stale_official_source_count",
        ),
        proxy_only_confirmation_market_count=_positive_metric_count(
            report_rows,
            "proxy_only_confirmation_count",
        ),
        missing_team_acknowledgement_market_count=_positive_metric_count(
            report_rows,
            "missing_team_acknowledgement_count",
        ),
        recheck_required_ratio=_ratio(
            _positive_metric_count(report_rows, "recheck_required"),
            market_count,
        ),
        unresolved_divergence_ratio=_ratio(
            _positive_metric_count(report_rows, "unresolved_divergence_count"),
            market_count,
        ),
        stale_official_ratio=_ratio(
            _positive_metric_count(report_rows, "stale_official_source_count"),
            market_count,
        ),
        proxy_only_confirmation_ratio=_ratio(
            _positive_metric_count(report_rows, "proxy_only_confirmation_count"),
            market_count,
        ),
        missing_team_acknowledgement_ratio=_ratio(
            _positive_metric_count(report_rows, "missing_team_acknowledgement_count"),
            market_count,
        ),
        max_official_age_seconds=_max_decimal(
            row.official_age_seconds for row in report_rows
        ),
        max_source_age_seconds=_max_decimal(
            row.max_source_age_seconds for row in report_rows
        ),
        rows=report_rows,
    )


def market_source_family_divergence_recheck_report_to_payload(
    report: MarketSourceFamilyDivergenceRecheckReport,
) -> dict[str, Any]:
    if type(report) is not MarketSourceFamilyDivergenceRecheckReport:
        raise ValueError(
            "report must be a MarketSourceFamilyDivergenceRecheckReport",
        )
    require_paper_only_flags(
        "market source family divergence recheck report",
        report,
    )
    ready = json_ready_no_floats(report)
    if type(ready) is not dict:
        raise ValueError("report value must be a JSON object")
    reject_unsafe_surface_fields(
        "market source family divergence recheck report value",
        ready,
    )
    return ready


def _normalize_input_rows(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[MarketSourceFamilyDivergenceRecheckInputRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not MarketSourceFamilyDivergenceRecheckInputRow:
            raise ValueError("input rows must contain divergence recheck input rows")
        require_paper_only_flags(
            "market source family divergence recheck input row",
            row,
        )
        if row.source_updated_at > generated_at:
            raise ValueError("source_updated_at must not be after generated_at")
        key = (row.market_id, row.source_family)
        if key in seen:
            raise ValueError("source_family values must be unique per market_id")
        seen.add(key)
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                row.market_id,
                SOURCE_FAMILY_RANK[row.source_family],
                row.observed_value,
                row.source_updated_at,
            ),
        ),
    )


def _market_row(
    market_id: str,
    rows: tuple[MarketSourceFamilyDivergenceRecheckInputRow, ...],
    *,
    config: MarketSourceFamilyDivergenceRecheckConfig,
    generated_at: datetime,
) -> MarketSourceFamilyDivergenceRecheckRow:
    by_family = {row.source_family: row for row in rows}
    source_update_count = _decimal_count(len(rows))
    reference_value = _reference_value(rows)
    divergent_source_family_count = _decimal_count(
        sum(
            1
            for row in rows
            if row.source_family in EVIDENCE_SOURCE_FAMILIES
            and reference_value is not None
            and row.observed_value != reference_value
        ),
    )
    official_age_seconds = _source_age_seconds(
        generated_at,
        by_family.get("official"),
    )
    max_source_age_seconds = _max_decimal(
        _age_seconds(generated_at, row.source_updated_at) for row in rows
    )
    unresolved_divergence_count = (
        ONE if divergent_source_family_count > ZERO else ZERO
    )
    stale_official_source_count = (
        ONE
        if "official" in by_family
        and official_age_seconds >= config.official_stale_after_seconds
        else ZERO
    )
    proxy_only_confirmation_count = (
        ONE
        if "proxy" in by_family
        and "official" not in by_family
        and "primary" not in by_family
        else ZERO
    )
    missing_team_acknowledgement_count = (
        ONE
        if "team_acknowledged" not in by_family
        and (
            unresolved_divergence_count > ZERO
            or stale_official_source_count > ZERO
            or proxy_only_confirmation_count > ZERO
        )
        and max_source_age_seconds >= config.acknowledgement_required_after_seconds
        else ZERO
    )
    reason_codes = _row_reason_codes(
        unresolved_divergence_count=unresolved_divergence_count,
        stale_official_source_count=stale_official_source_count,
        proxy_only_confirmation_count=proxy_only_confirmation_count,
        missing_team_acknowledgement_count=missing_team_acknowledgement_count,
    )
    recheck_status = _row_status_from_reason_codes(reason_codes)

    return MarketSourceFamilyDivergenceRecheckRow(
        market_id=market_id,
        official_value=_value_for_family(by_family, "official"),
        primary_value=_value_for_family(by_family, "primary"),
        proxy_value=_value_for_family(by_family, "proxy"),
        team_acknowledged_value=_value_for_family(by_family, "team_acknowledged"),
        source_update_count=source_update_count,
        divergent_source_family_count=divergent_source_family_count,
        unresolved_divergence_count=unresolved_divergence_count,
        stale_official_source_count=stale_official_source_count,
        proxy_only_confirmation_count=proxy_only_confirmation_count,
        missing_team_acknowledgement_count=missing_team_acknowledgement_count,
        official_age_seconds=official_age_seconds,
        max_source_age_seconds=max_source_age_seconds,
        divergence_ratio=_ratio(divergent_source_family_count, source_update_count),
        recheck_status=recheck_status,
        recheck_required=recheck_status != "clear",
        reason_codes=reason_codes,
    )


def _reference_value(
    rows: tuple[MarketSourceFamilyDivergenceRecheckInputRow, ...],
) -> str | None:
    official_value = next(
        (row.observed_value for row in rows if row.source_family == "official"),
        None,
    )
    if official_value is not None:
        return official_value
    counts: dict[str, int] = {}
    for row in rows:
        if row.source_family in EVIDENCE_SOURCE_FAMILIES:
            counts[row.observed_value] = counts.get(row.observed_value, 0) + 1
    if not counts:
        return None
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _value_for_family(
    rows_by_family: dict[str, MarketSourceFamilyDivergenceRecheckInputRow],
    source_family: str,
) -> str | None:
    row = rows_by_family.get(source_family)
    return None if row is None else row.observed_value


def _row_reason_codes(
    *,
    unresolved_divergence_count: Decimal,
    stale_official_source_count: Decimal,
    proxy_only_confirmation_count: Decimal,
    missing_team_acknowledgement_count: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if unresolved_divergence_count > ZERO:
        reason_codes.append(UNRESOLVED_DIVERGENCE_REASON)
    if stale_official_source_count > ZERO:
        reason_codes.append(STALE_OFFICIAL_SOURCE_REASON)
    if proxy_only_confirmation_count > ZERO:
        reason_codes.append(PROXY_ONLY_CONFIRMATION_REASON)
    if missing_team_acknowledgement_count > ZERO:
        reason_codes.append(MISSING_TEAM_ACKNOWLEDGEMENT_REASON)
    if not reason_codes:
        reason_codes.append(CLEAR_REASON)
    return tuple(reason_codes)


def _report_reason_codes(
    rows: tuple[MarketSourceFamilyDivergenceRecheckRow, ...],
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for reason_code in REASON_CODES:
        if reason_code == CLEAR_REASON:
            continue
        if any(reason_code in row.reason_codes for row in rows):
            reason_codes.append(reason_code)
    if not reason_codes:
        reason_codes.append(CLEAR_REASON)
    return tuple(reason_codes)


def _row_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if (
        UNRESOLVED_DIVERGENCE_REASON in reason_codes
        or PROXY_ONLY_CONFIRMATION_REASON in reason_codes
        or MISSING_TEAM_ACKNOWLEDGEMENT_REASON in reason_codes
    ):
        return "blocked"
    if STALE_OFFICIAL_SOURCE_REASON in reason_codes:
        return "watch"
    return "clear"


def _report_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if (
        UNRESOLVED_DIVERGENCE_REASON in reason_codes
        or PROXY_ONLY_CONFIRMATION_REASON in reason_codes
        or MISSING_TEAM_ACKNOWLEDGEMENT_REASON in reason_codes
    ):
        return "blocked"
    if STALE_OFFICIAL_SOURCE_REASON in reason_codes:
        return "watch"
    return "clear"


def _normalize_rows(
    value: object,
) -> tuple[MarketSourceFamilyDivergenceRecheckRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not MarketSourceFamilyDivergenceRecheckRow:
            raise ValueError("rows must contain divergence recheck rows")
        require_paper_only_flags(
            "market source family divergence recheck row",
            row,
        )
        if row.market_id in seen:
            raise ValueError("rows must be unique per market_id")
        seen.add(row.market_id)
    expected = _sort_rows(rows)
    if rows != expected:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _sort_rows(
    rows: tuple[MarketSourceFamilyDivergenceRecheckRow, ...],
) -> tuple[MarketSourceFamilyDivergenceRecheckRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_RANK[row.recheck_status],
                -row.missing_team_acknowledgement_count,
                -row.unresolved_divergence_count,
                -row.proxy_only_confirmation_count,
                -row.stale_official_source_count,
                -row.max_source_age_seconds,
                row.market_id,
            ),
        ),
    )


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in REASON_CODES if code in reason_codes) != reason_codes:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _validate_recheck_row(row: MarketSourceFamilyDivergenceRecheckRow) -> None:
    present_source_update_count = _decimal_count(
        sum(
            1
            for value in (
                row.official_value,
                row.primary_value,
                row.proxy_value,
                row.team_acknowledged_value,
            )
            if value is not None
        ),
    )
    if row.source_update_count != present_source_update_count:
        raise ValueError("source_update_count must match populated source families")
    if row.divergent_source_family_count > row.source_update_count:
        raise ValueError(
            "divergent_source_family_count must not exceed source_update_count",
        )
    for field_name in (
        "source_update_count",
        "divergent_source_family_count",
    ):
        if getattr(row, field_name) % ONE != ZERO:
            raise ValueError(f"{field_name} must be a whole Decimal")
    if (
        row.divergent_source_family_count
        != _expected_divergent_source_family_count(row)
    ):
        raise ValueError(
            "divergent_source_family_count must match source family values",
        )
    for field_name in (
        "unresolved_divergence_count",
        "stale_official_source_count",
        "proxy_only_confirmation_count",
        "missing_team_acknowledgement_count",
    ):
        value = getattr(row, field_name)
        if value not in (ZERO, ONE):
            raise ValueError(f"{field_name} must be zero or one")
    if row.unresolved_divergence_count != (
        ONE if row.divergent_source_family_count > ZERO else ZERO
    ):
        raise ValueError(
            "unresolved_divergence_count must match divergent source families",
        )
    expected_proxy_only = (
        ONE
        if row.proxy_value is not None
        and row.official_value is None
        and row.primary_value is None
        else ZERO
    )
    if row.proxy_only_confirmation_count != expected_proxy_only:
        raise ValueError(
            "proxy_only_confirmation_count must match source family values",
        )
    if row.official_value is None and row.official_age_seconds != ZERO:
        raise ValueError("official_age_seconds must be zero without official value")
    if row.official_value is None and row.stale_official_source_count != ZERO:
        raise ValueError(
            "stale_official_source_count must be zero without official value",
        )
    if row.stale_official_source_count > ZERO and row.official_age_seconds == ZERO:
        raise ValueError(
            "stale_official_source_count must match official_age_seconds",
        )
    if row.official_age_seconds > row.max_source_age_seconds:
        raise ValueError(
            "max_source_age_seconds must be at least official_age_seconds",
        )
    if row.team_acknowledged_value is not None:
        expected_missing_team_acknowledgement_count = ZERO
    elif (
        row.unresolved_divergence_count > ZERO
        or row.stale_official_source_count > ZERO
        or row.proxy_only_confirmation_count > ZERO
    ):
        expected_missing_team_acknowledgement_count = row.missing_team_acknowledgement_count
    else:
        expected_missing_team_acknowledgement_count = ZERO
    if (
        row.missing_team_acknowledgement_count
        != expected_missing_team_acknowledgement_count
    ):
        raise ValueError(
            "missing_team_acknowledgement_count must match source family values",
        )
    if row.divergence_ratio != _ratio(
        row.divergent_source_family_count,
        row.source_update_count,
    ):
        raise ValueError("divergence_ratio must match source update counts")
    expected_reason_codes = _row_reason_codes(
        unresolved_divergence_count=row.unresolved_divergence_count,
        stale_official_source_count=row.stale_official_source_count,
        proxy_only_confirmation_count=row.proxy_only_confirmation_count,
        missing_team_acknowledgement_count=row.missing_team_acknowledgement_count,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match recheck row metrics")
    if row.recheck_status != _row_status_from_reason_codes(row.reason_codes):
        raise ValueError("recheck_status must match reason_codes")
    if row.recheck_required is not (row.recheck_status != "clear"):
        raise ValueError("recheck_required must match recheck_status")


def _expected_divergent_source_family_count(
    row: MarketSourceFamilyDivergenceRecheckRow,
) -> Decimal:
    source_values = (
        ("official", row.official_value),
        ("primary", row.primary_value),
        ("proxy", row.proxy_value),
    )
    evidence_values = tuple(
        value for source_family, value in source_values if source_family and value is not None
    )
    if not evidence_values:
        return ZERO
    if row.official_value is not None:
        reference_value = row.official_value
    else:
        counts: dict[str, int] = {}
        for value in evidence_values:
            counts[value] = counts.get(value, 0) + 1
        reference_value = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[
            0
        ][0]
    return _decimal_count(sum(1 for value in evidence_values if value != reference_value))


def _validate_report(report: MarketSourceFamilyDivergenceRecheckReport) -> None:
    if report.market_count != _decimal_count(len(report.rows)):
        raise ValueError("market_count must match rows")
    if report.source_update_count != _sum_decimal(
        row.source_update_count for row in report.rows
    ):
        raise ValueError("source_update_count must match rows")
    if report.clear_market_count != _status_count(report.rows, "clear"):
        raise ValueError("clear_market_count must match rows")
    if report.watch_market_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_market_count must match rows")
    if report.blocked_market_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_market_count must match rows")
    if (
        report.clear_market_count
        + report.watch_market_count
        + report.blocked_market_count
        != report.market_count
    ):
        raise ValueError("market status counts must sum to market_count")
    if report.recheck_required_market_count != _positive_metric_count(
        report.rows,
        "recheck_required",
    ):
        raise ValueError("recheck_required_market_count must match rows")
    expected_counts = {
        "unresolved_divergence_market_count": _positive_metric_count(
            report.rows,
            "unresolved_divergence_count",
        ),
        "stale_official_market_count": _positive_metric_count(
            report.rows,
            "stale_official_source_count",
        ),
        "proxy_only_confirmation_market_count": _positive_metric_count(
            report.rows,
            "proxy_only_confirmation_count",
        ),
        "missing_team_acknowledgement_market_count": _positive_metric_count(
            report.rows,
            "missing_team_acknowledgement_count",
        ),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    expected_ratios = {
        "recheck_required_ratio": _ratio(
            report.recheck_required_market_count,
            report.market_count,
        ),
        "unresolved_divergence_ratio": _ratio(
            report.unresolved_divergence_market_count,
            report.market_count,
        ),
        "stale_official_ratio": _ratio(
            report.stale_official_market_count,
            report.market_count,
        ),
        "proxy_only_confirmation_ratio": _ratio(
            report.proxy_only_confirmation_market_count,
            report.market_count,
        ),
        "missing_team_acknowledgement_ratio": _ratio(
            report.missing_team_acknowledgement_market_count,
            report.market_count,
        ),
    }
    for field_name, expected in expected_ratios.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.max_official_age_seconds != _max_decimal(
        row.official_age_seconds for row in report.rows
    ):
        raise ValueError("max_official_age_seconds must match rows")
    if report.max_source_age_seconds != _max_decimal(
        row.max_source_age_seconds for row in report.rows
    ):
        raise ValueError("max_source_age_seconds must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.report_status != _report_status_from_reason_codes(report.reason_codes):
        raise ValueError("report_status must match reason_codes")


def _status_count(
    rows: tuple[MarketSourceFamilyDivergenceRecheckRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.recheck_status == status))


def _positive_metric_count(
    rows: tuple[MarketSourceFamilyDivergenceRecheckRow, ...],
    field_name: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if getattr(row, field_name) > ZERO))


def _max_decimal(values: object) -> Decimal:
    normalized = tuple(values)  # type: ignore[arg-type]
    if not normalized:
        return ZERO
    return max(normalized)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:  # type: ignore[union-attr]
        total += value
    return total.quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _source_age_seconds(
    generated_at: datetime,
    row: MarketSourceFamilyDivergenceRecheckInputRow | None,
) -> Decimal:
    if row is None:
        return ZERO
    return _age_seconds(generated_at, row.source_updated_at)


def _age_seconds(end_at: datetime, start_at: datetime) -> Decimal:
    delta = _as_utc("end_at", end_at) - _as_utc("start_at", start_at)
    age_seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if age_seconds < ZERO:
        raise ValueError("age_seconds must be nonnegative")
    return age_seconds.quantize(QUANT)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(QUANT)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(QUANT)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_report_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be clear, watch, or blocked")


def _require_recheck_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RECHECK_STATUSES:
        raise ValueError(f"{field_name} must be clear, watch, or blocked")


def _require_source_family(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SOURCE_FAMILIES:
        raise ValueError(
            f"{field_name} must be official, primary, proxy, or team_acknowledged",
        )


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _normalize_optional_public_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_public_string(field_name, value)
    return value


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


__all__ = (
    "DEFAULT_MARKET_SOURCE_FAMILY_DIVERGENCE_RECHECK_REPORT_CONFIG_VERSION",
    "MarketSourceFamilyDivergenceRecheckConfig",
    "MarketSourceFamilyDivergenceRecheckInputRow",
    "MarketSourceFamilyDivergenceRecheckReport",
    "MarketSourceFamilyDivergenceRecheckRow",
    "build_market_source_family_divergence_recheck_report",
    "market_source_family_divergence_recheck_report_to_payload",
)
