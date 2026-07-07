"""Phase 1 read-only guard for ambiguous Polymarket resolution rules."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_RESOLUTION_RULE_AMBIGUITY_GUARD_V2_CONFIG_VERSION = (
    "strategy-resolution-rule-ambiguity-guard-v2"
)

_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DEFAULT_WATCH_AMBIGUITY_SCORE = Decimal("0.250000")
_DEFAULT_BLOCK_AMBIGUITY_SCORE = Decimal("0.700000")
_NO_OFFICIAL_SOURCE_PENALTY = Decimal("0.250000")
_LIMITED_OFFICIAL_SOURCE_PENALTY = Decimal("0.100000")
_CONFLICTING_INTERPRETATION_PENALTY = Decimal("0.150000")
_MAX_CONFLICTING_INTERPRETATION_PENALTY = Decimal("0.450000")
_MISSING_DEADLINE_PENALTY = Decimal("0.200000")
_MANUAL_REVIEW_PENALTY = Decimal("0.300000")

_STATUSES = ("pass", "watch", "block")
_REPORT_STATUSES = ("empty", "pass", "watch", "block")
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}


@dataclass(frozen=True)
class StrategyResolutionRuleAmbiguityGuardV2Config:
    config_version: str = DEFAULT_STRATEGY_RESOLUTION_RULE_AMBIGUITY_GUARD_V2_CONFIG_VERSION
    watch_ambiguity_score: Decimal = _DEFAULT_WATCH_AMBIGUITY_SCORE
    block_ambiguity_score: Decimal = _DEFAULT_BLOCK_AMBIGUITY_SCORE
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "watch_ambiguity_score",
            _normalize_probability(
                "watch_ambiguity_score",
                self.watch_ambiguity_score,
            ),
        )
        object.__setattr__(
            self,
            "block_ambiguity_score",
            _normalize_probability(
                "block_ambiguity_score",
                self.block_ambiguity_score,
            ),
        )
        if self.block_ambiguity_score <= self.watch_ambiguity_score:
            raise ValueError("block_ambiguity_score must be greater than watch_ambiguity_score")
        require_paper_only_flags("StrategyResolutionRuleAmbiguityGuardV2Config", self)


@dataclass(frozen=True)
class StrategyResolutionRuleAmbiguityGuardV2Input:
    market_id: str
    event_slug: str
    category: str
    rule_text_quality_score: Decimal
    official_resolution_source_count: int
    conflicting_interpretation_count: int
    missing_deadline_flag: bool
    manual_review_required: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("event_slug", self.event_slug)
        _require_canonical_string("category", self.category)
        object.__setattr__(
            self,
            "rule_text_quality_score",
            _normalize_probability(
                "rule_text_quality_score",
                self.rule_text_quality_score,
            ),
        )
        _require_nonnegative_int(
            "official_resolution_source_count",
            self.official_resolution_source_count,
        )
        _require_nonnegative_int(
            "conflicting_interpretation_count",
            self.conflicting_interpretation_count,
        )
        _require_bool("missing_deadline_flag", self.missing_deadline_flag)
        _require_bool("manual_review_required", self.manual_review_required)
        require_paper_only_flags("StrategyResolutionRuleAmbiguityGuardV2Input", self)


@dataclass(frozen=True)
class StrategyResolutionRuleAmbiguityGuardV2ReasonCodeCount:
    reason_code: str
    count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("reason_code", self.reason_code)
        _require_positive_int("count", self.count)
        require_paper_only_flags(
            "StrategyResolutionRuleAmbiguityGuardV2ReasonCodeCount",
            self,
        )


@dataclass(frozen=True)
class StrategyResolutionRuleAmbiguityGuardV2Row:
    market_id: str
    event_slug: str
    category: str
    rule_text_quality_score: Decimal
    official_resolution_source_count: int
    conflicting_interpretation_count: int
    missing_deadline_flag: bool
    manual_review_required: bool
    ambiguity_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("event_slug", self.event_slug)
        _require_canonical_string("category", self.category)
        object.__setattr__(
            self,
            "rule_text_quality_score",
            _normalize_probability(
                "rule_text_quality_score",
                self.rule_text_quality_score,
            ),
        )
        _require_nonnegative_int(
            "official_resolution_source_count",
            self.official_resolution_source_count,
        )
        _require_nonnegative_int(
            "conflicting_interpretation_count",
            self.conflicting_interpretation_count,
        )
        _require_bool("missing_deadline_flag", self.missing_deadline_flag)
        _require_bool("manual_review_required", self.manual_review_required)
        object.__setattr__(
            self,
            "ambiguity_score",
            _normalize_probability("ambiguity_score", self.ambiguity_score),
        )
        _require_member("status", self.status, _STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        require_paper_only_flags("StrategyResolutionRuleAmbiguityGuardV2Row", self)


@dataclass(frozen=True)
class StrategyResolutionRuleAmbiguityGuardV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    candidate_count: int
    pass_count: int
    watch_count: int
    block_count: int
    ambiguous_candidate_count: int
    missing_deadline_count: int
    conflicting_interpretation_count: int
    max_ambiguity_score: Decimal
    validation_digest: str
    reason_code_counts: tuple[StrategyResolutionRuleAmbiguityGuardV2ReasonCodeCount, ...]
    rows: tuple[StrategyResolutionRuleAmbiguityGuardV2Row, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_member("report_status", self.report_status, _REPORT_STATUSES)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "ambiguous_candidate_count",
            "missing_deadline_count",
            "conflicting_interpretation_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "max_ambiguity_score",
            _normalize_probability("max_ambiguity_score", self.max_ambiguity_score),
        )
        _require_validation_digest(self.validation_digest)
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        expected_digest = _validation_digest_for_report(self)
        if self.validation_digest != expected_digest:
            raise ValueError("validation_digest must match report content")
        require_paper_only_flags("StrategyResolutionRuleAmbiguityGuardV2Report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_resolution_rule_ambiguity_guard_v2_payload(self)


def build_strategy_resolution_rule_ambiguity_guard_v2_report(
    inputs: tuple[StrategyResolutionRuleAmbiguityGuardV2Input, ...],
    *,
    config: StrategyResolutionRuleAmbiguityGuardV2Config,
    generated_at: datetime,
) -> StrategyResolutionRuleAmbiguityGuardV2Report:
    if type(config) is not StrategyResolutionRuleAmbiguityGuardV2Config:
        raise ValueError(
            "config must be a StrategyResolutionRuleAmbiguityGuardV2Config",
        )
    require_paper_only_flags("StrategyResolutionRuleAmbiguityGuardV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    rows = tuple(sorted((_row_for_input(item, config) for item in input_rows), key=_row_sort_key))
    report_status = _report_status(rows)
    reason_code_counts = _reason_code_counts(rows)
    max_ambiguity_score = max(
        (row.ambiguity_score for row in rows),
        default=_ZERO,
    )
    digest = _validation_digest_from_parts(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=report_status,
        candidate_count=len(rows),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        ambiguous_candidate_count=sum(1 for row in rows if row.status != "pass"),
        missing_deadline_count=sum(1 for row in rows if row.missing_deadline_flag),
        conflicting_interpretation_count=sum(
            row.conflicting_interpretation_count for row in rows
        ),
        max_ambiguity_score=max_ambiguity_score,
        reason_code_counts=reason_code_counts,
        rows=rows,
    )
    return StrategyResolutionRuleAmbiguityGuardV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=report_status,
        candidate_count=len(rows),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        ambiguous_candidate_count=sum(1 for row in rows if row.status != "pass"),
        missing_deadline_count=sum(1 for row in rows if row.missing_deadline_flag),
        conflicting_interpretation_count=sum(
            row.conflicting_interpretation_count for row in rows
        ),
        max_ambiguity_score=max_ambiguity_score,
        validation_digest=digest,
        reason_code_counts=reason_code_counts,
        rows=rows,
    )


def strategy_resolution_rule_ambiguity_guard_v2_payload(
    report: StrategyResolutionRuleAmbiguityGuardV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyResolutionRuleAmbiguityGuardV2Report:
        raise ValueError("report must be a StrategyResolutionRuleAmbiguityGuardV2Report")
    require_paper_only_flags("StrategyResolutionRuleAmbiguityGuardV2Report", report)
    payload = _report_payload(
        generated_at=report.generated_at,
        config_version=report.config_version,
        report_status=report.report_status,
        candidate_count=report.candidate_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        ambiguous_candidate_count=report.ambiguous_candidate_count,
        missing_deadline_count=report.missing_deadline_count,
        conflicting_interpretation_count=report.conflicting_interpretation_count,
        max_ambiguity_score=report.max_ambiguity_score,
        reason_code_counts=report.reason_code_counts,
        rows=report.rows,
        validation_digest=report.validation_digest,
    )
    reject_unsafe_surface_fields(
        "StrategyResolutionRuleAmbiguityGuardV2Report.payload",
        payload,
    )
    return payload


def _row_for_input(
    candidate: StrategyResolutionRuleAmbiguityGuardV2Input,
    config: StrategyResolutionRuleAmbiguityGuardV2Config,
) -> StrategyResolutionRuleAmbiguityGuardV2Row:
    ambiguity_score = _ambiguity_score(candidate)
    status = _row_status(candidate, ambiguity_score, config)
    return StrategyResolutionRuleAmbiguityGuardV2Row(
        market_id=candidate.market_id,
        event_slug=candidate.event_slug,
        category=candidate.category,
        rule_text_quality_score=candidate.rule_text_quality_score,
        official_resolution_source_count=candidate.official_resolution_source_count,
        conflicting_interpretation_count=candidate.conflicting_interpretation_count,
        missing_deadline_flag=candidate.missing_deadline_flag,
        manual_review_required=candidate.manual_review_required,
        ambiguity_score=ambiguity_score,
        status=status,
        reason_codes=_row_reason_codes(candidate, status),
    )


def _ambiguity_score(candidate: StrategyResolutionRuleAmbiguityGuardV2Input) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        score = _ONE - candidate.rule_text_quality_score
        if candidate.official_resolution_source_count == 0:
            score += _NO_OFFICIAL_SOURCE_PENALTY
        elif candidate.official_resolution_source_count == 1:
            score += _LIMITED_OFFICIAL_SOURCE_PENALTY
        conflict_penalty = (
            Decimal(candidate.conflicting_interpretation_count)
            * _CONFLICTING_INTERPRETATION_PENALTY
        )
        score += min(conflict_penalty, _MAX_CONFLICTING_INTERPRETATION_PENALTY)
        if candidate.missing_deadline_flag:
            score += _MISSING_DEADLINE_PENALTY
        if candidate.manual_review_required:
            score += _MANUAL_REVIEW_PENALTY
        return _cap_probability(score)


def _row_status(
    candidate: StrategyResolutionRuleAmbiguityGuardV2Input,
    ambiguity_score: Decimal,
    config: StrategyResolutionRuleAmbiguityGuardV2Config,
) -> str:
    if candidate.manual_review_required or ambiguity_score >= config.block_ambiguity_score:
        return "block"
    if ambiguity_score >= config.watch_ambiguity_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    candidate: StrategyResolutionRuleAmbiguityGuardV2Input,
    status: str,
) -> tuple[str, ...]:
    if status == "pass":
        reason_codes = ["resolution_criteria_clear"]
    elif status == "watch":
        reason_codes = ["resolution_rule_ambiguity_watch"]
    else:
        reason_codes = ["resolution_rule_ambiguity_block"]

    if candidate.manual_review_required:
        reason_codes.append("manual_review_required")
    if candidate.missing_deadline_flag:
        reason_codes.append("missing_resolution_deadline")
    if candidate.official_resolution_source_count == 0:
        reason_codes.append("no_official_resolution_sources")
    elif candidate.official_resolution_source_count == 1:
        reason_codes.append("limited_official_resolution_sources")
    if candidate.conflicting_interpretation_count > 0:
        reason_codes.append("conflicting_interpretations_present")
    if candidate.rule_text_quality_score < Decimal("0.750000"):
        reason_codes.append("low_rule_text_quality_score")
    return _normalize_reason_codes(tuple(reason_codes), require_nonempty=True)


def _report_status(rows: tuple[StrategyResolutionRuleAmbiguityGuardV2Row, ...]) -> str:
    if not rows:
        return "empty"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[StrategyResolutionRuleAmbiguityGuardV2Row, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _reason_code_counts(
    rows: tuple[StrategyResolutionRuleAmbiguityGuardV2Row, ...],
) -> tuple[StrategyResolutionRuleAmbiguityGuardV2ReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        StrategyResolutionRuleAmbiguityGuardV2ReasonCodeCount(
            reason_code=reason_code,
            count=count,
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _normalize_inputs(
    value: object,
) -> tuple[StrategyResolutionRuleAmbiguityGuardV2Input, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("inputs must contain StrategyResolutionRuleAmbiguityGuardV2Input values")
    try:
        inputs = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "inputs must contain StrategyResolutionRuleAmbiguityGuardV2Input values",
        ) from exc
    seen_market_ids: set[str] = set()
    for item in inputs:
        if type(item) is not StrategyResolutionRuleAmbiguityGuardV2Input:
            raise ValueError(
                "inputs must contain StrategyResolutionRuleAmbiguityGuardV2Input values",
            )
        require_paper_only_flags("StrategyResolutionRuleAmbiguityGuardV2Input", item)
        if item.market_id in seen_market_ids:
            raise ValueError("inputs must not contain duplicate market_id values")
        seen_market_ids.add(item.market_id)
    return inputs


def _normalize_rows(
    value: object,
) -> tuple[StrategyResolutionRuleAmbiguityGuardV2Row, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must contain StrategyResolutionRuleAmbiguityGuardV2Row values")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must contain StrategyResolutionRuleAmbiguityGuardV2Row values") from exc
    for row in rows:
        if type(row) is not StrategyResolutionRuleAmbiguityGuardV2Row:
            raise ValueError("rows must contain StrategyResolutionRuleAmbiguityGuardV2Row values")
        require_paper_only_flags("StrategyResolutionRuleAmbiguityGuardV2Row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must follow deterministic ambiguity risk order")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[StrategyResolutionRuleAmbiguityGuardV2ReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(
            "reason_code_counts must contain StrategyResolutionRuleAmbiguityGuardV2ReasonCodeCount values",
        )
    try:
        counts = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "reason_code_counts must contain StrategyResolutionRuleAmbiguityGuardV2ReasonCodeCount values",
        ) from exc
    for item in counts:
        if type(item) is not StrategyResolutionRuleAmbiguityGuardV2ReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain StrategyResolutionRuleAmbiguityGuardV2ReasonCodeCount values",
            )
        require_paper_only_flags(
            "StrategyResolutionRuleAmbiguityGuardV2ReasonCodeCount",
            item,
        )
    if counts != tuple(sorted(counts, key=lambda item: (-item.count, item.reason_code))):
        raise ValueError("reason_code_counts must follow deterministic count order")
    return counts


def _validate_report_consistency(
    report: StrategyResolutionRuleAmbiguityGuardV2Report,
) -> None:
    if report.candidate_count != len(report.rows):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.ambiguous_candidate_count != report.watch_count + report.block_count:
        raise ValueError("ambiguous_candidate_count must match watch and block counts")
    if report.missing_deadline_count != sum(
        1 for row in report.rows if row.missing_deadline_flag
    ):
        raise ValueError("missing_deadline_count must match rows")
    if report.conflicting_interpretation_count != sum(
        row.conflicting_interpretation_count for row in report.rows
    ):
        raise ValueError("conflicting_interpretation_count must match rows")
    expected_max = max((row.ambiguity_score for row in report.rows), default=_ZERO)
    if report.max_ambiguity_score != expected_max:
        raise ValueError("max_ambiguity_score must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _row_sort_key(row: StrategyResolutionRuleAmbiguityGuardV2Row) -> tuple[int, Decimal, str, str]:
    return (
        _STATUS_RANK[row.status],
        -row.ambiguity_score,
        row.market_id,
        row.event_slug,
    )


def _validation_digest_for_report(
    report: StrategyResolutionRuleAmbiguityGuardV2Report,
) -> str:
    return _validation_digest_from_parts(
        generated_at=report.generated_at,
        config_version=report.config_version,
        report_status=report.report_status,
        candidate_count=report.candidate_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        ambiguous_candidate_count=report.ambiguous_candidate_count,
        missing_deadline_count=report.missing_deadline_count,
        conflicting_interpretation_count=report.conflicting_interpretation_count,
        max_ambiguity_score=report.max_ambiguity_score,
        reason_code_counts=report.reason_code_counts,
        rows=report.rows,
    )


def _validation_digest_from_parts(
    *,
    generated_at: datetime,
    config_version: str,
    report_status: str,
    candidate_count: int,
    pass_count: int,
    watch_count: int,
    block_count: int,
    ambiguous_candidate_count: int,
    missing_deadline_count: int,
    conflicting_interpretation_count: int,
    max_ambiguity_score: Decimal,
    reason_code_counts: tuple[StrategyResolutionRuleAmbiguityGuardV2ReasonCodeCount, ...],
    rows: tuple[StrategyResolutionRuleAmbiguityGuardV2Row, ...],
) -> str:
    digest_payload = _report_payload(
        generated_at=generated_at,
        config_version=config_version,
        report_status=report_status,
        candidate_count=candidate_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        ambiguous_candidate_count=ambiguous_candidate_count,
        missing_deadline_count=missing_deadline_count,
        conflicting_interpretation_count=conflicting_interpretation_count,
        max_ambiguity_score=max_ambiguity_score,
        reason_code_counts=reason_code_counts,
        rows=rows,
        validation_digest=None,
    )
    canonical = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _report_payload(
    *,
    generated_at: datetime,
    config_version: str,
    report_status: str,
    candidate_count: int,
    pass_count: int,
    watch_count: int,
    block_count: int,
    ambiguous_candidate_count: int,
    missing_deadline_count: int,
    conflicting_interpretation_count: int,
    max_ambiguity_score: Decimal,
    reason_code_counts: tuple[StrategyResolutionRuleAmbiguityGuardV2ReasonCodeCount, ...],
    rows: tuple[StrategyResolutionRuleAmbiguityGuardV2Row, ...],
    validation_digest: str | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_at": _datetime_payload(generated_at),
        "config_version": config_version,
        "report_status": report_status,
        "candidate_count": candidate_count,
        "pass_count": pass_count,
        "watch_count": watch_count,
        "block_count": block_count,
        "ambiguous_candidate_count": ambiguous_candidate_count,
        "missing_deadline_count": missing_deadline_count,
        "conflicting_interpretation_count": conflicting_interpretation_count,
        "max_ambiguity_score": _decimal_payload(max_ambiguity_score),
        "reason_code_counts": [
            _reason_code_count_payload(item) for item in reason_code_counts
        ],
        "rows": [_row_payload(row) for row in rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if validation_digest is not None:
        payload["validation_digest"] = validation_digest
    reject_unsafe_surface_fields("StrategyResolutionRuleAmbiguityGuardV2Report", payload)
    return payload


def _row_payload(row: StrategyResolutionRuleAmbiguityGuardV2Row) -> dict[str, Any]:
    require_paper_only_flags("StrategyResolutionRuleAmbiguityGuardV2Row", row)
    return {
        "market_id": row.market_id,
        "event_slug": row.event_slug,
        "category": row.category,
        "rule_text_quality_score": _decimal_payload(row.rule_text_quality_score),
        "official_resolution_source_count": row.official_resolution_source_count,
        "conflicting_interpretation_count": row.conflicting_interpretation_count,
        "missing_deadline_flag": row.missing_deadline_flag,
        "manual_review_required": row.manual_review_required,
        "ambiguity_score": _decimal_payload(row.ambiguity_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _reason_code_count_payload(
    item: StrategyResolutionRuleAmbiguityGuardV2ReasonCodeCount,
) -> dict[str, Any]:
    require_paper_only_flags("StrategyResolutionRuleAmbiguityGuardV2ReasonCodeCount", item)
    return {
        "reason_code": item.reason_code,
        "count": item.count,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _cap_probability(value: Decimal) -> Decimal:
    if value >= _ONE:
        return _ONE
    if value <= _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _datetime_payload(value: datetime) -> str:
    return _as_utc("generated_at", value).isoformat()


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload decimal must be a Decimal")
    return format(value, "f")


def _normalize_reason_codes(
    value: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not value:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    reason_codes: list[str] = []
    for item in value:
        _require_canonical_string("reason_codes", item)
        if item in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(item)
        reason_codes.append(item)
    return tuple(reason_codes)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int or type(value) is bool:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: object) -> None:
    if type(value) is not int or type(value) is bool:
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_validation_digest(value: object) -> None:
    if type(value) is not str:
        raise ValueError("validation_digest must be a sha256 hex digest")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("validation_digest must be a sha256 hex digest")


__all__ = (
    "DEFAULT_STRATEGY_RESOLUTION_RULE_AMBIGUITY_GUARD_V2_CONFIG_VERSION",
    "StrategyResolutionRuleAmbiguityGuardV2Config",
    "StrategyResolutionRuleAmbiguityGuardV2Input",
    "StrategyResolutionRuleAmbiguityGuardV2ReasonCodeCount",
    "StrategyResolutionRuleAmbiguityGuardV2Report",
    "StrategyResolutionRuleAmbiguityGuardV2Row",
    "build_strategy_resolution_rule_ambiguity_guard_v2_report",
    "strategy_resolution_rule_ambiguity_guard_v2_payload",
)
