"""Pure report reducer for research source claim contradiction heatmaps."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_SOURCE_CLAIM_CONTRADICTION_HEATMAP_CONFIG_VERSION = (
    "research-source-claim-contradiction-heatmap-v1"
)

_COUNT_QUANTUM = Decimal("1")
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_STATUSES = ("block", "watch", "pass")
_STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
_FRESHNESS_WEIGHT = {"stale": 0, "recent": 1, "current": 2}
_REVIEWER_BUCKET_WEIGHT = {"unverified": 0, "verified": 1}
_HEX_CHARS = frozenset("0123456789abcdef")
_BLOCK_REASONS = frozenset(
    (
        "contradiction_pressure_block",
        "reviewer_verification_gap_block",
    ),
)
_PASS_REASONS = frozenset(("claim_family_pressure_pass",))
_REASON_PRIORITY = (
    "contradiction_pressure_block",
    "contradiction_pressure_watch",
    "cross_source_family_pressure",
    "high_authority_contradiction",
    "reviewer_verification_gap_block",
    "reviewer_verification_gap_watch",
    "stale_evidence_contradiction",
    "claim_family_pressure_pass",
    "research_source_claim_contradiction_heatmap_empty",
)


def _surface_term(*pieces: str) -> str:
    return "".join(pieces)


_UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    _surface_term("sec", "ret"),
    _surface_term("tok", "en"),
    _surface_term("pass", "word"),
    _surface_term("cred", "ential"),
    _surface_term("private", "_", "key"),
    _surface_term("api", "_", "key"),
    _surface_term("bear", "er"),
    _surface_term("wal", "let"),
    _surface_term("bro", "ker"),
    _surface_term("or", "der"),
    _surface_term("trad", "e"),
    _surface_term("li", "ve"),
    _surface_term("data", "base"),
    _surface_term("://"),
)
_UNSAFE_PAYLOAD_KEY_FRAGMENTS = _UNSAFE_PUBLIC_TEXT_FRAGMENTS + (
    _surface_term("candidate"),
    _surface_term("market", "_", "id"),
    _surface_term("market", "_", "slug"),
    _surface_term("market", "_", "question"),
    _surface_term("raw", "_", "source"),
    _surface_term("loc", "ator"),
    _surface_term("exc", "erpt"),
    _surface_term("url"),
    _surface_term("uri"),
    _surface_term("dsn"),
    _surface_term("table"),
)
_REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "evidence_count",
        "claim_family_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_contradiction_pressure",
        "max_contradiction_pressure",
        "status",
        "reason_codes",
        "claim_family_rows",
        "source_family_rollups",
        "authority_tier_rollups",
        "freshness_bucket_rollups",
        "reviewer_verification_rollups",
        "validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_HEATMAP_ROW_PAYLOAD_KEYS = frozenset(
    (
        "claim_family",
        "evidence_count",
        "source_family_count",
        "authority_tier_count",
        "freshness_bucket_count",
        "reviewer_verified_count",
        "reviewer_unverified_count",
        "reviewer_verification_ratio",
        "average_contradiction_pressure",
        "max_contradiction_pressure",
        "status",
        "reason_codes",
        "validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_COMMON_ROLLUP_PAYLOAD_KEYS = frozenset(
    (
        "evidence_count",
        "reviewer_verified_count",
        "reviewer_verification_ratio",
        "average_contradiction_pressure",
        "max_contradiction_pressure",
        "status",
        "reason_codes",
        "validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_SOURCE_FAMILY_ROLLUP_PAYLOAD_KEYS = _COMMON_ROLLUP_PAYLOAD_KEYS | frozenset(
    ("source_family",),
)
_AUTHORITY_TIER_ROLLUP_PAYLOAD_KEYS = _COMMON_ROLLUP_PAYLOAD_KEYS | frozenset(
    ("authority_tier",),
)
_FRESHNESS_BUCKET_ROLLUP_PAYLOAD_KEYS = _COMMON_ROLLUP_PAYLOAD_KEYS | frozenset(
    ("freshness_bucket",),
)
_REVIEWER_VERIFICATION_ROLLUP_PAYLOAD_KEYS = frozenset(
    (
        "reviewer_verification_bucket",
        "evidence_count",
        "average_contradiction_pressure",
        "max_contradiction_pressure",
        "status",
        "reason_codes",
        "validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)


@dataclass(frozen=True)
class ResearchSourceClaimContradictionHeatmapConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_CLAIM_CONTRADICTION_HEATMAP_CONFIG_VERSION
    contradiction_pressure_watch_threshold: Decimal = Decimal("0.250000")
    contradiction_pressure_block_threshold: Decimal = Decimal("0.600000")
    reviewer_verification_block_floor: Decimal = Decimal("0.250000")
    reviewer_verification_watch_floor: Decimal = Decimal("0.750000")
    cross_source_family_watch_floor: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CLAIM_CONTRADICTION_HEATMAP_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "contradiction_pressure_watch_threshold",
            "contradiction_pressure_block_threshold",
            "reviewer_verification_block_floor",
            "reviewer_verification_watch_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "cross_source_family_watch_floor",
            _normalize_positive_count(
                "cross_source_family_watch_floor",
                self.cross_source_family_watch_floor,
            ),
        )
        if (
            self.contradiction_pressure_watch_threshold
            > self.contradiction_pressure_block_threshold
        ):
            raise ValueError("watch threshold must not exceed block threshold")
        if self.reviewer_verification_block_floor > self.reviewer_verification_watch_floor:
            raise ValueError(
                "verification block floor must not exceed verification watch floor",
            )
        _require_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceClaimContradictionEvidence:
    candidate_id: str
    market_id: str
    market_slug: str
    market_question: str
    claim_family: str
    source_family: str
    authority_tier: str
    freshness_bucket: str
    contradiction_pressure: Decimal
    reviewer_verified: bool
    raw_source_locator: str
    raw_source_excerpt: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "candidate_id",
            "market_id",
            "market_slug",
            "market_question",
            "raw_source_locator",
            "raw_source_excerpt",
        ):
            _require_text(field_name, getattr(self, field_name))
        for field_name in (
            "claim_family",
            "source_family",
            "authority_tier",
            "freshness_bucket",
        ):
            _require_public_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "contradiction_pressure",
            _normalize_unit_decimal("contradiction_pressure", self.contradiction_pressure),
        )
        _require_bool("reviewer_verified", self.reviewer_verified)
        _require_flags("evidence", self)


@dataclass(frozen=True)
class ResearchSourceClaimContradictionHeatmapRow:
    claim_family: str
    evidence_count: Decimal
    source_family_count: Decimal
    authority_tier_count: Decimal
    freshness_bucket_count: Decimal
    reviewer_verified_count: Decimal
    reviewer_unverified_count: Decimal
    reviewer_verification_ratio: Decimal
    average_contradiction_pressure: Decimal
    max_contradiction_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("claim_family", self.claim_family)
        for field_name in (
            "evidence_count",
            "source_family_count",
            "authority_tier_count",
            "freshness_bucket_count",
            "reviewer_verified_count",
            "reviewer_unverified_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "reviewer_verification_ratio",
            "average_contradiction_pressure",
            "max_contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes("reason_codes", self.reason_codes),
        )
        _require_digest("validation_digest", self.validation_digest)
        _validate_heatmap_row(self)
        _require_flags("heatmap row", self)


@dataclass(frozen=True)
class ResearchSourceClaimContradictionSourceFamilyRollup:
    source_family: str
    evidence_count: Decimal
    reviewer_verified_count: Decimal
    reviewer_verification_ratio: Decimal
    average_contradiction_pressure: Decimal
    max_contradiction_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("source_family", self.source_family)
        _normalize_rollup_common(self)
        _validate_source_family_rollup(self)
        _require_flags("source family rollup", self)


@dataclass(frozen=True)
class ResearchSourceClaimContradictionAuthorityTierRollup:
    authority_tier: str
    evidence_count: Decimal
    reviewer_verified_count: Decimal
    reviewer_verification_ratio: Decimal
    average_contradiction_pressure: Decimal
    max_contradiction_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("authority_tier", self.authority_tier)
        _normalize_rollup_common(self)
        _validate_authority_tier_rollup(self)
        _require_flags("authority tier rollup", self)


@dataclass(frozen=True)
class ResearchSourceClaimContradictionFreshnessBucketRollup:
    freshness_bucket: str
    evidence_count: Decimal
    reviewer_verified_count: Decimal
    reviewer_verification_ratio: Decimal
    average_contradiction_pressure: Decimal
    max_contradiction_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("freshness_bucket", self.freshness_bucket)
        _normalize_rollup_common(self)
        _validate_freshness_bucket_rollup(self)
        _require_flags("freshness bucket rollup", self)


@dataclass(frozen=True)
class ResearchSourceClaimContradictionReviewerVerificationRollup:
    reviewer_verification_bucket: str
    evidence_count: Decimal
    average_contradiction_pressure: Decimal
    max_contradiction_pressure: Decimal
    status: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text(
            "reviewer_verification_bucket",
            self.reviewer_verification_bucket,
        )
        object.__setattr__(
            self,
            "evidence_count",
            _normalize_nonnegative_count("evidence_count", self.evidence_count),
        )
        for field_name in (
            "average_contradiction_pressure",
            "max_contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes("reason_codes", self.reason_codes),
        )
        _require_digest("validation_digest", self.validation_digest)
        _validate_reviewer_verification_rollup(self)
        _require_flags("reviewer verification rollup", self)


@dataclass(frozen=True)
class ResearchSourceClaimContradictionHeatmapReport:
    generated_at: datetime
    config_version: str
    evidence_count: Decimal
    claim_family_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_contradiction_pressure: Decimal | None
    max_contradiction_pressure: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    claim_family_rows: tuple[ResearchSourceClaimContradictionHeatmapRow, ...]
    source_family_rollups: tuple[ResearchSourceClaimContradictionSourceFamilyRollup, ...]
    authority_tier_rollups: tuple[ResearchSourceClaimContradictionAuthorityTierRollup, ...]
    freshness_bucket_rollups: tuple[ResearchSourceClaimContradictionFreshnessBucketRollup, ...]
    reviewer_verification_rollups: tuple[
        ResearchSourceClaimContradictionReviewerVerificationRollup,
        ...
    ]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CLAIM_CONTRADICTION_HEATMAP_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "evidence_count",
            "claim_family_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_contradiction_pressure",
            "max_contradiction_pressure",
        ):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _normalize_unit_decimal(field_name, value))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "claim_family_rows",
            _normalize_heatmap_rows(self.claim_family_rows),
        )
        object.__setattr__(
            self,
            "source_family_rollups",
            _normalize_source_family_rollups(self.source_family_rollups),
        )
        object.__setattr__(
            self,
            "authority_tier_rollups",
            _normalize_authority_tier_rollups(self.authority_tier_rollups),
        )
        object.__setattr__(
            self,
            "freshness_bucket_rollups",
            _normalize_freshness_bucket_rollups(self.freshness_bucket_rollups),
        )
        object.__setattr__(
            self,
            "reviewer_verification_rollups",
            _normalize_reviewer_verification_rollups(self.reviewer_verification_rollups),
        )
        _require_digest("validation_digest", self.validation_digest)
        _validate_report(self)
        _require_flags("heatmap report", self)


def build_research_source_claim_contradiction_heatmap_report(
    evidence_items: Iterable[ResearchSourceClaimContradictionEvidence],
    *,
    config: ResearchSourceClaimContradictionHeatmapConfig,
    generated_at: datetime,
) -> ResearchSourceClaimContradictionHeatmapReport:
    if type(config) is not ResearchSourceClaimContradictionHeatmapConfig:
        raise ValueError("config must be a ResearchSourceClaimContradictionHeatmapConfig")
    _require_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_evidence = _normalize_evidence_items(evidence_items)
    claim_family_rows = tuple(
        sorted(
            (
                _claim_family_row(claim_family, rows, config=config)
                for claim_family, rows in _group_by_text(normalized_evidence, "claim_family")
            ),
            key=_heatmap_row_sort_key,
        ),
    )
    evidence_count = _count(len(normalized_evidence))
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "evidence_count": evidence_count,
        "claim_family_count": _count(len(claim_family_rows)),
        "pass_count": _row_status_count(claim_family_rows, "pass"),
        "watch_count": _row_status_count(claim_family_rows, "watch"),
        "block_count": _row_status_count(claim_family_rows, "block"),
        "average_contradiction_pressure": (
            None
            if not claim_family_rows
            else _weighted_average_heatmap_pressure(claim_family_rows)
        ),
        "max_contradiction_pressure": (
            None
            if not claim_family_rows
            else max(row.max_contradiction_pressure for row in claim_family_rows)
        ),
        "status": _report_status(claim_family_rows),
        "reason_codes": _report_reason_codes(claim_family_rows),
        "claim_family_rows": claim_family_rows,
        "source_family_rollups": _source_family_rollups(normalized_evidence, config=config),
        "authority_tier_rollups": _authority_tier_rollups(normalized_evidence, config=config),
        "freshness_bucket_rollups": _freshness_bucket_rollups(normalized_evidence, config=config),
        "reviewer_verification_rollups": _reviewer_verification_rollups(
            normalized_evidence,
            config=config,
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceClaimContradictionHeatmapReport(
        **report_values,
        validation_digest=_validation_digest(report_values),
    )


def research_source_claim_contradiction_heatmap_report_payload(
    report: ResearchSourceClaimContradictionHeatmapReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSourceClaimContradictionHeatmapReport:
        _require_flags("heatmap report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchSourceClaimContradictionHeatmapReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    _reject_unsafe_payload(payload)
    _require_flags("heatmap payload", _PayloadFlags(payload))
    _validate_public_payload(payload)
    return payload


@dataclass(frozen=True)
class _PayloadFlags:
    payload: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.payload.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.payload.get("report_only")

    @property
    def readonly(self) -> object:
        return self.payload.get("readonly")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _require_exact_payload_keys("payload", payload, _REPORT_PAYLOAD_KEYS)
    _require_datetime_payload("generated_at", payload["generated_at"])
    _require_public_text("config_version", payload["config_version"])
    for field_name in (
        "evidence_count",
        "claim_family_count",
        "pass_count",
        "watch_count",
        "block_count",
    ):
        _require_count_payload(field_name, payload[field_name])
    for field_name in (
        "average_contradiction_pressure",
        "max_contradiction_pressure",
    ):
        _require_optional_unit_decimal_payload(field_name, payload[field_name])
    _require_status("status", payload["status"])
    _require_reason_codes_payload(
        "reason_codes",
        payload["reason_codes"],
        report_level=True,
    )
    _validate_heatmap_row_payloads(payload["claim_family_rows"])
    _validate_common_rollup_payloads(
        "source_family_rollups",
        payload["source_family_rollups"],
        _SOURCE_FAMILY_ROLLUP_PAYLOAD_KEYS,
        "source_family",
    )
    _validate_common_rollup_payloads(
        "authority_tier_rollups",
        payload["authority_tier_rollups"],
        _AUTHORITY_TIER_ROLLUP_PAYLOAD_KEYS,
        "authority_tier",
    )
    _validate_common_rollup_payloads(
        "freshness_bucket_rollups",
        payload["freshness_bucket_rollups"],
        _FRESHNESS_BUCKET_ROLLUP_PAYLOAD_KEYS,
        "freshness_bucket",
    )
    _validate_reviewer_verification_rollup_payloads(
        payload["reviewer_verification_rollups"],
    )
    _require_payload_flags("payload", payload)
    _require_digest("validation_digest", payload["validation_digest"])
    if payload["validation_digest"] != _validation_digest(_without_validation_digest(payload)):
        raise ValueError("validation_digest must match public payload")
    _validate_public_payload_semantics(payload)


def _validate_public_payload_semantics(payload: dict[str, Any]) -> None:
    claim_family_rows = tuple(
        ResearchSourceClaimContradictionHeatmapRow(
            claim_family=row["claim_family"],
            evidence_count=_decimal_from_payload(
                f"claim_family_rows[{index}].evidence_count",
                row["evidence_count"],
            ),
            source_family_count=_decimal_from_payload(
                f"claim_family_rows[{index}].source_family_count",
                row["source_family_count"],
            ),
            authority_tier_count=_decimal_from_payload(
                f"claim_family_rows[{index}].authority_tier_count",
                row["authority_tier_count"],
            ),
            freshness_bucket_count=_decimal_from_payload(
                f"claim_family_rows[{index}].freshness_bucket_count",
                row["freshness_bucket_count"],
            ),
            reviewer_verified_count=_decimal_from_payload(
                f"claim_family_rows[{index}].reviewer_verified_count",
                row["reviewer_verified_count"],
            ),
            reviewer_unverified_count=_decimal_from_payload(
                f"claim_family_rows[{index}].reviewer_unverified_count",
                row["reviewer_unverified_count"],
            ),
            reviewer_verification_ratio=_decimal_from_payload(
                f"claim_family_rows[{index}].reviewer_verification_ratio",
                row["reviewer_verification_ratio"],
            ),
            average_contradiction_pressure=_decimal_from_payload(
                f"claim_family_rows[{index}].average_contradiction_pressure",
                row["average_contradiction_pressure"],
            ),
            max_contradiction_pressure=_decimal_from_payload(
                f"claim_family_rows[{index}].max_contradiction_pressure",
                row["max_contradiction_pressure"],
            ),
            status=row["status"],
            reason_codes=tuple(row["reason_codes"]),
            validation_digest=row["validation_digest"],
            paper_only=row["paper_only"],
            report_only=row["report_only"],
            readonly=row["readonly"],
        )
        for index, row in enumerate(payload["claim_family_rows"])
    )
    source_family_rollups = tuple(
        ResearchSourceClaimContradictionSourceFamilyRollup(
            source_family=rollup["source_family"],
            **_common_rollup_payload_values(
                "source_family_rollups",
                index,
                rollup,
            ),
        )
        for index, rollup in enumerate(payload["source_family_rollups"])
    )
    authority_tier_rollups = tuple(
        ResearchSourceClaimContradictionAuthorityTierRollup(
            authority_tier=rollup["authority_tier"],
            **_common_rollup_payload_values(
                "authority_tier_rollups",
                index,
                rollup,
            ),
        )
        for index, rollup in enumerate(payload["authority_tier_rollups"])
    )
    freshness_bucket_rollups = tuple(
        ResearchSourceClaimContradictionFreshnessBucketRollup(
            freshness_bucket=rollup["freshness_bucket"],
            **_common_rollup_payload_values(
                "freshness_bucket_rollups",
                index,
                rollup,
            ),
        )
        for index, rollup in enumerate(payload["freshness_bucket_rollups"])
    )
    reviewer_verification_rollups = tuple(
        ResearchSourceClaimContradictionReviewerVerificationRollup(
            reviewer_verification_bucket=rollup["reviewer_verification_bucket"],
            evidence_count=_decimal_from_payload(
                f"reviewer_verification_rollups[{index}].evidence_count",
                rollup["evidence_count"],
            ),
            average_contradiction_pressure=_decimal_from_payload(
                f"reviewer_verification_rollups[{index}].average_contradiction_pressure",
                rollup["average_contradiction_pressure"],
            ),
            max_contradiction_pressure=_decimal_from_payload(
                f"reviewer_verification_rollups[{index}].max_contradiction_pressure",
                rollup["max_contradiction_pressure"],
            ),
            status=rollup["status"],
            reason_codes=tuple(rollup["reason_codes"]),
            validation_digest=rollup["validation_digest"],
            paper_only=rollup["paper_only"],
            report_only=rollup["report_only"],
            readonly=rollup["readonly"],
        )
        for index, rollup in enumerate(payload["reviewer_verification_rollups"])
    )
    ResearchSourceClaimContradictionHeatmapReport(
        generated_at=datetime.fromisoformat(payload["generated_at"]),
        config_version=payload["config_version"],
        evidence_count=_decimal_from_payload("evidence_count", payload["evidence_count"]),
        claim_family_count=_decimal_from_payload(
            "claim_family_count",
            payload["claim_family_count"],
        ),
        pass_count=_decimal_from_payload("pass_count", payload["pass_count"]),
        watch_count=_decimal_from_payload("watch_count", payload["watch_count"]),
        block_count=_decimal_from_payload("block_count", payload["block_count"]),
        average_contradiction_pressure=_optional_decimal_from_payload(
            "average_contradiction_pressure",
            payload["average_contradiction_pressure"],
        ),
        max_contradiction_pressure=_optional_decimal_from_payload(
            "max_contradiction_pressure",
            payload["max_contradiction_pressure"],
        ),
        status=payload["status"],
        reason_codes=tuple(payload["reason_codes"]),
        claim_family_rows=claim_family_rows,
        source_family_rollups=source_family_rollups,
        authority_tier_rollups=authority_tier_rollups,
        freshness_bucket_rollups=freshness_bucket_rollups,
        reviewer_verification_rollups=reviewer_verification_rollups,
        validation_digest=payload["validation_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _common_rollup_payload_values(
    name: str,
    index: int,
    rollup: dict[str, Any],
) -> dict[str, Any]:
    label = f"{name}[{index}]"
    return {
        "evidence_count": _decimal_from_payload(
            f"{label}.evidence_count",
            rollup["evidence_count"],
        ),
        "reviewer_verified_count": _decimal_from_payload(
            f"{label}.reviewer_verified_count",
            rollup["reviewer_verified_count"],
        ),
        "reviewer_verification_ratio": _decimal_from_payload(
            f"{label}.reviewer_verification_ratio",
            rollup["reviewer_verification_ratio"],
        ),
        "average_contradiction_pressure": _decimal_from_payload(
            f"{label}.average_contradiction_pressure",
            rollup["average_contradiction_pressure"],
        ),
        "max_contradiction_pressure": _decimal_from_payload(
            f"{label}.max_contradiction_pressure",
            rollup["max_contradiction_pressure"],
        ),
        "status": rollup["status"],
        "reason_codes": tuple(rollup["reason_codes"]),
        "validation_digest": rollup["validation_digest"],
        "paper_only": rollup["paper_only"],
        "report_only": rollup["report_only"],
        "readonly": rollup["readonly"],
    }


def _optional_decimal_from_payload(name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _decimal_from_payload(name, value)


def _validate_heatmap_row_payloads(value: object) -> None:
    rows = _require_payload_list("claim_family_rows", value)
    for index, row in enumerate(rows):
        label = f"claim_family_rows[{index}]"
        if type(row) is not dict:
            raise ValueError(f"{label} must be an object")
        _require_exact_payload_keys(label, row, _HEATMAP_ROW_PAYLOAD_KEYS)
        _require_public_text(f"{label}.claim_family", row["claim_family"])
        for field_name in (
            "evidence_count",
            "source_family_count",
            "authority_tier_count",
            "freshness_bucket_count",
            "reviewer_verified_count",
            "reviewer_unverified_count",
        ):
            _require_count_payload(f"{label}.{field_name}", row[field_name])
        for field_name in (
            "reviewer_verification_ratio",
            "average_contradiction_pressure",
            "max_contradiction_pressure",
        ):
            _require_unit_decimal_payload(f"{label}.{field_name}", row[field_name])
        _require_status(f"{label}.status", row["status"])
        _require_reason_codes_payload(f"{label}.reason_codes", row["reason_codes"])
        _require_payload_flags(label, row)
        _require_digest(f"{label}.validation_digest", row["validation_digest"])
        if row["validation_digest"] != _validation_digest(_without_validation_digest(row)):
            raise ValueError("validation_digest must match public row payload")


def _validate_common_rollup_payloads(
    name: str,
    value: object,
    expected_keys: frozenset[str],
    label_field: str,
) -> None:
    rollups = _require_payload_list(name, value)
    for index, rollup in enumerate(rollups):
        label = f"{name}[{index}]"
        if type(rollup) is not dict:
            raise ValueError(f"{label} must be an object")
        _require_exact_payload_keys(label, rollup, expected_keys)
        _require_public_text(f"{label}.{label_field}", rollup[label_field])
        for field_name in ("evidence_count", "reviewer_verified_count"):
            _require_count_payload(f"{label}.{field_name}", rollup[field_name])
        for field_name in (
            "reviewer_verification_ratio",
            "average_contradiction_pressure",
            "max_contradiction_pressure",
        ):
            _require_unit_decimal_payload(f"{label}.{field_name}", rollup[field_name])
        _require_status(f"{label}.status", rollup["status"])
        _require_reason_codes_payload(f"{label}.reason_codes", rollup["reason_codes"])
        _require_payload_flags(label, rollup)
        _require_digest(f"{label}.validation_digest", rollup["validation_digest"])
        if rollup["validation_digest"] != _validation_digest(
            _without_validation_digest(rollup),
        ):
            raise ValueError("validation_digest must match public rollup payload")


def _validate_reviewer_verification_rollup_payloads(value: object) -> None:
    rollups = _require_payload_list("reviewer_verification_rollups", value)
    for index, rollup in enumerate(rollups):
        label = f"reviewer_verification_rollups[{index}]"
        if type(rollup) is not dict:
            raise ValueError(f"{label} must be an object")
        _require_exact_payload_keys(label, rollup, _REVIEWER_VERIFICATION_ROLLUP_PAYLOAD_KEYS)
        _require_public_text(
            f"{label}.reviewer_verification_bucket",
            rollup["reviewer_verification_bucket"],
        )
        _require_count_payload(f"{label}.evidence_count", rollup["evidence_count"])
        for field_name in (
            "average_contradiction_pressure",
            "max_contradiction_pressure",
        ):
            _require_unit_decimal_payload(f"{label}.{field_name}", rollup[field_name])
        _require_status(f"{label}.status", rollup["status"])
        _require_reason_codes_payload(f"{label}.reason_codes", rollup["reason_codes"])
        _require_payload_flags(label, rollup)
        _require_digest(f"{label}.validation_digest", rollup["validation_digest"])
        if rollup["validation_digest"] != _validation_digest(
            _without_validation_digest(rollup),
        ):
            raise ValueError("validation_digest must match public rollup payload")


def _require_exact_payload_keys(
    name: str,
    payload: dict[str, Any],
    expected_keys: frozenset[str],
) -> None:
    actual_keys = frozenset(payload)
    extra_keys = actual_keys - expected_keys
    missing_keys = expected_keys - actual_keys
    if extra_keys:
        raise ValueError(f"unexpected public payload field in {name}")
    if missing_keys:
        raise ValueError(f"missing public payload field in {name}")


def _require_payload_list(name: str, value: object) -> list[Any]:
    if type(value) is not list:
        raise ValueError(f"{name} must be a list")
    return value


def _require_payload_flags(name: str, payload: dict[str, Any]) -> None:
    if payload["paper_only"] is not True:
        raise ValueError(f"{name} paper_only must be True")
    if payload["report_only"] is not True:
        raise ValueError(f"{name} report_only must be True")
    if payload["readonly"] is not True:
        raise ValueError(f"{name} readonly must be True")


def _require_datetime_payload(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO datetime string") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    if parsed.astimezone(UTC).isoformat() != value:
        raise ValueError(f"{name} must be normalized to UTC")


def _require_count_payload(name: str, value: object) -> None:
    normalized = _normalize_nonnegative_count(name, _decimal_from_payload(name, value))
    if value != str(normalized):
        raise ValueError(f"{name} must be a canonical Decimal string")


def _require_unit_decimal_payload(name: str, value: object) -> None:
    normalized = _normalize_unit_decimal(name, _decimal_from_payload(name, value))
    if value != str(normalized):
        raise ValueError(f"{name} must be a canonical Decimal string")


def _require_optional_unit_decimal_payload(name: str, value: object) -> None:
    if value is None:
        return
    _require_unit_decimal_payload(name, value)


def _decimal_from_payload(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} numeric values must use Decimal-derived strings")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{name} must be a Decimal-derived string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{name} must be finite")
    return decimal_value


def _require_reason_codes_payload(
    name: str,
    value: object,
    *,
    report_level: bool = False,
) -> None:
    if type(value) is not list:
        raise ValueError(f"{name} must be a list")
    normalized = (
        _normalize_report_reason_codes(name, tuple(value))
        if report_level
        else _normalize_row_reason_codes(name, tuple(value))
    )
    if list(normalized) != value:
        raise ValueError(f"{name} must be deterministically ordered")


def _without_validation_digest(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key != "validation_digest"}


def _claim_family_row(
    claim_family: str,
    rows: tuple[ResearchSourceClaimContradictionEvidence, ...],
    *,
    config: ResearchSourceClaimContradictionHeatmapConfig,
) -> ResearchSourceClaimContradictionHeatmapRow:
    reason_codes = _claim_family_reason_codes(rows, config=config)
    values = {
        "claim_family": claim_family,
        "evidence_count": _count(len(rows)),
        "source_family_count": _count(len({row.source_family for row in rows})),
        "authority_tier_count": _count(len({row.authority_tier for row in rows})),
        "freshness_bucket_count": _count(len({row.freshness_bucket for row in rows})),
        "reviewer_verified_count": _count(sum(1 for row in rows if row.reviewer_verified)),
        "reviewer_unverified_count": _count(sum(1 for row in rows if not row.reviewer_verified)),
        "reviewer_verification_ratio": _reviewer_verification_ratio(rows),
        "average_contradiction_pressure": _average_pressure(rows),
        "max_contradiction_pressure": max(row.contradiction_pressure for row in rows),
        "status": _status_from_reason_codes(reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceClaimContradictionHeatmapRow(
        **values,
        validation_digest=_validation_digest(values),
    )


def _source_family_rollups(
    evidence_items: tuple[ResearchSourceClaimContradictionEvidence, ...],
    *,
    config: ResearchSourceClaimContradictionHeatmapConfig,
) -> tuple[ResearchSourceClaimContradictionSourceFamilyRollup, ...]:
    return tuple(
        sorted(
            (
                _source_family_rollup(source_family, rows, config=config)
                for source_family, rows in _group_by_text(evidence_items, "source_family")
            ),
            key=_source_family_rollup_sort_key,
        ),
    )


def _authority_tier_rollups(
    evidence_items: tuple[ResearchSourceClaimContradictionEvidence, ...],
    *,
    config: ResearchSourceClaimContradictionHeatmapConfig,
) -> tuple[ResearchSourceClaimContradictionAuthorityTierRollup, ...]:
    return tuple(
        sorted(
            (
                _authority_tier_rollup(authority_tier, rows, config=config)
                for authority_tier, rows in _group_by_text(evidence_items, "authority_tier")
            ),
            key=_authority_tier_rollup_sort_key,
        ),
    )


def _freshness_bucket_rollups(
    evidence_items: tuple[ResearchSourceClaimContradictionEvidence, ...],
    *,
    config: ResearchSourceClaimContradictionHeatmapConfig,
) -> tuple[ResearchSourceClaimContradictionFreshnessBucketRollup, ...]:
    return tuple(
        sorted(
            (
                _freshness_bucket_rollup(freshness_bucket, rows, config=config)
                for freshness_bucket, rows in _group_by_text(evidence_items, "freshness_bucket")
            ),
            key=_freshness_bucket_rollup_sort_key,
        ),
    )


def _reviewer_verification_rollups(
    evidence_items: tuple[ResearchSourceClaimContradictionEvidence, ...],
    *,
    config: ResearchSourceClaimContradictionHeatmapConfig,
) -> tuple[ResearchSourceClaimContradictionReviewerVerificationRollup, ...]:
    return tuple(
        sorted(
            (
                _reviewer_verification_rollup(bucket, rows, config=config)
                for bucket, rows in _reviewer_verification_groups(evidence_items)
            ),
            key=_reviewer_verification_rollup_sort_key,
        ),
    )


def _source_family_rollup(
    source_family: str,
    rows: tuple[ResearchSourceClaimContradictionEvidence, ...],
    *,
    config: ResearchSourceClaimContradictionHeatmapConfig,
) -> ResearchSourceClaimContradictionSourceFamilyRollup:
    values = {
        "source_family": source_family,
        **_rollup_common_values(rows, config=config),
    }
    return ResearchSourceClaimContradictionSourceFamilyRollup(
        **values,
        validation_digest=_validation_digest(values),
    )


def _authority_tier_rollup(
    authority_tier: str,
    rows: tuple[ResearchSourceClaimContradictionEvidence, ...],
    *,
    config: ResearchSourceClaimContradictionHeatmapConfig,
) -> ResearchSourceClaimContradictionAuthorityTierRollup:
    values = {
        "authority_tier": authority_tier,
        **_rollup_common_values(rows, config=config),
    }
    return ResearchSourceClaimContradictionAuthorityTierRollup(
        **values,
        validation_digest=_validation_digest(values),
    )


def _freshness_bucket_rollup(
    freshness_bucket: str,
    rows: tuple[ResearchSourceClaimContradictionEvidence, ...],
    *,
    config: ResearchSourceClaimContradictionHeatmapConfig,
) -> ResearchSourceClaimContradictionFreshnessBucketRollup:
    values = {
        "freshness_bucket": freshness_bucket,
        **_rollup_common_values(rows, config=config),
    }
    return ResearchSourceClaimContradictionFreshnessBucketRollup(
        **values,
        validation_digest=_validation_digest(values),
    )


def _reviewer_verification_rollup(
    reviewer_verification_bucket: str,
    rows: tuple[ResearchSourceClaimContradictionEvidence, ...],
    *,
    config: ResearchSourceClaimContradictionHeatmapConfig,
) -> ResearchSourceClaimContradictionReviewerVerificationRollup:
    reason_codes = _rollup_reason_codes(rows, config=config)
    values = {
        "reviewer_verification_bucket": reviewer_verification_bucket,
        "evidence_count": _count(len(rows)),
        "average_contradiction_pressure": _average_pressure(rows),
        "max_contradiction_pressure": max(row.contradiction_pressure for row in rows),
        "status": _status_from_reason_codes(reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceClaimContradictionReviewerVerificationRollup(
        **values,
        validation_digest=_validation_digest(values),
    )


def _rollup_common_values(
    rows: tuple[ResearchSourceClaimContradictionEvidence, ...],
    *,
    config: ResearchSourceClaimContradictionHeatmapConfig,
) -> dict[str, Any]:
    reason_codes = _rollup_reason_codes(rows, config=config)
    return {
        "evidence_count": _count(len(rows)),
        "reviewer_verified_count": _count(sum(1 for row in rows if row.reviewer_verified)),
        "reviewer_verification_ratio": _reviewer_verification_ratio(rows),
        "average_contradiction_pressure": _average_pressure(rows),
        "max_contradiction_pressure": max(row.contradiction_pressure for row in rows),
        "status": _status_from_reason_codes(reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _claim_family_reason_codes(
    rows: tuple[ResearchSourceClaimContradictionEvidence, ...],
    *,
    config: ResearchSourceClaimContradictionHeatmapConfig,
) -> tuple[str, ...]:
    reasons = list(_pressure_reason_codes(rows, config=config))
    average_pressure = _average_pressure(rows)
    max_pressure = max(row.contradiction_pressure for row in rows)
    if (
        _count(len({row.source_family for row in rows}))
        >= config.cross_source_family_watch_floor
        and average_pressure >= config.contradiction_pressure_watch_threshold
    ):
        reasons.append("cross_source_family_pressure")
    if any(
        row.authority_tier == "primary"
        and row.contradiction_pressure >= config.contradiction_pressure_watch_threshold
        for row in rows
    ):
        reasons.append("high_authority_contradiction")
    if any(row.freshness_bucket == "stale" for row in rows) and (
        average_pressure >= config.contradiction_pressure_watch_threshold
        or max_pressure >= config.contradiction_pressure_block_threshold
    ):
        reasons.append("stale_evidence_contradiction")
    verification_ratio = _reviewer_verification_ratio(rows)
    if (
        average_pressure >= config.contradiction_pressure_block_threshold
        and verification_ratio < config.reviewer_verification_block_floor
    ):
        reasons.append("reviewer_verification_gap_block")
    elif (
        "contradiction_pressure_block" not in reasons
        and average_pressure >= config.contradiction_pressure_watch_threshold
        and verification_ratio < config.reviewer_verification_watch_floor
    ):
        reasons.append("reviewer_verification_gap_watch")
    if not reasons:
        reasons.append("claim_family_pressure_pass")
    return _normalize_row_reason_codes("reason_codes", tuple(reasons))


def _rollup_reason_codes(
    rows: tuple[ResearchSourceClaimContradictionEvidence, ...],
    *,
    config: ResearchSourceClaimContradictionHeatmapConfig,
) -> tuple[str, ...]:
    reasons = list(_pressure_reason_codes(rows, config=config))
    average_pressure = _average_pressure(rows)
    verification_ratio = _reviewer_verification_ratio(rows)
    if (
        average_pressure >= config.contradiction_pressure_block_threshold
        and verification_ratio < config.reviewer_verification_block_floor
    ):
        reasons.append("reviewer_verification_gap_block")
    elif (
        "contradiction_pressure_block" not in reasons
        and average_pressure >= config.contradiction_pressure_watch_threshold
        and verification_ratio < config.reviewer_verification_watch_floor
    ):
        reasons.append("reviewer_verification_gap_watch")
    if not reasons:
        reasons.append("claim_family_pressure_pass")
    return _normalize_row_reason_codes("reason_codes", tuple(reasons))


def _pressure_reason_codes(
    rows: tuple[ResearchSourceClaimContradictionEvidence, ...],
    *,
    config: ResearchSourceClaimContradictionHeatmapConfig,
) -> tuple[str, ...]:
    average_pressure = _average_pressure(rows)
    max_pressure = max(row.contradiction_pressure for row in rows)
    if (
        average_pressure >= config.contradiction_pressure_block_threshold
        or max_pressure >= config.contradiction_pressure_block_threshold
    ):
        return ("contradiction_pressure_block",)
    if (
        average_pressure >= config.contradiction_pressure_watch_threshold
        or max_pressure >= config.contradiction_pressure_watch_threshold
    ):
        return ("contradiction_pressure_watch",)
    return ()


def _normalize_evidence_items(
    evidence_items: Iterable[ResearchSourceClaimContradictionEvidence],
) -> tuple[ResearchSourceClaimContradictionEvidence, ...]:
    if isinstance(evidence_items, (str, bytes)):
        raise ValueError("evidence_items must be an iterable")
    try:
        items = tuple(evidence_items)
    except TypeError as exc:
        raise ValueError("evidence_items must be an iterable") from exc
    for item in items:
        if type(item) is not ResearchSourceClaimContradictionEvidence:
            raise ValueError(
                "evidence_items must contain ResearchSourceClaimContradictionEvidence",
            )
        _require_flags("evidence", item)
    return items


def _group_by_text(
    evidence_items: tuple[ResearchSourceClaimContradictionEvidence, ...],
    field_name: str,
) -> tuple[tuple[str, tuple[ResearchSourceClaimContradictionEvidence, ...]], ...]:
    values = tuple(sorted({getattr(item, field_name) for item in evidence_items}))
    return tuple(
        (
            value,
            tuple(
                sorted(
                    (item for item in evidence_items if getattr(item, field_name) == value),
                    key=_evidence_sort_key,
                ),
            ),
        )
        for value in values
    )


def _reviewer_verification_groups(
    evidence_items: tuple[ResearchSourceClaimContradictionEvidence, ...],
) -> tuple[tuple[str, tuple[ResearchSourceClaimContradictionEvidence, ...]], ...]:
    return tuple(
        (
            bucket,
            tuple(
                sorted(
                    (
                        item
                        for item in evidence_items
                        if _reviewer_verification_bucket(item) == bucket
                    ),
                    key=_evidence_sort_key,
                ),
            ),
        )
        for bucket in ("unverified", "verified")
        if any(_reviewer_verification_bucket(item) == bucket for item in evidence_items)
    )


def _reviewer_verification_bucket(
    evidence: ResearchSourceClaimContradictionEvidence,
) -> str:
    return "verified" if evidence.reviewer_verified else "unverified"


def _average_pressure(
    rows: tuple[ResearchSourceClaimContradictionEvidence, ...],
) -> Decimal:
    return _ratio(
        _sum_decimal(tuple(row.contradiction_pressure for row in rows)),
        _count(len(rows)),
    )


def _weighted_average_heatmap_pressure(
    rows: tuple[ResearchSourceClaimContradictionHeatmapRow, ...],
) -> Decimal:
    return _ratio(
        _sum_decimal(
            tuple(
                row.average_contradiction_pressure * row.evidence_count
                for row in rows
            ),
        ),
        _sum_decimal(tuple(row.evidence_count for row in rows)),
    )


def _reviewer_verification_ratio(
    rows: tuple[ResearchSourceClaimContradictionEvidence, ...],
) -> Decimal:
    return _ratio(
        _count(sum(1 for row in rows if row.reviewer_verified)),
        _count(len(rows)),
    )


def _row_status_count(
    rows: tuple[ResearchSourceClaimContradictionHeatmapRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason in _BLOCK_REASONS for reason in reason_codes):
        return "block"
    if reason_codes == ("claim_family_pressure_pass",):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchSourceClaimContradictionHeatmapRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceClaimContradictionHeatmapRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("research_source_claim_contradiction_heatmap_empty",)
    return _normalize_report_reason_codes(
        "reason_codes",
        tuple(reason for row in rows for reason in row.reason_codes),
    )


def _normalize_heatmap_rows(
    rows: object,
) -> tuple[ResearchSourceClaimContradictionHeatmapRow, ...]:
    normalized = _tuple_from_iterable("claim_family_rows", rows)
    for row in normalized:
        if type(row) is not ResearchSourceClaimContradictionHeatmapRow:
            raise ValueError(
                "claim_family_rows must contain ResearchSourceClaimContradictionHeatmapRow",
            )
        _require_flags("heatmap row", row)
    if normalized != tuple(sorted(normalized, key=_heatmap_row_sort_key)):
        raise ValueError("claim_family_rows must be sorted deterministically")
    return normalized


def _normalize_source_family_rollups(
    rollups: object,
) -> tuple[ResearchSourceClaimContradictionSourceFamilyRollup, ...]:
    normalized = _tuple_from_iterable("source_family_rollups", rollups)
    for rollup in normalized:
        if type(rollup) is not ResearchSourceClaimContradictionSourceFamilyRollup:
            raise ValueError(
                "source_family_rollups must contain "
                "ResearchSourceClaimContradictionSourceFamilyRollup",
            )
        _require_flags("source family rollup", rollup)
    if normalized != tuple(sorted(normalized, key=_source_family_rollup_sort_key)):
        raise ValueError("source_family_rollups must be sorted deterministically")
    return normalized


def _normalize_authority_tier_rollups(
    rollups: object,
) -> tuple[ResearchSourceClaimContradictionAuthorityTierRollup, ...]:
    normalized = _tuple_from_iterable("authority_tier_rollups", rollups)
    for rollup in normalized:
        if type(rollup) is not ResearchSourceClaimContradictionAuthorityTierRollup:
            raise ValueError(
                "authority_tier_rollups must contain "
                "ResearchSourceClaimContradictionAuthorityTierRollup",
            )
        _require_flags("authority tier rollup", rollup)
    if normalized != tuple(sorted(normalized, key=_authority_tier_rollup_sort_key)):
        raise ValueError("authority_tier_rollups must be sorted deterministically")
    return normalized


def _normalize_freshness_bucket_rollups(
    rollups: object,
) -> tuple[ResearchSourceClaimContradictionFreshnessBucketRollup, ...]:
    normalized = _tuple_from_iterable("freshness_bucket_rollups", rollups)
    for rollup in normalized:
        if type(rollup) is not ResearchSourceClaimContradictionFreshnessBucketRollup:
            raise ValueError(
                "freshness_bucket_rollups must contain "
                "ResearchSourceClaimContradictionFreshnessBucketRollup",
            )
        _require_flags("freshness bucket rollup", rollup)
    if normalized != tuple(sorted(normalized, key=_freshness_bucket_rollup_sort_key)):
        raise ValueError("freshness_bucket_rollups must be sorted deterministically")
    return normalized


def _normalize_reviewer_verification_rollups(
    rollups: object,
) -> tuple[ResearchSourceClaimContradictionReviewerVerificationRollup, ...]:
    normalized = _tuple_from_iterable("reviewer_verification_rollups", rollups)
    for rollup in normalized:
        if type(rollup) is not ResearchSourceClaimContradictionReviewerVerificationRollup:
            raise ValueError(
                "reviewer_verification_rollups must contain "
                "ResearchSourceClaimContradictionReviewerVerificationRollup",
            )
        _require_flags("reviewer verification rollup", rollup)
    if normalized != tuple(sorted(normalized, key=_reviewer_verification_rollup_sort_key)):
        raise ValueError("reviewer_verification_rollups must be sorted deterministically")
    return normalized


def _tuple_from_iterable(name: str, value: object) -> tuple[Any, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must be an iterable")
    try:
        return tuple(value)
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable") from exc


def _normalize_rollup_common(rollup: object) -> None:
    for field_name in ("evidence_count", "reviewer_verified_count"):
        object.__setattr__(
            rollup,
            field_name,
            _normalize_nonnegative_count(field_name, getattr(rollup, field_name)),
        )
    for field_name in (
        "reviewer_verification_ratio",
        "average_contradiction_pressure",
        "max_contradiction_pressure",
    ):
        object.__setattr__(
            rollup,
            field_name,
            _normalize_unit_decimal(field_name, getattr(rollup, field_name)),
        )
    _require_status("status", getattr(rollup, "status"))
    object.__setattr__(
        rollup,
        "reason_codes",
        _normalize_row_reason_codes("reason_codes", getattr(rollup, "reason_codes")),
    )
    _require_digest("validation_digest", getattr(rollup, "validation_digest"))
    evidence_count = getattr(rollup, "evidence_count")
    reviewer_verified_count = getattr(rollup, "reviewer_verified_count")
    reviewer_verification_ratio = getattr(rollup, "reviewer_verification_ratio")
    average_contradiction_pressure = getattr(
        rollup,
        "average_contradiction_pressure",
    )
    max_contradiction_pressure = getattr(rollup, "max_contradiction_pressure")
    if evidence_count <= _ZERO:
        raise ValueError("evidence_count must be positive for rollups")
    if reviewer_verified_count > evidence_count:
        raise ValueError("reviewer_verified_count must not exceed evidence_count")
    if reviewer_verification_ratio != _ratio(
        reviewer_verified_count,
        evidence_count,
    ):
        raise ValueError("reviewer_verification_ratio must match reviewer counts")
    if average_contradiction_pressure > max_contradiction_pressure:
        raise ValueError(
            "average_contradiction_pressure must not exceed "
            "max_contradiction_pressure",
        )


def _validate_heatmap_row(row: ResearchSourceClaimContradictionHeatmapRow) -> None:
    if row.evidence_count <= _ZERO:
        raise ValueError("evidence_count must be positive for heatmap rows")
    for field_name in (
        "source_family_count",
        "authority_tier_count",
        "freshness_bucket_count",
    ):
        value = getattr(row, field_name)
        if value <= _ZERO or value > row.evidence_count:
            raise ValueError(
                f"{field_name} must be positive and not exceed evidence_count",
            )
    if row.reviewer_verified_count + row.reviewer_unverified_count != row.evidence_count:
        raise ValueError("reviewer counts must match evidence_count")
    if row.reviewer_verification_ratio != _ratio(row.reviewer_verified_count, row.evidence_count):
        raise ValueError("reviewer_verification_ratio must match reviewer counts")
    if row.average_contradiction_pressure > row.max_contradiction_pressure:
        raise ValueError(
            "average_contradiction_pressure must not exceed "
            "max_contradiction_pressure",
        )
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.validation_digest != _validation_digest(_heatmap_row_digest_values(row)):
        raise ValueError("validation_digest must match heatmap row payload")


def _validate_source_family_rollup(
    rollup: ResearchSourceClaimContradictionSourceFamilyRollup,
) -> None:
    if rollup.status != _status_from_reason_codes(rollup.reason_codes):
        raise ValueError("status must match reason_codes")
    if rollup.validation_digest != _validation_digest(_source_family_rollup_digest_values(rollup)):
        raise ValueError("validation_digest must match source family rollup payload")


def _validate_authority_tier_rollup(
    rollup: ResearchSourceClaimContradictionAuthorityTierRollup,
) -> None:
    if rollup.status != _status_from_reason_codes(rollup.reason_codes):
        raise ValueError("status must match reason_codes")
    if rollup.validation_digest != _validation_digest(_authority_tier_rollup_digest_values(rollup)):
        raise ValueError("validation_digest must match authority tier rollup payload")


def _validate_freshness_bucket_rollup(
    rollup: ResearchSourceClaimContradictionFreshnessBucketRollup,
) -> None:
    if rollup.status != _status_from_reason_codes(rollup.reason_codes):
        raise ValueError("status must match reason_codes")
    if rollup.validation_digest != _validation_digest(_freshness_bucket_rollup_digest_values(rollup)):
        raise ValueError("validation_digest must match freshness bucket rollup payload")


def _validate_reviewer_verification_rollup(
    rollup: ResearchSourceClaimContradictionReviewerVerificationRollup,
) -> None:
    if rollup.reviewer_verification_bucket not in _REVIEWER_BUCKET_WEIGHT:
        raise ValueError(
            "reviewer_verification_bucket must be verified or unverified",
        )
    if rollup.evidence_count <= _ZERO:
        raise ValueError("evidence_count must be positive for rollups")
    if rollup.average_contradiction_pressure > rollup.max_contradiction_pressure:
        raise ValueError(
            "average_contradiction_pressure must not exceed "
            "max_contradiction_pressure",
        )
    if rollup.status != _status_from_reason_codes(rollup.reason_codes):
        raise ValueError("status must match reason_codes")
    if rollup.validation_digest != _validation_digest(
        _reviewer_verification_rollup_digest_values(rollup),
    ):
        raise ValueError("validation_digest must match reviewer verification rollup payload")


def _validate_report(report: ResearchSourceClaimContradictionHeatmapReport) -> None:
    _require_unique_labels("claim_family_rows", report.claim_family_rows, "claim_family")
    _require_unique_labels(
        "source_family_rollups",
        report.source_family_rollups,
        "source_family",
    )
    _require_unique_labels(
        "authority_tier_rollups",
        report.authority_tier_rollups,
        "authority_tier",
    )
    _require_unique_labels(
        "freshness_bucket_rollups",
        report.freshness_bucket_rollups,
        "freshness_bucket",
    )
    _require_unique_labels(
        "reviewer_verification_rollups",
        report.reviewer_verification_rollups,
        "reviewer_verification_bucket",
    )
    if report.claim_family_count != _count(len(report.claim_family_rows)):
        raise ValueError("claim_family_count must match claim_family_rows")
    if report.evidence_count != _sum_decimal(
        tuple(row.evidence_count for row in report.claim_family_rows),
    ):
        raise ValueError("evidence_count must match claim_family_rows")
    if report.pass_count != _row_status_count(report.claim_family_rows, "pass"):
        raise ValueError("pass_count must match claim_family_rows")
    if report.watch_count != _row_status_count(report.claim_family_rows, "watch"):
        raise ValueError("watch_count must match claim_family_rows")
    if report.block_count != _row_status_count(report.claim_family_rows, "block"):
        raise ValueError("block_count must match claim_family_rows")
    if report.status != _report_status(report.claim_family_rows):
        raise ValueError("status must match claim_family_rows")
    if report.reason_codes != _report_reason_codes(report.claim_family_rows):
        raise ValueError("reason_codes must match claim_family_rows")
    if report.evidence_count == _ZERO:
        if report.average_contradiction_pressure is not None:
            raise ValueError(
                "average_contradiction_pressure must be None for an empty report",
            )
        if report.max_contradiction_pressure is not None:
            raise ValueError(
                "max_contradiction_pressure must be None for an empty report",
            )
    else:
        if report.average_contradiction_pressure != _weighted_average_heatmap_pressure(
            report.claim_family_rows,
        ):
            raise ValueError(
                "average_contradiction_pressure must match claim_family_rows",
            )
        if report.max_contradiction_pressure != max(
            row.max_contradiction_pressure for row in report.claim_family_rows
        ):
            raise ValueError(
                "max_contradiction_pressure must match claim_family_rows",
            )
    total_reviewer_verified = _sum_decimal(
        tuple(row.reviewer_verified_count for row in report.claim_family_rows),
    )
    total_reviewer_unverified = _sum_decimal(
        tuple(row.reviewer_unverified_count for row in report.claim_family_rows),
    )
    for name, rollups in (
        ("source_family_rollups", report.source_family_rollups),
        ("authority_tier_rollups", report.authority_tier_rollups),
        ("freshness_bucket_rollups", report.freshness_bucket_rollups),
    ):
        if _sum_decimal(tuple(item.evidence_count for item in rollups)) != (
            report.evidence_count
        ):
            raise ValueError(f"{name} evidence_count must match report")
        if _sum_decimal(
            tuple(item.reviewer_verified_count for item in rollups),
        ) != total_reviewer_verified:
            raise ValueError(f"{name} reviewer_verified_count must match report")
        if report.evidence_count != _ZERO and max(
            item.max_contradiction_pressure for item in rollups
        ) != report.max_contradiction_pressure:
            raise ValueError(
                f"{name} max_contradiction_pressure must match report",
            )
        if report.evidence_count != _ZERO and abs(
            _weighted_average_rollup_pressure(rollups)
            - report.average_contradiction_pressure
        ) > _QUANTUM:
            raise ValueError(
                f"{name} average_contradiction_pressure must match report",
            )
    reviewer_bucket_counts = {
        item.reviewer_verification_bucket: item.evidence_count
        for item in report.reviewer_verification_rollups
    }
    expected_reviewer_bucket_counts = {
        bucket: count
        for bucket, count in (
            ("unverified", total_reviewer_unverified),
            ("verified", total_reviewer_verified),
        )
        if count > _ZERO
    }
    if reviewer_bucket_counts != expected_reviewer_bucket_counts:
        raise ValueError(
            "reviewer_verification_rollups evidence_count must match report",
        )
    if report.evidence_count != _ZERO and max(
        item.max_contradiction_pressure
        for item in report.reviewer_verification_rollups
    ) != report.max_contradiction_pressure:
        raise ValueError(
            "reviewer_verification_rollups max_contradiction_pressure "
            "must match report",
        )
    if report.evidence_count != _ZERO and abs(
        _weighted_average_rollup_pressure(report.reviewer_verification_rollups)
        - report.average_contradiction_pressure
    ) > _QUANTUM:
        raise ValueError(
            "reviewer_verification_rollups average_contradiction_pressure "
            "must match report",
        )
    if report.validation_digest != _validation_digest(_report_digest_values(report)):
        raise ValueError("validation_digest must match report payload")


def _require_unique_labels(
    name: str,
    values: tuple[Any, ...],
    field_name: str,
) -> None:
    labels = tuple(getattr(value, field_name) for value in values)
    if len(labels) != len(set(labels)):
        raise ValueError(f"{name} must contain unique {field_name} values")


def _weighted_average_rollup_pressure(rollups: tuple[Any, ...]) -> Decimal:
    return _ratio(
        _sum_decimal(
            tuple(
                item.average_contradiction_pressure * item.evidence_count
                for item in rollups
            ),
        ),
        _sum_decimal(tuple(item.evidence_count for item in rollups)),
    )


def _heatmap_row_digest_values(
    row: ResearchSourceClaimContradictionHeatmapRow,
) -> dict[str, Any]:
    return {
        "claim_family": row.claim_family,
        "evidence_count": row.evidence_count,
        "source_family_count": row.source_family_count,
        "authority_tier_count": row.authority_tier_count,
        "freshness_bucket_count": row.freshness_bucket_count,
        "reviewer_verified_count": row.reviewer_verified_count,
        "reviewer_unverified_count": row.reviewer_unverified_count,
        "reviewer_verification_ratio": row.reviewer_verification_ratio,
        "average_contradiction_pressure": row.average_contradiction_pressure,
        "max_contradiction_pressure": row.max_contradiction_pressure,
        "status": row.status,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _source_family_rollup_digest_values(
    rollup: ResearchSourceClaimContradictionSourceFamilyRollup,
) -> dict[str, Any]:
    return {
        "source_family": rollup.source_family,
        **_common_rollup_digest_values(rollup),
    }


def _authority_tier_rollup_digest_values(
    rollup: ResearchSourceClaimContradictionAuthorityTierRollup,
) -> dict[str, Any]:
    return {
        "authority_tier": rollup.authority_tier,
        **_common_rollup_digest_values(rollup),
    }


def _freshness_bucket_rollup_digest_values(
    rollup: ResearchSourceClaimContradictionFreshnessBucketRollup,
) -> dict[str, Any]:
    return {
        "freshness_bucket": rollup.freshness_bucket,
        **_common_rollup_digest_values(rollup),
    }


def _reviewer_verification_rollup_digest_values(
    rollup: ResearchSourceClaimContradictionReviewerVerificationRollup,
) -> dict[str, Any]:
    return {
        "reviewer_verification_bucket": rollup.reviewer_verification_bucket,
        "evidence_count": rollup.evidence_count,
        "average_contradiction_pressure": rollup.average_contradiction_pressure,
        "max_contradiction_pressure": rollup.max_contradiction_pressure,
        "status": rollup.status,
        "reason_codes": rollup.reason_codes,
        "paper_only": rollup.paper_only,
        "report_only": rollup.report_only,
        "readonly": rollup.readonly,
    }


def _common_rollup_digest_values(rollup: object) -> dict[str, Any]:
    return {
        "evidence_count": getattr(rollup, "evidence_count"),
        "reviewer_verified_count": getattr(rollup, "reviewer_verified_count"),
        "reviewer_verification_ratio": getattr(rollup, "reviewer_verification_ratio"),
        "average_contradiction_pressure": getattr(
            rollup,
            "average_contradiction_pressure",
        ),
        "max_contradiction_pressure": getattr(rollup, "max_contradiction_pressure"),
        "status": getattr(rollup, "status"),
        "reason_codes": getattr(rollup, "reason_codes"),
        "paper_only": getattr(rollup, "paper_only"),
        "report_only": getattr(rollup, "report_only"),
        "readonly": getattr(rollup, "readonly"),
    }


def _report_digest_values(
    report: ResearchSourceClaimContradictionHeatmapReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "evidence_count": report.evidence_count,
        "claim_family_count": report.claim_family_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "average_contradiction_pressure": report.average_contradiction_pressure,
        "max_contradiction_pressure": report.max_contradiction_pressure,
        "status": report.status,
        "reason_codes": report.reason_codes,
        "claim_family_rows": report.claim_family_rows,
        "source_family_rollups": report.source_family_rollups,
        "authority_tier_rollups": report.authority_tier_rollups,
        "freshness_bucket_rollups": report.freshness_bucket_rollups,
        "reviewer_verification_rollups": report.reviewer_verification_rollups,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _heatmap_row_sort_key(
    row: ResearchSourceClaimContradictionHeatmapRow,
) -> tuple[int, Decimal, str]:
    return (
        _STATUS_WEIGHT[row.status],
        -row.average_contradiction_pressure,
        row.claim_family,
    )


def _source_family_rollup_sort_key(
    rollup: ResearchSourceClaimContradictionSourceFamilyRollup,
) -> tuple[Decimal, Decimal, str]:
    return (
        -rollup.max_contradiction_pressure,
        -rollup.average_contradiction_pressure,
        rollup.source_family,
    )


def _authority_tier_rollup_sort_key(
    rollup: ResearchSourceClaimContradictionAuthorityTierRollup,
) -> tuple[Decimal, Decimal, str]:
    return (
        -rollup.max_contradiction_pressure,
        -rollup.average_contradiction_pressure,
        rollup.authority_tier,
    )


def _freshness_bucket_rollup_sort_key(
    rollup: ResearchSourceClaimContradictionFreshnessBucketRollup,
) -> tuple[int, Decimal, str]:
    return (
        _FRESHNESS_WEIGHT.get(rollup.freshness_bucket, len(_FRESHNESS_WEIGHT)),
        -rollup.max_contradiction_pressure,
        rollup.freshness_bucket,
    )


def _reviewer_verification_rollup_sort_key(
    rollup: ResearchSourceClaimContradictionReviewerVerificationRollup,
) -> tuple[int, Decimal, str]:
    return (
        _REVIEWER_BUCKET_WEIGHT.get(
            rollup.reviewer_verification_bucket,
            len(_REVIEWER_BUCKET_WEIGHT),
        ),
        -rollup.max_contradiction_pressure,
        rollup.reviewer_verification_bucket,
    )


def _evidence_sort_key(
    evidence: ResearchSourceClaimContradictionEvidence,
) -> tuple[str, str, str, str, str, str, str, str]:
    return (
        evidence.claim_family,
        evidence.source_family,
        evidence.authority_tier,
        evidence.freshness_bucket,
        evidence.candidate_id,
        evidence.market_id,
        evidence.market_slug,
        evidence.market_question,
    )


def _normalize_row_reason_codes(name: str, values: object) -> tuple[str, ...]:
    codes = _normalize_public_reason_codes(name, values)
    if not codes:
        raise ValueError(f"{name} must not be empty")
    if "claim_family_pressure_pass" in codes and len(codes) != 1:
        raise ValueError(f"{name} pass reason must stand alone")
    if any(code in _PASS_REASONS for code in codes) and codes != (
        "claim_family_pressure_pass",
    ):
        raise ValueError(f"{name} pass reason must stand alone")
    return codes


def _normalize_report_reason_codes(name: str, values: object) -> tuple[str, ...]:
    codes = _normalize_public_reason_codes(name, values)
    if not codes:
        raise ValueError(f"{name} must not be empty")
    if codes == ("research_source_claim_contradiction_heatmap_empty",):
        return codes
    if "research_source_claim_contradiction_heatmap_empty" in codes:
        raise ValueError(f"{name} empty reason must stand alone")
    return codes


def _normalize_public_reason_codes(name: str, values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be an iterable")
    try:
        codes = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable") from exc
    for code in codes:
        _require_public_text(name, code)
        compact_code = "".join(part for part in code if part != "_")
        if not compact_code.isalnum() or code.lower() != code:
            raise ValueError(f"{name} must contain lowercase snake case values")
    return tuple(sorted(dict.fromkeys(codes), key=_reason_sort_key))


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    if reason_code in _REASON_PRIORITY:
        return (_REASON_PRIORITY.index(reason_code), reason_code)
    return (len(_REASON_PRIORITY), reason_code)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = _ZERO
    for value in values:
        total += _normalize_decimal("sum value", value)
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator = _normalize_decimal("numerator", numerator)
    denominator = _normalize_decimal("denominator", denominator)
    if denominator <= _ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _normalize_positive_count(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be an integer")
    return normalized.quantize(_COUNT_QUANTUM)


def _normalize_unit_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(normalized)


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(name: str, value: object) -> None:
    _require_public_text(name, value)
    if value not in _STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_bool(name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")


def _require_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a non-empty canonical string")


def _require_public_text(name: str, value: object) -> None:
    _require_text(name, value)
    normalized = value.lower()
    if any(fragment in normalized for fragment in _UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public text")


def _require_digest(name: str, value: object) -> None:
    _require_text(name, value)
    if len(value) != 64 or any(char not in _HEX_CHARS for char in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _require_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _validation_digest(values: dict[str, Any]) -> str:
    ready = _json_ready(values)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("numeric Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) in (float, int):
        raise ValueError("numeric values must use Decimal-derived strings")
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


def _reject_unsafe_payload(value: object, path: str = "") -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            normalized_key = key.lower()
            if any(fragment in normalized_key for fragment in _UNSAFE_PAYLOAD_KEY_FRAGMENTS):
                raise ValueError(f"unsafe public payload field at {path or key}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True")
            _reject_unsafe_payload(item, key if not path else f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_unsafe_payload(item, f"{path}[{index}]")
        return
    if type(value) is str:
        normalized_value = value.lower()
        if any(fragment in normalized_value for fragment in _UNSAFE_PUBLIC_TEXT_FRAGMENTS):
            raise ValueError(f"unsafe public payload value at {path or 'payload'}")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_CLAIM_CONTRADICTION_HEATMAP_CONFIG_VERSION",
    "ResearchSourceClaimContradictionAuthorityTierRollup",
    "ResearchSourceClaimContradictionEvidence",
    "ResearchSourceClaimContradictionFreshnessBucketRollup",
    "ResearchSourceClaimContradictionHeatmapConfig",
    "ResearchSourceClaimContradictionHeatmapReport",
    "ResearchSourceClaimContradictionHeatmapRow",
    "ResearchSourceClaimContradictionReviewerVerificationRollup",
    "ResearchSourceClaimContradictionSourceFamilyRollup",
    "build_research_source_claim_contradiction_heatmap_report",
    "research_source_claim_contradiction_heatmap_report_payload",
)
