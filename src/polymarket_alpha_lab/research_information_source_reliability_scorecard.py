"""Pure paper-only source reliability scorecard reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_CONFIG_VERSION = "research-information-source-reliability-scorecard-v1"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("ready", "attention", "blocker")
STATUS_SORT_WEIGHT = {"blocker": 0, "attention": 1, "ready": 2}

PUBLIC_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "status",
    "source_count",
    "ready_count",
    "attention_count",
    "blocker_count",
    "attention_or_blocker_count",
    "average_reliability_score",
    "minimum_fetch_quality_score",
    "maximum_freshness_lag_seconds",
    "reason_code_counts",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
    "derived_validation_digest",
)
ROW_PAYLOAD_FIELDS = (
    "source_label",
    "official_source_score",
    "freshness_lag_seconds",
    "freshness_score",
    "independent_source_count",
    "independence_score",
    "conflict_signal_count",
    "conflict_score",
    "agent_reach_fetch_quality",
    "scrapling_fetch_quality",
    "fetch_quality_score",
    "reliability_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
    "derived_validation_digest",
)
REASON_COUNT_PAYLOAD_FIELDS = (
    "reason_code",
    "count",
    "source_ratio",
    "paper_only",
    "report_only",
    "readonly",
)

UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "raw-candidate",
    "raw candidate",
    "candidate_id",
    "candidate-",
    "market_id",
    "market-id",
    "market id",
    "market_slug",
    "market slug",
    "source_url",
    "source-url",
    "source url",
    "source_text",
    "source-text",
    "source text",
    "raw_url",
    "raw text",
    "http://",
    "https://",
    "www.",
    "dsn",
    "table",
    "token",
    "buy",
    "sell",
    "recommend",
    "quest" + "ion",
    "wall" + "et",
    "or" + "der",
    "tra" + "de",
    "pos" + "ition",
)

__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "ResearchInformationSourceReliabilityReasonCodeCount",
    "ResearchInformationSourceReliabilityRow",
    "ResearchInformationSourceReliabilityScorecardConfig",
    "ResearchInformationSourceReliabilityScorecardInput",
    "ResearchInformationSourceReliabilityScorecardReport",
    "STATUSES",
    "build_research_information_source_reliability_scorecard",
    "research_information_source_reliability_scorecard_payload",
    "validate_research_information_source_reliability_scorecard_payload",
)


@dataclass(frozen=True)
class ResearchInformationSourceReliabilityScorecardConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    ready_official_source_score: Decimal = Decimal("0.800000")
    attention_official_source_score: Decimal = Decimal("0.500000")
    ready_freshness_lag_seconds: Decimal = Decimal("3600.000000")
    blocker_freshness_lag_seconds: Decimal = Decimal("172800.000000")
    ready_independent_source_count: Decimal = Decimal("3.000000")
    attention_independent_source_count: Decimal = Decimal("2.000000")
    attention_conflict_signal_count: Decimal = Decimal("1.000000")
    blocker_conflict_signal_count: Decimal = Decimal("3.000000")
    ready_fetch_quality: Decimal = Decimal("0.800000")
    blocker_fetch_quality: Decimal = Decimal("0.500000")
    ready_reliability_score: Decimal = Decimal("0.800000")
    attention_reliability_score: Decimal = Decimal("0.600000")
    official_weight: Decimal = Decimal("0.200000")
    freshness_weight: Decimal = Decimal("0.200000")
    independence_weight: Decimal = Decimal("0.200000")
    conflict_weight: Decimal = Decimal("0.200000")
    fetch_quality_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchInformationSourceReliabilityScorecardConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchInformationSourceReliabilityScorecardConfig, "config")
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "ready_official_source_score",
            "attention_official_source_score",
            "ready_fetch_quality",
            "blocker_fetch_quality",
            "ready_reliability_score",
            "attention_reliability_score",
            "official_weight",
            "freshness_weight",
            "independence_weight",
            "conflict_weight",
            "fetch_quality_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "ready_freshness_lag_seconds",
            "blocker_freshness_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "ready_independent_source_count",
            "attention_independent_source_count",
            "attention_conflict_signal_count",
            "blocker_conflict_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.ready_official_source_score <= self.attention_official_source_score:
            raise ValueError(
                "ready_official_source_score must exceed attention_official_source_score",
            )
        if self.ready_freshness_lag_seconds >= self.blocker_freshness_lag_seconds:
            raise ValueError(
                "ready_freshness_lag_seconds must be below blocker_freshness_lag_seconds",
            )
        if self.ready_independent_source_count < self.attention_independent_source_count:
            raise ValueError(
                "ready_independent_source_count must not be below "
                "attention_independent_source_count",
            )
        if self.attention_conflict_signal_count > self.blocker_conflict_signal_count:
            raise ValueError(
                "attention_conflict_signal_count must not exceed "
                "blocker_conflict_signal_count",
            )
        if self.blocker_fetch_quality > self.ready_fetch_quality:
            raise ValueError("blocker_fetch_quality must not exceed ready_fetch_quality")
        if self.ready_reliability_score <= self.attention_reliability_score:
            raise ValueError("ready_reliability_score must exceed attention_reliability_score")
        weight_sum = _quantize(
            self.official_weight
            + self.freshness_weight
            + self.independence_weight
            + self.conflict_weight
            + self.fetch_quality_weight,
        )
        if weight_sum != ONE:
            raise ValueError("component weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchInformationSourceReliabilityScorecardInput:
    public_source_label: str
    official_source_score: Decimal
    freshness_lag_seconds: Decimal
    independent_source_count: Decimal
    conflict_signal_count: Decimal
    agent_reach_fetch_quality: Decimal
    scrapling_fetch_quality: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchInformationSourceReliabilityScorecardInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchInformationSourceReliabilityScorecardInput, "input")
        object.__setattr__(
            self,
            "public_source_label",
            _normalize_public_label("public_source_label", self.public_source_label),
        )
        object.__setattr__(
            self,
            "official_source_score",
            _normalize_ratio_decimal("official_source_score", self.official_source_score),
        )
        object.__setattr__(
            self,
            "freshness_lag_seconds",
            _normalize_nonnegative_decimal("freshness_lag_seconds", self.freshness_lag_seconds),
        )
        for field_name in ("independent_source_count", "conflict_signal_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("agent_reach_fetch_quality", "scrapling_fetch_quality"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchInformationSourceReliabilityRow:
    source_label: str
    official_source_score: Decimal
    freshness_lag_seconds: Decimal
    freshness_score: Decimal
    independent_source_count: Decimal
    independence_score: Decimal
    conflict_signal_count: Decimal
    conflict_score: Decimal
    agent_reach_fetch_quality: Decimal
    scrapling_fetch_quality: Decimal
    fetch_quality_score: Decimal
    reliability_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchInformationSourceReliabilityRow does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchInformationSourceReliabilityRow, "row")
        object.__setattr__(
            self,
            "source_label",
            _normalize_public_label("source_label", self.source_label),
        )
        for field_name in (
            "official_source_score",
            "freshness_score",
            "independence_score",
            "conflict_score",
            "agent_reach_fetch_quality",
            "scrapling_fetch_quality",
            "fetch_quality_score",
            "reliability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "freshness_lag_seconds",
            _normalize_nonnegative_decimal("freshness_lag_seconds", self.freshness_lag_seconds),
        )
        for field_name in ("independent_source_count", "conflict_signal_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest("derived_validation_digest", self.derived_validation_digest),
            )
        _validate_row(self)


@dataclass(frozen=True)
class ResearchInformationSourceReliabilityReasonCodeCount:
    reason_code: str
    count: Decimal
    source_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchInformationSourceReliabilityReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchInformationSourceReliabilityReasonCodeCount, "count")
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "source_ratio",
            _normalize_ratio_decimal("source_ratio", self.source_ratio),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchInformationSourceReliabilityScorecardReport:
    generated_at: datetime
    config_version: str
    status: str
    source_count: Decimal
    ready_count: Decimal
    attention_count: Decimal
    blocker_count: Decimal
    attention_or_blocker_count: Decimal
    average_reliability_score: Decimal | None
    minimum_fetch_quality_score: Decimal | None
    maximum_freshness_lag_seconds: Decimal
    reason_code_counts: tuple[ResearchInformationSourceReliabilityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchInformationSourceReliabilityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchInformationSourceReliabilityScorecardReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchInformationSourceReliabilityScorecardReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_member("status", self.status, STATUSES)
        for field_name in (
            "source_count",
            "ready_count",
            "attention_count",
            "blocker_count",
            "attention_or_blocker_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_reliability_score", "minimum_fetch_quality_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "maximum_freshness_lag_seconds",
            _normalize_nonnegative_decimal(
                "maximum_freshness_lag_seconds",
                self.maximum_freshness_lag_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest("derived_validation_digest", self.derived_validation_digest),
            )
        _validate_report(self)


def build_research_information_source_reliability_scorecard(
    source_rows: Iterable[object],
    *,
    config: ResearchInformationSourceReliabilityScorecardConfig,
    generated_at: datetime,
) -> ResearchInformationSourceReliabilityScorecardReport:
    if type(config) is not ResearchInformationSourceReliabilityScorecardConfig:
        raise ValueError("config must be a ResearchInformationSourceReliabilityScorecardConfig")
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(source_rows)
    rows = tuple(sorted((_row_from_input(item, config=config) for item in inputs), key=_row_key))
    reason_codes = _report_reason_codes(rows)
    return ResearchInformationSourceReliabilityScorecardReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        source_count=_decimal_count(len(rows)),
        ready_count=_status_count(rows, "ready"),
        attention_count=_status_count(rows, "attention"),
        blocker_count=_status_count(rows, "blocker"),
        attention_or_blocker_count=_status_count(rows, "attention")
        + _status_count(rows, "blocker"),
        average_reliability_score=_average(row.reliability_score for row in rows),
        minimum_fetch_quality_score=_min_decimal(
            (row.fetch_quality_score for row in rows),
            default=None,
        ),
        maximum_freshness_lag_seconds=_max_decimal(
            (row.freshness_lag_seconds for row in rows),
            default=ZERO,
        ),
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
        rows=rows,
    )


def research_information_source_reliability_scorecard_payload(
    value: ResearchInformationSourceReliabilityScorecardReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is dict:
        _reject_unsafe_public_payload("public payload", value)
        validate_research_information_source_reliability_scorecard_payload(value)
        return dict(value)
    if type(value) is not ResearchInformationSourceReliabilityScorecardReport:
        raise ValueError("value must be a scorecard report")
    _require_hard_flags("report", value)
    _validate_report(value)
    payload = _report_payload_without_digest(value)
    payload["derived_validation_digest"] = value.derived_validation_digest
    validate_research_information_source_reliability_scorecard_payload(payload)
    return payload


def validate_research_information_source_reliability_scorecard_payload(
    payload: object,
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload)
    _require_exact_keys("payload", payload, PUBLIC_PAYLOAD_FIELDS)
    _require_public_datetime_string("generated_at", payload["generated_at"])
    _require_public_string("config_version", payload["config_version"])
    _require_member("status", payload["status"], STATUSES)
    for field_name in (
        "source_count",
        "ready_count",
        "attention_count",
        "blocker_count",
        "attention_or_blocker_count",
    ):
        _decimal_from_payload_string(field_name, payload[field_name], require_integral=True)
    for field_name in (
        "average_reliability_score",
        "minimum_fetch_quality_score",
    ):
        if payload[field_name] is not None:
            _decimal_from_payload_string(field_name, payload[field_name])
    _decimal_from_payload_string("maximum_freshness_lag_seconds", payload["maximum_freshness_lag_seconds"])
    _validate_payload_reason_code_counts(payload["reason_code_counts"])
    _normalize_reason_codes("reason_codes", tuple(payload["reason_codes"]), allow_empty=False)
    _validate_payload_rows(payload["rows"])
    _require_payload_hard_flags("payload", payload)
    _validate_payload_consistency(payload)
    expected = _payload_digest(
        {field_name: payload[field_name] for field_name in PUBLIC_PAYLOAD_FIELDS[:-1]},
    )
    if payload["derived_validation_digest"] != expected:
        raise ValueError("derived_validation_digest must match payload fields")
    return True


def _row_from_input(
    source_row: ResearchInformationSourceReliabilityScorecardInput,
    *,
    config: ResearchInformationSourceReliabilityScorecardConfig,
) -> ResearchInformationSourceReliabilityRow:
    freshness_score = _freshness_score(source_row.freshness_lag_seconds, config=config)
    independence_score = _safe_ratio(
        source_row.independent_source_count,
        config.ready_independent_source_count,
    )
    conflict_score = _conflict_score(source_row.conflict_signal_count, config=config)
    fetch_quality_score = min(
        source_row.agent_reach_fetch_quality,
        source_row.scrapling_fetch_quality,
    )
    reliability_score = _quantize(
        (source_row.official_source_score * config.official_weight)
        + (freshness_score * config.freshness_weight)
        + (independence_score * config.independence_weight)
        + (conflict_score * config.conflict_weight)
        + (fetch_quality_score * config.fetch_quality_weight),
    )
    status = _status_for_source(
        source_row,
        fetch_quality_score=fetch_quality_score,
        reliability_score=reliability_score,
        config=config,
    )
    reason_codes = _reason_codes_for_source(
        source_row,
        status=status,
        fetch_quality_score=fetch_quality_score,
        config=config,
    )
    return ResearchInformationSourceReliabilityRow(
        source_label=source_row.public_source_label,
        official_source_score=source_row.official_source_score,
        freshness_lag_seconds=source_row.freshness_lag_seconds,
        freshness_score=freshness_score,
        independent_source_count=source_row.independent_source_count,
        independence_score=independence_score,
        conflict_signal_count=source_row.conflict_signal_count,
        conflict_score=conflict_score,
        agent_reach_fetch_quality=source_row.agent_reach_fetch_quality,
        scrapling_fetch_quality=source_row.scrapling_fetch_quality,
        fetch_quality_score=fetch_quality_score,
        reliability_score=reliability_score,
        status=status,
        reason_codes=reason_codes,
    )


def _status_for_source(
    source_row: ResearchInformationSourceReliabilityScorecardInput,
    *,
    fetch_quality_score: Decimal,
    reliability_score: Decimal,
    config: ResearchInformationSourceReliabilityScorecardConfig,
) -> str:
    if source_row.official_source_score < config.attention_official_source_score:
        return "blocker"
    if source_row.freshness_lag_seconds >= config.blocker_freshness_lag_seconds:
        return "blocker"
    if source_row.independent_source_count < config.attention_independent_source_count:
        return "blocker"
    if source_row.conflict_signal_count >= config.blocker_conflict_signal_count:
        return "blocker"
    if fetch_quality_score < config.blocker_fetch_quality:
        return "blocker"
    if reliability_score < config.attention_reliability_score:
        return "blocker"
    if source_row.official_source_score < config.ready_official_source_score:
        return "attention"
    if source_row.freshness_lag_seconds > config.ready_freshness_lag_seconds:
        return "attention"
    if source_row.independent_source_count < config.ready_independent_source_count:
        return "attention"
    if source_row.conflict_signal_count >= config.attention_conflict_signal_count:
        return "attention"
    if fetch_quality_score < config.ready_fetch_quality:
        return "attention"
    if reliability_score < config.ready_reliability_score:
        return "attention"
    return "ready"


def _reason_codes_for_source(
    source_row: ResearchInformationSourceReliabilityScorecardInput,
    *,
    status: str,
    fetch_quality_score: Decimal,
    config: ResearchInformationSourceReliabilityScorecardConfig,
) -> tuple[str, ...]:
    reasons: list[str] = [
        _threshold_reason(
            "official_source",
            source_row.official_source_score,
            ready_floor=config.ready_official_source_score,
            attention_floor=config.attention_official_source_score,
        ),
        _freshness_reason(source_row.freshness_lag_seconds, config=config),
        _independence_reason(source_row.independent_source_count, config=config),
        _conflict_reason(source_row.conflict_signal_count, config=config),
        _fetch_reason(
            "agent_reach_fetch_quality",
            source_row.agent_reach_fetch_quality,
            config=config,
        ),
        _fetch_reason(
            "scrapling_fetch_quality",
            source_row.scrapling_fetch_quality,
            config=config,
        ),
        f"source_reliability_{status}",
    ]
    for reason_code in source_row.reason_codes:
        reasons.append(f"input_{reason_code}")
    return tuple(sorted(reasons))


def _threshold_reason(
    prefix: str,
    value: Decimal,
    *,
    ready_floor: Decimal,
    attention_floor: Decimal,
) -> str:
    if value >= ready_floor:
        return f"{prefix}_ready"
    if value >= attention_floor:
        return f"{prefix}_attention"
    return f"{prefix}_blocker"


def _freshness_reason(
    freshness_lag_seconds: Decimal,
    *,
    config: ResearchInformationSourceReliabilityScorecardConfig,
) -> str:
    if freshness_lag_seconds <= config.ready_freshness_lag_seconds:
        return "freshness_ready"
    if freshness_lag_seconds < config.blocker_freshness_lag_seconds:
        return "freshness_attention"
    return "freshness_blocker"


def _independence_reason(
    independent_source_count: Decimal,
    *,
    config: ResearchInformationSourceReliabilityScorecardConfig,
) -> str:
    if independent_source_count >= config.ready_independent_source_count:
        return "independent_sources_ready"
    if independent_source_count >= config.attention_independent_source_count:
        return "independent_sources_attention"
    return "independent_sources_blocker"


def _conflict_reason(
    conflict_signal_count: Decimal,
    *,
    config: ResearchInformationSourceReliabilityScorecardConfig,
) -> str:
    if conflict_signal_count >= config.blocker_conflict_signal_count:
        return "conflict_signals_blocker"
    if conflict_signal_count >= config.attention_conflict_signal_count:
        return "conflict_signals_attention"
    return "conflict_signals_ready"


def _fetch_reason(
    prefix: str,
    quality: Decimal,
    *,
    config: ResearchInformationSourceReliabilityScorecardConfig,
) -> str:
    if quality >= config.ready_fetch_quality:
        return f"{prefix}_ready"
    if quality >= config.blocker_fetch_quality:
        return f"{prefix}_attention"
    return f"{prefix}_blocker"


def _freshness_score(
    freshness_lag_seconds: Decimal,
    *,
    config: ResearchInformationSourceReliabilityScorecardConfig,
) -> Decimal:
    if freshness_lag_seconds <= config.ready_freshness_lag_seconds:
        return ONE
    if freshness_lag_seconds >= config.blocker_freshness_lag_seconds:
        return ZERO
    span = config.blocker_freshness_lag_seconds - config.ready_freshness_lag_seconds
    excess = freshness_lag_seconds - config.ready_freshness_lag_seconds
    return _quantize(ONE - _safe_ratio(excess, span))


def _conflict_score(
    conflict_signal_count: Decimal,
    *,
    config: ResearchInformationSourceReliabilityScorecardConfig,
) -> Decimal:
    if conflict_signal_count >= config.blocker_conflict_signal_count:
        return ZERO
    return _quantize(ONE - _safe_ratio(conflict_signal_count, config.blocker_conflict_signal_count))


def _normalize_inputs(
    source_rows: Iterable[object],
) -> tuple[ResearchInformationSourceReliabilityScorecardInput, ...]:
    if isinstance(source_rows, (str, bytes)):
        raise ValueError("source_rows must be an iterable")
    try:
        values = tuple(source_rows)
    except TypeError as exc:
        raise ValueError("source_rows must be an iterable") from exc
    return tuple(_coerce_input(value) for value in values)


def _coerce_input(value: object) -> ResearchInformationSourceReliabilityScorecardInput:
    if type(value) is ResearchInformationSourceReliabilityScorecardInput:
        _require_hard_flags("input", value)
        _reject_unsafe_public_payload("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchInformationSourceReliabilityScorecardInput(
        public_source_label=_field_value(value, "public_source_label"),
        official_source_score=_field_value(value, "official_source_score"),
        freshness_lag_seconds=_field_value(value, "freshness_lag_seconds"),
        independent_source_count=_field_value(value, "independent_source_count"),
        conflict_signal_count=_field_value(value, "conflict_signal_count"),
        agent_reach_fetch_quality=_field_value(value, "agent_reach_fetch_quality"),
        scrapling_fetch_quality=_field_value(value, "scrapling_fetch_quality"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _field_value(value: object, field_name: str, *, default: object = None) -> object:
    has_default = default is not None
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if has_default:
        return default
    raise ValueError(f"{field_name} is required")


def _report_status(rows: tuple[ResearchInformationSourceReliabilityRow, ...]) -> str:
    if not rows:
        return "blocker"
    if any(row.status == "blocker" for row in rows):
        return "blocker"
    if any(row.status == "attention" for row in rows):
        return "attention"
    return "ready"


def _report_reason_codes(
    rows: tuple[ResearchInformationSourceReliabilityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("source_reliability_no_inputs",)
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchInformationSourceReliabilityRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchInformationSourceReliabilityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchInformationSourceReliabilityReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
                source_ratio=ONE,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    source_count = _decimal_count(len(rows))
    return tuple(
        ResearchInformationSourceReliabilityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
            source_ratio=_safe_ratio(_decimal_count(counter[reason_code]), source_count),
        )
        for reason_code in sorted(counter)
    )


def _row_key(row: ResearchInformationSourceReliabilityRow) -> tuple[int, Decimal, str]:
    return (STATUS_SORT_WEIGHT[row.status], row.reliability_score, row.source_label)


def _status_count(
    rows: tuple[ResearchInformationSourceReliabilityRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _average(values: Iterable[Decimal]) -> Decimal | None:
    values_tuple = tuple(values)
    if not values_tuple:
        return None
    return _safe_ratio(_sum_decimals(values_tuple), _decimal_count(len(values_tuple)))


def _sum_decimals(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _min_decimal(values: Iterable[Decimal], *, default: Decimal | None) -> Decimal | None:
    values_tuple = tuple(values)
    if not values_tuple:
        return default
    return min(values_tuple)


def _max_decimal(values: Iterable[Decimal], *, default: Decimal) -> Decimal:
    values_tuple = tuple(values)
    if not values_tuple:
        return default
    return max(values_tuple)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO
    return _quantize(min(ONE, max(ZERO, numerator / denominator)))


def _normalize_rows(
    rows: tuple[ResearchInformationSourceReliabilityRow, ...],
) -> tuple[ResearchInformationSourceReliabilityRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchInformationSourceReliabilityRow:
            raise ValueError("rows must contain ResearchInformationSourceReliabilityRow values")
        _require_hard_flags("row", row)
        _validate_row(row)
    sorted_rows = tuple(sorted(rows, key=_row_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by reliability priority")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchInformationSourceReliabilityReasonCodeCount, ...],
) -> tuple[ResearchInformationSourceReliabilityReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchInformationSourceReliabilityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchInformationSourceReliabilityReasonCodeCount values",
            )
        _require_hard_flags("reason code count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row(row: ResearchInformationSourceReliabilityRow) -> None:
    if row.fetch_quality_score != min(row.agent_reach_fetch_quality, row.scrapling_fetch_quality):
        raise ValueError("fetch_quality_score must match fetch quality inputs")
    if f"source_reliability_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must match row status")
    if row.status == "ready" and row.reliability_score < Decimal("0.800000"):
        raise ValueError("reliability_score must support ready status")
    if row.status == "attention" and row.reliability_score < Decimal("0.600000"):
        raise ValueError("reliability_score must support attention status")


def _validate_report(report: ResearchInformationSourceReliabilityScorecardReport) -> None:
    if report.source_count != _decimal_count(len(report.rows)):
        raise ValueError("source_count must match rows")
    if report.ready_count != _status_count(report.rows, "ready"):
        raise ValueError("ready_count must match rows")
    if report.attention_count != _status_count(report.rows, "attention"):
        raise ValueError("attention_count must match rows")
    if report.blocker_count != _status_count(report.rows, "blocker"):
        raise ValueError("blocker_count must match rows")
    if report.attention_or_blocker_count != report.attention_count + report.blocker_count:
        raise ValueError("attention_or_blocker_count must match rows")
    if report.average_reliability_score != _average(row.reliability_score for row in report.rows):
        raise ValueError("average_reliability_score must match rows")
    if report.minimum_fetch_quality_score != _min_decimal(
        (row.fetch_quality_score for row in report.rows),
        default=None,
    ):
        raise ValueError("minimum_fetch_quality_score must match rows")
    if report.maximum_freshness_lag_seconds != _max_decimal(
        (row.freshness_lag_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("maximum_freshness_lag_seconds must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _report_payload_without_digest(
    report: ResearchInformationSourceReliabilityScorecardReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "status": report.status,
        "source_count": str(report.source_count),
        "ready_count": str(report.ready_count),
        "attention_count": str(report.attention_count),
        "blocker_count": str(report.blocker_count),
        "attention_or_blocker_count": str(report.attention_or_blocker_count),
        "average_reliability_score": _optional_decimal_string(report.average_reliability_score),
        "minimum_fetch_quality_score": _optional_decimal_string(report.minimum_fetch_quality_score),
        "maximum_freshness_lag_seconds": str(report.maximum_freshness_lag_seconds),
        "reason_code_counts": [
            _reason_code_count_payload(count) for count in report.reason_code_counts
        ],
        "reason_codes": list(report.reason_codes),
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_payload(row: ResearchInformationSourceReliabilityRow) -> dict[str, Any]:
    return {
        "source_label": row.source_label,
        "official_source_score": str(row.official_source_score),
        "freshness_lag_seconds": str(row.freshness_lag_seconds),
        "freshness_score": str(row.freshness_score),
        "independent_source_count": str(row.independent_source_count),
        "independence_score": str(row.independence_score),
        "conflict_signal_count": str(row.conflict_signal_count),
        "conflict_score": str(row.conflict_score),
        "agent_reach_fetch_quality": str(row.agent_reach_fetch_quality),
        "scrapling_fetch_quality": str(row.scrapling_fetch_quality),
        "fetch_quality_score": str(row.fetch_quality_score),
        "reliability_score": str(row.reliability_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
        "derived_validation_digest": row.derived_validation_digest,
    }


def _reason_code_count_payload(
    count: ResearchInformationSourceReliabilityReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": count.reason_code,
        "count": str(count.count),
        "source_ratio": str(count.source_ratio),
        "paper_only": count.paper_only,
        "report_only": count.report_only,
        "readonly": count.readonly,
    }


def _optional_decimal_string(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _row_digest(row: ResearchInformationSourceReliabilityRow) -> str:
    payload = _row_payload_without_digest(row)
    return _payload_digest(payload)


def _report_digest(report: ResearchInformationSourceReliabilityScorecardReport) -> str:
    return _payload_digest(_report_payload_without_digest(report))


def _row_payload_without_digest(row: ResearchInformationSourceReliabilityRow) -> dict[str, Any]:
    payload = _row_payload(row)
    payload.pop("derived_validation_digest")
    return payload


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _validate_payload_rows(rows: object) -> None:
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        _require_exact_keys("row", row, ROW_PAYLOAD_FIELDS)
        _normalize_public_label("source_label", row["source_label"])
        for field_name in (
            "official_source_score",
            "freshness_score",
            "independence_score",
            "conflict_score",
            "agent_reach_fetch_quality",
            "scrapling_fetch_quality",
            "fetch_quality_score",
            "reliability_score",
        ):
            _decimal_from_payload_string(field_name, row[field_name])
        _decimal_from_payload_string("freshness_lag_seconds", row["freshness_lag_seconds"])
        for field_name in ("independent_source_count", "conflict_signal_count"):
            _decimal_from_payload_string(field_name, row[field_name], require_integral=True)
        _require_member("status", row["status"], STATUSES)
        _normalize_reason_codes("reason_codes", tuple(row["reason_codes"]), allow_empty=False)
        _require_payload_hard_flags("row", row)
        expected = _payload_digest(
            {field_name: row[field_name] for field_name in ROW_PAYLOAD_FIELDS[:-1]},
        )
        if row["derived_validation_digest"] != expected:
            raise ValueError("row derived_validation_digest must match row fields")


def _validate_payload_reason_code_counts(counts: object) -> None:
    if type(counts) is not list:
        raise ValueError("reason_code_counts must be a list")
    for count in counts:
        if type(count) is not dict:
            raise ValueError("reason_code_counts must contain JSON objects")
        _require_exact_keys("reason_code_count", count, REASON_COUNT_PAYLOAD_FIELDS)
        _require_reason_code("reason_code", count["reason_code"])
        _decimal_from_payload_string("count", count["count"], require_integral=True)
        _decimal_from_payload_string("source_ratio", count["source_ratio"])
        _require_payload_hard_flags("reason_code_count", count)


def _validate_payload_consistency(payload: dict[str, Any]) -> None:
    rows = payload["rows"]
    ready_count = sum(1 for row in rows if row["status"] == "ready")
    attention_count = sum(1 for row in rows if row["status"] == "attention")
    blocker_count = sum(1 for row in rows if row["status"] == "blocker")
    if payload["source_count"] != str(_decimal_count(len(rows))):
        raise ValueError("source_count must match rows")
    if payload["ready_count"] != str(_decimal_count(ready_count)):
        raise ValueError("ready_count must match rows")
    if payload["attention_count"] != str(_decimal_count(attention_count)):
        raise ValueError("attention_count must match rows")
    if payload["blocker_count"] != str(_decimal_count(blocker_count)):
        raise ValueError("blocker_count must match rows")
    expected_attention = _decimal_count(attention_count + blocker_count)
    if payload["attention_or_blocker_count"] != str(expected_attention):
        raise ValueError("attention_or_blocker_count must match rows")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public string")
    _assert_no_private_fragments(field_name, value)
    return value


def _normalize_public_label(field_name: str, value: object) -> str:
    text = _require_public_string(field_name, value)
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_-"
    if any(character not in allowed for character in text):
        raise ValueError(f"{field_name} must contain public safe characters")
    return text


def _require_reason_code(field_name: str, value: object) -> str:
    return _normalize_public_label(field_name, value)


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = tuple(_require_reason_code(field_name, value) for value in values)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{field_name} must not contain duplicates")
    if normalized != tuple(sorted(normalized)):
        normalized = tuple(sorted(normalized))
    return normalized


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be one of {members}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _normalize_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be in the closed unit interval")
    return _quantize(normalized)


def _normalize_optional_ratio_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_ratio_decimal(field_name, value)


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(normalized)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(normalized)


def _normalize_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return _quantize(normalized)


def _normalize_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return Decimal(value).quantize(QUANTUM)


def _decimal_from_payload_string(
    field_name: str,
    value: object,
    *,
    require_integral: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a decimal string") from exc
    normalized = _normalize_nonnegative_decimal(field_name, parsed)
    if require_integral and normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_public_datetime_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    _as_utc(field_name, parsed)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, field_name) or type(getattr(value, field_name)) is not bool:
            raise ValueError(f"{label} {field_name} must be a bool")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_payload_hard_flags(label: str, payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _assert_no_private_fragments(field_name: str, value: str) -> None:
    lowered = value.casefold()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains protected public material")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(f"{label}.{field.name}", field.name)
            _reject_unsafe_public_payload(f"{label}.{field.name}", getattr(value, field.name))
        return
    if type(value) is dict:
        for key, item in value.items():
            _reject_unsafe_public_payload(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        try:
            _assert_no_private_fragments(label, value)
        except ValueError as exc:
            raise ValueError(f"{label} contains unsafe public material") from exc


def _require_exact_keys(label: str, payload: dict[str, Any], expected: tuple[str, ...]) -> None:
    if tuple(payload.keys()) != expected:
        raise ValueError(f"{label} must contain exact public keys")


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    allowed = set("0123456789abcdef")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (+value).quantize(QUANTUM)
