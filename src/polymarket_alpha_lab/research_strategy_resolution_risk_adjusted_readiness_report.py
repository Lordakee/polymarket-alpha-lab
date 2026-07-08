"""Pure report-only strategy resolution-risk adjusted readiness snapshot."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any, Iterable, Mapping, Sequence


DEFAULT_RESEARCH_STRATEGY_RESOLUTION_RISK_ADJUSTED_READINESS_CONFIG_VERSION = (
    "research-strategy-resolution-risk-adjusted-readiness-report-v1"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_FOUR = Decimal("4.000000")
_STATUS_VALUES = frozenset((PASS_STATUS, WATCH_STATUS, BLOCK_STATUS))
_PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_ADEQUACY_FIELDS = (
    "settlement_clarity_score",
    "quorum_score",
    "contradiction_relief_score",
    "event_timing_score",
)
_UNSAFE_KEY_FRAGMENTS = (
    "raw",
    "candidate",
    "market_" "id",
    "market_" "slug",
    "slug",
    "question",
    "url",
    "source_" "text",
    "dsn",
    "table",
    "token",
    "private",
    "au" "th",
    "wal" "let",
    "net" "work",
    "data" "base",
    "or" "der",
    "b" "uy",
    "se" "ll",
    "tr" "ade",
    "position",
    "re" "commend",
    "siz" "ing",
    "li" "ve",
)
_UNSAFE_VALUE_FRAGMENTS = (
    "://",
    "www.",
    "raw",
    "candidate",
    "market_" "id",
    "market_" "slug",
    "slug",
    "question",
    "url",
    "source_" "text",
    "dsn",
    "table",
    "token",
    "private",
    "au" "th",
    "wal" "let",
    "net" "work",
    "data" "base",
    "or" "der",
    "b" "uy",
    "se" "ll",
    "tr" "ade",
    "position",
    "re" "commend",
    "siz" "ing",
    "li" "ve",
)


@dataclass(frozen=True)
class ResearchStrategyResolutionRiskAdjustedReadinessConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_RESOLUTION_RISK_ADJUSTED_READINESS_CONFIG_VERSION
    )
    pass_component_score: Decimal = Decimal("0.700000")
    watch_component_score: Decimal = Decimal("0.400000")
    pass_readiness_score: Decimal = Decimal("0.750000")
    watch_readiness_score: Decimal = Decimal("0.500000")
    watch_contradiction_pressure: Decimal = Decimal("0.300000")
    block_contradiction_pressure: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyResolutionRiskAdjustedReadinessConfig:
            raise TypeError(
                "ResearchStrategyResolutionRiskAdjustedReadinessConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyResolutionRiskAdjustedReadinessConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchStrategyResolutionRiskAdjustedReadinessConfig",
            )
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_RESOLUTION_RISK_ADJUSTED_READINESS_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_component_score",
            "watch_component_score",
            "pass_readiness_score",
            "watch_readiness_score",
            "watch_contradiction_pressure",
            "block_contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_component_score <= self.watch_component_score:
            raise ValueError("pass_component_score must exceed watch_component_score")
        if self.pass_readiness_score <= self.watch_readiness_score:
            raise ValueError("pass_readiness_score must exceed watch_readiness_score")
        if self.block_contradiction_pressure <= self.watch_contradiction_pressure:
            raise ValueError(
                "block_contradiction_pressure must exceed "
                "watch_contradiction_pressure",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyResolutionRiskAdjustedReadinessInput:
    review_packet_label: str
    settlement_clarity_score: Decimal
    quorum_score: Decimal
    contradiction_pressure_score: Decimal
    event_timing_score: Decimal
    risk_adjustment_quality: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyResolutionRiskAdjustedReadinessInput:
            raise TypeError(
                "ResearchStrategyResolutionRiskAdjustedReadinessInput "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyResolutionRiskAdjustedReadinessInput:
            raise ValueError(
                "input must be exactly "
                "ResearchStrategyResolutionRiskAdjustedReadinessInput",
            )
        _require_public_label("review_packet_label", self.review_packet_label)
        for field_name in (
            "settlement_clarity_score",
            "quorum_score",
            "contradiction_pressure_score",
            "event_timing_score",
            "risk_adjustment_quality",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchStrategyResolutionRiskAdjustedReadinessRow:
    review_packet_label: str
    settlement_clarity_score: Decimal
    quorum_score: Decimal
    contradiction_pressure_score: Decimal
    contradiction_relief_score: Decimal
    event_timing_score: Decimal
    risk_adjustment_quality: Decimal
    adjusted_readiness_score: Decimal
    lowest_adequacy_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyResolutionRiskAdjustedReadinessRow:
            raise TypeError(
                "ResearchStrategyResolutionRiskAdjustedReadinessRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyResolutionRiskAdjustedReadinessRow:
            raise ValueError(
                "row must be exactly ResearchStrategyResolutionRiskAdjustedReadinessRow",
            )
        _require_public_label("review_packet_label", self.review_packet_label)
        for field_name in (
            "settlement_clarity_score",
            "quorum_score",
            "contradiction_pressure_score",
            "contradiction_relief_score",
            "event_timing_score",
            "risk_adjustment_quality",
            "adjusted_readiness_score",
            "lowest_adequacy_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyResolutionRiskAdjustedReadinessReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyResolutionRiskAdjustedReadinessReasonCodeCount:
            raise TypeError(
                "ResearchStrategyResolutionRiskAdjustedReadinessReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyResolutionRiskAdjustedReadinessReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchStrategyResolutionRiskAdjustedReadinessReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchStrategyResolutionRiskAdjustedReadinessReport:
    generated_at: datetime
    config_version: str
    status: str
    review_packet_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_adjusted_readiness_score: Decimal | None
    max_contradiction_pressure_score: Decimal
    min_settlement_clarity_score: Decimal
    min_quorum_score: Decimal
    min_event_timing_score: Decimal
    rows: tuple[ResearchStrategyResolutionRiskAdjustedReadinessRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyResolutionRiskAdjustedReadinessReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyResolutionRiskAdjustedReadinessReport:
            raise TypeError(
                "ResearchStrategyResolutionRiskAdjustedReadinessReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyResolutionRiskAdjustedReadinessReport:
            raise ValueError(
                "report must be exactly "
                "ResearchStrategyResolutionRiskAdjustedReadinessReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_RESOLUTION_RISK_ADJUSTED_READINESS_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "review_packet_count",
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
            "average_adjusted_readiness_score",
            _require_optional_ratio_decimal(
                "average_adjusted_readiness_score",
                self.average_adjusted_readiness_score,
            ),
        )
        for field_name in (
            "max_contradiction_pressure_score",
            "min_settlement_clarity_score",
            "min_quorum_score",
            "min_event_timing_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
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
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        return research_strategy_resolution_risk_adjusted_readiness_report_payload(self)


def build_research_strategy_resolution_risk_adjusted_readiness_report(
    inputs: Iterable[ResearchStrategyResolutionRiskAdjustedReadinessInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyResolutionRiskAdjustedReadinessConfig | None = None,
) -> ResearchStrategyResolutionRiskAdjustedReadinessReport:
    """Build a deterministic local report-only readiness snapshot."""

    if config is None:
        config = ResearchStrategyResolutionRiskAdjustedReadinessConfig()
    if type(config) is not ResearchStrategyResolutionRiskAdjustedReadinessConfig:
        raise ValueError(
            "config must be a "
            "ResearchStrategyResolutionRiskAdjustedReadinessConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(inputs)
    rows = _build_rows(normalized, config)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "review_packet_count": _count_decimal(len(rows)),
        "pass_count": _count_decimal(_status_count(rows, PASS_STATUS)),
        "watch_count": _count_decimal(_status_count(rows, WATCH_STATUS)),
        "block_count": _count_decimal(_status_count(rows, BLOCK_STATUS)),
        "average_adjusted_readiness_score": _average_adjusted_readiness_score(rows),
        "max_contradiction_pressure_score": _max_decimal(
            row.contradiction_pressure_score for row in rows
        ),
        "min_settlement_clarity_score": _min_decimal(
            row.settlement_clarity_score for row in rows
        ),
        "min_quorum_score": _min_decimal(row.quorum_score for row in rows),
        "min_event_timing_score": _min_decimal(row.event_timing_score for row in rows),
        "rows": rows,
        "reason_code_counts": _reason_code_counts(reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyResolutionRiskAdjustedReadinessReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_resolution_risk_adjusted_readiness_report_payload(
    report: ResearchStrategyResolutionRiskAdjustedReadinessReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyResolutionRiskAdjustedReadinessReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyResolutionRiskAdjustedReadinessReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_strategy_resolution_risk_adjusted_readiness_public_payload(payload)
    return payload


def validate_research_strategy_resolution_risk_adjusted_readiness_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_numerics(payload)
    _reject_unsafe_public_payload("public payload", payload, allow_json_containers=True)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if digest != _report_digest_from_values(unsigned_payload):
        raise ValueError("derived_validation_digest does not match public payload")


def research_strategy_resolution_risk_adjusted_readiness_report_digest(
    report: ResearchStrategyResolutionRiskAdjustedReadinessReport,
) -> str:
    if type(report) is not ResearchStrategyResolutionRiskAdjustedReadinessReport:
        raise ValueError(
            "report must be a ResearchStrategyResolutionRiskAdjustedReadinessReport",
        )
    _require_hard_flags("report", report)
    digest = _report_digest_from_values(_report_values_without_digest(report))
    if digest != report.derived_validation_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return digest


def _build_rows(
    inputs: tuple[ResearchStrategyResolutionRiskAdjustedReadinessInput, ...],
    config: ResearchStrategyResolutionRiskAdjustedReadinessConfig,
) -> tuple[ResearchStrategyResolutionRiskAdjustedReadinessRow, ...]:
    rows = tuple(_row_from_input(item, config) for item in inputs)
    return tuple(sorted(rows, key=_row_sort_key))


def _row_from_input(
    item: ResearchStrategyResolutionRiskAdjustedReadinessInput,
    config: ResearchStrategyResolutionRiskAdjustedReadinessConfig,
) -> ResearchStrategyResolutionRiskAdjustedReadinessRow:
    relief_score = _quantize(_ONE - item.contradiction_pressure_score)
    adjusted_score = _adjusted_readiness_score(
        settlement_clarity_score=item.settlement_clarity_score,
        quorum_score=item.quorum_score,
        contradiction_relief_score=relief_score,
        event_timing_score=item.event_timing_score,
        risk_adjustment_quality=item.risk_adjustment_quality,
    )
    lowest_adequacy = min(
        item.settlement_clarity_score,
        item.quorum_score,
        relief_score,
        item.event_timing_score,
    )
    status = _row_status(
        adjusted_readiness_score=adjusted_score,
        lowest_adequacy_score=lowest_adequacy,
        contradiction_pressure_score=item.contradiction_pressure_score,
        config=config,
    )
    return ResearchStrategyResolutionRiskAdjustedReadinessRow(
        review_packet_label=item.review_packet_label,
        settlement_clarity_score=item.settlement_clarity_score,
        quorum_score=item.quorum_score,
        contradiction_pressure_score=item.contradiction_pressure_score,
        contradiction_relief_score=relief_score,
        event_timing_score=item.event_timing_score,
        risk_adjustment_quality=item.risk_adjustment_quality,
        adjusted_readiness_score=adjusted_score,
        lowest_adequacy_score=lowest_adequacy,
        status=status,
        reason_codes=_row_reason_codes(
            item,
            status=status,
            contradiction_relief_score=relief_score,
            config=config,
        ),
    )


def _adjusted_readiness_score(
    *,
    settlement_clarity_score: Decimal,
    quorum_score: Decimal,
    contradiction_relief_score: Decimal,
    event_timing_score: Decimal,
    risk_adjustment_quality: Decimal,
) -> Decimal:
    with localcontext() as context:
        context.prec = 28
        unadjusted = (
            settlement_clarity_score
            + quorum_score
            + contradiction_relief_score
            + event_timing_score
        ) / _FOUR
        adjusted = unadjusted * risk_adjustment_quality
    return _quantize(adjusted)


def _row_status(
    *,
    adjusted_readiness_score: Decimal,
    lowest_adequacy_score: Decimal,
    contradiction_pressure_score: Decimal,
    config: ResearchStrategyResolutionRiskAdjustedReadinessConfig,
) -> str:
    if contradiction_pressure_score >= config.block_contradiction_pressure:
        return BLOCK_STATUS
    if adjusted_readiness_score < config.watch_readiness_score:
        return BLOCK_STATUS
    if lowest_adequacy_score < config.watch_component_score:
        return BLOCK_STATUS
    if contradiction_pressure_score >= config.watch_contradiction_pressure:
        return WATCH_STATUS
    if adjusted_readiness_score < config.pass_readiness_score:
        return WATCH_STATUS
    if lowest_adequacy_score < config.pass_component_score:
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    item: ResearchStrategyResolutionRiskAdjustedReadinessInput,
    *,
    status: str,
    contradiction_relief_score: Decimal,
    config: ResearchStrategyResolutionRiskAdjustedReadinessConfig,
) -> tuple[str, ...]:
    reason_codes = {
        f"settlement_clarity_{_component_status(item.settlement_clarity_score, config)}",
        f"quorum_{_component_status(item.quorum_score, config)}",
        f"event_timing_{_component_status(item.event_timing_score, config)}",
        f"risk_adjustment_{_component_status(item.risk_adjustment_quality, config)}",
        f"resolution_readiness_{status}",
    }
    pressure_status = _contradiction_pressure_status(
        pressure_score=item.contradiction_pressure_score,
        relief_score=contradiction_relief_score,
        row_status=status,
        config=config,
    )
    reason_codes.add(f"contradiction_pressure_{pressure_status}")
    for code in item.reason_codes:
        reason_codes.add(f"input_{code}")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), allow_empty=False)


def _component_status(
    value: Decimal,
    config: ResearchStrategyResolutionRiskAdjustedReadinessConfig,
) -> str:
    if value < config.watch_component_score:
        return BLOCK_STATUS
    if value < config.pass_component_score:
        return WATCH_STATUS
    return PASS_STATUS


def _contradiction_pressure_status(
    *,
    pressure_score: Decimal,
    relief_score: Decimal,
    row_status: str,
    config: ResearchStrategyResolutionRiskAdjustedReadinessConfig,
) -> str:
    if pressure_score >= config.block_contradiction_pressure:
        return BLOCK_STATUS
    if pressure_score >= config.watch_contradiction_pressure:
        return WATCH_STATUS
    if row_status == WATCH_STATUS and pressure_score > _ZERO:
        return WATCH_STATUS
    if relief_score < config.watch_component_score:
        return BLOCK_STATUS
    if relief_score < config.pass_component_score:
        return WATCH_STATUS
    return PASS_STATUS


def _row_sort_key(
    row: ResearchStrategyResolutionRiskAdjustedReadinessRow,
) -> tuple[object, ...]:
    return (
        _status_rank(row.status),
        row.review_packet_label,
        -row.adjusted_readiness_score,
        -row.contradiction_pressure_score,
    )


def _report_status(
    rows: tuple[ResearchStrategyResolutionRiskAdjustedReadinessRow, ...],
) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchStrategyResolutionRiskAdjustedReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("resolution_readiness_no_packets",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), allow_empty=False)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyResolutionRiskAdjustedReadinessReasonCodeCount, ...]:
    counts = Counter(reason_codes)
    return tuple(
        ResearchStrategyResolutionRiskAdjustedReadinessReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(count),
        )
        for reason_code, count in sorted(counts.items())
    )


def _validate_row_consistency(
    row: ResearchStrategyResolutionRiskAdjustedReadinessRow,
) -> None:
    expected_relief = _quantize(_ONE - row.contradiction_pressure_score)
    if row.contradiction_relief_score != expected_relief:
        raise ValueError("contradiction_relief_score must match pressure score")
    expected_adjusted = _adjusted_readiness_score(
        settlement_clarity_score=row.settlement_clarity_score,
        quorum_score=row.quorum_score,
        contradiction_relief_score=row.contradiction_relief_score,
        event_timing_score=row.event_timing_score,
        risk_adjustment_quality=row.risk_adjustment_quality,
    )
    if row.adjusted_readiness_score != expected_adjusted:
        raise ValueError("adjusted_readiness_score must match row inputs")
    expected_lowest = min(
        getattr(row, field_name) for field_name in _ADEQUACY_FIELDS
    )
    if row.lowest_adequacy_score != expected_lowest:
        raise ValueError("lowest_adequacy_score must match adequacy scores")
    if f"resolution_readiness_{row.status}" not in row.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchStrategyResolutionRiskAdjustedReadinessReport,
) -> None:
    if report.review_packet_count != _count_decimal(len(report.rows)):
        raise ValueError("review_packet_count must match rows")
    for field_name, status in (
        ("pass_count", PASS_STATUS),
        ("watch_count", WATCH_STATUS),
        ("block_count", BLOCK_STATUS),
    ):
        if getattr(report, field_name) != _count_decimal(_status_count(report.rows, status)):
            raise ValueError(f"{field_name} must match rows")
    if report.average_adjusted_readiness_score != _average_adjusted_readiness_score(
        report.rows,
    ):
        raise ValueError("average_adjusted_readiness_score must match rows")
    if report.max_contradiction_pressure_score != _max_decimal(
        row.contradiction_pressure_score for row in report.rows
    ):
        raise ValueError("max_contradiction_pressure_score must match rows")
    if report.min_settlement_clarity_score != _min_decimal(
        row.settlement_clarity_score for row in report.rows
    ):
        raise ValueError("min_settlement_clarity_score must match rows")
    if report.min_quorum_score != _min_decimal(row.quorum_score for row in report.rows):
        raise ValueError("min_quorum_score must match rows")
    if report.min_event_timing_score != _min_decimal(
        row.event_timing_score for row in report.rows
    ):
        raise ValueError("min_event_timing_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyResolutionRiskAdjustedReadinessInput],
) -> tuple[ResearchStrategyResolutionRiskAdjustedReadinessInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be an iterable")
    normalized = tuple(inputs)
    for item in normalized:
        if type(item) is not ResearchStrategyResolutionRiskAdjustedReadinessInput:
            raise ValueError(
                "inputs must contain "
                "ResearchStrategyResolutionRiskAdjustedReadinessInput",
            )
        _require_hard_flags("input", item)
    return normalized


def _normalize_rows(
    rows: Sequence[ResearchStrategyResolutionRiskAdjustedReadinessRow],
) -> tuple[ResearchStrategyResolutionRiskAdjustedReadinessRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyResolutionRiskAdjustedReadinessRow:
            raise ValueError(
                "rows must contain ResearchStrategyResolutionRiskAdjustedReadinessRow",
            )
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: Sequence[ResearchStrategyResolutionRiskAdjustedReadinessReasonCodeCount],
) -> tuple[ResearchStrategyResolutionRiskAdjustedReadinessReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Sequence):
        raise ValueError("reason_code_counts must be a sequence")
    normalized = tuple(counts)
    for count in normalized:
        if (
            type(count)
            is not ResearchStrategyResolutionRiskAdjustedReadinessReasonCodeCount
        ):
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyResolutionRiskAdjustedReadinessReasonCodeCount",
            )
        _require_hard_flags("reason code count", count)
    return tuple(sorted(normalized, key=lambda item: item.reason_code))


def _normalize_reason_codes(
    field_name: str,
    reason_codes: Sequence[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError(f"{field_name} must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(sorted(normalized))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must contain public reason codes")
    if not _PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must contain public reason codes")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if isinstance(value, Decimal) and type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_optional_ratio_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _as_utc(field_name: str, value: object) -> datetime:
    if isinstance(value, datetime) and type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    return value.astimezone(UTC)


def _count_decimal(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT, rounding=ROUND_HALF_UP)


def _status_count(
    rows: tuple[ResearchStrategyResolutionRiskAdjustedReadinessRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_adjusted_readiness_score(
    rows: tuple[ResearchStrategyResolutionRiskAdjustedReadinessRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    with localcontext() as context:
        context.prec = 28
        return _quantize(
            sum((row.adjusted_readiness_score for row in rows), _ZERO)
            / _count_decimal(len(rows)),
        )


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    return max(tuple(values), default=_ZERO)


def _min_decimal(values: Iterable[Decimal]) -> Decimal:
    return min(tuple(values), default=_ZERO)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _status_rank(status: str) -> Decimal:
    if status == BLOCK_STATUS:
        return Decimal("0")
    if status == WATCH_STATUS:
        return Decimal("1")
    return Decimal("2")


def _report_values_without_digest(
    report: ResearchStrategyResolutionRiskAdjustedReadinessReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    _reject_public_numerics(payload)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_public_numerics(value: object) -> None:
    if type(value) is int or isinstance(value, float):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in _UNSAFE_KEY_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_VALUE_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")


@dataclass(frozen=True)
class _PayloadFlags:
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


__all__ = (
    "BLOCK_STATUS",
    "DEFAULT_RESEARCH_STRATEGY_RESOLUTION_RISK_ADJUSTED_READINESS_CONFIG_VERSION",
    "PASS_STATUS",
    "ResearchStrategyResolutionRiskAdjustedReadinessConfig",
    "ResearchStrategyResolutionRiskAdjustedReadinessInput",
    "ResearchStrategyResolutionRiskAdjustedReadinessReasonCodeCount",
    "ResearchStrategyResolutionRiskAdjustedReadinessReport",
    "ResearchStrategyResolutionRiskAdjustedReadinessRow",
    "WATCH_STATUS",
    "build_research_strategy_resolution_risk_adjusted_readiness_report",
    "research_strategy_resolution_risk_adjusted_readiness_report_digest",
    "research_strategy_resolution_risk_adjusted_readiness_report_payload",
    "validate_research_strategy_resolution_risk_adjusted_readiness_public_payload",
)
