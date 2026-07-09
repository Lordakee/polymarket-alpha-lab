"""Public-safe report-only domain memory drift watch reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_DRIFT_WATCH_REPORT_CONFIG_VERSION = (
    "research-team-domain-memory-drift-watch-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
PUBLIC_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_SORT_ORDER = {
    STATUS_BLOCK: Decimal("0.000000"),
    STATUS_WATCH: Decimal("1.000000"),
    STATUS_PASS: Decimal("2.000000"),
}

PUBLIC_DOMAIN_CATEGORIES = (
    "politics",
    "crypto",
    "equities",
    "commodities",
    "football",
    "basketball",
    "other",
)

CLEAR_REASON = "domain_memory_drift_clear"
NO_INPUTS_REASON = "domain_memory_drift_report_no_inputs"
REPORT_PASS_REASON = "domain_memory_drift_report_pass"
REPORT_WATCH_REASON = "domain_memory_drift_report_watch"
REPORT_BLOCK_REASON = "domain_memory_drift_report_block"

STALE_MEMORY_REUSE_BLOCK_REASON = "domain_memory_drift_stale_memory_reuse_block"
CALIBRATION_DRIFT_BLOCK_REASON = "domain_memory_drift_calibration_drift_block"
CORRECTION_FOLLOW_THROUGH_BLOCK_REASON = (
    "domain_memory_drift_correction_follow_through_block"
)
EVIDENCE_REUSE_QUALITY_BLOCK_REASON = (
    "domain_memory_drift_evidence_reuse_quality_block"
)
PEER_REVIEW_DEPTH_BLOCK_REASON = "domain_memory_drift_peer_review_depth_block"
REVIEW_LATENCY_BLOCK_REASON = "domain_memory_drift_review_latency_block"

STALE_MEMORY_REUSE_WATCH_REASON = "domain_memory_drift_stale_memory_reuse_watch"
CALIBRATION_DRIFT_WATCH_REASON = "domain_memory_drift_calibration_drift_watch"
CORRECTION_FOLLOW_THROUGH_WATCH_REASON = (
    "domain_memory_drift_correction_follow_through_watch"
)
EVIDENCE_REUSE_QUALITY_WATCH_REASON = (
    "domain_memory_drift_evidence_reuse_quality_watch"
)
PEER_REVIEW_DEPTH_WATCH_REASON = "domain_memory_drift_peer_review_depth_watch"
REVIEW_LATENCY_WATCH_REASON = "domain_memory_drift_review_latency_watch"

BLOCK_REASON_CODES = (
    STALE_MEMORY_REUSE_BLOCK_REASON,
    CALIBRATION_DRIFT_BLOCK_REASON,
    CORRECTION_FOLLOW_THROUGH_BLOCK_REASON,
    EVIDENCE_REUSE_QUALITY_BLOCK_REASON,
    PEER_REVIEW_DEPTH_BLOCK_REASON,
    REVIEW_LATENCY_BLOCK_REASON,
)
WATCH_REASON_CODES = (
    STALE_MEMORY_REUSE_WATCH_REASON,
    CALIBRATION_DRIFT_WATCH_REASON,
    CORRECTION_FOLLOW_THROUGH_WATCH_REASON,
    EVIDENCE_REUSE_QUALITY_WATCH_REASON,
    PEER_REVIEW_DEPTH_WATCH_REASON,
    REVIEW_LATENCY_WATCH_REASON,
)
ROW_REASON_CODES = BLOCK_REASON_CODES + WATCH_REASON_CODES + (CLEAR_REASON,)
REPORT_REASON_CODES = (
    NO_INPUTS_REASON,
    REPORT_BLOCK_REASON,
    REPORT_WATCH_REASON,
    REPORT_PASS_REASON,
) + ROW_REASON_CODES
REASON_CODE_COUNT_ORDER = (
    NO_INPUTS_REASON,
    *BLOCK_REASON_CODES,
    *WATCH_REASON_CODES,
    CLEAR_REASON,
    REPORT_BLOCK_REASON,
    REPORT_WATCH_REASON,
    REPORT_PASS_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
HEX_DIGITS = frozenset("0123456789abcdef")
VALIDATION_DIGEST_ALGORITHM = "sha256"

UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "raw",
        "candidate",
        "market",
        "slug",
        "question",
        "http://",
        "https://",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "trading",
        "live",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_DRIFT_WATCH_REPORT_CONFIG_VERSION",
    "PUBLIC_DOMAIN_CATEGORIES",
    "PUBLIC_STATUSES",
    "ResearchTeamDomainMemoryDriftWatchConfig",
    "ResearchTeamDomainMemoryDriftWatchObservation",
    "ResearchTeamDomainMemoryDriftWatchRow",
    "ResearchTeamDomainMemoryDriftWatchReasonCodeCount",
    "ResearchTeamDomainMemoryDriftWatchReport",
    "build_research_team_domain_memory_drift_watch_report",
    "research_team_domain_memory_drift_watch_report_payload",
    "research_team_domain_memory_drift_watch_report_digest",
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
class ResearchTeamDomainMemoryDriftWatchConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_DRIFT_WATCH_REPORT_CONFIG_VERSION
    )
    max_pass_stale_memory_reuse_ratio: Decimal = Decimal("0.050000")
    max_watch_stale_memory_reuse_ratio: Decimal = Decimal("0.150000")
    max_pass_calibration_drift_score: Decimal = Decimal("0.050000")
    max_watch_calibration_drift_score: Decimal = Decimal("0.120000")
    min_pass_correction_follow_through_ratio: Decimal = Decimal("0.900000")
    min_watch_correction_follow_through_ratio: Decimal = Decimal("0.700000")
    min_pass_evidence_reuse_quality_score: Decimal = Decimal("0.850000")
    min_watch_evidence_reuse_quality_score: Decimal = Decimal("0.650000")
    min_pass_peer_review_depth_score: Decimal = Decimal("0.800000")
    min_watch_peer_review_depth_score: Decimal = Decimal("0.600000")
    max_pass_review_latency_seconds: Decimal = Decimal("86400.000000")
    max_watch_review_latency_seconds: Decimal = Decimal("259200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainMemoryDriftWatchConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_supported_config_version(self.config_version),
        )
        for field_name in (
            "max_pass_stale_memory_reuse_ratio",
            "max_watch_stale_memory_reuse_ratio",
            "max_pass_calibration_drift_score",
            "max_watch_calibration_drift_score",
            "min_pass_correction_follow_through_ratio",
            "min_watch_correction_follow_through_ratio",
            "min_pass_evidence_reuse_quality_score",
            "min_watch_evidence_reuse_quality_score",
            "min_pass_peer_review_depth_score",
            "min_watch_peer_review_depth_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_review_latency_seconds",
            "max_watch_review_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainMemoryDriftWatchObservation(_FinalPublicDataclass):
    domain_category: str
    team_key: str
    observed_at: datetime
    stale_memory_reuse_ratio: Decimal
    calibration_drift_score: Decimal
    correction_follow_through_ratio: Decimal
    evidence_reuse_quality_score: Decimal
    peer_review_depth_score: Decimal
    review_latency_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainMemoryDriftWatchObservation,
            "observation",
        )
        object.__setattr__(
            self,
            "domain_category",
            _require_public_category("domain_category", self.domain_category),
        )
        object.__setattr__(
            self,
            "team_key",
            _require_public_string("team_key", self.team_key),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "stale_memory_reuse_ratio",
            "calibration_drift_score",
            "correction_follow_through_ratio",
            "evidence_reuse_quality_score",
            "peer_review_depth_score",
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
class ResearchTeamDomainMemoryDriftWatchRow(_FinalPublicDataclass):
    domain_category: str
    team_digest: str
    status: str
    observation_age_seconds: Decimal
    stale_memory_reuse_ratio: Decimal
    calibration_drift_score: Decimal
    correction_follow_through_ratio: Decimal
    evidence_reuse_quality_score: Decimal
    peer_review_depth_score: Decimal
    review_latency_seconds: Decimal
    reason_codes: tuple[str, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainMemoryDriftWatchRow, "row")
        object.__setattr__(
            self,
            "domain_category",
            _require_public_category("domain_category", self.domain_category),
        )
        object.__setattr__(
            self,
            "team_digest",
            _require_validation_digest("team_digest", self.team_digest),
        )
        object.__setattr__(self, "status", _require_status("status", self.status))
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
            "stale_memory_reuse_ratio",
            "calibration_drift_score",
            "correction_follow_through_ratio",
            "evidence_reuse_quality_score",
            "peer_review_depth_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row_status(self.status, self.reason_codes)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        object.__setattr__(
            self,
            "validation_digest",
            _normalize_validation_digest(
                "validation_digest",
                self.validation_digest,
                _row_validation_digest(self),
            ),
        )


@dataclass(frozen=True)
class ResearchTeamDomainMemoryDriftWatchReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    team_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainMemoryDriftWatchReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code(self.reason_code, REASON_CODE_COUNT_ORDER),
        )
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "team_ratio",
            _require_ratio_decimal("team_ratio", self.team_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamDomainMemoryDriftWatchReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    domain_team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    drift_team_count: Decimal
    stale_memory_reuse_team_count: Decimal
    calibration_drift_team_count: Decimal
    correction_gap_team_count: Decimal
    evidence_reuse_gap_team_count: Decimal
    peer_review_gap_team_count: Decimal
    review_latency_gap_team_count: Decimal
    average_stale_memory_reuse_ratio: Decimal
    average_calibration_drift_score: Decimal
    average_correction_follow_through_ratio: Decimal
    average_evidence_reuse_quality_score: Decimal
    average_peer_review_depth_score: Decimal
    max_review_latency_seconds: Decimal
    rows: tuple[ResearchTeamDomainMemoryDriftWatchRow, ...]
    reason_code_counts: tuple[ResearchTeamDomainMemoryDriftWatchReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainMemoryDriftWatchReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_supported_config_version(self.config_version),
        )
        object.__setattr__(self, "status", _require_status("status", self.status))
        for field_name in (
            "domain_team_count",
            "pass_count",
            "watch_count",
            "block_count",
            "drift_team_count",
            "stale_memory_reuse_team_count",
            "calibration_drift_team_count",
            "correction_gap_team_count",
            "evidence_reuse_gap_team_count",
            "peer_review_gap_team_count",
            "review_latency_gap_team_count",
            "max_review_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_stale_memory_reuse_ratio",
            "average_calibration_drift_score",
            "average_correction_follow_through_ratio",
            "average_evidence_reuse_quality_score",
            "average_peer_review_depth_score",
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
            _normalize_reason_codes(self.reason_codes, REPORT_REASON_CODES),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        object.__setattr__(
            self,
            "validation_digest",
            _normalize_validation_digest(
                "validation_digest",
                self.validation_digest,
                _report_validation_digest(self),
            ),
        )

    @property
    def payload(self) -> dict[str, Any]:
        return research_team_domain_memory_drift_watch_report_payload(self)


def build_research_team_domain_memory_drift_watch_report(
    observations: Iterable[object],
    *,
    config: ResearchTeamDomainMemoryDriftWatchConfig,
    generated_at: datetime,
) -> ResearchTeamDomainMemoryDriftWatchReport:
    if type(config) is not ResearchTeamDomainMemoryDriftWatchConfig:
        raise ValueError("config must be a ResearchTeamDomainMemoryDriftWatchConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_observations(observations)
    for item in items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    item,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for item in items
            ),
            key=_row_sort_key,
        ),
    )
    status = _report_status(rows)
    reason_codes = _report_reason_codes(rows, status)
    reason_code_counts = _reason_code_counts(rows, reason_codes)
    return ResearchTeamDomainMemoryDriftWatchReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=status,
        domain_team_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        drift_team_count=_decimal_count(
            sum(1 for row in rows if row.status != STATUS_PASS),
        ),
        stale_memory_reuse_team_count=_reason_count_any(
            rows,
            (STALE_MEMORY_REUSE_BLOCK_REASON, STALE_MEMORY_REUSE_WATCH_REASON),
        ),
        calibration_drift_team_count=_reason_count_any(
            rows,
            (CALIBRATION_DRIFT_BLOCK_REASON, CALIBRATION_DRIFT_WATCH_REASON),
        ),
        correction_gap_team_count=_reason_count_any(
            rows,
            (
                CORRECTION_FOLLOW_THROUGH_BLOCK_REASON,
                CORRECTION_FOLLOW_THROUGH_WATCH_REASON,
            ),
        ),
        evidence_reuse_gap_team_count=_reason_count_any(
            rows,
            (EVIDENCE_REUSE_QUALITY_BLOCK_REASON, EVIDENCE_REUSE_QUALITY_WATCH_REASON),
        ),
        peer_review_gap_team_count=_reason_count_any(
            rows,
            (PEER_REVIEW_DEPTH_BLOCK_REASON, PEER_REVIEW_DEPTH_WATCH_REASON),
        ),
        review_latency_gap_team_count=_reason_count_any(
            rows,
            (REVIEW_LATENCY_BLOCK_REASON, REVIEW_LATENCY_WATCH_REASON),
        ),
        average_stale_memory_reuse_ratio=_mean(
            tuple(row.stale_memory_reuse_ratio for row in rows),
        ),
        average_calibration_drift_score=_mean(
            tuple(row.calibration_drift_score for row in rows),
        ),
        average_correction_follow_through_ratio=_mean(
            tuple(row.correction_follow_through_ratio for row in rows),
        ),
        average_evidence_reuse_quality_score=_mean(
            tuple(row.evidence_reuse_quality_score for row in rows),
        ),
        average_peer_review_depth_score=_mean(
            tuple(row.peer_review_depth_score for row in rows),
        ),
        max_review_latency_seconds=_max_decimal(
            tuple(row.review_latency_seconds for row in rows),
        ),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_team_domain_memory_drift_watch_report_payload(
    report: ResearchTeamDomainMemoryDriftWatchReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamDomainMemoryDriftWatchReport:
        _validate_report_runtime(report)
        payload = _json_ready_public_payload(asdict(report), allow_decimal=True)
    elif type(report) is dict:
        _validate_payload_statuses(report)
        _reject_unsafe_public_payload("domain memory drift watch payload", report)
        payload = _canonical_report_payload(report)
    else:
        raise ValueError("report must be a ResearchTeamDomainMemoryDriftWatchReport")
    if type(payload) is not dict:
        raise ValueError("domain memory drift watch payload must be a JSON object")
    _reject_unsafe_public_payload("domain memory drift watch payload", payload)
    _validate_report_payload(payload)
    return payload


def research_team_domain_memory_drift_watch_report_digest(
    report: ResearchTeamDomainMemoryDriftWatchReport | dict[str, Any],
) -> dict[str, Any]:
    payload = research_team_domain_memory_drift_watch_report_payload(report)
    digest_keys = (
        "generated_at",
        "config_version",
        "status",
        "domain_team_count",
        "pass_count",
        "watch_count",
        "block_count",
        "drift_team_count",
        "stale_memory_reuse_team_count",
        "calibration_drift_team_count",
        "correction_gap_team_count",
        "evidence_reuse_gap_team_count",
        "peer_review_gap_team_count",
        "review_latency_gap_team_count",
        "average_stale_memory_reuse_ratio",
        "average_calibration_drift_score",
        "average_correction_follow_through_ratio",
        "average_evidence_reuse_quality_score",
        "average_peer_review_depth_score",
        "max_review_latency_seconds",
        "reason_codes",
        "validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
    return {key: payload[key] for key in digest_keys}


def _row_from_observation(
    item: ResearchTeamDomainMemoryDriftWatchObservation,
    *,
    config: ResearchTeamDomainMemoryDriftWatchConfig,
    generated_at: datetime,
) -> ResearchTeamDomainMemoryDriftWatchRow:
    reason_codes = _row_reason_codes(item, config)
    return ResearchTeamDomainMemoryDriftWatchRow(
        domain_category=item.domain_category,
        team_digest=_team_digest(item),
        status=_row_status(reason_codes),
        observation_age_seconds=_age_seconds(item.observed_at, generated_at),
        stale_memory_reuse_ratio=item.stale_memory_reuse_ratio,
        calibration_drift_score=item.calibration_drift_score,
        correction_follow_through_ratio=item.correction_follow_through_ratio,
        evidence_reuse_quality_score=item.evidence_reuse_quality_score,
        peer_review_depth_score=item.peer_review_depth_score,
        review_latency_seconds=item.review_latency_seconds,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchTeamDomainMemoryDriftWatchObservation,
    config: ResearchTeamDomainMemoryDriftWatchConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.stale_memory_reuse_ratio > config.max_watch_stale_memory_reuse_ratio:
        reason_codes.append(STALE_MEMORY_REUSE_BLOCK_REASON)
    elif item.stale_memory_reuse_ratio > config.max_pass_stale_memory_reuse_ratio:
        reason_codes.append(STALE_MEMORY_REUSE_WATCH_REASON)

    if item.calibration_drift_score > config.max_watch_calibration_drift_score:
        reason_codes.append(CALIBRATION_DRIFT_BLOCK_REASON)
    elif item.calibration_drift_score > config.max_pass_calibration_drift_score:
        reason_codes.append(CALIBRATION_DRIFT_WATCH_REASON)

    if (
        item.correction_follow_through_ratio
        < config.min_watch_correction_follow_through_ratio
    ):
        reason_codes.append(CORRECTION_FOLLOW_THROUGH_BLOCK_REASON)
    elif (
        item.correction_follow_through_ratio
        < config.min_pass_correction_follow_through_ratio
    ):
        reason_codes.append(CORRECTION_FOLLOW_THROUGH_WATCH_REASON)

    if item.evidence_reuse_quality_score < config.min_watch_evidence_reuse_quality_score:
        reason_codes.append(EVIDENCE_REUSE_QUALITY_BLOCK_REASON)
    elif item.evidence_reuse_quality_score < config.min_pass_evidence_reuse_quality_score:
        reason_codes.append(EVIDENCE_REUSE_QUALITY_WATCH_REASON)

    if item.peer_review_depth_score < config.min_watch_peer_review_depth_score:
        reason_codes.append(PEER_REVIEW_DEPTH_BLOCK_REASON)
    elif item.peer_review_depth_score < config.min_pass_peer_review_depth_score:
        reason_codes.append(PEER_REVIEW_DEPTH_WATCH_REASON)

    if item.review_latency_seconds > config.max_watch_review_latency_seconds:
        reason_codes.append(REVIEW_LATENCY_BLOCK_REASON)
    elif item.review_latency_seconds > config.max_pass_review_latency_seconds:
        reason_codes.append(REVIEW_LATENCY_WATCH_REASON)

    return _normalize_reason_codes(
        tuple(reason_codes) or (CLEAR_REASON,),
        ROW_REASON_CODES,
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(rows: tuple[ResearchTeamDomainMemoryDriftWatchRow, ...]) -> str:
    if not rows or any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainMemoryDriftWatchRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    report_reason_by_status = {
        STATUS_BLOCK: REPORT_BLOCK_REASON,
        STATUS_WATCH: REPORT_WATCH_REASON,
        STATUS_PASS: REPORT_PASS_REASON,
    }
    reasons = [report_reason_by_status[status]]
    for reason_code in ROW_REASON_CODES:
        if any(reason_code in row.reason_codes for row in rows):
            reasons.append(reason_code)
    return tuple(reasons)


def _reason_code_counts(
    rows: tuple[ResearchTeamDomainMemoryDriftWatchRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchTeamDomainMemoryDriftWatchReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamDomainMemoryDriftWatchReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                team_ratio=ONE,
            ),
        )
    counts: list[ResearchTeamDomainMemoryDriftWatchReasonCodeCount] = []
    denominator = _decimal_count(len(rows))
    for reason_code in REASON_CODE_COUNT_ORDER:
        if reason_code in (NO_INPUTS_REASON, REPORT_BLOCK_REASON, REPORT_WATCH_REASON):
            continue
        if reason_code == REPORT_PASS_REASON:
            continue
        count = _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))
        if count > ZERO:
            counts.append(
                ResearchTeamDomainMemoryDriftWatchReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                    team_ratio=_divide(count, denominator),
                ),
            )
    for reason_code in report_reason_codes:
        if reason_code in (REPORT_BLOCK_REASON, REPORT_WATCH_REASON, REPORT_PASS_REASON):
            counts.append(
                ResearchTeamDomainMemoryDriftWatchReasonCodeCount(
                    reason_code=reason_code,
                    count=ONE,
                    team_ratio=ONE,
                ),
            )
            break
    return tuple(counts)


def _validate_config(config: ResearchTeamDomainMemoryDriftWatchConfig) -> None:
    if config.max_pass_stale_memory_reuse_ratio > config.max_watch_stale_memory_reuse_ratio:
        raise ValueError("max_pass_stale_memory_reuse_ratio must not exceed watch threshold")
    if config.max_pass_calibration_drift_score > config.max_watch_calibration_drift_score:
        raise ValueError("max_pass_calibration_drift_score must not exceed watch threshold")
    if (
        config.min_pass_correction_follow_through_ratio
        < config.min_watch_correction_follow_through_ratio
    ):
        raise ValueError(
            "min_pass_correction_follow_through_ratio must not be below watch threshold",
        )
    if (
        config.min_pass_evidence_reuse_quality_score
        < config.min_watch_evidence_reuse_quality_score
    ):
        raise ValueError(
            "min_pass_evidence_reuse_quality_score must not be below watch threshold",
        )
    if config.min_pass_peer_review_depth_score < config.min_watch_peer_review_depth_score:
        raise ValueError("min_pass_peer_review_depth_score must not be below watch threshold")
    if config.max_pass_review_latency_seconds > config.max_watch_review_latency_seconds:
        raise ValueError("max_pass_review_latency_seconds must not exceed watch threshold")


def _validate_row_status(status: str, reason_codes: tuple[str, ...]) -> None:
    expected = _row_status(reason_codes)
    if status != expected:
        raise ValueError("status must match row reason codes")


def _validate_report(report: ResearchTeamDomainMemoryDriftWatchReport) -> None:
    expected_values = (
        ("domain_team_count", _decimal_count(len(report.rows))),
        ("pass_count", _status_count(report.rows, STATUS_PASS)),
        ("watch_count", _status_count(report.rows, STATUS_WATCH)),
        ("block_count", _status_count(report.rows, STATUS_BLOCK)),
        (
            "drift_team_count",
            _decimal_count(sum(1 for row in report.rows if row.status != STATUS_PASS)),
        ),
        (
            "stale_memory_reuse_team_count",
            _reason_count_any(
                report.rows,
                (STALE_MEMORY_REUSE_BLOCK_REASON, STALE_MEMORY_REUSE_WATCH_REASON),
            ),
        ),
        (
            "calibration_drift_team_count",
            _reason_count_any(
                report.rows,
                (CALIBRATION_DRIFT_BLOCK_REASON, CALIBRATION_DRIFT_WATCH_REASON),
            ),
        ),
        (
            "correction_gap_team_count",
            _reason_count_any(
                report.rows,
                (
                    CORRECTION_FOLLOW_THROUGH_BLOCK_REASON,
                    CORRECTION_FOLLOW_THROUGH_WATCH_REASON,
                ),
            ),
        ),
        (
            "evidence_reuse_gap_team_count",
            _reason_count_any(
                report.rows,
                (
                    EVIDENCE_REUSE_QUALITY_BLOCK_REASON,
                    EVIDENCE_REUSE_QUALITY_WATCH_REASON,
                ),
            ),
        ),
        (
            "peer_review_gap_team_count",
            _reason_count_any(
                report.rows,
                (PEER_REVIEW_DEPTH_BLOCK_REASON, PEER_REVIEW_DEPTH_WATCH_REASON),
            ),
        ),
        (
            "review_latency_gap_team_count",
            _reason_count_any(
                report.rows,
                (REVIEW_LATENCY_BLOCK_REASON, REVIEW_LATENCY_WATCH_REASON),
            ),
        ),
        (
            "average_stale_memory_reuse_ratio",
            _mean(tuple(row.stale_memory_reuse_ratio for row in report.rows)),
        ),
        (
            "average_calibration_drift_score",
            _mean(tuple(row.calibration_drift_score for row in report.rows)),
        ),
        (
            "average_correction_follow_through_ratio",
            _mean(tuple(row.correction_follow_through_ratio for row in report.rows)),
        ),
        (
            "average_evidence_reuse_quality_score",
            _mean(tuple(row.evidence_reuse_quality_score for row in report.rows)),
        ),
        (
            "average_peer_review_depth_score",
            _mean(tuple(row.peer_review_depth_score for row in report.rows)),
        ),
        (
            "max_review_latency_seconds",
            _max_decimal(tuple(row.review_latency_seconds for row in report.rows)),
        ),
    )
    for field_name, expected in expected_values:
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    expected_reason_codes = _report_reason_codes(report.rows, report.status)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.rows,
        expected_reason_codes,
    ):
        raise ValueError("reason_code_counts must match rows")


def _validate_report_runtime(report: ResearchTeamDomainMemoryDriftWatchReport) -> None:
    _require_hard_flags("report", report)
    if report.validation_digest != _report_validation_digest(report):
        raise ValueError("validation_digest must match report contents")
    for row in report.rows:
        if row.validation_digest != _row_validation_digest(row):
            raise ValueError("row validation_digest must match row contents")


def _canonical_report_payload(payload: dict[str, Any]) -> dict[str, Any]:
    report = _report_from_payload(payload)
    canonical = _json_ready_public_payload(asdict(report), allow_decimal=True)
    if canonical != payload:
        raise ValueError("report payload must be canonical")
    return canonical


def _report_from_payload(
    payload: dict[str, Any],
) -> ResearchTeamDomainMemoryDriftWatchReport:
    _require_payload_schema(
        "report",
        payload,
        ResearchTeamDomainMemoryDriftWatchReport,
    )
    values = dict(payload)
    values["generated_at"] = _datetime_from_payload(
        "generated_at",
        values["generated_at"],
    )
    for field_name in (
        "domain_team_count",
        "pass_count",
        "watch_count",
        "block_count",
        "drift_team_count",
        "stale_memory_reuse_team_count",
        "calibration_drift_team_count",
        "correction_gap_team_count",
        "evidence_reuse_gap_team_count",
        "peer_review_gap_team_count",
        "review_latency_gap_team_count",
        "average_stale_memory_reuse_ratio",
        "average_calibration_drift_score",
        "average_correction_follow_through_ratio",
        "average_evidence_reuse_quality_score",
        "average_peer_review_depth_score",
        "max_review_latency_seconds",
    ):
        values[field_name] = _decimal_from_payload(field_name, values[field_name])
    rows = values["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    values["rows"] = tuple(_row_from_payload(row) for row in rows)
    reason_code_counts = values["reason_code_counts"]
    if type(reason_code_counts) is not list:
        raise ValueError("reason_code_counts must be a list")
    values["reason_code_counts"] = tuple(
        _reason_code_count_from_payload(item) for item in reason_code_counts
    )
    values["reason_codes"] = _string_tuple_from_payload(
        "reason_codes",
        values["reason_codes"],
    )
    return ResearchTeamDomainMemoryDriftWatchReport(**values)


def _row_from_payload(
    payload: object,
) -> ResearchTeamDomainMemoryDriftWatchRow:
    if type(payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    _require_payload_schema("row", payload, ResearchTeamDomainMemoryDriftWatchRow)
    values = dict(payload)
    for field_name in (
        "observation_age_seconds",
        "stale_memory_reuse_ratio",
        "calibration_drift_score",
        "correction_follow_through_ratio",
        "evidence_reuse_quality_score",
        "peer_review_depth_score",
        "review_latency_seconds",
    ):
        values[field_name] = _decimal_from_payload(field_name, values[field_name])
    values["reason_codes"] = _string_tuple_from_payload(
        "reason_codes",
        values["reason_codes"],
    )
    return ResearchTeamDomainMemoryDriftWatchRow(**values)


def _reason_code_count_from_payload(
    payload: object,
) -> ResearchTeamDomainMemoryDriftWatchReasonCodeCount:
    if type(payload) is not dict:
        raise ValueError("reason code count payload must be a JSON object")
    _require_payload_schema(
        "reason code count",
        payload,
        ResearchTeamDomainMemoryDriftWatchReasonCodeCount,
    )
    values = dict(payload)
    for field_name in ("count", "team_ratio"):
        values[field_name] = _decimal_from_payload(field_name, values[field_name])
    return ResearchTeamDomainMemoryDriftWatchReasonCodeCount(**values)


def _require_payload_schema(
    label: str,
    payload: dict[str, Any],
    dataclass_type: type[object],
) -> None:
    expected_fields = {field.name for field in fields(dataclass_type)}
    if set(payload) != expected_fields:
        raise ValueError(f"{label} payload fields must match schema")


def _decimal_from_payload(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a Decimal string")
    try:
        return Decimal(value)
    except ArithmeticError as exc:
        raise ValueError(f"{name} must be a Decimal string") from exc


def _datetime_from_payload(name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{name} must be an ISO datetime string")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO datetime string") from exc


def _string_tuple_from_payload(name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list or any(type(item) is not str for item in value):
        raise ValueError(f"{name} must be a list of strings")
    return tuple(value)


def _validate_report_payload(payload: dict[str, Any]) -> None:
    if payload.get("paper_only") is not True:
        raise ValueError("paper_only must be True")
    if payload.get("report_only") is not True:
        raise ValueError("report_only must be True")
    if payload.get("readonly") is not True:
        raise ValueError("readonly must be True")
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("row payload must be a JSON object")
        expected = _validation_digest_for_payload(row)
        if row.get("validation_digest") != expected:
            raise ValueError("row validation_digest must match row contents")
    expected_report_digest = _validation_digest_for_payload(payload)
    if payload.get("validation_digest") != expected_report_digest:
        raise ValueError("validation_digest must match report contents")


def _validate_payload_statuses(payload: dict[str, Any]) -> None:
    status = payload.get("status")
    if status not in PUBLIC_STATUSES:
        raise ValueError("status must be pass, watch, or block")
    rows = payload.get("rows")
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict) and row.get("status") not in PUBLIC_STATUSES:
                raise ValueError("status must be pass, watch, or block")


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchTeamDomainMemoryDriftWatchObservation, ...]:
    items = tuple(observations)
    for item in items:
        if type(item) is not ResearchTeamDomainMemoryDriftWatchObservation:
            raise ValueError(
                "observations must be ResearchTeamDomainMemoryDriftWatchObservation",
            )
        _require_hard_flags("observation", item)
    return items


def _normalize_rows(
    rows: tuple[ResearchTeamDomainMemoryDriftWatchRow, ...],
) -> tuple[ResearchTeamDomainMemoryDriftWatchRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchTeamDomainMemoryDriftWatchRow:
            raise ValueError("rows must contain ResearchTeamDomainMemoryDriftWatchRow")
    return tuple(sorted(rows, key=_row_sort_key))


def _normalize_reason_code_counts(
    counts: tuple[ResearchTeamDomainMemoryDriftWatchReasonCodeCount, ...],
) -> tuple[ResearchTeamDomainMemoryDriftWatchReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchTeamDomainMemoryDriftWatchReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamDomainMemoryDriftWatchReasonCodeCount",
            )
    return tuple(sorted(counts, key=lambda item: _reason_code_count_sort_key(item)))


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        normalized.append(_require_reason_code(reason_code, allowed))
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return tuple(reason_code for reason_code in allowed if reason_code in normalized)


def _row_sort_key(row: ResearchTeamDomainMemoryDriftWatchRow) -> tuple[Decimal, str, str]:
    return (STATUS_SORT_ORDER[row.status], row.domain_category, row.team_digest)


def _reason_code_count_sort_key(
    item: ResearchTeamDomainMemoryDriftWatchReasonCodeCount,
) -> tuple[Decimal, str]:
    if item.reason_code in REASON_CODE_COUNT_ORDER:
        return (_decimal_count(REASON_CODE_COUNT_ORDER.index(item.reason_code)), item.reason_code)
    return (_decimal_count(len(REASON_CODE_COUNT_ORDER)), item.reason_code)


def _status_count(
    rows: tuple[ResearchTeamDomainMemoryDriftWatchRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _reason_count_any(
    rows: tuple[ResearchTeamDomainMemoryDriftWatchRow, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    return _decimal_count(
        sum(1 for row in rows if any(code in row.reason_codes for code in reason_codes)),
    )


def _team_digest(item: ResearchTeamDomainMemoryDriftWatchObservation) -> str:
    value = {
        "domain_category": item.domain_category,
        "team_key": item.team_key,
    }
    return "sha256:" + _hash_json(value)


def _row_validation_digest(row: ResearchTeamDomainMemoryDriftWatchRow) -> str:
    return _validation_digest_for_payload(_json_ready_public_payload(asdict(row), True))


def _report_validation_digest(report: ResearchTeamDomainMemoryDriftWatchReport) -> str:
    return _validation_digest_for_payload(_json_ready_public_payload(asdict(report), True))


def _validation_digest_for_payload(value: Any) -> str:
    return "sha256:" + _hash_json(_strip_validation_digest(value))


def _hash_json(value: Any) -> str:
    encoded = json.dumps(
        value,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _strip_validation_digest(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_validation_digest(item)
            for key, item in value.items()
            if key != "validation_digest"
        }
    if isinstance(value, list):
        return [_strip_validation_digest(item) for item in value]
    return value


def _json_ready_public_payload(value: Any, allow_decimal: bool) -> Any:
    if value is None:
        return None
    if type(value) is bool:
        return value
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready_public_payload(asdict(value), allow_decimal)
    if type(value) is Decimal:
        if not allow_decimal:
            raise ValueError("payload Decimal values must already be serialized")
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(_quantize_decimal(value))
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if type(value) is str:
        return value
    if type(value) in (int, float):
        raise ValueError("public numeric values must be Decimal-derived strings")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready_public_payload(item, allow_decimal)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready_public_payload(item, allow_decimal) for item in value]
    raise ValueError("value is not JSON serializable")


def _require_supported_config_version(value: str) -> str:
    normalized = _require_public_string("config_version", value)
    if normalized != DEFAULT_RESEARCH_TEAM_DOMAIN_MEMORY_DRIFT_WATCH_REPORT_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    return normalized


def _require_public_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must not be empty")
    return value


def _require_public_category(name: str, value: object) -> str:
    if type(value) is not str or value not in PUBLIC_DOMAIN_CATEGORIES:
        raise ValueError(f"{name} must be a public category")
    return value


def _require_reason_code(value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError("reason_code must be recognized")
    return value


def _require_status(name: str, value: object) -> str:
    if type(value) is not str or value not in PUBLIC_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")
    return value


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(name, value)
    if decimal_value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal_value


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize_decimal(value)


def _decimal_count(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _divide(sum(values, ZERO), _decimal_count(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize_decimal(max(values))


def _divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _age_seconds(observed_at: datetime, generated_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    if delta.days < 0:
        raise ValueError("observed_at must not be after generated_at")
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + _quantize_decimal(Decimal(delta.seconds))
        + _divide(Decimal(delta.microseconds), MICROSECONDS_PER_SECOND)
    )
    return _quantize_decimal(seconds)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_validation_digest(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a validation digest")
    if not value.startswith(f"{VALIDATION_DIGEST_ALGORITHM}:"):
        raise ValueError(f"{name} must be a sha256 validation digest")
    digest = value.split(":", 1)[1]
    if len(digest) != 64 or any(character not in HEX_DIGITS for character in digest):
        raise ValueError(f"{name} must be a sha256 validation digest")
    return value


def _normalize_validation_digest(name: str, value: str, expected: str) -> str:
    if value == "":
        return expected
    normalized = _require_validation_digest(name, value)
    if normalized != expected:
        raise ValueError(f"{name} must match report contents")
    return normalized


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str and _has_unsafe_public_fragment(value):
        raise ValueError(f"unsafe public payload in {label}")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)
