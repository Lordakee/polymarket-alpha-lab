"""Pure readonly research evidence refresh backlog report."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any, Iterable


DEFAULT_RESEARCH_EVIDENCE_REFRESH_BACKLOG_CONFIG_VERSION = (
    "research-evidence-refresh-backlog-v0"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

PUBLIC_STATUSES = frozenset(("pass", "watch", "block"))
NEXT_REFRESH_ACTIONS = frozenset(
    (
        "escalate_refresh_review",
        "fill_collection_gap",
        "fill_coverage_gap",
        "no_refresh_needed",
        "refresh_evidence",
        "route_to_research_owner",
    ),
)
ROW_REASON_CODE_PRIORITY = (
    "evidence_refresh_due",
    "collection_gap_blocking",
    "collection_gap_high",
    "coverage_gap_blocking",
    "coverage_gap_high",
    "team_sla_breached",
    "team_sla_pressure",
    "refresh_backlog_pass",
)
REPORT_REASON_CODE_PRIORITY = (
    "refresh_backlog_block_present",
    "refresh_backlog_watch_present",
    "refresh_backlog_pass_present",
    "evidence_refresh_due",
    "collection_gap_blocking",
    "collection_gap_high",
    "coverage_gap_blocking",
    "coverage_gap_high",
    "team_sla_breached",
    "team_sla_pressure",
)
REASON_CODE_SET = frozenset(ROW_REASON_CODE_PRIORITY + REPORT_REASON_CODE_PRIORITY)

PUBLIC_PAYLOAD_KEYS = frozenset(
    (
        "config_version",
        "status",
        "input_count",
        "pass_count",
        "watch_count",
        "block_count",
        "highest_priority_score",
        "rows",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
PUBLIC_ROW_KEYS = frozenset(
    (
        "redacted_refresh_id",
        "status",
        "priority_score",
        "refresh_rank",
        "refresh_signal_score",
        "collection_gap_score",
        "coverage_gap_score",
        "team_sla_pressure_score",
        "next_refresh_action",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = frozenset(
    (
        "://",
        "api_key",
        "auth",
        "buy",
        "candidate_id",
        "candidate_reference",
        "database",
        "dsn",
        "execute",
        "http",
        "market_id",
        "market_question",
        "market_reference",
        "market_slug",
        "order",
        "position",
        "private_key",
        "question",
        "raw-candidate",
        "raw-market",
        "recommend",
        "sell",
        "slug",
        "source_ref",
        "source_reference",
        "source_text",
        "source_url",
        "sql",
        "table",
        "token",
        "trade",
        "url",
        "wallet",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_EVIDENCE_REFRESH_BACKLOG_CONFIG_VERSION",
    "ResearchEvidenceRefreshBacklogConfig",
    "ResearchEvidenceRefreshBacklogItem",
    "ResearchEvidenceRefreshBacklogReport",
    "ResearchEvidenceRefreshBacklogRow",
    "build_research_evidence_refresh_backlog_report",
    "research_evidence_refresh_backlog_report_payload",
)


@dataclass(frozen=True)
class ResearchEvidenceRefreshBacklogConfig:
    config_version: str = DEFAULT_RESEARCH_EVIDENCE_REFRESH_BACKLOG_CONFIG_VERSION
    source_refresh_weight: Decimal = Decimal("0.200000")
    collection_gap_weight: Decimal = Decimal("0.300000")
    coverage_gap_weight: Decimal = Decimal("0.300000")
    team_sla_weight: Decimal = Decimal("0.200000")
    source_refresh_due_score: Decimal = Decimal("0.750000")
    high_collection_gap_score: Decimal = Decimal("0.700000")
    blocking_collection_gap_score: Decimal = Decimal("0.900000")
    high_coverage_gap_score: Decimal = Decimal("0.700000")
    blocking_coverage_gap_score: Decimal = Decimal("0.900000")
    team_sla_pressure_ratio: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEvidenceRefreshBacklogConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchEvidenceRefreshBacklogConfig)
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_EVIDENCE_REFRESH_BACKLOG_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        for field_name in (
            "source_refresh_weight",
            "collection_gap_weight",
            "coverage_gap_weight",
            "team_sla_weight",
            "source_refresh_due_score",
            "high_collection_gap_score",
            "blocking_collection_gap_score",
            "high_coverage_gap_score",
            "blocking_coverage_gap_score",
            "team_sla_pressure_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchEvidenceRefreshBacklogItem:
    candidate_id: str
    market_id: str
    market_slug: str
    market_question: str
    source_ref: str
    source_url: str
    source_text: str
    source_refresh_score: Decimal
    collection_gap_score: Decimal
    coverage_gap_score: Decimal
    team_sla_elapsed_hours: Decimal
    team_sla_limit_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEvidenceRefreshBacklogItem does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("item", self, ResearchEvidenceRefreshBacklogItem)
        for field_name in (
            "candidate_id",
            "market_id",
            "market_slug",
            "market_question",
            "source_ref",
            "source_url",
            "source_text",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "source_refresh_score",
            "collection_gap_score",
            "coverage_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "team_sla_elapsed_hours",
            _require_nonnegative_decimal(
                "team_sla_elapsed_hours",
                self.team_sla_elapsed_hours,
            ),
        )
        object.__setattr__(
            self,
            "team_sla_limit_hours",
            _require_positive_decimal(
                "team_sla_limit_hours",
                self.team_sla_limit_hours,
            ),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchEvidenceRefreshBacklogRow:
    redacted_refresh_id: str
    status: str
    priority_score: Decimal
    refresh_rank: Decimal
    refresh_signal_score: Decimal
    collection_gap_score: Decimal
    coverage_gap_score: Decimal
    team_sla_pressure_score: Decimal
    next_refresh_action: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEvidenceRefreshBacklogRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchEvidenceRefreshBacklogRow)
        _require_canonical_string("redacted_refresh_id", self.redacted_refresh_id)
        _require_status("status", self.status)
        for field_name in (
            "priority_score",
            "refresh_signal_score",
            "collection_gap_score",
            "coverage_gap_score",
            "team_sla_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "refresh_rank",
            _require_positive_count("refresh_rank", self.refresh_rank),
        )
        _require_next_refresh_action("next_refresh_action", self.next_refresh_action)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                priority=ROW_REASON_CODE_PRIORITY,
                require_nonempty=True,
            ),
        )
        _validate_row(self)
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchEvidenceRefreshBacklogReport:
    config_version: str
    status: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    highest_priority_score: Decimal
    rows: tuple[ResearchEvidenceRefreshBacklogRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEvidenceRefreshBacklogReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchEvidenceRefreshBacklogReport)
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_EVIDENCE_REFRESH_BACKLOG_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        _require_status("status", self.status)
        for field_name in (
            "input_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "highest_priority_score",
            _require_ratio("highest_priority_score", self.highest_priority_score),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                self.reason_codes,
                priority=REPORT_REASON_CODE_PRIORITY,
                require_nonempty=True,
            ),
        )
        _validate_report(self)
        _require_hard_flags(self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report payload")
        _require_digest("derived_validation_digest", self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_evidence_refresh_backlog_report_payload(self)


def build_research_evidence_refresh_backlog_report(
    items: Iterable[ResearchEvidenceRefreshBacklogItem],
    *,
    config: ResearchEvidenceRefreshBacklogConfig,
) -> ResearchEvidenceRefreshBacklogReport:
    """Build a deterministic public refresh backlog for research review only."""

    if type(config) is not ResearchEvidenceRefreshBacklogConfig:
        raise ValueError("config must be ResearchEvidenceRefreshBacklogConfig")
    _require_hard_flags(config)
    source_items = _normalize_items(items)
    ranked_rows = _ranked_rows(
        tuple(_unranked_row(item, config=config) for item in source_items),
    )
    return ResearchEvidenceRefreshBacklogReport(
        config_version=config.config_version,
        status=_report_status(ranked_rows),
        input_count=_count_decimal(len(source_items)),
        pass_count=_count_decimal(sum(1 for row in ranked_rows if row.status == "pass")),
        watch_count=_count_decimal(
            sum(1 for row in ranked_rows if row.status == "watch"),
        ),
        block_count=_count_decimal(
            sum(1 for row in ranked_rows if row.status == "block"),
        ),
        highest_priority_score=ranked_rows[0].priority_score if ranked_rows else ZERO,
        rows=ranked_rows,
        reason_codes=_combined_report_reason_codes(ranked_rows),
    )


def research_evidence_refresh_backlog_report_payload(
    report: ResearchEvidenceRefreshBacklogReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEvidenceRefreshBacklogReport:
        return _report_payload(report, include_digest=True)
    if type(report) is dict:
        return _validated_public_payload(report)
    raise ValueError("report must be ResearchEvidenceRefreshBacklogReport")


def _unranked_row(
    item: ResearchEvidenceRefreshBacklogItem,
    *,
    config: ResearchEvidenceRefreshBacklogConfig,
) -> ResearchEvidenceRefreshBacklogRow:
    team_sla_pressure_score = _team_sla_pressure(item)
    reason_codes = _item_reason_codes(
        item,
        team_sla_pressure_score=team_sla_pressure_score,
        config=config,
    )
    return ResearchEvidenceRefreshBacklogRow(
        redacted_refresh_id=_redacted_refresh_id(item),
        status=_row_status(reason_codes),
        priority_score=_priority_score(
            item,
            team_sla_pressure_score=team_sla_pressure_score,
            config=config,
        ),
        refresh_rank=ONE,
        refresh_signal_score=item.source_refresh_score,
        collection_gap_score=item.collection_gap_score,
        coverage_gap_score=item.coverage_gap_score,
        team_sla_pressure_score=team_sla_pressure_score,
        next_refresh_action=_next_refresh_action(reason_codes),
        reason_codes=reason_codes,
    )


def _priority_score(
    item: ResearchEvidenceRefreshBacklogItem,
    *,
    team_sla_pressure_score: Decimal,
    config: ResearchEvidenceRefreshBacklogConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            config.source_refresh_weight * item.source_refresh_score
            + config.collection_gap_weight * item.collection_gap_score
            + config.coverage_gap_weight * item.coverage_gap_score
            + config.team_sla_weight * team_sla_pressure_score
        )
    return _quantize_ratio("priority_score", _clamp_ratio(score))


def _team_sla_pressure(item: ResearchEvidenceRefreshBacklogItem) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(item.team_sla_elapsed_hours / item.team_sla_limit_hours)


def _item_reason_codes(
    item: ResearchEvidenceRefreshBacklogItem,
    *,
    team_sla_pressure_score: Decimal,
    config: ResearchEvidenceRefreshBacklogConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.source_refresh_score >= config.source_refresh_due_score:
        reason_codes.append("evidence_refresh_due")
    if item.collection_gap_score >= config.blocking_collection_gap_score:
        reason_codes.append("collection_gap_blocking")
    if item.collection_gap_score >= config.high_collection_gap_score:
        reason_codes.append("collection_gap_high")
    if item.coverage_gap_score >= config.blocking_coverage_gap_score:
        reason_codes.append("coverage_gap_blocking")
    if item.coverage_gap_score >= config.high_coverage_gap_score:
        reason_codes.append("coverage_gap_high")
    if team_sla_pressure_score >= ONE:
        reason_codes.append("team_sla_breached")
    elif team_sla_pressure_score >= config.team_sla_pressure_ratio:
        reason_codes.append("team_sla_pressure")
    if not reason_codes:
        reason_codes.append("refresh_backlog_pass")
    return _normalize_reason_codes(
        tuple(reason_codes),
        priority=ROW_REASON_CODE_PRIORITY,
        require_nonempty=True,
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code
        in {
            "collection_gap_blocking",
            "coverage_gap_blocking",
            "team_sla_breached",
        }
        for reason_code in reason_codes
    ):
        return "block"
    if reason_codes == ("refresh_backlog_pass",):
        return "pass"
    return "watch"


def _next_refresh_action(reason_codes: tuple[str, ...]) -> str:
    if (
        "collection_gap_blocking" in reason_codes
        or "coverage_gap_blocking" in reason_codes
        or "team_sla_breached" in reason_codes
    ):
        return "escalate_refresh_review"
    if "collection_gap_high" in reason_codes:
        return "fill_collection_gap"
    if "coverage_gap_high" in reason_codes:
        return "fill_coverage_gap"
    if "evidence_refresh_due" in reason_codes:
        return "refresh_evidence"
    if "team_sla_pressure" in reason_codes:
        return "route_to_research_owner"
    return "no_refresh_needed"


def _ranked_rows(
    rows: tuple[ResearchEvidenceRefreshBacklogRow, ...],
) -> tuple[ResearchEvidenceRefreshBacklogRow, ...]:
    return tuple(
        ResearchEvidenceRefreshBacklogRow(
            redacted_refresh_id=row.redacted_refresh_id,
            status=row.status,
            priority_score=row.priority_score,
            refresh_rank=_count_decimal(index),
            refresh_signal_score=row.refresh_signal_score,
            collection_gap_score=row.collection_gap_score,
            coverage_gap_score=row.coverage_gap_score,
            team_sla_pressure_score=row.team_sla_pressure_score,
            next_refresh_action=row.next_refresh_action,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted(rows, key=_row_sort_key), start=1)
    )


def _row_sort_key(row: ResearchEvidenceRefreshBacklogRow) -> tuple[Decimal, str]:
    return (-row.priority_score, row.redacted_refresh_id)


def _combined_report_reason_codes(
    rows: tuple[ResearchEvidenceRefreshBacklogRow, ...],
) -> tuple[str, ...]:
    found = {reason_code for row in rows for reason_code in row.reason_codes}
    status_found = {row.status for row in rows}
    report_codes: list[str] = []
    if "block" in status_found:
        report_codes.append("refresh_backlog_block_present")
    if "watch" in status_found:
        report_codes.append("refresh_backlog_watch_present")
    if "pass" in status_found or not rows:
        report_codes.append("refresh_backlog_pass_present")
    for reason_code in REPORT_REASON_CODE_PRIORITY:
        if (
            reason_code not in report_codes
            and reason_code in found
            and reason_code != "refresh_backlog_pass"
        ):
            report_codes.append(reason_code)
    return _normalize_reason_codes(
        tuple(report_codes),
        priority=REPORT_REASON_CODE_PRIORITY,
        require_nonempty=True,
    )


def _report_status(rows: tuple[ResearchEvidenceRefreshBacklogRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _normalize_items(
    items: Iterable[ResearchEvidenceRefreshBacklogItem],
) -> tuple[ResearchEvidenceRefreshBacklogItem, ...]:
    normalized = tuple(items)
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchEvidenceRefreshBacklogItem:
            raise ValueError("items must contain ResearchEvidenceRefreshBacklogItem")
        _require_hard_flags(item)
        redacted_refresh_id = _redacted_refresh_id(item)
        if redacted_refresh_id in seen:
            raise ValueError("items must not contain duplicate redacted refresh ids")
        seen.add(redacted_refresh_id)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchEvidenceRefreshBacklogRow, ...],
) -> tuple[ResearchEvidenceRefreshBacklogRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized: list[ResearchEvidenceRefreshBacklogRow] = []
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchEvidenceRefreshBacklogRow:
            raise ValueError("rows must contain ResearchEvidenceRefreshBacklogRow")
        _require_hard_flags(row)
        if row.redacted_refresh_id in seen:
            raise ValueError("rows must not contain duplicate redacted_refresh_id")
        seen.add(row.redacted_refresh_id)
        normalized.append(row)
    return tuple(normalized)


def _validate_config(config: ResearchEvidenceRefreshBacklogConfig) -> None:
    with localcontext(DECIMAL_CONTEXT):
        total_weight = (
            config.source_refresh_weight
            + config.collection_gap_weight
            + config.coverage_gap_weight
            + config.team_sla_weight
        )
    if total_weight != ONE:
        raise ValueError("priority weights must sum to 1.000000")
    if config.high_collection_gap_score > config.blocking_collection_gap_score:
        raise ValueError(
            "high_collection_gap_score must be <= blocking_collection_gap_score",
        )
    if config.high_coverage_gap_score > config.blocking_coverage_gap_score:
        raise ValueError(
            "high_coverage_gap_score must be <= blocking_coverage_gap_score",
        )


def _validate_row(row: ResearchEvidenceRefreshBacklogRow) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.next_refresh_action != _next_refresh_action(row.reason_codes):
        raise ValueError("next_refresh_action must match reason_codes")
    if row.status == "pass" and row.reason_codes != ("refresh_backlog_pass",):
        raise ValueError("pass rows must use refresh_backlog_pass only")
    if row.status != "pass" and row.reason_codes == ("refresh_backlog_pass",):
        raise ValueError("non-pass rows must not use refresh_backlog_pass")


def _validate_report(report: ResearchEvidenceRefreshBacklogReport) -> None:
    expected_pass_count = _count_decimal(sum(1 for row in report.rows if row.status == "pass"))
    expected_watch_count = _count_decimal(
        sum(1 for row in report.rows if row.status == "watch"),
    )
    expected_block_count = _count_decimal(
        sum(1 for row in report.rows if row.status == "block"),
    )
    if report.pass_count != expected_pass_count:
        raise ValueError("pass_count must match rows")
    if report.watch_count != expected_watch_count:
        raise ValueError("watch_count must match rows")
    if report.block_count != expected_block_count:
        raise ValueError("block_count must match rows")
    if report.input_count != _count_decimal(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    sorted_rows = tuple(sorted(report.rows, key=_row_sort_key))
    for index, row in enumerate(report.rows, start=1):
        if row != sorted_rows[index - 1] or row.refresh_rank != _count_decimal(index):
            raise ValueError("rows must follow deterministic sequence")
    if report.highest_priority_score != (
        report.rows[0].priority_score if report.rows else ZERO
    ):
        raise ValueError("highest_priority_score must match first row")
    if report.reason_codes != _combined_report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _report_payload(
    report: ResearchEvidenceRefreshBacklogReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    _require_hard_flags(report)
    payload: dict[str, Any] = {
        "config_version": report.config_version,
        "status": report.status,
        "input_count": _decimal_string(report.input_count),
        "pass_count": _decimal_string(report.pass_count),
        "watch_count": _decimal_string(report.watch_count),
        "block_count": _decimal_string(report.block_count),
        "highest_priority_score": _decimal_string(report.highest_priority_score),
        "rows": [
            {
                "redacted_refresh_id": row.redacted_refresh_id,
                "status": row.status,
                "priority_score": _decimal_string(row.priority_score),
                "refresh_rank": _decimal_string(row.refresh_rank),
                "refresh_signal_score": _decimal_string(row.refresh_signal_score),
                "collection_gap_score": _decimal_string(row.collection_gap_score),
                "coverage_gap_score": _decimal_string(row.coverage_gap_score),
                "team_sla_pressure_score": _decimal_string(row.team_sla_pressure_score),
                "next_refresh_action": row.next_refresh_action,
                "reason_codes": list(row.reason_codes),
                "paper_only": row.paper_only,
                "report_only": row.report_only,
                "readonly": row.readonly,
            }
            for row in report.rows
        ],
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    _reject_unsafe_public_payload(payload)
    return payload


def _validated_public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    _reject_unsafe_public_payload(payload)
    _require_public_payload_keys(payload)
    digest = _public_string(
        "derived_validation_digest",
        payload["derived_validation_digest"],
    )
    _require_digest("derived_validation_digest", digest)
    if digest != _public_payload_digest(payload):
        raise ValueError("derived_validation_digest must match report payload")
    if type(payload["rows"]) is not list:
        raise ValueError("rows must be a list")
    rows = tuple(_public_payload_row(row) for row in payload["rows"])
    report = ResearchEvidenceRefreshBacklogReport(
        config_version=_public_string("config_version", payload["config_version"]),
        status=_public_string("status", payload["status"]),
        input_count=_public_decimal("input_count", payload["input_count"]),
        pass_count=_public_decimal("pass_count", payload["pass_count"]),
        watch_count=_public_decimal("watch_count", payload["watch_count"]),
        block_count=_public_decimal("block_count", payload["block_count"]),
        highest_priority_score=_public_decimal(
            "highest_priority_score",
            payload["highest_priority_score"],
        ),
        rows=rows,
        reason_codes=_public_reason_codes(payload["reason_codes"]),
        derived_validation_digest=digest,
        paper_only=_public_true("paper_only", payload["paper_only"]),
        report_only=_public_true("report_only", payload["report_only"]),
        readonly=_public_true("readonly", payload["readonly"]),
    )
    return _report_payload(report, include_digest=True)


def _public_payload_row(payload: object) -> ResearchEvidenceRefreshBacklogRow:
    if type(payload) is not dict:
        raise ValueError("rows must contain dict payloads")
    _require_public_row_keys(payload)
    return ResearchEvidenceRefreshBacklogRow(
        redacted_refresh_id=_public_string(
            "redacted_refresh_id",
            payload["redacted_refresh_id"],
        ),
        status=_public_string("status", payload["status"]),
        priority_score=_public_decimal("priority_score", payload["priority_score"]),
        refresh_rank=_public_decimal("refresh_rank", payload["refresh_rank"]),
        refresh_signal_score=_public_decimal(
            "refresh_signal_score",
            payload["refresh_signal_score"],
        ),
        collection_gap_score=_public_decimal(
            "collection_gap_score",
            payload["collection_gap_score"],
        ),
        coverage_gap_score=_public_decimal(
            "coverage_gap_score",
            payload["coverage_gap_score"],
        ),
        team_sla_pressure_score=_public_decimal(
            "team_sla_pressure_score",
            payload["team_sla_pressure_score"],
        ),
        next_refresh_action=_public_string(
            "next_refresh_action",
            payload["next_refresh_action"],
        ),
        reason_codes=_public_reason_codes(payload["reason_codes"]),
        paper_only=_public_true("paper_only", payload["paper_only"]),
        report_only=_public_true("report_only", payload["report_only"]),
        readonly=_public_true("readonly", payload["readonly"]),
    )


def _require_public_payload_keys(payload: dict[str, Any]) -> None:
    missing = PUBLIC_PAYLOAD_KEYS - payload.keys()
    if missing:
        raise ValueError("public payload is missing required fields")
    extra = payload.keys() - PUBLIC_PAYLOAD_KEYS
    if extra:
        raise ValueError("public payload contains unsupported fields")


def _require_public_row_keys(payload: dict[str, Any]) -> None:
    missing = PUBLIC_ROW_KEYS - payload.keys()
    if missing:
        raise ValueError("row payload is missing required fields")
    extra = payload.keys() - PUBLIC_ROW_KEYS
    if extra:
        raise ValueError("row payload contains unsupported fields")


def _derived_validation_digest(report: ResearchEvidenceRefreshBacklogReport) -> str:
    return _public_payload_digest(_report_payload(report, include_digest=False))


def _public_payload_digest(payload: dict[str, Any]) -> str:
    return sha256(repr(_canonical_payload_value(payload)).encode("utf-8")).hexdigest()


def _canonical_payload_value(value: object) -> object:
    if type(value) is dict:
        return tuple(
            (key, _canonical_payload_value(value[key]))
            for key in sorted(value)
            if key != "derived_validation_digest"
        )
    if type(value) is list:
        return tuple(_canonical_payload_value(item) for item in value)
    if type(value) in {str, bool}:
        return value
    raise ValueError("public payload values must be strings, booleans, lists, or dicts")


def _reject_unsafe_public_payload(value: object) -> None:
    if type(value) is dict:
        for key, nested in value.items():
            _reject_unsafe_public_text(key)
            _reject_unsafe_public_payload(nested)
        return
    if type(value) is list:
        for nested in value:
            _reject_unsafe_public_payload(nested)
        return
    if type(value) is str:
        _reject_unsafe_public_text(value)
        return
    if type(value) is bool:
        return
    raise ValueError("public payload numeric values must be Decimal-derived strings")


def _reject_unsafe_public_text(value: str) -> None:
    normalized = value.lower()
    if any(term in normalized for term in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError("unsafe public payload surface")


def _public_string(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    return value


def _public_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError("public payload numeric values must be Decimal-derived strings")
    try:
        decimal_value = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    normalized = _require_decimal(field_name, decimal_value)
    if _decimal_string(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal-derived string")
    return normalized


def _public_true(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _public_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError("reason_codes must be a list")
    return tuple(_public_string("reason_code", item) for item in value)


def _require_exact_type(field_name: str, value: object, expected_type: type) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    if any(ord(character) < 32 or ord(character) > 126 for character in value):
        raise ValueError(f"{field_name} must be printable ASCII")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a 64-character hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a 64-character hex digest")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(QUANTUM)
    if value != quantized:
        raise ValueError(f"{field_name} must use six decimal places")
    return quantized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return decimal_value


def _quantize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(QUANTUM)
    if quantized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if quantized > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return quantized


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(field_name, value)


def _require_positive_count(field_name: str, value: object) -> Decimal:
    count = _require_nonnegative_count(field_name, value)
    if count <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return count


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    priority: tuple[str, ...],
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in REASON_CODE_SET:
            raise ValueError("reason_codes contains unsupported reason_code")
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    if require_nonempty and not normalized:
        raise ValueError("reason_codes must not be empty")
    expected = tuple(reason_code for reason_code in priority if reason_code in seen)
    if tuple(normalized) != expected:
        raise ValueError("reason_codes must follow deterministic order")
    return tuple(normalized)


def _require_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} is unsupported")


def _require_next_refresh_action(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in NEXT_REFRESH_ACTIONS:
        raise ValueError(f"{field_name} is unsupported")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _redacted_refresh_id(item: ResearchEvidenceRefreshBacklogItem) -> str:
    raw_value = "\x1f".join(
        (
            item.candidate_id,
            item.market_id,
            item.market_slug,
            item.market_question,
            item.source_ref,
            item.source_url,
            item.source_text,
        ),
    )
    return f"refresh_{sha256(raw_value.encode('utf-8')).hexdigest()[:16]}"


def _decimal_string(value: Decimal) -> str:
    return format(value, "f")
