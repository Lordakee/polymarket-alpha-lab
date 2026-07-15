"""Public-safe report-only domain rotation capacity reducer."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any, final


__all__ = (
    "PUBLIC_STATUSES",
    "REQUIRED_REVIEW_DOMAINS",
    "ResearchTeamDomainRotationCapacityConfig",
    "ResearchTeamDomainRotationCapacityObservation",
    "ResearchTeamDomainRotationCapacityReasonCodeCount",
    "ResearchTeamDomainRotationCapacityReport",
    "ResearchTeamDomainRotationCapacityRow",
    "build_research_team_domain_rotation_capacity_report",
    "research_team_domain_rotation_capacity_report_payload",
)


DEFAULT_CONFIG_VERSION = "research_team_domain_rotation_capacity_report.v1"
PUBLIC_STATUSES = ("pass", "watch", "block")
REQUIRED_REVIEW_DOMAINS = (
    "politics",
    "crypto",
    "equities",
    "commodities",
    "football",
    "basketball",
    "other",
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_DECIMAL_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_PUBLIC_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_FLAG_NAMES = ("paper_only", "report_only", "readonly")

CAPACITY_CLEAR_REASON = "domain_rotation_capacity_clear"
CAPACITY_BLOCK_PRESENT_REASON = "domain_rotation_capacity_block_present"
CAPACITY_WATCH_PRESENT_REASON = "domain_rotation_capacity_watch_present"
MISSING_DOMAIN_REASON = "domain_rotation_capacity_missing_domain"
CAPACITY_OVERLOADED_REASON = "capacity_overloaded"
CAPACITY_NEAR_LIMIT_REASON = "capacity_near_limit"
STALE_ROTATION_BLOCK_REASON = "stale_rotation_block"
STALE_ROTATION_WATCH_REASON = "stale_rotation_watch"
CALIBRATION_BLOCK_REASON = "calibration_block"
CALIBRATION_WATCH_REASON = "calibration_watch"

REASON_CODE_SEQUENCE = (
    CAPACITY_BLOCK_PRESENT_REASON,
    CAPACITY_WATCH_PRESENT_REASON,
    MISSING_DOMAIN_REASON,
    CAPACITY_OVERLOADED_REASON,
    CAPACITY_NEAR_LIMIT_REASON,
    STALE_ROTATION_BLOCK_REASON,
    STALE_ROTATION_WATCH_REASON,
    CALIBRATION_BLOCK_REASON,
    CALIBRATION_WATCH_REASON,
    CAPACITY_CLEAR_REASON,
)

_ROW_REASON_CODE_SEQUENCE = (
    CAPACITY_OVERLOADED_REASON,
    CAPACITY_NEAR_LIMIT_REASON,
    STALE_ROTATION_BLOCK_REASON,
    STALE_ROTATION_WATCH_REASON,
    CALIBRATION_BLOCK_REASON,
    CALIBRATION_WATCH_REASON,
    CAPACITY_CLEAR_REASON,
)

_UNSAFE_PUBLIC_TERMS = (
    "raw",
    "candidate_id",
    "candidateid",
    "market_id",
    "marketid",
    "market_slug",
    "marketslug",
    "market_question",
    "source_url",
    "source_text",
    "source_reference",
    "source_ref",
    "http://",
    "https://",
    "postgres://",
    "postgresql://",
    "database_url",
    "dsn",
    "table",
    "token",
    "secret",
    "credential",
    "password",
    "private_key",
    "api_key",
    "auth",
    "wallet",
    "order",
    "trade",
    "live",
    "execution",
    "position",
    "buy",
    "sell",
    "recommendation",
    "sizing",
)


class FrozenJsonObject(dict[str, Any]):
    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("payload is immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("payload is immutable")

    def clear(self) -> None:
        raise TypeError("payload is immutable")

    def pop(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def popitem(self) -> tuple[str, Any]:
        raise TypeError("payload is immutable")

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("payload is immutable")

    def __ior__(self, other: object) -> FrozenJsonObject:
        raise TypeError("payload is immutable")


class FrozenJsonArray(tuple[Any, ...]):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Sequence) and not isinstance(other, (str, bytes)):
            return tuple(self) == tuple(other)
        return False

    def append(self, value: Any) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: Any) -> None:
        raise TypeError("payload is immutable")


@final
@dataclass(frozen=True, slots=True)
class ResearchTeamDomainRotationCapacityConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    watch_capacity_utilization: Decimal = Decimal("0.850000")
    block_capacity_utilization: Decimal = Decimal("1.000000")
    watch_stale_review_ratio: Decimal = Decimal("0.150000")
    block_stale_review_ratio: Decimal = Decimal("0.300000")
    watch_min_calibration_score: Decimal = Decimal("0.700000")
    block_min_calibration_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super(ResearchTeamDomainRotationCapacityConfig, cls).__init_subclass__(
            **kwargs,
        )
        if cls is not ResearchTeamDomainRotationCapacityConfig:
            raise TypeError(
                "ResearchTeamDomainRotationCapacityConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainRotationCapacityConfig:
            raise ValueError(
                "config must be exactly ResearchTeamDomainRotationCapacityConfig",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        for field_name in (
            "watch_capacity_utilization",
            "block_capacity_utilization",
            "watch_stale_review_ratio",
            "block_stale_review_ratio",
            "watch_min_calibration_score",
            "block_min_calibration_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_capacity_utilization < self.watch_capacity_utilization:
            raise ValueError("block_capacity_utilization must meet or exceed watch")
        if self.block_stale_review_ratio < self.watch_stale_review_ratio:
            raise ValueError("block_stale_review_ratio must meet or exceed watch")
        if self.block_min_calibration_score > self.watch_min_calibration_score:
            raise ValueError("block_min_calibration_score must not exceed watch")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchTeamDomainRotationCapacityObservation:
    team_id: str
    domain_id: str
    observed_at: datetime
    pending_review_count: Decimal
    available_review_capacity: Decimal
    stale_review_count: Decimal
    calibration_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super(ResearchTeamDomainRotationCapacityObservation, cls).__init_subclass__(
            **kwargs,
        )
        if cls is not ResearchTeamDomainRotationCapacityObservation:
            raise TypeError(
                "ResearchTeamDomainRotationCapacityObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainRotationCapacityObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchTeamDomainRotationCapacityObservation",
            )
        object.__setattr__(
            self,
            "team_id",
            _require_public_identifier("team_id", self.team_id),
        )
        object.__setattr__(
            self,
            "domain_id",
            _require_domain_id("domain_id", self.domain_id),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("pending_review_count", "stale_review_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "available_review_capacity",
            _require_positive_count_decimal(
                "available_review_capacity",
                self.available_review_capacity,
            ),
        )
        object.__setattr__(
            self,
            "calibration_score",
            _require_ratio_decimal("calibration_score", self.calibration_score),
        )
        if self.stale_review_count > self.pending_review_count:
            raise ValueError("stale_review_count cannot exceed pending_review_count")
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchTeamDomainRotationCapacityRow:
    team_id: str
    domain_id: str
    observed_at: datetime
    pending_review_count: Decimal
    available_review_capacity: Decimal
    stale_review_count: Decimal
    calibration_score: Decimal
    capacity_utilization: Decimal
    capacity_shortfall_count: Decimal
    stale_review_ratio: Decimal
    calibration_gap_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super(ResearchTeamDomainRotationCapacityRow, cls).__init_subclass__(
            **kwargs,
        )
        if cls is not ResearchTeamDomainRotationCapacityRow:
            raise TypeError(
                "ResearchTeamDomainRotationCapacityRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainRotationCapacityRow:
            raise ValueError("row must be exactly ResearchTeamDomainRotationCapacityRow")
        object.__setattr__(
            self,
            "team_id",
            _require_public_identifier("team_id", self.team_id),
        )
        object.__setattr__(
            self,
            "domain_id",
            _require_domain_id("domain_id", self.domain_id),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "pending_review_count",
            "stale_review_count",
            "capacity_shortfall_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "capacity_utilization",
            _require_nonnegative_decimal(
                "capacity_utilization",
                self.capacity_utilization,
            ),
        )
        object.__setattr__(
            self,
            "available_review_capacity",
            _require_positive_count_decimal(
                "available_review_capacity",
                self.available_review_capacity,
            ),
        )
        object.__setattr__(
            self,
            "calibration_score",
            _require_ratio_decimal("calibration_score", self.calibration_score),
        )
        for field_name in ("stale_review_ratio", "calibration_gap_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        if self.stale_review_count > self.pending_review_count:
            raise ValueError("stale_review_count cannot exceed pending_review_count")
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchTeamDomainRotationCapacityReasonCodeCount:
    reason_code: str
    count: Decimal
    domain_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super(
            ResearchTeamDomainRotationCapacityReasonCodeCount,
            cls,
        ).__init_subclass__(**kwargs)
        if cls is not ResearchTeamDomainRotationCapacityReasonCodeCount:
            raise TypeError(
                "ResearchTeamDomainRotationCapacityReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainRotationCapacityReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "ResearchTeamDomainRotationCapacityReasonCodeCount",
            )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "domain_ratio",
            _require_ratio_decimal("domain_ratio", self.domain_ratio),
        )
        _require_hard_flags("reason count", self)
        _reject_unsafe_public_payload("reason count", self)


def _revalidate_config(
    value: object,
) -> ResearchTeamDomainRotationCapacityConfig:
    if type(value) is not ResearchTeamDomainRotationCapacityConfig:
        raise ValueError("config must be exactly ResearchTeamDomainRotationCapacityConfig")
    return ResearchTeamDomainRotationCapacityConfig(
        **{field.name: getattr(value, field.name) for field in fields(value)},
    )


def _revalidate_observation(
    value: object,
) -> ResearchTeamDomainRotationCapacityObservation:
    if type(value) is not ResearchTeamDomainRotationCapacityObservation:
        raise ValueError(
            "observations must contain ResearchTeamDomainRotationCapacityObservation",
        )
    return ResearchTeamDomainRotationCapacityObservation(
        **{field.name: getattr(value, field.name) for field in fields(value)},
    )


def _revalidate_row(value: object) -> ResearchTeamDomainRotationCapacityRow:
    if type(value) is not ResearchTeamDomainRotationCapacityRow:
        raise ValueError("rows must contain ResearchTeamDomainRotationCapacityRow")
    return ResearchTeamDomainRotationCapacityRow(
        **{field.name: getattr(value, field.name) for field in fields(value)},
    )


def _revalidate_reason_code_count(
    value: object,
) -> ResearchTeamDomainRotationCapacityReasonCodeCount:
    if type(value) is not ResearchTeamDomainRotationCapacityReasonCodeCount:
        raise ValueError(
            "reason_code_counts must contain "
            "ResearchTeamDomainRotationCapacityReasonCodeCount",
        )
    return ResearchTeamDomainRotationCapacityReasonCodeCount(
        **{field.name: getattr(value, field.name) for field in fields(value)},
    )


@final
@dataclass(frozen=True, slots=True)
class ResearchTeamDomainRotationCapacityReport:
    generated_at: datetime
    config_version: str
    config: ResearchTeamDomainRotationCapacityConfig
    report_status: str
    required_domain_count: Decimal
    covered_domain_count: Decimal
    missing_domain_count: Decimal
    team_domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_pending_review_count: Decimal
    total_available_review_capacity: Decimal
    total_capacity_shortfall_count: Decimal
    weighted_capacity_utilization: Decimal
    max_stale_review_ratio: Decimal
    min_calibration_score: Decimal
    average_calibration_score: Decimal
    rows: tuple[ResearchTeamDomainRotationCapacityRow, ...]
    reason_code_counts: tuple[ResearchTeamDomainRotationCapacityReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super(ResearchTeamDomainRotationCapacityReport, cls).__init_subclass__(
            **kwargs,
        )
        if cls is not ResearchTeamDomainRotationCapacityReport:
            raise TypeError(
                "ResearchTeamDomainRotationCapacityReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchTeamDomainRotationCapacityReport:
            raise ValueError(
                "report must be exactly ResearchTeamDomainRotationCapacityReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        object.__setattr__(self, "config", _revalidate_config(self.config))
        _require_hard_flags("config", self.config)
        _require_status("report_status", self.report_status)
        for field_name in (
            "required_domain_count",
            "covered_domain_count",
            "missing_domain_count",
            "team_domain_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_pending_review_count",
            "total_available_review_capacity",
            "total_capacity_shortfall_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "weighted_capacity_utilization",
            "max_stale_review_ratio",
            "min_calibration_score",
            "average_calibration_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
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
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _public_digest_for_report(self)
        if self.public_digest == "":
            object.__setattr__(self, "public_digest", expected_digest)
        else:
            _require_public_digest("public_digest", self.public_digest)
            if self.public_digest != expected_digest:
                raise ValueError("public_digest must match report payload")

    @property
    def payload(self) -> FrozenJsonObject:
        return research_team_domain_rotation_capacity_report_payload(self)


def build_research_team_domain_rotation_capacity_report(
    observations: Sequence[ResearchTeamDomainRotationCapacityObservation],
    *,
    generated_at: datetime,
    config: ResearchTeamDomainRotationCapacityConfig | None = None,
) -> ResearchTeamDomainRotationCapacityReport:
    cfg = _revalidate_config(config or ResearchTeamDomainRotationCapacityConfig())
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(
        observations,
        generated_at=report_time,
    )
    rows = tuple(sorted((_row_from_observation(row, cfg) for row in normalized), key=_row_sort_key))
    covered_domains = frozenset(row.domain_id for row in rows)
    missing_domain_count = _count(
        len(tuple(domain for domain in REQUIRED_REVIEW_DOMAINS if domain not in covered_domains)),
    )
    reason_codes = _report_reason_codes(rows, missing_domain_count=missing_domain_count)
    return ResearchTeamDomainRotationCapacityReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        config=cfg,
        report_status=_report_status(rows, missing_domain_count=missing_domain_count),
        required_domain_count=_count(len(REQUIRED_REVIEW_DOMAINS)),
        covered_domain_count=_count(len(covered_domains)),
        missing_domain_count=missing_domain_count,
        team_domain_count=_count(len(rows)),
        pass_count=_count(_status_count(rows, STATUS_PASS)),
        watch_count=_count(_status_count(rows, STATUS_WATCH)),
        block_count=_count(_status_count(rows, STATUS_BLOCK)),
        total_pending_review_count=_sum_decimal(
            row.pending_review_count for row in rows
        ),
        total_available_review_capacity=_sum_decimal(
            row.available_review_capacity for row in rows
        ),
        total_capacity_shortfall_count=_sum_decimal(
            row.capacity_shortfall_count for row in rows
        ),
        weighted_capacity_utilization=_clamp_ratio(
            _ratio_or_zero(
                _sum_decimal(row.pending_review_count for row in rows),
                _sum_decimal(row.available_review_capacity for row in rows),
            ),
        ),
        max_stale_review_ratio=max(
            (row.stale_review_ratio for row in rows),
            default=_ZERO,
        ),
        min_calibration_score=min(
            (row.calibration_score for row in rows),
            default=_ZERO,
        ),
        average_calibration_score=_average_decimal(
            row.calibration_score for row in rows
        ),
        rows=rows,
        reason_code_counts=_reason_code_counts(
            rows,
            missing_domain_count=missing_domain_count,
        ),
        reason_codes=reason_codes,
    )


def research_team_domain_rotation_capacity_report_payload(
    report: ResearchTeamDomainRotationCapacityReport | Mapping[str, Any],
) -> FrozenJsonObject:
    if type(report) is ResearchTeamDomainRotationCapacityReport:
        _require_hard_flags("report", report)
        _validate_report(report)
        _reject_unsafe_public_payload("report", report)
        payload = _report_payload(report)
        _validate_public_payload_schema(payload)
        _validate_payload_flags(payload)
        _validate_payload_digest(payload)
        validated_report = _report_from_payload(payload, derive_digest=True)
        if payload != _report_payload(validated_report):
            raise ValueError("report payload must use canonical schema values")
        _reject_unsafe_public_payload("payload", payload)
        return _freeze_json_object(payload)
    if not isinstance(report, Mapping):
        raise ValueError("report payload must be a mapping")
    _reject_unsafe_public_payload("payload", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a mapping")
    _validate_public_payload_schema(payload)
    _validate_payload_flags(payload)
    _validate_payload_digest(payload)
    validated_report = _report_from_payload(payload)
    if payload != _report_payload(validated_report):
        raise ValueError("report payload must use canonical schema values")
    _reject_unsafe_public_payload("payload", payload)
    return _freeze_json_object(payload)


def _validate_public_payload_schema(payload: Mapping[str, Any]) -> None:
    _require_exact_payload_schema(
        "report payload",
        payload,
        ResearchTeamDomainRotationCapacityReport,
    )
    config = payload["config"]
    if not isinstance(config, Mapping):
        raise ValueError("config payload must be a mapping")
    _require_exact_payload_schema(
        "config payload",
        config,
        ResearchTeamDomainRotationCapacityConfig,
    )
    rows = payload["rows"]
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise ValueError("rows must be a sequence")
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("row payload must be a mapping")
        _require_exact_payload_schema(
            "row payload",
            row,
            ResearchTeamDomainRotationCapacityRow,
        )
    reason_code_counts = payload["reason_code_counts"]
    if not isinstance(reason_code_counts, Sequence) or isinstance(
        reason_code_counts,
        (str, bytes),
    ):
        raise ValueError("reason_code_counts must be a sequence")
    for reason_code_count in reason_code_counts:
        if not isinstance(reason_code_count, Mapping):
            raise ValueError("reason code count payload must be a mapping")
        _require_exact_payload_schema(
            "reason code count payload",
            reason_code_count,
            ResearchTeamDomainRotationCapacityReasonCodeCount,
        )


def _require_exact_payload_schema(
    label: str,
    payload: Mapping[str, Any],
    expected_type: type[object],
) -> None:
    expected_fields = tuple(field.name for field in fields(expected_type))
    if not isinstance(payload, Mapping) or tuple(payload) != expected_fields:
        raise ValueError(f"{label} must use exact schema")


def _report_from_payload(
    payload: Mapping[str, Any],
    *,
    derive_digest: bool = False,
) -> ResearchTeamDomainRotationCapacityReport:
    config = _config_from_payload(payload["config"])
    return ResearchTeamDomainRotationCapacityReport(
        generated_at=_datetime_from_payload("generated_at", payload["generated_at"]),
        config_version=_identifier_from_payload(
            "config_version",
            payload["config_version"],
        ),
        config=config,
        report_status=_status_from_payload(
            "report_status",
            payload["report_status"],
        ),
        required_domain_count=_count_from_payload(
            "required_domain_count",
            payload["required_domain_count"],
        ),
        covered_domain_count=_count_from_payload(
            "covered_domain_count",
            payload["covered_domain_count"],
        ),
        missing_domain_count=_count_from_payload(
            "missing_domain_count",
            payload["missing_domain_count"],
        ),
        team_domain_count=_count_from_payload(
            "team_domain_count",
            payload["team_domain_count"],
        ),
        pass_count=_count_from_payload("pass_count", payload["pass_count"]),
        watch_count=_count_from_payload("watch_count", payload["watch_count"]),
        block_count=_count_from_payload("block_count", payload["block_count"]),
        total_pending_review_count=_count_from_payload(
            "total_pending_review_count",
            payload["total_pending_review_count"],
        ),
        total_available_review_capacity=_count_from_payload(
            "total_available_review_capacity",
            payload["total_available_review_capacity"],
        ),
        total_capacity_shortfall_count=_count_from_payload(
            "total_capacity_shortfall_count",
            payload["total_capacity_shortfall_count"],
        ),
        weighted_capacity_utilization=_ratio_from_payload(
            "weighted_capacity_utilization",
            payload["weighted_capacity_utilization"],
        ),
        max_stale_review_ratio=_ratio_from_payload(
            "max_stale_review_ratio",
            payload["max_stale_review_ratio"],
        ),
        min_calibration_score=_ratio_from_payload(
            "min_calibration_score",
            payload["min_calibration_score"],
        ),
        average_calibration_score=_ratio_from_payload(
            "average_calibration_score",
            payload["average_calibration_score"],
        ),
        rows=tuple(_row_from_payload(row) for row in payload["rows"]),
        reason_code_counts=tuple(
            _reason_code_count_from_payload(item)
            for item in payload["reason_code_counts"]
        ),
        reason_codes=_reason_codes_from_payload(
            "reason_codes",
            payload["reason_codes"],
        ),
        public_digest=(
            ""
            if derive_digest
            else _digest_from_payload("public_digest", payload["public_digest"])
        ),
        paper_only=_true_from_payload("paper_only", payload["paper_only"]),
        report_only=_true_from_payload("report_only", payload["report_only"]),
        readonly=_true_from_payload("readonly", payload["readonly"]),
    )


def _config_from_payload(
    payload: Mapping[str, Any],
) -> ResearchTeamDomainRotationCapacityConfig:
    return ResearchTeamDomainRotationCapacityConfig(
        config_version=_identifier_from_payload(
            "config.config_version",
            payload["config_version"],
        ),
        watch_capacity_utilization=_ratio_from_payload(
            "config.watch_capacity_utilization",
            payload["watch_capacity_utilization"],
        ),
        block_capacity_utilization=_ratio_from_payload(
            "config.block_capacity_utilization",
            payload["block_capacity_utilization"],
        ),
        watch_stale_review_ratio=_ratio_from_payload(
            "config.watch_stale_review_ratio",
            payload["watch_stale_review_ratio"],
        ),
        block_stale_review_ratio=_ratio_from_payload(
            "config.block_stale_review_ratio",
            payload["block_stale_review_ratio"],
        ),
        watch_min_calibration_score=_ratio_from_payload(
            "config.watch_min_calibration_score",
            payload["watch_min_calibration_score"],
        ),
        block_min_calibration_score=_ratio_from_payload(
            "config.block_min_calibration_score",
            payload["block_min_calibration_score"],
        ),
        paper_only=_true_from_payload("config.paper_only", payload["paper_only"]),
        report_only=_true_from_payload("config.report_only", payload["report_only"]),
        readonly=_true_from_payload("config.readonly", payload["readonly"]),
    )


def _row_from_payload(
    payload: Mapping[str, Any],
) -> ResearchTeamDomainRotationCapacityRow:
    return ResearchTeamDomainRotationCapacityRow(
        team_id=_identifier_from_payload("row.team_id", payload["team_id"]),
        domain_id=_domain_from_payload("row.domain_id", payload["domain_id"]),
        observed_at=_datetime_from_payload(
            "row.observed_at",
            payload["observed_at"],
        ),
        pending_review_count=_count_from_payload(
            "row.pending_review_count",
            payload["pending_review_count"],
        ),
        available_review_capacity=_positive_count_from_payload(
            "row.available_review_capacity",
            payload["available_review_capacity"],
        ),
        stale_review_count=_count_from_payload(
            "row.stale_review_count",
            payload["stale_review_count"],
        ),
        calibration_score=_ratio_from_payload(
            "row.calibration_score",
            payload["calibration_score"],
        ),
        capacity_utilization=_nonnegative_decimal_from_payload(
            "capacity_utilization",
            payload["capacity_utilization"],
        ),
        capacity_shortfall_count=_count_from_payload(
            "capacity_shortfall_count",
            payload["capacity_shortfall_count"],
        ),
        stale_review_ratio=_ratio_from_payload(
            "stale_review_ratio",
            payload["stale_review_ratio"],
        ),
        calibration_gap_score=_ratio_from_payload(
            "calibration_gap_score",
            payload["calibration_gap_score"],
        ),
        status=_status_from_payload("row.status", payload["status"]),
        reason_codes=_reason_codes_from_payload(
            "row.reason_codes",
            payload["reason_codes"],
        ),
        paper_only=_true_from_payload("row.paper_only", payload["paper_only"]),
        report_only=_true_from_payload("row.report_only", payload["report_only"]),
        readonly=_true_from_payload("row.readonly", payload["readonly"]),
    )


def _reason_code_count_from_payload(
    payload: Mapping[str, Any],
) -> ResearchTeamDomainRotationCapacityReasonCodeCount:
    return ResearchTeamDomainRotationCapacityReasonCodeCount(
        reason_code=_reason_code_from_payload(
            "reason_code_count.reason_code",
            payload["reason_code"],
        ),
        count=_count_from_payload(
            "reason_code_count.count",
            payload["count"],
        ),
        domain_ratio=_ratio_from_payload(
            "reason_code_count.domain_ratio",
            payload["domain_ratio"],
        ),
        paper_only=_true_from_payload(
            "reason_code_count.paper_only",
            payload["paper_only"],
        ),
        report_only=_true_from_payload(
            "reason_code_count.report_only",
            payload["report_only"],
        ),
        readonly=_true_from_payload(
            "reason_code_count.readonly",
            payload["readonly"],
        ),
    )


def _row_from_observation(
    observation: ResearchTeamDomainRotationCapacityObservation,
    config: ResearchTeamDomainRotationCapacityConfig,
) -> ResearchTeamDomainRotationCapacityRow:
    capacity_utilization = _ratio_or_zero(
        observation.pending_review_count,
        observation.available_review_capacity,
    )
    capacity_shortfall_count = max(
        _ZERO,
        _subtract_decimal(
            observation.pending_review_count,
            observation.available_review_capacity,
        ),
    )
    stale_review_ratio = _ratio_or_zero(
        observation.stale_review_count,
        observation.pending_review_count,
    )
    calibration_gap_score = _subtract_decimal(_ONE, observation.calibration_score)
    status = _row_status(
        observation,
        config,
        capacity_utilization=capacity_utilization,
        stale_review_ratio=stale_review_ratio,
    )
    return ResearchTeamDomainRotationCapacityRow(
        team_id=observation.team_id,
        domain_id=observation.domain_id,
        observed_at=observation.observed_at,
        pending_review_count=observation.pending_review_count,
        available_review_capacity=observation.available_review_capacity,
        stale_review_count=observation.stale_review_count,
        calibration_score=observation.calibration_score,
        capacity_utilization=capacity_utilization,
        capacity_shortfall_count=capacity_shortfall_count,
        stale_review_ratio=stale_review_ratio,
        calibration_gap_score=calibration_gap_score,
        status=status,
        reason_codes=_row_reason_codes(
            observation,
            config,
            capacity_utilization=capacity_utilization,
            stale_review_ratio=stale_review_ratio,
        ),
    )


def _row_status(
    observation: ResearchTeamDomainRotationCapacityObservation,
    config: ResearchTeamDomainRotationCapacityConfig,
    *,
    capacity_utilization: Decimal,
    stale_review_ratio: Decimal,
) -> str:
    if (
        capacity_utilization >= config.block_capacity_utilization
        or stale_review_ratio >= config.block_stale_review_ratio
        or observation.calibration_score <= config.block_min_calibration_score
    ):
        return STATUS_BLOCK
    if (
        capacity_utilization >= config.watch_capacity_utilization
        or stale_review_ratio >= config.watch_stale_review_ratio
        or observation.calibration_score <= config.watch_min_calibration_score
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    observation: ResearchTeamDomainRotationCapacityObservation,
    config: ResearchTeamDomainRotationCapacityConfig,
    *,
    capacity_utilization: Decimal,
    stale_review_ratio: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if capacity_utilization >= config.block_capacity_utilization:
        reason_codes.append(CAPACITY_OVERLOADED_REASON)
    elif capacity_utilization >= config.watch_capacity_utilization:
        reason_codes.append(CAPACITY_NEAR_LIMIT_REASON)
    if stale_review_ratio >= config.block_stale_review_ratio:
        reason_codes.append(STALE_ROTATION_BLOCK_REASON)
    elif stale_review_ratio >= config.watch_stale_review_ratio:
        reason_codes.append(STALE_ROTATION_WATCH_REASON)
    if observation.calibration_score <= config.block_min_calibration_score:
        reason_codes.append(CALIBRATION_BLOCK_REASON)
    elif observation.calibration_score <= config.watch_min_calibration_score:
        reason_codes.append(CALIBRATION_WATCH_REASON)
    if not reason_codes:
        reason_codes.append(CAPACITY_CLEAR_REASON)
    return _normalize_reason_codes(tuple(reason_codes), require_nonempty=True)


def _report_status(
    rows: tuple[ResearchTeamDomainRotationCapacityRow, ...],
    *,
    missing_domain_count: Decimal,
) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if missing_domain_count > _ZERO or any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainRotationCapacityRow, ...],
    *,
    missing_domain_count: Decimal,
) -> tuple[str, ...]:
    if any(row.status == STATUS_BLOCK for row in rows):
        reason_codes = [CAPACITY_BLOCK_PRESENT_REASON]
    elif any(row.status == STATUS_WATCH for row in rows):
        reason_codes = [CAPACITY_WATCH_PRESENT_REASON]
    elif missing_domain_count > _ZERO:
        return (MISSING_DOMAIN_REASON,)
    else:
        return (CAPACITY_CLEAR_REASON,)

    seen = set(reason_codes)
    if missing_domain_count > _ZERO:
        seen.add(MISSING_DOMAIN_REASON)
        reason_codes.append(MISSING_DOMAIN_REASON)
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code == CAPACITY_CLEAR_REASON or reason_code in seen:
                continue
            seen.add(reason_code)
            reason_codes.append(reason_code)
    return _normalize_reason_codes(tuple(reason_codes), require_nonempty=True)


def _reason_code_counts(
    rows: tuple[ResearchTeamDomainRotationCapacityRow, ...],
    *,
    missing_domain_count: Decimal,
) -> tuple[ResearchTeamDomainRotationCapacityReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    if missing_domain_count > _ZERO:
        counts[MISSING_DOMAIN_REASON] = missing_domain_count
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = _sum_decimal(
                (counts.get(reason_code, _ZERO), _ONE),
            )
    if not counts:
        counts[CAPACITY_CLEAR_REASON] = _ONE
    required_domain_total = _count(len(REQUIRED_REVIEW_DOMAINS))
    row_total = _count(len(rows))
    return tuple(
        ResearchTeamDomainRotationCapacityReasonCodeCount(
            reason_code=reason_code,
            count=counts[reason_code],
            domain_ratio=_ratio_or_zero(
                counts[reason_code],
                (
                    required_domain_total
                    if reason_code == MISSING_DOMAIN_REASON
                    else row_total
                ),
            ),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _normalize_observations(
    observations: Sequence[ResearchTeamDomainRotationCapacityObservation],
    *,
    generated_at: datetime,
) -> tuple[ResearchTeamDomainRotationCapacityObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized = tuple(observations)
    seen: set[tuple[str, str]] = set()
    validated: list[ResearchTeamDomainRotationCapacityObservation] = []
    for observation in normalized:
        normalized_observation = _revalidate_observation(observation)
        if normalized_observation.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")
        key = (
            normalized_observation.team_id,
            normalized_observation.domain_id,
        )
        if key in seen:
            raise ValueError("observations must not duplicate team/domain pairs")
        seen.add(key)
        validated.append(normalized_observation)
    return tuple(sorted(validated, key=lambda item: (item.domain_id, item.team_id)))


def _normalize_rows(
    rows: object,
) -> tuple[ResearchTeamDomainRotationCapacityRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must contain ResearchTeamDomainRotationCapacityRow")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "rows must contain ResearchTeamDomainRotationCapacityRow",
        ) from exc
    seen: set[tuple[str, str]] = set()
    validated: list[ResearchTeamDomainRotationCapacityRow] = []
    for row in normalized:
        normalized_row = _revalidate_row(row)
        key = (normalized_row.team_id, normalized_row.domain_id)
        if key in seen:
            raise ValueError("rows must not contain duplicate team/domain pairs")
        seen.add(key)
        validated.append(normalized_row)
    return tuple(sorted(validated, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: object,
) -> tuple[ResearchTeamDomainRotationCapacityReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(
            "reason_code_counts must contain "
            "ResearchTeamDomainRotationCapacityReasonCodeCount",
        )
    try:
        normalized = tuple(values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "reason_code_counts must contain "
            "ResearchTeamDomainRotationCapacityReasonCodeCount",
        ) from exc
    validated = tuple(_revalidate_reason_code_count(item) for item in normalized)
    return tuple(
        sorted(
            validated,
            key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code),
        ),
    )


def _row_sort_key(
    row: ResearchTeamDomainRotationCapacityRow,
) -> tuple[int, Decimal, Decimal, Decimal, str, str]:
    status_rank = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}
    return (
        status_rank[row.status],
        row.capacity_utilization.copy_negate(),
        row.stale_review_ratio.copy_negate(),
        row.calibration_score,
        row.domain_id,
        row.team_id,
    )


def _status_count(
    rows: tuple[ResearchTeamDomainRotationCapacityRow, ...],
    status: str,
) -> int:
    return len(tuple(row for row in rows if row.status == status))


def _validate_row(row: ResearchTeamDomainRotationCapacityRow) -> None:
    if any(
        reason_code not in _ROW_REASON_CODE_SEQUENCE
        for reason_code in row.reason_codes
    ):
        raise ValueError("reason_codes must contain only row reason codes")
    canonical_reason_codes = tuple(
        reason_code
        for reason_code in _ROW_REASON_CODE_SEQUENCE
        if reason_code in row.reason_codes
    )
    if row.reason_codes != canonical_reason_codes:
        raise ValueError("reason_codes must use canonical order")

    expected_capacity_utilization = _ratio_or_zero(
        row.pending_review_count,
        row.available_review_capacity,
    )
    if row.capacity_utilization != expected_capacity_utilization:
        raise ValueError(
            "capacity_utilization must match pending_review_count and "
            "available_review_capacity",
        )
    expected_capacity_shortfall = max(
        _ZERO,
        _subtract_decimal(
            row.pending_review_count,
            row.available_review_capacity,
        ),
    )
    if row.capacity_shortfall_count != expected_capacity_shortfall:
        raise ValueError(
            "capacity_shortfall_count must match pending_review_count and "
            "available_review_capacity",
        )
    expected_stale_review_ratio = _ratio_or_zero(
        row.stale_review_count,
        row.pending_review_count,
    )
    if row.stale_review_ratio != expected_stale_review_ratio:
        raise ValueError(
            "stale_review_ratio must match stale_review_count and "
            "pending_review_count",
        )
    expected_calibration_gap = _subtract_decimal(_ONE, row.calibration_score)
    if row.calibration_gap_score != expected_calibration_gap:
        raise ValueError("calibration_gap_score must match calibration_score")

    block_reasons = {
        CAPACITY_OVERLOADED_REASON,
        STALE_ROTATION_BLOCK_REASON,
        CALIBRATION_BLOCK_REASON,
    }
    watch_reasons = {
        CAPACITY_NEAR_LIMIT_REASON,
        STALE_ROTATION_WATCH_REASON,
        CALIBRATION_WATCH_REASON,
    }
    if any(reason_code in block_reasons for reason_code in row.reason_codes):
        expected_status = STATUS_BLOCK
    elif any(reason_code in watch_reasons for reason_code in row.reason_codes):
        expected_status = STATUS_WATCH
    else:
        expected_status = STATUS_PASS
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")
    if expected_status == STATUS_PASS:
        if row.reason_codes != (CAPACITY_CLEAR_REASON,):
            raise ValueError("reason_codes must use the clear reason for pass rows")
    elif CAPACITY_CLEAR_REASON in row.reason_codes:
        raise ValueError("reason_codes must not use the clear reason for attention rows")


def _validate_row_against_config(
    row: ResearchTeamDomainRotationCapacityRow,
    *,
    config: ResearchTeamDomainRotationCapacityConfig,
) -> None:
    observation = ResearchTeamDomainRotationCapacityObservation(
        team_id=row.team_id,
        domain_id=row.domain_id,
        observed_at=row.observed_at,
        pending_review_count=row.pending_review_count,
        available_review_capacity=row.available_review_capacity,
        stale_review_count=row.stale_review_count,
        calibration_score=row.calibration_score,
    )
    expected_status = _row_status(
        observation,
        config,
        capacity_utilization=row.capacity_utilization,
        stale_review_ratio=row.stale_review_ratio,
    )
    if row.status != expected_status:
        raise ValueError("status must match configured row policy")
    expected_reason_codes = _row_reason_codes(
        observation,
        config,
        capacity_utilization=row.capacity_utilization,
        stale_review_ratio=row.stale_review_ratio,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match configured row policy")


def _validate_report(report: ResearchTeamDomainRotationCapacityReport) -> None:
    generated_at = _as_utc("generated_at", report.generated_at)
    config = _revalidate_config(report.config)
    if report.config_version != config.config_version:
        raise ValueError("config_version must match config")
    for row in report.rows:
        validated_row = _revalidate_row(row)
        _validate_row_against_config(validated_row, config=config)
        if validated_row.observed_at > generated_at:
            raise ValueError("row observed_at must not be in the future")
    for reason_code_count in report.reason_code_counts:
        _revalidate_reason_code_count(reason_code_count)
    covered_domains = frozenset(row.domain_id for row in report.rows)
    if report.required_domain_count != _count(len(REQUIRED_REVIEW_DOMAINS)):
        raise ValueError("required_domain_count must match required domains")
    if report.covered_domain_count != _count(len(covered_domains)):
        raise ValueError("covered_domain_count must match rows")
    if report.missing_domain_count != _count(
        len(tuple(domain for domain in REQUIRED_REVIEW_DOMAINS if domain not in covered_domains)),
    ):
        raise ValueError("missing_domain_count must match required domains")
    if report.team_domain_count != _count(len(report.rows)):
        raise ValueError("team_domain_count must match rows")
    if report.pass_count != _count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if _sum_decimal(
        (report.pass_count, report.watch_count, report.block_count),
    ) != report.team_domain_count:
        raise ValueError("status counts must match team_domain_count")
    if report.report_status != _report_status(
        report.rows,
        missing_domain_count=report.missing_domain_count,
    ):
        raise ValueError("report_status must match rows")
    if report.total_pending_review_count != _sum_decimal(
        row.pending_review_count for row in report.rows
    ):
        raise ValueError("total_pending_review_count must match rows")
    if report.total_available_review_capacity != _sum_decimal(
        row.available_review_capacity for row in report.rows
    ):
        raise ValueError("total_available_review_capacity must match rows")
    if report.total_capacity_shortfall_count != _sum_decimal(
        row.capacity_shortfall_count for row in report.rows
    ):
        raise ValueError("total_capacity_shortfall_count must match rows")
    if report.weighted_capacity_utilization != _clamp_ratio(
        _ratio_or_zero(
            report.total_pending_review_count,
            report.total_available_review_capacity,
        ),
    ):
        raise ValueError("weighted_capacity_utilization must match totals")
    if report.max_stale_review_ratio != max(
        (row.stale_review_ratio for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_stale_review_ratio must match rows")
    if report.min_calibration_score != min(
        (row.calibration_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_calibration_score must match rows")
    if report.average_calibration_score != _average_decimal(
        row.calibration_score for row in report.rows
    ):
        raise ValueError("average_calibration_score must match rows")
    if report.reason_codes != _report_reason_codes(
        report.rows,
        missing_domain_count=report.missing_domain_count,
    ):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.rows,
        missing_domain_count=report.missing_domain_count,
    ):
        raise ValueError("reason_code_counts must match rows")


def _report_payload_without_digest(
    report: ResearchTeamDomainRotationCapacityReport,
) -> dict[str, Any]:
    return {
        "generated_at": _datetime_payload(report.generated_at),
        "config_version": report.config_version,
        "config": _config_payload(report.config),
        "report_status": report.report_status,
        "required_domain_count": _decimal_payload(report.required_domain_count),
        "covered_domain_count": _decimal_payload(report.covered_domain_count),
        "missing_domain_count": _decimal_payload(report.missing_domain_count),
        "team_domain_count": _decimal_payload(report.team_domain_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "total_pending_review_count": _decimal_payload(
            report.total_pending_review_count,
        ),
        "total_available_review_capacity": _decimal_payload(
            report.total_available_review_capacity,
        ),
        "total_capacity_shortfall_count": _decimal_payload(
            report.total_capacity_shortfall_count,
        ),
        "weighted_capacity_utilization": _decimal_payload(
            report.weighted_capacity_utilization,
        ),
        "max_stale_review_ratio": _decimal_payload(report.max_stale_review_ratio),
        "min_calibration_score": _decimal_payload(report.min_calibration_score),
        "average_calibration_score": _decimal_payload(report.average_calibration_score),
        "rows": [_row_payload(row) for row in report.rows],
        "reason_code_counts": [
            _reason_code_count_payload(item) for item in report.reason_code_counts
        ],
        "reason_codes": list(report.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_payload(
    report: ResearchTeamDomainRotationCapacityReport,
) -> dict[str, Any]:
    payload = _report_payload_without_digest(report)
    flags = {field_name: payload.pop(field_name) for field_name in _FLAG_NAMES}
    payload["public_digest"] = report.public_digest
    payload.update(flags)
    return payload


def _config_payload(
    config: ResearchTeamDomainRotationCapacityConfig,
) -> dict[str, Any]:
    return {
        "config_version": config.config_version,
        "watch_capacity_utilization": _decimal_payload(
            config.watch_capacity_utilization,
        ),
        "block_capacity_utilization": _decimal_payload(
            config.block_capacity_utilization,
        ),
        "watch_stale_review_ratio": _decimal_payload(
            config.watch_stale_review_ratio,
        ),
        "block_stale_review_ratio": _decimal_payload(
            config.block_stale_review_ratio,
        ),
        "watch_min_calibration_score": _decimal_payload(
            config.watch_min_calibration_score,
        ),
        "block_min_calibration_score": _decimal_payload(
            config.block_min_calibration_score,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_payload(row: ResearchTeamDomainRotationCapacityRow) -> dict[str, Any]:
    return {
        "team_id": row.team_id,
        "domain_id": row.domain_id,
        "observed_at": _datetime_payload(row.observed_at),
        "pending_review_count": _decimal_payload(row.pending_review_count),
        "available_review_capacity": _decimal_payload(row.available_review_capacity),
        "stale_review_count": _decimal_payload(row.stale_review_count),
        "calibration_score": _decimal_payload(row.calibration_score),
        "capacity_utilization": _decimal_payload(row.capacity_utilization),
        "capacity_shortfall_count": _decimal_payload(row.capacity_shortfall_count),
        "stale_review_ratio": _decimal_payload(row.stale_review_ratio),
        "calibration_gap_score": _decimal_payload(row.calibration_gap_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _reason_code_count_payload(
    item: ResearchTeamDomainRotationCapacityReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": item.reason_code,
        "count": _decimal_payload(item.count),
        "domain_ratio": _decimal_payload(item.domain_ratio),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _public_digest_for_report(
    report: ResearchTeamDomainRotationCapacityReport,
) -> str:
    return _public_digest(_report_payload_without_digest(report))


def _validate_payload_digest(payload: Mapping[str, Any]) -> None:
    digest = payload.get("public_digest")
    _require_public_digest("public_digest", digest)
    values = dict(payload)
    values.pop("public_digest", None)
    expected = _public_digest(values)
    if digest != expected:
        raise ValueError("public_digest must match payload")


def _public_digest(value: object) -> str:
    payload = _json_ready(value)
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{sha256(encoded).hexdigest()}"


def _json_ready(value: object) -> Any:
    if is_dataclass(value):
        return _json_ready({field.name: getattr(value, field.name) for field in fields(value)})
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [_json_ready(item) for item in value]
    if type(value) is datetime:
        return _datetime_payload(value)
    if type(value) is Decimal:
        return _decimal_payload(value)
    return value


def _validate_payload_flags(payload: Mapping[str, Any]) -> None:
    for field_name in _FLAG_NAMES:
        if payload.get(field_name) is not True:
            raise ValueError(f"payload must set {field_name}=True")


def _count(value: int) -> Decimal:
    return _decimal(Decimal(value))


def _sum_decimal(values: Sequence[Decimal] | Any) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        total = _ZERO
        for value in values:
            total += value
        return _decimal(total)


def _average_decimal(values: Sequence[Decimal] | Any) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _decimal(
            _sum_decimal(normalized) / Decimal(len(normalized)),
        )


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _decimal(left - right)


def _ratio_or_zero(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _decimal(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _decimal(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _normalize_decimal_precision(field_name, raw)


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < _ZERO or raw > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _normalize_decimal_precision(field_name, raw)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _normalize_decimal_precision(field_name, raw)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    return _normalize_decimal_precision(
        field_name,
        _require_raw_decimal(field_name, value),
    )


def _require_raw_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    return value


def _normalize_decimal_precision(field_name: str, value: Decimal) -> Decimal:
    try:
        normalized = _decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must use the required decimal precision") from exc
    if normalized != value:
        raise ValueError(f"{field_name} must use the required decimal precision")
    return normalized


def _decimal(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        normalized = value.quantize(_DECIMAL_QUANTUM)
    if normalized.is_zero():
        return _ZERO
    return normalized


def _datetime_payload(value: datetime) -> str:
    return _as_utc("datetime", value).isoformat()


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("payload decimal must be a Decimal")
    if value.is_zero() and value.is_signed():
        raise ValueError("payload decimal must not use signed zero")
    return format(value, ".6f")


def _decimal_string_from_payload(
    field_name: str,
    value: object,
) -> tuple[str, Decimal]:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        parsed = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a canonical Decimal string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if parsed.is_zero() and parsed.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    return value, parsed


def _canonical_decimal_from_payload(
    field_name: str,
    value: object,
    validator: Any,
) -> Decimal:
    text, parsed = _decimal_string_from_payload(field_name, value)
    normalized = validator(field_name, parsed)
    if text != format(normalized, ".6f"):
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _count_from_payload(field_name: str, value: object) -> Decimal:
    return _canonical_decimal_from_payload(
        field_name,
        value,
        _require_nonnegative_count_decimal,
    )


def _positive_count_from_payload(field_name: str, value: object) -> Decimal:
    return _canonical_decimal_from_payload(
        field_name,
        value,
        _require_positive_count_decimal,
    )


def _nonnegative_decimal_from_payload(
    field_name: str,
    value: object,
) -> Decimal:
    return _canonical_decimal_from_payload(
        field_name,
        value,
        _require_nonnegative_decimal,
    )


def _ratio_from_payload(field_name: str, value: object) -> Decimal:
    return _canonical_decimal_from_payload(
        field_name,
        value,
        _require_ratio_decimal,
    )


def _datetime_from_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
        normalized = _as_utc(field_name, parsed)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be a canonical UTC datetime string",
        ) from exc
    if value != normalized.isoformat():
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _identifier_from_payload(field_name: str, value: object) -> str:
    return _require_public_identifier(field_name, value)


def _domain_from_payload(field_name: str, value: object) -> str:
    return _require_domain_id(field_name, value)


def _status_from_payload(field_name: str, value: object) -> str:
    _require_status(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _reason_code_from_payload(field_name: str, value: object) -> str:
    return _require_reason_code(field_name, value)


def _reason_codes_from_payload(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a sequence")
    return _normalize_reason_codes(tuple(value), require_nonempty=True)


def _digest_from_payload(field_name: str, value: object) -> str:
    _require_public_digest(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a public sha256 digest")
    return value


def _true_from_payload(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a public identifier")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_text(field_name, value)
    return value


def _require_domain_id(field_name: str, value: object) -> str:
    normalized = _require_public_identifier(field_name, value)
    if normalized not in REQUIRED_REVIEW_DOMAINS:
        raise ValueError(f"{field_name} must be one of {REQUIRED_REVIEW_DOMAINS}")
    return normalized


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_reason_code(field_name: str, value: object) -> str:
    normalized = _require_public_identifier(field_name, value)
    if normalized not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")
    return normalized


def _normalize_reason_codes(
    value: object,
    *,
    require_nonempty: bool = False,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not value:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        normalized_reason_code = _require_reason_code("reason_codes", reason_code)
        if normalized_reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(normalized_reason_code)
        normalized.append(normalized_reason_code)
    return tuple(normalized)


def _require_public_digest(field_name: str, value: object) -> None:
    if type(value) is not str or _PUBLIC_DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public sha256 digest")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_NAMES:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == "public_digest":
                continue
            _reject_unsafe_public_payload(f"{label}.{field.name}", getattr(value, field.name))
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_text(label, value)


def _reject_unsafe_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(_unsafe_term_matches(lowered, term) for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} must not expose restricted public material")


def _unsafe_term_matches(value: str, term: str) -> bool:
    if "://" in term or "_" in term:
        return term in value
    return re.search(rf"(^|[^a-z0-9]){re.escape(term)}([^a-z0-9]|$)", value) is not None


def _freeze_json_object(value: Mapping[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject(
        {key: _freeze_json_value(item) for key, item in value.items()},
    )


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _freeze_json_object(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value
