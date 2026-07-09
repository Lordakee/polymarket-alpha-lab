"""Report-only readiness gate for analyst source-conflict resolution."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_EVENT_SOURCE_CONFLICT_RESOLUTION_READINESS_CONFIG_VERSION = (
    "research-event-source-conflict-resolution-readiness-report"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_KEY_TOKENS = frozenset(
    (
        "auth",
        "candidate",
        "credential",
        "dsn",
        "live",
        "market",
        "order",
        "password",
        "question",
        "scrape",
        "scraping",
        "secret",
        "slug",
        "table",
        "text",
        "token",
        "trade",
        "url",
        "wallet",
    ),
)
_UNSAFE_PUBLIC_VALUE_PATTERNS = (
    "://",
    "candidate",
    "credential",
    "dsn",
    "market id",
    "market_id",
    "market slug",
    "market_slug",
    "order",
    "password",
    "postgres",
    "question",
    "scrape",
    "scraping",
    "source url",
    "source_url",
    "table",
    "token",
    "trade",
    "wallet",
)
_UNSAFE_PUBLIC_VALUE_TOKENS = frozenset(
    (
        "auth",
        "authorization",
        "execution",
        "live",
        "recommendation",
        "secret",
        "sizing",
        "trading",
    )
)
_REASON_CODE_SEQUENCE = (
    "empty_conflict_set",
    "insufficient_source_claims",
    "authority_below_threshold",
    "source_freshness_block",
    "source_freshness_watch",
    "insufficient_independence",
    "low_contradiction_severity_watch",
    "rule_source_mapping_gap",
    "readiness_score_watch",
    "conflict_resolution_readiness_pass",
)


@dataclass(frozen=True)
class ResearchEventSourceConflictResolutionReadinessConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_SOURCE_CONFLICT_RESOLUTION_READINESS_CONFIG_VERSION
    )
    min_source_claim_count: Decimal = Decimal("2.000000")
    max_fresh_source_age_seconds: Decimal = Decimal("86400.000000")
    min_authority_score: Decimal = Decimal("0.650000")
    min_independent_source_count: Decimal = Decimal("2.000000")
    min_contradiction_severity: Decimal = Decimal("0.250000")
    min_rule_source_mapping_score: Decimal = Decimal("0.750000")
    min_readiness_score: Decimal = Decimal("0.750000")
    authority_weight: Decimal = Decimal("0.250000")
    freshness_weight: Decimal = Decimal("0.200000")
    independence_weight: Decimal = Decimal("0.200000")
    contradiction_weight: Decimal = Decimal("0.150000")
    rule_source_mapping_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSourceConflictResolutionReadinessConfig:
            raise TypeError(
                "ResearchEventSourceConflictResolutionReadinessConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceConflictResolutionReadinessConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchEventSourceConflictResolutionReadinessConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_SOURCE_CONFLICT_RESOLUTION_READINESS_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("min_source_claim_count", "min_independent_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_fresh_source_age_seconds",
            _require_positive_decimal(
                "max_fresh_source_age_seconds",
                self.max_fresh_source_age_seconds,
            ),
        )
        for field_name in (
            "min_authority_score",
            "min_contradiction_severity",
            "min_rule_source_mapping_score",
            "min_readiness_score",
            "authority_weight",
            "freshness_weight",
            "independence_weight",
            "contradiction_weight",
            "rule_source_mapping_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.authority_weight
            + self.freshness_weight
            + self.independence_weight
            + self.contradiction_weight
            + self.rule_source_mapping_weight
            != _ONE
        ):
            raise ValueError("readiness weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventSourceConflictResolutionReadinessInput:
    conflict_digest: str
    rule_source_mapping_digest: str
    source_claim_count: Decimal
    independent_source_count: Decimal
    authority_score: Decimal
    newest_source_age_seconds: Decimal
    oldest_source_age_seconds: Decimal
    contradiction_severity: Decimal
    rule_source_mapping_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSourceConflictResolutionReadinessInput:
            raise TypeError(
                "ResearchEventSourceConflictResolutionReadinessInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceConflictResolutionReadinessInput:
            raise ValueError(
                "input must be exactly "
                "ResearchEventSourceConflictResolutionReadinessInput",
            )
        _require_sha256_digest("conflict_digest", self.conflict_digest)
        _require_sha256_digest(
            "rule_source_mapping_digest",
            self.rule_source_mapping_digest,
        )
        for field_name in ("source_claim_count", "independent_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.independent_source_count > self.source_claim_count:
            raise ValueError(
                "independent_source_count must not exceed source_claim_count",
            )
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
        for field_name in (
            "authority_score",
            "contradiction_severity",
            "rule_source_mapping_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchEventSourceConflictResolutionReadinessPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSourceConflictResolutionReadinessPublicPayloadItem:
            raise TypeError(
                "ResearchEventSourceConflictResolutionReadinessPublicPayloadItem "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceConflictResolutionReadinessPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchEventSourceConflictResolutionReadinessPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchEventSourceConflictResolutionReadinessRow:
    conflict_digest: str
    rule_source_mapping_digest: str
    source_claim_count: Decimal
    independent_source_count: Decimal
    authority_score: Decimal
    freshness_score: Decimal
    independence_score: Decimal
    contradiction_severity: Decimal
    rule_source_mapping_score: Decimal
    readiness_score: Decimal
    newest_source_age_seconds: Decimal
    oldest_source_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSourceConflictResolutionReadinessRow:
            raise TypeError(
                "ResearchEventSourceConflictResolutionReadinessRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceConflictResolutionReadinessRow:
            raise ValueError(
                "row must be exactly "
                "ResearchEventSourceConflictResolutionReadinessRow",
            )
        _require_sha256_digest("conflict_digest", self.conflict_digest)
        _require_sha256_digest(
            "rule_source_mapping_digest",
            self.rule_source_mapping_digest,
        )
        for field_name in ("source_claim_count", "independent_source_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.independent_source_count > self.source_claim_count:
            raise ValueError(
                "independent_source_count must not exceed source_claim_count",
            )
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
        for field_name in (
            "authority_score",
            "freshness_score",
            "independence_score",
            "contradiction_severity",
            "rule_source_mapping_score",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventSourceConflictResolutionReadinessReport:
    generated_at: datetime
    config_version: str
    status: str
    conflict_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_readiness_score: Decimal
    average_authority_score: Decimal
    average_freshness_score: Decimal
    average_independence_score: Decimal
    average_rule_source_mapping_score: Decimal
    max_contradiction_severity: Decimal
    rows: tuple[ResearchEventSourceConflictResolutionReadinessRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[
        ResearchEventSourceConflictResolutionReadinessPublicPayloadItem,
        ...,
    ]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventSourceConflictResolutionReadinessReport:
            raise TypeError(
                "ResearchEventSourceConflictResolutionReadinessReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventSourceConflictResolutionReadinessReport:
            raise ValueError(
                "report must be exactly "
                "ResearchEventSourceConflictResolutionReadinessReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_SOURCE_CONFLICT_RESOLUTION_READINESS_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in ("conflict_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_readiness_score",
            "average_authority_score",
            "average_freshness_score",
            "average_independence_score",
            "average_rule_source_mapping_score",
            "max_contradiction_severity",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
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
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchEventSourceConflictResolutionReadinessReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_event_source_conflict_resolution_readiness_report(
    inputs: Sequence[ResearchEventSourceConflictResolutionReadinessInput],
    *,
    generated_at: datetime,
    config: ResearchEventSourceConflictResolutionReadinessConfig | None = None,
    public_payload: Sequence[
        ResearchEventSourceConflictResolutionReadinessPublicPayloadItem
    ] = (),
) -> ResearchEventSourceConflictResolutionReadinessReport:
    """Build a deterministic report-only snapshot for source-conflict readiness."""

    if config is None:
        config = ResearchEventSourceConflictResolutionReadinessConfig()
    if type(config) is not ResearchEventSourceConflictResolutionReadinessConfig:
        raise ValueError(
            "config must be a ResearchEventSourceConflictResolutionReadinessConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = _build_rows(normalized_inputs, config)
    payload_items = _normalize_public_payload(public_payload)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "conflict_count": _decimal_count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_readiness_score": _average(tuple(row.readiness_score for row in rows)),
        "average_authority_score": _average(tuple(row.authority_score for row in rows)),
        "average_freshness_score": _average(tuple(row.freshness_score for row in rows)),
        "average_independence_score": _average(
            tuple(row.independence_score for row in rows),
        ),
        "average_rule_source_mapping_score": _average(
            tuple(row.rule_source_mapping_score for row in rows),
        ),
        "max_contradiction_severity": max(
            (row.contradiction_severity for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventSourceConflictResolutionReadinessReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _build_rows(
    inputs: tuple[ResearchEventSourceConflictResolutionReadinessInput, ...],
    config: ResearchEventSourceConflictResolutionReadinessConfig,
) -> tuple[ResearchEventSourceConflictResolutionReadinessRow, ...]:
    return tuple(_row_from_input(item, config) for item in inputs)


def _row_from_input(
    item: ResearchEventSourceConflictResolutionReadinessInput,
    config: ResearchEventSourceConflictResolutionReadinessConfig,
) -> ResearchEventSourceConflictResolutionReadinessRow:
    freshness_score = _freshness_score(item.newest_source_age_seconds, config)
    independence_score = _clamp_ratio(
        item.independent_source_count / config.min_independent_source_count,
    )
    readiness_score = _readiness_score(
        authority_score=item.authority_score,
        freshness_score=freshness_score,
        independence_score=independence_score,
        contradiction_severity=item.contradiction_severity,
        rule_source_mapping_score=item.rule_source_mapping_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        item,
        freshness_score=freshness_score,
        independence_score=independence_score,
        readiness_score=readiness_score,
        config=config,
    )
    return ResearchEventSourceConflictResolutionReadinessRow(
        conflict_digest=item.conflict_digest,
        rule_source_mapping_digest=item.rule_source_mapping_digest,
        source_claim_count=item.source_claim_count,
        independent_source_count=item.independent_source_count,
        authority_score=item.authority_score,
        freshness_score=freshness_score,
        independence_score=independence_score,
        contradiction_severity=item.contradiction_severity,
        rule_source_mapping_score=item.rule_source_mapping_score,
        readiness_score=readiness_score,
        newest_source_age_seconds=item.newest_source_age_seconds,
        oldest_source_age_seconds=item.oldest_source_age_seconds,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _freshness_score(
    newest_source_age_seconds: Decimal,
    config: ResearchEventSourceConflictResolutionReadinessConfig,
) -> Decimal:
    return _clamp_ratio(_ONE - (newest_source_age_seconds / config.max_fresh_source_age_seconds))


def _readiness_score(
    *,
    authority_score: Decimal,
    freshness_score: Decimal,
    independence_score: Decimal,
    contradiction_severity: Decimal,
    rule_source_mapping_score: Decimal,
    config: ResearchEventSourceConflictResolutionReadinessConfig,
) -> Decimal:
    return _clamp_ratio(
        authority_score * config.authority_weight
        + freshness_score * config.freshness_weight
        + independence_score * config.independence_weight
        + contradiction_severity * config.contradiction_weight
        + rule_source_mapping_score * config.rule_source_mapping_weight,
    )


def _row_reason_codes(
    item: ResearchEventSourceConflictResolutionReadinessInput,
    *,
    freshness_score: Decimal,
    independence_score: Decimal,
    readiness_score: Decimal,
    config: ResearchEventSourceConflictResolutionReadinessConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.source_claim_count < config.min_source_claim_count:
        reason_codes.append("insufficient_source_claims")
    if item.authority_score < config.min_authority_score:
        reason_codes.append("authority_below_threshold")
    if item.newest_source_age_seconds > config.max_fresh_source_age_seconds:
        reason_codes.append("source_freshness_block")
    elif item.oldest_source_age_seconds > config.max_fresh_source_age_seconds:
        reason_codes.append("source_freshness_watch")
    if independence_score < _ONE:
        reason_codes.append("insufficient_independence")
    if item.contradiction_severity < config.min_contradiction_severity:
        reason_codes.append("low_contradiction_severity_watch")
    if item.rule_source_mapping_score < config.min_rule_source_mapping_score:
        reason_codes.append("rule_source_mapping_gap")
    if (
        freshness_score > _ZERO
        and readiness_score < config.min_readiness_score
        and not _has_block_reason(reason_codes)
    ):
        reason_codes.append("readiness_score_watch")
    if not reason_codes:
        reason_codes.append("conflict_resolution_readiness_pass")
    return _normalize_reason_codes(reason_codes)


def _row_status(reason_codes: Sequence[str]) -> str:
    if _has_block_reason(reason_codes):
        return "block"
    if reason_codes == ("conflict_resolution_readiness_pass",):
        return "pass"
    return "watch"


def _has_block_reason(reason_codes: Sequence[str]) -> bool:
    return any(
        reason_code
        in {
            "insufficient_source_claims",
            "authority_below_threshold",
            "source_freshness_block",
            "insufficient_independence",
            "rule_source_mapping_gap",
        }
        for reason_code in reason_codes
    )


def _report_status(
    rows: tuple[ResearchEventSourceConflictResolutionReadinessRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventSourceConflictResolutionReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_conflict_set",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(reason_codes)


def _normalize_inputs(
    inputs: Sequence[ResearchEventSourceConflictResolutionReadinessInput],
) -> tuple[ResearchEventSourceConflictResolutionReadinessInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Sequence):
        raise ValueError("inputs must be a sequence")
    normalized: list[ResearchEventSourceConflictResolutionReadinessInput] = []
    seen: set[tuple[str, str]] = set()
    for item in inputs:
        if type(item) is not ResearchEventSourceConflictResolutionReadinessInput:
            raise ValueError(
                "inputs must contain ResearchEventSourceConflictResolutionReadinessInput",
            )
        key = (item.conflict_digest, item.rule_source_mapping_digest)
        if key in seen:
            raise ValueError("conflict and rule source mapping digests must be unique")
        seen.add(key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: (item.conflict_digest, item.rule_source_mapping_digest)))


def _normalize_rows(
    rows: Sequence[ResearchEventSourceConflictResolutionReadinessRow],
) -> tuple[ResearchEventSourceConflictResolutionReadinessRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchEventSourceConflictResolutionReadinessRow] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchEventSourceConflictResolutionReadinessRow:
            raise ValueError(
                "rows must contain ResearchEventSourceConflictResolutionReadinessRow",
            )
        key = (row.conflict_digest, row.rule_source_mapping_digest)
        if key in seen:
            raise ValueError("row digests must be unique")
        seen.add(key)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: (row.conflict_digest, row.rule_source_mapping_digest)))


def _normalize_public_payload(
    public_payload: Sequence[
        ResearchEventSourceConflictResolutionReadinessPublicPayloadItem
    ],
) -> tuple[ResearchEventSourceConflictResolutionReadinessPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchEventSourceConflictResolutionReadinessPublicPayloadItem] = []
    seen: set[str] = set()
    for item in public_payload:
        if type(item) is not ResearchEventSourceConflictResolutionReadinessPublicPayloadItem:
            raise ValueError(
                "public_payload must contain "
                "ResearchEventSourceConflictResolutionReadinessPublicPayloadItem",
            )
        if item.key in seen:
            raise ValueError("public_payload keys must be unique")
        seen.add(item.key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _validate_report_consistency(
    report: ResearchEventSourceConflictResolutionReadinessReport,
) -> None:
    rows = report.rows
    if report.conflict_count != _decimal_count(len(rows)):
        raise ValueError("conflict_count does not match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count does not match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count does not match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count does not match rows")
    if report.status != _report_status(rows):
        raise ValueError("status does not match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes do not match rows")
    expected_averages = {
        "average_readiness_score": _average(tuple(row.readiness_score for row in rows)),
        "average_authority_score": _average(tuple(row.authority_score for row in rows)),
        "average_freshness_score": _average(tuple(row.freshness_score for row in rows)),
        "average_independence_score": _average(
            tuple(row.independence_score for row in rows),
        ),
        "average_rule_source_mapping_score": _average(
            tuple(row.rule_source_mapping_score for row in rows),
        ),
        "max_contradiction_severity": max(
            (row.contradiction_severity for row in rows),
            default=_ZERO,
        ),
    }
    for field_name, expected in expected_averages.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} does not match rows")


def _status_count(
    rows: tuple[ResearchEventSourceConflictResolutionReadinessRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} must have hard {field_name}=True")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    normalized = " ".join(value.strip().split())
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    _reject_unsafe_public_string(field_name, normalized)
    return normalized


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchEventSourceConflictResolutionReadinessReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    tokens = tuple(token for token in re.split(r"[^a-z0-9]+", lowered) if token)
    if any(token in _UNSAFE_PUBLIC_KEY_TOKENS for token in tokens):
        raise ValueError(f"{path}.{key} has unsafe public field")
    if any(term in lowered for term in ("market_id", "market_slug", "source_url")):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(path: str, value: str) -> None:
    lowered = value.lower()
    tokens = tuple(token for token in re.split(r"[^a-z0-9]+", lowered) if token)
    if any(
        pattern in lowered for pattern in _UNSAFE_PUBLIC_VALUE_PATTERNS
    ) or any(token in _UNSAFE_PUBLIC_VALUE_TOKENS for token in tokens):
        raise ValueError(f"{path} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_EVENT_SOURCE_CONFLICT_RESOLUTION_READINESS_CONFIG_VERSION",
    "ResearchEventSourceConflictResolutionReadinessConfig",
    "ResearchEventSourceConflictResolutionReadinessInput",
    "ResearchEventSourceConflictResolutionReadinessPublicPayloadItem",
    "ResearchEventSourceConflictResolutionReadinessReport",
    "ResearchEventSourceConflictResolutionReadinessRow",
    "build_research_event_source_conflict_resolution_readiness_report",
)
