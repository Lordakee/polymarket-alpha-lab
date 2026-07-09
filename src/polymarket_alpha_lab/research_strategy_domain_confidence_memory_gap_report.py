"""Sanitized report for domain confidence memory gaps."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_DOMAIN_CONFIDENCE_MEMORY_GAP_REPORT_CONFIG_VERSION = (
    "research-strategy-domain-confidence-memory-gap-report-v0"
)
RESEARCH_STRATEGY_DOMAIN_CONFIDENCE_MEMORY_GAP_REPORT_STATUSES = (
    "pass",
    "watch",
    "block",
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUS_SORT_SEQUENCE = (STATUS_BLOCK, STATUS_WATCH, STATUS_PASS)
STATUS_SEQUENCE = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FIVE = Decimal("5.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
HEX_CHARS = frozenset("0123456789abcdef")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "candidate_id",
        "candidate_reference",
        "candidate_",
        "market_id",
        "market_reference",
        "market_slug",
        "market_question",
        "question_text",
        "source_url",
        "source_text",
        "evidence_locator",
        "evidence_excerpt",
        "http://",
        "https://",
        "dsn",
        "table",
        _join_parts("to", "ken"),
        "secret",
        "credential",
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("or", "der"),
        _join_parts("tra", "de"),
        _join_parts("trad", "ing"),
        _join_parts("b", "uy"),
        _join_parts("se", "ll"),
        _join_parts("reco", "mmendation"),
        _join_parts("siz", "ing"),
        "private",
        "raw",
        "dsn=",
    ),
)

ROW_REASON_CODES = (
    "domain_confidence_memory_gap_pass",
    "domain_confidence_memory_gap_watch",
    "domain_confidence_memory_gap_block",
    "calibration_freshness_pass",
    "calibration_freshness_watch",
    "calibration_freshness_block",
    "historical_forecast_error_pass",
    "historical_forecast_error_watch",
    "historical_forecast_error_block",
    "evidence_confidence_pass",
    "evidence_confidence_watch",
    "evidence_confidence_block",
    "source_disagreement_pass",
    "source_disagreement_watch",
    "source_disagreement_block",
    "liquidity_cost_pressure_pass",
    "liquidity_cost_pressure_watch",
    "liquidity_cost_pressure_block",
)
REPORT_REASON_CODES = (
    "domain_confidence_memory_gap_report_pass",
    "domain_confidence_memory_gap_report_watch",
    "domain_confidence_memory_gap_report_block",
    "domain_confidence_memory_gap_report_empty",
    "calibration_refresh_review",
    "forecast_error_review",
    "evidence_confidence_review",
    "source_disagreement_review",
    "liquidity_cost_pressure_review",
)
REASON_CODES = ROW_REASON_CODES + REPORT_REASON_CODES

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_DOMAIN_CONFIDENCE_MEMORY_GAP_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_DOMAIN_CONFIDENCE_MEMORY_GAP_REPORT_STATUSES",
    "ResearchStrategyDomainConfidenceMemoryGapConfig",
    "ResearchStrategyDomainConfidenceMemoryGapInput",
    "ResearchStrategyDomainConfidenceMemoryGapReasonCodeCount",
    "ResearchStrategyDomainConfidenceMemoryGapRow",
    "ResearchStrategyDomainConfidenceMemoryGapReport",
    "build_research_strategy_domain_confidence_memory_gap_report",
    "research_strategy_domain_confidence_memory_gap_report_digest",
    "research_strategy_domain_confidence_memory_gap_report_payload",
)


@dataclass(frozen=True)
class ResearchStrategyDomainConfidenceMemoryGapConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_DOMAIN_CONFIDENCE_MEMORY_GAP_REPORT_CONFIG_VERSION
    )
    calibration_freshness_pass_ceiling_seconds: Decimal = Decimal("2592000.000000")
    calibration_freshness_watch_ceiling_seconds: Decimal = Decimal("7776000.000000")
    historical_forecast_error_pass_ceiling: Decimal = Decimal("0.100000")
    historical_forecast_error_watch_ceiling: Decimal = Decimal("0.250000")
    evidence_confidence_pass_floor: Decimal = Decimal("0.800000")
    evidence_confidence_watch_floor: Decimal = Decimal("0.550000")
    source_disagreement_pass_ceiling: Decimal = Decimal("0.100000")
    source_disagreement_watch_ceiling: Decimal = Decimal("0.300000")
    liquidity_cost_pressure_pass_ceiling: Decimal = Decimal("0.020000")
    liquidity_cost_pressure_watch_ceiling: Decimal = Decimal("0.060000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "calibration_freshness_pass_ceiling_seconds",
            "calibration_freshness_watch_ceiling_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "historical_forecast_error_pass_ceiling",
            "historical_forecast_error_watch_ceiling",
            "evidence_confidence_pass_floor",
            "evidence_confidence_watch_floor",
            "source_disagreement_pass_ceiling",
            "source_disagreement_watch_ceiling",
            "liquidity_cost_pressure_pass_ceiling",
            "liquidity_cost_pressure_watch_ceiling",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_ceiling_pair(
            "calibration_freshness_pass_ceiling_seconds",
            self.calibration_freshness_pass_ceiling_seconds,
            self.calibration_freshness_watch_ceiling_seconds,
        )
        _require_ceiling_pair(
            "historical_forecast_error",
            self.historical_forecast_error_pass_ceiling,
            self.historical_forecast_error_watch_ceiling,
        )
        _require_floor_pair(
            "evidence_confidence",
            self.evidence_confidence_pass_floor,
            self.evidence_confidence_watch_floor,
        )
        _require_ceiling_pair(
            "source_disagreement",
            self.source_disagreement_pass_ceiling,
            self.source_disagreement_watch_ceiling,
        )
        _require_ceiling_pair(
            "liquidity_cost_pressure",
            self.liquidity_cost_pressure_pass_ceiling,
            self.liquidity_cost_pressure_watch_ceiling,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyDomainConfidenceMemoryGapInput:
    domain_key: str
    analyst_group: str
    private_candidate_reference: str
    private_market_reference: str
    private_market_slug_text: str
    private_question_text: str
    private_evidence_locator: str
    private_evidence_excerpt: str
    calibration_updated_at: datetime
    historical_forecast_error: Decimal
    evidence_confidence_score: Decimal
    source_disagreement_score: Decimal
    liquidity_cost_pressure_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "domain_key",
            _require_public_string("domain_key", self.domain_key),
        )
        object.__setattr__(
            self,
            "analyst_group",
            _require_public_string("analyst_group", self.analyst_group),
        )
        for field_name in (
            "private_candidate_reference",
            "private_market_reference",
            "private_market_slug_text",
            "private_question_text",
            "private_evidence_locator",
            "private_evidence_excerpt",
        ):
            _require_private_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "calibration_updated_at",
            _as_utc("calibration_updated_at", self.calibration_updated_at),
        )
        for field_name in (
            "historical_forecast_error",
            "evidence_confidence_score",
            "source_disagreement_score",
            "liquidity_cost_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyDomainConfidenceMemoryGapReasonCodeCount:
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count("count", self.count),
        )
        object.__setattr__(
            self,
            "input_ratio",
            _require_ratio_decimal("input_ratio", self.input_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyDomainConfidenceMemoryGapRow:
    row_number: Decimal
    domain_key: str
    analyst_group: str
    calibration_age_seconds: Decimal
    historical_forecast_error: Decimal
    evidence_confidence_score: Decimal
    source_disagreement_score: Decimal
    liquidity_cost_pressure_score: Decimal
    calibration_freshness_score: Decimal
    forecast_error_safety_score: Decimal
    evidence_confidence_quality_score: Decimal
    source_agreement_score: Decimal
    liquidity_cost_safety_score: Decimal
    domain_confidence_memory_score: Decimal
    memory_gap_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "row_number",
            _require_positive_count("row_number", self.row_number),
        )
        object.__setattr__(
            self,
            "domain_key",
            _require_public_string("domain_key", self.domain_key),
        )
        object.__setattr__(
            self,
            "analyst_group",
            _require_public_string("analyst_group", self.analyst_group),
        )
        object.__setattr__(
            self,
            "calibration_age_seconds",
            _require_nonnegative_decimal(
                "calibration_age_seconds",
                self.calibration_age_seconds,
            ),
        )
        for field_name in (
            "historical_forecast_error",
            "evidence_confidence_score",
            "source_disagreement_score",
            "liquidity_cost_pressure_score",
            "calibration_freshness_score",
            "forecast_error_safety_score",
            "evidence_confidence_quality_score",
            "source_agreement_score",
            "liquidity_cost_safety_score",
            "domain_confidence_memory_score",
            "memory_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchStrategyDomainConfidenceMemoryGapReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_domain_confidence_memory_score: Decimal
    mean_memory_gap_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategyDomainConfidenceMemoryGapReasonCodeCount, ...]
    rows: tuple[ResearchStrategyDomainConfidenceMemoryGapRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_domain_confidence_memory_score",
            "mean_memory_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)


def build_research_strategy_domain_confidence_memory_gap_report(
    inputs: Iterable[ResearchStrategyDomainConfidenceMemoryGapInput],
    *,
    config: ResearchStrategyDomainConfidenceMemoryGapConfig,
    generated_at: datetime,
) -> ResearchStrategyDomainConfidenceMemoryGapReport:
    if type(config) is not ResearchStrategyDomainConfidenceMemoryGapConfig:
        raise ValueError(
            "config must be a ResearchStrategyDomainConfidenceMemoryGapConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_inputs = _normalize_inputs(inputs)
    row_values = sorted(
        (
            _row_values_from_input(value, config=config, generated_at=generated_at_utc)
            for value in source_inputs
        ),
        key=_row_values_sort_key,
    )
    rows = tuple(
        ResearchStrategyDomainConfidenceMemoryGapRow(
            row_number=_count(index),
            **values,
        )
        for index, values in enumerate(row_values, start=1)
    )
    return ResearchStrategyDomainConfidenceMemoryGapReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        mean_domain_confidence_memory_score=_mean(
            tuple(row.domain_confidence_memory_score for row in rows),
        ),
        mean_memory_gap_score=_mean(tuple(row.memory_gap_score for row in rows)),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_domain_confidence_memory_gap_report_payload(
    report: ResearchStrategyDomainConfidenceMemoryGapReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyDomainConfidenceMemoryGapReport:
        _require_hard_flags("report", report)
        _verify_report_integrity(report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        _verify_public_payload_integrity(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyDomainConfidenceMemoryGapReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_strategy_domain_confidence_memory_gap_report_digest(
    report: ResearchStrategyDomainConfidenceMemoryGapReport | dict[str, Any],
) -> str:
    return research_strategy_domain_confidence_memory_gap_report_payload(report)[
        "derived_validation_digest"
    ]


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


def _normalize_inputs(
    value: Iterable[ResearchStrategyDomainConfidenceMemoryGapInput],
) -> tuple[ResearchStrategyDomainConfidenceMemoryGapInput, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError("inputs must be an iterable")
    rows = tuple(value)
    seen_public_keys: set[tuple[str, str]] = set()
    for item in rows:
        if type(item) is not ResearchStrategyDomainConfidenceMemoryGapInput:
            raise ValueError(
                "inputs must contain ResearchStrategyDomainConfidenceMemoryGapInput values",
            )
        _require_hard_flags("input", item)
        public_key = (item.domain_key, item.analyst_group)
        if public_key in seen_public_keys:
            raise ValueError("duplicate domain_key and analyst_group values are not allowed")
        seen_public_keys.add(public_key)
    return rows


def _row_values_from_input(
    value: ResearchStrategyDomainConfidenceMemoryGapInput,
    *,
    config: ResearchStrategyDomainConfidenceMemoryGapConfig,
    generated_at: datetime,
) -> dict[str, Any]:
    calibration_updated_at = _as_utc(
        "calibration_updated_at",
        value.calibration_updated_at,
    )
    if calibration_updated_at > generated_at:
        raise ValueError("calibration_updated_at must not be after generated_at")
    calibration_age = _age_seconds(calibration_updated_at, generated_at)
    calibration_score = _ceiling_safety_score(
        calibration_age,
        pass_ceiling=config.calibration_freshness_pass_ceiling_seconds,
        watch_ceiling=config.calibration_freshness_watch_ceiling_seconds,
    )
    forecast_error_score = _ceiling_safety_score(
        value.historical_forecast_error,
        pass_ceiling=config.historical_forecast_error_pass_ceiling,
        watch_ceiling=config.historical_forecast_error_watch_ceiling,
    )
    evidence_score = _floor_quality_score(
        value.evidence_confidence_score,
        pass_floor=config.evidence_confidence_pass_floor,
        watch_floor=config.evidence_confidence_watch_floor,
    )
    source_agreement = _ceiling_safety_score(
        value.source_disagreement_score,
        pass_ceiling=config.source_disagreement_pass_ceiling,
        watch_ceiling=config.source_disagreement_watch_ceiling,
    )
    liquidity_score = _ceiling_safety_score(
        value.liquidity_cost_pressure_score,
        pass_ceiling=config.liquidity_cost_pressure_pass_ceiling,
        watch_ceiling=config.liquidity_cost_pressure_watch_ceiling,
    )
    memory_score = _mean(
        (
            calibration_score,
            forecast_error_score,
            evidence_score,
            source_agreement,
            liquidity_score,
        ),
    )
    gap_score = _clamped_ratio(ONE - memory_score)
    status = _row_status(
        calibration_age_seconds=calibration_age,
        historical_forecast_error=value.historical_forecast_error,
        evidence_confidence_score=value.evidence_confidence_score,
        source_disagreement_score=value.source_disagreement_score,
        liquidity_cost_pressure_score=value.liquidity_cost_pressure_score,
        config=config,
    )
    return {
        "domain_key": value.domain_key,
        "analyst_group": value.analyst_group,
        "calibration_age_seconds": calibration_age,
        "historical_forecast_error": value.historical_forecast_error,
        "evidence_confidence_score": value.evidence_confidence_score,
        "source_disagreement_score": value.source_disagreement_score,
        "liquidity_cost_pressure_score": value.liquidity_cost_pressure_score,
        "calibration_freshness_score": calibration_score,
        "forecast_error_safety_score": forecast_error_score,
        "evidence_confidence_quality_score": evidence_score,
        "source_agreement_score": source_agreement,
        "liquidity_cost_safety_score": liquidity_score,
        "domain_confidence_memory_score": memory_score,
        "memory_gap_score": gap_score,
        "status": status,
        "reason_codes": _row_reason_codes(
            calibration_age_seconds=calibration_age,
            historical_forecast_error=value.historical_forecast_error,
            evidence_confidence_score=value.evidence_confidence_score,
            source_disagreement_score=value.source_disagreement_score,
            liquidity_cost_pressure_score=value.liquidity_cost_pressure_score,
            status=status,
            config=config,
        ),
    }


def _row_status(
    *,
    calibration_age_seconds: Decimal,
    historical_forecast_error: Decimal,
    evidence_confidence_score: Decimal,
    source_disagreement_score: Decimal,
    liquidity_cost_pressure_score: Decimal,
    config: ResearchStrategyDomainConfidenceMemoryGapConfig,
) -> str:
    component_statuses = (
        _ceiling_status(
            calibration_age_seconds,
            pass_ceiling=config.calibration_freshness_pass_ceiling_seconds,
            watch_ceiling=config.calibration_freshness_watch_ceiling_seconds,
        ),
        _ceiling_status(
            historical_forecast_error,
            pass_ceiling=config.historical_forecast_error_pass_ceiling,
            watch_ceiling=config.historical_forecast_error_watch_ceiling,
        ),
        _floor_status(
            evidence_confidence_score,
            pass_floor=config.evidence_confidence_pass_floor,
            watch_floor=config.evidence_confidence_watch_floor,
        ),
        _ceiling_status(
            source_disagreement_score,
            pass_ceiling=config.source_disagreement_pass_ceiling,
            watch_ceiling=config.source_disagreement_watch_ceiling,
        ),
        _ceiling_status(
            liquidity_cost_pressure_score,
            pass_ceiling=config.liquidity_cost_pressure_pass_ceiling,
            watch_ceiling=config.liquidity_cost_pressure_watch_ceiling,
        ),
    )
    if STATUS_BLOCK in component_statuses:
        return STATUS_BLOCK
    if STATUS_WATCH in component_statuses:
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    calibration_age_seconds: Decimal,
    historical_forecast_error: Decimal,
    evidence_confidence_score: Decimal,
    source_disagreement_score: Decimal,
    liquidity_cost_pressure_score: Decimal,
    status: str,
    config: ResearchStrategyDomainConfidenceMemoryGapConfig,
) -> tuple[str, ...]:
    return _normalize_reason_codes(
        "reason_codes",
        (
            f"domain_confidence_memory_gap_{status}",
            "calibration_freshness_"
            + _ceiling_status(
                calibration_age_seconds,
                pass_ceiling=config.calibration_freshness_pass_ceiling_seconds,
                watch_ceiling=config.calibration_freshness_watch_ceiling_seconds,
            ),
            "historical_forecast_error_"
            + _ceiling_status(
                historical_forecast_error,
                pass_ceiling=config.historical_forecast_error_pass_ceiling,
                watch_ceiling=config.historical_forecast_error_watch_ceiling,
            ),
            "evidence_confidence_"
            + _floor_status(
                evidence_confidence_score,
                pass_floor=config.evidence_confidence_pass_floor,
                watch_floor=config.evidence_confidence_watch_floor,
            ),
            "source_disagreement_"
            + _ceiling_status(
                source_disagreement_score,
                pass_ceiling=config.source_disagreement_pass_ceiling,
                watch_ceiling=config.source_disagreement_watch_ceiling,
            ),
            "liquidity_cost_pressure_"
            + _ceiling_status(
                liquidity_cost_pressure_score,
                pass_ceiling=config.liquidity_cost_pressure_pass_ceiling,
                watch_ceiling=config.liquidity_cost_pressure_watch_ceiling,
            ),
        ),
        ROW_REASON_CODES,
    )


def _ceiling_status(
    value: Decimal,
    *,
    pass_ceiling: Decimal,
    watch_ceiling: Decimal,
) -> str:
    if value <= pass_ceiling:
        return STATUS_PASS
    if value <= watch_ceiling:
        return STATUS_WATCH
    return STATUS_BLOCK


def _floor_status(value: Decimal, *, pass_floor: Decimal, watch_floor: Decimal) -> str:
    if value >= pass_floor:
        return STATUS_PASS
    if value >= watch_floor:
        return STATUS_WATCH
    return STATUS_BLOCK


def _ceiling_safety_score(
    value: Decimal,
    *,
    pass_ceiling: Decimal,
    watch_ceiling: Decimal,
) -> Decimal:
    if value <= pass_ceiling:
        return ONE
    if value >= watch_ceiling:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamped_ratio((watch_ceiling - value) / (watch_ceiling - pass_ceiling))


def _floor_quality_score(
    value: Decimal,
    *,
    pass_floor: Decimal,
    watch_floor: Decimal,
) -> Decimal:
    if value >= pass_floor:
        return ONE
    if value <= watch_floor:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamped_ratio((value - watch_floor) / (pass_floor - watch_floor))


def _row_values_sort_key(values: dict[str, Any]) -> tuple[int, Decimal, str, str]:
    return (
        STATUS_SORT_SEQUENCE.index(values["status"]),
        values["domain_confidence_memory_score"],
        values["domain_key"],
        values["analyst_group"],
    )


def _report_status(
    rows: tuple[ResearchStrategyDomainConfidenceMemoryGapRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    statuses = tuple(row.status for row in rows)
    if STATUS_BLOCK in statuses:
        return STATUS_BLOCK
    if STATUS_WATCH in statuses:
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchStrategyDomainConfidenceMemoryGapRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("domain_confidence_memory_gap_report_empty",)
    codes: list[str] = [f"domain_confidence_memory_gap_report_{_report_status(rows)}"]
    if any(_has_reason_suffix(row, "calibration_freshness") for row in rows):
        codes.append("calibration_refresh_review")
    if any(_has_reason_suffix(row, "historical_forecast_error") for row in rows):
        codes.append("forecast_error_review")
    if any(_has_reason_suffix(row, "evidence_confidence") for row in rows):
        codes.append("evidence_confidence_review")
    if any(_has_reason_suffix(row, "source_disagreement") for row in rows):
        codes.append("source_disagreement_review")
    if any(_has_reason_suffix(row, "liquidity_cost_pressure") for row in rows):
        codes.append("liquidity_cost_pressure_review")
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _has_reason_suffix(
    row: ResearchStrategyDomainConfidenceMemoryGapRow,
    prefix: str,
) -> bool:
    return any(
        code in row.reason_codes
        for code in (f"{prefix}_{STATUS_WATCH}", f"{prefix}_{STATUS_BLOCK}")
    )


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategyDomainConfidenceMemoryGapRow, ...],
) -> tuple[ResearchStrategyDomainConfidenceMemoryGapReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyDomainConfidenceMemoryGapReasonCodeCount(
                reason_code="domain_confidence_memory_gap_report_empty",
                count=ONE,
                input_ratio=ONE,
            ),
        )
    report_reasons = _report_reason_codes(rows)
    reason_codes = tuple(
        code
        for code in REASON_CODES
        if code in report_reasons or any(code in row.reason_codes for row in rows)
    )
    denominator = _count(len(rows))
    return tuple(
        ResearchStrategyDomainConfidenceMemoryGapReasonCodeCount(
            reason_code=code,
            count=_count(
                sum(1 for row in rows if code in row.reason_codes)
                + (1 if code in report_reasons else 0),
            ),
            input_ratio=_ratio(
                _count(
                    sum(1 for row in rows if code in row.reason_codes)
                    + (1 if code in report_reasons else 0),
                ),
                denominator,
            ),
        )
        for code in reason_codes
    )


def _status_count(
    rows: tuple[ResearchStrategyDomainConfidenceMemoryGapRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _normalize_rows(
    value: object,
) -> tuple[ResearchStrategyDomainConfidenceMemoryGapRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    expected_numbers = tuple(_count(index) for index in range(1, len(rows) + 1))
    seen_public_keys: set[tuple[str, str]] = set()
    for row, expected_number in zip(rows, expected_numbers):
        if type(row) is not ResearchStrategyDomainConfidenceMemoryGapRow:
            raise ValueError(
                "rows must contain ResearchStrategyDomainConfidenceMemoryGapRow values",
            )
        _require_hard_flags("row", row)
        if row.row_number != expected_number:
            raise ValueError("row_number values must be sequential")
        public_key = (row.domain_key, row.analyst_group)
        if public_key in seen_public_keys:
            raise ValueError("duplicate row public keys are not allowed")
        seen_public_keys.add(public_key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return rows


def _row_sort_key(
    row: ResearchStrategyDomainConfidenceMemoryGapRow,
) -> tuple[int, Decimal, str, str]:
    return (
        STATUS_SORT_SEQUENCE.index(row.status),
        row.domain_confidence_memory_score,
        row.domain_key,
        row.analyst_group,
    )


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchStrategyDomainConfidenceMemoryGapReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    items = tuple(value)
    previous_index = -1
    seen_codes: set[str] = set()
    for item in items:
        if type(item) is not ResearchStrategyDomainConfidenceMemoryGapReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchStrategyDomainConfidenceMemoryGapReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in seen_codes:
            raise ValueError("reason_code_counts must be unique")
        seen_codes.add(item.reason_code)
        current_index = REASON_CODES.index(item.reason_code)
        if current_index <= previous_index:
            raise ValueError("reason_code_counts must be deterministic")
        previous_index = current_index
    return items


def _validate_row_consistency(row: ResearchStrategyDomainConfidenceMemoryGapRow) -> None:
    expected_score = _mean(
        (
            row.calibration_freshness_score,
            row.forecast_error_safety_score,
            row.evidence_confidence_quality_score,
            row.source_agreement_score,
            row.liquidity_cost_safety_score,
        ),
    )
    if row.domain_confidence_memory_score != expected_score:
        raise ValueError("domain_confidence_memory_score must match component scores")
    if row.memory_gap_score != _clamped_ratio(ONE - row.domain_confidence_memory_score):
        raise ValueError("memory_gap_score must match domain_confidence_memory_score")
    if row.reason_codes == ():
        raise ValueError("reason_codes must not be empty")
    if f"domain_confidence_memory_gap_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")


def _validate_report_consistency(
    report: ResearchStrategyDomainConfidenceMemoryGapReport,
) -> None:
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    expected_counts = {
        "pass_count": _status_count(report.rows, STATUS_PASS),
        "watch_count": _status_count(report.rows, STATUS_WATCH),
        "block_count": _status_count(report.rows, STATUS_BLOCK),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.mean_domain_confidence_memory_score != _mean(
        tuple(row.domain_confidence_memory_score for row in report.rows),
    ):
        raise ValueError("mean_domain_confidence_memory_score must match rows")
    if report.mean_memory_gap_score != _mean(
        tuple(row.memory_gap_score for row in report.rows),
    ):
        raise ValueError("mean_memory_gap_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _apply_or_verify_digest(value: object) -> None:
    digest = getattr(value, "derived_validation_digest", "")
    expected = _object_digest(value)
    if digest:
        _require_digest_string("derived_validation_digest", digest)
        if digest != expected:
            raise ValueError("derived_validation_digest must match report contents")
    object.__setattr__(value, "derived_validation_digest", expected)


def _object_digest(value: object) -> str:
    payload = {
        field.name: getattr(value, field.name)
        for field in fields(value)
        if field.name != "derived_validation_digest"
    }
    return _digest_for_json_payload(_json_ready(payload))


def _verify_report_integrity(
    report: ResearchStrategyDomainConfidenceMemoryGapReport,
) -> None:
    for row in report.rows:
        if row.derived_validation_digest != _object_digest(row):
            raise ValueError("derived_validation_digest must match report contents")
    if report.derived_validation_digest != _object_digest(report):
        raise ValueError("derived_validation_digest must match report contents")


def _verify_public_payload_integrity(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be present")
    _require_digest_string("derived_validation_digest", digest)
    rows = payload.get("rows", [])
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        row_digest = row.get("derived_validation_digest")
        if type(row_digest) is not str:
            raise ValueError("derived_validation_digest must be present")
        _require_digest_string("derived_validation_digest", row_digest)
        if row_digest != _digest_for_json_payload(row):
            raise ValueError("derived_validation_digest must match report contents")
    if digest != _digest_for_json_payload(payload):
        raise ValueError("derived_validation_digest must match report contents")


def _digest_for_json_payload(payload: dict[str, Any]) -> str:
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    canonical_payload = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical_payload.encode("utf-8")).hexdigest()


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamped_ratio(sum(values, ZERO) / _count(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamped_ratio(numerator / denominator)


def _age_seconds(value: datetime, generated_at: datetime) -> Decimal:
    if value > generated_at:
        return ZERO
    delta = generated_at - value
    with localcontext(DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days).quantize(QUANTUM) * SECONDS_PER_DAY
            + Decimal(delta.seconds).quantize(QUANTUM)
            + (
                Decimal(delta.microseconds).quantize(QUANTUM)
                / MICROSECONDS_PER_SECOND
            )
        )
        return seconds.quantize(QUANTUM)


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(QUANTUM)


def _clamped_ratio(value: Decimal) -> Decimal:
    normalized = _require_decimal("ratio", value).quantize(QUANTUM)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _require_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_ceiling_pair(label: str, pass_ceiling: Decimal, watch_ceiling: Decimal) -> None:
    if pass_ceiling > watch_ceiling:
        suffixes = ("_pass_ceiling", "_pass_ceiling_seconds")
        field_name = label if label.endswith(suffixes) else f"{label}_pass_ceiling"
        raise ValueError(f"{field_name} must not exceed watch threshold")


def _require_floor_pair(label: str, pass_floor: Decimal, watch_floor: Decimal) -> None:
    if watch_floor > pass_floor:
        raise ValueError(f"{label}_watch_floor must not exceed pass threshold")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in STATUS_SEQUENCE:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    codes = tuple(value)
    for code in codes:
        if code not in allowed_codes:
            raise ValueError(f"{field_name} must contain known reason codes")
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(code for code in allowed_codes if code in codes) != codes:
        raise ValueError(f"{field_name} must be deterministic")
    return codes


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"unsafe public value in {field_name}")
    return value


def _require_private_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_digest_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) in (str, bool):
        return value
    if type(value) is int:
        raise ValueError("JSON value must not be an int")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")
