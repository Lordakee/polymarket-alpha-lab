from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from typing import Any


DEFAULT_RESEARCH_EVENT_CATALYST_SOURCE_RELIABILITY_CONFIG_VERSION = (
    "research-event-catalyst-source-reliability-v0"
)

STATUSES = ("pass", "watch", "block")
ROW_REASON_CODES = (
    "catalyst_recency_block",
    "source_reliability_block",
    "source_contradiction_block",
    "coverage_gap_block",
    "team_capacity_block",
    "catalyst_recency_watch",
    "source_reliability_watch",
    "source_contradiction_watch",
    "coverage_gap_watch",
    "team_capacity_watch",
)
REPORT_REASON_CODES = ROW_REASON_CODES + (
    "event_catalyst_source_reliability_report_pass",
    "event_catalyst_source_reliability_report_watch",
    "event_catalyst_source_reliability_report_block",
    "event_catalyst_source_reliability_report_no_inputs",
)
STATUS_REASON = {
    "pass": "event_catalyst_source_reliability_report_pass",
    "watch": "event_catalyst_source_reliability_report_watch",
    "block": "event_catalyst_source_reliability_report_block",
}
STATUS_RANK = {
    "block": Decimal("0"),
    "watch": Decimal("1"),
    "pass": Decimal("2"),
}

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_RISK_SCORE = Decimal("0.500000")
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
        _piece("raw", "_", "event"),
        _piece("raw", "_", "market"),
        _piece("raw", "_", "source"),
    ),
)
ACTION_LANGUAGE_FRAGMENTS = frozenset(
    (
        _piece("wal", "let"),
        _piece("au", "th"),
        _piece("or", "der"),
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
        _piece("reque", "sts"),
    ),
)


@dataclass(frozen=True)
class ResearchEventCatalystSourceReliabilityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_CATALYST_SOURCE_RELIABILITY_CONFIG_VERSION
    )
    max_pass_catalyst_recency_hours: Decimal = Decimal("24.000000")
    max_watch_catalyst_recency_hours: Decimal = Decimal("72.000000")
    min_pass_source_reliability_score: Decimal = Decimal("0.800000")
    min_watch_source_reliability_score: Decimal = Decimal("0.600000")
    max_pass_contradiction_count: Decimal = Decimal("0")
    max_watch_contradiction_count: Decimal = Decimal("2")
    max_pass_coverage_gap_ratio: Decimal = Decimal("0.100000")
    max_watch_coverage_gap_ratio: Decimal = Decimal("0.300000")
    max_pass_team_capacity_utilization_ratio: Decimal = Decimal("0.800000")
    max_watch_team_capacity_utilization_ratio: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventCatalystSourceReliabilityConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_CATALYST_SOURCE_RELIABILITY_CONFIG_VERSION
        ):
            raise ValueError("config_version is unsupported")
        for field_name in (
            "max_pass_catalyst_recency_hours",
            "max_watch_catalyst_recency_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_source_reliability_score",
            "min_watch_source_reliability_score",
            "max_pass_coverage_gap_ratio",
            "max_watch_coverage_gap_ratio",
            "max_pass_team_capacity_utilization_ratio",
            "max_watch_team_capacity_utilization_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_contradiction_count",
            "max_watch_contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventCatalystSourceReliabilityInput:
    event_domain: str
    source_class: str
    catalyst_observation_count: Decimal
    average_catalyst_recency_hours: Decimal
    source_reliability_score: Decimal
    contradiction_count: Decimal
    coverage_gap_ratio: Decimal
    team_capacity_utilization_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventCatalystSourceReliabilityInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in ("event_domain", "source_class"):
            _require_public_label(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "catalyst_observation_count",
            _normalize_positive_count(
                "catalyst_observation_count",
                self.catalyst_observation_count,
            ),
        )
        object.__setattr__(
            self,
            "average_catalyst_recency_hours",
            _normalize_nonnegative_decimal(
                "average_catalyst_recency_hours",
                self.average_catalyst_recency_hours,
            ),
        )
        object.__setattr__(
            self,
            "source_reliability_score",
            _normalize_probability(
                "source_reliability_score",
                self.source_reliability_score,
            ),
        )
        object.__setattr__(
            self,
            "contradiction_count",
            _normalize_nonnegative_count("contradiction_count", self.contradiction_count),
        )
        for field_name in ("coverage_gap_ratio", "team_capacity_utilization_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventCatalystSourceReliabilityReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventCatalystSourceReliabilityReasonCodeCount does not support "
            "subclassing",
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
class ResearchEventCatalystSourceReliabilityRow:
    event_domain: str
    source_class: str
    catalyst_observation_count: Decimal
    average_catalyst_recency_hours: Decimal
    source_reliability_score: Decimal
    contradiction_count: Decimal
    coverage_gap_ratio: Decimal
    team_capacity_utilization_ratio: Decimal
    reliability_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventCatalystSourceReliabilityRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in ("event_domain", "source_class"):
            _require_public_label(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "catalyst_observation_count",
            _normalize_positive_count(
                "catalyst_observation_count",
                self.catalyst_observation_count,
            ),
        )
        for field_name in ("average_catalyst_recency_hours",):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "contradiction_count",
            _normalize_nonnegative_count("contradiction_count", self.contradiction_count),
        )
        for field_name in (
            "source_reliability_score",
            "coverage_gap_ratio",
            "team_capacity_utilization_ratio",
            "reliability_risk_score",
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
class ResearchEventCatalystSourceReliabilityReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    event_domain_count: Decimal
    source_class_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_catalyst_count: Decimal
    low_reliability_count: Decimal
    contradiction_count: Decimal
    coverage_gap_count: Decimal
    capacity_pressure_count: Decimal
    average_catalyst_recency_hours: Decimal | None
    average_source_reliability_score: Decimal | None
    max_coverage_gap_ratio: Decimal | None
    max_team_capacity_utilization_ratio: Decimal | None
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchEventCatalystSourceReliabilityReasonCodeCount, ...]
    rows: tuple[ResearchEventCatalystSourceReliabilityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEventCatalystSourceReliabilityReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_CATALYST_SOURCE_RELIABILITY_CONFIG_VERSION
        ):
            raise ValueError("config_version is unsupported")
        _require_choice("status", self.status, STATUSES)
        for field_name in (
            "input_count",
            "event_domain_count",
            "source_class_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_catalyst_count",
            "low_reliability_count",
            "contradiction_count",
            "coverage_gap_count",
            "capacity_pressure_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_catalyst_recency_hours",
            "average_source_reliability_score",
            "max_coverage_gap_ratio",
            "max_team_capacity_utilization_ratio",
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
                _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)


def build_research_event_catalyst_source_reliability_report(
    inputs: object,
    *,
    config: ResearchEventCatalystSourceReliabilityConfig,
    generated_at: datetime,
) -> ResearchEventCatalystSourceReliabilityReport:
    if type(config) is not ResearchEventCatalystSourceReliabilityConfig:
        raise ValueError(
            "config must be a ResearchEventCatalystSourceReliabilityConfig",
        )
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
    return ResearchEventCatalystSourceReliabilityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=_count(len(rows)),
        event_domain_count=_count(len({row.event_domain for row in rows})),
        source_class_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        stale_catalyst_count=_dimension_count(rows, "catalyst_recency"),
        low_reliability_count=_dimension_count(rows, "source_reliability"),
        contradiction_count=sum((row.contradiction_count for row in rows), ZERO),
        coverage_gap_count=_dimension_count(rows, "coverage_gap"),
        capacity_pressure_count=_dimension_count(rows, "team_capacity"),
        average_catalyst_recency_hours=_average_decimal(
            row.average_catalyst_recency_hours for row in rows
        ),
        average_source_reliability_score=_average_decimal(
            row.source_reliability_score for row in rows
        ),
        max_coverage_gap_ratio=_max_decimal(row.coverage_gap_ratio for row in rows),
        max_team_capacity_utilization_ratio=_max_decimal(
            row.team_capacity_utilization_ratio for row in rows
        ),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_event_catalyst_source_reliability_report_payload(
    report: ResearchEventCatalystSourceReliabilityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventCatalystSourceReliabilityReport:
        raise ValueError(
            "report must be a ResearchEventCatalystSourceReliabilityReport",
        )
    _validate_report(report)
    payload = _report_public_payload_for_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    validate_research_event_catalyst_source_reliability_public_payload(payload)
    return payload


def validate_research_event_catalyst_source_reliability_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("catalyst source reliability payload", payload)
    _reject_public_numeric_values(payload)
    _require_public_payload_flags(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _normalize_sha256("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _build_row(
    item: ResearchEventCatalystSourceReliabilityInput,
    *,
    config: ResearchEventCatalystSourceReliabilityConfig,
) -> ResearchEventCatalystSourceReliabilityRow:
    reason_codes = _row_reason_codes(item, config=config)
    status = _row_status(reason_codes)
    return ResearchEventCatalystSourceReliabilityRow(
        event_domain=item.event_domain,
        source_class=item.source_class,
        catalyst_observation_count=item.catalyst_observation_count,
        average_catalyst_recency_hours=item.average_catalyst_recency_hours,
        source_reliability_score=item.source_reliability_score,
        contradiction_count=item.contradiction_count,
        coverage_gap_ratio=item.coverage_gap_ratio,
        team_capacity_utilization_ratio=item.team_capacity_utilization_ratio,
        reliability_risk_score=_reliability_risk_score(status),
        status=status,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchEventCatalystSourceReliabilityInput,
    *,
    config: ResearchEventCatalystSourceReliabilityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.average_catalyst_recency_hours > config.max_watch_catalyst_recency_hours:
        reason_codes.append("catalyst_recency_block")
    elif item.average_catalyst_recency_hours > config.max_pass_catalyst_recency_hours:
        reason_codes.append("catalyst_recency_watch")

    if item.source_reliability_score < config.min_watch_source_reliability_score:
        reason_codes.append("source_reliability_block")
    elif item.source_reliability_score < config.min_pass_source_reliability_score:
        reason_codes.append("source_reliability_watch")

    if item.contradiction_count > config.max_watch_contradiction_count:
        reason_codes.append("source_contradiction_block")
    elif item.contradiction_count > config.max_pass_contradiction_count:
        reason_codes.append("source_contradiction_watch")

    if item.coverage_gap_ratio > config.max_watch_coverage_gap_ratio:
        reason_codes.append("coverage_gap_block")
    elif item.coverage_gap_ratio > config.max_pass_coverage_gap_ratio:
        reason_codes.append("coverage_gap_watch")

    if (
        item.team_capacity_utilization_ratio
        > config.max_watch_team_capacity_utilization_ratio
    ):
        reason_codes.append("team_capacity_block")
    elif (
        item.team_capacity_utilization_ratio
        > config.max_pass_team_capacity_utilization_ratio
    ):
        reason_codes.append("team_capacity_watch")
    return _normalize_row_reason_codes("reason_codes", tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if reason_codes:
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchEventCatalystSourceReliabilityRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventCatalystSourceReliabilityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("event_catalyst_source_reliability_report_no_inputs",)
    observed = frozenset(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        [
            *(reason_code for reason_code in ROW_REASON_CODES if reason_code in observed),
            STATUS_REASON[_report_status(rows)],
        ],
    )


def _reason_code_counts(
    rows: tuple[ResearchEventCatalystSourceReliabilityRow, ...],
) -> tuple[ResearchEventCatalystSourceReliabilityReasonCodeCount, ...]:
    return tuple(
        ResearchEventCatalystSourceReliabilityReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
        )
        for reason_code in ROW_REASON_CODES
        if _reason_count(rows, reason_code) > ZERO
    )


def _normalize_inputs(
    value: object,
) -> tuple[ResearchEventCatalystSourceReliabilityInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(
            "inputs must be an iterable of ResearchEventCatalystSourceReliabilityInput",
        )
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "inputs must be an iterable of ResearchEventCatalystSourceReliabilityInput",
        ) from exc
    seen_keys: set[tuple[str, str]] = set()
    for item in rows:
        if type(item) is not ResearchEventCatalystSourceReliabilityInput:
            raise ValueError(
                "inputs must contain ResearchEventCatalystSourceReliabilityInput "
                "values",
            )
        _require_hard_flags("input", item)
        key = (item.event_domain, item.source_class)
        if key in seen_keys:
            raise ValueError(
                "inputs must not contain duplicate event domain source class rows",
            )
        seen_keys.add(key)
    return rows


def _normalize_rows(
    value: object,
) -> tuple[ResearchEventCatalystSourceReliabilityRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchEventCatalystSourceReliabilityRow:
            raise ValueError(
                "rows must contain ResearchEventCatalystSourceReliabilityRow values",
            )
        _require_hard_flags("row", row)
        key = (row.event_domain, row.source_class)
        if key in seen_keys:
            raise ValueError("rows must not contain duplicate event domain source class rows")
        seen_keys.add(key)
    if rows != tuple(sorted(rows, key=_row_rank_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchEventCatalystSourceReliabilityReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchEventCatalystSourceReliabilityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventCatalystSourceReliabilityReasonCodeCount values",
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
            "event_catalyst_source_reliability_report_pass",
            "event_catalyst_source_reliability_report_watch",
            "event_catalyst_source_reliability_report_block",
            "event_catalyst_source_reliability_report_no_inputs",
        )
        if reason_code in seen
    )
    expected = row_codes + status_codes
    if reason_codes != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _validate_config(config: ResearchEventCatalystSourceReliabilityConfig) -> None:
    if config.max_pass_catalyst_recency_hours > config.max_watch_catalyst_recency_hours:
        raise ValueError(
            "max_pass_catalyst_recency_hours must be at most "
            "max_watch_catalyst_recency_hours",
        )
    if (
        config.min_pass_source_reliability_score
        < config.min_watch_source_reliability_score
    ):
        raise ValueError(
            "min_pass_source_reliability_score must be at least "
            "min_watch_source_reliability_score",
        )
    if config.max_pass_contradiction_count > config.max_watch_contradiction_count:
        raise ValueError(
            "max_pass_contradiction_count must be at most "
            "max_watch_contradiction_count",
        )
    if config.max_pass_coverage_gap_ratio > config.max_watch_coverage_gap_ratio:
        raise ValueError(
            "max_pass_coverage_gap_ratio must be at most "
            "max_watch_coverage_gap_ratio",
        )
    if (
        config.max_pass_team_capacity_utilization_ratio
        > config.max_watch_team_capacity_utilization_ratio
    ):
        raise ValueError(
            "max_pass_team_capacity_utilization_ratio must be at most "
            "max_watch_team_capacity_utilization_ratio",
        )


def _validate_row(row: ResearchEventCatalystSourceReliabilityRow) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.reliability_risk_score != _reliability_risk_score(row.status):
        raise ValueError("reliability_risk_score must match status")


def _validate_report(report: ResearchEventCatalystSourceReliabilityReport) -> None:
    rows = report.rows
    expected_values = {
        "status": _report_status(rows),
        "input_count": _count(len(rows)),
        "event_domain_count": _count(len({row.event_domain for row in rows})),
        "source_class_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "stale_catalyst_count": _dimension_count(rows, "catalyst_recency"),
        "low_reliability_count": _dimension_count(rows, "source_reliability"),
        "contradiction_count": sum((row.contradiction_count for row in rows), ZERO),
        "coverage_gap_count": _dimension_count(rows, "coverage_gap"),
        "capacity_pressure_count": _dimension_count(rows, "team_capacity"),
        "average_catalyst_recency_hours": _average_decimal(
            row.average_catalyst_recency_hours for row in rows
        ),
        "average_source_reliability_score": _average_decimal(
            row.source_reliability_score for row in rows
        ),
        "max_coverage_gap_ratio": _max_decimal(row.coverage_gap_ratio for row in rows),
        "max_team_capacity_utilization_ratio": _max_decimal(
            row.team_capacity_utilization_ratio for row in rows
        ),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match report rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _row_rank_key(
    row: ResearchEventCatalystSourceReliabilityRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.status],
        -row.reliability_risk_score,
        row.event_domain,
        row.source_class,
    )


def _status_count(
    rows: tuple[ResearchEventCatalystSourceReliabilityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _dimension_count(
    rows: tuple[ResearchEventCatalystSourceReliabilityRow, ...],
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
    rows: tuple[ResearchEventCatalystSourceReliabilityRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _reliability_risk_score(status: str) -> Decimal:
    return {"pass": ZERO, "watch": WATCH_RISK_SCORE, "block": ONE}[status]


def _average_decimal(values: object) -> Decimal | None:
    items = tuple(values)  # type: ignore[arg-type]
    if not items:
        return None
    return _quantize(sum(items, ZERO) / _count(len(items)))


def _max_decimal(values: object) -> Decimal | None:
    items = tuple(values)  # type: ignore[arg-type]
    if not items:
        return None
    return max(items)


def _count(value: int) -> Decimal:
    return Decimal(value)


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
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
        raise ValueError(f"{field_name} has unsafe public surface language")


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
    report: ResearchEventCatalystSourceReliabilityReport,
) -> dict[str, Any]:
    return {
        "generated_at": _datetime_to_public_string(report.generated_at),
        "config_version": report.config_version,
        "status": report.status,
        "input_count": _count_to_public_string(report.input_count),
        "event_domain_count": _count_to_public_string(report.event_domain_count),
        "source_class_count": _count_to_public_string(report.source_class_count),
        "pass_count": _count_to_public_string(report.pass_count),
        "watch_count": _count_to_public_string(report.watch_count),
        "block_count": _count_to_public_string(report.block_count),
        "stale_catalyst_count": _count_to_public_string(report.stale_catalyst_count),
        "low_reliability_count": _count_to_public_string(report.low_reliability_count),
        "contradiction_count": _count_to_public_string(report.contradiction_count),
        "coverage_gap_count": _count_to_public_string(report.coverage_gap_count),
        "capacity_pressure_count": _count_to_public_string(
            report.capacity_pressure_count,
        ),
        "average_catalyst_recency_hours": _optional_decimal_to_public_string(
            report.average_catalyst_recency_hours,
        ),
        "average_source_reliability_score": _optional_decimal_to_public_string(
            report.average_source_reliability_score,
        ),
        "max_coverage_gap_ratio": _optional_decimal_to_public_string(
            report.max_coverage_gap_ratio,
        ),
        "max_team_capacity_utilization_ratio": _optional_decimal_to_public_string(
            report.max_team_capacity_utilization_ratio,
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


def _row_payload(row: ResearchEventCatalystSourceReliabilityRow) -> dict[str, Any]:
    return {
        "event_domain": row.event_domain,
        "source_class": row.source_class,
        "catalyst_observation_count": _count_to_public_string(
            row.catalyst_observation_count,
        ),
        "average_catalyst_recency_hours": _decimal_to_public_string(
            row.average_catalyst_recency_hours,
        ),
        "source_reliability_score": _decimal_to_public_string(
            row.source_reliability_score,
        ),
        "contradiction_count": _count_to_public_string(row.contradiction_count),
        "coverage_gap_ratio": _decimal_to_public_string(row.coverage_gap_ratio),
        "team_capacity_utilization_ratio": _decimal_to_public_string(
            row.team_capacity_utilization_ratio,
        ),
        "reliability_risk_score": _decimal_to_public_string(
            row.reliability_risk_score,
        ),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _reason_code_count_payload(
    row: ResearchEventCatalystSourceReliabilityReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": row.reason_code,
        "count": _count_to_public_string(row.count),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_derived_validation_digest(
    report: ResearchEventCatalystSourceReliabilityReport,
) -> str:
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
        raise ValueError(f"{label} has unsafe public surface language")


def _has_raw_identifier_fragment(value: str) -> bool:
    return any(fragment in value for fragment in RAW_IDENTIFIER_FRAGMENTS)


def _has_action_language_fragment(value: str) -> bool:
    return any(fragment in value for fragment in ACTION_LANGUAGE_FRAGMENTS)


def _has_external_io_fragment(value: str) -> bool:
    return any(fragment in value for fragment in EXTERNAL_IO_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_EVENT_CATALYST_SOURCE_RELIABILITY_CONFIG_VERSION",
    "STATUSES",
    "ROW_REASON_CODES",
    "REPORT_REASON_CODES",
    "ResearchEventCatalystSourceReliabilityConfig",
    "ResearchEventCatalystSourceReliabilityInput",
    "ResearchEventCatalystSourceReliabilityReasonCodeCount",
    "ResearchEventCatalystSourceReliabilityRow",
    "ResearchEventCatalystSourceReliabilityReport",
    "build_research_event_catalyst_source_reliability_report",
    "research_event_catalyst_source_reliability_report_payload",
    "validate_research_event_catalyst_source_reliability_public_payload",
)
