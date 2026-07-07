"""Deterministic paper-only manual review checklist builder."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from typing import Any


__all__ = (
    "ResearchManualReviewChecklistConfig",
    "ResearchManualReviewChecklistCost",
    "ResearchManualReviewChecklistEvidence",
    "ResearchManualReviewChecklistItem",
    "ResearchManualReviewChecklistReasonCodeCount",
    "ResearchManualReviewChecklistReport",
    "ResearchManualReviewChecklistRule",
    "ResearchManualReviewChecklistScore",
    "ResearchManualReviewChecklistTeamStatus",
    "build_research_manual_review_checklist",
    "research_manual_review_checklist_payload",
)


CONFIG_VERSION = "research-manual-review-checklist-v1"
BOUNDARY_STATEMENT = "Paper-only readonly research checklist for manual review."
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_QUANTUM = Decimal("0.000001")
PUBLIC_STATUSES = ("pass", "watch", "block")
CATEGORY_ORDER = {
    "score": Decimal("1.000000"),
    "rule": Decimal("2.000000"),
    "evidence": Decimal("3.000000"),
    "cost": Decimal("4.000000"),
    "team_status": Decimal("5.000000"),
}
REQUIRED_CATEGORY_REASON_CODES = {
    "score": "missing_required_score",
    "rule": "missing_required_rule",
    "evidence": "missing_required_evidence",
    "cost": "missing_required_cost",
    "team_status": "missing_required_team_status",
}
PUBLIC_FORBIDDEN_FRAGMENTS = frozenset(
    (
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    ),
)
INPUT_LEAK_FRAGMENTS = PUBLIC_FORBIDDEN_FRAGMENTS | frozenset(
    (
        "http://",
        "https://",
        "polymarket",
        "slug",
        "market",
        "url",
        "ref",
        "raw",
    ),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(base, _FinalPublicDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchManualReviewChecklistConfig(_FinalPublicDataclass):
    config_version: str = CONFIG_VERSION
    boundary_statement: str = BOUNDARY_STATEMENT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchManualReviewChecklistConfig, "config")
        _require_public_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_public_string("boundary_statement", self.boundary_statement)
        _reject_public_leaks("config", self.boundary_statement)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchManualReviewChecklistScore(_FinalPublicDataclass):
    score_code: str
    score_value: Decimal
    pass_floor: Decimal
    watch_floor: Decimal
    redaction_check_text: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchManualReviewChecklistScore, "score")
        _require_input_code("score_code", self.score_code)
        object.__setattr__(self, "score_value", _require_ratio_decimal("score_value", self.score_value))
        object.__setattr__(self, "pass_floor", _require_ratio_decimal("pass_floor", self.pass_floor))
        object.__setattr__(self, "watch_floor", _require_ratio_decimal("watch_floor", self.watch_floor))
        if self.watch_floor > self.pass_floor:
            raise ValueError("watch_floor must not exceed pass_floor")
        _require_optional_input_text("redaction_check_text", self.redaction_check_text)
        _require_hard_flags("score", self)


@dataclass(frozen=True)
class ResearchManualReviewChecklistRule(_FinalPublicDataclass):
    rule_code: str
    rule_status: str
    redaction_check_text: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchManualReviewChecklistRule, "rule")
        _require_input_code("rule_code", self.rule_code)
        _require_public_status("rule_status", self.rule_status)
        _require_optional_input_text("redaction_check_text", self.redaction_check_text)
        _require_hard_flags("rule", self)


@dataclass(frozen=True)
class ResearchManualReviewChecklistEvidence(_FinalPublicDataclass):
    evidence_code: str
    evidence_status: str
    coverage_score: Decimal | None = None
    redaction_check_text: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchManualReviewChecklistEvidence, "evidence")
        _require_input_code("evidence_code", self.evidence_code)
        _require_public_status("evidence_status", self.evidence_status)
        if self.coverage_score is not None:
            object.__setattr__(
                self,
                "coverage_score",
                _require_ratio_decimal("coverage_score", self.coverage_score),
            )
        _require_optional_input_text("redaction_check_text", self.redaction_check_text)
        _require_hard_flags("evidence", self)


@dataclass(frozen=True)
class ResearchManualReviewChecklistCost(_FinalPublicDataclass):
    cost_code: str
    cost_ratio: Decimal
    watch_ceiling: Decimal
    block_ceiling: Decimal
    redaction_check_text: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchManualReviewChecklistCost, "cost")
        _require_input_code("cost_code", self.cost_code)
        object.__setattr__(self, "cost_ratio", _require_nonnegative_decimal("cost_ratio", self.cost_ratio))
        object.__setattr__(
            self,
            "watch_ceiling",
            _require_nonnegative_decimal("watch_ceiling", self.watch_ceiling),
        )
        object.__setattr__(
            self,
            "block_ceiling",
            _require_nonnegative_decimal("block_ceiling", self.block_ceiling),
        )
        if self.watch_ceiling > self.block_ceiling:
            raise ValueError("watch_ceiling must not exceed block_ceiling")
        _require_optional_input_text("redaction_check_text", self.redaction_check_text)
        _require_hard_flags("cost", self)


@dataclass(frozen=True)
class ResearchManualReviewChecklistTeamStatus(_FinalPublicDataclass):
    team_status_code: str
    team_status: str
    coverage_score: Decimal | None = None
    redaction_check_text: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchManualReviewChecklistTeamStatus, "team_status")
        _require_input_code("team_status_code", self.team_status_code)
        _require_public_status("team_status", self.team_status)
        if self.coverage_score is not None:
            object.__setattr__(
                self,
                "coverage_score",
                _require_ratio_decimal("coverage_score", self.coverage_score),
            )
        _require_optional_input_text("redaction_check_text", self.redaction_check_text)
        _require_hard_flags("team_status", self)


@dataclass(frozen=True)
class ResearchManualReviewChecklistItem(_FinalPublicDataclass):
    item_key: str
    category: str
    status: str
    metric_value: Decimal | None
    threshold_value: Decimal | None
    reason_codes: tuple[str, ...]
    review_prompt: str
    sort_key: Decimal = field(repr=False, compare=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchManualReviewChecklistItem, "item")
        _require_public_key("item_key", self.item_key)
        _require_category(self.category)
        _require_public_status("status", self.status)
        if self.metric_value is not None:
            object.__setattr__(
                self,
                "metric_value",
                _require_finite_decimal("metric_value", self.metric_value),
            )
        if self.threshold_value is not None:
            object.__setattr__(
                self,
                "threshold_value",
                _require_finite_decimal("threshold_value", self.threshold_value),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_public_string("review_prompt", self.review_prompt)
        _reject_public_leaks("review_prompt", self.review_prompt)
        object.__setattr__(self, "sort_key", _require_finite_decimal("sort_key", self.sort_key))
        _require_hard_flags("item", self)


@dataclass(frozen=True)
class ResearchManualReviewChecklistReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchManualReviewChecklistReasonCodeCount, "reason_code_count")
        object.__setattr__(
            self,
            "reason_code",
            _normalize_reason_codes("reason_code", (self.reason_code,))[0],
        )
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        if self.count <= ZERO:
            raise ValueError("count must be positive")
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchManualReviewChecklistReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    checklist_status: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    items: tuple[ResearchManualReviewChecklistItem, ...]
    reason_code_counts: tuple[ResearchManualReviewChecklistReasonCodeCount, ...]
    boundary_statement: str = BOUNDARY_STATEMENT
    source_scores: tuple[ResearchManualReviewChecklistScore, ...] = field(default=(), repr=False)
    source_rules: tuple[ResearchManualReviewChecklistRule, ...] = field(default=(), repr=False)
    source_evidence: tuple[ResearchManualReviewChecklistEvidence, ...] = field(default=(), repr=False)
    source_costs: tuple[ResearchManualReviewChecklistCost, ...] = field(default=(), repr=False)
    source_team_statuses: tuple[ResearchManualReviewChecklistTeamStatus, ...] = field(default=(), repr=False)
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchManualReviewChecklistReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if self.config_version != CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_public_status("checklist_status", self.checklist_status)
        for field_name in ("item_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "items", _normalize_items(self.items))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_public_string("boundary_statement", self.boundary_statement)
        _reject_public_leaks("boundary_statement", self.boundary_statement)
        object.__setattr__(
            self,
            "source_scores",
            _normalize_typed_tuple("source_scores", self.source_scores, ResearchManualReviewChecklistScore),
        )
        object.__setattr__(
            self,
            "source_rules",
            _normalize_typed_tuple("source_rules", self.source_rules, ResearchManualReviewChecklistRule),
        )
        object.__setattr__(
            self,
            "source_evidence",
            _normalize_typed_tuple(
                "source_evidence",
                self.source_evidence,
                ResearchManualReviewChecklistEvidence,
            ),
        )
        object.__setattr__(
            self,
            "source_costs",
            _normalize_typed_tuple("source_costs", self.source_costs, ResearchManualReviewChecklistCost),
        )
        object.__setattr__(
            self,
            "source_team_statuses",
            _normalize_typed_tuple(
                "source_team_statuses",
                self.source_team_statuses,
                ResearchManualReviewChecklistTeamStatus,
            ),
        )
        _validate_report_counts(self)
        _require_hard_flags("report", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match checklist payload")


def build_research_manual_review_checklist(
    *,
    scores: Iterable[ResearchManualReviewChecklistScore],
    rules: Iterable[ResearchManualReviewChecklistRule],
    evidence: Iterable[ResearchManualReviewChecklistEvidence],
    costs: Iterable[ResearchManualReviewChecklistCost],
    team_statuses: Iterable[ResearchManualReviewChecklistTeamStatus],
    generated_at: datetime,
    config: ResearchManualReviewChecklistConfig | None = None,
) -> ResearchManualReviewChecklistReport:
    checklist_config = ResearchManualReviewChecklistConfig() if config is None else config
    if type(checklist_config) is not ResearchManualReviewChecklistConfig:
        raise ValueError("config must be a ResearchManualReviewChecklistConfig")
    _require_hard_flags("config", checklist_config)
    generated = _as_utc("generated_at", generated_at)
    normalized_scores = tuple(sorted(_normalize_typed_iterable("scores", scores, ResearchManualReviewChecklistScore), key=lambda item: item.score_code))
    normalized_rules = tuple(sorted(_normalize_typed_iterable("rules", rules, ResearchManualReviewChecklistRule), key=lambda item: item.rule_code))
    normalized_evidence = tuple(sorted(_normalize_typed_iterable("evidence", evidence, ResearchManualReviewChecklistEvidence), key=lambda item: item.evidence_code))
    normalized_costs = tuple(sorted(_normalize_typed_iterable("costs", costs, ResearchManualReviewChecklistCost), key=lambda item: item.cost_code))
    normalized_team_statuses = tuple(sorted(_normalize_typed_iterable("team_statuses", team_statuses, ResearchManualReviewChecklistTeamStatus), key=lambda item: item.team_status_code))
    draft_items = (
        _score_items(normalized_scores)
        + _rule_items(normalized_rules)
        + _evidence_items(normalized_evidence)
        + _cost_items(normalized_costs)
        + _team_status_items(normalized_team_statuses)
    )
    items = _finalize_item_keys(_with_missing_category_items(draft_items))
    reason_code_counts = _reason_code_counts(items)
    return ResearchManualReviewChecklistReport(
        generated_at=generated,
        config_version=checklist_config.config_version,
        checklist_status=_rollup_status(items),
        item_count=_count(len(items)),
        pass_count=_count(sum(1 for item in items if item.status == "pass")),
        watch_count=_count(sum(1 for item in items if item.status == "watch")),
        block_count=_count(sum(1 for item in items if item.status == "block")),
        items=items,
        reason_code_counts=reason_code_counts,
        boundary_statement=checklist_config.boundary_statement,
        source_scores=normalized_scores,
        source_rules=normalized_rules,
        source_evidence=normalized_evidence,
        source_costs=normalized_costs,
        source_team_statuses=normalized_team_statuses,
    )


def research_manual_review_checklist_payload(
    report: ResearchManualReviewChecklistReport,
) -> dict[str, Any]:
    if type(report) is not ResearchManualReviewChecklistReport:
        raise ValueError("report must be a ResearchManualReviewChecklistReport")
    _require_hard_flags("report", report)
    _validate_report_counts(report)
    payload = _public_payload(report, include_digest=True)
    _reject_public_payload_leaks("payload", payload)
    return payload


def _score_items(
    scores: tuple[ResearchManualReviewChecklistScore, ...],
) -> tuple[ResearchManualReviewChecklistItem, ...]:
    items: list[ResearchManualReviewChecklistItem] = []
    for offset, score in enumerate(scores, start=1):
        if _input_has_leak(score.score_code, score.redaction_check_text):
            status = "block"
            reasons = ("unsafe_public_surface_block",)
        elif score.score_value >= score.pass_floor:
            status = "pass"
            reasons = ("score_pass_floor_met",)
        elif score.score_value >= score.watch_floor:
            status = "watch"
            reasons = ("score_watch_floor_met",)
        else:
            status = "block"
            reasons = ("score_below_watch_floor",)
        items.append(
            _draft_item(
                category="score",
                ordinal=offset,
                status=status,
                metric_value=score.score_value,
                threshold_value=score.pass_floor if status == "pass" else score.watch_floor,
                reason_codes=reasons,
                review_prompt="Human reviewer verifies redacted score inputs.",
            ),
        )
    return tuple(items)


def _rule_items(
    rules: tuple[ResearchManualReviewChecklistRule, ...],
) -> tuple[ResearchManualReviewChecklistItem, ...]:
    return tuple(
        _draft_item(
            category="rule",
            ordinal=offset,
            status="block" if _input_has_leak(rule.rule_code, rule.redaction_check_text) else rule.rule_status,
            metric_value=None,
            threshold_value=None,
            reason_codes=(
                ("unsafe_public_surface_block",)
                if _input_has_leak(rule.rule_code, rule.redaction_check_text)
                else (f"rule_status_{rule.rule_status}",)
            ),
            review_prompt="Human reviewer verifies redacted rule summary.",
        )
        for offset, rule in enumerate(rules, start=1)
    )


def _evidence_items(
    evidence: tuple[ResearchManualReviewChecklistEvidence, ...],
) -> tuple[ResearchManualReviewChecklistItem, ...]:
    return tuple(
        _draft_item(
            category="evidence",
            ordinal=offset,
            status=(
                "block"
                if _input_has_leak(item.evidence_code, item.redaction_check_text)
                else item.evidence_status
            ),
            metric_value=item.coverage_score,
            threshold_value=None,
            reason_codes=(
                ("unsafe_public_surface_block",)
                if _input_has_leak(item.evidence_code, item.redaction_check_text)
                else (f"evidence_status_{item.evidence_status}",)
            ),
            review_prompt="Human reviewer verifies redacted evidence coverage.",
        )
        for offset, item in enumerate(evidence, start=1)
    )


def _cost_items(
    costs: tuple[ResearchManualReviewChecklistCost, ...],
) -> tuple[ResearchManualReviewChecklistItem, ...]:
    items: list[ResearchManualReviewChecklistItem] = []
    for offset, cost in enumerate(costs, start=1):
        if _input_has_leak(cost.cost_code, cost.redaction_check_text):
            status = "block"
            reasons = ("unsafe_public_surface_block",)
            threshold_value = cost.block_ceiling
        elif cost.cost_ratio <= cost.watch_ceiling:
            status = "pass"
            reasons = ("cost_within_watch_ceiling",)
            threshold_value = cost.watch_ceiling
        elif cost.cost_ratio <= cost.block_ceiling:
            status = "watch"
            reasons = ("cost_above_watch_ceiling",)
            threshold_value = cost.block_ceiling
        else:
            status = "block"
            reasons = ("cost_above_block_ceiling",)
            threshold_value = cost.block_ceiling
        items.append(
            _draft_item(
                category="cost",
                ordinal=offset,
                status=status,
                metric_value=cost.cost_ratio,
                threshold_value=threshold_value,
                reason_codes=reasons,
                review_prompt="Human reviewer verifies redacted cost inputs.",
            ),
        )
    return tuple(items)


def _team_status_items(
    team_statuses: tuple[ResearchManualReviewChecklistTeamStatus, ...],
) -> tuple[ResearchManualReviewChecklistItem, ...]:
    return tuple(
        _draft_item(
            category="team_status",
            ordinal=offset,
            status=(
                "block"
                if _input_has_leak(item.team_status_code, item.redaction_check_text)
                else item.team_status
            ),
            metric_value=item.coverage_score,
            threshold_value=None,
            reason_codes=(
                ("unsafe_public_surface_block",)
                if _input_has_leak(item.team_status_code, item.redaction_check_text)
                else (f"team_status_{item.team_status}",)
            ),
            review_prompt="Human reviewer verifies redacted team state.",
        )
        for offset, item in enumerate(team_statuses, start=1)
    )


def _draft_item(
    *,
    category: str,
    ordinal: int,
    status: str,
    metric_value: Decimal | None,
    threshold_value: Decimal | None,
    reason_codes: tuple[str, ...],
    review_prompt: str,
) -> ResearchManualReviewChecklistItem:
    return ResearchManualReviewChecklistItem(
        item_key=f"{category}:draft",
        category=category,
        status=status,
        metric_value=metric_value,
        threshold_value=threshold_value,
        reason_codes=reason_codes,
        review_prompt=review_prompt,
        sort_key=CATEGORY_ORDER[category] + (Decimal(ordinal) / Decimal("1000000")),
    )


def _with_missing_category_items(
    items: tuple[ResearchManualReviewChecklistItem, ...],
) -> tuple[ResearchManualReviewChecklistItem, ...]:
    present = {item.category for item in items}
    missing_items = tuple(
        _draft_item(
            category=category,
            ordinal=999999,
            status="watch",
            metric_value=None,
            threshold_value=None,
            reason_codes=(reason_code,),
            review_prompt="Human reviewer verifies redacted input completeness.",
        )
        for category, reason_code in REQUIRED_CATEGORY_REASON_CODES.items()
        if category not in present
    )
    return tuple(sorted(items + missing_items, key=lambda item: item.sort_key))


def _finalize_item_keys(
    items: tuple[ResearchManualReviewChecklistItem, ...],
) -> tuple[ResearchManualReviewChecklistItem, ...]:
    return tuple(
        ResearchManualReviewChecklistItem(
            item_key=f"check_{_decimal_index(index)}",
            category=item.category,
            status=item.status,
            metric_value=item.metric_value,
            threshold_value=item.threshold_value,
            reason_codes=item.reason_codes,
            review_prompt=item.review_prompt,
            sort_key=item.sort_key,
        )
        for index, item in enumerate(items, start=1)
    )


def _reason_code_counts(
    items: tuple[ResearchManualReviewChecklistItem, ...],
) -> tuple[ResearchManualReviewChecklistReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for item in items:
        for reason_code in item.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchManualReviewChecklistReasonCodeCount(reason_code=reason_code, count=counts[reason_code])
        for reason_code in sorted(counts)
    )


def _rollup_status(items: tuple[ResearchManualReviewChecklistItem, ...]) -> str:
    if any(item.status == "block" for item in items):
        return "block"
    if any(item.status == "watch" for item in items):
        return "watch"
    return "pass"


def _validate_report_counts(report: ResearchManualReviewChecklistReport) -> None:
    if report.item_count != _count(len(report.items)):
        raise ValueError("item_count must match items")
    if report.pass_count != _count(sum(1 for item in report.items if item.status == "pass")):
        raise ValueError("pass_count must match items")
    if report.watch_count != _count(sum(1 for item in report.items if item.status == "watch")):
        raise ValueError("watch_count must match items")
    if report.block_count != _count(sum(1 for item in report.items if item.status == "block")):
        raise ValueError("block_count must match items")
    if report.checklist_status != _rollup_status(report.items):
        raise ValueError("checklist_status must match items")
    if report.reason_code_counts != _reason_code_counts(report.items):
        raise ValueError("reason_code_counts must match items")


def _public_payload(
    report: ResearchManualReviewChecklistReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_at": report.generated_at.astimezone(UTC).isoformat(),
        "config_version": report.config_version,
        "checklist_status": report.checklist_status,
        "item_count": str(report.item_count),
        "pass_count": str(report.pass_count),
        "watch_count": str(report.watch_count),
        "block_count": str(report.block_count),
        "items": [
            {
                "item_key": item.item_key,
                "category": item.category,
                "status": item.status,
                "metric_value": None if item.metric_value is None else str(item.metric_value),
                "threshold_value": (
                    None if item.threshold_value is None else str(item.threshold_value)
                ),
                "reason_codes": list(item.reason_codes),
                "review_prompt": item.review_prompt,
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            }
            for item in report.items
        ],
        "reason_code_counts": [
            {
                "reason_code": item.reason_code,
                "count": str(item.count),
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            }
            for item in report.reason_code_counts
        ],
        "boundary_statement": report.boundary_statement,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    _reject_public_payload_leaks("payload", payload)
    return payload


def _derived_validation_digest(report: ResearchManualReviewChecklistReport) -> str:
    encoded = json.dumps(
        _public_payload(report, include_digest=False),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _normalize_typed_iterable(
    field_name: str,
    values: Iterable[Any],
    expected_type: type,
) -> tuple[Any, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of {expected_type.__name__} values")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(
            f"{field_name} must be an iterable of {expected_type.__name__} values",
        ) from exc
    for value in normalized:
        if type(value) is not expected_type:
            raise ValueError(f"{field_name} must contain {expected_type.__name__} values")
    return normalized


def _normalize_typed_tuple(
    field_name: str,
    values: tuple[Any, ...],
    expected_type: type,
) -> tuple[Any, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for value in values:
        if type(value) is not expected_type:
            raise ValueError(f"{field_name} must contain {expected_type.__name__} values")
    return values


def _normalize_items(
    items: tuple[ResearchManualReviewChecklistItem, ...],
) -> tuple[ResearchManualReviewChecklistItem, ...]:
    normalized = _normalize_typed_tuple("items", items, ResearchManualReviewChecklistItem)
    expected = tuple(sorted(normalized, key=lambda item: item.sort_key))
    if normalized != expected:
        raise ValueError("items must be sorted deterministically")
    return normalized


def _normalize_reason_code_counts(
    values: tuple[ResearchManualReviewChecklistReasonCodeCount, ...],
) -> tuple[ResearchManualReviewChecklistReasonCodeCount, ...]:
    normalized = _normalize_typed_tuple(
        "reason_code_counts",
        values,
        ResearchManualReviewChecklistReasonCodeCount,
    )
    if normalized != tuple(sorted(normalized, key=lambda item: item.reason_code)):
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return normalized


def _normalize_reason_codes(field_name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized: list[str] = []
    for value in values:
        _require_public_key(field_name, value)
        normalized.append(value)
    return tuple(normalized)


def _require_exact_type(value: object, expected_type: type, label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_public_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")
    return value


def _require_category(value: str) -> str:
    if type(value) is not str or value not in CATEGORY_ORDER:
        raise ValueError("category must be a supported checklist category")
    return value


def _require_input_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be canonical")
    return value


def _require_public_key(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    text = value
    assert type(text) is str
    if any(character not in "abcdefghijklmnopqrstuvwxyz0123456789_:-" for character in text):
        raise ValueError(f"{field_name} must be a public key")
    _reject_public_leaks(field_name, text)
    return text


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be canonical")
    return value


def _require_optional_input_text(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be canonical")
    return value


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(DECIMAL_QUANTUM)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most 1.000000")
    return decimal_value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(DECIMAL_QUANTUM)


def _decimal_index(value: int) -> str:
    return f"{value:06d}"


def _input_has_leak(*values: str | None) -> bool:
    for value in values:
        if value is None:
            continue
        normalized = value.lower()
        if any(fragment in normalized for fragment in INPUT_LEAK_FRAGMENTS):
            return True
    return False


def _reject_public_payload_leaks(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_public_leaks(label, key)
            _reject_public_payload_leaks(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_payload_leaks(label, item)
        return
    if type(value) is str:
        _reject_public_leaks(label, value)


def _reject_public_leaks(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in PUBLIC_FORBIDDEN_FRAGMENTS):
        raise ValueError(f"unsafe public value in {label}")
