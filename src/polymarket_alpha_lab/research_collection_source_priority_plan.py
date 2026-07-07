"""Pure report-only research collection source priority plan."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from decimal import Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_COLLECTION_SOURCE_PRIORITY_PLAN_CONFIG_VERSION = (
    "research-collection-source-priority-plan-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_COVERAGE_GAP_WEIGHT = Decimal("0.350000")
_RELIABILITY_GAP_WEIGHT = Decimal("0.250000")
_FRESHNESS_GAP_WEIGHT = Decimal("0.250000")
_AUDIT_TRAIL_GAP_WEIGHT = Decimal("0.150000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"

STATUSES = ("pass", "watch", "block")
_STATUS_SORT_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
_COLLECTION_PLAN_BY_STATUS = {
    "pass": "report_only_standard_source_monitoring",
    "watch": "report_only_prioritized_source_collection",
    "block": "report_only_hold_until_source_plan",
}
_ROW_PRIORITY_BY_STATUS = {
    "pass": "defer_collection",
    "watch": "prioritize_collection",
    "block": "collect_before_research_use",
}
_REASON_CODE_SEQUENCE = (
    "source_collection_no_inputs",
    "source_collection_status_pass",
    "source_collection_status_watch",
    "source_collection_status_block",
    "coverage_gap_priority",
    "source_reliability_gap",
    "source_freshness_gap",
    "audit_trail_gap",
)
_DETAIL_REASON_CODES = _REASON_CODE_SEQUENCE[4:]
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market_id",
    "market-id",
    "market id",
    "market_slug",
    "market-slug",
    "market slug",
    "slug",
    "question",
    "source_ref",
    "source-ref",
    "source ref",
    "source_url",
    "source-url",
    "source url",
    "source_text",
    "source-text",
    "source text",
    "http://",
    "https://",
    "://",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommend",
    "recommendation",
)

__all__ = (
    "DEFAULT_RESEARCH_COLLECTION_SOURCE_PRIORITY_PLAN_CONFIG_VERSION",
    "ResearchCollectionSourcePriorityPlanConfig",
    "ResearchCollectionSourcePriorityPlanInput",
    "ResearchCollectionSourcePriorityPlanReport",
    "ResearchCollectionSourcePriorityPlanRow",
    "STATUSES",
    "build_research_collection_source_priority_plan",
    "research_collection_source_priority_plan_payload",
)


@dataclass(frozen=True)
class ResearchCollectionSourcePriorityPlanConfig:
    config_version: str = DEFAULT_RESEARCH_COLLECTION_SOURCE_PRIORITY_PLAN_CONFIG_VERSION
    watch_priority_score: Decimal = Decimal("0.250000")
    block_priority_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCollectionSourcePriorityPlanConfig:
            raise TypeError(
                "ResearchCollectionSourcePriorityPlanConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCollectionSourcePriorityPlanConfig:
            raise ValueError(
                "config must be exactly ResearchCollectionSourcePriorityPlanConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_COLLECTION_SOURCE_PRIORITY_PLAN_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("watch_priority_score", "block_priority_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_priority_score >= self.block_priority_score:
            raise ValueError("watch_priority_score must be below block_priority_score")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchCollectionSourcePriorityPlanInput:
    collection_item_ref: str
    source_reliability_score: Decimal
    source_freshness_score: Decimal
    coverage_gap_score: Decimal
    audit_trail_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCollectionSourcePriorityPlanInput:
            raise TypeError(
                "ResearchCollectionSourcePriorityPlanInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCollectionSourcePriorityPlanInput:
            raise ValueError(
                "input must be exactly ResearchCollectionSourcePriorityPlanInput",
            )
        _require_public_identifier("collection_item_ref", self.collection_item_ref)
        _reject_unsafe_public_text("collection_item_ref", self.collection_item_ref)
        for field_name in (
            "source_reliability_score",
            "source_freshness_score",
            "coverage_gap_score",
            "audit_trail_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchCollectionSourcePriorityPlanRow:
    collection_slot_ref: str
    priority_rank: Decimal
    priority_score: Decimal
    source_reliability_score: Decimal
    source_freshness_score: Decimal
    coverage_gap_score: Decimal
    audit_trail_score: Decimal
    source_reliability_gap_score: Decimal
    source_freshness_gap_score: Decimal
    audit_trail_gap_score: Decimal
    status: str
    collection_priority: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCollectionSourcePriorityPlanRow:
            raise TypeError(
                "ResearchCollectionSourcePriorityPlanRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCollectionSourcePriorityPlanRow:
            raise ValueError("row must be exactly ResearchCollectionSourcePriorityPlanRow")
        _require_slot_ref(self.collection_slot_ref)
        object.__setattr__(
            self,
            "priority_rank",
            _require_positive_count_decimal("priority_rank", self.priority_rank),
        )
        for field_name in (
            "priority_score",
            "source_reliability_score",
            "source_freshness_score",
            "coverage_gap_score",
            "audit_trail_score",
            "source_reliability_gap_score",
            "source_freshness_gap_score",
            "audit_trail_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_choice(
            "collection_priority",
            self.collection_priority,
            tuple(_ROW_PRIORITY_BY_STATUS.values()),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchCollectionSourcePriorityPlanReport:
    config_version: str
    status: str
    collection_plan: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    coverage_gap_priority_count: Decimal
    source_reliability_gap_count: Decimal
    source_freshness_gap_count: Decimal
    audit_trail_gap_count: Decimal
    highest_priority_score: Decimal
    rows: tuple[ResearchCollectionSourcePriorityPlanRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCollectionSourcePriorityPlanReport:
            raise TypeError(
                "ResearchCollectionSourcePriorityPlanReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCollectionSourcePriorityPlanReport:
            raise ValueError(
                "report must be exactly ResearchCollectionSourcePriorityPlanReport",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_COLLECTION_SOURCE_PRIORITY_PLAN_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        _require_choice(
            "collection_plan",
            self.collection_plan,
            tuple(_COLLECTION_PLAN_BY_STATUS.values()),
        )
        for field_name in (
            "item_count",
            "pass_count",
            "watch_count",
            "block_count",
            "coverage_gap_priority_count",
            "source_reliability_gap_count",
            "source_freshness_gap_count",
            "audit_trail_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "highest_priority_score",
            _require_ratio_decimal("highest_priority_score", self.highest_priority_score),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, _DERIVED_VALIDATION_DIGEST_FIELD, expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest mismatch")
        _require_digest(_DERIVED_VALIDATION_DIGEST_FIELD, self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, object]:
        return research_collection_source_priority_plan_payload(self)


def build_research_collection_source_priority_plan(
    inputs: Sequence[ResearchCollectionSourcePriorityPlanInput],
    *,
    config: ResearchCollectionSourcePriorityPlanConfig | None = None,
) -> ResearchCollectionSourcePriorityPlanReport:
    """Build a deterministic paper-only source collection priority plan."""

    if config is None:
        config = ResearchCollectionSourcePriorityPlanConfig()
    if type(config) is not ResearchCollectionSourcePriorityPlanConfig:
        raise ValueError(
            "config must be exactly ResearchCollectionSourcePriorityPlanConfig",
        )
    _require_hard_flags("config", config)
    normalized_inputs = _normalize_inputs(inputs)
    unranked_rows = tuple(
        (item.collection_item_ref, _unranked_row(item, config=config))
        for item in normalized_inputs
    )
    ranked_rows = tuple(
        _ranked_row(row, rank=index + 1)
        for index, (_item_ref, row) in enumerate(
            sorted(unranked_rows, key=_unranked_sort_key),
        )
    )
    status = _report_status(ranked_rows)
    return ResearchCollectionSourcePriorityPlanReport(
        config_version=config.config_version,
        status=status,
        collection_plan=_COLLECTION_PLAN_BY_STATUS[status],
        item_count=_decimal_count(len(ranked_rows)),
        pass_count=_status_count(ranked_rows, "pass"),
        watch_count=_status_count(ranked_rows, "watch"),
        block_count=_status_count(ranked_rows, "block"),
        coverage_gap_priority_count=_reason_count(
            ranked_rows,
            "coverage_gap_priority",
        ),
        source_reliability_gap_count=_reason_count(
            ranked_rows,
            "source_reliability_gap",
        ),
        source_freshness_gap_count=_reason_count(
            ranked_rows,
            "source_freshness_gap",
        ),
        audit_trail_gap_count=_reason_count(ranked_rows, "audit_trail_gap"),
        highest_priority_score=_highest_priority_score(ranked_rows),
        rows=ranked_rows,
        reason_codes=_report_reason_codes(ranked_rows),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def research_collection_source_priority_plan_payload(
    report: ResearchCollectionSourcePriorityPlanReport | dict[str, object],
) -> dict[str, object]:
    if type(report) is ResearchCollectionSourcePriorityPlanReport:
        _require_hard_flags("report", report)
        _validate_report(report)
        payload = _report_public_payload_values(report)
        payload[_DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
    elif type(report) is dict:
        payload = _copy_json_object(report)
    else:
        raise ValueError(
            "report must be a ResearchCollectionSourcePriorityPlanReport or dict",
        )
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_public_payload_digest(payload)
    return payload


def _unranked_row(
    item: ResearchCollectionSourcePriorityPlanInput,
    *,
    config: ResearchCollectionSourcePriorityPlanConfig,
) -> ResearchCollectionSourcePriorityPlanRow:
    source_reliability_gap_score = _quantize(_ONE - item.source_reliability_score)
    source_freshness_gap_score = _quantize(_ONE - item.source_freshness_score)
    audit_trail_gap_score = _quantize(_ONE - item.audit_trail_score)
    priority_score = _priority_score(
        coverage_gap_score=item.coverage_gap_score,
        source_reliability_gap_score=source_reliability_gap_score,
        source_freshness_gap_score=source_freshness_gap_score,
        audit_trail_gap_score=audit_trail_gap_score,
    )
    status = _row_status(priority_score, config)
    return ResearchCollectionSourcePriorityPlanRow(
        collection_slot_ref="collection-slot-000001",
        priority_rank=_ONE,
        priority_score=priority_score,
        source_reliability_score=item.source_reliability_score,
        source_freshness_score=item.source_freshness_score,
        coverage_gap_score=item.coverage_gap_score,
        audit_trail_score=item.audit_trail_score,
        source_reliability_gap_score=source_reliability_gap_score,
        source_freshness_gap_score=source_freshness_gap_score,
        audit_trail_gap_score=audit_trail_gap_score,
        status=status,
        collection_priority=_ROW_PRIORITY_BY_STATUS[status],
        reason_codes=_row_reason_codes(
            status=status,
            coverage_gap_score=item.coverage_gap_score,
            source_reliability_gap_score=source_reliability_gap_score,
            source_freshness_gap_score=source_freshness_gap_score,
            audit_trail_gap_score=audit_trail_gap_score,
        ),
    )


def _ranked_row(
    row: ResearchCollectionSourcePriorityPlanRow,
    *,
    rank: int,
) -> ResearchCollectionSourcePriorityPlanRow:
    return replace(
        row,
        collection_slot_ref=f"collection-slot-{rank:06d}",
        priority_rank=_decimal_count(rank),
    )


def _unranked_sort_key(
    item: tuple[str, ResearchCollectionSourcePriorityPlanRow],
) -> tuple[int, Decimal, str]:
    collection_item_ref, row = item
    return (_STATUS_SORT_WEIGHT[row.status], -row.priority_score, collection_item_ref)


def _priority_score(
    *,
    coverage_gap_score: Decimal,
    source_reliability_gap_score: Decimal,
    source_freshness_gap_score: Decimal,
    audit_trail_gap_score: Decimal,
) -> Decimal:
    return _clamp_ratio(
        coverage_gap_score * _COVERAGE_GAP_WEIGHT
        + source_reliability_gap_score * _RELIABILITY_GAP_WEIGHT
        + source_freshness_gap_score * _FRESHNESS_GAP_WEIGHT
        + audit_trail_gap_score * _AUDIT_TRAIL_GAP_WEIGHT,
    )


def _row_status(
    priority_score: Decimal,
    config: ResearchCollectionSourcePriorityPlanConfig,
) -> str:
    if priority_score >= config.block_priority_score:
        return "block"
    if priority_score >= config.watch_priority_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    coverage_gap_score: Decimal,
    source_reliability_gap_score: Decimal,
    source_freshness_gap_score: Decimal,
    audit_trail_gap_score: Decimal,
) -> tuple[str, ...]:
    codes = [f"source_collection_status_{status}"]
    if status == "pass":
        return tuple(codes)
    if coverage_gap_score > _ZERO:
        codes.append("coverage_gap_priority")
    if source_reliability_gap_score > _ZERO:
        codes.append("source_reliability_gap")
    if source_freshness_gap_score > _ZERO:
        codes.append("source_freshness_gap")
    if audit_trail_gap_score > _ZERO:
        codes.append("audit_trail_gap")
    return tuple(code for code in _REASON_CODE_SEQUENCE if code in codes)


def _report_status(
    rows: tuple[ResearchCollectionSourcePriorityPlanRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchCollectionSourcePriorityPlanRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("source_collection_no_inputs",)
    found = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in found)


def _report_public_payload_values(
    report: ResearchCollectionSourcePriorityPlanReport,
) -> dict[str, object]:
    return _json_ready(
        {
            "config_version": report.config_version,
            "status": report.status,
            "collection_plan": report.collection_plan,
            "item_count": report.item_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "coverage_gap_priority_count": report.coverage_gap_priority_count,
            "source_reliability_gap_count": report.source_reliability_gap_count,
            "source_freshness_gap_count": report.source_freshness_gap_count,
            "audit_trail_gap_count": report.audit_trail_gap_count,
            "highest_priority_score": report.highest_priority_score,
            "collection_rows": report.rows,
            "reason_codes": report.reason_codes,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _row_public_payload_values(
    row: ResearchCollectionSourcePriorityPlanRow,
) -> dict[str, object]:
    return {
        "collection_slot_ref": row.collection_slot_ref,
        "priority_rank": row.priority_rank,
        "priority_score": row.priority_score,
        "source_reliability_score": row.source_reliability_score,
        "source_freshness_score": row.source_freshness_score,
        "coverage_gap_score": row.coverage_gap_score,
        "audit_trail_score": row.audit_trail_score,
        "source_reliability_gap_score": row.source_reliability_gap_score,
        "source_freshness_gap_score": row.source_freshness_gap_score,
        "audit_trail_gap_score": row.audit_trail_gap_score,
        "status": row.status,
        "collection_priority": row.collection_priority,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_digest(report: ResearchCollectionSourcePriorityPlanReport) -> str:
    return _digest_payload(_report_public_payload_values(report))


def _digest_payload(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _validate_public_payload_digest(payload: dict[str, object]) -> None:
    _require_hard_flags("payload", _DictFlags(payload))
    digest = payload.get(_DERIVED_VALIDATION_DIGEST_FIELD)
    _require_digest(_DERIVED_VALIDATION_DIGEST_FIELD, digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop(_DERIVED_VALIDATION_DIGEST_FIELD, None)
    if _digest_payload(unsigned_payload) != digest:
        raise ValueError("derived_validation_digest mismatch")


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _normalize_inputs(
    inputs: Sequence[ResearchCollectionSourcePriorityPlanInput],
) -> tuple[ResearchCollectionSourcePriorityPlanInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized: list[ResearchCollectionSourcePriorityPlanInput] = []
    for item in inputs:
        if type(item) is not ResearchCollectionSourcePriorityPlanInput:
            raise ValueError(
                "input must be exactly ResearchCollectionSourcePriorityPlanInput",
            )
        _require_hard_flags("input", item)
        _reject_unsafe_public_payload("input", item)
        normalized.append(item)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[ResearchCollectionSourcePriorityPlanRow, ...],
) -> tuple[ResearchCollectionSourcePriorityPlanRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a tuple")
    normalized: list[ResearchCollectionSourcePriorityPlanRow] = []
    for row in rows:
        if type(row) is not ResearchCollectionSourcePriorityPlanRow:
            raise ValueError("row must be exactly ResearchCollectionSourcePriorityPlanRow")
        _require_hard_flags("row", row)
        _reject_unsafe_public_payload("row", row)
        normalized.append(row)
    return tuple(normalized)


def _validate_row(row: ResearchCollectionSourcePriorityPlanRow) -> None:
    if row.collection_priority != _ROW_PRIORITY_BY_STATUS[row.status]:
        raise ValueError("collection_priority is inconsistent with status")
    status_reason = f"source_collection_status_{row.status}"
    if status_reason not in row.reason_codes:
        raise ValueError("reason_codes must include the row status reason")
    if row.status == "pass" and row.reason_codes != (status_reason,):
        raise ValueError("pass rows must not carry priority gap reasons")


def _validate_report(report: ResearchCollectionSourcePriorityPlanReport) -> None:
    rows = report.rows
    expected_values = {
        "item_count": _decimal_count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "coverage_gap_priority_count": _reason_count(rows, "coverage_gap_priority"),
        "source_reliability_gap_count": _reason_count(rows, "source_reliability_gap"),
        "source_freshness_gap_count": _reason_count(rows, "source_freshness_gap"),
        "audit_trail_gap_count": _reason_count(rows, "audit_trail_gap"),
        "highest_priority_score": _highest_priority_score(rows),
        "status": _report_status(rows),
        "collection_plan": _COLLECTION_PLAN_BY_STATUS[_report_status(rows)],
        "reason_codes": _report_reason_codes(rows),
    }
    for field_name, expected in expected_values.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} is inconsistent with rows")
    for index, row in enumerate(rows, start=1):
        if row.priority_rank != _decimal_count(index):
            raise ValueError("priority_rank must be contiguous")
        if row.collection_slot_ref != f"collection-slot-{index:06d}":
            raise ValueError("collection_slot_ref must be deterministic")


def _status_count(
    rows: tuple[ResearchCollectionSourcePriorityPlanRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[ResearchCollectionSourcePriorityPlanRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _highest_priority_score(
    rows: tuple[ResearchCollectionSourcePriorityPlanRow, ...],
) -> Decimal:
    highest = _ZERO
    for row in rows:
        if row.priority_score > highest:
            highest = row.priority_score
    return highest


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError("reason_codes entries must be strings")
        _require_choice("reason_codes", reason_code, _REASON_CODE_SEQUENCE)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    return tuple(reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in normalized)


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a canonical public identifier")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public value")
    return value


def _require_slot_ref(value: object) -> None:
    _require_public_identifier("collection_slot_ref", value)
    if not str(value).startswith("collection-slot-"):
        raise ValueError("collection_slot_ref must be deterministic")


def _require_status(field_name: str, value: object) -> None:
    _require_choice(field_name, value, STATUSES)


def _require_choice(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value(rounding=ROUND_HALF_UP):
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < _ZERO:
        return _ZERO
    if value > _ONE:
        return _ONE
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.rounding = ROUND_HALF_UP
        return value.quantize(_QUANT)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if type(value) is ResearchCollectionSourcePriorityPlanRow:
        return _json_ready(_row_public_payload_values(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON value must use Decimal-derived strings")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    ready = _json_ready(value)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    decoded = json.loads(encoded)
    if type(decoded) is not dict:
        raise ValueError("payload must be a JSON object")
    return decoded


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if dataclass_is_instance(value):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=allow_json_containers,
        )
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if allow_json_containers and (
        value is None
        or type(value) in (bool, int, float)
    ):
        if isinstance(value, float) or type(value) is int:
            raise ValueError("public payload numerics must be Decimal-derived strings")
        return


def dataclass_is_instance(value: object) -> bool:
    return hasattr(value, "__dataclass_fields__") and not isinstance(value, type)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"unsafe public value in {label}")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.casefold()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value
