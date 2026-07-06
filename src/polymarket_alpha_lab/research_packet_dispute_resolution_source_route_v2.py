from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_PACKET_DISPUTE_RESOLUTION_SOURCE_ROUTE_V2_CONFIG_VERSION = (
    "research-packet-dispute-resolution-source-route-v2"
)

_COUNT_QUANTUM = Decimal("1")
_RATIO_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ZERO_RATIO = Decimal("0.000000")
_ONE_RATIO = Decimal("1.000000")
_PUBLIC_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_SOURCE_ROUTE_TYPES = ("official", "independent", "context")
_SELECTED_SOURCE_ROUTES = (
    "official_resolution_route",
    "independent_resolution_route",
    "source_gap_route",
)
_SOURCE_ROUTE_STATUSES = ("pass", "review", "blocked")
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
_ROW_REASON_CODE_SEQUENCE = (
    "official_route_boost_applied",
    "independent_route_support",
    "ambiguous_route_penalty_applied",
    "missing_official_route_penalty_applied",
    "resolution_source_route_clear",
    "resolution_source_route_review",
    "resolution_source_route_blocked",
)
_REPORT_REASON_CODE_SEQUENCE = (
    "dispute_resolution_source_route_clear",
    "dispute_resolution_source_route_blocked",
    "dispute_resolution_source_route_review",
    "ambiguous_route_penalty_applied",
    "missing_official_route_penalty_applied",
)


@dataclass(frozen=True)
class ResearchPacketDisputeResolutionSourceRouteConfig:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_DISPUTE_RESOLUTION_SOURCE_ROUTE_V2_CONFIG_VERSION
    )
    min_official_source_count: Decimal = Decimal("1")
    min_independent_source_count: Decimal = Decimal("2")
    min_source_route_score: Decimal = Decimal("0.700000")
    official_source_route_boost: Decimal = Decimal("0.150000")
    ambiguous_route_penalty: Decimal = Decimal("0.250000")
    missing_official_route_penalty: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketDisputeResolutionSourceRouteConfig:
            raise ValueError(
                "config must be a ResearchPacketDisputeResolutionSourceRouteConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_DISPUTE_RESOLUTION_SOURCE_ROUTE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_official_source_count",
            "min_independent_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_source_route_score",
            "official_source_route_boost",
            "ambiguous_route_penalty",
            "missing_official_route_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchPacketDisputeResolutionSourceRouteSource:
    packet_id: str
    resolution_reference: str
    source_id: str
    source_route_type: str
    source_available: bool
    checked_at: datetime
    route_confidence_score: Decimal
    ambiguous_resolution_route: bool
    public_summary: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketDisputeResolutionSourceRouteSource:
            raise ValueError(
                "source must be a ResearchPacketDisputeResolutionSourceRouteSource",
            )
        for field_name in ("packet_id", "resolution_reference", "source_id"):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_member("source_route_type", self.source_route_type, _SOURCE_ROUTE_TYPES)
        _require_bool("source_available", self.source_available)
        object.__setattr__(self, "checked_at", _as_utc("checked_at", self.checked_at))
        object.__setattr__(
            self,
            "route_confidence_score",
            _normalize_ratio("route_confidence_score", self.route_confidence_score),
        )
        _require_bool("ambiguous_resolution_route", self.ambiguous_resolution_route)
        object.__setattr__(
            self,
            "public_summary",
            _normalize_optional_public_text("public_summary", self.public_summary),
        )
        _require_hard_flags("source", self)
        _reject_unsafe_public_payload("source", self)


@dataclass(frozen=True)
class ResearchPacketDisputeResolutionSourceRouteRow:
    packet_id: str
    resolution_reference: str
    selected_source_route: str
    source_route_status: str
    source_count: Decimal
    official_source_count: Decimal
    independent_source_count: Decimal
    available_source_count: Decimal
    ambiguous_route_count: Decimal
    average_route_confidence_score: Decimal
    official_route_boost: Decimal
    ambiguous_route_penalty: Decimal
    missing_official_route_penalty: Decimal
    source_route_score: Decimal
    latest_checked_at: datetime
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketDisputeResolutionSourceRouteRow:
            raise ValueError("row must be a ResearchPacketDisputeResolutionSourceRouteRow")
        _require_public_identifier("packet_id", self.packet_id)
        _require_public_identifier("resolution_reference", self.resolution_reference)
        _require_member(
            "selected_source_route",
            self.selected_source_route,
            _SELECTED_SOURCE_ROUTES,
        )
        _require_member(
            "source_route_status",
            self.source_route_status,
            _SOURCE_ROUTE_STATUSES,
        )
        for field_name in (
            "source_count",
            "official_source_count",
            "independent_source_count",
            "available_source_count",
            "ambiguous_route_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_route_confidence_score",
            "official_route_boost",
            "ambiguous_route_penalty",
            "missing_official_route_penalty",
            "source_route_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_checked_at",
            _as_utc("latest_checked_at", self.latest_checked_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        expected_digest = _derived_digest(self)
        if self.derived_validation_digest:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchPacketDisputeResolutionSourceRouteReport:
    generated_at: datetime
    config_version: str
    source_count: Decimal
    route_row_count: Decimal
    pass_count: Decimal
    review_count: Decimal
    blocked_count: Decimal
    average_source_route_score: Decimal
    max_ambiguous_route_penalty: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchPacketDisputeResolutionSourceRouteRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketDisputeResolutionSourceRouteReport:
            raise ValueError(
                "report must be a ResearchPacketDisputeResolutionSourceRouteReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_DISPUTE_RESOLUTION_SOURCE_ROUTE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "source_count",
            "route_row_count",
            "pass_count",
            "review_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_source_route_score",
            "max_ambiguous_route_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("report_status", self.report_status, _SOURCE_ROUTE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _REPORT_REASON_CODE_SEQUENCE),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        expected_digest = _derived_digest(self)
        if self.derived_validation_digest:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest mismatch")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)


def build_research_packet_dispute_resolution_source_route_v2(
    sources: Sequence[ResearchPacketDisputeResolutionSourceRouteSource],
    *,
    config: ResearchPacketDisputeResolutionSourceRouteConfig,
    generated_at: datetime,
) -> ResearchPacketDisputeResolutionSourceRouteReport:
    if type(config) is not ResearchPacketDisputeResolutionSourceRouteConfig:
        raise ValueError("config must be a ResearchPacketDisputeResolutionSourceRouteConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_sources = _normalize_sources(sources)
    for source in normalized_sources:
        if source.checked_at > generated_at_utc:
            raise ValueError("source checked_at must not be after generated_at")
    rows = tuple(
        sorted(
            (
                _row_for_group(group, config=config)
                for group in _group_sources(normalized_sources)
            ),
            key=lambda row: (row.packet_id, row.resolution_reference),
        ),
    )
    pass_count = _count(sum(1 for row in rows if row.source_route_status == "pass"))
    review_count = _count(sum(1 for row in rows if row.source_route_status == "review"))
    blocked_count = _count(sum(1 for row in rows if row.source_route_status == "blocked"))
    return ResearchPacketDisputeResolutionSourceRouteReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_count=_count(len(normalized_sources)),
        route_row_count=_count(len(rows)),
        pass_count=pass_count,
        review_count=review_count,
        blocked_count=blocked_count,
        average_source_route_score=_average(
            tuple(row.source_route_score for row in rows),
        ),
        max_ambiguous_route_penalty=max(
            (row.ambiguous_route_penalty for row in rows),
            default=_ZERO_RATIO,
        ),
        report_status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_packet_dispute_resolution_source_route_v2_payload(
    report: ResearchPacketDisputeResolutionSourceRouteReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchPacketDisputeResolutionSourceRouteReport:
        _require_hard_flags("report", report)
        _validate_report(report)
        _require_expected_digest(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchPacketDisputeResolutionSourceRouteReport")
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_flag_downgrades("payload", payload)
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
    sources: Sequence[ResearchPacketDisputeResolutionSourceRouteSource],
) -> tuple[ResearchPacketDisputeResolutionSourceRouteSource, ...]:
    if isinstance(sources, (str, bytes)) or not isinstance(sources, Sequence):
        raise ValueError("sources must be a sequence")
    normalized = tuple(sources)
    seen: set[tuple[str, str]] = set()
    for source in normalized:
        if type(source) is not ResearchPacketDisputeResolutionSourceRouteSource:
            raise ValueError("sources must contain dispute resolution source route sources")
        _require_hard_flags("source", source)
        pair = (source.packet_id, source.source_id)
        if pair in seen:
            raise ValueError("sources must not contain duplicate packet source pairs")
        seen.add(pair)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.packet_id,
                item.resolution_reference,
                item.checked_at,
                item.source_id,
            ),
        ),
    )


def _group_sources(
    sources: tuple[ResearchPacketDisputeResolutionSourceRouteSource, ...],
) -> tuple[tuple[ResearchPacketDisputeResolutionSourceRouteSource, ...], ...]:
    keys = tuple(sorted({(source.packet_id, source.resolution_reference) for source in sources}))
    return tuple(
        tuple(
            source
            for source in sources
            if (source.packet_id, source.resolution_reference) == key
        )
        for key in keys
    )


def _row_for_group(
    sources: tuple[ResearchPacketDisputeResolutionSourceRouteSource, ...],
    *,
    config: ResearchPacketDisputeResolutionSourceRouteConfig,
) -> ResearchPacketDisputeResolutionSourceRouteRow:
    packet_id = sources[0].packet_id
    resolution_reference = sources[0].resolution_reference
    available_sources = tuple(source for source in sources if source.source_available)
    official_count = _count(
        sum(
            1
            for source in available_sources
            if source.source_route_type == "official"
        ),
    )
    independent_count = _count(
        sum(
            1
            for source in available_sources
            if source.source_route_type == "independent"
        ),
    )
    ambiguous_count = _count(
        sum(1 for source in available_sources if source.ambiguous_resolution_route),
    )
    average_confidence = _average(
        tuple(source.route_confidence_score for source in available_sources),
    )
    official_boost = (
        config.official_source_route_boost
        if official_count >= config.min_official_source_count
        else _ZERO_RATIO
    )
    ambiguous_penalty = (
        config.ambiguous_route_penalty if ambiguous_count > _ZERO_COUNT else _ZERO_RATIO
    )
    missing_penalty = (
        config.missing_official_route_penalty
        if official_count < config.min_official_source_count
        else _ZERO_RATIO
    )
    score = _clamp_ratio(
        average_confidence + official_boost - ambiguous_penalty - missing_penalty,
    )
    selected_route = _selected_source_route(
        official_count=official_count,
        independent_count=independent_count,
        config=config,
    )
    status = _source_route_status(
        official_count=official_count,
        ambiguous_count=ambiguous_count,
        source_route_score=score,
        config=config,
    )
    return ResearchPacketDisputeResolutionSourceRouteRow(
        packet_id=packet_id,
        resolution_reference=resolution_reference,
        selected_source_route=selected_route,
        source_route_status=status,
        source_count=_count(len(sources)),
        official_source_count=official_count,
        independent_source_count=independent_count,
        available_source_count=_count(len(available_sources)),
        ambiguous_route_count=ambiguous_count,
        average_route_confidence_score=average_confidence,
        official_route_boost=official_boost,
        ambiguous_route_penalty=ambiguous_penalty,
        missing_official_route_penalty=missing_penalty,
        source_route_score=score,
        latest_checked_at=max(source.checked_at for source in sources),
        reason_codes=_row_reason_codes(
            official_route_boost=official_boost,
            independent_route_supported=(
                official_count >= config.min_official_source_count
                and independent_count > _ZERO_COUNT
            ),
            ambiguous_route_penalty=ambiguous_penalty,
            missing_official_route_penalty=missing_penalty,
            source_route_status=status,
        ),
    )


def _selected_source_route(
    *,
    official_count: Decimal,
    independent_count: Decimal,
    config: ResearchPacketDisputeResolutionSourceRouteConfig,
) -> str:
    if official_count >= config.min_official_source_count:
        return "official_resolution_route"
    if independent_count >= config.min_independent_source_count:
        return "independent_resolution_route"
    return "source_gap_route"


def _source_route_status(
    *,
    official_count: Decimal,
    ambiguous_count: Decimal,
    source_route_score: Decimal,
    config: ResearchPacketDisputeResolutionSourceRouteConfig,
) -> str:
    if official_count < config.min_official_source_count:
        return "blocked"
    if ambiguous_count > _ZERO_COUNT:
        return "review"
    if source_route_score >= config.min_source_route_score:
        return "pass"
    return "review"


def _row_reason_codes(
    *,
    official_route_boost: Decimal,
    independent_route_supported: bool,
    ambiguous_route_penalty: Decimal,
    missing_official_route_penalty: Decimal,
    source_route_status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if official_route_boost > _ZERO_RATIO:
        reason_codes.append("official_route_boost_applied")
    if independent_route_supported:
        reason_codes.append("independent_route_support")
    if ambiguous_route_penalty > _ZERO_RATIO:
        reason_codes.append("ambiguous_route_penalty_applied")
    if missing_official_route_penalty > _ZERO_RATIO:
        reason_codes.append("missing_official_route_penalty_applied")
    if source_route_status == "pass":
        reason_codes.append("resolution_source_route_clear")
    elif source_route_status == "review":
        reason_codes.append("resolution_source_route_review")
    else:
        reason_codes.append("resolution_source_route_blocked")
    return _normalize_reason_codes(tuple(reason_codes), _ROW_REASON_CODE_SEQUENCE)


def _report_status(
    rows: tuple[ResearchPacketDisputeResolutionSourceRouteRow, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.source_route_status == "blocked" for row in rows):
        return "blocked"
    if any(row.source_route_status == "review" for row in rows):
        return "review"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchPacketDisputeResolutionSourceRouteRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("dispute_resolution_source_route_blocked",)
    reason_codes: list[str] = []
    report_status = _report_status(rows)
    if report_status == "pass":
        reason_codes.append("dispute_resolution_source_route_clear")
    elif report_status == "review":
        reason_codes.append("dispute_resolution_source_route_review")
    else:
        reason_codes.append("dispute_resolution_source_route_blocked")
        if any(row.source_route_status == "review" for row in rows):
            reason_codes.append("dispute_resolution_source_route_review")
    if any(row.ambiguous_route_penalty > _ZERO_RATIO for row in rows):
        reason_codes.append("ambiguous_route_penalty_applied")
    if any(row.missing_official_route_penalty > _ZERO_RATIO for row in rows):
        reason_codes.append("missing_official_route_penalty_applied")
    return _normalize_reason_codes(tuple(reason_codes), _REPORT_REASON_CODE_SEQUENCE)


def _normalize_rows(
    rows: Sequence[ResearchPacketDisputeResolutionSourceRouteRow],
) -> tuple[ResearchPacketDisputeResolutionSourceRouteRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchPacketDisputeResolutionSourceRouteRow:
            raise ValueError("rows must contain dispute resolution source route rows")
        _require_expected_digest(row)
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=lambda row: (row.packet_id, row.resolution_reference)))


def _validate_row(row: ResearchPacketDisputeResolutionSourceRouteRow) -> None:
    if row.official_source_count > row.available_source_count:
        raise ValueError("official_source_count must not exceed available_source_count")
    if row.independent_source_count > row.available_source_count:
        raise ValueError("independent_source_count must not exceed available_source_count")
    if row.ambiguous_route_count > row.available_source_count:
        raise ValueError("ambiguous_route_count must not exceed available_source_count")
    if row.available_source_count > row.source_count:
        raise ValueError("available_source_count must not exceed source_count")
    if row.source_route_status == "pass" and "resolution_source_route_clear" not in row.reason_codes:
        raise ValueError("pass rows must include clear reason code")
    if (
        row.source_route_status == "blocked"
        and "resolution_source_route_blocked" not in row.reason_codes
    ):
        raise ValueError("blocked rows must include blocked reason code")
    if (
        row.source_route_status == "review"
        and "resolution_source_route_review" not in row.reason_codes
    ):
        raise ValueError("review rows must include review reason code")


def _validate_report(report: ResearchPacketDisputeResolutionSourceRouteReport) -> None:
    if report.route_row_count != _count(len(report.rows)):
        raise ValueError("route_row_count must match rows")
    if report.pass_count != _count(sum(1 for row in report.rows if row.source_route_status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.review_count != _count(
        sum(1 for row in report.rows if row.source_route_status == "review"),
    ):
        raise ValueError("review_count must match rows")
    if report.blocked_count != _count(
        sum(1 for row in report.rows if row.source_route_status == "blocked"),
    ):
        raise ValueError("blocked_count must match rows")
    if report.average_source_route_score != _average(
        tuple(row.source_route_score for row in report.rows),
    ):
        raise ValueError("average_source_route_score must match rows")
    expected_max_penalty = max(
        (row.ambiguous_route_penalty for row in report.rows),
        default=_ZERO_RATIO,
    )
    if report.max_ambiguous_route_penalty != expected_max_penalty:
        raise ValueError("max_ambiguous_route_penalty must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _require_expected_digest(
    value: (
        ResearchPacketDisputeResolutionSourceRouteRow
        | ResearchPacketDisputeResolutionSourceRouteReport
    ),
) -> None:
    if value.derived_validation_digest != _derived_digest(value):
        raise ValueError("derived_validation_digest mismatch")


def _derived_digest(
    value: (
        ResearchPacketDisputeResolutionSourceRouteRow
        | ResearchPacketDisputeResolutionSourceRouteReport
    ),
) -> str:
    payload = asdict(value)
    payload.pop("derived_validation_digest", None)
    ready = _json_ready(payload)
    encoded = json.dumps(
        ready,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must be exactly Decimal")
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if isinstance(value, datetime):
        raise ValueError("JSON datetime value must be a datetime")
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool or type(value) is str:
        return value
    if value is None:
        return None
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, Mapping):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
            )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{current_path}[{index}]")
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if type(value) is datetime:
        _as_utc(current_path, value)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    raise ValueError("value is not JSON serializable")


def _reject_flag_downgrades(label: str, value: object) -> None:
    if isinstance(value, Mapping):
        for field_name in _PHASE_FLAG_FIELDS:
            if field_name in value and value[field_name] is not True:
                raise ValueError(f"{field_name} must be True for {label}")
        for item in value.values():
            _reject_flag_downgrades(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_flag_downgrades(label, item)


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    for term in _UNSAFE_PUBLIC_TERMS:
        if term in lowered:
            raise ValueError(f"unsafe public field in {path}: {key}")


def _reject_unsafe_public_string(label: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"unsafe public value in {label}")
    for term in _UNSAFE_PUBLIC_TERMS:
        if term in lowered:
            raise ValueError(f"unsafe public value in {label}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} must be {field_name}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_ID_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _normalize_optional_public_text(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _require_public_text(field_name, value)


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> str:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value).quantize(_COUNT_QUANTUM)
    if decimal_value < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value).quantize(
        _RATIO_QUANTUM,
        rounding=ROUND_HALF_UP,
    )
    if decimal_value < _ZERO_RATIO or decimal_value > _ONE_RATIO:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO_RATIO
    return _quantize_ratio(sum(values, _ZERO_RATIO) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    quantized = _quantize_ratio(value)
    if quantized < _ZERO_RATIO:
        return _ZERO_RATIO
    if quantized > _ONE_RATIO:
        return _ONE_RATIO
    return quantized


def _quantize_ratio(value: Decimal) -> Decimal:
    return value.quantize(_RATIO_QUANTUM, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(
    reason_codes: Sequence[str],
    supported_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in supported_codes:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(reason_code for reason_code in supported_codes if reason_code in normalized)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "ResearchPacketDisputeResolutionSourceRouteConfig",
    "ResearchPacketDisputeResolutionSourceRouteSource",
    "ResearchPacketDisputeResolutionSourceRouteRow",
    "ResearchPacketDisputeResolutionSourceRouteReport",
    "build_research_packet_dispute_resolution_source_route_v2",
    "research_packet_dispute_resolution_source_route_v2_payload",
)
