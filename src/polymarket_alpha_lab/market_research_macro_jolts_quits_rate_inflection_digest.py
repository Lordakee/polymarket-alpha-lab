"""Pure Phase 1 macro JOLTS quits-rate inflection digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_MACRO_JOLTS_QUITS_RATE_INFLECTION_DIGEST_CONFIG_VERSION = (
    "market-research-macro-jolts-quits-rate-inflection-digest-v0"
)

INFLECTION_STATUSES = ("pass", "watch", "blocked")
INFLECTION_DIRECTIONS = ("deteriorating", "flat", "improving")
ROW_REASON_CODES = (
    "macro_jolts_quits_rate_blocked_inflection",
    "macro_jolts_quits_rate_watch_inflection",
    "macro_jolts_quits_rate_inline",
    "macro_jolts_quits_rate_deteriorating",
    "macro_jolts_quits_rate_improving",
    "macro_jolts_quits_rate_openings_confirmation",
    "macro_jolts_quits_rate_source_stale",
    "macro_jolts_quits_rate_source_count_low",
    "macro_jolts_quits_rate_source_disagreement",
    "macro_jolts_quits_rate_upstream_reasons",
)
REPORT_REASON_CODES = (
    "macro_jolts_quits_rate_inflection_blocked_present",
    "macro_jolts_quits_rate_inflection_watch_present",
    "macro_jolts_quits_rate_deteriorating_present",
    "macro_jolts_quits_rate_improving_present",
    "macro_jolts_quits_rate_openings_confirmation_present",
    "macro_jolts_quits_rate_source_stale_present",
    "macro_jolts_quits_rate_source_count_gap_present",
    "macro_jolts_quits_rate_source_disagreement_present",
    "macro_jolts_quits_rate_upstream_reasons_present",
    "macro_jolts_quits_rate_inflection_digest_clear",
    "macro_jolts_quits_rate_inflection_digest_empty",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
WATCH_RISK_SCORE = Decimal("0.500000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_RANK = {
    "blocked": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_MACRO_JOLTS_QUITS_RATE_INFLECTION_DIGEST_CONFIG_VERSION",
    "MacroJoltsQuitsRateInflectionDigestConfig",
    "MacroJoltsQuitsRateInflectionObservation",
    "MacroJoltsQuitsRateInflectionDigestRow",
    "MacroJoltsQuitsRateInflectionReasonCodeCount",
    "MacroJoltsQuitsRateInflectionDigestReport",
    "build_market_research_macro_jolts_quits_rate_inflection_digest",
    "market_research_macro_jolts_quits_rate_inflection_digest_payload",
)


@dataclass(frozen=True)
class MacroJoltsQuitsRateInflectionDigestConfig:
    config_version: str = DEFAULT_MACRO_JOLTS_QUITS_RATE_INFLECTION_DIGEST_CONFIG_VERSION
    watch_inflection_delta: Decimal = Decimal("0.150000")
    blocked_inflection_delta: Decimal = Decimal("0.300000")
    openings_confirmation_threshold: Decimal = Decimal("0.100000")
    stale_source_age_hours: Decimal = Decimal("48.000000")
    min_source_count: Decimal = Decimal("2.000000")
    source_disagreement_threshold: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MacroJoltsQuitsRateInflectionDigestConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, MacroJoltsQuitsRateInflectionDigestConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MACRO_JOLTS_QUITS_RATE_INFLECTION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_inflection_delta",
            "blocked_inflection_delta",
            "openings_confirmation_threshold",
            "stale_source_age_hours",
            "source_disagreement_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_count("min_source_count", self.min_source_count),
        )
        if self.watch_inflection_delta > self.blocked_inflection_delta:
            raise ValueError(
                "watch_inflection_delta must not exceed blocked_inflection_delta",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MacroJoltsQuitsRateInflectionObservation:
    source_id: str
    release_id: str
    region: str
    industry: str
    current_quits_rate: Decimal
    prior_quits_rate: Decimal
    expected_quits_rate: Decimal
    current_job_openings_rate: Decimal
    prior_job_openings_rate: Decimal
    source_age_hours: Decimal
    source_count: Decimal
    source_disagreement: Decimal
    observed_at: datetime
    upstream_reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MacroJoltsQuitsRateInflectionObservation does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, MacroJoltsQuitsRateInflectionObservation, "observation")
        for field_name in ("source_id", "release_id", "region", "industry"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "current_quits_rate",
            "prior_quits_rate",
            "expected_quits_rate",
            "current_job_openings_rate",
            "prior_job_openings_rate",
            "source_age_hours",
            "source_disagreement",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_count",
            _require_positive_count("source_count", self.source_count),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MacroJoltsQuitsRateInflectionDigestRow:
    source_id: str
    release_id: str
    region: str
    industry: str
    current_quits_rate: Decimal
    prior_quits_rate: Decimal
    expected_quits_rate: Decimal
    quits_rate_delta: Decimal
    quits_rate_surprise: Decimal
    absolute_quits_rate_inflection: Decimal
    current_job_openings_rate: Decimal
    prior_job_openings_rate: Decimal
    job_openings_rate_delta: Decimal
    source_age_hours: Decimal
    source_count: Decimal
    source_disagreement: Decimal
    observed_at: datetime
    upstream_reason_codes: tuple[str, ...]
    inflection_direction: str
    inflection_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MacroJoltsQuitsRateInflectionDigestRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, MacroJoltsQuitsRateInflectionDigestRow, "row")
        for field_name in ("source_id", "release_id", "region", "industry"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in (
            "current_quits_rate",
            "prior_quits_rate",
            "expected_quits_rate",
            "current_job_openings_rate",
            "prior_job_openings_rate",
            "source_age_hours",
            "source_disagreement",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "quits_rate_delta",
            "quits_rate_surprise",
            "job_openings_rate_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "absolute_quits_rate_inflection",
            _require_nonnegative_decimal(
                "absolute_quits_rate_inflection",
                self.absolute_quits_rate_inflection,
            ),
        )
        object.__setattr__(
            self,
            "source_count",
            _require_positive_count("source_count", self.source_count),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_upstream_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
            ),
        )
        _require_member(
            "inflection_direction",
            self.inflection_direction,
            INFLECTION_DIRECTIONS,
        )
        _require_member(
            "inflection_status",
            self.inflection_status,
            INFLECTION_STATUSES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MacroJoltsQuitsRateInflectionReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MacroJoltsQuitsRateInflectionReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MacroJoltsQuitsRateInflectionReasonCodeCount,
            "reason code count",
        )
        _require_member("reason_code", self.reason_code, REPORT_REASON_CODES)
        object.__setattr__(self, "count", _require_positive_count("count", self.count))
        object.__setattr__(self, "row_ratio", _require_ratio("row_ratio", self.row_ratio))
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class MacroJoltsQuitsRateInflectionDigestReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    blocked_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    inflection_count: Decimal
    deteriorating_count: Decimal
    improving_count: Decimal
    openings_confirmation_count: Decimal
    source_quality_gap_count: Decimal
    stale_source_count: Decimal
    max_absolute_quits_rate_inflection: Decimal
    average_absolute_quits_rate_inflection: Decimal
    inflection_risk_score: Decimal
    digest_status: str
    recommended_next_step: str
    rows: tuple[MacroJoltsQuitsRateInflectionDigestRow, ...]
    reason_code_counts: tuple[MacroJoltsQuitsRateInflectionReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MacroJoltsQuitsRateInflectionDigestReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, MacroJoltsQuitsRateInflectionDigestReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MACRO_JOLTS_QUITS_RATE_INFLECTION_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "blocked_count",
            "watch_count",
            "pass_count",
            "inflection_count",
            "deteriorating_count",
            "improving_count",
            "openings_confirmation_count",
            "source_quality_gap_count",
            "stale_source_count",
            "max_absolute_quits_rate_inflection",
            "average_absolute_quits_rate_inflection",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "inflection_risk_score",
            _require_ratio("inflection_risk_score", self.inflection_risk_score),
        )
        _require_member("digest_status", self.digest_status, INFLECTION_STATUSES)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_macro_jolts_quits_rate_inflection_digest(
    observations: Iterable[MacroJoltsQuitsRateInflectionObservation],
    *,
    config: MacroJoltsQuitsRateInflectionDigestConfig,
    generated_at: datetime,
) -> MacroJoltsQuitsRateInflectionDigestReport:
    if type(config) is not MacroJoltsQuitsRateInflectionDigestConfig:
        raise ValueError("config must be exactly MacroJoltsQuitsRateInflectionDigestConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    _require_hard_flags("config", config)
    normalized = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(observation, config=config)
                for observation in normalized
            ),
            key=_row_sort_key,
        ),
    )
    row_count = _count_decimal(len(rows))
    reason_codes = _report_reason_codes(rows)
    digest_status = _digest_status(rows)

    return MacroJoltsQuitsRateInflectionDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count_decimal(len(normalized)),
        row_count=row_count,
        blocked_count=_status_count(rows, "blocked"),
        watch_count=_status_count(rows, "watch"),
        pass_count=_status_count(rows, "pass"),
        inflection_count=_inflection_count(rows),
        deteriorating_count=_reason_count(rows, "macro_jolts_quits_rate_deteriorating"),
        improving_count=_reason_count(rows, "macro_jolts_quits_rate_improving"),
        openings_confirmation_count=_reason_count(
            rows,
            "macro_jolts_quits_rate_openings_confirmation",
        ),
        source_quality_gap_count=_source_quality_gap_count(rows),
        stale_source_count=_reason_count(rows, "macro_jolts_quits_rate_source_stale"),
        max_absolute_quits_rate_inflection=_max_row_decimal(
            rows,
            "absolute_quits_rate_inflection",
        ),
        average_absolute_quits_rate_inflection=_ratio(
            _sum_decimal(row.absolute_quits_rate_inflection for row in rows),
            row_count,
        ),
        inflection_risk_score=_inflection_risk_score(rows),
        digest_status=digest_status,
        recommended_next_step=_recommended_next_step(digest_status),
        rows=rows,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
        reason_codes=reason_codes,
    )


def market_research_macro_jolts_quits_rate_inflection_digest_payload(
    report: MacroJoltsQuitsRateInflectionDigestReport,
) -> dict[str, Any]:
    if type(report) is not MacroJoltsQuitsRateInflectionDigestReport:
        raise ValueError(
            "report must be exactly MacroJoltsQuitsRateInflectionDigestReport",
        )
    _require_hard_flags("report", report)
    _validate_report(report)
    return _payload_value(report)


def _row_from_observation(
    observation: MacroJoltsQuitsRateInflectionObservation,
    *,
    config: MacroJoltsQuitsRateInflectionDigestConfig,
) -> MacroJoltsQuitsRateInflectionDigestRow:
    quits_rate_delta = _quantize_decimal(
        observation.current_quits_rate - observation.prior_quits_rate,
    )
    quits_rate_surprise = _quantize_decimal(
        observation.current_quits_rate - observation.expected_quits_rate,
    )
    absolute_inflection = _absolute_decimal(quits_rate_delta)
    job_openings_rate_delta = _quantize_decimal(
        observation.current_job_openings_rate - observation.prior_job_openings_rate,
    )
    reason_codes = _row_reason_codes(
        observation,
        quits_rate_delta=quits_rate_delta,
        absolute_inflection=absolute_inflection,
        job_openings_rate_delta=job_openings_rate_delta,
        config=config,
    )
    status = _row_status(
        observation,
        absolute_inflection=absolute_inflection,
        config=config,
    )
    return MacroJoltsQuitsRateInflectionDigestRow(
        source_id=observation.source_id,
        release_id=observation.release_id,
        region=observation.region,
        industry=observation.industry,
        current_quits_rate=observation.current_quits_rate,
        prior_quits_rate=observation.prior_quits_rate,
        expected_quits_rate=observation.expected_quits_rate,
        quits_rate_delta=quits_rate_delta,
        quits_rate_surprise=quits_rate_surprise,
        absolute_quits_rate_inflection=absolute_inflection,
        current_job_openings_rate=observation.current_job_openings_rate,
        prior_job_openings_rate=observation.prior_job_openings_rate,
        job_openings_rate_delta=job_openings_rate_delta,
        source_age_hours=observation.source_age_hours,
        source_count=observation.source_count,
        source_disagreement=observation.source_disagreement,
        observed_at=observation.observed_at,
        upstream_reason_codes=observation.upstream_reason_codes,
        inflection_direction=_inflection_direction(
            quits_rate_delta,
            _has_inflection_reason(reason_codes),
        ),
        inflection_status=status,
        reason_codes=reason_codes,
    )


def _row_status(
    observation: MacroJoltsQuitsRateInflectionObservation,
    *,
    absolute_inflection: Decimal,
    config: MacroJoltsQuitsRateInflectionDigestConfig,
) -> str:
    if _has_blocking_source_quality_risk(observation, config=config):
        return "blocked"
    if absolute_inflection >= config.blocked_inflection_delta:
        return "blocked"
    if absolute_inflection >= config.watch_inflection_delta:
        return "watch"
    return "pass"


def _row_reason_codes(
    observation: MacroJoltsQuitsRateInflectionObservation,
    *,
    quits_rate_delta: Decimal,
    absolute_inflection: Decimal,
    job_openings_rate_delta: Decimal,
    config: MacroJoltsQuitsRateInflectionDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if absolute_inflection >= config.blocked_inflection_delta:
        reason_codes.append("macro_jolts_quits_rate_blocked_inflection")
    elif absolute_inflection >= config.watch_inflection_delta:
        reason_codes.append("macro_jolts_quits_rate_watch_inflection")
    else:
        reason_codes.append("macro_jolts_quits_rate_inline")

    if absolute_inflection >= config.watch_inflection_delta:
        if quits_rate_delta < ZERO:
            reason_codes.append("macro_jolts_quits_rate_deteriorating")
        elif quits_rate_delta > ZERO:
            reason_codes.append("macro_jolts_quits_rate_improving")
    if _openings_confirm(
        quits_rate_delta,
        job_openings_rate_delta,
        config.openings_confirmation_threshold,
    ):
        reason_codes.append("macro_jolts_quits_rate_openings_confirmation")
    if observation.source_age_hours >= config.stale_source_age_hours:
        reason_codes.append("macro_jolts_quits_rate_source_stale")
    if observation.source_count < config.min_source_count:
        reason_codes.append("macro_jolts_quits_rate_source_count_low")
    if observation.source_disagreement >= config.source_disagreement_threshold:
        reason_codes.append("macro_jolts_quits_rate_source_disagreement")
    if observation.upstream_reason_codes:
        reason_codes.append("macro_jolts_quits_rate_upstream_reasons")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), ROW_REASON_CODES)


def _report_reason_codes(
    rows: tuple[MacroJoltsQuitsRateInflectionDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("macro_jolts_quits_rate_inflection_digest_empty",)
    reason_codes: list[str] = []
    if _reason_count(rows, "macro_jolts_quits_rate_blocked_inflection") > ZERO:
        reason_codes.append("macro_jolts_quits_rate_inflection_blocked_present")
    if _reason_count(rows, "macro_jolts_quits_rate_watch_inflection") > ZERO:
        reason_codes.append("macro_jolts_quits_rate_inflection_watch_present")
    if _reason_count(rows, "macro_jolts_quits_rate_deteriorating") > ZERO:
        reason_codes.append("macro_jolts_quits_rate_deteriorating_present")
    if _reason_count(rows, "macro_jolts_quits_rate_improving") > ZERO:
        reason_codes.append("macro_jolts_quits_rate_improving_present")
    if _reason_count(rows, "macro_jolts_quits_rate_openings_confirmation") > ZERO:
        reason_codes.append("macro_jolts_quits_rate_openings_confirmation_present")
    if _reason_count(rows, "macro_jolts_quits_rate_source_stale") > ZERO:
        reason_codes.append("macro_jolts_quits_rate_source_stale_present")
    if _reason_count(rows, "macro_jolts_quits_rate_source_count_low") > ZERO:
        reason_codes.append("macro_jolts_quits_rate_source_count_gap_present")
    if _reason_count(rows, "macro_jolts_quits_rate_source_disagreement") > ZERO:
        reason_codes.append("macro_jolts_quits_rate_source_disagreement_present")
    if _reason_count(rows, "macro_jolts_quits_rate_upstream_reasons") > ZERO:
        reason_codes.append("macro_jolts_quits_rate_upstream_reasons_present")
    if not reason_codes:
        reason_codes.append("macro_jolts_quits_rate_inflection_digest_clear")
    return tuple(reason_code for reason_code in REPORT_REASON_CODES if reason_code in reason_codes)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[MacroJoltsQuitsRateInflectionDigestRow, ...],
) -> tuple[MacroJoltsQuitsRateInflectionReasonCodeCount, ...]:
    row_count = _count_decimal(len(rows))
    if reason_codes == ("macro_jolts_quits_rate_inflection_digest_empty",):
        return (
            MacroJoltsQuitsRateInflectionReasonCodeCount(
                reason_code="macro_jolts_quits_rate_inflection_digest_empty",
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    return tuple(
        MacroJoltsQuitsRateInflectionReasonCodeCount(
            reason_code=reason_code,
            count=_report_reason_row_count(reason_code, rows),
            row_ratio=_ratio(_report_reason_row_count(reason_code, rows), row_count),
        )
        for reason_code in reason_codes
    )


def _report_reason_row_count(
    reason_code: str,
    rows: tuple[MacroJoltsQuitsRateInflectionDigestRow, ...],
) -> Decimal:
    row_reason_code = {
        "macro_jolts_quits_rate_inflection_blocked_present": (
            "macro_jolts_quits_rate_blocked_inflection"
        ),
        "macro_jolts_quits_rate_inflection_watch_present": (
            "macro_jolts_quits_rate_watch_inflection"
        ),
        "macro_jolts_quits_rate_deteriorating_present": (
            "macro_jolts_quits_rate_deteriorating"
        ),
        "macro_jolts_quits_rate_improving_present": (
            "macro_jolts_quits_rate_improving"
        ),
        "macro_jolts_quits_rate_openings_confirmation_present": (
            "macro_jolts_quits_rate_openings_confirmation"
        ),
        "macro_jolts_quits_rate_source_stale_present": (
            "macro_jolts_quits_rate_source_stale"
        ),
        "macro_jolts_quits_rate_source_count_gap_present": (
            "macro_jolts_quits_rate_source_count_low"
        ),
        "macro_jolts_quits_rate_source_disagreement_present": (
            "macro_jolts_quits_rate_source_disagreement"
        ),
        "macro_jolts_quits_rate_upstream_reasons_present": (
            "macro_jolts_quits_rate_upstream_reasons"
        ),
        "macro_jolts_quits_rate_inflection_digest_clear": (
            "macro_jolts_quits_rate_inline"
        ),
    }[reason_code]
    return _reason_count(rows, row_reason_code)


def _digest_status(rows: tuple[MacroJoltsQuitsRateInflectionDigestRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.inflection_status == "blocked" for row in rows):
        return "blocked"
    if any(row.inflection_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _recommended_next_step(status: str) -> str:
    if status == "pass":
        return "allow_report_only_macro_jolts_quits_rate_inflection_screening"
    if status == "watch":
        return "monitor_report_only_macro_jolts_quits_rate_inflection_screening"
    return "block_report_only_macro_jolts_quits_rate_inflection_screening"


def _inflection_risk_score(
    rows: tuple[MacroJoltsQuitsRateInflectionDigestRow, ...],
) -> Decimal:
    digest_status = _digest_status(rows)
    if digest_status == "blocked":
        return ONE if rows else ZERO
    if digest_status == "watch":
        return WATCH_RISK_SCORE
    return ZERO


def _has_blocking_source_quality_risk(
    observation: MacroJoltsQuitsRateInflectionObservation,
    *,
    config: MacroJoltsQuitsRateInflectionDigestConfig,
) -> bool:
    return (
        observation.source_age_hours >= config.stale_source_age_hours
        or observation.source_count < config.min_source_count
        or observation.source_disagreement >= config.source_disagreement_threshold
    )


def _openings_confirm(
    quits_rate_delta: Decimal,
    job_openings_rate_delta: Decimal,
    threshold: Decimal,
) -> bool:
    if _absolute_decimal(job_openings_rate_delta) < threshold:
        return False
    return (quits_rate_delta > ZERO and job_openings_rate_delta > ZERO) or (
        quits_rate_delta < ZERO and job_openings_rate_delta < ZERO
    )


def _has_inflection_reason(reason_codes: tuple[str, ...]) -> bool:
    return (
        "macro_jolts_quits_rate_blocked_inflection" in reason_codes
        or "macro_jolts_quits_rate_watch_inflection" in reason_codes
    )


def _inflection_direction(value: Decimal, has_inflection_reason: bool) -> str:
    if not has_inflection_reason:
        return "flat"
    if value < ZERO:
        return "deteriorating"
    if value > ZERO:
        return "improving"
    return "flat"


def _inflection_count(rows: tuple[MacroJoltsQuitsRateInflectionDigestRow, ...]) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if "macro_jolts_quits_rate_blocked_inflection" in row.reason_codes
            or "macro_jolts_quits_rate_watch_inflection" in row.reason_codes
        ),
    )


def _source_quality_gap_count(
    rows: tuple[MacroJoltsQuitsRateInflectionDigestRow, ...],
) -> Decimal:
    return _count_decimal(
        sum(
            1
            for row in rows
            if "macro_jolts_quits_rate_source_stale" in row.reason_codes
            or "macro_jolts_quits_rate_source_count_low" in row.reason_codes
            or "macro_jolts_quits_rate_source_disagreement" in row.reason_codes
        ),
    )


def _validate_row(row: MacroJoltsQuitsRateInflectionDigestRow) -> None:
    if row.quits_rate_delta != _quantize_decimal(
        row.current_quits_rate - row.prior_quits_rate,
    ):
        raise ValueError("quits_rate_delta must match quits rate values")
    if row.quits_rate_surprise != _quantize_decimal(
        row.current_quits_rate - row.expected_quits_rate,
    ):
        raise ValueError("quits_rate_surprise must match current less expected")
    if row.absolute_quits_rate_inflection != _absolute_decimal(row.quits_rate_delta):
        raise ValueError("absolute_quits_rate_inflection must match quits_rate_delta")
    if row.job_openings_rate_delta != _quantize_decimal(
        row.current_job_openings_rate - row.prior_job_openings_rate,
    ):
        raise ValueError("job_openings_rate_delta must match openings rate values")
    has_blocked_inflection = (
        "macro_jolts_quits_rate_blocked_inflection" in row.reason_codes
    )
    has_watch_inflection = "macro_jolts_quits_rate_watch_inflection" in row.reason_codes
    has_inline = "macro_jolts_quits_rate_inline" in row.reason_codes
    has_inflection_reason = has_blocked_inflection or has_watch_inflection
    has_source_quality_risk = any(
        reason_code in row.reason_codes
        for reason_code in (
            "macro_jolts_quits_rate_source_stale",
            "macro_jolts_quits_rate_source_count_low",
            "macro_jolts_quits_rate_source_disagreement",
        )
    )
    if row.inflection_direction != _inflection_direction(
        row.quits_rate_delta,
        has_inflection_reason,
    ):
        raise ValueError("reason_codes must match inflection_direction")
    if sum((has_blocked_inflection, has_watch_inflection, has_inline)) != 1:
        raise ValueError("reason_codes must match inflection state")
    if has_blocked_inflection and row.inflection_status != "blocked":
        raise ValueError("reason_codes must match inflection_status")
    if has_watch_inflection and row.inflection_status == "pass":
        raise ValueError("reason_codes must match inflection_status")
    if (
        has_watch_inflection
        and row.inflection_status == "blocked"
        and not has_source_quality_risk
    ):
        raise ValueError("reason_codes must match inflection_status")
    if row.inflection_status == "blocked" and not (
        has_blocked_inflection or has_source_quality_risk
    ):
        raise ValueError("reason_codes must match inflection_status")
    if row.inflection_status == "watch" and not has_watch_inflection:
        raise ValueError("reason_codes must match inflection_status")
    if row.inflection_status == "pass" and not has_inline:
        raise ValueError("reason_codes must match inflection_status")
    if (
        bool(row.upstream_reason_codes)
        != ("macro_jolts_quits_rate_upstream_reasons" in row.reason_codes)
    ):
        raise ValueError("reason_codes must match upstream_reason_codes")
    has_deteriorating_reason = (
        "macro_jolts_quits_rate_deteriorating" in row.reason_codes
    )
    has_improving_reason = "macro_jolts_quits_rate_improving" in row.reason_codes
    if has_inflection_reason:
        if (row.quits_rate_delta < ZERO) != has_deteriorating_reason:
            raise ValueError("reason_codes must match inflection_direction")
        if (row.quits_rate_delta > ZERO) != has_improving_reason:
            raise ValueError("reason_codes must match inflection_direction")
    elif has_deteriorating_reason or has_improving_reason:
        raise ValueError("reason_codes must match inflection_direction")
    if "macro_jolts_quits_rate_openings_confirmation" in row.reason_codes and not (
        (row.quits_rate_delta > ZERO and row.job_openings_rate_delta > ZERO)
        or (row.quits_rate_delta < ZERO and row.job_openings_rate_delta < ZERO)
    ):
        raise ValueError("reason_codes must match job_openings_rate_delta")


def _validate_report(report: MacroJoltsQuitsRateInflectionDigestReport) -> None:
    for row in report.rows:
        _validate_row(row)
        _require_hard_flags("row", row)
    for reason_count in report.reason_code_counts:
        _validate_reason_code_count(reason_count)
        _require_hard_flags("reason code count", reason_count)
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.blocked_count + report.watch_count + report.pass_count != report.row_count:
        raise ValueError("status counts must match rows")
    if report.inflection_count != _inflection_count(report.rows):
        raise ValueError("inflection_count must match rows")
    if report.deteriorating_count != _reason_count(
        report.rows,
        "macro_jolts_quits_rate_deteriorating",
    ):
        raise ValueError("deteriorating_count must match rows")
    if report.improving_count != _reason_count(
        report.rows,
        "macro_jolts_quits_rate_improving",
    ):
        raise ValueError("improving_count must match rows")
    if report.openings_confirmation_count != _reason_count(
        report.rows,
        "macro_jolts_quits_rate_openings_confirmation",
    ):
        raise ValueError("openings_confirmation_count must match rows")
    if report.source_quality_gap_count != _source_quality_gap_count(report.rows):
        raise ValueError("source_quality_gap_count must match rows")
    if report.stale_source_count != _reason_count(
        report.rows,
        "macro_jolts_quits_rate_source_stale",
    ):
        raise ValueError("stale_source_count must match rows")
    if report.max_absolute_quits_rate_inflection != _max_row_decimal(
        report.rows,
        "absolute_quits_rate_inflection",
    ):
        raise ValueError("max_absolute_quits_rate_inflection must match rows")
    if report.average_absolute_quits_rate_inflection != _ratio(
        _sum_decimal(row.absolute_quits_rate_inflection for row in report.rows),
        report.row_count,
    ):
        raise ValueError("average_absolute_quits_rate_inflection must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.inflection_risk_score != _inflection_risk_score(report.rows):
        raise ValueError("inflection_risk_score must match rows")
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _validate_reason_code_count(
    value: MacroJoltsQuitsRateInflectionReasonCodeCount,
) -> None:
    _require_member("reason_code", value.reason_code, REPORT_REASON_CODES)
    _require_positive_count("count", value.count)
    _require_ratio("row_ratio", value.row_ratio)


def _normalize_observations(
    observations: Iterable[MacroJoltsQuitsRateInflectionObservation],
) -> tuple[MacroJoltsQuitsRateInflectionObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError(
            "observations must contain MacroJoltsQuitsRateInflectionObservation",
        )
    normalized = tuple(observations)
    seen_source_ids: set[str] = set()
    for observation in normalized:
        if type(observation) is not MacroJoltsQuitsRateInflectionObservation:
            raise ValueError(
                "observations must contain MacroJoltsQuitsRateInflectionObservation",
            )
        _require_hard_flags("observation", observation)
        if observation.source_id in seen_source_ids:
            raise ValueError("observations must not contain duplicate source_id values")
        seen_source_ids.add(observation.source_id)
    return normalized


def _normalize_rows(
    rows: tuple[MacroJoltsQuitsRateInflectionDigestRow, ...],
) -> tuple[MacroJoltsQuitsRateInflectionDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    seen_source_ids: set[str] = set()
    for row in normalized:
        if type(row) is not MacroJoltsQuitsRateInflectionDigestRow:
            raise ValueError("rows must contain MacroJoltsQuitsRateInflectionDigestRow")
        _require_hard_flags("row", row)
        if row.source_id in seen_source_ids:
            raise ValueError("rows must not contain duplicate source_id values")
        seen_source_ids.add(row.source_id)
    return tuple(sorted(normalized, key=_row_sort_key))


def _normalize_reason_code_counts(
    values: tuple[MacroJoltsQuitsRateInflectionReasonCodeCount, ...],
) -> tuple[MacroJoltsQuitsRateInflectionReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized = tuple(values)
    for value in normalized:
        if type(value) is not MacroJoltsQuitsRateInflectionReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain MacroJoltsQuitsRateInflectionReasonCodeCount",
            )
        _validate_reason_code_count(value)
        _require_hard_flags("reason code count", value)
    return tuple(
        sorted(normalized, key=lambda value: REPORT_REASON_CODES.index(value.reason_code)),
    )


def _normalize_upstream_reason_codes(
    field_name: str,
    values: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_canonical_string("reason_code", value)
        if value not in normalized:
            normalized.append(value)
    return tuple(sorted(normalized))


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = tuple(values)
    for value in normalized:
        _require_member("reason_code", value, allowed)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(normalized, key=lambda value: allowed.index(value)))


def _row_sort_key(
    row: MacroJoltsQuitsRateInflectionDigestRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.inflection_status],
        -row.absolute_quits_rate_inflection,
        row.release_id,
        row.source_id,
    )


def _status_count(
    rows: tuple[MacroJoltsQuitsRateInflectionDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.inflection_status == status))


def _reason_count(
    rows: tuple[MacroJoltsQuitsRateInflectionDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_row_decimal(
    rows: tuple[MacroJoltsQuitsRateInflectionDigestRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("values must be Decimals")
        total += value
    return _quantize_decimal(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _require_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.quantize(Decimal("1")):
        raise ValueError(f"{field_name} must be an integer Decimal")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _absolute_decimal(value: Decimal) -> Decimal:
    return _quantize_decimal(abs(value))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    return value
