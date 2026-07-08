"""Report-only domain specialist queue balance aggregates."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_QUEUE_BALANCE_CONFIG_VERSION = (
    "research-team-domain-specialist-queue-balance-report-v0"
)
QUEUE_BALANCE_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
HEX_CHARS = frozenset("0123456789abcdef")

PASS_REASON = "queue_balance_domain_clear"
EMPTY_REASON = "queue_balance_no_domains"
REPORT_REASON_BY_STATUS = {
    "pass": "queue_balance_report_pass",
    "watch": "queue_balance_report_watch",
    "block": "queue_balance_report_block",
}
MODE_BY_STATUS = {
    "pass": "paper_queue_balance_monitor",
    "watch": "paper_queue_balance_watch",
    "block": "paper_queue_balance_block",
}
ROW_REASON_SEQUENCE = (
    "queue_balance_backlog_pressure_block",
    "queue_balance_review_latency_block",
    "queue_balance_calibration_feedback_freshness_block",
    "queue_balance_memory_conflict_load_block",
    "queue_balance_backlog_pressure_watch",
    "queue_balance_review_latency_watch",
    "queue_balance_calibration_feedback_freshness_watch",
    "queue_balance_memory_conflict_load_watch",
    PASS_REASON,
)
REPORT_REASON_SEQUENCE = (
    "queue_balance_report_block",
    "queue_balance_report_watch",
    "queue_balance_report_pass",
    EMPTY_REASON,
) + ROW_REASON_SEQUENCE[:-1]
REASON_COUNT_SEQUENCE = (EMPTY_REASON,) + ROW_REASON_SEQUENCE


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _join_parts("r", "aw"),
        _join_parts("candi", "date"),
        _join_parts("mar", "ket"),
        _join_parts("sl", "ug"),
        _join_parts("ques", "tion"),
        _join_parts("u", "rl"),
        _join_parts("ht", "tp://"),
        _join_parts("ht", "tps://"),
        _join_parts("so", "urce"),
        _join_parts("d", "sn"),
        _join_parts("ta", "ble"),
        _join_parts("to", "ken"),
        _join_parts("sec", "ret"),
        _join_parts("creden", "tial"),
        _join_parts("pass", "word"),
        _join_parts("private", "_", "key"),
        _join_parts("wal", "let"),
        _join_parts("au", "th"),
        _join_parts("or", "der"),
        _join_parts("tr", "ade"),
        _join_parts("trad", "ing"),
        _join_parts("li", "ve"),
        _join_parts("b", "uy"),
        _join_parts("s", "ell"),
        _join_parts("recom", "mendation"),
        _join_parts("siz", "ing"),
        "position",
    ),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistQueueBalanceConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_QUEUE_BALANCE_CONFIG_VERSION
    )
    watch_backlog_pressure_ratio: Decimal = Decimal("0.750000")
    block_backlog_pressure_ratio: Decimal = Decimal("1.250000")
    watch_review_latency_seconds: Decimal = Decimal("3600.000000")
    block_review_latency_seconds: Decimal = Decimal("10800.000000")
    watch_calibration_feedback_age_seconds: Decimal = Decimal("604800.000000")
    block_calibration_feedback_age_seconds: Decimal = Decimal("1209600.000000")
    watch_memory_conflict_ratio: Decimal = Decimal("0.200000")
    block_memory_conflict_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainSpecialistQueueBalanceConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_QUEUE_BALANCE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_backlog_pressure_ratio",
            "block_backlog_pressure_ratio",
            "watch_review_latency_seconds",
            "block_review_latency_seconds",
            "watch_calibration_feedback_age_seconds",
            "block_calibration_feedback_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_memory_conflict_ratio",
            "block_memory_conflict_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistQueueBalanceInput(_FinalPublicDataclass):
    domain_label: str
    pending_backlog_count: Decimal
    domain_capacity_count: Decimal
    review_latency_seconds: Decimal
    calibration_feedback_age_seconds: Decimal
    memory_conflict_count: Decimal
    memory_item_count: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainSpecialistQueueBalanceInput,
            "input",
        )
        _require_public_label("domain_label", self.domain_label)
        for field_name in (
            "pending_backlog_count",
            "domain_capacity_count",
            "memory_conflict_count",
            "memory_item_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.domain_capacity_count <= ZERO:
            raise ValueError("domain_capacity_count must be positive")
        if self.memory_item_count <= ZERO:
            raise ValueError("memory_item_count must be positive")
        if self.memory_conflict_count > self.memory_item_count:
            raise ValueError("memory_conflict_count must be at most memory_item_count")
        for field_name in (
            "review_latency_seconds",
            "calibration_feedback_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistQueueBalanceRow(_FinalPublicDataclass):
    domain_label: str
    status: str
    pending_backlog_count: Decimal
    domain_capacity_count: Decimal
    backlog_pressure_ratio: Decimal
    review_latency_seconds: Decimal
    calibration_feedback_age_seconds: Decimal
    memory_conflict_count: Decimal
    memory_item_count: Decimal
    memory_conflict_ratio: Decimal
    queue_balance_score: Decimal
    observed_at: datetime
    observation_age_seconds: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainSpecialistQueueBalanceRow,
            "row",
        )
        _require_public_label("domain_label", self.domain_label)
        _require_status("status", self.status)
        for field_name in (
            "pending_backlog_count",
            "domain_capacity_count",
            "memory_conflict_count",
            "memory_item_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.domain_capacity_count <= ZERO:
            raise ValueError("domain_capacity_count must be positive")
        if self.memory_item_count <= ZERO:
            raise ValueError("memory_item_count must be positive")
        if self.memory_conflict_count > self.memory_item_count:
            raise ValueError("memory_conflict_count must be at most memory_item_count")
        for field_name in (
            "backlog_pressure_ratio",
            "review_latency_seconds",
            "calibration_feedback_age_seconds",
            "observation_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("memory_conflict_ratio", "queue_balance_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistQueueBalanceReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    domain_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainSpecialistQueueBalanceReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        if self.reason_code not in REASON_COUNT_SEQUENCE:
            raise ValueError("reason_code must be supported")
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "domain_ratio",
            _require_ratio_decimal("domain_ratio", self.domain_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamDomainSpecialistQueueBalanceReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    queue_balance_mode: str
    domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    imbalanced_domain_count: Decimal
    average_backlog_pressure_ratio: Decimal
    max_backlog_pressure_ratio: Decimal
    average_review_latency_seconds: Decimal
    max_review_latency_seconds: Decimal
    average_calibration_feedback_age_seconds: Decimal
    max_calibration_feedback_age_seconds: Decimal
    average_memory_conflict_ratio: Decimal
    max_memory_conflict_ratio: Decimal
    max_queue_balance_score: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamDomainSpecialistQueueBalanceReasonCodeCount, ...]
    rows: tuple[ResearchTeamDomainSpecialistQueueBalanceRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainSpecialistQueueBalanceReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_QUEUE_BALANCE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        _require_public_string("queue_balance_mode", self.queue_balance_mode)
        for field_name in (
            "domain_count",
            "pass_count",
            "watch_count",
            "block_count",
            "imbalanced_domain_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_backlog_pressure_ratio",
            "max_backlog_pressure_ratio",
            "average_review_latency_seconds",
            "max_review_latency_seconds",
            "average_calibration_feedback_age_seconds",
            "max_calibration_feedback_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_memory_conflict_ratio",
            "max_memory_conflict_ratio",
            "max_queue_balance_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
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
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        else:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError(
                    "derived_validation_digest does not match report payload",
                )


def build_research_team_domain_specialist_queue_balance_report(
    inputs: Iterable[ResearchTeamDomainSpecialistQueueBalanceInput],
    *,
    config: ResearchTeamDomainSpecialistQueueBalanceConfig,
    generated_at: datetime,
) -> ResearchTeamDomainSpecialistQueueBalanceReport:
    _require_exact_type(
        config,
        ResearchTeamDomainSpecialistQueueBalanceConfig,
        "config",
    )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_input(item, config=config, generated_at=generated_at_utc)
                for item in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    status = _report_status(rows)
    return ResearchTeamDomainSpecialistQueueBalanceReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=status,
        queue_balance_mode=MODE_BY_STATUS[status],
        domain_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        imbalanced_domain_count=_count(sum(row.status != "pass" for row in rows)),
        average_backlog_pressure_ratio=_average_decimal(
            row.backlog_pressure_ratio for row in rows
        ),
        max_backlog_pressure_ratio=_max_decimal(
            tuple(row.backlog_pressure_ratio for row in rows)
        ),
        average_review_latency_seconds=_average_decimal(
            row.review_latency_seconds for row in rows
        ),
        max_review_latency_seconds=_max_decimal(
            tuple(row.review_latency_seconds for row in rows)
        ),
        average_calibration_feedback_age_seconds=_average_decimal(
            row.calibration_feedback_age_seconds for row in rows
        ),
        max_calibration_feedback_age_seconds=_max_decimal(
            tuple(row.calibration_feedback_age_seconds for row in rows)
        ),
        average_memory_conflict_ratio=_average_decimal(
            row.memory_conflict_ratio for row in rows
        ),
        max_memory_conflict_ratio=_max_decimal(
            tuple(row.memory_conflict_ratio for row in rows)
        ),
        max_queue_balance_score=_max_decimal(
            tuple(row.queue_balance_score for row in rows)
        ),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_team_domain_specialist_queue_balance_report_payload(
    report: ResearchTeamDomainSpecialistQueueBalanceReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchTeamDomainSpecialistQueueBalanceReport:
        _require_hard_flags("report", report)
        if report.derived_validation_digest != _digest_from_values(
            _report_values_without_digest(report),
        ):
            raise ValueError("derived_validation_digest does not match report payload")
        _validate_report(report)
        payload = _json_ready(report)
    elif isinstance(report, Mapping):
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchTeamDomainSpecialistQueueBalanceReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_payload_flags(payload)
    _reject_public_numeric_values(payload)
    _reject_unsafe_public_payload(
        "report payload",
        payload,
        allow_json_containers=True,
    )
    expected_digest = _digest_from_payload(payload)
    if payload["derived_validation_digest"] != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    return payload


def research_team_domain_specialist_queue_balance_report_digest(
    report: ResearchTeamDomainSpecialistQueueBalanceReport | Mapping[str, object],
) -> str:
    payload = research_team_domain_specialist_queue_balance_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def _row_from_input(
    item: ResearchTeamDomainSpecialistQueueBalanceInput,
    *,
    config: ResearchTeamDomainSpecialistQueueBalanceConfig,
    generated_at: datetime,
) -> ResearchTeamDomainSpecialistQueueBalanceRow:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    backlog_pressure_ratio = _ratio_uncapped(
        item.pending_backlog_count,
        item.domain_capacity_count,
    )
    memory_conflict_ratio = _ratio_uncapped(
        item.memory_conflict_count,
        item.memory_item_count,
    )
    reason_codes = _row_reason_codes(
        backlog_pressure_ratio=backlog_pressure_ratio,
        review_latency_seconds=item.review_latency_seconds,
        calibration_feedback_age_seconds=item.calibration_feedback_age_seconds,
        memory_conflict_ratio=memory_conflict_ratio,
        config=config,
    )
    return ResearchTeamDomainSpecialistQueueBalanceRow(
        domain_label=item.domain_label,
        status=_row_status(reason_codes),
        pending_backlog_count=item.pending_backlog_count,
        domain_capacity_count=item.domain_capacity_count,
        backlog_pressure_ratio=backlog_pressure_ratio,
        review_latency_seconds=item.review_latency_seconds,
        calibration_feedback_age_seconds=item.calibration_feedback_age_seconds,
        memory_conflict_count=item.memory_conflict_count,
        memory_item_count=item.memory_item_count,
        memory_conflict_ratio=memory_conflict_ratio,
        queue_balance_score=_queue_balance_score(
            backlog_pressure_ratio=backlog_pressure_ratio,
            review_latency_seconds=item.review_latency_seconds,
            calibration_feedback_age_seconds=item.calibration_feedback_age_seconds,
            memory_conflict_ratio=memory_conflict_ratio,
            config=config,
        ),
        observed_at=item.observed_at,
        observation_age_seconds=_datetime_delta_seconds(generated_at, item.observed_at),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    backlog_pressure_ratio: Decimal,
    review_latency_seconds: Decimal,
    calibration_feedback_age_seconds: Decimal,
    memory_conflict_ratio: Decimal,
    config: ResearchTeamDomainSpecialistQueueBalanceConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_high_threshold_reason(
        reasons,
        metric=backlog_pressure_ratio,
        watch=config.watch_backlog_pressure_ratio,
        block=config.block_backlog_pressure_ratio,
        watch_code="queue_balance_backlog_pressure_watch",
        block_code="queue_balance_backlog_pressure_block",
    )
    _append_high_threshold_reason(
        reasons,
        metric=review_latency_seconds,
        watch=config.watch_review_latency_seconds,
        block=config.block_review_latency_seconds,
        watch_code="queue_balance_review_latency_watch",
        block_code="queue_balance_review_latency_block",
    )
    _append_high_threshold_reason(
        reasons,
        metric=calibration_feedback_age_seconds,
        watch=config.watch_calibration_feedback_age_seconds,
        block=config.block_calibration_feedback_age_seconds,
        watch_code="queue_balance_calibration_feedback_freshness_watch",
        block_code="queue_balance_calibration_feedback_freshness_block",
    )
    _append_high_threshold_reason(
        reasons,
        metric=memory_conflict_ratio,
        watch=config.watch_memory_conflict_ratio,
        block=config.block_memory_conflict_ratio,
        watch_code="queue_balance_memory_conflict_load_watch",
        block_code="queue_balance_memory_conflict_load_block",
    )
    if not reasons:
        return (PASS_REASON,)
    return _require_row_reason_codes(tuple(reasons))


def _append_high_threshold_reason(
    reasons: list[str],
    *,
    metric: Decimal,
    watch: Decimal,
    block: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if metric >= block:
        reasons.append(block_code)
        return
    if metric >= watch:
        reasons.append(watch_code)


def _queue_balance_score(
    *,
    backlog_pressure_ratio: Decimal,
    review_latency_seconds: Decimal,
    calibration_feedback_age_seconds: Decimal,
    memory_conflict_ratio: Decimal,
    config: ResearchTeamDomainSpecialistQueueBalanceConfig,
) -> Decimal:
    return _max_decimal(
        (
            _ratio_to_cap(backlog_pressure_ratio, config.block_backlog_pressure_ratio),
            _ratio_to_cap(review_latency_seconds, config.block_review_latency_seconds),
            _ratio_to_cap(
                calibration_feedback_age_seconds,
                config.block_calibration_feedback_age_seconds,
            ),
            _ratio_to_cap(memory_conflict_ratio, config.block_memory_conflict_ratio),
        ),
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchTeamDomainSpecialistQueueBalanceRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainSpecialistQueueBalanceRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    status = _report_status(rows)
    present = {reason for row in rows for reason in row.reason_codes}
    reasons = [REPORT_REASON_BY_STATUS[status]]
    reasons.extend(
        reason
        for reason in ROW_REASON_SEQUENCE[:-1]
        if reason in present
    )
    return tuple(reasons)


def _reason_code_counts(
    rows: tuple[ResearchTeamDomainSpecialistQueueBalanceRow, ...],
) -> tuple[ResearchTeamDomainSpecialistQueueBalanceReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamDomainSpecialistQueueBalanceReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=_count(1),
                domain_ratio=ONE,
            ),
        )
    counter = Counter(reason for row in rows for reason in row.reason_codes)
    domain_count = _count(len(rows))
    return tuple(
        ResearchTeamDomainSpecialistQueueBalanceReasonCodeCount(
            reason_code=reason,
            count=_count(counter[reason]),
            domain_ratio=_ratio_capped(_count(counter[reason]), domain_count),
        )
        for reason in REASON_COUNT_SEQUENCE
        if counter[reason] > 0
    )


def _row_sort_key(
    row: ResearchTeamDomainSpecialistQueueBalanceRow,
) -> tuple[int, Decimal, Decimal, Decimal, str]:
    return (
        -_status_rank(row.status),
        -row.queue_balance_score,
        -row.backlog_pressure_ratio,
        -row.review_latency_seconds,
        row.domain_label,
    )


def _status_rank(status: str) -> int:
    if status == "block":
        return 2
    if status == "watch":
        return 1
    return 0


def _status_count(
    rows: tuple[ResearchTeamDomainSpecialistQueueBalanceRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _normalize_inputs(
    inputs: Iterable[ResearchTeamDomainSpecialistQueueBalanceInput],
) -> tuple[ResearchTeamDomainSpecialistQueueBalanceInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        rows = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_domain_labels: set[str] = set()
    for item in rows:
        _require_exact_type(
            item,
            ResearchTeamDomainSpecialistQueueBalanceInput,
            "input",
        )
        _require_hard_flags("input", item)
        if item.domain_label in seen_domain_labels:
            raise ValueError("domain labels must be unique")
        seen_domain_labels.add(item.domain_label)
    return rows


def _validate_config(config: ResearchTeamDomainSpecialistQueueBalanceConfig) -> None:
    if config.watch_backlog_pressure_ratio > config.block_backlog_pressure_ratio:
        raise ValueError(
            "block_backlog_pressure_ratio must be at least "
            "watch_backlog_pressure_ratio",
        )
    if config.watch_review_latency_seconds > config.block_review_latency_seconds:
        raise ValueError(
            "block_review_latency_seconds must be at least "
            "watch_review_latency_seconds",
        )
    if (
        config.watch_calibration_feedback_age_seconds
        > config.block_calibration_feedback_age_seconds
    ):
        raise ValueError(
            "block_calibration_feedback_age_seconds must be at least "
            "watch_calibration_feedback_age_seconds",
        )
    if config.watch_memory_conflict_ratio > config.block_memory_conflict_ratio:
        raise ValueError(
            "block_memory_conflict_ratio must be at least "
            "watch_memory_conflict_ratio",
        )


def _validate_row(row: ResearchTeamDomainSpecialistQueueBalanceRow) -> None:
    if row.backlog_pressure_ratio != _ratio_uncapped(
        row.pending_backlog_count,
        row.domain_capacity_count,
    ):
        raise ValueError("backlog_pressure_ratio must match backlog and capacity")
    if row.memory_conflict_ratio != _ratio_uncapped(
        row.memory_conflict_count,
        row.memory_item_count,
    ):
        raise ValueError("memory_conflict_ratio must match memory counts")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must use the clear reason")
    if row.status != "pass" and row.reason_codes == (PASS_REASON,):
        raise ValueError("reason_codes must match status")


def _validate_report(report: ResearchTeamDomainSpecialistQueueBalanceReport) -> None:
    rows = report.rows
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.queue_balance_mode != MODE_BY_STATUS[report.status]:
        raise ValueError("queue_balance_mode must match status")
    checks = {
        "domain_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "imbalanced_domain_count": _count(sum(row.status != "pass" for row in rows)),
        "average_backlog_pressure_ratio": _average_decimal(
            row.backlog_pressure_ratio for row in rows
        ),
        "max_backlog_pressure_ratio": _max_decimal(
            tuple(row.backlog_pressure_ratio for row in rows)
        ),
        "average_review_latency_seconds": _average_decimal(
            row.review_latency_seconds for row in rows
        ),
        "max_review_latency_seconds": _max_decimal(
            tuple(row.review_latency_seconds for row in rows)
        ),
        "average_calibration_feedback_age_seconds": _average_decimal(
            row.calibration_feedback_age_seconds for row in rows
        ),
        "max_calibration_feedback_age_seconds": _max_decimal(
            tuple(row.calibration_feedback_age_seconds for row in rows)
        ),
        "average_memory_conflict_ratio": _average_decimal(
            row.memory_conflict_ratio for row in rows
        ),
        "max_memory_conflict_ratio": _max_decimal(
            tuple(row.memory_conflict_ratio for row in rows)
        ),
        "max_queue_balance_score": _max_decimal(
            tuple(row.queue_balance_score for row in rows)
        ),
    }
    for field_name, expected in checks.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_rows(
    rows: tuple[ResearchTeamDomainSpecialistQueueBalanceRow, ...],
) -> tuple[ResearchTeamDomainSpecialistQueueBalanceRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_domain_labels: set[str] = set()
    for row in normalized:
        _require_exact_type(
            row,
            ResearchTeamDomainSpecialistQueueBalanceRow,
            "row",
        )
        _require_hard_flags("row", row)
        if row.domain_label in seen_domain_labels:
            raise ValueError("rows must contain unique domain labels")
        seen_domain_labels.add(row.domain_label)
    return tuple(sorted(normalized, key=_row_sort_key))


def _require_reason_code_counts(
    counts: tuple[ResearchTeamDomainSpecialistQueueBalanceReasonCodeCount, ...],
) -> tuple[ResearchTeamDomainSpecialistQueueBalanceReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for count in normalized:
        _require_exact_type(
            count,
            ResearchTeamDomainSpecialistQueueBalanceReasonCodeCount,
            "reason_code_count",
        )
        _require_hard_flags("reason_code_count", count)
    if len({count.reason_code for count in normalized}) != len(normalized):
        raise ValueError("reason_code_counts must use unique reason codes")
    return tuple(
        sorted(
            normalized,
            key=lambda count: REASON_COUNT_SEQUENCE.index(count.reason_code),
        ),
    )


def _require_report_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        _require_public_string("reason_code", reason_code)
        if reason_code not in REPORT_REASON_SEQUENCE:
            raise ValueError("reason_code must be supported")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return tuple(
        reason
        for reason in REPORT_REASON_SEQUENCE
        if reason in set(normalized)
    )


def _require_row_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        _require_public_string("reason_code", reason_code)
        if reason_code not in ROW_REASON_SEQUENCE:
            raise ValueError("reason_code must be supported")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    sorted_reasons = tuple(
        reason for reason in ROW_REASON_SEQUENCE if reason in set(normalized)
    )
    if PASS_REASON in sorted_reasons and len(sorted_reasons) != 1:
        raise ValueError("clear reason must not be mixed with pressure reasons")
    return sorted_reasons


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in QUEUE_BALANCE_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_public_label(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if PUBLIC_LABEL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public aggregate label")
    try:
        _reject_unsafe_public_text(field_name, value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a public aggregate label") from exc


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be true")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be true")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be true")


def _require_payload_flags(payload: dict[str, object]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if field_name not in payload or payload[field_name] is not True:
            raise ValueError(f"report payload {field_name} must be true")


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(normalized)


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return _quantize(normalized)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    microseconds = (
        Decimal(delta.days) * Decimal("86400000000")
        + Decimal(delta.seconds) * Decimal("1000000")
        + Decimal(delta.microseconds)
    )
    return _quantize(microseconds / Decimal("1000000"))


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("sum values must be Decimal")
        total = _quantize(total + value)
    return total


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return _quantize(_sum_decimal(normalized) / Decimal(len(normalized)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(max(values))


def _ratio_uncapped(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    return _quantize(numerator / denominator)


def _ratio_capped(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO
    return _clamp_ratio(numerator / denominator)


def _ratio_to_cap(value: Decimal, cap: Decimal) -> Decimal:
    if cap <= ZERO:
        return ONE if value > ZERO else ZERO
    return _clamp_ratio(value / cap)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _report_values_without_digest(
    report: ResearchTeamDomainSpecialistQueueBalanceReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return _digest_from_payload(payload)


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode(
        "utf-8",
    )
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is bool or type(value) is str or value is None:
        return value
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must be Decimal strings")
    raise ValueError(f"unsupported public payload value: {type(value).__name__}")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must be Decimal strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if isinstance(value, list | tuple):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if allow_json_containers and isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} contains unsafe public key")
            _reject_unsafe_public_text("public key", key)
            _reject_unsafe_public_payload(
                str(key),
                item,
                allow_json_containers=True,
            )
        return
    if allow_json_containers and isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
            )
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(field.name, getattr(value, field.name))


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")


__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_QUEUE_BALANCE_CONFIG_VERSION",
    "QUEUE_BALANCE_STATUSES",
    "ResearchTeamDomainSpecialistQueueBalanceConfig",
    "ResearchTeamDomainSpecialistQueueBalanceInput",
    "ResearchTeamDomainSpecialistQueueBalanceReasonCodeCount",
    "ResearchTeamDomainSpecialistQueueBalanceReport",
    "ResearchTeamDomainSpecialistQueueBalanceRow",
    "build_research_team_domain_specialist_queue_balance_report",
    "research_team_domain_specialist_queue_balance_report_digest",
    "research_team_domain_specialist_queue_balance_report_payload",
)
