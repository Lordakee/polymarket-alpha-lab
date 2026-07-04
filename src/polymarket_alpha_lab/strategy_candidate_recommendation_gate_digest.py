"""Pure candidate recommendation gate digest."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_STRATEGY_CANDIDATE_RECOMMENDATION_GATE_DIGEST_CONFIG_VERSION = (
    "strategy-candidate-recommendation-gate-digest-v0"
)

_COUNT_QUANTUM = Decimal("1")
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_STATUSES = ("block", "watch", "pass")
_STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
_REPORT_REASON_PRIORITY = (
    "candidate_recommendation_gate_blocked",
    "candidate_recommendation_gate_watch",
    "candidate_recommendation_gate_pass",
    "candidate_recommendation_gate_empty",
)
_ROW_REASON_PRIORITY = (
    "gate_block_present",
    "gate_score_below_watch",
    "gate_watch_present",
    "gate_score_below_pass",
    "candidate_recommendation_gate_pass",
)
_HEX_CHARS = frozenset("0123456789abcdef")
_UNSAFE_TEXT_FRAGMENTS = (
    "sec" "ret",
    "tok" "en",
    "pass" "word",
    "cred" "ential",
    "private" "_" "key",
    "api" "_" "key",
    "bear" "er",
    "wal" "let",
    "au" "th",
    "bro" "ker",
    "or" "der",
    "can" "cel",
    "re" "place",
    "sign" "ing",
    "li" "ve",
    "trad" "ing",
    "://" ,
)
_FLAG_NAMES = ("paper_only", "report_only", "readonly")


@dataclass(frozen=True)
class StrategyCandidateRecommendationGateConfig:
    config_version: str = (
        DEFAULT_STRATEGY_CANDIDATE_RECOMMENDATION_GATE_DIGEST_CONFIG_VERSION
    )
    min_pass_weighted_gate_score: Decimal = Decimal("0.800000")
    min_watch_weighted_gate_score: Decimal = Decimal("0.500000")
    max_block_gate_count: Decimal = Decimal("0")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_pass_weighted_gate_score",
            _normalize_unit_decimal(
                "min_pass_weighted_gate_score",
                self.min_pass_weighted_gate_score,
            ),
        )
        object.__setattr__(
            self,
            "min_watch_weighted_gate_score",
            _normalize_unit_decimal(
                "min_watch_weighted_gate_score",
                self.min_watch_weighted_gate_score,
            ),
        )
        if self.min_watch_weighted_gate_score > self.min_pass_weighted_gate_score:
            raise ValueError("watch gate threshold must not exceed pass threshold")
        object.__setattr__(
            self,
            "max_block_gate_count",
            _normalize_nonnegative_count("max_block_gate_count", self.max_block_gate_count),
        )
        require_paper_only_flags("candidate recommendation gate config", self)


@dataclass(frozen=True)
class StrategyCandidateRecommendationGateSignal:
    candidate_reference: str
    gate_name: str
    gate_status: str
    gate_score: Decimal
    gate_weight: Decimal
    observed_at: datetime
    source_reference: str
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("candidate_reference", self.candidate_reference)
        object.__setattr__(
            self,
            "candidate_reference",
            _redacted_reference("candidate_ref_", self.candidate_reference),
        )
        _require_public_text("gate_name", self.gate_name)
        _require_status("gate_status", self.gate_status)
        object.__setattr__(
            self,
            "gate_score",
            _normalize_unit_decimal("gate_score", self.gate_score),
        )
        object.__setattr__(
            self,
            "gate_weight",
            _normalize_positive_decimal("gate_weight", self.gate_weight),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_text("source_reference", self.source_reference)
        object.__setattr__(
            self,
            "source_reference",
            _redacted_reference("source_ref_", self.source_reference),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_public_reason_codes("reason_codes", self.reason_codes),
        )
        require_paper_only_flags("candidate recommendation gate signal", self)


@dataclass(frozen=True)
class StrategyCandidateRecommendationGateRow:
    redacted_candidate_reference: str
    gate_count: Decimal
    pass_gate_count: Decimal
    watch_gate_count: Decimal
    block_gate_count: Decimal
    total_gate_weight: Decimal
    weighted_gate_score: Decimal
    latest_observed_at: datetime
    gate_names: tuple[str, ...]
    source_references: tuple[str, ...]
    gate_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_redacted_reference(
            "redacted_candidate_reference",
            self.redacted_candidate_reference,
            "candidate_ref_",
        )
        for field_name in (
            "gate_count",
            "pass_gate_count",
            "watch_gate_count",
            "block_gate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_gate_weight",
            _normalize_positive_decimal("total_gate_weight", self.total_gate_weight),
        )
        object.__setattr__(
            self,
            "weighted_gate_score",
            _normalize_unit_decimal("weighted_gate_score", self.weighted_gate_score),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(self, "gate_names", _normalize_public_tuple("gate_names", self.gate_names))
        object.__setattr__(
            self,
            "source_references",
            _normalize_redacted_tuple("source_references", self.source_references, "source_ref_"),
        )
        _require_status("gate_status", self.gate_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        require_paper_only_flags("candidate recommendation gate row", self)


@dataclass(frozen=True)
class StrategyCandidateRecommendationGateReasonCount:
    reason_code: str
    candidate_count: Decimal
    candidate_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "candidate_count",
            _normalize_nonnegative_count("candidate_count", self.candidate_count),
        )
        object.__setattr__(
            self,
            "candidate_ratio",
            _normalize_unit_decimal("candidate_ratio", self.candidate_ratio),
        )
        require_paper_only_flags("candidate recommendation gate reason count", self)


@dataclass(frozen=True)
class StrategyCandidateRecommendationGateReport:
    generated_at: datetime
    config_version: str
    signal_count: Decimal
    candidate_count: Decimal
    pass_candidate_count: Decimal
    watch_candidate_count: Decimal
    block_candidate_count: Decimal
    min_weighted_gate_score: Decimal | None
    max_block_gate_count: Decimal
    gate_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyCandidateRecommendationGateRow, ...]
    reason_counts: tuple[StrategyCandidateRecommendationGateReasonCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "signal_count",
            "candidate_count",
            "pass_candidate_count",
            "watch_candidate_count",
            "block_candidate_count",
            "max_block_gate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.min_weighted_gate_score is not None:
            object.__setattr__(
                self,
                "min_weighted_gate_score",
                _normalize_unit_decimal(
                    "min_weighted_gate_score",
                    self.min_weighted_gate_score,
                ),
            )
        _require_status("gate_status", self.gate_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_counts", _normalize_reason_counts(self.reason_counts))
        _validate_report(self)
        require_paper_only_flags("candidate recommendation gate report", self)


def build_strategy_candidate_recommendation_gate_digest(
    signals: Iterable[StrategyCandidateRecommendationGateSignal],
    *,
    config: StrategyCandidateRecommendationGateConfig,
    generated_at: datetime,
) -> StrategyCandidateRecommendationGateReport:
    if type(config) is not StrategyCandidateRecommendationGateConfig:
        raise ValueError("config must be a StrategyCandidateRecommendationGateConfig")
    require_paper_only_flags("candidate recommendation gate config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    rows = tuple(
        sorted(
            (
                _row_from_signals(
                    candidate_reference,
                    candidate_signals,
                    config=config,
                )
                for candidate_reference, candidate_signals in _group_signals(normalized_signals)
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    candidate_count = _count(len(rows))
    return StrategyCandidateRecommendationGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        signal_count=_count(len(normalized_signals)),
        candidate_count=candidate_count,
        pass_candidate_count=_row_status_count(rows, "pass"),
        watch_candidate_count=_row_status_count(rows, "watch"),
        block_candidate_count=_row_status_count(rows, "block"),
        min_weighted_gate_score=(
            None if not rows else min(row.weighted_gate_score for row in rows)
        ),
        max_block_gate_count=max((row.block_gate_count for row in rows), default=_ZERO),
        gate_status=_report_status(rows),
        reason_codes=reason_codes,
        rows=rows,
        reason_counts=_reason_counts(rows, candidate_count),
    )


def strategy_candidate_recommendation_gate_digest_payload(
    report: StrategyCandidateRecommendationGateReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyCandidateRecommendationGateReport:
        require_paper_only_flags("candidate recommendation gate report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a StrategyCandidateRecommendationGateReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    _reject_unsafe_payload(payload)
    require_paper_only_flags("candidate recommendation gate payload", _PayloadFlags(payload))
    return payload


@dataclass(frozen=True)
class _PayloadFlags:
    payload: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.payload.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.payload.get("report_only")

    @property
    def readonly(self) -> object:
        return self.payload.get("readonly")


def _normalize_signals(
    signals: Iterable[StrategyCandidateRecommendationGateSignal],
) -> tuple[StrategyCandidateRecommendationGateSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        items = tuple(signals)
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for item in items:
        if type(item) is not StrategyCandidateRecommendationGateSignal:
            raise ValueError("signals must contain StrategyCandidateRecommendationGateSignal")
        require_paper_only_flags("candidate recommendation gate signal", item)
        key = (item.candidate_reference, item.gate_name)
        if key in seen:
            raise ValueError("signals must contain unique candidate and gate values")
        seen.add(key)
    return items


def _group_signals(
    signals: tuple[StrategyCandidateRecommendationGateSignal, ...],
) -> tuple[tuple[str, tuple[StrategyCandidateRecommendationGateSignal, ...]], ...]:
    candidate_references = tuple(sorted({signal.candidate_reference for signal in signals}))
    return tuple(
        (
            candidate_reference,
            tuple(
                sorted(
                    (
                        signal
                        for signal in signals
                        if signal.candidate_reference == candidate_reference
                    ),
                    key=lambda signal: signal.gate_name,
                ),
            ),
        )
        for candidate_reference in candidate_references
    )


def _row_from_signals(
    candidate_reference: str,
    signals: tuple[StrategyCandidateRecommendationGateSignal, ...],
    *,
    config: StrategyCandidateRecommendationGateConfig,
) -> StrategyCandidateRecommendationGateRow:
    total_weight = _sum_decimal(signal.gate_weight for signal in signals)
    weighted_score = _ratio(
        _sum_decimal(signal.gate_score * signal.gate_weight for signal in signals),
        total_weight,
    )
    block_count = _status_count(signals, "block")
    watch_count = _status_count(signals, "watch")
    pass_count = _status_count(signals, "pass")
    reasons = _row_reason_codes_from_values(
        block_count=block_count,
        watch_count=watch_count,
        weighted_score=weighted_score,
        config=config,
        input_reason_codes=tuple(
            reason
            for signal in signals
            for reason in signal.reason_codes
        ),
    )
    return StrategyCandidateRecommendationGateRow(
        redacted_candidate_reference=candidate_reference,
        gate_count=_count(len(signals)),
        pass_gate_count=pass_count,
        watch_gate_count=watch_count,
        block_gate_count=block_count,
        total_gate_weight=total_weight,
        weighted_gate_score=weighted_score,
        latest_observed_at=max(signal.observed_at for signal in signals),
        gate_names=tuple(signal.gate_name for signal in signals),
        source_references=tuple(sorted({signal.source_reference for signal in signals})),
        gate_status=_row_status(
            block_gate_count=block_count,
            watch_gate_count=watch_count,
            weighted_gate_score=weighted_score,
            config=config,
        ),
        reason_codes=reasons,
    )


def _row_status(
    *,
    block_gate_count: Decimal,
    watch_gate_count: Decimal,
    weighted_gate_score: Decimal,
    config: StrategyCandidateRecommendationGateConfig,
) -> str:
    if block_gate_count > config.max_block_gate_count:
        return "block"
    if weighted_gate_score < config.min_watch_weighted_gate_score:
        return "block"
    if watch_gate_count > _ZERO:
        return "watch"
    if weighted_gate_score < config.min_pass_weighted_gate_score:
        return "watch"
    return "pass"


def _row_reason_codes_from_values(
    *,
    block_count: Decimal,
    watch_count: Decimal,
    weighted_score: Decimal,
    config: StrategyCandidateRecommendationGateConfig,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if block_count > config.max_block_gate_count:
        reasons.append("gate_block_present")
    if weighted_score < config.min_watch_weighted_gate_score:
        reasons.append("gate_score_below_watch")
    if watch_count > _ZERO:
        reasons.append("gate_watch_present")
    if (
        weighted_score >= config.min_watch_weighted_gate_score
        and weighted_score < config.min_pass_weighted_gate_score
    ):
        reasons.append("gate_score_below_pass")
    if not reasons:
        reasons.append("candidate_recommendation_gate_pass")
    reasons.extend(input_reason_codes)
    return _normalize_public_reason_codes("reason_codes", tuple(reasons))


def _report_status(rows: tuple[StrategyCandidateRecommendationGateRow, ...]) -> str:
    if any(row.gate_status == "block" for row in rows):
        return "block"
    if any(row.gate_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[StrategyCandidateRecommendationGateRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("candidate_recommendation_gate_empty",)
    status = _report_status(rows)
    if status == "block":
        return ("candidate_recommendation_gate_blocked",)
    if status == "watch":
        return ("candidate_recommendation_gate_watch",)
    return ("candidate_recommendation_gate_pass",)


def _reason_counts(
    rows: tuple[StrategyCandidateRecommendationGateRow, ...],
    candidate_count: Decimal,
) -> tuple[StrategyCandidateRecommendationGateReasonCount, ...]:
    if candidate_count == _ZERO:
        return ()
    counts = Counter(
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != "candidate_recommendation_gate_pass"
    )
    return tuple(
        StrategyCandidateRecommendationGateReasonCount(
            reason_code=reason,
            candidate_count=_count(count),
            candidate_ratio=_ratio(_count(count), candidate_count),
        )
        for reason, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], _reason_sort_key(item[0])),
        )
    )


def _row_status_count(rows: tuple[StrategyCandidateRecommendationGateRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.gate_status == status))


def _status_count(
    signals: tuple[StrategyCandidateRecommendationGateSignal, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for signal in signals if signal.gate_status == status))


def _normalize_rows(rows: object) -> tuple[StrategyCandidateRecommendationGateRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not StrategyCandidateRecommendationGateRow:
            raise ValueError("rows must contain StrategyCandidateRecommendationGateRow")
        require_paper_only_flags("candidate recommendation gate row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return normalized


def _normalize_reason_counts(
    values: object,
) -> tuple[StrategyCandidateRecommendationGateReasonCount, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_counts must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_counts must be an iterable") from exc
    for value in normalized:
        if type(value) is not StrategyCandidateRecommendationGateReasonCount:
            raise ValueError("reason_counts must contain StrategyCandidateRecommendationGateReasonCount")
        require_paper_only_flags("candidate recommendation gate reason count", value)
    if normalized != tuple(
        sorted(
            normalized,
            key=lambda item: (-item.candidate_count, _reason_sort_key(item.reason_code)),
        ),
    ):
        raise ValueError("reason_counts must use deterministic sequence")
    return normalized


def _normalize_public_tuple(name: str, values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable") from exc
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    for value in normalized:
        _require_public_text(name, value)
    if normalized != tuple(sorted(dict.fromkeys(normalized))):
        raise ValueError(f"{name} must use deterministic sequence")
    return normalized


def _normalize_redacted_tuple(name: str, values: object, prefix: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable") from exc
    if not normalized:
        raise ValueError(f"{name} must not be empty")
    for value in normalized:
        _require_redacted_reference(name, value, prefix)
    if normalized != tuple(sorted(dict.fromkeys(normalized))):
        raise ValueError(f"{name} must use deterministic sequence")
    return normalized


def _normalize_public_reason_codes(name: str, values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be an iterable")
    try:
        codes = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable") from exc
    for code in codes:
        _require_public_text(name, code)
        compact_code = "".join(part for part in code if part != "_")
        if not compact_code.isalnum() or code.lower() != code:
            raise ValueError(f"{name} must contain lowercase snake case values")
    return tuple(sorted(dict.fromkeys(codes), key=_reason_sort_key))


def _normalize_row_reason_codes(name: str, values: object) -> tuple[str, ...]:
    codes = _normalize_public_reason_codes(name, values)
    if not codes:
        raise ValueError(f"{name} must not be empty")
    if codes != tuple(sorted(codes, key=_reason_sort_key)):
        raise ValueError(f"{name} must use deterministic sequence")
    return codes


def _normalize_report_reason_codes(name: str, values: object) -> tuple[str, ...]:
    codes = _normalize_public_reason_codes(name, values)
    if codes not in (
        ("candidate_recommendation_gate_blocked",),
        ("candidate_recommendation_gate_watch",),
        ("candidate_recommendation_gate_pass",),
        ("candidate_recommendation_gate_empty",),
    ):
        raise ValueError(f"{name} must contain a known report summary")
    return codes


def _validate_row(row: StrategyCandidateRecommendationGateRow) -> None:
    if (
        row.pass_gate_count
        + row.watch_gate_count
        + row.block_gate_count
        != row.gate_count
    ):
        raise ValueError("gate status counts must match gate_count")
    if _row_status_from_row_reason_codes(row.reason_codes) != row.gate_status:
        raise ValueError("gate_status must match reason_codes")


def _validate_report(report: StrategyCandidateRecommendationGateReport) -> None:
    if report.candidate_count != _count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.signal_count != _sum_decimal(row.gate_count for row in report.rows):
        raise ValueError("signal_count must match rows")
    if report.pass_candidate_count != _row_status_count(report.rows, "pass"):
        raise ValueError("pass_candidate_count must match rows")
    if report.watch_candidate_count != _row_status_count(report.rows, "watch"):
        raise ValueError("watch_candidate_count must match rows")
    if report.block_candidate_count != _row_status_count(report.rows, "block"):
        raise ValueError("block_candidate_count must match rows")
    expected_min = None if not report.rows else min(row.weighted_gate_score for row in report.rows)
    if report.min_weighted_gate_score != expected_min:
        raise ValueError("min_weighted_gate_score must match rows")
    expected_max_block = max((row.block_gate_count for row in report.rows), default=_ZERO)
    if report.max_block_gate_count != expected_max_block:
        raise ValueError("max_block_gate_count must match rows")
    if report.gate_status != _report_status(report.rows):
        raise ValueError("gate_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_counts != _reason_counts(report.rows, report.candidate_count):
        raise ValueError("reason_counts must match rows")
    if any(row.latest_observed_at > report.generated_at for row in report.rows):
        raise ValueError("latest_observed_at must not be after generated_at")


def _row_status_from_row_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if "gate_block_present" in reason_codes or "gate_score_below_watch" in reason_codes:
        return "block"
    if "gate_watch_present" in reason_codes or "gate_score_below_pass" in reason_codes:
        return "watch"
    return "pass"


def _row_sort_key(row: StrategyCandidateRecommendationGateRow) -> tuple[int, Decimal, Decimal, str]:
    return (
        _STATUS_WEIGHT[row.gate_status],
        -row.weighted_gate_score,
        -row.block_gate_count,
        row.redacted_candidate_reference,
    )


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    if reason_code in _ROW_REASON_PRIORITY:
        return (_ROW_REASON_PRIORITY.index(reason_code), reason_code)
    if reason_code in _REPORT_REASON_PRIORITY:
        return (_REPORT_REASON_PRIORITY.index(reason_code), reason_code)
    return (len(_ROW_REASON_PRIORITY) + len(_REPORT_REASON_PRIORITY), reason_code)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = _ZERO
    for value in values:
        total += _normalize_decimal("sum value", value)
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    denominator = _normalize_decimal("denominator", denominator)
    if denominator <= _ZERO:
        raise ValueError("denominator must be positive")
    numerator = _normalize_decimal("numerator", numerator)
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be integral")
    return normalized.quantize(_COUNT_QUANTUM)


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return _quantize(normalized)


def _normalize_unit_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(normalized)


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(name: str, value: object) -> None:
    _require_public_text(name, value)
    if value not in _STATUSES:
        raise ValueError(f"{name} must be block, watch, or pass")


def _require_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _require_public_text(name: str, value: object) -> None:
    _require_text(name, value)
    normalized = value.lower()
    if any(fragment in normalized for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public text")


def _redacted_reference(prefix: str, value: str) -> str:
    _require_text("reference", value)
    return f"{prefix}{sha256(value.encode('utf-8')).hexdigest()[:16]}"


def _require_redacted_reference(name: str, value: object, prefix: str) -> None:
    _require_text(name, value)
    if not value.startswith(prefix):
        raise ValueError(f"{name} must be redacted")
    suffix = value[len(prefix) :]
    if len(suffix) != 16 or any(char not in _HEX_CHARS for char in suffix):
        raise ValueError(f"{name} must be redacted")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) is str:
        _require_public_text("JSON value", value)
        return value
    if type(value) in (int, float):
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_public_text("JSON object key", key)
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_payload(value: Any) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if key in _FLAG_NAMES and item is not True:
                raise ValueError(f"{key} must be True in payload")
            _require_public_text("payload key", key)
            _reject_unsafe_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item)
        return
    if type(value) in (int, float):
        raise ValueError("payload numeric values must use Decimal strings")
    if isinstance(value, datetime):
        if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("payload datetime values must be timezone-aware")
    if type(value) is str:
        _require_public_text("payload value", value)


__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_RECOMMENDATION_GATE_DIGEST_CONFIG_VERSION",
    "StrategyCandidateRecommendationGateConfig",
    "StrategyCandidateRecommendationGateReasonCount",
    "StrategyCandidateRecommendationGateReport",
    "StrategyCandidateRecommendationGateRow",
    "StrategyCandidateRecommendationGateSignal",
    "build_strategy_candidate_recommendation_gate_digest",
    "strategy_candidate_recommendation_gate_digest_payload",
)
