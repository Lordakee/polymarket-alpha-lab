"""Paper-only candidate fee sensitivity digest."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256


__all__ = (
    "DEFAULT_PAPER_CANDIDATE_FEE_SENSITIVITY_DIGEST_CONFIG_VERSION",
    "PaperCandidateFeeSensitivityDigestCandidate",
    "PaperCandidateFeeSensitivityDigestConfig",
    "PaperCandidateFeeSensitivityDigestReport",
    "PaperCandidateFeeSensitivityDigestRow",
    "build_paper_candidate_fee_sensitivity_digest",
    "paper_candidate_fee_sensitivity_digest_payload",
)


DEFAULT_PAPER_CANDIDATE_FEE_SENSITIVITY_DIGEST_CONFIG_VERSION = (
    "paper-candidate-fee-sensitivity-digest-v0"
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
DECIMAL_CONTEXT = Context(prec=64)

STATUSES = ("blocked", "watch", "clear")
STATUS_RANK = {"blocked": 0, "watch": 1, "clear": 2}
EMPTY_REASON_CODE = "fee_sensitivity_digest_empty"
CLEAR_REASON_CODE = "fee_sensitivity_clear"
NEGATIVE_STRESSED_EDGE_REASON_CODE = "fee_sensitivity_negative_stressed_edge"
NET_EDGE_BELOW_WATCH_REASON_CODE = "fee_sensitivity_net_edge_below_watch"
NET_EDGE_BELOW_CLEAR_REASON_CODE = "fee_sensitivity_net_edge_below_clear"
FEE_DRAG_SHARE_ELEVATED_REASON_CODE = "fee_sensitivity_fee_drag_share_elevated"
BASE_DRAG_REASON_CODE = "fee_sensitivity_base_drag_present"
STRESS_DRAG_REASON_CODE = "fee_sensitivity_stress_drag_present"
REPORT_REASON_PRIORITY = (
    NEGATIVE_STRESSED_EDGE_REASON_CODE,
    NET_EDGE_BELOW_WATCH_REASON_CODE,
    FEE_DRAG_SHARE_ELEVATED_REASON_CODE,
    CLEAR_REASON_CODE,
    STRESS_DRAG_REASON_CODE,
    BASE_DRAG_REASON_CODE,
    EMPTY_REASON_CODE,
)


@dataclass(frozen=True)
class PaperCandidateFeeSensitivityDigestConfig:
    config_version: str = DEFAULT_PAPER_CANDIDATE_FEE_SENSITIVITY_DIGEST_CONFIG_VERSION
    watch_net_edge_floor: Decimal = Decimal("0.020000")
    blocked_net_edge_floor: Decimal = Decimal("0.000000")
    watch_fee_drag_share: Decimal = Decimal("0.300000")
    blocked_fee_drag_share: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            PaperCandidateFeeSensitivityDigestConfig,
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_net_edge_floor",
            "blocked_net_edge_floor",
            "watch_fee_drag_share",
            "blocked_fee_drag_share",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class PaperCandidateFeeSensitivityDigestCandidate:
    candidate_reference: str
    market_slug: str
    observed_at: datetime
    base_edge: Decimal
    fee_drag: Decimal
    stress_fee_drag: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "candidate",
            self,
            PaperCandidateFeeSensitivityDigestCandidate,
        )
        _require_canonical_string("candidate_reference", self.candidate_reference)
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "base_edge",
            _normalize_ratio("base_edge", self.base_edge),
        )
        for field_name in ("fee_drag", "stress_fee_drag"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class PaperCandidateFeeSensitivityDigestRow:
    redacted_candidate_reference: str
    market_slug: str
    observed_at: datetime
    base_edge: Decimal
    fee_drag: Decimal
    stress_fee_drag: Decimal
    incremental_fee_drag: Decimal
    total_fee_drag: Decimal
    stressed_net_edge: Decimal
    fee_drag_share: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, PaperCandidateFeeSensitivityDigestRow)
        _require_canonical_string(
            "redacted_candidate_reference",
            self.redacted_candidate_reference,
        )
        _require_redacted_reference(self.redacted_candidate_reference)
        _require_canonical_string("market_slug", self.market_slug)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "base_edge",
            _normalize_ratio("base_edge", self.base_edge),
        )
        for field_name in (
            "fee_drag",
            "stress_fee_drag",
            "incremental_fee_drag",
            "total_fee_drag",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("stressed_net_edge", "fee_drag_share"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class PaperCandidateFeeSensitivityDigestReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    clear_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_stress_fee_drag: Decimal
    max_fee_drag_share: Decimal
    min_stressed_net_edge: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[PaperCandidateFeeSensitivityDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, PaperCandidateFeeSensitivityDigestReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "clear_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_stress_fee_drag",
            _normalize_nonnegative_ratio(
                "max_stress_fee_drag",
                self.max_stress_fee_drag,
            ),
        )
        for field_name in ("max_fee_drag_share", "min_stressed_net_edge"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                require_sorted=False,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)


def build_paper_candidate_fee_sensitivity_digest(
    candidates: Iterable[object],
    *,
    config: PaperCandidateFeeSensitivityDigestConfig,
    generated_at: datetime,
) -> PaperCandidateFeeSensitivityDigestReport:
    if type(config) is not PaperCandidateFeeSensitivityDigestConfig:
        raise ValueError("config must be a PaperCandidateFeeSensitivityDigestConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_candidates(candidates)
    for candidate in normalized:
        if candidate.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (
                _row_from_candidate(candidate, config=config)
                for candidate in normalized
            ),
            key=_row_sort_key,
        ),
    )
    return PaperCandidateFeeSensitivityDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count_decimal(len(rows)),
        clear_count=_status_count(rows, "clear"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        max_stress_fee_drag=max(
            (row.stress_fee_drag for row in rows),
            default=ZERO_RATIO,
        ),
        max_fee_drag_share=max(
            (row.fee_drag_share for row in rows),
            default=ZERO_RATIO,
        ),
        min_stressed_net_edge=min(
            (row.stressed_net_edge for row in rows),
            default=ZERO_RATIO,
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def paper_candidate_fee_sensitivity_digest_payload(
    report: PaperCandidateFeeSensitivityDigestReport,
) -> dict[str, object]:
    if type(report) is not PaperCandidateFeeSensitivityDigestReport:
        raise ValueError("report must be a PaperCandidateFeeSensitivityDigestReport")
    _require_hard_flags("report", report)
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "candidate_count": _decimal_payload(report.candidate_count),
        "clear_count": _decimal_payload(report.clear_count),
        "watch_count": _decimal_payload(report.watch_count),
        "blocked_count": _decimal_payload(report.blocked_count),
        "max_stress_fee_drag": _decimal_payload(report.max_stress_fee_drag),
        "max_fee_drag_share": _decimal_payload(report.max_fee_drag_share),
        "min_stressed_net_edge": _decimal_payload(report.min_stressed_net_edge),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_payload(row: PaperCandidateFeeSensitivityDigestRow) -> dict[str, object]:
    _require_hard_flags("row", row)
    return {
        "redacted_candidate_reference": row.redacted_candidate_reference,
        "market_slug": row.market_slug,
        "observed_at": row.observed_at.isoformat(),
        "base_edge": _decimal_payload(row.base_edge),
        "fee_drag": _decimal_payload(row.fee_drag),
        "stress_fee_drag": _decimal_payload(row.stress_fee_drag),
        "incremental_fee_drag": _decimal_payload(row.incremental_fee_drag),
        "total_fee_drag": _decimal_payload(row.total_fee_drag),
        "stressed_net_edge": _decimal_payload(row.stressed_net_edge),
        "fee_drag_share": _decimal_payload(row.fee_drag_share),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_from_candidate(
    candidate: PaperCandidateFeeSensitivityDigestCandidate,
    *,
    config: PaperCandidateFeeSensitivityDigestConfig,
) -> PaperCandidateFeeSensitivityDigestRow:
    incremental_fee_drag = max(
        ZERO_RATIO,
        _subtract_ratio(candidate.stress_fee_drag, candidate.fee_drag),
    )
    total_fee_drag = _sum_ratio((candidate.fee_drag, candidate.stress_fee_drag))
    stressed_net_edge = _subtract_ratio(candidate.base_edge, total_fee_drag)
    fee_drag_share = _ratio(candidate.stress_fee_drag, candidate.base_edge)
    generated_codes = _candidate_reason_codes(
        candidate=candidate,
        stressed_net_edge=stressed_net_edge,
        fee_drag_share=fee_drag_share,
        config=config,
    )
    reason_codes = _normalize_reason_codes(
        "reason_codes",
        tuple(sorted((*candidate.reason_codes, *generated_codes))),
    )
    return PaperCandidateFeeSensitivityDigestRow(
        redacted_candidate_reference=_redacted_reference(candidate.candidate_reference),
        market_slug=candidate.market_slug,
        observed_at=candidate.observed_at,
        base_edge=candidate.base_edge,
        fee_drag=candidate.fee_drag,
        stress_fee_drag=candidate.stress_fee_drag,
        incremental_fee_drag=incremental_fee_drag,
        total_fee_drag=total_fee_drag,
        stressed_net_edge=stressed_net_edge,
        fee_drag_share=fee_drag_share,
        status=_candidate_status(
            stressed_net_edge=stressed_net_edge,
            fee_drag_share=fee_drag_share,
            config=config,
        ),
        reason_codes=reason_codes,
    )


def _candidate_reason_codes(
    *,
    candidate: PaperCandidateFeeSensitivityDigestCandidate,
    stressed_net_edge: Decimal,
    fee_drag_share: Decimal,
    config: PaperCandidateFeeSensitivityDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if stressed_net_edge < config.blocked_net_edge_floor:
        reason_codes.append(NEGATIVE_STRESSED_EDGE_REASON_CODE)
    elif stressed_net_edge <= config.watch_net_edge_floor:
        reason_codes.append(NET_EDGE_BELOW_CLEAR_REASON_CODE)
    if fee_drag_share >= config.watch_fee_drag_share:
        reason_codes.append(FEE_DRAG_SHARE_ELEVATED_REASON_CODE)
    if candidate.fee_drag > ZERO_RATIO:
        reason_codes.append(BASE_DRAG_REASON_CODE)
    if candidate.stress_fee_drag > ZERO_RATIO:
        reason_codes.append(STRESS_DRAG_REASON_CODE)
    status_codes = {
        NEGATIVE_STRESSED_EDGE_REASON_CODE,
        NET_EDGE_BELOW_CLEAR_REASON_CODE,
        FEE_DRAG_SHARE_ELEVATED_REASON_CODE,
    }
    if not any(code in status_codes for code in reason_codes):
        reason_codes.append(CLEAR_REASON_CODE)
    return tuple(reason_codes)


def _candidate_status(
    *,
    stressed_net_edge: Decimal,
    fee_drag_share: Decimal,
    config: PaperCandidateFeeSensitivityDigestConfig,
) -> str:
    if (
        stressed_net_edge < config.blocked_net_edge_floor
        or fee_drag_share >= config.blocked_fee_drag_share
    ):
        return "blocked"
    if (
        stressed_net_edge <= config.watch_net_edge_floor
        or fee_drag_share >= config.watch_fee_drag_share
    ):
        return "watch"
    return "clear"


def _report_status(rows: tuple[PaperCandidateFeeSensitivityDigestRow, ...]) -> str:
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "clear"


def _report_reason_codes(
    rows: tuple[PaperCandidateFeeSensitivityDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    observed = {code for row in rows for code in row.reason_codes}
    if any(row.status in {"blocked", "watch"} for row in rows):
        observed.discard(CLEAR_REASON_CODE)
    if any(
        row.status == "blocked"
        and NET_EDGE_BELOW_CLEAR_REASON_CODE in row.reason_codes
        for row in rows
    ):
        observed.add(NET_EDGE_BELOW_WATCH_REASON_CODE)
    if any(row.stressed_net_edge < ZERO_RATIO for row in rows):
        observed.add(NET_EDGE_BELOW_WATCH_REASON_CODE)
    return tuple(code for code in REPORT_REASON_PRIORITY if code in observed)


def _row_sort_key(row: PaperCandidateFeeSensitivityDigestRow) -> tuple[object, ...]:
    return (
        STATUS_RANK[row.status],
        row.stressed_net_edge,
        -row.total_fee_drag,
        row.market_slug,
        row.redacted_candidate_reference,
    )


def _normalize_candidates(
    candidates: Iterable[object],
) -> tuple[PaperCandidateFeeSensitivityDigestCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        normalized = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen_references: set[str] = set()
    for candidate in normalized:
        if type(candidate) is not PaperCandidateFeeSensitivityDigestCandidate:
            raise ValueError(
                "candidates must contain PaperCandidateFeeSensitivityDigestCandidate values",
            )
        _require_hard_flags("candidate", candidate)
        if candidate.candidate_reference in seen_references:
            raise ValueError("duplicate candidate_reference")
        seen_references.add(candidate.candidate_reference)
    return normalized


def _normalize_rows(
    rows: Iterable[object],
) -> tuple[PaperCandidateFeeSensitivityDigestRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not PaperCandidateFeeSensitivityDigestRow:
            raise ValueError("rows must contain PaperCandidateFeeSensitivityDigestRow values")
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return normalized


def _validate_config(config: PaperCandidateFeeSensitivityDigestConfig) -> None:
    if config.blocked_net_edge_floor > config.watch_net_edge_floor:
        raise ValueError("blocked_net_edge_floor must not exceed watch_net_edge_floor")
    if config.watch_fee_drag_share > config.blocked_fee_drag_share:
        raise ValueError("watch_fee_drag_share must not exceed blocked_fee_drag_share")


def _validate_row(row: PaperCandidateFeeSensitivityDigestRow) -> None:
    expected_incremental = max(
        ZERO_RATIO,
        _subtract_ratio(row.stress_fee_drag, row.fee_drag),
    )
    if row.incremental_fee_drag != expected_incremental:
        raise ValueError("incremental_fee_drag must match stress and base fee drags")
    if row.total_fee_drag != _sum_ratio((row.fee_drag, row.stress_fee_drag)):
        raise ValueError("total_fee_drag must match fee drags")
    if row.stressed_net_edge != _subtract_ratio(row.base_edge, row.total_fee_drag):
        raise ValueError("stressed_net_edge must match base edge and total fee drag")
    if row.fee_drag_share != _ratio(row.stress_fee_drag, row.base_edge):
        raise ValueError("fee_drag_share must match stress fee drag and base edge")


def _validate_report(report: PaperCandidateFeeSensitivityDigestReport) -> None:
    if report.candidate_count != _count_decimal(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.clear_count != _status_count(report.rows, "clear"):
        raise ValueError("clear_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.max_stress_fee_drag != max(
        (row.stress_fee_drag for row in report.rows),
        default=ZERO_RATIO,
    ):
        raise ValueError("max_stress_fee_drag must match rows")
    if report.max_fee_drag_share != max(
        (row.fee_drag_share for row in report.rows),
        default=ZERO_RATIO,
    ):
        raise ValueError("max_fee_drag_share must match rows")
    if report.min_stressed_net_edge != min(
        (row.stressed_net_edge for row in report.rows),
        default=ZERO_RATIO,
    ):
        raise ValueError("min_stressed_net_edge must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _status_count(
    rows: tuple[PaperCandidateFeeSensitivityDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _sum_ratio(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO_RATIO
    for value in values:
        total = _add_ratio(total, value)
    return total


def _add_ratio(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left + right).quantize(RATIO_QUANTUM)


def _subtract_ratio(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left - right).quantize(RATIO_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_RATIO:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _count_decimal(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized != normalized.quantize(COUNT_QUANTUM):
        raise ValueError(f"{field_name} must be a whole Decimal")
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_nonnegative_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_ratio(field_name, value)
    if normalized < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    return _normalize_decimal(field_name, value).quantize(RATIO_QUANTUM)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return +value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    require_sorted: bool = True,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    for reason_code in normalized:
        _require_canonical_string(field_name, reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if require_sorted and normalized != tuple(sorted(normalized)):
        raise ValueError(f"{field_name} must be sorted")
    return normalized


def _redacted_reference(value: str) -> str:
    digest = sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"candidate_ref_{digest}"


def _require_redacted_reference(value: str) -> None:
    if not value.startswith("candidate_ref_"):
        raise ValueError("redacted_candidate_reference must be redacted")


def _decimal_payload(value: Decimal) -> str:
    return format(value, "f")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be one of {members}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")
