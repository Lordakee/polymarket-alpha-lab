"""Pure report-only analyst queue bottleneck report."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_QUEUE_BOTTLENECK_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_QUEUE_BOTTLENECK_REPORT_STATUSES",
    "ResearchStrategyQueueBottleneckConfig",
    "ResearchStrategyQueueBottleneckInput",
    "ResearchStrategyQueueBottleneckReport",
    "ResearchStrategyQueueBottleneckRow",
    "build_research_strategy_queue_bottleneck_report",
    "research_strategy_queue_bottleneck_report_digest",
    "research_strategy_queue_bottleneck_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_QUEUE_BOTTLENECK_REPORT_CONFIG_VERSION = (
    "research-strategy-queue-bottleneck-report-v0"
)
RESEARCH_STRATEGY_QUEUE_BOTTLENECK_REPORT_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FIVE = Decimal("5.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
BOTTLENECK_FIELDS = (
    "evidence_gap_score",
    "cost_sanity_gap_score",
    "resolution_ambiguity_score",
    "team_capacity_pressure_score",
    "memory_staleness_score",
)
BOTTLENECK_REASON_PREFIXES = (
    "evidence_gap",
    "cost_sanity_gap",
    "resolution_ambiguity",
    "team_capacity_pressure",
    "memory_staleness",
)
STATUS_WEIGHT = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
NO_ITEMS_REASON = "queue_bottleneck_report_empty"
SUMMARY_KEYS = (
    "generated_at",
    "config_version",
    "queue_item_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_queue_bottleneck_score",
    "maximum_bottleneck_score",
    "status",
    "queue_review_state",
    "reason_codes",
    "validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_DIGEST_KEYS = (
    "row_number",
    "public_queue_item_hash",
    "observed_at",
    "evidence_gap_score",
    "cost_sanity_gap_score",
    "resolution_ambiguity_score",
    "team_capacity_pressure_score",
    "memory_staleness_score",
    "queue_bottleneck_score",
    "maximum_bottleneck_score",
    "status",
    "queue_review_state",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_DIGEST_KEYS = (
    "generated_at",
    "config_version",
    "queue_item_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_queue_bottleneck_score",
    "maximum_bottleneck_score",
    "status",
    "queue_review_state",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
REASON_PRIORITY = (
    "evidence_gap_block",
    "cost_sanity_gap_block",
    "resolution_ambiguity_block",
    "team_capacity_pressure_block",
    "memory_staleness_block",
    "queue_bottleneck_report_block",
    "evidence_gap_watch",
    "cost_sanity_gap_watch",
    "resolution_ambiguity_watch",
    "team_capacity_pressure_watch",
    "memory_staleness_watch",
    "queue_bottleneck_report_watch",
    "queue_bottleneck_pass",
    "queue_bottleneck_report_pass",
    NO_ITEMS_REASON,
    "evidence_gap_review",
    "cost_sanity_gap_review",
    "resolution_ambiguity_review",
    "team_capacity_pressure_review",
    "memory_staleness_review",
)
QUEUE_REVIEW_STATES = (
    "queue_review_ready",
    "queue_review_watch",
    "queue_review_block",
)
UNSAFE_TEXT_FRAGMENTS = (
    "raw" "-" "candidate",
    "candidate" "_" "id",
    "candidate" "-" "id",
    "market" "_" "id",
    "market" "-" "id",
    "market" "_" "slug",
    "market" "-" "slug",
    "ques" "tion",
    "source" "_" "url",
    "source" "-" "url",
    "source" "_" "text",
    "source" "-" "text",
    "d" "sn",
    "ta" "ble",
    "tok" "en",
    "private" "_" "key",
    "api" "_" "key",
    "sec" "ret",
    "pass" "word",
    "au" "th",
    "wal" "let",
    "bro" "ker",
    "or" "der",
    "can" "cel",
    "re" "place",
    "sign" "ing",
    "li" "ve",
    "data" "base",
    "net" "work",
    "req" "uests",
    "ht" "tp",
    "sock" "et",
    "sub" "process",
    "reco" "mmend",
    "siz" "ing",
    "po" "sition",
    "b" "uy",
    "s" "ell",
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
class ResearchStrategyQueueBottleneckConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_QUEUE_BOTTLENECK_REPORT_CONFIG_VERSION
    )
    component_watch_threshold: Decimal = Decimal("0.250000")
    component_block_threshold: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyQueueBottleneckConfig, "config")
        _require_public_text("config_version", self.config_version)
        for field_name in ("component_watch_threshold", "component_block_threshold"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.component_block_threshold < self.component_watch_threshold:
            raise ValueError(
                "component_block_threshold must be at least component_watch_threshold",
            )
        _require_hard_phase_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyQueueBottleneckInput(_FinalDataclass):
    internal_queue_ref: str
    observed_at: datetime
    evidence_gap_score: Decimal
    cost_sanity_gap_score: Decimal
    resolution_ambiguity_score: Decimal
    team_capacity_pressure_score: Decimal
    memory_staleness_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyQueueBottleneckInput, "input")
        _require_private_reference("internal_queue_ref", self.internal_queue_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in BOTTLENECK_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_phase_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyQueueBottleneckRow(_FinalDataclass):
    row_number: Decimal
    public_queue_item_hash: str
    observed_at: datetime
    evidence_gap_score: Decimal
    cost_sanity_gap_score: Decimal
    resolution_ambiguity_score: Decimal
    team_capacity_pressure_score: Decimal
    memory_staleness_score: Decimal
    queue_bottleneck_score: Decimal
    maximum_bottleneck_score: Decimal
    status: str
    queue_review_state: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyQueueBottleneckRow, "row")
        object.__setattr__(
            self,
            "row_number",
            _normalize_positive_count("row_number", self.row_number),
        )
        _require_public_hash("public_queue_item_hash", self.public_queue_item_hash)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in BOTTLENECK_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "queue_bottleneck_score",
            _normalize_ratio("queue_bottleneck_score", self.queue_bottleneck_score),
        )
        object.__setattr__(
            self,
            "maximum_bottleneck_score",
            _normalize_ratio("maximum_bottleneck_score", self.maximum_bottleneck_score),
        )
        _require_status("status", self.status)
        _require_queue_review_state("queue_review_state", self.queue_review_state)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_digest("validation_digest", self.validation_digest)
        _require_hard_phase_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchStrategyQueueBottleneckReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    queue_item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_queue_bottleneck_score: Decimal | None
    maximum_bottleneck_score: Decimal | None
    status: str
    queue_review_state: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyQueueBottleneckRow, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyQueueBottleneckReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        for field_name in ("queue_item_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_queue_bottleneck_score", "maximum_bottleneck_score"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _normalize_ratio(field_name, value))
        _require_status("status", self.status)
        _require_queue_review_state("queue_review_state", self.queue_review_state)
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


def build_research_strategy_queue_bottleneck_report(
    queue_items: Iterable[ResearchStrategyQueueBottleneckInput],
    *,
    config: ResearchStrategyQueueBottleneckConfig,
    generated_at: datetime,
) -> ResearchStrategyQueueBottleneckReport:
    if type(config) is not ResearchStrategyQueueBottleneckConfig:
        raise ValueError("config must be a ResearchStrategyQueueBottleneckConfig")
    _require_hard_phase_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_queue_items(queue_items)
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
        "queue_item_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_queue_bottleneck_score": _average_queue_bottleneck_score(rows),
        "maximum_bottleneck_score": _report_maximum_bottleneck_score(rows),
        "status": report_status,
        "queue_review_state": _queue_review_state(report_status),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyQueueBottleneckReport(
        **report_values,
        validation_digest=_validation_digest(report_values),
    )


def research_strategy_queue_bottleneck_report_payload(
    report: ResearchStrategyQueueBottleneckReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyQueueBottleneckReport:
        _require_hard_phase_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchStrategyQueueBottleneckReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_payload(payload)
    _require_hard_phase_flags("payload", _DictFlags(payload))
    _validate_payload_digests(payload)
    return payload


def research_strategy_queue_bottleneck_report_digest(
    report: ResearchStrategyQueueBottleneckReport,
) -> dict[str, Any]:
    payload = research_strategy_queue_bottleneck_report_payload(report)
    return {key: payload[key] for key in SUMMARY_KEYS}


def _draft_row_values(
    queue_item: ResearchStrategyQueueBottleneckInput,
    *,
    config: ResearchStrategyQueueBottleneckConfig,
) -> dict[str, object]:
    bottleneck_values = _bottleneck_values(queue_item)
    reason_codes = _row_reason_codes(queue_item, config=config)
    row_status = _row_status(reason_codes)
    return {
        "public_queue_item_hash": _public_hash(queue_item.internal_queue_ref),
        "observed_at": queue_item.observed_at,
        "evidence_gap_score": queue_item.evidence_gap_score,
        "cost_sanity_gap_score": queue_item.cost_sanity_gap_score,
        "resolution_ambiguity_score": queue_item.resolution_ambiguity_score,
        "team_capacity_pressure_score": queue_item.team_capacity_pressure_score,
        "memory_staleness_score": queue_item.memory_staleness_score,
        "queue_bottleneck_score": _queue_bottleneck_score(bottleneck_values),
        "maximum_bottleneck_score": max(bottleneck_values),
        "status": row_status,
        "queue_review_state": _queue_review_state(row_status),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_from_draft(
    *,
    row_number: int,
    draft_values: dict[str, object],
) -> ResearchStrategyQueueBottleneckRow:
    row_values = {"row_number": _count(row_number), **draft_values}
    return ResearchStrategyQueueBottleneckRow(
        **row_values,
        validation_digest=_validation_digest(row_values),
    )


def _row_reason_codes(
    queue_item: ResearchStrategyQueueBottleneckInput,
    *,
    config: ResearchStrategyQueueBottleneckConfig,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    for field_name, reason_prefix in zip(BOTTLENECK_FIELDS, BOTTLENECK_REASON_PREFIXES):
        value = getattr(queue_item, field_name)
        if value >= config.component_block_threshold:
            block_reasons.append(f"{reason_prefix}_block")
        elif value > config.component_watch_threshold:
            watch_reasons.append(f"{reason_prefix}_watch")
    reasons = tuple(block_reasons + watch_reasons)
    if not reasons:
        reasons = ("queue_bottleneck_pass",)
    return _normalize_reason_codes(reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchStrategyQueueBottleneckRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _queue_review_state(status: str) -> str:
    if status == "block":
        return "queue_review_block"
    if status == "watch":
        return "queue_review_watch"
    return "queue_review_ready"


def _report_reason_codes(
    rows: tuple[ResearchStrategyQueueBottleneckRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_ITEMS_REASON,)
    status = _report_status(rows)
    row_codes = tuple(code for row in rows for code in row.reason_codes)
    review_codes = []
    for reason_prefix in BOTTLENECK_REASON_PREFIXES:
        if any(code.startswith(f"{reason_prefix}_") for code in row_codes):
            review_codes.append(f"{reason_prefix}_review")
    return _normalize_reason_codes(
        (f"queue_bottleneck_report_{status}", *tuple(review_codes)),
    )


def _bottleneck_values(
    queue_item: ResearchStrategyQueueBottleneckInput,
) -> tuple[Decimal, ...]:
    return tuple(getattr(queue_item, field_name) for field_name in BOTTLENECK_FIELDS)


def _queue_bottleneck_score(values: tuple[Decimal, ...]) -> Decimal:
    return _ratio(_sum_decimal(values), FIVE)


def _average_queue_bottleneck_score(
    rows: tuple[ResearchStrategyQueueBottleneckRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _ratio(
        _sum_decimal(tuple(row.queue_bottleneck_score for row in rows)),
        _count(len(rows)),
    )


def _report_maximum_bottleneck_score(
    rows: tuple[ResearchStrategyQueueBottleneckRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return max(row.maximum_bottleneck_score for row in rows)


def _normalize_queue_items(
    queue_items: Iterable[ResearchStrategyQueueBottleneckInput],
) -> tuple[ResearchStrategyQueueBottleneckInput, ...]:
    if isinstance(queue_items, (str, bytes)):
        raise ValueError("queue_items must be an iterable")
    try:
        values = tuple(queue_items)
    except TypeError as exc:
        raise ValueError("queue_items must be an iterable") from exc
    seen: set[str] = set()
    for queue_item in values:
        if type(queue_item) is not ResearchStrategyQueueBottleneckInput:
            raise ValueError(
                "queue_items must contain ResearchStrategyQueueBottleneckInput",
            )
        _require_hard_phase_flags("input", queue_item)
        if queue_item.internal_queue_ref in seen:
            raise ValueError("queue_items must not contain duplicate values")
        seen.add(queue_item.internal_queue_ref)
    return values


def _normalize_rows(
    rows: Iterable[ResearchStrategyQueueBottleneckRow],
) -> tuple[ResearchStrategyQueueBottleneckRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in values:
        if type(row) is not ResearchStrategyQueueBottleneckRow:
            raise ValueError("rows must contain ResearchStrategyQueueBottleneckRow")
        _require_hard_phase_flags("row", row)
        if row.public_queue_item_hash in seen:
            raise ValueError("public_queue_item_hash values must be unique")
        seen.add(row.public_queue_item_hash)
    expected_numbers = tuple(_count(index) for index in range(1, len(values) + 1))
    actual_numbers = tuple(row.row_number for row in values)
    if actual_numbers != expected_numbers:
        raise ValueError("rows must be sorted deterministically")
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return values


def _validate_row(row: ResearchStrategyQueueBottleneckRow) -> None:
    bottleneck_values = tuple(getattr(row, field_name) for field_name in BOTTLENECK_FIELDS)
    if row.queue_bottleneck_score != _queue_bottleneck_score(bottleneck_values):
        raise ValueError("queue_bottleneck_score must match bottleneck scores")
    if row.maximum_bottleneck_score != max(bottleneck_values):
        raise ValueError("maximum_bottleneck_score must match bottleneck scores")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.queue_review_state != _queue_review_state(row.status):
        raise ValueError("queue_review_state must match status")
    if row.validation_digest != _validation_digest(_row_digest_values(row)):
        raise ValueError("validation_digest must match row payload")


def _validate_report(report: ResearchStrategyQueueBottleneckReport) -> None:
    if report.queue_item_count != _count(len(report.rows)):
        raise ValueError("queue_item_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_queue_bottleneck_score != _average_queue_bottleneck_score(
        report.rows,
    ):
        raise ValueError("average_queue_bottleneck_score must match rows")
    if report.maximum_bottleneck_score != _report_maximum_bottleneck_score(report.rows):
        raise ValueError("maximum_bottleneck_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.queue_review_state != _queue_review_state(report.status):
        raise ValueError("queue_review_state must match status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.validation_digest != _validation_digest(_report_digest_values(report)):
        raise ValueError("validation_digest must match report payload")


def _row_digest_values(row: ResearchStrategyQueueBottleneckRow) -> dict[str, Any]:
    return {key: getattr(row, key) for key in ROW_DIGEST_KEYS}


def _report_digest_values(report: ResearchStrategyQueueBottleneckReport) -> dict[str, Any]:
    return {key: getattr(report, key) for key in REPORT_DIGEST_KEYS}


def _status_count(
    rows: tuple[ResearchStrategyQueueBottleneckRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _draft_sort_key(draft_values: dict[str, object]) -> tuple[Decimal, Decimal, str]:
    status = draft_values["status"]
    if type(status) is not str:
        raise ValueError("draft status must be a string")
    maximum_bottleneck_score = draft_values["maximum_bottleneck_score"]
    if type(maximum_bottleneck_score) is not Decimal:
        raise ValueError("draft maximum_bottleneck_score must be a Decimal")
    public_hash = draft_values["public_queue_item_hash"]
    if type(public_hash) is not str:
        raise ValueError("draft public_queue_item_hash must be a string")
    return (STATUS_WEIGHT[status], -maximum_bottleneck_score, public_hash)


def _row_sort_key(row: ResearchStrategyQueueBottleneckRow) -> tuple[Decimal, Decimal, str]:
    return (STATUS_WEIGHT[row.status], -row.maximum_bottleneck_score, row.public_queue_item_hash)


def _validate_payload_digests(payload: dict[str, Any]) -> None:
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("payload rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("payload rows must contain objects")
        _require_payload_keys(row, (*ROW_DIGEST_KEYS, "validation_digest"))
        row_values = {key: row[key] for key in ROW_DIGEST_KEYS}
        if row["validation_digest"] != _validation_digest(row_values):
            raise ValueError("validation_digest must match row payload")
    _require_payload_keys(payload, (*REPORT_DIGEST_KEYS, "validation_digest"))
    report_values = {key: payload[key] for key in REPORT_DIGEST_KEYS}
    if payload["validation_digest"] != _validation_digest(report_values):
        raise ValueError("validation_digest must match report payload")


def _require_payload_keys(payload: dict[str, Any], keys: Sequence[str]) -> None:
    missing = tuple(key for key in keys if key not in payload)
    if missing:
        raise ValueError("payload is missing required digest fields")


def _validation_digest(values: Mapping[str, Any]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_payload(payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal-derived strings")
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


def _reject_unsafe_payload(value: object, path: str = "payload") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_payload(asdict(value), path)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError(f"{path}.{key} has unsafe public field")
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{path}.{key} must be True")
            _reject_unsafe_payload(item, key if not path else f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_unsafe_payload(item, f"{path}[{index}]")
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"{path} has unsafe public value")


def _has_unsafe_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_phase_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_private_reference(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty private text")
    if len(value) > 1024:
        raise ValueError(f"{field_name} must not exceed 1024 characters")
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 256:
        raise ValueError(f"{field_name} must not exceed 256 characters")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{field_name} has unsafe public value")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in RESEARCH_STRATEGY_QUEUE_BOTTLENECK_REPORT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_queue_review_state(field_name: str, value: object) -> str:
    if type(value) is not str or value not in QUEUE_REVIEW_STATES:
        raise ValueError(f"{field_name} must be a queue review state")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or set(value) - set("0123456789abcdef"):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_public_hash(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    prefix = "sha256:"
    digest = value.removeprefix(prefix)
    if digest == value:
        raise ValueError(f"{field_name} must be a sha256 public hash")
    _require_digest(field_name, digest)
    return value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_text("reason_code", reason_code)
        if reason_code not in REASON_PRIORITY:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(code for code in REASON_PRIORITY if code in normalized)


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    with localcontext(DECIMAL_CONTEXT):
        for value in values:
            total += value
    return total.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        value = numerator / denominator
    return _normalize_ratio("ratio", value)


def _public_hash(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()
