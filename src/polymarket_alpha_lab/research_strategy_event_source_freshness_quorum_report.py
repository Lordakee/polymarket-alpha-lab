"""Pure in-memory event-source freshness and evidence-quorum diagnostic report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields
from datetime import UTC, datetime
from decimal import Context, Decimal, DecimalException, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_STRATEGY_EVENT_SOURCE_FRESHNESS_QUORUM_CONFIG_VERSION = (
    "research-strategy-event-source-freshness-quorum-report-v0"
)

DIAGNOSTIC_STATUSES = ("pass", "watch", "block")
PASS_REASON_CODE = "event_source_freshness_quorum_pass"
REASON_CODES = (
    "event_source_freshness_watch",
    "event_source_freshness_block",
    "event_evidence_quorum_watch",
    "event_evidence_quorum_block",
    "event_independent_evidence_quorum_watch",
    "event_independent_evidence_quorum_block",
    PASS_REASON_CODE,
)
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
ROW_DIGEST_LABEL = "research_strategy_event_source_freshness_quorum_report_row"
REPORT_DIGEST_LABEL = "research_strategy_event_source_freshness_quorum_report"

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
MICROSECOND_DIVISOR = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=50, rounding=ROUND_HALF_UP)

PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
CANONICAL_NONNEGATIVE_DECIMAL_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "private_source_identifier",
    "source_url",
    "source_text",
    "raw_text",
    "raw_identifier",
    "candidate_id",
    "condition_id",
    "market_id",
    "market_slug",
    "private_key",
    "api_key",
    "wallet",
    "order",
    "trade",
    "position",
    "recommend",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "://",
    "www.",
    "private_source_identifier",
    "source_url",
    "source_text",
    "raw_text",
    "private_key",
    "api_key",
    "credential",
    "secret",
    "wallet",
    "order",
    "trade",
    "position",
    "recommend",
    "buy",
    "sell",
)

CONFIG_PAYLOAD_FIELDS = (
    "config_version",
    "freshness_watch_age_seconds",
    "freshness_block_age_seconds",
    "quorum_pass_threshold",
    "quorum_block_threshold",
    "independent_quorum_pass_threshold",
    "independent_quorum_block_threshold",
    "freshness_weight",
    "evidence_quorum_weight",
    "independent_quorum_weight",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "config_version",
    "review_rank",
    "event_label",
    "public_source_label",
    "observed_at",
    "evidence_count",
    "required_evidence_count",
    "independent_evidence_count",
    "required_independent_evidence_count",
    "source_age_seconds",
    "freshness_score",
    "evidence_quorum_score",
    "independent_quorum_score",
    "diagnostic_score",
    "diagnostic_status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_FIELDS = (
    *ROW_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)
REASON_COUNT_PAYLOAD_FIELDS = (
    "reason_code",
    "row_count",
    "row_ratio",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "config",
    "generated_at",
    "status",
    "event_source_count",
    "pass_count",
    "watch_count",
    "block_count",
    "stale_count",
    "quorum_deficit_count",
    "average_freshness_score",
    "average_evidence_quorum_score",
    "average_independent_quorum_score",
    "average_diagnostic_score",
    "minimum_diagnostic_score",
    "maximum_source_age_seconds",
    "reason_codes",
    "reason_code_counts",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_FIELDS = (
    *REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_EVENT_SOURCE_FRESHNESS_QUORUM_CONFIG_VERSION",
    "DIAGNOSTIC_STATUSES",
    "ResearchStrategyEventSourceFreshnessQuorumConfig",
    "ResearchStrategyEventSourceFreshnessQuorumObservation",
    "ResearchStrategyEventSourceFreshnessQuorumReasonCount",
    "ResearchStrategyEventSourceFreshnessQuorumReport",
    "ResearchStrategyEventSourceFreshnessQuorumRow",
    "build_research_strategy_event_source_freshness_quorum_report",
    "research_strategy_event_source_freshness_quorum_report_digest",
    "research_strategy_event_source_freshness_quorum_report_payload",
    "validate_research_strategy_event_source_freshness_quorum_public_payload",
)


@dataclass(frozen=True)
class ResearchStrategyEventSourceFreshnessQuorumConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_EVENT_SOURCE_FRESHNESS_QUORUM_CONFIG_VERSION
    )
    freshness_watch_age_seconds: Decimal = Decimal("1800.000000")
    freshness_block_age_seconds: Decimal = Decimal("7200.000000")
    quorum_pass_threshold: Decimal = Decimal("0.750000")
    quorum_block_threshold: Decimal = Decimal("0.500000")
    independent_quorum_pass_threshold: Decimal = Decimal("0.750000")
    independent_quorum_block_threshold: Decimal = Decimal("0.500000")
    freshness_weight: Decimal = Decimal("0.400000")
    evidence_quorum_weight: Decimal = Decimal("0.350000")
    independent_quorum_weight: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyEventSourceFreshnessQuorumConfig "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchStrategyEventSourceFreshnessQuorumConfig,
        )
        _require_public_label("config_version", self.config_version)
        weight_field_names = (
            "freshness_weight",
            "evidence_quorum_weight",
            "independent_quorum_weight",
        )
        raw_weight_total = _sum_decimals(
            tuple(
                _require_probability_decimal_raw(
                    field_name,
                    getattr(self, field_name),
                )
                for field_name in weight_field_names
            ),
        )
        if raw_weight_total != ONE:
            raise ValueError("weights must sum to one")
        for field_name in (
            "freshness_watch_age_seconds",
            "freshness_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "quorum_pass_threshold",
            "quorum_block_threshold",
            "independent_quorum_pass_threshold",
            "independent_quorum_block_threshold",
            *weight_field_names,
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.freshness_block_age_seconds <= self.freshness_watch_age_seconds:
            raise ValueError(
                "freshness_block_age_seconds must exceed "
                "freshness_watch_age_seconds",
            )
        if self.quorum_pass_threshold <= self.quorum_block_threshold:
            raise ValueError(
                "quorum_pass_threshold must exceed quorum_block_threshold",
            )
        if (
            self.independent_quorum_pass_threshold
            <= self.independent_quorum_block_threshold
        ):
            raise ValueError(
                "independent_quorum_pass_threshold must exceed "
                "independent_quorum_block_threshold",
            )
        if _sum_decimals(
            (
                self.freshness_weight,
                self.evidence_quorum_weight,
                self.independent_quorum_weight,
            ),
        ) != ONE:
            raise ValueError("weights must sum to one")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyEventSourceFreshnessQuorumObservation:
    event_label: str
    public_source_label: str
    private_source_identifier: str
    observed_at: datetime
    evidence_count: Decimal
    required_evidence_count: Decimal
    independent_evidence_count: Decimal
    required_independent_evidence_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyEventSourceFreshnessQuorumObservation "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "observation",
            self,
            ResearchStrategyEventSourceFreshnessQuorumObservation,
        )
        _require_public_label("event_label", self.event_label)
        _require_public_label("public_source_label", self.public_source_label)
        _require_private_identifier(self.private_source_identifier)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("evidence_count", "independent_evidence_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "required_evidence_count",
            "required_independent_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _validate_evidence_counts(
            self.evidence_count,
            self.required_evidence_count,
            self.independent_evidence_count,
            self.required_independent_evidence_count,
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchStrategyEventSourceFreshnessQuorumRow:
    config_version: str
    review_rank: Decimal
    event_label: str
    public_source_label: str
    observed_at: datetime
    evidence_count: Decimal
    required_evidence_count: Decimal
    independent_evidence_count: Decimal
    required_independent_evidence_count: Decimal
    source_age_seconds: Decimal
    freshness_score: Decimal
    evidence_quorum_score: Decimal
    independent_quorum_score: Decimal
    diagnostic_score: Decimal
    diagnostic_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyEventSourceFreshnessQuorumRow "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "row",
            self,
            ResearchStrategyEventSourceFreshnessQuorumRow,
        )
        for field_name in ("config_version", "event_label", "public_source_label"):
            _require_public_label(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "review_rank",
            _normalize_positive_whole_decimal("review_rank", self.review_rank),
        )
        for field_name in ("evidence_count", "independent_evidence_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "required_evidence_count",
            "required_independent_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_nonnegative_decimal(
                "source_age_seconds",
                self.source_age_seconds,
            ),
        )
        for field_name in (
            "freshness_score",
            "evidence_quorum_score",
            "independent_quorum_score",
            "diagnostic_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("diagnostic_status", self.diagnostic_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_evidence_counts(
            self.evidence_count,
            self.required_evidence_count,
            self.independent_evidence_count,
            self.required_independent_evidence_count,
        )
        _validate_status_reason_shape(self.diagnostic_status, self.reason_codes)
        _require_hard_flags("row", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _row_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _require_sha256_digest(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_row_derived_validation_digest(self)


@dataclass(frozen=True)
class ResearchStrategyEventSourceFreshnessQuorumReasonCount:
    reason_code: str
    row_count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyEventSourceFreshnessQuorumReasonCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "reason_count",
            self,
            ResearchStrategyEventSourceFreshnessQuorumReasonCount,
        )
        _require_member("reason_code", self.reason_code, REASON_CODES)
        object.__setattr__(
            self,
            "row_count",
            _normalize_positive_whole_decimal("row_count", self.row_count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_probability_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_count", self)


@dataclass(frozen=True)
class ResearchStrategyEventSourceFreshnessQuorumReport:
    config: ResearchStrategyEventSourceFreshnessQuorumConfig
    generated_at: datetime
    status: str
    event_source_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_count: Decimal
    quorum_deficit_count: Decimal
    average_freshness_score: Decimal
    average_evidence_quorum_score: Decimal
    average_independent_quorum_score: Decimal
    average_diagnostic_score: Decimal
    minimum_diagnostic_score: Decimal
    maximum_source_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategyEventSourceFreshnessQuorumReasonCount, ...]
    rows: tuple[ResearchStrategyEventSourceFreshnessQuorumRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchStrategyEventSourceFreshnessQuorumReport "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            ResearchStrategyEventSourceFreshnessQuorumReport,
        )
        _require_exact_type(
            "config",
            self.config,
            ResearchStrategyEventSourceFreshnessQuorumConfig,
        )
        object.__setattr__(self, "config", _normalize_config(self.config))
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_counts(self.reason_code_counts),
        )
        for field_name in (
            "event_source_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_count",
            "quorum_deficit_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_freshness_score",
            "average_evidence_quorum_score",
            "average_independent_quorum_score",
            "average_diagnostic_score",
            "minimum_diagnostic_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "maximum_source_age_seconds",
            _normalize_nonnegative_decimal(
                "maximum_source_age_seconds",
                self.maximum_source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _require_sha256_digest(
                    DERIVED_VALIDATION_DIGEST_FIELD,
                    self.derived_validation_digest,
                ),
            )
        _validate_report_derived_validation_digest(self)
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        return research_strategy_event_source_freshness_quorum_report_payload(self)


def build_research_strategy_event_source_freshness_quorum_report(
    observations: Iterable[object],
    *,
    generated_at: datetime,
    config: ResearchStrategyEventSourceFreshnessQuorumConfig | None = None,
) -> ResearchStrategyEventSourceFreshnessQuorumReport:
    """Build a deterministic diagnostic for human research review."""

    if config is None:
        config = ResearchStrategyEventSourceFreshnessQuorumConfig()
    config = _normalize_config(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for observation in normalized_observations:
        if observation.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    metrics = tuple(
        sorted(
            (
                _metrics_from_values(
                    config_version=config.config_version,
                    event_label=observation.event_label,
                    public_source_label=observation.public_source_label,
                    observed_at=observation.observed_at,
                    evidence_count=observation.evidence_count,
                    required_evidence_count=observation.required_evidence_count,
                    independent_evidence_count=observation.independent_evidence_count,
                    required_independent_evidence_count=(
                        observation.required_independent_evidence_count
                    ),
                    generated_at=generated_at_utc,
                    config=config,
                )
                for observation in normalized_observations
            ),
            key=_metrics_sort_key,
        ),
    )
    rows = tuple(
        ResearchStrategyEventSourceFreshnessQuorumRow(
            review_rank=_count(index),
            **item,
        )
        for index, item in enumerate(metrics, start=1)
    )
    row_count = _count(len(rows))
    return ResearchStrategyEventSourceFreshnessQuorumReport(
        config=config,
        generated_at=generated_at_utc,
        status=_report_status(rows),
        event_source_count=row_count,
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        stale_count=_stale_count(rows),
        quorum_deficit_count=_quorum_deficit_count(rows),
        average_freshness_score=_average(
            tuple(row.freshness_score for row in rows),
        ),
        average_evidence_quorum_score=_average(
            tuple(row.evidence_quorum_score for row in rows),
        ),
        average_independent_quorum_score=_average(
            tuple(row.independent_quorum_score for row in rows),
        ),
        average_diagnostic_score=_average(
            tuple(row.diagnostic_score for row in rows),
        ),
        minimum_diagnostic_score=_minimum(
            tuple(row.diagnostic_score for row in rows),
        ),
        maximum_source_age_seconds=_maximum(
            tuple(row.source_age_seconds for row in rows),
        ),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_strategy_event_source_freshness_quorum_report_payload(
    report: ResearchStrategyEventSourceFreshnessQuorumReport | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchStrategyEventSourceFreshnessQuorumReport:
        _validate_report_derived_validation_digest(report)
        _validate_report_consistency(report)
        payload = _report_public_payload_without_digest(report)
        payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
        _reject_unsafe_public_payload("report payload", payload)
        return payload
    if type(report) is dict:
        validated = _report_from_public_payload(report)
        return research_strategy_event_source_freshness_quorum_report_payload(
            validated,
        )
    raise ValueError(
        "report must be a ResearchStrategyEventSourceFreshnessQuorumReport "
        "or exact dict",
    )


def research_strategy_event_source_freshness_quorum_report_digest(
    report: ResearchStrategyEventSourceFreshnessQuorumReport,
) -> str:
    _require_exact_type(
        "report",
        report,
        ResearchStrategyEventSourceFreshnessQuorumReport,
    )
    _validate_report_derived_validation_digest(report)
    _validate_report_consistency(report)
    return report.derived_validation_digest


def validate_research_strategy_event_source_freshness_quorum_public_payload(
    payload: object,
) -> bool:
    try:
        if type(payload) is not dict:
            return False
        _report_from_public_payload(payload)
        return True
    except (TypeError, ValueError):
        return False


def _metrics_from_values(
    *,
    config_version: str,
    event_label: str,
    public_source_label: str,
    observed_at: datetime,
    evidence_count: Decimal,
    required_evidence_count: Decimal,
    independent_evidence_count: Decimal,
    required_independent_evidence_count: Decimal,
    generated_at: datetime,
    config: ResearchStrategyEventSourceFreshnessQuorumConfig,
) -> dict[str, Any]:
    with localcontext(DECIMAL_CONTEXT):
        source_age_seconds = _datetime_delta_seconds(generated_at, observed_at)
        freshness_score = _cap_probability(
            ONE - _ratio_raw(source_age_seconds, config.freshness_block_age_seconds),
        )
        evidence_quorum_score = _ratio(evidence_count, required_evidence_count)
        independent_quorum_score = _ratio(
            independent_evidence_count,
            required_independent_evidence_count,
        )
        diagnostic_score = _cap_probability(
            (freshness_score * config.freshness_weight)
            + (evidence_quorum_score * config.evidence_quorum_weight)
            + (independent_quorum_score * config.independent_quorum_weight),
        )
    diagnostic_status = _diagnostic_status(
        source_age_seconds=source_age_seconds,
        evidence_quorum_score=evidence_quorum_score,
        independent_quorum_score=independent_quorum_score,
        config=config,
    )
    return {
        "config_version": config_version,
        "event_label": event_label,
        "public_source_label": public_source_label,
        "observed_at": observed_at,
        "evidence_count": evidence_count,
        "required_evidence_count": required_evidence_count,
        "independent_evidence_count": independent_evidence_count,
        "required_independent_evidence_count": (
            required_independent_evidence_count
        ),
        "source_age_seconds": source_age_seconds,
        "freshness_score": freshness_score,
        "evidence_quorum_score": evidence_quorum_score,
        "independent_quorum_score": independent_quorum_score,
        "diagnostic_score": diagnostic_score,
        "diagnostic_status": diagnostic_status,
        "reason_codes": _row_reason_codes(
            source_age_seconds=source_age_seconds,
            evidence_quorum_score=evidence_quorum_score,
            independent_quorum_score=independent_quorum_score,
            diagnostic_status=diagnostic_status,
            config=config,
        ),
    }


def _diagnostic_status(
    *,
    source_age_seconds: Decimal,
    evidence_quorum_score: Decimal,
    independent_quorum_score: Decimal,
    config: ResearchStrategyEventSourceFreshnessQuorumConfig,
) -> str:
    if (
        source_age_seconds >= config.freshness_block_age_seconds
        or evidence_quorum_score < config.quorum_block_threshold
        or (
            independent_quorum_score
            < config.independent_quorum_block_threshold
        )
    ):
        return "block"
    if (
        source_age_seconds >= config.freshness_watch_age_seconds
        or evidence_quorum_score < config.quorum_pass_threshold
        or (
            independent_quorum_score
            < config.independent_quorum_pass_threshold
        )
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    source_age_seconds: Decimal,
    evidence_quorum_score: Decimal,
    independent_quorum_score: Decimal,
    diagnostic_status: str,
    config: ResearchStrategyEventSourceFreshnessQuorumConfig,
) -> tuple[str, ...]:
    values: list[str] = []
    if source_age_seconds >= config.freshness_block_age_seconds:
        values.append("event_source_freshness_block")
    elif source_age_seconds >= config.freshness_watch_age_seconds:
        values.append("event_source_freshness_watch")

    if evidence_quorum_score < config.quorum_block_threshold:
        values.append("event_evidence_quorum_block")
    elif evidence_quorum_score < config.quorum_pass_threshold:
        values.append("event_evidence_quorum_watch")

    if (
        independent_quorum_score
        < config.independent_quorum_block_threshold
    ):
        values.append("event_independent_evidence_quorum_block")
    elif (
        independent_quorum_score
        < config.independent_quorum_pass_threshold
    ):
        values.append("event_independent_evidence_quorum_watch")

    if not values:
        values.append(PASS_REASON_CODE)
    normalized = _normalize_reason_codes("reason_codes", tuple(values))
    _validate_status_reason_shape(diagnostic_status, normalized)
    return normalized


def _report_status(
    rows: tuple[ResearchStrategyEventSourceFreshnessQuorumRow, ...],
) -> str:
    if any(row.diagnostic_status == "block" for row in rows):
        return "block"
    if any(row.diagnostic_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyEventSourceFreshnessQuorumRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (PASS_REASON_CODE,)
    present = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
    }
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in present)


def _reason_code_counts(
    rows: tuple[ResearchStrategyEventSourceFreshnessQuorumRow, ...],
) -> tuple[ResearchStrategyEventSourceFreshnessQuorumReasonCount, ...]:
    if not rows:
        return ()
    row_count = _count(len(rows))
    values: list[ResearchStrategyEventSourceFreshnessQuorumReasonCount] = []
    for reason_code in _report_reason_codes(rows):
        count = _count(
            sum(1 for row in rows if reason_code in row.reason_codes),
        )
        values.append(
            ResearchStrategyEventSourceFreshnessQuorumReasonCount(
                reason_code=reason_code,
                row_count=count,
                row_ratio=_ratio(count, row_count),
            ),
        )
    return tuple(values)


def _status_count(
    rows: tuple[ResearchStrategyEventSourceFreshnessQuorumRow, ...],
    status: str,
) -> Decimal:
    _require_status("status", status)
    return _count(sum(1 for row in rows if row.diagnostic_status == status))


def _stale_count(
    rows: tuple[ResearchStrategyEventSourceFreshnessQuorumRow, ...],
) -> Decimal:
    stale_reasons = {
        "event_source_freshness_watch",
        "event_source_freshness_block",
    }
    return _count(
        sum(1 for row in rows if stale_reasons.intersection(row.reason_codes)),
    )


def _quorum_deficit_count(
    rows: tuple[ResearchStrategyEventSourceFreshnessQuorumRow, ...],
) -> Decimal:
    quorum_reasons = {
        "event_evidence_quorum_watch",
        "event_evidence_quorum_block",
        "event_independent_evidence_quorum_watch",
        "event_independent_evidence_quorum_block",
    }
    return _count(
        sum(1 for row in rows if quorum_reasons.intersection(row.reason_codes)),
    )


def _metrics_sort_key(item: dict[str, Any]) -> tuple[object, ...]:
    return (
        -_status_severity(item["diagnostic_status"]),
        item["diagnostic_score"],
        _negate_decimal(item["source_age_seconds"]),
        item["event_label"],
        item["public_source_label"],
        item["observed_at"],
        item["evidence_count"],
        item["required_evidence_count"],
        item["independent_evidence_count"],
        item["required_independent_evidence_count"],
        item["freshness_score"],
        item["evidence_quorum_score"],
        item["independent_quorum_score"],
        item["reason_codes"],
        item["config_version"],
    )


def _row_sort_key(
    row: ResearchStrategyEventSourceFreshnessQuorumRow,
) -> tuple[object, ...]:
    return (
        -_status_severity(row.diagnostic_status),
        row.diagnostic_score,
        _negate_decimal(row.source_age_seconds),
        row.event_label,
        row.public_source_label,
        row.observed_at,
        row.evidence_count,
        row.required_evidence_count,
        row.independent_evidence_count,
        row.required_independent_evidence_count,
        row.freshness_score,
        row.evidence_quorum_score,
        row.independent_quorum_score,
        row.reason_codes,
        row.config_version,
    )


def _status_severity(status: str) -> int:
    _require_status("status", status)
    return {"pass": 0, "watch": 1, "block": 2}[status]


def _validate_report_consistency(
    report: ResearchStrategyEventSourceFreshnessQuorumReport,
) -> None:
    _require_hard_flags("config", report.config)
    expected_rows: list[ResearchStrategyEventSourceFreshnessQuorumRow] = []
    seen_keys: set[tuple[str, str]] = set()
    for index, row in enumerate(report.rows, start=1):
        if row.config_version != report.config.config_version:
            raise ValueError("row config_version must match report config")
        if row.observed_at > report.generated_at:
            raise ValueError("observed_at must not be after generated_at")
        public_key = (row.event_label, row.public_source_label)
        if public_key in seen_keys:
            raise ValueError("event and public source labels must be unique")
        seen_keys.add(public_key)
        expected_values = _metrics_from_values(
            config_version=report.config.config_version,
            event_label=row.event_label,
            public_source_label=row.public_source_label,
            observed_at=row.observed_at,
            evidence_count=row.evidence_count,
            required_evidence_count=row.required_evidence_count,
            independent_evidence_count=row.independent_evidence_count,
            required_independent_evidence_count=(
                row.required_independent_evidence_count
            ),
            generated_at=report.generated_at,
            config=report.config,
        )
        expected = ResearchStrategyEventSourceFreshnessQuorumRow(
            review_rank=_count(index),
            **expected_values,
        )
        _validate_row_matches_rederived(row, expected)
        expected_rows.append(expected)

    expected_rows_tuple = tuple(sorted(expected_rows, key=_row_sort_key))
    for index, expected in enumerate(expected_rows_tuple, start=1):
        actual = report.rows[index - 1]
        if actual.review_rank != _count(index):
            raise ValueError("review_rank must match stable row order")
        if _row_identity(actual) != _row_identity(expected):
            raise ValueError("rows must match stable diagnostic rank order")

    row_count = _count(len(report.rows))
    expected_scalars: tuple[tuple[str, Decimal | str], ...] = (
        ("event_source_count", row_count),
        ("pass_count", _status_count(report.rows, "pass")),
        ("watch_count", _status_count(report.rows, "watch")),
        ("block_count", _status_count(report.rows, "block")),
        ("stale_count", _stale_count(report.rows)),
        ("quorum_deficit_count", _quorum_deficit_count(report.rows)),
        (
            "average_freshness_score",
            _average(tuple(row.freshness_score for row in report.rows)),
        ),
        (
            "average_evidence_quorum_score",
            _average(tuple(row.evidence_quorum_score for row in report.rows)),
        ),
        (
            "average_independent_quorum_score",
            _average(tuple(row.independent_quorum_score for row in report.rows)),
        ),
        (
            "average_diagnostic_score",
            _average(tuple(row.diagnostic_score for row in report.rows)),
        ),
        (
            "minimum_diagnostic_score",
            _minimum(tuple(row.diagnostic_score for row in report.rows)),
        ),
        (
            "maximum_source_age_seconds",
            _maximum(tuple(row.source_age_seconds for row in report.rows)),
        ),
        ("status", _report_status(report.rows)),
    )
    for field_name, expected_value in expected_scalars:
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rederived rows")
    if _sum_decimals(
        (report.pass_count, report.watch_count, report.block_count),
    ) != row_count:
        raise ValueError("status counts must match event_source_count")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rederived rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rederived rows")


def _validate_row_matches_rederived(
    actual: ResearchStrategyEventSourceFreshnessQuorumRow,
    expected: ResearchStrategyEventSourceFreshnessQuorumRow,
) -> None:
    derived_fields = (
        "source_age_seconds",
        "freshness_score",
        "evidence_quorum_score",
        "independent_quorum_score",
        "diagnostic_score",
        "diagnostic_status",
        "reason_codes",
    )
    for field_name in derived_fields:
        if getattr(actual, field_name) != getattr(expected, field_name):
            raise ValueError(f"{field_name} must match rederived row inputs")


def _row_identity(
    row: ResearchStrategyEventSourceFreshnessQuorumRow,
) -> tuple[object, ...]:
    return (
        row.event_label,
        row.public_source_label,
        row.observed_at,
        row.evidence_count,
        row.required_evidence_count,
        row.independent_evidence_count,
        row.required_independent_evidence_count,
        row.source_age_seconds,
        row.freshness_score,
        row.evidence_quorum_score,
        row.independent_quorum_score,
        row.diagnostic_score,
        row.diagnostic_status,
        row.reason_codes,
    )


def _validate_status_reason_shape(
    status: str,
    reason_codes: tuple[str, ...],
) -> None:
    if status == "pass" and reason_codes != (PASS_REASON_CODE,):
        raise ValueError("pass status must only use the pass reason code")
    if status != "pass" and reason_codes == (PASS_REASON_CODE,):
        raise ValueError("non-pass status must include diagnostic reason codes")
    if status != "pass" and PASS_REASON_CODE in reason_codes:
        raise ValueError("non-pass status must not include the pass reason code")


def _validate_evidence_counts(
    evidence_count: Decimal,
    required_evidence_count: Decimal,
    independent_evidence_count: Decimal,
    required_independent_evidence_count: Decimal,
) -> None:
    if evidence_count > required_evidence_count:
        raise ValueError(
            "evidence_count must not exceed required_evidence_count",
        )
    if independent_evidence_count > required_independent_evidence_count:
        raise ValueError(
            "independent_evidence_count must not exceed "
            "required_independent_evidence_count",
        )


def _config_public_payload(
    config: ResearchStrategyEventSourceFreshnessQuorumConfig,
) -> dict[str, object]:
    return {
        "config_version": config.config_version,
        "freshness_watch_age_seconds": _decimal_payload(
            config.freshness_watch_age_seconds,
        ),
        "freshness_block_age_seconds": _decimal_payload(
            config.freshness_block_age_seconds,
        ),
        "quorum_pass_threshold": _decimal_payload(config.quorum_pass_threshold),
        "quorum_block_threshold": _decimal_payload(config.quorum_block_threshold),
        "independent_quorum_pass_threshold": _decimal_payload(
            config.independent_quorum_pass_threshold,
        ),
        "independent_quorum_block_threshold": _decimal_payload(
            config.independent_quorum_block_threshold,
        ),
        "freshness_weight": _decimal_payload(config.freshness_weight),
        "evidence_quorum_weight": _decimal_payload(config.evidence_quorum_weight),
        "independent_quorum_weight": _decimal_payload(
            config.independent_quorum_weight,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_public_payload_without_digest(
    row: ResearchStrategyEventSourceFreshnessQuorumRow,
) -> dict[str, object]:
    return {
        "config_version": row.config_version,
        "review_rank": _decimal_payload(row.review_rank),
        "event_label": row.event_label,
        "public_source_label": row.public_source_label,
        "observed_at": _datetime_payload(row.observed_at),
        "evidence_count": _decimal_payload(row.evidence_count),
        "required_evidence_count": _decimal_payload(row.required_evidence_count),
        "independent_evidence_count": _decimal_payload(
            row.independent_evidence_count,
        ),
        "required_independent_evidence_count": _decimal_payload(
            row.required_independent_evidence_count,
        ),
        "source_age_seconds": _decimal_payload(row.source_age_seconds),
        "freshness_score": _decimal_payload(row.freshness_score),
        "evidence_quorum_score": _decimal_payload(row.evidence_quorum_score),
        "independent_quorum_score": _decimal_payload(
            row.independent_quorum_score,
        ),
        "diagnostic_score": _decimal_payload(row.diagnostic_score),
        "diagnostic_status": row.diagnostic_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_public_payload(
    row: ResearchStrategyEventSourceFreshnessQuorumRow,
) -> dict[str, object]:
    _validate_row_derived_validation_digest(row)
    payload = _row_public_payload_without_digest(row)
    payload[DERIVED_VALIDATION_DIGEST_FIELD] = row.derived_validation_digest
    return payload


def _reason_count_public_payload(
    value: ResearchStrategyEventSourceFreshnessQuorumReasonCount,
) -> dict[str, object]:
    return {
        "reason_code": value.reason_code,
        "row_count": _decimal_payload(value.row_count),
        "row_ratio": _decimal_payload(value.row_ratio),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_public_payload_without_digest(
    report: ResearchStrategyEventSourceFreshnessQuorumReport,
) -> dict[str, object]:
    return {
        "config": _config_public_payload(report.config),
        "generated_at": _datetime_payload(report.generated_at),
        "status": report.status,
        "event_source_count": _decimal_payload(report.event_source_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "stale_count": _decimal_payload(report.stale_count),
        "quorum_deficit_count": _decimal_payload(report.quorum_deficit_count),
        "average_freshness_score": _decimal_payload(
            report.average_freshness_score,
        ),
        "average_evidence_quorum_score": _decimal_payload(
            report.average_evidence_quorum_score,
        ),
        "average_independent_quorum_score": _decimal_payload(
            report.average_independent_quorum_score,
        ),
        "average_diagnostic_score": _decimal_payload(
            report.average_diagnostic_score,
        ),
        "minimum_diagnostic_score": _decimal_payload(
            report.minimum_diagnostic_score,
        ),
        "maximum_source_age_seconds": _decimal_payload(
            report.maximum_source_age_seconds,
        ),
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            _reason_count_public_payload(value)
            for value in report.reason_code_counts
        ],
        "rows": [_row_public_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_derived_validation_digest(
    row: ResearchStrategyEventSourceFreshnessQuorumRow,
) -> str:
    return _derived_validation_digest(
        ROW_DIGEST_LABEL,
        _row_public_payload_without_digest(row),
    )


def _report_derived_validation_digest(
    report: ResearchStrategyEventSourceFreshnessQuorumReport,
) -> str:
    return _derived_validation_digest(
        REPORT_DIGEST_LABEL,
        _report_public_payload_without_digest(report),
    )


def _derived_validation_digest(label: str, payload: dict[str, object]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(f"{label}|{canonical}".encode("utf-8")).hexdigest()


def _validate_row_derived_validation_digest(
    row: ResearchStrategyEventSourceFreshnessQuorumRow,
) -> None:
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report_derived_validation_digest(
    report: ResearchStrategyEventSourceFreshnessQuorumReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _report_from_public_payload(
    payload: dict[str, object],
) -> ResearchStrategyEventSourceFreshnessQuorumReport:
    _require_exact_schema("report payload", payload, REPORT_PAYLOAD_FIELDS)
    _reject_unsafe_public_payload("report payload", payload)
    _validate_raw_digest(payload, REPORT_DIGEST_LABEL)
    config = _config_from_public_payload(payload["config"])
    rows_value = payload["rows"]
    reason_counts_value = payload["reason_code_counts"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a list")
    if type(reason_counts_value) is not list:
        raise ValueError("reason_code_counts must be a list")
    return ResearchStrategyEventSourceFreshnessQuorumReport(
        config=config,
        generated_at=_datetime_from_payload("generated_at", payload["generated_at"]),
        status=_string_from_payload("status", payload["status"]),
        event_source_count=_decimal_from_payload(
            "event_source_count",
            payload["event_source_count"],
        ),
        pass_count=_decimal_from_payload("pass_count", payload["pass_count"]),
        watch_count=_decimal_from_payload("watch_count", payload["watch_count"]),
        block_count=_decimal_from_payload("block_count", payload["block_count"]),
        stale_count=_decimal_from_payload("stale_count", payload["stale_count"]),
        quorum_deficit_count=_decimal_from_payload(
            "quorum_deficit_count",
            payload["quorum_deficit_count"],
        ),
        average_freshness_score=_decimal_from_payload(
            "average_freshness_score",
            payload["average_freshness_score"],
        ),
        average_evidence_quorum_score=_decimal_from_payload(
            "average_evidence_quorum_score",
            payload["average_evidence_quorum_score"],
        ),
        average_independent_quorum_score=_decimal_from_payload(
            "average_independent_quorum_score",
            payload["average_independent_quorum_score"],
        ),
        average_diagnostic_score=_decimal_from_payload(
            "average_diagnostic_score",
            payload["average_diagnostic_score"],
        ),
        minimum_diagnostic_score=_decimal_from_payload(
            "minimum_diagnostic_score",
            payload["minimum_diagnostic_score"],
        ),
        maximum_source_age_seconds=_decimal_from_payload(
            "maximum_source_age_seconds",
            payload["maximum_source_age_seconds"],
        ),
        reason_codes=_reason_codes_from_payload(payload["reason_codes"]),
        reason_code_counts=tuple(
            _reason_count_from_public_payload(value)
            for value in reason_counts_value
        ),
        rows=tuple(_row_from_public_payload(value) for value in rows_value),
        derived_validation_digest=_string_from_payload(
            DERIVED_VALIDATION_DIGEST_FIELD,
            payload[DERIVED_VALIDATION_DIGEST_FIELD],
        ),
        paper_only=_true_from_payload("paper_only", payload["paper_only"]),
        report_only=_true_from_payload("report_only", payload["report_only"]),
        readonly=_true_from_payload("readonly", payload["readonly"]),
    )


def _config_from_public_payload(
    value: object,
) -> ResearchStrategyEventSourceFreshnessQuorumConfig:
    if type(value) is not dict:
        raise ValueError("config must be a dict")
    _require_exact_schema("config payload", value, CONFIG_PAYLOAD_FIELDS)
    return ResearchStrategyEventSourceFreshnessQuorumConfig(
        config_version=_string_from_payload(
            "config_version",
            value["config_version"],
        ),
        freshness_watch_age_seconds=_decimal_from_payload(
            "freshness_watch_age_seconds",
            value["freshness_watch_age_seconds"],
        ),
        freshness_block_age_seconds=_decimal_from_payload(
            "freshness_block_age_seconds",
            value["freshness_block_age_seconds"],
        ),
        quorum_pass_threshold=_decimal_from_payload(
            "quorum_pass_threshold",
            value["quorum_pass_threshold"],
        ),
        quorum_block_threshold=_decimal_from_payload(
            "quorum_block_threshold",
            value["quorum_block_threshold"],
        ),
        independent_quorum_pass_threshold=_decimal_from_payload(
            "independent_quorum_pass_threshold",
            value["independent_quorum_pass_threshold"],
        ),
        independent_quorum_block_threshold=_decimal_from_payload(
            "independent_quorum_block_threshold",
            value["independent_quorum_block_threshold"],
        ),
        freshness_weight=_decimal_from_payload(
            "freshness_weight",
            value["freshness_weight"],
        ),
        evidence_quorum_weight=_decimal_from_payload(
            "evidence_quorum_weight",
            value["evidence_quorum_weight"],
        ),
        independent_quorum_weight=_decimal_from_payload(
            "independent_quorum_weight",
            value["independent_quorum_weight"],
        ),
        paper_only=_true_from_payload("paper_only", value["paper_only"]),
        report_only=_true_from_payload("report_only", value["report_only"]),
        readonly=_true_from_payload("readonly", value["readonly"]),
    )


def _row_from_public_payload(
    value: object,
) -> ResearchStrategyEventSourceFreshnessQuorumRow:
    if type(value) is not dict:
        raise ValueError("row must be a dict")
    _require_exact_schema("row payload", value, ROW_PAYLOAD_FIELDS)
    _reject_unsafe_public_payload("row payload", value)
    _validate_raw_digest(value, ROW_DIGEST_LABEL)
    return ResearchStrategyEventSourceFreshnessQuorumRow(
        config_version=_string_from_payload(
            "config_version",
            value["config_version"],
        ),
        review_rank=_decimal_from_payload("review_rank", value["review_rank"]),
        event_label=_string_from_payload("event_label", value["event_label"]),
        public_source_label=_string_from_payload(
            "public_source_label",
            value["public_source_label"],
        ),
        observed_at=_datetime_from_payload("observed_at", value["observed_at"]),
        evidence_count=_decimal_from_payload(
            "evidence_count",
            value["evidence_count"],
        ),
        required_evidence_count=_decimal_from_payload(
            "required_evidence_count",
            value["required_evidence_count"],
        ),
        independent_evidence_count=_decimal_from_payload(
            "independent_evidence_count",
            value["independent_evidence_count"],
        ),
        required_independent_evidence_count=_decimal_from_payload(
            "required_independent_evidence_count",
            value["required_independent_evidence_count"],
        ),
        source_age_seconds=_decimal_from_payload(
            "source_age_seconds",
            value["source_age_seconds"],
        ),
        freshness_score=_decimal_from_payload(
            "freshness_score",
            value["freshness_score"],
        ),
        evidence_quorum_score=_decimal_from_payload(
            "evidence_quorum_score",
            value["evidence_quorum_score"],
        ),
        independent_quorum_score=_decimal_from_payload(
            "independent_quorum_score",
            value["independent_quorum_score"],
        ),
        diagnostic_score=_decimal_from_payload(
            "diagnostic_score",
            value["diagnostic_score"],
        ),
        diagnostic_status=_string_from_payload(
            "diagnostic_status",
            value["diagnostic_status"],
        ),
        reason_codes=_reason_codes_from_payload(value["reason_codes"]),
        derived_validation_digest=_string_from_payload(
            DERIVED_VALIDATION_DIGEST_FIELD,
            value[DERIVED_VALIDATION_DIGEST_FIELD],
        ),
        paper_only=_true_from_payload("paper_only", value["paper_only"]),
        report_only=_true_from_payload("report_only", value["report_only"]),
        readonly=_true_from_payload("readonly", value["readonly"]),
    )


def _reason_count_from_public_payload(
    value: object,
) -> ResearchStrategyEventSourceFreshnessQuorumReasonCount:
    if type(value) is not dict:
        raise ValueError("reason count must be a dict")
    _require_exact_schema("reason count payload", value, REASON_COUNT_PAYLOAD_FIELDS)
    return ResearchStrategyEventSourceFreshnessQuorumReasonCount(
        reason_code=_string_from_payload("reason_code", value["reason_code"]),
        row_count=_decimal_from_payload("row_count", value["row_count"]),
        row_ratio=_decimal_from_payload("row_ratio", value["row_ratio"]),
        paper_only=_true_from_payload("paper_only", value["paper_only"]),
        report_only=_true_from_payload("report_only", value["report_only"]),
        readonly=_true_from_payload("readonly", value["readonly"]),
    )


def _validate_raw_digest(payload: dict[str, object], label: str) -> None:
    supplied = _require_sha256_digest(
        DERIVED_VALIDATION_DIGEST_FIELD,
        _string_from_payload(
            DERIVED_VALIDATION_DIGEST_FIELD,
            payload[DERIVED_VALIDATION_DIGEST_FIELD],
        ),
    )
    unsigned = {
        key: value
        for key, value in payload.items()
        if key != DERIVED_VALIDATION_DIGEST_FIELD
    }
    expected = _derived_validation_digest(label, unsigned)
    if supplied != expected:
        raise ValueError("derived_validation_digest must match public payload")


def _require_exact_schema(
    label: str,
    payload: dict[str, object],
    expected_fields: tuple[str, ...],
) -> None:
    if type(payload) is not dict:
        raise ValueError(f"{label} must be an exact dict")
    if any(type(key) is not str for key in payload):
        raise ValueError(f"{label} keys must be exact strings")
    if tuple(payload) != expected_fields:
        raise ValueError(
            f"{label} must use the exact schema and canonical field order",
        )


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} contains an unsafe key")
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
                raise ValueError(f"{label} contains an unsafe key")
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        lowered_value = value.lower()
        if any(
            fragment in lowered_value
            for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS
        ):
            raise ValueError(f"{label} contains an unsafe value")
        return
    if type(value) is bool:
        return
    raise ValueError(f"{label} contains a non-canonical public value")


def _normalize_config(
    config: object,
) -> ResearchStrategyEventSourceFreshnessQuorumConfig:
    _require_exact_type(
        "config",
        config,
        ResearchStrategyEventSourceFreshnessQuorumConfig,
    )
    return ResearchStrategyEventSourceFreshnessQuorumConfig(
        **{field.name: getattr(config, field.name) for field in fields(config)},
    )


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchStrategyEventSourceFreshnessQuorumObservation, ...]:
    if isinstance(observations, (str, bytes, bytearray, dict)):
        raise ValueError("observations must be an iterable of exact observations")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be iterable") from exc
    normalized: list[ResearchStrategyEventSourceFreshnessQuorumObservation] = []
    seen_keys: set[tuple[str, str]] = set()
    for value in values:
        _require_exact_type(
            "observation",
            value,
            ResearchStrategyEventSourceFreshnessQuorumObservation,
        )
        normalized_value = ResearchStrategyEventSourceFreshnessQuorumObservation(
            **{field.name: getattr(value, field.name) for field in fields(value)},
        )
        public_key = (
            normalized_value.event_label,
            normalized_value.public_source_label,
        )
        if public_key in seen_keys:
            raise ValueError("event and public source labels must be unique")
        seen_keys.add(public_key)
        normalized.append(normalized_value)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[ResearchStrategyEventSourceFreshnessQuorumRow, ...],
) -> tuple[ResearchStrategyEventSourceFreshnessQuorumRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be exactly tuple")
    normalized_rows: list[ResearchStrategyEventSourceFreshnessQuorumRow] = []
    for row in rows:
        _require_exact_type(
            "row",
            row,
            ResearchStrategyEventSourceFreshnessQuorumRow,
        )
        normalized_rows.append(
            ResearchStrategyEventSourceFreshnessQuorumRow(
                **{field.name: getattr(row, field.name) for field in fields(row)},
            ),
        )
    return tuple(normalized_rows)


def _normalize_reason_counts(
    values: tuple[ResearchStrategyEventSourceFreshnessQuorumReasonCount, ...],
) -> tuple[ResearchStrategyEventSourceFreshnessQuorumReasonCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be exactly tuple")
    normalized_values: list[
        ResearchStrategyEventSourceFreshnessQuorumReasonCount
    ] = []
    for value in values:
        _require_exact_type(
            "reason_count",
            value,
            ResearchStrategyEventSourceFreshnessQuorumReasonCount,
        )
        normalized_values.append(
            ResearchStrategyEventSourceFreshnessQuorumReasonCount(
                **{field.name: getattr(value, field.name) for field in fields(value)},
            ),
        )
    values = tuple(normalized_values)
    if tuple(item.reason_code for item in values) != tuple(
        reason_code
        for reason_code in REASON_CODES
        if any(item.reason_code == reason_code for item in values)
    ):
        raise ValueError("reason_code_counts must use stable reason order")
    return values


def _normalize_reason_codes(
    name: str,
    value: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be exactly tuple")
    if not value:
        raise ValueError(f"{name} must not be empty")
    if any(type(item) is not str for item in value):
        raise ValueError(f"{name} values must be exact strings")
    if len(set(value)) != len(value):
        raise ValueError(f"{name} must not contain duplicates")
    for item in value:
        _require_member(name, item, REASON_CODES)
    normalized = tuple(reason_code for reason_code in REASON_CODES if reason_code in value)
    if value != normalized:
        raise ValueError(f"{name} must use canonical order")
    return value


def _reason_codes_from_payload(value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError("reason_codes must be a list")
    if any(type(item) is not str for item in value):
        raise ValueError("reason_codes values must be exact strings")
    supplied = tuple(value)
    normalized = _normalize_reason_codes("reason_codes", supplied)
    if supplied != normalized:
        raise ValueError("reason_codes must use stable canonical order")
    return normalized


def _require_exact_type(name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_public_label(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be exactly str")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public text")
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a canonical public label")
    return value


def _require_private_identifier(value: object) -> str:
    if type(value) is not str:
        raise ValueError("private_source_identifier must be exactly str")
    if not value or len(value) > 1024 or any(ord(character) < 32 for character in value):
        raise ValueError("private_source_identifier must be nonempty private text")
    return value


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{name} {field_name} must be exactly True")


def _require_status(name: str, value: object) -> str:
    return _require_member(name, value, DIAGNOSTIC_STATUSES)


def _require_member(name: str, value: object, members: tuple[str, ...]) -> str:
    if type(value) is not str or value not in members:
        raise ValueError(f"{name} must be one of {members}")
    return value


def _require_decimal_raw(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{name} must not use signed zero")
    return value


def _require_probability_decimal_raw(name: str, value: object) -> Decimal:
    raw = _require_decimal_raw(name, value)
    if raw < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if raw > ONE:
        raise ValueError(f"{name} must be at most one")
    return raw


def _normalize_decimal(name: str, value: object) -> Decimal:
    return _quantize(_require_decimal_raw(name, value), name=name)


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    raw = _require_decimal_raw(name, value)
    if raw < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(raw, name=name)


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    raw = _require_decimal_raw(name, value)
    if raw <= ZERO:
        raise ValueError(f"{name} must be positive")
    normalized = _quantize(raw, name=name)
    if normalized <= ZERO:
        raise ValueError(f"{name} must remain positive after quantization")
    return normalized


def _normalize_probability_decimal(name: str, value: object) -> Decimal:
    return _quantize(_require_probability_decimal_raw(name, value), name=name)


def _normalize_nonnegative_whole_decimal(name: str, value: object) -> Decimal:
    raw = _require_decimal_raw(name, value)
    if raw < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT) as context:
        integral = raw.to_integral_value(context=context)
    if raw != integral:
        raise ValueError(f"{name} must be whole")
    return _quantize(raw, name=name)


def _normalize_positive_whole_decimal(name: str, value: object) -> Decimal:
    raw = _require_decimal_raw(name, value)
    if raw <= ZERO:
        raise ValueError(f"{name} must be positive")
    with localcontext(DECIMAL_CONTEXT) as context:
        integral = raw.to_integral_value(context=context)
    if raw != integral:
        raise ValueError(f"{name} must be whole")
    return _quantize(raw, name=name)


def _quantize(value: Decimal, *, name: str = "Decimal value") -> Decimal:
    raw = _require_decimal_raw(name, value)
    try:
        with localcontext(DECIMAL_CONTEXT) as context:
            normalized = raw.quantize(
                QUANTUM,
                rounding=ROUND_HALF_UP,
                context=context,
            )
    except DecimalException as exc:
        raise ValueError(f"{name} must be quantizable") from exc
    return ZERO if normalized.is_zero() else normalized


def _count(value: int) -> Decimal:
    if type(value) is not int or isinstance(value, bool) or value < 0:
        raise ValueError("count must be a nonnegative exact int")
    return _quantize(Decimal(value), name="count")


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    return _cap_probability(_ratio_raw(numerator, denominator))


def _ratio_raw(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return numerator / denominator


def _cap_probability(value: Decimal) -> Decimal:
    return _quantize(min(ONE, max(ZERO, value)))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            _sum_decimals(values) / _count(len(values)),
            name="average",
        )


def _minimum(values: tuple[Decimal, ...]) -> Decimal:
    return min(values, default=ZERO)


def _maximum(values: tuple[Decimal, ...]) -> Decimal:
    return max(values, default=ZERO)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{name} utcoffset must not be None")
    return value.astimezone(UTC)


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    if earlier > later:
        raise ValueError("observed_at must not be after generated_at")
    delta = later - earlier
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days * 86400 + delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECOND_DIVISOR)
        )
    return _normalize_nonnegative_decimal("source_age_seconds", seconds)


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = ZERO
        for value in values:
            total += _require_decimal_raw("Decimal sum value", value)
        return total


def _negate_decimal(value: Decimal) -> Decimal:
    raw = _require_decimal_raw("Decimal sort value", value)
    if raw.is_zero():
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return -raw


def _datetime_payload(value: datetime) -> str:
    return _as_utc("datetime", value).isoformat()


def _datetime_from_payload(name: str, value: object) -> datetime:
    text = _string_from_payload(name, value)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{name} must be a canonical datetime") from exc
    normalized = _as_utc(name, parsed)
    if _datetime_payload(normalized) != text:
        raise ValueError(f"{name} must be a canonical UTC datetime")
    return normalized


def _decimal_payload(value: Decimal) -> str:
    normalized = _normalize_nonnegative_decimal("payload decimal", value)
    return format(normalized, ".6f")


def _decimal_from_payload(name: str, value: object) -> Decimal:
    text = _string_from_payload(name, value)
    if not CANONICAL_NONNEGATIVE_DECIMAL_RE.fullmatch(text):
        raise ValueError(f"{name} must be a canonical nonnegative Decimal string")
    parsed = Decimal(text)
    if parsed.is_zero() and parsed.is_signed():
        raise ValueError(f"{name} must not use signed zero")
    normalized = _normalize_nonnegative_decimal(name, parsed)
    if _decimal_payload(normalized) != text:
        raise ValueError(f"{name} must be a canonical Decimal string")
    return normalized


def _string_from_payload(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be exactly str")
    return value


def _true_from_payload(name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{name} must be exactly True")
    return True


def _require_sha256_digest(name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    return value
