"""Pure probability memory cost floor report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
from typing import Any, Mapping


DEFAULT_RESEARCH_MARKET_PROBABILITY_MEMORY_COST_FLOOR_REPORT_CONFIG_VERSION = (
    "research-probability-memory-cost-floor-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_EMPTY_INPUT = "empty_input"
REASON_PASS = "memory_cost_floor_pass"
REASON_WATCH = "memory_cost_floor_watch"
REASON_BLOCK = "memory_cost_floor_block"
REASON_PROBABILITY_GAP_WATCH = "probability_gap_watch"
REASON_PROBABILITY_GAP_BLOCK = "probability_gap_block"
REASON_MEMORY_SCORE_WATCH = "memory_score_watch"
REASON_MEMORY_SCORE_BLOCK = "memory_score_block"
REASON_COST_FLOOR_GAP_WATCH = "cost_floor_gap_watch"
REASON_COST_FLOOR_GAP_BLOCK = "cost_floor_gap_block"
REASON_STALE_EVIDENCE_WATCH = "stale_evidence_watch"
REASON_STALE_EVIDENCE_BLOCK = "stale_evidence_block"

_REASON_SEQUENCE = (
    REASON_EMPTY_INPUT,
    REASON_BLOCK,
    REASON_PROBABILITY_GAP_BLOCK,
    REASON_MEMORY_SCORE_BLOCK,
    REASON_COST_FLOOR_GAP_BLOCK,
    REASON_STALE_EVIDENCE_BLOCK,
    REASON_WATCH,
    REASON_PROBABILITY_GAP_WATCH,
    REASON_MEMORY_SCORE_WATCH,
    REASON_COST_FLOOR_GAP_WATCH,
    REASON_STALE_EVIDENCE_WATCH,
    REASON_PASS,
)
_ROW_REASON_SEQUENCE = tuple(reason for reason in _REASON_SEQUENCE if reason != REASON_EMPTY_INPUT)
_STATUS_VALUES = frozenset((STATUS_PASS, STATUS_WATCH, STATUS_BLOCK))
_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_DIGEST_FIELD = "derived_validation_digest"
_Q = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_MICROS_PER_HOUR = Decimal("3600000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)


def _term(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "source",
    "url",
    "text",
    "raw_",
    "raw ",
    "dsn",
    "table",
    _term("to", "ken"),
    _term("wal", "let"),
    _term("au", "th"),
    _term("or", "der"),
    _term("li", "ve"),
    _term("tra", "ding"),
    _term("siz", "ing"),
    _term("recom", "mendation"),
    _term("d", "b"),
    _term("data", "base"),
    _term("net", "work"),
    "http://",
    "https://",
    "://",
)


@dataclass(frozen=True)
class ResearchMarketProbabilityMemoryCostFloorConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_PROBABILITY_MEMORY_COST_FLOOR_REPORT_CONFIG_VERSION
    )
    pass_min_memory_score: Decimal = Decimal("0.800000")
    watch_min_memory_score: Decimal = Decimal("0.600000")
    max_pass_probability_gap: Decimal = Decimal("0.050000")
    max_watch_probability_gap: Decimal = Decimal("0.120000")
    max_pass_cost_floor_gap: Decimal = Decimal("0.000000")
    max_watch_cost_floor_gap: Decimal = Decimal("0.050000")
    watch_stale_evidence_hours: Decimal = Decimal("24.000000")
    block_stale_evidence_hours: Decimal = Decimal("72.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketProbabilityMemoryCostFloorConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_text("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_PROBABILITY_MEMORY_COST_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match the supported version")
        for field_name in (
            "pass_min_memory_score",
            "watch_min_memory_score",
            "max_pass_probability_gap",
            "max_watch_probability_gap",
            "max_pass_cost_floor_gap",
            "max_watch_cost_floor_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_stale_evidence_hours",
            "block_stale_evidence_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_min_memory_score < self.watch_min_memory_score:
            raise ValueError("pass_min_memory_score must be at least watch_min_memory_score")
        if self.max_pass_probability_gap > self.max_watch_probability_gap:
            raise ValueError(
                "max_pass_probability_gap must not exceed max_watch_probability_gap",
            )
        if self.max_pass_cost_floor_gap > self.max_watch_cost_floor_gap:
            raise ValueError(
                "max_pass_cost_floor_gap must not exceed max_watch_cost_floor_gap",
            )
        if self.watch_stale_evidence_hours >= self.block_stale_evidence_hours:
            raise ValueError(
                "watch_stale_evidence_hours must be less than block_stale_evidence_hours",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityMemoryCostFloorInput:
    private_ref: str
    observed_probability: Decimal
    memory_probability: Decimal
    memory_score: Decimal
    cost_floor_probability: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketProbabilityMemoryCostFloorInput, "input")
        object.__setattr__(
            self,
            "private_ref",
            _require_private_text("private_ref", self.private_ref),
        )
        for field_name in (
            "observed_probability",
            "memory_probability",
            "memory_score",
            "cost_floor_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityMemoryCostFloorReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityMemoryCostFloorReasonCodeCount,
            "reason_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_public_text("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        _require_hard_flags("reason_count", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityMemoryCostFloorRow:
    case_digest: str
    status: str
    observed_probability: Decimal
    memory_probability: Decimal
    probability_gap: Decimal
    memory_score: Decimal
    cost_floor_probability: Decimal
    cost_floor_gap: Decimal
    observed_at: datetime
    observed_age_hours: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketProbabilityMemoryCostFloorRow, "row")
        object.__setattr__(
            self,
            "case_digest",
            _require_private_digest("case_digest", self.case_digest),
        )
        _require_status("status", self.status)
        for field_name in (
            "observed_probability",
            "memory_probability",
            "probability_gap",
            "memory_score",
            "cost_floor_probability",
            "cost_floor_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "observed_age_hours",
            _require_nonnegative_decimal("observed_age_hours", self.observed_age_hours),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchMarketProbabilityMemoryCostFloorReport:
    generated_at: datetime
    config_version: str
    status: str
    case_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_probability_gap: Decimal
    max_cost_floor_gap: Decimal
    max_observed_age_hours: Decimal
    reason_code_counts: tuple[ResearchMarketProbabilityMemoryCostFloorReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchMarketProbabilityMemoryCostFloorRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketProbabilityMemoryCostFloorReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_text("config_version", self.config_version),
        )
        _require_status("status", self.status)
        for field_name in ("case_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_probability_gap",
            "max_cost_floor_gap",
            "max_observed_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "derived_validation_digest",
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            ),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match public payload")


def build_research_market_probability_memory_cost_floor_report(
    *,
    items: object,
    generated_at: datetime,
    config: ResearchMarketProbabilityMemoryCostFloorConfig | None = None,
) -> ResearchMarketProbabilityMemoryCostFloorReport:
    generated_at = _as_utc("generated_at", generated_at)
    resolved_config = config or ResearchMarketProbabilityMemoryCostFloorConfig()
    if type(resolved_config) is not ResearchMarketProbabilityMemoryCostFloorConfig:
        raise ValueError("config must be a ResearchMarketProbabilityMemoryCostFloorConfig")
    _require_hard_flags("config", resolved_config)
    inputs = _normalize_inputs(items)
    for item in inputs:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (_row_from_input(item, config=resolved_config, generated_at=generated_at) for item in inputs),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": resolved_config.config_version,
        "status": _report_status(rows),
        "case_count": _count(len(rows)),
        "pass_count": _status_count(rows, STATUS_PASS),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "block_count": _status_count(rows, STATUS_BLOCK),
        "average_probability_gap": _average_probability_gap(rows),
        "max_cost_floor_gap": _max_cost_floor_gap(rows),
        "max_observed_age_hours": _max_observed_age_hours(rows),
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "reason_codes": reason_codes,
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketProbabilityMemoryCostFloorReport(
        **values,
        derived_validation_digest=_digest_from_values(values),
    )


def research_market_probability_memory_cost_floor_report_public_payload(
    report: ResearchMarketProbabilityMemoryCostFloorReport | Mapping[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketProbabilityMemoryCostFloorReport:
        _require_hard_flags("report", report)
        payload = _json_ready(asdict(report))
        if type(payload) is not dict:
            raise ValueError("public payload must be a JSON object")
        return validate_research_market_probability_memory_cost_floor_report_public_payload(
            payload,
        )
    return validate_research_market_probability_memory_cost_floor_report_public_payload(
        report,
    )


def research_market_probability_memory_cost_floor_report_digest(
    report: ResearchMarketProbabilityMemoryCostFloorReport | Mapping[str, Any],
) -> str:
    payload = research_market_probability_memory_cost_floor_report_public_payload(report)
    return _require_sha256_digest(_DIGEST_FIELD, payload[_DIGEST_FIELD])


def validate_research_market_probability_memory_cost_floor_report_public_payload(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(payload, Mapping) or isinstance(payload, (str, bytes)):
        raise ValueError("public payload must be a JSON object")
    ready = _json_ready(dict(payload))
    if type(ready) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload("public payload", ready, allow_json_containers=True)
    _require_hard_flags("public payload", _MapFlags(ready))
    _require_nested_hard_flags("public payload", ready)
    digest = _require_sha256_digest(_DIGEST_FIELD, ready.get(_DIGEST_FIELD))
    expected_digest = _digest_from_values(_without_digest(ready))
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")
    return ready


@dataclass(frozen=True)
class _MapFlags:
    value: Mapping[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_from_input(
    item: ResearchMarketProbabilityMemoryCostFloorInput,
    *,
    config: ResearchMarketProbabilityMemoryCostFloorConfig,
    generated_at: datetime,
) -> ResearchMarketProbabilityMemoryCostFloorRow:
    probability_gap = _absolute(item.observed_probability - item.memory_probability)
    cost_floor_gap = _cost_floor_gap(item.cost_floor_probability, item.observed_probability)
    observed_age_hours = _hours_between(item.observed_at, generated_at)
    reason_codes = _row_reason_codes(
        item,
        probability_gap=probability_gap,
        cost_floor_gap=cost_floor_gap,
        observed_age_hours=observed_age_hours,
        config=config,
    )
    return ResearchMarketProbabilityMemoryCostFloorRow(
        case_digest=_private_digest(item.private_ref),
        status=_row_status(reason_codes),
        observed_probability=item.observed_probability,
        memory_probability=item.memory_probability,
        probability_gap=probability_gap,
        memory_score=item.memory_score,
        cost_floor_probability=item.cost_floor_probability,
        cost_floor_gap=cost_floor_gap,
        observed_at=item.observed_at,
        observed_age_hours=observed_age_hours,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchMarketProbabilityMemoryCostFloorInput,
    *,
    probability_gap: Decimal,
    cost_floor_gap: Decimal,
    observed_age_hours: Decimal,
    config: ResearchMarketProbabilityMemoryCostFloorConfig,
) -> tuple[str, ...]:
    reasons = list(item.reason_codes)
    has_block = (
        probability_gap > config.max_watch_probability_gap
        or item.memory_score < config.watch_min_memory_score
        or cost_floor_gap > config.max_watch_cost_floor_gap
        or observed_age_hours >= config.block_stale_evidence_hours
    )
    has_watch = (
        probability_gap > config.max_pass_probability_gap
        or item.memory_score < config.pass_min_memory_score
        or cost_floor_gap > config.max_pass_cost_floor_gap
        or observed_age_hours >= config.watch_stale_evidence_hours
    )
    if has_block:
        reasons.append(REASON_BLOCK)
        if probability_gap > config.max_watch_probability_gap:
            reasons.append(REASON_PROBABILITY_GAP_BLOCK)
        if item.memory_score < config.watch_min_memory_score:
            reasons.append(REASON_MEMORY_SCORE_BLOCK)
        if cost_floor_gap > config.max_watch_cost_floor_gap:
            reasons.append(REASON_COST_FLOOR_GAP_BLOCK)
        if observed_age_hours >= config.block_stale_evidence_hours:
            reasons.append(REASON_STALE_EVIDENCE_BLOCK)
    elif has_watch:
        reasons.append(REASON_WATCH)
        if probability_gap > config.max_pass_probability_gap:
            reasons.append(REASON_PROBABILITY_GAP_WATCH)
        if item.memory_score < config.pass_min_memory_score:
            reasons.append(REASON_MEMORY_SCORE_WATCH)
        if cost_floor_gap > config.max_pass_cost_floor_gap:
            reasons.append(REASON_COST_FLOOR_GAP_WATCH)
        if observed_age_hours >= config.watch_stale_evidence_hours:
            reasons.append(REASON_STALE_EVIDENCE_WATCH)
    else:
        reasons.append(REASON_PASS)
    return _normalize_reason_codes(tuple(reasons), allow_empty=False)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return STATUS_BLOCK
    if any(reason.endswith("_watch") for reason in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(rows: tuple[ResearchMarketProbabilityMemoryCostFloorRow, ...]) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchMarketProbabilityMemoryCostFloorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (REASON_EMPTY_INPUT,)
    return _normalize_reason_codes(
        tuple(dict.fromkeys(reason for row in rows for reason in row.reason_codes)),
        allow_empty=False,
    )


def _reason_code_counts(
    rows: tuple[ResearchMarketProbabilityMemoryCostFloorRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketProbabilityMemoryCostFloorReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketProbabilityMemoryCostFloorReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
            ),
        )
    return tuple(
        ResearchMarketProbabilityMemoryCostFloorReasonCodeCount(
            reason_code=reason_code,
            count=_count(sum(1 for row in rows if reason_code in row.reason_codes)),
        )
        for reason_code in reason_codes
    )


def _normalize_inputs(
    items: object,
) -> tuple[ResearchMarketProbabilityMemoryCostFloorInput, ...]:
    if isinstance(items, (str, bytes)):
        raise ValueError("items must be an iterable")
    try:
        normalized = tuple(items)
    except TypeError as exc:
        raise ValueError("items must be an iterable") from exc
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchMarketProbabilityMemoryCostFloorInput:
            raise ValueError("items must contain ResearchMarketProbabilityMemoryCostFloorInput")
        _require_hard_flags("input", item)
        item_digest = _private_digest(item.private_ref)
        if item_digest in seen:
            raise ValueError("items must contain unique private_ref values")
        seen.add(item_digest)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchMarketProbabilityMemoryCostFloorRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchMarketProbabilityMemoryCostFloorRow:
            raise ValueError("rows must contain ResearchMarketProbabilityMemoryCostFloorRow")
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: object,
) -> tuple[ResearchMarketProbabilityMemoryCostFloorReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchMarketProbabilityMemoryCostFloorReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketProbabilityMemoryCostFloorReasonCodeCount",
            )
        _require_hard_flags("reason_count", value)
        if value.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(value.reason_code)
    return tuple(sorted(normalized, key=lambda value: _reason_sort_key(value.reason_code)))


def _normalize_reason_codes(reason_codes: object, *, allow_empty: bool) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not normalized and not allow_empty:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        _require_public_text("reason_codes", reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return tuple(sorted(normalized, key=_reason_sort_key))


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    try:
        return (_REASON_SEQUENCE.index(reason_code), reason_code)
    except ValueError:
        return (len(_REASON_SEQUENCE), reason_code)


def _row_sort_key(row: ResearchMarketProbabilityMemoryCostFloorRow) -> tuple[int, Decimal, Decimal, str]:
    return (
        {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[row.status],
        _quantize(_ONE - row.memory_score),
        row.probability_gap,
        row.case_digest,
    )


def _status_count(
    rows: tuple[ResearchMarketProbabilityMemoryCostFloorRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _average_probability_gap(
    rows: tuple[ResearchMarketProbabilityMemoryCostFloorRow, ...],
) -> Decimal:
    if not rows:
        return _ZERO
    return _quantize(sum((row.probability_gap for row in rows), _ZERO) / _count(len(rows)))


def _max_cost_floor_gap(rows: tuple[ResearchMarketProbabilityMemoryCostFloorRow, ...]) -> Decimal:
    if not rows:
        return _ZERO
    return max(row.cost_floor_gap for row in rows)


def _max_observed_age_hours(
    rows: tuple[ResearchMarketProbabilityMemoryCostFloorRow, ...],
) -> Decimal:
    if not rows:
        return _ZERO
    return max(row.observed_age_hours for row in rows)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _absolute(value: Decimal) -> Decimal:
    return _quantize(abs(value))


def _cost_floor_gap(cost_floor_probability: Decimal, observed_probability: Decimal) -> Decimal:
    if cost_floor_probability <= observed_probability:
        return _ZERO
    return _quantize(cost_floor_probability - observed_probability)


def _hours_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    total_micros = (
        Decimal(delta.days * 86400 * 1000000)
        + Decimal(delta.seconds * 1000000)
        + Decimal(delta.microseconds)
    )
    if total_micros < _ZERO:
        raise ValueError("observed_at must not be after generated_at")
    return _quantize(total_micros / _MICROS_PER_HOUR)


def _private_digest(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"


def _report_values_without_digest(
    report: ResearchMarketProbabilityMemoryCostFloorReport,
) -> dict[str, object]:
    return _without_digest(asdict(report))


def _without_digest(value: Mapping[str, object]) -> dict[str, object]:
    unsigned = dict(value)
    unsigned.pop(_DIGEST_FIELD, None)
    return unsigned


def _digest_from_values(values: Mapping[str, object]) -> str:
    ready = _json_ready(dict(values))
    _reject_unsafe_public_payload("digest payload", ready, allow_json_containers=True)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) in (int, float):
        raise ValueError("JSON numeric values must be Decimal-derived strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=True,
        )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers and type(value) is not dict:
            raise ValueError(f"{label} must use standard JSON containers")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_text(label, key)
            if key == _DIGEST_FIELD:
                _require_sha256_digest(key, item)
                continue
            if key.endswith("_digest"):
                _require_private_digest(key, item)
                continue
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        if not allow_json_containers and type(value) not in (list, tuple):
            raise ValueError(f"{label} must use standard JSON containers")
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value in {label}")


def _require_nested_hard_flags(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        for field_name in _FLAG_FIELDS:
            if field_name in value and value[field_name] is not True:
                raise ValueError(f"{field_name} must be True for {label}")
        for item in value.values():
            _require_nested_hard_flags(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _require_nested_hard_flags(label, item)


def _validate_row(row: ResearchMarketProbabilityMemoryCostFloorRow) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == STATUS_PASS and row.reason_codes != (REASON_PASS,):
        raise ValueError("pass status must have pass reason")
    if row.status == STATUS_WATCH and not any(
        reason.endswith("_watch") for reason in row.reason_codes
    ):
        raise ValueError("watch status must have watch reason")
    if row.status == STATUS_BLOCK and not any(
        reason.endswith("_block") for reason in row.reason_codes
    ):
        raise ValueError("block status must have block reason")
    if row.probability_gap != _absolute(row.observed_probability - row.memory_probability):
        raise ValueError("probability_gap must match probability values")
    if row.cost_floor_gap != _cost_floor_gap(
        row.cost_floor_probability,
        row.observed_probability,
    ):
        raise ValueError("cost_floor_gap must match probability values")


def _validate_report(report: ResearchMarketProbabilityMemoryCostFloorReport) -> None:
    if report.case_count != _count(len(report.rows)):
        raise ValueError("case_count must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.case_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match case_count")
    if report.average_probability_gap != _average_probability_gap(report.rows):
        raise ValueError("average_probability_gap must match rows")
    if report.max_cost_floor_gap != _max_cost_floor_gap(report.rows):
        raise ValueError("max_cost_floor_gap must match rows")
    if report.max_observed_age_hours != _max_observed_age_hours(report.rows):
        raise ValueError("max_observed_age_hours must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_private_text(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_private_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a private SHA-256 digest")
    if len(value) != 71 or not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a private SHA-256 digest")
    _require_sha256_digest(field_name, value[7:])
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a SHA-256 digest") from exc
    if value.lower() != value:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < _ZERO or value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_Q)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise TypeError(f"{label} must be {expected_type.__name__}")


__all__ = (
    "DEFAULT_RESEARCH_MARKET_PROBABILITY_MEMORY_COST_FLOOR_REPORT_CONFIG_VERSION",
    "ResearchMarketProbabilityMemoryCostFloorConfig",
    "ResearchMarketProbabilityMemoryCostFloorInput",
    "ResearchMarketProbabilityMemoryCostFloorReasonCodeCount",
    "ResearchMarketProbabilityMemoryCostFloorRow",
    "ResearchMarketProbabilityMemoryCostFloorReport",
    "build_research_market_probability_memory_cost_floor_report",
    "research_market_probability_memory_cost_floor_report_public_payload",
    "research_market_probability_memory_cost_floor_report_digest",
    "validate_research_market_probability_memory_cost_floor_report_public_payload",
)
