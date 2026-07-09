"""Pure report-only event memory claim guard."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_EVENT_MEMORY_SOURCE_CLAIM_GUARD_REPORT_CONFIG_VERSION = (
    "research-event-memory-source-claim-guard-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_CLAIM_POSITIONS = frozenset(("supports", "contradicts", "neutral"))
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_REASON_SEQUENCE = (
    "claim_guard_no_inputs",
    "thin_claim_memory",
    "thin_independent_channels",
    "contradiction_pressure_watch",
    "contradiction_pressure_block",
    "stale_memory_claims",
    "low_credibility_watch",
    "low_credibility_block",
    "claim_guard_pass",
)
_DIGEST_FIELD = "derived_validation_digest"
_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_BLOCK_REASONS = frozenset(
    (
        "claim_guard_no_inputs",
        "thin_claim_memory",
        "thin_independent_channels",
        "contradiction_pressure_block",
        "low_credibility_block",
    ),
)
_WATCH_REASONS = frozenset(
    (
        "contradiction_pressure_watch",
        "stale_memory_claims",
        "low_credibility_watch",
    ),
)
_UNSAFE_TOKENS = frozenset(
    (
        "candidate",
        "market",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "http",
        "www",
    ),
)


@dataclass(frozen=True)
class ResearchEventMemorySourceClaimGuardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_MEMORY_SOURCE_CLAIM_GUARD_REPORT_CONFIG_VERSION
    )
    min_claim_count: Decimal = Decimal("2.000000")
    min_independent_channel_count: Decimal = Decimal("2.000000")
    stale_claim_age_seconds: Decimal = Decimal("86400.000000")
    contradiction_watch_threshold: Decimal = Decimal("0.250000")
    contradiction_block_threshold: Decimal = Decimal("0.500000")
    credibility_watch_threshold: Decimal = Decimal("0.600000")
    credibility_block_threshold: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventMemorySourceClaimGuardConfig:
            raise TypeError(
                "ResearchEventMemorySourceClaimGuardConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventMemorySourceClaimGuardConfig:
            raise ValueError(
                "config must be exactly ResearchEventMemorySourceClaimGuardConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_MEMORY_SOURCE_CLAIM_GUARD_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_claim_count",
            "min_independent_channel_count",
            "stale_claim_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "contradiction_watch_threshold",
            "contradiction_block_threshold",
            "credibility_watch_threshold",
            "credibility_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.contradiction_block_threshold <= self.contradiction_watch_threshold:
            raise ValueError(
                "contradiction_watch_threshold must be less than "
                "contradiction_block_threshold",
            )
        if self.credibility_watch_threshold <= self.credibility_block_threshold:
            raise ValueError(
                "credibility_block_threshold must be less than "
                "credibility_watch_threshold",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventMemorySourceClaimGuardInputRow:
    event_memory_key: str
    evidence_channel: str
    claim_position: str
    observed_at: datetime
    credibility_weight_score: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventMemorySourceClaimGuardInputRow:
            raise TypeError(
                "ResearchEventMemorySourceClaimGuardInputRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventMemorySourceClaimGuardInputRow:
            raise ValueError(
                "input row must be exactly ResearchEventMemorySourceClaimGuardInputRow",
            )
        _require_public_identifier("event_memory_key", self.event_memory_key)
        _require_public_identifier("evidence_channel", self.evidence_channel)
        _require_claim_position("claim_position", self.claim_position)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "credibility_weight_score",
            _require_ratio_decimal(
                "credibility_weight_score",
                self.credibility_weight_score,
            ),
        )
        _require_hard_flags("input row", self)
        _reject_unsafe_public_payload("input row", self)


@dataclass(frozen=True)
class ResearchEventMemorySourceClaimGuardPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventMemorySourceClaimGuardPublicPayloadItem:
            raise TypeError(
                "ResearchEventMemorySourceClaimGuardPublicPayloadItem does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventMemorySourceClaimGuardPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchEventMemorySourceClaimGuardPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchEventMemorySourceClaimGuardRow:
    event_memory_key: str
    claim_count: Decimal
    independent_channel_count: Decimal
    support_count: Decimal
    contradiction_count: Decimal
    neutral_count: Decimal
    contradiction_ratio: Decimal
    stale_claim_count: Decimal
    credibility_weight_score: Decimal
    guard_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventMemorySourceClaimGuardRow:
            raise TypeError(
                "ResearchEventMemorySourceClaimGuardRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventMemorySourceClaimGuardRow:
            raise ValueError("row must be exactly ResearchEventMemorySourceClaimGuardRow")
        _require_public_identifier("event_memory_key", self.event_memory_key)
        for field_name in (
            "claim_count",
            "independent_channel_count",
            "support_count",
            "contradiction_count",
            "neutral_count",
            "stale_claim_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("contradiction_ratio", "credibility_weight_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("guard_status", self.guard_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.guard_status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("guard_status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventMemorySourceClaimGuardReport:
    generated_at: datetime
    config_version: str
    guard_status: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    claim_count: Decimal
    contradiction_count: Decimal
    stale_claim_count: Decimal
    average_contradiction_ratio: Decimal
    average_credibility_weight_score: Decimal
    rows: tuple[ResearchEventMemorySourceClaimGuardRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchEventMemorySourceClaimGuardPublicPayloadItem, ...] = ()
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventMemorySourceClaimGuardReport:
            raise TypeError(
                "ResearchEventMemorySourceClaimGuardReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventMemorySourceClaimGuardReport:
            raise ValueError(
                "report must be exactly ResearchEventMemorySourceClaimGuardReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_MEMORY_SOURCE_CLAIM_GUARD_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("guard_status", self.guard_status)
        for field_name in (
            "event_count",
            "pass_count",
            "watch_count",
            "block_count",
            "claim_count",
            "contradiction_count",
            "stale_claim_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_contradiction_ratio",
            "average_credibility_weight_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_row_tuple("rows", self.rows)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.guard_status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("guard_status must match reason_codes")
        object.__setattr__(
            self,
            "public_payload",
            _require_public_payload_tuple("public_payload", self.public_payload),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        payload = research_event_memory_source_claim_guard_report_public_payload(self)
        expected_digest = _payload_digest(payload)
        if expected_digest != self.derived_validation_digest:
            raise ValueError("derived_validation_digest does not match public payload")

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_memory_source_claim_guard_report_public_payload(self)


def build_research_event_memory_source_claim_guard_report(
    rows: tuple[ResearchEventMemorySourceClaimGuardInputRow, ...],
    *,
    generated_at: datetime,
    config: ResearchEventMemorySourceClaimGuardConfig | None = None,
    public_payload: tuple[ResearchEventMemorySourceClaimGuardPublicPayloadItem, ...] = (),
) -> ResearchEventMemorySourceClaimGuardReport:
    cfg = config or ResearchEventMemorySourceClaimGuardConfig()
    if type(cfg) is not ResearchEventMemorySourceClaimGuardConfig:
        raise TypeError(
            "config must be exactly ResearchEventMemorySourceClaimGuardConfig",
        )
    observed_at = _as_utc("generated_at", generated_at)
    input_rows = _require_input_row_tuple("rows", rows)
    extra_payload = _require_public_payload_tuple("public_payload", public_payload)
    for row in input_rows:
        if row.observed_at > observed_at:
            raise ValueError("observed_at must not be in the future")

    if not input_rows:
        report_rows: tuple[ResearchEventMemorySourceClaimGuardRow, ...] = ()
        reason_codes = ("claim_guard_no_inputs",)
    else:
        report_rows = tuple(
            sorted(
                (
                    _build_report_row(
                        event_memory_key=event_memory_key,
                        input_rows=group_rows,
                        config=cfg,
                        generated_at=observed_at,
                    )
                    for event_memory_key, group_rows in _group_rows(input_rows)
                ),
                key=lambda row: (
                    _STATUS_RANK[row.guard_status],
                    row.event_memory_key,
                ),
            ),
        )
        reason_codes = _report_reason_codes(report_rows)

    guard_status = _status_from_reason_codes(reason_codes)
    event_count = _count_decimal(report_rows)
    report = _report_with_digest(
        generated_at=observed_at,
        config_version=cfg.config_version,
        guard_status=guard_status,
        event_count=event_count,
        pass_count=_sum_if(report_rows, lambda row: row.guard_status == "pass"),
        watch_count=_sum_if(report_rows, lambda row: row.guard_status == "watch"),
        block_count=_sum_if(report_rows, lambda row: row.guard_status == "block"),
        claim_count=_sum_decimal(row.claim_count for row in report_rows),
        contradiction_count=_sum_decimal(row.contradiction_count for row in report_rows),
        stale_claim_count=_sum_decimal(row.stale_claim_count for row in report_rows),
        average_contradiction_ratio=_mean_decimal(
            row.contradiction_ratio for row in report_rows
        ),
        average_credibility_weight_score=_mean_decimal(
            row.credibility_weight_score for row in report_rows
        ),
        rows=report_rows,
        reason_codes=reason_codes,
        public_payload=extra_payload,
    )
    return report


def research_event_memory_source_claim_guard_report_public_payload(
    report: ResearchEventMemorySourceClaimGuardReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventMemorySourceClaimGuardReport:
        raise TypeError(
            "report must be exactly ResearchEventMemorySourceClaimGuardReport",
        )
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_unsafe_public_payload("public payload", payload, allow_json_containers=True)
    if report.derived_validation_digest:
        supplied_digest = payload.get(_DIGEST_FIELD)
        if supplied_digest != _payload_digest(payload):
            raise ValueError("derived_validation_digest does not match public payload")
    return payload


def validate_research_event_memory_source_claim_guard_report_public_payload(
    payload: Mapping[str, Any],
) -> bool:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    payload_dict = dict(payload)
    _reject_unsafe_public_payload("payload", payload_dict, allow_json_containers=True)
    _require_hard_flags("payload", _FlagView(payload_dict))
    supplied_digest = payload_dict.get(_DIGEST_FIELD)
    _require_sha256_digest("derived_validation_digest", supplied_digest)
    expected_digest = _payload_digest(payload_dict)
    if supplied_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")
    statuses = _collect_statuses(payload_dict)
    if not statuses <= _STATUSES:
        raise ValueError("payload status must be pass, watch, or block")
    return True


def _report_with_digest(**values: Any) -> ResearchEventMemorySourceClaimGuardReport:
    payload = _json_ready({**values, _DIGEST_FIELD: "0" * 64, **_default_flags()})
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    digest = _payload_digest(payload)
    return ResearchEventMemorySourceClaimGuardReport(
        **values,
        derived_validation_digest=digest,
    )


def _default_flags() -> dict[str, bool]:
    return {"paper_only": True, "report_only": True, "readonly": True}


def _build_report_row(
    *,
    event_memory_key: str,
    input_rows: tuple[ResearchEventMemorySourceClaimGuardInputRow, ...],
    config: ResearchEventMemorySourceClaimGuardConfig,
    generated_at: datetime,
) -> ResearchEventMemorySourceClaimGuardRow:
    claim_count = _count_decimal(input_rows)
    support_count = _sum_if(input_rows, lambda row: row.claim_position == "supports")
    contradiction_count = _sum_if(
        input_rows,
        lambda row: row.claim_position == "contradicts",
    )
    neutral_count = _sum_if(input_rows, lambda row: row.claim_position == "neutral")
    independent_channel_count = _count_decimal(
        tuple({row.evidence_channel for row in input_rows})
    )
    stale_claim_count = _sum_if(
        input_rows,
        lambda row: _age_seconds(generated_at, row.observed_at)
        > config.stale_claim_age_seconds,
    )
    credibility_weight_score = _mean_decimal(
        row.credibility_weight_score for row in input_rows
    )
    contradiction_ratio = _safe_ratio(contradiction_count, claim_count)
    reason_codes = _row_reason_codes(
        claim_count=claim_count,
        independent_channel_count=independent_channel_count,
        contradiction_ratio=contradiction_ratio,
        stale_claim_count=stale_claim_count,
        credibility_weight_score=credibility_weight_score,
        config=config,
    )
    return ResearchEventMemorySourceClaimGuardRow(
        event_memory_key=event_memory_key,
        claim_count=claim_count,
        independent_channel_count=independent_channel_count,
        support_count=support_count,
        contradiction_count=contradiction_count,
        neutral_count=neutral_count,
        contradiction_ratio=contradiction_ratio,
        stale_claim_count=stale_claim_count,
        credibility_weight_score=credibility_weight_score,
        guard_status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    claim_count: Decimal,
    independent_channel_count: Decimal,
    contradiction_ratio: Decimal,
    stale_claim_count: Decimal,
    credibility_weight_score: Decimal,
    config: ResearchEventMemorySourceClaimGuardConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if claim_count < config.min_claim_count:
        reasons.append("thin_claim_memory")
    if independent_channel_count < config.min_independent_channel_count:
        reasons.append("thin_independent_channels")
    if contradiction_ratio >= config.contradiction_block_threshold:
        reasons.append("contradiction_pressure_block")
    elif contradiction_ratio >= config.contradiction_watch_threshold:
        reasons.append("contradiction_pressure_watch")
    if stale_claim_count > _ZERO:
        reasons.append("stale_memory_claims")
    has_blocking_reason = any(reason_code in _BLOCK_REASONS for reason_code in reasons)
    if credibility_weight_score <= config.credibility_block_threshold:
        reasons.append("low_credibility_block")
    elif (
        not has_blocking_reason
        and credibility_weight_score < config.credibility_watch_threshold
    ):
        reasons.append("low_credibility_watch")
    if not reasons:
        reasons.append("claim_guard_pass")
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _report_reason_codes(
    rows: tuple[ResearchEventMemorySourceClaimGuardRow, ...],
) -> tuple[str, ...]:
    reasons: list[str] = []
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code not in reasons:
                reasons.append(reason_code)
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _group_rows(
    rows: tuple[ResearchEventMemorySourceClaimGuardInputRow, ...],
) -> tuple[tuple[str, tuple[ResearchEventMemorySourceClaimGuardInputRow, ...]], ...]:
    groups: dict[str, list[ResearchEventMemorySourceClaimGuardInputRow]] = {}
    for row in rows:
        groups.setdefault(row.event_memory_key, []).append(row)
    return tuple(
        (key, tuple(sorted(group_rows, key=lambda item: (item.evidence_channel, item.claim_position))))
        for key, group_rows in sorted(groups.items())
    )


def _json_ready(value: object) -> Any:
    if isinstance(value, Decimal):
        return _format_decimal(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, (str, bool)) or value is None:
        return value
    raise ValueError(f"unsupported public payload value {value!r}")


def _payload_digest(payload: Mapping[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop(_DIGEST_FIELD, None)
    _reject_unsafe_public_payload(
        "digest payload",
        digest_payload,
        allow_json_containers=True,
    )
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _collect_statuses(value: object) -> set[str]:
    statuses: set[str] = set()
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in {"guard_status"} and isinstance(child, str):
                statuses.add(child)
            statuses.update(_collect_statuses(child))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            statuses.update(_collect_statuses(child))
    return statuses


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASONS for reason_code in reason_codes):
        return "block"
    if any(reason_code in _WATCH_REASONS for reason_code in reason_codes):
        return "watch"
    return "pass"


def _normalize_reason_codes(name: str, values: object) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise ValueError(f"{name} must be a tuple")
    if not values:
        raise ValueError(f"{name} must not be empty")
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str) or value not in _REASON_SEQUENCE:
            raise ValueError(f"{name} contains an unsupported reason code")
        if value not in normalized:
            normalized.append(value)
    return tuple(
        reason_code
        for reason_code in _REASON_SEQUENCE
        if reason_code in normalized
    )


def _require_input_row_tuple(
    name: str,
    values: object,
) -> tuple[ResearchEventMemorySourceClaimGuardInputRow, ...]:
    if not isinstance(values, tuple):
        raise TypeError(f"{name} must be a tuple")
    for value in values:
        if type(value) is not ResearchEventMemorySourceClaimGuardInputRow:
            raise TypeError(
                f"{name} must contain ResearchEventMemorySourceClaimGuardInputRow",
            )
    return values


def _require_row_tuple(
    name: str,
    values: object,
) -> tuple[ResearchEventMemorySourceClaimGuardRow, ...]:
    if not isinstance(values, tuple):
        raise ValueError(f"{name} must be a tuple")
    for value in values:
        if type(value) is not ResearchEventMemorySourceClaimGuardRow:
            raise ValueError(
                f"{name} must contain ResearchEventMemorySourceClaimGuardRow",
            )
    return values


def _require_public_payload_tuple(
    name: str,
    values: object,
) -> tuple[ResearchEventMemorySourceClaimGuardPublicPayloadItem, ...]:
    if not isinstance(values, tuple):
        raise ValueError(f"{name} must be a tuple")
    for value in values:
        if type(value) is not ResearchEventMemorySourceClaimGuardPublicPayloadItem:
            raise ValueError(
                f"{name} must contain "
                "ResearchEventMemorySourceClaimGuardPublicPayloadItem",
            )
    return values


def _require_public_identifier(name: str, value: object) -> None:
    if not isinstance(value, str) or not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public identifier")
    _reject_unsafe_text(name, value)


def _require_public_text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 240:
        raise ValueError(f"{name} must be public text")
    _reject_unsafe_text(name, value)
    return value


def _require_claim_position(name: str, value: object) -> None:
    if not isinstance(value, str) or value not in _CLAIM_POSITIONS:
        raise ValueError(f"{name} must be supports, contradicts, or neutral")


def _require_status(name: str, value: object) -> None:
    if not isinstance(value, str) or value not in _STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_sha256_digest(name: str, value: object) -> None:
    if not isinstance(value, str) or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase sha256 digest")


def _require_positive_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal_value


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANT)


def _format_decimal(value: Decimal) -> str:
    return format(_require_decimal("decimal", value), ".6f")


def _sum_decimal(values: Sequence[Decimal] | Any) -> Decimal:
    total = _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        for value in values:
            total += _require_decimal("sum value", value)
    return _quantize_decimal(total)


def _sum_if(values: Sequence[Any], predicate: Any) -> Decimal:
    total = _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        for value in values:
            if predicate(value):
                total += _ONE
    return _quantize_decimal(total)


def _count_decimal(values: Sequence[Any]) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize_decimal(Decimal(len(values)))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator = _require_decimal("numerator", numerator)
    denominator = _require_decimal("denominator", denominator)
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)


def _mean_decimal(values: Any) -> Decimal:
    items = tuple(values)
    if not items:
        return _ZERO
    return _safe_ratio(_sum_decimal(items), _count_decimal(items))


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = _as_utc("later", later) - _as_utc("earlier", earlier)
    total = (
        Decimal(delta.days) * _SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / _MICROSECONDS_PER_SECOND)
    )
    return _quantize_decimal(total)


def _as_utc(name: str, value: object) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in _FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_text(f"{label}.{field.name}", field.name)
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{label} must not contain raw mappings")
        for key, child in value.items():
            _reject_unsafe_text(f"{label}.{key}", str(key))
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                child,
                allow_json_containers=True,
            )
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _reject_unsafe_public_payload(
                f"{label}[{index}]",
                child,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, str):
        _reject_unsafe_text(label, value)


def _reject_unsafe_text(name: str, value: str) -> None:
    lowered = value.lower()
    for token in _UNSAFE_TOKENS:
        if token in lowered:
            raise ValueError(f"{name} contains unsafe public payload text")


@dataclass(frozen=True)
class _FlagView:
    value: Mapping[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")
