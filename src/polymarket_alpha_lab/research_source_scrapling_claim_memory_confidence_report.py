"""Pure report-only Scrapling claim memory confidence diagnostics."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Iterable, Sequence


DEFAULT_RESEARCH_SOURCE_SCRAPLING_CLAIM_MEMORY_CONFIDENCE_CONFIG_VERSION = (
    "research-source-scrapling-claim-memory-confidence-report-v1"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_STATUS_VALUES = frozenset((PASS_STATUS, WATCH_STATUS, BLOCK_STATUS))
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_DECIMAL_TEXT_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")
_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_PUBLIC_REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "status",
        "observation_count",
        "pass_count",
        "watch_count",
        "block_count",
        "low_memory_count",
        "low_confidence_count",
        "stale_memory_count",
        "sparse_memory_evidence_count",
        "sparse_confidence_evidence_count",
        "max_claim_age_seconds",
        "min_memory_score",
        "min_confidence_score",
        "rows",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_PUBLIC_ROW_PAYLOAD_KEYS = frozenset(
    (
        "row_label",
        "observed_at",
        "memory_score",
        "confidence_score",
        "claim_age_seconds",
        "memory_evidence_count",
        "confidence_evidence_count",
        "claim_revision_count",
        "memory_confidence_floor_score",
        "watch_signal_count",
        "low_memory",
        "low_confidence",
        "stale_memory",
        "sparse_memory_evidence",
        "sparse_confidence_evidence",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_PUBLIC_REPORT_WHOLE_DECIMAL_FIELDS = frozenset(
    (
        "observation_count",
        "pass_count",
        "watch_count",
        "block_count",
        "low_memory_count",
        "low_confidence_count",
        "stale_memory_count",
        "sparse_memory_evidence_count",
        "sparse_confidence_evidence_count",
        "max_claim_age_seconds",
    ),
)
_PUBLIC_REPORT_OPTIONAL_RATIO_DECIMAL_FIELDS = frozenset(
    ("min_memory_score", "min_confidence_score"),
)
_PUBLIC_ROW_RATIO_DECIMAL_FIELDS = frozenset(
    ("memory_score", "confidence_score", "memory_confidence_floor_score"),
)
_PUBLIC_ROW_WHOLE_DECIMAL_FIELDS = frozenset(
    (
        "claim_age_seconds",
        "memory_evidence_count",
        "confidence_evidence_count",
        "claim_revision_count",
        "watch_signal_count",
    ),
)
_PUBLIC_ROW_BOOL_FIELDS = frozenset(
    (
        "low_memory",
        "low_confidence",
        "stale_memory",
        "sparse_memory_evidence",
        "sparse_confidence_evidence",
    ),
)
_UNSAFE_KEY_FRAGMENTS = (
    "raw",
    "candidate",
    "market_id",
    "market_slug",
    "slug",
    "question",
    "source_url",
    "source_text",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "private",
    "auth",
    "wallet",
    "network",
    "database",
    "order",
    "buy",
    "sell",
    "trade",
    "position",
    "recommend",
    "sizing",
    "live",
)
_UNSAFE_VALUE_FRAGMENTS = (
    "://",
    "www.",
    "raw-candidate",
    "candidate_id",
    "market_id",
    "market_slug",
    "market-slug",
    "question?",
    "dsn",
    "postgres://",
    "wallet",
    "database",
    "order",
    "token",
    "private",
)
_REASON_CODE_SEQUENCE = (
    "low_memory_score_watch",
    "low_memory_score_block",
    "low_confidence_score_watch",
    "low_confidence_score_block",
    "stale_claim_memory_watch",
    "stale_claim_memory_block",
    "sparse_memory_evidence_watch",
    "sparse_confidence_evidence_watch",
    "claim_memory_confidence_watch",
    "claim_memory_confidence_block",
    "claim_memory_confidence_pass",
)


@dataclass(frozen=True)
class ResearchSourceScraplingClaimMemoryConfidenceConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_SCRAPLING_CLAIM_MEMORY_CONFIDENCE_CONFIG_VERSION
    )
    watch_memory_score_floor: Decimal = Decimal("0.650000")
    block_memory_score_floor: Decimal = Decimal("0.400000")
    watch_confidence_score_floor: Decimal = Decimal("0.700000")
    block_confidence_score_floor: Decimal = Decimal("0.450000")
    watch_claim_age_seconds: Decimal = Decimal("21600.000000")
    block_claim_age_seconds: Decimal = Decimal("86400.000000")
    min_memory_evidence_count: Decimal = Decimal("2.000000")
    min_confidence_evidence_count: Decimal = Decimal("3.000000")
    block_watch_signal_count: Decimal = Decimal("3.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingClaimMemoryConfidenceConfig:
            raise TypeError(
                "ResearchSourceScraplingClaimMemoryConfidenceConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScraplingClaimMemoryConfidenceConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchSourceScraplingClaimMemoryConfidenceConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPLING_CLAIM_MEMORY_CONFIDENCE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_memory_score_floor",
            "block_memory_score_floor",
            "watch_confidence_score_floor",
            "block_confidence_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_claim_age_seconds",
            "block_claim_age_seconds",
            "min_memory_evidence_count",
            "min_confidence_evidence_count",
            "block_watch_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "block_memory_score_floor",
            self.watch_memory_score_floor,
            self.block_memory_score_floor,
        )
        _require_floor_pair(
            "block_confidence_score_floor",
            self.watch_confidence_score_floor,
            self.block_confidence_score_floor,
        )
        _require_ceiling_pair(
            "block_claim_age_seconds",
            self.watch_claim_age_seconds,
            self.block_claim_age_seconds,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceScraplingClaimMemoryConfidenceObservation:
    observed_at: datetime
    memory_score: Decimal
    confidence_score: Decimal
    claim_age_seconds: Decimal
    memory_evidence_count: Decimal
    confidence_evidence_count: Decimal
    claim_revision_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingClaimMemoryConfidenceObservation:
            raise TypeError(
                "ResearchSourceScraplingClaimMemoryConfidenceObservation "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScraplingClaimMemoryConfidenceObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchSourceScraplingClaimMemoryConfidenceObservation",
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("memory_score", "confidence_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "claim_age_seconds",
            "memory_evidence_count",
            "confidence_evidence_count",
            "claim_revision_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchSourceScraplingClaimMemoryConfidenceRow:
    row_label: str
    observed_at: datetime
    memory_score: Decimal
    confidence_score: Decimal
    claim_age_seconds: Decimal
    memory_evidence_count: Decimal
    confidence_evidence_count: Decimal
    claim_revision_count: Decimal
    memory_confidence_floor_score: Decimal
    watch_signal_count: Decimal
    low_memory: bool
    low_confidence: bool
    stale_memory: bool
    sparse_memory_evidence: bool
    sparse_confidence_evidence: bool
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingClaimMemoryConfidenceRow:
            raise TypeError(
                "ResearchSourceScraplingClaimMemoryConfidenceRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScraplingClaimMemoryConfidenceRow:
            raise ValueError(
                "row must be exactly ResearchSourceScraplingClaimMemoryConfidenceRow",
            )
        _require_public_identifier("row_label", self.row_label)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "memory_score",
            "confidence_score",
            "memory_confidence_floor_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "claim_age_seconds",
            "memory_evidence_count",
            "confidence_evidence_count",
            "claim_revision_count",
            "watch_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "low_memory",
            "low_confidence",
            "stale_memory",
            "sparse_memory_evidence",
            "sparse_confidence_evidence",
        ):
            _require_bool(field_name, getattr(self, field_name))
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceScraplingClaimMemoryConfidenceReport:
    generated_at: datetime
    config_version: str
    status: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    low_memory_count: Decimal
    low_confidence_count: Decimal
    stale_memory_count: Decimal
    sparse_memory_evidence_count: Decimal
    sparse_confidence_evidence_count: Decimal
    max_claim_age_seconds: Decimal
    min_memory_score: Decimal | None
    min_confidence_score: Decimal | None
    rows: tuple[ResearchSourceScraplingClaimMemoryConfidenceRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingClaimMemoryConfidenceReport:
            raise TypeError(
                "ResearchSourceScraplingClaimMemoryConfidenceReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScraplingClaimMemoryConfidenceReport:
            raise ValueError(
                "report must be exactly ResearchSourceScraplingClaimMemoryConfidenceReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPLING_CLAIM_MEMORY_CONFIDENCE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "low_memory_count",
            "low_confidence_count",
            "stale_memory_count",
            "sparse_memory_evidence_count",
            "sparse_confidence_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_claim_age_seconds",
            _require_nonnegative_whole_decimal(
                "max_claim_age_seconds",
                self.max_claim_age_seconds,
            ),
        )
        for field_name in ("min_memory_score", "min_confidence_score"):
            object.__setattr__(
                self,
                field_name,
                _require_optional_ratio_decimal(field_name, getattr(self, field_name)),
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
    def payload(self) -> dict[str, Any]:
        return research_source_scrapling_claim_memory_confidence_report_payload(self)


def build_research_source_scrapling_claim_memory_confidence_report(
    observations: Iterable[ResearchSourceScraplingClaimMemoryConfidenceObservation],
    *,
    generated_at: datetime,
    config: ResearchSourceScraplingClaimMemoryConfidenceConfig | None = None,
) -> ResearchSourceScraplingClaimMemoryConfidenceReport:
    """Build a deterministic local report-only claim memory confidence diagnostic."""

    if config is None:
        config = ResearchSourceScraplingClaimMemoryConfidenceConfig()
    if type(config) is not ResearchSourceScraplingClaimMemoryConfidenceConfig:
        raise ValueError(
            "config must be a ResearchSourceScraplingClaimMemoryConfidenceConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    for item in normalized:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = _build_rows(normalized, config)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "observation_count": _count_decimal(len(rows)),
        "pass_count": _count_decimal(_status_count(rows, PASS_STATUS)),
        "watch_count": _count_decimal(_status_count(rows, WATCH_STATUS)),
        "block_count": _count_decimal(_status_count(rows, BLOCK_STATUS)),
        "low_memory_count": _flag_total(rows, "low_memory"),
        "low_confidence_count": _flag_total(rows, "low_confidence"),
        "stale_memory_count": _flag_total(rows, "stale_memory"),
        "sparse_memory_evidence_count": _flag_total(rows, "sparse_memory_evidence"),
        "sparse_confidence_evidence_count": _flag_total(
            rows,
            "sparse_confidence_evidence",
        ),
        "max_claim_age_seconds": _max_decimal(row.claim_age_seconds for row in rows),
        "min_memory_score": _min_optional_decimal(row.memory_score for row in rows),
        "min_confidence_score": _min_optional_decimal(
            row.confidence_score for row in rows
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceScraplingClaimMemoryConfidenceReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_scrapling_claim_memory_confidence_report_payload(
    report: ResearchSourceScraplingClaimMemoryConfidenceReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSourceScraplingClaimMemoryConfidenceReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchSourceScraplingClaimMemoryConfidenceReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_source_scrapling_claim_memory_confidence_public_payload(payload)
    return payload


def research_source_scrapling_claim_memory_confidence_report_digest(
    report: ResearchSourceScraplingClaimMemoryConfidenceReport,
) -> str:
    if type(report) is not ResearchSourceScraplingClaimMemoryConfidenceReport:
        raise ValueError(
            "report must be a ResearchSourceScraplingClaimMemoryConfidenceReport",
        )
    _require_hard_flags("report", report)
    digest = _report_digest_from_values(_report_values_without_digest(report))
    if digest != report.derived_validation_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return digest


def validate_research_source_scrapling_claim_memory_confidence_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_public_numerics(payload)
    _reject_unsafe_public_payload("public payload", payload, allow_json_containers=True)
    _validate_public_payload_shape(payload)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if digest != _report_digest_from_values(unsigned_payload):
        raise ValueError("derived_validation_digest does not match public payload")
    _validate_public_payload_consistency(payload)


def _build_rows(
    observations: tuple[ResearchSourceScraplingClaimMemoryConfidenceObservation, ...],
    config: ResearchSourceScraplingClaimMemoryConfidenceConfig,
) -> tuple[ResearchSourceScraplingClaimMemoryConfidenceRow, ...]:
    draft_rows = tuple(_row_from_observation(observation, config) for observation in observations)
    sorted_draft_rows = tuple(sorted(draft_rows, key=_row_sort_key_without_label))
    return tuple(
        ResearchSourceScraplingClaimMemoryConfidenceRow(
            row_label=f"redacted-claim-memory-confidence-{index:06d}",
            observed_at=row.observed_at,
            memory_score=row.memory_score,
            confidence_score=row.confidence_score,
            claim_age_seconds=row.claim_age_seconds,
            memory_evidence_count=row.memory_evidence_count,
            confidence_evidence_count=row.confidence_evidence_count,
            claim_revision_count=row.claim_revision_count,
            memory_confidence_floor_score=row.memory_confidence_floor_score,
            watch_signal_count=row.watch_signal_count,
            low_memory=row.low_memory,
            low_confidence=row.low_confidence,
            stale_memory=row.stale_memory,
            sparse_memory_evidence=row.sparse_memory_evidence,
            sparse_confidence_evidence=row.sparse_confidence_evidence,
            status=row.status,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted_draft_rows, start=1)
    )


def _row_from_observation(
    observation: ResearchSourceScraplingClaimMemoryConfidenceObservation,
    config: ResearchSourceScraplingClaimMemoryConfidenceConfig,
) -> ResearchSourceScraplingClaimMemoryConfidenceRow:
    memory_level = _floor_level(
        observation.memory_score,
        config.watch_memory_score_floor,
        config.block_memory_score_floor,
    )
    confidence_level = _floor_level(
        observation.confidence_score,
        config.watch_confidence_score_floor,
        config.block_confidence_score_floor,
    )
    stale_level = _ceiling_level(
        observation.claim_age_seconds,
        config.watch_claim_age_seconds,
        config.block_claim_age_seconds,
    )
    sparse_memory_evidence = (
        observation.memory_evidence_count < config.min_memory_evidence_count
    )
    sparse_confidence_evidence = (
        observation.confidence_evidence_count < config.min_confidence_evidence_count
    )
    signal_count = _count_decimal(
        sum(
            1
            for value in (
                memory_level,
                confidence_level,
                stale_level,
                WATCH_STATUS if sparse_memory_evidence else None,
                WATCH_STATUS if sparse_confidence_evidence else None,
            )
            if value is not None
        ),
    )
    status = _row_status(
        (memory_level, confidence_level, stale_level),
        signal_count,
        config,
    )
    return ResearchSourceScraplingClaimMemoryConfidenceRow(
        row_label="redacted-claim-memory-confidence-000000",
        observed_at=observation.observed_at,
        memory_score=observation.memory_score,
        confidence_score=observation.confidence_score,
        claim_age_seconds=observation.claim_age_seconds,
        memory_evidence_count=observation.memory_evidence_count,
        confidence_evidence_count=observation.confidence_evidence_count,
        claim_revision_count=observation.claim_revision_count,
        memory_confidence_floor_score=min(
            observation.memory_score,
            observation.confidence_score,
        ),
        watch_signal_count=signal_count,
        low_memory=memory_level is not None,
        low_confidence=confidence_level is not None,
        stale_memory=stale_level is not None,
        sparse_memory_evidence=sparse_memory_evidence,
        sparse_confidence_evidence=sparse_confidence_evidence,
        status=status,
        reason_codes=_row_reason_codes(
            memory_level=memory_level,
            confidence_level=confidence_level,
            stale_level=stale_level,
            sparse_memory_evidence=sparse_memory_evidence,
            sparse_confidence_evidence=sparse_confidence_evidence,
            status=status,
        ),
    )


def _floor_level(value: Decimal, watch_floor: Decimal, block_floor: Decimal) -> str | None:
    if value <= block_floor:
        return BLOCK_STATUS
    if value < watch_floor:
        return WATCH_STATUS
    return None


def _ceiling_level(
    value: Decimal,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> str | None:
    if value >= block_threshold:
        return BLOCK_STATUS
    if value >= watch_threshold:
        return WATCH_STATUS
    return None


def _row_status(
    levels: tuple[str | None, ...],
    signal_count: Decimal,
    config: ResearchSourceScraplingClaimMemoryConfidenceConfig,
) -> str:
    if any(level == BLOCK_STATUS for level in levels):
        return BLOCK_STATUS
    if signal_count > config.block_watch_signal_count:
        return BLOCK_STATUS
    if signal_count > _ZERO:
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    *,
    memory_level: str | None,
    confidence_level: str | None,
    stale_level: str | None,
    sparse_memory_evidence: bool,
    sparse_confidence_evidence: bool,
    status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_level_code(reason_codes, "low_memory_score", memory_level)
    _append_level_code(reason_codes, "low_confidence_score", confidence_level)
    _append_level_code(reason_codes, "stale_claim_memory", stale_level)
    if sparse_memory_evidence:
        reason_codes.append("sparse_memory_evidence_watch")
    if sparse_confidence_evidence:
        reason_codes.append("sparse_confidence_evidence_watch")
    if status == BLOCK_STATUS:
        reason_codes.append("claim_memory_confidence_block")
    elif status == WATCH_STATUS:
        reason_codes.append("claim_memory_confidence_watch")
    else:
        reason_codes.append("claim_memory_confidence_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _append_level_code(
    reason_codes: list[str],
    prefix: str,
    level: str | None,
) -> None:
    if level is not None:
        reason_codes.append(f"{prefix}_{level}")


def _row_sort_key_without_label(
    row: ResearchSourceScraplingClaimMemoryConfidenceRow,
) -> tuple[object, ...]:
    return (
        _status_rank(row.status),
        -row.watch_signal_count,
        row.memory_confidence_floor_score,
        row.memory_score,
        row.confidence_score,
        -row.claim_age_seconds,
        row.memory_evidence_count,
        row.confidence_evidence_count,
        -row.claim_revision_count,
        row.observed_at,
    )


def _row_sort_key(
    row: ResearchSourceScraplingClaimMemoryConfidenceRow,
) -> tuple[object, ...]:
    return (*_row_sort_key_without_label(row), row.row_label)


def _report_status(
    rows: tuple[ResearchSourceScraplingClaimMemoryConfidenceRow, ...],
) -> str:
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[ResearchSourceScraplingClaimMemoryConfidenceRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("claim_memory_confidence_pass",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _validate_row_consistency(
    row: ResearchSourceScraplingClaimMemoryConfidenceRow,
) -> None:
    expected_signal_count = _count_decimal(
        sum(
            1
            for value in (
                row.low_memory,
                row.low_confidence,
                row.stale_memory,
                row.sparse_memory_evidence,
                row.sparse_confidence_evidence,
            )
            if value is True
        ),
    )
    if row.watch_signal_count != expected_signal_count:
        raise ValueError("watch_signal_count must match row flags")
    if row.memory_confidence_floor_score != min(row.memory_score, row.confidence_score):
        raise ValueError("memory_confidence_floor_score must match row scores")
    if row.status == PASS_STATUS and row.watch_signal_count != _ZERO:
        raise ValueError("pass rows must have no watch signals")
    if row.status in {WATCH_STATUS, BLOCK_STATUS} and row.watch_signal_count == _ZERO:
        raise ValueError("watch and block rows must have watch signals")
    if row.status == PASS_STATUS:
        expected_codes = ("claim_memory_confidence_pass",)
    else:
        if not any(code.endswith(row.status) for code in row.reason_codes):
            raise ValueError("status must match reason_codes")
        expected_codes = row.reason_codes
    if row.reason_codes != expected_codes:
        raise ValueError("reason_codes must match row status")


def _validate_report_consistency(
    report: ResearchSourceScraplingClaimMemoryConfidenceReport,
) -> None:
    if report.observation_count != _count_decimal(len(report.rows)):
        raise ValueError("observation_count must match rows")
    for field_name, status in (
        ("pass_count", PASS_STATUS),
        ("watch_count", WATCH_STATUS),
        ("block_count", BLOCK_STATUS),
    ):
        if getattr(report, field_name) != _count_decimal(_status_count(report.rows, status)):
            raise ValueError(f"{field_name} must match rows")
    for field_name, row_field in (
        ("low_memory_count", "low_memory"),
        ("low_confidence_count", "low_confidence"),
        ("stale_memory_count", "stale_memory"),
        ("sparse_memory_evidence_count", "sparse_memory_evidence"),
        ("sparse_confidence_evidence_count", "sparse_confidence_evidence"),
    ):
        if getattr(report, field_name) != _flag_total(report.rows, row_field):
            raise ValueError(f"{field_name} must match rows")
    if report.max_claim_age_seconds != _max_decimal(
        row.claim_age_seconds for row in report.rows
    ):
        raise ValueError("max_claim_age_seconds must match rows")
    if report.min_memory_score != _min_optional_decimal(
        row.memory_score for row in report.rows
    ):
        raise ValueError("min_memory_score must match rows")
    if report.min_confidence_score != _min_optional_decimal(
        row.confidence_score for row in report.rows
    ):
        raise ValueError("min_confidence_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_observations(
    observations: Iterable[ResearchSourceScraplingClaimMemoryConfidenceObservation],
) -> tuple[ResearchSourceScraplingClaimMemoryConfidenceObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    for item in normalized:
        if type(item) is not ResearchSourceScraplingClaimMemoryConfidenceObservation:
            raise ValueError(
                "observations must contain "
                "ResearchSourceScraplingClaimMemoryConfidenceObservation",
            )
    return normalized


def _normalize_rows(
    rows: Sequence[ResearchSourceScraplingClaimMemoryConfidenceRow],
) -> tuple[ResearchSourceScraplingClaimMemoryConfidenceRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchSourceScraplingClaimMemoryConfidenceRow:
            raise ValueError(
                "rows must contain ResearchSourceScraplingClaimMemoryConfidenceRow",
            )
    return tuple(sorted(normalized, key=_row_sort_key))


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
        reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in normalized
    )


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if isinstance(value, Decimal) and type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
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


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_optional_ratio_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _require_floor_pair(
    block_field_name: str,
    watch_floor: Decimal,
    block_floor: Decimal,
) -> None:
    if block_floor >= watch_floor:
        raise ValueError(f"{block_field_name} must be below the watch floor")


def _require_ceiling_pair(
    block_field_name: str,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if block_threshold <= watch_threshold:
        raise ValueError(f"{block_field_name} must exceed the watch threshold")


def _as_utc(field_name: str, value: object) -> datetime:
    if isinstance(value, datetime) and type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    return value.astimezone(UTC)


def _count_decimal(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _status_count(
    rows: tuple[ResearchSourceScraplingClaimMemoryConfidenceRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _flag_total(
    rows: tuple[ResearchSourceScraplingClaimMemoryConfidenceRow, ...],
    field_name: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if getattr(row, field_name) is True))


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return _ZERO
    return max(normalized)


def _min_optional_decimal(values: Iterable[Decimal]) -> Decimal | None:
    normalized = tuple(values)
    if not normalized:
        return None
    return min(normalized)


def _status_rank(status: str) -> int:
    return {BLOCK_STATUS: 0, WATCH_STATUS: 1, PASS_STATUS: 2}[status]


def _report_values_without_digest(
    report: ResearchSourceScraplingClaimMemoryConfidenceReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: object) -> str:
    return hashlib.sha256(
        json.dumps(
            _json_ready(values),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()


def _json_ready(value: object) -> Any:
    if isinstance(value, Decimal):
        return str(_quantize(value))
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


def _reject_public_numerics(value: object) -> None:
    if type(value) in (float, int):
        raise ValueError("public payload must serialize numerics as strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _validate_public_payload_shape(payload: dict[str, Any]) -> None:
    _require_public_payload_keys(
        "public payload",
        payload,
        _PUBLIC_REPORT_PAYLOAD_KEYS,
    )
    _require_public_payload_datetime("generated_at", payload["generated_at"])
    _require_public_identifier("config_version", payload["config_version"])
    if (
        payload["config_version"]
        != DEFAULT_RESEARCH_SOURCE_SCRAPLING_CLAIM_MEMORY_CONFIDENCE_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    _require_status("status", payload["status"])
    for field_name in _PUBLIC_REPORT_WHOLE_DECIMAL_FIELDS:
        _require_public_payload_decimal_text(
            field_name,
            payload[field_name],
            whole=True,
        )
    for field_name in _PUBLIC_REPORT_OPTIONAL_RATIO_DECIMAL_FIELDS:
        _require_public_payload_decimal_text(
            field_name,
            payload[field_name],
            optional=True,
            ratio=True,
        )
    _validate_public_payload_rows(payload["rows"])
    _validate_public_payload_reason_codes("reason_codes", payload["reason_codes"])


def _validate_public_payload_rows(value: object) -> None:
    if type(value) is not list:
        raise ValueError("rows must be a public payload list")
    for row in value:
        if type(row) is not dict:
            raise ValueError("rows must contain public payload objects")
        _require_public_payload_keys(
            "public payload row",
            row,
            _PUBLIC_ROW_PAYLOAD_KEYS,
        )
        _require_public_payload_flags("row public payload", row)
        _require_public_identifier("row_label", row["row_label"])
        _require_public_payload_datetime("observed_at", row["observed_at"])
        for field_name in _PUBLIC_ROW_RATIO_DECIMAL_FIELDS:
            _require_public_payload_decimal_text(
                field_name,
                row[field_name],
                ratio=True,
            )
        for field_name in _PUBLIC_ROW_WHOLE_DECIMAL_FIELDS:
            _require_public_payload_decimal_text(
                field_name,
                row[field_name],
                whole=True,
            )
        for field_name in _PUBLIC_ROW_BOOL_FIELDS:
            _require_bool(field_name, row[field_name])
        _require_status("status", row["status"])
        _validate_public_payload_reason_codes("row reason_codes", row["reason_codes"])


def _require_public_payload_keys(
    label: str,
    payload: dict[object, object],
    expected_keys: frozenset[str],
) -> None:
    for key in payload:
        if type(key) is not str:
            raise ValueError("public payload keys must be strings")
    keys = set(payload)
    unexpected_keys = keys - expected_keys
    if unexpected_keys:
        raise ValueError(f"unexpected {label} key")
    missing_keys = expected_keys - keys
    if missing_keys:
        raise ValueError(f"missing {label} key")


def _require_public_payload_flags(label: str, payload: dict[str, Any]) -> None:
    for field_name in _FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_payload_datetime(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    if _as_utc(field_name, parsed).isoformat() != value:
        raise ValueError(f"{field_name} must be canonical UTC ISO datetime")
    return value


def _require_public_payload_decimal_text(
    field_name: str,
    value: object,
    *,
    optional: bool = False,
    ratio: bool = False,
    whole: bool = False,
) -> Decimal | None:
    if optional and value is None:
        return None
    if type(value) is not str:
        if isinstance(value, Decimal) or type(value) in (float, int):
            raise ValueError("unsupported public payload value")
        raise ValueError(f"{field_name} must be canonical Decimal text")
    if _DECIMAL_TEXT_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be canonical Decimal text")
    try:
        parsed = _require_nonnegative_decimal(field_name, Decimal(value))
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be canonical Decimal text") from exc
    if str(parsed) != value:
        raise ValueError(f"{field_name} must be canonical Decimal text")
    if ratio and (parsed < _ZERO or parsed > _ONE):
        raise ValueError(f"{field_name} must be between zero and one")
    if whole and parsed != parsed.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return parsed


def _validate_public_payload_reason_codes(field_name: str, value: object) -> None:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a public payload list")
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    normalized = _normalize_reason_codes(tuple(value))
    if list(normalized) != value:
        raise ValueError(f"{field_name} must be canonical")


def _validate_public_payload_consistency(payload: dict[str, Any]) -> None:
    rows = tuple(_row_from_public_payload(row) for row in payload["rows"])
    ResearchSourceScraplingClaimMemoryConfidenceReport(
        generated_at=_datetime_from_public_payload(
            "generated_at",
            payload["generated_at"],
        ),
        config_version=payload["config_version"],
        status=payload["status"],
        observation_count=_public_payload_decimal(
            "observation_count",
            payload["observation_count"],
            whole=True,
        ),
        pass_count=_public_payload_decimal(
            "pass_count",
            payload["pass_count"],
            whole=True,
        ),
        watch_count=_public_payload_decimal(
            "watch_count",
            payload["watch_count"],
            whole=True,
        ),
        block_count=_public_payload_decimal(
            "block_count",
            payload["block_count"],
            whole=True,
        ),
        low_memory_count=_public_payload_decimal(
            "low_memory_count",
            payload["low_memory_count"],
            whole=True,
        ),
        low_confidence_count=_public_payload_decimal(
            "low_confidence_count",
            payload["low_confidence_count"],
            whole=True,
        ),
        stale_memory_count=_public_payload_decimal(
            "stale_memory_count",
            payload["stale_memory_count"],
            whole=True,
        ),
        sparse_memory_evidence_count=_public_payload_decimal(
            "sparse_memory_evidence_count",
            payload["sparse_memory_evidence_count"],
            whole=True,
        ),
        sparse_confidence_evidence_count=_public_payload_decimal(
            "sparse_confidence_evidence_count",
            payload["sparse_confidence_evidence_count"],
            whole=True,
        ),
        max_claim_age_seconds=_public_payload_decimal(
            "max_claim_age_seconds",
            payload["max_claim_age_seconds"],
            whole=True,
        ),
        min_memory_score=_optional_public_payload_decimal(
            "min_memory_score",
            payload["min_memory_score"],
        ),
        min_confidence_score=_optional_public_payload_decimal(
            "min_confidence_score",
            payload["min_confidence_score"],
        ),
        rows=rows,
        reason_codes=tuple(payload["reason_codes"]),
        derived_validation_digest=payload["derived_validation_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _row_from_public_payload(
    row: dict[str, Any],
) -> ResearchSourceScraplingClaimMemoryConfidenceRow:
    return ResearchSourceScraplingClaimMemoryConfidenceRow(
        row_label=row["row_label"],
        observed_at=_datetime_from_public_payload("observed_at", row["observed_at"]),
        memory_score=_public_payload_decimal(
            "memory_score",
            row["memory_score"],
            ratio=True,
        ),
        confidence_score=_public_payload_decimal(
            "confidence_score",
            row["confidence_score"],
            ratio=True,
        ),
        claim_age_seconds=_public_payload_decimal(
            "claim_age_seconds",
            row["claim_age_seconds"],
            whole=True,
        ),
        memory_evidence_count=_public_payload_decimal(
            "memory_evidence_count",
            row["memory_evidence_count"],
            whole=True,
        ),
        confidence_evidence_count=_public_payload_decimal(
            "confidence_evidence_count",
            row["confidence_evidence_count"],
            whole=True,
        ),
        claim_revision_count=_public_payload_decimal(
            "claim_revision_count",
            row["claim_revision_count"],
            whole=True,
        ),
        memory_confidence_floor_score=_public_payload_decimal(
            "memory_confidence_floor_score",
            row["memory_confidence_floor_score"],
            ratio=True,
        ),
        watch_signal_count=_public_payload_decimal(
            "watch_signal_count",
            row["watch_signal_count"],
            whole=True,
        ),
        low_memory=row["low_memory"],
        low_confidence=row["low_confidence"],
        stale_memory=row["stale_memory"],
        sparse_memory_evidence=row["sparse_memory_evidence"],
        sparse_confidence_evidence=row["sparse_confidence_evidence"],
        status=row["status"],
        reason_codes=tuple(row["reason_codes"]),
        paper_only=row["paper_only"],
        report_only=row["report_only"],
        readonly=row["readonly"],
    )


def _datetime_from_public_payload(field_name: str, value: object) -> datetime:
    _require_public_payload_datetime(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    return datetime.fromisoformat(value)


def _public_payload_decimal(
    field_name: str,
    value: object,
    *,
    ratio: bool = False,
    whole: bool = False,
) -> Decimal:
    parsed = _require_public_payload_decimal_text(
        field_name,
        value,
        ratio=ratio,
        whole=whole,
    )
    if parsed is None:
        raise ValueError(f"{field_name} must be canonical Decimal text")
    return parsed


def _optional_public_payload_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    return _require_public_payload_decimal_text(
        field_name,
        value,
        optional=True,
        ratio=True,
    )


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
    path: str = "",
) -> None:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=True,
            path=path,
        )
        return
    if isinstance(value, dict):
        if not allow_json_containers:
            raise ValueError(f"{label} must not expose dict surfaces")
        for key, item in value.items():
            key_text = str(key)
            lowered_key = key_text.lower()
            if any(fragment in lowered_key for fragment in _UNSAFE_KEY_FRAGMENTS):
                raise ValueError(f"{label} contains unsafe public key: {key_text}")
            if key_text in _FLAG_FIELDS and item is not True:
                raise ValueError(f"{key_text} must be True for {label}")
            item_path = f"{path}.{key_text}" if path else key_text
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
                path=item_path,
            )
        return
    if isinstance(value, (list, tuple)):
        if not allow_json_containers:
            raise ValueError(f"{label} must not expose sequence surfaces")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
                path=f"{path}[{index}]",
            )
        return
    if isinstance(value, str):
        _reject_unsafe_public_string(path or label, value)


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_VALUE_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public value")


class _PayloadFlags:
    def __init__(self, value: dict[str, Any]) -> None:
        self.value = value

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
    "ResearchSourceScraplingClaimMemoryConfidenceConfig",
    "ResearchSourceScraplingClaimMemoryConfidenceObservation",
    "ResearchSourceScraplingClaimMemoryConfidenceRow",
    "ResearchSourceScraplingClaimMemoryConfidenceReport",
    "build_research_source_scrapling_claim_memory_confidence_report",
    "research_source_scrapling_claim_memory_confidence_report_digest",
    "research_source_scrapling_claim_memory_confidence_report_payload",
    "validate_research_source_scrapling_claim_memory_confidence_public_payload",
)
