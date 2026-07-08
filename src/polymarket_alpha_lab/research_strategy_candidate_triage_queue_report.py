"""Pure report-only triage queue reducer."""

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
    "DEFAULT_RESEARCH_STRATEGY_CANDIDATE_TRIAGE_QUEUE_REPORT_CONFIG_VERSION",
    "ResearchStrategyCandidateTriageQueueConfig",
    "ResearchStrategyCandidateTriageQueueInput",
    "ResearchStrategyCandidateTriageQueueReasonCodeCount",
    "ResearchStrategyCandidateTriageQueueReport",
    "ResearchStrategyCandidateTriageQueueRow",
    "build_research_strategy_candidate_triage_queue_report",
    "research_strategy_candidate_triage_queue_report_digest",
    "research_strategy_candidate_triage_queue_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_CANDIDATE_TRIAGE_QUEUE_REPORT_CONFIG_VERSION = (
    "research-strategy-candidate-triage-queue-report-v0"
)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
NO_INPUTS_REASON = "research_strategy_candidate_triage_queue_no_inputs"
BASE_TRIAGE_SCORE = Decimal("0.040000")

_UNSAFE_TEXT_PARTS = (
    "raw_candidate_id",
    "mar" + "ket",
    "sl" + "ug",
    "ques" + "tion",
    "sou" + "rce",
    "r" + "ef",
    "u" + "rl",
    "d" + "sn",
    "ta" + "ble",
    "to" + "ken",
    "wal" + "let",
    "or" + "der",
    "tra" + "de",
    "tra" + "ding",
    "posi" + "tion",
    "b" + "uy",
    "se" + "ll",
    "rec" + "ommend",
    "au" + "th",
    "pri" + "vate_key",
    "api" + "_key",
    "se" + "cret",
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
class ResearchStrategyCandidateTriageQueueConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_CANDIDATE_TRIAGE_QUEUE_REPORT_CONFIG_VERSION
    )
    evidence_gap_watch: Decimal = Decimal("0.500000")
    evidence_gap_block: Decimal = Decimal("0.850000")
    cost_surface_watch: Decimal = Decimal("0.350000")
    cost_surface_block: Decimal = Decimal("0.750000")
    calibration_drift_watch: Decimal = Decimal("0.100000")
    calibration_drift_block: Decimal = Decimal("0.250000")
    team_assignment_watch: Decimal = Decimal("0.500000")
    team_assignment_block: Decimal = Decimal("0.800000")
    stale_data_watch_seconds: Decimal = Decimal("86400.000000")
    stale_data_block_seconds: Decimal = Decimal("259200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCandidateTriageQueueConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "evidence_gap_watch",
            "evidence_gap_block",
            "cost_surface_watch",
            "cost_surface_block",
            "calibration_drift_watch",
            "calibration_drift_block",
            "team_assignment_watch",
            "team_assignment_block",
            "stale_data_watch_seconds",
            "stale_data_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_at_most(
            "evidence_gap_watch",
            self.evidence_gap_watch,
            self.evidence_gap_block,
        )
        _require_at_most(
            "cost_surface_watch",
            self.cost_surface_watch,
            self.cost_surface_block,
        )
        _require_at_most(
            "calibration_drift_watch",
            self.calibration_drift_watch,
            self.calibration_drift_block,
        )
        _require_at_most(
            "team_assignment_watch",
            self.team_assignment_watch,
            self.team_assignment_block,
        )
        _require_at_most(
            "stale_data_watch_seconds",
            self.stale_data_watch_seconds,
            self.stale_data_block_seconds,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateTriageQueueInput(_FinalPublicDataclass):
    candidate_key: str
    team_key: str
    evidence_gap_score: Decimal
    cost_surface_score: Decimal
    calibration_drift_score: Decimal
    team_assignment_gap_score: Decimal
    data_observed_at: datetime
    evidence_gap_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCandidateTriageQueueInput, "input")
        _require_canonical_string("candidate_key", self.candidate_key)
        _require_canonical_string("team_key", self.team_key)
        for field_name in (
            "evidence_gap_score",
            "cost_surface_score",
            "calibration_drift_score",
            "team_assignment_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "data_observed_at",
            _as_utc("data_observed_at", self.data_observed_at),
        )
        object.__setattr__(
            self,
            "evidence_gap_codes",
            _normalize_reason_codes("evidence_gap_codes", self.evidence_gap_codes),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateTriageQueueRow(_FinalPublicDataclass):
    triage_rank: Decimal
    candidate_key: str
    team_key: str
    status: str
    evidence_gap_score: Decimal
    cost_surface_score: Decimal
    calibration_drift_score: Decimal
    team_assignment_gap_score: Decimal
    data_observed_at: datetime
    data_age_seconds: Decimal
    triage_score: Decimal
    evidence_gap_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCandidateTriageQueueRow, "row")
        object.__setattr__(
            self,
            "triage_rank",
            _normalize_positive_count("triage_rank", self.triage_rank),
        )
        _require_canonical_string("candidate_key", self.candidate_key)
        _require_canonical_string("team_key", self.team_key)
        _require_status("status", self.status)
        for field_name in (
            "evidence_gap_score",
            "cost_surface_score",
            "calibration_drift_score",
            "team_assignment_gap_score",
            "data_age_seconds",
            "triage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "data_observed_at",
            _as_utc("data_observed_at", self.data_observed_at),
        )
        object.__setattr__(
            self,
            "evidence_gap_codes",
            _normalize_reason_codes("evidence_gap_codes", self.evidence_gap_codes),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.status != _row_status(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateTriageQueueReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyCandidateTriageQueueReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyCandidateTriageQueueReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    evidence_gap_watch_count: Decimal
    cost_surface_watch_count: Decimal
    calibration_drift_watch_count: Decimal
    team_assignment_watch_count: Decimal
    stale_data_count: Decimal
    mean_triage_score: Decimal
    max_triage_score: Decimal
    status: str
    public_digest: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategyCandidateTriageQueueReasonCodeCount, ...]
    rows: tuple[ResearchStrategyCandidateTriageQueueRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyCandidateTriageQueueReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "evidence_gap_watch_count",
            "cost_surface_watch_count",
            "calibration_drift_watch_count",
            "team_assignment_watch_count",
            "stale_data_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("mean_triage_score", "max_triage_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
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
    ResearchStrategyCandidateTriageQueueConfig,
    ResearchStrategyCandidateTriageQueueInput,
    ResearchStrategyCandidateTriageQueueReasonCodeCount,
    ResearchStrategyCandidateTriageQueueReport,
    ResearchStrategyCandidateTriageQueueRow,
)


def build_research_strategy_candidate_triage_queue_report(
    candidates: Iterable[ResearchStrategyCandidateTriageQueueInput],
    *,
    config: ResearchStrategyCandidateTriageQueueConfig,
    generated_at: datetime,
) -> ResearchStrategyCandidateTriageQueueReport:
    if type(config) is not ResearchStrategyCandidateTriageQueueConfig:
        raise ValueError("config must be a ResearchStrategyCandidateTriageQueueConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(candidates)
    row_values = sorted(
        (
            _triage_row_values(candidate, config=config, generated_at=generated_at_utc)
            for candidate in inputs
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
    return ResearchStrategyCandidateTriageQueueReport(
        **values,
        public_digest=_digest_from_mapping(values),
    )


def research_strategy_candidate_triage_queue_report_digest(
    report: ResearchStrategyCandidateTriageQueueReport,
) -> str:
    if type(report) is not ResearchStrategyCandidateTriageQueueReport:
        raise ValueError("report must be a ResearchStrategyCandidateTriageQueueReport")
    _revalidate_report_for_payload(report)
    return _computed_report_digest(report)


def research_strategy_candidate_triage_queue_report_payload(
    report: ResearchStrategyCandidateTriageQueueReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyCandidateTriageQueueReport:
        raise ValueError("report must be a ResearchStrategyCandidateTriageQueueReport")
    _revalidate_report_for_payload(report)
    _reject_unsafe_public_payload("report", report)
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
class _TriageRowValues:
    candidate_key: str
    team_key: str
    status: str
    evidence_gap_score: Decimal
    cost_surface_score: Decimal
    calibration_drift_score: Decimal
    team_assignment_gap_score: Decimal
    data_observed_at: datetime
    data_age_seconds: Decimal
    triage_score: Decimal
    evidence_gap_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]


def _triage_row_values(
    candidate: ResearchStrategyCandidateTriageQueueInput,
    *,
    config: ResearchStrategyCandidateTriageQueueConfig,
    generated_at: datetime,
) -> _TriageRowValues:
    data_age_seconds = _data_age_seconds(candidate.data_observed_at, generated_at)
    triage_score = _triage_score(candidate)
    reason_codes = _row_reason_codes(
        candidate,
        data_age_seconds=data_age_seconds,
        config=config,
    )
    return _TriageRowValues(
        candidate_key=candidate.candidate_key,
        team_key=candidate.team_key,
        status=_row_status(reason_codes),
        evidence_gap_score=candidate.evidence_gap_score,
        cost_surface_score=candidate.cost_surface_score,
        calibration_drift_score=candidate.calibration_drift_score,
        team_assignment_gap_score=candidate.team_assignment_gap_score,
        data_observed_at=candidate.data_observed_at,
        data_age_seconds=data_age_seconds,
        triage_score=triage_score,
        evidence_gap_codes=candidate.evidence_gap_codes,
        reason_codes=reason_codes,
    )


def _row_from_values(
    triage_rank: Decimal,
    values: _TriageRowValues,
) -> ResearchStrategyCandidateTriageQueueRow:
    return ResearchStrategyCandidateTriageQueueRow(
        triage_rank=triage_rank,
        candidate_key=values.candidate_key,
        team_key=values.team_key,
        status=values.status,
        evidence_gap_score=values.evidence_gap_score,
        cost_surface_score=values.cost_surface_score,
        calibration_drift_score=values.calibration_drift_score,
        team_assignment_gap_score=values.team_assignment_gap_score,
        data_observed_at=values.data_observed_at,
        data_age_seconds=values.data_age_seconds,
        triage_score=values.triage_score,
        evidence_gap_codes=values.evidence_gap_codes,
        reason_codes=values.reason_codes,
    )


def _triage_score(candidate: ResearchStrategyCandidateTriageQueueInput) -> Decimal:
    return _quantize(
        candidate.evidence_gap_score
        + candidate.cost_surface_score
        + candidate.calibration_drift_score
        + candidate.team_assignment_gap_score
        + BASE_TRIAGE_SCORE,
    )


def _row_reason_codes(
    candidate: ResearchStrategyCandidateTriageQueueInput,
    *,
    data_age_seconds: Decimal,
    config: ResearchStrategyCandidateTriageQueueConfig,
) -> tuple[str, ...]:
    reason_codes = [*candidate.evidence_gap_codes, *candidate.reason_codes]
    if candidate.evidence_gap_score >= config.evidence_gap_block:
        reason_codes.append("evidence_gap_block")
    elif candidate.evidence_gap_score >= config.evidence_gap_watch:
        reason_codes.append("evidence_gap_watch")
    if candidate.cost_surface_score >= config.cost_surface_block:
        reason_codes.append("cost_surface_block")
    elif candidate.cost_surface_score >= config.cost_surface_watch:
        reason_codes.append("cost_surface_watch")
    if candidate.calibration_drift_score >= config.calibration_drift_block:
        reason_codes.append("calibration_drift_block")
    elif candidate.calibration_drift_score >= config.calibration_drift_watch:
        reason_codes.append("calibration_drift_watch")
    if candidate.team_assignment_gap_score >= config.team_assignment_block:
        reason_codes.append("team_assignment_block")
    elif candidate.team_assignment_gap_score >= config.team_assignment_watch:
        reason_codes.append("team_assignment_watch")
    if data_age_seconds > config.stale_data_block_seconds:
        reason_codes.append("data_stale_block")
    elif data_age_seconds > config.stale_data_watch_seconds:
        reason_codes.append("data_stale_watch")
    if not _has_attention_reason(reason_codes):
        reason_codes.append("triage_clear")
    return _normalize_reason_codes("reason_codes", tuple(sorted(reason_codes)))


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
    rows: tuple[ResearchStrategyCandidateTriageQueueRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _rollup_status(tuple(row.status for row in rows))
    suffix = "clear" if status == "pass" else status
    reason_codes = [f"research_strategy_candidate_triage_queue_{suffix}"]
    row_reason_codes = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
    )
    for reason_code in (
        "calibration_drift_block",
        "calibration_drift_watch",
        "cost_surface_block",
        "cost_surface_watch",
        "data_stale_block",
        "data_stale_watch",
        "evidence_gap_block",
        "evidence_gap_watch",
        "team_assignment_block",
        "team_assignment_watch",
    ):
        if reason_code in row_reason_codes:
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchStrategyCandidateTriageQueueRow, ...],
) -> tuple[ResearchStrategyCandidateTriageQueueReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyCandidateTriageQueueReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=COUNT_QUANTUM,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchStrategyCandidateTriageQueueReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _report_values(
    *,
    generated_at: datetime,
    config_version: str,
    rows: tuple[ResearchStrategyCandidateTriageQueueRow, ...],
) -> dict[str, Any]:
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "candidate_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "evidence_gap_watch_count": _kind_count(rows, "evidence_gap_"),
        "cost_surface_watch_count": _kind_count(rows, "cost_surface_"),
        "calibration_drift_watch_count": _kind_count(rows, "calibration_drift_"),
        "team_assignment_watch_count": _kind_count(rows, "team_assignment_"),
        "stale_data_count": _kind_count(rows, "data_stale_"),
        "mean_triage_score": _mean(tuple(row.triage_score for row in rows)),
        "max_triage_score": _max_decimal(tuple(row.triage_score for row in rows)),
        "status": _rollup_status(tuple(row.status for row in rows)),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _data_age_seconds(data_observed_at: datetime, generated_at: datetime) -> Decimal:
    seconds = Decimal(str((generated_at - _as_utc("data_observed_at", data_observed_at)).total_seconds()))
    age_seconds = _quantize(seconds)
    if age_seconds < ZERO:
        raise ValueError("data_observed_at must not be after generated_at")
    return age_seconds


def _normalize_inputs(
    candidates: Iterable[ResearchStrategyCandidateTriageQueueInput],
) -> tuple[ResearchStrategyCandidateTriageQueueInput, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        rows = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen_keys: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyCandidateTriageQueueInput:
            raise ValueError(
                "candidates must contain ResearchStrategyCandidateTriageQueueInput values",
            )
        _require_hard_flags("input", row)
        _reject_unsafe_public_payload("input", row)
        if row.candidate_key in seen_keys:
            raise ValueError("candidates must not contain duplicate candidate_key values")
        seen_keys.add(row.candidate_key)
    return rows


def _normalize_rows(
    rows: Iterable[ResearchStrategyCandidateTriageQueueRow],
) -> tuple[ResearchStrategyCandidateTriageQueueRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_keys: set[str] = set()
    for row in values:
        if type(row) is not ResearchStrategyCandidateTriageQueueRow:
            raise ValueError("rows must contain ResearchStrategyCandidateTriageQueueRow values")
        _require_hard_flags("row", row)
        _reject_unsafe_public_payload("row", row)
        if row.candidate_key in seen_keys:
            raise ValueError("rows must not contain duplicate candidate_key values")
        seen_keys.add(row.candidate_key)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must use canonical sequence")
    return values


def _normalize_reason_code_counts(
    rows: Iterable[ResearchStrategyCandidateTriageQueueReasonCodeCount],
) -> tuple[ResearchStrategyCandidateTriageQueueReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in values:
        if type(row) is not ResearchStrategyCandidateTriageQueueReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchStrategyCandidateTriageQueueReasonCodeCount values",
            )
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate reason_code values")
        seen_codes.add(row.reason_code)
    expected = tuple(sorted(values, key=lambda item: (-item.count, item.reason_code)))
    if values != expected:
        raise ValueError("reason_code_counts must be sorted by count then reason_code")
    return values


def _row_sort_key(
    row: ResearchStrategyCandidateTriageQueueRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -row.triage_score,
        row.candidate_key,
        row.team_key,
    )


def _row_values_sort_key(values: _TriageRowValues) -> tuple[Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[values.status],
        -values.triage_score,
        values.candidate_key,
        values.team_key,
    )


def _status_count(
    rows: tuple[ResearchStrategyCandidateTriageQueueRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _kind_count(
    rows: tuple[ResearchStrategyCandidateTriageQueueRow, ...],
    kind: str,
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if any(reason_code.startswith(kind) for reason_code in row.reason_codes)
        ),
    )


def _validate_report(report: ResearchStrategyCandidateTriageQueueReport) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.evidence_gap_watch_count != _kind_count(rows, "evidence_gap_"):
        raise ValueError("evidence_gap_watch_count must match rows")
    if report.cost_surface_watch_count != _kind_count(rows, "cost_surface_"):
        raise ValueError("cost_surface_watch_count must match rows")
    if report.calibration_drift_watch_count != _kind_count(rows, "calibration_drift_"):
        raise ValueError("calibration_drift_watch_count must match rows")
    if report.team_assignment_watch_count != _kind_count(rows, "team_assignment_"):
        raise ValueError("team_assignment_watch_count must match rows")
    if report.stale_data_count != _kind_count(rows, "data_stale_"):
        raise ValueError("stale_data_count must match rows")
    if report.mean_triage_score != _mean(tuple(row.triage_score for row in rows)):
        raise ValueError("mean_triage_score must match rows")
    if report.max_triage_score != _max_decimal(tuple(row.triage_score for row in rows)):
        raise ValueError("max_triage_score must match rows")
    if report.status != _rollup_status(tuple(row.status for row in rows)):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    for index, row in enumerate(rows, start=1):
        if row.triage_rank != _count(index):
            raise ValueError("triage_rank must match rows")


def _revalidate_report_for_payload(
    report: ResearchStrategyCandidateTriageQueueReport,
) -> None:
    _require_exact_type(report, ResearchStrategyCandidateTriageQueueReport, "report")
    _require_utc_datetime("generated_at", report.generated_at)
    _require_canonical_string("config_version", report.config_version)
    for field_name in (
        "candidate_count",
        "pass_count",
        "watch_count",
        "block_count",
        "evidence_gap_watch_count",
        "cost_surface_watch_count",
        "calibration_drift_watch_count",
        "team_assignment_watch_count",
        "stale_data_count",
        "mean_triage_score",
        "max_triage_score",
    ):
        _require_nonnegative_six_decimal_decimal(field_name, getattr(report, field_name))
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
    if type(row) is not ResearchStrategyCandidateTriageQueueRow:
        raise ValueError("rows must contain ResearchStrategyCandidateTriageQueueRow values")
    _require_positive_six_decimal_decimal("triage_rank", row.triage_rank)
    _require_canonical_string("candidate_key", row.candidate_key)
    _require_canonical_string("team_key", row.team_key)
    _require_status("status", row.status)
    for field_name in (
        "evidence_gap_score",
        "cost_surface_score",
        "calibration_drift_score",
        "team_assignment_gap_score",
        "data_age_seconds",
        "triage_score",
    ):
        _require_nonnegative_six_decimal_decimal(field_name, getattr(row, field_name))
    _require_utc_datetime("data_observed_at", row.data_observed_at)
    _require_reason_codes_tuple("evidence_gap_codes", row.evidence_gap_codes)
    if row.evidence_gap_codes != _normalize_reason_codes(
        "evidence_gap_codes",
        row.evidence_gap_codes,
    ):
        raise ValueError("evidence_gap_codes must use canonical sequence")
    _require_reason_codes_tuple("reason_codes", row.reason_codes)
    if row.reason_codes != _normalize_reason_codes("reason_codes", row.reason_codes):
        raise ValueError("reason_codes must use canonical sequence")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    _require_hard_flags("row", row)


def _revalidate_reason_code_count_for_payload(row: object) -> None:
    if type(row) is not ResearchStrategyCandidateTriageQueueReasonCodeCount:
        raise ValueError(
            "reason_code_counts must contain ResearchStrategyCandidateTriageQueueReasonCodeCount values",
        )
    _require_canonical_string("reason_code", row.reason_code)
    _require_positive_six_decimal_decimal("count", row.count)
    _require_hard_flags("reason_code_count", row)


def _computed_report_digest(report: ResearchStrategyCandidateTriageQueueReport) -> str:
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


def _normalize_reason_codes(label: str, values: tuple[str, ...]) -> tuple[str, ...]:
    _require_reason_codes_tuple(label, values)
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


def _require_at_most(label: str, value: Decimal, limit: Decimal) -> None:
    if value > limit:
        raise ValueError(f"{label} must be less than or equal to its block level")


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
