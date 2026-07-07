from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Iterable, Mapping


DEFAULT_RESEARCH_PACKET_SOURCE_FAMILY_COVERAGE_GAP_V2_CONFIG_VERSION = (
    "research_packet_source_family_coverage_gap_v2:1.0"
)

SOURCE_FAMILY_KINDS = ("official", "primary", "secondary", "contradiction")
STATUSES = ("covered", "watch", "blocked")

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SIX_PLACES = Decimal("0.000001")
COUNT_PLACES = Decimal("0.000000")

PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}$")
UNSAFE_PUBLIC_TERMS = (
    "private",
    "mnemonic",
    "seed phrase",
    "password",
    "bearer",
)


@dataclass(frozen=True)
class ResearchPacketSourceFamilyCoverageGapV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_SOURCE_FAMILY_COVERAGE_GAP_V2_CONFIG_VERSION
    )
    max_freshness_age_hours: Decimal = Decimal("24.000000")
    min_independent_source_count: Decimal = Decimal("3.000000")
    watch_gap_score: Decimal = Decimal("0.250000")
    blocked_gap_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceFamilyCoverageGapV2Config:
            raise TypeError(
                "ResearchPacketSourceFamilyCoverageGapV2Config does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFamilyCoverageGapV2Config:
            raise ValueError(
                "config must be exactly "
                "ResearchPacketSourceFamilyCoverageGapV2Config",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_SOURCE_FAMILY_COVERAGE_GAP_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        object.__setattr__(
            self,
            "max_freshness_age_hours",
            _require_positive_decimal(
                "max_freshness_age_hours",
                self.max_freshness_age_hours,
            ),
        )
        object.__setattr__(
            self,
            "min_independent_source_count",
            _require_positive_decimal(
                "min_independent_source_count",
                self.min_independent_source_count,
            ),
        )
        object.__setattr__(
            self,
            "watch_gap_score",
            _require_probability_decimal("watch_gap_score", self.watch_gap_score),
        )
        object.__setattr__(
            self,
            "blocked_gap_score",
            _require_probability_decimal("blocked_gap_score", self.blocked_gap_score),
        )
        if self.watch_gap_score >= self.blocked_gap_score:
            raise ValueError("watch_gap_score must be below blocked_gap_score")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchPacketSourceFamilyCoverageEvidenceV2:
    source_id: str
    source_family: str
    source_family_kind: str
    observed_at: datetime
    independence_key: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceFamilyCoverageEvidenceV2:
            raise TypeError(
                "ResearchPacketSourceFamilyCoverageEvidenceV2 does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFamilyCoverageEvidenceV2:
            raise ValueError(
                "evidence must be exactly "
                "ResearchPacketSourceFamilyCoverageEvidenceV2",
            )
        for field_name in ("source_id", "source_family", "independence_key"):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_member(
            "source_family_kind",
            self.source_family_kind,
            SOURCE_FAMILY_KINDS,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("evidence", self)
        _reject_unsafe_public_payload("evidence", self)


@dataclass(frozen=True)
class ResearchPacketSourceFamilyCoverageSubjectV2:
    packet_id: str
    category: str
    archetype: str
    required_official_source_families: tuple[str, ...]
    required_primary_source_families: tuple[str, ...]
    required_secondary_source_families: tuple[str, ...]
    required_contradiction_source_families: tuple[str, ...]
    observed_source_families: tuple[ResearchPacketSourceFamilyCoverageEvidenceV2, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceFamilyCoverageSubjectV2:
            raise TypeError(
                "ResearchPacketSourceFamilyCoverageSubjectV2 does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFamilyCoverageSubjectV2:
            raise ValueError(
                "subject must be exactly "
                "ResearchPacketSourceFamilyCoverageSubjectV2",
            )
        for field_name in ("packet_id", "category", "archetype"):
            _require_public_identifier(field_name, getattr(self, field_name))
        for field_name in (
            "required_official_source_families",
            "required_primary_source_families",
            "required_secondary_source_families",
            "required_contradiction_source_families",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_identifier_tuple(field_name, getattr(self, field_name)),
            )
        if (
            not self.required_official_source_families
            and not self.required_primary_source_families
            and not self.required_secondary_source_families
            and not self.required_contradiction_source_families
        ):
            raise ValueError("at least one required source family must be configured")
        object.__setattr__(
            self,
            "observed_source_families",
            _normalize_evidence_tuple(self.observed_source_families),
        )
        _require_hard_flags("subject", self)
        _reject_unsafe_public_payload("subject", self)


@dataclass(frozen=True)
class ResearchPacketSourceFamilyCoverageGapV2Row:
    packet_id: str
    category: str
    archetype: str
    coverage_status: str
    coverage_gap_score: Decimal
    official_family_gap_score: Decimal
    primary_family_gap_score: Decimal
    secondary_family_gap_score: Decimal
    contradiction_family_gap_score: Decimal
    freshness_gap_score: Decimal
    independence_gap_score: Decimal
    required_family_count: Decimal
    observed_required_family_count: Decimal
    fresh_required_family_count: Decimal
    independent_source_count: Decimal
    missing_official_source_families: tuple[str, ...]
    missing_primary_source_families: tuple[str, ...]
    missing_secondary_source_families: tuple[str, ...]
    missing_contradiction_source_families: tuple[str, ...]
    stale_required_source_families: tuple[str, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceFamilyCoverageGapV2Row:
            raise TypeError(
                "ResearchPacketSourceFamilyCoverageGapV2Row does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFamilyCoverageGapV2Row:
            raise ValueError(
                "row must be exactly ResearchPacketSourceFamilyCoverageGapV2Row",
            )
        for field_name in ("packet_id", "category", "archetype"):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_member("coverage_status", self.coverage_status, STATUSES)
        for field_name in (
            "coverage_gap_score",
            "official_family_gap_score",
            "primary_family_gap_score",
            "secondary_family_gap_score",
            "contradiction_family_gap_score",
            "freshness_gap_score",
            "independence_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "required_family_count",
            "observed_required_family_count",
            "fresh_required_family_count",
            "independent_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "missing_official_source_families",
            "missing_primary_source_families",
            "missing_secondary_source_families",
            "missing_contradiction_source_families",
            "stale_required_source_families",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_identifier_tuple(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchPacketSourceFamilyCoverageGapV2Report:
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    covered_row_count: Decimal
    watch_row_count: Decimal
    blocked_row_count: Decimal
    max_coverage_gap_score: Decimal
    rows: tuple[ResearchPacketSourceFamilyCoverageGapV2Row, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceFamilyCoverageGapV2Report:
            raise TypeError(
                "ResearchPacketSourceFamilyCoverageGapV2Report does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceFamilyCoverageGapV2Report:
            raise ValueError(
                "report must be exactly ResearchPacketSourceFamilyCoverageGapV2Report",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        _require_member("status", self.status, STATUSES)
        for field_name in (
            "row_count",
            "covered_row_count",
            "watch_row_count",
            "blocked_row_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_coverage_gap_score",
            _require_probability_decimal(
                "max_coverage_gap_score",
                self.max_coverage_gap_score,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_public_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_payload(_payload_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _reject_unsafe_public_payload(
            "ResearchPacketSourceFamilyCoverageGapV2Report.payload",
            payload,
            allow_json_containers=True,
        )
        return payload


def build_research_packet_source_family_coverage_gap_v2_report(
    subjects: Iterable[ResearchPacketSourceFamilyCoverageSubjectV2],
    *,
    generated_at: datetime,
    config: ResearchPacketSourceFamilyCoverageGapV2Config | None = None,
) -> ResearchPacketSourceFamilyCoverageGapV2Report:
    normalized_config = config or ResearchPacketSourceFamilyCoverageGapV2Config()
    if type(normalized_config) is not ResearchPacketSourceFamilyCoverageGapV2Config:
        raise ValueError(
            "config must be exactly ResearchPacketSourceFamilyCoverageGapV2Config",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _row_for_subject(subject, generated_at_utc, normalized_config)
                for subject in _normalize_subjects(subjects)
            ),
            key=lambda row: (row.category, row.archetype, row.packet_id),
        ),
    )
    row_count = _count_decimal(len(rows))
    covered_row_count = _count_decimal(
        sum(Decimal("1") for row in rows if row.coverage_status == "covered"),
    )
    watch_row_count = _count_decimal(
        sum(Decimal("1") for row in rows if row.coverage_status == "watch"),
    )
    blocked_row_count = _count_decimal(
        sum(Decimal("1") for row in rows if row.coverage_status == "blocked"),
    )
    max_coverage_gap_score = max(
        (row.coverage_gap_score for row in rows),
        default=ZERO,
    )
    status = _report_status(blocked_row_count, watch_row_count)
    reason_codes = _report_reason_codes(status)
    payload_without_digest = {
        "generated_at": generated_at_utc,
        "config_version": normalized_config.config_version,
        "status": status,
        "row_count": row_count,
        "covered_row_count": covered_row_count,
        "watch_row_count": watch_row_count,
        "blocked_row_count": blocked_row_count,
        "max_coverage_gap_score": max_coverage_gap_score,
        "rows": rows,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchPacketSourceFamilyCoverageGapV2Report(
        generated_at=generated_at_utc,
        config_version=normalized_config.config_version,
        status=status,
        row_count=row_count,
        covered_row_count=covered_row_count,
        watch_row_count=watch_row_count,
        blocked_row_count=blocked_row_count,
        max_coverage_gap_score=max_coverage_gap_score,
        rows=rows,
        reason_codes=reason_codes,
        derived_validation_digest=_digest_payload(payload_without_digest),
    )


def research_packet_source_family_coverage_gap_v2_payload(
    report: ResearchPacketSourceFamilyCoverageGapV2Report,
) -> dict[str, object]:
    if type(report) is not ResearchPacketSourceFamilyCoverageGapV2Report:
        raise ValueError(
            "report must be exactly ResearchPacketSourceFamilyCoverageGapV2Report",
        )
    return report.payload


def _row_for_subject(
    subject: ResearchPacketSourceFamilyCoverageSubjectV2,
    generated_at: datetime,
    config: ResearchPacketSourceFamilyCoverageGapV2Config,
) -> ResearchPacketSourceFamilyCoverageGapV2Row:
    required_by_kind = _required_by_kind(subject)
    observed_pairs = _observed_required_pairs(subject, required_by_kind)
    fresh_pairs = _fresh_required_pairs(
        subject,
        required_by_kind,
        generated_at,
        config.max_freshness_age_hours,
    )

    for evidence in subject.observed_source_families:
        if evidence.observed_at > generated_at:
            raise ValueError("generated_at must not be before observed_at")

    missing_by_kind = {
        kind: tuple(
            sorted(family for family in required_by_kind[kind] if (kind, family) not in observed_pairs),
        )
        for kind in SOURCE_FAMILY_KINDS
    }
    stale_required_source_families = tuple(
        sorted(
            family
            for kind, family in observed_pairs
            if (kind, family) not in fresh_pairs
        ),
    )
    required_pair_count = sum(len(families) for families in required_by_kind.values())
    required_family_count = _count_decimal(required_pair_count)
    observed_required_family_count = _count_decimal(len(observed_pairs))
    fresh_required_family_count = _count_decimal(len(fresh_pairs))
    independent_source_count = _count_decimal(
        len(_independence_keys_for_required_sources(subject, required_by_kind)),
    )

    official_family_gap_score = _gap_ratio(
        len(missing_by_kind["official"]),
        len(required_by_kind["official"]),
    )
    primary_family_gap_score = _gap_ratio(
        len(missing_by_kind["primary"]),
        len(required_by_kind["primary"]),
    )
    secondary_family_gap_score = _gap_ratio(
        len(missing_by_kind["secondary"]),
        len(required_by_kind["secondary"]),
    )
    contradiction_family_gap_score = _gap_ratio(
        len(missing_by_kind["contradiction"]),
        len(required_by_kind["contradiction"]),
    )
    freshness_gap_score = _gap_ratio(
        required_pair_count - len(fresh_pairs),
        required_pair_count,
    )
    independence_gap_score = _decimal_gap_against_floor(
        independent_source_count,
        config.min_independent_source_count,
    )
    coverage_gap_score = _mean_probability(
        (
            official_family_gap_score,
            primary_family_gap_score,
            secondary_family_gap_score,
            contradiction_family_gap_score,
            freshness_gap_score,
            independence_gap_score,
        ),
    )
    coverage_status = _row_status(
        coverage_gap_score,
        config.watch_gap_score,
        config.blocked_gap_score,
    )
    return ResearchPacketSourceFamilyCoverageGapV2Row(
        packet_id=subject.packet_id,
        category=subject.category,
        archetype=subject.archetype,
        coverage_status=coverage_status,
        coverage_gap_score=coverage_gap_score,
        official_family_gap_score=official_family_gap_score,
        primary_family_gap_score=primary_family_gap_score,
        secondary_family_gap_score=secondary_family_gap_score,
        contradiction_family_gap_score=contradiction_family_gap_score,
        freshness_gap_score=freshness_gap_score,
        independence_gap_score=independence_gap_score,
        required_family_count=required_family_count,
        observed_required_family_count=observed_required_family_count,
        fresh_required_family_count=fresh_required_family_count,
        independent_source_count=independent_source_count,
        missing_official_source_families=missing_by_kind["official"],
        missing_primary_source_families=missing_by_kind["primary"],
        missing_secondary_source_families=missing_by_kind["secondary"],
        missing_contradiction_source_families=missing_by_kind["contradiction"],
        stale_required_source_families=stale_required_source_families,
        reason_codes=_row_reason_codes(
            coverage_status,
            missing_by_kind,
            stale_required_source_families,
            independence_gap_score,
        ),
    )


def _required_by_kind(
    subject: ResearchPacketSourceFamilyCoverageSubjectV2,
) -> dict[str, tuple[str, ...]]:
    return {
        "official": subject.required_official_source_families,
        "primary": subject.required_primary_source_families,
        "secondary": subject.required_secondary_source_families,
        "contradiction": subject.required_contradiction_source_families,
    }


def _observed_required_pairs(
    subject: ResearchPacketSourceFamilyCoverageSubjectV2,
    required_by_kind: Mapping[str, tuple[str, ...]],
) -> frozenset[tuple[str, str]]:
    return frozenset(
        (evidence.source_family_kind, evidence.source_family)
        for evidence in subject.observed_source_families
        if evidence.source_family in required_by_kind[evidence.source_family_kind]
    )


def _fresh_required_pairs(
    subject: ResearchPacketSourceFamilyCoverageSubjectV2,
    required_by_kind: Mapping[str, tuple[str, ...]],
    generated_at: datetime,
    max_freshness_age_hours: Decimal,
) -> frozenset[tuple[str, str]]:
    return frozenset(
        (evidence.source_family_kind, evidence.source_family)
        for evidence in subject.observed_source_families
        if evidence.source_family in required_by_kind[evidence.source_family_kind]
        and _age_hours(generated_at, evidence.observed_at) <= max_freshness_age_hours
    )


def _independence_keys_for_required_sources(
    subject: ResearchPacketSourceFamilyCoverageSubjectV2,
    required_by_kind: Mapping[str, tuple[str, ...]],
) -> frozenset[str]:
    return frozenset(
        evidence.independence_key
        for evidence in subject.observed_source_families
        if evidence.source_family in required_by_kind[evidence.source_family_kind]
    )


def _row_reason_codes(
    coverage_status: str,
    missing_by_kind: Mapping[str, tuple[str, ...]],
    stale_required_source_families: tuple[str, ...],
    independence_gap_score: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for kind in SOURCE_FAMILY_KINDS:
        if missing_by_kind[kind]:
            reason_codes.append(f"missing_{kind}_source_family")
    if stale_required_source_families:
        reason_codes.append("stale_required_source_family")
    if independence_gap_score > ZERO:
        reason_codes.append("independent_source_count_below_floor")
    if coverage_status == "covered" and not reason_codes:
        reason_codes.append("source_family_coverage_complete")
    elif coverage_status == "watch":
        reason_codes.append("source_family_coverage_watch")
    elif coverage_status == "blocked":
        reason_codes.append("source_family_coverage_blocked")
    return tuple(reason_codes)


def _report_status(blocked_row_count: Decimal, watch_row_count: Decimal) -> str:
    if blocked_row_count > ZERO:
        return "blocked"
    if watch_row_count > ZERO:
        return "watch"
    return "covered"


def _report_reason_codes(status: str) -> tuple[str, ...]:
    if status == "blocked":
        return ("blocked_source_family_coverage_gap_detected",)
    if status == "watch":
        return ("watch_source_family_coverage_gap_detected",)
    return ("source_family_coverage_clear",)


def _row_status(
    coverage_gap_score: Decimal,
    watch_gap_score: Decimal,
    blocked_gap_score: Decimal,
) -> str:
    if coverage_gap_score >= blocked_gap_score:
        return "blocked"
    if coverage_gap_score >= watch_gap_score:
        return "watch"
    return "covered"


def _gap_ratio(missing_count: int, required_count: int) -> Decimal:
    if required_count == 0:
        return ZERO
    return _quantize_probability(Decimal(missing_count) / Decimal(required_count))


def _decimal_gap_against_floor(value: Decimal, floor: Decimal) -> Decimal:
    if value >= floor:
        return ZERO
    return _quantize_probability((floor - value) / floor)


def _mean_probability(values: tuple[Decimal, ...]) -> Decimal:
    return _quantize_probability(sum(values, ZERO) / Decimal(len(values)))


def _age_hours(generated_at: datetime, observed_at: datetime) -> Decimal:
    seconds = Decimal(str((generated_at - observed_at).total_seconds()))
    if seconds < ZERO:
        raise ValueError("generated_at must not be before observed_at")
    return (seconds / Decimal("3600")).quantize(SIX_PLACES, rounding=ROUND_HALF_UP)


def _normalize_subjects(
    subjects: Iterable[ResearchPacketSourceFamilyCoverageSubjectV2],
) -> tuple[ResearchPacketSourceFamilyCoverageSubjectV2, ...]:
    if type(subjects) is tuple:
        items = subjects
    else:
        items = tuple(subjects)
    for item in items:
        if type(item) is not ResearchPacketSourceFamilyCoverageSubjectV2:
            raise ValueError(
                "subjects must contain only "
                "ResearchPacketSourceFamilyCoverageSubjectV2 values",
            )
    return items


def _normalize_rows(
    rows: tuple[ResearchPacketSourceFamilyCoverageGapV2Row, ...],
) -> tuple[ResearchPacketSourceFamilyCoverageGapV2Row, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchPacketSourceFamilyCoverageGapV2Row:
            raise ValueError(
                "rows must contain only ResearchPacketSourceFamilyCoverageGapV2Row",
            )
    return rows


def _normalize_evidence_tuple(
    values: tuple[ResearchPacketSourceFamilyCoverageEvidenceV2, ...],
) -> tuple[ResearchPacketSourceFamilyCoverageEvidenceV2, ...]:
    if type(values) is not tuple:
        raise ValueError("observed_source_families must be a tuple")
    for value in values:
        if type(value) is not ResearchPacketSourceFamilyCoverageEvidenceV2:
            raise ValueError(
                "observed_source_families must contain only "
                "ResearchPacketSourceFamilyCoverageEvidenceV2 values",
            )
    return values


def _normalize_identifier_tuple(field_name: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        _require_public_identifier(field_name, value)
        if value in seen:
            raise ValueError(f"{field_name} must not contain duplicate values")
        seen.add(value)
        normalized.append(value)
    return tuple(sorted(normalized))


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        raise ValueError("reason_codes must be a non-empty tuple")
    for value in values:
        _require_public_identifier("reason_codes", value)
    return values


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, field_name):
            raise ValueError(f"{label}.{field_name} must be present")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical public identifier")
    if not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a canonical public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _require_member(field_name: str, value: object, choices: tuple[str, ...]) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in choices:
        raise ValueError(f"{field_name} must be one of {choices}")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    return value.quantize(SIX_PLACES, rounding=ROUND_HALF_UP)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_PLACES, rounding=ROUND_HALF_UP)


def _quantize_probability(value: Decimal) -> Decimal:
    normalized = value.quantize(SIX_PLACES, rounding=ROUND_HALF_UP)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _payload_without_digest(
    report: ResearchPacketSourceFamilyCoverageGapV2Report,
) -> dict[str, object]:
    payload = asdict(report)
    payload.pop("derived_validation_digest")
    return payload


def _digest_payload(payload: Mapping[str, object]) -> str:
    json_ready_payload = _json_ready(payload)
    encoded = json.dumps(
        json_ready_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError(f"{type(value).__name__} is not JSON-ready")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_string("field", field.name)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{label} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_string("field", key)
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
            )
        return
    if isinstance(value, tuple):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, list):
        if not allow_json_containers:
            raise ValueError(f"{label} must remain constructor-normalized")
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)
        return
    if value is None or type(value) in (bool, Decimal, datetime):
        return
    raise ValueError(f"{label} contains unsupported public payload value")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} contains unsafe public text")
