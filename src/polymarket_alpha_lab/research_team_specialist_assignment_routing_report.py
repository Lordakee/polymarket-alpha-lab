"""Public-safe specialist assignment routing report reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_TEAM_SPECIALIST_ASSIGNMENT_ROUTING_CONFIG_VERSION = (
    "research-team-specialist-assignment-routing-report-v0"
)
ASSIGNMENT_ROUTING_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
HEX_CHARS = frozenset("0123456789abcdef")

ROUTING_SOURCE_GAP_WEIGHT = Decimal("8.000000")
ROUTING_MEMORY_GAP_WEIGHT = Decimal("6.000000")
ROUTING_WORKLOAD_WEIGHT = Decimal("3.000000")
ROUTING_CALIBRATION_WEIGHT = Decimal("7.000000")
ROUTING_WEIGHT_TOTAL = Decimal("24.000000")

PAPER_ACTION_BY_STATUS = {
    "pass": "paper_specialist_assignment_monitor",
    "watch": "paper_specialist_assignment_watch",
    "block": "paper_specialist_assignment_block",
}

DOMAIN_TEAM_PREFIXES = {
    "politics": "team_politics",
    "crypto": "team_crypto",
    "macro": "team_macro",
    "energy": "team_energy",
    "weather": "team_weather",
    "sports.soccer": "team_soccer",
    "soccer": "team_soccer",
    "sports.basketball": "team_basketball",
    "basketball": "team_basketball",
    "sports.tennis": "team_tennis",
    "tennis": "team_tennis",
    "equities": "team_equities",
    "gold": "team_gold",
}

REASON_SEQUENCE = (
    "assignment_routing_source_gap_block",
    "assignment_routing_memory_quality_block",
    "assignment_routing_workload_pressure_block",
    "assignment_routing_calibration_backlog_block",
    "assignment_routing_source_gap_watch",
    "assignment_routing_memory_quality_watch",
    "assignment_routing_workload_pressure_watch",
    "assignment_routing_calibration_backlog_watch",
    "assignment_routing_clear",
)
REPORT_REASON_SEQUENCE = (
    "assignment_routing_no_topics",
    *REASON_SEQUENCE,
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def _compact_public_key(value: str) -> str:
    return "".join(char for char in value.lower() if char.isalnum())


UNSAFE_LABEL_FRAGMENTS = frozenset(
    (
        "candidate",
        "market",
        "slug",
        "question",
        "raw",
        "http",
        "url",
        "dsn",
        "table",
        "token",
        "secret",
        "credential",
        "api_key",
        "sizing",
        "recommendation",
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("li", "ve"),
        _join_parts("b", "uy"),
        _join_parts("s", "ell"),
    ),
)
UNSAFE_PAYLOAD_KEYS = frozenset(
    (
        "candidate_id",
        "candidate_key",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "raw_source",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "order_ticket",
        "trade",
        "sizing",
        "recommendation",
        "live",
    ),
)
COMPACT_UNSAFE_PAYLOAD_KEYS = frozenset(
    _compact_public_key(key) for key in UNSAFE_PAYLOAD_KEYS
)
UNSAFE_PAYLOAD_KEY_FRAGMENTS = frozenset(
    _compact_public_key(fragment) for fragment in UNSAFE_LABEL_FRAGMENTS
) | frozenset(("auth", "execute", "execution"))
UNSAFE_PAYLOAD_VALUE_FRAGMENTS = frozenset(
    (
        "candidate",
        "market",
        "slug",
        "question",
        "https://",
        "http://",
        "source_url",
        "source_text",
        "postgres://",
        "dsn",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
        " live ",
    ),
)
REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "topic_count",
        "routed_topic_count",
        "manual_review_topic_count",
        "pass_count",
        "watch_count",
        "block_count",
        "manual_review_topic_ratio",
        "max_routing_pressure_score",
        "avg_routing_pressure_score",
        "max_source_gap_score",
        "min_memory_quality_score",
        "max_workload_pressure_score",
        "max_calibration_backlog_score",
        "status",
        "paper_queue_action",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
REPORT_COUNT_PAYLOAD_FIELDS = frozenset(
    (
        "topic_count",
        "routed_topic_count",
        "manual_review_topic_count",
        "pass_count",
        "watch_count",
        "block_count",
    ),
)
REPORT_RATIO_PAYLOAD_FIELDS = frozenset(
    (
        "max_routing_pressure_score",
        "avg_routing_pressure_score",
        "manual_review_topic_ratio",
        "max_source_gap_score",
        "min_memory_quality_score",
        "max_workload_pressure_score",
        "max_calibration_backlog_score",
    ),
)
ROW_PAYLOAD_FIELDS = frozenset(
    (
        "assignment_rank",
        "topic_ref",
        "domain_label",
        "specialist_team_label",
        "status",
        "routing_pressure_score",
        "source_gap_score",
        "memory_quality_score",
        "memory_gap_score",
        "workload_pressure_score",
        "calibration_backlog_score",
        "observed_at",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_RATIO_PAYLOAD_FIELDS = frozenset(
    (
        "routing_pressure_score",
        "source_gap_score",
        "memory_quality_score",
        "memory_gap_score",
        "workload_pressure_score",
        "calibration_backlog_score",
    ),
)
REASON_CODE_COUNT_PAYLOAD_FIELDS = frozenset(
    (
        "reason_code",
        "count",
        "topic_ratio",
        "paper_only",
        "report_only",
        "readonly",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_ASSIGNMENT_ROUTING_CONFIG_VERSION",
    "ASSIGNMENT_ROUTING_STATUSES",
    "ResearchTeamSpecialistAssignmentRoutingConfig",
    "ResearchTeamSpecialistAssignmentRoutingInput",
    "ResearchTeamSpecialistAssignmentRoutingReasonCodeCount",
    "ResearchTeamSpecialistAssignmentRoutingReport",
    "ResearchTeamSpecialistAssignmentRoutingRow",
    "build_research_team_specialist_assignment_routing_report",
    "research_team_specialist_assignment_routing_report_digest",
    "research_team_specialist_assignment_routing_report_payload",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamSpecialistAssignmentRoutingConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_ASSIGNMENT_ROUTING_CONFIG_VERSION
    )
    max_pass_source_gap_score: Decimal = Decimal("0.400000")
    max_watch_source_gap_score: Decimal = Decimal("0.800000")
    min_pass_memory_quality_score: Decimal = Decimal("0.700000")
    min_watch_memory_quality_score: Decimal = Decimal("0.400000")
    max_pass_workload_pressure_score: Decimal = Decimal("0.400000")
    max_watch_workload_pressure_score: Decimal = Decimal("0.800000")
    max_pass_calibration_backlog_score: Decimal = Decimal("0.400000")
    max_watch_calibration_backlog_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistAssignmentRoutingConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_ASSIGNMENT_ROUTING_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_source_gap_score",
            "max_watch_source_gap_score",
            "min_pass_memory_quality_score",
            "min_watch_memory_quality_score",
            "max_pass_workload_pressure_score",
            "max_watch_workload_pressure_score",
            "max_pass_calibration_backlog_score",
            "max_watch_calibration_backlog_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_pass_source_gap_score > self.max_watch_source_gap_score:
            raise ValueError(
                "max_watch_source_gap_score must be at least max_pass_source_gap_score",
            )
        if self.min_watch_memory_quality_score > self.min_pass_memory_quality_score:
            raise ValueError(
                "min_pass_memory_quality_score must be at least "
                "min_watch_memory_quality_score",
            )
        if self.max_pass_workload_pressure_score > self.max_watch_workload_pressure_score:
            raise ValueError(
                "max_watch_workload_pressure_score must be at least "
                "max_pass_workload_pressure_score",
            )
        if (
            self.max_pass_calibration_backlog_score
            > self.max_watch_calibration_backlog_score
        ):
            raise ValueError(
                "max_watch_calibration_backlog_score must be at least "
                "max_pass_calibration_backlog_score",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistAssignmentRoutingInput(_FinalDataclass):
    raw_topic_key: str
    domain_label: str
    source_gap_score: Decimal
    memory_quality_score: Decimal
    workload_pressure_score: Decimal
    calibration_backlog_score: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistAssignmentRoutingInput,
            "input",
        )
        _require_raw_topic_key("raw_topic_key", self.raw_topic_key)
        _require_public_label("domain_label", self.domain_label)
        for field_name in (
            "source_gap_score",
            "memory_quality_score",
            "workload_pressure_score",
            "calibration_backlog_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistAssignmentRoutingRow(_FinalDataclass):
    assignment_rank: Decimal
    topic_ref: str
    domain_label: str
    specialist_team_label: str
    status: str
    routing_pressure_score: Decimal
    source_gap_score: Decimal
    memory_quality_score: Decimal
    memory_gap_score: Decimal
    workload_pressure_score: Decimal
    calibration_backlog_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistAssignmentRoutingRow, "row")
        object.__setattr__(
            self,
            "assignment_rank",
            _require_count_decimal("assignment_rank", self.assignment_rank),
        )
        _require_public_string("topic_ref", self.topic_ref)
        _require_public_label("domain_label", self.domain_label)
        _require_public_label("specialist_team_label", self.specialist_team_label)
        _require_status("status", self.status)
        for field_name in (
            "routing_pressure_score",
            "source_gap_score",
            "memory_quality_score",
            "memory_gap_score",
            "workload_pressure_score",
            "calibration_backlog_score",
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
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistAssignmentRoutingReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    topic_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistAssignmentRoutingReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "topic_ratio",
            _require_ratio_decimal("topic_ratio", self.topic_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistAssignmentRoutingReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    topic_count: Decimal
    routed_topic_count: Decimal
    manual_review_topic_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    manual_review_topic_ratio: Decimal
    max_routing_pressure_score: Decimal
    avg_routing_pressure_score: Decimal
    max_source_gap_score: Decimal
    min_memory_quality_score: Decimal
    max_workload_pressure_score: Decimal
    max_calibration_backlog_score: Decimal
    status: str
    paper_queue_action: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchTeamSpecialistAssignmentRoutingReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchTeamSpecialistAssignmentRoutingRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistAssignmentRoutingReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_ASSIGNMENT_ROUTING_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "topic_count",
            "routed_topic_count",
            "manual_review_topic_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_routing_pressure_score",
            "avg_routing_pressure_score",
            "manual_review_topic_ratio",
            "max_source_gap_score",
            "min_memory_quality_score",
            "max_workload_pressure_score",
            "max_calibration_backlog_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_public_string("paper_queue_action", self.paper_queue_action)
        if self.paper_queue_action != PAPER_ACTION_BY_STATUS[self.status]:
            raise ValueError("paper_queue_action must match status")
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        _require_sha256("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_team_specialist_assignment_routing_report(
    inputs: Iterable[ResearchTeamSpecialistAssignmentRoutingInput],
    *,
    config: ResearchTeamSpecialistAssignmentRoutingConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistAssignmentRoutingReport:
    _require_exact_type(
        config,
        ResearchTeamSpecialistAssignmentRoutingConfig,
        "config",
    )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    base_rows = tuple(_row_from_input(item, config) for item in input_rows)
    rows = tuple(
        _with_rank(row, rank)
        for rank, row in enumerate(sorted(base_rows, key=_row_sort_key), start=1)
    )
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "topic_count": _count(len(rows)),
        "routed_topic_count": _count(len(rows)),
        "manual_review_topic_count": _manual_review_topic_count(rows),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "manual_review_topic_ratio": _ratio(
            _manual_review_topic_count(rows),
            _count(len(rows)),
        ),
        "max_routing_pressure_score": _max_decimal(
            tuple(row.routing_pressure_score for row in rows),
        ),
        "avg_routing_pressure_score": _avg_decimal(
            tuple(row.routing_pressure_score for row in rows),
        ),
        "max_source_gap_score": _max_decimal(
            tuple(row.source_gap_score for row in rows),
        ),
        "min_memory_quality_score": _min_ratio(
            tuple(row.memory_quality_score for row in rows),
        ),
        "max_workload_pressure_score": _max_decimal(
            tuple(row.workload_pressure_score for row in rows),
        ),
        "max_calibration_backlog_score": _max_decimal(
            tuple(row.calibration_backlog_score for row in rows),
        ),
        "status": _report_status(rows),
        "paper_queue_action": PAPER_ACTION_BY_STATUS[_report_status(rows)],
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchTeamSpecialistAssignmentRoutingReport(
        **values,
        derived_validation_digest=_digest_from_values(values),
    )


def research_team_specialist_assignment_routing_report_payload(
    report: ResearchTeamSpecialistAssignmentRoutingReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchTeamSpecialistAssignmentRoutingReport:
        _require_hard_flags("report", report)
        payload = _json_ready(asdict(report))
    elif isinstance(report, Mapping):
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchTeamSpecialistAssignmentRoutingReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("report payload", _MappingFlags(payload))
    expected_digest = _digest_from_payload(payload)
    if payload.get("derived_validation_digest") != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    _reject_unsafe_public_payload("report payload", payload, allow_json_containers=True)
    _require_public_payload_schema(payload)
    return payload


def research_team_specialist_assignment_routing_report_digest(
    report: ResearchTeamSpecialistAssignmentRoutingReport | Mapping[str, object],
) -> str:
    payload = research_team_specialist_assignment_routing_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


@dataclass(frozen=True)
class _MappingFlags:
    value: Mapping[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _require_public_payload_schema(payload: Mapping[str, object]) -> None:
    _require_payload_fields("report payload", payload, REPORT_PAYLOAD_FIELDS)
    _require_utc_datetime_payload("generated_at", payload["generated_at"])
    _require_public_string("config_version", payload["config_version"])
    if (
        payload["config_version"]
        != DEFAULT_RESEARCH_TEAM_SPECIALIST_ASSIGNMENT_ROUTING_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    for field_name in REPORT_COUNT_PAYLOAD_FIELDS:
        _require_decimal_payload(field_name, payload[field_name], maximum=None)
    for field_name in REPORT_RATIO_PAYLOAD_FIELDS:
        _require_decimal_payload(field_name, payload[field_name], maximum=ONE)
    status = payload["status"]
    _require_status("status", status)
    _require_public_string("paper_queue_action", payload["paper_queue_action"])
    if payload["paper_queue_action"] != PAPER_ACTION_BY_STATUS[status]:
        raise ValueError("paper_queue_action must match status")
    _require_reason_code_payload_list(
        "reason_codes",
        payload["reason_codes"],
        report_level=True,
    )
    _require_reason_code_count_payloads(payload["reason_code_counts"])
    _require_row_payloads(payload["rows"])
    _require_sha256("derived_validation_digest", payload["derived_validation_digest"])
    _require_hard_flags("report payload", _MappingFlags(payload))


def _require_payload_fields(
    label: str,
    payload: Mapping[str, object],
    expected_fields: frozenset[str],
) -> None:
    keys = frozenset(payload)
    extra = sorted(keys - expected_fields)
    if extra:
        raise ValueError(f"unexpected public payload field in {label}: {extra[0]}")
    missing = sorted(expected_fields - keys)
    if missing:
        raise ValueError(f"missing public payload field in {label}: {missing[0]}")


def _require_row_payloads(value: object) -> None:
    if not isinstance(value, list):
        raise ValueError("rows must be a list")
    for item in value:
        if type(item) is not dict:
            raise ValueError("rows must contain JSON objects")
        _require_payload_fields("row payload", item, ROW_PAYLOAD_FIELDS)
        _require_decimal_payload("assignment_rank", item["assignment_rank"], maximum=None)
        _require_topic_ref_payload(item["topic_ref"])
        _require_public_label("domain_label", item["domain_label"])
        _require_public_label("specialist_team_label", item["specialist_team_label"])
        _require_status("status", item["status"])
        for field_name in ROW_RATIO_PAYLOAD_FIELDS:
            _require_decimal_payload(field_name, item[field_name], maximum=ONE)
        _require_utc_datetime_payload("observed_at", item["observed_at"])
        _require_reason_code_payload_list(
            "reason_codes",
            item["reason_codes"],
            report_level=False,
        )
        _require_hard_flags("row payload", _MappingFlags(item))


def _require_reason_code_count_payloads(value: object) -> None:
    if not isinstance(value, list):
        raise ValueError("reason_code_counts must be a list")
    reason_codes: list[str] = []
    for item in value:
        if type(item) is not dict:
            raise ValueError("reason_code_counts must contain JSON objects")
        _require_payload_fields(
            "reason_code_count payload",
            item,
            REASON_CODE_COUNT_PAYLOAD_FIELDS,
        )
        reason_code = item["reason_code"]
        _require_reason_codes((reason_code,), require_nonempty=True)
        if type(reason_code) is not str:
            raise ValueError("reason_code must be a string")
        if reason_code in reason_codes:
            raise ValueError("reason_code_counts must be unique")
        reason_codes.append(reason_code)
        _require_decimal_payload("count", item["count"], maximum=None)
        _require_decimal_payload("topic_ratio", item["topic_ratio"], maximum=ONE)
        _require_hard_flags("reason_code_count payload", _MappingFlags(item))
    expected = tuple(
        reason_code
        for reason_code in REPORT_REASON_SEQUENCE
        if reason_code in reason_codes
    )
    if tuple(reason_codes) != expected:
        raise ValueError("reason_code_counts must be sorted deterministically")


def _require_reason_code_payload_list(
    name: str,
    value: object,
    *,
    report_level: bool,
) -> None:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    reason_codes = tuple(value)
    if report_level:
        _require_report_reason_codes(reason_codes)
        return
    _require_reason_codes(reason_codes, require_nonempty=True)


def _require_decimal_payload(
    name: str,
    value: object,
    *,
    maximum: Decimal | None,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be a Decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{name} must be finite")
    quantized = decimal_value.quantize(QUANTUM)
    if value != str(quantized):
        raise ValueError(f"{name} must be a canonical Decimal string")
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if maximum is not None and decimal_value > maximum:
        raise ValueError(f"{name} must be between 0 and 1")
    return quantized


def _require_utc_datetime_payload(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a UTC datetime string") from exc
    _as_utc(name, parsed)


def _require_topic_ref_payload(value: object) -> None:
    if type(value) is not str or not value.startswith("topic_ref_"):
        raise ValueError("topic_ref must be a hashed topic reference")
    _require_sha256("topic_ref", value.removeprefix("topic_ref_"))


def _row_from_input(
    item: ResearchTeamSpecialistAssignmentRoutingInput,
    config: ResearchTeamSpecialistAssignmentRoutingConfig,
) -> ResearchTeamSpecialistAssignmentRoutingRow:
    memory_gap_score = _clamp_ratio(ONE - item.memory_quality_score)
    reason_codes = _row_reason_codes(item=item, config=config)
    return ResearchTeamSpecialistAssignmentRoutingRow(
        assignment_rank=ONE,
        topic_ref=_topic_ref(item.raw_topic_key),
        domain_label=item.domain_label,
        specialist_team_label=_specialist_team_label(item.domain_label),
        status=_row_status(reason_codes),
        routing_pressure_score=_routing_pressure_score(
            source_gap_score=item.source_gap_score,
            memory_gap_score=memory_gap_score,
            workload_pressure_score=item.workload_pressure_score,
            calibration_backlog_score=item.calibration_backlog_score,
        ),
        source_gap_score=item.source_gap_score,
        memory_quality_score=item.memory_quality_score,
        memory_gap_score=memory_gap_score,
        workload_pressure_score=item.workload_pressure_score,
        calibration_backlog_score=item.calibration_backlog_score,
        observed_at=item.observed_at,
        reason_codes=reason_codes,
    )


def _with_rank(
    row: ResearchTeamSpecialistAssignmentRoutingRow,
    rank: int,
) -> ResearchTeamSpecialistAssignmentRoutingRow:
    return ResearchTeamSpecialistAssignmentRoutingRow(
        assignment_rank=_count(rank),
        topic_ref=row.topic_ref,
        domain_label=row.domain_label,
        specialist_team_label=row.specialist_team_label,
        status=row.status,
        routing_pressure_score=row.routing_pressure_score,
        source_gap_score=row.source_gap_score,
        memory_quality_score=row.memory_quality_score,
        memory_gap_score=row.memory_gap_score,
        workload_pressure_score=row.workload_pressure_score,
        calibration_backlog_score=row.calibration_backlog_score,
        observed_at=row.observed_at,
        reason_codes=row.reason_codes,
    )


def _row_reason_codes(
    *,
    item: ResearchTeamSpecialistAssignmentRoutingInput,
    config: ResearchTeamSpecialistAssignmentRoutingConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_high_threshold_reason(
        reasons,
        metric=item.source_gap_score,
        watch=config.max_pass_source_gap_score,
        block=config.max_watch_source_gap_score,
        watch_code="assignment_routing_source_gap_watch",
        block_code="assignment_routing_source_gap_block",
    )
    _append_low_threshold_reason(
        reasons,
        metric=item.memory_quality_score,
        watch=config.min_pass_memory_quality_score,
        block=config.min_watch_memory_quality_score,
        watch_code="assignment_routing_memory_quality_watch",
        block_code="assignment_routing_memory_quality_block",
    )
    _append_high_threshold_reason(
        reasons,
        metric=item.workload_pressure_score,
        watch=config.max_pass_workload_pressure_score,
        block=config.max_watch_workload_pressure_score,
        watch_code="assignment_routing_workload_pressure_watch",
        block_code="assignment_routing_workload_pressure_block",
    )
    _append_high_threshold_reason(
        reasons,
        metric=item.calibration_backlog_score,
        watch=config.max_pass_calibration_backlog_score,
        block=config.max_watch_calibration_backlog_score,
        watch_code="assignment_routing_calibration_backlog_watch",
        block_code="assignment_routing_calibration_backlog_block",
    )
    if not reasons:
        reasons.append("assignment_routing_clear")
    return _require_reason_codes(tuple(reasons), require_nonempty=True)


def _append_low_threshold_reason(
    reasons: list[str],
    *,
    metric: Decimal,
    watch: Decimal,
    block: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if metric < block:
        reasons.append(block_code)
        return
    if metric < watch:
        reasons.append(watch_code)


def _append_high_threshold_reason(
    reasons: list[str],
    *,
    metric: Decimal,
    watch: Decimal,
    block: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if metric >= block:
        reasons.append(block_code)
        return
    if metric >= watch:
        reasons.append(watch_code)


def _routing_pressure_score(
    *,
    source_gap_score: Decimal,
    memory_gap_score: Decimal,
    workload_pressure_score: Decimal,
    calibration_backlog_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            source_gap_score * ROUTING_SOURCE_GAP_WEIGHT
            + memory_gap_score * ROUTING_MEMORY_GAP_WEIGHT
            + workload_pressure_score * ROUTING_WORKLOAD_WEIGHT
            + calibration_backlog_score * ROUTING_CALIBRATION_WEIGHT
        ) / ROUTING_WEIGHT_TOTAL
    return _clamp_ratio(score)


def _specialist_team_label(domain_label: str) -> str:
    if domain_label in DOMAIN_TEAM_PREFIXES:
        return DOMAIN_TEAM_PREFIXES[domain_label]
    prefix = domain_label.split(".", 1)[0]
    if prefix in DOMAIN_TEAM_PREFIXES:
        return DOMAIN_TEAM_PREFIXES[prefix]
    return f"team_{prefix.replace('-', '_')}"


def _topic_ref(raw_topic_key: str) -> str:
    digest = sha256(raw_topic_key.encode("utf-8")).hexdigest()
    return f"topic_ref_{digest}"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchTeamSpecialistAssignmentRoutingRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _row_sort_key(
    row: ResearchTeamSpecialistAssignmentRoutingRow,
) -> tuple[int, Decimal, str, str]:
    return (
        _status_rank(row.status),
        -row.routing_pressure_score,
        row.specialist_team_label,
        row.topic_ref,
    )


def _status_rank(status: str) -> int:
    return {"block": 0, "watch": 1, "pass": 2}[status]


def _status_count(
    rows: tuple[ResearchTeamSpecialistAssignmentRoutingRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _manual_review_topic_count(
    rows: tuple[ResearchTeamSpecialistAssignmentRoutingRow, ...],
) -> Decimal:
    return _count(sum(1 for row in rows if row.status in {"watch", "block"}))


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistAssignmentRoutingRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("assignment_routing_no_topics",)
    reason_codes = frozenset(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(
        reason_code for reason_code in REASON_SEQUENCE if reason_code in reason_codes
    )


def _reason_code_counts(
    rows: tuple[ResearchTeamSpecialistAssignmentRoutingRow, ...],
) -> tuple[ResearchTeamSpecialistAssignmentRoutingReasonCodeCount, ...]:
    if not rows:
        return ()
    counter = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    total = _count(len(rows))
    return tuple(
        ResearchTeamSpecialistAssignmentRoutingReasonCodeCount(
            reason_code=reason_code,
            count=_count(counter[reason_code]),
            topic_ratio=_ratio(_count(counter[reason_code]), total),
        )
        for reason_code in REASON_SEQUENCE
        if counter[reason_code]
    )


def _normalize_inputs(
    inputs: Iterable[ResearchTeamSpecialistAssignmentRoutingInput],
) -> tuple[ResearchTeamSpecialistAssignmentRoutingInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        items = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchTeamSpecialistAssignmentRoutingInput:
            raise ValueError(
                "inputs must contain ResearchTeamSpecialistAssignmentRoutingInput",
            )
        _require_hard_flags("input", item)
        if item.raw_topic_key in seen:
            raise ValueError("raw_topic_key values must be unique")
        seen.add(item.raw_topic_key)
    return items


def _require_rows(
    rows: tuple[ResearchTeamSpecialistAssignmentRoutingRow, ...],
) -> tuple[ResearchTeamSpecialistAssignmentRoutingRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    topic_refs: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchTeamSpecialistAssignmentRoutingRow:
            raise ValueError("rows must contain ResearchTeamSpecialistAssignmentRoutingRow")
        _require_hard_flags("row", row)
        if row.topic_ref in topic_refs:
            raise ValueError("topic_ref values must be unique")
        topic_refs.add(row.topic_ref)
    return normalized


def _require_reason_code_counts(
    value: tuple[ResearchTeamSpecialistAssignmentRoutingReasonCodeCount, ...],
) -> tuple[ResearchTeamSpecialistAssignmentRoutingReasonCodeCount, ...]:
    if not isinstance(value, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    normalized = tuple(value)
    expected = tuple(
        sorted(
            normalized,
            key=lambda item: REPORT_REASON_SEQUENCE.index(item.reason_code),
        ),
    )
    if normalized != expected:
        raise ValueError("reason_code_counts must be sorted deterministically")
    reason_codes: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchTeamSpecialistAssignmentRoutingReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamSpecialistAssignmentRoutingReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
        if item.reason_code in reason_codes:
            raise ValueError("reason_code_counts must be unique")
        reason_codes.add(item.reason_code)
    return normalized


def _require_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    reason_codes = _require_reason_codes(value, require_nonempty=True)
    expected = tuple(
        reason_code
        for reason_code in REPORT_REASON_SEQUENCE
        if reason_code in reason_codes
    )
    if reason_codes != expected:
        raise ValueError("reason_codes must be sorted deterministically")
    return reason_codes


def _validate_row(row: ResearchTeamSpecialistAssignmentRoutingRow) -> None:
    if row.specialist_team_label != _specialist_team_label(row.domain_label):
        raise ValueError("specialist_team_label must match domain_label")
    if row.memory_gap_score != _clamp_ratio(ONE - row.memory_quality_score):
        raise ValueError("memory_gap_score must match memory_quality_score")
    expected_score = _routing_pressure_score(
        source_gap_score=row.source_gap_score,
        memory_gap_score=row.memory_gap_score,
        workload_pressure_score=row.workload_pressure_score,
        calibration_backlog_score=row.calibration_backlog_score,
    )
    if row.routing_pressure_score != expected_score:
        raise ValueError("routing_pressure_score must match component scores")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchTeamSpecialistAssignmentRoutingReport) -> None:
    rows = report.rows
    if report.topic_count != _count(len(rows)):
        raise ValueError("topic_count must match rows")
    if report.routed_topic_count != report.topic_count:
        raise ValueError("routed_topic_count must match topic_count")
    if report.manual_review_topic_count != _manual_review_topic_count(rows):
        raise ValueError("manual_review_topic_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    expected_manual_review_ratio = _ratio(
        report.manual_review_topic_count,
        report.topic_count,
    )
    if report.manual_review_topic_ratio != expected_manual_review_ratio:
        raise ValueError("manual_review_topic_ratio must match rows")
    if report.max_routing_pressure_score != _max_decimal(
        tuple(row.routing_pressure_score for row in rows),
    ):
        raise ValueError("max_routing_pressure_score must match rows")
    if report.avg_routing_pressure_score != _avg_decimal(
        tuple(row.routing_pressure_score for row in rows),
    ):
        raise ValueError("avg_routing_pressure_score must match rows")
    if report.max_source_gap_score != _max_decimal(
        tuple(row.source_gap_score for row in rows),
    ):
        raise ValueError("max_source_gap_score must match rows")
    if report.min_memory_quality_score != _min_ratio(
        tuple(row.memory_quality_score for row in rows),
    ):
        raise ValueError("min_memory_quality_score must match rows")
    if report.max_workload_pressure_score != _max_decimal(
        tuple(row.workload_pressure_score for row in rows),
    ):
        raise ValueError("max_workload_pressure_score must match rows")
    if report.max_calibration_backlog_score != _max_decimal(
        tuple(row.calibration_backlog_score for row in rows),
    ):
        raise ValueError("max_calibration_backlog_score must match rows")


def _report_values_without_digest(
    report: ResearchTeamSpecialistAssignmentRoutingReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    return _digest_from_payload(payload)


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value.quantize(QUANTUM))
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int:
        return value
    if type(value) is float:
        raise ValueError("public payload must not contain floats")
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


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(numerator / denominator)


def _avg_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _ratio(_sum_decimal(values), _count(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values).quantize(QUANTUM)


def _min_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values).quantize(QUANTUM)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = sum(values, ZERO)
    return total.quantize(QUANTUM)


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        if value < ZERO:
            return ZERO
        if value > ONE:
            return ONE
        return value.quantize(QUANTUM)


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return value.quantize(QUANTUM)


def _require_count_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    quantized = value.quantize(QUANTUM)
    if quantized != value:
        raise ValueError(f"{name} must use six decimal places or fewer")
    return quantized


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be UTC-aware")
    if value.utcoffset() != timedelta(0):
        raise ValueError(f"{name} must be UTC")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_public_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must not be empty")
    if len(value) > 160:
        raise ValueError(f"{name} is too long")


def _require_raw_topic_key(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} must not be empty")
    if len(value) > 512:
        raise ValueError(f"{name} is too long")


def _require_public_label(name: str, value: object) -> None:
    _require_public_string(name, value)
    text = str(value)
    if not PUBLIC_LABEL_RE.fullmatch(text):
        raise ValueError(f"{name} must be a public aggregate label")
    lowered = text.lower()
    if any(fragment in lowered for fragment in UNSAFE_LABEL_FRAGMENTS):
        raise ValueError(f"{name} must be a public aggregate label")


def _require_status(name: str, value: object) -> None:
    if type(value) is not str or value not in ASSIGNMENT_ROUTING_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_reason_codes(
    value: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not value:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in value:
        _require_public_string("reason_code", reason_code)
        if reason_code not in REPORT_REASON_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    return tuple(value)


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _require_sha256(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64 or any(char not in HEX_CHARS for char in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _reject_unsafe_public_payload(
    label: str,
    payload: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(payload) and not isinstance(payload, type):
        _reject_unsafe_public_payload(
            label,
            asdict(payload),
            allow_json_containers=allow_json_containers,
        )
        return
    if isinstance(payload, Mapping):
        for key, item in payload.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            normalized_key = key.lower()
            compact_key = _compact_public_key(key)
            if (
                normalized_key in UNSAFE_PAYLOAD_KEYS
                or compact_key in COMPACT_UNSAFE_PAYLOAD_KEYS
                or any(
                    fragment in compact_key
                    for fragment in UNSAFE_PAYLOAD_KEY_FRAGMENTS
                )
            ):
                raise ValueError(f"unsafe public payload key in {label}")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(payload, (list, tuple)):
        for item in payload:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(payload) is str:
        lowered = payload.lower()
        if any(fragment in lowered for fragment in UNSAFE_PAYLOAD_VALUE_FRAGMENTS):
            raise ValueError(f"unsafe public payload value in {label}")
        return
    if type(payload) is float:
        raise ValueError(f"unsafe public payload numeric in {label}")
    if allow_json_containers:
        return
