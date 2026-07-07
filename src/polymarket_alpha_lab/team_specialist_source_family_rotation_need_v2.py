"""Readonly paper report for specialist source-family rotation need."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_taxonomy import require_team_category_pair, require_team_id


DEFAULT_TEAM_SPECIALIST_SOURCE_FAMILY_ROTATION_NEED_V2_CONFIG_VERSION = (
    "team-specialist-source-family-rotation-need-v2"
)
DECIMAL_CONTEXT = Context(prec=64)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
SECONDS_QUANTUM = Decimal("0.000001")
SCORE_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ZERO_RATIO = Decimal("0").quantize(RATIO_QUANTUM)
ZERO_SECONDS = Decimal("0").quantize(SECONDS_QUANTUM)
ZERO_SCORE = Decimal("0").quantize(SCORE_QUANTUM)
ONE_RATIO = Decimal("1").quantize(RATIO_QUANTUM)
ONE_SCORE = Decimal("1").quantize(SCORE_QUANTUM)
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
SIGNAL_REASON_CODES = (
    "source_family_concentrated",
    "recent_misses_present",
    "stale_evidence_present",
    "domain_mismatch_present",
    "source_latency_breached",
    "unresolved_contradiction_history",
)
ROW_REASON_CODES = SIGNAL_REASON_CODES + ("source_family_fit_current",)
REPORT_REASON_CODES = SIGNAL_REASON_CODES + (
    "source_family_rotation_not_needed",
    "no_source_evidence_supplied",
)
ROTATION_PRIORITIES = ("high", "medium", "low")
RECOMMENDATION_BY_PRIORITY = {
    "high": "rotate_now",
    "medium": "watch_source_family_mix",
    "low": "keep_source_family_mix",
}
UNSAFE_PUBLIC_TERMS = (
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
)


@dataclass(frozen=True)
class TeamSpecialistSourceFamilyRotationNeedV2Config:
    config_version: str = (
        DEFAULT_TEAM_SPECIALIST_SOURCE_FAMILY_ROTATION_NEED_V2_CONFIG_VERSION
    )
    max_source_family_share: Decimal = Decimal("0.500000")
    stale_evidence_after_seconds: Decimal = Decimal("604800.000000")
    max_source_latency_seconds: Decimal = Decimal("600.000000")
    medium_rotation_need_score: Decimal = Decimal("0.333333")
    high_rotation_need_score: Decimal = Decimal("0.666667")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistSourceFamilyRotationNeedV2Config:
            raise TypeError(
                "TeamSpecialistSourceFamilyRotationNeedV2Config does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistSourceFamilyRotationNeedV2Config:
            raise ValueError(
                "config must be exactly TeamSpecialistSourceFamilyRotationNeedV2Config",
            )
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "max_source_family_share",
            _normalize_positive_probability(
                "max_source_family_share",
                self.max_source_family_share,
            ),
        )
        for field_name in (
            "stale_evidence_after_seconds",
            "max_source_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "medium_rotation_need_score",
            "high_rotation_need_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        if self.medium_rotation_need_score > self.high_rotation_need_score:
            raise ValueError(
                "medium_rotation_need_score must not exceed high_rotation_need_score",
            )
        _reject_unsafe_public_payload("source family rotation config", self)
        _require_hard_flags("TeamSpecialistSourceFamilyRotationNeedV2Config", self)


@dataclass(frozen=True)
class TeamSpecialistSourceFamilyRotationNeedV2Evidence:
    evidence_id: str
    team_id: str
    category_id: str
    specialist_id: str
    source_family: str
    source_domain: str
    expected_domain: str
    observed_at: datetime
    evidence_updated_at: datetime
    recent_miss_count: Decimal
    source_latency_seconds: Decimal
    contradiction_count: Decimal
    contradiction_resolved_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistSourceFamilyRotationNeedV2Evidence:
            raise TypeError(
                "TeamSpecialistSourceFamilyRotationNeedV2Evidence does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistSourceFamilyRotationNeedV2Evidence:
            raise ValueError(
                "evidence must be exactly TeamSpecialistSourceFamilyRotationNeedV2Evidence",
            )
        _require_public_string("evidence_id", self.evidence_id)
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_public_string("category_id", self.category_id)
        _require_public_string("specialist_id", self.specialist_id)
        _require_public_string("source_family", self.source_family)
        _require_public_string("source_domain", self.source_domain)
        _require_public_string("expected_domain", self.expected_domain)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "evidence_updated_at",
            _as_utc("evidence_updated_at", self.evidence_updated_at),
        )
        for field_name in (
            "recent_miss_count",
            "contradiction_count",
            "contradiction_resolved_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_latency_seconds",
            _normalize_nonnegative_seconds(
                "source_latency_seconds",
                self.source_latency_seconds,
            ),
        )
        if self.contradiction_resolved_count > self.contradiction_count:
            raise ValueError(
                "contradiction_resolved_count must not exceed contradiction_count",
            )
        _reject_unsafe_public_payload("source family rotation evidence", self)
        _require_hard_flags("TeamSpecialistSourceFamilyRotationNeedV2Evidence", self)


@dataclass(frozen=True)
class TeamSpecialistSourceFamilyRotationNeedV2Row:
    evidence_id: str
    team_id: str
    category_id: str
    specialist_id: str
    source_family: str
    source_domain: str
    expected_domain: str
    row_priority: str
    family_source_count: Decimal
    family_source_share: Decimal
    observed_at: datetime
    evidence_updated_at: datetime
    evidence_age_seconds: Decimal
    recent_miss_count: Decimal
    source_latency_seconds: Decimal
    contradiction_count: Decimal
    contradiction_resolved_count: Decimal
    unresolved_contradiction_count: Decimal
    rotation_need_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistSourceFamilyRotationNeedV2Row:
            raise TypeError(
                "TeamSpecialistSourceFamilyRotationNeedV2Row does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistSourceFamilyRotationNeedV2Row:
            raise ValueError(
                "row must be exactly TeamSpecialistSourceFamilyRotationNeedV2Row",
            )
        _require_public_string("evidence_id", self.evidence_id)
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_public_string("category_id", self.category_id)
        _require_public_string("specialist_id", self.specialist_id)
        _require_public_string("source_family", self.source_family)
        _require_public_string("source_domain", self.source_domain)
        _require_public_string("expected_domain", self.expected_domain)
        _require_member("row_priority", self.row_priority, ROTATION_PRIORITIES)
        object.__setattr__(
            self,
            "family_source_count",
            _normalize_nonnegative_count(
                "family_source_count",
                self.family_source_count,
            ),
        )
        object.__setattr__(
            self,
            "family_source_share",
            _normalize_probability("family_source_share", self.family_source_share),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "evidence_updated_at",
            _as_utc("evidence_updated_at", self.evidence_updated_at),
        )
        for field_name in (
            "evidence_age_seconds",
            "source_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_seconds(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "recent_miss_count",
            "contradiction_count",
            "contradiction_resolved_count",
            "unresolved_contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "rotation_need_score",
            _normalize_score("rotation_need_score", self.rotation_need_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _reject_unsafe_public_payload("source family rotation row", self)
        _require_hard_flags("TeamSpecialistSourceFamilyRotationNeedV2Row", self)
        _validate_row(self)


@dataclass(frozen=True)
class TeamSpecialistSourceFamilyRotationNeedV2Report:
    generated_at: datetime
    config_version: str
    rotation_priority: str
    recommendation: str
    source_count: Decimal
    source_family_count: Decimal
    dominant_source_family: str | None
    dominant_source_family_count: Decimal
    dominant_source_family_share: Decimal
    recent_miss_count: Decimal
    stale_evidence_count: Decimal
    domain_mismatch_count: Decimal
    latency_breach_count: Decimal
    contradiction_count: Decimal
    contradiction_resolved_count: Decimal
    unresolved_contradiction_count: Decimal
    rotation_need_score: Decimal
    rows: tuple[TeamSpecialistSourceFamilyRotationNeedV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not TeamSpecialistSourceFamilyRotationNeedV2Report:
            raise TypeError(
                "TeamSpecialistSourceFamilyRotationNeedV2Report does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not TeamSpecialistSourceFamilyRotationNeedV2Report:
            raise ValueError(
                "report must be exactly TeamSpecialistSourceFamilyRotationNeedV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_member("rotation_priority", self.rotation_priority, ROTATION_PRIORITIES)
        _require_member(
            "recommendation",
            self.recommendation,
            tuple(RECOMMENDATION_BY_PRIORITY.values()),
        )
        for field_name in (
            "source_count",
            "source_family_count",
            "dominant_source_family_count",
            "recent_miss_count",
            "stale_evidence_count",
            "domain_mismatch_count",
            "latency_breach_count",
            "contradiction_count",
            "contradiction_resolved_count",
            "unresolved_contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.dominant_source_family is not None:
            _require_public_string("dominant_source_family", self.dominant_source_family)
        object.__setattr__(
            self,
            "dominant_source_family_share",
            _normalize_probability(
                "dominant_source_family_share",
                self.dominant_source_family_share,
            ),
        )
        object.__setattr__(
            self,
            "rotation_need_score",
            _normalize_score("rotation_need_score", self.rotation_need_score),
        )
        object.__setattr__(self, "rows", _normalize_report_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _reject_unsafe_public_payload("source family rotation report", self)
        _require_hard_flags("TeamSpecialistSourceFamilyRotationNeedV2Report", self)
        _validate_report(self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_digest_string(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report contents")
        object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_team_specialist_source_family_rotation_need_v2(
    evidence_rows: list[TeamSpecialistSourceFamilyRotationNeedV2Evidence]
    | tuple[TeamSpecialistSourceFamilyRotationNeedV2Evidence, ...],
    *,
    config: TeamSpecialistSourceFamilyRotationNeedV2Config,
    generated_at: datetime,
) -> TeamSpecialistSourceFamilyRotationNeedV2Report:
    if type(config) is not TeamSpecialistSourceFamilyRotationNeedV2Config:
        raise ValueError(
            "config must be a TeamSpecialistSourceFamilyRotationNeedV2Config",
        )
    _require_hard_flags("TeamSpecialistSourceFamilyRotationNeedV2Config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_evidence_rows(evidence_rows)
    family_counts = _source_family_counts(source_rows)
    dominant_family, dominant_count, dominant_share = _dominant_family(
        family_counts,
        len(source_rows),
    )
    rows = tuple(
        sorted(
            (
                _row_for_evidence(
                    row,
                    config=config,
                    generated_at=generated_at_utc,
                    family_source_count=family_counts[row.source_family],
                    source_count=len(source_rows),
                )
                for row in source_rows
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows, len(source_rows))
    rotation_need_score = _report_rotation_need_score(
        reason_codes,
        dominant_share,
        config=config,
    )
    rotation_priority = _priority_for_score(rotation_need_score, config=config)

    return TeamSpecialistSourceFamilyRotationNeedV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        rotation_priority=rotation_priority,
        recommendation=RECOMMENDATION_BY_PRIORITY[rotation_priority],
        source_count=_count(len(source_rows)),
        source_family_count=_count(len(family_counts)),
        dominant_source_family=dominant_family,
        dominant_source_family_count=_count(dominant_count),
        dominant_source_family_share=dominant_share,
        recent_miss_count=_sum_decimal(rows, "recent_miss_count"),
        stale_evidence_count=_reason_count(rows, "stale_evidence_present"),
        domain_mismatch_count=_reason_count(rows, "domain_mismatch_present"),
        latency_breach_count=_reason_count(rows, "source_latency_breached"),
        contradiction_count=_sum_decimal(rows, "contradiction_count"),
        contradiction_resolved_count=_sum_decimal(rows, "contradiction_resolved_count"),
        unresolved_contradiction_count=_sum_decimal(
            rows,
            "unresolved_contradiction_count",
        ),
        rotation_need_score=rotation_need_score,
        rows=rows,
        reason_codes=reason_codes,
    )


def team_specialist_source_family_rotation_need_v2_payload(
    report: TeamSpecialistSourceFamilyRotationNeedV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is TeamSpecialistSourceFamilyRotationNeedV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("source family rotation report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("source family rotation payload", report)
        _require_hard_flags("payload", _DictFlags(report))
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
        _validate_payload_digest(payload)
    else:
        raise ValueError(
            "report must be a TeamSpecialistSourceFamilyRotationNeedV2Report",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("source family rotation payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_payload_digest(payload)
    return payload


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


def _normalize_evidence_rows(
    value: object,
) -> tuple[TeamSpecialistSourceFamilyRotationNeedV2Evidence, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("evidence rows must be a list or tuple")
    rows = tuple(value)
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not TeamSpecialistSourceFamilyRotationNeedV2Evidence:
            raise ValueError(
                "evidence rows must contain TeamSpecialistSourceFamilyRotationNeedV2Evidence",
            )
        _require_hard_flags("TeamSpecialistSourceFamilyRotationNeedV2Evidence", row)
        if row.evidence_id in seen_ids:
            raise ValueError("duplicate evidence_id values are not allowed")
        seen_ids.add(row.evidence_id)
    return rows


def _source_family_counts(
    rows: tuple[TeamSpecialistSourceFamilyRotationNeedV2Evidence, ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.source_family] = counts.get(row.source_family, 0) + 1
    return counts


def _dominant_family(
    family_counts: dict[str, int],
    source_count: int,
) -> tuple[str | None, int, Decimal]:
    if source_count == 0 or not family_counts:
        return None, 0, ZERO_RATIO
    family, count = sorted(
        family_counts.items(),
        key=lambda item: (-item[1], item[0]),
    )[0]
    return family, count, _ratio(count, source_count)


def _row_for_evidence(
    row: TeamSpecialistSourceFamilyRotationNeedV2Evidence,
    *,
    config: TeamSpecialistSourceFamilyRotationNeedV2Config,
    generated_at: datetime,
    family_source_count: int,
    source_count: int,
) -> TeamSpecialistSourceFamilyRotationNeedV2Row:
    family_share = _ratio(family_source_count, source_count)
    evidence_age_seconds = _age_seconds(row.evidence_updated_at, generated_at)
    unresolved_contradiction_count = (
        row.contradiction_count - row.contradiction_resolved_count
    )
    reason_codes = _row_reason_codes(
        family_share=family_share,
        evidence_age_seconds=evidence_age_seconds,
        unresolved_contradiction_count=unresolved_contradiction_count,
        row=row,
        config=config,
    )
    rotation_need_score = _row_rotation_need_score(
        reason_codes,
        family_share,
        config=config,
    )

    return TeamSpecialistSourceFamilyRotationNeedV2Row(
        evidence_id=row.evidence_id,
        team_id=row.team_id,
        category_id=row.category_id,
        specialist_id=row.specialist_id,
        source_family=row.source_family,
        source_domain=row.source_domain,
        expected_domain=row.expected_domain,
        row_priority=_priority_for_score(rotation_need_score, config=config),
        family_source_count=_count(family_source_count),
        family_source_share=family_share,
        observed_at=row.observed_at,
        evidence_updated_at=row.evidence_updated_at,
        evidence_age_seconds=evidence_age_seconds,
        recent_miss_count=row.recent_miss_count,
        source_latency_seconds=row.source_latency_seconds,
        contradiction_count=row.contradiction_count,
        contradiction_resolved_count=row.contradiction_resolved_count,
        unresolved_contradiction_count=unresolved_contradiction_count,
        rotation_need_score=rotation_need_score,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    family_share: Decimal,
    evidence_age_seconds: Decimal,
    unresolved_contradiction_count: Decimal,
    row: TeamSpecialistSourceFamilyRotationNeedV2Evidence,
    config: TeamSpecialistSourceFamilyRotationNeedV2Config,
) -> tuple[str, ...]:
    codes: list[str] = []
    if family_share > config.max_source_family_share:
        codes.append("source_family_concentrated")
    if row.recent_miss_count > ZERO_COUNT:
        codes.append("recent_misses_present")
    if evidence_age_seconds > config.stale_evidence_after_seconds:
        codes.append("stale_evidence_present")
    if row.source_domain != row.expected_domain:
        codes.append("domain_mismatch_present")
    if row.source_latency_seconds > config.max_source_latency_seconds:
        codes.append("source_latency_breached")
    if unresolved_contradiction_count > ZERO_COUNT:
        codes.append("unresolved_contradiction_history")
    if not codes:
        codes.append("source_family_fit_current")
    return tuple(code for code in ROW_REASON_CODES if code in codes)


def _report_reason_codes(
    rows: tuple[TeamSpecialistSourceFamilyRotationNeedV2Row, ...],
    source_row_count: int,
) -> tuple[str, ...]:
    if source_row_count == 0:
        return ("no_source_evidence_supplied",)
    codes: list[str] = []
    for signal_code in SIGNAL_REASON_CODES:
        if any(signal_code in row.reason_codes for row in rows):
            codes.append(signal_code)
    if not codes:
        codes.append("source_family_rotation_not_needed")
    return tuple(code for code in REPORT_REASON_CODES if code in codes)


def _row_rotation_need_score(
    reason_codes: tuple[str, ...],
    family_share: Decimal,
    *,
    config: TeamSpecialistSourceFamilyRotationNeedV2Config,
) -> Decimal:
    signal_count = _signal_reason_count(reason_codes)
    if signal_count == 0:
        return ZERO_SCORE
    return max(
        _score_ratio(signal_count, len(SIGNAL_REASON_CODES)),
        _concentration_excess_score(family_share, config.max_source_family_share),
    )


def _report_rotation_need_score(
    reason_codes: tuple[str, ...],
    dominant_family_share: Decimal,
    *,
    config: TeamSpecialistSourceFamilyRotationNeedV2Config,
) -> Decimal:
    signal_count = _signal_reason_count(reason_codes)
    if signal_count == 0:
        return ZERO_SCORE
    return max(
        _score_ratio(signal_count, len(SIGNAL_REASON_CODES)),
        _concentration_excess_score(
            dominant_family_share,
            config.max_source_family_share,
        ),
    )


def _concentration_excess_score(
    family_share: Decimal,
    max_source_family_share: Decimal,
) -> Decimal:
    if family_share <= max_source_family_share:
        return ZERO_SCORE
    if max_source_family_share >= ONE_RATIO:
        return ONE_SCORE
    with localcontext(DECIMAL_CONTEXT):
        return (
            (family_share - max_source_family_share)
            / (ONE_RATIO - max_source_family_share)
        ).quantize(SCORE_QUANTUM)


def _signal_reason_count(reason_codes: tuple[str, ...]) -> int:
    return sum(1 for code in reason_codes if code in SIGNAL_REASON_CODES)


def _priority_for_score(
    score: Decimal,
    *,
    config: TeamSpecialistSourceFamilyRotationNeedV2Config,
) -> str:
    if score >= config.high_rotation_need_score:
        return "high"
    if score >= config.medium_rotation_need_score:
        return "medium"
    return "low"


def _row_sort_key(
    row: TeamSpecialistSourceFamilyRotationNeedV2Row,
) -> tuple[int, Decimal, str, str, str, str]:
    return (
        ROTATION_PRIORITIES.index(row.row_priority),
        -row.rotation_need_score,
        row.team_id,
        row.category_id,
        row.specialist_id,
        row.evidence_id,
    )


def _reason_count(
    rows: tuple[TeamSpecialistSourceFamilyRotationNeedV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _sum_decimal(
    rows: tuple[TeamSpecialistSourceFamilyRotationNeedV2Row, ...],
    field_name: str,
) -> Decimal:
    return sum((getattr(row, field_name) for row in rows), ZERO_COUNT)


def _normalize_report_rows(
    value: object,
) -> tuple[TeamSpecialistSourceFamilyRotationNeedV2Row, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_ids: set[str] = set()
    for row in rows:
        if type(row) is not TeamSpecialistSourceFamilyRotationNeedV2Row:
            raise ValueError(
                "rows must contain TeamSpecialistSourceFamilyRotationNeedV2Row values",
            )
        _require_hard_flags("TeamSpecialistSourceFamilyRotationNeedV2Row", row)
        if row.evidence_id in seen_ids:
            raise ValueError("duplicate evidence_id values are not allowed")
        seen_ids.add(row.evidence_id)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return rows


def _validate_row(row: TeamSpecialistSourceFamilyRotationNeedV2Row) -> None:
    if row.reason_codes == ():
        raise ValueError("reason_codes must not be empty")
    if "source_family_fit_current" in row.reason_codes and len(row.reason_codes) != 1:
        raise ValueError("current source family fit cannot include risk reasons")
    expected_unresolved = row.contradiction_count - row.contradiction_resolved_count
    if row.unresolved_contradiction_count != expected_unresolved:
        raise ValueError("unresolved_contradiction_count must match contradiction counts")


def _validate_report(report: TeamSpecialistSourceFamilyRotationNeedV2Report) -> None:
    if report.source_count != _count(len(report.rows)):
        raise ValueError("source_count must match rows")
    if report.source_family_count != _count(len({row.source_family for row in report.rows})):
        raise ValueError("source_family_count must match rows")
    if report.recommendation != RECOMMENDATION_BY_PRIORITY[report.rotation_priority]:
        raise ValueError("recommendation must match rotation_priority")
    expected_dominant_family, expected_dominant_count, expected_dominant_share = (
        _dominant_family(
            _row_source_family_counts(report.rows),
            len(report.rows),
        )
    )
    if report.dominant_source_family != expected_dominant_family:
        raise ValueError("dominant_source_family must match rows")
    if report.dominant_source_family_count != _count(expected_dominant_count):
        raise ValueError("dominant_source_family_count must match rows")
    if report.dominant_source_family_share != expected_dominant_share:
        raise ValueError("dominant_source_family_share must match rows")
    expected_counts = {
        "recent_miss_count": _sum_decimal(report.rows, "recent_miss_count"),
        "stale_evidence_count": _reason_count(report.rows, "stale_evidence_present"),
        "domain_mismatch_count": _reason_count(report.rows, "domain_mismatch_present"),
        "latency_breach_count": _reason_count(report.rows, "source_latency_breached"),
        "contradiction_count": _sum_decimal(report.rows, "contradiction_count"),
        "contradiction_resolved_count": _sum_decimal(
            report.rows,
            "contradiction_resolved_count",
        ),
        "unresolved_contradiction_count": _sum_decimal(
            report.rows,
            "unresolved_contradiction_count",
        ),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")


def _row_source_family_counts(
    rows: tuple[TeamSpecialistSourceFamilyRotationNeedV2Row, ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.source_family] = counts.get(row.source_family, 0) + 1
    return counts


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be present")
    _require_digest_string("derived_validation_digest", digest)
    expected = _digest_for_json_payload(payload)
    if digest != expected:
        raise ValueError("derived_validation_digest must match report contents")


def _report_digest(report: TeamSpecialistSourceFamilyRotationNeedV2Report) -> str:
    payload = {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }
    return _digest_for_json_payload(_json_ready(payload))


def _digest_for_json_payload(payload: dict[str, Any]) -> str:
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    canonical_payload = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical_payload.encode("utf-8")).hexdigest()


def _age_seconds(value: datetime, generated_at: datetime) -> Decimal:
    if value > generated_at:
        return ZERO_SECONDS
    delta = generated_at - value
    with localcontext(DECIMAL_CONTEXT):
        return (
            Decimal(delta.days) * SECONDS_PER_DAY
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        ).quantize(SECONDS_QUANTUM)


def _ratio(numerator: int, denominator: int) -> Decimal:
    if denominator == 0:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (Decimal(numerator) / Decimal(denominator)).quantize(RATIO_QUANTUM)


def _score_ratio(numerator: int, denominator: int) -> Decimal:
    if denominator == 0:
        return ZERO_SCORE
    with localcontext(DECIMAL_CONTEXT):
        return (Decimal(numerator) / Decimal(denominator)).quantize(SCORE_QUANTUM)


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_score(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(SCORE_QUANTUM)
    if normalized < ZERO_SCORE:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE_SCORE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _normalize_positive_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_probability(field_name, value)
    if normalized <= ZERO_RATIO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(RATIO_QUANTUM)
    if normalized < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _normalize_positive_seconds(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_seconds(field_name, value)
    if normalized <= ZERO_SECONDS:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_seconds(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(SECONDS_QUANTUM)
    if normalized < ZERO_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    normalized = decimal.quantize(COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != decimal:
        raise ValueError(f"{field_name} must be a whole number")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    codes = tuple(value)
    for code in codes:
        _require_member("reason_codes", code, ROW_REASON_CODES)
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in ROW_REASON_CODES if code in codes) != codes:
        raise ValueError("reason_codes must be deterministic")
    return codes


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    codes = tuple(value)
    for code in codes:
        _require_member("reason_codes", code, REPORT_REASON_CODES)
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in REPORT_REASON_CODES if code in codes) != codes:
        raise ValueError("reason_codes must be deterministic")
    return codes


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    if _has_unsafe_public_term(value):
        raise ValueError(f"unsafe public value in {field_name}")


def _require_digest_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    _require_public_string(field_name, value)
    if value not in members:
        raise ValueError(f"{field_name} must be one of {', '.join(members)}")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_unsafe_public_term(value):
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_term(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _has_unsafe_public_term(value: str) -> bool:
    normalized = value.lower()
    return any(term in normalized for term in UNSAFE_PUBLIC_TERMS)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON value must use Decimal-derived string values")
    if type(value) is bool or type(value) is str:
        return value
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")
