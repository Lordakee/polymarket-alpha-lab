"""Pure expiry-risk reporting for caller-supplied research event rows."""

from __future__ import annotations

from collections import Counter
from dataclasses import InitVar, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "ResearchEventExpiryRiskConfig",
    "ResearchEventExpiryRiskInputRow",
    "ResearchEventExpiryRiskReasonCodeCount",
    "ResearchEventExpiryRiskReport",
    "ResearchEventExpiryRiskRow",
    "build_research_event_expiry_risk_report",
    "research_event_expiry_risk_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-event-expiry-risk-report-v0"
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")


@dataclass(frozen=True)
class ResearchEventExpiryRiskConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    expiry_watch_window_seconds: Decimal = Decimal("86400")
    expiry_block_window_seconds: Decimal = Decimal("3600")
    fresh_information_max_age_seconds: Decimal = Decimal("1800")
    stale_information_block_age_seconds: Decimal = Decimal("7200")
    settlement_evidence_stale_age_seconds: Decimal = Decimal("14400")
    min_settlement_evidence_count: Decimal = Decimal("2")
    min_settlement_evidence_family_count: Decimal = Decimal("2")
    liquidity_pass_threshold: Decimal = Decimal("0.500000")
    liquidity_block_threshold: Decimal = Decimal("0.200000")
    rule_ambiguity_watch_threshold: Decimal = Decimal("0.250000")
    rule_ambiguity_block_threshold: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventExpiryRiskConfig:
            raise TypeError("ResearchEventExpiryRiskConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventExpiryRiskConfig:
            raise ValueError("config must be exactly ResearchEventExpiryRiskConfig")
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "expiry_watch_window_seconds",
            "expiry_block_window_seconds",
            "fresh_information_max_age_seconds",
            "stale_information_block_age_seconds",
            "settlement_evidence_stale_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.expiry_block_window_seconds >= self.expiry_watch_window_seconds:
            raise ValueError(
                "expiry_watch_window_seconds must exceed expiry_block_window_seconds",
            )
        if self.fresh_information_max_age_seconds >= self.stale_information_block_age_seconds:
            raise ValueError(
                "stale_information_block_age_seconds must exceed "
                "fresh_information_max_age_seconds",
            )
        for field_name in (
            "min_settlement_evidence_count",
            "min_settlement_evidence_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_settlement_evidence_family_count > self.min_settlement_evidence_count:
            raise ValueError(
                "min_settlement_evidence_family_count must not exceed "
                "min_settlement_evidence_count",
            )
        for field_name in (
            "liquidity_pass_threshold",
            "liquidity_block_threshold",
            "rule_ambiguity_watch_threshold",
            "rule_ambiguity_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.liquidity_block_threshold >= self.liquidity_pass_threshold:
            raise ValueError(
                "liquidity_pass_threshold must exceed liquidity_block_threshold",
            )
        if self.rule_ambiguity_watch_threshold >= self.rule_ambiguity_block_threshold:
            raise ValueError(
                "rule_ambiguity_block_threshold must exceed "
                "rule_ambiguity_watch_threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventExpiryRiskInputRow:
    research_key: str
    condition_id: str
    event_slug: str
    event_expiry_at: datetime
    settlement_expected_at: datetime | None
    latest_information_observed_at: datetime
    latest_settlement_evidence_at: datetime | None
    settlement_evidence_count: Decimal
    settlement_evidence_family_count: Decimal
    liquidity_score: Decimal
    rule_ambiguity_score: Decimal
    public_resolution_reference: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventExpiryRiskInputRow:
            raise TypeError("ResearchEventExpiryRiskInputRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventExpiryRiskInputRow:
            raise ValueError("input row must be exactly ResearchEventExpiryRiskInputRow")
        for field_name in ("research_key", "condition_id", "event_slug"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "event_expiry_at",
            _as_utc("event_expiry_at", self.event_expiry_at),
        )
        object.__setattr__(
            self,
            "settlement_expected_at",
            _optional_utc("settlement_expected_at", self.settlement_expected_at),
        )
        object.__setattr__(
            self,
            "latest_information_observed_at",
            _as_utc(
                "latest_information_observed_at",
                self.latest_information_observed_at,
            ),
        )
        object.__setattr__(
            self,
            "latest_settlement_evidence_at",
            _optional_utc(
                "latest_settlement_evidence_at",
                self.latest_settlement_evidence_at,
            ),
        )
        for field_name in (
            "settlement_evidence_count",
            "settlement_evidence_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.settlement_evidence_count > ZERO and self.latest_settlement_evidence_at is None:
            raise ValueError(
                "latest_settlement_evidence_at is required when "
                "settlement_evidence_count is positive",
            )
        if self.settlement_evidence_family_count > self.settlement_evidence_count:
            raise ValueError(
                "settlement_evidence_family_count must not exceed "
                "settlement_evidence_count",
            )
        for field_name in ("liquidity_score", "rule_ambiguity_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "public_resolution_reference",
            _optional_public_reference(
                "public_resolution_reference",
                self.public_resolution_reference,
            ),
        )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchEventExpiryRiskRow:
    research_key: str
    condition_id: str
    event_slug: str
    event_expiry_at: datetime
    settlement_expected_at: datetime | None
    latest_information_observed_at: datetime
    latest_settlement_evidence_at: datetime | None
    seconds_to_expiry: Decimal
    information_age_seconds: Decimal
    settlement_evidence_age_seconds: Decimal | None
    settlement_evidence_count: Decimal
    settlement_evidence_family_count: Decimal
    liquidity_score: Decimal
    rule_ambiguity_score: Decimal
    expiry_risk_status: str
    redacted_resolution_reference: str | None
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[ResearchEventExpiryRiskConfig | None] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventExpiryRiskRow:
            raise TypeError("ResearchEventExpiryRiskRow does not support subclassing")

    def __post_init__(
        self,
        validation_config: ResearchEventExpiryRiskConfig | None,
    ) -> None:
        if type(self) is not ResearchEventExpiryRiskRow:
            raise ValueError("row must be exactly ResearchEventExpiryRiskRow")
        for field_name in ("research_key", "condition_id", "event_slug"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "event_expiry_at",
            _as_utc("event_expiry_at", self.event_expiry_at),
        )
        object.__setattr__(
            self,
            "settlement_expected_at",
            _optional_utc("settlement_expected_at", self.settlement_expected_at),
        )
        object.__setattr__(
            self,
            "latest_information_observed_at",
            _as_utc(
                "latest_information_observed_at",
                self.latest_information_observed_at,
            ),
        )
        object.__setattr__(
            self,
            "latest_settlement_evidence_at",
            _optional_utc(
                "latest_settlement_evidence_at",
                self.latest_settlement_evidence_at,
            ),
        )
        for field_name in ("seconds_to_expiry", "information_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "settlement_evidence_age_seconds",
            _require_optional_nonnegative_decimal(
                "settlement_evidence_age_seconds",
                self.settlement_evidence_age_seconds,
            ),
        )
        for field_name in (
            "settlement_evidence_count",
            "settlement_evidence_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        if self.settlement_evidence_family_count > self.settlement_evidence_count:
            raise ValueError(
                "settlement_evidence_family_count must not exceed "
                "settlement_evidence_count",
            )
        for field_name in ("liquidity_score", "rule_ambiguity_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("expiry_risk_status", self.expiry_risk_status)
        object.__setattr__(
            self,
            "redacted_resolution_reference",
            _optional_redacted_reference(
                "redacted_resolution_reference",
                self.redacted_resolution_reference,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        if validation_config is not None and type(validation_config) is not ResearchEventExpiryRiskConfig:
            raise ValueError("validation_config must be a ResearchEventExpiryRiskConfig")
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchEventExpiryRiskReasonCodeCount:
    reason_code: str
    count: Decimal
    event_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventExpiryRiskReasonCodeCount:
            raise TypeError(
                "ResearchEventExpiryRiskReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventExpiryRiskReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchEventExpiryRiskReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "event_ratio",
            _require_ratio_decimal("event_ratio", self.event_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchEventExpiryRiskReport:
    generated_at: datetime
    config_version: str
    status: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    near_expiry_count: Decimal
    stale_information_count: Decimal
    thin_settlement_evidence_count: Decimal
    weak_liquidity_count: Decimal
    rule_ambiguity_count: Decimal
    min_seconds_to_expiry: Decimal
    average_information_age_seconds: Decimal
    average_liquidity_score: Decimal
    max_rule_ambiguity_score: Decimal
    rows: tuple[ResearchEventExpiryRiskRow, ...]
    reason_code_counts: tuple[ResearchEventExpiryRiskReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventExpiryRiskReport:
            raise TypeError("ResearchEventExpiryRiskReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventExpiryRiskReport:
            raise ValueError("report must be exactly ResearchEventExpiryRiskReport")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "event_count",
            "pass_count",
            "watch_count",
            "block_count",
            "near_expiry_count",
            "stale_information_count",
            "thin_settlement_evidence_count",
            "weak_liquidity_count",
            "rule_ambiguity_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_seconds_to_expiry",
            "average_information_age_seconds",
            "average_liquidity_score",
            "max_rule_ambiguity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_research_event_expiry_risk_report(
    input_rows: list[ResearchEventExpiryRiskInputRow]
    | tuple[ResearchEventExpiryRiskInputRow, ...],
    *,
    config: ResearchEventExpiryRiskConfig | None = None,
    generated_at: datetime,
) -> ResearchEventExpiryRiskReport:
    cfg = config or ResearchEventExpiryRiskConfig()
    if type(cfg) is not ResearchEventExpiryRiskConfig:
        raise ValueError("config must be a ResearchEventExpiryRiskConfig")
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    rows = _normalize_input_rows(input_rows)
    for row in rows:
        _reject_future_row_times(row, report_time)
    built_rows = tuple(_build_row(row, config=cfg, generated_at=report_time) for row in rows)
    ranked_rows = tuple(sorted(built_rows, key=lambda row: row.research_key))
    event_count = _count(len(ranked_rows))
    reason_code_counts = _reason_code_counts(ranked_rows)
    reason_codes = _summary_reason_codes(ranked_rows)
    if not ranked_rows:
        reason_code_counts = (
            ResearchEventExpiryRiskReasonCodeCount(
                reason_code="no_expiry_events",
                count=ONE,
                event_ratio=ONE,
            ),
        )
        reason_codes = ("no_expiry_events",)
    return ResearchEventExpiryRiskReport(
        generated_at=report_time,
        config_version=cfg.config_version,
        status=_summary_status(reason_codes),
        event_count=event_count,
        pass_count=_status_count(ranked_rows, "pass"),
        watch_count=_status_count(ranked_rows, "watch"),
        block_count=_status_count(ranked_rows, "block"),
        near_expiry_count=_count(
            sum(
                1
                for row in ranked_rows
                if "expiry_watch_window" in row.reason_codes
                or "expiry_block_window" in row.reason_codes
                or "expiry_elapsed" in row.reason_codes
            ),
        ),
        stale_information_count=_count(
            sum(
                1
                for row in ranked_rows
                if "information_refresh_watch" in row.reason_codes
                or "information_refresh_block" in row.reason_codes
            ),
        ),
        thin_settlement_evidence_count=_count(
            sum(
                1
                for row in ranked_rows
                if "thin_settlement_evidence" in row.reason_codes
                or "missing_settlement_evidence" in row.reason_codes
            ),
        ),
        weak_liquidity_count=_count(
            sum(
                1
                for row in ranked_rows
                if "liquidity_watch" in row.reason_codes
                or "liquidity_block" in row.reason_codes
            ),
        ),
        rule_ambiguity_count=_count(
            sum(
                1
                for row in ranked_rows
                if "rules_ambiguous_watch" in row.reason_codes
                or "rules_ambiguous_block" in row.reason_codes
            ),
        ),
        min_seconds_to_expiry=min(
            (row.seconds_to_expiry for row in ranked_rows),
            default=ZERO,
        ),
        average_information_age_seconds=_ratio(
            _sum_decimal(row.information_age_seconds for row in ranked_rows),
            event_count,
        ),
        average_liquidity_score=_ratio(
            _sum_decimal(row.liquidity_score for row in ranked_rows),
            event_count,
        ),
        max_rule_ambiguity_score=max(
            (row.rule_ambiguity_score for row in ranked_rows),
            default=ZERO,
        ),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_event_expiry_risk_report_payload(
    report: ResearchEventExpiryRiskReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventExpiryRiskReport:
        raise ValueError("report must be a ResearchEventExpiryRiskReport")
    _require_hard_flags("report", report)
    payload = _public_report_payload(report)
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_payload("payload", payload)
    return payload


def _public_report_payload(report: ResearchEventExpiryRiskReport) -> dict[str, Any]:
    payload = _json_ready(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "status": report.status,
            "event_count": report.event_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "near_expiry_count": report.near_expiry_count,
            "stale_information_count": report.stale_information_count,
            "thin_settlement_evidence_count": report.thin_settlement_evidence_count,
            "weak_liquidity_count": report.weak_liquidity_count,
            "rule_ambiguity_count": report.rule_ambiguity_count,
            "min_seconds_to_expiry": report.min_seconds_to_expiry,
            "average_information_age_seconds": report.average_information_age_seconds,
            "average_liquidity_score": report.average_liquidity_score,
            "max_rule_ambiguity_score": report.max_rule_ambiguity_score,
            "rows": tuple(_public_row_payload(row) for row in report.rows),
            "reason_code_counts": tuple(
                _public_reason_code_count_payload(count)
                for count in report.reason_code_counts
            ),
            "reason_codes": report.reason_codes,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _public_row_payload(row: ResearchEventExpiryRiskRow) -> dict[str, Any]:
    return {
        "event_expiry_at": row.event_expiry_at,
        "settlement_expected_at": row.settlement_expected_at,
        "latest_information_observed_at": row.latest_information_observed_at,
        "latest_settlement_evidence_at": row.latest_settlement_evidence_at,
        "seconds_to_expiry": row.seconds_to_expiry,
        "information_age_seconds": row.information_age_seconds,
        "settlement_evidence_age_seconds": row.settlement_evidence_age_seconds,
        "settlement_evidence_count": row.settlement_evidence_count,
        "settlement_evidence_family_count": row.settlement_evidence_family_count,
        "liquidity_score": row.liquidity_score,
        "rule_ambiguity_score": row.rule_ambiguity_score,
        "expiry_risk_status": row.expiry_risk_status,
        "redacted_resolution_reference": row.redacted_resolution_reference,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _public_reason_code_count_payload(
    count: ResearchEventExpiryRiskReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": count.reason_code,
        "count": count.count,
        "event_ratio": count.event_ratio,
        "paper_only": count.paper_only,
        "report_only": count.report_only,
        "readonly": count.readonly,
    }


@dataclass(frozen=True)
class _DictFlags:
    payload: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.payload.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.payload.get("report_only")

    @property
    def readonly(self) -> object:
        return self.payload.get("readonly")


def _build_row(
    input_row: ResearchEventExpiryRiskInputRow,
    *,
    config: ResearchEventExpiryRiskConfig,
    generated_at: datetime,
) -> ResearchEventExpiryRiskRow:
    seconds_to_expiry = _future_seconds(generated_at, input_row.event_expiry_at)
    information_age_seconds = _age_seconds(
        generated_at,
        input_row.latest_information_observed_at,
    )
    settlement_evidence_age_seconds = None
    if (
        input_row.settlement_evidence_count > ZERO
        and input_row.latest_settlement_evidence_at is not None
    ):
        settlement_evidence_age_seconds = _age_seconds(
            generated_at,
            input_row.latest_settlement_evidence_at,
        )
    reason_codes = _row_reason_codes(
        input_row,
        config=config,
        seconds_to_expiry=seconds_to_expiry,
        information_age_seconds=information_age_seconds,
        settlement_evidence_age_seconds=settlement_evidence_age_seconds,
    )
    status = _row_status(reason_codes)
    return ResearchEventExpiryRiskRow(
        research_key=input_row.research_key,
        condition_id=input_row.condition_id,
        event_slug=input_row.event_slug,
        event_expiry_at=input_row.event_expiry_at,
        settlement_expected_at=input_row.settlement_expected_at,
        latest_information_observed_at=input_row.latest_information_observed_at,
        latest_settlement_evidence_at=input_row.latest_settlement_evidence_at,
        seconds_to_expiry=seconds_to_expiry,
        information_age_seconds=information_age_seconds,
        settlement_evidence_age_seconds=settlement_evidence_age_seconds,
        settlement_evidence_count=input_row.settlement_evidence_count,
        settlement_evidence_family_count=input_row.settlement_evidence_family_count,
        liquidity_score=input_row.liquidity_score,
        rule_ambiguity_score=input_row.rule_ambiguity_score,
        expiry_risk_status=status,
        redacted_resolution_reference=_redacted_reference(
            input_row.public_resolution_reference,
        ),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    input_row: ResearchEventExpiryRiskInputRow,
    *,
    config: ResearchEventExpiryRiskConfig,
    seconds_to_expiry: Decimal,
    information_age_seconds: Decimal,
    settlement_evidence_age_seconds: Decimal | None,
) -> tuple[str, ...]:
    reason_codes: set[str] = set()
    if input_row.event_expiry_at <= input_row.latest_information_observed_at:
        reason_codes.add("expiry_elapsed")
    elif seconds_to_expiry <= config.expiry_block_window_seconds:
        reason_codes.add("expiry_block_window")
    elif seconds_to_expiry <= config.expiry_watch_window_seconds:
        reason_codes.add("expiry_watch_window")
    else:
        reason_codes.add("expiry_window_clear")

    if information_age_seconds >= config.stale_information_block_age_seconds:
        reason_codes.add("information_refresh_block")
    elif information_age_seconds > config.fresh_information_max_age_seconds:
        reason_codes.add("information_refresh_watch")
    else:
        reason_codes.add("information_refresh_current")

    if input_row.settlement_evidence_count == ZERO:
        reason_codes.add("missing_settlement_evidence")
    elif (
        input_row.settlement_evidence_count < config.min_settlement_evidence_count
        or input_row.settlement_evidence_family_count
        < config.min_settlement_evidence_family_count
    ):
        reason_codes.add("thin_settlement_evidence")
    elif (
        settlement_evidence_age_seconds is not None
        and settlement_evidence_age_seconds >= config.settlement_evidence_stale_age_seconds
    ):
        reason_codes.add("settlement_evidence_stale")
    else:
        reason_codes.add("settlement_evidence_current")
        reason_codes.add("settlement_evidence_sufficient")

    if input_row.liquidity_score <= config.liquidity_block_threshold:
        reason_codes.add("liquidity_block")
    elif input_row.liquidity_score < config.liquidity_pass_threshold:
        reason_codes.add("liquidity_watch")
    else:
        reason_codes.add("liquidity_clear")

    if input_row.rule_ambiguity_score >= config.rule_ambiguity_block_threshold:
        reason_codes.add("rules_ambiguous_block")
    elif input_row.rule_ambiguity_score >= config.rule_ambiguity_watch_threshold:
        reason_codes.add("rules_ambiguous_watch")
    else:
        reason_codes.add("rules_clear")

    status = _row_status(tuple(reason_codes))
    reason_codes.add(f"expiry_risk_{status}")
    return tuple(sorted(reason_codes))


def _row_status(reason_codes: tuple[str, ...] | set[str]) -> str:
    if any(code.endswith("_block") or code == "expiry_elapsed" for code in reason_codes):
        return "block"
    if any(code.endswith("_watch") or code == "expiry_watch_window" for code in reason_codes):
        return "watch"
    return "pass"


def _summary_reason_codes(
    rows: tuple[ResearchEventExpiryRiskRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_expiry_events",)
    risk_rows = tuple(row for row in rows if row.expiry_risk_status != "pass")
    if not risk_rows:
        return ("expiry_risk_pass",)
    return tuple(
        sorted(
            {
                code
                for row in risk_rows
                for code in row.reason_codes
                if _is_report_level_reason_code(code)
            },
        ),
    )


def _is_report_level_reason_code(reason_code: str) -> bool:
    return not (
        reason_code.endswith("_clear")
        or reason_code.endswith("_current")
        or reason_code.endswith("_sufficient")
    )


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_expiry_events",):
        return "block"
    if "expiry_risk_block" in reason_codes:
        return "block"
    if "expiry_risk_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchEventExpiryRiskRow, ...],
) -> tuple[ResearchEventExpiryRiskReasonCodeCount, ...]:
    if not rows:
        return ()
    event_count = _count(len(rows))
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchEventExpiryRiskReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            event_ratio=_ratio(_count(count), event_count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _normalize_input_rows(
    input_rows: list[ResearchEventExpiryRiskInputRow]
    | tuple[ResearchEventExpiryRiskInputRow, ...],
) -> tuple[ResearchEventExpiryRiskInputRow, ...]:
    if type(input_rows) not in (list, tuple):
        raise ValueError("input_rows must be a list or tuple")
    rows = tuple(input_rows)
    for row in rows:
        if type(row) is not ResearchEventExpiryRiskInputRow:
            raise ValueError("input_rows must contain ResearchEventExpiryRiskInputRow")
        _require_hard_flags("input row", row)
    return rows


def _normalize_rows(
    rows: tuple[ResearchEventExpiryRiskRow, ...],
) -> tuple[ResearchEventExpiryRiskRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchEventExpiryRiskRow:
            raise ValueError("rows must contain ResearchEventExpiryRiskRow")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.research_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by research_key")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchEventExpiryRiskReasonCodeCount, ...],
) -> tuple[ResearchEventExpiryRiskReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchEventExpiryRiskReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventExpiryRiskReasonCodeCount",
            )
        _require_hard_flags("reason code count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row(row: ResearchEventExpiryRiskRow) -> None:
    expected_status = _row_status(
        tuple(
            code
            for code in row.reason_codes
            if not code.startswith("expiry_risk_")
        ),
    )
    if row.expiry_risk_status != expected_status:
        raise ValueError("expiry_risk_status must match reason_codes")
    expected_status_reason = f"expiry_risk_{row.expiry_risk_status}"
    if expected_status_reason not in row.reason_codes:
        raise ValueError("reason_codes must include expiry risk status")
    if row.settlement_evidence_count == ZERO and row.settlement_evidence_age_seconds is not None:
        raise ValueError("settlement_evidence_age_seconds must be absent without evidence")
    if row.settlement_evidence_count > ZERO and row.latest_settlement_evidence_at is None:
        raise ValueError("latest_settlement_evidence_at is required with evidence")


def _validate_report(report: ResearchEventExpiryRiskReport) -> None:
    if report.event_count != _count(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.min_seconds_to_expiry != min(
        (row.seconds_to_expiry for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_seconds_to_expiry must match rows")
    if report.average_information_age_seconds != _ratio(
        _sum_decimal(row.information_age_seconds for row in report.rows),
        report.event_count,
    ):
        raise ValueError("average_information_age_seconds must match rows")
    if report.average_liquidity_score != _ratio(
        _sum_decimal(row.liquidity_score for row in report.rows),
        report.event_count,
    ):
        raise ValueError("average_liquidity_score must match rows")
    if report.max_rule_ambiguity_score != max(
        (row.rule_ambiguity_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_rule_ambiguity_score must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _reject_future_row_times(
    row: ResearchEventExpiryRiskInputRow,
    generated_at: datetime,
) -> None:
    if row.latest_information_observed_at > generated_at:
        raise ValueError("latest_information_observed_at must not be after generated_at")
    if (
        row.latest_settlement_evidence_at is not None
        and row.latest_settlement_evidence_at > generated_at
    ):
        raise ValueError("latest_settlement_evidence_at must not be after generated_at")


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    return (
        Decimal(delta.days * 86_400)
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / Decimal("1000000"))
    )


def _future_seconds(generated_at: datetime, future_at: datetime) -> Decimal:
    if future_at <= generated_at:
        return ZERO
    return _age_seconds(future_at, generated_at)


def _status_count(rows: tuple[ResearchEventExpiryRiskRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.expiry_risk_status == status))


def _sum_decimal(values: Any) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return total


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _redacted_reference(reference: str | None) -> str | None:
    if reference is None:
        return None
    return "reference_provided"


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("payload must not contain float values")
    if type(value) in (str, int, bool):
        return value
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return _json_dict_ready(value)
    raise ValueError("payload contains a non-public value")


def _json_dict_ready(value: dict[Any, Any]) -> dict[str, Any]:
    ready: dict[str, Any] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("payload keys must be strings")
        ready[key] = _json_ready(item)
    return ready


def _reject_unsafe_payload(label: str, value: object) -> None:
    for key in _iter_payload_keys(value):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in _unsafe_fragments()):
            raise ValueError(f"unsafe public payload field in {label}: {key}")


def _iter_payload_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_payload_keys({field.name: getattr(value, field.name) for field in fields(value)})
    if type(value) is dict:
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            keys.append(key)
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    if type(value) in (list, tuple):
        keys = []
        for item in value:
            keys.extend(_iter_payload_keys(item))
        return tuple(keys)
    return ()


def _unsafe_fragments() -> tuple[str, ...]:
    return (
        "auth",
        "private_key",
        "wallet",
        "account",
        "balance",
        "order",
        "cancel",
        "replace",
        "sign",
        "exchange_mutation",
        "research_key",
        "condition_id",
        "event_slug",
        "b" + "uy",
        "se" + "ll",
        "posi" + "tion",
        "recom" + "mend",
    )


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _optional_public_reference(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public reference")
    return value


def _optional_redacted_reference(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    if value != "reference_provided":
        raise ValueError(f"{field_name} must be redacted")
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical reason code")
    for character in value:
        if not (character.islower() or character.isdigit() or character == "_"):
            raise ValueError(f"{field_name} must be snake_case")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")
