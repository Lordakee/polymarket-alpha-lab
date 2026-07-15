"""Report-only Scrapling authority-memory scorecard.

This module only builds deterministic, readonly research summaries from already
provided observations. It performs no retrieval, persistence, execution, or
decision automation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_SOURCE_SCRAPLING_AUTHORITY_MEMORY_CONFIG_VERSION = (
    "research-source-scrapling-authority-memory-scorecard-report-v1"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=50, rounding=ROUND_HALF_UP)
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_CANONICAL_DECIMAL_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_STATUS_ORDER = {"block": 0, "watch": 1, "pass": 2}
_REASON_CODE_SEQUENCE = (
    "empty_evidence",
    "conflict_score_block",
    "authority_score_block",
    "authority_memory_score_watch",
    "authority_memory_score_pass",
)
_SENSITIVE_PUBLIC_TOKENS = frozenset(
    (
        "account",
        "api",
        "auth",
        "authentication",
        "authorization",
        "broker",
        "candidate",
        "client",
        "credential",
        "database",
        "db",
        "dsn",
        "execution",
        "httpx",
        "live",
        "market",
        "network",
        "order",
        "postgres",
        "private",
        "psycopg",
        "raw",
        "recommendation",
        "requests",
        "secret",
        "sign",
        "sizing",
        "socket",
        "source",
        "sqlalchemy",
        "supabase",
        "table",
        "text",
        "token",
        "trade",
        "trading",
        "url",
        "urllib",
        "wallet",
        "web3",
    )
)
_SENSITIVE_PUBLIC_COMPACT_FRAGMENTS = (
    "://",
    "apikey",
    "api_key",
    "candidateid",
    "candidate_id",
    "marketid",
    "market_id",
    "orderid",
    "order_id",
    "sourceurl",
    "source_url",
    "tradeid",
    "trade_id",
    "walletid",
    "wallet_id",
)
_REPORT_PUBLIC_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "status",
    "row_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_composite_score",
    "rows",
    "reason_codes",
    "public_payload",
    "validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_PUBLIC_PAYLOAD_KEYS = (
    "evidence_digest",
    "authority_family",
    "memory_class",
    "observed_at",
    "authority_score",
    "memory_score",
    "corroboration_score",
    "recency_score",
    "conflict_score",
    "composite_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_PUBLIC_PAYLOAD_ITEM_KEYS = (
    "key",
    "value",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class ResearchSourceScraplingAuthorityMemoryConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_SCRAPLING_AUTHORITY_MEMORY_CONFIG_VERSION
    min_pass_score: Decimal = Decimal("0.700000")
    max_block_conflict_score: Decimal = Decimal("0.700000")
    min_block_authority_score: Decimal = Decimal("0.300000")
    authority_weight: Decimal = Decimal("0.300000")
    memory_weight: Decimal = Decimal("0.300000")
    corroboration_weight: Decimal = Decimal("0.200000")
    recency_weight: Decimal = Decimal("0.100000")
    conflict_penalty_weight: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingAuthorityMemoryConfig:
            raise TypeError(
                "ResearchSourceScraplingAuthorityMemoryConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScraplingAuthorityMemoryConfig:
            raise ValueError(
                "config must be exactly ResearchSourceScraplingAuthorityMemoryConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPLING_AUTHORITY_MEMORY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_score",
            "max_block_conflict_score",
            "min_block_authority_score",
            "authority_weight",
            "memory_weight",
            "corroboration_weight",
            "recency_weight",
            "conflict_penalty_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceScraplingAuthorityMemoryEvidence:
    private_reference: str
    authority_family: str
    memory_class: str
    observed_at: datetime
    authority_score: Decimal
    memory_score: Decimal
    corroboration_score: Decimal
    recency_score: Decimal
    conflict_score: Decimal = _ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingAuthorityMemoryEvidence:
            raise TypeError(
                "ResearchSourceScraplingAuthorityMemoryEvidence does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScraplingAuthorityMemoryEvidence:
            raise ValueError(
                "evidence must be exactly ResearchSourceScraplingAuthorityMemoryEvidence",
            )
        _require_private_reference("private_reference", self.private_reference)
        _require_public_identifier("authority_family", self.authority_family)
        _require_public_identifier("memory_class", self.memory_class)
        _reject_sensitive_public_text("authority_family", self.authority_family)
        _reject_sensitive_public_text("memory_class", self.memory_class)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "authority_score",
            "memory_score",
            "corroboration_score",
            "recency_score",
            "conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("evidence", self)


@dataclass(frozen=True)
class ResearchSourceScraplingAuthorityMemoryPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingAuthorityMemoryPublicPayloadItem:
            raise TypeError(
                "ResearchSourceScraplingAuthorityMemoryPublicPayloadItem does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScraplingAuthorityMemoryPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchSourceScraplingAuthorityMemoryPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        _reject_sensitive_public_text("key", self.key)
        object.__setattr__(
            self,
            "value",
            _require_public_text("value", self.value),
        )
        _reject_sensitive_public_text("value", self.value)
        _require_hard_flags("public payload item", self)


@dataclass(frozen=True)
class ResearchSourceScraplingAuthorityMemoryRow:
    evidence_digest: str
    authority_family: str
    memory_class: str
    observed_at: datetime
    authority_score: Decimal
    memory_score: Decimal
    corroboration_score: Decimal
    recency_score: Decimal
    conflict_score: Decimal
    composite_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingAuthorityMemoryRow:
            raise TypeError(
                "ResearchSourceScraplingAuthorityMemoryRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScraplingAuthorityMemoryRow:
            raise ValueError("row must be exactly ResearchSourceScraplingAuthorityMemoryRow")
        _require_sha256_digest("evidence_digest", self.evidence_digest)
        _require_public_identifier("authority_family", self.authority_family)
        _require_public_identifier("memory_class", self.memory_class)
        _reject_sensitive_public_text("authority_family", self.authority_family)
        _reject_sensitive_public_text("memory_class", self.memory_class)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "authority_score",
            "memory_score",
            "corroboration_score",
            "recency_score",
            "conflict_score",
            "composite_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        if self.status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchSourceScraplingAuthorityMemoryReport:
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_composite_score: Decimal
    rows: tuple[ResearchSourceScraplingAuthorityMemoryRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchSourceScraplingAuthorityMemoryPublicPayloadItem, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingAuthorityMemoryReport:
            raise TypeError(
                "ResearchSourceScraplingAuthorityMemoryReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScraplingAuthorityMemoryReport:
            raise ValueError(
                "report must be exactly ResearchSourceScraplingAuthorityMemoryReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPLING_AUTHORITY_MEMORY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_composite_score",
            _require_probability_decimal(
                "average_composite_score",
                self.average_composite_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _require_sha256_digest("validation_digest", self.validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.validation_digest != expected_digest:
            raise ValueError("validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        validate_research_source_scrapling_authority_memory_scorecard_report_payload(
            payload,
        )
        return payload


def build_research_source_scrapling_authority_memory_scorecard_report(
    evidence: Sequence[ResearchSourceScraplingAuthorityMemoryEvidence],
    *,
    generated_at: datetime,
    config: ResearchSourceScraplingAuthorityMemoryConfig | None = None,
    public_payload: Sequence[ResearchSourceScraplingAuthorityMemoryPublicPayloadItem] = (),
) -> ResearchSourceScraplingAuthorityMemoryReport:
    """Build a deterministic, readonly Scrapling authority-memory scorecard."""

    if config is None:
        config = ResearchSourceScraplingAuthorityMemoryConfig()
    config = _normalize_config(config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_evidence = _normalize_evidence(evidence)
    for item in normalized_evidence:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(sorted((_row_from_evidence(item, config) for item in normalized_evidence), key=_row_sort_key))
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_composite_score": _average(tuple(row.composite_score for row in rows)),
        "rows": rows,
        "reason_codes": reason_codes,
        "public_payload": _normalize_public_payload(public_payload),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceScraplingAuthorityMemoryReport(
        **values,
        validation_digest=_report_digest_from_values(values),
    )


def validate_research_source_scrapling_authority_memory_scorecard_report_payload(
    payload: dict[str, object],
) -> bool:
    """Validate an exported scorecard payload against its canonical public schema."""

    _require_payload_keys(
        "report",
        payload,
        _REPORT_PUBLIC_PAYLOAD_KEYS,
    )
    rows = tuple(
        _row_from_public_payload(item)
        for item in _payload_required_list(payload, "rows")
    )
    public_payload = tuple(
        _public_payload_item_from_public_payload(item)
        for item in _payload_required_list(payload, "public_payload")
    )
    ResearchSourceScraplingAuthorityMemoryReport(
        generated_at=_datetime_from_public_payload(payload, "generated_at"),
        config_version=_payload_required_string(payload, "config_version"),
        status=_payload_required_string(payload, "status"),
        row_count=_decimal_from_public_payload(payload, "row_count"),
        pass_count=_decimal_from_public_payload(payload, "pass_count"),
        watch_count=_decimal_from_public_payload(payload, "watch_count"),
        block_count=_decimal_from_public_payload(payload, "block_count"),
        average_composite_score=_decimal_from_public_payload(
            payload,
            "average_composite_score",
        ),
        rows=rows,
        reason_codes=_reason_codes_from_public_payload(payload, "reason_codes"),
        public_payload=public_payload,
        validation_digest=_payload_required_string(payload, "validation_digest"),
        paper_only=_payload_required_true(payload, "paper_only"),
        report_only=_payload_required_true(payload, "report_only"),
        readonly=_payload_required_true(payload, "readonly"),
    )
    return True


def _row_from_evidence(
    value: ResearchSourceScraplingAuthorityMemoryEvidence,
    config: ResearchSourceScraplingAuthorityMemoryConfig,
) -> ResearchSourceScraplingAuthorityMemoryRow:
    composite_score = _composite_score(value, config)
    reason_codes = _row_reason_codes(value, composite_score, config)
    return ResearchSourceScraplingAuthorityMemoryRow(
        evidence_digest=_digest_private_reference(value.private_reference),
        authority_family=value.authority_family,
        memory_class=value.memory_class,
        observed_at=value.observed_at,
        authority_score=value.authority_score,
        memory_score=value.memory_score,
        corroboration_score=value.corroboration_score,
        recency_score=value.recency_score,
        conflict_score=value.conflict_score,
        composite_score=composite_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _composite_score(
    value: ResearchSourceScraplingAuthorityMemoryEvidence,
    config: ResearchSourceScraplingAuthorityMemoryConfig,
) -> Decimal:
    return _composite_score_from_values(
        authority_score=value.authority_score,
        memory_score=value.memory_score,
        corroboration_score=value.corroboration_score,
        recency_score=value.recency_score,
        conflict_score=value.conflict_score,
        config=config,
    )


def _composite_score_from_values(
    *,
    authority_score: Decimal,
    memory_score: Decimal,
    corroboration_score: Decimal,
    recency_score: Decimal,
    conflict_score: Decimal,
    config: ResearchSourceScraplingAuthorityMemoryConfig,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        weighted = (
            (authority_score * config.authority_weight)
            + (memory_score * config.memory_weight)
            + (corroboration_score * config.corroboration_weight)
            + (recency_score * config.recency_weight)
            - (conflict_score * config.conflict_penalty_weight)
        )
        return _clamp_probability(weighted)


def _row_reason_codes(
    value: ResearchSourceScraplingAuthorityMemoryEvidence,
    composite_score: Decimal,
    config: ResearchSourceScraplingAuthorityMemoryConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if value.conflict_score >= config.max_block_conflict_score:
        reason_codes.append("conflict_score_block")
    if value.authority_score < config.min_block_authority_score:
        reason_codes.append("authority_score_block")
    if not reason_codes:
        if composite_score < config.min_pass_score:
            reason_codes.append("authority_memory_score_watch")
        else:
            reason_codes.append("authority_memory_score_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[ResearchSourceScraplingAuthorityMemoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_evidence",)
    seen: list[str] = []
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code not in seen:
                seen.append(reason_code)
    return _normalize_reason_codes(tuple(seen))


def _report_status(rows: tuple[ResearchSourceScraplingAuthorityMemoryRow, ...]) -> str:
    if not rows:
        return "watch"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if reason_codes == ("authority_memory_score_pass",):
        return "pass"
    return "watch"


def _status_count(
    rows: tuple[ResearchSourceScraplingAuthorityMemoryRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _row_sort_key(row: ResearchSourceScraplingAuthorityMemoryRow) -> tuple[object, ...]:
    return (
        _STATUS_ORDER[row.status],
        row.evidence_digest,
        row.authority_family,
        row.memory_class,
        row.observed_at,
        row.authority_score,
        row.memory_score,
        row.corroboration_score,
        row.recency_score,
        row.conflict_score,
        row.composite_score,
        row.reason_codes,
    )


def _validate_report_consistency(report: ResearchSourceScraplingAuthorityMemoryReport) -> None:
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_composite_score != _average(tuple(row.composite_score for row in report.rows)):
        raise ValueError("average_composite_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")


def _validate_row_consistency(
    row: ResearchSourceScraplingAuthorityMemoryRow,
) -> None:
    config = ResearchSourceScraplingAuthorityMemoryConfig()
    expected_composite_score = _composite_score_from_values(
        authority_score=row.authority_score,
        memory_score=row.memory_score,
        corroboration_score=row.corroboration_score,
        recency_score=row.recency_score,
        conflict_score=row.conflict_score,
        config=config,
    )
    if row.composite_score != expected_composite_score:
        raise ValueError("composite_score must match derived score")

    expected_reason_codes: list[str] = []
    if row.conflict_score >= config.max_block_conflict_score:
        expected_reason_codes.append("conflict_score_block")
    if row.authority_score < config.min_block_authority_score:
        expected_reason_codes.append("authority_score_block")
    if not expected_reason_codes:
        if row.composite_score < config.min_pass_score:
            expected_reason_codes.append("authority_memory_score_watch")
        else:
            expected_reason_codes.append("authority_memory_score_pass")
    normalized_reason_codes = _normalize_reason_codes(tuple(expected_reason_codes))
    if row.reason_codes != normalized_reason_codes:
        raise ValueError("reason_codes must match derived score logic")
    if row.status != _status_from_reason_codes(normalized_reason_codes):
        raise ValueError("status must match derived reason_codes")


def _normalize_config(
    config: ResearchSourceScraplingAuthorityMemoryConfig,
) -> ResearchSourceScraplingAuthorityMemoryConfig:
    if type(config) is not ResearchSourceScraplingAuthorityMemoryConfig:
        raise ValueError("config must be a ResearchSourceScraplingAuthorityMemoryConfig")
    return ResearchSourceScraplingAuthorityMemoryConfig(
        config_version=config.config_version,
        min_pass_score=config.min_pass_score,
        max_block_conflict_score=config.max_block_conflict_score,
        min_block_authority_score=config.min_block_authority_score,
        authority_weight=config.authority_weight,
        memory_weight=config.memory_weight,
        corroboration_weight=config.corroboration_weight,
        recency_weight=config.recency_weight,
        conflict_penalty_weight=config.conflict_penalty_weight,
        paper_only=config.paper_only,
        report_only=config.report_only,
        readonly=config.readonly,
    )


def _normalize_evidence(
    evidence: Sequence[ResearchSourceScraplingAuthorityMemoryEvidence],
) -> tuple[ResearchSourceScraplingAuthorityMemoryEvidence, ...]:
    if isinstance(evidence, (str, bytes)) or not isinstance(evidence, Sequence):
        raise ValueError("evidence must be a sequence")
    normalized: list[ResearchSourceScraplingAuthorityMemoryEvidence] = []
    for item in evidence:
        if type(item) is not ResearchSourceScraplingAuthorityMemoryEvidence:
            raise ValueError("evidence items must be ResearchSourceScraplingAuthorityMemoryEvidence")
        normalized.append(
            ResearchSourceScraplingAuthorityMemoryEvidence(
                private_reference=item.private_reference,
                authority_family=item.authority_family,
                memory_class=item.memory_class,
                observed_at=item.observed_at,
                authority_score=item.authority_score,
                memory_score=item.memory_score,
                corroboration_score=item.corroboration_score,
                recency_score=item.recency_score,
                conflict_score=item.conflict_score,
                paper_only=item.paper_only,
                report_only=item.report_only,
                readonly=item.readonly,
            ),
        )
    return tuple(normalized)


def _normalize_rows(
    rows: Sequence[ResearchSourceScraplingAuthorityMemoryRow],
) -> tuple[ResearchSourceScraplingAuthorityMemoryRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchSourceScraplingAuthorityMemoryRow] = []
    for row in rows:
        if type(row) is not ResearchSourceScraplingAuthorityMemoryRow:
            raise ValueError("rows must contain ResearchSourceScraplingAuthorityMemoryRow")
        normalized.append(
            ResearchSourceScraplingAuthorityMemoryRow(
                evidence_digest=row.evidence_digest,
                authority_family=row.authority_family,
                memory_class=row.memory_class,
                observed_at=row.observed_at,
                authority_score=row.authority_score,
                memory_score=row.memory_score,
                corroboration_score=row.corroboration_score,
                recency_score=row.recency_score,
                conflict_score=row.conflict_score,
                composite_score=row.composite_score,
                status=row.status,
                reason_codes=row.reason_codes,
                paper_only=row.paper_only,
                report_only=row.report_only,
                readonly=row.readonly,
            ),
        )
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_public_payload(
    public_payload: Sequence[ResearchSourceScraplingAuthorityMemoryPublicPayloadItem],
) -> tuple[ResearchSourceScraplingAuthorityMemoryPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchSourceScraplingAuthorityMemoryPublicPayloadItem] = []
    seen_keys: set[str] = set()
    for item in public_payload:
        if type(item) is not ResearchSourceScraplingAuthorityMemoryPublicPayloadItem:
            raise ValueError(
                "public_payload items must be "
                "ResearchSourceScraplingAuthorityMemoryPublicPayloadItem",
            )
        normalized_item = ResearchSourceScraplingAuthorityMemoryPublicPayloadItem(
            key=item.key,
            value=item.value,
            paper_only=item.paper_only,
            report_only=item.report_only,
            readonly=item.readonly,
        )
        if normalized_item.key in seen_keys:
            raise ValueError("public_payload must not contain duplicate keys")
        seen_keys.add(normalized_item.key)
        normalized.append(normalized_item)
    return tuple(sorted(normalized, key=lambda item: item.key))


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


def _require_private_reference(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a canonical public identifier")


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical nonblank public text")
    return value


def _reject_sensitive_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    tokens = frozenset(re.findall(r"[a-z0-9]+", lowered))
    if (
        tokens.intersection(_SENSITIVE_PUBLIC_TOKENS)
        or any(
            fragment in lowered
            for fragment in _SENSITIVE_PUBLIC_COMPACT_FRAGMENTS
        )
    ):
        raise ValueError(f"{field_name} contains sensitive public payload material")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    return value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if raw != raw.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    return _quantize(raw)


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_decimal(field_name, value)
    if raw < _ZERO or raw > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return _quantize(raw)


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _clamp_probability(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        normalized = value.quantize(_QUANT, rounding=ROUND_HALF_UP)
    if normalized == _ZERO:
        return _ZERO
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _digest_private_reference(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _report_values_without_digest(
    report: ResearchSourceScraplingAuthorityMemoryReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _row_from_public_payload(
    value: object,
) -> ResearchSourceScraplingAuthorityMemoryRow:
    if type(value) is not dict:
        raise ValueError("rows must contain JSON objects")
    _require_payload_keys("row", value, _ROW_PUBLIC_PAYLOAD_KEYS)
    return ResearchSourceScraplingAuthorityMemoryRow(
        evidence_digest=_payload_required_string(value, "evidence_digest"),
        authority_family=_payload_required_string(value, "authority_family"),
        memory_class=_payload_required_string(value, "memory_class"),
        observed_at=_datetime_from_public_payload(value, "observed_at"),
        authority_score=_decimal_from_public_payload(value, "authority_score"),
        memory_score=_decimal_from_public_payload(value, "memory_score"),
        corroboration_score=_decimal_from_public_payload(
            value,
            "corroboration_score",
        ),
        recency_score=_decimal_from_public_payload(value, "recency_score"),
        conflict_score=_decimal_from_public_payload(value, "conflict_score"),
        composite_score=_decimal_from_public_payload(value, "composite_score"),
        status=_payload_required_string(value, "status"),
        reason_codes=_reason_codes_from_public_payload(value, "reason_codes"),
        paper_only=_payload_required_true(value, "paper_only"),
        report_only=_payload_required_true(value, "report_only"),
        readonly=_payload_required_true(value, "readonly"),
    )


def _public_payload_item_from_public_payload(
    value: object,
) -> ResearchSourceScraplingAuthorityMemoryPublicPayloadItem:
    if type(value) is not dict:
        raise ValueError("public_payload must contain JSON objects")
    _require_payload_keys("public payload item", value, _PUBLIC_PAYLOAD_ITEM_KEYS)
    return ResearchSourceScraplingAuthorityMemoryPublicPayloadItem(
        key=_payload_required_string(value, "key"),
        value=_payload_required_string(value, "value"),
        paper_only=_payload_required_true(value, "paper_only"),
        report_only=_payload_required_true(value, "report_only"),
        readonly=_payload_required_true(value, "readonly"),
    )


def _require_payload_keys(
    label: str,
    payload: object,
    expected_keys: tuple[str, ...],
) -> None:
    if type(payload) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    if tuple(payload) != expected_keys:
        raise ValueError(f"{label} must use canonical {label} payload schema")


def _payload_required_string(payload: Mapping[str, object], field_name: str) -> str:
    value = payload[field_name]
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_required_list(
    payload: Mapping[str, object],
    field_name: str,
) -> list[object]:
    value = payload[field_name]
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return value


def _payload_required_true(payload: Mapping[str, object], field_name: str) -> bool:
    value = payload[field_name]
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _decimal_from_public_payload(
    payload: Mapping[str, object],
    field_name: str,
) -> Decimal:
    value = _payload_required_string(payload, field_name)
    if _CANONICAL_DECIMAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return Decimal(value)


def _datetime_from_public_payload(
    payload: Mapping[str, object],
    field_name: str,
) -> datetime:
    value = _payload_required_string(payload, field_name)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _reason_codes_from_public_payload(
    payload: Mapping[str, object],
    field_name: str,
) -> tuple[str, ...]:
    values = _payload_required_list(payload, field_name)
    reason_codes: list[str] = []
    for value in values:
        if type(value) is not str:
            raise ValueError(f"{field_name} must contain strings")
        reason_codes.append(value)
    return tuple(reason_codes)


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


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_SCRAPLING_AUTHORITY_MEMORY_CONFIG_VERSION",
    "ResearchSourceScraplingAuthorityMemoryConfig",
    "ResearchSourceScraplingAuthorityMemoryEvidence",
    "ResearchSourceScraplingAuthorityMemoryPublicPayloadItem",
    "ResearchSourceScraplingAuthorityMemoryReport",
    "ResearchSourceScraplingAuthorityMemoryRow",
    "build_research_source_scrapling_authority_memory_scorecard_report",
    "validate_research_source_scrapling_authority_memory_scorecard_report_payload",
)
