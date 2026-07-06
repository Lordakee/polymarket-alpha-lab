from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
from typing import Any


DEFAULT_RESEARCH_PACKET_EXTERNAL_SOURCE_VERIFICATION_ROUTE_V2_CONFIG_VERSION = (
    "research-packet-external-source-verification-route-v2"
)
SOURCE_KINDS = ("official", "third_party")
SOURCE_STATUSES = ("available", "missing", "stale", "contradictory")
VERIFICATION_ROUTES = ("official_priority", "corroboration_gap", "source_missing")
ROUTE_STATUSES = ("verified", "review_required", "blocked")

_COUNT_QUANTUM = Decimal("1")
_RATIO_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ZERO_RATIO = Decimal("0.000000")
_ONE_RATIO = Decimal("1.000000")
_DERIVED_DIGEST_PREFIX = "rpesvr-v2:"
_ROW_STATUS_RANK = {"verified": 0, "review_required": 1, "blocked": 2}
_BAD_TEXT_BITS = frozenset(
    "".join(parts)
    for parts in (
        ("li", "ve"),
        ("au", "th"),
        ("wal", "let"),
        ("or", "der"),
        ("net", "work"),
        ("data", "base"),
        ("per", "sist"),
        ("sig", "ning"),
        ("muta", "tion"),
        ("b", "uy"),
        ("se", "ll"),
        ("tra", "de"),
        ("trad", "ing"),
        ("bro", "ker"),
        ("cli", "ent"),
        ("exe", "cute"),
        ("con", "nect"),
    )
)


@dataclass(frozen=True)
class ResearchPacketExternalSourceVerificationRouteV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_EXTERNAL_SOURCE_VERIFICATION_ROUTE_V2_CONFIG_VERSION
    )
    minimum_official_source_count: Decimal = Decimal("1")
    minimum_corroborating_third_party_count: Decimal = Decimal("2")
    minimum_verification_score: Decimal = Decimal("0.700000")
    stale_after_seconds: Decimal = Decimal("86400")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketExternalSourceVerificationRouteV2Config:
            raise ValueError(
                "config must be a ResearchPacketExternalSourceVerificationRouteV2Config",
            )
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "minimum_official_source_count",
            "minimum_corroborating_third_party_count",
            "stale_after_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_verification_score",
            _normalize_ratio(
                "minimum_verification_score",
                self.minimum_verification_score,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchPacketExternalSourceVerificationRouteV2Source:
    packet_id: str
    source_id: str
    source_kind: str
    source_status: str
    observed_value: str
    checked_at: datetime
    verification_score: Decimal
    corroborates_official: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketExternalSourceVerificationRouteV2Source:
            raise ValueError(
                "source must be a ResearchPacketExternalSourceVerificationRouteV2Source",
            )
        for field_name in ("packet_id", "source_id", "observed_value"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_member("source_kind", self.source_kind, SOURCE_KINDS)
        _require_member("source_status", self.source_status, SOURCE_STATUSES)
        object.__setattr__(self, "checked_at", _as_utc("checked_at", self.checked_at))
        object.__setattr__(
            self,
            "verification_score",
            _normalize_ratio("verification_score", self.verification_score),
        )
        _require_bool("corroborates_official", self.corroborates_official)
        _reject_unsafe_public_payload("source", self)
        _require_hard_flags("source", self)


@dataclass(frozen=True)
class ResearchPacketExternalSourceVerificationRouteV2Row:
    packet_id: str
    verification_route: str
    route_status: str
    official_source_count: Decimal
    third_party_source_count: Decimal
    corroborating_third_party_count: Decimal
    contradiction_source_count: Decimal
    stale_source_count: Decimal
    max_verification_score: Decimal
    latest_checked_at: datetime
    official_source_priority_applied: bool
    priority_rank: Decimal
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = field(default="", init=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketExternalSourceVerificationRouteV2Row:
            raise ValueError("row must be a ResearchPacketExternalSourceVerificationRouteV2Row")
        _require_public_string("packet_id", self.packet_id)
        _require_member("verification_route", self.verification_route, VERIFICATION_ROUTES)
        _require_member("route_status", self.route_status, ROUTE_STATUSES)
        for field_name in (
            "official_source_count",
            "third_party_source_count",
            "corroborating_third_party_count",
            "contradiction_source_count",
            "stale_source_count",
            "priority_rank",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_verification_score",
            _normalize_ratio("max_verification_score", self.max_verification_score),
        )
        object.__setattr__(
            self,
            "latest_checked_at",
            _as_utc("latest_checked_at", self.latest_checked_at),
        )
        _require_bool(
            "official_source_priority_applied",
            self.official_source_priority_applied,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        object.__setattr__(self, "derived_validation_digest", _row_derived_digest(self))
        _require_row_derived_digest(self)
        _reject_unsafe_public_payload("row", self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchPacketExternalSourceVerificationRouteV2Report:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    route_row_count: Decimal
    verified_route_count: Decimal
    review_route_count: Decimal
    blocked_route_count: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    route_rows: tuple[ResearchPacketExternalSourceVerificationRouteV2Row, ...]
    derived_validation_digest: str = field(default="", init=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketExternalSourceVerificationRouteV2Report:
            raise ValueError(
                "report must be a ResearchPacketExternalSourceVerificationRouteV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "source_row_count",
            "route_row_count",
            "verified_route_count",
            "review_route_count",
            "blocked_route_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("report_status", self.report_status, ROUTE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        rows = tuple(self.route_rows)
        for row in rows:
            if type(row) is not ResearchPacketExternalSourceVerificationRouteV2Row:
                raise ValueError("route_rows must contain verification route rows")
            _require_row_derived_digest(row)
            _require_hard_flags("row", row)
        object.__setattr__(self, "route_rows", rows)
        _validate_report(self)
        object.__setattr__(self, "derived_validation_digest", _report_derived_digest(self))
        _require_report_derived_digest(self)
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)


def build_research_packet_external_source_verification_route_v2(
    sources: (
        list[ResearchPacketExternalSourceVerificationRouteV2Source]
        | tuple[ResearchPacketExternalSourceVerificationRouteV2Source, ...]
    ),
    *,
    config: ResearchPacketExternalSourceVerificationRouteV2Config,
    generated_at: datetime,
) -> ResearchPacketExternalSourceVerificationRouteV2Report:
    if type(config) is not ResearchPacketExternalSourceVerificationRouteV2Config:
        raise ValueError("config must be a ResearchPacketExternalSourceVerificationRouteV2Config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_sources = _normalize_sources(sources)
    rows_without_rank = tuple(
        _route_row_for_packet(
            packet_sources,
            config=config,
            generated_at=generated_at_utc,
        )
        for packet_sources in _group_sources_by_packet(normalized_sources)
    )
    sorted_rows = tuple(sorted(rows_without_rank, key=_row_key))
    rows = tuple(
        _row_with_rank(row, _count(index))
        for index, row in enumerate(sorted_rows, start=1)
    )
    verified_route_count = _count(sum(1 for row in rows if row.route_status == "verified"))
    review_route_count = _count(
        sum(1 for row in rows if row.route_status == "review_required"),
    )
    blocked_route_count = _count(sum(1 for row in rows if row.route_status == "blocked"))
    report_status = _report_status(rows)
    return ResearchPacketExternalSourceVerificationRouteV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_row_count=_count(len(normalized_sources)),
        route_row_count=_count(len(rows)),
        verified_route_count=verified_route_count,
        review_route_count=review_route_count,
        blocked_route_count=blocked_route_count,
        report_status=report_status,
        reason_codes=_report_reason_codes(
            report_status,
            review_route_count=review_route_count,
            blocked_route_count=blocked_route_count,
        ),
        route_rows=rows,
    )


def research_packet_external_source_verification_route_v2_payload(
    report: ResearchPacketExternalSourceVerificationRouteV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchPacketExternalSourceVerificationRouteV2Report:
        _require_hard_flags("report", report)
        _validate_report(report)
        _require_report_derived_digest(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchPacketExternalSourceVerificationRouteV2Report")
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
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
    sources: (
        list[ResearchPacketExternalSourceVerificationRouteV2Source]
        | tuple[ResearchPacketExternalSourceVerificationRouteV2Source, ...]
    ),
) -> tuple[ResearchPacketExternalSourceVerificationRouteV2Source, ...]:
    if type(sources) not in (list, tuple):
        raise ValueError("sources must be a list or tuple")
    normalized = tuple(sources)
    seen: set[tuple[str, str]] = set()
    for source in normalized:
        if type(source) is not ResearchPacketExternalSourceVerificationRouteV2Source:
            raise ValueError("sources must contain verification source rows")
        _require_hard_flags("source", source)
        pair = (source.packet_id, source.source_id)
        if pair in seen:
            raise ValueError("sources must not contain duplicate packet source pairs")
        seen.add(pair)
    return normalized


def _group_sources_by_packet(
    sources: tuple[ResearchPacketExternalSourceVerificationRouteV2Source, ...],
) -> tuple[tuple[ResearchPacketExternalSourceVerificationRouteV2Source, ...], ...]:
    packet_ids = tuple(sorted({source.packet_id for source in sources}))
    return tuple(
        tuple(source for source in sources if source.packet_id == packet_id)
        for packet_id in packet_ids
    )


def _route_row_for_packet(
    sources: tuple[ResearchPacketExternalSourceVerificationRouteV2Source, ...],
    *,
    config: ResearchPacketExternalSourceVerificationRouteV2Config,
    generated_at: datetime,
) -> ResearchPacketExternalSourceVerificationRouteV2Row:
    packet_id = sources[0].packet_id
    official_count = _count(
        sum(
            1
            for source in sources
            if source.source_kind == "official"
            and source.source_status == "available"
            and source.verification_score >= config.minimum_verification_score
        ),
    )
    third_party_count = _count(
        sum(
            1
            for source in sources
            if source.source_kind == "third_party" and source.source_status != "missing"
        ),
    )
    corroborating_count = _count(
        sum(
            1
            for source in sources
            if source.source_kind == "third_party"
            and source.source_status == "available"
            and source.corroborates_official
            and source.verification_score >= config.minimum_verification_score
        ),
    )
    contradiction_count = _count(
        sum(
            1
            for source in sources
            if source.source_status == "contradictory"
            or (
                source.source_kind == "third_party"
                and source.source_status == "available"
                and not source.corroborates_official
            )
        ),
    )
    stale_count = _count(
        sum(
            1
            for source in sources
            if source.source_status == "stale"
            or _duration_seconds(source.checked_at, generated_at) > config.stale_after_seconds
        ),
    )
    max_score = max((source.verification_score for source in sources), default=_ZERO_RATIO)
    route, status, official_priority, reason_codes = _route_decision(
        official_count=official_count,
        corroborating_count=corroborating_count,
        contradiction_count=contradiction_count,
        stale_count=stale_count,
        max_score=max_score,
        config=config,
    )
    return ResearchPacketExternalSourceVerificationRouteV2Row(
        packet_id=packet_id,
        verification_route=route,
        route_status=status,
        official_source_count=official_count,
        third_party_source_count=third_party_count,
        corroborating_third_party_count=corroborating_count,
        contradiction_source_count=contradiction_count,
        stale_source_count=stale_count,
        max_verification_score=max_score,
        latest_checked_at=max(source.checked_at for source in sources),
        official_source_priority_applied=official_priority,
        priority_rank=_ZERO_COUNT,
        reason_codes=reason_codes,
    )


def _route_decision(
    *,
    official_count: Decimal,
    corroborating_count: Decimal,
    contradiction_count: Decimal,
    stale_count: Decimal,
    max_score: Decimal,
    config: ResearchPacketExternalSourceVerificationRouteV2Config,
) -> tuple[str, str, bool, tuple[str, ...]]:
    if official_count < config.minimum_official_source_count:
        return "source_missing", "blocked", False, ("official_source_missing",)

    reason_codes = ["official_source_priority"]
    if corroborating_count >= config.minimum_corroborating_third_party_count:
        reason_codes.append("third_party_corroborated")
        route = "official_priority"
        status = "verified"
    else:
        reason_codes.append("third_party_corroboration_gap")
        route = "corroboration_gap"
        status = "review_required"
    if contradiction_count > _ZERO_COUNT:
        reason_codes.append("source_contradiction_present")
        status = "review_required"
    if stale_count > _ZERO_COUNT:
        reason_codes.append("external_source_stale")
        status = "review_required"
    if max_score < config.minimum_verification_score:
        reason_codes.append("source_score_below_floor")
        status = "review_required"
    return route, status, True, tuple(reason_codes)


def _row_with_rank(
    row: ResearchPacketExternalSourceVerificationRouteV2Row,
    priority_rank: Decimal,
) -> ResearchPacketExternalSourceVerificationRouteV2Row:
    return ResearchPacketExternalSourceVerificationRouteV2Row(
        packet_id=row.packet_id,
        verification_route=row.verification_route,
        route_status=row.route_status,
        official_source_count=row.official_source_count,
        third_party_source_count=row.third_party_source_count,
        corroborating_third_party_count=row.corroborating_third_party_count,
        contradiction_source_count=row.contradiction_source_count,
        stale_source_count=row.stale_source_count,
        max_verification_score=row.max_verification_score,
        latest_checked_at=row.latest_checked_at,
        official_source_priority_applied=row.official_source_priority_applied,
        priority_rank=priority_rank,
        reason_codes=row.reason_codes,
    )


def _row_key(
    row: ResearchPacketExternalSourceVerificationRouteV2Row,
) -> tuple[int, str, Decimal, str]:
    return (
        _ROW_STATUS_RANK[row.route_status],
        row.verification_route,
        -row.max_verification_score,
        row.packet_id,
    )


def _report_status(
    rows: tuple[ResearchPacketExternalSourceVerificationRouteV2Row, ...],
) -> str:
    if not rows:
        return "verified"
    if all(row.route_status == "verified" for row in rows):
        return "verified"
    if all(row.route_status == "blocked" for row in rows):
        return "blocked"
    return "review_required"


def _report_reason_codes(
    report_status: str,
    *,
    review_route_count: Decimal,
    blocked_route_count: Decimal,
) -> tuple[str, ...]:
    if report_status == "verified":
        return ("external_source_verification_verified",)
    if report_status == "blocked":
        return ("external_source_verification_blocked",)
    reason_codes = []
    if review_route_count > _ZERO_COUNT:
        reason_codes.append("external_source_verification_review_required")
    if blocked_route_count > _ZERO_COUNT:
        reason_codes.append("external_source_verification_blocked")
    return tuple(reason_codes)


def _validate_row(row: ResearchPacketExternalSourceVerificationRouteV2Row) -> None:
    if row.route_status == "blocked" and row.verification_route != "source_missing":
        raise ValueError("blocked rows must use source_missing")
    if row.verification_route == "source_missing":
        if row.official_source_count != _ZERO_COUNT:
            raise ValueError("source_missing must have zero official sources")
        if row.reason_codes != ("official_source_missing",):
            raise ValueError("source_missing reason_codes must match route")
    if row.official_source_priority_applied != (
        row.official_source_count > _ZERO_COUNT
    ):
        raise ValueError("official_source_priority_applied must match official sources")
    if row.verification_route == "official_priority" and (
        "third_party_corroborated" not in row.reason_codes
    ):
        raise ValueError("official_priority must have third party corroboration")
    if row.verification_route == "corroboration_gap" and (
        "third_party_corroboration_gap" not in row.reason_codes
    ):
        raise ValueError("corroboration_gap must have gap reason_codes")


def _validate_report(report: ResearchPacketExternalSourceVerificationRouteV2Report) -> None:
    rows = report.route_rows
    for row in rows:
        if type(row) is not ResearchPacketExternalSourceVerificationRouteV2Row:
            raise ValueError("route_rows must contain verification route rows")
        _require_row_derived_digest(row)
        _require_hard_flags("row", row)
    if report.route_row_count != _count(len(rows)):
        raise ValueError("route_row_count must match route_rows")
    if report.verified_route_count != _count(
        sum(1 for row in rows if row.route_status == "verified"),
    ):
        raise ValueError("verified_route_count must match route_rows")
    if report.review_route_count != _count(
        sum(1 for row in rows if row.route_status == "review_required"),
    ):
        raise ValueError("review_route_count must match route_rows")
    if report.blocked_route_count != _count(
        sum(1 for row in rows if row.route_status == "blocked"),
    ):
        raise ValueError("blocked_route_count must match route_rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match route_rows")


def _row_derived_digest(row: ResearchPacketExternalSourceVerificationRouteV2Row) -> str:
    return _derived_digest(
        (
            row.packet_id,
            row.verification_route,
            row.route_status,
            row.official_source_count,
            row.third_party_source_count,
            row.corroborating_third_party_count,
            row.contradiction_source_count,
            row.stale_source_count,
            row.max_verification_score,
            row.latest_checked_at,
            row.official_source_priority_applied,
            row.priority_rank,
            row.reason_codes,
            row.paper_only,
            row.report_only,
            row.readonly,
        ),
    )


def _report_derived_digest(
    report: ResearchPacketExternalSourceVerificationRouteV2Report,
) -> str:
    return _derived_digest(
        (
            report.generated_at,
            report.config_version,
            report.source_row_count,
            report.route_row_count,
            report.verified_route_count,
            report.review_route_count,
            report.blocked_route_count,
            report.report_status,
            report.reason_codes,
            tuple(row.derived_validation_digest for row in report.route_rows),
            report.paper_only,
            report.report_only,
            report.readonly,
        ),
    )


def _require_row_derived_digest(
    row: ResearchPacketExternalSourceVerificationRouteV2Row,
) -> None:
    if row.derived_validation_digest != _row_derived_digest(row):
        raise ValueError("derived_validation_digest mismatch: row may be tampered")


def _require_report_derived_digest(
    report: ResearchPacketExternalSourceVerificationRouteV2Report,
) -> None:
    if report.derived_validation_digest != _report_derived_digest(report):
        raise ValueError("derived_validation_digest mismatch: report may be tampered")


def _derived_digest(parts: tuple[object, ...]) -> str:
    material = "\n".join(_digest_part(part) for part in parts)
    return _DERIVED_DIGEST_PREFIX + hashlib.sha256(material.encode("utf-8")).hexdigest()


def _digest_part(value: object) -> str:
    if value is None:
        return "none:"
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("derived_validation_digest values must be finite")
        return f"decimal:{value}"
    if type(value) is datetime:
        return f"datetime:{_as_utc('derived_validation_digest datetime', value).isoformat()}"
    if type(value) is str:
        return f"str:{len(value)}:{value}"
    if type(value) is bool:
        if value:
            return "bool:true"
        return "bool:false"
    if type(value) is tuple:
        return "tuple:[" + ",".join(_digest_part(item) for item in value) + "]"
    raise ValueError("derived_validation_digest values must be canonical")


def _json_ready(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        if not _is_allowed_public_dataclass(value):
            raise ValueError("unsafe payload object must use plain values")
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("JSON datetime", value).isoformat()
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        if type(value) is not dict:
            raise ValueError("unsafe payload object must use plain dict values")
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        if type(value) not in (list, tuple):
            raise ValueError("unsafe payload object must use plain sequence values")
        return [_json_ready(item) for item in value]
    if type(value) is str:
        return value
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if not _is_allowed_public_dataclass(value):
            raise ValueError("unsafe payload object must use plain values")
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if isinstance(value, dict):
        if type(value) is not dict:
            raise ValueError("unsafe payload object must use plain dict values")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        if type(value) not in (list, tuple):
            raise ValueError("unsafe payload object must use plain sequence values")
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _is_allowed_public_dataclass(value: object) -> bool:
    return type(value) in (
        ResearchPacketExternalSourceVerificationRouteV2Config,
        ResearchPacketExternalSourceVerificationRouteV2Source,
        ResearchPacketExternalSourceVerificationRouteV2Row,
        ResearchPacketExternalSourceVerificationRouteV2Report,
    )


def _reject_unsafe_public_text(label: str, value: str) -> None:
    if _has_bad_fragment(value):
        raise ValueError(f"unsafe public value in {label}")


def _has_bad_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _BAD_TEXT_BITS)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    _reject_unsafe_public_text(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _duration_seconds(start: datetime, end: datetime) -> Decimal:
    start_utc = _as_utc("start", start)
    end_utc = _as_utc("end", end)
    seconds = end_utc - start_utc
    value = (
        Decimal(seconds.days) * Decimal("86400")
        + Decimal(seconds.seconds)
        + (Decimal(seconds.microseconds) / Decimal("1000000"))
    )
    if value < _ZERO_COUNT:
        raise ValueError("duration seconds must be nonnegative")
    return value.quantize(_COUNT_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    quantized = _normalize_nonnegative_count(field_name, value)
    if quantized == _ZERO_COUNT:
        raise ValueError(f"{field_name} must be positive")
    return quantized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_RATIO_QUANTUM)
    if quantized < _ZERO_RATIO or quantized > _ONE_RATIO:
        raise ValueError(f"{field_name} must be between zero and one")
    return quantized


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    for reason_code in reason_codes:
        _require_reason_code(reason_code)
    return reason_codes


def _require_reason_code(value: object) -> None:
    if type(value) is not str:
        raise ValueError("reason_codes must contain strings")
    if not value or value.strip() != value:
        raise ValueError("reason_codes must contain canonical strings")
    if value != value.lower() or value[0] == "_" or value[-1] == "_":
        raise ValueError("reason_codes must be lowercase snake_case strings")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError("reason_codes must be lowercase snake_case strings")
    _reject_unsafe_public_text("reason_codes", value)


__all__ = (
    "DEFAULT_RESEARCH_PACKET_EXTERNAL_SOURCE_VERIFICATION_ROUTE_V2_CONFIG_VERSION",
    "SOURCE_KINDS",
    "SOURCE_STATUSES",
    "VERIFICATION_ROUTES",
    "ROUTE_STATUSES",
    "ResearchPacketExternalSourceVerificationRouteV2Config",
    "ResearchPacketExternalSourceVerificationRouteV2Source",
    "ResearchPacketExternalSourceVerificationRouteV2Row",
    "ResearchPacketExternalSourceVerificationRouteV2Report",
    "build_research_packet_external_source_verification_route_v2",
    "research_packet_external_source_verification_route_v2_payload",
)
