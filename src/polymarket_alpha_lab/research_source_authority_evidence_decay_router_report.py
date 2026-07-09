"""Report-only authority/evidence decay router for research source signals."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import InitVar, asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_AUTHORITY_EVIDENCE_DECAY_ROUTER_CONFIG_VERSION = (
    "research-source-authority-evidence-decay-router-report-v1"
)
RESEARCH_SOURCE_AUTHORITY_EVIDENCE_DECAY_ROUTER_STATUSES = ("pass", "watch", "block")

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
_PUBLIC_KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_CANONICAL_DECIMAL_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_TERMS = (
    "candidate_id",
    "raw_candidate",
    "market_id",
    "market_slug",
    "market_question",
    "source_url",
    "source_text",
    "raw_source",
    "raw source",
    "dsn",
    "table",
    "table_name",
    "token",
    "secret",
    "password",
    "wallet",
    "order",
    "trade",
    "buy",
    "sell",
    "sizing",
    "recommendation",
    "live",
    "auth_token",
    "authentication",
    "authorization",
)
_UNSAFE_EXACT_PUBLIC_KEY_TERMS = (
    "candidate",
    "market",
    "slug",
    "question",
    "source",
    "url",
)
_REASON_CODE_SEQUENCE = (
    "no_evidence",
    "authority_block",
    "authority_watch",
    "authority_pass",
    "evidence_decay_block",
    "evidence_decay_watch",
    "evidence_fresh",
    "independence_watch",
    "independent_evidence",
    "conflict_block",
    "conflict_watch",
    "conflict_clear",
    "router_block",
    "router_watch",
    "router_pass",
)


@dataclass(frozen=True)
class ResearchSourceAuthorityEvidenceDecayRouterConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_AUTHORITY_EVIDENCE_DECAY_ROUTER_CONFIG_VERSION
    )
    pass_authority_score: Decimal = Decimal("0.750000")
    watch_authority_score: Decimal = Decimal("0.450000")
    pass_evidence_decay_score: Decimal = Decimal("0.700000")
    watch_evidence_decay_score: Decimal = Decimal("0.400000")
    fresh_evidence_seconds: Decimal = Decimal("86400.000000")
    decayed_evidence_seconds: Decimal = Decimal("604800.000000")
    independence_watch_below: Decimal = Decimal("0.500000")
    conflict_watch_threshold: Decimal = Decimal("0.300000")
    conflict_block_threshold: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityEvidenceDecayRouterConfig:
            raise TypeError(
                "ResearchSourceAuthorityEvidenceDecayRouterConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityEvidenceDecayRouterConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchSourceAuthorityEvidenceDecayRouterConfig",
            )
        _require_public_key("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_AUTHORITY_EVIDENCE_DECAY_ROUTER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_authority_score",
            "watch_authority_score",
            "pass_evidence_decay_score",
            "watch_evidence_decay_score",
            "independence_watch_below",
            "conflict_watch_threshold",
            "conflict_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("fresh_evidence_seconds", "decayed_evidence_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_authority_score > self.pass_authority_score:
            raise ValueError(
                "watch_authority_score must not exceed pass_authority_score",
            )
        if self.watch_evidence_decay_score > self.pass_evidence_decay_score:
            raise ValueError(
                "watch_evidence_decay_score must not exceed "
                "pass_evidence_decay_score",
            )
        if self.fresh_evidence_seconds > self.decayed_evidence_seconds:
            raise ValueError(
                "fresh_evidence_seconds must not exceed decayed_evidence_seconds",
            )
        if self.conflict_watch_threshold > self.conflict_block_threshold:
            raise ValueError(
                "conflict_watch_threshold must not exceed conflict_block_threshold",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityEvidenceDecayRouterInput:
    raw_candidate_id: str
    raw_market_id: str
    raw_market_slug: str
    raw_market_question: str
    raw_source_reference: str
    raw_source_text: str | None
    authority_score: Decimal
    evidence_support_score: Decimal
    evidence_observed_at: datetime
    independence_score: Decimal
    conflict_score: Decimal = Decimal("0.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityEvidenceDecayRouterInput:
            raise TypeError(
                "ResearchSourceAuthorityEvidenceDecayRouterInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityEvidenceDecayRouterInput:
            raise ValueError(
                "input must be exactly ResearchSourceAuthorityEvidenceDecayRouterInput",
            )
        for field_name in (
            "raw_candidate_id",
            "raw_market_id",
            "raw_market_slug",
            "raw_market_question",
            "raw_source_reference",
        ):
            _require_raw_text(field_name, getattr(self, field_name))
        if self.raw_source_text is not None:
            _require_raw_text("raw_source_text", self.raw_source_text)
        for field_name in (
            "authority_score",
            "evidence_support_score",
            "independence_score",
            "conflict_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_observed_at",
            _as_utc("evidence_observed_at", self.evidence_observed_at),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityEvidenceDecayRouterPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityEvidenceDecayRouterPublicPayloadItem:
            raise TypeError(
                "ResearchSourceAuthorityEvidenceDecayRouterPublicPayloadItem "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityEvidenceDecayRouterPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchSourceAuthorityEvidenceDecayRouterPublicPayloadItem",
            )
        _require_public_key("key", self.key)
        _reject_unsafe_public_key(self.key, "public payload item")
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityEvidenceDecayRouterRow:
    evidence_ref: str
    authority_score: Decimal
    evidence_support_score: Decimal
    evidence_age_seconds: Decimal
    evidence_decay_score: Decimal
    independence_score: Decimal
    conflict_score: Decimal
    router_score: Decimal
    router_status: str
    reason_codes: tuple[str, ...]
    validation_config: InitVar[
        ResearchSourceAuthorityEvidenceDecayRouterConfig | None
    ] = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityEvidenceDecayRouterRow:
            raise TypeError(
                "ResearchSourceAuthorityEvidenceDecayRouterRow does not "
                "support subclassing",
            )

    def __post_init__(
        self,
        validation_config: ResearchSourceAuthorityEvidenceDecayRouterConfig | None,
    ) -> None:
        if type(self) is not ResearchSourceAuthorityEvidenceDecayRouterRow:
            raise ValueError(
                "row must be exactly ResearchSourceAuthorityEvidenceDecayRouterRow",
            )
        _require_digest_ref("evidence_ref", self.evidence_ref)
        for field_name in (
            "authority_score",
            "evidence_support_score",
            "evidence_decay_score",
            "independence_score",
            "conflict_score",
            "router_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_age_seconds",
            _require_nonnegative_decimal(
                "evidence_age_seconds",
                self.evidence_age_seconds,
            ),
        )
        _require_status("router_status", self.router_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(
            self,
            config=_row_validation_config(validation_config),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceAuthorityEvidenceDecayRouterReport:
    generated_at: datetime
    config_version: str
    router_status: str
    evidence_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_authority_score: Decimal
    average_evidence_decay_score: Decimal
    oldest_evidence_age_seconds: Decimal
    rows: tuple[ResearchSourceAuthorityEvidenceDecayRouterRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[
        ResearchSourceAuthorityEvidenceDecayRouterPublicPayloadItem,
        ...,
    ]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceAuthorityEvidenceDecayRouterReport:
            raise TypeError(
                "ResearchSourceAuthorityEvidenceDecayRouterReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceAuthorityEvidenceDecayRouterReport:
            raise ValueError(
                "report must be exactly ResearchSourceAuthorityEvidenceDecayRouterReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_key("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_AUTHORITY_EVIDENCE_DECAY_ROUTER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("router_status", self.router_status)
        for field_name in ("evidence_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in ("average_authority_score", "average_evidence_decay_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "oldest_evidence_age_seconds",
            _require_nonnegative_decimal(
                "oldest_evidence_age_seconds",
                self.oldest_evidence_age_seconds,
            ),
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
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_public_payload(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_authority_evidence_decay_router_report_payload(self)


def build_research_source_authority_evidence_decay_router_report(
    inputs: Sequence[ResearchSourceAuthorityEvidenceDecayRouterInput],
    *,
    generated_at: datetime,
    config: ResearchSourceAuthorityEvidenceDecayRouterConfig | None = None,
    public_payload: Sequence[
        ResearchSourceAuthorityEvidenceDecayRouterPublicPayloadItem
    ] = (),
) -> ResearchSourceAuthorityEvidenceDecayRouterReport:
    """Build a local, read-only authority/evidence decay routing report."""

    if config is None:
        config = ResearchSourceAuthorityEvidenceDecayRouterConfig()
    if type(config) is not ResearchSourceAuthorityEvidenceDecayRouterConfig:
        raise ValueError(
            "config must be a ResearchSourceAuthorityEvidenceDecayRouterConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for item in normalized_inputs:
        if item.evidence_observed_at > generated_at_utc:
            raise ValueError("evidence_observed_at must not be after generated_at")
    rows = _build_rows(normalized_inputs, config=config, generated_at=generated_at_utc)
    return ResearchSourceAuthorityEvidenceDecayRouterReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        router_status=_report_status(rows),
        evidence_count=_decimal_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        average_authority_score=_average(tuple(row.authority_score for row in rows)),
        average_evidence_decay_score=_average(
            tuple(row.evidence_decay_score for row in rows),
        ),
        oldest_evidence_age_seconds=max(
            (row.evidence_age_seconds for row in rows),
            default=_ZERO,
        ),
        rows=rows,
        reason_codes=_report_reason_codes(rows),
        public_payload=_normalize_public_payload(public_payload),
    )


def research_source_authority_evidence_decay_router_report_payload(
    report: ResearchSourceAuthorityEvidenceDecayRouterReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceAuthorityEvidenceDecayRouterReport:
        raise ValueError(
            "report must be a ResearchSourceAuthorityEvidenceDecayRouterReport",
        )
    validate_research_source_authority_evidence_decay_router_report_digest(report)
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_source_authority_evidence_decay_router_public_payload(payload)
    return payload


def research_source_authority_evidence_decay_router_report_digest(
    report: ResearchSourceAuthorityEvidenceDecayRouterReport,
) -> str:
    if type(report) is not ResearchSourceAuthorityEvidenceDecayRouterReport:
        raise ValueError(
            "report must be a ResearchSourceAuthorityEvidenceDecayRouterReport",
        )
    return _report_digest_from_public_payload(report)


def validate_research_source_authority_evidence_decay_router_report_digest(
    report: ResearchSourceAuthorityEvidenceDecayRouterReport,
) -> None:
    if type(report) is not ResearchSourceAuthorityEvidenceDecayRouterReport:
        raise ValueError(
            "report must be a ResearchSourceAuthorityEvidenceDecayRouterReport",
        )
    _require_sha256_digest("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_digest_from_public_payload(report):
        raise ValueError("derived_validation_digest must match report payload")


def validate_research_source_authority_evidence_decay_router_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _require_exact_public_fields(
        "public payload",
        payload,
        ResearchSourceAuthorityEvidenceDecayRouterReport,
    )
    _reject_unsafe_public_payload(
        "public payload",
        payload,
        allow_json_containers=True,
    )
    _reject_public_numerics("public payload", payload)
    normalized_report = _report_from_public_payload(payload)
    if _json_ready(normalized_report) != payload:
        raise ValueError("public payload must use canonical schema values")


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchSourceAuthorityEvidenceDecayRouterReport:
    return ResearchSourceAuthorityEvidenceDecayRouterReport(
        generated_at=_parse_public_datetime("generated_at", payload["generated_at"]),
        config_version=payload["config_version"],
        router_status=payload["router_status"],
        evidence_count=_parse_public_decimal(
            "evidence_count",
            payload["evidence_count"],
        ),
        pass_count=_parse_public_decimal("pass_count", payload["pass_count"]),
        watch_count=_parse_public_decimal("watch_count", payload["watch_count"]),
        block_count=_parse_public_decimal("block_count", payload["block_count"]),
        average_authority_score=_parse_public_decimal(
            "average_authority_score",
            payload["average_authority_score"],
        ),
        average_evidence_decay_score=_parse_public_decimal(
            "average_evidence_decay_score",
            payload["average_evidence_decay_score"],
        ),
        oldest_evidence_age_seconds=_parse_public_decimal(
            "oldest_evidence_age_seconds",
            payload["oldest_evidence_age_seconds"],
        ),
        rows=_rows_from_public_payload(payload["rows"]),
        reason_codes=_parse_public_reason_codes(
            "reason_codes",
            payload["reason_codes"],
        ),
        public_payload=_public_items_from_public_payload(payload["public_payload"]),
        derived_validation_digest=payload["derived_validation_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _rows_from_public_payload(
    value: object,
) -> tuple[ResearchSourceAuthorityEvidenceDecayRouterRow, ...]:
    if type(value) is not list:
        raise ValueError("rows must be a list")
    rows: list[ResearchSourceAuthorityEvidenceDecayRouterRow] = []
    for item in value:
        row_payload = _require_exact_public_fields(
            "row",
            item,
            ResearchSourceAuthorityEvidenceDecayRouterRow,
        )
        rows.append(
            ResearchSourceAuthorityEvidenceDecayRouterRow(
                evidence_ref=row_payload["evidence_ref"],
                authority_score=_parse_public_decimal(
                    "authority_score",
                    row_payload["authority_score"],
                ),
                evidence_support_score=_parse_public_decimal(
                    "evidence_support_score",
                    row_payload["evidence_support_score"],
                ),
                evidence_age_seconds=_parse_public_decimal(
                    "evidence_age_seconds",
                    row_payload["evidence_age_seconds"],
                ),
                evidence_decay_score=_parse_public_decimal(
                    "evidence_decay_score",
                    row_payload["evidence_decay_score"],
                ),
                independence_score=_parse_public_decimal(
                    "independence_score",
                    row_payload["independence_score"],
                ),
                conflict_score=_parse_public_decimal(
                    "conflict_score",
                    row_payload["conflict_score"],
                ),
                router_score=_parse_public_decimal(
                    "router_score",
                    row_payload["router_score"],
                ),
                router_status=row_payload["router_status"],
                reason_codes=_parse_public_reason_codes(
                    "row.reason_codes",
                    row_payload["reason_codes"],
                ),
                paper_only=row_payload["paper_only"],
                report_only=row_payload["report_only"],
                readonly=row_payload["readonly"],
            ),
        )
    normalized = _normalize_rows(tuple(rows))
    if tuple(rows) != normalized:
        raise ValueError("rows must use deterministic evidence_ref order")
    return normalized


def _public_items_from_public_payload(
    value: object,
) -> tuple[ResearchSourceAuthorityEvidenceDecayRouterPublicPayloadItem, ...]:
    if type(value) is not list:
        raise ValueError("public_payload must be a list")
    items: list[ResearchSourceAuthorityEvidenceDecayRouterPublicPayloadItem] = []
    for item in value:
        item_payload = _require_exact_public_fields(
            "public payload item",
            item,
            ResearchSourceAuthorityEvidenceDecayRouterPublicPayloadItem,
        )
        items.append(
            ResearchSourceAuthorityEvidenceDecayRouterPublicPayloadItem(
                key=item_payload["key"],
                value=item_payload["value"],
                paper_only=item_payload["paper_only"],
                report_only=item_payload["report_only"],
                readonly=item_payload["readonly"],
            ),
        )
    normalized = _normalize_public_payload(tuple(items))
    if tuple(items) != normalized:
        raise ValueError("public_payload must use deterministic key order")
    return normalized


def _require_exact_public_fields(
    label: str,
    value: object,
    dataclass_type: type[object],
) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    expected = {field.name for field in fields(dataclass_type)}
    actual = set(value)
    if actual != expected:
        missing = ",".join(sorted(expected - actual))
        unexpected = ",".join(sorted(actual - expected))
        raise ValueError(
            f"{label} fields must exactly match schema; "
            f"missing={missing or '-'}; unexpected={unexpected or '-'}",
        )
    return value


def _parse_public_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str or not _CANONICAL_DECIMAL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    normalized = Decimal(value)
    try:
        quantized = _quantize(normalized)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be a canonical Decimal string",
        ) from exc
    if not normalized.is_finite() or str(quantized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _parse_public_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be a canonical UTC datetime string",
        ) from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _parse_public_reason_codes(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    normalized = _normalize_reason_codes(tuple(value))
    if list(normalized) != value:
        raise ValueError(f"{field_name} must use canonical reason code order")
    return normalized


def _build_rows(
    inputs: tuple[ResearchSourceAuthorityEvidenceDecayRouterInput, ...],
    *,
    config: ResearchSourceAuthorityEvidenceDecayRouterConfig,
    generated_at: datetime,
) -> tuple[ResearchSourceAuthorityEvidenceDecayRouterRow, ...]:
    rows = tuple(_row_for_input(item, config=config, generated_at=generated_at) for item in inputs)
    return tuple(sorted(rows, key=lambda row: row.evidence_ref))


def _row_for_input(
    item: ResearchSourceAuthorityEvidenceDecayRouterInput,
    *,
    config: ResearchSourceAuthorityEvidenceDecayRouterConfig,
    generated_at: datetime,
) -> ResearchSourceAuthorityEvidenceDecayRouterRow:
    evidence_age_seconds = _seconds_between(item.evidence_observed_at, generated_at)
    evidence_decay_score = _evidence_decay_score(
        item.evidence_support_score,
        evidence_age_seconds=evidence_age_seconds,
        config=config,
    )
    router_score = _router_score(
        authority_score=item.authority_score,
        evidence_decay_score=evidence_decay_score,
        independence_score=item.independence_score,
        conflict_score=item.conflict_score,
    )
    status = _row_status(
        authority_score=item.authority_score,
        evidence_decay_score=evidence_decay_score,
        evidence_age_seconds=evidence_age_seconds,
        independence_score=item.independence_score,
        conflict_score=item.conflict_score,
        config=config,
    )
    return ResearchSourceAuthorityEvidenceDecayRouterRow(
        evidence_ref=_evidence_ref(item),
        authority_score=item.authority_score,
        evidence_support_score=item.evidence_support_score,
        evidence_age_seconds=evidence_age_seconds,
        evidence_decay_score=evidence_decay_score,
        independence_score=item.independence_score,
        conflict_score=item.conflict_score,
        router_score=router_score,
        router_status=status,
        reason_codes=_row_reason_codes(
            authority_score=item.authority_score,
            evidence_decay_score=evidence_decay_score,
            evidence_age_seconds=evidence_age_seconds,
            independence_score=item.independence_score,
            conflict_score=item.conflict_score,
            status=status,
            config=config,
        ),
        validation_config=config,
    )


def _evidence_decay_score(
    evidence_support_score: Decimal,
    *,
    evidence_age_seconds: Decimal,
    config: ResearchSourceAuthorityEvidenceDecayRouterConfig,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        if evidence_age_seconds <= config.fresh_evidence_seconds:
            return evidence_support_score
        if evidence_age_seconds >= config.decayed_evidence_seconds:
            return _ZERO
        decay_window = config.decayed_evidence_seconds - config.fresh_evidence_seconds
        decay_age = evidence_age_seconds - config.fresh_evidence_seconds
        decay_factor = _ONE - (decay_age / decay_window)
        return _quantize(evidence_support_score * decay_factor)


def _router_score(
    *,
    authority_score: Decimal,
    evidence_decay_score: Decimal,
    independence_score: Decimal,
    conflict_score: Decimal,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        score = (
            (authority_score * Decimal("0.400000"))
            + (evidence_decay_score * Decimal("0.400000"))
            + (independence_score * Decimal("0.150000"))
            + ((_ONE - conflict_score) * Decimal("0.050000"))
        )
        return _quantize(max(_ZERO, min(_ONE, score)))


def _row_status(
    *,
    authority_score: Decimal,
    evidence_decay_score: Decimal,
    evidence_age_seconds: Decimal,
    independence_score: Decimal,
    conflict_score: Decimal,
    config: ResearchSourceAuthorityEvidenceDecayRouterConfig,
) -> str:
    if authority_score < config.watch_authority_score:
        return "block"
    if evidence_age_seconds >= config.decayed_evidence_seconds:
        return "block"
    if evidence_decay_score < config.watch_evidence_decay_score:
        return "block"
    if conflict_score >= config.conflict_block_threshold:
        return "block"
    if (
        authority_score >= config.pass_authority_score
        and evidence_decay_score >= config.pass_evidence_decay_score
        and evidence_age_seconds <= config.fresh_evidence_seconds
        and independence_score >= config.independence_watch_below
        and conflict_score < config.conflict_watch_threshold
    ):
        return "pass"
    return "watch"


def _row_reason_codes(
    *,
    authority_score: Decimal,
    evidence_decay_score: Decimal,
    evidence_age_seconds: Decimal,
    independence_score: Decimal,
    conflict_score: Decimal,
    status: str,
    config: ResearchSourceAuthorityEvidenceDecayRouterConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if authority_score < config.watch_authority_score:
        reason_codes.append("authority_block")
    elif authority_score < config.pass_authority_score:
        reason_codes.append("authority_watch")
    else:
        reason_codes.append("authority_pass")
    if (
        evidence_age_seconds >= config.decayed_evidence_seconds
        or evidence_decay_score < config.watch_evidence_decay_score
    ):
        reason_codes.append("evidence_decay_block")
    elif (
        evidence_age_seconds > config.fresh_evidence_seconds
        or evidence_decay_score < config.pass_evidence_decay_score
    ):
        reason_codes.append("evidence_decay_watch")
    else:
        reason_codes.append("evidence_fresh")
    if independence_score < config.independence_watch_below:
        reason_codes.append("independence_watch")
    else:
        reason_codes.append("independent_evidence")
    if conflict_score >= config.conflict_block_threshold:
        reason_codes.append("conflict_block")
    elif conflict_score >= config.conflict_watch_threshold:
        reason_codes.append("conflict_watch")
    else:
        reason_codes.append("conflict_clear")
    reason_codes.append(f"router_{status}")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(
    rows: tuple[ResearchSourceAuthorityEvidenceDecayRouterRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.router_status == "block" for row in rows):
        return "block"
    if any(row.router_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceAuthorityEvidenceDecayRouterRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_evidence", "router_block")
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[ResearchSourceAuthorityEvidenceDecayRouterRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.router_status == status))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _validate_row_consistency(
    row: ResearchSourceAuthorityEvidenceDecayRouterRow,
    *,
    config: ResearchSourceAuthorityEvidenceDecayRouterConfig,
) -> None:
    expected_router_score = _router_score(
        authority_score=row.authority_score,
        evidence_decay_score=row.evidence_decay_score,
        independence_score=row.independence_score,
        conflict_score=row.conflict_score,
    )
    if row.router_score != expected_router_score:
        raise ValueError("router_score must match row components")
    expected_router_status = _row_status(
        authority_score=row.authority_score,
        evidence_decay_score=row.evidence_decay_score,
        evidence_age_seconds=row.evidence_age_seconds,
        independence_score=row.independence_score,
        conflict_score=row.conflict_score,
        config=config,
    )
    if row.router_status != expected_router_status:
        raise ValueError("router_status must match row components")
    expected_reason_codes = _row_reason_codes(
        authority_score=row.authority_score,
        evidence_decay_score=row.evidence_decay_score,
        evidence_age_seconds=row.evidence_age_seconds,
        independence_score=row.independence_score,
        conflict_score=row.conflict_score,
        status=expected_router_status,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row components")
    expected_status_marker = f"router_{row.router_status}"
    if expected_status_marker not in row.reason_codes:
        raise ValueError("router_status must match reason_codes")
    if "no_evidence" in row.reason_codes:
        raise ValueError("row reason_codes must not include no_evidence")
    reason_groups = (
        ("authority", ("authority_block", "authority_watch", "authority_pass")),
        (
            "evidence_decay",
            ("evidence_decay_block", "evidence_decay_watch", "evidence_fresh"),
        ),
        ("independence", ("independence_watch", "independent_evidence")),
        ("conflict", ("conflict_block", "conflict_watch", "conflict_clear")),
        ("router", ("router_block", "router_watch", "router_pass")),
    )
    for label, reason_codes in reason_groups:
        if sum(reason_code in row.reason_codes for reason_code in reason_codes) != 1:
            raise ValueError(f"row must contain exactly one {label} reason code")


def _row_validation_config(
    config: ResearchSourceAuthorityEvidenceDecayRouterConfig | None,
) -> ResearchSourceAuthorityEvidenceDecayRouterConfig:
    if config is None:
        return ResearchSourceAuthorityEvidenceDecayRouterConfig()
    if type(config) is not ResearchSourceAuthorityEvidenceDecayRouterConfig:
        raise ValueError(
            "validation_config must be a "
            "ResearchSourceAuthorityEvidenceDecayRouterConfig",
        )
    _require_hard_flags("validation_config", config)
    return config


def _validate_report_consistency(
    report: ResearchSourceAuthorityEvidenceDecayRouterReport,
) -> None:
    if report.evidence_count != _decimal_count(len(report.rows)):
        raise ValueError("evidence_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_authority_score != _average(
        tuple(row.authority_score for row in report.rows),
    ):
        raise ValueError("average_authority_score must match rows")
    if report.average_evidence_decay_score != _average(
        tuple(row.evidence_decay_score for row in report.rows),
    ):
        raise ValueError("average_evidence_decay_score must match rows")
    expected_oldest_age = max(
        (row.evidence_age_seconds for row in report.rows),
        default=_ZERO,
    )
    if report.oldest_evidence_age_seconds != expected_oldest_age:
        raise ValueError("oldest_evidence_age_seconds must match rows")
    if report.router_status != _report_status(report.rows):
        raise ValueError("router_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_inputs(
    inputs: Sequence[ResearchSourceAuthorityEvidenceDecayRouterInput],
) -> tuple[ResearchSourceAuthorityEvidenceDecayRouterInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Sequence):
        raise ValueError("inputs must be a sequence")
    normalized: list[ResearchSourceAuthorityEvidenceDecayRouterInput] = []
    seen_evidence_refs: set[str] = set()
    for item in inputs:
        if type(item) is not ResearchSourceAuthorityEvidenceDecayRouterInput:
            raise ValueError(
                "inputs must contain ResearchSourceAuthorityEvidenceDecayRouterInput",
            )
        _require_hard_flags("input", item)
        evidence_ref = _evidence_ref(item)
        if evidence_ref in seen_evidence_refs:
            raise ValueError("inputs must be unique by evidence_ref")
        seen_evidence_refs.add(evidence_ref)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.evidence_observed_at,
                _evidence_ref(item),
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchSourceAuthorityEvidenceDecayRouterRow],
) -> tuple[ResearchSourceAuthorityEvidenceDecayRouterRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchSourceAuthorityEvidenceDecayRouterRow] = []
    seen_evidence_refs: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceAuthorityEvidenceDecayRouterRow:
            raise ValueError("rows must contain ResearchSourceAuthorityEvidenceDecayRouterRow")
        _require_hard_flags("row", row)
        if row.evidence_ref in seen_evidence_refs:
            raise ValueError("rows must be unique by evidence_ref")
        seen_evidence_refs.add(row.evidence_ref)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.evidence_ref))


def _normalize_public_payload(
    public_payload: Sequence[
        ResearchSourceAuthorityEvidenceDecayRouterPublicPayloadItem
    ],
) -> tuple[ResearchSourceAuthorityEvidenceDecayRouterPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchSourceAuthorityEvidenceDecayRouterPublicPayloadItem] = []
    seen_keys: set[str] = set()
    for item in public_payload:
        if type(item) is not ResearchSourceAuthorityEvidenceDecayRouterPublicPayloadItem:
            raise ValueError(
                "public_payload must contain "
                "ResearchSourceAuthorityEvidenceDecayRouterPublicPayloadItem",
            )
        _require_hard_flags("public payload item", item)
        if item.key in seen_keys:
            raise ValueError("public_payload keys must be unique")
        seen_keys.add(item.key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_key("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_raw_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty text")
    if len(value) > 4096:
        raise ValueError(f"{field_name} must not exceed 4096 characters")
    return value


def _require_public_key(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_KEY_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public key")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in RESEARCH_SOURCE_AUTHORITY_EVIDENCE_DECAY_ROUTER_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_digest_ref(field_name: str, value: object) -> str:
    if type(value) is not str or not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a sha256 digest reference")
    _require_sha256_digest(field_name, value.removeprefix("sha256:"))
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return _quantize(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


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
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return _quantize(Decimal(value))


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    with localcontext(_DECIMAL_CONTEXT):
        seconds = (
            Decimal(delta.days * 86400)
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / Decimal("1000000"))
        )
    return _require_nonnegative_decimal("evidence_age_seconds", seconds)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(_DECIMAL_CONTEXT):
            return value.quantize(_QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be representable at six places") from exc


def _evidence_ref(item: ResearchSourceAuthorityEvidenceDecayRouterInput) -> str:
    private_payload = {
        "authority_score": str(item.authority_score),
        "candidate": item.raw_candidate_id,
        "conflict_score": str(item.conflict_score),
        "evidence_observed_at": item.evidence_observed_at.isoformat(),
        "evidence_support_score": str(item.evidence_support_score),
        "independence_score": str(item.independence_score),
        "market": item.raw_market_id,
        "question": item.raw_market_question,
        "reference": item.raw_source_reference,
        "slug": item.raw_market_slug,
        "text": item.raw_source_text,
    }
    canonical = json.dumps(
        private_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"sha256:{sha256(canonical.encode('utf-8')).hexdigest()}"


def _report_digest_from_public_payload(
    report: ResearchSourceAuthorityEvidenceDecayRouterReport,
) -> str:
    payload = _json_ready(_report_values_without_digest(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return _payload_digest(payload)


def _report_values_without_digest(
    report: ResearchSourceAuthorityEvidenceDecayRouterReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _payload_digest(payload: Mapping[str, Any]) -> str:
    ready = _json_ready(payload)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        ready,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        ready,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


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


def _reject_public_numerics(label: str, value: object) -> None:
    if type(value) is int or isinstance(value, float) or type(value) is Decimal:
        raise ValueError(f"{label} must use Decimal strings for numeric values")
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_public_numerics(f"{label}.{key}", item)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_public_numerics(f"{label}[{index}]", item)


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
    normalized_key_parts = tuple(part for part in re.split(r"[^a-z0-9]+", lowered) if part)
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS) or any(
        term in normalized_key_parts for term in _UNSAFE_EXACT_PUBLIC_KEY_TERMS
    ):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if (
        "://" in lowered
        or "?" in lowered
        or "@" in lowered
        or lowered.startswith("www.")
        or re.search(r"\b[a-z0-9.-]+\.[a-z]{2,}(?:/|$)", lowered) is not None
    ):
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_AUTHORITY_EVIDENCE_DECAY_ROUTER_CONFIG_VERSION",
    "RESEARCH_SOURCE_AUTHORITY_EVIDENCE_DECAY_ROUTER_STATUSES",
    "ResearchSourceAuthorityEvidenceDecayRouterConfig",
    "ResearchSourceAuthorityEvidenceDecayRouterInput",
    "ResearchSourceAuthorityEvidenceDecayRouterPublicPayloadItem",
    "ResearchSourceAuthorityEvidenceDecayRouterReport",
    "ResearchSourceAuthorityEvidenceDecayRouterRow",
    "build_research_source_authority_evidence_decay_router_report",
    "research_source_authority_evidence_decay_router_report_digest",
    "research_source_authority_evidence_decay_router_report_payload",
    "validate_research_source_authority_evidence_decay_router_public_payload",
    "validate_research_source_authority_evidence_decay_router_report_digest",
)
