"""Paper-only candidate resolution evidence weight report v2."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any


__all__ = (
    "StrategyCandidateResolutionEvidenceWeightV2Config",
    "StrategyCandidateResolutionEvidenceWeightV2Evidence",
    "StrategyCandidateResolutionEvidenceWeightV2Report",
    "StrategyCandidateResolutionEvidenceWeightV2Row",
    "build_strategy_candidate_resolution_evidence_weight_v2_report",
    "strategy_candidate_resolution_evidence_weight_v2_payload",
    "validate_strategy_candidate_resolution_evidence_weight_v2_public_payload",
)


ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
EVIDENCE_STATUSES = ("strong", "watch", "weak")
REPORT_STATUSES = ("strong", "watch", "weak", "empty")
STATUS_PRIORITY = {"weak": 0, "watch": 1, "strong": 2}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_FRAGMENTS = (
    "li" + "ve",
    "au" + "th",
    "wal" + "let",
    "or" + "der",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
    "sig" + "ning",
    "muta" + "tion",
    "b" + "uy",
    "se" + "ll",
    "tr" + "ade",
)

ROW_PUBLIC_FIELDS_WITHOUT_DIGEST = (
    "candidate_id",
    "market_slug",
    "question",
    "resolution_outcome",
    "first_observed_at",
    "latest_observed_at",
    "evidence_count",
    "unique_source_count",
    "official_evidence_count",
    "weak_evidence_count",
    "average_base_evidence_score",
    "official_evidence_boost",
    "corroboration_boost",
    "weak_evidence_penalty",
    "resolution_evidence_weight",
    "evidence_status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PUBLIC_FIELDS = (
    *ROW_PUBLIC_FIELDS_WITHOUT_DIGEST[:-3],
    DERIVED_VALIDATION_DIGEST_FIELD,
    *PHASE_FLAG_FIELDS,
)
REPORT_PUBLIC_FIELDS_WITHOUT_DIGEST = (
    "generated_at",
    "config_version",
    "candidate_count",
    "row_count",
    "strong_count",
    "watch_count",
    "weak_count",
    "first_observed_at",
    "latest_observed_at",
    "max_resolution_evidence_weight",
    "min_resolution_evidence_weight",
    "report_status",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PUBLIC_FIELDS = (
    *REPORT_PUBLIC_FIELDS_WITHOUT_DIGEST[:-3],
    DERIVED_VALIDATION_DIGEST_FIELD,
    *PHASE_FLAG_FIELDS,
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class StrategyCandidateResolutionEvidenceWeightV2Config(_FinalPublicDataclass):
    config_version: str
    official_source_bonus: Decimal
    weak_evidence_penalty: Decimal
    corroboration_bonus_per_extra_source: Decimal
    min_strong_resolution_evidence_weight: Decimal
    min_watch_resolution_evidence_weight: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            StrategyCandidateResolutionEvidenceWeightV2Config,
        )
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "official_source_bonus",
            "weak_evidence_penalty",
            "corroboration_bonus_per_extra_source",
            "min_strong_resolution_evidence_weight",
            "min_watch_resolution_evidence_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if (
            self.min_strong_resolution_evidence_weight
            < self.min_watch_resolution_evidence_weight
        ):
            raise ValueError("strong threshold must be at least watch threshold")
        _reject_unsafe_public_payload("config", self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyCandidateResolutionEvidenceWeightV2Evidence(_FinalPublicDataclass):
    candidate_id: str
    market_slug: str
    question: str
    resolution_outcome: str
    observed_at: datetime
    evidence_source: str
    evidence_kind: str
    source_quality_score: Decimal
    specificity_score: Decimal
    recency_score: Decimal
    independence_score: Decimal
    official_source: bool
    weak_evidence: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "evidence",
            self,
            StrategyCandidateResolutionEvidenceWeightV2Evidence,
        )
        for field_name in (
            "candidate_id",
            "market_slug",
            "question",
            "resolution_outcome",
            "evidence_source",
            "evidence_kind",
        ):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "source_quality_score",
            "specificity_score",
            "recency_score",
            "independence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_bool("official_source", self.official_source)
        _require_bool("weak_evidence", self.weak_evidence)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _reject_unsafe_public_payload("evidence", self)
        _require_hard_flags("evidence", self)


@dataclass(frozen=True)
class StrategyCandidateResolutionEvidenceWeightV2Row(_FinalPublicDataclass):
    candidate_id: str
    market_slug: str
    question: str
    resolution_outcome: str
    first_observed_at: datetime
    latest_observed_at: datetime
    evidence_count: Decimal
    unique_source_count: Decimal
    official_evidence_count: Decimal
    weak_evidence_count: Decimal
    average_base_evidence_score: Decimal
    official_evidence_boost: Decimal
    corroboration_boost: Decimal
    weak_evidence_penalty: Decimal
    resolution_evidence_weight: Decimal
    evidence_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, StrategyCandidateResolutionEvidenceWeightV2Row)
        for field_name in (
            "candidate_id",
            "market_slug",
            "question",
            "resolution_outcome",
        ):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "first_observed_at",
            _as_utc("first_observed_at", self.first_observed_at),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in (
            "evidence_count",
            "unique_source_count",
            "official_evidence_count",
            "weak_evidence_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        for field_name in (
            "average_base_evidence_score",
            "official_evidence_boost",
            "corroboration_boost",
            "weak_evidence_penalty",
            "resolution_evidence_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("evidence_status", self.evidence_status, EVIDENCE_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if not self.reason_codes:
            raise ValueError("reason_codes must not be empty")
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)
        _reject_unsafe_public_payload("row", self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class StrategyCandidateResolutionEvidenceWeightV2Report(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    row_count: Decimal
    strong_count: Decimal
    watch_count: Decimal
    weak_count: Decimal
    first_observed_at: datetime | None
    latest_observed_at: datetime | None
    max_resolution_evidence_weight: Decimal
    min_resolution_evidence_weight: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyCandidateResolutionEvidenceWeightV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "report",
            self,
            StrategyCandidateResolutionEvidenceWeightV2Report,
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "row_count",
            "strong_count",
            "watch_count",
            "weak_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "first_observed_at",
            _as_optional_utc("first_observed_at", self.first_observed_at),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_optional_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in (
            "max_resolution_evidence_weight",
            "min_resolution_evidence_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if not self.reason_codes:
            raise ValueError("reason_codes must not be empty")
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)


def build_strategy_candidate_resolution_evidence_weight_v2_report(
    evidence_items: Iterable[StrategyCandidateResolutionEvidenceWeightV2Evidence],
    *,
    config: StrategyCandidateResolutionEvidenceWeightV2Config,
    generated_at: datetime,
) -> StrategyCandidateResolutionEvidenceWeightV2Report:
    """Build a pure in-memory report weighting resolution evidence by candidate."""

    _require_exact_type("config", config, StrategyCandidateResolutionEvidenceWeightV2Config)
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_evidence_items(evidence_items)
    grouped_items = _group_evidence_by_candidate(normalized_items)
    rows = tuple(
        sorted(
            (
                _row_from_group(
                    group,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for group in grouped_items
            ),
            key=_row_sort_key,
        ),
    )
    observed_times = tuple(
        observed_at
        for row in rows
        for observed_at in (row.first_observed_at, row.latest_observed_at)
    )
    report_status = _report_status(rows)
    return StrategyCandidateResolutionEvidenceWeightV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count_decimal(len(grouped_items)),
        row_count=_count_decimal(len(rows)),
        strong_count=_status_count(rows, "strong"),
        watch_count=_status_count(rows, "watch"),
        weak_count=_status_count(rows, "weak"),
        first_observed_at=min(observed_times) if observed_times else None,
        latest_observed_at=max(observed_times) if observed_times else None,
        max_resolution_evidence_weight=_max_decimal(
            tuple(row.resolution_evidence_weight for row in rows),
        ),
        min_resolution_evidence_weight=_min_decimal(
            tuple(row.resolution_evidence_weight for row in rows),
        ),
        report_status=report_status,
        reason_codes=_report_reason_codes(report_status, rows),
        rows=rows,
    )


def strategy_candidate_resolution_evidence_weight_v2_payload(
    report: StrategyCandidateResolutionEvidenceWeightV2Report | dict[str, object],
) -> dict[str, object]:
    if type(report) is StrategyCandidateResolutionEvidenceWeightV2Report:
        _require_hard_flags("report", report)
        _validate_report_consistency(report)
        _verify_digest(report)
        for row in report.rows:
            _verify_digest(row)
        payload = _json_ready(asdict(report))
        validate_strategy_candidate_resolution_evidence_weight_v2_public_payload(payload)
        return payload
    if type(report) is dict:
        validate_strategy_candidate_resolution_evidence_weight_v2_public_payload(report)
        return dict(report)
    raise ValueError(
        "report must be a StrategyCandidateResolutionEvidenceWeightV2Report",
    )


def validate_strategy_candidate_resolution_evidence_weight_v2_public_payload(
    payload: object,
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _require_public_payload_json_ready(payload)
    _require_digest(
        DERIVED_VALIDATION_DIGEST_FIELD,
        payload.get(DERIVED_VALIDATION_DIGEST_FIELD),  # type: ignore[arg-type]
    )
    _require_exact_payload_fields(payload, REPORT_PUBLIC_FIELDS, "report payload")
    _require_public_payload_flags(payload, "report payload")
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain objects")
        _require_digest(
            DERIVED_VALIDATION_DIGEST_FIELD,
            row.get(DERIVED_VALIDATION_DIGEST_FIELD),  # type: ignore[arg-type]
        )
        _require_exact_payload_fields(row, ROW_PUBLIC_FIELDS, "row payload")
        _require_public_payload_flags(row, "row payload")
        _validate_public_payload_digest(row, ROW_PUBLIC_FIELDS_WITHOUT_DIGEST)
    _validate_public_payload_digest(payload, REPORT_PUBLIC_FIELDS_WITHOUT_DIGEST)
    return True


def _row_from_group(
    group: tuple[StrategyCandidateResolutionEvidenceWeightV2Evidence, ...],
    *,
    config: StrategyCandidateResolutionEvidenceWeightV2Config,
    generated_at: datetime,
) -> StrategyCandidateResolutionEvidenceWeightV2Row:
    if not group:
        raise ValueError("evidence group must not be empty")
    ordered = tuple(sorted(group, key=lambda item: (item.observed_at, item.evidence_source)))
    first = ordered[0]
    _validate_group_metadata(ordered)
    for item in ordered:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")

    evidence_count = _count_decimal(len(ordered))
    unique_sources = frozenset(item.evidence_source for item in ordered)
    unique_source_count = _count_decimal(len(unique_sources))
    official_count = _count_decimal(sum(1 for item in ordered if item.official_source))
    weak_count = _count_decimal(sum(1 for item in ordered if item.weak_evidence))
    average_base_score = _average_decimal(
        tuple(_base_evidence_score(item) for item in ordered),
    )
    official_boost = config.official_source_bonus if official_count > ZERO else ZERO
    corroboration_boost = _multiply_decimal(
        config.corroboration_bonus_per_extra_source,
        _count_decimal(max(len(unique_sources) - 1, 0)),
    )
    weak_penalty = _multiply_decimal(config.weak_evidence_penalty, weak_count)
    resolution_weight = _clamp_probability(
        _subtract_decimal(
            _sum_decimals((average_base_score, official_boost, corroboration_boost)),
            weak_penalty,
        ),
    )
    status = _evidence_status(resolution_weight, config=config)
    reason_codes = _row_reason_codes(
        ordered,
        status=status,
        official_boost=official_boost,
        corroboration_boost=corroboration_boost,
        weak_penalty=weak_penalty,
    )
    return StrategyCandidateResolutionEvidenceWeightV2Row(
        candidate_id=first.candidate_id,
        market_slug=first.market_slug,
        question=first.question,
        resolution_outcome=first.resolution_outcome,
        first_observed_at=ordered[0].observed_at,
        latest_observed_at=max(item.observed_at for item in ordered),
        evidence_count=evidence_count,
        unique_source_count=unique_source_count,
        official_evidence_count=official_count,
        weak_evidence_count=weak_count,
        average_base_evidence_score=average_base_score,
        official_evidence_boost=official_boost,
        corroboration_boost=corroboration_boost,
        weak_evidence_penalty=weak_penalty,
        resolution_evidence_weight=resolution_weight,
        evidence_status=status,
        reason_codes=reason_codes,
    )


def _base_evidence_score(
    item: StrategyCandidateResolutionEvidenceWeightV2Evidence,
) -> Decimal:
    return _average_decimal(
        (
            item.source_quality_score,
            item.specificity_score,
            item.recency_score,
            item.independence_score,
        ),
    )


def _row_reason_codes(
    group: tuple[StrategyCandidateResolutionEvidenceWeightV2Evidence, ...],
    *,
    status: str,
    official_boost: Decimal,
    corroboration_boost: Decimal,
    weak_penalty: Decimal,
) -> tuple[str, ...]:
    codes = [f"resolution_evidence_weight_{status}"]
    if official_boost > ZERO:
        codes.append("official_evidence_boost_applied")
    if corroboration_boost > ZERO:
        codes.append("corroborated_resolution_evidence")
    if weak_penalty > ZERO:
        codes.append("weak_resolution_evidence_penalty")
    for item in group:
        codes.extend(item.reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(codes))


def _evidence_status(
    resolution_weight: Decimal,
    *,
    config: StrategyCandidateResolutionEvidenceWeightV2Config,
) -> str:
    if resolution_weight >= config.min_strong_resolution_evidence_weight:
        return "strong"
    if resolution_weight >= config.min_watch_resolution_evidence_weight:
        return "watch"
    return "weak"


def _report_status(
    rows: tuple[StrategyCandidateResolutionEvidenceWeightV2Row, ...],
) -> str:
    if not rows:
        return "empty"
    if any(row.evidence_status == "weak" for row in rows):
        return "weak"
    if any(row.evidence_status == "watch" for row in rows):
        return "watch"
    return "strong"


def _report_reason_codes(
    report_status: str,
    rows: tuple[StrategyCandidateResolutionEvidenceWeightV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("resolution_evidence_weight_no_candidates",)
    codes = [f"resolution_evidence_weight_report_{report_status}"]
    if any(row.evidence_status == "weak" for row in rows):
        codes.append("weak_resolution_evidence_candidates_present")
    if any(row.evidence_status == "watch" for row in rows):
        codes.append("watch_resolution_evidence_candidates_present")
    if all(row.evidence_status == "strong" for row in rows):
        codes.append("all_candidates_have_strong_resolution_evidence")
    return _normalize_reason_codes("reason_codes", tuple(codes))


def _normalize_evidence_items(
    evidence_items: Iterable[StrategyCandidateResolutionEvidenceWeightV2Evidence],
) -> tuple[StrategyCandidateResolutionEvidenceWeightV2Evidence, ...]:
    if isinstance(evidence_items, (str, bytes)):
        raise ValueError("evidence_items must be an iterable")
    try:
        normalized = tuple(evidence_items)
    except TypeError as exc:
        raise ValueError("evidence_items must be an iterable") from exc
    for item in normalized:
        _require_exact_type(
            "evidence",
            item,
            StrategyCandidateResolutionEvidenceWeightV2Evidence,
        )
        _require_hard_flags("evidence", item)
    return normalized


def _group_evidence_by_candidate(
    evidence_items: tuple[StrategyCandidateResolutionEvidenceWeightV2Evidence, ...],
) -> tuple[tuple[StrategyCandidateResolutionEvidenceWeightV2Evidence, ...], ...]:
    grouped: dict[str, list[StrategyCandidateResolutionEvidenceWeightV2Evidence]] = {}
    for item in evidence_items:
        grouped.setdefault(item.candidate_id, []).append(item)
    return tuple(tuple(grouped[candidate_id]) for candidate_id in sorted(grouped))


def _validate_group_metadata(
    group: tuple[StrategyCandidateResolutionEvidenceWeightV2Evidence, ...],
) -> None:
    first = group[0]
    for item in group[1:]:
        if item.market_slug != first.market_slug:
            raise ValueError("candidate evidence must share market_slug")
        if item.question != first.question:
            raise ValueError("candidate evidence must share question")
        if item.resolution_outcome != first.resolution_outcome:
            raise ValueError("candidate evidence must share resolution_outcome")


def _normalize_rows(
    rows: Iterable[StrategyCandidateResolutionEvidenceWeightV2Row],
) -> tuple[StrategyCandidateResolutionEvidenceWeightV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        _require_exact_type("row", row, StrategyCandidateResolutionEvidenceWeightV2Row)
        _require_hard_flags("row", row)
        _verify_digest(row)
    return normalized


def _validate_row_consistency(
    row: StrategyCandidateResolutionEvidenceWeightV2Row,
) -> None:
    if row.first_observed_at > row.latest_observed_at:
        raise ValueError("first_observed_at must not follow latest_observed_at")
    if row.evidence_count <= ZERO:
        raise ValueError("evidence_count must be positive")
    if row.unique_source_count <= ZERO:
        raise ValueError("unique_source_count must be positive")
    if row.official_evidence_count > row.evidence_count:
        raise ValueError("official_evidence_count must not exceed evidence_count")
    if row.weak_evidence_count > row.evidence_count:
        raise ValueError("weak_evidence_count must not exceed evidence_count")


def _validate_report_consistency(
    report: StrategyCandidateResolutionEvidenceWeightV2Report,
) -> None:
    rows = report.rows
    if report.row_count != _count_decimal(len(rows)):
        raise ValueError("row_count must match rows")
    if report.candidate_count != _count_decimal(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.strong_count != _status_count(rows, "strong"):
        raise ValueError("strong_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.weak_count != _status_count(rows, "weak"):
        raise ValueError("weak_count must match rows")
    observed_times = tuple(
        observed_at
        for row in rows
        for observed_at in (row.first_observed_at, row.latest_observed_at)
    )
    expected_first = min(observed_times) if observed_times else None
    expected_latest = max(observed_times) if observed_times else None
    if report.first_observed_at != expected_first:
        raise ValueError("first_observed_at must match rows")
    if report.latest_observed_at != expected_latest:
        raise ValueError("latest_observed_at must match rows")
    if report.max_resolution_evidence_weight != _max_decimal(
        tuple(row.resolution_evidence_weight for row in rows),
    ):
        raise ValueError("max_resolution_evidence_weight must match rows")
    if report.min_resolution_evidence_weight != _min_decimal(
        tuple(row.resolution_evidence_weight for row in rows),
    ):
        raise ValueError("min_resolution_evidence_weight must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.report_status, rows):
        raise ValueError("reason_codes must match rows")


def _row_sort_key(
    row: StrategyCandidateResolutionEvidenceWeightV2Row,
) -> tuple[int, Decimal, str, str]:
    return (
        STATUS_PRIORITY[row.evidence_status],
        -row.resolution_evidence_weight,
        row.market_slug,
        row.candidate_id,
    )


def _status_count(
    rows: tuple[StrategyCandidateResolutionEvidenceWeightV2Row, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.evidence_status == status))


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _divide_decimal(sum(values, ZERO), _count_decimal(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values)


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    return _quantize(sum(values, ZERO))


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    return _quantize(left - right)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    return _quantize(left * right)


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        raise ValueError("denominator must be nonzero")
    return _quantize(left / right)


def _clamp_probability(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _quantize(value)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal = _normalize_decimal(field_name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal = _normalize_decimal(field_name, value)
    if decimal < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal != _count_decimal(int(decimal)):
        raise ValueError(f"{field_name} must be whole")
    return decimal


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


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


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_canonical_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed_values)}")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    codes: list[str] = []
    for item in value:
        _require_canonical_public_string(field_name, item)
        if item not in codes:
            codes.append(item)
    return tuple(codes)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _apply_or_verify_digest(
    value: StrategyCandidateResolutionEvidenceWeightV2Row
    | StrategyCandidateResolutionEvidenceWeightV2Report,
) -> None:
    expected = _derived_digest(value)
    provided = value.derived_validation_digest
    if provided == "":
        object.__setattr__(value, DERIVED_VALIDATION_DIGEST_FIELD, expected)
        return
    _require_digest(DERIVED_VALIDATION_DIGEST_FIELD, provided)
    if provided != expected:
        raise ValueError("derived_validation_digest must match derived fields")


def _verify_digest(
    value: StrategyCandidateResolutionEvidenceWeightV2Row
    | StrategyCandidateResolutionEvidenceWeightV2Report,
) -> None:
    if value.derived_validation_digest != _derived_digest(value):
        raise ValueError("derived_validation_digest must match derived fields")


def _derived_digest(
    value: StrategyCandidateResolutionEvidenceWeightV2Row
    | StrategyCandidateResolutionEvidenceWeightV2Report,
) -> str:
    if type(value) is StrategyCandidateResolutionEvidenceWeightV2Row:
        fields_without_digest = ROW_PUBLIC_FIELDS_WITHOUT_DIGEST
    elif type(value) is StrategyCandidateResolutionEvidenceWeightV2Report:
        fields_without_digest = REPORT_PUBLIC_FIELDS_WITHOUT_DIGEST
    else:
        raise ValueError("value must be a supported digest dataclass")
    ready = _json_ready(asdict(value))
    if type(ready) is not dict:
        raise ValueError("digest input must be an object")
    digest_input = {field_name: ready[field_name] for field_name in fields_without_digest}
    encoded = dumps(digest_input, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _validate_public_payload_digest(
    payload: dict[str, object],
    fields_without_digest: tuple[str, ...],
) -> None:
    digest = payload.get(DERIVED_VALIDATION_DIGEST_FIELD)
    _require_digest(DERIVED_VALIDATION_DIGEST_FIELD, digest)
    digest_input = {field_name: payload[field_name] for field_name in fields_without_digest}
    encoded = dumps(digest_input, sort_keys=True, separators=(",", ":")).encode("utf-8")
    expected = sha256(encoded).hexdigest()
    if digest != expected:
        raise ValueError("derived_validation_digest must match public payload")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (int, float):
        raise ValueError("numeric values must be Decimal-derived strings")
    if type(value) is tuple or type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    current_path = path or label
    if type(value) is str:
        lowered = value.lower()
        if value.strip() != value or "://" in lowered:
            raise ValueError(f"{current_path} has unsafe value")
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"{current_path} has unsafe value")
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if type(value) is datetime:
        _as_utc(current_path, value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"{key} is an unsafe public field")
            item_path = key if not path else f"{path}.{key}"
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is tuple or type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{current_path} is not JSON serializable")


def _require_public_payload_json_ready(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _require_public_payload_json_ready(item)
        return
    if type(value) is list:
        for item in value:
            _require_public_payload_json_ready(item)
        return
    if value is None or type(value) in (str, bool):
        return
    if type(value) in (Decimal, int, float):
        raise ValueError("public payload numeric values must be strings")
    raise ValueError("public payload value is not JSON-ready")


def _require_exact_payload_fields(
    payload: dict[str, object],
    expected_fields: tuple[str, ...],
    label: str,
) -> None:
    if tuple(payload.keys()) != expected_fields:
        raise ValueError(f"{label} fields must match the public contract")


def _require_public_payload_flags(payload: dict[str, object], label: str) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
