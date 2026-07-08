"""Deterministic report-only strategy signal quality scorecard."""

from __future__ import annotations

from dataclasses import InitVar, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_STRATEGY_SIGNAL_QUALITY_SCORECARD_CONFIG_VERSION = (
    "research-strategy-signal-quality-scorecard-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_EMPTY_INPUT = "empty_input"
REASON_EVIDENCE_STRENGTH_BLOCK = "evidence_strength_block"
REASON_TIMELINESS_BLOCK = "timeliness_block"
REASON_CONFLICT_RATE_BLOCK = "conflict_rate_block"
REASON_CALIBRATION_ERROR_BLOCK = "calibration_error_block"
REASON_QUALITY_SCORE_BLOCK = "quality_score_block"
REASON_EVIDENCE_STRENGTH_WATCH = "evidence_strength_watch"
REASON_TIMELINESS_WATCH = "timeliness_watch"
REASON_CONFLICT_RATE_WATCH = "conflict_rate_watch"
REASON_CALIBRATION_ERROR_WATCH = "calibration_error_watch"
REASON_CALIBRATION_SAMPLE_WATCH = "calibration_sample_watch"
REASON_QUALITY_SCORE_WATCH = "quality_score_watch"
REASON_SIGNAL_QUALITY_PASS = "signal_quality_pass"

_REASON_CODE_SEQUENCE = (
    REASON_EMPTY_INPUT,
    REASON_EVIDENCE_STRENGTH_BLOCK,
    REASON_TIMELINESS_BLOCK,
    REASON_CONFLICT_RATE_BLOCK,
    REASON_CALIBRATION_ERROR_BLOCK,
    REASON_QUALITY_SCORE_BLOCK,
    REASON_EVIDENCE_STRENGTH_WATCH,
    REASON_TIMELINESS_WATCH,
    REASON_CONFLICT_RATE_WATCH,
    REASON_CALIBRATION_ERROR_WATCH,
    REASON_CALIBRATION_SAMPLE_WATCH,
    REASON_QUALITY_SCORE_WATCH,
    REASON_SIGNAL_QUALITY_PASS,
)
_ROW_REASON_CODE_SEQUENCE = tuple(
    reason_code
    for reason_code in _REASON_CODE_SEQUENCE
    if reason_code != REASON_EMPTY_INPUT
)
_BLOCK_REASON_CODES = frozenset(
    (
        REASON_EVIDENCE_STRENGTH_BLOCK,
        REASON_TIMELINESS_BLOCK,
        REASON_CONFLICT_RATE_BLOCK,
        REASON_CALIBRATION_ERROR_BLOCK,
        REASON_QUALITY_SCORE_BLOCK,
    ),
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_FIELD = "derived_validation_digest"
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_SIGNAL_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_STATUS_VALUES = frozenset((STATUS_PASS, STATUS_WATCH, STATUS_BLOCK))
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "source_ref",
    "source-ref",
    "source ref",
    "source_url",
    "source-url",
    "source url",
    "source_text",
    "source-text",
    "source text",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommendation",
    "http://",
    "https://",
    "://",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchStrategySignalQualityScorecardConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_STRATEGY_SIGNAL_QUALITY_SCORECARD_CONFIG_VERSION
    min_evidence_strength_score: Decimal = Decimal("0.600000")
    pass_evidence_strength_score: Decimal = Decimal("0.800000")
    watch_freshness_age_hours: Decimal = Decimal("24.000000")
    block_freshness_age_hours: Decimal = Decimal("72.000000")
    watch_conflict_rate: Decimal = Decimal("0.250000")
    block_conflict_rate: Decimal = Decimal("0.600000")
    watch_calibration_error_rate: Decimal = Decimal("0.250000")
    block_calibration_error_rate: Decimal = Decimal("0.400000")
    min_calibration_sample_count: Decimal = Decimal("5.000000")
    pass_quality_score: Decimal = Decimal("0.750000")
    watch_quality_score: Decimal = Decimal("0.500000")
    evidence_strength_weight: Decimal = Decimal("0.350000")
    timeliness_weight: Decimal = Decimal("0.250000")
    conflict_rate_weight: Decimal = Decimal("0.200000")
    calibration_history_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySignalQualityScorecardConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_RESEARCH_STRATEGY_SIGNAL_QUALITY_SCORECARD_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_evidence_strength_score",
            "pass_evidence_strength_score",
            "watch_conflict_rate",
            "block_conflict_rate",
            "watch_calibration_error_rate",
            "block_calibration_error_rate",
            "pass_quality_score",
            "watch_quality_score",
            "evidence_strength_weight",
            "timeliness_weight",
            "conflict_rate_weight",
            "calibration_history_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_freshness_age_hours",
            "block_freshness_age_hours",
            "min_calibration_sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_evidence_strength_score > self.pass_evidence_strength_score:
            raise ValueError(
                "min_evidence_strength_score must not exceed pass_evidence_strength_score",
            )
        if self.watch_freshness_age_hours > self.block_freshness_age_hours:
            raise ValueError(
                "watch_freshness_age_hours must not exceed block_freshness_age_hours",
            )
        if self.watch_conflict_rate > self.block_conflict_rate:
            raise ValueError("watch_conflict_rate must not exceed block_conflict_rate")
        if self.watch_calibration_error_rate > self.block_calibration_error_rate:
            raise ValueError(
                "watch_calibration_error_rate must not exceed block_calibration_error_rate",
            )
        if self.pass_quality_score <= self.watch_quality_score:
            raise ValueError("pass_quality_score must exceed watch_quality_score")
        weight_sum = _quantize(
            self.evidence_strength_weight
            + self.timeliness_weight
            + self.conflict_rate_weight
            + self.calibration_history_weight,
        )
        if weight_sum != _ONE:
            raise ValueError("quality score weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategySignalQualityInput(_FinalPublicDataclass):
    signal_key: str
    evidence_strength_score: Decimal
    evidence_freshness_age_hours: Decimal
    conflict_rate: Decimal
    calibration_error_rate: Decimal
    calibration_sample_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySignalQualityInput, "input")
        object.__setattr__(self, "signal_key", _require_private_key("signal_key", self.signal_key))
        for field_name in (
            "evidence_strength_score",
            "conflict_rate",
            "calibration_error_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_freshness_age_hours",
            _require_nonnegative_decimal(
                "evidence_freshness_age_hours",
                self.evidence_freshness_age_hours,
            ),
        )
        object.__setattr__(
            self,
            "calibration_sample_count",
            _require_nonnegative_count_decimal(
                "calibration_sample_count",
                self.calibration_sample_count,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategySignalQualityPublicNote(_FinalPublicDataclass):
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySignalQualityPublicNote, "public note")
        object.__setattr__(self, "key", _require_public_identifier("key", self.key))
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public note", self)
        _reject_unsafe_public_payload("public note", self)


@dataclass(frozen=True)
class ResearchStrategySignalQualityRow(_FinalPublicDataclass):
    signal_digest: str
    evidence_strength_score: Decimal
    evidence_freshness_age_hours: Decimal
    timeliness_score: Decimal
    conflict_rate: Decimal
    calibration_error_rate: Decimal
    calibration_sample_count: Decimal
    calibration_history_score: Decimal
    quality_score: Decimal
    human_review_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchStrategySignalQualityScorecardConfig | None] = None

    def __post_init__(
        self,
        validation_config: ResearchStrategySignalQualityScorecardConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchStrategySignalQualityRow, "row")
        object.__setattr__(
            self,
            "signal_digest",
            _require_signal_digest("signal_digest", self.signal_digest),
        )
        for field_name in (
            "evidence_strength_score",
            "timeliness_score",
            "conflict_rate",
            "calibration_error_rate",
            "calibration_history_score",
            "quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_freshness_age_hours",
            _require_nonnegative_decimal(
                "evidence_freshness_age_hours",
                self.evidence_freshness_age_hours,
            ),
        )
        object.__setattr__(
            self,
            "calibration_sample_count",
            _require_nonnegative_count_decimal(
                "calibration_sample_count",
                self.calibration_sample_count,
            ),
        )
        _require_status("human_review_status", self.human_review_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self, validation_config)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategySignalQualityReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySignalQualityReasonCodeCount, "reason count")
        _require_reason_code("reason_code", self.reason_code, _REASON_CODE_SEQUENCE)
        object.__setattr__(self, "count", _require_nonnegative_count_decimal("count", self.count))
        object.__setattr__(self, "row_ratio", _require_ratio_decimal("row_ratio", self.row_ratio))
        _require_hard_flags("reason count", self)
        _reject_unsafe_public_payload("reason count", self)


@dataclass(frozen=True)
class ResearchStrategySignalQualityReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    human_review_status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_quality_score: Decimal
    min_evidence_strength_score: Decimal
    max_freshness_age_hours: Decimal
    max_conflict_rate: Decimal
    max_calibration_error_rate: Decimal
    min_calibration_sample_count: Decimal
    rows: tuple[ResearchStrategySignalQualityRow, ...]
    reason_code_counts: tuple[ResearchStrategySignalQualityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    public_notes: tuple[ResearchStrategySignalQualityPublicNote, ...] = ()
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySignalQualityReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_RESEARCH_STRATEGY_SIGNAL_QUALITY_SCORECARD_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_status("human_review_status", self.human_review_status)
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "min_calibration_sample_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_quality_score",
            "min_evidence_strength_score",
            "max_conflict_rate",
            "max_calibration_error_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_freshness_age_hours",
            _require_nonnegative_decimal(
                "max_freshness_age_hours",
                self.max_freshness_age_hours,
            ),
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
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "public_notes", _normalize_public_notes(self.public_notes))
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, _DIGEST_FIELD, expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest mismatch")
        _require_digest(_DIGEST_FIELD, self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, object]:
        return research_strategy_signal_quality_scorecard_payload(self)


def build_research_strategy_signal_quality_scorecard(
    inputs: Sequence[ResearchStrategySignalQualityInput],
    *,
    generated_at: datetime,
    config: ResearchStrategySignalQualityScorecardConfig | None = None,
    public_notes: Sequence[ResearchStrategySignalQualityPublicNote] = (),
) -> ResearchStrategySignalQualityReport:
    """Build a pure paper-only scorecard for human review of signal quality."""

    cfg = config or ResearchStrategySignalQualityScorecardConfig()
    if type(cfg) is not ResearchStrategySignalQualityScorecardConfig:
        raise ValueError("config must be a ResearchStrategySignalQualityScorecardConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_for_input(row, cfg) for row in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not rows:
        reason_code_counts = (
            ResearchStrategySignalQualityReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
        reason_codes = (REASON_EMPTY_INPUT,)
    status = _report_status(rows)
    values: dict[str, object] = {
        "generated_at": report_time,
        "config_version": cfg.config_version,
        "human_review_status": status,
        "row_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, STATUS_PASS)),
        "watch_count": _decimal_count(_status_count(rows, STATUS_WATCH)),
        "block_count": _decimal_count(_status_count(rows, STATUS_BLOCK)),
        "average_quality_score": _average_ratio(tuple(row.quality_score for row in rows)),
        "min_evidence_strength_score": min(
            (row.evidence_strength_score for row in rows),
            default=_ZERO,
        ),
        "max_freshness_age_hours": max(
            (row.evidence_freshness_age_hours for row in rows),
            default=_ZERO,
        ),
        "max_conflict_rate": max((row.conflict_rate for row in rows), default=_ZERO),
        "max_calibration_error_rate": max(
            (row.calibration_error_rate for row in rows),
            default=_ZERO,
        ),
        "min_calibration_sample_count": min(
            (row.calibration_sample_count for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "public_notes": _normalize_public_notes(public_notes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategySignalQualityReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_signal_quality_scorecard_payload(
    value: ResearchStrategySignalQualityReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchStrategySignalQualityReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError("value must be a ResearchStrategySignalQualityReport or dict")
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_digest(payload)
    return payload


def _row_for_input(
    row: ResearchStrategySignalQualityInput,
    config: ResearchStrategySignalQualityScorecardConfig,
) -> ResearchStrategySignalQualityRow:
    timeliness_score = _timeliness_score(row.evidence_freshness_age_hours, config)
    calibration_history_score = _calibration_history_score(
        error_rate=row.calibration_error_rate,
        sample_count=row.calibration_sample_count,
        config=config,
    )
    quality_score = _quality_score(
        evidence_strength_score=row.evidence_strength_score,
        timeliness_score=timeliness_score,
        conflict_rate=row.conflict_rate,
        calibration_history_score=calibration_history_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        evidence_strength_score=row.evidence_strength_score,
        evidence_freshness_age_hours=row.evidence_freshness_age_hours,
        conflict_rate=row.conflict_rate,
        calibration_error_rate=row.calibration_error_rate,
        calibration_sample_count=row.calibration_sample_count,
        quality_score=quality_score,
        config=config,
    )
    return ResearchStrategySignalQualityRow(
        signal_digest=_signal_digest(row.signal_key),
        evidence_strength_score=row.evidence_strength_score,
        evidence_freshness_age_hours=row.evidence_freshness_age_hours,
        timeliness_score=timeliness_score,
        conflict_rate=row.conflict_rate,
        calibration_error_rate=row.calibration_error_rate,
        calibration_sample_count=row.calibration_sample_count,
        calibration_history_score=calibration_history_score,
        quality_score=quality_score,
        human_review_status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    *,
    evidence_strength_score: Decimal,
    evidence_freshness_age_hours: Decimal,
    conflict_rate: Decimal,
    calibration_error_rate: Decimal,
    calibration_sample_count: Decimal,
    quality_score: Decimal,
    config: ResearchStrategySignalQualityScorecardConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if evidence_strength_score < config.min_evidence_strength_score:
        reason_codes.append(REASON_EVIDENCE_STRENGTH_BLOCK)
    elif evidence_strength_score < config.pass_evidence_strength_score:
        reason_codes.append(REASON_EVIDENCE_STRENGTH_WATCH)
    if evidence_freshness_age_hours >= config.block_freshness_age_hours:
        reason_codes.append(REASON_TIMELINESS_BLOCK)
    elif evidence_freshness_age_hours > config.watch_freshness_age_hours:
        reason_codes.append(REASON_TIMELINESS_WATCH)
    if conflict_rate >= config.block_conflict_rate:
        reason_codes.append(REASON_CONFLICT_RATE_BLOCK)
    elif conflict_rate > config.watch_conflict_rate:
        reason_codes.append(REASON_CONFLICT_RATE_WATCH)
    if calibration_error_rate >= config.block_calibration_error_rate:
        reason_codes.append(REASON_CALIBRATION_ERROR_BLOCK)
    elif calibration_error_rate > config.watch_calibration_error_rate:
        reason_codes.append(REASON_CALIBRATION_ERROR_WATCH)
    if calibration_sample_count < config.min_calibration_sample_count:
        reason_codes.append(REASON_CALIBRATION_SAMPLE_WATCH)
    if quality_score < config.watch_quality_score:
        reason_codes.append(REASON_QUALITY_SCORE_BLOCK)
    elif quality_score < config.pass_quality_score:
        reason_codes.append(REASON_QUALITY_SCORE_WATCH)
    if not reason_codes:
        reason_codes.append(REASON_SIGNAL_QUALITY_PASS)
    return tuple(
        reason_code
        for reason_code in _ROW_REASON_CODE_SEQUENCE
        if reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if reason_codes == (REASON_SIGNAL_QUALITY_PASS,):
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(rows: tuple[ResearchStrategySignalQualityRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.human_review_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.human_review_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(rows: tuple[ResearchStrategySignalQualityRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.human_review_status == status)


def _row_sort_key(row: ResearchStrategySignalQualityRow) -> tuple[int, Decimal, str]:
    return (_status_rank(row.human_review_status), row.quality_score, row.signal_digest)


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchStrategySignalQualityRow, ...],
) -> tuple[ResearchStrategySignalQualityReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, _ZERO) + _ONE
    return tuple(
        ResearchStrategySignalQualityReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
            row_ratio=_ratio(counts[reason_code], total),
        )
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _timeliness_score(
    evidence_freshness_age_hours: Decimal,
    config: ResearchStrategySignalQualityScorecardConfig,
) -> Decimal:
    if evidence_freshness_age_hours >= config.block_freshness_age_hours:
        return _ZERO
    return _clamp_ratio(_ONE - (evidence_freshness_age_hours / config.block_freshness_age_hours))


def _calibration_history_score(
    *,
    error_rate: Decimal,
    sample_count: Decimal,
    config: ResearchStrategySignalQualityScorecardConfig,
) -> Decimal:
    sample_score = _clamp_ratio(sample_count / config.min_calibration_sample_count)
    error_score = _inverse_ratio(
        error_rate,
        block_threshold=config.block_calibration_error_rate,
    )
    return _average_ratio((sample_score, error_score))


def _quality_score(
    *,
    evidence_strength_score: Decimal,
    timeliness_score: Decimal,
    conflict_rate: Decimal,
    calibration_history_score: Decimal,
    config: ResearchStrategySignalQualityScorecardConfig,
) -> Decimal:
    conflict_quality_score = _clamp_ratio(_ONE - conflict_rate)
    return _clamp_ratio(
        evidence_strength_score * config.evidence_strength_weight
        + timeliness_score * config.timeliness_weight
        + conflict_quality_score * config.conflict_rate_weight
        + calibration_history_score * config.calibration_history_weight,
    )


def _inverse_ratio(value: Decimal, *, block_threshold: Decimal) -> Decimal:
    if block_threshold == _ZERO:
        return _ZERO if value > _ZERO else _ONE
    if value >= block_threshold:
        return _ZERO
    return _clamp_ratio(_ONE - (value / block_threshold))


def _validate_row(
    row: ResearchStrategySignalQualityRow,
    config: ResearchStrategySignalQualityScorecardConfig | None,
) -> None:
    if config is not None:
        if type(config) is not ResearchStrategySignalQualityScorecardConfig:
            raise ValueError(
                "validation_config must be a ResearchStrategySignalQualityScorecardConfig",
            )
        expected_timeliness = _timeliness_score(row.evidence_freshness_age_hours, config)
        if row.timeliness_score != expected_timeliness:
            raise ValueError("timeliness_score must match evidence_freshness_age_hours")
        expected_calibration = _calibration_history_score(
            error_rate=row.calibration_error_rate,
            sample_count=row.calibration_sample_count,
            config=config,
        )
        if row.calibration_history_score != expected_calibration:
            raise ValueError("calibration_history_score must match calibration inputs")
        expected_quality = _quality_score(
            evidence_strength_score=row.evidence_strength_score,
            timeliness_score=row.timeliness_score,
            conflict_rate=row.conflict_rate,
            calibration_history_score=row.calibration_history_score,
            config=config,
        )
        if row.quality_score != expected_quality:
            raise ValueError("quality_score must match component scores")
        expected_reasons = _row_reason_codes(
            evidence_strength_score=row.evidence_strength_score,
            evidence_freshness_age_hours=row.evidence_freshness_age_hours,
            conflict_rate=row.conflict_rate,
            calibration_error_rate=row.calibration_error_rate,
            calibration_sample_count=row.calibration_sample_count,
            quality_score=row.quality_score,
            config=config,
        )
        if row.reason_codes != expected_reasons:
            raise ValueError("reason_codes must match row inputs")
    if row.human_review_status != _row_status(row.reason_codes):
        raise ValueError("human_review_status must match reason_codes")
    if row.reason_codes == (REASON_SIGNAL_QUALITY_PASS,) and row.human_review_status != STATUS_PASS:
        raise ValueError("pass reason must map to pass status")


def _validate_report(report: ResearchStrategySignalQualityReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.average_quality_score != _average_ratio(tuple(row.quality_score for row in report.rows)):
        raise ValueError("average_quality_score must match rows")
    if report.min_evidence_strength_score != min(
        (row.evidence_strength_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_evidence_strength_score must match rows")
    if report.max_freshness_age_hours != max(
        (row.evidence_freshness_age_hours for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_freshness_age_hours must match rows")
    if report.max_conflict_rate != max((row.conflict_rate for row in report.rows), default=_ZERO):
        raise ValueError("max_conflict_rate must match rows")
    if report.max_calibration_error_rate != max(
        (row.calibration_error_rate for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_calibration_error_rate must match rows")
    if report.min_calibration_sample_count != min(
        (row.calibration_sample_count for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_calibration_sample_count must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            ResearchStrategySignalQualityReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
        expected_codes = (REASON_EMPTY_INPUT,)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    if report.human_review_status != _report_status(report.rows):
        raise ValueError("human_review_status must match rows")


def _normalize_inputs(
    inputs: Sequence[ResearchStrategySignalQualityInput],
) -> tuple[ResearchStrategySignalQualityInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategySignalQualityInput:
            raise ValueError("inputs must contain ResearchStrategySignalQualityInput")
        _require_hard_flags("input", row)
        digest = _signal_digest(row.signal_key)
        if digest in seen:
            raise ValueError("inputs must be unique by signal digest")
        seen.add(digest)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchStrategySignalQualityRow, ...],
) -> tuple[ResearchStrategySignalQualityRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategySignalQualityRow:
            raise ValueError("rows must contain ResearchStrategySignalQualityRow")
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")
    signal_digests = tuple(row.signal_digest for row in normalized)
    if len(set(signal_digests)) != len(signal_digests):
        raise ValueError("rows must have unique signal digests")
    return normalized


def _normalize_reason_code_counts(
    rows: tuple[ResearchStrategySignalQualityReasonCodeCount, ...],
) -> tuple[ResearchStrategySignalQualityReasonCodeCount, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategySignalQualityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchStrategySignalQualityReasonCodeCount",
            )
        _require_hard_flags("reason count", row)
    expected_order = tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in tuple(row.reason_code for row in normalized)
    )
    if tuple(row.reason_code for row in normalized) != expected_order:
        raise ValueError("reason_code_counts must use deterministic ordering")
    if len(set(row.reason_code for row in normalized)) != len(normalized):
        raise ValueError("reason_code_counts must not contain duplicates")
    return normalized


def _normalize_public_notes(
    public_notes: Sequence[ResearchStrategySignalQualityPublicNote],
) -> tuple[ResearchStrategySignalQualityPublicNote, ...]:
    if type(public_notes) not in (list, tuple):
        raise ValueError("public_notes must be a list or tuple")
    normalized = tuple(public_notes)
    for note in normalized:
        if type(note) is not ResearchStrategySignalQualityPublicNote:
            raise ValueError("public_notes must contain ResearchStrategySignalQualityPublicNote")
        _require_hard_flags("public note", note)
    keys = tuple(note.key for note in normalized)
    if keys != tuple(sorted(keys)):
        raise ValueError("public_notes must be sorted by key")
    if len(set(keys)) != len(keys):
        raise ValueError("public_notes must have unique keys")
    return normalized


def _normalize_row_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, _ROW_REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in _ROW_REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and deterministic")
    if REASON_SIGNAL_QUALITY_PASS in value and len(value) != 1:
        raise ValueError("reason_codes cannot mix pass with risk reasons")
    return normalized


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, _REASON_CODE_SEQUENCE)
    normalized = tuple(reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in value)
    if normalized != value:
        raise ValueError("reason_codes must be unique and deterministic")
    return normalized


def _report_payload(report: ResearchStrategySignalQualityReport) -> dict[str, object]:
    payload = _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        human_review_status=report.human_review_status,
        row_count=report.row_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_quality_score=report.average_quality_score,
        min_evidence_strength_score=report.min_evidence_strength_score,
        max_freshness_age_hours=report.max_freshness_age_hours,
        max_conflict_rate=report.max_conflict_rate,
        max_calibration_error_rate=report.max_calibration_error_rate,
        min_calibration_sample_count=report.min_calibration_sample_count,
        rows=report.rows,
        reason_code_counts=report.reason_code_counts,
        reason_codes=report.reason_codes,
        public_notes=report.public_notes,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    payload[_DIGEST_FIELD] = report.derived_validation_digest
    return payload


def _report_payload_without_digest(
    *,
    generated_at: datetime,
    config_version: str,
    human_review_status: str,
    row_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    average_quality_score: Decimal,
    min_evidence_strength_score: Decimal,
    max_freshness_age_hours: Decimal,
    max_conflict_rate: Decimal,
    max_calibration_error_rate: Decimal,
    min_calibration_sample_count: Decimal,
    rows: tuple[ResearchStrategySignalQualityRow, ...],
    reason_code_counts: tuple[ResearchStrategySignalQualityReasonCodeCount, ...],
    reason_codes: tuple[str, ...],
    public_notes: tuple[ResearchStrategySignalQualityPublicNote, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> dict[str, object]:
    return {
        "generated_at": _json_ready(generated_at),
        "config_version": config_version,
        "human_review_status": human_review_status,
        "row_count": _json_ready(row_count),
        "pass_count": _json_ready(pass_count),
        "watch_count": _json_ready(watch_count),
        "block_count": _json_ready(block_count),
        "average_quality_score": _json_ready(average_quality_score),
        "min_evidence_strength_score": _json_ready(min_evidence_strength_score),
        "max_freshness_age_hours": _json_ready(max_freshness_age_hours),
        "max_conflict_rate": _json_ready(max_conflict_rate),
        "max_calibration_error_rate": _json_ready(max_calibration_error_rate),
        "min_calibration_sample_count": _json_ready(min_calibration_sample_count),
        "rows": [_row_payload(row) for row in rows],
        "reason_code_counts": [_reason_count_payload(row) for row in reason_code_counts],
        "reason_codes": list(reason_codes),
        "public_notes": [_public_note_payload(note) for note in public_notes],
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }


def _row_payload(row: ResearchStrategySignalQualityRow) -> dict[str, object]:
    return {
        "signal_digest": row.signal_digest,
        "evidence_strength_score": _json_ready(row.evidence_strength_score),
        "evidence_freshness_age_hours": _json_ready(row.evidence_freshness_age_hours),
        "timeliness_score": _json_ready(row.timeliness_score),
        "conflict_rate": _json_ready(row.conflict_rate),
        "calibration_error_rate": _json_ready(row.calibration_error_rate),
        "calibration_sample_count": _json_ready(row.calibration_sample_count),
        "calibration_history_score": _json_ready(row.calibration_history_score),
        "quality_score": _json_ready(row.quality_score),
        "human_review_status": row.human_review_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _reason_count_payload(row: ResearchStrategySignalQualityReasonCodeCount) -> dict[str, object]:
    return {
        "reason_code": row.reason_code,
        "count": _json_ready(row.count),
        "row_ratio": _json_ready(row.row_ratio),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _public_note_payload(note: ResearchStrategySignalQualityPublicNote) -> dict[str, object]:
    return {
        "key": note.key,
        "value": note.value,
        "paper_only": note.paper_only,
        "report_only": note.report_only,
        "readonly": note.readonly,
    }


def _report_digest(report: ResearchStrategySignalQualityReport) -> str:
    return _report_digest_from_values(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "human_review_status": report.human_review_status,
            "row_count": report.row_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "average_quality_score": report.average_quality_score,
            "min_evidence_strength_score": report.min_evidence_strength_score,
            "max_freshness_age_hours": report.max_freshness_age_hours,
            "max_conflict_rate": report.max_conflict_rate,
            "max_calibration_error_rate": report.max_calibration_error_rate,
            "min_calibration_sample_count": report.min_calibration_sample_count,
            "rows": report.rows,
            "reason_code_counts": report.reason_code_counts,
            "reason_codes": report.reason_codes,
            "public_notes": report.public_notes,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _report_digest_from_values(values: dict[str, object]) -> str:
    payload = _report_payload_without_digest(
        generated_at=_require_mapping_value(values, "generated_at", datetime),
        config_version=_require_mapping_value(values, "config_version", str),
        human_review_status=_require_mapping_value(values, "human_review_status", str),
        row_count=_require_mapping_value(values, "row_count", Decimal),
        pass_count=_require_mapping_value(values, "pass_count", Decimal),
        watch_count=_require_mapping_value(values, "watch_count", Decimal),
        block_count=_require_mapping_value(values, "block_count", Decimal),
        average_quality_score=_require_mapping_value(values, "average_quality_score", Decimal),
        min_evidence_strength_score=_require_mapping_value(
            values,
            "min_evidence_strength_score",
            Decimal,
        ),
        max_freshness_age_hours=_require_mapping_value(
            values,
            "max_freshness_age_hours",
            Decimal,
        ),
        max_conflict_rate=_require_mapping_value(values, "max_conflict_rate", Decimal),
        max_calibration_error_rate=_require_mapping_value(
            values,
            "max_calibration_error_rate",
            Decimal,
        ),
        min_calibration_sample_count=_require_mapping_value(
            values,
            "min_calibration_sample_count",
            Decimal,
        ),
        rows=_require_mapping_value(values, "rows", tuple),
        reason_code_counts=_require_mapping_value(values, "reason_code_counts", tuple),
        reason_codes=_require_mapping_value(values, "reason_codes", tuple),
        public_notes=_require_mapping_value(values, "public_notes", tuple),
        paper_only=_require_mapping_value(values, "paper_only", bool),
        report_only=_require_mapping_value(values, "report_only", bool),
        readonly=_require_mapping_value(values, "readonly", bool),
    )
    return _digest_payload(payload)


def _validate_payload_digest(payload: dict[str, object]) -> None:
    if _DIGEST_FIELD not in payload:
        raise ValueError("derived_validation_digest is required")
    _require_digest(_DIGEST_FIELD, payload[_DIGEST_FIELD])
    digest_payload = dict(payload)
    digest_payload.pop(_DIGEST_FIELD)
    if payload[_DIGEST_FIELD] != _digest_payload(digest_payload):
        raise ValueError("derived_validation_digest mismatch")


def _digest_payload(payload: dict[str, object]) -> str:
    return sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8"),
    ).hexdigest()


def _json_ready(value: object) -> Any:
    if type(value) is ResearchStrategySignalQualityReport:
        return _report_payload(value)
    if type(value) is ResearchStrategySignalQualityRow:
        return _row_payload(value)
    if type(value) is ResearchStrategySignalQualityReasonCodeCount:
        return _reason_count_payload(value)
    if type(value) is ResearchStrategySignalQualityPublicNote:
        return _public_note_payload(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return _copy_json_object(value)
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    raise ValueError("value is not JSON-ready")


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied: dict[str, object] = {}
    for key, nested_value in value.items():
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        copied[key] = _copy_json_value(nested_value)
    return copied


def _copy_json_value(value: object) -> object:
    if type(value) is dict:
        return _copy_json_object(value)
    if type(value) is list:
        return [_copy_json_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, Decimal):
        raise ValueError("JSON payload values must serialize Decimal values as strings")
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON payload numeric values must be strings")
    raise ValueError("JSON payload is not JSON-ready")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            ResearchStrategySignalQualityScorecardConfig,
            ResearchStrategySignalQualityPublicNote,
            ResearchStrategySignalQualityRow,
            ResearchStrategySignalQualityReasonCodeCount,
            ResearchStrategySignalQualityReport,
        ):
            if type(value) is ResearchStrategySignalQualityInput:
                return
            raise ValueError(f"{current_path} must be a supported public dataclass")
        for field in fields(value):
            if field.name == "validation_config":
                continue
            if _has_unsafe_public_fragment(field.name):
                raise ValueError(f"{field.name} has unsafe public field")
            field_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field_path,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{current_path} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{current_path} must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{current_path} must be timezone-aware")
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is dict:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{item_path} has unsafe public field")
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            if key.endswith("status") and type(item) is str and item not in _STATUS_VALUES:
                raise ValueError(f"{item_path} must be pass, watch, or block")
            _reject_unsafe_public_payload(
                label,
                item,
                item_path,
                allow_json_containers=True,
            )
        return
    if type(value) is list:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=True,
            )
        return
    if type(value) is str:
        if value.strip() != value:
            raise ValueError(f"{current_path} has unsafe public value")
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{current_path} has unsafe public value")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float) or type(value) is int:
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    raise ValueError(f"{current_path} is not JSON-ready")


def _require_exact_type(value: object, expected_type: type, label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_private_key(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical text")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public detail")
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical public text")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public detail")
    return value


def _require_signal_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _SIGNAL_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a redacted sha256 digest")
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return decimal_value


def _require_mapping_value(
    values: dict[str, object],
    key: str,
    expected_type: type,
) -> Any:
    value = values[key]
    if type(value) is not expected_type:
        raise ValueError(f"{key} must be {expected_type.__name__}")
    return value


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _clamp_ratio(numerator / denominator)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _clamp_ratio(sum(values, _ZERO) / _decimal_count(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(max(_quantize(value), _ZERO), _ONE)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext() as context:
            context.rounding = ROUND_HALF_UP
            return value.quantize(_QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _signal_digest(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.casefold()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_SIGNAL_QUALITY_SCORECARD_CONFIG_VERSION",
    "ResearchStrategySignalQualityInput",
    "ResearchStrategySignalQualityPublicNote",
    "ResearchStrategySignalQualityReasonCodeCount",
    "ResearchStrategySignalQualityReport",
    "ResearchStrategySignalQualityRow",
    "ResearchStrategySignalQualityScorecardConfig",
    "build_research_strategy_signal_quality_scorecard",
    "research_strategy_signal_quality_scorecard_payload",
)
