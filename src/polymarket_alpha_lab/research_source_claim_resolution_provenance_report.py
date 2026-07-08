"""Report-only source-side claim resolution provenance rollup."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_SOURCE_CLAIM_RESOLUTION_PROVENANCE_REPORT_CONFIG_VERSION = (
    "research-source-claim-resolution-provenance-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_DAY = Decimal("86400.000000")
_SECONDS_PER_HOUR = Decimal("3600.000000")
_MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_SOURCE_TIERS = frozenset(("official", "primary", "secondary"))
_HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_TERMS = (
    "://",
    "?",
    "@",
    "candidate",
    "market_id",
    "slug",
    "question",
    "url",
    "raw",
    "source_text",
    "source text",
    "dsn",
    "table_name",
    "token",
    "wallet",
    "order",
    "trade",
    "auth",
    "network",
    "database",
    "sizing",
    "recommend",
    "live",
)
_UNSAFE_PUBLIC_KEY_TERMS = tuple(
    term for term in _UNSAFE_PUBLIC_TERMS if term not in ("?", "@", "://", "raw")
)
_REASON_CODE_SEQUENCE = (
    "source_claim_resolution_fresh_retrieval",
    "source_claim_resolution_capture_trace_gap",
    "source_claim_resolution_resolution_trace_gap",
    "source_claim_resolution_source_family_trace_gap",
    "source_claim_resolution_contradiction_block",
    "source_claim_resolution_method_trace_gap",
    "source_claim_resolution_official_quorum_gap",
    "source_claim_resolution_official_quorum_met",
    "source_claim_resolution_provenance_block",
    "source_claim_resolution_provenance_complete",
    "source_claim_resolution_provenance_incomplete",
    "source_claim_resolution_provenance_pass",
    "source_claim_resolution_provenance_watch",
    "source_claim_resolution_stale_retrieval",
    "source_claim_resolution_provenance_empty",
)


@dataclass(frozen=True)
class ResearchSourceClaimResolutionProvenanceConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_CLAIM_RESOLUTION_PROVENANCE_REPORT_CONFIG_VERSION
    )
    min_official_source_count: Decimal = Decimal("2.000000")
    min_provenance_completeness: Decimal = Decimal("0.800000")
    block_provenance_completeness: Decimal = Decimal("0.500000")
    min_retrieval_freshness: Decimal = Decimal("0.750000")
    max_retrieval_age_seconds: Decimal = Decimal("57600.000000")
    contradiction_block_threshold: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimResolutionProvenanceConfig:
            raise TypeError(
                "ResearchSourceClaimResolutionProvenanceConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceClaimResolutionProvenanceConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CLAIM_RESOLUTION_PROVENANCE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "min_official_source_count",
            _require_positive_count_decimal(
                "min_official_source_count",
                self.min_official_source_count,
            ),
        )
        for field_name in (
            "min_provenance_completeness",
            "block_provenance_completeness",
            "min_retrieval_freshness",
            "contradiction_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_provenance_completeness >= self.min_provenance_completeness:
            raise ValueError(
                "block_provenance_completeness must be below "
                "min_provenance_completeness",
            )
        object.__setattr__(
            self,
            "max_retrieval_age_seconds",
            _require_positive_duration_decimal(
                "max_retrieval_age_seconds",
                self.max_retrieval_age_seconds,
            ),
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceClaimResolutionProvenanceObservation:
    claim_group: str
    source_family: str
    source_tier: str
    retrieved_at: datetime
    provenance_completeness: Decimal
    supports_resolution: bool
    contradicts_resolution: bool
    has_capture_timestamp: bool
    has_resolution_timestamp: bool
    has_source_family_trace: bool
    has_method_trace: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimResolutionProvenanceObservation:
            raise TypeError(
                "ResearchSourceClaimResolutionProvenanceObservation does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchSourceClaimResolutionProvenanceObservation,
            "observation",
        )
        for field_name in ("claim_group", "source_family"):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_source_tier("source_tier", self.source_tier)
        object.__setattr__(
            self,
            "retrieved_at",
            _as_utc("retrieved_at", self.retrieved_at),
        )
        object.__setattr__(
            self,
            "provenance_completeness",
            _require_ratio_decimal(
                "provenance_completeness",
                self.provenance_completeness,
            ),
        )
        for field_name in (
            "supports_resolution",
            "contradicts_resolution",
            "has_capture_timestamp",
            "has_resolution_timestamp",
            "has_source_family_trace",
            "has_method_trace",
        ):
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchSourceClaimResolutionProvenanceRow:
    claim_group: str
    source_count: Decimal
    source_family_count: Decimal
    official_source_count: Decimal
    official_source_quorum_met: bool
    latest_retrieval_age_seconds: Decimal
    provenance_completeness_score: Decimal
    retrieval_freshness_score: Decimal
    contradiction_risk_score: Decimal
    supporting_source_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimResolutionProvenanceRow:
            raise TypeError(
                "ResearchSourceClaimResolutionProvenanceRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceClaimResolutionProvenanceRow, "row")
        _require_public_identifier("claim_group", self.claim_group)
        for field_name in (
            "source_count",
            "source_family_count",
            "official_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_bool("official_source_quorum_met", self.official_source_quorum_met)
        object.__setattr__(
            self,
            "latest_retrieval_age_seconds",
            _require_nonnegative_duration_decimal(
                "latest_retrieval_age_seconds",
                self.latest_retrieval_age_seconds,
            ),
        )
        for field_name in (
            "provenance_completeness_score",
            "retrieval_freshness_score",
            "contradiction_risk_score",
            "supporting_source_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceClaimResolutionProvenanceReport:
    generated_at: datetime
    config_version: str
    status: str
    report_next_step: str
    claim_group_count: Decimal
    source_family_count: Decimal
    official_source_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_provenance_completeness: Decimal
    average_retrieval_freshness: Decimal
    average_contradiction_risk: Decimal
    rows: tuple[ResearchSourceClaimResolutionProvenanceRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceClaimResolutionProvenanceReport:
            raise TypeError(
                "ResearchSourceClaimResolutionProvenanceReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceClaimResolutionProvenanceReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_CLAIM_RESOLUTION_PROVENANCE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        _require_report_next_step(self.status, self.report_next_step)
        for field_name in (
            "claim_group_count",
            "source_family_count",
            "official_source_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_provenance_completeness",
            "average_retrieval_freshness",
            "average_contradiction_risk",
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
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload(
            "ResearchSourceClaimResolutionProvenanceReport.payload",
            payload,
            allow_json_containers=True,
        )
        return payload


def build_research_source_claim_resolution_provenance_report(
    observations: Sequence[ResearchSourceClaimResolutionProvenanceObservation],
    *,
    generated_at: datetime,
    config: ResearchSourceClaimResolutionProvenanceConfig | None = None,
) -> ResearchSourceClaimResolutionProvenanceReport:
    """Build a pure report-only provenance summary without exposing source text."""

    if config is None:
        config = ResearchSourceClaimResolutionProvenanceConfig()
    if type(config) is not ResearchSourceClaimResolutionProvenanceConfig:
        raise ValueError(
            "config must be a ResearchSourceClaimResolutionProvenanceConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    for item in normalized:
        if item.retrieved_at > generated_at:
            raise ValueError("retrieved_at must not be after generated_at")
    rows = _build_rows(normalized, generated_at=generated_at, config=config)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "report_next_step": _report_next_step(_report_status(rows)),
        "claim_group_count": _decimal_count(len(rows)),
        "source_family_count": _sum_decimal(
            tuple(row.source_family_count for row in rows),
        ),
        "official_source_count": _sum_decimal(
            tuple(row.official_source_count for row in rows),
        ),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_provenance_completeness": _average(
            tuple(row.provenance_completeness_score for row in rows),
        ),
        "average_retrieval_freshness": _average(
            tuple(row.retrieval_freshness_score for row in rows),
        ),
        "average_contradiction_risk": _average(
            tuple(row.contradiction_risk_score for row in rows),
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceClaimResolutionProvenanceReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_claim_resolution_provenance_report_payload(
    report: ResearchSourceClaimResolutionProvenanceReport,
) -> dict[str, object]:
    if type(report) is not ResearchSourceClaimResolutionProvenanceReport:
        raise ValueError(
            "report must be a ResearchSourceClaimResolutionProvenanceReport",
        )
    _require_hard_flags("report", report)
    return report.payload


def _build_rows(
    observations: tuple[ResearchSourceClaimResolutionProvenanceObservation, ...],
    *,
    generated_at: datetime,
    config: ResearchSourceClaimResolutionProvenanceConfig,
) -> tuple[ResearchSourceClaimResolutionProvenanceRow, ...]:
    grouped: dict[str, list[ResearchSourceClaimResolutionProvenanceObservation]] = {}
    for item in observations:
        grouped.setdefault(item.claim_group, []).append(item)
    return tuple(
        _row_for_group(
            claim_group,
            tuple(items),
            generated_at=generated_at,
            config=config,
        )
        for claim_group, items in sorted(grouped.items())
    )


def _row_for_group(
    claim_group: str,
    observations: tuple[ResearchSourceClaimResolutionProvenanceObservation, ...],
    *,
    generated_at: datetime,
    config: ResearchSourceClaimResolutionProvenanceConfig,
) -> ResearchSourceClaimResolutionProvenanceRow:
    source_count = _decimal_count(len(observations))
    source_family_count = _decimal_count(
        len({item.source_family for item in observations}),
    )
    official_source_count = _decimal_count(
        sum(1 for item in observations if item.source_tier == "official"),
    )
    official_source_quorum_met = (
        official_source_count >= config.min_official_source_count
    )
    latest_age = min(
        _seconds_between(generated_at, item.retrieved_at) for item in observations
    )
    provenance_score = _average(
        tuple(item.provenance_completeness for item in observations),
    )
    freshness_score = _average(
        tuple(
            _retrieval_freshness_score(
                _seconds_between(generated_at, item.retrieved_at),
                config.max_retrieval_age_seconds,
            )
            for item in observations
        ),
    )
    contradiction_risk = _ratio(
        _decimal_count(sum(1 for item in observations if item.contradicts_resolution)),
        source_count,
    )
    supporting_source_ratio = _ratio(
        _decimal_count(sum(1 for item in observations if item.supports_resolution)),
        source_count,
    )
    trace_flags = {
        "has_capture_timestamp": all(
            item.has_capture_timestamp for item in observations
        ),
        "has_resolution_timestamp": all(
            item.has_resolution_timestamp for item in observations
        ),
        "has_source_family_trace": all(
            item.has_source_family_trace for item in observations
        ),
        "has_method_trace": all(item.has_method_trace for item in observations),
    }
    status = _row_status(
        official_source_quorum_met=official_source_quorum_met,
        provenance_score=provenance_score,
        freshness_score=freshness_score,
        contradiction_risk=contradiction_risk,
        trace_flags=trace_flags,
        config=config,
    )
    return ResearchSourceClaimResolutionProvenanceRow(
        claim_group=claim_group,
        source_count=source_count,
        source_family_count=source_family_count,
        official_source_count=official_source_count,
        official_source_quorum_met=official_source_quorum_met,
        latest_retrieval_age_seconds=latest_age,
        provenance_completeness_score=provenance_score,
        retrieval_freshness_score=freshness_score,
        contradiction_risk_score=contradiction_risk,
        supporting_source_ratio=supporting_source_ratio,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            official_source_quorum_met=official_source_quorum_met,
            provenance_score=provenance_score,
            freshness_score=freshness_score,
            contradiction_risk=contradiction_risk,
            trace_flags=trace_flags,
            config=config,
        ),
    )


def _row_status(
    *,
    official_source_quorum_met: bool,
    provenance_score: Decimal,
    freshness_score: Decimal,
    contradiction_risk: Decimal,
    trace_flags: Mapping[str, bool],
    config: ResearchSourceClaimResolutionProvenanceConfig,
) -> str:
    if contradiction_risk >= config.contradiction_block_threshold:
        return "block"
    if provenance_score < config.block_provenance_completeness:
        return "block"
    if freshness_score == _ZERO:
        return "block"
    if (
        official_source_quorum_met
        and provenance_score >= config.min_provenance_completeness
        and freshness_score >= config.min_retrieval_freshness
        and contradiction_risk == _ZERO
        and all(trace_flags.values())
    ):
        return "pass"
    return "watch"


def _row_reason_codes(
    *,
    status: str,
    official_source_quorum_met: bool,
    provenance_score: Decimal,
    freshness_score: Decimal,
    contradiction_risk: Decimal,
    trace_flags: Mapping[str, bool],
    config: ResearchSourceClaimResolutionProvenanceConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if status == "pass":
        reason_codes.append("source_claim_resolution_fresh_retrieval")
    if not trace_flags["has_capture_timestamp"]:
        reason_codes.append("source_claim_resolution_capture_trace_gap")
    if not trace_flags["has_resolution_timestamp"]:
        reason_codes.append("source_claim_resolution_resolution_trace_gap")
    if not trace_flags["has_source_family_trace"]:
        reason_codes.append("source_claim_resolution_source_family_trace_gap")
    if contradiction_risk >= config.contradiction_block_threshold:
        reason_codes.append("source_claim_resolution_contradiction_block")
    if not trace_flags["has_method_trace"]:
        reason_codes.append("source_claim_resolution_method_trace_gap")
    if official_source_quorum_met:
        reason_codes.append("source_claim_resolution_official_quorum_met")
    else:
        reason_codes.append("source_claim_resolution_official_quorum_gap")
    if status == "block":
        reason_codes.append("source_claim_resolution_provenance_block")
    if provenance_score >= config.min_provenance_completeness:
        reason_codes.append("source_claim_resolution_provenance_complete")
    elif provenance_score < config.block_provenance_completeness:
        reason_codes.append("source_claim_resolution_provenance_incomplete")
    if status == "pass":
        reason_codes.append("source_claim_resolution_provenance_pass")
    elif status == "watch":
        reason_codes.append("source_claim_resolution_provenance_watch")
    if freshness_score == _ZERO:
        reason_codes.append("source_claim_resolution_stale_retrieval")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(
    rows: tuple[ResearchSourceClaimResolutionProvenanceRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_source_claim_resolution_provenance_review"
    if status == "watch":
        return "watch_report_only_source_claim_resolution_provenance_review"
    if status == "block":
        return "block_report_only_source_claim_resolution_provenance_review"
    raise ValueError("status must be pass, watch, or block")


def _report_reason_codes(
    rows: tuple[ResearchSourceClaimResolutionProvenanceRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("source_claim_resolution_provenance_empty",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[ResearchSourceClaimResolutionProvenanceRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_observations(
    observations: Sequence[ResearchSourceClaimResolutionProvenanceObservation],
) -> tuple[ResearchSourceClaimResolutionProvenanceObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchSourceClaimResolutionProvenanceObservation] = []
    for item in observations:
        if type(item) is not ResearchSourceClaimResolutionProvenanceObservation:
            raise ValueError(
                "observations must contain "
                "ResearchSourceClaimResolutionProvenanceObservation",
            )
        _require_hard_flags("observation", item)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.claim_group,
                item.retrieved_at,
                item.source_tier,
                item.source_family,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchSourceClaimResolutionProvenanceRow],
) -> tuple[ResearchSourceClaimResolutionProvenanceRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchSourceClaimResolutionProvenanceRow] = []
    for row in rows:
        if type(row) is not ResearchSourceClaimResolutionProvenanceRow:
            raise ValueError(
                "rows must contain ResearchSourceClaimResolutionProvenanceRow",
            )
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.claim_group))


def _validate_row_consistency(
    row: ResearchSourceClaimResolutionProvenanceRow,
) -> None:
    if row.source_family_count > row.source_count:
        raise ValueError("source_family_count must not exceed source_count")
    if row.official_source_count > row.source_count:
        raise ValueError("official_source_count must not exceed source_count")
    if row.status == "pass":
        if "source_claim_resolution_provenance_pass" not in row.reason_codes:
            raise ValueError("pass rows must include provenance pass reason")
        if not row.official_source_quorum_met:
            raise ValueError("pass rows must meet official source quorum")
        if row.contradiction_risk_score != _ZERO:
            raise ValueError("pass rows must not have contradiction risk")
    elif row.status == "watch":
        if "source_claim_resolution_provenance_watch" not in row.reason_codes:
            raise ValueError("watch rows must include provenance watch reason")
    elif "source_claim_resolution_provenance_block" not in row.reason_codes:
        raise ValueError("block rows must include provenance block reason")


def _validate_report_consistency(
    report: ResearchSourceClaimResolutionProvenanceReport,
) -> None:
    rows = report.rows
    if report.claim_group_count != _decimal_count(len(rows)):
        raise ValueError("claim_group_count must match rows")
    if report.source_family_count != _sum_decimal(
        tuple(row.source_family_count for row in rows),
    ):
        raise ValueError("source_family_count must match rows")
    if report.official_source_count != _sum_decimal(
        tuple(row.official_source_count for row in rows),
    ):
        raise ValueError("official_source_count must match rows")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_provenance_completeness != _average(
        tuple(row.provenance_completeness_score for row in rows),
    ):
        raise ValueError("average_provenance_completeness must match rows")
    if report.average_retrieval_freshness != _average(
        tuple(row.retrieval_freshness_score for row in rows),
    ):
        raise ValueError("average_retrieval_freshness must match rows")
    if report.average_contradiction_risk != _average(
        tuple(row.contradiction_risk_score for row in rows),
    ):
        raise ValueError("average_contradiction_risk must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.report_next_step != _report_next_step(report.status):
        raise ValueError("report_next_step must match status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


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


def _require_source_tier(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _SOURCE_TIERS:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_report_next_step(status: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError("report_next_step must be a string")
    if value != _report_next_step(status):
        raise ValueError("report_next_step must match status")
    _reject_unsafe_public_string("report_next_step", value)
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


def _require_nonnegative_duration_decimal(field_name: str, value: object) -> Decimal:
    return _require_nonnegative_count_decimal(field_name, value)


def _require_positive_duration_decimal(field_name: str, value: object) -> Decimal:
    return _require_positive_count_decimal(field_name, value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT, rounding=ROUND_HALF_UP)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    return sum(values, _ZERO).quantize(_QUANT, rounding=ROUND_HALF_UP)


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


def _retrieval_freshness_score(age_seconds: Decimal, max_age_seconds: Decimal) -> Decimal:
    if age_seconds >= max_age_seconds:
        return _ZERO
    return _ratio(max_age_seconds - age_seconds, max_age_seconds)


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
    report: ResearchSourceClaimResolutionProvenanceReport,
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
    if any(term in lowered for term in _UNSAFE_PUBLIC_KEY_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_CLAIM_RESOLUTION_PROVENANCE_REPORT_CONFIG_VERSION",
    "ResearchSourceClaimResolutionProvenanceConfig",
    "ResearchSourceClaimResolutionProvenanceObservation",
    "ResearchSourceClaimResolutionProvenanceReport",
    "ResearchSourceClaimResolutionProvenanceRow",
    "build_research_source_claim_resolution_provenance_report",
    "research_source_claim_resolution_provenance_report_payload",
)
