from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from decimal import Decimal
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_PACKET_RESOLUTION_RULE_AUTHORITY_MATRIX_V2_CONFIG_VERSION = (
    "research-packet-resolution-rule-authority-matrix-v2"
)

AUTHORITY_MATRIX_STATUSES = ("pass", "watch", "block", "empty")

ROW_REASON_CODES = (
    "polymarket_rule_available",
    "polymarket_rule_missing",
    "official_primary_available",
    "official_primary_missing",
    "secondary_official_present",
    "secondary_official_missing",
    "conflicting_rules_absent",
    "conflicting_rules_present",
    "proxy_dependency_absent",
    "proxy_dependency_present",
    "proxy_dependency_high",
    "authority_row_pass",
    "authority_row_watch",
    "authority_row_block",
)

REPORT_REASON_CODES = (
    "report_status_pass",
    "report_status_watch",
    "report_status_block",
    "report_status_empty",
    "polymarket_rule_missing",
    "official_primary_missing",
    "conflicting_rules_present",
    "proxy_dependency_present",
)

_REASON_CODE_COUNT_ORDER = (
    "authority_row_pass",
    "authority_row_watch",
    "authority_row_block",
    "conflicting_rules_absent",
    "conflicting_rules_present",
    "official_primary_available",
    "official_primary_missing",
    "polymarket_rule_available",
    "polymarket_rule_missing",
    "proxy_dependency_absent",
    "proxy_dependency_high",
    "proxy_dependency_present",
    "secondary_official_missing",
    "secondary_official_present",
)

_ZERO = Decimal("0")
_ONE = Decimal("1.000000")
_ONE_COUNT = Decimal("1")
_AUTHORITY_FAMILY_WEIGHT = Decimal("0.400000")
_SIX_PLACES = Decimal("0.000001")
_HIGH_PROXY_RATIO = Decimal("0.500000")
_DIGEST_FIELD = "derived_validation_digest"
_SURFACE_FRAGMENTS = (
    "livemode",
    "authtoken",
    "authentication",
    "authorization",
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


@dataclass(frozen=True)
class ResearchPacketResolutionRuleAuthorityMatrixV2Input:
    packet_id: str
    market_id: str
    event_slug: str
    category: str
    polymarket_rule_source_count: Decimal
    official_primary_source_count: Decimal
    official_secondary_source_count: Decimal
    proxy_source_count: Decimal
    conflicting_rule_source_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("packet_id", "market_id", "event_slug", "category"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in _COUNT_FIELD_NAMES:
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _reject_unsafe_public_surface("authority input", self)
        _require_hard_flags("authority input", self)


@dataclass(frozen=True)
class ResearchPacketResolutionRuleAuthorityMatrixV2Row:
    packet_id: str
    market_id: str
    event_slug: str
    category: str
    polymarket_rule_source_count: Decimal
    official_primary_source_count: Decimal
    official_secondary_source_count: Decimal
    proxy_source_count: Decimal
    conflicting_rule_source_count: Decimal
    authority_coverage_score: Decimal
    proxy_dependency_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("packet_id", "market_id", "event_slug", "category"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in _COUNT_FIELD_NAMES:
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "authority_coverage_score",
            _require_probability_decimal(
                "authority_coverage_score",
                self.authority_coverage_score,
            ),
        )
        object.__setattr__(
            self,
            "proxy_dependency_ratio",
            _require_probability_decimal(
                "proxy_dependency_ratio",
                self.proxy_dependency_ratio,
            ),
        )
        _require_member("status", self.status, AUTHORITY_MATRIX_STATUSES[:-1])
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        if self.reason_codes != _row_reason_codes(self):
            raise ValueError("reason_codes must be canonical")
        _reject_unsafe_public_surface("authority row", self)
        _require_hard_flags("authority row", self)
        _require_or_set_digest(self)


@dataclass(frozen=True)
class ResearchPacketResolutionRuleAuthorityMatrixV2ReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_member("reason_code", self.reason_code, ROW_REASON_CODES)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        if self.count <= _ZERO:
            raise ValueError("count must be positive")
        _reject_unsafe_public_surface("reason code count", self)
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchPacketResolutionRuleAuthorityMatrixV2Report:
    config_version: str
    packet_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    missing_polymarket_rule_count: Decimal
    missing_official_primary_count: Decimal
    conflicting_rule_count: Decimal
    min_authority_coverage_score: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchPacketResolutionRuleAuthorityMatrixV2ReasonCodeCount,
        ...,
    ]
    authority_rows: tuple[ResearchPacketResolutionRuleAuthorityMatrixV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "packet_count",
            "pass_count",
            "watch_count",
            "block_count",
            "missing_polymarket_rule_count",
            "missing_official_primary_count",
            "conflicting_rule_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_authority_coverage_score",
            _require_probability_decimal(
                "min_authority_coverage_score",
                self.min_authority_coverage_score,
            ),
        )
        _require_member("report_status", self.report_status, AUTHORITY_MATRIX_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "authority_rows",
            _normalize_authority_rows(self.authority_rows),
        )
        _reject_unsafe_public_surface("authority report", self)
        _require_hard_flags("authority report", self)
        _require_or_set_digest(self)
        _validate_report_rollups(self)


_COUNT_FIELD_NAMES = (
    "polymarket_rule_source_count",
    "official_primary_source_count",
    "official_secondary_source_count",
    "proxy_source_count",
    "conflicting_rule_source_count",
)


def build_research_packet_resolution_rule_authority_matrix_v2_report(
    rows: list[ResearchPacketResolutionRuleAuthorityMatrixV2Input]
    | tuple[ResearchPacketResolutionRuleAuthorityMatrixV2Input, ...],
) -> ResearchPacketResolutionRuleAuthorityMatrixV2Report:
    normalized_rows = _normalize_inputs(rows)
    authority_rows = tuple(
        _authority_row(row)
        for row in sorted(
            normalized_rows,
            key=lambda row: (row.packet_id, row.market_id, row.event_slug, row.category),
        )
    )
    return ResearchPacketResolutionRuleAuthorityMatrixV2Report(
        config_version=(
            DEFAULT_RESEARCH_PACKET_RESOLUTION_RULE_AUTHORITY_MATRIX_V2_CONFIG_VERSION
        ),
        packet_count=_count_from_integer(len(authority_rows)),
        pass_count=_status_count(authority_rows, "pass"),
        watch_count=_status_count(authority_rows, "watch"),
        block_count=_status_count(authority_rows, "block"),
        missing_polymarket_rule_count=_predicate_count(
            authority_rows,
            lambda row: row.polymarket_rule_source_count == _ZERO,
        ),
        missing_official_primary_count=_predicate_count(
            authority_rows,
            lambda row: row.official_primary_source_count == _ZERO,
        ),
        conflicting_rule_count=_predicate_count(
            authority_rows,
            lambda row: row.conflicting_rule_source_count > _ZERO,
        ),
        min_authority_coverage_score=_min_authority_coverage_score(authority_rows),
        report_status=_report_status(authority_rows),
        reason_codes=_report_reason_codes(authority_rows),
        reason_code_counts=_reason_code_counts(authority_rows),
        authority_rows=authority_rows,
    )


def research_packet_resolution_rule_authority_matrix_v2_payload(
    report: ResearchPacketResolutionRuleAuthorityMatrixV2Report,
) -> dict[str, object]:
    if type(report) is not ResearchPacketResolutionRuleAuthorityMatrixV2Report:
        raise ValueError(
            "payload must be a ResearchPacketResolutionRuleAuthorityMatrixV2Report",
        )
    payload = _json_ready(asdict(report))
    _reject_unsafe_public_surface("authority payload", payload)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def validate_research_packet_resolution_rule_authority_matrix_v2_payload(
    payload: object,
) -> object:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_surface("authority payload", payload)
    _require_json_safe_payload_values(payload)
    _validate_payload_digest_tree(payload)
    return payload


def _authority_row(
    row: ResearchPacketResolutionRuleAuthorityMatrixV2Input,
) -> ResearchPacketResolutionRuleAuthorityMatrixV2Row:
    authority_coverage_score = _authority_coverage_score(row)
    proxy_dependency_ratio = _proxy_dependency_ratio(row)
    status = _row_status(
        row,
        authority_coverage_score=authority_coverage_score,
        proxy_dependency_ratio=proxy_dependency_ratio,
    )
    return ResearchPacketResolutionRuleAuthorityMatrixV2Row(
        packet_id=row.packet_id,
        market_id=row.market_id,
        event_slug=row.event_slug,
        category=row.category,
        polymarket_rule_source_count=row.polymarket_rule_source_count,
        official_primary_source_count=row.official_primary_source_count,
        official_secondary_source_count=row.official_secondary_source_count,
        proxy_source_count=row.proxy_source_count,
        conflicting_rule_source_count=row.conflicting_rule_source_count,
        authority_coverage_score=authority_coverage_score,
        proxy_dependency_ratio=proxy_dependency_ratio,
        status=status,
        reason_codes=_row_reason_codes_for_values(
            polymarket_rule_source_count=row.polymarket_rule_source_count,
            official_primary_source_count=row.official_primary_source_count,
            official_secondary_source_count=row.official_secondary_source_count,
            proxy_dependency_ratio=proxy_dependency_ratio,
            conflicting_rule_source_count=row.conflicting_rule_source_count,
            status=status,
        ),
    )


def _authority_coverage_score(
    row: ResearchPacketResolutionRuleAuthorityMatrixV2Input,
) -> Decimal:
    present_authority_family_count = _ZERO
    if row.polymarket_rule_source_count > _ZERO:
        present_authority_family_count += _ONE_COUNT
    if row.official_primary_source_count > _ZERO:
        present_authority_family_count += _ONE_COUNT
    if row.official_secondary_source_count > _ZERO:
        present_authority_family_count += _ONE_COUNT
    return min(
        _ONE,
        present_authority_family_count * _AUTHORITY_FAMILY_WEIGHT,
    ).quantize(_SIX_PLACES)


def _proxy_dependency_ratio(
    row: ResearchPacketResolutionRuleAuthorityMatrixV2Input,
) -> Decimal:
    total_source_count = (
        row.polymarket_rule_source_count
        + row.official_primary_source_count
        + row.official_secondary_source_count
        + row.proxy_source_count
    )
    if total_source_count == _ZERO:
        return _ZERO.quantize(_SIX_PLACES)
    return (row.proxy_source_count / total_source_count).quantize(_SIX_PLACES)


def _row_status(
    row: ResearchPacketResolutionRuleAuthorityMatrixV2Input,
    *,
    authority_coverage_score: Decimal,
    proxy_dependency_ratio: Decimal,
) -> str:
    if (
        row.polymarket_rule_source_count == _ZERO
        or row.official_primary_source_count == _ZERO
        or row.conflicting_rule_source_count > _ZERO
    ):
        return "block"
    if authority_coverage_score < _ONE or proxy_dependency_ratio > _ZERO:
        return "watch"
    return "pass"


def _row_reason_codes(
    row: ResearchPacketResolutionRuleAuthorityMatrixV2Row,
) -> tuple[str, ...]:
    return _row_reason_codes_for_values(
        polymarket_rule_source_count=row.polymarket_rule_source_count,
        official_primary_source_count=row.official_primary_source_count,
        official_secondary_source_count=row.official_secondary_source_count,
        proxy_dependency_ratio=row.proxy_dependency_ratio,
        conflicting_rule_source_count=row.conflicting_rule_source_count,
        status=row.status,
    )


def _row_reason_codes_for_values(
    *,
    polymarket_rule_source_count: Decimal,
    official_primary_source_count: Decimal,
    official_secondary_source_count: Decimal,
    proxy_dependency_ratio: Decimal,
    conflicting_rule_source_count: Decimal,
    status: str,
) -> tuple[str, ...]:
    proxy_reason_code = "proxy_dependency_absent"
    if proxy_dependency_ratio > _HIGH_PROXY_RATIO:
        proxy_reason_code = "proxy_dependency_high"
    elif proxy_dependency_ratio > _ZERO:
        proxy_reason_code = "proxy_dependency_present"
    return (
        (
            "polymarket_rule_available"
            if polymarket_rule_source_count > _ZERO
            else "polymarket_rule_missing"
        ),
        (
            "official_primary_available"
            if official_primary_source_count > _ZERO
            else "official_primary_missing"
        ),
        (
            "secondary_official_present"
            if official_secondary_source_count > _ZERO
            else "secondary_official_missing"
        ),
        (
            "conflicting_rules_present"
            if conflicting_rule_source_count > _ZERO
            else "conflicting_rules_absent"
        ),
        proxy_reason_code,
        f"authority_row_{status}",
    )


def _report_status(
    rows: tuple[ResearchPacketResolutionRuleAuthorityMatrixV2Row, ...],
) -> str:
    if not rows:
        return "empty"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchPacketResolutionRuleAuthorityMatrixV2Row, ...],
) -> tuple[str, ...]:
    status = _report_status(rows)
    if status == "empty":
        return ("report_status_empty",)
    codes = [f"report_status_{status}"]
    if any(row.polymarket_rule_source_count == _ZERO for row in rows):
        codes.append("polymarket_rule_missing")
    if any(row.official_primary_source_count == _ZERO for row in rows):
        codes.append("official_primary_missing")
    if any(row.conflicting_rule_source_count > _ZERO for row in rows):
        codes.append("conflicting_rules_present")
    if any(row.proxy_dependency_ratio > _ZERO for row in rows):
        codes.append("proxy_dependency_present")
    return tuple(codes)


def _reason_code_counts(
    rows: tuple[ResearchPacketResolutionRuleAuthorityMatrixV2Row, ...],
) -> tuple[ResearchPacketResolutionRuleAuthorityMatrixV2ReasonCodeCount, ...]:
    counts = {reason_code: _ZERO for reason_code in _REASON_CODE_COUNT_ORDER}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] += _ONE_COUNT
    return tuple(
        ResearchPacketResolutionRuleAuthorityMatrixV2ReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
        )
        for reason_code in _REASON_CODE_COUNT_ORDER
        if counts[reason_code] > _ZERO
    )


def _validate_report_rollups(
    report: ResearchPacketResolutionRuleAuthorityMatrixV2Report,
) -> None:
    rows = report.authority_rows
    expected = {
        "packet_count": _count_from_integer(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "missing_polymarket_rule_count": _predicate_count(
            rows,
            lambda row: row.polymarket_rule_source_count == _ZERO,
        ),
        "missing_official_primary_count": _predicate_count(
            rows,
            lambda row: row.official_primary_source_count == _ZERO,
        ),
        "conflicting_rule_count": _predicate_count(
            rows,
            lambda row: row.conflicting_rule_source_count > _ZERO,
        ),
        "min_authority_coverage_score": _min_authority_coverage_score(rows),
    }
    for field_name, expected_value in expected.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match authority_rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match authority_rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match authority_rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match authority_rows")


def _status_count(
    rows: tuple[ResearchPacketResolutionRuleAuthorityMatrixV2Row, ...],
    status: str,
) -> Decimal:
    return _count_from_integer(sum(_ONE_COUNT for row in rows if row.status == status))


def _predicate_count(
    rows: tuple[ResearchPacketResolutionRuleAuthorityMatrixV2Row, ...],
    predicate: Any,
) -> Decimal:
    return _count_from_integer(sum(_ONE_COUNT for row in rows if predicate(row)))


def _count_from_integer(value: object) -> Decimal:
    return Decimal(str(value))


def _min_authority_coverage_score(
    rows: tuple[ResearchPacketResolutionRuleAuthorityMatrixV2Row, ...],
) -> Decimal:
    if not rows:
        return _ZERO.quantize(_SIX_PLACES)
    return min(row.authority_coverage_score for row in rows)


def _normalize_inputs(
    rows: list[ResearchPacketResolutionRuleAuthorityMatrixV2Input]
    | tuple[ResearchPacketResolutionRuleAuthorityMatrixV2Input, ...],
) -> tuple[ResearchPacketResolutionRuleAuthorityMatrixV2Input, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("authority rows must be a list or tuple")
    normalized = tuple(rows)
    if not all(
        type(row) is ResearchPacketResolutionRuleAuthorityMatrixV2Input
        for row in normalized
    ):
        raise ValueError("authority rows must contain exact authority input rows")
    return normalized


def _normalize_authority_rows(
    rows: object,
) -> tuple[ResearchPacketResolutionRuleAuthorityMatrixV2Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("authority_rows must be a tuple")
    if not all(
        type(row) is ResearchPacketResolutionRuleAuthorityMatrixV2Row for row in rows
    ):
        raise ValueError("authority_rows must contain exact authority rows")
    if rows != tuple(
        sorted(rows, key=lambda row: (row.packet_id, row.market_id, row.event_slug, row.category))
    ):
        raise ValueError("authority_rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[ResearchPacketResolutionRuleAuthorityMatrixV2ReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    if not all(
        type(row) is ResearchPacketResolutionRuleAuthorityMatrixV2ReasonCodeCount
        for row in rows
    ):
        raise ValueError("reason_code_counts must contain exact reason code count rows")
    expected_order = tuple(
        reason_code
        for reason_code in _REASON_CODE_COUNT_ORDER
        if any(row.reason_code == reason_code for row in rows)
    )
    if tuple(row.reason_code for row in rows) != expected_order:
        raise ValueError("reason_code_counts must be canonical")
    return rows


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if not all(type(reason_code) is str and reason_code for reason_code in value):
        raise ValueError(f"{field_name} must contain non-empty strings")
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must be unique")
    unknown_reason_codes = tuple(
        reason_code for reason_code in value if reason_code not in allowed_reason_codes
    )
    if unknown_reason_codes:
        raise ValueError(f"{field_name} contains unknown reason code")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if _contains_surface_fragment(value):
        raise ValueError("unsafe public value")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value > _ONE:
        raise ValueError(f"{field_name} must be at most 1.000000")
    return value.quantize(_SIX_PLACES)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_or_set_digest(value: object) -> None:
    current_digest = getattr(value, _DIGEST_FIELD)
    if type(current_digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected_digest = _digest_for_dataclass(value)
    if current_digest:
        if current_digest != expected_digest:
            raise ValueError("derived_validation_digest must match")
        return
    object.__setattr__(value, _DIGEST_FIELD, expected_digest)


def _digest_for_dataclass(value: object) -> str:
    payload = _json_ready(asdict(value))
    if type(payload) is not dict:
        raise ValueError("digest payload must be a dict")
    return _digest_for_mapping(
        {key: item for key, item in payload.items() if key != _DIGEST_FIELD},
    )


def _digest_for_mapping(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if type(value) is Decimal:
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is dict:
        return {key: _json_ready(item) for key, item in value.items()}
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    return value


def _validate_payload_digest_tree(value: object) -> None:
    if type(value) is dict:
        if _DIGEST_FIELD in value:
            digest = value[_DIGEST_FIELD]
            if type(digest) is not str:
                raise ValueError("derived_validation_digest must be a string")
            expected_digest = _digest_for_mapping(
                {
                    key: item
                    for key, item in value.items()
                    if key != _DIGEST_FIELD
                },
            )
            if digest != expected_digest:
                raise ValueError("derived_validation_digest must match")
        for item in value.values():
            _validate_payload_digest_tree(item)
        return
    if type(value) is list:
        for item in value:
            _validate_payload_digest_tree(item)


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload field must be a string")
            if _contains_surface_fragment(key):
                raise ValueError("unsafe public field")
            _reject_unsafe_public_surface(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_surface(label, item)
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if _contains_surface_fragment(field.name):
                raise ValueError("unsafe public field")
            _reject_unsafe_public_surface(label, getattr(value, field.name))
        return
    if type(value) is str and _contains_surface_fragment(value):
        raise ValueError("unsafe public value")


def _contains_surface_fragment(value: str) -> bool:
    normalized = "".join(character for character in value.lower() if character.isalnum())
    return any(fragment in normalized for fragment in _SURFACE_FRAGMENTS)


def _require_json_safe_payload_values(value: object) -> None:
    if type(value) is dict:
        for item in value.values():
            _require_json_safe_payload_values(item)
        return
    if type(value) is list:
        for item in value:
            _require_json_safe_payload_values(item)
        return
    if type(value) in (Decimal, float, int):
        raise ValueError("public payload numeric values must be decimal strings")
    if type(value) in (str, bool) or value is None:
        return
    raise ValueError("public payload values must be JSON safe")


__all__ = (
    "DEFAULT_RESEARCH_PACKET_RESOLUTION_RULE_AUTHORITY_MATRIX_V2_CONFIG_VERSION",
    "AUTHORITY_MATRIX_STATUSES",
    "ROW_REASON_CODES",
    "REPORT_REASON_CODES",
    "ResearchPacketResolutionRuleAuthorityMatrixV2Input",
    "ResearchPacketResolutionRuleAuthorityMatrixV2Row",
    "ResearchPacketResolutionRuleAuthorityMatrixV2ReasonCodeCount",
    "ResearchPacketResolutionRuleAuthorityMatrixV2Report",
    "build_research_packet_resolution_rule_authority_matrix_v2_report",
    "research_packet_resolution_rule_authority_matrix_v2_payload",
    "validate_research_packet_resolution_rule_authority_matrix_v2_payload",
)
