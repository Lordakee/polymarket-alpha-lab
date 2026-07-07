"""Pure report-only specialist postmortem readiness scoring."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_TEAM_SPECIALIST_POSTMORTEM_READINESS_SCORE_CONFIG_VERSION = (
    "team-specialist-postmortem-readiness-score-v0"
)
DEFAULT_TEAM_SPECIALIST_POSTMORTEM_READINESS_SCORE_VERSION = (
    DEFAULT_TEAM_SPECIALIST_POSTMORTEM_READINESS_SCORE_CONFIG_VERSION
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
RATIO_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")

STATUS_VALUES = ("pass", "watch", "block")
COMPONENT_IDS = (
    "timeline",
    "decision_log",
    "outcome_evidence",
    "root_cause",
    "action_items",
    "memory_update",
)
PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "team_id",
        "specialist_id",
        "postmortem_status",
        "postmortem_readiness_score",
        "timeline_completeness_score",
        "decision_log_score",
        "outcome_evidence_score",
        "root_cause_score",
        "action_item_score",
        "memory_update_score",
        "component_count",
        "pass_component_count",
        "watch_component_count",
        "block_component_count",
        "reason_codes",
        "component_rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
COMPONENT_ROW_PAYLOAD_FIELDS = frozenset(
    (
        "component_id",
        "observed_value",
        "component_score",
        "component_status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
UNSAFE_PUBLIC_FIELD_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "source",
    "url",
    "dsn",
    "table",
    "token",
    "secret",
    "auth",
    "wallet",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommendation",
    "仓位",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = UNSAFE_PUBLIC_FIELD_FRAGMENTS + (
    "source_ref",
    "source_reference",
    "question_text",
    "text",
)
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


@dataclass(frozen=True)
class TeamSpecialistPostmortemReadinessScoreConfig:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_POSTMORTEM_READINESS_SCORE_CONFIG_VERSION
    )
    timeline_weight: Decimal = Decimal("0.200000")
    decision_log_weight: Decimal = Decimal("0.200000")
    outcome_evidence_weight: Decimal = Decimal("0.200000")
    root_cause_weight: Decimal = Decimal("0.150000")
    action_item_weight: Decimal = Decimal("0.150000")
    memory_update_weight: Decimal = Decimal("0.100000")
    min_pass_postmortem_readiness_score: Decimal = Decimal("0.850000")
    min_watch_postmortem_readiness_score: Decimal = Decimal("0.650000")
    min_pass_timeline_completeness_score: Decimal = Decimal("0.900000")
    min_watch_timeline_completeness_score: Decimal = Decimal("0.700000")
    min_pass_decision_log_score: Decimal = Decimal("0.900000")
    min_watch_decision_log_score: Decimal = Decimal("0.700000")
    min_pass_outcome_evidence_score: Decimal = Decimal("0.900000")
    min_watch_outcome_evidence_score: Decimal = Decimal("0.700000")
    min_pass_root_cause_score: Decimal = Decimal("0.850000")
    min_watch_root_cause_score: Decimal = Decimal("0.650000")
    min_pass_action_item_score: Decimal = Decimal("0.850000")
    min_watch_action_item_score: Decimal = Decimal("0.650000")
    min_pass_memory_update_score: Decimal = Decimal("0.800000")
    min_watch_memory_update_score: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            TeamSpecialistPostmortemReadinessScoreConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "timeline_weight",
            "decision_log_weight",
            "outcome_evidence_weight",
            "root_cause_weight",
            "action_item_weight",
            "memory_update_weight",
            "min_pass_postmortem_readiness_score",
            "min_watch_postmortem_readiness_score",
            "min_pass_timeline_completeness_score",
            "min_watch_timeline_completeness_score",
            "min_pass_decision_log_score",
            "min_watch_decision_log_score",
            "min_pass_outcome_evidence_score",
            "min_watch_outcome_evidence_score",
            "min_pass_root_cause_score",
            "min_watch_root_cause_score",
            "min_pass_action_item_score",
            "min_watch_action_item_score",
            "min_pass_memory_update_score",
            "min_watch_memory_update_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class TeamSpecialistPostmortemReadinessScoreInput:
    team_id: str
    specialist_id: str
    timeline_completeness_score: Decimal
    decision_log_score: Decimal
    outcome_evidence_score: Decimal
    root_cause_score: Decimal
    action_item_score: Decimal
    memory_update_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            TeamSpecialistPostmortemReadinessScoreInput,
            "packet",
        )
        object.__setattr__(
            self,
            "team_id",
            _require_public_string("team_id", self.team_id),
        )
        object.__setattr__(
            self,
            "specialist_id",
            _require_public_string("specialist_id", self.specialist_id),
        )
        for field_name in (
            "timeline_completeness_score",
            "decision_log_score",
            "outcome_evidence_score",
            "root_cause_score",
            "action_item_score",
            "memory_update_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("packet", self)
        _reject_unsafe_public_payload("packet", self)


@dataclass(frozen=True)
class TeamSpecialistPostmortemReadinessScoreComponentRow:
    component_id: str
    observed_value: Decimal
    component_score: Decimal
    component_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            TeamSpecialistPostmortemReadinessScoreComponentRow,
            "row",
        )
        _require_member("component_id", self.component_id, COMPONENT_IDS)
        object.__setattr__(
            self,
            "observed_value",
            _normalize_ratio("observed_value", self.observed_value),
        )
        object.__setattr__(
            self,
            "component_score",
            _normalize_ratio("component_score", self.component_score),
        )
        _require_status("component_status", self.component_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_component_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class TeamSpecialistPostmortemReadinessScoreReport:
    generated_at: datetime
    config_version: str
    team_id: str
    specialist_id: str
    postmortem_status: str
    postmortem_readiness_score: Decimal
    timeline_completeness_score: Decimal
    decision_log_score: Decimal
    outcome_evidence_score: Decimal
    root_cause_score: Decimal
    action_item_score: Decimal
    memory_update_score: Decimal
    component_count: Decimal
    pass_component_count: Decimal
    watch_component_count: Decimal
    block_component_count: Decimal
    reason_codes: tuple[str, ...]
    component_rows: tuple[TeamSpecialistPostmortemReadinessScoreComponentRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            TeamSpecialistPostmortemReadinessScoreReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "team_id",
            _require_public_string("team_id", self.team_id),
        )
        object.__setattr__(
            self,
            "specialist_id",
            _require_public_string("specialist_id", self.specialist_id),
        )
        _require_status("postmortem_status", self.postmortem_status)
        for field_name in (
            "postmortem_readiness_score",
            "timeline_completeness_score",
            "decision_log_score",
            "outcome_evidence_score",
            "root_cause_score",
            "action_item_score",
            "memory_update_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "component_count",
            "pass_component_count",
            "watch_component_count",
            "block_component_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "component_rows",
            _normalize_component_rows(self.component_rows),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _payload_digest(_report_payload_without_digest(self))
        if self.derived_validation_digest:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report contents")
        object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        payload = _json_ready(self)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        return validate_team_specialist_postmortem_readiness_score_payload(payload)


def build_team_specialist_postmortem_readiness_score_report(
    packet: TeamSpecialistPostmortemReadinessScoreInput,
    *,
    config: TeamSpecialistPostmortemReadinessScoreConfig | None = None,
    generated_at: datetime,
) -> TeamSpecialistPostmortemReadinessScoreReport:
    if type(packet) is not TeamSpecialistPostmortemReadinessScoreInput:
        raise ValueError(
            "packet must be a TeamSpecialistPostmortemReadinessScoreInput",
        )
    if config is None:
        config = TeamSpecialistPostmortemReadinessScoreConfig()
    if type(config) is not TeamSpecialistPostmortemReadinessScoreConfig:
        raise ValueError(
            "config must be a TeamSpecialistPostmortemReadinessScoreConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags("packet", packet)
    _require_hard_flags("config", config)

    component_rows = (
        _ratio_component_row(
            "timeline",
            observed_value=packet.timeline_completeness_score,
            pass_threshold=config.min_pass_timeline_completeness_score,
            watch_threshold=config.min_watch_timeline_completeness_score,
            watch_reason="timeline_watch",
            block_reason="timeline_block",
        ),
        _ratio_component_row(
            "decision_log",
            observed_value=packet.decision_log_score,
            pass_threshold=config.min_pass_decision_log_score,
            watch_threshold=config.min_watch_decision_log_score,
            watch_reason="decision_log_watch",
            block_reason="decision_log_block",
        ),
        _ratio_component_row(
            "outcome_evidence",
            observed_value=packet.outcome_evidence_score,
            pass_threshold=config.min_pass_outcome_evidence_score,
            watch_threshold=config.min_watch_outcome_evidence_score,
            watch_reason="outcome_evidence_watch",
            block_reason="outcome_evidence_block",
        ),
        _ratio_component_row(
            "root_cause",
            observed_value=packet.root_cause_score,
            pass_threshold=config.min_pass_root_cause_score,
            watch_threshold=config.min_watch_root_cause_score,
            watch_reason="root_cause_watch",
            block_reason="root_cause_block",
        ),
        _ratio_component_row(
            "action_items",
            observed_value=packet.action_item_score,
            pass_threshold=config.min_pass_action_item_score,
            watch_threshold=config.min_watch_action_item_score,
            watch_reason="action_items_watch",
            block_reason="action_items_block",
        ),
        _ratio_component_row(
            "memory_update",
            observed_value=packet.memory_update_score,
            pass_threshold=config.min_pass_memory_update_score,
            watch_threshold=config.min_watch_memory_update_score,
            watch_reason="memory_update_watch",
            block_reason="memory_update_block",
        ),
    )
    readiness_score = _weighted_readiness_score(component_rows, config)
    reason_codes = _report_reason_codes(component_rows, readiness_score, config)
    status = _postmortem_status(component_rows, readiness_score, config)

    return TeamSpecialistPostmortemReadinessScoreReport(
        generated_at=generated_at,
        config_version=config.config_version,
        team_id=packet.team_id,
        specialist_id=packet.specialist_id,
        postmortem_status=status,
        postmortem_readiness_score=readiness_score,
        timeline_completeness_score=packet.timeline_completeness_score,
        decision_log_score=packet.decision_log_score,
        outcome_evidence_score=packet.outcome_evidence_score,
        root_cause_score=packet.root_cause_score,
        action_item_score=packet.action_item_score,
        memory_update_score=packet.memory_update_score,
        component_count=_decimal_count(len(component_rows)),
        pass_component_count=_decimal_count(_status_count(component_rows, "pass")),
        watch_component_count=_decimal_count(_status_count(component_rows, "watch")),
        block_component_count=_decimal_count(_status_count(component_rows, "block")),
        reason_codes=reason_codes,
        component_rows=component_rows,
    )


def team_specialist_postmortem_readiness_score_payload(
    report: TeamSpecialistPostmortemReadinessScoreReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is TeamSpecialistPostmortemReadinessScoreReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        return report.payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report, allow_json_containers=True)
        return validate_team_specialist_postmortem_readiness_score_payload(report)
    raise ValueError(
        "report must be a TeamSpecialistPostmortemReadinessScoreReport or payload",
    )


def validate_team_specialist_postmortem_readiness_score_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _require_payload_hard_flags(payload)
    if set(payload) != REPORT_PAYLOAD_FIELDS:
        raise ValueError("payload fields must match postmortem readiness report")
    if type(payload["component_rows"]) is not list:
        raise ValueError("component_rows must be a list")
    for row in payload["component_rows"]:
        if type(row) is not dict:
            raise ValueError("component row must be a JSON object")
        if set(row) != COMPONENT_ROW_PAYLOAD_FIELDS:
            raise ValueError("component row fields must match postmortem readiness row")
        _require_payload_hard_flags(row)
        _require_member("component_id", row["component_id"], COMPONENT_IDS)
        _require_status("component_status", row["component_status"])
        _parse_payload_decimal("observed_value", row["observed_value"], ratio=True)
        _parse_payload_decimal("component_score", row["component_score"], ratio=True)
        _require_payload_reason_codes(row["reason_codes"])

    _require_status("postmortem_status", payload["postmortem_status"])
    for field_name in (
        "postmortem_readiness_score",
        "timeline_completeness_score",
        "decision_log_score",
        "outcome_evidence_score",
        "root_cause_score",
        "action_item_score",
        "memory_update_score",
    ):
        _parse_payload_decimal(field_name, payload[field_name], ratio=True)
    for field_name in (
        "component_count",
        "pass_component_count",
        "watch_component_count",
        "block_component_count",
    ):
        _parse_payload_decimal(field_name, payload[field_name], count=True)
    _require_payload_reason_codes(payload["reason_codes"])
    _validate_payload_consistency(payload)
    _validate_payload_digest(payload)
    return payload


def _ratio_component_row(
    component_id: str,
    *,
    observed_value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> TeamSpecialistPostmortemReadinessScoreComponentRow:
    if observed_value >= pass_threshold:
        status = "pass"
        reason_codes = ()
    elif observed_value >= watch_threshold:
        status = "watch"
        reason_codes = (watch_reason,)
    else:
        status = "block"
        reason_codes = (block_reason,)
    return TeamSpecialistPostmortemReadinessScoreComponentRow(
        component_id=component_id,
        observed_value=observed_value,
        component_score=observed_value,
        component_status=status,
        reason_codes=reason_codes,
    )


def _weighted_readiness_score(
    rows: Sequence[TeamSpecialistPostmortemReadinessScoreComponentRow],
    config: TeamSpecialistPostmortemReadinessScoreConfig,
) -> Decimal:
    row_by_component = {row.component_id: row for row in rows}
    with localcontext(DECIMAL_CONTEXT):
        score = (
            row_by_component["timeline"].component_score * config.timeline_weight
            + row_by_component["decision_log"].component_score
            * config.decision_log_weight
            + row_by_component["outcome_evidence"].component_score
            * config.outcome_evidence_weight
            + row_by_component["root_cause"].component_score * config.root_cause_weight
            + row_by_component["action_items"].component_score
            * config.action_item_weight
            + row_by_component["memory_update"].component_score
            * config.memory_update_weight
        )
    return _quantize_ratio("postmortem_readiness_score", score)


def _postmortem_status(
    rows: Sequence[TeamSpecialistPostmortemReadinessScoreComponentRow],
    score: Decimal,
    config: TeamSpecialistPostmortemReadinessScoreConfig,
) -> str:
    if any(row.component_status == "block" for row in rows):
        return "block"
    if score < config.min_watch_postmortem_readiness_score:
        return "block"
    if any(row.component_status == "watch" for row in rows):
        return "watch"
    if score < config.min_pass_postmortem_readiness_score:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: Sequence[TeamSpecialistPostmortemReadinessScoreComponentRow],
    score: Decimal,
    config: TeamSpecialistPostmortemReadinessScoreConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    if score < config.min_watch_postmortem_readiness_score:
        reason_codes.append("postmortem_score_block")
    elif score < config.min_pass_postmortem_readiness_score:
        reason_codes.append("postmortem_score_watch")
    if not reason_codes:
        reason_codes.append("postmortem_materials_complete")
    return tuple(reason_codes)


def _validate_config(config: TeamSpecialistPostmortemReadinessScoreConfig) -> None:
    with localcontext(DECIMAL_CONTEXT):
        weight_sum = (
            config.timeline_weight
            + config.decision_log_weight
            + config.outcome_evidence_weight
            + config.root_cause_weight
            + config.action_item_weight
            + config.memory_update_weight
        )
    if _quantize_ratio("config_weight_sum", weight_sum) != ONE_RATIO:
        raise ValueError("config weights must sum to 1.000000")
    if (
        config.min_watch_postmortem_readiness_score
        > config.min_pass_postmortem_readiness_score
    ):
        raise ValueError("config postmortem readiness thresholds invalid")
    if (
        config.min_watch_timeline_completeness_score
        > config.min_pass_timeline_completeness_score
    ):
        raise ValueError("config timeline thresholds invalid")
    if config.min_watch_decision_log_score > config.min_pass_decision_log_score:
        raise ValueError("config decision log thresholds invalid")
    if (
        config.min_watch_outcome_evidence_score
        > config.min_pass_outcome_evidence_score
    ):
        raise ValueError("config outcome evidence thresholds invalid")
    if config.min_watch_root_cause_score > config.min_pass_root_cause_score:
        raise ValueError("config root cause thresholds invalid")
    if config.min_watch_action_item_score > config.min_pass_action_item_score:
        raise ValueError("config action item thresholds invalid")
    if config.min_watch_memory_update_score > config.min_pass_memory_update_score:
        raise ValueError("config memory update thresholds invalid")


def _validate_component_row(
    row: TeamSpecialistPostmortemReadinessScoreComponentRow,
) -> None:
    if row.component_status == "pass" and row.reason_codes:
        raise ValueError("pass component row must not have reason_codes")
    if row.component_status in ("watch", "block") and not row.reason_codes:
        raise ValueError("non-pass component row must have reason_codes")


def _validate_report(report: TeamSpecialistPostmortemReadinessScoreReport) -> None:
    if tuple(row.component_id for row in report.component_rows) != COMPONENT_IDS:
        raise ValueError("component_rows must follow canonical component order")
    if report.component_count != _decimal_count(len(report.component_rows)):
        raise ValueError("component_count must match component_rows")
    if report.pass_component_count != _decimal_count(
        _status_count(report.component_rows, "pass"),
    ):
        raise ValueError("pass_component_count must match component_rows")
    if report.watch_component_count != _decimal_count(
        _status_count(report.component_rows, "watch"),
    ):
        raise ValueError("watch_component_count must match component_rows")
    if report.block_component_count != _decimal_count(
        _status_count(report.component_rows, "block"),
    ):
        raise ValueError("block_component_count must match component_rows")
    expected_status = _status_from_rows(report.component_rows)
    if report.postmortem_status != expected_status:
        raise ValueError("postmortem_status must match component_rows")
    if (
        report.postmortem_status == "pass"
        and report.reason_codes != ("postmortem_materials_complete",)
    ):
        raise ValueError("pass report reason_codes must be complete")
    if (
        report.postmortem_status != "pass"
        and report.reason_codes == ("postmortem_materials_complete",)
    ):
        raise ValueError("non-pass report reason_codes must explain the status")


def _validate_payload_consistency(payload: dict[str, Any]) -> None:
    rows = payload["component_rows"]
    if tuple(row["component_id"] for row in rows) != COMPONENT_IDS:
        raise ValueError("component_rows must follow canonical component order")
    if _parse_payload_decimal("component_count", payload["component_count"], count=True) != (
        _decimal_count(len(rows))
    ):
        raise ValueError("component_count must match component_rows")
    for status in STATUS_VALUES:
        field_name = f"{status}_component_count"
        expected = _decimal_count(
            sum(Decimal("1") for row in rows if row["component_status"] == status),
        )
        if _parse_payload_decimal(field_name, payload[field_name], count=True) != expected:
            raise ValueError(f"{field_name} must match component_rows")
    row_status = _status_from_payload_rows(rows)
    if payload["postmortem_status"] != row_status:
        raise ValueError("postmortem_status must match component_rows")


def _status_from_rows(
    rows: Sequence[TeamSpecialistPostmortemReadinessScoreComponentRow],
) -> str:
    if any(row.component_status == "block" for row in rows):
        return "block"
    if any(row.component_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_from_payload_rows(rows: list[dict[str, Any]]) -> str:
    if any(row["component_status"] == "block" for row in rows):
        return "block"
    if any(row["component_status"] == "watch" for row in rows):
        return "watch"
    return "pass"


def _normalize_component_rows(
    rows: tuple[TeamSpecialistPostmortemReadinessScoreComponentRow, ...],
) -> tuple[TeamSpecialistPostmortemReadinessScoreComponentRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("component_rows must be a tuple")
    for row in rows:
        if type(row) is not TeamSpecialistPostmortemReadinessScoreComponentRow:
            raise ValueError("component_rows must contain postmortem readiness rows")
    return rows


def _normalize_reason_codes(label: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{label} must be a tuple")
    normalized = tuple(_require_public_string(label, value) for value in values)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{label} must not contain duplicate values")
    return normalized


def _require_payload_reason_codes(values: object) -> None:
    if type(values) is not list:
        raise ValueError("reason_codes must be a list")
    seen: set[str] = set()
    for value in values:
        _require_public_string("reason_codes", value)
        if value in seen:
            raise ValueError("reason_codes must not contain duplicate values")
        seen.add(value)


def _normalize_ratio(label: str, value: Decimal) -> Decimal:
    normalized = _quantize_ratio(label, value)
    if normalized < ZERO_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{label} must be between 0.000000 and 1.000000")
    return normalized


def _quantize_ratio(label: str, value: Decimal) -> Decimal:
    return _require_decimal(label, value).quantize(RATIO_QUANTUM)


def _normalize_nonnegative_count(label: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(label, value)
    if normalized < ZERO_RATIO:
        raise ValueError(f"{label} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{label} must be a whole Decimal")
    return normalized.quantize(COUNT_QUANTUM)


def _require_decimal(label: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{label} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{label} must be finite")
    return value


def _parse_payload_decimal(
    label: str,
    value: object,
    *,
    ratio: bool = False,
    count: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{label} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{label} must be a Decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{label} must be finite")
    if ratio:
        return _normalize_ratio(label, decimal_value)
    if count:
        return _normalize_nonnegative_count(label, decimal_value)
    return _require_decimal(label, decimal_value)


def _decimal_count(value: int | Decimal) -> Decimal:
    if type(value) is Decimal:
        return _normalize_nonnegative_count("count", value)
    return Decimal(str(value)).quantize(COUNT_QUANTUM)


def _status_count(
    rows: Sequence[TeamSpecialistPostmortemReadinessScoreComponentRow],
    status: str,
) -> int:
    return sum(1 for row in rows if row.component_status == status)


def _as_utc(label: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{label} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(label: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{label} must be a non-empty canonical string")
    if "://" in value or "?" in value:
        raise ValueError(f"{label} has unsafe public value")
    if _has_unsafe_public_fragment(value, value_check=True):
        raise ValueError(f"{label} has unsafe public value")
    if not IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(f"{label} must be a public identifier")
    return value


def _require_member(label: str, value: object, allowed_values: Sequence[str]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{label} must be one of {', '.join(allowed_values)}")


def _require_status(label: str, value: object) -> None:
    _require_member(label, value, STATUS_VALUES)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"payload {field_name} must be True")


def _require_sha256_digest(label: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{label} must be a sha256 digest")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            TeamSpecialistPostmortemReadinessScoreConfig,
            TeamSpecialistPostmortemReadinessScoreInput,
            TeamSpecialistPostmortemReadinessScoreComponentRow,
            TeamSpecialistPostmortemReadinessScoreReport,
        ):
            raise ValueError(f"{current_path} must be a supported public dataclass")
        for field in fields(value):
            if _has_unsafe_public_fragment(field.name):
                raise ValueError(f"{field.name} has unsafe public field")
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is dict:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{key} has unsafe public field")
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"payload {key} must be True")
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if type(value) in (list, tuple):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        if value.strip() != value or "://" in value or "?" in value:
            raise ValueError(f"{current_path} has unsafe public value")
        if _has_unsafe_public_fragment(value, value_check=True):
            raise ValueError(f"{current_path} has unsafe public value")
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{current_path} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int or type(value) is float:
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    raise ValueError(f"{current_path} is not JSON-ready")


def _has_unsafe_public_fragment(value: str, *, value_check: bool = False) -> bool:
    lowered = value.lower()
    fragments = (
        UNSAFE_PUBLIC_VALUE_FRAGMENTS if value_check else UNSAFE_PUBLIC_FIELD_FRAGMENTS
    )
    return any(fragment in lowered for fragment in fragments)


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        ready = {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
        if type(value) is TeamSpecialistPostmortemReadinessScoreReport:
            ready["derived_validation_digest"] = value.derived_validation_digest
        return ready
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {key: _json_ready(item) for key, item in value.items()}
    if value is None or type(value) in (str, bool):
        return value
    if type(value) is int or type(value) is float:
        raise ValueError("JSON value must use Decimal strings")
    raise ValueError("value is not JSON-ready")


def _report_payload_without_digest(
    report: TeamSpecialistPostmortemReadinessScoreReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report must serialize to a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _payload_digest(payload_without_digest: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    unsigned_payload = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    if digest != _payload_digest(unsigned_payload):
        raise ValueError("derived_validation_digest must match payload contents")


__all__ = (
    "DEFAULT_TEAM_SPECIALIST_POSTMORTEM_READINESS_SCORE_CONFIG_VERSION",
    "DEFAULT_TEAM_SPECIALIST_POSTMORTEM_READINESS_SCORE_VERSION",
    "TeamSpecialistPostmortemReadinessScoreConfig",
    "TeamSpecialistPostmortemReadinessScoreInput",
    "TeamSpecialistPostmortemReadinessScoreComponentRow",
    "TeamSpecialistPostmortemReadinessScoreReport",
    "build_team_specialist_postmortem_readiness_score_report",
    "team_specialist_postmortem_readiness_score_payload",
    "validate_team_specialist_postmortem_readiness_score_payload",
)
