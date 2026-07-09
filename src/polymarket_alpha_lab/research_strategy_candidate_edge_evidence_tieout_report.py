"""Pure edge evidence tieout report for screened research candidates."""

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
    "DEFAULT_RESEARCH_STRATEGY_CANDIDATE_EDGE_EVIDENCE_TIEOUT_REPORT_CONFIG_VERSION",
    "ResearchStrategyCandidateEdgeEvidenceTieoutConfig",
    "ResearchStrategyCandidateEdgeEvidenceTieoutInput",
    "ResearchStrategyCandidateEdgeEvidenceTieoutReasonCodeCount",
    "ResearchStrategyCandidateEdgeEvidenceTieoutReport",
    "ResearchStrategyCandidateEdgeEvidenceTieoutRow",
    "build_research_strategy_candidate_edge_evidence_tieout_report",
    "research_strategy_candidate_edge_evidence_tieout_report_digest",
    "research_strategy_candidate_edge_evidence_tieout_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_CANDIDATE_EDGE_EVIDENCE_TIEOUT_REPORT_CONFIG_VERSION = (
    "research-strategy-candidate-edge-evidence-tieout-report-v0"
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
NO_INPUTS_REASON = "candidate_edge_evidence_tieout_no_inputs"
REPORT_REASON_PRIORITY = (
    "alignment_block",
    "alignment_watch",
    "edge_decay_pressure_block",
    "edge_decay_pressure_watch",
    "evidence_quorum_block",
    "evidence_quorum_watch",
    "manual_review_pressure_block",
    "manual_review_pressure_watch",
    "unresolved_conflict_pressure_block",
    "unresolved_conflict_pressure_watch",
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
class ResearchStrategyCandidateEdgeEvidenceTieoutConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_CANDIDATE_EDGE_EVIDENCE_TIEOUT_REPORT_CONFIG_VERSION
    )
    alignment_pass_floor: Decimal = Decimal("0.800000")
    alignment_watch_floor: Decimal = Decimal("0.600000")
    evidence_quorum_pass_floor: Decimal = Decimal("0.800000")
    evidence_quorum_watch_floor: Decimal = Decimal("0.600000")
    edge_decay_pressure_watch: Decimal = Decimal("0.400000")
    edge_decay_pressure_block: Decimal = Decimal("0.750000")
    unresolved_conflict_pressure_watch: Decimal = Decimal("0.400000")
    unresolved_conflict_pressure_block: Decimal = Decimal("0.700000")
    manual_review_pressure_watch: Decimal = Decimal("0.400000")
    manual_review_pressure_block: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCandidateEdgeEvidenceTieoutConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_CANDIDATE_EDGE_EVIDENCE_TIEOUT_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "alignment_pass_floor",
            "alignment_watch_floor",
            "evidence_quorum_pass_floor",
            "evidence_quorum_watch_floor",
            "edge_decay_pressure_watch",
            "edge_decay_pressure_block",
            "unresolved_conflict_pressure_watch",
            "unresolved_conflict_pressure_block",
            "manual_review_pressure_watch",
            "manual_review_pressure_block",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_at_least(
            "alignment_pass_floor",
            self.alignment_pass_floor,
            self.alignment_watch_floor,
        )
        _require_at_least(
            "evidence_quorum_pass_floor",
            self.evidence_quorum_pass_floor,
            self.evidence_quorum_watch_floor,
        )
        _require_at_most(
            "edge_decay_pressure_watch",
            self.edge_decay_pressure_watch,
            self.edge_decay_pressure_block,
        )
        _require_at_most(
            "unresolved_conflict_pressure_watch",
            self.unresolved_conflict_pressure_watch,
            self.unresolved_conflict_pressure_block,
        )
        _require_at_most(
            "manual_review_pressure_watch",
            self.manual_review_pressure_watch,
            self.manual_review_pressure_block,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateEdgeEvidenceTieoutInput(_FinalPublicDataclass):
    tieout_key: str
    edge_score: Decimal
    evidence_support_score: Decimal
    evidence_quorum_score: Decimal
    edge_decay_pressure: Decimal
    unresolved_conflict_pressure: Decimal
    manual_review_pressure: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCandidateEdgeEvidenceTieoutInput,
            "input",
        )
        _require_canonical_string("tieout_key", self.tieout_key)
        for field_name in (
            "edge_score",
            "evidence_support_score",
            "evidence_quorum_score",
            "edge_decay_pressure",
            "unresolved_conflict_pressure",
            "manual_review_pressure",
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
class ResearchStrategyCandidateEdgeEvidenceTieoutRow(_FinalPublicDataclass):
    aggregate_row_number: Decimal
    aggregate_row_hash: str
    status: str
    edge_score: Decimal
    evidence_support_score: Decimal
    alignment_score: Decimal
    evidence_quorum_score: Decimal
    edge_decay_pressure: Decimal
    unresolved_conflict_pressure: Decimal
    manual_review_pressure: Decimal
    tieout_readiness_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCandidateEdgeEvidenceTieoutRow, "row")
        object.__setattr__(
            self,
            "aggregate_row_number",
            _normalize_positive_count(
                "aggregate_row_number",
                self.aggregate_row_number,
            ),
        )
        _require_public_digest("aggregate_row_hash", self.aggregate_row_hash)
        _require_status("status", self.status)
        for field_name in (
            "edge_score",
            "evidence_support_score",
            "alignment_score",
            "evidence_quorum_score",
            "edge_decay_pressure",
            "unresolved_conflict_pressure",
            "manual_review_pressure",
            "tieout_readiness_score",
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
        if self.alignment_score != _alignment_score(
            self.edge_score,
            self.evidence_support_score,
        ):
            raise ValueError("alignment_score must match scores")
        if self.tieout_readiness_score != _tieout_readiness_score(
            self.alignment_score,
            self.evidence_quorum_score,
            self.edge_decay_pressure,
            self.unresolved_conflict_pressure,
            self.manual_review_pressure,
        ):
            raise ValueError("tieout_readiness_score must match scores")
        if self.status != _row_status(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateEdgeEvidenceTieoutReasonCodeCount(
    _FinalPublicDataclass,
):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCandidateEdgeEvidenceTieoutReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateEdgeEvidenceTieoutReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    alignment_attention_count: Decimal
    evidence_quorum_attention_count: Decimal
    edge_decay_attention_count: Decimal
    unresolved_conflict_attention_count: Decimal
    manual_review_attention_count: Decimal
    mean_edge_score: Decimal
    mean_evidence_support_score: Decimal
    mean_alignment_score: Decimal
    mean_evidence_quorum_score: Decimal
    mean_tieout_readiness_score: Decimal
    max_edge_decay_pressure: Decimal
    max_unresolved_conflict_pressure: Decimal
    max_manual_review_pressure: Decimal
    status: str
    public_digest: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategyCandidateEdgeEvidenceTieoutReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchStrategyCandidateEdgeEvidenceTieoutRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCandidateEdgeEvidenceTieoutReport, "report")
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
            "alignment_attention_count",
            "evidence_quorum_attention_count",
            "edge_decay_attention_count",
            "unresolved_conflict_attention_count",
            "manual_review_attention_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_edge_score",
            "mean_evidence_support_score",
            "mean_alignment_score",
            "mean_evidence_quorum_score",
            "mean_tieout_readiness_score",
            "max_edge_decay_pressure",
            "max_unresolved_conflict_pressure",
            "max_manual_review_pressure",
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
    ResearchStrategyCandidateEdgeEvidenceTieoutConfig,
    ResearchStrategyCandidateEdgeEvidenceTieoutInput,
    ResearchStrategyCandidateEdgeEvidenceTieoutReasonCodeCount,
    ResearchStrategyCandidateEdgeEvidenceTieoutReport,
    ResearchStrategyCandidateEdgeEvidenceTieoutRow,
)


def build_research_strategy_candidate_edge_evidence_tieout_report(
    candidates: Iterable[ResearchStrategyCandidateEdgeEvidenceTieoutInput],
    *,
    config: ResearchStrategyCandidateEdgeEvidenceTieoutConfig,
    generated_at: datetime,
) -> ResearchStrategyCandidateEdgeEvidenceTieoutReport:
    if type(config) is not ResearchStrategyCandidateEdgeEvidenceTieoutConfig:
        raise ValueError(
            "config must be a ResearchStrategyCandidateEdgeEvidenceTieoutConfig",
        )
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(candidates)
    row_values = sorted(
        (
            _row_values_for_input(value, config=config)
            for value in inputs
        ),
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
    return ResearchStrategyCandidateEdgeEvidenceTieoutReport(
        **values,
        public_digest=_digest_from_mapping(values),
    )


def research_strategy_candidate_edge_evidence_tieout_report_digest(
    report: ResearchStrategyCandidateEdgeEvidenceTieoutReport,
) -> str:
    if type(report) is not ResearchStrategyCandidateEdgeEvidenceTieoutReport:
        raise ValueError(
            "report must be a ResearchStrategyCandidateEdgeEvidenceTieoutReport",
        )
    _revalidate_report_for_payload(report)
    return _computed_report_digest(report)


def research_strategy_candidate_edge_evidence_tieout_report_payload(
    report: ResearchStrategyCandidateEdgeEvidenceTieoutReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyCandidateEdgeEvidenceTieoutReport:
        raise ValueError(
            "report must be a ResearchStrategyCandidateEdgeEvidenceTieoutReport",
        )
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
    edge_score: Decimal
    evidence_support_score: Decimal
    alignment_score: Decimal
    evidence_quorum_score: Decimal
    edge_decay_pressure: Decimal
    unresolved_conflict_pressure: Decimal
    manual_review_pressure: Decimal
    tieout_readiness_score: Decimal
    reason_codes: tuple[str, ...]


def _row_values_for_input(
    value: ResearchStrategyCandidateEdgeEvidenceTieoutInput,
    *,
    config: ResearchStrategyCandidateEdgeEvidenceTieoutConfig,
) -> _RowValues:
    alignment_score = _alignment_score(value.edge_score, value.evidence_support_score)
    tieout_readiness_score = _tieout_readiness_score(
        alignment_score,
        value.evidence_quorum_score,
        value.edge_decay_pressure,
        value.unresolved_conflict_pressure,
        value.manual_review_pressure,
    )
    reason_codes = _row_reason_codes(
        value,
        config=config,
        alignment_score=alignment_score,
    )
    return _RowValues(
        aggregate_row_hash=_public_hash(value.tieout_key),
        status=_row_status(reason_codes),
        edge_score=value.edge_score,
        evidence_support_score=value.evidence_support_score,
        alignment_score=alignment_score,
        evidence_quorum_score=value.evidence_quorum_score,
        edge_decay_pressure=value.edge_decay_pressure,
        unresolved_conflict_pressure=value.unresolved_conflict_pressure,
        manual_review_pressure=value.manual_review_pressure,
        tieout_readiness_score=tieout_readiness_score,
        reason_codes=reason_codes,
    )


def _row_from_values(
    aggregate_row_number: Decimal,
    values: _RowValues,
) -> ResearchStrategyCandidateEdgeEvidenceTieoutRow:
    return ResearchStrategyCandidateEdgeEvidenceTieoutRow(
        aggregate_row_number=aggregate_row_number,
        aggregate_row_hash=values.aggregate_row_hash,
        status=values.status,
        edge_score=values.edge_score,
        evidence_support_score=values.evidence_support_score,
        alignment_score=values.alignment_score,
        evidence_quorum_score=values.evidence_quorum_score,
        edge_decay_pressure=values.edge_decay_pressure,
        unresolved_conflict_pressure=values.unresolved_conflict_pressure,
        manual_review_pressure=values.manual_review_pressure,
        tieout_readiness_score=values.tieout_readiness_score,
        reason_codes=values.reason_codes,
    )


def _row_reason_codes(
    value: ResearchStrategyCandidateEdgeEvidenceTieoutInput,
    *,
    config: ResearchStrategyCandidateEdgeEvidenceTieoutConfig,
    alignment_score: Decimal,
) -> tuple[str, ...]:
    reason_codes = [*value.reason_codes]
    _append_floor_reason(
        reason_codes,
        "alignment",
        alignment_score,
        config.alignment_pass_floor,
        config.alignment_watch_floor,
    )
    _append_floor_reason(
        reason_codes,
        "evidence_quorum",
        value.evidence_quorum_score,
        config.evidence_quorum_pass_floor,
        config.evidence_quorum_watch_floor,
    )
    _append_pressure_reason(
        reason_codes,
        "edge_decay_pressure",
        value.edge_decay_pressure,
        config.edge_decay_pressure_watch,
        config.edge_decay_pressure_block,
    )
    _append_pressure_reason(
        reason_codes,
        "unresolved_conflict_pressure",
        value.unresolved_conflict_pressure,
        config.unresolved_conflict_pressure_watch,
        config.unresolved_conflict_pressure_block,
    )
    _append_pressure_reason(
        reason_codes,
        "manual_review_pressure",
        value.manual_review_pressure,
        config.manual_review_pressure_watch,
        config.manual_review_pressure_block,
    )
    if not _has_attention_reason(reason_codes):
        reason_codes.append("edge_evidence_tieout_clear")
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
    pressure: Decimal,
    watch_limit: Decimal,
    block_limit: Decimal,
) -> None:
    if pressure >= block_limit:
        reason_codes.append(f"{prefix}_block")
    elif pressure >= watch_limit:
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
    rows: tuple[ResearchStrategyCandidateEdgeEvidenceTieoutRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _rollup_status(tuple(row.status for row in rows))
    reason_codes = [f"candidate_edge_evidence_tieout_{status}"]
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
    rows: tuple[ResearchStrategyCandidateEdgeEvidenceTieoutRow, ...],
) -> tuple[ResearchStrategyCandidateEdgeEvidenceTieoutReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyCandidateEdgeEvidenceTieoutReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=COUNT_QUANTUM,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchStrategyCandidateEdgeEvidenceTieoutReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _report_values(
    *,
    generated_at: datetime,
    config_version: str,
    rows: tuple[ResearchStrategyCandidateEdgeEvidenceTieoutRow, ...],
) -> dict[str, Any]:
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "candidate_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "alignment_attention_count": _kind_count(rows, "alignment_"),
        "evidence_quorum_attention_count": _kind_count(rows, "evidence_quorum_"),
        "edge_decay_attention_count": _kind_count(rows, "edge_decay_pressure_"),
        "unresolved_conflict_attention_count": _kind_count(
            rows,
            "unresolved_conflict_pressure_",
        ),
        "manual_review_attention_count": _kind_count(rows, "manual_review_pressure_"),
        "mean_edge_score": _mean(tuple(row.edge_score for row in rows)),
        "mean_evidence_support_score": _mean(
            tuple(row.evidence_support_score for row in rows),
        ),
        "mean_alignment_score": _mean(tuple(row.alignment_score for row in rows)),
        "mean_evidence_quorum_score": _mean(
            tuple(row.evidence_quorum_score for row in rows),
        ),
        "mean_tieout_readiness_score": _mean(
            tuple(row.tieout_readiness_score for row in rows),
        ),
        "max_edge_decay_pressure": _max_decimal(
            tuple(row.edge_decay_pressure for row in rows),
        ),
        "max_unresolved_conflict_pressure": _max_decimal(
            tuple(row.unresolved_conflict_pressure for row in rows),
        ),
        "max_manual_review_pressure": _max_decimal(
            tuple(row.manual_review_pressure for row in rows),
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
    candidates: Iterable[ResearchStrategyCandidateEdgeEvidenceTieoutInput],
) -> tuple[ResearchStrategyCandidateEdgeEvidenceTieoutInput, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        rows = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen_keys: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyCandidateEdgeEvidenceTieoutInput:
            raise ValueError(
                "candidates must contain ResearchStrategyCandidateEdgeEvidenceTieoutInput values",
            )
        _require_hard_flags("input", row)
        _reject_unsafe_public_payload("input", row)
        if row.tieout_key in seen_keys:
            raise ValueError("candidates must not contain duplicate tieout_key values")
        seen_keys.add(row.tieout_key)
    return rows


def _normalize_rows(
    rows: Iterable[ResearchStrategyCandidateEdgeEvidenceTieoutRow],
) -> tuple[ResearchStrategyCandidateEdgeEvidenceTieoutRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_hashes: set[str] = set()
    for row in values:
        if type(row) is not ResearchStrategyCandidateEdgeEvidenceTieoutRow:
            raise ValueError(
                "rows must contain ResearchStrategyCandidateEdgeEvidenceTieoutRow values",
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
    rows: Iterable[ResearchStrategyCandidateEdgeEvidenceTieoutReasonCodeCount],
) -> tuple[ResearchStrategyCandidateEdgeEvidenceTieoutReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in values:
        if type(row) is not ResearchStrategyCandidateEdgeEvidenceTieoutReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchStrategyCandidateEdgeEvidenceTieoutReasonCodeCount values",
            )
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate reason_code values")
        seen_codes.add(row.reason_code)
    expected = tuple(sorted(values, key=lambda item: (-item.count, item.reason_code)))
    if values != expected:
        raise ValueError("reason_code_counts must use canonical sequence")
    return values


def _row_sort_key(
    row: ResearchStrategyCandidateEdgeEvidenceTieoutRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -_max_decimal(
            (
                row.edge_decay_pressure,
                row.unresolved_conflict_pressure,
                row.manual_review_pressure,
            ),
        ),
        -_tieout_readiness_gap(row.tieout_readiness_score),
        row.aggregate_row_hash,
    )


def _row_values_sort_key(values: _RowValues) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[values.status],
        -_max_decimal(
            (
                values.edge_decay_pressure,
                values.unresolved_conflict_pressure,
                values.manual_review_pressure,
            ),
        ),
        -_tieout_readiness_gap(values.tieout_readiness_score),
        values.aggregate_row_hash,
    )


def _status_count(
    rows: tuple[ResearchStrategyCandidateEdgeEvidenceTieoutRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _kind_count(
    rows: tuple[ResearchStrategyCandidateEdgeEvidenceTieoutRow, ...],
    kind: str,
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if any(reason_code.startswith(kind) for reason_code in row.reason_codes)
        ),
    )


def _validate_report(report: ResearchStrategyCandidateEdgeEvidenceTieoutReport) -> None:
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
        ("alignment_attention_count", "alignment_"),
        ("evidence_quorum_attention_count", "evidence_quorum_"),
        ("edge_decay_attention_count", "edge_decay_pressure_"),
        ("unresolved_conflict_attention_count", "unresolved_conflict_pressure_"),
        ("manual_review_attention_count", "manual_review_pressure_"),
    ):
        if getattr(report, field_name) != _kind_count(rows, kind):
            raise ValueError(f"{field_name} must match rows")
    for field_name in (
        "edge_score",
        "evidence_support_score",
        "alignment_score",
        "evidence_quorum_score",
        "tieout_readiness_score",
    ):
        report_field_name = f"mean_{field_name}"
        if getattr(report, report_field_name) != _mean(
            tuple(getattr(row, field_name) for row in rows),
        ):
            raise ValueError(f"{report_field_name} must match rows")
    if report.max_edge_decay_pressure != _max_decimal(
        tuple(row.edge_decay_pressure for row in rows),
    ):
        raise ValueError("max_edge_decay_pressure must match rows")
    if report.max_unresolved_conflict_pressure != _max_decimal(
        tuple(row.unresolved_conflict_pressure for row in rows),
    ):
        raise ValueError("max_unresolved_conflict_pressure must match rows")
    if report.max_manual_review_pressure != _max_decimal(
        tuple(row.manual_review_pressure for row in rows),
    ):
        raise ValueError("max_manual_review_pressure must match rows")
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
    report: ResearchStrategyCandidateEdgeEvidenceTieoutReport,
) -> None:
    _require_exact_type(report, ResearchStrategyCandidateEdgeEvidenceTieoutReport, "report")
    _require_utc_datetime("generated_at", report.generated_at)
    _require_canonical_string("config_version", report.config_version)
    for field_name in (
        "candidate_count",
        "pass_count",
        "watch_count",
        "block_count",
        "alignment_attention_count",
        "evidence_quorum_attention_count",
        "edge_decay_attention_count",
        "unresolved_conflict_attention_count",
        "manual_review_attention_count",
    ):
        _require_nonnegative_six_decimal_decimal(field_name, getattr(report, field_name))
    for field_name in (
        "mean_edge_score",
        "mean_evidence_support_score",
        "mean_alignment_score",
        "mean_evidence_quorum_score",
        "mean_tieout_readiness_score",
        "max_edge_decay_pressure",
        "max_unresolved_conflict_pressure",
        "max_manual_review_pressure",
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
    if type(row) is not ResearchStrategyCandidateEdgeEvidenceTieoutRow:
        raise ValueError("rows must contain ResearchStrategyCandidateEdgeEvidenceTieoutRow values")
    _require_positive_six_decimal_decimal(
        "aggregate_row_number",
        row.aggregate_row_number,
    )
    _require_public_digest("aggregate_row_hash", row.aggregate_row_hash)
    _require_status("status", row.status)
    for field_name in (
        "edge_score",
        "evidence_support_score",
        "alignment_score",
        "evidence_quorum_score",
        "edge_decay_pressure",
        "unresolved_conflict_pressure",
        "manual_review_pressure",
        "tieout_readiness_score",
    ):
        _require_probability_six_decimal_decimal(field_name, getattr(row, field_name))
    _require_reason_codes_tuple("reason_codes", row.reason_codes)
    if row.reason_codes != _normalize_reason_codes("reason_codes", row.reason_codes):
        raise ValueError("reason_codes must use canonical sequence")
    if row.alignment_score != _alignment_score(row.edge_score, row.evidence_support_score):
        raise ValueError("alignment_score must match scores")
    if row.tieout_readiness_score != _tieout_readiness_score(
        row.alignment_score,
        row.evidence_quorum_score,
        row.edge_decay_pressure,
        row.unresolved_conflict_pressure,
        row.manual_review_pressure,
    ):
        raise ValueError("tieout_readiness_score must match scores")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    _require_hard_flags("row", row)


def _revalidate_reason_code_count_for_payload(row: object) -> None:
    if type(row) is not ResearchStrategyCandidateEdgeEvidenceTieoutReasonCodeCount:
        raise ValueError(
            "reason_code_counts must contain ResearchStrategyCandidateEdgeEvidenceTieoutReasonCodeCount values",
        )
    _require_canonical_string("reason_code", row.reason_code)
    _require_positive_six_decimal_decimal("count", row.count)
    _require_hard_flags("reason_code_count", row)


def _alignment_score(edge_score: Decimal, evidence_support_score: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(ONE - abs(edge_score - evidence_support_score))


def _tieout_readiness_score(
    alignment_score: Decimal,
    evidence_quorum_score: Decimal,
    edge_decay_pressure: Decimal,
    unresolved_conflict_pressure: Decimal,
    manual_review_pressure: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            (
                alignment_score
                + evidence_quorum_score
                + (ONE - edge_decay_pressure)
                + (ONE - unresolved_conflict_pressure)
                + (ONE - manual_review_pressure)
            )
            / FIVE,
        )


def _tieout_readiness_gap(value: Decimal) -> Decimal:
    return _quantize(ONE - value)


def _public_hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _computed_report_digest(
    report: ResearchStrategyCandidateEdgeEvidenceTieoutReport,
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


def _require_at_most(label: str, value: Decimal, limit: Decimal) -> None:
    if value > limit:
        raise ValueError(f"{label} must be at most its block level")


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
