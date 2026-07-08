"""Public-safe specialist team/domain learning velocity report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_LEARNING_VELOCITY_REPORT_CONFIG_VERSION",
    "ResearchTeamDomainLearningVelocityConfig",
    "ResearchTeamDomainLearningVelocityInput",
    "ResearchTeamDomainLearningVelocityReasonCodeCount",
    "ResearchTeamDomainLearningVelocityReport",
    "ResearchTeamDomainLearningVelocityRow",
    "build_research_team_domain_learning_velocity_report",
    "research_team_domain_learning_velocity_report_payload",
)


DEFAULT_RESEARCH_TEAM_DOMAIN_LEARNING_VELOCITY_REPORT_CONFIG_VERSION = (
    "research-team-domain-learning-velocity-report-v0"
)

STATUSES = ("pass", "watch", "block")
STATUS_RANK = {"block": Decimal("0.000000"), "watch": Decimal("1.000000"), "pass": Decimal("2.000000")}
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
PASS_REASON_CODE = "domain_learning_velocity_pass"
EMPTY_REPORT_REASON_CODE = "domain_learning_velocity_no_inputs"
REPORT_BLOCK_REASON_CODE = "domain_learning_velocity_report_block_rows"
REPORT_WATCH_REASON_CODE = "domain_learning_velocity_report_watch_rows"
REPORT_PASS_REASON_CODE = "domain_learning_velocity_report_pass"
BLOCK_REASON_CODES = (
    "outcome_count_block",
    "calibration_improvement_block",
    "memory_freshness_block",
    "evidence_miss_reduction_block",
    "review_capacity_block",
)
WATCH_REASON_CODES = (
    "outcome_count_watch",
    "calibration_improvement_watch",
    "memory_freshness_watch",
    "evidence_miss_reduction_watch",
    "review_capacity_watch",
)
ROW_REASON_CODES = (PASS_REASON_CODE,) + WATCH_REASON_CODES + BLOCK_REASON_CODES
REPORT_REASON_CODES = (
    REPORT_BLOCK_REASON_CODE,
    REPORT_WATCH_REASON_CODE,
    REPORT_PASS_REASON_CODE,
    EMPTY_REPORT_REASON_CODE,
)
HEX_CHARS = frozenset("0123456789abcdef")
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "raw",
        "event",
        "market",
        "source",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "recom" + "mendation",
        "siz" + "ing",
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
                raise ValueError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamDomainLearningVelocityConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_LEARNING_VELOCITY_REPORT_CONFIG_VERSION
    )
    watch_min_outcome_count: Decimal = Decimal("10.000000")
    pass_min_outcome_count: Decimal = Decimal("30.000000")
    watch_min_calibration_improvement: Decimal = Decimal("0.010000")
    pass_min_calibration_improvement: Decimal = Decimal("0.050000")
    watch_min_memory_freshness: Decimal = Decimal("0.600000")
    pass_min_memory_freshness: Decimal = Decimal("0.800000")
    watch_min_evidence_miss_reduction: Decimal = Decimal("0.250000")
    pass_min_evidence_miss_reduction: Decimal = Decimal("0.500000")
    watch_min_review_capacity: Decimal = Decimal("0.400000")
    pass_min_review_capacity: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainLearningVelocityConfig, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_LEARNING_VELOCITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("watch_min_outcome_count", "pass_min_outcome_count"):
            object.__setattr__(
                self,
                field_name,
                _require_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_min_calibration_improvement",
            "pass_min_calibration_improvement",
            "watch_min_memory_freshness",
            "pass_min_memory_freshness",
            "watch_min_evidence_miss_reduction",
            "pass_min_evidence_miss_reduction",
            "watch_min_review_capacity",
            "pass_min_review_capacity",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainLearningVelocityInput(_FinalPublicDataclass):
    specialist_team_key: str
    domain_key: str
    aggregate_outcome_count: Decimal
    calibration_improvement: Decimal
    memory_freshness: Decimal
    evidence_miss_reduction: Decimal
    review_capacity: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainLearningVelocityInput, "input")
        object.__setattr__(
            self,
            "specialist_team_key",
            _require_safe_key("specialist_team_key", self.specialist_team_key),
        )
        object.__setattr__(
            self,
            "domain_key",
            _require_safe_key("domain_key", self.domain_key),
        )
        object.__setattr__(
            self,
            "aggregate_outcome_count",
            _require_whole_decimal(
                "aggregate_outcome_count",
                self.aggregate_outcome_count,
            ),
        )
        for field_name in (
            "calibration_improvement",
            "memory_freshness",
            "evidence_miss_reduction",
            "review_capacity",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamDomainLearningVelocityRow(_FinalPublicDataclass):
    specialist_team_key: str
    domain_key: str
    status: str
    aggregate_outcome_count: Decimal
    calibration_improvement: Decimal
    memory_freshness: Decimal
    evidence_miss_reduction: Decimal
    review_capacity: Decimal
    learning_velocity_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainLearningVelocityRow, "row")
        object.__setattr__(
            self,
            "specialist_team_key",
            _require_safe_key("specialist_team_key", self.specialist_team_key),
        )
        object.__setattr__(
            self,
            "domain_key",
            _require_safe_key("domain_key", self.domain_key),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "aggregate_outcome_count",
            _require_whole_decimal(
                "aggregate_outcome_count",
                self.aggregate_outcome_count,
            ),
        )
        for field_name in (
            "calibration_improvement",
            "memory_freshness",
            "evidence_miss_reduction",
            "review_capacity",
            "learning_velocity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(
                self.reason_codes,
                allowed=ROW_REASON_CODES,
                require_nonempty=True,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamDomainLearningVelocityReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    team_domain_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainLearningVelocityReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code, allowed=ROW_REASON_CODES)
        object.__setattr__(self, "count", _require_whole_decimal("count", self.count))
        object.__setattr__(
            self,
            "team_domain_ratio",
            _require_ratio_decimal("team_domain_ratio", self.team_domain_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamDomainLearningVelocityReport(_FinalPublicDataclass):
    config_version: str
    generated_at: datetime
    status: str
    team_domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_outcome_count: Decimal
    average_calibration_improvement: Decimal
    average_memory_freshness: Decimal
    average_evidence_miss_reduction: Decimal
    average_review_capacity: Decimal
    average_learning_velocity_score: Decimal
    lowest_learning_velocity_score: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamDomainLearningVelocityReasonCodeCount, ...]
    rows: tuple[ResearchTeamDomainLearningVelocityRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainLearningVelocityReport, "report")
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        for field_name in (
            "team_domain_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_outcome_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_calibration_improvement",
            "average_memory_freshness",
            "average_evidence_miss_reduction",
            "average_review_capacity",
            "average_learning_velocity_score",
            "lowest_learning_velocity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(
                self.reason_codes,
                allowed=REPORT_REASON_CODES,
                require_nonempty=True,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_tuple_of_exact(
                "reason_code_counts",
                self.reason_code_counts,
                ResearchTeamDomainLearningVelocityReasonCodeCount,
            ),
        )
        object.__setattr__(
            self,
            "rows",
            _require_tuple_of_exact(
                "rows",
                self.rows,
                ResearchTeamDomainLearningVelocityRow,
            ),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        _require_hard_flags("report", self)


def build_research_team_domain_learning_velocity_report(
    items: Iterable[ResearchTeamDomainLearningVelocityInput],
    *,
    config: ResearchTeamDomainLearningVelocityConfig | None = None,
    generated_at: datetime,
) -> ResearchTeamDomainLearningVelocityReport:
    cfg = config if config is not None else ResearchTeamDomainLearningVelocityConfig()
    _require_exact_type(cfg, ResearchTeamDomainLearningVelocityConfig, "config")
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(_row_from_input(item, config=cfg, generated_at=generated_at_utc) for item in items)
    rows = tuple(sorted(rows, key=_row_sort_key))
    report_without_digest = _report_from_rows(
        rows,
        config=cfg,
        generated_at=generated_at_utc,
        derived_validation_digest="0" * 64,
    )
    unsigned_payload = _unsigned_payload(report_without_digest)
    digest = _digest_payload(unsigned_payload)
    return _report_from_rows(
        rows,
        config=cfg,
        generated_at=generated_at_utc,
        derived_validation_digest=digest,
    )


def research_team_domain_learning_velocity_report_payload(
    report: ResearchTeamDomainLearningVelocityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamDomainLearningVelocityReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_surface("report", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _validate_public_payload(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_surface("payload", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _validate_public_payload(payload)
        return payload
    raise ValueError("report must be a ResearchTeamDomainLearningVelocityReport")


def _row_from_input(
    item: ResearchTeamDomainLearningVelocityInput,
    *,
    config: ResearchTeamDomainLearningVelocityConfig,
    generated_at: datetime,
) -> ResearchTeamDomainLearningVelocityRow:
    _require_exact_type(item, ResearchTeamDomainLearningVelocityInput, "input")
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    reason_codes = _row_reason_codes(item, config=config)
    status = _status_for_reason_codes(reason_codes)
    return ResearchTeamDomainLearningVelocityRow(
        specialist_team_key=item.specialist_team_key,
        domain_key=item.domain_key,
        status=status,
        aggregate_outcome_count=item.aggregate_outcome_count,
        calibration_improvement=item.calibration_improvement,
        memory_freshness=item.memory_freshness,
        evidence_miss_reduction=item.evidence_miss_reduction,
        review_capacity=item.review_capacity,
        learning_velocity_score=_learning_velocity_score(item),
        observed_at=item.observed_at,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchTeamDomainLearningVelocityInput,
    *,
    config: ResearchTeamDomainLearningVelocityConfig,
) -> tuple[str, ...]:
    block_codes: list[str] = []
    watch_codes: list[str] = []
    _append_metric_reason(
        block_codes,
        watch_codes,
        metric_name="outcome_count",
        value=item.aggregate_outcome_count,
        watch_threshold=config.watch_min_outcome_count,
        pass_threshold=config.pass_min_outcome_count,
    )
    _append_metric_reason(
        block_codes,
        watch_codes,
        metric_name="calibration_improvement",
        value=item.calibration_improvement,
        watch_threshold=config.watch_min_calibration_improvement,
        pass_threshold=config.pass_min_calibration_improvement,
    )
    _append_metric_reason(
        block_codes,
        watch_codes,
        metric_name="memory_freshness",
        value=item.memory_freshness,
        watch_threshold=config.watch_min_memory_freshness,
        pass_threshold=config.pass_min_memory_freshness,
    )
    _append_metric_reason(
        block_codes,
        watch_codes,
        metric_name="evidence_miss_reduction",
        value=item.evidence_miss_reduction,
        watch_threshold=config.watch_min_evidence_miss_reduction,
        pass_threshold=config.pass_min_evidence_miss_reduction,
    )
    _append_metric_reason(
        block_codes,
        watch_codes,
        metric_name="review_capacity",
        value=item.review_capacity,
        watch_threshold=config.watch_min_review_capacity,
        pass_threshold=config.pass_min_review_capacity,
    )
    if block_codes:
        return tuple(block_codes)
    if watch_codes:
        return tuple(watch_codes)
    return (PASS_REASON_CODE,)


def _append_metric_reason(
    block_codes: list[str],
    watch_codes: list[str],
    *,
    metric_name: str,
    value: Decimal,
    watch_threshold: Decimal,
    pass_threshold: Decimal,
) -> None:
    if value < watch_threshold:
        block_codes.append(f"{metric_name}_block")
    elif value < pass_threshold:
        watch_codes.append(f"{metric_name}_watch")


def _learning_velocity_score(item: ResearchTeamDomainLearningVelocityInput) -> Decimal:
    total = (
        item.calibration_improvement
        + item.memory_freshness
        + item.evidence_miss_reduction
        + item.review_capacity
    )
    return _ratio(total / Decimal("4.000000"))


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_from_rows(
    rows: tuple[ResearchTeamDomainLearningVelocityRow, ...],
    *,
    config: ResearchTeamDomainLearningVelocityConfig,
    generated_at: datetime,
    derived_validation_digest: str,
) -> ResearchTeamDomainLearningVelocityReport:
    status = _report_status(rows)
    row_count = _whole(len(rows))
    pass_count = _whole(sum(1 for row in rows if row.status == "pass"))
    watch_count = _whole(sum(1 for row in rows if row.status == "watch"))
    block_count = _whole(sum(1 for row in rows if row.status == "block"))
    total_outcome_count = _sum_whole(row.aggregate_outcome_count for row in rows)
    reason_codes = _report_reason_codes(rows)
    return ResearchTeamDomainLearningVelocityReport(
        config_version=config.config_version,
        generated_at=generated_at,
        status=status,
        team_domain_count=row_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        total_outcome_count=total_outcome_count,
        average_calibration_improvement=_average_ratio(
            row.calibration_improvement for row in rows
        ),
        average_memory_freshness=_average_ratio(row.memory_freshness for row in rows),
        average_evidence_miss_reduction=_average_ratio(
            row.evidence_miss_reduction for row in rows
        ),
        average_review_capacity=_average_ratio(row.review_capacity for row in rows),
        average_learning_velocity_score=_average_ratio(
            row.learning_velocity_score for row in rows
        ),
        lowest_learning_velocity_score=_min_ratio(
            row.learning_velocity_score for row in rows
        ),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
        derived_validation_digest=derived_validation_digest,
    )


def _report_status(rows: tuple[ResearchTeamDomainLearningVelocityRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainLearningVelocityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REPORT_REASON_CODE,)
    reason_codes: list[str] = []
    if any(row.status == "block" for row in rows):
        reason_codes.append(REPORT_BLOCK_REASON_CODE)
    if any(row.status == "watch" for row in rows):
        reason_codes.append(REPORT_WATCH_REASON_CODE)
    if not reason_codes:
        reason_codes.append(REPORT_PASS_REASON_CODE)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchTeamDomainLearningVelocityRow, ...],
) -> tuple[ResearchTeamDomainLearningVelocityReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        for reason_code in row.reason_codes:
            counter[reason_code] += 1
    row_count = _whole(len(rows))
    ordered_reason_codes = [
        reason_code for reason_code in ROW_REASON_CODES if counter.get(reason_code, 0) > 0
    ]
    return tuple(
        ResearchTeamDomainLearningVelocityReasonCodeCount(
            reason_code=reason_code,
            count=_whole(counter[reason_code]),
            team_domain_ratio=_ratio(Decimal(counter[reason_code]) / row_count),
        )
        for reason_code in ordered_reason_codes
    )


def _row_sort_key(row: ResearchTeamDomainLearningVelocityRow) -> tuple[str, str]:
    return (row.specialist_team_key, row.domain_key)


def _sum_whole(values: Iterable[Decimal]) -> Decimal:
    total = Decimal("0.000000")
    with localcontext(DECIMAL_CONTEXT):
        for value in values:
            total += value
    return _whole(total)


def _average_ratio(values: Iterable[Decimal]) -> Decimal:
    collected = tuple(values)
    if not collected:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _ratio(sum(collected, Decimal("0.000000")) / Decimal(len(collected)))


def _min_ratio(values: Iterable[Decimal]) -> Decimal:
    collected = tuple(values)
    if not collected:
        return ZERO
    return _ratio(min(collected))


def _validate_config(config: ResearchTeamDomainLearningVelocityConfig) -> None:
    if config.watch_min_outcome_count > config.pass_min_outcome_count:
        raise ValueError("watch_min_outcome_count must not exceed pass_min_outcome_count")
    for watch_name, pass_name in (
        (
            "watch_min_calibration_improvement",
            "pass_min_calibration_improvement",
        ),
        ("watch_min_memory_freshness", "pass_min_memory_freshness"),
        (
            "watch_min_evidence_miss_reduction",
            "pass_min_evidence_miss_reduction",
        ),
        ("watch_min_review_capacity", "pass_min_review_capacity"),
    ):
        if getattr(config, watch_name) > getattr(config, pass_name):
            raise ValueError(f"{watch_name} must not exceed {pass_name}")


def _validate_row(row: ResearchTeamDomainLearningVelocityRow) -> None:
    expected_status = _status_for_reason_codes(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("row status does not match reason codes")


def _validate_report(report: ResearchTeamDomainLearningVelocityReport) -> None:
    if report.team_domain_count != _whole(len(report.rows)):
        raise ValueError("team_domain_count does not match rows")
    if report.pass_count != _whole(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count does not match rows")
    if report.watch_count != _whole(sum(1 for row in report.rows if row.status == "watch")):
        raise ValueError("watch_count does not match rows")
    if report.block_count != _whole(sum(1 for row in report.rows if row.status == "block")):
        raise ValueError("block_count does not match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("report status does not match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("report reason_codes do not match rows")
    if report.total_outcome_count != _sum_whole(
        row.aggregate_outcome_count for row in report.rows
    ):
        raise ValueError("total_outcome_count does not match rows")
    if report.average_learning_velocity_score != _average_ratio(
        row.learning_velocity_score for row in report.rows
    ):
        raise ValueError("average_learning_velocity_score does not match rows")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unsafe_public_surface("payload", payload)
    _reject_public_numerics(payload)
    _require_hard_flags("payload", _PayloadFlags(payload))
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if digest != _digest_payload(unsigned_payload):
        raise ValueError("derived_validation_digest mismatch")


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


def _unsigned_payload(report: ResearchTeamDomainLearningVelocityReport) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is str:
        return value
    if type(value) is bool:
        return value
    if type(value) in (int, float):
        raise ValueError("JSON numeric values must be Decimal-derived")
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_public_numerics(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value))
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
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface(label, item)


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _require_tuple_of_exact(
    field_name: str,
    value: object,
    item_type: type[object],
) -> tuple[Any, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be a tuple")
    for item in value:
        _require_exact_type(item, item_type, field_name)
    return value


def _require_reason_codes(
    value: object,
    *,
    allowed: tuple[str, ...],
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError("reason_codes must be a tuple")
    if require_nonempty and not value:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    for item in value:
        normalized.append(_require_reason_code("reason_code", item, allowed=allowed))
    if len(normalized) != len(set(normalized)):
        raise ValueError("reason_codes must be unique")
    ordered = tuple(reason_code for reason_code in allowed if reason_code in normalized)
    if tuple(normalized) != ordered:
        raise ValueError("reason_codes must be canonical")
    return tuple(normalized)


def _require_reason_code(
    field_name: str,
    value: object,
    *,
    allowed: tuple[str, ...],
) -> str:
    _require_public_string(field_name, value)
    if value not in allowed:
        raise ValueError(f"{field_name} is not supported")
    return value


def _require_status(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_safe_key(field_name: str, value: object) -> str:
    text = _require_public_string(field_name, value)
    if _has_unsafe_public_fragment(text):
        raise ValueError(f"{field_name} must be public-safe")
    if not text:
        raise ValueError(f"{field_name} must not be empty")
    if text.strip() != text:
        raise ValueError(f"{field_name} must not have surrounding whitespace")
    if not all(character.islower() or character.isdigit() or character == "_" for character in text):
        raise ValueError(f"{field_name} must use lowercase letters, digits, or underscores")
    return text


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be a str")
    if "\x00" in value:
        raise ValueError(f"{field_name} must not contain NUL")
    return value


def _require_whole_decimal(field_name: str, value: object) -> Decimal:
    number = _require_decimal(field_name, value)
    if number < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if number != number.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return _decimal(number)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    number = _require_decimal(field_name, value)
    if number < ZERO or number > ONE:
        raise ValueError(f"{field_name} must be in the unit interval")
    return _ratio(number)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _whole(value: int | Decimal) -> Decimal:
    return _decimal(Decimal(value))


def _ratio(value: Decimal) -> Decimal:
    return _decimal(value)


def _decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(DECIMAL_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    normalized = value.astimezone(UTC)
    if normalized.microsecond:
        raise ValueError(f"{field_name} must be a whole second")
    return normalized


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_exact_type(value: object, type_: type[object], label: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{label} must be exactly {type_.__name__}")
