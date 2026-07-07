"""Pure Phase 1 external corroboration gap report."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_PACKET_EXTERNAL_CORROBORATION_GAP_V2_CONFIG_VERSION = (
    "research-packet-external-corroboration-gap-v2"
)

Q = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SCORE_FACTOR_COUNT = Decimal("6.000000")

REPORT_STATUSES = ("pass", "watch", "blocked")
OFFICIAL_SOURCE_STATUSES = ("missing", "present")
SOURCE_AGE_STATUSES = ("missing", "fresh", "watch", "stale")
CONTRADICTION_STATUSES = ("none", "elevated", "severe")
MARKET_MOVE_STATUSES = ("quiet", "material", "large")
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}

PASS_REASON = "research_packet_external_corroboration_gap_v2_passed"
MISSING_EXTERNAL_CORROBORATION_REASON = (
    "research_packet_external_corroboration_gap_v2_missing_external_corroboration"
)
WEAK_INDEPENDENT_FAMILY_REASON = (
    "research_packet_external_corroboration_gap_v2_weak_independent_family_count"
)
MISSING_OFFICIAL_SOURCE_REASON = (
    "research_packet_external_corroboration_gap_v2_missing_official_source"
)
HIGH_DUPLICATE_SOURCE_RATIO_REASON = (
    "research_packet_external_corroboration_gap_v2_high_duplicate_source_ratio"
)
SOURCE_AGE_MISSING_REASON = (
    "research_packet_external_corroboration_gap_v2_source_age_missing"
)
SOURCE_AGE_WATCH_REASON = "research_packet_external_corroboration_gap_v2_source_age_watch"
SOURCE_AGE_STALE_REASON = "research_packet_external_corroboration_gap_v2_source_age_stale"
CONTRADICTION_ELEVATED_REASON = (
    "research_packet_external_corroboration_gap_v2_contradiction_elevated"
)
CONTRADICTION_SEVERE_REASON = (
    "research_packet_external_corroboration_gap_v2_contradiction_severe"
)
UNEXPLAINED_MARKET_MOVE_MATERIAL_REASON = (
    "research_packet_external_corroboration_gap_v2_unexplained_market_move_material"
)
UNEXPLAINED_MARKET_MOVE_LARGE_REASON = (
    "research_packet_external_corroboration_gap_v2_unexplained_market_move_large"
)

ROW_REASON_CODES = (
    PASS_REASON,
    MISSING_EXTERNAL_CORROBORATION_REASON,
    WEAK_INDEPENDENT_FAMILY_REASON,
    MISSING_OFFICIAL_SOURCE_REASON,
    HIGH_DUPLICATE_SOURCE_RATIO_REASON,
    SOURCE_AGE_MISSING_REASON,
    SOURCE_AGE_WATCH_REASON,
    SOURCE_AGE_STALE_REASON,
    CONTRADICTION_ELEVATED_REASON,
    CONTRADICTION_SEVERE_REASON,
    UNEXPLAINED_MARKET_MOVE_MATERIAL_REASON,
    UNEXPLAINED_MARKET_MOVE_LARGE_REASON,
)
ROW_REASON_SET = frozenset(ROW_REASON_CODES)
REPORT_REASON_CODES = ROW_REASON_CODES
REPORT_REASON_SET = frozenset(REPORT_REASON_CODES)
BLOCKED_REASONS = frozenset(
    (
        MISSING_EXTERNAL_CORROBORATION_REASON,
        MISSING_OFFICIAL_SOURCE_REASON,
        SOURCE_AGE_MISSING_REASON,
        SOURCE_AGE_STALE_REASON,
        CONTRADICTION_SEVERE_REASON,
        UNEXPLAINED_MARKET_MOVE_LARGE_REASON,
    ),
)

REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "report_status",
        "candidate_count",
        "pass_count",
        "watch_count",
        "blocked_count",
        "attention_count",
        "attention_ratio",
        "weak_independent_family_count",
        "missing_official_source_count",
        "high_duplicate_source_ratio_count",
        "source_age_gap_count",
        "stale_source_age_count",
        "contradiction_gap_count",
        "severe_contradiction_count",
        "unexplained_market_move_count",
        "large_market_move_count",
        "max_duplicate_source_ratio",
        "max_contradiction_severity",
        "max_market_move_abs",
        "min_independent_family_count_observed",
        "min_independent_family_count",
        "fresh_source_max_age_seconds",
        "stale_source_age_seconds",
        "max_duplicate_source_ratio_threshold",
        "elevated_contradiction_threshold",
        "severe_contradiction_threshold",
        "material_market_move_threshold",
        "large_market_move_threshold",
        "reason_codes",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_FIELDS = frozenset(
    (
        "gap_rank",
        "packet_id",
        "claim_id",
        "market_id",
        "captured_at",
        "source_count",
        "independent_family_count",
        "official_source_count",
        "official_source_status",
        "duplicate_source_count",
        "duplicate_source_ratio",
        "latest_source_age_seconds",
        "source_age_status",
        "contradiction_severity",
        "contradiction_status",
        "market_move_abs",
        "market_move_status",
        "market_move_explained",
        "gap_score",
        "gap_status",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)


def _join(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _join("li", "ve"),
        _join("au", "th"),
        _join("wal", "let"),
        _join("or", "der"),
        _join("net", "work"),
        _join("data", "base"),
        _join("per", "sist"),
        _join("sign", "ing"),
        _join("muta", "tion"),
        _join("b", "uy"),
        _join("se", "ll"),
        _join("tra", "de"),
    ),
)


@dataclass(frozen=True)
class ResearchPacketExternalCorroborationGapV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_EXTERNAL_CORROBORATION_GAP_V2_CONFIG_VERSION
    )
    min_independent_family_count: Decimal = Decimal("2.000000")
    fresh_source_max_age_seconds: Decimal = Decimal("3600.000000")
    stale_source_age_seconds: Decimal = Decimal("86400.000000")
    max_duplicate_source_ratio: Decimal = Decimal("0.500000")
    elevated_contradiction_threshold: Decimal = Decimal("0.250000")
    severe_contradiction_threshold: Decimal = Decimal("0.750000")
    material_market_move_threshold: Decimal = Decimal("0.050000")
    large_market_move_threshold: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "ResearchPacketExternalCorroborationGapV2Config does not support subclassing",
        )

    def __post_init__(self) -> None:
        _config_version(self.config_version)
        object.__setattr__(
            self,
            "min_independent_family_count",
            _count_positive(
                "min_independent_family_count",
                self.min_independent_family_count,
            ),
        )
        for field_name in ("fresh_source_max_age_seconds", "stale_source_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _decimal_positive(field_name, getattr(self, field_name)),
            )
        if self.fresh_source_max_age_seconds > self.stale_source_age_seconds:
            raise ValueError(
                "fresh_source_max_age_seconds must not exceed stale_source_age_seconds",
            )
        for field_name in (
            "max_duplicate_source_ratio",
            "elevated_contradiction_threshold",
            "severe_contradiction_threshold",
            "material_market_move_threshold",
            "large_market_move_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _ratio(field_name, getattr(self, field_name)),
            )
        if self.elevated_contradiction_threshold > self.severe_contradiction_threshold:
            raise ValueError(
                "elevated_contradiction_threshold must not exceed "
                "severe_contradiction_threshold",
            )
        if self.material_market_move_threshold > self.large_market_move_threshold:
            raise ValueError(
                "material_market_move_threshold must not exceed "
                "large_market_move_threshold",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload(self)


@dataclass(frozen=True)
class ResearchPacketExternalCorroborationGapV2Candidate:
    packet_id: str
    claim_id: str
    market_id: str
    captured_at: datetime
    source_count: Decimal
    independent_family_count: Decimal
    official_source_count: Decimal
    latest_source_age_seconds: Decimal | None
    contradiction_severity: Decimal
    market_move_abs: Decimal
    market_move_explained: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "ResearchPacketExternalCorroborationGapV2Candidate does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        for field_name in ("packet_id", "claim_id", "market_id"):
            _safe_text(field_name, getattr(self, field_name))
        object.__setattr__(self, "captured_at", _as_utc("captured_at", self.captured_at))
        for field_name in (
            "source_count",
            "independent_family_count",
            "official_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _count_nonnegative(field_name, getattr(self, field_name)),
            )
        if self.independent_family_count > self.source_count:
            raise ValueError("independent_family_count must not exceed source_count")
        if self.official_source_count > self.source_count:
            raise ValueError("official_source_count must not exceed source_count")
        object.__setattr__(
            self,
            "latest_source_age_seconds",
            _optional_decimal_nonnegative(
                "latest_source_age_seconds",
                self.latest_source_age_seconds,
            ),
        )
        if self.source_count == ZERO and self.latest_source_age_seconds is not None:
            raise ValueError("latest_source_age_seconds must be absent without sources")
        object.__setattr__(
            self,
            "contradiction_severity",
            _ratio("contradiction_severity", self.contradiction_severity),
        )
        object.__setattr__(
            self,
            "market_move_abs",
            _ratio("market_move_abs", self.market_move_abs),
        )
        _require_bool("market_move_explained", self.market_move_explained)
        _require_hard_flags("candidate", self)
        _reject_unsafe_public_payload(self)


@dataclass(frozen=True)
class ResearchPacketExternalCorroborationGapV2Row:
    gap_rank: Decimal
    packet_id: str
    claim_id: str
    market_id: str
    captured_at: datetime
    source_count: Decimal
    independent_family_count: Decimal
    official_source_count: Decimal
    official_source_status: str
    duplicate_source_count: Decimal
    duplicate_source_ratio: Decimal
    latest_source_age_seconds: Decimal | None
    source_age_status: str
    contradiction_severity: Decimal
    contradiction_status: str
    market_move_abs: Decimal
    market_move_status: str
    market_move_explained: bool
    gap_score: Decimal
    gap_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "ResearchPacketExternalCorroborationGapV2Row does not support subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(self, "gap_rank", _count_positive("gap_rank", self.gap_rank))
        for field_name in ("packet_id", "claim_id", "market_id"):
            _safe_text(field_name, getattr(self, field_name))
        object.__setattr__(self, "captured_at", _as_utc("captured_at", self.captured_at))
        for field_name in (
            "source_count",
            "independent_family_count",
            "official_source_count",
            "duplicate_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _count_nonnegative(field_name, getattr(self, field_name)),
            )
        _member(
            "official_source_status",
            self.official_source_status,
            OFFICIAL_SOURCE_STATUSES,
        )
        object.__setattr__(
            self,
            "duplicate_source_ratio",
            _ratio("duplicate_source_ratio", self.duplicate_source_ratio),
        )
        object.__setattr__(
            self,
            "latest_source_age_seconds",
            _optional_decimal_nonnegative(
                "latest_source_age_seconds",
                self.latest_source_age_seconds,
            ),
        )
        _member("source_age_status", self.source_age_status, SOURCE_AGE_STATUSES)
        object.__setattr__(
            self,
            "contradiction_severity",
            _ratio("contradiction_severity", self.contradiction_severity),
        )
        _member(
            "contradiction_status",
            self.contradiction_status,
            CONTRADICTION_STATUSES,
        )
        object.__setattr__(
            self,
            "market_move_abs",
            _ratio("market_move_abs", self.market_move_abs),
        )
        _member("market_move_status", self.market_move_status, MARKET_MOVE_STATUSES)
        _require_bool("market_move_explained", self.market_move_explained)
        object.__setattr__(self, "gap_score", _ratio("gap_score", self.gap_score))
        _member("gap_status", self.gap_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload(self)
        _validate_row(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _hex_digest("derived_validation_digest", self.derived_validation_digest),
            )
            _validate_row_digest(self)


@dataclass(frozen=True)
class ResearchPacketExternalCorroborationGapV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    attention_count: Decimal
    attention_ratio: Decimal
    weak_independent_family_count: Decimal
    missing_official_source_count: Decimal
    high_duplicate_source_ratio_count: Decimal
    source_age_gap_count: Decimal
    stale_source_age_count: Decimal
    contradiction_gap_count: Decimal
    severe_contradiction_count: Decimal
    unexplained_market_move_count: Decimal
    large_market_move_count: Decimal
    max_duplicate_source_ratio: Decimal
    max_contradiction_severity: Decimal
    max_market_move_abs: Decimal
    min_independent_family_count_observed: Decimal
    min_independent_family_count: Decimal
    fresh_source_max_age_seconds: Decimal
    stale_source_age_seconds: Decimal
    max_duplicate_source_ratio_threshold: Decimal
    elevated_contradiction_threshold: Decimal
    severe_contradiction_threshold: Decimal
    material_market_move_threshold: Decimal
    large_market_move_threshold: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchPacketExternalCorroborationGapV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "ResearchPacketExternalCorroborationGapV2Report does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _config_version(self.config_version)
        _member("report_status", self.report_status, REPORT_STATUSES)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "attention_count",
            "weak_independent_family_count",
            "missing_official_source_count",
            "high_duplicate_source_ratio_count",
            "source_age_gap_count",
            "stale_source_age_count",
            "contradiction_gap_count",
            "severe_contradiction_count",
            "unexplained_market_move_count",
            "large_market_move_count",
            "min_independent_family_count_observed",
            "min_independent_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _count_nonnegative(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "attention_ratio",
            "max_duplicate_source_ratio",
            "max_contradiction_severity",
            "max_market_move_abs",
            "max_duplicate_source_ratio_threshold",
            "elevated_contradiction_threshold",
            "severe_contradiction_threshold",
            "material_market_move_threshold",
            "large_market_move_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("fresh_source_max_age_seconds", "stale_source_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _decimal_nonnegative(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload(self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _hex_digest("derived_validation_digest", self.derived_validation_digest),
            )
            _validate_report_digest(self)
        _validate_report(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_packet_external_corroboration_gap_v2_payload(self)


def build_research_packet_external_corroboration_gap_v2_report(
    candidates: Iterable[ResearchPacketExternalCorroborationGapV2Candidate],
    *,
    config: ResearchPacketExternalCorroborationGapV2Config,
    generated_at: datetime,
) -> ResearchPacketExternalCorroborationGapV2Report:
    if type(config) is not ResearchPacketExternalCorroborationGapV2Config:
        raise ValueError(
            "config must be a ResearchPacketExternalCorroborationGapV2Config",
        )
    _require_hard_flags("config", config)
    stamp = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    for candidate in normalized_candidates:
        if candidate.captured_at > stamp:
            raise ValueError("candidate captured_at must not be after generated_at")
    rows = _ranked_rows(tuple(_row(candidate, config) for candidate in normalized_candidates))
    count = _count_from_int(len(rows))
    attention_count = _count_from_int(sum(1 for row in rows if row.gap_status != "pass"))
    return ResearchPacketExternalCorroborationGapV2Report(
        generated_at=stamp,
        config_version=config.config_version,
        report_status=_report_status(rows),
        candidate_count=count,
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        attention_count=attention_count,
        attention_ratio=_safe_ratio(attention_count, count),
        weak_independent_family_count=_reason_count(
            rows,
            WEAK_INDEPENDENT_FAMILY_REASON,
        ),
        missing_official_source_count=_reason_count(rows, MISSING_OFFICIAL_SOURCE_REASON),
        high_duplicate_source_ratio_count=_reason_count(
            rows,
            HIGH_DUPLICATE_SOURCE_RATIO_REASON,
        ),
        source_age_gap_count=_count_from_int(
            sum(1 for row in rows if row.source_age_status != "fresh"),
        ),
        stale_source_age_count=_count_from_int(
            sum(1 for row in rows if row.source_age_status == "stale"),
        ),
        contradiction_gap_count=_count_from_int(
            sum(1 for row in rows if row.contradiction_status != "none"),
        ),
        severe_contradiction_count=_reason_count(rows, CONTRADICTION_SEVERE_REASON),
        unexplained_market_move_count=_count_from_int(
            sum(
                1
                for row in rows
                if row.market_move_status != "quiet" and not row.market_move_explained
            ),
        ),
        large_market_move_count=_count_from_int(
            sum(1 for row in rows if row.market_move_status == "large"),
        ),
        max_duplicate_source_ratio=max(
            (row.duplicate_source_ratio for row in rows),
            default=ZERO,
        ),
        max_contradiction_severity=max(
            (row.contradiction_severity for row in rows),
            default=ZERO,
        ),
        max_market_move_abs=max((row.market_move_abs for row in rows), default=ZERO),
        min_independent_family_count_observed=min(
            (row.independent_family_count for row in rows),
            default=ZERO,
        ),
        min_independent_family_count=config.min_independent_family_count,
        fresh_source_max_age_seconds=config.fresh_source_max_age_seconds,
        stale_source_age_seconds=config.stale_source_age_seconds,
        max_duplicate_source_ratio_threshold=config.max_duplicate_source_ratio,
        elevated_contradiction_threshold=config.elevated_contradiction_threshold,
        severe_contradiction_threshold=config.severe_contradiction_threshold,
        material_market_move_threshold=config.material_market_move_threshold,
        large_market_move_threshold=config.large_market_move_threshold,
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_packet_external_corroboration_gap_v2_payload(
    value: ResearchPacketExternalCorroborationGapV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchPacketExternalCorroborationGapV2Report:
        _require_hard_flags("report", value)
        _validate_report(value)
        _validate_report_digest(value)
        payload = _payload(value)
    elif type(value) is dict:
        payload = _json_ready(value)
    else:
        raise ValueError(
            "value must be a ResearchPacketExternalCorroborationGapV2Report or dict",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _validate_public_payload(payload)
    return payload


def derive_research_packet_external_corroboration_gap_v2_digest(
    value: ResearchPacketExternalCorroborationGapV2Report | dict[str, Any],
) -> str:
    if type(value) is ResearchPacketExternalCorroborationGapV2Report:
        _require_hard_flags("report", value)
        _validate_report(value)
        payload = _payload(value)
    elif type(value) is dict:
        payload = _json_ready(value)
    else:
        raise ValueError(
            "value must be a ResearchPacketExternalCorroborationGapV2Report or dict",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload(payload)
    _require_supported_payload(payload, digest_required=False)
    _require_public_payload_flags("payload", payload)
    for row_payload in _payload_rows(payload):
        _require_public_payload_flags("row payload", row_payload)
        _require_row_payload_digest(row_payload)
    return _public_digest(payload)


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row(
    candidate: ResearchPacketExternalCorroborationGapV2Candidate,
    config: ResearchPacketExternalCorroborationGapV2Config,
) -> ResearchPacketExternalCorroborationGapV2Row:
    duplicate_source_count = max(
        candidate.source_count - candidate.independent_family_count,
        ZERO,
    )
    duplicate_source_ratio = _safe_ratio(duplicate_source_count, candidate.source_count)
    source_age_status = _source_age_status(candidate.latest_source_age_seconds, config)
    contradiction_status = _contradiction_status(candidate.contradiction_severity, config)
    market_move_status = _market_move_status(candidate.market_move_abs, config)
    reason_codes = _row_reason_codes(
        candidate=candidate,
        config=config,
        duplicate_source_ratio=duplicate_source_ratio,
        source_age_status=source_age_status,
        contradiction_status=contradiction_status,
        market_move_status=market_move_status,
    )
    return ResearchPacketExternalCorroborationGapV2Row(
        gap_rank=Decimal("1.000000"),
        packet_id=candidate.packet_id,
        claim_id=candidate.claim_id,
        market_id=candidate.market_id,
        captured_at=candidate.captured_at,
        source_count=candidate.source_count,
        independent_family_count=candidate.independent_family_count,
        official_source_count=candidate.official_source_count,
        official_source_status=(
            "present" if candidate.official_source_count > ZERO else "missing"
        ),
        duplicate_source_count=duplicate_source_count,
        duplicate_source_ratio=duplicate_source_ratio,
        latest_source_age_seconds=candidate.latest_source_age_seconds,
        source_age_status=source_age_status,
        contradiction_severity=candidate.contradiction_severity,
        contradiction_status=contradiction_status,
        market_move_abs=candidate.market_move_abs,
        market_move_status=market_move_status,
        market_move_explained=candidate.market_move_explained,
        gap_score=_gap_score(
            candidate=candidate,
            config=config,
            duplicate_source_ratio=duplicate_source_ratio,
            source_age_status=source_age_status,
        ),
        gap_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _ranked_rows(
    rows: tuple[ResearchPacketExternalCorroborationGapV2Row, ...],
) -> tuple[ResearchPacketExternalCorroborationGapV2Row, ...]:
    ranked: list[ResearchPacketExternalCorroborationGapV2Row] = []
    for index, row in enumerate(sorted(rows, key=_row_sort_key), start=1):
        ranked.append(
            ResearchPacketExternalCorroborationGapV2Row(
                gap_rank=_count_from_int(index),
                packet_id=row.packet_id,
                claim_id=row.claim_id,
                market_id=row.market_id,
                captured_at=row.captured_at,
                source_count=row.source_count,
                independent_family_count=row.independent_family_count,
                official_source_count=row.official_source_count,
                official_source_status=row.official_source_status,
                duplicate_source_count=row.duplicate_source_count,
                duplicate_source_ratio=row.duplicate_source_ratio,
                latest_source_age_seconds=row.latest_source_age_seconds,
                source_age_status=row.source_age_status,
                contradiction_severity=row.contradiction_severity,
                contradiction_status=row.contradiction_status,
                market_move_abs=row.market_move_abs,
                market_move_status=row.market_move_status,
                market_move_explained=row.market_move_explained,
                gap_score=row.gap_score,
                gap_status=row.gap_status,
                reason_codes=row.reason_codes,
            ),
        )
    return tuple(ranked)


def _row_sort_key(
    row: ResearchPacketExternalCorroborationGapV2Row,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.gap_status],
        -row.gap_score,
        -row.market_move_abs,
        -row.contradiction_severity,
        row.packet_id,
        row.claim_id,
        row.market_id,
    )


def _row_reason_codes(
    *,
    candidate: ResearchPacketExternalCorroborationGapV2Candidate,
    config: ResearchPacketExternalCorroborationGapV2Config,
    duplicate_source_ratio: Decimal,
    source_age_status: str,
    contradiction_status: str,
    market_move_status: str,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if candidate.source_count == ZERO:
        reasons.append(MISSING_EXTERNAL_CORROBORATION_REASON)
    if candidate.independent_family_count < config.min_independent_family_count:
        reasons.append(WEAK_INDEPENDENT_FAMILY_REASON)
    if candidate.official_source_count == ZERO:
        reasons.append(MISSING_OFFICIAL_SOURCE_REASON)
    if duplicate_source_ratio > config.max_duplicate_source_ratio:
        reasons.append(HIGH_DUPLICATE_SOURCE_RATIO_REASON)
    if source_age_status == "missing":
        reasons.append(SOURCE_AGE_MISSING_REASON)
    elif source_age_status == "watch":
        reasons.append(SOURCE_AGE_WATCH_REASON)
    elif source_age_status == "stale":
        reasons.append(SOURCE_AGE_STALE_REASON)
    if contradiction_status == "severe":
        reasons.append(CONTRADICTION_SEVERE_REASON)
    elif contradiction_status == "elevated":
        reasons.append(CONTRADICTION_ELEVATED_REASON)
    if not candidate.market_move_explained:
        if market_move_status == "large":
            reasons.append(UNEXPLAINED_MARKET_MOVE_LARGE_REASON)
        elif market_move_status == "material":
            reasons.append(UNEXPLAINED_MARKET_MOVE_MATERIAL_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return _reason_codes("reason_codes", tuple(reasons), ROW_REASON_CODES)


def _gap_score(
    *,
    candidate: ResearchPacketExternalCorroborationGapV2Candidate,
    config: ResearchPacketExternalCorroborationGapV2Config,
    duplicate_source_ratio: Decimal,
    source_age_status: str,
) -> Decimal:
    independent_gap = _safe_ratio(
        max(config.min_independent_family_count - candidate.independent_family_count, ZERO),
        config.min_independent_family_count,
    )
    official_gap = ONE if candidate.official_source_count == ZERO else ZERO
    source_age_gap = _source_age_gap_score(source_age_status)
    return _ratio(
        "gap_score",
        (
            independent_gap
            + official_gap
            + duplicate_source_ratio
            + source_age_gap
            + candidate.contradiction_severity
            + candidate.market_move_abs
        )
        / SCORE_FACTOR_COUNT,
    )


def _source_age_gap_score(source_age_status: str) -> Decimal:
    if source_age_status in ("missing", "stale"):
        return ONE
    if source_age_status == "watch":
        return Decimal("0.500000")
    return ZERO


def _source_age_status(
    latest_source_age_seconds: Decimal | None,
    config: ResearchPacketExternalCorroborationGapV2Config,
) -> str:
    if latest_source_age_seconds is None:
        return "missing"
    if latest_source_age_seconds <= config.fresh_source_max_age_seconds:
        return "fresh"
    if latest_source_age_seconds <= config.stale_source_age_seconds:
        return "watch"
    return "stale"


def _contradiction_status(
    contradiction_severity: Decimal,
    config: ResearchPacketExternalCorroborationGapV2Config,
) -> str:
    if contradiction_severity >= config.severe_contradiction_threshold:
        return "severe"
    if contradiction_severity >= config.elevated_contradiction_threshold:
        return "elevated"
    return "none"


def _market_move_status(
    market_move_abs: Decimal,
    config: ResearchPacketExternalCorroborationGapV2Config,
) -> str:
    if market_move_abs >= config.large_market_move_threshold:
        return "large"
    if market_move_abs >= config.material_market_move_threshold:
        return "material"
    return "quiet"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCKED_REASONS for reason_code in reason_codes):
        return "blocked"
    if reason_codes == (PASS_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchPacketExternalCorroborationGapV2Row, ...]) -> str:
    if any(row.gap_status == "blocked" for row in rows):
        return "blocked"
    if any(row.gap_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchPacketExternalCorroborationGapV2Row, ...],
) -> tuple[str, ...]:
    present = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON
    )
    if not present:
        return (PASS_REASON,)
    return tuple(reason_code for reason_code in REPORT_REASON_CODES if reason_code in present)


def _normalize_candidates(
    value: Iterable[ResearchPacketExternalCorroborationGapV2Candidate],
) -> tuple[ResearchPacketExternalCorroborationGapV2Candidate, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("candidate rows must be an iterable")
    try:
        candidates = tuple(value)
    except TypeError as exc:
        raise ValueError("candidate rows must be an iterable") from exc
    seen: set[tuple[str, str, str]] = set()
    for candidate in candidates:
        if type(candidate) is not ResearchPacketExternalCorroborationGapV2Candidate:
            raise ValueError(
                "candidate rows must contain "
                "ResearchPacketExternalCorroborationGapV2Candidate values",
            )
        _require_hard_flags("candidate", candidate)
        key = (candidate.packet_id, candidate.claim_id, candidate.market_id)
        if key in seen:
            raise ValueError("candidate rows must be unique by packet_id claim_id market_id")
        seen.add(key)
    return candidates


def _normalize_rows(
    value: object,
) -> tuple[ResearchPacketExternalCorroborationGapV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    seen: set[tuple[str, str, str]] = set()
    expected_ranks = tuple(_count_from_int(index) for index in range(1, len(rows) + 1))
    actual_ranks: list[Decimal] = []
    for row in rows:
        if type(row) is not ResearchPacketExternalCorroborationGapV2Row:
            raise ValueError(
                "rows must contain ResearchPacketExternalCorroborationGapV2Row values",
            )
        _require_hard_flags("row", row)
        _validate_row(row)
        _validate_row_digest(row)
        key = (row.packet_id, row.claim_id, row.market_id)
        if key in seen:
            raise ValueError("rows must be unique by packet_id claim_id market_id")
        seen.add(key)
        actual_ranks.append(row.gap_rank)
    if tuple(actual_ranks) != expected_ranks:
        raise ValueError("row ranks must be sequential")
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _validate_row(row: ResearchPacketExternalCorroborationGapV2Row) -> None:
    if row.independent_family_count > row.source_count:
        raise ValueError("independent_family_count must not exceed source_count")
    if row.official_source_count > row.source_count:
        raise ValueError("official_source_count must not exceed source_count")
    expected_duplicate_count = max(row.source_count - row.independent_family_count, ZERO)
    if row.duplicate_source_count != expected_duplicate_count:
        raise ValueError("duplicate_source_count must match source counts")
    if row.duplicate_source_ratio != _safe_ratio(row.duplicate_source_count, row.source_count):
        raise ValueError("duplicate_source_ratio must match source counts")
    if row.official_source_status != (
        "present" if row.official_source_count > ZERO else "missing"
    ):
        raise ValueError("official_source_status must match official_source_count")
    if row.source_count == ZERO and row.latest_source_age_seconds is not None:
        raise ValueError("latest_source_age_seconds must be absent without sources")
    if row.gap_status != _row_status(row.reason_codes):
        raise ValueError("gap_status must match reason_codes")


def _validate_report(report: ResearchPacketExternalCorroborationGapV2Report) -> None:
    rows = report.rows
    count = _count_from_int(len(rows))
    if report.candidate_count != count:
        raise ValueError("candidate_count must match rows")
    for field_name, status in (
        ("pass_count", "pass"),
        ("watch_count", "watch"),
        ("blocked_count", "blocked"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match rows")
    attention_count = _count_from_int(sum(1 for row in rows if row.gap_status != "pass"))
    if report.attention_count != attention_count:
        raise ValueError("attention_count must match rows")
    if report.attention_ratio != _safe_ratio(attention_count, count):
        raise ValueError("attention_ratio must match rows")
    expected_counts = (
        (
            "weak_independent_family_count",
            _reason_count(rows, WEAK_INDEPENDENT_FAMILY_REASON),
        ),
        (
            "missing_official_source_count",
            _reason_count(rows, MISSING_OFFICIAL_SOURCE_REASON),
        ),
        (
            "high_duplicate_source_ratio_count",
            _reason_count(rows, HIGH_DUPLICATE_SOURCE_RATIO_REASON),
        ),
        (
            "source_age_gap_count",
            _count_from_int(sum(1 for row in rows if row.source_age_status != "fresh")),
        ),
        (
            "stale_source_age_count",
            _count_from_int(sum(1 for row in rows if row.source_age_status == "stale")),
        ),
        (
            "contradiction_gap_count",
            _count_from_int(sum(1 for row in rows if row.contradiction_status != "none")),
        ),
        (
            "severe_contradiction_count",
            _reason_count(rows, CONTRADICTION_SEVERE_REASON),
        ),
        (
            "unexplained_market_move_count",
            _count_from_int(
                sum(
                    1
                    for row in rows
                    if row.market_move_status != "quiet" and not row.market_move_explained
                ),
            ),
        ),
        (
            "large_market_move_count",
            _count_from_int(sum(1 for row in rows if row.market_move_status == "large")),
        ),
    )
    for field_name, expected_value in expected_counts:
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.max_duplicate_source_ratio != max(
        (row.duplicate_source_ratio for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_duplicate_source_ratio must match rows")
    if report.max_contradiction_severity != max(
        (row.contradiction_severity for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_contradiction_severity must match rows")
    if report.max_market_move_abs != max((row.market_move_abs for row in rows), default=ZERO):
        raise ValueError("max_market_move_abs must match rows")
    if report.min_independent_family_count_observed != min(
        (row.independent_family_count for row in rows),
        default=ZERO,
    ):
        raise ValueError("min_independent_family_count_observed must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _status_count(
    rows: tuple[ResearchPacketExternalCorroborationGapV2Row, ...],
    status: str,
) -> Decimal:
    return _count_from_int(sum(1 for row in rows if row.gap_status == status))


def _reason_count(
    rows: tuple[ResearchPacketExternalCorroborationGapV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _count_from_int(sum(1 for row in rows if reason_code in row.reason_codes))


def _row_digest(row: ResearchPacketExternalCorroborationGapV2Row) -> str:
    return _public_digest(_payload(row))


def _report_digest(report: ResearchPacketExternalCorroborationGapV2Report) -> str:
    return _public_digest(_payload(report))


def _validate_row_digest(row: ResearchPacketExternalCorroborationGapV2Row) -> None:
    if row.derived_validation_digest != _row_digest(row):
        raise ValueError("derived_validation_digest must match row payload")


def _validate_report_digest(report: ResearchPacketExternalCorroborationGapV2Report) -> None:
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report payload")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unsafe_public_payload(payload)
    _require_supported_payload(payload, digest_required=True)
    _require_public_payload_flags("payload", payload)
    for row_payload in _payload_rows(payload):
        _require_public_payload_flags("row payload", row_payload)
        _require_row_payload_digest(row_payload)
    _require_payload_digest(payload)


def _require_supported_payload(
    payload: dict[str, Any],
    *,
    digest_required: bool,
) -> None:
    for key in payload:
        if key not in REPORT_PAYLOAD_FIELDS:
            raise ValueError("payload field is not supported")
    required = (
        REPORT_PAYLOAD_FIELDS
        if digest_required
        else REPORT_PAYLOAD_FIELDS - {"derived_validation_digest"}
    )
    if not required.issubset(payload.keys()):
        raise ValueError("payload field is missing")
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row_payload in rows:
        if type(row_payload) is not dict:
            raise ValueError("rows must contain payload objects")
        for key in row_payload:
            if key not in ROW_PAYLOAD_FIELDS:
                raise ValueError("payload field is not supported")
        if not ROW_PAYLOAD_FIELDS.issubset(row_payload.keys()):
            raise ValueError("payload field is missing")


def _payload_rows(payload: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    normalized_rows: list[dict[str, Any]] = []
    for row_payload in rows:
        if type(row_payload) is not dict:
            raise ValueError("rows must contain payload objects")
        normalized_rows.append(row_payload)
    return tuple(normalized_rows)


def _require_public_payload_flags(label: str, payload: dict[str, Any]) -> None:
    _require_hard_flags(label, _DictFlags(payload))


def _require_row_payload_digest(row_payload: dict[str, Any]) -> None:
    digest = row_payload.get("derived_validation_digest")
    _hex_digest("derived_validation_digest", digest)
    if digest != _public_digest(row_payload):
        raise ValueError("derived_validation_digest must match row payload")


def _require_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _hex_digest("derived_validation_digest", digest)
    if digest != _public_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")


def _public_digest(payload: dict[str, Any]) -> str:
    core = {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    canonical = json.dumps(core, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _payload(value: Any, *, field_name: str | None = None) -> Any:
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        text = value.astimezone(UTC).isoformat()
        if text.endswith("+00:00"):
            return text[:-6] + "Z"
        return text
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload(getattr(value, field.name), field_name=field.name)
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_payload(item) for item in value]
    if type(value) is list:
        return [_payload(item) for item in value]
    if type(value) is dict:
        return {key: _payload(item, field_name=key) for key, item in value.items()}
    return value


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(_payload(value))
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is bool or type(value) is str or value is None:
        return value
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _unsafe_text(key):
                raise ValueError("unsafe public payload key")
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, tuple):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str and _unsafe_text(value):
        raise ValueError("unsafe public payload value")


def _unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _safe_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be text")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical nonblank text")
    if any(character in value for character in ("\n", "\r", "\t")):
        raise ValueError(f"{field_name} must be canonical nonblank text")
    if _unsafe_text(value):
        raise ValueError(f"{field_name} contains unsafe text")


def _config_version(value: object) -> None:
    _safe_text("config_version", value)
    if value != DEFAULT_RESEARCH_PACKET_EXTERNAL_CORROBORATION_GAP_V2_CONFIG_VERSION:
        raise ValueError("config_version must be the supported value")


def _member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be supported")


def _reason_codes(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    seen: set[str] = set()
    for reason_code in value:
        if type(reason_code) is not str:
            raise ValueError(f"{field_name} must contain text")
        if reason_code not in ROW_REASON_SET and reason_code not in REPORT_REASON_SET:
            raise ValueError(f"{field_name} must be supported")
        if reason_code not in allowed_values:
            raise ValueError(f"{field_name} must be supported")
        if reason_code in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(reason_code)
    expected = tuple(reason_code for reason_code in allowed_values if reason_code in seen)
    if value != expected:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} must be {field_name}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 64
        context.rounding = ROUND_HALF_EVEN
        return value.quantize(Q)


def _decimal_nonnegative(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize(_require_decimal(field_name, value))
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _optional_decimal_nonnegative(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _decimal_nonnegative(field_name, value)


def _decimal_positive(field_name: str, value: object) -> Decimal:
    decimal_value = _decimal_nonnegative(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize(_require_decimal(field_name, value))
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _count_nonnegative(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    normalized = _quantize(decimal_value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _count_positive(field_name: str, value: object) -> Decimal:
    normalized = _count_nonnegative(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _count_from_int(value: int) -> Decimal:
    return Decimal(value).quantize(Q)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _ratio("ratio", numerator / denominator)


def _hex_digest(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a sha256 hex digest") from exc
    return value


__all__ = (
    "DEFAULT_RESEARCH_PACKET_EXTERNAL_CORROBORATION_GAP_V2_CONFIG_VERSION",
    "ResearchPacketExternalCorroborationGapV2Candidate",
    "ResearchPacketExternalCorroborationGapV2Config",
    "ResearchPacketExternalCorroborationGapV2Report",
    "ResearchPacketExternalCorroborationGapV2Row",
    "build_research_packet_external_corroboration_gap_v2_report",
    "derive_research_packet_external_corroboration_gap_v2_digest",
    "research_packet_external_corroboration_gap_v2_payload",
)
