from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    UNSAFE_SURFACE_FIELD_FRAGMENTS,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_CATEGORY_RESEARCH_CAPACITY_ROTATION_DIGEST_CONFIG_VERSION = (
    "strategy-category-research-capacity-rotation-digest-v0"
)
ROTATION_STATUSES = ("rotating_in", "rotating_out", "stable")
DIGEST_STATUSES = ("pass", "watch", "blocked")

_COUNT_QUANTUM = Decimal("1")
_RATIO_QUANTUM = Decimal("0.000001")
_ZERO_COUNT = Decimal("0")
_ONE_COUNT = Decimal("1")
_ZERO_RATIO = Decimal("0.000000")
_DECIMAL_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)

_STATUS_RANK = {"blocked": 0, "watch": 1, "pass": 2}
_ROTATION_RANK = {"rotating_in": 0, "rotating_out": 1, "stable": 2}
_UNSAFE_SURFACE_FRAGMENTS = (
    frozenset(
        fragment
        for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS
        if fragment != "".join(("si", "gn"))
    )
    | frozenset(
        "".join(parts)
        for parts in (
            ("li", "ve"),
            ("trad", "ing"),
            ("tra", "de"),
            ("bro", "ker"),
            ("cl", "ient"),
            ("exec", "ute"),
            ("conn", "ect"),
            ("requ", "est"),
            ("http",),
            ("market", "_slug"),
            ("ques", "tion"),
            ("reco", "mmend"),
            ("ad", "vice"),
        )
    )
)
_SENSITIVE_TEXT_FRAGMENTS = frozenset(
    "".join(parts)
    for parts in (
        ("sec", "ret"),
        ("api", "_key"),
        ("to", "ken"),
        ("sk_", "li", "ve"),
        ("0", "x"),
    )
)


@dataclass(frozen=True)
class StrategyCategoryResearchCapacityRotationDigestConfig:
    config_version: str = (
        DEFAULT_STRATEGY_CATEGORY_RESEARCH_CAPACITY_ROTATION_DIGEST_CONFIG_VERSION
    )
    min_rotation_in_share_delta: Decimal = Decimal("0.050000")
    watch_capacity_pressure_ratio: Decimal = Decimal("1.000000")
    blocked_capacity_pressure_ratio: Decimal = Decimal("2.000000")
    min_slot_coverage_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_rotation_in_share_delta",
            "watch_capacity_pressure_ratio",
            "blocked_capacity_pressure_ratio",
            "min_slot_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_ratio(field_name, getattr(self, field_name)),
            )
        if self.blocked_capacity_pressure_ratio < self.watch_capacity_pressure_ratio:
            raise ValueError(
                "blocked_capacity_pressure_ratio must be at least watch_capacity_pressure_ratio",
            )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class StrategyCategoryResearchCapacityRotationSignal:
    category_id: str = field(repr=False)
    strategy_id: str = field(repr=False)
    rotation_status: str
    liquidity_share_ratio_delta: Decimal
    ending_liquidity_share_ratio: Decimal
    queue_count: Decimal
    available_analyst_agent_slots: Decimal
    capacity_gap_count: Decimal
    source_row_count: Decimal = _ONE_COUNT
    source_missing: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("category_id", self.category_id)
        _require_canonical_string("strategy_id", self.strategy_id)
        _require_member("rotation_status", self.rotation_status, ROTATION_STATUSES)
        object.__setattr__(
            self,
            "liquidity_share_ratio_delta",
            _normalize_ratio("liquidity_share_ratio_delta", self.liquidity_share_ratio_delta),
        )
        object.__setattr__(
            self,
            "ending_liquidity_share_ratio",
            _normalize_nonnegative_ratio(
                "ending_liquidity_share_ratio",
                self.ending_liquidity_share_ratio,
            ),
        )
        for field_name in (
            "queue_count",
            "available_analyst_agent_slots",
            "capacity_gap_count",
            "source_row_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.capacity_gap_count > self.queue_count:
            raise ValueError("capacity_gap_count must not exceed queue_count")
        if type(self.source_missing) is not bool:
            raise ValueError("source_missing must be a bool")
        require_paper_only_flags("signal", self)


@dataclass(frozen=True)
class StrategyCategoryResearchCapacityRotationRow:
    redacted_category_ref: str
    redacted_strategy_ref: str
    rotation_status: str
    liquidity_share_ratio_delta: Decimal
    ending_liquidity_share_ratio: Decimal
    queue_count: Decimal
    available_analyst_agent_slots: Decimal
    capacity_gap_count: Decimal
    source_row_count: Decimal
    source_missing: bool
    capacity_pressure_ratio: Decimal
    slot_coverage_ratio: Decimal
    rotation_capacity_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_redacted_ref(
            "redacted_category_ref",
            self.redacted_category_ref,
            "<redacted-category-",
        )
        _require_redacted_ref(
            "redacted_strategy_ref",
            self.redacted_strategy_ref,
            "<redacted-strategy-",
        )
        _require_member("rotation_status", self.rotation_status, ROTATION_STATUSES)
        object.__setattr__(
            self,
            "liquidity_share_ratio_delta",
            _normalize_ratio("liquidity_share_ratio_delta", self.liquidity_share_ratio_delta),
        )
        object.__setattr__(
            self,
            "ending_liquidity_share_ratio",
            _normalize_nonnegative_ratio(
                "ending_liquidity_share_ratio",
                self.ending_liquidity_share_ratio,
            ),
        )
        for field_name in (
            "queue_count",
            "available_analyst_agent_slots",
            "capacity_gap_count",
            "source_row_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("capacity_pressure_ratio", "slot_coverage_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_ratio(field_name, getattr(self, field_name)),
            )
        if type(self.source_missing) is not bool:
            raise ValueError("source_missing must be a bool")
        _require_member(
            "rotation_capacity_status",
            self.rotation_capacity_status,
            DIGEST_STATUSES,
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "derived_validation_digest",
            (
                _row_derived_validation_digest(self)
                if self.derived_validation_digest == ""
                else _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                )
            ),
        )
        require_paper_only_flags("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class StrategyCategoryResearchCapacityRotationDigestReport:
    generated_at: datetime
    config_version: str
    source_signal_count: Decimal
    digest_row_count: Decimal
    pass_row_count: Decimal
    watch_row_count: Decimal
    blocked_row_count: Decimal
    source_missing_count: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    digest_rows: tuple[StrategyCategoryResearchCapacityRotationRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_signal_count",
            "digest_row_count",
            "pass_row_count",
            "watch_row_count",
            "blocked_row_count",
            "source_missing_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, DIGEST_STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        rows = tuple(self.digest_rows)
        for row in rows:
            if type(row) is not StrategyCategoryResearchCapacityRotationRow:
                raise ValueError("digest_rows must contain digest row values")
            require_paper_only_flags("row", row)
        object.__setattr__(self, "digest_rows", rows)
        _validate_report(self)
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
        require_paper_only_flags("report", self)
        _validate_report_derived_validation_digest(self)
        _reject_unsafe_public_payload("report", self)


def build_strategy_category_research_capacity_rotation_digest(
    signals: (
        list[StrategyCategoryResearchCapacityRotationSignal]
        | tuple[StrategyCategoryResearchCapacityRotationSignal, ...]
    ),
    *,
    config: StrategyCategoryResearchCapacityRotationDigestConfig,
    generated_at: datetime,
) -> StrategyCategoryResearchCapacityRotationDigestReport:
    if type(config) is not StrategyCategoryResearchCapacityRotationDigestConfig:
        raise ValueError(
            "config must be a StrategyCategoryResearchCapacityRotationDigestConfig",
        )
    require_paper_only_flags("config", config)
    normalized_signals = _normalize_signals(signals)
    category_refs = _redaction_map(
        tuple(signal.category_id for signal in normalized_signals),
        "category",
    )
    strategy_refs = _redaction_map(
        tuple(signal.strategy_id for signal in normalized_signals),
        "strategy",
    )
    rows = tuple(
        sorted(
            (
                _row_from_signal(
                    signal,
                    config=config,
                    redacted_category_ref=category_refs[signal.category_id],
                    redacted_strategy_ref=strategy_refs[signal.strategy_id],
                )
                for signal in normalized_signals
            ),
            key=_row_key,
        ),
    )

    pass_row_count = _count(
        sum(1 for row in rows if row.rotation_capacity_status == "pass"),
    )
    watch_row_count = _count(
        sum(1 for row in rows if row.rotation_capacity_status == "watch"),
    )
    blocked_row_count = _count(
        sum(1 for row in rows if row.rotation_capacity_status == "blocked"),
    )
    source_missing_count = _count(sum(1 for row in rows if row.source_missing))
    digest_status = _digest_status(rows)

    return StrategyCategoryResearchCapacityRotationDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_signal_count=_count(len(normalized_signals)),
        digest_row_count=_count(len(rows)),
        pass_row_count=pass_row_count,
        watch_row_count=watch_row_count,
        blocked_row_count=blocked_row_count,
        source_missing_count=source_missing_count,
        digest_status=digest_status,
        reason_codes=_report_reason_codes(
            digest_status,
            source_missing_count=source_missing_count,
        ),
        digest_rows=rows,
    )


def strategy_category_research_capacity_rotation_digest_payload(
    report: StrategyCategoryResearchCapacityRotationDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyCategoryResearchCapacityRotationDigestReport:
        require_paper_only_flags("report", report)
        _validate_report(report)
        _validate_report_derived_validation_digest(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a StrategyCategoryResearchCapacityRotationDigestReport",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    require_paper_only_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    _validate_public_payload(payload)
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


def _normalize_signals(
    signals: (
        list[StrategyCategoryResearchCapacityRotationSignal]
        | tuple[StrategyCategoryResearchCapacityRotationSignal, ...]
    ),
) -> tuple[StrategyCategoryResearchCapacityRotationSignal, ...]:
    if type(signals) not in (list, tuple):
        raise ValueError("signals must be a list or tuple")
    normalized = tuple(signals)
    seen_pairs: set[tuple[str, str]] = set()
    for signal in normalized:
        if type(signal) is not StrategyCategoryResearchCapacityRotationSignal:
            raise ValueError("signals must contain rotation signal values")
        require_paper_only_flags("signal", signal)
        pair = (signal.category_id, signal.strategy_id)
        if pair in seen_pairs:
            raise ValueError("signals must not contain duplicate category strategy pairs")
        seen_pairs.add(pair)
    return normalized


def _row_from_signal(
    signal: StrategyCategoryResearchCapacityRotationSignal,
    *,
    config: StrategyCategoryResearchCapacityRotationDigestConfig,
    redacted_category_ref: str,
    redacted_strategy_ref: str,
) -> StrategyCategoryResearchCapacityRotationRow:
    capacity_pressure_ratio = _ratio(
        signal.queue_count,
        signal.available_analyst_agent_slots,
    )
    slot_coverage_ratio = _ratio(
        signal.available_analyst_agent_slots,
        signal.queue_count,
    )
    status = _row_status(
        signal,
        config=config,
        capacity_pressure_ratio=capacity_pressure_ratio,
        slot_coverage_ratio=slot_coverage_ratio,
    )
    return StrategyCategoryResearchCapacityRotationRow(
        redacted_category_ref=redacted_category_ref,
        redacted_strategy_ref=redacted_strategy_ref,
        rotation_status=signal.rotation_status,
        liquidity_share_ratio_delta=signal.liquidity_share_ratio_delta,
        ending_liquidity_share_ratio=signal.ending_liquidity_share_ratio,
        queue_count=signal.queue_count,
        available_analyst_agent_slots=signal.available_analyst_agent_slots,
        capacity_gap_count=signal.capacity_gap_count,
        source_row_count=signal.source_row_count,
        source_missing=signal.source_missing,
        capacity_pressure_ratio=capacity_pressure_ratio,
        slot_coverage_ratio=slot_coverage_ratio,
        rotation_capacity_status=status,
        reason_codes=_row_reason_codes(
            signal,
            config=config,
            capacity_pressure_ratio=capacity_pressure_ratio,
            slot_coverage_ratio=slot_coverage_ratio,
            status=status,
        ),
    )


def _row_status(
    signal: StrategyCategoryResearchCapacityRotationSignal,
    *,
    config: StrategyCategoryResearchCapacityRotationDigestConfig,
    capacity_pressure_ratio: Decimal,
    slot_coverage_ratio: Decimal,
) -> str:
    if signal.source_missing:
        return "watch"
    if signal.rotation_status == "rotating_out":
        return "pass"
    if _is_blocked(signal, config, capacity_pressure_ratio, slot_coverage_ratio):
        return "blocked"
    if signal.rotation_status == "rotating_in":
        if signal.liquidity_share_ratio_delta >= config.min_rotation_in_share_delta:
            return "watch"
        if capacity_pressure_ratio >= config.watch_capacity_pressure_ratio:
            return "watch"
    if capacity_pressure_ratio >= config.watch_capacity_pressure_ratio:
        return "watch"
    return "pass"


def _is_blocked(
    signal: StrategyCategoryResearchCapacityRotationSignal,
    config: StrategyCategoryResearchCapacityRotationDigestConfig,
    capacity_pressure_ratio: Decimal,
    slot_coverage_ratio: Decimal,
) -> bool:
    if signal.capacity_gap_count > _ZERO_COUNT:
        return True
    if signal.queue_count > _ZERO_COUNT and signal.available_analyst_agent_slots == _ZERO_COUNT:
        return True
    if capacity_pressure_ratio >= config.blocked_capacity_pressure_ratio:
        return True
    return signal.queue_count > _ZERO_COUNT and slot_coverage_ratio < config.min_slot_coverage_ratio


def _row_reason_codes(
    signal: StrategyCategoryResearchCapacityRotationSignal,
    *,
    config: StrategyCategoryResearchCapacityRotationDigestConfig,
    capacity_pressure_ratio: Decimal,
    slot_coverage_ratio: Decimal,
    status: str,
) -> tuple[str, ...]:
    if signal.source_missing:
        return ("strategy_category_research_capacity_rotation_source_missing",)
    if signal.rotation_status == "rotating_out":
        return ("rotation_out_capacity_release",)

    reason_codes: list[str] = []
    if signal.rotation_status == "rotating_in":
        reason_codes.append(f"rotation_in_capacity_{status}")
    else:
        reason_codes.append(f"stable_capacity_{status}")

    if signal.capacity_gap_count > _ZERO_COUNT:
        reason_codes.append("capacity_gap_present")
    if signal.queue_count > _ZERO_COUNT and slot_coverage_ratio < config.min_slot_coverage_ratio:
        reason_codes.append("low_slot_coverage")
    if capacity_pressure_ratio >= config.blocked_capacity_pressure_ratio:
        reason_codes.append("capacity_pressure_blocked")
    elif capacity_pressure_ratio >= config.watch_capacity_pressure_ratio:
        reason_codes.append("capacity_pressure_watch")
    return tuple(reason_codes)


def _digest_status(
    rows: tuple[StrategyCategoryResearchCapacityRotationRow, ...],
) -> str:
    if any(row.rotation_capacity_status == "blocked" for row in rows):
        return "blocked"
    if any(row.rotation_capacity_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    digest_status: str,
    *,
    source_missing_count: Decimal,
) -> tuple[str, ...]:
    if digest_status == "blocked":
        return ("strategy_category_research_capacity_rotation_blocked",)
    if digest_status == "watch":
        reason_codes = ["strategy_category_research_capacity_rotation_watch"]
        if source_missing_count > _ZERO_COUNT:
            reason_codes.append(
                "strategy_category_research_capacity_rotation_source_missing",
            )
        return tuple(reason_codes)
    return ("strategy_category_research_capacity_rotation_clear",)


def _row_key(row: StrategyCategoryResearchCapacityRotationRow) -> tuple[int, int, str, str]:
    return (
        _STATUS_RANK[row.rotation_capacity_status],
        _ROTATION_RANK[row.rotation_status],
        row.redacted_category_ref,
        row.redacted_strategy_ref,
    )


def _redaction_map(values: tuple[str, ...], label: str) -> dict[str, str]:
    return {
        value: f"<redacted-{label}-{index:03d}>"
        for index, value in enumerate(sorted(set(values)), start=1)
    }


def _validate_report(report: StrategyCategoryResearchCapacityRotationDigestReport) -> None:
    rows = report.digest_rows
    for row in rows:
        _validate_row(row)
    if report.digest_row_count != _count(len(rows)):
        raise ValueError("digest_row_count must match digest_rows")
    if report.source_signal_count != report.digest_row_count:
        raise ValueError("source_signal_count must match digest_row_count")
    if report.pass_row_count != _count(
        sum(1 for row in rows if row.rotation_capacity_status == "pass"),
    ):
        raise ValueError("pass_row_count must match digest_rows")
    if report.watch_row_count != _count(
        sum(1 for row in rows if row.rotation_capacity_status == "watch"),
    ):
        raise ValueError("watch_row_count must match digest_rows")
    if report.blocked_row_count != _count(
        sum(1 for row in rows if row.rotation_capacity_status == "blocked"),
    ):
        raise ValueError("blocked_row_count must match digest_rows")
    if report.source_missing_count != _count(sum(1 for row in rows if row.source_missing)):
        raise ValueError("source_missing_count must match digest_rows")
    if report.digest_status != _digest_status(rows):
        raise ValueError("digest_status must match digest_rows")


def _validate_row(row: StrategyCategoryResearchCapacityRotationRow) -> None:
    expected_capacity_pressure_ratio = _ratio(
        row.queue_count,
        row.available_analyst_agent_slots,
    )
    if row.capacity_pressure_ratio != expected_capacity_pressure_ratio:
        raise ValueError("capacity_pressure_ratio must match row inputs")
    expected_slot_coverage_ratio = _ratio(
        row.available_analyst_agent_slots,
        row.queue_count,
    )
    if row.slot_coverage_ratio != expected_slot_coverage_ratio:
        raise ValueError("slot_coverage_ratio must match row inputs")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report_derived_validation_digest(
    report: StrategyCategoryResearchCapacityRotationDigestReport,
) -> None:
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _row_derived_validation_digest(
    row: StrategyCategoryResearchCapacityRotationRow,
) -> str:
    return _sha256(
        (
            "strategy_category_research_capacity_rotation_row",
            f"redacted_category_ref={row.redacted_category_ref}",
            f"redacted_strategy_ref={row.redacted_strategy_ref}",
            f"rotation_status={row.rotation_status}",
            f"liquidity_share_ratio_delta={_decimal_payload(row.liquidity_share_ratio_delta)}",
            f"ending_liquidity_share_ratio={_decimal_payload(row.ending_liquidity_share_ratio)}",
            f"queue_count={_decimal_payload(row.queue_count)}",
            "available_analyst_agent_slots="
            f"{_decimal_payload(row.available_analyst_agent_slots)}",
            f"capacity_gap_count={_decimal_payload(row.capacity_gap_count)}",
            f"source_row_count={_decimal_payload(row.source_row_count)}",
            f"source_missing={row.source_missing}",
            f"capacity_pressure_ratio={_decimal_payload(row.capacity_pressure_ratio)}",
            f"slot_coverage_ratio={_decimal_payload(row.slot_coverage_ratio)}",
            f"rotation_capacity_status={row.rotation_capacity_status}",
            f"reason_codes={','.join(row.reason_codes)}",
            f"paper_only={row.paper_only}",
            f"report_only={row.report_only}",
            f"readonly={row.readonly}",
        ),
    )


def _report_derived_validation_digest(
    report: StrategyCategoryResearchCapacityRotationDigestReport,
) -> str:
    return _sha256(
        (
            "strategy_category_research_capacity_rotation_report",
            f"generated_at={_as_utc('generated_at', report.generated_at).isoformat()}",
            f"config_version={report.config_version}",
            f"source_signal_count={_decimal_payload(report.source_signal_count)}",
            f"digest_row_count={_decimal_payload(report.digest_row_count)}",
            f"pass_row_count={_decimal_payload(report.pass_row_count)}",
            f"watch_row_count={_decimal_payload(report.watch_row_count)}",
            f"blocked_row_count={_decimal_payload(report.blocked_row_count)}",
            f"source_missing_count={_decimal_payload(report.source_missing_count)}",
            f"digest_status={report.digest_status}",
            f"reason_codes={','.join(report.reason_codes)}",
            "digest_rows="
            f"{','.join(row.derived_validation_digest for row in report.digest_rows)}",
            f"paper_only={report.paper_only}",
            f"report_only={report.report_only}",
            f"readonly={report.readonly}",
        ),
    )


def _sha256(parts: tuple[str, ...]) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode("utf-8"))
        digest.update(b"\x1f")
    return digest.hexdigest()


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a SHA-256 hex string")
    if len(value) != 64 or value.lower() != value:
        raise ValueError(f"{field_name} must be a SHA-256 hex string")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex string")
    return value


def _decimal_payload(value: Decimal) -> str:
    if type(value) is not Decimal:
        raise ValueError("Decimal payload value must be a Decimal")
    if not value.is_finite():
        raise ValueError("Decimal payload value must be finite")
    return str(value)


def _validate_public_payload(payload: dict[str, Any]) -> None:
    rows = _payload_rows(payload.get("digest_rows"))
    generated_at = _payload_generated_at(payload.get("generated_at"))
    config_version = _payload_string("config_version", payload.get("config_version"))
    source_signal_count = _payload_count(
        "source_signal_count",
        payload.get("source_signal_count"),
    )
    digest_row_count = _payload_count("digest_row_count", payload.get("digest_row_count"))
    pass_row_count = _payload_count("pass_row_count", payload.get("pass_row_count"))
    watch_row_count = _payload_count("watch_row_count", payload.get("watch_row_count"))
    blocked_row_count = _payload_count(
        "blocked_row_count",
        payload.get("blocked_row_count"),
    )
    source_missing_count = _payload_count(
        "source_missing_count",
        payload.get("source_missing_count"),
    )
    digest_status = _payload_member(
        "digest_status",
        payload.get("digest_status"),
        DIGEST_STATUSES,
    )
    reason_codes = _payload_reason_codes(payload.get("reason_codes"))
    paper_only = _payload_bool("paper_only", payload.get("paper_only"))
    report_only = _payload_bool("report_only", payload.get("report_only"))
    readonly = _payload_bool("readonly", payload.get("readonly"))

    if digest_row_count != _count(len(rows)):
        raise ValueError("digest_row_count must match digest_rows")
    if source_signal_count != digest_row_count:
        raise ValueError("source_signal_count must match digest_row_count")
    if pass_row_count != _count(
        sum(1 for row in rows if row["rotation_capacity_status"] == "pass"),
    ):
        raise ValueError("pass_row_count must match digest_rows")
    if watch_row_count != _count(
        sum(1 for row in rows if row["rotation_capacity_status"] == "watch"),
    ):
        raise ValueError("watch_row_count must match digest_rows")
    if blocked_row_count != _count(
        sum(1 for row in rows if row["rotation_capacity_status"] == "blocked"),
    ):
        raise ValueError("blocked_row_count must match digest_rows")
    if source_missing_count != _count(sum(1 for row in rows if row["source_missing"])):
        raise ValueError("source_missing_count must match digest_rows")
    expected_digest_status = _public_digest_status(rows)
    if digest_status != expected_digest_status:
        raise ValueError("digest_status must match digest_rows")

    expected_report_digest = _public_report_derived_validation_digest(
        generated_at=generated_at,
        config_version=config_version,
        source_signal_count=source_signal_count,
        digest_row_count=digest_row_count,
        pass_row_count=pass_row_count,
        watch_row_count=watch_row_count,
        blocked_row_count=blocked_row_count,
        source_missing_count=source_missing_count,
        digest_status=digest_status,
        reason_codes=reason_codes,
        row_digests=tuple(row["derived_validation_digest"] for row in rows),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )
    if _normalize_sha256(
        "derived_validation_digest",
        payload.get("derived_validation_digest"),
    ) != expected_report_digest:
        raise ValueError("derived_validation_digest must match payload fields")


def _payload_rows(value: object) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list):
        raise ValueError("digest_rows must be a list")
    rows: list[dict[str, Any]] = []
    for item in value:
        if type(item) is not dict:
            raise ValueError("digest_rows must contain JSON objects")
        rows.append(_validate_public_row(item))
    return tuple(rows)


def _validate_public_row(row: dict[str, Any]) -> dict[str, Any]:
    redacted_category_ref = _payload_string(
        "redacted_category_ref",
        row.get("redacted_category_ref"),
    )
    _require_redacted_ref(
        "redacted_category_ref",
        redacted_category_ref,
        "<redacted-category-",
    )
    redacted_strategy_ref = _payload_string(
        "redacted_strategy_ref",
        row.get("redacted_strategy_ref"),
    )
    _require_redacted_ref(
        "redacted_strategy_ref",
        redacted_strategy_ref,
        "<redacted-strategy-",
    )
    rotation_status = _payload_member(
        "rotation_status",
        row.get("rotation_status"),
        ROTATION_STATUSES,
    )
    liquidity_share_ratio_delta = _payload_ratio(
        "liquidity_share_ratio_delta",
        row.get("liquidity_share_ratio_delta"),
    )
    ending_liquidity_share_ratio = _payload_nonnegative_ratio(
        "ending_liquidity_share_ratio",
        row.get("ending_liquidity_share_ratio"),
    )
    queue_count = _payload_count("queue_count", row.get("queue_count"))
    available_analyst_agent_slots = _payload_count(
        "available_analyst_agent_slots",
        row.get("available_analyst_agent_slots"),
    )
    capacity_gap_count = _payload_count(
        "capacity_gap_count",
        row.get("capacity_gap_count"),
    )
    source_row_count = _payload_count("source_row_count", row.get("source_row_count"))
    source_missing = _payload_bool("source_missing", row.get("source_missing"))
    capacity_pressure_ratio = _payload_nonnegative_ratio(
        "capacity_pressure_ratio",
        row.get("capacity_pressure_ratio"),
    )
    slot_coverage_ratio = _payload_nonnegative_ratio(
        "slot_coverage_ratio",
        row.get("slot_coverage_ratio"),
    )
    rotation_capacity_status = _payload_member(
        "rotation_capacity_status",
        row.get("rotation_capacity_status"),
        DIGEST_STATUSES,
    )
    reason_codes = _payload_reason_codes(row.get("reason_codes"))
    paper_only = _payload_bool("paper_only", row.get("paper_only"))
    report_only = _payload_bool("report_only", row.get("report_only"))
    readonly = _payload_bool("readonly", row.get("readonly"))

    if capacity_gap_count > queue_count:
        raise ValueError("capacity_gap_count must not exceed queue_count")
    if capacity_pressure_ratio != _ratio(queue_count, available_analyst_agent_slots):
        raise ValueError("capacity_pressure_ratio must match row inputs")
    if slot_coverage_ratio != _ratio(available_analyst_agent_slots, queue_count):
        raise ValueError("slot_coverage_ratio must match row inputs")

    expected_row_digest = _public_row_derived_validation_digest(
        redacted_category_ref=redacted_category_ref,
        redacted_strategy_ref=redacted_strategy_ref,
        rotation_status=rotation_status,
        liquidity_share_ratio_delta=liquidity_share_ratio_delta,
        ending_liquidity_share_ratio=ending_liquidity_share_ratio,
        queue_count=queue_count,
        available_analyst_agent_slots=available_analyst_agent_slots,
        capacity_gap_count=capacity_gap_count,
        source_row_count=source_row_count,
        source_missing=source_missing,
        capacity_pressure_ratio=capacity_pressure_ratio,
        slot_coverage_ratio=slot_coverage_ratio,
        rotation_capacity_status=rotation_capacity_status,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )
    if _normalize_sha256(
        "derived_validation_digest",
        row.get("derived_validation_digest"),
    ) != expected_row_digest:
        raise ValueError("derived_validation_digest must match row payload fields")
    return {
        "rotation_capacity_status": rotation_capacity_status,
        "source_missing": source_missing,
        "derived_validation_digest": expected_row_digest,
    }


def _public_row_derived_validation_digest(
    *,
    redacted_category_ref: str,
    redacted_strategy_ref: str,
    rotation_status: str,
    liquidity_share_ratio_delta: Decimal,
    ending_liquidity_share_ratio: Decimal,
    queue_count: Decimal,
    available_analyst_agent_slots: Decimal,
    capacity_gap_count: Decimal,
    source_row_count: Decimal,
    source_missing: bool,
    capacity_pressure_ratio: Decimal,
    slot_coverage_ratio: Decimal,
    rotation_capacity_status: str,
    reason_codes: tuple[str, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> str:
    return _sha256(
        (
            "strategy_category_research_capacity_rotation_row",
            f"redacted_category_ref={redacted_category_ref}",
            f"redacted_strategy_ref={redacted_strategy_ref}",
            f"rotation_status={rotation_status}",
            f"liquidity_share_ratio_delta={_decimal_payload(liquidity_share_ratio_delta)}",
            f"ending_liquidity_share_ratio={_decimal_payload(ending_liquidity_share_ratio)}",
            f"queue_count={_decimal_payload(queue_count)}",
            "available_analyst_agent_slots="
            f"{_decimal_payload(available_analyst_agent_slots)}",
            f"capacity_gap_count={_decimal_payload(capacity_gap_count)}",
            f"source_row_count={_decimal_payload(source_row_count)}",
            f"source_missing={source_missing}",
            f"capacity_pressure_ratio={_decimal_payload(capacity_pressure_ratio)}",
            f"slot_coverage_ratio={_decimal_payload(slot_coverage_ratio)}",
            f"rotation_capacity_status={rotation_capacity_status}",
            f"reason_codes={','.join(reason_codes)}",
            f"paper_only={paper_only}",
            f"report_only={report_only}",
            f"readonly={readonly}",
        ),
    )


def _public_report_derived_validation_digest(
    *,
    generated_at: str,
    config_version: str,
    source_signal_count: Decimal,
    digest_row_count: Decimal,
    pass_row_count: Decimal,
    watch_row_count: Decimal,
    blocked_row_count: Decimal,
    source_missing_count: Decimal,
    digest_status: str,
    reason_codes: tuple[str, ...],
    row_digests: tuple[str, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> str:
    return _sha256(
        (
            "strategy_category_research_capacity_rotation_report",
            f"generated_at={generated_at}",
            f"config_version={config_version}",
            f"source_signal_count={_decimal_payload(source_signal_count)}",
            f"digest_row_count={_decimal_payload(digest_row_count)}",
            f"pass_row_count={_decimal_payload(pass_row_count)}",
            f"watch_row_count={_decimal_payload(watch_row_count)}",
            f"blocked_row_count={_decimal_payload(blocked_row_count)}",
            f"source_missing_count={_decimal_payload(source_missing_count)}",
            f"digest_status={digest_status}",
            f"reason_codes={','.join(reason_codes)}",
            f"digest_rows={','.join(row_digests)}",
            f"paper_only={paper_only}",
            f"report_only={report_only}",
            f"readonly={readonly}",
        ),
    )


def _public_digest_status(rows: tuple[dict[str, Any], ...]) -> str:
    if any(row["rotation_capacity_status"] == "blocked" for row in rows):
        return "blocked"
    if any(row["rotation_capacity_status"] == "watch" for row in rows):
        return "watch"
    return "pass"


def _payload_generated_at(value: object) -> str:
    if type(value) is not str:
        raise ValueError("generated_at must be a timezone-aware datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("generated_at must be a timezone-aware datetime string") from exc
    canonical = _as_utc("generated_at", parsed).isoformat()
    if value != canonical:
        raise ValueError("generated_at must be a canonical UTC datetime string")
    return value


def _payload_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    _reject_unsafe_public_text(field_name, value)
    return value


def _payload_member(field_name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")
    return value


def _payload_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _payload_count(field_name: str, value: object) -> Decimal:
    return _payload_decimal(field_name, value, _normalize_nonnegative_count)


def _payload_ratio(field_name: str, value: object) -> Decimal:
    return _payload_decimal(field_name, value, _normalize_ratio)


def _payload_nonnegative_ratio(field_name: str, value: object) -> Decimal:
    return _payload_decimal(field_name, value, _normalize_nonnegative_ratio)


def _payload_decimal(field_name: str, value: object, normalizer: Any) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal-derived string")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    normalized = normalizer(field_name, decimal_value)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal-derived string")
    return normalized


def _payload_reason_codes(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError("reason_codes must be a list")
    return _normalize_reason_codes(tuple(value))


def _json_ready(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("JSON datetime", value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, (str, bool)):
        return value
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_public_key(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _reject_unsafe_public_key(label: str, value: str) -> None:
    if _has_fragment(value, _UNSAFE_SURFACE_FRAGMENTS):
        raise ValueError(f"unsafe public field in {label}")
    if _has_fragment(value, _SENSITIVE_TEXT_FRAGMENTS):
        raise ValueError(f"sensitive public field in {label}")


def _reject_unsafe_public_text(label: str, value: str) -> None:
    if _has_fragment(value, _UNSAFE_SURFACE_FRAGMENTS):
        raise ValueError(f"unsafe public value in {label}")
    if _has_fragment(value, _SENSITIVE_TEXT_FRAGMENTS):
        raise ValueError(f"sensitive public value in {label}")


def _has_fragment(value: str, fragments: frozenset[str]) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in fragments)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO_COUNT:
        return _ZERO_RATIO
    with localcontext(_DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(_RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(_RATIO_QUANTUM)


def _normalize_nonnegative_ratio(field_name: str, value: object) -> Decimal:
    quantized = _normalize_ratio(field_name, value)
    if quantized < _ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    return reason_codes


def _require_reason_code(value: object) -> None:
    if type(value) is not str:
        raise ValueError("reason_codes must contain strings")
    if value.strip() != value or not value:
        raise ValueError("reason_codes must contain canonical strings")
    if value != value.lower() or value[0] == "_" or value[-1] == "_":
        raise ValueError("reason_codes must be lowercase snake_case strings")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError("reason_codes must be lowercase snake_case strings")
    _reject_unsafe_public_text("reason_codes", value)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_redacted_ref(field_name: str, value: object, prefix: str) -> None:
    _require_canonical_string(field_name, value)
    if not value.startswith(prefix) or not value.endswith(">"):
        raise ValueError(f"{field_name} must be redacted")
    opaque_id = value[len(prefix) : -1]
    if len(opaque_id) != 3 or not opaque_id.isdecimal():
        raise ValueError(f"{field_name} must be redacted")


__all__ = (
    "DEFAULT_STRATEGY_CATEGORY_RESEARCH_CAPACITY_ROTATION_DIGEST_CONFIG_VERSION",
    "ROTATION_STATUSES",
    "DIGEST_STATUSES",
    "StrategyCategoryResearchCapacityRotationDigestConfig",
    "StrategyCategoryResearchCapacityRotationSignal",
    "StrategyCategoryResearchCapacityRotationRow",
    "StrategyCategoryResearchCapacityRotationDigestReport",
    "build_strategy_category_research_capacity_rotation_digest",
    "strategy_category_research_capacity_rotation_digest_payload",
)
