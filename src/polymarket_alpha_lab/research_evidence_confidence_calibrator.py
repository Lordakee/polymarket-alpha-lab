"""Pure report-only confidence calibration for caller-supplied research evidence.

The module is deterministic and side-effect free. Callers provide typed research
evidence rows; the calibrator returns Decimal confidence bands, statuses, and
public-safe reason codes.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "ResearchEvidenceConfidenceCalibratedRow",
    "ResearchEvidenceConfidenceCalibratorConfig",
    "ResearchEvidenceConfidenceEvidence",
    "ResearchEvidenceConfidenceReasonCodeCount",
    "ResearchEvidenceConfidenceReport",
    "build_research_evidence_confidence_report",
    "research_evidence_confidence_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-evidence-confidence-calibrator-v0"
STATUSES = ("pass", "watch", "blocked")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
DEFAULT_PASS_CONFIDENCE_SCORE = Decimal("0.700000")
DEFAULT_WATCH_CONFIDENCE_SCORE = Decimal("0.400000")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_FRAGMENTS = (
    "://",
    "?",
    "api_key",
    "apikey",
    "auth",
    "bearer",
    "credential",
    "mnemonic",
    "password",
    "secret",
    "session",
    "signature",
    "token",
)


@dataclass(frozen=True)
class ResearchEvidenceConfidenceCalibratorConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_confidence_score: Decimal = DEFAULT_PASS_CONFIDENCE_SCORE
    watch_confidence_score: Decimal = DEFAULT_WATCH_CONFIDENCE_SCORE
    source_quality_weight: Decimal = Decimal("0.350000")
    freshness_weight: Decimal = Decimal("0.250000")
    consistency_weight: Decimal = Decimal("0.250000")
    counterevidence_resistance_weight: Decimal = Decimal("0.150000")
    min_pass_consistency_score: Decimal = Decimal("0.650000")
    watch_counterevidence_strength: Decimal = Decimal("0.500000")
    block_counterevidence_strength: Decimal = Decimal("0.850000")
    base_band_half_width: Decimal = Decimal("0.050000")
    consistency_uncertainty_weight: Decimal = Decimal("0.100000")
    counterevidence_uncertainty_weight: Decimal = Decimal("0.100000")
    max_band_half_width: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEvidenceConfidenceCalibratorConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEvidenceConfidenceCalibratorConfig:
            raise ValueError(
                "config must be exactly ResearchEvidenceConfidenceCalibratorConfig",
            )
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_confidence_score",
            "watch_confidence_score",
            "source_quality_weight",
            "freshness_weight",
            "consistency_weight",
            "counterevidence_resistance_weight",
            "min_pass_consistency_score",
            "watch_counterevidence_strength",
            "block_counterevidence_strength",
            "base_band_half_width",
            "consistency_uncertainty_weight",
            "counterevidence_uncertainty_weight",
            "max_band_half_width",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_confidence_score <= self.watch_confidence_score:
            raise ValueError("pass_confidence_score must be greater than watch_confidence_score")
        if self.block_counterevidence_strength < self.watch_counterevidence_strength:
            raise ValueError(
                "block_counterevidence_strength must be at least "
                "watch_counterevidence_strength",
            )
        weight_sum = _quantize(
            self.source_quality_weight
            + self.freshness_weight
            + self.consistency_weight
            + self.counterevidence_resistance_weight,
        )
        if weight_sum != ONE:
            raise ValueError(
                "source_quality_weight, freshness_weight, consistency_weight, "
                "and counterevidence_resistance_weight must sum to 1",
            )
        max_derived_band = _quantize(
            self.base_band_half_width
            + self.consistency_uncertainty_weight
            + self.counterevidence_uncertainty_weight,
        )
        if self.max_band_half_width < self.base_band_half_width:
            raise ValueError("max_band_half_width must be at least base_band_half_width")
        if self.max_band_half_width > ONE or max_derived_band > ONE:
            raise ValueError("confidence band widths must remain probabilities")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEvidenceConfidenceEvidence:
    claim_id: str
    evidence_id: str
    source_id: str
    source_family: str
    observed_at: datetime
    source_quality_score: Decimal
    freshness_score: Decimal
    consistency_score: Decimal
    counterevidence_strength: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchEvidenceConfidenceEvidence does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchEvidenceConfidenceEvidence:
            raise ValueError("evidence must be exactly ResearchEvidenceConfidenceEvidence")
        for field_name in ("claim_id", "evidence_id", "source_id", "source_family"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "source_quality_score",
            "freshness_score",
            "consistency_score",
            "counterevidence_strength",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("evidence", self)
        _reject_unsafe_public_payload("evidence", self)


@dataclass(frozen=True)
class ResearchEvidenceConfidenceCalibratedRow:
    claim_id: str
    evidence_count: Decimal
    latest_observed_at: datetime
    source_quality_score: Decimal
    freshness_score: Decimal
    consistency_score: Decimal
    counterevidence_strength: Decimal
    confidence_score: Decimal
    band_half_width: Decimal
    confidence_band_low: Decimal
    confidence_band_high: Decimal
    evidence_ids: tuple[str, ...]
    source_ids: tuple[str, ...]
    source_families: tuple[str, ...]
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEvidenceConfidenceCalibratedRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEvidenceConfidenceCalibratedRow:
            raise ValueError("row must be exactly ResearchEvidenceConfidenceCalibratedRow")
        _require_public_string("claim_id", self.claim_id)
        object.__setattr__(
            self,
            "evidence_count",
            _require_positive_whole_decimal("evidence_count", self.evidence_count),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in (
            "source_quality_score",
            "freshness_score",
            "consistency_score",
            "counterevidence_strength",
            "confidence_score",
            "band_half_width",
            "confidence_band_low",
            "confidence_band_high",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("evidence_ids", "source_ids", "source_families"):
            object.__setattr__(
                self,
                field_name,
                _normalize_string_tuple(field_name, getattr(self, field_name), allow_empty=True),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchEvidenceConfidenceReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchEvidenceConfidenceReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEvidenceConfidenceReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly ResearchEvidenceConfidenceReasonCodeCount",
            )
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchEvidenceConfidenceReport:
    generated_at: datetime
    config_version: str
    claim_count: Decimal
    evidence_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_confidence_score: Decimal | None
    status: str
    rows: tuple[ResearchEvidenceConfidenceCalibratedRow, ...]
    reason_code_counts: tuple[ResearchEvidenceConfidenceReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchEvidenceConfidenceReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchEvidenceConfidenceReport:
            raise ValueError("report must be exactly ResearchEvidenceConfidenceReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "claim_count",
            "evidence_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_confidence_score",
            _require_optional_probability_decimal(
                "average_confidence_score",
                self.average_confidence_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report_consistency(self)


def build_research_evidence_confidence_report(
    evidence_rows: Iterable[object],
    *,
    config: ResearchEvidenceConfidenceCalibratorConfig,
    generated_at: datetime,
) -> ResearchEvidenceConfidenceReport:
    if type(config) is not ResearchEvidenceConfidenceCalibratorConfig:
        raise ValueError("config must be a ResearchEvidenceConfidenceCalibratorConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    evidence_items = _normalize_evidence_rows(evidence_rows)
    for item in evidence_items:
        _reject_future_observed_at(item, generated_at_utc)

    grouped: dict[str, list[ResearchEvidenceConfidenceEvidence]] = {}
    for item in evidence_items:
        grouped.setdefault(item.claim_id, []).append(item)

    rows = tuple(
        _calibrated_row_from_claim(
            claim_id=claim_id,
            evidence_rows=tuple(grouped[claim_id]),
            config=config,
        )
        for claim_id in sorted(grouped)
    )
    reason_codes = _summary_reason_codes(rows)

    return ResearchEvidenceConfidenceReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        claim_count=_decimal_count(len(rows)),
        evidence_count=sum((row.evidence_count for row in rows), ZERO),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        blocked_count=_decimal_count(_status_count(rows, "blocked")),
        average_confidence_score=_average_confidence_score(rows),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_evidence_confidence_report_payload(
    report: ResearchEvidenceConfidenceReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEvidenceConfidenceReport:
        raise ValueError("report must be a ResearchEvidenceConfidenceReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    _reject_unsafe_public_payload(
        "report_payload",
        payload,
        allow_json_containers=True,
    )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _calibrated_row_from_claim(
    *,
    claim_id: str,
    evidence_rows: tuple[ResearchEvidenceConfidenceEvidence, ...],
    config: ResearchEvidenceConfidenceCalibratorConfig,
) -> ResearchEvidenceConfidenceCalibratedRow:
    sorted_rows = tuple(
        sorted(
            evidence_rows,
            key=lambda item: (item.evidence_id, item.source_id, item.source_family),
        ),
    )
    source_quality_score = _average_decimal(
        tuple(item.source_quality_score for item in sorted_rows),
    )
    freshness_score = _average_decimal(tuple(item.freshness_score for item in sorted_rows))
    consistency_score = _average_decimal(
        tuple(item.consistency_score for item in sorted_rows),
    )
    counterevidence_strength = max(
        (item.counterevidence_strength for item in sorted_rows),
        default=ZERO,
    )
    confidence_score = _confidence_score(
        source_quality_score=source_quality_score,
        freshness_score=freshness_score,
        consistency_score=consistency_score,
        counterevidence_strength=counterevidence_strength,
        config=config,
    )
    band_half_width = _band_half_width(
        consistency_score=consistency_score,
        counterevidence_strength=counterevidence_strength,
        config=config,
    )
    status = _row_status(
        confidence_score=confidence_score,
        consistency_score=consistency_score,
        counterevidence_strength=counterevidence_strength,
        config=config,
    )
    reason_codes = _row_reason_codes(
        status=status,
        source_quality_score=source_quality_score,
        freshness_score=freshness_score,
        consistency_score=consistency_score,
        counterevidence_strength=counterevidence_strength,
        input_reason_codes=tuple(
            reason_code for item in sorted_rows for reason_code in item.reason_codes
        ),
        config=config,
    )

    return ResearchEvidenceConfidenceCalibratedRow(
        claim_id=claim_id,
        evidence_count=_decimal_count(len(sorted_rows)),
        latest_observed_at=max(item.observed_at for item in sorted_rows),
        source_quality_score=source_quality_score,
        freshness_score=freshness_score,
        consistency_score=consistency_score,
        counterevidence_strength=counterevidence_strength,
        confidence_score=confidence_score,
        band_half_width=band_half_width,
        confidence_band_low=_bounded_probability(confidence_score - band_half_width),
        confidence_band_high=_bounded_probability(confidence_score + band_half_width),
        evidence_ids=tuple(item.evidence_id for item in sorted_rows),
        source_ids=tuple(sorted({item.source_id for item in sorted_rows})),
        source_families=tuple(sorted({item.source_family for item in sorted_rows})),
        status=status,
        reason_codes=reason_codes,
    )


def _normalize_evidence_rows(
    evidence_rows: Iterable[object],
) -> tuple[ResearchEvidenceConfidenceEvidence, ...]:
    if isinstance(evidence_rows, (str, bytes)):
        raise ValueError("evidence_rows must be an iterable")
    try:
        values = tuple(evidence_rows)
    except TypeError as exc:
        raise ValueError("evidence_rows must be an iterable") from exc
    for value in values:
        if type(value) is not ResearchEvidenceConfidenceEvidence:
            raise ValueError(
                "evidence_rows must contain ResearchEvidenceConfidenceEvidence values",
            )
        _require_hard_flags("evidence", value)
    return values


def _confidence_score(
    *,
    source_quality_score: Decimal,
    freshness_score: Decimal,
    consistency_score: Decimal,
    counterevidence_strength: Decimal,
    config: ResearchEvidenceConfidenceCalibratorConfig,
) -> Decimal:
    raw_score = (
        (source_quality_score * config.source_quality_weight)
        + (freshness_score * config.freshness_weight)
        + (consistency_score * config.consistency_weight)
        + ((ONE - counterevidence_strength) * config.counterevidence_resistance_weight)
    )
    return _bounded_probability(raw_score)


def _band_half_width(
    *,
    consistency_score: Decimal,
    counterevidence_strength: Decimal,
    config: ResearchEvidenceConfidenceCalibratorConfig,
) -> Decimal:
    raw_width = (
        config.base_band_half_width
        + ((ONE - consistency_score) * config.consistency_uncertainty_weight)
        + (counterevidence_strength * config.counterevidence_uncertainty_weight)
    )
    return _quantize(min(config.max_band_half_width, raw_width))


def _row_status(
    *,
    confidence_score: Decimal,
    consistency_score: Decimal,
    counterevidence_strength: Decimal,
    config: ResearchEvidenceConfidenceCalibratorConfig,
) -> str:
    if counterevidence_strength >= config.block_counterevidence_strength:
        return "blocked"
    if confidence_score < config.watch_confidence_score:
        return "blocked"
    if confidence_score < config.pass_confidence_score:
        return "watch"
    if counterevidence_strength >= config.watch_counterevidence_strength:
        return "watch"
    if consistency_score < config.min_pass_consistency_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    source_quality_score: Decimal,
    freshness_score: Decimal,
    consistency_score: Decimal,
    counterevidence_strength: Decimal,
    input_reason_codes: tuple[str, ...],
    config: ResearchEvidenceConfidenceCalibratorConfig,
) -> tuple[str, ...]:
    reason_codes: set[str] = {f"research_evidence_confidence_{status}"}
    reason_codes.add(
        "source_quality_support"
        if source_quality_score >= config.pass_confidence_score
        else "weak_source_quality",
    )
    reason_codes.add(
        "fresh_evidence"
        if freshness_score >= config.pass_confidence_score
        else "stale_or_low_freshness",
    )
    if consistency_score < config.min_pass_consistency_score:
        reason_codes.add("low_consistency")
    if counterevidence_strength >= config.block_counterevidence_strength:
        reason_codes.add("blocking_counterevidence")
    elif counterevidence_strength >= config.watch_counterevidence_strength:
        reason_codes.add("material_counterevidence")
    else:
        reason_codes.add("low_counterevidence")
    for reason_code in input_reason_codes:
        reason_codes.add(f"public_reason_input_{reason_code}")
    return tuple(sorted(reason_codes))


def _summary_reason_codes(
    rows: tuple[ResearchEvidenceConfidenceCalibratedRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_research_evidence",)
    if any(row.status == "blocked" for row in rows):
        return tuple(sorted({code for row in rows for code in row.reason_codes}))
    if all(row.status == "pass" for row in rows):
        return ("research_evidence_confidence_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_research_evidence",):
        return "blocked"
    if "research_evidence_confidence_blocked" in reason_codes:
        return "blocked"
    if "research_evidence_confidence_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchEvidenceConfidenceCalibratedRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchEvidenceConfidenceReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchEvidenceConfidenceReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchEvidenceConfidenceReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_confidence_score(
    rows: tuple[ResearchEvidenceConfidenceCalibratedRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _average_decimal(tuple(row.confidence_score for row in rows))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must be nonempty")
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _reject_future_observed_at(
    item: ResearchEvidenceConfidenceEvidence,
    generated_at: datetime,
) -> None:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")


def _status_count(
    rows: tuple[ResearchEvidenceConfidenceCalibratedRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchEvidenceConfidenceCalibratedRow, ...],
) -> tuple[ResearchEvidenceConfidenceCalibratedRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchEvidenceConfidenceCalibratedRow:
            raise ValueError(
                "rows must contain ResearchEvidenceConfidenceCalibratedRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.claim_id))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by claim_id")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchEvidenceConfidenceReasonCodeCount, ...],
) -> tuple[ResearchEvidenceConfidenceReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchEvidenceConfidenceReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEvidenceConfidenceReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: ResearchEvidenceConfidenceCalibratedRow) -> None:
    if row.evidence_count != _decimal_count(len(row.evidence_ids)):
        raise ValueError("evidence_ids must match evidence_count")
    if row.confidence_band_low > row.confidence_score:
        raise ValueError("confidence_band_low must not exceed confidence_score")
    if row.confidence_band_high < row.confidence_score:
        raise ValueError("confidence_band_high must not be below confidence_score")
    if row.confidence_band_low > row.confidence_band_high:
        raise ValueError("confidence_band_low must not exceed confidence_band_high")
    expected_low = _bounded_probability(row.confidence_score - row.band_half_width)
    expected_high = _bounded_probability(row.confidence_score + row.band_half_width)
    if row.confidence_band_low != expected_low:
        raise ValueError("confidence_band_low must match confidence_score and band_half_width")
    if row.confidence_band_high != expected_high:
        raise ValueError("confidence_band_high must match confidence_score and band_half_width")
    if row.status == "pass" and row.confidence_score < DEFAULT_PASS_CONFIDENCE_SCORE:
        raise ValueError("confidence_score must support pass status")
    if row.status == "watch" and (
        row.confidence_score < DEFAULT_WATCH_CONFIDENCE_SCORE
        or row.confidence_score >= DEFAULT_PASS_CONFIDENCE_SCORE
        and "material_counterevidence" not in row.reason_codes
        and "low_consistency" not in row.reason_codes
    ):
        raise ValueError("confidence_score must support watch status")
    if row.status == "blocked" and (
        row.confidence_score >= DEFAULT_WATCH_CONFIDENCE_SCORE
        and "blocking_counterevidence" not in row.reason_codes
    ):
        raise ValueError("confidence_score must support blocked status")


def _validate_report_consistency(report: ResearchEvidenceConfidenceReport) -> None:
    if report.claim_count != _decimal_count(len(report.rows)):
        raise ValueError("claim_count must match rows")
    if report.evidence_count != sum((row.evidence_count for row in report.rows), ZERO):
        raise ValueError("evidence_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.average_confidence_score != _average_confidence_score(report.rows):
        raise ValueError("average_confidence_score must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


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
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _bounded_probability(value: Decimal) -> Decimal:
    return _quantize(max(ZERO, min(ONE, value)))


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public value")


def _normalize_string_tuple(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_public_string(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(normalized)


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_public_string(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in PHASE_FLAG_FIELDS:
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{flag_name} must be True for {field_name}")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            ResearchEvidenceConfidenceCalibratorConfig,
            ResearchEvidenceConfidenceEvidence,
            ResearchEvidenceConfidenceCalibratedRow,
            ResearchEvidenceConfidenceReasonCodeCount,
            ResearchEvidenceConfidenceReport,
        ):
            raise ValueError(f"{current_path} must be a supported public dataclass")
        for field in fields(value):
            if _has_unsafe_public_fragment(field.name):
                raise ValueError(f"{field.name} has unsafe public field")
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                item_path,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{current_path} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{current_path} must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{current_path} must be timezone-aware")
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is dict:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{key} has unsafe public field")
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True")
            item_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_payload(
                label,
                item,
                item_path,
                allow_json_containers=True,
            )
        return
    if type(value) is list:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=True,
            )
        return
    if type(value) is str:
        _require_public_string(current_path, value)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float) or type(value) is int:
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    raise ValueError(f"{current_path} is not JSON-ready")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)
