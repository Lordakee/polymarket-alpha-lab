"""Pure report-only diagnostics for strategy market question specificity risk."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


DEFAULT_STRATEGY_MARKET_QUESTION_SPECIFICITY_RISK_DIGEST_CONFIG_VERSION = (
    "strategy-market-question-specificity-risk-digest-v0"
)

PASS_REASON = "strategy_market_question_specificity_risk_passed"
EMPTY_REASON = "strategy_market_question_specificity_risk_empty_findings"
RULE_UNCLEAR_REASON = "strategy_market_question_specificity_risk_rule_unclear"
ENDPOINT_NOT_MEASURABLE_REASON = (
    "strategy_market_question_specificity_risk_endpoint_not_measurable"
)
DEADLINE_UNCLEAR_REASON = "strategy_market_question_specificity_risk_deadline_unclear"
AMBIGUOUS_TERMS_REASON = "strategy_market_question_specificity_risk_ambiguous_terms"
SOURCES_PARTIAL_REASON = "strategy_market_question_specificity_risk_sources_partial"

SPECIFICITY_RISK_REASON_CODES = (
    PASS_REASON,
    EMPTY_REASON,
    RULE_UNCLEAR_REASON,
    ENDPOINT_NOT_MEASURABLE_REASON,
    DEADLINE_UNCLEAR_REASON,
    AMBIGUOUS_TERMS_REASON,
    SOURCES_PARTIAL_REASON,
)
SPECIFICITY_RISK_STATUSES = ("pass", "watch", "blocked")
NEXT_STEPS = {
    "pass": "allow_report_only_strategy_question_specificity_diagnostics",
    "watch": "review_report_only_strategy_question_specificity_sources",
    "blocked": "block_report_only_strategy_question_specificity_diagnostics",
}
ZERO_DECIMAL = Decimal("0.000000")
ONE_DECIMAL = Decimal("1.000000")
TWO_DECIMAL = Decimal("2.000000")
SIX_PLACES = Decimal("0.000001")
REDACTED_MARKERS = ("redacted", "anon", "masked", "synthetic", "sample")
SENSITIVE_MARKERS = ("0x", "@", "email", "key", "secret", "acc" + "ount")
UNSAFE_MARKERS = (
    "li" + "ve",
    "au" + "th",
    "wal" + "let",
    "or" + "der",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
)


__all__ = (
    "DEFAULT_STRATEGY_MARKET_QUESTION_SPECIFICITY_RISK_DIGEST_CONFIG_VERSION",
    "StrategyMarketQuestionSpecificityRiskDigestConfig",
    "StrategyMarketQuestionSpecificityRiskDigestReasonCodeCount",
    "StrategyMarketQuestionSpecificityRiskDigestReport",
    "StrategyMarketQuestionSpecificityRiskFinding",
    "build_strategy_market_question_specificity_risk_digest",
    "strategy_market_question_specificity_risk_digest_payload",
)


@dataclass(frozen=True)
class StrategyMarketQuestionSpecificityRiskDigestConfig:
    config_version: str = (
        DEFAULT_STRATEGY_MARKET_QUESTION_SPECIFICITY_RISK_DIGEST_CONFIG_VERSION
    )
    min_rule_clarity_score: Decimal = Decimal("0.700000")
    min_measurable_endpoint_coverage_ratio: Decimal = Decimal("0.750000")
    min_deadline_clarity_score: Decimal = Decimal("0.800000")
    max_ambiguous_term_count: Decimal = Decimal("1.000000")
    min_source_coverage_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyMarketQuestionSpecificityRiskDigestConfig:
            raise ValueError(
                "config must be exactly "
                "StrategyMarketQuestionSpecificityRiskDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        _require_no_unsafe_surface("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_rule_clarity_score",
            _require_ratio("min_rule_clarity_score", self.min_rule_clarity_score),
        )
        object.__setattr__(
            self,
            "min_measurable_endpoint_coverage_ratio",
            _require_ratio(
                "min_measurable_endpoint_coverage_ratio",
                self.min_measurable_endpoint_coverage_ratio,
            ),
        )
        object.__setattr__(
            self,
            "min_deadline_clarity_score",
            _require_ratio("min_deadline_clarity_score", self.min_deadline_clarity_score),
        )
        object.__setattr__(
            self,
            "max_ambiguous_term_count",
            _require_nonnegative_count_decimal(
                "max_ambiguous_term_count",
                self.max_ambiguous_term_count,
            ),
        )
        object.__setattr__(
            self,
            "min_source_coverage_ratio",
            _require_ratio("min_source_coverage_ratio", self.min_source_coverage_ratio),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyMarketQuestionSpecificityRiskFinding:
    strategy_reference: str
    market_reference: str
    rule_clarity_score: Decimal
    measurable_endpoint_coverage_ratio: Decimal
    deadline_clarity_score: Decimal
    ambiguous_term_count: Decimal
    source_mapping: tuple[tuple[str, str], ...]
    source_config_version: str
    specificity_risk_status: str | None = None
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyMarketQuestionSpecificityRiskFinding:
            raise ValueError(
                "finding must be exactly StrategyMarketQuestionSpecificityRiskFinding",
            )
        _require_canonical_string("strategy_reference", self.strategy_reference)
        _require_redacted_reference("strategy_reference", self.strategy_reference)
        _require_no_unsafe_surface("strategy_reference", self.strategy_reference)
        _require_canonical_string("market_reference", self.market_reference)
        _require_redacted_reference("market_reference", self.market_reference)
        _require_no_unsafe_surface("market_reference", self.market_reference)
        object.__setattr__(
            self,
            "rule_clarity_score",
            _require_ratio("rule_clarity_score", self.rule_clarity_score),
        )
        object.__setattr__(
            self,
            "measurable_endpoint_coverage_ratio",
            _require_ratio(
                "measurable_endpoint_coverage_ratio",
                self.measurable_endpoint_coverage_ratio,
            ),
        )
        object.__setattr__(
            self,
            "deadline_clarity_score",
            _require_ratio("deadline_clarity_score", self.deadline_clarity_score),
        )
        object.__setattr__(
            self,
            "ambiguous_term_count",
            _require_nonnegative_count_decimal(
                "ambiguous_term_count",
                self.ambiguous_term_count,
            ),
        )
        object.__setattr__(
            self,
            "source_mapping",
            _normalize_source_mapping(self.source_mapping),
        )
        _require_canonical_string("source_config_version", self.source_config_version)
        _require_no_sensitive_marker("source_config_version", self.source_config_version)
        _require_no_unsafe_surface("source_config_version", self.source_config_version)
        if self.specificity_risk_status is not None:
            _require_status("specificity_risk_status", self.specificity_risk_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _validate_finding_consistency(self)
        _require_hard_flags("finding", self)


@dataclass(frozen=True)
class StrategyMarketQuestionSpecificityRiskDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyMarketQuestionSpecificityRiskDigestReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "StrategyMarketQuestionSpecificityRiskDigestReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class StrategyMarketQuestionSpecificityRiskDigestReport:
    generated_at: datetime
    config_version: str
    specificity_risk_status: str
    recommended_next_step: str
    finding_count: Decimal
    pass_finding_count: Decimal
    watch_finding_count: Decimal
    blocked_finding_count: Decimal
    average_rule_clarity_score: Decimal
    average_measurable_endpoint_coverage_ratio: Decimal
    average_deadline_clarity_score: Decimal
    total_ambiguous_term_count: Decimal
    source_coverage_ratio: Decimal
    findings: tuple[StrategyMarketQuestionSpecificityRiskFinding, ...]
    source_config_versions: tuple[tuple[str, str, str], ...]
    reason_code_counts: tuple[
        StrategyMarketQuestionSpecificityRiskDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    readiness_gap_count: Decimal = ZERO_DECIMAL
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyMarketQuestionSpecificityRiskDigestReport:
            raise ValueError(
                "report must be exactly StrategyMarketQuestionSpecificityRiskDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_no_unsafe_surface("config_version", self.config_version)
        _require_status("specificity_risk_status", self.specificity_risk_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "finding_count",
            "pass_finding_count",
            "watch_finding_count",
            "blocked_finding_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_rule_clarity_score",
            _require_ratio(
                "average_rule_clarity_score",
                self.average_rule_clarity_score,
            ),
        )
        object.__setattr__(
            self,
            "average_measurable_endpoint_coverage_ratio",
            _require_ratio(
                "average_measurable_endpoint_coverage_ratio",
                self.average_measurable_endpoint_coverage_ratio,
            ),
        )
        object.__setattr__(
            self,
            "average_deadline_clarity_score",
            _require_ratio(
                "average_deadline_clarity_score",
                self.average_deadline_clarity_score,
            ),
        )
        object.__setattr__(
            self,
            "total_ambiguous_term_count",
            _require_nonnegative_count_decimal(
                "total_ambiguous_term_count",
                self.total_ambiguous_term_count,
            ),
        )
        object.__setattr__(
            self,
            "source_coverage_ratio",
            _require_ratio("source_coverage_ratio", self.source_coverage_ratio),
        )
        object.__setattr__(self, "findings", _normalize_findings(self.findings))
        object.__setattr__(
            self,
            "source_config_versions",
            _normalize_source_config_versions(self.source_config_versions),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "readiness_gap_count",
            _require_nonnegative_count_decimal(
                "readiness_gap_count",
                self.readiness_gap_count,
            ),
        )
        _require_canonical_string(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_strategy_market_question_specificity_risk_digest(
    findings: list[StrategyMarketQuestionSpecificityRiskFinding]
    | tuple[StrategyMarketQuestionSpecificityRiskFinding, ...],
    *,
    config: StrategyMarketQuestionSpecificityRiskDigestConfig,
    generated_at: datetime,
) -> StrategyMarketQuestionSpecificityRiskDigestReport:
    if type(config) is not StrategyMarketQuestionSpecificityRiskDigestConfig:
        raise ValueError(
            "config must be a StrategyMarketQuestionSpecificityRiskDigestConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_findings = _normalize_input_findings(findings)
    evaluated_findings = tuple(
        sorted(
            (
                _evaluate_finding(finding, config=config)
                for finding in normalized_findings
            ),
            key=lambda row: (row.strategy_reference, row.market_reference),
        )
    )
    reason_codes = _report_reason_codes(evaluated_findings)
    specificity_risk_status = _report_status(evaluated_findings, reason_codes)
    finding_count = _count_decimal(len(evaluated_findings))
    pass_finding_count = _count_matching(evaluated_findings, "pass")
    watch_finding_count = _count_matching(evaluated_findings, "watch")
    blocked_finding_count = _count_matching(evaluated_findings, "blocked")
    readiness_gap_count = sum(
        (_readiness_gap_count(row) for row in evaluated_findings),
        ZERO_DECIMAL,
    ).quantize(SIX_PLACES)

    return StrategyMarketQuestionSpecificityRiskDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        specificity_risk_status=specificity_risk_status,
        recommended_next_step=NEXT_STEPS[specificity_risk_status],
        finding_count=finding_count,
        pass_finding_count=pass_finding_count,
        watch_finding_count=watch_finding_count,
        blocked_finding_count=blocked_finding_count,
        average_rule_clarity_score=_average(
            tuple(row.rule_clarity_score for row in evaluated_findings),
        ),
        average_measurable_endpoint_coverage_ratio=_average(
            tuple(
                row.measurable_endpoint_coverage_ratio
                for row in evaluated_findings
            ),
        ),
        average_deadline_clarity_score=_average(
            tuple(row.deadline_clarity_score for row in evaluated_findings),
        ),
        total_ambiguous_term_count=sum(
            (row.ambiguous_term_count for row in evaluated_findings),
            ZERO_DECIMAL,
        ).quantize(SIX_PLACES),
        source_coverage_ratio=_average(
            tuple(_source_coverage_ratio(row) for row in evaluated_findings),
        ),
        findings=evaluated_findings,
        source_config_versions=_source_config_versions(evaluated_findings),
        reason_code_counts=_reason_code_counts_for_findings(evaluated_findings),
        reason_codes=reason_codes,
        readiness_gap_count=readiness_gap_count,
        derived_validation_digest=_derived_validation_digest(
            specificity_risk_status=specificity_risk_status,
            finding_count=finding_count,
            blocked_finding_count=blocked_finding_count,
            watch_finding_count=watch_finding_count,
            pass_finding_count=pass_finding_count,
            readiness_gap_count=readiness_gap_count,
            reason_codes=reason_codes,
        ),
    )


def strategy_market_question_specificity_risk_digest_payload(
    report: StrategyMarketQuestionSpecificityRiskDigestReport,
) -> dict[str, object]:
    if type(report) is not StrategyMarketQuestionSpecificityRiskDigestReport:
        raise ValueError(
            "report must be a StrategyMarketQuestionSpecificityRiskDigestReport",
        )
    _require_hard_flags("report", report)
    _validate_report_consistency(report)
    return {
        "generated_at": _datetime_payload(report.generated_at),
        "config_version": report.config_version,
        "specificity_risk_status": report.specificity_risk_status,
        "recommended_next_step": report.recommended_next_step,
        "finding_count": _decimal_payload(report.finding_count),
        "pass_finding_count": _decimal_payload(report.pass_finding_count),
        "watch_finding_count": _decimal_payload(report.watch_finding_count),
        "blocked_finding_count": _decimal_payload(report.blocked_finding_count),
        "average_rule_clarity_score": _decimal_payload(report.average_rule_clarity_score),
        "average_measurable_endpoint_coverage_ratio": _decimal_payload(
            report.average_measurable_endpoint_coverage_ratio,
        ),
        "average_deadline_clarity_score": _decimal_payload(
            report.average_deadline_clarity_score,
        ),
        "total_ambiguous_term_count": _decimal_payload(
            report.total_ambiguous_term_count,
        ),
        "source_coverage_ratio": _decimal_payload(report.source_coverage_ratio),
        "findings": [_finding_payload(finding) for finding in report.findings],
        "source_config_versions": [
            [strategy_reference, market_reference, source_config_version]
            for (
                strategy_reference,
                market_reference,
                source_config_version,
            ) in report.source_config_versions
        ],
        "reason_code_counts": [
            _reason_code_count_payload(count) for count in report.reason_code_counts
        ],
        "reason_codes": list(report.reason_codes),
        "readiness_gap_count": _decimal_payload(report.readiness_gap_count),
        "derived_validation_digest": report.derived_validation_digest,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _finding_payload(
    finding: StrategyMarketQuestionSpecificityRiskFinding,
) -> dict[str, object]:
    if type(finding) is not StrategyMarketQuestionSpecificityRiskFinding:
        raise ValueError("finding must be a StrategyMarketQuestionSpecificityRiskFinding")
    _require_hard_flags("finding", finding)
    return {
        "strategy_reference": finding.strategy_reference,
        "market_reference": finding.market_reference,
        "rule_clarity_score": _decimal_payload(finding.rule_clarity_score),
        "measurable_endpoint_coverage_ratio": _decimal_payload(
            finding.measurable_endpoint_coverage_ratio,
        ),
        "deadline_clarity_score": _decimal_payload(finding.deadline_clarity_score),
        "ambiguous_term_count": _decimal_payload(finding.ambiguous_term_count),
        "source_mapping": [
            [source_role, source_reference]
            for source_role, source_reference in finding.source_mapping
        ],
        "source_config_version": finding.source_config_version,
        "specificity_risk_status": finding.specificity_risk_status,
        "reason_codes": list(finding.reason_codes),
        "paper_only": finding.paper_only,
        "report_only": finding.report_only,
        "readonly": finding.readonly,
    }


def _reason_code_count_payload(
    count: StrategyMarketQuestionSpecificityRiskDigestReasonCodeCount,
) -> dict[str, object]:
    if type(count) is not StrategyMarketQuestionSpecificityRiskDigestReasonCodeCount:
        raise ValueError(
            "reason_code_count must be a "
            "StrategyMarketQuestionSpecificityRiskDigestReasonCodeCount",
        )
    _require_hard_flags("reason_code_count", count)
    return {
        "reason_code": count.reason_code,
        "count": _decimal_payload(count.count),
        "paper_only": count.paper_only,
        "report_only": count.report_only,
        "readonly": count.readonly,
    }


def _datetime_payload(value: datetime) -> str:
    return _as_utc("generated_at", value).isoformat()


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload numeric values must be Decimal")
    return format(value, "f")


def _evaluate_finding(
    finding: StrategyMarketQuestionSpecificityRiskFinding,
    *,
    config: StrategyMarketQuestionSpecificityRiskDigestConfig,
) -> StrategyMarketQuestionSpecificityRiskFinding:
    reason_codes: list[str] = []
    if finding.rule_clarity_score < config.min_rule_clarity_score:
        reason_codes.append(RULE_UNCLEAR_REASON)
    if (
        finding.measurable_endpoint_coverage_ratio
        < config.min_measurable_endpoint_coverage_ratio
    ):
        reason_codes.append(ENDPOINT_NOT_MEASURABLE_REASON)
    if finding.deadline_clarity_score < config.min_deadline_clarity_score:
        reason_codes.append(DEADLINE_UNCLEAR_REASON)
    if finding.ambiguous_term_count > config.max_ambiguous_term_count:
        reason_codes.append(AMBIGUOUS_TERMS_REASON)
    if _source_coverage_ratio(finding) < config.min_source_coverage_ratio:
        reason_codes.append(SOURCES_PARTIAL_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    sorted_reason_codes = tuple(sorted(reason_codes))
    return StrategyMarketQuestionSpecificityRiskFinding(
        strategy_reference=finding.strategy_reference,
        market_reference=finding.market_reference,
        rule_clarity_score=finding.rule_clarity_score,
        measurable_endpoint_coverage_ratio=finding.measurable_endpoint_coverage_ratio,
        deadline_clarity_score=finding.deadline_clarity_score,
        ambiguous_term_count=finding.ambiguous_term_count,
        source_mapping=finding.source_mapping,
        source_config_version=finding.source_config_version,
        specificity_risk_status=_finding_status(sorted_reason_codes),
        reason_codes=sorted_reason_codes,
    )


def _finding_status(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code
        in (
            RULE_UNCLEAR_REASON,
            ENDPOINT_NOT_MEASURABLE_REASON,
            DEADLINE_UNCLEAR_REASON,
            AMBIGUOUS_TERMS_REASON,
            EMPTY_REASON,
        )
        for reason_code in reason_codes
    ):
        return "blocked"
    if reason_codes == (SOURCES_PARTIAL_REASON,):
        return "watch"
    if reason_codes == (PASS_REASON,):
        return "pass"
    raise ValueError("reason_codes must contain known specificity diagnostics")


def _report_status(
    findings: tuple[StrategyMarketQuestionSpecificityRiskFinding, ...],
    reason_codes: tuple[str, ...],
) -> str:
    if not findings:
        return "blocked"
    if any(row.specificity_risk_status == "blocked" for row in findings):
        return "blocked"
    if any(row.specificity_risk_status == "watch" for row in findings):
        return "watch"
    if reason_codes == (PASS_REASON,):
        return "pass"
    raise ValueError("findings must resolve to a known specificity risk status")


def _report_reason_codes(
    findings: tuple[StrategyMarketQuestionSpecificityRiskFinding, ...],
) -> tuple[str, ...]:
    if not findings:
        return (EMPTY_REASON,)
    reason_codes = tuple(
        reason_code
        for finding in findings
        for reason_code in finding.reason_codes
    )
    unique_reason_codes = sorted(set(reason_codes))
    if len(unique_reason_codes) > 1 and PASS_REASON in unique_reason_codes:
        unique_reason_codes.remove(PASS_REASON)
    return tuple(unique_reason_codes)


def _reason_code_counts_for_findings(
    findings: tuple[StrategyMarketQuestionSpecificityRiskFinding, ...],
) -> tuple[StrategyMarketQuestionSpecificityRiskDigestReasonCodeCount, ...]:
    reason_codes = tuple(
        reason_code
        for finding in findings
        for reason_code in finding.reason_codes
        if reason_code != PASS_REASON or finding.specificity_risk_status == "pass"
    )
    return _reason_code_counts(reason_codes or (EMPTY_REASON,))


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[StrategyMarketQuestionSpecificityRiskDigestReasonCodeCount, ...]:
    return tuple(
        StrategyMarketQuestionSpecificityRiskDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(sum(1 for item in reason_codes if item == reason_code)),
        )
        for reason_code in sorted(set(reason_codes))
    )


def _readiness_gap_count(
    finding: StrategyMarketQuestionSpecificityRiskFinding,
) -> Decimal:
    return _count_decimal(
        sum(1 for reason_code in finding.reason_codes if reason_code != PASS_REASON),
    )


def _count_matching(
    findings: tuple[StrategyMarketQuestionSpecificityRiskFinding, ...],
    status: str,
) -> Decimal:
    return _count_decimal(
        sum(1 for row in findings if row.specificity_risk_status == status),
    )


def _count_decimal(value: int) -> Decimal:
    if isinstance(value, bool) or type(value) is not int or value < 0:
        raise ValueError("internal count must be a nonnegative int")
    return Decimal(value).quantize(SIX_PLACES)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_DECIMAL
    return (sum(values, ZERO_DECIMAL) / Decimal(len(values))).quantize(SIX_PLACES)


def _source_coverage_ratio(
    finding: StrategyMarketQuestionSpecificityRiskFinding,
) -> Decimal:
    if not finding.source_mapping:
        return ZERO_DECIMAL
    observed_source_count = sum(
        1 for _, source_reference in finding.source_mapping if source_reference
    )
    return (Decimal(observed_source_count) / TWO_DECIMAL).quantize(SIX_PLACES)


def _source_config_versions(
    findings: tuple[StrategyMarketQuestionSpecificityRiskFinding, ...],
) -> tuple[tuple[str, str, str], ...]:
    return tuple(
        sorted(
            (
                row.strategy_reference,
                row.market_reference,
                row.source_config_version,
            )
            for row in findings
        )
    )


def _normalize_input_findings(
    findings: list[StrategyMarketQuestionSpecificityRiskFinding]
    | tuple[StrategyMarketQuestionSpecificityRiskFinding, ...],
) -> tuple[StrategyMarketQuestionSpecificityRiskFinding, ...]:
    if type(findings) not in (list, tuple):
        raise ValueError("findings must be a list or tuple")
    normalized_findings = tuple(findings)
    seen_pairs: set[tuple[str, str]] = set()
    for finding in normalized_findings:
        if type(finding) is not StrategyMarketQuestionSpecificityRiskFinding:
            raise ValueError(
                "findings must contain StrategyMarketQuestionSpecificityRiskFinding",
            )
        _require_hard_flags("finding", finding)
        pair = (finding.strategy_reference, finding.market_reference)
        if pair in seen_pairs:
            raise ValueError("strategy/market pairs must be unique")
        seen_pairs.add(pair)
    return normalized_findings


def _normalize_findings(
    findings: tuple[StrategyMarketQuestionSpecificityRiskFinding, ...],
) -> tuple[StrategyMarketQuestionSpecificityRiskFinding, ...]:
    if type(findings) not in (list, tuple):
        raise ValueError("findings must be a list or tuple")
    normalized_findings = tuple(findings)
    seen_pairs: set[tuple[str, str]] = set()
    for finding in normalized_findings:
        if type(finding) is not StrategyMarketQuestionSpecificityRiskFinding:
            raise ValueError("findings must contain finding rows")
        _require_hard_flags("finding", finding)
        if finding.specificity_risk_status is None:
            raise ValueError("findings must contain evaluated finding rows")
        if not finding.reason_codes:
            raise ValueError("findings must contain reason_codes")
        pair = (finding.strategy_reference, finding.market_reference)
        if pair in seen_pairs:
            raise ValueError("strategy/market pairs must be unique")
        seen_pairs.add(pair)
    if normalized_findings != tuple(
        sorted(
            normalized_findings,
            key=lambda row: (row.strategy_reference, row.market_reference),
        )
    ):
        raise ValueError("findings must be sorted by strategy_reference and market_reference")
    return normalized_findings


def _normalize_source_mapping(
    source_mapping: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(source_mapping) not in (list, tuple):
        raise ValueError("source_mapping must be a list or tuple")
    rows = tuple(source_mapping)
    seen_source_roles: set[str] = set()
    for item in rows:
        if type(item) not in (list, tuple) or len(item) != 2:
            raise ValueError(
                "source_mapping entries must be source role/reference pairs",
            )
        source_role, source_reference = item
        _require_canonical_string("source_mapping source_role", source_role)
        _require_no_unsafe_surface("source_mapping source_role", source_role)
        _require_canonical_string(
            "source_mapping source_reference",
            source_reference,
        )
        _require_redacted_reference(
            "source_mapping source_reference",
            source_reference,
        )
        _require_no_unsafe_surface("source_mapping source_reference", source_reference)
        if source_role in seen_source_roles:
            raise ValueError("source_mapping source roles must be unique")
        seen_source_roles.add(source_role)
    if rows != tuple(sorted(rows)):
        raise ValueError("source_mapping must be sorted")
    return rows


def _normalize_source_config_versions(
    source_config_versions: tuple[tuple[str, str, str], ...],
) -> tuple[tuple[str, str, str], ...]:
    if type(source_config_versions) not in (list, tuple):
        raise ValueError("source_config_versions must be a list or tuple")
    versions = tuple(source_config_versions)
    seen_pairs: set[tuple[str, str]] = set()
    for item in versions:
        if type(item) not in (list, tuple) or len(item) != 3:
            raise ValueError("source_config_versions entries must have three fields")
        strategy_reference, market_reference, source_config_version = item
        _require_canonical_string(
            "source_config_versions strategy_reference",
            strategy_reference,
        )
        _require_redacted_reference(
            "source_config_versions strategy_reference",
            strategy_reference,
        )
        _require_no_unsafe_surface(
            "source_config_versions strategy_reference",
            strategy_reference,
        )
        _require_canonical_string(
            "source_config_versions market_reference",
            market_reference,
        )
        _require_redacted_reference(
            "source_config_versions market_reference",
            market_reference,
        )
        _require_no_unsafe_surface(
            "source_config_versions market_reference",
            market_reference,
        )
        _require_canonical_string(
            "source_config_versions source_config_version",
            source_config_version,
        )
        _require_no_sensitive_marker(
            "source_config_versions source_config_version",
            source_config_version,
        )
        _require_no_unsafe_surface(
            "source_config_versions source_config_version",
            source_config_version,
        )
        pair = (strategy_reference, market_reference)
        if pair in seen_pairs:
            raise ValueError("source_config_versions strategy/market pairs must be unique")
        seen_pairs.add(pair)
    if versions != tuple(sorted(versions)):
        raise ValueError(
            "source_config_versions must be sorted by strategy_reference and market_reference",
        )
    return versions


def _normalize_reason_code_counts(
    reason_code_counts: tuple[
        StrategyMarketQuestionSpecificityRiskDigestReasonCodeCount,
        ...,
    ],
) -> tuple[StrategyMarketQuestionSpecificityRiskDigestReasonCodeCount, ...]:
    if type(reason_code_counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(reason_code_counts)
    seen_reason_codes: set[str] = set()
    for count in counts:
        if type(count) is not StrategyMarketQuestionSpecificityRiskDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count rows")
        _require_hard_flags("reason_code_count", count)
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(count.reason_code)
    if tuple(count.reason_code for count in counts) != tuple(
        sorted(count.reason_code for count in counts)
    ):
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    normalized_reason_codes = tuple(reason_codes)
    if not normalized_reason_codes and not allow_empty:
        raise ValueError(f"{field_name} is required")
    seen_reason_codes: set[str] = set()
    for reason_code in normalized_reason_codes:
        _require_reason_code(field_name, reason_code)
        if reason_code in seen_reason_codes:
            raise ValueError(f"{field_name} values must be unique")
        seen_reason_codes.add(reason_code)
    if normalized_reason_codes != tuple(sorted(normalized_reason_codes)):
        raise ValueError(f"{field_name} must be sorted")
    return normalized_reason_codes


def _validate_finding_consistency(
    finding: StrategyMarketQuestionSpecificityRiskFinding,
) -> None:
    if finding.specificity_risk_status is None:
        if finding.reason_codes:
            raise ValueError("reason_codes must be empty before evaluation")
        return
    expected_status = _finding_status(finding.reason_codes)
    if finding.specificity_risk_status != expected_status:
        if finding.reason_codes == (PASS_REASON,):
            raise ValueError("reason_codes must match specificity_risk_status")
        raise ValueError("specificity_risk_status must match reason_codes")


def _validate_report_consistency(
    report: StrategyMarketQuestionSpecificityRiskDigestReport,
) -> None:
    if report.recommended_next_step != NEXT_STEPS[report.specificity_risk_status]:
        raise ValueError("recommended_next_step must match specificity_risk_status")
    if report.finding_count != _count_decimal(len(report.findings)):
        raise ValueError("finding_count must match findings")
    if report.pass_finding_count != _count_matching(report.findings, "pass"):
        raise ValueError("pass_finding_count must match findings")
    if report.watch_finding_count != _count_matching(report.findings, "watch"):
        raise ValueError("watch_finding_count must match findings")
    if report.blocked_finding_count != _count_matching(report.findings, "blocked"):
        raise ValueError("blocked_finding_count must match findings")
    if report.average_rule_clarity_score != _average(
        tuple(row.rule_clarity_score for row in report.findings)
    ):
        raise ValueError("average_rule_clarity_score must match findings")
    if report.average_measurable_endpoint_coverage_ratio != _average(
        tuple(row.measurable_endpoint_coverage_ratio for row in report.findings)
    ):
        raise ValueError(
            "average_measurable_endpoint_coverage_ratio must match findings",
        )
    if report.average_deadline_clarity_score != _average(
        tuple(row.deadline_clarity_score for row in report.findings)
    ):
        raise ValueError("average_deadline_clarity_score must match findings")
    if report.total_ambiguous_term_count != sum(
        (row.ambiguous_term_count for row in report.findings),
        ZERO_DECIMAL,
    ).quantize(SIX_PLACES):
        raise ValueError("total_ambiguous_term_count must match findings")
    if report.source_coverage_ratio != _average(
        tuple(_source_coverage_ratio(row) for row in report.findings)
    ):
        raise ValueError("source_coverage_ratio must match findings")
    if report.reason_codes != _report_reason_codes(report.findings):
        raise ValueError("reason_codes must match findings")
    if report.reason_code_counts != _reason_code_counts_for_findings(report.findings):
        raise ValueError("reason_code_counts must match findings")
    if report.source_config_versions != _source_config_versions(report.findings):
        raise ValueError("source_config_versions must match findings")
    if report.specificity_risk_status != _report_status(
        report.findings,
        report.reason_codes,
    ):
        raise ValueError("specificity_risk_status must match findings")
    if report.readiness_gap_count != sum(
        (_readiness_gap_count(row) for row in report.findings),
        ZERO_DECIMAL,
    ).quantize(SIX_PLACES):
        raise ValueError("readiness_gap_count must match findings")
    if report.derived_validation_digest != _derived_validation_digest(
        specificity_risk_status=report.specificity_risk_status,
        finding_count=report.finding_count,
        blocked_finding_count=report.blocked_finding_count,
        watch_finding_count=report.watch_finding_count,
        pass_finding_count=report.pass_finding_count,
        readiness_gap_count=report.readiness_gap_count,
        reason_codes=report.reason_codes,
    ):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(
    *,
    specificity_risk_status: str,
    finding_count: Decimal,
    blocked_finding_count: Decimal,
    watch_finding_count: Decimal,
    pass_finding_count: Decimal,
    readiness_gap_count: Decimal,
    reason_codes: tuple[str, ...],
) -> str:
    return (
        "strategy_market_question_specificity_risk_digest_v0|"
        f"status={specificity_risk_status}|"
        f"findings={_decimal_payload(finding_count)}|"
        f"blocked={_decimal_payload(blocked_finding_count)}|"
        f"watch={_decimal_payload(watch_finding_count)}|"
        f"pass={_decimal_payload(pass_finding_count)}|"
        f"gaps={_decimal_payload(readiness_gap_count)}|"
        f"reasons={','.join(reason_codes)}"
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_ratio(field_name: str, value: object) -> Decimal:
    normalized_value = _require_exact_decimal(field_name, value)
    if normalized_value < ZERO_DECIMAL or normalized_value > ONE_DECIMAL:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized_value.quantize(SIX_PLACES)


def _require_exact_decimal(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SPECIFICITY_RISK_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SPECIFICITY_RISK_REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized_value = _require_nonnegative_count_decimal(field_name, value)
    if normalized_value <= ZERO_DECIMAL:
        raise ValueError(f"{field_name} must be a positive Decimal count")
    return normalized_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized_value = _require_exact_decimal(field_name, value)
    if normalized_value < ZERO_DECIMAL:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized_value != normalized_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return normalized_value.quantize(SIX_PLACES)


def _require_redacted_reference(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(marker in lowered for marker in SENSITIVE_MARKERS):
        raise ValueError(f"{field_name} must be redacted")
    if not any(marker in lowered for marker in REDACTED_MARKERS):
        raise ValueError(f"{field_name} must be redacted")


def _require_no_sensitive_marker(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(marker in lowered for marker in SENSITIVE_MARKERS):
        raise ValueError(f"{field_name} must not contain sensitive markers")


def _require_no_unsafe_surface(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(marker in lowered for marker in UNSAFE_MARKERS):
        raise ValueError(f"{field_name} contains unsafe surface")


def _require_hard_flags(label: str, value: object) -> None:
    if object.__getattribute__(value, "paper_only") is not True:
        raise ValueError(f"{label} paper_only must be True")
    if object.__getattribute__(value, "report_only") is not True:
        raise ValueError(f"{label} report_only must be True")
    if object.__getattribute__(value, "readonly") is not True:
        raise ValueError(f"{label} readonly must be True")
