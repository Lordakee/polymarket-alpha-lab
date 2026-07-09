"""Report-only multisource freshness-gap detector for sanitized research groups.

The module is deterministic and side-effect free. Callers provide already
sanitized source-family observations; the report surfaces freshness gaps without
network, storage, execution, recommendation, order, wallet, or live surfaces.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_MULTISOURCE_FRESHNESS_GAP_REPORT_CONFIG_VERSION = (
    "research-source-multisource-freshness-gap-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_CONTRADICTION_EXPOSURE_THRESHOLD = Decimal("0.500000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = ("pass", "watch", "block")
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_TOKENS = frozenset(
    (
        "candidate",
        "market",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "trading",
        "buy",
        "sell",
        "live",
        "network",
        "database",
        "persist",
        "storage",
        "supabase",
        "postgres",
        "sqlite",
        "file_path",
        "filepath",
        "filename",
        "signing",
        "mutation",
        "recommend",
        "execute",
        "execution",
        "sizing",
        "position_size",
        "notional",
        "stake_amount",
        "authentication",
        "authorization",
        "oauth",
        "credential",
        "bearer",
        "password",
        "login",
        "secret",
        "private_key",
        "apikey",
        "api_key",
        "raw",
    ),
)
_REASON_CODE_SEQUENCE = (
    "empty_multisource_freshness_observations",
    "update_age_gap_watch",
    "update_age_gap_block",
    "low_authority_watch",
    "low_authority_block",
    "low_corroboration_watch",
    "low_corroboration_block",
    "contradiction_exposure_watch",
    "contradiction_exposure_block",
    "domain_coverage_gap_watch",
    "domain_coverage_gap_block",
    "missing_source_family_watch",
    "missing_source_family_block",
    "freshness_gap_watch",
    "freshness_gap_block",
    "source_multisource_freshness_gap_passed",
)


@dataclass(frozen=True)
class ResearchSourceMultisourceFreshnessGapReportConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_MULTISOURCE_FRESHNESS_GAP_REPORT_CONFIG_VERSION
    )
    required_source_families: tuple[str, ...] = (
        "official_reporting",
        "domain_specialist",
        "independent_archive",
    )
    max_fresh_age_seconds: Decimal = Decimal("7200.000000")
    min_authority_score: Decimal = Decimal("0.700000")
    min_corroboration_score: Decimal = Decimal("0.650000")
    min_domain_coverage_score: Decimal = Decimal("0.750000")
    watch_freshness_gap_score: Decimal = Decimal("0.350000")
    block_freshness_gap_score: Decimal = Decimal("0.700000")
    block_missing_source_family_count: Decimal = Decimal("2.000000")
    update_age_gap_weight: Decimal = Decimal("0.250000")
    authority_gap_weight: Decimal = Decimal("0.200000")
    corroboration_gap_weight: Decimal = Decimal("0.200000")
    contradiction_exposure_weight: Decimal = Decimal("0.200000")
    domain_coverage_gap_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceMultisourceFreshnessGapReportConfig:
            raise TypeError(
                "ResearchSourceMultisourceFreshnessGapReportConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceMultisourceFreshnessGapReportConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchSourceMultisourceFreshnessGapReportConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_MULTISOURCE_FRESHNESS_GAP_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "required_source_families",
            _normalize_public_identifiers(
                "required_source_families",
                self.required_source_families,
            ),
        )
        object.__setattr__(
            self,
            "max_fresh_age_seconds",
            _require_positive_decimal(
                "max_fresh_age_seconds",
                self.max_fresh_age_seconds,
            ),
        )
        for field_name in (
            "min_authority_score",
            "min_corroboration_score",
            "min_domain_coverage_score",
            "watch_freshness_gap_score",
            "block_freshness_gap_score",
            "update_age_gap_weight",
            "authority_gap_weight",
            "corroboration_gap_weight",
            "contradiction_exposure_weight",
            "domain_coverage_gap_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_freshness_gap_score >= self.block_freshness_gap_score:
            raise ValueError(
                "watch_freshness_gap_score must be below "
                "block_freshness_gap_score",
            )
        object.__setattr__(
            self,
            "block_missing_source_family_count",
            _require_positive_count_decimal(
                "block_missing_source_family_count",
                self.block_missing_source_family_count,
            ),
        )
        if self.block_missing_source_family_count > _decimal_count(
            len(self.required_source_families),
        ):
            raise ValueError(
                "block_missing_source_family_count must not exceed "
                "required_source_families count",
            )
        weight_sum = _quantize(
            self.update_age_gap_weight
            + self.authority_gap_weight
            + self.corroboration_gap_weight
            + self.contradiction_exposure_weight
            + self.domain_coverage_gap_weight,
        )
        if weight_sum != _ONE:
            raise ValueError("freshness gap weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceMultisourceFreshnessObservation:
    research_group_id: str
    source_family: str
    observed_at: datetime
    authority_score: Decimal
    corroboration_score: Decimal
    contradiction_exposure_score: Decimal
    domain_coverage_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceMultisourceFreshnessObservation:
            raise TypeError(
                "ResearchSourceMultisourceFreshnessObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceMultisourceFreshnessObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchSourceMultisourceFreshnessObservation",
            )
        _require_public_identifier("research_group_id", self.research_group_id)
        _require_public_identifier("source_family", self.source_family)
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        for field_name in (
            "authority_score",
            "corroboration_score",
            "contradiction_exposure_score",
            "domain_coverage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchSourceMultisourceFreshnessGapPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceMultisourceFreshnessGapPublicPayloadItem:
            raise TypeError(
                "ResearchSourceMultisourceFreshnessGapPublicPayloadItem does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceMultisourceFreshnessGapPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchSourceMultisourceFreshnessGapPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchSourceMultisourceFreshnessGapReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceMultisourceFreshnessGapReasonCodeCount:
            raise TypeError(
                "ResearchSourceMultisourceFreshnessGapReasonCodeCount does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceMultisourceFreshnessGapReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchSourceMultisourceFreshnessGapReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchSourceMultisourceFreshnessGapRow:
    research_group_id: str
    source_count: Decimal
    source_family_count: Decimal
    missing_source_family_count: Decimal
    stale_source_count: Decimal
    low_authority_source_count: Decimal
    low_corroboration_source_count: Decimal
    contradiction_exposed_source_count: Decimal
    domain_coverage_gap_count: Decimal
    max_source_age_seconds: Decimal
    average_authority_score: Decimal
    average_corroboration_score: Decimal
    max_contradiction_exposure_score: Decimal
    average_domain_coverage_score: Decimal
    freshness_gap_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceMultisourceFreshnessGapRow:
            raise TypeError(
                "ResearchSourceMultisourceFreshnessGapRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceMultisourceFreshnessGapRow:
            raise ValueError("row must be exactly ResearchSourceMultisourceFreshnessGapRow")
        _require_public_identifier("research_group_id", self.research_group_id)
        for field_name in (
            "source_count",
            "source_family_count",
            "missing_source_family_count",
            "stale_source_count",
            "low_authority_source_count",
            "low_corroboration_source_count",
            "contradiction_exposed_source_count",
            "domain_coverage_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _require_nonnegative_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        for field_name in (
            "average_authority_score",
            "average_corroboration_score",
            "max_contradiction_exposure_score",
            "average_domain_coverage_score",
            "freshness_gap_score",
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
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceMultisourceFreshnessGapReport:
    generated_at: datetime
    config_version: str
    max_fresh_age_seconds: Decimal
    min_authority_score: Decimal
    min_corroboration_score: Decimal
    min_domain_coverage_score: Decimal
    watch_freshness_gap_score: Decimal
    block_freshness_gap_score: Decimal
    block_missing_source_family_count: Decimal
    status: str
    group_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_freshness_gap_score: Decimal
    max_freshness_gap_score: Decimal
    rows: tuple[ResearchSourceMultisourceFreshnessGapRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchSourceMultisourceFreshnessGapReasonCodeCount, ...]
    public_payload: tuple[ResearchSourceMultisourceFreshnessGapPublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceMultisourceFreshnessGapReport:
            raise TypeError(
                "ResearchSourceMultisourceFreshnessGapReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceMultisourceFreshnessGapReport:
            raise ValueError(
                "report must be exactly ResearchSourceMultisourceFreshnessGapReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_MULTISOURCE_FRESHNESS_GAP_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "max_fresh_age_seconds",
            _require_positive_decimal(
                "max_fresh_age_seconds",
                self.max_fresh_age_seconds,
            ),
        )
        for field_name in (
            "min_authority_score",
            "min_corroboration_score",
            "min_domain_coverage_score",
            "watch_freshness_gap_score",
            "block_freshness_gap_score",
            "average_freshness_gap_score",
            "max_freshness_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_freshness_gap_score >= self.block_freshness_gap_score:
            raise ValueError(
                "watch_freshness_gap_score must be below "
                "block_freshness_gap_score",
            )
        object.__setattr__(
            self,
            "block_missing_source_family_count",
            _require_positive_count_decimal(
                "block_missing_source_family_count",
                self.block_missing_source_family_count,
            ),
        )
        _require_status("status", self.status)
        for field_name in ("group_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
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
            "ResearchSourceMultisourceFreshnessGapReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_source_multisource_freshness_gap_report(
    observations: Sequence[ResearchSourceMultisourceFreshnessObservation],
    *,
    generated_at: datetime,
    config: ResearchSourceMultisourceFreshnessGapReportConfig | None = None,
    public_payload: Sequence[ResearchSourceMultisourceFreshnessGapPublicPayloadItem] = (),
) -> ResearchSourceMultisourceFreshnessGapReport:
    """Build a local report-only multisource freshness-gap snapshot."""

    if config is None:
        config = ResearchSourceMultisourceFreshnessGapReportConfig()
    if type(config) is not ResearchSourceMultisourceFreshnessGapReportConfig:
        raise ValueError(
            "config must be a ResearchSourceMultisourceFreshnessGapReportConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for item in normalized_observations:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    payload_items = _normalize_public_payload(public_payload)
    rows = _build_rows(normalized_observations, generated_at_utc, config)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "max_fresh_age_seconds": config.max_fresh_age_seconds,
        "min_authority_score": config.min_authority_score,
        "min_corroboration_score": config.min_corroboration_score,
        "min_domain_coverage_score": config.min_domain_coverage_score,
        "watch_freshness_gap_score": config.watch_freshness_gap_score,
        "block_freshness_gap_score": config.block_freshness_gap_score,
        "block_missing_source_family_count": config.block_missing_source_family_count,
        "status": _report_status(rows),
        "group_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_freshness_gap_score": _average(
            tuple(row.freshness_gap_score for row in rows),
        ),
        "max_freshness_gap_score": max(
            (row.freshness_gap_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceMultisourceFreshnessGapReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_multisource_freshness_gap_report_payload(
    report: ResearchSourceMultisourceFreshnessGapReport,
) -> dict[str, object]:
    if type(report) is not ResearchSourceMultisourceFreshnessGapReport:
        raise ValueError(
            "report must be a ResearchSourceMultisourceFreshnessGapReport",
        )
    _require_hard_flags("report", report)
    return report.payload


def research_source_multisource_freshness_gap_report_digest(
    report: ResearchSourceMultisourceFreshnessGapReport,
) -> str:
    if type(report) is not ResearchSourceMultisourceFreshnessGapReport:
        raise ValueError(
            "report must be a ResearchSourceMultisourceFreshnessGapReport",
        )
    _require_hard_flags("report", report)
    return report.derived_validation_digest


def _build_rows(
    observations: tuple[ResearchSourceMultisourceFreshnessObservation, ...],
    generated_at: datetime,
    config: ResearchSourceMultisourceFreshnessGapReportConfig,
) -> tuple[ResearchSourceMultisourceFreshnessGapRow, ...]:
    grouped: dict[str, list[ResearchSourceMultisourceFreshnessObservation]] = {}
    for item in observations:
        grouped.setdefault(item.research_group_id, []).append(item)
    rows = tuple(
        _row_for_group(research_group_id, tuple(items), generated_at, config)
        for research_group_id, items in sorted(grouped.items())
    )
    return _normalize_rows(rows)


def _row_for_group(
    research_group_id: str,
    observations: tuple[ResearchSourceMultisourceFreshnessObservation, ...],
    generated_at: datetime,
    config: ResearchSourceMultisourceFreshnessGapReportConfig,
) -> ResearchSourceMultisourceFreshnessGapRow:
    source_count = _decimal_count(len(observations))
    present_families = frozenset(item.source_family for item in observations)
    missing_count = _decimal_count(
        sum(
            1
            for source_family in config.required_source_families
            if source_family not in present_families
        ),
    )
    source_ages = tuple(
        _age_seconds(generated_at, item.observed_at)
        for item in observations
    )
    max_source_age = max(source_ages, default=_ZERO)
    average_authority = _average(tuple(item.authority_score for item in observations))
    average_corroboration = _average(
        tuple(item.corroboration_score for item in observations),
    )
    max_contradiction = max(
        (item.contradiction_exposure_score for item in observations),
        default=_ZERO,
    )
    average_domain_coverage = _average(
        tuple(item.domain_coverage_score for item in observations),
    )
    raw_gap_score = _freshness_gap_score(
        update_age_gap_score=_clamp_ratio(max_source_age / config.max_fresh_age_seconds),
        authority_gap_score=_clamp_ratio(_ONE - average_authority),
        corroboration_gap_score=_clamp_ratio(_ONE - average_corroboration),
        contradiction_exposure_score=max_contradiction,
        domain_coverage_gap_score=_clamp_ratio(_ONE - average_domain_coverage),
        config=config,
    )
    if missing_count >= config.block_missing_source_family_count:
        gap_score = max(raw_gap_score, config.block_freshness_gap_score)
    else:
        gap_score = raw_gap_score
    status = _row_status(
        freshness_gap_score=gap_score,
        missing_source_family_count=missing_count,
        config=config,
    )
    return ResearchSourceMultisourceFreshnessGapRow(
        research_group_id=research_group_id,
        source_count=source_count,
        source_family_count=_decimal_count(len(present_families)),
        missing_source_family_count=missing_count,
        stale_source_count=_decimal_count(
            sum(1 for age in source_ages if age > config.max_fresh_age_seconds),
        ),
        low_authority_source_count=_decimal_count(
            sum(1 for item in observations if item.authority_score < config.min_authority_score),
        ),
        low_corroboration_source_count=_decimal_count(
            sum(
                1
                for item in observations
                if item.corroboration_score < config.min_corroboration_score
            ),
        ),
        contradiction_exposed_source_count=_decimal_count(
            sum(
                1
                for item in observations
                if item.contradiction_exposure_score >= _CONTRADICTION_EXPOSURE_THRESHOLD
            ),
        ),
        domain_coverage_gap_count=_decimal_count(
            sum(
                1
                for item in observations
                if item.domain_coverage_score < config.min_domain_coverage_score
            ),
        ),
        max_source_age_seconds=max_source_age,
        average_authority_score=average_authority,
        average_corroboration_score=average_corroboration,
        max_contradiction_exposure_score=max_contradiction,
        average_domain_coverage_score=average_domain_coverage,
        freshness_gap_score=gap_score,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            max_source_age_seconds=max_source_age,
            average_authority_score=average_authority,
            average_corroboration_score=average_corroboration,
            max_contradiction_exposure_score=max_contradiction,
            average_domain_coverage_score=average_domain_coverage,
            missing_source_family_count=missing_count,
            config=config,
        ),
    )


def _freshness_gap_score(
    *,
    update_age_gap_score: Decimal,
    authority_gap_score: Decimal,
    corroboration_gap_score: Decimal,
    contradiction_exposure_score: Decimal,
    domain_coverage_gap_score: Decimal,
    config: ResearchSourceMultisourceFreshnessGapReportConfig,
) -> Decimal:
    return _clamp_ratio(
        (update_age_gap_score * config.update_age_gap_weight)
        + (authority_gap_score * config.authority_gap_weight)
        + (corroboration_gap_score * config.corroboration_gap_weight)
        + (contradiction_exposure_score * config.contradiction_exposure_weight)
        + (domain_coverage_gap_score * config.domain_coverage_gap_weight),
    )


def _row_status(
    *,
    freshness_gap_score: Decimal,
    missing_source_family_count: Decimal,
    config: ResearchSourceMultisourceFreshnessGapReportConfig,
) -> str:
    if freshness_gap_score >= config.block_freshness_gap_score:
        return "block"
    if freshness_gap_score >= config.watch_freshness_gap_score:
        return "watch"
    if missing_source_family_count >= config.block_missing_source_family_count:
        return "block"
    if missing_source_family_count > _ZERO:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    max_source_age_seconds: Decimal,
    average_authority_score: Decimal,
    average_corroboration_score: Decimal,
    max_contradiction_exposure_score: Decimal,
    average_domain_coverage_score: Decimal,
    missing_source_family_count: Decimal,
    config: ResearchSourceMultisourceFreshnessGapReportConfig,
) -> tuple[str, ...]:
    if status == "pass":
        return ("source_multisource_freshness_gap_passed",)
    suffix = status
    reason_codes: list[str] = []
    if max_source_age_seconds > config.max_fresh_age_seconds:
        reason_codes.append(f"update_age_gap_{suffix}")
    if average_authority_score < config.min_authority_score:
        reason_codes.append(f"low_authority_{suffix}")
    if average_corroboration_score < config.min_corroboration_score:
        reason_codes.append(f"low_corroboration_{suffix}")
    if max_contradiction_exposure_score >= _CONTRADICTION_EXPOSURE_THRESHOLD:
        reason_codes.append(f"contradiction_exposure_{suffix}")
    if average_domain_coverage_score < config.min_domain_coverage_score:
        reason_codes.append(f"domain_coverage_gap_{suffix}")
    if missing_source_family_count > _ZERO:
        reason_codes.append(f"missing_source_family_{suffix}")
    reason_codes.append(f"freshness_gap_{suffix}")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(rows: tuple[ResearchSourceMultisourceFreshnessGapRow, ...]) -> str:
    if not rows:
        return "pass"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceMultisourceFreshnessGapRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_multisource_freshness_observations",)
    return _normalize_reason_codes(tuple(code for row in rows for code in row.reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchSourceMultisourceFreshnessGapRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceMultisourceFreshnessGapReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchSourceMultisourceFreshnessGapReasonCodeCount(
                reason_code=reason_codes[0],
                count=_ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchSourceMultisourceFreshnessGapReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
        )
        for reason_code in _REASON_CODE_SEQUENCE
        if counts[reason_code] > 0
    )


def _status_count(
    rows: tuple[ResearchSourceMultisourceFreshnessGapRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_observations(
    observations: Sequence[ResearchSourceMultisourceFreshnessObservation],
) -> tuple[ResearchSourceMultisourceFreshnessObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchSourceMultisourceFreshnessObservation] = []
    for item in observations:
        if type(item) is not ResearchSourceMultisourceFreshnessObservation:
            raise ValueError(
                "observations must contain "
                "ResearchSourceMultisourceFreshnessObservation",
            )
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.research_group_id,
                item.source_family,
                item.observed_at,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchSourceMultisourceFreshnessGapRow],
) -> tuple[ResearchSourceMultisourceFreshnessGapRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchSourceMultisourceFreshnessGapRow] = []
    research_group_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceMultisourceFreshnessGapRow:
            raise ValueError(
                "rows must contain ResearchSourceMultisourceFreshnessGapRow",
            )
        if row.research_group_id in research_group_ids:
            raise ValueError("rows must not contain duplicate research_group_id")
        research_group_ids.add(row.research_group_id)
        normalized.append(row)
    return tuple(
        sorted(
            normalized,
            key=lambda row: (
                _status_sort_value(row.status),
                -row.freshness_gap_score,
                row.research_group_id,
            ),
        ),
    )


def _normalize_reason_code_counts(
    reason_code_counts: Sequence[ResearchSourceMultisourceFreshnessGapReasonCodeCount],
) -> tuple[ResearchSourceMultisourceFreshnessGapReasonCodeCount, ...]:
    if isinstance(reason_code_counts, (str, bytes)) or not isinstance(
        reason_code_counts,
        Sequence,
    ):
        raise ValueError("reason_code_counts must be a sequence")
    normalized: list[ResearchSourceMultisourceFreshnessGapReasonCodeCount] = []
    for item in reason_code_counts:
        if type(item) is not ResearchSourceMultisourceFreshnessGapReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceMultisourceFreshnessGapReasonCodeCount",
            )
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: _REASON_CODE_SEQUENCE.index(item.reason_code),
        ),
    )


def _normalize_public_payload(
    public_payload: Sequence[ResearchSourceMultisourceFreshnessGapPublicPayloadItem],
) -> tuple[ResearchSourceMultisourceFreshnessGapPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchSourceMultisourceFreshnessGapPublicPayloadItem] = []
    keys: set[str] = set()
    for item in public_payload:
        if type(item) is not ResearchSourceMultisourceFreshnessGapPublicPayloadItem:
            raise ValueError(
                "public_payload must contain "
                "ResearchSourceMultisourceFreshnessGapPublicPayloadItem",
            )
        if item.key in keys:
            raise ValueError("duplicate public_payload key")
        keys.add(item.key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _normalize_public_identifiers(field_name: str, values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ValueError(f"{field_name} must be a sequence")
    normalized: list[str] = []
    for value in values:
        public_value = _require_public_identifier(field_name, value)
        if public_value in normalized:
            raise ValueError(f"duplicate {field_name}")
        normalized.append(public_value)
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return tuple(normalized)


def _validate_row_consistency(row: ResearchSourceMultisourceFreshnessGapRow) -> None:
    if row.source_family_count > row.source_count:
        raise ValueError("source_family_count must not exceed source_count")
    for field_name in (
        "stale_source_count",
        "low_authority_source_count",
        "low_corroboration_source_count",
        "contradiction_exposed_source_count",
        "domain_coverage_gap_count",
    ):
        if getattr(row, field_name) > row.source_count:
            raise ValueError(f"{field_name} must not exceed source_count")
    if row.status == "pass" and row.reason_codes != (
        "source_multisource_freshness_gap_passed",
    ):
        raise ValueError("pass rows must include the pass reason only")
    if row.status != "pass" and not row.reason_codes:
        raise ValueError("non-pass rows must include reason codes")


def _validate_report_consistency(report: ResearchSourceMultisourceFreshnessGapReport) -> None:
    if report.group_count != _decimal_count(len(report.rows)):
        raise ValueError("group_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_freshness_gap_score != _average(
        tuple(row.freshness_gap_score for row in report.rows),
    ):
        raise ValueError("average_freshness_gap_score must match rows")
    expected_max = max(
        (row.freshness_gap_score for row in report.rows),
        default=_ZERO,
    )
    if report.max_freshness_gap_score != expected_max:
        raise ValueError("max_freshness_gap_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(
        report.rows,
        report.reason_codes,
    ):
        raise ValueError("reason_code_counts must match rows")


def _status_sort_value(status: str) -> int:
    if status == "block":
        return 0
    if status == "watch":
        return 1
    return 2


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if type(getattr(value, field_name, None)) is not bool:
            raise ValueError(f"{field_name} must be a bool")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_string(field_name, value)
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "www." in lowered or "@" in lowered or "?" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if _contains_unsafe_public_token(lowered):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    public_value = _require_public_identifier(field_name, value)
    if public_value not in _REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be supported")
    return public_value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
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
        raise ValueError(f"{field_name} must be a whole Decimal")
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


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _require_nonnegative_decimal("source_age_seconds", seconds + microseconds)


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} utcoffset must not be None")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchSourceMultisourceFreshnessGapReport,
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
    if _contains_unsafe_public_token(lowered):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _contains_unsafe_public_token(lowered: str) -> bool:
    if any(term in lowered for term in _UNSAFE_PUBLIC_TOKENS):
        return True
    return re.search(r"(^|[^a-z0-9])auth([^a-z0-9]|$)", lowered) is not None


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_MULTISOURCE_FRESHNESS_GAP_REPORT_CONFIG_VERSION",
    "ResearchSourceMultisourceFreshnessGapPublicPayloadItem",
    "ResearchSourceMultisourceFreshnessGapReasonCodeCount",
    "ResearchSourceMultisourceFreshnessGapReport",
    "ResearchSourceMultisourceFreshnessGapReportConfig",
    "ResearchSourceMultisourceFreshnessGapRow",
    "ResearchSourceMultisourceFreshnessObservation",
    "build_research_source_multisource_freshness_gap_report",
    "research_source_multisource_freshness_gap_report_digest",
    "research_source_multisource_freshness_gap_report_payload",
)
