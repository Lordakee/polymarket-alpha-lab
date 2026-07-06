"""Pure Phase 1 event update completeness gate for research packets."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_PACKET_EVENT_UPDATE_COMPLETENESS_GATE_V2_CONFIG_VERSION = (
    "research-packet-event-update-completeness-gate-v2-v0"
)

PASS_REASON = "research_packet_event_update_completeness_gate_v2_passed"
EMPTY_REASON = "research_packet_event_update_completeness_gate_v2_empty"
MISSING_UPDATE_REASON = "research_packet_event_update_completeness_missing_update"
OFFICIAL_UPDATE_BOOST_REASON = (
    "research_packet_event_update_completeness_official_update_boost"
)
LOW_SCORE_REASON = "research_packet_event_update_completeness_score_below_threshold"

ROW_REASON_CODES = (
    PASS_REASON,
    MISSING_UPDATE_REASON,
    OFFICIAL_UPDATE_BOOST_REASON,
    LOW_SCORE_REASON,
)
REPORT_REASON_CODES = (EMPTY_REASON, *ROW_REASON_CODES)
GATE_STATUSES = ("pass", "blocked")
NEXT_STEPS = {
    "pass": "use_research_packet_event_update_report",
    "blocked": "hold_research_packet_until_event_updates_complete",
}
STATUS_WEIGHT = {"blocked": 0, "pass": 1}
REQUIRED_UPDATE_FIELDS = (
    "official_update_observed_at",
    "event_status_update_observed_at",
    "resolution_update_observed_at",
    "forecast_update_observed_at",
)
MISSING_UPDATE_CODE_BY_FIELD = {
    "official_update_observed_at": "missing_official_update",
    "event_status_update_observed_at": "missing_event_status_update",
    "resolution_update_observed_at": "missing_resolution_update",
    "forecast_update_observed_at": "missing_forecast_update",
}
MISSING_UPDATE_CODES = tuple(
    MISSING_UPDATE_CODE_BY_FIELD[field_name] for field_name in REQUIRED_UPDATE_FIELDS
)
UNSAFE_PUBLIC_FRAGMENTS = (
    "li" + "ve",
    "au" + "th",
    "wa" + "llet",
    "or" + "der",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
    "sig" + "ning",
    "muta" + "tion",
    "b" + "uy",
    "se" + "ll",
    "tra" + "de",
)
DECIMAL_CONTEXT = Context(prec=28)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


@dataclass(frozen=True)
class ResearchPacketEventUpdateCompletenessGateV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_EVENT_UPDATE_COMPLETENESS_GATE_V2_CONFIG_VERSION
    )
    missing_update_penalty: Decimal = Decimal("0.250000")
    official_update_boost: Decimal = Decimal("0.100000")
    min_pass_score: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "missing_update_penalty",
            "official_update_boost",
            "min_pass_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchPacketEventUpdateCompletenessGateV2Observation:
    packet_id: str
    event_id: str
    team_id: str
    packet_generated_at: datetime
    official_update_observed_at: datetime | None = None
    event_status_update_observed_at: datetime | None = None
    resolution_update_observed_at: datetime | None = None
    forecast_update_observed_at: datetime | None = None
    source_config_version: str = (
        DEFAULT_RESEARCH_PACKET_EVENT_UPDATE_COMPLETENESS_GATE_V2_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("packet_id", "event_id", "team_id", "source_config_version"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "packet_generated_at",
            _as_utc("packet_generated_at", self.packet_generated_at),
        )
        for field_name in REQUIRED_UPDATE_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchPacketEventUpdateCompletenessGateV2Row:
    packet_id: str
    event_id: str
    team_id: str
    row_status: str
    packet_generated_at: datetime
    official_update_observed_at: datetime | None
    event_status_update_observed_at: datetime | None
    resolution_update_observed_at: datetime | None
    forecast_update_observed_at: datetime | None
    latest_update_observed_at: datetime | None
    latest_update_age_seconds: Decimal | None
    required_update_count: Decimal
    present_update_count: Decimal
    missing_update_count: Decimal
    missing_update_penalty_total: Decimal
    official_update_boost: Decimal
    completeness_score: Decimal
    missing_update_codes: tuple[str, ...]
    reason_codes: tuple[str, ...]
    source_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("packet_id", "event_id", "team_id", "source_config_version"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("row_status", self.row_status, GATE_STATUSES)
        object.__setattr__(
            self,
            "packet_generated_at",
            _as_utc("packet_generated_at", self.packet_generated_at),
        )
        for field_name in REQUIRED_UPDATE_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _as_optional_utc(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_update_observed_at",
            _as_optional_utc(
                "latest_update_observed_at",
                self.latest_update_observed_at,
            ),
        )
        object.__setattr__(
            self,
            "latest_update_age_seconds",
            _normalize_optional_decimal(
                "latest_update_age_seconds",
                self.latest_update_age_seconds,
            ),
        )
        for field_name in (
            "required_update_count",
            "present_update_count",
            "missing_update_count",
            "missing_update_penalty_total",
            "official_update_boost",
            "completeness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.completeness_score > ONE:
            raise ValueError("completeness_score must be <= 1")
        object.__setattr__(
            self,
            "missing_update_codes",
            _normalize_missing_update_codes(self.missing_update_codes),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchPacketEventUpdateCompletenessGateV2Report:
    generated_at: datetime
    config_version: str
    gate_status: str
    next_step: str
    packet_count: Decimal
    event_count: Decimal
    team_count: Decimal
    pass_row_count: Decimal
    blocked_row_count: Decimal
    required_update_count: Decimal
    present_update_count: Decimal
    missing_update_count: Decimal
    missing_row_count: Decimal
    average_completeness_score: Decimal
    min_completeness_score: Decimal
    max_missing_update_count: Decimal
    rows: tuple[ResearchPacketEventUpdateCompletenessGateV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_member("gate_status", self.gate_status, GATE_STATUSES)
        _require_public_string("next_step", self.next_step)
        for field_name in (
            "packet_count",
            "event_count",
            "team_count",
            "pass_row_count",
            "blocked_row_count",
            "required_update_count",
            "present_update_count",
            "missing_update_count",
            "missing_row_count",
            "average_completeness_score",
            "min_completeness_score",
            "max_missing_update_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.average_completeness_score > ONE:
            raise ValueError("average_completeness_score must be <= 1")
        if self.min_completeness_score > ONE:
            raise ValueError("min_completeness_score must be <= 1")
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report contents")


def build_research_packet_event_update_completeness_gate_v2(
    observations: list[ResearchPacketEventUpdateCompletenessGateV2Observation]
    | tuple[ResearchPacketEventUpdateCompletenessGateV2Observation, ...],
    *,
    config: ResearchPacketEventUpdateCompletenessGateV2Config,
    generated_at: datetime,
) -> ResearchPacketEventUpdateCompletenessGateV2Report:
    if type(config) is not ResearchPacketEventUpdateCompletenessGateV2Config:
        raise ValueError(
            "config must be a ResearchPacketEventUpdateCompletenessGateV2Config"
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(
        observations,
        generated_at=generated_at_utc,
    )
    rows = tuple(
        sorted(
            (
                _row_for_observation(
                    observation,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for observation in normalized_observations
            ),
            key=_row_sort_key,
        )
    )
    gate_status = _gate_status(rows)

    return ResearchPacketEventUpdateCompletenessGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        gate_status=gate_status,
        next_step=NEXT_STEPS[gate_status],
        packet_count=_decimal_count(len(rows)),
        event_count=_decimal_count(len({row.event_id for row in rows})),
        team_count=_decimal_count(len({row.team_id for row in rows})),
        pass_row_count=_decimal_count(_row_status_count(rows, "pass")),
        blocked_row_count=_decimal_count(_row_status_count(rows, "blocked")),
        required_update_count=_sum_decimals(row.required_update_count for row in rows),
        present_update_count=_sum_decimals(row.present_update_count for row in rows),
        missing_update_count=_sum_decimals(row.missing_update_count for row in rows),
        missing_row_count=_decimal_count(
            sum(row.missing_update_count > ZERO for row in rows),
        ),
        average_completeness_score=_average_completeness_score(rows),
        min_completeness_score=_min_decimal(
            (row.completeness_score for row in rows),
            default=ONE,
        ),
        max_missing_update_count=_max_decimal(
            (row.missing_update_count for row in rows),
            default=ZERO,
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
    )


def research_packet_event_update_completeness_gate_v2_payload(
    report: ResearchPacketEventUpdateCompletenessGateV2Report,
) -> dict[str, Any]:
    if type(report) is not ResearchPacketEventUpdateCompletenessGateV2Report:
        raise ValueError(
            "report must be a ResearchPacketEventUpdateCompletenessGateV2Report"
        )
    _require_hard_flags("report", report)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report contents")
    payload = _report_payload(report, include_digest=True)
    validate_research_packet_event_update_completeness_gate_v2_public_payload(payload)
    return payload


def validate_research_packet_event_update_completeness_gate_v2_public_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _row_for_observation(
    observation: ResearchPacketEventUpdateCompletenessGateV2Observation,
    *,
    config: ResearchPacketEventUpdateCompletenessGateV2Config,
    generated_at: datetime,
) -> ResearchPacketEventUpdateCompletenessGateV2Row:
    missing_update_codes = _missing_update_codes(observation)
    missing_update_count = _decimal_count(len(missing_update_codes))
    present_update_count = _decimal_count(len(REQUIRED_UPDATE_FIELDS)) - missing_update_count
    missing_update_penalty_total = _multiply(
        missing_update_count,
        config.missing_update_penalty,
    )
    official_update_boost = (
        config.official_update_boost
        if observation.official_update_observed_at is not None
        else ZERO
    )
    completeness_score = _bounded_score(
        ONE - missing_update_penalty_total + official_update_boost
    )
    row_status = "pass" if completeness_score >= config.min_pass_score else "blocked"
    latest_observed_at = _latest_update_observed_at(observation)

    return ResearchPacketEventUpdateCompletenessGateV2Row(
        packet_id=observation.packet_id,
        event_id=observation.event_id,
        team_id=observation.team_id,
        row_status=row_status,
        packet_generated_at=observation.packet_generated_at,
        official_update_observed_at=observation.official_update_observed_at,
        event_status_update_observed_at=observation.event_status_update_observed_at,
        resolution_update_observed_at=observation.resolution_update_observed_at,
        forecast_update_observed_at=observation.forecast_update_observed_at,
        latest_update_observed_at=latest_observed_at,
        latest_update_age_seconds=(
            None if latest_observed_at is None else _age_seconds(generated_at, latest_observed_at)
        ),
        required_update_count=_decimal_count(len(REQUIRED_UPDATE_FIELDS)),
        present_update_count=present_update_count,
        missing_update_count=missing_update_count,
        missing_update_penalty_total=missing_update_penalty_total,
        official_update_boost=official_update_boost,
        completeness_score=completeness_score,
        missing_update_codes=missing_update_codes,
        reason_codes=_row_reason_codes(
            row_status=row_status,
            missing_update_codes=missing_update_codes,
            official_update_boost=official_update_boost,
        ),
        source_config_version=observation.source_config_version,
    )


def _missing_update_codes(
    observation: ResearchPacketEventUpdateCompletenessGateV2Observation,
) -> tuple[str, ...]:
    return tuple(
        MISSING_UPDATE_CODE_BY_FIELD[field_name]
        for field_name in REQUIRED_UPDATE_FIELDS
        if getattr(observation, field_name) is None
    )


def _row_reason_codes(
    *,
    row_status: str,
    missing_update_codes: tuple[str, ...],
    official_update_boost: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if row_status == "pass":
        reason_codes.append(PASS_REASON)
    if missing_update_codes:
        reason_codes.append(MISSING_UPDATE_REASON)
    if official_update_boost > ZERO:
        reason_codes.append(OFFICIAL_UPDATE_BOOST_REASON)
    if row_status == "blocked":
        reason_codes.append(LOW_SCORE_REASON)
    return tuple(reason_codes)


def _report_reason_codes(
    rows: tuple[ResearchPacketEventUpdateCompletenessGateV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    present_reason_codes = {
        reason_code for row in rows for reason_code in row.reason_codes
    }
    return tuple(
        reason_code for reason_code in REPORT_REASON_CODES if reason_code in present_reason_codes
    )


def _gate_status(rows: tuple[ResearchPacketEventUpdateCompletenessGateV2Row, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.row_status == "blocked" for row in rows):
        return "blocked"
    return "pass"


def _normalize_observations(
    observations: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchPacketEventUpdateCompletenessGateV2Observation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    normalized = tuple(observations)
    seen_keys: set[tuple[str, str, str]] = set()
    for observation in normalized:
        if type(observation) is not ResearchPacketEventUpdateCompletenessGateV2Observation:
            raise ValueError("observations must contain completeness observations")
        _require_hard_flags("observation", observation)
        key = (observation.packet_id, observation.event_id, observation.team_id)
        if key in seen_keys:
            raise ValueError("packet, event, and team values must be unique")
        seen_keys.add(key)
        if observation.packet_generated_at > generated_at:
            raise ValueError("packet_generated_at must not be after generated_at")
        for observed_at in _observed_at_values(observation):
            if observed_at > generated_at:
                raise ValueError("observed_at timestamps must not be after generated_at")
    return normalized


def _observed_at_values(
    observation: ResearchPacketEventUpdateCompletenessGateV2Observation,
) -> tuple[datetime, ...]:
    return tuple(
        observed_at
        for observed_at in (
            observation.official_update_observed_at,
            observation.event_status_update_observed_at,
            observation.resolution_update_observed_at,
            observation.forecast_update_observed_at,
        )
        if observed_at is not None
    )


def _latest_update_observed_at(
    observation: ResearchPacketEventUpdateCompletenessGateV2Observation,
) -> datetime | None:
    values = _observed_at_values(observation)
    if not values:
        return None
    return max(values)


def _validate_config(config: ResearchPacketEventUpdateCompletenessGateV2Config) -> None:
    if config.missing_update_penalty == ZERO:
        raise ValueError("missing_update_penalty must be positive")
    if config.min_pass_score == ZERO:
        raise ValueError("min_pass_score must be positive")


def _validate_row(row: ResearchPacketEventUpdateCompletenessGateV2Row) -> None:
    observation = _observation_from_row(row)
    if row.latest_update_observed_at != _latest_update_observed_at(observation):
        raise ValueError("latest_update_observed_at must match row updates")
    if row.latest_update_age_seconds is None and row.latest_update_observed_at is not None:
        raise ValueError("latest_update_age_seconds is required with latest update")
    if row.latest_update_age_seconds is not None and row.latest_update_observed_at is None:
        raise ValueError("latest_update_age_seconds must be absent without latest update")
    if row.required_update_count != _decimal_count(len(REQUIRED_UPDATE_FIELDS)):
        raise ValueError("required_update_count must match required updates")
    if row.present_update_count != _decimal_count(_present_update_count(row)):
        raise ValueError("present_update_count must match row updates")
    if row.missing_update_count != _decimal_count(len(row.missing_update_codes)):
        raise ValueError("missing_update_count must match missing_update_codes")
    if row.present_update_count + row.missing_update_count != row.required_update_count:
        raise ValueError("update counts must reconcile")
    if row.official_update_observed_at is None and row.official_update_boost != ZERO:
        raise ValueError("official_update_boost must be zero without official update")
    expected_reason_codes = _row_reason_codes(
        row_status=row.row_status,
        missing_update_codes=row.missing_update_codes,
        official_update_boost=row.official_update_boost,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match completeness state")
    if row.row_status == "pass" and LOW_SCORE_REASON in row.reason_codes:
        raise ValueError("row_status must match reason_codes")
    if row.row_status == "blocked" and LOW_SCORE_REASON not in row.reason_codes:
        raise ValueError("row_status must match reason_codes")


def _validate_report(report: ResearchPacketEventUpdateCompletenessGateV2Report) -> None:
    if report.next_step != NEXT_STEPS[report.gate_status]:
        raise ValueError("next_step must match gate_status")
    if report.gate_status != _gate_status(report.rows):
        raise ValueError("gate_status must match rows")
    if report.packet_count != _decimal_count(len(report.rows)):
        raise ValueError("packet_count must match rows")
    if report.event_count != _decimal_count(len({row.event_id for row in report.rows})):
        raise ValueError("event_count must match rows")
    if report.team_count != _decimal_count(len({row.team_id for row in report.rows})):
        raise ValueError("team_count must match rows")
    if report.pass_row_count != _decimal_count(_row_status_count(report.rows, "pass")):
        raise ValueError("pass_row_count must match rows")
    if report.blocked_row_count != _decimal_count(
        _row_status_count(report.rows, "blocked")
    ):
        raise ValueError("blocked_row_count must match rows")
    if report.required_update_count != _sum_decimals(
        row.required_update_count for row in report.rows
    ):
        raise ValueError("required_update_count must match rows")
    if report.present_update_count != _sum_decimals(
        row.present_update_count for row in report.rows
    ):
        raise ValueError("present_update_count must match rows")
    if report.missing_update_count != _sum_decimals(
        row.missing_update_count for row in report.rows
    ):
        raise ValueError("missing_update_count must match rows")
    if report.missing_row_count != _decimal_count(
        sum(row.missing_update_count > ZERO for row in report.rows)
    ):
        raise ValueError("missing_row_count must match rows")
    if report.average_completeness_score != _average_completeness_score(report.rows):
        raise ValueError("average_completeness_score must match rows")
    if report.min_completeness_score != _min_decimal(
        (row.completeness_score for row in report.rows),
        default=ONE,
    ):
        raise ValueError("min_completeness_score must match rows")
    if report.max_missing_update_count != _max_decimal(
        (row.missing_update_count for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_missing_update_count must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_rows(
    rows: object,
) -> tuple[ResearchPacketEventUpdateCompletenessGateV2Row, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_keys: set[tuple[str, str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchPacketEventUpdateCompletenessGateV2Row:
            raise ValueError("rows must contain completeness rows")
        _require_hard_flags("row", row)
        key = (row.packet_id, row.event_id, row.team_id)
        if key in seen_keys:
            raise ValueError("rows packet, event, and team values must be unique")
        seen_keys.add(key)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and score")
    return normalized


def _row_sort_key(
    row: ResearchPacketEventUpdateCompletenessGateV2Row,
) -> tuple[object, ...]:
    return (
        STATUS_WEIGHT[row.row_status],
        row.completeness_score,
        row.team_id,
        row.event_id,
        row.packet_id,
    )


def _row_status_count(
    rows: tuple[ResearchPacketEventUpdateCompletenessGateV2Row, ...],
    row_status: str,
) -> int:
    return sum(1 for row in rows if row.row_status == row_status)


def _present_update_count(row: ResearchPacketEventUpdateCompletenessGateV2Row) -> int:
    return sum(getattr(row, field_name) is not None for field_name in REQUIRED_UPDATE_FIELDS)


def _observation_from_row(
    row: ResearchPacketEventUpdateCompletenessGateV2Row,
) -> ResearchPacketEventUpdateCompletenessGateV2Observation:
    return ResearchPacketEventUpdateCompletenessGateV2Observation(
        packet_id=row.packet_id,
        event_id=row.event_id,
        team_id=row.team_id,
        packet_generated_at=row.packet_generated_at,
        official_update_observed_at=row.official_update_observed_at,
        event_status_update_observed_at=row.event_status_update_observed_at,
        resolution_update_observed_at=row.resolution_update_observed_at,
        forecast_update_observed_at=row.forecast_update_observed_at,
        source_config_version=row.source_config_version,
    )


def _normalize_missing_update_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("missing_update_codes must be a list or tuple")
    codes = tuple(value)
    previous_position = -1
    for code in codes:
        _require_member("missing_update_code", code, MISSING_UPDATE_CODES)
        position = MISSING_UPDATE_CODES.index(code)
        if position <= previous_position:
            raise ValueError("missing_update_codes must be sorted by unique value")
        previous_position = position
    return codes


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    return _normalize_reason_codes(value, allowed_values=ROW_REASON_CODES)


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    return _normalize_reason_codes(value, allowed_values=REPORT_REASON_CODES)


def _normalize_reason_codes(
    value: object,
    *,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must contain at least one value")
    previous_position = -1
    for reason_code in reason_codes:
        _require_member("reason_code", reason_code, allowed_values)
        position = allowed_values.index(reason_code)
        if position <= previous_position:
            raise ValueError("reason_codes must follow canonical sequence")
        previous_position = position
    return reason_codes


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed_values)}")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if type(value) is str and _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")
    try:
        return _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be <= 1")
    return decimal_value


def _normalize_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count must be an int")
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _sum_decimals(values: object) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must contain Decimal")
        total += value
    return _quantize(total)


def _multiply(left: Decimal, right: Decimal) -> Decimal:
    if type(left) is not Decimal or type(right) is not Decimal:
        raise ValueError("operands must be Decimal")
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left * right)


def _divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    if type(numerator) is not Decimal or type(denominator) is not Decimal:
        raise ValueError("operands must be Decimal")
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _average_completeness_score(
    rows: tuple[ResearchPacketEventUpdateCompletenessGateV2Row, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _divide(
        _sum_decimals(row.completeness_score for row in rows),
        _decimal_count(len(rows)),
    )


def _min_decimal(values: object, *, default: Decimal) -> Decimal:
    decimal_values = tuple(values)
    if not decimal_values:
        return _quantize(default)
    return _quantize(min(decimal_values))


def _max_decimal(values: object, *, default: Decimal) -> Decimal:
    decimal_values = tuple(values)
    if not decimal_values:
        return _quantize(default)
    return _quantize(max(decimal_values))


def _bounded_score(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _quantize(value)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return _quantize(Decimal(str(delta.total_seconds())))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _datetime_payload(value: datetime) -> str:
    return _as_utc("datetime", value).isoformat()


def _optional_datetime_payload(value: datetime | None) -> str | None:
    if value is None:
        return None
    return _datetime_payload(value)


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("value must be a Decimal")
    return str(_quantize(value))


def _optional_decimal_payload(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return _decimal_payload(value)


def _report_digest(report: ResearchPacketEventUpdateCompletenessGateV2Report) -> str:
    payload = _report_payload(report, include_digest=False)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _report_payload(
    report: ResearchPacketEventUpdateCompletenessGateV2Report,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_at": _datetime_payload(report.generated_at),
        "config_version": report.config_version,
        "gate_status": report.gate_status,
        "next_step": report.next_step,
        "packet_count": _decimal_payload(report.packet_count),
        "event_count": _decimal_payload(report.event_count),
        "team_count": _decimal_payload(report.team_count),
        "pass_row_count": _decimal_payload(report.pass_row_count),
        "blocked_row_count": _decimal_payload(report.blocked_row_count),
        "required_update_count": _decimal_payload(report.required_update_count),
        "present_update_count": _decimal_payload(report.present_update_count),
        "missing_update_count": _decimal_payload(report.missing_update_count),
        "missing_row_count": _decimal_payload(report.missing_row_count),
        "average_completeness_score": _decimal_payload(
            report.average_completeness_score,
        ),
        "min_completeness_score": _decimal_payload(report.min_completeness_score),
        "max_missing_update_count": _decimal_payload(report.max_missing_update_count),
        "rows": [_row_payload(row) for row in report.rows],
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _row_payload(row: ResearchPacketEventUpdateCompletenessGateV2Row) -> dict[str, Any]:
    return {
        "packet_id": row.packet_id,
        "event_id": row.event_id,
        "team_id": row.team_id,
        "row_status": row.row_status,
        "packet_generated_at": _datetime_payload(row.packet_generated_at),
        "official_update_observed_at": _optional_datetime_payload(
            row.official_update_observed_at,
        ),
        "event_status_update_observed_at": _optional_datetime_payload(
            row.event_status_update_observed_at,
        ),
        "resolution_update_observed_at": _optional_datetime_payload(
            row.resolution_update_observed_at,
        ),
        "forecast_update_observed_at": _optional_datetime_payload(
            row.forecast_update_observed_at,
        ),
        "latest_update_observed_at": _optional_datetime_payload(
            row.latest_update_observed_at,
        ),
        "latest_update_age_seconds": _optional_decimal_payload(
            row.latest_update_age_seconds,
        ),
        "required_update_count": _decimal_payload(row.required_update_count),
        "present_update_count": _decimal_payload(row.present_update_count),
        "missing_update_count": _decimal_payload(row.missing_update_count),
        "missing_update_penalty_total": _decimal_payload(
            row.missing_update_penalty_total,
        ),
        "official_update_boost": _decimal_payload(row.official_update_boost),
        "completeness_score": _decimal_payload(row.completeness_score),
        "missing_update_codes": list(row.missing_update_codes),
        "reason_codes": list(row.reason_codes),
        "source_config_version": row.source_config_version,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if type(value) is datetime:
        _as_utc(path or label, value)
        return
    if type(value) in (int, float):
        raise ValueError(f"{path or label} must use Decimal string values")
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{nested_path} has unsafe public key")
            if key in {"paper_only", "report_only", "readonly"} and nested_value is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, nested_value in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_PACKET_EVENT_UPDATE_COMPLETENESS_GATE_V2_CONFIG_VERSION",
    "ResearchPacketEventUpdateCompletenessGateV2Config",
    "ResearchPacketEventUpdateCompletenessGateV2Observation",
    "ResearchPacketEventUpdateCompletenessGateV2Report",
    "ResearchPacketEventUpdateCompletenessGateV2Row",
    "build_research_packet_event_update_completeness_gate_v2",
    "research_packet_event_update_completeness_gate_v2_payload",
    "validate_research_packet_event_update_completeness_gate_v2_public_payload",
)
