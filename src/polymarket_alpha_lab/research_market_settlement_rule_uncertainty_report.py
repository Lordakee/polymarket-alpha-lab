"""Pure public report for market settlement-rule uncertainty review."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_MARKET_SETTLEMENT_RULE_UNCERTAINTY_CONFIG_VERSION",
    "ResearchMarketSettlementRuleUncertaintyCandidate",
    "ResearchMarketSettlementRuleUncertaintyConfig",
    "ResearchMarketSettlementRuleUncertaintyReasonCodeCount",
    "ResearchMarketSettlementRuleUncertaintyReport",
    "ResearchMarketSettlementRuleUncertaintyRow",
    "build_research_market_settlement_rule_uncertainty_report",
    "research_market_settlement_rule_uncertainty_digest",
    "research_market_settlement_rule_uncertainty_report_payload",
)


DEFAULT_RESEARCH_MARKET_SETTLEMENT_RULE_UNCERTAINTY_CONFIG_VERSION = (
    "research-market-settlement-rule-uncertainty-v0"
)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
NO_CANDIDATES_REASON = "no_settlement_rule_candidates_block"
MANUAL_REVIEW_PRESENT_THRESHOLD = Decimal("0.500000")

REASON_CODES = tuple(
    sorted(
        (
            "contradiction_pressure_hard_block",
            "contradiction_pressure_high",
            "contradiction_pressure_low",
            "contradiction_pressure_watch",
            "dependent_outcome_count_high",
            "dependent_outcome_count_low",
            "dependent_outcome_count_watch",
            "manual_review_urgency_high",
            "manual_review_urgency_low",
            "manual_review_urgency_present",
            "manual_review_urgency_watch",
            NO_CANDIDATES_REASON,
            "official_source_freshness_aging",
            "official_source_freshness_current",
            "official_source_freshness_stale",
            "official_source_stale_hard_block",
            "rule_ambiguity_hard_block",
            "rule_ambiguity_high",
            "rule_ambiguity_low",
            "rule_ambiguity_watch",
            "settlement_rule_uncertainty_block",
            "settlement_rule_uncertainty_pass",
            "settlement_rule_uncertainty_report_block",
            "settlement_rule_uncertainty_report_pass",
            "settlement_rule_uncertainty_report_watch",
            "settlement_rule_uncertainty_watch",
        ),
    ),
)
UNSAFE_PUBLIC_KEYS = (
    "candidate_id",
    "raw_candidate_id",
    "market_id",
    "market_slug",
    "market_question",
    "source_url",
    "source_text",
    "dsn",
    "table",
    "table_name",
    "token",
    "private_token",
    "wallet",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommend",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "http://",
    "https://",
    "postgres://",
    "dsn ",
    " table ",
    "token ",
    " wallet ",
    " order ",
    " position ",
    " buy ",
    " sell ",
    " recommend",
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
class ResearchMarketSettlementRuleUncertaintyConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_SETTLEMENT_RULE_UNCERTAINTY_CONFIG_VERSION
    )
    pass_max_uncertainty_score: Decimal = Decimal("0.250000")
    watch_max_uncertainty_score: Decimal = Decimal("0.550000")
    dependent_outcome_watch_count: Decimal = Decimal("3.000000")
    dependent_outcome_block_count: Decimal = Decimal("6.000000")
    rule_ambiguity_weight: Decimal = Decimal("0.300000")
    official_source_staleness_weight: Decimal = Decimal("0.200000")
    dependent_outcome_weight: Decimal = Decimal("0.150000")
    contradiction_pressure_weight: Decimal = Decimal("0.200000")
    manual_review_urgency_weight: Decimal = Decimal("0.150000")
    hard_rule_ambiguity_floor: Decimal = Decimal("0.850000")
    hard_source_freshness_ceiling: Decimal = Decimal("0.150000")
    hard_contradiction_pressure_floor: Decimal = Decimal("0.850000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketSettlementRuleUncertaintyConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "pass_max_uncertainty_score",
            "watch_max_uncertainty_score",
            "rule_ambiguity_weight",
            "official_source_staleness_weight",
            "dependent_outcome_weight",
            "contradiction_pressure_weight",
            "manual_review_urgency_weight",
            "hard_rule_ambiguity_floor",
            "hard_source_freshness_ceiling",
            "hard_contradiction_pressure_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "dependent_outcome_watch_count",
            "dependent_outcome_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        if self.pass_max_uncertainty_score > self.watch_max_uncertainty_score:
            raise ValueError(
                "pass_max_uncertainty_score must be less than or equal to "
                "watch_max_uncertainty_score",
            )
        if self.dependent_outcome_watch_count >= self.dependent_outcome_block_count:
            raise ValueError(
                "dependent_outcome_watch_count must be below "
                "dependent_outcome_block_count",
            )
        _require_weights_total_one(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketSettlementRuleUncertaintyCandidate(_FinalPublicDataclass):
    candidate_id: str
    observed_at: datetime
    rule_ambiguity: Decimal
    official_source_freshness: Decimal
    dependent_outcome_count: Decimal
    contradiction_pressure: Decimal
    manual_review_urgency: Decimal
    market_id: str | None = None
    market_slug: str | None = None
    market_question: str | None = None
    source_url: str | None = None
    source_text: str | None = None
    dsn: str | None = None
    table_name: str | None = None
    private_token: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketSettlementRuleUncertaintyCandidate,
            "candidate",
        )
        _require_canonical_string("candidate_id", self.candidate_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "rule_ambiguity",
            "official_source_freshness",
            "contradiction_pressure",
            "manual_review_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "dependent_outcome_count",
            _normalize_count("dependent_outcome_count", self.dependent_outcome_count),
        )
        for field_name in (
            "market_id",
            "market_slug",
            "market_question",
            "source_url",
            "source_text",
            "dsn",
            "table_name",
            "private_token",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_string(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class ResearchMarketSettlementRuleUncertaintyRow(_FinalPublicDataclass):
    row_number: Decimal
    rule_ambiguity_score: Decimal
    official_source_staleness_score: Decimal
    dependent_outcome_count: Decimal
    dependent_outcome_score: Decimal
    contradiction_pressure_score: Decimal
    manual_review_urgency_score: Decimal
    uncertainty_score: Decimal
    status: str
    hard_flags: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSettlementRuleUncertaintyRow, "row")
        object.__setattr__(
            self,
            "row_number",
            _normalize_positive_count("row_number", self.row_number),
        )
        object.__setattr__(
            self,
            "dependent_outcome_count",
            _normalize_count("dependent_outcome_count", self.dependent_outcome_count),
        )
        for field_name in (
            "rule_ambiguity_score",
            "official_source_staleness_score",
            "dependent_outcome_score",
            "contradiction_pressure_score",
            "manual_review_urgency_score",
            "uncertainty_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "hard_flags",
            _normalize_reason_codes("hard_flags", self.hard_flags, allow_empty=True),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketSettlementRuleUncertaintyReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketSettlementRuleUncertaintyReasonCodeCount,
            "reason_code_count",
        )
        _require_member("reason_code", self.reason_code, REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketSettlementRuleUncertaintyReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_dependent_outcome_count: Decimal
    manual_review_urgent_count: Decimal
    mean_uncertainty_score: Decimal
    max_manual_review_urgency: Decimal
    status: str
    reason_code_counts: tuple[ResearchMarketSettlementRuleUncertaintyReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchMarketSettlementRuleUncertaintyRow, ...]
    public_report_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketSettlementRuleUncertaintyReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_dependent_outcome_count",
            "manual_review_urgent_count",
            "mean_uncertainty_score",
            "max_manual_review_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("public_report_digest", self.public_report_digest)
        _validate_report(self)
        expected_digest = _expected_public_report_digest(self)
        if self.public_report_digest != expected_digest:
            raise ValueError("public_report_digest must match public report payload")
        _require_hard_flags("report", self)


_PUBLIC_DATACLASS_TYPES = (
    ResearchMarketSettlementRuleUncertaintyReasonCodeCount,
    ResearchMarketSettlementRuleUncertaintyReport,
    ResearchMarketSettlementRuleUncertaintyRow,
)


@dataclass(frozen=True)
class _RowDraft:
    rule_ambiguity_score: Decimal
    official_source_staleness_score: Decimal
    dependent_outcome_count: Decimal
    dependent_outcome_score: Decimal
    contradiction_pressure_score: Decimal
    manual_review_urgency_score: Decimal
    uncertainty_score: Decimal
    status: str
    hard_flags: tuple[str, ...]
    reason_codes: tuple[str, ...]


def build_research_market_settlement_rule_uncertainty_report(
    candidates: Iterable[ResearchMarketSettlementRuleUncertaintyCandidate],
    *,
    config: ResearchMarketSettlementRuleUncertaintyConfig,
    generated_at: datetime,
) -> ResearchMarketSettlementRuleUncertaintyReport:
    if type(config) is not ResearchMarketSettlementRuleUncertaintyConfig:
        raise ValueError(
            "config must be a ResearchMarketSettlementRuleUncertaintyConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    candidate_rows = _normalize_candidates(candidates)
    for row in candidate_rows:
        if row.observed_at > generated_at_utc:
            raise ValueError("observed_at must be less than or equal to generated_at")
    drafts = tuple(_row_draft(row, config=config) for row in candidate_rows)
    rows = tuple(
        _row_from_draft(
            row_number=_count(index),
            draft=draft,
        )
        for index, draft in enumerate(sorted(drafts, key=_draft_sort_key), start=1)
    )
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "candidate_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "total_dependent_outcome_count": _sum_decimal(
            tuple(row.dependent_outcome_count for row in rows),
        ),
        "manual_review_urgent_count": _manual_review_urgent_count(rows),
        "mean_uncertainty_score": _mean(tuple(row.uncertainty_score for row in rows)),
        "max_manual_review_urgency": _max_decimal(
            tuple(row.manual_review_urgency_score for row in rows),
        ),
        "status": _report_status(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
    }
    return ResearchMarketSettlementRuleUncertaintyReport(
        **report_values,
        public_report_digest=_public_digest(_report_payload_without_digest(**report_values)),
    )


def research_market_settlement_rule_uncertainty_report_payload(
    report: ResearchMarketSettlementRuleUncertaintyReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketSettlementRuleUncertaintyReport:
        raise ValueError(
            "report must be a ResearchMarketSettlementRuleUncertaintyReport",
        )
    _require_payload_safe_value("report", report)
    _validate_report(report)
    expected_digest = _expected_public_report_digest(report)
    if report.public_report_digest != expected_digest:
        raise ValueError("public_report_digest must match public report payload")
    payload = _report_payload_without_digest_from_report(report)
    payload["public_report_digest"] = report.public_report_digest
    payload["paper_only"] = True
    payload["report_only"] = True
    payload["readonly"] = True
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_public_payload(ready)
    return ready


def research_market_settlement_rule_uncertainty_digest(
    report: ResearchMarketSettlementRuleUncertaintyReport,
) -> str:
    payload = research_market_settlement_rule_uncertainty_report_payload(report)
    digest = payload.get("public_report_digest")
    if type(digest) is not str:
        raise ValueError("public_report_digest must be a string")
    return digest


def _row_draft(
    candidate: ResearchMarketSettlementRuleUncertaintyCandidate,
    *,
    config: ResearchMarketSettlementRuleUncertaintyConfig,
) -> _RowDraft:
    official_source_staleness_score = _normalize_probability(
        "official_source_staleness_score",
        ONE - candidate.official_source_freshness,
    )
    dependent_outcome_score = _dependent_outcome_score(
        candidate.dependent_outcome_count,
        config=config,
    )
    uncertainty_score = _weighted_score(
        rule_ambiguity_score=candidate.rule_ambiguity,
        official_source_staleness_score=official_source_staleness_score,
        dependent_outcome_score=dependent_outcome_score,
        contradiction_pressure_score=candidate.contradiction_pressure,
        manual_review_urgency_score=candidate.manual_review_urgency,
        config=config,
    )
    hard_flags = _hard_flags(candidate, config=config)
    status = _row_status(
        rule_ambiguity_score=candidate.rule_ambiguity,
        official_source_staleness_score=official_source_staleness_score,
        dependent_outcome_score=dependent_outcome_score,
        contradiction_pressure_score=candidate.contradiction_pressure,
        manual_review_urgency_score=candidate.manual_review_urgency,
        uncertainty_score=uncertainty_score,
        hard_flags=hard_flags,
        config=config,
    )
    return _RowDraft(
        rule_ambiguity_score=candidate.rule_ambiguity,
        official_source_staleness_score=official_source_staleness_score,
        dependent_outcome_count=candidate.dependent_outcome_count,
        dependent_outcome_score=dependent_outcome_score,
        contradiction_pressure_score=candidate.contradiction_pressure,
        manual_review_urgency_score=candidate.manual_review_urgency,
        uncertainty_score=uncertainty_score,
        status=status,
        hard_flags=hard_flags,
        reason_codes=_row_reason_codes(
            rule_ambiguity_score=candidate.rule_ambiguity,
            official_source_staleness_score=official_source_staleness_score,
            dependent_outcome_count=candidate.dependent_outcome_count,
            contradiction_pressure_score=candidate.contradiction_pressure,
            manual_review_urgency_score=candidate.manual_review_urgency,
            status=status,
            hard_flags=hard_flags,
            config=config,
        ),
    )


def _row_from_draft(
    *,
    row_number: Decimal,
    draft: _RowDraft,
) -> ResearchMarketSettlementRuleUncertaintyRow:
    return ResearchMarketSettlementRuleUncertaintyRow(
        row_number=row_number,
        rule_ambiguity_score=draft.rule_ambiguity_score,
        official_source_staleness_score=draft.official_source_staleness_score,
        dependent_outcome_count=draft.dependent_outcome_count,
        dependent_outcome_score=draft.dependent_outcome_score,
        contradiction_pressure_score=draft.contradiction_pressure_score,
        manual_review_urgency_score=draft.manual_review_urgency_score,
        uncertainty_score=draft.uncertainty_score,
        status=draft.status,
        hard_flags=draft.hard_flags,
        reason_codes=draft.reason_codes,
    )


def _weighted_score(
    *,
    rule_ambiguity_score: Decimal,
    official_source_staleness_score: Decimal,
    dependent_outcome_score: Decimal,
    contradiction_pressure_score: Decimal,
    manual_review_urgency_score: Decimal,
    config: ResearchMarketSettlementRuleUncertaintyConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            rule_ambiguity_score * config.rule_ambiguity_weight
            + official_source_staleness_score
            * config.official_source_staleness_weight
            + dependent_outcome_score * config.dependent_outcome_weight
            + contradiction_pressure_score * config.contradiction_pressure_weight
            + manual_review_urgency_score * config.manual_review_urgency_weight
        )
    return _normalize_probability("uncertainty_score", score)


def _dependent_outcome_score(
    dependent_outcome_count: Decimal,
    *,
    config: ResearchMarketSettlementRuleUncertaintyConfig,
) -> Decimal:
    if dependent_outcome_count >= config.dependent_outcome_block_count:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            "dependent_outcome_score",
            dependent_outcome_count / config.dependent_outcome_block_count,
        )


def _hard_flags(
    candidate: ResearchMarketSettlementRuleUncertaintyCandidate,
    *,
    config: ResearchMarketSettlementRuleUncertaintyConfig,
) -> tuple[str, ...]:
    hard_flags: list[str] = []
    if candidate.rule_ambiguity >= config.hard_rule_ambiguity_floor:
        hard_flags.append("rule_ambiguity_hard_block")
    if candidate.official_source_freshness <= config.hard_source_freshness_ceiling:
        hard_flags.append("official_source_stale_hard_block")
    if candidate.contradiction_pressure >= config.hard_contradiction_pressure_floor:
        hard_flags.append("contradiction_pressure_hard_block")
    return tuple(sorted(hard_flags))


def _row_status(
    *,
    rule_ambiguity_score: Decimal,
    official_source_staleness_score: Decimal,
    dependent_outcome_score: Decimal,
    contradiction_pressure_score: Decimal,
    manual_review_urgency_score: Decimal,
    uncertainty_score: Decimal,
    hard_flags: tuple[str, ...],
    config: ResearchMarketSettlementRuleUncertaintyConfig,
) -> str:
    if hard_flags or uncertainty_score > config.watch_max_uncertainty_score:
        return "block"
    component_scores = (
        rule_ambiguity_score,
        official_source_staleness_score,
        dependent_outcome_score,
        contradiction_pressure_score,
        manual_review_urgency_score,
    )
    if uncertainty_score > config.pass_max_uncertainty_score or any(
        score > config.pass_max_uncertainty_score for score in component_scores
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    rule_ambiguity_score: Decimal,
    official_source_staleness_score: Decimal,
    dependent_outcome_count: Decimal,
    contradiction_pressure_score: Decimal,
    manual_review_urgency_score: Decimal,
    status: str,
    hard_flags: tuple[str, ...],
    config: ResearchMarketSettlementRuleUncertaintyConfig,
) -> tuple[str, ...]:
    reason_codes = [
        _band_reason(
            rule_ambiguity_score,
            low="rule_ambiguity_low",
            watch="rule_ambiguity_watch",
            high="rule_ambiguity_high",
        ),
        _source_freshness_reason(official_source_staleness_score),
        _dependent_outcome_reason(dependent_outcome_count, config=config),
        _band_reason(
            contradiction_pressure_score,
            low="contradiction_pressure_low",
            watch="contradiction_pressure_watch",
            high="contradiction_pressure_high",
        ),
        _band_reason(
            manual_review_urgency_score,
            low="manual_review_urgency_low",
            watch="manual_review_urgency_watch",
            high="manual_review_urgency_high",
        ),
        f"settlement_rule_uncertainty_{status}",
    ]
    reason_codes.extend(hard_flags)
    return tuple(sorted(reason_codes))


def _band_reason(value: Decimal, *, low: str, watch: str, high: str) -> str:
    if value <= Decimal("0.250000"):
        return low
    if value >= Decimal("0.750000"):
        return high
    return watch


def _source_freshness_reason(official_source_staleness_score: Decimal) -> str:
    official_source_freshness = _normalize_probability(
        "official_source_freshness",
        ONE - official_source_staleness_score,
    )
    if official_source_freshness >= Decimal("0.750000"):
        return "official_source_freshness_current"
    if official_source_freshness <= Decimal("0.250000"):
        return "official_source_freshness_stale"
    return "official_source_freshness_aging"


def _dependent_outcome_reason(
    dependent_outcome_count: Decimal,
    *,
    config: ResearchMarketSettlementRuleUncertaintyConfig,
) -> str:
    if dependent_outcome_count >= config.dependent_outcome_block_count:
        return "dependent_outcome_count_high"
    if dependent_outcome_count >= config.dependent_outcome_watch_count:
        return "dependent_outcome_count_watch"
    return "dependent_outcome_count_low"


def _report_status(
    rows: tuple[ResearchMarketSettlementRuleUncertaintyRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketSettlementRuleUncertaintyRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_CANDIDATES_REASON,)
    reason_codes = {f"settlement_rule_uncertainty_report_{_report_status(rows)}"}
    reason_codes.update(flag for row in rows for flag in row.hard_flags)
    if any(
        row.manual_review_urgency_score >= MANUAL_REVIEW_PRESENT_THRESHOLD
        for row in rows
    ):
        reason_codes.add("manual_review_urgency_present")
    return tuple(sorted(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchMarketSettlementRuleUncertaintyRow, ...],
) -> tuple[ResearchMarketSettlementRuleUncertaintyReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketSettlementRuleUncertaintyReasonCodeCount(
                reason_code=NO_CANDIDATES_REASON,
                count=ONE,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchMarketSettlementRuleUncertaintyReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _draft_sort_key(
    draft: _RowDraft,
) -> tuple[Decimal, Decimal, Decimal, Decimal, tuple[str, ...], tuple[str, ...]]:
    return (
        -STATUS_WEIGHT[draft.status],
        -draft.manual_review_urgency_score,
        -draft.uncertainty_score,
        -draft.dependent_outcome_count,
        draft.hard_flags,
        draft.reason_codes,
    )


def _status_count(
    rows: tuple[ResearchMarketSettlementRuleUncertaintyRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _manual_review_urgent_count(
    rows: tuple[ResearchMarketSettlementRuleUncertaintyRow, ...],
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if row.manual_review_urgency_score >= MANUAL_REVIEW_PRESENT_THRESHOLD
        ),
    )


def _validate_row(row: ResearchMarketSettlementRuleUncertaintyRow) -> None:
    expected_score = _normalize_probability(
        "uncertainty_score",
        row.rule_ambiguity_score * Decimal("0.300000")
        + row.official_source_staleness_score * Decimal("0.200000")
        + row.dependent_outcome_score * Decimal("0.150000")
        + row.contradiction_pressure_score * Decimal("0.200000")
        + row.manual_review_urgency_score * Decimal("0.150000"),
    )
    if row.uncertainty_score != expected_score:
        raise ValueError("uncertainty_score must match weighted component scores")
    if row.status != _status_from_row(row):
        raise ValueError("status must match row scores")
    if row.hard_flags != tuple(code for code in row.reason_codes if code.endswith("_hard_block")):
        raise ValueError("hard_flags must match reason_codes")
    if row.reason_codes != _row_reason_codes(
        rule_ambiguity_score=row.rule_ambiguity_score,
        official_source_staleness_score=row.official_source_staleness_score,
        dependent_outcome_count=row.dependent_outcome_count,
        contradiction_pressure_score=row.contradiction_pressure_score,
        manual_review_urgency_score=row.manual_review_urgency_score,
        status=row.status,
        hard_flags=row.hard_flags,
        config=ResearchMarketSettlementRuleUncertaintyConfig(),
    ):
        raise ValueError("reason_codes must match row scores")


def _status_from_row(row: ResearchMarketSettlementRuleUncertaintyRow) -> str:
    if row.hard_flags or row.uncertainty_score > Decimal("0.550000"):
        return "block"
    component_scores = (
        row.rule_ambiguity_score,
        row.official_source_staleness_score,
        row.dependent_outcome_score,
        row.contradiction_pressure_score,
        row.manual_review_urgency_score,
    )
    if row.uncertainty_score > Decimal("0.250000") or any(
        score > Decimal("0.250000") for score in component_scores
    ):
        return "watch"
    return "pass"


def _validate_report(report: ResearchMarketSettlementRuleUncertaintyReport) -> None:
    rows = report.rows
    for row in rows:
        _validate_row(row)
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.total_dependent_outcome_count != _sum_decimal(
        tuple(row.dependent_outcome_count for row in rows),
    ):
        raise ValueError("total_dependent_outcome_count must match rows")
    if report.manual_review_urgent_count != _manual_review_urgent_count(rows):
        raise ValueError("manual_review_urgent_count must match rows")
    if report.mean_uncertainty_score != _mean(tuple(row.uncertainty_score for row in rows)):
        raise ValueError("mean_uncertainty_score must match rows")
    if report.max_manual_review_urgency != _max_decimal(
        tuple(row.manual_review_urgency_score for row in rows),
    ):
        raise ValueError("max_manual_review_urgency must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _normalize_candidates(
    candidates: Iterable[ResearchMarketSettlementRuleUncertaintyCandidate],
) -> tuple[ResearchMarketSettlementRuleUncertaintyCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        rows = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMarketSettlementRuleUncertaintyCandidate:
            raise ValueError(
                "candidates must contain ResearchMarketSettlementRuleUncertaintyCandidate values",
            )
        _require_hard_flags("candidate", row)
        if row.candidate_id in seen:
            raise ValueError("candidates must not contain duplicate candidate_id values")
        seen.add(row.candidate_id)
    return rows


def _normalize_rows(
    rows: object,
) -> tuple[ResearchMarketSettlementRuleUncertaintyRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must contain row values")
    try:
        values = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must contain row values") from exc
    for row in values:
        if type(row) is not ResearchMarketSettlementRuleUncertaintyRow:
            raise ValueError("rows must contain row values")
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must use canonical sequence")
    return values


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[ResearchMarketSettlementRuleUncertaintyReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must contain reason code counts")
    try:
        values = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must contain reason code counts") from exc
    seen_codes: set[str] = set()
    for row in values:
        if type(row) is not ResearchMarketSettlementRuleUncertaintyReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason code counts")
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate reason_code values")
        seen_codes.add(row.reason_code)
    if values != tuple(sorted(values, key=lambda item: (-item.count, item.reason_code))):
        raise ValueError("reason_code_counts must use canonical sequence")
    return values


def _row_sort_key(
    row: ResearchMarketSettlementRuleUncertaintyRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, tuple[str, ...], tuple[str, ...], Decimal]:
    return (
        -STATUS_WEIGHT[row.status],
        -row.manual_review_urgency_score,
        -row.uncertainty_score,
        -row.dependent_outcome_count,
        row.hard_flags,
        row.reason_codes,
        row.row_number,
    )


def _report_payload_without_digest_from_report(
    report: ResearchMarketSettlementRuleUncertaintyReport,
) -> dict[str, object]:
    return _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        candidate_count=report.candidate_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        total_dependent_outcome_count=report.total_dependent_outcome_count,
        manual_review_urgent_count=report.manual_review_urgent_count,
        mean_uncertainty_score=report.mean_uncertainty_score,
        max_manual_review_urgency=report.max_manual_review_urgency,
        status=report.status,
        reason_code_counts=report.reason_code_counts,
        reason_codes=report.reason_codes,
        rows=report.rows,
    )


def _report_payload_without_digest(
    *,
    generated_at: datetime,
    config_version: str,
    candidate_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    total_dependent_outcome_count: Decimal,
    manual_review_urgent_count: Decimal,
    mean_uncertainty_score: Decimal,
    max_manual_review_urgency: Decimal,
    status: str,
    reason_code_counts: tuple[ResearchMarketSettlementRuleUncertaintyReasonCodeCount, ...],
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchMarketSettlementRuleUncertaintyRow, ...],
) -> dict[str, object]:
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "candidate_count": candidate_count,
        "pass_count": pass_count,
        "watch_count": watch_count,
        "block_count": block_count,
        "total_dependent_outcome_count": total_dependent_outcome_count,
        "manual_review_urgent_count": manual_review_urgent_count,
        "mean_uncertainty_score": mean_uncertainty_score,
        "max_manual_review_urgency": max_manual_review_urgency,
        "status": status,
        "reason_code_counts": tuple(
            {
                "reason_code": row.reason_code,
                "count": row.count,
            }
            for row in reason_code_counts
        ),
        "reason_codes": reason_codes,
        "rows": tuple(_row_payload(row) for row in rows),
    }


def _row_payload(row: ResearchMarketSettlementRuleUncertaintyRow) -> dict[str, object]:
    _require_hard_flags("row", row)
    _validate_row(row)
    return {
        "row_number": row.row_number,
        "rule_ambiguity_score": row.rule_ambiguity_score,
        "official_source_staleness_score": row.official_source_staleness_score,
        "dependent_outcome_count": row.dependent_outcome_count,
        "dependent_outcome_score": row.dependent_outcome_score,
        "contradiction_pressure_score": row.contradiction_pressure_score,
        "manual_review_urgency_score": row.manual_review_urgency_score,
        "uncertainty_score": row.uncertainty_score,
        "status": row.status,
        "hard_flags": row.hard_flags,
        "reason_codes": row.reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _expected_public_report_digest(
    report: ResearchMarketSettlementRuleUncertaintyReport,
) -> str:
    return _public_digest(_report_payload_without_digest_from_report(report))


def _public_digest(payload: dict[str, object]) -> str:
    ready = _json_ready(payload)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        _require_six_decimal_decimal("JSON Decimal value", value)
        return format(value, "f")
    if type(value) is datetime:
        _require_utc_datetime("JSON datetime value", value)
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        _require_payload_safe_value("JSON value", value)
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) in (int, float):
        raise ValueError("JSON numeric value must use Decimal strings")
    if type(value) is str:
        _require_canonical_string("JSON string", value)
        return value
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, set)):
        raise ValueError("JSON value must come from public dataclass fields")
    raise ValueError("value is not JSON serializable")


def _require_payload_safe_value(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{label} contains unsupported dataclass")
        for field in fields(value):
            _require_payload_safe_value(f"{label}.{field.name}", getattr(value, field.name))
        return
    if type(value) is Decimal:
        _require_six_decimal_decimal(label, value)
        return
    if type(value) is datetime:
        _require_utc_datetime(label, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{label}[{index}]", item)
        return
    if value is None or type(value) in (bool, str):
        if type(value) is str:
            _require_canonical_string(label, value)
        return
    if type(value) in (int, float) or isinstance(value, (list, dict, set)):
        raise ValueError(f"{label} must come from public dataclass fields")
    raise ValueError(f"{label} contains unsupported value")


def _require_public_payload(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in UNSAFE_PUBLIC_KEYS):
                raise ValueError("public payload contains a private key")
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True")
            _require_public_payload(item)
        return
    if type(value) is list:
        for item in value:
            _require_public_payload(item)
        return
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        lowered_value = value.lower()
        if any(fragment in lowered_value for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
            raise ValueError("public payload contains a private value")
        return
    raise ValueError("public payload must contain JSON scalar strings")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_utc_datetime(field_name: str, value: object) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")


def _normalize_optional_string(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    _require_canonical_string(field_name, value)
    return value


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must contain reason codes")
    try:
        normalized = tuple(values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain reason codes") from exc
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if normalized != tuple(sorted(normalized)):
        raise ValueError(f"{field_name} must use canonical sequence")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    for reason_code in normalized:
        _require_member(field_name, reason_code, REASON_CODES)
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.quantize(COUNT_QUANTUM):
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    return _quantize(decimal_value)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    return _quantize(sum(values, ZERO))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / _count(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_six_decimal_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_status(field_name: str, value: object) -> None:
    _require_member(field_name, value, STATUSES)


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_weights_total_one(
    config: ResearchMarketSettlementRuleUncertaintyConfig,
) -> None:
    total = _quantize(
        config.rule_ambiguity_weight
        + config.official_source_staleness_weight
        + config.dependent_outcome_weight
        + config.contradiction_pressure_weight
        + config.manual_review_urgency_weight,
    )
    if total != ONE:
        raise ValueError("rule_ambiguity_weight must be part of weights totaling 1.000000")
