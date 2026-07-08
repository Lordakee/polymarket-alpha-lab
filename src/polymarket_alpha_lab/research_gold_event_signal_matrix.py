"""Pure gold event signal matrix for public research prioritization."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import UNSAFE_SURFACE_FIELD_FRAGMENTS


__all__ = (
    "DEFAULT_RESEARCH_GOLD_EVENT_SIGNAL_MATRIX_CONFIG_VERSION",
    "GoldEventSignalMatrixCandidate",
    "GoldEventSignalMatrixConfig",
    "GoldEventSignalMatrixReasonCodeCount",
    "GoldEventSignalMatrixReport",
    "GoldEventSignalMatrixRow",
    "build_research_gold_event_signal_matrix_report",
    "research_gold_event_signal_matrix_digest",
    "research_gold_event_signal_matrix_payload",
)


DEFAULT_RESEARCH_GOLD_EVENT_SIGNAL_MATRIX_CONFIG_VERSION = (
    "research-gold-event-signal-matrix-v0"
)
DIGEST_PREFIX = "gold-event-signal-matrix-v0:"
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
NO_INPUTS_REASON = "gold_event_signal_matrix_no_inputs"


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
class GoldEventSignalMatrixConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_GOLD_EVENT_SIGNAL_MATRIX_CONFIG_VERSION
    dollar_pressure_watch: Decimal = Decimal("0.500000")
    dollar_pressure_block: Decimal = Decimal("0.800000")
    real_rate_pressure_watch: Decimal = Decimal("0.500000")
    real_rate_pressure_block: Decimal = Decimal("0.800000")
    central_bank_signal_watch: Decimal = Decimal("0.450000")
    central_bank_signal_block: Decimal = Decimal("0.750000")
    risk_appetite_shift_watch: Decimal = Decimal("0.450000")
    risk_appetite_shift_block: Decimal = Decimal("0.750000")
    source_confidence_watch: Decimal = Decimal("0.500000")
    source_confidence_block: Decimal = Decimal("0.250000")
    recency_watch_seconds: Decimal = Decimal("86400.000000")
    recency_block_seconds: Decimal = Decimal("259200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, GoldEventSignalMatrixConfig, "config")
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_GOLD_EVENT_SIGNAL_MATRIX_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for name in (
            "dollar_pressure_watch",
            "dollar_pressure_block",
            "real_rate_pressure_watch",
            "real_rate_pressure_block",
            "central_bank_signal_watch",
            "central_bank_signal_block",
            "risk_appetite_shift_watch",
            "risk_appetite_shift_block",
            "source_confidence_watch",
            "source_confidence_block",
        ):
            object.__setattr__(self, name, _normalize_probability(name, getattr(self, name)))
        for name in ("recency_watch_seconds", "recency_block_seconds"):
            object.__setattr__(
                self,
                name,
                _normalize_nonnegative_decimal(name, getattr(self, name)),
            )
        _require_at_most(
            "dollar_pressure_watch",
            self.dollar_pressure_watch,
            self.dollar_pressure_block,
        )
        _require_at_most(
            "real_rate_pressure_watch",
            self.real_rate_pressure_watch,
            self.real_rate_pressure_block,
        )
        _require_at_most(
            "central_bank_signal_watch",
            self.central_bank_signal_watch,
            self.central_bank_signal_block,
        )
        _require_at_most(
            "risk_appetite_shift_watch",
            self.risk_appetite_shift_watch,
            self.risk_appetite_shift_block,
        )
        _require_at_least(
            "source_confidence_watch",
            self.source_confidence_watch,
            self.source_confidence_block,
        )
        _require_at_most(
            "recency_watch_seconds",
            self.recency_watch_seconds,
            self.recency_block_seconds,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class GoldEventSignalMatrixCandidate(_FinalPublicDataclass):
    public_event_label: str
    metal_family: str
    event_family: str
    dollar_pressure_score: Decimal
    real_rate_pressure_score: Decimal
    central_bank_signal_score: Decimal
    risk_appetite_shift_score: Decimal
    source_confidence_score: Decimal
    recency_seconds: Decimal
    evidence_family_count: Decimal
    reason_codes: tuple[str, ...]
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, GoldEventSignalMatrixCandidate, "candidate")
        for name in ("public_event_label", "metal_family", "event_family"):
            _require_public_string(name, getattr(self, name))
        for name in (
            "dollar_pressure_score",
            "real_rate_pressure_score",
            "central_bank_signal_score",
            "risk_appetite_shift_score",
            "source_confidence_score",
        ):
            object.__setattr__(self, name, _normalize_probability(name, getattr(self, name)))
        for name in ("recency_seconds", "evidence_family_count"):
            object.__setattr__(
                self,
                name,
                _normalize_nonnegative_decimal(name, getattr(self, name)),
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class GoldEventSignalMatrixRow(_FinalPublicDataclass):
    public_event_label: str
    metal_family: str
    event_family: str
    public_status: str
    hard_flag: bool
    dollar_pressure_score: Decimal
    real_rate_pressure_score: Decimal
    central_bank_signal_score: Decimal
    risk_appetite_shift_score: Decimal
    source_confidence_score: Decimal
    recency_seconds: Decimal
    evidence_family_count: Decimal
    research_priority_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, GoldEventSignalMatrixRow, "row")
        for name in ("public_event_label", "metal_family", "event_family"):
            _require_public_string(name, getattr(self, name))
        _require_public_status("public_status", self.public_status)
        if type(self.hard_flag) is not bool:
            raise ValueError("hard_flag must be a bool")
        for name in (
            "dollar_pressure_score",
            "real_rate_pressure_score",
            "central_bank_signal_score",
            "risk_appetite_shift_score",
            "source_confidence_score",
            "research_priority_score",
        ):
            object.__setattr__(self, name, _normalize_probability(name, getattr(self, name)))
        for name in ("recency_seconds", "evidence_family_count"):
            object.__setattr__(
                self,
                name,
                _normalize_nonnegative_decimal(name, getattr(self, name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        if self.public_status != _row_status(self.reason_codes):
            raise ValueError("public_status must match reason_codes")
        if self.hard_flag != _hard_flag_from_reason_codes(self.reason_codes):
            raise ValueError("hard_flag must match reason_codes")
        _require_hard_flags("row", self)
        expected_digest = _row_digest(self)
        if self.digest:
            _require_digest("digest", self.digest)
            if self.digest != expected_digest:
                raise ValueError("row digest mismatch")
        else:
            object.__setattr__(self, "digest", expected_digest)


@dataclass(frozen=True)
class GoldEventSignalMatrixReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, GoldEventSignalMatrixReasonCodeCount, "reason_count")
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_decimal("count", self.count))
        _require_hard_flags("reason_count", self)


@dataclass(frozen=True)
class GoldEventSignalMatrixReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    hard_flag_count: Decimal
    average_research_priority_score: Decimal
    max_research_priority_score: Decimal
    average_recency_seconds: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[GoldEventSignalMatrixReasonCodeCount, ...]
    rows: tuple[GoldEventSignalMatrixRow, ...]
    digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, GoldEventSignalMatrixReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_GOLD_EVENT_SIGNAL_MATRIX_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_public_status("status", self.status)
        for name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "hard_flag_count",
            "average_research_priority_score",
            "max_research_priority_score",
            "average_recency_seconds",
        ):
            object.__setattr__(
                self,
                name,
                _normalize_nonnegative_decimal(name, getattr(self, name)),
            )
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
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.digest:
            _require_digest("digest", self.digest)
            if self.digest != expected_digest:
                raise ValueError("report digest mismatch")
        else:
            object.__setattr__(self, "digest", expected_digest)


_PUBLIC_DATACLASS_TYPES = (
    GoldEventSignalMatrixCandidate,
    GoldEventSignalMatrixConfig,
    GoldEventSignalMatrixReasonCodeCount,
    GoldEventSignalMatrixReport,
    GoldEventSignalMatrixRow,
)


def build_research_gold_event_signal_matrix_report(
    candidates: Iterable[GoldEventSignalMatrixCandidate],
    *,
    config: GoldEventSignalMatrixConfig,
    generated_at: datetime,
) -> GoldEventSignalMatrixReport:
    if type(config) is not GoldEventSignalMatrixConfig:
        raise ValueError("config must be a GoldEventSignalMatrixConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_candidates(candidates)
    rows = tuple(
        sorted(
            (_matrix_row(row, config=config) for row in inputs),
            key=_row_sort_key,
        ),
    )
    return GoldEventSignalMatrixReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_rollup_status(tuple(row.public_status for row in rows)),
        candidate_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        hard_flag_count=_count(sum(1 for row in rows if row.hard_flag)),
        average_research_priority_score=_mean(
            tuple(row.research_priority_score for row in rows),
        ),
        max_research_priority_score=_max_decimal(
            tuple(row.research_priority_score for row in rows),
        ),
        average_recency_seconds=_mean(tuple(row.recency_seconds for row in rows)),
        reason_codes=_rollup_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_gold_event_signal_matrix_payload(
    report: GoldEventSignalMatrixReport,
) -> dict[str, Any]:
    if type(report) is not GoldEventSignalMatrixReport:
        raise ValueError("report must be a GoldEventSignalMatrixReport")
    _require_payload_safe_value("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_gold_event_signal_matrix_digest(
    report: GoldEventSignalMatrixReport,
) -> dict[str, Any]:
    payload = research_gold_event_signal_matrix_payload(report)
    digest = {
        "generated_at": payload["generated_at"],
        "config_version": payload["config_version"],
        "status": payload["status"],
        "candidate_count": payload["candidate_count"],
        "pass_count": payload["pass_count"],
        "watch_count": payload["watch_count"],
        "block_count": payload["block_count"],
        "hard_flag_count": payload["hard_flag_count"],
        "reason_codes": payload["reason_codes"],
        "top_rows": payload["rows"][:3],
        "digest": payload["digest"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    _reject_unsafe_public_payload("digest", digest)
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


def _matrix_row(
    row: GoldEventSignalMatrixCandidate,
    *,
    config: GoldEventSignalMatrixConfig,
) -> GoldEventSignalMatrixRow:
    reason_codes = _row_reason_codes(row, config=config)
    return GoldEventSignalMatrixRow(
        public_event_label=row.public_event_label,
        metal_family=row.metal_family,
        event_family=row.event_family,
        public_status=_row_status(reason_codes),
        hard_flag=_hard_flag_from_reason_codes(reason_codes),
        dollar_pressure_score=row.dollar_pressure_score,
        real_rate_pressure_score=row.real_rate_pressure_score,
        central_bank_signal_score=row.central_bank_signal_score,
        risk_appetite_shift_score=row.risk_appetite_shift_score,
        source_confidence_score=row.source_confidence_score,
        recency_seconds=row.recency_seconds,
        evidence_family_count=row.evidence_family_count,
        research_priority_score=_research_priority_score(row),
        observed_at=row.observed_at,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: GoldEventSignalMatrixCandidate,
    *,
    config: GoldEventSignalMatrixConfig,
) -> tuple[str, ...]:
    reason_codes = list(row.reason_codes)
    _append_threshold_reason(
        reason_codes,
        prefix="dollar_pressure",
        value=row.dollar_pressure_score,
        watch=config.dollar_pressure_watch,
        block=config.dollar_pressure_block,
    )
    _append_threshold_reason(
        reason_codes,
        prefix="real_rate_pressure",
        value=row.real_rate_pressure_score,
        watch=config.real_rate_pressure_watch,
        block=config.real_rate_pressure_block,
    )
    _append_threshold_reason(
        reason_codes,
        prefix="central_bank_signal",
        value=row.central_bank_signal_score,
        watch=config.central_bank_signal_watch,
        block=config.central_bank_signal_block,
    )
    _append_threshold_reason(
        reason_codes,
        prefix="risk_appetite_shift",
        value=row.risk_appetite_shift_score,
        watch=config.risk_appetite_shift_watch,
        block=config.risk_appetite_shift_block,
    )
    if row.source_confidence_score <= config.source_confidence_block:
        reason_codes.append("source_confidence_block")
    elif row.source_confidence_score <= config.source_confidence_watch:
        reason_codes.append("source_confidence_watch")
    if row.recency_seconds > config.recency_block_seconds:
        reason_codes.append("recency_block")
    elif row.recency_seconds > config.recency_watch_seconds:
        reason_codes.append("recency_watch")
    if not _has_matrix_signal(reason_codes):
        reason_codes.append("gold_event_signal_clear")
    return _normalize_reason_codes(tuple(sorted(reason_codes)))


def _append_threshold_reason(
    reason_codes: list[str],
    *,
    prefix: str,
    value: Decimal,
    watch: Decimal,
    block: Decimal,
) -> None:
    if value >= block:
        reason_codes.append(f"{prefix}_block")
    elif value >= watch:
        reason_codes.append(f"{prefix}_watch")


def _research_priority_score(row: GoldEventSignalMatrixCandidate) -> Decimal:
    source_gap = _quantize(ONE - row.source_confidence_score)
    recency_pressure = min(ONE, _quantize(row.recency_seconds / Decimal("259200.000000")))
    return _clamp_probability(
        _quantize(
            row.dollar_pressure_score * Decimal("0.220000")
            + row.real_rate_pressure_score * Decimal("0.240000")
            + row.central_bank_signal_score * Decimal("0.220000")
            + row.risk_appetite_shift_score * Decimal("0.170000")
            + source_gap * Decimal("0.100000")
            + recency_pressure * Decimal("0.050000"),
        ),
    )


def _has_matrix_signal(reason_codes: Iterable[str]) -> bool:
    return any(code.endswith("_watch") or code.endswith("_block") for code in reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(code.endswith("_block") for code in reason_codes):
        return "block"
    if any(code.endswith("_watch") for code in reason_codes):
        return "watch"
    return "pass"


def _hard_flag_from_reason_codes(reason_codes: tuple[str, ...]) -> bool:
    return any(code.endswith("_block") for code in reason_codes)


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "block"
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _rollup_reason_codes(rows: tuple[GoldEventSignalMatrixRow, ...]) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    status = _rollup_status(tuple(row.public_status for row in rows))
    reason_codes = [f"gold_event_signal_matrix_{status}"]
    row_reason_codes = frozenset(code for row in rows for code in row.reason_codes)
    for code in (
        "central_bank_signal_block",
        "central_bank_signal_watch",
        "dollar_pressure_block",
        "dollar_pressure_watch",
        "real_rate_pressure_block",
        "real_rate_pressure_watch",
        "recency_block",
        "recency_watch",
        "risk_appetite_shift_block",
        "risk_appetite_shift_watch",
        "source_confidence_block",
        "source_confidence_watch",
    ):
        if code in row_reason_codes:
            reason_codes.append(code)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[GoldEventSignalMatrixRow, ...],
) -> tuple[GoldEventSignalMatrixReasonCodeCount, ...]:
    if not rows:
        return (
            GoldEventSignalMatrixReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=COUNT_QUANTUM,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        GoldEventSignalMatrixReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    )


def _normalize_candidates(
    candidates: Iterable[GoldEventSignalMatrixCandidate],
) -> tuple[GoldEventSignalMatrixCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        rows = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen_labels: set[str] = set()
    for row in rows:
        if type(row) is not GoldEventSignalMatrixCandidate:
            raise ValueError("candidates must contain GoldEventSignalMatrixCandidate values")
        _require_hard_flags("candidate", row)
        if row.public_event_label in seen_labels:
            raise ValueError("candidates must not contain duplicate public_event_label values")
        seen_labels.add(row.public_event_label)
    return rows


def _normalize_rows(
    rows: Iterable[GoldEventSignalMatrixRow],
) -> tuple[GoldEventSignalMatrixRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_labels: set[str] = set()
    for row in values:
        if type(row) is not GoldEventSignalMatrixRow:
            raise ValueError("rows must contain GoldEventSignalMatrixRow values")
        _require_hard_flags("row", row)
        if row.public_event_label in seen_labels:
            raise ValueError("rows must not contain duplicate public_event_label values")
        seen_labels.add(row.public_event_label)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must use canonical sequence")
    return values


def _normalize_reason_code_counts(
    rows: Iterable[GoldEventSignalMatrixReasonCodeCount],
) -> tuple[GoldEventSignalMatrixReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in values:
        if type(row) is not GoldEventSignalMatrixReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain GoldEventSignalMatrixReasonCodeCount values",
            )
        if row.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate reason_code values")
        seen_codes.add(row.reason_code)
    if values != tuple(sorted(values, key=lambda item: (-item.count, item.reason_code))):
        raise ValueError("reason_code_counts must be sorted by count then reason_code")
    return values


def _row_sort_key(row: GoldEventSignalMatrixRow) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        -STATUS_WEIGHT[row.public_status],
        -row.research_priority_score,
        row.public_event_label,
        row.metal_family,
        row.event_family,
    )


def _status_count(rows: tuple[GoldEventSignalMatrixRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.public_status == status))


def _validate_report(report: GoldEventSignalMatrixReport) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.hard_flag_count != _count(sum(1 for row in rows if row.hard_flag)):
        raise ValueError("hard_flag_count must match rows")
    if report.average_research_priority_score != _mean(
        tuple(row.research_priority_score for row in rows),
    ):
        raise ValueError("average_research_priority_score must match rows")
    if report.max_research_priority_score != _max_decimal(
        tuple(row.research_priority_score for row in rows),
    ):
        raise ValueError("max_research_priority_score must match rows")
    if report.average_recency_seconds != _mean(tuple(row.recency_seconds for row in rows)):
        raise ValueError("average_recency_seconds must match rows")
    if report.status != _rollup_status(tuple(row.public_status for row in rows)):
        raise ValueError("status must match rows")
    if report.reason_codes != _rollup_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_payload_safe_value(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{label} contains unsupported dataclass")
        for field in fields(value):
            _require_payload_safe_value(f"{label}.{field.name}", getattr(value, field.name))
        _rebuild_public_dataclass(label, value)
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
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        _require_public_string(label, value)
        return
    if type(value) in (int, float) or isinstance(value, (list, dict, set)):
        raise ValueError(f"{label} must come from public dataclass fields")
    raise ValueError(f"{label} contains unsupported value")


def _rebuild_public_dataclass(label: str, value: object) -> None:
    kwargs = {field.name: getattr(value, field.name) for field in fields(value)}
    try:
        type(value)(**kwargs)
    except Exception as exc:
        raise ValueError(f"{label} failed payload revalidation: {exc}") from exc


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        _require_six_decimal_decimal("JSON Decimal value", value)
        return format(value, "f")
    if type(value) is datetime:
        _require_utc_datetime("JSON datetime value", value)
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        _require_payload_safe_value("JSON value", value)
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if value is None:
        return None
    if type(value) is bool:
        return value
    if type(value) is str:
        return value
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) in (int, float) or isinstance(value, (list, dict, set)):
        raise ValueError("JSON value must come from public dataclass fields")
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{path or label} contains unsupported dataclass")
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(label, getattr(value, field.name), item_path)
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if type(value) is Decimal:
        _require_six_decimal_decimal(path or label, value)
        return
    if type(value) is datetime:
        _require_utc_datetime(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError(f"{path or label} must use Decimal values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe field in {label}: {key}")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError("value is not JSON serializable")


def _unsafe_fragments() -> tuple[str, ...]:
    shared_fragments = tuple(
        fragment
        for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS
        if fragment != "sign"
    )
    return (
        *shared_fragments,
        "candidate_id",
        "candidate id",
        "mark" "et",
        "slug",
        "ques" "tion",
        "source_ref",
        "source ref",
        "source_u" "rl",
        "source u" "rl",
        "://" ,
        "ht" "tp",
        "raw",
        "tex" "t",
        "dsn",
        "tab" "le",
        "tok" "en",
        "api_",
        "wal" "let",
        "or" "der",
        "tr" "ade",
        "b" "uy",
        "s" "ell",
        "rec" "ommend",
        "pos" "ition",
    )


def _has_unsafe_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _unsafe_fragments())


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_utc_datetime(name: str, value: datetime) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() is None:
        raise ValueError(f"{name} must be UTC-aware")


def _normalize_decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _normalize_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_probability(name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(name, value)
    if normalized > ONE:
        raise ValueError(f"{name} must be at most one")
    return normalized


def _require_six_decimal_decimal(name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{name} must use six decimal places")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not values:
        raise ValueError("reason_codes must not be empty")
    for reason_code in values:
        _require_public_string("reason_codes", reason_code)
    normalized = tuple(sorted(values))
    if values != normalized:
        raise ValueError("reason_codes must use canonical sequence")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return normalized


def _normalize_report_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        values = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not values:
        raise ValueError("reason_codes must not be empty")
    for reason_code in values:
        _require_public_string("reason_codes", reason_code)
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must not contain duplicates")
    if values == (NO_INPUTS_REASON,):
        return values
    if not values[0].startswith("gold_event_signal_matrix_"):
        raise ValueError("reason_codes must begin with matrix rollup code")
    if values[1:] != tuple(sorted(values[1:])):
        raise ValueError("reason_codes must use canonical sequence")
    return values


def _require_public_string(name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical string")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{name} has unsafe value")


def _require_public_status(name: str, value: str) -> None:
    if value not in PUBLIC_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_at_most(name: str, lower: Decimal, upper: Decimal) -> None:
    if lower > upper:
        raise ValueError(f"{name} must be at most paired block threshold")


def _require_at_least(name: str, upper: Decimal, lower: Decimal) -> None:
    if upper < lower:
        raise ValueError(f"{name} must be at least paired block threshold")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / _count(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(max(values))


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _clamp_probability(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


def _row_digest(row: GoldEventSignalMatrixRow) -> str:
    return _digest_from_public_value(row)


def _report_digest(report: GoldEventSignalMatrixReport) -> str:
    return _digest_from_public_value(report)


def _require_digest(name: str, value: str) -> None:
    _require_public_string(name, value)
    if not value.startswith(DIGEST_PREFIX):
        raise ValueError(f"{name} must use the gold signal matrix digest prefix")
    suffix = value.removeprefix(DIGEST_PREFIX)
    if len(suffix) != 64 or any(char not in "0123456789abcdef" for char in suffix):
        raise ValueError(f"{name} must use a sha256 hex suffix")


def _digest_from_public_value(value: object) -> str:
    canonical_payload = _digest_ready(value)
    encoded = json.dumps(canonical_payload, sort_keys=True, separators=(",", ":"))
    return f"{DIGEST_PREFIX}{sha256(encoded.encode('utf-8')).hexdigest()}"


def _digest_ready(value: object) -> object:
    if type(value) is Decimal:
        _require_six_decimal_decimal("digest Decimal value", value)
        return format(value, "f")
    if type(value) is datetime:
        _require_utc_datetime("digest datetime value", value)
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _digest_ready(getattr(value, field.name))
            for field in fields(value)
            if field.name != "digest"
        }
    if type(value) is tuple:
        return [_digest_ready(item) for item in value]
    if value is None or type(value) in (bool, str):
        return value
    raise ValueError("value is not digest serializable")
