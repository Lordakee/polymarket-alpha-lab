"""Report-only settlement-rule change diff research snapshot."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_SETTLEMENT_RULE_CHANGE_DIFF_REPORT_CONFIG_VERSION = (
    "research-settlement-rule-change-diff-report-v1"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_VERDICTS = frozenset(("pass", "watch", "block"))
_RISK_DIRECTIONS = frozenset(("decreased", "unchanged", "increased"))
_REVIEW_STATUSES = frozenset(("not_required", "pending", "complete"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TERMS = (
    "raw",
    "question",
    "slug",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "auth",
    "private_key",
    "secret",
    "wallet",
    "account",
    "balance",
    "order",
    "cancel",
    "replace",
    "sign",
    "exchange_mutation",
    "mutation",
    "buy",
    "sell",
    "trade",
    "network",
    "database",
    "persist",
    "write",
)
_REASON_CODE_SEQUENCE = (
    "event_id_mismatch_block",
    "risk_decreased",
    "risk_unchanged",
    "risk_increase_pass",
    "risk_increase_watch",
    "risk_increase_block",
    "source_verification_pass",
    "source_verification_watch",
    "source_verification_block",
    "manual_review_not_required",
    "manual_review_complete",
    "manual_review_pending",
    "manual_review_unresolved_block",
    "settlement_rule_change_diff_pass",
)


@dataclass(frozen=True)
class SettlementRuleChangeDiffConfig:
    config_version: str = DEFAULT_RESEARCH_SETTLEMENT_RULE_CHANGE_DIFF_REPORT_CONFIG_VERSION
    watch_risk_delta: Decimal = Decimal("0.050000")
    block_risk_delta: Decimal = Decimal("0.200000")
    min_verified_source_count: Decimal = Decimal("2.000000")
    min_official_source_count: Decimal = Decimal("1.000000")
    min_independent_source_family_count: Decimal = Decimal("2.000000")
    min_source_confidence_score: Decimal = Decimal("0.700000")
    max_conflicting_source_count: Decimal = Decimal("0.000000")
    max_source_age_hours: Decimal = Decimal("24.000000")
    manual_review_block_issue_count: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SettlementRuleChangeDiffConfig:
            raise TypeError("SettlementRuleChangeDiffConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not SettlementRuleChangeDiffConfig:
            raise ValueError("config must be exactly SettlementRuleChangeDiffConfig")
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SETTLEMENT_RULE_CHANGE_DIFF_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("watch_risk_delta", "block_risk_delta"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_risk_delta <= self.watch_risk_delta:
            raise ValueError("block_risk_delta must be greater than watch_risk_delta")
        for field_name in (
            "min_verified_source_count",
            "min_official_source_count",
            "min_independent_source_family_count",
            "max_conflicting_source_count",
            "manual_review_block_issue_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.manual_review_block_issue_count <= _ZERO:
            raise ValueError("manual_review_block_issue_count must be positive")
        object.__setattr__(
            self,
            "min_source_confidence_score",
            _require_ratio_decimal(
                "min_source_confidence_score",
                self.min_source_confidence_score,
            ),
        )
        object.__setattr__(
            self,
            "max_source_age_hours",
            _require_nonnegative_decimal("max_source_age_hours", self.max_source_age_hours),
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class SettlementRuleSummary:
    event_id: str
    rule_digest: str
    criteria_count: Decimal
    ambiguous_criteria_count: Decimal
    dispute_window_hours: Decimal
    settlement_window_hours: Decimal
    manual_resolution_allowed: bool
    evidence_threshold_score: Decimal
    settlement_risk_score: Decimal
    summary_reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SettlementRuleSummary:
            raise TypeError("SettlementRuleSummary does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not SettlementRuleSummary:
            raise ValueError("rule summary must be exactly SettlementRuleSummary")
        _require_public_identifier("event_id", self.event_id)
        _require_sha256_digest("rule_digest", self.rule_digest)
        object.__setattr__(
            self,
            "criteria_count",
            _require_positive_count_decimal("criteria_count", self.criteria_count),
        )
        object.__setattr__(
            self,
            "ambiguous_criteria_count",
            _require_nonnegative_count_decimal(
                "ambiguous_criteria_count",
                self.ambiguous_criteria_count,
            ),
        )
        if self.ambiguous_criteria_count > self.criteria_count:
            raise ValueError("ambiguous_criteria_count must not exceed criteria_count")
        for field_name in ("dispute_window_hours", "settlement_window_hours"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_bool("manual_resolution_allowed", self.manual_resolution_allowed)
        for field_name in ("evidence_threshold_score", "settlement_risk_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "summary_reason_codes",
            _normalize_reason_codes(
                "summary_reason_codes",
                self.summary_reason_codes,
                allow_empty=True,
            ),
        )
        _require_hard_flags("rule summary", self)
        _reject_unsafe_public_payload("rule summary", self)


@dataclass(frozen=True)
class SettlementRuleSourceVerification:
    verification_digest: str
    verified_source_count: Decimal
    official_source_count: Decimal
    independent_source_family_count: Decimal
    conflicting_source_count: Decimal
    source_confidence_score: Decimal
    latest_source_age_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SettlementRuleSourceVerification:
            raise TypeError("SettlementRuleSourceVerification does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not SettlementRuleSourceVerification:
            raise ValueError(
                "source verification must be exactly SettlementRuleSourceVerification",
            )
        _normalize_source_verification_fields(self)
        _require_hard_flags("source verification", self)
        _reject_unsafe_public_payload("source verification", self)


@dataclass(frozen=True)
class SettlementRuleManualReview:
    review_digest: str
    review_status: str
    required_issue_count: Decimal
    completed_issue_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SettlementRuleManualReview:
            raise TypeError("SettlementRuleManualReview does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not SettlementRuleManualReview:
            raise ValueError("manual review must be exactly SettlementRuleManualReview")
        _require_sha256_digest("review_digest", self.review_digest)
        _require_member("review_status", self.review_status, _REVIEW_STATUSES)
        for field_name in ("required_issue_count", "completed_issue_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        _validate_manual_review_counts(
            review_status=self.review_status,
            required_issue_count=self.required_issue_count,
            completed_issue_count=self.completed_issue_count,
        )
        _require_hard_flags("manual review", self)
        _reject_unsafe_public_payload("manual review", self)


@dataclass(frozen=True)
class SettlementRuleRiskChange:
    old_risk_score: Decimal
    new_risk_score: Decimal
    risk_delta: Decimal
    risk_direction: str
    risk_verdict: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SettlementRuleRiskChange:
            raise TypeError("SettlementRuleRiskChange does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not SettlementRuleRiskChange:
            raise ValueError("risk change must be exactly SettlementRuleRiskChange")
        for field_name in ("old_risk_score", "new_risk_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "risk_delta",
            _require_delta_decimal("risk_delta", self.risk_delta),
        )
        if self.risk_delta != _quantize(self.new_risk_score - self.old_risk_score):
            raise ValueError("risk_delta must equal new_risk_score less old_risk_score")
        _require_member("risk_direction", self.risk_direction, _RISK_DIRECTIONS)
        if self.risk_direction != _risk_direction(self.risk_delta):
            raise ValueError("risk_direction must match risk_delta")
        _require_verdict("risk_verdict", self.risk_verdict)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        if self.risk_verdict != _verdict_from_reason_codes(self.reason_codes):
            raise ValueError("risk_verdict must match reason_codes")
        _require_hard_flags("risk change", self)
        _reject_unsafe_public_payload("risk change", self)


@dataclass(frozen=True)
class SettlementRuleSourceVerificationResult:
    verification_digest: str
    verified_source_count: Decimal
    official_source_count: Decimal
    independent_source_family_count: Decimal
    conflicting_source_count: Decimal
    source_confidence_score: Decimal
    latest_source_age_hours: Decimal
    verification_verdict: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SettlementRuleSourceVerificationResult:
            raise TypeError(
                "SettlementRuleSourceVerificationResult does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not SettlementRuleSourceVerificationResult:
            raise ValueError(
                "source verification result must be exactly "
                "SettlementRuleSourceVerificationResult",
            )
        _normalize_source_verification_fields(self)
        _require_verdict("verification_verdict", self.verification_verdict)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        if self.verification_verdict != _verdict_from_reason_codes(self.reason_codes):
            raise ValueError("verification_verdict must match reason_codes")
        _require_hard_flags("source verification result", self)
        _reject_unsafe_public_payload("source verification result", self)


@dataclass(frozen=True)
class SettlementRuleManualReviewResult:
    review_digest: str
    review_status: str
    required_issue_count: Decimal
    completed_issue_count: Decimal
    unresolved_issue_count: Decimal
    review_verdict: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not SettlementRuleManualReviewResult:
            raise TypeError("SettlementRuleManualReviewResult does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not SettlementRuleManualReviewResult:
            raise ValueError(
                "manual review result must be exactly SettlementRuleManualReviewResult",
            )
        _require_sha256_digest("review_digest", self.review_digest)
        _require_member("review_status", self.review_status, _REVIEW_STATUSES)
        for field_name in (
            "required_issue_count",
            "completed_issue_count",
            "unresolved_issue_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        _validate_manual_review_counts(
            review_status=self.review_status,
            required_issue_count=self.required_issue_count,
            completed_issue_count=self.completed_issue_count,
        )
        expected_unresolved = _quantize(
            self.required_issue_count - self.completed_issue_count,
        )
        if self.unresolved_issue_count != expected_unresolved:
            raise ValueError("unresolved_issue_count must match issue counts")
        _require_verdict("review_verdict", self.review_verdict)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        if self.review_verdict != _verdict_from_reason_codes(self.reason_codes):
            raise ValueError("review_verdict must match reason_codes")
        _require_hard_flags("manual review result", self)
        _reject_unsafe_public_payload("manual review result", self)


@dataclass(frozen=True)
class ResearchSettlementRuleChangeDiffReport:
    generated_at: datetime
    config_version: str
    verdict: str
    old_rule_summary: SettlementRuleSummary
    new_rule_summary: SettlementRuleSummary
    risk_change: SettlementRuleRiskChange
    source_verification: SettlementRuleSourceVerificationResult
    manual_review: SettlementRuleManualReviewResult
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSettlementRuleChangeDiffReport:
            raise TypeError(
                "ResearchSettlementRuleChangeDiffReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSettlementRuleChangeDiffReport:
            raise ValueError(
                "report must be exactly ResearchSettlementRuleChangeDiffReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SETTLEMENT_RULE_CHANGE_DIFF_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_verdict("verdict", self.verdict)
        _require_exact_type(
            "old_rule_summary",
            self.old_rule_summary,
            SettlementRuleSummary,
        )
        _require_exact_type(
            "new_rule_summary",
            self.new_rule_summary,
            SettlementRuleSummary,
        )
        _require_exact_type("risk_change", self.risk_change, SettlementRuleRiskChange)
        _require_exact_type(
            "source_verification",
            self.source_verification,
            SettlementRuleSourceVerificationResult,
        )
        _require_exact_type(
            "manual_review",
            self.manual_review,
            SettlementRuleManualReviewResult,
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
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchSettlementRuleChangeDiffReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_settlement_rule_change_diff_report(
    old_rule_summary: SettlementRuleSummary,
    new_rule_summary: SettlementRuleSummary,
    *,
    source_verification: SettlementRuleSourceVerification,
    manual_review: SettlementRuleManualReview,
    generated_at: datetime,
    config: SettlementRuleChangeDiffConfig | None = None,
) -> ResearchSettlementRuleChangeDiffReport:
    """Build a local, report-only event settlement rule-change diff."""

    if config is None:
        config = SettlementRuleChangeDiffConfig()
    _require_exact_type("config", config, SettlementRuleChangeDiffConfig)
    _require_exact_type("old_rule_summary", old_rule_summary, SettlementRuleSummary)
    _require_exact_type("new_rule_summary", new_rule_summary, SettlementRuleSummary)
    _require_exact_type(
        "source_verification",
        source_verification,
        SettlementRuleSourceVerification,
    )
    _require_exact_type("manual_review", manual_review, SettlementRuleManualReview)
    generated_at = _as_utc("generated_at", generated_at)

    risk_change = _build_risk_change(old_rule_summary, new_rule_summary, config)
    source_result = _build_source_verification_result(source_verification, config)
    manual_result = _build_manual_review_result(manual_review, config)
    reason_codes = _report_reason_codes(
        old_rule_summary=old_rule_summary,
        new_rule_summary=new_rule_summary,
        risk_change=risk_change,
        source_verification=source_result,
        manual_review=manual_result,
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "verdict": _verdict_from_reason_codes(reason_codes),
        "old_rule_summary": old_rule_summary,
        "new_rule_summary": new_rule_summary,
        "risk_change": risk_change,
        "source_verification": source_result,
        "manual_review": manual_result,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSettlementRuleChangeDiffReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _build_risk_change(
    old_rule_summary: SettlementRuleSummary,
    new_rule_summary: SettlementRuleSummary,
    config: SettlementRuleChangeDiffConfig,
) -> SettlementRuleRiskChange:
    risk_delta = _quantize(
        new_rule_summary.settlement_risk_score - old_rule_summary.settlement_risk_score,
    )
    if risk_delta < _ZERO:
        reason_codes = ("risk_decreased",)
    elif risk_delta == _ZERO:
        reason_codes = ("risk_unchanged",)
    elif risk_delta >= config.block_risk_delta:
        reason_codes = ("risk_increase_block",)
    elif risk_delta >= config.watch_risk_delta:
        reason_codes = ("risk_increase_watch",)
    else:
        reason_codes = ("risk_increase_pass",)
    return SettlementRuleRiskChange(
        old_risk_score=old_rule_summary.settlement_risk_score,
        new_risk_score=new_rule_summary.settlement_risk_score,
        risk_delta=risk_delta,
        risk_direction=_risk_direction(risk_delta),
        risk_verdict=_verdict_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _build_source_verification_result(
    source_verification: SettlementRuleSourceVerification,
    config: SettlementRuleChangeDiffConfig,
) -> SettlementRuleSourceVerificationResult:
    if (
        source_verification.verified_source_count < config.min_verified_source_count
        or source_verification.official_source_count < config.min_official_source_count
        or source_verification.independent_source_family_count
        < config.min_independent_source_family_count
        or source_verification.conflicting_source_count > config.max_conflicting_source_count
        or source_verification.source_confidence_score < config.min_source_confidence_score
    ):
        reason_codes = ("source_verification_block",)
    elif source_verification.latest_source_age_hours > config.max_source_age_hours:
        reason_codes = ("source_verification_watch",)
    else:
        reason_codes = ("source_verification_pass",)
    return SettlementRuleSourceVerificationResult(
        verification_digest=source_verification.verification_digest,
        verified_source_count=source_verification.verified_source_count,
        official_source_count=source_verification.official_source_count,
        independent_source_family_count=(
            source_verification.independent_source_family_count
        ),
        conflicting_source_count=source_verification.conflicting_source_count,
        source_confidence_score=source_verification.source_confidence_score,
        latest_source_age_hours=source_verification.latest_source_age_hours,
        verification_verdict=_verdict_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _build_manual_review_result(
    manual_review: SettlementRuleManualReview,
    config: SettlementRuleChangeDiffConfig,
) -> SettlementRuleManualReviewResult:
    unresolved_issue_count = _quantize(
        manual_review.required_issue_count - manual_review.completed_issue_count,
    )
    if unresolved_issue_count >= config.manual_review_block_issue_count:
        reason_codes = ("manual_review_unresolved_block",)
    elif manual_review.review_status == "pending" or unresolved_issue_count > _ZERO:
        reason_codes = ("manual_review_pending",)
    elif manual_review.review_status == "complete":
        reason_codes = ("manual_review_complete",)
    else:
        reason_codes = ("manual_review_not_required",)
    return SettlementRuleManualReviewResult(
        review_digest=manual_review.review_digest,
        review_status=manual_review.review_status,
        required_issue_count=manual_review.required_issue_count,
        completed_issue_count=manual_review.completed_issue_count,
        unresolved_issue_count=unresolved_issue_count,
        review_verdict=_verdict_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _report_reason_codes(
    *,
    old_rule_summary: SettlementRuleSummary,
    new_rule_summary: SettlementRuleSummary,
    risk_change: SettlementRuleRiskChange,
    source_verification: SettlementRuleSourceVerificationResult,
    manual_review: SettlementRuleManualReviewResult,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if old_rule_summary.event_id != new_rule_summary.event_id:
        reason_codes.append("event_id_mismatch_block")
    reason_codes.extend(risk_change.reason_codes)
    reason_codes.extend(source_verification.reason_codes)
    reason_codes.extend(manual_review.reason_codes)
    normalized = _normalize_reason_codes(
        "report reason_codes",
        tuple(reason_codes),
        allow_empty=False,
    )
    if _verdict_from_reason_codes(normalized) == "pass":
        normalized = _normalize_reason_codes(
            "report reason_codes",
            (*normalized, "settlement_rule_change_diff_pass"),
            allow_empty=False,
        )
    return normalized


def _validate_report_consistency(report: ResearchSettlementRuleChangeDiffReport) -> None:
    expected_reason_codes = _report_reason_codes(
        old_rule_summary=report.old_rule_summary,
        new_rule_summary=report.new_rule_summary,
        risk_change=report.risk_change,
        source_verification=report.source_verification,
        manual_review=report.manual_review,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match report sections")
    if report.verdict != _verdict_from_reason_codes(report.reason_codes):
        raise ValueError("verdict must match reason_codes")


def _normalize_source_verification_fields(
    value: SettlementRuleSourceVerification | SettlementRuleSourceVerificationResult,
) -> None:
    _require_sha256_digest("verification_digest", value.verification_digest)
    for field_name in (
        "verified_source_count",
        "official_source_count",
        "independent_source_family_count",
        "conflicting_source_count",
    ):
        object.__setattr__(
            value,
            field_name,
            _require_nonnegative_count_decimal(field_name, getattr(value, field_name)),
        )
    if value.official_source_count > value.verified_source_count:
        raise ValueError("official_source_count must not exceed verified_source_count")
    if value.independent_source_family_count > value.verified_source_count:
        raise ValueError(
            "independent_source_family_count must not exceed verified_source_count",
        )
    if value.conflicting_source_count > value.verified_source_count:
        raise ValueError("conflicting_source_count must not exceed verified_source_count")
    object.__setattr__(
        value,
        "source_confidence_score",
        _require_ratio_decimal(
            "source_confidence_score",
            value.source_confidence_score,
        ),
    )
    object.__setattr__(
        value,
        "latest_source_age_hours",
        _require_nonnegative_decimal(
            "latest_source_age_hours",
            value.latest_source_age_hours,
        ),
    )


def _validate_manual_review_counts(
    *,
    review_status: str,
    required_issue_count: Decimal,
    completed_issue_count: Decimal,
) -> None:
    if completed_issue_count > required_issue_count:
        raise ValueError("completed_issue_count must not exceed required_issue_count")
    if review_status == "not_required" and (
        required_issue_count != _ZERO or completed_issue_count != _ZERO
    ):
        raise ValueError("not_required review must have zero issue counts")
    if review_status == "complete" and completed_issue_count != required_issue_count:
        raise ValueError("complete review must have completed all issues")
    if review_status == "pending" and completed_issue_count >= required_issue_count:
        raise ValueError("pending review must have unresolved issues")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_member(field_name: str, value: object, allowed: frozenset[str]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a supported value")
    return value


def _require_verdict(field_name: str, value: object) -> str:
    return _require_member(field_name, value, _VERDICTS)


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_delta_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < -_ONE or normalized > _ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


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
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _risk_direction(risk_delta: Decimal) -> str:
    if risk_delta < _ZERO:
        return "decreased"
    if risk_delta > _ZERO:
        return "increased"
    return "unchanged"


def _verdict_from_reason_codes(reason_codes: Sequence[str]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    if "manual_review_pending" in reason_codes:
        return "watch"
    return "pass"


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchSettlementRuleChangeDiffReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
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
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_SETTLEMENT_RULE_CHANGE_DIFF_REPORT_CONFIG_VERSION",
    "ResearchSettlementRuleChangeDiffReport",
    "SettlementRuleChangeDiffConfig",
    "SettlementRuleManualReview",
    "SettlementRuleManualReviewResult",
    "SettlementRuleRiskChange",
    "SettlementRuleSourceVerification",
    "SettlementRuleSourceVerificationResult",
    "SettlementRuleSummary",
    "build_research_settlement_rule_change_diff_report",
)
