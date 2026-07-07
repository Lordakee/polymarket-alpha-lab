"""Read-only research packet information gap detector for Phase 1 review."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_PACKET_LIVE_INFORMATION_GAP_CONFIG_VERSION = (
    "research-packet-live-information-gap-v2"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")

REPORT_STATUSES = ("pass", "watch", "blocked")
ROW_STATUSES = ("pass", "watch", "blocked")
ROW_REASON_CODES = (
    "information_gap_clear",
    "source_missing",
    "official_source_missing",
    "source_stale",
    "official_source_stale",
    "event_velocity_high",
    "contradiction_count_elevated",
    "market_probability_moved",
    "resolution_horizon_near",
)
REPORT_REASON_CODES = (
    "information_gap_clear",
    "information_gap_watch",
    "information_gap_blocked",
    "source_missing",
    "official_source_missing",
    "source_stale",
    "official_source_stale",
    "contradiction_count_elevated",
    "market_probability_moved",
    "resolution_horizon_near",
)
UNSAFE_PUBLIC_TERMS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)
PUBLIC_VALUE_TERM_ALLOWLIST_KEYS = frozenset(("config_version",))
SAFETY_FLAG_NAMES = frozenset(("paper_only", "report_only", "readonly"))


@dataclass(frozen=True)
class ResearchPacketLiveInformationGapConfig:
    config_version: str = DEFAULT_RESEARCH_PACKET_LIVE_INFORMATION_GAP_CONFIG_VERSION
    max_source_age_seconds: Decimal = Decimal("1800")
    max_official_source_age_seconds: Decimal = Decimal("1800")
    high_event_velocity_threshold: Decimal = Decimal("0.700000")
    contradiction_count_threshold: Decimal = Decimal("1")
    market_probability_movement_threshold: Decimal = Decimal("0.050000")
    near_resolution_horizon_seconds: Decimal = Decimal("21600")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string(
            "config_version",
            self.config_version,
            allow_public_terms=True,
        )
        for field_name in (
            "max_source_age_seconds",
            "max_official_source_age_seconds",
            "near_resolution_horizon_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "high_event_velocity_threshold",
            _normalize_probability(
                "high_event_velocity_threshold",
                self.high_event_velocity_threshold,
            ),
        )
        object.__setattr__(
            self,
            "contradiction_count_threshold",
            _normalize_positive_count(
                "contradiction_count_threshold",
                self.contradiction_count_threshold,
            ),
        )
        object.__setattr__(
            self,
            "market_probability_movement_threshold",
            _normalize_probability(
                "market_probability_movement_threshold",
                self.market_probability_movement_threshold,
            ),
        )
        _require_hard_flags("ResearchPacketLiveInformationGapConfig", self)


@dataclass(frozen=True)
class ResearchPacketLiveInformationGapInput:
    packet_id: str
    event_title: str
    latest_source_at: datetime | None
    latest_official_source_at: datetime | None
    event_velocity_score: Decimal
    contradiction_count: Decimal
    market_probability_movement: Decimal
    resolution_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("packet_id", self.packet_id)
        _require_canonical_string("event_title", self.event_title)
        object.__setattr__(
            self,
            "latest_source_at",
            _as_optional_utc("latest_source_at", self.latest_source_at),
        )
        object.__setattr__(
            self,
            "latest_official_source_at",
            _as_optional_utc(
                "latest_official_source_at",
                self.latest_official_source_at,
            ),
        )
        object.__setattr__(
            self,
            "event_velocity_score",
            _normalize_probability("event_velocity_score", self.event_velocity_score),
        )
        object.__setattr__(
            self,
            "contradiction_count",
            _normalize_nonnegative_count("contradiction_count", self.contradiction_count),
        )
        object.__setattr__(
            self,
            "market_probability_movement",
            _normalize_probability(
                "market_probability_movement",
                self.market_probability_movement,
            ),
        )
        object.__setattr__(
            self,
            "resolution_at",
            _as_utc("resolution_at", self.resolution_at),
        )
        _require_hard_flags("ResearchPacketLiveInformationGapInput", self)


@dataclass(frozen=True)
class ResearchPacketLiveInformationGapRow:
    packet_id: str
    event_title: str
    latest_source_at: datetime | None
    latest_official_source_at: datetime | None
    source_age_seconds: Decimal | None
    official_source_age_seconds: Decimal | None
    event_velocity_score: Decimal
    contradiction_count: Decimal
    market_probability_movement: Decimal
    resolution_at: datetime
    resolution_horizon_seconds: Decimal
    information_gap_score: Decimal
    gap_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("packet_id", self.packet_id)
        _require_canonical_string("event_title", self.event_title)
        object.__setattr__(
            self,
            "latest_source_at",
            _as_optional_utc("latest_source_at", self.latest_source_at),
        )
        object.__setattr__(
            self,
            "latest_official_source_at",
            _as_optional_utc(
                "latest_official_source_at",
                self.latest_official_source_at,
            ),
        )
        for field_name in ("source_age_seconds", "official_source_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_count(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "event_velocity_score",
            _normalize_probability("event_velocity_score", self.event_velocity_score),
        )
        object.__setattr__(
            self,
            "contradiction_count",
            _normalize_nonnegative_count("contradiction_count", self.contradiction_count),
        )
        object.__setattr__(
            self,
            "market_probability_movement",
            _normalize_probability(
                "market_probability_movement",
                self.market_probability_movement,
            ),
        )
        object.__setattr__(self, "resolution_at", _as_utc("resolution_at", self.resolution_at))
        object.__setattr__(
            self,
            "resolution_horizon_seconds",
            _normalize_nonnegative_count(
                "resolution_horizon_seconds",
                self.resolution_horizon_seconds,
            ),
        )
        object.__setattr__(
            self,
            "information_gap_score",
            _normalize_probability("information_gap_score", self.information_gap_score),
        )
        _require_member("gap_status", self.gap_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("ResearchPacketLiveInformationGapRow", self)
        _validate_digest(self)


@dataclass(frozen=True)
class ResearchPacketLiveInformationGapReport:
    generated_at: datetime
    config_version: str
    packet_count: Decimal
    pass_packet_count: Decimal
    watch_packet_count: Decimal
    blocked_packet_count: Decimal
    missing_source_count: Decimal
    missing_official_source_count: Decimal
    stale_source_count: Decimal
    stale_official_source_count: Decimal
    contradiction_gap_count: Decimal
    market_probability_movement_gap_count: Decimal
    near_resolution_count: Decimal
    max_information_gap_score: Decimal
    max_source_age_seconds: Decimal | None
    min_resolution_horizon_seconds: Decimal | None
    report_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchPacketLiveInformationGapRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string(
            "config_version",
            self.config_version,
            allow_public_terms=True,
        )
        for field_name in (
            "packet_count",
            "pass_packet_count",
            "watch_packet_count",
            "blocked_packet_count",
            "missing_source_count",
            "missing_official_source_count",
            "stale_source_count",
            "stale_official_source_count",
            "contradiction_gap_count",
            "market_probability_movement_gap_count",
            "near_resolution_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_information_gap_score",
            _normalize_probability("max_information_gap_score", self.max_information_gap_score),
        )
        for field_name in ("max_source_age_seconds", "min_resolution_horizon_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("ResearchPacketLiveInformationGapReport", self)
        _validate_digest(self)
        _validate_report_counts(self)


def build_research_packet_live_information_gap_report(
    inputs: list[ResearchPacketLiveInformationGapInput]
    | tuple[ResearchPacketLiveInformationGapInput, ...],
    *,
    config: ResearchPacketLiveInformationGapConfig,
    generated_at: datetime,
) -> ResearchPacketLiveInformationGapReport:
    if type(config) is not ResearchPacketLiveInformationGapConfig:
        raise ValueError("config must be a ResearchPacketLiveInformationGapConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    _validate_input_times(normalized_inputs, generated_at_utc)
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    row,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for row in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchPacketLiveInformationGapReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        packet_count=_count(len(rows)),
        pass_packet_count=_status_count(rows, "pass"),
        watch_packet_count=_status_count(rows, "watch"),
        blocked_packet_count=_status_count(rows, "blocked"),
        missing_source_count=_reason_count(rows, "source_missing"),
        missing_official_source_count=_reason_count(rows, "official_source_missing"),
        stale_source_count=_reason_count(rows, "source_stale"),
        stale_official_source_count=_reason_count(rows, "official_source_stale"),
        contradiction_gap_count=_reason_count(rows, "contradiction_count_elevated"),
        market_probability_movement_gap_count=_reason_count(
            rows,
            "market_probability_moved",
        ),
        near_resolution_count=_reason_count(rows, "resolution_horizon_near"),
        max_information_gap_score=_max_score(rows),
        max_source_age_seconds=_max_optional_count(
            tuple(row.source_age_seconds for row in rows),
        ),
        min_resolution_horizon_seconds=_min_optional_count(
            tuple(row.resolution_horizon_seconds for row in rows),
        ),
        report_status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_packet_live_information_gap_report_payload(
    report: ResearchPacketLiveInformationGapReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchPacketLiveInformationGapReport:
        _require_hard_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchPacketLiveInformationGapReport or payload")
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_payload_flags(payload)
    _reject_unsafe_public_payload("payload", payload)
    _validate_payload_digest(payload)
    return payload


def _normalize_inputs(
    inputs: list[ResearchPacketLiveInformationGapInput]
    | tuple[ResearchPacketLiveInformationGapInput, ...],
) -> tuple[ResearchPacketLiveInformationGapInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    seen_packet_ids: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchPacketLiveInformationGapInput:
            raise ValueError("inputs must contain ResearchPacketLiveInformationGapInput values")
        _require_hard_flags("input", row)
        if row.packet_id in seen_packet_ids:
            raise ValueError("inputs must not contain duplicate packet_id values")
        seen_packet_ids.add(row.packet_id)
    return normalized


def _validate_input_times(
    rows: tuple[ResearchPacketLiveInformationGapInput, ...],
    generated_at: datetime,
) -> None:
    for row in rows:
        for value in (row.latest_source_at, row.latest_official_source_at):
            if value is not None and value > generated_at:
                raise ValueError("timestamps must not be after generated_at")
        if row.resolution_at < generated_at:
            raise ValueError("resolution_at must not be before generated_at")


def _row_from_input(
    row: ResearchPacketLiveInformationGapInput,
    *,
    config: ResearchPacketLiveInformationGapConfig,
    generated_at: datetime,
) -> ResearchPacketLiveInformationGapRow:
    source_age_seconds = _age_seconds(row.latest_source_at, generated_at)
    official_source_age_seconds = _age_seconds(row.latest_official_source_at, generated_at)
    resolution_horizon_seconds = _duration_seconds(generated_at, row.resolution_at)
    reason_codes = _row_reason_codes(
        row,
        config=config,
        source_age_seconds=source_age_seconds,
        official_source_age_seconds=official_source_age_seconds,
        resolution_horizon_seconds=resolution_horizon_seconds,
    )
    information_gap_score = _information_gap_score(reason_codes)
    return ResearchPacketLiveInformationGapRow(
        packet_id=row.packet_id,
        event_title=row.event_title,
        latest_source_at=row.latest_source_at,
        latest_official_source_at=row.latest_official_source_at,
        source_age_seconds=source_age_seconds,
        official_source_age_seconds=official_source_age_seconds,
        event_velocity_score=row.event_velocity_score,
        contradiction_count=row.contradiction_count,
        market_probability_movement=row.market_probability_movement,
        resolution_at=row.resolution_at,
        resolution_horizon_seconds=resolution_horizon_seconds,
        information_gap_score=information_gap_score,
        gap_status=_row_status(reason_codes, information_gap_score),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    row: ResearchPacketLiveInformationGapInput,
    *,
    config: ResearchPacketLiveInformationGapConfig,
    source_age_seconds: Decimal | None,
    official_source_age_seconds: Decimal | None,
    resolution_horizon_seconds: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if source_age_seconds is None:
        reason_codes.append("source_missing")
    elif source_age_seconds > config.max_source_age_seconds:
        reason_codes.append("source_stale")
    if official_source_age_seconds is None:
        reason_codes.append("official_source_missing")
    elif official_source_age_seconds > config.max_official_source_age_seconds:
        reason_codes.append("official_source_stale")
    if row.event_velocity_score >= config.high_event_velocity_threshold:
        reason_codes.append("event_velocity_high")
    if row.contradiction_count >= config.contradiction_count_threshold:
        reason_codes.append("contradiction_count_elevated")
    if row.market_probability_movement >= config.market_probability_movement_threshold:
        reason_codes.append("market_probability_moved")
    if resolution_horizon_seconds <= config.near_resolution_horizon_seconds:
        reason_codes.append("resolution_horizon_near")
    if not reason_codes:
        reason_codes.append("information_gap_clear")
    return tuple(reason_codes)


def _information_gap_score(reason_codes: tuple[str, ...]) -> Decimal:
    if reason_codes == ("information_gap_clear",):
        return ZERO_RATIO
    score = ZERO_RATIO
    for reason_code in reason_codes:
        if reason_code in (
            "source_missing",
            "official_source_missing",
            "source_stale",
            "official_source_stale",
        ):
            score += Decimal("0.250000")
        elif reason_code in (
            "event_velocity_high",
            "contradiction_count_elevated",
            "market_probability_moved",
            "resolution_horizon_near",
        ):
            score += Decimal("0.150000")
    if score > ONE_RATIO:
        return ONE_RATIO
    return _quantize_ratio(score)


def _row_status(
    reason_codes: tuple[str, ...],
    information_gap_score: Decimal,
) -> str:
    if any(
        reason_code in reason_codes
        for reason_code in (
            "source_missing",
            "official_source_missing",
            "source_stale",
            "official_source_stale",
        )
    ):
        return "blocked"
    if information_gap_score >= Decimal("0.750000"):
        return "blocked"
    if information_gap_score > ZERO_RATIO:
        return "watch"
    return "pass"


def _row_sort_key(row: ResearchPacketLiveInformationGapRow) -> tuple[Decimal, Decimal, Decimal, str]:
    status_weight = {
        "blocked": Decimal("0"),
        "watch": Decimal("1"),
        "pass": Decimal("2"),
    }[row.gap_status]
    return (
        status_weight,
        ONE_RATIO - row.information_gap_score,
        row.resolution_horizon_seconds,
        row.packet_id,
    )


def _status_count(rows: tuple[ResearchPacketLiveInformationGapRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.gap_status == status))


def _reason_count(
    rows: tuple[ResearchPacketLiveInformationGapRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_score(rows: tuple[ResearchPacketLiveInformationGapRow, ...]) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return max(row.information_gap_score for row in rows)


def _report_status(rows: tuple[ResearchPacketLiveInformationGapRow, ...]) -> str:
    if any(row.gap_status == "blocked" for row in rows):
        return "blocked"
    if any(row.gap_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchPacketLiveInformationGapRow, ...],
) -> tuple[str, ...]:
    status = _report_status(rows)
    reason_codes: list[str] = [f"information_gap_{status}" if status != "pass" else "information_gap_clear"]
    for reason_code in (
        "source_missing",
        "official_source_missing",
        "source_stale",
        "official_source_stale",
        "contradiction_count_elevated",
        "market_probability_moved",
        "resolution_horizon_near",
    ):
        if any(reason_code in row.reason_codes for row in rows):
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _normalize_rows(
    rows: tuple[ResearchPacketLiveInformationGapRow, ...],
) -> tuple[ResearchPacketLiveInformationGapRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_packet_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketLiveInformationGapRow:
            raise ValueError("rows must contain ResearchPacketLiveInformationGapRow values")
        _require_hard_flags("row", row)
        if row.packet_id in seen_packet_ids:
            raise ValueError("rows must not contain duplicate packet_id values")
        seen_packet_ids.add(row.packet_id)
    return rows


def _validate_report_counts(report: ResearchPacketLiveInformationGapReport) -> None:
    if report.pass_packet_count + report.watch_packet_count + report.blocked_packet_count != report.packet_count:
        raise ValueError("status packet counts must equal packet_count")
    if report.packet_count != _count(len(report.rows)):
        raise ValueError("packet_count must equal row count")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _validate_digest(value: object) -> None:
    current_digest = getattr(value, "derived_validation_digest")
    if current_digest != "":
        _require_digest(current_digest)
    expected_digest = _derived_validation_digest(value)
    if current_digest == "":
        object.__setattr__(value, "derived_validation_digest", expected_digest)
        return
    if current_digest != expected_digest:
        raise ValueError("derived_validation_digest mismatch")


def _derived_validation_digest(value: object) -> str:
    payload = _json_ready(value, include_digest=False)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    if "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest is required")
    current_digest = payload["derived_validation_digest"]
    if type(current_digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _require_digest(current_digest)
    payload_without_digest = dict(payload)
    payload_without_digest["derived_validation_digest"] = ""
    expected_digest = _derived_validation_digest_from_payload(payload_without_digest)
    if current_digest != expected_digest:
        raise ValueError("derived_validation_digest mismatch")


def _derived_validation_digest_from_payload(payload: dict[str, Any]) -> str:
    canonical = _copy_without_digest(payload)
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _copy_without_digest(value: Any) -> Any:
    if isinstance(value, dict):
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if key == "derived_validation_digest":
                continue
            copied[key] = _copy_without_digest(item)
        return copied
    if isinstance(value, list):
        return [_copy_without_digest(item) for item in value]
    return value


def _require_digest(value: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("derived_validation_digest must be a lowercase sha256 hex string")


def _json_ready(value: Any, *, include_digest: bool = True) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        ready: dict[str, Any] = {}
        for field in fields(value):
            if not include_digest and field.name == "derived_validation_digest":
                continue
            ready[field.name] = _json_ready(
                getattr(value, field.name),
                include_digest=include_digest,
            )
        return ready
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return format(value, "f")
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("payload must not contain floats")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        ready = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if not include_digest and key == "derived_validation_digest":
                continue
            ready[key] = _json_ready(item, include_digest=include_digest)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item, include_digest=include_digest) for item in value]
    if isinstance(value, list):
        return [_json_ready(item, include_digest=include_digest) for item in value]
    raise ValueError("payload contains unsupported value")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if _contains_unsafe_public_term(key):
                raise ValueError(f"unsafe public key in {label}: {key}")
            item_path = key if path == "" else f"{path}.{key}"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{path}[{index}]")
        return
    if isinstance(value, str) and _path_leaf(path) not in PUBLIC_VALUE_TERM_ALLOWLIST_KEYS:
        if _contains_unsafe_public_term(value):
            raise ValueError(f"unsafe public value in {label}: {path}")


def _path_leaf(path: str) -> str:
    if "." in path:
        return path.rsplit(".", 1)[1]
    return path


def _contains_unsafe_public_term(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in UNSAFE_PUBLIC_TERMS)


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in SAFETY_FLAG_NAMES:
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for payload")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in SAFETY_FLAG_NAMES:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_canonical_string(
    field_name: str,
    value: str,
    *,
    allow_public_terms: bool = False,
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() == "":
        raise ValueError(f"{field_name} must not be blank")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    if not allow_public_terms and _contains_unsafe_public_term(value):
        raise ValueError(f"unsafe public value in {field_name}")
    return value


def _require_member(field_name: str, value: str, allowed_values: tuple[str, ...]) -> None:
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed_values)}")


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized: list[str] = []
    seen_values: set[str] = set()
    for value in values:
        _require_canonical_string(field_name, value)
        _require_member(field_name, value, allowed_values)
        if value in seen_values:
            raise ValueError(f"{field_name} must not contain duplicates")
        normalized.append(value)
        seen_values.add(value)
    return tuple(normalized)


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_probability(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value, RATIO_QUANTUM)
    if normalized < ZERO_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_decimal(field_name, value, COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_optional_nonnegative_count(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_count(field_name, value)


def _normalize_decimal(field_name: str, value: Decimal, quantum: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(quantum)
    if normalized != value:
        raise ValueError(f"{field_name} must align to {quantum}")
    return normalized


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _age_seconds(value: datetime | None, generated_at: datetime) -> Decimal | None:
    if value is None:
        return None
    return _duration_seconds(value, generated_at)


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    if delta.microseconds:
        seconds += Decimal(delta.microseconds) / Decimal("1000000")
    return _normalize_nonnegative_count("duration_seconds", seconds)


def _max_optional_count(values: tuple[Decimal | None, ...]) -> Decimal | None:
    present = tuple(value for value in values if value is not None)
    if not present:
        return None
    return max(present)


def _min_optional_count(values: tuple[Decimal | None, ...]) -> Decimal | None:
    present = tuple(value for value in values if value is not None)
    if not present:
        return None
    return min(present)


__all__ = (
    "DEFAULT_RESEARCH_PACKET_LIVE_INFORMATION_GAP_CONFIG_VERSION",
    "ResearchPacketLiveInformationGapConfig",
    "ResearchPacketLiveInformationGapInput",
    "ResearchPacketLiveInformationGapReport",
    "ResearchPacketLiveInformationGapRow",
    "build_research_packet_live_information_gap_report",
    "research_packet_live_information_gap_report_payload",
)
