"""Pure report-only reducer for research strategy governance checks."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_STRATEGY_GOVERNANCE_REPORT_CONFIG_VERSION = (
    "research-strategy-governance-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_GOVERNANCE_STATUSES = frozenset(("pass", "watch", "block"))
_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_BLOCK_REASON_CODES = frozenset(
    (
        "execution_boundary_block",
        "quality_assurance_block",
        "team_routing_block",
        "data_feed_quality_block",
        "local_memory_plan_block",
    ),
)
_REASON_CODE_SEQUENCE = (
    "empty_governance_queue",
    "execution_boundary_block",
    "quality_assurance_block",
    "team_routing_block",
    "data_feed_quality_block",
    "local_memory_plan_block",
    "execution_boundary_watch",
    "quality_assurance_watch",
    "team_routing_watch",
    "data_feed_quality_watch",
    "local_memory_plan_watch",
    "governance_pass",
)
_DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "source",
    "ref",
    "url",
    "text",
    "http://",
    "https://",
    "://",
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
    "recommend",
    "recommendation",
)


@dataclass(frozen=True)
class ResearchStrategyGovernanceReportConfig:
    config_version: str = DEFAULT_RESEARCH_STRATEGY_GOVERNANCE_REPORT_CONFIG_VERSION
    min_execution_boundary_score: Decimal = Decimal("0.500000")
    pass_execution_boundary_score: Decimal = Decimal("0.750000")
    min_quality_assurance_score: Decimal = Decimal("0.500000")
    pass_quality_assurance_score: Decimal = Decimal("0.750000")
    min_team_routing_score: Decimal = Decimal("0.350000")
    pass_team_routing_score: Decimal = Decimal("0.650000")
    min_data_feed_quality_score: Decimal = Decimal("0.500000")
    pass_data_feed_quality_score: Decimal = Decimal("0.750000")
    min_local_memory_plan_score: Decimal = Decimal("0.500000")
    pass_local_memory_plan_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyGovernanceReportConfig:
            raise TypeError(
                "ResearchStrategyGovernanceReportConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyGovernanceReportConfig:
            raise ValueError(
                "config must be exactly ResearchStrategyGovernanceReportConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_STRATEGY_GOVERNANCE_REPORT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_execution_boundary_score",
            "pass_execution_boundary_score",
            "min_quality_assurance_score",
            "pass_quality_assurance_score",
            "min_team_routing_score",
            "pass_team_routing_score",
            "min_data_feed_quality_score",
            "pass_data_feed_quality_score",
            "min_local_memory_plan_score",
            "pass_local_memory_plan_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_execution_boundary_score > self.pass_execution_boundary_score:
            raise ValueError("min_execution_boundary_score must not exceed pass threshold")
        if self.min_quality_assurance_score > self.pass_quality_assurance_score:
            raise ValueError("min_quality_assurance_score must not exceed pass threshold")
        if self.min_team_routing_score > self.pass_team_routing_score:
            raise ValueError("min_team_routing_score must not exceed pass threshold")
        if self.min_data_feed_quality_score > self.pass_data_feed_quality_score:
            raise ValueError("min_data_feed_quality_score must not exceed pass threshold")
        if self.min_local_memory_plan_score > self.pass_local_memory_plan_score:
            raise ValueError("min_local_memory_plan_score must not exceed pass threshold")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyGovernanceCheck:
    anonymized_research_key: str
    execution_boundary_score: Decimal
    quality_assurance_score: Decimal
    team_routing_score: Decimal
    data_feed_quality_score: Decimal
    local_memory_plan_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyGovernanceCheck:
            raise TypeError("ResearchStrategyGovernanceCheck does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyGovernanceCheck:
            raise ValueError("check must be exactly ResearchStrategyGovernanceCheck")
        _require_public_identifier("anonymized_research_key", self.anonymized_research_key)
        for field_name in (
            "execution_boundary_score",
            "quality_assurance_score",
            "team_routing_score",
            "data_feed_quality_score",
            "local_memory_plan_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("check", self)
        _reject_unsafe_public_payload("check", self)


@dataclass(frozen=True)
class ResearchStrategyGovernancePublicNote:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyGovernancePublicNote:
            raise TypeError(
                "ResearchStrategyGovernancePublicNote does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyGovernancePublicNote:
            raise ValueError(
                "public note must be exactly ResearchStrategyGovernancePublicNote",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public note", self)
        _reject_unsafe_public_payload("public note", self)


@dataclass(frozen=True)
class ResearchStrategyGovernanceReportRow:
    anonymized_research_key: str
    execution_boundary_score: Decimal
    quality_assurance_score: Decimal
    team_routing_score: Decimal
    data_feed_quality_score: Decimal
    local_memory_plan_score: Decimal
    governance_score: Decimal
    governance_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyGovernanceReportRow:
            raise TypeError(
                "ResearchStrategyGovernanceReportRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyGovernanceReportRow:
            raise ValueError("row must be exactly ResearchStrategyGovernanceReportRow")
        _require_public_identifier("anonymized_research_key", self.anonymized_research_key)
        for field_name in (
            "execution_boundary_score",
            "quality_assurance_score",
            "team_routing_score",
            "data_feed_quality_score",
            "local_memory_plan_score",
            "governance_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_governance_status("governance_status", self.governance_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyGovernanceReport:
    generated_at: datetime
    config_version: str
    governance_status: str
    check_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    pass_ratio: Decimal | None
    watch_ratio: Decimal | None
    block_ratio: Decimal | None
    average_execution_boundary_score: Decimal
    average_quality_assurance_score: Decimal
    average_team_routing_score: Decimal
    average_data_feed_quality_score: Decimal
    average_local_memory_plan_score: Decimal
    average_governance_score: Decimal
    lowest_execution_boundary_score: Decimal
    lowest_quality_assurance_score: Decimal
    lowest_team_routing_score: Decimal
    lowest_data_feed_quality_score: Decimal
    lowest_local_memory_plan_score: Decimal
    reason_codes: tuple[str, ...]
    deterministic_summary: str
    rows: tuple[ResearchStrategyGovernanceReportRow, ...]
    public_notes: tuple[ResearchStrategyGovernancePublicNote, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyGovernanceReport:
            raise TypeError("ResearchStrategyGovernanceReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyGovernanceReport:
            raise ValueError("report must be exactly ResearchStrategyGovernanceReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_STRATEGY_GOVERNANCE_REPORT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_governance_status("governance_status", self.governance_status)
        for field_name in ("check_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("pass_ratio", "watch_ratio", "block_ratio"):
            _require_optional_ratio_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "average_execution_boundary_score",
            "average_quality_assurance_score",
            "average_team_routing_score",
            "average_data_feed_quality_score",
            "average_local_memory_plan_score",
            "average_governance_score",
            "lowest_execution_boundary_score",
            "lowest_quality_assurance_score",
            "lowest_team_routing_score",
            "lowest_data_feed_quality_score",
            "lowest_local_memory_plan_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "public_notes", _normalize_public_notes(self.public_notes))
        object.__setattr__(
            self,
            "deterministic_summary",
            _require_public_text("deterministic_summary", self.deterministic_summary),
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
        return research_strategy_governance_report_payload(self)


def build_research_strategy_governance_report(
    checks: Sequence[ResearchStrategyGovernanceCheck],
    *,
    generated_at: datetime,
    config: ResearchStrategyGovernanceReportConfig | None = None,
    public_notes: Sequence[ResearchStrategyGovernancePublicNote] = (),
) -> ResearchStrategyGovernanceReport:
    """Build a deterministic report-only strategy governance report."""

    if config is None:
        config = ResearchStrategyGovernanceReportConfig()
    if type(config) is not ResearchStrategyGovernanceReportConfig:
        raise ValueError("config must be a ResearchStrategyGovernanceReportConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_checks = _normalize_checks(checks)
    rows = _build_rows(normalized_checks, config)
    status = _report_status(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "governance_status": status,
        "check_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "pass_ratio": _optional_ratio(_status_count(rows, "pass"), len(rows)),
        "watch_ratio": _optional_ratio(_status_count(rows, "watch"), len(rows)),
        "block_ratio": _optional_ratio(_status_count(rows, "block"), len(rows)),
        "average_execution_boundary_score": _average_ratio(
            tuple(row.execution_boundary_score for row in rows),
        ),
        "average_quality_assurance_score": _average_ratio(
            tuple(row.quality_assurance_score for row in rows),
        ),
        "average_team_routing_score": _average_ratio(
            tuple(row.team_routing_score for row in rows),
        ),
        "average_data_feed_quality_score": _average_ratio(
            tuple(row.data_feed_quality_score for row in rows),
        ),
        "average_local_memory_plan_score": _average_ratio(
            tuple(row.local_memory_plan_score for row in rows),
        ),
        "average_governance_score": _average_ratio(
            tuple(row.governance_score for row in rows),
        ),
        "lowest_execution_boundary_score": min(
            (row.execution_boundary_score for row in rows),
            default=_ZERO,
        ),
        "lowest_quality_assurance_score": min(
            (row.quality_assurance_score for row in rows),
            default=_ZERO,
        ),
        "lowest_team_routing_score": min(
            (row.team_routing_score for row in rows),
            default=_ZERO,
        ),
        "lowest_data_feed_quality_score": min(
            (row.data_feed_quality_score for row in rows),
            default=_ZERO,
        ),
        "lowest_local_memory_plan_score": min(
            (row.local_memory_plan_score for row in rows),
            default=_ZERO,
        ),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "public_notes": _normalize_public_notes(public_notes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["deterministic_summary"] = _deterministic_summary(values)
    return ResearchStrategyGovernanceReport(**values)


def research_strategy_governance_report_payload(
    value: ResearchStrategyGovernanceReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchStrategyGovernanceReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError("value must be a ResearchStrategyGovernanceReport or dict")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_flag_downgrades("payload", payload)
    _reject_public_numerics(payload)
    _reject_unsafe_public_payload("payload", payload)
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
    checks: tuple[ResearchStrategyGovernanceCheck, ...],
    config: ResearchStrategyGovernanceReportConfig,
) -> tuple[ResearchStrategyGovernanceReportRow, ...]:
    return tuple(sorted((_row_for_check(check, config) for check in checks), key=_row_sort_key))


def _row_for_check(
    check: ResearchStrategyGovernanceCheck,
    config: ResearchStrategyGovernanceReportConfig,
) -> ResearchStrategyGovernanceReportRow:
    governance_score = _average_ratio(
        (
            check.execution_boundary_score,
            check.quality_assurance_score,
            check.team_routing_score,
            check.data_feed_quality_score,
            check.local_memory_plan_score,
        ),
    )
    reason_codes = _row_reason_codes(
        execution_boundary_score=check.execution_boundary_score,
        quality_assurance_score=check.quality_assurance_score,
        team_routing_score=check.team_routing_score,
        data_feed_quality_score=check.data_feed_quality_score,
        local_memory_plan_score=check.local_memory_plan_score,
        config=config,
    )
    return ResearchStrategyGovernanceReportRow(
        anonymized_research_key=check.anonymized_research_key,
        execution_boundary_score=check.execution_boundary_score,
        quality_assurance_score=check.quality_assurance_score,
        team_routing_score=check.team_routing_score,
        data_feed_quality_score=check.data_feed_quality_score,
        local_memory_plan_score=check.local_memory_plan_score,
        governance_score=governance_score,
        governance_status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    execution_boundary_score: Decimal,
    quality_assurance_score: Decimal,
    team_routing_score: Decimal,
    data_feed_quality_score: Decimal,
    local_memory_plan_score: Decimal,
    config: ResearchStrategyGovernanceReportConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if execution_boundary_score < config.min_execution_boundary_score:
        reason_codes.append("execution_boundary_block")
    if quality_assurance_score < config.min_quality_assurance_score:
        reason_codes.append("quality_assurance_block")
    if team_routing_score < config.min_team_routing_score:
        reason_codes.append("team_routing_block")
    if data_feed_quality_score < config.min_data_feed_quality_score:
        reason_codes.append("data_feed_quality_block")
    if local_memory_plan_score < config.min_local_memory_plan_score:
        reason_codes.append("local_memory_plan_block")
    if not any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        if execution_boundary_score < config.pass_execution_boundary_score:
            reason_codes.append("execution_boundary_watch")
        if quality_assurance_score < config.pass_quality_assurance_score:
            reason_codes.append("quality_assurance_watch")
        if team_routing_score < config.pass_team_routing_score:
            reason_codes.append("team_routing_watch")
        if data_feed_quality_score < config.pass_data_feed_quality_score:
            reason_codes.append("data_feed_quality_watch")
        if local_memory_plan_score < config.pass_local_memory_plan_score:
            reason_codes.append("local_memory_plan_watch")
    return tuple(reason_codes or ("governance_pass",))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("governance_pass",):
        return "pass"
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    return "watch"


def _report_status(rows: tuple[ResearchStrategyGovernanceReportRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.governance_status == "block" for row in rows):
        return "block"
    if any(row.governance_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyGovernanceReportRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_governance_queue",)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if any(reason_code in row.reason_codes for row in rows)
    )


def _status_count(rows: tuple[ResearchStrategyGovernanceReportRow, ...], status: str) -> int:
    return len(tuple(row for row in rows if row.governance_status == status))


def _validate_row_consistency(row: ResearchStrategyGovernanceReportRow) -> None:
    if row.governance_score != _average_ratio(
        (
            row.execution_boundary_score,
            row.quality_assurance_score,
            row.team_routing_score,
            row.data_feed_quality_score,
            row.local_memory_plan_score,
        ),
    ):
        raise ValueError("governance_score must match component scores")
    if row.governance_status != _row_status(row.reason_codes):
        raise ValueError("governance_status must match reason_codes")


def _validate_report_consistency(report: ResearchStrategyGovernanceReport) -> None:
    if report.check_count != _decimal_count(len(report.rows)):
        raise ValueError("check_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.pass_ratio != _optional_ratio(_status_count(report.rows, "pass"), len(report.rows)):
        raise ValueError("pass_ratio must match rows")
    if report.watch_ratio != _optional_ratio(_status_count(report.rows, "watch"), len(report.rows)):
        raise ValueError("watch_ratio must match rows")
    if report.block_ratio != _optional_ratio(_status_count(report.rows, "block"), len(report.rows)):
        raise ValueError("block_ratio must match rows")
    if report.average_execution_boundary_score != _average_ratio(
        tuple(row.execution_boundary_score for row in report.rows),
    ):
        raise ValueError("average_execution_boundary_score must match rows")
    if report.average_quality_assurance_score != _average_ratio(
        tuple(row.quality_assurance_score for row in report.rows),
    ):
        raise ValueError("average_quality_assurance_score must match rows")
    if report.average_team_routing_score != _average_ratio(
        tuple(row.team_routing_score for row in report.rows),
    ):
        raise ValueError("average_team_routing_score must match rows")
    if report.average_data_feed_quality_score != _average_ratio(
        tuple(row.data_feed_quality_score for row in report.rows),
    ):
        raise ValueError("average_data_feed_quality_score must match rows")
    if report.average_local_memory_plan_score != _average_ratio(
        tuple(row.local_memory_plan_score for row in report.rows),
    ):
        raise ValueError("average_local_memory_plan_score must match rows")
    if report.average_governance_score != _average_ratio(
        tuple(row.governance_score for row in report.rows),
    ):
        raise ValueError("average_governance_score must match rows")
    if report.lowest_execution_boundary_score != min(
        (row.execution_boundary_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("lowest_execution_boundary_score must match rows")
    if report.lowest_quality_assurance_score != min(
        (row.quality_assurance_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("lowest_quality_assurance_score must match rows")
    if report.lowest_team_routing_score != min(
        (row.team_routing_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("lowest_team_routing_score must match rows")
    if report.lowest_data_feed_quality_score != min(
        (row.data_feed_quality_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("lowest_data_feed_quality_score must match rows")
    if report.lowest_local_memory_plan_score != min(
        (row.local_memory_plan_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("lowest_local_memory_plan_score must match rows")
    if report.governance_status != _report_status(report.rows):
        raise ValueError("governance_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.deterministic_summary != _deterministic_summary(
        {
            "governance_status": report.governance_status,
            "check_count": report.check_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "average_execution_boundary_score": report.average_execution_boundary_score,
            "average_quality_assurance_score": report.average_quality_assurance_score,
            "average_team_routing_score": report.average_team_routing_score,
            "average_data_feed_quality_score": report.average_data_feed_quality_score,
            "average_local_memory_plan_score": report.average_local_memory_plan_score,
            "reason_codes": report.reason_codes,
        },
    ):
        raise ValueError("deterministic_summary must match report fields")


def _normalize_checks(
    checks: Sequence[ResearchStrategyGovernanceCheck],
) -> tuple[ResearchStrategyGovernanceCheck, ...]:
    if type(checks) not in (list, tuple):
        raise ValueError("checks must be a list or tuple")
    normalized = tuple(checks)
    for check in normalized:
        if type(check) is not ResearchStrategyGovernanceCheck:
            raise ValueError("checks items must be ResearchStrategyGovernanceCheck")
        _require_hard_flags("check", check)
    keys = tuple(check.anonymized_research_key for check in normalized)
    if len(set(keys)) != len(keys):
        raise ValueError("anonymized_research_key values must be unique")
    return normalized


def _normalize_rows(
    rows: tuple[ResearchStrategyGovernanceReportRow, ...],
) -> tuple[ResearchStrategyGovernanceReportRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchStrategyGovernanceReportRow:
            raise ValueError("rows items must be ResearchStrategyGovernanceReportRow")
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic governance sorting")
    keys = tuple(row.anonymized_research_key for row in normalized)
    if len(set(keys)) != len(keys):
        raise ValueError("row anonymized_research_key values must be unique")
    return normalized


def _normalize_public_notes(
    public_notes: Sequence[ResearchStrategyGovernancePublicNote],
) -> tuple[ResearchStrategyGovernancePublicNote, ...]:
    if type(public_notes) not in (list, tuple):
        raise ValueError("public_notes must be a list or tuple")
    normalized = tuple(sorted(public_notes, key=lambda item: item.key))
    for item in normalized:
        if type(item) is not ResearchStrategyGovernancePublicNote:
            raise ValueError(
                "public_notes items must be ResearchStrategyGovernancePublicNote",
            )
        _require_hard_flags("public note", item)
    keys = tuple(item.key for item in normalized)
    if len(set(keys)) != len(keys):
        raise ValueError("public_notes keys must be unique")
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


def _row_sort_key(row: ResearchStrategyGovernanceReportRow) -> tuple[int, Decimal, str]:
    status_weight = {"block": 0, "watch": 1, "pass": 2}
    return (
        status_weight[row.governance_status],
        -row.governance_score,
        row.anonymized_research_key,
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


def _require_governance_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _GOVERNANCE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


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


def _require_optional_ratio_decimal(field_name: str, value: object) -> None:
    if value is None:
        return
    _require_ratio_decimal(field_name, value)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _optional_ratio(numerator: int, denominator: int) -> Decimal | None:
    if denominator == 0:
        return None
    return _quantize(Decimal(numerator) / Decimal(denominator))


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


def _deterministic_summary(values: dict[str, object]) -> str:
    return (
        f"{_require_dict_str(values, 'governance_status')}"
        f"|checks={_require_dict_decimal(values, 'check_count')}"
        f"|pass={_require_dict_decimal(values, 'pass_count')}"
        f"|watch={_require_dict_decimal(values, 'watch_count')}"
        f"|block={_require_dict_decimal(values, 'block_count')}"
        f"|boundary_avg={_require_dict_decimal(values, 'average_execution_boundary_score')}"
        f"|qa_avg={_require_dict_decimal(values, 'average_quality_assurance_score')}"
        f"|routing_avg={_require_dict_decimal(values, 'average_team_routing_score')}"
        f"|feed_avg={_require_dict_decimal(values, 'average_data_feed_quality_score')}"
        f"|memory_avg={_require_dict_decimal(values, 'average_local_memory_plan_score')}"
        f"|reasons={','.join(_require_dict_reason_codes(values, 'reason_codes'))}"
    )


def _report_payload_without_digest(report: ResearchStrategyGovernanceReport) -> dict[str, object]:
    return {
        "generated_at": _json_ready(report.generated_at),
        "config_version": report.config_version,
        "governance_status": report.governance_status,
        "check_count": _json_ready(report.check_count),
        "pass_count": _json_ready(report.pass_count),
        "watch_count": _json_ready(report.watch_count),
        "block_count": _json_ready(report.block_count),
        "pass_ratio": _json_ready(report.pass_ratio),
        "watch_ratio": _json_ready(report.watch_ratio),
        "block_ratio": _json_ready(report.block_ratio),
        "average_execution_boundary_score": _json_ready(
            report.average_execution_boundary_score,
        ),
        "average_quality_assurance_score": _json_ready(
            report.average_quality_assurance_score,
        ),
        "average_team_routing_score": _json_ready(report.average_team_routing_score),
        "average_data_feed_quality_score": _json_ready(
            report.average_data_feed_quality_score,
        ),
        "average_local_memory_plan_score": _json_ready(
            report.average_local_memory_plan_score,
        ),
        "average_governance_score": _json_ready(report.average_governance_score),
        "lowest_execution_boundary_score": _json_ready(
            report.lowest_execution_boundary_score,
        ),
        "lowest_quality_assurance_score": _json_ready(
            report.lowest_quality_assurance_score,
        ),
        "lowest_team_routing_score": _json_ready(report.lowest_team_routing_score),
        "lowest_data_feed_quality_score": _json_ready(
            report.lowest_data_feed_quality_score,
        ),
        "lowest_local_memory_plan_score": _json_ready(
            report.lowest_local_memory_plan_score,
        ),
        "reason_codes": list(report.reason_codes),
        "deterministic_summary": report.deterministic_summary,
        "rows": [_row_payload(row) for row in report.rows],
        "public_notes": [_public_note_payload(item) for item in report.public_notes],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_payload(row: ResearchStrategyGovernanceReportRow) -> dict[str, object]:
    return {
        "anonymized_research_key": row.anonymized_research_key,
        "execution_boundary_score": _json_ready(row.execution_boundary_score),
        "quality_assurance_score": _json_ready(row.quality_assurance_score),
        "team_routing_score": _json_ready(row.team_routing_score),
        "data_feed_quality_score": _json_ready(row.data_feed_quality_score),
        "local_memory_plan_score": _json_ready(row.local_memory_plan_score),
        "governance_score": _json_ready(row.governance_score),
        "governance_status": row.governance_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _public_note_payload(item: ResearchStrategyGovernancePublicNote) -> dict[str, object]:
    return {
        "key": item.key,
        "value": item.value,
        "paper_only": item.paper_only,
        "report_only": item.report_only,
        "readonly": item.readonly,
    }


def _report_payload(report: ResearchStrategyGovernanceReport) -> dict[str, object]:
    payload = _report_payload_without_digest(report)
    payload[_DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
    return payload


def _report_digest(report: ResearchStrategyGovernanceReport) -> str:
    return _canonical_digest(_report_payload_without_digest(report))


def _canonical_digest(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _validate_public_payload_digest(payload: dict[str, object]) -> None:
    digest = payload.get(_DERIVED_VALIDATION_DIGEST_FIELD)
    _require_digest(_DERIVED_VALIDATION_DIGEST_FIELD, digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop(_DERIVED_VALIDATION_DIGEST_FIELD, None)
    expected_digest = _canonical_digest(unsigned_payload)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest mismatch")


def _require_dict_str(values: dict[str, object], key: str) -> str:
    value = values.get(key)
    if type(value) is not str:
        raise ValueError(f"{key} must be a string")
    return value


def _require_dict_decimal(values: dict[str, object], key: str) -> Decimal:
    value = values.get(key)
    if type(value) is not Decimal:
        raise ValueError(f"{key} must be a Decimal")
    return value


def _require_dict_reason_codes(values: dict[str, object], key: str) -> tuple[str, ...]:
    value = values.get(key)
    if type(value) is not tuple:
        raise ValueError(f"{key} must be a tuple")
    return _normalize_reason_codes(value)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
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
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        raise ValueError("JSON numeric value must use Decimal-derived strings")
    if type(value) is str:
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


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    if type(value) is not dict:
        raise ValueError("payload must be a JSON object")
    copied: dict[str, object] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        copied[key] = _copy_json_value(item)
    return copied


def _copy_json_value(value: object) -> object:
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (int, float) or type(value) is Decimal:
        raise ValueError("public payload numerics must use Decimal-derived strings")
    if type(value) is dict:
        return _copy_json_object(value)
    if type(value) is list:
        return [_copy_json_value(item) for item in value]
    raise ValueError("public payload must be JSON serializable")


def _reject_public_numerics(value: object) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float, Decimal)):
        raise ValueError("public payload numerics must use Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if _has_unsafe_public_fragment(field.name):
                raise ValueError(f"unsafe public field in {label}: {field.name}")
            _reject_unsafe_public_payload(label, getattr(value, field.name))
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
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _reject_flag_downgrades(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in _FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True for {label}")
            _reject_flag_downgrades(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_flag_downgrades(label, item)


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_GOVERNANCE_REPORT_CONFIG_VERSION",
    "ResearchStrategyGovernanceCheck",
    "ResearchStrategyGovernancePublicNote",
    "ResearchStrategyGovernanceReport",
    "ResearchStrategyGovernanceReportConfig",
    "ResearchStrategyGovernanceReportRow",
    "build_research_strategy_governance_report",
    "research_strategy_governance_report_payload",
)
