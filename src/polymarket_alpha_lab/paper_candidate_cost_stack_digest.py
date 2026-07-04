"""Paper-only candidate cost stack digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256


__all__ = (
    "DEFAULT_PAPER_CANDIDATE_COST_STACK_DIGEST_CONFIG_VERSION",
    "PaperCandidateCostStackDigestCandidate",
    "PaperCandidateCostStackDigestConfig",
    "PaperCandidateCostStackDigestReport",
    "PaperCandidateCostStackDigestRow",
    "build_paper_candidate_cost_stack_digest",
    "paper_candidate_cost_stack_digest_payload",
)


DEFAULT_PAPER_CANDIDATE_COST_STACK_DIGEST_CONFIG_VERSION = (
    "paper-candidate-cost-stack-digest-v0"
)

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
DECIMAL_CONTEXT = Context(prec=64)

ROW_STATUSES = ("pass", "watch", "blocked")
REPORT_STATUSES = ("pass", "watch", "blocked")
ROW_STATUS_SORT_PRIORITY = {"blocked": 0, "watch": 1, "pass": 2}

EMPTY_REASON_CODE = "cost_stack_digest_empty"
PASS_REASON_CODE = "cost_stack_passed"
WATCH_REASON_CODE = "cost_stack_watch"
BLOCKED_REASON_CODE = "cost_stack_blocked"
CASH_DRAG_REASON_CODE = "cash_drag_cost_present"
FEE_REASON_CODE = "fee_cost_present"
GAS_REASON_CODE = "gas_cost_present"
SETTLEMENT_REASON_CODE = "settlement_cost_present"
SLIPPAGE_REASON_CODE = "slippage_cost_present"
SPREAD_REASON_CODE = "spread_cost_present"
REPORT_REASON_PRIORITY = (
    BLOCKED_REASON_CODE,
    PASS_REASON_CODE,
    WATCH_REASON_CODE,
    CASH_DRAG_REASON_CODE,
    FEE_REASON_CODE,
    GAS_REASON_CODE,
    SETTLEMENT_REASON_CODE,
    SLIPPAGE_REASON_CODE,
    SPREAD_REASON_CODE,
    EMPTY_REASON_CODE,
)
SENSITIVE_REFERENCE_TOKENS = (
    "secret",
    "tok" "en",
    "private",
    "key",
    "bearer",
    "dsn",
    "password",
    "wal" "let",
)
SENSITIVE_VALUE_FRAGMENTS = (
    "api" "_" "key",
    "bear" "er",
    "dsn",
    "password",
    "private" "-" "key",
    "private" "_" "key",
    "secret",
    "sk_",
    "tok" "en",
    "wal" "let",
)
UNSAFE_FIELD_FRAGMENTS = (
    "au" "th",
    "private" "_" "key",
    "exchange_mutation",
    "bro" "ker",
    "can" "cel",
    "li" "ve",
    "or" "der",
    "re" "place",
    "si" "gn",
    "tra" "de",
    "wal" "let",
)


@dataclass(frozen=True)
class PaperCandidateCostStackDigestConfig:
    config_version: str = DEFAULT_PAPER_CANDIDATE_COST_STACK_DIGEST_CONFIG_VERSION
    watch_net_probability_edge: Decimal = Decimal("0.030000")
    max_pass_cost_to_edge_ratio: Decimal = Decimal("0.500000")
    max_watch_cost_to_edge_ratio: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_net_probability_edge",
            "max_pass_cost_to_edge_ratio",
            "max_watch_cost_to_edge_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_safety_flags("config", self)


@dataclass(frozen=True)
class PaperCandidateCostStackDigestCandidate:
    candidate_reference: str
    market_slug: str
    observed_at: datetime
    expected_probability_edge: Decimal
    fee_probability_cost: Decimal
    spread_probability_cost: Decimal
    slippage_probability_cost: Decimal
    gas_probability_cost: Decimal
    settlement_probability_cost: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_reference", self.candidate_reference)
        _require_canonical_string("market_slug", self.market_slug)
        _reject_sensitive_value("market_slug", self.market_slug)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "expected_probability_edge",
            _normalize_decimal(
                "expected_probability_edge",
                self.expected_probability_edge,
            ),
        )
        for field_name in (
            "fee_probability_cost",
            "spread_probability_cost",
            "slippage_probability_cost",
            "gas_probability_cost",
            "settlement_probability_cost",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        for reason_code in self.reason_codes:
            _reject_sensitive_value("reason_codes", reason_code)
        _require_safety_flags("candidate", self)


@dataclass(frozen=True)
class PaperCandidateCostStackDigestRow:
    redacted_candidate_reference: str
    market_slug: str
    observed_at: datetime
    expected_probability_edge: Decimal
    fee_probability_cost: Decimal
    spread_probability_cost: Decimal
    slippage_probability_cost: Decimal
    gas_probability_cost: Decimal
    settlement_probability_cost: Decimal
    total_probability_cost: Decimal
    net_probability_edge: Decimal
    cost_to_edge_ratio: Decimal
    edge_shortfall: Decimal
    cost_stack_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string(
            "redacted_candidate_reference",
            self.redacted_candidate_reference,
        )
        _require_redacted_reference(self.redacted_candidate_reference)
        _require_canonical_string("market_slug", self.market_slug)
        _reject_sensitive_value("market_slug", self.market_slug)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "expected_probability_edge",
            "net_probability_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fee_probability_cost",
            "spread_probability_cost",
            "slippage_probability_cost",
            "gas_probability_cost",
            "settlement_probability_cost",
            "total_probability_cost",
            "cost_to_edge_ratio",
            "edge_shortfall",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("cost_stack_status", self.cost_stack_status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        for reason_code in self.reason_codes:
            _reject_sensitive_value("reason_codes", reason_code)
        _validate_row(self)
        _require_safety_flags("row", self)


@dataclass(frozen=True)
class PaperCandidateCostStackDigestReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    total_probability_cost: Decimal
    max_total_probability_cost: Decimal
    min_net_probability_edge: Decimal
    max_cost_to_edge_ratio: Decimal
    max_edge_shortfall: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[PaperCandidateCostStackDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_probability_cost",
            "max_total_probability_cost",
            "min_net_probability_edge",
            "max_cost_to_edge_ratio",
            "max_edge_shortfall",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_safety_flags("report", self)


def build_paper_candidate_cost_stack_digest(
    candidates: Iterable[object],
    *,
    config: PaperCandidateCostStackDigestConfig,
    generated_at: datetime,
) -> PaperCandidateCostStackDigestReport:
    if type(config) is not PaperCandidateCostStackDigestConfig:
        raise ValueError("config must be a PaperCandidateCostStackDigestConfig")
    _require_safety_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    for candidate in normalized_candidates:
        if candidate.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (
                _row_from_candidate(candidate, config=config)
                for candidate in normalized_candidates
            ),
            key=_row_sort_key,
        ),
    )
    return PaperCandidateCostStackDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        total_probability_cost=_sum_decimal(rows, "total_probability_cost"),
        max_total_probability_cost=max(
            (row.total_probability_cost for row in rows),
            default=ZERO,
        ),
        min_net_probability_edge=min(
            (row.net_probability_edge for row in rows),
            default=ZERO,
        ),
        max_cost_to_edge_ratio=max(
            (row.cost_to_edge_ratio for row in rows),
            default=ZERO,
        ),
        max_edge_shortfall=max(
            (row.edge_shortfall for row in rows),
            default=ZERO,
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def paper_candidate_cost_stack_digest_payload(
    report: PaperCandidateCostStackDigestReport,
) -> dict[str, object]:
    if type(report) is not PaperCandidateCostStackDigestReport:
        raise ValueError("report must be a PaperCandidateCostStackDigestReport")
    _require_safety_flags("report", report)
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "candidate_count": _count_payload(report.candidate_count),
        "pass_count": _count_payload(report.pass_count),
        "watch_count": _count_payload(report.watch_count),
        "blocked_count": _count_payload(report.blocked_count),
        "total_probability_cost": _decimal_payload(report.total_probability_cost),
        "max_total_probability_cost": _decimal_payload(
            report.max_total_probability_cost,
        ),
        "min_net_probability_edge": _decimal_payload(report.min_net_probability_edge),
        "max_cost_to_edge_ratio": _decimal_payload(report.max_cost_to_edge_ratio),
        "max_edge_shortfall": _decimal_payload(report.max_edge_shortfall),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_payload(row: PaperCandidateCostStackDigestRow) -> dict[str, object]:
    _require_safety_flags("row", row)
    return {
        "redacted_candidate_reference": row.redacted_candidate_reference,
        "market_slug": row.market_slug,
        "observed_at": row.observed_at.isoformat(),
        "expected_probability_edge": _decimal_payload(row.expected_probability_edge),
        "fee_probability_cost": _decimal_payload(row.fee_probability_cost),
        "spread_probability_cost": _decimal_payload(row.spread_probability_cost),
        "slippage_probability_cost": _decimal_payload(row.slippage_probability_cost),
        "gas_probability_cost": _decimal_payload(row.gas_probability_cost),
        "settlement_probability_cost": _decimal_payload(
            row.settlement_probability_cost,
        ),
        "total_probability_cost": _decimal_payload(row.total_probability_cost),
        "net_probability_edge": _decimal_payload(row.net_probability_edge),
        "cost_to_edge_ratio": _decimal_payload(row.cost_to_edge_ratio),
        "edge_shortfall": _decimal_payload(row.edge_shortfall),
        "cost_stack_status": row.cost_stack_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_from_candidate(
    candidate: PaperCandidateCostStackDigestCandidate,
    *,
    config: PaperCandidateCostStackDigestConfig,
) -> PaperCandidateCostStackDigestRow:
    total_probability_cost = _add_decimal(
        candidate.fee_probability_cost,
        candidate.spread_probability_cost,
        candidate.slippage_probability_cost,
        candidate.gas_probability_cost,
        candidate.settlement_probability_cost,
    )
    net_probability_edge = _subtract_decimal(
        candidate.expected_probability_edge,
        total_probability_cost,
    )
    cost_to_edge_ratio = _ratio(
        total_probability_cost,
        candidate.expected_probability_edge,
    )
    edge_shortfall = _max_decimal(_subtract_decimal(ZERO, net_probability_edge), ZERO)
    status, terminal_reason = _row_status_and_reason(
        net_probability_edge=net_probability_edge,
        cost_to_edge_ratio=cost_to_edge_ratio,
        config=config,
    )
    reason_codes = _normalize_reason_codes(
        (
            *candidate.reason_codes,
            terminal_reason,
            *_cost_reason_codes(candidate),
        ),
        require_nonempty=True,
    )
    return PaperCandidateCostStackDigestRow(
        redacted_candidate_reference=_redacted_reference(candidate.candidate_reference),
        market_slug=candidate.market_slug,
        observed_at=candidate.observed_at,
        expected_probability_edge=candidate.expected_probability_edge,
        fee_probability_cost=candidate.fee_probability_cost,
        spread_probability_cost=candidate.spread_probability_cost,
        slippage_probability_cost=candidate.slippage_probability_cost,
        gas_probability_cost=candidate.gas_probability_cost,
        settlement_probability_cost=candidate.settlement_probability_cost,
        total_probability_cost=total_probability_cost,
        net_probability_edge=net_probability_edge,
        cost_to_edge_ratio=cost_to_edge_ratio,
        edge_shortfall=edge_shortfall,
        cost_stack_status=status,
        reason_codes=reason_codes,
    )


def _row_status_and_reason(
    *,
    net_probability_edge: Decimal,
    cost_to_edge_ratio: Decimal,
    config: PaperCandidateCostStackDigestConfig,
) -> tuple[str, str]:
    if (
        net_probability_edge < ZERO
        or cost_to_edge_ratio > config.max_watch_cost_to_edge_ratio
    ):
        return "blocked", BLOCKED_REASON_CODE
    if (
        net_probability_edge <= config.watch_net_probability_edge
        or cost_to_edge_ratio > config.max_pass_cost_to_edge_ratio
    ):
        return "watch", WATCH_REASON_CODE
    return "pass", PASS_REASON_CODE


def _cost_reason_codes(
    candidate: PaperCandidateCostStackDigestCandidate,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if candidate.fee_probability_cost > ZERO:
        reason_codes.append(FEE_REASON_CODE)
    if candidate.spread_probability_cost > ZERO:
        reason_codes.append(SPREAD_REASON_CODE)
    if candidate.slippage_probability_cost > ZERO:
        reason_codes.append(SLIPPAGE_REASON_CODE)
    if candidate.gas_probability_cost > ZERO:
        reason_codes.append(GAS_REASON_CODE)
    if candidate.settlement_probability_cost > ZERO:
        reason_codes.append(SETTLEMENT_REASON_CODE)
    return tuple(reason_codes)


def _normalize_candidates(
    candidates: Iterable[object],
) -> tuple[PaperCandidateCostStackDigestCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        normalized = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen: set[str] = set()
    for candidate in normalized:
        if type(candidate) is not PaperCandidateCostStackDigestCandidate:
            raise ValueError(
                "candidates must contain PaperCandidateCostStackDigestCandidate",
            )
        _require_safety_flags("candidate", candidate)
        if candidate.candidate_reference in seen:
            raise ValueError("duplicate candidate_reference")
        seen.add(candidate.candidate_reference)
    return normalized


def _normalize_rows(rows: object) -> tuple[PaperCandidateCostStackDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not PaperCandidateCostStackDigestRow:
            raise ValueError("rows must contain PaperCandidateCostStackDigestRow")
        _require_safety_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return normalized


def _row_sort_key(
    row: PaperCandidateCostStackDigestRow,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        ROW_STATUS_SORT_PRIORITY[row.cost_stack_status],
        -row.edge_shortfall,
        -row.cost_to_edge_ratio,
        row.market_slug,
        row.redacted_candidate_reference,
    )


def _status_count(
    rows: tuple[PaperCandidateCostStackDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.cost_stack_status == status))


def _sum_decimal(
    rows: tuple[PaperCandidateCostStackDigestRow, ...],
    field_name: str,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return sum((getattr(row, field_name) for row in rows), ZERO).quantize(QUANTUM)


def _report_status(rows: tuple[PaperCandidateCostStackDigestRow, ...]) -> str:
    if any(row.cost_stack_status == "blocked" for row in rows):
        return "blocked"
    if any(row.cost_stack_status == "watch" for row in rows) or not rows:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[PaperCandidateCostStackDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    observed: set[str] = set()
    for row in rows:
        observed.update(row.reason_codes)
    return tuple(
        reason_code
        for reason_code in REPORT_REASON_PRIORITY
        if reason_code in observed
    )


def _validate_config(config: PaperCandidateCostStackDigestConfig) -> None:
    if config.max_pass_cost_to_edge_ratio > config.max_watch_cost_to_edge_ratio:
        raise ValueError(
            "max_pass_cost_to_edge_ratio must be at most max_watch_cost_to_edge_ratio",
        )


def _validate_row(row: PaperCandidateCostStackDigestRow) -> None:
    expected_total_cost = _add_decimal(
        row.fee_probability_cost,
        row.spread_probability_cost,
        row.slippage_probability_cost,
        row.gas_probability_cost,
        row.settlement_probability_cost,
    )
    if row.total_probability_cost != expected_total_cost:
        raise ValueError("total_probability_cost must match component costs")
    if row.net_probability_edge != _subtract_decimal(
        row.expected_probability_edge,
        row.total_probability_cost,
    ):
        raise ValueError("net_probability_edge must match edge less costs")
    if row.cost_to_edge_ratio != _ratio(
        row.total_probability_cost,
        row.expected_probability_edge,
    ):
        raise ValueError("cost_to_edge_ratio must match total cost and edge")
    expected_shortfall = _max_decimal(_subtract_decimal(ZERO, row.net_probability_edge), ZERO)
    if row.edge_shortfall != expected_shortfall:
        raise ValueError("edge_shortfall must match net_probability_edge")


def _validate_report(report: PaperCandidateCostStackDigestReport) -> None:
    if report.candidate_count != _count_decimal(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.total_probability_cost != _sum_decimal(report.rows, "total_probability_cost"):
        raise ValueError("total_probability_cost must match rows")
    if report.max_total_probability_cost != max(
        (row.total_probability_cost for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_total_probability_cost must match rows")
    if report.min_net_probability_edge != min(
        (row.net_probability_edge for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_net_probability_edge must match rows")
    if report.max_cost_to_edge_ratio != max(
        (row.cost_to_edge_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_cost_to_edge_ratio must match rows")
    if report.max_edge_shortfall != max(
        (row.edge_shortfall for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_edge_shortfall must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_safety_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only") is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly") is not True:
        raise ValueError(f"readonly must be True for {label}")
    _reject_unsafe_fields(label, value)


def _reject_unsafe_fields(label: str, payload: object) -> None:
    for key in _iter_keys(payload):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in UNSAFE_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe surface field in {label}: {key}")


def _iter_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_keys(asdict(value))
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_iter_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_keys(item))
        return tuple(keys)
    return ()


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be canonical text")


def _require_redacted_reference(value: str) -> None:
    lowered = value.lower()
    if any(token in lowered for token in SENSITIVE_REFERENCE_TOKENS):
        raise ValueError("redacted_candidate_reference must not expose sensitive tokens")


def _reject_sensitive_value(field_name: str, value: object) -> None:
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in SENSITIVE_VALUE_FRAGMENTS):
            raise ValueError(f"{field_name} contains sensitive material")


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a nonnegative count Decimal")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < QUANTUM.as_tuple().exponent:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _normalize_reason_codes(
    values: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes = tuple(values)
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes is required")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_canonical_reason_code("reason_codes", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    return reason_codes


def _require_canonical_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value != value.lower() or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError(f"{field_name} must contain canonical reason codes")


def _add_decimal(*values: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return sum(values, ZERO).quantize(QUANTUM)


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left - right).quantize(QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("expected_probability_edge must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _max_decimal(left: Decimal, right: Decimal) -> Decimal:
    return left if left >= right else right


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _redacted_reference(value: str) -> str:
    digest = sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"candidate_ref_{digest}"


def _decimal_payload(value: Decimal) -> str:
    return format(_normalize_decimal("payload decimal", value), "f")


def _count_payload(value: Decimal) -> str:
    return str(int(_normalize_count_decimal("payload count", value)))
