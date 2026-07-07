"""Pure report-only candidate event triage matrix for manual research routing."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_CANDIDATE_TRIAGE_MATRIX_CONFIG_VERSION = (
    "research-event-triage-matrix-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_TRIAGE_STATUSES = frozenset(("pass", "watch", "block"))
_MANUAL_RESEARCH_BUCKETS = frozenset(("ready_queue", "priority_review", "hold_rework"))
_BLOCK_REASON_CODES = frozenset(
    (
        "research_readiness_block",
        "cost_threshold_block",
        "evidence_package_block",
        "team_capacity_block",
    ),
)
_REASON_CODE_SEQUENCE = (
    "empty_input",
    "research_readiness_block",
    "cost_threshold_block",
    "evidence_package_block",
    "team_capacity_block",
    "research_readiness_watch",
    "cost_threshold_watch",
    "evidence_package_watch",
    "team_capacity_watch",
    "triage_matrix_pass",
)
_BUCKET_BY_STATUS = {
    "pass": "ready_queue",
    "watch": "priority_review",
    "block": "hold_rework",
}
_DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
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
class ResearchCandidateTriageMatrixConfig:
    config_version: str = DEFAULT_RESEARCH_CANDIDATE_TRIAGE_MATRIX_CONFIG_VERSION
    min_research_readiness_score: Decimal = Decimal("0.550000")
    pass_research_readiness_score: Decimal = Decimal("0.750000")
    min_cost_threshold_score: Decimal = Decimal("0.450000")
    pass_cost_threshold_score: Decimal = Decimal("0.700000")
    min_evidence_package_score: Decimal = Decimal("0.500000")
    pass_evidence_package_score: Decimal = Decimal("0.750000")
    min_team_capacity_score: Decimal = Decimal("0.350000")
    pass_team_capacity_score: Decimal = Decimal("0.650000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCandidateTriageMatrixConfig:
            raise TypeError("ResearchCandidateTriageMatrixConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchCandidateTriageMatrixConfig:
            raise ValueError("config must be exactly ResearchCandidateTriageMatrixConfig")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_CANDIDATE_TRIAGE_MATRIX_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_research_readiness_score",
            "pass_research_readiness_score",
            "min_cost_threshold_score",
            "pass_cost_threshold_score",
            "min_evidence_package_score",
            "pass_evidence_package_score",
            "min_team_capacity_score",
            "pass_team_capacity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_research_readiness_score > self.pass_research_readiness_score:
            raise ValueError("min_research_readiness_score must not exceed pass threshold")
        if self.min_cost_threshold_score > self.pass_cost_threshold_score:
            raise ValueError("min_cost_threshold_score must not exceed pass threshold")
        if self.min_evidence_package_score > self.pass_evidence_package_score:
            raise ValueError("min_evidence_package_score must not exceed pass threshold")
        if self.min_team_capacity_score > self.pass_team_capacity_score:
            raise ValueError("min_team_capacity_score must not exceed pass threshold")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchCandidateTriageInput:
    triage_item_key: str
    research_readiness_score: Decimal
    cost_threshold_score: Decimal
    evidence_package_score: Decimal
    team_capacity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCandidateTriageInput:
            raise TypeError("ResearchCandidateTriageInput does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchCandidateTriageInput:
            raise ValueError("input must be exactly ResearchCandidateTriageInput")
        _require_public_identifier("triage_item_key", self.triage_item_key)
        for field_name in (
            "research_readiness_score",
            "cost_threshold_score",
            "evidence_package_score",
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
class ResearchCandidateTriageMatrixPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCandidateTriageMatrixPublicPayloadItem:
            raise TypeError(
                "ResearchCandidateTriageMatrixPublicPayloadItem does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCandidateTriageMatrixPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchCandidateTriageMatrixPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchCandidateTriageMatrixRow:
    triage_item_key: str
    research_readiness_score: Decimal
    cost_threshold_score: Decimal
    evidence_package_score: Decimal
    team_capacity_score: Decimal
    composite_triage_score: Decimal
    manual_research_priority_score: Decimal
    triage_status: str
    manual_research_bucket: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCandidateTriageMatrixRow:
            raise TypeError("ResearchCandidateTriageMatrixRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchCandidateTriageMatrixRow:
            raise ValueError("row must be exactly ResearchCandidateTriageMatrixRow")
        _require_public_identifier("triage_item_key", self.triage_item_key)
        for field_name in (
            "research_readiness_score",
            "cost_threshold_score",
            "evidence_package_score",
            "team_capacity_score",
            "composite_triage_score",
            "manual_research_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_triage_status("triage_status", self.triage_status)
        _require_manual_research_bucket(
            "manual_research_bucket",
            self.manual_research_bucket,
        )
        if self.manual_research_bucket != _BUCKET_BY_STATUS[self.triage_status]:
            raise ValueError("manual_research_bucket must match triage_status")
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchCandidateTriageMatrixReport:
    generated_at: datetime
    config_version: str
    triage_status: str
    top_manual_research_bucket: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_composite_triage_score: Decimal
    max_manual_research_priority_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchCandidateTriageMatrixRow, ...]
    public_payload: tuple[ResearchCandidateTriageMatrixPublicPayloadItem, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCandidateTriageMatrixReport:
            raise TypeError("ResearchCandidateTriageMatrixReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchCandidateTriageMatrixReport:
            raise ValueError("report must be exactly ResearchCandidateTriageMatrixReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_CANDIDATE_TRIAGE_MATRIX_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_triage_status("triage_status", self.triage_status)
        _require_manual_research_bucket(
            "top_manual_research_bucket",
            self.top_manual_research_bucket,
        )
        if self.top_manual_research_bucket != _BUCKET_BY_STATUS[self.triage_status]:
            raise ValueError("top_manual_research_bucket must match triage_status")
        for field_name in ("item_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_composite_triage_score",
            "max_manual_research_priority_score",
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
        return research_candidate_triage_matrix_payload(self)


def build_research_candidate_triage_matrix(
    inputs: Sequence[ResearchCandidateTriageInput],
    *,
    generated_at: datetime,
    config: ResearchCandidateTriageMatrixConfig | None = None,
    public_payload: Sequence[ResearchCandidateTriageMatrixPublicPayloadItem] = (),
) -> ResearchCandidateTriageMatrixReport:
    """Build a deterministic paper-only triage matrix report."""

    if config is None:
        config = ResearchCandidateTriageMatrixConfig()
    if type(config) is not ResearchCandidateTriageMatrixConfig:
        raise ValueError("config must be a ResearchCandidateTriageMatrixConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = _build_rows(normalized_inputs, config)
    status = _report_status(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "triage_status": status,
        "top_manual_research_bucket": _BUCKET_BY_STATUS[status],
        "item_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_composite_triage_score": _average_ratio(
            tuple(row.composite_triage_score for row in rows),
        ),
        "max_manual_research_priority_score": max(
            (row.manual_research_priority_score for row in rows),
            default=_ZERO,
        ),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "public_payload": _normalize_public_payload(public_payload),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchCandidateTriageMatrixReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_candidate_triage_matrix_payload(
    value: ResearchCandidateTriageMatrixReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchCandidateTriageMatrixReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError("value must be a ResearchCandidateTriageMatrixReport or dict")
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_public_payload_digest(payload)
    return payload


def _build_rows(
    inputs: tuple[ResearchCandidateTriageInput, ...],
    config: ResearchCandidateTriageMatrixConfig,
) -> tuple[ResearchCandidateTriageMatrixRow, ...]:
    return tuple(sorted((_row_for_input(item, config) for item in inputs), key=_row_sort_key))


def _row_for_input(
    item: ResearchCandidateTriageInput,
    config: ResearchCandidateTriageMatrixConfig,
) -> ResearchCandidateTriageMatrixRow:
    composite_score = _average_ratio(
        (
            item.research_readiness_score,
            item.cost_threshold_score,
            item.evidence_package_score,
            item.team_capacity_score,
        ),
    )
    reason_codes = _row_reason_codes(
        research_readiness_score=item.research_readiness_score,
        cost_threshold_score=item.cost_threshold_score,
        evidence_package_score=item.evidence_package_score,
        team_capacity_score=item.team_capacity_score,
        config=config,
    )
    status = _row_status(reason_codes)
    return ResearchCandidateTriageMatrixRow(
        triage_item_key=item.triage_item_key,
        research_readiness_score=item.research_readiness_score,
        cost_threshold_score=item.cost_threshold_score,
        evidence_package_score=item.evidence_package_score,
        team_capacity_score=item.team_capacity_score,
        composite_triage_score=composite_score,
        manual_research_priority_score=_manual_research_priority_score(
            triage_status=status,
            research_readiness_score=item.research_readiness_score,
            cost_threshold_score=item.cost_threshold_score,
            evidence_package_score=item.evidence_package_score,
            team_capacity_score=item.team_capacity_score,
        ),
        triage_status=status,
        manual_research_bucket=_BUCKET_BY_STATUS[status],
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    research_readiness_score: Decimal,
    cost_threshold_score: Decimal,
    evidence_package_score: Decimal,
    team_capacity_score: Decimal,
    config: ResearchCandidateTriageMatrixConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if research_readiness_score < config.min_research_readiness_score:
        reason_codes.append("research_readiness_block")
    if cost_threshold_score < config.min_cost_threshold_score:
        reason_codes.append("cost_threshold_block")
    if evidence_package_score < config.min_evidence_package_score:
        reason_codes.append("evidence_package_block")
    if team_capacity_score < config.min_team_capacity_score:
        reason_codes.append("team_capacity_block")
    if not any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        if research_readiness_score < config.pass_research_readiness_score:
            reason_codes.append("research_readiness_watch")
        if cost_threshold_score < config.pass_cost_threshold_score:
            reason_codes.append("cost_threshold_watch")
        if evidence_package_score < config.pass_evidence_package_score:
            reason_codes.append("evidence_package_watch")
        if team_capacity_score < config.pass_team_capacity_score:
            reason_codes.append("team_capacity_watch")
    return tuple(reason_codes or ("triage_matrix_pass",))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("triage_matrix_pass",):
        return "pass"
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    return "watch"


def _manual_research_priority_score(
    triage_status: str,
    *,
    research_readiness_score: Decimal,
    cost_threshold_score: Decimal,
    evidence_package_score: Decimal,
    team_capacity_score: Decimal,
) -> Decimal:
    base_priority = (
        (_ONE - research_readiness_score) * Decimal("0.100000")
        + (_ONE - cost_threshold_score) * Decimal("0.150000")
        + (_ONE - evidence_package_score) * Decimal("0.200000")
        + (_ONE - team_capacity_score) * Decimal("0.333333")
    )
    if triage_status == "block":
        return _clamp_ratio(base_priority + Decimal("0.500000"))
    if triage_status == "watch":
        return _clamp_ratio(base_priority + Decimal("0.250000"))
    return _clamp_ratio(base_priority)


def _report_status(rows: tuple[ResearchCandidateTriageMatrixRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.triage_status == "block" for row in rows):
        return "block"
    if any(row.triage_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[ResearchCandidateTriageMatrixRow, ...]) -> tuple[str, ...]:
    if not rows:
        return ("empty_input",)
    reason_codes: list[str] = []
    for code in _REASON_CODE_SEQUENCE:
        if any(code in row.reason_codes for row in rows):
            reason_codes.append(code)
    return tuple(reason_codes)


def _status_count(rows: tuple[ResearchCandidateTriageMatrixRow, ...], status: str) -> int:
    return len(tuple(row for row in rows if row.triage_status == status))


def _validate_row_consistency(row: ResearchCandidateTriageMatrixRow) -> None:
    expected_status = _row_status(row.reason_codes)
    if row.triage_status != expected_status:
        raise ValueError("triage_status must match reason_codes")


def _validate_report_consistency(report: ResearchCandidateTriageMatrixReport) -> None:
    if report.item_count != _decimal_count(len(report.rows)):
        raise ValueError("item_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    expected_average_score = _average_ratio(
        tuple(row.composite_triage_score for row in report.rows),
    )
    if report.average_composite_triage_score != expected_average_score:
        raise ValueError("average_composite_triage_score must match rows")
    expected_max_priority = max(
        (row.manual_research_priority_score for row in report.rows),
        default=_ZERO,
    )
    if report.max_manual_research_priority_score != expected_max_priority:
        raise ValueError("max_manual_research_priority_score must match rows")
    if report.triage_status != _report_status(report.rows):
        raise ValueError("triage_status must match rows")
    if report.top_manual_research_bucket != _BUCKET_BY_STATUS[report.triage_status]:
        raise ValueError("top_manual_research_bucket must match triage_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_inputs(
    inputs: Sequence[ResearchCandidateTriageInput],
) -> tuple[ResearchCandidateTriageInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    for item in normalized:
        if type(item) is not ResearchCandidateTriageInput:
            raise ValueError("inputs items must be ResearchCandidateTriageInput")
        _require_hard_flags("input", item)
    item_keys = tuple(item.triage_item_key for item in normalized)
    if len(set(item_keys)) != len(item_keys):
        raise ValueError("triage_item_key values must be unique")
    return normalized


def _normalize_rows(
    rows: tuple[ResearchCandidateTriageMatrixRow, ...],
) -> tuple[ResearchCandidateTriageMatrixRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchCandidateTriageMatrixRow:
            raise ValueError("rows items must be ResearchCandidateTriageMatrixRow")
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic triage matrix ordering")
    item_keys = tuple(row.triage_item_key for row in normalized)
    if len(set(item_keys)) != len(item_keys):
        raise ValueError("row triage_item_key values must be unique")
    return normalized


def _normalize_public_payload(
    public_payload: Sequence[ResearchCandidateTriageMatrixPublicPayloadItem],
) -> tuple[ResearchCandidateTriageMatrixPublicPayloadItem, ...]:
    if type(public_payload) not in (list, tuple):
        raise ValueError("public_payload must be a list or tuple")
    normalized = tuple(public_payload)
    for item in normalized:
        if type(item) is not ResearchCandidateTriageMatrixPublicPayloadItem:
            raise ValueError(
                "public_payload items must be ResearchCandidateTriageMatrixPublicPayloadItem",
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


def _row_sort_key(row: ResearchCandidateTriageMatrixRow) -> tuple[int, Decimal, str]:
    status_weight = {"block": 0, "watch": 1, "pass": 2}
    return (
        status_weight[row.triage_status],
        -row.manual_research_priority_score,
        row.triage_item_key,
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


def _require_triage_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _TRIAGE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_manual_research_bucket(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _MANUAL_RESEARCH_BUCKETS:
        raise ValueError(f"{field_name} must be a supported manual research bucket")


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
    triage_status: str,
    top_manual_research_bucket: str,
    item_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    average_composite_triage_score: Decimal,
    max_manual_research_priority_score: Decimal,
    reason_codes: tuple[str, ...],
    rows: tuple[ResearchCandidateTriageMatrixRow, ...],
    public_payload: tuple[ResearchCandidateTriageMatrixPublicPayloadItem, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> dict[str, object]:
    return {
        "generated_at": _json_ready(generated_at),
        "config_version": config_version,
        "triage_status": triage_status,
        "top_manual_research_bucket": top_manual_research_bucket,
        "item_count": _json_ready(item_count),
        "pass_count": _json_ready(pass_count),
        "watch_count": _json_ready(watch_count),
        "block_count": _json_ready(block_count),
        "average_composite_triage_score": _json_ready(average_composite_triage_score),
        "max_manual_research_priority_score": _json_ready(
            max_manual_research_priority_score,
        ),
        "reason_codes": list(reason_codes),
        "rows": [_row_payload(row) for row in rows],
        "public_payload": [_public_payload_item_payload(item) for item in public_payload],
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }


def _row_payload(row: ResearchCandidateTriageMatrixRow) -> dict[str, object]:
    return {
        "triage_item_key": row.triage_item_key,
        "research_readiness_score": _json_ready(row.research_readiness_score),
        "cost_threshold_score": _json_ready(row.cost_threshold_score),
        "evidence_package_score": _json_ready(row.evidence_package_score),
        "team_capacity_score": _json_ready(row.team_capacity_score),
        "composite_triage_score": _json_ready(row.composite_triage_score),
        "manual_research_priority_score": _json_ready(
            row.manual_research_priority_score,
        ),
        "triage_status": row.triage_status,
        "manual_research_bucket": row.manual_research_bucket,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _public_payload_item_payload(
    item: ResearchCandidateTriageMatrixPublicPayloadItem,
) -> dict[str, object]:
    return {
        "key": item.key,
        "value": item.value,
        "paper_only": item.paper_only,
        "report_only": item.report_only,
        "readonly": item.readonly,
    }


def _report_payload(report: ResearchCandidateTriageMatrixReport) -> dict[str, object]:
    payload = _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        triage_status=report.triage_status,
        top_manual_research_bucket=report.top_manual_research_bucket,
        item_count=report.item_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_composite_triage_score=report.average_composite_triage_score,
        max_manual_research_priority_score=report.max_manual_research_priority_score,
        reason_codes=report.reason_codes,
        rows=report.rows,
        public_payload=report.public_payload,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    payload[_DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
    return payload


def _report_digest(report: ResearchCandidateTriageMatrixReport) -> str:
    return _report_digest_from_values(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "triage_status": report.triage_status,
            "top_manual_research_bucket": report.top_manual_research_bucket,
            "item_count": report.item_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "average_composite_triage_score": report.average_composite_triage_score,
            "max_manual_research_priority_score": (
                report.max_manual_research_priority_score
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
        triage_status=_require_mapping_value(values, "triage_status", str),
        top_manual_research_bucket=_require_mapping_value(
            values,
            "top_manual_research_bucket",
            str,
        ),
        item_count=_require_mapping_value(values, "item_count", Decimal),
        pass_count=_require_mapping_value(values, "pass_count", Decimal),
        watch_count=_require_mapping_value(values, "watch_count", Decimal),
        block_count=_require_mapping_value(values, "block_count", Decimal),
        average_composite_triage_score=_require_mapping_value(
            values,
            "average_composite_triage_score",
            Decimal,
        ),
        max_manual_research_priority_score=_require_mapping_value(
            values,
            "max_manual_research_priority_score",
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
    if type(value) is ResearchCandidateTriageMatrixReport:
        return _report_payload(value)
    if type(value) is ResearchCandidateTriageMatrixRow:
        return _row_payload(value)
    if type(value) is ResearchCandidateTriageMatrixPublicPayloadItem:
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
    raise ValueError("JSON payload is not JSON-ready")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            ResearchCandidateTriageMatrixConfig,
            ResearchCandidateTriageInput,
            ResearchCandidateTriageMatrixPublicPayloadItem,
            ResearchCandidateTriageMatrixRow,
            ResearchCandidateTriageMatrixReport,
        ):
            raise ValueError(f"{label} contains unsupported public dataclass")
        for field in fields(value):
            _reject_unsafe_public_fragment(f"{current_path}.{field.name}", field.name)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                f"{current_path}.{field.name}",
            )
        return
    if type(value) is dict:
        if not allow_json_containers:
            raise ValueError(f"{current_path} contains unsupported public mapping")
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_fragment(f"{current_path}.{key}", key)
            _reject_unsafe_public_payload(
                label,
                nested_value,
                f"{current_path}.{key}",
                allow_json_containers=True,
            )
        return
    if type(value) is list or type(value) is tuple:
        if not allow_json_containers:
            for index, nested_value in enumerate(value):
                _reject_unsafe_public_payload(
                    label,
                    nested_value,
                    f"{current_path}[{index}]",
                )
            return
        for index, nested_value in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                nested_value,
                f"{current_path}[{index}]",
                allow_json_containers=True,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_fragment(current_path, value)


def _reject_unsafe_public_fragment(field_name: str, value: str) -> None:
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public detail")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.casefold()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_CANDIDATE_TRIAGE_MATRIX_CONFIG_VERSION",
    "ResearchCandidateTriageInput",
    "ResearchCandidateTriageMatrixConfig",
    "ResearchCandidateTriageMatrixPublicPayloadItem",
    "ResearchCandidateTriageMatrixReport",
    "ResearchCandidateTriageMatrixRow",
    "build_research_candidate_triage_matrix",
    "research_candidate_triage_matrix_payload",
)
