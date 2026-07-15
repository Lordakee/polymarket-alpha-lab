"""Pure report for research-team domain review learning gaps."""

from __future__ import annotations

import json
import weakref
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, DecimalException, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_TEAM_DOMAIN_REVIEW_LEARNING_GAP_REPORT_CONFIG_VERSION = (
    "research-team-domain-review-learning-gap-report-v1"
)

_COUNT_QUANTUM = Decimal("1")
_COUNT_ZERO = Decimal("0")
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SIX = Decimal("6.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_STATUSES = ("block", "watch", "pass")
_STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_HEX_CHARS = frozenset("0123456789abcdef")
_MAX_PUBLIC_PAYLOAD_DEPTH = 8
_PUBLIC_SNAPSHOTS: dict[int, tuple[tuple[str, Any], ...]] = {}
_PUBLIC_SNAPSHOT_REFS: dict[int, weakref.ReferenceType[object]] = {}
_BLOCK_REASONS = frozenset(
    (
        "unresolved_corrections_block",
        "stale_memory_reuse_block",
        "calibration_drift_block",
        "evidence_coverage_block",
        "peer_review_depth_block",
        "review_latency_block",
    ),
)
_PASS_REASONS = frozenset(("domain_review_learning_gap_pass",))
_REASON_PRIORITY = (
    "unresolved_corrections_block",
    "unresolved_corrections_watch",
    "stale_memory_reuse_block",
    "stale_memory_reuse_watch",
    "calibration_drift_block",
    "calibration_drift_watch",
    "evidence_coverage_block",
    "evidence_coverage_watch",
    "peer_review_depth_block",
    "peer_review_depth_watch",
    "review_latency_block",
    "review_latency_watch",
    "domain_review_learning_gap_pass",
    "research_team_domain_review_learning_gap_report_empty",
)
_RESULT_REASONS = frozenset(_REASON_PRIORITY[:-1])
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "url",
    "://",
    "dsn",
    "table",
    "tok" "en",
    "wal" "let",
    "or" "der",
    "tra" "de",
    "li" "ve",
    "raw",
)
_CONFIG_THRESHOLD_FIELDS = (
    "unresolved_corrections_watch_threshold",
    "unresolved_corrections_block_threshold",
    "stale_memory_reuse_watch_threshold",
    "stale_memory_reuse_block_threshold",
    "calibration_drift_watch_threshold",
    "calibration_drift_block_threshold",
    "evidence_coverage_pass_threshold",
    "evidence_coverage_block_threshold",
    "peer_review_depth_pass_threshold",
    "peer_review_depth_block_threshold",
    "review_latency_watch_hours",
    "review_latency_block_hours",
)
_RESULT_PUBLIC_FIELDS = (
    "review_fingerprint",
    "domain_fingerprint",
    "unresolved_corrections",
    "stale_memory_reuse_count",
    "calibration_drift",
    "evidence_coverage_ratio",
    "peer_review_depth",
    "review_latency_hours",
    "unresolved_corrections_score",
    "stale_memory_reuse_score",
    "calibration_drift_score",
    "evidence_gap_score",
    "peer_review_gap_score",
    "review_latency_score",
    "learning_gap_score",
    "review_status",
    "reason_codes",
    "validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_REASON_COUNT_PUBLIC_FIELDS = (
    "reason_code",
    "count",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_PUBLIC_FIELDS = (
    "generated_at",
    "config_version",
    *_CONFIG_THRESHOLD_FIELDS,
    "review_count",
    "pass_count",
    "watch_count",
    "block_count",
    "max_learning_gap_score",
    "report_status",
    "reason_codes",
    "reason_code_counts",
    "results",
    "validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamDomainReviewLearningGapConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_REVIEW_LEARNING_GAP_REPORT_CONFIG_VERSION
    )
    unresolved_corrections_watch_threshold: Decimal = Decimal("1")
    unresolved_corrections_block_threshold: Decimal = Decimal("3")
    stale_memory_reuse_watch_threshold: Decimal = Decimal("1")
    stale_memory_reuse_block_threshold: Decimal = Decimal("2")
    calibration_drift_watch_threshold: Decimal = Decimal("0.150000")
    calibration_drift_block_threshold: Decimal = Decimal("0.300000")
    evidence_coverage_pass_threshold: Decimal = Decimal("0.850000")
    evidence_coverage_block_threshold: Decimal = Decimal("0.500000")
    peer_review_depth_pass_threshold: Decimal = Decimal("2")
    peer_review_depth_block_threshold: Decimal = Decimal("1")
    review_latency_watch_hours: Decimal = Decimal("48.000000")
    review_latency_block_hours: Decimal = Decimal("96.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainReviewLearningGapConfig,
            "config",
        )
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_REVIEW_LEARNING_GAP_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "unresolved_corrections_watch_threshold",
            "unresolved_corrections_block_threshold",
            "stale_memory_reuse_watch_threshold",
            "stale_memory_reuse_block_threshold",
            "peer_review_depth_pass_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "peer_review_depth_block_threshold",
            _normalize_nonnegative_count(
                "peer_review_depth_block_threshold",
                self.peer_review_depth_block_threshold,
            ),
        )
        for field_name in (
            "calibration_drift_watch_threshold",
            "calibration_drift_block_threshold",
            "evidence_coverage_pass_threshold",
            "evidence_coverage_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "review_latency_watch_hours",
            "review_latency_block_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_watch_not_above_block(
            self.unresolved_corrections_watch_threshold,
            self.unresolved_corrections_block_threshold,
        )
        _require_watch_not_above_block(
            self.stale_memory_reuse_watch_threshold,
            self.stale_memory_reuse_block_threshold,
        )
        _require_watch_not_above_block(
            self.calibration_drift_watch_threshold,
            self.calibration_drift_block_threshold,
        )
        _require_watch_not_above_block(
            self.review_latency_watch_hours,
            self.review_latency_block_hours,
        )
        if self.evidence_coverage_block_threshold > self.evidence_coverage_pass_threshold:
            raise ValueError("block threshold must not exceed pass threshold")
        if self.peer_review_depth_block_threshold > self.peer_review_depth_pass_threshold:
            raise ValueError("block threshold must not exceed pass threshold")
        require_paper_only_flags("domain review learning gap config", self)
        _store_public_snapshot(self)


@dataclass(frozen=True)
class ResearchTeamDomainReviewLearningGapInput(_FinalDataclass):
    review_key: str
    domain_key: str
    unresolved_corrections: Decimal
    stale_memory_reuse_count: Decimal
    calibration_drift: Decimal
    evidence_coverage_ratio: Decimal
    peer_review_depth: Decimal
    review_latency_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainReviewLearningGapInput,
            "input",
        )
        _require_private_key("review_key", self.review_key)
        _require_private_key("domain_key", self.domain_key)
        for field_name in (
            "unresolved_corrections",
            "stale_memory_reuse_count",
            "peer_review_depth",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "calibration_drift",
            _normalize_unit_decimal("calibration_drift", self.calibration_drift),
        )
        object.__setattr__(
            self,
            "evidence_coverage_ratio",
            _normalize_unit_decimal(
                "evidence_coverage_ratio",
                self.evidence_coverage_ratio,
            ),
        )
        object.__setattr__(
            self,
            "review_latency_hours",
            _normalize_nonnegative_decimal(
                "review_latency_hours",
                self.review_latency_hours,
            ),
        )
        require_paper_only_flags("domain review learning gap input", self)
        _store_public_snapshot(self)


@dataclass(frozen=True)
class ResearchTeamDomainReviewLearningGapResult(_FinalDataclass):
    review_fingerprint: str
    domain_fingerprint: str
    unresolved_corrections: Decimal
    stale_memory_reuse_count: Decimal
    calibration_drift: Decimal
    evidence_coverage_ratio: Decimal
    peer_review_depth: Decimal
    review_latency_hours: Decimal
    unresolved_corrections_score: Decimal
    stale_memory_reuse_score: Decimal
    calibration_drift_score: Decimal
    evidence_gap_score: Decimal
    peer_review_gap_score: Decimal
    review_latency_score: Decimal
    learning_gap_score: Decimal
    review_status: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainReviewLearningGapResult,
            "result",
        )
        _require_digest("review_fingerprint", self.review_fingerprint)
        _require_digest("domain_fingerprint", self.domain_fingerprint)
        for field_name in (
            "unresolved_corrections",
            "stale_memory_reuse_count",
            "peer_review_depth",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("review_latency_hours",):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_drift",
            "evidence_coverage_ratio",
            "unresolved_corrections_score",
            "stale_memory_reuse_score",
            "calibration_drift_score",
            "evidence_gap_score",
            "peer_review_gap_score",
            "review_latency_score",
            "learning_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("review_status", self.review_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_result_reason_codes("reason_codes", self.reason_codes),
        )
        _require_digest("validation_digest", self.validation_digest)
        _validate_result(self)
        require_paper_only_flags("domain review learning gap result", self)
        _store_public_snapshot(self)


@dataclass(frozen=True)
class ResearchTeamDomainReviewLearningGapReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainReviewLearningGapReasonCodeCount,
            "reason count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _normalize_reason_count_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        require_paper_only_flags("domain review learning gap reason count", self)
        _store_public_snapshot(self)


@dataclass(frozen=True)
class ResearchTeamDomainReviewLearningGapReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    unresolved_corrections_watch_threshold: Decimal
    unresolved_corrections_block_threshold: Decimal
    stale_memory_reuse_watch_threshold: Decimal
    stale_memory_reuse_block_threshold: Decimal
    calibration_drift_watch_threshold: Decimal
    calibration_drift_block_threshold: Decimal
    evidence_coverage_pass_threshold: Decimal
    evidence_coverage_block_threshold: Decimal
    peer_review_depth_pass_threshold: Decimal
    peer_review_depth_block_threshold: Decimal
    review_latency_watch_hours: Decimal
    review_latency_block_hours: Decimal
    review_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_learning_gap_score: Decimal | None
    report_status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamDomainReviewLearningGapReasonCodeCount, ...]
    results: tuple[ResearchTeamDomainReviewLearningGapResult, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainReviewLearningGapReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        config = _config_from_report(self)
        for field_name in _CONFIG_THRESHOLD_FIELDS:
            object.__setattr__(self, field_name, getattr(config, field_name))
        for field_name in (
            "review_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.max_learning_gap_score is not None:
            object.__setattr__(
                self,
                "max_learning_gap_score",
                _normalize_unit_decimal(
                    "max_learning_gap_score",
                    self.max_learning_gap_score,
                ),
            )
        _require_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "results", _normalize_results(self.results))
        _require_digest("validation_digest", self.validation_digest)
        _validate_report(self)
        _require_untampered_report_members(self)
        require_paper_only_flags("domain review learning gap report", self)
        _store_public_snapshot(self)


def build_research_team_domain_review_learning_gap_report(
    reviews: Iterable[ResearchTeamDomainReviewLearningGapInput],
    *,
    config: ResearchTeamDomainReviewLearningGapConfig,
    generated_at: datetime,
) -> ResearchTeamDomainReviewLearningGapReport:
    if type(config) is not ResearchTeamDomainReviewLearningGapConfig:
        raise ValueError("config must be a ResearchTeamDomainReviewLearningGapConfig")
    _require_untampered_public_dataclass(config, "config")
    require_paper_only_flags("domain review learning gap config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_reviews = _normalize_reviews(reviews)
    results = tuple(
        sorted(
            (
                _result_from_review(review, config=config)
                for review in normalized_reviews
            ),
            key=_result_sort_key,
        ),
    )
    review_count = _count(len(results))
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        **{
            field_name: getattr(config, field_name)
            for field_name in _CONFIG_THRESHOLD_FIELDS
        },
        "review_count": review_count,
        "pass_count": _result_status_count(results, "pass"),
        "watch_count": _result_status_count(results, "watch"),
        "block_count": _result_status_count(results, "block"),
        "max_learning_gap_score": (
            None if not results else max(result.learning_gap_score for result in results)
        ),
        "report_status": _report_status(results),
        "reason_codes": _report_reason_codes(results),
        "reason_code_counts": _reason_code_counts(results),
        "results": results,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamDomainReviewLearningGapReport(
        **report_values,
        validation_digest=_validation_digest(report_values),
    )


def research_team_domain_review_learning_gap_report_payload(
    report: ResearchTeamDomainReviewLearningGapReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamDomainReviewLearningGapReport:
        _require_untampered_report(report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = report
    else:
        raise ValueError("report must be a ResearchTeamDomainReviewLearningGapReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    _reject_unsafe_payload(payload)
    rebuilt = _report_from_public_payload(payload)
    canonical = _json_ready(rebuilt)
    if type(canonical) is not dict:
        raise ValueError("report payload must be an object")
    if canonical != payload:
        raise ValueError("report payload must match exact canonical schema")
    _reject_unsafe_payload(canonical)
    return canonical


def _normalize_reviews(
    reviews: Iterable[ResearchTeamDomainReviewLearningGapInput],
) -> tuple[ResearchTeamDomainReviewLearningGapInput, ...]:
    if isinstance(reviews, (str, bytes)):
        raise ValueError("reviews must be an iterable")
    try:
        items = tuple(reviews)
    except TypeError as exc:
        raise ValueError("reviews must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchTeamDomainReviewLearningGapInput:
            raise ValueError(
                "reviews must contain ResearchTeamDomainReviewLearningGapInput",
            )
        _require_untampered_public_dataclass(item, "input")
        require_paper_only_flags("domain review learning gap input", item)
        if item.review_key in seen:
            raise ValueError("review_key values must be unique")
        seen.add(item.review_key)
    return items


def _result_from_review(
    review: ResearchTeamDomainReviewLearningGapInput,
    *,
    config: ResearchTeamDomainReviewLearningGapConfig,
) -> ResearchTeamDomainReviewLearningGapResult:
    scores = _component_scores(review, config)
    reason_codes = _result_reason_codes(review, config)
    result_values = {
        "review_fingerprint": _fingerprint(review.review_key),
        "domain_fingerprint": _fingerprint(review.domain_key),
        "unresolved_corrections": review.unresolved_corrections,
        "stale_memory_reuse_count": review.stale_memory_reuse_count,
        "calibration_drift": review.calibration_drift,
        "evidence_coverage_ratio": review.evidence_coverage_ratio,
        "peer_review_depth": review.peer_review_depth,
        "review_latency_hours": review.review_latency_hours,
        **scores,
        "learning_gap_score": _learning_gap_score(
            tuple(scores[field_name] for field_name in _COMPONENT_SCORE_FIELDS),
        ),
        "review_status": _status_from_reason_codes(reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamDomainReviewLearningGapResult(
        **result_values,
        validation_digest=_validation_digest(result_values),
    )


_COMPONENT_SCORE_FIELDS = (
    "unresolved_corrections_score",
    "stale_memory_reuse_score",
    "calibration_drift_score",
    "evidence_gap_score",
    "peer_review_gap_score",
    "review_latency_score",
)


def _component_scores(
    review: (
        ResearchTeamDomainReviewLearningGapInput
        | ResearchTeamDomainReviewLearningGapResult
    ),
    config: ResearchTeamDomainReviewLearningGapConfig,
) -> dict[str, Decimal]:
    return {
        "unresolved_corrections_score": _capped_ratio(
            review.unresolved_corrections,
            config.unresolved_corrections_block_threshold,
        ),
        "stale_memory_reuse_score": _capped_ratio(
            review.stale_memory_reuse_count,
            config.stale_memory_reuse_block_threshold,
        ),
        "calibration_drift_score": _capped_ratio(
            review.calibration_drift,
            config.calibration_drift_block_threshold,
        ),
        "evidence_gap_score": _difference(
            _ONE,
            review.evidence_coverage_ratio,
        ),
        "peer_review_gap_score": _peer_review_gap_score(
            review.peer_review_depth,
            config,
        ),
        "review_latency_score": _capped_ratio(
            review.review_latency_hours,
            config.review_latency_block_hours,
        ),
    }


def _result_reason_codes(
    review: (
        ResearchTeamDomainReviewLearningGapInput
        | ResearchTeamDomainReviewLearningGapResult
    ),
    config: ResearchTeamDomainReviewLearningGapConfig,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    if review.unresolved_corrections >= config.unresolved_corrections_block_threshold:
        block_reasons.append("unresolved_corrections_block")
    elif review.unresolved_corrections >= config.unresolved_corrections_watch_threshold:
        watch_reasons.append("unresolved_corrections_watch")
    if review.stale_memory_reuse_count >= config.stale_memory_reuse_block_threshold:
        block_reasons.append("stale_memory_reuse_block")
    elif review.stale_memory_reuse_count >= config.stale_memory_reuse_watch_threshold:
        watch_reasons.append("stale_memory_reuse_watch")
    if review.calibration_drift >= config.calibration_drift_block_threshold:
        block_reasons.append("calibration_drift_block")
    elif review.calibration_drift >= config.calibration_drift_watch_threshold:
        watch_reasons.append("calibration_drift_watch")
    if review.evidence_coverage_ratio <= config.evidence_coverage_block_threshold:
        block_reasons.append("evidence_coverage_block")
    elif review.evidence_coverage_ratio < config.evidence_coverage_pass_threshold:
        watch_reasons.append("evidence_coverage_watch")
    if review.peer_review_depth < config.peer_review_depth_block_threshold:
        block_reasons.append("peer_review_depth_block")
    elif review.peer_review_depth < config.peer_review_depth_pass_threshold:
        watch_reasons.append("peer_review_depth_watch")
    if review.review_latency_hours >= config.review_latency_block_hours:
        block_reasons.append("review_latency_block")
    elif review.review_latency_hours >= config.review_latency_watch_hours:
        watch_reasons.append("review_latency_watch")
    reasons = tuple(block_reasons + watch_reasons)
    if not reasons:
        reasons = ("domain_review_learning_gap_pass",)
    return _normalize_result_reason_codes("reason_codes", reasons)


def _peer_review_gap_score(
    peer_review_depth: Decimal,
    config: ResearchTeamDomainReviewLearningGapConfig,
) -> Decimal:
    if peer_review_depth >= config.peer_review_depth_pass_threshold:
        return _ZERO
    return _capped_ratio(
        _difference(config.peer_review_depth_pass_threshold, peer_review_depth),
        config.peer_review_depth_pass_threshold,
    )


def _learning_gap_score(component_values: tuple[Decimal, ...]) -> Decimal:
    return _ratio(_sum_decimal(component_values), _SIX)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason in _BLOCK_REASONS for reason in reason_codes):
        return "block"
    if reason_codes == ("domain_review_learning_gap_pass",):
        return "pass"
    return "watch"


def _report_status(
    results: tuple[ResearchTeamDomainReviewLearningGapResult, ...],
) -> str:
    if not results:
        return "block"
    if any(result.review_status == "block" for result in results):
        return "block"
    if any(result.review_status == "watch" for result in results):
        return "watch"
    return "pass"


def _report_reason_codes(
    results: tuple[ResearchTeamDomainReviewLearningGapResult, ...],
) -> tuple[str, ...]:
    if not results:
        return ("research_team_domain_review_learning_gap_report_empty",)
    return _normalize_report_reason_codes(
        "reason_codes",
        tuple(reason for result in results for reason in result.reason_codes),
    )


def _result_status_count(
    results: tuple[ResearchTeamDomainReviewLearningGapResult, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for result in results if result.review_status == status))


def _normalize_results(
    results: object,
) -> tuple[ResearchTeamDomainReviewLearningGapResult, ...]:
    if isinstance(results, (str, bytes)):
        raise ValueError("results must be an iterable")
    try:
        normalized = tuple(results)
    except TypeError as exc:
        raise ValueError("results must be an iterable") from exc
    seen_review_fingerprints: set[str] = set()
    for result in normalized:
        if type(result) is not ResearchTeamDomainReviewLearningGapResult:
            raise ValueError(
                "results must contain ResearchTeamDomainReviewLearningGapResult",
            )
        require_paper_only_flags("domain review learning gap result", result)
        if result.review_fingerprint in seen_review_fingerprints:
            raise ValueError("review_fingerprint values must be unique")
        seen_review_fingerprints.add(result.review_fingerprint)
    if normalized != tuple(sorted(normalized, key=_result_sort_key)):
        raise ValueError("results must be sorted deterministically")
    return normalized


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[ResearchTeamDomainReviewLearningGapReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_reason_codes: set[str] = set()
    for count in normalized:
        if type(count) is not ResearchTeamDomainReviewLearningGapReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamDomainReviewLearningGapReasonCodeCount",
            )
        require_paper_only_flags("domain review learning gap reason count", count)
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen_reason_codes.add(count.reason_code)
    if normalized != tuple(sorted(normalized, key=_reason_count_sort_key)):
        raise ValueError("reason_code_counts must be sorted deterministically")
    return normalized


def _reason_code_counts(
    results: tuple[ResearchTeamDomainReviewLearningGapResult, ...],
) -> tuple[ResearchTeamDomainReviewLearningGapReasonCodeCount, ...]:
    reason_codes = (
        ("research_team_domain_review_learning_gap_report_empty",)
        if not results
        else tuple(reason for result in results for reason in result.reason_codes)
    )
    unique_reason_codes = tuple(sorted(set(reason_codes), key=_reason_sort_key))
    return tuple(
        ResearchTeamDomainReviewLearningGapReasonCodeCount(
            reason_code=reason_code,
            count=_count(
                sum(1 for candidate in reason_codes if candidate == reason_code),
            ),
        )
        for reason_code in unique_reason_codes
    )


def _validate_result(result: ResearchTeamDomainReviewLearningGapResult) -> None:
    expected_score = _learning_gap_score(
        (
            result.unresolved_corrections_score,
            result.stale_memory_reuse_score,
            result.calibration_drift_score,
            result.evidence_gap_score,
            result.peer_review_gap_score,
            result.review_latency_score,
        ),
    )
    if result.learning_gap_score != expected_score:
        raise ValueError("learning_gap_score must match component scores")
    if result.review_status != _status_from_reason_codes(result.reason_codes):
        raise ValueError("review_status must match reason_codes")
    if result.validation_digest != _validation_digest(_result_digest_values(result)):
        raise ValueError("validation_digest must match result payload")


def _validate_report(report: ResearchTeamDomainReviewLearningGapReport) -> None:
    config = _config_from_report(report)
    for result in report.results:
        _validate_result(result)
        _validate_result_against_config(result, config)
    if report.review_count != _count(len(report.results)):
        raise ValueError("review_count must match results")
    if report.pass_count != _result_status_count(report.results, "pass"):
        raise ValueError("pass_count must match results")
    if report.watch_count != _result_status_count(report.results, "watch"):
        raise ValueError("watch_count must match results")
    if report.block_count != _result_status_count(report.results, "block"):
        raise ValueError("block_count must match results")
    expected_max = (
        None
        if not report.results
        else max(result.learning_gap_score for result in report.results)
    )
    if report.max_learning_gap_score != expected_max:
        raise ValueError("max_learning_gap_score must match results")
    if report.report_status != _report_status(report.results):
        raise ValueError("report_status must match results")
    if report.reason_codes != _report_reason_codes(report.results):
        raise ValueError("reason_codes must match results")
    if report.reason_code_counts != _reason_code_counts(report.results):
        raise ValueError("reason_code_counts must match results")
    if report.validation_digest != _validation_digest(_report_digest_values(report)):
        raise ValueError("validation_digest must match report payload")


def _validate_result_against_config(
    result: ResearchTeamDomainReviewLearningGapResult,
    config: ResearchTeamDomainReviewLearningGapConfig,
) -> None:
    expected_scores = _component_scores(result, config)
    for field_name in _COMPONENT_SCORE_FIELDS:
        if getattr(result, field_name) != expected_scores[field_name]:
            raise ValueError(f"{field_name} must match raw values and config")
    expected_reasons = _result_reason_codes(result, config)
    if result.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match raw values and config")
    if result.review_status != _status_from_reason_codes(expected_reasons):
        raise ValueError("review_status must match raw values and config")


def _config_from_report(
    report: ResearchTeamDomainReviewLearningGapReport,
) -> ResearchTeamDomainReviewLearningGapConfig:
    return ResearchTeamDomainReviewLearningGapConfig(
        config_version=report.config_version,
        unresolved_corrections_watch_threshold=(
            report.unresolved_corrections_watch_threshold
        ),
        unresolved_corrections_block_threshold=(
            report.unresolved_corrections_block_threshold
        ),
        stale_memory_reuse_watch_threshold=report.stale_memory_reuse_watch_threshold,
        stale_memory_reuse_block_threshold=report.stale_memory_reuse_block_threshold,
        calibration_drift_watch_threshold=report.calibration_drift_watch_threshold,
        calibration_drift_block_threshold=report.calibration_drift_block_threshold,
        evidence_coverage_pass_threshold=report.evidence_coverage_pass_threshold,
        evidence_coverage_block_threshold=report.evidence_coverage_block_threshold,
        peer_review_depth_pass_threshold=report.peer_review_depth_pass_threshold,
        peer_review_depth_block_threshold=report.peer_review_depth_block_threshold,
        review_latency_watch_hours=report.review_latency_watch_hours,
        review_latency_block_hours=report.review_latency_block_hours,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _result_digest_values(
    result: ResearchTeamDomainReviewLearningGapResult,
) -> dict[str, Any]:
    return {
        "review_fingerprint": result.review_fingerprint,
        "domain_fingerprint": result.domain_fingerprint,
        "unresolved_corrections": result.unresolved_corrections,
        "stale_memory_reuse_count": result.stale_memory_reuse_count,
        "calibration_drift": result.calibration_drift,
        "evidence_coverage_ratio": result.evidence_coverage_ratio,
        "peer_review_depth": result.peer_review_depth,
        "review_latency_hours": result.review_latency_hours,
        "unresolved_corrections_score": result.unresolved_corrections_score,
        "stale_memory_reuse_score": result.stale_memory_reuse_score,
        "calibration_drift_score": result.calibration_drift_score,
        "evidence_gap_score": result.evidence_gap_score,
        "peer_review_gap_score": result.peer_review_gap_score,
        "review_latency_score": result.review_latency_score,
        "learning_gap_score": result.learning_gap_score,
        "review_status": result.review_status,
        "reason_codes": result.reason_codes,
        "paper_only": result.paper_only,
        "report_only": result.report_only,
        "readonly": result.readonly,
    }


def _report_digest_values(
    report: ResearchTeamDomainReviewLearningGapReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        **{
            field_name: getattr(report, field_name)
            for field_name in _CONFIG_THRESHOLD_FIELDS
        },
        "review_count": report.review_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "max_learning_gap_score": report.max_learning_gap_score,
        "report_status": report.report_status,
        "reason_codes": report.reason_codes,
        "reason_code_counts": report.reason_code_counts,
        "results": report.results,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchTeamDomainReviewLearningGapReport:
    _require_exact_schema("report payload", payload, _REPORT_PUBLIC_FIELDS)
    results_value = payload["results"]
    if type(results_value) is not list:
        raise ValueError("results must match exact canonical schema")
    reason_counts_value = payload["reason_code_counts"]
    if type(reason_counts_value) is not list:
        raise ValueError("reason_code_counts must match exact canonical schema")
    results = tuple(_result_from_public_payload(item) for item in results_value)
    reason_code_counts = tuple(
        _reason_code_count_from_public_payload(item)
        for item in reason_counts_value
    )
    return ResearchTeamDomainReviewLearningGapReport(
        generated_at=_public_datetime("generated_at", payload["generated_at"]),
        config_version=_public_text("config_version", payload["config_version"]),
        unresolved_corrections_watch_threshold=_public_positive_count(
            "unresolved_corrections_watch_threshold",
            payload["unresolved_corrections_watch_threshold"],
        ),
        unresolved_corrections_block_threshold=_public_positive_count(
            "unresolved_corrections_block_threshold",
            payload["unresolved_corrections_block_threshold"],
        ),
        stale_memory_reuse_watch_threshold=_public_positive_count(
            "stale_memory_reuse_watch_threshold",
            payload["stale_memory_reuse_watch_threshold"],
        ),
        stale_memory_reuse_block_threshold=_public_positive_count(
            "stale_memory_reuse_block_threshold",
            payload["stale_memory_reuse_block_threshold"],
        ),
        calibration_drift_watch_threshold=_public_unit_decimal(
            "calibration_drift_watch_threshold",
            payload["calibration_drift_watch_threshold"],
        ),
        calibration_drift_block_threshold=_public_unit_decimal(
            "calibration_drift_block_threshold",
            payload["calibration_drift_block_threshold"],
        ),
        evidence_coverage_pass_threshold=_public_unit_decimal(
            "evidence_coverage_pass_threshold",
            payload["evidence_coverage_pass_threshold"],
        ),
        evidence_coverage_block_threshold=_public_unit_decimal(
            "evidence_coverage_block_threshold",
            payload["evidence_coverage_block_threshold"],
        ),
        peer_review_depth_pass_threshold=_public_positive_count(
            "peer_review_depth_pass_threshold",
            payload["peer_review_depth_pass_threshold"],
        ),
        peer_review_depth_block_threshold=_public_nonnegative_count(
            "peer_review_depth_block_threshold",
            payload["peer_review_depth_block_threshold"],
        ),
        review_latency_watch_hours=_public_positive_decimal(
            "review_latency_watch_hours",
            payload["review_latency_watch_hours"],
        ),
        review_latency_block_hours=_public_positive_decimal(
            "review_latency_block_hours",
            payload["review_latency_block_hours"],
        ),
        review_count=_public_nonnegative_count(
            "review_count",
            payload["review_count"],
        ),
        pass_count=_public_nonnegative_count("pass_count", payload["pass_count"]),
        watch_count=_public_nonnegative_count("watch_count", payload["watch_count"]),
        block_count=_public_nonnegative_count("block_count", payload["block_count"]),
        max_learning_gap_score=_public_optional_unit_decimal(
            "max_learning_gap_score",
            payload["max_learning_gap_score"],
        ),
        report_status=_public_status("report_status", payload["report_status"]),
        reason_codes=_public_report_reason_codes(
            "reason_codes",
            payload["reason_codes"],
        ),
        reason_code_counts=reason_code_counts,
        results=results,
        validation_digest=_public_digest(
            "validation_digest",
            payload["validation_digest"],
        ),
        paper_only=_public_true("paper_only", payload["paper_only"]),
        report_only=_public_true("report_only", payload["report_only"]),
        readonly=_public_true("readonly", payload["readonly"]),
    )


def _reason_code_count_from_public_payload(
    value: object,
) -> ResearchTeamDomainReviewLearningGapReasonCodeCount:
    if type(value) is not dict:
        raise ValueError("reason_code_count must match exact canonical schema")
    _require_exact_schema("reason_code_count", value, _REASON_COUNT_PUBLIC_FIELDS)
    return ResearchTeamDomainReviewLearningGapReasonCodeCount(
        reason_code=_public_reason_count_code("reason_code", value["reason_code"]),
        count=_public_positive_count("count", value["count"]),
        paper_only=_public_true("paper_only", value["paper_only"]),
        report_only=_public_true("report_only", value["report_only"]),
        readonly=_public_true("readonly", value["readonly"]),
    )


def _result_from_public_payload(
    value: object,
) -> ResearchTeamDomainReviewLearningGapResult:
    if type(value) is not dict:
        raise ValueError("result must match exact canonical schema")
    _require_exact_schema("result", value, _RESULT_PUBLIC_FIELDS)
    return ResearchTeamDomainReviewLearningGapResult(
        review_fingerprint=_public_digest(
            "review_fingerprint",
            value["review_fingerprint"],
        ),
        domain_fingerprint=_public_digest(
            "domain_fingerprint",
            value["domain_fingerprint"],
        ),
        unresolved_corrections=_public_nonnegative_count(
            "unresolved_corrections",
            value["unresolved_corrections"],
        ),
        stale_memory_reuse_count=_public_nonnegative_count(
            "stale_memory_reuse_count",
            value["stale_memory_reuse_count"],
        ),
        calibration_drift=_public_unit_decimal(
            "calibration_drift",
            value["calibration_drift"],
        ),
        evidence_coverage_ratio=_public_unit_decimal(
            "evidence_coverage_ratio",
            value["evidence_coverage_ratio"],
        ),
        peer_review_depth=_public_nonnegative_count(
            "peer_review_depth",
            value["peer_review_depth"],
        ),
        review_latency_hours=_public_nonnegative_decimal(
            "review_latency_hours",
            value["review_latency_hours"],
        ),
        unresolved_corrections_score=_public_unit_decimal(
            "unresolved_corrections_score",
            value["unresolved_corrections_score"],
        ),
        stale_memory_reuse_score=_public_unit_decimal(
            "stale_memory_reuse_score",
            value["stale_memory_reuse_score"],
        ),
        calibration_drift_score=_public_unit_decimal(
            "calibration_drift_score",
            value["calibration_drift_score"],
        ),
        evidence_gap_score=_public_unit_decimal(
            "evidence_gap_score",
            value["evidence_gap_score"],
        ),
        peer_review_gap_score=_public_unit_decimal(
            "peer_review_gap_score",
            value["peer_review_gap_score"],
        ),
        review_latency_score=_public_unit_decimal(
            "review_latency_score",
            value["review_latency_score"],
        ),
        learning_gap_score=_public_unit_decimal(
            "learning_gap_score",
            value["learning_gap_score"],
        ),
        review_status=_public_status("review_status", value["review_status"]),
        reason_codes=_public_result_reason_codes(
            "reason_codes",
            value["reason_codes"],
        ),
        validation_digest=_public_digest(
            "validation_digest",
            value["validation_digest"],
        ),
        paper_only=_public_true("paper_only", value["paper_only"]),
        report_only=_public_true("report_only", value["report_only"]),
        readonly=_public_true("readonly", value["readonly"]),
    )


def _require_exact_schema(
    name: str,
    value: dict[str, Any],
    expected_fields: tuple[str, ...],
) -> None:
    if any(type(key) is not str for key in value):
        raise ValueError(f"{name} must match exact canonical schema")
    if tuple(value) != expected_fields:
        raise ValueError(f"{name} must match exact canonical schema")


def _public_decimal(
    name: str,
    value: object,
    normalize: Any,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a canonical Decimal string")
    try:
        parsed = Decimal(value)
    except (ValueError, ArithmeticError) as exc:
        raise ValueError(f"{name} must be a canonical Decimal string") from exc
    normalized = normalize(name, parsed)
    if format(normalized, "f") != value:
        raise ValueError(f"{name} must be a canonical Decimal string")
    return normalized


def _public_positive_count(name: str, value: object) -> Decimal:
    return _public_decimal(name, value, _normalize_positive_count)


def _public_nonnegative_count(name: str, value: object) -> Decimal:
    return _public_decimal(name, value, _normalize_nonnegative_count)


def _public_positive_decimal(name: str, value: object) -> Decimal:
    return _public_decimal(name, value, _normalize_positive_decimal)


def _public_nonnegative_decimal(name: str, value: object) -> Decimal:
    return _public_decimal(name, value, _normalize_nonnegative_decimal)


def _public_unit_decimal(name: str, value: object) -> Decimal:
    return _public_decimal(name, value, _normalize_unit_decimal)


def _public_optional_unit_decimal(name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _public_unit_decimal(name, value)


def _public_text(name: str, value: object) -> str:
    _require_public_text(name, value)
    return value


def _public_status(name: str, value: object) -> str:
    _require_status(name, value)
    return value


def _public_digest(name: str, value: object) -> str:
    _require_digest(name, value)
    return value


def _public_true(name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{name} must be True")
    return True


def _public_datetime(name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a canonical UTC datetime string") from exc
    normalized = _as_utc(name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{name} must be a canonical UTC datetime string")
    return normalized


def _public_result_reason_codes(name: str, value: object) -> tuple[str, ...]:
    return _public_reason_codes(name, value, _normalize_result_reason_codes)


def _public_report_reason_codes(name: str, value: object) -> tuple[str, ...]:
    return _public_reason_codes(name, value, _normalize_report_reason_codes)


def _public_reason_count_code(name: str, value: object) -> str:
    return _normalize_reason_count_code(name, value)


def _public_reason_codes(name: str, value: object, normalize: Any) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{name} must match exact canonical schema")
    normalized = normalize(name, tuple(value))
    if list(normalized) != value:
        raise ValueError(f"{name} must match exact canonical schema")
    return normalized


def _result_sort_key(
    result: ResearchTeamDomainReviewLearningGapResult,
) -> tuple[int, Decimal, str, str]:
    return (
        _STATUS_WEIGHT[result.review_status],
        _negative_decimal(result.learning_gap_score),
        result.domain_fingerprint,
        result.review_fingerprint,
    )


def _normalize_result_reason_codes(name: str, values: object) -> tuple[str, ...]:
    codes = _normalize_public_reason_codes(name, values)
    if not codes:
        raise ValueError(f"{name} must not be empty")
    if any(code not in _RESULT_REASONS for code in codes):
        raise ValueError(f"{name} must contain a supported reason code")
    if "domain_review_learning_gap_pass" in codes and len(codes) != 1:
        raise ValueError(f"{name} pass reason must stand alone")
    if codes == ("domain_review_learning_gap_pass",):
        return codes
    if any(code in _PASS_REASONS for code in codes):
        raise ValueError(f"{name} pass reason must stand alone")
    return codes


def _normalize_report_reason_codes(name: str, values: object) -> tuple[str, ...]:
    codes = _normalize_public_reason_codes(name, values)
    if not codes:
        raise ValueError(f"{name} must not be empty")
    if codes == ("research_team_domain_review_learning_gap_report_empty",):
        return codes
    if "research_team_domain_review_learning_gap_report_empty" in codes:
        raise ValueError(f"{name} empty reason must stand alone")
    return codes


def _normalize_public_reason_codes(name: str, values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be an iterable")
    try:
        codes = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable") from exc
    for code in codes:
        _require_public_text(name, code)
        compact_code = "".join(part for part in code if part != "_")
        if not compact_code.isalnum() or code.lower() != code:
            raise ValueError(f"{name} must contain lowercase snake case values")
    return tuple(sorted(dict.fromkeys(codes), key=_reason_sort_key))


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    if reason_code in _REASON_PRIORITY:
        return (_REASON_PRIORITY.index(reason_code), reason_code)
    return (len(_REASON_PRIORITY), reason_code)


def _reason_count_sort_key(
    count: ResearchTeamDomainReviewLearningGapReasonCodeCount,
) -> tuple[int, str]:
    return _reason_sort_key(count.reason_code)


def _normalize_reason_count_code(name: str, value: object) -> str:
    code = _normalize_public_reason_codes(name, (value,))[0]
    if code not in _REASON_PRIORITY:
        raise ValueError(f"{name} must be a supported reason code")
    return code


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize_count(Decimal(value))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        total = _ZERO
        for value in values:
            total = total + _normalize_decimal("sum value", value)
        return _quantize(total)


def _difference(left: Decimal, right: Decimal) -> Decimal:
    left = _normalize_decimal("left value", left)
    right = _normalize_decimal("right value", right)
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(left - right)


def _negative_decimal(value: Decimal) -> Decimal:
    value = _normalize_decimal("sort score", value)
    if value.is_zero():
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return -value


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    denominator = _normalize_decimal("denominator", denominator)
    if denominator <= _ZERO:
        raise ValueError("denominator must be positive")
    numerator = _normalize_decimal("numerator", numerator)
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    value = _ratio(numerator, denominator)
    if value > _ONE:
        return _ONE
    return value


def _normalize_positive_count(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be an integer")
    return _quantize_count(normalized)


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    quantized = _quantize(normalized)
    if quantized <= _ZERO:
        raise ValueError(f"{name} must remain positive after quantization")
    return quantized


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(normalized)


def _normalize_unit_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(normalized)


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal of exact type")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{name} must not use signed zero")
    return value


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(_DECIMAL_CONTEXT):
            quantized = value.quantize(_QUANTUM)
    except DecimalException as exc:
        raise ValueError("value exceeds fixed Decimal context") from exc
    return _ZERO if quantized.is_zero() else quantized


def _quantize_count(value: Decimal) -> Decimal:
    try:
        with localcontext(_DECIMAL_CONTEXT):
            quantized = value.quantize(_COUNT_QUANTUM)
    except DecimalException as exc:
        raise ValueError("value exceeds fixed Decimal context") from exc
    return _COUNT_ZERO if quantized.is_zero() else quantized


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    try:
        offset = value.utcoffset()
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValueError(f"{name} must use a valid timezone offset") from exc
    if offset is None:
        raise ValueError(f"{name} must be timezone-aware")
    try:
        return value.astimezone(UTC)
    except (OverflowError, TypeError, ValueError) as exc:
        raise ValueError(f"{name} must fit within the UTC datetime boundary") from exc


def _require_watch_not_above_block(watch_threshold: Decimal, block_threshold: Decimal) -> None:
    if watch_threshold > block_threshold:
        raise ValueError("watch threshold must not exceed block threshold")


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _store_public_snapshot(value: object) -> None:
    identity = id(value)
    existing_reference = _PUBLIC_SNAPSHOT_REFS.get(identity)
    if existing_reference is not None and existing_reference() is value:
        _require_untampered_public_dataclass(value, type(value).__name__)
        return
    snapshot = _public_snapshot(value)

    def _clear_snapshot(reference: weakref.ReferenceType[object]) -> None:
        if _PUBLIC_SNAPSHOT_REFS.get(identity) is reference:
            _PUBLIC_SNAPSHOTS.pop(identity, None)
            _PUBLIC_SNAPSHOT_REFS.pop(identity, None)

    reference = weakref.ref(value, _clear_snapshot)
    _PUBLIC_SNAPSHOTS[identity] = snapshot
    _PUBLIC_SNAPSHOT_REFS[identity] = reference


def _require_untampered_public_dataclass(value: object, label: str) -> None:
    identity = id(value)
    expected = _PUBLIC_SNAPSHOTS.get(identity)
    reference = _PUBLIC_SNAPSHOT_REFS.get(identity)
    if type(expected) is not tuple or reference is None or reference() is not value:
        raise ValueError(f"{label} canonical snapshot is missing")
    try:
        actual = _public_snapshot(value)
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError(f"{label} was modified after initialization") from exc
    if actual != expected:
        raise ValueError(f"{label} was modified after initialization")


def _require_untampered_report(
    report: ResearchTeamDomainReviewLearningGapReport,
) -> None:
    _require_exact_public_shape(report, "report")
    if type(report.results) is not tuple or type(report.reason_code_counts) is not tuple:
        raise ValueError("report was modified after initialization")
    for result in report.results:
        if type(result) is not ResearchTeamDomainReviewLearningGapResult:
            raise ValueError("report was modified after initialization")
        _require_exact_public_shape(result, "result")
        require_paper_only_flags("domain review learning gap result", result)
    for count in report.reason_code_counts:
        if type(count) is not ResearchTeamDomainReviewLearningGapReasonCodeCount:
            raise ValueError("report was modified after initialization")
        _require_exact_public_shape(count, "reason count")
        require_paper_only_flags("domain review learning gap reason count", count)
    require_paper_only_flags("domain review learning gap report", report)
    _validate_report(report)
    _require_untampered_report_members(report)
    _require_untampered_public_dataclass(report, "report")


def _require_untampered_report_members(
    report: ResearchTeamDomainReviewLearningGapReport,
) -> None:
    for result in report.results:
        _require_untampered_public_dataclass(result, "result")
    for count in report.reason_code_counts:
        _require_untampered_public_dataclass(count, "reason count")


def _public_snapshot(value: object) -> tuple[tuple[str, Any], ...]:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("public snapshot requires a dataclass instance")
    _require_exact_public_shape(value, "dataclass")
    field_info = fields(value)
    return tuple(
        (field.name, _snapshot_value(getattr(value, field.name)))
        for field in field_info
    )


def _require_exact_public_shape(value: object, label: str) -> None:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError(f"{label} was modified after initialization")
    field_names = tuple(field.name for field in fields(value))
    try:
        namespace = vars(value)
    except TypeError as exc:
        raise ValueError(f"{label} was modified after initialization") from exc
    if type(namespace) is not dict or tuple(namespace) != field_names:
        raise ValueError(f"{label} was modified after initialization")


def _snapshot_value(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return (
            "dataclass",
            type(value),
            _public_snapshot(value),
        )
    if type(value) is Decimal:
        return ("decimal", value.as_tuple())
    if type(value) is datetime:
        return ("datetime", value.isoformat(), value.fold)
    if type(value) is tuple:
        return ("tuple", tuple(_snapshot_value(item) for item in value))
    if type(value) is list:
        return ("list", tuple(_snapshot_value(item) for item in value))
    if type(value) is dict:
        return (
            "dict",
            tuple(
                (_snapshot_value(key), _snapshot_value(item))
                for key, item in value.items()
            ),
        )
    if type(value) is str:
        return (
            "string_digest",
            sha256(b"canonical-snapshot\0" + value.encode("utf-8")).hexdigest(),
        )
    if value is None or type(value) in (bool, int, float):
        return (type(value), value)
    raise ValueError("public snapshot contains an unsupported value")


def _require_status(name: str, value: object) -> None:
    _require_public_text(name, value)
    if value not in _STATUSES:
        raise ValueError(f"{name} must be block, watch, or pass")


def _require_private_key(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a non-empty canonical string")


def _require_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a non-empty canonical string")


def _require_public_text(name: str, value: object) -> None:
    _require_text(name, value)
    normalized = value.lower()
    if any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public value")


def _require_digest(name: str, value: object) -> None:
    _require_text(name, value)
    if len(value) != 64 or any(char not in _HEX_CHARS for char in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _fingerprint(value: str) -> str:
    _require_private_key("fingerprint value", value)
    return sha256(value.encode("utf-8")).hexdigest()


def _validation_digest(values: dict[str, Any]) -> str:
    ready = _json_ready(values)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool:
        return value
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        if value.is_zero() and value.is_signed():
            raise ValueError("JSON Decimal value must not use signed zero")
        return format(value, "f")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is str:
        _require_public_text("JSON value", value)
        return value
    if type(value) in (int, float):
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_public_text("JSON object key", key)
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_payload(
    value: Any,
    *,
    _active_ids: set[int] | None = None,
    _depth: int = 0,
) -> None:
    if _depth > _MAX_PUBLIC_PAYLOAD_DEPTH:
        raise ValueError("payload exceeds the maximum nesting depth")
    active_ids = set() if _active_ids is None else _active_ids
    if type(value) is dict:
        identity = id(value)
        if identity in active_ids:
            raise ValueError("payload must not contain cycles")
        active_ids.add(identity)
        try:
            for key, item in value.items():
                _require_public_text("payload key", key)
                if key in _FLAG_NAMES and item is not True:
                    raise ValueError(f"{key} must be True in payload")
                _reject_unsafe_payload(
                    item,
                    _active_ids=active_ids,
                    _depth=_depth + 1,
                )
        finally:
            active_ids.remove(identity)
        return
    if isinstance(value, list):
        identity = id(value)
        if identity in active_ids:
            raise ValueError("payload must not contain cycles")
        active_ids.add(identity)
        try:
            for item in value:
                _reject_unsafe_payload(
                    item,
                    _active_ids=active_ids,
                    _depth=_depth + 1,
                )
        finally:
            active_ids.remove(identity)
        return
    if type(value) in (int, float):
        raise ValueError("payload numeric values must use Decimal strings")
    if isinstance(value, datetime):
        if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("payload datetime values must be timezone-aware")
    if type(value) is str:
        _require_public_text("payload value", value)


__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_REVIEW_LEARNING_GAP_REPORT_CONFIG_VERSION",
    "ResearchTeamDomainReviewLearningGapConfig",
    "ResearchTeamDomainReviewLearningGapInput",
    "ResearchTeamDomainReviewLearningGapReasonCodeCount",
    "ResearchTeamDomainReviewLearningGapReport",
    "ResearchTeamDomainReviewLearningGapResult",
    "build_research_team_domain_review_learning_gap_report",
    "research_team_domain_review_learning_gap_report_payload",
)
