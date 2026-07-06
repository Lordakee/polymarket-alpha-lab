"""Pure paper/report/readonly candidate resolution source authority v10."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
import hashlib
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_CANDIDATE_RESOLUTION_SOURCE_AUTHORITY_V10_CONFIG_VERSION = (
    "strategy-candidate-resolution-source-authority-v10"
)

SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)

SOURCE_HIERARCHY_WEIGHT = Decimal("0.250000")
RULE_SPECIFICITY_WEIGHT = Decimal("0.200000")
ADJUDICATION_INDEPENDENCE_WEIGHT = Decimal("0.200000")
CONFLICT_QUALITY_WEIGHT = Decimal("0.075000")
OFFICIAL_SOURCE_AVAILABLE_WEIGHT = Decimal("0.315000")
BASELINE_SOURCE_RISK_OFFSET = Decimal("0.030000")

STATUSES = ("pass", "watch", "block")
RESULT_REASON_CODES = (
    "resolution_source_authority_pass",
    "resolution_source_authority_empty",
    "official_resolution_source_missing",
    "source_hierarchy_confidence_block",
    "source_hierarchy_confidence_watch",
    "conflicting_sources_block",
    "conflicting_sources_watch",
    "resolution_rule_specificity_block",
    "resolution_rule_specificity_watch",
    "adjudication_dependency_block",
    "adjudication_dependency_watch",
    "authority_score_block",
    "authority_score_watch",
)
REPORT_REASON_CODE_SEQUENCE = (
    "official_resolution_source_missing",
    "source_hierarchy_confidence_block",
    "source_hierarchy_confidence_watch",
    "conflicting_sources_block",
    "conflicting_sources_watch",
    "resolution_rule_specificity_block",
    "resolution_rule_specificity_watch",
    "adjudication_dependency_block",
    "adjudication_dependency_watch",
    "authority_score_block",
    "authority_score_watch",
)
BLOCK_REASON_CODES = (
    "official_resolution_source_missing",
    "source_hierarchy_confidence_block",
    "conflicting_sources_block",
    "resolution_rule_specificity_block",
    "adjudication_dependency_block",
    "authority_score_block",
)
WATCH_REASON_CODES = (
    "source_hierarchy_confidence_watch",
    "conflicting_sources_watch",
    "resolution_rule_specificity_watch",
    "adjudication_dependency_watch",
    "authority_score_watch",
)

UNSAFE_PUBLIC_PAYLOAD_KEY_FRAGMENTS = (
    "api_key",
    "authorization",
    "credential",
    "private" + "_key",
    "signing",
)
UNSAFE_PUBLIC_PAYLOAD_KEY_TOKENS = (
    "account",
    "auth",
    "balance",
    "cancel",
    "credential",
    "or" + "der",
    "secret",
    "sign",
    "token",
    "trade",
    "wal" + "let",
)


@dataclass(frozen=True)
class StrategyCandidateResolutionSourceAuthorityV10Config:
    config_version: str = (
        DEFAULT_STRATEGY_CANDIDATE_RESOLUTION_SOURCE_AUTHORITY_V10_CONFIG_VERSION
    )
    min_pass_source_hierarchy_confidence: Decimal = Decimal("0.750000")
    min_watch_source_hierarchy_confidence: Decimal = Decimal("0.500000")
    max_pass_conflicting_source_count: Decimal = Decimal("1.000000")
    max_watch_conflicting_source_count: Decimal = Decimal("3.000000")
    min_pass_rule_specificity: Decimal = Decimal("0.700000")
    min_watch_rule_specificity: Decimal = Decimal("0.450000")
    max_pass_adjudication_dependency: Decimal = Decimal("0.250000")
    max_watch_adjudication_dependency: Decimal = Decimal("0.600000")
    min_pass_authority_score: Decimal = Decimal("0.750000")
    min_watch_authority_score: Decimal = Decimal("0.550000")
    max_conflicting_source_count_for_score: Decimal = Decimal("5.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateResolutionSourceAuthorityV10Config:
            raise ValueError("config must be a StrategyCandidateResolutionSourceAuthorityV10Config")
        _require_identifier("config_version", self.config_version)
        for field_name in (
            "min_pass_source_hierarchy_confidence",
            "min_watch_source_hierarchy_confidence",
            "min_pass_rule_specificity",
            "min_watch_rule_specificity",
            "max_pass_adjudication_dependency",
            "max_watch_adjudication_dependency",
            "min_pass_authority_score",
            "min_watch_authority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_conflicting_source_count",
            "max_watch_conflicting_source_count",
            "max_conflicting_source_count_for_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.min_pass_source_hierarchy_confidence
            < self.min_watch_source_hierarchy_confidence
        ):
            raise ValueError(
                "min_pass_source_hierarchy_confidence must be at least watch threshold",
            )
        if self.max_pass_conflicting_source_count > self.max_watch_conflicting_source_count:
            raise ValueError(
                "max_pass_conflicting_source_count must be at most watch threshold",
            )
        if self.min_pass_rule_specificity < self.min_watch_rule_specificity:
            raise ValueError("min_pass_rule_specificity must be at least watch threshold")
        if self.max_pass_adjudication_dependency > self.max_watch_adjudication_dependency:
            raise ValueError(
                "max_pass_adjudication_dependency must be at most watch threshold",
            )
        if self.min_pass_authority_score < self.min_watch_authority_score:
            raise ValueError("min_pass_authority_score must be at least watch threshold")
        if self.max_conflicting_source_count_for_score <= ZERO:
            raise ValueError("max_conflicting_source_count_for_score must be positive")
        _reject_unsafe_public_payload("source authority config", self)
        require_paper_only_flags("source authority config", self)


@dataclass(frozen=True)
class StrategyCandidateResolutionSourceAuthorityV10Candidate:
    candidate_reference: str
    market_slug: str
    event_title: str
    official_source_available: bool
    source_hierarchy_confidence: Decimal
    conflicting_source_count: Decimal
    rule_specificity: Decimal
    adjudication_dependency: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateResolutionSourceAuthorityV10Candidate:
            raise ValueError(
                "candidate must be a StrategyCandidateResolutionSourceAuthorityV10Candidate",
            )
        _require_identifier("candidate_reference", self.candidate_reference)
        _require_identifier("market_slug", self.market_slug)
        _require_public_text("event_title", self.event_title)
        if type(self.official_source_available) is not bool:
            raise ValueError("official_source_available must be a bool")
        for field_name in (
            "source_hierarchy_confidence",
            "rule_specificity",
            "adjudication_dependency",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "conflicting_source_count",
            _normalize_whole_nonnegative_decimal(
                "conflicting_source_count",
                self.conflicting_source_count,
            ),
        )
        _reject_unsafe_public_payload("source authority candidate", self)
        require_paper_only_flags("source authority candidate", self)


@dataclass(frozen=True)
class StrategyCandidateResolutionSourceAuthorityV10Result:
    redacted_candidate_reference: str
    market_slug: str
    event_title: str
    official_source_available: bool
    source_hierarchy_confidence: Decimal
    conflicting_source_count: Decimal
    rule_specificity: Decimal
    adjudication_dependency: Decimal
    conflict_penalty: Decimal
    authority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    max_conflicting_source_count_for_score: Decimal = Decimal("5.000000")
    result_sha256: str = ""
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateResolutionSourceAuthorityV10Result:
            raise ValueError("result must be a StrategyCandidateResolutionSourceAuthorityV10Result")
        _require_redacted_reference(
            "redacted_candidate_reference",
            self.redacted_candidate_reference,
        )
        _require_identifier("market_slug", self.market_slug)
        _require_public_text("event_title", self.event_title)
        if type(self.official_source_available) is not bool:
            raise ValueError("official_source_available must be a bool")
        for field_name in (
            "source_hierarchy_confidence",
            "rule_specificity",
            "adjudication_dependency",
            "conflict_penalty",
            "authority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "conflicting_source_count",
            _normalize_whole_nonnegative_decimal(
                "conflicting_source_count",
                self.conflicting_source_count,
            ),
        )
        object.__setattr__(
            self,
            "max_conflicting_source_count_for_score",
            _normalize_whole_nonnegative_decimal(
                "max_conflicting_source_count_for_score",
                self.max_conflicting_source_count_for_score,
            ),
        )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _reject_unsafe_public_payload("source authority result", self)
        require_paper_only_flags("source authority result", self)
        if self.result_sha256 == "":
            object.__setattr__(self, "result_sha256", _result_sha256(self))
        else:
            object.__setattr__(
                self,
                "result_sha256",
                _normalize_sha256("result_sha256", self.result_sha256),
            )
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _result_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_result(self)


@dataclass(frozen=True)
class StrategyCandidateResolutionSourceAuthorityV10Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    min_authority_score: Decimal
    max_authority_score: Decimal
    average_authority_score: Decimal
    max_conflicting_source_count: Decimal
    max_adjudication_dependency: Decimal
    status: str
    reason_codes: tuple[str, ...]
    results: tuple[StrategyCandidateResolutionSourceAuthorityV10Result, ...]
    report_sha256: str = ""
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateResolutionSourceAuthorityV10Report:
            raise ValueError("report must be a StrategyCandidateResolutionSourceAuthorityV10Report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_identifier("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_conflicting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_whole_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_authority_score",
            "max_authority_score",
            "average_authority_score",
            "max_adjudication_dependency",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        if type(self.results) is not tuple:
            raise ValueError("results must be a tuple")
        for result in self.results:
            if type(result) is not StrategyCandidateResolutionSourceAuthorityV10Result:
                raise ValueError(
                    "results must contain StrategyCandidateResolutionSourceAuthorityV10Result",
                )
            require_paper_only_flags("source authority result", result)
        _reject_unsafe_public_payload("source authority report", self)
        require_paper_only_flags("source authority report", self)
        if self.report_sha256 == "":
            object.__setattr__(self, "report_sha256", _report_sha256(self))
        else:
            object.__setattr__(
                self,
                "report_sha256",
                _normalize_sha256("report_sha256", self.report_sha256),
            )
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)


def build_strategy_candidate_resolution_source_authority_v10(
    candidates: object,
    *,
    config: StrategyCandidateResolutionSourceAuthorityV10Config,
    generated_at: datetime,
) -> StrategyCandidateResolutionSourceAuthorityV10Report:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable of source authority candidates")
    try:
        candidate_rows = tuple(candidates)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "candidates must be an iterable of source authority candidates",
        ) from exc
    if type(config) is not StrategyCandidateResolutionSourceAuthorityV10Config:
        raise ValueError("config must be a StrategyCandidateResolutionSourceAuthorityV10Config")
    generated_at_utc = _as_utc("generated_at", generated_at)
    _reject_unsafe_public_payload("source authority config", config)
    require_paper_only_flags("source authority config", config)

    seen_references: set[str] = set()
    results: list[StrategyCandidateResolutionSourceAuthorityV10Result] = []
    for candidate in candidate_rows:
        if type(candidate) is not StrategyCandidateResolutionSourceAuthorityV10Candidate:
            raise ValueError(
                "candidates must contain StrategyCandidateResolutionSourceAuthorityV10Candidate",
            )
        _reject_unsafe_public_payload("source authority candidate", candidate)
        require_paper_only_flags("source authority candidate", candidate)
        if candidate.candidate_reference in seen_references:
            raise ValueError("duplicate candidate_reference")
        seen_references.add(candidate.candidate_reference)
        results.append(_build_result(candidate, config=config))

    sorted_results = tuple(
        sorted(
            results,
            key=lambda result: (
                result.authority_score,
                result.market_slug,
                result.redacted_candidate_reference,
            ),
        ),
    )
    return StrategyCandidateResolutionSourceAuthorityV10Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count_decimal(len(sorted_results)),
        pass_count=_count_decimal(
            sum(1 for result in sorted_results if result.status == "pass"),
        ),
        watch_count=_count_decimal(
            sum(1 for result in sorted_results if result.status == "watch"),
        ),
        block_count=_count_decimal(
            sum(1 for result in sorted_results if result.status == "block"),
        ),
        min_authority_score=_min_authority_score(sorted_results),
        max_authority_score=_max_authority_score(sorted_results),
        average_authority_score=_average_authority_score(sorted_results),
        max_conflicting_source_count=_max_conflicting_source_count(sorted_results),
        max_adjudication_dependency=_max_adjudication_dependency(sorted_results),
        status=_report_status(sorted_results),
        reason_codes=_report_reason_codes(sorted_results),
        results=sorted_results,
    )


def validate_strategy_candidate_resolution_source_authority_v10_report(
    report: StrategyCandidateResolutionSourceAuthorityV10Report,
) -> bool:
    if type(report) is not StrategyCandidateResolutionSourceAuthorityV10Report:
        raise ValueError("report must be a StrategyCandidateResolutionSourceAuthorityV10Report")
    _reject_unsafe_public_payload("source authority report", report)
    require_paper_only_flags("source authority report", report)
    _validate_report(report)
    return True


def validate_strategy_candidate_resolution_source_authority_v10_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("source authority public payload", payload)
    _require_public_payload_flags(payload)
    return True


def strategy_candidate_resolution_source_authority_v10_payload(
    report: StrategyCandidateResolutionSourceAuthorityV10Report,
) -> dict[str, Any]:
    if type(report) is not StrategyCandidateResolutionSourceAuthorityV10Report:
        raise ValueError("report must be a StrategyCandidateResolutionSourceAuthorityV10Report")
    validate_strategy_candidate_resolution_source_authority_v10_report(report)
    payload = json_ready_no_floats(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_strategy_candidate_resolution_source_authority_v10_public_payload(payload)
    return payload


def _build_result(
    candidate: StrategyCandidateResolutionSourceAuthorityV10Candidate,
    *,
    config: StrategyCandidateResolutionSourceAuthorityV10Config,
) -> StrategyCandidateResolutionSourceAuthorityV10Result:
    conflict_penalty = _conflict_penalty(
        candidate.conflicting_source_count,
        config.max_conflicting_source_count_for_score,
    )
    authority_score = _authority_score(
        official_source_available=candidate.official_source_available,
        source_hierarchy_confidence=candidate.source_hierarchy_confidence,
        conflict_penalty=conflict_penalty,
        rule_specificity=candidate.rule_specificity,
        adjudication_dependency=candidate.adjudication_dependency,
    )
    reason_codes = _candidate_reason_codes(
        candidate,
        authority_score=authority_score,
        config=config,
    )
    return StrategyCandidateResolutionSourceAuthorityV10Result(
        redacted_candidate_reference=_redacted_candidate_reference(
            candidate.candidate_reference,
        ),
        market_slug=candidate.market_slug,
        event_title=candidate.event_title,
        official_source_available=candidate.official_source_available,
        source_hierarchy_confidence=candidate.source_hierarchy_confidence,
        conflicting_source_count=candidate.conflicting_source_count,
        rule_specificity=candidate.rule_specificity,
        adjudication_dependency=candidate.adjudication_dependency,
        conflict_penalty=conflict_penalty,
        authority_score=authority_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        max_conflicting_source_count_for_score=config.max_conflicting_source_count_for_score,
    )


def _candidate_reason_codes(
    candidate: StrategyCandidateResolutionSourceAuthorityV10Candidate,
    *,
    authority_score: Decimal,
    config: StrategyCandidateResolutionSourceAuthorityV10Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if not candidate.official_source_available:
        reason_codes.append("official_resolution_source_missing")
    if candidate.source_hierarchy_confidence < config.min_watch_source_hierarchy_confidence:
        reason_codes.append("source_hierarchy_confidence_block")
    elif candidate.source_hierarchy_confidence < config.min_pass_source_hierarchy_confidence:
        reason_codes.append("source_hierarchy_confidence_watch")
    if candidate.conflicting_source_count > config.max_watch_conflicting_source_count:
        reason_codes.append("conflicting_sources_block")
    elif candidate.conflicting_source_count > config.max_pass_conflicting_source_count:
        reason_codes.append("conflicting_sources_watch")
    if candidate.rule_specificity < config.min_watch_rule_specificity:
        reason_codes.append("resolution_rule_specificity_block")
    elif candidate.rule_specificity < config.min_pass_rule_specificity:
        reason_codes.append("resolution_rule_specificity_watch")
    if candidate.adjudication_dependency > config.max_watch_adjudication_dependency:
        reason_codes.append("adjudication_dependency_block")
    elif candidate.adjudication_dependency > config.max_pass_adjudication_dependency:
        reason_codes.append("adjudication_dependency_watch")
    if authority_score < config.min_watch_authority_score:
        reason_codes.append("authority_score_block")
    elif authority_score < config.min_pass_authority_score:
        reason_codes.append("authority_score_watch")
    if not reason_codes:
        return ("resolution_source_authority_pass",)
    return tuple(reason_codes)


def _conflict_penalty(
    conflicting_source_count: Decimal,
    max_conflicting_source_count_for_score: Decimal,
) -> Decimal:
    if max_conflicting_source_count_for_score <= ZERO:
        raise ValueError("max_conflicting_source_count_for_score must be positive")
    with localcontext(DECIMAL_CONTEXT):
        raw_penalty = conflicting_source_count / max_conflicting_source_count_for_score
    return _bounded_probability(raw_penalty)


def _authority_score(
    *,
    official_source_available: bool,
    source_hierarchy_confidence: Decimal,
    conflict_penalty: Decimal,
    rule_specificity: Decimal,
    adjudication_dependency: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        official_component = (
            OFFICIAL_SOURCE_AVAILABLE_WEIGHT if official_source_available else ZERO
        )
        raw_score = (
            (source_hierarchy_confidence * SOURCE_HIERARCHY_WEIGHT)
            + (rule_specificity * RULE_SPECIFICITY_WEIGHT)
            + ((ONE - adjudication_dependency) * ADJUDICATION_INDEPENDENCE_WEIGHT)
            + ((ONE - conflict_penalty) * CONFLICT_QUALITY_WEIGHT)
            + official_component
            - BASELINE_SOURCE_RISK_OFFSET
        )
    return _bounded_probability(raw_score)


def _validate_result(result: StrategyCandidateResolutionSourceAuthorityV10Result) -> None:
    expected_conflict_penalty = _conflict_penalty(
        result.conflicting_source_count,
        result.max_conflicting_source_count_for_score,
    )
    expected_authority_score = _authority_score(
        official_source_available=result.official_source_available,
        source_hierarchy_confidence=result.source_hierarchy_confidence,
        conflict_penalty=expected_conflict_penalty,
        rule_specificity=result.rule_specificity,
        adjudication_dependency=result.adjudication_dependency,
    )
    if result.conflict_penalty != expected_conflict_penalty:
        raise ValueError("conflict_penalty must match candidate fields")
    if result.authority_score != expected_authority_score:
        raise ValueError("authority_score must match candidate fields")
    if result.status != _status_from_reason_codes(result.reason_codes):
        raise ValueError("status must match reason_codes")
    if result.result_sha256 != _result_sha256(result):
        raise ValueError("result_sha256 must match result fields")
    if result.derived_validation_digest != _result_derived_validation_digest(result):
        raise ValueError("derived_validation_digest must match result fields")


def _validate_report(report: StrategyCandidateResolutionSourceAuthorityV10Report) -> None:
    results = report.results
    if report.candidate_count != _count_decimal(len(results)):
        raise ValueError("candidate_count must match results")
    if report.pass_count != _count_decimal(sum(1 for result in results if result.status == "pass")):
        raise ValueError("pass_count must match results")
    if report.watch_count != _count_decimal(
        sum(1 for result in results if result.status == "watch"),
    ):
        raise ValueError("watch_count must match results")
    if report.block_count != _count_decimal(
        sum(1 for result in results if result.status == "block"),
    ):
        raise ValueError("block_count must match results")
    if report.min_authority_score != _min_authority_score(results):
        raise ValueError("min_authority_score must match results")
    if report.max_authority_score != _max_authority_score(results):
        raise ValueError("max_authority_score must match results")
    if report.average_authority_score != _average_authority_score(results):
        raise ValueError("average_authority_score must match results")
    if report.max_conflicting_source_count != _max_conflicting_source_count(results):
        raise ValueError("max_conflicting_source_count must match results")
    if report.max_adjudication_dependency != _max_adjudication_dependency(results):
        raise ValueError("max_adjudication_dependency must match results")
    if report.status != _report_status(results):
        raise ValueError("status must match results")
    if report.reason_codes != _report_reason_codes(results):
        raise ValueError("reason_codes must match results")
    if report.report_sha256 != _report_sha256(report):
        raise ValueError("report_sha256 must match report fields")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("resolution_source_authority_pass",):
        return "pass"
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    raise ValueError("reason_codes must imply a supported status")


def _report_status(
    results: tuple[StrategyCandidateResolutionSourceAuthorityV10Result, ...],
) -> str:
    if not results:
        return "block"
    if any(result.status == "block" for result in results):
        return "block"
    if any(result.status == "watch" for result in results):
        return "watch"
    return "pass"


def _report_reason_codes(
    results: tuple[StrategyCandidateResolutionSourceAuthorityV10Result, ...],
) -> tuple[str, ...]:
    if not results:
        return ("resolution_source_authority_empty",)
    aggregated: list[str] = []
    result_reason_codes = {
        reason_code for result in results for reason_code in result.reason_codes
    }
    for reason_code in REPORT_REASON_CODE_SEQUENCE:
        if reason_code in result_reason_codes:
            aggregated.append(reason_code)
    if not aggregated:
        return ("resolution_source_authority_pass",)
    return tuple(aggregated)


def _min_authority_score(
    results: tuple[StrategyCandidateResolutionSourceAuthorityV10Result, ...],
) -> Decimal:
    if not results:
        return ZERO
    return min(result.authority_score for result in results)


def _max_authority_score(
    results: tuple[StrategyCandidateResolutionSourceAuthorityV10Result, ...],
) -> Decimal:
    if not results:
        return ZERO
    return max(result.authority_score for result in results)


def _average_authority_score(
    results: tuple[StrategyCandidateResolutionSourceAuthorityV10Result, ...],
) -> Decimal:
    if not results:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _q(
            sum((result.authority_score for result in results), ZERO)
            / _count_decimal(len(results)),
        )


def _max_conflicting_source_count(
    results: tuple[StrategyCandidateResolutionSourceAuthorityV10Result, ...],
) -> Decimal:
    if not results:
        return ZERO
    return max(result.conflicting_source_count for result in results)


def _max_adjudication_dependency(
    results: tuple[StrategyCandidateResolutionSourceAuthorityV10Result, ...],
) -> Decimal:
    if not results:
        return ZERO
    return max(result.adjudication_dependency for result in results)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_whole_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.quantize(COUNT_QUANT):
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        if isinstance(value, Decimal):
            raise ValueError(f"{field_name} must be an exact Decimal")
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _q(value)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(SCORE_QUANT)


def _bounded_probability(value: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO
    if value >= ONE:
        return ONE
    return _q(value)


def _q(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SCORE_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not allow_empty and not values:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")
    for value in values:
        _require_member(field_name, value, RESULT_REASON_CODES)
    return values


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values!r}")


def _require_identifier(field_name: str, value: object) -> None:
    _require_public_text(field_name, value)
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_redacted_reference(field_name: str, value: object) -> None:
    _require_identifier(field_name, value)
    if not value.startswith("candidate_ref_"):
        raise ValueError(f"{field_name} must be redacted")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or value.lower() != value:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest") from exc
    return value


def _redacted_candidate_reference(candidate_reference: str) -> str:
    return f"candidate_ref_{hashlib.sha256(candidate_reference.encode('utf-8')).hexdigest()[:16]}"


def _result_sha256(result: StrategyCandidateResolutionSourceAuthorityV10Result) -> str:
    return _sha256(
        "result",
        (
            f"redacted_candidate_reference={result.redacted_candidate_reference}",
            f"market_slug={result.market_slug}",
            f"event_title={result.event_title}",
            f"official_source_available={result.official_source_available}",
            f"source_hierarchy_confidence={result.source_hierarchy_confidence}",
            f"conflicting_source_count={result.conflicting_source_count}",
            f"rule_specificity={result.rule_specificity}",
            f"adjudication_dependency={result.adjudication_dependency}",
            f"conflict_penalty={result.conflict_penalty}",
            f"authority_score={result.authority_score}",
            f"status={result.status}",
            f"reason_codes={_digest_tuple(result.reason_codes)}",
            "max_conflicting_source_count_for_score="
            f"{result.max_conflicting_source_count_for_score}",
            f"paper_only={result.paper_only}",
            f"report_only={result.report_only}",
            f"readonly={result.readonly}",
        ),
    )


def _result_derived_validation_digest(
    result: StrategyCandidateResolutionSourceAuthorityV10Result,
) -> str:
    return _sha256(
        "result_derived",
        (
            f"conflict_penalty={result.conflict_penalty}",
            f"authority_score={result.authority_score}",
            f"status={result.status}",
            f"reason_codes={_digest_tuple(result.reason_codes)}",
            f"result_sha256={result.result_sha256}",
            f"paper_only={result.paper_only}",
            f"report_only={result.report_only}",
            f"readonly={result.readonly}",
        ),
    )


def _report_sha256(report: StrategyCandidateResolutionSourceAuthorityV10Report) -> str:
    return _sha256(
        "report",
        (
            f"generated_at={report.generated_at.isoformat()}",
            f"config_version={report.config_version}",
            f"candidate_count={report.candidate_count}",
            f"pass_count={report.pass_count}",
            f"watch_count={report.watch_count}",
            f"block_count={report.block_count}",
            f"min_authority_score={report.min_authority_score}",
            f"max_authority_score={report.max_authority_score}",
            f"average_authority_score={report.average_authority_score}",
            f"max_conflicting_source_count={report.max_conflicting_source_count}",
            f"max_adjudication_dependency={report.max_adjudication_dependency}",
            f"status={report.status}",
            f"reason_codes={_digest_tuple(report.reason_codes)}",
            f"results={_digest_tuple(tuple(result.result_sha256 for result in report.results))}",
            f"paper_only={report.paper_only}",
            f"report_only={report.report_only}",
            f"readonly={report.readonly}",
        ),
    )


def _report_derived_validation_digest(
    report: StrategyCandidateResolutionSourceAuthorityV10Report,
) -> str:
    return _sha256(
        "report_derived",
        (
            f"candidate_count={report.candidate_count}",
            f"pass_count={report.pass_count}",
            f"watch_count={report.watch_count}",
            f"block_count={report.block_count}",
            f"min_authority_score={report.min_authority_score}",
            f"max_authority_score={report.max_authority_score}",
            f"average_authority_score={report.average_authority_score}",
            f"status={report.status}",
            f"reason_codes={_digest_tuple(report.reason_codes)}",
            "result_derived_validation_digest="
            f"{_digest_tuple(tuple(result.derived_validation_digest for result in report.results))}",
            f"report_sha256={report.report_sha256}",
            f"paper_only={report.paper_only}",
            f"report_only={report.report_only}",
            f"readonly={report.readonly}",
        ),
    )


def _sha256(label: str, values: tuple[str, ...]) -> str:
    return hashlib.sha256((f"{label}|" + "|".join(values)).encode("utf-8")).hexdigest()


def _digest_tuple(values: tuple[str, ...]) -> str:
    return ",".join(values)


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    for key in _payload_keys(payload):
        if _is_unsafe_public_payload_key(key):
            raise ValueError(f"unsafe live surface field in {label}: {key}")


def _is_unsafe_public_payload_key(key: str) -> bool:
    normalized_key = key.lower()
    if any(fragment in normalized_key for fragment in UNSAFE_PUBLIC_PAYLOAD_KEY_FRAGMENTS):
        return True
    tokens = _surface_key_tokens(normalized_key)
    return any(token in tokens for token in UNSAFE_PUBLIC_PAYLOAD_KEY_TOKENS)


def _surface_key_tokens(key: str) -> tuple[str, ...]:
    tokens: list[str] = []
    current: list[str] = []
    for character in key:
        if ("a" <= character <= "z") or ("0" <= character <= "9"):
            current.append(character)
            continue
        if current:
            tokens.append("".join(current))
            current = []
    if current:
        tokens.append("".join(current))
    return tuple(tokens)


def _payload_keys(value: object) -> tuple[str, ...]:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_keys(asdict(value))
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            keys.append(key)
            keys.extend(_payload_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_payload_keys(item))
        return tuple(keys)
    return ()


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True in public payload")
    results = payload.get("results")
    if not isinstance(results, list):
        raise ValueError("public payload results must be a list")
    for result in results:
        if not isinstance(result, dict):
            raise ValueError("public payload results must contain dict rows")
        for field_name in ("paper_only", "report_only", "readonly"):
            if result.get(field_name) is not True:
                raise ValueError(f"{field_name} must be True in public payload result")


__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_RESOLUTION_SOURCE_AUTHORITY_V10_CONFIG_VERSION",
    "StrategyCandidateResolutionSourceAuthorityV10Candidate",
    "StrategyCandidateResolutionSourceAuthorityV10Config",
    "StrategyCandidateResolutionSourceAuthorityV10Report",
    "StrategyCandidateResolutionSourceAuthorityV10Result",
    "build_strategy_candidate_resolution_source_authority_v10",
    "strategy_candidate_resolution_source_authority_v10_payload",
    "validate_strategy_candidate_resolution_source_authority_v10_public_payload",
    "validate_strategy_candidate_resolution_source_authority_v10_report",
)
