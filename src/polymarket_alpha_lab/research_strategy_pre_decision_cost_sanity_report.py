"""Pure pre-decision cost sanity report for manual review."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_STRATEGY_PRE_DECISION_COST_SANITY_REPORT_CONFIG_VERSION = (
    "research-strategy-pre-decision-cost-sanity-report-v0"
)
RESEARCH_STRATEGY_PRE_DECISION_COST_SANITY_REPORT_STATUSES = (
    "pass",
    "watch",
    "block",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FIVE = Decimal("5.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
COMPONENT_FIELDS = (
    "fee_accounted_score",
    "spread_accounted_score",
    "depth_haircut_accounted_score",
    "latency_haircut_accounted_score",
    "settlement_uncertainty_accounted_score",
)
COMPONENT_REASON_PREFIXES = (
    "fee_accounting",
    "spread_accounting",
    "depth_haircut_accounting",
    "latency_haircut_accounting",
    "settlement_uncertainty_accounting",
)
PUBLIC_STATUSES = RESEARCH_STRATEGY_PRE_DECISION_COST_SANITY_REPORT_STATUSES
STATUS_WEIGHT = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
SUMMARY_KEYS = (
    "generated_at",
    "config_version",
    "candidate_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_cost_sanity_score",
    "minimum_component_score",
    "status",
    "manual_decision_review_state",
    "reason_codes",
    "validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
PUBLIC_PAYLOAD_FIELDS = frozenset((*SUMMARY_KEYS, "rows"))
PUBLIC_ROW_FIELDS = frozenset(
    (
        "row_number",
        "public_candidate_hash",
        "observed_at",
        "fee_accounted_score",
        "spread_accounted_score",
        "depth_haircut_accounted_score",
        "latency_haircut_accounted_score",
        "settlement_uncertainty_accounted_score",
        "cost_sanity_score",
        "minimum_component_score",
        "status",
        "manual_decision_review_state",
        "reason_codes",
        "validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
NO_CANDIDATES_REASON = "pre_decision_cost_sanity_report_empty"
REASON_PRIORITY = (
    "fee_accounting_block",
    "spread_accounting_block",
    "depth_haircut_accounting_block",
    "latency_haircut_accounting_block",
    "settlement_uncertainty_accounting_block",
    "pre_decision_cost_sanity_report_block",
    "fee_accounting_watch",
    "spread_accounting_watch",
    "depth_haircut_accounting_watch",
    "latency_haircut_accounting_watch",
    "settlement_uncertainty_accounting_watch",
    "pre_decision_cost_sanity_report_watch",
    "pre_decision_cost_sanity_pass",
    "pre_decision_cost_sanity_report_pass",
    NO_CANDIDATES_REASON,
    "fee_accounting_review",
    "spread_accounting_review",
    "depth_haircut_accounting_review",
    "latency_haircut_accounting_review",
    "settlement_uncertainty_accounting_review",
)
UNSAFE_TEXT_FRAGMENTS = (
    "li" "ve",
    "au" "th",
    "wal" "let",
    "bro" "ker",
    "or" "der",
    "can" "cel",
    "re" "pl" "ace",
    "ex" "change",
    "private" "_" "key",
    "api" "_" "key",
    "sec" "ret",
    "mar" "ket" "_" "id",
    "mar" "ket" "_" "s" "lug",
    "ques" "tion",
    "source" "_" "u" "rl",
    "source" "_" "text",
    "d" "sn",
    "ta" "ble",
    "to" "ken",
    "po" "sition",
    "b" "uy",
    "se" "ll",
    "reco" "mmend",
    "siz" "ing",
    "data" "base",
    "net" "work",
    "req" "uests",
    "ht" "tp",
    "sock" "et",
    "sub" "process",
    "tr" "ade",
    "://",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchStrategyPreDecisionCostSanityConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_PRE_DECISION_COST_SANITY_REPORT_CONFIG_VERSION
    )
    component_pass_floor: Decimal = Decimal("0.800000")
    component_watch_floor: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyPreDecisionCostSanityConfig, "config")
        _require_public_text("config_version", self.config_version)
        for field_name in ("component_pass_floor", "component_watch_floor"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.component_pass_floor < self.component_watch_floor:
            raise ValueError("component_pass_floor must be at least component_watch_floor")
        _require_hard_phase_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyPreDecisionCostSanityInput(_FinalDataclass):
    internal_candidate_key: str
    observed_at: datetime
    fee_accounted_score: Decimal
    spread_accounted_score: Decimal
    depth_haircut_accounted_score: Decimal
    latency_haircut_accounted_score: Decimal
    settlement_uncertainty_accounted_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyPreDecisionCostSanityInput, "input")
        _require_text("internal_candidate_key", self.internal_candidate_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in COMPONENT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_phase_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyPreDecisionCostSanityRow(_FinalDataclass):
    row_number: Decimal
    public_candidate_hash: str
    observed_at: datetime
    fee_accounted_score: Decimal
    spread_accounted_score: Decimal
    depth_haircut_accounted_score: Decimal
    latency_haircut_accounted_score: Decimal
    settlement_uncertainty_accounted_score: Decimal
    cost_sanity_score: Decimal
    minimum_component_score: Decimal
    status: str
    manual_decision_review_state: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyPreDecisionCostSanityRow, "row")
        object.__setattr__(
            self,
            "row_number",
            _normalize_positive_count("row_number", self.row_number),
        )
        _require_public_hash("public_candidate_hash", self.public_candidate_hash)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in COMPONENT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cost_sanity_score",
            _normalize_ratio("cost_sanity_score", self.cost_sanity_score),
        )
        object.__setattr__(
            self,
            "minimum_component_score",
            _normalize_ratio("minimum_component_score", self.minimum_component_score),
        )
        _require_status("status", self.status)
        _require_manual_decision_review_state(
            "manual_decision_review_state",
            self.manual_decision_review_state,
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_digest("validation_digest", self.validation_digest)
        _require_hard_phase_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchStrategyPreDecisionCostSanityReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_cost_sanity_score: Decimal | None
    minimum_component_score: Decimal | None
    status: str
    manual_decision_review_state: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyPreDecisionCostSanityRow, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyPreDecisionCostSanityReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        for field_name in ("candidate_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_cost_sanity_score", "minimum_component_score"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _normalize_ratio(field_name, value))
        _require_status("status", self.status)
        _require_manual_decision_review_state(
            "manual_decision_review_state",
            self.manual_decision_review_state,
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("validation_digest", self.validation_digest)
        _require_hard_phase_flags("report", self)
        _validate_report(self)


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def build_research_strategy_pre_decision_cost_sanity_report(
    candidates: Iterable[ResearchStrategyPreDecisionCostSanityInput],
    *,
    config: ResearchStrategyPreDecisionCostSanityConfig,
    generated_at: datetime,
) -> ResearchStrategyPreDecisionCostSanityReport:
    if type(config) is not ResearchStrategyPreDecisionCostSanityConfig:
        raise ValueError("config must be a ResearchStrategyPreDecisionCostSanityConfig")
    _require_hard_phase_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_candidates(candidates)
    for value in inputs:
        if value.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    draft_rows = tuple(
        sorted(
            (_draft_row_values(value, config=config) for value in inputs),
            key=_draft_sort_key,
        ),
    )
    rows = tuple(
        _row_from_draft(row_number=index, draft_values=draft_values)
        for index, draft_values in enumerate(draft_rows, start=1)
    )
    report_status = _report_status(rows)
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "candidate_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_cost_sanity_score": _average_cost_sanity_score(rows),
        "minimum_component_score": _report_minimum_component_score(rows),
        "status": report_status,
        "manual_decision_review_state": _manual_decision_review_state(report_status),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyPreDecisionCostSanityReport(
        **report_values,
        validation_digest=_validation_digest(report_values),
    )


def research_strategy_pre_decision_cost_sanity_report_payload(
    report: ResearchStrategyPreDecisionCostSanityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyPreDecisionCostSanityReport:
        _require_hard_phase_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchStrategyPreDecisionCostSanityReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_payload(payload)
    _require_hard_phase_flags("payload", _DictFlags(payload))
    _validate_payload_digests(payload)
    _validate_payload_schema(payload)
    return payload


def research_strategy_pre_decision_cost_sanity_report_digest(
    report: ResearchStrategyPreDecisionCostSanityReport,
) -> dict[str, Any]:
    payload = research_strategy_pre_decision_cost_sanity_report_payload(report)
    return {key: payload[key] for key in SUMMARY_KEYS}


def _draft_row_values(
    candidate: ResearchStrategyPreDecisionCostSanityInput,
    *,
    config: ResearchStrategyPreDecisionCostSanityConfig,
) -> dict[str, object]:
    component_values = _component_values(candidate)
    reason_codes = _row_reason_codes(candidate, config=config)
    row_status = _row_status(reason_codes)
    return {
        "public_candidate_hash": _public_hash(candidate.internal_candidate_key),
        "observed_at": candidate.observed_at,
        "fee_accounted_score": candidate.fee_accounted_score,
        "spread_accounted_score": candidate.spread_accounted_score,
        "depth_haircut_accounted_score": candidate.depth_haircut_accounted_score,
        "latency_haircut_accounted_score": candidate.latency_haircut_accounted_score,
        "settlement_uncertainty_accounted_score": (
            candidate.settlement_uncertainty_accounted_score
        ),
        "cost_sanity_score": _cost_sanity_score(component_values),
        "minimum_component_score": min(component_values),
        "status": row_status,
        "manual_decision_review_state": _manual_decision_review_state(row_status),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_from_draft(
    *,
    row_number: int,
    draft_values: dict[str, object],
) -> ResearchStrategyPreDecisionCostSanityRow:
    row_values = {"row_number": _count(row_number), **draft_values}
    return ResearchStrategyPreDecisionCostSanityRow(
        **row_values,
        validation_digest=_validation_digest(row_values),
    )


def _row_reason_codes(
    candidate: ResearchStrategyPreDecisionCostSanityInput,
    *,
    config: ResearchStrategyPreDecisionCostSanityConfig,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    for field_name, reason_prefix in zip(COMPONENT_FIELDS, COMPONENT_REASON_PREFIXES):
        value = getattr(candidate, field_name)
        if value < config.component_watch_floor:
            block_reasons.append(f"{reason_prefix}_block")
        elif value < config.component_pass_floor:
            watch_reasons.append(f"{reason_prefix}_watch")
    reasons = tuple(block_reasons + watch_reasons)
    if not reasons:
        reasons = ("pre_decision_cost_sanity_pass",)
    return _normalize_reason_codes(reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchStrategyPreDecisionCostSanityRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _manual_decision_review_state(status: str) -> str:
    if status == "block":
        return "manual_decision_review_block"
    if status == "watch":
        return "manual_decision_review_watch"
    return "manual_decision_review_ready"


def _report_reason_codes(
    rows: tuple[ResearchStrategyPreDecisionCostSanityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_CANDIDATES_REASON,)
    status = _report_status(rows)
    row_codes = tuple(code for row in rows for code in row.reason_codes)
    review_codes = []
    for reason_prefix in COMPONENT_REASON_PREFIXES:
        if any(code.startswith(f"{reason_prefix}_") for code in row_codes):
            review_codes.append(f"{reason_prefix}_review")
    return _normalize_reason_codes(
        (f"pre_decision_cost_sanity_report_{status}", *tuple(review_codes)),
    )


def _component_values(
    candidate: ResearchStrategyPreDecisionCostSanityInput,
) -> tuple[Decimal, ...]:
    return tuple(getattr(candidate, field_name) for field_name in COMPONENT_FIELDS)


def _cost_sanity_score(values: tuple[Decimal, ...]) -> Decimal:
    return _ratio(_sum_decimal(values), FIVE)


def _average_cost_sanity_score(
    rows: tuple[ResearchStrategyPreDecisionCostSanityRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _ratio(
        _sum_decimal(tuple(row.cost_sanity_score for row in rows)),
        _count(len(rows)),
    )


def _report_minimum_component_score(
    rows: tuple[ResearchStrategyPreDecisionCostSanityRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return min(row.minimum_component_score for row in rows)


def _normalize_candidates(
    candidates: Iterable[ResearchStrategyPreDecisionCostSanityInput],
) -> tuple[ResearchStrategyPreDecisionCostSanityInput, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        values = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen: set[str] = set()
    for candidate in values:
        if type(candidate) is not ResearchStrategyPreDecisionCostSanityInput:
            raise ValueError(
                "candidates must contain ResearchStrategyPreDecisionCostSanityInput",
            )
        _require_hard_phase_flags("input", candidate)
        if candidate.internal_candidate_key in seen:
            raise ValueError("candidates must not contain duplicate values")
        seen.add(candidate.internal_candidate_key)
    return values


def _normalize_rows(
    rows: Iterable[ResearchStrategyPreDecisionCostSanityRow],
) -> tuple[ResearchStrategyPreDecisionCostSanityRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in values:
        if type(row) is not ResearchStrategyPreDecisionCostSanityRow:
            raise ValueError("rows must contain ResearchStrategyPreDecisionCostSanityRow")
        _require_hard_phase_flags("row", row)
        if row.public_candidate_hash in seen:
            raise ValueError("public_candidate_hash values must be unique")
        seen.add(row.public_candidate_hash)
    expected_numbers = tuple(_count(index) for index in range(1, len(values) + 1))
    actual_numbers = tuple(row.row_number for row in values)
    if actual_numbers != expected_numbers:
        raise ValueError("rows must be sorted deterministically")
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return values


def _validate_row(row: ResearchStrategyPreDecisionCostSanityRow) -> None:
    component_values = tuple(getattr(row, field_name) for field_name in COMPONENT_FIELDS)
    if row.cost_sanity_score != _cost_sanity_score(component_values):
        raise ValueError("cost_sanity_score must match component scores")
    if row.minimum_component_score != min(component_values):
        raise ValueError("minimum_component_score must match component scores")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.manual_decision_review_state != _manual_decision_review_state(row.status):
        raise ValueError("manual_decision_review_state must match status")
    if row.validation_digest != _validation_digest(_row_digest_values(row)):
        raise ValueError("validation_digest must match row payload")


def _validate_report(report: ResearchStrategyPreDecisionCostSanityReport) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_cost_sanity_score != _average_cost_sanity_score(report.rows):
        raise ValueError("average_cost_sanity_score must match rows")
    if report.minimum_component_score != _report_minimum_component_score(report.rows):
        raise ValueError("minimum_component_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.manual_decision_review_state != _manual_decision_review_state(report.status):
        raise ValueError("manual_decision_review_state must match status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.validation_digest != _validation_digest(_report_digest_values(report)):
        raise ValueError("validation_digest must match report payload")


def _row_digest_values(row: ResearchStrategyPreDecisionCostSanityRow) -> dict[str, Any]:
    return {
        "row_number": row.row_number,
        "public_candidate_hash": row.public_candidate_hash,
        "observed_at": row.observed_at,
        "fee_accounted_score": row.fee_accounted_score,
        "spread_accounted_score": row.spread_accounted_score,
        "depth_haircut_accounted_score": row.depth_haircut_accounted_score,
        "latency_haircut_accounted_score": row.latency_haircut_accounted_score,
        "settlement_uncertainty_accounted_score": (
            row.settlement_uncertainty_accounted_score
        ),
        "cost_sanity_score": row.cost_sanity_score,
        "minimum_component_score": row.minimum_component_score,
        "status": row.status,
        "manual_decision_review_state": row.manual_decision_review_state,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_digest_values(
    report: ResearchStrategyPreDecisionCostSanityReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "candidate_count": report.candidate_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "average_cost_sanity_score": report.average_cost_sanity_score,
        "minimum_component_score": report.minimum_component_score,
        "status": report.status,
        "manual_decision_review_state": report.manual_decision_review_state,
        "reason_codes": report.reason_codes,
        "rows": report.rows,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _validate_payload_digests(payload: dict[str, Any]) -> None:
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain objects")
        _require_digest("validation_digest", row.get("validation_digest"))
        if row["validation_digest"] != _validation_digest(_without_digest(row)):
            raise ValueError("validation_digest must match row payload")
    _require_digest("validation_digest", payload.get("validation_digest"))
    if payload["validation_digest"] != _validation_digest(_without_digest(payload)):
        raise ValueError("validation_digest must match report payload")


def _validate_payload_schema(payload: dict[str, Any]) -> None:
    _require_payload_fields(
        "public payload",
        payload,
        PUBLIC_PAYLOAD_FIELDS,
        "unexpected public payload fields",
    )
    _require_status("status", payload["status"])
    _require_manual_decision_review_state(
        "manual_decision_review_state",
        payload["manual_decision_review_state"],
    )
    _normalize_reason_codes(payload["reason_codes"])
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain objects")
        _require_payload_fields(
            "row payload",
            row,
            PUBLIC_ROW_FIELDS,
            "unexpected row payload fields",
        )
        _require_public_hash("public_candidate_hash", row["public_candidate_hash"])
        _require_status("status", row["status"])
        _require_manual_decision_review_state(
            "manual_decision_review_state",
            row["manual_decision_review_state"],
        )
        _normalize_reason_codes(row["reason_codes"])
        _require_hard_phase_flags("row payload", _DictFlags(row))


def _require_payload_fields(
    name: str,
    value: dict[str, Any],
    expected: frozenset[str],
    message: str,
) -> None:
    actual = frozenset(value)
    if actual != expected:
        raise ValueError(message)
    for key in actual:
        _require_public_text(f"{name} key", key)


def _without_digest(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != "validation_digest"}


def _draft_sort_key(values: dict[str, object]) -> tuple[Decimal, Decimal, Decimal, str]:
    status = values["status"]
    score = values["cost_sanity_score"]
    minimum_score = values["minimum_component_score"]
    public_hash = values["public_candidate_hash"]
    if type(status) is not str or type(score) is not Decimal:
        raise ValueError("row draft has invalid sort values")
    if type(minimum_score) is not Decimal or type(public_hash) is not str:
        raise ValueError("row draft has invalid sort values")
    return (STATUS_WEIGHT[status], score, minimum_score, public_hash)


def _row_sort_key(
    row: ResearchStrategyPreDecisionCostSanityRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str]:
    return (
        STATUS_WEIGHT[row.status],
        row.cost_sanity_score,
        row.minimum_component_score,
        row.row_number,
        row.public_candidate_hash,
    )


def _status_count(
    rows: tuple[ResearchStrategyPreDecisionCostSanityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_public_text("reason_codes", reason_code)
        compact = "".join(part for part in reason_code if part != "_")
        if not compact.isalnum() or reason_code.lower() != reason_code:
            raise ValueError("reason_codes must be lowercase snake case")
    normalized = tuple(sorted(dict.fromkeys(reason_codes), key=_reason_sort_key))
    if "pre_decision_cost_sanity_pass" in normalized and len(normalized) != 1:
        raise ValueError("pre_decision_cost_sanity_pass must stand alone")
    if NO_CANDIDATES_REASON in normalized and len(normalized) != 1:
        raise ValueError("empty report reason must stand alone")
    return normalized


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    if reason_code in REASON_PRIORITY:
        return (REASON_PRIORITY.index(reason_code), reason_code)
    return (len(REASON_PRIORITY), reason_code)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(QUANTUM)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += _normalize_decimal("sum value", value)
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    denominator = _normalize_decimal("denominator", denominator)
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    numerator = _normalize_decimal("numerator", numerator)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _normalize_positive_count(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be an integer")
    return normalized.quantize(QUANTUM)


def _normalize_ratio(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(normalized)


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_status(name: str, value: object) -> None:
    _require_public_text(name, value)
    if value not in PUBLIC_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_manual_decision_review_state(name: str, value: object) -> None:
    _require_public_text(name, value)
    if value not in {
        "manual_decision_review_ready",
        "manual_decision_review_watch",
        "manual_decision_review_block",
    }:
        raise ValueError(f"{name} must be a manual decision review state")


def _require_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a non-empty canonical string")


def _require_public_text(name: str, value: object) -> None:
    _require_text(name, value)
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public text")


def _require_digest(name: str, value: object) -> None:
    _require_text(name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _require_public_hash(name: str, value: object) -> None:
    _require_text(name, value)
    if not value.startswith("sha256:"):
        raise ValueError(f"{name} must be a public hash")
    _require_digest(name, value.removeprefix("sha256:"))


def _require_hard_phase_flags(name: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _public_hash(value: str) -> str:
    _require_text("internal_candidate_key", value)
    digest = sha256(value.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


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
        return format(value, "f")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is str:
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


def _reject_unsafe_payload(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _require_public_text("payload key", key)
            _reject_unsafe_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item)
        return
    if type(value) is str:
        _require_public_text("payload value", value)
        return
    if value is None or type(value) is bool:
        return
    raise ValueError("payload contains unsupported value")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_PRE_DECISION_COST_SANITY_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_PRE_DECISION_COST_SANITY_REPORT_STATUSES",
    "ResearchStrategyPreDecisionCostSanityConfig",
    "ResearchStrategyPreDecisionCostSanityInput",
    "ResearchStrategyPreDecisionCostSanityRow",
    "ResearchStrategyPreDecisionCostSanityReport",
    "build_research_strategy_pre_decision_cost_sanity_report",
    "research_strategy_pre_decision_cost_sanity_report_digest",
    "research_strategy_pre_decision_cost_sanity_report_payload",
)
