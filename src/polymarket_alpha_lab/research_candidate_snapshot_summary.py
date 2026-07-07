"""Deterministic readonly candidate research snapshot summary."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_CANDIDATE_SNAPSHOT_SUMMARY_CONFIG_VERSION = (
    "research-snapshot-summary-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")

_PUBLIC_STATUSES = ("pass", "watch", "block")
_HUMAN_SCREENING_BUCKETS = ("ready_screen", "priority_screen", "hold_for_rework")
_BUCKET_BY_STATUS = {
    "pass": "ready_screen",
    "watch": "priority_screen",
    "block": "hold_for_rework",
}
_EVENT_TYPE_ROUTES = {
    "binary_event": "standard_event_review",
    "deadline_event": "time_sensitive_review",
    "news_event": "update_driven_review",
    "resolution_event": "resolution_rule_review",
    "volume_event": "signal_context_review",
}
_BLOCK_REASON_CODES = frozenset(
    (
        "evidence_package_quality_block",
        "cost_threshold_block",
        "team_capacity_block",
    ),
)
_REASON_CODE_SEQUENCE = (
    "evidence_package_quality_block",
    "cost_threshold_block",
    "team_capacity_block",
    "missing_required_fields_watch",
    "queue_priority_watch",
    "evidence_package_quality_watch",
    "cost_threshold_watch",
    "team_capacity_watch",
    "snapshot_pass",
)
_STATUS_WEIGHT = {
    "block": Decimal("0"),
    "watch": Decimal("1"),
    "pass": Decimal("2"),
}
_REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "public_status",
    "snapshot_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_queue_priority_score",
    "average_evidence_package_quality_score",
    "average_cost_threshold_score",
    "average_team_capacity_score",
    "total_missing_required_field_count",
    "max_screening_priority_score",
    "reason_codes",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_PAYLOAD_KEYS = (
    "snapshot_key",
    "queue_priority_score",
    "event_type",
    "event_type_route",
    "evidence_package_quality_score",
    "cost_threshold_score",
    "team_capacity_score",
    "missing_required_field_count",
    "screening_priority_score",
    "public_status",
    "human_screening_bucket",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    "candidate",
    "candidate_id",
    "candidate-id",
    "candidate id",
    "market",
    "market_id",
    "market-id",
    "market id",
    "market_slug",
    "market-slug",
    "market slug",
    "market_question",
    "market-question",
    "market question",
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
    "postgres://",
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


@dataclass(frozen=True)
class ResearchCandidateSnapshotSummaryConfig:
    config_version: str = DEFAULT_RESEARCH_CANDIDATE_SNAPSHOT_SUMMARY_CONFIG_VERSION
    watch_queue_priority_score: Decimal = Decimal("0.750000")
    min_pass_evidence_package_quality_score: Decimal = Decimal("0.750000")
    min_watch_evidence_package_quality_score: Decimal = Decimal("0.500000")
    min_pass_cost_threshold_score: Decimal = Decimal("0.700000")
    min_watch_cost_threshold_score: Decimal = Decimal("0.500000")
    min_pass_team_capacity_score: Decimal = Decimal("0.650000")
    min_watch_team_capacity_score: Decimal = Decimal("0.350000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchCandidateSnapshotSummaryConfig does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchCandidateSnapshotSummaryConfig)
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_CANDIDATE_SNAPSHOT_SUMMARY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_queue_priority_score",
            "min_pass_evidence_package_quality_score",
            "min_watch_evidence_package_quality_score",
            "min_pass_cost_threshold_score",
            "min_watch_cost_threshold_score",
            "min_pass_team_capacity_score",
            "min_watch_team_capacity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchCandidateSnapshotSummaryInput:
    snapshot_key: str
    queue_priority_score: Decimal
    event_type: str
    evidence_package_quality_score: Decimal
    cost_threshold_score: Decimal
    team_capacity_score: Decimal
    missing_required_field_count: Decimal = Decimal("0.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchCandidateSnapshotSummaryInput does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type("input", self, ResearchCandidateSnapshotSummaryInput)
        _require_public_identifier("snapshot_key", self.snapshot_key)
        for field_name in (
            "queue_priority_score",
            "evidence_package_quality_score",
            "cost_threshold_score",
            "team_capacity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "missing_required_field_count",
            _require_count_decimal(
                "missing_required_field_count",
                self.missing_required_field_count,
            ),
        )
        _require_event_type("event_type", self.event_type)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchCandidateSnapshotSummaryRow:
    snapshot_key: str
    queue_priority_score: Decimal
    event_type: str
    event_type_route: str
    evidence_package_quality_score: Decimal
    cost_threshold_score: Decimal
    team_capacity_score: Decimal
    missing_required_field_count: Decimal
    screening_priority_score: Decimal
    public_status: str
    human_screening_bucket: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchCandidateSnapshotSummaryRow does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchCandidateSnapshotSummaryRow)
        _require_public_identifier("snapshot_key", self.snapshot_key)
        _require_event_type("event_type", self.event_type)
        _require_event_type_route("event_type_route", self.event_type_route)
        if self.event_type_route != _EVENT_TYPE_ROUTES[self.event_type]:
            raise ValueError("event_type_route must match event_type")
        for field_name in (
            "queue_priority_score",
            "evidence_package_quality_score",
            "cost_threshold_score",
            "team_capacity_score",
            "screening_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "missing_required_field_count",
            _require_count_decimal(
                "missing_required_field_count",
                self.missing_required_field_count,
            ),
        )
        _require_public_status("public_status", self.public_status)
        _require_human_screening_bucket(
            "human_screening_bucket",
            self.human_screening_bucket,
        )
        if self.human_screening_bucket != _BUCKET_BY_STATUS[self.public_status]:
            raise ValueError("human_screening_bucket must match public_status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchCandidateSnapshotSummaryReport:
    generated_at: datetime
    config_version: str
    public_status: str
    snapshot_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_queue_priority_score: Decimal
    average_evidence_package_quality_score: Decimal
    average_cost_threshold_score: Decimal
    average_team_capacity_score: Decimal
    total_missing_required_field_count: Decimal
    max_screening_priority_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchCandidateSnapshotSummaryRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchCandidateSnapshotSummaryReport does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchCandidateSnapshotSummaryReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_CANDIDATE_SNAPSHOT_SUMMARY_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_public_status("public_status", self.public_status)
        for field_name in (
            "snapshot_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_missing_required_field_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_queue_priority_score",
            "average_evidence_package_quality_score",
            "average_cost_threshold_score",
            "average_team_capacity_score",
            "max_screening_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report payload")
        _require_digest("derived_validation_digest", self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_candidate_snapshot_summary_payload(self)


def build_research_candidate_snapshot_summary(
    inputs: Sequence[ResearchCandidateSnapshotSummaryInput],
    *,
    generated_at: datetime,
    config: ResearchCandidateSnapshotSummaryConfig | None = None,
) -> ResearchCandidateSnapshotSummaryReport:
    """Build a deterministic snapshot for manual candidate research screening."""

    if config is None:
        config = ResearchCandidateSnapshotSummaryConfig()
    if type(config) is not ResearchCandidateSnapshotSummaryConfig:
        raise ValueError("config must be a ResearchCandidateSnapshotSummaryConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (_row_from_input(item, config) for item in _normalize_inputs(inputs)),
            key=_row_sort_key,
        ),
    )
    return ResearchCandidateSnapshotSummaryReport(
        generated_at=generated_at,
        config_version=config.config_version,
        public_status=_report_status(rows),
        snapshot_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_queue_priority_score=_average_ratio(
            tuple(row.queue_priority_score for row in rows),
        ),
        average_evidence_package_quality_score=_average_ratio(
            tuple(row.evidence_package_quality_score for row in rows),
        ),
        average_cost_threshold_score=_average_ratio(
            tuple(row.cost_threshold_score for row in rows),
        ),
        average_team_capacity_score=_average_ratio(
            tuple(row.team_capacity_score for row in rows),
        ),
        total_missing_required_field_count=sum(
            (row.missing_required_field_count for row in rows),
            _ZERO,
        ).quantize(_QUANT),
        max_screening_priority_score=max(
            (row.screening_priority_score for row in rows),
            default=_ZERO,
        ),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_candidate_snapshot_summary_payload(
    value: ResearchCandidateSnapshotSummaryReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchCandidateSnapshotSummaryReport:
        _require_hard_flags("report", value)
        _reject_unsafe_public_payload("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError("value must be a ResearchCandidateSnapshotSummaryReport or dict")
    _reject_unsafe_public_payload("public payload", payload)
    _validate_public_payload(payload)
    return payload


def _row_from_input(
    item: ResearchCandidateSnapshotSummaryInput,
    config: ResearchCandidateSnapshotSummaryConfig,
) -> ResearchCandidateSnapshotSummaryRow:
    reason_codes = _row_reason_codes(item, config)
    public_status = _status_from_reason_codes(reason_codes)
    return ResearchCandidateSnapshotSummaryRow(
        snapshot_key=item.snapshot_key,
        queue_priority_score=item.queue_priority_score,
        event_type=item.event_type,
        event_type_route=_EVENT_TYPE_ROUTES[item.event_type],
        evidence_package_quality_score=item.evidence_package_quality_score,
        cost_threshold_score=item.cost_threshold_score,
        team_capacity_score=item.team_capacity_score,
        missing_required_field_count=item.missing_required_field_count,
        screening_priority_score=_screening_priority_score(
            queue_priority_score=item.queue_priority_score,
            public_status=public_status,
        ),
        public_status=public_status,
        human_screening_bucket=_BUCKET_BY_STATUS[public_status],
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchCandidateSnapshotSummaryInput,
    config: ResearchCandidateSnapshotSummaryConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.evidence_package_quality_score < config.min_watch_evidence_package_quality_score:
        reason_codes.append("evidence_package_quality_block")
    if item.cost_threshold_score < config.min_watch_cost_threshold_score:
        reason_codes.append("cost_threshold_block")
    if item.team_capacity_score < config.min_watch_team_capacity_score:
        reason_codes.append("team_capacity_block")
    if not any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        if item.missing_required_field_count > _ZERO:
            reason_codes.append("missing_required_fields_watch")
        if item.queue_priority_score >= config.watch_queue_priority_score:
            reason_codes.append("queue_priority_watch")
        if item.evidence_package_quality_score < config.min_pass_evidence_package_quality_score:
            reason_codes.append("evidence_package_quality_watch")
        if item.cost_threshold_score < config.min_pass_cost_threshold_score:
            reason_codes.append("cost_threshold_watch")
        if item.team_capacity_score < config.min_pass_team_capacity_score:
            reason_codes.append("team_capacity_watch")
    return tuple(reason_codes or ("snapshot_pass",))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if reason_codes == ("snapshot_pass",):
        return "pass"
    return "watch"


def _screening_priority_score(
    *,
    queue_priority_score: Decimal,
    public_status: str,
) -> Decimal:
    value = Decimal("0.100000") + queue_priority_score * Decimal("0.375000")
    if public_status == "block":
        value += Decimal("0.500000")
    elif public_status == "watch":
        value += Decimal("0.250000")
    return _clamp_ratio(value)


def _report_status(rows: tuple[ResearchCandidateSnapshotSummaryRow, ...]) -> str:
    if any(row.public_status == "block" for row in rows):
        return "block"
    if any(row.public_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchCandidateSnapshotSummaryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("snapshot_pass",)
    found = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in found)


def _status_count(
    rows: tuple[ResearchCandidateSnapshotSummaryRow, ...],
    status: str,
) -> int:
    return len(tuple(row for row in rows if row.public_status == status))


def _validate_config(config: ResearchCandidateSnapshotSummaryConfig) -> None:
    if (
        config.min_watch_evidence_package_quality_score
        > config.min_pass_evidence_package_quality_score
    ):
        raise ValueError("min_watch_evidence_package_quality_score must not exceed pass")
    if config.min_watch_cost_threshold_score > config.min_pass_cost_threshold_score:
        raise ValueError("min_watch_cost_threshold_score must not exceed pass")
    if config.min_watch_team_capacity_score > config.min_pass_team_capacity_score:
        raise ValueError("min_watch_team_capacity_score must not exceed pass")


def _validate_row(row: ResearchCandidateSnapshotSummaryRow) -> None:
    if row.public_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("public_status must match reason_codes")
    expected_priority = _screening_priority_score(
        queue_priority_score=row.queue_priority_score,
        public_status=row.public_status,
    )
    if row.screening_priority_score != expected_priority:
        raise ValueError("screening_priority_score must match row fields")


def _validate_report(report: ResearchCandidateSnapshotSummaryReport) -> None:
    rows = report.rows
    if report.snapshot_count != _decimal_count(len(rows)):
        raise ValueError("snapshot_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_queue_priority_score != _average_ratio(
        tuple(row.queue_priority_score for row in rows),
    ):
        raise ValueError("average_queue_priority_score must match rows")
    if report.average_evidence_package_quality_score != _average_ratio(
        tuple(row.evidence_package_quality_score for row in rows),
    ):
        raise ValueError("average_evidence_package_quality_score must match rows")
    if report.average_cost_threshold_score != _average_ratio(
        tuple(row.cost_threshold_score for row in rows),
    ):
        raise ValueError("average_cost_threshold_score must match rows")
    if report.average_team_capacity_score != _average_ratio(
        tuple(row.team_capacity_score for row in rows),
    ):
        raise ValueError("average_team_capacity_score must match rows")
    if report.total_missing_required_field_count != sum(
        (row.missing_required_field_count for row in rows),
        _ZERO,
    ).quantize(_QUANT):
        raise ValueError("total_missing_required_field_count must match rows")
    if report.max_screening_priority_score != max(
        (row.screening_priority_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_screening_priority_score must match rows")
    if report.public_status != _report_status(rows):
        raise ValueError("public_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _normalize_inputs(
    inputs: Sequence[ResearchCandidateSnapshotSummaryInput],
) -> tuple[ResearchCandidateSnapshotSummaryInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchCandidateSnapshotSummaryInput:
            raise ValueError("inputs must contain ResearchCandidateSnapshotSummaryInput")
        _require_hard_flags("input", item)
        if item.snapshot_key in seen:
            raise ValueError("snapshot_key values must be unique")
        seen.add(item.snapshot_key)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchCandidateSnapshotSummaryRow, ...],
) -> tuple[ResearchCandidateSnapshotSummaryRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchCandidateSnapshotSummaryRow:
            raise ValueError("rows must contain ResearchCandidateSnapshotSummaryRow")
        _require_hard_flags("row", row)
        if row.snapshot_key in seen:
            raise ValueError("snapshot_key values must be unique")
        seen.add(row.snapshot_key)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic snapshot ordering")
    return normalized


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(reason_codes)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        if type(reason_code) is not str or reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must contain known values")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    expected = tuple(reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in normalized)
    if normalized != expected:
        raise ValueError("reason_codes must use canonical ordering")
    return normalized


def _row_sort_key(row: ResearchCandidateSnapshotSummaryRow) -> tuple[Decimal, Decimal, str]:
    return (
        _STATUS_WEIGHT[row.public_status],
        -row.screening_priority_score,
        row.snapshot_key,
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public detail")


def _require_event_type(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _EVENT_TYPE_ROUTES:
        raise ValueError(f"{field_name} must be a supported event type")


def _require_event_type_route(field_name: str, value: object) -> None:
    if type(value) is not str or value not in set(_EVENT_TYPE_ROUTES.values()):
        raise ValueError(f"{field_name} must be a supported event type route")


def _require_public_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_human_screening_bucket(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _HUMAN_SCREENING_BUCKETS:
        raise ValueError(f"{field_name} must be a supported screening bucket")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return decimal_value


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _clamp_ratio(sum(values, _ZERO) / _decimal_count(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(max(_quantize(value), _ZERO), _ONE)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext() as context:
            context.rounding = ROUND_HALF_UP
            return value.quantize(_QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _report_digest(report: ResearchCandidateSnapshotSummaryReport) -> str:
    payload = _report_payload(report)
    payload.pop("derived_validation_digest", None)
    return _digest_payload(payload)


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _report_payload(report: ResearchCandidateSnapshotSummaryReport) -> dict[str, Any]:
    return {
        "generated_at": _json_ready(report.generated_at),
        "config_version": report.config_version,
        "public_status": report.public_status,
        "snapshot_count": _json_ready(report.snapshot_count),
        "pass_count": _json_ready(report.pass_count),
        "watch_count": _json_ready(report.watch_count),
        "block_count": _json_ready(report.block_count),
        "average_queue_priority_score": _json_ready(report.average_queue_priority_score),
        "average_evidence_package_quality_score": _json_ready(
            report.average_evidence_package_quality_score,
        ),
        "average_cost_threshold_score": _json_ready(report.average_cost_threshold_score),
        "average_team_capacity_score": _json_ready(report.average_team_capacity_score),
        "total_missing_required_field_count": _json_ready(
            report.total_missing_required_field_count,
        ),
        "max_screening_priority_score": _json_ready(report.max_screening_priority_score),
        "reason_codes": _json_ready(report.reason_codes),
        "rows": [_row_payload(row) for row in report.rows],
        "derived_validation_digest": report.derived_validation_digest,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_payload(row: ResearchCandidateSnapshotSummaryRow) -> dict[str, Any]:
    return {
        "snapshot_key": row.snapshot_key,
        "queue_priority_score": _json_ready(row.queue_priority_score),
        "event_type": row.event_type,
        "event_type_route": row.event_type_route,
        "evidence_package_quality_score": _json_ready(
            row.evidence_package_quality_score,
        ),
        "cost_threshold_score": _json_ready(row.cost_threshold_score),
        "team_capacity_score": _json_ready(row.team_capacity_score),
        "missing_required_field_count": _json_ready(row.missing_required_field_count),
        "screening_priority_score": _json_ready(row.screening_priority_score),
        "public_status": row.public_status,
        "human_screening_bucket": row.human_screening_bucket,
        "reason_codes": _json_ready(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


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
    if type(value) is str or type(value) is bool:
        return value
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON value must use Decimal-derived strings")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _copy_json_object(value: dict[str, Any]) -> dict[str, Any]:
    copied = _json_ready(value)
    if type(copied) is not dict:
        raise ValueError("public payload must be a JSON object")
    return copied


def _validate_public_payload(payload: dict[str, Any]) -> None:
    if tuple(payload.keys()) != _REPORT_PAYLOAD_KEYS:
        if set(payload.keys()) != set(_REPORT_PAYLOAD_KEYS):
            raise ValueError("public payload must use the snapshot summary schema")
    for field_name in (
        "generated_at",
        "config_version",
    ):
        if type(payload[field_name]) is not str:
            raise ValueError(f"{field_name} must be a string")
    if payload["config_version"] != DEFAULT_RESEARCH_CANDIDATE_SNAPSHOT_SUMMARY_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    _require_public_status("public_status", payload["public_status"])
    for field_name in (
        "snapshot_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_queue_priority_score",
        "average_evidence_package_quality_score",
        "average_cost_threshold_score",
        "average_team_capacity_score",
        "total_missing_required_field_count",
        "max_screening_priority_score",
    ):
        _require_decimal_string(field_name, payload[field_name])
    _normalize_reason_codes_from_payload("reason_codes", payload["reason_codes"])
    if type(payload["rows"]) is not list:
        raise ValueError("rows must be a list")
    for row in payload["rows"]:
        _validate_public_row_payload(row)
    _require_digest("derived_validation_digest", payload["derived_validation_digest"])
    _require_hard_flags("public payload", _DictFlags(payload))
    payload_without_digest = dict(payload)
    payload_without_digest.pop("derived_validation_digest", None)
    if payload["derived_validation_digest"] != _digest_payload(payload_without_digest):
        raise ValueError("derived_validation_digest must match public payload")


def _validate_public_row_payload(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("rows must contain JSON objects")
    if tuple(value.keys()) != _ROW_PAYLOAD_KEYS:
        if set(value.keys()) != set(_ROW_PAYLOAD_KEYS):
            raise ValueError("row payload must use the snapshot summary schema")
    _require_public_identifier("snapshot_key", value["snapshot_key"])
    _require_event_type("event_type", value["event_type"])
    _require_event_type_route("event_type_route", value["event_type_route"])
    if value["event_type_route"] != _EVENT_TYPE_ROUTES[value["event_type"]]:
        raise ValueError("event_type_route must match event_type")
    for field_name in (
        "queue_priority_score",
        "evidence_package_quality_score",
        "cost_threshold_score",
        "team_capacity_score",
        "missing_required_field_count",
        "screening_priority_score",
    ):
        _require_decimal_string(field_name, value[field_name])
    _require_public_status("public_status", value["public_status"])
    _require_human_screening_bucket("human_screening_bucket", value["human_screening_bucket"])
    if value["human_screening_bucket"] != _BUCKET_BY_STATUS[value["public_status"]]:
        raise ValueError("human_screening_bucket must match public_status")
    _normalize_reason_codes_from_payload("reason_codes", value["reason_codes"])
    _require_hard_flags("row payload", _DictFlags(value))


def _require_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use Decimal-derived string values")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must use Decimal-derived string values") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal_value


def _normalize_reason_codes_from_payload(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_codes(tuple(value))


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


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.casefold()
    compact = "".join(character for character in normalized if character.isalnum())
    for fragment in _UNSAFE_PUBLIC_FRAGMENTS:
        if fragment in normalized:
            return True
        compact_fragment = "".join(
            character for character in fragment.casefold() if character.isalnum()
        )
        if compact_fragment and compact_fragment in compact:
            return True
    return False


__all__ = (
    "DEFAULT_RESEARCH_CANDIDATE_SNAPSHOT_SUMMARY_CONFIG_VERSION",
    "ResearchCandidateSnapshotSummaryConfig",
    "ResearchCandidateSnapshotSummaryInput",
    "ResearchCandidateSnapshotSummaryReport",
    "ResearchCandidateSnapshotSummaryRow",
    "build_research_candidate_snapshot_summary",
    "research_candidate_snapshot_summary_payload",
)
