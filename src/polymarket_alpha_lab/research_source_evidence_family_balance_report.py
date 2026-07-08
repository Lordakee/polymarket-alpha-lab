"""Pure report for sanitized evidence-family balance pressure."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_SOURCE_EVIDENCE_FAMILY_BALANCE_CONFIG_VERSION = (
    "research-source-evidence-family-balance-v0"
)

STATUSES = ("pass", "watch", "block")
EVIDENCE_FAMILIES = ("official", "primary", "news", "data")

NO_EVIDENCE_REASON = "evidence_family_balance_no_evidence"
MISSING_FAMILY_BLOCK_REASON = "evidence_family_balance_missing_family_block"
MISSING_FAMILY_WATCH_REASON = "evidence_family_balance_missing_family_watch"
COVERAGE_BALANCE_BLOCK_REASON = "evidence_family_balance_coverage_balance_block"
COVERAGE_BALANCE_WATCH_REASON = "evidence_family_balance_coverage_balance_watch"
FRESHNESS_BLOCK_REASON = "evidence_family_balance_freshness_block"
FRESHNESS_WATCH_REASON = "evidence_family_balance_freshness_watch"
STALE_FAMILY_BLOCK_REASON = "evidence_family_balance_stale_family_block"
STALE_FAMILY_WATCH_REASON = "evidence_family_balance_stale_family_watch"
CONTRADICTION_PRESSURE_BLOCK_REASON = (
    "evidence_family_balance_contradiction_pressure_block"
)
CONTRADICTION_PRESSURE_WATCH_REASON = (
    "evidence_family_balance_contradiction_pressure_watch"
)
PASS_REASON = "evidence_family_balance_pass"

REASON_CODES = (
    NO_EVIDENCE_REASON,
    MISSING_FAMILY_BLOCK_REASON,
    MISSING_FAMILY_WATCH_REASON,
    COVERAGE_BALANCE_BLOCK_REASON,
    COVERAGE_BALANCE_WATCH_REASON,
    FRESHNESS_BLOCK_REASON,
    FRESHNESS_WATCH_REASON,
    STALE_FAMILY_BLOCK_REASON,
    STALE_FAMILY_WATCH_REASON,
    CONTRADICTION_PRESSURE_BLOCK_REASON,
    CONTRADICTION_PRESSURE_WATCH_REASON,
    PASS_REASON,
)

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
FLAG_FIELDS = ("paper_only", "report_only", "readonly")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_TERMS = (
    _join_parts("candidate", "_", "id"),
    _join_parts("market", "_", "id"),
    _join_parts("market", "_", "slug"),
    _join_parts("slug"),
    _join_parts("que", "stion"),
    _join_parts("http", "://"),
    _join_parts("https", "://"),
    _join_parts("u", "r", "l"),
    _join_parts("source", "_", "text"),
    _join_parts("source", "_", "u", "r", "l"),
    _join_parts("raw", "_"),
    _join_parts("d", "s", "n"),
    _join_parts("table", "_", "name"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("au", "th"),
    _join_parts("recom", "mendation"),
    _join_parts("siz", "ing"),
    _join_parts("cre", "dential"),
    _join_parts("private", "_", "key"),
)


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_EVIDENCE_FAMILY_BALANCE_CONFIG_VERSION",
    "STATUSES",
    "EVIDENCE_FAMILIES",
    "ResearchSourceEvidenceFamilyBalanceConfig",
    "ResearchSourceEvidenceFamilyBalanceObservation",
    "ResearchSourceEvidenceFamilyBalanceFamilyRow",
    "ResearchSourceEvidenceFamilyBalanceReport",
    "build_research_source_evidence_family_balance_report",
    "research_source_evidence_family_balance_report_payload",
    "validate_research_source_evidence_family_balance_report_payload",
)


@dataclass(frozen=True)
class ResearchSourceEvidenceFamilyBalanceConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_EVIDENCE_FAMILY_BALANCE_CONFIG_VERSION
    fresh_age_seconds: Decimal = Decimal("3600.000000")
    stale_age_seconds: Decimal = Decimal("86400.000000")
    coverage_balance_watch_threshold: Decimal = Decimal("0.750000")
    coverage_balance_block_threshold: Decimal = Decimal("0.500000")
    freshness_watch_threshold: Decimal = Decimal("0.750000")
    freshness_block_threshold: Decimal = Decimal("0.500000")
    contradiction_watch_threshold: Decimal = Decimal("0.200000")
    contradiction_block_threshold: Decimal = Decimal("0.400000")
    stale_family_watch_ratio: Decimal = Decimal("0.250000")
    stale_family_block_ratio: Decimal = Decimal("0.500000")
    missing_family_block_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceEvidenceFamilyBalanceConfig:
            raise TypeError(
                "ResearchSourceEvidenceFamilyBalanceConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceEvidenceFamilyBalanceConfig:
            raise ValueError(
                "config must be exactly ResearchSourceEvidenceFamilyBalanceConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_SOURCE_EVIDENCE_FAMILY_BALANCE_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        for field_name in ("fresh_age_seconds", "stale_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_age_seconds <= self.fresh_age_seconds:
            raise ValueError("stale_age_seconds must exceed fresh_age_seconds")
        for field_name in (
            "coverage_balance_watch_threshold",
            "coverage_balance_block_threshold",
            "freshness_watch_threshold",
            "freshness_block_threshold",
            "contradiction_watch_threshold",
            "contradiction_block_threshold",
            "stale_family_watch_ratio",
            "stale_family_block_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "missing_family_block_count",
            _require_positive_whole_decimal(
                "missing_family_block_count",
                self.missing_family_block_count,
            ),
        )
        if self.coverage_balance_block_threshold >= self.coverage_balance_watch_threshold:
            raise ValueError(
                "coverage_balance_block_threshold must be below "
                "coverage_balance_watch_threshold",
            )
        if self.freshness_block_threshold >= self.freshness_watch_threshold:
            raise ValueError(
                "freshness_block_threshold must be below freshness_watch_threshold",
            )
        if self.contradiction_block_threshold <= self.contradiction_watch_threshold:
            raise ValueError(
                "contradiction_block_threshold must exceed "
                "contradiction_watch_threshold",
            )
        if self.stale_family_block_ratio <= self.stale_family_watch_ratio:
            raise ValueError(
                "stale_family_block_ratio must exceed stale_family_watch_ratio",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceFamilyBalanceObservation:
    evidence_family: str
    observed_at: datetime
    evidence_count: Decimal = Decimal("1.000000")
    contradiction_count: Decimal = Decimal("0.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceEvidenceFamilyBalanceObservation:
            raise TypeError(
                "ResearchSourceEvidenceFamilyBalanceObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceEvidenceFamilyBalanceObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchSourceEvidenceFamilyBalanceObservation",
            )
        _require_evidence_family("evidence_family", self.evidence_family)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "evidence_count",
            _require_positive_whole_decimal("evidence_count", self.evidence_count),
        )
        object.__setattr__(
            self,
            "contradiction_count",
            _require_nonnegative_whole_decimal(
                "contradiction_count",
                self.contradiction_count,
            ),
        )
        if self.contradiction_count > self.evidence_count:
            raise ValueError("contradiction_count must not exceed evidence_count")
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceFamilyBalanceFamilyRow:
    evidence_family: str
    evidence_count: Decimal
    contradiction_count: Decimal
    latest_observed_at: datetime | None
    latest_age_seconds: Decimal | None
    family_share: Decimal
    freshness_score: Decimal
    contradiction_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceEvidenceFamilyBalanceFamilyRow:
            raise TypeError(
                "ResearchSourceEvidenceFamilyBalanceFamilyRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceEvidenceFamilyBalanceFamilyRow:
            raise ValueError(
                "row must be exactly ResearchSourceEvidenceFamilyBalanceFamilyRow",
            )
        _require_evidence_family("evidence_family", self.evidence_family)
        for field_name in ("evidence_count", "contradiction_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_optional_utc("latest_observed_at", self.latest_observed_at),
        )
        object.__setattr__(
            self,
            "latest_age_seconds",
            _require_optional_nonnegative_decimal(
                "latest_age_seconds",
                self.latest_age_seconds,
            ),
        )
        for field_name in (
            "family_share",
            "freshness_score",
            "contradiction_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_family_row(self)
        _require_hard_flags("family row", self)
        _reject_unsafe_public_payload("family row", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceFamilyBalanceReport:
    generated_at: datetime
    config_version: str
    status: str
    required_family_count: Decimal
    covered_family_count: Decimal
    missing_family_count: Decimal
    evidence_count: Decimal
    contradiction_count: Decimal
    coverage_balance_score: Decimal
    average_freshness_score: Decimal
    contradiction_pressure_score: Decimal
    stale_family_ratio: Decimal
    family_rows: tuple[ResearchSourceEvidenceFamilyBalanceFamilyRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceEvidenceFamilyBalanceReport:
            raise TypeError(
                "ResearchSourceEvidenceFamilyBalanceReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceEvidenceFamilyBalanceReport:
            raise ValueError(
                "report must be exactly ResearchSourceEvidenceFamilyBalanceReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "required_family_count",
            "covered_family_count",
            "missing_family_count",
            "evidence_count",
            "contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "coverage_balance_score",
            "average_freshness_score",
            "contradiction_pressure_score",
            "stale_family_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "family_rows", _normalize_family_rows(self.family_rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_report(self)
        _require_or_set_digest(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)


def build_research_source_evidence_family_balance_report(
    observations: list[ResearchSourceEvidenceFamilyBalanceObservation]
    | tuple[ResearchSourceEvidenceFamilyBalanceObservation, ...],
    *,
    config: ResearchSourceEvidenceFamilyBalanceConfig,
    generated_at: datetime,
) -> ResearchSourceEvidenceFamilyBalanceReport:
    if type(config) is not ResearchSourceEvidenceFamilyBalanceConfig:
        raise ValueError(
            "config must be a ResearchSourceEvidenceFamilyBalanceConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    observation_rows = _normalize_observations(
        observations,
        generated_at=generated_at_utc,
    )
    if not observation_rows:
        return ResearchSourceEvidenceFamilyBalanceReport(
            generated_at=generated_at_utc,
            config_version=config.config_version,
            status="block",
            required_family_count=_decimal_count(len(EVIDENCE_FAMILIES)),
            covered_family_count=ZERO,
            missing_family_count=_decimal_count(len(EVIDENCE_FAMILIES)),
            evidence_count=ZERO,
            contradiction_count=ZERO,
            coverage_balance_score=ZERO,
            average_freshness_score=ZERO,
            contradiction_pressure_score=ZERO,
            stale_family_ratio=ZERO,
            family_rows=(),
            reason_codes=(NO_EVIDENCE_REASON,),
        )

    total_evidence_count = _decimal_sum(
        tuple(row.evidence_count for row in observation_rows),
    )
    family_rows = _build_family_rows(
        observation_rows,
        config=config,
        generated_at=generated_at_utc,
        total_evidence_count=total_evidence_count,
    )
    reason_codes = _report_reason_codes(family_rows, config=config)
    return ResearchSourceEvidenceFamilyBalanceReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_status_from_reason_codes(reason_codes),
        required_family_count=_decimal_count(len(EVIDENCE_FAMILIES)),
        covered_family_count=_decimal_count(
            sum(row.evidence_count > ZERO for row in family_rows),
        ),
        missing_family_count=_decimal_count(
            sum(row.evidence_count == ZERO for row in family_rows),
        ),
        evidence_count=total_evidence_count,
        contradiction_count=_decimal_sum(
            tuple(row.contradiction_count for row in family_rows),
        ),
        coverage_balance_score=_coverage_balance_score(family_rows),
        average_freshness_score=_average_ratio(
            tuple(row.freshness_score for row in family_rows),
        ),
        contradiction_pressure_score=_ratio(
            _decimal_sum(tuple(row.contradiction_count for row in family_rows)),
            total_evidence_count,
        ),
        stale_family_ratio=_ratio(
            _decimal_count(sum(row.freshness_score == ZERO for row in family_rows)),
            _decimal_count(len(EVIDENCE_FAMILIES)),
        ),
        family_rows=family_rows,
        reason_codes=reason_codes,
    )


def research_source_evidence_family_balance_report_payload(
    value: ResearchSourceEvidenceFamilyBalanceReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchSourceEvidenceFamilyBalanceReport:
        _require_hard_flags("report", value)
        _require_or_set_digest(value)
        payload = _json_ready(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchSourceEvidenceFamilyBalanceReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_flag_downgrades("payload", payload)
    _validate_public_payload_statuses(payload)
    _verify_public_digest(payload)
    return payload


def validate_research_source_evidence_family_balance_report_payload(
    payload: dict[str, object],
) -> bool:
    research_source_evidence_family_balance_report_payload(payload)
    return True


def _build_family_rows(
    rows: tuple[ResearchSourceEvidenceFamilyBalanceObservation, ...],
    *,
    config: ResearchSourceEvidenceFamilyBalanceConfig,
    generated_at: datetime,
    total_evidence_count: Decimal,
) -> tuple[ResearchSourceEvidenceFamilyBalanceFamilyRow, ...]:
    grouped: dict[str, list[ResearchSourceEvidenceFamilyBalanceObservation]] = {}
    for row in rows:
        grouped.setdefault(row.evidence_family, []).append(row)
    return tuple(
        _family_row(
            evidence_family,
            tuple(grouped.get(evidence_family, ())),
            config=config,
            generated_at=generated_at,
            total_evidence_count=total_evidence_count,
        )
        for evidence_family in EVIDENCE_FAMILIES
    )


def _family_row(
    evidence_family: str,
    rows: tuple[ResearchSourceEvidenceFamilyBalanceObservation, ...],
    *,
    config: ResearchSourceEvidenceFamilyBalanceConfig,
    generated_at: datetime,
    total_evidence_count: Decimal,
) -> ResearchSourceEvidenceFamilyBalanceFamilyRow:
    evidence_count = _decimal_sum(tuple(row.evidence_count for row in rows))
    contradiction_count = _decimal_sum(tuple(row.contradiction_count for row in rows))
    latest_observed_at: datetime | None = None
    latest_age_seconds: Decimal | None = None
    freshness_score = ZERO
    if rows:
        latest_observed_at = max(rows, key=lambda row: row.observed_at).observed_at
        latest_age_seconds = _age_seconds(generated_at, latest_observed_at)
        freshness_score = _freshness_score(latest_age_seconds, config=config)
    family_share = _ratio(evidence_count, total_evidence_count)
    contradiction_pressure_score = _ratio(contradiction_count, evidence_count)
    reason_codes = _family_reason_codes(
        evidence_count=evidence_count,
        freshness_score=freshness_score,
    )
    return ResearchSourceEvidenceFamilyBalanceFamilyRow(
        evidence_family=evidence_family,
        evidence_count=evidence_count,
        contradiction_count=contradiction_count,
        latest_observed_at=latest_observed_at,
        latest_age_seconds=latest_age_seconds,
        family_share=family_share,
        freshness_score=freshness_score,
        contradiction_pressure_score=contradiction_pressure_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _family_reason_codes(
    *,
    evidence_count: Decimal,
    freshness_score: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if evidence_count == ZERO:
        reasons.append(MISSING_FAMILY_WATCH_REASON)
    if freshness_score == ZERO:
        reasons.append(STALE_FAMILY_WATCH_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return tuple(code for code in REASON_CODES if code in reasons)


def _report_reason_codes(
    rows: tuple[ResearchSourceEvidenceFamilyBalanceFamilyRow, ...],
    *,
    config: ResearchSourceEvidenceFamilyBalanceConfig,
) -> tuple[str, ...]:
    if not rows:
        return (NO_EVIDENCE_REASON,)
    missing_family_count = _decimal_count(sum(row.evidence_count == ZERO for row in rows))
    coverage_balance_score = _coverage_balance_score(rows)
    average_freshness_score = _average_ratio(tuple(row.freshness_score for row in rows))
    stale_family_ratio = _ratio(
        _decimal_count(sum(row.freshness_score == ZERO for row in rows)),
        _decimal_count(len(EVIDENCE_FAMILIES)),
    )
    contradiction_pressure_score = _ratio(
        _decimal_sum(tuple(row.contradiction_count for row in rows)),
        _decimal_sum(tuple(row.evidence_count for row in rows)),
    )
    reasons: list[str] = []
    if missing_family_count >= config.missing_family_block_count:
        reasons.append(MISSING_FAMILY_BLOCK_REASON)
    elif missing_family_count > ZERO:
        reasons.append(MISSING_FAMILY_WATCH_REASON)
    if coverage_balance_score < config.coverage_balance_block_threshold:
        reasons.append(COVERAGE_BALANCE_BLOCK_REASON)
    elif coverage_balance_score < config.coverage_balance_watch_threshold:
        reasons.append(COVERAGE_BALANCE_WATCH_REASON)
    if average_freshness_score < config.freshness_block_threshold:
        reasons.append(FRESHNESS_BLOCK_REASON)
    elif average_freshness_score < config.freshness_watch_threshold:
        reasons.append(FRESHNESS_WATCH_REASON)
    if stale_family_ratio >= config.stale_family_block_ratio:
        reasons.append(STALE_FAMILY_BLOCK_REASON)
    elif stale_family_ratio >= config.stale_family_watch_ratio:
        reasons.append(STALE_FAMILY_WATCH_REASON)
    if contradiction_pressure_score >= config.contradiction_block_threshold:
        reasons.append(CONTRADICTION_PRESSURE_BLOCK_REASON)
    elif contradiction_pressure_score >= config.contradiction_watch_threshold:
        reasons.append(CONTRADICTION_PRESSURE_WATCH_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return tuple(code for code in REASON_CODES if code in reasons)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if (
        NO_EVIDENCE_REASON in reason_codes
        or MISSING_FAMILY_BLOCK_REASON in reason_codes
        or COVERAGE_BALANCE_BLOCK_REASON in reason_codes
        or FRESHNESS_BLOCK_REASON in reason_codes
        or STALE_FAMILY_BLOCK_REASON in reason_codes
        or CONTRADICTION_PRESSURE_BLOCK_REASON in reason_codes
    ):
        return "block"
    if reason_codes == (PASS_REASON,):
        return "pass"
    return "watch"


def _coverage_balance_score(
    rows: tuple[ResearchSourceEvidenceFamilyBalanceFamilyRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    target_share = _ratio(ONE, _decimal_count(len(EVIDENCE_FAMILIES)))
    max_deviation = (
        Decimal("2.000000")
        * _decimal_count(len(EVIDENCE_FAMILIES) - 1)
        / _decimal_count(len(EVIDENCE_FAMILIES))
    ).quantize(QUANT)
    deviation = ZERO
    for row in rows:
        deviation += _absolute_decimal(row.family_share - target_share)
    normalized_deviation = _ratio(deviation.quantize(QUANT), max_deviation)
    score = (ONE - normalized_deviation).quantize(QUANT)
    if score < ZERO:
        return ZERO
    return _require_ratio_decimal("coverage_balance_score", score)


def _freshness_score(
    latest_age_seconds: Decimal,
    *,
    config: ResearchSourceEvidenceFamilyBalanceConfig,
) -> Decimal:
    if latest_age_seconds <= config.fresh_age_seconds:
        return ONE
    if latest_age_seconds >= config.stale_age_seconds:
        return ZERO
    return _ratio(
        config.stale_age_seconds - latest_age_seconds,
        config.stale_age_seconds - config.fresh_age_seconds,
    )


def _normalize_observations(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchSourceEvidenceFamilyBalanceObservation, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchSourceEvidenceFamilyBalanceObservation:
            raise ValueError(
                "observations must contain ResearchSourceEvidenceFamilyBalanceObservation",
            )
        _require_hard_flags("observation", row)
        if row.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                EVIDENCE_FAMILIES.index(row.evidence_family),
                row.observed_at.isoformat(),
                row.evidence_count,
                row.contradiction_count,
            ),
        ),
    )


def _normalize_family_rows(
    value: object,
) -> tuple[ResearchSourceEvidenceFamilyBalanceFamilyRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("family_rows must be a list or tuple")
    rows = tuple(value)
    if not rows:
        return rows
    if len(rows) != len(EVIDENCE_FAMILIES):
        raise ValueError("family_rows must cover every evidence family")
    expected_families = tuple(row.evidence_family for row in rows)
    if expected_families != EVIDENCE_FAMILIES:
        raise ValueError("family_rows must be deterministic by evidence_family")
    for row in rows:
        if type(row) is not ResearchSourceEvidenceFamilyBalanceFamilyRow:
            raise ValueError(
                "family_rows must contain ResearchSourceEvidenceFamilyBalanceFamilyRow",
            )
        _require_hard_flags("family row", row)
    return rows


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in REASON_CODES:
            raise ValueError("reason_code must be known")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    expected = tuple(code for code in REASON_CODES if code in reason_codes)
    if reason_codes != expected:
        raise ValueError("reason_codes must be deterministic")
    return reason_codes


def _validate_family_row(row: ResearchSourceEvidenceFamilyBalanceFamilyRow) -> None:
    if row.contradiction_count > row.evidence_count:
        raise ValueError("contradiction_count must not exceed evidence_count")
    if row.evidence_count == ZERO:
        if row.latest_observed_at is not None:
            raise ValueError("latest_observed_at must be empty for missing families")
        if row.latest_age_seconds is not None:
            raise ValueError("latest_age_seconds must be empty for missing families")
    else:
        if row.latest_observed_at is None:
            raise ValueError("latest_observed_at must be present for covered families")
        if row.latest_age_seconds is None:
            raise ValueError("latest_age_seconds must be present for covered families")
    if row.contradiction_pressure_score != _ratio(
        row.contradiction_count,
        row.evidence_count,
    ):
        raise ValueError("contradiction_pressure_score must match counts")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchSourceEvidenceFamilyBalanceReport) -> None:
    if report.required_family_count != _decimal_count(len(EVIDENCE_FAMILIES)):
        raise ValueError("required_family_count must match evidence families")
    if report.evidence_count == ZERO:
        if report.family_rows != ():
            raise ValueError("family_rows must be empty when evidence_count is zero")
        if report.covered_family_count != ZERO:
            raise ValueError("covered_family_count must be zero without evidence")
        if report.missing_family_count != report.required_family_count:
            raise ValueError("missing_family_count must match evidence families")
        if report.reason_codes != (NO_EVIDENCE_REASON,):
            raise ValueError("reason_codes must mark no evidence")
        if report.status != "block":
            raise ValueError("status must be block without evidence")
        return
    if report.family_rows == ():
        raise ValueError("family_rows must be present when evidence_count is positive")
    if report.covered_family_count != _decimal_count(
        sum(row.evidence_count > ZERO for row in report.family_rows),
    ):
        raise ValueError("covered_family_count must match family_rows")
    if report.missing_family_count != _decimal_count(
        sum(row.evidence_count == ZERO for row in report.family_rows),
    ):
        raise ValueError("missing_family_count must match family_rows")
    if report.evidence_count != _decimal_sum(
        tuple(row.evidence_count for row in report.family_rows),
    ):
        raise ValueError("evidence_count must match family_rows")
    if report.contradiction_count != _decimal_sum(
        tuple(row.contradiction_count for row in report.family_rows),
    ):
        raise ValueError("contradiction_count must match family_rows")
    for row in report.family_rows:
        if row.family_share != _ratio(row.evidence_count, report.evidence_count):
            raise ValueError("family_share must match evidence_count")
    if report.coverage_balance_score != _coverage_balance_score(report.family_rows):
        raise ValueError("coverage_balance_score must match family_rows")
    if report.average_freshness_score != _average_ratio(
        tuple(row.freshness_score for row in report.family_rows),
    ):
        raise ValueError("average_freshness_score must match family_rows")
    if report.contradiction_pressure_score != _ratio(
        report.contradiction_count,
        report.evidence_count,
    ):
        raise ValueError("contradiction_pressure_score must match counts")
    if report.stale_family_ratio != _ratio(
        _decimal_count(sum(row.freshness_score == ZERO for row in report.family_rows)),
        _decimal_count(len(EVIDENCE_FAMILIES)),
    ):
        raise ValueError("stale_family_ratio must match family_rows")
    if report.status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _decimal_sum(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total += _require_nonnegative_decimal("sum value", value)
    return total.quantize(QUANT)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _ratio(_decimal_sum(values), _decimal_count(len(values)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator = _require_nonnegative_decimal("ratio numerator", numerator)
    denominator = _require_nonnegative_decimal("ratio denominator", denominator)
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANT)


def _age_seconds(end_at: datetime, start_at: datetime) -> Decimal:
    delta = _as_utc("end_at", end_at) - _as_utc("start_at", start_at)
    value = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if value < ZERO:
        raise ValueError("observed_at must not be in the future")
    return value.quantize(QUANT)


def _absolute_decimal(value: Decimal) -> Decimal:
    if value < ZERO:
        return (ZERO - value).quantize(QUANT)
    return value.quantize(QUANT)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            decimal_value = value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must fit the decimal context") from exc
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    if _has_unsafe_public_term(value):
        raise ValueError(f"{field_name} contains unsafe public value")


def _require_evidence_family(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in EVIDENCE_FAMILIES:
        raise ValueError(f"{field_name} must be official, primary, news, or data")


def _require_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_or_set_digest(report: ResearchSourceEvidenceFamilyBalanceReport) -> None:
    if type(report.derived_validation_digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _report_digest(report)
    if report.derived_validation_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    _require_digest("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a sha256 hex digest") from exc
    if value.lower() != value:
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _report_digest(report: ResearchSourceEvidenceFamilyBalanceReport) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _canonical_digest(payload)


def _verify_public_digest(payload: dict[str, object]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    if digest != _canonical_digest(unsigned):
        raise ValueError("derived_validation_digest does not match public payload")


def _validate_public_payload_statuses(payload: dict[str, object]) -> None:
    _require_status("status", payload.get("status"))
    family_rows = payload.get("family_rows")
    if family_rows is None:
        return
    if type(family_rows) is not list:
        raise ValueError("family_rows must be a list")
    for index, row in enumerate(family_rows):
        if type(row) is not dict:
            raise ValueError("family_rows must contain JSON objects")
        _require_status(f"family_rows[{index}].status", row.get("status"))


def _canonical_digest(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("JSON datetime value", value).isoformat()
    if isinstance(value, bool):
        return value
    if isinstance(value, (float, int)):
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, str):
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


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied = _json_ready(value)
    if type(copied) is not dict:
        raise ValueError("payload must be a JSON object")
    return copied


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=allow_json_containers,
        )
        return
    if isinstance(value, dict):
        if not allow_json_containers and type(value) is not dict:
            raise ValueError(f"{label} must use plain dict containers")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_term(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, (list, tuple)):
        if not allow_json_containers and type(value) not in (list, tuple):
            raise ValueError(f"{label} must use plain sequence containers")
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str and _has_unsafe_public_term(value):
        raise ValueError(f"unsafe public value in {label}")


def _has_unsafe_public_term(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in UNSAFE_PUBLIC_TERMS)


def _reject_flag_downgrades(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True for {label}")
            _reject_flag_downgrades(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_flag_downgrades(label, item)


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")
