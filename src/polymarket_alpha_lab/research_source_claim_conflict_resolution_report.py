"""Report-only sanitized source-claim conflict resolution triage."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_SOURCE_CLAIM_CONFLICT_RESOLUTION_REPORT_CONFIG_VERSION = (
    "research-source-claim-conflict-resolution-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_DAY = Decimal("86400.000000")
_MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_AUTHORITY_TIERS = frozenset(("official", "primary", "secondary", "community"))
_RESOLUTION_DEPENDENCIES = frozenset(("none", "pending", "blocked"))
_HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_AUTHORITY_TIER_SCORES = {
    "official": Decimal("1.000000"),
    "primary": Decimal("0.800000"),
    "secondary": Decimal("0.500000"),
    "community": Decimal("0.200000"),
}
_REASON_CODE_SEQUENCE = (
    "claim_conflict_authority_block",
    "claim_conflict_authority_watch",
    "claim_conflict_authority_pass",
    "claim_conflict_freshness_block",
    "claim_conflict_freshness_watch",
    "claim_conflict_freshness_pass",
    "claim_conflict_corroboration_block",
    "claim_conflict_corroboration_watch",
    "claim_conflict_corroboration_pass",
    "claim_conflict_dependency_block",
    "claim_conflict_dependency_pending",
    "claim_conflict_dependency_clear",
    "claim_conflict_resolution_block",
    "claim_conflict_resolution_watch",
    "claim_conflict_resolution_pass",
    "claim_conflict_empty",
)
_BLOCK_REASON_CODES = frozenset(
    (
        "claim_conflict_authority_block",
        "claim_conflict_freshness_block",
        "claim_conflict_corroboration_block",
        "claim_conflict_dependency_block",
    ),
)
_WATCH_REASON_CODES = frozenset(
    (
        "claim_conflict_authority_watch",
        "claim_conflict_freshness_watch",
        "claim_conflict_corroboration_watch",
        "claim_conflict_dependency_pending",
    ),
)
_UNSAFE_PUBLIC_KEY_TOKENS = frozenset(
    (
        "account",
        "authentication",
        "candidate",
        "credential",
        "database",
        "db",
        "dsn",
        "live",
        "market",
        "network",
        "order",
        "password",
        "private",
        "question",
        "raw",
        "recommend",
        "recommendation",
        "secret",
        "sizing",
        "slug",
        "source_text",
        "source_url",
        "table",
        "table_name",
        "token",
        "trade",
        "url",
        "wallet",
    ),
)
_UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "://",
    "?",
    "account",
    "authentication",
    "candidate",
    "credential",
    "database",
    "dsn",
    "live_trading",
    "market_id",
    "market slug",
    "market_slug",
    "order",
    "password",
    "private_key",
    "question",
    "raw",
    "recommend",
    "sizing",
    "slug",
    "source text",
    "source_text",
    "source url",
    "source_url",
    "table_name",
    "token",
    "trade",
    "wallet",
)


@dataclass(frozen=True)
class ResearchSourceClaimConflictResolutionConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_CLAIM_CONFLICT_RESOLUTION_REPORT_CONFIG_VERSION
    )
    min_pass_authority_score: Decimal = Decimal("0.800000")
    min_watch_authority_score: Decimal = Decimal("0.300000")
    max_pass_freshness_lag_seconds: Decimal = Decimal("3600.000000")
    max_watch_freshness_lag_seconds: Decimal = Decimal("86400.000000")
    min_pass_corroboration_count: Decimal = Decimal("3.000000")
    min_watch_corroboration_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimConflictResolutionConfig:
            raise TypeError(
                "ResearchSourceClaimConflictResolutionConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceClaimConflictResolutionConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CLAIM_CONFLICT_RESOLUTION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("min_pass_authority_score", "min_watch_authority_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_authority_score > self.min_pass_authority_score:
            raise ValueError(
                "min_watch_authority_score must not exceed min_pass_authority_score",
            )
        for field_name in (
            "max_pass_freshness_lag_seconds",
            "max_watch_freshness_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_pass_freshness_lag_seconds > self.max_watch_freshness_lag_seconds:
            raise ValueError(
                "max_pass_freshness_lag_seconds must not exceed "
                "max_watch_freshness_lag_seconds",
            )
        for field_name in (
            "min_pass_corroboration_count",
            "min_watch_corroboration_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_corroboration_count > self.min_pass_corroboration_count:
            raise ValueError(
                "min_watch_corroboration_count must not exceed "
                "min_pass_corroboration_count",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceClaimConflictResolutionInput:
    claim_ref: str
    authority_tier: str
    freshness_lag_seconds: Decimal
    corroboration_count: Decimal
    resolution_dependency: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimConflictResolutionInput:
            raise TypeError(
                "ResearchSourceClaimConflictResolutionInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceClaimConflictResolutionInput, "input")
        _require_public_identifier("claim_ref", self.claim_ref)
        _require_authority_tier("authority_tier", self.authority_tier)
        object.__setattr__(
            self,
            "freshness_lag_seconds",
            _require_nonnegative_decimal(
                "freshness_lag_seconds",
                self.freshness_lag_seconds,
            ),
        )
        object.__setattr__(
            self,
            "corroboration_count",
            _require_nonnegative_decimal("corroboration_count", self.corroboration_count),
        )
        _require_resolution_dependency(
            "resolution_dependency",
            self.resolution_dependency,
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchSourceClaimConflictResolutionRow:
    claim_ref: str
    authority_tier: str
    authority_score: Decimal
    freshness_lag_seconds: Decimal
    freshness_score: Decimal
    corroboration_count: Decimal
    corroboration_score: Decimal
    resolution_dependency: str
    dependency_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimConflictResolutionRow:
            raise TypeError(
                "ResearchSourceClaimConflictResolutionRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceClaimConflictResolutionRow, "row")
        _require_public_identifier("claim_ref", self.claim_ref)
        _require_authority_tier("authority_tier", self.authority_tier)
        for field_name in (
            "authority_score",
            "freshness_score",
            "corroboration_score",
            "dependency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.authority_score != _authority_score(self.authority_tier):
            raise ValueError("authority_score must match authority_tier")
        object.__setattr__(
            self,
            "freshness_lag_seconds",
            _require_nonnegative_decimal(
                "freshness_lag_seconds",
                self.freshness_lag_seconds,
            ),
        )
        object.__setattr__(
            self,
            "corroboration_count",
            _require_nonnegative_decimal("corroboration_count", self.corroboration_count),
        )
        _require_resolution_dependency(
            "resolution_dependency",
            self.resolution_dependency,
        )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceClaimConflictResolutionReport:
    generated_at: datetime
    config_version: str
    status: str
    triage_next_step: str
    conflict_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_authority_score: Decimal
    average_freshness_score: Decimal
    average_corroboration_score: Decimal
    average_dependency_score: Decimal
    rows: tuple[ResearchSourceClaimConflictResolutionRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimConflictResolutionReport:
            raise TypeError(
                "ResearchSourceClaimConflictResolutionReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceClaimConflictResolutionReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CLAIM_CONFLICT_RESOLUTION_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        _require_triage_next_step(self.status, self.triage_next_step)
        for field_name in ("conflict_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_authority_score",
            "average_freshness_score",
            "average_corroboration_score",
            "average_dependency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def public_payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("public_payload must be a dict")
        validate_research_source_claim_conflict_resolution_public_payload(payload)
        return payload

    @property
    def payload(self) -> dict[str, object]:
        return self.public_payload


def build_research_source_claim_conflict_resolution_report(
    inputs: Sequence[ResearchSourceClaimConflictResolutionInput],
    *,
    generated_at: datetime,
    config: ResearchSourceClaimConflictResolutionConfig | None = None,
) -> ResearchSourceClaimConflictResolutionReport:
    """Build a deterministic report-only conflict resolution triage."""

    if config is None:
        config = ResearchSourceClaimConflictResolutionConfig()
    if type(config) is not ResearchSourceClaimConflictResolutionConfig:
        raise ValueError(
            "config must be a ResearchSourceClaimConflictResolutionConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(inputs)
    rows = tuple(_row_from_input(item, config) for item in normalized)
    status = _report_status(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": status,
        "triage_next_step": _triage_next_step(status),
        "conflict_count": _decimal_count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_authority_score": _average(tuple(row.authority_score for row in rows)),
        "average_freshness_score": _average(tuple(row.freshness_score for row in rows)),
        "average_corroboration_score": _average(
            tuple(row.corroboration_score for row in rows),
        ),
        "average_dependency_score": _average(tuple(row.dependency_score for row in rows)),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceClaimConflictResolutionReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_claim_conflict_resolution_report_public_payload(
    report: ResearchSourceClaimConflictResolutionReport,
) -> dict[str, object]:
    if type(report) is not ResearchSourceClaimConflictResolutionReport:
        raise ValueError(
            "report must be a ResearchSourceClaimConflictResolutionReport",
        )
    _require_hard_flags("report", report)
    return report.public_payload


def validate_research_source_claim_conflict_resolution_public_payload(
    payload: dict[str, object],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload(
        "public payload",
        payload,
        allow_json_containers=True,
    )
    _reject_public_numerics(payload)
    _require_hard_flags("public payload", _DictFlags(payload))
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    expected_digest = _digest_payload(unsigned_payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")


def _row_from_input(
    item: ResearchSourceClaimConflictResolutionInput,
    config: ResearchSourceClaimConflictResolutionConfig,
) -> ResearchSourceClaimConflictResolutionRow:
    authority_score = _authority_score(item.authority_tier)
    freshness_score = _freshness_score(
        item.freshness_lag_seconds,
        config.max_watch_freshness_lag_seconds,
    )
    corroboration_score = _corroboration_score(
        item.corroboration_count,
        config.min_pass_corroboration_count,
    )
    dependency_score = _dependency_score(item.resolution_dependency)
    status = _row_status(
        authority_score=authority_score,
        freshness_lag_seconds=item.freshness_lag_seconds,
        corroboration_count=item.corroboration_count,
        resolution_dependency=item.resolution_dependency,
        config=config,
    )
    return ResearchSourceClaimConflictResolutionRow(
        claim_ref=item.claim_ref,
        authority_tier=item.authority_tier,
        authority_score=authority_score,
        freshness_lag_seconds=item.freshness_lag_seconds,
        freshness_score=freshness_score,
        corroboration_count=item.corroboration_count,
        corroboration_score=corroboration_score,
        resolution_dependency=item.resolution_dependency,
        dependency_score=dependency_score,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            authority_score=authority_score,
            freshness_lag_seconds=item.freshness_lag_seconds,
            corroboration_count=item.corroboration_count,
            resolution_dependency=item.resolution_dependency,
            config=config,
        ),
    )


def _row_status(
    *,
    authority_score: Decimal,
    freshness_lag_seconds: Decimal,
    corroboration_count: Decimal,
    resolution_dependency: str,
    config: ResearchSourceClaimConflictResolutionConfig,
) -> str:
    if authority_score < config.min_watch_authority_score:
        return "block"
    if freshness_lag_seconds > config.max_watch_freshness_lag_seconds:
        return "block"
    if corroboration_count < config.min_watch_corroboration_count:
        return "block"
    if resolution_dependency == "blocked":
        return "block"
    if (
        authority_score >= config.min_pass_authority_score
        and freshness_lag_seconds <= config.max_pass_freshness_lag_seconds
        and corroboration_count >= config.min_pass_corroboration_count
        and resolution_dependency == "none"
    ):
        return "pass"
    return "watch"


def _row_reason_codes(
    *,
    status: str,
    authority_score: Decimal,
    freshness_lag_seconds: Decimal,
    corroboration_count: Decimal,
    resolution_dependency: str,
    config: ResearchSourceClaimConflictResolutionConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if authority_score < config.min_watch_authority_score:
        reason_codes.append("claim_conflict_authority_block")
    elif authority_score < config.min_pass_authority_score:
        reason_codes.append("claim_conflict_authority_watch")
    else:
        reason_codes.append("claim_conflict_authority_pass")
    if freshness_lag_seconds > config.max_watch_freshness_lag_seconds:
        reason_codes.append("claim_conflict_freshness_block")
    elif freshness_lag_seconds > config.max_pass_freshness_lag_seconds:
        reason_codes.append("claim_conflict_freshness_watch")
    else:
        reason_codes.append("claim_conflict_freshness_pass")
    if corroboration_count < config.min_watch_corroboration_count:
        reason_codes.append("claim_conflict_corroboration_block")
    elif corroboration_count < config.min_pass_corroboration_count:
        reason_codes.append("claim_conflict_corroboration_watch")
    else:
        reason_codes.append("claim_conflict_corroboration_pass")
    if resolution_dependency == "blocked":
        reason_codes.append("claim_conflict_dependency_block")
    elif resolution_dependency == "pending":
        reason_codes.append("claim_conflict_dependency_pending")
    else:
        reason_codes.append("claim_conflict_dependency_clear")
    if status == "block":
        reason_codes.append("claim_conflict_resolution_block")
    elif status == "watch":
        reason_codes.append("claim_conflict_resolution_watch")
    else:
        reason_codes.append("claim_conflict_resolution_pass")
    return _normalize_reason_codes(reason_codes)


def _report_status(
    rows: tuple[ResearchSourceClaimConflictResolutionRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _triage_next_step(status: str) -> str:
    if status == "pass":
        return "allow_claim_conflict_resolution_analyst_review"
    if status == "watch":
        return "watch_claim_conflict_resolution_analyst_review"
    if status == "block":
        return "block_claim_conflict_resolution_analyst_review"
    raise ValueError("status must be pass, watch, or block")


def _report_reason_codes(
    rows: tuple[ResearchSourceClaimConflictResolutionRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("claim_conflict_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(reason_codes)


def _normalize_inputs(
    inputs: Sequence[ResearchSourceClaimConflictResolutionInput],
) -> tuple[ResearchSourceClaimConflictResolutionInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Sequence):
        raise ValueError("inputs must be a sequence")
    normalized: list[ResearchSourceClaimConflictResolutionInput] = []
    seen: set[str] = set()
    for item in inputs:
        if type(item) is not ResearchSourceClaimConflictResolutionInput:
            raise ValueError(
                "inputs must contain ResearchSourceClaimConflictResolutionInput",
            )
        _require_hard_flags("input", item)
        if item.claim_ref in seen:
            raise ValueError("claim_ref values must be unique")
        seen.add(item.claim_ref)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.claim_ref))


def _normalize_rows(
    rows: Sequence[ResearchSourceClaimConflictResolutionRow],
) -> tuple[ResearchSourceClaimConflictResolutionRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchSourceClaimConflictResolutionRow] = []
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceClaimConflictResolutionRow:
            raise ValueError("rows must contain ResearchSourceClaimConflictResolutionRow")
        _require_hard_flags("row", row)
        if row.claim_ref in seen:
            raise ValueError("row claim_ref values must be unique")
        seen.add(row.claim_ref)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.claim_ref))


def _validate_row_consistency(row: ResearchSourceClaimConflictResolutionRow) -> None:
    if row.status == "pass":
        if "claim_conflict_resolution_pass" not in row.reason_codes:
            raise ValueError("pass rows must include resolution pass reason")
        for reason_code in (
            "claim_conflict_authority_pass",
            "claim_conflict_freshness_pass",
            "claim_conflict_corroboration_pass",
            "claim_conflict_dependency_clear",
        ):
            if reason_code not in row.reason_codes:
                raise ValueError("pass rows must include all pass reasons")
        if any(reason_code in row.reason_codes for reason_code in _BLOCK_REASON_CODES):
            raise ValueError("pass rows must not include block reasons")
        if any(reason_code in row.reason_codes for reason_code in _WATCH_REASON_CODES):
            raise ValueError("pass rows must not include watch reasons")
        if row.resolution_dependency != "none":
            raise ValueError("pass rows must have clear dependency")
    elif row.status == "watch":
        if "claim_conflict_resolution_watch" not in row.reason_codes:
            raise ValueError("watch rows must include resolution watch reason")
        if any(reason_code in row.reason_codes for reason_code in _BLOCK_REASON_CODES):
            raise ValueError("watch rows must not include block reasons")
    elif "claim_conflict_resolution_block" not in row.reason_codes:
        raise ValueError("block rows must include resolution block reason")
    elif not any(reason_code in row.reason_codes for reason_code in _BLOCK_REASON_CODES):
        raise ValueError("block rows must include at least one block reason")


def _validate_report_consistency(
    report: ResearchSourceClaimConflictResolutionReport,
) -> None:
    rows = report.rows
    if report.conflict_count != _decimal_count(len(rows)):
        raise ValueError("conflict_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_authority_score != _average(tuple(row.authority_score for row in rows)):
        raise ValueError("average_authority_score must match rows")
    if report.average_freshness_score != _average(tuple(row.freshness_score for row in rows)):
        raise ValueError("average_freshness_score must match rows")
    if report.average_corroboration_score != _average(
        tuple(row.corroboration_score for row in rows),
    ):
        raise ValueError("average_corroboration_score must match rows")
    if report.average_dependency_score != _average(tuple(row.dependency_score for row in rows)):
        raise ValueError("average_dependency_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.triage_next_step != _triage_next_step(report.status):
        raise ValueError("triage_next_step must match status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _status_count(
    rows: tuple[ResearchSourceClaimConflictResolutionRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _authority_score(authority_tier: str) -> Decimal:
    return _AUTHORITY_TIER_SCORES[authority_tier]


def _freshness_score(
    freshness_lag_seconds: Decimal,
    max_watch_freshness_lag_seconds: Decimal,
) -> Decimal:
    if freshness_lag_seconds >= max_watch_freshness_lag_seconds:
        return _ZERO
    return _ratio(
        max_watch_freshness_lag_seconds - freshness_lag_seconds,
        max_watch_freshness_lag_seconds,
    )


def _corroboration_score(
    corroboration_count: Decimal,
    min_pass_corroboration_count: Decimal,
) -> Decimal:
    return _clamp_ratio(_ratio(corroboration_count, min_pass_corroboration_count))


def _dependency_score(resolution_dependency: str) -> Decimal:
    if resolution_dependency == "none":
        return _ONE
    if resolution_dependency == "pending":
        return Decimal("0.500000")
    if resolution_dependency == "blocked":
        return _ZERO
    raise ValueError("resolution_dependency must be supported")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _HARD_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_authority_tier(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _AUTHORITY_TIERS:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_resolution_dependency(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _RESOLUTION_DEPENDENCIES:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_triage_next_step(status: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError("triage_next_step must be a string")
    if value != _triage_next_step(status):
        raise ValueError("triage_next_step must match status")
    _reject_unsafe_public_string("triage_next_step", value)
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
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


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


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT, rounding=ROUND_HALF_UP)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext() as context:
        context.rounding = ROUND_HALF_UP
        return (sum(values, _ZERO) / Decimal(len(values))).quantize(_QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext() as context:
        context.rounding = ROUND_HALF_UP
        return (numerator / denominator).quantize(_QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < _ZERO:
        return _ZERO
    if value > _ONE:
        return _ONE
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _seconds_between(end_at: datetime, start_at: datetime) -> Decimal:
    delta = end_at - start_at
    seconds = (
        Decimal(delta.days) * _SECONDS_PER_DAY
        + Decimal(delta.seconds).quantize(_QUANT)
        + (Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND)
    )
    return seconds.quantize(_QUANT, rounding=ROUND_HALF_UP)


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
    report: ResearchSourceClaimConflictResolutionReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    return _digest_payload(payload)


def _digest_payload(payload: Mapping[str, object]) -> str:
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
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}.{index}",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)


def _reject_unsafe_public_key(key: str, path: str) -> None:
    if type(key) is not str:
        raise ValueError("public payload keys must be strings")
    if key in _HARD_FLAG_FIELDS:
        return
    lowered = key.lower()
    tokens = tuple(token for token in re.split(r"[^a-z0-9]+", lowered) if token)
    if any(token in _UNSAFE_PUBLIC_KEY_TOKENS for token in tokens):
        raise ValueError(f"unsafe public payload field at {path}: {key}")
    if any(fragment in lowered for fragment in ("source_text", "source_url")):
        raise ValueError(f"unsafe public payload field at {path}: {key}")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"unsafe public value for {field_name}")


def _reject_public_numerics(value: object) -> None:
    if type(value) is int or isinstance(value, float) or isinstance(value, Decimal):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


@dataclass(frozen=True)
class _DictFlags:
    value: Mapping[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_CLAIM_CONFLICT_RESOLUTION_REPORT_CONFIG_VERSION",
    "ResearchSourceClaimConflictResolutionConfig",
    "ResearchSourceClaimConflictResolutionInput",
    "ResearchSourceClaimConflictResolutionRow",
    "ResearchSourceClaimConflictResolutionReport",
    "build_research_source_claim_conflict_resolution_report",
    "research_source_claim_conflict_resolution_report_public_payload",
    "validate_research_source_claim_conflict_resolution_public_payload",
)
