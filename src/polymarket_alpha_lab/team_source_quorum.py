"""Pure report-only source quorum summaries for specialist research items."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext

from polymarket_alpha_lab.team_taxonomy import require_team_id


DEFAULT_TEAM_SOURCE_QUORUM_CONFIG_VERSION = "team-source-quorum-v0"

PASS_REASON = "team_source_quorum_passed"
EMPTY_REASON = "team_source_quorum_empty_items"
INSUFFICIENT_FAMILY_REASON = "team_source_quorum_insufficient_source_families"
STALE_SOURCE_REASON = "team_source_quorum_stale_sources_present"
CURRENT_SOURCE_REASON = "team_source_quorum_insufficient_current_sources"
CORROBORATION_REASON = "team_source_quorum_insufficient_corroboration"
BLOCKED_SOURCE_REASON = "team_source_quorum_blocked_sources_present"
MISSING_SOURCE_REASON = "team_source_quorum_missing_sources_present"

SUMMARY_REASON_CODES = (
    PASS_REASON,
    EMPTY_REASON,
    INSUFFICIENT_FAMILY_REASON,
    STALE_SOURCE_REASON,
    CURRENT_SOURCE_REASON,
    CORROBORATION_REASON,
    BLOCKED_SOURCE_REASON,
    MISSING_SOURCE_REASON,
)
SUMMARY_STATUSES = ("pass", "watch", "blocked")
SOURCE_STATUSES = ("current", "stale", "missing", "blocked")
SOURCE_STATUS_WEIGHT = {"blocked": 0, "missing": 1, "stale": 2, "current": 3}
ITEM_REASON_CODE_SEQUENCE = (
    EMPTY_REASON,
    BLOCKED_SOURCE_REASON,
    MISSING_SOURCE_REASON,
    STALE_SOURCE_REASON,
    INSUFFICIENT_FAMILY_REASON,
    CURRENT_SOURCE_REASON,
    CORROBORATION_REASON,
    PASS_REASON,
)
NEXT_STEPS = {
    "pass": "allow_report_only_research_item_summary",
    "watch": "refresh_report_only_research_item_sources",
    "blocked": "block_report_only_research_item_summary",
}
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO_DECIMAL = Decimal("0.000000")
ONE_DECIMAL = Decimal("1.000000")


__all__ = (
    "DEFAULT_TEAM_SOURCE_QUORUM_CONFIG_VERSION",
    "TeamSourceQuorumConfig",
    "TeamSourceQuorumItem",
    "TeamSourceQuorumItemStatus",
    "TeamSourceQuorumReasonCodeCount",
    "TeamSourceQuorumReport",
    "TeamSourceQuorumSource",
    "TeamSourceQuorumSourceStatus",
    "build_team_source_quorum_summary",
)


@dataclass(frozen=True)
class TeamSourceQuorumConfig:
    config_version: str = DEFAULT_TEAM_SOURCE_QUORUM_CONFIG_VERSION
    max_source_age_seconds: Decimal = Decimal("86400.000000")
    min_independent_source_families: Decimal = Decimal("2.000000")
    min_current_source_count: Decimal = Decimal("2.000000")
    min_corroboration_coverage_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _require_positive_decimal("max_source_age_seconds", self.max_source_age_seconds),
        )
        object.__setattr__(
            self,
            "min_independent_source_families",
            _require_positive_integral_decimal(
                "min_independent_source_families",
                self.min_independent_source_families,
            ),
        )
        object.__setattr__(
            self,
            "min_current_source_count",
            _require_positive_integral_decimal(
                "min_current_source_count",
                self.min_current_source_count,
            ),
        )
        object.__setattr__(
            self,
            "min_corroboration_coverage_ratio",
            _require_coverage_ratio(
                "min_corroboration_coverage_ratio",
                self.min_corroboration_coverage_ratio,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class TeamSourceQuorumSource:
    team_id: str
    item_id: str
    source_id: str
    source_family: str
    observed_at: datetime | None = None
    corroborates_item: bool = False
    source_config_version: str = DEFAULT_TEAM_SOURCE_QUORUM_CONFIG_VERSION
    missing_reason: str | None = None
    blocked_reason: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_canonical_string("item_id", self.item_id)
        _require_redacted_identifier("item_id", self.item_id)
        _require_canonical_string("source_id", self.source_id)
        _require_redacted_identifier("source_id", self.source_id)
        _require_canonical_string("source_family", self.source_family)
        _require_redacted_identifier("source_family", self.source_family)
        if self.observed_at is not None:
            object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if type(self.corroborates_item) is not bool:
            raise ValueError("corroborates_item must be a bool")
        _require_canonical_string("source_config_version", self.source_config_version)
        _require_optional_canonical_string("missing_reason", self.missing_reason)
        _require_optional_canonical_string("blocked_reason", self.blocked_reason)
        _validate_source_shape(self)
        _require_hard_flags("source", self)


@dataclass(frozen=True)
class TeamSourceQuorumSourceStatus:
    team_id: str
    item_id: str
    source_id: str
    source_family: str
    source_status: str
    observed_at: datetime | None
    source_age_seconds: Decimal | None
    corroborates_item: bool
    source_config_version: str
    missing_reason: str | None
    blocked_reason: str | None
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_canonical_string("item_id", self.item_id)
        _require_redacted_identifier("item_id", self.item_id)
        _require_canonical_string("source_id", self.source_id)
        _require_redacted_identifier("source_id", self.source_id)
        _require_canonical_string("source_family", self.source_family)
        _require_redacted_identifier("source_family", self.source_family)
        if type(self.source_status) is not str or self.source_status not in SOURCE_STATUSES:
            raise ValueError("source_status must be a known source status")
        if self.observed_at is not None:
            object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if self.source_age_seconds is not None:
            object.__setattr__(
                self,
                "source_age_seconds",
                _require_nonnegative_decimal(
                    "source_age_seconds",
                    self.source_age_seconds,
                ),
            )
        if type(self.corroborates_item) is not bool:
            raise ValueError("corroborates_item must be a bool")
        _require_canonical_string("source_config_version", self.source_config_version)
        _require_optional_canonical_string("missing_reason", self.missing_reason)
        _require_optional_canonical_string("blocked_reason", self.blocked_reason)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=SUMMARY_REASON_CODES,
            ),
        )
        _validate_source_status_shape(self)
        _require_hard_flags("source_status", self)


@dataclass(frozen=True)
class TeamSourceQuorumItem:
    team_id: str
    item_id: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_canonical_string("item_id", self.item_id)
        _require_redacted_identifier("item_id", self.item_id)
        _require_hard_flags("item", self)


@dataclass(frozen=True)
class TeamSourceQuorumItemStatus:
    team_id: str
    item_id: str
    summary_status: str
    required_source_family_count: Decimal
    observed_source_family_count: Decimal
    current_source_family_count: Decimal
    required_current_source_count: Decimal
    current_source_count: Decimal
    stale_source_count: Decimal
    missing_source_count: Decimal
    blocked_source_count: Decimal
    corroborating_current_source_count: Decimal
    corroboration_coverage_ratio: Decimal
    max_source_age_seconds: Decimal | None
    reason_codes: tuple[str, ...]
    readiness_gap_count: Decimal = ZERO_DECIMAL
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_canonical_string("item_id", self.item_id)
        _require_redacted_identifier("item_id", self.item_id)
        if type(self.summary_status) is not str or self.summary_status not in SUMMARY_STATUSES:
            raise ValueError("summary_status must be pass, watch, or blocked")
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
            "observed_source_family_count",
            _require_nonnegative_decimal(
                "observed_source_family_count",
                self.observed_source_family_count,
            ),
        )
        object.__setattr__(
            self,
            "current_source_family_count",
            _require_nonnegative_decimal(
                "current_source_family_count",
                self.current_source_family_count,
            ),
        )
        object.__setattr__(
            self,
            "required_current_source_count",
            _require_positive_decimal(
                "required_current_source_count",
                self.required_current_source_count,
            ),
        )
        for field_name in (
            "current_source_count",
            "stale_source_count",
            "missing_source_count",
            "blocked_source_count",
            "corroborating_current_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "corroboration_coverage_ratio",
            _require_coverage_ratio(
                "corroboration_coverage_ratio",
                self.corroboration_coverage_ratio,
            ),
        )
        if self.max_source_age_seconds is not None:
            object.__setattr__(
                self,
                "max_source_age_seconds",
                _require_nonnegative_decimal(
                    "max_source_age_seconds",
                    self.max_source_age_seconds,
                ),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=SUMMARY_REASON_CODES,
            ),
        )
        _require_item_reason_code_sequence("reason_codes", self.reason_codes)
        object.__setattr__(
            self,
            "readiness_gap_count",
            _require_nonnegative_decimal("readiness_gap_count", self.readiness_gap_count),
        )
        _validate_item_status_consistency(self)
        _require_hard_flags("item_status", self)


@dataclass(frozen=True)
class TeamSourceQuorumReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_summary_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class TeamSourceQuorumReport:
    generated_at: datetime
    config_version: str
    team_id: str | None
    summary_status: str
    recommended_next_step: str
    item_count: Decimal
    pass_item_count: Decimal
    watch_item_count: Decimal
    blocked_item_count: Decimal
    required_source_family_count: Decimal
    required_current_source_count: Decimal
    min_corroboration_coverage_ratio: Decimal
    current_source_count: Decimal
    stale_source_count: Decimal
    missing_source_count: Decimal
    blocked_source_count: Decimal
    corroborating_current_source_count: Decimal
    corroboration_coverage_ratio: Decimal
    max_source_age_seconds: Decimal
    max_observed_source_age_seconds: Decimal | None
    source_statuses: tuple[TeamSourceQuorumSourceStatus, ...]
    item_statuses: tuple[TeamSourceQuorumItemStatus, ...]
    source_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[TeamSourceQuorumReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    readiness_gap_count: Decimal = ZERO_DECIMAL
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.team_id is not None:
            object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        if type(self.summary_status) is not str or self.summary_status not in SUMMARY_STATUSES:
            raise ValueError("summary_status must be pass, watch, or blocked")
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "item_count",
            "pass_item_count",
            "watch_item_count",
            "blocked_item_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
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
            "required_current_source_count",
            _require_positive_decimal(
                "required_current_source_count",
                self.required_current_source_count,
            ),
        )
        object.__setattr__(
            self,
            "min_corroboration_coverage_ratio",
            _require_coverage_ratio(
                "min_corroboration_coverage_ratio",
                self.min_corroboration_coverage_ratio,
            ),
        )
        for field_name in (
            "current_source_count",
            "stale_source_count",
            "missing_source_count",
            "blocked_source_count",
            "corroborating_current_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "corroboration_coverage_ratio",
            _require_coverage_ratio(
                "corroboration_coverage_ratio",
                self.corroboration_coverage_ratio,
            ),
        )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _require_positive_decimal("max_source_age_seconds", self.max_source_age_seconds),
        )
        if self.max_observed_source_age_seconds is not None:
            object.__setattr__(
                self,
                "max_observed_source_age_seconds",
                _require_nonnegative_decimal(
                    "max_observed_source_age_seconds",
                    self.max_observed_source_age_seconds,
                ),
            )
        object.__setattr__(
            self,
            "source_statuses",
            _normalize_source_statuses(self.source_statuses),
        )
        object.__setattr__(
            self,
            "item_statuses",
            _normalize_item_statuses(self.item_statuses),
        )
        object.__setattr__(
            self,
            "source_config_versions",
            _normalize_source_config_versions(self.source_config_versions),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=SUMMARY_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "readiness_gap_count",
            _require_nonnegative_decimal("readiness_gap_count", self.readiness_gap_count),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_team_source_quorum_summary(
    sources: list[TeamSourceQuorumSource] | tuple[TeamSourceQuorumSource, ...],
    *,
    config: TeamSourceQuorumConfig,
    generated_at: datetime,
    expected_items: list[TeamSourceQuorumItem] | tuple[TeamSourceQuorumItem, ...] = (),
) -> TeamSourceQuorumReport:
    if type(config) is not TeamSourceQuorumConfig:
        raise ValueError("config must be a TeamSourceQuorumConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_sources = _normalize_sources(sources)
    normalized_items = _normalize_expected_items(expected_items)
    source_statuses = _source_statuses(
        normalized_sources,
        generated_at=generated_at_utc,
        max_source_age_seconds=config.max_source_age_seconds,
    )
    item_statuses = _item_statuses(
        source_statuses=source_statuses,
        expected_items=normalized_items,
        config=config,
    )
    reason_codes = _report_reason_codes(item_statuses)
    reason_code_counts = _reason_code_counts_for_items(item_statuses)
    summary_status = _summary_status(reason_codes)
    current_source_count = _count_decimal(
        sum(1 for row in source_statuses if row.source_status == "current"),
    )
    stale_source_count = _count_decimal(
        sum(1 for row in source_statuses if row.source_status == "stale"),
    )
    missing_source_count = _count_decimal(
        sum(1 for row in source_statuses if row.source_status == "missing"),
    )
    blocked_source_count = _count_decimal(
        sum(1 for row in source_statuses if row.source_status == "blocked"),
    )
    corroborating_current_source_count = _count_decimal(
        sum(
            1
            for row in source_statuses
            if row.source_status == "current" and row.corroborates_item
        ),
    )

    return TeamSourceQuorumReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        team_id=_report_team_id(item_statuses),
        summary_status=summary_status,
        recommended_next_step=NEXT_STEPS[summary_status],
        item_count=_count_decimal(len(item_statuses)),
        pass_item_count=_count_decimal(
            sum(1 for row in item_statuses if row.summary_status == "pass"),
        ),
        watch_item_count=_count_decimal(
            sum(1 for row in item_statuses if row.summary_status == "watch"),
        ),
        blocked_item_count=_count_decimal(
            sum(1 for row in item_statuses if row.summary_status == "blocked"),
        ),
        required_source_family_count=config.min_independent_source_families,
        required_current_source_count=config.min_current_source_count,
        min_corroboration_coverage_ratio=config.min_corroboration_coverage_ratio,
        current_source_count=current_source_count,
        stale_source_count=stale_source_count,
        missing_source_count=missing_source_count,
        blocked_source_count=blocked_source_count,
        corroborating_current_source_count=corroborating_current_source_count,
        corroboration_coverage_ratio=_coverage_ratio(
            corroborating_current_source_count,
            current_source_count,
        ),
        max_source_age_seconds=config.max_source_age_seconds,
        max_observed_source_age_seconds=_max_source_age_seconds(source_statuses),
        source_statuses=source_statuses,
        item_statuses=item_statuses,
        source_config_versions=_source_config_versions(source_statuses),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
        readiness_gap_count=sum(
            (row.readiness_gap_count for row in item_statuses),
            ZERO_DECIMAL,
        ),
    )


def _source_statuses(
    sources: tuple[TeamSourceQuorumSource, ...],
    *,
    generated_at: datetime,
    max_source_age_seconds: Decimal,
) -> tuple[TeamSourceQuorumSourceStatus, ...]:
    return tuple(
        sorted(
            (
                _source_status(
                    source,
                    generated_at=generated_at,
                    max_source_age_seconds=max_source_age_seconds,
                )
                for source in sources
            ),
            key=lambda row: (
                row.team_id,
                row.item_id,
                SOURCE_STATUS_WEIGHT[row.source_status],
                row.source_family,
                row.source_id,
            ),
        )
    )


def _source_status(
    source: TeamSourceQuorumSource,
    *,
    generated_at: datetime,
    max_source_age_seconds: Decimal,
) -> TeamSourceQuorumSourceStatus:
    if source.blocked_reason is not None:
        return TeamSourceQuorumSourceStatus(
            team_id=source.team_id,
            item_id=source.item_id,
            source_id=source.source_id,
            source_family=source.source_family,
            source_status="blocked",
            observed_at=None,
            source_age_seconds=None,
            corroborates_item=False,
            source_config_version=source.source_config_version,
            missing_reason=None,
            blocked_reason=source.blocked_reason,
            reason_codes=(BLOCKED_SOURCE_REASON,),
        )
    if source.missing_reason is not None:
        return TeamSourceQuorumSourceStatus(
            team_id=source.team_id,
            item_id=source.item_id,
            source_id=source.source_id,
            source_family=source.source_family,
            source_status="missing",
            observed_at=None,
            source_age_seconds=None,
            corroborates_item=False,
            source_config_version=source.source_config_version,
            missing_reason=source.missing_reason,
            blocked_reason=None,
            reason_codes=(MISSING_SOURCE_REASON,),
        )
    if source.observed_at is None:
        raise ValueError("observed_at is required for observed sources")
    if source.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    age_seconds = _age_seconds(generated_at, source.observed_at)
    source_status = "current" if age_seconds <= max_source_age_seconds else "stale"
    return TeamSourceQuorumSourceStatus(
        team_id=source.team_id,
        item_id=source.item_id,
        source_id=source.source_id,
        source_family=source.source_family,
        source_status=source_status,
        observed_at=source.observed_at,
        source_age_seconds=age_seconds,
        corroborates_item=source.corroborates_item and source_status == "current",
        source_config_version=source.source_config_version,
        missing_reason=None,
        blocked_reason=None,
        reason_codes=(PASS_REASON if source_status == "current" else STALE_SOURCE_REASON,),
    )


def _item_statuses(
    *,
    source_statuses: tuple[TeamSourceQuorumSourceStatus, ...],
    expected_items: tuple[TeamSourceQuorumItem, ...],
    config: TeamSourceQuorumConfig,
) -> tuple[TeamSourceQuorumItemStatus, ...]:
    keys = {(item.team_id, item.item_id) for item in expected_items}
    keys.update((row.team_id, row.item_id) for row in source_statuses)
    return tuple(
        _item_status(
            team_id=team_id,
            item_id=item_id,
            source_statuses=tuple(
                row
                for row in source_statuses
                if row.team_id == team_id and row.item_id == item_id
            ),
            config=config,
        )
        for team_id, item_id in sorted(keys)
    )


def _item_status(
    *,
    team_id: str,
    item_id: str,
    source_statuses: tuple[TeamSourceQuorumSourceStatus, ...],
    config: TeamSourceQuorumConfig,
) -> TeamSourceQuorumItemStatus:
    current_source_count_int = sum(
        1 for row in source_statuses if row.source_status == "current"
    )
    stale_source_count_int = sum(1 for row in source_statuses if row.source_status == "stale")
    missing_source_count_int = sum(
        1 for row in source_statuses if row.source_status == "missing"
    )
    blocked_source_count_int = sum(
        1 for row in source_statuses if row.source_status == "blocked"
    )
    current_families = frozenset(
        row.source_family for row in source_statuses if row.source_status == "current"
    )
    observed_families = frozenset(
        row.source_family
        for row in source_statuses
        if row.source_status in ("current", "stale")
    )
    corroborating_current_source_count_int = sum(
        1
        for row in source_statuses
        if row.source_status == "current" and row.corroborates_item
    )
    reason_codes = _item_reason_codes(
        source_count=len(source_statuses),
        current_source_count=current_source_count_int,
        stale_source_count=stale_source_count_int,
        missing_source_count=missing_source_count_int,
        blocked_source_count=blocked_source_count_int,
        current_source_family_count=len(current_families),
        min_source_family_count=config.min_independent_source_families,
        min_current_source_count=config.min_current_source_count,
        corroboration_coverage_ratio=_coverage_ratio(
            _count_decimal(corroborating_current_source_count_int),
            _count_decimal(current_source_count_int),
        ),
        min_corroboration_coverage_ratio=config.min_corroboration_coverage_ratio,
    )
    return TeamSourceQuorumItemStatus(
        team_id=team_id,
        item_id=item_id,
        summary_status=_summary_status(reason_codes),
        required_source_family_count=config.min_independent_source_families,
        observed_source_family_count=_count_decimal(len(observed_families)),
        current_source_family_count=_count_decimal(len(current_families)),
        required_current_source_count=config.min_current_source_count,
        current_source_count=_count_decimal(current_source_count_int),
        stale_source_count=_count_decimal(stale_source_count_int),
        missing_source_count=_count_decimal(missing_source_count_int),
        blocked_source_count=_count_decimal(blocked_source_count_int),
        corroborating_current_source_count=_count_decimal(
            corroborating_current_source_count_int,
        ),
        corroboration_coverage_ratio=_coverage_ratio(
            _count_decimal(corroborating_current_source_count_int),
            _count_decimal(current_source_count_int),
        ),
        max_source_age_seconds=_max_source_age_seconds(source_statuses),
        reason_codes=reason_codes,
        readiness_gap_count=_readiness_gap_count(reason_codes),
    )


def _item_reason_codes(
    *,
    source_count: int,
    current_source_count: int,
    stale_source_count: int,
    missing_source_count: int,
    blocked_source_count: int,
    current_source_family_count: int,
    min_source_family_count: Decimal,
    min_current_source_count: Decimal,
    corroboration_coverage_ratio: Decimal,
    min_corroboration_coverage_ratio: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if source_count == 0:
        reason_codes.append(EMPTY_REASON)
    if blocked_source_count > 0:
        reason_codes.append(BLOCKED_SOURCE_REASON)
    if missing_source_count > 0:
        reason_codes.append(MISSING_SOURCE_REASON)
    if stale_source_count > 0:
        reason_codes.append(STALE_SOURCE_REASON)
    if current_source_family_count < min_source_family_count:
        reason_codes.append(INSUFFICIENT_FAMILY_REASON)
    if current_source_count < min_current_source_count:
        reason_codes.append(CURRENT_SOURCE_REASON)
    if current_source_count > 0 and corroboration_coverage_ratio < min_corroboration_coverage_ratio:
        reason_codes.append(CORROBORATION_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return tuple(reason_codes)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code
        in (
            EMPTY_REASON,
            INSUFFICIENT_FAMILY_REASON,
            CURRENT_SOURCE_REASON,
            CORROBORATION_REASON,
            BLOCKED_SOURCE_REASON,
            MISSING_SOURCE_REASON,
        )
        for reason_code in reason_codes
    ):
        return "blocked"
    if reason_codes == (STALE_SOURCE_REASON,):
        return "watch"
    if reason_codes == (PASS_REASON,):
        return "pass"
    raise ValueError("reason_codes must contain known quorum reasons")


def _report_reason_codes(
    item_statuses: tuple[TeamSourceQuorumItemStatus, ...],
) -> tuple[str, ...]:
    if not item_statuses:
        return (EMPTY_REASON,)
    reason_codes: list[str] = []
    for item_status in item_statuses:
        for reason_code in item_status.reason_codes:
            if reason_code not in reason_codes:
                reason_codes.append(reason_code)
    if len(reason_codes) > 1 and PASS_REASON in reason_codes:
        reason_codes.remove(PASS_REASON)
    return tuple(reason_codes)


def _readiness_gap_count(reason_codes: tuple[str, ...]) -> Decimal:
    return _count_decimal(sum(1 for reason_code in reason_codes if reason_code != PASS_REASON))


def _normalize_sources(
    sources: list[TeamSourceQuorumSource] | tuple[TeamSourceQuorumSource, ...],
) -> tuple[TeamSourceQuorumSource, ...]:
    if type(sources) not in (list, tuple):
        raise ValueError("sources must be a list or tuple")
    normalized_sources = tuple(sources)
    seen_source_ids: set[str] = set()
    for source in normalized_sources:
        if type(source) is not TeamSourceQuorumSource:
            raise ValueError("sources must contain TeamSourceQuorumSource")
        _require_hard_flags("source", source)
        if source.source_id in seen_source_ids:
            raise ValueError("source_id values must be unique")
        seen_source_ids.add(source.source_id)
    return normalized_sources


def _normalize_expected_items(
    expected_items: list[TeamSourceQuorumItem] | tuple[TeamSourceQuorumItem, ...],
) -> tuple[TeamSourceQuorumItem, ...]:
    if type(expected_items) not in (list, tuple):
        raise ValueError("expected_items must be a list or tuple")
    normalized_items = tuple(expected_items)
    seen_keys: set[tuple[str, str]] = set()
    for item in normalized_items:
        if type(item) is not TeamSourceQuorumItem:
            raise ValueError("expected_items must contain TeamSourceQuorumItem")
        _require_hard_flags("item", item)
        key = (item.team_id, item.item_id)
        if key in seen_keys:
            raise ValueError("expected_items must be unique by team_id and item_id")
        seen_keys.add(key)
    return normalized_items


def _normalize_source_statuses(
    source_statuses: tuple[TeamSourceQuorumSourceStatus, ...],
) -> tuple[TeamSourceQuorumSourceStatus, ...]:
    if type(source_statuses) not in (list, tuple):
        raise ValueError("source_statuses must be a list or tuple")
    statuses = tuple(source_statuses)
    seen_source_ids: set[str] = set()
    for status in statuses:
        if type(status) is not TeamSourceQuorumSourceStatus:
            raise ValueError("source_statuses must contain source status rows")
        _require_hard_flags("source_status", status)
        if status.source_id in seen_source_ids:
            raise ValueError("source_statuses source_id values must be unique")
        seen_source_ids.add(status.source_id)
    expected = tuple(
        sorted(
            statuses,
            key=lambda row: (
                row.team_id,
                row.item_id,
                SOURCE_STATUS_WEIGHT[row.source_status],
                row.source_family,
                row.source_id,
            ),
        )
    )
    if statuses != expected:
        raise ValueError("source_statuses must be sorted deterministically")
    return statuses


def _normalize_item_statuses(
    item_statuses: tuple[TeamSourceQuorumItemStatus, ...],
) -> tuple[TeamSourceQuorumItemStatus, ...]:
    if type(item_statuses) not in (list, tuple):
        raise ValueError("item_statuses must be a list or tuple")
    statuses = tuple(item_statuses)
    seen_keys: set[tuple[str, str]] = set()
    for status in statuses:
        if type(status) is not TeamSourceQuorumItemStatus:
            raise ValueError("item_statuses must contain item status rows")
        _require_hard_flags("item_status", status)
        key = (status.team_id, status.item_id)
        if key in seen_keys:
            raise ValueError("item_statuses must be unique by team_id and item_id")
        seen_keys.add(key)
    if statuses != tuple(sorted(statuses, key=lambda row: (row.team_id, row.item_id))):
        raise ValueError("item_statuses must be sorted by team_id and item_id")
    return statuses


def _normalize_source_config_versions(
    source_config_versions: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(source_config_versions) not in (list, tuple):
        raise ValueError("source_config_versions must be a list or tuple")
    versions: list[tuple[str, str]] = []
    seen_source_ids: set[str] = set()
    for item in source_config_versions:
        if type(item) not in (list, tuple) or len(item) != 2:
            raise ValueError("source_config_versions entries must be source/version pairs")
        source_id, source_config_version = item
        _require_canonical_string("source_config_versions source_id", source_id)
        _require_redacted_identifier("source_config_versions source_id", source_id)
        _require_canonical_string(
            "source_config_versions source_config_version",
            source_config_version,
        )
        if source_id in seen_source_ids:
            raise ValueError("source_config_versions source_id values must be unique")
        seen_source_ids.add(source_id)
        versions.append((source_id, source_config_version))
    normalized = tuple(versions)
    if normalized != tuple(sorted(normalized)):
        raise ValueError("source_config_versions must be sorted by source_id")
    return normalized


def _normalize_reason_code_counts(
    reason_code_counts: tuple[TeamSourceQuorumReasonCodeCount, ...],
) -> tuple[TeamSourceQuorumReasonCodeCount, ...]:
    if type(reason_code_counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(reason_code_counts)
    seen_reason_codes: set[str] = set()
    for count in counts:
        if type(count) is not TeamSourceQuorumReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason_code_count", count)
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(count.reason_code)
    if tuple(count.reason_code for count in counts) != tuple(
        sorted(count.reason_code for count in counts)
    ):
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _source_config_versions(
    source_statuses: tuple[TeamSourceQuorumSourceStatus, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(
        sorted((row.source_id, row.source_config_version) for row in source_statuses)
    )


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[TeamSourceQuorumReasonCodeCount, ...]:
    return tuple(
        TeamSourceQuorumReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(sum(1 for item in reason_codes if item == reason_code)),
        )
        for reason_code in sorted(set(reason_codes))
    )


def _reason_code_counts_for_items(
    item_statuses: tuple[TeamSourceQuorumItemStatus, ...],
) -> tuple[TeamSourceQuorumReasonCodeCount, ...]:
    reason_codes = tuple(
        reason_code
        for item_status in item_statuses
        for reason_code in item_status.reason_codes
        if reason_code != PASS_REASON or item_status.summary_status == "pass"
    )
    return _reason_code_counts(reason_codes or (EMPTY_REASON,))


def _max_source_age_seconds(
    source_statuses: tuple[TeamSourceQuorumSourceStatus, ...],
) -> Decimal | None:
    ages = tuple(
        row.source_age_seconds
        for row in source_statuses
        if row.source_age_seconds is not None
    )
    return max(ages) if ages else None


def _report_team_id(item_statuses: tuple[TeamSourceQuorumItemStatus, ...]) -> str | None:
    team_ids = tuple(sorted({row.team_id for row in item_statuses}))
    if len(team_ids) == 1:
        return team_ids[0]
    return None


def _validate_report_consistency(report: TeamSourceQuorumReport) -> None:
    if report.item_count != _count_decimal(len(report.item_statuses)):
        raise ValueError("item_count must match item_statuses")
    if report.pass_item_count != _count_decimal(
        sum(1 for row in report.item_statuses if row.summary_status == "pass"),
    ):
        raise ValueError("pass_item_count must match item_statuses")
    if report.watch_item_count != _count_decimal(
        sum(1 for row in report.item_statuses if row.summary_status == "watch"),
    ):
        raise ValueError("watch_item_count must match item_statuses")
    if report.blocked_item_count != _count_decimal(
        sum(1 for row in report.item_statuses if row.summary_status == "blocked"),
    ):
        raise ValueError("blocked_item_count must match item_statuses")
    if report.team_id != _report_team_id(report.item_statuses):
        raise ValueError("team_id must match item_statuses")
    for field_name, source_status in (
        ("current_source_count", "current"),
        ("stale_source_count", "stale"),
        ("missing_source_count", "missing"),
        ("blocked_source_count", "blocked"),
    ):
        if getattr(report, field_name) != _count_decimal(
            sum(1 for row in report.source_statuses if row.source_status == source_status),
        ):
            raise ValueError(f"{field_name} must match source_statuses")
    expected_corroborating = _count_decimal(
        sum(
            1
            for row in report.source_statuses
            if row.source_status == "current" and row.corroborates_item
        ),
    )
    if report.corroborating_current_source_count != expected_corroborating:
        raise ValueError("corroborating_current_source_count must match source_statuses")
    expected_coverage = _coverage_ratio(
        report.corroborating_current_source_count,
        report.current_source_count,
    )
    if report.corroboration_coverage_ratio != expected_coverage:
        raise ValueError("corroboration_coverage_ratio must match source_statuses")
    if report.max_observed_source_age_seconds != _max_source_age_seconds(
        report.source_statuses,
    ):
        raise ValueError("max_observed_source_age_seconds must match source_statuses")
    if report.source_config_versions != _source_config_versions(report.source_statuses):
        raise ValueError("source_config_versions must match source_statuses")
    if report.reason_codes != _report_reason_codes(report.item_statuses):
        raise ValueError("reason_codes must match item_statuses")
    if report.summary_status != _summary_status(report.reason_codes):
        raise ValueError("summary_status must match reason_codes")
    if report.recommended_next_step != NEXT_STEPS[report.summary_status]:
        raise ValueError("recommended_next_step must match summary_status")
    if report.reason_code_counts != _reason_code_counts_for_items(report.item_statuses):
        raise ValueError("reason_code_counts must summarize item_statuses")
    if report.readiness_gap_count != sum(
        row.readiness_gap_count for row in report.item_statuses
    ):
        raise ValueError("readiness_gap_count must match item_statuses")


def _validate_item_status_consistency(status: TeamSourceQuorumItemStatus) -> None:
    if status.corroborating_current_source_count > status.current_source_count:
        raise ValueError("corroborating_current_source_count cannot exceed current sources")
    expected_coverage = _coverage_ratio(
        status.corroborating_current_source_count,
        status.current_source_count,
    )
    if status.corroboration_coverage_ratio != expected_coverage:
        raise ValueError("corroboration_coverage_ratio must match current sources")
    expected_min_corroboration_ratio = (
        ZERO_DECIMAL
        if CORROBORATION_REASON not in status.reason_codes
        else status.corroboration_coverage_ratio + QUANT
    )
    expected_reason_codes = _item_reason_codes(
        source_count=(
            int(status.current_source_count)
            + int(status.stale_source_count)
            + int(status.missing_source_count)
            + int(status.blocked_source_count)
        ),
        current_source_count=int(status.current_source_count),
        stale_source_count=int(status.stale_source_count),
        missing_source_count=int(status.missing_source_count),
        blocked_source_count=int(status.blocked_source_count),
        current_source_family_count=int(status.current_source_family_count),
        min_source_family_count=status.required_source_family_count,
        min_current_source_count=status.required_current_source_count,
        corroboration_coverage_ratio=status.corroboration_coverage_ratio,
        min_corroboration_coverage_ratio=expected_min_corroboration_ratio,
    )
    if status.summary_status != _summary_status(status.reason_codes):
        raise ValueError("summary_status must match reason_codes")
    if status.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match item source counts")
    if status.readiness_gap_count != _readiness_gap_count(status.reason_codes):
        raise ValueError("readiness_gap_count must match reason_codes")


def _validate_source_shape(source: TeamSourceQuorumSource) -> None:
    populated = sum(
        item is not None
        for item in (source.observed_at, source.missing_reason, source.blocked_reason)
    )
    if populated != 1:
        raise ValueError("source status inputs must contain exactly one status")
    if source.observed_at is None and source.corroborates_item:
        raise ValueError("only observed sources can corroborate an item")


def _validate_source_status_shape(source_status: TeamSourceQuorumSourceStatus) -> None:
    if source_status.source_status in ("current", "stale"):
        if source_status.observed_at is None or source_status.source_age_seconds is None:
            raise ValueError("observed source status requires observed_at and age")
        if source_status.missing_reason is not None or source_status.blocked_reason is not None:
            raise ValueError("observed source status cannot include missing or blocked reasons")
    if source_status.source_status == "missing":
        if (
            source_status.observed_at is not None
            or source_status.source_age_seconds is not None
            or source_status.missing_reason is None
            or source_status.blocked_reason is not None
            or source_status.corroborates_item
        ):
            raise ValueError("missing source status must include only missing_reason")
    if source_status.source_status == "blocked":
        if (
            source_status.observed_at is not None
            or source_status.source_age_seconds is not None
            or source_status.missing_reason is not None
            or source_status.blocked_reason is None
            or source_status.corroborates_item
        ):
            raise ValueError("blocked source status must include only blocked_reason")
    expected_reason_code = (
        PASS_REASON if source_status.source_status == "current" else f"team_source_quorum_{source_status.source_status}_sources_present"
    )
    if source_status.reason_codes != (expected_reason_code,):
        raise ValueError("source status reason_codes must match source_status")


def _coverage_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_DECIMAL:
        return ZERO_DECIMAL
    return _quantize_decimal(numerator / denominator)


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = delta.days * 86_400 + delta.seconds
    if delta.microseconds:
        seconds += 1
    return _count_decimal(seconds)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_reason_codes(
    name: str,
    value: tuple[str, ...],
    *,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{name} must contain at least one value")
    for reason_code in reason_codes:
        _require_canonical_string(name, reason_code)
        if reason_code not in allowed:
            raise ValueError(f"{name} must contain known reason codes")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{name} must be unique")
    return reason_codes


def _require_summary_reason_code(name: str, value: object) -> None:
    _require_canonical_string(name, value)
    if value not in SUMMARY_REASON_CODES:
        raise ValueError(f"{name} must contain known summary reason codes")


def _require_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized <= ZERO_DECIMAL:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO_DECIMAL:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _require_positive_integral_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value <= ZERO_DECIMAL:
        raise ValueError(f"{name} must be positive")
    if value != value.to_integral_value():
        raise ValueError(f"{name} must be an integral Decimal")
    return _quantize_decimal(value)


def _require_coverage_ratio(name: str, value: object) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO_DECIMAL or normalized > ONE_DECIMAL:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize_decimal(value)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _require_optional_canonical_string(name: str, value: object) -> None:
    if value is None:
        return
    _require_canonical_string(name, value)
    _require_redacted_identifier(name, value)


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _require_redacted_identifier(name: str, value: str) -> None:
    lowered = value.lower()
    forbidden_fragments = ("0x", "account", "email", "@", "private", "secret", "token")
    if any(fragment in lowered for fragment in forbidden_fragments):
        raise ValueError(f"{name} must be a redacted identifier")


def _require_item_reason_code_sequence(name: str, value: tuple[str, ...]) -> None:
    expected = tuple(reason_code for reason_code in ITEM_REASON_CODE_SEQUENCE if reason_code in value)
    if value != expected:
        raise ValueError(f"{name} must be sorted deterministically")


def _require_nonnegative_int(name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{name} must be a nonnegative int")
    if value < 0:
        raise ValueError(f"{name} must be a nonnegative int")


def _require_positive_int(name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{name} must be a positive int")
    if value <= 0:
        raise ValueError(f"{name} must be a positive int")


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")
