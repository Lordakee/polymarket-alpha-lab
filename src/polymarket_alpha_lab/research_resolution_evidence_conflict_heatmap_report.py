"""Public-safe resolution evidence conflict heatmap report.

This module is pure and side-effect free. Callers provide already-sanitized
event categories, evidence categories, and team confidence scores; the returned
report aggregates conflict heat without exposing raw event, evidence, source, or
market identifiers.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from typing import Any


DEFAULT_CONFIG_VERSION = "research-resolution-evidence-conflict-heatmap-v0"
PUBLIC_STATUSES = ("pass", "watch", "block")
CONFIDENCE_BANDS = ("low_confidence", "medium_confidence", "high_confidence")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
DEFAULT_WATCH_CONFLICT_HEAT_SCORE = Decimal("0.250000")
DEFAULT_BLOCK_CONFLICT_HEAT_SCORE = Decimal("0.600000")
DEFAULT_LOW_CONFIDENCE_FLOOR = Decimal("0.500000")
DEFAULT_HIGH_CONFIDENCE_FLOOR = Decimal("0.750000")
_STATUS_SEVERITY = {"block": 0, "watch": 1, "pass": 2}
_DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
_UNSAFE_PUBLIC_FRAGMENTS = (
    "event_id",
    "source_id",
    "market_id",
    "market_slug",
    "source_reference",
    "raw_event",
    "raw_source",
    "raw_market",
    "trade",
    "trading",
    "order",
    "wallet",
    "auth",
    "private-key",
    "private_key",
    "api_key",
    "secret",
    "token",
    "credential",
)


@dataclass(frozen=True)
class ResearchResolutionEvidenceConflictHeatmapConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    watch_conflict_heat_score: Decimal = DEFAULT_WATCH_CONFLICT_HEAT_SCORE
    block_conflict_heat_score: Decimal = DEFAULT_BLOCK_CONFLICT_HEAT_SCORE
    low_confidence_floor: Decimal = DEFAULT_LOW_CONFIDENCE_FLOOR
    high_confidence_floor: Decimal = DEFAULT_HIGH_CONFIDENCE_FLOOR
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_label("config_version", self.config_version)
        for field_name in (
            "watch_conflict_heat_score",
            "block_conflict_heat_score",
            "low_confidence_floor",
            "high_confidence_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_conflict_heat_score <= self.watch_conflict_heat_score:
            raise ValueError("block_conflict_heat_score must exceed watch_conflict_heat_score")
        if self.high_confidence_floor <= self.low_confidence_floor:
            raise ValueError("high_confidence_floor must exceed low_confidence_floor")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchResolutionEvidenceConflictHeatmapObservation:
    event_category: str
    resolution_evidence_category: str
    team_confidence_score: Decimal
    evidence_conflict_score: Decimal
    evidence_item_count: Decimal
    disputed_evidence_count: Decimal
    stale_evidence_count: Decimal
    team_review_count: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_label("event_category", self.event_category)
        _require_public_label(
            "resolution_evidence_category",
            self.resolution_evidence_category,
        )
        for field_name in ("team_confidence_score", "evidence_conflict_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_item_count",
            "disputed_evidence_count",
            "stale_evidence_count",
            "team_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        if self.disputed_evidence_count > self.evidence_item_count:
            raise ValueError("disputed_evidence_count must not exceed evidence_item_count")
        if self.stale_evidence_count > self.evidence_item_count:
            raise ValueError("stale_evidence_count must not exceed evidence_item_count")
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchResolutionEvidenceConflictHeatmapCell:
    event_category: str
    resolution_evidence_category: str
    team_confidence_band: str
    observation_count: Decimal
    evidence_item_count: Decimal
    disputed_evidence_count: Decimal
    stale_evidence_count: Decimal
    team_review_count: Decimal
    average_team_confidence_score: Decimal
    average_evidence_conflict_score: Decimal
    disputed_evidence_share: Decimal
    stale_evidence_share: Decimal
    conflict_heat_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_label("event_category", self.event_category)
        _require_public_label(
            "resolution_evidence_category",
            self.resolution_evidence_category,
        )
        _require_enum("team_confidence_band", self.team_confidence_band, CONFIDENCE_BANDS)
        for field_name in (
            "observation_count",
            "evidence_item_count",
            "disputed_evidence_count",
            "stale_evidence_count",
            "team_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_team_confidence_score",
            "average_evidence_conflict_score",
            "disputed_evidence_share",
            "stale_evidence_share",
            "conflict_heat_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_cell_consistency(self)
        _require_hard_flags("cell", self)


@dataclass(frozen=True)
class ResearchResolutionEvidenceConflictHeatmapReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchResolutionEvidenceConflictHeatmapReport:
    generated_at: datetime
    config_version: str
    status: str
    cell_count: Decimal
    observation_count: Decimal
    event_category_count: Decimal
    resolution_evidence_category_count: Decimal
    confidence_band_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_evidence_item_count: Decimal
    total_disputed_evidence_count: Decimal
    total_stale_evidence_count: Decimal
    average_team_confidence_score: Decimal | None
    average_conflict_heat_score: Decimal | None
    cells: tuple[ResearchResolutionEvidenceConflictHeatmapCell, ...]
    reason_code_counts: tuple[ResearchResolutionEvidenceConflictHeatmapReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "cell_count",
            "observation_count",
            "event_category_count",
            "resolution_evidence_category_count",
            "confidence_band_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_evidence_item_count",
            "total_disputed_evidence_count",
            "total_stale_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_team_confidence_score", "average_conflict_heat_score"):
            object.__setattr__(
                self,
                field_name,
                _require_optional_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "cells", _normalize_cells(self.cells))
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
        _validate_report_consistency(self)
        expected_digest = _report_derived_validation_digest(self)
        if self.derived_validation_digest:
            digest = _require_sha256_digest(
                _DERIVED_VALIDATION_DIGEST_FIELD,
                self.derived_validation_digest,
            )
            object.__setattr__(self, _DERIVED_VALIDATION_DIGEST_FIELD, digest)
            if digest != expected_digest:
                raise ValueError("derived_validation_digest must match report payload")
        else:
            object.__setattr__(self, _DERIVED_VALIDATION_DIGEST_FIELD, expected_digest)
        _require_hard_flags("report", self)


def build_research_resolution_evidence_conflict_heatmap_report(
    observations: Iterable[object],
    *,
    config: ResearchResolutionEvidenceConflictHeatmapConfig,
    generated_at: datetime,
) -> ResearchResolutionEvidenceConflictHeatmapReport:
    if type(config) is not ResearchResolutionEvidenceConflictHeatmapConfig:
        raise ValueError("config must be a ResearchResolutionEvidenceConflictHeatmapConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    for item in normalized_observations:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")

    grouped: dict[tuple[str, str, str], list[ResearchResolutionEvidenceConflictHeatmapObservation]] = {}
    for item in normalized_observations:
        grouped.setdefault(
            (
                item.event_category,
                item.resolution_evidence_category,
                _confidence_band(item.team_confidence_score, config=config),
            ),
            [],
        ).append(item)

    cells = tuple(
        sorted(
            (
                _cell_from_observations(
                    key=key,
                    observations=tuple(values),
                    config=config,
                )
                for key, values in grouped.items()
            ),
            key=lambda cell: (
                _STATUS_SEVERITY[cell.status],
                cell.event_category,
                cell.resolution_evidence_category,
                cell.team_confidence_band,
            ),
        ),
    )
    reason_codes = _report_reason_codes(cells)

    return ResearchResolutionEvidenceConflictHeatmapReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=_report_status(cells),
        cell_count=_decimal_count(len(cells)),
        observation_count=_decimal_count(len(normalized_observations)),
        event_category_count=_decimal_count(
            len({item.event_category for item in normalized_observations}),
        ),
        resolution_evidence_category_count=_decimal_count(
            len({item.resolution_evidence_category for item in normalized_observations}),
        ),
        confidence_band_count=_decimal_count(
            len({_confidence_band(item.team_confidence_score, config=config) for item in normalized_observations}),
        ),
        pass_count=_decimal_count(_status_count(cells, "pass")),
        watch_count=_decimal_count(_status_count(cells, "watch")),
        block_count=_decimal_count(_status_count(cells, "block")),
        total_evidence_item_count=_sum_decimal(
            item.evidence_item_count for item in normalized_observations
        ),
        total_disputed_evidence_count=_sum_decimal(
            item.disputed_evidence_count for item in normalized_observations
        ),
        total_stale_evidence_count=_sum_decimal(
            item.stale_evidence_count for item in normalized_observations
        ),
        average_team_confidence_score=_average_optional(
            tuple(item.team_confidence_score for item in normalized_observations),
        ),
        average_conflict_heat_score=_average_optional(
            tuple(cell.conflict_heat_score for cell in cells),
        ),
        cells=cells,
        reason_code_counts=_reason_code_counts(cells, reason_codes),
        reason_codes=reason_codes,
    )


def research_resolution_evidence_conflict_heatmap_report_payload(
    report: ResearchResolutionEvidenceConflictHeatmapReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchResolutionEvidenceConflictHeatmapReport:
        _require_hard_flags("report", report)
        _validate_report_consistency(report)
        _validate_report_derived_validation_digest(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _reject_unsafe_public_payload("report payload", payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _require_hard_flags("payload", _DictFlags(report))
        if _DERIVED_VALIDATION_DIGEST_FIELD in report:
            _validate_public_payload_derived_validation_digest(report)
        return dict(report)
    raise ValueError("report must be a ResearchResolutionEvidenceConflictHeatmapReport")


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


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchResolutionEvidenceConflictHeatmapObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        values = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    return tuple(_coerce_observation(value) for value in values)


def _coerce_observation(
    value: object,
) -> ResearchResolutionEvidenceConflictHeatmapObservation:
    if type(value) is ResearchResolutionEvidenceConflictHeatmapObservation:
        _require_hard_flags("observation", value)
        return value
    _require_hard_flags("observation", value)
    return ResearchResolutionEvidenceConflictHeatmapObservation(
        event_category=_field_value(value, "event_category"),
        resolution_evidence_category=_field_value(value, "resolution_evidence_category"),
        team_confidence_score=_field_value(value, "team_confidence_score"),
        evidence_conflict_score=_field_value(value, "evidence_conflict_score"),
        evidence_item_count=_field_value(value, "evidence_item_count"),
        disputed_evidence_count=_field_value(value, "disputed_evidence_count"),
        stale_evidence_count=_field_value(value, "stale_evidence_count"),
        team_review_count=_field_value(value, "team_review_count"),
        observed_at=_field_value(value, "observed_at"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _cell_from_observations(
    *,
    key: tuple[str, str, str],
    observations: tuple[ResearchResolutionEvidenceConflictHeatmapObservation, ...],
    config: ResearchResolutionEvidenceConflictHeatmapConfig,
) -> ResearchResolutionEvidenceConflictHeatmapCell:
    event_category, resolution_evidence_category, confidence_band = key
    evidence_item_count = _sum_decimal(item.evidence_item_count for item in observations)
    disputed_evidence_count = _sum_decimal(
        item.disputed_evidence_count for item in observations
    )
    stale_evidence_count = _sum_decimal(item.stale_evidence_count for item in observations)
    team_confidence_score = _average(
        tuple(item.team_confidence_score for item in observations),
    )
    evidence_conflict_score = _average(
        tuple(item.evidence_conflict_score for item in observations),
    )
    disputed_evidence_share = _ratio(disputed_evidence_count, evidence_item_count)
    stale_evidence_share = _ratio(stale_evidence_count, evidence_item_count)
    conflict_heat_score = _quantize(max(evidence_conflict_score, disputed_evidence_share))
    status = _cell_status(
        conflict_heat_score=conflict_heat_score,
        average_team_confidence_score=team_confidence_score,
        stale_evidence_count=stale_evidence_count,
        config=config,
    )

    return ResearchResolutionEvidenceConflictHeatmapCell(
        event_category=event_category,
        resolution_evidence_category=resolution_evidence_category,
        team_confidence_band=confidence_band,
        observation_count=_decimal_count(len(observations)),
        evidence_item_count=evidence_item_count,
        disputed_evidence_count=disputed_evidence_count,
        stale_evidence_count=stale_evidence_count,
        team_review_count=_sum_decimal(item.team_review_count for item in observations),
        average_team_confidence_score=team_confidence_score,
        average_evidence_conflict_score=evidence_conflict_score,
        disputed_evidence_share=disputed_evidence_share,
        stale_evidence_share=stale_evidence_share,
        conflict_heat_score=conflict_heat_score,
        status=status,
        reason_codes=_cell_reason_codes(
            status=status,
            team_confidence_band=confidence_band,
            disputed_evidence_share=disputed_evidence_share,
            evidence_conflict_score=evidence_conflict_score,
            stale_evidence_count=stale_evidence_count,
            config=config,
            input_reason_codes=tuple(
                reason_code for item in observations for reason_code in item.reason_codes
            ),
        ),
    )


def _cell_status(
    *,
    conflict_heat_score: Decimal,
    average_team_confidence_score: Decimal,
    stale_evidence_count: Decimal,
    config: ResearchResolutionEvidenceConflictHeatmapConfig,
) -> str:
    if conflict_heat_score >= config.block_conflict_heat_score:
        return "block"
    if conflict_heat_score >= config.watch_conflict_heat_score:
        return "watch"
    if average_team_confidence_score < config.high_confidence_floor:
        return "watch"
    if stale_evidence_count > ZERO:
        return "watch"
    return "pass"


def _cell_reason_codes(
    *,
    status: str,
    team_confidence_band: str,
    disputed_evidence_share: Decimal,
    evidence_conflict_score: Decimal,
    stale_evidence_count: Decimal,
    config: ResearchResolutionEvidenceConflictHeatmapConfig,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes = {f"resolution_evidence_conflict_heatmap_{status}"}
    if team_confidence_band == "low_confidence":
        reason_codes.add("low_team_confidence")
    elif team_confidence_band == "medium_confidence":
        reason_codes.add("medium_team_confidence")
    else:
        reason_codes.add("high_team_confidence")
    if disputed_evidence_share >= config.block_conflict_heat_score:
        reason_codes.add("evidence_dispute_share_block")
    elif disputed_evidence_share >= config.watch_conflict_heat_score:
        reason_codes.add("evidence_dispute_share_watch")
    elif evidence_conflict_score >= config.block_conflict_heat_score:
        reason_codes.add("evidence_conflict_score_block")
    elif evidence_conflict_score >= config.watch_conflict_heat_score:
        reason_codes.add("evidence_conflict_score_watch")
    if stale_evidence_count > ZERO:
        reason_codes.add("stale_resolution_evidence_present")
    for reason_code in input_reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _confidence_band(
    team_confidence_score: Decimal,
    *,
    config: ResearchResolutionEvidenceConflictHeatmapConfig,
) -> str:
    if team_confidence_score < config.low_confidence_floor:
        return "low_confidence"
    if team_confidence_score < config.high_confidence_floor:
        return "medium_confidence"
    return "high_confidence"


def _report_reason_codes(
    cells: tuple[ResearchResolutionEvidenceConflictHeatmapCell, ...],
) -> tuple[str, ...]:
    if not cells:
        return ("no_resolution_evidence_conflict_observations",)
    if all(cell.status == "pass" for cell in cells):
        return ("resolution_evidence_conflict_heatmap_pass",)
    return tuple(sorted({reason_code for cell in cells for reason_code in cell.reason_codes}))


def _report_status(
    cells: tuple[ResearchResolutionEvidenceConflictHeatmapCell, ...],
) -> str:
    if not cells:
        return "block"
    if any(cell.status == "block" for cell in cells):
        return "block"
    if any(cell.status == "watch" for cell in cells):
        return "watch"
    return "pass"


def _reason_code_counts(
    cells: tuple[ResearchResolutionEvidenceConflictHeatmapCell, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchResolutionEvidenceConflictHeatmapReasonCodeCount, ...]:
    if not cells:
        return (
            ResearchResolutionEvidenceConflictHeatmapReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for cell in cells:
        counts.update(cell.reason_codes)
    return tuple(
        ResearchResolutionEvidenceConflictHeatmapReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _validate_cell_consistency(
    cell: ResearchResolutionEvidenceConflictHeatmapCell,
) -> None:
    if cell.observation_count <= ZERO:
        raise ValueError("observation_count must be positive")
    if cell.disputed_evidence_count > cell.evidence_item_count:
        raise ValueError("disputed_evidence_count must not exceed evidence_item_count")
    if cell.stale_evidence_count > cell.evidence_item_count:
        raise ValueError("stale_evidence_count must not exceed evidence_item_count")
    if cell.disputed_evidence_share != _ratio(
        cell.disputed_evidence_count,
        cell.evidence_item_count,
    ):
        raise ValueError("disputed_evidence_share must match counts")
    if cell.stale_evidence_share != _ratio(
        cell.stale_evidence_count,
        cell.evidence_item_count,
    ):
        raise ValueError("stale_evidence_share must match counts")
    if cell.conflict_heat_score != _quantize(
        max(cell.average_evidence_conflict_score, cell.disputed_evidence_share),
    ):
        raise ValueError("conflict_heat_score must match evidence conflict inputs")
    if f"resolution_evidence_conflict_heatmap_{cell.status}" not in cell.reason_codes:
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchResolutionEvidenceConflictHeatmapReport,
) -> None:
    if report.cell_count != _decimal_count(len(report.cells)):
        raise ValueError("cell_count must match cells")
    if report.observation_count != _sum_decimal(
        cell.observation_count for cell in report.cells
    ):
        raise ValueError("observation_count must match cells")
    if report.event_category_count != _decimal_count(
        len({cell.event_category for cell in report.cells}),
    ):
        raise ValueError("event_category_count must match cells")
    if report.resolution_evidence_category_count != _decimal_count(
        len({cell.resolution_evidence_category for cell in report.cells}),
    ):
        raise ValueError("resolution_evidence_category_count must match cells")
    if report.confidence_band_count != _decimal_count(
        len({cell.team_confidence_band for cell in report.cells}),
    ):
        raise ValueError("confidence_band_count must match cells")
    if report.pass_count != _decimal_count(_status_count(report.cells, "pass")):
        raise ValueError("pass_count must match cells")
    if report.watch_count != _decimal_count(_status_count(report.cells, "watch")):
        raise ValueError("watch_count must match cells")
    if report.block_count != _decimal_count(_status_count(report.cells, "block")):
        raise ValueError("block_count must match cells")
    if report.total_evidence_item_count != _sum_decimal(
        cell.evidence_item_count for cell in report.cells
    ):
        raise ValueError("total_evidence_item_count must match cells")
    if report.total_disputed_evidence_count != _sum_decimal(
        cell.disputed_evidence_count for cell in report.cells
    ):
        raise ValueError("total_disputed_evidence_count must match cells")
    if report.total_stale_evidence_count != _sum_decimal(
        cell.stale_evidence_count for cell in report.cells
    ):
        raise ValueError("total_stale_evidence_count must match cells")
    if report.average_team_confidence_score != _weighted_cell_average(
        report.cells,
        "average_team_confidence_score",
    ):
        raise ValueError("average_team_confidence_score must match cells")
    if report.average_conflict_heat_score != _average_optional(
        tuple(cell.conflict_heat_score for cell in report.cells),
    ):
        raise ValueError("average_conflict_heat_score must match cells")
    if report.reason_codes != _report_reason_codes(report.cells):
        raise ValueError("reason_codes must match cells")
    if report.status != _report_status(report.cells):
        raise ValueError("status must match cells")
    if report.reason_code_counts != _reason_code_counts(report.cells, report.reason_codes):
        raise ValueError("reason_code_counts must match cells")


def _validate_report_derived_validation_digest(
    report: ResearchResolutionEvidenceConflictHeatmapReport,
) -> None:
    expected_digest = _report_derived_validation_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report payload")


def _validate_public_payload_derived_validation_digest(payload: dict[str, Any]) -> None:
    supplied = payload.get(_DERIVED_VALIDATION_DIGEST_FIELD)
    if type(supplied) is not str:
        raise ValueError("derived_validation_digest must be a string")
    digest = _require_sha256_digest(_DERIVED_VALIDATION_DIGEST_FIELD, supplied)
    payload_without_digest = dict(payload)
    payload_without_digest.pop(_DERIVED_VALIDATION_DIGEST_FIELD)
    expected = sha256(
        json.dumps(
            payload_without_digest,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    if digest != expected:
        raise ValueError("derived_validation_digest must match report payload")


def _report_derived_validation_digest(
    report: ResearchResolutionEvidenceConflictHeatmapReport,
) -> str:
    payload = _report_payload_without_digest(report)
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _report_payload_without_digest(
    report: ResearchResolutionEvidenceConflictHeatmapReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop(_DERIVED_VALIDATION_DIGEST_FIELD, None)
    return payload


def _normalize_cells(
    cells: tuple[ResearchResolutionEvidenceConflictHeatmapCell, ...],
) -> tuple[ResearchResolutionEvidenceConflictHeatmapCell, ...]:
    if type(cells) is not tuple:
        raise ValueError("cells must be a tuple")
    for cell in cells:
        if type(cell) is not ResearchResolutionEvidenceConflictHeatmapCell:
            raise ValueError("cells must contain ResearchResolutionEvidenceConflictHeatmapCell values")
        _require_hard_flags("cell", cell)
    sorted_cells = tuple(
        sorted(
            cells,
            key=lambda cell: (
                _STATUS_SEVERITY[cell.status],
                cell.event_category,
                cell.resolution_evidence_category,
                cell.team_confidence_band,
            ),
        ),
    )
    if cells != sorted_cells:
        raise ValueError("cells must be sorted deterministically")
    return cells


def _normalize_reason_code_counts(
    counts: tuple[ResearchResolutionEvidenceConflictHeatmapReasonCodeCount, ...],
) -> tuple[ResearchResolutionEvidenceConflictHeatmapReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchResolutionEvidenceConflictHeatmapReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchResolutionEvidenceConflictHeatmapReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _field_value(value: object, field_name: str, *, default: object = None) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not None:
        return default
    raise ValueError(f"{field_name} is required")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is bool:
        return value
    if type(value) in (int, float):
        raise ValueError("numeric payload values must be Decimal-derived strings")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, _json_ready(value))
        return
    if type(value) in (int, float):
        raise ValueError(f"{label} contains numeric values outside Decimal strings")
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{label} contains unsafe public value")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{label} contains unsafe public field")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


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


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_whole_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_public_label(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase public text")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public text")
    for character in value:
        if not (character.islower() or character.isdigit() or character in {"_", "-"}):
            raise ValueError(f"{field_name} contains unsupported public characters")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_public_label(field_name, value)


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
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_enum(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_status(field_name: str, value: object) -> None:
    _require_enum(field_name, value, PUBLIC_STATUSES)


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be lowercase hexadecimal")
    return value


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return total


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must be nonempty")
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _average_optional(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _average(values)


def _weighted_cell_average(
    cells: tuple[ResearchResolutionEvidenceConflictHeatmapCell, ...],
    field_name: str,
) -> Decimal | None:
    observation_count = _sum_decimal(cell.observation_count for cell in cells)
    if observation_count == ZERO:
        return None
    weighted_total = sum(
        getattr(cell, field_name) * cell.observation_count for cell in cells
    )
    return _quantize(weighted_total / observation_count)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _status_count(
    cells: tuple[ResearchResolutionEvidenceConflictHeatmapCell, ...],
    status: str,
) -> int:
    return sum(1 for cell in cells if cell.status == status)


__all__ = (
    "CONFIDENCE_BANDS",
    "DEFAULT_CONFIG_VERSION",
    "PUBLIC_STATUSES",
    "ResearchResolutionEvidenceConflictHeatmapCell",
    "ResearchResolutionEvidenceConflictHeatmapConfig",
    "ResearchResolutionEvidenceConflictHeatmapObservation",
    "ResearchResolutionEvidenceConflictHeatmapReasonCodeCount",
    "ResearchResolutionEvidenceConflictHeatmapReport",
    "build_research_resolution_evidence_conflict_heatmap_report",
    "research_resolution_evidence_conflict_heatmap_report_payload",
)
