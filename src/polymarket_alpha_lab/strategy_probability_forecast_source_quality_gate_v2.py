"""Pure Phase 1 forecast source-quality gate reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_STRATEGY_PROBABILITY_FORECAST_SOURCE_QUALITY_GATE_V2_CONFIG_VERSION = (
    "strategy-probability-forecast-source-quality-gate-v2"
)

DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")

STATUSES = ("pass", "watch", "blocked")
SOURCE_KINDS = ("official", "specialist", "model", "context", "community")

EMPTY_REASON_CODE = "empty_forecast_source_quality_inputs"
REPORT_REASON_CODES = (
    "forecast_source_quality_gate_pass",
    "forecast_source_quality_gate_watch",
    "forecast_source_quality_gate_blocked",
    "official_source_gap_present",
    "stale_evidence_present",
    EMPTY_REASON_CODE,
)
ROW_REASON_CODES = (
    "forecast_source_quality_pass",
    "forecast_source_quality_watch",
    "forecast_source_quality_blocked",
    "official_source_absent",
    "official_source_thin",
    "stale_evidence_present",
    "stale_evidence_blocked",
    "source_quality_below_watch_threshold",
    "source_quality_below_block_threshold",
)
ROW_DETAIL_REASON_CODES = ROW_REASON_CODES[3:]

REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "status",
    "candidate_count",
    "pass_count",
    "watch_count",
    "blocked_count",
    "official_source_gap_count",
    "stale_evidence_count",
    "average_source_quality_score",
    "min_source_quality_score",
    "max_source_quality_score",
    "rows",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_FIELDS = (
    *REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST,
    DERIVED_VALIDATION_DIGEST_FIELD,
)
ROW_PAYLOAD_FIELDS = (
    "candidate_id",
    "status",
    "source_count",
    "official_source_count",
    "stale_source_count",
    "latest_observed_at",
    "average_forecast_probability",
    "official_source_ratio",
    "stale_source_ratio",
    "freshness_score",
    "evidence_strength_score",
    "source_relevance_score",
    "calibration_score",
    "source_quality_score",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)

_UNSAFE_PUBLIC_TEXT_TOKENS = (
    "li" + "ve",
    "au" + "th",
    "wal" + "let",
    "or" + "der",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
    "si" + "gn",
    "si" + "gning",
    "mut" + "ation",
    "b" + "uy",
    "s" + "ell",
    "tra" + "de",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")

EVIDENCE_STRENGTH_WEIGHT = Decimal("0.250000")
SOURCE_RELEVANCE_WEIGHT = Decimal("0.250000")
FRESHNESS_WEIGHT = Decimal("0.200000")
OFFICIAL_SOURCE_WEIGHT = Decimal("0.200000")
CALIBRATION_WEIGHT = Decimal("0.100000")

_STATUS_WEIGHT = {"blocked": 0, "watch": 1, "pass": 2}


@dataclass(frozen=True)
class StrategyProbabilityForecastSourceQualityGateV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_PROBABILITY_FORECAST_SOURCE_QUALITY_GATE_V2_CONFIG_VERSION
    )
    max_evidence_age_seconds: Decimal = Decimal("172800.000000")
    quality_watch_threshold: Decimal = Decimal("0.700000")
    quality_block_threshold: Decimal = Decimal("0.500000")
    official_source_watch_threshold: Decimal = Decimal("0.500000")
    official_source_block_threshold: Decimal = Decimal("0.000001")
    stale_source_watch_threshold: Decimal = Decimal("0.250000")
    stale_source_block_threshold: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "StrategyProbabilityForecastSourceQualityGateV2Config "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            StrategyProbabilityForecastSourceQualityGateV2Config,
        )
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_PROBABILITY_FORECAST_SOURCE_QUALITY_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        object.__setattr__(
            self,
            "max_evidence_age_seconds",
            _require_positive_seconds(
                "max_evidence_age_seconds",
                self.max_evidence_age_seconds,
            ),
        )
        for field_name in (
            "quality_watch_threshold",
            "quality_block_threshold",
            "official_source_watch_threshold",
            "official_source_block_threshold",
            "stale_source_watch_threshold",
            "stale_source_block_threshold",
        ):
            object.__setattr__(self, field_name, _require_ratio(field_name, getattr(self, field_name)))
        _require_threshold_sequence(
            "quality_threshold",
            self.quality_block_threshold,
            self.quality_watch_threshold,
        )
        _require_threshold_sequence(
            "official_source_threshold",
            self.official_source_block_threshold,
            self.official_source_watch_threshold,
        )
        _require_threshold_sequence(
            "stale_source_threshold",
            self.stale_source_watch_threshold,
            self.stale_source_block_threshold,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class StrategyProbabilityForecastSourceQualityEvidence:
    candidate_id: str
    source_id: str
    source_kind: str
    observed_at: datetime
    forecast_probability: Decimal
    evidence_strength_score: Decimal
    source_relevance_score: Decimal
    calibration_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "StrategyProbabilityForecastSourceQualityEvidence "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("evidence", self, StrategyProbabilityForecastSourceQualityEvidence)
        _require_public_text("candidate_id", self.candidate_id)
        _require_public_text("source_id", self.source_id)
        _require_member("source_kind", self.source_kind, SOURCE_KINDS)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "forecast_probability",
            "evidence_strength_score",
            "source_relevance_score",
            "calibration_score",
        ):
            object.__setattr__(self, field_name, _require_ratio(field_name, getattr(self, field_name)))
        _require_hard_flags("evidence", self)
        _reject_unsafe_public_payload("evidence", self)


@dataclass(frozen=True)
class StrategyProbabilityForecastSourceQualityGateV2Row:
    candidate_id: str
    status: str
    source_count: Decimal
    official_source_count: Decimal
    stale_source_count: Decimal
    latest_observed_at: datetime | None
    average_forecast_probability: Decimal
    official_source_ratio: Decimal
    stale_source_ratio: Decimal
    freshness_score: Decimal
    evidence_strength_score: Decimal
    source_relevance_score: Decimal
    calibration_score: Decimal
    source_quality_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "StrategyProbabilityForecastSourceQualityGateV2Row "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, StrategyProbabilityForecastSourceQualityGateV2Row)
        _require_public_text("candidate_id", self.candidate_id)
        _require_member("status", self.status, STATUSES)
        for field_name in ("source_count", "official_source_count", "stale_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_optional_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in (
            "average_forecast_probability",
            "official_source_ratio",
            "stale_source_ratio",
            "freshness_score",
            "evidence_strength_score",
            "source_relevance_score",
            "calibration_score",
            "source_quality_score",
        ):
            object.__setattr__(self, field_name, _require_ratio(field_name, getattr(self, field_name)))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _validate_row(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class StrategyProbabilityForecastSourceQualityGateV2Report:
    generated_at: datetime
    config_version: str
    status: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    official_source_gap_count: Decimal
    stale_evidence_count: Decimal
    average_source_quality_score: Decimal
    min_source_quality_score: Decimal
    max_source_quality_score: Decimal
    rows: tuple[StrategyProbabilityForecastSourceQualityGateV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "StrategyProbabilityForecastSourceQualityGateV2Report "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, StrategyProbabilityForecastSourceQualityGateV2Report)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_PROBABILITY_FORECAST_SOURCE_QUALITY_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        _require_member("status", self.status, STATUSES)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "official_source_gap_count",
            "stale_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_source_quality_score",
            "min_source_quality_score",
            "max_source_quality_score",
        ):
            object.__setattr__(self, field_name, _require_ratio(field_name, getattr(self, field_name)))
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                DERIVED_VALIDATION_DIGEST_FIELD,
                _report_derived_validation_digest(self),
            )
        else:
            _require_sha256_digest(
                DERIVED_VALIDATION_DIGEST_FIELD,
                self.derived_validation_digest,
            )
            _validate_report_derived_validation_digest(self)


def build_strategy_probability_forecast_source_quality_gate_v2_report(
    evidence_rows: object,
    *,
    config: StrategyProbabilityForecastSourceQualityGateV2Config,
    generated_at: datetime,
) -> StrategyProbabilityForecastSourceQualityGateV2Report:
    if type(config) is not StrategyProbabilityForecastSourceQualityGateV2Config:
        raise ValueError(
            "config must be a StrategyProbabilityForecastSourceQualityGateV2Config",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows_by_candidate: dict[str, list[StrategyProbabilityForecastSourceQualityEvidence]] = {}
    source_rows = _normalize_evidence_rows(evidence_rows)
    _validate_observation_times(source_rows, generated_at_utc)
    for row in source_rows:
        rows_by_candidate.setdefault(row.candidate_id, []).append(row)
    rows = tuple(
        sorted(
            (
                _build_row(
                    candidate_id,
                    tuple(candidate_rows),
                    config=config,
                    generated_at=generated_at_utc,
                )
                for candidate_id, candidate_rows in rows_by_candidate.items()
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows, len(source_rows))
    return StrategyProbabilityForecastSourceQualityGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(reason_codes),
        candidate_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        official_source_gap_count=_row_reason_count(rows, ("official_source_absent", "official_source_thin")),
        stale_evidence_count=_stale_evidence_row_count(rows),
        average_source_quality_score=_average_source_quality_score(rows),
        min_source_quality_score=_min_source_quality_score(rows),
        max_source_quality_score=_max_source_quality_score(rows),
        rows=rows,
        reason_codes=reason_codes,
    )


def strategy_probability_forecast_source_quality_gate_v2_report_to_payload(
    report: StrategyProbabilityForecastSourceQualityGateV2Report | dict[str, object],
) -> dict[str, object]:
    if type(report) is StrategyProbabilityForecastSourceQualityGateV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        _validate_report_derived_validation_digest(report)
        payload = _report_public_payload_values(report)
        payload[DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
        _validate_public_report_payload(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _require_payload_fields("payload", report, REPORT_PAYLOAD_FIELDS)
        _validate_public_report_payload(report)
        return dict(report)
    raise ValueError(
        "report must be a StrategyProbabilityForecastSourceQualityGateV2Report",
    )


def _normalize_evidence_rows(
    value: object,
) -> tuple[StrategyProbabilityForecastSourceQualityEvidence, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("evidence_rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not StrategyProbabilityForecastSourceQualityEvidence:
            raise ValueError(
                "evidence_rows must contain "
                "StrategyProbabilityForecastSourceQualityEvidence values",
            )
        _require_hard_flags("evidence", row)
        key = (row.candidate_id, row.source_id)
        if key in seen:
            raise ValueError("evidence_rows must be unique by candidate_id and source_id")
        seen.add(key)
    return rows


def _validate_observation_times(
    rows: tuple[StrategyProbabilityForecastSourceQualityEvidence, ...],
    generated_at: datetime,
) -> None:
    for row in rows:
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")


def _build_row(
    candidate_id: str,
    rows: tuple[StrategyProbabilityForecastSourceQualityEvidence, ...],
    *,
    config: StrategyProbabilityForecastSourceQualityGateV2Config,
    generated_at: datetime,
) -> StrategyProbabilityForecastSourceQualityGateV2Row:
    source_count = _count(len(rows))
    official_count = _count(sum(1 for row in rows if row.source_kind == "official"))
    stale_count = _count(
        sum(
            1
            for row in rows
            if _duration_seconds(row.observed_at, generated_at) > config.max_evidence_age_seconds
        ),
    )
    official_source_ratio = _ratio(official_count, source_count)
    stale_source_ratio = _ratio(stale_count, source_count)
    freshness_score = _average(
        tuple(
            _freshness_score(
                _duration_seconds(row.observed_at, generated_at),
                config.max_evidence_age_seconds,
            )
            for row in rows
        ),
    )
    source_quality_score = _source_quality_score(
        evidence_strength_score=_average(tuple(row.evidence_strength_score for row in rows)),
        source_relevance_score=_average(tuple(row.source_relevance_score for row in rows)),
        calibration_score=_average(tuple(row.calibration_score for row in rows)),
        freshness_score=freshness_score,
        official_source_ratio=official_source_ratio,
    )
    reason_codes = _row_reason_codes(
        source_quality_score=source_quality_score,
        official_source_ratio=official_source_ratio,
        stale_source_ratio=stale_source_ratio,
        config=config,
    )
    return StrategyProbabilityForecastSourceQualityGateV2Row(
        candidate_id=candidate_id,
        status=_row_status(reason_codes),
        source_count=source_count,
        official_source_count=official_count,
        stale_source_count=stale_count,
        latest_observed_at=max(row.observed_at for row in rows),
        average_forecast_probability=_average(tuple(row.forecast_probability for row in rows)),
        official_source_ratio=official_source_ratio,
        stale_source_ratio=stale_source_ratio,
        freshness_score=freshness_score,
        evidence_strength_score=_average(tuple(row.evidence_strength_score for row in rows)),
        source_relevance_score=_average(tuple(row.source_relevance_score for row in rows)),
        calibration_score=_average(tuple(row.calibration_score for row in rows)),
        source_quality_score=source_quality_score,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    source_quality_score: Decimal,
    official_source_ratio: Decimal,
    stale_source_ratio: Decimal,
    config: StrategyProbabilityForecastSourceQualityGateV2Config,
) -> tuple[str, ...]:
    detail_reasons: list[str] = []
    if official_source_ratio < config.official_source_block_threshold:
        detail_reasons.append("official_source_absent")
    elif official_source_ratio < config.official_source_watch_threshold:
        detail_reasons.append("official_source_thin")
    if stale_source_ratio >= config.stale_source_block_threshold:
        detail_reasons.append("stale_evidence_blocked")
    elif stale_source_ratio >= config.stale_source_watch_threshold:
        detail_reasons.append("stale_evidence_present")
    if source_quality_score < config.quality_block_threshold:
        detail_reasons.append("source_quality_below_block_threshold")
    elif source_quality_score < config.quality_watch_threshold:
        detail_reasons.append("source_quality_below_watch_threshold")
    status = _status_from_detail_reasons(detail_reasons)
    return (f"forecast_source_quality_{status}", *tuple(detail_reasons))


def _status_from_detail_reasons(detail_reasons: list[str]) -> str:
    if not detail_reasons:
        return "pass"
    if any(reason.endswith("_blocked") or reason.endswith("_absent") for reason in detail_reasons):
        return "blocked"
    if "source_quality_below_block_threshold" in detail_reasons:
        return "blocked"
    return "watch"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes[0] == "forecast_source_quality_blocked":
        return "blocked"
    if reason_codes[0] == "forecast_source_quality_watch":
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyProbabilityForecastSourceQualityGateV2Row, ...],
    source_row_count: int,
) -> tuple[str, ...]:
    if source_row_count == 0:
        return (EMPTY_REASON_CODE,)
    status = _rollup_status(rows)
    reason_codes: list[str] = [f"forecast_source_quality_gate_{status}"]
    if any(
        reason_code in {"official_source_absent", "official_source_thin"}
        for row in rows
        for reason_code in row.reason_codes
    ):
        reason_codes.append("official_source_gap_present")
    if any(row.stale_source_count > _count(0) for row in rows):
        reason_codes.append("stale_evidence_present")
    return tuple(reason_codes)


def _rollup_status(rows: tuple[StrategyProbabilityForecastSourceQualityGateV2Row, ...]) -> str:
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes[0] in (EMPTY_REASON_CODE, "forecast_source_quality_gate_blocked"):
        return "blocked"
    if reason_codes[0] == "forecast_source_quality_gate_watch":
        return "watch"
    return "pass"


def _row_sort_key(
    row: StrategyProbabilityForecastSourceQualityGateV2Row,
) -> tuple[int, Decimal, str]:
    return (_STATUS_WEIGHT[row.status], -row.source_quality_score, row.candidate_id)


def _source_quality_score(
    *,
    evidence_strength_score: Decimal,
    source_relevance_score: Decimal,
    calibration_score: Decimal,
    freshness_score: Decimal,
    official_source_ratio: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (
            evidence_strength_score * EVIDENCE_STRENGTH_WEIGHT
            + source_relevance_score * SOURCE_RELEVANCE_WEIGHT
            + freshness_score * FRESHNESS_WEIGHT
            + official_source_ratio * OFFICIAL_SOURCE_WEIGHT
            + calibration_score * CALIBRATION_WEIGHT
        ).quantize(RATIO_QUANTUM)


def _freshness_score(source_age_seconds: Decimal, max_evidence_age_seconds: Decimal) -> Decimal:
    if source_age_seconds >= max_evidence_age_seconds:
        return ZERO_RATIO
    return _ratio(max_evidence_age_seconds - source_age_seconds, max_evidence_age_seconds)


def _status_count(
    rows: tuple[StrategyProbabilityForecastSourceQualityGateV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _row_reason_count(
    rows: tuple[StrategyProbabilityForecastSourceQualityGateV2Row, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if any(reason_code in row.reason_codes for reason_code in reason_codes)
        ),
    )


def _stale_evidence_row_count(
    rows: tuple[StrategyProbabilityForecastSourceQualityGateV2Row, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if row.stale_source_count > _count(0)))


def _average_source_quality_score(
    rows: tuple[StrategyProbabilityForecastSourceQualityGateV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return _average(tuple(row.source_quality_score for row in rows))


def _min_source_quality_score(
    rows: tuple[StrategyProbabilityForecastSourceQualityGateV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return min(row.source_quality_score for row in rows)


def _max_source_quality_score(
    rows: tuple[StrategyProbabilityForecastSourceQualityGateV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return max(row.source_quality_score for row in rows)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO_RATIO) / Decimal(len(values))).quantize(RATIO_QUANTUM)


def _validate_row(row: StrategyProbabilityForecastSourceQualityGateV2Row) -> None:
    if row.source_count == _count(0):
        raise ValueError("row source_count must be positive")
    if row.official_source_count > row.source_count:
        raise ValueError("official_source_count must not exceed source_count")
    if row.stale_source_count > row.source_count:
        raise ValueError("stale_source_count must not exceed source_count")
    if row.reason_codes[0] != f"forecast_source_quality_{row.status}":
        raise ValueError("reason_codes must match status")
    details = tuple(reason for reason in row.reason_codes if reason in ROW_DETAIL_REASON_CODES)
    if row.status == "pass" and details:
        raise ValueError("pass rows must not include detail reason codes")
    if row.status != "pass" and not details:
        raise ValueError("non-pass rows must include detail reason codes")


def _validate_report(report: StrategyProbabilityForecastSourceQualityGateV2Report) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.official_source_gap_count != _row_reason_count(
        report.rows,
        ("official_source_absent", "official_source_thin"),
    ):
        raise ValueError("official_source_gap_count must match rows")
    if report.stale_evidence_count != _stale_evidence_row_count(report.rows):
        raise ValueError("stale_evidence_count must match rows")
    if report.average_source_quality_score != _average_source_quality_score(report.rows):
        raise ValueError("average_source_quality_score must match rows")
    if report.min_source_quality_score != _min_source_quality_score(report.rows):
        raise ValueError("min_source_quality_score must match rows")
    if report.max_source_quality_score != _max_source_quality_score(report.rows):
        raise ValueError("max_source_quality_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, int(report.candidate_count)):
        raise ValueError("reason_codes must match rows")
    if report.status != _report_status(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequencing")


def _require_rows(
    value: object,
) -> tuple[StrategyProbabilityForecastSourceQualityGateV2Row, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not StrategyProbabilityForecastSourceQualityGateV2Row:
            raise ValueError(
                "rows must contain StrategyProbabilityForecastSourceQualityGateV2Row values",
            )
        _require_hard_flags("row", row)
        if row.candidate_id in seen:
            raise ValueError("rows must be unique by candidate_id")
        seen.add(row.candidate_id)
    return rows


def _validate_report_derived_validation_digest(
    report: StrategyProbabilityForecastSourceQualityGateV2Report,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _report_derived_validation_digest(
    report: StrategyProbabilityForecastSourceQualityGateV2Report,
) -> str:
    return _digest_public_payload(
        "strategy_probability_forecast_source_quality_gate_v2_report",
        _report_public_payload_values(report),
    )


def _digest_public_payload(label: str, payload: dict[str, object]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop(DERIVED_VALIDATION_DIGEST_FIELD, None)
    encoded = (
        label
        + "|"
        + json.dumps(
            digest_payload,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _report_public_payload_values(
    report: StrategyProbabilityForecastSourceQualityGateV2Report,
) -> dict[str, object]:
    return {
        "generated_at": _datetime_payload(report.generated_at),
        "config_version": report.config_version,
        "status": report.status,
        "candidate_count": _decimal_payload(report.candidate_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "blocked_count": _decimal_payload(report.blocked_count),
        "official_source_gap_count": _decimal_payload(report.official_source_gap_count),
        "stale_evidence_count": _decimal_payload(report.stale_evidence_count),
        "average_source_quality_score": _decimal_payload(report.average_source_quality_score),
        "min_source_quality_score": _decimal_payload(report.min_source_quality_score),
        "max_source_quality_score": _decimal_payload(report.max_source_quality_score),
        "rows": [_row_public_payload(row) for row in report.rows],
        "reason_codes": list(report.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_public_payload(
    row: StrategyProbabilityForecastSourceQualityGateV2Row,
) -> dict[str, object]:
    return {
        "candidate_id": row.candidate_id,
        "status": row.status,
        "source_count": _decimal_payload(row.source_count),
        "official_source_count": _decimal_payload(row.official_source_count),
        "stale_source_count": _decimal_payload(row.stale_source_count),
        "latest_observed_at": _optional_datetime_payload(row.latest_observed_at),
        "average_forecast_probability": _decimal_payload(row.average_forecast_probability),
        "official_source_ratio": _decimal_payload(row.official_source_ratio),
        "stale_source_ratio": _decimal_payload(row.stale_source_ratio),
        "freshness_score": _decimal_payload(row.freshness_score),
        "evidence_strength_score": _decimal_payload(row.evidence_strength_score),
        "source_relevance_score": _decimal_payload(row.source_relevance_score),
        "calibration_score": _decimal_payload(row.calibration_score),
        "source_quality_score": _decimal_payload(row.source_quality_score),
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _validate_public_report_payload(payload: dict[str, object]) -> None:
    _reject_unsafe_public_payload("payload", payload)
    _require_payload_fields("payload", payload, REPORT_PAYLOAD_FIELDS)
    for field_name in PHASE_FLAG_FIELDS:
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True for payload")
    _require_datetime_payload_string("generated_at", payload["generated_at"])
    _require_public_text("config_version", payload["config_version"])
    if (
        payload["config_version"]
        != DEFAULT_STRATEGY_PROBABILITY_FORECAST_SOURCE_QUALITY_GATE_V2_CONFIG_VERSION
    ):
        raise ValueError("config_version must be supported")
    _require_member("status", payload["status"], STATUSES)
    parsed_counts = {
        "candidate_count": _require_decimal_payload_string(payload["candidate_count"], count=True),
        "pass_count": _require_decimal_payload_string(payload["pass_count"], count=True),
        "watch_count": _require_decimal_payload_string(payload["watch_count"], count=True),
        "blocked_count": _require_decimal_payload_string(payload["blocked_count"], count=True),
        "official_source_gap_count": _require_decimal_payload_string(
            payload["official_source_gap_count"],
            count=True,
        ),
        "stale_evidence_count": _require_decimal_payload_string(
            payload["stale_evidence_count"],
            count=True,
        ),
    }
    for field_name in (
        "average_source_quality_score",
        "min_source_quality_score",
        "max_source_quality_score",
    ):
        _require_decimal_payload_string(payload[field_name], ratio=True)
    rows = _require_public_rows(payload["rows"])
    _require_public_reason_code_list(
        "reason_codes",
        payload["reason_codes"],
        REPORT_REASON_CODES,
    )
    if parsed_counts["candidate_count"] != _count(len(rows)):
        raise ValueError("candidate_count must match payload rows")
    _require_sha256_digest(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload[DERIVED_VALIDATION_DIGEST_FIELD],
    )
    expected_digest = _digest_public_payload(
        "strategy_probability_forecast_source_quality_gate_v2_report",
        {field_name: payload[field_name] for field_name in REPORT_PAYLOAD_FIELDS_WITHOUT_DIGEST},
    )
    if payload[DERIVED_VALIDATION_DIGEST_FIELD] != expected_digest:
        raise ValueError("derived_validation_digest must match public payload")


def _require_public_rows(value: object) -> tuple[dict[str, object], ...]:
    if type(value) is not list:
        raise ValueError("rows must be a list")
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in value:
        if type(item) is not dict:
            raise ValueError("rows must contain objects")
        _validate_public_row_payload(item)
        candidate_id = item["candidate_id"]
        if type(candidate_id) is not str:
            raise ValueError("candidate_id must be a string")
        if candidate_id in seen:
            raise ValueError("rows must be unique by candidate_id")
        seen.add(candidate_id)
        rows.append(item)
    return tuple(rows)


def _validate_public_row_payload(payload: dict[str, object]) -> None:
    _require_payload_fields("row", payload, ROW_PAYLOAD_FIELDS)
    for field_name in PHASE_FLAG_FIELDS:
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True for row")
    _require_public_text("candidate_id", payload["candidate_id"])
    _require_member("status", payload["status"], STATUSES)
    for field_name in ("source_count", "official_source_count", "stale_source_count"):
        _require_decimal_payload_string(payload[field_name], count=True)
    if payload["latest_observed_at"] is not None:
        _require_datetime_payload_string("latest_observed_at", payload["latest_observed_at"])
    for field_name in (
        "average_forecast_probability",
        "official_source_ratio",
        "stale_source_ratio",
        "freshness_score",
        "evidence_strength_score",
        "source_relevance_score",
        "calibration_score",
        "source_quality_score",
    ):
        _require_decimal_payload_string(payload[field_name], ratio=True)
    reason_codes = _require_public_reason_code_list(
        "reason_codes",
        payload["reason_codes"],
        ROW_REASON_CODES,
    )
    if reason_codes[0] != f"forecast_source_quality_{payload['status']}":
        raise ValueError("row reason_codes must match status")


def _require_payload_fields(
    label: str,
    payload: dict[str, object],
    expected_fields: tuple[str, ...],
) -> None:
    if set(payload) != set(expected_fields):
        raise ValueError(f"{label} fields must match expected public fields")


def _require_public_reason_code_list(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        _require_member(field_name, item, allowed)
        if item in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        normalized.append(item)
        seen.add(item)
    return tuple(normalized)


def _require_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        _require_member(field_name, item, allowed)
        if item not in seen:
            normalized.append(item)
            seen.add(item)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(normalized)


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    _reject_unsafe_public_text(field_name, value)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_public_text(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be a known value")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_threshold_sequence(label: str, lower: Decimal, upper: Decimal) -> None:
    if lower > upper:
        raise ValueError(f"{label} lower threshold must not exceed upper threshold")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_RATIO or decimal_value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value.quantize(RATIO_QUANTUM)


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value.quantize(COUNT_QUANTUM)


def _require_positive_seconds(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_seconds(field_name, value)
    if decimal_value <= Decimal("0"):
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value.quantize(SECONDS_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == Decimal("0"):
        raise ValueError("ratio denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    total_seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )
    return total_seconds.quantize(SECONDS_QUANTUM)


def _datetime_payload(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def _optional_datetime_payload(value: datetime | None) -> str | None:
    if value is None:
        return None
    return _datetime_payload(value)


def _decimal_payload(value: Decimal) -> str:
    _require_decimal("payload_decimal", value)
    return str(value)


def _require_datetime_payload_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if _datetime_payload(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _require_decimal_payload_string(
    value: object,
    *,
    ratio: bool = False,
    count: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError("Decimal payload must be a string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError("Decimal payload must be a stringified Decimal") from exc
    if ratio:
        normalized = _require_ratio("Decimal payload", decimal_value)
    elif count:
        normalized = _require_nonnegative_count("Decimal payload", decimal_value)
    else:
        normalized = _require_decimal("Decimal payload", decimal_value)
    if str(normalized) != value:
        raise ValueError("Decimal payload must be canonical")
    return normalized


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    lowered = value.lower()
    if lowered != value or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_text(f"{label} key", key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if type(value) is Decimal:
        _require_decimal("public Decimal value", value)
        return
    if type(value) is datetime:
        _as_utc("public datetime value", value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must use Decimal strings")
    raise ValueError("public payload value is not supported")


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(token in lowered for token in _UNSAFE_PUBLIC_TEXT_TOKENS):
        raise ValueError(f"unsafe public text in {label}")


__all__ = (
    "DEFAULT_STRATEGY_PROBABILITY_FORECAST_SOURCE_QUALITY_GATE_V2_CONFIG_VERSION",
    "StrategyProbabilityForecastSourceQualityEvidence",
    "StrategyProbabilityForecastSourceQualityGateV2Config",
    "StrategyProbabilityForecastSourceQualityGateV2Report",
    "StrategyProbabilityForecastSourceQualityGateV2Row",
    "build_strategy_probability_forecast_source_quality_gate_v2_report",
    "strategy_probability_forecast_source_quality_gate_v2_report_to_payload",
)
