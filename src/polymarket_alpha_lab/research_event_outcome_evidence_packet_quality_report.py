"""Pure report-only event outcome evidence packet quality reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_CONFIG_VERSION = "research-event-outcome-evidence-packet-quality-report-v0"

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "block")
STATUS_ORDER = {"block": 0, "watch": 1, "pass": 2}

EMPTY_REASON = "evidence_packet_quality_empty"
PASS_REASON = "evidence_packet_quality_pass"
WATCH_REASON = "evidence_packet_quality_watch"
BLOCK_REASON = "evidence_packet_quality_block"
OFFICIAL_FRESHNESS_WATCH_REASON = "official_evidence_freshness_watch"
OFFICIAL_FRESHNESS_BLOCK_REASON = "official_evidence_freshness_block"
OFFICIAL_SOURCE_WATCH_REASON = "official_source_quorum_watch"
OFFICIAL_SOURCE_BLOCK_REASON = "official_source_quorum_block"
INDEPENDENT_SOURCE_WATCH_REASON = "independent_source_quorum_watch"
INDEPENDENT_SOURCE_BLOCK_REASON = "independent_source_quorum_block"
CONTRADICTION_WATCH_REASON = "contradiction_pressure_watch"
CONTRADICTION_BLOCK_REASON = "contradiction_pressure_block"
RULE_COVERAGE_WATCH_REASON = "resolution_rule_coverage_watch"
RULE_COVERAGE_BLOCK_REASON = "resolution_rule_coverage_block"

REASON_CODE_PRIORITY = (
    EMPTY_REASON,
    OFFICIAL_FRESHNESS_BLOCK_REASON,
    OFFICIAL_SOURCE_BLOCK_REASON,
    INDEPENDENT_SOURCE_BLOCK_REASON,
    CONTRADICTION_BLOCK_REASON,
    RULE_COVERAGE_BLOCK_REASON,
    BLOCK_REASON,
    OFFICIAL_FRESHNESS_WATCH_REASON,
    OFFICIAL_SOURCE_WATCH_REASON,
    INDEPENDENT_SOURCE_WATCH_REASON,
    CONTRADICTION_WATCH_REASON,
    RULE_COVERAGE_WATCH_REASON,
    WATCH_REASON,
    PASS_REASON,
)
REASON_CODES = frozenset(REASON_CODE_PRIORITY)
BLOCK_REASONS = frozenset(
    (
        EMPTY_REASON,
        OFFICIAL_FRESHNESS_BLOCK_REASON,
        OFFICIAL_SOURCE_BLOCK_REASON,
        INDEPENDENT_SOURCE_BLOCK_REASON,
        CONTRADICTION_BLOCK_REASON,
        RULE_COVERAGE_BLOCK_REASON,
        BLOCK_REASON,
    ),
)
WATCH_REASONS = frozenset(
    (
        OFFICIAL_FRESHNESS_WATCH_REASON,
        OFFICIAL_SOURCE_WATCH_REASON,
        INDEPENDENT_SOURCE_WATCH_REASON,
        CONTRADICTION_WATCH_REASON,
        RULE_COVERAGE_WATCH_REASON,
        WATCH_REASON,
    ),
)

PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market_id",
    "market-id",
    "market_slug",
    "market-slug",
    "raw_id",
    "raw-",
    "raw_",
    "slug",
    "question",
    "source_url",
    "source-url",
    "source_text",
    "source-text",
    "source_ref",
    "source-ref",
    "://",
    "http://",
    "https://",
    "www.",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "trading",
    "buy",
    "sell",
    "position",
    "sizing",
    "recommendation",
    "network",
    "database",
    "live",
)


@dataclass(frozen=True)
class ResearchEventOutcomeEvidencePacketQualityReportConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    max_pass_official_evidence_age_seconds: Decimal = Decimal("3600.000000")
    max_watch_official_evidence_age_seconds: Decimal = Decimal("14400.000000")
    min_pass_official_source_count: Decimal = Decimal("2")
    min_watch_official_source_count: Decimal = Decimal("1")
    min_pass_independent_source_count: Decimal = Decimal("1")
    min_watch_independent_source_count: Decimal = Decimal("1")
    watch_contradiction_pressure: Decimal = Decimal("0.150000")
    block_contradiction_pressure: Decimal = Decimal("0.600000")
    min_pass_resolution_rule_coverage_ratio: Decimal = Decimal("1.000000")
    min_watch_resolution_rule_coverage_ratio: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventOutcomeEvidencePacketQualityReportConfig:
            raise TypeError(
                "ResearchEventOutcomeEvidencePacketQualityReportConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventOutcomeEvidencePacketQualityReportConfig:
            raise ValueError(
                "config must be a ResearchEventOutcomeEvidencePacketQualityReportConfig",
            )
        _require_public_label("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        for field_name in (
            "max_pass_official_evidence_age_seconds",
            "max_watch_official_evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_official_source_count",
            "min_watch_official_source_count",
            "min_pass_independent_source_count",
            "min_watch_independent_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_contradiction_pressure",
            "block_contradiction_pressure",
            "min_pass_resolution_rule_coverage_ratio",
            "min_watch_resolution_rule_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventOutcomeEvidencePacketQualityReportInput:
    evidence_packet_label: str
    latest_official_evidence_at: datetime
    official_source_count: Decimal
    independent_source_count: Decimal
    contradiction_pressure: Decimal
    required_resolution_rule_count: Decimal
    covered_resolution_rule_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventOutcomeEvidencePacketQualityReportInput:
            raise TypeError(
                "ResearchEventOutcomeEvidencePacketQualityReportInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventOutcomeEvidencePacketQualityReportInput:
            raise ValueError(
                "input must be a ResearchEventOutcomeEvidencePacketQualityReportInput",
            )
        _require_private_label("evidence_packet_label", self.evidence_packet_label)
        object.__setattr__(
            self,
            "latest_official_evidence_at",
            _as_utc("latest_official_evidence_at", self.latest_official_evidence_at),
        )
        for field_name in (
            "official_source_count",
            "independent_source_count",
            "required_resolution_rule_count",
            "covered_resolution_rule_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "contradiction_pressure",
            _normalize_probability(
                "contradiction_pressure",
                self.contradiction_pressure,
            ),
        )
        if self.covered_resolution_rule_count > self.required_resolution_rule_count:
            raise ValueError(
                "covered_resolution_rule_count must not exceed "
                "required_resolution_rule_count",
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventOutcomeEvidencePacketQualityReportRow:
    packet_public_label: str
    official_evidence_age_seconds: Decimal
    official_freshness_pressure: Decimal
    official_source_count: Decimal
    independent_source_count: Decimal
    source_quorum_score: Decimal
    contradiction_pressure: Decimal
    required_resolution_rule_count: Decimal
    covered_resolution_rule_count: Decimal
    resolution_rule_coverage_ratio: Decimal
    quality_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventOutcomeEvidencePacketQualityReportRow:
            raise TypeError(
                "ResearchEventOutcomeEvidencePacketQualityReportRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventOutcomeEvidencePacketQualityReportRow:
            raise ValueError(
                "row must be a ResearchEventOutcomeEvidencePacketQualityReportRow",
            )
        _require_public_label("packet_public_label", self.packet_public_label)
        object.__setattr__(
            self,
            "official_evidence_age_seconds",
            _normalize_nonnegative_decimal(
                "official_evidence_age_seconds",
                self.official_evidence_age_seconds,
            ),
        )
        for field_name in (
            "official_freshness_pressure",
            "source_quorum_score",
            "contradiction_pressure",
            "resolution_rule_coverage_ratio",
            "quality_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_source_count",
            "independent_source_count",
            "required_resolution_rule_count",
            "covered_resolution_rule_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchEventOutcomeEvidencePacketQualityReportReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventOutcomeEvidencePacketQualityReportReasonCodeCount:
            raise ValueError(
                "reason code count must be a "
                "ResearchEventOutcomeEvidencePacketQualityReportReasonCodeCount",
            )
        _require_member("reason_code", self.reason_code, REASON_CODE_PRIORITY)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchEventOutcomeEvidencePacketQualityReport:
    generated_at: datetime
    config_version: str
    packet_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_official_evidence_age_seconds: Decimal
    min_source_quorum_score: Decimal
    max_contradiction_pressure: Decimal
    min_resolution_rule_coverage_ratio: Decimal
    average_quality_pressure_score: Decimal
    status: str
    rows: tuple[ResearchEventOutcomeEvidencePacketQualityReportRow, ...]
    reason_code_counts: tuple[
        ResearchEventOutcomeEvidencePacketQualityReportReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventOutcomeEvidencePacketQualityReport:
            raise TypeError(
                "ResearchEventOutcomeEvidencePacketQualityReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventOutcomeEvidencePacketQualityReport:
            raise ValueError(
                "report must be a ResearchEventOutcomeEvidencePacketQualityReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        for field_name in ("packet_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_official_evidence_age_seconds",
            _normalize_nonnegative_decimal(
                "max_official_evidence_age_seconds",
                self.max_official_evidence_age_seconds,
            ),
        )
        for field_name in (
            "min_source_quorum_score",
            "max_contradiction_pressure",
            "min_resolution_rule_coverage_ratio",
            "average_quality_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        _set_or_validate_public_digest(self)
        _reject_unsafe_public_payload("report", _payload_value(self))

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_outcome_evidence_packet_quality_report_public_payload(self)


def build_research_event_outcome_evidence_packet_quality_report(
    inputs: Iterable[ResearchEventOutcomeEvidencePacketQualityReportInput],
    *,
    generated_at: datetime,
    config: ResearchEventOutcomeEvidencePacketQualityReportConfig,
) -> ResearchEventOutcomeEvidencePacketQualityReport:
    if type(config) is not ResearchEventOutcomeEvidencePacketQualityReportConfig:
        raise ValueError(
            "config must be a ResearchEventOutcomeEvidencePacketQualityReportConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs, generated_at=generated_at_utc)
    public_labels = {
        item.evidence_packet_label: f"evidence-packet-{index:03d}"
        for index, item in enumerate(
            sorted(normalized_inputs, key=lambda item: item.evidence_packet_label),
            start=1,
        )
    }
    rows = tuple(
        sorted(
            (
                _row_for_input(
                    item,
                    packet_public_label=public_labels[item.evidence_packet_label],
                    generated_at=generated_at_utc,
                    config=config,
                )
                for item in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    return ResearchEventOutcomeEvidencePacketQualityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        packet_count=_count(len(rows)),
        pass_count=_count(_status_count(rows, "pass")),
        watch_count=_count(_status_count(rows, "watch")),
        block_count=_count(_status_count(rows, "block")),
        max_official_evidence_age_seconds=_max_decimal(
            (row.official_evidence_age_seconds for row in rows),
            default=ZERO,
        ),
        min_source_quorum_score=_min_decimal(
            (row.source_quorum_score for row in rows),
            default=ONE,
        ),
        max_contradiction_pressure=_max_decimal(
            (row.contradiction_pressure for row in rows),
            default=ZERO,
        ),
        min_resolution_rule_coverage_ratio=_min_decimal(
            (row.resolution_rule_coverage_ratio for row in rows),
            default=ONE,
        ),
        average_quality_pressure_score=(
            _average_decimal(row.quality_pressure_score for row in rows)
            if rows
            else ONE
        ),
        status=_status_from_reason_codes(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_event_outcome_evidence_packet_quality_report_public_payload(
    value: ResearchEventOutcomeEvidencePacketQualityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchEventOutcomeEvidencePacketQualityReport:
        _validate_report(value)
        _validate_public_digest(value)
        payload = _payload_value(value)
    elif type(value) is dict:
        payload = value
    else:
        raise ValueError(
            "value must be a ResearchEventOutcomeEvidencePacketQualityReport or dict",
        )
    validate_research_event_outcome_evidence_packet_quality_report_public_payload(payload)
    return dict(payload)


def validate_research_event_outcome_evidence_packet_quality_report_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_unsafe_public_payload("public payload", payload)
    _reject_public_numeric_scalars(payload)
    _validate_public_statuses(payload)
    _validate_payload_public_digest(payload)


def research_event_outcome_evidence_packet_quality_report_public_digest(
    value: ResearchEventOutcomeEvidencePacketQualityReport | dict[str, Any],
) -> str:
    payload = research_event_outcome_evidence_packet_quality_report_public_payload(value)
    public_digest = payload.get("public_digest")
    _require_sha256_digest("public_digest", public_digest)
    return public_digest


def _row_for_input(
    item: ResearchEventOutcomeEvidencePacketQualityReportInput,
    *,
    packet_public_label: str,
    generated_at: datetime,
    config: ResearchEventOutcomeEvidencePacketQualityReportConfig,
) -> ResearchEventOutcomeEvidencePacketQualityReportRow:
    official_evidence_age_seconds = _elapsed_seconds(
        item.latest_official_evidence_at,
        generated_at,
    )
    official_freshness_pressure = _ratio(
        official_evidence_age_seconds,
        config.max_watch_official_evidence_age_seconds,
    )
    source_quorum_score = _source_quorum_score(item, config)
    resolution_rule_coverage_ratio = _resolution_rule_coverage_ratio(item)
    quality_pressure_score = _quality_pressure_score(
        official_freshness_pressure=official_freshness_pressure,
        source_quorum_score=source_quorum_score,
        contradiction_pressure=item.contradiction_pressure,
        resolution_rule_coverage_ratio=resolution_rule_coverage_ratio,
    )
    reason_codes = _row_reason_codes(
        official_evidence_age_seconds=official_evidence_age_seconds,
        official_source_count=item.official_source_count,
        independent_source_count=item.independent_source_count,
        contradiction_pressure=item.contradiction_pressure,
        resolution_rule_coverage_ratio=resolution_rule_coverage_ratio,
        config=config,
    )
    return ResearchEventOutcomeEvidencePacketQualityReportRow(
        packet_public_label=packet_public_label,
        official_evidence_age_seconds=official_evidence_age_seconds,
        official_freshness_pressure=official_freshness_pressure,
        official_source_count=item.official_source_count,
        independent_source_count=item.independent_source_count,
        source_quorum_score=source_quorum_score,
        contradiction_pressure=item.contradiction_pressure,
        required_resolution_rule_count=item.required_resolution_rule_count,
        covered_resolution_rule_count=item.covered_resolution_rule_count,
        resolution_rule_coverage_ratio=resolution_rule_coverage_ratio,
        quality_pressure_score=quality_pressure_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    official_evidence_age_seconds: Decimal,
    official_source_count: Decimal,
    independent_source_count: Decimal,
    contradiction_pressure: Decimal,
    resolution_rule_coverage_ratio: Decimal,
    config: ResearchEventOutcomeEvidencePacketQualityReportConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if official_evidence_age_seconds > config.max_watch_official_evidence_age_seconds:
        reasons.append(OFFICIAL_FRESHNESS_BLOCK_REASON)
    elif official_evidence_age_seconds > config.max_pass_official_evidence_age_seconds:
        reasons.append(OFFICIAL_FRESHNESS_WATCH_REASON)

    if official_source_count < config.min_watch_official_source_count:
        reasons.append(OFFICIAL_SOURCE_BLOCK_REASON)
    elif official_source_count < config.min_pass_official_source_count:
        reasons.append(OFFICIAL_SOURCE_WATCH_REASON)

    if independent_source_count < config.min_watch_independent_source_count:
        reasons.append(INDEPENDENT_SOURCE_BLOCK_REASON)
    elif independent_source_count < config.min_pass_independent_source_count:
        reasons.append(INDEPENDENT_SOURCE_WATCH_REASON)

    if contradiction_pressure > config.block_contradiction_pressure:
        reasons.append(CONTRADICTION_BLOCK_REASON)
    elif contradiction_pressure > config.watch_contradiction_pressure:
        reasons.append(CONTRADICTION_WATCH_REASON)

    if resolution_rule_coverage_ratio < config.min_watch_resolution_rule_coverage_ratio:
        reasons.append(RULE_COVERAGE_BLOCK_REASON)
    elif resolution_rule_coverage_ratio < config.min_pass_resolution_rule_coverage_ratio:
        reasons.append(RULE_COVERAGE_WATCH_REASON)

    if any(reason in BLOCK_REASONS for reason in reasons):
        reasons.append(BLOCK_REASON)
    elif any(reason in WATCH_REASONS for reason in reasons):
        reasons.append(WATCH_REASON)
    else:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _report_reason_codes(
    rows: tuple[ResearchEventOutcomeEvidencePacketQualityReportRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON, BLOCK_REASON)
    if all(row.status == "pass" for row in rows):
        return (PASS_REASON,)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(
            reason
            for row in rows
            for reason in row.reason_codes
            if reason != PASS_REASON
        ),
    )


def _reason_code_counts(
    rows: tuple[ResearchEventOutcomeEvidencePacketQualityReportRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchEventOutcomeEvidencePacketQualityReportReasonCodeCount, ...]:
    if not rows:
        return tuple(
            ResearchEventOutcomeEvidencePacketQualityReportReasonCodeCount(
                reason_code=reason_code,
                count=ONE,
            )
            for reason_code in reason_codes
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchEventOutcomeEvidencePacketQualityReportReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: REASON_CODE_PRIORITY.index(item[0]),
        )
    )


def _normalize_inputs(
    value: Iterable[ResearchEventOutcomeEvidencePacketQualityReportInput],
    *,
    generated_at: datetime,
) -> tuple[ResearchEventOutcomeEvidencePacketQualityReportInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchEventOutcomeEvidencePacketQualityReportInput:
            raise ValueError(
                "inputs must contain "
                "ResearchEventOutcomeEvidencePacketQualityReportInput values",
            )
        _require_hard_flags("input", row)
        if row.evidence_packet_label in seen:
            raise ValueError("evidence_packet_label values must be unique")
        seen.add(row.evidence_packet_label)
        if row.latest_official_evidence_at > generated_at:
            raise ValueError(
                "latest_official_evidence_at must not be after generated_at",
            )
    return tuple(sorted(rows, key=lambda row: row.evidence_packet_label))


def _normalize_rows(
    value: Iterable[ResearchEventOutcomeEvidencePacketQualityReportRow],
) -> tuple[ResearchEventOutcomeEvidencePacketQualityReportRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchEventOutcomeEvidencePacketQualityReportRow:
            raise ValueError(
                "rows must contain "
                "ResearchEventOutcomeEvidencePacketQualityReportRow values",
            )
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and packet_public_label")
    return rows


def _normalize_reason_code_counts(
    value: Iterable[ResearchEventOutcomeEvidencePacketQualityReportReasonCodeCount],
) -> tuple[ResearchEventOutcomeEvidencePacketQualityReportReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        counts = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for count in counts:
        if type(count) is not ResearchEventOutcomeEvidencePacketQualityReportReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventOutcomeEvidencePacketQualityReportReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    if counts != tuple(
        sorted(counts, key=lambda row: REASON_CODE_PRIORITY.index(row.reason_code)),
    ):
        raise ValueError("reason_code_counts must be sorted by reason_code priority")
    return counts


def _validate_config(
    config: ResearchEventOutcomeEvidencePacketQualityReportConfig,
) -> None:
    if (
        config.max_pass_official_evidence_age_seconds
        >= config.max_watch_official_evidence_age_seconds
    ):
        raise ValueError(
            "max_pass_official_evidence_age_seconds must be less than "
            "max_watch_official_evidence_age_seconds",
        )
    if config.min_pass_official_source_count < config.min_watch_official_source_count:
        raise ValueError(
            "min_pass_official_source_count must be greater than or equal to "
            "min_watch_official_source_count",
        )
    if (
        config.min_pass_independent_source_count
        < config.min_watch_independent_source_count
    ):
        raise ValueError(
            "min_pass_independent_source_count must be greater than or equal to "
            "min_watch_independent_source_count",
        )
    if config.block_contradiction_pressure <= config.watch_contradiction_pressure:
        raise ValueError(
            "block_contradiction_pressure must exceed watch_contradiction_pressure",
        )
    if (
        config.min_pass_resolution_rule_coverage_ratio
        < config.min_watch_resolution_rule_coverage_ratio
    ):
        raise ValueError(
            "min_pass_resolution_rule_coverage_ratio must be greater than or equal to "
            "min_watch_resolution_rule_coverage_ratio",
        )


def _validate_row(row: ResearchEventOutcomeEvidencePacketQualityReportRow) -> None:
    if row.covered_resolution_rule_count > row.required_resolution_rule_count:
        raise ValueError(
            "covered_resolution_rule_count must not exceed required_resolution_rule_count",
        )
    if row.resolution_rule_coverage_ratio != _safe_ratio(
        row.covered_resolution_rule_count,
        row.required_resolution_rule_count,
        zero_denominator=ONE,
    ):
        raise ValueError("resolution_rule_coverage_ratio must match rule counts")
    expected_quality_pressure = _quality_pressure_score(
        official_freshness_pressure=row.official_freshness_pressure,
        source_quorum_score=row.source_quorum_score,
        contradiction_pressure=row.contradiction_pressure,
        resolution_rule_coverage_ratio=row.resolution_rule_coverage_ratio,
    )
    if row.quality_pressure_score != expected_quality_pressure:
        raise ValueError("quality_pressure_score must match component pressures")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("row status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must only carry pass reason")


def _validate_report(report: ResearchEventOutcomeEvidencePacketQualityReport) -> None:
    _require_hard_flags("report", report)
    row_count = len(report.rows)
    if report.packet_count != _count(row_count):
        raise ValueError("packet_count must match rows")
    if report.pass_count != _count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.max_official_evidence_age_seconds != _max_decimal(
        (row.official_evidence_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_official_evidence_age_seconds must match rows")
    if report.min_source_quorum_score != _min_decimal(
        (row.source_quorum_score for row in report.rows),
        default=ONE,
    ):
        raise ValueError("min_source_quorum_score must match rows")
    if report.max_contradiction_pressure != _max_decimal(
        (row.contradiction_pressure for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_contradiction_pressure must match rows")
    if report.min_resolution_rule_coverage_ratio != _min_decimal(
        (row.resolution_rule_coverage_ratio for row in report.rows),
        default=ONE,
    ):
        raise ValueError("min_resolution_rule_coverage_ratio must match rows")
    expected_average = (
        _average_decimal(row.quality_pressure_score for row in report.rows)
        if report.rows
        else ONE
    )
    if report.average_quality_pressure_score != expected_average:
        raise ValueError("average_quality_pressure_score must match rows")
    expected_reason_codes = _report_reason_codes(report.rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("report reason_codes must match rows")
    if report.status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("report status must match reason_codes")
    expected_reason_code_counts = _reason_code_counts(report.rows, report.reason_codes)
    if report.reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts must match rows")


def _set_or_validate_public_digest(
    report: ResearchEventOutcomeEvidencePacketQualityReport,
) -> None:
    expected_digest = _public_digest_from_payload(_payload_value_without_digest(report))
    if report.public_digest == "":
        object.__setattr__(report, "public_digest", expected_digest)
        return
    _require_sha256_digest("public_digest", report.public_digest)
    if report.public_digest != expected_digest:
        raise ValueError("public_digest must match report payload")


def _validate_public_digest(
    report: ResearchEventOutcomeEvidencePacketQualityReport,
) -> None:
    _require_sha256_digest("public_digest", report.public_digest)
    expected_digest = _public_digest_from_payload(_payload_value_without_digest(report))
    if report.public_digest != expected_digest:
        raise ValueError("public_digest must match report payload")


def _validate_payload_public_digest(payload: dict[str, Any]) -> None:
    public_digest = payload.get("public_digest")
    _require_sha256_digest("public_digest", public_digest)
    payload_without_digest = dict(payload)
    payload_without_digest.pop("public_digest", None)
    expected_digest = _public_digest_from_payload(payload_without_digest)
    if public_digest != expected_digest:
        raise ValueError("public_digest must match public payload")


def _payload_value(
    report: ResearchEventOutcomeEvidencePacketQualityReport,
) -> dict[str, Any]:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _payload_value_without_digest(
    report: ResearchEventOutcomeEvidencePacketQualityReport,
) -> dict[str, Any]:
    values = asdict(report)
    values.pop("public_digest", None)
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _public_digest_from_payload(payload: Mapping[str, Any]) -> str:
    _reject_unsafe_public_payload("public digest payload", payload)
    _reject_public_numeric_scalars(payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        payload: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            payload[key] = _json_ready(item)
        return payload
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _validate_public_statuses(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key == "status":
                _require_member("status", item, STATUSES)
            _validate_public_statuses(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_public_statuses(item)


def _reject_public_numeric_scalars(value: object) -> None:
    if type(value) in (int, float) or type(value) is Decimal:
        raise ValueError("public payload numeric values must be Decimal strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_numeric_scalars(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numeric_scalars(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    if type(value) in (int, float):
        return
    raise ValueError("unsupported public payload value")


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public payload")


def _require_private_label(field_name: str, value: object) -> str:
    label = _require_public_label(field_name, value)
    _reject_unsafe_public_text(field_name, label)
    return label


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a stable public label")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    return value


def _require_member(field_name: str, value: object, allowed: Iterable[str]) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    allowed_values = tuple(allowed)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must include {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if isinstance(value, Decimal) and type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    return _quantize(_require_decimal(field_name, value))


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(COUNT_QUANTUM)
    if normalized != value:
        raise ValueError(f"{field_name} must be an integral Decimal")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _elapsed_seconds(earlier: datetime, later: datetime) -> Decimal:
    earlier_utc = _as_utc("latest_official_evidence_at", earlier)
    later_utc = _as_utc("generated_at", later)
    if earlier_utc > later_utc:
        raise ValueError("latest_official_evidence_at must not be after generated_at")
    return _quantize(Decimal(str((later_utc - earlier_utc).total_seconds())))


def _source_quorum_score(
    item: ResearchEventOutcomeEvidencePacketQualityReportInput,
    config: ResearchEventOutcomeEvidencePacketQualityReportConfig,
) -> Decimal:
    official_ratio = _safe_ratio(
        item.official_source_count,
        config.min_pass_official_source_count,
        zero_denominator=ONE,
    )
    independent_ratio = _safe_ratio(
        item.independent_source_count,
        config.min_pass_independent_source_count,
        zero_denominator=ONE,
    )
    return min(official_ratio, independent_ratio)


def _resolution_rule_coverage_ratio(
    item: ResearchEventOutcomeEvidencePacketQualityReportInput,
) -> Decimal:
    return _safe_ratio(
        item.covered_resolution_rule_count,
        item.required_resolution_rule_count,
        zero_denominator=ONE,
    )


def _quality_pressure_score(
    *,
    official_freshness_pressure: Decimal,
    source_quorum_score: Decimal,
    contradiction_pressure: Decimal,
    resolution_rule_coverage_ratio: Decimal,
) -> Decimal:
    return max(
        official_freshness_pressure,
        _quantize(ONE - source_quorum_score),
        contradiction_pressure,
        _quantize(ONE - resolution_rule_coverage_ratio),
    )


def _safe_ratio(
    numerator: Decimal,
    denominator: Decimal,
    *,
    zero_denominator: Decimal,
) -> Decimal:
    if denominator == ZERO:
        return zero_denominator
    return _ratio(numerator, denominator)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        value = numerator / denominator
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _quantize(value)


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(items, ZERO) / Decimal(len(items)))


def _max_decimal(values: Iterable[Decimal], *, default: Decimal) -> Decimal:
    items = tuple(values)
    if not items:
        return default
    return max(items)


def _min_decimal(values: Iterable[Decimal], *, default: Decimal) -> Decimal:
    items = tuple(values)
    if not items:
        return default
    return min(items)


def _status_count(
    rows: tuple[ResearchEventOutcomeEvidencePacketQualityReportRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _row_sort_key(
    row: ResearchEventOutcomeEvidencePacketQualityReportRow,
) -> tuple[int, str]:
    return (STATUS_ORDER[row.status], row.packet_public_label)


def _normalize_reason_codes(
    field_name: str,
    value: Iterable[str],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_member("reason_code", reason_code, REASON_CODES)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in REASON_CODE_PRIORITY
        if reason_code in normalized
    )


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(VALUE_QUANTUM, rounding=ROUND_HALF_EVEN)


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "STATUSES",
    "ResearchEventOutcomeEvidencePacketQualityReportConfig",
    "ResearchEventOutcomeEvidencePacketQualityReportInput",
    "ResearchEventOutcomeEvidencePacketQualityReportReasonCodeCount",
    "ResearchEventOutcomeEvidencePacketQualityReportRow",
    "ResearchEventOutcomeEvidencePacketQualityReport",
    "build_research_event_outcome_evidence_packet_quality_report",
    "research_event_outcome_evidence_packet_quality_report_public_payload",
    "research_event_outcome_evidence_packet_quality_report_public_digest",
    "validate_research_event_outcome_evidence_packet_quality_report_public_payload",
)
