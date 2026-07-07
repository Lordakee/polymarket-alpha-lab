"""Read-only research watch report for market rule, settlement, and dependency changes."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import hashlib
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_MARKET_RULE_CHANGE_WATCH_CONFIG_VERSION = (
    "research-market-rule-change-watch-report-v0"
)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
AGE_SECONDS_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ZERO_AGE_SECONDS = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

WATCH_STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("2"),
    "watch": Decimal("1"),
    "pass": Decimal("0"),
}
ROW_REASON_CODES = (
    "market_rule_change_clear",
    "prediction_event_rule_changed",
    "settlement_description_changed",
    "dependency_reference_changed",
    "missing_rule_change_review",
)
REPORT_REASON_CODES = (
    "market_rule_change_watch_clear",
    "prediction_event_rule_change_present",
    "settlement_description_change_present",
    "dependency_reference_change_present",
    "missing_rule_change_review_present",
    "market_rule_change_block_present",
)
RISK_NOTES = (
    "No review-triggering rule, settlement, or dependency change observed.",
    "Prediction event rule changed; confirm event boundaries before use.",
    "Settlement description changed; confirm outcome criteria before use.",
    "Evidence dependency changed; confirm reference independence before use.",
    "Change review acknowledgement missing; keep the market in research watch.",
)
UNSAFE_PUBLIC_SURFACE_FRAGMENTS = (
    "question",
    "slug",
    "source_url",
    "source url",
    "source_text",
    "source text",
    "raw",
    "url",
    "dsn",
    "table",
    "token",
    "http://",
    "https://",
    "://",
    "postgres://",
    "mysql://",
    "sqlite://",
)
REPORT_DECIMAL_PAYLOAD_FIELDS = (
    "observed_market_count",
    "pass_market_count",
    "watch_market_count",
    "block_market_count",
    "changed_market_count",
    "unreviewed_change_count",
    "max_change_count",
    "max_change_severity",
    "max_change_age_seconds",
    "watch_ratio",
    "block_ratio",
)
ROW_DECIMAL_PAYLOAD_FIELDS = (
    "prediction_rule_change_count",
    "settlement_description_change_count",
    "dependency_reference_change_count",
    "max_change_count",
    "prediction_rule_change_severity",
    "settlement_description_change_severity",
    "dependency_reference_change_severity",
    "max_change_severity",
    "latest_change_age_seconds",
    "flag_count",
)
ROW_BOOL_PAYLOAD_FIELDS = (
    "prediction_event_rule_changed",
    "settlement_description_changed",
    "dependency_reference_changed",
    "missing_rule_change_review",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    *REPORT_DECIMAL_PAYLOAD_FIELDS,
    "status",
    "reason_codes",
    "change_rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_KEYS = (
    "market_key",
    "status",
    *ROW_DECIMAL_PAYLOAD_FIELDS,
    *ROW_BOOL_PAYLOAD_FIELDS,
    "reason_codes",
    "risk_notes",
)


@dataclass(frozen=True)
class ResearchMarketRuleChangeWatchConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_RULE_CHANGE_WATCH_CONFIG_VERSION
    watch_change_count_threshold: Decimal = Decimal("1")
    block_change_count_threshold: Decimal = Decimal("2")
    watch_change_severity_threshold: Decimal = Decimal("0.250000")
    block_change_severity_threshold: Decimal = Decimal("0.750000")
    max_unreviewed_change_age_seconds: Decimal = Decimal("86400")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketRuleChangeWatchConfig:
            raise ValueError("config must be exact")
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_MARKET_RULE_CHANGE_WATCH_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("watch_change_count_threshold", "block_change_count_threshold"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_change_severity_threshold",
            "block_change_severity_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_unreviewed_change_age_seconds",
            _normalize_nonnegative_age_seconds(
                "max_unreviewed_change_age_seconds",
                self.max_unreviewed_change_age_seconds,
            ),
        )
        if self.watch_change_count_threshold == ZERO_COUNT:
            raise ValueError("watch_change_count_threshold must be positive")
        if self.block_change_count_threshold < self.watch_change_count_threshold:
            raise ValueError(
                "block_change_count_threshold must be at least watch_change_count_threshold",
            )
        if self.block_change_severity_threshold < self.watch_change_severity_threshold:
            raise ValueError(
                "block_change_severity_threshold must be at least "
                "watch_change_severity_threshold",
            )
        require_paper_only_flags("research market rule change watch config", self)


@dataclass(frozen=True)
class ResearchMarketRuleChangeWatchInput:
    market_key: str
    prediction_rule_change_count: Decimal
    settlement_description_change_count: Decimal
    dependency_reference_change_count: Decimal
    prediction_rule_change_severity: Decimal
    settlement_description_change_severity: Decimal
    dependency_reference_change_severity: Decimal
    latest_change_observed_at: datetime
    change_review_acknowledged: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketRuleChangeWatchInput:
            raise ValueError("input must be exact")
        _require_public_identifier("market_key", self.market_key)
        for field_name in (
            "prediction_rule_change_count",
            "settlement_description_change_count",
            "dependency_reference_change_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "prediction_rule_change_severity",
            "settlement_description_change_severity",
            "dependency_reference_change_severity",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_change_observed_at",
            _as_utc("latest_change_observed_at", self.latest_change_observed_at),
        )
        if type(self.change_review_acknowledged) is not bool:
            raise ValueError("change_review_acknowledged must be a bool")
        require_paper_only_flags("research market rule change watch input", self)
        _validate_input(self)


@dataclass(frozen=True)
class ResearchMarketRuleChangeWatchRow:
    market_key: str
    status: str
    prediction_rule_change_count: Decimal
    settlement_description_change_count: Decimal
    dependency_reference_change_count: Decimal
    max_change_count: Decimal
    prediction_rule_change_severity: Decimal
    settlement_description_change_severity: Decimal
    dependency_reference_change_severity: Decimal
    max_change_severity: Decimal
    latest_change_age_seconds: Decimal
    flag_count: Decimal
    prediction_event_rule_changed: bool
    settlement_description_changed: bool
    dependency_reference_changed: bool
    missing_rule_change_review: bool
    reason_codes: tuple[str, ...]
    risk_notes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketRuleChangeWatchRow:
            raise ValueError("row must be exact")
        _require_public_identifier("market_key", self.market_key)
        _require_member("status", self.status, WATCH_STATUSES)
        for field_name in (
            "prediction_rule_change_count",
            "settlement_description_change_count",
            "dependency_reference_change_count",
            "max_change_count",
            "flag_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "prediction_rule_change_severity",
            "settlement_description_change_severity",
            "dependency_reference_change_severity",
            "max_change_severity",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_change_age_seconds",
            _normalize_nonnegative_age_seconds(
                "latest_change_age_seconds",
                self.latest_change_age_seconds,
            ),
        )
        for field_name in (
            "prediction_event_rule_changed",
            "settlement_description_changed",
            "dependency_reference_changed",
            "missing_rule_change_review",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        object.__setattr__(
            self,
            "risk_notes",
            _normalize_risk_notes(self.risk_notes),
        )
        require_paper_only_flags("research market rule change watch row", self)
        _validate_row(self)
        _reject_unsafe_public_payload("research market rule change watch row", self)


@dataclass(frozen=True)
class ResearchMarketRuleChangeWatchReport:
    generated_at: datetime
    config_version: str
    observed_market_count: Decimal
    pass_market_count: Decimal
    watch_market_count: Decimal
    block_market_count: Decimal
    changed_market_count: Decimal
    unreviewed_change_count: Decimal
    max_change_count: Decimal
    max_change_severity: Decimal
    max_change_age_seconds: Decimal
    watch_ratio: Decimal
    block_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    change_rows: tuple[ResearchMarketRuleChangeWatchRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketRuleChangeWatchReport:
            raise ValueError("report must be exact")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "observed_market_count",
            "pass_market_count",
            "watch_market_count",
            "block_market_count",
            "changed_market_count",
            "unreviewed_change_count",
            "max_change_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_change_severity",
            _normalize_ratio("max_change_severity", self.max_change_severity),
        )
        object.__setattr__(
            self,
            "max_change_age_seconds",
            _normalize_nonnegative_age_seconds(
                "max_change_age_seconds",
                self.max_change_age_seconds,
            ),
        )
        for field_name in ("watch_ratio", "block_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, WATCH_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(self, "change_rows", _normalize_rows(self.change_rows))
        require_paper_only_flags("research market rule change watch report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("research market rule change watch report", self)
        _validate_derived_validation_digest(self)


def build_research_market_rule_change_watch_report(
    inputs: list[ResearchMarketRuleChangeWatchInput]
    | tuple[ResearchMarketRuleChangeWatchInput, ...],
    *,
    config: ResearchMarketRuleChangeWatchConfig,
    generated_at: datetime,
) -> ResearchMarketRuleChangeWatchReport:
    if type(config) is not ResearchMarketRuleChangeWatchConfig:
        raise ValueError("config must be a ResearchMarketRuleChangeWatchConfig")
    require_paper_only_flags("research market rule change watch config", config)
    generated_at = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _change_row(source, config=config, generated_at=generated_at)
                for source in _normalize_inputs(inputs, generated_at)
            ),
            key=_row_sort_key,
        ),
    )
    observed_market_count = _count(len(rows))
    pass_market_count = _status_total(rows, "pass")
    watch_market_count = _status_total(rows, "watch")
    block_market_count = _status_total(rows, "block")
    changed_market_count = _count(
        sum(1 for row in rows if row.status in ("watch", "block")),
    )
    unreviewed_change_count = _flag_total(rows, "missing_rule_change_review")
    max_change_count = _max_count(row.max_change_count for row in rows)
    max_change_severity = _max_ratio(row.max_change_severity for row in rows)
    max_change_age_seconds = _max_age_seconds(
        row.latest_change_age_seconds for row in rows if row.status in ("watch", "block")
    )
    watch_ratio = _ratio(changed_market_count, observed_market_count)
    block_ratio = _ratio(block_market_count, observed_market_count)
    status = _report_status(rows)
    reason_codes = _report_reason_codes(rows)
    return ResearchMarketRuleChangeWatchReport(
        generated_at=generated_at,
        config_version=config.config_version,
        observed_market_count=observed_market_count,
        pass_market_count=pass_market_count,
        watch_market_count=watch_market_count,
        block_market_count=block_market_count,
        changed_market_count=changed_market_count,
        unreviewed_change_count=unreviewed_change_count,
        max_change_count=max_change_count,
        max_change_severity=max_change_severity,
        max_change_age_seconds=max_change_age_seconds,
        watch_ratio=watch_ratio,
        block_ratio=block_ratio,
        status=status,
        reason_codes=reason_codes,
        change_rows=rows,
        derived_validation_digest=_derived_validation_digest(
            generated_at=generated_at,
            config_version=config.config_version,
            observed_market_count=observed_market_count,
            pass_market_count=pass_market_count,
            watch_market_count=watch_market_count,
            block_market_count=block_market_count,
            changed_market_count=changed_market_count,
            unreviewed_change_count=unreviewed_change_count,
            max_change_count=max_change_count,
            max_change_severity=max_change_severity,
            max_change_age_seconds=max_change_age_seconds,
            watch_ratio=watch_ratio,
            block_ratio=block_ratio,
            status=status,
            reason_codes=reason_codes,
            change_rows=rows,
            paper_only=True,
            report_only=True,
            readonly=True,
        ),
    )


def research_market_rule_change_watch_payload(
    report: ResearchMarketRuleChangeWatchReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketRuleChangeWatchReport:
        require_paper_only_flags("research market rule change watch report", report)
        reject_unsafe_surface_fields("research market rule change watch report", report)
        _reject_unsafe_public_payload("research market rule change watch report", report)
        payload = json_ready_no_floats(report)
    elif type(report) is dict:
        reject_unsafe_surface_fields("research market rule change watch payload", report)
        _reject_unsafe_public_payload("research market rule change watch payload", report)
        payload = json_ready_no_floats(report)
    else:
        raise ValueError("report must be a ResearchMarketRuleChangeWatchReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    require_paper_only_flags("research market rule change watch payload", _DictFlags(payload))
    return payload


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


def _normalize_inputs(
    values: list[ResearchMarketRuleChangeWatchInput]
    | tuple[ResearchMarketRuleChangeWatchInput, ...],
    generated_at: datetime,
) -> tuple[ResearchMarketRuleChangeWatchInput, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(values)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMarketRuleChangeWatchInput:
            raise ValueError("inputs must contain ResearchMarketRuleChangeWatchInput values")
        require_paper_only_flags("research market rule change watch input", row)
        if row.market_key in seen:
            raise ValueError("duplicate market_key values are not allowed")
        if row.latest_change_observed_at > generated_at:
            raise ValueError("latest_change_observed_at must not be after generated_at")
        seen.add(row.market_key)
    return rows


def _change_row(
    source: ResearchMarketRuleChangeWatchInput,
    *,
    config: ResearchMarketRuleChangeWatchConfig,
    generated_at: datetime,
) -> ResearchMarketRuleChangeWatchRow:
    latest_change_age_seconds = _age_seconds(generated_at, source.latest_change_observed_at)
    prediction_event_rule_changed = _change_flag(
        source.prediction_rule_change_count,
        source.prediction_rule_change_severity,
        config=config,
    )
    settlement_description_changed = _change_flag(
        source.settlement_description_change_count,
        source.settlement_description_change_severity,
        config=config,
    )
    dependency_reference_changed = _change_flag(
        source.dependency_reference_change_count,
        source.dependency_reference_change_severity,
        config=config,
    )
    any_change = (
        prediction_event_rule_changed
        or settlement_description_changed
        or dependency_reference_changed
    )
    missing_rule_change_review = any_change and not source.change_review_acknowledged
    max_change_count = _max_count(
        (
            source.prediction_rule_change_count,
            source.settlement_description_change_count,
            source.dependency_reference_change_count,
        ),
    )
    max_change_severity = _max_ratio(
        (
            source.prediction_rule_change_severity,
            source.settlement_description_change_severity,
            source.dependency_reference_change_severity,
        ),
    )
    return ResearchMarketRuleChangeWatchRow(
        market_key=source.market_key,
        status=_row_status(
            prediction_rule_change_count=source.prediction_rule_change_count,
            settlement_description_change_count=source.settlement_description_change_count,
            dependency_reference_change_count=source.dependency_reference_change_count,
            prediction_rule_change_severity=source.prediction_rule_change_severity,
            settlement_description_change_severity=source.settlement_description_change_severity,
            dependency_reference_change_severity=source.dependency_reference_change_severity,
            latest_change_age_seconds=latest_change_age_seconds,
            prediction_event_rule_changed=prediction_event_rule_changed,
            settlement_description_changed=settlement_description_changed,
            dependency_reference_changed=dependency_reference_changed,
            missing_rule_change_review=missing_rule_change_review,
            config=config,
        ),
        prediction_rule_change_count=source.prediction_rule_change_count,
        settlement_description_change_count=source.settlement_description_change_count,
        dependency_reference_change_count=source.dependency_reference_change_count,
        max_change_count=max_change_count,
        prediction_rule_change_severity=source.prediction_rule_change_severity,
        settlement_description_change_severity=source.settlement_description_change_severity,
        dependency_reference_change_severity=source.dependency_reference_change_severity,
        max_change_severity=max_change_severity,
        latest_change_age_seconds=latest_change_age_seconds,
        flag_count=_count(
            sum(
                1
                for flag in (
                    prediction_event_rule_changed,
                    settlement_description_changed,
                    dependency_reference_changed,
                    missing_rule_change_review,
                )
                if flag
            ),
        ),
        prediction_event_rule_changed=prediction_event_rule_changed,
        settlement_description_changed=settlement_description_changed,
        dependency_reference_changed=dependency_reference_changed,
        missing_rule_change_review=missing_rule_change_review,
        reason_codes=_row_reason_codes(
            prediction_event_rule_changed=prediction_event_rule_changed,
            settlement_description_changed=settlement_description_changed,
            dependency_reference_changed=dependency_reference_changed,
            missing_rule_change_review=missing_rule_change_review,
        ),
        risk_notes=_risk_notes(
            prediction_event_rule_changed=prediction_event_rule_changed,
            settlement_description_changed=settlement_description_changed,
            dependency_reference_changed=dependency_reference_changed,
            missing_rule_change_review=missing_rule_change_review,
        ),
    )


def _change_flag(
    change_count: Decimal,
    change_severity: Decimal,
    *,
    config: ResearchMarketRuleChangeWatchConfig,
) -> bool:
    return (
        change_count >= config.watch_change_count_threshold
        or change_severity >= config.watch_change_severity_threshold
    )


def _row_status(
    *,
    prediction_rule_change_count: Decimal,
    settlement_description_change_count: Decimal,
    dependency_reference_change_count: Decimal,
    prediction_rule_change_severity: Decimal,
    settlement_description_change_severity: Decimal,
    dependency_reference_change_severity: Decimal,
    latest_change_age_seconds: Decimal,
    prediction_event_rule_changed: bool,
    settlement_description_changed: bool,
    dependency_reference_changed: bool,
    missing_rule_change_review: bool,
    config: ResearchMarketRuleChangeWatchConfig,
) -> str:
    if not (
        prediction_event_rule_changed
        or settlement_description_changed
        or dependency_reference_changed
        or missing_rule_change_review
    ):
        return "pass"
    if (
        prediction_rule_change_count >= config.block_change_count_threshold
        or settlement_description_change_count >= config.block_change_count_threshold
        or dependency_reference_change_count >= config.block_change_count_threshold
        or prediction_rule_change_severity >= config.block_change_severity_threshold
        or settlement_description_change_severity >= config.block_change_severity_threshold
        or dependency_reference_change_severity >= config.block_change_severity_threshold
    ):
        return "block"
    if (
        missing_rule_change_review
        and latest_change_age_seconds >= config.max_unreviewed_change_age_seconds
    ):
        return "block"
    return "watch"


def _row_reason_codes(
    *,
    prediction_event_rule_changed: bool,
    settlement_description_changed: bool,
    dependency_reference_changed: bool,
    missing_rule_change_review: bool,
) -> tuple[str, ...]:
    codes: list[str] = []
    if prediction_event_rule_changed:
        codes.append("prediction_event_rule_changed")
    if settlement_description_changed:
        codes.append("settlement_description_changed")
    if dependency_reference_changed:
        codes.append("dependency_reference_changed")
    if missing_rule_change_review:
        codes.append("missing_rule_change_review")
    return tuple(codes) if codes else ("market_rule_change_clear",)


def _risk_notes(
    *,
    prediction_event_rule_changed: bool,
    settlement_description_changed: bool,
    dependency_reference_changed: bool,
    missing_rule_change_review: bool,
) -> tuple[str, ...]:
    notes: list[str] = []
    if prediction_event_rule_changed:
        notes.append("Prediction event rule changed; confirm event boundaries before use.")
    if settlement_description_changed:
        notes.append("Settlement description changed; confirm outcome criteria before use.")
    if dependency_reference_changed:
        notes.append("Evidence dependency changed; confirm reference independence before use.")
    if missing_rule_change_review:
        notes.append("Change review acknowledgement missing; keep the market in research watch.")
    return tuple(notes) if notes else (RISK_NOTES[0],)


def _report_status(rows: tuple[ResearchMarketRuleChangeWatchRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketRuleChangeWatchRow, ...],
) -> tuple[str, ...]:
    if not any(row.status in ("watch", "block") for row in rows):
        return ("market_rule_change_watch_clear",)
    codes: list[str] = []
    if any(row.prediction_event_rule_changed for row in rows):
        codes.append("prediction_event_rule_change_present")
    if any(row.settlement_description_changed for row in rows):
        codes.append("settlement_description_change_present")
    if any(row.dependency_reference_changed for row in rows):
        codes.append("dependency_reference_change_present")
    if any(row.missing_rule_change_review for row in rows):
        codes.append("missing_rule_change_review_present")
    if any(row.status == "block" for row in rows):
        codes.append("market_rule_change_block_present")
    return tuple(codes)


def _row_sort_key(
    row: ResearchMarketRuleChangeWatchRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -row.flag_count,
        -row.max_change_severity,
        -row.max_change_count,
        row.market_key,
    )


def _validate_input(row: ResearchMarketRuleChangeWatchInput) -> None:
    for count_name, severity_name in (
        ("prediction_rule_change_count", "prediction_rule_change_severity"),
        ("settlement_description_change_count", "settlement_description_change_severity"),
        ("dependency_reference_change_count", "dependency_reference_change_severity"),
    ):
        if getattr(row, count_name) == ZERO_COUNT and getattr(row, severity_name) != ZERO_RATIO:
            raise ValueError(f"{severity_name} must be zero when {count_name} is zero")


def _validate_row(row: ResearchMarketRuleChangeWatchRow) -> None:
    expected_max_count = _max_count(
        (
            row.prediction_rule_change_count,
            row.settlement_description_change_count,
            row.dependency_reference_change_count,
        ),
    )
    if row.max_change_count != expected_max_count:
        raise ValueError("max_change_count must match row counts")
    expected_max_severity = _max_ratio(
        (
            row.prediction_rule_change_severity,
            row.settlement_description_change_severity,
            row.dependency_reference_change_severity,
        ),
    )
    if row.max_change_severity != expected_max_severity:
        raise ValueError("max_change_severity must match row severities")
    expected_flag_count = _count(
        sum(
            1
            for flag in (
                row.prediction_event_rule_changed,
                row.settlement_description_changed,
                row.dependency_reference_changed,
                row.missing_rule_change_review,
            )
            if flag
        ),
    )
    if row.flag_count != expected_flag_count:
        raise ValueError("flag_count must match row flags")
    expected_reason_codes = _row_reason_codes(
        prediction_event_rule_changed=row.prediction_event_rule_changed,
        settlement_description_changed=row.settlement_description_changed,
        dependency_reference_changed=row.dependency_reference_changed,
        missing_rule_change_review=row.missing_rule_change_review,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row flags")
    expected_risk_notes = _risk_notes(
        prediction_event_rule_changed=row.prediction_event_rule_changed,
        settlement_description_changed=row.settlement_description_changed,
        dependency_reference_changed=row.dependency_reference_changed,
        missing_rule_change_review=row.missing_rule_change_review,
    )
    if row.risk_notes != expected_risk_notes:
        raise ValueError("risk_notes must match row flags")
    if row.status == "pass" and row.flag_count != ZERO_COUNT:
        raise ValueError("pass rows must not have change flags")
    if row.status in ("watch", "block") and row.flag_count == ZERO_COUNT:
        raise ValueError("watch and block rows must have change flags")


def _validate_report(report: ResearchMarketRuleChangeWatchReport) -> None:
    if report.observed_market_count != _count(len(report.change_rows)):
        raise ValueError("observed_market_count must match change_rows")
    for field_name, status in (
        ("pass_market_count", "pass"),
        ("watch_market_count", "watch"),
        ("block_market_count", "block"),
    ):
        if getattr(report, field_name) != _status_total(report.change_rows, status):
            raise ValueError(f"{field_name} must match change_rows")
    if report.changed_market_count != _count(
        sum(1 for row in report.change_rows if row.status in ("watch", "block")),
    ):
        raise ValueError("changed_market_count must match change_rows")
    if report.unreviewed_change_count != _flag_total(
        report.change_rows,
        "missing_rule_change_review",
    ):
        raise ValueError("unreviewed_change_count must match change_rows")
    if report.max_change_count != _max_count(row.max_change_count for row in report.change_rows):
        raise ValueError("max_change_count must match change_rows")
    if report.max_change_severity != _max_ratio(
        row.max_change_severity for row in report.change_rows
    ):
        raise ValueError("max_change_severity must match change_rows")
    if report.max_change_age_seconds != _max_age_seconds(
        row.latest_change_age_seconds
        for row in report.change_rows
        if row.status in ("watch", "block")
    ):
        raise ValueError("max_change_age_seconds must match change_rows")
    if report.watch_ratio != _ratio(report.changed_market_count, report.observed_market_count):
        raise ValueError("watch_ratio must match counts")
    if report.block_ratio != _ratio(report.block_market_count, report.observed_market_count):
        raise ValueError("block_ratio must match counts")
    if report.status != _report_status(report.change_rows):
        raise ValueError("status must match change_rows")
    if report.reason_codes != _report_reason_codes(report.change_rows):
        raise ValueError("reason_codes must match change_rows")
    if report.change_rows != tuple(sorted(report.change_rows, key=_row_sort_key)):
        raise ValueError("change_rows must use deterministic sequence")


def _validate_derived_validation_digest(report: ResearchMarketRuleChangeWatchReport) -> None:
    _require_digest_string("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match derived report values")


def _normalize_rows(value: object) -> tuple[ResearchMarketRuleChangeWatchRow, ...]:
    if type(value) is not tuple:
        raise ValueError("change_rows must be a tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not ResearchMarketRuleChangeWatchRow:
            raise ValueError("change_rows must contain watch row values")
        require_paper_only_flags("research market rule change watch row", row)
    return rows


def _normalize_reason_codes(
    field_name: str,
    values: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(values)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
        if reason_code not in allowed:
            raise ValueError(f"{field_name} must contain known values")
    if tuple(code for code in allowed if code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _normalize_risk_notes(values: object) -> tuple[str, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("risk_notes must be a list or tuple")
    risk_notes = tuple(values)
    if not risk_notes:
        raise ValueError("risk_notes must not be empty")
    if len(set(risk_notes)) != len(risk_notes):
        raise ValueError("risk_notes must be unique")
    for risk_note in risk_notes:
        _require_canonical_string("risk_notes", risk_note)
        if risk_note not in RISK_NOTES:
            raise ValueError("risk_notes must contain public non-sensitive values")
    if tuple(note for note in RISK_NOTES if note in risk_notes) != risk_notes:
        raise ValueError("risk_notes must be deterministic")
    return risk_notes


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unknown_payload_keys("report payload", payload, REPORT_PAYLOAD_KEYS)
    _require_canonical_string("generated_at", payload["generated_at"])
    _require_canonical_string("config_version", payload["config_version"])
    if payload["config_version"] != DEFAULT_RESEARCH_MARKET_RULE_CHANGE_WATCH_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    for field_name in REPORT_DECIMAL_PAYLOAD_FIELDS:
        _require_decimal_string(field_name, payload[field_name])
    _require_member("status", payload["status"], WATCH_STATUSES)
    _normalize_reason_codes("reason_codes", payload["reason_codes"], REPORT_REASON_CODES)
    if type(payload["change_rows"]) is not list:
        raise ValueError("change_rows must be a list")
    for row in payload["change_rows"]:
        _validate_public_row_payload(row)
    _require_digest_string("derived_validation_digest", payload["derived_validation_digest"])
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    if payload["derived_validation_digest"] != _payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match payload values")


def _validate_public_row_payload(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("change_rows must contain JSON objects")
    _reject_unknown_payload_keys("watch row payload", value, ROW_PAYLOAD_KEYS)
    _require_public_identifier("market_key", value["market_key"])
    _require_member("status", value["status"], WATCH_STATUSES)
    for field_name in ROW_DECIMAL_PAYLOAD_FIELDS:
        _require_decimal_string(field_name, value[field_name])
    for field_name in ROW_BOOL_PAYLOAD_FIELDS:
        if type(value[field_name]) is not bool:
            raise ValueError(f"{field_name} must be a bool")
    for field_name in ("paper_only", "report_only", "readonly"):
        if value[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    _normalize_reason_codes("reason_codes", value["reason_codes"], ROW_REASON_CODES)
    _normalize_risk_notes(value["risk_notes"])


def _reject_unknown_payload_keys(
    label: str,
    payload: dict[str, Any],
    allowed_keys: tuple[str, ...],
) -> None:
    if tuple(payload.keys()) != allowed_keys:
        if set(payload.keys()) != set(allowed_keys):
            raise ValueError(f"{label} must use the public readonly schema")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_fragment(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_fragment(label, value)


def _reject_unsafe_fragment(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError(f"unsafe public surface in {label}")


def _require_decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use Decimal-derived string values")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must use Decimal-derived string values") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal_value


def _require_digest_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _report_derived_validation_digest(report: ResearchMarketRuleChangeWatchReport) -> str:
    return _derived_validation_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        observed_market_count=report.observed_market_count,
        pass_market_count=report.pass_market_count,
        watch_market_count=report.watch_market_count,
        block_market_count=report.block_market_count,
        changed_market_count=report.changed_market_count,
        unreviewed_change_count=report.unreviewed_change_count,
        max_change_count=report.max_change_count,
        max_change_severity=report.max_change_severity,
        max_change_age_seconds=report.max_change_age_seconds,
        watch_ratio=report.watch_ratio,
        block_ratio=report.block_ratio,
        status=report.status,
        reason_codes=report.reason_codes,
        change_rows=report.change_rows,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def _payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    return _hash_digest_parts(
        (
            str(payload["generated_at"]),
            str(payload["config_version"]),
            *(str(payload[field_name]) for field_name in REPORT_DECIMAL_PAYLOAD_FIELDS),
            str(payload["status"]),
            *tuple(str(reason_code) for reason_code in payload["reason_codes"]),
            *tuple(
                component
                for row in payload["change_rows"]
                for component in _payload_row_digest_parts(row)
            ),
            str(payload["paper_only"]),
            str(payload["report_only"]),
            str(payload["readonly"]),
        ),
    )


def _derived_validation_digest(
    *,
    generated_at: datetime,
    config_version: str,
    observed_market_count: Decimal,
    pass_market_count: Decimal,
    watch_market_count: Decimal,
    block_market_count: Decimal,
    changed_market_count: Decimal,
    unreviewed_change_count: Decimal,
    max_change_count: Decimal,
    max_change_severity: Decimal,
    max_change_age_seconds: Decimal,
    watch_ratio: Decimal,
    block_ratio: Decimal,
    status: str,
    reason_codes: tuple[str, ...],
    change_rows: tuple[ResearchMarketRuleChangeWatchRow, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> str:
    return _hash_digest_parts(
        (
            generated_at.isoformat(),
            config_version,
            str(observed_market_count),
            str(pass_market_count),
            str(watch_market_count),
            str(block_market_count),
            str(changed_market_count),
            str(unreviewed_change_count),
            str(max_change_count),
            str(max_change_severity),
            str(max_change_age_seconds),
            str(watch_ratio),
            str(block_ratio),
            status,
            *reason_codes,
            *tuple(component for row in change_rows for component in _row_digest_parts(row)),
            str(paper_only),
            str(report_only),
            str(readonly),
        ),
    )


def _row_digest_parts(row: ResearchMarketRuleChangeWatchRow) -> tuple[str, ...]:
    return (
        row.market_key,
        row.status,
        *(str(getattr(row, field_name)) for field_name in ROW_DECIMAL_PAYLOAD_FIELDS),
        str(row.prediction_event_rule_changed),
        str(row.settlement_description_changed),
        str(row.dependency_reference_changed),
        str(row.missing_rule_change_review),
        *row.reason_codes,
        *row.risk_notes,
        str(row.paper_only),
        str(row.report_only),
        str(row.readonly),
    )


def _payload_row_digest_parts(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        str(row["market_key"]),
        str(row["status"]),
        *(str(row[field_name]) for field_name in ROW_DECIMAL_PAYLOAD_FIELDS),
        str(row["prediction_event_rule_changed"]),
        str(row["settlement_description_changed"]),
        str(row["dependency_reference_changed"]),
        str(row["missing_rule_change_review"]),
        *tuple(str(reason_code) for reason_code in row["reason_codes"]),
        *tuple(str(risk_note) for risk_note in row["risk_notes"]),
        str(row["paper_only"]),
        str(row["report_only"]),
        str(row["readonly"]),
    )


def _hash_digest_parts(parts: tuple[str, ...]) -> str:
    digest = hashlib.sha256()
    for part in parts:
        encoded = part.encode("utf-8")
        digest.update(str(len(encoded)).encode("ascii"))
        digest.update(b":")
        digest.update(encoded)
        digest.update(b"|")
    return digest.hexdigest()


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _status_total(rows: tuple[ResearchMarketRuleChangeWatchRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _flag_total(rows: tuple[ResearchMarketRuleChangeWatchRow, ...], field_name: str) -> Decimal:
    return _count(sum(1 for row in rows if getattr(row, field_name)))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    _normalize_nonnegative_count("numerator", numerator)
    _normalize_nonnegative_count("denominator", denominator)
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _max_count(values: object) -> Decimal:
    maximum = ZERO_COUNT
    for value in values:
        candidate = _normalize_nonnegative_count("value", value)
        if candidate > maximum:
            maximum = candidate
    return maximum


def _max_ratio(values: object) -> Decimal:
    maximum = ZERO_RATIO
    for value in values:
        candidate = _normalize_ratio("value", value)
        if candidate > maximum:
            maximum = candidate
    return maximum


def _max_age_seconds(values: object) -> Decimal:
    maximum = ZERO_AGE_SECONDS
    for value in values:
        candidate = _normalize_nonnegative_age_seconds("value", value)
        if candidate > maximum:
            maximum = candidate
    return maximum


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    delta = generated_at - observed_at
    whole_seconds = delta.days * 86_400 + delta.seconds
    with localcontext(DECIMAL_CONTEXT):
        return (Decimal(whole_seconds) + Decimal(delta.microseconds) / Decimal(1_000_000)).quantize(
            AGE_SECONDS_QUANTUM,
        )


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    quantized = decimal_value.quantize(COUNT_QUANTUM)
    if quantized != decimal_value:
        raise ValueError(f"{field_name} must be integral")
    return quantized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_RATIO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    with localcontext(DECIMAL_CONTEXT):
        return decimal_value.quantize(RATIO_QUANTUM)


def _normalize_nonnegative_age_seconds(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_AGE_SECONDS:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return decimal_value.quantize(AGE_SECONDS_QUANTUM)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must have a UTC offset")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_public_identifier(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_fragment(field_name, value)
    if not value.startswith("market-"):
        raise ValueError(f"{field_name} must be a redacted public identifier")
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a redacted public identifier")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    _require_canonical_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


__all__ = (
    "DEFAULT_RESEARCH_MARKET_RULE_CHANGE_WATCH_CONFIG_VERSION",
    "ResearchMarketRuleChangeWatchConfig",
    "ResearchMarketRuleChangeWatchInput",
    "ResearchMarketRuleChangeWatchReport",
    "ResearchMarketRuleChangeWatchRow",
    "build_research_market_rule_change_watch_report",
    "research_market_rule_change_watch_payload",
)
