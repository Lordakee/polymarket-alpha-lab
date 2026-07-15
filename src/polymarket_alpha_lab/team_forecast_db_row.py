"""Pure row codecs for team forecast persistence payloads."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.team_forecast_packet import (
    TeamForecastEvidencePacket,
    TeamForecastPacket,
    team_forecast_packet_payload,
)
from polymarket_alpha_lab.team_market_router import TeamMarketRouteReport
from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)
from polymarket_alpha_lab.team_taxonomy import require_team_id


__all__ = (
    "TeamForecastDbRow",
    "TeamForecastEvidenceDbRow",
    "TeamForecastOutcome",
    "TeamForecastOutcomeDbRow",
    "TeamMarketRouteDbRow",
    "team_forecast_evidence_from_db_row",
    "team_forecast_evidence_to_db_row",
    "team_forecast_from_db_row",
    "team_forecast_outcome_from_db_row",
    "team_forecast_outcome_to_db_row",
    "team_forecast_to_db_row",
    "team_route_from_db_row",
    "team_route_to_db_row",
)


_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_DECIMAL_QUANTUM = Decimal("0.000001")
_DECIMAL_CONTEXT = Context(prec=64)
_SIDES = frozenset(("yes", "no"))
_HARD_FLAGS = ("paper_only", "report_only", "readonly")
_NESTED_HARD_FLAG_PAYLOAD_KEYS = frozenset(("evidence", "outcome"))
_MISSING = object()


@dataclass(frozen=True)
class TeamMarketRouteDbRow:
    payload_sha256: str
    generated_at: datetime
    team_id: str
    market_slug: str
    config_version: str
    condition_id: str
    category_id: str
    event_template: str
    routing_confidence: Decimal
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256("payload_sha256", self.payload_sha256)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        for field_name in (
            "market_slug",
            "config_version",
            "condition_id",
            "category_id",
            "event_template",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "routing_confidence",
            _normalize_probability("routing_confidence", self.routing_confidence),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_payload_json("payload_json", self.payload_json),
        )
        require_paper_only_flags("team market route DB row", self)
        _validate_payload_hard_flags(self.payload_json, "payload_json")
        _validate_payload_hash(self.payload_sha256, self.payload_json)
        _validate_route_row_matches_payload(self)


@dataclass(frozen=True)
class TeamForecastDbRow:
    """Store canonical Decimal P(YES), regardless of selected_side; selected_side identifies the paper-review side being evaluated and never reorients forecast_probability; P(NO) is 1 - P(YES)."""

    payload_sha256: str
    generated_at: datetime
    forecast_id: str
    condition_id: str
    team_id: str
    market_slug: str
    config_version: str
    selected_side: str
    forecast_probability: Decimal
    confidence: Decimal
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256("payload_sha256", self.payload_sha256)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        for field_name in (
            "forecast_id",
            "condition_id",
            "market_slug",
            "config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_choice("selected_side", self.selected_side, _SIDES)
        object.__setattr__(
            self,
            "forecast_probability",
            _normalize_probability(
                "forecast_probability",
                self.forecast_probability,
            ),
        )
        object.__setattr__(
            self,
            "confidence",
            _normalize_probability("confidence", self.confidence),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_payload_json("payload_json", self.payload_json),
        )
        require_paper_only_flags("team forecast DB row", self)
        _validate_payload_hard_flags(self.payload_json, "payload_json")
        _validate_payload_hash(self.payload_sha256, self.payload_json)
        _validate_forecast_row_matches_payload(self)


@dataclass(frozen=True)
class TeamForecastEvidenceDbRow:
    payload_sha256: str
    generated_at: datetime
    forecast_id: str
    evidence_id: str
    team_id: str
    market_slug: str
    config_version: str
    source_id: str
    data_timestamp: datetime
    data_freshness_seconds: int
    evidence_type: str
    weight: Decimal
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256("payload_sha256", self.payload_sha256)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        for field_name in (
            "forecast_id",
            "evidence_id",
            "market_slug",
            "config_version",
            "source_id",
            "evidence_type",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        object.__setattr__(
            self,
            "data_timestamp",
            _as_utc("data_timestamp", self.data_timestamp),
        )
        _require_nonnegative_int(
            "data_freshness_seconds",
            self.data_freshness_seconds,
        )
        object.__setattr__(self, "weight", _normalize_probability("weight", self.weight))
        object.__setattr__(
            self,
            "payload_json",
            _normalize_payload_json("payload_json", self.payload_json),
        )
        require_paper_only_flags("team forecast evidence DB row", self)
        _validate_payload_hard_flags(self.payload_json, "payload_json")
        _validate_payload_hash(self.payload_sha256, self.payload_json)
        _validate_evidence_row_matches_payload(self)


@dataclass(frozen=True)
class TeamForecastOutcome:
    outcome_id: str
    forecast_id: str
    team_id: str
    market_slug: str
    actual_outcome: str
    resolved_at: datetime
    settlement_source: str
    forecast_error: Decimal
    brier_score: Decimal
    paper_pnl: Decimal
    cost_adjusted_return: Decimal
    directionally_correct: bool
    profitable_after_cost: bool
    resolution_dispute_flag: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "outcome_id",
            "forecast_id",
            "market_slug",
            "settlement_source",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_choice("actual_outcome", self.actual_outcome, _SIDES)
        object.__setattr__(self, "resolved_at", _as_utc("resolved_at", self.resolved_at))
        for field_name in ("forecast_error", "brier_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("paper_pnl", "cost_adjusted_return"):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "directionally_correct",
            "profitable_after_cost",
            "resolution_dispute_flag",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple("reason_codes", self.reason_codes),
        )
        require_paper_only_flags("team forecast outcome", self)


@dataclass(frozen=True)
class TeamForecastOutcomeDbRow:
    payload_sha256: str
    generated_at: datetime
    outcome_id: str
    forecast_id: str
    team_id: str
    market_slug: str
    config_version: str
    resolved_at: datetime
    actual_outcome: str
    forecast_error: Decimal
    brier_score: Decimal
    paper_pnl: Decimal
    cost_adjusted_return: Decimal
    directionally_correct: bool
    profitable_after_cost: bool
    resolution_dispute_flag: bool
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256("payload_sha256", self.payload_sha256)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        for field_name in (
            "outcome_id",
            "forecast_id",
            "market_slug",
            "config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        object.__setattr__(self, "resolved_at", _as_utc("resolved_at", self.resolved_at))
        _require_choice("actual_outcome", self.actual_outcome, _SIDES)
        for field_name in ("forecast_error", "brier_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("paper_pnl", "cost_adjusted_return"):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "directionally_correct",
            "profitable_after_cost",
            "resolution_dispute_flag",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "payload_json",
            _normalize_payload_json("payload_json", self.payload_json),
        )
        require_paper_only_flags("team forecast outcome DB row", self)
        _validate_payload_hard_flags(self.payload_json, "payload_json")
        _validate_payload_hash(self.payload_sha256, self.payload_json)
        _validate_outcome_row_matches_payload(self)


def team_route_to_db_row(report: TeamMarketRouteReport) -> TeamMarketRouteDbRow:
    if type(report) is not TeamMarketRouteReport:
        raise ValueError("report must be a TeamMarketRouteReport")
    require_paper_only_flags("team market route report", report)
    if len(report.rows) != 1:
        raise ValueError("route report must contain exactly one row")
    route = report.rows[0]
    payload_json = _payload_from_dataclass(report)
    return TeamMarketRouteDbRow(
        payload_sha256=_payload_sha256(payload_json),
        generated_at=report.generated_at,
        team_id=route.primary_team_id,
        market_slug=route.market_slug,
        config_version=report.config_version,
        condition_id=route.condition_id,
        category_id=route.category_id,
        event_template=route.event_template,
        routing_confidence=route.routing_confidence,
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def team_route_from_db_row(row: TeamMarketRouteDbRow) -> TeamMarketRouteReport:
    canonical_row = _canonical_row(TeamMarketRouteDbRow, row)
    return _route_report_from_payload(canonical_row.payload_json)


def team_forecast_to_db_row(packet: TeamForecastPacket) -> TeamForecastDbRow:
    if type(packet) is not TeamForecastPacket:
        raise ValueError("packet must be a TeamForecastPacket")
    payload_json = team_forecast_packet_payload(packet)
    return TeamForecastDbRow(
        payload_sha256=_payload_sha256(payload_json),
        generated_at=packet.generated_at,
        forecast_id=packet.forecast_id,
        condition_id=packet.condition_id,
        team_id=packet.team_id,
        market_slug=packet.market_slug,
        config_version=packet.config_version,
        selected_side=packet.selected_side,
        forecast_probability=packet.forecast_probability,
        confidence=packet.confidence,
        payload_json=payload_json,
        paper_only=packet.paper_only,
        report_only=packet.report_only,
        readonly=packet.readonly,
    )


def team_forecast_from_db_row(row: TeamForecastDbRow) -> TeamForecastPacket:
    canonical_row = _canonical_row(TeamForecastDbRow, row)
    return _forecast_from_payload(canonical_row.payload_json)


def team_forecast_evidence_to_db_row(
    packet: TeamForecastEvidencePacket,
    *,
    forecast_id: str,
    config_version: str,
    generated_at: datetime,
) -> TeamForecastEvidenceDbRow:
    if type(packet) is not TeamForecastEvidencePacket:
        raise ValueError("packet must be a TeamForecastEvidencePacket")
    _require_canonical_string("forecast_id", forecast_id)
    _require_canonical_string("config_version", config_version)
    generated_at = _as_utc("generated_at", generated_at)
    payload_json = _evidence_payload_json(
        packet,
        forecast_id=forecast_id,
        config_version=config_version,
        generated_at=generated_at,
    )
    return TeamForecastEvidenceDbRow(
        payload_sha256=_payload_sha256(payload_json),
        generated_at=generated_at,
        forecast_id=forecast_id,
        evidence_id=packet.evidence_id,
        team_id=packet.team_id,
        market_slug=packet.market_slug,
        config_version=config_version,
        source_id=packet.source_id,
        data_timestamp=packet.data_timestamp,
        data_freshness_seconds=packet.data_freshness_seconds,
        evidence_type=packet.evidence_type,
        weight=packet.weight,
        payload_json=payload_json,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def team_forecast_evidence_from_db_row(
    row: TeamForecastEvidenceDbRow,
) -> TeamForecastEvidencePacket:
    canonical_row = _canonical_row(TeamForecastEvidenceDbRow, row)
    return _evidence_from_payload(canonical_row.payload_json)


def team_forecast_outcome_to_db_row(
    outcome: TeamForecastOutcome,
    *,
    config_version: str,
    generated_at: datetime,
) -> TeamForecastOutcomeDbRow:
    if type(outcome) is not TeamForecastOutcome:
        raise ValueError("outcome must be a TeamForecastOutcome")
    _require_canonical_string("config_version", config_version)
    generated_at = _as_utc("generated_at", generated_at)
    payload_json = _outcome_payload_json(
        outcome,
        config_version=config_version,
        generated_at=generated_at,
    )
    return TeamForecastOutcomeDbRow(
        payload_sha256=_payload_sha256(payload_json),
        generated_at=generated_at,
        outcome_id=outcome.outcome_id,
        forecast_id=outcome.forecast_id,
        team_id=outcome.team_id,
        market_slug=outcome.market_slug,
        config_version=config_version,
        resolved_at=outcome.resolved_at,
        actual_outcome=outcome.actual_outcome,
        forecast_error=outcome.forecast_error,
        brier_score=outcome.brier_score,
        paper_pnl=outcome.paper_pnl,
        cost_adjusted_return=outcome.cost_adjusted_return,
        directionally_correct=outcome.directionally_correct,
        profitable_after_cost=outcome.profitable_after_cost,
        resolution_dispute_flag=outcome.resolution_dispute_flag,
        payload_json=payload_json,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def team_forecast_outcome_from_db_row(
    row: TeamForecastOutcomeDbRow,
) -> TeamForecastOutcome:
    canonical_row = _canonical_row(TeamForecastOutcomeDbRow, row)
    return _outcome_from_payload(canonical_row.payload_json)


def _canonical_row(row_type: type[Any], row: Any) -> Any:
    if type(row) is not row_type:
        raise ValueError(f"row must be a {row_type.__name__}")
    return row_type(**{field.name: getattr(row, field.name) for field in fields(row_type)})


def _payload_from_dataclass(value: Any) -> dict[str, Any]:
    payload = json_ready_no_floats(asdict(value))
    if not isinstance(payload, dict):
        raise ValueError("payload_json must be a JSON object")
    return _normalize_payload_json("payload_json", payload)


def _evidence_payload_json(
    packet: TeamForecastEvidencePacket,
    *,
    forecast_id: str,
    config_version: str,
    generated_at: datetime,
) -> dict[str, Any]:
    return _normalize_payload_json(
        "payload_json",
        {
            "forecast_id": forecast_id,
            "config_version": config_version,
            "generated_at": generated_at,
            "evidence": team_forecast_packet_payload(packet),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )


def _outcome_payload_json(
    outcome: TeamForecastOutcome,
    *,
    config_version: str,
    generated_at: datetime,
) -> dict[str, Any]:
    return _normalize_payload_json(
        "payload_json",
        {
            "config_version": config_version,
            "generated_at": generated_at,
            "outcome": _payload_from_dataclass(outcome),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )


def _payload_sha256(payload_json: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_payload_hash(payload_sha256: str, payload_json: dict[str, Any]) -> None:
    if payload_sha256 != _payload_sha256(payload_json):
        raise ValueError("payload_sha256 must match payload_json")


def _route_report_from_payload(payload_json: dict[str, Any]) -> TeamMarketRouteReport:
    try:
        report = from_jsonable(TeamMarketRouteReport, payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"payload_json is not a valid team route report: {exc}") from exc
    if type(report) is not TeamMarketRouteReport:
        raise ValueError("payload_json must recover a TeamMarketRouteReport")
    return report


def _forecast_from_payload(payload_json: dict[str, Any]) -> TeamForecastPacket:
    try:
        packet = from_jsonable(TeamForecastPacket, payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"payload_json is not a valid team forecast packet: {exc}") from exc
    if type(packet) is not TeamForecastPacket:
        raise ValueError("payload_json must recover a TeamForecastPacket")
    return packet


def _evidence_from_payload(payload_json: dict[str, Any]) -> TeamForecastEvidencePacket:
    evidence_payload = _json_object_at(payload_json, "evidence")
    try:
        packet = from_jsonable(TeamForecastEvidencePacket, evidence_payload)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            f"payload_json is not a valid team forecast evidence packet: {exc}",
        ) from exc
    if type(packet) is not TeamForecastEvidencePacket:
        raise ValueError("payload_json must recover a TeamForecastEvidencePacket")
    return packet


def _outcome_from_payload(payload_json: dict[str, Any]) -> TeamForecastOutcome:
    outcome_payload = _json_object_at(payload_json, "outcome")
    try:
        outcome = from_jsonable(TeamForecastOutcome, outcome_payload)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"payload_json is not a valid team forecast outcome: {exc}") from exc
    if type(outcome) is not TeamForecastOutcome:
        raise ValueError("payload_json must recover a TeamForecastOutcome")
    return outcome


def _validate_route_row_matches_payload(row: TeamMarketRouteDbRow) -> None:
    report = _route_report_from_payload(row.payload_json)
    if len(report.rows) != 1:
        raise ValueError("route report must contain exactly one row")
    route = report.rows[0]
    expected_values = {
        "generated_at": report.generated_at,
        "team_id": route.primary_team_id,
        "market_slug": route.market_slug,
        "config_version": report.config_version,
        "condition_id": route.condition_id,
        "category_id": route.category_id,
        "event_template": route.event_template,
        "routing_confidence": route.routing_confidence,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    _compare_expected_values(row, expected_values)
    _require_canonical_payload_json(row.payload_json, _payload_from_dataclass(report))


def _validate_forecast_row_matches_payload(row: TeamForecastDbRow) -> None:
    packet = _forecast_from_payload(row.payload_json)
    expected_values = {
        "generated_at": packet.generated_at,
        "forecast_id": packet.forecast_id,
        "condition_id": packet.condition_id,
        "team_id": packet.team_id,
        "market_slug": packet.market_slug,
        "config_version": packet.config_version,
        "selected_side": packet.selected_side,
        "forecast_probability": packet.forecast_probability,
        "confidence": packet.confidence,
        "paper_only": packet.paper_only,
        "report_only": packet.report_only,
        "readonly": packet.readonly,
    }
    _compare_expected_values(row, expected_values)
    _require_canonical_payload_json(
        row.payload_json,
        team_forecast_packet_payload(packet),
    )


def _validate_evidence_row_matches_payload(row: TeamForecastEvidenceDbRow) -> None:
    _require_json_exact_match(
        "forecast_id",
        row.forecast_id,
        row.payload_json.get("forecast_id", _MISSING),
    )
    _require_json_exact_match(
        "config_version",
        row.config_version,
        row.payload_json.get("config_version", _MISSING),
    )
    _require_json_exact_match(
        "generated_at",
        row.generated_at.isoformat(),
        _json_datetime_string(row.payload_json, "generated_at"),
    )
    packet = _evidence_from_payload(row.payload_json)
    expected_values = {
        "forecast_id": row.payload_json["forecast_id"],
        "config_version": row.payload_json["config_version"],
        "generated_at": _datetime_from_payload(row.payload_json, "generated_at"),
        "evidence_id": packet.evidence_id,
        "team_id": packet.team_id,
        "market_slug": packet.market_slug,
        "source_id": packet.source_id,
        "data_timestamp": packet.data_timestamp,
        "data_freshness_seconds": packet.data_freshness_seconds,
        "evidence_type": packet.evidence_type,
        "weight": packet.weight,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    _compare_expected_values(row, expected_values)
    _require_canonical_payload_json(
        row.payload_json,
        _evidence_payload_json(
            packet,
            forecast_id=row.payload_json["forecast_id"],
            config_version=row.payload_json["config_version"],
            generated_at=_datetime_from_payload(row.payload_json, "generated_at"),
        ),
    )


def _validate_outcome_row_matches_payload(row: TeamForecastOutcomeDbRow) -> None:
    _require_json_exact_match(
        "config_version",
        row.config_version,
        row.payload_json.get("config_version", _MISSING),
    )
    _require_json_exact_match(
        "generated_at",
        row.generated_at.isoformat(),
        _json_datetime_string(row.payload_json, "generated_at"),
    )
    outcome = _outcome_from_payload(row.payload_json)
    expected_values = {
        "generated_at": _datetime_from_payload(row.payload_json, "generated_at"),
        "outcome_id": outcome.outcome_id,
        "forecast_id": outcome.forecast_id,
        "team_id": outcome.team_id,
        "market_slug": outcome.market_slug,
        "config_version": row.payload_json["config_version"],
        "resolved_at": outcome.resolved_at,
        "actual_outcome": outcome.actual_outcome,
        "forecast_error": outcome.forecast_error,
        "brier_score": outcome.brier_score,
        "paper_pnl": outcome.paper_pnl,
        "cost_adjusted_return": outcome.cost_adjusted_return,
        "directionally_correct": outcome.directionally_correct,
        "profitable_after_cost": outcome.profitable_after_cost,
        "resolution_dispute_flag": outcome.resolution_dispute_flag,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    _compare_expected_values(row, expected_values)
    _require_canonical_payload_json(
        row.payload_json,
        _outcome_payload_json(
            outcome,
            config_version=row.payload_json["config_version"],
            generated_at=_datetime_from_payload(row.payload_json, "generated_at"),
        ),
    )


def _compare_expected_values(row: Any, expected_values: dict[str, Any]) -> None:
    for field_name, expected_value in expected_values.items():
        if getattr(row, field_name) != expected_value:
            raise ValueError(f"{field_name} must match payload_json")


def _require_canonical_payload_json(
    payload_json: dict[str, Any],
    expected_payload_json: dict[str, Any],
) -> None:
    if payload_json != expected_payload_json:
        raise ValueError("payload_json must match canonical recovered payload")


def _normalize_payload_json(field_name: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    normalized = _normalize_json_value(field_name, value)
    if not isinstance(normalized, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    reject_unsafe_surface_fields(field_name, normalized)
    return normalized


def _normalize_json_value(field_path: str, value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        raise ValueError(f"{field_path} must not contain float values")
    if isinstance(value, Decimal):
        return str(_normalize_decimal(field_path, value))
    if isinstance(value, datetime):
        return _as_utc(field_path, value).isoformat()
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            normalized[key] = _normalize_json_value(f"{field_path}.{key}", item)
        return normalized
    if isinstance(value, (list, tuple)):
        return [
            _normalize_json_value(f"{field_path}.{index}", item)
            for index, item in enumerate(value)
        ]
    raise ValueError(f"{field_path} contains a non-JSON value")


def _validate_payload_hard_flags(value: Any, field_path: str) -> None:
    if isinstance(value, dict):
        require_explicit = _requires_explicit_hard_flags(field_path)
        for flag_name in _HARD_FLAGS:
            if require_explicit and value.get(flag_name, _MISSING) is not True:
                raise ValueError(f"{field_path} {flag_name} must be explicitly True")
            if flag_name in value and value[flag_name] is not True:
                raise ValueError(f"{field_path} {flag_name} must be True")
        for key, item in value.items():
            _validate_payload_hard_flags(item, f"{field_path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _validate_payload_hard_flags(item, f"{field_path}.{index}")


def _requires_explicit_hard_flags(field_path: str) -> bool:
    if field_path == "payload_json":
        return True
    return field_path.rsplit(".", 1)[-1] in _NESTED_HARD_FLAG_PAYLOAD_KEYS


def _json_object_at(payload_json: dict[str, Any], field_name: str) -> dict[str, Any]:
    value = payload_json.get(field_name)
    if not isinstance(value, dict):
        raise ValueError(f"payload_json.{field_name} must be a JSON object")
    return value


def _json_datetime_string(payload_json: dict[str, Any], field_name: str) -> str:
    value = payload_json.get(field_name, _MISSING)
    if type(value) is not str:
        raise ValueError(f"{field_name} must match payload_json")
    return _as_utc(field_name, datetime.fromisoformat(value)).isoformat()


def _datetime_from_payload(payload_json: dict[str, Any], field_name: str) -> datetime:
    value = payload_json.get(field_name, _MISSING)
    if type(value) is not str:
        raise ValueError(f"{field_name} must match payload_json")
    return _as_utc(field_name, datetime.fromisoformat(value))


def _require_json_exact_match(
    field_name: str,
    actual_value: object,
    expected_value: object,
) -> None:
    if type(actual_value) is not type(expected_value) or actual_value != expected_value:
        raise ValueError(f"{field_name} must match payload_json")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex string")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_choice(
    field_name: str,
    value: object,
    choices: frozenset[str],
) -> None:
    if type(value) is not str or value not in choices:
        raise ValueError(f"{field_name} must be one of {tuple(sorted(choices))}")


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_DECIMAL_QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < Decimal("0") or value > Decimal("1"):
        raise ValueError(f"{field_name} must be between zero and one")
    return _normalize_decimal(field_name, value)


def _normalize_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain canonical strings")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain canonical strings") from exc
    if not items:
        raise ValueError(f"{field_name} must contain canonical strings")
    for item in items:
        _require_canonical_string(field_name, item)
    return items


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
