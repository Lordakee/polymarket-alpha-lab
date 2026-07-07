"""Phase 1 report-only source freshness and authority join gate."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Iterable


DEFAULT_RESEARCH_PACKET_SOURCE_FRESHNESS_AUTHORITY_JOIN_V2_CONFIG_VERSION = (
    "research-packet-source-freshness-authority-join-v2"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_ROW_STATUSES = frozenset(("pass", "watch", "block"))
_REPORT_STATUSES = frozenset(("empty", "pass", "watch", "block"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TOKENS = frozenset(
    (
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
    ),
)
_REASON_CODE_SEQUENCE = (
    "stale_source",
    "low_authority",
    "proxy_dependent",
    "conflicting_sources",
    "quality_below_minimum",
    "freshness_authority_pass",
)
_DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"


@dataclass(frozen=True)
class ResearchPacketSourceFreshnessAuthorityJoinV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_SOURCE_FRESHNESS_AUTHORITY_JOIN_V2_CONFIG_VERSION
    )
    stale_source_age_seconds: Decimal = Decimal("86400.000000")
    min_authority_score: Decimal = Decimal("0.500000")
    max_proxy_dependency_ratio: Decimal = Decimal("0.750000")
    min_quality_score: Decimal = Decimal("0.700000")
    freshness_weight: Decimal = Decimal("0.500000")
    authority_weight: Decimal = Decimal("0.500000")
    proxy_dependency_penalty_weight: Decimal = Decimal("0.200000")
    conflict_penalty_per_source: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceFreshnessAuthorityJoinV2Config:
            raise TypeError(
                "ResearchPacketSourceFreshnessAuthorityJoinV2Config does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFreshnessAuthorityJoinV2Config:
            raise ValueError(
                "config must be exactly "
                "ResearchPacketSourceFreshnessAuthorityJoinV2Config",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_SOURCE_FRESHNESS_AUTHORITY_JOIN_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "stale_source_age_seconds",
            _require_positive_decimal(
                "stale_source_age_seconds",
                self.stale_source_age_seconds,
            ),
        )
        for field_name in (
            "min_authority_score",
            "max_proxy_dependency_ratio",
            "min_quality_score",
            "freshness_weight",
            "authority_weight",
            "proxy_dependency_penalty_weight",
            "conflict_penalty_per_source",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.freshness_weight + self.authority_weight != _ONE:
            raise ValueError("freshness_weight plus authority_weight must equal one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchPacketSourceFreshnessAuthorityInput:
    packet_id: str
    event_slug: str
    category: str
    newest_source_age_seconds: Decimal
    oldest_source_age_seconds: Decimal
    authority_score: Decimal
    proxy_dependency_ratio: Decimal
    conflicting_source_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceFreshnessAuthorityInput:
            raise TypeError(
                "ResearchPacketSourceFreshnessAuthorityInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFreshnessAuthorityInput:
            raise ValueError(
                "input must be exactly ResearchPacketSourceFreshnessAuthorityInput",
            )
        for field_name in ("packet_id", "event_slug", "category"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in ("newest_source_age_seconds", "oldest_source_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.oldest_source_age_seconds < self.newest_source_age_seconds:
            raise ValueError(
                "oldest_source_age_seconds must be greater than or equal to "
                "newest_source_age_seconds",
            )
        object.__setattr__(
            self,
            "authority_score",
            _require_ratio_decimal("authority_score", self.authority_score),
        )
        object.__setattr__(
            self,
            "proxy_dependency_ratio",
            _require_ratio_decimal(
                "proxy_dependency_ratio",
                self.proxy_dependency_ratio,
            ),
        )
        object.__setattr__(
            self,
            "conflicting_source_count",
            _require_nonnegative_count_decimal(
                "conflicting_source_count",
                self.conflicting_source_count,
            ),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchPacketSourceFreshnessAuthorityJoinV2Row:
    packet_id: str
    event_slug: str
    category: str
    newest_source_age_seconds: Decimal
    oldest_source_age_seconds: Decimal
    authority_score: Decimal
    proxy_dependency_ratio: Decimal
    conflicting_source_count: Decimal
    freshness_authority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceFreshnessAuthorityJoinV2Row:
            raise TypeError(
                "ResearchPacketSourceFreshnessAuthorityJoinV2Row does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFreshnessAuthorityJoinV2Row:
            raise ValueError(
                "row must be exactly ResearchPacketSourceFreshnessAuthorityJoinV2Row",
            )
        for field_name in ("packet_id", "event_slug", "category"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in (
            "newest_source_age_seconds",
            "oldest_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.oldest_source_age_seconds < self.newest_source_age_seconds:
            raise ValueError(
                "oldest_source_age_seconds must be greater than or equal to "
                "newest_source_age_seconds",
            )
        for field_name in (
            "authority_score",
            "proxy_dependency_ratio",
            "freshness_authority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "conflicting_source_count",
            _require_nonnegative_count_decimal(
                "conflicting_source_count",
                self.conflicting_source_count,
            ),
        )
        _require_row_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchPacketSourceFreshnessAuthorityJoinV2ReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceFreshnessAuthorityJoinV2ReasonCodeCount:
            raise TypeError(
                "ResearchPacketSourceFreshnessAuthorityJoinV2ReasonCodeCount does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFreshnessAuthorityJoinV2ReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchPacketSourceFreshnessAuthorityJoinV2ReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchPacketSourceFreshnessAuthorityJoinV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    packet_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_source_count: Decimal
    low_authority_count: Decimal
    proxy_dependent_count: Decimal
    conflict_count: Decimal
    min_quality_score: Decimal
    rows: tuple[ResearchPacketSourceFreshnessAuthorityJoinV2Row, ...]
    reason_code_counts: tuple[
        ResearchPacketSourceFreshnessAuthorityJoinV2ReasonCodeCount,
        ...,
    ]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceFreshnessAuthorityJoinV2Report:
            raise TypeError(
                "ResearchPacketSourceFreshnessAuthorityJoinV2Report does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFreshnessAuthorityJoinV2Report:
            raise ValueError(
                "report must be exactly "
                "ResearchPacketSourceFreshnessAuthorityJoinV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_SOURCE_FRESHNESS_AUTHORITY_JOIN_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_report_status("report_status", self.report_status)
        for field_name in (
            "packet_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_source_count",
            "low_authority_count",
            "proxy_dependent_count",
            "conflict_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_quality_score",
            _require_ratio_decimal("min_quality_score", self.min_quality_score),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
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
        return research_packet_source_freshness_authority_join_v2_payload(self)


def build_research_packet_source_freshness_authority_join_v2_report(
    packet_inputs: Iterable[ResearchPacketSourceFreshnessAuthorityInput],
    *,
    generated_at: datetime,
    config: ResearchPacketSourceFreshnessAuthorityJoinV2Config | None = None,
) -> ResearchPacketSourceFreshnessAuthorityJoinV2Report:
    """Build a local report-only source freshness and authority quality gate."""

    if config is None:
        config = ResearchPacketSourceFreshnessAuthorityJoinV2Config()
    if type(config) is not ResearchPacketSourceFreshnessAuthorityJoinV2Config:
        raise ValueError(
            "config must be a ResearchPacketSourceFreshnessAuthorityJoinV2Config",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(packet_inputs)
    rows = tuple(_row_for_input(item, config) for item in normalized_inputs)
    reason_code_counts = _reason_code_counts(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "report_status": _report_status(rows),
        "packet_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "stale_source_count": _decimal_count(_reason_row_count(rows, "stale_source")),
        "low_authority_count": _decimal_count(_reason_row_count(rows, "low_authority")),
        "proxy_dependent_count": _decimal_count(
            _reason_row_count(rows, "proxy_dependent"),
        ),
        "conflict_count": sum(
            (row.conflicting_source_count for row in rows),
            _ZERO,
        ),
        "min_quality_score": min(
            (row.freshness_authority_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchPacketSourceFreshnessAuthorityJoinV2Report(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_packet_source_freshness_authority_join_v2_payload(
    value: ResearchPacketSourceFreshnessAuthorityJoinV2Report | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchPacketSourceFreshnessAuthorityJoinV2Report:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchPacketSourceFreshnessAuthorityJoinV2Report or dict",
        )
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_public_payload_digest(payload)
    return payload


def _row_for_input(
    item: ResearchPacketSourceFreshnessAuthorityInput,
    config: ResearchPacketSourceFreshnessAuthorityJoinV2Config,
) -> ResearchPacketSourceFreshnessAuthorityJoinV2Row:
    freshness_score = _freshness_score(item, config)
    proxy_penalty = _quantize(
        item.proxy_dependency_ratio * config.proxy_dependency_penalty_weight,
    )
    conflict_penalty = _quantize(
        item.conflicting_source_count * config.conflict_penalty_per_source,
    )
    score = _clamp_ratio(
        freshness_score * config.freshness_weight
        + item.authority_score * config.authority_weight
        - proxy_penalty
        - conflict_penalty,
    )
    reason_codes = _row_reason_codes(item, score, config)
    status = _row_status(reason_codes, score, config)
    return ResearchPacketSourceFreshnessAuthorityJoinV2Row(
        packet_id=item.packet_id,
        event_slug=item.event_slug,
        category=item.category,
        newest_source_age_seconds=item.newest_source_age_seconds,
        oldest_source_age_seconds=item.oldest_source_age_seconds,
        authority_score=item.authority_score,
        proxy_dependency_ratio=item.proxy_dependency_ratio,
        conflicting_source_count=item.conflicting_source_count,
        freshness_authority_score=score,
        status=status,
        reason_codes=reason_codes,
    )


def _freshness_score(
    item: ResearchPacketSourceFreshnessAuthorityInput,
    config: ResearchPacketSourceFreshnessAuthorityJoinV2Config,
) -> Decimal:
    if _has_stale_source(item, config):
        return _ZERO
    freshest_source_ratio = _clamp_ratio(
        item.newest_source_age_seconds / config.stale_source_age_seconds,
    )
    oldest_source_ratio = _clamp_ratio(
        item.oldest_source_age_seconds / config.stale_source_age_seconds,
    )
    return _clamp_ratio(
        _ONE
        - (freshest_source_ratio * Decimal("0.500000"))
        - (oldest_source_ratio * Decimal("0.500000")),
    )


def _has_stale_source(
    item: ResearchPacketSourceFreshnessAuthorityInput,
    config: ResearchPacketSourceFreshnessAuthorityJoinV2Config,
) -> bool:
    return item.oldest_source_age_seconds >= config.stale_source_age_seconds


def _row_reason_codes(
    item: ResearchPacketSourceFreshnessAuthorityInput,
    score: Decimal,
    config: ResearchPacketSourceFreshnessAuthorityJoinV2Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if _has_stale_source(item, config):
        reason_codes.append("stale_source")
    if item.authority_score < config.min_authority_score:
        reason_codes.append("low_authority")
    if item.proxy_dependency_ratio > config.max_proxy_dependency_ratio:
        reason_codes.append("proxy_dependent")
    if item.conflicting_source_count > _ZERO:
        reason_codes.append("conflicting_sources")
    if score < config.min_quality_score:
        reason_codes.append("quality_below_minimum")
    if not reason_codes:
        reason_codes.append("freshness_authority_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(
    reason_codes: tuple[str, ...],
    score: Decimal,
    config: ResearchPacketSourceFreshnessAuthorityJoinV2Config,
) -> str:
    if score < config.min_quality_score:
        return "block"
    if "stale_source" in reason_codes or "low_authority" in reason_codes:
        return "block"
    if "proxy_dependent" in reason_codes or "conflicting_sources" in reason_codes:
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchPacketSourceFreshnessAuthorityJoinV2Row, ...],
) -> str:
    if not rows:
        return "empty"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchPacketSourceFreshnessAuthorityJoinV2Row, ...],
) -> tuple[ResearchPacketSourceFreshnessAuthorityJoinV2ReasonCodeCount, ...]:
    counts: list[ResearchPacketSourceFreshnessAuthorityJoinV2ReasonCodeCount] = []
    for reason_code in _REASON_CODE_SEQUENCE:
        count = sum(1 for row in rows if reason_code in row.reason_codes)
        if count:
            counts.append(
                ResearchPacketSourceFreshnessAuthorityJoinV2ReasonCodeCount(
                    reason_code=reason_code,
                    count=_decimal_count(count),
                ),
            )
    return tuple(counts)


def _status_count(
    rows: tuple[ResearchPacketSourceFreshnessAuthorityJoinV2Row, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _reason_row_count(
    rows: tuple[ResearchPacketSourceFreshnessAuthorityJoinV2Row, ...],
    reason_code: str,
) -> int:
    return sum(1 for row in rows if reason_code in row.reason_codes)


def _validate_report_consistency(
    report: ResearchPacketSourceFreshnessAuthorityJoinV2Report,
) -> None:
    if report.packet_count != _decimal_count(len(report.rows)):
        raise ValueError("packet_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.stale_source_count != _decimal_count(
        _reason_row_count(report.rows, "stale_source"),
    ):
        raise ValueError("stale_source_count must match rows")
    if report.low_authority_count != _decimal_count(
        _reason_row_count(report.rows, "low_authority"),
    ):
        raise ValueError("low_authority_count must match rows")
    if report.proxy_dependent_count != _decimal_count(
        _reason_row_count(report.rows, "proxy_dependent"),
    ):
        raise ValueError("proxy_dependent_count must match rows")
    expected_conflict_count = sum(
        (row.conflicting_source_count for row in report.rows),
        _ZERO,
    )
    if report.conflict_count != expected_conflict_count:
        raise ValueError("conflict_count must match rows")
    expected_min_quality_score = min(
        (row.freshness_authority_score for row in report.rows),
        default=_ZERO,
    )
    if report.min_quality_score != expected_min_quality_score:
        raise ValueError("min_quality_score must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_inputs(
    packet_inputs: Iterable[ResearchPacketSourceFreshnessAuthorityInput],
) -> tuple[ResearchPacketSourceFreshnessAuthorityInput, ...]:
    if isinstance(packet_inputs, (str, bytes)):
        raise ValueError("packet_inputs must be an iterable")
    try:
        values = tuple(packet_inputs)
    except TypeError as exc:
        raise ValueError("packet_inputs must be an iterable") from exc
    for item in values:
        if type(item) is not ResearchPacketSourceFreshnessAuthorityInput:
            raise ValueError(
                "packet_inputs items must be "
                "ResearchPacketSourceFreshnessAuthorityInput",
            )
        _require_hard_flags("input", item)
    sorted_values = tuple(
        sorted(values, key=lambda item: (item.packet_id, item.event_slug, item.category)),
    )
    packet_ids = tuple(item.packet_id for item in sorted_values)
    if len(set(packet_ids)) != len(packet_ids):
        raise ValueError("packet_inputs packet_id values must be unique")
    return sorted_values


def _normalize_rows(
    rows: tuple[ResearchPacketSourceFreshnessAuthorityJoinV2Row, ...],
) -> tuple[ResearchPacketSourceFreshnessAuthorityJoinV2Row, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchPacketSourceFreshnessAuthorityJoinV2Row:
            raise ValueError(
                "rows items must be ResearchPacketSourceFreshnessAuthorityJoinV2Row",
            )
        _require_hard_flags("row", row)
    sort_keys = tuple((row.packet_id, row.event_slug, row.category) for row in normalized)
    if sort_keys != tuple(sorted(sort_keys)):
        raise ValueError("rows must be sorted by packet_id, event_slug, and category")
    packet_ids = tuple(row.packet_id for row in normalized)
    if len(set(packet_ids)) != len(packet_ids):
        raise ValueError("rows packet_id values must be unique")
    return normalized


def _normalize_reason_code_counts(
    reason_code_counts: tuple[
        ResearchPacketSourceFreshnessAuthorityJoinV2ReasonCodeCount,
        ...,
    ],
) -> tuple[ResearchPacketSourceFreshnessAuthorityJoinV2ReasonCodeCount, ...]:
    if type(reason_code_counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(reason_code_counts)
    for item in normalized:
        if type(item) is not ResearchPacketSourceFreshnessAuthorityJoinV2ReasonCodeCount:
            raise ValueError(
                "reason_code_counts items must be "
                "ResearchPacketSourceFreshnessAuthorityJoinV2ReasonCodeCount",
            )
        _require_hard_flags("reason code count", item)
    reason_codes = tuple(item.reason_code for item in normalized)
    expected_order = tuple(
        reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in reason_codes
    )
    if reason_codes != expected_order:
        raise ValueError("reason_code_counts must use canonical ordering")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_code_counts must not contain duplicates")
    return normalized


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        _require_reason_code("reason_code", reason_code)
    expected_order = tuple(
        reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in normalized
    )
    if normalized != expected_order:
        raise ValueError("reason_codes must use canonical ordering")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public detail")


def _require_row_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _ROW_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_report_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _REPORT_STATUSES:
        raise ValueError(f"{field_name} must be empty, pass, watch, or block")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _decimal_count(value: int) -> Decimal:
    if not isinstance(value, int) or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(max(_quantize(value), _ZERO), _ONE)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext() as context:
            context.rounding = ROUND_HALF_UP
            return value.quantize(_QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _report_values_without_digest(
    report: ResearchPacketSourceFreshnessAuthorityJoinV2Report,
) -> dict[str, object]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "report_status": report.report_status,
        "packet_count": report.packet_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "stale_source_count": report.stale_source_count,
        "low_authority_count": report.low_authority_count,
        "proxy_dependent_count": report.proxy_dependent_count,
        "conflict_count": report.conflict_count,
        "min_quality_score": report.min_quality_score,
        "rows": report.rows,
        "reason_code_counts": report.reason_code_counts,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _report_payload_without_digest(
    *,
    generated_at: datetime,
    config_version: str,
    report_status: str,
    packet_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    stale_source_count: Decimal,
    low_authority_count: Decimal,
    proxy_dependent_count: Decimal,
    conflict_count: Decimal,
    min_quality_score: Decimal,
    rows: tuple[ResearchPacketSourceFreshnessAuthorityJoinV2Row, ...],
    reason_code_counts: tuple[
        ResearchPacketSourceFreshnessAuthorityJoinV2ReasonCodeCount,
        ...,
    ],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> dict[str, object]:
    return {
        "generated_at": _json_ready(generated_at),
        "config_version": config_version,
        "report_status": report_status,
        "packet_count": _json_ready(packet_count),
        "pass_count": _json_ready(pass_count),
        "watch_count": _json_ready(watch_count),
        "block_count": _json_ready(block_count),
        "stale_source_count": _json_ready(stale_source_count),
        "low_authority_count": _json_ready(low_authority_count),
        "proxy_dependent_count": _json_ready(proxy_dependent_count),
        "conflict_count": _json_ready(conflict_count),
        "min_quality_score": _json_ready(min_quality_score),
        "rows": [_row_payload(row) for row in rows],
        "reason_code_counts": [
            _reason_code_count_payload(item) for item in reason_code_counts
        ],
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }


def _row_payload(
    row: ResearchPacketSourceFreshnessAuthorityJoinV2Row,
) -> dict[str, object]:
    return {
        "packet_id": row.packet_id,
        "event_slug": row.event_slug,
        "category": row.category,
        "newest_source_age_seconds": _json_ready(row.newest_source_age_seconds),
        "oldest_source_age_seconds": _json_ready(row.oldest_source_age_seconds),
        "authority_score": _json_ready(row.authority_score),
        "proxy_dependency_ratio": _json_ready(row.proxy_dependency_ratio),
        "conflicting_source_count": _json_ready(row.conflicting_source_count),
        "freshness_authority_score": _json_ready(row.freshness_authority_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _reason_code_count_payload(
    item: ResearchPacketSourceFreshnessAuthorityJoinV2ReasonCodeCount,
) -> dict[str, object]:
    return {
        "reason_code": item.reason_code,
        "count": _json_ready(item.count),
        "paper_only": item.paper_only,
        "report_only": item.report_only,
        "readonly": item.readonly,
    }


def _report_payload(
    report: ResearchPacketSourceFreshnessAuthorityJoinV2Report,
) -> dict[str, object]:
    payload = _report_payload_without_digest(**_report_values_without_digest(report))
    payload[_DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
    return payload


def _report_digest_from_values(values: dict[str, object]) -> str:
    payload = _report_payload_without_digest(
        generated_at=_require_mapping_value(values, "generated_at", datetime),
        config_version=_require_mapping_value(values, "config_version", str),
        report_status=_require_mapping_value(values, "report_status", str),
        packet_count=_require_mapping_value(values, "packet_count", Decimal),
        pass_count=_require_mapping_value(values, "pass_count", Decimal),
        watch_count=_require_mapping_value(values, "watch_count", Decimal),
        block_count=_require_mapping_value(values, "block_count", Decimal),
        stale_source_count=_require_mapping_value(
            values,
            "stale_source_count",
            Decimal,
        ),
        low_authority_count=_require_mapping_value(
            values,
            "low_authority_count",
            Decimal,
        ),
        proxy_dependent_count=_require_mapping_value(
            values,
            "proxy_dependent_count",
            Decimal,
        ),
        conflict_count=_require_mapping_value(values, "conflict_count", Decimal),
        min_quality_score=_require_mapping_value(values, "min_quality_score", Decimal),
        rows=_require_mapping_value(values, "rows", tuple),
        reason_code_counts=_require_mapping_value(values, "reason_code_counts", tuple),
        paper_only=_require_mapping_value(values, "paper_only", bool),
        report_only=_require_mapping_value(values, "report_only", bool),
        readonly=_require_mapping_value(values, "readonly", bool),
    )
    return _digest_payload(payload)


def _require_mapping_value(
    values: dict[str, object],
    key: str,
    expected_type: type,
) -> Any:
    value = values[key]
    if type(value) is not expected_type:
        raise ValueError(f"{key} must be {expected_type.__name__}")
    return value


def _validate_public_payload_digest(payload: dict[str, object]) -> None:
    if _DERIVED_VALIDATION_DIGEST_FIELD not in payload:
        raise ValueError("derived_validation_digest is required")
    _require_sha256_digest(
        _DERIVED_VALIDATION_DIGEST_FIELD,
        payload[_DERIVED_VALIDATION_DIGEST_FIELD],
    )
    digest_payload = dict(payload)
    digest_payload.pop(_DERIVED_VALIDATION_DIGEST_FIELD)
    if payload[_DERIVED_VALIDATION_DIGEST_FIELD] != _digest_payload(digest_payload):
        raise ValueError("derived_validation_digest mismatch")


def _digest_payload(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> Any:
    if type(value) is ResearchPacketSourceFreshnessAuthorityJoinV2Report:
        return _report_payload(value)
    if type(value) is ResearchPacketSourceFreshnessAuthorityJoinV2Row:
        return _row_payload(value)
    if type(value) is ResearchPacketSourceFreshnessAuthorityJoinV2ReasonCodeCount:
        return _reason_code_count_payload(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return _copy_json_object(value)
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    raise ValueError("value is not JSON-ready")


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied: dict[str, object] = {}
    for key, nested_value in value.items():
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        copied[key] = _copy_json_value(nested_value)
    return copied


def _copy_json_value(value: object) -> object:
    if type(value) is dict:
        return _copy_json_object(value)
    if type(value) is list:
        return [_copy_json_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, Decimal):
        raise ValueError("JSON payload values must serialize Decimal values as strings")
    if isinstance(value, (float, int)):
        raise ValueError("JSON payload numeric values must be strings")
    raise ValueError("JSON payload is not JSON-ready")


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
            ResearchPacketSourceFreshnessAuthorityJoinV2Config,
            ResearchPacketSourceFreshnessAuthorityInput,
            ResearchPacketSourceFreshnessAuthorityJoinV2Row,
            ResearchPacketSourceFreshnessAuthorityJoinV2ReasonCodeCount,
            ResearchPacketSourceFreshnessAuthorityJoinV2Report,
        ):
            raise ValueError(f"{current_path} must be a supported public dataclass")
        for field in fields(value):
            if _has_unsafe_public_fragment(field.name):
                raise ValueError(f"{field.name} has unsafe public field")
            field_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field_path,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{current_path} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{current_path} must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{current_path} must be timezone-aware")
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is dict:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{item_path} has unsafe public field")
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(
                label,
                item,
                item_path,
                allow_json_containers=True,
            )
        return
    if type(value) is list:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=True,
            )
        return
    if type(value) is str:
        if value.strip() != value:
            raise ValueError(f"{current_path} has unsafe public value")
        if "://" in value or "?" in value:
            raise ValueError(f"{current_path} has unsafe public value")
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{current_path} has unsafe public value")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, (float, int)):
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    raise ValueError(f"{current_path} is not JSON-ready")


def _has_unsafe_public_fragment(value: str) -> bool:
    tokens = tuple(token for token in re.split(r"[^a-z0-9]+", value.lower()) if token)
    return any(token in _UNSAFE_PUBLIC_TOKENS for token in tokens)


__all__ = (
    "DEFAULT_RESEARCH_PACKET_SOURCE_FRESHNESS_AUTHORITY_JOIN_V2_CONFIG_VERSION",
    "ResearchPacketSourceFreshnessAuthorityJoinV2Config",
    "ResearchPacketSourceFreshnessAuthorityInput",
    "ResearchPacketSourceFreshnessAuthorityJoinV2Row",
    "ResearchPacketSourceFreshnessAuthorityJoinV2ReasonCodeCount",
    "ResearchPacketSourceFreshnessAuthorityJoinV2Report",
    "build_research_packet_source_freshness_authority_join_v2_report",
    "research_packet_source_freshness_authority_join_v2_payload",
)
