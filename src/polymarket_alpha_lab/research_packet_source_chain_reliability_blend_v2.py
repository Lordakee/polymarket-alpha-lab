"""Pure in-memory research packet source reliability blend report."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_taxonomy import require_team_id


DEFAULT_RESEARCH_PACKET_SOURCE_CHAIN_RELIABILITY_BLEND_V2_CONFIG_VERSION = (
    "research-packet-source-chain-reliability-blend-v2"
)

PASSED_REASON = "source_chain_reliability_blend_v2_passed"
EMPTY_INPUT_REASON = "source_chain_reliability_blend_v2_empty_input"
CONTRADICTION_PENALTY_REASON = (
    "source_chain_reliability_blend_v2_contradiction_penalty"
)
INDEPENDENT_SOURCES_BOOSTED_REASON = (
    "source_chain_reliability_blend_v2_independent_sources_boosted"
)
BELOW_MINIMUM_RELIABILITY_REASON = (
    "source_chain_reliability_blend_v2_below_minimum_reliability"
)

REASON_CODES = (
    PASSED_REASON,
    EMPTY_INPUT_REASON,
    CONTRADICTION_PENALTY_REASON,
    INDEPENDENT_SOURCES_BOOSTED_REASON,
    BELOW_MINIMUM_RELIABILITY_REASON,
)
REPORT_REASON_SEQUENCE = (
    EMPTY_INPUT_REASON,
    CONTRADICTION_PENALTY_REASON,
    INDEPENDENT_SOURCES_BOOSTED_REASON,
    BELOW_MINIMUM_RELIABILITY_REASON,
)
RELIABILITY_STATUSES = ("ready", "watch", "blocked")
STATUS_RANK = {"blocked": 0, "watch": 1, "ready": 2}
DECIMAL_CONTEXT = Context(prec=28)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
UNSAFE_PUBLIC_FRAGMENTS = (
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

__all__ = (
    "DEFAULT_RESEARCH_PACKET_SOURCE_CHAIN_RELIABILITY_BLEND_V2_CONFIG_VERSION",
    "ResearchPacketSourceChainReliabilityBlendV2Config",
    "ResearchPacketSourceChainReliabilityBlendV2Report",
    "ResearchPacketSourceChainReliabilityBlendV2Row",
    "ResearchPacketSourceChainReliabilityBlendV2Source",
    "build_research_packet_source_chain_reliability_blend_v2_report",
    "research_packet_source_chain_reliability_blend_v2_payload",
)


@dataclass(frozen=True)
class ResearchPacketSourceChainReliabilityBlendV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_SOURCE_CHAIN_RELIABILITY_BLEND_V2_CONFIG_VERSION
    )
    min_blended_reliability: Decimal = Decimal("0.600000")
    contradiction_penalty_per_count: Decimal = Decimal("0.080000")
    independent_source_boost_per_family: Decimal = Decimal("0.030000")
    max_independent_source_boost: Decimal = Decimal("0.090000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_safe_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_blended_reliability",
            _require_ratio("min_blended_reliability", self.min_blended_reliability),
        )
        object.__setattr__(
            self,
            "contradiction_penalty_per_count",
            _require_ratio(
                "contradiction_penalty_per_count",
                self.contradiction_penalty_per_count,
            ),
        )
        object.__setattr__(
            self,
            "independent_source_boost_per_family",
            _require_ratio(
                "independent_source_boost_per_family",
                self.independent_source_boost_per_family,
            ),
        )
        object.__setattr__(
            self,
            "max_independent_source_boost",
            _require_ratio(
                "max_independent_source_boost",
                self.max_independent_source_boost,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchPacketSourceChainReliabilityBlendV2Source:
    packet_id: str
    team_id: str
    source_id: str
    source_family: str
    reliability_score: Decimal
    chain_weight: Decimal
    contradiction_count: Decimal = ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_safe_canonical_string("packet_id", self.packet_id)
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        _require_safe_canonical_string("source_id", self.source_id)
        _require_safe_canonical_string("source_family", self.source_family)
        object.__setattr__(
            self,
            "reliability_score",
            _require_ratio("reliability_score", self.reliability_score),
        )
        object.__setattr__(
            self,
            "chain_weight",
            _require_positive_decimal("chain_weight", self.chain_weight),
        )
        object.__setattr__(
            self,
            "contradiction_count",
            _require_count("contradiction_count", self.contradiction_count),
        )
        _require_hard_flags("source", self)


@dataclass(frozen=True)
class ResearchPacketSourceChainReliabilityBlendV2Row:
    packet_id: str
    team_id: str
    source_count: Decimal
    independent_source_family_count: Decimal
    total_chain_weight: Decimal
    base_reliability_score: Decimal
    contradiction_count: Decimal
    contradiction_penalty: Decimal
    independent_source_boost: Decimal
    blended_reliability_score: Decimal
    reliability_status: str
    reason_codes: tuple[str, ...]
    source_ids: tuple[str, ...]
    source_families: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_safe_canonical_string("packet_id", self.packet_id)
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        for field_name in (
            "source_count",
            "independent_source_family_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_chain_weight",
            _require_positive_decimal("total_chain_weight", self.total_chain_weight),
        )
        for field_name in (
            "base_reliability_score",
            "contradiction_penalty",
            "independent_source_boost",
            "blended_reliability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_reliability_status("reliability_status", self.reliability_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "source_ids",
            _normalize_safe_string_tuple("source_ids", self.source_ids),
        )
        object.__setattr__(
            self,
            "source_families",
            _normalize_safe_string_tuple("source_families", self.source_families),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("row", self)
        _require_matching_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
            _row_digest_payload(self),
        )
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchPacketSourceChainReliabilityBlendV2Report:
    generated_at: datetime
    config_version: str
    reliability_status: str
    packet_count: Decimal
    source_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    contradiction_penalty_count: Decimal
    independent_source_boost_count: Decimal
    average_blended_reliability: Decimal
    rows: tuple[ResearchPacketSourceChainReliabilityBlendV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_safe_canonical_string("config_version", self.config_version)
        _require_reliability_status("reliability_status", self.reliability_status)
        for field_name in (
            "packet_count",
            "source_count",
            "ready_count",
            "watch_count",
            "blocked_count",
            "contradiction_penalty_count",
            "independent_source_boost_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_blended_reliability",
            _require_ratio(
                "average_blended_reliability",
                self.average_blended_reliability,
            ),
        )
        object.__setattr__(self, "rows", _normalize_blend_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _require_matching_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
            _report_digest_payload(self),
        )
        _validate_report_consistency(self)


def build_research_packet_source_chain_reliability_blend_v2_report(
    sources: list[ResearchPacketSourceChainReliabilityBlendV2Source]
    | tuple[ResearchPacketSourceChainReliabilityBlendV2Source, ...],
    *,
    config: ResearchPacketSourceChainReliabilityBlendV2Config,
    generated_at: datetime,
) -> ResearchPacketSourceChainReliabilityBlendV2Report:
    if type(config) is not ResearchPacketSourceChainReliabilityBlendV2Config:
        raise ValueError("config must be a ResearchPacketSourceChainReliabilityBlendV2Config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_sources = _normalize_sources(sources)
    rows = tuple(
        sorted(
            (
                _row_from_sources(group, config=config)
                for group in _source_groups(normalized_sources)
            ),
            key=_row_sort_key,
        )
    )
    report = _report_from_rows(
        rows,
        config_version=config.config_version,
        generated_at=generated_at_utc,
        source_count=_count_from_int(len(normalized_sources)),
    )
    return report


def research_packet_source_chain_reliability_blend_v2_payload(
    report: ResearchPacketSourceChainReliabilityBlendV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchPacketSourceChainReliabilityBlendV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
        if type(payload) is dict and "derived_validation_digest" in payload:
            _validate_payload_digest(payload)
    else:
        raise ValueError(
            "report must be a ResearchPacketSourceChainReliabilityBlendV2Report",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


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


def _normalize_sources(
    sources: list[ResearchPacketSourceChainReliabilityBlendV2Source]
    | tuple[ResearchPacketSourceChainReliabilityBlendV2Source, ...],
) -> tuple[ResearchPacketSourceChainReliabilityBlendV2Source, ...]:
    if type(sources) not in (list, tuple):
        raise ValueError("sources must be a list or tuple")
    normalized = tuple(sources)
    seen_keys: set[tuple[str, str, str]] = set()
    for source in normalized:
        if type(source) is not ResearchPacketSourceChainReliabilityBlendV2Source:
            raise ValueError(
                "sources must contain ResearchPacketSourceChainReliabilityBlendV2Source",
            )
        _require_hard_flags("source", source)
        key = (source.team_id, source.packet_id, source.source_id)
        if key in seen_keys:
            raise ValueError("sources must be unique by team, packet, and source")
        seen_keys.add(key)
    return tuple(sorted(normalized, key=lambda item: (item.team_id, item.packet_id, item.source_id)))


def _source_groups(
    sources: tuple[ResearchPacketSourceChainReliabilityBlendV2Source, ...],
) -> tuple[tuple[ResearchPacketSourceChainReliabilityBlendV2Source, ...], ...]:
    groups: dict[tuple[str, str], list[ResearchPacketSourceChainReliabilityBlendV2Source]] = {}
    for source in sources:
        groups.setdefault((source.team_id, source.packet_id), []).append(source)
    return tuple(
        tuple(values)
        for _, values in sorted(groups.items(), key=lambda item: (item[0][0], item[0][1]))
    )


def _row_from_sources(
    sources: tuple[ResearchPacketSourceChainReliabilityBlendV2Source, ...],
    *,
    config: ResearchPacketSourceChainReliabilityBlendV2Config,
) -> ResearchPacketSourceChainReliabilityBlendV2Row:
    source_count = _count_from_int(len(sources))
    source_ids = tuple(sorted(source.source_id for source in sources))
    source_families = tuple(sorted({source.source_family for source in sources}))
    independent_source_family_count = _count_from_int(len(source_families))
    total_chain_weight = _sum_decimals(source.chain_weight for source in sources)
    weighted_score = _sum_decimals(
        source.reliability_score * source.chain_weight for source in sources
    )
    base_reliability_score = _safe_ratio(weighted_score, total_chain_weight)
    contradiction_count = _sum_decimals(source.contradiction_count for source in sources)
    contradiction_penalty = _min_decimal(
        ONE,
        contradiction_count * config.contradiction_penalty_per_count,
    )
    independent_source_boost = _independent_source_boost(
        independent_source_family_count,
        config=config,
    )
    blended_reliability_score = _clamp_ratio(
        base_reliability_score - contradiction_penalty + independent_source_boost,
    )
    reason_codes = _row_reason_codes(
        contradiction_penalty=contradiction_penalty,
        independent_source_boost=independent_source_boost,
        blended_reliability_score=blended_reliability_score,
        config=config,
    )
    reliability_status = _row_status(reason_codes)
    row_values = {
        "packet_id": sources[0].packet_id,
        "team_id": sources[0].team_id,
        "source_count": source_count,
        "independent_source_family_count": independent_source_family_count,
        "total_chain_weight": total_chain_weight,
        "base_reliability_score": base_reliability_score,
        "contradiction_count": contradiction_count,
        "contradiction_penalty": contradiction_penalty,
        "independent_source_boost": independent_source_boost,
        "blended_reliability_score": blended_reliability_score,
        "reliability_status": reliability_status,
        "reason_codes": reason_codes,
        "source_ids": source_ids,
        "source_families": source_families,
    }
    return ResearchPacketSourceChainReliabilityBlendV2Row(
        **row_values,
        derived_validation_digest=_digest(row_values),
    )


def _report_from_rows(
    rows: tuple[ResearchPacketSourceChainReliabilityBlendV2Row, ...],
    *,
    config_version: str,
    generated_at: datetime,
    source_count: Decimal,
) -> ResearchPacketSourceChainReliabilityBlendV2Report:
    packet_count = _count_from_int(len(rows))
    ready_count = _count_from_int(_status_count(rows, "ready"))
    watch_count = _count_from_int(_status_count(rows, "watch"))
    blocked_count = _count_from_int(_status_count(rows, "blocked"))
    contradiction_penalty_count = _count_from_int(
        sum(1 for row in rows if row.contradiction_penalty > ZERO),
    )
    independent_source_boost_count = _count_from_int(
        sum(1 for row in rows if row.independent_source_boost > ZERO),
    )
    average_blended_reliability = (
        ZERO
        if not rows
        else _safe_ratio(
            _sum_decimals(row.blended_reliability_score for row in rows),
            packet_count,
        )
    )
    reason_codes = _report_reason_codes(rows)
    reliability_status = _report_status(rows)
    report_values = {
        "generated_at": generated_at,
        "config_version": config_version,
        "reliability_status": reliability_status,
        "packet_count": packet_count,
        "source_count": source_count,
        "ready_count": ready_count,
        "watch_count": watch_count,
        "blocked_count": blocked_count,
        "contradiction_penalty_count": contradiction_penalty_count,
        "independent_source_boost_count": independent_source_boost_count,
        "average_blended_reliability": average_blended_reliability,
        "rows": rows,
        "reason_codes": reason_codes,
    }
    return ResearchPacketSourceChainReliabilityBlendV2Report(
        **report_values,
        derived_validation_digest=_digest(report_values),
    )


def _row_reason_codes(
    *,
    contradiction_penalty: Decimal,
    independent_source_boost: Decimal,
    blended_reliability_score: Decimal,
    config: ResearchPacketSourceChainReliabilityBlendV2Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if contradiction_penalty > ZERO:
        reason_codes.append(CONTRADICTION_PENALTY_REASON)
    if independent_source_boost > ZERO:
        reason_codes.append(INDEPENDENT_SOURCES_BOOSTED_REASON)
    if blended_reliability_score < config.min_blended_reliability:
        reason_codes.append(BELOW_MINIMUM_RELIABILITY_REASON)
    if not reason_codes:
        reason_codes.append(PASSED_REASON)
    return tuple(reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if BELOW_MINIMUM_RELIABILITY_REASON in reason_codes:
        return "blocked"
    if CONTRADICTION_PENALTY_REASON in reason_codes:
        return "watch"
    return "ready"


def _report_status(
    rows: tuple[ResearchPacketSourceChainReliabilityBlendV2Row, ...],
) -> str:
    if not rows or any(row.reliability_status == "blocked" for row in rows):
        return "blocked"
    if any(row.reliability_status == "watch" for row in rows):
        return "watch"
    return "ready"


def _report_reason_codes(
    rows: tuple[ResearchPacketSourceChainReliabilityBlendV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_INPUT_REASON,)
    reason_codes = tuple(
        reason_code
        for reason_code in REPORT_REASON_SEQUENCE
        if any(reason_code in row.reason_codes for row in rows)
    )
    return reason_codes or (PASSED_REASON,)


def _status_count(
    rows: tuple[ResearchPacketSourceChainReliabilityBlendV2Row, ...],
    reliability_status: str,
) -> int:
    return sum(1 for row in rows if row.reliability_status == reliability_status)


def _normalize_blend_rows(
    rows: list[ResearchPacketSourceChainReliabilityBlendV2Row]
    | tuple[ResearchPacketSourceChainReliabilityBlendV2Row, ...],
) -> tuple[ResearchPacketSourceChainReliabilityBlendV2Row, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized_rows = tuple(rows)
    seen_keys: set[tuple[str, str]] = set()
    for row in normalized_rows:
        if type(row) is not ResearchPacketSourceChainReliabilityBlendV2Row:
            raise ValueError("rows must contain ResearchPacketSourceChainReliabilityBlendV2Row")
        _require_hard_flags("row", row)
        key = (row.team_id, row.packet_id)
        if key in seen_keys:
            raise ValueError("rows must be unique by team and packet")
        seen_keys.add(key)
    if normalized_rows != tuple(sorted(normalized_rows, key=_row_sort_key)):
        raise ValueError("rows must use stable sort")
    return normalized_rows


def _row_sort_key(
    row: ResearchPacketSourceChainReliabilityBlendV2Row,
) -> tuple[int, Decimal, str, str]:
    return (
        STATUS_RANK[row.reliability_status],
        -row.blended_reliability_score,
        row.team_id,
        row.packet_id,
    )


def _validate_row_consistency(
    row: ResearchPacketSourceChainReliabilityBlendV2Row,
) -> None:
    if row.source_count != _count_from_int(len(row.source_ids)):
        raise ValueError("source_count must match source_ids")
    if row.independent_source_family_count != _count_from_int(len(row.source_families)):
        raise ValueError("independent_source_family_count must match source_families")
    if row.independent_source_family_count > row.source_count:
        raise ValueError("independent_source_family_count must not exceed source_count")
    if row.reliability_status != _row_status(row.reason_codes):
        raise ValueError("reliability_status must match reason_codes")
    if PASSED_REASON in row.reason_codes and row.reason_codes != (PASSED_REASON,):
        raise ValueError("passed reason must stand alone")
    expected_blend = _clamp_ratio(
        row.base_reliability_score
        - row.contradiction_penalty
        + row.independent_source_boost,
    )
    if row.blended_reliability_score != expected_blend:
        raise ValueError("blended_reliability_score must match components")


def _validate_report_consistency(
    report: ResearchPacketSourceChainReliabilityBlendV2Report,
) -> None:
    if report.packet_count != _count_from_int(len(report.rows)):
        raise ValueError("packet_count must match rows")
    if report.ready_count != _count_from_int(_status_count(report.rows, "ready")):
        raise ValueError("ready_count must match rows")
    if report.watch_count != _count_from_int(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _count_from_int(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.contradiction_penalty_count != _count_from_int(
        sum(1 for row in report.rows if row.contradiction_penalty > ZERO),
    ):
        raise ValueError("contradiction_penalty_count must match rows")
    if report.independent_source_boost_count != _count_from_int(
        sum(1 for row in report.rows if row.independent_source_boost > ZERO),
    ):
        raise ValueError("independent_source_boost_count must match rows")
    if report.source_count < report.packet_count:
        raise ValueError("source_count must cover packets")
    expected_average = (
        ZERO
        if not report.rows
        else _safe_ratio(
            _sum_decimals(row.blended_reliability_score for row in report.rows),
            report.packet_count,
        )
    )
    if report.average_blended_reliability != expected_average:
        raise ValueError("average_blended_reliability must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reliability_status != _report_status(report.rows):
        raise ValueError("reliability_status must match rows")


def _normalize_reason_codes(value: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_safe_canonical_string("reason_codes", reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError("reason_codes must contain known reason codes")
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    return reason_codes


def _normalize_safe_string_tuple(
    field_name: str,
    value: tuple[str, ...] | list[str],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    items = tuple(value)
    if not items:
        raise ValueError(f"{field_name} must not be empty")
    for item in items:
        _require_safe_canonical_string(field_name, item)
    if items != tuple(sorted(items)):
        raise ValueError(f"{field_name} must use stable sort")
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must be unique")
    return items


def _require_reliability_status(name: str, value: object) -> None:
    if type(value) is not str or value not in RELIABILITY_STATUSES:
        raise ValueError(f"{name} must be ready, watch, or blocked")


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_ratio(name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(name, value)
    if normalized > ONE:
        raise ValueError(f"{name} must be at most 1")
    return normalized


def _require_count(name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return normalized


def _require_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(value)


def _count_from_int(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _sum_decimals(values: object) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("sum values must be Decimal")
        total += value
    return _quantize(total)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _require_ratio("ratio", numerator / denominator)


def _independent_source_boost(
    independent_source_family_count: Decimal,
    *,
    config: ResearchPacketSourceChainReliabilityBlendV2Config,
) -> Decimal:
    family_delta = independent_source_family_count - ONE
    if family_delta <= ZERO:
        return ZERO
    return _min_decimal(
        config.max_independent_source_boost,
        family_delta * config.independent_source_boost_per_family,
    )


def _clamp_ratio(value: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO
    if value >= ONE:
        return ONE
    return _require_ratio("ratio", value)


def _min_decimal(left: Decimal, right: Decimal) -> Decimal:
    return _quantize(left if left <= right else right)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _require_safe_canonical_string(name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"unsafe public value in {name}")


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a sha256 digest")


def _require_matching_digest(name: str, value: str, digest_payload: object) -> None:
    if value != _digest(digest_payload):
        raise ValueError(f"{name} mismatch")


def _row_digest_payload(
    row: ResearchPacketSourceChainReliabilityBlendV2Row,
) -> dict[str, object]:
    return {
        "packet_id": row.packet_id,
        "team_id": row.team_id,
        "source_count": row.source_count,
        "independent_source_family_count": row.independent_source_family_count,
        "total_chain_weight": row.total_chain_weight,
        "base_reliability_score": row.base_reliability_score,
        "contradiction_count": row.contradiction_count,
        "contradiction_penalty": row.contradiction_penalty,
        "independent_source_boost": row.independent_source_boost,
        "blended_reliability_score": row.blended_reliability_score,
        "reliability_status": row.reliability_status,
        "reason_codes": row.reason_codes,
        "source_ids": row.source_ids,
        "source_families": row.source_families,
    }


def _report_digest_payload(
    report: ResearchPacketSourceChainReliabilityBlendV2Report,
) -> dict[str, object]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "reliability_status": report.reliability_status,
        "packet_count": report.packet_count,
        "source_count": report.source_count,
        "ready_count": report.ready_count,
        "watch_count": report.watch_count,
        "blocked_count": report.blocked_count,
        "contradiction_penalty_count": report.contradiction_penalty_count,
        "independent_source_boost_count": report.independent_source_boost_count,
        "average_blended_reliability": report.average_blended_reliability,
        "rows": report.rows,
        "reason_codes": report.reason_codes,
    }


def _digest(payload: object) -> str:
    ready = _json_ready(payload)
    encoded = _canonical_json(ready).encode("utf-8")
    return sha256(encoded).hexdigest()


def _canonical_json(value: object) -> str:
    return __import__("json").dumps(value, sort_keys=True, separators=(",", ":"))


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat().replace("+00:00", "Z")
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    _require_digest("derived_validation_digest", payload["derived_validation_digest"])
    if "rows" in payload:
        rows = payload["rows"]
        if type(rows) is not list:
            raise ValueError("rows must be a list")
        for row in rows:
            if type(row) is dict and "derived_validation_digest" in row:
                _require_matching_digest(
                    "derived_validation_digest",
                    row["derived_validation_digest"],
                    _payload_without_digest(row),
                )
    _require_matching_digest(
        "derived_validation_digest",
        payload["derived_validation_digest"],
        _payload_without_digest(payload),
    )


def _payload_without_digest(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: item
        for key, item in payload.items()
        if key != "derived_validation_digest"
    }


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, _json_ready(value))
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)
