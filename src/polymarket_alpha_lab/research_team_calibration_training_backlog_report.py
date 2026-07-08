"""Public-safe calibration training backlog report for specialist teams."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_RESEARCH_TEAM_CALIBRATION_TRAINING_BACKLOG_CONFIG_VERSION = (
    "research-team-calibration-training-backlog-v0"
)

STATUSES = ("pass", "watch", "block")
PASS_REASON_CODE = "training_backlog_clear"
BLOCK_REASON_CODES = (
    "calibration_drift_block",
    "sample_count_block",
    "evidence_miss_rate_block",
    "stale_memory_block",
    "review_capacity_block",
)
WATCH_REASON_CODES = (
    "calibration_drift_watch",
    "sample_count_watch",
    "evidence_miss_rate_watch",
    "stale_memory_watch",
    "review_capacity_watch",
)
REPORT_REASON_CODES = BLOCK_REASON_CODES + WATCH_REASON_CODES + (PASS_REASON_CODE,)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
WATCH_PRIORITY_SCORE = Decimal("0.500000")
BLOCK_PRIORITY_SCORE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "event",
        "market",
        "source",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "database",
        "network",
        "broker",
        "execution",
        "recom" + "mendation",
        "siz" + "ing",
    ),
)


@dataclass(frozen=True)
class ResearchTeamCalibrationTrainingBacklogConfig:
    config_version: str = DEFAULT_RESEARCH_TEAM_CALIBRATION_TRAINING_BACKLOG_CONFIG_VERSION
    watch_calibration_drift: Decimal = Decimal("0.050000")
    block_calibration_drift: Decimal = Decimal("0.120000")
    watch_min_sample_count: Decimal = Decimal("30")
    block_min_sample_count: Decimal = Decimal("10")
    watch_evidence_miss_rate: Decimal = Decimal("0.100000")
    block_evidence_miss_rate: Decimal = Decimal("0.250000")
    watch_stale_memory_hours: Decimal = Decimal("48.000000")
    block_stale_memory_hours: Decimal = Decimal("168.000000")
    watch_min_review_capacity_hours: Decimal = Decimal("6.000000")
    block_min_review_capacity_hours: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_calibration_drift",
            "block_calibration_drift",
            "watch_evidence_miss_rate",
            "block_evidence_miss_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_min_sample_count", "block_min_sample_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_stale_memory_hours",
            "block_stale_memory_hours",
            "watch_min_review_capacity_hours",
            "block_min_review_capacity_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamCalibrationTrainingBacklogInput:
    team_key: str
    aggregate_calibration_drift: Decimal
    sample_count: Decimal
    evidence_miss_rate: Decimal
    stale_memory_hours: Decimal
    review_capacity_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_safe_team_key("team_key", self.team_key)
        object.__setattr__(
            self,
            "aggregate_calibration_drift",
            _normalize_signed_ratio(
                "aggregate_calibration_drift",
                self.aggregate_calibration_drift,
            ),
        )
        object.__setattr__(
            self,
            "sample_count",
            _normalize_nonnegative_count("sample_count", self.sample_count),
        )
        object.__setattr__(
            self,
            "evidence_miss_rate",
            _normalize_nonnegative_ratio("evidence_miss_rate", self.evidence_miss_rate),
        )
        object.__setattr__(
            self,
            "stale_memory_hours",
            _normalize_nonnegative_value("stale_memory_hours", self.stale_memory_hours),
        )
        object.__setattr__(
            self,
            "review_capacity_hours",
            _normalize_nonnegative_value(
                "review_capacity_hours",
                self.review_capacity_hours,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamCalibrationTrainingBacklogItem:
    team_key: str
    status: str
    reason_codes: tuple[str, ...]
    priority_score: Decimal
    aggregate_calibration_drift: Decimal
    sample_count: Decimal
    evidence_miss_rate: Decimal
    stale_memory_hours: Decimal
    review_capacity_hours: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_safe_team_key("team_key", self.team_key)
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "priority_score",
            _normalize_nonnegative_ratio("priority_score", self.priority_score),
        )
        object.__setattr__(
            self,
            "aggregate_calibration_drift",
            _normalize_signed_ratio(
                "aggregate_calibration_drift",
                self.aggregate_calibration_drift,
            ),
        )
        object.__setattr__(
            self,
            "sample_count",
            _normalize_nonnegative_count("sample_count", self.sample_count),
        )
        object.__setattr__(
            self,
            "evidence_miss_rate",
            _normalize_nonnegative_ratio("evidence_miss_rate", self.evidence_miss_rate),
        )
        object.__setattr__(
            self,
            "stale_memory_hours",
            _normalize_nonnegative_value("stale_memory_hours", self.stale_memory_hours),
        )
        object.__setattr__(
            self,
            "review_capacity_hours",
            _normalize_nonnegative_value(
                "review_capacity_hours",
                self.review_capacity_hours,
            ),
        )
        _validate_backlog_item(self)
        _require_hard_flags("backlog item", self)


@dataclass(frozen=True)
class ResearchTeamCalibrationTrainingBacklogReport:
    generated_at: datetime
    config_version: str
    team_count: Decimal
    backlog_item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    backlog_items: tuple[ResearchTeamCalibrationTrainingBacklogItem, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "team_count",
            "backlog_item_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "backlog_items",
            _normalize_backlog_items(self.backlog_items),
        )
        object.__setattr__(
            self,
            "derived_validation_digest",
            (
                _report_derived_validation_digest(self)
                if self.derived_validation_digest == ""
                else _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                )
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_research_team_calibration_training_backlog_report(
    inputs: list[ResearchTeamCalibrationTrainingBacklogInput]
    | tuple[ResearchTeamCalibrationTrainingBacklogInput, ...],
    *,
    config: ResearchTeamCalibrationTrainingBacklogConfig,
    generated_at: datetime,
) -> ResearchTeamCalibrationTrainingBacklogReport:
    if type(config) is not ResearchTeamCalibrationTrainingBacklogConfig:
        raise ValueError(
            "config must be a ResearchTeamCalibrationTrainingBacklogConfig",
        )
    _require_hard_flags("config", config)
    rows = _normalize_inputs(inputs)
    generated_at_utc = _as_utc("generated_at", generated_at)
    row_statuses = tuple((row, _row_status(row, config)) for row in rows)
    backlog_items = tuple(
        sorted(
            (
                _backlog_item(row, config, status)
                for row, status in row_statuses
                if status != "pass"
            ),
            key=_backlog_item_sort_key,
        ),
    )
    return ResearchTeamCalibrationTrainingBacklogReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        team_count=_count(len(rows)),
        backlog_item_count=_count(len(backlog_items)),
        pass_count=_count(sum(1 for _, status in row_statuses if status == "pass")),
        watch_count=_count(sum(1 for _, status in row_statuses if status == "watch")),
        block_count=_count(sum(1 for _, status in row_statuses if status == "block")),
        status=_report_status(backlog_items),
        reason_codes=_report_reason_codes(backlog_items),
        backlog_items=backlog_items,
    )


def research_team_calibration_training_backlog_report_payload(
    report: ResearchTeamCalibrationTrainingBacklogReport,
) -> dict[str, Any]:
    if type(report) is not ResearchTeamCalibrationTrainingBacklogReport:
        raise ValueError(
            "report must be a ResearchTeamCalibrationTrainingBacklogReport",
        )
    _require_hard_flags("report", report)
    _validate_report(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_team_calibration_training_backlog_public_payload(payload)
    return payload


def validate_research_team_calibration_training_backlog_public_payload(
    payload: object,
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _require_hard_flags("payload", _PayloadFlags(payload))
    _require_safe_public_payload("training backlog public payload", payload)


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


def _backlog_item(
    row: ResearchTeamCalibrationTrainingBacklogInput,
    config: ResearchTeamCalibrationTrainingBacklogConfig,
    status: str,
) -> ResearchTeamCalibrationTrainingBacklogItem:
    return ResearchTeamCalibrationTrainingBacklogItem(
        team_key=row.team_key,
        status=status,
        reason_codes=_row_reason_codes_from_config(row, config),
        priority_score=BLOCK_PRIORITY_SCORE if status == "block" else WATCH_PRIORITY_SCORE,
        aggregate_calibration_drift=row.aggregate_calibration_drift,
        sample_count=row.sample_count,
        evidence_miss_rate=row.evidence_miss_rate,
        stale_memory_hours=row.stale_memory_hours,
        review_capacity_hours=row.review_capacity_hours,
    )


def _row_status(
    row: ResearchTeamCalibrationTrainingBacklogInput,
    config: ResearchTeamCalibrationTrainingBacklogConfig,
) -> str:
    reason_codes = _row_reason_codes_from_config(row, config)
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _row_reason_codes_from_config(
    row: ResearchTeamCalibrationTrainingBacklogInput,
    config: ResearchTeamCalibrationTrainingBacklogConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    abs_drift = _abs_decimal(row.aggregate_calibration_drift)
    if abs_drift >= config.block_calibration_drift:
        codes.append("calibration_drift_block")
    elif abs_drift >= config.watch_calibration_drift:
        codes.append("calibration_drift_watch")

    if row.sample_count < config.block_min_sample_count:
        codes.append("sample_count_block")
    elif row.sample_count < config.watch_min_sample_count:
        codes.append("sample_count_watch")

    if row.evidence_miss_rate >= config.block_evidence_miss_rate:
        codes.append("evidence_miss_rate_block")
    elif row.evidence_miss_rate >= config.watch_evidence_miss_rate:
        codes.append("evidence_miss_rate_watch")

    if row.stale_memory_hours >= config.block_stale_memory_hours:
        codes.append("stale_memory_block")
    elif row.stale_memory_hours >= config.watch_stale_memory_hours:
        codes.append("stale_memory_watch")

    if row.review_capacity_hours < config.block_min_review_capacity_hours:
        codes.append("review_capacity_block")
    elif row.review_capacity_hours < config.watch_min_review_capacity_hours:
        codes.append("review_capacity_watch")

    return tuple(codes)


def _row_reason_codes(
    row: ResearchTeamCalibrationTrainingBacklogInput,
    status: str,
) -> tuple[str, ...]:
    codes: list[str] = []
    abs_drift = _abs_decimal(row.aggregate_calibration_drift)
    if status == "block":
        if abs_drift >= Decimal("0.120000"):
            codes.append("calibration_drift_block")
        if row.sample_count < Decimal("10"):
            codes.append("sample_count_block")
        if row.evidence_miss_rate >= Decimal("0.250000"):
            codes.append("evidence_miss_rate_block")
        if row.stale_memory_hours >= Decimal("168.000000"):
            codes.append("stale_memory_block")
        if row.review_capacity_hours < Decimal("2.000000"):
            codes.append("review_capacity_block")
    elif status == "watch":
        if abs_drift >= Decimal("0.050000"):
            codes.append("calibration_drift_watch")
        if row.sample_count < Decimal("30"):
            codes.append("sample_count_watch")
        if row.evidence_miss_rate >= Decimal("0.100000"):
            codes.append("evidence_miss_rate_watch")
        if row.stale_memory_hours >= Decimal("48.000000"):
            codes.append("stale_memory_watch")
        if row.review_capacity_hours < Decimal("6.000000"):
            codes.append("review_capacity_watch")
    return tuple(codes)


def _report_status(
    items: tuple[ResearchTeamCalibrationTrainingBacklogItem, ...],
) -> str:
    if any(item.status == "block" for item in items):
        return "block"
    if any(item.status == "watch" for item in items):
        return "watch"
    return "pass"


def _report_reason_codes(
    items: tuple[ResearchTeamCalibrationTrainingBacklogItem, ...],
) -> tuple[str, ...]:
    if not items:
        return (PASS_REASON_CODE,)
    item_reason_codes = {reason_code for item in items for reason_code in item.reason_codes}
    return tuple(
        reason_code
        for reason_code in BLOCK_REASON_CODES + WATCH_REASON_CODES
        if reason_code in item_reason_codes
    )


def _backlog_item_sort_key(
    item: ResearchTeamCalibrationTrainingBacklogItem,
) -> tuple[int, Decimal, str]:
    status_rank = {"block": 0, "watch": 1, "pass": 2}
    return (status_rank[item.status], -item.priority_score, item.team_key)


def _normalize_inputs(
    inputs: list[ResearchTeamCalibrationTrainingBacklogInput]
    | tuple[ResearchTeamCalibrationTrainingBacklogInput, ...],
) -> tuple[ResearchTeamCalibrationTrainingBacklogInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamCalibrationTrainingBacklogInput:
            raise ValueError(
                "inputs must contain ResearchTeamCalibrationTrainingBacklogInput values",
            )
        _require_hard_flags("input", row)
        if row.team_key in seen:
            raise ValueError("inputs must contain unique team_key values")
        seen.add(row.team_key)
    return rows


def _normalize_backlog_items(
    value: object,
) -> tuple[ResearchTeamCalibrationTrainingBacklogItem, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("backlog_items must be a tuple")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("backlog_items must be a tuple") from exc
    for item in items:
        if type(item) is not ResearchTeamCalibrationTrainingBacklogItem:
            raise ValueError(
                "backlog_items must contain ResearchTeamCalibrationTrainingBacklogItem values",
            )
        _require_hard_flags("backlog item", item)
    return items


def _validate_config(config: ResearchTeamCalibrationTrainingBacklogConfig) -> None:
    if config.block_calibration_drift < config.watch_calibration_drift:
        raise ValueError("block_calibration_drift must be at least watch_calibration_drift")
    if config.block_min_sample_count > config.watch_min_sample_count:
        raise ValueError("block_min_sample_count must not exceed watch_min_sample_count")
    if config.block_evidence_miss_rate < config.watch_evidence_miss_rate:
        raise ValueError("block_evidence_miss_rate must be at least watch_evidence_miss_rate")
    if config.block_stale_memory_hours < config.watch_stale_memory_hours:
        raise ValueError("block_stale_memory_hours must be at least watch_stale_memory_hours")
    if config.block_min_review_capacity_hours > config.watch_min_review_capacity_hours:
        raise ValueError(
            "block_min_review_capacity_hours must not exceed "
            "watch_min_review_capacity_hours",
        )


def _validate_backlog_item(
    item: ResearchTeamCalibrationTrainingBacklogItem,
) -> None:
    if item.status == "pass":
        raise ValueError("backlog item status must be watch or block")
    if item.status == "block" and not any(
        reason_code in BLOCK_REASON_CODES for reason_code in item.reason_codes
    ):
        raise ValueError("block backlog items require block reason_codes")
    if item.status == "watch" and not item.reason_codes:
        raise ValueError("watch backlog items require reason_codes")
    if item.status == "watch" and any(
        reason_code in BLOCK_REASON_CODES for reason_code in item.reason_codes
    ):
        raise ValueError("watch backlog items must not contain block reason_codes")
    expected_priority = (
        BLOCK_PRIORITY_SCORE if item.status == "block" else WATCH_PRIORITY_SCORE
    )
    if item.priority_score != expected_priority:
        raise ValueError("priority_score must match status")


def _validate_report(report: ResearchTeamCalibrationTrainingBacklogReport) -> None:
    if report.backlog_item_count != _count(len(report.backlog_items)):
        raise ValueError("backlog_item_count must match backlog_items")
    if report.block_count != _count(
        sum(1 for item in report.backlog_items if item.status == "block"),
    ):
        raise ValueError("block_count must match backlog_items")
    if report.watch_count != _count(
        sum(1 for item in report.backlog_items if item.status == "watch"),
    ):
        raise ValueError("watch_count must match backlog_items")
    if report.pass_count + report.watch_count + report.block_count != report.team_count:
        raise ValueError("team_count must match status counts")
    if report.status != _report_status(report.backlog_items):
        raise ValueError("status must match backlog_items")
    if report.reason_codes != _report_reason_codes(report.backlog_items):
        raise ValueError("reason_codes must match backlog_items")
    if report.backlog_items != tuple(
        sorted(report.backlog_items, key=_backlog_item_sort_key),
    ):
        raise ValueError("backlog_items must be deterministic")
    team_keys = tuple(item.team_key for item in report.backlog_items)
    if len(set(team_keys)) != len(team_keys):
        raise ValueError("backlog_items must contain unique team_key values")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match backlog_items")


def _report_derived_validation_digest(
    report: ResearchTeamCalibrationTrainingBacklogReport,
) -> str:
    values = [
        "research_team_calibration_training_backlog_report",
        f"generated_at={_as_utc('generated_at', report.generated_at).isoformat()}",
        f"config_version={report.config_version}",
        f"team_count={report.team_count}",
        f"backlog_item_count={report.backlog_item_count}",
        f"pass_count={report.pass_count}",
        f"watch_count={report.watch_count}",
        f"block_count={report.block_count}",
        f"status={report.status}",
        f"reason_codes={','.join(report.reason_codes)}",
        f"paper_only={report.paper_only}",
        f"report_only={report.report_only}",
        f"readonly={report.readonly}",
    ]
    for item in report.backlog_items:
        values.extend(
            (
                "backlog_item",
                f"team_key={item.team_key}",
                f"status={item.status}",
                f"reason_codes={','.join(item.reason_codes)}",
                f"priority_score={item.priority_score}",
                f"aggregate_calibration_drift={item.aggregate_calibration_drift}",
                f"sample_count={item.sample_count}",
                f"evidence_miss_rate={item.evidence_miss_rate}",
                f"stale_memory_hours={item.stale_memory_hours}",
                f"review_capacity_hours={item.review_capacity_hours}",
                f"paper_only={item.paper_only}",
                f"report_only={item.report_only}",
                f"readonly={item.readonly}",
            ),
        )
    return _sha256(tuple(values))


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, bool)):
        return value
    if isinstance(value, int):
        raise ValueError("JSON value must use Decimal-derived string values")
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


def _require_safe_public_payload(label: str, value: object, path: str = "") -> None:
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{item_path} has unsafe public key")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True for {label}")
            _require_safe_public_payload(label, item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _require_safe_public_payload(label, item, item_path)
        return
    if type(value) in (Decimal, int):
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if type(value) is float:
        raise ValueError(f"{path or label} must not be a float")
    raise ValueError(f"{path or label} contains unsupported value")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    tokens = tuple(
        part
        for part in "".join(char if char.isalnum() else "_" for char in lowered).split(
            "_",
        )
        if part
    )
    for fragment in UNSAFE_PUBLIC_FRAGMENTS:
        if "_" in fragment:
            if fragment in lowered:
                return True
            continue
        if fragment in tokens:
            return True
    return False


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    return reason_codes


def _normalize_signed_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_value(field_name, value)
    if normalized < -ONE_RATIO or normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return normalized


def _normalize_nonnegative_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_value(field_name, value)
    if normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _normalize_nonnegative_value(field_name: str, value: object) -> Decimal:
    normalized = _normalize_value(field_name, value)
    if normalized < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_value(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        quantized = value.quantize(RATIO_QUANTUM)
    if value != quantized:
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    return quantized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANTUM)
    if value != quantized:
        raise ValueError(f"{field_name} must be integral")
    if quantized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    normalized = value.strip()
    if normalized != value or len(normalized) != 64:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if normalized.lower() != normalized:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in normalized):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_safe_team_key(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _abs_decimal(value: Decimal) -> Decimal:
    if value < ZERO_RATIO:
        return -value
    return value


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _sha256(values: tuple[str, ...]) -> str:
    return hashlib.sha256("\n".join(values).encode("utf-8")).hexdigest()


__all__ = (
    "DEFAULT_RESEARCH_TEAM_CALIBRATION_TRAINING_BACKLOG_CONFIG_VERSION",
    "STATUSES",
    "ResearchTeamCalibrationTrainingBacklogConfig",
    "ResearchTeamCalibrationTrainingBacklogInput",
    "ResearchTeamCalibrationTrainingBacklogItem",
    "ResearchTeamCalibrationTrainingBacklogReport",
    "build_research_team_calibration_training_backlog_report",
    "research_team_calibration_training_backlog_report_payload",
    "validate_research_team_calibration_training_backlog_public_payload",
)
