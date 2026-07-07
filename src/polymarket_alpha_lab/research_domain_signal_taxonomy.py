"""Pure report-only signal taxonomy for research domain teams."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_SIGNAL_TAXONOMY_CONFIG_VERSION",
    "ResearchDomainSignalTaxonomyCoverageCount",
    "ResearchDomainSignalTaxonomyFilter",
    "ResearchDomainSignalTaxonomyReport",
    "ResearchDomainSignalTaxonomyRow",
    "build_research_domain_signal_taxonomy_report",
    "research_domain_signal_taxonomy_payload",
)


DEFAULT_RESEARCH_DOMAIN_SIGNAL_TAXONOMY_CONFIG_VERSION = (
    "research-domain-signal-taxonomy-v0"
)
DOMAINS = ("politics", "btc", "equity_index", "gold", "soccer", "basketball")
COVERAGE_STATUSES = ("pass", "watch", "block")
STATUS_SEQUENCE = ("block", "watch", "pass")
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

REASON_PREFIX = "research_domain_signal_taxonomy_"
NO_SIGNALS_REASON = f"{REASON_PREFIX}no_signals"
FILTERS_ACTIVE_REASON = f"{REASON_PREFIX}filters_active"
REQUIRED_DOMAINS_PRESENT_REASON = f"{REASON_PREFIX}required_domains_present"
PASS_REASON = f"{REASON_PREFIX}pass"
WATCH_REASON = f"{REASON_PREFIX}watch"
BLOCK_REASON = f"{REASON_PREFIX}block"

REPORT_REASON_SEQUENCE = (
    NO_SIGNALS_REASON,
    FILTERS_ACTIVE_REASON,
    BLOCK_REASON,
    REQUIRED_DOMAINS_PRESENT_REASON,
    WATCH_REASON,
    PASS_REASON,
)
ROW_REASON_SEQUENCE = (
    "coverage_block",
    "coverage_watch",
    "coverage_pass",
    "high_update_cadence",
    "single_source_fragility",
    "cross_domain_dependency",
)
NEXT_STEPS = {
    "pass": "pass_report_only_research_domain_signal_taxonomy",
    "watch": "watch_report_only_research_domain_signal_taxonomy",
    "block": "block_report_only_research_domain_signal_taxonomy",
}
SAFE_TEXT_FRAGMENTS = (
    "credential",
    "private" + "_key",
    "api" + "_key",
    "sec" + "ret",
)


@dataclass(frozen=True)
class ResearchDomainSignalTaxonomyFilter:
    config_version: str = DEFAULT_RESEARCH_DOMAIN_SIGNAL_TAXONOMY_CONFIG_VERSION
    domain_filters: tuple[str, ...] = ()
    coverage_status_filters: tuple[str, ...] = ()
    max_risk_score: Decimal | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainSignalTaxonomyFilter:
            raise TypeError("ResearchDomainSignalTaxonomyFilter does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainSignalTaxonomyFilter:
            raise ValueError("filters must be exactly ResearchDomainSignalTaxonomyFilter")
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "domain_filters",
            _normalize_enum_filter("domain_filters", self.domain_filters, DOMAINS),
        )
        object.__setattr__(
            self,
            "coverage_status_filters",
            _normalize_enum_filter(
                "coverage_status_filters",
                self.coverage_status_filters,
                COVERAGE_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "max_risk_score",
            _require_optional_ratio_decimal("max_risk_score", self.max_risk_score),
        )
        _require_hard_flags("filters", self)


@dataclass(frozen=True)
class ResearchDomainSignalTaxonomyRow:
    domain: str
    signal_class: str
    applicable_scope: tuple[str, ...]
    refresh_requirement: str
    risk_notes: tuple[str, ...]
    coverage_status: str
    risk_score: Decimal | None
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainSignalTaxonomyRow:
            raise TypeError("ResearchDomainSignalTaxonomyRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainSignalTaxonomyRow:
            raise ValueError("row must be exactly ResearchDomainSignalTaxonomyRow")
        _require_enum("domain", self.domain, DOMAINS)
        _require_public_string("signal_class", self.signal_class)
        object.__setattr__(
            self,
            "applicable_scope",
            _normalize_public_string_tuple("applicable_scope", self.applicable_scope),
        )
        _require_public_string("refresh_requirement", self.refresh_requirement)
        object.__setattr__(
            self,
            "risk_notes",
            _normalize_public_string_tuple("risk_notes", self.risk_notes),
        )
        _require_enum("coverage_status", self.coverage_status, COVERAGE_STATUSES)
        object.__setattr__(
            self,
            "risk_score",
            _require_optional_ratio_decimal("risk_score", self.risk_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchDomainSignalTaxonomyCoverageCount:
    coverage_status: str
    count: Decimal
    coverage_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainSignalTaxonomyCoverageCount:
            raise TypeError(
                "ResearchDomainSignalTaxonomyCoverageCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainSignalTaxonomyCoverageCount:
            raise ValueError(
                "coverage count must be exactly ResearchDomainSignalTaxonomyCoverageCount",
            )
        _require_enum("coverage_status", self.coverage_status, COVERAGE_STATUSES)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "coverage_ratio",
            _require_ratio_decimal("coverage_ratio", self.coverage_ratio),
        )
        _require_hard_flags("coverage_count", self)


@dataclass(frozen=True)
class ResearchDomainSignalTaxonomyReport:
    generated_at: datetime
    config_version: str
    status: str
    next_step: str
    signal_count: Decimal
    domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_risk_score: Decimal | None
    rows: tuple[ResearchDomainSignalTaxonomyRow, ...]
    coverage_counts: tuple[ResearchDomainSignalTaxonomyCoverageCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainSignalTaxonomyReport:
            raise TypeError("ResearchDomainSignalTaxonomyReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainSignalTaxonomyReport:
            raise ValueError("report must be exactly ResearchDomainSignalTaxonomyReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_enum("status", self.status, COVERAGE_STATUSES)
        _require_public_string("next_step", self.next_step)
        for field_name in (
            "signal_count",
            "domain_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_risk_score",
            _require_optional_ratio_decimal("max_risk_score", self.max_risk_score),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "coverage_counts",
            _normalize_coverage_counts(self.coverage_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report(self)


def build_research_domain_signal_taxonomy_report(
    *,
    filters: ResearchDomainSignalTaxonomyFilter,
    generated_at: datetime,
) -> ResearchDomainSignalTaxonomyReport:
    if type(filters) is not ResearchDomainSignalTaxonomyFilter:
        raise ValueError("filters must be a ResearchDomainSignalTaxonomyFilter")
    _require_hard_flags("filters", filters)
    report_time = _as_utc("generated_at", generated_at)
    rows = _filtered_rows(_base_rows(), filters)
    return ResearchDomainSignalTaxonomyReport(
        generated_at=report_time,
        config_version=filters.config_version,
        status=_report_status(rows),
        next_step=NEXT_STEPS[_report_status(rows)],
        signal_count=_count(len(rows)),
        domain_count=_count(len({row.domain for row in rows})),
        pass_count=_count(sum(1 for row in rows if row.coverage_status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.coverage_status == "watch")),
        block_count=_count(sum(1 for row in rows if row.coverage_status == "block")),
        max_risk_score=_max_risk_score(rows),
        rows=rows,
        coverage_counts=_coverage_counts(rows),
        reason_codes=_report_reason_codes(rows, filters),
    )


def research_domain_signal_taxonomy_payload(
    report: ResearchDomainSignalTaxonomyReport,
) -> dict[str, Any]:
    if type(report) is not ResearchDomainSignalTaxonomyReport:
        raise ValueError("report must be a ResearchDomainSignalTaxonomyReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
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


def _base_rows() -> tuple[ResearchDomainSignalTaxonomyRow, ...]:
    return tuple(
        _sorted_rows(
            (
                ResearchDomainSignalTaxonomyRow(
                    domain="politics",
                    signal_class="policy_calendar",
                    applicable_scope=(
                        "public_calendar_events",
                        "legislative_timing",
                        "agency_rule_windows",
                    ),
                    refresh_requirement="refresh_daily_and_before_major_votes",
                    risk_notes=(
                        "calendar_slippage_can_delay_resolution_context",
                        "headline_framing_can_overstate_scope",
                    ),
                    coverage_status="pass",
                    risk_score=Decimal("0.360000"),
                    reason_codes=("coverage_pass",),
                ),
                ResearchDomainSignalTaxonomyRow(
                    domain="politics",
                    signal_class="election_integrity",
                    applicable_scope=(
                        "public_vote_admin_updates",
                        "legal_challenge_context",
                        "certification_timing",
                    ),
                    refresh_requirement="refresh_on_each_official_update",
                    risk_notes=(
                        "jurisdiction_rules_can_differ_materially",
                        "single_update_can_change_certification_context",
                    ),
                    coverage_status="block",
                    risk_score=Decimal("0.880000"),
                    reason_codes=(
                        "coverage_block",
                        "high_update_cadence",
                        "cross_domain_dependency",
                    ),
                ),
                ResearchDomainSignalTaxonomyRow(
                    domain="btc",
                    signal_class="chain_flow_context",
                    applicable_scope=(
                        "public_chain_metrics",
                        "large_transfer_context",
                        "settlement_activity",
                    ),
                    refresh_requirement="refresh_hourly_when_conditions_move",
                    risk_notes=(
                        "entity_labeling_can_be_imprecise",
                        "flow_direction_can_be_ambiguous",
                    ),
                    coverage_status="watch",
                    risk_score=Decimal("0.560000"),
                    reason_codes=("coverage_watch", "cross_domain_dependency"),
                ),
                ResearchDomainSignalTaxonomyRow(
                    domain="btc",
                    signal_class="venue_liquidity_context",
                    applicable_scope=(
                        "public_depth_snapshots",
                        "basis_context",
                        "funding_context",
                    ),
                    refresh_requirement="refresh_intraday_during_fast_moves",
                    risk_notes=(
                        "venue_mix_can_shift_quickly",
                        "thin_public_snapshots_can_be_unstable",
                    ),
                    coverage_status="block",
                    risk_score=Decimal("0.900000"),
                    reason_codes=(
                        "coverage_block",
                        "high_update_cadence",
                        "single_source_fragility",
                    ),
                ),
                ResearchDomainSignalTaxonomyRow(
                    domain="equity_index",
                    signal_class="macro_release_calendar",
                    applicable_scope=(
                        "public_release_schedule",
                        "consensus_context",
                        "revision_window",
                    ),
                    refresh_requirement="refresh_before_and_after_release_window",
                    risk_notes=(
                        "revision_risk_can_change_macro_context",
                        "cross_asset_interpretation_can_vary",
                    ),
                    coverage_status="watch",
                    risk_score=Decimal("0.620000"),
                    reason_codes=("coverage_watch", "high_update_cadence"),
                ),
                ResearchDomainSignalTaxonomyRow(
                    domain="equity_index",
                    signal_class="breadth_and_volatility",
                    applicable_scope=(
                        "public_index_breadth",
                        "volatility_context",
                        "sector_rotation",
                    ),
                    refresh_requirement="refresh_each_session_close",
                    risk_notes=(
                        "late_session_reversal_can_shift_context",
                        "index_membership_can_mask_dispersion",
                    ),
                    coverage_status="pass",
                    risk_score=Decimal("0.420000"),
                    reason_codes=("coverage_pass",),
                ),
                ResearchDomainSignalTaxonomyRow(
                    domain="gold",
                    signal_class="real_rate_context",
                    applicable_scope=(
                        "public_rate_curve",
                        "inflation_expectation_context",
                        "currency_context",
                    ),
                    refresh_requirement="refresh_daily_and_after_rate_shocks",
                    risk_notes=(
                        "real_rate_proxy_choice_can_shift_signal",
                        "currency_context_can_dominate_short_windows",
                    ),
                    coverage_status="pass",
                    risk_score=Decimal("0.440000"),
                    reason_codes=("coverage_pass",),
                ),
                ResearchDomainSignalTaxonomyRow(
                    domain="gold",
                    signal_class="official_sector_flow",
                    applicable_scope=(
                        "public_reserve_updates",
                        "import_export_context",
                        "physical_flow_reports",
                    ),
                    refresh_requirement="refresh_when_public_reports_update",
                    risk_notes=(
                        "publication_lag_can_be_material",
                        "physical_flow_reports_can_be_sparse",
                    ),
                    coverage_status="pass",
                    risk_score=Decimal("0.310000"),
                    reason_codes=("coverage_pass",),
                ),
                ResearchDomainSignalTaxonomyRow(
                    domain="soccer",
                    signal_class="lineup_availability",
                    applicable_scope=(
                        "public_team_news",
                        "suspension_context",
                        "travel_context",
                    ),
                    refresh_requirement="refresh_at_team_news_and_lineup_release",
                    risk_notes=(
                        "coach_rotation_can_surprise",
                        "source_language_context_can_matter",
                    ),
                    coverage_status="pass",
                    risk_score=Decimal("0.470000"),
                    reason_codes=("coverage_pass",),
                ),
                ResearchDomainSignalTaxonomyRow(
                    domain="soccer",
                    signal_class="fixture_congestion",
                    applicable_scope=(
                        "public_fixture_schedule",
                        "travel_distance_context",
                        "rest_day_context",
                    ),
                    refresh_requirement="refresh_after_each_fixture_change",
                    risk_notes=(
                        "cup_progression_can_change_rest_context",
                        "weather_delays_can_shift_schedule",
                    ),
                    coverage_status="watch",
                    risk_score=Decimal("0.580000"),
                    reason_codes=("coverage_watch", "cross_domain_dependency"),
                ),
                ResearchDomainSignalTaxonomyRow(
                    domain="basketball",
                    signal_class="injury_rotation",
                    applicable_scope=(
                        "public_injury_reports",
                        "rotation_context",
                        "availability_uncertainty",
                    ),
                    refresh_requirement="refresh_before_each_slate",
                    risk_notes=(
                        "late_scratch_updates_can_change_context",
                        "single_source_availability_can_be_fragile",
                    ),
                    coverage_status="block",
                    risk_score=Decimal("0.910000"),
                    reason_codes=(
                        "coverage_block",
                        "high_update_cadence",
                        "single_source_fragility",
                    ),
                ),
                ResearchDomainSignalTaxonomyRow(
                    domain="basketball",
                    signal_class="schedule_density",
                    applicable_scope=(
                        "public_schedule_context",
                        "rest_day_context",
                        "travel_context",
                    ),
                    refresh_requirement="refresh_daily_during_season",
                    risk_notes=(
                        "overtime_load_can_change_fatigue_context",
                        "travel_context_can_be_team_specific",
                    ),
                    coverage_status="watch",
                    risk_score=Decimal("0.520000"),
                    reason_codes=("coverage_watch",),
                ),
            ),
        ),
    )


def _filtered_rows(
    rows: tuple[ResearchDomainSignalTaxonomyRow, ...],
    filters: ResearchDomainSignalTaxonomyFilter,
) -> tuple[ResearchDomainSignalTaxonomyRow, ...]:
    filtered = rows
    if filters.domain_filters:
        filtered = tuple(row for row in filtered if row.domain in filters.domain_filters)
    if filters.coverage_status_filters:
        filtered = tuple(
            row
            for row in filtered
            if row.coverage_status in filters.coverage_status_filters
        )
    if filters.max_risk_score is not None:
        filtered = tuple(
            row
            for row in filtered
            if row.risk_score is not None and row.risk_score <= filters.max_risk_score
        )
    return _sorted_rows(filtered)


def _sorted_rows(
    rows: tuple[ResearchDomainSignalTaxonomyRow, ...],
) -> tuple[ResearchDomainSignalTaxonomyRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                STATUS_SEQUENCE.index(row.coverage_status),
                row.domain,
                row.signal_class,
            ),
        ),
    )


def _coverage_counts(
    rows: tuple[ResearchDomainSignalTaxonomyRow, ...],
) -> tuple[ResearchDomainSignalTaxonomyCoverageCount, ...]:
    if not rows:
        return (
            ResearchDomainSignalTaxonomyCoverageCount(
                coverage_status="block",
                count=ONE,
                coverage_ratio=ONE,
            ),
        )
    total = _count(len(rows))
    return tuple(
        ResearchDomainSignalTaxonomyCoverageCount(
            coverage_status=status,
            count=_count(sum(1 for row in rows if row.coverage_status == status)),
            coverage_ratio=_ratio(
                _count(sum(1 for row in rows if row.coverage_status == status)),
                total,
            ),
        )
        for status in STATUS_SEQUENCE
        if any(row.coverage_status == status for row in rows)
    )


def _report_reason_codes(
    rows: tuple[ResearchDomainSignalTaxonomyRow, ...],
    filters: ResearchDomainSignalTaxonomyFilter,
) -> tuple[str, ...]:
    if not rows:
        return (NO_SIGNALS_REASON,)
    reasons: set[str] = set()
    if filters.domain_filters or filters.coverage_status_filters or filters.max_risk_score:
        reasons.add(FILTERS_ACTIVE_REASON)
    if set(row.domain for row in rows) == set(DOMAINS):
        reasons.add(REQUIRED_DOMAINS_PRESENT_REASON)
    status = _report_status(rows)
    if status == "block":
        reasons.add(BLOCK_REASON)
    if any(row.coverage_status == "watch" for row in rows):
        reasons.add(WATCH_REASON)
    if status == "pass":
        reasons.add(PASS_REASON)
    return tuple(reason for reason in REPORT_REASON_SEQUENCE if reason in reasons)


def _report_status(rows: tuple[ResearchDomainSignalTaxonomyRow, ...]) -> str:
    if not rows or any(row.coverage_status == "block" for row in rows):
        return "block"
    if any(row.coverage_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _max_risk_score(rows: tuple[ResearchDomainSignalTaxonomyRow, ...]) -> Decimal | None:
    scores = tuple(row.risk_score for row in rows if row.risk_score is not None)
    if not scores:
        return None
    return max(scores)


def _normalize_rows(
    rows: tuple[ResearchDomainSignalTaxonomyRow, ...],
) -> tuple[ResearchDomainSignalTaxonomyRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchDomainSignalTaxonomyRow:
            raise ValueError("rows must contain ResearchDomainSignalTaxonomyRow")
        _require_hard_flags("row", row)
    if rows != _sorted_rows(rows):
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_coverage_counts(
    counts: tuple[ResearchDomainSignalTaxonomyCoverageCount, ...],
) -> tuple[ResearchDomainSignalTaxonomyCoverageCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("coverage_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchDomainSignalTaxonomyCoverageCount:
            raise ValueError(
                "coverage_counts must contain ResearchDomainSignalTaxonomyCoverageCount",
            )
        _require_hard_flags("coverage_count", count)
    sorted_counts = tuple(
        sorted(counts, key=lambda count: STATUS_SEQUENCE.index(count.coverage_status)),
    )
    if counts != sorted_counts:
        raise ValueError("coverage_counts must be sorted deterministically")
    return counts


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_enum("reason_codes", reason_code, ROW_REASON_SEQUENCE)
    normalized = tuple(reason for reason in ROW_REASON_SEQUENCE if reason in value)
    if normalized != value:
        raise ValueError("reason_codes must be unique and sorted")
    return normalized


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_enum("reason_codes", reason_code, REPORT_REASON_SEQUENCE)
    normalized = tuple(reason for reason in REPORT_REASON_SEQUENCE if reason in value)
    if normalized != value:
        raise ValueError("reason_codes must be unique and sorted")
    return normalized


def _normalize_enum_filter(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for item in value:
        _require_enum(field_name, item, allowed)
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must be unique")
    normalized = tuple(item for item in allowed if item in value)
    return normalized


def _normalize_public_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a nonempty tuple")
    normalized = []
    for item in value:
        normalized.append(_require_public_string(field_name, item))
    result = tuple(normalized)
    if len(set(result)) != len(result):
        raise ValueError(f"{field_name} must be unique")
    return result


def _validate_row(row: ResearchDomainSignalTaxonomyRow) -> None:
    expected_reason = f"coverage_{row.coverage_status}"
    if expected_reason not in row.reason_codes:
        raise ValueError("reason_codes must include coverage_status")
    coverage_reasons = tuple(
        reason
        for reason in row.reason_codes
        if reason in ("coverage_pass", "coverage_watch", "coverage_block")
    )
    if coverage_reasons != (expected_reason,):
        raise ValueError("reason_codes must match coverage_status")
    if row.risk_score is not None:
        if row.coverage_status == "pass" and row.risk_score > Decimal("0.500000"):
            raise ValueError("risk_score must support pass coverage_status")
        if (
            row.coverage_status == "watch"
            and (row.risk_score <= Decimal("0.500000") or row.risk_score >= Decimal("0.800000"))
        ):
            raise ValueError("risk_score must support watch coverage_status")
        if row.coverage_status == "block" and row.risk_score < Decimal("0.800000"):
            raise ValueError("risk_score must support block coverage_status")


def _validate_report(report: ResearchDomainSignalTaxonomyReport) -> None:
    if report.next_step != NEXT_STEPS[report.status]:
        raise ValueError("next_step must match status")
    if report.signal_count != _count(len(report.rows)):
        raise ValueError("signal_count must match rows")
    if report.domain_count != _count(len({row.domain for row in report.rows})):
        raise ValueError("domain_count must match rows")
    if report.pass_count != _count(
        sum(1 for row in report.rows if row.coverage_status == "pass"),
    ):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(
        sum(1 for row in report.rows if row.coverage_status == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(
        sum(1 for row in report.rows if row.coverage_status == "block"),
    ):
        raise ValueError("block_count must match rows")
    if report.max_risk_score != _max_risk_score(report.rows):
        raise ValueError("max_risk_score must match rows")
    if report.coverage_counts != _coverage_counts(report.rows):
        raise ValueError("coverage_counts must match rows")
    expected_status = _report_status(report.rows)
    if report.status != expected_status:
        raise ValueError("status must match rows")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_enum(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public string")
    lowered = value.lower()
    for unsafe in SAFE_TEXT_FRAGMENTS:
        if unsafe in lowered:
            raise ValueError(f"{field_name} must be public")
    return value


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
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be from 0 to 1")
    return _quantize(normalized)


def _require_optional_ratio_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return _quantize(normalized)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
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
