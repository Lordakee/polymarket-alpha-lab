"""Pure report-only review calibration and domain memory bridge report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_TEAM_REVIEW_CALIBRATION_MEMORY_BRIDGE_REPORT_CONFIG_VERSION = (
    "research-team-review-calibration-memory-bridge-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
RESEARCH_TEAM_REVIEW_CALIBRATION_MEMORY_BRIDGE_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)

EMPTY_REASON = "review_calibration_memory_bridge_empty"
CLEAR_REASON = "review_calibration_memory_bridge_clear"
OUTCOME_FOLLOWUP_BLOCK_REASON = "outcome_followup_block"
OUTCOME_FOLLOWUP_WATCH_REASON = "outcome_followup_watch"
CORRECTION_ADOPTION_BLOCK_REASON = "correction_adoption_block"
CORRECTION_ADOPTION_WATCH_REASON = "correction_adoption_watch"
STALE_MEMORY_REDUCTION_BLOCK_REASON = "stale_memory_reduction_block"
STALE_MEMORY_REDUCTION_WATCH_REASON = "stale_memory_reduction_watch"
EVIDENCE_REUSE_QUALITY_BLOCK_REASON = "evidence_reuse_quality_block"
EVIDENCE_REUSE_QUALITY_WATCH_REASON = "evidence_reuse_quality_watch"
PEER_REVIEW_COVERAGE_BLOCK_REASON = "peer_review_coverage_block"
PEER_REVIEW_COVERAGE_WATCH_REASON = "peer_review_coverage_watch"
REVIEW_LATENCY_BLOCK_REASON = "review_latency_block"
REVIEW_LATENCY_WATCH_REASON = "review_latency_watch"
BRIDGE_SCORE_BLOCK_REASON = "bridge_score_block"
BRIDGE_SCORE_WATCH_REASON = "bridge_score_watch"

ROW_REASON_CODES = (
    OUTCOME_FOLLOWUP_BLOCK_REASON,
    CORRECTION_ADOPTION_BLOCK_REASON,
    STALE_MEMORY_REDUCTION_BLOCK_REASON,
    EVIDENCE_REUSE_QUALITY_BLOCK_REASON,
    PEER_REVIEW_COVERAGE_BLOCK_REASON,
    REVIEW_LATENCY_BLOCK_REASON,
    BRIDGE_SCORE_BLOCK_REASON,
    OUTCOME_FOLLOWUP_WATCH_REASON,
    CORRECTION_ADOPTION_WATCH_REASON,
    STALE_MEMORY_REDUCTION_WATCH_REASON,
    EVIDENCE_REUSE_QUALITY_WATCH_REASON,
    PEER_REVIEW_COVERAGE_WATCH_REASON,
    REVIEW_LATENCY_WATCH_REASON,
    BRIDGE_SCORE_WATCH_REASON,
    CLEAR_REASON,
)

REPORT_BLOCK_PRESENT_REASON = "review_calibration_memory_bridge_block_present"
REPORT_WATCH_PRESENT_REASON = "review_calibration_memory_bridge_watch_present"
REPORT_OUTCOME_FOLLOWUP_GAP_REASON = "outcome_followup_gap_present"
REPORT_CORRECTION_ADOPTION_GAP_REASON = "correction_adoption_gap_present"
REPORT_STALE_MEMORY_REDUCTION_GAP_REASON = "stale_memory_reduction_gap_present"
REPORT_EVIDENCE_REUSE_QUALITY_GAP_REASON = "evidence_reuse_quality_gap_present"
REPORT_PEER_REVIEW_COVERAGE_GAP_REASON = "peer_review_coverage_gap_present"
REPORT_REVIEW_LATENCY_GAP_REASON = "review_latency_gap_present"
REPORT_BRIDGE_SCORE_GAP_REASON = "bridge_score_gap_present"
REPORT_CLEAR_REASON = "review_calibration_memory_bridge_report_clear"

REPORT_REASON_CODES = (
    EMPTY_REASON,
    REPORT_BLOCK_PRESENT_REASON,
    REPORT_WATCH_PRESENT_REASON,
    REPORT_OUTCOME_FOLLOWUP_GAP_REASON,
    REPORT_CORRECTION_ADOPTION_GAP_REASON,
    REPORT_STALE_MEMORY_REDUCTION_GAP_REASON,
    REPORT_EVIDENCE_REUSE_QUALITY_GAP_REASON,
    REPORT_PEER_REVIEW_COVERAGE_GAP_REASON,
    REPORT_REVIEW_LATENCY_GAP_REASON,
    REPORT_BRIDGE_SCORE_GAP_REASON,
    REPORT_CLEAR_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")

UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "raw_",
    "_raw",
    "candidate",
    "market",
    "slug",
    "question",
    "source_url",
    "source_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "trading",
    "recommend",
    "sizing",
    "secret",
    "credential",
    "private",
    "password",
    "database",
    "network",
    "scrape",
    "scraping",
    "url",
    "live_surface",
)

UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "http://",
    "https://",
    "://",
    "postgres://",
    "mysql://",
    "jdbc:",
    "raw candidate",
    "candidate",
    "market",
    "slug",
    "question",
    "source_url",
    "source text",
    "source_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "trading",
    "recommend",
    "sizing",
    "secret",
    "credential",
    "private",
    "password",
    "database",
    "network",
    "scrape",
    "scraping",
    "live surface",
    "live_surface",
)


@dataclass(frozen=True)
class ResearchTeamReviewCalibrationMemoryBridgeConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_REVIEW_CALIBRATION_MEMORY_BRIDGE_REPORT_CONFIG_VERSION
    )
    max_pass_review_latency_seconds: Decimal = Decimal("1800.000000")
    max_watch_review_latency_seconds: Decimal = Decimal("7200.000000")
    min_pass_outcome_followup_score: Decimal = Decimal("0.700000")
    min_watch_outcome_followup_score: Decimal = Decimal("0.500000")
    min_pass_correction_adoption_score: Decimal = Decimal("0.700000")
    min_watch_correction_adoption_score: Decimal = Decimal("0.500000")
    min_pass_stale_memory_reduction_score: Decimal = Decimal("0.700000")
    min_watch_stale_memory_reduction_score: Decimal = Decimal("0.500000")
    min_pass_evidence_reuse_quality_score: Decimal = Decimal("0.700000")
    min_watch_evidence_reuse_quality_score: Decimal = Decimal("0.500000")
    min_pass_peer_review_coverage_score: Decimal = Decimal("0.700000")
    min_watch_peer_review_coverage_score: Decimal = Decimal("0.500000")
    min_pass_bridge_score: Decimal = Decimal("0.700000")
    min_watch_bridge_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamReviewCalibrationMemoryBridgeConfig:
            raise TypeError(
                "ResearchTeamReviewCalibrationMemoryBridgeConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamReviewCalibrationMemoryBridgeConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_REVIEW_CALIBRATION_MEMORY_BRIDGE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_pass_review_latency_seconds",
            _require_positive_decimal(
                "max_pass_review_latency_seconds",
                self.max_pass_review_latency_seconds,
            ),
        )
        object.__setattr__(
            self,
            "max_watch_review_latency_seconds",
            _require_positive_decimal(
                "max_watch_review_latency_seconds",
                self.max_watch_review_latency_seconds,
            ),
        )
        for field_name in (
            "min_pass_outcome_followup_score",
            "min_watch_outcome_followup_score",
            "min_pass_correction_adoption_score",
            "min_watch_correction_adoption_score",
            "min_pass_stale_memory_reduction_score",
            "min_watch_stale_memory_reduction_score",
            "min_pass_evidence_reuse_quality_score",
            "min_watch_evidence_reuse_quality_score",
            "min_pass_peer_review_coverage_score",
            "min_watch_peer_review_coverage_score",
            "min_pass_bridge_score",
            "min_watch_bridge_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamReviewCalibrationMemoryBridgeObservation:
    review_group: str
    domain_label: str
    reviewer_label: str
    observed_at: datetime
    resolved_outcome_followup_score: Decimal
    correction_adoption_score: Decimal
    stale_memory_reduction_score: Decimal
    evidence_reuse_quality_score: Decimal
    peer_review_coverage_score: Decimal
    review_latency_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamReviewCalibrationMemoryBridgeObservation:
            raise TypeError(
                "ResearchTeamReviewCalibrationMemoryBridgeObservation does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamReviewCalibrationMemoryBridgeObservation,
            "observation",
        )
        for field_name in ("review_group", "domain_label", "reviewer_label"):
            object.__setattr__(
                self,
                field_name,
                _require_public_label(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "resolved_outcome_followup_score",
            "correction_adoption_score",
            "stale_memory_reduction_score",
            "evidence_reuse_quality_score",
            "peer_review_coverage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "review_latency_seconds",
            _require_nonnegative_decimal(
                "review_latency_seconds",
                self.review_latency_seconds,
            ),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchTeamReviewCalibrationMemoryBridgeRow:
    review_group: str
    domain_label: str
    reviewer_label: str
    observed_at: datetime
    observation_age_seconds: Decimal
    resolved_outcome_followup_score: Decimal
    correction_adoption_score: Decimal
    stale_memory_reduction_score: Decimal
    evidence_reuse_quality_score: Decimal
    peer_review_coverage_score: Decimal
    review_latency_seconds: Decimal
    review_latency_score: Decimal
    calibration_memory_score: Decimal
    review_quality_score: Decimal
    bridge_score: Decimal
    bridge_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamReviewCalibrationMemoryBridgeRow:
            raise TypeError(
                "ResearchTeamReviewCalibrationMemoryBridgeRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamReviewCalibrationMemoryBridgeRow, "row")
        for field_name in ("review_group", "domain_label", "reviewer_label"):
            object.__setattr__(
                self,
                field_name,
                _require_public_label(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "observation_age_seconds",
            "review_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "resolved_outcome_followup_score",
            "correction_adoption_score",
            "stale_memory_reduction_score",
            "evidence_reuse_quality_score",
            "peer_review_coverage_score",
            "review_latency_score",
            "calibration_memory_score",
            "review_quality_score",
            "bridge_score",
            "bridge_pressure_score",
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
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamReviewCalibrationMemoryBridgeReport:
    generated_at: datetime
    config_version: str
    status: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    outcome_followup_gap_count: Decimal
    correction_adoption_gap_count: Decimal
    stale_memory_reduction_gap_count: Decimal
    evidence_reuse_quality_gap_count: Decimal
    peer_review_coverage_gap_count: Decimal
    review_latency_gap_count: Decimal
    bridge_score_gap_count: Decimal
    average_calibration_memory_score: Decimal
    average_review_quality_score: Decimal
    average_bridge_score: Decimal
    lowest_bridge_score: Decimal
    highest_bridge_pressure_score: Decimal
    highest_review_latency_seconds: Decimal
    oldest_observation_age_seconds: Decimal
    rows: tuple[ResearchTeamReviewCalibrationMemoryBridgeRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchTeamReviewCalibrationMemoryBridgeReport:
            raise TypeError(
                "ResearchTeamReviewCalibrationMemoryBridgeReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamReviewCalibrationMemoryBridgeReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        object.__setattr__(self, "status", _require_status("status", self.status))
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "outcome_followup_gap_count",
            "correction_adoption_gap_count",
            "stale_memory_reduction_gap_count",
            "evidence_reuse_quality_gap_count",
            "peer_review_coverage_gap_count",
            "review_latency_gap_count",
            "bridge_score_gap_count",
            "highest_review_latency_seconds",
            "oldest_observation_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_calibration_memory_score",
            "average_review_quality_score",
            "average_bridge_score",
            "lowest_bridge_score",
            "highest_bridge_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_public_payload(self)
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report payload")
        object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_team_review_calibration_memory_bridge_report_payload(self)


def build_research_team_review_calibration_memory_bridge_report(
    observations: Sequence[ResearchTeamReviewCalibrationMemoryBridgeObservation],
    *,
    config: ResearchTeamReviewCalibrationMemoryBridgeConfig | None = None,
    generated_at: datetime,
) -> ResearchTeamReviewCalibrationMemoryBridgeReport:
    cfg = config or ResearchTeamReviewCalibrationMemoryBridgeConfig()
    if type(cfg) is not ResearchTeamReviewCalibrationMemoryBridgeConfig:
        raise ValueError(
            "config must be exactly ResearchTeamReviewCalibrationMemoryBridgeConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(
        observations,
        generated_at=generated_at_utc,
    )
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    config=cfg,
                    generated_at=generated_at_utc,
                )
                for observation in normalized_observations
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchTeamReviewCalibrationMemoryBridgeReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        status=_report_status(rows),
        observation_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        outcome_followup_gap_count=_reason_count(
            rows,
            (OUTCOME_FOLLOWUP_BLOCK_REASON, OUTCOME_FOLLOWUP_WATCH_REASON),
        ),
        correction_adoption_gap_count=_reason_count(
            rows,
            (CORRECTION_ADOPTION_BLOCK_REASON, CORRECTION_ADOPTION_WATCH_REASON),
        ),
        stale_memory_reduction_gap_count=_reason_count(
            rows,
            (STALE_MEMORY_REDUCTION_BLOCK_REASON, STALE_MEMORY_REDUCTION_WATCH_REASON),
        ),
        evidence_reuse_quality_gap_count=_reason_count(
            rows,
            (EVIDENCE_REUSE_QUALITY_BLOCK_REASON, EVIDENCE_REUSE_QUALITY_WATCH_REASON),
        ),
        peer_review_coverage_gap_count=_reason_count(
            rows,
            (PEER_REVIEW_COVERAGE_BLOCK_REASON, PEER_REVIEW_COVERAGE_WATCH_REASON),
        ),
        review_latency_gap_count=_reason_count(
            rows,
            (REVIEW_LATENCY_BLOCK_REASON, REVIEW_LATENCY_WATCH_REASON),
        ),
        bridge_score_gap_count=_reason_count(
            rows,
            (BRIDGE_SCORE_BLOCK_REASON, BRIDGE_SCORE_WATCH_REASON),
        ),
        average_calibration_memory_score=_average(
            tuple(row.calibration_memory_score for row in rows),
        ),
        average_review_quality_score=_average(
            tuple(row.review_quality_score for row in rows),
        ),
        average_bridge_score=_average(tuple(row.bridge_score for row in rows)),
        lowest_bridge_score=min((row.bridge_score for row in rows), default=ZERO).quantize(
            QUANT,
        ),
        highest_bridge_pressure_score=max(
            (row.bridge_pressure_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        highest_review_latency_seconds=max(
            (row.review_latency_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        oldest_observation_age_seconds=max(
            (row.observation_age_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_team_review_calibration_memory_bridge_report_payload(
    report: ResearchTeamReviewCalibrationMemoryBridgeReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamReviewCalibrationMemoryBridgeReport:
        raise ValueError(
            "report must be exactly ResearchTeamReviewCalibrationMemoryBridgeReport",
        )
    validate_research_team_review_calibration_memory_bridge_report_digest(report)
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _reject_raw_payload_numbers(payload)
    return payload


def research_team_review_calibration_memory_bridge_report_digest(
    report: ResearchTeamReviewCalibrationMemoryBridgeReport,
) -> str:
    if type(report) is not ResearchTeamReviewCalibrationMemoryBridgeReport:
        raise ValueError(
            "report must be exactly ResearchTeamReviewCalibrationMemoryBridgeReport",
        )
    validate_research_team_review_calibration_memory_bridge_report_digest(report)
    return report.derived_validation_digest


def validate_research_team_review_calibration_memory_bridge_report_digest(
    report: ResearchTeamReviewCalibrationMemoryBridgeReport,
) -> None:
    if type(report) is not ResearchTeamReviewCalibrationMemoryBridgeReport:
        raise ValueError(
            "report must be exactly ResearchTeamReviewCalibrationMemoryBridgeReport",
        )
    _require_sha256("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_digest_from_public_payload(report):
        raise ValueError("derived_validation_digest must match report payload")


def _normalize_observations(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchTeamReviewCalibrationMemoryBridgeObservation, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    observations = tuple(value)
    seen: set[tuple[str, str, str, datetime]] = set()
    for observation in observations:
        if type(observation) is not ResearchTeamReviewCalibrationMemoryBridgeObservation:
            raise ValueError(
                "observations must contain "
                "ResearchTeamReviewCalibrationMemoryBridgeObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")
        key = (
            observation.review_group,
            observation.domain_label,
            observation.reviewer_label,
            observation.observed_at,
        )
        if key in seen:
            raise ValueError("observations must be unique by public review labels")
        seen.add(key)
    return tuple(
        sorted(
            observations,
            key=lambda observation: (
                observation.review_group,
                observation.domain_label,
                observation.reviewer_label,
                observation.observed_at,
            ),
        ),
    )


def _row_from_observation(
    observation: ResearchTeamReviewCalibrationMemoryBridgeObservation,
    *,
    config: ResearchTeamReviewCalibrationMemoryBridgeConfig,
    generated_at: datetime,
) -> ResearchTeamReviewCalibrationMemoryBridgeRow:
    age_seconds = _age_seconds(generated_at, observation.observed_at)
    review_latency_score = _review_latency_score(
        observation.review_latency_seconds,
        config=config,
    )
    calibration_memory_score = _calibration_memory_score(
        resolved_outcome_followup_score=observation.resolved_outcome_followup_score,
        correction_adoption_score=observation.correction_adoption_score,
        stale_memory_reduction_score=observation.stale_memory_reduction_score,
    )
    review_quality_score = _review_quality_score(
        evidence_reuse_quality_score=observation.evidence_reuse_quality_score,
        peer_review_coverage_score=observation.peer_review_coverage_score,
        review_latency_score=review_latency_score,
    )
    bridge_score = _bridge_score(
        resolved_outcome_followup_score=observation.resolved_outcome_followup_score,
        correction_adoption_score=observation.correction_adoption_score,
        stale_memory_reduction_score=observation.stale_memory_reduction_score,
        evidence_reuse_quality_score=observation.evidence_reuse_quality_score,
        peer_review_coverage_score=observation.peer_review_coverage_score,
        review_latency_score=review_latency_score,
    )
    reason_codes = _row_reason_codes(
        resolved_outcome_followup_score=observation.resolved_outcome_followup_score,
        correction_adoption_score=observation.correction_adoption_score,
        stale_memory_reduction_score=observation.stale_memory_reduction_score,
        evidence_reuse_quality_score=observation.evidence_reuse_quality_score,
        peer_review_coverage_score=observation.peer_review_coverage_score,
        review_latency_seconds=observation.review_latency_seconds,
        bridge_score=bridge_score,
        config=config,
    )
    return ResearchTeamReviewCalibrationMemoryBridgeRow(
        review_group=observation.review_group,
        domain_label=observation.domain_label,
        reviewer_label=observation.reviewer_label,
        observed_at=observation.observed_at,
        observation_age_seconds=age_seconds,
        resolved_outcome_followup_score=observation.resolved_outcome_followup_score,
        correction_adoption_score=observation.correction_adoption_score,
        stale_memory_reduction_score=observation.stale_memory_reduction_score,
        evidence_reuse_quality_score=observation.evidence_reuse_quality_score,
        peer_review_coverage_score=observation.peer_review_coverage_score,
        review_latency_seconds=observation.review_latency_seconds,
        review_latency_score=review_latency_score,
        calibration_memory_score=calibration_memory_score,
        review_quality_score=review_quality_score,
        bridge_score=bridge_score,
        bridge_pressure_score=(ONE - bridge_score).quantize(QUANT),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    resolved_outcome_followup_score: Decimal,
    correction_adoption_score: Decimal,
    stale_memory_reduction_score: Decimal,
    evidence_reuse_quality_score: Decimal,
    peer_review_coverage_score: Decimal,
    review_latency_seconds: Decimal,
    bridge_score: Decimal,
    config: ResearchTeamReviewCalibrationMemoryBridgeConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if resolved_outcome_followup_score < config.min_watch_outcome_followup_score:
        reason_codes.append(OUTCOME_FOLLOWUP_BLOCK_REASON)
    elif resolved_outcome_followup_score < config.min_pass_outcome_followup_score:
        reason_codes.append(OUTCOME_FOLLOWUP_WATCH_REASON)
    if correction_adoption_score < config.min_watch_correction_adoption_score:
        reason_codes.append(CORRECTION_ADOPTION_BLOCK_REASON)
    elif correction_adoption_score < config.min_pass_correction_adoption_score:
        reason_codes.append(CORRECTION_ADOPTION_WATCH_REASON)
    if stale_memory_reduction_score < config.min_watch_stale_memory_reduction_score:
        reason_codes.append(STALE_MEMORY_REDUCTION_BLOCK_REASON)
    elif stale_memory_reduction_score < config.min_pass_stale_memory_reduction_score:
        reason_codes.append(STALE_MEMORY_REDUCTION_WATCH_REASON)
    if evidence_reuse_quality_score < config.min_watch_evidence_reuse_quality_score:
        reason_codes.append(EVIDENCE_REUSE_QUALITY_BLOCK_REASON)
    elif evidence_reuse_quality_score < config.min_pass_evidence_reuse_quality_score:
        reason_codes.append(EVIDENCE_REUSE_QUALITY_WATCH_REASON)
    if peer_review_coverage_score < config.min_watch_peer_review_coverage_score:
        reason_codes.append(PEER_REVIEW_COVERAGE_BLOCK_REASON)
    elif peer_review_coverage_score < config.min_pass_peer_review_coverage_score:
        reason_codes.append(PEER_REVIEW_COVERAGE_WATCH_REASON)
    if review_latency_seconds > config.max_watch_review_latency_seconds:
        reason_codes.append(REVIEW_LATENCY_BLOCK_REASON)
    elif review_latency_seconds > config.max_pass_review_latency_seconds:
        reason_codes.append(REVIEW_LATENCY_WATCH_REASON)
    if bridge_score < config.min_watch_bridge_score:
        reason_codes.append(BRIDGE_SCORE_BLOCK_REASON)
    elif bridge_score < config.min_pass_bridge_score:
        reason_codes.append(BRIDGE_SCORE_WATCH_REASON)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes) or (CLEAR_REASON,),
        ROW_REASON_CODES,
    )


def _calibration_memory_score(
    *,
    resolved_outcome_followup_score: Decimal,
    correction_adoption_score: Decimal,
    stale_memory_reduction_score: Decimal,
) -> Decimal:
    return _average(
        (
            resolved_outcome_followup_score,
            correction_adoption_score,
            stale_memory_reduction_score,
        ),
    )


def _review_quality_score(
    *,
    evidence_reuse_quality_score: Decimal,
    peer_review_coverage_score: Decimal,
    review_latency_score: Decimal,
) -> Decimal:
    return _average(
        (
            evidence_reuse_quality_score,
            peer_review_coverage_score,
            review_latency_score,
        ),
    )


def _bridge_score(
    *,
    resolved_outcome_followup_score: Decimal,
    correction_adoption_score: Decimal,
    stale_memory_reduction_score: Decimal,
    evidence_reuse_quality_score: Decimal,
    peer_review_coverage_score: Decimal,
    review_latency_score: Decimal,
) -> Decimal:
    return _average(
        (
            resolved_outcome_followup_score,
            correction_adoption_score,
            stale_memory_reduction_score,
            evidence_reuse_quality_score,
            peer_review_coverage_score,
            review_latency_score,
        ),
    )


def _review_latency_score(
    review_latency_seconds: Decimal,
    *,
    config: ResearchTeamReviewCalibrationMemoryBridgeConfig,
) -> Decimal:
    if review_latency_seconds <= config.max_pass_review_latency_seconds:
        return ONE
    if review_latency_seconds >= config.max_watch_review_latency_seconds:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        latency_window = (
            config.max_watch_review_latency_seconds
            - config.max_pass_review_latency_seconds
        )
        return (
            (config.max_watch_review_latency_seconds - review_latency_seconds)
            / latency_window
        ).quantize(QUANT)


def _report_status(rows: tuple[ResearchTeamReviewCalibrationMemoryBridgeRow, ...]) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return STATUS_BLOCK
    if any(reason.endswith("_watch") for reason in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchTeamReviewCalibrationMemoryBridgeRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reason_codes: list[str] = []
    if any(row.status == STATUS_BLOCK for row in rows):
        reason_codes.append(REPORT_BLOCK_PRESENT_REASON)
    if any(row.status == STATUS_WATCH for row in rows):
        reason_codes.append(REPORT_WATCH_PRESENT_REASON)
    reason_mappings = (
        (
            REPORT_OUTCOME_FOLLOWUP_GAP_REASON,
            (OUTCOME_FOLLOWUP_BLOCK_REASON, OUTCOME_FOLLOWUP_WATCH_REASON),
        ),
        (
            REPORT_CORRECTION_ADOPTION_GAP_REASON,
            (CORRECTION_ADOPTION_BLOCK_REASON, CORRECTION_ADOPTION_WATCH_REASON),
        ),
        (
            REPORT_STALE_MEMORY_REDUCTION_GAP_REASON,
            (STALE_MEMORY_REDUCTION_BLOCK_REASON, STALE_MEMORY_REDUCTION_WATCH_REASON),
        ),
        (
            REPORT_EVIDENCE_REUSE_QUALITY_GAP_REASON,
            (EVIDENCE_REUSE_QUALITY_BLOCK_REASON, EVIDENCE_REUSE_QUALITY_WATCH_REASON),
        ),
        (
            REPORT_PEER_REVIEW_COVERAGE_GAP_REASON,
            (PEER_REVIEW_COVERAGE_BLOCK_REASON, PEER_REVIEW_COVERAGE_WATCH_REASON),
        ),
        (
            REPORT_REVIEW_LATENCY_GAP_REASON,
            (REVIEW_LATENCY_BLOCK_REASON, REVIEW_LATENCY_WATCH_REASON),
        ),
        (
            REPORT_BRIDGE_SCORE_GAP_REASON,
            (BRIDGE_SCORE_BLOCK_REASON, BRIDGE_SCORE_WATCH_REASON),
        ),
    )
    for report_reason, row_reasons in reason_mappings:
        if any(any(reason in row.reason_codes for reason in row_reasons) for row in rows):
            reason_codes.append(report_reason)
    if not reason_codes:
        reason_codes.append(REPORT_CLEAR_REASON)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes),
        REPORT_REASON_CODES,
    )


def _row_sort_key(
    row: ResearchTeamReviewCalibrationMemoryBridgeRow,
) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        -row.bridge_pressure_score,
        row.bridge_score,
        row.review_group,
        row.domain_label,
        row.reviewer_label,
    )


def _status_count(
    rows: tuple[ResearchTeamReviewCalibrationMemoryBridgeRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchTeamReviewCalibrationMemoryBridgeRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if any(reason in row.reason_codes for reason in reason_codes)),
    )


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO) / Decimal(len(values))).quantize(QUANT)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    generated_at_utc = _as_utc("generated_at", generated_at)
    observed_at_utc = _as_utc("observed_at", observed_at)
    delta = generated_at_utc - observed_at_utc
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds).quantize(QUANT)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if seconds < ZERO:
        raise ValueError("observed_at must not be in the future")
    return seconds.quantize(QUANT)


def _validate_config(
    config: ResearchTeamReviewCalibrationMemoryBridgeConfig,
) -> None:
    if (
        config.max_pass_review_latency_seconds
        >= config.max_watch_review_latency_seconds
    ):
        raise ValueError(
            "max_pass_review_latency_seconds must be less than watch latency",
        )
    if (
        config.min_watch_outcome_followup_score
        > config.min_pass_outcome_followup_score
    ):
        raise ValueError("min_watch_outcome_followup_score must not exceed pass")
    if (
        config.min_watch_correction_adoption_score
        > config.min_pass_correction_adoption_score
    ):
        raise ValueError("min_watch_correction_adoption_score must not exceed pass")
    if (
        config.min_watch_stale_memory_reduction_score
        > config.min_pass_stale_memory_reduction_score
    ):
        raise ValueError("min_watch_stale_memory_reduction_score must not exceed pass")
    if (
        config.min_watch_evidence_reuse_quality_score
        > config.min_pass_evidence_reuse_quality_score
    ):
        raise ValueError("min_watch_evidence_reuse_quality_score must not exceed pass")
    if (
        config.min_watch_peer_review_coverage_score
        > config.min_pass_peer_review_coverage_score
    ):
        raise ValueError("min_watch_peer_review_coverage_score must not exceed pass")
    if config.min_watch_bridge_score > config.min_pass_bridge_score:
        raise ValueError("min_watch_bridge_score must not exceed pass")


def _validate_row(row: ResearchTeamReviewCalibrationMemoryBridgeRow) -> None:
    expected_calibration_memory_score = _calibration_memory_score(
        resolved_outcome_followup_score=row.resolved_outcome_followup_score,
        correction_adoption_score=row.correction_adoption_score,
        stale_memory_reduction_score=row.stale_memory_reduction_score,
    )
    if row.calibration_memory_score != expected_calibration_memory_score:
        raise ValueError("calibration_memory_score must match row components")
    expected_review_quality_score = _review_quality_score(
        evidence_reuse_quality_score=row.evidence_reuse_quality_score,
        peer_review_coverage_score=row.peer_review_coverage_score,
        review_latency_score=row.review_latency_score,
    )
    if row.review_quality_score != expected_review_quality_score:
        raise ValueError("review_quality_score must match row components")
    expected_bridge_score = _bridge_score(
        resolved_outcome_followup_score=row.resolved_outcome_followup_score,
        correction_adoption_score=row.correction_adoption_score,
        stale_memory_reduction_score=row.stale_memory_reduction_score,
        evidence_reuse_quality_score=row.evidence_reuse_quality_score,
        peer_review_coverage_score=row.peer_review_coverage_score,
        review_latency_score=row.review_latency_score,
    )
    if row.bridge_score != expected_bridge_score:
        raise ValueError("bridge_score must match row components")
    if row.bridge_pressure_score != (ONE - row.bridge_score).quantize(QUANT):
        raise ValueError("bridge_pressure_score must match bridge_score")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.reason_codes == (CLEAR_REASON,) and row.status != STATUS_PASS:
        raise ValueError("clear reason requires pass status")
    if row.status == STATUS_PASS and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("pass status requires clear reason")


def _validate_report(report: ResearchTeamReviewCalibrationMemoryBridgeReport) -> None:
    rows = report.rows
    expected_values = {
        "observation_count": _count_decimal(len(rows)),
        "pass_count": _status_count(rows, STATUS_PASS),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "block_count": _status_count(rows, STATUS_BLOCK),
        "outcome_followup_gap_count": _reason_count(
            rows,
            (OUTCOME_FOLLOWUP_BLOCK_REASON, OUTCOME_FOLLOWUP_WATCH_REASON),
        ),
        "correction_adoption_gap_count": _reason_count(
            rows,
            (CORRECTION_ADOPTION_BLOCK_REASON, CORRECTION_ADOPTION_WATCH_REASON),
        ),
        "stale_memory_reduction_gap_count": _reason_count(
            rows,
            (STALE_MEMORY_REDUCTION_BLOCK_REASON, STALE_MEMORY_REDUCTION_WATCH_REASON),
        ),
        "evidence_reuse_quality_gap_count": _reason_count(
            rows,
            (EVIDENCE_REUSE_QUALITY_BLOCK_REASON, EVIDENCE_REUSE_QUALITY_WATCH_REASON),
        ),
        "peer_review_coverage_gap_count": _reason_count(
            rows,
            (PEER_REVIEW_COVERAGE_BLOCK_REASON, PEER_REVIEW_COVERAGE_WATCH_REASON),
        ),
        "review_latency_gap_count": _reason_count(
            rows,
            (REVIEW_LATENCY_BLOCK_REASON, REVIEW_LATENCY_WATCH_REASON),
        ),
        "bridge_score_gap_count": _reason_count(
            rows,
            (BRIDGE_SCORE_BLOCK_REASON, BRIDGE_SCORE_WATCH_REASON),
        ),
        "average_calibration_memory_score": _average(
            tuple(row.calibration_memory_score for row in rows),
        ),
        "average_review_quality_score": _average(
            tuple(row.review_quality_score for row in rows),
        ),
        "average_bridge_score": _average(tuple(row.bridge_score for row in rows)),
        "lowest_bridge_score": min(
            (row.bridge_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        "highest_bridge_pressure_score": max(
            (row.bridge_pressure_score for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        "highest_review_latency_seconds": max(
            (row.review_latency_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
        "oldest_observation_age_seconds": max(
            (row.observation_age_seconds for row in rows),
            default=ZERO,
        ).quantize(QUANT),
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _normalize_rows(
    value: object,
) -> tuple[ResearchTeamReviewCalibrationMemoryBridgeRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str, str, datetime]] = set()
    for row in rows:
        if type(row) is not ResearchTeamReviewCalibrationMemoryBridgeRow:
            raise ValueError(
                "rows must contain ResearchTeamReviewCalibrationMemoryBridgeRow",
            )
        _require_hard_flags("row", row)
        key = (row.review_group, row.domain_label, row.reviewer_label, row.observed_at)
        if key in seen:
            raise ValueError("rows must be unique by public review labels")
        seen.add(key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")
    return rows


def _normalize_reason_codes(
    name: str,
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{name} must be a tuple or list")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{name} must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_public_label("reason_code", reason_code)
        if reason_code not in allowed_reason_codes:
            raise ValueError(f"{name} contains an unknown reason code")
        if reason_code in seen:
            raise ValueError(f"{name} must be unique")
        seen.add(reason_code)
    if CLEAR_REASON in reason_codes and len(reason_codes) != 1:
        raise ValueError("clear reason must stand alone")
    if EMPTY_REASON in reason_codes and len(reason_codes) != 1:
        raise ValueError("empty reason must stand alone")
    if REPORT_CLEAR_REASON in reason_codes and len(reason_codes) != 1:
        raise ValueError("report clear reason must stand alone")
    return reason_codes


def _report_digest_from_public_payload(
    report: ResearchTeamReviewCalibrationMemoryBridgeReport,
) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a dict")
    payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload("digest payload", payload)
    _reject_raw_payload_numbers(payload)
    canonical_payload = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        return format(value.quantize(QUANT), "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (tuple, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported JSON payload value: {type(value).__name__}")


def _reject_raw_payload_numbers(value: object) -> None:
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_raw_payload_numbers(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_raw_payload_numbers(item)
        return
    if type(value) in (Decimal, float):
        raise ValueError("payload must not expose raw numeric values")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} contains a non-string public key")
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
                raise ValueError(f"{label} contains unsafe public key")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, str):
        lowered_value = value.lower()
        if any(fragment in lowered_value for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe text")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_label(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public label")
    lowered_value = value.lower()
    if any(fragment in lowered_value for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe text")
    return value


def _require_status(name: str, value: object) -> str:
    if type(value) is not str or value not in RESEARCH_TEAM_REVIEW_CALIBRATION_MEMORY_BRIDGE_STATUSES:
        raise ValueError(f"{name} must be one of: pass, watch, block")
    return value


def _require_sha256(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not SHA256_HEX_RE.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 hex digest")


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _require_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _require_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _count_decimal(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(QUANT)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_RESEARCH_TEAM_REVIEW_CALIBRATION_MEMORY_BRIDGE_REPORT_CONFIG_VERSION",
    "RESEARCH_TEAM_REVIEW_CALIBRATION_MEMORY_BRIDGE_STATUSES",
    "ResearchTeamReviewCalibrationMemoryBridgeConfig",
    "ResearchTeamReviewCalibrationMemoryBridgeObservation",
    "ResearchTeamReviewCalibrationMemoryBridgeReport",
    "ResearchTeamReviewCalibrationMemoryBridgeRow",
    "build_research_team_review_calibration_memory_bridge_report",
    "research_team_review_calibration_memory_bridge_report_digest",
    "research_team_review_calibration_memory_bridge_report_payload",
    "validate_research_team_review_calibration_memory_bridge_report_digest",
)
