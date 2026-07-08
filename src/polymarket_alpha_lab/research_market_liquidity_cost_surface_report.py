"""Public, paper-only liquidity cost surface report."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_MARKET_LIQUIDITY_COST_SURFACE_REPORT_CONFIG_VERSION = (
    "research-market-liquidity-cost-surface-report-v0"
)
RATIO_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO_RATIO = Decimal("0").quantize(RATIO_QUANTUM)
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
DECIMAL_CONTEXT_PRECISION = 28
PUBLIC_STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
BASE_REASON_CODES = (
    "no_liquidity_cost_surface_observations",
    "liquidity_cost_surface_block",
    "liquidity_cost_surface_watch",
    "liquidity_cost_surface_pass",
    "manual_review_required",
    "settlement_wait_block",
    "settlement_wait_watch",
    "source_missing",
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "candidate",
    "market_id",
    "market-slug",
    "market_slug",
    "question",
    "source_ref",
    "source_reference",
    "source_url",
    "source_text",
    "url",
    "table",
    "d" + "sn",
    "tok" + "en",
    "wal" + "let",
    "au" + "th",
    "or" + "der_id",
    "or" + "der_ref",
    "tra" + "de",
    "pos" + "ition",
    "buy",
    "sell",
    "recommend",
)


@dataclass(frozen=True)
class LiquidityCostSurfaceConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_LIQUIDITY_COST_SURFACE_REPORT_CONFIG_VERSION
    )
    watch_total_cost_threshold: Decimal = Decimal("0.030000")
    block_total_cost_threshold: Decimal = Decimal("0.060000")
    watch_settlement_wait_seconds: Decimal = Decimal("3600")
    block_settlement_wait_seconds: Decimal = Decimal("86400")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, LiquidityCostSurfaceConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        for field_name in ("watch_total_cost_threshold", "block_total_cost_threshold"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_settlement_wait_seconds",
            "block_settlement_wait_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.watch_total_cost_threshold >= self.block_total_cost_threshold:
            raise ValueError(
                "watch_total_cost_threshold must be below block_total_cost_threshold",
            )
        if self.watch_settlement_wait_seconds >= self.block_settlement_wait_seconds:
            raise ValueError(
                "watch_settlement_wait_seconds must be below "
                "block_settlement_wait_seconds",
            )
        require_paper_only_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class LiquidityCostSurfaceObservation:
    public_surface_key: str
    observed_at: datetime
    fee_rate: Decimal
    spread_cost: Decimal
    depth_cost: Decimal
    slippage_cost: Decimal
    settlement_wait_seconds: Decimal
    manual_review_required: bool = False
    source_missing: bool = False
    upstream_reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, LiquidityCostSurfaceObservation, "observation")
        _require_public_identifier("public_surface_key", self.public_surface_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "fee_rate",
            "spread_cost",
            "depth_cost",
            "slippage_cost",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "settlement_wait_seconds",
            _normalize_nonnegative_count(
                "settlement_wait_seconds",
                self.settlement_wait_seconds,
            ),
        )
        _require_bool("manual_review_required", self.manual_review_required)
        _require_bool("source_missing", self.source_missing)
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_public_reason_codes(
                "upstream_reason_codes",
                self.upstream_reason_codes,
                allow_empty=True,
            ),
        )
        require_paper_only_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class LiquidityCostSurfaceRow:
    public_surface_key: str
    observed_at: datetime
    fee_rate: Decimal
    spread_cost: Decimal
    depth_cost: Decimal
    slippage_cost: Decimal
    total_cost: Decimal
    settlement_wait_seconds: Decimal
    manual_review_required: bool
    source_missing: bool
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, LiquidityCostSurfaceRow, "row")
        _require_public_identifier("public_surface_key", self.public_surface_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "fee_rate",
            "spread_cost",
            "depth_cost",
            "slippage_cost",
            "total_cost",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "settlement_wait_seconds",
            _normalize_nonnegative_count(
                "settlement_wait_seconds",
                self.settlement_wait_seconds,
            ),
        )
        _require_bool("manual_review_required", self.manual_review_required)
        _require_bool("source_missing", self.source_missing)
        _require_member("status", self.status, PUBLIC_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_public_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
            ),
        )
        _validate_row(self)
        require_paper_only_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class LiquidityCostSurfaceReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_total_cost: Decimal
    max_settlement_wait_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[LiquidityCostSurfaceRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, LiquidityCostSurfaceReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "max_settlement_wait_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_total_cost",
            _normalize_nonnegative_ratio("max_total_cost", self.max_total_cost),
        )
        _require_member("status", self.status, PUBLIC_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_public_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        require_paper_only_flags("report", self)
        _validate_report(self)
        reject_unsafe_surface_fields("liquidity cost surface report", self)
        _reject_unsafe_public_payload("report", self)
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        if self.derived_validation_digest != _report_derived_validation_digest(self):
            raise ValueError("derived_validation_digest must match report fields")

    @property
    def payload(self) -> dict[str, Any]:
        return research_market_liquidity_cost_surface_report_payload(self)


@dataclass(frozen=True)
class LiquidityCostSurfaceReportDigest:
    generated_at: datetime
    config_version: str
    report_digest: str
    report_status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_total_cost: Decimal
    max_settlement_wait_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, LiquidityCostSurfaceReportDigest, "digest")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        _require_sha256_digest("report_digest", self.report_digest)
        _require_member("report_status", self.report_status, PUBLIC_STATUSES)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "max_settlement_wait_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_total_cost",
            _normalize_nonnegative_ratio("max_total_cost", self.max_total_cost),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_public_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
            ),
        )
        require_paper_only_flags("digest", self)
        reject_unsafe_surface_fields("liquidity cost surface digest", self)
        _reject_unsafe_public_payload("digest", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_market_liquidity_cost_surface_report_payload(self)


def build_research_market_liquidity_cost_surface_report(
    observations: tuple[LiquidityCostSurfaceObservation, ...]
    | list[LiquidityCostSurfaceObservation],
    *,
    config: LiquidityCostSurfaceConfig,
    generated_at: datetime,
) -> LiquidityCostSurfaceReport:
    if type(config) is not LiquidityCostSurfaceConfig:
        raise ValueError("config must be a LiquidityCostSurfaceConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations, generated_at_utc)
    rows = tuple(sorted((_row_for_observation(item, config) for item in normalized), key=_row_key))
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "input_count": _count(len(normalized)),
        "row_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "blocked_count": _status_count(rows, "block"),
        "max_total_cost": _max_ratio(rows, "total_cost"),
        "max_settlement_wait_seconds": _max_count(rows, "settlement_wait_seconds"),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return LiquidityCostSurfaceReport(
        **values,
        derived_validation_digest=_derived_validation_digest(values),
    )


def research_market_liquidity_cost_surface_report_payload(
    value: LiquidityCostSurfaceReport | LiquidityCostSurfaceReportDigest | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is LiquidityCostSurfaceReport:
        require_paper_only_flags("report", value)
        if value.derived_validation_digest != _report_derived_validation_digest(value):
            raise ValueError("derived_validation_digest must match report fields")
        payload = json_ready_no_floats(value)
    elif type(value) is LiquidityCostSurfaceReportDigest:
        require_paper_only_flags("digest", value)
        payload = json_ready_no_floats(value)
    elif type(value) is dict:
        payload = json_ready_no_floats(value)
    else:
        raise ValueError(
            "value must be a LiquidityCostSurfaceReport or "
            "LiquidityCostSurfaceReportDigest",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    require_paper_only_flags("payload", _DictFlags(payload))
    reject_unsafe_surface_fields("liquidity cost surface payload", payload)
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_market_liquidity_cost_surface_report_digest(
    report: LiquidityCostSurfaceReport,
) -> LiquidityCostSurfaceReportDigest:
    if type(report) is not LiquidityCostSurfaceReport:
        raise ValueError("report must be a LiquidityCostSurfaceReport")
    require_paper_only_flags("report", report)
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")
    return LiquidityCostSurfaceReportDigest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        report_digest=report.derived_validation_digest,
        report_status=report.status,
        input_count=report.input_count,
        row_count=report.row_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        max_total_cost=report.max_total_cost,
        max_settlement_wait_seconds=report.max_settlement_wait_seconds,
        reason_codes=report.reason_codes,
    )


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


def _row_for_observation(
    observation: LiquidityCostSurfaceObservation,
    config: LiquidityCostSurfaceConfig,
) -> LiquidityCostSurfaceRow:
    total_cost = _total_cost(observation)
    status = _row_status(
        total_cost=total_cost,
        settlement_wait_seconds=observation.settlement_wait_seconds,
        manual_review_required=observation.manual_review_required,
        source_missing=observation.source_missing,
        config=config,
    )
    return LiquidityCostSurfaceRow(
        public_surface_key=observation.public_surface_key,
        observed_at=observation.observed_at,
        fee_rate=observation.fee_rate,
        spread_cost=observation.spread_cost,
        depth_cost=observation.depth_cost,
        slippage_cost=observation.slippage_cost,
        total_cost=total_cost,
        settlement_wait_seconds=observation.settlement_wait_seconds,
        manual_review_required=observation.manual_review_required,
        source_missing=observation.source_missing,
        status=status,
        reason_codes=_row_reason_codes(
            observation.upstream_reason_codes,
            status=status,
            settlement_wait_seconds=observation.settlement_wait_seconds,
            manual_review_required=observation.manual_review_required,
            source_missing=observation.source_missing,
            config=config,
        ),
    )


def _total_cost(observation: LiquidityCostSurfaceObservation) -> Decimal:
    with localcontext() as context:
        context.prec = DECIMAL_CONTEXT_PRECISION
        value = (
            observation.fee_rate
            + observation.spread_cost
            + observation.depth_cost
            + observation.slippage_cost
        )
    return _normalize_nonnegative_ratio("total_cost", value)


def _row_status(
    *,
    total_cost: Decimal,
    settlement_wait_seconds: Decimal,
    manual_review_required: bool,
    source_missing: bool,
    config: LiquidityCostSurfaceConfig,
) -> str:
    if (
        total_cost >= config.block_total_cost_threshold
        or settlement_wait_seconds >= config.block_settlement_wait_seconds
        or manual_review_required
        or source_missing
    ):
        return "block"
    if (
        total_cost >= config.watch_total_cost_threshold
        or settlement_wait_seconds >= config.watch_settlement_wait_seconds
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    status: str,
    settlement_wait_seconds: Decimal,
    manual_review_required: bool,
    source_missing: bool,
    config: LiquidityCostSurfaceConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = [f"liquidity_cost_surface_{status}"]
    reason_codes.extend(f"input_{code}" for code in upstream_reason_codes)
    if manual_review_required:
        reason_codes.append("manual_review_required")
    if settlement_wait_seconds >= config.block_settlement_wait_seconds:
        reason_codes.append("settlement_wait_block")
    elif settlement_wait_seconds >= config.watch_settlement_wait_seconds:
        reason_codes.append("settlement_wait_watch")
    if source_missing:
        reason_codes.append("source_missing")
    return _normalize_public_reason_codes(
        "reason_codes",
        tuple(reason_codes),
        allow_empty=False,
    )


def _report_status(rows: tuple[LiquidityCostSurfaceRow, ...]) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[LiquidityCostSurfaceRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("no_liquidity_cost_surface_observations",)
    codes: list[str] = []
    status = _report_status(rows)
    codes.append(f"liquidity_cost_surface_{status}")
    if any(row.manual_review_required for row in rows):
        codes.append("manual_review_required")
    if any("settlement_wait_block" in row.reason_codes for row in rows):
        codes.append("settlement_wait_block")
    elif any("settlement_wait_watch" in row.reason_codes for row in rows):
        codes.append("settlement_wait_watch")
    if any(row.source_missing for row in rows):
        codes.append("source_missing")
    return _normalize_public_reason_codes(
        "reason_codes",
        tuple(codes),
        allow_empty=False,
    )


def _normalize_observations(
    observations: tuple[LiquidityCostSurfaceObservation, ...]
    | list[LiquidityCostSurfaceObservation],
    generated_at: datetime,
) -> tuple[LiquidityCostSurfaceObservation, ...]:
    if type(observations) not in (list, tuple):
        raise ValueError("observations must be a list or tuple")
    normalized = tuple(observations)
    seen_keys: set[str] = set()
    for item in normalized:
        if type(item) is not LiquidityCostSurfaceObservation:
            raise ValueError(
                "observations must contain LiquidityCostSurfaceObservation values",
            )
        require_paper_only_flags("observation", item)
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        if item.public_surface_key in seen_keys:
            raise ValueError("observations must contain unique public_surface_key values")
        seen_keys.add(item.public_surface_key)
    return normalized


def _normalize_rows(value: object) -> tuple[LiquidityCostSurfaceRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not LiquidityCostSurfaceRow:
            raise ValueError("rows must contain LiquidityCostSurfaceRow values")
        require_paper_only_flags("row", row)
    return tuple(sorted(rows, key=_row_key))


def _row_key(row: LiquidityCostSurfaceRow) -> tuple[int, Decimal, Decimal, str]:
    return (
        STATUS_WEIGHT[row.status],
        -row.total_cost,
        -row.settlement_wait_seconds,
        row.public_surface_key,
    )


def _status_count(rows: tuple[LiquidityCostSurfaceRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _max_ratio(rows: tuple[LiquidityCostSurfaceRow, ...], field_name: str) -> Decimal:
    if not rows:
        return ZERO_RATIO
    return _normalize_nonnegative_ratio(
        field_name,
        max(getattr(row, field_name) for row in rows),
    )


def _max_count(rows: tuple[LiquidityCostSurfaceRow, ...], field_name: str) -> Decimal:
    if not rows:
        return ZERO_COUNT
    return _normalize_nonnegative_count(
        field_name,
        max(getattr(row, field_name) for row in rows),
    )


def _validate_row(row: LiquidityCostSurfaceRow) -> None:
    expected_total = _normalize_nonnegative_ratio(
        "total_cost",
        row.fee_rate + row.spread_cost + row.depth_cost + row.slippage_cost,
    )
    if row.total_cost != expected_total:
        raise ValueError("total_cost must match component costs")
    if f"liquidity_cost_surface_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must match status")


def _validate_report(report: LiquidityCostSurfaceReport) -> None:
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.input_count != report.row_count:
        raise ValueError("input_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "block"):
        raise ValueError("blocked_count must match rows")
    if report.max_total_cost != _max_ratio(report.rows, "total_cost"):
        raise ValueError("max_total_cost must match rows")
    if report.max_settlement_wait_seconds != _max_count(
        report.rows,
        "settlement_wait_seconds",
    ):
        raise ValueError("max_settlement_wait_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.rows != tuple(sorted(report.rows, key=_row_key)):
        raise ValueError("rows must be deterministic")


def _report_derived_validation_digest(report: LiquidityCostSurfaceReport) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return _derived_validation_digest(values)


def _derived_validation_digest(values: dict[str, object]) -> str:
    ready = json_ready_no_floats(values)
    reject_unsafe_surface_fields("liquidity cost surface digest", ready)
    _reject_unsafe_public_payload("digest", ready)
    canonical = json.dumps(
        ready,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize_public_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    codes = tuple(value)
    if not allow_empty and not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        _require_public_identifier(field_name, code)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must be unique")
    if field_name == "upstream_reason_codes":
        if tuple(sorted(codes)) != codes:
            raise ValueError(f"{field_name} must be deterministic")
        return codes
    base_codes = tuple(code for code in codes if not code.startswith("input_"))
    if tuple(code for code in BASE_REASON_CODES if code in base_codes) != base_codes:
        raise ValueError(f"{field_name} must be deterministic")
    input_codes = tuple(code for code in codes if code.startswith("input_"))
    if tuple(sorted(input_codes)) != input_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return codes


def _normalize_nonnegative_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value, quantum=RATIO_QUANTUM)
    if decimal_value < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value, quantum=COUNT_QUANTUM)
    if decimal_value != value:
        raise ValueError(f"{field_name} must be integral")
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_decimal(field_name: str, value: object, *, quantum: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(quantum)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    for character in value:
        if not (
            character.islower()
            or character.isdigit()
            or character in ("-", "_")
        ):
            raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_string(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)


def _reject_unsafe_public_string(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"unsafe public value in {label}")


__all__ = (
    "DEFAULT_RESEARCH_MARKET_LIQUIDITY_COST_SURFACE_REPORT_CONFIG_VERSION",
    "LiquidityCostSurfaceConfig",
    "LiquidityCostSurfaceObservation",
    "LiquidityCostSurfaceRow",
    "LiquidityCostSurfaceReport",
    "LiquidityCostSurfaceReportDigest",
    "build_research_market_liquidity_cost_surface_report",
    "research_market_liquidity_cost_surface_report_payload",
    "research_market_liquidity_cost_surface_report_digest",
)
