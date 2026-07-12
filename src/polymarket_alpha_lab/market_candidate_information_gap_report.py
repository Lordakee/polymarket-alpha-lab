"""Pure read-only information gap report for candidate Polymarket events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_MARKET_CANDIDATE_INFORMATION_GAP_REPORT_CONFIG_VERSION = (
    "market-candidate-information-gap-report-v0"
)
INFORMATION_GAP_BANDS = ("ready", "attention", "blocker")

READY_REASON = "market_candidate_information_gap_ready"
ATTENTION_REASON = "market_candidate_information_gap_attention"
BLOCKER_REASON = "market_candidate_information_gap_blocker"

OFFICIAL_SOURCE_MISSING_BLOCKER_REASON = "official_source_missing_blocker"
INDEPENDENT_SOURCE_GAP_ATTENTION_REASON = "independent_source_gap_attention"
INDEPENDENT_SOURCE_GAP_BLOCKER_REASON = "independent_source_gap_blocker"
FRESHNESS_GAP_ATTENTION_REASON = "freshness_gap_attention"
FRESHNESS_GAP_BLOCKER_REASON = "freshness_gap_blocker"
RESOLUTION_RULE_GAP_BLOCKER_REASON = "resolution_rule_gap_blocker"
COST_MODEL_GAP_ATTENTION_REASON = "cost_model_gap_attention"
TEAM_MEMORY_GAP_ATTENTION_REASON = "team_memory_gap_attention"
OPERATOR_REDACTION_GAP_BLOCKER_REASON = "operator_redaction_gap_blocker"
MANUAL_REVIEW_REQUIRED_BLOCKER_REASON = "manual_review_required_blocker"

REASON_PRIORITY = (
    BLOCKER_REASON,
    OFFICIAL_SOURCE_MISSING_BLOCKER_REASON,
    INDEPENDENT_SOURCE_GAP_BLOCKER_REASON,
    FRESHNESS_GAP_BLOCKER_REASON,
    RESOLUTION_RULE_GAP_BLOCKER_REASON,
    OPERATOR_REDACTION_GAP_BLOCKER_REASON,
    MANUAL_REVIEW_REQUIRED_BLOCKER_REASON,
    ATTENTION_REASON,
    INDEPENDENT_SOURCE_GAP_ATTENTION_REASON,
    FRESHNESS_GAP_ATTENTION_REASON,
    COST_MODEL_GAP_ATTENTION_REASON,
    TEAM_MEMORY_GAP_ATTENTION_REASON,
    READY_REASON,
)
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class MarketCandidateInformationGapConfig(_FinalDataclass):
    config_version: str = DEFAULT_MARKET_CANDIDATE_INFORMATION_GAP_REPORT_CONFIG_VERSION
    attention_score_threshold: Decimal = Decimal("0.250000")
    blocker_score_threshold: Decimal = Decimal("0.600000")
    freshness_attention_seconds: Decimal = Decimal("3600.000000")
    freshness_blocker_seconds: Decimal = Decimal("21600.000000")
    independent_source_attention_threshold: Decimal = Decimal("1.000000")
    independent_source_blocker_threshold: Decimal = Decimal("3.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketCandidateInformationGapConfig, "config")
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "attention_score_threshold",
            "blocker_score_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "freshness_attention_seconds",
            "freshness_blocker_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "independent_source_attention_threshold",
            "independent_source_blocker_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.blocker_score_threshold < self.attention_score_threshold:
            raise ValueError(
                "blocker_score_threshold must be greater than or equal to "
                "attention_score_threshold",
            )
        if self.freshness_blocker_seconds < self.freshness_attention_seconds:
            raise ValueError(
                "freshness_blocker_seconds must be greater than or equal to "
                "freshness_attention_seconds",
            )
        if (
            self.independent_source_blocker_threshold
            < self.independent_source_attention_threshold
        ):
            raise ValueError(
                "independent_source_blocker_threshold must be greater than or equal to "
                "independent_source_attention_threshold",
            )
        reject_unsafe_surface_fields("market candidate information gap config", self)
        require_paper_only_flags("market candidate information gap config", self)


@dataclass(frozen=True)
class MarketCandidateInformationGapInput(_FinalDataclass):
    candidate_key: str
    official_source_missing: bool
    independent_source_gap_count: Decimal
    freshness_gap_seconds: Decimal
    resolution_rule_gap: bool
    cost_model_gap: bool
    team_memory_gap: bool
    operator_redaction_gap: bool
    manual_review_required: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketCandidateInformationGapInput, "candidate")
        _require_public_string("candidate_key", self.candidate_key)
        object.__setattr__(
            self,
            "independent_source_gap_count",
            _require_nonnegative_count(
                "independent_source_gap_count",
                self.independent_source_gap_count,
            ),
        )
        object.__setattr__(
            self,
            "freshness_gap_seconds",
            _require_nonnegative_decimal(
                "freshness_gap_seconds",
                self.freshness_gap_seconds,
            ),
        )
        for field_name in (
            "official_source_missing",
            "resolution_rule_gap",
            "cost_model_gap",
            "team_memory_gap",
            "operator_redaction_gap",
            "manual_review_required",
        ):
            _require_bool(field_name, getattr(self, field_name))
        reject_unsafe_surface_fields("market candidate information gap input", self)
        require_paper_only_flags("market candidate information gap input", self)


@dataclass(frozen=True)
class MarketCandidateInformationGapReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    attention_score_threshold: Decimal
    blocker_score_threshold: Decimal
    candidate_key: str
    official_source_missing: bool
    independent_source_gap_count: Decimal
    freshness_gap_seconds: Decimal
    freshness_attention_seconds: Decimal
    freshness_blocker_seconds: Decimal
    independent_source_attention_threshold: Decimal
    independent_source_blocker_threshold: Decimal
    resolution_rule_gap: bool
    cost_model_gap: bool
    team_memory_gap: bool
    operator_redaction_gap: bool
    manual_review_required: bool
    information_gap_score: Decimal
    gap_band: str
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketCandidateInformationGapReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "attention_score_threshold",
            "blocker_score_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if self.blocker_score_threshold < self.attention_score_threshold:
            raise ValueError(
                "blocker_score_threshold must be greater than or equal to "
                "attention_score_threshold",
            )
        _require_public_string("candidate_key", self.candidate_key)
        object.__setattr__(
            self,
            "independent_source_gap_count",
            _require_nonnegative_count(
                "independent_source_gap_count",
                self.independent_source_gap_count,
            ),
        )
        object.__setattr__(
            self,
            "freshness_gap_seconds",
            _require_nonnegative_decimal(
                "freshness_gap_seconds",
                self.freshness_gap_seconds,
            ),
        )
        for field_name in (
            "freshness_attention_seconds",
            "freshness_blocker_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "independent_source_attention_threshold",
            "independent_source_blocker_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.freshness_blocker_seconds < self.freshness_attention_seconds:
            raise ValueError(
                "freshness_blocker_seconds must be greater than or equal to "
                "freshness_attention_seconds",
            )
        if (
            self.independent_source_blocker_threshold
            < self.independent_source_attention_threshold
        ):
            raise ValueError(
                "independent_source_blocker_threshold must be greater than or equal to "
                "independent_source_attention_threshold",
            )
        for field_name in (
            "official_source_missing",
            "resolution_rule_gap",
            "cost_model_gap",
            "team_memory_gap",
            "operator_redaction_gap",
            "manual_review_required",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "information_gap_score",
            _require_ratio("information_gap_score", self.information_gap_score),
        )
        _require_band("gap_band", self.gap_band)
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_reason_codes(
                self.blocked_reason_codes,
                allow_summary=False,
                field_name="blocked_reason_codes",
            ),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _normalize_reason_codes(
                self.attention_reason_codes,
                allow_summary=False,
                field_name="attention_reason_codes",
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                allow_summary=True,
                field_name="reason_codes",
            ),
        )
        object.__setattr__(
            self,
            "ready_ratio",
            _require_ratio("ready_ratio", self.ready_ratio),
        )
        _validate_report(self)
        reject_unsafe_surface_fields("market candidate information gap report", self)
        require_paper_only_flags("market candidate information gap report", self)

    @property
    def public_payload(self) -> dict[str, Any]:
        return market_candidate_information_gap_public_payload(self)

    @property
    def digest(self) -> str:
        return market_candidate_information_gap_digest(self)


def build_market_candidate_information_gap_report(
    candidate: MarketCandidateInformationGapInput,
    *,
    config: MarketCandidateInformationGapConfig,
    generated_at: datetime,
) -> MarketCandidateInformationGapReport:
    if type(candidate) is not MarketCandidateInformationGapInput:
        raise ValueError("candidate must be a MarketCandidateInformationGapInput")
    if type(config) is not MarketCandidateInformationGapConfig:
        raise ValueError("config must be a MarketCandidateInformationGapConfig")
    require_paper_only_flags("candidate", candidate)
    require_paper_only_flags("config", config)
    blocked_reason_codes = _blocked_reason_codes(candidate, config=config)
    attention_reason_codes = _attention_reason_codes(candidate, config=config)
    information_gap_score = _information_gap_score(
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
    )
    gap_band = _gap_band(
        information_gap_score=information_gap_score,
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
        config=config,
    )
    return MarketCandidateInformationGapReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        attention_score_threshold=config.attention_score_threshold,
        blocker_score_threshold=config.blocker_score_threshold,
        candidate_key=candidate.candidate_key,
        official_source_missing=candidate.official_source_missing,
        independent_source_gap_count=candidate.independent_source_gap_count,
        freshness_gap_seconds=candidate.freshness_gap_seconds,
        freshness_attention_seconds=config.freshness_attention_seconds,
        freshness_blocker_seconds=config.freshness_blocker_seconds,
        independent_source_attention_threshold=config.independent_source_attention_threshold,
        independent_source_blocker_threshold=config.independent_source_blocker_threshold,
        resolution_rule_gap=candidate.resolution_rule_gap,
        cost_model_gap=candidate.cost_model_gap,
        team_memory_gap=candidate.team_memory_gap,
        operator_redaction_gap=candidate.operator_redaction_gap,
        manual_review_required=candidate.manual_review_required,
        information_gap_score=information_gap_score,
        gap_band=gap_band,
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
        reason_codes=_summary_reason_codes(
            gap_band=gap_band,
            blocked_reason_codes=blocked_reason_codes,
            attention_reason_codes=attention_reason_codes,
        ),
        ready_ratio=_subtract_ratio(ONE, information_gap_score),
    )


def market_candidate_information_gap_public_payload(
    report: MarketCandidateInformationGapReport,
) -> dict[str, Any]:
    if type(report) is not MarketCandidateInformationGapReport:
        raise ValueError("report must be a MarketCandidateInformationGapReport")
    require_paper_only_flags("report", report)
    reject_unsafe_surface_fields("market candidate information gap report", report)
    payload = json_ready_no_floats(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    return payload


def market_candidate_information_gap_digest(
    report: MarketCandidateInformationGapReport,
) -> str:
    payload = market_candidate_information_gap_public_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _blocked_reason_codes(
    candidate: MarketCandidateInformationGapInput,
    *,
    config: MarketCandidateInformationGapConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if candidate.official_source_missing:
        reason_codes.append(OFFICIAL_SOURCE_MISSING_BLOCKER_REASON)
    if candidate.independent_source_gap_count >= config.independent_source_blocker_threshold:
        reason_codes.append(INDEPENDENT_SOURCE_GAP_BLOCKER_REASON)
    if candidate.freshness_gap_seconds >= config.freshness_blocker_seconds:
        reason_codes.append(FRESHNESS_GAP_BLOCKER_REASON)
    if candidate.resolution_rule_gap:
        reason_codes.append(RESOLUTION_RULE_GAP_BLOCKER_REASON)
    if candidate.operator_redaction_gap:
        reason_codes.append(OPERATOR_REDACTION_GAP_BLOCKER_REASON)
    if candidate.manual_review_required:
        reason_codes.append(MANUAL_REVIEW_REQUIRED_BLOCKER_REASON)
    return _normalize_reason_codes(
        tuple(reason_codes),
        allow_summary=False,
        field_name="blocked_reason_codes",
    )


def _attention_reason_codes(
    candidate: MarketCandidateInformationGapInput,
    *,
    config: MarketCandidateInformationGapConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if (
        config.independent_source_attention_threshold
        <= candidate.independent_source_gap_count
        < config.independent_source_blocker_threshold
    ):
        reason_codes.append(INDEPENDENT_SOURCE_GAP_ATTENTION_REASON)
    if (
        config.freshness_attention_seconds
        <= candidate.freshness_gap_seconds
        < config.freshness_blocker_seconds
    ):
        reason_codes.append(FRESHNESS_GAP_ATTENTION_REASON)
    if candidate.cost_model_gap:
        reason_codes.append(COST_MODEL_GAP_ATTENTION_REASON)
    if candidate.team_memory_gap:
        reason_codes.append(TEAM_MEMORY_GAP_ATTENTION_REASON)
    return _normalize_reason_codes(
        tuple(reason_codes),
        allow_summary=False,
        field_name="attention_reason_codes",
    )


def _information_gap_score(
    *,
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            Decimal(len(blocked_reason_codes)) * Decimal("0.125000")
            + Decimal(len(attention_reason_codes)) * Decimal("0.125000")
        )
        if score > ONE:
            return ONE
        return score.quantize(QUANT)


def _gap_band(
    *,
    information_gap_score: Decimal,
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
    config: MarketCandidateInformationGapConfig,
) -> str:
    if blocked_reason_codes or information_gap_score >= config.blocker_score_threshold:
        return "blocker"
    if attention_reason_codes or information_gap_score >= config.attention_score_threshold:
        return "attention"
    return "ready"


def _summary_reason_codes(
    *,
    gap_band: str,
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    summary = {
        "ready": READY_REASON,
        "attention": ATTENTION_REASON,
        "blocker": BLOCKER_REASON,
    }[gap_band]
    return _normalize_reason_codes(
        (summary,) + blocked_reason_codes + attention_reason_codes,
        allow_summary=True,
        field_name="reason_codes",
    )


def _validate_report(report: MarketCandidateInformationGapReport) -> None:
    expected_blocked = _blocked_reason_codes(
        MarketCandidateInformationGapInput(
            candidate_key=report.candidate_key,
            official_source_missing=report.official_source_missing,
            independent_source_gap_count=report.independent_source_gap_count,
            freshness_gap_seconds=report.freshness_gap_seconds,
            resolution_rule_gap=report.resolution_rule_gap,
            cost_model_gap=report.cost_model_gap,
            team_memory_gap=report.team_memory_gap,
            operator_redaction_gap=report.operator_redaction_gap,
            manual_review_required=report.manual_review_required,
        ),
        config=MarketCandidateInformationGapConfig(
            config_version=report.config_version,
            attention_score_threshold=report.attention_score_threshold,
            blocker_score_threshold=report.blocker_score_threshold,
            freshness_attention_seconds=report.freshness_attention_seconds,
            freshness_blocker_seconds=report.freshness_blocker_seconds,
            independent_source_attention_threshold=(
                report.independent_source_attention_threshold
            ),
            independent_source_blocker_threshold=(
                report.independent_source_blocker_threshold
            ),
        ),
    )
    expected_attention = _attention_reason_codes(
        MarketCandidateInformationGapInput(
            candidate_key=report.candidate_key,
            official_source_missing=report.official_source_missing,
            independent_source_gap_count=report.independent_source_gap_count,
            freshness_gap_seconds=report.freshness_gap_seconds,
            resolution_rule_gap=report.resolution_rule_gap,
            cost_model_gap=report.cost_model_gap,
            team_memory_gap=report.team_memory_gap,
            operator_redaction_gap=report.operator_redaction_gap,
            manual_review_required=report.manual_review_required,
        ),
        config=MarketCandidateInformationGapConfig(
            config_version=report.config_version,
            attention_score_threshold=report.attention_score_threshold,
            blocker_score_threshold=report.blocker_score_threshold,
            freshness_attention_seconds=report.freshness_attention_seconds,
            freshness_blocker_seconds=report.freshness_blocker_seconds,
            independent_source_attention_threshold=(
                report.independent_source_attention_threshold
            ),
            independent_source_blocker_threshold=(
                report.independent_source_blocker_threshold
            ),
        ),
    )
    if report.blocked_reason_codes != expected_blocked:
        raise ValueError("blocked_reason_codes must match gap inputs")
    if report.attention_reason_codes != expected_attention:
        raise ValueError("attention_reason_codes must match gap inputs")
    expected_score = _information_gap_score(
        blocked_reason_codes=report.blocked_reason_codes,
        attention_reason_codes=report.attention_reason_codes,
    )
    if report.information_gap_score != expected_score:
        raise ValueError("information_gap_score must match reason codes")
    if report.ready_ratio != _subtract_ratio(ONE, report.information_gap_score):
        raise ValueError("ready_ratio must equal one minus information_gap_score")
    if report.reason_codes != _summary_reason_codes(
        gap_band=report.gap_band,
        blocked_reason_codes=report.blocked_reason_codes,
        attention_reason_codes=report.attention_reason_codes,
    ):
        raise ValueError("reason_codes must match gap band and reason codes")
    expected_band = _gap_band(
        information_gap_score=report.information_gap_score,
        blocked_reason_codes=report.blocked_reason_codes,
        attention_reason_codes=report.attention_reason_codes,
        config=MarketCandidateInformationGapConfig(
            config_version=report.config_version,
            attention_score_threshold=report.attention_score_threshold,
            blocker_score_threshold=report.blocker_score_threshold,
            freshness_attention_seconds=report.freshness_attention_seconds,
            freshness_blocker_seconds=report.freshness_blocker_seconds,
            independent_source_attention_threshold=(
                report.independent_source_attention_threshold
            ),
            independent_source_blocker_threshold=(
                report.independent_source_blocker_threshold
            ),
        ),
    )
    if report.gap_band != expected_band:
        raise ValueError("gap_band must match gap inputs and thresholds")
    if report.gap_band == "ready" and (
        report.blocked_reason_codes
        or report.attention_reason_codes
        or report.information_gap_score != ZERO
    ):
        raise ValueError("ready report must not contain open gaps")
    if report.gap_band == "attention" and report.blocked_reason_codes:
        raise ValueError("attention report must not contain blocked reason codes")


def _subtract_ratio(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = left - right
    if value < ZERO:
        return ZERO
    return value.quantize(QUANT)


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer")
    return normalized.quantize(QUANT)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized.quantize(QUANT)


def _require_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE:
        raise ValueError(f"{field_name} must not exceed 1")
    return normalized.quantize(QUANT)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANT)


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_band(field_name: str, value: object) -> None:
    if type(value) is not str or value not in INFORMATION_GAP_BANDS:
        allowed = ", ".join(INFORMATION_GAP_BANDS)
        raise ValueError(f"{field_name} must be one of: {allowed}")


def _normalize_reason_codes(
    values: tuple[str, ...],
    *,
    allow_summary: bool,
    field_name: str,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    allowed = set(REASON_PRIORITY)
    if not allow_summary:
        allowed.discard(READY_REASON)
        allowed.discard(ATTENTION_REASON)
        allowed.discard(BLOCKER_REASON)
    for value in values:
        if type(value) is not str or not value:
            raise ValueError(f"{field_name} must contain non-empty strings")
        if value not in allowed:
            raise ValueError(f"unknown reason_code: {value}")
        if value not in normalized:
            normalized.append(value)
    return tuple(sorted(normalized, key=REASON_PRIORITY.index))


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


__all__ = (
    "DEFAULT_MARKET_CANDIDATE_INFORMATION_GAP_REPORT_CONFIG_VERSION",
    "INFORMATION_GAP_BANDS",
    "MarketCandidateInformationGapConfig",
    "MarketCandidateInformationGapInput",
    "MarketCandidateInformationGapReport",
    "build_market_candidate_information_gap_report",
    "market_candidate_information_gap_digest",
    "market_candidate_information_gap_public_payload",
)
