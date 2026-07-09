"""Pure readonly report for source-memory claim floor checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_STRATEGY_SOURCE_MEMORY_CLAIM_FLOOR_CONFIG_VERSION = (
    "research-strategy-source-memory-claim-floor-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
PASS_REASON = "claim_floor_pass"
WATCH_REASON = "claim_floor_watch"
BLOCK_REASON = "claim_floor_block"
WATCH_MARGIN_REASON = "claim_floor_watch_margin"
MEMORY_BELOW_REASON = "memory_score_below_floor"
EMPTY_REASON = "claim_floor_empty"
STATUSES = ("pass", "watch", "block")
STATUS_RANK = {"block": "0", "watch": "1", "pass": "2"}
REASON_CODES = (
    EMPTY_REASON,
    PASS_REASON,
    WATCH_REASON,
    BLOCK_REASON,
    WATCH_MARGIN_REASON,
    MEMORY_BELOW_REASON,
)


def _surface_term(*pieces: str) -> str:
    return "".join(pieces)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _surface_term("au", "th"),
        _surface_term("wa", "llet"),
        _surface_term("or", "der"),
        _surface_term("net", "work"),
        _surface_term("data", "base"),
        _surface_term("d", "sn"),
        _surface_term("ta", "ble"),
        _surface_term("to", "ken"),
        _surface_term("se", "cret"),
        _surface_term("api", "_key"),
        _surface_term("private", "_key"),
        _surface_term("sign", "ing"),
        _surface_term("mut", "ation"),
        _surface_term("li", "ve"),
        _surface_term("tra", "ding"),
        _surface_term("si", "zing"),
        _surface_term("reco", "mmendation"),
        _surface_term("ur", "l"),
        _surface_term("te", "xt"),
    ),
)


@dataclass(frozen=True)
class ResearchStrategySourceMemoryClaimFloorConfig:
    config_version: str = DEFAULT_RESEARCH_STRATEGY_SOURCE_MEMORY_CLAIM_FLOOR_CONFIG_VERSION
    claim_floor_score: Decimal = Decimal("0.600000")
    watch_margin: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "claim_floor_score",
            _require_ratio("claim_floor_score", self.claim_floor_score),
        )
        object.__setattr__(
            self,
            "watch_margin",
            _require_nonnegative_decimal("watch_margin", self.watch_margin),
        )
        if self.claim_floor_score + self.watch_margin > ONE:
            raise ValueError("watch_margin must keep the watch ceiling at or below one")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategySourceMemoryClaimFloorClaim:
    candidate_ref: str
    market_ref: str
    source_locator: str
    claim_text: str
    memory_score: Decimal
    claim_support_score: Decimal
    source_independence_score: Decimal
    source_recency_score: Decimal
    contradiction_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "candidate_ref",
            "market_ref",
            "source_locator",
            "claim_text",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_private_string(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "memory_score",
            "claim_support_score",
            "source_independence_score",
            "source_recency_score",
            "contradiction_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("claim", self)


@dataclass(frozen=True)
class ResearchStrategySourceMemoryClaimFloorRow:
    claim_ref_digest: str
    market_ref_digest: str
    source_ref_digest: str
    claim_body_digest: str
    memory_score: Decimal
    claim_support_score: Decimal
    source_independence_score: Decimal
    source_recency_score: Decimal
    contradiction_score: Decimal
    claim_floor_score: Decimal
    floor_delta: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "claim_ref_digest",
            "market_ref_digest",
            "source_ref_digest",
            "claim_body_digest",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_digest(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "memory_score",
            "claim_support_score",
            "source_independence_score",
            "source_recency_score",
            "contradiction_score",
            "claim_floor_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "floor_delta",
            _require_decimal("floor_delta", self.floor_delta),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.status != _row_status_from_reasons(self.reason_codes):
            raise ValueError("status is inconsistent with reason_codes")
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchStrategySourceMemoryClaimFloorReport:
    generated_at: datetime
    config_version: str
    claim_floor_score: Decimal
    watch_margin: Decimal
    claim_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategySourceMemoryClaimFloorRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "claim_floor_score",
            _require_ratio("claim_floor_score", self.claim_floor_score),
        )
        object.__setattr__(
            self,
            "watch_margin",
            _require_nonnegative_decimal("watch_margin", self.watch_margin),
        )
        for field_name in ("claim_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report(self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest does not match public payload")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        _require_digest("derived_validation_digest", self.derived_validation_digest)


def build_research_strategy_source_memory_claim_floor_report(
    claims: object,
    *,
    config: ResearchStrategySourceMemoryClaimFloorConfig,
    generated_at: datetime,
) -> ResearchStrategySourceMemoryClaimFloorReport:
    if type(config) is not ResearchStrategySourceMemoryClaimFloorConfig:
        raise ValueError("config must be a ResearchStrategySourceMemoryClaimFloorConfig")
    _require_hard_flags("config", config)
    rows = tuple(
        sorted(
            (
                _row_from_claim(claim, config=config)
                for claim in _normalize_claims(claims)
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchStrategySourceMemoryClaimFloorReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        claim_floor_score=config.claim_floor_score,
        watch_margin=config.watch_margin,
        claim_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_strategy_source_memory_claim_floor_report_payload(
    report: ResearchStrategySourceMemoryClaimFloorReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategySourceMemoryClaimFloorReport:
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchStrategySourceMemoryClaimFloorReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_strategy_source_memory_claim_floor_public_payload(payload)
    return payload


def validate_research_strategy_source_memory_claim_floor_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _require_hard_flags("public payload", _PayloadFlags(payload))
    _reject_public_numerics(payload)
    _reject_unsafe_public_surface("public payload", payload)
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    expected_digest = _digest_payload(unsigned_payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")


def _row_from_claim(
    claim: ResearchStrategySourceMemoryClaimFloorClaim,
    *,
    config: ResearchStrategySourceMemoryClaimFloorConfig,
) -> ResearchStrategySourceMemoryClaimFloorRow:
    if type(claim) is not ResearchStrategySourceMemoryClaimFloorClaim:
        raise ValueError("claim must be a ResearchStrategySourceMemoryClaimFloorClaim")
    _require_hard_flags("claim", claim)
    floor_score = min(
        claim.memory_score,
        claim.claim_support_score,
        claim.source_independence_score,
        claim.source_recency_score,
    )
    delta = _require_decimal("floor_delta", floor_score - config.claim_floor_score)
    status = _row_status(floor_score, config)
    return ResearchStrategySourceMemoryClaimFloorRow(
        claim_ref_digest=_private_digest(claim.candidate_ref),
        market_ref_digest=_private_digest(claim.market_ref),
        source_ref_digest=_private_digest(claim.source_locator),
        claim_body_digest=_private_digest(claim.claim_text),
        memory_score=claim.memory_score,
        claim_support_score=claim.claim_support_score,
        source_independence_score=claim.source_independence_score,
        source_recency_score=claim.source_recency_score,
        contradiction_score=claim.contradiction_score,
        claim_floor_score=floor_score,
        floor_delta=delta,
        status=status,
        reason_codes=_row_reason_codes(claim, status=status, floor_score=floor_score),
    )


def _row_status(
    floor_score: Decimal,
    config: ResearchStrategySourceMemoryClaimFloorConfig,
) -> str:
    if floor_score < config.claim_floor_score:
        return "block"
    if floor_score <= config.claim_floor_score + config.watch_margin:
        return "watch"
    return "pass"


def _row_reason_codes(
    claim: ResearchStrategySourceMemoryClaimFloorClaim,
    *,
    status: str,
    floor_score: Decimal,
) -> tuple[str, ...]:
    if status == "pass":
        return (PASS_REASON,)
    if status == "watch":
        return (WATCH_REASON, WATCH_MARGIN_REASON)
    reasons = [BLOCK_REASON]
    if floor_score == claim.memory_score:
        reasons.append(MEMORY_BELOW_REASON)
    return tuple(reasons)


def _row_status_from_reasons(reason_codes: tuple[str, ...]) -> str:
    if BLOCK_REASON in reason_codes:
        return "block"
    if WATCH_REASON in reason_codes:
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchStrategySourceMemoryClaimFloorRow, ...],
) -> str:
    if not rows:
        return "watch"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategySourceMemoryClaimFloorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    found = tuple(dict.fromkeys(reason for row in rows for reason in row.reason_codes))
    return tuple(reason for reason in REASON_CODES if reason in found)


def _status_count(
    rows: tuple[ResearchStrategySourceMemoryClaimFloorRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _row_sort_key(row: ResearchStrategySourceMemoryClaimFloorRow) -> tuple[str, str]:
    return (STATUS_RANK[row.status], row.claim_ref_digest)


def _normalize_claims(
    claims: object,
) -> tuple[ResearchStrategySourceMemoryClaimFloorClaim, ...]:
    if isinstance(claims, (str, bytes)):
        raise ValueError("claims must be an iterable")
    try:
        items = tuple(claims)
    except TypeError as exc:
        raise ValueError("claims must be an iterable") from exc
    for claim in items:
        if type(claim) is not ResearchStrategySourceMemoryClaimFloorClaim:
            raise ValueError("claims must contain ResearchStrategySourceMemoryClaimFloorClaim")
        _require_hard_flags("claim", claim)
    return items


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategySourceMemoryClaimFloorRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in items:
        if type(row) is not ResearchStrategySourceMemoryClaimFloorRow:
            raise ValueError("rows must contain ResearchStrategySourceMemoryClaimFloorRow")
        _require_hard_flags("row", row)
    return items


def _validate_report(report: ResearchStrategySourceMemoryClaimFloorReport) -> None:
    rows = report.rows
    expected = {
        "claim_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
    }
    for field_name, value in expected.items():
        if getattr(report, field_name) != value:
            raise ValueError(f"{field_name} is inconsistent with rows")


def _report_digest(report: ResearchStrategySourceMemoryClaimFloorReport) -> str:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _digest_payload(payload)


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _private_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class _PayloadFlags:
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


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_private_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    value = _require_private_string(field_name, value)
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public value")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_status(field_name: str, value: object) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_reason_codes(field_name: str, reason_codes: object) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        if type(reason_code) is not str:
            raise ValueError(f"{field_name} entries must be strings")
        if reason_code not in REASON_CODES:
            raise ValueError(f"{field_name} contains an unknown value")
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in normalized)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_count(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exact")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
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


def _reject_public_numerics(value: object) -> None:
    if isinstance(value, float) or type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_surface(label, item)


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_SOURCE_MEMORY_CLAIM_FLOOR_CONFIG_VERSION",
    "ResearchStrategySourceMemoryClaimFloorClaim",
    "ResearchStrategySourceMemoryClaimFloorConfig",
    "ResearchStrategySourceMemoryClaimFloorReport",
    "ResearchStrategySourceMemoryClaimFloorRow",
    "build_research_strategy_source_memory_claim_floor_report",
    "research_strategy_source_memory_claim_floor_report_payload",
    "validate_research_strategy_source_memory_claim_floor_public_payload",
)
