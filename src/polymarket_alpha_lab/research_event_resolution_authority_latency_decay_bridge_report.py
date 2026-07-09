"""Report-only bridge for resolution authority latency decay research."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_LATENCY_DECAY_BRIDGE_CONFIG_VERSION = (
    "research-event-resolution-authority-latency-decay-bridge-report-v0"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
SCORE_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

STATUSES = ("pass", "watch", "block")
ROW_REASON_CODES = (
    "resolution_authority_bridge_pass",
    "resolution_authority_bridge_watch",
    "resolution_authority_bridge_block",
    "resolution_authority_latency_pass",
    "resolution_authority_latency_watch",
    "resolution_authority_latency_block",
    "resolution_authority_confidence_pass",
    "resolution_authority_confidence_watch",
    "resolution_authority_confidence_block",
    "resolution_latency_decay_pass",
    "resolution_latency_decay_watch",
    "resolution_latency_decay_block",
)
REPORT_REASON_CODES = (
    "resolution_authority_latency_report_pass",
    "resolution_authority_latency_report_watch_rows",
    "resolution_authority_latency_report_block_rows",
    "resolution_authority_latency_report_empty",
)
UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "raw_candidate_id",
    "candidate_id",
    "market_id",
    "market_slug",
    "market_question",
    "source_url",
    "source_text",
    "resolver_reference",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "sizing",
    "recommendation",
)
UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "auth ",
    "auth_",
    "auth=",
    "authentication",
    "authorization",
    "bearer ",
    "database",
    "dsn",
    "live",
    "network",
    "password",
    "recommendation",
    "sizing",
    "table",
    "token",
    "wallet",
    "bearer ",
    "wallet",
    "order",
    "trade",
    "buy",
    "sell",
    "source_url",
    "source_text",
)

__all__ = (
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_LATENCY_DECAY_BRIDGE_CONFIG_VERSION",
    "STATUSES",
    "ResearchEventResolutionAuthorityLatencyDecayBridgeConfig",
    "ResearchEventResolutionAuthorityLatencyDecayBridgeObservation",
    "ResearchEventResolutionAuthorityLatencyDecayBridgeReasonCodeCount",
    "ResearchEventResolutionAuthorityLatencyDecayBridgeReport",
    "ResearchEventResolutionAuthorityLatencyDecayBridgeRow",
    "build_research_event_resolution_authority_latency_decay_bridge_report",
    "research_event_resolution_authority_latency_decay_bridge_report_to_json_payload",
    "validate_research_event_resolution_authority_latency_decay_bridge_report_public_payload",
)


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityLatencyDecayBridgeConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_LATENCY_DECAY_BRIDGE_CONFIG_VERSION
    )
    pass_latency_seconds: Decimal = Decimal("600.000000")
    block_latency_seconds: Decimal = Decimal("3600.000000")
    decay_window_seconds: Decimal = Decimal("3600.000000")
    pass_resolver_confidence: Decimal = Decimal("0.900000")
    block_resolver_confidence: Decimal = Decimal("0.500000")
    pass_latency_decay_score: Decimal = Decimal("0.800000")
    block_latency_decay_score: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityLatencyDecayBridgeConfig:
            raise TypeError(
                "ResearchEventResolutionAuthorityLatencyDecayBridgeConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionAuthorityLatencyDecayBridgeConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchEventResolutionAuthorityLatencyDecayBridgeConfig",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_LATENCY_DECAY_BRIDGE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_latency_seconds",
            "block_latency_seconds",
            "decay_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_resolver_confidence",
            "block_resolver_confidence",
            "pass_latency_decay_score",
            "block_latency_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.block_latency_seconds <= self.pass_latency_seconds:
            raise ValueError("block_latency_seconds must exceed pass_latency_seconds")
        if self.pass_resolver_confidence < self.block_resolver_confidence:
            raise ValueError(
                "pass_resolver_confidence must be >= block_resolver_confidence",
            )
        if self.pass_latency_decay_score < self.block_latency_decay_score:
            raise ValueError(
                "pass_latency_decay_score must be >= block_latency_decay_score",
            )
        _require_hard_flags(
            "ResearchEventResolutionAuthorityLatencyDecayBridgeConfig",
            self,
        )


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityLatencyDecayBridgeObservation:
    raw_candidate_id: str
    market_id: str
    market_slug: str
    market_question: str
    resolver_reference: str
    resolver_kind: str
    event_resolved_at: datetime
    authority_observed_at: datetime
    authority_confidence: Decimal
    source_url: str
    source_text: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityLatencyDecayBridgeObservation:
            raise TypeError(
                "ResearchEventResolutionAuthorityLatencyDecayBridgeObservation "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionAuthorityLatencyDecayBridgeObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchEventResolutionAuthorityLatencyDecayBridgeObservation",
            )
        for field_name in (
            "raw_candidate_id",
            "market_id",
            "market_slug",
            "market_question",
            "resolver_reference",
            "resolver_kind",
            "source_url",
            "source_text",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_private_input_string(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "event_resolved_at",
            _as_utc("event_resolved_at", self.event_resolved_at),
        )
        object.__setattr__(
            self,
            "authority_observed_at",
            _as_utc("authority_observed_at", self.authority_observed_at),
        )
        if self.authority_observed_at < self.event_resolved_at:
            raise ValueError("authority_observed_at must not precede event_resolved_at")
        object.__setattr__(
            self,
            "authority_confidence",
            _normalize_ratio("authority_confidence", self.authority_confidence),
        )
        _require_hard_flags(
            "ResearchEventResolutionAuthorityLatencyDecayBridgeObservation",
            self,
        )


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityLatencyDecayBridgeRow:
    bridge_digest: str
    resolver_kind: str
    event_resolved_at: datetime
    authority_observed_at: datetime
    latency_seconds: Decimal
    latency_decay_score: Decimal
    resolver_confidence: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityLatencyDecayBridgeRow:
            raise TypeError(
                "ResearchEventResolutionAuthorityLatencyDecayBridgeRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionAuthorityLatencyDecayBridgeRow:
            raise ValueError(
                "row must be exactly "
                "ResearchEventResolutionAuthorityLatencyDecayBridgeRow",
            )
        _require_sha256_digest("bridge_digest", self.bridge_digest)
        object.__setattr__(
            self,
            "resolver_kind",
            _require_public_string("resolver_kind", self.resolver_kind),
        )
        object.__setattr__(
            self,
            "event_resolved_at",
            _as_utc("event_resolved_at", self.event_resolved_at),
        )
        object.__setattr__(
            self,
            "authority_observed_at",
            _as_utc("authority_observed_at", self.authority_observed_at),
        )
        if self.authority_observed_at < self.event_resolved_at:
            raise ValueError("authority_observed_at must not precede event_resolved_at")
        object.__setattr__(
            self,
            "latency_seconds",
            _normalize_nonnegative_decimal("latency_seconds", self.latency_seconds),
        )
        for field_name in (
            "latency_decay_score",
            "resolver_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags(
            "ResearchEventResolutionAuthorityLatencyDecayBridgeRow",
            self,
        )
        _validate_row_consistency(self)
        _reject_unsafe_public_payload(
            "ResearchEventResolutionAuthorityLatencyDecayBridgeRow",
            _payload_value(asdict(self)),
        )


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityLatencyDecayBridgeReasonCodeCount:
    reason_code: str
    count: Decimal
    event_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityLatencyDecayBridgeReasonCodeCount:
            raise TypeError(
                "ResearchEventResolutionAuthorityLatencyDecayBridgeReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionAuthorityLatencyDecayBridgeReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchEventResolutionAuthorityLatencyDecayBridgeReasonCodeCount",
            )
        object.__setattr__(
            self,
            "reason_code",
            _require_public_string("reason_code", self.reason_code),
        )
        if self.reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_code must be a known row reason code")
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_integral_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "event_ratio",
            _normalize_ratio("event_ratio", self.event_ratio),
        )
        _require_hard_flags(
            "ResearchEventResolutionAuthorityLatencyDecayBridgeReasonCodeCount",
            self,
        )


@dataclass(frozen=True)
class ResearchEventResolutionAuthorityLatencyDecayBridgeReport:
    generated_at: datetime
    config_version: str
    status: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_latency_seconds: Decimal
    average_latency_decay_score: Decimal
    average_resolver_confidence: Decimal
    rows: tuple[ResearchEventResolutionAuthorityLatencyDecayBridgeRow, ...]
    reason_code_counts: tuple[
        ResearchEventResolutionAuthorityLatencyDecayBridgeReasonCodeCount,
        ...
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionAuthorityLatencyDecayBridgeReport:
            raise TypeError(
                "ResearchEventResolutionAuthorityLatencyDecayBridgeReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionAuthorityLatencyDecayBridgeReport:
            raise ValueError(
                "report must be exactly "
                "ResearchEventResolutionAuthorityLatencyDecayBridgeReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_non_empty_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_LATENCY_DECAY_BRIDGE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "event_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_integral_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "average_latency_seconds",
            _normalize_nonnegative_decimal(
                "average_latency_seconds",
                self.average_latency_seconds,
            ),
        )
        for field_name in (
            "average_latency_decay_score",
            "average_resolver_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _require_hard_flags(
            "ResearchEventResolutionAuthorityLatencyDecayBridgeReport",
            self,
        )
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
        _validate_report_consistency(self)
        _report_public_payload_for_report(self)

    @property
    def payload(self) -> dict[str, Any]:
        return (
            research_event_resolution_authority_latency_decay_bridge_report_to_json_payload(
                self,
            )
        )


def build_research_event_resolution_authority_latency_decay_bridge_report(
    observations: object,
    *,
    config: ResearchEventResolutionAuthorityLatencyDecayBridgeConfig | None = None,
    generated_at: datetime,
) -> ResearchEventResolutionAuthorityLatencyDecayBridgeReport:
    if config is None:
        config = ResearchEventResolutionAuthorityLatencyDecayBridgeConfig()
    if type(config) is not ResearchEventResolutionAuthorityLatencyDecayBridgeConfig:
        raise ValueError(
            "config must be a ResearchEventResolutionAuthorityLatencyDecayBridgeConfig",
        )
    _require_hard_flags(
        "ResearchEventResolutionAuthorityLatencyDecayBridgeConfig",
        config,
    )
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_observations(observations)
    for item in items:
        if item.event_resolved_at > generated_at_utc:
            raise ValueError("event_resolved_at must not be after generated_at")
        if item.authority_observed_at > generated_at_utc:
            raise ValueError("authority_observed_at must not be after generated_at")

    rows = tuple(
        sorted(
            (_row_for_observation(item, config) for item in items),
            key=_row_sort_key,
        ),
    )
    status = _report_status(rows)
    return ResearchEventResolutionAuthorityLatencyDecayBridgeReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=status,
        event_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        average_latency_seconds=_average_decimal(
            tuple(row.latency_seconds for row in rows),
        ),
        average_latency_decay_score=_average_decimal(
            tuple(row.latency_decay_score for row in rows),
        ),
        average_resolver_confidence=_average_decimal(
            tuple(row.resolver_confidence for row in rows),
        ),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows),
        reason_codes=_report_reason_codes(rows, status),
    )


def research_event_resolution_authority_latency_decay_bridge_report_to_json_payload(
    report: ResearchEventResolutionAuthorityLatencyDecayBridgeReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventResolutionAuthorityLatencyDecayBridgeReport:
        raise ValueError(
            "report must be a ResearchEventResolutionAuthorityLatencyDecayBridgeReport",
        )
    revalidated_report = _revalidate_report(report)
    payload = _report_public_payload_for_report(revalidated_report)
    payload["derived_validation_digest"] = revalidated_report.derived_validation_digest
    validate_research_event_resolution_authority_latency_decay_bridge_report_public_payload(
        payload,
    )
    return payload


def validate_research_event_resolution_authority_latency_decay_bridge_report_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload(
        "research event resolution authority latency decay bridge payload",
        payload,
    )
    _require_public_payload_flags(payload)
    _reject_public_numeric_values(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _row_for_observation(
    item: ResearchEventResolutionAuthorityLatencyDecayBridgeObservation,
    config: ResearchEventResolutionAuthorityLatencyDecayBridgeConfig,
) -> ResearchEventResolutionAuthorityLatencyDecayBridgeRow:
    latency_seconds = _latency_seconds(item.event_resolved_at, item.authority_observed_at)
    latency_decay_score = _latency_decay_score(latency_seconds, config)
    status = _row_status(
        latency_seconds=latency_seconds,
        latency_decay_score=latency_decay_score,
        resolver_confidence=item.authority_confidence,
        config=config,
    )
    return ResearchEventResolutionAuthorityLatencyDecayBridgeRow(
        bridge_digest=_bridge_digest(item),
        resolver_kind=item.resolver_kind,
        event_resolved_at=item.event_resolved_at,
        authority_observed_at=item.authority_observed_at,
        latency_seconds=latency_seconds,
        latency_decay_score=latency_decay_score,
        resolver_confidence=item.authority_confidence,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            latency_seconds=latency_seconds,
            latency_decay_score=latency_decay_score,
            resolver_confidence=item.authority_confidence,
            config=config,
        ),
    )


def _latency_seconds(started_at: datetime, finished_at: datetime) -> Decimal:
    delta = finished_at - started_at
    return _normalize_nonnegative_decimal(
        "latency_seconds",
        Decimal(delta.days * 86400 + delta.seconds).quantize(SCORE_QUANT),
    )


def _latency_decay_score(
    latency_seconds: Decimal,
    config: ResearchEventResolutionAuthorityLatencyDecayBridgeConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(ONE - (latency_seconds / config.decay_window_seconds))


def _row_status(
    *,
    latency_seconds: Decimal,
    latency_decay_score: Decimal,
    resolver_confidence: Decimal,
    config: ResearchEventResolutionAuthorityLatencyDecayBridgeConfig,
) -> str:
    if (
        latency_seconds >= config.block_latency_seconds
        or resolver_confidence <= config.block_resolver_confidence
        or latency_decay_score <= config.block_latency_decay_score
    ):
        return "block"
    if (
        latency_seconds <= config.pass_latency_seconds
        and resolver_confidence >= config.pass_resolver_confidence
        and latency_decay_score >= config.pass_latency_decay_score
    ):
        return "pass"
    return "watch"


def _row_reason_codes(
    *,
    status: str,
    latency_seconds: Decimal,
    latency_decay_score: Decimal,
    resolver_confidence: Decimal,
    config: ResearchEventResolutionAuthorityLatencyDecayBridgeConfig,
) -> tuple[str, ...]:
    return (
        f"resolution_authority_bridge_{status}",
        _tier_reason(
            value=latency_seconds,
            pass_floor=config.pass_latency_seconds,
            block_floor=config.block_latency_seconds,
            pass_reason="resolution_authority_latency_pass",
            watch_reason="resolution_authority_latency_watch",
            block_reason="resolution_authority_latency_block",
            higher_is_worse=True,
        ),
        _tier_reason(
            value=resolver_confidence,
            pass_floor=config.pass_resolver_confidence,
            block_floor=config.block_resolver_confidence,
            pass_reason="resolution_authority_confidence_pass",
            watch_reason="resolution_authority_confidence_watch",
            block_reason="resolution_authority_confidence_block",
            higher_is_worse=False,
        ),
        _tier_reason(
            value=latency_decay_score,
            pass_floor=config.pass_latency_decay_score,
            block_floor=config.block_latency_decay_score,
            pass_reason="resolution_latency_decay_pass",
            watch_reason="resolution_latency_decay_watch",
            block_reason="resolution_latency_decay_block",
            higher_is_worse=False,
        ),
    )


def _tier_reason(
    *,
    value: Decimal,
    pass_floor: Decimal,
    block_floor: Decimal,
    pass_reason: str,
    watch_reason: str,
    block_reason: str,
    higher_is_worse: bool,
) -> str:
    if higher_is_worse:
        if value >= block_floor:
            return block_reason
        if value <= pass_floor:
            return pass_reason
        return watch_reason
    if value <= block_floor:
        return block_reason
    if value >= pass_floor:
        return pass_reason
    return watch_reason


def _report_status(
    rows: tuple[ResearchEventResolutionAuthorityLatencyDecayBridgeRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionAuthorityLatencyDecayBridgeRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("resolution_authority_latency_report_empty",)
    reason_codes: list[str] = []
    if any(row.status == "block" for row in rows):
        reason_codes.append("resolution_authority_latency_report_block_rows")
    if any(row.status == "watch" for row in rows):
        reason_codes.append("resolution_authority_latency_report_watch_rows")
    if not reason_codes and status == "pass":
        reason_codes.append("resolution_authority_latency_report_pass")
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchEventResolutionAuthorityLatencyDecayBridgeRow, ...],
) -> tuple[ResearchEventResolutionAuthorityLatencyDecayBridgeReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        ResearchEventResolutionAuthorityLatencyDecayBridgeReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            event_ratio=_ratio(counts[reason_code], len(rows)),
        )
        for reason_code in sorted(counts)
    )


def _normalize_observations(
    value: object,
) -> tuple[ResearchEventResolutionAuthorityLatencyDecayBridgeObservation, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError("observations must be an iterable")
    items = tuple(value)
    for item in items:
        if type(item) is not ResearchEventResolutionAuthorityLatencyDecayBridgeObservation:
            raise ValueError(
                "observations must contain "
                "ResearchEventResolutionAuthorityLatencyDecayBridgeObservation values",
            )
        _require_hard_flags(
            "ResearchEventResolutionAuthorityLatencyDecayBridgeObservation",
            item,
        )
    keys = tuple(
        (
            item.raw_candidate_id,
            item.market_id,
            item.market_slug,
            item.resolver_reference,
            item.event_resolved_at,
        )
        for item in items
    )
    if len(set(keys)) != len(keys):
        raise ValueError("observations must not contain duplicate bridge keys")
    return items


def _normalize_rows(
    value: object,
) -> tuple[ResearchEventResolutionAuthorityLatencyDecayBridgeRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not ResearchEventResolutionAuthorityLatencyDecayBridgeRow:
            raise ValueError(
                "rows must contain "
                "ResearchEventResolutionAuthorityLatencyDecayBridgeRow values",
            )
        _require_hard_flags(
            "ResearchEventResolutionAuthorityLatencyDecayBridgeRow",
            row,
        )
    if value != tuple(sorted(value, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status, latency, and bridge digest")
    return value


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchEventResolutionAuthorityLatencyDecayBridgeReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in value:
        if (
            type(item)
            is not ResearchEventResolutionAuthorityLatencyDecayBridgeReasonCodeCount
        ):
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventResolutionAuthorityLatencyDecayBridgeReasonCodeCount values",
            )
        _require_hard_flags(
            "ResearchEventResolutionAuthorityLatencyDecayBridgeReasonCodeCount",
            item,
        )
    if value != tuple(sorted(value, key=lambda item: item.reason_code)):
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return value


def _row_sort_key(
    row: ResearchEventResolutionAuthorityLatencyDecayBridgeRow,
) -> tuple[int, Decimal, str]:
    severity = {"block": 0, "watch": 1, "pass": 2}
    return (severity[row.status], -row.latency_seconds, row.bridge_digest)


def _validate_row_consistency(
    row: ResearchEventResolutionAuthorityLatencyDecayBridgeRow,
) -> None:
    if row.reason_codes[0] != f"resolution_authority_bridge_{row.status}":
        raise ValueError("status must match reason_codes")
    if row.latency_seconds != _latency_seconds(
        row.event_resolved_at,
        row.authority_observed_at,
    ):
        raise ValueError("latency_seconds must match event and authority times")


def _validate_report_consistency(
    report: ResearchEventResolutionAuthorityLatencyDecayBridgeReport,
) -> None:
    rows = report.rows
    if report.event_count != _decimal_count(len(rows)):
        raise ValueError("event_count must match rows")
    if (
        report.pass_count != _status_count(rows, "pass")
        or report.watch_count != _status_count(rows, "watch")
        or report.block_count != _status_count(rows, "block")
    ):
        raise ValueError("event counts must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.event_count:
        raise ValueError("event counts must sum to event_count")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.status):
        raise ValueError("reason_codes must match status")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.average_latency_seconds != _average_decimal(
        tuple(row.latency_seconds for row in rows),
    ):
        raise ValueError("average_latency_seconds must match rows")
    if report.average_latency_decay_score != _average_decimal(
        tuple(row.latency_decay_score for row in rows),
    ):
        raise ValueError("average_latency_decay_score must match rows")
    if report.average_resolver_confidence != _average_decimal(
        tuple(row.resolver_confidence for row in rows),
    ):
        raise ValueError("average_resolver_confidence must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _revalidate_report(
    report: ResearchEventResolutionAuthorityLatencyDecayBridgeReport,
) -> ResearchEventResolutionAuthorityLatencyDecayBridgeReport:
    return ResearchEventResolutionAuthorityLatencyDecayBridgeReport(
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        event_count=report.event_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_latency_seconds=report.average_latency_seconds,
        average_latency_decay_score=report.average_latency_decay_score,
        average_resolver_confidence=report.average_resolver_confidence,
        rows=report.rows,
        reason_code_counts=report.reason_code_counts,
        reason_codes=report.reason_codes,
        derived_validation_digest=report.derived_validation_digest,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _report_derived_validation_digest(
    report: ResearchEventResolutionAuthorityLatencyDecayBridgeReport,
) -> str:
    return _public_payload_derived_validation_digest(_report_public_payload_for_report(report))


def _report_public_payload_for_report(
    report: ResearchEventResolutionAuthorityLatencyDecayBridgeReport,
) -> dict[str, Any]:
    payload = _payload_value(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload(
        "research event resolution authority latency decay bridge report",
        payload,
    )
    return payload


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _bridge_digest(
    item: ResearchEventResolutionAuthorityLatencyDecayBridgeObservation,
) -> str:
    private_payload = {
        "authority_confidence": str(item.authority_confidence),
        "authority_observed_at": item.authority_observed_at.isoformat(),
        "event_resolved_at": item.event_resolved_at.isoformat(),
        "market_id": item.market_id,
        "market_question": item.market_question,
        "market_slug": item.market_slug,
        "raw_candidate_id": item.raw_candidate_id,
        "resolver_kind": item.resolver_kind,
        "resolver_reference": item.resolver_reference,
        "source_text": item.source_text,
        "source_url": item.source_url,
    }
    encoded = json.dumps(
        private_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _status_count(
    rows: tuple[ResearchEventResolutionAuthorityLatencyDecayBridgeRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANT)


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO) / Decimal(len(values))).quantize(SCORE_QUANT)


def _ratio(count: int, total: int) -> Decimal:
    if total == 0:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (Decimal(count) / Decimal(total)).quantize(SCORE_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_private_input_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    value = _require_non_empty_string(field_name, value)
    _reject_unsafe_public_payload(field_name, value)
    return value


def _require_non_empty_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    return value


def _require_status(field_name: str, value: object) -> None:
    _require_non_empty_string(field_name, value)
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_public_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if any(item not in allowed for item in normalized):
        raise ValueError(f"{field_name} must contain known reason codes")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value > ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(SCORE_QUANT)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return quantized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_nonnegative_integral_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANT)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _clamp_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return min(ONE, max(ZERO, value)).quantize(SCORE_QUANT)


def _require_sha256_digest(field_name: str, value: object) -> None:
    value = _require_non_empty_string(field_name, value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {field_name}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {field_name}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {field_name}")


def _payload_value(value: object) -> object:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _payload_value(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (int, float):
        raise ValueError("payload contains unsafe numeric value")
    raise ValueError("payload contains unsupported value")


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    if field_name not in payload:
        raise ValueError(f"{field_name} is required")
    value = payload[field_name]
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload.get(flag_name) is not True:
            raise ValueError(f"{flag_name} must be True")
    _require_nested_public_payload_flags(payload)


def _require_nested_public_payload_flags(value: Any) -> None:
    if isinstance(value, dict):
        flag_names = ("paper_only", "report_only", "readonly")
        if any(flag_name in value for flag_name in flag_names):
            for flag_name in flag_names:
                if value.get(flag_name) is not True:
                    raise ValueError(f"{flag_name} must be True")
        for item in value.values():
            _require_nested_public_payload_flags(item)
    elif isinstance(value, list):
        for item in value:
            _require_nested_public_payload_flags(item)


def _reject_public_numeric_values(value: Any) -> None:
    if type(value) in (int, float) or type(value) is Decimal:
        raise ValueError("public payload numeric values must be Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_key(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float) or type(value) is Decimal:
        raise ValueError(f"unsafe public payload in {label}")
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_key(label: str, value: str) -> None:
    normalized = value.lower()
    if value.strip() != value:
        raise ValueError(f"unsafe public payload in {label}")
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if value.strip() != value:
        raise ValueError(f"unsafe public payload in {label}")
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")
