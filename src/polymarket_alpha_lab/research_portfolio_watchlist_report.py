"""Pure report-only portfolio watchlist report for manual research review."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_PORTFOLIO_WATCHLIST_REPORT_CONFIG_VERSION = (
    "research-portfolio-watchlist-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_WATCHLIST_STATUSES = frozenset(("pass", "watch", "block"))
_SORTING_BUCKETS = frozenset(("ready_queue", "watch_queue", "hold_rework"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_BLOCK_REASON_CODES = frozenset(
    (
        "snapshot_quality_block",
        "strategy_scorecard_block",
        "cost_threshold_block",
        "rule_risk_block",
        "team_capacity_block",
    ),
)
_REASON_CODE_SEQUENCE = (
    "empty_input",
    "snapshot_quality_block",
    "strategy_scorecard_block",
    "cost_threshold_block",
    "rule_risk_block",
    "team_capacity_block",
    "snapshot_quality_watch",
    "strategy_scorecard_watch",
    "cost_threshold_watch",
    "rule_risk_watch",
    "team_capacity_watch",
    "watchlist_pass",
)
_BUCKET_BY_STATUS = {
    "pass": "ready_queue",
    "watch": "watch_queue",
    "block": "hold_rework",
}
_DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
_UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "raw candidate",
    "candidate_id",
    "candidate id",
    "candidate",
    "market_id",
    "market id",
    "market",
    "slug",
    "question",
    "source_ref",
    "source-ref",
    "source ref",
    "source_url",
    "source-url",
    "source url",
    "source_text",
    "source-text",
    "source text",
    "url",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommendation",
    "http://",
    "https://",
    "://",
)


@dataclass(frozen=True)
class ResearchPortfolioWatchlistReportConfig:
    config_version: str = DEFAULT_RESEARCH_PORTFOLIO_WATCHLIST_REPORT_CONFIG_VERSION
    min_snapshot_quality_score: Decimal = Decimal("0.550000")
    pass_snapshot_quality_score: Decimal = Decimal("0.750000")
    min_strategy_scorecard_score: Decimal = Decimal("0.550000")
    pass_strategy_scorecard_score: Decimal = Decimal("0.750000")
    min_cost_score: Decimal = Decimal("0.450000")
    pass_cost_score: Decimal = Decimal("0.700000")
    watch_rule_risk_score: Decimal = Decimal("0.400000")
    block_rule_risk_score: Decimal = Decimal("0.800000")
    min_team_capacity_score: Decimal = Decimal("0.350000")
    pass_team_capacity_score: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPortfolioWatchlistReportConfig:
            raise TypeError(
                "ResearchPortfolioWatchlistReportConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPortfolioWatchlistReportConfig:
            raise ValueError(
                "config must be exactly ResearchPortfolioWatchlistReportConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PORTFOLIO_WATCHLIST_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_snapshot_quality_score",
            "pass_snapshot_quality_score",
            "min_strategy_scorecard_score",
            "pass_strategy_scorecard_score",
            "min_cost_score",
            "pass_cost_score",
            "watch_rule_risk_score",
            "block_rule_risk_score",
            "min_team_capacity_score",
            "pass_team_capacity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_snapshot_quality_score > self.pass_snapshot_quality_score:
            raise ValueError("min_snapshot_quality_score must not exceed pass threshold")
        if self.min_strategy_scorecard_score > self.pass_strategy_scorecard_score:
            raise ValueError(
                "min_strategy_scorecard_score must not exceed pass threshold",
            )
        if self.min_cost_score > self.pass_cost_score:
            raise ValueError("min_cost_score must not exceed pass threshold")
        if self.watch_rule_risk_score > self.block_rule_risk_score:
            raise ValueError("watch_rule_risk_score must not exceed block threshold")
        if self.min_team_capacity_score > self.pass_team_capacity_score:
            raise ValueError("min_team_capacity_score must not exceed pass threshold")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchPortfolioWatchlistInput:
    watchlist_item_key: str
    snapshot_quality_score: Decimal
    strategy_scorecard_score: Decimal
    cost_score: Decimal
    rule_risk_score: Decimal
    team_capacity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPortfolioWatchlistInput:
            raise TypeError("ResearchPortfolioWatchlistInput does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchPortfolioWatchlistInput:
            raise ValueError("input must be exactly ResearchPortfolioWatchlistInput")
        _require_public_identifier("watchlist_item_key", self.watchlist_item_key)
        for field_name in (
            "snapshot_quality_score",
            "strategy_scorecard_score",
            "cost_score",
            "rule_risk_score",
            "team_capacity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchPortfolioWatchlistPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPortfolioWatchlistPublicPayloadItem:
            raise TypeError(
                "ResearchPortfolioWatchlistPublicPayloadItem does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPortfolioWatchlistPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchPortfolioWatchlistPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchPortfolioWatchlistRow:
    watchlist_item_key: str
    snapshot_quality_score: Decimal
    strategy_scorecard_score: Decimal
    cost_score: Decimal
    rule_risk_score: Decimal
    rule_clearance_score: Decimal
    team_capacity_score: Decimal
    aggregate_watchlist_score: Decimal
    manual_review_priority_score: Decimal
    watchlist_status: str
    sorting_bucket: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPortfolioWatchlistRow:
            raise TypeError("ResearchPortfolioWatchlistRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchPortfolioWatchlistRow:
            raise ValueError("row must be exactly ResearchPortfolioWatchlistRow")
        _require_public_identifier("watchlist_item_key", self.watchlist_item_key)
        for field_name in (
            "snapshot_quality_score",
            "strategy_scorecard_score",
            "cost_score",
            "rule_risk_score",
            "rule_clearance_score",
            "team_capacity_score",
            "aggregate_watchlist_score",
            "manual_review_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_watchlist_status("watchlist_status", self.watchlist_status)
        _require_sorting_bucket("sorting_bucket", self.sorting_bucket)
        if self.sorting_bucket != _BUCKET_BY_STATUS[self.watchlist_status]:
            raise ValueError("sorting_bucket must match watchlist_status")
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchPortfolioWatchlistReport:
    generated_at: datetime
    config_version: str
    watchlist_status: str
    top_sorting_bucket: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_aggregate_watchlist_score: Decimal
    max_rule_risk_score: Decimal
    max_manual_review_priority_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchPortfolioWatchlistRow, ...]
    public_payload: tuple[ResearchPortfolioWatchlistPublicPayloadItem, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPortfolioWatchlistReport:
            raise TypeError("ResearchPortfolioWatchlistReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchPortfolioWatchlistReport:
            raise ValueError("report must be exactly ResearchPortfolioWatchlistReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PORTFOLIO_WATCHLIST_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_watchlist_status("watchlist_status", self.watchlist_status)
        _require_sorting_bucket("top_sorting_bucket", self.top_sorting_bucket)
        if self.top_sorting_bucket != _BUCKET_BY_STATUS[self.watchlist_status]:
            raise ValueError("top_sorting_bucket must match watchlist_status")
        for field_name in ("item_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_aggregate_watchlist_score",
            "max_rule_risk_score",
            "max_manual_review_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest mismatch")
        _require_digest("derived_validation_digest", self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, object]:
        return research_portfolio_watchlist_report_payload(self)


def build_research_portfolio_watchlist_report(
    inputs: Sequence[ResearchPortfolioWatchlistInput],
    *,
    generated_at: datetime,
    config: ResearchPortfolioWatchlistReportConfig | None = None,
    public_payload: Sequence[ResearchPortfolioWatchlistPublicPayloadItem] = (),
) -> ResearchPortfolioWatchlistReport:
    """Build a deterministic paper-only watchlist report for manual review."""

    if config is None:
        config = ResearchPortfolioWatchlistReportConfig()
    if type(config) is not ResearchPortfolioWatchlistReportConfig:
        raise ValueError("config must be a ResearchPortfolioWatchlistReportConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = _build_rows(normalized_inputs, config)
    status = _report_status(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "watchlist_status": status,
        "top_sorting_bucket": _BUCKET_BY_STATUS[status],
        "item_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_aggregate_watchlist_score": _average_ratio(
            tuple(row.aggregate_watchlist_score for row in rows),
        ),
        "max_rule_risk_score": max((row.rule_risk_score for row in rows), default=_ZERO),
        "max_manual_review_priority_score": max(
            (row.manual_review_priority_score for row in rows),
            default=_ZERO,
        ),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "public_payload": _normalize_public_payload(public_payload),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchPortfolioWatchlistReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_portfolio_watchlist_report_payload(
    value: ResearchPortfolioWatchlistReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchPortfolioWatchlistReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError("value must be a ResearchPortfolioWatchlistReport or dict")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_flag_downgrades("payload", payload)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_public_payload_digest(payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _build_rows(
    inputs: tuple[ResearchPortfolioWatchlistInput, ...],
    config: ResearchPortfolioWatchlistReportConfig,
) -> tuple[ResearchPortfolioWatchlistRow, ...]:
    return tuple(sorted((_row_for_input(item, config) for item in inputs), key=_row_sort_key))


def _row_for_input(
    item: ResearchPortfolioWatchlistInput,
    config: ResearchPortfolioWatchlistReportConfig,
) -> ResearchPortfolioWatchlistRow:
    rule_clearance_score = _quantize(_ONE - item.rule_risk_score)
    aggregate_score = _average_ratio(
        (
            item.snapshot_quality_score,
            item.strategy_scorecard_score,
            item.cost_score,
            rule_clearance_score,
            item.team_capacity_score,
        ),
    )
    reason_codes = _row_reason_codes(
        snapshot_quality_score=item.snapshot_quality_score,
        strategy_scorecard_score=item.strategy_scorecard_score,
        cost_score=item.cost_score,
        rule_risk_score=item.rule_risk_score,
        team_capacity_score=item.team_capacity_score,
        config=config,
    )
    status = _row_status(reason_codes)
    return ResearchPortfolioWatchlistRow(
        watchlist_item_key=item.watchlist_item_key,
        snapshot_quality_score=item.snapshot_quality_score,
        strategy_scorecard_score=item.strategy_scorecard_score,
        cost_score=item.cost_score,
        rule_risk_score=item.rule_risk_score,
        rule_clearance_score=rule_clearance_score,
        team_capacity_score=item.team_capacity_score,
        aggregate_watchlist_score=aggregate_score,
        manual_review_priority_score=_manual_review_priority_score(
            watchlist_status=status,
            snapshot_quality_score=item.snapshot_quality_score,
            strategy_scorecard_score=item.strategy_scorecard_score,
            cost_score=item.cost_score,
            rule_risk_score=item.rule_risk_score,
            team_capacity_score=item.team_capacity_score,
        ),
        watchlist_status=status,
        sorting_bucket=_BUCKET_BY_STATUS[status],
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    snapshot_quality_score: Decimal,
    strategy_scorecard_score: Decimal,
    cost_score: Decimal,
    rule_risk_score: Decimal,
    team_capacity_score: Decimal,
    config: ResearchPortfolioWatchlistReportConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if snapshot_quality_score < config.min_snapshot_quality_score:
        reason_codes.append("snapshot_quality_block")
    if strategy_scorecard_score < config.min_strategy_scorecard_score:
        reason_codes.append("strategy_scorecard_block")
    if cost_score < config.min_cost_score:
        reason_codes.append("cost_threshold_block")
    if rule_risk_score >= config.block_rule_risk_score:
        reason_codes.append("rule_risk_block")
    if team_capacity_score < config.min_team_capacity_score:
        reason_codes.append("team_capacity_block")
    if not any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        if snapshot_quality_score < config.pass_snapshot_quality_score:
            reason_codes.append("snapshot_quality_watch")
        if strategy_scorecard_score < config.pass_strategy_scorecard_score:
            reason_codes.append("strategy_scorecard_watch")
        if cost_score < config.pass_cost_score:
            reason_codes.append("cost_threshold_watch")
        if rule_risk_score > config.watch_rule_risk_score:
            reason_codes.append("rule_risk_watch")
        if team_capacity_score < config.pass_team_capacity_score:
            reason_codes.append("team_capacity_watch")
    return tuple(reason_codes or ("watchlist_pass",))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("watchlist_pass",):
        return "pass"
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    return "watch"


def _manual_review_priority_score(
    watchlist_status: str,
    *,
    snapshot_quality_score: Decimal,
    strategy_scorecard_score: Decimal,
    cost_score: Decimal,
    rule_risk_score: Decimal,
    team_capacity_score: Decimal,
) -> Decimal:
    base_priority = (
        (_ONE - snapshot_quality_score) * Decimal("0.125000")
        + (_ONE - strategy_scorecard_score) * Decimal("0.200000")
        + (_ONE - cost_score) * Decimal("0.150000")
        + rule_risk_score * Decimal("0.250000")
        + (_ONE - team_capacity_score) * Decimal("0.316666")
    )
    if watchlist_status == "block":
        return _clamp_ratio(base_priority + Decimal("0.500000"))
    if watchlist_status == "watch":
        return _clamp_ratio(base_priority + Decimal("0.250000"))
    return _clamp_ratio(base_priority)


def _report_status(rows: tuple[ResearchPortfolioWatchlistRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.watchlist_status == "block" for row in rows):
        return "block"
    if any(row.watchlist_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[ResearchPortfolioWatchlistRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("empty_input",)
    reason_codes: list[str] = []
    for code in _REASON_CODE_SEQUENCE:
        if any(code in row.reason_codes for row in rows):
            reason_codes.append(code)
    return tuple(reason_codes)


def _status_count(rows: tuple[ResearchPortfolioWatchlistRow, ...], status: str) -> int:
    return len(tuple(row for row in rows if row.watchlist_status == status))


def _validate_row_consistency(row: ResearchPortfolioWatchlistRow) -> None:
    expected_status = _row_status(row.reason_codes)
    if row.watchlist_status != expected_status:
        raise ValueError("watchlist_status must match reason_codes")


def _validate_report_consistency(report: ResearchPortfolioWatchlistReport) -> None:
    if report.item_count != _decimal_count(len(report.rows)):
        raise ValueError("item_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    expected_average = _average_ratio(
        tuple(row.aggregate_watchlist_score for row in report.rows),
    )
    if report.average_aggregate_watchlist_score != expected_average:
        raise ValueError("average_aggregate_watchlist_score must match rows")
    expected_max_rule_risk = max((row.rule_risk_score for row in report.rows), default=_ZERO)
    if report.max_rule_risk_score != expected_max_rule_risk:
        raise ValueError("max_rule_risk_score must match rows")
    expected_max_priority = max(
        (row.manual_review_priority_score for row in report.rows),
        default=_ZERO,
    )
    if report.max_manual_review_priority_score != expected_max_priority:
        raise ValueError("max_manual_review_priority_score must match rows")
    if report.watchlist_status != _report_status(report.rows):
        raise ValueError("watchlist_status must match rows")
    if report.top_sorting_bucket != _BUCKET_BY_STATUS[report.watchlist_status]:
        raise ValueError("top_sorting_bucket must match watchlist_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_inputs(
    inputs: Sequence[ResearchPortfolioWatchlistInput],
) -> tuple[ResearchPortfolioWatchlistInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    for item in normalized:
        if type(item) is not ResearchPortfolioWatchlistInput:
            raise ValueError("inputs items must be ResearchPortfolioWatchlistInput")
        _require_hard_flags("input", item)
    item_keys = tuple(item.watchlist_item_key for item in normalized)
    if len(set(item_keys)) != len(item_keys):
        raise ValueError("watchlist_item_key values must be unique")
    return normalized


def _normalize_rows(
    rows: tuple[ResearchPortfolioWatchlistRow, ...],
) -> tuple[ResearchPortfolioWatchlistRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchPortfolioWatchlistRow:
            raise ValueError("rows items must be ResearchPortfolioWatchlistRow")
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic watchlist ordering")
    item_keys = tuple(row.watchlist_item_key for row in normalized)
    if len(set(item_keys)) != len(item_keys):
        raise ValueError("row watchlist_item_key values must be unique")
    return normalized


def _normalize_public_payload(
    public_payload: Sequence[ResearchPortfolioWatchlistPublicPayloadItem],
) -> tuple[ResearchPortfolioWatchlistPublicPayloadItem, ...]:
    if type(public_payload) not in (list, tuple):
        raise ValueError("public_payload must be a list or tuple")
    normalized = tuple(public_payload)
    for item in normalized:
        if type(item) is not ResearchPortfolioWatchlistPublicPayloadItem:
            raise ValueError(
                "public_payload items must be ResearchPortfolioWatchlistPublicPayloadItem",
            )
        _require_hard_flags("public payload item", item)
    keys = tuple(item.key for item in normalized)
    if keys != tuple(sorted(keys)):
        raise ValueError("public_payload must be sorted by key")
    if len(set(keys)) != len(keys):
        raise ValueError("public_payload keys must be unique")
    return normalized


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        if type(reason_code) is not str or reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must contain known reason codes")
    expected_order = tuple(code for code in _REASON_CODE_SEQUENCE if code in normalized)
    if normalized != expected_order:
        raise ValueError("reason_codes must use canonical ordering")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return normalized


def _row_sort_key(row: ResearchPortfolioWatchlistRow) -> tuple[int, Decimal, str]:
    status_weight = {"block": 0, "watch": 1, "pass": 2}
    return (
        status_weight[row.watchlist_status],
        -row.manual_review_priority_score,
        row.watchlist_item_key,
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public detail")


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical public text")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public detail")
    return value


def _require_watchlist_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _WATCHLIST_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_sorting_bucket(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _SORTING_BUCKETS:
        raise ValueError(f"{field_name} must be a supported sorting bucket")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return decimal_value


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _clamp_ratio(sum(values, _ZERO) / _decimal_count(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(max(_quantize(value), _ZERO), _ONE)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext() as context:
            context.rounding = ROUND_HALF_UP
            return value.quantize(_QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _report_payload_without_digest(
    *,
    generated_at: datetime,
    config_version: str,
    watchlist_status: str,
    top_sorting_bucket: str,
    item_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    average_aggregate_watchlist_score: Decimal,
    max_rule_risk_score: Decimal,
    max_manual_review_priority_score: Decimal,
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchPortfolioWatchlistRow, ...],
    public_payload: tuple[ResearchPortfolioWatchlistPublicPayloadItem, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> dict[str, object]:
    return {
        "generated_at": _json_ready(generated_at),
        "config_version": config_version,
        "watchlist_status": watchlist_status,
        "top_sorting_bucket": top_sorting_bucket,
        "item_count": _json_ready(item_count),
        "pass_count": _json_ready(pass_count),
        "watch_count": _json_ready(watch_count),
        "block_count": _json_ready(block_count),
        "average_aggregate_watchlist_score": _json_ready(
            average_aggregate_watchlist_score,
        ),
        "max_rule_risk_score": _json_ready(max_rule_risk_score),
        "max_manual_review_priority_score": _json_ready(
            max_manual_review_priority_score,
        ),
        "reason_codes": list(reason_codes),
        "rows": [_row_payload(row) for row in rows],
        "public_payload": [_public_payload_item_payload(item) for item in public_payload],
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }


def _row_payload(row: ResearchPortfolioWatchlistRow) -> dict[str, object]:
    return {
        "watchlist_item_key": row.watchlist_item_key,
        "snapshot_quality_score": _json_ready(row.snapshot_quality_score),
        "strategy_scorecard_score": _json_ready(row.strategy_scorecard_score),
        "cost_score": _json_ready(row.cost_score),
        "rule_risk_score": _json_ready(row.rule_risk_score),
        "rule_clearance_score": _json_ready(row.rule_clearance_score),
        "team_capacity_score": _json_ready(row.team_capacity_score),
        "aggregate_watchlist_score": _json_ready(row.aggregate_watchlist_score),
        "manual_review_priority_score": _json_ready(row.manual_review_priority_score),
        "watchlist_status": row.watchlist_status,
        "sorting_bucket": row.sorting_bucket,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _public_payload_item_payload(
    item: ResearchPortfolioWatchlistPublicPayloadItem,
) -> dict[str, object]:
    return {
        "key": item.key,
        "value": item.value,
        "paper_only": item.paper_only,
        "report_only": item.report_only,
        "readonly": item.readonly,
    }


def _report_payload(report: ResearchPortfolioWatchlistReport) -> dict[str, object]:
    payload = _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        watchlist_status=report.watchlist_status,
        top_sorting_bucket=report.top_sorting_bucket,
        item_count=report.item_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_aggregate_watchlist_score=report.average_aggregate_watchlist_score,
        max_rule_risk_score=report.max_rule_risk_score,
        max_manual_review_priority_score=report.max_manual_review_priority_score,
        reason_codes=report.reason_codes,
        rows=report.rows,
        public_payload=report.public_payload,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    payload[_DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
    return payload


def _report_digest(report: ResearchPortfolioWatchlistReport) -> str:
    return _report_digest_from_values(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "watchlist_status": report.watchlist_status,
            "top_sorting_bucket": report.top_sorting_bucket,
            "item_count": report.item_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "average_aggregate_watchlist_score": (
                report.average_aggregate_watchlist_score
            ),
            "max_rule_risk_score": report.max_rule_risk_score,
            "max_manual_review_priority_score": (
                report.max_manual_review_priority_score
            ),
            "reason_codes": report.reason_codes,
            "rows": report.rows,
            "public_payload": report.public_payload,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _report_digest_from_values(values: dict[str, object]) -> str:
    payload = _report_payload_without_digest(
        generated_at=_require_mapping_value(values, "generated_at", datetime),
        config_version=_require_mapping_value(values, "config_version", str),
        watchlist_status=_require_mapping_value(values, "watchlist_status", str),
        top_sorting_bucket=_require_mapping_value(values, "top_sorting_bucket", str),
        item_count=_require_mapping_value(values, "item_count", Decimal),
        pass_count=_require_mapping_value(values, "pass_count", Decimal),
        watch_count=_require_mapping_value(values, "watch_count", Decimal),
        block_count=_require_mapping_value(values, "block_count", Decimal),
        average_aggregate_watchlist_score=_require_mapping_value(
            values,
            "average_aggregate_watchlist_score",
            Decimal,
        ),
        max_rule_risk_score=_require_mapping_value(
            values,
            "max_rule_risk_score",
            Decimal,
        ),
        max_manual_review_priority_score=_require_mapping_value(
            values,
            "max_manual_review_priority_score",
            Decimal,
        ),
        reason_codes=_require_mapping_value(values, "reason_codes", tuple),
        rows=_require_mapping_value(values, "rows", tuple),
        public_payload=_require_mapping_value(values, "public_payload", tuple),
        paper_only=_require_mapping_value(values, "paper_only", bool),
        report_only=_require_mapping_value(values, "report_only", bool),
        readonly=_require_mapping_value(values, "readonly", bool),
    )
    return _digest_payload(payload)


def _require_mapping_value(
    values: dict[str, object],
    key: str,
    expected_type: type,
) -> Any:
    value = values[key]
    if type(value) is not expected_type:
        raise ValueError(f"{key} must be {expected_type.__name__}")
    return value


def _validate_public_payload_digest(payload: dict[str, object]) -> None:
    if _DERIVED_VALIDATION_DIGEST_FIELD not in payload:
        raise ValueError("derived_validation_digest is required")
    _require_digest(
        _DERIVED_VALIDATION_DIGEST_FIELD,
        payload[_DERIVED_VALIDATION_DIGEST_FIELD],
    )
    digest_payload = dict(payload)
    digest_payload.pop(_DERIVED_VALIDATION_DIGEST_FIELD)
    if payload[_DERIVED_VALIDATION_DIGEST_FIELD] != _digest_payload(digest_payload):
        raise ValueError("derived_validation_digest mismatch")


def _digest_payload(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> Any:
    if type(value) is ResearchPortfolioWatchlistReport:
        return _report_payload(value)
    if type(value) is ResearchPortfolioWatchlistRow:
        return _row_payload(value)
    if type(value) is ResearchPortfolioWatchlistPublicPayloadItem:
        return _public_payload_item_payload(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return _copy_json_object(value)
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    raise ValueError("value is not JSON-ready")


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied: dict[str, object] = {}
    for key, nested_value in value.items():
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        copied[key] = _copy_json_value(nested_value)
    return copied


def _copy_json_value(value: object) -> object:
    if type(value) is dict:
        return _copy_json_object(value)
    if type(value) is list:
        return [_copy_json_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, Decimal):
        raise ValueError("JSON payload values must serialize Decimal values as strings")
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON payload numeric values must be strings")
    raise ValueError("JSON payload value is not supported")


def _reject_flag_downgrades(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True for {label}")
            _reject_flag_downgrades(label, item)
        return
    if type(value) is list:
        for item in value:
            _reject_flag_downgrades(label, item)


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if _has_unsafe_public_fragment(field.name):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_payload(label, getattr(value, field.name))
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if type(value) is dict:
        if not allow_json_containers:
            raise ValueError(f"{label} must not contain raw dict values")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.casefold()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_PORTFOLIO_WATCHLIST_REPORT_CONFIG_VERSION",
    "ResearchPortfolioWatchlistInput",
    "ResearchPortfolioWatchlistPublicPayloadItem",
    "ResearchPortfolioWatchlistReport",
    "ResearchPortfolioWatchlistReportConfig",
    "ResearchPortfolioWatchlistRow",
    "build_research_portfolio_watchlist_report",
    "research_portfolio_watchlist_report_payload",
)
