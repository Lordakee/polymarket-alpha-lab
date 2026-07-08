"""Pure report-only specialist score normalization reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_DOMAIN_SPECIALIST_SCORE_NORMALIZATION_CONFIG_VERSION = (
    "research-domain-specialist-score-normalization-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DOMAIN_SEQUENCE = (
    "politics",
    "crypto",
    "equities",
    "gold",
    "soccer",
    "basketball",
    "other",
)
_STATUS_SEQUENCE = ("pass", "watch", "block")
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_UNSAFE_PUBLIC_TERMS = (
    "event",
    "market",
    "source",
    "wallet",
    "auth",
    "order",
    "trade",
    "live",
    "execution",
    "recommendation",
    "sizing",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
)
_REASON_CODE_SEQUENCE = (
    "empty_domains",
    "aggregate_calibration_block",
    "evidence_quality_block",
    "freshness_block",
    "capacity_block",
    "normalized_score_block",
    "aggregate_calibration_watch",
    "evidence_quality_watch",
    "freshness_watch",
    "capacity_watch",
    "normalized_score_watch",
    "normalization_pass",
)


@dataclass(frozen=True)
class ResearchDomainSpecialistScoreNormalizationConfig:
    config_version: str = (
        DEFAULT_RESEARCH_DOMAIN_SPECIALIST_SCORE_NORMALIZATION_CONFIG_VERSION
    )
    aggregate_calibration_weight: Decimal = Decimal("0.350000")
    evidence_quality_weight: Decimal = Decimal("0.350000")
    freshness_weight: Decimal = Decimal("0.150000")
    capacity_weight: Decimal = Decimal("0.150000")
    freshness_window_seconds: Decimal = Decimal("86400.000000")
    pass_min_normalized_score: Decimal = Decimal("0.600000")
    block_max_normalized_score: Decimal = Decimal("0.300000")
    watch_min_component_score: Decimal = Decimal("0.600000")
    block_max_component_score: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainSpecialistScoreNormalizationConfig:
            raise TypeError(
                "ResearchDomainSpecialistScoreNormalizationConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainSpecialistScoreNormalizationConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchDomainSpecialistScoreNormalizationConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_DOMAIN_SPECIALIST_SCORE_NORMALIZATION_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "aggregate_calibration_weight",
            "evidence_quality_weight",
            "freshness_weight",
            "capacity_weight",
            "pass_min_normalized_score",
            "block_max_normalized_score",
            "watch_min_component_score",
            "block_max_component_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "freshness_window_seconds",
            _require_positive_decimal(
                "freshness_window_seconds",
                self.freshness_window_seconds,
            ),
        )
        if _component_weight_total(self) != _ONE:
            raise ValueError("component weights must sum to one")
        if self.block_max_normalized_score >= self.pass_min_normalized_score:
            raise ValueError(
                "pass_min_normalized_score must exceed block_max_normalized_score",
            )
        if self.block_max_component_score >= self.watch_min_component_score:
            raise ValueError(
                "watch_min_component_score must exceed block_max_component_score",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchDomainSpecialistScoreInput:
    domain: str
    team_label: str
    observed_at: datetime
    raw_research_score: Decimal
    aggregate_calibration_score: Decimal
    evidence_quality_score: Decimal
    capacity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainSpecialistScoreInput:
            raise TypeError(
                "ResearchDomainSpecialistScoreInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainSpecialistScoreInput:
            raise ValueError("input must be exactly ResearchDomainSpecialistScoreInput")
        object.__setattr__(self, "domain", _require_domain("domain", self.domain))
        _require_public_identifier("team_label", self.team_label)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "raw_research_score",
            "aggregate_calibration_score",
            "evidence_quality_score",
            "capacity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchDomainSpecialistScoreNormalizationRow:
    domain: str
    team_label: str
    observed_at: datetime
    age_seconds: Decimal
    raw_research_score: Decimal
    aggregate_calibration_score: Decimal
    evidence_quality_score: Decimal
    freshness_score: Decimal
    capacity_score: Decimal
    normalized_score: Decimal
    score_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainSpecialistScoreNormalizationRow:
            raise TypeError(
                "ResearchDomainSpecialistScoreNormalizationRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainSpecialistScoreNormalizationRow:
            raise ValueError(
                "row must be exactly ResearchDomainSpecialistScoreNormalizationRow",
            )
        object.__setattr__(self, "domain", _require_domain("domain", self.domain))
        _require_public_identifier("team_label", self.team_label)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "age_seconds",
            _require_nonnegative_decimal("age_seconds", self.age_seconds),
        )
        for field_name in (
            "raw_research_score",
            "aggregate_calibration_score",
            "evidence_quality_score",
            "freshness_score",
            "capacity_score",
            "normalized_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("score_status", self.score_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchDomainSpecialistScoreDomainSummary:
    domain: str
    team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_normalized_score: Decimal
    domain_status: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainSpecialistScoreDomainSummary:
            raise TypeError(
                "ResearchDomainSpecialistScoreDomainSummary does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainSpecialistScoreDomainSummary:
            raise ValueError(
                "domain summary must be exactly "
                "ResearchDomainSpecialistScoreDomainSummary",
            )
        object.__setattr__(self, "domain", _require_domain("domain", self.domain))
        for field_name in ("team_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_normalized_score",
            _require_ratio_decimal(
                "average_normalized_score",
                self.average_normalized_score,
            ),
        )
        _require_status("domain_status", self.domain_status)
        _validate_domain_summary_consistency(self)
        _require_hard_flags("domain summary", self)
        _reject_unsafe_public_payload("domain summary", self)


@dataclass(frozen=True)
class ResearchDomainSpecialistScoreNormalizationReport:
    generated_at: datetime
    config_version: str
    report_status: str
    domain_count: Decimal
    team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_normalized_score: Decimal
    rows: tuple[ResearchDomainSpecialistScoreNormalizationRow, ...]
    domain_summaries: tuple[ResearchDomainSpecialistScoreDomainSummary, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainSpecialistScoreNormalizationReport:
            raise TypeError(
                "ResearchDomainSpecialistScoreNormalizationReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainSpecialistScoreNormalizationReport:
            raise ValueError(
                "report must be exactly ResearchDomainSpecialistScoreNormalizationReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_DOMAIN_SPECIALIST_SCORE_NORMALIZATION_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("report_status", self.report_status)
        for field_name in (
            "domain_count",
            "team_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_normalized_score",
            _require_ratio_decimal(
                "average_normalized_score",
                self.average_normalized_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "domain_summaries",
            _normalize_domain_summaries(self.domain_summaries),
        )
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
        _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_domain_specialist_score_normalization_report(
    inputs: Sequence[ResearchDomainSpecialistScoreInput],
    *,
    generated_at: datetime,
    config: ResearchDomainSpecialistScoreNormalizationConfig | None = None,
) -> ResearchDomainSpecialistScoreNormalizationReport:
    """Build a local report-only normalized specialist score snapshot."""

    if config is None:
        config = ResearchDomainSpecialistScoreNormalizationConfig()
    if type(config) is not ResearchDomainSpecialistScoreNormalizationConfig:
        raise ValueError(
            "config must be a ResearchDomainSpecialistScoreNormalizationConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for item in normalized_inputs:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        _build_row(item, generated_at=generated_at, config=config)
        for item in normalized_inputs
    )
    summaries = _build_domain_summaries(rows)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "report_status": _report_status(rows),
        "domain_count": _decimal_count(len({row.domain for row in rows})),
        "team_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_normalized_score": _average(
            tuple(row.normalized_score for row in rows),
        ),
        "rows": rows,
        "domain_summaries": summaries,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchDomainSpecialistScoreNormalizationReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _build_row(
    item: ResearchDomainSpecialistScoreInput,
    *,
    generated_at: datetime,
    config: ResearchDomainSpecialistScoreNormalizationConfig,
) -> ResearchDomainSpecialistScoreNormalizationRow:
    age_seconds = _datetime_delta_seconds(generated_at, item.observed_at)
    freshness_score = _freshness_score(age_seconds, config.freshness_window_seconds)
    normalized_score = _normalized_score(
        raw_research_score=item.raw_research_score,
        aggregate_calibration_score=item.aggregate_calibration_score,
        evidence_quality_score=item.evidence_quality_score,
        freshness_score=freshness_score,
        capacity_score=item.capacity_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        aggregate_calibration_score=item.aggregate_calibration_score,
        evidence_quality_score=item.evidence_quality_score,
        freshness_score=freshness_score,
        capacity_score=item.capacity_score,
        normalized_score=normalized_score,
        config=config,
    )
    return ResearchDomainSpecialistScoreNormalizationRow(
        domain=item.domain,
        team_label=item.team_label,
        observed_at=item.observed_at,
        age_seconds=age_seconds,
        raw_research_score=item.raw_research_score,
        aggregate_calibration_score=item.aggregate_calibration_score,
        evidence_quality_score=item.evidence_quality_score,
        freshness_score=freshness_score,
        capacity_score=item.capacity_score,
        normalized_score=normalized_score,
        score_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _build_domain_summaries(
    rows: tuple[ResearchDomainSpecialistScoreNormalizationRow, ...],
) -> tuple[ResearchDomainSpecialistScoreDomainSummary, ...]:
    summaries: list[ResearchDomainSpecialistScoreDomainSummary] = []
    for domain in _DOMAIN_SEQUENCE:
        domain_rows = tuple(row for row in rows if row.domain == domain)
        if not domain_rows:
            continue
        summaries.append(
            ResearchDomainSpecialistScoreDomainSummary(
                domain=domain,
                team_count=_decimal_count(len(domain_rows)),
                pass_count=_decimal_count(_status_count(domain_rows, "pass")),
                watch_count=_decimal_count(_status_count(domain_rows, "watch")),
                block_count=_decimal_count(_status_count(domain_rows, "block")),
                average_normalized_score=_average(
                    tuple(row.normalized_score for row in domain_rows),
                ),
                domain_status=_report_status(domain_rows),
            ),
        )
    return tuple(summaries)


def _normalize_inputs(
    inputs: Sequence[ResearchDomainSpecialistScoreInput],
) -> tuple[ResearchDomainSpecialistScoreInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Sequence):
        raise ValueError("inputs must be a sequence")
    normalized: list[ResearchDomainSpecialistScoreInput] = []
    seen: set[tuple[str, str]] = set()
    for item in inputs:
        if type(item) is not ResearchDomainSpecialistScoreInput:
            raise ValueError("inputs must contain ResearchDomainSpecialistScoreInput")
        _require_hard_flags("input", item)
        key = (item.domain, item.team_label)
        if key in seen:
            raise ValueError("inputs must not contain duplicate domain team labels")
        seen.add(key)
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (_domain_rank(item.domain), item.team_label),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchDomainSpecialistScoreNormalizationRow],
) -> tuple[ResearchDomainSpecialistScoreNormalizationRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchDomainSpecialistScoreNormalizationRow] = []
    for row in rows:
        if type(row) is not ResearchDomainSpecialistScoreNormalizationRow:
            raise ValueError(
                "rows must contain ResearchDomainSpecialistScoreNormalizationRow",
            )
        normalized.append(row)
    return tuple(
        sorted(
            normalized,
            key=lambda row: (_domain_rank(row.domain), row.team_label),
        ),
    )


def _normalize_domain_summaries(
    summaries: Sequence[ResearchDomainSpecialistScoreDomainSummary],
) -> tuple[ResearchDomainSpecialistScoreDomainSummary, ...]:
    if isinstance(summaries, (str, bytes)) or not isinstance(summaries, Sequence):
        raise ValueError("domain_summaries must be a sequence")
    normalized: list[ResearchDomainSpecialistScoreDomainSummary] = []
    seen: set[str] = set()
    for summary in summaries:
        if type(summary) is not ResearchDomainSpecialistScoreDomainSummary:
            raise ValueError(
                "domain_summaries must contain "
                "ResearchDomainSpecialistScoreDomainSummary",
            )
        if summary.domain in seen:
            raise ValueError("domain_summaries must not contain duplicate domains")
        seen.add(summary.domain)
        normalized.append(summary)
    return tuple(sorted(normalized, key=lambda summary: _domain_rank(summary.domain)))


def _row_reason_codes(
    *,
    aggregate_calibration_score: Decimal,
    evidence_quality_score: Decimal,
    freshness_score: Decimal,
    capacity_score: Decimal,
    normalized_score: Decimal,
    config: ResearchDomainSpecialistScoreNormalizationConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_component_reason(
        reason_codes,
        "aggregate_calibration",
        aggregate_calibration_score,
        config,
    )
    _append_component_reason(
        reason_codes,
        "evidence_quality",
        evidence_quality_score,
        config,
    )
    _append_component_reason(reason_codes, "freshness", freshness_score, config)
    _append_component_reason(reason_codes, "capacity", capacity_score, config)
    if normalized_score <= config.block_max_normalized_score:
        reason_codes.append("normalized_score_block")
    elif normalized_score < config.pass_min_normalized_score:
        reason_codes.append("normalized_score_watch")
    if not reason_codes:
        reason_codes.append("normalization_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _append_component_reason(
    reason_codes: list[str],
    prefix: str,
    value: Decimal,
    config: ResearchDomainSpecialistScoreNormalizationConfig,
) -> None:
    if value <= config.block_max_component_score:
        reason_codes.append(f"{prefix}_block")
    elif value < config.watch_min_component_score:
        reason_codes.append(f"{prefix}_watch")


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if reason_codes == ("normalization_pass",):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchDomainSpecialistScoreNormalizationRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.score_status == "block" for row in rows):
        return "block"
    if any(row.score_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchDomainSpecialistScoreNormalizationRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_domains",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _validate_row_consistency(
    row: ResearchDomainSpecialistScoreNormalizationRow,
) -> None:
    expected_status = _row_status(row.reason_codes)
    if row.score_status != expected_status:
        raise ValueError("score_status must match reason_codes")
    if row.score_status == "pass" and row.reason_codes != ("normalization_pass",):
        raise ValueError("pass rows must contain only normalization_pass")
    if row.score_status != "pass" and row.reason_codes == ("normalization_pass",):
        raise ValueError("watch and block rows must include risk reason codes")


def _validate_domain_summary_consistency(
    summary: ResearchDomainSpecialistScoreDomainSummary,
) -> None:
    if summary.team_count != _quantize(
        summary.pass_count + summary.watch_count + summary.block_count,
    ):
        raise ValueError("team_count must match status counts")
    if summary.team_count == _ZERO:
        raise ValueError("team_count must be positive")
    expected_status = _status_from_counts(
        block_count=summary.block_count,
        watch_count=summary.watch_count,
    )
    if summary.domain_status != expected_status:
        raise ValueError("domain_status must match status counts")


def _validate_report_consistency(
    report: ResearchDomainSpecialistScoreNormalizationReport,
) -> None:
    if report.rows != _normalize_rows(report.rows):
        raise ValueError("rows must be sorted deterministically")
    if report.domain_summaries != _build_domain_summaries(report.rows):
        raise ValueError("domain_summaries must match rows")
    if report.domain_count != _decimal_count(len({row.domain for row in report.rows})):
        raise ValueError("domain_count must match rows")
    if report.team_count != _decimal_count(len(report.rows)):
        raise ValueError("team_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_normalized_score != _average(
        tuple(row.normalized_score for row in report.rows),
    ):
        raise ValueError("average_normalized_score must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _status_from_counts(*, block_count: Decimal, watch_count: Decimal) -> str:
    if block_count > _ZERO:
        return "block"
    if watch_count > _ZERO:
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchDomainSpecialistScoreNormalizationRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.score_status == status)


def _normalized_score(
    *,
    raw_research_score: Decimal,
    aggregate_calibration_score: Decimal,
    evidence_quality_score: Decimal,
    freshness_score: Decimal,
    capacity_score: Decimal,
    config: ResearchDomainSpecialistScoreNormalizationConfig,
) -> Decimal:
    calibration_factor = _quantize(
        aggregate_calibration_score * config.aggregate_calibration_weight
        + evidence_quality_score * config.evidence_quality_weight
        + freshness_score * config.freshness_weight
        + capacity_score * config.capacity_weight,
    )
    return _clamp_ratio(_quantize(raw_research_score * calibration_factor))


def _freshness_score(age_seconds: Decimal, freshness_window_seconds: Decimal) -> Decimal:
    if age_seconds >= freshness_window_seconds:
        return _ZERO
    return _clamp_ratio(_quantize(_ONE - (age_seconds / freshness_window_seconds)))


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    microseconds = Decimal(delta.microseconds) / Decimal("1000000")
    return _quantize(seconds + microseconds)


def _component_weight_total(
    config: ResearchDomainSpecialistScoreNormalizationConfig,
) -> Decimal:
    return _quantize(
        config.aggregate_calibration_weight
        + config.evidence_quality_weight
        + config.freshness_weight
        + config.capacity_weight,
    )


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


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _require_decimal(field_name: str, value: object) -> Decimal:
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


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(field_name, value)


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


def _require_domain(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _DOMAIN_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported domain")
    return value


def _domain_rank(value: str) -> int:
    return _DOMAIN_SEQUENCE.index(value)


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_SEQUENCE:
        raise ValueError(f"{field_name} must be one of pass/watch/block")
    return value


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


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchDomainSpecialistScoreNormalizationReport,
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


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_SPECIALIST_SCORE_NORMALIZATION_CONFIG_VERSION",
    "ResearchDomainSpecialistScoreDomainSummary",
    "ResearchDomainSpecialistScoreInput",
    "ResearchDomainSpecialistScoreNormalizationConfig",
    "ResearchDomainSpecialistScoreNormalizationReport",
    "ResearchDomainSpecialistScoreNormalizationRow",
    "build_research_domain_specialist_score_normalization_report",
)
