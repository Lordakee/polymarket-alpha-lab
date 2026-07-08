from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from typing import Any


DEFAULT_RESEARCH_TEAM_CATALYST_COVERAGE_GAP_CONFIG_VERSION = (
    "research-team-catalyst-coverage-gap-v0"
)

STATUSES = ("pass", "watch", "block")
ROW_REASON_CODES = (
    "catalyst_cadence_block",
    "team_capacity_block",
    "expertise_fit_block",
    "evidence_freshness_block",
    "source_class_coverage_block",
    "catalyst_cadence_watch",
    "team_capacity_watch",
    "expertise_fit_watch",
    "evidence_freshness_watch",
    "source_class_coverage_watch",
)
REPORT_REASON_CODES = ROW_REASON_CODES + (
    "catalyst_coverage_gap_report_pass",
    "catalyst_coverage_gap_report_watch",
    "catalyst_coverage_gap_report_block",
    "catalyst_coverage_gap_report_no_inputs",
)
STATUS_REASON = {
    "pass": "catalyst_coverage_gap_report_pass",
    "watch": "catalyst_coverage_gap_report_watch",
    "block": "catalyst_coverage_gap_report_block",
}
STATUS_RANK = {
    "block": Decimal("0"),
    "watch": Decimal("1"),
    "pass": Decimal("2"),
}

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_GAP_SCORE = Decimal("0.500000")
WEEK_DAYS = Decimal("7.000000")
DECIMAL_QUANT = Decimal("0.000001")
COUNT_ONE = Decimal("1")


def _piece(*parts: str) -> str:
    return "".join(parts)


RAW_IDENTIFIER_FRAGMENTS = frozenset(
    (
        _piece("event", "_", "id"),
        _piece("market", "_", "id"),
        _piece("market", "_", "slug"),
        _piece("source", "_", "id"),
        _piece("source", "_", "identifier"),
    ),
)
ACTION_LANGUAGE_FRAGMENTS = frozenset(
    (
        _piece("wal", "let"),
        _piece("au", "th"),
        _piece("ord", "er"),
        _piece("tra", "de"),
        _piece("live", "_", "execution"),
        _piece("reco", "mmend"),
        _piece("sizi", "ng"),
        _piece("position", "_", "size"),
        _piece("sta", "ke"),
        _piece("alloc", "ation"),
    ),
)
EXTERNAL_IO_FRAGMENTS = frozenset(
    (
        _piece("net", "work"),
        _piece("data", "base"),
        _piece("per", "sist"),
        _piece("bro", "ker"),
        _piece("acc", "ount"),
    ),
)


@dataclass(frozen=True)
class ResearchTeamCatalystCoverageGapConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_CATALYST_COVERAGE_GAP_CONFIG_VERSION
    min_pass_catalyst_cadence_per_week: Decimal = Decimal("3.000000")
    min_watch_catalyst_cadence_per_week: Decimal = Decimal("1.000000")
    max_pass_capacity_utilization_ratio: Decimal = Decimal("0.800000")
    max_watch_capacity_utilization_ratio: Decimal = Decimal("1.000000")
    min_pass_expertise_fit_score: Decimal = Decimal("0.750000")
    min_watch_expertise_fit_score: Decimal = Decimal("0.500000")
    max_pass_evidence_age_hours: Decimal = Decimal("24.000000")
    max_watch_evidence_age_hours: Decimal = Decimal("72.000000")
    min_pass_source_class_coverage_ratio: Decimal = Decimal("0.750000")
    min_watch_source_class_coverage_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchTeamCatalystCoverageGapConfig does not support subclassing")

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_TEAM_CATALYST_COVERAGE_GAP_CONFIG_VERSION:
            raise ValueError("config_version is unsupported")
        for field_name in (
            "min_pass_catalyst_cadence_per_week",
            "min_watch_catalyst_cadence_per_week",
            "max_pass_evidence_age_hours",
            "max_watch_evidence_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_capacity_utilization_ratio",
            "max_watch_capacity_utilization_ratio",
            "min_pass_expertise_fit_score",
            "min_watch_expertise_fit_score",
            "min_pass_source_class_coverage_ratio",
            "min_watch_source_class_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamCatalystCoverageGapInput:
    specialist_team: str
    coverage_area: str
    catalyst_class: str
    lookback_days: Decimal
    observed_catalyst_count: Decimal
    available_research_capacity: Decimal
    active_catalyst_load: Decimal
    expertise_fit_score: Decimal
    latest_evidence_age_hours: Decimal
    covered_source_class_count: Decimal
    required_source_class_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchTeamCatalystCoverageGapInput does not support subclassing")

    def __post_init__(self) -> None:
        for field_name in ("specialist_team", "coverage_area", "catalyst_class"):
            _require_public_label(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "lookback_days",
            _normalize_positive_decimal("lookback_days", self.lookback_days),
        )
        for field_name in ("observed_catalyst_count", "covered_source_class_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "required_source_class_count",
            _normalize_positive_count(
                "required_source_class_count",
                self.required_source_class_count,
            ),
        )
        for field_name in ("available_research_capacity", "active_catalyst_load"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "expertise_fit_score",
            _normalize_probability("expertise_fit_score", self.expertise_fit_score),
        )
        object.__setattr__(
            self,
            "latest_evidence_age_hours",
            _normalize_nonnegative_decimal(
                "latest_evidence_age_hours",
                self.latest_evidence_age_hours,
            ),
        )
        if self.covered_source_class_count > self.required_source_class_count:
            raise ValueError(
                "covered_source_class_count must be at most required_source_class_count",
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamCatalystCoverageGapReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchTeamCatalystCoverageGapReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_choice("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamCatalystCoverageGapRow:
    specialist_team: str
    coverage_area: str
    catalyst_class: str
    lookback_days: Decimal
    observed_catalyst_count: Decimal
    catalyst_cadence_per_week: Decimal
    available_research_capacity: Decimal
    active_catalyst_load: Decimal
    capacity_utilization_ratio: Decimal
    expertise_fit_score: Decimal
    latest_evidence_age_hours: Decimal
    covered_source_class_count: Decimal
    required_source_class_count: Decimal
    source_class_coverage_ratio: Decimal
    gap_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchTeamCatalystCoverageGapRow does not support subclassing")

    def __post_init__(self) -> None:
        for field_name in ("specialist_team", "coverage_area", "catalyst_class"):
            _require_public_label(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "lookback_days",
            _normalize_positive_decimal("lookback_days", self.lookback_days),
        )
        for field_name in (
            "observed_catalyst_count",
            "covered_source_class_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "required_source_class_count",
            _normalize_positive_count(
                "required_source_class_count",
                self.required_source_class_count,
            ),
        )
        for field_name in (
            "catalyst_cadence_per_week",
            "available_research_capacity",
            "active_catalyst_load",
            "latest_evidence_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "capacity_utilization_ratio",
            "expertise_fit_score",
            "source_class_coverage_ratio",
            "gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_choice("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchTeamCatalystCoverageGapReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    gap_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    low_catalyst_cadence_count: Decimal
    capacity_gap_count: Decimal
    expertise_gap_count: Decimal
    stale_evidence_count: Decimal
    source_class_gap_count: Decimal
    gap_ratio: Decimal | None
    max_gap_score: Decimal | None
    min_catalyst_cadence_per_week: Decimal | None
    max_capacity_utilization_ratio: Decimal | None
    min_expertise_fit_score: Decimal | None
    max_evidence_age_hours: Decimal | None
    min_source_class_coverage_ratio: Decimal | None
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamCatalystCoverageGapReasonCodeCount, ...]
    rows: tuple[ResearchTeamCatalystCoverageGapRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchTeamCatalystCoverageGapReport does not support subclassing")

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_TEAM_CATALYST_COVERAGE_GAP_CONFIG_VERSION:
            raise ValueError("config_version is unsupported")
        _require_choice("status", self.status, STATUSES)
        for field_name in (
            "input_count",
            "gap_count",
            "pass_count",
            "watch_count",
            "block_count",
            "low_catalyst_cadence_count",
            "capacity_gap_count",
            "expertise_gap_count",
            "stale_evidence_count",
            "source_class_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "gap_ratio",
            _normalize_optional_probability("gap_ratio", self.gap_ratio),
        )
        for field_name in (
            "max_gap_score",
            "min_source_class_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_catalyst_cadence_per_week",
            "max_capacity_utilization_ratio",
            "min_expertise_fit_score",
            "max_evidence_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256("derived_validation_digest", self.derived_validation_digest),
            )
        _validate_report(self)


def build_research_team_catalyst_coverage_gap_report(
    inputs: object,
    *,
    config: ResearchTeamCatalystCoverageGapConfig,
    generated_at: datetime,
) -> ResearchTeamCatalystCoverageGapReport:
    if type(config) is not ResearchTeamCatalystCoverageGapConfig:
        raise ValueError("config must be a ResearchTeamCatalystCoverageGapConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _build_row(item, config=config)
                for item in _normalize_inputs(inputs)
            ),
            key=_row_rank_key,
        ),
    )
    return ResearchTeamCatalystCoverageGapReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=_count(len(rows)),
        gap_count=_status_not_pass_count(rows),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        low_catalyst_cadence_count=_dimension_count(rows, "catalyst_cadence"),
        capacity_gap_count=_dimension_count(rows, "team_capacity"),
        expertise_gap_count=_dimension_count(rows, "expertise_fit"),
        stale_evidence_count=_dimension_count(rows, "evidence_freshness"),
        source_class_gap_count=_dimension_count(rows, "source_class_coverage"),
        gap_ratio=_optional_ratio(_status_not_pass_count(rows), _count(len(rows))),
        max_gap_score=_max_decimal(row.gap_score for row in rows),
        min_catalyst_cadence_per_week=_min_decimal(
            row.catalyst_cadence_per_week for row in rows
        ),
        max_capacity_utilization_ratio=_max_decimal(
            row.capacity_utilization_ratio for row in rows
        ),
        min_expertise_fit_score=_min_decimal(row.expertise_fit_score for row in rows),
        max_evidence_age_hours=_max_decimal(row.latest_evidence_age_hours for row in rows),
        min_source_class_coverage_ratio=_min_decimal(
            row.source_class_coverage_ratio for row in rows
        ),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_team_catalyst_coverage_gap_report_payload(
    report: ResearchTeamCatalystCoverageGapReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamCatalystCoverageGapReport:
        raise ValueError("report must be a ResearchTeamCatalystCoverageGapReport")
    _validate_report(report)
    payload = _report_public_payload_for_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    validate_research_team_catalyst_coverage_gap_public_payload(payload)
    return payload


def validate_research_team_catalyst_coverage_gap_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("catalyst coverage gap payload", payload)
    _reject_public_numeric_values(payload)
    _require_public_payload_flags(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _normalize_sha256("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _build_row(
    item: ResearchTeamCatalystCoverageGapInput,
    *,
    config: ResearchTeamCatalystCoverageGapConfig,
) -> ResearchTeamCatalystCoverageGapRow:
    catalyst_cadence_per_week = _catalyst_cadence_per_week(item)
    capacity_utilization_ratio = _capacity_utilization_ratio(item)
    source_class_coverage_ratio = _source_class_coverage_ratio(item)
    reason_codes = _row_reason_codes(
        item,
        catalyst_cadence_per_week=catalyst_cadence_per_week,
        capacity_utilization_ratio=capacity_utilization_ratio,
        source_class_coverage_ratio=source_class_coverage_ratio,
        config=config,
    )
    status = _row_status(reason_codes)
    return ResearchTeamCatalystCoverageGapRow(
        specialist_team=item.specialist_team,
        coverage_area=item.coverage_area,
        catalyst_class=item.catalyst_class,
        lookback_days=item.lookback_days,
        observed_catalyst_count=item.observed_catalyst_count,
        catalyst_cadence_per_week=catalyst_cadence_per_week,
        available_research_capacity=item.available_research_capacity,
        active_catalyst_load=item.active_catalyst_load,
        capacity_utilization_ratio=capacity_utilization_ratio,
        expertise_fit_score=item.expertise_fit_score,
        latest_evidence_age_hours=item.latest_evidence_age_hours,
        covered_source_class_count=item.covered_source_class_count,
        required_source_class_count=item.required_source_class_count,
        source_class_coverage_ratio=source_class_coverage_ratio,
        gap_score=_gap_score(status),
        status=status,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchTeamCatalystCoverageGapInput,
    *,
    catalyst_cadence_per_week: Decimal,
    capacity_utilization_ratio: Decimal,
    source_class_coverage_ratio: Decimal,
    config: ResearchTeamCatalystCoverageGapConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if catalyst_cadence_per_week < config.min_watch_catalyst_cadence_per_week:
        reason_codes.append("catalyst_cadence_block")
    elif catalyst_cadence_per_week < config.min_pass_catalyst_cadence_per_week:
        reason_codes.append("catalyst_cadence_watch")

    if _is_capacity_block(item, config=config):
        reason_codes.append("team_capacity_block")
    elif capacity_utilization_ratio > config.max_pass_capacity_utilization_ratio:
        reason_codes.append("team_capacity_watch")

    if item.expertise_fit_score < config.min_watch_expertise_fit_score:
        reason_codes.append("expertise_fit_block")
    elif item.expertise_fit_score < config.min_pass_expertise_fit_score:
        reason_codes.append("expertise_fit_watch")

    if item.latest_evidence_age_hours > config.max_watch_evidence_age_hours:
        reason_codes.append("evidence_freshness_block")
    elif item.latest_evidence_age_hours > config.max_pass_evidence_age_hours:
        reason_codes.append("evidence_freshness_watch")

    if source_class_coverage_ratio < config.min_watch_source_class_coverage_ratio:
        reason_codes.append("source_class_coverage_block")
    elif source_class_coverage_ratio < config.min_pass_source_class_coverage_ratio:
        reason_codes.append("source_class_coverage_watch")
    return _normalize_row_reason_codes("reason_codes", tuple(reason_codes))


def _is_capacity_block(
    item: ResearchTeamCatalystCoverageGapInput,
    *,
    config: ResearchTeamCatalystCoverageGapConfig,
) -> bool:
    if item.available_research_capacity == ZERO:
        return item.active_catalyst_load > ZERO
    return _raw_ratio(item.active_catalyst_load, item.available_research_capacity) > (
        config.max_watch_capacity_utilization_ratio
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if reason_codes:
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchTeamCatalystCoverageGapRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamCatalystCoverageGapRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("catalyst_coverage_gap_report_no_inputs",)
    observed = frozenset(reason_code for row in rows for reason_code in row.reason_codes)
    report_status = _report_status(rows)
    return tuple(
        [
            *(reason_code for reason_code in ROW_REASON_CODES if reason_code in observed),
            STATUS_REASON[report_status],
        ],
    )


def _reason_code_counts(
    rows: tuple[ResearchTeamCatalystCoverageGapRow, ...],
) -> tuple[ResearchTeamCatalystCoverageGapReasonCodeCount, ...]:
    return tuple(
        ResearchTeamCatalystCoverageGapReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
        )
        for reason_code in ROW_REASON_CODES
        if _reason_count(rows, reason_code) > ZERO
    )


def _normalize_inputs(value: object) -> tuple[ResearchTeamCatalystCoverageGapInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("inputs must be an iterable of ResearchTeamCatalystCoverageGapInput")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "inputs must be an iterable of ResearchTeamCatalystCoverageGapInput",
        ) from exc
    seen_keys: set[tuple[str, str, str]] = set()
    for item in rows:
        if type(item) is not ResearchTeamCatalystCoverageGapInput:
            raise ValueError(
                "inputs must contain ResearchTeamCatalystCoverageGapInput values",
            )
        _require_hard_flags("input", item)
        key = (item.specialist_team, item.coverage_area, item.catalyst_class)
        if key in seen_keys:
            raise ValueError("inputs must not contain duplicate team catalyst coverage rows")
        seen_keys.add(key)
    return rows


def _normalize_rows(value: object) -> tuple[ResearchTeamCatalystCoverageGapRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not ResearchTeamCatalystCoverageGapRow:
            raise ValueError("rows must contain ResearchTeamCatalystCoverageGapRow values")
        _require_hard_flags("row", row)
        key = (row.specialist_team, row.coverage_area, row.catalyst_class)
        if key in seen_keys:
            raise ValueError("rows must not contain duplicate team catalyst coverage rows")
        seen_keys.add(key)
    if rows != tuple(sorted(rows, key=_row_rank_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchTeamCatalystCoverageGapReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamCatalystCoverageGapReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamCatalystCoverageGapReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(row.reason_code)
    expected = tuple(
        row for reason_code in ROW_REASON_CODES for row in rows if row.reason_code == reason_code
    )
    if rows != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return rows


def _normalize_row_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_choice(field_name, reason_code, ROW_REASON_CODES)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    expected = tuple(reason_code for reason_code in ROW_REASON_CODES if reason_code in seen)
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _normalize_report_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_choice(field_name, reason_code, REPORT_REASON_CODES)
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    row_codes = tuple(reason_code for reason_code in ROW_REASON_CODES if reason_code in seen)
    status_codes = tuple(
        reason_code
        for reason_code in (
            "catalyst_coverage_gap_report_pass",
            "catalyst_coverage_gap_report_watch",
            "catalyst_coverage_gap_report_block",
            "catalyst_coverage_gap_report_no_inputs",
        )
        if reason_code in seen
    )
    expected = row_codes + status_codes
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _validate_config(config: ResearchTeamCatalystCoverageGapConfig) -> None:
    if config.min_pass_catalyst_cadence_per_week < config.min_watch_catalyst_cadence_per_week:
        raise ValueError(
            "min_pass_catalyst_cadence_per_week must be at least "
            "min_watch_catalyst_cadence_per_week",
        )
    if config.max_pass_capacity_utilization_ratio > config.max_watch_capacity_utilization_ratio:
        raise ValueError(
            "max_pass_capacity_utilization_ratio must be at most "
            "max_watch_capacity_utilization_ratio",
        )
    if config.min_pass_expertise_fit_score < config.min_watch_expertise_fit_score:
        raise ValueError(
            "min_pass_expertise_fit_score must be at least min_watch_expertise_fit_score",
        )
    if config.max_pass_evidence_age_hours > config.max_watch_evidence_age_hours:
        raise ValueError(
            "max_pass_evidence_age_hours must be at most max_watch_evidence_age_hours",
        )
    if (
        config.min_pass_source_class_coverage_ratio
        < config.min_watch_source_class_coverage_ratio
    ):
        raise ValueError(
            "min_pass_source_class_coverage_ratio must be at least "
            "min_watch_source_class_coverage_ratio",
        )


def _validate_row(row: ResearchTeamCatalystCoverageGapRow) -> None:
    if row.covered_source_class_count > row.required_source_class_count:
        raise ValueError(
            "covered_source_class_count must be at most required_source_class_count",
        )
    if row.catalyst_cadence_per_week != _quantize(
        row.observed_catalyst_count / row.lookback_days * WEEK_DAYS,
    ):
        raise ValueError("catalyst_cadence_per_week must match catalyst cadence")
    expected_capacity = (
        ZERO
        if row.available_research_capacity == ZERO and row.active_catalyst_load == ZERO
        else ONE
        if row.available_research_capacity == ZERO
        else min(ONE, _raw_ratio(row.active_catalyst_load, row.available_research_capacity))
    )
    if row.capacity_utilization_ratio != expected_capacity:
        raise ValueError("capacity_utilization_ratio must match team capacity")
    if row.source_class_coverage_ratio != _raw_ratio(
        row.covered_source_class_count,
        row.required_source_class_count,
    ):
        raise ValueError("source_class_coverage_ratio must match class counts")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.gap_score != _gap_score(row.status):
        raise ValueError("gap_score must match status")


def _validate_report(report: ResearchTeamCatalystCoverageGapReport) -> None:
    rows = report.rows
    expected_values = {
        "status": _report_status(rows),
        "input_count": _count(len(rows)),
        "gap_count": _status_not_pass_count(rows),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "low_catalyst_cadence_count": _dimension_count(rows, "catalyst_cadence"),
        "capacity_gap_count": _dimension_count(rows, "team_capacity"),
        "expertise_gap_count": _dimension_count(rows, "expertise_fit"),
        "stale_evidence_count": _dimension_count(rows, "evidence_freshness"),
        "source_class_gap_count": _dimension_count(rows, "source_class_coverage"),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
    }
    expected_values["gap_ratio"] = _optional_ratio(
        expected_values["gap_count"],
        expected_values["input_count"],
    )
    expected_values["max_gap_score"] = _max_decimal(row.gap_score for row in rows)
    expected_values["min_catalyst_cadence_per_week"] = _min_decimal(
        row.catalyst_cadence_per_week for row in rows
    )
    expected_values["max_capacity_utilization_ratio"] = _max_decimal(
        row.capacity_utilization_ratio for row in rows
    )
    expected_values["min_expertise_fit_score"] = _min_decimal(
        row.expertise_fit_score for row in rows
    )
    expected_values["max_evidence_age_hours"] = _max_decimal(
        row.latest_evidence_age_hours for row in rows
    )
    expected_values["min_source_class_coverage_ratio"] = _min_decimal(
        row.source_class_coverage_ratio for row in rows
    )
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match report rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _catalyst_cadence_per_week(item: ResearchTeamCatalystCoverageGapInput) -> Decimal:
    return _quantize(item.observed_catalyst_count / item.lookback_days * WEEK_DAYS)


def _capacity_utilization_ratio(item: ResearchTeamCatalystCoverageGapInput) -> Decimal:
    if item.available_research_capacity == ZERO:
        if item.active_catalyst_load == ZERO:
            return ZERO
        return ONE
    return min(ONE, _raw_ratio(item.active_catalyst_load, item.available_research_capacity))


def _source_class_coverage_ratio(item: ResearchTeamCatalystCoverageGapInput) -> Decimal:
    return _raw_ratio(item.covered_source_class_count, item.required_source_class_count)


def _raw_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        raise ValueError("ratio denominator must be positive")
    return _quantize(numerator / denominator)


def _optional_ratio(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator == ZERO:
        return None
    return _raw_ratio(numerator, denominator)


def _row_rank_key(
    row: ResearchTeamCatalystCoverageGapRow,
) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.status],
        -row.gap_score,
        row.specialist_team,
        row.coverage_area,
        row.catalyst_class,
    )


def _status_count(
    rows: tuple[ResearchTeamCatalystCoverageGapRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _status_not_pass_count(rows: tuple[ResearchTeamCatalystCoverageGapRow, ...]) -> Decimal:
    return _count(sum(1 for row in rows if row.status != "pass"))


def _dimension_count(
    rows: tuple[ResearchTeamCatalystCoverageGapRow, ...],
    reason_prefix: str,
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if any(reason_code.startswith(reason_prefix) for reason_code in row.reason_codes)
        ),
    )


def _reason_count(
    rows: tuple[ResearchTeamCatalystCoverageGapRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _gap_score(status: str) -> Decimal:
    return {"pass": ZERO, "watch": WATCH_GAP_SCORE, "block": ONE}[status]


def _max_decimal(values: object) -> Decimal | None:
    items = tuple(values)  # type: ignore[arg-type]
    if not items:
        return None
    return max(items)


def _min_decimal(values: object) -> Decimal | None:
    items = tuple(values)  # type: ignore[arg-type]
    if not items:
        return None
    return min(items)


def _count(value: int) -> Decimal:
    return Decimal(value)


def _normalize_optional_probability(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability(field_name, value)


def _normalize_optional_nonnegative_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized.quantize(COUNT_ONE)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = _quantize(value)
    if quantized != value:
        raise ValueError(f"{field_name} must not exceed six decimal digits")
    return quantized


def _quantize(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 64
        return value.quantize(DECIMAL_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_label(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    assert type(value) is str
    lowered = value.casefold()
    if _has_raw_identifier_fragment(lowered):
        raise ValueError(f"{field_name} has raw identifier language")
    if _has_action_language_fragment(lowered):
        raise ValueError(f"{field_name} has action language")
    if _has_external_io_fragment(lowered):
        raise ValueError(f"{field_name} has unsafe external surface language")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_choice(field_name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str or value not in choices:
        raise ValueError(f"{field_name} must be one of {choices}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _report_public_payload_for_digest(
    report: ResearchTeamCatalystCoverageGapReport,
) -> dict[str, Any]:
    return {
        "generated_at": _datetime_to_public_string(report.generated_at),
        "config_version": report.config_version,
        "status": report.status,
        "input_count": _count_to_public_string(report.input_count),
        "gap_count": _count_to_public_string(report.gap_count),
        "pass_count": _count_to_public_string(report.pass_count),
        "watch_count": _count_to_public_string(report.watch_count),
        "block_count": _count_to_public_string(report.block_count),
        "low_catalyst_cadence_count": _count_to_public_string(
            report.low_catalyst_cadence_count,
        ),
        "capacity_gap_count": _count_to_public_string(report.capacity_gap_count),
        "expertise_gap_count": _count_to_public_string(report.expertise_gap_count),
        "stale_evidence_count": _count_to_public_string(report.stale_evidence_count),
        "source_class_gap_count": _count_to_public_string(report.source_class_gap_count),
        "gap_ratio": _optional_decimal_to_public_string(report.gap_ratio),
        "max_gap_score": _optional_decimal_to_public_string(report.max_gap_score),
        "min_catalyst_cadence_per_week": _optional_decimal_to_public_string(
            report.min_catalyst_cadence_per_week,
        ),
        "max_capacity_utilization_ratio": _optional_decimal_to_public_string(
            report.max_capacity_utilization_ratio,
        ),
        "min_expertise_fit_score": _optional_decimal_to_public_string(
            report.min_expertise_fit_score,
        ),
        "max_evidence_age_hours": _optional_decimal_to_public_string(
            report.max_evidence_age_hours,
        ),
        "min_source_class_coverage_ratio": _optional_decimal_to_public_string(
            report.min_source_class_coverage_ratio,
        ),
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            _reason_code_count_payload(row) for row in report.reason_code_counts
        ],
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_payload(row: ResearchTeamCatalystCoverageGapRow) -> dict[str, Any]:
    return {
        "specialist_team": row.specialist_team,
        "coverage_area": row.coverage_area,
        "catalyst_class": row.catalyst_class,
        "lookback_days": _decimal_to_public_string(row.lookback_days),
        "observed_catalyst_count": _count_to_public_string(row.observed_catalyst_count),
        "catalyst_cadence_per_week": _decimal_to_public_string(
            row.catalyst_cadence_per_week,
        ),
        "available_research_capacity": _decimal_to_public_string(
            row.available_research_capacity,
        ),
        "active_catalyst_load": _decimal_to_public_string(row.active_catalyst_load),
        "capacity_utilization_ratio": _decimal_to_public_string(
            row.capacity_utilization_ratio,
        ),
        "expertise_fit_score": _decimal_to_public_string(row.expertise_fit_score),
        "latest_evidence_age_hours": _decimal_to_public_string(
            row.latest_evidence_age_hours,
        ),
        "covered_source_class_count": _count_to_public_string(
            row.covered_source_class_count,
        ),
        "required_source_class_count": _count_to_public_string(
            row.required_source_class_count,
        ),
        "source_class_coverage_ratio": _decimal_to_public_string(
            row.source_class_coverage_ratio,
        ),
        "gap_score": _decimal_to_public_string(row.gap_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _reason_code_count_payload(
    row: ResearchTeamCatalystCoverageGapReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": row.reason_code,
        "count": _count_to_public_string(row.count),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_derived_validation_digest(report: ResearchTeamCatalystCoverageGapReport) -> str:
    return _public_payload_derived_validation_digest(_report_public_payload_for_digest(report))


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    payload_for_digest = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    return hashlib.sha256(
        json.dumps(
            payload_for_digest,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()


def _datetime_to_public_string(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def _optional_decimal_to_public_string(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return _decimal_to_public_string(value)


def _decimal_to_public_string(value: Decimal) -> str:
    return format(value, "f")


def _count_to_public_string(value: Decimal) -> str:
    return str(value.quantize(COUNT_ONE))


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    if field_name not in payload:
        raise ValueError(f"{field_name} is required")
    value = payload[field_name]
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    lowered = value.lower()
    if lowered != value or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _reject_public_numeric_values(value: object) -> None:
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, (int, float, Decimal)):
        raise ValueError("public payload numeric values must be Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is str:
        _reject_unsafe_public_string(label, value)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_string(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _reject_unsafe_public_string(label: str, value: str) -> None:
    lowered = value.casefold()
    if _has_raw_identifier_fragment(lowered):
        raise ValueError(f"{label} has raw identifier language")
    if _has_action_language_fragment(lowered):
        raise ValueError(f"{label} has action language")
    if _has_external_io_fragment(lowered):
        raise ValueError(f"{label} has unsafe external surface language")


def _has_raw_identifier_fragment(value: str) -> bool:
    return any(fragment in value for fragment in RAW_IDENTIFIER_FRAGMENTS)


def _has_action_language_fragment(value: str) -> bool:
    return any(fragment in value for fragment in ACTION_LANGUAGE_FRAGMENTS)


def _has_external_io_fragment(value: str) -> bool:
    return any(fragment in value for fragment in EXTERNAL_IO_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_TEAM_CATALYST_COVERAGE_GAP_CONFIG_VERSION",
    "STATUSES",
    "ROW_REASON_CODES",
    "REPORT_REASON_CODES",
    "ResearchTeamCatalystCoverageGapConfig",
    "ResearchTeamCatalystCoverageGapInput",
    "ResearchTeamCatalystCoverageGapReasonCodeCount",
    "ResearchTeamCatalystCoverageGapRow",
    "ResearchTeamCatalystCoverageGapReport",
    "build_research_team_catalyst_coverage_gap_report",
    "research_team_catalyst_coverage_gap_report_payload",
    "validate_research_team_catalyst_coverage_gap_public_payload",
)
