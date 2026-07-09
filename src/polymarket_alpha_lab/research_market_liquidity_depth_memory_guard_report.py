"""Pure report for market cost pressure across liquidity, depth, and memory."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_MARKET_LIQUIDITY_DEPTH_MEMORY_GUARD_CONFIG_VERSION",
    "ResearchMarketLiquidityDepthMemoryGuardConfig",
    "ResearchMarketLiquidityDepthMemoryGuardObservation",
    "ResearchMarketLiquidityDepthMemoryGuardReport",
    "ResearchMarketLiquidityDepthMemoryGuardRow",
    "STATUSES",
    "build_research_market_liquidity_depth_memory_guard_report",
    "research_market_liquidity_depth_memory_guard_report_payload",
    "validate_research_market_liquidity_depth_memory_guard_report_payload",
)


DEFAULT_RESEARCH_MARKET_LIQUIDITY_DEPTH_MEMORY_GUARD_CONFIG_VERSION = (
    "research-market-liquidity-depth-memory-guard-report-v0"
)

STATUSES = ("pass", "watch", "block")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
PASS_GUARD_SCORE = Decimal("0.900000")
WATCH_GUARD_SCORE = Decimal("0.650000")
BLOCK_GUARD_SCORE = Decimal("0.350000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
HEX_CHARS = frozenset("0123456789abcdef")

READY_REASON_CODE = "liquidity_depth_memory_guard_ready"
REPORT_REASON_BY_STATUS = {
    "pass": "liquidity_depth_memory_guard_report_pass",
    "watch": "liquidity_depth_memory_guard_report_watch",
    "block": "liquidity_depth_memory_guard_report_block",
}
REPORT_EMPTY_REASON_CODE = "liquidity_depth_memory_guard_report_empty"
STATUS_SUMMARY = {
    "pass": "pass: liquidity/depth/memory guard inputs are sufficient for paper review",
    "watch": (
        "watch: liquidity/depth/memory guard inputs need manual review "
        "before paper review"
    ),
    "block": (
        "block: liquidity/depth/memory guard inputs are not sufficient "
        "for paper review"
    ),
}
EMPTY_SUMMARY = "block: no liquidity/depth/memory guard inputs supplied for paper review"
BLOCK_REASON_CODES = (
    "liquidity_depth_memory_guard_cost_block",
    "liquidity_depth_memory_guard_liquidity_block",
    "liquidity_depth_memory_guard_depth_block",
    "liquidity_depth_memory_guard_memory_block",
)
WATCH_REASON_CODES = (
    "liquidity_depth_memory_guard_cost_watch",
    "liquidity_depth_memory_guard_liquidity_watch",
    "liquidity_depth_memory_guard_depth_watch",
    "liquidity_depth_memory_guard_memory_watch",
)
REPORT_REASON_PRIORITY = (
    *BLOCK_REASON_CODES,
    *WATCH_REASON_CODES,
)
PRIVATE_TEXT_FIELDS = (
    "raw_candidate_ref",
    "raw_market_ref",
    "evidence_locator",
    "evidence_excerpt",
    "evidence_store_ref",
    "evidence_collection_ref",
    "evidence_secret_ref",
)
UNSAFE_PUBLIC_FIELD_PARTS = (
    "raw",
    "candidate",
    "source",
    "locator",
    "excerpt",
    "store_ref",
    "collection_ref",
    "secret_ref",
    "url",
    "dsn",
    "table",
    "token",
)
UNSAFE_PUBLIC_VALUE_PARTS = (
    "://",
    "postgresql",
    "private",
    "secret",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise ValueError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchMarketLiquidityDepthMemoryGuardConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_LIQUIDITY_DEPTH_MEMORY_GUARD_CONFIG_VERSION
    )
    max_pass_cost_rate: Decimal = Decimal("0.025000")
    max_watch_cost_rate: Decimal = Decimal("0.060000")
    min_pass_liquidity_score: Decimal = Decimal("0.700000")
    min_watch_liquidity_score: Decimal = Decimal("0.450000")
    min_pass_depth_score: Decimal = Decimal("0.700000")
    min_watch_depth_score: Decimal = Decimal("0.450000")
    min_pass_memory_score: Decimal = Decimal("0.750000")
    min_watch_memory_score: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityDepthMemoryGuardConfig, "config")
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_DEPTH_MEMORY_GUARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_cost_rate",
            "max_watch_cost_rate",
            "min_pass_liquidity_score",
            "min_watch_liquidity_score",
            "min_pass_depth_score",
            "min_watch_depth_score",
            "min_pass_memory_score",
            "min_watch_memory_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_watch_cost_rate < self.max_pass_cost_rate:
            raise ValueError("max_watch_cost_rate must be at least max_pass_cost_rate")
        if self.min_pass_liquidity_score < self.min_watch_liquidity_score:
            raise ValueError(
                "min_pass_liquidity_score must be at least "
                "min_watch_liquidity_score",
            )
        if self.min_pass_depth_score < self.min_watch_depth_score:
            raise ValueError(
                "min_pass_depth_score must be at least min_watch_depth_score",
            )
        if self.min_pass_memory_score < self.min_watch_memory_score:
            raise ValueError(
                "min_pass_memory_score must be at least min_watch_memory_score",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityDepthMemoryGuardObservation(_FinalPublicDataclass):
    raw_candidate_ref: str
    raw_market_ref: str
    evidence_locator: str
    evidence_excerpt: str
    evidence_store_ref: str
    evidence_collection_ref: str
    evidence_secret_ref: str
    cost_rate: Decimal
    liquidity_score: Decimal
    depth_score: Decimal
    memory_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketLiquidityDepthMemoryGuardObservation,
            "observation",
        )
        for field_name in PRIVATE_TEXT_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_private_text(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "cost_rate",
            "liquidity_score",
            "depth_score",
            "memory_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityDepthMemoryGuardRow(_FinalPublicDataclass):
    row_index: Decimal
    subject_ref: str
    venue_ref: str
    evidence_ref: str
    cost_rate: Decimal
    liquidity_score: Decimal
    depth_score: Decimal
    memory_score: Decimal
    guard_score: Decimal
    observed_at: datetime
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityDepthMemoryGuardRow, "row")
        object.__setattr__(
            self,
            "row_index",
            _require_positive_decimal("row_index", self.row_index),
        )
        _require_ref("subject_ref", self.subject_ref, "subject_ref_")
        _require_ref("venue_ref", self.venue_ref, "venue_ref_")
        _require_ref("evidence_ref", self.evidence_ref, "evidence_ref_")
        for field_name in (
            "cost_rate",
            "liquidity_score",
            "depth_score",
            "memory_score",
            "guard_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketLiquidityDepthMemoryGuardReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_cost_rate: Decimal
    min_liquidity_score: Decimal
    min_depth_score: Decimal
    min_memory_score: Decimal
    min_guard_score: Decimal
    status: str
    summary: str
    rows: tuple[ResearchMarketLiquidityDepthMemoryGuardRow, ...]
    reason_codes: tuple[str, ...]
    payload_sha256: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketLiquidityDepthMemoryGuardReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_LIQUIDITY_DEPTH_MEMORY_GUARD_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_cost_rate",
            "min_liquidity_score",
            "min_depth_score",
            "min_memory_score",
            "min_guard_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_public_text("summary", self.summary)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_sha256("payload_sha256", self.payload_sha256)
        _validate_report(self)
        _require_hard_flags("report", self)
        expected_digest = _digest_from_values(_report_values_without_digest(self))
        if self.payload_sha256 != expected_digest:
            raise ValueError("payload_sha256 does not match public payload")


def build_research_market_liquidity_depth_memory_guard_report(
    observations: Iterable[ResearchMarketLiquidityDepthMemoryGuardObservation],
    *,
    config: ResearchMarketLiquidityDepthMemoryGuardConfig | None = None,
    generated_at: datetime,
) -> ResearchMarketLiquidityDepthMemoryGuardReport:
    cfg = config or ResearchMarketLiquidityDepthMemoryGuardConfig()
    _require_exact_type(cfg, ResearchMarketLiquidityDepthMemoryGuardConfig, "config")
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    row_values = []
    for observation in observations:
        _require_exact_type(
            observation,
            ResearchMarketLiquidityDepthMemoryGuardObservation,
            "observation",
        )
        _require_hard_flags("observation", observation)
        row_values.append(_row_values_from_observation(observation, cfg))
    row_values.sort(
        key=lambda value: (
            STATUS_RANK[value["status"]],
            value["subject_ref"],
            value["venue_ref"],
            value["evidence_ref"],
        ),
    )
    rows = tuple(
        ResearchMarketLiquidityDepthMemoryGuardRow(
            row_index=_decimal_count(index),
            **values,
        )
        for index, values in enumerate(row_values, start=1)
    )
    observation_count = _decimal_count(len(rows))
    pass_count = _decimal_count(sum(row.status == "pass" for row in rows))
    watch_count = _decimal_count(sum(row.status == "watch" for row in rows))
    block_count = _decimal_count(sum(row.status == "block" for row in rows))
    status = _report_status(rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": cfg.config_version,
        "observation_count": observation_count,
        "pass_count": pass_count,
        "watch_count": watch_count,
        "block_count": block_count,
        "max_cost_rate": max((row.cost_rate for row in rows), default=ZERO),
        "min_liquidity_score": min(
            (row.liquidity_score for row in rows),
            default=ZERO,
        ),
        "min_depth_score": min((row.depth_score for row in rows), default=ZERO),
        "min_memory_score": min((row.memory_score for row in rows), default=ZERO),
        "min_guard_score": min((row.guard_score for row in rows), default=ZERO),
        "status": status,
        "summary": EMPTY_SUMMARY if not rows else STATUS_SUMMARY[status],
        "rows": rows,
        "reason_codes": _report_reason_codes(rows, status),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketLiquidityDepthMemoryGuardReport(
        **values,
        payload_sha256=_digest_from_values(values),
    )


def research_market_liquidity_depth_memory_guard_report_payload(
    report: ResearchMarketLiquidityDepthMemoryGuardReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is dict:
        validate_research_market_liquidity_depth_memory_guard_report_payload(report)
        return dict(report)
    if type(report) is not ResearchMarketLiquidityDepthMemoryGuardReport:
        raise ValueError(
            "report must be a ResearchMarketLiquidityDepthMemoryGuardReport",
        )
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    validate_research_market_liquidity_depth_memory_guard_report_payload(payload)
    return payload


def validate_research_market_liquidity_depth_memory_guard_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _require_payload_flags(payload)
    _reject_unsafe_public_surface(payload)
    _reject_public_numerics(payload)
    digest = payload.get("payload_sha256")
    _require_sha256("payload_sha256", digest)
    without_digest = dict(payload)
    without_digest.pop("payload_sha256", None)
    if digest != _payload_digest(without_digest):
        raise ValueError("payload_sha256 does not match public payload")
    return True


def _row_values_from_observation(
    observation: ResearchMarketLiquidityDepthMemoryGuardObservation,
    config: ResearchMarketLiquidityDepthMemoryGuardConfig,
) -> dict[str, object]:
    reason_codes = list(observation.reason_codes)
    status = "pass"
    if observation.cost_rate > config.max_watch_cost_rate:
        reason_codes.append("liquidity_depth_memory_guard_cost_block")
        status = "block"
    elif observation.cost_rate > config.max_pass_cost_rate:
        reason_codes.append("liquidity_depth_memory_guard_cost_watch")
        status = _max_status(status, "watch")
    if observation.liquidity_score < config.min_watch_liquidity_score:
        reason_codes.append("liquidity_depth_memory_guard_liquidity_block")
        status = "block"
    elif observation.liquidity_score < config.min_pass_liquidity_score:
        reason_codes.append("liquidity_depth_memory_guard_liquidity_watch")
        status = _max_status(status, "watch")
    if observation.depth_score < config.min_watch_depth_score:
        reason_codes.append("liquidity_depth_memory_guard_depth_block")
        status = "block"
    elif observation.depth_score < config.min_pass_depth_score:
        reason_codes.append("liquidity_depth_memory_guard_depth_watch")
        status = _max_status(status, "watch")
    if observation.memory_score < config.min_watch_memory_score:
        reason_codes.append("liquidity_depth_memory_guard_memory_block")
        status = "block"
    elif observation.memory_score < config.min_pass_memory_score:
        reason_codes.append("liquidity_depth_memory_guard_memory_watch")
        status = _max_status(status, "watch")
    if status == "pass":
        reason_codes.append(READY_REASON_CODE)
    return {
        "subject_ref": _public_ref("subject_ref", observation.raw_candidate_ref),
        "venue_ref": _public_ref("venue_ref", observation.raw_market_ref),
        "evidence_ref": _public_ref(
            "evidence_ref",
            observation.evidence_locator,
            observation.evidence_excerpt,
            observation.evidence_store_ref,
            observation.evidence_collection_ref,
            observation.evidence_secret_ref,
        ),
        "cost_rate": observation.cost_rate,
        "liquidity_score": observation.liquidity_score,
        "depth_score": observation.depth_score,
        "memory_score": observation.memory_score,
        "guard_score": {
            "pass": PASS_GUARD_SCORE,
            "watch": WATCH_GUARD_SCORE,
            "block": BLOCK_GUARD_SCORE,
        }[status],
        "observed_at": observation.observed_at,
        "status": status,
        "reason_codes": _normalize_reason_codes("reason_codes", reason_codes),
    }


def _report_status(
    rows: tuple[ResearchMarketLiquidityDepthMemoryGuardRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketLiquidityDepthMemoryGuardRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (REPORT_EMPTY_REASON_CODE,)
    row_codes = {reason_code for row in rows for reason_code in row.reason_codes}
    reason_codes = [REPORT_REASON_BY_STATUS[status]]
    reason_codes.extend(
        reason_code for reason_code in REPORT_REASON_PRIORITY if reason_code in row_codes
    )
    return _normalize_reason_codes("reason_codes", reason_codes)


def _max_status(left: str, right: str) -> str:
    return left if STATUS_RANK[left] <= STATUS_RANK[right] else right


def _validate_row(row: ResearchMarketLiquidityDepthMemoryGuardRow) -> None:
    expected_score = {
        "pass": PASS_GUARD_SCORE,
        "watch": WATCH_GUARD_SCORE,
        "block": BLOCK_GUARD_SCORE,
    }[row.status]
    if row.guard_score != expected_score:
        raise ValueError("guard_score does not match status")
    if row.status == "pass" and READY_REASON_CODE not in row.reason_codes:
        raise ValueError("pass row must include ready reason code")


def _validate_report(report: ResearchMarketLiquidityDepthMemoryGuardReport) -> None:
    if report.observation_count != _decimal_count(len(report.rows)):
        raise ValueError("observation_count does not match rows")
    if report.pass_count != _decimal_count(sum(row.status == "pass" for row in report.rows)):
        raise ValueError("pass_count does not match rows")
    if report.watch_count != _decimal_count(
        sum(row.status == "watch" for row in report.rows),
    ):
        raise ValueError("watch_count does not match rows")
    if report.block_count != _decimal_count(
        sum(row.status == "block" for row in report.rows),
    ):
        raise ValueError("block_count does not match rows")
    expected_status = _report_status(report.rows)
    if report.status != expected_status:
        raise ValueError("status does not match rows")
    expected_summary = EMPTY_SUMMARY if not report.rows else STATUS_SUMMARY[report.status]
    if report.summary != expected_summary:
        raise ValueError("summary does not match status")
    if report.reason_codes != _report_reason_codes(report.rows, report.status):
        raise ValueError("reason_codes do not match rows")
    if report.rows:
        if report.max_cost_rate != max(row.cost_rate for row in report.rows):
            raise ValueError("max_cost_rate does not match rows")
        if report.min_liquidity_score != min(
            (row.liquidity_score for row in report.rows),
        ):
            raise ValueError("min_liquidity_score does not match rows")
        if report.min_depth_score != min(row.depth_score for row in report.rows):
            raise ValueError("min_depth_score does not match rows")
        if report.min_memory_score != min(row.memory_score for row in report.rows):
            raise ValueError("min_memory_score does not match rows")
        if report.min_guard_score != min(row.guard_score for row in report.rows):
            raise ValueError("min_guard_score does not match rows")
    elif any(
        value != ZERO
        for value in (
            report.max_cost_rate,
            report.min_liquidity_score,
            report.min_depth_score,
            report.min_memory_score,
            report.min_guard_score,
        )
    ):
        raise ValueError("empty report metrics must be zero")


def _report_values_without_digest(
    report: ResearchMarketLiquidityDepthMemoryGuardReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("payload_sha256", None)
    return values


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_surface(payload)
    _reject_public_numerics(payload)
    return _payload_digest(payload)


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (tuple, list):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"{type(value).__name__} is not JSON ready")


def _public_ref(prefix: str, *parts: str) -> str:
    joined = "\x1f".join(parts)
    digest = sha256(joined.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def _normalize_rows(
    rows: Iterable[ResearchMarketLiquidityDepthMemoryGuardRow],
) -> tuple[ResearchMarketLiquidityDepthMemoryGuardRow, ...]:
    if type(rows) is str:
        raise ValueError("rows must be an iterable of rows")
    normalized = tuple(rows)
    for row in normalized:
        _require_exact_type(row, ResearchMarketLiquidityDepthMemoryGuardRow, "row")
        _require_hard_flags("row", row)
    expected_indexes = tuple(_decimal_count(index) for index in range(1, len(normalized) + 1))
    if tuple(row.row_index for row in normalized) != expected_indexes:
        raise ValueError("row_index sequence is not valid")
    if tuple(sorted(normalized, key=lambda row: (STATUS_RANK[row.status], row.subject_ref))) != normalized:
        raise ValueError("rows are not in canonical sequence")
    return normalized


def _normalize_reason_codes(field_name: str, values: Iterable[str]) -> tuple[str, ...]:
    if type(values) is str:
        raise ValueError(f"{field_name} must be an iterable of strings")
    normalized = []
    seen = set()
    for value in values:
        reason_code = _require_public_text(field_name, value)
        if reason_code not in seen:
            normalized.append(reason_code)
            seen.add(reason_code)
    return tuple(normalized)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must include timezone")
    return value.astimezone(UTC)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _decimal_count(value: int) -> Decimal:
    return Decimal(str(value)).quantize(QUANTUM)


def _require_private_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be blank")
    return normalized


def _require_public_text(field_name: str, value: object) -> str:
    normalized = _require_private_text(field_name, value)
    lowered = normalized.lower()
    if any(part in lowered for part in UNSAFE_PUBLIC_FIELD_PARTS):
        raise ValueError(f"{field_name} contains unsafe public text")
    if any(part in lowered for part in UNSAFE_PUBLIC_VALUE_PARTS):
        raise ValueError(f"{field_name} contains unsafe public text")
    return normalized


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in STATUSES:
        raise ValueError(f"{field_name} is not supported")
    return value


def _require_ref(field_name: str, value: object, prefix: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.startswith(prefix):
        raise ValueError(f"{field_name} must start with {prefix}")
    digest = value.removeprefix(prefix)
    if len(digest) != 16 or any(character not in HEX_CHARS for character in digest):
        raise ValueError(f"{field_name} must end with a 16 character hex digest")
    return value


def _require_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_exact_type(value: object, expected_type: type, label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} must be readonly")


def _require_payload_flags(payload: dict[str, Any]) -> None:
    if payload.get("paper_only") is not True:
        raise ValueError("payload must be paper_only")
    if payload.get("report_only") is not True:
        raise ValueError("payload must be report_only")
    if payload.get("readonly") is not True:
        raise ValueError("payload must be readonly")


def _reject_unsafe_public_surface(value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            lowered_key = str(key).lower()
            if any(part in lowered_key for part in UNSAFE_PUBLIC_FIELD_PARTS):
                raise ValueError("unsafe public field")
            _reject_unsafe_public_surface(item)
        return
    if type(value) is list:
        for item in value:
            _reject_unsafe_public_surface(item)
        return
    if type(value) is str:
        lowered_value = value.lower()
        if any(part in lowered_value for part in UNSAFE_PUBLIC_VALUE_PARTS):
            raise ValueError("unsafe public value")


def _reject_public_numerics(value: object) -> None:
    if type(value) is dict:
        for item in value.values():
            _reject_public_numerics(item)
        return
    if type(value) is list:
        for item in value:
            _reject_public_numerics(item)
        return
    if type(value) is bool:
        return
    if type(value) in (int, float, Decimal):
        raise ValueError("public payload numeric values must be strings")
