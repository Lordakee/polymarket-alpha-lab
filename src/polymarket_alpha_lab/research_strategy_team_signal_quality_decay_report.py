"""Report-only signal quality decay report for research strategy teams."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_TEAM_SIGNAL_QUALITY_DECAY_REPORT_CONFIG_VERSION = (
    "research-strategy-team-signal-quality-decay-report-v0"
)
RESEARCH_STRATEGY_TEAM_SIGNAL_QUALITY_DECAY_STATUSES = ("pass", "watch", "block")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

ROW_PASS_REASON = "signal_quality_decay_pass"
QUALITY_DROP_BLOCK_REASON = "quality_drop_block"
QUALITY_DROP_WATCH_REASON = "quality_drop_watch"
CURRENT_QUALITY_BLOCK_REASON = "current_quality_block"
CURRENT_QUALITY_WATCH_REASON = "current_quality_watch"
EVIDENCE_BLOCK_REASON = "evidence_freshness_block"
EVIDENCE_WATCH_REASON = "evidence_freshness_watch"
CALIBRATION_BLOCK_REASON = "calibration_block"
CALIBRATION_WATCH_REASON = "calibration_watch"
DISAGREEMENT_BLOCK_REASON = "disagreement_pressure_block"
DISAGREEMENT_WATCH_REASON = "disagreement_pressure_watch"
LATENCY_BLOCK_REASON = "review_latency_block"
LATENCY_WATCH_REASON = "review_latency_watch"
DECAY_PRESSURE_BLOCK_REASON = "decay_pressure_block"
DECAY_PRESSURE_WATCH_REASON = "decay_pressure_watch"
ADJUSTED_QUALITY_BLOCK_REASON = "adjusted_quality_block"
ADJUSTED_QUALITY_WATCH_REASON = "adjusted_quality_watch"
SIGNAL_AGE_BLOCK_REASON = "signal_age_block"
SIGNAL_AGE_WATCH_REASON = "signal_age_watch"

REPORT_PASS_REASON = "signal_quality_decay_pass"
REPORT_WATCH_REASON = "signal_quality_decay_watch"
REPORT_BLOCK_REASON = "signal_quality_decay_block"
REPORT_NO_INPUTS_REASON = "signal_quality_decay_no_inputs"
QUALITY_DROP_REVIEW_REASON = "quality_drop_review"
CURRENT_QUALITY_REVIEW_REASON = "current_quality_review"
EVIDENCE_REVIEW_REASON = "evidence_freshness_review"
CALIBRATION_REVIEW_REASON = "calibration_review"
DISAGREEMENT_REVIEW_REASON = "disagreement_pressure_review"
LATENCY_REVIEW_REASON = "review_latency_review"
DECAY_PRESSURE_REVIEW_REASON = "decay_pressure_review"
ADJUSTED_QUALITY_REVIEW_REASON = "adjusted_quality_review"
SIGNAL_AGE_REVIEW_REASON = "signal_age_review"

ROW_REASON_CODES = (
    ROW_PASS_REASON,
    QUALITY_DROP_BLOCK_REASON,
    QUALITY_DROP_WATCH_REASON,
    CURRENT_QUALITY_BLOCK_REASON,
    CURRENT_QUALITY_WATCH_REASON,
    EVIDENCE_BLOCK_REASON,
    EVIDENCE_WATCH_REASON,
    CALIBRATION_BLOCK_REASON,
    CALIBRATION_WATCH_REASON,
    DISAGREEMENT_BLOCK_REASON,
    DISAGREEMENT_WATCH_REASON,
    LATENCY_BLOCK_REASON,
    LATENCY_WATCH_REASON,
    DECAY_PRESSURE_BLOCK_REASON,
    DECAY_PRESSURE_WATCH_REASON,
    ADJUSTED_QUALITY_BLOCK_REASON,
    ADJUSTED_QUALITY_WATCH_REASON,
    SIGNAL_AGE_BLOCK_REASON,
    SIGNAL_AGE_WATCH_REASON,
)
REPORT_REASON_CODES = (
    REPORT_PASS_REASON,
    REPORT_WATCH_REASON,
    REPORT_BLOCK_REASON,
    REPORT_NO_INPUTS_REASON,
    QUALITY_DROP_REVIEW_REASON,
    CURRENT_QUALITY_REVIEW_REASON,
    EVIDENCE_REVIEW_REASON,
    CALIBRATION_REVIEW_REASON,
    DISAGREEMENT_REVIEW_REASON,
    LATENCY_REVIEW_REASON,
    DECAY_PRESSURE_REVIEW_REASON,
    ADJUSTED_QUALITY_REVIEW_REASON,
    SIGNAL_AGE_REVIEW_REASON,
)

UNSAFE_KEY_FRAGMENTS = (
    "raw",
    "d" + "b",
    "net" + "work",
    "au" + "th",
    "cand" + "idate" + "_" + "id",
    "cand" + "idate" + "-" + "id",
    "mar" + "ket" + "_" + "id",
    "mar" + "ket" + "-" + "id",
    "mar" + "ket" + "_" + "slug",
    "mar" + "ket" + "-" + "slug",
    "slug",
    "que" + "stion",
    "source" + "_" + "url",
    "source" + "-" + "url",
    "source" + "_" + "text",
    "source" + "-" + "text",
    "d" + "sn",
    "ta" + "ble",
    "to" + "ken",
    "wal" + "let",
    "or" + "der",
    "tr" + "ade",
    "li" + "ve",
    "pos" + "ition",
    "siz" + "ing",
    "reco" + "mmend",
    "exe" + "cution",
    "secret",
    "credential",
    "api" + "_" + "key",
)
UNSAFE_VALUE_FRAGMENTS = (
    "http://",
    "https://",
    "://",
    "postgres://",
    "mysql://",
    "jdbc:",
    "net" + "work",
    "au" + "th",
    "cand" + "idate",
    "mar" + "ket-alpha",
    "mar" + "ket" + "_" + "id",
    "mar" + "ket" + "_" + "slug",
    "que" + "stion",
    "source" + "_" + "url",
    "source" + "_" + "text",
    "d" + "sn",
    "ta" + "ble=",
    "db.",
    "to" + "ken",
    "wal" + "let",
    "or" + "der",
    "tr" + "ade",
    "li" + "ve",
    "pos" + "ition",
    "siz" + "ing",
    "reco" + "mmend",
    "exe" + "cution",
    "secret",
    "credential",
    "api" + "_" + "key",
)
PUBLIC_REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "mean_quality_drop",
        "mean_decay_pressure_score",
        "mean_decay_adjusted_quality_score",
        "lowest_decay_adjusted_quality_score",
        "highest_quality_drop",
        "status",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
PUBLIC_REPORT_DECIMAL_KEYS = frozenset(
    (
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "mean_quality_drop",
        "mean_decay_pressure_score",
        "mean_decay_adjusted_quality_score",
        "lowest_decay_adjusted_quality_score",
        "highest_quality_drop",
    ),
)
PUBLIC_ROW_PAYLOAD_KEYS = frozenset(
    (
        "aggregate_row_number",
        "signal_hash",
        "signal_age_seconds",
        "signal_age_pressure",
        "baseline_quality_score",
        "current_quality_score",
        "quality_drop",
        "baseline_confidence_score",
        "current_confidence_score",
        "confidence_drop",
        "evidence_freshness_score",
        "calibration_score",
        "disagreement_pressure",
        "review_latency_pressure",
        "decay_pressure_score",
        "decay_adjusted_quality_score",
        "status",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
PUBLIC_ROW_DECIMAL_KEYS = frozenset(
    (
        "aggregate_row_number",
        "signal_age_seconds",
        "signal_age_pressure",
        "baseline_quality_score",
        "current_quality_score",
        "quality_drop",
        "baseline_confidence_score",
        "current_confidence_score",
        "confidence_drop",
        "evidence_freshness_score",
        "calibration_score",
        "disagreement_pressure",
        "review_latency_pressure",
        "decay_pressure_score",
        "decay_adjusted_quality_score",
    ),
)
PUBLIC_REASON_CODE_COUNT_ALLOWED = ROW_REASON_CODES + (REPORT_NO_INPUTS_REASON,)


@dataclass(frozen=True)
class ResearchStrategyTeamSignalQualityDecayConfig:
    config_version: str
    fresh_signal_age_seconds: Decimal
    stale_signal_age_seconds: Decimal
    watch_quality_drop: Decimal
    block_quality_drop: Decimal
    min_pass_current_quality_score: Decimal
    min_watch_current_quality_score: Decimal
    min_pass_decay_adjusted_quality_score: Decimal
    min_watch_decay_adjusted_quality_score: Decimal
    max_pass_decay_pressure_score: Decimal
    max_watch_decay_pressure_score: Decimal
    min_pass_evidence_freshness_score: Decimal
    min_watch_evidence_freshness_score: Decimal
    min_pass_calibration_score: Decimal
    min_watch_calibration_score: Decimal
    max_pass_disagreement_pressure: Decimal
    max_watch_disagreement_pressure: Decimal
    max_pass_review_latency_pressure: Decimal
    max_watch_review_latency_pressure: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTeamSignalQualityDecayConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_TEAM_SIGNAL_QUALITY_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("fresh_signal_age_seconds", "stale_signal_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_quality_drop",
            "block_quality_drop",
            "min_pass_current_quality_score",
            "min_watch_current_quality_score",
            "min_pass_decay_adjusted_quality_score",
            "min_watch_decay_adjusted_quality_score",
            "max_pass_decay_pressure_score",
            "max_watch_decay_pressure_score",
            "min_pass_evidence_freshness_score",
            "min_watch_evidence_freshness_score",
            "min_pass_calibration_score",
            "min_watch_calibration_score",
            "max_pass_disagreement_pressure",
            "max_watch_disagreement_pressure",
            "max_pass_review_latency_pressure",
            "max_watch_review_latency_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_age_threshold_pair(
            "signal age threshold",
            self.fresh_signal_age_seconds,
            self.stale_signal_age_seconds,
        )
        _require_max_threshold_pair(
            "quality drop threshold",
            self.watch_quality_drop,
            self.block_quality_drop,
        )
        _require_min_threshold_pair(
            "current quality threshold",
            self.min_watch_current_quality_score,
            self.min_pass_current_quality_score,
        )
        _require_min_threshold_pair(
            "adjusted quality threshold",
            self.min_watch_decay_adjusted_quality_score,
            self.min_pass_decay_adjusted_quality_score,
        )
        _require_max_threshold_pair(
            "decay pressure threshold",
            self.max_pass_decay_pressure_score,
            self.max_watch_decay_pressure_score,
        )
        _require_min_threshold_pair(
            "evidence threshold",
            self.min_watch_evidence_freshness_score,
            self.min_pass_evidence_freshness_score,
        )
        _require_min_threshold_pair(
            "calibration threshold",
            self.min_watch_calibration_score,
            self.min_pass_calibration_score,
        )
        _require_max_threshold_pair(
            "disagreement threshold",
            self.max_pass_disagreement_pressure,
            self.max_watch_disagreement_pressure,
        )
        _require_max_threshold_pair(
            "latency threshold",
            self.max_pass_review_latency_pressure,
            self.max_watch_review_latency_pressure,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyTeamSignalQualityDecayInput:
    signal_ref: str
    observed_at: datetime
    baseline_quality_score: Decimal
    current_quality_score: Decimal
    baseline_confidence_score: Decimal
    current_confidence_score: Decimal
    evidence_freshness_score: Decimal
    calibration_score: Decimal
    disagreement_pressure: Decimal
    review_latency_pressure: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTeamSignalQualityDecayInput, "input")
        _require_private_ref("signal_ref", self.signal_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "baseline_quality_score",
            "current_quality_score",
            "baseline_confidence_score",
            "current_confidence_score",
            "evidence_freshness_score",
            "calibration_score",
            "disagreement_pressure",
            "review_latency_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyTeamSignalQualityDecayRow:
    aggregate_row_number: Decimal
    signal_hash: str
    signal_age_seconds: Decimal
    signal_age_pressure: Decimal
    baseline_quality_score: Decimal
    current_quality_score: Decimal
    quality_drop: Decimal
    baseline_confidence_score: Decimal
    current_confidence_score: Decimal
    confidence_drop: Decimal
    evidence_freshness_score: Decimal
    calibration_score: Decimal
    disagreement_pressure: Decimal
    review_latency_pressure: Decimal
    decay_pressure_score: Decimal
    decay_adjusted_quality_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTeamSignalQualityDecayRow, "row")
        object.__setattr__(
            self,
            "aggregate_row_number",
            _normalize_positive_count("aggregate_row_number", self.aggregate_row_number),
        )
        _require_sha256_digest("signal_hash", self.signal_hash)
        object.__setattr__(
            self,
            "signal_age_seconds",
            _normalize_nonnegative_decimal("signal_age_seconds", self.signal_age_seconds),
        )
        for field_name in (
            "signal_age_pressure",
            "baseline_quality_score",
            "current_quality_score",
            "quality_drop",
            "baseline_confidence_score",
            "current_confidence_score",
            "confidence_drop",
            "evidence_freshness_score",
            "calibration_score",
            "disagreement_pressure",
            "review_latency_pressure",
            "decay_pressure_score",
            "decay_adjusted_quality_score",
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
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchStrategyTeamSignalQualityDecayReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_quality_drop: Decimal
    mean_decay_pressure_score: Decimal
    mean_decay_adjusted_quality_score: Decimal
    lowest_decay_adjusted_quality_score: Decimal
    highest_quality_drop: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    rows: tuple[ResearchStrategyTeamSignalQualityDecayRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTeamSignalQualityDecayReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_quality_drop",
            "mean_decay_pressure_score",
            "mean_decay_adjusted_quality_score",
            "lowest_decay_adjusted_quality_score",
            "highest_quality_drop",
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


def build_research_strategy_team_signal_quality_decay_report(
    inputs: Iterable[ResearchStrategyTeamSignalQualityDecayInput],
    *,
    config: ResearchStrategyTeamSignalQualityDecayConfig,
    generated_at: datetime,
) -> ResearchStrategyTeamSignalQualityDecayReport:
    if type(config) is not ResearchStrategyTeamSignalQualityDecayConfig:
        raise ValueError("config must be a ResearchStrategyTeamSignalQualityDecayConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    prepared_rows = tuple(
        sorted(
            (
                _prepare_row(value, config=config, generated_at=generated_at_utc)
                for value in normalized_inputs
            ),
            key=_prepared_row_sort_key,
        ),
    )
    rows = tuple(
        _row_from_prepared(value, aggregate_row_number=_count(index))
        for index, value in enumerate(prepared_rows, start=1)
    )
    return ResearchStrategyTeamSignalQualityDecayReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        row_count=_count(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        mean_quality_drop=_mean(tuple(row.quality_drop for row in rows)),
        mean_decay_pressure_score=_mean(tuple(row.decay_pressure_score for row in rows)),
        mean_decay_adjusted_quality_score=_mean(
            tuple(row.decay_adjusted_quality_score for row in rows),
        ),
        lowest_decay_adjusted_quality_score=min(
            (row.decay_adjusted_quality_score for row in rows),
            default=ZERO,
        ),
        highest_quality_drop=max((row.quality_drop for row in rows), default=ZERO),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_team_signal_quality_decay_report_payload(
    report: ResearchStrategyTeamSignalQualityDecayReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyTeamSignalQualityDecayReport:
        _require_hard_flags("report", report)
        _verify_report_integrity(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        _validate_public_payload_values("payload", report)
        _validate_public_payload_schema(report)
        _verify_public_payload_integrity(report)
        _verify_public_payload_row_integrity(report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchStrategyTeamSignalQualityDecayReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_TEAM_SIGNAL_QUALITY_DECAY_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_TEAM_SIGNAL_QUALITY_DECAY_STATUSES",
    "ResearchStrategyTeamSignalQualityDecayConfig",
    "ResearchStrategyTeamSignalQualityDecayInput",
    "ResearchStrategyTeamSignalQualityDecayRow",
    "ResearchStrategyTeamSignalQualityDecayReport",
    "build_research_strategy_team_signal_quality_decay_report",
    "research_strategy_team_signal_quality_decay_report_payload",
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


@dataclass(frozen=True)
class _PreparedRow:
    signal_hash: str
    signal_age_seconds: Decimal
    signal_age_pressure: Decimal
    baseline_quality_score: Decimal
    current_quality_score: Decimal
    quality_drop: Decimal
    baseline_confidence_score: Decimal
    current_confidence_score: Decimal
    confidence_drop: Decimal
    evidence_freshness_score: Decimal
    calibration_score: Decimal
    disagreement_pressure: Decimal
    review_latency_pressure: Decimal
    decay_pressure_score: Decimal
    decay_adjusted_quality_score: Decimal
    status: str
    reason_codes: tuple[str, ...]


def _prepare_row(
    value: ResearchStrategyTeamSignalQualityDecayInput,
    *,
    config: ResearchStrategyTeamSignalQualityDecayConfig,
    generated_at: datetime,
) -> _PreparedRow:
    if value.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    signal_age_seconds = _age_seconds(generated_at, value.observed_at)
    signal_age_pressure = _age_pressure(
        signal_age_seconds,
        fresh_age=config.fresh_signal_age_seconds,
        stale_age=config.stale_signal_age_seconds,
    )
    quality_drop = _quantize(
        _max_decimal(value.baseline_quality_score - value.current_quality_score, ZERO),
    )
    confidence_drop = _quantize(
        _max_decimal(value.baseline_confidence_score - value.current_confidence_score, ZERO),
    )
    decay_pressure_score = _decay_pressure_score(
        signal_age_pressure=signal_age_pressure,
        quality_drop=quality_drop,
        confidence_drop=confidence_drop,
        evidence_freshness_score=value.evidence_freshness_score,
        calibration_score=value.calibration_score,
        disagreement_pressure=value.disagreement_pressure,
        review_latency_pressure=value.review_latency_pressure,
    )
    adjusted_quality = _quantize(value.current_quality_score * (ONE - decay_pressure_score))
    reason_codes = _row_reason_codes(
        quality_drop=quality_drop,
        current_quality_score=value.current_quality_score,
        evidence_freshness_score=value.evidence_freshness_score,
        calibration_score=value.calibration_score,
        disagreement_pressure=value.disagreement_pressure,
        review_latency_pressure=value.review_latency_pressure,
        decay_pressure_score=decay_pressure_score,
        decay_adjusted_quality_score=adjusted_quality,
        signal_age_pressure=signal_age_pressure,
        config=config,
    )
    status = _row_status(reason_codes)
    return _PreparedRow(
        signal_hash=_signal_hash(value.signal_ref),
        signal_age_seconds=signal_age_seconds,
        signal_age_pressure=signal_age_pressure,
        baseline_quality_score=value.baseline_quality_score,
        current_quality_score=value.current_quality_score,
        quality_drop=quality_drop,
        baseline_confidence_score=value.baseline_confidence_score,
        current_confidence_score=value.current_confidence_score,
        confidence_drop=confidence_drop,
        evidence_freshness_score=value.evidence_freshness_score,
        calibration_score=value.calibration_score,
        disagreement_pressure=value.disagreement_pressure,
        review_latency_pressure=value.review_latency_pressure,
        decay_pressure_score=decay_pressure_score,
        decay_adjusted_quality_score=adjusted_quality,
        status=status,
        reason_codes=reason_codes,
    )


def _row_from_prepared(
    value: _PreparedRow,
    *,
    aggregate_row_number: Decimal,
) -> ResearchStrategyTeamSignalQualityDecayRow:
    return ResearchStrategyTeamSignalQualityDecayRow(
        aggregate_row_number=aggregate_row_number,
        signal_hash=value.signal_hash,
        signal_age_seconds=value.signal_age_seconds,
        signal_age_pressure=value.signal_age_pressure,
        baseline_quality_score=value.baseline_quality_score,
        current_quality_score=value.current_quality_score,
        quality_drop=value.quality_drop,
        baseline_confidence_score=value.baseline_confidence_score,
        current_confidence_score=value.current_confidence_score,
        confidence_drop=value.confidence_drop,
        evidence_freshness_score=value.evidence_freshness_score,
        calibration_score=value.calibration_score,
        disagreement_pressure=value.disagreement_pressure,
        review_latency_pressure=value.review_latency_pressure,
        decay_pressure_score=value.decay_pressure_score,
        decay_adjusted_quality_score=value.decay_adjusted_quality_score,
        status=value.status,
        reason_codes=value.reason_codes,
    )


def _row_reason_codes(
    *,
    quality_drop: Decimal,
    current_quality_score: Decimal,
    evidence_freshness_score: Decimal,
    calibration_score: Decimal,
    disagreement_pressure: Decimal,
    review_latency_pressure: Decimal,
    decay_pressure_score: Decimal,
    decay_adjusted_quality_score: Decimal,
    signal_age_pressure: Decimal,
    config: ResearchStrategyTeamSignalQualityDecayConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if quality_drop >= config.block_quality_drop:
        codes.append(QUALITY_DROP_BLOCK_REASON)
    elif quality_drop >= config.watch_quality_drop:
        codes.append(QUALITY_DROP_WATCH_REASON)
    if current_quality_score < config.min_watch_current_quality_score:
        codes.append(CURRENT_QUALITY_BLOCK_REASON)
    elif current_quality_score < config.min_pass_current_quality_score:
        codes.append(CURRENT_QUALITY_WATCH_REASON)
    if evidence_freshness_score < config.min_watch_evidence_freshness_score:
        codes.append(EVIDENCE_BLOCK_REASON)
    elif evidence_freshness_score < config.min_pass_evidence_freshness_score:
        codes.append(EVIDENCE_WATCH_REASON)
    if calibration_score < config.min_watch_calibration_score:
        codes.append(CALIBRATION_BLOCK_REASON)
    elif calibration_score < config.min_pass_calibration_score:
        codes.append(CALIBRATION_WATCH_REASON)
    if disagreement_pressure > config.max_watch_disagreement_pressure:
        codes.append(DISAGREEMENT_BLOCK_REASON)
    elif disagreement_pressure > config.max_pass_disagreement_pressure:
        codes.append(DISAGREEMENT_WATCH_REASON)
    if review_latency_pressure > config.max_watch_review_latency_pressure:
        codes.append(LATENCY_BLOCK_REASON)
    elif review_latency_pressure > config.max_pass_review_latency_pressure:
        codes.append(LATENCY_WATCH_REASON)
    if decay_pressure_score > config.max_watch_decay_pressure_score:
        codes.append(DECAY_PRESSURE_BLOCK_REASON)
    elif decay_pressure_score > config.max_pass_decay_pressure_score:
        codes.append(DECAY_PRESSURE_WATCH_REASON)
    if decay_adjusted_quality_score < config.min_watch_decay_adjusted_quality_score:
        codes.append(ADJUSTED_QUALITY_BLOCK_REASON)
    elif decay_adjusted_quality_score < config.min_pass_decay_adjusted_quality_score:
        codes.append(ADJUSTED_QUALITY_WATCH_REASON)
    if signal_age_pressure >= ONE:
        codes.append(SIGNAL_AGE_BLOCK_REASON)
    elif signal_age_pressure > ZERO:
        codes.append(SIGNAL_AGE_WATCH_REASON)
    if not codes:
        return (ROW_PASS_REASON,)
    return _normalize_reason_codes("reason_codes", tuple(sorted(codes)), ROW_REASON_CODES)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return STATUS_BLOCK
    if reason_codes != (ROW_PASS_REASON,):
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(rows: tuple[ResearchStrategyTeamSignalQualityDecayRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchStrategyTeamSignalQualityDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (REPORT_BLOCK_REASON, REPORT_NO_INPUTS_REASON)
    status = _report_status(rows)
    codes: list[str] = [
        {
            STATUS_PASS: REPORT_PASS_REASON,
            STATUS_WATCH: REPORT_WATCH_REASON,
            STATUS_BLOCK: REPORT_BLOCK_REASON,
        }[status],
    ]
    review_pairs = (
        ((QUALITY_DROP_BLOCK_REASON, QUALITY_DROP_WATCH_REASON), QUALITY_DROP_REVIEW_REASON),
        (
            (CURRENT_QUALITY_BLOCK_REASON, CURRENT_QUALITY_WATCH_REASON),
            CURRENT_QUALITY_REVIEW_REASON,
        ),
        ((EVIDENCE_BLOCK_REASON, EVIDENCE_WATCH_REASON), EVIDENCE_REVIEW_REASON),
        ((CALIBRATION_BLOCK_REASON, CALIBRATION_WATCH_REASON), CALIBRATION_REVIEW_REASON),
        (
            (DISAGREEMENT_BLOCK_REASON, DISAGREEMENT_WATCH_REASON),
            DISAGREEMENT_REVIEW_REASON,
        ),
        ((LATENCY_BLOCK_REASON, LATENCY_WATCH_REASON), LATENCY_REVIEW_REASON),
        (
            (DECAY_PRESSURE_BLOCK_REASON, DECAY_PRESSURE_WATCH_REASON),
            DECAY_PRESSURE_REVIEW_REASON,
        ),
        (
            (ADJUSTED_QUALITY_BLOCK_REASON, ADJUSTED_QUALITY_WATCH_REASON),
            ADJUSTED_QUALITY_REVIEW_REASON,
        ),
        ((SIGNAL_AGE_BLOCK_REASON, SIGNAL_AGE_WATCH_REASON), SIGNAL_AGE_REVIEW_REASON),
    )
    for row_reasons, report_reason in review_pairs:
        if any(any(reason in row.reason_codes for reason in row_reasons) for row in rows):
            codes.append(report_reason)
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _prepared_row_sort_key(value: _PreparedRow) -> tuple[int, Decimal, str]:
    return (
        {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value.status],
        -value.decay_pressure_score,
        value.signal_hash,
    )


def _normalize_inputs(
    value: Iterable[ResearchStrategyTeamSignalQualityDecayInput],
) -> tuple[ResearchStrategyTeamSignalQualityDecayInput, ...]:
    if isinstance(value, (str, bytes, dict)):
        raise ValueError("inputs must be an iterable of input rows")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyTeamSignalQualityDecayInput:
            raise ValueError("inputs must contain ResearchStrategyTeamSignalQualityDecayInput")
        _require_hard_flags("input", row)
        if row.signal_ref in seen:
            raise ValueError("duplicate signal_ref values are not allowed")
        seen.add(row.signal_ref)
    return rows


def _normalize_rows(
    value: object,
) -> tuple[ResearchStrategyTeamSignalQualityDecayRow, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    rows = tuple(value)
    seen_numbers: set[Decimal] = set()
    seen_hashes: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyTeamSignalQualityDecayRow:
            raise ValueError("rows must contain ResearchStrategyTeamSignalQualityDecayRow")
        _require_hard_flags("row", row)
        if row.aggregate_row_number in seen_numbers:
            raise ValueError("aggregate_row_number values must be unique")
        if row.signal_hash in seen_hashes:
            raise ValueError("signal_hash values must be unique")
        seen_numbers.add(row.aggregate_row_number)
        seen_hashes.add(row.signal_hash)
    return rows


def _normalize_reason_code_counts(value: object) -> tuple[tuple[str, Decimal], ...]:
    if type(value) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    rows = tuple(value)
    normalized: list[tuple[str, Decimal]] = []
    seen: set[str] = set()
    for item in rows:
        if type(item) not in (tuple, list) or len(item) != 2:
            raise ValueError("reason_code_counts must contain reason/count pairs")
        reason_code = item[0]
        count = _normalize_nonnegative_count("reason_code_count", item[1])
        _require_reason_code("reason_code", reason_code)
        if reason_code in seen:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen.add(reason_code)
        normalized.append((reason_code, count))
    result = tuple(sorted(normalized, key=lambda item: item[0]))
    if tuple(normalized) != result:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return result


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategyTeamSignalQualityDecayRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    if not rows:
        counts[REPORT_NO_INPUTS_REASON] = ONE
    return tuple((reason, count) for reason, count in sorted(counts.items()))


def _status_count(
    rows: tuple[ResearchStrategyTeamSignalQualityDecayRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _validate_row_consistency(row: ResearchStrategyTeamSignalQualityDecayRow) -> None:
    if row.quality_drop != _quantize(
        _max_decimal(row.baseline_quality_score - row.current_quality_score, ZERO),
    ):
        raise ValueError("quality_drop must match row scores")
    if row.confidence_drop != _quantize(
        _max_decimal(row.baseline_confidence_score - row.current_confidence_score, ZERO),
    ):
        raise ValueError("confidence_drop must match row scores")
    expected_decay = _decay_pressure_score(
        signal_age_pressure=row.signal_age_pressure,
        quality_drop=row.quality_drop,
        confidence_drop=row.confidence_drop,
        evidence_freshness_score=row.evidence_freshness_score,
        calibration_score=row.calibration_score,
        disagreement_pressure=row.disagreement_pressure,
        review_latency_pressure=row.review_latency_pressure,
    )
    if row.decay_pressure_score != expected_decay:
        raise ValueError("decay_pressure_score must match row components")
    expected_adjusted = _quantize(row.current_quality_score * (ONE - row.decay_pressure_score))
    if row.decay_adjusted_quality_score != expected_adjusted:
        raise ValueError("decay_adjusted_quality_score must match row components")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchStrategyTeamSignalQualityDecayReport,
) -> None:
    expected_values = {
        "row_count": _count(len(report.rows)),
        "pass_count": _status_count(report.rows, STATUS_PASS),
        "watch_count": _status_count(report.rows, STATUS_WATCH),
        "block_count": _status_count(report.rows, STATUS_BLOCK),
        "mean_quality_drop": _mean(tuple(row.quality_drop for row in report.rows)),
        "mean_decay_pressure_score": _mean(
            tuple(row.decay_pressure_score for row in report.rows),
        ),
        "mean_decay_adjusted_quality_score": _mean(
            tuple(row.decay_adjusted_quality_score for row in report.rows),
        ),
        "lowest_decay_adjusted_quality_score": min(
            (row.decay_adjusted_quality_score for row in report.rows),
            default=ZERO,
        ),
        "highest_quality_drop": max((row.quality_drop for row in report.rows), default=ZERO),
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _decay_pressure_score(
    *,
    signal_age_pressure: Decimal,
    quality_drop: Decimal,
    confidence_drop: Decimal,
    evidence_freshness_score: Decimal,
    calibration_score: Decimal,
    disagreement_pressure: Decimal,
    review_latency_pressure: Decimal,
) -> Decimal:
    return _mean(
        (
            signal_age_pressure,
            quality_drop,
            confidence_drop,
            ONE - evidence_freshness_score,
            ONE - calibration_score,
            disagreement_pressure,
            review_latency_pressure,
        ),
    )


def _age_pressure(
    age_seconds: Decimal,
    *,
    fresh_age: Decimal,
    stale_age: Decimal,
) -> Decimal:
    if age_seconds <= fresh_age:
        return ZERO
    if age_seconds >= stale_age:
        return ONE
    return _quantize((age_seconds - fresh_age) / (stale_age - fresh_age))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    generated = _as_utc("generated_at", generated_at)
    observed = _as_utc("observed_at", observed_at)
    if observed > generated:
        raise ValueError("observed_at must not be after generated_at")
    delta = generated - observed
    return _quantize(
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
    )


def _signal_hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / _count(len(values)))


def _max_decimal(left: Decimal, right: Decimal) -> Decimal:
    if left >= right:
        return left
    return right


def _normalize_reason_codes(
    name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{name} must be a tuple or list")
    codes = tuple(value)
    if not codes:
        raise ValueError(f"{name} must not be empty")
    seen: set[str] = set()
    for code in codes:
        _require_reason_code("reason_code", code)
        if code not in allowed:
            raise ValueError(f"{name} contains an unsupported reason code")
        if code in seen:
            raise ValueError(f"{name} must be unique")
        seen.add(code)
    return codes


def _apply_or_verify_digest(value: object) -> None:
    current_digest = getattr(value, "derived_validation_digest")
    if current_digest == "":
        object.__setattr__(value, "derived_validation_digest", _digest_for_value(value))
        return
    _require_sha256_digest("derived_validation_digest", current_digest)
    if current_digest != _digest_for_value(value):
        raise ValueError("derived_validation_digest does not match payload")


def _digest_for_value(value: object) -> str:
    ready = _json_ready_without_digest(value)
    _reject_unsafe_public_payload("digest payload", ready)
    canonical_payload = dumps(
        ready,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical_payload.encode("utf-8")).hexdigest()


def _json_ready_without_digest(value: object) -> dict[str, Any]:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("digest value must be a dataclass instance")
    ready = _json_ready(asdict(value))
    if type(ready) is not dict:
        raise ValueError("digest payload must be a JSON object")
    ready.pop("derived_validation_digest", None)
    return ready


def _verify_report_integrity(report: ResearchStrategyTeamSignalQualityDecayReport) -> None:
    _require_sha256_digest("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _digest_for_value(report):
        raise ValueError("derived_validation_digest does not match payload")
    for row in report.rows:
        _require_sha256_digest("derived_validation_digest", row.derived_validation_digest)
        if row.derived_validation_digest != _digest_for_value(row):
            raise ValueError("derived_validation_digest does not match row payload")


def _verify_public_payload_integrity(payload: dict[str, Any]) -> None:
    expected_digest = payload.get("derived_validation_digest")
    if type(expected_digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _require_sha256_digest("derived_validation_digest", expected_digest)
    comparable = dict(payload)
    comparable.pop("derived_validation_digest", None)
    canonical_payload = dumps(
        comparable,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    actual_digest = sha256(canonical_payload.encode("utf-8")).hexdigest()
    if expected_digest != actual_digest:
        raise ValueError("derived_validation_digest does not match payload")


def _verify_public_payload_row_integrity(payload: dict[str, Any]) -> None:
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        expected_digest = row.get("derived_validation_digest")
        if type(expected_digest) is not str:
            raise ValueError("derived_validation_digest must be a string")
        _require_sha256_digest("derived_validation_digest", expected_digest)
        comparable = dict(row)
        comparable.pop("derived_validation_digest", None)
        canonical_payload = dumps(
            comparable,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        actual_digest = sha256(canonical_payload.encode("utf-8")).hexdigest()
        if expected_digest != actual_digest:
            raise ValueError("derived_validation_digest does not match row payload")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        return format(_quantize(value), "f")
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("payload contains unsupported value type")


def _validate_public_payload_values(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _validate_public_payload_values(key, item)
    elif isinstance(value, list):
        for item in value:
            _validate_public_payload_values(label, item)
    elif type(value) in (Decimal, int, float):
        raise ValueError(f"{label} must be JSON string encoded")
    elif type(value) not in (str, bool) and value is not None:
        raise ValueError(f"{label} contains unsupported value type")


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    _require_public_payload_keys("payload", payload, PUBLIC_REPORT_PAYLOAD_KEYS)
    if payload.get("config_version") != (
        DEFAULT_RESEARCH_STRATEGY_TEAM_SIGNAL_QUALITY_DECAY_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    for key in PUBLIC_REPORT_DECIMAL_KEYS:
        _validate_decimal_string(key, payload.get(key))
    _require_status("status", payload.get("status"))
    _validate_public_reason_codes(
        "reason_codes",
        payload.get("reason_codes"),
        REPORT_REASON_CODES,
    )
    _validate_public_reason_code_counts(payload.get("reason_code_counts"))
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        _validate_public_row_payload_schema(row)


def _validate_public_row_payload_schema(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("rows must contain JSON objects")
    _require_public_payload_keys("row", value, PUBLIC_ROW_PAYLOAD_KEYS)
    for key in PUBLIC_ROW_DECIMAL_KEYS:
        _validate_decimal_string(key, value.get(key))
    _require_sha256_digest("signal_hash", value.get("signal_hash"))
    _require_status("status", value.get("status"))
    _validate_public_reason_codes(
        "row.reason_codes",
        value.get("reason_codes"),
        ROW_REASON_CODES,
    )


def _require_public_payload_keys(
    label: str,
    payload: dict[str, Any],
    expected_keys: frozenset[str],
) -> None:
    actual_keys = set(payload)
    if actual_keys - expected_keys:
        raise ValueError(f"{label} contains unexpected public payload key")
    if expected_keys - actual_keys:
        raise ValueError(f"{label} is missing required public payload key")


def _validate_public_reason_codes(
    label: str,
    value: object,
    allowed: tuple[str, ...],
) -> None:
    if type(value) is not list:
        raise ValueError(f"{label} must be a list")
    if not value:
        raise ValueError(f"{label} must not be empty")
    seen: set[str] = set()
    for reason_code in value:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in allowed:
            raise ValueError(f"{label} contains an unsupported reason code")
        if reason_code in seen:
            raise ValueError(f"{label} must be unique")
        seen.add(reason_code)


def _validate_public_reason_code_counts(value: object) -> None:
    if type(value) is not list:
        raise ValueError("reason_code_counts must be a list")
    seen: set[str] = set()
    for item in value:
        if type(item) is not list or len(item) != 2:
            raise ValueError("reason_code_counts must contain reason/count pairs")
        reason_code = item[0]
        _require_reason_code("reason_code", reason_code)
        if reason_code not in PUBLIC_REASON_CODE_COUNT_ALLOWED:
            raise ValueError("reason_code_counts contains an unsupported reason code")
        if reason_code in seen:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen.add(reason_code)
        _validate_decimal_string("reason_code_count", item[1])


def _validate_decimal_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be JSON string encoded")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be decimal encoded") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{name} must be finite")
    if format(_quantize(decimal_value), "f") != value:
        raise ValueError(f"{name} must use six decimal places")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_key(label, field.name)
            _reject_unsafe_public_payload(field.name, getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _reject_unsafe_key(label, key)
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{key} must be True")
            _reject_unsafe_public_payload(key, item)
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_VALUE_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe public value")


def _reject_unsafe_key(label: str, key: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in UNSAFE_KEY_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public key")


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be integral")
    return normalized


def _normalize_positive_count(name: str, value: object) -> Decimal:
    normalized = _normalize_positive_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be integral")
    return normalized


def _normalize_probability(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between zero and one")
    return normalized


def _decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    try:
        return _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be quantizable") from exc


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_canonical_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{name} must not contain whitespace")
    return value


def _require_private_ref(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")
    return value


def _require_reason_code(name: str, value: object) -> str:
    _require_canonical_string(name, value)
    return value


def _require_status(name: str, value: object) -> None:
    if type(value) is not str or value not in RESEARCH_STRATEGY_TEAM_SIGNAL_QUALITY_DECAY_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_sha256_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a sha256 digest")


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{label}.{flag_name} must be True")


def _require_age_threshold_pair(label: str, fresh_value: Decimal, stale_value: Decimal) -> None:
    if fresh_value >= stale_value:
        raise ValueError(f"{label} threshold must have fresh below stale")


def _require_min_threshold_pair(label: str, watch_value: Decimal, pass_value: Decimal) -> None:
    if watch_value > pass_value:
        raise ValueError(f"{label} threshold watch value must not exceed pass value")


def _require_max_threshold_pair(label: str, pass_value: Decimal, watch_value: Decimal) -> None:
    if pass_value > watch_value:
        raise ValueError(f"{label} threshold pass value must not exceed watch value")
