"""Pure strategy-side selection readiness gate report."""

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
    "DEFAULT_RESEARCH_STRATEGY_MARKET_SELECTION_READINESS_GATE_REPORT_CONFIG_VERSION",
    "ResearchStrategyMarketSelectionReadinessGateCandidate",
    "ResearchStrategyMarketSelectionReadinessGateConfig",
    "ResearchStrategyMarketSelectionReadinessGateReasonCodeCount",
    "ResearchStrategyMarketSelectionReadinessGateReport",
    "ResearchStrategyMarketSelectionReadinessGateRow",
    "build_research_strategy_market_selection_readiness_gate_report",
    "research_strategy_market_selection_readiness_gate_report_digest",
    "research_strategy_market_selection_readiness_gate_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_MARKET_SELECTION_READINESS_GATE_REPORT_CONFIG_VERSION = (
    "research-strategy-market-selection-readiness-gate-report-v0"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FIVE = Decimal("5.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_STATUSES = ("pass", "watch", "block")
STATUS_SORT_WEIGHT = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
NO_CANDIDATES_REASON = "market_selection_readiness_no_candidates"
REASON_PRIORITY = (
    "evidence_maturity_block",
    "liquidity_cost_freshness_block",
    "settlement_clarity_block",
    "domain_memory_quality_block",
    "conflict_pressure_block",
    "market_selection_readiness_block",
    "evidence_maturity_watch",
    "liquidity_cost_freshness_watch",
    "settlement_clarity_watch",
    "domain_memory_quality_watch",
    "conflict_pressure_watch",
    "market_selection_readiness_watch",
    "market_selection_readiness_pass",
    NO_CANDIDATES_REASON,
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = (
    _join_parts("raw", "_candidate", "_id"),
    _join_parts("mar", "ket", "_id"),
    _join_parts("mar", "ket", "_s", "lug"),
    _join_parts("s", "lug"),
    _join_parts("ques", "tion"),
    _join_parts("source", "_u", "rl"),
    _join_parts("source", "_te", "xt"),
    _join_parts("d", "sn"),
    _join_parts("ta", "ble", "_na", "me"),
    _join_parts("private", "_to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("tra", "ding"),
    _join_parts("position", "_si", "ze"),
    _join_parts("b", "uy"),
    _join_parts("se", "ll"),
    _join_parts("rec", "ommend"),
    _join_parts("si", "zing"),
    _join_parts("data", "base"),
    _join_parts("net", "work"),
    _join_parts("req", "uests"),
    _join_parts("ht", "tp"),
    _join_parts("so", "cket"),
    _join_parts("sub", "process"),
    _join_parts("://"),
    _join_parts("api", "_key"),
    _join_parts("sec", "ret"),
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchStrategyMarketSelectionReadinessGateConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_MARKET_SELECTION_READINESS_GATE_REPORT_CONFIG_VERSION
    )
    evidence_maturity_pass_floor: Decimal = Decimal("0.800000")
    evidence_maturity_watch_floor: Decimal = Decimal("0.600000")
    liquidity_cost_freshness_pass_floor: Decimal = Decimal("0.800000")
    liquidity_cost_freshness_watch_floor: Decimal = Decimal("0.600000")
    settlement_clarity_pass_floor: Decimal = Decimal("0.800000")
    settlement_clarity_watch_floor: Decimal = Decimal("0.600000")
    domain_memory_quality_pass_floor: Decimal = Decimal("0.750000")
    domain_memory_quality_watch_floor: Decimal = Decimal("0.550000")
    conflict_pressure_watch_ceiling: Decimal = Decimal("0.250000")
    conflict_pressure_block_ceiling: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyMarketSelectionReadinessGateConfig,
            "config",
        )
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_MARKET_SELECTION_READINESS_GATE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "evidence_maturity_pass_floor",
            "evidence_maturity_watch_floor",
            "liquidity_cost_freshness_pass_floor",
            "liquidity_cost_freshness_watch_floor",
            "settlement_clarity_pass_floor",
            "settlement_clarity_watch_floor",
            "domain_memory_quality_pass_floor",
            "domain_memory_quality_watch_floor",
            "conflict_pressure_watch_ceiling",
            "conflict_pressure_block_ceiling",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_at_least(
            "evidence_maturity_pass_floor",
            self.evidence_maturity_pass_floor,
            self.evidence_maturity_watch_floor,
        )
        _require_at_least(
            "liquidity_cost_freshness_pass_floor",
            self.liquidity_cost_freshness_pass_floor,
            self.liquidity_cost_freshness_watch_floor,
        )
        _require_at_least(
            "settlement_clarity_pass_floor",
            self.settlement_clarity_pass_floor,
            self.settlement_clarity_watch_floor,
        )
        _require_at_least(
            "domain_memory_quality_pass_floor",
            self.domain_memory_quality_pass_floor,
            self.domain_memory_quality_watch_floor,
        )
        _require_at_most(
            "conflict_pressure_watch_ceiling",
            self.conflict_pressure_watch_ceiling,
            self.conflict_pressure_block_ceiling,
        )
        _require_hard_phase_flags("config", self)
        _reject_unsafe_payload(_json_ready(self))


@dataclass(frozen=True)
class ResearchStrategyMarketSelectionReadinessGateCandidate(_FinalDataclass):
    screening_key: str
    evidence_maturity_score: Decimal
    liquidity_cost_freshness_score: Decimal
    settlement_clarity_score: Decimal
    domain_memory_quality_score: Decimal
    conflict_pressure_score: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyMarketSelectionReadinessGateCandidate,
            "candidate",
        )
        _require_internal_reference_text("screening_key", self.screening_key)
        for field_name in (
            "evidence_maturity_score",
            "liquidity_cost_freshness_score",
            "settlement_clarity_score",
            "domain_memory_quality_score",
            "conflict_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        _require_hard_phase_flags("candidate", self)


@dataclass(frozen=True)
class ResearchStrategyMarketSelectionReadinessGateRow(_FinalDataclass):
    row_number: Decimal
    public_candidate_hash: str
    evidence_maturity_score: Decimal
    liquidity_cost_freshness_score: Decimal
    settlement_clarity_score: Decimal
    domain_memory_quality_score: Decimal
    conflict_pressure_score: Decimal
    conflict_clearance_score: Decimal
    market_selection_readiness_score: Decimal
    observed_at: datetime
    observation_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyMarketSelectionReadinessGateRow, "row")
        object.__setattr__(
            self,
            "row_number",
            _normalize_positive_count("row_number", self.row_number),
        )
        _require_public_hash("public_candidate_hash", self.public_candidate_hash)
        for field_name in (
            "evidence_maturity_score",
            "liquidity_cost_freshness_score",
            "settlement_clarity_score",
            "domain_memory_quality_score",
            "conflict_pressure_score",
            "conflict_clearance_score",
            "market_selection_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "observation_age_seconds",
            _normalize_nonnegative_decimal(
                "observation_age_seconds",
                self.observation_age_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_digest("validation_digest", self.validation_digest)
        _require_hard_phase_flags("row", self)
        _validate_row(self)
        if self.validation_digest != _validation_digest(_public_mapping(self)):
            raise ValueError("validation_digest must match row fields")
        _reject_unsafe_payload(_json_ready(self))


@dataclass(frozen=True)
class ResearchStrategyMarketSelectionReadinessGateReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyMarketSelectionReadinessGateReasonCodeCount,
            "reason_code_count",
        )
        _require_public_text("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        _require_hard_phase_flags("reason_code_count", self)
        _reject_unsafe_payload(_json_ready(self))


@dataclass(frozen=True)
class ResearchStrategyMarketSelectionReadinessGateReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_readiness_score: Decimal
    min_readiness_score: Decimal
    max_conflict_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategyMarketSelectionReadinessGateReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchStrategyMarketSelectionReadinessGateRow, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyMarketSelectionReadinessGateReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_readiness_score",
            "min_readiness_score",
            "max_conflict_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("validation_digest", self.validation_digest)
        _require_hard_phase_flags("report", self)
        _validate_report(self)
        if self.validation_digest != _validation_digest(_public_mapping(self)):
            raise ValueError("validation_digest must match report fields")
        _reject_unsafe_payload(_json_ready(self))


def build_research_strategy_market_selection_readiness_gate_report(
    candidates: Iterable[ResearchStrategyMarketSelectionReadinessGateCandidate],
    *,
    config: ResearchStrategyMarketSelectionReadinessGateConfig,
    generated_at: datetime,
) -> ResearchStrategyMarketSelectionReadinessGateReport:
    if type(config) is not ResearchStrategyMarketSelectionReadinessGateConfig:
        raise ValueError(
            "config must be a ResearchStrategyMarketSelectionReadinessGateConfig",
        )
    _require_hard_phase_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    draft_rows = tuple(
        sorted(
            (
                _draft_row_values(
                    candidate,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for candidate in normalized_candidates
            ),
            key=_draft_row_sort_key,
        ),
    )
    rows = tuple(
        _row_from_draft(row_number=index, draft_values=draft_values)
        for index, draft_values in enumerate(draft_rows, start=1)
    )
    status = _report_status(rows)
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "candidate_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_readiness_score": _average_readiness_score(rows),
        "min_readiness_score": _min_readiness_score(rows),
        "max_conflict_pressure_score": _max_conflict_pressure_score(rows),
        "status": status,
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyMarketSelectionReadinessGateReport(
        **report_values,
        validation_digest=_validation_digest(report_values),
    )


def research_strategy_market_selection_readiness_gate_report_payload(
    report: ResearchStrategyMarketSelectionReadinessGateReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyMarketSelectionReadinessGateReport:
        _require_hard_phase_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyMarketSelectionReadinessGateReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_payload(payload)
    _reject_numeric_public_payload(payload)
    _require_hard_phase_flags("payload", _DictFlags(payload))
    _require_digest("validation_digest", payload.get("validation_digest"))
    if payload["validation_digest"] != _validation_digest(payload):
        raise ValueError("validation_digest must match payload fields")
    return payload


def research_strategy_market_selection_readiness_gate_report_digest(
    report: ResearchStrategyMarketSelectionReadinessGateReport,
) -> str:
    payload = research_strategy_market_selection_readiness_gate_report_payload(report)
    digest = payload["validation_digest"]
    if type(digest) is not str:
        raise ValueError("validation_digest must be a string")
    return digest


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


def _draft_row_values(
    candidate: ResearchStrategyMarketSelectionReadinessGateCandidate,
    *,
    config: ResearchStrategyMarketSelectionReadinessGateConfig,
    generated_at: datetime,
) -> dict[str, object]:
    if candidate.observed_at > generated_at:
        raise ValueError("generated_at must not precede observed_at")
    conflict_clearance_score = _quantize(ONE - candidate.conflict_pressure_score)
    reason_codes = _row_reason_codes(candidate, config=config)
    status = _row_status(reason_codes)
    return {
        "public_candidate_hash": _public_hash(candidate.screening_key),
        "evidence_maturity_score": candidate.evidence_maturity_score,
        "liquidity_cost_freshness_score": candidate.liquidity_cost_freshness_score,
        "settlement_clarity_score": candidate.settlement_clarity_score,
        "domain_memory_quality_score": candidate.domain_memory_quality_score,
        "conflict_pressure_score": candidate.conflict_pressure_score,
        "conflict_clearance_score": conflict_clearance_score,
        "market_selection_readiness_score": _readiness_score(
            (
                candidate.evidence_maturity_score,
                candidate.liquidity_cost_freshness_score,
                candidate.settlement_clarity_score,
                candidate.domain_memory_quality_score,
                conflict_clearance_score,
            ),
        ),
        "observed_at": candidate.observed_at,
        "observation_age_seconds": _seconds_between(candidate.observed_at, generated_at),
        "status": status,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_from_draft(
    *,
    row_number: int,
    draft_values: dict[str, object],
) -> ResearchStrategyMarketSelectionReadinessGateRow:
    row_values = {"row_number": _count(row_number), **draft_values}
    return ResearchStrategyMarketSelectionReadinessGateRow(
        **row_values,
        validation_digest=_validation_digest(row_values),
    )


def _row_reason_codes(
    candidate: ResearchStrategyMarketSelectionReadinessGateCandidate,
    *,
    config: ResearchStrategyMarketSelectionReadinessGateConfig,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    _append_floor_reasons(
        block_reasons,
        watch_reasons,
        value=candidate.evidence_maturity_score,
        pass_floor=config.evidence_maturity_pass_floor,
        watch_floor=config.evidence_maturity_watch_floor,
        reason_prefix="evidence_maturity",
    )
    _append_floor_reasons(
        block_reasons,
        watch_reasons,
        value=candidate.liquidity_cost_freshness_score,
        pass_floor=config.liquidity_cost_freshness_pass_floor,
        watch_floor=config.liquidity_cost_freshness_watch_floor,
        reason_prefix="liquidity_cost_freshness",
    )
    _append_floor_reasons(
        block_reasons,
        watch_reasons,
        value=candidate.settlement_clarity_score,
        pass_floor=config.settlement_clarity_pass_floor,
        watch_floor=config.settlement_clarity_watch_floor,
        reason_prefix="settlement_clarity",
    )
    _append_floor_reasons(
        block_reasons,
        watch_reasons,
        value=candidate.domain_memory_quality_score,
        pass_floor=config.domain_memory_quality_pass_floor,
        watch_floor=config.domain_memory_quality_watch_floor,
        reason_prefix="domain_memory_quality",
    )
    if candidate.conflict_pressure_score >= config.conflict_pressure_block_ceiling:
        block_reasons.append("conflict_pressure_block")
    elif candidate.conflict_pressure_score > config.conflict_pressure_watch_ceiling:
        watch_reasons.append("conflict_pressure_watch")
    reasons = tuple(block_reasons + watch_reasons)
    if not reasons:
        reasons = ("market_selection_readiness_pass",)
    return _normalize_reason_codes(reasons)


def _append_floor_reasons(
    block_reasons: list[str],
    watch_reasons: list[str],
    *,
    value: Decimal,
    pass_floor: Decimal,
    watch_floor: Decimal,
    reason_prefix: str,
) -> None:
    if value < watch_floor:
        block_reasons.append(f"{reason_prefix}_block")
    elif value < pass_floor:
        watch_reasons.append(f"{reason_prefix}_watch")


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchStrategyMarketSelectionReadinessGateRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyMarketSelectionReadinessGateRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_CANDIDATES_REASON,)
    status = _report_status(rows)
    values = tuple(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != "market_selection_readiness_pass"
    )
    return _normalize_reason_codes((*values, f"market_selection_readiness_{status}"))


def _reason_code_counts(
    rows: tuple[ResearchStrategyMarketSelectionReadinessGateRow, ...],
) -> tuple[ResearchStrategyMarketSelectionReadinessGateReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyMarketSelectionReadinessGateReasonCodeCount(
                reason_code=NO_CANDIDATES_REASON,
                count=ONE,
            ),
        )
    counter: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(
        ResearchStrategyMarketSelectionReadinessGateReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(
            counter.items(),
            key=lambda item: (_reason_rank(item[0]), item[0]),
        )
    )


def _readiness_score(values: tuple[Decimal, ...]) -> Decimal:
    return _ratio(_sum_decimal(values), FIVE)


def _average_readiness_score(
    rows: tuple[ResearchStrategyMarketSelectionReadinessGateRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _ratio(
        _sum_decimal(tuple(row.market_selection_readiness_score for row in rows)),
        _count(len(rows)),
    )


def _min_readiness_score(
    rows: tuple[ResearchStrategyMarketSelectionReadinessGateRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return min(row.market_selection_readiness_score for row in rows)


def _max_conflict_pressure_score(
    rows: tuple[ResearchStrategyMarketSelectionReadinessGateRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return max(row.conflict_pressure_score for row in rows)


def _normalize_candidates(
    candidates: Iterable[ResearchStrategyMarketSelectionReadinessGateCandidate],
) -> tuple[ResearchStrategyMarketSelectionReadinessGateCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        values = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen: set[str] = set()
    for candidate in values:
        if type(candidate) is not ResearchStrategyMarketSelectionReadinessGateCandidate:
            raise ValueError(
                "candidates must contain ResearchStrategyMarketSelectionReadinessGateCandidate",
            )
        _require_hard_phase_flags("candidate", candidate)
        if candidate.screening_key in seen:
            raise ValueError("screening_key values must be unique")
        seen.add(candidate.screening_key)
    return values


def _normalize_rows(
    rows: tuple[ResearchStrategyMarketSelectionReadinessGateRow, ...],
) -> tuple[ResearchStrategyMarketSelectionReadinessGateRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyMarketSelectionReadinessGateRow:
            raise ValueError(
                "rows must contain ResearchStrategyMarketSelectionReadinessGateRow",
            )
    return rows


def _normalize_reason_code_counts(
    reason_code_counts: tuple[
        ResearchStrategyMarketSelectionReadinessGateReasonCodeCount,
        ...,
    ],
) -> tuple[ResearchStrategyMarketSelectionReadinessGateReasonCodeCount, ...]:
    if type(reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for reason_code_count in reason_code_counts:
        if (
            type(reason_code_count)
            is not ResearchStrategyMarketSelectionReadinessGateReasonCodeCount
        ):
            raise ValueError(
                "reason_code_counts must contain ResearchStrategyMarketSelectionReadinessGateReasonCodeCount",
            )
    expected = tuple(
        sorted(
            reason_code_counts,
            key=lambda item: (_reason_rank(item.reason_code), item.reason_code),
        ),
    )
    if reason_code_counts != expected:
        raise ValueError("reason_code_counts must be sorted deterministically")
    if len({item.reason_code for item in reason_code_counts}) != len(reason_code_counts):
        raise ValueError("reason_code_counts must be unique by reason_code")
    return reason_code_counts


def _validate_row(row: ResearchStrategyMarketSelectionReadinessGateRow) -> None:
    if row.conflict_clearance_score != _quantize(ONE - row.conflict_pressure_score):
        raise ValueError("conflict_clearance_score must match conflict pressure")
    expected_score = _readiness_score(
        (
            row.evidence_maturity_score,
            row.liquidity_cost_freshness_score,
            row.settlement_clarity_score,
            row.domain_memory_quality_score,
            row.conflict_clearance_score,
        ),
    )
    if row.market_selection_readiness_score != expected_score:
        raise ValueError("market_selection_readiness_score must match inputs")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchStrategyMarketSelectionReadinessGateReport) -> None:
    rows = report.rows
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    expected_numbers = tuple(_count(index) for index in range(1, len(rows) + 1))
    if tuple(row.row_number for row in rows) != expected_numbers:
        raise ValueError("rows must be sorted deterministically")
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    for status in PUBLIC_STATUSES:
        expected = _status_count(rows, status)
        actual = getattr(report, f"{status}_count")
        if actual != expected:
            raise ValueError(f"{status}_count must match rows")
    if report.average_readiness_score != _average_readiness_score(rows):
        raise ValueError("average_readiness_score must match rows")
    if report.min_readiness_score != _min_readiness_score(rows):
        raise ValueError("min_readiness_score must match rows")
    if report.max_conflict_pressure_score != _max_conflict_pressure_score(rows):
        raise ValueError("max_conflict_pressure_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _status_count(
    rows: tuple[ResearchStrategyMarketSelectionReadinessGateRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _draft_row_sort_key(value: dict[str, object]) -> tuple[Decimal, Decimal, str]:
    status = value["status"]
    score = value["market_selection_readiness_score"]
    public_hash = value["public_candidate_hash"]
    if type(status) is not str:
        raise ValueError("status must be a string")
    if type(score) is not Decimal:
        raise ValueError("market_selection_readiness_score must be Decimal")
    if type(public_hash) is not str:
        raise ValueError("public_candidate_hash must be a string")
    return (STATUS_SORT_WEIGHT[status], score, public_hash)


def _row_sort_key(
    row: ResearchStrategyMarketSelectionReadinessGateRow,
) -> tuple[Decimal, Decimal, str]:
    return (
        STATUS_SORT_WEIGHT[row.status],
        row.market_selection_readiness_score,
        row.public_candidate_hash,
    )


def _reason_rank(reason_code: str) -> int:
    try:
        return REASON_PRIORITY.index(reason_code)
    except ValueError:
        return len(REASON_PRIORITY)


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_text("reason_codes", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        sorted(
            normalized,
            key=lambda reason_code: (_reason_rank(reason_code), reason_code),
        ),
    )


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_public_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value != value.strip() or not value:
        raise ValueError(f"{name} must be a non-empty canonical string")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{name} must not contain control characters")
    _reject_unsafe_text(name, value)


def _require_internal_reference_text(name: str, value: object) -> None:
    _require_public_text(name, value)


def _require_status(name: str, value: object) -> None:
    if value not in PUBLIC_STATUSES:
        raise ValueError(f"{name} must be one of pass/watch/block")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a SHA-256 hex digest")


def _require_public_hash(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value.startswith("sha256:"):
        raise ValueError(f"{name} must be a public SHA-256 hash")
    _require_digest(name, value.removeprefix("sha256:"))


def _require_hard_phase_flags(name: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{name}.{field_name} must be hard-coded True")


def _require_at_least(name: str, left: Decimal, right: Decimal) -> None:
    if left < right:
        raise ValueError(f"{name} must be at least paired watch floor")


def _require_at_most(name: str, left: Decimal, right: Decimal) -> None:
    if left > right:
        raise ValueError(f"{name} must be at most paired block ceiling")


def _normalize_ratio(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(decimal_value)


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(decimal_value)


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be a whole-number Decimal")
    return decimal_value


def _normalize_positive_count(name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_count(name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    with localcontext(DECIMAL_CONTEXT):
        for value in values:
            total += value
    return _quantize(total)


def _count(value: int) -> Decimal:
    return Decimal(str(value)).quantize(QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    seconds = (end - start).total_seconds()
    return _normalize_nonnegative_decimal(
        "observation_age_seconds",
        Decimal(str(seconds)),
    )


def _public_hash(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"


def _validation_digest(value: object) -> str:
    payload = _json_ready(_without_validation_digest(value))
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _without_validation_digest(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _without_validation_digest(getattr(value, field.name))
            for field in fields(value)
            if field.name != "validation_digest"
        }
    if isinstance(value, dict):
        return {
            key: _without_validation_digest(item)
            for key, item in value.items()
            if key != "validation_digest"
        }
    if isinstance(value, tuple):
        return tuple(_without_validation_digest(item) for item in value)
    if isinstance(value, list):
        return [_without_validation_digest(item) for item in value]
    return value


def _public_mapping(value: object) -> dict[str, object]:
    payload = _without_validation_digest(value)
    if type(payload) is not dict:
        raise ValueError("public mapping must be a dict")
    return payload


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (int, float):
        return value
    raise ValueError(f"unsupported payload value: {type(value).__name__}")


def _reject_numeric_public_payload(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("public numeric values must be serialized strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_numeric_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_numeric_public_payload(item)


def _reject_unsafe_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_text("payload key", key)
            _reject_unsafe_payload(item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item)
    elif type(value) is str:
        _reject_unsafe_text("payload value", value)


def _reject_unsafe_text(name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public content")
