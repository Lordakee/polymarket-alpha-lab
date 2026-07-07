"""Pure Phase 1 research evidence quorum score."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


CONFIG_VERSION = "phase-1-research-evidence-quorum-score"
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ONE_COUNT = Decimal("1")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
MINIMUM_OFFICIAL_SOURCE_COUNT = Decimal("1")
MINIMUM_INDEPENDENT_SOURCE_COUNT = Decimal("3")
MAXIMUM_SOURCE_FAMILY_CONCENTRATION = Decimal("0.500000")
BLOCK_SOURCE_FAMILY_CONCENTRATION = Decimal("0.750000")
MINIMUM_EVIDENCE_FRESHNESS_SCORE = Decimal("0.750000")
BLOCK_EVIDENCE_FRESHNESS_SCORE = Decimal("0.500000")
MINIMUM_RESOLUTION_RULE_COVERAGE_SCORE = Decimal("0.750000")
BLOCK_RESOLUTION_RULE_COVERAGE_SCORE = Decimal("0.500000")
PASS_SCORE_THRESHOLD = Decimal("0.800000")
WATCH_SCORE_THRESHOLD = Decimal("0.500000")
OFFICIAL_SOURCE_WEIGHT = Decimal("0.200000")
INDEPENDENT_SOURCE_WEIGHT = Decimal("0.250000")
SOURCE_FAMILY_DIVERSITY_WEIGHT = Decimal("0.200000")
EVIDENCE_FRESHNESS_WEIGHT = Decimal("0.175000")
RESOLUTION_RULE_COVERAGE_WEIGHT = Decimal("0.175000")
CONTRADICTION_PENALTY_WEIGHT = Decimal("0.350000")
STALE_SOURCE_PENALTY_WEIGHT = Decimal("0.050000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

QUORUM_SUPPORT_LEVELS = ("pass", "watch", "block")
RESEARCH_EVIDENCE_QUORUM_REASON_CODES = (
    "research_evidence_quorum_passed",
    "missing_official_source",
    "insufficient_independent_sources",
    "source_contradictions_present",
    "stale_sources_present",
    "source_family_concentration_high",
    "evidence_freshness_low",
    "resolution_rule_coverage_low",
    "quorum_support_watch_score",
    "quorum_support_block_score",
)

_ROW_DIGEST_FIELDS = (
    "candidate_public_ref",
    "official_source_count",
    "independent_source_count",
    "contradiction_count",
    "stale_source_count",
    "source_family_concentration",
    "evidence_freshness_score",
    "resolution_rule_coverage_score",
    "official_source_support_score",
    "independent_source_support_score",
    "source_family_diversity_score",
    "quorum_support_score",
    "quorum_support",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_DIGEST_FIELDS = (
    "config_version",
    "candidate_count",
    "pass_count",
    "watch_count",
    "block_count",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
)
_UNSAFE_PUBLIC_TERM_PARTS = (
    ("ht", "tp"),
    ("w", "ww."),
    (":", "//"),
    ("poly", "market"),
    ("mar", "ket"),
    ("sl", "ug"),
    ("ques", "tion"),
    ("0", "x"),
    ("au", "th"),
    ("wal", "let"),
    ("acc", "ount"),
    ("or", "der"),
    ("ex", "change"),
    ("mut", "ation"),
    ("net", "work"),
    ("data", "base"),
    ("d", "sn"),
    ("ta", "ble"),
    ("en", "v"),
    ("pri", "vate"),
    ("a", "pi_key"),
    ("se", "cret"),
    ("to", "ken"),
    ("sig", "ning"),
    ("tra", "de"),
    ("ad", "vice"),
    ("recom", "mend"),
    ("pos", "ition"),
    ("sta", "ke"),
    ("b", "uy"),
    ("se", "ll"),
)
_UNSAFE_PUBLIC_TERMS = tuple("".join(parts) for parts in _UNSAFE_PUBLIC_TERM_PARTS)


@dataclass(frozen=True)
class ResearchEvidenceQuorumPacketAggregate:
    candidate_public_ref: str
    official_source_count: Decimal
    independent_source_count: Decimal
    contradiction_count: Decimal
    stale_source_count: Decimal
    source_family_concentration: Decimal
    evidence_freshness_score: Decimal
    resolution_rule_coverage_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "aggregate",
            self,
            ResearchEvidenceQuorumPacketAggregate,
        )
        _require_public_ref("candidate_public_ref", self.candidate_public_ref)
        for field_name in (
            "official_source_count",
            "independent_source_count",
            "contradiction_count",
            "stale_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_family_concentration",
            "evidence_freshness_score",
            "resolution_rule_coverage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        reject_research_evidence_quorum_score_unsafe_payload(
            "research evidence quorum aggregate",
            self,
        )
        _require_paper_flags("research evidence quorum aggregate", self)


@dataclass(frozen=True)
class ResearchEvidenceQuorumScoreRow:
    candidate_public_ref: str
    official_source_count: Decimal
    independent_source_count: Decimal
    contradiction_count: Decimal
    stale_source_count: Decimal
    source_family_concentration: Decimal
    evidence_freshness_score: Decimal
    resolution_rule_coverage_score: Decimal
    official_source_support_score: Decimal
    independent_source_support_score: Decimal
    source_family_diversity_score: Decimal
    quorum_support_score: Decimal
    quorum_support: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchEvidenceQuorumScoreRow)
        _require_public_ref("candidate_public_ref", self.candidate_public_ref)
        for field_name in (
            "official_source_count",
            "independent_source_count",
            "contradiction_count",
            "stale_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_family_concentration",
            "evidence_freshness_score",
            "resolution_rule_coverage_score",
            "official_source_support_score",
            "independent_source_support_score",
            "source_family_diversity_score",
            "quorum_support_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_quorum_support("quorum_support", self.quorum_support)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        reject_research_evidence_quorum_score_unsafe_payload(
            "research evidence quorum row",
            self,
        )
        _require_paper_flags("research evidence quorum row", self)
        expected_digest = _row_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match row fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_evidence_quorum_score_row_payload(self)


@dataclass(frozen=True)
class ResearchEvidenceQuorumScoreReport:
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchEvidenceQuorumScoreRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchEvidenceQuorumScoreReport)
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report(self)
        reject_research_evidence_quorum_score_unsafe_payload(
            "research evidence quorum report",
            self,
        )
        _require_paper_flags("research evidence quorum report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_canonical_digest(self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_evidence_quorum_score_payload(self)


def score_research_evidence_quorum(
    aggregates: tuple[ResearchEvidenceQuorumPacketAggregate, ...],
) -> ResearchEvidenceQuorumScoreReport:
    if type(aggregates) is not tuple:
        raise ValueError("aggregates must be a tuple")
    if not aggregates:
        raise ValueError("aggregates must not be empty")

    rows: list[ResearchEvidenceQuorumScoreRow] = []
    seen_public_refs: set[str] = set()
    for aggregate in aggregates:
        if type(aggregate) is not ResearchEvidenceQuorumPacketAggregate:
            raise ValueError("aggregate must be a ResearchEvidenceQuorumPacketAggregate")
        _require_paper_flags("research evidence quorum aggregate", aggregate)
        reject_research_evidence_quorum_score_unsafe_payload(
            "research evidence quorum aggregate",
            aggregate,
        )
        if aggregate.candidate_public_ref in seen_public_refs:
            raise ValueError("candidate_public_ref must be unique")
        seen_public_refs.add(aggregate.candidate_public_ref)
        rows.append(_score_row(aggregate))

    sorted_rows = tuple(sorted(rows, key=lambda row: row.candidate_public_ref))
    return ResearchEvidenceQuorumScoreReport(
        config_version=CONFIG_VERSION,
        candidate_count=_count_decimal(len(sorted_rows)),
        pass_count=_support_count(sorted_rows, "pass"),
        watch_count=_support_count(sorted_rows, "watch"),
        block_count=_support_count(sorted_rows, "block"),
        reason_codes=_report_reason_codes(sorted_rows),
        rows=sorted_rows,
    )


def research_evidence_quorum_score_row_payload(
    row: ResearchEvidenceQuorumScoreRow,
) -> dict[str, Any]:
    if type(row) is not ResearchEvidenceQuorumScoreRow:
        raise ValueError("row must be a ResearchEvidenceQuorumScoreRow")
    _require_paper_flags("research evidence quorum row", row)
    if row.derived_validation_digest != _row_digest(row):
        raise ValueError("derived_validation_digest must match row fields")
    _validate_row(row)
    reject_research_evidence_quorum_score_unsafe_payload(
        "research evidence quorum row",
        row,
    )
    payload = _json_ready(asdict(row))
    if type(payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    return payload


def research_evidence_quorum_score_payload(
    report: ResearchEvidenceQuorumScoreReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEvidenceQuorumScoreReport:
        raise ValueError("report must be a ResearchEvidenceQuorumScoreReport")
    _require_paper_flags("research evidence quorum report", report)
    _validate_report(report)
    if report.derived_validation_digest != _report_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    reject_research_evidence_quorum_score_unsafe_payload(
        "research evidence quorum report",
        report,
    )
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def reject_research_evidence_quorum_score_unsafe_payload(
    label: str,
    payload: object,
) -> None:
    for item in _iter_public_strings(payload):
        lowered = item.lower()
        if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
            raise ValueError(f"unsafe public payload entry in {label}")


def _score_row(
    aggregate: ResearchEvidenceQuorumPacketAggregate,
) -> ResearchEvidenceQuorumScoreRow:
    official_support_score = _official_source_support_score(
        aggregate.official_source_count,
    )
    independent_support_score = _independent_source_support_score(
        aggregate.independent_source_count,
    )
    family_diversity_score = _source_family_diversity_score(
        aggregate.source_family_concentration,
    )
    support_score = _quorum_support_score(
        official_source_support_score=official_support_score,
        independent_source_support_score=independent_support_score,
        source_family_diversity_score=family_diversity_score,
        evidence_freshness_score=aggregate.evidence_freshness_score,
        resolution_rule_coverage_score=aggregate.resolution_rule_coverage_score,
        contradiction_count=aggregate.contradiction_count,
        stale_source_count=aggregate.stale_source_count,
    )
    support = _quorum_support(
        official_source_count=aggregate.official_source_count,
        independent_source_count=aggregate.independent_source_count,
        contradiction_count=aggregate.contradiction_count,
        source_family_concentration=aggregate.source_family_concentration,
        evidence_freshness_score=aggregate.evidence_freshness_score,
        resolution_rule_coverage_score=aggregate.resolution_rule_coverage_score,
        quorum_support_score=support_score,
    )
    return ResearchEvidenceQuorumScoreRow(
        candidate_public_ref=aggregate.candidate_public_ref,
        official_source_count=aggregate.official_source_count,
        independent_source_count=aggregate.independent_source_count,
        contradiction_count=aggregate.contradiction_count,
        stale_source_count=aggregate.stale_source_count,
        source_family_concentration=aggregate.source_family_concentration,
        evidence_freshness_score=aggregate.evidence_freshness_score,
        resolution_rule_coverage_score=aggregate.resolution_rule_coverage_score,
        official_source_support_score=official_support_score,
        independent_source_support_score=independent_support_score,
        source_family_diversity_score=family_diversity_score,
        quorum_support_score=support_score,
        quorum_support=support,
        reason_codes=_row_reason_codes(
            official_source_count=aggregate.official_source_count,
            independent_source_count=aggregate.independent_source_count,
            contradiction_count=aggregate.contradiction_count,
            stale_source_count=aggregate.stale_source_count,
            source_family_concentration=aggregate.source_family_concentration,
            evidence_freshness_score=aggregate.evidence_freshness_score,
            resolution_rule_coverage_score=aggregate.resolution_rule_coverage_score,
            quorum_support=support,
            quorum_support_score=support_score,
        ),
    )


def _official_source_support_score(official_source_count: Decimal) -> Decimal:
    return _coverage_ratio(official_source_count, MINIMUM_OFFICIAL_SOURCE_COUNT)


def _independent_source_support_score(independent_source_count: Decimal) -> Decimal:
    return _coverage_ratio(independent_source_count, MINIMUM_INDEPENDENT_SOURCE_COUNT)


def _source_family_diversity_score(source_family_concentration: Decimal) -> Decimal:
    return _clamp_ratio(ONE_RATIO - source_family_concentration)


def _coverage_ratio(value: Decimal, target: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(value / target)


def _quorum_support_score(
    *,
    official_source_support_score: Decimal,
    independent_source_support_score: Decimal,
    source_family_diversity_score: Decimal,
    evidence_freshness_score: Decimal,
    resolution_rule_coverage_score: Decimal,
    contradiction_count: Decimal,
    stale_source_count: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        raw_score = (
            official_source_support_score * OFFICIAL_SOURCE_WEIGHT
            + independent_source_support_score * INDEPENDENT_SOURCE_WEIGHT
            + source_family_diversity_score * SOURCE_FAMILY_DIVERSITY_WEIGHT
            + evidence_freshness_score * EVIDENCE_FRESHNESS_WEIGHT
            + resolution_rule_coverage_score * RESOLUTION_RULE_COVERAGE_WEIGHT
            - contradiction_count * CONTRADICTION_PENALTY_WEIGHT
            - stale_source_count * STALE_SOURCE_PENALTY_WEIGHT
        )
        return _clamp_ratio(raw_score)


def _quorum_support(
    *,
    official_source_count: Decimal,
    independent_source_count: Decimal,
    contradiction_count: Decimal,
    source_family_concentration: Decimal,
    evidence_freshness_score: Decimal,
    resolution_rule_coverage_score: Decimal,
    quorum_support_score: Decimal,
) -> str:
    if (
        official_source_count < MINIMUM_OFFICIAL_SOURCE_COUNT
        or contradiction_count > ZERO_COUNT
        or source_family_concentration > BLOCK_SOURCE_FAMILY_CONCENTRATION
        or evidence_freshness_score < BLOCK_EVIDENCE_FRESHNESS_SCORE
        or resolution_rule_coverage_score < BLOCK_RESOLUTION_RULE_COVERAGE_SCORE
        or quorum_support_score < WATCH_SCORE_THRESHOLD
    ):
        return "block"
    if (
        independent_source_count < MINIMUM_INDEPENDENT_SOURCE_COUNT
        or source_family_concentration > MAXIMUM_SOURCE_FAMILY_CONCENTRATION
        or evidence_freshness_score < MINIMUM_EVIDENCE_FRESHNESS_SCORE
        or resolution_rule_coverage_score < MINIMUM_RESOLUTION_RULE_COVERAGE_SCORE
        or quorum_support_score < PASS_SCORE_THRESHOLD
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    official_source_count: Decimal,
    independent_source_count: Decimal,
    contradiction_count: Decimal,
    stale_source_count: Decimal,
    source_family_concentration: Decimal,
    evidence_freshness_score: Decimal,
    resolution_rule_coverage_score: Decimal,
    quorum_support: str,
    quorum_support_score: Decimal,
) -> tuple[str, ...]:
    codes: list[str] = []
    if official_source_count < MINIMUM_OFFICIAL_SOURCE_COUNT:
        codes.append("missing_official_source")
    if independent_source_count < MINIMUM_INDEPENDENT_SOURCE_COUNT:
        codes.append("insufficient_independent_sources")
    if contradiction_count > ZERO_COUNT:
        codes.append("source_contradictions_present")
    if stale_source_count > ZERO_COUNT:
        codes.append("stale_sources_present")
    if source_family_concentration > MAXIMUM_SOURCE_FAMILY_CONCENTRATION:
        codes.append("source_family_concentration_high")
    if evidence_freshness_score < MINIMUM_EVIDENCE_FRESHNESS_SCORE:
        codes.append("evidence_freshness_low")
    if resolution_rule_coverage_score < MINIMUM_RESOLUTION_RULE_COVERAGE_SCORE:
        codes.append("resolution_rule_coverage_low")
    if quorum_support == "block" or quorum_support_score < WATCH_SCORE_THRESHOLD:
        codes.append("quorum_support_block_score")
    elif quorum_support == "watch" or quorum_support_score < PASS_SCORE_THRESHOLD:
        codes.append("quorum_support_watch_score")
    if not codes:
        codes.append("research_evidence_quorum_passed")
    return _normalize_reason_codes(tuple(codes))


def _report_reason_codes(
    rows: tuple[ResearchEvidenceQuorumScoreRow, ...],
) -> tuple[str, ...]:
    seen: set[str] = set()
    for row in rows:
        seen.update(row.reason_codes)
    return tuple(
        reason_code
        for reason_code in RESEARCH_EVIDENCE_QUORUM_REASON_CODES
        if reason_code in seen
    )


def _support_count(
    rows: tuple[ResearchEvidenceQuorumScoreRow, ...],
    support: str,
) -> Decimal:
    return _count_decimal(sum(ONE_COUNT for row in rows if row.quorum_support == support))


def _validate_row(row: ResearchEvidenceQuorumScoreRow) -> None:
    if row.official_source_support_score != _official_source_support_score(
        row.official_source_count,
    ):
        raise ValueError("official_source_support_score must match source count")
    if row.independent_source_support_score != _independent_source_support_score(
        row.independent_source_count,
    ):
        raise ValueError("independent_source_support_score must match source count")
    if row.source_family_diversity_score != _source_family_diversity_score(
        row.source_family_concentration,
    ):
        raise ValueError("source_family_diversity_score must match concentration")
    expected_score = _quorum_support_score(
        official_source_support_score=row.official_source_support_score,
        independent_source_support_score=row.independent_source_support_score,
        source_family_diversity_score=row.source_family_diversity_score,
        evidence_freshness_score=row.evidence_freshness_score,
        resolution_rule_coverage_score=row.resolution_rule_coverage_score,
        contradiction_count=row.contradiction_count,
        stale_source_count=row.stale_source_count,
    )
    if row.quorum_support_score != expected_score:
        raise ValueError("quorum_support_score must match components")
    expected_support = _quorum_support(
        official_source_count=row.official_source_count,
        independent_source_count=row.independent_source_count,
        contradiction_count=row.contradiction_count,
        source_family_concentration=row.source_family_concentration,
        evidence_freshness_score=row.evidence_freshness_score,
        resolution_rule_coverage_score=row.resolution_rule_coverage_score,
        quorum_support_score=row.quorum_support_score,
    )
    if row.quorum_support != expected_support:
        raise ValueError("quorum_support must match score and gates")
    expected_reasons = _row_reason_codes(
        official_source_count=row.official_source_count,
        independent_source_count=row.independent_source_count,
        contradiction_count=row.contradiction_count,
        stale_source_count=row.stale_source_count,
        source_family_concentration=row.source_family_concentration,
        evidence_freshness_score=row.evidence_freshness_score,
        resolution_rule_coverage_score=row.resolution_rule_coverage_score,
        quorum_support=row.quorum_support,
        quorum_support_score=row.quorum_support_score,
    )
    if row.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match quorum support")


def _validate_report(report: ResearchEvidenceQuorumScoreReport) -> None:
    if report.config_version != CONFIG_VERSION:
        raise ValueError("config_version must match Phase 1 quorum score")
    rows = _normalize_rows(report.rows)
    for row in rows:
        _require_current_row_digest(row)
        _validate_row(row)
    if rows != tuple(sorted(rows, key=lambda row: row.candidate_public_ref)):
        raise ValueError("rows must be sorted by candidate_public_ref")
    if report.candidate_count != _count_decimal(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _support_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _support_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _support_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _row_digest(row: ResearchEvidenceQuorumScoreRow) -> str:
    return _digest_from_fields(row, _ROW_DIGEST_FIELDS)


def _report_digest(report: ResearchEvidenceQuorumScoreReport) -> str:
    parts = []
    for field_name in _REPORT_DIGEST_FIELDS:
        if field_name == "rows":
            value = tuple(row.derived_validation_digest for row in report.rows)
        else:
            value = getattr(report, field_name)
        parts.append(f"{field_name}={_digest_value(value)}")
    return sha256("|".join(parts).encode("utf-8")).hexdigest()


def _require_current_row_digest(row: ResearchEvidenceQuorumScoreRow) -> None:
    if row.derived_validation_digest != _row_digest(row):
        raise ValueError("row derived_validation_digest must match row fields")


def _digest_from_fields(value: object, field_names: tuple[str, ...]) -> str:
    parts = tuple(
        f"{field_name}={_digest_value(getattr(value, field_name))}"
        for field_name in field_names
    )
    return sha256("|".join(parts).encode("utf-8")).hexdigest()


def _digest_value(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, tuple):
        return "[" + ",".join(_digest_value(item) for item in value) + "]"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is str:
        return value
    raise ValueError("digest value must be public scalar data")


def _normalize_rows(
    rows: tuple[ResearchEvidenceQuorumScoreRow, ...],
) -> tuple[ResearchEvidenceQuorumScoreRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_public_refs: set[str] = set()
    normalized_rows: list[ResearchEvidenceQuorumScoreRow] = []
    for row in rows:
        if type(row) is not ResearchEvidenceQuorumScoreRow:
            raise ValueError("rows must contain ResearchEvidenceQuorumScoreRow")
        if row.candidate_public_ref in seen_public_refs:
            raise ValueError("candidate_public_ref must be unique")
        seen_public_refs.add(row.candidate_public_ref)
        normalized_rows.append(row)
    return tuple(normalized_rows)


def _normalize_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for value in values:
        _require_canonical_string("reason_codes", value)
        if value not in RESEARCH_EVIDENCE_QUORUM_REASON_CODES:
            raise ValueError("reason_codes contains unsupported value")
        if value in seen:
            raise ValueError("reason_codes contains duplicate value")
        seen.add(value)
    return tuple(
        reason_code
        for reason_code in RESEARCH_EVIDENCE_QUORUM_REASON_CODES
        if reason_code in seen
    )


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(COUNT_QUANTUM)
    if normalized != value:
        raise ValueError(f"{field_name} must be integral")
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(RATIO_QUANTUM)
    if normalized != value:
        raise ValueError(f"{field_name} must use 0.000001 precision")
    if normalized < ZERO_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _clamp_ratio(value: Decimal) -> Decimal:
    if value <= ZERO_RATIO:
        return ZERO_RATIO
    if value >= ONE_RATIO:
        return ONE_RATIO
    return value.quantize(RATIO_QUANTUM)


def _count_decimal(value: object) -> Decimal:
    if isinstance(value, Decimal):
        return _normalize_nonnegative_count("count", value)
    return _normalize_nonnegative_count("count", Decimal(str(value)))


def _require_public_ref(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be public-safe")
    allowed_characters = "abcdefghijklmnopqrstuvwxyz0123456789-"
    if (
        len(value) > 96
        or not value.startswith("candidate-")
        or any(character not in allowed_characters for character in value)
        or "--" in value
        or any(term in value.lower() for term in _UNSAFE_PUBLIC_TERMS)
    ):
        raise ValueError(f"{field_name} must be public-safe")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")


def _require_quorum_support(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in QUORUM_SUPPORT_LEVELS:
        raise ValueError(f"{field_name} must be one of {QUORUM_SUPPORT_LEVELS!r}")


def _require_canonical_digest(value: object) -> None:
    _require_canonical_string("derived_validation_digest", value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError("derived_validation_digest must be lowercase hex")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_paper_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _iter_public_strings(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_strings(asdict(value))
    if isinstance(value, dict):
        items: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            items.append(key)
            items.extend(_iter_public_strings(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("public payload Decimal values must be finite")
        return ()
    if isinstance(value, float) or (isinstance(value, int) and not isinstance(value, bool)):
        raise ValueError("public payload numeric values must be Decimal strings")
    if value is None or type(value) is bool:
        return ()
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_iter_public_strings(item))
        return tuple(items)
    raise ValueError("public payload entries must be JSON scalar or container data")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, int) and not isinstance(value, bool):
        raise ValueError("JSON value must not be an int")
    if isinstance(value, (str, bool)):
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


__all__ = (
    "QUORUM_SUPPORT_LEVELS",
    "RESEARCH_EVIDENCE_QUORUM_REASON_CODES",
    "ResearchEvidenceQuorumPacketAggregate",
    "ResearchEvidenceQuorumScoreRow",
    "ResearchEvidenceQuorumScoreReport",
    "score_research_evidence_quorum",
    "research_evidence_quorum_score_row_payload",
    "research_evidence_quorum_score_payload",
    "reject_research_evidence_quorum_score_unsafe_payload",
)
