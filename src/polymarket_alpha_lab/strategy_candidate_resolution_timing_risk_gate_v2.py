"""Pure Phase 1 report-only resolution timing risk gate."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_CONFIG_VERSION = "strategy-candidate-resolution-timing-risk-gate-v2"

_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_WATCH_SCORE = Decimal("0.500000")
_BLOCK_SCORE = Decimal("1.000000")
_SECONDS_PER_HOUR = Decimal("3600.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

_GATE_STATUSES = ("pass", "watch", "blocked")
_NEXT_STEP_BY_STATUS = {
    "pass": "allow_report_only_resolution_timing_candidates",
    "watch": "refresh_report_only_resolution_timing_evidence",
    "blocked": "block_report_only_resolution_timing_candidates",
}

_EMPTY_REASON = "resolution_timing_gate_empty"
_PASS_REASON = "resolution_timing_gate_passed"
_WINDOW_BLOCK_REASON = "resolution_window_imminent"
_SOURCE_AGE_BLOCK_REASON = "resolution_source_stale"
_RULE_BLOCK_REASON = "resolution_rule_ambiguity_block"
_SOURCE_COUNT_BLOCK_REASON = "resolution_source_quorum_missing"
_DISPUTE_BLOCK_REASON = "resolution_dispute_risk_high"
_DEPENDENCY_BLOCK_REASON = "resolution_dependency_block"
_WINDOW_WATCH_REASON = "resolution_window_near"
_SOURCE_AGE_WATCH_REASON = "resolution_source_aging"
_RULE_WATCH_REASON = "resolution_rule_clarity_watch"
_SOURCE_COUNT_WATCH_REASON = "resolution_source_quorum_limited"
_DISPUTE_WATCH_REASON = "resolution_dispute_risk_elevated"
_DEPENDENCY_WATCH_REASON = "resolution_dependency_watch"

_BLOCK_REASONS = frozenset(
    (
        _WINDOW_BLOCK_REASON,
        _SOURCE_AGE_BLOCK_REASON,
        _RULE_BLOCK_REASON,
        _SOURCE_COUNT_BLOCK_REASON,
        _DISPUTE_BLOCK_REASON,
        _DEPENDENCY_BLOCK_REASON,
        _EMPTY_REASON,
    ),
)
_WATCH_REASONS = frozenset(
    (
        _WINDOW_WATCH_REASON,
        _SOURCE_AGE_WATCH_REASON,
        _RULE_WATCH_REASON,
        _SOURCE_COUNT_WATCH_REASON,
        _DISPUTE_WATCH_REASON,
        _DEPENDENCY_WATCH_REASON,
    ),
)
_REASON_PRIORITY = (
    _EMPTY_REASON,
    _WINDOW_BLOCK_REASON,
    _SOURCE_AGE_BLOCK_REASON,
    _RULE_BLOCK_REASON,
    _SOURCE_COUNT_BLOCK_REASON,
    _DISPUTE_BLOCK_REASON,
    _DEPENDENCY_BLOCK_REASON,
    _WINDOW_WATCH_REASON,
    _SOURCE_AGE_WATCH_REASON,
    _RULE_WATCH_REASON,
    _SOURCE_COUNT_WATCH_REASON,
    _DISPUTE_WATCH_REASON,
    _DEPENDENCY_WATCH_REASON,
    _PASS_REASON,
)
_REASONS = frozenset(_REASON_PRIORITY)
_ROW_DIGEST_FIELDS = (
    "generated_at",
    "redacted_candidate_reference",
    "market_slug",
    "observed_at",
    "expected_resolution_at",
    "latest_resolution_source_at",
    "hours_to_resolution",
    "resolution_source_age_hours",
    "rule_clarity_score",
    "official_source_count",
    "dispute_risk_score",
    "resolution_dependency_count",
    "timing_risk_score",
    "gate_status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_DIGEST_FIELDS = (
    "generated_at",
    "config_version",
    "candidate_count",
    "pass_count",
    "watch_count",
    "blocked_count",
    "max_timing_risk_score",
    "min_hours_to_resolution",
    "max_resolution_source_age_hours",
    "gate_status",
    "recommended_next_step",
    "reason_codes",
    "reason_code_counts",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
_UNSAFE_PUBLIC_TERMS = frozenset(
    (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    ),
)


@dataclass(frozen=True)
class StrategyCandidateResolutionTimingRiskGateConfigV2:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_pass_hours_to_resolution: Decimal = Decimal("24.000000")
    min_watch_hours_to_resolution: Decimal = Decimal("6.000000")
    max_pass_resolution_source_age_hours: Decimal = Decimal("8.000000")
    max_watch_resolution_source_age_hours: Decimal = Decimal("24.000000")
    pass_rule_clarity_score: Decimal = Decimal("0.800000")
    block_rule_clarity_score: Decimal = Decimal("0.500000")
    pass_official_source_count: Decimal = Decimal("2.000000")
    block_official_source_count: Decimal = Decimal("1.000000")
    max_pass_dispute_risk_score: Decimal = Decimal("0.300000")
    max_watch_dispute_risk_score: Decimal = Decimal("0.600000")
    max_pass_resolution_dependency_count: Decimal = Decimal("1.000000")
    max_watch_resolution_dependency_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateResolutionTimingRiskGateConfigV2:
            raise ValueError(
                "config must be a StrategyCandidateResolutionTimingRiskGateConfigV2",
            )
        _require_text("config_version", self.config_version)
        for field_name in (
            "min_pass_hours_to_resolution",
            "min_watch_hours_to_resolution",
            "max_pass_resolution_source_age_hours",
            "max_watch_resolution_source_age_hours",
            "max_pass_dispute_risk_score",
            "max_watch_dispute_risk_score",
            "max_pass_resolution_dependency_count",
            "max_watch_resolution_dependency_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("pass_rule_clarity_score", "block_rule_clarity_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_interval_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("pass_official_source_count", "block_official_source_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _validate_config(self)
        require_paper_only_flags("config", self)
        _reject_unsafe_public_surface("config", self)


@dataclass(frozen=True)
class StrategyCandidateResolutionTimingRiskCandidateV2:
    candidate_reference: str
    market_slug: str
    observed_at: datetime
    expected_resolution_at: datetime
    latest_resolution_source_at: datetime
    rule_clarity_score: Decimal
    official_source_count: Decimal
    dispute_risk_score: Decimal
    resolution_dependency_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateResolutionTimingRiskCandidateV2:
            raise ValueError(
                "candidate must be a StrategyCandidateResolutionTimingRiskCandidateV2",
            )
        _require_text("candidate_reference", self.candidate_reference)
        _require_text("market_slug", self.market_slug)
        for field_name in (
            "observed_at",
            "expected_resolution_at",
            "latest_resolution_source_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "rule_clarity_score",
            _normalize_unit_interval_decimal(
                "rule_clarity_score",
                self.rule_clarity_score,
            ),
        )
        object.__setattr__(
            self,
            "official_source_count",
            _normalize_nonnegative_whole_decimal(
                "official_source_count",
                self.official_source_count,
            ),
        )
        object.__setattr__(
            self,
            "dispute_risk_score",
            _normalize_unit_interval_decimal(
                "dispute_risk_score",
                self.dispute_risk_score,
            ),
        )
        object.__setattr__(
            self,
            "resolution_dependency_count",
            _normalize_nonnegative_whole_decimal(
                "resolution_dependency_count",
                self.resolution_dependency_count,
            ),
        )
        require_paper_only_flags("candidate", self)
        _reject_unsafe_public_surface("candidate", self)


@dataclass(frozen=True)
class StrategyCandidateResolutionTimingRiskGateRowV2:
    generated_at: datetime
    redacted_candidate_reference: str
    market_slug: str
    observed_at: datetime
    expected_resolution_at: datetime
    latest_resolution_source_at: datetime
    hours_to_resolution: Decimal
    resolution_source_age_hours: Decimal
    rule_clarity_score: Decimal
    official_source_count: Decimal
    dispute_risk_score: Decimal
    resolution_dependency_count: Decimal
    timing_risk_score: Decimal
    gate_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateResolutionTimingRiskGateRowV2:
            raise ValueError("row must be a StrategyCandidateResolutionTimingRiskGateRowV2")
        _require_text("redacted_candidate_reference", self.redacted_candidate_reference)
        _require_text("market_slug", self.market_slug)
        for field_name in (
            "generated_at",
            "observed_at",
            "expected_resolution_at",
            "latest_resolution_source_at",
        ):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        for field_name in ("hours_to_resolution", "resolution_source_age_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("rule_clarity_score", "dispute_risk_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_interval_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("official_source_count", "resolution_dependency_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "timing_risk_score",
            _normalize_unit_interval_decimal(
                "timing_risk_score",
                self.timing_risk_score,
            ),
        )
        _require_gate_status("gate_status", self.gate_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        require_paper_only_flags("row", self)
        _reject_unsafe_public_surface("row", self)
        if self.derived_validation_digest != _row_digest(self):
            raise ValueError("derived_validation_digest must match row fields")
        _validate_row(self)


@dataclass(frozen=True)
class StrategyCandidateResolutionTimingRiskReasonCodeCountV2:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateResolutionTimingRiskReasonCodeCountV2:
            raise ValueError(
                "reason row must be a "
                "StrategyCandidateResolutionTimingRiskReasonCodeCountV2",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_whole_decimal("count", self.count),
        )
        require_paper_only_flags("reason row", self)
        _reject_unsafe_public_surface("reason row", self)


@dataclass(frozen=True)
class StrategyCandidateResolutionTimingRiskGateReportV2:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_timing_risk_score: Decimal
    min_hours_to_resolution: Decimal | None
    max_resolution_source_age_hours: Decimal
    gate_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        StrategyCandidateResolutionTimingRiskReasonCodeCountV2,
        ...,
    ]
    rows: tuple[StrategyCandidateResolutionTimingRiskGateRowV2, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateResolutionTimingRiskGateReportV2:
            raise ValueError(
                "report must be a StrategyCandidateResolutionTimingRiskGateReportV2",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(
            self,
            "max_timing_risk_score",
            _normalize_unit_interval_decimal(
                "max_timing_risk_score",
                self.max_timing_risk_score,
            ),
        )
        object.__setattr__(
            self,
            "min_hours_to_resolution",
            _normalize_optional_nonnegative_decimal(
                "min_hours_to_resolution",
                self.min_hours_to_resolution,
            ),
        )
        object.__setattr__(
            self,
            "max_resolution_source_age_hours",
            _normalize_nonnegative_decimal(
                "max_resolution_source_age_hours",
                self.max_resolution_source_age_hours,
            ),
        )
        _require_gate_status("gate_status", self.gate_status)
        _require_text("recommended_next_step", self.recommended_next_step)
        if self.recommended_next_step != _NEXT_STEP_BY_STATUS[self.gate_status]:
            raise ValueError("recommended_next_step must match gate_status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        require_paper_only_flags("report", self)
        _reject_unsafe_public_surface("report", self)
        if self.derived_validation_digest != _report_digest(self):
            raise ValueError("derived_validation_digest must match report fields")
        _validate_report(self)


def build_strategy_candidate_resolution_timing_risk_gate_v2(
    candidates: Iterable[object],
    *,
    config: StrategyCandidateResolutionTimingRiskGateConfigV2,
    generated_at: datetime,
) -> StrategyCandidateResolutionTimingRiskGateReportV2:
    """Build a readonly Phase 1 paper gate over candidate resolution timing risk."""

    if type(config) is not StrategyCandidateResolutionTimingRiskGateConfigV2:
        raise ValueError(
            "config must be a StrategyCandidateResolutionTimingRiskGateConfigV2",
        )
    require_paper_only_flags("config", config)
    _reject_unsafe_public_surface("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        _build_row(candidate, config=config, generated_at=generated_at_utc)
        for candidate in _normalize_candidates(candidates)
    )
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    reason_codes = _report_reason_codes(sorted_rows)
    gate_status = _status_from_reason_codes(reason_codes)
    reason_code_counts = tuple(
        StrategyCandidateResolutionTimingRiskReasonCodeCountV2(
            reason_code=reason_code,
            count=_count(sum(reason_code in row.reason_codes for row in sorted_rows)),
        )
        for reason_code in reason_codes
    )
    report_data = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "candidate_count": _count(len(sorted_rows)),
        "pass_count": _count(sum(row.gate_status == "pass" for row in sorted_rows)),
        "watch_count": _count(sum(row.gate_status == "watch" for row in sorted_rows)),
        "blocked_count": _count(
            sum(row.gate_status == "blocked" for row in sorted_rows),
        ),
        "max_timing_risk_score": _max_decimal(
            row.timing_risk_score for row in sorted_rows
        ),
        "min_hours_to_resolution": _min_optional_decimal(
            row.hours_to_resolution for row in sorted_rows
        ),
        "max_resolution_source_age_hours": _max_decimal(
            row.resolution_source_age_hours for row in sorted_rows
        ),
        "gate_status": gate_status,
        "recommended_next_step": _NEXT_STEP_BY_STATUS[gate_status],
        "reason_codes": reason_codes,
        "reason_code_counts": reason_code_counts,
        "rows": sorted_rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return StrategyCandidateResolutionTimingRiskGateReportV2(
        **report_data,
        derived_validation_digest=_digest_from_fields(report_data, _REPORT_DIGEST_FIELDS),
    )


def strategy_candidate_resolution_timing_risk_gate_v2_payload(
    report: StrategyCandidateResolutionTimingRiskGateReportV2,
) -> dict[str, Any]:
    if type(report) is not StrategyCandidateResolutionTimingRiskGateReportV2:
        raise ValueError(
            "report must be a StrategyCandidateResolutionTimingRiskGateReportV2",
        )
    require_paper_only_flags("report", report)
    _reject_unsafe_public_surface("report", report)
    payload = {
        "generated_at": _datetime_string(report.generated_at),
        "config_version": report.config_version,
        "candidate_count": _decimal_string(report.candidate_count),
        "pass_count": _decimal_string(report.pass_count),
        "watch_count": _decimal_string(report.watch_count),
        "blocked_count": _decimal_string(report.blocked_count),
        "max_timing_risk_score": _decimal_string(report.max_timing_risk_score),
        "min_hours_to_resolution": _optional_decimal_string(
            report.min_hours_to_resolution,
        ),
        "max_resolution_source_age_hours": _decimal_string(
            report.max_resolution_source_age_hours,
        ),
        "gate_status": report.gate_status,
        "recommended_next_step": report.recommended_next_step,
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            {
                "reason_code": row.reason_code,
                "count": _decimal_string(row.count),
                "paper_only": row.paper_only,
                "report_only": row.report_only,
                "readonly": row.readonly,
            }
            for row in report.reason_code_counts
        ],
        "rows": [_row_payload(row) for row in report.rows],
        "derived_validation_digest": report.derived_validation_digest,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    validate_strategy_candidate_resolution_timing_risk_gate_v2_public_payload(payload)
    return payload


def validate_strategy_candidate_resolution_timing_risk_gate_v2_public_payload(
    payload: object,
) -> None:
    _reject_unsafe_public_surface("public payload", payload)


def _build_row(
    candidate: StrategyCandidateResolutionTimingRiskCandidateV2,
    *,
    config: StrategyCandidateResolutionTimingRiskGateConfigV2,
    generated_at: datetime,
) -> StrategyCandidateResolutionTimingRiskGateRowV2:
    _validate_candidate_timestamps(candidate, generated_at)
    hours_to_resolution = max(
        _hours_between(generated_at, candidate.expected_resolution_at),
        _ZERO,
    )
    resolution_source_age_hours = _hours_between(
        candidate.latest_resolution_source_at,
        generated_at,
    )
    reason_codes = _reason_codes_for_candidate(
        candidate,
        hours_to_resolution=hours_to_resolution,
        resolution_source_age_hours=resolution_source_age_hours,
        config=config,
    )
    gate_status = _status_from_reason_codes(reason_codes)
    row_data = {
        "generated_at": generated_at,
        "redacted_candidate_reference": _redacted_reference(candidate.candidate_reference),
        "market_slug": candidate.market_slug,
        "observed_at": candidate.observed_at,
        "expected_resolution_at": candidate.expected_resolution_at,
        "latest_resolution_source_at": candidate.latest_resolution_source_at,
        "hours_to_resolution": hours_to_resolution,
        "resolution_source_age_hours": resolution_source_age_hours,
        "rule_clarity_score": candidate.rule_clarity_score,
        "official_source_count": candidate.official_source_count,
        "dispute_risk_score": candidate.dispute_risk_score,
        "resolution_dependency_count": candidate.resolution_dependency_count,
        "timing_risk_score": _score_for_status(gate_status),
        "gate_status": gate_status,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return StrategyCandidateResolutionTimingRiskGateRowV2(
        **row_data,
        derived_validation_digest=_digest_from_fields(row_data, _ROW_DIGEST_FIELDS),
    )


def _reason_codes_for_candidate(
    candidate: StrategyCandidateResolutionTimingRiskCandidateV2,
    *,
    hours_to_resolution: Decimal,
    resolution_source_age_hours: Decimal,
    config: StrategyCandidateResolutionTimingRiskGateConfigV2,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    _append_minimum_reason(
        reason_codes,
        hours_to_resolution,
        pass_threshold=config.min_pass_hours_to_resolution,
        watch_threshold=config.min_watch_hours_to_resolution,
        watch_reason=_WINDOW_WATCH_REASON,
        block_reason=_WINDOW_BLOCK_REASON,
    )
    _append_maximum_reason(
        reason_codes,
        resolution_source_age_hours,
        pass_threshold=config.max_pass_resolution_source_age_hours,
        watch_threshold=config.max_watch_resolution_source_age_hours,
        watch_reason=_SOURCE_AGE_WATCH_REASON,
        block_reason=_SOURCE_AGE_BLOCK_REASON,
    )
    _append_minimum_reason(
        reason_codes,
        candidate.rule_clarity_score,
        pass_threshold=config.pass_rule_clarity_score,
        watch_threshold=config.block_rule_clarity_score,
        watch_reason=_RULE_WATCH_REASON,
        block_reason=_RULE_BLOCK_REASON,
    )
    _append_minimum_reason(
        reason_codes,
        candidate.official_source_count,
        pass_threshold=config.pass_official_source_count,
        watch_threshold=config.block_official_source_count,
        watch_reason=_SOURCE_COUNT_WATCH_REASON,
        block_reason=_SOURCE_COUNT_BLOCK_REASON,
    )
    _append_maximum_reason(
        reason_codes,
        candidate.dispute_risk_score,
        pass_threshold=config.max_pass_dispute_risk_score,
        watch_threshold=config.max_watch_dispute_risk_score,
        watch_reason=_DISPUTE_WATCH_REASON,
        block_reason=_DISPUTE_BLOCK_REASON,
    )
    _append_maximum_reason(
        reason_codes,
        candidate.resolution_dependency_count,
        pass_threshold=config.max_pass_resolution_dependency_count,
        watch_threshold=config.max_watch_resolution_dependency_count,
        watch_reason=_DEPENDENCY_WATCH_REASON,
        block_reason=_DEPENDENCY_BLOCK_REASON,
    )
    if not reason_codes:
        reason_codes.append(_PASS_REASON)
    return _stable_reason_codes(reason_codes)


def _append_minimum_reason(
    reason_codes: list[str],
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value < watch_threshold:
        reason_codes.append(block_reason)
    elif value < pass_threshold:
        reason_codes.append(watch_reason)


def _append_maximum_reason(
    reason_codes: list[str],
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value > watch_threshold:
        reason_codes.append(block_reason)
    elif value > pass_threshold:
        reason_codes.append(watch_reason)


def _validate_candidate_timestamps(
    candidate: StrategyCandidateResolutionTimingRiskCandidateV2,
    generated_at: datetime,
) -> None:
    if candidate.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    if candidate.latest_resolution_source_at > generated_at:
        raise ValueError("latest_resolution_source_at must not be after generated_at")


def _normalize_candidates(
    candidates: Iterable[object],
) -> tuple[StrategyCandidateResolutionTimingRiskCandidateV2, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be iterable")
    try:
        normalized = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be iterable") from exc
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not StrategyCandidateResolutionTimingRiskCandidateV2:
            raise ValueError(
                "candidates must contain "
                "StrategyCandidateResolutionTimingRiskCandidateV2 values",
            )
        require_paper_only_flags("candidate", row)
        _reject_unsafe_public_surface("candidate", row)
        if row.candidate_reference in seen:
            raise ValueError("duplicate candidate_reference")
        seen.add(row.candidate_reference)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[StrategyCandidateResolutionTimingRiskGateRowV2, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    seen_references: set[str] = set()
    for row in normalized:
        if type(row) is not StrategyCandidateResolutionTimingRiskGateRowV2:
            raise ValueError(
                "rows must contain StrategyCandidateResolutionTimingRiskGateRowV2 values",
            )
        require_paper_only_flags("row", row)
        _reject_unsafe_public_surface("row", row)
        if row.redacted_candidate_reference in seen_references:
            raise ValueError("rows must not contain duplicate candidates")
        seen_references.add(row.redacted_candidate_reference)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted")
    return normalized


def _normalize_reason_code_counts(
    values: object,
) -> tuple[StrategyCandidateResolutionTimingRiskReasonCodeCountV2, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized = tuple(values)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not StrategyCandidateResolutionTimingRiskReasonCodeCountV2:
            raise ValueError("reason_code_counts must contain reason rows")
        require_paper_only_flags("reason row", row)
        _reject_unsafe_public_surface("reason row", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(row.reason_code)
    return normalized


def _validate_config(
    config: StrategyCandidateResolutionTimingRiskGateConfigV2,
) -> None:
    if config.min_pass_hours_to_resolution < config.min_watch_hours_to_resolution:
        raise ValueError(
            "min_pass_hours_to_resolution must be at least "
            "min_watch_hours_to_resolution",
        )
    if (
        config.max_pass_resolution_source_age_hours
        > config.max_watch_resolution_source_age_hours
    ):
        raise ValueError(
            "max_pass_resolution_source_age_hours must be at most "
            "max_watch_resolution_source_age_hours",
        )
    if config.block_rule_clarity_score >= config.pass_rule_clarity_score:
        raise ValueError("block_rule_clarity_score must be below pass_rule_clarity_score")
    if config.block_official_source_count >= config.pass_official_source_count:
        raise ValueError(
            "block_official_source_count must be below pass_official_source_count",
        )
    if config.max_pass_dispute_risk_score > config.max_watch_dispute_risk_score:
        raise ValueError(
            "max_pass_dispute_risk_score must be at most "
            "max_watch_dispute_risk_score",
        )
    if (
        config.max_pass_resolution_dependency_count
        > config.max_watch_resolution_dependency_count
    ):
        raise ValueError(
            "max_pass_resolution_dependency_count must be at most "
            "max_watch_resolution_dependency_count",
        )


def _validate_row(row: StrategyCandidateResolutionTimingRiskGateRowV2) -> None:
    if row.hours_to_resolution != max(
        _hours_between(row.generated_at, row.expected_resolution_at),
        _ZERO,
    ):
        raise ValueError("hours_to_resolution must match timestamps")
    if row.resolution_source_age_hours != _hours_between(
        row.latest_resolution_source_at,
        row.generated_at,
    ):
        raise ValueError("resolution_source_age_hours must match timestamps")
    if row.gate_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("gate_status must match reason_codes")
    if row.timing_risk_score != _score_for_status(row.gate_status):
        raise ValueError("timing_risk_score must match gate_status")
    if row.gate_status == "pass" and row.reason_codes != (_PASS_REASON,):
        raise ValueError("pass rows must only include pass reason")
    if row.gate_status != "pass" and _PASS_REASON in row.reason_codes:
        raise ValueError("non-pass rows must not include pass reason")


def _validate_report(report: StrategyCandidateResolutionTimingRiskGateReportV2) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _count(sum(row.gate_status == "pass" for row in rows)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(row.gate_status == "watch" for row in rows)):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _count(sum(row.gate_status == "blocked" for row in rows)):
        raise ValueError("blocked_count must match rows")
    if report.max_timing_risk_score != _max_decimal(
        row.timing_risk_score for row in rows
    ):
        raise ValueError("max_timing_risk_score must match rows")
    if report.min_hours_to_resolution != _min_optional_decimal(
        row.hours_to_resolution for row in rows
    ):
        raise ValueError("min_hours_to_resolution must match rows")
    if report.max_resolution_source_age_hours != _max_decimal(
        row.resolution_source_age_hours for row in rows
    ):
        raise ValueError("max_resolution_source_age_hours must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.gate_status != _status_from_reason_codes(report.reason_codes):
        raise ValueError("gate_status must match reason_codes")
    if tuple(row.reason_code for row in report.reason_code_counts) != report.reason_codes:
        raise ValueError("reason_code_counts must match reason_codes")
    for reason_row in report.reason_code_counts:
        expected_count = _count(
            sum(reason_row.reason_code in row.reason_codes for row in rows),
        )
        if reason_row.count != expected_count:
            raise ValueError("reason_code_counts counts must match rows")


def _row_payload(row: StrategyCandidateResolutionTimingRiskGateRowV2) -> dict[str, Any]:
    return {
        "generated_at": _datetime_string(row.generated_at),
        "redacted_candidate_reference": row.redacted_candidate_reference,
        "market_slug": row.market_slug,
        "observed_at": _datetime_string(row.observed_at),
        "expected_resolution_at": _datetime_string(row.expected_resolution_at),
        "latest_resolution_source_at": _datetime_string(row.latest_resolution_source_at),
        "hours_to_resolution": _decimal_string(row.hours_to_resolution),
        "resolution_source_age_hours": _decimal_string(
            row.resolution_source_age_hours,
        ),
        "rule_clarity_score": _decimal_string(row.rule_clarity_score),
        "official_source_count": _decimal_string(row.official_source_count),
        "dispute_risk_score": _decimal_string(row.dispute_risk_score),
        "resolution_dependency_count": _decimal_string(
            row.resolution_dependency_count,
        ),
        "timing_risk_score": _decimal_string(row.timing_risk_score),
        "gate_status": row.gate_status,
        "reason_codes": list(row.reason_codes),
        "derived_validation_digest": row.derived_validation_digest,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_reason_codes(
    rows: tuple[StrategyCandidateResolutionTimingRiskGateRowV2, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    unique = {reason_code for row in rows for reason_code in row.reason_codes}
    if unique == {_PASS_REASON}:
        return (_PASS_REASON,)
    unique.discard(_PASS_REASON)
    return tuple(reason_code for reason_code in _REASON_PRIORITY if reason_code in unique)


def _stable_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    unique = set(reason_codes)
    return tuple(reason_code for reason_code in _REASON_PRIORITY if reason_code in unique)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASONS for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in _WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _score_for_status(gate_status: str) -> Decimal:
    if gate_status == "blocked":
        return _BLOCK_SCORE
    if gate_status == "watch":
        return _WATCH_SCORE
    return _ZERO


def _row_sort_key(row: StrategyCandidateResolutionTimingRiskGateRowV2) -> tuple[str, str]:
    status_order = {"blocked": "0", "watch": "1", "pass": "2"}
    return (status_order[row.gate_status], row.redacted_candidate_reference)


def _normalize_reason_codes(field_name: str, values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must contain at least one reason code")
    if len(set(values)) != len(values):
        raise ValueError(f"{field_name} must not contain duplicates")
    for value in values:
        _require_reason_code(field_name, value)
    stable = _stable_reason_codes(values)
    if values != stable:
        raise ValueError(f"{field_name} must follow canonical order")
    return values


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_unit_interval_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value > _ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return value


def _normalize_positive_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_nonnegative_whole_decimal(field_name, value)
    if value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_nonnegative_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return value


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _normalize_decimal(field_name, value)
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _normalize_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _require_text(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_gate_status(field_name: str, value: str) -> None:
    _require_text(field_name, value)
    if value not in _GATE_STATUSES:
        raise ValueError(f"{field_name} must be one of {_GATE_STATUSES!r}")


def _require_reason_code(field_name: str, value: str) -> None:
    _require_text(field_name, value)
    if value not in _REASONS:
        raise ValueError(f"{field_name} has unknown reason code")


def _require_digest(field_name: str, value: str) -> None:
    _require_text(field_name, value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _hours_between(start: datetime, end: datetime) -> Decimal:
    seconds = Decimal(str((end - start).total_seconds()))
    return _quantize(seconds / _SECONDS_PER_HOUR)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_QUANTUM)


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return _ZERO
    return max(normalized)


def _min_optional_decimal(values: Iterable[Decimal]) -> Decimal | None:
    normalized = tuple(values)
    if not normalized:
        return None
    return min(normalized)


def _redacted_reference(candidate_reference: str) -> str:
    digest = sha256(candidate_reference.encode("utf-8")).hexdigest()[:16]
    return f"candidate:{digest}"


def _row_digest(row: StrategyCandidateResolutionTimingRiskGateRowV2) -> str:
    return _digest_from_fields(row, _ROW_DIGEST_FIELDS)


def _report_digest(report: StrategyCandidateResolutionTimingRiskGateReportV2) -> str:
    return _digest_from_fields(report, _REPORT_DIGEST_FIELDS)


def _digest_from_fields(source: object, field_names: tuple[str, ...]) -> str:
    if isinstance(source, Mapping):
        data = {field_name: source[field_name] for field_name in field_names}
    else:
        data = {field_name: getattr(source, field_name) for field_name in field_names}
    payload = json.dumps(
        _digest_ready(data),
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def _digest_ready(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _digest_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return _datetime_string(value)
    if type(value) in (str, bool):
        return value
    if isinstance(value, Mapping):
        return {str(key): _digest_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_digest_ready(item) for item in value]
    raise ValueError("value is not digest serializable")


def _datetime_string(value: datetime) -> str:
    return _as_utc("datetime", value).isoformat()


def _decimal_string(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("value must be a Decimal")
    return str(value)


def _optional_decimal_string(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return _decimal_string(value)


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_text(f"{label}.{field.name}", field.name)
            _reject_unsafe_public_surface(
                f"{label}.{field.name}",
                getattr(value, field.name),
            )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public surface in {label}")
            _reject_unsafe_text(f"{label}.{key}", key)
            _reject_unsafe_public_surface(f"{label}.{key}", item)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_unsafe_public_surface(f"{label}[{index}]", item)
        return
    if type(value) is str:
        _reject_unsafe_text(label, value)
        return
    if type(value) in (Decimal, datetime, bool) or value is None:
        return
    raise ValueError(f"unsafe public surface in {label}")


def _reject_unsafe_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(term in normalized for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"unsafe public surface in {label}")


__all__ = (
    "StrategyCandidateResolutionTimingRiskGateConfigV2",
    "StrategyCandidateResolutionTimingRiskCandidateV2",
    "StrategyCandidateResolutionTimingRiskGateRowV2",
    "StrategyCandidateResolutionTimingRiskReasonCodeCountV2",
    "StrategyCandidateResolutionTimingRiskGateReportV2",
    "build_strategy_candidate_resolution_timing_risk_gate_v2",
    "strategy_candidate_resolution_timing_risk_gate_v2_payload",
    "validate_strategy_candidate_resolution_timing_risk_gate_v2_public_payload",
)
