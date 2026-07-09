"""Readonly report for research team specialist memory authority floors."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, DecimalException, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_AUTHORITY_FLOOR_REPORT_CONFIG_VERSION = (
    "research-team-specialist-memory-authority-floor-report"
)
DECIMAL_CONTEXT = Context(prec=64)
COUNT_QUANTUM = Decimal("1")
SCORE_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ZERO_SCORE = Decimal("0").quantize(SCORE_QUANTUM)
ONE_SCORE = Decimal("1").quantize(SCORE_QUANTUM)
STATUSES = ("pass", "watch", "block")
ROW_STATUS_SORT_ORDER = ("block", "watch", "pass")
ROW_REASON_CODES = (
    "authority_floor_block",
    "authority_floor_watch",
    "authority_floor_pass",
)
REPORT_REASON_CODES = (
    "no_memory_authority_rows_supplied",
    "authority_floor_block_present",
    "authority_floor_watch_present",
    "authority_floor_pass_present",
)
UNSAFE_PUBLIC_KEY_FRAGMENTS = (
    "candidate",
    "market",
    "source",
    "url",
    "dsn",
    "table",
    "token",
    "raw",
    "text",
    "wallet",
    "order",
)
UNSAFE_PUBLIC_VALUE_TERMS = (
    "candidate",
    "market",
    "source",
    "url",
    "dsn",
    "table",
    "token",
    "raw",
    "wallet",
    "private",
    "secret",
    "database",
    "db",
    "buy",
    "sell",
    "trade",
    "live",
    "sizing",
    "size it",
    "recommend",
)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryAuthorityFloorReportConfig:
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_AUTHORITY_FLOOR_REPORT_CONFIG_VERSION
    )
    min_pass_floor: Decimal = Decimal("0.700000")
    min_watch_floor: Decimal = Decimal("0.450000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_identifier("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_pass_floor",
            _normalize_score("min_pass_floor", self.min_pass_floor),
        )
        object.__setattr__(
            self,
            "min_watch_floor",
            _normalize_score("min_watch_floor", self.min_watch_floor),
        )
        if self.min_watch_floor > self.min_pass_floor:
            raise ValueError("min_watch_floor must not exceed min_pass_floor")
        _reject_unsafe_public_payload("memory authority floor config", self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryAuthorityFloorReportObservation:
    team_id: str
    specialist_id: str
    category_id: str
    memory_digest: str
    authority_score: Decimal
    evidence_quality_score: Decimal
    calibration_score: Decimal
    recency_score: Decimal
    independence_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_identifier("team_id", self.team_id)
        _require_public_identifier("specialist_id", self.specialist_id)
        _require_public_identifier("category_id", self.category_id)
        _require_digest_string("memory_digest", self.memory_digest)
        for field_name in (
            "authority_score",
            "evidence_quality_score",
            "calibration_score",
            "recency_score",
            "independence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        _reject_unsafe_public_payload("memory authority floor observation", self)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryAuthorityFloorReportRow:
    team_id: str
    specialist_id: str
    category_id: str
    memory_digest: str
    row_status: str
    authority_floor_score: Decimal
    floor_gap_to_pass: Decimal
    authority_score: Decimal
    evidence_quality_score: Decimal
    calibration_score: Decimal
    recency_score: Decimal
    independence_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_identifier("team_id", self.team_id)
        _require_public_identifier("specialist_id", self.specialist_id)
        _require_public_identifier("category_id", self.category_id)
        _require_digest_string("memory_digest", self.memory_digest)
        _require_member("row_status", self.row_status, STATUSES)
        for field_name in (
            "authority_floor_score",
            "floor_gap_to_pass",
            "authority_score",
            "evidence_quality_score",
            "calibration_score",
            "recency_score",
            "independence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _reject_unsafe_public_payload("memory authority floor row", self)
        _require_hard_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchTeamSpecialistMemoryAuthorityFloorReport:
    generated_at: datetime
    config_version: str
    report_status: str
    item_count: Decimal
    team_count: Decimal
    specialist_count: Decimal
    category_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_authority_floor_score: Decimal
    minimum_authority_floor_score: Decimal
    rows: tuple[ResearchTeamSpecialistMemoryAuthorityFloorReportRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        _require_member("report_status", self.report_status, STATUSES)
        for field_name in (
            "item_count",
            "team_count",
            "specialist_count",
            "category_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_authority_floor_score",
            "minimum_authority_floor_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_score(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_report_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _reject_unsafe_public_payload("memory authority floor report", self)
        _require_hard_flags("report", self)
        _validate_report(self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest:
            _require_digest_string(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report contents")
        object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_team_specialist_memory_authority_floor_report(
    rows: list[ResearchTeamSpecialistMemoryAuthorityFloorReportObservation]
    | tuple[ResearchTeamSpecialistMemoryAuthorityFloorReportObservation, ...],
    *,
    config: ResearchTeamSpecialistMemoryAuthorityFloorReportConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistMemoryAuthorityFloorReport:
    if type(config) is not ResearchTeamSpecialistMemoryAuthorityFloorReportConfig:
        raise ValueError(
            "config must be a ResearchTeamSpecialistMemoryAuthorityFloorReportConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    observations = _normalize_observations(rows)
    report_rows = tuple(
        sorted(
            (
                _row_for_observation(observation, config=config)
                for observation in observations
            ),
            key=_row_sort_key,
        ),
    )
    pass_count = _status_count(report_rows, "pass")
    watch_count = _status_count(report_rows, "watch")
    block_count = _status_count(report_rows, "block")

    return ResearchTeamSpecialistMemoryAuthorityFloorReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=_report_status(block_count, watch_count),
        item_count=_count(len(report_rows)),
        team_count=_count(len({row.team_id for row in report_rows})),
        specialist_count=_count(len({row.specialist_id for row in report_rows})),
        category_count=_count(len({row.category_id for row in report_rows})),
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        average_authority_floor_score=_average_score(
            tuple(row.authority_floor_score for row in report_rows),
        ),
        minimum_authority_floor_score=_minimum_score(
            tuple(row.authority_floor_score for row in report_rows),
        ),
        rows=report_rows,
        reason_codes=_report_reason_codes(report_rows, len(observations)),
    )


def research_team_specialist_memory_authority_floor_report_payload(
    report: ResearchTeamSpecialistMemoryAuthorityFloorReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamSpecialistMemoryAuthorityFloorReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("memory authority floor report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("memory authority floor payload", report)
        _require_hard_flags("payload", _DictFlags(report))
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _require_hard_flags("payload", _DictFlags(payload))
        _validate_payload_digest(payload)
        payload = _validated_payload(payload)
    else:
        raise ValueError(
            "report must be a ResearchTeamSpecialistMemoryAuthorityFloorReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("memory authority floor payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_payload_digest(payload)
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


def _validated_payload(payload: dict[str, Any]) -> dict[str, Any]:
    validated_report = _report_from_payload(payload)
    validated_payload = _json_ready(validated_report)
    if type(validated_payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    if validated_payload != payload:
        raise ValueError("report payload must be canonical")
    return validated_payload


def _report_from_payload(
    payload: dict[str, Any],
) -> ResearchTeamSpecialistMemoryAuthorityFloorReport:
    _require_exact_payload_fields(
        "report payload",
        payload,
        ResearchTeamSpecialistMemoryAuthorityFloorReport,
    )
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must be a JSON array")
    rows = tuple(
        _row_from_payload(row, index=index) for index, row in enumerate(rows_value)
    )
    return ResearchTeamSpecialistMemoryAuthorityFloorReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=payload["config_version"],
        report_status=payload["report_status"],
        item_count=_payload_decimal("item_count", payload["item_count"]),
        team_count=_payload_decimal("team_count", payload["team_count"]),
        specialist_count=_payload_decimal(
            "specialist_count",
            payload["specialist_count"],
        ),
        category_count=_payload_decimal("category_count", payload["category_count"]),
        pass_count=_payload_decimal("pass_count", payload["pass_count"]),
        watch_count=_payload_decimal("watch_count", payload["watch_count"]),
        block_count=_payload_decimal("block_count", payload["block_count"]),
        average_authority_floor_score=_payload_decimal(
            "average_authority_floor_score",
            payload["average_authority_floor_score"],
        ),
        minimum_authority_floor_score=_payload_decimal(
            "minimum_authority_floor_score",
            payload["minimum_authority_floor_score"],
        ),
        rows=rows,
        reason_codes=_payload_string_tuple("reason_codes", payload["reason_codes"]),
        derived_validation_digest=payload["derived_validation_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _row_from_payload(
    value: object,
    *,
    index: int,
) -> ResearchTeamSpecialistMemoryAuthorityFloorReportRow:
    if type(value) is not dict:
        raise ValueError(f"rows[{index}] must be a JSON object")
    _require_exact_payload_fields(
        f"rows[{index}]",
        value,
        ResearchTeamSpecialistMemoryAuthorityFloorReportRow,
    )
    return ResearchTeamSpecialistMemoryAuthorityFloorReportRow(
        team_id=value["team_id"],
        specialist_id=value["specialist_id"],
        category_id=value["category_id"],
        memory_digest=value["memory_digest"],
        row_status=value["row_status"],
        authority_floor_score=_payload_decimal(
            f"rows[{index}].authority_floor_score",
            value["authority_floor_score"],
        ),
        floor_gap_to_pass=_payload_decimal(
            f"rows[{index}].floor_gap_to_pass",
            value["floor_gap_to_pass"],
        ),
        authority_score=_payload_decimal(
            f"rows[{index}].authority_score",
            value["authority_score"],
        ),
        evidence_quality_score=_payload_decimal(
            f"rows[{index}].evidence_quality_score",
            value["evidence_quality_score"],
        ),
        calibration_score=_payload_decimal(
            f"rows[{index}].calibration_score",
            value["calibration_score"],
        ),
        recency_score=_payload_decimal(
            f"rows[{index}].recency_score",
            value["recency_score"],
        ),
        independence_score=_payload_decimal(
            f"rows[{index}].independence_score",
            value["independence_score"],
        ),
        reason_codes=_payload_string_tuple(
            f"rows[{index}].reason_codes",
            value["reason_codes"],
        ),
        paper_only=value["paper_only"],
        report_only=value["report_only"],
        readonly=value["readonly"],
    )


def _require_exact_payload_fields(
    label: str,
    value: dict[str, Any],
    dataclass_type: type[object],
) -> None:
    expected = {field.name for field in fields(dataclass_type)}
    if set(value) != expected:
        raise ValueError(f"{label} must contain exactly the report fields")


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal = Decimal(value)
    except DecimalException as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not decimal.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO-8601 datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 datetime string") from exc
    return _as_utc(field_name, parsed)


def _payload_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON array")
    return tuple(value)


def _normalize_observations(
    value: object,
) -> tuple[ResearchTeamSpecialistMemoryAuthorityFloorReportObservation, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_digests: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamSpecialistMemoryAuthorityFloorReportObservation:
            raise ValueError(
                "rows must contain ResearchTeamSpecialistMemoryAuthorityFloorReportObservation values",
            )
        _require_hard_flags("observation", row)
        if row.memory_digest in seen_digests:
            raise ValueError("duplicate memory_digest values are not allowed")
        seen_digests.add(row.memory_digest)
    return rows


def _row_for_observation(
    row: ResearchTeamSpecialistMemoryAuthorityFloorReportObservation,
    *,
    config: ResearchTeamSpecialistMemoryAuthorityFloorReportConfig,
) -> ResearchTeamSpecialistMemoryAuthorityFloorReportRow:
    floor_score = min(
        (
            row.authority_score,
            row.evidence_quality_score,
            row.calibration_score,
            row.recency_score,
            row.independence_score,
        ),
    )
    return ResearchTeamSpecialistMemoryAuthorityFloorReportRow(
        team_id=row.team_id,
        specialist_id=row.specialist_id,
        category_id=row.category_id,
        memory_digest=row.memory_digest,
        row_status=_row_status(floor_score, config),
        authority_floor_score=floor_score,
        floor_gap_to_pass=_floor_gap_to_pass(floor_score, config),
        authority_score=row.authority_score,
        evidence_quality_score=row.evidence_quality_score,
        calibration_score=row.calibration_score,
        recency_score=row.recency_score,
        independence_score=row.independence_score,
        reason_codes=_row_reason_codes(floor_score, config),
    )


def _row_status(
    authority_floor_score: Decimal,
    config: ResearchTeamSpecialistMemoryAuthorityFloorReportConfig,
) -> str:
    if authority_floor_score >= config.min_pass_floor:
        return "pass"
    if authority_floor_score >= config.min_watch_floor:
        return "watch"
    return "block"


def _floor_gap_to_pass(
    authority_floor_score: Decimal,
    config: ResearchTeamSpecialistMemoryAuthorityFloorReportConfig,
) -> Decimal:
    if authority_floor_score >= config.min_pass_floor:
        return ZERO_SCORE
    with localcontext(DECIMAL_CONTEXT):
        return (config.min_pass_floor - authority_floor_score).quantize(SCORE_QUANTUM)


def _row_reason_codes(
    authority_floor_score: Decimal,
    config: ResearchTeamSpecialistMemoryAuthorityFloorReportConfig,
) -> tuple[str, ...]:
    row_status = _row_status(authority_floor_score, config)
    if row_status == "block":
        return ("authority_floor_block",)
    if row_status == "watch":
        return ("authority_floor_watch",)
    return ("authority_floor_pass",)


def _row_sort_key(
    row: ResearchTeamSpecialistMemoryAuthorityFloorReportRow,
) -> tuple[int, Decimal, str, str, str, str]:
    return (
        ROW_STATUS_SORT_ORDER.index(row.row_status),
        row.authority_floor_score,
        row.team_id,
        row.category_id,
        row.specialist_id,
        row.memory_digest,
    )


def _report_status(block_count: Decimal, watch_count: Decimal) -> str:
    if block_count > ZERO_COUNT:
        return "block"
    if watch_count > ZERO_COUNT:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamSpecialistMemoryAuthorityFloorReportRow, ...],
    input_count: int,
) -> tuple[str, ...]:
    if input_count == 0:
        return ("no_memory_authority_rows_supplied",)
    codes: list[str] = []
    if any(row.row_status == "block" for row in rows):
        codes.append("authority_floor_block_present")
    if any(row.row_status == "watch" for row in rows):
        codes.append("authority_floor_watch_present")
    if any(row.row_status == "pass" for row in rows):
        codes.append("authority_floor_pass_present")
    return tuple(code for code in REPORT_REASON_CODES if code in codes)


def _status_count(
    rows: tuple[ResearchTeamSpecialistMemoryAuthorityFloorReportRow, ...],
    row_status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.row_status == row_status))


def _normalize_report_rows(
    value: object,
) -> tuple[ResearchTeamSpecialistMemoryAuthorityFloorReportRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_digests: set[str] = set()
    for row in rows:
        if type(row) is not ResearchTeamSpecialistMemoryAuthorityFloorReportRow:
            raise ValueError(
                "rows must contain ResearchTeamSpecialistMemoryAuthorityFloorReportRow values",
            )
        _require_hard_flags("row", row)
        if row.memory_digest in seen_digests:
            raise ValueError("duplicate memory_digest values are not allowed")
        seen_digests.add(row.memory_digest)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return rows


def _normalize_row_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    codes = tuple(value)
    for code in codes:
        _require_member("reason_codes", code, ROW_REASON_CODES)
    if not codes:
        raise ValueError("reason_codes must not be empty")
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in ROW_REASON_CODES if code in codes) != codes:
        raise ValueError("reason_codes must be deterministic")
    return codes


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    codes = tuple(value)
    for code in codes:
        _require_member("reason_codes", code, REPORT_REASON_CODES)
    if len(set(codes)) != len(codes):
        raise ValueError("reason_codes must be unique")
    if tuple(code for code in REPORT_REASON_CODES if code in codes) != codes:
        raise ValueError("reason_codes must be deterministic")
    return codes


def _validate_row(row: ResearchTeamSpecialistMemoryAuthorityFloorReportRow) -> None:
    expected_floor_score = min(
        (
            row.authority_score,
            row.evidence_quality_score,
            row.calibration_score,
            row.recency_score,
            row.independence_score,
        ),
    )
    if row.authority_floor_score != expected_floor_score:
        raise ValueError("authority_floor_score must match row dimension floor")
    if row.floor_gap_to_pass < ZERO_SCORE:
        raise ValueError("floor_gap_to_pass must be nonnegative")
    if row.row_status == "pass" and row.floor_gap_to_pass != ZERO_SCORE:
        raise ValueError("pass rows must not have a floor gap")
    if row.reason_codes != _row_reason_codes_for_status(row.row_status):
        raise ValueError("reason_codes must match row_status")


def _row_reason_codes_for_status(row_status: str) -> tuple[str, ...]:
    if row_status == "block":
        return ("authority_floor_block",)
    if row_status == "watch":
        return ("authority_floor_watch",)
    return ("authority_floor_pass",)


def _validate_report(report: ResearchTeamSpecialistMemoryAuthorityFloorReport) -> None:
    if report.item_count != _count(len(report.rows)):
        raise ValueError("item_count must match rows")
    if report.team_count != _count(len({row.team_id for row in report.rows})):
        raise ValueError("team_count must match rows")
    if report.specialist_count != _count(len({row.specialist_id for row in report.rows})):
        raise ValueError("specialist_count must match rows")
    if report.category_count != _count(len({row.category_id for row in report.rows})):
        raise ValueError("category_count must match rows")
    expected_counts = {
        "pass_count": _status_count(report.rows, "pass"),
        "watch_count": _status_count(report.rows, "watch"),
        "block_count": _status_count(report.rows, "block"),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    values = tuple(row.authority_floor_score for row in report.rows)
    if report.average_authority_floor_score != _average_score(values):
        raise ValueError("average_authority_floor_score must match rows")
    if report.minimum_authority_floor_score != _minimum_score(values):
        raise ValueError("minimum_authority_floor_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, int(report.item_count)):
        raise ValueError("reason_codes must match rows")
    if report.report_status != _report_status(report.block_count, report.watch_count):
        raise ValueError("report_status must match rows")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be present")
    _require_digest_string("derived_validation_digest", digest)
    expected = _digest_for_json_payload(payload)
    if digest != expected:
        raise ValueError("derived_validation_digest must match report contents")


def _report_digest(report: ResearchTeamSpecialistMemoryAuthorityFloorReport) -> str:
    payload = {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "derived_validation_digest"
    }
    return _digest_for_json_payload(_json_ready(payload))


def _digest_for_json_payload(payload: dict[str, Any]) -> str:
    payload_without_digest = {
        key: value for key, value in payload.items() if key != "derived_validation_digest"
    }
    canonical_payload = json.dumps(
        payload_without_digest,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical_payload.encode("utf-8")).hexdigest()


def _average_score(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_SCORE
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO_SCORE) / _count(len(values))).quantize(SCORE_QUANTUM)


def _minimum_score(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_SCORE
    with localcontext(DECIMAL_CONTEXT):
        return min(values).quantize(SCORE_QUANTUM)


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_score(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    if decimal < ZERO_SCORE:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal > ONE_SCORE:
        raise ValueError(f"{field_name} must be at most 1")
    with localcontext(DECIMAL_CONTEXT):
        normalized = decimal.quantize(SCORE_QUANTUM)
    if normalized == ZERO_SCORE:
        return ZERO_SCORE
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    if decimal < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal != decimal.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    with localcontext(DECIMAL_CONTEXT):
        normalized = decimal.quantize(COUNT_QUANTUM)
    if normalized == ZERO_COUNT:
        return ZERO_COUNT
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


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be canonical")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single line")
    if _has_unsafe_public_value(value):
        raise ValueError(f"unsafe public value in {field_name}")


def _require_public_identifier(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if not value.isascii() or any(
        not (character.isalnum() or character in "._-") for character in value
    ):
        raise ValueError(f"{field_name} must be a canonical public identifier")


def _require_digest_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    _require_public_string(field_name, value)
    if value not in members:
        raise ValueError(f"{field_name} must be one of {', '.join(members)}")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        digest_field_name = _digest_field_name(path)
        if digest_field_name is not None:
            if digest_field_name == "derived_validation_digest" and value == "":
                return
            _require_digest_string(digest_field_name, value)
            return
        if _has_unsafe_public_value(value):
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_key(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _digest_field_name(path: str) -> str | None:
    field_name = path.rsplit(".", maxsplit=1)[-1]
    if field_name in {"memory_digest", "derived_validation_digest"}:
        return field_name
    return None


def _has_unsafe_public_key(value: str) -> bool:
    normalized = value.lower()
    return any(term in normalized for term in UNSAFE_PUBLIC_KEY_FRAGMENTS)


def _has_unsafe_public_value(value: str) -> bool:
    normalized = value.lower()
    return any(term in normalized for term in UNSAFE_PUBLIC_VALUE_TERMS)


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric values must use Decimal strings")
    if type(value) in (str, bool):
        return value
    if isinstance(value, dict):
        return _json_dict(value)
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _json_dict(value: dict[Any, Any]) -> dict[str, Any]:
    ready: dict[str, Any] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        ready[key] = _json_ready(item)
    return ready


__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_MEMORY_AUTHORITY_FLOOR_REPORT_CONFIG_VERSION",
    "ResearchTeamSpecialistMemoryAuthorityFloorReport",
    "ResearchTeamSpecialistMemoryAuthorityFloorReportConfig",
    "ResearchTeamSpecialistMemoryAuthorityFloorReportObservation",
    "ResearchTeamSpecialistMemoryAuthorityFloorReportRow",
    "build_research_team_specialist_memory_authority_floor_report",
    "research_team_specialist_memory_authority_floor_report_payload",
)
