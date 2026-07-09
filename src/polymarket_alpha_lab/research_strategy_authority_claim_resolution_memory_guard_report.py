from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from typing import Any


DEFAULT_CONFIG_VERSION = (
    "research_strategy_authority_claim_resolution_memory_guard_v1"
)
REPORT_STATUSES = ("pass", "watch", "block")

_METRIC_QUANTUM = Decimal("0.000001")
_ZERO_METRIC = Decimal("0.000000")
_COUNT_ZERO = Decimal("0")
_COUNT_ONE = Decimal("1")
_HEX_DIGITS = frozenset("0123456789abcdef")
_STATUS_RANK = {"pass": 0, "watch": 1, "block": 2}
_PUBLIC_PAYLOAD_KEYS = frozenset(
    {
        "generated_at",
        "config_version",
        "status",
        "checked_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_claim_resolution_age_hours",
        "max_authority_memory_age_hours",
        "min_resolution_agreement_score",
        "min_memory_recall_score",
        "max_conflict_pressure",
        "rows",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    },
)
_ROW_PAYLOAD_KEYS = frozenset(
    {
        "memory_key",
        "authority_bucket",
        "status",
        "claim_resolution_age_hours",
        "authority_memory_age_hours",
        "resolution_agreement_score",
        "memory_recall_score",
        "conflict_pressure",
        "reason_codes",
    },
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate_id",
    "candidate-",
    "market_id",
    "market-",
    "market_slug",
    "slug=",
    "question",
    "source_url",
    "source_text",
    "http://",
    "https://",
    "postgres://",
    "postgresql://",
    "mysql://",
    "sqlite://",
    "mongodb://",
    "redis://",
    "dsn",
    "table_name",
    "private_table",
    "password",
    "secret",
    "token",
    "api_key",
    "bearer ",
    "authorization",
    "oauth",
    "wallet",
    "order",
    "trade",
    "execution",
    "live_trading",
    "position",
    "notional",
    "sizing",
    "recommendation",
    "recommended",
)


@dataclass(frozen=True)
class AuthorityClaimResolutionMemoryGuardConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    claim_resolution_watch_age_hours: Decimal = Decimal("18.000000")
    claim_resolution_block_age_hours: Decimal = Decimal("72.000000")
    authority_memory_watch_age_hours: Decimal = Decimal("36.000000")
    authority_memory_block_age_hours: Decimal = Decimal("96.000000")
    resolution_agreement_watch_floor: Decimal = Decimal("0.850000")
    resolution_agreement_block_floor: Decimal = Decimal("0.650000")
    memory_recall_watch_floor: Decimal = Decimal("0.800000")
    memory_recall_block_floor: Decimal = Decimal("0.550000")
    conflict_pressure_watch_ceiling: Decimal = Decimal("0.200000")
    conflict_pressure_block_ceiling: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_flags("config", self)
        _require_safe_public_string("config_version", self.config_version)
        _normalize_decimal_field(
            self,
            "claim_resolution_watch_age_hours",
            non_negative=True,
        )
        _normalize_decimal_field(
            self,
            "claim_resolution_block_age_hours",
            non_negative=True,
        )
        _normalize_decimal_field(
            self,
            "authority_memory_watch_age_hours",
            non_negative=True,
        )
        _normalize_decimal_field(
            self,
            "authority_memory_block_age_hours",
            non_negative=True,
        )
        _normalize_decimal_field(
            self,
            "resolution_agreement_watch_floor",
            probability=True,
        )
        _normalize_decimal_field(
            self,
            "resolution_agreement_block_floor",
            probability=True,
        )
        _normalize_decimal_field(self, "memory_recall_watch_floor", probability=True)
        _normalize_decimal_field(self, "memory_recall_block_floor", probability=True)
        _normalize_decimal_field(
            self,
            "conflict_pressure_watch_ceiling",
            probability=True,
        )
        _normalize_decimal_field(
            self,
            "conflict_pressure_block_ceiling",
            probability=True,
        )
        if self.claim_resolution_watch_age_hours > self.claim_resolution_block_age_hours:
            raise ValueError(
                "claim_resolution_watch_age_hours must not exceed block threshold",
            )
        if self.authority_memory_watch_age_hours > self.authority_memory_block_age_hours:
            raise ValueError(
                "authority_memory_watch_age_hours must not exceed block threshold",
            )
        if self.resolution_agreement_watch_floor < self.resolution_agreement_block_floor:
            raise ValueError(
                "resolution_agreement_watch_floor must not be below block floor",
            )
        if self.memory_recall_watch_floor < self.memory_recall_block_floor:
            raise ValueError("memory_recall_watch_floor must not be below block floor")
        if self.conflict_pressure_watch_ceiling > self.conflict_pressure_block_ceiling:
            raise ValueError(
                "conflict_pressure_watch_ceiling must not exceed block ceiling",
            )


@dataclass(frozen=True)
class AuthorityClaimResolutionMemoryGuardInput:
    raw_claim_reference: str
    raw_authority_reference: str
    authority_bucket: str
    claim_resolution_age_hours: Decimal
    authority_memory_age_hours: Decimal
    resolution_agreement_score: Decimal
    memory_recall_score: Decimal
    conflict_pressure: Decimal
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_nonempty_string("raw_claim_reference", self.raw_claim_reference)
        _require_nonempty_string(
            "raw_authority_reference",
            self.raw_authority_reference,
        )
        _require_safe_public_string("authority_bucket", self.authority_bucket)
        _normalize_decimal_field(self, "claim_resolution_age_hours", non_negative=True)
        _normalize_decimal_field(self, "authority_memory_age_hours", non_negative=True)
        _normalize_decimal_field(
            self,
            "resolution_agreement_score",
            probability=True,
        )
        _normalize_decimal_field(self, "memory_recall_score", probability=True)
        _normalize_decimal_field(self, "conflict_pressure", probability=True)
        _normalize_reason_codes("reason_codes", self.reason_codes)


@dataclass(frozen=True)
class ResearchStrategyAuthorityClaimResolutionMemoryGuardRow:
    memory_key: str
    authority_bucket: str
    status: str
    claim_resolution_age_hours: Decimal
    authority_memory_age_hours: Decimal
    resolution_agreement_score: Decimal
    memory_recall_score: Decimal
    conflict_pressure: Decimal
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_digest_string("memory_key", self.memory_key)
        _require_safe_public_string("authority_bucket", self.authority_bucket)
        _require_status("status", self.status)
        _normalize_decimal_field(self, "claim_resolution_age_hours", non_negative=True)
        _normalize_decimal_field(self, "authority_memory_age_hours", non_negative=True)
        _normalize_decimal_field(
            self,
            "resolution_agreement_score",
            probability=True,
        )
        _normalize_decimal_field(self, "memory_recall_score", probability=True)
        _normalize_decimal_field(self, "conflict_pressure", probability=True)
        _normalize_reason_codes("reason_codes", self.reason_codes)


@dataclass(frozen=True)
class ResearchStrategyAuthorityClaimResolutionMemoryGuardReport:
    generated_at: datetime
    config_version: str
    status: str
    checked_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_claim_resolution_age_hours: Decimal
    max_authority_memory_age_hours: Decimal
    min_resolution_agreement_score: Decimal
    min_memory_recall_score: Decimal
    max_conflict_pressure: Decimal
    rows: tuple[ResearchStrategyAuthorityClaimResolutionMemoryGuardRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_flags("report", self)
        _require_datetime("generated_at", self.generated_at)
        _require_safe_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        _normalize_count_field(self, "checked_count")
        _normalize_count_field(self, "pass_count")
        _normalize_count_field(self, "watch_count")
        _normalize_count_field(self, "block_count")
        _normalize_decimal_field(
            self,
            "max_claim_resolution_age_hours",
            non_negative=True,
        )
        _normalize_decimal_field(
            self,
            "max_authority_memory_age_hours",
            non_negative=True,
        )
        _normalize_decimal_field(
            self,
            "min_resolution_agreement_score",
            probability=True,
        )
        _normalize_decimal_field(self, "min_memory_recall_score", probability=True)
        _normalize_decimal_field(self, "max_conflict_pressure", probability=True)
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not ResearchStrategyAuthorityClaimResolutionMemoryGuardRow:
                raise ValueError("rows must contain memory guard rows")
        _normalize_reason_codes("reason_codes", self.reason_codes)
        _require_digest_string(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _validate_report_consistency(self)
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        if self.derived_validation_digest != _payload_validation_digest(payload):
            raise ValueError("derived_validation_digest must match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return research_strategy_authority_claim_resolution_memory_guard_payload(self)


def build_research_strategy_authority_claim_resolution_memory_guard_report(
    inputs: tuple[AuthorityClaimResolutionMemoryGuardInput, ...],
    *,
    generated_at: datetime,
    config: AuthorityClaimResolutionMemoryGuardConfig | None = None,
) -> ResearchStrategyAuthorityClaimResolutionMemoryGuardReport:
    if type(inputs) is not tuple:
        raise ValueError("inputs must be a tuple")
    active_config = config or AuthorityClaimResolutionMemoryGuardConfig()
    if type(active_config) is not AuthorityClaimResolutionMemoryGuardConfig:
        raise ValueError(
            "config must be an AuthorityClaimResolutionMemoryGuardConfig",
        )
    _require_flags("config", active_config)
    _require_datetime("generated_at", generated_at)

    rows = tuple(_row_from_input(item, active_config) for item in inputs)
    _reject_duplicate_memory_keys(rows)
    status = _aggregate_status(rows)
    pass_count = _count_status(rows, "pass")
    watch_count = _count_status(rows, "watch")
    block_count = _count_status(rows, "block")
    checked_count = pass_count + watch_count + block_count
    reason_codes = _aggregate_reason_codes(rows)
    metrics = _aggregate_metrics(rows)

    unsigned_payload = {
        "generated_at": _json_ready(generated_at),
        "config_version": active_config.config_version,
        "status": status,
        "checked_count": _json_ready(checked_count),
        "pass_count": _json_ready(pass_count),
        "watch_count": _json_ready(watch_count),
        "block_count": _json_ready(block_count),
        "max_claim_resolution_age_hours": _json_ready(
            metrics["max_claim_resolution_age_hours"],
        ),
        "max_authority_memory_age_hours": _json_ready(
            metrics["max_authority_memory_age_hours"],
        ),
        "min_resolution_agreement_score": _json_ready(
            metrics["min_resolution_agreement_score"],
        ),
        "min_memory_recall_score": _json_ready(metrics["min_memory_recall_score"]),
        "max_conflict_pressure": _json_ready(metrics["max_conflict_pressure"]),
        "rows": _json_ready(rows),
        "reason_codes": _json_ready(reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    digest = _payload_validation_digest(unsigned_payload)
    return ResearchStrategyAuthorityClaimResolutionMemoryGuardReport(
        generated_at=generated_at,
        config_version=active_config.config_version,
        status=status,
        checked_count=checked_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        max_claim_resolution_age_hours=metrics["max_claim_resolution_age_hours"],
        max_authority_memory_age_hours=metrics["max_authority_memory_age_hours"],
        min_resolution_agreement_score=metrics["min_resolution_agreement_score"],
        min_memory_recall_score=metrics["min_memory_recall_score"],
        max_conflict_pressure=metrics["max_conflict_pressure"],
        rows=rows,
        reason_codes=reason_codes,
        derived_validation_digest=digest,
    )


def research_strategy_authority_claim_resolution_memory_guard_payload(
    report: ResearchStrategyAuthorityClaimResolutionMemoryGuardReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyAuthorityClaimResolutionMemoryGuardReport:
        _require_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyAuthorityClaimResolutionMemoryGuardReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def _row_from_input(
    item: AuthorityClaimResolutionMemoryGuardInput,
    config: AuthorityClaimResolutionMemoryGuardConfig,
) -> ResearchStrategyAuthorityClaimResolutionMemoryGuardRow:
    if type(item) is not AuthorityClaimResolutionMemoryGuardInput:
        raise ValueError("inputs must contain memory guard input rows")
    status = _status_for_input(item, config)
    return ResearchStrategyAuthorityClaimResolutionMemoryGuardRow(
        memory_key=_memory_key_for_input(item),
        authority_bucket=item.authority_bucket,
        status=status,
        claim_resolution_age_hours=item.claim_resolution_age_hours,
        authority_memory_age_hours=item.authority_memory_age_hours,
        resolution_agreement_score=item.resolution_agreement_score,
        memory_recall_score=item.memory_recall_score,
        conflict_pressure=item.conflict_pressure,
        reason_codes=item.reason_codes,
    )


def _status_for_input(
    item: AuthorityClaimResolutionMemoryGuardInput,
    config: AuthorityClaimResolutionMemoryGuardConfig,
) -> str:
    if (
        item.claim_resolution_age_hours >= config.claim_resolution_block_age_hours
        or item.authority_memory_age_hours >= config.authority_memory_block_age_hours
        or item.resolution_agreement_score <= config.resolution_agreement_block_floor
        or item.memory_recall_score <= config.memory_recall_block_floor
        or item.conflict_pressure >= config.conflict_pressure_block_ceiling
    ):
        return "block"
    if (
        item.claim_resolution_age_hours >= config.claim_resolution_watch_age_hours
        or item.authority_memory_age_hours >= config.authority_memory_watch_age_hours
        or item.resolution_agreement_score <= config.resolution_agreement_watch_floor
        or item.memory_recall_score <= config.memory_recall_watch_floor
        or item.conflict_pressure >= config.conflict_pressure_watch_ceiling
    ):
        return "watch"
    return "pass"


def _memory_key_for_input(item: AuthorityClaimResolutionMemoryGuardInput) -> str:
    encoded = json.dumps(
        {
            "authority_bucket": item.authority_bucket,
            "raw_authority_reference": item.raw_authority_reference,
            "raw_claim_reference": item.raw_claim_reference,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _aggregate_status(
    rows: tuple[ResearchStrategyAuthorityClaimResolutionMemoryGuardRow, ...],
) -> str:
    status = "pass"
    for row in rows:
        if _STATUS_RANK[row.status] > _STATUS_RANK[status]:
            status = row.status
    return status


def _count_status(
    rows: tuple[ResearchStrategyAuthorityClaimResolutionMemoryGuardRow, ...],
    status: str,
) -> Decimal:
    total = _COUNT_ZERO
    for row in rows:
        if row.status == status:
            total += _COUNT_ONE
    return total


def _aggregate_reason_codes(
    rows: tuple[ResearchStrategyAuthorityClaimResolutionMemoryGuardRow, ...],
) -> tuple[str, ...]:
    reason_codes = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
    }
    if not reason_codes:
        return ("authority_claim_resolution_memory_clear",)
    return tuple(sorted(reason_codes))


def _aggregate_metrics(
    rows: tuple[ResearchStrategyAuthorityClaimResolutionMemoryGuardRow, ...],
) -> dict[str, Decimal]:
    if not rows:
        return {
            "max_claim_resolution_age_hours": _ZERO_METRIC,
            "max_authority_memory_age_hours": _ZERO_METRIC,
            "min_resolution_agreement_score": _ZERO_METRIC,
            "min_memory_recall_score": _ZERO_METRIC,
            "max_conflict_pressure": _ZERO_METRIC,
        }
    return {
        "max_claim_resolution_age_hours": max(
            row.claim_resolution_age_hours for row in rows
        ),
        "max_authority_memory_age_hours": max(
            row.authority_memory_age_hours for row in rows
        ),
        "min_resolution_agreement_score": min(
            row.resolution_agreement_score for row in rows
        ),
        "min_memory_recall_score": min(row.memory_recall_score for row in rows),
        "max_conflict_pressure": max(row.conflict_pressure for row in rows),
    }


def _validate_report_consistency(
    report: ResearchStrategyAuthorityClaimResolutionMemoryGuardReport,
) -> None:
    rows = report.rows
    if report.status != _aggregate_status(rows):
        raise ValueError("status must match row statuses")
    if report.pass_count != _count_status(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_status(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count_status(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.checked_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("checked_count must match row counts")
    if report.reason_codes != _aggregate_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if _aggregate_metrics(rows) != {
        "max_claim_resolution_age_hours": report.max_claim_resolution_age_hours,
        "max_authority_memory_age_hours": report.max_authority_memory_age_hours,
        "min_resolution_agreement_score": report.min_resolution_agreement_score,
        "min_memory_recall_score": report.min_memory_recall_score,
        "max_conflict_pressure": report.max_conflict_pressure,
    }:
        raise ValueError("aggregate metrics must match rows")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    unknown = set(payload) - _PUBLIC_PAYLOAD_KEYS
    if unknown:
        raise ValueError("unsafe or unsupported public payload field")
    missing = _PUBLIC_PAYLOAD_KEYS - set(payload)
    if missing:
        raise ValueError("public payload missing required field")
    _require_datetime_string("generated_at", payload["generated_at"])
    _require_safe_public_string("config_version", payload["config_version"])
    _require_status("status", payload["status"])
    for field_name in (
        "checked_count",
        "pass_count",
        "watch_count",
        "block_count",
    ):
        _require_decimal_string(field_name, payload[field_name], count=True)
    for field_name in (
        "max_claim_resolution_age_hours",
        "max_authority_memory_age_hours",
        "min_resolution_agreement_score",
        "min_memory_recall_score",
        "max_conflict_pressure",
    ):
        _require_decimal_string(field_name, payload[field_name])
    if type(payload["rows"]) is not list:
        raise ValueError("rows must be a list")
    for row in payload["rows"]:
        _validate_public_row_payload(row)
    _normalize_reason_codes("reason_codes", tuple(payload["reason_codes"]))
    _require_digest_string(
        "derived_validation_digest",
        payload["derived_validation_digest"],
    )
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    if payload["derived_validation_digest"] != _payload_validation_digest(payload):
        raise ValueError("derived_validation_digest must match payload values")


def _validate_public_row_payload(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("rows must contain JSON objects")
    unknown = set(value) - _ROW_PAYLOAD_KEYS
    if unknown:
        raise ValueError("unsafe or unsupported public row field")
    missing = _ROW_PAYLOAD_KEYS - set(value)
    if missing:
        raise ValueError("public row missing required field")
    _require_digest_string("memory_key", value["memory_key"])
    _require_safe_public_string("authority_bucket", value["authority_bucket"])
    _require_status("status", value["status"])
    for field_name in (
        "claim_resolution_age_hours",
        "authority_memory_age_hours",
        "resolution_agreement_score",
        "memory_recall_score",
        "conflict_pressure",
    ):
        _require_decimal_string(field_name, value[field_name])
    _normalize_reason_codes("reason_codes", tuple(value["reason_codes"]))


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(
        unsigned,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        _require_datetime("datetime", value)
        return value.astimezone(UTC).isoformat()
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        raise ValueError("JSON numerics must be Decimal-derived strings")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _normalize_decimal_field(
    instance: object,
    field_name: str,
    *,
    non_negative: bool = False,
    probability: bool = False,
) -> None:
    value = getattr(instance, field_name)
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if non_negative and value < _COUNT_ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    if probability and not (_COUNT_ZERO <= value <= _COUNT_ONE):
        raise ValueError(f"{field_name} must be between 0 and 1")
    object.__setattr__(instance, field_name, value.quantize(_METRIC_QUANTUM))


def _normalize_count_field(instance: object, field_name: str) -> None:
    value = getattr(instance, field_name)
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < _COUNT_ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")


def _require_decimal_string(
    field_name: str,
    value: object,
    *,
    count: bool = False,
) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if count and parsed != parsed.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal string")


def _require_datetime(field_name: str, value: object) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _require_datetime_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    _require_datetime(field_name, parsed)


def _require_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_status(field_name: str, value: object) -> None:
    if value not in REPORT_STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")


def _normalize_reason_codes(
    field_name: str,
    value: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for reason_code in value:
        _require_safe_public_string(field_name, reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _require_nonempty_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_safe_public_string(field_name: str, value: object) -> None:
    _require_nonempty_string(field_name, value)
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    _reject_unsafe_fragment(field_name, value)


def _require_digest_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest string")
    if len(value) != 64 or any(character not in _HEX_DIGITS for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest string")


def _reject_duplicate_memory_keys(
    rows: tuple[ResearchStrategyAuthorityClaimResolutionMemoryGuardRow, ...],
) -> None:
    seen: set[str] = set()
    for row in rows:
        if row.memory_key in seen:
            raise ValueError("duplicate memory_key values are not supported")
        seen.add(row.memory_key)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_fragment(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_fragment(label, value)
        return
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)):
        raise ValueError("public payload numerics must be Decimal-derived strings")


def _reject_unsafe_fragment(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public payload fragment in {label}")


__all__ = (
    "AuthorityClaimResolutionMemoryGuardConfig",
    "AuthorityClaimResolutionMemoryGuardInput",
    "ResearchStrategyAuthorityClaimResolutionMemoryGuardReport",
    "ResearchStrategyAuthorityClaimResolutionMemoryGuardRow",
    "build_research_strategy_authority_claim_resolution_memory_guard_report",
    "research_strategy_authority_claim_resolution_memory_guard_payload",
)
