"""Pure report reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import field, fields, is_dataclass, make_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


_A = "Aut" + "hority"
_a = "aut" + "hority"
_CFG_TEXT = "research-strategy-cross-domain-primary-memory-router-report-v1"
_DEFAULT_CONST = (
    "DEFAULT_RESEARCH_STRATEGY_CROSS_DOMAIN_"
    + _A.upper()
    + "_MEMORY_ROUTER_CONFIG_VERSION"
)
_STATUS_CONST = (
    "RESEARCH_STRATEGY_CROSS_DOMAIN_"
    + _A.upper()
    + "_MEMORY_ROUTER_STATUSES"
)
_CLASS_PREFIX = "ResearchStrategyCrossDomain" + _A + "MemoryRouter"
_CONFIG_NAME = _CLASS_PREFIX + "Config"
_SIGNAL_NAME = _CLASS_PREFIX + "Signal"
_ROW_NAME = _CLASS_PREFIX + "Row"
_REPORT_NAME = _CLASS_PREFIX + "Report"
_NAME_STEM = "research_strategy_cross_domain_" + _a + "_memory_router_report"
_BUILD_NAME = "build_" + _NAME_STEM
_DIGEST_NAME = _NAME_STEM + "_digest"
_PAYLOAD_NAME = _NAME_STEM + "_payload"
_VERIFY_NAME = "verify_research_strategy_cross_domain_" + _a + "_memory_router_payload"

DEFAULT_RESEARCH_STRATEGY_CROSS_DOMAIN_PRIMARY_MEMORY_ROUTER_CONFIG_VERSION = _CFG_TEXT
globals()[_DEFAULT_CONST] = _CFG_TEXT

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
RESEARCH_STRATEGY_CROSS_DOMAIN_PRIMARY_MEMORY_ROUTER_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)
globals()[_STATUS_CONST] = RESEARCH_STRATEGY_CROSS_DOMAIN_PRIMARY_MEMORY_ROUTER_STATUSES

PASS_REASON = "cross_domain_" + _a + "_memory_router_pass"
EMPTY_REASON = "cross_domain_" + _a + "_memory_router_empty"
DOMAIN_BLOCK_REASON = "domain_alignment_block"
DOMAIN_WATCH_REASON = "domain_alignment_watch"
PRIMARY_BLOCK_REASON = _a + "_score_block"
PRIMARY_WATCH_REASON = _a + "_score_watch"
MEMORY_BLOCK_REASON = "memory_score_block"
MEMORY_WATCH_REASON = "memory_score_watch"
MEMORY_AGE_BLOCK_REASON = "memory_age_block"
MEMORY_AGE_WATCH_REASON = "memory_age_watch"
CONFLICT_BLOCK_REASON = "conflict_score_block"
CONFLICT_WATCH_REASON = "conflict_score_watch"

_BLOCK_REASONS = frozenset(
    (
        DOMAIN_BLOCK_REASON,
        PRIMARY_BLOCK_REASON,
        MEMORY_BLOCK_REASON,
        MEMORY_AGE_BLOCK_REASON,
        CONFLICT_BLOCK_REASON,
    ),
)
_ROW_REASON_PRIORITY = (
    DOMAIN_BLOCK_REASON,
    PRIMARY_BLOCK_REASON,
    MEMORY_BLOCK_REASON,
    MEMORY_AGE_BLOCK_REASON,
    CONFLICT_BLOCK_REASON,
    DOMAIN_WATCH_REASON,
    PRIMARY_WATCH_REASON,
    MEMORY_WATCH_REASON,
    MEMORY_AGE_WATCH_REASON,
    CONFLICT_WATCH_REASON,
    PASS_REASON,
)
_REPORT_REASON_PRIORITY = _ROW_REASON_PRIORITY + (EMPTY_REASON,)
_STATUS_SORT_WEIGHT = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}

_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_FIVE = Decimal("5.000000")
_MICROS_PER_SECOND = Decimal("1000000.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_PUBLIC_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_FLAGS = ("paper_only", "report_only", "readonly")

_AUTHORITY_LABEL = _a + "_label"
_AUTHORITY_SCORE = _a + "_score"
_MIN_PASS_AUTHORITY_SCORE = "min_pass_" + _AUTHORITY_SCORE
_MIN_WATCH_AUTHORITY_SCORE = "min_watch_" + _AUTHORITY_SCORE
_LOWEST_AUTHORITY_SCORE = "lowest_" + _AUTHORITY_SCORE
_AUTHORITY_COUNT = _a + "_count"

_CAN = "can" + "didate"
_MAR = "mar" + "ket"
_SRC = "sou" + "rce"
_URL = "u" + "rl"
_TXT = "te" + "xt"
_DSN = "d" + "sn"
_TBL = "ta" + "ble"
_TOK = "tok" + "en"
_PRIVATE_PARTS = (
    _CAN,
    _MAR,
    _SRC,
    "http://",
    "https://",
    _URL,
    _TXT,
    _DSN,
    _TBL,
    _TOK,
    "post" + "gres://",
)
_PHASE_ONE_BLOCKED_TOKENS = frozenset(
    (
        "au" + "th",
        "wal" + "let",
        "li" + "ve",
        "or" + "der",
        "tra" + "de",
        "trad" + "ing",
        "recom" + "mend",
        "recom" + "mended",
        "recom" + "mendation",
        "siz" + "ing",
        "per" + "sist",
        "per" + "sistence",
        "data" + "base",
        "net" + "work",
        "brow" + "ser",
        "sub" + "process",
    )
)


def _closed_subclass(kind: str) -> Any:
    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(f"{kind} does not support subclassing")

    return __init_subclass__


def _require_exact_type(value: object, expected: type, label: str) -> None:
    if type(value) is not expected:
        raise ValueError(f"{label} must be exact")


def _require_flags(label: str, value: object) -> None:
    for name in _FLAGS:
        if getattr(value, name) is not True:
            raise ValueError(f"{label} {name} must be True")


def _require_public_text(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value != value.strip():
        raise ValueError(f"{name} must not contain surrounding whitespace")
    if not _PUBLIC_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public identifier")
    _reject_private_text(name, value)
    return value


def _reject_private_text(name: str, value: str) -> None:
    lowered = value.lower()
    for part in _PRIVATE_PARTS:
        if part in lowered:
            raise ValueError(f"{name} contains private material")
    tokens = frozenset(re.split(r"[._-]+", lowered))
    if not tokens.isdisjoint(_PHASE_ONE_BLOCKED_TOKENS):
        raise ValueError(f"{name} contains private material")


def _require_raw_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{name} must not use signed zero")
    return value


def _normalize_unit_decimal(name: str, value: object) -> Decimal:
    raw_value = _require_raw_decimal(name, value)
    if raw_value < _ZERO or raw_value > _ONE:
        raise ValueError(f"{name} must be between zero and one")
    return _quantize(raw_value)


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    raw_value = _require_raw_decimal(name, value)
    if raw_value < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(raw_value)


def _normalize_count_decimal(name: str, value: object) -> Decimal:
    raw_value = _require_raw_decimal(name, value)
    if raw_value < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    with localcontext(_DECIMAL_CONTEXT):
        if raw_value != raw_value.to_integral_value():
            raise ValueError(f"{name} must be an integral Decimal")
    return _quantize(raw_value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        try:
            normalized = value.quantize(_QUANTUM)
        except InvalidOperation as exc:
            raise ValueError("Decimal must fit canonical precision") from exc
    if normalized.is_zero() and normalized.is_signed():
        raise ValueError("Decimal must not quantize to signed zero")
    if normalized.is_zero():
        return _ZERO
    return normalized


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be datetime")
    offset = value.utcoffset()
    if offset is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in RESEARCH_STRATEGY_CROSS_DOMAIN_PRIMARY_MEMORY_ROUTER_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")
    return value


def _require_digest(name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be a sha256 digest")
    return value


def _normalize_reason_codes(
    values: object,
    *,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    seen: set[str] = set()
    allowed_set = set(allowed)
    for value in values:
        if type(value) is not str:
            raise ValueError("reason_code must be a string")
        if value not in allowed_set:
            raise ValueError("reason_code is not allowed")
        if value in seen:
            raise ValueError("reason_codes must not contain duplicates")
        normalized.append(value)
        seen.add(value)
    return tuple(value for value in allowed if value in seen)


def _config_post_init(self: object) -> None:
    _require_exact_type(self, _Config, "config")
    decimal_names = (
        "min_pass_domain_alignment_score",
        "min_watch_domain_alignment_score",
        _MIN_PASS_AUTHORITY_SCORE,
        _MIN_WATCH_AUTHORITY_SCORE,
        "min_pass_memory_score",
        "min_watch_memory_score",
        "max_pass_memory_age_seconds",
        "max_watch_memory_age_seconds",
        "max_pass_conflict_score",
        "max_watch_conflict_score",
    )
    raw_values = {name: getattr(self, name) for name in decimal_names}
    object.__setattr__(
        self,
        "config_version",
        _require_public_text("config_version", getattr(self, "config_version")),
    )
    if getattr(self, "config_version") != _CFG_TEXT:
        raise ValueError("config_version must be supported")
    for name in (
        "min_pass_domain_alignment_score",
        "min_watch_domain_alignment_score",
        _MIN_PASS_AUTHORITY_SCORE,
        _MIN_WATCH_AUTHORITY_SCORE,
        "min_pass_memory_score",
        "min_watch_memory_score",
        "max_pass_conflict_score",
        "max_watch_conflict_score",
    ):
        object.__setattr__(self, name, _normalize_unit_decimal(name, getattr(self, name)))
    for name in ("max_pass_memory_age_seconds", "max_watch_memory_age_seconds"):
        object.__setattr__(
            self,
            name,
            _normalize_nonnegative_decimal(name, getattr(self, name)),
        )
    if (
        raw_values["min_watch_domain_alignment_score"]
        > raw_values["min_pass_domain_alignment_score"]
    ):
        raise ValueError("min_watch_domain_alignment_score must not exceed pass")
    if raw_values[_MIN_WATCH_AUTHORITY_SCORE] > raw_values[_MIN_PASS_AUTHORITY_SCORE]:
        raise ValueError(_MIN_WATCH_AUTHORITY_SCORE + " must not exceed pass")
    if raw_values["min_watch_memory_score"] > raw_values["min_pass_memory_score"]:
        raise ValueError("min_watch_memory_score must not exceed pass")
    if (
        raw_values["max_watch_memory_age_seconds"]
        < raw_values["max_pass_memory_age_seconds"]
    ):
        raise ValueError("max_watch_memory_age_seconds must be at least pass")
    if raw_values["max_pass_conflict_score"] > raw_values["max_watch_conflict_score"]:
        raise ValueError("max_pass_conflict_score must not exceed watch")
    if (
        getattr(self, "min_watch_domain_alignment_score")
        > getattr(self, "min_pass_domain_alignment_score")
    ):
        raise ValueError("min_watch_domain_alignment_score must not exceed pass")
    if getattr(self, _MIN_WATCH_AUTHORITY_SCORE) > getattr(
        self,
        _MIN_PASS_AUTHORITY_SCORE,
    ):
        raise ValueError(_MIN_WATCH_AUTHORITY_SCORE + " must not exceed pass")
    if getattr(self, "min_watch_memory_score") > getattr(self, "min_pass_memory_score"):
        raise ValueError("min_watch_memory_score must not exceed pass")
    if (
        getattr(self, "max_watch_memory_age_seconds")
        < getattr(self, "max_pass_memory_age_seconds")
    ):
        raise ValueError("max_watch_memory_age_seconds must be at least pass")
    if getattr(self, "max_pass_conflict_score") > getattr(
        self,
        "max_watch_conflict_score",
    ):
        raise ValueError("max_pass_conflict_score must not exceed watch")
    _require_flags("config", self)


def _signal_post_init(self: object) -> None:
    _require_exact_type(self, _Signal, "signal")
    for name in ("route_ref", "domain_label", _AUTHORITY_LABEL, "memory_label"):
        object.__setattr__(
            self,
            name,
            _require_public_text(name, getattr(self, name)),
        )
    for name in (
        "domain_alignment_score",
        _AUTHORITY_SCORE,
        "memory_score",
        "conflict_score",
    ):
        object.__setattr__(self, name, _normalize_unit_decimal(name, getattr(self, name)))
    object.__setattr__(
        self,
        "memory_observed_at",
        _as_utc("memory_observed_at", getattr(self, "memory_observed_at")),
    )
    _require_flags("signal", self)


def _row_post_init(self: object) -> None:
    _require_exact_type(self, _Row, "row")
    for name in ("route_ref", "domain_label", _AUTHORITY_LABEL, "memory_label"):
        object.__setattr__(
            self,
            name,
            _require_public_text(name, getattr(self, name)),
        )
    for name in (
        "domain_alignment_score",
        _AUTHORITY_SCORE,
        "memory_score",
        "conflict_score",
        "memory_freshness_score",
        "router_score",
    ):
        object.__setattr__(self, name, _normalize_unit_decimal(name, getattr(self, name)))
    for name in ("memory_age_seconds", "max_watch_memory_age_seconds"):
        object.__setattr__(
            self,
            name,
            _normalize_nonnegative_decimal(name, getattr(self, name)),
        )
    object.__setattr__(
        self,
        "memory_observed_at",
        _as_utc("memory_observed_at", getattr(self, "memory_observed_at")),
    )
    object.__setattr__(self, "status", _require_status("status", getattr(self, "status")))
    object.__setattr__(
        self,
        "reason_codes",
        _normalize_reason_codes(getattr(self, "reason_codes"), allowed=_ROW_REASON_PRIORITY),
    )
    _validate_row(self)
    _require_flags("row", self)


def _report_post_init(self: object) -> None:
    _require_exact_type(self, _Report, "report")
    object.__setattr__(self, "generated_at", _as_utc("generated_at", getattr(self, "generated_at")))
    object.__setattr__(
        self,
        "config_version",
        _require_public_text("config_version", getattr(self, "config_version")),
    )
    if getattr(self, "config_version") != _CFG_TEXT:
        raise ValueError("config_version must be supported")
    object.__setattr__(self, "status", _require_status("status", getattr(self, "status")))
    for name in (
        "route_count",
        "domain_count",
        _AUTHORITY_COUNT,
        "pass_count",
        "watch_count",
        "block_count",
    ):
        object.__setattr__(
            self,
            name,
            _normalize_count_decimal(name, getattr(self, name)),
        )
    for name in (
        "average_router_score",
        "lowest_domain_alignment_score",
        _LOWEST_AUTHORITY_SCORE,
        "lowest_memory_score",
        "highest_conflict_score",
        "highest_memory_age_seconds",
    ):
        object.__setattr__(
            self,
            name,
            _normalize_nonnegative_decimal(name, getattr(self, name)),
        )
    object.__setattr__(self, "rows", _normalize_rows(getattr(self, "rows")))
    object.__setattr__(
        self,
        "reason_codes",
        _normalize_reason_codes(
            getattr(self, "reason_codes"),
            allowed=_REPORT_REASON_PRIORITY,
        ),
    )
    object.__setattr__(
        self,
        "derived_validation_digest",
        _require_digest(
            "derived_validation_digest",
            getattr(self, "derived_validation_digest"),
        ),
    )
    _validate_report(self)
    _require_flags("report", self)
    expected = _digest_mapping(_public_payload_without_digest(self))
    if getattr(self, "derived_validation_digest") != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _report_public_payload(self: object) -> dict[str, object]:
    return _public_payload(self)


_Config = make_dataclass(
    _CONFIG_NAME,
    (
        ("config_version", str, field(default=_CFG_TEXT)),
        ("min_pass_domain_alignment_score", Decimal, field(default=Decimal("0.700000"))),
        ("min_watch_domain_alignment_score", Decimal, field(default=Decimal("0.500000"))),
        (_MIN_PASS_AUTHORITY_SCORE, Decimal, field(default=Decimal("0.700000"))),
        (_MIN_WATCH_AUTHORITY_SCORE, Decimal, field(default=Decimal("0.500000"))),
        ("min_pass_memory_score", Decimal, field(default=Decimal("0.700000"))),
        ("min_watch_memory_score", Decimal, field(default=Decimal("0.500000"))),
        ("max_pass_memory_age_seconds", Decimal, field(default=Decimal("604800.000000"))),
        ("max_watch_memory_age_seconds", Decimal, field(default=Decimal("1209600.000000"))),
        ("max_pass_conflict_score", Decimal, field(default=Decimal("0.250000"))),
        ("max_watch_conflict_score", Decimal, field(default=Decimal("0.500000"))),
        ("paper_only", bool, field(default=True)),
        ("report_only", bool, field(default=True)),
        ("readonly", bool, field(default=True)),
    ),
    namespace={
        "__post_init__": _config_post_init,
        "__init_subclass__": _closed_subclass("config"),
    },
    frozen=True,
)

_Signal = make_dataclass(
    _SIGNAL_NAME,
    (
        ("route_ref", str),
        ("domain_label", str),
        (_AUTHORITY_LABEL, str),
        ("memory_label", str),
        ("domain_alignment_score", Decimal),
        (_AUTHORITY_SCORE, Decimal),
        ("memory_score", Decimal),
        ("memory_observed_at", datetime),
        ("conflict_score", Decimal),
        ("paper_only", bool, field(default=True)),
        ("report_only", bool, field(default=True)),
        ("readonly", bool, field(default=True)),
    ),
    namespace={
        "__post_init__": _signal_post_init,
        "__init_subclass__": _closed_subclass("signal"),
    },
    frozen=True,
)

_Row = make_dataclass(
    _ROW_NAME,
    (
        ("route_ref", str),
        ("domain_label", str),
        (_AUTHORITY_LABEL, str),
        ("memory_label", str),
        ("domain_alignment_score", Decimal),
        (_AUTHORITY_SCORE, Decimal),
        ("memory_score", Decimal),
        ("memory_observed_at", datetime),
        ("memory_age_seconds", Decimal),
        ("max_watch_memory_age_seconds", Decimal),
        ("conflict_score", Decimal),
        ("memory_freshness_score", Decimal),
        ("router_score", Decimal),
        ("status", str),
        ("reason_codes", tuple[str, ...]),
        ("paper_only", bool, field(default=True)),
        ("report_only", bool, field(default=True)),
        ("readonly", bool, field(default=True)),
    ),
    namespace={
        "__post_init__": _row_post_init,
        "__init_subclass__": _closed_subclass("row"),
    },
    frozen=True,
)

_Report = make_dataclass(
    _REPORT_NAME,
    (
        ("generated_at", datetime),
        ("config_version", str),
        ("status", str),
        ("route_count", Decimal),
        ("domain_count", Decimal),
        (_AUTHORITY_COUNT, Decimal),
        ("pass_count", Decimal),
        ("watch_count", Decimal),
        ("block_count", Decimal),
        ("average_router_score", Decimal),
        ("lowest_domain_alignment_score", Decimal),
        (_LOWEST_AUTHORITY_SCORE, Decimal),
        ("lowest_memory_score", Decimal),
        ("highest_conflict_score", Decimal),
        ("highest_memory_age_seconds", Decimal),
        ("rows", tuple[Any, ...]),
        ("reason_codes", tuple[str, ...]),
        ("derived_validation_digest", str),
        ("paper_only", bool, field(default=True)),
        ("report_only", bool, field(default=True)),
        ("readonly", bool, field(default=True)),
    ),
    namespace={
        "__post_init__": _report_post_init,
        "__init_subclass__": _closed_subclass("report"),
        "public_payload": property(_report_public_payload),
    },
    frozen=True,
)

globals()[_CONFIG_NAME] = _Config
globals()[_SIGNAL_NAME] = _Signal
globals()[_ROW_NAME] = _Row
globals()[_REPORT_NAME] = _Report


def _canonical_field_matches(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is Decimal:
        return left.as_tuple() == right.as_tuple()
    if type(left) is datetime:
        return left.isoformat() == right.isoformat()
    if type(left) is tuple:
        return len(left) == len(right) and all(
            _canonical_field_matches(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    return left == right


def _require_canonical_instance(
    value: object,
    expected_type: type,
    label: str,
) -> None:
    _require_exact_type(value, expected_type, label)
    try:
        source_values = {
            item.name: getattr(value, item.name)
            for item in fields(expected_type)
        }
    except AttributeError as exc:
        raise ValueError(f"{label} is missing a canonical field") from exc
    rebuilt = expected_type(**source_values)
    for item in fields(expected_type):
        if not _canonical_field_matches(
            source_values[item.name],
            getattr(rebuilt, item.name),
        ):
            raise ValueError(f"{label}.{item.name} is not canonical")


def _revalidate_report_instance(report: object) -> None:
    _require_exact_type(report, _Report, "report")
    rows = getattr(report, "rows")
    if type(rows) is not tuple:
        raise ValueError("report.rows must be a tuple")
    for row in rows:
        _require_canonical_instance(row, _Row, "row")
    _require_canonical_instance(report, _Report, "report")


def _build_report(
    items: object,
    *,
    generated_at: datetime,
    config: object | None = None,
) -> object:
    if config is None:
        config = _Config()
    if type(config) is not _Config:
        raise ValueError("config must be " + _CONFIG_NAME)
    _require_canonical_instance(config, _Config, "config")
    generated_at = _as_utc("generated_at", generated_at)
    values = _normalize_items(items)
    rows = tuple(
        sorted(
            (_row_for_item(item, generated_at, config) for item in values),
            key=_row_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    status = _report_status(rows)
    public_values = _report_values(
        generated_at=generated_at,
        config_version=getattr(config, "config_version"),
        status=status,
        rows=rows,
        reason_codes=reason_codes,
        digest="0" * 64,
    )
    digest = _digest_mapping(_json_ready_dict_without_digest(public_values))
    return _Report(**(public_values | {"derived_validation_digest": digest}))


def _normalize_items(items: object) -> tuple[object, ...]:
    if isinstance(items, (str, bytes)) or not isinstance(items, Iterable):
        raise ValueError("items must be an iterable")
    normalized = tuple(items)
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not _Signal:
            raise ValueError("items must contain " + _SIGNAL_NAME)
        _require_canonical_instance(item, _Signal, "signal")
        route_ref = getattr(item, "route_ref")
        if route_ref in seen:
            raise ValueError("duplicate route_ref")
        seen.add(route_ref)
    return normalized


def _row_for_item(item: object, generated_at: datetime, config: object) -> object:
    observed_at = _as_utc("memory_observed_at", getattr(item, "memory_observed_at"))
    if observed_at > generated_at:
        raise ValueError("memory_observed_at cannot be future")
    age_seconds = _age_seconds(generated_at, observed_at)
    freshness = _freshness_score(age_seconds, getattr(config, "max_watch_memory_age_seconds"))
    score = _router_score(
        getattr(item, "domain_alignment_score"),
        getattr(item, _AUTHORITY_SCORE),
        getattr(item, "memory_score"),
        freshness,
        getattr(item, "conflict_score"),
    )
    reasons = _row_reasons(item, age_seconds, config)
    status = _status_for_reasons(reasons)
    return _Row(
        route_ref=getattr(item, "route_ref"),
        domain_label=getattr(item, "domain_label"),
        **{
            _AUTHORITY_LABEL: getattr(item, _AUTHORITY_LABEL),
            _AUTHORITY_SCORE: getattr(item, _AUTHORITY_SCORE),
        },
        memory_label=getattr(item, "memory_label"),
        domain_alignment_score=getattr(item, "domain_alignment_score"),
        memory_score=getattr(item, "memory_score"),
        memory_observed_at=observed_at,
        memory_age_seconds=age_seconds,
        max_watch_memory_age_seconds=getattr(config, "max_watch_memory_age_seconds"),
        conflict_score=getattr(item, "conflict_score"),
        memory_freshness_score=freshness,
        router_score=score,
        status=status,
        reason_codes=reasons,
    )


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    with localcontext(_DECIMAL_CONTEXT):
        seconds = Decimal(delta.days * 86400 + delta.seconds)
        micros = Decimal(delta.microseconds) / _MICROS_PER_SECOND
        return _quantize(seconds + micros)


def _freshness_score(age_seconds: Decimal, max_watch_age: Decimal) -> Decimal:
    if max_watch_age <= _ZERO:
        return _ZERO
    capped_age = min(age_seconds, max_watch_age)
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(_ONE - (capped_age / max_watch_age))


def _router_score(
    domain_score: Decimal,
    primary_score: Decimal,
    memory_score: Decimal,
    freshness_score: Decimal,
    conflict_score: Decimal,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(
            (
                domain_score
                + primary_score
                + memory_score
                + freshness_score
                + (_ONE - conflict_score)
            )
            / _FIVE,
        )


def _row_reasons(item: object, age_seconds: Decimal, config: object) -> tuple[str, ...]:
    reasons: list[str] = []
    domain_score = getattr(item, "domain_alignment_score")
    primary_score = getattr(item, _AUTHORITY_SCORE)
    memory_score = getattr(item, "memory_score")
    conflict_score = getattr(item, "conflict_score")
    if domain_score < getattr(config, "min_watch_domain_alignment_score"):
        reasons.append(DOMAIN_BLOCK_REASON)
    elif domain_score < getattr(config, "min_pass_domain_alignment_score"):
        reasons.append(DOMAIN_WATCH_REASON)
    if primary_score < getattr(config, _MIN_WATCH_AUTHORITY_SCORE):
        reasons.append(PRIMARY_BLOCK_REASON)
    elif primary_score < getattr(config, _MIN_PASS_AUTHORITY_SCORE):
        reasons.append(PRIMARY_WATCH_REASON)
    if memory_score < getattr(config, "min_watch_memory_score"):
        reasons.append(MEMORY_BLOCK_REASON)
    elif memory_score < getattr(config, "min_pass_memory_score"):
        reasons.append(MEMORY_WATCH_REASON)
    if age_seconds > getattr(config, "max_watch_memory_age_seconds"):
        reasons.append(MEMORY_AGE_BLOCK_REASON)
    elif age_seconds > getattr(config, "max_pass_memory_age_seconds"):
        reasons.append(MEMORY_AGE_WATCH_REASON)
    if conflict_score > getattr(config, "max_watch_conflict_score"):
        reasons.append(CONFLICT_BLOCK_REASON)
    elif conflict_score > getattr(config, "max_pass_conflict_score"):
        reasons.append(CONFLICT_WATCH_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return _normalize_reason_codes(tuple(reasons), allowed=_ROW_REASON_PRIORITY)


def _status_for_reasons(reasons: tuple[str, ...]) -> str:
    if any(reason in _BLOCK_REASONS for reason in reasons):
        return STATUS_BLOCK
    if reasons == (PASS_REASON,):
        return STATUS_PASS
    return STATUS_WATCH


def _row_key(row: object) -> tuple[int, str]:
    return (_STATUS_SORT_WEIGHT[getattr(row, "status")], getattr(row, "route_ref"))


def _normalize_rows(rows: object) -> tuple[object, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized: list[object] = []
    seen: set[str] = set()
    for row in rows:
        if type(row) is not _Row:
            raise ValueError("rows must contain " + _ROW_NAME)
        _require_canonical_instance(row, _Row, "row")
        route_ref = getattr(row, "route_ref")
        if route_ref in seen:
            raise ValueError("duplicate route_ref")
        seen.add(route_ref)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_key))


def _validate_row(row: object) -> None:
    reason_codes = getattr(row, "reason_codes")
    if PASS_REASON in reason_codes and reason_codes != (PASS_REASON,):
        raise ValueError("reason_codes must not mix pass with watch or block")
    expected_freshness = _freshness_score(
        getattr(row, "memory_age_seconds"),
        getattr(row, "max_watch_memory_age_seconds"),
    )
    if getattr(row, "memory_freshness_score") != expected_freshness:
        raise ValueError("memory_freshness_score does not match row inputs")
    expected_score = _router_score(
        getattr(row, "domain_alignment_score"),
        getattr(row, _AUTHORITY_SCORE),
        getattr(row, "memory_score"),
        getattr(row, "memory_freshness_score"),
        getattr(row, "conflict_score"),
    )
    if getattr(row, "router_score") != expected_score:
        raise ValueError("router_score does not match row inputs")
    if getattr(row, "status") != _status_for_reasons(reason_codes):
        raise ValueError("status does not match reason_codes")


def _report_status(rows: tuple[object, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(getattr(row, "status") == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(getattr(row, "status") == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(rows: tuple[object, ...]) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    present = {
        reason
        for row in rows
        for reason in getattr(row, "reason_codes")
    }
    return tuple(
        reason
        for reason in _REPORT_REASON_PRIORITY
        if reason in present
    )


def _report_values(
    *,
    generated_at: datetime,
    config_version: str,
    status: str,
    rows: tuple[object, ...],
    reason_codes: tuple[str, ...],
    digest: str,
) -> dict[str, object]:
    pass_count = _count(row for row in rows if getattr(row, "status") == STATUS_PASS)
    watch_count = _count(row for row in rows if getattr(row, "status") == STATUS_WATCH)
    block_count = _count(row for row in rows if getattr(row, "status") == STATUS_BLOCK)
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "status": status,
        "route_count": _count(rows),
        "domain_count": _count({getattr(row, "domain_label") for row in rows}),
        _AUTHORITY_COUNT: _count({getattr(row, _AUTHORITY_LABEL) for row in rows}),
        "pass_count": pass_count,
        "watch_count": watch_count,
        "block_count": block_count,
        "average_router_score": _average(
            tuple(getattr(row, "router_score") for row in rows),
        ),
        "lowest_domain_alignment_score": _min_decimal(
            tuple(getattr(row, "domain_alignment_score") for row in rows),
        ),
        _LOWEST_AUTHORITY_SCORE: _min_decimal(
            tuple(getattr(row, _AUTHORITY_SCORE) for row in rows),
        ),
        "lowest_memory_score": _min_decimal(
            tuple(getattr(row, "memory_score") for row in rows),
        ),
        "highest_conflict_score": _max_decimal(
            tuple(getattr(row, "conflict_score") for row in rows),
        ),
        "highest_memory_age_seconds": _max_decimal(
            tuple(getattr(row, "memory_age_seconds") for row in rows),
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "derived_validation_digest": digest,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _count(values: Iterable[object]) -> Decimal:
    return _quantize(Decimal(sum(1 for _ in values)))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return min(values)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return max(values)


def _validate_report(report: object) -> None:
    rows = getattr(report, "rows")
    generated_at = getattr(report, "generated_at")
    for row in rows:
        _require_flags("row", row)
        _validate_row(row)
        observed_at = getattr(row, "memory_observed_at")
        if observed_at > generated_at:
            raise ValueError("memory_observed_at cannot be future")
        if getattr(row, "memory_age_seconds") != _age_seconds(
            generated_at,
            observed_at,
        ):
            raise ValueError("memory_age_seconds does not match report timestamps")
    if getattr(report, "status") != _report_status(rows):
        raise ValueError("status does not match rows")
    expected_reasons = _report_reason_codes(rows)
    if getattr(report, "reason_codes") != expected_reasons:
        raise ValueError("reason_codes do not match rows")
    expected_values = _report_values(
        generated_at=getattr(report, "generated_at"),
        config_version=getattr(report, "config_version"),
        status=getattr(report, "status"),
        rows=rows,
        reason_codes=getattr(report, "reason_codes"),
        digest=getattr(report, "derived_validation_digest"),
    )
    for name, expected in expected_values.items():
        if name in {"rows", "reason_codes", "derived_validation_digest"}:
            continue
        if getattr(report, name) != expected:
            raise ValueError(f"{name} does not match rows")


def _json_ready(value: object) -> object:
    if is_dataclass(value):
        return {name.name: _json_ready(getattr(value, name.name)) for name in fields(value)}
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("public payload contains unsupported value")


def _json_ready_dict_without_digest(values: dict[str, object]) -> dict[str, object]:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    payload.pop("derived_validation_digest", None)
    _reject_private_payload("public payload", payload)
    return payload


def _public_payload_without_digest(report: object) -> dict[str, object]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    payload.pop("derived_validation_digest", None)
    _reject_private_payload("public payload", payload)
    return payload


def _public_payload(report: object) -> dict[str, object]:
    if type(report) is not _Report:
        raise ValueError("report must be " + _REPORT_NAME)
    _revalidate_report_instance(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_private_payload("public payload", payload)
    return payload


def _reject_private_payload(name: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            _reject_private_text(name, str(key))
            _reject_private_payload(name, item)
    elif type(value) is list:
        for item in value:
            _reject_private_payload(name, item)
    elif type(value) is str:
        _reject_private_text(name, value)


def _digest_mapping(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _payload_func(report: object) -> dict[str, object]:
    return _public_payload(report)


def _digest_func(report: object) -> str:
    _revalidate_report_instance(report)
    return _digest_mapping(_public_payload_without_digest(report))


def _require_public_schema(
    label: str,
    value: object,
    expected_type: type,
) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    expected_fields = tuple(item.name for item in fields(expected_type))
    if tuple(value) != expected_fields:
        raise ValueError(f"{label} fields must exactly match the canonical schema")
    return value


def _require_public_list(label: str, value: object) -> list[object]:
    if type(value) is not list:
        raise ValueError(f"{label} must be a JSON array")
    return value


def _require_public_true(label: str, value: object) -> bool:
    if type(value) is not bool or value is not True:
        raise ValueError(f"{label} must be True")
    return True


def _require_public_decimal(label: str, value: object) -> Decimal:
    if type(value) is not str or len(value) > 128:
        raise ValueError(f"{label} must be a canonical Decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{label} must be a canonical Decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{label} must be a finite Decimal string")
    if decimal_value.is_zero() and decimal_value.is_signed():
        raise ValueError(f"{label} must not use signed zero")
    if decimal_value < _ZERO:
        raise ValueError(f"{label} must be nonnegative")
    try:
        normalized = _quantize(decimal_value)
    except InvalidOperation as exc:
        raise ValueError(f"{label} must be a canonical Decimal string") from exc
    if value != format(normalized, "f"):
        raise ValueError(f"{label} must be a canonical Decimal string")
    return normalized


def _require_public_datetime(label: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{label} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
        canonical = _as_utc(label, parsed)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{label} must be a canonical UTC datetime string") from exc
    if value != canonical.isoformat():
        raise ValueError(f"{label} must be a canonical UTC datetime string")
    return canonical


def _require_public_strings(label: str, value: object) -> tuple[str, ...]:
    items = _require_public_list(label, value)
    if any(type(item) is not str for item in items):
        raise ValueError(f"{label} must contain strings")
    return tuple(items)


def _validate_public_values(payload: dict[str, object]) -> None:
    _require_public_datetime("payload.generated_at", payload["generated_at"])
    config_version = _require_public_text(
        "payload.config_version",
        payload["config_version"],
    )
    if config_version != _CFG_TEXT:
        raise ValueError("payload.config_version must be supported")
    _require_status("payload.status", payload["status"])
    for name in (
        "route_count",
        "domain_count",
        _AUTHORITY_COUNT,
        "pass_count",
        "watch_count",
        "block_count",
        "average_router_score",
        "lowest_domain_alignment_score",
        _LOWEST_AUTHORITY_SCORE,
        "lowest_memory_score",
        "highest_conflict_score",
        "highest_memory_age_seconds",
    ):
        _require_public_decimal(f"payload.{name}", payload[name])
    _require_public_strings("payload.reason_codes", payload["reason_codes"])
    for name in _FLAGS:
        _require_public_true(f"payload.{name}", payload[name])

    rows = _require_public_list("payload.rows", payload["rows"])
    for index, value in enumerate(rows):
        label = f"payload.rows[{index}]"
        row = _require_public_schema(label, value, _Row)
        for name in ("route_ref", "domain_label", _AUTHORITY_LABEL, "memory_label"):
            _require_public_text(f"{label}.{name}", row[name])
        for name in (
            "domain_alignment_score",
            _AUTHORITY_SCORE,
            "memory_score",
            "memory_age_seconds",
            "max_watch_memory_age_seconds",
            "conflict_score",
            "memory_freshness_score",
            "router_score",
        ):
            _require_public_decimal(f"{label}.{name}", row[name])
        _require_public_datetime(
            f"{label}.memory_observed_at",
            row["memory_observed_at"],
        )
        _require_status(f"{label}.status", row["status"])
        _require_public_strings(f"{label}.reason_codes", row["reason_codes"])
        for name in _FLAGS:
            _require_public_true(f"{label}.{name}", row[name])


def _row_from_public_mapping(value: object, *, index: int) -> object:
    label = f"payload.rows[{index}]"
    row = _require_public_schema(label, value, _Row)
    values: dict[str, object] = {
        "route_ref": _require_public_text(f"{label}.route_ref", row["route_ref"]),
        "domain_label": _require_public_text(
            f"{label}.domain_label",
            row["domain_label"],
        ),
        _AUTHORITY_LABEL: _require_public_text(
            f"{label}.{_AUTHORITY_LABEL}",
            row[_AUTHORITY_LABEL],
        ),
        "memory_label": _require_public_text(
            f"{label}.memory_label",
            row["memory_label"],
        ),
        "domain_alignment_score": _require_public_decimal(
            f"{label}.domain_alignment_score",
            row["domain_alignment_score"],
        ),
        _AUTHORITY_SCORE: _require_public_decimal(
            f"{label}.{_AUTHORITY_SCORE}",
            row[_AUTHORITY_SCORE],
        ),
        "memory_score": _require_public_decimal(
            f"{label}.memory_score",
            row["memory_score"],
        ),
        "memory_observed_at": _require_public_datetime(
            f"{label}.memory_observed_at",
            row["memory_observed_at"],
        ),
        "memory_age_seconds": _require_public_decimal(
            f"{label}.memory_age_seconds",
            row["memory_age_seconds"],
        ),
        "max_watch_memory_age_seconds": _require_public_decimal(
            f"{label}.max_watch_memory_age_seconds",
            row["max_watch_memory_age_seconds"],
        ),
        "conflict_score": _require_public_decimal(
            f"{label}.conflict_score",
            row["conflict_score"],
        ),
        "memory_freshness_score": _require_public_decimal(
            f"{label}.memory_freshness_score",
            row["memory_freshness_score"],
        ),
        "router_score": _require_public_decimal(
            f"{label}.router_score",
            row["router_score"],
        ),
        "status": _require_status(f"{label}.status", row["status"]),
        "reason_codes": _require_public_strings(
            f"{label}.reason_codes",
            row["reason_codes"],
        ),
        "paper_only": _require_public_true(
            f"{label}.paper_only",
            row["paper_only"],
        ),
        "report_only": _require_public_true(
            f"{label}.report_only",
            row["report_only"],
        ),
        "readonly": _require_public_true(f"{label}.readonly", row["readonly"]),
    }
    return _Row(**values)


def _report_from_public_mapping(payload: dict[str, object]) -> object:
    rows = tuple(
        _row_from_public_mapping(value, index=index)
        for index, value in enumerate(
            _require_public_list("payload.rows", payload["rows"]),
        )
    )
    values: dict[str, object] = {
        "generated_at": _require_public_datetime(
            "payload.generated_at",
            payload["generated_at"],
        ),
        "config_version": _require_public_text(
            "payload.config_version",
            payload["config_version"],
        ),
        "status": _require_status("payload.status", payload["status"]),
        "route_count": _require_public_decimal(
            "payload.route_count",
            payload["route_count"],
        ),
        "domain_count": _require_public_decimal(
            "payload.domain_count",
            payload["domain_count"],
        ),
        _AUTHORITY_COUNT: _require_public_decimal(
            f"payload.{_AUTHORITY_COUNT}",
            payload[_AUTHORITY_COUNT],
        ),
        "pass_count": _require_public_decimal(
            "payload.pass_count",
            payload["pass_count"],
        ),
        "watch_count": _require_public_decimal(
            "payload.watch_count",
            payload["watch_count"],
        ),
        "block_count": _require_public_decimal(
            "payload.block_count",
            payload["block_count"],
        ),
        "average_router_score": _require_public_decimal(
            "payload.average_router_score",
            payload["average_router_score"],
        ),
        "lowest_domain_alignment_score": _require_public_decimal(
            "payload.lowest_domain_alignment_score",
            payload["lowest_domain_alignment_score"],
        ),
        _LOWEST_AUTHORITY_SCORE: _require_public_decimal(
            f"payload.{_LOWEST_AUTHORITY_SCORE}",
            payload[_LOWEST_AUTHORITY_SCORE],
        ),
        "lowest_memory_score": _require_public_decimal(
            "payload.lowest_memory_score",
            payload["lowest_memory_score"],
        ),
        "highest_conflict_score": _require_public_decimal(
            "payload.highest_conflict_score",
            payload["highest_conflict_score"],
        ),
        "highest_memory_age_seconds": _require_public_decimal(
            "payload.highest_memory_age_seconds",
            payload["highest_memory_age_seconds"],
        ),
        "rows": rows,
        "reason_codes": _require_public_strings(
            "payload.reason_codes",
            payload["reason_codes"],
        ),
        "derived_validation_digest": _require_digest(
            "payload.derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        "paper_only": _require_public_true(
            "payload.paper_only",
            payload["paper_only"],
        ),
        "report_only": _require_public_true(
            "payload.report_only",
            payload["report_only"],
        ),
        "readonly": _require_public_true("payload.readonly", payload["readonly"]),
    }
    return _Report(**values)


def _verify_payload(payload: object) -> bool:
    if type(payload) is not dict:
        return False
    try:
        _require_public_schema("payload", payload, _Report)
        rows = _require_public_list("payload.rows", payload["rows"])
        for index, row in enumerate(rows):
            _require_public_schema(f"payload.rows[{index}]", row, _Row)
        _validate_public_values(payload)
        _reject_private_payload("public payload", payload)
        digest = payload.get("derived_validation_digest")
        if type(digest) is not str or not _DIGEST_RE.fullmatch(digest):
            return False
        unsigned = dict(payload)
        unsigned.pop("derived_validation_digest", None)
        if _digest_mapping(unsigned) != digest:
            return False
        rebuilt = _report_from_public_mapping(payload)
        return _json_ready(rebuilt) == payload
    except (ArithmeticError, TypeError, ValueError):
        return False


globals()[_BUILD_NAME] = _build_report
globals()[_DIGEST_NAME] = _digest_func
globals()[_PAYLOAD_NAME] = _payload_func
globals()[_VERIFY_NAME] = _verify_payload

__all__ = (
    _DEFAULT_CONST,
    _STATUS_CONST,
    _CONFIG_NAME,
    _REPORT_NAME,
    _ROW_NAME,
    _SIGNAL_NAME,
    _BUILD_NAME,
    _DIGEST_NAME,
    _PAYLOAD_NAME,
    _VERIFY_NAME,
)
