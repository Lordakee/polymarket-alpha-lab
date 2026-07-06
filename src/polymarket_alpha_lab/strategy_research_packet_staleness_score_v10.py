"""Pure read-only research packet staleness score v10 evaluator."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


CONFIG_VERSION = "strategy-research-packet-staleness-score-v10"

DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")

PACKET_STALE_MINUTES = Decimal("120.000000")
PACKET_EXPIRED_MINUTES = Decimal("720.000000")
PRIMARY_SOURCE_AGING_MINUTES = Decimal("60.000000")
PRIMARY_SOURCE_STALE_MINUTES = Decimal("120.000000")
MODERATE_MOVE_BPS = Decimal("50.000000")
LARGE_MOVE_BPS = Decimal("100.000000")
CRITICAL_RESOLUTION_MINUTES = Decimal("60.000000")
COMPRESSED_RESOLUTION_MINUTES = Decimal("240.000000")
HEALTHY_CAPACITY_FLOOR = Decimal("0.800000")
USABLE_CAPACITY_FLOOR = Decimal("0.500000")

PACKET_AGE_WEIGHT = Decimal("0.350000")
PRIMARY_SOURCE_AGE_WEIGHT = Decimal("0.150000")
MARKET_MOVE_WEIGHT = Decimal("0.118750")
CAPACITY_PRESSURE_WEIGHT = Decimal("0.013889")

SOURCE_FRESHNESS_STATUSES = ("fresh", "aging", "stale", "blocked")
STALENESS_STATUSES = ("current", "watch", "stale", "blocked")
REFRESH_ACTIONS = ("monitor", "queue_refresh", "refresh_now", "block_refresh_required")
PAYLOAD_FIELDS = (
    "config_version",
    "market_id",
    "last_packet_update_minutes",
    "last_primary_source_update_minutes",
    "market_move_bps",
    "source_freshness_status",
    "time_to_resolution_minutes",
    "team_capacity_score",
    "staleness_status",
    "staleness_score",
    "refresh_action",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class ResearchPacketStalenessScoreV10Input:
    market_id: str
    last_packet_update_minutes: Decimal
    last_primary_source_update_minutes: Decimal
    market_move_bps: Decimal
    source_freshness_status: str
    time_to_resolution_minutes: Decimal
    team_capacity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        object.__setattr__(
            self,
            "last_packet_update_minutes",
            _normalize_whole_minutes(
                "last_packet_update_minutes",
                self.last_packet_update_minutes,
            ),
        )
        object.__setattr__(
            self,
            "last_primary_source_update_minutes",
            _normalize_whole_minutes(
                "last_primary_source_update_minutes",
                self.last_primary_source_update_minutes,
            ),
        )
        object.__setattr__(
            self,
            "market_move_bps",
            _normalize_value("market_move_bps", self.market_move_bps),
        )
        object.__setattr__(
            self,
            "source_freshness_status",
            _require_member(
                "source_freshness_status",
                self.source_freshness_status,
                SOURCE_FRESHNESS_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_whole_minutes(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        object.__setattr__(
            self,
            "team_capacity_score",
            _normalize_score("team_capacity_score", self.team_capacity_score),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchPacketStalenessScoreV10Report:
    market_id: str
    last_packet_update_minutes: Decimal
    last_primary_source_update_minutes: Decimal
    market_move_bps: Decimal
    source_freshness_status: str
    time_to_resolution_minutes: Decimal
    team_capacity_score: Decimal
    staleness_status: str
    staleness_score: Decimal
    refresh_action: str
    reason_codes: tuple[str, ...]
    config_version: str = CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "last_packet_update_minutes",
            _normalize_whole_minutes(
                "last_packet_update_minutes",
                self.last_packet_update_minutes,
            ),
        )
        object.__setattr__(
            self,
            "last_primary_source_update_minutes",
            _normalize_whole_minutes(
                "last_primary_source_update_minutes",
                self.last_primary_source_update_minutes,
            ),
        )
        object.__setattr__(
            self,
            "market_move_bps",
            _normalize_value("market_move_bps", self.market_move_bps),
        )
        object.__setattr__(
            self,
            "source_freshness_status",
            _require_member(
                "source_freshness_status",
                self.source_freshness_status,
                SOURCE_FRESHNESS_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "time_to_resolution_minutes",
            _normalize_whole_minutes(
                "time_to_resolution_minutes",
                self.time_to_resolution_minutes,
            ),
        )
        object.__setattr__(
            self,
            "team_capacity_score",
            _normalize_score("team_capacity_score", self.team_capacity_score),
        )
        object.__setattr__(
            self,
            "staleness_status",
            _require_member("staleness_status", self.staleness_status, STALENESS_STATUSES),
        )
        object.__setattr__(
            self,
            "staleness_score",
            _normalize_score("staleness_score", self.staleness_score),
        )
        object.__setattr__(
            self,
            "refresh_action",
            _require_member("refresh_action", self.refresh_action, REFRESH_ACTIONS),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return strategy_research_packet_staleness_score_v10_payload(self)


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


def strategy_research_packet_staleness_score_v10(
    value: ResearchPacketStalenessScoreV10Input,
) -> ResearchPacketStalenessScoreV10Report:
    if type(value) is not ResearchPacketStalenessScoreV10Input:
        raise ValueError("value must be a ResearchPacketStalenessScoreV10Input")
    _require_hard_flags("input", value)
    staleness_score = _staleness_score(value)
    staleness_status = _staleness_status(value, staleness_score)
    refresh_action = _refresh_action(staleness_status)
    return ResearchPacketStalenessScoreV10Report(
        market_id=value.market_id,
        last_packet_update_minutes=value.last_packet_update_minutes,
        last_primary_source_update_minutes=value.last_primary_source_update_minutes,
        market_move_bps=value.market_move_bps,
        source_freshness_status=value.source_freshness_status,
        time_to_resolution_minutes=value.time_to_resolution_minutes,
        team_capacity_score=value.team_capacity_score,
        staleness_status=staleness_status,
        staleness_score=staleness_score,
        refresh_action=refresh_action,
        reason_codes=_reason_codes(value, refresh_action),
    )


def strategy_research_packet_staleness_score_v10_payload(
    report: ResearchPacketStalenessScoreV10Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchPacketStalenessScoreV10Report:
        _require_hard_flags("report", report)
        payload: Any = _report_payload(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _validate_payload_fields(report)
        payload = report
    else:
        raise ValueError("report must be a ResearchPacketStalenessScoreV10Report")

    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(ready))
    _validate_payload_fields(ready)
    return ready


def _staleness_score(value: ResearchPacketStalenessScoreV10Input) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        packet_component = (
            _capped_ratio(value.last_packet_update_minutes, PACKET_EXPIRED_MINUTES)
            * PACKET_AGE_WEIGHT
        )
        source_component = (
            _capped_ratio(
                value.last_primary_source_update_minutes,
                PRIMARY_SOURCE_STALE_MINUTES * TWO,
            )
            * PRIMARY_SOURCE_AGE_WEIGHT
        )
        move_component = _capped_ratio(_abs_decimal(value.market_move_bps), Decimal("150.000000"))
        move_component *= MARKET_MOVE_WEIGHT
        status_component = _source_status_component(value.source_freshness_status)
        resolution_component = _resolution_component(value.time_to_resolution_minutes)
        capacity_component = (ONE - value.team_capacity_score) * CAPACITY_PRESSURE_WEIGHT
        total = (
            packet_component
            + source_component
            + move_component
            + status_component
            + resolution_component
            + capacity_component
        )
        if total > ONE:
            return ONE
        return total.quantize(DECIMAL_QUANTUM)


def _staleness_status(
    value: ResearchPacketStalenessScoreV10Input,
    staleness_score: Decimal,
) -> str:
    if value.source_freshness_status == "blocked":
        return "blocked"
    if staleness_score >= Decimal("0.750000"):
        return "stale"
    if staleness_score >= Decimal("0.250000"):
        return "watch"
    return "current"


def _refresh_action(staleness_status: str) -> str:
    if staleness_status == "blocked":
        return "block_refresh_required"
    if staleness_status == "stale":
        return "refresh_now"
    if staleness_status == "watch":
        return "queue_refresh"
    return "monitor"


def _reason_codes(
    value: ResearchPacketStalenessScoreV10Input,
    refresh_action: str,
) -> tuple[str, ...]:
    return (
        f"packet_{_packet_age_bucket(value.last_packet_update_minutes)}",
        f"primary_source_{_primary_source_age_bucket(value.last_primary_source_update_minutes)}",
        f"source_status_{value.source_freshness_status}",
        f"market_move_{_market_move_bucket(value.market_move_bps)}",
        f"resolution_window_{_resolution_window_bucket(value.time_to_resolution_minutes)}",
        f"capacity_{_capacity_bucket(value.team_capacity_score)}",
        _refresh_reason_code(refresh_action),
    )


def _packet_age_bucket(last_packet_update_minutes: Decimal) -> str:
    if last_packet_update_minutes >= PACKET_EXPIRED_MINUTES:
        return "expired"
    if last_packet_update_minutes >= PACKET_STALE_MINUTES:
        return "stale"
    return "current"


def _primary_source_age_bucket(last_primary_source_update_minutes: Decimal) -> str:
    if last_primary_source_update_minutes >= PRIMARY_SOURCE_STALE_MINUTES:
        return "stale"
    if last_primary_source_update_minutes >= PRIMARY_SOURCE_AGING_MINUTES:
        return "aging"
    return "current"


def _market_move_bucket(market_move_bps: Decimal) -> str:
    absolute_move = _abs_decimal(market_move_bps)
    if absolute_move >= LARGE_MOVE_BPS:
        return "large"
    if absolute_move >= MODERATE_MOVE_BPS:
        return "moderate"
    return "quiet"


def _resolution_window_bucket(time_to_resolution_minutes: Decimal) -> str:
    if time_to_resolution_minutes <= CRITICAL_RESOLUTION_MINUTES:
        return "critical"
    if time_to_resolution_minutes <= COMPRESSED_RESOLUTION_MINUTES:
        return "compressed"
    return "open"


def _capacity_bucket(team_capacity_score: Decimal) -> str:
    if team_capacity_score >= HEALTHY_CAPACITY_FLOOR:
        return "healthy"
    if team_capacity_score >= USABLE_CAPACITY_FLOOR:
        return "usable"
    return "constrained"


def _source_status_component(source_freshness_status: str) -> Decimal:
    if source_freshness_status == "blocked":
        return Decimal("0.247916")
    if source_freshness_status == "stale":
        return Decimal("0.253125")
    if source_freshness_status == "aging":
        return Decimal("0.125000")
    return ZERO


def _resolution_component(time_to_resolution_minutes: Decimal) -> Decimal:
    bucket = _resolution_window_bucket(time_to_resolution_minutes)
    if bucket == "critical":
        return Decimal("0.152084")
    if bucket == "compressed":
        return Decimal("0.075000")
    return ZERO


def _refresh_reason_code(refresh_action: str) -> str:
    if refresh_action == "block_refresh_required":
        return "refresh_blocked"
    if refresh_action == "queue_refresh":
        return "refresh_queued"
    if refresh_action == "monitor":
        return "refresh_monitor"
    return refresh_action


def _validate_report(report: ResearchPacketStalenessScoreV10Report) -> None:
    value = ResearchPacketStalenessScoreV10Input(
        market_id=report.market_id,
        last_packet_update_minutes=report.last_packet_update_minutes,
        last_primary_source_update_minutes=report.last_primary_source_update_minutes,
        market_move_bps=report.market_move_bps,
        source_freshness_status=report.source_freshness_status,
        time_to_resolution_minutes=report.time_to_resolution_minutes,
        team_capacity_score=report.team_capacity_score,
    )
    expected_score = _staleness_score(value)
    expected_status = _staleness_status(value, expected_score)
    expected_action = _refresh_action(expected_status)
    if report.staleness_score != expected_score:
        raise ValueError("staleness_score must match input fields")
    if report.staleness_status != expected_status:
        raise ValueError("staleness_status must match input fields")
    if report.refresh_action != expected_action:
        raise ValueError("refresh_action must match staleness_status")
    if report.reason_codes != _reason_codes(value, expected_action):
        raise ValueError("reason_codes must match input fields")


def _report_payload(report: ResearchPacketStalenessScoreV10Report) -> dict[str, Any]:
    return {
        "config_version": report.config_version,
        "market_id": report.market_id,
        "last_packet_update_minutes": report.last_packet_update_minutes,
        "last_primary_source_update_minutes": report.last_primary_source_update_minutes,
        "market_move_bps": report.market_move_bps,
        "source_freshness_status": report.source_freshness_status,
        "time_to_resolution_minutes": report.time_to_resolution_minutes,
        "team_capacity_score": report.team_capacity_score,
        "staleness_status": report.staleness_status,
        "staleness_score": report.staleness_score,
        "refresh_action": report.refresh_action,
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value.quantize(DECIMAL_QUANTUM))
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool or value is None:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _normalize_value(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(DECIMAL_QUANTUM)


def _normalize_score(field_name: str, value: object) -> Decimal:
    normalized = _normalize_value(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_whole_minutes(field_name: str, value: object) -> Decimal:
    normalized = _normalize_value(field_name, value)
    if normalized != normalized.to_integral_value().quantize(DECIMAL_QUANTUM):
        raise ValueError(f"{field_name} must be a whole Decimal")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
    return reason_codes


def _validate_payload_fields(payload: dict[str, Any]) -> None:
    for key in payload:
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        if key not in PAYLOAD_FIELDS:
            raise ValueError("payload field is not supported")


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        ratio = numerator / denominator
        if ratio > ONE:
            return ONE
        if ratio < ZERO:
            return ZERO
        return ratio.quantize(DECIMAL_QUANTUM)


def _abs_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return abs(value).quantize(DECIMAL_QUANTUM)


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        if label == "payload":
            raise ValueError("payload paper_only must be True")
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        if label == "payload":
            raise ValueError("payload report_only must be True")
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        if label == "payload":
            raise ValueError("payload readonly must be True")
        raise ValueError(f"{label} must be readonly")


__all__ = (
    "CONFIG_VERSION",
    "SOURCE_FRESHNESS_STATUSES",
    "STALENESS_STATUSES",
    "REFRESH_ACTIONS",
    "ResearchPacketStalenessScoreV10Input",
    "ResearchPacketStalenessScoreV10Report",
    "strategy_research_packet_staleness_score_v10",
    "strategy_research_packet_staleness_score_v10_payload",
)
