"""Pure paper-only evidence staleness score for candidate decisions."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal, localcontext
from typing import Any


DEFAULT_CANDIDATE_DECISION_EVIDENCE_STALENESS_SCORE_CONFIG_VERSION = (
    "candidate-decision-evidence-staleness-score-v0"
)
STALENESS_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT_PRECISION = 64

_RAW_CANDIDATE_PUBLIC_TERM_PARTS = (
    ("candidate", "_id"),
    ("candidate", "_slug"),
    ("condition", "_id"),
)
_RAW_MARKET_PUBLIC_TERM_PARTS = (
    ("market", "_id"),
    ("market", "_slug"),
    ("ques", "tion"),
)
_SOURCE_REFERENCE_PUBLIC_TERM_PARTS = (
    ("source", "_ref"),
    ("source", "_refs"),
    ("source", "_url"),
    ("source", "_uri"),
    ("source", "_text"),
    ("source", "_excerpt"),
    ("source", "_title"),
    ("raw", "_text"),
    ("ht", "tp://"),
    ("ht", "tps://"),
    ("w", "ww."),
    (":", "//"),
    ("source", "-ref:"),
    ("source", "_ref:"),
    ("source", "-url:"),
)
_UNSAFE_LIVE_PUBLIC_TERM_PARTS = (
    ("api", "_key"),
    ("au", "th"),
    ("bear", "er"),
    ("b", "uy"),
    ("connection", "_string"),
    ("credential", ""),
    ("data", "base"),
    ("d", "sn"),
    ("j", "wt"),
    ("oauth", ""),
    ("or", "der"),
    ("password", ""),
    ("position", ""),
    ("private", "_key"),
    ("recommenda", "tion"),
    ("secret", ""),
    ("se", "ll"),
    ("session", ""),
    ("ta", "ble"),
    ("to", "ken"),
    ("tra", "de"),
    ("trading", ""),
    ("wal", "let"),
    ("\u4ed3", "\u4f4d"),
)
_PUBLIC_STATUS_ALIASES = ("ready", "blocked", "matched", "supported")

_RAW_CANDIDATE_PUBLIC_TERMS = tuple(
    "".join(parts) for parts in _RAW_CANDIDATE_PUBLIC_TERM_PARTS
)
_RAW_MARKET_PUBLIC_TERMS = tuple("".join(parts) for parts in _RAW_MARKET_PUBLIC_TERM_PARTS)
_SOURCE_REFERENCE_PUBLIC_TERMS = tuple(
    "".join(parts) for parts in _SOURCE_REFERENCE_PUBLIC_TERM_PARTS
)
_UNSAFE_LIVE_PUBLIC_TERMS = tuple(
    "".join(parts) for parts in _UNSAFE_LIVE_PUBLIC_TERM_PARTS
)


@dataclass(frozen=True)
class CandidateDecisionEvidenceStalenessScoreConfig:
    config_version: str = (
        DEFAULT_CANDIDATE_DECISION_EVIDENCE_STALENESS_SCORE_CONFIG_VERSION
    )
    max_pass_evidence_staleness_score: Decimal = Decimal("0.250000")
    max_watch_evidence_staleness_score: Decimal = Decimal("0.500000")
    max_pass_newest_evidence_age_hours: Decimal = Decimal("24.000000")
    max_watch_newest_evidence_age_hours: Decimal = Decimal("72.000000")
    max_pass_average_evidence_age_hours: Decimal = Decimal("48.000000")
    max_watch_average_evidence_age_hours: Decimal = Decimal("168.000000")
    max_pass_prior_research_age_hours: Decimal = Decimal("24.000000")
    max_watch_prior_research_age_hours: Decimal = Decimal("72.000000")
    max_pass_stale_source_ratio: Decimal = Decimal("0.250000")
    max_watch_stale_source_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionEvidenceStalenessScoreConfig:
            raise TypeError(
                "CandidateDecisionEvidenceStalenessScoreConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, CandidateDecisionEvidenceStalenessScoreConfig)
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_CANDIDATE_DECISION_EVIDENCE_STALENESS_SCORE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "max_pass_evidence_staleness_score",
            "max_watch_evidence_staleness_score",
            "max_pass_stale_source_ratio",
            "max_watch_stale_source_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_newest_evidence_age_hours",
            "max_watch_newest_evidence_age_hours",
            "max_pass_average_evidence_age_hours",
            "max_watch_average_evidence_age_hours",
            "max_pass_prior_research_age_hours",
            "max_watch_prior_research_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_phase_flags("config", self)
        reject_candidate_decision_evidence_staleness_score_unsafe_payload(
            "evidence staleness config",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionEvidenceStalenessScoreInput:
    source_count: Decimal
    stale_source_count: Decimal
    newest_evidence_age_hours: Decimal
    average_evidence_age_hours: Decimal
    oldest_evidence_age_hours: Decimal
    prior_research_age_hours: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionEvidenceStalenessScoreInput:
            raise TypeError(
                "CandidateDecisionEvidenceStalenessScoreInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("input", self, CandidateDecisionEvidenceStalenessScoreInput)
        for field_name in ("source_count", "stale_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "newest_evidence_age_hours",
            "average_evidence_age_hours",
            "oldest_evidence_age_hours",
            "prior_research_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _validate_input(self)
        _require_phase_flags("input", self)
        reject_candidate_decision_evidence_staleness_score_unsafe_payload(
            "evidence staleness input",
            self,
        )


@dataclass(frozen=True)
class CandidateDecisionEvidenceStalenessScoreReport:
    config_version: str
    max_pass_evidence_staleness_score: Decimal
    max_watch_evidence_staleness_score: Decimal
    max_pass_newest_evidence_age_hours: Decimal
    max_watch_newest_evidence_age_hours: Decimal
    max_pass_average_evidence_age_hours: Decimal
    max_watch_average_evidence_age_hours: Decimal
    max_pass_prior_research_age_hours: Decimal
    max_watch_prior_research_age_hours: Decimal
    max_pass_stale_source_ratio: Decimal
    max_watch_stale_source_ratio: Decimal
    source_count: Decimal
    stale_source_count: Decimal
    newest_evidence_age_hours: Decimal
    average_evidence_age_hours: Decimal
    oldest_evidence_age_hours: Decimal
    prior_research_age_hours: Decimal
    stale_source_ratio: Decimal
    newest_evidence_staleness_component: Decimal
    average_evidence_staleness_component: Decimal
    prior_research_staleness_component: Decimal
    stale_source_ratio_component: Decimal
    evidence_staleness_score: Decimal
    staleness_status: str
    hard_blocker_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateDecisionEvidenceStalenessScoreReport:
            raise TypeError(
                "CandidateDecisionEvidenceStalenessScoreReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, CandidateDecisionEvidenceStalenessScoreReport)
        object.__setattr__(
            self,
            "config_version",
            _require_canonical_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_CANDIDATE_DECISION_EVIDENCE_STALENESS_SCORE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "max_pass_evidence_staleness_score",
            "max_watch_evidence_staleness_score",
            "max_pass_stale_source_ratio",
            "max_watch_stale_source_ratio",
            "stale_source_ratio",
            "newest_evidence_staleness_component",
            "average_evidence_staleness_component",
            "prior_research_staleness_component",
            "stale_source_ratio_component",
            "evidence_staleness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_newest_evidence_age_hours",
            "max_watch_newest_evidence_age_hours",
            "max_pass_average_evidence_age_hours",
            "max_watch_average_evidence_age_hours",
            "max_pass_prior_research_age_hours",
            "max_watch_prior_research_age_hours",
            "newest_evidence_age_hours",
            "average_evidence_age_hours",
            "oldest_evidence_age_hours",
            "prior_research_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_count", "stale_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_choice("staleness_status", self.staleness_status, STALENESS_STATUSES)
        object.__setattr__(
            self,
            "hard_blocker_codes",
            _normalize_reason_codes(
                "hard_blocker_codes",
                self.hard_blocker_codes,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_report(self)
        _require_phase_flags("report", self)
        reject_candidate_decision_evidence_staleness_score_unsafe_payload(
            "evidence staleness report",
            self,
        )
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return candidate_decision_evidence_staleness_score_payload(self)


def build_candidate_decision_evidence_staleness_score_report(
    score_input: CandidateDecisionEvidenceStalenessScoreInput,
    *,
    config: CandidateDecisionEvidenceStalenessScoreConfig | None = None,
) -> CandidateDecisionEvidenceStalenessScoreReport:
    if type(score_input) is not CandidateDecisionEvidenceStalenessScoreInput:
        raise ValueError(
            "score_input must be a CandidateDecisionEvidenceStalenessScoreInput",
        )
    report_config = config or CandidateDecisionEvidenceStalenessScoreConfig()
    if type(report_config) is not CandidateDecisionEvidenceStalenessScoreConfig:
        raise ValueError(
            "config must be a CandidateDecisionEvidenceStalenessScoreConfig",
        )
    _require_phase_flags("input", score_input)
    _require_phase_flags("config", report_config)
    reject_candidate_decision_evidence_staleness_score_unsafe_payload(
        "evidence staleness input",
        score_input,
    )
    reject_candidate_decision_evidence_staleness_score_unsafe_payload(
        "evidence staleness config",
        report_config,
    )
    return CandidateDecisionEvidenceStalenessScoreReport(
        **_report_values(score_input, report_config),
    )


def candidate_decision_evidence_staleness_score_payload(
    report: CandidateDecisionEvidenceStalenessScoreReport,
) -> dict[str, Any]:
    if type(report) is not CandidateDecisionEvidenceStalenessScoreReport:
        raise ValueError(
            "report must be a CandidateDecisionEvidenceStalenessScoreReport",
        )
    _require_phase_flags("report", report)
    _validate_report(report)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    reject_candidate_decision_evidence_staleness_score_unsafe_payload(
        "evidence staleness report",
        report,
    )
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_candidate_decision_evidence_staleness_score_public_payload(payload)
    return payload


def validate_candidate_decision_evidence_staleness_score_public_payload(
    payload: object,
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_numbers(payload)
    _reject_public_status_aliases(payload)
    reject_candidate_decision_evidence_staleness_score_unsafe_payload(
        "evidence staleness public payload",
        payload,
    )


def reject_candidate_decision_evidence_staleness_score_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for path, item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _RAW_CANDIDATE_PUBLIC_TERMS):
            raise ValueError(f"raw candidate public payload entry in {label}: {path}")
        if any(term in lowered for term in _RAW_MARKET_PUBLIC_TERMS):
            raise ValueError(f"raw market public payload entry in {label}: {path}")
        if any(term in lowered for term in _SOURCE_REFERENCE_PUBLIC_TERMS):
            raise ValueError(f"source refs public payload entry in {label}: {path}")
        if any(term in lowered for term in _UNSAFE_LIVE_PUBLIC_TERMS):
            raise ValueError(f"unsafe live surface public payload entry in {label}: {path}")


def _report_values(
    score_input: CandidateDecisionEvidenceStalenessScoreInput,
    config: CandidateDecisionEvidenceStalenessScoreConfig,
) -> dict[str, object]:
    stale_source_ratio = _stale_source_ratio(
        score_input.stale_source_count,
        score_input.source_count,
    )
    newest_component = _threshold_component(
        score_input.newest_evidence_age_hours,
        config.max_pass_newest_evidence_age_hours,
        config.max_watch_newest_evidence_age_hours,
    )
    average_component = _threshold_component(
        score_input.average_evidence_age_hours,
        config.max_pass_average_evidence_age_hours,
        config.max_watch_average_evidence_age_hours,
    )
    prior_research_component = _threshold_component(
        score_input.prior_research_age_hours,
        config.max_pass_prior_research_age_hours,
        config.max_watch_prior_research_age_hours,
    )
    stale_source_component = _threshold_component(
        stale_source_ratio,
        config.max_pass_stale_source_ratio,
        config.max_watch_stale_source_ratio,
    )
    evidence_staleness_score = _evidence_staleness_score(
        newest_component,
        average_component,
        prior_research_component,
        stale_source_component,
    )
    hard_blockers = _hard_blocker_codes(
        score_input.newest_evidence_age_hours,
        score_input.average_evidence_age_hours,
        score_input.prior_research_age_hours,
        stale_source_ratio,
        evidence_staleness_score,
        config,
    )
    staleness_status = _staleness_status(evidence_staleness_score, hard_blockers, config)
    return {
        "config_version": config.config_version,
        "max_pass_evidence_staleness_score": config.max_pass_evidence_staleness_score,
        "max_watch_evidence_staleness_score": config.max_watch_evidence_staleness_score,
        "max_pass_newest_evidence_age_hours": config.max_pass_newest_evidence_age_hours,
        "max_watch_newest_evidence_age_hours": config.max_watch_newest_evidence_age_hours,
        "max_pass_average_evidence_age_hours": (
            config.max_pass_average_evidence_age_hours
        ),
        "max_watch_average_evidence_age_hours": (
            config.max_watch_average_evidence_age_hours
        ),
        "max_pass_prior_research_age_hours": config.max_pass_prior_research_age_hours,
        "max_watch_prior_research_age_hours": config.max_watch_prior_research_age_hours,
        "max_pass_stale_source_ratio": config.max_pass_stale_source_ratio,
        "max_watch_stale_source_ratio": config.max_watch_stale_source_ratio,
        "source_count": score_input.source_count,
        "stale_source_count": score_input.stale_source_count,
        "newest_evidence_age_hours": score_input.newest_evidence_age_hours,
        "average_evidence_age_hours": score_input.average_evidence_age_hours,
        "oldest_evidence_age_hours": score_input.oldest_evidence_age_hours,
        "prior_research_age_hours": score_input.prior_research_age_hours,
        "stale_source_ratio": stale_source_ratio,
        "newest_evidence_staleness_component": newest_component,
        "average_evidence_staleness_component": average_component,
        "prior_research_staleness_component": prior_research_component,
        "stale_source_ratio_component": stale_source_component,
        "evidence_staleness_score": evidence_staleness_score,
        "staleness_status": staleness_status,
        "hard_blocker_codes": hard_blockers,
        "reason_codes": _reason_codes(
            score_input.reason_codes,
            score_input.newest_evidence_age_hours,
            score_input.average_evidence_age_hours,
            score_input.prior_research_age_hours,
            stale_source_ratio,
            evidence_staleness_score,
            staleness_status,
            config,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _threshold_component(
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> Decimal:
    if value <= pass_threshold:
        return ZERO
    if value >= watch_threshold:
        return ONE
    numerator = _subtract_nonnegative(
        "threshold_component_numerator",
        value,
        pass_threshold,
    )
    denominator = _subtract_nonnegative(
        "threshold_component_denominator",
        watch_threshold,
        pass_threshold,
    )
    return _safe_unit_ratio(numerator, denominator)


def _stale_source_ratio(stale_source_count: Decimal, source_count: Decimal) -> Decimal:
    if source_count == ZERO:
        return ONE
    return _safe_unit_ratio(stale_source_count, source_count)


def _evidence_staleness_score(
    newest_component: Decimal,
    average_component: Decimal,
    prior_research_component: Decimal,
    stale_source_component: Decimal,
) -> Decimal:
    return _normalize_unit_decimal(
        "evidence_staleness_score",
        (
            newest_component
            + average_component
            + prior_research_component
            + stale_source_component
        )
        / Decimal("4"),
    )


def _hard_blocker_codes(
    newest_evidence_age_hours: Decimal,
    average_evidence_age_hours: Decimal,
    prior_research_age_hours: Decimal,
    stale_source_ratio: Decimal,
    evidence_staleness_score: Decimal,
    config: CandidateDecisionEvidenceStalenessScoreConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if newest_evidence_age_hours > config.max_watch_newest_evidence_age_hours:
        codes.append("newest_evidence_age_block")
    if average_evidence_age_hours > config.max_watch_average_evidence_age_hours:
        codes.append("average_evidence_age_block")
    if prior_research_age_hours > config.max_watch_prior_research_age_hours:
        codes.append("prior_research_age_block")
    if stale_source_ratio > config.max_watch_stale_source_ratio:
        codes.append("stale_source_ratio_block")
    if evidence_staleness_score > config.max_watch_evidence_staleness_score:
        codes.append("evidence_staleness_score_block")
    return tuple(codes)


def _staleness_status(
    evidence_staleness_score: Decimal,
    hard_blocker_codes: tuple[str, ...],
    config: CandidateDecisionEvidenceStalenessScoreConfig,
) -> str:
    if hard_blocker_codes:
        return "block"
    if evidence_staleness_score <= config.max_pass_evidence_staleness_score:
        return "pass"
    if evidence_staleness_score <= config.max_watch_evidence_staleness_score:
        return "watch"
    return "block"


def _reason_codes(
    existing: tuple[str, ...],
    newest_evidence_age_hours: Decimal,
    average_evidence_age_hours: Decimal,
    prior_research_age_hours: Decimal,
    stale_source_ratio: Decimal,
    evidence_staleness_score: Decimal,
    staleness_status: str,
    config: CandidateDecisionEvidenceStalenessScoreConfig,
) -> tuple[str, ...]:
    additions = [
        "candidate_decision_evidence_staleness_score",
        f"staleness_{staleness_status}",
        _threshold_reason(
            "newest_evidence_age",
            newest_evidence_age_hours,
            config.max_pass_newest_evidence_age_hours,
            config.max_watch_newest_evidence_age_hours,
        ),
        _threshold_reason(
            "average_evidence_age",
            average_evidence_age_hours,
            config.max_pass_average_evidence_age_hours,
            config.max_watch_average_evidence_age_hours,
        ),
        _threshold_reason(
            "prior_research_age",
            prior_research_age_hours,
            config.max_pass_prior_research_age_hours,
            config.max_watch_prior_research_age_hours,
        ),
        _threshold_reason(
            "stale_source_ratio",
            stale_source_ratio,
            config.max_pass_stale_source_ratio,
            config.max_watch_stale_source_ratio,
        ),
    ]
    if staleness_status == "pass":
        additions.append("research_refresh_not_required")
    elif staleness_status == "watch":
        additions.append("research_refresh_watch")
    else:
        additions.append("research_refresh_required")
    if evidence_staleness_score > config.max_watch_evidence_staleness_score:
        additions.append("evidence_staleness_score_block")
    return _append_reason_codes(existing, tuple(additions))


def _threshold_reason(
    prefix: str,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value <= pass_threshold:
        return f"{prefix}_pass"
    if value <= watch_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_block"


def _append_reason_codes(
    existing: tuple[str, ...],
    additions: tuple[str, ...],
) -> tuple[str, ...]:
    values = list(existing)
    for addition in additions:
        if addition not in values:
            values.append(addition)
    return tuple(values)


def _validate_config(config: CandidateDecisionEvidenceStalenessScoreConfig) -> None:
    if config.max_pass_evidence_staleness_score > config.max_watch_evidence_staleness_score:
        raise ValueError("max_pass_evidence_staleness_score must not exceed watch level")
    if config.max_pass_newest_evidence_age_hours > config.max_watch_newest_evidence_age_hours:
        raise ValueError("max_pass_newest_evidence_age_hours must not exceed watch level")
    if (
        config.max_pass_average_evidence_age_hours
        > config.max_watch_average_evidence_age_hours
    ):
        raise ValueError("max_pass_average_evidence_age_hours must not exceed watch level")
    if config.max_pass_prior_research_age_hours > config.max_watch_prior_research_age_hours:
        raise ValueError("max_pass_prior_research_age_hours must not exceed watch level")
    if config.max_pass_stale_source_ratio > config.max_watch_stale_source_ratio:
        raise ValueError("max_pass_stale_source_ratio must not exceed watch level")


def _validate_input(score_input: CandidateDecisionEvidenceStalenessScoreInput) -> None:
    if score_input.stale_source_count > score_input.source_count:
        raise ValueError("stale_source_count must not exceed source_count")
    if score_input.oldest_evidence_age_hours < score_input.newest_evidence_age_hours:
        raise ValueError("oldest_evidence_age_hours must not be less than newest evidence age")
    if score_input.average_evidence_age_hours < score_input.newest_evidence_age_hours:
        raise ValueError("average_evidence_age_hours must not be less than newest evidence age")
    if score_input.average_evidence_age_hours > score_input.oldest_evidence_age_hours:
        raise ValueError("average_evidence_age_hours must not exceed oldest evidence age")


def _validate_report(report: CandidateDecisionEvidenceStalenessScoreReport) -> None:
    _validate_config_fields(report)
    if report.stale_source_count > report.source_count:
        raise ValueError("stale_source_count must not exceed source_count")
    if report.oldest_evidence_age_hours < report.newest_evidence_age_hours:
        raise ValueError("oldest_evidence_age_hours must not be less than newest evidence age")
    if report.average_evidence_age_hours < report.newest_evidence_age_hours:
        raise ValueError("average_evidence_age_hours must not be less than newest evidence age")
    if report.average_evidence_age_hours > report.oldest_evidence_age_hours:
        raise ValueError("average_evidence_age_hours must not exceed oldest evidence age")

    expected_stale_ratio = _stale_source_ratio(report.stale_source_count, report.source_count)
    if report.stale_source_ratio != expected_stale_ratio:
        raise ValueError("stale_source_ratio must match source counts")
    expected_newest_component = _threshold_component(
        report.newest_evidence_age_hours,
        report.max_pass_newest_evidence_age_hours,
        report.max_watch_newest_evidence_age_hours,
    )
    if report.newest_evidence_staleness_component != expected_newest_component:
        raise ValueError("newest_evidence_staleness_component must match evidence age")
    expected_average_component = _threshold_component(
        report.average_evidence_age_hours,
        report.max_pass_average_evidence_age_hours,
        report.max_watch_average_evidence_age_hours,
    )
    if report.average_evidence_staleness_component != expected_average_component:
        raise ValueError("average_evidence_staleness_component must match evidence age")
    expected_prior_component = _threshold_component(
        report.prior_research_age_hours,
        report.max_pass_prior_research_age_hours,
        report.max_watch_prior_research_age_hours,
    )
    if report.prior_research_staleness_component != expected_prior_component:
        raise ValueError("prior_research_staleness_component must match research age")
    expected_stale_source_component = _threshold_component(
        report.stale_source_ratio,
        report.max_pass_stale_source_ratio,
        report.max_watch_stale_source_ratio,
    )
    if report.stale_source_ratio_component != expected_stale_source_component:
        raise ValueError("stale_source_ratio_component must match stale source ratio")
    expected_score = _evidence_staleness_score(
        expected_newest_component,
        expected_average_component,
        expected_prior_component,
        expected_stale_source_component,
    )
    if report.evidence_staleness_score != expected_score:
        raise ValueError("evidence_staleness_score must match staleness components")
    expected_blockers = _hard_blocker_codes(
        report.newest_evidence_age_hours,
        report.average_evidence_age_hours,
        report.prior_research_age_hours,
        report.stale_source_ratio,
        report.evidence_staleness_score,
        _config_from_report(report),
    )
    if report.hard_blocker_codes != expected_blockers:
        raise ValueError("hard_blocker_codes must match evidence staleness fields")
    expected_status = _staleness_status(
        report.evidence_staleness_score,
        report.hard_blocker_codes,
        _config_from_report(report),
    )
    if report.staleness_status != expected_status:
        raise ValueError("staleness_status must match evidence staleness score")


def _validate_config_fields(report: CandidateDecisionEvidenceStalenessScoreReport) -> None:
    if report.max_pass_evidence_staleness_score > report.max_watch_evidence_staleness_score:
        raise ValueError("max_pass_evidence_staleness_score must not exceed watch level")
    if (
        report.max_pass_newest_evidence_age_hours
        > report.max_watch_newest_evidence_age_hours
    ):
        raise ValueError("max_pass_newest_evidence_age_hours must not exceed watch level")
    if (
        report.max_pass_average_evidence_age_hours
        > report.max_watch_average_evidence_age_hours
    ):
        raise ValueError("max_pass_average_evidence_age_hours must not exceed watch level")
    if report.max_pass_prior_research_age_hours > report.max_watch_prior_research_age_hours:
        raise ValueError("max_pass_prior_research_age_hours must not exceed watch level")
    if report.max_pass_stale_source_ratio > report.max_watch_stale_source_ratio:
        raise ValueError("max_pass_stale_source_ratio must not exceed watch level")


def _config_from_report(
    report: CandidateDecisionEvidenceStalenessScoreReport,
) -> CandidateDecisionEvidenceStalenessScoreConfig:
    return CandidateDecisionEvidenceStalenessScoreConfig(
        config_version=report.config_version,
        max_pass_evidence_staleness_score=report.max_pass_evidence_staleness_score,
        max_watch_evidence_staleness_score=report.max_watch_evidence_staleness_score,
        max_pass_newest_evidence_age_hours=report.max_pass_newest_evidence_age_hours,
        max_watch_newest_evidence_age_hours=report.max_watch_newest_evidence_age_hours,
        max_pass_average_evidence_age_hours=report.max_pass_average_evidence_age_hours,
        max_watch_average_evidence_age_hours=report.max_watch_average_evidence_age_hours,
        max_pass_prior_research_age_hours=report.max_pass_prior_research_age_hours,
        max_watch_prior_research_age_hours=report.max_watch_prior_research_age_hours,
        max_pass_stale_source_ratio=report.max_pass_stale_source_ratio,
        max_watch_stale_source_ratio=report.max_watch_stale_source_ratio,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _report_digest(report: CandidateDecisionEvidenceStalenessScoreReport) -> str:
    payload = _json_ready(
        {
            key: value
            for key, value in asdict(report).items()
            if key != "derived_validation_digest"
        },
    )
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        return str(value)
    if type(value) in (str, bool) or value is None:
        return value
    if type(value) is tuple or type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {
            str(key): _json_ready(item)
            for key, item in value.items()
        }
    if isinstance(value, Mapping):
        return {
            str(key): _json_ready(item)
            for key, item in value.items()
        }
    if type(value) is int or type(value) is float:
        raise ValueError("payload numeric values must be decimal strings")
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value.quantize(COUNT_QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        return decimal_value.quantize(QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is Decimal:
        return value
    if isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be an exact Decimal")
    raise ValueError(f"{field_name} must be a Decimal")


def _safe_unit_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        return _normalize_unit_decimal("ratio", numerator / denominator)


def _subtract_nonnegative(field_name: str, left: Decimal, right: Decimal) -> Decimal:
    value = left - right
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for item in value:
        normalized_item = _require_canonical_string(field_name, item)
        if normalized_item in normalized:
            raise ValueError(f"{field_name} must not contain duplicates")
        normalized.append(normalized_item)
    return tuple(normalized)


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value != value.strip() or not value:
        raise ValueError(f"{field_name} must be canonical")
    return value


def _require_choice(field_name: str, value: object, choices: tuple[str, ...]) -> None:
    if type(value) is not str or value not in choices:
        raise ValueError(f"{field_name} must be one of {choices}")


def _require_phase_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name)
        if type(flag) is not bool or flag is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(item not in "0123456789abcdef" for item in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be an exact {expected_type.__name__}")


def _iter_public_strings(payload: object, path: str = "$") -> tuple[tuple[str, str], ...]:
    values: list[tuple[str, str]] = []
    if is_dataclass(payload) and not isinstance(payload, type):
        values.extend(_iter_public_strings(asdict(payload), path))
    elif isinstance(payload, Mapping):
        for key, value in payload.items():
            key_text = str(key)
            values.append((f"{path}.{key_text}", key_text))
            values.extend(_iter_public_strings(value, f"{path}.{key_text}"))
    elif type(payload) is tuple or type(payload) is list:
        for index, item in enumerate(payload):
            values.extend(_iter_public_strings(item, f"{path}[{index}]"))
    elif type(payload) is str:
        values.append((path, payload))
    return tuple(values)


def _reject_public_numbers(value: object) -> None:
    if type(value) is bool:
        return
    if type(value) is int or type(value) is float or type(value) is Decimal:
        raise ValueError("public payload numeric values must be decimal strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_numbers(item)
    elif type(value) is tuple or type(value) is list:
        for item in value:
            _reject_public_numbers(item)


def _reject_public_status_aliases(payload: object) -> None:
    for path, item in _iter_public_strings(payload):
        if item.lower() in _PUBLIC_STATUS_ALIASES:
            raise ValueError(f"public status alias is not allowed: {path}")


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_EVIDENCE_STALENESS_SCORE_CONFIG_VERSION",
    "STALENESS_STATUSES",
    "CandidateDecisionEvidenceStalenessScoreConfig",
    "CandidateDecisionEvidenceStalenessScoreInput",
    "CandidateDecisionEvidenceStalenessScoreReport",
    "build_candidate_decision_evidence_staleness_score_report",
    "candidate_decision_evidence_staleness_score_payload",
    "validate_candidate_decision_evidence_staleness_score_public_payload",
    "reject_candidate_decision_evidence_staleness_score_unsafe_payload",
)
