"""Pure strategy decision evidence balance report."""

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
    "DEFAULT_RESEARCH_STRATEGY_DECISION_EVIDENCE_BALANCE_REPORT_CONFIG_VERSION",
    "ResearchStrategyDecisionEvidenceBalanceCandidate",
    "ResearchStrategyDecisionEvidenceBalanceConfig",
    "ResearchStrategyDecisionEvidenceBalanceReasonCodeCount",
    "ResearchStrategyDecisionEvidenceBalanceReport",
    "ResearchStrategyDecisionEvidenceBalanceRow",
    "build_research_strategy_decision_evidence_balance_report",
    "research_strategy_decision_evidence_balance_report_digest",
    "research_strategy_decision_evidence_balance_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_DECISION_EVIDENCE_BALANCE_REPORT_CONFIG_VERSION = (
    "research-strategy-decision-evidence-balance-report-v0"
)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FIVE = Decimal("5.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
NO_INPUTS_REASON = "decision_evidence_balance_no_inputs"
REPORT_REASON_PRIORITY = (
    "evidence_balance_imbalance_block",
    "evidence_balance_imbalance_watch",
    "market_mechanics_block",
    "market_mechanics_watch",
    "probability_model_block",
    "probability_model_watch",
    "resolution_risk_block",
    "resolution_risk_watch",
    "source_corroboration_block",
    "source_corroboration_watch",
    "team_memory_block",
    "team_memory_watch",
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_TEXT_PARTS = (
    _join_parts("raw", "_candidate", "_id"),
    _join_parts("mar", "ket", "_id"),
    _join_parts("mar", "ket", "_sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("sou", "rce", "_u", "rl"),
    _join_parts("sou", "rce", "_te", "xt"),
    _join_parts("d", "sn"),
    _join_parts("ta", "ble", "_na", "me"),
    _join_parts("pri", "vate", "_to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("tra", "ding"),
    _join_parts("posi", "tion", "_si", "ze"),
    _join_parts("b", "uy"),
    _join_parts("se", "ll"),
    _join_parts("rec", "ommend"),
    _join_parts("siz", "ing"),
    _join_parts("au", "th"),
    _join_parts("data", "base"),
    _join_parts("net", "work"),
    _join_parts("req", "uests"),
    _join_parts("ht", "tp"),
    _join_parts("so", "cket"),
    _join_parts("sub", "process"),
    _join_parts("sec", "ret"),
    _join_parts("api", "_key"),
    "://",
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
class ResearchStrategyDecisionEvidenceBalanceConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_DECISION_EVIDENCE_BALANCE_REPORT_CONFIG_VERSION
    )
    probability_model_pass_floor: Decimal = Decimal("0.800000")
    probability_model_watch_floor: Decimal = Decimal("0.600000")
    team_memory_pass_floor: Decimal = Decimal("0.800000")
    team_memory_watch_floor: Decimal = Decimal("0.600000")
    source_corroboration_pass_floor: Decimal = Decimal("0.800000")
    source_corroboration_watch_floor: Decimal = Decimal("0.600000")
    market_mechanics_pass_floor: Decimal = Decimal("0.800000")
    market_mechanics_watch_floor: Decimal = Decimal("0.600000")
    resolution_risk_pass_floor: Decimal = Decimal("0.800000")
    resolution_risk_watch_floor: Decimal = Decimal("0.600000")
    imbalance_watch_threshold: Decimal = Decimal("0.250000")
    imbalance_block_threshold: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDecisionEvidenceBalanceConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DECISION_EVIDENCE_BALANCE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "probability_model_pass_floor",
            "probability_model_watch_floor",
            "team_memory_pass_floor",
            "team_memory_watch_floor",
            "source_corroboration_pass_floor",
            "source_corroboration_watch_floor",
            "market_mechanics_pass_floor",
            "market_mechanics_watch_floor",
            "resolution_risk_pass_floor",
            "resolution_risk_watch_floor",
            "imbalance_watch_threshold",
            "imbalance_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name, lower_name in (
            ("probability_model_pass_floor", "probability_model_watch_floor"),
            ("team_memory_pass_floor", "team_memory_watch_floor"),
            ("source_corroboration_pass_floor", "source_corroboration_watch_floor"),
            ("market_mechanics_pass_floor", "market_mechanics_watch_floor"),
            ("resolution_risk_pass_floor", "resolution_risk_watch_floor"),
            ("imbalance_block_threshold", "imbalance_watch_threshold"),
        ):
            _require_at_least(field_name, getattr(self, field_name), getattr(self, lower_name))
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyDecisionEvidenceBalanceCandidate(_FinalPublicDataclass):
    evidence_key: str
    probability_model_score: Decimal
    team_memory_score: Decimal
    source_corroboration_score: Decimal
    market_mechanics_score: Decimal
    resolution_risk_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDecisionEvidenceBalanceCandidate, "candidate")
        _require_canonical_string("evidence_key", self.evidence_key)
        for field_name in (
            "probability_model_score",
            "team_memory_score",
            "source_corroboration_score",
            "market_mechanics_score",
            "resolution_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("candidate", self)
        _reject_unsafe_public_payload("candidate", self)


@dataclass(frozen=True)
class ResearchStrategyDecisionEvidenceBalanceRow(_FinalPublicDataclass):
    aggregate_row_number: Decimal
    aggregate_row_hash: str
    status: str
    probability_model_score: Decimal
    team_memory_score: Decimal
    source_corroboration_score: Decimal
    market_mechanics_score: Decimal
    resolution_risk_score: Decimal
    evidence_balance_score: Decimal
    evidence_imbalance_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDecisionEvidenceBalanceRow, "row")
        object.__setattr__(
            self,
            "aggregate_row_number",
            _normalize_positive_count("aggregate_row_number", self.aggregate_row_number),
        )
        _require_public_digest("aggregate_row_hash", self.aggregate_row_hash)
        _require_status("status", self.status)
        for field_name in (
            "probability_model_score",
            "team_memory_score",
            "source_corroboration_score",
            "market_mechanics_score",
            "resolution_risk_score",
            "evidence_balance_score",
            "evidence_imbalance_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.status != _row_status(self.reason_codes):
            raise ValueError("status must match reason_codes")
        if self.evidence_balance_score != _evidence_balance_score(
            self.probability_model_score,
            self.team_memory_score,
            self.source_corroboration_score,
            self.market_mechanics_score,
            self.resolution_risk_score,
        ):
            raise ValueError("evidence_balance_score must match scores")
        if self.evidence_imbalance_score != _evidence_imbalance_score(
            self.probability_model_score,
            self.team_memory_score,
            self.source_corroboration_score,
            self.market_mechanics_score,
            self.resolution_risk_score,
        ):
            raise ValueError("evidence_imbalance_score must match scores")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyDecisionEvidenceBalanceReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDecisionEvidenceBalanceReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyDecisionEvidenceBalanceReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    probability_model_attention_count: Decimal
    team_memory_attention_count: Decimal
    source_corroboration_attention_count: Decimal
    market_mechanics_attention_count: Decimal
    resolution_risk_attention_count: Decimal
    balance_imbalance_attention_count: Decimal
    mean_probability_model_score: Decimal
    mean_team_memory_score: Decimal
    mean_source_corroboration_score: Decimal
    mean_market_mechanics_score: Decimal
    mean_resolution_risk_score: Decimal
    mean_evidence_balance_score: Decimal
    max_evidence_imbalance_score: Decimal
    status: str
    public_digest: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategyDecisionEvidenceBalanceReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchStrategyDecisionEvidenceBalanceRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDecisionEvidenceBalanceReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "probability_model_attention_count",
            "team_memory_attention_count",
            "source_corroboration_attention_count",
            "market_mechanics_attention_count",
            "resolution_risk_attention_count",
            "balance_imbalance_attention_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_probability_model_score",
            "mean_team_memory_score",
            "mean_source_corroboration_score",
            "mean_market_mechanics_score",
            "mean_resolution_risk_score",
            "mean_evidence_balance_score",
            "max_evidence_imbalance_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_public_digest("public_digest", self.public_digest)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        if self.public_digest != _computed_report_digest(self):
            raise ValueError("public_digest must match report values")
        _reject_unsafe_public_payload("report", self)


_PUBLIC_DATACLASS_TYPES = (
    ResearchStrategyDecisionEvidenceBalanceCandidate,
    ResearchStrategyDecisionEvidenceBalanceConfig,
    ResearchStrategyDecisionEvidenceBalanceReasonCodeCount,
    ResearchStrategyDecisionEvidenceBalanceReport,
    ResearchStrategyDecisionEvidenceBalanceRow,
)


def build_research_strategy_decision_evidence_balance_report(
    candidates: Iterable[ResearchStrategyDecisionEvidenceBalanceCandidate],
    *,
    config: ResearchStrategyDecisionEvidenceBalanceConfig,
    generated_at: datetime,
) -> ResearchStrategyDecisionEvidenceBalanceReport:
    if type(config) is not ResearchStrategyDecisionEvidenceBalanceConfig:
        raise ValueError("config must be a ResearchStrategyDecisionEvidenceBalanceConfig")
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(candidates)
    row_values = sorted(
        (_row_values_for_input(value, config=config) for value in inputs),
        key=_row_values_sort_key,
    )
    rows = tuple(
        _row_from_values(_count(index), values)
        for index, values in enumerate(row_values, start=1)
    )
    values = _report_values(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        rows=rows,
    )
    return ResearchStrategyDecisionEvidenceBalanceReport(
        **values,
        public_digest=_digest_from_mapping(values),
    )


def research_strategy_decision_evidence_balance_report_digest(
    report: ResearchStrategyDecisionEvidenceBalanceReport,
) -> str:
    if type(report) is not ResearchStrategyDecisionEvidenceBalanceReport:
        raise ValueError("report must be a ResearchStrategyDecisionEvidenceBalanceReport")
    _revalidate_report_for_payload(report)
    return _computed_report_digest(report)


def research_strategy_decision_evidence_balance_report_payload(
    report: ResearchStrategyDecisionEvidenceBalanceReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyDecisionEvidenceBalanceReport:
        raise ValueError("report must be a ResearchStrategyDecisionEvidenceBalanceReport")
    _reject_unsafe_public_payload("report", report)
    _revalidate_report_for_payload(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


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


@dataclass(frozen=True)
class _RowValues:
    aggregate_row_hash: str
    status: str
    probability_model_score: Decimal
    team_memory_score: Decimal
    source_corroboration_score: Decimal
    market_mechanics_score: Decimal
    resolution_risk_score: Decimal
    evidence_balance_score: Decimal
    evidence_imbalance_score: Decimal
    reason_codes: tuple[str, ...]


def _row_values_for_input(
    value: ResearchStrategyDecisionEvidenceBalanceCandidate,
    *,
    config: ResearchStrategyDecisionEvidenceBalanceConfig,
) -> _RowValues:
    reason_codes = _row_reason_codes(value, config=config)
    return _RowValues(
        aggregate_row_hash=_public_hash(value.evidence_key),
        status=_row_status(reason_codes),
        probability_model_score=value.probability_model_score,
        team_memory_score=value.team_memory_score,
        source_corroboration_score=value.source_corroboration_score,
        market_mechanics_score=value.market_mechanics_score,
        resolution_risk_score=value.resolution_risk_score,
        evidence_balance_score=_evidence_balance_score(
            value.probability_model_score,
            value.team_memory_score,
            value.source_corroboration_score,
            value.market_mechanics_score,
            value.resolution_risk_score,
        ),
        evidence_imbalance_score=_evidence_imbalance_score(
            value.probability_model_score,
            value.team_memory_score,
            value.source_corroboration_score,
            value.market_mechanics_score,
            value.resolution_risk_score,
        ),
        reason_codes=reason_codes,
    )


def _row_from_values(
    aggregate_row_number: Decimal,
    values: _RowValues,
) -> ResearchStrategyDecisionEvidenceBalanceRow:
    return ResearchStrategyDecisionEvidenceBalanceRow(
        aggregate_row_number=aggregate_row_number,
        aggregate_row_hash=values.aggregate_row_hash,
        status=values.status,
        probability_model_score=values.probability_model_score,
        team_memory_score=values.team_memory_score,
        source_corroboration_score=values.source_corroboration_score,
        market_mechanics_score=values.market_mechanics_score,
        resolution_risk_score=values.resolution_risk_score,
        evidence_balance_score=values.evidence_balance_score,
        evidence_imbalance_score=values.evidence_imbalance_score,
        reason_codes=values.reason_codes,
    )


def _row_reason_codes(
    value: ResearchStrategyDecisionEvidenceBalanceCandidate,
    *,
    config: ResearchStrategyDecisionEvidenceBalanceConfig,
) -> tuple[str, ...]:
    reason_codes = [*value.reason_codes]
    _append_floor_reason(
        reason_codes,
        "probability_model",
        value.probability_model_score,
        config.probability_model_pass_floor,
        config.probability_model_watch_floor,
    )
    _append_floor_reason(
        reason_codes,
        "team_memory",
        value.team_memory_score,
        config.team_memory_pass_floor,
        config.team_memory_watch_floor,
    )
    _append_floor_reason(
        reason_codes,
        "source_corroboration",
        value.source_corroboration_score,
        config.source_corroboration_pass_floor,
        config.source_corroboration_watch_floor,
    )
    _append_floor_reason(
        reason_codes,
        "market_mechanics",
        value.market_mechanics_score,
        config.market_mechanics_pass_floor,
        config.market_mechanics_watch_floor,
    )
    _append_floor_reason(
        reason_codes,
        "resolution_risk",
        value.resolution_risk_score,
        config.resolution_risk_pass_floor,
        config.resolution_risk_watch_floor,
    )
    imbalance_score = _evidence_imbalance_score(
        value.probability_model_score,
        value.team_memory_score,
        value.source_corroboration_score,
        value.market_mechanics_score,
        value.resolution_risk_score,
    )
    if imbalance_score >= config.imbalance_block_threshold:
        reason_codes.append("evidence_balance_imbalance_block")
    elif imbalance_score >= config.imbalance_watch_threshold:
        reason_codes.append("evidence_balance_imbalance_watch")
    if not _has_attention_reason(reason_codes):
        reason_codes.append("decision_evidence_balance_clear")
    return _normalize_reason_codes("reason_codes", tuple(sorted(reason_codes)))


def _append_floor_reason(
    reason_codes: list[str],
    prefix: str,
    score: Decimal,
    pass_floor: Decimal,
    watch_floor: Decimal,
) -> None:
    if score < watch_floor:
        reason_codes.append(f"{prefix}_block")
    elif score < pass_floor:
        reason_codes.append(f"{prefix}_watch")


def _has_attention_reason(reason_codes: list[str]) -> bool:
    return any(
        reason_code.endswith("_watch") or reason_code.endswith("_block")
        for reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "block"
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyDecisionEvidenceBalanceRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _rollup_status(tuple(row.status for row in rows))
    reason_codes = [f"decision_evidence_balance_{status}"]
    row_reason_codes = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
    )
    reason_codes.extend(
        reason_code
        for reason_code in REPORT_REASON_PRIORITY
        if reason_code in row_reason_codes
    )
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchStrategyDecisionEvidenceBalanceRow, ...],
) -> tuple[ResearchStrategyDecisionEvidenceBalanceReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyDecisionEvidenceBalanceReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=COUNT_QUANTUM,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchStrategyDecisionEvidenceBalanceReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _report_values(
    *,
    generated_at: datetime,
    config_version: str,
    rows: tuple[ResearchStrategyDecisionEvidenceBalanceRow, ...],
) -> dict[str, Any]:
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "candidate_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "probability_model_attention_count": _kind_count(rows, "probability_model_"),
        "team_memory_attention_count": _kind_count(rows, "team_memory_"),
        "source_corroboration_attention_count": _kind_count(rows, "source_corroboration_"),
        "market_mechanics_attention_count": _kind_count(rows, "market_mechanics_"),
        "resolution_risk_attention_count": _kind_count(rows, "resolution_risk_"),
        "balance_imbalance_attention_count": _kind_count(rows, "evidence_balance_imbalance_"),
        "mean_probability_model_score": _mean(
            tuple(row.probability_model_score for row in rows),
        ),
        "mean_team_memory_score": _mean(tuple(row.team_memory_score for row in rows)),
        "mean_source_corroboration_score": _mean(
            tuple(row.source_corroboration_score for row in rows),
        ),
        "mean_market_mechanics_score": _mean(
            tuple(row.market_mechanics_score for row in rows),
        ),
        "mean_resolution_risk_score": _mean(
            tuple(row.resolution_risk_score for row in rows),
        ),
        "mean_evidence_balance_score": _mean(
            tuple(row.evidence_balance_score for row in rows),
        ),
        "max_evidence_imbalance_score": _max_decimal(
            tuple(row.evidence_imbalance_score for row in rows),
        ),
        "status": _rollup_status(tuple(row.status for row in rows)),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _normalize_inputs(
    candidates: Iterable[ResearchStrategyDecisionEvidenceBalanceCandidate],
) -> tuple[ResearchStrategyDecisionEvidenceBalanceCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        rows = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen_keys: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyDecisionEvidenceBalanceCandidate:
            raise ValueError(
                "candidates must contain ResearchStrategyDecisionEvidenceBalanceCandidate values",
            )
        _require_hard_flags("candidate", row)
        _reject_unsafe_public_payload("candidate", row)
        if row.evidence_key in seen_keys:
            raise ValueError("candidates must not contain duplicate evidence_key values")
        seen_keys.add(row.evidence_key)
    return rows


def _normalize_rows(
    rows: Iterable[ResearchStrategyDecisionEvidenceBalanceRow],
) -> tuple[ResearchStrategyDecisionEvidenceBalanceRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_hashes: set[str] = set()
    for row in values:
        if type(row) is not ResearchStrategyDecisionEvidenceBalanceRow:
            raise ValueError("rows must contain ResearchStrategyDecisionEvidenceBalanceRow values")
        _require_hard_flags("row", row)
        _reject_unsafe_public_payload("row", row)
        if row.aggregate_row_hash in seen_hashes:
            raise ValueError("rows must not contain duplicate aggregate_row_hash values")
        seen_hashes.add(row.aggregate_row_hash)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must use canonical sequence")
    return values


def _normalize_reason_code_counts(
    rows: Iterable[ResearchStrategyDecisionEvidenceBalanceReasonCodeCount],
) -> tuple[ResearchStrategyDecisionEvidenceBalanceReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in values:
        if type(row) is not ResearchStrategyDecisionEvidenceBalanceReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchStrategyDecisionEvidenceBalanceReasonCodeCount values",
            )
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate reason_code values")
        seen_codes.add(row.reason_code)
    expected = tuple(sorted(values, key=lambda item: (-item.count, item.reason_code)))
    if values != expected:
        raise ValueError("reason_code_counts must use canonical sequence")
    return values


def _row_sort_key(
    row: ResearchStrategyDecisionEvidenceBalanceRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -row.evidence_imbalance_score,
        -_evidence_balance_gap(row.evidence_balance_score),
        row.aggregate_row_hash,
    )


def _row_values_sort_key(values: _RowValues) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[values.status],
        -values.evidence_imbalance_score,
        -_evidence_balance_gap(values.evidence_balance_score),
        values.aggregate_row_hash,
    )


def _status_count(
    rows: tuple[ResearchStrategyDecisionEvidenceBalanceRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _kind_count(
    rows: tuple[ResearchStrategyDecisionEvidenceBalanceRow, ...],
    kind: str,
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if any(reason_code.startswith(kind) for reason_code in row.reason_codes)
        ),
    )


def _validate_report(report: ResearchStrategyDecisionEvidenceBalanceReport) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    for field_name, kind in (
        ("probability_model_attention_count", "probability_model_"),
        ("team_memory_attention_count", "team_memory_"),
        ("source_corroboration_attention_count", "source_corroboration_"),
        ("market_mechanics_attention_count", "market_mechanics_"),
        ("resolution_risk_attention_count", "resolution_risk_"),
        ("balance_imbalance_attention_count", "evidence_balance_imbalance_"),
    ):
        if getattr(report, field_name) != _kind_count(rows, kind):
            raise ValueError(f"{field_name} must match rows")
    for field_name in (
        "probability_model_score",
        "team_memory_score",
        "source_corroboration_score",
        "market_mechanics_score",
        "resolution_risk_score",
        "evidence_balance_score",
    ):
        report_field_name = f"mean_{field_name}"
        if getattr(report, report_field_name) != _mean(
            tuple(getattr(row, field_name) for row in rows),
        ):
            raise ValueError(f"{report_field_name} must match rows")
    if report.max_evidence_imbalance_score != _max_decimal(
        tuple(row.evidence_imbalance_score for row in rows),
    ):
        raise ValueError("max_evidence_imbalance_score must match rows")
    if report.status != _rollup_status(tuple(row.status for row in rows)):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    for index, row in enumerate(rows, start=1):
        if row.aggregate_row_number != _count(index):
            raise ValueError("aggregate_row_number must match rows")


def _revalidate_report_for_payload(
    report: ResearchStrategyDecisionEvidenceBalanceReport,
) -> None:
    _require_exact_type(report, ResearchStrategyDecisionEvidenceBalanceReport, "report")
    _require_utc_datetime("generated_at", report.generated_at)
    _require_canonical_string("config_version", report.config_version)
    for field_name in (
        "candidate_count",
        "pass_count",
        "watch_count",
        "block_count",
        "probability_model_attention_count",
        "team_memory_attention_count",
        "source_corroboration_attention_count",
        "market_mechanics_attention_count",
        "resolution_risk_attention_count",
        "balance_imbalance_attention_count",
    ):
        _require_nonnegative_six_decimal_decimal(field_name, getattr(report, field_name))
    for field_name in (
        "mean_probability_model_score",
        "mean_team_memory_score",
        "mean_source_corroboration_score",
        "mean_market_mechanics_score",
        "mean_resolution_risk_score",
        "mean_evidence_balance_score",
        "max_evidence_imbalance_score",
    ):
        _require_probability_six_decimal_decimal(field_name, getattr(report, field_name))
    _require_status("status", report.status)
    _require_public_digest("public_digest", report.public_digest)
    _require_reason_codes_tuple("reason_codes", report.reason_codes)
    _normalize_report_reason_codes(report.reason_codes)
    if type(report.reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in report.reason_code_counts:
        _revalidate_reason_code_count_for_payload(row)
    if type(report.rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in report.rows:
        _revalidate_row_for_payload(row)
    _validate_report(report)
    if report.public_digest != _computed_report_digest(report):
        raise ValueError("public_digest must match report values")
    _require_hard_flags("report", report)


def _revalidate_row_for_payload(row: object) -> None:
    if type(row) is not ResearchStrategyDecisionEvidenceBalanceRow:
        raise ValueError("rows must contain ResearchStrategyDecisionEvidenceBalanceRow values")
    _require_positive_six_decimal_decimal("aggregate_row_number", row.aggregate_row_number)
    _require_public_digest("aggregate_row_hash", row.aggregate_row_hash)
    _require_status("status", row.status)
    for field_name in (
        "probability_model_score",
        "team_memory_score",
        "source_corroboration_score",
        "market_mechanics_score",
        "resolution_risk_score",
        "evidence_balance_score",
        "evidence_imbalance_score",
    ):
        _require_probability_six_decimal_decimal(field_name, getattr(row, field_name))
    _require_reason_codes_tuple("reason_codes", row.reason_codes)
    if row.reason_codes != _normalize_reason_codes("reason_codes", row.reason_codes):
        raise ValueError("reason_codes must use canonical sequence")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.evidence_balance_score != _evidence_balance_score(
        row.probability_model_score,
        row.team_memory_score,
        row.source_corroboration_score,
        row.market_mechanics_score,
        row.resolution_risk_score,
    ):
        raise ValueError("evidence_balance_score must match scores")
    if row.evidence_imbalance_score != _evidence_imbalance_score(
        row.probability_model_score,
        row.team_memory_score,
        row.source_corroboration_score,
        row.market_mechanics_score,
        row.resolution_risk_score,
    ):
        raise ValueError("evidence_imbalance_score must match scores")
    _require_hard_flags("row", row)


def _revalidate_reason_code_count_for_payload(row: object) -> None:
    if type(row) is not ResearchStrategyDecisionEvidenceBalanceReasonCodeCount:
        raise ValueError(
            "reason_code_counts must contain ResearchStrategyDecisionEvidenceBalanceReasonCodeCount values",
        )
    _require_canonical_string("reason_code", row.reason_code)
    _require_positive_six_decimal_decimal("count", row.count)
    _require_hard_flags("reason_code_count", row)


def _evidence_balance_score(
    probability_model_score: Decimal,
    team_memory_score: Decimal,
    source_corroboration_score: Decimal,
    market_mechanics_score: Decimal,
    resolution_risk_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            (
                probability_model_score
                + team_memory_score
                + source_corroboration_score
                + market_mechanics_score
                + resolution_risk_score
            )
            / FIVE,
        )


def _evidence_imbalance_score(
    probability_model_score: Decimal,
    team_memory_score: Decimal,
    source_corroboration_score: Decimal,
    market_mechanics_score: Decimal,
    resolution_risk_score: Decimal,
) -> Decimal:
    values = (
        probability_model_score,
        team_memory_score,
        source_corroboration_score,
        market_mechanics_score,
        resolution_risk_score,
    )
    return _quantize(max(values) - min(values))


def _evidence_balance_gap(value: Decimal) -> Decimal:
    return _quantize(ONE - value)


def _public_hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _computed_report_digest(
    report: ResearchStrategyDecisionEvidenceBalanceReport,
) -> str:
    values = {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "public_digest"
    }
    return _digest_from_mapping(values)


def _digest_from_mapping(values: dict[str, Any]) -> str:
    ready = _json_ready(values)
    return sha256(
        json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError("payload contains unknown dataclass")
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        _require_six_decimal_decimal("JSON Decimal value", value)
        return str(value)
    if type(value) is datetime:
        _require_utc_datetime("JSON datetime value", value)
        return value.isoformat()
    if value is None or type(value) in (bool, str):
        if type(value) is str:
            _require_canonical_string("JSON string value", value)
        return value
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_canonical_string("JSON object key", key)
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (int, float) or isinstance(value, (list, set)):
        raise ValueError("value must use public dataclass fields")
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{label} contains unknown dataclass")
        for field in fields(value):
            _reject_unsafe_public_payload(f"{label}.{field.name}", getattr(value, field.name))
        return
    if type(value) is str:
        _reject_unsafe_text(label, value)
        return
    if type(value) in (Decimal, datetime) or value is None or type(value) is bool:
        return
    if type(value) in (tuple, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(f"{label}[{index}]", item)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_text(label, key)
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if type(value) in (int, float) or isinstance(value, set):
        raise ValueError(f"{label} must use public dataclass fields")
    raise ValueError(f"{label} has unknown value")


def _reject_unsafe_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(piece in lowered for piece in _UNSAFE_TEXT_PARTS):
        raise ValueError(f"{label} contains unsafe public value")


def _normalize_reason_codes(
    label: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool = False,
) -> tuple[str, ...]:
    _require_reason_codes_tuple(label, values)
    if not allow_empty and not values:
        raise ValueError(f"{label} must not be empty")
    seen: set[str] = set()
    for value in values:
        _require_canonical_string(label, value)
        if value in seen:
            raise ValueError(f"{label} must not contain duplicates")
        seen.add(value)
    normalized = tuple(sorted(values))
    if values != normalized:
        raise ValueError(f"{label} must use canonical sequence")
    return normalized


def _normalize_report_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    _require_reason_codes_tuple("reason_codes", values)
    if not values:
        raise ValueError("reason_codes must not be empty")
    for value in values:
        _require_canonical_string("reason_codes", value)
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must not contain duplicates")
    return values


def _require_reason_codes_tuple(label: str, values: object) -> None:
    if type(values) is not tuple:
        raise ValueError(f"{label} must be a tuple")
    for value in values:
        if type(value) is not str:
            raise ValueError(f"{label} must contain strings")


def _require_canonical_string(label: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{label} must be canonical")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{label} must be canonical")
    _reject_unsafe_text(label, value)


def _require_status(label: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{label} must be pass, watch, or block")


def _require_public_digest(label: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    if len(value) != 64 or value.lower() != value:
        raise ValueError(f"{label} must be a lowercase hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{label} must be a lowercase hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_at_least(label: str, value: Decimal, limit: Decimal) -> None:
    if value < limit:
        raise ValueError(f"{label} must be at least its watch level")


def _as_utc(label: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{label} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value.astimezone(UTC)


def _require_utc_datetime(label: str, value: object) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{label} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{label} must be UTC")


def _normalize_decimal(label: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{label} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{label} must be finite")
    return _quantize(value)


def _normalize_nonnegative_decimal(label: str, value: object) -> Decimal:
    normalized = _normalize_decimal(label, value)
    if normalized < ZERO:
        raise ValueError(f"{label} must be nonnegative")
    return normalized


def _normalize_positive_count(label: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(label, value)
    if normalized <= ZERO:
        raise ValueError(f"{label} must be positive")
    return normalized


def _normalize_probability_decimal(label: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(label, value)
    if normalized > ONE:
        raise ValueError(f"{label} must be between 0 and 1")
    return normalized


def _require_six_decimal_decimal(label: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{label} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{label} must be finite")
    if value != _quantize(value):
        raise ValueError(f"{label} must use six decimal places")


def _require_nonnegative_six_decimal_decimal(label: str, value: object) -> None:
    _require_six_decimal_decimal(label, value)
    if value < ZERO:
        raise ValueError(f"{label} must be nonnegative")


def _require_positive_six_decimal_decimal(label: str, value: object) -> None:
    _require_nonnegative_six_decimal_decimal(label, value)
    if value <= ZERO:
        raise ValueError(f"{label} must be positive")


def _require_probability_six_decimal_decimal(label: str, value: object) -> None:
    _require_nonnegative_six_decimal_decimal(label, value)
    if value > ONE:
        raise ValueError(f"{label} must be between 0 and 1")


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)
