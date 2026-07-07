"""Phase 1 report-only SLA snapshot for market-context refresh freshness."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_PACKET_MARKET_CONTEXT_REFRESH_SLA_V2_CONFIG_VERSION = (
    "research-packet-market-context-refresh-sla-v2"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_ROW_STATUSES = frozenset(("pass", "watch", "blocked"))
_REPORT_STATUSES = _ROW_STATUSES
_CLOSE_URGENCIES = frozenset(("normal", "near", "urgent", "elapsed"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TERMS = (
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
_REASON_CODE_SEQUENCE = (
    "market_context_refresh_empty",
    "market_context_refresh_fresh",
    "price_move_age_stale",
    "latest_source_age_stale",
    "official_update_age_stale",
    "liquidity_context_age_stale",
    "contradiction_follow_up_missing",
    "contradiction_follow_up_age_stale",
    "close_urgency_near",
    "close_urgency_urgent",
    "close_urgency_elapsed",
    "market_context_refresh_watch",
    "market_context_refresh_blocked",
)


@dataclass(frozen=True)
class ResearchPacketMarketContextRefreshSlaV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_MARKET_CONTEXT_REFRESH_SLA_V2_CONFIG_VERSION
    )
    price_move_max_age_seconds: Decimal = Decimal("900.000000")
    latest_source_max_age_seconds: Decimal = Decimal("1800.000000")
    official_update_max_age_seconds: Decimal = Decimal("3600.000000")
    liquidity_context_max_age_seconds: Decimal = Decimal("1800.000000")
    contradiction_follow_up_max_age_seconds: Decimal = Decimal("7200.000000")
    close_urgent_seconds: Decimal = Decimal("3600.000000")
    close_watch_seconds: Decimal = Decimal("21600.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketMarketContextRefreshSlaV2Config:
            raise TypeError(
                "ResearchPacketMarketContextRefreshSlaV2Config does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketMarketContextRefreshSlaV2Config:
            raise ValueError(
                "config must be exactly ResearchPacketMarketContextRefreshSlaV2Config",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_MARKET_CONTEXT_REFRESH_SLA_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "price_move_max_age_seconds",
            "latest_source_max_age_seconds",
            "official_update_max_age_seconds",
            "liquidity_context_max_age_seconds",
            "contradiction_follow_up_max_age_seconds",
            "close_urgent_seconds",
            "close_watch_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_seconds_decimal(field_name, getattr(self, field_name)),
            )
        if self.close_urgent_seconds > self.close_watch_seconds:
            raise ValueError("close_urgent_seconds must not exceed close_watch_seconds")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchPacketMarketContextRefreshSlaV2Observation:
    packet_id: str
    market_id: str
    price_move_at: datetime
    latest_source_at: datetime
    official_update_at: datetime
    liquidity_context_at: datetime
    market_closes_at: datetime
    contradiction_detected_at: datetime | None = None
    contradiction_follow_up_at: datetime | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketMarketContextRefreshSlaV2Observation:
            raise TypeError(
                "ResearchPacketMarketContextRefreshSlaV2Observation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketMarketContextRefreshSlaV2Observation:
            raise ValueError(
                "observation must be exactly "
                "ResearchPacketMarketContextRefreshSlaV2Observation",
            )
        _require_public_identifier("packet_id", self.packet_id)
        _require_public_identifier("market_id", self.market_id)
        for field_name in (
            "price_move_at",
            "latest_source_at",
            "official_update_at",
            "liquidity_context_at",
            "market_closes_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "contradiction_detected_at",
            _as_optional_utc(
                "contradiction_detected_at",
                self.contradiction_detected_at,
            ),
        )
        object.__setattr__(
            self,
            "contradiction_follow_up_at",
            _as_optional_utc(
                "contradiction_follow_up_at",
                self.contradiction_follow_up_at,
            ),
        )
        if (
            self.contradiction_detected_at is None
            and self.contradiction_follow_up_at is not None
        ):
            raise ValueError(
                "contradiction_follow_up_at requires contradiction_detected_at",
            )
        if (
            self.contradiction_detected_at is not None
            and self.contradiction_follow_up_at is not None
            and self.contradiction_follow_up_at < self.contradiction_detected_at
        ):
            raise ValueError(
                "contradiction_follow_up_at must not be before "
                "contradiction_detected_at",
            )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchPacketMarketContextRefreshSlaV2Row:
    packet_id: str
    market_id: str
    row_status: str
    price_move_age_seconds: Decimal
    latest_source_age_seconds: Decimal
    official_update_age_seconds: Decimal
    liquidity_context_age_seconds: Decimal
    contradiction_follow_up_age_seconds: Decimal
    seconds_to_close: Decimal
    close_urgency: str
    price_move_stale: bool
    latest_source_stale: bool
    official_update_stale: bool
    liquidity_context_stale: bool
    contradiction_follow_up_stale: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketMarketContextRefreshSlaV2Row:
            raise TypeError(
                "ResearchPacketMarketContextRefreshSlaV2Row does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketMarketContextRefreshSlaV2Row:
            raise ValueError(
                "row must be exactly ResearchPacketMarketContextRefreshSlaV2Row",
            )
        _require_public_identifier("packet_id", self.packet_id)
        _require_public_identifier("market_id", self.market_id)
        _require_member("row_status", self.row_status, _ROW_STATUSES)
        for field_name in (
            "price_move_age_seconds",
            "latest_source_age_seconds",
            "official_update_age_seconds",
            "liquidity_context_age_seconds",
            "contradiction_follow_up_age_seconds",
            "seconds_to_close",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_seconds_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("close_urgency", self.close_urgency, _CLOSE_URGENCIES)
        for field_name in (
            "price_move_stale",
            "latest_source_stale",
            "official_update_stale",
            "liquidity_context_stale",
            "contradiction_follow_up_stale",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_bool(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchPacketMarketContextRefreshSlaV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    market_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    price_move_stale_count: Decimal
    latest_source_stale_count: Decimal
    official_update_stale_count: Decimal
    liquidity_context_stale_count: Decimal
    contradiction_follow_up_stale_count: Decimal
    close_urgent_count: Decimal
    oldest_price_move_age_seconds: Decimal
    oldest_latest_source_age_seconds: Decimal
    oldest_official_update_age_seconds: Decimal
    oldest_liquidity_context_age_seconds: Decimal
    oldest_contradiction_follow_up_age_seconds: Decimal
    minimum_seconds_to_close: Decimal
    rows: tuple[ResearchPacketMarketContextRefreshSlaV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketMarketContextRefreshSlaV2Report:
            raise TypeError(
                "ResearchPacketMarketContextRefreshSlaV2Report does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketMarketContextRefreshSlaV2Report:
            raise ValueError(
                "report must be exactly ResearchPacketMarketContextRefreshSlaV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_MARKET_CONTEXT_REFRESH_SLA_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_member("report_status", self.report_status, _REPORT_STATUSES)
        for field_name in (
            "market_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "price_move_stale_count",
            "latest_source_stale_count",
            "official_update_stale_count",
            "liquidity_context_stale_count",
            "contradiction_follow_up_stale_count",
            "close_urgent_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "oldest_price_move_age_seconds",
            "oldest_latest_source_age_seconds",
            "oldest_official_update_age_seconds",
            "oldest_liquidity_context_age_seconds",
            "oldest_contradiction_follow_up_age_seconds",
            "minimum_seconds_to_close",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_seconds_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
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
            "ResearchPacketMarketContextRefreshSlaV2Report.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_packet_market_context_refresh_sla_v2_report(
    observations: Sequence[ResearchPacketMarketContextRefreshSlaV2Observation],
    *,
    generated_at: datetime,
    config: ResearchPacketMarketContextRefreshSlaV2Config | None = None,
) -> ResearchPacketMarketContextRefreshSlaV2Report:
    """Build a local, deterministic Phase 1 market-context refresh SLA report."""

    if config is None:
        config = ResearchPacketMarketContextRefreshSlaV2Config()
    if type(config) is not ResearchPacketMarketContextRefreshSlaV2Config:
        raise ValueError(
            "config must be a ResearchPacketMarketContextRefreshSlaV2Config",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    _validate_observation_times(normalized_observations, generated_at_utc)
    rows = _build_rows(normalized_observations, generated_at_utc, config)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "report_status": _report_status(rows),
        "market_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "blocked_count": _decimal_count(_status_count(rows, "blocked")),
        "price_move_stale_count": _decimal_count(
            _true_count(tuple(row.price_move_stale for row in rows)),
        ),
        "latest_source_stale_count": _decimal_count(
            _true_count(tuple(row.latest_source_stale for row in rows)),
        ),
        "official_update_stale_count": _decimal_count(
            _true_count(tuple(row.official_update_stale for row in rows)),
        ),
        "liquidity_context_stale_count": _decimal_count(
            _true_count(tuple(row.liquidity_context_stale for row in rows)),
        ),
        "contradiction_follow_up_stale_count": _decimal_count(
            _true_count(tuple(row.contradiction_follow_up_stale for row in rows)),
        ),
        "close_urgent_count": _decimal_count(
            _true_count(tuple(row.close_urgency == "urgent" for row in rows)),
        ),
        "oldest_price_move_age_seconds": _max_decimal(
            tuple(row.price_move_age_seconds for row in rows),
        ),
        "oldest_latest_source_age_seconds": _max_decimal(
            tuple(row.latest_source_age_seconds for row in rows),
        ),
        "oldest_official_update_age_seconds": _max_decimal(
            tuple(row.official_update_age_seconds for row in rows),
        ),
        "oldest_liquidity_context_age_seconds": _max_decimal(
            tuple(row.liquidity_context_age_seconds for row in rows),
        ),
        "oldest_contradiction_follow_up_age_seconds": _max_decimal(
            tuple(row.contradiction_follow_up_age_seconds for row in rows),
        ),
        "minimum_seconds_to_close": _min_decimal(
            tuple(row.seconds_to_close for row in rows),
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchPacketMarketContextRefreshSlaV2Report(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _build_rows(
    observations: tuple[ResearchPacketMarketContextRefreshSlaV2Observation, ...],
    generated_at: datetime,
    config: ResearchPacketMarketContextRefreshSlaV2Config,
) -> tuple[ResearchPacketMarketContextRefreshSlaV2Row, ...]:
    return tuple(
        _row_for_observation(observation, generated_at, config)
        for observation in observations
    )


def _row_for_observation(
    observation: ResearchPacketMarketContextRefreshSlaV2Observation,
    generated_at: datetime,
    config: ResearchPacketMarketContextRefreshSlaV2Config,
) -> ResearchPacketMarketContextRefreshSlaV2Row:
    price_move_age = _age_seconds(
        "price_move_at",
        observation.price_move_at,
        generated_at,
    )
    latest_source_age = _age_seconds(
        "latest_source_at",
        observation.latest_source_at,
        generated_at,
    )
    official_update_age = _age_seconds(
        "official_update_at",
        observation.official_update_at,
        generated_at,
    )
    liquidity_context_age = _age_seconds(
        "liquidity_context_at",
        observation.liquidity_context_at,
        generated_at,
    )
    (
        contradiction_follow_up_age,
        contradiction_follow_up_stale,
        contradiction_follow_up_missing,
    ) = _contradiction_follow_up_state(observation, generated_at, config)
    seconds_to_close = _seconds_until(observation.market_closes_at, generated_at)
    close_urgency = _close_urgency(seconds_to_close, config)
    price_move_stale = price_move_age > config.price_move_max_age_seconds
    latest_source_stale = latest_source_age > config.latest_source_max_age_seconds
    official_update_stale = official_update_age > config.official_update_max_age_seconds
    liquidity_context_stale = (
        liquidity_context_age > config.liquidity_context_max_age_seconds
    )
    reason_codes = _row_reason_codes(
        price_move_stale=price_move_stale,
        latest_source_stale=latest_source_stale,
        official_update_stale=official_update_stale,
        liquidity_context_stale=liquidity_context_stale,
        contradiction_follow_up_stale=contradiction_follow_up_stale,
        contradiction_follow_up_missing=contradiction_follow_up_missing,
        close_urgency=close_urgency,
    )
    return ResearchPacketMarketContextRefreshSlaV2Row(
        packet_id=observation.packet_id,
        market_id=observation.market_id,
        row_status=_row_status(
            price_move_stale=price_move_stale,
            latest_source_stale=latest_source_stale,
            official_update_stale=official_update_stale,
            liquidity_context_stale=liquidity_context_stale,
            contradiction_follow_up_stale=contradiction_follow_up_stale,
            close_urgency=close_urgency,
        ),
        price_move_age_seconds=price_move_age,
        latest_source_age_seconds=latest_source_age,
        official_update_age_seconds=official_update_age,
        liquidity_context_age_seconds=liquidity_context_age,
        contradiction_follow_up_age_seconds=contradiction_follow_up_age,
        seconds_to_close=seconds_to_close,
        close_urgency=close_urgency,
        price_move_stale=price_move_stale,
        latest_source_stale=latest_source_stale,
        official_update_stale=official_update_stale,
        liquidity_context_stale=liquidity_context_stale,
        contradiction_follow_up_stale=contradiction_follow_up_stale,
        reason_codes=reason_codes,
    )


def _contradiction_follow_up_state(
    observation: ResearchPacketMarketContextRefreshSlaV2Observation,
    generated_at: datetime,
    config: ResearchPacketMarketContextRefreshSlaV2Config,
) -> tuple[Decimal, bool, bool]:
    if observation.contradiction_detected_at is None:
        return _ZERO, False, False
    if observation.contradiction_follow_up_at is None:
        return (
            _age_seconds(
                "contradiction_detected_at",
                observation.contradiction_detected_at,
                generated_at,
            ),
            True,
            True,
        )
    follow_up_age = _age_seconds(
        "contradiction_follow_up_at",
        observation.contradiction_follow_up_at,
        generated_at,
    )
    return (
        follow_up_age,
        follow_up_age > config.contradiction_follow_up_max_age_seconds,
        False,
    )


def _row_reason_codes(
    *,
    price_move_stale: bool,
    latest_source_stale: bool,
    official_update_stale: bool,
    liquidity_context_stale: bool,
    contradiction_follow_up_stale: bool,
    contradiction_follow_up_missing: bool,
    close_urgency: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if price_move_stale:
        reason_codes.append("price_move_age_stale")
    if latest_source_stale:
        reason_codes.append("latest_source_age_stale")
    if official_update_stale:
        reason_codes.append("official_update_age_stale")
    if liquidity_context_stale:
        reason_codes.append("liquidity_context_age_stale")
    if contradiction_follow_up_missing:
        reason_codes.append("contradiction_follow_up_missing")
    elif contradiction_follow_up_stale:
        reason_codes.append("contradiction_follow_up_age_stale")
    if close_urgency == "near":
        reason_codes.append("close_urgency_near")
    elif close_urgency == "urgent":
        reason_codes.append("close_urgency_urgent")
    elif close_urgency == "elapsed":
        reason_codes.append("close_urgency_elapsed")
    row_status = _row_status(
        price_move_stale=price_move_stale,
        latest_source_stale=latest_source_stale,
        official_update_stale=official_update_stale,
        liquidity_context_stale=liquidity_context_stale,
        contradiction_follow_up_stale=contradiction_follow_up_stale,
        close_urgency=close_urgency,
    )
    if row_status == "pass":
        reason_codes.append("market_context_refresh_fresh")
    elif row_status == "watch":
        reason_codes.append("market_context_refresh_watch")
    else:
        reason_codes.append("market_context_refresh_blocked")
    return _normalize_reason_codes(tuple(reason_codes), require_nonempty=True)


def _row_status(
    *,
    price_move_stale: bool,
    latest_source_stale: bool,
    official_update_stale: bool,
    liquidity_context_stale: bool,
    contradiction_follow_up_stale: bool,
    close_urgency: str,
) -> str:
    if contradiction_follow_up_stale or close_urgency == "elapsed":
        return "blocked"
    if (
        price_move_stale
        or latest_source_stale
        or official_update_stale
        or liquidity_context_stale
        or close_urgency in ("near", "urgent")
    ):
        return "watch"
    return "pass"


def _close_urgency(
    seconds_to_close: Decimal,
    config: ResearchPacketMarketContextRefreshSlaV2Config,
) -> str:
    if seconds_to_close == _ZERO:
        return "elapsed"
    if seconds_to_close <= config.close_urgent_seconds:
        return "urgent"
    if seconds_to_close <= config.close_watch_seconds:
        return "near"
    return "normal"


def _report_status(
    rows: tuple[ResearchPacketMarketContextRefreshSlaV2Row, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.row_status == "blocked" for row in rows):
        return "blocked"
    if any(row.row_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchPacketMarketContextRefreshSlaV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("market_context_refresh_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes), require_nonempty=True)


def _status_count(
    rows: tuple[ResearchPacketMarketContextRefreshSlaV2Row, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.row_status == status)


def _true_count(values: tuple[bool, ...]) -> int:
    return sum(1 for value in values if value)


def _validate_observation_times(
    observations: tuple[ResearchPacketMarketContextRefreshSlaV2Observation, ...],
    generated_at: datetime,
) -> None:
    for observation in observations:
        for field_name in (
            "price_move_at",
            "latest_source_at",
            "official_update_at",
            "liquidity_context_at",
            "contradiction_detected_at",
            "contradiction_follow_up_at",
        ):
            timestamp = getattr(observation, field_name)
            if timestamp is not None and timestamp > generated_at:
                raise ValueError(f"{field_name} must not be after generated_at")


def _validate_row_consistency(
    row: ResearchPacketMarketContextRefreshSlaV2Row,
) -> None:
    _require_reason_pair(
        row.price_move_stale,
        "price_move_age_stale",
        row.reason_codes,
        "price_move_stale",
    )
    _require_reason_pair(
        row.latest_source_stale,
        "latest_source_age_stale",
        row.reason_codes,
        "latest_source_stale",
    )
    _require_reason_pair(
        row.official_update_stale,
        "official_update_age_stale",
        row.reason_codes,
        "official_update_stale",
    )
    _require_reason_pair(
        row.liquidity_context_stale,
        "liquidity_context_age_stale",
        row.reason_codes,
        "liquidity_context_stale",
    )
    contradiction_reasons = (
        "contradiction_follow_up_missing",
        "contradiction_follow_up_age_stale",
    )
    has_contradiction_reason = any(
        reason_code in row.reason_codes for reason_code in contradiction_reasons
    )
    if row.contradiction_follow_up_stale != has_contradiction_reason:
        raise ValueError(
            "contradiction_follow_up_stale must match contradiction reason_codes",
        )
    if row.row_status == "pass":
        if row.reason_codes != ("market_context_refresh_fresh",):
            raise ValueError("pass rows must only include fresh reason code")
        if row.close_urgency != "normal":
            raise ValueError("pass rows must have normal close_urgency")
    if row.row_status == "watch":
        if "market_context_refresh_watch" not in row.reason_codes:
            raise ValueError("watch rows must include market_context_refresh_watch")
        if "market_context_refresh_blocked" in row.reason_codes:
            raise ValueError("watch rows must not include blocked reason code")
        if row.close_urgency == "elapsed":
            raise ValueError("elapsed close_urgency rows must be blocked")
        if row.contradiction_follow_up_stale:
            raise ValueError("contradiction follow-up stale rows must be blocked")
    if row.row_status == "blocked":
        if "market_context_refresh_blocked" not in row.reason_codes:
            raise ValueError("blocked rows must include market_context_refresh_blocked")
    if row.close_urgency == "near" and "close_urgency_near" not in row.reason_codes:
        raise ValueError("near close_urgency must include close_urgency_near")
    if row.close_urgency == "urgent" and "close_urgency_urgent" not in row.reason_codes:
        raise ValueError("urgent close_urgency must include close_urgency_urgent")
    if row.close_urgency == "elapsed":
        if "close_urgency_elapsed" not in row.reason_codes:
            raise ValueError("elapsed close_urgency must include close_urgency_elapsed")
        if row.row_status != "blocked":
            raise ValueError("elapsed close_urgency rows must be blocked")


def _validate_report_consistency(
    report: ResearchPacketMarketContextRefreshSlaV2Report,
) -> None:
    if report.market_count != _decimal_count(len(report.rows)):
        raise ValueError("market_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.price_move_stale_count != _decimal_count(
        _true_count(tuple(row.price_move_stale for row in report.rows)),
    ):
        raise ValueError("price_move_stale_count must match rows")
    if report.latest_source_stale_count != _decimal_count(
        _true_count(tuple(row.latest_source_stale for row in report.rows)),
    ):
        raise ValueError("latest_source_stale_count must match rows")
    if report.official_update_stale_count != _decimal_count(
        _true_count(tuple(row.official_update_stale for row in report.rows)),
    ):
        raise ValueError("official_update_stale_count must match rows")
    if report.liquidity_context_stale_count != _decimal_count(
        _true_count(tuple(row.liquidity_context_stale for row in report.rows)),
    ):
        raise ValueError("liquidity_context_stale_count must match rows")
    if report.contradiction_follow_up_stale_count != _decimal_count(
        _true_count(tuple(row.contradiction_follow_up_stale for row in report.rows)),
    ):
        raise ValueError("contradiction_follow_up_stale_count must match rows")
    if report.close_urgent_count != _decimal_count(
        _true_count(tuple(row.close_urgency == "urgent" for row in report.rows)),
    ):
        raise ValueError("close_urgent_count must match rows")
    if report.oldest_price_move_age_seconds != _max_decimal(
        tuple(row.price_move_age_seconds for row in report.rows),
    ):
        raise ValueError("oldest_price_move_age_seconds must match rows")
    if report.oldest_latest_source_age_seconds != _max_decimal(
        tuple(row.latest_source_age_seconds for row in report.rows),
    ):
        raise ValueError("oldest_latest_source_age_seconds must match rows")
    if report.oldest_official_update_age_seconds != _max_decimal(
        tuple(row.official_update_age_seconds for row in report.rows),
    ):
        raise ValueError("oldest_official_update_age_seconds must match rows")
    if report.oldest_liquidity_context_age_seconds != _max_decimal(
        tuple(row.liquidity_context_age_seconds for row in report.rows),
    ):
        raise ValueError("oldest_liquidity_context_age_seconds must match rows")
    if report.oldest_contradiction_follow_up_age_seconds != _max_decimal(
        tuple(row.contradiction_follow_up_age_seconds for row in report.rows),
    ):
        raise ValueError("oldest_contradiction_follow_up_age_seconds must match rows")
    if report.minimum_seconds_to_close != _min_decimal(
        tuple(row.seconds_to_close for row in report.rows),
    ):
        raise ValueError("minimum_seconds_to_close must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _require_reason_pair(
    flag: bool,
    reason_code: str,
    reason_codes: tuple[str, ...],
    field_name: str,
) -> None:
    if flag and reason_code not in reason_codes:
        raise ValueError(f"{field_name} must include {reason_code}")
    if not flag and reason_code in reason_codes:
        raise ValueError(f"{field_name} must not include {reason_code}")


def _normalize_observations(
    observations: Sequence[ResearchPacketMarketContextRefreshSlaV2Observation],
) -> tuple[ResearchPacketMarketContextRefreshSlaV2Observation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchPacketMarketContextRefreshSlaV2Observation] = []
    for observation in observations:
        if type(observation) is not ResearchPacketMarketContextRefreshSlaV2Observation:
            raise ValueError(
                "observations must contain "
                "ResearchPacketMarketContextRefreshSlaV2Observation values",
            )
        _require_hard_flags("observation", observation)
        normalized.append(observation)
    return tuple(sorted(normalized, key=lambda item: (item.packet_id, item.market_id)))


def _normalize_rows(
    rows: Sequence[ResearchPacketMarketContextRefreshSlaV2Row],
) -> tuple[ResearchPacketMarketContextRefreshSlaV2Row, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchPacketMarketContextRefreshSlaV2Row] = []
    for row in rows:
        if type(row) is not ResearchPacketMarketContextRefreshSlaV2Row:
            raise ValueError(
                "rows must contain ResearchPacketMarketContextRefreshSlaV2Row values",
            )
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: (row.packet_id, row.market_id)))


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


def _require_member(field_name: str, value: object, allowed: frozenset[str]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be a supported value")
    _reject_unsafe_public_string(field_name, value)
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


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


def _require_nonnegative_seconds_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_seconds_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_seconds_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return max(values)


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return min(values)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _age_seconds(field_name: str, timestamp: datetime, generated_at: datetime) -> Decimal:
    if timestamp > generated_at:
        raise ValueError(f"{field_name} must not be after generated_at")
    return _duration_seconds(generated_at, timestamp)


def _seconds_until(target_at: datetime, generated_at: datetime) -> Decimal:
    if target_at <= generated_at:
        return _ZERO
    return _duration_seconds(target_at, generated_at)


def _duration_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    days_seconds = Decimal(delta.days) * _SECONDS_PER_DAY
    whole_seconds = Decimal(delta.seconds)
    microseconds = Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND
    return _quantize(days_seconds + whole_seconds + microseconds)


def _normalize_reason_codes(
    reason_codes: Sequence[str],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    ordered = tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )
    if require_nonempty and not ordered:
        raise ValueError("reason_codes must not be empty")
    return ordered


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


def _report_values_without_digest(
    report: ResearchPacketMarketContextRefreshSlaV2Report,
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
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


__all__ = (
    "DEFAULT_RESEARCH_PACKET_MARKET_CONTEXT_REFRESH_SLA_V2_CONFIG_VERSION",
    "ResearchPacketMarketContextRefreshSlaV2Config",
    "ResearchPacketMarketContextRefreshSlaV2Observation",
    "ResearchPacketMarketContextRefreshSlaV2Report",
    "ResearchPacketMarketContextRefreshSlaV2Row",
    "build_research_packet_market_context_refresh_sla_v2_report",
)
