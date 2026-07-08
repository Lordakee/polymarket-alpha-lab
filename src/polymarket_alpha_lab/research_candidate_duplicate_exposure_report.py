"""Pure report-only duplicate research exposure checks for candidates."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any


DEFAULT_CONFIG_VERSION = "research-candidate-duplicate-exposure-report-v0"

STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1.000000")
RATIO_QUANT = Decimal("0.000001")

NO_PAIRS_REASON = "no_candidate_overlap_pairs"
DUPLICATE_PASS_REASON = "duplicate_exposure_pass"
DUPLICATE_WATCH_REASON = "duplicate_exposure_watch"
DUPLICATE_BLOCK_REASON = "duplicate_exposure_block"
CATALYST_WATCH_REASON = "aggregate_catalyst_overlap_watch"
CATALYST_BLOCK_REASON = "aggregate_catalyst_overlap_block"
DOMAIN_WATCH_REASON = "domain_overlap_watch"
DOMAIN_BLOCK_REASON = "domain_overlap_block"
SOURCE_WATCH_REASON = "source_class_overlap_watch"
SOURCE_BLOCK_REASON = "source_class_overlap_block"
SETTLEMENT_WATCH_REASON = "settlement_linkage_watch"
SETTLEMENT_BLOCK_REASON = "settlement_linkage_block"
PRESSURE_WATCH_REASON = "liquidity_cost_pressure_watch"
PRESSURE_BLOCK_REASON = "liquidity_cost_pressure_block"
REPORT_PASS_REASON = "candidate_duplicate_exposure_pass"

REASON_CODES = (
    NO_PAIRS_REASON,
    REPORT_PASS_REASON,
    DUPLICATE_PASS_REASON,
    DUPLICATE_WATCH_REASON,
    DUPLICATE_BLOCK_REASON,
    CATALYST_WATCH_REASON,
    CATALYST_BLOCK_REASON,
    DOMAIN_WATCH_REASON,
    DOMAIN_BLOCK_REASON,
    SOURCE_WATCH_REASON,
    SOURCE_BLOCK_REASON,
    SETTLEMENT_WATCH_REASON,
    SETTLEMENT_BLOCK_REASON,
    PRESSURE_WATCH_REASON,
    PRESSURE_BLOCK_REASON,
)

UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "event_id",
    "market_id",
    "market_slug",
    "source_id",
)


@dataclass(frozen=True)
class ResearchCandidateDuplicateExposureConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    watch_duplicate_exposure_score: Decimal = Decimal("0.300000")
    block_duplicate_exposure_score: Decimal = Decimal("0.800000")
    catalyst_overlap_weight: Decimal = Decimal("0.225000")
    domain_overlap_weight: Decimal = Decimal("0.225000")
    source_class_overlap_weight: Decimal = Decimal("0.225000")
    settlement_linkage_weight: Decimal = Decimal("0.125000")
    liquidity_cost_pressure_weight: Decimal = Decimal("0.200000")
    component_watch_threshold: Decimal = Decimal("0.333333")
    component_block_threshold: Decimal = Decimal("0.800000")
    pressure_watch_threshold: Decimal = Decimal("0.700000")
    pressure_block_threshold: Decimal = Decimal("0.900000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "watch_duplicate_exposure_score",
            "block_duplicate_exposure_score",
            "catalyst_overlap_weight",
            "domain_overlap_weight",
            "source_class_overlap_weight",
            "settlement_linkage_weight",
            "liquidity_cost_pressure_weight",
            "component_watch_threshold",
            "component_block_threshold",
            "pressure_watch_threshold",
            "pressure_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.watch_duplicate_exposure_score >= self.block_duplicate_exposure_score:
            raise ValueError(
                "watch_duplicate_exposure_score must be less than block_duplicate_exposure_score",
            )
        if self.component_watch_threshold >= self.component_block_threshold:
            raise ValueError(
                "component_watch_threshold must be less than component_block_threshold",
            )
        if self.pressure_watch_threshold >= self.pressure_block_threshold:
            raise ValueError(
                "pressure_watch_threshold must be less than pressure_block_threshold",
            )
        if _quantize(
            self.catalyst_overlap_weight
            + self.domain_overlap_weight
            + self.source_class_overlap_weight
            + self.settlement_linkage_weight
            + self.liquidity_cost_pressure_weight,
        ) != ONE:
            raise ValueError("duplicate exposure component weights must sum to 1")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchCandidateExposureAggregate:
    candidate_label: str
    catalyst_classes: tuple[str, ...]
    domain_classes: tuple[str, ...]
    source_classes: tuple[str, ...]
    settlement_linkage_classes: tuple[str, ...]
    liquidity_pressure_score: Decimal
    cost_pressure_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("candidate_label", self.candidate_label)
        object.__setattr__(
            self,
            "catalyst_classes",
            _normalize_public_tuple("catalyst_classes", self.catalyst_classes),
        )
        object.__setattr__(
            self,
            "domain_classes",
            _normalize_public_tuple("domain_classes", self.domain_classes),
        )
        object.__setattr__(
            self,
            "source_classes",
            _normalize_public_tuple("source_classes", self.source_classes),
        )
        object.__setattr__(
            self,
            "settlement_linkage_classes",
            _normalize_public_tuple(
                "settlement_linkage_classes",
                self.settlement_linkage_classes,
            ),
        )
        object.__setattr__(
            self,
            "liquidity_pressure_score",
            _normalize_ratio("liquidity_pressure_score", self.liquidity_pressure_score),
        )
        object.__setattr__(
            self,
            "cost_pressure_score",
            _normalize_ratio("cost_pressure_score", self.cost_pressure_score),
        )
        _require_hard_flags("candidate aggregate", self)


@dataclass(frozen=True)
class ResearchCandidateDuplicateExposureReportRow:
    candidate_a_label: str
    candidate_b_label: str
    catalyst_overlap_ratio: Decimal
    domain_overlap_ratio: Decimal
    source_class_overlap_ratio: Decimal
    settlement_linkage_ratio: Decimal
    liquidity_cost_pressure_score: Decimal
    duplicate_exposure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("candidate_a_label", self.candidate_a_label)
        _require_public_string("candidate_b_label", self.candidate_b_label)
        if self.candidate_a_label >= self.candidate_b_label:
            raise ValueError("candidate labels must be sorted and unique")
        for field_name in (
            "catalyst_overlap_ratio",
            "domain_overlap_ratio",
            "source_class_overlap_ratio",
            "settlement_linkage_ratio",
            "liquidity_cost_pressure_score",
            "duplicate_exposure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report row", self)


@dataclass(frozen=True)
class ResearchCandidateDuplicateExposureReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_count("count", self.count))
        if self.count <= ZERO:
            raise ValueError("count must be positive")
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchCandidateDuplicateExposureReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pair_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_duplicate_exposure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchCandidateDuplicateExposureReasonCodeCount, ...]
    report_digest: str
    rows: tuple[ResearchCandidateDuplicateExposureReportRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pair_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_duplicate_exposure_score",
            _normalize_ratio(
                "max_duplicate_exposure_score",
                self.max_duplicate_exposure_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_digest("report_digest", self.report_digest)
        object.__setattr__(self, "rows", _normalize_report_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report(self)


def build_research_candidate_duplicate_exposure_report(
    candidates: tuple[ResearchCandidateExposureAggregate, ...],
    *,
    config: ResearchCandidateDuplicateExposureConfig,
    generated_at: datetime,
) -> ResearchCandidateDuplicateExposureReport:
    if type(config) is not ResearchCandidateDuplicateExposureConfig:
        raise ValueError("config must be a ResearchCandidateDuplicateExposureConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    candidate_rows = _normalize_candidate_rows(candidates)
    pair_rows = _build_pair_rows(candidate_rows, config=config)
    status = _report_status(pair_rows)
    reason_codes = _report_reason_codes(pair_rows, status)
    max_score = max((row.duplicate_exposure_score for row in pair_rows), default=ZERO)
    values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "candidate_count": Decimal(len(candidate_rows)),
        "pair_count": Decimal(len(pair_rows)),
        "pass_count": _status_count(pair_rows, "pass"),
        "watch_count": _status_count(pair_rows, "watch"),
        "block_count": _status_count(pair_rows, "block"),
        "max_duplicate_exposure_score": _quantize(max_score),
        "status": status,
        "reason_codes": reason_codes,
        "reason_code_counts": _reason_code_counts(pair_rows, reason_codes),
        "rows": pair_rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchCandidateDuplicateExposureReport(
        report_digest=_report_digest_for_values(values),
        **values,
    )


def research_candidate_duplicate_exposure_report_payload(
    report: ResearchCandidateDuplicateExposureReport,
) -> dict[str, Any]:
    if type(report) is not ResearchCandidateDuplicateExposureReport:
        raise ValueError("report must be a ResearchCandidateDuplicateExposureReport")
    _require_hard_flags("report", report)
    return _json_ready(asdict(report))


def _build_pair_rows(
    candidates: tuple[ResearchCandidateExposureAggregate, ...],
    *,
    config: ResearchCandidateDuplicateExposureConfig,
) -> tuple[ResearchCandidateDuplicateExposureReportRow, ...]:
    rows: list[ResearchCandidateDuplicateExposureReportRow] = []
    for left_index, left in enumerate(candidates):
        for right in candidates[left_index + 1 :]:
            rows.append(_build_pair_row(left, right, config=config))
    return tuple(sorted(rows, key=_report_row_sort_key))


def _build_pair_row(
    left: ResearchCandidateExposureAggregate,
    right: ResearchCandidateExposureAggregate,
    *,
    config: ResearchCandidateDuplicateExposureConfig,
) -> ResearchCandidateDuplicateExposureReportRow:
    candidate_a, candidate_b = tuple(
        sorted((left, right), key=lambda item: item.candidate_label),
    )
    catalyst_overlap = _overlap_ratio(candidate_a.catalyst_classes, candidate_b.catalyst_classes)
    domain_overlap = _overlap_ratio(candidate_a.domain_classes, candidate_b.domain_classes)
    source_overlap = _overlap_ratio(candidate_a.source_classes, candidate_b.source_classes)
    settlement_overlap = _overlap_ratio(
        candidate_a.settlement_linkage_classes,
        candidate_b.settlement_linkage_classes,
    )
    pressure_score = max(
        _average_pressure_score(candidate_a),
        _average_pressure_score(candidate_b),
    )
    exposure_score = _quantize(
        (catalyst_overlap * config.catalyst_overlap_weight)
        + (domain_overlap * config.domain_overlap_weight)
        + (source_overlap * config.source_class_overlap_weight)
        + (settlement_overlap * config.settlement_linkage_weight)
        + (pressure_score * config.liquidity_cost_pressure_weight),
    )
    status = _row_status(
        duplicate_exposure_score=exposure_score,
        pressure_score=pressure_score,
        config=config,
    )
    return ResearchCandidateDuplicateExposureReportRow(
        candidate_a_label=candidate_a.candidate_label,
        candidate_b_label=candidate_b.candidate_label,
        catalyst_overlap_ratio=catalyst_overlap,
        domain_overlap_ratio=domain_overlap,
        source_class_overlap_ratio=source_overlap,
        settlement_linkage_ratio=settlement_overlap,
        liquidity_cost_pressure_score=pressure_score,
        duplicate_exposure_score=exposure_score,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            catalyst_overlap=catalyst_overlap,
            domain_overlap=domain_overlap,
            source_overlap=source_overlap,
            settlement_overlap=settlement_overlap,
            pressure_score=pressure_score,
            config=config,
        ),
    )


def _row_status(
    *,
    duplicate_exposure_score: Decimal,
    pressure_score: Decimal,
    config: ResearchCandidateDuplicateExposureConfig,
) -> str:
    _ = pressure_score
    if duplicate_exposure_score >= config.block_duplicate_exposure_score:
        return "block"
    if duplicate_exposure_score >= config.watch_duplicate_exposure_score:
        return "watch"
    return "pass"


def _average_pressure_score(candidate: ResearchCandidateExposureAggregate) -> Decimal:
    return _quantize(
        (candidate.liquidity_pressure_score + candidate.cost_pressure_score)
        / Decimal("2"),
    )


def _row_reason_codes(
    *,
    status: str,
    catalyst_overlap: Decimal,
    domain_overlap: Decimal,
    source_overlap: Decimal,
    settlement_overlap: Decimal,
    pressure_score: Decimal,
    config: ResearchCandidateDuplicateExposureConfig,
) -> tuple[str, ...]:
    reasons: set[str] = set()
    if status == "block":
        reasons.add(DUPLICATE_BLOCK_REASON)
    elif status == "watch":
        reasons.add(DUPLICATE_WATCH_REASON)
    else:
        reasons.add(DUPLICATE_PASS_REASON)
    _add_component_reason(
        reasons,
        catalyst_overlap,
        watch_reason=CATALYST_WATCH_REASON,
        block_reason=CATALYST_BLOCK_REASON,
        config=config,
    )
    _add_component_reason(
        reasons,
        domain_overlap,
        watch_reason=DOMAIN_WATCH_REASON,
        block_reason=DOMAIN_BLOCK_REASON,
        config=config,
    )
    _add_component_reason(
        reasons,
        source_overlap,
        watch_reason=SOURCE_WATCH_REASON,
        block_reason=SOURCE_BLOCK_REASON,
        config=config,
    )
    _add_component_reason(
        reasons,
        settlement_overlap,
        watch_reason=SETTLEMENT_WATCH_REASON,
        block_reason=SETTLEMENT_BLOCK_REASON,
        config=config,
    )
    if pressure_score >= config.pressure_block_threshold:
        reasons.add(PRESSURE_BLOCK_REASON)
    elif pressure_score >= config.pressure_watch_threshold:
        reasons.add(PRESSURE_WATCH_REASON)
    return tuple(sorted(reasons))


def _add_component_reason(
    reasons: set[str],
    value: Decimal,
    *,
    watch_reason: str,
    block_reason: str,
    config: ResearchCandidateDuplicateExposureConfig,
) -> None:
    if value >= config.component_block_threshold:
        reasons.add(block_reason)
    elif value >= config.component_watch_threshold:
        reasons.add(watch_reason)


def _report_status(rows: tuple[ResearchCandidateDuplicateExposureReportRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchCandidateDuplicateExposureReportRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (NO_PAIRS_REASON,)
    if status == "pass":
        return (REPORT_PASS_REASON,)
    return tuple(sorted({code for row in rows if row.status == status for code in row.reason_codes}))


def _reason_code_counts(
    rows: tuple[ResearchCandidateDuplicateExposureReportRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchCandidateDuplicateExposureReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchCandidateDuplicateExposureReasonCodeCount(
                reason_code=NO_PAIRS_REASON,
                count=Decimal("1"),
            ),
        )
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + Decimal("1")
    if reason_codes == (REPORT_PASS_REASON,):
        counts[REPORT_PASS_REASON] = Decimal("1")
    return tuple(
        ResearchCandidateDuplicateExposureReasonCodeCount(reason_code=code, count=count)
        for code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _report_row_sort_key(
    row: ResearchCandidateDuplicateExposureReportRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        -row.duplicate_exposure_score,
        -row.liquidity_cost_pressure_score,
        row.candidate_a_label,
        row.candidate_b_label,
    )


def _normalize_candidate_rows(
    value: tuple[ResearchCandidateExposureAggregate, ...],
) -> tuple[ResearchCandidateExposureAggregate, ...]:
    if type(value) is not tuple:
        raise ValueError("candidates must be a tuple")
    for item in value:
        if type(item) is not ResearchCandidateExposureAggregate:
            raise ValueError("candidates must contain ResearchCandidateExposureAggregate values")
        _require_hard_flags("candidate aggregate", item)
    labels = tuple(item.candidate_label for item in value)
    if len(set(labels)) != len(labels):
        raise ValueError("candidate_label values must be unique")
    return tuple(sorted(value, key=lambda item: item.candidate_label))


def _normalize_report_rows(
    rows: object,
) -> tuple[ResearchCandidateDuplicateExposureReportRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchCandidateDuplicateExposureReportRow:
            raise ValueError(
                "rows must contain ResearchCandidateDuplicateExposureReportRow values",
            )
        _require_hard_flags("report row", row)
    if tuple(sorted(rows, key=_report_row_sort_key)) != rows:
        raise ValueError("rows must be sorted")
    if len({(row.candidate_a_label, row.candidate_b_label) for row in rows}) != len(rows):
        raise ValueError("rows must be unique by candidate pair")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[ResearchCandidateDuplicateExposureReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    counts = tuple(value)
    for count in counts:
        if type(count) is not ResearchCandidateDuplicateExposureReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchCandidateDuplicateExposureReasonCodeCount values",
            )
        _require_hard_flags("reason code count", count)
    if tuple(sorted(counts, key=lambda item: item.reason_code)) != counts:
        raise ValueError("reason_code_counts must be sorted")
    return counts


def _normalize_reason_codes(value: object, *, allow_empty: bool) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code)
    normalized = tuple(sorted(set(value)))
    if not allow_empty and not normalized:
        raise ValueError("reason_codes must be nonempty")
    return normalized


def _validate_report(report: ResearchCandidateDuplicateExposureReport) -> None:
    if report.pair_count != Decimal(len(report.rows)):
        raise ValueError("pair_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.max_duplicate_exposure_score != _quantize(
        max((row.duplicate_exposure_score for row in report.rows), default=ZERO),
    ):
        raise ValueError("max_duplicate_exposure_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, report.status):
        raise ValueError("reason_codes must match rows")
    if report.report_digest != _report_digest(report):
        raise ValueError("report_digest must match report fields")


def _status_count(
    rows: tuple[ResearchCandidateDuplicateExposureReportRow, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in rows if row.status == status))


def _overlap_ratio(left: tuple[str, ...], right: tuple[str, ...]) -> Decimal:
    left_set = set(left)
    right_set = set(right)
    union = left_set | right_set
    if not union:
        return _quantize(ZERO)
    return _quantize(Decimal(len(left_set & right_set)) / Decimal(len(union)))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(RATIO_QUANT)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _normalize_public_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    for item in value:
        _require_public_string(field_name, item)
    return tuple(sorted(set(value)))


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain known duplicate exposure reasons")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must not contain raw public identifiers")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANT)


def _report_digest(report: ResearchCandidateDuplicateExposureReport) -> str:
    return _report_digest_for_values(asdict(report))


def _report_digest_for_values(values: dict[str, Any]) -> str:
    payload = {key: value for key, value in values.items() if key != "report_digest"}
    encoded = json.dumps(
        _json_ready(payload),
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return str(value)
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        raise ValueError("payload must not contain int values")
    if isinstance(value, float):
        raise ValueError("payload must not contain float values")
    if isinstance(value, str):
        _require_public_string("payload string", value)
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _require_public_string("payload key", key)
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "ResearchCandidateDuplicateExposureConfig",
    "ResearchCandidateExposureAggregate",
    "ResearchCandidateDuplicateExposureReportRow",
    "ResearchCandidateDuplicateExposureReasonCodeCount",
    "ResearchCandidateDuplicateExposureReport",
    "build_research_candidate_duplicate_exposure_report",
    "research_candidate_duplicate_exposure_report_payload",
)
