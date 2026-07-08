"""Deterministic report-only backlog for external research collection needs.

The module only normalizes caller-supplied collection needs into a public
backlog report. It does not fetch pages, call services, write files, execute
collection tooling, or expose private candidate/source identifiers.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from typing import Any


__all__ = (
    "ResearchExternalInformationCollectionBacklogConfig",
    "ResearchExternalInformationCollectionBacklogNeed",
    "ResearchExternalInformationCollectionBacklogReasonCodeCount",
    "ResearchExternalInformationCollectionBacklogReport",
    "ResearchExternalInformationCollectionBacklogRow",
    "build_research_external_information_collection_backlog_report",
    "research_external_information_collection_backlog_digest",
    "research_external_information_collection_backlog_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-external-information-collection-backlog-v0"
STATUSES = ("pass", "watch", "block")
COLLECTION_AREAS = (
    "data_availability",
    "event_status",
    "official_results",
    "resolution_rules",
    "source_discovery",
)
COLLECTION_TOOLS = ("agent_reach", "manual_review", "scrapling")
NEXT_STEPS = (
    "do_not_collect",
    "queue_public_collection",
    "route_to_manual_review",
)
REASON_CODES = (
    "automation_ready",
    "collection_backlog_block",
    "collection_backlog_pass",
    "collection_backlog_watch",
    "elevated_public_safety_risk",
    "execution_surface_required",
    "human_review_required",
    "low_automation_fit",
    "no_collection_needs",
    "private_access_required",
)
HARD_BLOCK_REASON_CODES = (
    "execution_surface_required",
    "private_access_required",
)
REPORT_REASON_PRIORITY = REASON_CODES
ZERO = Decimal("0")
ONE = Decimal("1")
COUNT_QUANTUM = Decimal("1")
SCORE_QUANTUM = Decimal("0.000001")


@dataclass(frozen=True)
class ResearchExternalInformationCollectionBacklogConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_backlog_score: Decimal = Decimal("0.700000")
    watch_automation_fit_score: Decimal = Decimal("0.400000")
    watch_public_safety_risk_score: Decimal = Decimal("0.300000")
    block_public_safety_risk_score: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchExternalInformationCollectionBacklogConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchExternalInformationCollectionBacklogConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_backlog_score",
            "watch_automation_fit_score",
            "watch_public_safety_risk_score",
            "block_public_safety_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_public_safety_risk_score < self.watch_public_safety_risk_score:
            raise ValueError(
                "block_public_safety_risk_score must be at least the watch threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchExternalInformationCollectionBacklogNeed:
    private_request_key: str
    collection_area: str
    collection_tool: str
    information_need: str
    urgency_score: Decimal
    automation_fit_score: Decimal
    public_safety_risk_score: Decimal
    requires_human_review: bool = False
    hard_block_reasons: tuple[str, ...] = ()
    upstream_reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchExternalInformationCollectionBacklogNeed does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_private_key("private_request_key", self.private_request_key)
        _require_member("collection_area", self.collection_area, COLLECTION_AREAS)
        _require_member("collection_tool", self.collection_tool, COLLECTION_TOOLS)
        _require_public_string("information_need", self.information_need)
        for field_name in (
            "urgency_score",
            "automation_fit_score",
            "public_safety_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.requires_human_review) is not bool:
            raise ValueError("requires_human_review must be a bool")
        object.__setattr__(
            self,
            "hard_block_reasons",
            _normalize_reason_codes(
                "hard_block_reasons",
                self.hard_block_reasons,
                allowed=HARD_BLOCK_REASON_CODES,
                allow_empty=True,
            ),
        )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_open_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        _require_hard_flags("need", self)


@dataclass(frozen=True)
class ResearchExternalInformationCollectionBacklogRow:
    public_request_ref: str
    collection_area: str
    collection_tool: str
    information_need: str
    urgency_score: Decimal
    automation_fit_score: Decimal
    public_safety_risk_score: Decimal
    backlog_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    next_step: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchExternalInformationCollectionBacklogRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_public_ref("public_request_ref", self.public_request_ref)
        _require_member("collection_area", self.collection_area, COLLECTION_AREAS)
        _require_member("collection_tool", self.collection_tool, COLLECTION_TOOLS)
        _require_public_string("information_need", self.information_need)
        for field_name in (
            "urgency_score",
            "automation_fit_score",
            "public_safety_risk_score",
            "backlog_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=REASON_CODES,
                allow_empty=False,
            ),
        )
        _require_member("next_step", self.next_step, NEXT_STEPS)
        _require_hard_flags("row", self)
        _validate_row_consistency(self)
        _reject_unsafe_public_payload("row", _payload_value(self))


@dataclass(frozen=True)
class ResearchExternalInformationCollectionBacklogReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchExternalInformationCollectionBacklogReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_probability_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchExternalInformationCollectionBacklogReport:
    generated_at: datetime
    config_version: str
    request_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_backlog_score: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchExternalInformationCollectionBacklogReasonCodeCount, ...]
    rows: tuple[ResearchExternalInformationCollectionBacklogRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchExternalInformationCollectionBacklogReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "request_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_backlog_score",
            _require_optional_probability_decimal(
                "average_backlog_score",
                self.average_backlog_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allowed=REASON_CODES,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", _payload_value(self))


def build_research_external_information_collection_backlog_report(
    needs: Iterable[object],
    *,
    config: ResearchExternalInformationCollectionBacklogConfig,
    generated_at: datetime,
) -> ResearchExternalInformationCollectionBacklogReport:
    if type(config) is not ResearchExternalInformationCollectionBacklogConfig:
        raise ValueError(
            "config must be a ResearchExternalInformationCollectionBacklogConfig",
        )
    _require_hard_flags("config", config)
    rows = _build_rows(_normalize_needs(needs), config=config)
    reason_codes = _report_reason_codes(rows)

    return ResearchExternalInformationCollectionBacklogReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        request_count=_count(len(rows)),
        pass_count=_count(_status_count(rows, "pass")),
        watch_count=_count(_status_count(rows, "watch")),
        block_count=_count(_status_count(rows, "block")),
        average_backlog_score=_average_score(row.backlog_score for row in rows),
        status=_report_status(rows),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        rows=rows,
    )


def research_external_information_collection_backlog_report_payload(
    report: ResearchExternalInformationCollectionBacklogReport,
) -> dict[str, Any]:
    if type(report) is not ResearchExternalInformationCollectionBacklogReport:
        raise ValueError(
            "report must be a ResearchExternalInformationCollectionBacklogReport",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    payload["digest"] = research_external_information_collection_backlog_digest(report)
    _reject_unsafe_public_payload("report payload", payload)
    return payload


def research_external_information_collection_backlog_digest(
    report: ResearchExternalInformationCollectionBacklogReport,
) -> dict[str, Any]:
    if type(report) is not ResearchExternalInformationCollectionBacklogReport:
        raise ValueError(
            "report must be a ResearchExternalInformationCollectionBacklogReport",
        )
    _require_hard_flags("report", report)
    digest = {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "status": report.status,
        "request_count": format(report.request_count, "f"),
        "pass_count": format(report.pass_count, "f"),
        "watch_count": format(report.watch_count, "f"),
        "block_count": format(report.block_count, "f"),
        "average_backlog_score": (
            None
            if report.average_backlog_score is None
            else format(report.average_backlog_score, "f")
        ),
        "reason_codes": list(report.reason_codes),
        "priority_items": [
            {
                "public_request_ref": row.public_request_ref,
                "status": row.status,
                "collection_area": row.collection_area,
                "collection_tool": row.collection_tool,
                "backlog_score": format(row.backlog_score, "f"),
                "next_step": row.next_step,
                "reason_codes": list(row.reason_codes),
            }
            for row in report.rows
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    _reject_unsafe_public_payload("digest", digest)
    return digest


def _build_rows(
    needs: tuple[ResearchExternalInformationCollectionBacklogNeed, ...],
    *,
    config: ResearchExternalInformationCollectionBacklogConfig,
) -> tuple[ResearchExternalInformationCollectionBacklogRow, ...]:
    prepared = tuple(
        sorted(
            (
                _row_parts(need=need, config=config)
                for need in needs
            ),
            key=lambda item: (
                _status_sort_value(item[0]),
                item[1].collection_area,
                item[1].collection_tool,
                item[1].information_need,
                item[1].private_request_key,
            ),
        ),
    )
    return tuple(
        ResearchExternalInformationCollectionBacklogRow(
            public_request_ref=f"<collection-{index:03d}>",
            collection_area=need.collection_area,
            collection_tool=need.collection_tool,
            information_need=need.information_need,
            urgency_score=need.urgency_score,
            automation_fit_score=need.automation_fit_score,
            public_safety_risk_score=need.public_safety_risk_score,
            backlog_score=backlog_score,
            status=status,
            reason_codes=reason_codes,
            next_step=_next_step(status),
        )
        for index, (status, need, backlog_score, reason_codes) in enumerate(prepared, start=1)
    )


def _row_parts(
    *,
    need: ResearchExternalInformationCollectionBacklogNeed,
    config: ResearchExternalInformationCollectionBacklogConfig,
) -> tuple[
    str,
    ResearchExternalInformationCollectionBacklogNeed,
    Decimal,
    tuple[str, ...],
]:
    backlog_score = _backlog_score(need)
    status = _need_status(need, backlog_score=backlog_score, config=config)
    reason_codes = _need_reason_codes(
        need,
        status=status,
        backlog_score=backlog_score,
        config=config,
    )
    return status, need, backlog_score, reason_codes


def _normalize_needs(
    needs: Iterable[object],
) -> tuple[ResearchExternalInformationCollectionBacklogNeed, ...]:
    if isinstance(needs, (str, bytes)):
        raise ValueError("needs must be an iterable")
    try:
        values = tuple(needs)
    except TypeError as exc:
        raise ValueError("needs must be an iterable") from exc
    normalized = []
    for value in values:
        if type(value) is not ResearchExternalInformationCollectionBacklogNeed:
            raise ValueError(
                "needs must contain ResearchExternalInformationCollectionBacklogNeed items",
            )
        _require_hard_flags("need", value)
        normalized.append(value)
    return tuple(normalized)


def _backlog_score(need: ResearchExternalInformationCollectionBacklogNeed) -> Decimal:
    safety_readiness = _quantize(ONE - need.public_safety_risk_score)
    with localcontext() as context:
        context.prec = 28
        return _quantize(
            (Decimal("0.450000") * need.urgency_score)
            + (Decimal("0.500000") * need.automation_fit_score)
            + (Decimal("0.050000") * safety_readiness),
        )


def _need_status(
    need: ResearchExternalInformationCollectionBacklogNeed,
    *,
    backlog_score: Decimal,
    config: ResearchExternalInformationCollectionBacklogConfig,
) -> str:
    if need.hard_block_reasons:
        return "block"
    if need.public_safety_risk_score >= config.block_public_safety_risk_score:
        return "block"
    if need.requires_human_review:
        return "watch"
    if need.public_safety_risk_score >= config.watch_public_safety_risk_score:
        return "watch"
    if need.automation_fit_score < config.watch_automation_fit_score:
        return "watch"
    if backlog_score < config.pass_backlog_score:
        return "watch"
    return "pass"


def _need_reason_codes(
    need: ResearchExternalInformationCollectionBacklogNeed,
    *,
    status: str,
    backlog_score: Decimal,
    config: ResearchExternalInformationCollectionBacklogConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = list(need.hard_block_reasons)
    if status == "block":
        reason_codes.append("collection_backlog_block")
    elif status == "pass":
        reason_codes.extend(("automation_ready", "collection_backlog_pass"))
    else:
        reason_codes.append("collection_backlog_watch")
    if need.requires_human_review:
        reason_codes.append("human_review_required")
    if need.public_safety_risk_score >= config.watch_public_safety_risk_score:
        reason_codes.append("elevated_public_safety_risk")
    if need.automation_fit_score < config.watch_automation_fit_score:
        reason_codes.append("low_automation_fit")
    if status == "watch" and backlog_score < config.pass_backlog_score:
        reason_codes.append("low_automation_fit")
    for code in need.upstream_reason_codes:
        if code in REASON_CODES:
            reason_codes.append(code)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes),
        allowed=REASON_CODES,
        allow_empty=False,
    )


def _report_reason_codes(
    rows: tuple[ResearchExternalInformationCollectionBacklogRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_collection_needs",)
    codes = tuple(code for row in rows for code in row.reason_codes)
    return _normalize_reason_codes(
        "reason_codes",
        codes,
        allowed=REPORT_REASON_PRIORITY,
        allow_empty=False,
    )


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchExternalInformationCollectionBacklogRow, ...],
) -> tuple[ResearchExternalInformationCollectionBacklogReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchExternalInformationCollectionBacklogReasonCodeCount(
                reason_code="no_collection_needs",
                count=ONE,
                row_ratio=ONE,
            ),
        )
    counts = Counter(code for row in rows for code in row.reason_codes)
    row_count = Decimal(len(rows))
    return tuple(
        ResearchExternalInformationCollectionBacklogReasonCodeCount(
            reason_code=code,
            count=_count(counts[code]),
            row_ratio=_quantize(Decimal(counts[code]) / row_count),
        )
        for code in reason_codes
    )


def _report_status(rows: tuple[ResearchExternalInformationCollectionBacklogRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    if rows:
        return "pass"
    return "block"


def _status_count(
    rows: tuple[ResearchExternalInformationCollectionBacklogRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _next_step(status: str) -> str:
    if status == "pass":
        return "queue_public_collection"
    if status == "watch":
        return "route_to_manual_review"
    return "do_not_collect"


def _validate_row_consistency(
    row: ResearchExternalInformationCollectionBacklogRow,
) -> None:
    if row.status == "pass":
        if "automation_ready" not in row.reason_codes:
            raise ValueError("reason_codes must match pass status")
        if row.next_step != "queue_public_collection":
            raise ValueError("next_step must match pass status")
        return
    if row.status == "watch":
        if not {
            "collection_backlog_watch",
            "elevated_public_safety_risk",
            "human_review_required",
            "low_automation_fit",
        }.intersection(row.reason_codes):
            raise ValueError("reason_codes must match watch status")
        if row.next_step != "route_to_manual_review":
            raise ValueError("next_step must match watch status")
        return
    if "collection_backlog_block" not in row.reason_codes:
        raise ValueError("reason_codes must match block status")
    if row.next_step != "do_not_collect":
        raise ValueError("next_step must match block status")


def _validate_report_consistency(
    report: ResearchExternalInformationCollectionBacklogReport,
) -> None:
    rows = report.rows
    if report.request_count != _count(len(rows)):
        raise ValueError("request_count must match rows")
    for status, field_name in (
        ("pass", "pass_count"),
        ("watch", "watch_count"),
        ("block", "block_count"),
    ):
        if getattr(report, field_name) != _count(_status_count(rows, status)):
            raise ValueError(f"{field_name} must match rows")
    if report.average_backlog_score != _average_score(row.backlog_score for row in rows):
        raise ValueError("average_backlog_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    expected_counts = _reason_code_counts(report.reason_codes, rows)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(
    rows: Iterable[ResearchExternalInformationCollectionBacklogRow],
) -> tuple[ResearchExternalInformationCollectionBacklogRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchExternalInformationCollectionBacklogRow:
            raise ValueError(
                "rows must contain ResearchExternalInformationCollectionBacklogRow items",
            )
    return tuple(sorted(values, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: Iterable[ResearchExternalInformationCollectionBacklogReasonCodeCount],
) -> tuple[ResearchExternalInformationCollectionBacklogReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for item in items:
        if type(item) is not ResearchExternalInformationCollectionBacklogReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchExternalInformationCollectionBacklogReasonCodeCount items",
            )
    return tuple(
        sorted(
            items,
            key=lambda item: REPORT_REASON_PRIORITY.index(item.reason_code),
        ),
    )


def _row_sort_key(
    row: ResearchExternalInformationCollectionBacklogRow,
) -> tuple[int, str, str, str, str]:
    return (
        _status_sort_value(row.status),
        row.collection_area,
        row.collection_tool,
        row.information_need,
        row.public_request_ref,
    )


def _status_sort_value(status: str) -> int:
    return {"block": 0, "pass": 1, "watch": 2}[status]


def _average_score(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    with localcontext() as context:
        context.prec = 28
        return _quantize(sum(items, ZERO) / Decimal(len(items)))


def _normalize_reason_codes(
    field_name: str,
    values: Iterable[str],
    *,
    allowed: tuple[str, ...],
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of reason codes")
    try:
        codes = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of reason codes") from exc
    if not codes:
        if allow_empty:
            return ()
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        _require_member(field_name, code, allowed)
    return tuple(sorted(set(codes), key=allowed.index))


def _normalize_open_reason_codes(
    field_name: str,
    values: Iterable[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of reason codes")
    try:
        codes = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of reason codes") from exc
    normalized = []
    for code in codes:
        _require_canonical_reason_code(field_name, code)
        normalized.append(code)
    return tuple(sorted(set(normalized)))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_private_key(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip() or "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_public_ref(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if not (value.startswith("<collection-") and value.endswith(">")):
        raise ValueError(f"{field_name} must be a public collection reference")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip() or "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a canonical string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public content")


def _require_canonical_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must contain non-empty strings")
    if value != value.strip() or not value.replace("_", "").isalnum() or value.lower() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public content")


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be one of {members}")


def _require_status(field_name: str, value: object) -> None:
    _require_member(field_name, value, STATUSES)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a nonnegative whole Decimal")
    return normalized.quantize(COUNT_QUANTUM)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative integer")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(SCORE_QUANTUM)


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {
            str(key): _payload_value(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload contains an unsupported value")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{current_path} has unsafe public content")
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError(f"{current_path} must not use native numeric values")
    if type(value) is list:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if _has_unsafe_surface_field(key):
                raise ValueError(f"{current_path}.{key} is an unsafe public field")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{current_path}.{key} must be True")
            _reject_unsafe_public_payload(label, item, f"{current_path}.{key}")
        return
    raise ValueError(f"{current_path} contains an unsupported public payload value")


def _has_unsafe_surface_field(value: str) -> bool:
    normalized = value.lower()
    unsafe_fields = (
        "auth",
        "candidate_id",
        "dsn",
        "market_id",
        "market_slug",
        "market_question",
        "order",
        "position",
        "raw_candidate",
        "source_ref",
        "source_text",
        "source_url",
        "table",
        "token",
        "trade",
        "wallet",
    )
    return any(fragment in normalized for fragment in unsafe_fields)


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    unsafe_fragments = (
        "://",
        "auth",
        "buy ",
        "buying",
        "candidate id",
        "candidate_id",
        "dsn",
        "live trading",
        "market id",
        "market question",
        "market slug",
        "market_id",
        "market_question",
        "market_slug",
        "order",
        "position",
        "raw candidate",
        "raw-candidate",
        "recommend",
        "sell ",
        "selling",
        "source ref",
        "source text",
        "source url",
        "source_ref",
        "source_text",
        "source_url",
        "table",
        "token",
        "trading",
        "wallet",
    )
    return any(fragment in normalized for fragment in unsafe_fragments)
