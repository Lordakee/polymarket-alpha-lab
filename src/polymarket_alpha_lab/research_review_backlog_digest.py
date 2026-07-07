"""Pure readonly digest for manual research review backlog pressure."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_REVIEW_BACKLOG_DIGEST_CONFIG_VERSION = (
    "research-review-backlog-digest-v1"
)

RESEARCH_REVIEW_BACKLOG_DIGEST_STATUSES = ("pass", "watch", "block")

_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_QUANT = Decimal("0.000001")
_COUNT_QUANT = Decimal("1.000000")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_STATUS_RANK = {"block": Decimal("0.000000"), "watch": Decimal("1.000000"), "pass": Decimal("2.000000")}
_ROW_REASON_CODES = (
    "review_backlog_pass",
    "review_backlog_watch",
    "review_backlog_block",
    "queue_pressure_pass",
    "queue_pressure_watch",
    "queue_pressure_block",
    "reminder_priority_pass",
    "reminder_priority_watch",
    "reminder_priority_block",
    "team_capacity_pass",
    "team_capacity_watch",
    "team_capacity_block",
    "domain_concentration_pass",
    "domain_concentration_watch",
    "domain_concentration_block",
)
_REPORT_REASON_CODES = (
    "review_backlog_digest_passed",
    "review_backlog_digest_watch_rows",
    "review_backlog_digest_block_rows",
    "review_backlog_digest_empty",
)
_UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "candidate_id",
    "raw_candidate",
    "market_id",
    "market_slug",
    "market_question",
    "source_ref",
    "source_url",
    "source_text",
    "url",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
)
_UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "://",
    " wallet",
    "wallet ",
    " auth",
    "auth ",
    " order",
    "order ",
    " trade",
    "trade ",
    " position",
    "position ",
    " buy",
    "buy ",
    " sell",
    "sell ",
    "recommendation",
    " dsn",
    "dsn ",
    " table",
    "table ",
    " token",
    "token ",
)

__all__ = (
    "DEFAULT_RESEARCH_REVIEW_BACKLOG_DIGEST_CONFIG_VERSION",
    "RESEARCH_REVIEW_BACKLOG_DIGEST_STATUSES",
    "ResearchReviewBacklogDigestConfig",
    "ResearchReviewBacklogDigestItem",
    "ResearchReviewBacklogDigestRow",
    "ResearchReviewBacklogDigestReport",
    "build_research_review_backlog_digest",
    "research_review_backlog_digest_payload",
)


@dataclass(frozen=True)
class ResearchReviewBacklogDigestConfig:
    config_version: str = DEFAULT_RESEARCH_REVIEW_BACKLOG_DIGEST_CONFIG_VERSION
    queue_pressure_weight: Decimal = Decimal("0.300000")
    reminder_priority_weight: Decimal = Decimal("0.300000")
    team_capacity_weight: Decimal = Decimal("0.250000")
    domain_concentration_weight: Decimal = Decimal("0.150000")
    queue_pressure_watch_floor: Decimal = Decimal("0.700000")
    queue_pressure_block_floor: Decimal = Decimal("1.000000")
    reminder_priority_watch_floor: Decimal = Decimal("0.300000")
    reminder_priority_block_floor: Decimal = Decimal("0.900000")
    team_capacity_watch_floor: Decimal = Decimal("0.700000")
    team_capacity_block_floor: Decimal = Decimal("1.000000")
    domain_concentration_watch_floor: Decimal = Decimal("0.500000")
    domain_concentration_block_floor: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchReviewBacklogDigestConfig:
            raise ValueError("config must be exactly ResearchReviewBacklogDigestConfig")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        for field_name in (
            "queue_pressure_weight",
            "reminder_priority_weight",
            "team_capacity_weight",
            "domain_concentration_weight",
            "queue_pressure_watch_floor",
            "queue_pressure_block_floor",
            "reminder_priority_watch_floor",
            "reminder_priority_block_floor",
            "team_capacity_watch_floor",
            "team_capacity_block_floor",
            "domain_concentration_watch_floor",
            "domain_concentration_block_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchReviewBacklogDigestItem:
    candidate_id: str
    market_id: str
    market_slug: str
    market_question: str
    source_ref: str
    source_url: str
    source_text: str
    team_id: str
    domain: str
    queue_depth: Decimal
    queue_capacity: Decimal
    reminder_priority: Decimal
    team_available_capacity: Decimal
    team_committed_reviews: Decimal
    domain_backlog_count: Decimal
    total_backlog_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchReviewBacklogDigestItem:
            raise ValueError("item must be exactly ResearchReviewBacklogDigestItem")
        for field_name in (
            "candidate_id",
            "market_id",
            "market_slug",
            "market_question",
            "source_ref",
            "source_url",
            "source_text",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_raw_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "team_id",
            _require_public_identifier("team_id", self.team_id),
        )
        object.__setattr__(
            self,
            "domain",
            _require_public_identifier("domain", self.domain),
        )
        for field_name in (
            "queue_depth",
            "queue_capacity",
            "team_available_capacity",
            "team_committed_reviews",
            "domain_backlog_count",
            "total_backlog_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reminder_priority",
            _require_ratio("reminder_priority", self.reminder_priority),
        )
        if self.queue_capacity <= _ZERO:
            raise ValueError("queue_capacity must be positive")
        if self.domain_backlog_count > self.total_backlog_count:
            raise ValueError("domain_backlog_count must not exceed total_backlog_count")
        _require_hard_flags("item", self)


@dataclass(frozen=True)
class ResearchReviewBacklogDigestRow:
    redacted_candidate_ref: str
    team_id: str
    domain: str
    queue_pressure_ratio: Decimal
    reminder_priority: Decimal
    team_capacity_pressure_ratio: Decimal
    domain_concentration_ratio: Decimal
    review_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    digest_summary: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchReviewBacklogDigestRow:
            raise ValueError("row must be exactly ResearchReviewBacklogDigestRow")
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_redacted_candidate_ref(
                "redacted_candidate_ref",
                self.redacted_candidate_ref,
            ),
        )
        object.__setattr__(
            self,
            "team_id",
            _require_public_identifier("team_id", self.team_id),
        )
        object.__setattr__(
            self,
            "domain",
            _require_public_identifier("domain", self.domain),
        )
        for field_name in (
            "queue_pressure_ratio",
            "reminder_priority",
            "team_capacity_pressure_ratio",
            "domain_concentration_ratio",
            "review_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "status", _require_status("status", self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "digest_summary",
            _require_public_summary("digest_summary", self.digest_summary),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchReviewBacklogDigestReport:
    generated_at: datetime
    config_version: str
    report_status: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_review_pressure_score: Decimal
    top_queue_pressure_ratio: Decimal
    top_reminder_priority: Decimal
    top_team_capacity_pressure_ratio: Decimal
    top_domain_concentration_ratio: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchReviewBacklogDigestRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchReviewBacklogDigestReport:
            raise ValueError("report must be exactly ResearchReviewBacklogDigestReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "report_status",
            _require_status("report_status", self.report_status),
        )
        for field_name in ("item_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_review_pressure_score",
            "top_queue_pressure_ratio",
            "top_reminder_priority",
            "top_team_capacity_pressure_ratio",
            "top_domain_concentration_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_from_values(_values_without_digest(self))
        if self.derived_validation_digest:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report contents")
        object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, object]:
        return research_review_backlog_digest_payload(self)


def build_research_review_backlog_digest(
    items: Sequence[ResearchReviewBacklogDigestItem],
    *,
    generated_at: datetime,
    config: ResearchReviewBacklogDigestConfig | None = None,
) -> ResearchReviewBacklogDigestReport:
    if config is None:
        config = ResearchReviewBacklogDigestConfig()
    if type(config) is not ResearchReviewBacklogDigestConfig:
        raise ValueError("config must be a ResearchReviewBacklogDigestConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_items(items)
    sorted_items = tuple(sorted(normalized_items, key=lambda item: _item_sort_key(item, config)))
    rows = tuple(
        _row_for_item(
            item,
            redacted_candidate_ref=_redacted_candidate_ref(index),
            config=config,
        )
        for index, item in enumerate(sorted_items, start=1)
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "report_status": _report_status(rows),
        "item_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_review_pressure_score": _average_score(rows),
        "top_queue_pressure_ratio": _top_ratio(rows, "queue_pressure_ratio"),
        "top_reminder_priority": _top_ratio(rows, "reminder_priority"),
        "top_team_capacity_pressure_ratio": _top_ratio(
            rows,
            "team_capacity_pressure_ratio",
        ),
        "top_domain_concentration_ratio": _top_ratio(
            rows,
            "domain_concentration_ratio",
        ),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchReviewBacklogDigestReport(
        **values,
        derived_validation_digest=_digest_from_values(values),
    )


def research_review_backlog_digest_payload(
    report: ResearchReviewBacklogDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchReviewBacklogDigestReport:
        _require_hard_flags("report", report)
        payload = _json_ready(asdict(report))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload("payload", payload)
        _require_hard_flags("payload", _DictFlags(payload))
        _validate_payload_digest(payload)
        return payload
    if type(report) is dict:
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload("payload", payload)
        _require_hard_flags("payload", _DictFlags(payload))
        _validate_payload_digest(payload)
        return payload
    raise ValueError("report must be a ResearchReviewBacklogDigestReport or payload")


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


def _row_for_item(
    item: ResearchReviewBacklogDigestItem,
    *,
    redacted_candidate_ref: str,
    config: ResearchReviewBacklogDigestConfig,
) -> ResearchReviewBacklogDigestRow:
    queue_pressure = _queue_pressure_ratio(item)
    team_capacity = _team_capacity_pressure_ratio(item)
    domain_concentration = _domain_concentration_ratio(item)
    score = _review_pressure_score(
        queue_pressure=queue_pressure,
        reminder_priority=item.reminder_priority,
        team_capacity=team_capacity,
        domain_concentration=domain_concentration,
        config=config,
    )
    queue_status = _threshold_status(
        queue_pressure,
        watch_floor=config.queue_pressure_watch_floor,
        block_floor=config.queue_pressure_block_floor,
    )
    reminder_status = _threshold_status(
        item.reminder_priority,
        watch_floor=config.reminder_priority_watch_floor,
        block_floor=config.reminder_priority_block_floor,
    )
    capacity_status = _threshold_status(
        team_capacity,
        watch_floor=config.team_capacity_watch_floor,
        block_floor=config.team_capacity_block_floor,
    )
    domain_status = _threshold_status(
        domain_concentration,
        watch_floor=config.domain_concentration_watch_floor,
        block_floor=config.domain_concentration_block_floor,
    )
    status = _worst_status((queue_status, reminder_status, capacity_status, domain_status))
    return ResearchReviewBacklogDigestRow(
        redacted_candidate_ref=redacted_candidate_ref,
        team_id=item.team_id,
        domain=item.domain,
        queue_pressure_ratio=queue_pressure,
        reminder_priority=item.reminder_priority,
        team_capacity_pressure_ratio=team_capacity,
        domain_concentration_ratio=domain_concentration,
        review_pressure_score=score,
        status=status,
        reason_codes=(
            f"review_backlog_{status}",
            f"queue_pressure_{queue_status}",
            f"reminder_priority_{reminder_status}",
            f"team_capacity_{capacity_status}",
            f"domain_concentration_{domain_status}",
        ),
        digest_summary=_digest_summary(
            status=status,
            queue_status=queue_status,
            reminder_status=reminder_status,
            capacity_status=capacity_status,
            domain_status=domain_status,
            domain_concentration=domain_concentration,
        ),
    )


def _item_sort_key(
    item: ResearchReviewBacklogDigestItem,
    config: ResearchReviewBacklogDigestConfig,
) -> tuple[Decimal, Decimal, str, str, str]:
    queue_pressure = _queue_pressure_ratio(item)
    team_capacity = _team_capacity_pressure_ratio(item)
    domain_concentration = _domain_concentration_ratio(item)
    score = _review_pressure_score(
        queue_pressure=queue_pressure,
        reminder_priority=item.reminder_priority,
        team_capacity=team_capacity,
        domain_concentration=domain_concentration,
        config=config,
    )
    status = _worst_status(
        (
            _threshold_status(
                queue_pressure,
                watch_floor=config.queue_pressure_watch_floor,
                block_floor=config.queue_pressure_block_floor,
            ),
            _threshold_status(
                item.reminder_priority,
                watch_floor=config.reminder_priority_watch_floor,
                block_floor=config.reminder_priority_block_floor,
            ),
            _threshold_status(
                team_capacity,
                watch_floor=config.team_capacity_watch_floor,
                block_floor=config.team_capacity_block_floor,
            ),
            _threshold_status(
                domain_concentration,
                watch_floor=config.domain_concentration_watch_floor,
                block_floor=config.domain_concentration_block_floor,
            ),
        ),
    )
    return (_STATUS_RANK[status], -score, item.team_id, item.domain, item.candidate_id)


def _queue_pressure_ratio(item: ResearchReviewBacklogDigestItem) -> Decimal:
    return _clamp_ratio(_ratio(item.queue_depth, item.queue_capacity))


def _team_capacity_pressure_ratio(item: ResearchReviewBacklogDigestItem) -> Decimal:
    if item.team_available_capacity == _ZERO:
        if item.team_committed_reviews == _ZERO:
            return _ZERO
        return _ONE
    return _clamp_ratio(_ratio(item.team_committed_reviews, item.team_available_capacity))


def _domain_concentration_ratio(item: ResearchReviewBacklogDigestItem) -> Decimal:
    if item.total_backlog_count == _ZERO:
        return _ZERO
    return _clamp_ratio(_ratio(item.domain_backlog_count, item.total_backlog_count))


def _review_pressure_score(
    *,
    queue_pressure: Decimal,
    reminder_priority: Decimal,
    team_capacity: Decimal,
    domain_concentration: Decimal,
    config: ResearchReviewBacklogDigestConfig,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _clamp_ratio(
            queue_pressure * config.queue_pressure_weight
            + reminder_priority * config.reminder_priority_weight
            + team_capacity * config.team_capacity_weight
            + domain_concentration * config.domain_concentration_weight,
        )


def _threshold_status(
    value: Decimal,
    *,
    watch_floor: Decimal,
    block_floor: Decimal,
) -> str:
    if value >= block_floor:
        return "block"
    if value >= watch_floor:
        return "watch"
    return "pass"


def _worst_status(statuses: Sequence[str]) -> str:
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _digest_summary(
    *,
    status: str,
    queue_status: str,
    reminder_status: str,
    capacity_status: str,
    domain_status: str,
    domain_concentration: Decimal,
) -> str:
    return (
        f"{status} review backlog: "
        f"{_queue_phrase(queue_status)}; "
        f"{_reminder_phrase(reminder_status)}; "
        f"{_capacity_phrase(capacity_status)}; "
        f"{_domain_phrase(domain_status, domain_concentration)}"
    )


def _queue_phrase(status: str) -> str:
    if status == "block":
        return "queue saturated"
    if status == "watch":
        return "queue elevated"
    return "queue manageable"


def _reminder_phrase(status: str) -> str:
    if status == "block":
        return "reminder critical"
    if status == "watch":
        return "reminder elevated"
    return "reminder low"


def _capacity_phrase(status: str) -> str:
    if status == "block":
        return "capacity overdrawn"
    if status == "watch":
        return "capacity tightening"
    return "capacity available"


def _domain_phrase(status: str, domain_concentration: Decimal) -> str:
    if status == "block":
        return "domain saturated"
    if domain_concentration >= Decimal("0.750000"):
        return "domain concentrated"
    if status == "watch":
        return "domain clustered"
    return "domain dispersed"


def _report_status(rows: tuple[ResearchReviewBacklogDigestRow, ...]) -> str:
    if not rows:
        return "block"
    return _worst_status(tuple(row.status for row in rows))


def _report_reason_codes(
    rows: tuple[ResearchReviewBacklogDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("review_backlog_digest_empty",)
    codes: list[str] = []
    if any(row.status == "watch" for row in rows):
        codes.append("review_backlog_digest_watch_rows")
    if any(row.status == "block" for row in rows):
        codes.append("review_backlog_digest_block_rows")
    if not codes:
        codes.append("review_backlog_digest_passed")
    return tuple(codes)


def _status_count(rows: tuple[ResearchReviewBacklogDigestRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_score(rows: tuple[ResearchReviewBacklogDigestRow, ...]) -> Decimal:
    if not rows:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _clamp_ratio(
            sum(row.review_pressure_score for row in rows) / Decimal(len(rows)),
        )


def _top_ratio(rows: tuple[ResearchReviewBacklogDigestRow, ...], field_name: str) -> Decimal:
    if not rows:
        return _ZERO
    return max(getattr(row, field_name) for row in rows)


def _normalize_items(
    items: Sequence[ResearchReviewBacklogDigestItem],
) -> tuple[ResearchReviewBacklogDigestItem, ...]:
    if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
        raise ValueError("items must be a sequence")
    normalized: list[ResearchReviewBacklogDigestItem] = []
    seen_candidate_ids: set[str] = set()
    for item in items:
        if type(item) is not ResearchReviewBacklogDigestItem:
            raise ValueError("items must contain ResearchReviewBacklogDigestItem")
        _require_hard_flags("item", item)
        if item.candidate_id in seen_candidate_ids:
            raise ValueError("items must not contain duplicate candidate_id values")
        seen_candidate_ids.add(item.candidate_id)
        normalized.append(item)
    return tuple(normalized)


def _normalize_rows(
    rows: Sequence[ResearchReviewBacklogDigestRow],
) -> tuple[ResearchReviewBacklogDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchReviewBacklogDigestRow] = []
    seen_refs: set[str] = set()
    for row in rows:
        if type(row) is not ResearchReviewBacklogDigestRow:
            raise ValueError("rows must contain ResearchReviewBacklogDigestRow")
        _require_hard_flags("row", row)
        if row.redacted_candidate_ref in seen_refs:
            raise ValueError("rows must not contain duplicate redacted refs")
        seen_refs.add(row.redacted_candidate_ref)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _row_sort_key(row: ResearchReviewBacklogDigestRow) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        _STATUS_RANK[row.status],
        -row.review_pressure_score,
        row.team_id,
        row.domain,
        row.redacted_candidate_ref,
    )


def _validate_config(config: ResearchReviewBacklogDigestConfig) -> None:
    with localcontext(_DECIMAL_CONTEXT):
        weight_total = (
            config.queue_pressure_weight
            + config.reminder_priority_weight
            + config.team_capacity_weight
            + config.domain_concentration_weight
        ).quantize(_QUANT)
    if weight_total != _ONE:
        raise ValueError("digest weights must sum to 1.000000")
    for prefix in (
        "queue_pressure",
        "reminder_priority",
        "team_capacity",
        "domain_concentration",
    ):
        watch_floor = getattr(config, f"{prefix}_watch_floor")
        block_floor = getattr(config, f"{prefix}_block_floor")
        if watch_floor > block_floor:
            raise ValueError(f"{prefix}_watch_floor must not exceed block floor")


def _validate_row(row: ResearchReviewBacklogDigestRow) -> None:
    if f"review_backlog_{row.status}" not in row.reason_codes:
        raise ValueError("row status must match reason_codes")
    if not row.digest_summary.startswith(f"{row.status} review backlog:"):
        raise ValueError("digest_summary must match row status")


def _validate_report(report: ResearchReviewBacklogDigestReport) -> None:
    rows = report.rows
    if report.item_count != _decimal_count(len(rows)):
        raise ValueError("item_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.average_review_pressure_score != _average_score(rows):
        raise ValueError("average_review_pressure_score must match rows")
    if report.top_queue_pressure_ratio != _top_ratio(rows, "queue_pressure_ratio"):
        raise ValueError("top_queue_pressure_ratio must match rows")
    if report.top_reminder_priority != _top_ratio(rows, "reminder_priority"):
        raise ValueError("top_reminder_priority must match rows")
    if report.top_team_capacity_pressure_ratio != _top_ratio(
        rows,
        "team_capacity_pressure_ratio",
    ):
        raise ValueError("top_team_capacity_pressure_ratio must match rows")
    if report.top_domain_concentration_ratio != _top_ratio(
        rows,
        "domain_concentration_ratio",
    ):
        raise ValueError("top_domain_concentration_ratio must match rows")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"{field_name} must be a sequence")
    normalized: list[str] = []
    for item in value:
        if type(item) is not str or item not in _ROW_REASON_CODES:
            raise ValueError(f"{field_name} must contain known reason codes")
        if item not in normalized:
            normalized.append(item)
    return tuple(code for code in _ROW_REASON_CODES if code in normalized)


def _normalize_report_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"{field_name} must be a sequence")
    normalized: list[str] = []
    for item in value:
        if type(item) is not str or item not in _REPORT_REASON_CODES:
            raise ValueError(f"{field_name} must contain known reason codes")
        if item not in normalized:
            normalized.append(item)
    return tuple(code for code in _REPORT_REASON_CODES if code in normalized)


def _require_raw_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_summary(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    normalized = value.strip()
    _reject_unsafe_public_string(field_name, normalized)
    return normalized


def _require_redacted_candidate_ref(field_name: str, value: object) -> str:
    if type(value) is not str or not re.fullmatch(r"<redacted-candidate-[0-9]{3}>", value):
        raise ValueError(f"{field_name} must be redacted")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in RESEARCH_REVIEW_BACKLOG_DIGEST_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized.quantize(_COUNT_QUANT) != normalized:
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _require_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must not exceed 1.000000")
    return normalized


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(_QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return min(_ONE, max(_ZERO, value)).quantize(_QUANT)


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_COUNT_QUANT)


def _redacted_candidate_ref(index: int) -> str:
    return f"<redacted-candidate-{index:03d}>"


def _values_without_digest(report: ResearchReviewBacklogDigestReport) -> dict[str, object]:
    return {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }


def _digest_from_values(values: dict[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a dict")
    _reject_unsafe_public_payload("digest payload", payload)
    return _digest_json_payload(payload)


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    if digest != _digest_json_payload(payload):
        raise ValueError("derived_validation_digest must match report contents")


def _digest_json_payload(payload: dict[str, Any]) -> str:
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    encoded = json.dumps(
        payload_without_digest,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_KEY_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    padded = f" {value.lower()} "
    if any(fragment in padded for fragment in _UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        _reject_unsafe_public_string(path or label, value)
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError(f"{path or label} must use Decimal-derived values")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_key(key, path or label)
            if key in _FLAG_FIELDS and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if type(value) in (list, tuple):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    raise ValueError(f"{path or label} contains unsafe public payload")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) in (int, float):
        raise ValueError("JSON value must use Decimal-derived values")
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")
