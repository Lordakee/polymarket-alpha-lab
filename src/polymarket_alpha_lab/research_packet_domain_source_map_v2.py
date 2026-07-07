"""Read-only Phase 1 domain source family map for research packets."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_PACKET_DOMAIN_SOURCE_MAP_V2_CONFIG_VERSION = (
    "research-packet-domain-source-map-v2"
)
READY_REASON = "domain_source_map_ready"
RELIABILITY_REASON = "domain_source_reliability_watch"
LATENCY_REASON = "domain_source_latency_watch"
INDEPENDENCE_REASON = "domain_source_independence_watch"
CONTRADICTION_REASON = "domain_source_contradiction_watch"
REASON_CODES = (
    READY_REASON,
    RELIABILITY_REASON,
    LATENCY_REASON,
    INDEPENDENCE_REASON,
    CONTRADICTION_REASON,
)
MAPPING_STATUSES = ("ready", "watch")
RISK_BANDS = ("low", "medium", "high")
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
LOW_RISK_CEILING = Decimal("0.100000")
MEDIUM_RISK_CEILING = Decimal("0.300000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("or", "der"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sig", "ning"),
        _join_parts("muta", "tion"),
        _join_parts("b", "uy"),
        _join_parts("s", "ell"),
        _join_parts("tra", "de"),
    ),
)


@dataclass(frozen=True)
class ResearchPacketDomainSourceMapV2Config:
    config_version: str = DEFAULT_RESEARCH_PACKET_DOMAIN_SOURCE_MAP_V2_CONFIG_VERSION
    minimum_reliability_score: Decimal = Decimal("0.800000")
    maximum_latency_seconds: Decimal = Decimal("3600.000000")
    minimum_independence_score: Decimal = Decimal("0.600000")
    maximum_contradiction_risk_score: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "minimum_reliability_score",
            _require_probability_decimal(
                "minimum_reliability_score",
                self.minimum_reliability_score,
            ),
        )
        object.__setattr__(
            self,
            "maximum_latency_seconds",
            _require_nonnegative_decimal(
                "maximum_latency_seconds",
                self.maximum_latency_seconds,
            ),
        )
        object.__setattr__(
            self,
            "minimum_independence_score",
            _require_probability_decimal(
                "minimum_independence_score",
                self.minimum_independence_score,
            ),
        )
        object.__setattr__(
            self,
            "maximum_contradiction_risk_score",
            _require_probability_decimal(
                "maximum_contradiction_risk_score",
                self.maximum_contradiction_risk_score,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class DomainSourceFamilyScoreV2:
    source_family: str
    official_source_anchor: str
    historical_reliability_score: Decimal
    median_latency_seconds: Decimal
    independence_score: Decimal
    contradiction_risk_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("source_family", self.source_family)
        _require_public_string("official_source_anchor", self.official_source_anchor)
        object.__setattr__(
            self,
            "historical_reliability_score",
            _require_probability_decimal(
                "historical_reliability_score",
                self.historical_reliability_score,
            ),
        )
        object.__setattr__(
            self,
            "median_latency_seconds",
            _require_nonnegative_decimal(
                "median_latency_seconds",
                self.median_latency_seconds,
            ),
        )
        object.__setattr__(
            self,
            "independence_score",
            _require_probability_decimal("independence_score", self.independence_score),
        )
        object.__setattr__(
            self,
            "contradiction_risk_score",
            _require_probability_decimal(
                "contradiction_risk_score",
                self.contradiction_risk_score,
            ),
        )
        _require_hard_flags("source family", self)


@dataclass(frozen=True)
class ResearchPacketDomainSourceMapV2InputRow:
    event_domain: str
    preferred_source_families: tuple[DomainSourceFamilyScoreV2, ...]
    backup_source_families: tuple[DomainSourceFamilyScoreV2, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("event_domain", self.event_domain)
        object.__setattr__(
            self,
            "preferred_source_families",
            _normalize_family_scores(
                "preferred_source_families",
                self.preferred_source_families,
            ),
        )
        object.__setattr__(
            self,
            "backup_source_families",
            _normalize_family_scores(
                "backup_source_families",
                self.backup_source_families,
            ),
        )
        if not self.preferred_source_families:
            raise ValueError("preferred_source_families must not be empty")
        if not self.backup_source_families:
            raise ValueError("backup_source_families must not be empty")
        _require_unique_families(
            self.preferred_source_families + self.backup_source_families,
        )
        _require_hard_flags("input row", self)

    def to_report_row(self) -> ResearchPacketDomainSourceMapV2Row:
        preferred = self.preferred_source_families
        source_families = preferred + self.backup_source_families
        return ResearchPacketDomainSourceMapV2Row(
            event_domain=self.event_domain,
            preferred_source_families=preferred,
            official_source_anchors=tuple(
                row.official_source_anchor for row in source_families
            ),
            backup_source_families=self.backup_source_families,
            historical_reliability_score=max(
                row.historical_reliability_score for row in preferred
            ),
            median_latency_seconds=min(row.median_latency_seconds for row in preferred),
            independence_score=max(row.independence_score for row in preferred),
            contradiction_risk_score=min(
                row.contradiction_risk_score for row in preferred
            ),
            contradiction_risk_band=_risk_band(
                min(row.contradiction_risk_score for row in preferred),
            ),
            source_family_count=_count(len(source_families)),
        )


@dataclass(frozen=True)
class ResearchPacketDomainSourceMapV2Row:
    event_domain: str
    preferred_source_families: tuple[DomainSourceFamilyScoreV2, ...]
    official_source_anchors: tuple[str, ...]
    backup_source_families: tuple[DomainSourceFamilyScoreV2, ...]
    historical_reliability_score: Decimal
    median_latency_seconds: Decimal
    independence_score: Decimal
    contradiction_risk_score: Decimal
    contradiction_risk_band: str
    source_family_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("event_domain", self.event_domain)
        object.__setattr__(
            self,
            "preferred_source_families",
            _normalize_family_scores(
                "preferred_source_families",
                self.preferred_source_families,
            ),
        )
        object.__setattr__(
            self,
            "backup_source_families",
            _normalize_family_scores(
                "backup_source_families",
                self.backup_source_families,
            ),
        )
        if not self.preferred_source_families:
            raise ValueError("preferred_source_families must not be empty")
        if not self.backup_source_families:
            raise ValueError("backup_source_families must not be empty")
        _require_unique_families(
            self.preferred_source_families + self.backup_source_families,
        )
        object.__setattr__(
            self,
            "official_source_anchors",
            _normalize_public_strings("official_source_anchors", self.official_source_anchors),
        )
        for field_name in (
            "historical_reliability_score",
            "independence_score",
            "contradiction_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "median_latency_seconds",
            _require_nonnegative_decimal(
                "median_latency_seconds",
                self.median_latency_seconds,
            ),
        )
        _require_member("contradiction_risk_band", self.contradiction_risk_band, RISK_BANDS)
        object.__setattr__(
            self,
            "source_family_count",
            _require_count_decimal("source_family_count", self.source_family_count),
        )
        _validate_report_row(self)
        _require_hard_flags("report row", self)


@dataclass(frozen=True)
class ResearchPacketDomainSourceMapV2Report:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    preferred_source_family_count: Decimal
    backup_source_family_count: Decimal
    average_historical_reliability_score: Decimal
    maximum_median_latency_seconds: Decimal
    average_independence_score: Decimal
    maximum_contradiction_risk_score: Decimal
    mapping_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchPacketDomainSourceMapV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "row_count",
            "preferred_source_family_count",
            "backup_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_historical_reliability_score",
            "average_independence_score",
            "maximum_contradiction_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "maximum_median_latency_seconds",
            _require_nonnegative_decimal(
                "maximum_median_latency_seconds",
                self.maximum_median_latency_seconds,
            ),
        )
        _require_member("mapping_status", self.mapping_status, MAPPING_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_report_rows(self.rows))
        _ensure_validation_digest(self)
        _validate_report(self)
        _require_hard_flags("report", self)


def build_research_packet_domain_source_map_v2(
    input_rows: list[ResearchPacketDomainSourceMapV2InputRow]
    | tuple[ResearchPacketDomainSourceMapV2InputRow, ...],
    *,
    config: ResearchPacketDomainSourceMapV2Config,
    generated_at: datetime,
) -> ResearchPacketDomainSourceMapV2Report:
    if type(config) is not ResearchPacketDomainSourceMapV2Config:
        raise ValueError("config must be a ResearchPacketDomainSourceMapV2Config")
    _require_hard_flags("config", config)
    rows = tuple(row.to_report_row() for row in _normalize_input_rows(input_rows))
    reason_codes = _report_reason_codes(rows, config)
    return ResearchPacketDomainSourceMapV2Report(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        row_count=_count(len(rows)),
        preferred_source_family_count=_count(
            sum(len(row.preferred_source_families) for row in rows),
        ),
        backup_source_family_count=_count(
            sum(len(row.backup_source_families) for row in rows),
        ),
        average_historical_reliability_score=_mean(
            tuple(row.historical_reliability_score for row in rows),
        ),
        maximum_median_latency_seconds=_maximum(
            tuple(row.median_latency_seconds for row in rows),
        ),
        average_independence_score=_mean(tuple(row.independence_score for row in rows)),
        maximum_contradiction_risk_score=_maximum(
            tuple(row.contradiction_risk_score for row in rows),
        ),
        mapping_status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        rows=rows,
    )


def research_packet_domain_source_map_v2_payload(
    report: ResearchPacketDomainSourceMapV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchPacketDomainSourceMapV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public("report", report)
        ready = _json_ready(report)
    elif type(report) is dict:
        _require_hard_flags("public report", _DictFlags(report))
        _reject_unsafe_public("public report", report)
        ready = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchPacketDomainSourceMapV2Report")
    if type(ready) is not dict:
        raise ValueError("report must serialize to an object")
    _require_hard_flags("public report", _DictFlags(ready))
    _reject_unsafe_public("public report", ready)
    _validate_public_digest(ready)
    return ready


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


def _normalize_input_rows(
    value: object,
) -> tuple[ResearchPacketDomainSourceMapV2InputRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("input rows must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("input rows must be a tuple") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketDomainSourceMapV2InputRow:
            raise ValueError(
                "input rows must contain ResearchPacketDomainSourceMapV2InputRow values",
            )
        _require_hard_flags("input row", row)
        if row.event_domain in seen:
            raise ValueError("event_domain values must be unique")
        seen.add(row.event_domain)
    return tuple(sorted(rows, key=lambda row: row.event_domain))


def _normalize_report_rows(
    value: object,
) -> tuple[ResearchPacketDomainSourceMapV2Row, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be a tuple") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketDomainSourceMapV2Row:
            raise ValueError(
                "rows must contain ResearchPacketDomainSourceMapV2Row values",
            )
        _require_hard_flags("report row", row)
        if row.event_domain in seen:
            raise ValueError("event_domain values must be unique")
        seen.add(row.event_domain)
    return tuple(sorted(rows, key=lambda row: row.event_domain))


def _normalize_family_scores(
    field_name: str,
    value: object,
) -> tuple[DomainSourceFamilyScoreV2, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a tuple") from exc
    for row in rows:
        if type(row) is not DomainSourceFamilyScoreV2:
            raise ValueError(f"{field_name} must contain DomainSourceFamilyScoreV2 values")
        _require_hard_flags(field_name, row)
    return tuple(sorted(rows, key=lambda row: row.source_family))


def _normalize_public_strings(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a tuple") from exc
    for row in rows:
        _require_public_string(field_name, row)
    if len(set(rows)) != len(rows):
        raise ValueError(f"{field_name} values must be unique")
    return rows


def _require_unique_families(rows: tuple[DomainSourceFamilyScoreV2, ...]) -> None:
    names = tuple(row.source_family for row in rows)
    if len(set(names)) != len(names):
        raise ValueError("source_family values must be unique")


def _validate_report_row(row: ResearchPacketDomainSourceMapV2Row) -> None:
    preferred = row.preferred_source_families
    all_families = preferred + row.backup_source_families
    expected_anchors = tuple(family.official_source_anchor for family in all_families)
    if row.official_source_anchors != expected_anchors:
        raise ValueError("official_source_anchors must match source families")
    if row.historical_reliability_score != max(
        family.historical_reliability_score for family in preferred
    ):
        raise ValueError("historical_reliability_score must match preferred families")
    if row.median_latency_seconds != min(
        family.median_latency_seconds for family in preferred
    ):
        raise ValueError("median_latency_seconds must match preferred families")
    if row.independence_score != max(family.independence_score for family in preferred):
        raise ValueError("independence_score must match preferred families")
    if row.contradiction_risk_score != min(
        family.contradiction_risk_score for family in preferred
    ):
        raise ValueError("contradiction_risk_score must match preferred families")
    if row.contradiction_risk_band != _risk_band(row.contradiction_risk_score):
        raise ValueError("contradiction_risk_band must match score")
    if row.source_family_count != _count(len(all_families)):
        raise ValueError("source_family_count must match source families")


def _validate_report(report: ResearchPacketDomainSourceMapV2Report) -> None:
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.preferred_source_family_count != _count(
        sum(len(row.preferred_source_families) for row in report.rows),
    ):
        raise ValueError("preferred_source_family_count must match rows")
    if report.backup_source_family_count != _count(
        sum(len(row.backup_source_families) for row in report.rows),
    ):
        raise ValueError("backup_source_family_count must match rows")
    if report.average_historical_reliability_score != _mean(
        tuple(row.historical_reliability_score for row in report.rows),
    ):
        raise ValueError("average_historical_reliability_score must match rows")
    if report.maximum_median_latency_seconds != _maximum(
        tuple(row.median_latency_seconds for row in report.rows),
    ):
        raise ValueError("maximum_median_latency_seconds must match rows")
    if report.average_independence_score != _mean(
        tuple(row.independence_score for row in report.rows),
    ):
        raise ValueError("average_independence_score must match rows")
    if report.maximum_contradiction_risk_score != _maximum(
        tuple(row.contradiction_risk_score for row in report.rows),
    ):
        raise ValueError("maximum_contradiction_risk_score must match rows")
    if report.mapping_status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("mapping_status must match reason_codes")


def _report_reason_codes(
    rows: tuple[ResearchPacketDomainSourceMapV2Row, ...],
    config: ResearchPacketDomainSourceMapV2Config,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if any(
        row.historical_reliability_score < config.minimum_reliability_score
        for row in rows
    ):
        reasons.append(RELIABILITY_REASON)
    if any(row.median_latency_seconds > config.maximum_latency_seconds for row in rows):
        reasons.append(LATENCY_REASON)
    if any(row.independence_score < config.minimum_independence_score for row in rows):
        reasons.append(INDEPENDENCE_REASON)
    if any(
        row.contradiction_risk_score > config.maximum_contradiction_risk_score
        for row in rows
    ):
        reasons.append(CONTRADICTION_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return tuple(reasons)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return "ready"
    return "watch"


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple")
    try:
        codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be a tuple") from exc
    for code in codes:
        _require_member(field_name, code, REASON_CODES)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} values must be unique")
    if tuple(code for code in REASON_CODES if code in codes) != codes:
        raise ValueError(f"{field_name} values must be deterministic")
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    if READY_REASON in codes and codes != (READY_REASON,):
        raise ValueError(f"{field_name} ready reason must stand alone")
    return codes


def _ensure_validation_digest(report: ResearchPacketDomainSourceMapV2Report) -> None:
    digest = _validation_digest(_json_ready(report))
    if not report.derived_validation_digest:
        object.__setattr__(report, "derived_validation_digest", digest)
        return
    _require_digest("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != digest:
        raise ValueError("derived_validation_digest does not match report")


def _validate_public_digest(payload: dict[str, Any]) -> None:
    digest_value = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest_value)
    if digest_value != _validation_digest(payload):
        raise ValueError("derived_validation_digest does not match report")


def _validation_digest(value: object) -> str:
    if type(value) is not dict:
        raise ValueError("digest source must be an object")
    digest_input = {key: item for key, item in value.items() if key != "derived_validation_digest"}
    encoded = json.dumps(digest_input, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal-derived strings")
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError(f"{label} has invalid Decimal value")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{label} has invalid datetime value")
        return
    if type(value) in (bool, type(None)):
        return
    if isinstance(value, float) or type(value) is int:
        raise ValueError(f"{label} has unsafe public value")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} has unsafe public field")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{key} must be True")
            _reject_unsafe_public(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public(label, item)
        return
    raise ValueError(f"{label} has unsafe public value")


def _has_unsafe_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if _has_unsafe_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public text")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} is not supported")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value.quantize(COUNT_QUANTUM)


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    decimal_value = _quantize_ratio(decimal_value)
    if decimal_value < ZERO_RATIO or decimal_value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    decimal_value = _quantize_ratio(decimal_value)
    if decimal_value < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(sum(values, ZERO_RATIO) / Decimal(len(values)))


def _maximum(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    return _quantize_ratio(max(values))


def _risk_band(score: Decimal) -> str:
    if score <= LOW_RISK_CEILING:
        return "low"
    if score <= MEDIUM_RISK_CEILING:
        return "medium"
    return "high"


__all__ = (
    "DEFAULT_RESEARCH_PACKET_DOMAIN_SOURCE_MAP_V2_CONFIG_VERSION",
    "DomainSourceFamilyScoreV2",
    "ResearchPacketDomainSourceMapV2Config",
    "ResearchPacketDomainSourceMapV2InputRow",
    "ResearchPacketDomainSourceMapV2Report",
    "ResearchPacketDomainSourceMapV2Row",
    "build_research_packet_domain_source_map_v2",
    "research_packet_domain_source_map_v2_payload",
)
