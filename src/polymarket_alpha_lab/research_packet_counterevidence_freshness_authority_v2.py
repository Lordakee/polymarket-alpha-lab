"""Phase 1 report-only counterevidence freshness and authority gate."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Iterable


DEFAULT_RESEARCH_PACKET_COUNTEREVIDENCE_FRESHNESS_AUTHORITY_V2_CONFIG_VERSION = (
    "research-packet-counterevidence-freshness-authority-v2"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_COUNTEREVIDENCE_WEIGHT = Decimal("0.400000")
_FRESHNESS_WEIGHT = Decimal("0.300000")
_AUTHORITY_WEIGHT = Decimal("0.300000")
_CONTRADICTION_PENALTY = Decimal("0.100000")
_MISSING_OFFICIAL_SOURCE_PENALTY = Decimal("0.100000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_ROW_STATUSES = frozenset(("pass", "watch", "block"))
_REPORT_STATUSES = frozenset(("empty", "pass", "watch", "block"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TOKENS = frozenset(
    (
        "live",
        "auth",
        "account",
        "private",
        "secret",
        "token",
        "wallet",
        "key",
        "broker",
        "trade",
        "buy",
        "sell",
        "signing",
        "mutation",
        "exchange",
        "network",
        "database",
        "persist",
        "cancel",
        "replace",
    ),
)
_REASON_CODE_SEQUENCE = (
    "counterevidence_quorum_below_floor",
    "source_age_stale",
    "authority_score_below_floor",
    "source_contradiction_present",
    "official_source_missing",
    "readiness_score_below_pass",
    "counterevidence_freshness_authority_pass",
    "counterevidence_freshness_authority_watch",
    "counterevidence_freshness_authority_block",
)
_DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"


@dataclass(frozen=True)
class ResearchPacketCounterevidenceFreshnessAuthorityV2Config:
    max_source_age_seconds: Decimal
    min_counterevidence_quorum_ratio: Decimal
    min_authority_score: Decimal
    pass_readiness_score: Decimal
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_COUNTEREVIDENCE_FRESHNESS_AUTHORITY_V2_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketCounterevidenceFreshnessAuthorityV2Config:
            raise TypeError(
                "ResearchPacketCounterevidenceFreshnessAuthorityV2Config does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketCounterevidenceFreshnessAuthorityV2Config:
            raise ValueError(
                "config must be exactly "
                "ResearchPacketCounterevidenceFreshnessAuthorityV2Config",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_COUNTEREVIDENCE_FRESHNESS_AUTHORITY_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _require_positive_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        for field_name in (
            "min_counterevidence_quorum_ratio",
            "min_authority_score",
            "pass_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchPacketCounterevidenceFreshnessAuthorityV2Input:
    packet_id: str
    event_slug: str
    category: str
    counterevidence_quorum_ratio: Decimal
    source_age_seconds: Decimal
    authority_score: Decimal
    contradiction_count: Decimal
    official_source_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketCounterevidenceFreshnessAuthorityV2Input:
            raise TypeError(
                "ResearchPacketCounterevidenceFreshnessAuthorityV2Input does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketCounterevidenceFreshnessAuthorityV2Input:
            raise ValueError(
                "input must be exactly "
                "ResearchPacketCounterevidenceFreshnessAuthorityV2Input",
            )
        for field_name in ("packet_id", "event_slug", "category"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "counterevidence_quorum_ratio",
            _require_ratio_decimal(
                "counterevidence_quorum_ratio",
                self.counterevidence_quorum_ratio,
            ),
        )
        object.__setattr__(
            self,
            "source_age_seconds",
            _require_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        object.__setattr__(
            self,
            "authority_score",
            _require_ratio_decimal("authority_score", self.authority_score),
        )
        for field_name in ("contradiction_count", "official_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchPacketCounterevidenceFreshnessAuthorityV2Row:
    packet_id: str
    event_slug: str
    category: str
    counterevidence_quorum_ratio: Decimal
    source_age_seconds: Decimal
    authority_score: Decimal
    contradiction_count: Decimal
    official_source_count: Decimal
    freshness_score: Decimal
    readiness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketCounterevidenceFreshnessAuthorityV2Row:
            raise TypeError(
                "ResearchPacketCounterevidenceFreshnessAuthorityV2Row does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketCounterevidenceFreshnessAuthorityV2Row:
            raise ValueError(
                "row must be exactly "
                "ResearchPacketCounterevidenceFreshnessAuthorityV2Row",
            )
        for field_name in ("packet_id", "event_slug", "category"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in (
            "counterevidence_quorum_ratio",
            "authority_score",
            "freshness_score",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_age_seconds",
            _require_nonnegative_decimal("source_age_seconds", self.source_age_seconds),
        )
        for field_name in ("contradiction_count", "official_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_row_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_sha256_digest(
            _DERIVED_VALIDATION_DIGEST_FIELD,
            self.derived_validation_digest,
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        expected_digest = _row_digest_from_values(_row_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match row payload")


@dataclass(frozen=True)
class ResearchPacketCounterevidenceFreshnessAuthorityV2Report:
    config_version: str
    report_status: str
    packet_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_source_count: Decimal
    low_authority_count: Decimal
    low_quorum_count: Decimal
    contradiction_count: Decimal
    min_readiness_score: Decimal
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    rows: tuple[ResearchPacketCounterevidenceFreshnessAuthorityV2Row, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketCounterevidenceFreshnessAuthorityV2Report:
            raise TypeError(
                "ResearchPacketCounterevidenceFreshnessAuthorityV2Report does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketCounterevidenceFreshnessAuthorityV2Report:
            raise ValueError(
                "report must be exactly "
                "ResearchPacketCounterevidenceFreshnessAuthorityV2Report",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_COUNTEREVIDENCE_FRESHNESS_AUTHORITY_V2_CONFIG_VERSION
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
            "low_quorum_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_readiness_score",
            _require_ratio_decimal("min_readiness_score", self.min_readiness_score),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_sha256_digest(
            _DERIVED_VALIDATION_DIGEST_FIELD,
            self.derived_validation_digest,
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        _validate_report_consistency(self)

    @property
    def payload(self) -> dict[str, object]:
        return research_packet_counterevidence_freshness_authority_v2_payload(self)


def build_research_packet_counterevidence_freshness_authority_v2_report(
    packet_inputs: Iterable[ResearchPacketCounterevidenceFreshnessAuthorityV2Input],
    *,
    config: ResearchPacketCounterevidenceFreshnessAuthorityV2Config,
) -> ResearchPacketCounterevidenceFreshnessAuthorityV2Report:
    """Build a local, deterministic Phase 1 research quality report."""

    if type(config) is not ResearchPacketCounterevidenceFreshnessAuthorityV2Config:
        raise ValueError(
            "config must be a "
            "ResearchPacketCounterevidenceFreshnessAuthorityV2Config",
        )
    _require_hard_flags("config", config)
    normalized_inputs = _normalize_inputs(packet_inputs)
    rows = tuple(
        sorted(
            (_row_for_input(item, config) for item in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "config_version": config.config_version,
        "report_status": _report_status(rows),
        "packet_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "stale_source_count": _decimal_count(
            _reason_row_count(rows, "source_age_stale"),
        ),
        "low_authority_count": _decimal_count(
            _reason_row_count(rows, "authority_score_below_floor"),
        ),
        "low_quorum_count": _decimal_count(
            _reason_row_count(rows, "counterevidence_quorum_below_floor"),
        ),
        "contradiction_count": sum(
            (row.contradiction_count for row in rows),
            Decimal("0"),
        ),
        "min_readiness_score": min(
            (row.readiness_score for row in rows),
            default=_ZERO,
        ),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchPacketCounterevidenceFreshnessAuthorityV2Report(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_packet_counterevidence_freshness_authority_v2_payload(
    value: ResearchPacketCounterevidenceFreshnessAuthorityV2Report | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchPacketCounterevidenceFreshnessAuthorityV2Report:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_public_payload_object(value)
    else:
        raise ValueError(
            "value must be a "
            "ResearchPacketCounterevidenceFreshnessAuthorityV2Report or dict",
        )
    validate_research_packet_counterevidence_freshness_authority_v2_public_payload(
        payload,
    )
    return payload


def validate_research_packet_counterevidence_freshness_authority_v2_public_payload(
    payload: dict[str, object],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_unsafe_public_payload("public payload", payload, allow_json_containers=True)
    _require_public_payload_hard_flags(payload)
    _validate_public_row_digests(payload)
    _validate_public_report_digest(payload)


def _row_for_input(
    item: ResearchPacketCounterevidenceFreshnessAuthorityV2Input,
    config: ResearchPacketCounterevidenceFreshnessAuthorityV2Config,
) -> ResearchPacketCounterevidenceFreshnessAuthorityV2Row:
    freshness_score = _freshness_score(item, config)
    readiness_score = _readiness_score(
        counterevidence_quorum_ratio=item.counterevidence_quorum_ratio,
        freshness_score=freshness_score,
        authority_score=item.authority_score,
        contradiction_count=item.contradiction_count,
        official_source_count=item.official_source_count,
    )
    reason_codes = _row_reason_codes(
        item=item,
        freshness_score=freshness_score,
        readiness_score=readiness_score,
        config=config,
    )
    status = _row_status(reason_codes)
    values: dict[str, object] = {
        "packet_id": item.packet_id,
        "event_slug": item.event_slug,
        "category": item.category,
        "counterevidence_quorum_ratio": item.counterevidence_quorum_ratio,
        "source_age_seconds": item.source_age_seconds,
        "authority_score": item.authority_score,
        "contradiction_count": item.contradiction_count,
        "official_source_count": item.official_source_count,
        "freshness_score": freshness_score,
        "readiness_score": readiness_score,
        "status": status,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchPacketCounterevidenceFreshnessAuthorityV2Row(
        **values,
        derived_validation_digest=_row_digest_from_values(values),
    )


def _freshness_score(
    item: ResearchPacketCounterevidenceFreshnessAuthorityV2Input,
    config: ResearchPacketCounterevidenceFreshnessAuthorityV2Config,
) -> Decimal:
    if item.source_age_seconds >= config.max_source_age_seconds:
        return _ZERO
    return _clamp_ratio(_ONE - (item.source_age_seconds / config.max_source_age_seconds))


def _readiness_score(
    *,
    counterevidence_quorum_ratio: Decimal,
    freshness_score: Decimal,
    authority_score: Decimal,
    contradiction_count: Decimal,
    official_source_count: Decimal,
) -> Decimal:
    contradiction_penalty = contradiction_count * _CONTRADICTION_PENALTY
    official_source_penalty = (
        _MISSING_OFFICIAL_SOURCE_PENALTY
        if official_source_count == Decimal("0")
        else _ZERO
    )
    return _clamp_ratio(
        counterevidence_quorum_ratio * _COUNTEREVIDENCE_WEIGHT
        + freshness_score * _FRESHNESS_WEIGHT
        + authority_score * _AUTHORITY_WEIGHT
        - contradiction_penalty
        - official_source_penalty,
    )


def _row_reason_codes(
    *,
    item: ResearchPacketCounterevidenceFreshnessAuthorityV2Input,
    freshness_score: Decimal,
    readiness_score: Decimal,
    config: ResearchPacketCounterevidenceFreshnessAuthorityV2Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.counterevidence_quorum_ratio < config.min_counterevidence_quorum_ratio:
        reason_codes.append("counterevidence_quorum_below_floor")
    if freshness_score == _ZERO and item.source_age_seconds >= config.max_source_age_seconds:
        reason_codes.append("source_age_stale")
    if item.authority_score < config.min_authority_score:
        reason_codes.append("authority_score_below_floor")
    if item.contradiction_count > Decimal("0"):
        reason_codes.append("source_contradiction_present")
    if item.official_source_count == Decimal("0"):
        reason_codes.append("official_source_missing")
    if readiness_score < config.pass_readiness_score:
        reason_codes.append("readiness_score_below_pass")
    reason_codes.append(f"counterevidence_freshness_authority_{_row_status(tuple(reason_codes))}")
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code in reason_codes
        for reason_code in (
            "counterevidence_quorum_below_floor",
            "authority_score_below_floor",
            "source_contradiction_present",
            "official_source_missing",
        )
    ):
        return "block"
    if (
        "source_age_stale" in reason_codes
        or "readiness_score_below_pass" in reason_codes
    ):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchPacketCounterevidenceFreshnessAuthorityV2Row, ...],
) -> str:
    if not rows:
        return "empty"
    if _status_count(rows, "block"):
        return "block"
    if _status_count(rows, "watch"):
        return "watch"
    return "pass"


def _row_sort_key(
    row: ResearchPacketCounterevidenceFreshnessAuthorityV2Row,
) -> tuple[Decimal, Decimal, str, str, str]:
    severity = {"block": Decimal("0"), "watch": Decimal("1"), "pass": Decimal("2")}
    return (
        severity[row.status],
        row.readiness_score,
        row.packet_id,
        row.event_slug,
        row.category,
    )


def _status_count(
    rows: tuple[ResearchPacketCounterevidenceFreshnessAuthorityV2Row, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _reason_row_count(
    rows: tuple[ResearchPacketCounterevidenceFreshnessAuthorityV2Row, ...],
    reason_code: str,
) -> int:
    return sum(1 for row in rows if reason_code in row.reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchPacketCounterevidenceFreshnessAuthorityV2Row, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts: list[tuple[str, Decimal]] = []
    for reason_code in _REASON_CODE_SEQUENCE:
        count = _reason_row_count(rows, reason_code)
        if count:
            counts.append((reason_code, _decimal_count(count)))
    return tuple(counts)


def _validate_report_consistency(
    report: ResearchPacketCounterevidenceFreshnessAuthorityV2Report,
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
        _reason_row_count(report.rows, "source_age_stale"),
    ):
        raise ValueError("stale_source_count must match rows")
    if report.low_authority_count != _decimal_count(
        _reason_row_count(report.rows, "authority_score_below_floor"),
    ):
        raise ValueError("low_authority_count must match rows")
    if report.low_quorum_count != _decimal_count(
        _reason_row_count(report.rows, "counterevidence_quorum_below_floor"),
    ):
        raise ValueError("low_quorum_count must match rows")
    expected_contradiction_count = sum(
        (row.contradiction_count for row in report.rows),
        Decimal("0"),
    )
    if report.contradiction_count != expected_contradiction_count:
        raise ValueError("contradiction_count must match rows")
    expected_min_readiness_score = min(
        (row.readiness_score for row in report.rows),
        default=_ZERO,
    )
    if report.min_readiness_score != expected_min_readiness_score:
        raise ValueError("min_readiness_score must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_inputs(
    packet_inputs: Iterable[ResearchPacketCounterevidenceFreshnessAuthorityV2Input],
) -> tuple[ResearchPacketCounterevidenceFreshnessAuthorityV2Input, ...]:
    if isinstance(packet_inputs, (str, bytes)):
        raise ValueError("packet_inputs must be an iterable")
    try:
        values = tuple(packet_inputs)
    except TypeError as exc:
        raise ValueError("packet_inputs must be an iterable") from exc
    for item in values:
        if type(item) is not ResearchPacketCounterevidenceFreshnessAuthorityV2Input:
            raise ValueError(
                "packet_inputs items must be "
                "ResearchPacketCounterevidenceFreshnessAuthorityV2Input",
            )
        _require_hard_flags("input", item)
    packet_ids = tuple(item.packet_id for item in values)
    if len(set(packet_ids)) != len(packet_ids):
        raise ValueError("duplicate packet_id values are not allowed")
    return values


def _normalize_rows(
    rows: tuple[ResearchPacketCounterevidenceFreshnessAuthorityV2Row, ...],
) -> tuple[ResearchPacketCounterevidenceFreshnessAuthorityV2Row, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchPacketCounterevidenceFreshnessAuthorityV2Row:
            raise ValueError(
                "rows items must be "
                "ResearchPacketCounterevidenceFreshnessAuthorityV2Row",
            )
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic readiness ordering")
    packet_ids = tuple(row.packet_id for row in normalized)
    if len(set(packet_ids)) != len(packet_ids):
        raise ValueError("rows packet_id values must be unique")
    return normalized


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
    canonical = tuple(
        reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in reason_codes
    )
    if reason_codes != canonical:
        raise ValueError("reason_codes must use canonical ordering")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    return canonical


def _normalize_reason_code_counts(
    reason_code_counts: tuple[tuple[str, Decimal], ...],
) -> tuple[tuple[str, Decimal], ...]:
    if type(reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[tuple[str, Decimal]] = []
    for item in reason_code_counts:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError("reason_code_counts entries must be reason/count tuples")
        reason_code, count = item
        _require_reason_code("reason_code", reason_code)
        normalized.append(
            (
                reason_code,
                _require_positive_count_decimal("reason_code_count", count),
            ),
        )
    canonical = tuple(
        item
        for reason_code in _REASON_CODE_SEQUENCE
        for item in normalized
        if item[0] == reason_code
    )
    if tuple(normalized) != canonical:
        raise ValueError("reason_code_counts must use canonical ordering")
    reason_codes = tuple(item[0] for item in normalized)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_code_counts must not contain duplicates")
    return canonical


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public value")
    return value


def _require_row_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _ROW_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_report_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _REPORT_STATUSES:
        raise ValueError(f"{field_name} must be empty, pass, watch, or block")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_public_payload_hard_flags(payload: dict[str, object]) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for public payload")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(decimal_value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= Decimal("0"):
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < Decimal("0") or decimal_value > Decimal("1"):
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize(decimal_value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return decimal_value.to_integral_value()


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value <= Decimal("0"):
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value)


def _clamp_ratio(value: Decimal) -> Decimal:
    quantized = _quantize(value)
    if quantized < _ZERO:
        return _ZERO
    if quantized > _ONE:
        return _ONE
    return quantized


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext() as context:
            context.rounding = ROUND_HALF_UP
            return value.quantize(_QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _row_values_without_digest(
    row: ResearchPacketCounterevidenceFreshnessAuthorityV2Row,
) -> dict[str, object]:
    return {
        "packet_id": row.packet_id,
        "event_slug": row.event_slug,
        "category": row.category,
        "counterevidence_quorum_ratio": row.counterevidence_quorum_ratio,
        "source_age_seconds": row.source_age_seconds,
        "authority_score": row.authority_score,
        "contradiction_count": row.contradiction_count,
        "official_source_count": row.official_source_count,
        "freshness_score": row.freshness_score,
        "readiness_score": row.readiness_score,
        "status": row.status,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_values_without_digest(
    report: ResearchPacketCounterevidenceFreshnessAuthorityV2Report,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "report_status": report.report_status,
        "packet_count": report.packet_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "stale_source_count": report.stale_source_count,
        "low_authority_count": report.low_authority_count,
        "low_quorum_count": report.low_quorum_count,
        "contradiction_count": report.contradiction_count,
        "min_readiness_score": report.min_readiness_score,
        "reason_code_counts": report.reason_code_counts,
        "rows": report.rows,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_payload_without_digest(
    values: dict[str, object],
) -> dict[str, object]:
    return {
        "packet_id": _require_mapping_value(values, "packet_id", str),
        "event_slug": _require_mapping_value(values, "event_slug", str),
        "category": _require_mapping_value(values, "category", str),
        "counterevidence_quorum_ratio": _json_ready(
            _require_mapping_value(values, "counterevidence_quorum_ratio", Decimal),
        ),
        "source_age_seconds": _json_ready(
            _require_mapping_value(values, "source_age_seconds", Decimal),
        ),
        "authority_score": _json_ready(
            _require_mapping_value(values, "authority_score", Decimal),
        ),
        "contradiction_count": _json_ready(
            _require_mapping_value(values, "contradiction_count", Decimal),
        ),
        "official_source_count": _json_ready(
            _require_mapping_value(values, "official_source_count", Decimal),
        ),
        "freshness_score": _json_ready(
            _require_mapping_value(values, "freshness_score", Decimal),
        ),
        "readiness_score": _json_ready(
            _require_mapping_value(values, "readiness_score", Decimal),
        ),
        "status": _require_mapping_value(values, "status", str),
        "reason_codes": _json_ready(
            _require_mapping_value(values, "reason_codes", tuple),
        ),
        "paper_only": _require_mapping_value(values, "paper_only", bool),
        "report_only": _require_mapping_value(values, "report_only", bool),
        "readonly": _require_mapping_value(values, "readonly", bool),
    }


def _report_payload_without_digest(
    values: dict[str, object],
) -> dict[str, object]:
    return {
        "config_version": _require_mapping_value(values, "config_version", str),
        "report_status": _require_mapping_value(values, "report_status", str),
        "packet_count": _json_ready(
            _require_mapping_value(values, "packet_count", Decimal),
        ),
        "pass_count": _json_ready(
            _require_mapping_value(values, "pass_count", Decimal),
        ),
        "watch_count": _json_ready(
            _require_mapping_value(values, "watch_count", Decimal),
        ),
        "block_count": _json_ready(
            _require_mapping_value(values, "block_count", Decimal),
        ),
        "stale_source_count": _json_ready(
            _require_mapping_value(values, "stale_source_count", Decimal),
        ),
        "low_authority_count": _json_ready(
            _require_mapping_value(values, "low_authority_count", Decimal),
        ),
        "low_quorum_count": _json_ready(
            _require_mapping_value(values, "low_quorum_count", Decimal),
        ),
        "contradiction_count": _json_ready(
            _require_mapping_value(values, "contradiction_count", Decimal),
        ),
        "min_readiness_score": _json_ready(
            _require_mapping_value(values, "min_readiness_score", Decimal),
        ),
        "reason_code_counts": _reason_code_counts_payload(
            _require_mapping_value(values, "reason_code_counts", tuple),
        ),
        "rows": _json_ready(_require_mapping_value(values, "rows", tuple)),
        "paper_only": _require_mapping_value(values, "paper_only", bool),
        "report_only": _require_mapping_value(values, "report_only", bool),
        "readonly": _require_mapping_value(values, "readonly", bool),
    }


def _row_payload(
    row: ResearchPacketCounterevidenceFreshnessAuthorityV2Row,
) -> dict[str, object]:
    payload = _row_payload_without_digest(_row_values_without_digest(row))
    payload[_DERIVED_VALIDATION_DIGEST_FIELD] = row.derived_validation_digest
    return payload


def _report_payload(
    report: ResearchPacketCounterevidenceFreshnessAuthorityV2Report,
) -> dict[str, object]:
    payload = _report_payload_without_digest(_report_values_without_digest(report))
    payload[_DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
    return payload


def _reason_code_counts_payload(
    reason_code_counts: tuple[tuple[str, Decimal], ...],
) -> dict[str, object]:
    return {
        reason_code: _json_ready(count)
        for reason_code, count in reason_code_counts
    }


def _row_digest_from_values(values: dict[str, object]) -> str:
    return _digest_payload(_row_payload_without_digest(values))


def _report_digest_from_values(values: dict[str, object]) -> str:
    return _digest_payload(_report_payload_without_digest(values))


def _digest_payload(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_mapping_value(
    values: dict[str, object],
    key: str,
    expected_type: type,
) -> Any:
    value = values[key]
    if type(value) is not expected_type:
        raise ValueError(f"{key} must be {expected_type.__name__}")
    return value


def _json_ready(value: object) -> Any:
    if type(value) is ResearchPacketCounterevidenceFreshnessAuthorityV2Row:
        return _row_payload(value)
    if type(value) is ResearchPacketCounterevidenceFreshnessAuthorityV2Report:
        return _report_payload(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return _copy_public_payload_object(value)
    if value is None or type(value) in (str, bool):
        return value
    if type(value) is float:
        raise ValueError("payload value must not be a float")
    if type(value) is int:
        raise ValueError("payload value must use Decimal-derived string values")
    raise ValueError("payload value is not JSON-ready")


def _copy_public_payload_object(value: dict[str, object]) -> dict[str, object]:
    copied: dict[str, object] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("public payload keys must be strings")
        copied[key] = _copy_public_payload_value(item)
    return copied


def _copy_public_payload_value(value: object) -> object:
    if type(value) is dict:
        return _copy_public_payload_object(value)
    if type(value) is list:
        return [_copy_public_payload_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if type(value) is Decimal:
        raise ValueError("public payload numerics must be Decimal-derived string values")
    if type(value) is float:
        raise ValueError("public payload value must not be a float")
    if type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived string values")
    raise ValueError("public payload value is not JSON-ready")


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
            ResearchPacketCounterevidenceFreshnessAuthorityV2Config,
            ResearchPacketCounterevidenceFreshnessAuthorityV2Input,
            ResearchPacketCounterevidenceFreshnessAuthorityV2Row,
            ResearchPacketCounterevidenceFreshnessAuthorityV2Report,
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
    if type(value) is dict:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
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
    if type(value) is tuple:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        if allow_json_containers:
            raise ValueError(
                f"{current_path} must use Decimal-derived string values",
            )
        return
    if type(value) is str:
        if value.strip() != value or "://" in value or "?" in value or "@" in value:
            raise ValueError(f"{current_path} has unsafe public value")
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{current_path} has unsafe public value")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is float:
        raise ValueError(f"{current_path} must not be a float")
    if type(value) is int:
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    raise ValueError(f"{current_path} is not JSON-ready")


def _has_unsafe_public_fragment(value: str) -> bool:
    tokens = tuple(token for token in re.split(r"[^a-z0-9]+", value.lower()) if token)
    return any(token in _UNSAFE_PUBLIC_TOKENS for token in tokens)


def _validate_public_row_digests(payload: dict[str, object]) -> None:
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a public payload list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain public payload dicts")
        if _DERIVED_VALIDATION_DIGEST_FIELD not in row:
            raise ValueError("derived_validation_digest is required for rows")
        _require_sha256_digest(
            _DERIVED_VALIDATION_DIGEST_FIELD,
            row[_DERIVED_VALIDATION_DIGEST_FIELD],
        )
        digest_payload = dict(row)
        digest_payload.pop(_DERIVED_VALIDATION_DIGEST_FIELD)
        if row[_DERIVED_VALIDATION_DIGEST_FIELD] != _digest_payload(digest_payload):
            raise ValueError("derived_validation_digest mismatch for row payload")


def _validate_public_report_digest(payload: dict[str, object]) -> None:
    if _DERIVED_VALIDATION_DIGEST_FIELD not in payload:
        raise ValueError("derived_validation_digest is required")
    _require_sha256_digest(
        _DERIVED_VALIDATION_DIGEST_FIELD,
        payload[_DERIVED_VALIDATION_DIGEST_FIELD],
    )
    digest_payload = dict(payload)
    digest_payload.pop(_DERIVED_VALIDATION_DIGEST_FIELD)
    if payload[_DERIVED_VALIDATION_DIGEST_FIELD] != _digest_payload(digest_payload):
        raise ValueError("derived_validation_digest mismatch for report payload")


__all__ = (
    "DEFAULT_RESEARCH_PACKET_COUNTEREVIDENCE_FRESHNESS_AUTHORITY_V2_CONFIG_VERSION",
    "ResearchPacketCounterevidenceFreshnessAuthorityV2Config",
    "ResearchPacketCounterevidenceFreshnessAuthorityV2Input",
    "ResearchPacketCounterevidenceFreshnessAuthorityV2Report",
    "ResearchPacketCounterevidenceFreshnessAuthorityV2Row",
    "build_research_packet_counterevidence_freshness_authority_v2_report",
    "research_packet_counterevidence_freshness_authority_v2_payload",
    "validate_research_packet_counterevidence_freshness_authority_v2_public_payload",
)
