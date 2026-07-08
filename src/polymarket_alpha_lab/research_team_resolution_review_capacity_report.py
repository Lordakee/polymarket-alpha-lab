"""Public-safe resolution review capacity report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_TEAM_RESOLUTION_REVIEW_CAPACITY_REPORT_CONFIG_VERSION",
    "ResearchTeamResolutionReviewCapacityConfig",
    "ResearchTeamResolutionReviewCapacityInput",
    "ResearchTeamResolutionReviewCapacityReasonCodeCount",
    "ResearchTeamResolutionReviewCapacityReport",
    "ResearchTeamResolutionReviewCapacityRow",
    "build_research_team_resolution_review_capacity_report",
    "research_team_resolution_review_capacity_report_payload",
)


DEFAULT_RESEARCH_TEAM_RESOLUTION_REVIEW_CAPACITY_REPORT_CONFIG_VERSION = (
    "research-team-resolution-review-capacity-report-v0"
)

STATUSES = ("pass", "watch", "block")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
PASS_REASON_CODE = "resolution_review_capacity_pass"
EMPTY_REPORT_REASON_CODE = "resolution_review_capacity_no_inputs"
REPORT_BLOCK_REASON_CODE = "resolution_review_capacity_report_block_rows"
REPORT_WATCH_REASON_CODE = "resolution_review_capacity_report_watch_rows"
REPORT_PASS_REASON_CODE = "resolution_review_capacity_report_pass"
WATCH_REASON_CODES = (
    "deadline_proximity_watch",
    "evidence_age_watch",
    "oracle_lag_watch",
    "team_capacity_watch",
    "domain_expertise_watch",
)
BLOCK_REASON_CODES = (
    "deadline_proximity_block",
    "evidence_age_block",
    "oracle_lag_block",
    "team_capacity_block",
    "domain_expertise_block",
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
class ResearchTeamResolutionReviewCapacityConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_RESOLUTION_REVIEW_CAPACITY_REPORT_CONFIG_VERSION
    )
    pass_max_deadline_proximity: Decimal = Decimal("0.300000")
    watch_max_deadline_proximity: Decimal = Decimal("0.700000")
    pass_max_evidence_age_seconds: Decimal = Decimal("21600.000000")
    watch_max_evidence_age_seconds: Decimal = Decimal("86400.000000")
    pass_max_oracle_lag_seconds: Decimal = Decimal("1200.000000")
    watch_max_oracle_lag_seconds: Decimal = Decimal("7200.000000")
    watch_min_team_capacity: Decimal = Decimal("0.500000")
    pass_min_team_capacity: Decimal = Decimal("0.750000")
    watch_min_domain_expertise: Decimal = Decimal("0.500000")
    pass_min_domain_expertise: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamResolutionReviewCapacityConfig, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_RESOLUTION_REVIEW_CAPACITY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_max_deadline_proximity",
            "watch_max_deadline_proximity",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_max_evidence_age_seconds",
            "watch_max_evidence_age_seconds",
            "pass_max_oracle_lag_seconds",
            "watch_max_oracle_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_min_team_capacity",
            "pass_min_team_capacity",
            "watch_min_domain_expertise",
            "pass_min_domain_expertise",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamResolutionReviewCapacityInput(_FinalPublicDataclass):
    review_team_key: str
    domain_key: str
    aggregate_deadline_proximity: Decimal
    evidence_age_seconds: Decimal
    oracle_lag_seconds: Decimal
    team_capacity: Decimal
    domain_expertise: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamResolutionReviewCapacityInput, "input")
        object.__setattr__(
            self,
            "review_team_key",
            _require_safe_key("review_team_key", self.review_team_key),
        )
        object.__setattr__(
            self,
            "domain_key",
            _require_safe_key("domain_key", self.domain_key),
        )
        object.__setattr__(
            self,
            "aggregate_deadline_proximity",
            _require_ratio_decimal(
                "aggregate_deadline_proximity",
                self.aggregate_deadline_proximity,
            ),
        )
        for field_name in ("evidence_age_seconds", "oracle_lag_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("team_capacity", "domain_expertise"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamResolutionReviewCapacityRow(_FinalPublicDataclass):
    review_team_key: str
    domain_key: str
    status: str
    aggregate_deadline_proximity: Decimal
    evidence_age_seconds: Decimal
    oracle_lag_seconds: Decimal
    team_capacity: Decimal
    domain_expertise: Decimal
    capacity_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamResolutionReviewCapacityRow, "row")
        object.__setattr__(
            self,
            "review_team_key",
            _require_safe_key("review_team_key", self.review_team_key),
        )
        object.__setattr__(
            self,
            "domain_key",
            _require_safe_key("domain_key", self.domain_key),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "aggregate_deadline_proximity",
            _require_ratio_decimal(
                "aggregate_deadline_proximity",
                self.aggregate_deadline_proximity,
            ),
        )
        for field_name in ("evidence_age_seconds", "oracle_lag_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("team_capacity", "domain_expertise", "capacity_score"):
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
class ResearchTeamResolutionReviewCapacityReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    review_scope_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamResolutionReviewCapacityReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code, allowed=ROW_REASON_CODES)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "review_scope_ratio",
            _require_ratio_decimal("review_scope_ratio", self.review_scope_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamResolutionReviewCapacityReport(_FinalPublicDataclass):
    config_version: str
    generated_at: datetime
    status: str
    review_scope_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_deadline_proximity: Decimal
    average_evidence_age_seconds: Decimal
    average_oracle_lag_seconds: Decimal
    average_team_capacity: Decimal
    average_domain_expertise: Decimal
    average_capacity_score: Decimal
    lowest_capacity_score: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchTeamResolutionReviewCapacityReasonCodeCount, ...]
    rows: tuple[ResearchTeamResolutionReviewCapacityRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamResolutionReviewCapacityReport, "report")
        _require_public_string("config_version", self.config_version)
        _require_status("status", self.status)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        for field_name in ("review_scope_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_deadline_proximity",
            "average_team_capacity",
            "average_domain_expertise",
            "average_capacity_score",
            "lowest_capacity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_evidence_age_seconds", "average_oracle_lag_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
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
                ResearchTeamResolutionReviewCapacityReasonCodeCount,
            ),
        )
        object.__setattr__(
            self,
            "rows",
            _require_tuple_of_exact(
                "rows",
                self.rows,
                ResearchTeamResolutionReviewCapacityRow,
            ),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        _require_hard_flags("report", self)


def build_research_team_resolution_review_capacity_report(
    items: Iterable[ResearchTeamResolutionReviewCapacityInput],
    *,
    config: ResearchTeamResolutionReviewCapacityConfig | None = None,
    generated_at: datetime,
) -> ResearchTeamResolutionReviewCapacityReport:
    cfg = config if config is not None else ResearchTeamResolutionReviewCapacityConfig()
    _require_exact_type(cfg, ResearchTeamResolutionReviewCapacityConfig, "config")
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


def research_team_resolution_review_capacity_report_payload(
    report: ResearchTeamResolutionReviewCapacityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamResolutionReviewCapacityReport:
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
    raise ValueError("report must be a ResearchTeamResolutionReviewCapacityReport")


def _row_from_input(
    item: ResearchTeamResolutionReviewCapacityInput,
    *,
    config: ResearchTeamResolutionReviewCapacityConfig,
    generated_at: datetime,
) -> ResearchTeamResolutionReviewCapacityRow:
    _require_exact_type(item, ResearchTeamResolutionReviewCapacityInput, "input")
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    reason_codes = _row_reason_codes(item, config=config)
    status = _status_for_reason_codes(reason_codes)
    return ResearchTeamResolutionReviewCapacityRow(
        review_team_key=item.review_team_key,
        domain_key=item.domain_key,
        status=status,
        aggregate_deadline_proximity=item.aggregate_deadline_proximity,
        evidence_age_seconds=item.evidence_age_seconds,
        oracle_lag_seconds=item.oracle_lag_seconds,
        team_capacity=item.team_capacity,
        domain_expertise=item.domain_expertise,
        capacity_score=_capacity_score(item, config),
        observed_at=item.observed_at,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchTeamResolutionReviewCapacityInput,
    *,
    config: ResearchTeamResolutionReviewCapacityConfig,
) -> tuple[str, ...]:
    block_codes: list[str] = []
    watch_codes: list[str] = []
    _append_max_reason(
        block_codes,
        watch_codes,
        metric_name="deadline_proximity",
        value=item.aggregate_deadline_proximity,
        pass_threshold=config.pass_max_deadline_proximity,
        watch_threshold=config.watch_max_deadline_proximity,
    )
    _append_max_reason(
        block_codes,
        watch_codes,
        metric_name="evidence_age",
        value=item.evidence_age_seconds,
        pass_threshold=config.pass_max_evidence_age_seconds,
        watch_threshold=config.watch_max_evidence_age_seconds,
    )
    _append_max_reason(
        block_codes,
        watch_codes,
        metric_name="oracle_lag",
        value=item.oracle_lag_seconds,
        pass_threshold=config.pass_max_oracle_lag_seconds,
        watch_threshold=config.watch_max_oracle_lag_seconds,
    )
    _append_min_reason(
        block_codes,
        watch_codes,
        metric_name="team_capacity",
        value=item.team_capacity,
        watch_threshold=config.watch_min_team_capacity,
        pass_threshold=config.pass_min_team_capacity,
    )
    _append_min_reason(
        block_codes,
        watch_codes,
        metric_name="domain_expertise",
        value=item.domain_expertise,
        watch_threshold=config.watch_min_domain_expertise,
        pass_threshold=config.pass_min_domain_expertise,
    )
    if block_codes:
        return tuple(block_codes)
    if watch_codes:
        return tuple(watch_codes)
    return (PASS_REASON_CODE,)


def _append_max_reason(
    block_codes: list[str],
    watch_codes: list[str],
    *,
    metric_name: str,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> None:
    if value > watch_threshold:
        block_codes.append(f"{metric_name}_block")
    elif value > pass_threshold:
        watch_codes.append(f"{metric_name}_watch")


def _append_min_reason(
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


def _capacity_score(
    item: ResearchTeamResolutionReviewCapacityInput,
    config: ResearchTeamResolutionReviewCapacityConfig,
) -> Decimal:
    values = (
        ONE - item.aggregate_deadline_proximity,
        _remaining_capacity(item.evidence_age_seconds, config.watch_max_evidence_age_seconds),
        _remaining_capacity(item.oracle_lag_seconds, config.watch_max_oracle_lag_seconds),
        item.team_capacity,
        item.domain_expertise,
    )
    with localcontext(DECIMAL_CONTEXT):
        return _ratio(sum(values, ZERO) / Decimal("5.000000"))


def _remaining_capacity(value: Decimal, maximum: Decimal) -> Decimal:
    if maximum == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        remaining = ONE - (value / maximum)
    if remaining <= ZERO:
        return ZERO
    if remaining >= ONE:
        return ONE
    return _ratio(remaining)


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_from_rows(
    rows: tuple[ResearchTeamResolutionReviewCapacityRow, ...],
    *,
    config: ResearchTeamResolutionReviewCapacityConfig,
    generated_at: datetime,
    derived_validation_digest: str,
) -> ResearchTeamResolutionReviewCapacityReport:
    status = _report_status(rows)
    row_count = _decimal(len(rows))
    pass_count = _decimal(sum(1 for row in rows if row.status == "pass"))
    watch_count = _decimal(sum(1 for row in rows if row.status == "watch"))
    block_count = _decimal(sum(1 for row in rows if row.status == "block"))
    return ResearchTeamResolutionReviewCapacityReport(
        config_version=config.config_version,
        generated_at=generated_at,
        status=status,
        review_scope_count=row_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        average_deadline_proximity=_average_decimal(
            row.aggregate_deadline_proximity for row in rows
        ),
        average_evidence_age_seconds=_average_decimal(
            row.evidence_age_seconds for row in rows
        ),
        average_oracle_lag_seconds=_average_decimal(
            row.oracle_lag_seconds for row in rows
        ),
        average_team_capacity=_average_decimal(row.team_capacity for row in rows),
        average_domain_expertise=_average_decimal(row.domain_expertise for row in rows),
        average_capacity_score=_average_decimal(row.capacity_score for row in rows),
        lowest_capacity_score=_min_decimal(row.capacity_score for row in rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
        derived_validation_digest=derived_validation_digest,
    )


def _report_status(rows: tuple[ResearchTeamResolutionReviewCapacityRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamResolutionReviewCapacityRow, ...],
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
    rows: tuple[ResearchTeamResolutionReviewCapacityRow, ...],
) -> tuple[ResearchTeamResolutionReviewCapacityReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        for reason_code in row.reason_codes:
            counter[reason_code] += 1
    row_count = _decimal(len(rows))
    ordered_reason_codes = [
        reason_code for reason_code in ROW_REASON_CODES if counter.get(reason_code, 0) > 0
    ]
    return tuple(
        ResearchTeamResolutionReviewCapacityReasonCodeCount(
            reason_code=reason_code,
            count=_decimal(counter[reason_code]),
            review_scope_ratio=_ratio(Decimal(counter[reason_code]) / row_count),
        )
        for reason_code in ordered_reason_codes
    )


def _row_sort_key(row: ResearchTeamResolutionReviewCapacityRow) -> tuple[str, str]:
    return (row.review_team_key, row.domain_key)


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    collected = tuple(values)
    if not collected:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _decimal(sum(collected, ZERO) / Decimal(len(collected)))


def _min_decimal(values: Iterable[Decimal]) -> Decimal:
    collected = tuple(values)
    if not collected:
        return ZERO
    return _decimal(min(collected))


def _validate_config(config: ResearchTeamResolutionReviewCapacityConfig) -> None:
    for pass_name, watch_name in (
        ("pass_max_deadline_proximity", "watch_max_deadline_proximity"),
        ("pass_max_evidence_age_seconds", "watch_max_evidence_age_seconds"),
        ("pass_max_oracle_lag_seconds", "watch_max_oracle_lag_seconds"),
    ):
        if getattr(config, pass_name) > getattr(config, watch_name):
            raise ValueError(f"{pass_name} must not exceed {watch_name}")
    for watch_name, pass_name in (
        ("watch_min_team_capacity", "pass_min_team_capacity"),
        ("watch_min_domain_expertise", "pass_min_domain_expertise"),
    ):
        if getattr(config, watch_name) > getattr(config, pass_name):
            raise ValueError(f"{watch_name} must not exceed {pass_name}")


def _validate_row(row: ResearchTeamResolutionReviewCapacityRow) -> None:
    expected_status = _status_for_reason_codes(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("row status does not match reason codes")


def _validate_report(report: ResearchTeamResolutionReviewCapacityReport) -> None:
    if report.review_scope_count != _decimal(len(report.rows)):
        raise ValueError("review_scope_count does not match rows")
    if report.pass_count != _decimal(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count does not match rows")
    if report.watch_count != _decimal(sum(1 for row in report.rows if row.status == "watch")):
        raise ValueError("watch_count does not match rows")
    if report.block_count != _decimal(sum(1 for row in report.rows if row.status == "block")):
        raise ValueError("block_count does not match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("report status does not match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("report reason_codes do not match rows")
    if report.average_capacity_score != _average_decimal(row.capacity_score for row in report.rows):
        raise ValueError("average_capacity_score does not match rows")


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


def _unsigned_payload(report: ResearchTeamResolutionReviewCapacityReport) -> dict[str, Any]:
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


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    number = _require_decimal(field_name, value)
    if number < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
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


def _ratio(value: Decimal) -> Decimal:
    return _decimal(value)


def _decimal(value: int | Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(DECIMAL_QUANTUM)


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
