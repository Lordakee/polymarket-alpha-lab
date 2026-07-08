"""Deterministic report-only market resolution evidence review queue."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_MARKET_RESOLUTION_EVIDENCE_QUEUE_REPORT_CONFIG_VERSION = (
    "research-market-resolution-evidence-queue-report-v1"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_TWO = Decimal("2.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_STATUSES = frozenset(("pass", "watch", "block"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TERMS = (
    "raw_candidate_id",
    "rawcandidate",
    "candidate_id",
    "market_id",
    "market_slug",
    "market_question",
    "question",
    "source_ref",
    "source_url",
    "source_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommend",
    "auth",
    "live",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
)
_REASON_CODE_SEQUENCE = (
    "empty_review_queue",
    "parsed_rules_missing",
    "parsed_rules_present",
    "result_evidence_missing",
    "result_evidence_present",
    "conflict_evidence_present",
    "no_conflict_evidence",
    "hard_block_flag",
    "hard_watch_flag",
    "resolution_evidence_score_block",
    "resolution_evidence_score_watch",
    "resolution_evidence_score_pass",
    "human_review_required",
    "human_review_not_required",
)
_STATUS_ORDER = {"block": 0, "watch": 1, "pass": 2}


@dataclass(frozen=True)
class ResearchMarketResolutionEvidenceQueueConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_RESOLUTION_EVIDENCE_QUEUE_REPORT_CONFIG_VERSION
    )
    pass_resolution_evidence_score: Decimal = Decimal("0.700000")
    watch_resolution_evidence_score: Decimal = Decimal("0.400000")
    conflict_block_severity_score: Decimal = Decimal("0.800000")
    hard_watch_priority_boost: Decimal = Decimal("0.250000")
    hard_block_priority_boost: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketResolutionEvidenceQueueConfig:
            raise TypeError(
                "ResearchMarketResolutionEvidenceQueueConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketResolutionEvidenceQueueConfig:
            raise ValueError(
                "config must be exactly ResearchMarketResolutionEvidenceQueueConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_RESOLUTION_EVIDENCE_QUEUE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_resolution_evidence_score",
            "watch_resolution_evidence_score",
            "conflict_block_severity_score",
            "hard_watch_priority_boost",
            "hard_block_priority_boost",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_resolution_evidence_score <= self.watch_resolution_evidence_score:
            raise ValueError(
                "pass_resolution_evidence_score must exceed watch_resolution_evidence_score",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketResolutionEvidenceQueueInput:
    review_key: str
    parsed_rule_count: Decimal
    result_evidence_count: Decimal
    conflict_evidence_count: Decimal
    rule_confidence_score: Decimal
    result_evidence_score: Decimal
    conflict_severity_score: Decimal
    hard_block_flag: bool = False
    hard_watch_flag: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketResolutionEvidenceQueueInput:
            raise TypeError(
                "ResearchMarketResolutionEvidenceQueueInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketResolutionEvidenceQueueInput:
            raise ValueError(
                "input must be exactly ResearchMarketResolutionEvidenceQueueInput",
            )
        _require_public_identifier("review_key", self.review_key)
        for field_name in (
            "parsed_rule_count",
            "result_evidence_count",
            "conflict_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "rule_confidence_score",
            "result_evidence_score",
            "conflict_severity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "hard_block_flag",
            _require_bool("hard_block_flag", self.hard_block_flag),
        )
        object.__setattr__(
            self,
            "hard_watch_flag",
            _require_bool("hard_watch_flag", self.hard_watch_flag),
        )
        if self.hard_block_flag and self.hard_watch_flag:
            raise ValueError("hard_block_flag and hard_watch_flag cannot both be True")
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchMarketResolutionEvidenceQueuePublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketResolutionEvidenceQueuePublicPayloadItem:
            raise TypeError(
                "ResearchMarketResolutionEvidenceQueuePublicPayloadItem does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketResolutionEvidenceQueuePublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchMarketResolutionEvidenceQueuePublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchMarketResolutionEvidenceQueueRow:
    review_key: str
    queue_rank: Decimal
    parsed_rule_count: Decimal
    result_evidence_count: Decimal
    conflict_evidence_count: Decimal
    rule_confidence_score: Decimal
    result_evidence_score: Decimal
    conflict_severity_score: Decimal
    resolution_evidence_score: Decimal
    review_priority_score: Decimal
    hard_block_flag: bool
    hard_watch_flag: bool
    public_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketResolutionEvidenceQueueRow:
            raise TypeError(
                "ResearchMarketResolutionEvidenceQueueRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketResolutionEvidenceQueueRow:
            raise ValueError("row must be exactly ResearchMarketResolutionEvidenceQueueRow")
        _require_public_identifier("review_key", self.review_key)
        object.__setattr__(
            self,
            "queue_rank",
            _require_positive_count_decimal("queue_rank", self.queue_rank),
        )
        for field_name in (
            "parsed_rule_count",
            "result_evidence_count",
            "conflict_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "rule_confidence_score",
            "result_evidence_score",
            "conflict_severity_score",
            "resolution_evidence_score",
            "review_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "hard_block_flag",
            _require_bool("hard_block_flag", self.hard_block_flag),
        )
        object.__setattr__(
            self,
            "hard_watch_flag",
            _require_bool("hard_watch_flag", self.hard_watch_flag),
        )
        if self.hard_block_flag and self.hard_watch_flag:
            raise ValueError("hard_block_flag and hard_watch_flag cannot both be True")
        _require_public_status("public_status", self.public_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketResolutionEvidenceQueueReport:
    generated_at: datetime
    config_version: str
    public_status: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_resolution_evidence_score: Decimal
    max_review_priority_score: Decimal
    rows: tuple[ResearchMarketResolutionEvidenceQueueRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchMarketResolutionEvidenceQueuePublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketResolutionEvidenceQueueReport:
            raise TypeError(
                "ResearchMarketResolutionEvidenceQueueReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketResolutionEvidenceQueueReport:
            raise ValueError(
                "report must be exactly ResearchMarketResolutionEvidenceQueueReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_RESOLUTION_EVIDENCE_QUEUE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_public_status("public_status", self.public_status)
        for field_name in ("item_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_resolution_evidence_score",
            "max_review_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchMarketResolutionEvidenceQueueReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_market_resolution_evidence_queue_report(
    items: Sequence[ResearchMarketResolutionEvidenceQueueInput],
    *,
    generated_at: datetime,
    config: ResearchMarketResolutionEvidenceQueueConfig | None = None,
    public_payload: Sequence[ResearchMarketResolutionEvidenceQueuePublicPayloadItem] = (),
) -> ResearchMarketResolutionEvidenceQueueReport:
    """Build a local, side-effect-free human review queue report."""

    if config is None:
        config = ResearchMarketResolutionEvidenceQueueConfig()
    if type(config) is not ResearchMarketResolutionEvidenceQueueConfig:
        raise ValueError("config must be a ResearchMarketResolutionEvidenceQueueConfig")
    generated_at = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_inputs(items)
    payload_items = _normalize_public_payload(public_payload)
    rows = _rank_rows(
        tuple(_row_from_input(item, config) for item in normalized_items),
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "public_status": _report_status(rows),
        "item_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_resolution_evidence_score": _average(
            tuple(row.resolution_evidence_score for row in rows),
        ),
        "max_review_priority_score": max(
            (row.review_priority_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketResolutionEvidenceQueueReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_market_resolution_evidence_queue_report_payload(
    report: ResearchMarketResolutionEvidenceQueueReport,
) -> dict[str, object]:
    if type(report) is not ResearchMarketResolutionEvidenceQueueReport:
        raise ValueError("report must be a ResearchMarketResolutionEvidenceQueueReport")
    return report.payload


def _row_from_input(
    item: ResearchMarketResolutionEvidenceQueueInput,
    config: ResearchMarketResolutionEvidenceQueueConfig,
) -> ResearchMarketResolutionEvidenceQueueRow:
    score = _resolution_evidence_score(item)
    public_status = _row_status(item, score, config)
    priority_score = _review_priority_score(item, score, config)
    return ResearchMarketResolutionEvidenceQueueRow(
        review_key=item.review_key,
        queue_rank=_ONE,
        parsed_rule_count=item.parsed_rule_count,
        result_evidence_count=item.result_evidence_count,
        conflict_evidence_count=item.conflict_evidence_count,
        rule_confidence_score=item.rule_confidence_score,
        result_evidence_score=item.result_evidence_score,
        conflict_severity_score=item.conflict_severity_score,
        resolution_evidence_score=score,
        review_priority_score=priority_score,
        hard_block_flag=item.hard_block_flag,
        hard_watch_flag=item.hard_watch_flag,
        public_status=public_status,
        reason_codes=_row_reason_codes(item, score, public_status, config),
    )


def _resolution_evidence_score(
    item: ResearchMarketResolutionEvidenceQueueInput,
) -> Decimal:
    if item.parsed_rule_count == _ZERO or item.result_evidence_count == _ZERO:
        return _ZERO
    score = _quantize(
        ((item.rule_confidence_score + item.result_evidence_score) / _TWO)
        - item.conflict_severity_score,
    )
    return _clamp_ratio(score)


def _row_status(
    item: ResearchMarketResolutionEvidenceQueueInput,
    score: Decimal,
    config: ResearchMarketResolutionEvidenceQueueConfig,
) -> str:
    if item.hard_block_flag:
        return "block"
    if (
        item.conflict_evidence_count > _ZERO
        and item.conflict_severity_score >= config.conflict_block_severity_score
    ):
        return "block"
    if score < config.watch_resolution_evidence_score:
        return "block"
    if item.hard_watch_flag:
        return "watch"
    if item.conflict_evidence_count > _ZERO:
        return "watch"
    if score < config.pass_resolution_evidence_score:
        return "watch"
    return "pass"


def _review_priority_score(
    item: ResearchMarketResolutionEvidenceQueueInput,
    score: Decimal,
    config: ResearchMarketResolutionEvidenceQueueConfig,
) -> Decimal:
    priority = _ONE - score
    if item.conflict_evidence_count > _ZERO:
        priority += item.conflict_severity_score
    if item.hard_watch_flag:
        priority += config.hard_watch_priority_boost
    if item.hard_block_flag:
        priority += config.hard_block_priority_boost
    return _clamp_ratio(priority)


def _row_reason_codes(
    item: ResearchMarketResolutionEvidenceQueueInput,
    score: Decimal,
    public_status: str,
    config: ResearchMarketResolutionEvidenceQueueConfig,
) -> tuple[str, ...]:
    reason_codes = [
        "parsed_rules_present"
        if item.parsed_rule_count > _ZERO
        else "parsed_rules_missing",
        "result_evidence_present"
        if item.result_evidence_count > _ZERO
        else "result_evidence_missing",
        "conflict_evidence_present"
        if item.conflict_evidence_count > _ZERO
        else "no_conflict_evidence",
    ]
    if item.hard_block_flag:
        reason_codes.append("hard_block_flag")
    if item.hard_watch_flag:
        reason_codes.append("hard_watch_flag")
    if score < config.watch_resolution_evidence_score:
        reason_codes.append("resolution_evidence_score_block")
    elif score < config.pass_resolution_evidence_score:
        reason_codes.append("resolution_evidence_score_watch")
    else:
        reason_codes.append("resolution_evidence_score_pass")
    reason_codes.append(
        "human_review_not_required"
        if public_status == "pass"
        else "human_review_required",
    )
    return _normalize_reason_codes(tuple(reason_codes))


def _rank_rows(
    rows: tuple[ResearchMarketResolutionEvidenceQueueRow, ...],
) -> tuple[ResearchMarketResolutionEvidenceQueueRow, ...]:
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                _STATUS_ORDER[row.public_status],
                -row.review_priority_score,
                row.review_key,
            ),
        ),
    )
    ranked_rows: list[ResearchMarketResolutionEvidenceQueueRow] = []
    for index, row in enumerate(sorted_rows, start=1):
        ranked_rows.append(
            ResearchMarketResolutionEvidenceQueueRow(
                review_key=row.review_key,
                queue_rank=_decimal_count(index),
                parsed_rule_count=row.parsed_rule_count,
                result_evidence_count=row.result_evidence_count,
                conflict_evidence_count=row.conflict_evidence_count,
                rule_confidence_score=row.rule_confidence_score,
                result_evidence_score=row.result_evidence_score,
                conflict_severity_score=row.conflict_severity_score,
                resolution_evidence_score=row.resolution_evidence_score,
                review_priority_score=row.review_priority_score,
                hard_block_flag=row.hard_block_flag,
                hard_watch_flag=row.hard_watch_flag,
                public_status=row.public_status,
                reason_codes=row.reason_codes,
            ),
        )
    return tuple(ranked_rows)


def _report_status(rows: tuple[ResearchMarketResolutionEvidenceQueueRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.public_status == "block" for row in rows):
        return "block"
    if any(row.public_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketResolutionEvidenceQueueRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_review_queue",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[ResearchMarketResolutionEvidenceQueueRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.public_status == status)


def _validate_row_consistency(row: ResearchMarketResolutionEvidenceQueueRow) -> None:
    if row.public_status == "pass" and row.review_priority_score > Decimal("0.300000"):
        raise ValueError("review_priority_score must support pass status")
    if row.public_status == "pass" and "human_review_not_required" not in row.reason_codes:
        raise ValueError("pass rows must not require human review")
    if row.public_status in ("watch", "block") and (
        "human_review_required" not in row.reason_codes
    ):
        raise ValueError("watch and block rows must require human review")
    if row.hard_block_flag and row.public_status != "block":
        raise ValueError("hard_block_flag rows must be block")
    if row.hard_watch_flag and row.public_status == "pass":
        raise ValueError("hard_watch_flag rows must not pass")


def _validate_report_consistency(
    report: ResearchMarketResolutionEvidenceQueueReport,
) -> None:
    if report.item_count != _decimal_count(len(report.rows)):
        raise ValueError("item_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_resolution_evidence_score != _average(
        tuple(row.resolution_evidence_score for row in report.rows),
    ):
        raise ValueError("average_resolution_evidence_score must match rows")
    if report.max_review_priority_score != max(
        (row.review_priority_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_review_priority_score must match rows")
    if report.public_status != _report_status(report.rows):
        raise ValueError("public_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    expected_ranks = tuple(_decimal_count(index) for index in range(1, len(report.rows) + 1))
    if tuple(row.queue_rank for row in report.rows) != expected_ranks:
        raise ValueError("queue_rank values must be contiguous")


def _normalize_inputs(
    items: Sequence[ResearchMarketResolutionEvidenceQueueInput],
) -> tuple[ResearchMarketResolutionEvidenceQueueInput, ...]:
    if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
        raise ValueError("items must be a sequence")
    normalized: list[ResearchMarketResolutionEvidenceQueueInput] = []
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchMarketResolutionEvidenceQueueInput:
            raise ValueError(
                "items must contain ResearchMarketResolutionEvidenceQueueInput",
            )
        if item.review_key in seen:
            raise ValueError("review_key values must be unique")
        seen.add(item.review_key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.review_key))


def _normalize_rows(
    rows: Sequence[ResearchMarketResolutionEvidenceQueueRow],
) -> tuple[ResearchMarketResolutionEvidenceQueueRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchMarketResolutionEvidenceQueueRow] = []
    for row in rows:
        if type(row) is not ResearchMarketResolutionEvidenceQueueRow:
            raise ValueError(
                "rows must contain ResearchMarketResolutionEvidenceQueueRow",
            )
        normalized.append(row)
    sorted_rows = tuple(
        sorted(
            normalized,
            key=lambda row: (
                row.queue_rank,
                _STATUS_ORDER[row.public_status],
                -row.review_priority_score,
                row.review_key,
            ),
        ),
    )
    if tuple(normalized) != sorted_rows:
        raise ValueError("rows must be sorted by queue_rank and priority")
    return tuple(normalized)


def _normalize_public_payload(
    public_payload: Sequence[ResearchMarketResolutionEvidenceQueuePublicPayloadItem],
) -> tuple[ResearchMarketResolutionEvidenceQueuePublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchMarketResolutionEvidenceQueuePublicPayloadItem] = []
    seen: set[str] = set()
    for item in public_payload:
        if type(item) is not ResearchMarketResolutionEvidenceQueuePublicPayloadItem:
            raise ValueError(
                "public_payload items must be "
                "ResearchMarketResolutionEvidenceQueuePublicPayloadItem",
            )
        if item.key in seen:
            raise ValueError("public_payload keys must be unique")
        seen.add(item.key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_public_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be a known public status")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized == _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count must be an int")
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchMarketResolutionEvidenceQueueReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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
        raise ValueError("numeric payload values must be Decimal strings")
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


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    if type(key) is not str:
        raise ValueError(f"{path} contains a non-string key")
    _reject_unsafe_public_string(path, key)


__all__ = (
    "DEFAULT_RESEARCH_MARKET_RESOLUTION_EVIDENCE_QUEUE_REPORT_CONFIG_VERSION",
    "ResearchMarketResolutionEvidenceQueueConfig",
    "ResearchMarketResolutionEvidenceQueueInput",
    "ResearchMarketResolutionEvidenceQueuePublicPayloadItem",
    "ResearchMarketResolutionEvidenceQueueReport",
    "ResearchMarketResolutionEvidenceQueueRow",
    "build_research_market_resolution_evidence_queue_report",
    "research_market_resolution_evidence_queue_report_payload",
)
