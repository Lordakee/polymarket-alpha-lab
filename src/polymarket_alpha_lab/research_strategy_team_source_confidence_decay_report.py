"""Report-only source confidence decay snapshot for research team inputs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any, final


DEFAULT_RESEARCH_STRATEGY_TEAM_SOURCE_CONFIDENCE_DECAY_CONFIG_VERSION = (
    "research-strategy-team-source-confidence-decay-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_FIXED_DECIMAL_CONTEXT = Context(prec=50, rounding=ROUND_HALF_UP)
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_PUBLIC_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = frozenset(("pass", "watch", "blocked"))
_SOURCE_KINDS = frozenset(("primary", "secondary", "context"))
_TEAM_ROLES = frozenset(("resolver", "reviewer", "specialist"))
_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_REPORT_PAYLOAD_KEYS = (
    "generated_at",
    "config_version",
    "status",
    "source_count",
    "pass_count",
    "watch_count",
    "blocked_count",
    "average_effective_confidence_score",
    "max_source_age_seconds",
    "rows",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_PAYLOAD_KEYS = (
    "source_public_key",
    "source_family",
    "source_kind",
    "team_role",
    "observed_at",
    "source_age_seconds",
    "age_confidence_score",
    "base_confidence_score",
    "historical_success_count",
    "historical_miss_count",
    "track_record_score",
    "effective_confidence_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_UNSAFE_PUBLIC_TERMS = (
    "li" + "ve",
    "au" + "th",
    "wal" + "let",
    "or" + "der",
    "net" + "work",
    "data" + "base",
    "per" + "sist",
    "sign" + "ing",
    "buy",
    "sell",
    "tra" + "de",
    "siz" + "ing",
    "rec" + "ommend" + "ation",
    "tok" + "en",
    "ds" + "n",
)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyTeamSourceConfidenceDecayConfig:
    config_version: str = DEFAULT_RESEARCH_STRATEGY_TEAM_SOURCE_CONFIDENCE_DECAY_CONFIG_VERSION
    fresh_age_seconds: Decimal = Decimal("3600.000000")
    stale_age_seconds: Decimal = Decimal("86400.000000")
    pass_effective_confidence_score: Decimal = Decimal("0.700000")
    watch_effective_confidence_score: Decimal = Decimal("0.400000")
    age_weight: Decimal = Decimal("0.550000")
    base_confidence_weight: Decimal = Decimal("0.450000")
    low_sample_block_threshold: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        object.__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamSourceConfidenceDecayConfig:
            raise TypeError(
                "ResearchStrategyTeamSourceConfidenceDecayConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyTeamSourceConfidenceDecayConfig:
            raise ValueError(
                "config must be exactly ResearchStrategyTeamSourceConfidenceDecayConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_TEAM_SOURCE_CONFIDENCE_DECAY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        object.__setattr__(
            self,
            "fresh_age_seconds",
            _require_positive_decimal("fresh_age_seconds", self.fresh_age_seconds),
        )
        object.__setattr__(
            self,
            "stale_age_seconds",
            _require_positive_decimal("stale_age_seconds", self.stale_age_seconds),
        )
        if self.stale_age_seconds <= self.fresh_age_seconds:
            raise ValueError("stale_age_seconds must exceed fresh_age_seconds")
        for field_name in (
            "pass_effective_confidence_score",
            "watch_effective_confidence_score",
            "age_weight",
            "base_confidence_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_effective_confidence_score <= self.watch_effective_confidence_score:
            raise ValueError(
                "pass_effective_confidence_score must exceed "
                "watch_effective_confidence_score",
            )
        with localcontext(_FIXED_DECIMAL_CONTEXT):
            weights_sum = self.age_weight + self.base_confidence_weight
        if _quantize(weights_sum) != _ONE:
            raise ValueError("age_weight and base_confidence_weight must sum to one")
        object.__setattr__(
            self,
            "low_sample_block_threshold",
            _require_nonnegative_count_decimal(
                "low_sample_block_threshold",
                self.low_sample_block_threshold,
            ),
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyTeamSourceConfidenceDecayInput:
    candidate_id: str
    market_id: str
    market_slug: str
    market_question: str
    source_url: str
    source_text: str
    source_family: str
    source_kind: str
    team_role: str
    observed_at: datetime
    base_confidence_score: Decimal
    historical_success_count: Decimal
    historical_miss_count: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        object.__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamSourceConfidenceDecayInput:
            raise TypeError(
                "ResearchStrategyTeamSourceConfidenceDecayInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyTeamSourceConfidenceDecayInput:
            raise ValueError(
                "input must be exactly ResearchStrategyTeamSourceConfidenceDecayInput",
            )
        for field_name in (
            "candidate_id",
            "market_id",
            "market_slug",
            "market_question",
            "source_url",
            "source_text",
        ):
            _require_raw_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "source_family",
            _require_public_identifier("source_family", self.source_family),
        )
        _require_enum("source_kind", self.source_kind, _SOURCE_KINDS)
        _require_enum("team_role", self.team_role, _TEAM_ROLES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "base_confidence_score",
            _require_ratio_decimal("base_confidence_score", self.base_confidence_score),
        )
        for field_name in ("historical_success_count", "historical_miss_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_input_reason_codes(self.reason_codes),
        )
        _require_hard_flags("input", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyTeamSourceConfidenceDecayRow:
    source_public_key: str
    source_family: str
    source_kind: str
    team_role: str
    observed_at: datetime
    source_age_seconds: Decimal
    age_confidence_score: Decimal
    base_confidence_score: Decimal
    historical_success_count: Decimal
    historical_miss_count: Decimal
    track_record_score: Decimal
    effective_confidence_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        object.__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamSourceConfidenceDecayRow:
            raise TypeError(
                "ResearchStrategyTeamSourceConfidenceDecayRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyTeamSourceConfidenceDecayRow:
            raise ValueError("row must be exactly ResearchStrategyTeamSourceConfidenceDecayRow")
        _require_public_digest("source_public_key", self.source_public_key)
        object.__setattr__(
            self,
            "source_family",
            _require_public_identifier("source_family", self.source_family),
        )
        _require_enum("source_kind", self.source_kind, _SOURCE_KINDS)
        _require_enum("team_role", self.team_role, _TEAM_ROLES)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "source_age_seconds",
            "historical_success_count",
            "historical_miss_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "age_confidence_score",
            "base_confidence_score",
            "track_record_score",
            "effective_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyTeamSourceConfidenceDecayReport:
    generated_at: datetime
    config_version: str
    status: str
    source_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_effective_confidence_score: Decimal
    max_source_age_seconds: Decimal
    rows: tuple[ResearchStrategyTeamSourceConfidenceDecayRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        object.__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamSourceConfidenceDecayReport:
            raise TypeError(
                "ResearchStrategyTeamSourceConfidenceDecayReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyTeamSourceConfidenceDecayReport:
            raise ValueError(
                "report must be exactly ResearchStrategyTeamSourceConfidenceDecayReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_TEAM_SOURCE_CONFIDENCE_DECAY_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        _require_status("status", self.status)
        for field_name in ("source_count", "pass_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("average_effective_confidence_score", "max_source_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")


def build_research_strategy_team_source_confidence_decay_report(
    source_inputs: Sequence[ResearchStrategyTeamSourceConfidenceDecayInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyTeamSourceConfidenceDecayConfig | None = None,
) -> ResearchStrategyTeamSourceConfidenceDecayReport:
    if config is None:
        config = ResearchStrategyTeamSourceConfidenceDecayConfig()
    if type(config) is not ResearchStrategyTeamSourceConfidenceDecayConfig:
        raise ValueError("config must be ResearchStrategyTeamSourceConfidenceDecayConfig")
    ResearchStrategyTeamSourceConfidenceDecayConfig.__post_init__(config)
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    inputs = _normalize_source_inputs(source_inputs)
    for item in inputs:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (_row_from_input(item, generated_at=generated_at, config=config) for item in inputs),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "source_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "blocked_count": _decimal_count(_status_count(rows, "blocked")),
        "average_effective_confidence_score": _average(
            tuple(row.effective_confidence_score for row in rows),
        ),
        "max_source_age_seconds": max(
            (row.source_age_seconds for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyTeamSourceConfidenceDecayReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_strategy_team_source_confidence_decay_report_payload(
    report: ResearchStrategyTeamSourceConfidenceDecayReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyTeamSourceConfidenceDecayReport:
        _require_hard_flags("report", report)
        expected_digest = _report_digest_from_values(_report_values_without_digest(report))
        if report.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _reject_unsafe_public_keys("payload", report)
        _validate_public_payload_schema(report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be ResearchStrategyTeamSourceConfidenceDecayReport")
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    if type(report) is ResearchStrategyTeamSourceConfidenceDecayReport:
        _validate_public_payload_schema(payload)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    return payload


def _row_from_input(
    item: ResearchStrategyTeamSourceConfidenceDecayInput,
    *,
    generated_at: datetime,
    config: ResearchStrategyTeamSourceConfidenceDecayConfig,
) -> ResearchStrategyTeamSourceConfidenceDecayRow:
    age_seconds = _age_seconds(generated_at, item.observed_at)
    age_score = _age_confidence_score(age_seconds, config.stale_age_seconds)
    sample_count = _decimal_add(
        item.historical_success_count,
        item.historical_miss_count,
    )
    track_score = _track_record_score(
        item.historical_success_count,
        item.historical_miss_count,
    )
    effective_score = _effective_confidence_score(
        age_confidence_score=age_score,
        base_confidence_score=item.base_confidence_score,
        track_record_score=track_score,
        config=config,
    )
    status = _row_status(
        effective_confidence_score=effective_score,
        sample_count=sample_count,
        config=config,
    )
    return ResearchStrategyTeamSourceConfidenceDecayRow(
        source_public_key=_source_public_key(item),
        source_family=item.source_family,
        source_kind=item.source_kind,
        team_role=item.team_role,
        observed_at=item.observed_at,
        source_age_seconds=age_seconds,
        age_confidence_score=age_score,
        base_confidence_score=item.base_confidence_score,
        historical_success_count=item.historical_success_count,
        historical_miss_count=item.historical_miss_count,
        track_record_score=track_score,
        effective_confidence_score=effective_score,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            source_age_seconds=age_seconds,
            track_record_score=track_score,
            sample_count=sample_count,
            config=config,
            input_reason_codes=item.reason_codes,
        ),
    )


def _source_public_key(item: ResearchStrategyTeamSourceConfidenceDecayInput) -> str:
    payload = _json_ready(
        (
            item.candidate_id,
            item.market_id,
            item.market_slug,
            item.market_question,
            item.source_url,
            item.source_text,
            item.source_family,
            item.source_kind,
            item.team_role,
            item.observed_at,
        ),
    )
    canonical = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _age_confidence_score(age_seconds: Decimal, stale_age_seconds: Decimal) -> Decimal:
    if age_seconds >= stale_age_seconds:
        return _ZERO
    with localcontext(_FIXED_DECIMAL_CONTEXT):
        value = _ONE - (age_seconds / stale_age_seconds)
    return _clamp_ratio(value)


def _track_record_score(success_count: Decimal, miss_count: Decimal) -> Decimal:
    sample_count = _decimal_add(success_count, miss_count)
    if sample_count <= _ZERO:
        return _ZERO
    with localcontext(_FIXED_DECIMAL_CONTEXT):
        value = success_count / sample_count
    return _clamp_ratio(value)


def _effective_confidence_score(
    *,
    age_confidence_score: Decimal,
    base_confidence_score: Decimal,
    track_record_score: Decimal,
    config: ResearchStrategyTeamSourceConfidenceDecayConfig,
) -> Decimal:
    with localcontext(_FIXED_DECIMAL_CONTEXT):
        miss_rate = _ONE - track_record_score
        miss_penalty_base = max(age_confidence_score, base_confidence_score)
        raw_score = (
            (age_confidence_score * config.age_weight)
            + (base_confidence_score * config.base_confidence_weight)
            - (miss_rate * config.base_confidence_weight * miss_penalty_base)
        )
    return _clamp_ratio(raw_score)


def _row_status(
    *,
    effective_confidence_score: Decimal,
    sample_count: Decimal,
    config: ResearchStrategyTeamSourceConfidenceDecayConfig,
) -> str:
    if sample_count <= config.low_sample_block_threshold:
        return "blocked"
    if effective_confidence_score < config.watch_effective_confidence_score:
        return "blocked"
    if effective_confidence_score < config.pass_effective_confidence_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    status: str,
    source_age_seconds: Decimal,
    track_record_score: Decimal,
    sample_count: Decimal,
    config: ResearchStrategyTeamSourceConfidenceDecayConfig,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes: set[str] = {f"source_confidence_decay_{status}"}
    reason_codes.add(
        "stale_source" if source_age_seconds >= config.stale_age_seconds else "fresh_source",
    )
    if sample_count <= config.low_sample_block_threshold:
        reason_codes.add("low_sample_source")
    if track_record_score < config.watch_effective_confidence_score:
        reason_codes.add("weak_track_record")
    elif track_record_score >= config.pass_effective_confidence_score:
        reason_codes.add("strong_track_record")
    for reason_code in input_reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(rows: tuple[ResearchStrategyTeamSourceConfidenceDecayRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyTeamSourceConfidenceDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_sources",)
    if all(row.status == "pass" for row in rows):
        return ("source_confidence_decay_pass",)
    return _normalize_reason_codes(tuple(code for row in rows for code in row.reason_codes))


def _status_count(
    rows: tuple[ResearchStrategyTeamSourceConfidenceDecayRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_FIXED_DECIMAL_CONTEXT):
        value = sum(values, _ZERO) / Decimal(len(values))
    return _quantize(value)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    with localcontext(_FIXED_DECIMAL_CONTEXT):
        value = (
            Decimal(delta.days * 86_400)
            + Decimal(delta.seconds)
            + (Decimal(delta.microseconds) / Decimal("1000000"))
        )
    return _require_nonnegative_decimal("source_age_seconds", _quantize(value))


def _row_sort_key(row: ResearchStrategyTeamSourceConfidenceDecayRow) -> tuple[Decimal, str]:
    return (row.source_age_seconds, row.source_public_key)


def _normalize_source_inputs(
    source_inputs: Sequence[ResearchStrategyTeamSourceConfidenceDecayInput],
) -> tuple[ResearchStrategyTeamSourceConfidenceDecayInput, ...]:
    if isinstance(source_inputs, (str, bytes)) or not isinstance(source_inputs, Sequence):
        raise ValueError("source_inputs must be a sequence")
    normalized: list[ResearchStrategyTeamSourceConfidenceDecayInput] = []
    for item in source_inputs:
        if type(item) is not ResearchStrategyTeamSourceConfidenceDecayInput:
            raise ValueError(
                "source_inputs must contain ResearchStrategyTeamSourceConfidenceDecayInput",
            )
        ResearchStrategyTeamSourceConfidenceDecayInput.__post_init__(item)
        _require_hard_flags("input", item)
        normalized.append(item)
    return tuple(normalized)


def _normalize_rows(
    rows: Sequence[ResearchStrategyTeamSourceConfidenceDecayRow],
) -> tuple[ResearchStrategyTeamSourceConfidenceDecayRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchStrategyTeamSourceConfidenceDecayRow] = []
    seen_keys: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyTeamSourceConfidenceDecayRow:
            raise ValueError(
                "rows must contain ResearchStrategyTeamSourceConfidenceDecayRow",
            )
        _require_hard_flags("row", row)
        if row.source_public_key in seen_keys:
            raise ValueError("source_public_key values must be unique")
        seen_keys.add(row.source_public_key)
        normalized.append(row)
    sorted_rows = tuple(sorted(normalized, key=_row_sort_key))
    if tuple(normalized) != sorted_rows:
        raise ValueError("rows must be sorted")
    return sorted_rows


def _validate_row_consistency(row: ResearchStrategyTeamSourceConfidenceDecayRow) -> None:
    expected_track_score = _track_record_score(
        row.historical_success_count,
        row.historical_miss_count,
    )
    if row.track_record_score != expected_track_score:
        raise ValueError("track_record_score must match historical counts")
    if f"source_confidence_decay_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include status")


def _validate_report_consistency(
    report: ResearchStrategyTeamSourceConfidenceDecayReport,
) -> None:
    if report.source_count != _decimal_count(len(report.rows)):
        raise ValueError("source_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    expected_average = _average(tuple(row.effective_confidence_score for row in report.rows))
    if report.average_effective_confidence_score != expected_average:
        raise ValueError("average_effective_confidence_score must match rows")
    expected_max_age = max((row.source_age_seconds for row in report.rows), default=_ZERO)
    if report.max_source_age_seconds != expected_max_age:
        raise ValueError("max_source_age_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _report_values_without_digest(
    report: ResearchStrategyTeamSourceConfidenceDecayReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    if set(payload) != set(_REPORT_PAYLOAD_KEYS):
        raise ValueError("payload schema keys must match report payload")
    generated_at = _require_payload_datetime("generated_at", payload["generated_at"])
    _require_public_identifier("config_version", payload["config_version"])
    if (
        payload["config_version"]
        != DEFAULT_RESEARCH_STRATEGY_TEAM_SOURCE_CONFIDENCE_DECAY_CONFIG_VERSION
    ):
        raise ValueError("config_version must be supported")
    status = _require_status("status", payload["status"])
    source_count = _require_payload_count_decimal("source_count", payload["source_count"])
    pass_count = _require_payload_count_decimal("pass_count", payload["pass_count"])
    watch_count = _require_payload_count_decimal("watch_count", payload["watch_count"])
    blocked_count = _require_payload_count_decimal(
        "blocked_count",
        payload["blocked_count"],
    )
    average_effective_confidence_score = _require_payload_ratio_decimal(
        "average_effective_confidence_score",
        payload["average_effective_confidence_score"],
    )
    max_source_age_seconds = _require_payload_nonnegative_decimal(
        "max_source_age_seconds",
        payload["max_source_age_seconds"],
    )
    rows = _validate_public_payload_rows(payload["rows"])
    reason_codes = _require_payload_reason_codes("reason_codes", payload["reason_codes"])
    derived_validation_digest = _require_sha256_digest(
        "derived_validation_digest",
        payload["derived_validation_digest"],
    )
    _require_payload_hard_flags("payload", payload)
    expected_digest = _public_payload_digest(payload)
    if derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    if source_count != _decimal_count(len(rows)):
        raise ValueError("source_count must match rows")
    if pass_count != _decimal_count(_public_status_count(rows, "pass")):
        raise ValueError("pass_count must match rows")
    if watch_count != _decimal_count(_public_status_count(rows, "watch")):
        raise ValueError("watch_count must match rows")
    if blocked_count != _decimal_count(_public_status_count(rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if status != _public_report_status(rows):
        raise ValueError("status must match rows")
    expected_average = _average(
        tuple(row["effective_confidence_score"] for row in rows),
    )
    if average_effective_confidence_score != expected_average:
        raise ValueError("average_effective_confidence_score must match rows")
    expected_max_age = max((row["source_age_seconds"] for row in rows), default=_ZERO)
    if max_source_age_seconds != expected_max_age:
        raise ValueError("max_source_age_seconds must match rows")
    if reason_codes != _public_report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if generated_at.tzinfo is not UTC:
        raise ValueError("generated_at must be a UTC datetime string")


def _validate_public_payload_rows(value: object) -> tuple[dict[str, Any], ...]:
    if type(value) is not list:
        raise ValueError("payload schema rows must be a list")
    rows: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    for row_value in value:
        row = _validate_public_payload_row(row_value)
        source_public_key = row["source_public_key"]
        if source_public_key in seen_keys:
            raise ValueError("source_public_key values must be unique")
        seen_keys.add(source_public_key)
        rows.append(row)
    normalized = tuple(rows)
    if normalized != tuple(sorted(normalized, key=_public_row_sort_key)):
        raise ValueError("rows must be sorted")
    return normalized


def _validate_public_payload_row(value: object) -> dict[str, Any]:
    if type(value) is not dict or set(value) != set(_ROW_PAYLOAD_KEYS):
        raise ValueError("payload schema row keys must match row payload")
    row = {
        "source_public_key": _require_public_digest(
            "source_public_key",
            value["source_public_key"],
        ),
        "source_family": _require_public_identifier(
            "source_family",
            value["source_family"],
        ),
        "source_kind": _require_enum("source_kind", value["source_kind"], _SOURCE_KINDS),
        "team_role": _require_enum("team_role", value["team_role"], _TEAM_ROLES),
        "observed_at": _require_payload_datetime("observed_at", value["observed_at"]),
        "source_age_seconds": _require_payload_nonnegative_decimal(
            "source_age_seconds",
            value["source_age_seconds"],
        ),
        "age_confidence_score": _require_payload_ratio_decimal(
            "age_confidence_score",
            value["age_confidence_score"],
        ),
        "base_confidence_score": _require_payload_ratio_decimal(
            "base_confidence_score",
            value["base_confidence_score"],
        ),
        "historical_success_count": _require_payload_count_decimal(
            "historical_success_count",
            value["historical_success_count"],
        ),
        "historical_miss_count": _require_payload_count_decimal(
            "historical_miss_count",
            value["historical_miss_count"],
        ),
        "track_record_score": _require_payload_ratio_decimal(
            "track_record_score",
            value["track_record_score"],
        ),
        "effective_confidence_score": _require_payload_ratio_decimal(
            "effective_confidence_score",
            value["effective_confidence_score"],
        ),
        "status": _require_status("status", value["status"]),
        "reason_codes": _require_payload_reason_codes(
            "reason_codes",
            value["reason_codes"],
        ),
        "paper_only": value["paper_only"],
        "report_only": value["report_only"],
        "readonly": value["readonly"],
    }
    _require_payload_hard_flags("row", row)
    expected_track_score = _track_record_score(
        row["historical_success_count"],
        row["historical_miss_count"],
    )
    if row["track_record_score"] != expected_track_score:
        raise ValueError("track_record_score must match historical counts")
    if f"source_confidence_decay_{row['status']}" not in row["reason_codes"]:
        raise ValueError("reason_codes must include status")
    return row


def _require_payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a UTC datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a UTC datetime string")
    return normalized


def _require_payload_count_decimal(field_name: str, value: object) -> Decimal:
    return _require_payload_decimal_string(
        field_name,
        value,
        normalizer=_require_nonnegative_count_decimal,
    )


def _require_payload_ratio_decimal(field_name: str, value: object) -> Decimal:
    return _require_payload_decimal_string(
        field_name,
        value,
        normalizer=_require_ratio_decimal,
    )


def _require_payload_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    return _require_payload_decimal_string(
        field_name,
        value,
        normalizer=_require_nonnegative_decimal,
    )


def _require_payload_decimal_string(
    field_name: str,
    value: object,
    *,
    normalizer: Any,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    normalized = normalizer(field_name, parsed)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _require_payload_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    normalized = _normalize_reason_codes(tuple(value))
    if list(normalized) != value:
        raise ValueError(f"{field_name} must be sorted and unique")
    return normalized


def _require_payload_hard_flags(label: str, value: Mapping[str, object]) -> None:
    for field_name in _FLAG_FIELDS:
        if value.get(field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _public_status_count(rows: tuple[dict[str, Any], ...], status: str) -> int:
    return sum(1 for row in rows if row["status"] == status)


def _public_report_status(rows: tuple[dict[str, Any], ...]) -> str:
    if not rows:
        return "blocked"
    if any(row["status"] == "blocked" for row in rows):
        return "blocked"
    if any(row["status"] == "watch" for row in rows):
        return "watch"
    return "pass"


def _public_report_reason_codes(rows: tuple[dict[str, Any], ...]) -> tuple[str, ...]:
    if not rows:
        return ("no_sources",)
    if all(row["status"] == "pass" for row in rows):
        return ("source_confidence_decay_pass",)
    return _normalize_reason_codes(
        tuple(code for row in rows for code in row["reason_codes"]),
    )


def _public_row_sort_key(row: dict[str, Any]) -> tuple[Decimal, str]:
    return (row["source_age_seconds"], row["source_public_key"])


def _public_payload_digest(payload: Mapping[str, object]) -> str:
    unsigned = {key: payload[key] for key in _REPORT_PAYLOAD_KEYS if key != "derived_validation_digest"}
    canonical = json.dumps(unsigned, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload("derived_validation_digest payload", payload)
    canonical = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON ready")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = True,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if value is None or type(value) is bool or type(value) is Decimal or type(value) is datetime:
        return
    raise ValueError(f"{current_path} is not a supported public value")


def _reject_unsafe_public_keys(label: str, value: object, path: str = "") -> None:
    current_path = path or label
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_keys(label, item, key if not path else f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_unsafe_public_keys(label, item, f"{current_path}[{index}]")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_raw_text(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be nonempty text")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _PUBLIC_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 public key")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_enum(field_name: str, value: object, allowed: frozenset[str]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be supported")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_input_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_public_identifier("reason_codes", value)
        normalized.append(value)
    return tuple(sorted(set(normalized)))


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_public_identifier("reason_codes", value)
        normalized.append(value)
    if not normalized:
        raise ValueError("reason_codes must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_FIXED_DECIMAL_CONTEXT):
        normalized = value.quantize(_QUANT, rounding=ROUND_HALF_UP)
    return _ZERO if normalized.is_zero() else normalized


def _decimal_add(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(_FIXED_DECIMAL_CONTEXT):
        value = left + right
    return _quantize(value)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_TEAM_SOURCE_CONFIDENCE_DECAY_CONFIG_VERSION",
    "ResearchStrategyTeamSourceConfidenceDecayConfig",
    "ResearchStrategyTeamSourceConfidenceDecayInput",
    "ResearchStrategyTeamSourceConfidenceDecayReport",
    "ResearchStrategyTeamSourceConfidenceDecayRow",
    "build_research_strategy_team_source_confidence_decay_report",
    "research_strategy_team_source_confidence_decay_report_payload",
)
