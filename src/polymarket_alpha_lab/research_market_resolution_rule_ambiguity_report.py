"""Pure public report for market resolution-rule ambiguity review."""

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
    "DEFAULT_RESEARCH_MARKET_RESOLUTION_RULE_AMBIGUITY_CONFIG_VERSION",
    "ResearchMarketResolutionRuleAmbiguityCandidate",
    "ResearchMarketResolutionRuleAmbiguityConfig",
    "ResearchMarketResolutionRuleAmbiguityReasonCodeCount",
    "ResearchMarketResolutionRuleAmbiguityReport",
    "ResearchMarketResolutionRuleAmbiguityRow",
    "build_research_market_resolution_rule_ambiguity_report",
    "research_market_resolution_rule_ambiguity_digest",
    "research_market_resolution_rule_ambiguity_report_payload",
)


DEFAULT_RESEARCH_MARKET_RESOLUTION_RULE_AMBIGUITY_CONFIG_VERSION = (
    "research-market-resolution-rule-ambiguity-v0"
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
NO_CANDIDATES_REASON = "no_resolution_rule_candidates_block"

REASON_CODES = tuple(
    sorted(
        (
            "edge_case_hard_block",
            "edge_case_high",
            "edge_case_low",
            "edge_case_watch",
            "manual_review_high",
            "manual_review_low",
            "manual_review_watch",
            NO_CANDIDATES_REASON,
            "resolution_rule_ambiguity_block",
            "resolution_rule_ambiguity_pass",
            "resolution_rule_ambiguity_report_block",
            "resolution_rule_ambiguity_report_pass",
            "resolution_rule_ambiguity_report_watch",
            "resolution_rule_ambiguity_watch",
            "rule_ambiguity_high",
            "rule_ambiguity_low",
            "rule_ambiguity_watch",
            "rule_clarity_hard_block",
            "source_disagreement_hard_block",
            "source_disagreement_high",
            "source_disagreement_low",
            "source_disagreement_watch",
        ),
    ),
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
class ResearchMarketResolutionRuleAmbiguityConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_MARKET_RESOLUTION_RULE_AMBIGUITY_CONFIG_VERSION
    pass_max_ambiguity_score: Decimal = Decimal("0.250000")
    watch_max_ambiguity_score: Decimal = Decimal("0.550000")
    rule_ambiguity_weight: Decimal = Decimal("0.400000")
    source_disagreement_weight: Decimal = Decimal("0.250000")
    edge_case_weight: Decimal = Decimal("0.200000")
    manual_review_weight: Decimal = Decimal("0.150000")
    hard_rule_clarity_floor: Decimal = Decimal("0.200000")
    hard_source_disagreement_floor: Decimal = Decimal("0.850000")
    hard_edge_case_floor: Decimal = Decimal("0.900000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketResolutionRuleAmbiguityConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "pass_max_ambiguity_score",
            "watch_max_ambiguity_score",
            "rule_ambiguity_weight",
            "source_disagreement_weight",
            "edge_case_weight",
            "manual_review_weight",
            "hard_rule_clarity_floor",
            "hard_source_disagreement_floor",
            "hard_edge_case_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.pass_max_ambiguity_score > self.watch_max_ambiguity_score:
            raise ValueError(
                "pass_max_ambiguity_score must be less than or equal to watch_max_ambiguity_score",
            )
        _require_weights_total_one(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketResolutionRuleAmbiguityCandidate(_FinalPublicDataclass):
    candidate_id: str
    observed_at: datetime
    resolution_rule_clarity: Decimal
    source_disagreement: Decimal
    edge_case_exposure: Decimal
    manual_review_signal: Decimal
    market_id: str | None = None
    market_slug: str | None = None
    market_question: str | None = None
    source_ref: str | None = None
    source_url: str | None = None
    source_text: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketResolutionRuleAmbiguityCandidate,
            "candidate",
        )
        _require_canonical_string("candidate_id", self.candidate_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "resolution_rule_clarity",
            "source_disagreement",
            "edge_case_exposure",
            "manual_review_signal",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "market_id",
            "market_slug",
            "market_question",
            "source_ref",
            "source_url",
            "source_text",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_string(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class ResearchMarketResolutionRuleAmbiguityRow(_FinalPublicDataclass):
    row_number: Decimal
    rule_ambiguity_score: Decimal
    source_disagreement_score: Decimal
    edge_case_score: Decimal
    manual_review_score: Decimal
    ambiguity_score: Decimal
    review_priority_score: Decimal
    status: str
    hard_flags: tuple[str, ...]
    reason_codes: tuple[str, ...]
    rule_ambiguity_weight: Decimal
    source_disagreement_weight: Decimal
    edge_case_weight: Decimal
    manual_review_weight: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketResolutionRuleAmbiguityRow, "row")
        object.__setattr__(
            self,
            "row_number",
            _normalize_positive_count("row_number", self.row_number),
        )
        for field_name in (
            "rule_ambiguity_score",
            "source_disagreement_score",
            "edge_case_score",
            "manual_review_score",
            "ambiguity_score",
            "review_priority_score",
            "rule_ambiguity_weight",
            "source_disagreement_weight",
            "edge_case_weight",
            "manual_review_weight",
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
        _require_row_weights_total_one(self)
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketResolutionRuleAmbiguityReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketResolutionRuleAmbiguityReasonCodeCount,
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
class ResearchMarketResolutionRuleAmbiguityReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    hard_flag_count: Decimal
    mean_ambiguity_score: Decimal
    max_review_priority_score: Decimal
    status: str
    reason_code_counts: tuple[ResearchMarketResolutionRuleAmbiguityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchMarketResolutionRuleAmbiguityRow, ...]
    public_report_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketResolutionRuleAmbiguityReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "hard_flag_count",
            "mean_ambiguity_score",
            "max_review_priority_score",
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
    ResearchMarketResolutionRuleAmbiguityConfig,
    ResearchMarketResolutionRuleAmbiguityCandidate,
    ResearchMarketResolutionRuleAmbiguityReasonCodeCount,
    ResearchMarketResolutionRuleAmbiguityReport,
    ResearchMarketResolutionRuleAmbiguityRow,
)


@dataclass(frozen=True)
class _RowDraft:
    rule_ambiguity_score: Decimal
    source_disagreement_score: Decimal
    edge_case_score: Decimal
    manual_review_score: Decimal
    ambiguity_score: Decimal
    review_priority_score: Decimal
    status: str
    hard_flags: tuple[str, ...]
    reason_codes: tuple[str, ...]


def build_research_market_resolution_rule_ambiguity_report(
    candidates: Iterable[ResearchMarketResolutionRuleAmbiguityCandidate],
    *,
    config: ResearchMarketResolutionRuleAmbiguityConfig,
    generated_at: datetime,
) -> ResearchMarketResolutionRuleAmbiguityReport:
    if type(config) is not ResearchMarketResolutionRuleAmbiguityConfig:
        raise ValueError(
            "config must be a ResearchMarketResolutionRuleAmbiguityConfig",
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
            config=config,
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
        "hard_flag_count": _count(sum(len(row.hard_flags) for row in rows)),
        "mean_ambiguity_score": _mean(tuple(row.ambiguity_score for row in rows)),
        "max_review_priority_score": _max_decimal(
            tuple(row.review_priority_score for row in rows),
        ),
        "status": _report_status(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
    }
    return ResearchMarketResolutionRuleAmbiguityReport(
        **report_values,
        public_report_digest=_public_digest(_report_payload_without_digest(**report_values)),
    )


def research_market_resolution_rule_ambiguity_report_payload(
    report: ResearchMarketResolutionRuleAmbiguityReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketResolutionRuleAmbiguityReport:
        raise ValueError(
            "report must be a ResearchMarketResolutionRuleAmbiguityReport",
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


def research_market_resolution_rule_ambiguity_digest(
    report: ResearchMarketResolutionRuleAmbiguityReport,
) -> str:
    payload = research_market_resolution_rule_ambiguity_report_payload(report)
    digest = payload.get("public_report_digest")
    if type(digest) is not str:
        raise ValueError("public_report_digest must be a string")
    return digest


def _row_draft(
    candidate: ResearchMarketResolutionRuleAmbiguityCandidate,
    *,
    config: ResearchMarketResolutionRuleAmbiguityConfig,
) -> _RowDraft:
    rule_ambiguity_score = _normalize_probability(
        "rule_ambiguity_score",
        ONE - candidate.resolution_rule_clarity,
    )
    source_disagreement_score = candidate.source_disagreement
    edge_case_score = candidate.edge_case_exposure
    manual_review_score = candidate.manual_review_signal
    ambiguity_score = _weighted_score(
        rule_ambiguity_score=rule_ambiguity_score,
        source_disagreement_score=source_disagreement_score,
        edge_case_score=edge_case_score,
        manual_review_score=manual_review_score,
        config=config,
    )
    review_priority_score = max(ambiguity_score, manual_review_score)
    hard_flags = _hard_flags(
        resolution_rule_clarity=candidate.resolution_rule_clarity,
        source_disagreement_score=source_disagreement_score,
        edge_case_score=edge_case_score,
        config=config,
    )
    status = _row_status(
        ambiguity_score=ambiguity_score,
        hard_flags=hard_flags,
        config=config,
    )
    return _RowDraft(
        rule_ambiguity_score=rule_ambiguity_score,
        source_disagreement_score=source_disagreement_score,
        edge_case_score=edge_case_score,
        manual_review_score=manual_review_score,
        ambiguity_score=ambiguity_score,
        review_priority_score=review_priority_score,
        status=status,
        hard_flags=hard_flags,
        reason_codes=_row_reason_codes(
            rule_ambiguity_score=rule_ambiguity_score,
            source_disagreement_score=source_disagreement_score,
            edge_case_score=edge_case_score,
            manual_review_score=manual_review_score,
            status=status,
            hard_flags=hard_flags,
        ),
    )


def _row_from_draft(
    *,
    row_number: Decimal,
    draft: _RowDraft,
    config: ResearchMarketResolutionRuleAmbiguityConfig,
) -> ResearchMarketResolutionRuleAmbiguityRow:
    return ResearchMarketResolutionRuleAmbiguityRow(
        row_number=row_number,
        rule_ambiguity_score=draft.rule_ambiguity_score,
        source_disagreement_score=draft.source_disagreement_score,
        edge_case_score=draft.edge_case_score,
        manual_review_score=draft.manual_review_score,
        ambiguity_score=draft.ambiguity_score,
        review_priority_score=draft.review_priority_score,
        status=draft.status,
        hard_flags=draft.hard_flags,
        reason_codes=draft.reason_codes,
        rule_ambiguity_weight=config.rule_ambiguity_weight,
        source_disagreement_weight=config.source_disagreement_weight,
        edge_case_weight=config.edge_case_weight,
        manual_review_weight=config.manual_review_weight,
    )


def _weighted_score(
    *,
    rule_ambiguity_score: Decimal,
    source_disagreement_score: Decimal,
    edge_case_score: Decimal,
    manual_review_score: Decimal,
    config: ResearchMarketResolutionRuleAmbiguityConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            rule_ambiguity_score * config.rule_ambiguity_weight
            + source_disagreement_score * config.source_disagreement_weight
            + edge_case_score * config.edge_case_weight
            + manual_review_score * config.manual_review_weight
        )
    return _normalize_probability("ambiguity_score", score)


def _hard_flags(
    *,
    resolution_rule_clarity: Decimal,
    source_disagreement_score: Decimal,
    edge_case_score: Decimal,
    config: ResearchMarketResolutionRuleAmbiguityConfig,
) -> tuple[str, ...]:
    hard_flags: list[str] = []
    if resolution_rule_clarity <= config.hard_rule_clarity_floor:
        hard_flags.append("rule_clarity_hard_block")
    if source_disagreement_score >= config.hard_source_disagreement_floor:
        hard_flags.append("source_disagreement_hard_block")
    if edge_case_score >= config.hard_edge_case_floor:
        hard_flags.append("edge_case_hard_block")
    return tuple(sorted(hard_flags))


def _row_status(
    *,
    ambiguity_score: Decimal,
    hard_flags: tuple[str, ...],
    config: ResearchMarketResolutionRuleAmbiguityConfig,
) -> str:
    if hard_flags or ambiguity_score > config.watch_max_ambiguity_score:
        return "block"
    if ambiguity_score > config.pass_max_ambiguity_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    rule_ambiguity_score: Decimal,
    source_disagreement_score: Decimal,
    edge_case_score: Decimal,
    manual_review_score: Decimal,
    status: str,
    hard_flags: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes = [
        _band_reason(
            rule_ambiguity_score,
            low="rule_ambiguity_low",
            watch="rule_ambiguity_watch",
            high="rule_ambiguity_high",
        ),
        _band_reason(
            source_disagreement_score,
            low="source_disagreement_low",
            watch="source_disagreement_watch",
            high="source_disagreement_high",
        ),
        _band_reason(
            edge_case_score,
            low="edge_case_low",
            watch="edge_case_watch",
            high="edge_case_high",
        ),
        _band_reason(
            manual_review_score,
            low="manual_review_low",
            watch="manual_review_watch",
            high="manual_review_high",
        ),
        f"resolution_rule_ambiguity_{status}",
    ]
    reason_codes.extend(hard_flags)
    return tuple(sorted(reason_codes))


def _band_reason(value: Decimal, *, low: str, watch: str, high: str) -> str:
    if value <= Decimal("0.250000"):
        return low
    if value >= Decimal("0.750000"):
        return high
    return watch


def _report_status(
    rows: tuple[ResearchMarketResolutionRuleAmbiguityRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketResolutionRuleAmbiguityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_CANDIDATES_REASON,)
    reason_codes = {f"resolution_rule_ambiguity_report_{_report_status(rows)}"}
    reason_codes.update(flag for row in rows for flag in row.hard_flags)
    return tuple(sorted(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchMarketResolutionRuleAmbiguityRow, ...],
) -> tuple[ResearchMarketResolutionRuleAmbiguityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketResolutionRuleAmbiguityReasonCodeCount(
                reason_code=NO_CANDIDATES_REASON,
                count=ONE,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchMarketResolutionRuleAmbiguityReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _draft_sort_key(
    draft: _RowDraft,
) -> tuple[Decimal, Decimal, Decimal, tuple[str, ...], tuple[str, ...]]:
    return (
        -STATUS_WEIGHT[draft.status],
        -draft.review_priority_score,
        -draft.ambiguity_score,
        draft.hard_flags,
        draft.reason_codes,
    )


def _status_count(
    rows: tuple[ResearchMarketResolutionRuleAmbiguityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _validate_row(row: ResearchMarketResolutionRuleAmbiguityRow) -> None:
    expected_score = _normalize_probability(
        "ambiguity_score",
        row.rule_ambiguity_score * row.rule_ambiguity_weight
        + row.source_disagreement_score * row.source_disagreement_weight
        + row.edge_case_score * row.edge_case_weight
        + row.manual_review_score * row.manual_review_weight,
    )
    if row.ambiguity_score != expected_score:
        raise ValueError("ambiguity_score must match weighted component scores")
    expected_review_priority_score = max(row.ambiguity_score, row.manual_review_score)
    if row.review_priority_score != expected_review_priority_score:
        raise ValueError("review_priority_score must match row scores")
    if row.status != _status_from_row(row):
        raise ValueError("status must match row scores")
    if row.hard_flags != tuple(code for code in row.reason_codes if code.endswith("_hard_block")):
        raise ValueError("hard_flags must match reason_codes")
    if row.reason_codes != _row_reason_codes(
        rule_ambiguity_score=row.rule_ambiguity_score,
        source_disagreement_score=row.source_disagreement_score,
        edge_case_score=row.edge_case_score,
        manual_review_score=row.manual_review_score,
        status=row.status,
        hard_flags=row.hard_flags,
    ):
        raise ValueError("reason_codes must match row scores")


def _status_from_row(row: ResearchMarketResolutionRuleAmbiguityRow) -> str:
    if row.hard_flags or row.ambiguity_score > Decimal("0.550000"):
        return "block"
    if row.ambiguity_score > Decimal("0.250000"):
        return "watch"
    return "pass"


def _validate_report(report: ResearchMarketResolutionRuleAmbiguityReport) -> None:
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
    if report.hard_flag_count != _count(sum(len(row.hard_flags) for row in rows)):
        raise ValueError("hard_flag_count must match rows")
    if report.mean_ambiguity_score != _mean(tuple(row.ambiguity_score for row in rows)):
        raise ValueError("mean_ambiguity_score must match rows")
    if report.max_review_priority_score != _max_decimal(
        tuple(row.review_priority_score for row in rows),
    ):
        raise ValueError("max_review_priority_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _normalize_candidates(
    candidates: Iterable[ResearchMarketResolutionRuleAmbiguityCandidate],
) -> tuple[ResearchMarketResolutionRuleAmbiguityCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        rows = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMarketResolutionRuleAmbiguityCandidate:
            raise ValueError(
                "candidates must contain ResearchMarketResolutionRuleAmbiguityCandidate values",
            )
        _require_hard_flags("candidate", row)
        if row.candidate_id in seen:
            raise ValueError("candidates must not contain duplicate candidate_id values")
        seen.add(row.candidate_id)
    return rows


def _normalize_rows(
    rows: object,
) -> tuple[ResearchMarketResolutionRuleAmbiguityRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must contain row values")
    try:
        values = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must contain row values") from exc
    for row in values:
        if type(row) is not ResearchMarketResolutionRuleAmbiguityRow:
            raise ValueError("rows must contain row values")
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must use canonical sequence")
    return values


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[ResearchMarketResolutionRuleAmbiguityReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must contain reason code counts")
    try:
        values = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must contain reason code counts") from exc
    seen_codes: set[str] = set()
    for row in values:
        if type(row) is not ResearchMarketResolutionRuleAmbiguityReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason code counts")
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate reason_code values")
        seen_codes.add(row.reason_code)
    if values != tuple(sorted(values, key=lambda item: (-item.count, item.reason_code))):
        raise ValueError("reason_code_counts must use canonical sequence")
    return values


def _row_sort_key(
    row: ResearchMarketResolutionRuleAmbiguityRow,
) -> tuple[Decimal, Decimal, Decimal, tuple[str, ...], tuple[str, ...], Decimal]:
    return (
        -STATUS_WEIGHT[row.status],
        -row.review_priority_score,
        -row.ambiguity_score,
        row.hard_flags,
        row.reason_codes,
        row.row_number,
    )


def _report_payload_without_digest_from_report(
    report: ResearchMarketResolutionRuleAmbiguityReport,
) -> dict[str, object]:
    return _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        candidate_count=report.candidate_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        hard_flag_count=report.hard_flag_count,
        mean_ambiguity_score=report.mean_ambiguity_score,
        max_review_priority_score=report.max_review_priority_score,
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
    hard_flag_count: Decimal,
    mean_ambiguity_score: Decimal,
    max_review_priority_score: Decimal,
    status: str,
    reason_code_counts: tuple[ResearchMarketResolutionRuleAmbiguityReasonCodeCount, ...],
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchMarketResolutionRuleAmbiguityRow, ...],
) -> dict[str, object]:
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "candidate_count": candidate_count,
        "pass_count": pass_count,
        "watch_count": watch_count,
        "block_count": block_count,
        "hard_flag_count": hard_flag_count,
        "mean_ambiguity_score": mean_ambiguity_score,
        "max_review_priority_score": max_review_priority_score,
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


def _row_payload(row: ResearchMarketResolutionRuleAmbiguityRow) -> dict[str, object]:
    _require_hard_flags("row", row)
    _validate_row(row)
    return {
        "row_number": row.row_number,
        "rule_ambiguity_score": row.rule_ambiguity_score,
        "source_disagreement_score": row.source_disagreement_score,
        "edge_case_score": row.edge_case_score,
        "manual_review_score": row.manual_review_score,
        "ambiguity_score": row.ambiguity_score,
        "review_priority_score": row.review_priority_score,
        "status": row.status,
        "hard_flags": row.hard_flags,
        "reason_codes": row.reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _expected_public_report_digest(
    report: ResearchMarketResolutionRuleAmbiguityReport,
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
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True")
            _require_public_payload(item)
        return
    if type(value) is list:
        for item in value:
            _require_public_payload(item)
        return
    if value is None or type(value) in (bool, str):
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


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    return _quantize(decimal_value)


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.quantize(COUNT_QUANTUM):
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


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
    config: ResearchMarketResolutionRuleAmbiguityConfig,
) -> None:
    total = _quantize(
        config.rule_ambiguity_weight
        + config.source_disagreement_weight
        + config.edge_case_weight
        + config.manual_review_weight,
    )
    if total != ONE:
        raise ValueError("rule_ambiguity_weight must be part of weights totaling 1.000000")


def _require_row_weights_total_one(
    row: ResearchMarketResolutionRuleAmbiguityRow,
) -> None:
    total = _quantize(
        row.rule_ambiguity_weight
        + row.source_disagreement_weight
        + row.edge_case_weight
        + row.manual_review_weight,
    )
    if total != ONE:
        raise ValueError("rule_ambiguity_weight must be part of weights totaling 1.000000")
