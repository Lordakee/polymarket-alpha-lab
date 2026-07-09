"""Report-only review confidence decay report for research strategy teams."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_TEAM_REVIEW_CONFIDENCE_DECAY_REPORT_CONFIG_VERSION = (
    "research-strategy-team-review-confidence-decay-report-v0"
)
RESEARCH_STRATEGY_TEAM_REVIEW_CONFIDENCE_DECAY_STATUSES = ("pass", "watch", "block")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

ROW_PASS_REASON = "review_confidence_decay_pass"
CONFIDENCE_DROP_BLOCK_REASON = "confidence_drop_block"
CONFIDENCE_DROP_WATCH_REASON = "confidence_drop_watch"
CURRENT_CONFIDENCE_BLOCK_REASON = "current_confidence_block"
CURRENT_CONFIDENCE_WATCH_REASON = "current_confidence_watch"
EVIDENCE_BLOCK_REASON = "evidence_freshness_block"
EVIDENCE_WATCH_REASON = "evidence_freshness_watch"
CALIBRATION_BLOCK_REASON = "team_calibration_block"
CALIBRATION_WATCH_REASON = "team_calibration_watch"
AGREEMENT_BLOCK_REASON = "reviewer_agreement_block"
AGREEMENT_WATCH_REASON = "reviewer_agreement_watch"
LATENCY_BLOCK_REASON = "review_latency_block"
LATENCY_WATCH_REASON = "review_latency_watch"
DECAY_PRESSURE_BLOCK_REASON = "decay_pressure_block"
DECAY_PRESSURE_WATCH_REASON = "decay_pressure_watch"
ADJUSTED_CONFIDENCE_BLOCK_REASON = "adjusted_confidence_block"
ADJUSTED_CONFIDENCE_WATCH_REASON = "adjusted_confidence_watch"
CONFIDENCE_AGE_BLOCK_REASON = "confidence_age_block"
CONFIDENCE_AGE_WATCH_REASON = "confidence_age_watch"

REPORT_PASS_REASON = "review_confidence_decay_pass"
REPORT_WATCH_REASON = "review_confidence_decay_watch"
REPORT_BLOCK_REASON = "review_confidence_decay_block"
REPORT_NO_INPUTS_REASON = "review_confidence_decay_no_inputs"
CONFIDENCE_DROP_REVIEW_REASON = "confidence_drop_review"
CURRENT_CONFIDENCE_REVIEW_REASON = "current_confidence_review"
EVIDENCE_REVIEW_REASON = "evidence_freshness_review"
CALIBRATION_REVIEW_REASON = "team_calibration_review"
AGREEMENT_REVIEW_REASON = "reviewer_agreement_review"
LATENCY_REVIEW_REASON = "review_latency_review"
DECAY_PRESSURE_REVIEW_REASON = "decay_pressure_review"
ADJUSTED_CONFIDENCE_REVIEW_REASON = "adjusted_confidence_review"
CONFIDENCE_AGE_REVIEW_REASON = "confidence_age_review"

ROW_REASON_CODES = (
    ROW_PASS_REASON,
    CONFIDENCE_DROP_BLOCK_REASON,
    CONFIDENCE_DROP_WATCH_REASON,
    CURRENT_CONFIDENCE_BLOCK_REASON,
    CURRENT_CONFIDENCE_WATCH_REASON,
    EVIDENCE_BLOCK_REASON,
    EVIDENCE_WATCH_REASON,
    CALIBRATION_BLOCK_REASON,
    CALIBRATION_WATCH_REASON,
    AGREEMENT_BLOCK_REASON,
    AGREEMENT_WATCH_REASON,
    LATENCY_BLOCK_REASON,
    LATENCY_WATCH_REASON,
    DECAY_PRESSURE_BLOCK_REASON,
    DECAY_PRESSURE_WATCH_REASON,
    ADJUSTED_CONFIDENCE_BLOCK_REASON,
    ADJUSTED_CONFIDENCE_WATCH_REASON,
    CONFIDENCE_AGE_BLOCK_REASON,
    CONFIDENCE_AGE_WATCH_REASON,
)
REPORT_REASON_CODES = (
    REPORT_PASS_REASON,
    REPORT_WATCH_REASON,
    REPORT_BLOCK_REASON,
    REPORT_NO_INPUTS_REASON,
    CONFIDENCE_DROP_REVIEW_REASON,
    CURRENT_CONFIDENCE_REVIEW_REASON,
    EVIDENCE_REVIEW_REASON,
    CALIBRATION_REVIEW_REASON,
    AGREEMENT_REVIEW_REASON,
    LATENCY_REVIEW_REASON,
    DECAY_PRESSURE_REVIEW_REASON,
    ADJUSTED_CONFIDENCE_REVIEW_REASON,
    CONFIDENCE_AGE_REVIEW_REASON,
)

UNSAFE_KEY_FRAGMENTS = (
    "raw",
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
    "secret",
    "credential",
    "api" + "_" + "key",
)


@dataclass(frozen=True)
class ResearchStrategyTeamReviewConfidenceDecayConfig:
    config_version: str
    fresh_confidence_age_seconds: Decimal
    stale_confidence_age_seconds: Decimal
    watch_confidence_drop: Decimal
    block_confidence_drop: Decimal
    min_pass_current_confidence_score: Decimal
    min_watch_current_confidence_score: Decimal
    min_pass_decay_adjusted_confidence_score: Decimal
    min_watch_decay_adjusted_confidence_score: Decimal
    max_pass_decay_pressure_score: Decimal
    max_watch_decay_pressure_score: Decimal
    min_pass_review_evidence_freshness_score: Decimal
    min_watch_review_evidence_freshness_score: Decimal
    min_pass_team_calibration_score: Decimal
    min_watch_team_calibration_score: Decimal
    min_pass_reviewer_agreement_score: Decimal
    min_watch_reviewer_agreement_score: Decimal
    max_pass_review_latency_pressure: Decimal
    max_watch_review_latency_pressure: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTeamReviewConfidenceDecayConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_TEAM_REVIEW_CONFIDENCE_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("fresh_confidence_age_seconds", "stale_confidence_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_confidence_drop",
            "block_confidence_drop",
            "min_pass_current_confidence_score",
            "min_watch_current_confidence_score",
            "min_pass_decay_adjusted_confidence_score",
            "min_watch_decay_adjusted_confidence_score",
            "max_pass_decay_pressure_score",
            "max_watch_decay_pressure_score",
            "min_pass_review_evidence_freshness_score",
            "min_watch_review_evidence_freshness_score",
            "min_pass_team_calibration_score",
            "min_watch_team_calibration_score",
            "min_pass_reviewer_agreement_score",
            "min_watch_reviewer_agreement_score",
            "max_pass_review_latency_pressure",
            "max_watch_review_latency_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_age_threshold_pair(
            "confidence age threshold",
            self.fresh_confidence_age_seconds,
            self.stale_confidence_age_seconds,
        )
        _require_max_threshold_pair(
            "confidence drop threshold",
            self.watch_confidence_drop,
            self.block_confidence_drop,
        )
        _require_min_threshold_pair(
            "current confidence threshold",
            self.min_watch_current_confidence_score,
            self.min_pass_current_confidence_score,
        )
        _require_min_threshold_pair(
            "adjusted confidence threshold",
            self.min_watch_decay_adjusted_confidence_score,
            self.min_pass_decay_adjusted_confidence_score,
        )
        _require_max_threshold_pair(
            "decay pressure threshold",
            self.max_pass_decay_pressure_score,
            self.max_watch_decay_pressure_score,
        )
        _require_min_threshold_pair(
            "evidence threshold",
            self.min_watch_review_evidence_freshness_score,
            self.min_pass_review_evidence_freshness_score,
        )
        _require_min_threshold_pair(
            "calibration threshold",
            self.min_watch_team_calibration_score,
            self.min_pass_team_calibration_score,
        )
        _require_min_threshold_pair(
            "agreement threshold",
            self.min_watch_reviewer_agreement_score,
            self.min_pass_reviewer_agreement_score,
        )
        _require_max_threshold_pair(
            "latency threshold",
            self.max_pass_review_latency_pressure,
            self.max_watch_review_latency_pressure,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyTeamReviewConfidenceDecayInput:
    team_ref: str
    review_ref: str
    reviewed_at: datetime
    last_confidence_update_at: datetime
    baseline_confidence_score: Decimal
    current_confidence_score: Decimal
    review_evidence_freshness_score: Decimal
    team_calibration_score: Decimal
    reviewer_agreement_score: Decimal
    review_latency_pressure: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTeamReviewConfidenceDecayInput, "input")
        _require_public_string("team_ref", self.team_ref)
        _require_private_ref("review_ref", self.review_ref)
        for field_name in ("reviewed_at", "last_confidence_update_at"):
            object.__setattr__(self, field_name, _as_utc(field_name, getattr(self, field_name)))
        if self.last_confidence_update_at < self.reviewed_at:
            raise ValueError("last_confidence_update_at must not be before reviewed_at")
        for field_name in (
            "baseline_confidence_score",
            "current_confidence_score",
            "review_evidence_freshness_score",
            "team_calibration_score",
            "reviewer_agreement_score",
            "review_latency_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyTeamReviewConfidenceDecayRow:
    aggregate_row_number: Decimal
    team_ref: str
    review_hash: str
    confidence_age_seconds: Decimal
    confidence_age_pressure: Decimal
    baseline_confidence_score: Decimal
    current_confidence_score: Decimal
    confidence_drop: Decimal
    review_evidence_freshness_score: Decimal
    team_calibration_score: Decimal
    reviewer_agreement_score: Decimal
    review_latency_pressure: Decimal
    decay_pressure_score: Decimal
    decay_adjusted_confidence_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTeamReviewConfidenceDecayRow, "row")
        object.__setattr__(
            self,
            "aggregate_row_number",
            _normalize_positive_count("aggregate_row_number", self.aggregate_row_number),
        )
        _require_public_string("team_ref", self.team_ref)
        _require_sha256_digest("review_hash", self.review_hash)
        object.__setattr__(
            self,
            "confidence_age_seconds",
            _normalize_nonnegative_decimal("confidence_age_seconds", self.confidence_age_seconds),
        )
        for field_name in (
            "confidence_age_pressure",
            "baseline_confidence_score",
            "current_confidence_score",
            "confidence_drop",
            "review_evidence_freshness_score",
            "team_calibration_score",
            "reviewer_agreement_score",
            "review_latency_pressure",
            "decay_pressure_score",
            "decay_adjusted_confidence_score",
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
class ResearchStrategyTeamReviewConfidenceDecayReport:
    generated_at: datetime
    config_version: str
    review_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_confidence_drop: Decimal
    mean_decay_pressure_score: Decimal
    mean_decay_adjusted_confidence_score: Decimal
    lowest_decay_adjusted_confidence_score: Decimal
    highest_confidence_drop: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    rows: tuple[ResearchStrategyTeamReviewConfidenceDecayRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTeamReviewConfidenceDecayReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("review_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_confidence_drop",
            "mean_decay_pressure_score",
            "mean_decay_adjusted_confidence_score",
            "lowest_decay_adjusted_confidence_score",
            "highest_confidence_drop",
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


def build_research_strategy_team_review_confidence_decay_report(
    inputs: Iterable[ResearchStrategyTeamReviewConfidenceDecayInput],
    *,
    config: ResearchStrategyTeamReviewConfidenceDecayConfig,
    generated_at: datetime,
) -> ResearchStrategyTeamReviewConfidenceDecayReport:
    if type(config) is not ResearchStrategyTeamReviewConfidenceDecayConfig:
        raise ValueError("config must be a ResearchStrategyTeamReviewConfidenceDecayConfig")
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
    return ResearchStrategyTeamReviewConfidenceDecayReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        review_count=_count(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        mean_confidence_drop=_mean(tuple(row.confidence_drop for row in rows)),
        mean_decay_pressure_score=_mean(tuple(row.decay_pressure_score for row in rows)),
        mean_decay_adjusted_confidence_score=_mean(
            tuple(row.decay_adjusted_confidence_score for row in rows),
        ),
        lowest_decay_adjusted_confidence_score=min(
            (row.decay_adjusted_confidence_score for row in rows),
            default=ZERO,
        ),
        highest_confidence_drop=max((row.confidence_drop for row in rows), default=ZERO),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_team_review_confidence_decay_report_payload(
    report: ResearchStrategyTeamReviewConfidenceDecayReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyTeamReviewConfidenceDecayReport:
        _require_hard_flags("report", report)
        _verify_report_integrity(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        _validate_public_payload_values("payload", report)
        _verify_public_payload_integrity(report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchStrategyTeamReviewConfidenceDecayReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_TEAM_REVIEW_CONFIDENCE_DECAY_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_TEAM_REVIEW_CONFIDENCE_DECAY_STATUSES",
    "ResearchStrategyTeamReviewConfidenceDecayConfig",
    "ResearchStrategyTeamReviewConfidenceDecayInput",
    "ResearchStrategyTeamReviewConfidenceDecayRow",
    "ResearchStrategyTeamReviewConfidenceDecayReport",
    "build_research_strategy_team_review_confidence_decay_report",
    "research_strategy_team_review_confidence_decay_report_payload",
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
    team_ref: str
    review_hash: str
    confidence_age_seconds: Decimal
    confidence_age_pressure: Decimal
    baseline_confidence_score: Decimal
    current_confidence_score: Decimal
    confidence_drop: Decimal
    review_evidence_freshness_score: Decimal
    team_calibration_score: Decimal
    reviewer_agreement_score: Decimal
    review_latency_pressure: Decimal
    decay_pressure_score: Decimal
    decay_adjusted_confidence_score: Decimal
    status: str
    reason_codes: tuple[str, ...]


def _prepare_row(
    value: ResearchStrategyTeamReviewConfidenceDecayInput,
    *,
    config: ResearchStrategyTeamReviewConfidenceDecayConfig,
    generated_at: datetime,
) -> _PreparedRow:
    if value.reviewed_at > generated_at:
        raise ValueError("reviewed_at must not be after generated_at")
    if value.last_confidence_update_at > generated_at:
        raise ValueError("last_confidence_update_at must not be after generated_at")
    confidence_age_seconds = _age_seconds(generated_at, value.last_confidence_update_at)
    confidence_age_pressure = _age_pressure(
        confidence_age_seconds,
        fresh_age=config.fresh_confidence_age_seconds,
        stale_age=config.stale_confidence_age_seconds,
    )
    confidence_drop = _quantize(
        _max_decimal(value.baseline_confidence_score - value.current_confidence_score, ZERO),
    )
    decay_pressure_score = _decay_pressure_score(
        confidence_age_pressure=confidence_age_pressure,
        confidence_drop=confidence_drop,
        review_evidence_freshness_score=value.review_evidence_freshness_score,
        team_calibration_score=value.team_calibration_score,
        reviewer_agreement_score=value.reviewer_agreement_score,
        review_latency_pressure=value.review_latency_pressure,
    )
    adjusted_confidence = _quantize(
        value.current_confidence_score * (ONE - decay_pressure_score),
    )
    reason_codes = _row_reason_codes(
        confidence_drop=confidence_drop,
        current_confidence_score=value.current_confidence_score,
        review_evidence_freshness_score=value.review_evidence_freshness_score,
        team_calibration_score=value.team_calibration_score,
        reviewer_agreement_score=value.reviewer_agreement_score,
        review_latency_pressure=value.review_latency_pressure,
        decay_pressure_score=decay_pressure_score,
        decay_adjusted_confidence_score=adjusted_confidence,
        confidence_age_pressure=confidence_age_pressure,
        config=config,
    )
    status = _row_status(reason_codes)
    return _PreparedRow(
        team_ref=value.team_ref,
        review_hash=_review_hash(value.team_ref, value.review_ref),
        confidence_age_seconds=confidence_age_seconds,
        confidence_age_pressure=confidence_age_pressure,
        baseline_confidence_score=value.baseline_confidence_score,
        current_confidence_score=value.current_confidence_score,
        confidence_drop=confidence_drop,
        review_evidence_freshness_score=value.review_evidence_freshness_score,
        team_calibration_score=value.team_calibration_score,
        reviewer_agreement_score=value.reviewer_agreement_score,
        review_latency_pressure=value.review_latency_pressure,
        decay_pressure_score=decay_pressure_score,
        decay_adjusted_confidence_score=adjusted_confidence,
        status=status,
        reason_codes=reason_codes,
    )


def _row_from_prepared(
    value: _PreparedRow,
    *,
    aggregate_row_number: Decimal,
) -> ResearchStrategyTeamReviewConfidenceDecayRow:
    return ResearchStrategyTeamReviewConfidenceDecayRow(
        aggregate_row_number=aggregate_row_number,
        team_ref=value.team_ref,
        review_hash=value.review_hash,
        confidence_age_seconds=value.confidence_age_seconds,
        confidence_age_pressure=value.confidence_age_pressure,
        baseline_confidence_score=value.baseline_confidence_score,
        current_confidence_score=value.current_confidence_score,
        confidence_drop=value.confidence_drop,
        review_evidence_freshness_score=value.review_evidence_freshness_score,
        team_calibration_score=value.team_calibration_score,
        reviewer_agreement_score=value.reviewer_agreement_score,
        review_latency_pressure=value.review_latency_pressure,
        decay_pressure_score=value.decay_pressure_score,
        decay_adjusted_confidence_score=value.decay_adjusted_confidence_score,
        status=value.status,
        reason_codes=value.reason_codes,
    )


def _row_reason_codes(
    *,
    confidence_drop: Decimal,
    current_confidence_score: Decimal,
    review_evidence_freshness_score: Decimal,
    team_calibration_score: Decimal,
    reviewer_agreement_score: Decimal,
    review_latency_pressure: Decimal,
    decay_pressure_score: Decimal,
    decay_adjusted_confidence_score: Decimal,
    confidence_age_pressure: Decimal,
    config: ResearchStrategyTeamReviewConfidenceDecayConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if confidence_drop >= config.block_confidence_drop:
        codes.append(CONFIDENCE_DROP_BLOCK_REASON)
    elif confidence_drop >= config.watch_confidence_drop:
        codes.append(CONFIDENCE_DROP_WATCH_REASON)
    if current_confidence_score < config.min_watch_current_confidence_score:
        codes.append(CURRENT_CONFIDENCE_BLOCK_REASON)
    elif current_confidence_score < config.min_pass_current_confidence_score:
        codes.append(CURRENT_CONFIDENCE_WATCH_REASON)
    if review_evidence_freshness_score < config.min_watch_review_evidence_freshness_score:
        codes.append(EVIDENCE_BLOCK_REASON)
    elif review_evidence_freshness_score < config.min_pass_review_evidence_freshness_score:
        codes.append(EVIDENCE_WATCH_REASON)
    if team_calibration_score < config.min_watch_team_calibration_score:
        codes.append(CALIBRATION_BLOCK_REASON)
    elif team_calibration_score < config.min_pass_team_calibration_score:
        codes.append(CALIBRATION_WATCH_REASON)
    if reviewer_agreement_score < config.min_watch_reviewer_agreement_score:
        codes.append(AGREEMENT_BLOCK_REASON)
    elif reviewer_agreement_score < config.min_pass_reviewer_agreement_score:
        codes.append(AGREEMENT_WATCH_REASON)
    if review_latency_pressure > config.max_watch_review_latency_pressure:
        codes.append(LATENCY_BLOCK_REASON)
    elif review_latency_pressure > config.max_pass_review_latency_pressure:
        codes.append(LATENCY_WATCH_REASON)
    if decay_pressure_score > config.max_watch_decay_pressure_score:
        codes.append(DECAY_PRESSURE_BLOCK_REASON)
    elif decay_pressure_score > config.max_pass_decay_pressure_score:
        codes.append(DECAY_PRESSURE_WATCH_REASON)
    if decay_adjusted_confidence_score < config.min_watch_decay_adjusted_confidence_score:
        codes.append(ADJUSTED_CONFIDENCE_BLOCK_REASON)
    elif decay_adjusted_confidence_score < config.min_pass_decay_adjusted_confidence_score:
        codes.append(ADJUSTED_CONFIDENCE_WATCH_REASON)
    if confidence_age_pressure >= ONE:
        codes.append(CONFIDENCE_AGE_BLOCK_REASON)
    elif confidence_age_pressure > ZERO:
        codes.append(CONFIDENCE_AGE_WATCH_REASON)
    if not codes:
        return (ROW_PASS_REASON,)
    return _normalize_reason_codes("reason_codes", tuple(sorted(codes)), ROW_REASON_CODES)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return STATUS_BLOCK
    if reason_codes != (ROW_PASS_REASON,):
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(rows: tuple[ResearchStrategyTeamReviewConfidenceDecayRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchStrategyTeamReviewConfidenceDecayRow, ...],
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
        (
            (CONFIDENCE_DROP_BLOCK_REASON, CONFIDENCE_DROP_WATCH_REASON),
            CONFIDENCE_DROP_REVIEW_REASON,
        ),
        (
            (CURRENT_CONFIDENCE_BLOCK_REASON, CURRENT_CONFIDENCE_WATCH_REASON),
            CURRENT_CONFIDENCE_REVIEW_REASON,
        ),
        ((EVIDENCE_BLOCK_REASON, EVIDENCE_WATCH_REASON), EVIDENCE_REVIEW_REASON),
        ((CALIBRATION_BLOCK_REASON, CALIBRATION_WATCH_REASON), CALIBRATION_REVIEW_REASON),
        ((AGREEMENT_BLOCK_REASON, AGREEMENT_WATCH_REASON), AGREEMENT_REVIEW_REASON),
        ((LATENCY_BLOCK_REASON, LATENCY_WATCH_REASON), LATENCY_REVIEW_REASON),
        (
            (DECAY_PRESSURE_BLOCK_REASON, DECAY_PRESSURE_WATCH_REASON),
            DECAY_PRESSURE_REVIEW_REASON,
        ),
        (
            (ADJUSTED_CONFIDENCE_BLOCK_REASON, ADJUSTED_CONFIDENCE_WATCH_REASON),
            ADJUSTED_CONFIDENCE_REVIEW_REASON,
        ),
        (
            (CONFIDENCE_AGE_BLOCK_REASON, CONFIDENCE_AGE_WATCH_REASON),
            CONFIDENCE_AGE_REVIEW_REASON,
        ),
    )
    for row_reasons, report_reason in review_pairs:
        if any(any(reason in row.reason_codes for reason in row_reasons) for row in rows):
            codes.append(report_reason)
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _prepared_row_sort_key(value: _PreparedRow) -> tuple[int, Decimal, str, str]:
    return (
        {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value.status],
        -value.decay_pressure_score,
        value.team_ref,
        value.review_hash,
    )


def _normalize_inputs(
    value: Iterable[ResearchStrategyTeamReviewConfidenceDecayInput],
) -> tuple[ResearchStrategyTeamReviewConfidenceDecayInput, ...]:
    if isinstance(value, (str, bytes, dict)):
        raise ValueError("inputs must be an iterable of input rows")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyTeamReviewConfidenceDecayInput:
            raise ValueError("inputs must contain ResearchStrategyTeamReviewConfidenceDecayInput")
        _require_hard_flags("input", row)
        if row.review_ref in seen:
            raise ValueError("duplicate review_ref values are not allowed")
        seen.add(row.review_ref)
    return rows


def _normalize_rows(
    value: object,
) -> tuple[ResearchStrategyTeamReviewConfidenceDecayRow, ...]:
    if type(value) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    rows = tuple(value)
    seen_numbers: set[Decimal] = set()
    seen_hashes: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyTeamReviewConfidenceDecayRow:
            raise ValueError("rows must contain ResearchStrategyTeamReviewConfidenceDecayRow")
        _require_hard_flags("row", row)
        if row.aggregate_row_number in seen_numbers:
            raise ValueError("aggregate_row_number values must be unique")
        if row.review_hash in seen_hashes:
            raise ValueError("review_hash values must be unique")
        seen_numbers.add(row.aggregate_row_number)
        seen_hashes.add(row.review_hash)
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
    rows: tuple[ResearchStrategyTeamReviewConfidenceDecayRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    if not rows:
        counts[REPORT_NO_INPUTS_REASON] = ONE
    return tuple((reason, count) for reason, count in sorted(counts.items()))


def _status_count(
    rows: tuple[ResearchStrategyTeamReviewConfidenceDecayRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _validate_row_consistency(row: ResearchStrategyTeamReviewConfidenceDecayRow) -> None:
    if row.confidence_drop != _quantize(
        _max_decimal(row.baseline_confidence_score - row.current_confidence_score, ZERO),
    ):
        raise ValueError("confidence_drop must match row scores")
    expected_decay = _decay_pressure_score(
        confidence_age_pressure=row.confidence_age_pressure,
        confidence_drop=row.confidence_drop,
        review_evidence_freshness_score=row.review_evidence_freshness_score,
        team_calibration_score=row.team_calibration_score,
        reviewer_agreement_score=row.reviewer_agreement_score,
        review_latency_pressure=row.review_latency_pressure,
    )
    if row.decay_pressure_score != expected_decay:
        raise ValueError("decay_pressure_score must match row components")
    expected_adjusted = _quantize(
        row.current_confidence_score * (ONE - row.decay_pressure_score),
    )
    if row.decay_adjusted_confidence_score != expected_adjusted:
        raise ValueError("decay_adjusted_confidence_score must match row components")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchStrategyTeamReviewConfidenceDecayReport,
) -> None:
    expected_values = {
        "review_count": _count(len(report.rows)),
        "pass_count": _status_count(report.rows, STATUS_PASS),
        "watch_count": _status_count(report.rows, STATUS_WATCH),
        "block_count": _status_count(report.rows, STATUS_BLOCK),
        "mean_confidence_drop": _mean(tuple(row.confidence_drop for row in report.rows)),
        "mean_decay_pressure_score": _mean(
            tuple(row.decay_pressure_score for row in report.rows),
        ),
        "mean_decay_adjusted_confidence_score": _mean(
            tuple(row.decay_adjusted_confidence_score for row in report.rows),
        ),
        "lowest_decay_adjusted_confidence_score": min(
            (row.decay_adjusted_confidence_score for row in report.rows),
            default=ZERO,
        ),
        "highest_confidence_drop": max((row.confidence_drop for row in report.rows), default=ZERO),
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
    confidence_age_pressure: Decimal,
    confidence_drop: Decimal,
    review_evidence_freshness_score: Decimal,
    team_calibration_score: Decimal,
    reviewer_agreement_score: Decimal,
    review_latency_pressure: Decimal,
) -> Decimal:
    return _mean(
        (
            confidence_age_pressure,
            confidence_drop,
            ONE - review_evidence_freshness_score,
            ONE - team_calibration_score,
            ONE - reviewer_agreement_score,
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
    observed = _as_utc("last_confidence_update_at", observed_at)
    if observed > generated:
        raise ValueError("last_confidence_update_at must not be after generated_at")
    delta = generated - observed
    return _quantize(
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND),
    )


def _review_hash(team_ref: str, review_ref: str) -> str:
    return sha256((team_ref + "\x00" + review_ref).encode("utf-8")).hexdigest()


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


def _verify_report_integrity(report: ResearchStrategyTeamReviewConfidenceDecayReport) -> None:
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


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_canonical_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{name} must be canonical text")
    return value


def _require_public_string(name: str, value: object) -> str:
    _require_canonical_string(name, value)
    if len(value) > 128:
        raise ValueError(f"{name} must be short public text")
    _reject_unsafe_public_payload(name, value)
    return value


def _require_private_ref(name: str, value: object) -> str:
    _require_canonical_string(name, value)
    if len(value) > 512:
        raise ValueError(f"{name} must not exceed 512 characters")
    return value


def _require_status(name: str, value: object) -> str:
    if type(value) is not str or value not in RESEARCH_STRATEGY_TEAM_REVIEW_CONFIDENCE_DECAY_STATUSES:
        raise ValueError(f"{name} must be one of pass, watch, block")
    return value


def _require_reason_code(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in ROW_REASON_CODES and value not in REPORT_REASON_CODES:
        raise ValueError(f"{name} must be supported")
    return value


def _require_sha256_digest(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a lowercase sha256 digest")
    return value


def _require_age_threshold_pair(label: str, fresh: Decimal, stale: Decimal) -> None:
    if fresh >= stale:
        raise ValueError(f"{label} threshold values must increase")


def _require_min_threshold_pair(label: str, watch: Decimal, passed: Decimal) -> None:
    if watch >= passed:
        raise ValueError(f"{label} threshold values must increase")


def _require_max_threshold_pair(label: str, passed: Decimal, watch: Decimal) -> None:
    if passed >= watch:
        raise ValueError(f"{label} threshold values must increase")


def _normalize_probability(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_positive_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exactly Decimal")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)
