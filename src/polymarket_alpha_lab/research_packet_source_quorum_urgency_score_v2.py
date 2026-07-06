"""Paper-only scoring for research packet source quorum urgency."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_PACKET_SOURCE_QUORUM_URGENCY_SCORE_V2_CONFIG_VERSION = (
    "research-packet-source-quorum-urgency-score-v2"
)

_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_PREFIX = "rpsqusv2"
_DIGEST_FIELD = "derived_validation_digest"
_BAD_PARTS = (
    "".join(("li", "ve")),
    "".join(("au", "th")),
    "".join(("wall", "et")),
    "".join(("or", "der")),
    "".join(("net", "wor", "k")),
    "".join(("data", "base")),
    "".join(("per", "sis", "t")),
    "".join(("si", "gn", "ing")),
    "".join(("mu", "ta", "tion")),
    "".join(("b", "uy")),
    "".join(("s", "ell")),
    "".join(("tr", "ade")),
)
_STATUSES = ("blocked", "watch", "pass")
_STATUS_WEIGHTS = {"blocked": 0, "watch": 1, "pass": 2}
_NO_ITEMS_REASON = "no_research_packets_to_score"


__all__ = (
    "DEFAULT_RESEARCH_PACKET_SOURCE_QUORUM_URGENCY_SCORE_V2_CONFIG_VERSION",
    "ResearchPacketSourceQuorumUrgencyScoreV2Config",
    "ResearchPacketSourceQuorumUrgencyScoreV2Observation",
    "ResearchPacketSourceQuorumUrgencyScoreV2Row",
    "ResearchPacketSourceQuorumUrgencyScoreV2Report",
    "build_research_packet_source_quorum_urgency_score_v2",
    "research_packet_source_quorum_urgency_score_v2_payload",
)


@dataclass(frozen=True)
class ResearchPacketSourceQuorumUrgencyScoreV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_SOURCE_QUORUM_URGENCY_SCORE_V2_CONFIG_VERSION
    )
    required_source_family_count: Decimal = Decimal("3.000000")
    required_current_source_count: Decimal = Decimal("3.000000")
    max_source_age_seconds: Decimal = Decimal("86400.000000")
    urgent_deadline_seconds: Decimal = Decimal("21600.000000")
    watch_deadline_seconds: Decimal = Decimal("86400.000000")
    source_gap_weight: Decimal = Decimal("0.600000")
    deadline_pressure_weight: Decimal = Decimal("0.400000")
    watch_score_threshold: Decimal = Decimal("0.250000")
    block_score_threshold: Decimal = Decimal("0.750000")
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("config", self, ResearchPacketSourceQuorumUrgencyScoreV2Config)
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "required_source_family_count",
            "required_current_source_count",
            "max_source_age_seconds",
            "urgent_deadline_seconds",
            "watch_deadline_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_gap_weight",
            "deadline_pressure_weight",
            "watch_score_threshold",
            "block_score_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_positive_count(
            "required_source_family_count",
            self.required_source_family_count,
        )
        _require_positive_count(
            "required_current_source_count",
            self.required_current_source_count,
        )
        _require_positive_decimal("max_source_age_seconds", self.max_source_age_seconds)
        _require_positive_decimal("urgent_deadline_seconds", self.urgent_deadline_seconds)
        _require_positive_decimal("watch_deadline_seconds", self.watch_deadline_seconds)
        if self.urgent_deadline_seconds >= self.watch_deadline_seconds:
            raise ValueError("urgent_deadline_seconds must be below watch_deadline_seconds")
        if self.source_gap_weight + self.deadline_pressure_weight != _ONE:
            raise ValueError("score weights must sum to 1.000000")
        if self.watch_score_threshold > self.block_score_threshold:
            raise ValueError("watch_score_threshold must not exceed block_score_threshold")
        _require_hard_flags("config", self)
        _reject_public_surface("config", self)
        _require_digest("config", self)


@dataclass(frozen=True)
class ResearchPacketSourceQuorumUrgencyScoreV2Observation:
    packet_id: str
    source_id: str
    source_family: str
    deadline_at: datetime
    observed_at: datetime | None = None
    source_blocked: bool = False
    supports_research_packet: bool = True
    reason_codes: tuple[str, ...] = ("research_packet_source_observed",)
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            "observation",
            self,
            ResearchPacketSourceQuorumUrgencyScoreV2Observation,
        )
        for field_name in ("packet_id", "source_id", "source_family"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "deadline_at", _as_utc("deadline_at", self.deadline_at))
        object.__setattr__(
            self,
            "observed_at",
            _as_optional_utc("observed_at", self.observed_at),
        )
        for field_name in ("source_blocked", "supports_research_packet"):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("observation", self)
        _reject_public_surface("observation", self)
        _require_digest("observation", self)


@dataclass(frozen=True)
class ResearchPacketSourceQuorumUrgencyScoreV2Row:
    packet_id: str
    deadline_at: datetime
    seconds_until_deadline: Decimal
    observed_source_count: Decimal
    current_source_count: Decimal
    current_source_family_count: Decimal
    stale_source_count: Decimal
    blocked_source_count: Decimal
    source_family_gap_count: Decimal
    current_source_gap_count: Decimal
    source_gap_score: Decimal
    deadline_pressure_score: Decimal
    quorum_urgency_score: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchPacketSourceQuorumUrgencyScoreV2Row)
        _require_public_string("packet_id", self.packet_id)
        object.__setattr__(self, "deadline_at", _as_utc("deadline_at", self.deadline_at))
        for field_name in (
            "seconds_until_deadline",
            "observed_source_count",
            "current_source_count",
            "current_source_family_count",
            "stale_source_count",
            "blocked_source_count",
            "source_family_gap_count",
            "current_source_gap_count",
            "source_gap_score",
            "deadline_pressure_score",
            "quorum_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "observed_source_count",
            "current_source_count",
            "current_source_family_count",
            "stale_source_count",
            "blocked_source_count",
            "source_family_gap_count",
            "current_source_gap_count",
        ):
            _require_nonnegative_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "source_gap_score",
            "deadline_pressure_score",
            "quorum_urgency_score",
        ):
            _require_ratio_decimal(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_public_surface("row", self)
        _require_digest("row", self)


@dataclass(frozen=True)
class ResearchPacketSourceQuorumUrgencyScoreV2Report:
    generated_at: datetime
    config_version: str
    digest_status: str
    packet_count: Decimal
    pass_packet_count: Decimal
    watch_packet_count: Decimal
    blocked_packet_count: Decimal
    max_source_family_gap_count: Decimal
    max_current_source_gap_count: Decimal
    max_deadline_pressure_score: Decimal
    max_quorum_urgency_score: Decimal
    avg_quorum_urgency_score: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchPacketSourceQuorumUrgencyScoreV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchPacketSourceQuorumUrgencyScoreV2Report)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        for field_name in (
            "packet_count",
            "pass_packet_count",
            "watch_packet_count",
            "blocked_packet_count",
            "max_source_family_gap_count",
            "max_current_source_gap_count",
            "max_deadline_pressure_score",
            "max_quorum_urgency_score",
            "avg_quorum_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_deadline_pressure_score",
            "max_quorum_urgency_score",
            "avg_quorum_urgency_score",
        ):
            _require_ratio_decimal(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_public_surface("report", self)
        _require_digest("report", self)


def build_research_packet_source_quorum_urgency_score_v2(
    observations: Iterable[ResearchPacketSourceQuorumUrgencyScoreV2Observation],
    *,
    config: ResearchPacketSourceQuorumUrgencyScoreV2Config,
    generated_at: datetime,
) -> ResearchPacketSourceQuorumUrgencyScoreV2Report:
    if type(config) is not ResearchPacketSourceQuorumUrgencyScoreV2Config:
        raise ValueError(
            "config must be a ResearchPacketSourceQuorumUrgencyScoreV2Config",
        )
    _require_hard_flags("config", config)
    _reject_public_surface("config", config)
    _require_digest("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    by_packet: dict[str, list[ResearchPacketSourceQuorumUrgencyScoreV2Observation]] = {}
    for item in normalized:
        by_packet.setdefault(item.packet_id, []).append(item)
    rows = tuple(
        sorted(
            (
                _row_from_group(packet_id, tuple(packet_items), config, generated_at)
                for packet_id, packet_items in by_packet.items()
            ),
            key=_row_sort_key,
        ),
    )
    digest_status = _report_status(rows)
    packet_count = _count_decimal(rows)
    return ResearchPacketSourceQuorumUrgencyScoreV2Report(
        generated_at=generated_at,
        config_version=config.config_version,
        digest_status=digest_status,
        packet_count=packet_count,
        pass_packet_count=_count_decimal(row for row in rows if row.digest_status == "pass"),
        watch_packet_count=_count_decimal(
            row for row in rows if row.digest_status == "watch"
        ),
        blocked_packet_count=_count_decimal(
            row for row in rows if row.digest_status == "blocked"
        ),
        max_source_family_gap_count=_max_decimal(
            row.source_family_gap_count for row in rows
        ),
        max_current_source_gap_count=_max_decimal(
            row.current_source_gap_count for row in rows
        ),
        max_deadline_pressure_score=_max_decimal(
            row.deadline_pressure_score for row in rows
        ),
        max_quorum_urgency_score=_max_decimal(
            row.quorum_urgency_score for row in rows
        ),
        avg_quorum_urgency_score=_ratio(
            _sum_decimal(row.quorum_urgency_score for row in rows),
            packet_count,
        ),
        reason_codes=_report_reason_codes(rows, digest_status),
        rows=rows,
    )


def research_packet_source_quorum_urgency_score_v2_payload(
    report: ResearchPacketSourceQuorumUrgencyScoreV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchPacketSourceQuorumUrgencyScoreV2Report:
        _require_hard_flags("report", report)
        _reject_public_surface("report", report)
        _require_digest("report", report)
        for row in report.rows:
            _require_hard_flags("row", row)
            _reject_public_surface("row", row)
            _require_digest("row", row)
        payload = _payload_value(report)
    elif type(report) is dict:
        _reject_public_surface("payload", report)
        payload = _payload_value(report)
    else:
        raise ValueError(
            "report must be a ResearchPacketSourceQuorumUrgencyScoreV2Report",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_public_surface("payload", payload)
    return payload


def _row_from_group(
    packet_id: str,
    observations: tuple[ResearchPacketSourceQuorumUrgencyScoreV2Observation, ...],
    config: ResearchPacketSourceQuorumUrgencyScoreV2Config,
    generated_at: datetime,
) -> ResearchPacketSourceQuorumUrgencyScoreV2Row:
    deadline_at = min(item.deadline_at for item in observations)
    current_items = tuple(
        item for item in observations if _is_current_source(item, config, generated_at)
    )
    stale_count = _count_decimal(
        item
        for item in observations
        if item.observed_at is None
        or (
            item.observed_at <= generated_at
            and _age_seconds(generated_at, item.observed_at) > config.max_source_age_seconds
        )
    )
    blocked_count = _count_decimal(
        item
        for item in observations
        if item.source_blocked or not item.supports_research_packet
    )
    current_source_count = _count_decimal(current_items)
    current_family_count = _decimal_from_int(
        len({item.source_family for item in current_items}),
    )
    family_gap = _positive_gap(
        config.required_source_family_count,
        current_family_count,
    )
    current_gap = _positive_gap(
        config.required_current_source_count,
        current_source_count,
    )
    source_gap_score = max(
        _ratio(family_gap, config.required_source_family_count),
        _ratio(current_gap, config.required_current_source_count),
    )
    seconds_until_deadline = _seconds_between(generated_at, deadline_at)
    deadline_pressure_score = _deadline_pressure_score(
        seconds_until_deadline,
        config,
    )
    score = _quantize(
        source_gap_score * config.source_gap_weight
        + deadline_pressure_score * config.deadline_pressure_weight,
    )
    reason_codes = _row_reason_codes(
        observations,
        family_gap,
        current_gap,
        stale_count,
        blocked_count,
        seconds_until_deadline,
        deadline_pressure_score,
        config,
    )
    return ResearchPacketSourceQuorumUrgencyScoreV2Row(
        packet_id=packet_id,
        deadline_at=deadline_at,
        seconds_until_deadline=seconds_until_deadline,
        observed_source_count=_count_decimal(observations),
        current_source_count=current_source_count,
        current_source_family_count=current_family_count,
        stale_source_count=stale_count,
        blocked_source_count=blocked_count,
        source_family_gap_count=family_gap,
        current_source_gap_count=current_gap,
        source_gap_score=source_gap_score,
        deadline_pressure_score=deadline_pressure_score,
        quorum_urgency_score=score,
        digest_status=_row_status(reason_codes, score, config),
        reason_codes=reason_codes,
    )


def _is_current_source(
    item: ResearchPacketSourceQuorumUrgencyScoreV2Observation,
    config: ResearchPacketSourceQuorumUrgencyScoreV2Config,
    generated_at: datetime,
) -> bool:
    if item.observed_at is None:
        return False
    if item.observed_at > generated_at:
        return False
    if item.source_blocked or not item.supports_research_packet:
        return False
    return _age_seconds(generated_at, item.observed_at) <= config.max_source_age_seconds


def _row_reason_codes(
    observations: tuple[ResearchPacketSourceQuorumUrgencyScoreV2Observation, ...],
    family_gap: Decimal,
    current_gap: Decimal,
    stale_count: Decimal,
    blocked_count: Decimal,
    seconds_until_deadline: Decimal,
    deadline_pressure_score: Decimal,
    config: ResearchPacketSourceQuorumUrgencyScoreV2Config,
) -> tuple[str, ...]:
    codes: list[str] = []
    for item in observations:
        codes.extend(item.reason_codes)
    if family_gap > _ZERO:
        codes.append("family_gap")
    if current_gap > _ZERO:
        codes.append("current_source_gap")
    if stale_count > _ZERO:
        codes.append("stale_source_present")
    if blocked_count > _ZERO:
        codes.append("blocked_source_present")
    if seconds_until_deadline <= config.urgent_deadline_seconds:
        codes.append("deadline_block")
    elif deadline_pressure_score > _ZERO:
        codes.append("deadline_watch")
    return _normalize_reason_codes(tuple(codes))


def _row_status(
    reason_codes: tuple[str, ...],
    score: Decimal,
    config: ResearchPacketSourceQuorumUrgencyScoreV2Config,
) -> str:
    if score >= config.block_score_threshold or "deadline_block" in reason_codes:
        return "blocked"
    if (
        score >= config.watch_score_threshold
        or "family_gap" in reason_codes
        or "current_source_gap" in reason_codes
        or "deadline_watch" in reason_codes
        or "stale_source_present" in reason_codes
        or "blocked_source_present" in reason_codes
    ):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchPacketSourceQuorumUrgencyScoreV2Row, ...]) -> str:
    if not rows:
        return "blocked"
    return min((row.digest_status for row in rows), key=lambda value: _STATUS_WEIGHTS[value])


def _report_reason_codes(
    rows: tuple[ResearchPacketSourceQuorumUrgencyScoreV2Row, ...],
    digest_status: str,
) -> tuple[str, ...]:
    if not rows:
        return (_NO_ITEMS_REASON,)
    codes = [f"research_packet_source_quorum_urgency_{digest_status}"]
    for row in rows:
        for code in row.reason_codes:
            if code != "research_packet_source_observed":
                codes.append(f"{code}_present")
    return _normalize_reason_codes(tuple(codes))


def _row_sort_key(row: ResearchPacketSourceQuorumUrgencyScoreV2Row) -> tuple[int, Decimal, str]:
    return (_STATUS_WEIGHTS[row.digest_status], -row.quorum_urgency_score, row.packet_id)


def _deadline_pressure_score(
    seconds_until_deadline: Decimal,
    config: ResearchPacketSourceQuorumUrgencyScoreV2Config,
) -> Decimal:
    if seconds_until_deadline <= config.urgent_deadline_seconds:
        return _ONE
    if seconds_until_deadline >= config.watch_deadline_seconds:
        return _ZERO
    return _ratio(
        config.watch_deadline_seconds - seconds_until_deadline,
        config.watch_deadline_seconds - config.urgent_deadline_seconds,
    )


def _normalize_observations(
    observations: Iterable[ResearchPacketSourceQuorumUrgencyScoreV2Observation],
) -> tuple[ResearchPacketSourceQuorumUrgencyScoreV2Observation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable of observation objects")
    normalized = tuple(observations)
    for item in normalized:
        if type(item) is not ResearchPacketSourceQuorumUrgencyScoreV2Observation:
            raise ValueError(
                "observations must contain ResearchPacketSourceQuorumUrgencyScoreV2Observation",
            )
        _require_hard_flags("observation", item)
        _reject_public_surface("observation", item)
        _require_digest("observation", item)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchPacketSourceQuorumUrgencyScoreV2Row],
) -> tuple[ResearchPacketSourceQuorumUrgencyScoreV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable of row objects")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchPacketSourceQuorumUrgencyScoreV2Row:
            raise ValueError("rows must contain ResearchPacketSourceQuorumUrgencyScoreV2Row")
        _require_hard_flags("row", row)
        _reject_public_surface("row", row)
        _require_digest("row", row)
    return normalized


def _validate_row(row: ResearchPacketSourceQuorumUrgencyScoreV2Row) -> None:
    if row.current_source_count > row.observed_source_count:
        raise ValueError("current_source_count must not exceed observed_source_count")
    if row.current_source_family_count > row.current_source_count:
        raise ValueError("current_source_family_count must not exceed current_source_count")
    if row.stale_source_count + row.blocked_source_count > row.observed_source_count:
        raise ValueError("inactive source counts must not exceed observed_source_count")


def _validate_report(report: ResearchPacketSourceQuorumUrgencyScoreV2Report) -> None:
    if report.packet_count != _count_decimal(report.rows):
        raise ValueError("packet_count must match rows")
    if (
        report.pass_packet_count
        + report.watch_packet_count
        + report.blocked_packet_count
        != report.packet_count
    ):
        raise ValueError("packet status counts must match packet_count")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status must match rows")


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if type(value) is bool:
        return value
    if value is None:
        return None
    if isinstance(value, float):
        raise ValueError("payload value must not be a float")
    if type(value) is int:
        raise ValueError("payload numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _payload_value(item)
        return ready
    raise ValueError("unsupported payload value")


def _require_digest(label: str, value: object) -> None:
    current = getattr(value, _DIGEST_FIELD, None)
    if type(current) is not str:
        raise ValueError(f"{label} {_DIGEST_FIELD} must be a string")
    expected = _derived_digest(value)
    if current == "":
        object.__setattr__(value, _DIGEST_FIELD, expected)
        return
    if current != expected:
        raise ValueError(f"{label} {_DIGEST_FIELD} mismatch")


def _derived_digest(value: object) -> str:
    payload = _digest_ready(value)
    encoded = repr(payload).encode("utf-8")
    return f"{_DIGEST_PREFIX}:{sha256(encoded).hexdigest()}"


def _digest_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _digest_ready(asdict(value))
    if isinstance(value, Decimal):
        return str(_require_decimal("digest_decimal", value))
    if isinstance(value, datetime):
        return _as_utc("digest_datetime", value).isoformat()
    if isinstance(value, tuple):
        return tuple(_digest_ready(item) for item in value)
    if isinstance(value, list):
        return tuple(_digest_ready(item) for item in value)
    if isinstance(value, dict):
        return tuple(
            (key, _digest_ready(item))
            for key, item in sorted(value.items())
            if key != _DIGEST_FIELD
        )
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("value is not digest ready")


def _reject_public_surface(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_public_surface(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_bad_text(value):
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if isinstance(value, Decimal):
        _require_decimal(path or label, value)
        return
    if isinstance(value, datetime):
        _as_utc(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("payload value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal numeric values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if _has_bad_text(key):
                raise ValueError(f"unsafe public field in {label}")
            nested_path = key if not path else f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_public_surface(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_public_surface(label, item, nested_path)
        return
    raise ValueError("unsupported payload value")


def _has_bad_text(value: str) -> bool:
    lowered = value.lower()
    tokens = _text_tokens(lowered)
    return any(lowered == part or any(token == part for token in tokens) for part in _BAD_PARTS)


def _text_tokens(value: str) -> tuple[str, ...]:
    tokens: list[str] = []
    token: list[str] = []
    for char in value:
        if "a" <= char <= "z" or "0" <= char <= "9":
            token.append(char)
        elif token:
            tokens.append("".join(token))
            token = []
    if token:
        tokens.append("".join(token))
    return tuple(tokens)


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


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_exact_type(label: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    if _has_bad_text(value):
        raise ValueError(f"{field_name} has unsafe public value")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, tuple):
        raise ValueError("reason_codes must be a tuple")
    codes: list[str] = []
    for item in value:
        _require_public_string("reason_code", item)
        if item in codes:
            continue
        codes.append(item)
    return tuple(sorted(codes))


def _require_status(field_name: str, value: object) -> None:
    if value not in _STATUSES:
        raise ValueError(f"{field_name} must be blocked, watch, or pass")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    total = (end - start).total_seconds()
    return _quantize(Decimal(str(int(total))))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    return _seconds_between(observed_at, generated_at)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_positive_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _positive_gap(required: Decimal, observed: Decimal) -> Decimal:
    if observed >= required:
        return _ZERO
    return _quantize(required - observed)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = _ZERO
    for value in values:
        total += value
    return _quantize(total)


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    seen = tuple(values)
    if not seen:
        return _ZERO
    return max(seen)


def _count_decimal(values: Iterable[object]) -> Decimal:
    return _decimal_from_int(sum(1 for _ in values))


def _decimal_from_int(value: int) -> Decimal:
    return _quantize(Decimal(str(value)))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)
