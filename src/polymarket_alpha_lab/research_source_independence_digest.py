"""Pure Phase 1 source-independence digest for redacted research groups."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_INDEPENDENCE_DIGEST_CONFIG_VERSION = (
    "research-source-independence-digest-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SOURCE_GROUP_REF_RE = re.compile(r"^sg_[a-z0-9]{8,64}$")
_CORRELATION_GROUP_REF_RE = re.compile(r"^cg_[a-z0-9]{8,64}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_KEY_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_SOURCE_ROLES = frozenset(("official", "primary", "secondary"))
_OFFICIAL_PRIMARY_SOURCE_ROLES = frozenset(("official", "primary"))
_STANCES = frozenset(("corroborating", "contradicting", "contextual"))
_STATUSES = frozenset(("pass", "watch", "blocked"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TERMS = (
    "account",
    "live",
    "auth",
    "credential",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "private",
    "secret",
    "signing",
    "token",
    "mutation",
    "buy",
    "sell",
    "trade",
    "trading",
)
_UNSAFE_REDACTION_TERMS = (
    "http",
    "https",
    "link",
    "market",
    "question",
    "url",
    "uri",
    "raw",
    "text",
    "name",
    "slug",
    "www",
)
_REASON_CODE_SEQUENCE = (
    "empty_source_group_facts",
    "source_group_independent",
    "source_group_correlated",
    "source_group_official_or_primary",
    "source_group_secondary",
    "source_group_contradicting",
    "source_group_freshness_pass",
    "source_group_freshness_watch",
    "source_group_freshness_blocked",
    "independent_source_coverage_pass",
    "independent_source_coverage_watch",
    "independent_source_coverage_blocked",
    "correlated_source_concentration_pass",
    "correlated_source_concentration_watch",
    "correlated_source_concentration_blocked",
    "official_or_primary_source_present",
    "official_or_primary_source_missing",
    "contradiction_diversity_present",
    "contradiction_diversity_missing",
    "freshness_quality_pass",
    "freshness_quality_watch",
    "freshness_quality_blocked",
    "research_source_independence_pass",
    "research_source_independence_watch",
    "research_source_independence_blocked",
)


@dataclass(frozen=True)
class ResearchSourceIndependenceDigestConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_INDEPENDENCE_DIGEST_CONFIG_VERSION
    pass_independent_source_coverage: Decimal = Decimal("0.666667")
    blocked_independent_source_coverage: Decimal = Decimal("0.250000")
    pass_max_correlated_source_concentration: Decimal = Decimal("0.500000")
    blocked_max_correlated_source_concentration: Decimal = Decimal("0.850000")
    pass_official_primary_source_presence: Decimal = Decimal("0.000001")
    pass_contradiction_diversity: Decimal = Decimal("0.333333")
    pass_freshness_quality: Decimal = Decimal("0.700000")
    blocked_freshness_quality: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceIndependenceDigestConfig:
            raise TypeError(
                "ResearchSourceIndependenceDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceIndependenceDigestConfig:
            raise ValueError(
                "config must be exactly ResearchSourceIndependenceDigestConfig",
            )
        _require_config_version(self.config_version)
        for field_name in (
            "pass_independent_source_coverage",
            "blocked_independent_source_coverage",
            "pass_max_correlated_source_concentration",
            "blocked_max_correlated_source_concentration",
            "pass_official_primary_source_presence",
            "pass_contradiction_diversity",
            "pass_freshness_quality",
            "blocked_freshness_quality",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_independent_source_coverage <= self.blocked_independent_source_coverage:
            raise ValueError(
                "pass_independent_source_coverage must exceed "
                "blocked_independent_source_coverage",
            )
        if (
            self.blocked_max_correlated_source_concentration
            <= self.pass_max_correlated_source_concentration
        ):
            raise ValueError(
                "blocked_max_correlated_source_concentration must exceed "
                "pass_max_correlated_source_concentration",
            )
        if self.pass_official_primary_source_presence <= _ZERO:
            raise ValueError("pass_official_primary_source_presence must be positive")
        if self.pass_freshness_quality <= self.blocked_freshness_quality:
            raise ValueError(
                "pass_freshness_quality must exceed blocked_freshness_quality",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceGroupFact:
    source_group_ref: str
    source_group_digest: str
    correlation_group_ref: str
    weight: Decimal
    source_role: str
    stance: str
    freshness_quality: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceGroupFact:
            raise TypeError("ResearchSourceGroupFact does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceGroupFact:
            raise ValueError("fact must be exactly ResearchSourceGroupFact")
        object.__setattr__(
            self,
            "source_group_ref",
            _require_source_group_ref("source_group_ref", self.source_group_ref),
        )
        object.__setattr__(
            self,
            "source_group_digest",
            _require_sha256_digest("source_group_digest", self.source_group_digest),
        )
        object.__setattr__(
            self,
            "correlation_group_ref",
            _require_correlation_group_ref(
                "correlation_group_ref",
                self.correlation_group_ref,
            ),
        )
        object.__setattr__(
            self,
            "weight",
            _require_positive_decimal("weight", self.weight),
        )
        object.__setattr__(
            self,
            "source_role",
            _require_member("source_role", self.source_role, _SOURCE_ROLES),
        )
        object.__setattr__(
            self,
            "stance",
            _require_member("stance", self.stance, _STANCES),
        )
        object.__setattr__(
            self,
            "freshness_quality",
            _require_ratio_decimal("freshness_quality", self.freshness_quality),
        )
        _require_hard_flags("fact", self)
        _reject_unsafe_public_payload("fact", self)


@dataclass(frozen=True)
class ResearchSourceIndependencePublicPayloadItem:
    key: str
    value_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceIndependencePublicPayloadItem:
            raise TypeError(
                "ResearchSourceIndependencePublicPayloadItem does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceIndependencePublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchSourceIndependencePublicPayloadItem",
            )
        object.__setattr__(self, "key", _require_public_key("key", self.key))
        object.__setattr__(
            self,
            "value_digest",
            _require_sha256_digest("value_digest", self.value_digest),
        )
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchSourceIndependenceDigestRow:
    source_group_ref: str
    source_group_digest: str
    correlation_group_ref: str
    weight: Decimal
    independent_weight: Decimal
    correlated_weight_share: Decimal
    source_role: str
    stance: str
    freshness_quality: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceIndependenceDigestRow:
            raise TypeError(
                "ResearchSourceIndependenceDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceIndependenceDigestRow:
            raise ValueError("row must be exactly ResearchSourceIndependenceDigestRow")
        object.__setattr__(
            self,
            "source_group_ref",
            _require_source_group_ref("source_group_ref", self.source_group_ref),
        )
        object.__setattr__(
            self,
            "source_group_digest",
            _require_sha256_digest("source_group_digest", self.source_group_digest),
        )
        object.__setattr__(
            self,
            "correlation_group_ref",
            _require_correlation_group_ref(
                "correlation_group_ref",
                self.correlation_group_ref,
            ),
        )
        object.__setattr__(
            self,
            "weight",
            _require_positive_decimal("weight", self.weight),
        )
        object.__setattr__(
            self,
            "independent_weight",
            _require_nonnegative_decimal("independent_weight", self.independent_weight),
        )
        object.__setattr__(
            self,
            "correlated_weight_share",
            _require_ratio_decimal(
                "correlated_weight_share",
                self.correlated_weight_share,
            ),
        )
        object.__setattr__(
            self,
            "source_role",
            _require_member("source_role", self.source_role, _SOURCE_ROLES),
        )
        object.__setattr__(
            self,
            "stance",
            _require_member("stance", self.stance, _STANCES),
        )
        object.__setattr__(
            self,
            "freshness_quality",
            _require_ratio_decimal("freshness_quality", self.freshness_quality),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        if self.independent_weight > self.weight:
            raise ValueError("independent_weight must not exceed weight")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceIndependenceDigestReport:
    generated_at: datetime
    config_version: str
    pass_freshness_quality: Decimal
    blocked_freshness_quality: Decimal
    status: str
    source_group_count: Decimal
    correlation_group_count: Decimal
    total_weight: Decimal
    independent_weight: Decimal
    independent_source_coverage: Decimal
    correlated_source_concentration: Decimal
    official_primary_source_presence: Decimal
    contradiction_diversity: Decimal
    freshness_quality: Decimal
    rows: tuple[ResearchSourceIndependenceDigestRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchSourceIndependencePublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceIndependenceDigestReport:
            raise TypeError(
                "ResearchSourceIndependenceDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceIndependenceDigestReport:
            raise ValueError(
                "report must be exactly ResearchSourceIndependenceDigestReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_config_version(self.config_version)
        for field_name in ("pass_freshness_quality", "blocked_freshness_quality"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_freshness_quality <= self.blocked_freshness_quality:
            raise ValueError(
                "pass_freshness_quality must exceed blocked_freshness_quality",
            )
        object.__setattr__(self, "status", _require_status("status", self.status))
        for field_name in ("source_group_count", "correlation_group_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("total_weight", "independent_weight"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "independent_source_coverage",
            "correlated_source_concentration",
            "official_primary_source_presence",
            "contradiction_diversity",
            "freshness_quality",
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
            "ResearchSourceIndependenceDigestReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_source_independence_digest(
    source_group_facts: Sequence[ResearchSourceGroupFact],
    *,
    generated_at: datetime,
    config: ResearchSourceIndependenceDigestConfig | None = None,
    public_payload: Sequence[ResearchSourceIndependencePublicPayloadItem] = (),
) -> ResearchSourceIndependenceDigestReport:
    """Build a deterministic report-only independence digest from redacted facts."""

    if config is None:
        config = ResearchSourceIndependenceDigestConfig()
    if type(config) is not ResearchSourceIndependenceDigestConfig:
        raise ValueError("config must be a ResearchSourceIndependenceDigestConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    facts = _normalize_facts(source_group_facts)
    payload_items = _normalize_public_payload(public_payload)
    _reject_duplicate_facts(facts)

    total_weight = _sum_decimal(tuple(fact.weight for fact in facts))
    correlation_group_count = _decimal_count(
        len({fact.correlation_group_ref for fact in facts}),
    )
    correlation_weights = _correlation_weights(facts)
    correlation_counts = _correlation_counts(facts)
    rows = _build_rows(
        facts=facts,
        total_weight=total_weight,
        correlation_weights=correlation_weights,
        correlation_counts=correlation_counts,
        config=config,
    )
    independent_weight = _sum_decimal(tuple(row.independent_weight for row in rows))
    independent_source_coverage = _ratio(independent_weight, total_weight)
    correlated_source_concentration = max(
        (_ratio(weight, total_weight) for weight in correlation_weights.values()),
        default=_ZERO,
    )
    official_primary_source_presence = _ratio(
        _sum_decimal(
            tuple(
                fact.weight
                for fact in facts
                if fact.source_role in _OFFICIAL_PRIMARY_SOURCE_ROLES
            ),
        ),
        total_weight,
    )
    contradiction_diversity = _contradiction_diversity(facts)
    freshness_quality = _freshness_quality(facts, total_weight)
    report_reason_codes = _report_reason_codes(
        rows=rows,
        independent_source_coverage=independent_source_coverage,
        correlated_source_concentration=correlated_source_concentration,
        official_primary_source_presence=official_primary_source_presence,
        contradiction_diversity=contradiction_diversity,
        freshness_quality=freshness_quality,
        config=config,
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "pass_freshness_quality": config.pass_freshness_quality,
        "blocked_freshness_quality": config.blocked_freshness_quality,
        "status": _report_status(report_reason_codes),
        "source_group_count": _decimal_count(len(rows)),
        "correlation_group_count": correlation_group_count,
        "total_weight": total_weight,
        "independent_weight": independent_weight,
        "independent_source_coverage": independent_source_coverage,
        "correlated_source_concentration": correlated_source_concentration,
        "official_primary_source_presence": official_primary_source_presence,
        "contradiction_diversity": contradiction_diversity,
        "freshness_quality": freshness_quality,
        "rows": rows,
        "reason_codes": report_reason_codes,
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceIndependenceDigestReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _normalize_facts(
    source_group_facts: Sequence[ResearchSourceGroupFact],
) -> tuple[ResearchSourceGroupFact, ...]:
    if isinstance(source_group_facts, (str, bytes)) or not isinstance(
        source_group_facts,
        Sequence,
    ):
        raise ValueError("source_group_facts must be a sequence")
    normalized: list[ResearchSourceGroupFact] = []
    for fact in source_group_facts:
        if type(fact) is not ResearchSourceGroupFact:
            raise ValueError("source_group_facts must contain ResearchSourceGroupFact")
        _require_hard_flags("fact", fact)
        normalized.append(fact)
    return tuple(
        sorted(
            normalized,
            key=lambda fact: (
                fact.source_group_ref,
                fact.source_group_digest,
                fact.correlation_group_ref,
            ),
        ),
    )


def _reject_duplicate_facts(facts: tuple[ResearchSourceGroupFact, ...]) -> None:
    refs: set[str] = set()
    digests: set[str] = set()
    for fact in facts:
        if fact.source_group_ref in refs:
            raise ValueError("duplicate source_group_ref")
        refs.add(fact.source_group_ref)
        if fact.source_group_digest in digests:
            raise ValueError("duplicate source_group_digest")
        digests.add(fact.source_group_digest)


def _build_rows(
    *,
    facts: tuple[ResearchSourceGroupFact, ...],
    total_weight: Decimal,
    correlation_weights: Mapping[str, Decimal],
    correlation_counts: Mapping[str, Decimal],
    config: ResearchSourceIndependenceDigestConfig,
) -> tuple[ResearchSourceIndependenceDigestRow, ...]:
    rows: list[ResearchSourceIndependenceDigestRow] = []
    for fact in facts:
        correlation_weight = correlation_weights[fact.correlation_group_ref]
        source_group_is_independent = (
            correlation_counts[fact.correlation_group_ref] == _ONE
        )
        rows.append(
            ResearchSourceIndependenceDigestRow(
                source_group_ref=fact.source_group_ref,
                source_group_digest=fact.source_group_digest,
                correlation_group_ref=fact.correlation_group_ref,
                weight=fact.weight,
                independent_weight=(
                    fact.weight if source_group_is_independent else _ZERO
                ),
                correlated_weight_share=_ratio(correlation_weight, total_weight),
                source_role=fact.source_role,
                stance=fact.stance,
                freshness_quality=fact.freshness_quality,
                reason_codes=_row_reason_codes(
                    source_group_is_independent=source_group_is_independent,
                    source_role=fact.source_role,
                    stance=fact.stance,
                    freshness_quality=fact.freshness_quality,
                    pass_freshness_quality=config.pass_freshness_quality,
                    blocked_freshness_quality=config.blocked_freshness_quality,
                ),
            ),
        )
    return tuple(rows)


def _row_reason_codes(
    *,
    source_group_is_independent: bool,
    source_role: str,
    stance: str,
    freshness_quality: Decimal,
    pass_freshness_quality: Decimal,
    blocked_freshness_quality: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = [
        (
            "source_group_independent"
            if source_group_is_independent
            else "source_group_correlated"
        ),
        (
            "source_group_official_or_primary"
            if source_role in _OFFICIAL_PRIMARY_SOURCE_ROLES
            else "source_group_secondary"
        ),
    ]
    if stance == "contradicting":
        reason_codes.append("source_group_contradicting")
    if freshness_quality >= pass_freshness_quality:
        reason_codes.append("source_group_freshness_pass")
    elif freshness_quality >= blocked_freshness_quality:
        reason_codes.append("source_group_freshness_watch")
    else:
        reason_codes.append("source_group_freshness_blocked")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_reason_codes(
    *,
    rows: tuple[ResearchSourceIndependenceDigestRow, ...],
    independent_source_coverage: Decimal,
    correlated_source_concentration: Decimal,
    official_primary_source_presence: Decimal,
    contradiction_diversity: Decimal,
    freshness_quality: Decimal,
    config: ResearchSourceIndependenceDigestConfig,
) -> tuple[str, ...]:
    if not rows:
        return (
            "empty_source_group_facts",
            "research_source_independence_blocked",
        )

    reason_codes: list[str] = []
    if independent_source_coverage < config.blocked_independent_source_coverage:
        reason_codes.append("independent_source_coverage_blocked")
    elif independent_source_coverage >= config.pass_independent_source_coverage:
        reason_codes.append("independent_source_coverage_pass")
    else:
        reason_codes.append("independent_source_coverage_watch")

    if (
        correlated_source_concentration
        > config.blocked_max_correlated_source_concentration
    ):
        reason_codes.append("correlated_source_concentration_blocked")
    elif (
        correlated_source_concentration
        <= config.pass_max_correlated_source_concentration
    ):
        reason_codes.append("correlated_source_concentration_pass")
    else:
        reason_codes.append("correlated_source_concentration_watch")

    reason_codes.append(
        "official_or_primary_source_present"
        if official_primary_source_presence
        >= config.pass_official_primary_source_presence
        else "official_or_primary_source_missing",
    )
    reason_codes.append(
        "contradiction_diversity_present"
        if contradiction_diversity >= config.pass_contradiction_diversity
        else "contradiction_diversity_missing",
    )

    if freshness_quality < config.blocked_freshness_quality:
        reason_codes.append("freshness_quality_blocked")
    elif freshness_quality >= config.pass_freshness_quality:
        reason_codes.append("freshness_quality_pass")
    else:
        reason_codes.append("freshness_quality_watch")

    status = _report_status(tuple(reason_codes))
    reason_codes.append(f"research_source_independence_{status}")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(reason_codes: Sequence[str]) -> str:
    if "empty_source_group_facts" in reason_codes:
        return "blocked"
    if any(reason_code.endswith("_blocked") for reason_code in reason_codes):
        return "blocked"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    if "official_or_primary_source_missing" in reason_codes:
        return "watch"
    if "contradiction_diversity_missing" in reason_codes:
        return "watch"
    return "pass"


def _correlation_weights(
    facts: tuple[ResearchSourceGroupFact, ...],
) -> dict[str, Decimal]:
    weights: dict[str, Decimal] = {}
    for fact in facts:
        weights[fact.correlation_group_ref] = _quantize(
            weights.get(fact.correlation_group_ref, _ZERO) + fact.weight,
        )
    return weights


def _correlation_counts(
    facts: tuple[ResearchSourceGroupFact, ...],
) -> dict[str, Decimal]:
    counts: dict[str, Decimal] = {}
    for fact in facts:
        counts[fact.correlation_group_ref] = _quantize(
            counts.get(fact.correlation_group_ref, _ZERO) + _ONE,
        )
    return counts


def _contradiction_diversity(
    facts: tuple[ResearchSourceGroupFact, ...],
) -> Decimal:
    correlation_group_refs = {fact.correlation_group_ref for fact in facts}
    if not correlation_group_refs:
        return _ZERO
    contradicting_refs = {
        fact.correlation_group_ref for fact in facts if fact.stance == "contradicting"
    }
    return _ratio(
        _decimal_count(len(contradicting_refs)),
        _decimal_count(len(correlation_group_refs)),
    )


def _freshness_quality(
    facts: tuple[ResearchSourceGroupFact, ...],
    total_weight: Decimal,
) -> Decimal:
    if total_weight == _ZERO:
        return _ZERO
    weighted = _sum_decimal(
        tuple(fact.freshness_quality * fact.weight for fact in facts),
    )
    return _ratio(weighted, total_weight)


def _validate_report_consistency(report: ResearchSourceIndependenceDigestReport) -> None:
    if report.source_group_count != _decimal_count(len(report.rows)):
        raise ValueError("source_group_count must match rows")
    if report.correlation_group_count != _decimal_count(
        len({row.correlation_group_ref for row in report.rows}),
    ):
        raise ValueError("correlation_group_count must match rows")
    expected_total_weight = _sum_decimal(tuple(row.weight for row in report.rows))
    if report.total_weight != expected_total_weight:
        raise ValueError("total_weight must match rows")
    expected_independent_weight = _sum_decimal(
        tuple(row.independent_weight for row in report.rows),
    )
    if report.independent_weight != expected_independent_weight:
        raise ValueError("independent_weight must match rows")
    if report.independent_weight > report.total_weight:
        raise ValueError("independent_weight must not exceed total_weight")
    if report.independent_source_coverage != _ratio(
        report.independent_weight,
        report.total_weight,
    ):
        raise ValueError("independent_source_coverage must match rows")
    expected_correlation_weights: dict[str, Decimal] = {}
    for row in report.rows:
        expected_correlation_weights[row.correlation_group_ref] = _quantize(
            expected_correlation_weights.get(row.correlation_group_ref, _ZERO)
            + row.weight,
        )
    expected_concentration = max(
        (
            _ratio(weight, report.total_weight)
            for weight in expected_correlation_weights.values()
        ),
        default=_ZERO,
    )
    if report.correlated_source_concentration != expected_concentration:
        raise ValueError("correlated_source_concentration must match rows")
    expected_official_primary = _ratio(
        _sum_decimal(
            tuple(
                row.weight
                for row in report.rows
                if row.source_role in _OFFICIAL_PRIMARY_SOURCE_ROLES
            ),
        ),
        report.total_weight,
    )
    if report.official_primary_source_presence != expected_official_primary:
        raise ValueError("official_primary_source_presence must match rows")
    expected_contradiction_diversity = _row_contradiction_diversity(report.rows)
    if report.contradiction_diversity != expected_contradiction_diversity:
        raise ValueError("contradiction_diversity must match rows")
    expected_freshness_quality = _row_freshness_quality(
        report.rows,
        report.total_weight,
    )
    if report.freshness_quality != expected_freshness_quality:
        raise ValueError("freshness_quality must match rows")
    _validate_row_consistency(
        report.rows,
        report.total_weight,
        pass_freshness_quality=report.pass_freshness_quality,
        blocked_freshness_quality=report.blocked_freshness_quality,
    )
    _validate_report_reason_code_surface(report)
    if report.status != _report_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_row_consistency(
    rows: tuple[ResearchSourceIndependenceDigestRow, ...],
    total_weight: Decimal,
    *,
    pass_freshness_quality: Decimal,
    blocked_freshness_quality: Decimal,
) -> None:
    correlation_weights: dict[str, Decimal] = {}
    correlation_counts: dict[str, Decimal] = {}
    for row in rows:
        correlation_weights[row.correlation_group_ref] = _quantize(
            correlation_weights.get(row.correlation_group_ref, _ZERO) + row.weight,
        )
        correlation_counts[row.correlation_group_ref] = _quantize(
            correlation_counts.get(row.correlation_group_ref, _ZERO) + _ONE,
        )
    for row in rows:
        source_group_is_independent = (
            correlation_counts[row.correlation_group_ref] == _ONE
        )
        expected_independent_weight = (
            row.weight if source_group_is_independent else _ZERO
        )
        if row.independent_weight != expected_independent_weight:
            raise ValueError("row independent_weight must match correlation grouping")
        expected_correlated_weight_share = _ratio(
            correlation_weights[row.correlation_group_ref],
            total_weight,
        )
        if row.correlated_weight_share != expected_correlated_weight_share:
            raise ValueError(
                "row correlated_weight_share must match correlation grouping",
            )
        expected_reason_codes = _row_reason_codes(
            source_group_is_independent=source_group_is_independent,
            source_role=row.source_role,
            stance=row.stance,
            freshness_quality=row.freshness_quality,
            pass_freshness_quality=pass_freshness_quality,
            blocked_freshness_quality=blocked_freshness_quality,
        )
        if row.reason_codes != expected_reason_codes:
            raise ValueError("row reason_codes must match row fields")


def _validate_report_reason_code_surface(
    report: ResearchSourceIndependenceDigestReport,
) -> None:
    if not report.rows:
        if report.reason_codes != (
            "empty_source_group_facts",
            "research_source_independence_blocked",
        ):
            raise ValueError("empty_source_group_facts reason_codes must match empty rows")
        if report.status != "blocked":
            raise ValueError("status must match empty_source_group_facts")
        return

    if "empty_source_group_facts" in report.reason_codes:
        raise ValueError("empty_source_group_facts requires an empty report")

    report_code_groups = (
        (
            "independent_source_coverage_pass",
            "independent_source_coverage_watch",
            "independent_source_coverage_blocked",
        ),
        (
            "correlated_source_concentration_pass",
            "correlated_source_concentration_watch",
            "correlated_source_concentration_blocked",
        ),
        (
            "official_or_primary_source_present",
            "official_or_primary_source_missing",
        ),
        (
            "contradiction_diversity_present",
            "contradiction_diversity_missing",
        ),
        (
            "freshness_quality_pass",
            "freshness_quality_watch",
            "freshness_quality_blocked",
        ),
    )
    terminal_codes = (
        "research_source_independence_pass",
        "research_source_independence_watch",
        "research_source_independence_blocked",
    )
    allowed_report_codes = frozenset(
        code for group in report_code_groups for code in group
    ) | frozenset(terminal_codes)
    for reason_code in report.reason_codes:
        if reason_code not in allowed_report_codes:
            raise ValueError("report reason_codes must use only report-level codes")
    for group in report_code_groups:
        if sum(reason_code in report.reason_codes for reason_code in group) != 1:
            raise ValueError("report reason_codes must include one code per category")
    terminal_reason_codes = tuple(
        reason_code for reason_code in terminal_codes if reason_code in report.reason_codes
    )
    metric_reason_codes = tuple(
        reason_code
        for reason_code in report.reason_codes
        if reason_code not in terminal_codes
    )
    expected_terminal_code = f"research_source_independence_{_report_status(metric_reason_codes)}"
    if terminal_reason_codes != (expected_terminal_code,):
        raise ValueError("report reason_codes must include one matching status code")
    if report.status != expected_terminal_code.removeprefix(
        "research_source_independence_",
    ):
        raise ValueError("status must match report reason_codes")


def _row_contradiction_diversity(
    rows: tuple[ResearchSourceIndependenceDigestRow, ...],
) -> Decimal:
    correlation_group_refs = {row.correlation_group_ref for row in rows}
    if not correlation_group_refs:
        return _ZERO
    contradicting_refs = {
        row.correlation_group_ref for row in rows if row.stance == "contradicting"
    }
    return _ratio(
        _decimal_count(len(contradicting_refs)),
        _decimal_count(len(correlation_group_refs)),
    )


def _row_freshness_quality(
    rows: tuple[ResearchSourceIndependenceDigestRow, ...],
    total_weight: Decimal,
) -> Decimal:
    if total_weight == _ZERO:
        return _ZERO
    weighted = _sum_decimal(
        tuple(row.freshness_quality * row.weight for row in rows),
    )
    return _ratio(weighted, total_weight)


def _normalize_rows(
    rows: Sequence[ResearchSourceIndependenceDigestRow],
) -> tuple[ResearchSourceIndependenceDigestRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchSourceIndependenceDigestRow] = []
    for row in rows:
        if type(row) is not ResearchSourceIndependenceDigestRow:
            raise ValueError("rows must contain ResearchSourceIndependenceDigestRow")
        _require_hard_flags("row", row)
        normalized.append(row)
    sorted_rows = tuple(sorted(normalized, key=lambda row: row.source_group_ref))
    if tuple(normalized) != sorted_rows:
        raise ValueError("rows must be sorted by source_group_ref")
    return sorted_rows


def _normalize_public_payload(
    public_payload: Sequence[ResearchSourceIndependencePublicPayloadItem],
) -> tuple[ResearchSourceIndependencePublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(
        public_payload,
        Sequence,
    ):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchSourceIndependencePublicPayloadItem] = []
    for item in public_payload:
        if type(item) is not ResearchSourceIndependencePublicPayloadItem:
            raise ValueError(
                "public_payload items must be ResearchSourceIndependencePublicPayloadItem",
            )
        _require_hard_flags("public payload item", item)
        normalized.append(item)
    sorted_items = tuple(sorted(normalized, key=lambda item: item.key))
    seen_keys: set[str] = set()
    for item in sorted_items:
        if item.key in seen_keys:
            raise ValueError("duplicate public_payload key")
        seen_keys.add(item.key)
    return sorted_items


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
        reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in normalized
    )


def _report_values_without_digest(
    report: ResearchSourceIndependenceDigestReport,
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


def _require_source_group_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _SOURCE_GROUP_REF_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a redacted source group ref")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_correlation_group_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _CORRELATION_GROUP_REF_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a redacted correlation group ref")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_key(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_KEY_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public key")
    _reject_unsafe_public_string(field_name, value)
    _reject_unsafe_public_key(value, field_name)
    return value


def _require_config_version(value: object) -> str:
    if type(value) is not str:
        raise ValueError("config_version must be a string")
    if value != DEFAULT_RESEARCH_SOURCE_INDEPENDENCE_DIGEST_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    _reject_unsafe_public_string("config_version", value)
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_member(field_name: str, value: object, allowed: frozenset[str]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be supported")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be a known status")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_REDACTION_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")
    if "_id" in lowered or lowered.endswith("id"):
        raise ValueError(f"{field_name} has unsafe public value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")
    if any(term in lowered for term in _UNSAFE_REDACTION_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")
    if "_id" in lowered or lowered.endswith("id"):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return _quantize(Decimal(value))


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    return _quantize(sum(values, _ZERO))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _clamp_ratio(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_INDEPENDENCE_DIGEST_CONFIG_VERSION",
    "ResearchSourceGroupFact",
    "ResearchSourceIndependenceDigestConfig",
    "ResearchSourceIndependenceDigestReport",
    "ResearchSourceIndependenceDigestRow",
    "ResearchSourceIndependencePublicPayloadItem",
    "build_research_source_independence_digest",
)
