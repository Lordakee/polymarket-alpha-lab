"""Public-safe specialist calibration quorum report reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any, cast


DEFAULT_RESEARCH_TEAM_SPECIALIST_CALIBRATION_QUORUM_CONFIG_VERSION = (
    "research-team-specialist-calibration-quorum-report-v0"
)

STATUSES = ("pass", "watch", "block")

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}

PASS_ROW_REASON_CODE = "specialist_calibration_quorum_vote_pass"
WATCH_ROW_REASON_CODE = "specialist_calibration_quorum_vote_watch"
BLOCK_ROW_REASON_CODE = "specialist_calibration_quorum_vote_block"
EMPTY_REPORT_REASON_CODE = "specialist_calibration_quorum_no_rows"
REPORT_PASS_REASON_CODE = "specialist_calibration_quorum_report_pass"
REPORT_WATCH_REASON_CODE = "specialist_calibration_quorum_report_watch"
REPORT_BLOCK_REASON_CODE = "specialist_calibration_quorum_report_block"

BELOW_MINIMUM_BLOCK_REASON = "specialist_calibration_quorum_below_minimum"
AGREEMENT_BLOCK_REASON = "specialist_calibration_quorum_agreement_block"
BLOCK_RATIO_BLOCK_REASON = "specialist_calibration_quorum_block_ratio_block"
EVIDENCE_BLOCK_REASON = "specialist_calibration_quorum_evidence_block"
AGREEMENT_WATCH_REASON = "specialist_calibration_quorum_agreement_watch"
BLOCK_RATIO_WATCH_REASON = "specialist_calibration_quorum_block_ratio_watch"
EVIDENCE_WATCH_REASON = "specialist_calibration_quorum_evidence_watch"

ROW_REASON_CODES = (
    BLOCK_ROW_REASON_CODE,
    WATCH_ROW_REASON_CODE,
    PASS_ROW_REASON_CODE,
)
REPORT_REASON_PREFIX_BY_STATUS = {
    "pass": REPORT_PASS_REASON_CODE,
    "watch": REPORT_WATCH_REASON_CODE,
    "block": REPORT_BLOCK_REASON_CODE,
}
REPORT_STATUS_REASON_CODES = (
    REPORT_PASS_REASON_CODE,
    REPORT_WATCH_REASON_CODE,
    REPORT_BLOCK_REASON_CODE,
)
REPORT_BLOCK_REASON_CODES = (
    BELOW_MINIMUM_BLOCK_REASON,
    AGREEMENT_BLOCK_REASON,
    BLOCK_RATIO_BLOCK_REASON,
    EVIDENCE_BLOCK_REASON,
)
REPORT_WATCH_REASON_CODES = (
    AGREEMENT_WATCH_REASON,
    BLOCK_RATIO_WATCH_REASON,
    EVIDENCE_WATCH_REASON,
)
REPORT_REASON_CODES = (
    EMPTY_REPORT_REASON_CODE,
    REPORT_PASS_REASON_CODE,
    REPORT_WATCH_REASON_CODE,
    REPORT_BLOCK_REASON_CODE,
) + REPORT_BLOCK_REASON_CODES + REPORT_WATCH_REASON_CODES
REASON_CODE_COUNT_PRIORITY = (
    EMPTY_REPORT_REASON_CODE,
    BLOCK_ROW_REASON_CODE,
    WATCH_ROW_REASON_CODE,
    PASS_ROW_REASON_CODE,
)
PUBLIC_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "specialist_count",
        "pass_count",
        "watch_count",
        "block_count",
        "quorum_gap_count",
        "agreement_ratio",
        "block_ratio",
        "average_evidence_score",
        "min_evidence_score",
        "consensus_status",
        "status",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
PUBLIC_REASON_CODE_COUNT_KEYS = frozenset(
    (
        "reason_code",
        "count",
        "specialist_ratio",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
PUBLIC_ROW_KEYS = frozenset(
    (
        "specialist_digest",
        "group_digest",
        "status",
        "evidence_score",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)

HEX_CHARS = frozenset("0123456789abcdef")
SAFE_IDENTIFIER_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
UNSAFE_IDENTIFIER_FRAGMENTS = frozenset(
    (
        "raw",
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "dsn",
        "table",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "trading",
        "buy",
        "sell",
        "recommend",
        "position",
    ),
)
UNSAFE_PUBLIC_KEY_FRAGMENTS = frozenset(
    (
        "raw",
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "trading",
        "buy",
        "sell",
        "recommend",
        "position",
    ),
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = frozenset(
    (
        "http://",
        "https://",
        "source_url",
        "source_text",
        "dsn",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "trading",
        "buy",
        "sell",
        "recommend",
        "position",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_CALIBRATION_QUORUM_CONFIG_VERSION",
    "ResearchTeamSpecialistCalibrationQuorumConfig",
    "ResearchTeamSpecialistCalibrationQuorumInput",
    "ResearchTeamSpecialistCalibrationQuorumRow",
    "ResearchTeamSpecialistCalibrationQuorumReasonCodeCount",
    "ResearchTeamSpecialistCalibrationQuorumReport",
    "build_research_team_specialist_calibration_quorum_report",
    "research_team_specialist_calibration_quorum_report_public_payload",
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
class ResearchTeamSpecialistCalibrationQuorumConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_CALIBRATION_QUORUM_CONFIG_VERSION
    )
    min_quorum_specialist_count: Decimal = Decimal("3")
    min_pass_agreement_ratio: Decimal = Decimal("0.750000")
    min_watch_agreement_ratio: Decimal = Decimal("0.600000")
    max_pass_block_ratio: Decimal = Decimal("0.000000")
    max_watch_block_ratio: Decimal = Decimal("0.250000")
    min_pass_average_evidence_score: Decimal = Decimal("0.800000")
    min_watch_average_evidence_score: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistCalibrationQuorumConfig,
            "config",
        )
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_CALIBRATION_QUORUM_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "min_quorum_specialist_count",
            _require_count_decimal(
                "min_quorum_specialist_count",
                self.min_quorum_specialist_count,
            ),
        )
        for field_name in (
            "min_pass_agreement_ratio",
            "min_watch_agreement_ratio",
            "max_pass_block_ratio",
            "max_watch_block_ratio",
            "min_pass_average_evidence_score",
            "min_watch_average_evidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistCalibrationQuorumInput(_FinalPublicDataclass):
    specialist_key: str
    calibration_group: str
    status: str
    evidence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistCalibrationQuorumInput, "input")
        _require_safe_identifier("specialist_key", self.specialist_key)
        _require_safe_identifier("calibration_group", self.calibration_group)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "evidence_score",
            _require_ratio_decimal("evidence_score", self.evidence_score),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistCalibrationQuorumRow(_FinalPublicDataclass):
    specialist_key: str
    calibration_group: str
    status: str
    evidence_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistCalibrationQuorumRow, "row")
        _require_safe_identifier("specialist_key", self.specialist_key)
        _require_safe_identifier("calibration_group", self.calibration_group)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "evidence_score",
            _require_ratio_decimal("evidence_score", self.evidence_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistCalibrationQuorumReasonCodeCount(
    _FinalPublicDataclass,
):
    reason_code: str
    count: Decimal
    specialist_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistCalibrationQuorumReasonCodeCount,
            "reason_code_count",
        )
        _require_public_text("reason_code", self.reason_code)
        if self.reason_code not in REASON_CODE_COUNT_PRIORITY:
            raise ValueError("reason_code must be supported")
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        if self.count == ZERO_COUNT:
            raise ValueError("count must be positive")
        object.__setattr__(
            self,
            "specialist_ratio",
            _require_ratio_decimal("specialist_ratio", self.specialist_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistCalibrationQuorumReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    specialist_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    quorum_gap_count: Decimal
    agreement_ratio: Decimal
    block_ratio: Decimal
    average_evidence_score: Decimal
    min_evidence_score: Decimal
    consensus_status: str
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchTeamSpecialistCalibrationQuorumReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchTeamSpecialistCalibrationQuorumRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistCalibrationQuorumReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_CALIBRATION_QUORUM_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "specialist_count",
            "pass_count",
            "watch_count",
            "block_count",
            "quorum_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "agreement_ratio",
            "block_ratio",
            "average_evidence_score",
            "min_evidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("consensus_status", self.consensus_status)
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        _require_hard_flags("report", self)
        _validate_report_materialized_fields(self)
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _derived_validation_digest(self):
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )

    @property
    def public_payload(self) -> dict[str, Any]:
        return research_team_specialist_calibration_quorum_report_public_payload(self)


def build_research_team_specialist_calibration_quorum_report(
    quorum_items: Iterable[ResearchTeamSpecialistCalibrationQuorumInput],
    *,
    config: ResearchTeamSpecialistCalibrationQuorumConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistCalibrationQuorumReport:
    if type(config) is not ResearchTeamSpecialistCalibrationQuorumConfig:
        raise ValueError(
            "config must be a ResearchTeamSpecialistCalibrationQuorumConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_quorum_items(quorum_items)
    rows = tuple(
        sorted(
            (_row_for_quorum_item(item) for item in items),
            key=_row_sort_key,
        ),
    )
    specialist_count = _count(len(rows))
    pass_count = _status_count(rows, "pass")
    watch_count = _status_count(rows, "watch")
    block_count = _status_count(rows, "block")
    reason_codes = _report_reason_codes(
        rows,
        config=config,
        specialist_count=specialist_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
    )
    status = _report_status(reason_codes)
    return ResearchTeamSpecialistCalibrationQuorumReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        specialist_count=specialist_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        quorum_gap_count=_quorum_gap_count(specialist_count, config),
        agreement_ratio=_agreement_ratio(
            specialist_count,
            pass_count,
            watch_count,
            block_count,
        ),
        block_ratio=_ratio(block_count, specialist_count),
        average_evidence_score=_mean_decimal(
            tuple(row.evidence_score for row in rows),
        ),
        min_evidence_score=_min_decimal(tuple(row.evidence_score for row in rows)),
        consensus_status=_consensus_status(pass_count, watch_count, block_count),
        status=status,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_team_specialist_calibration_quorum_report_public_payload(
    report: ResearchTeamSpecialistCalibrationQuorumReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamSpecialistCalibrationQuorumReport:
        _require_hard_flags("report", report)
        _validate_report_materialized_fields(report)
        if report.derived_validation_digest != _derived_validation_digest(report):
            raise ValueError("derived_validation_digest does not match report payload")
        payload = _report_payload(report)
        _reject_unsafe_public_payload("payload", payload)
        _reject_public_numeric_values(payload)
        _validate_public_payload(payload, validate_materialized=True)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _reject_public_numeric_values(report)
        _validate_public_payload(report, validate_materialized=False)
        _require_hard_flags("payload", _PayloadFlags(report))
        supplied_digest = report.get("derived_validation_digest")
        if type(supplied_digest) is not str:
            raise ValueError("derived_validation_digest is required")
        _require_sha256("derived_validation_digest", supplied_digest)
        if supplied_digest != _payload_validation_digest(report):
            raise ValueError("derived_validation_digest does not match report payload")
        _validate_public_payload(report, validate_materialized=True)
        return report
    raise ValueError("report must be a ResearchTeamSpecialistCalibrationQuorumReport")


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


def _normalize_quorum_items(
    quorum_items: Iterable[ResearchTeamSpecialistCalibrationQuorumInput],
) -> tuple[ResearchTeamSpecialistCalibrationQuorumInput, ...]:
    if isinstance(quorum_items, (str, bytes)):
        raise ValueError("quorum_items must be an iterable")
    try:
        items = tuple(quorum_items)
    except TypeError as exc:
        raise ValueError("quorum_items must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchTeamSpecialistCalibrationQuorumInput:
            raise ValueError(
                "quorum_items must contain "
                "ResearchTeamSpecialistCalibrationQuorumInput",
            )
        _require_hard_flags("input", item)
        if item.specialist_key in seen:
            raise ValueError("specialist_key values must be unique")
        seen.add(item.specialist_key)
    return items


def _row_for_quorum_item(
    item: ResearchTeamSpecialistCalibrationQuorumInput,
) -> ResearchTeamSpecialistCalibrationQuorumRow:
    return ResearchTeamSpecialistCalibrationQuorumRow(
        specialist_key=item.specialist_key,
        calibration_group=item.calibration_group,
        status=item.status,
        evidence_score=item.evidence_score,
        reason_codes=_row_reason_codes(item.status),
    )


def _row_reason_codes(status: str) -> tuple[str, ...]:
    if status == "block":
        return (BLOCK_ROW_REASON_CODE,)
    if status == "watch":
        return (WATCH_ROW_REASON_CODE,)
    if status == "pass":
        return (PASS_ROW_REASON_CODE,)
    raise ValueError("status must be one of pass, watch, block")


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistCalibrationQuorumRow, ...],
    *,
    config: ResearchTeamSpecialistCalibrationQuorumConfig,
    specialist_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REPORT_REASON_CODE,)
    report_reasons = _report_level_reasons(
        rows,
        config=config,
        specialist_count=specialist_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
    )
    status = _report_status_from_reasons(report_reasons)
    return (REPORT_REASON_PREFIX_BY_STATUS[status], *report_reasons)


def _report_level_reasons(
    rows: tuple[ResearchTeamSpecialistCalibrationQuorumRow, ...],
    *,
    config: ResearchTeamSpecialistCalibrationQuorumConfig,
    specialist_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
) -> tuple[str, ...]:
    if specialist_count < config.min_quorum_specialist_count:
        return (BELOW_MINIMUM_BLOCK_REASON,)

    reasons: list[str] = []
    agreement_ratio = _agreement_ratio(
        specialist_count,
        pass_count,
        watch_count,
        block_count,
    )
    block_ratio = _ratio(block_count, specialist_count)
    average_evidence_score = _mean_decimal(tuple(row.evidence_score for row in rows))

    if agreement_ratio < config.min_watch_agreement_ratio:
        reasons.append(AGREEMENT_BLOCK_REASON)
    elif agreement_ratio < config.min_pass_agreement_ratio:
        reasons.append(AGREEMENT_WATCH_REASON)

    if block_ratio > config.max_watch_block_ratio:
        reasons.append(BLOCK_RATIO_BLOCK_REASON)
    elif block_ratio > config.max_pass_block_ratio:
        reasons.append(BLOCK_RATIO_WATCH_REASON)

    if average_evidence_score < config.min_watch_average_evidence_score:
        reasons.append(EVIDENCE_BLOCK_REASON)
    elif average_evidence_score < config.min_pass_average_evidence_score:
        reasons.append(EVIDENCE_WATCH_REASON)

    return tuple(
        reason
        for reason in REPORT_BLOCK_REASON_CODES + REPORT_WATCH_REASON_CODES
        if reason in reasons
    )


def _report_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (EMPTY_REPORT_REASON_CODE,):
        return "block"
    if any(reason_code in REPORT_BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in REPORT_WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status_from_reasons(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in REPORT_BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in REPORT_WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchTeamSpecialistCalibrationQuorumRow, ...],
) -> tuple[ResearchTeamSpecialistCalibrationQuorumReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamSpecialistCalibrationQuorumReasonCodeCount(
                reason_code=EMPTY_REPORT_REASON_CODE,
                count=_count(1),
                specialist_ratio=ONE_RATIO,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        for reason_code in row.reason_codes:
            counter[reason_code] += 1
    denominator = _count(len(rows))
    priority = {
        reason_code: index
        for index, reason_code in enumerate(REASON_CODE_COUNT_PRIORITY)
    }
    return tuple(
        ResearchTeamSpecialistCalibrationQuorumReasonCodeCount(
            reason_code=reason_code,
            count=count,
            specialist_ratio=_ratio(count, denominator),
        )
        for count, reason_code in sorted(
            ((_count(count), reason_code) for reason_code, count in counter.items()),
            key=lambda item: (-item[0], priority.get(item[1], 999), item[1]),
        )
    )


def _row_sort_key(
    row: ResearchTeamSpecialistCalibrationQuorumRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[row.status],
        row.evidence_score,
        _identifier_digest("group", row.calibration_group),
        _identifier_digest("specialist", row.specialist_key),
    )


def _status_count(
    rows: tuple[ResearchTeamSpecialistCalibrationQuorumRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(row.status == status for row in rows))


def _quorum_gap_count(
    specialist_count: Decimal,
    config: ResearchTeamSpecialistCalibrationQuorumConfig,
) -> Decimal:
    if specialist_count >= config.min_quorum_specialist_count:
        return ZERO_COUNT
    return (config.min_quorum_specialist_count - specialist_count).quantize(
        COUNT_QUANTUM,
    )


def _agreement_ratio(
    specialist_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
) -> Decimal:
    if specialist_count == ZERO_COUNT:
        return ZERO_RATIO
    return _ratio(max(pass_count, watch_count, block_count), specialist_count)


def _consensus_status(
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
) -> str:
    max_count = max(pass_count, watch_count, block_count)
    if block_count == max_count:
        return "block"
    if watch_count == max_count:
        return "watch"
    return "pass"


def _validate_config(config: ResearchTeamSpecialistCalibrationQuorumConfig) -> None:
    if config.min_quorum_specialist_count == ZERO_COUNT:
        raise ValueError("min_quorum_specialist_count must be positive")
    if config.min_pass_agreement_ratio < config.min_watch_agreement_ratio:
        raise ValueError(
            "min_pass_agreement_ratio must be at least min_watch_agreement_ratio",
        )
    if config.max_watch_block_ratio < config.max_pass_block_ratio:
        raise ValueError(
            "max_watch_block_ratio must be at least max_pass_block_ratio",
        )
    if (
        config.min_pass_average_evidence_score
        < config.min_watch_average_evidence_score
    ):
        raise ValueError(
            "min_pass_average_evidence_score must be at least "
            "min_watch_average_evidence_score",
        )


def _validate_row(row: ResearchTeamSpecialistCalibrationQuorumRow) -> None:
    if row.reason_codes != _row_reason_codes(row.status):
        raise ValueError("reason_codes must match status")


def _validate_report_materialized_fields(
    report: ResearchTeamSpecialistCalibrationQuorumReport,
) -> None:
    rows = report.rows
    checks = {
        "specialist_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "agreement_ratio": _agreement_ratio(
            _count(len(rows)),
            _status_count(rows, "pass"),
            _status_count(rows, "watch"),
            _status_count(rows, "block"),
        ),
        "block_ratio": _ratio(_status_count(rows, "block"), _count(len(rows))),
        "average_evidence_score": _mean_decimal(
            tuple(row.evidence_score for row in rows),
        ),
        "min_evidence_score": _min_decimal(tuple(row.evidence_score for row in rows)),
        "consensus_status": _consensus_status(
            _status_count(rows, "pass"),
            _status_count(rows, "watch"),
            _status_count(rows, "block"),
        ),
        "reason_code_counts": _reason_code_counts(rows),
    }
    for field_name, expected in checks.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if not rows and report.reason_codes != (EMPTY_REPORT_REASON_CODE,):
        raise ValueError("reason_codes must match empty rows")
    if rows and report.reason_codes[0] != REPORT_REASON_PREFIX_BY_STATUS[report.status]:
        raise ValueError("reason_codes must start with report status reason")
    _validate_quorum_gap_reason_consistency(
        report.quorum_gap_count,
        report.reason_codes,
    )


def _validate_public_payload(
    payload: dict[str, Any],
    *,
    validate_materialized: bool,
) -> None:
    _require_payload_keys("payload", payload, PUBLIC_PAYLOAD_KEYS)
    _require_public_datetime("generated_at", payload["generated_at"])
    _require_public_text("config_version", payload["config_version"])
    if (
        payload["config_version"]
        != DEFAULT_RESEARCH_TEAM_SPECIALIST_CALIBRATION_QUORUM_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")

    counts = {
        field_name: _require_decimal_payload_string(
            field_name,
            payload[field_name],
            count=True,
        )
        for field_name in (
            "specialist_count",
            "pass_count",
            "watch_count",
            "block_count",
            "quorum_gap_count",
        )
    }
    ratios = {
        field_name: _require_decimal_payload_string(
            field_name,
            payload[field_name],
            ratio=True,
        )
        for field_name in (
            "agreement_ratio",
            "block_ratio",
            "average_evidence_score",
            "min_evidence_score",
        )
    }
    _require_status("consensus_status", payload["consensus_status"])
    _require_status("status", payload["status"])
    reason_codes = _require_report_reason_codes(
        _require_public_text_list("reason_codes", payload["reason_codes"]),
    )
    reason_code_counts = _validate_public_reason_code_counts(
        payload["reason_code_counts"],
    )
    rows = _validate_public_rows(payload["rows"])
    _require_hard_flags("payload", _PayloadFlags(payload))
    if validate_materialized:
        _validate_public_payload_materialized_fields(
            payload,
            counts=counts,
            ratios=ratios,
            reason_codes=reason_codes,
            reason_code_counts=reason_code_counts,
            rows=rows,
        )


def _validate_public_payload_materialized_fields(
    payload: dict[str, Any],
    *,
    counts: dict[str, Decimal],
    ratios: dict[str, Decimal],
    reason_codes: tuple[str, ...],
    reason_code_counts: tuple[dict[str, Decimal | str], ...],
    rows: tuple[dict[str, Decimal | str], ...],
) -> None:
    status_counts = {
        "pass_count": _count(sum(row["status"] == "pass" for row in rows)),
        "watch_count": _count(sum(row["status"] == "watch" for row in rows)),
        "block_count": _count(sum(row["status"] == "block" for row in rows)),
    }
    expected_counts = {"specialist_count": _count(len(rows)), **status_counts}
    for field_name, expected in expected_counts.items():
        if counts[field_name] != expected:
            raise ValueError(f"{field_name} must match rows")

    specialist_count = counts["specialist_count"]
    if ratios["agreement_ratio"] != _agreement_ratio(
        specialist_count,
        status_counts["pass_count"],
        status_counts["watch_count"],
        status_counts["block_count"],
    ):
        raise ValueError("agreement_ratio must match rows")
    if ratios["block_ratio"] != _ratio(status_counts["block_count"], specialist_count):
        raise ValueError("block_ratio must match rows")

    evidence_scores = tuple(
        row["evidence_score"]
        for row in rows
        if type(row["evidence_score"]) is Decimal
    )
    if ratios["average_evidence_score"] != _mean_decimal(evidence_scores):
        raise ValueError("average_evidence_score must match rows")
    if ratios["min_evidence_score"] != _min_decimal(evidence_scores):
        raise ValueError("min_evidence_score must match rows")
    if payload["consensus_status"] != _consensus_status(
        status_counts["pass_count"],
        status_counts["watch_count"],
        status_counts["block_count"],
    ):
        raise ValueError("consensus_status must match rows")
    if payload["status"] != _report_status(reason_codes):
        raise ValueError("status must match reason_codes")
    if not rows and reason_codes != (EMPTY_REPORT_REASON_CODE,):
        raise ValueError("reason_codes must match empty rows")
    if rows and reason_codes[0] != REPORT_REASON_PREFIX_BY_STATUS[payload["status"]]:
        raise ValueError("reason_codes must start with report status reason")
    _validate_quorum_gap_reason_consistency(
        counts["quorum_gap_count"],
        reason_codes,
    )

    expected_reason_code_counts = _public_reason_code_counts_from_rows(rows)
    if reason_code_counts != expected_reason_code_counts:
        raise ValueError("reason_code_counts must match rows")


def _public_reason_code_counts_from_rows(
    rows: tuple[dict[str, Decimal | str], ...],
) -> tuple[dict[str, Decimal | str], ...]:
    if not rows:
        return (
            {
                "reason_code": EMPTY_REPORT_REASON_CODE,
                "count": _count(1),
                "specialist_ratio": ONE_RATIO,
            },
        )
    counter: Counter[str] = Counter()
    for row in rows:
        reason_code = row.get("reason_code")
        if type(reason_code) is not str:
            raise ValueError("row reason_code must be a string")
        counter[reason_code] += 1
    denominator = _count(len(rows))
    priority = {
        reason_code: index
        for index, reason_code in enumerate(REASON_CODE_COUNT_PRIORITY)
    }
    return tuple(
        {
            "reason_code": reason_code,
            "count": count,
            "specialist_ratio": _ratio(count, denominator),
        }
        for count, reason_code in sorted(
            ((_count(count), reason_code) for reason_code, count in counter.items()),
            key=lambda item: (-item[0], priority.get(item[1], 999), item[1]),
        )
    )


def _validate_public_reason_code_counts(
    value: object,
) -> tuple[dict[str, Decimal | str], ...]:
    rows = _require_public_object_list("reason_code_counts", value)
    normalized: list[dict[str, Decimal | str]] = []
    for index, row in enumerate(rows):
        label = f"reason_code_counts[{index}]"
        _require_payload_keys(label, row, PUBLIC_REASON_CODE_COUNT_KEYS)
        _require_hard_flags(label, _PayloadFlags(row))
        _require_public_text("reason_code", row["reason_code"])
        if row["reason_code"] not in REASON_CODE_COUNT_PRIORITY:
            raise ValueError("reason_code must be supported")
        normalized.append(
            {
                "reason_code": row["reason_code"],
                "count": _require_decimal_payload_string(
                    "count",
                    row["count"],
                    count=True,
                ),
                "specialist_ratio": _require_decimal_payload_string(
                    "specialist_ratio",
                    row["specialist_ratio"],
                    ratio=True,
                ),
            },
        )
    if len({row["reason_code"] for row in normalized}) != len(normalized):
        raise ValueError("reason_code_counts reason_code values must be unique")
    return tuple(normalized)


def _validate_public_rows(value: object) -> tuple[dict[str, Decimal | str], ...]:
    rows = _require_public_object_list("rows", value)
    normalized: list[dict[str, Decimal | str]] = []
    specialist_digests: set[str] = set()
    for index, row in enumerate(rows):
        label = f"rows[{index}]"
        _require_payload_keys(label, row, PUBLIC_ROW_KEYS)
        specialist_digest = _require_prefixed_sha256(
            "specialist_digest",
            row["specialist_digest"],
        )
        if specialist_digest in specialist_digests:
            raise ValueError("specialist_digest values must be unique")
        specialist_digests.add(specialist_digest)
        group_digest = _require_prefixed_sha256(
            "group_digest",
            row["group_digest"],
        )
        _require_status("status", row["status"])
        reason_codes = _require_row_reason_codes(
            _require_public_text_list("reason_codes", row["reason_codes"]),
        )
        if reason_codes != _row_reason_codes(cast(str, row["status"])):
            raise ValueError("reason_codes must match status")
        _require_hard_flags(label, _PayloadFlags(row))
        normalized.append(
            {
                "specialist_digest": specialist_digest,
                "group_digest": group_digest,
                "status": row["status"],
                "evidence_score": _require_decimal_payload_string(
                    "evidence_score",
                    row["evidence_score"],
                    ratio=True,
                ),
                "reason_code": reason_codes[0],
            },
        )
    result = tuple(normalized)
    if result != tuple(sorted(result, key=_public_row_sort_key)):
        raise ValueError("rows must be in canonical order")
    return result


def _public_row_sort_key(
    row: dict[str, Decimal | str],
) -> tuple[Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[cast(str, row["status"])],
        cast(Decimal, row["evidence_score"]),
        cast(str, row["group_digest"]),
        cast(str, row["specialist_digest"]),
    )


def _require_payload_keys(
    label: str,
    payload: dict[str, Any],
    expected_keys: frozenset[str],
) -> None:
    if type(payload) is not dict:
        raise ValueError(f"{label} must be an object")
    if set(payload) != expected_keys:
        raise ValueError(f"{label} must contain only supported public fields")


def _require_public_datetime(field_name: str, value: object) -> None:
    _require_public_text(field_name, value)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime") from exc
    normalized = _as_utc(field_name, parsed)
    if value != normalized.isoformat():
        raise ValueError(f"{field_name} must be a canonical UTC ISO datetime")


def _require_public_text_list(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    normalized: list[str] = []
    for item in value:
        _require_public_text(field_name, item)
        normalized.append(item)
    return tuple(normalized)


def _require_public_object_list(
    field_name: str,
    value: object,
) -> tuple[dict[str, Any], ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    normalized: list[dict[str, Any]] = []
    for item in value:
        if type(item) is not dict:
            raise ValueError(f"{field_name} must contain objects")
        normalized.append(item)
    return tuple(normalized)


def _require_decimal_payload_string(
    field_name: str,
    value: object,
    *,
    count: bool = False,
    ratio: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if count:
        normalized = _require_count_decimal(field_name, parsed)
    elif ratio:
        normalized = _require_ratio_decimal(field_name, parsed)
    else:
        normalized = _require_decimal(field_name, parsed)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _require_prefixed_sha256(field_name: str, value: object) -> str:
    _require_public_text(field_name, value)
    if not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a sha256 digest")
    _require_sha256(field_name, value.removeprefix("sha256:"))
    return value


def _validate_quorum_gap_reason_consistency(
    quorum_gap_count: Decimal,
    reason_codes: tuple[str, ...],
) -> None:
    gap_reason_present = (
        reason_codes == (EMPTY_REPORT_REASON_CODE,)
        or BELOW_MINIMUM_BLOCK_REASON in reason_codes
    )
    if (quorum_gap_count > ZERO_COUNT) is not gap_reason_present:
        raise ValueError("quorum_gap_count must match reason_codes")


def _require_rows(
    rows: tuple[ResearchTeamSpecialistCalibrationQuorumRow, ...],
) -> tuple[ResearchTeamSpecialistCalibrationQuorumRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchTeamSpecialistCalibrationQuorumRow:
            raise ValueError(
                "rows must contain ResearchTeamSpecialistCalibrationQuorumRow",
            )
        _require_hard_flags("row", row)
        if row.specialist_key in seen:
            raise ValueError("rows must contain unique specialist_key values")
        seen.add(row.specialist_key)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and evidence_score")
    return normalized


def _require_reason_code_counts(
    rows: tuple[ResearchTeamSpecialistCalibrationQuorumReasonCodeCount, ...],
) -> tuple[ResearchTeamSpecialistCalibrationQuorumReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchTeamSpecialistCalibrationQuorumReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamSpecialistCalibrationQuorumReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", row)
    if len({row.reason_code for row in normalized}) != len(normalized):
        raise ValueError("reason_code_counts reason_code values must be unique")
    return normalized


def _require_row_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not normalized:
        raise ValueError("reason_codes must be non-empty")
    for reason_code in normalized:
        _require_public_text("reason_code", reason_code)
        if reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_code must be supported")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    if normalized != tuple(reason for reason in ROW_REASON_CODES if reason in normalized):
        raise ValueError("reason_codes must be sorted")
    if len(normalized) != 1:
        raise ValueError("vote reason_codes must contain exactly one reason")
    return normalized


def _require_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not normalized:
        raise ValueError("reason_codes must be non-empty")
    for reason_code in normalized:
        _require_public_text("reason_code", reason_code)
        if reason_code not in REPORT_REASON_CODES:
            raise ValueError("reason_code must be supported")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    if normalized == (EMPTY_REPORT_REASON_CODE,):
        return normalized
    if EMPTY_REPORT_REASON_CODE in normalized:
        raise ValueError("empty report reason must be the only reason_code")
    status_reasons = tuple(
        reason_code
        for reason_code in REPORT_STATUS_REASON_CODES
        if reason_code in normalized
    )
    if len(status_reasons) != 1:
        raise ValueError("reason_codes must contain exactly one report status reason")
    canonical = (
        status_reasons[0],
        *(
            reason_code
            for reason_code in REPORT_BLOCK_REASON_CODES + REPORT_WATCH_REASON_CODES
            if reason_code in normalized
        ),
    )
    if normalized != canonical:
        raise ValueError("reason_codes must be in canonical order")
    return normalized


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_safe_identifier(field_name: str, value: object) -> None:
    _require_public_text(field_name, value)
    if any(character not in SAFE_IDENTIFIER_CHARS for character in value):
        raise ValueError(f"{field_name} must be lowercase snake case")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_IDENTIFIER_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    _reject_unsafe_public_value(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be non-negative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    quantized = normalized.quantize(COUNT_QUANTUM)
    return ZERO_COUNT if quantized == ZERO_COUNT else quantized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be non-negative")
    quantized = _quantize_ratio(normalized)
    return ZERO_RATIO if quantized == ZERO_COUNT else quantized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be no greater than 1")
    return normalized


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _mean_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO_RATIO) / Decimal(len(values))).quantize(RATIO_QUANTUM)


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    return min(values).quantize(RATIO_QUANTUM)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _derived_validation_digest(
    report: ResearchTeamSpecialistCalibrationQuorumReport,
) -> str:
    payload = _report_payload_base(report)
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = _strip_digest(payload)
    canonical = json.dumps(
        digest_payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _strip_digest(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_digest(item)
            for key, item in sorted(value.items())
            if key != "derived_validation_digest"
        }
    if isinstance(value, list):
        return [_strip_digest(item) for item in value]
    return value


def _report_payload(
    report: ResearchTeamSpecialistCalibrationQuorumReport,
) -> dict[str, Any]:
    payload = _report_payload_base(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _report_payload_base(
    report: ResearchTeamSpecialistCalibrationQuorumReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "specialist_count": str(report.specialist_count),
        "pass_count": str(report.pass_count),
        "watch_count": str(report.watch_count),
        "block_count": str(report.block_count),
        "quorum_gap_count": str(report.quorum_gap_count),
        "agreement_ratio": str(report.agreement_ratio),
        "block_ratio": str(report.block_ratio),
        "average_evidence_score": str(report.average_evidence_score),
        "min_evidence_score": str(report.min_evidence_score),
        "consensus_status": report.consensus_status,
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            _reason_code_count_payload(row) for row in report.reason_code_counts
        ],
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _reason_code_count_payload(
    row: ResearchTeamSpecialistCalibrationQuorumReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": row.reason_code,
        "count": str(row.count),
        "specialist_ratio": str(row.specialist_ratio),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _row_payload(row: ResearchTeamSpecialistCalibrationQuorumRow) -> dict[str, Any]:
    return {
        "specialist_digest": _identifier_digest("specialist", row.specialist_key),
        "group_digest": _identifier_digest("group", row.calibration_group),
        "status": row.status,
        "evidence_score": str(row.evidence_score),
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _identifier_digest(namespace: str, value: str) -> str:
    canonical = json.dumps(
        {"namespace": namespace, "value": value},
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return "sha256:" + sha256(canonical.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload key for {label}")
            lowered = key.lower()
            if any(fragment in lowered for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
                raise ValueError(f"unsafe public payload key for {label}")
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(f"{label}[{index}]", item)
        return
    if isinstance(value, str):
        _reject_unsafe_public_value(label, value)


def _reject_unsafe_public_value(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"unsafe public value for {field_name}")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must be decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    if isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)
