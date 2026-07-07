"""Report-only research information gap prioritizer."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_INFORMATION_GAP_PRIORITIZER_CONFIG_VERSION = (
    "research-information-gap-prioritizer-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
REPORT_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCKED)
ROW_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCKED)

NO_INFORMATION_GAPS_REASON = "no_information_gaps"
INFORMATION_GAP_PASS_REASON = "information_gap_pass"
INFORMATION_GAP_WATCH_REASON = "information_gap_watch"
INFORMATION_GAP_BLOCK_REASON = "information_gap_block"
PRIORITY_PASS_REASON = "priority_pass"
PRIORITY_WATCH_REASON = "priority_watch"
PRIORITY_BLOCK_REASON = "priority_block"
IMPACT_WATCH_REASON = "impact_watch"
TIME_SENSITIVITY_WATCH_REASON = "time_sensitivity_watch"
AVAILABILITY_WATCH_REASON = "availability_watch"
CONFLICT_RISK_BLOCK_REASON = "conflict_risk_block"

ROW_REASON_CODES = (
    PRIORITY_BLOCK_REASON,
    PRIORITY_WATCH_REASON,
    PRIORITY_PASS_REASON,
    IMPACT_WATCH_REASON,
    TIME_SENSITIVITY_WATCH_REASON,
    AVAILABILITY_WATCH_REASON,
    CONFLICT_RISK_BLOCK_REASON,
)
REPORT_REASON_CODES = (
    NO_INFORMATION_GAPS_REASON,
    INFORMATION_GAP_BLOCK_REASON,
    INFORMATION_GAP_WATCH_REASON,
    INFORMATION_GAP_PASS_REASON,
    PRIORITY_BLOCK_REASON,
    PRIORITY_WATCH_REASON,
    PRIORITY_PASS_REASON,
    IMPACT_WATCH_REASON,
    TIME_SENSITIVITY_WATCH_REASON,
    AVAILABILITY_WATCH_REASON,
    CONFLICT_RISK_BLOCK_REASON,
)
NEXT_STEPS = {
    STATUS_PASS: "archive_report_only_information_gap_priorities",
    STATUS_WATCH: "collect_watched_information_gaps",
    STATUS_BLOCKED: "collect_blocking_information_gaps",
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")

SAFETY_FLAG_NAMES = frozenset(("paper_only", "report_only", "readonly"))
PUBLIC_VALUE_TERM_ALLOWLIST_KEYS = frozenset(("config_version",))
UNSAFE_PUBLIC_TERMS = (
    "http://",
    "https://",
    "api_key",
    "auth",
    "buy",
    "client",
    "credential",
    "database",
    "network",
    "order",
    "position",
    "private",
    "request",
    "secret",
    "sell",
    "socket",
    "stake",
    "token",
    "trade",
    "wallet",
)


@dataclass(frozen=True)
class ResearchInformationGapPrioritizerConfig:
    config_version: str = DEFAULT_RESEARCH_INFORMATION_GAP_PRIORITIZER_CONFIG_VERSION
    impact_weight: Decimal = Decimal("0.400000")
    time_sensitivity_weight: Decimal = Decimal("0.250000")
    availability_weight: Decimal = Decimal("0.200000")
    conflict_risk_weight: Decimal = Decimal("0.150000")
    watch_priority_threshold: Decimal = Decimal("0.500000")
    block_priority_threshold: Decimal = Decimal("0.750000")
    component_watch_threshold: Decimal = Decimal("0.600000")
    availability_watch_threshold: Decimal = Decimal("0.700000")
    conflict_block_threshold: Decimal = Decimal("0.850000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchInformationGapPrioritizerConfig:
            raise TypeError(
                "ResearchInformationGapPrioritizerConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchInformationGapPrioritizerConfig:
            raise ValueError(
                "config must be exactly ResearchInformationGapPrioritizerConfig",
            )
        _require_public_string(
            "config_version",
            self.config_version,
            allow_public_terms=True,
        )
        for field_name in (
            "impact_weight",
            "time_sensitivity_weight",
            "availability_weight",
            "conflict_risk_weight",
            "watch_priority_threshold",
            "block_priority_threshold",
            "component_watch_threshold",
            "availability_watch_threshold",
            "conflict_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchInformationGapInput:
    gap_id: str
    research_area: str
    public_gap_summary: str
    impact_score: Decimal
    time_sensitivity_score: Decimal
    availability_score: Decimal
    conflict_risk_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchInformationGapInput:
            raise TypeError("ResearchInformationGapInput does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchInformationGapInput:
            raise ValueError("input must be exactly ResearchInformationGapInput")
        for field_name in ("gap_id", "research_area", "public_gap_summary"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "impact_score",
            "time_sensitivity_score",
            "availability_score",
            "conflict_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchInformationGapRow:
    gap_id: str
    research_area: str
    public_gap_summary: str
    collection_priority: Decimal
    impact_score: Decimal
    time_sensitivity_score: Decimal
    availability_score: Decimal
    conflict_risk_score: Decimal
    priority_score: Decimal
    gap_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchInformationGapRow:
            raise TypeError("ResearchInformationGapRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchInformationGapRow:
            raise ValueError("row must be exactly ResearchInformationGapRow")
        for field_name in ("gap_id", "research_area", "public_gap_summary"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "collection_priority",
            _require_nonnegative_count_decimal(
                "collection_priority",
                self.collection_priority,
            ),
        )
        if self.collection_priority <= ZERO_COUNT:
            raise ValueError("collection_priority must be positive")
        for field_name in (
            "impact_score",
            "time_sensitivity_score",
            "availability_score",
            "conflict_risk_score",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("gap_status", self.gap_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _validate_or_set_digest(self)


@dataclass(frozen=True)
class ResearchInformationGapPrioritizerReport:
    generated_at: datetime
    config_version: str
    report_status: str
    next_step: str
    gap_count: Decimal
    pass_gap_count: Decimal
    watch_gap_count: Decimal
    blocked_gap_count: Decimal
    high_impact_count: Decimal
    high_time_sensitivity_count: Decimal
    high_availability_count: Decimal
    high_conflict_risk_count: Decimal
    max_priority_score: Decimal
    average_priority_score: Decimal
    rows: tuple[ResearchInformationGapRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchInformationGapPrioritizerReport:
            raise TypeError(
                "ResearchInformationGapPrioritizerReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchInformationGapPrioritizerReport:
            raise ValueError(
                "report must be exactly ResearchInformationGapPrioritizerReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string(
            "config_version",
            self.config_version,
            allow_public_terms=True,
        )
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        _require_public_string("next_step", self.next_step)
        for field_name in (
            "gap_count",
            "pass_gap_count",
            "watch_gap_count",
            "blocked_gap_count",
            "high_impact_count",
            "high_time_sensitivity_count",
            "high_availability_count",
            "high_conflict_risk_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_priority_score", "average_priority_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_hard_flags("report", self)
        _validate_or_set_digest(self)
        _validate_report(self)


def build_research_information_gap_prioritizer_report(
    inputs: list[ResearchInformationGapInput] | tuple[ResearchInformationGapInput, ...],
    *,
    config: ResearchInformationGapPrioritizerConfig,
    generated_at: datetime,
) -> ResearchInformationGapPrioritizerReport:
    if type(config) is not ResearchInformationGapPrioritizerConfig:
        raise ValueError("config must be a ResearchInformationGapPrioritizerConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    unranked_rows = tuple(_row_from_input(row, config=config) for row in normalized_inputs)
    sorted_rows = tuple(sorted(unranked_rows, key=_row_sort_key))
    ranked_rows = tuple(
        _row_with_collection_priority(row, _count(index))
        for index, row in enumerate(sorted_rows, start=1)
    )
    report_status = _report_status(ranked_rows)
    return ResearchInformationGapPrioritizerReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=report_status,
        next_step=NEXT_STEPS[report_status],
        gap_count=_count(len(ranked_rows)),
        pass_gap_count=_status_count(ranked_rows, STATUS_PASS),
        watch_gap_count=_status_count(ranked_rows, STATUS_WATCH),
        blocked_gap_count=_status_count(ranked_rows, STATUS_BLOCKED),
        high_impact_count=_component_count(
            tuple(row.impact_score for row in ranked_rows),
            config.component_watch_threshold,
        ),
        high_time_sensitivity_count=_component_count(
            tuple(row.time_sensitivity_score for row in ranked_rows),
            config.component_watch_threshold,
        ),
        high_availability_count=_component_count(
            tuple(row.availability_score for row in ranked_rows),
            config.availability_watch_threshold,
        ),
        high_conflict_risk_count=_component_count(
            tuple(row.conflict_risk_score for row in ranked_rows),
            config.conflict_block_threshold,
        ),
        max_priority_score=_max_priority(ranked_rows),
        average_priority_score=_average_priority(ranked_rows),
        rows=ranked_rows,
        reason_codes=_report_reason_codes(ranked_rows),
    )


def research_information_gap_prioritizer_payload(
    report: ResearchInformationGapPrioritizerReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchInformationGapPrioritizerReport:
        _require_hard_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchInformationGapPrioritizerReport or payload",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_payload_flags(payload)
    _reject_unsafe_public_payload("payload", payload)
    _validate_payload_digest(payload)
    return payload


def _validate_config(config: ResearchInformationGapPrioritizerConfig) -> None:
    with localcontext(DECIMAL_CONTEXT):
        total_weight = (
            config.impact_weight
            + config.time_sensitivity_weight
            + config.availability_weight
            + config.conflict_risk_weight
        ).quantize(RATIO_QUANTUM)
    if total_weight != ONE_RATIO:
        raise ValueError("weight values must sum to 1.000000")
    if config.watch_priority_threshold > config.block_priority_threshold:
        raise ValueError("block_priority_threshold must be at least watch_priority_threshold")


def _normalize_inputs(
    inputs: list[ResearchInformationGapInput] | tuple[ResearchInformationGapInput, ...],
) -> tuple[ResearchInformationGapInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    seen_gap_ids: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchInformationGapInput:
            raise ValueError("inputs must contain ResearchInformationGapInput values")
        _require_hard_flags("input", row)
        if row.gap_id in seen_gap_ids:
            raise ValueError("inputs must not contain duplicate gap_id values")
        seen_gap_ids.add(row.gap_id)
    return normalized


def _row_from_input(
    row: ResearchInformationGapInput,
    *,
    config: ResearchInformationGapPrioritizerConfig,
) -> ResearchInformationGapRow:
    priority_score = _priority_score(row, config)
    status = _row_status(row, config=config, priority_score=priority_score)
    return ResearchInformationGapRow(
        gap_id=row.gap_id,
        research_area=row.research_area,
        public_gap_summary=row.public_gap_summary,
        collection_priority=ONE_RATIO.quantize(COUNT_QUANTUM),
        impact_score=row.impact_score,
        time_sensitivity_score=row.time_sensitivity_score,
        availability_score=row.availability_score,
        conflict_risk_score=row.conflict_risk_score,
        priority_score=priority_score,
        gap_status=status,
        reason_codes=_row_reason_codes(
            row,
            config=config,
            priority_score=priority_score,
            status=status,
        ),
    )


def _row_with_collection_priority(
    row: ResearchInformationGapRow,
    collection_priority: Decimal,
) -> ResearchInformationGapRow:
    return ResearchInformationGapRow(
        gap_id=row.gap_id,
        research_area=row.research_area,
        public_gap_summary=row.public_gap_summary,
        collection_priority=collection_priority,
        impact_score=row.impact_score,
        time_sensitivity_score=row.time_sensitivity_score,
        availability_score=row.availability_score,
        conflict_risk_score=row.conflict_risk_score,
        priority_score=row.priority_score,
        gap_status=row.gap_status,
        reason_codes=row.reason_codes,
    )


def _priority_score(
    row: ResearchInformationGapInput,
    config: ResearchInformationGapPrioritizerConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            row.impact_score * config.impact_weight
            + row.time_sensitivity_score * config.time_sensitivity_weight
            + row.availability_score * config.availability_weight
            + row.conflict_risk_score * config.conflict_risk_weight
        )
        return score.quantize(RATIO_QUANTUM)


def _row_status(
    row: ResearchInformationGapInput,
    *,
    config: ResearchInformationGapPrioritizerConfig,
    priority_score: Decimal,
) -> str:
    if (
        priority_score >= config.block_priority_threshold
        or row.conflict_risk_score >= config.conflict_block_threshold
    ):
        return STATUS_BLOCKED
    if (
        priority_score >= config.watch_priority_threshold
        or row.impact_score >= config.component_watch_threshold
        or row.time_sensitivity_score >= config.component_watch_threshold
        or row.availability_score >= config.availability_watch_threshold
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    row: ResearchInformationGapInput,
    *,
    config: ResearchInformationGapPrioritizerConfig,
    priority_score: Decimal,
    status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if status == STATUS_BLOCKED:
        reason_codes.append(PRIORITY_BLOCK_REASON)
    elif priority_score >= config.watch_priority_threshold:
        reason_codes.append(PRIORITY_WATCH_REASON)
    else:
        reason_codes.append(PRIORITY_PASS_REASON)
    if row.impact_score >= config.component_watch_threshold:
        reason_codes.append(IMPACT_WATCH_REASON)
    if row.time_sensitivity_score >= config.component_watch_threshold:
        reason_codes.append(TIME_SENSITIVITY_WATCH_REASON)
    if row.availability_score >= config.availability_watch_threshold:
        reason_codes.append(AVAILABILITY_WATCH_REASON)
    if row.conflict_risk_score >= config.conflict_block_threshold:
        reason_codes.append(CONFLICT_RISK_BLOCK_REASON)
    return tuple(reason_codes)


def _row_sort_key(row: ResearchInformationGapRow) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, str, str]:
    return (
        -row.priority_score,
        -row.impact_score,
        -row.time_sensitivity_score,
        -row.availability_score,
        -row.conflict_risk_score,
        row.research_area,
        row.gap_id,
    )


def _report_status(rows: tuple[ResearchInformationGapRow, ...]) -> str:
    if any(row.gap_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.gap_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(rows: tuple[ResearchInformationGapRow, ...]) -> tuple[str, ...]:
    if not rows:
        return (NO_INFORMATION_GAPS_REASON,)
    reason_codes: list[str] = []
    report_status = _report_status(rows)
    if report_status == STATUS_BLOCKED:
        reason_codes.append(INFORMATION_GAP_BLOCK_REASON)
    elif report_status == STATUS_WATCH:
        reason_codes.append(INFORMATION_GAP_WATCH_REASON)
    else:
        reason_codes.append(INFORMATION_GAP_PASS_REASON)
    present = {reason for row in rows for reason in row.reason_codes}
    for reason in ROW_REASON_CODES:
        if reason == PRIORITY_PASS_REASON and report_status != STATUS_PASS:
            continue
        if reason in present:
            reason_codes.append(reason)
    return tuple(reason_codes)


def _status_count(rows: tuple[ResearchInformationGapRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.gap_status == status))


def _component_count(values: tuple[Decimal, ...], threshold: Decimal) -> Decimal:
    return _count(sum(1 for value in values if value >= threshold))


def _max_priority(rows: tuple[ResearchInformationGapRow, ...]) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return max(row.priority_score for row in rows)


def _average_priority(rows: tuple[ResearchInformationGapRow, ...]) -> Decimal:
    if not rows:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (sum((row.priority_score for row in rows), ZERO_RATIO) / _count(len(rows))).quantize(
            RATIO_QUANTUM,
        )


def _normalize_rows(
    rows: tuple[ResearchInformationGapRow, ...],
) -> tuple[ResearchInformationGapRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchInformationGapRow:
            raise ValueError("rows must contain ResearchInformationGapRow values")
        _require_hard_flags("row", row)
    return rows


def _validate_report(report: ResearchInformationGapPrioritizerReport) -> None:
    if report.next_step != NEXT_STEPS[report.report_status]:
        raise ValueError("next_step does not match report_status")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted by deterministic priority")
    expected_priorities = tuple(_count(index) for index in range(1, len(report.rows) + 1))
    if tuple(row.collection_priority for row in report.rows) != expected_priorities:
        raise ValueError("collection_priority values must be sequential")
    if report.gap_count != _count(len(report.rows)):
        raise ValueError("gap_count does not match rows")
    if report.pass_gap_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_gap_count does not match rows")
    if report.watch_gap_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_gap_count does not match rows")
    if report.blocked_gap_count != _status_count(report.rows, STATUS_BLOCKED):
        raise ValueError("blocked_gap_count does not match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status does not match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes do not match rows")
    if report.max_priority_score != _max_priority(report.rows):
        raise ValueError("max_priority_score does not match rows")
    if report.average_priority_score != _average_priority(report.rows):
        raise ValueError("average_priority_score does not match rows")


def _validate_or_set_digest(value: object) -> None:
    current = getattr(value, "derived_validation_digest")
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _digest(value)
    if current == "":
        object.__setattr__(value, "derived_validation_digest", expected)
        return
    if current != expected:
        raise ValueError("derived_validation_digest mismatch")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    payload_without_digest = _strip_digest(payload)
    canonical = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    expected = sha256(canonical.encode("utf-8")).hexdigest()
    if digest != expected:
        raise ValueError("derived_validation_digest mismatch")
    for row_payload in payload.get("rows", []):
        if type(row_payload) is not dict:
            raise ValueError("rows must contain objects")
        row_digest = row_payload.get("derived_validation_digest")
        if type(row_digest) is not str:
            raise ValueError("row derived_validation_digest must be a string")
        row_without_digest = _strip_digest(row_payload)
        row_canonical = json.dumps(
            row_without_digest,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        expected_row_digest = sha256(row_canonical.encode("utf-8")).hexdigest()
        if row_digest != expected_row_digest:
            raise ValueError("derived_validation_digest mismatch")


def _digest(value: object) -> str:
    payload = _json_ready(value, include_digest=False)
    _reject_unsafe_public_payload("digest payload", payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _strip_digest(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_digest(item)
            for key, item in value.items()
            if key != "derived_validation_digest"
        }
    if isinstance(value, list):
        return [_strip_digest(item) for item in value]
    return value


def _json_ready(value: Any, *, include_digest: bool = True) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        ready: dict[str, Any] = {}
        for field in fields(value):
            if not include_digest and field.name == "derived_validation_digest":
                continue
            ready[field.name] = _json_ready(
                getattr(value, field.name),
                include_digest=include_digest,
            )
        return ready
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item, include_digest=include_digest) for item in value]
    if isinstance(value, list):
        return [_json_ready(item, include_digest=include_digest) for item in value]
    if isinstance(value, dict):
        return {
            _json_ready(key, include_digest=include_digest): _json_ready(
                item,
                include_digest=include_digest,
            )
            for key, item in value.items()
        }
    raise ValueError("payload contains unsupported value")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if _contains_unsafe_public_term(key):
                raise ValueError(f"unsafe public key in {label}: {key}")
            item_path = key if path == "" else f"{path}.{key}"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{path}[{index}]")
        return
    if isinstance(value, str) and _path_leaf(path) not in PUBLIC_VALUE_TERM_ALLOWLIST_KEYS:
        if _contains_unsafe_public_term(value):
            raise ValueError(f"unsafe public value in {label}: {path}")


def _path_leaf(path: str) -> str:
    if "." in path:
        return path.rsplit(".", 1)[1]
    return path


def _contains_unsafe_public_term(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in UNSAFE_PUBLIC_TERMS)


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in SAFETY_FLAG_NAMES:
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for payload")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in SAFETY_FLAG_NAMES:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_string(
    field_name: str,
    value: str,
    *,
    allow_public_terms: bool = False,
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() == "":
        raise ValueError(f"{field_name} must not be blank")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    if not allow_public_terms and _contains_unsafe_public_term(value):
        raise ValueError(f"unsafe public value in {field_name}")
    return value


def _require_member(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed_values)}")


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized: list[str] = []
    seen_values: set[str] = set()
    for value in values:
        _require_public_string(field_name, value)
        _require_member(field_name, value, allowed_values)
        if value in seen_values:
            raise ValueError(f"{field_name} must not contain duplicates")
        normalized.append(value)
        seen_values.add(value)
    return tuple(normalized)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value, RATIO_QUANTUM)
    if normalized < ZERO_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value, COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_decimal(field_name: str, value: Decimal, quantum: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(quantum)
    if normalized != value:
        raise ValueError(f"{field_name} must align to {quantum}")
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


__all__ = (
    "DEFAULT_RESEARCH_INFORMATION_GAP_PRIORITIZER_CONFIG_VERSION",
    "ResearchInformationGapInput",
    "ResearchInformationGapPrioritizerConfig",
    "ResearchInformationGapPrioritizerReport",
    "ResearchInformationGapRow",
    "build_research_information_gap_prioritizer_report",
    "research_information_gap_prioritizer_payload",
)
