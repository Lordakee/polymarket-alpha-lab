"""Report-only authority-claim memory router research snapshot."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_STRATEGY_AUTHORITY_CLAIM_MEMORY_ROUTER_REPORT_VERSION = (
    "research-strategy-authority-claim-memory-router-report"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATES = frozenset(("pass", "watch", "block"))
_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TERMS = (
    "auth",
    "buy",
    "candidate",
    "database",
    "db",
    "dsn",
    "live",
    "market",
    "network",
    "order",
    "persist",
    "recommendation",
    "sell",
    "signing",
    "sizing",
    "source",
    "table",
    "text",
    "token",
    "trade",
    "trading",
    "url",
    "wallet",
)
_REASON_SEQUENCE = (
    "authority_memory_route_pass",
    "authority_memory_route_watch",
    "authority_memory_route_block",
    "authority_weak",
    "memory_weak",
    "contradiction_high",
    "freshness_weak",
    "empty_claims",
)


@dataclass(frozen=True)
class AuthorityClaimMemoryRouterConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_AUTHORITY_CLAIM_MEMORY_ROUTER_REPORT_VERSION
    )
    min_pass_score: Decimal = Decimal("0.700000")
    min_watch_score: Decimal = Decimal("0.350000")
    authority_weight: Decimal = Decimal("0.400000")
    memory_weight: Decimal = Decimal("0.350000")
    freshness_weight: Decimal = Decimal("0.250000")
    contradiction_drag: Decimal = Decimal("0.550000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not AuthorityClaimMemoryRouterConfig:
            raise TypeError("AuthorityClaimMemoryRouterConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not AuthorityClaimMemoryRouterConfig:
            raise ValueError("config must be exactly AuthorityClaimMemoryRouterConfig")
        _require_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_AUTHORITY_CLAIM_MEMORY_ROUTER_REPORT_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_score",
            "min_watch_score",
            "authority_weight",
            "memory_weight",
            "freshness_weight",
            "contradiction_drag",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_score > self.min_pass_score:
            raise ValueError("min_watch_score must not exceed min_pass_score")
        _require_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class AuthorityClaimMemoryRouterInput:
    claim_ref: str
    observed_at: datetime
    authority_score: Decimal
    memory_match_score: Decimal
    contradiction_score: Decimal
    freshness_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not AuthorityClaimMemoryRouterInput:
            raise TypeError("AuthorityClaimMemoryRouterInput does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not AuthorityClaimMemoryRouterInput:
            raise ValueError("input must be exactly AuthorityClaimMemoryRouterInput")
        _require_claim_ref("claim_ref", self.claim_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "authority_score",
            "memory_match_score",
            "contradiction_score",
            "freshness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_flags("input", self)


@dataclass(frozen=True)
class PublicPayloadMemo:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PublicPayloadMemo:
            raise TypeError("PublicPayloadMemo does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not PublicPayloadMemo:
            raise ValueError("memo must be exactly PublicPayloadMemo")
        _require_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_value("value", self.value))
        _require_flags("memo", self)
        _reject_unsafe_public_payload("memo", self)


@dataclass(frozen=True)
class AuthorityClaimMemoryRouterRow:
    claim_digest: str
    observed_at: datetime
    authority_score: Decimal
    memory_match_score: Decimal
    contradiction_score: Decimal
    freshness_score: Decimal
    router_score: Decimal
    state: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not AuthorityClaimMemoryRouterRow:
            raise TypeError("AuthorityClaimMemoryRouterRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not AuthorityClaimMemoryRouterRow:
            raise ValueError("row must be exactly AuthorityClaimMemoryRouterRow")
        _require_digest("claim_digest", self.claim_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "authority_score",
            "memory_match_score",
            "contradiction_score",
            "freshness_score",
            "router_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_state("state", self.state)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class AuthorityClaimMemoryRouterReport:
    generated_at: datetime
    config_version: str
    state: str
    claim_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_router_score: Decimal
    max_contradiction_score: Decimal
    rows: tuple[AuthorityClaimMemoryRouterRow, ...]
    reason_codes: tuple[str, ...]
    public_memos: tuple[PublicPayloadMemo, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not AuthorityClaimMemoryRouterReport:
            raise TypeError("AuthorityClaimMemoryRouterReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not AuthorityClaimMemoryRouterReport:
            raise ValueError("report must be exactly AuthorityClaimMemoryRouterReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_AUTHORITY_CLAIM_MEMORY_ROUTER_REPORT_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_state("state", self.state)
        for field_name in ("claim_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_router_score", "max_contradiction_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "public_memos", _normalize_memos(self.public_memos))
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "AuthorityClaimMemoryRouterReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_strategy_authority_claim_memory_router_report(
    claims: Sequence[AuthorityClaimMemoryRouterInput],
    *,
    generated_at: datetime,
    config: AuthorityClaimMemoryRouterConfig | None = None,
    public_memos: Sequence[PublicPayloadMemo] = (),
) -> AuthorityClaimMemoryRouterReport:
    """Build a local report-only authority claim memory router snapshot."""

    if config is None:
        config = AuthorityClaimMemoryRouterConfig()
    if type(config) is not AuthorityClaimMemoryRouterConfig:
        raise ValueError("config must be an AuthorityClaimMemoryRouterConfig")
    generated_at = _as_utc("generated_at", generated_at)
    normalized_claims = _normalize_claims(claims)
    for claim in normalized_claims:
        if claim.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = _normalize_rows(
        tuple(_row_for_claim(claim, config) for claim in normalized_claims),
    )
    memos = _normalize_memos(public_memos)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "state": _report_state(rows),
        "claim_count": _decimal_count(len(rows)),
        "pass_count": _state_count(rows, "pass"),
        "watch_count": _state_count(rows, "watch"),
        "block_count": _state_count(rows, "block"),
        "average_router_score": _average(tuple(row.router_score for row in rows)),
        "max_contradiction_score": max(
            (row.contradiction_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "public_memos": memos,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return AuthorityClaimMemoryRouterReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _row_for_claim(
    claim: AuthorityClaimMemoryRouterInput,
    config: AuthorityClaimMemoryRouterConfig,
) -> AuthorityClaimMemoryRouterRow:
    router_score = _router_score(claim, config)
    state = _row_state(router_score, config)
    return AuthorityClaimMemoryRouterRow(
        claim_digest=_claim_digest(claim.claim_ref),
        observed_at=claim.observed_at,
        authority_score=claim.authority_score,
        memory_match_score=claim.memory_match_score,
        contradiction_score=claim.contradiction_score,
        freshness_score=claim.freshness_score,
        router_score=router_score,
        state=state,
        reason_codes=_row_reason_codes(claim, state),
    )


def _router_score(
    claim: AuthorityClaimMemoryRouterInput,
    config: AuthorityClaimMemoryRouterConfig,
) -> Decimal:
    score = (
        claim.authority_score * config.authority_weight
        + claim.memory_match_score * config.memory_weight
        + claim.freshness_score * config.freshness_weight
        - claim.contradiction_score * config.contradiction_drag
    )
    return _clamp_ratio(score)


def _row_state(
    router_score: Decimal,
    config: AuthorityClaimMemoryRouterConfig,
) -> str:
    if router_score >= config.min_pass_score:
        return "pass"
    if router_score >= config.min_watch_score:
        return "watch"
    return "block"


def _row_reason_codes(
    claim: AuthorityClaimMemoryRouterInput,
    state: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if state == "pass":
        reason_codes.append("authority_memory_route_pass")
    elif state == "watch":
        reason_codes.append("authority_memory_route_watch")
    else:
        reason_codes.append("authority_memory_route_block")
    if claim.authority_score < Decimal("0.500000"):
        reason_codes.append("authority_weak")
    if claim.memory_match_score < Decimal("0.500000"):
        reason_codes.append("memory_weak")
    if claim.contradiction_score > Decimal("0.500000"):
        reason_codes.append("contradiction_high")
    if claim.freshness_score < Decimal("0.500000"):
        reason_codes.append("freshness_weak")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_state(rows: tuple[AuthorityClaimMemoryRouterRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.state == "block" for row in rows):
        return "block"
    if any(row.state == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[AuthorityClaimMemoryRouterRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_claims",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _state_count(rows: tuple[AuthorityClaimMemoryRouterRow, ...], state: str) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.state == state))


def _validate_row_consistency(row: AuthorityClaimMemoryRouterRow) -> None:
    if row.state == "pass" and "authority_memory_route_pass" not in row.reason_codes:
        raise ValueError("pass rows must include authority_memory_route_pass")
    if row.state == "watch" and "authority_memory_route_watch" not in row.reason_codes:
        raise ValueError("watch rows must include authority_memory_route_watch")
    if row.state == "block" and "authority_memory_route_block" not in row.reason_codes:
        raise ValueError("block rows must include authority_memory_route_block")


def _validate_report_consistency(report: AuthorityClaimMemoryRouterReport) -> None:
    if report.claim_count != _decimal_count(len(report.rows)):
        raise ValueError("claim_count must match rows")
    if report.pass_count != _state_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _state_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _state_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_router_score != _average(tuple(row.router_score for row in report.rows)):
        raise ValueError("average_router_score must match rows")
    if report.max_contradiction_score != max(
        (row.contradiction_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_contradiction_score must match rows")
    if report.state != _report_state(report.rows):
        raise ValueError("state must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_claims(
    claims: Sequence[AuthorityClaimMemoryRouterInput],
) -> tuple[AuthorityClaimMemoryRouterInput, ...]:
    if isinstance(claims, (str, bytes)) or not isinstance(claims, Sequence):
        raise ValueError("claims must be a sequence")
    normalized: list[AuthorityClaimMemoryRouterInput] = []
    seen: set[str] = set()
    for claim in claims:
        if type(claim) is not AuthorityClaimMemoryRouterInput:
            raise ValueError("claims must contain AuthorityClaimMemoryRouterInput")
        if claim.claim_ref in seen:
            raise ValueError("claim_ref values must be unique")
        seen.add(claim.claim_ref)
        normalized.append(claim)
    return tuple(sorted(normalized, key=lambda item: item.claim_ref))


def _normalize_rows(
    rows: Sequence[AuthorityClaimMemoryRouterRow],
) -> tuple[AuthorityClaimMemoryRouterRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[AuthorityClaimMemoryRouterRow] = []
    for row in rows:
        if type(row) is not AuthorityClaimMemoryRouterRow:
            raise ValueError("rows must contain AuthorityClaimMemoryRouterRow")
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.claim_digest))


def _normalize_memos(memos: Sequence[PublicPayloadMemo]) -> tuple[PublicPayloadMemo, ...]:
    if isinstance(memos, (str, bytes)) or not isinstance(memos, Sequence):
        raise ValueError("public_memos must be a sequence")
    normalized: list[PublicPayloadMemo] = []
    for memo in memos:
        if type(memo) is not PublicPayloadMemo:
            raise ValueError("public_memos must contain PublicPayloadMemo")
        normalized.append(memo)
    return tuple(sorted(normalized, key=lambda memo: memo.key))


def _require_flags(label: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_claim_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value or len(value) > 128:
        raise ValueError(f"{field_name} must be a non-empty stable reference")
    if "://" in value or "?" in value or "@" in value:
        raise ValueError(f"{field_name} has unsafe value")
    return value


def _require_public_value(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(_has_unsafe_public_term(lowered, term) for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_state(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_identifier("reason_code", reason_code)
        if reason_code not in _REASON_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(reason_code for reason_code in _REASON_SEQUENCE if reason_code in normalized)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _claim_digest(claim_ref: str) -> str:
    return hashlib.sha256(claim_ref.encode("utf-8")).hexdigest()


def _report_values_without_digest(report: AuthorityClaimMemoryRouterReport) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(_has_unsafe_public_term(lowered, term) for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _has_unsafe_public_term(value: str, term: str) -> bool:
    if term in {"auth", "db"}:
        return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", value) is not None
    return term in value


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_AUTHORITY_CLAIM_MEMORY_ROUTER_REPORT_VERSION",
    "AuthorityClaimMemoryRouterConfig",
    "AuthorityClaimMemoryRouterInput",
    "AuthorityClaimMemoryRouterReport",
    "AuthorityClaimMemoryRouterRow",
    "PublicPayloadMemo",
    "build_research_strategy_authority_claim_memory_router_report",
)
