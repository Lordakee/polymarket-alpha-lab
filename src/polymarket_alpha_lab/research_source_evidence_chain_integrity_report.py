"""Phase 1 report-only research source evidence-chain integrity report."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_SOURCE_EVIDENCE_CHAIN_INTEGRITY_CONFIG_VERSION = (
    "research-source-evidence-chain-integrity-report-v1"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_REASON_CODE_SEQUENCE = (
    "empty_evidence_chain",
    "source_class_quorum_gap",
    "claim_linkage_gap",
    "stale_link_pressure_watch",
    "stale_link_pressure_block",
    "contradiction_exposure_watch",
    "contradiction_exposure_block",
    "manual_review_urgency_watch",
    "manual_review_urgency_block",
    "evidence_chain_integrity_pass",
)
_UNSAFE_PUBLIC_TERMS = (
    "raw",
    "url",
    "uri",
    "text",
    "transcript",
    "market",
    "slug",
    "identifier",
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "db",
    "signing",
    "trade",
    "trading",
    "sizing",
    "recommendation",
)


@dataclass(frozen=True)
class ResearchSourceEvidenceChainIntegrityConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_EVIDENCE_CHAIN_INTEGRITY_CONFIG_VERSION
    minimum_source_class_count: Decimal = Decimal("2.000000")
    stale_after_seconds: Decimal = Decimal("86400.000000")
    watch_stale_link_pressure: Decimal = Decimal("0.250000")
    block_stale_link_pressure: Decimal = Decimal("0.750000")
    watch_contradiction_exposure: Decimal = Decimal("0.250000")
    block_contradiction_exposure: Decimal = Decimal("0.500000")
    watch_manual_review_urgency: Decimal = Decimal("0.500000")
    block_manual_review_urgency: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceEvidenceChainIntegrityConfig:
            raise TypeError(
                "ResearchSourceEvidenceChainIntegrityConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceEvidenceChainIntegrityConfig:
            raise ValueError(
                "config must be exactly ResearchSourceEvidenceChainIntegrityConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_EVIDENCE_CHAIN_INTEGRITY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "minimum_source_class_count",
            _require_positive_count_decimal(
                "minimum_source_class_count",
                self.minimum_source_class_count,
            ),
        )
        object.__setattr__(
            self,
            "stale_after_seconds",
            _require_positive_count_decimal("stale_after_seconds", self.stale_after_seconds),
        )
        for field_name in (
            "watch_stale_link_pressure",
            "block_stale_link_pressure",
            "watch_contradiction_exposure",
            "block_contradiction_exposure",
            "watch_manual_review_urgency",
            "block_manual_review_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_stale_link_pressure < self.watch_stale_link_pressure:
            raise ValueError("block_stale_link_pressure must be at least watch threshold")
        if self.block_contradiction_exposure < self.watch_contradiction_exposure:
            raise ValueError("block_contradiction_exposure must be at least watch threshold")
        if self.block_manual_review_urgency < self.watch_manual_review_urgency:
            raise ValueError("block_manual_review_urgency must be at least watch threshold")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceChainIntegrityLink:
    chain_id: str
    claim_id: str
    evidence_id: str
    source_class: str
    observed_at: datetime
    linked_to_claim: bool = True
    supports_claim: bool = True
    contradicts_claim: bool = False
    manual_review_flag: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceEvidenceChainIntegrityLink:
            raise TypeError(
                "ResearchSourceEvidenceChainIntegrityLink does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceEvidenceChainIntegrityLink:
            raise ValueError(
                "link must be exactly ResearchSourceEvidenceChainIntegrityLink",
            )
        for field_name in ("chain_id", "claim_id", "evidence_id", "source_class"):
            _require_public_identifier(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "linked_to_claim",
            "supports_claim",
            "contradicts_claim",
            "manual_review_flag",
        ):
            _require_bool(field_name, getattr(self, field_name))
        if self.contradicts_claim and self.supports_claim:
            raise ValueError("contradicts_claim and supports_claim cannot both be true")
        _require_hard_flags("link", self)
        _reject_unsafe_public_payload("link", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceChainIntegrityPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceEvidenceChainIntegrityPublicPayloadItem:
            raise TypeError(
                "ResearchSourceEvidenceChainIntegrityPublicPayloadItem does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceEvidenceChainIntegrityPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchSourceEvidenceChainIntegrityPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceChainIntegrityRow:
    chain_id: str
    claim_count: Decimal
    evidence_link_count: Decimal
    linked_claim_count: Decimal
    unlinked_claim_count: Decimal
    source_class_count: Decimal
    source_class_quorum_score: Decimal
    claim_linkage_completeness: Decimal
    stale_link_count: Decimal
    stale_link_pressure: Decimal
    contradiction_count: Decimal
    contradiction_exposure: Decimal
    manual_review_signal_count: Decimal
    manual_review_urgency: Decimal
    integrity_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceEvidenceChainIntegrityRow:
            raise TypeError(
                "ResearchSourceEvidenceChainIntegrityRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceEvidenceChainIntegrityRow:
            raise ValueError(
                "row must be exactly ResearchSourceEvidenceChainIntegrityRow",
            )
        _require_public_identifier("chain_id", self.chain_id)
        for field_name in (
            "claim_count",
            "evidence_link_count",
            "linked_claim_count",
            "unlinked_claim_count",
            "source_class_count",
            "stale_link_count",
            "contradiction_count",
            "manual_review_signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_class_quorum_score",
            "claim_linkage_completeness",
            "stale_link_pressure",
            "contradiction_exposure",
            "manual_review_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("integrity_status", self.integrity_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceChainIntegrityReport:
    generated_at: datetime
    config_version: str
    integrity_status: str
    chain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_source_class_quorum_score: Decimal
    average_claim_linkage_completeness: Decimal
    average_stale_link_pressure: Decimal
    max_contradiction_exposure: Decimal
    max_manual_review_urgency: Decimal
    rows: tuple[ResearchSourceEvidenceChainIntegrityRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchSourceEvidenceChainIntegrityPublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceEvidenceChainIntegrityReport:
            raise TypeError(
                "ResearchSourceEvidenceChainIntegrityReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceEvidenceChainIntegrityReport:
            raise ValueError(
                "report must be exactly ResearchSourceEvidenceChainIntegrityReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_EVIDENCE_CHAIN_INTEGRITY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("integrity_status", self.integrity_status)
        for field_name in ("chain_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_source_class_quorum_score",
            "average_claim_linkage_completeness",
            "average_stale_link_pressure",
            "max_contradiction_exposure",
            "max_manual_review_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
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
            "ResearchSourceEvidenceChainIntegrityReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_source_evidence_chain_integrity_report(
    links: Sequence[ResearchSourceEvidenceChainIntegrityLink],
    *,
    generated_at: datetime,
    config: ResearchSourceEvidenceChainIntegrityConfig | None = None,
    public_payload: Sequence[ResearchSourceEvidenceChainIntegrityPublicPayloadItem] = (),
) -> ResearchSourceEvidenceChainIntegrityReport:
    """Build a local, deterministic, report-only evidence-chain integrity snapshot."""

    if config is None:
        config = ResearchSourceEvidenceChainIntegrityConfig()
    if type(config) is not ResearchSourceEvidenceChainIntegrityConfig:
        raise ValueError(
            "config must be a ResearchSourceEvidenceChainIntegrityConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_links = _normalize_links(links)
    for link in normalized_links:
        if link.observed_at > generated_at:
            raise ValueError("link observed_at must not be after generated_at")
    payload_items = _normalize_public_payload(public_payload)
    rows = _build_rows(normalized_links, generated_at=generated_at, config=config)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "integrity_status": _report_status(rows),
        "chain_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_source_class_quorum_score": _average(
            tuple(row.source_class_quorum_score for row in rows),
        ),
        "average_claim_linkage_completeness": _average(
            tuple(row.claim_linkage_completeness for row in rows),
        ),
        "average_stale_link_pressure": _average(
            tuple(row.stale_link_pressure for row in rows),
        ),
        "max_contradiction_exposure": max(
            (row.contradiction_exposure for row in rows),
            default=_ZERO,
        ),
        "max_manual_review_urgency": max(
            (row.manual_review_urgency for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceEvidenceChainIntegrityReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _build_rows(
    links: tuple[ResearchSourceEvidenceChainIntegrityLink, ...],
    *,
    generated_at: datetime,
    config: ResearchSourceEvidenceChainIntegrityConfig,
) -> tuple[ResearchSourceEvidenceChainIntegrityRow, ...]:
    grouped: dict[str, list[ResearchSourceEvidenceChainIntegrityLink]] = {}
    for link in links:
        grouped.setdefault(link.chain_id, []).append(link)
    return tuple(
        _row_for_chain(
            chain_id,
            tuple(sorted(items, key=_link_sort_key)),
            generated_at=generated_at,
            config=config,
        )
        for chain_id, items in sorted(grouped.items())
    )


def _row_for_chain(
    chain_id: str,
    links: tuple[ResearchSourceEvidenceChainIntegrityLink, ...],
    *,
    generated_at: datetime,
    config: ResearchSourceEvidenceChainIntegrityConfig,
) -> ResearchSourceEvidenceChainIntegrityRow:
    evidence_link_count = _decimal_count(len(links))
    linked_claim_count = _decimal_count(sum(1 for link in links if link.linked_to_claim))
    unlinked_claim_count = _quantize(evidence_link_count - linked_claim_count)
    source_class_count = _decimal_count(len({link.source_class for link in links}))
    claim_count = _decimal_count(len({link.claim_id for link in links if link.linked_to_claim}))
    stale_link_count = _decimal_count(
        sum(
            1
            for link in links
            if _source_age_seconds(generated_at, link.observed_at) > config.stale_after_seconds
        ),
    )
    contradiction_count = _decimal_count(sum(1 for link in links if link.contradicts_claim))
    manual_review_count = _decimal_count(sum(1 for link in links if link.manual_review_flag))
    source_class_quorum_score = _clamp_ratio(
        source_class_count / config.minimum_source_class_count,
    )
    claim_linkage_completeness = _ratio(linked_claim_count, evidence_link_count)
    stale_link_pressure = _ratio(stale_link_count, evidence_link_count)
    contradiction_exposure = _ratio(contradiction_count, evidence_link_count)
    manual_review_urgency = (
        _ONE
        if manual_review_count > _ZERO
        else _clamp_ratio(
            max(
                _ZERO,
                (stale_link_pressure + contradiction_exposure) / Decimal("2"),
            ),
        )
    )
    reason_codes = _row_reason_codes(
        evidence_link_count=evidence_link_count,
        source_class_count=source_class_count,
        claim_linkage_completeness=claim_linkage_completeness,
        stale_link_pressure=stale_link_pressure,
        contradiction_exposure=contradiction_exposure,
        manual_review_urgency=manual_review_urgency,
        config=config,
    )
    return ResearchSourceEvidenceChainIntegrityRow(
        chain_id=chain_id,
        claim_count=claim_count,
        evidence_link_count=evidence_link_count,
        linked_claim_count=linked_claim_count,
        unlinked_claim_count=unlinked_claim_count,
        source_class_count=source_class_count,
        source_class_quorum_score=source_class_quorum_score,
        claim_linkage_completeness=claim_linkage_completeness,
        stale_link_count=stale_link_count,
        stale_link_pressure=stale_link_pressure,
        contradiction_count=contradiction_count,
        contradiction_exposure=contradiction_exposure,
        manual_review_signal_count=manual_review_count,
        manual_review_urgency=manual_review_urgency,
        integrity_status=_row_status(
            source_class_count=source_class_count,
            claim_linkage_completeness=claim_linkage_completeness,
            stale_link_pressure=stale_link_pressure,
            contradiction_exposure=contradiction_exposure,
            manual_review_urgency=manual_review_urgency,
            config=config,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    evidence_link_count: Decimal,
    source_class_count: Decimal,
    claim_linkage_completeness: Decimal,
    stale_link_pressure: Decimal,
    contradiction_exposure: Decimal,
    manual_review_urgency: Decimal,
    config: ResearchSourceEvidenceChainIntegrityConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if evidence_link_count == _ZERO:
        reason_codes.append("empty_evidence_chain")
    if source_class_count < config.minimum_source_class_count:
        reason_codes.append("source_class_quorum_gap")
    if claim_linkage_completeness < _ONE:
        reason_codes.append("claim_linkage_gap")
    _append_threshold_reason(
        reason_codes,
        value=stale_link_pressure,
        watch=config.watch_stale_link_pressure,
        block=config.block_stale_link_pressure,
        watch_code="stale_link_pressure_watch",
        block_code="stale_link_pressure_block",
    )
    _append_threshold_reason(
        reason_codes,
        value=contradiction_exposure,
        watch=config.watch_contradiction_exposure,
        block=config.block_contradiction_exposure,
        watch_code="contradiction_exposure_watch",
        block_code="contradiction_exposure_block",
    )
    _append_threshold_reason(
        reason_codes,
        value=manual_review_urgency,
        watch=config.watch_manual_review_urgency,
        block=config.block_manual_review_urgency,
        watch_code="manual_review_urgency_watch",
        block_code="manual_review_urgency_block",
    )
    if not reason_codes:
        reason_codes.append("evidence_chain_integrity_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _append_threshold_reason(
    reason_codes: list[str],
    *,
    value: Decimal,
    watch: Decimal,
    block: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if value >= block:
        reason_codes.append(block_code)
        return
    if value >= watch:
        reason_codes.append(watch_code)


def _row_status(
    *,
    source_class_count: Decimal,
    claim_linkage_completeness: Decimal,
    stale_link_pressure: Decimal,
    contradiction_exposure: Decimal,
    manual_review_urgency: Decimal,
    config: ResearchSourceEvidenceChainIntegrityConfig,
) -> str:
    if (
        source_class_count < config.minimum_source_class_count
        or claim_linkage_completeness < _ONE
        or stale_link_pressure >= config.block_stale_link_pressure
        or contradiction_exposure >= config.block_contradiction_exposure
        or manual_review_urgency >= config.block_manual_review_urgency
    ):
        return "block"
    if (
        stale_link_pressure >= config.watch_stale_link_pressure
        or contradiction_exposure >= config.watch_contradiction_exposure
        or manual_review_urgency >= config.watch_manual_review_urgency
    ):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchSourceEvidenceChainIntegrityRow, ...]) -> str:
    if not rows:
        return "pass"
    if any(row.integrity_status == "block" for row in rows):
        return "block"
    if any(row.integrity_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceEvidenceChainIntegrityRow, ...],
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[ResearchSourceEvidenceChainIntegrityRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.integrity_status == status)


def _source_age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    return _quantize(Decimal(str((generated_at - observed_at).total_seconds())))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _clamp_ratio(numerator / denominator)


def _link_sort_key(link: ResearchSourceEvidenceChainIntegrityLink) -> tuple[str, str, str, str]:
    return (link.chain_id, link.claim_id, link.evidence_id, link.source_class)


def _normalize_links(
    links: Sequence[ResearchSourceEvidenceChainIntegrityLink],
) -> tuple[ResearchSourceEvidenceChainIntegrityLink, ...]:
    if isinstance(links, (str, bytes)) or not isinstance(links, Sequence):
        raise ValueError("links must be a sequence")
    normalized: list[ResearchSourceEvidenceChainIntegrityLink] = []
    seen: set[tuple[str, str, str, str]] = set()
    for link in links:
        if type(link) is not ResearchSourceEvidenceChainIntegrityLink:
            raise ValueError("links must contain ResearchSourceEvidenceChainIntegrityLink")
        key = _link_sort_key(link)
        if key in seen:
            raise ValueError("links must not contain duplicate evidence links")
        seen.add(key)
        normalized.append(link)
    return tuple(sorted(normalized, key=_link_sort_key))


def _normalize_rows(
    rows: Sequence[ResearchSourceEvidenceChainIntegrityRow],
) -> tuple[ResearchSourceEvidenceChainIntegrityRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchSourceEvidenceChainIntegrityRow] = []
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceEvidenceChainIntegrityRow:
            raise ValueError("rows must contain ResearchSourceEvidenceChainIntegrityRow")
        if row.chain_id in seen:
            raise ValueError("rows must not contain duplicate chain_id")
        seen.add(row.chain_id)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.chain_id))


def _normalize_public_payload(
    items: Sequence[ResearchSourceEvidenceChainIntegrityPublicPayloadItem],
) -> tuple[ResearchSourceEvidenceChainIntegrityPublicPayloadItem, ...]:
    if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchSourceEvidenceChainIntegrityPublicPayloadItem] = []
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchSourceEvidenceChainIntegrityPublicPayloadItem:
            raise ValueError(
                "public_payload must contain "
                "ResearchSourceEvidenceChainIntegrityPublicPayloadItem",
            )
        if item.key in seen:
            raise ValueError("public_payload keys must be unique")
        seen.add(item.key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _validate_row_consistency(row: ResearchSourceEvidenceChainIntegrityRow) -> None:
    if row.linked_claim_count + row.unlinked_claim_count != row.evidence_link_count:
        raise ValueError("linked and unlinked counts must equal evidence_link_count")
    for count_name in (
        "linked_claim_count",
        "unlinked_claim_count",
        "stale_link_count",
        "contradiction_count",
        "manual_review_signal_count",
    ):
        if getattr(row, count_name) > row.evidence_link_count:
            raise ValueError(f"{count_name} cannot exceed evidence_link_count")


def _validate_report_consistency(report: ResearchSourceEvidenceChainIntegrityReport) -> None:
    if report.chain_count != _decimal_count(len(report.rows)):
        raise ValueError("chain_count must equal row count")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must equal passing rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must equal watched rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must equal blocked rows")
    if report.integrity_status != _report_status(report.rows):
        raise ValueError("integrity_status must match row statuses")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be public text")
    if len(value) > 256:
        raise ValueError(f"{field_name} must be short public text")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
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
    report: ResearchSourceEvidenceChainIntegrityReport,
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
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(path: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path} has unsafe public value")
    if "://" in lowered or lowered.startswith("www."):
        raise ValueError(f"{path} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_EVIDENCE_CHAIN_INTEGRITY_CONFIG_VERSION",
    "ResearchSourceEvidenceChainIntegrityConfig",
    "ResearchSourceEvidenceChainIntegrityLink",
    "ResearchSourceEvidenceChainIntegrityPublicPayloadItem",
    "ResearchSourceEvidenceChainIntegrityReport",
    "ResearchSourceEvidenceChainIntegrityRow",
    "build_research_source_evidence_chain_integrity_report",
)
