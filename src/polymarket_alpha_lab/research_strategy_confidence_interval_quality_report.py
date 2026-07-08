"""Pure confidence interval quality report reducer for manual review."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_CONFIDENCE_INTERVAL_QUALITY_REPORT_CONFIG_VERSION = (
    "research-strategy-confidence-interval-quality-report-v0"
)
RESEARCH_STRATEGY_CONFIDENCE_INTERVAL_QUALITY_STATUSES = ("pass", "watch", "block")

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

ROW_REASON_CODES = (
    "calibration_support_block",
    "calibration_support_watch",
    "confidence_interval_quality_pass",
    "interval_width_block",
    "interval_width_watch",
    "recheck_urgency_block",
    "recheck_urgency_watch",
    "source_confidence_block",
    "source_confidence_watch",
    "stale_evidence_block",
    "stale_evidence_watch",
)
REPORT_REASON_CODES = (
    "calibration_support_review",
    "confidence_interval_quality_block",
    "confidence_interval_quality_pass",
    "confidence_interval_quality_watch",
    "interval_width_review",
    "recheck_urgency_review",
    "source_confidence_review",
    "stale_evidence_review",
)
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "auth",
    "credential",
    "private",
    "secret",
    "token",
    "wal" + "let",
    "or" + "der",
    "li" + "ve",
    "trad" + "e",
    "trad" + "ing",
    "data" + "base",
    "net" + "work",
    "candidate",
    "dsn",
    "market",
    "persist",
    "question",
    "signing",
    "slug",
    "table",
    "text",
    "url",
    "mutation",
    "b" + "uy",
    "se" + "ll",
)


@dataclass(frozen=True)
class ResearchStrategyConfidenceIntervalQualityConfig:
    config_version: str
    interval_width_watch_threshold: Decimal
    interval_width_block_threshold: Decimal
    calibration_support_watch_floor: Decimal
    calibration_support_block_floor: Decimal
    stale_evidence_watch_age_seconds: Decimal
    stale_evidence_block_age_seconds: Decimal
    source_confidence_watch_floor: Decimal
    source_confidence_block_floor: Decimal
    recheck_urgency_watch_threshold: Decimal
    recheck_urgency_block_threshold: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "interval_width_watch_threshold",
            "interval_width_block_threshold",
            "calibration_support_watch_floor",
            "calibration_support_block_floor",
            "source_confidence_watch_floor",
            "source_confidence_block_floor",
            "recheck_urgency_watch_threshold",
            "recheck_urgency_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "stale_evidence_watch_age_seconds",
            "stale_evidence_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_pair(
            "interval width threshold",
            self.interval_width_watch_threshold,
            self.interval_width_block_threshold,
        )
        _require_floor_pair(
            "calibration support threshold",
            self.calibration_support_watch_floor,
            self.calibration_support_block_floor,
        )
        _require_age_threshold_pair(
            self.stale_evidence_watch_age_seconds,
            self.stale_evidence_block_age_seconds,
        )
        _require_floor_pair(
            "source confidence threshold",
            self.source_confidence_watch_floor,
            self.source_confidence_block_floor,
        )
        _require_threshold_pair(
            "recheck urgency threshold",
            self.recheck_urgency_watch_threshold,
            self.recheck_urgency_block_threshold,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyConfidenceIntervalQualityInput:
    confidence_case_ref: str
    strategy_ref: str
    market_slug: str
    observed_at: datetime
    forecast_probability: Decimal
    lower_bound_probability: Decimal
    upper_bound_probability: Decimal
    calibration_support_score: Decimal
    source_confidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("confidence_case_ref", "strategy_ref"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        _require_canonical_raw_string("market_slug", self.market_slug)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "forecast_probability",
            "lower_bound_probability",
            "upper_bound_probability",
            "calibration_support_score",
            "source_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _validate_input_bounds(self)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyConfidenceIntervalQualityRow:
    confidence_case_ref: str
    strategy_ref: str
    observed_at: datetime
    forecast_probability: Decimal
    lower_bound_probability: Decimal
    upper_bound_probability: Decimal
    interval_width_probability: Decimal
    calibration_support_score: Decimal
    stale_evidence_age_seconds: Decimal
    stale_evidence_pressure: Decimal
    source_confidence_score: Decimal
    recheck_urgency_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("confidence_case_ref", "strategy_ref"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "forecast_probability",
            "lower_bound_probability",
            "upper_bound_probability",
            "interval_width_probability",
            "calibration_support_score",
            "stale_evidence_pressure",
            "source_confidence_score",
            "recheck_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_evidence_age_seconds",
            _normalize_nonnegative_decimal(
                "stale_evidence_age_seconds",
                self.stale_evidence_age_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchStrategyConfidenceIntervalQualityReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_interval_width_probability: Decimal
    mean_calibration_support_score: Decimal
    mean_stale_evidence_pressure: Decimal
    mean_source_confidence_score: Decimal
    mean_recheck_urgency_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    rows: tuple[ResearchStrategyConfidenceIntervalQualityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in ("source_row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_interval_width_probability",
            "mean_calibration_support_score",
            "mean_stale_evidence_pressure",
            "mean_source_confidence_score",
            "mean_recheck_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)


def build_research_strategy_confidence_interval_quality_report(
    inputs: Iterable[ResearchStrategyConfidenceIntervalQualityInput],
    *,
    config: ResearchStrategyConfidenceIntervalQualityConfig,
    generated_at: datetime,
) -> ResearchStrategyConfidenceIntervalQualityReport:
    if type(config) is not ResearchStrategyConfidenceIntervalQualityConfig:
        raise ValueError(
            "config must be a ResearchStrategyConfidenceIntervalQualityConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    value,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for value in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchStrategyConfidenceIntervalQualityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_row_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_interval_width_probability=_mean(
            tuple(row.interval_width_probability for row in rows),
        ),
        mean_calibration_support_score=_mean(
            tuple(row.calibration_support_score for row in rows),
        ),
        mean_stale_evidence_pressure=_mean(
            tuple(row.stale_evidence_pressure for row in rows),
        ),
        mean_source_confidence_score=_mean(
            tuple(row.source_confidence_score for row in rows),
        ),
        mean_recheck_urgency_score=_mean(
            tuple(row.recheck_urgency_score for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_confidence_interval_quality_report_payload(
    report: ResearchStrategyConfidenceIntervalQualityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyConfidenceIntervalQualityReport:
        _require_hard_flags("report", report)
        _verify_report_integrity(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        _verify_public_payload_integrity(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyConfidenceIntervalQualityReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_CONFIDENCE_INTERVAL_QUALITY_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_CONFIDENCE_INTERVAL_QUALITY_STATUSES",
    "ResearchStrategyConfidenceIntervalQualityConfig",
    "ResearchStrategyConfidenceIntervalQualityInput",
    "ResearchStrategyConfidenceIntervalQualityRow",
    "ResearchStrategyConfidenceIntervalQualityReport",
    "build_research_strategy_confidence_interval_quality_report",
    "research_strategy_confidence_interval_quality_report_payload",
)


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


def _row_from_input(
    value: ResearchStrategyConfidenceIntervalQualityInput,
    *,
    config: ResearchStrategyConfidenceIntervalQualityConfig,
    generated_at: datetime,
) -> ResearchStrategyConfidenceIntervalQualityRow:
    observed_at = _as_utc("observed_at", value.observed_at)
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    stale_age = _age_seconds(generated_at, observed_at)
    interval_width = _subtract_decimal(
        value.upper_bound_probability,
        value.lower_bound_probability,
    )
    stale_pressure = _stale_evidence_pressure(stale_age, config)
    urgency = _recheck_urgency_score(
        interval_width=interval_width,
        stale_evidence_pressure=stale_pressure,
        calibration_support_score=value.calibration_support_score,
        source_confidence_score=value.source_confidence_score,
        config=config,
    )
    return ResearchStrategyConfidenceIntervalQualityRow(
        confidence_case_ref=value.confidence_case_ref,
        strategy_ref=value.strategy_ref,
        observed_at=observed_at,
        forecast_probability=value.forecast_probability,
        lower_bound_probability=value.lower_bound_probability,
        upper_bound_probability=value.upper_bound_probability,
        interval_width_probability=interval_width,
        calibration_support_score=value.calibration_support_score,
        stale_evidence_age_seconds=stale_age,
        stale_evidence_pressure=stale_pressure,
        source_confidence_score=value.source_confidence_score,
        recheck_urgency_score=urgency,
        status=_row_status(value, config, generated_at=generated_at),
        reason_codes=_row_reason_codes(value, config, generated_at=generated_at),
    )


def _row_status(
    value: ResearchStrategyConfidenceIntervalQualityInput,
    config: ResearchStrategyConfidenceIntervalQualityConfig,
    *,
    generated_at: datetime,
) -> str:
    codes = _row_reason_codes(value, config, generated_at=generated_at)
    if any(code.endswith("_block") for code in codes):
        return "block"
    if len(codes) != 1 or codes[0] != "confidence_interval_quality_pass":
        return "watch"
    return "pass"


def _row_reason_codes(
    value: ResearchStrategyConfidenceIntervalQualityInput,
    config: ResearchStrategyConfidenceIntervalQualityConfig,
    *,
    generated_at: datetime,
) -> tuple[str, ...]:
    codes: list[str] = []
    interval_width = _subtract_decimal(
        value.upper_bound_probability,
        value.lower_bound_probability,
    )
    stale_age = _age_seconds(generated_at, value.observed_at)
    stale_pressure = _stale_evidence_pressure(stale_age, config)
    urgency = _recheck_urgency_score(
        interval_width=interval_width,
        stale_evidence_pressure=stale_pressure,
        calibration_support_score=value.calibration_support_score,
        source_confidence_score=value.source_confidence_score,
        config=config,
    )
    if interval_width >= config.interval_width_block_threshold:
        codes.append("interval_width_block")
    elif interval_width >= config.interval_width_watch_threshold:
        codes.append("interval_width_watch")
    if value.calibration_support_score < config.calibration_support_block_floor:
        codes.append("calibration_support_block")
    elif value.calibration_support_score < config.calibration_support_watch_floor:
        codes.append("calibration_support_watch")
    if stale_age >= config.stale_evidence_block_age_seconds:
        codes.append("stale_evidence_block")
    elif stale_age >= config.stale_evidence_watch_age_seconds:
        codes.append("stale_evidence_watch")
    if value.source_confidence_score < config.source_confidence_block_floor:
        codes.append("source_confidence_block")
    elif value.source_confidence_score < config.source_confidence_watch_floor:
        codes.append("source_confidence_watch")
    if urgency >= config.recheck_urgency_block_threshold:
        codes.append("recheck_urgency_block")
    elif urgency >= config.recheck_urgency_watch_threshold:
        codes.append("recheck_urgency_watch")
    if not codes:
        codes.append("confidence_interval_quality_pass")
    return _normalize_reason_codes("reason_codes", tuple(sorted(codes)), ROW_REASON_CODES)


def _report_status(rows: tuple[ResearchStrategyConfidenceIntervalQualityRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyConfidenceIntervalQualityRow, ...],
) -> tuple[str, ...]:
    if not rows or all(row.status == "pass" for row in rows):
        return ("confidence_interval_quality_pass",)
    codes: list[str] = []
    if any(row.status == "block" for row in rows):
        codes.append("confidence_interval_quality_block")
    elif any(row.status == "watch" for row in rows):
        codes.append("confidence_interval_quality_watch")
    if any(code.startswith("interval_width_") for row in rows for code in row.reason_codes):
        codes.append("interval_width_review")
    if any(
        code.startswith("calibration_support_")
        for row in rows
        for code in row.reason_codes
    ):
        codes.append("calibration_support_review")
    if any(
        code.startswith("stale_evidence_") for row in rows for code in row.reason_codes
    ):
        codes.append("stale_evidence_review")
    if any(
        code.startswith("source_confidence_") for row in rows for code in row.reason_codes
    ):
        codes.append("source_confidence_review")
    if any(
        code.startswith("recheck_urgency_") for row in rows for code in row.reason_codes
    ):
        codes.append("recheck_urgency_review")
    return _normalize_reason_codes("reason_codes", tuple(sorted(codes)), REPORT_REASON_CODES)


def _row_sort_key(
    row: ResearchStrategyConfidenceIntervalQualityRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        -row.recheck_urgency_score,
        -row.interval_width_probability,
        -row.stale_evidence_pressure,
        row.calibration_support_score,
        row.source_confidence_score,
        row.confidence_case_ref,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyConfidenceIntervalQualityInput],
) -> tuple[ResearchStrategyConfidenceIntervalQualityInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_refs: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategyConfidenceIntervalQualityInput:
            raise ValueError(
                "inputs must contain only ResearchStrategyConfidenceIntervalQualityInput values",
            )
        _require_hard_flags("input", value)
        if value.confidence_case_ref in seen_refs:
            raise ValueError("inputs must not contain duplicate confidence_case_ref values")
        seen_refs.add(value.confidence_case_ref)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchStrategyConfidenceIntervalQualityRow],
) -> tuple[ResearchStrategyConfidenceIntervalQualityRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_refs: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyConfidenceIntervalQualityRow:
            raise ValueError(
                "rows must contain ResearchStrategyConfidenceIntervalQualityRow values",
            )
        _require_hard_flags("row", row)
        _verify_digest(row)
        if row.confidence_case_ref in seen_refs:
            raise ValueError("rows must not contain duplicate confidence_case_ref values")
        seen_refs.add(row.confidence_case_ref)
    return normalized


def _validate_input_bounds(
    value: ResearchStrategyConfidenceIntervalQualityInput,
) -> None:
    if value.lower_bound_probability > value.upper_bound_probability:
        raise ValueError("lower_bound_probability must not exceed upper_bound_probability")
    if (
        value.forecast_probability < value.lower_bound_probability
        or value.forecast_probability > value.upper_bound_probability
    ):
        raise ValueError("forecast_probability must be within interval bounds")


def _validate_row_consistency(row: ResearchStrategyConfidenceIntervalQualityRow) -> None:
    _validate_row_bounds(row)
    expected_width = _subtract_decimal(
        row.upper_bound_probability,
        row.lower_bound_probability,
    )
    if row.interval_width_probability != expected_width:
        raise ValueError("interval_width_probability does not match interval bounds")
    if row.status == "pass" and row.reason_codes != ("confidence_interval_quality_pass",):
        raise ValueError("pass rows must only contain pass reason code")
    if row.status == "watch" and not any(code.endswith("_watch") for code in row.reason_codes):
        raise ValueError("watch rows must contain watch reason code")
    if row.status == "block" and not any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("block rows must contain block reason code")


def _validate_row_bounds(row: ResearchStrategyConfidenceIntervalQualityRow) -> None:
    if row.lower_bound_probability > row.upper_bound_probability:
        raise ValueError("lower_bound_probability must not exceed upper_bound_probability")
    if (
        row.forecast_probability < row.lower_bound_probability
        or row.forecast_probability > row.upper_bound_probability
    ):
        raise ValueError("forecast_probability must be within interval bounds")


def _validate_report_consistency(
    report: ResearchStrategyConfidenceIntervalQualityReport,
) -> None:
    if report.source_row_count != _count(len(report.rows)):
        raise ValueError("source_row_count must match rows")
    if report.source_row_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match source_row_count")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.mean_interval_width_probability != _mean(
        tuple(row.interval_width_probability for row in report.rows),
    ):
        raise ValueError("mean_interval_width_probability must match rows")
    if report.mean_calibration_support_score != _mean(
        tuple(row.calibration_support_score for row in report.rows),
    ):
        raise ValueError("mean_calibration_support_score must match rows")
    if report.mean_stale_evidence_pressure != _mean(
        tuple(row.stale_evidence_pressure for row in report.rows),
    ):
        raise ValueError("mean_stale_evidence_pressure must match rows")
    if report.mean_source_confidence_score != _mean(
        tuple(row.source_confidence_score for row in report.rows),
    ):
        raise ValueError("mean_source_confidence_score must match rows")
    if report.mean_recheck_urgency_score != _mean(
        tuple(row.recheck_urgency_score for row in report.rows),
    ):
        raise ValueError("mean_recheck_urgency_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must use deterministic sequence")


def _verify_report_integrity(report: ResearchStrategyConfidenceIntervalQualityReport) -> None:
    _verify_digest(report)
    _validate_report_consistency(report)
    for row in report.rows:
        _verify_digest(row)


def _verify_public_payload_integrity(payload: dict[str, Any]) -> None:
    _verify_public_payload_digest("payload", payload)
    rows = payload.get("rows")
    if rows is None:
        return
    if type(rows) is not list:
        raise ValueError("payload.rows must be a list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("payload.rows must contain JSON objects")
        _verify_public_payload_digest(f"payload.rows[{index}]", row)


def _verify_public_payload_digest(label: str, payload: dict[str, Any]) -> None:
    provided = payload.get("derived_validation_digest")
    _require_digest(f"{label}.derived_validation_digest", provided)
    digest_input = dict(payload)
    digest_input.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(digest_input),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    expected = sha256(encoded).hexdigest()
    if provided != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _status_count(
    rows: tuple[ResearchStrategyConfidenceIntervalQualityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategyConfidenceIntervalQualityRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        (reason_code, _count(count))
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _normalize_reason_code_counts(
    value: Iterable[tuple[str, Decimal]],
) -> tuple[tuple[str, Decimal], ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    normalized: list[tuple[str, Decimal]] = []
    for row in rows:
        if type(row) is not tuple or len(row) != 2:
            raise ValueError("reason_code_counts must contain reason_code count tuples")
        reason_code, count = row
        _require_reason_code("reason_code_counts reason_code", reason_code)
        if reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_code_counts reason_code is not supported")
        normalized.append(
            (
                reason_code,
                _normalize_nonnegative_count("reason_code_counts count", count),
            ),
        )
    return tuple(normalized)


def _stale_evidence_pressure(
    stale_age: Decimal,
    config: ResearchStrategyConfidenceIntervalQualityConfig,
) -> Decimal:
    if stale_age <= config.stale_evidence_watch_age_seconds:
        return ZERO.quantize(RATIO_QUANTUM)
    if stale_age >= config.stale_evidence_block_age_seconds:
        return ONE.quantize(RATIO_QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        span = config.stale_evidence_block_age_seconds - config.stale_evidence_watch_age_seconds
        return _quantize((stale_age - config.stale_evidence_watch_age_seconds) / span)


def _recheck_urgency_score(
    *,
    interval_width: Decimal,
    stale_evidence_pressure: Decimal,
    calibration_support_score: Decimal,
    source_confidence_score: Decimal,
    config: ResearchStrategyConfidenceIntervalQualityConfig,
) -> Decimal:
    width_pressure = _bounded_ratio(interval_width, config.interval_width_block_threshold)
    calibration_gap = _subtract_decimal(ONE, calibration_support_score)
    source_gap = _subtract_decimal(ONE, source_confidence_score)
    return max(
        width_pressure,
        stale_evidence_pressure,
        calibration_gap,
        source_gap,
    ).quantize(RATIO_QUANTUM)


def _bounded_ratio(value: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(max(ZERO, min(ONE, value / denominator)))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(RATIO_QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    with localcontext(DECIMAL_CONTEXT):
        return (
            Decimal(delta.days * 86_400)
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / Decimal("1000000"))
        )


def _apply_or_verify_digest(
    value: (
        ResearchStrategyConfidenceIntervalQualityRow
        | ResearchStrategyConfidenceIntervalQualityReport
    ),
) -> None:
    expected = _derived_digest(value)
    provided = value.derived_validation_digest
    if provided == "":
        object.__setattr__(value, "derived_validation_digest", expected)
        return
    _require_digest("derived_validation_digest", provided)
    if provided != expected:
        raise ValueError("derived_validation_digest does not match derived fields")


def _verify_digest(
    value: (
        ResearchStrategyConfidenceIntervalQualityRow
        | ResearchStrategyConfidenceIntervalQualityReport
    ),
) -> None:
    _require_digest("derived_validation_digest", value.derived_validation_digest)
    if value.derived_validation_digest != _derived_digest(value):
        raise ValueError("derived_validation_digest does not match derived fields")


def _derived_digest(
    value: (
        ResearchStrategyConfidenceIntervalQualityRow
        | ResearchStrategyConfidenceIntervalQualityReport
    ),
) -> str:
    digest_input = asdict(value)
    digest_input.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(digest_input),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(_quantize(value), "f")
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if value is None or type(value) in (str, bool):
        return value
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_canonical_public_string("public_payload_key", key)
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True for {label}")
            if key == "status":
                _require_status("status", item)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _require_canonical_public_string(label, value)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{label} must be a Decimal")
        if not value.is_finite():
            raise ValueError(f"{label} must be finite")
        return
    if isinstance(value, datetime):
        _as_utc(label, value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        raise ValueError(f"{label} must use Decimal-derived strings")
    if isinstance(value, float):
        raise ValueError(f"{label} must not be a float")
    raise ValueError(f"{label} is not JSON serializable")


def _normalize_reason_codes(
    field_name: str,
    value: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
        if reason_code not in allowed:
            raise ValueError(f"{field_name} is not supported")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    if reason_codes != tuple(sorted(reason_codes)):
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_public_string(field_name, value)
    if value.startswith("_") or value.endswith("_") or "__" in value:
        raise ValueError(f"{field_name} must be a canonical reason code")
    for character in value:
        if not (character.islower() or character.isdigit() or character == "_"):
            raise ValueError(f"{field_name} must be a canonical reason code")


def _require_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_STRATEGY_CONFIDENCE_INTERVAL_QUALITY_STATUSES
    ):
        raise ValueError(f"{field_name} must be a known status")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _require_canonical_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public content")


def _require_canonical_raw_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower().replace("-", "_").replace(" ", "_")
    compact = "".join(character for character in lowered if character.isalnum())
    return any(fragment in lowered or fragment in compact for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_threshold_pair(label: str, watch_threshold: Decimal, block_threshold: Decimal) -> None:
    if watch_threshold > block_threshold:
        raise ValueError(f"{label} watch threshold must not exceed block threshold")


def _require_floor_pair(label: str, watch_floor: Decimal, block_floor: Decimal) -> None:
    if block_floor > watch_floor:
        raise ValueError(f"{label} block threshold must not exceed watch threshold")


def _require_age_threshold_pair(
    watch_age: Decimal,
    block_age: Decimal,
) -> None:
    if watch_age <= ZERO:
        raise ValueError("stale evidence watch threshold must be positive")
    if block_age <= watch_age:
        raise ValueError("stale evidence block threshold must exceed watch threshold")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value.quantize(COUNT_QUANTUM)


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return _normalize_nonnegative_count("count", Decimal(value))


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    return _quantize(decimal_value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return +value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    for character in value:
        if character not in "0123456789abcdef":
            raise ValueError(f"{field_name} must be a sha256 hex digest")
