"""Deterministic report-only reducer for candidate triage playbooks."""

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
    "DEFAULT_RESEARCH_STRATEGY_CANDIDATE_TRIAGE_PLAYBOOK_REPORT_CONFIG_VERSION",
    "ResearchStrategyCandidateTriagePlaybookConfig",
    "ResearchStrategyCandidateTriagePlaybookInput",
    "ResearchStrategyCandidateTriagePlaybookReasonCodeCount",
    "ResearchStrategyCandidateTriagePlaybookReport",
    "ResearchStrategyCandidateTriagePlaybookRow",
    "build_research_strategy_candidate_triage_playbook_report",
    "research_strategy_candidate_triage_playbook_report_digest",
    "research_strategy_candidate_triage_playbook_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_CANDIDATE_TRIAGE_PLAYBOOK_REPORT_CONFIG_VERSION = (
    "research-strategy-candidate-triage-playbook-report-v0"
)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FOUR = Decimal("4.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
NO_INPUTS_REASON = "strategy_candidate_triage_playbook_no_inputs"
REPORT_REASON_PRIORITY = (
    "evidence_quality_block",
    "evidence_quality_watch",
    "liquidity_cost_pressure_block",
    "liquidity_cost_pressure_watch",
    "probability_gap_block",
    "probability_gap_watch",
    "review_urgency_block",
    "review_urgency_watch",
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
class ResearchStrategyCandidateTriagePlaybookConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_CANDIDATE_TRIAGE_PLAYBOOK_REPORT_CONFIG_VERSION
    )
    evidence_quality_pass_floor: Decimal = Decimal("0.800000")
    evidence_quality_watch_floor: Decimal = Decimal("0.600000")
    probability_gap_pass_floor: Decimal = Decimal("0.050000")
    probability_gap_watch_floor: Decimal = Decimal("0.020000")
    liquidity_cost_pressure_watch: Decimal = Decimal("0.350000")
    liquidity_cost_pressure_block: Decimal = Decimal("0.750000")
    review_urgency_watch: Decimal = Decimal("0.400000")
    review_urgency_block: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCandidateTriagePlaybookConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_CANDIDATE_TRIAGE_PLAYBOOK_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "evidence_quality_pass_floor",
            "evidence_quality_watch_floor",
            "probability_gap_pass_floor",
            "probability_gap_watch_floor",
            "liquidity_cost_pressure_watch",
            "liquidity_cost_pressure_block",
            "review_urgency_watch",
            "review_urgency_block",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_at_least(
            "evidence_quality_pass_floor",
            self.evidence_quality_pass_floor,
            self.evidence_quality_watch_floor,
        )
        _require_at_least(
            "probability_gap_pass_floor",
            self.probability_gap_pass_floor,
            self.probability_gap_watch_floor,
        )
        _require_at_most(
            "liquidity_cost_pressure_watch",
            self.liquidity_cost_pressure_watch,
            self.liquidity_cost_pressure_block,
        )
        _require_at_most(
            "review_urgency_watch",
            self.review_urgency_watch,
            self.review_urgency_block,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateTriagePlaybookInput(_FinalPublicDataclass):
    triage_key: str
    evidence_quality_score: Decimal
    probability_gap: Decimal
    liquidity_cost_pressure: Decimal
    review_urgency: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCandidateTriagePlaybookInput, "input")
        _require_canonical_string("triage_key", self.triage_key)
        for field_name in (
            "evidence_quality_score",
            "probability_gap",
            "liquidity_cost_pressure",
            "review_urgency",
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
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateTriagePlaybookRow(_FinalPublicDataclass):
    aggregate_row_number: Decimal
    aggregate_row_hash: str
    status: str
    evidence_quality_score: Decimal
    probability_gap: Decimal
    liquidity_cost_pressure: Decimal
    review_urgency: Decimal
    playbook_priority_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCandidateTriagePlaybookRow, "row")
        object.__setattr__(
            self,
            "aggregate_row_number",
            _normalize_positive_count("aggregate_row_number", self.aggregate_row_number),
        )
        _require_public_digest("aggregate_row_hash", self.aggregate_row_hash)
        _require_status("status", self.status)
        for field_name in (
            "evidence_quality_score",
            "probability_gap",
            "liquidity_cost_pressure",
            "review_urgency",
            "playbook_priority_score",
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
        if self.playbook_priority_score != _playbook_priority_score(
            self.evidence_quality_score,
            self.probability_gap,
            self.liquidity_cost_pressure,
            self.review_urgency,
        ):
            raise ValueError("playbook_priority_score must match row inputs")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateTriagePlaybookReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCandidateTriagePlaybookReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateTriagePlaybookReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    evidence_quality_attention_count: Decimal
    probability_gap_attention_count: Decimal
    liquidity_cost_attention_count: Decimal
    review_urgency_attention_count: Decimal
    mean_evidence_quality_score: Decimal
    mean_probability_gap: Decimal
    mean_liquidity_cost_pressure: Decimal
    mean_review_urgency: Decimal
    mean_playbook_priority_score: Decimal
    max_review_urgency: Decimal
    status: str
    public_digest: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategyCandidateTriagePlaybookReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchStrategyCandidateTriagePlaybookRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCandidateTriagePlaybookReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "evidence_quality_attention_count",
            "probability_gap_attention_count",
            "liquidity_cost_attention_count",
            "review_urgency_attention_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_evidence_quality_score",
            "mean_probability_gap",
            "mean_liquidity_cost_pressure",
            "mean_review_urgency",
            "mean_playbook_priority_score",
            "max_review_urgency",
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
    ResearchStrategyCandidateTriagePlaybookConfig,
    ResearchStrategyCandidateTriagePlaybookInput,
    ResearchStrategyCandidateTriagePlaybookReasonCodeCount,
    ResearchStrategyCandidateTriagePlaybookReport,
    ResearchStrategyCandidateTriagePlaybookRow,
)


def build_research_strategy_candidate_triage_playbook_report(
    candidates: Iterable[ResearchStrategyCandidateTriagePlaybookInput],
    *,
    config: ResearchStrategyCandidateTriagePlaybookConfig,
    generated_at: datetime,
) -> ResearchStrategyCandidateTriagePlaybookReport:
    if type(config) is not ResearchStrategyCandidateTriagePlaybookConfig:
        raise ValueError("config must be a ResearchStrategyCandidateTriagePlaybookConfig")
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
    return ResearchStrategyCandidateTriagePlaybookReport(
        **values,
        public_digest=_digest_from_mapping(values),
    )


def research_strategy_candidate_triage_playbook_report_digest(
    report: ResearchStrategyCandidateTriagePlaybookReport,
) -> str:
    if type(report) is not ResearchStrategyCandidateTriagePlaybookReport:
        raise ValueError("report must be a ResearchStrategyCandidateTriagePlaybookReport")
    _revalidate_report_for_payload(report)
    return _computed_report_digest(report)


def research_strategy_candidate_triage_playbook_report_payload(
    report: ResearchStrategyCandidateTriagePlaybookReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyCandidateTriagePlaybookReport:
        raise ValueError("report must be a ResearchStrategyCandidateTriagePlaybookReport")
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
    evidence_quality_score: Decimal
    probability_gap: Decimal
    liquidity_cost_pressure: Decimal
    review_urgency: Decimal
    playbook_priority_score: Decimal
    reason_codes: tuple[str, ...]


def _row_values_for_input(
    value: ResearchStrategyCandidateTriagePlaybookInput,
    *,
    config: ResearchStrategyCandidateTriagePlaybookConfig,
) -> _RowValues:
    reason_codes = _row_reason_codes(value, config=config)
    return _RowValues(
        aggregate_row_hash=_public_hash(value.triage_key),
        status=_row_status(reason_codes),
        evidence_quality_score=value.evidence_quality_score,
        probability_gap=value.probability_gap,
        liquidity_cost_pressure=value.liquidity_cost_pressure,
        review_urgency=value.review_urgency,
        playbook_priority_score=_playbook_priority_score(
            value.evidence_quality_score,
            value.probability_gap,
            value.liquidity_cost_pressure,
            value.review_urgency,
        ),
        reason_codes=reason_codes,
    )


def _row_from_values(
    aggregate_row_number: Decimal,
    values: _RowValues,
) -> ResearchStrategyCandidateTriagePlaybookRow:
    return ResearchStrategyCandidateTriagePlaybookRow(
        aggregate_row_number=aggregate_row_number,
        aggregate_row_hash=values.aggregate_row_hash,
        status=values.status,
        evidence_quality_score=values.evidence_quality_score,
        probability_gap=values.probability_gap,
        liquidity_cost_pressure=values.liquidity_cost_pressure,
        review_urgency=values.review_urgency,
        playbook_priority_score=values.playbook_priority_score,
        reason_codes=values.reason_codes,
    )


def _row_reason_codes(
    value: ResearchStrategyCandidateTriagePlaybookInput,
    *,
    config: ResearchStrategyCandidateTriagePlaybookConfig,
) -> tuple[str, ...]:
    reason_codes = [*value.reason_codes]
    _append_floor_reason(
        reason_codes,
        "evidence_quality",
        value.evidence_quality_score,
        config.evidence_quality_pass_floor,
        config.evidence_quality_watch_floor,
    )
    _append_floor_reason(
        reason_codes,
        "probability_gap",
        value.probability_gap,
        config.probability_gap_pass_floor,
        config.probability_gap_watch_floor,
    )
    _append_pressure_reason(
        reason_codes,
        "liquidity_cost_pressure",
        value.liquidity_cost_pressure,
        config.liquidity_cost_pressure_watch,
        config.liquidity_cost_pressure_block,
    )
    _append_pressure_reason(
        reason_codes,
        "review_urgency",
        value.review_urgency,
        config.review_urgency_watch,
        config.review_urgency_block,
    )
    if not _has_attention_reason(reason_codes):
        reason_codes.append("strategy_candidate_triage_playbook_clear")
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


def _append_pressure_reason(
    reason_codes: list[str],
    prefix: str,
    score: Decimal,
    watch_level: Decimal,
    block_level: Decimal,
) -> None:
    if score >= block_level:
        reason_codes.append(f"{prefix}_block")
    elif score >= watch_level:
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
    rows: tuple[ResearchStrategyCandidateTriagePlaybookRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _rollup_status(tuple(row.status for row in rows))
    reason_codes = [f"strategy_candidate_triage_playbook_{status}"]
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
    rows: tuple[ResearchStrategyCandidateTriagePlaybookRow, ...],
) -> tuple[ResearchStrategyCandidateTriagePlaybookReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyCandidateTriagePlaybookReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=COUNT_QUANTUM,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchStrategyCandidateTriagePlaybookReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _report_values(
    *,
    generated_at: datetime,
    config_version: str,
    rows: tuple[ResearchStrategyCandidateTriagePlaybookRow, ...],
) -> dict[str, Any]:
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "candidate_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "evidence_quality_attention_count": _kind_count(rows, "evidence_quality_"),
        "probability_gap_attention_count": _kind_count(rows, "probability_gap_"),
        "liquidity_cost_attention_count": _kind_count(rows, "liquidity_cost_pressure_"),
        "review_urgency_attention_count": _kind_count(rows, "review_urgency_"),
        "mean_evidence_quality_score": _mean(
            tuple(row.evidence_quality_score for row in rows),
        ),
        "mean_probability_gap": _mean(tuple(row.probability_gap for row in rows)),
        "mean_liquidity_cost_pressure": _mean(
            tuple(row.liquidity_cost_pressure for row in rows),
        ),
        "mean_review_urgency": _mean(tuple(row.review_urgency for row in rows)),
        "mean_playbook_priority_score": _mean(
            tuple(row.playbook_priority_score for row in rows),
        ),
        "max_review_urgency": _max_decimal(tuple(row.review_urgency for row in rows)),
        "status": _rollup_status(tuple(row.status for row in rows)),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _normalize_inputs(
    candidates: Iterable[ResearchStrategyCandidateTriagePlaybookInput],
) -> tuple[ResearchStrategyCandidateTriagePlaybookInput, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        rows = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen_keys: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyCandidateTriagePlaybookInput:
            raise ValueError(
                "candidates must contain ResearchStrategyCandidateTriagePlaybookInput values",
            )
        _require_hard_flags("input", row)
        _reject_unsafe_public_payload("input", row)
        if row.triage_key in seen_keys:
            raise ValueError("candidates must not contain duplicate triage_key values")
        seen_keys.add(row.triage_key)
    return rows


def _normalize_rows(
    rows: Iterable[ResearchStrategyCandidateTriagePlaybookRow],
) -> tuple[ResearchStrategyCandidateTriagePlaybookRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_hashes: set[str] = set()
    for row in values:
        if type(row) is not ResearchStrategyCandidateTriagePlaybookRow:
            raise ValueError(
                "rows must contain ResearchStrategyCandidateTriagePlaybookRow values",
            )
        _require_hard_flags("row", row)
        _reject_unsafe_public_payload("row", row)
        if row.aggregate_row_hash in seen_hashes:
            raise ValueError("rows must not contain duplicate aggregate_row_hash values")
        seen_hashes.add(row.aggregate_row_hash)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must use canonical sequence")
    return values


def _normalize_reason_code_counts(
    rows: Iterable[ResearchStrategyCandidateTriagePlaybookReasonCodeCount],
) -> tuple[ResearchStrategyCandidateTriagePlaybookReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in values:
        if type(row) is not ResearchStrategyCandidateTriagePlaybookReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchStrategyCandidateTriagePlaybookReasonCodeCount values",
            )
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate reason_code values")
        seen_codes.add(row.reason_code)
    expected = tuple(sorted(values, key=lambda item: (-item.count, item.reason_code)))
    if values != expected:
        raise ValueError("reason_code_counts must use canonical sequence")
    return values


def _row_sort_key(
    row: ResearchStrategyCandidateTriagePlaybookRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -row.playbook_priority_score,
        -row.review_urgency,
        row.aggregate_row_hash,
    )


def _row_values_sort_key(values: _RowValues) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[values.status],
        -values.playbook_priority_score,
        -values.review_urgency,
        values.aggregate_row_hash,
    )


def _status_count(
    rows: tuple[ResearchStrategyCandidateTriagePlaybookRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _kind_count(
    rows: tuple[ResearchStrategyCandidateTriagePlaybookRow, ...],
    kind: str,
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if any(reason_code.startswith(kind) for reason_code in row.reason_codes)
        ),
    )


def _validate_report(report: ResearchStrategyCandidateTriagePlaybookReport) -> None:
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
        ("evidence_quality_attention_count", "evidence_quality_"),
        ("probability_gap_attention_count", "probability_gap_"),
        ("liquidity_cost_attention_count", "liquidity_cost_pressure_"),
        ("review_urgency_attention_count", "review_urgency_"),
    ):
        if getattr(report, field_name) != _kind_count(rows, kind):
            raise ValueError(f"{field_name} must match rows")
    for row_field_name in (
        "evidence_quality_score",
        "probability_gap",
        "liquidity_cost_pressure",
        "review_urgency",
        "playbook_priority_score",
    ):
        report_field_name = (
            f"mean_{row_field_name}"
            if row_field_name != "playbook_priority_score"
            else "mean_playbook_priority_score"
        )
        if getattr(report, report_field_name) != _mean(
            tuple(getattr(row, row_field_name) for row in rows),
        ):
            raise ValueError(f"{report_field_name} must match rows")
    if report.max_review_urgency != _max_decimal(
        tuple(row.review_urgency for row in rows),
    ):
        raise ValueError("max_review_urgency must match rows")
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
    report: ResearchStrategyCandidateTriagePlaybookReport,
) -> None:
    _require_exact_type(report, ResearchStrategyCandidateTriagePlaybookReport, "report")
    _require_utc_datetime("generated_at", report.generated_at)
    _require_canonical_string("config_version", report.config_version)
    for field_name in (
        "candidate_count",
        "pass_count",
        "watch_count",
        "block_count",
        "evidence_quality_attention_count",
        "probability_gap_attention_count",
        "liquidity_cost_attention_count",
        "review_urgency_attention_count",
    ):
        _require_nonnegative_six_decimal_decimal(field_name, getattr(report, field_name))
    for field_name in (
        "mean_evidence_quality_score",
        "mean_probability_gap",
        "mean_liquidity_cost_pressure",
        "mean_review_urgency",
        "mean_playbook_priority_score",
        "max_review_urgency",
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
    if type(row) is not ResearchStrategyCandidateTriagePlaybookRow:
        raise ValueError("rows must contain ResearchStrategyCandidateTriagePlaybookRow values")
    _require_positive_six_decimal_decimal(
        "aggregate_row_number",
        row.aggregate_row_number,
    )
    _require_public_digest("aggregate_row_hash", row.aggregate_row_hash)
    _require_status("status", row.status)
    for field_name in (
        "evidence_quality_score",
        "probability_gap",
        "liquidity_cost_pressure",
        "review_urgency",
        "playbook_priority_score",
    ):
        _require_probability_six_decimal_decimal(field_name, getattr(row, field_name))
    _require_reason_codes_tuple("reason_codes", row.reason_codes)
    if row.reason_codes != _normalize_reason_codes("reason_codes", row.reason_codes):
        raise ValueError("reason_codes must use canonical sequence")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.playbook_priority_score != _playbook_priority_score(
        row.evidence_quality_score,
        row.probability_gap,
        row.liquidity_cost_pressure,
        row.review_urgency,
    ):
        raise ValueError("playbook_priority_score must match row inputs")
    _require_hard_flags("row", row)


def _revalidate_reason_code_count_for_payload(row: object) -> None:
    if type(row) is not ResearchStrategyCandidateTriagePlaybookReasonCodeCount:
        raise ValueError(
            "reason_code_counts must contain ResearchStrategyCandidateTriagePlaybookReasonCodeCount values",
        )
    _require_canonical_string("reason_code", row.reason_code)
    _require_positive_six_decimal_decimal("count", row.count)
    _require_hard_flags("reason_code_count", row)


def _playbook_priority_score(
    evidence_quality_score: Decimal,
    probability_gap: Decimal,
    liquidity_cost_pressure: Decimal,
    review_urgency: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            (
                (ONE - evidence_quality_score)
                + (ONE - probability_gap)
                + liquidity_cost_pressure
                + review_urgency
            )
            / FOUR,
        )


def _public_hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _computed_report_digest(
    report: ResearchStrategyCandidateTriagePlaybookReport,
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
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
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
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
            )
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
    if values != normalized and not allow_empty:
        raise ValueError(f"{label} must use canonical sequence")
    return normalized


def _normalize_report_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    _require_reason_codes_tuple("reason_codes", values)
    if not values:
        raise ValueError("reason_codes must not be empty")
    for value in values:
        _require_canonical_string("reason_codes", value)
    return values


def _require_reason_codes_tuple(label: str, values: object) -> None:
    if type(values) is not tuple:
        raise ValueError(f"{label} must be a tuple")
    for value in values:
        _require_canonical_string(label, value)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise TypeError(f"{label} must be {expected_type.__name__}")


def _require_canonical_string(label: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    if not value:
        raise ValueError(f"{label} must not be empty")
    if value != value.strip():
        raise ValueError(f"{label} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{label} must be single-line text")
    _reject_unsafe_text(label, value)


def _require_status(label: str, value: object) -> None:
    if value not in STATUSES:
        raise ValueError(f"{label} must be pass, watch, or block")


def _require_public_digest(label: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{label} must be a SHA-256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")


def _as_utc(label: str, value: datetime) -> datetime:
    _require_aware_datetime(label, value)
    return value.astimezone(UTC)


def _require_aware_datetime(label: str, value: object) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{label} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")


def _require_utc_datetime(label: str, value: object) -> None:
    _require_aware_datetime(label, value)
    if value.tzinfo is not UTC:
        raise ValueError(f"{label} must be UTC")


def _normalize_probability_decimal(label: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(label, value)
    if normalized > ONE:
        raise ValueError(f"{label} must be less than or equal to 1.000000")
    return normalized


def _normalize_nonnegative_decimal(label: str, value: object) -> Decimal:
    normalized = _normalize_decimal(label, value)
    if normalized < ZERO:
        raise ValueError(f"{label} must be nonnegative")
    return normalized


def _normalize_positive_count(label: str, value: object) -> Decimal:
    normalized = _normalize_decimal(label, value)
    if normalized <= ZERO:
        raise ValueError(f"{label} must be positive")
    return normalized


def _normalize_decimal(label: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{label} must be a Decimal")
    return _quantize(value)


def _require_nonnegative_six_decimal_decimal(label: str, value: object) -> None:
    normalized = _require_six_decimal_decimal(label, value)
    if normalized < ZERO:
        raise ValueError(f"{label} must be nonnegative")


def _require_positive_six_decimal_decimal(label: str, value: object) -> None:
    normalized = _require_six_decimal_decimal(label, value)
    if normalized <= ZERO:
        raise ValueError(f"{label} must be positive")


def _require_probability_six_decimal_decimal(label: str, value: object) -> None:
    normalized = _require_six_decimal_decimal(label, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{label} must be between 0.000000 and 1.000000")


def _require_six_decimal_decimal(label: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{label} must be a Decimal")
    if value != value.quantize(QUANTUM):
        raise ValueError(f"{label} must have six decimal places")
    return value


def _require_at_least(label: str, value: Decimal, floor: Decimal) -> None:
    if value < floor:
        raise ValueError(f"{label} must be greater than or equal to watch floor")


def _require_at_most(label: str, value: Decimal, ceiling: Decimal) -> None:
    if value > ceiling:
        raise ValueError(f"{label} must be less than or equal to block level")


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / _count(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)
