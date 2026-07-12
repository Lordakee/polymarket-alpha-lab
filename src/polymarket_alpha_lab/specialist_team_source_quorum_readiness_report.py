"""Pure public-safe report-only specialist team source quorum reducer."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_SPECIALIST_TEAM_SOURCE_QUORUM_READINESS_REPORT_CONFIG_VERSION = (
    "specialist-team-source-quorum-readiness-report-v1"
)
SPECIALIST_TEAM_SOURCE_QUORUM_STATUSES = ("ready", "watch", "blocked")
SPECIALIST_TEAM_SOURCE_QUORUM_CONTRADICTION_STATUSES = ("none", "minor", "major")
SPECIALIST_TEAM_SOURCE_QUORUM_CATEGORIES = (
    "politics",
    "crypto",
    "equities",
    "gold",
    "soccer",
    "basketball",
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

_PUBLIC_CODE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
_DIGEST_LENGTH = 64
_UNSAFE_TEXT_FRAGMENTS = (
    "://",
    "@",
    "secret",
    "password",
    "passwd",
    "api_key",
    "apikey",
    "private_key",
    "access_token",
    "bearer ",
    "au" + "th",
    "wal" + "let",
    "ord" + "er",
    "tra" + "de",
    "live",
    "exec" + "ution",
    "event_" + "id",
    "market_" + "id",
    "market_" + "slug",
    "source_" + "id",
    "source_" + "url",
    "source_" + "name",
    "source_" + "text",
    "raw_" + "source",
    "data" + "base",
    "net" + "work",
    "req" + "uests",
    "url" + "lib",
    "sock" + "et",
    "sql" + "ite",
    "reco" + "mmend",
    "siz" + "ing",
)
_CATEGORY_INDEX = {
    category: index for index, category in enumerate(SPECIALIST_TEAM_SOURCE_QUORUM_CATEGORIES)
}


@dataclass(frozen=True)
class SpecialistTeamSourceQuorumReadinessConfig:
    config_version: str = (
        DEFAULT_SPECIALIST_TEAM_SOURCE_QUORUM_READINESS_REPORT_CONFIG_VERSION
    )
    required_source_family_count: Decimal = Decimal("3.000000")
    required_specialist_ack_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamSourceQuorumReadinessConfig, "config")
        _require_config_version(self.config_version)
        object.__setattr__(
            self,
            "required_source_family_count",
            _normalize_integer_decimal(
                "required_source_family_count",
                self.required_source_family_count,
            ),
        )
        object.__setattr__(
            self,
            "required_specialist_ack_count",
            _normalize_integer_decimal(
                "required_specialist_ack_count",
                self.required_specialist_ack_count,
            ),
        )
        if self.required_source_family_count <= ZERO:
            raise ValueError("required_source_family_count must be positive")
        if self.required_specialist_ack_count <= ZERO:
            raise ValueError("required_specialist_ack_count must be positive")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class SpecialistTeamSourceQuorumSignal:
    team_id: str
    category: str
    source_family_count: Decimal
    official_anchor_present: bool
    contradiction_status: str
    specialist_ack_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamSourceQuorumSignal, "signal")
        _require_public_code("team_id", self.team_id)
        _require_category(self.category)
        object.__setattr__(
            self,
            "source_family_count",
            _normalize_integer_decimal("source_family_count", self.source_family_count),
        )
        if type(self.official_anchor_present) is not bool:
            raise ValueError("official_anchor_present must be a bool")
        _require_contradiction_status("contradiction_status", self.contradiction_status)
        object.__setattr__(
            self,
            "specialist_ack_count",
            _normalize_integer_decimal("specialist_ack_count", self.specialist_ack_count),
        )
        _require_hard_flags("signal", self)


@dataclass(frozen=True)
class SpecialistTeamSourceQuorumReadinessRow:
    team_id: str
    category: str
    source_family_count: Decimal
    official_anchor_present: bool
    contradiction_status: str
    specialist_ack_count: Decimal
    quorum_status: str
    missing_source_families: Decimal
    manual_follow_up: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamSourceQuorumReadinessRow, "row")
        _require_public_code("team_id", self.team_id)
        _require_category(self.category)
        object.__setattr__(
            self,
            "source_family_count",
            _normalize_integer_decimal("source_family_count", self.source_family_count),
        )
        if type(self.official_anchor_present) is not bool:
            raise ValueError("official_anchor_present must be a bool")
        _require_contradiction_status("contradiction_status", self.contradiction_status)
        object.__setattr__(
            self,
            "specialist_ack_count",
            _normalize_integer_decimal("specialist_ack_count", self.specialist_ack_count),
        )
        _require_quorum_status("quorum_status", self.quorum_status)
        object.__setattr__(
            self,
            "missing_source_families",
            _normalize_integer_decimal(
                "missing_source_families",
                self.missing_source_families,
            ),
        )
        if type(self.manual_follow_up) is not bool:
            raise ValueError("manual_follow_up must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class SpecialistTeamSourceQuorumReadinessReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            SpecialistTeamSourceQuorumReadinessReasonCodeCount,
            "reason_code_count",
        )
        _require_public_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_integer_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class SpecialistTeamSourceQuorumReadinessReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    team_count: Decimal
    category_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    manual_follow_up_count: Decimal
    total_missing_source_families: Decimal
    total_specialist_ack_count: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[SpecialistTeamSourceQuorumReadinessReasonCodeCount, ...]
    rows: tuple[SpecialistTeamSourceQuorumReadinessRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamSourceQuorumReadinessReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_config_version(self.config_version)
        for field_name in (
            "row_count",
            "team_count",
            "category_count",
            "ready_count",
            "watch_count",
            "blocked_count",
            "manual_follow_up_count",
            "total_missing_source_families",
            "total_specialist_ack_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_integer_decimal(field_name, getattr(self, field_name)),
            )
        _require_quorum_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)

    @property
    def payload(self) -> dict[str, Any]:
        return specialist_team_source_quorum_readiness_report_payload(self)


def build_specialist_team_source_quorum_readiness_report(
    signals: object,
    *,
    config: SpecialistTeamSourceQuorumReadinessConfig,
    generated_at: datetime,
) -> SpecialistTeamSourceQuorumReadinessReport:
    if type(config) is not SpecialistTeamSourceQuorumReadinessConfig:
        raise ValueError("config must be a SpecialistTeamSourceQuorumReadinessConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    _validate_unique_signals(normalized_signals)
    rows = tuple(
        sorted(
            (
                _row_for_signal(signal, config=config)
                for signal in normalized_signals
            ),
            key=_row_key,
        ),
    )
    report_reason_codes = _report_reason_codes(rows)
    return SpecialistTeamSourceQuorumReadinessReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        row_count=_count(len(rows)),
        team_count=_count(len({row.team_id for row in rows})),
        category_count=_count(len({row.category for row in rows})),
        ready_count=_status_count(rows, "ready"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        manual_follow_up_count=_count(sum(1 for row in rows if row.manual_follow_up)),
        total_missing_source_families=_sum_counts(
            tuple(row.missing_source_families for row in rows),
        ),
        total_specialist_ack_count=_sum_counts(
            tuple(row.specialist_ack_count for row in rows),
        ),
        report_status=_report_status(rows),
        reason_codes=report_reason_codes,
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def specialist_team_source_quorum_readiness_report_payload(
    report: SpecialistTeamSourceQuorumReadinessReport,
) -> dict[str, Any]:
    if type(report) is not SpecialistTeamSourceQuorumReadinessReport:
        raise ValueError("report must be a SpecialistTeamSourceQuorumReadinessReport")
    _validate_report(report)
    payload = _report_public_payload_for_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    validate_specialist_team_source_quorum_readiness_report_payload(payload)
    return payload


def validate_specialist_team_source_quorum_readiness_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload("payload", payload)
    _reject_public_numeric_values(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match payload")
    return True


def _row_for_signal(
    signal: SpecialistTeamSourceQuorumSignal,
    *,
    config: SpecialistTeamSourceQuorumReadinessConfig,
) -> SpecialistTeamSourceQuorumReadinessRow:
    missing_source_families = _missing_count(
        required=config.required_source_family_count,
        actual=signal.source_family_count,
    )
    ack_gap = _missing_count(
        required=config.required_specialist_ack_count,
        actual=signal.specialist_ack_count,
    )
    quorum_status = _quorum_status(
        missing_source_families=missing_source_families,
        official_anchor_present=signal.official_anchor_present,
        contradiction_status=signal.contradiction_status,
        ack_gap=ack_gap,
    )
    manual_follow_up = quorum_status != "ready"
    return SpecialistTeamSourceQuorumReadinessRow(
        team_id=signal.team_id,
        category=signal.category,
        source_family_count=signal.source_family_count,
        official_anchor_present=signal.official_anchor_present,
        contradiction_status=signal.contradiction_status,
        specialist_ack_count=signal.specialist_ack_count,
        quorum_status=quorum_status,
        missing_source_families=missing_source_families,
        manual_follow_up=manual_follow_up,
        reason_codes=_row_reason_codes(
            quorum_status=quorum_status,
            missing_source_families=missing_source_families,
            official_anchor_present=signal.official_anchor_present,
            contradiction_status=signal.contradiction_status,
            ack_gap=ack_gap,
        ),
    )


def _missing_count(*, required: Decimal, actual: Decimal) -> Decimal:
    if actual >= required:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(required - actual)


def _quorum_status(
    *,
    missing_source_families: Decimal,
    official_anchor_present: bool,
    contradiction_status: str,
    ack_gap: Decimal,
) -> str:
    if contradiction_status == "major" or not official_anchor_present:
        return "blocked"
    if missing_source_families > Decimal("1.000000"):
        return "blocked"
    if ack_gap > Decimal("1.000000"):
        return "blocked"
    if missing_source_families > ZERO or ack_gap > ZERO or contradiction_status == "minor":
        return "watch"
    return "ready"


def _row_reason_codes(
    *,
    quorum_status: str,
    missing_source_families: Decimal,
    official_anchor_present: bool,
    contradiction_status: str,
    ack_gap: Decimal,
) -> tuple[str, ...]:
    reason_codes = [f"source_quorum_{quorum_status}"]
    if missing_source_families > ZERO:
        reason_codes.append("source_family_gap")
    if not official_anchor_present:
        reason_codes.append("official_anchor_missing")
    if ack_gap > ZERO:
        reason_codes.append("specialist_ack_gap")
    if contradiction_status == "minor":
        reason_codes.append("minor_contradiction")
    if contradiction_status == "major":
        reason_codes.append("major_contradiction")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[SpecialistTeamSourceQuorumReadinessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("source_quorum_empty",)
    report_status = _report_status(rows)
    reason_codes = [f"source_quorum_report_{report_status}"]
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code not in reason_codes:
                reason_codes.append(reason_code)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_status(rows: tuple[SpecialistTeamSourceQuorumReadinessRow, ...]) -> str:
    if any(row.quorum_status == "blocked" for row in rows):
        return "blocked"
    if any(row.quorum_status == "watch" for row in rows):
        return "watch"
    return "ready"


def _reason_code_counts(
    rows: tuple[SpecialistTeamSourceQuorumReadinessRow, ...],
) -> tuple[SpecialistTeamSourceQuorumReadinessReasonCodeCount, ...]:
    reason_codes = sorted({reason_code for row in rows for reason_code in row.reason_codes})
    return tuple(
        SpecialistTeamSourceQuorumReadinessReasonCodeCount(
            reason_code=reason_code,
            count=_count(sum(1 for row in rows if reason_code in row.reason_codes)),
        )
        for reason_code in reason_codes
    )


def _normalize_signals(value: object) -> tuple[SpecialistTeamSourceQuorumSignal, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("signals must be an iterable")
    try:
        signals = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("signals must be an iterable") from exc
    for item in signals:
        if type(item) is not SpecialistTeamSourceQuorumSignal:
            raise ValueError("signals must contain SpecialistTeamSourceQuorumSignal values")
        _require_hard_flags("signal", item)
    return signals


def _normalize_rows(
    value: object,
) -> tuple[SpecialistTeamSourceQuorumReadinessRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not SpecialistTeamSourceQuorumReadinessRow:
            raise ValueError("rows must contain SpecialistTeamSourceQuorumReadinessRow values")
        _require_hard_flags("row", row)
    normalized = tuple(sorted(rows, key=_row_key))
    if rows != normalized:
        raise ValueError("rows must use deterministic sequence")
    _validate_unique_rows(rows)
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[SpecialistTeamSourceQuorumReadinessReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for count in counts:
        if type(count) is not SpecialistTeamSourceQuorumReadinessReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "SpecialistTeamSourceQuorumReadinessReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
        if count.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(count.reason_code)
    normalized = tuple(sorted(counts, key=lambda item: item.reason_code))
    if counts != normalized:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return counts


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_public_code(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    return reason_codes


def _validate_unique_signals(
    signals: tuple[SpecialistTeamSourceQuorumSignal, ...],
) -> None:
    seen: set[tuple[str, str]] = set()
    for signal in signals:
        key = (signal.category, signal.team_id)
        if key in seen:
            raise ValueError("signals must be unique by team and category")
        seen.add(key)


def _validate_unique_rows(
    rows: tuple[SpecialistTeamSourceQuorumReadinessRow, ...],
) -> None:
    seen: set[tuple[int, str]] = set()
    for row in rows:
        key = _row_key(row)
        if key in seen:
            raise ValueError("rows must be unique by team and category")
        seen.add(key)


def _validate_report(report: SpecialistTeamSourceQuorumReadinessReport) -> None:
    _require_hard_flags("report", report)
    _validate_unique_rows(report.rows)
    if report.row_count != _count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.team_count != _count(len({row.team_id for row in report.rows})):
        raise ValueError("team_count must match rows")
    if report.category_count != _count(len({row.category for row in report.rows})):
        raise ValueError("category_count must match rows")
    if report.ready_count != _status_count(report.rows, "ready"):
        raise ValueError("ready_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if report.manual_follow_up_count != _count(
        sum(1 for row in report.rows if row.manual_follow_up),
    ):
        raise ValueError("manual_follow_up_count must match rows")
    if report.total_missing_source_families != _sum_counts(
        tuple(row.missing_source_families for row in report.rows),
    ):
        raise ValueError("total_missing_source_families must match rows")
    if report.total_specialist_ack_count != _sum_counts(
        tuple(row.specialist_ack_count for row in report.rows),
    ):
        raise ValueError("total_specialist_ack_count must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report")


def _row_key(row: SpecialistTeamSourceQuorumReadinessRow) -> tuple[int, str]:
    return (_CATEGORY_INDEX[row.category], row.team_id)


def _status_count(
    rows: tuple[SpecialistTeamSourceQuorumReadinessRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.quorum_status == status))


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _sum_counts(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_integer_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be {expected_type.__name__}")


def _require_config_version(value: object) -> None:
    if type(value) is not str:
        raise ValueError("config_version must be a string")
    if value != DEFAULT_SPECIALIST_TEAM_SOURCE_QUORUM_READINESS_REPORT_CONFIG_VERSION:
        raise ValueError("config_version is not supported")


def _require_category(value: object) -> None:
    if type(value) is not str or value not in SPECIALIST_TEAM_SOURCE_QUORUM_CATEGORIES:
        raise ValueError("category must be supported")


def _require_public_code(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a public code")
    if not value:
        raise ValueError(f"{field_name} must be a public code")
    if any(fragment in value.lower() for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} must be a public code")
    if any(character not in _PUBLIC_CODE_CHARS for character in value):
        raise ValueError(f"{field_name} must be a public code")


def _require_contradiction_status(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in SPECIALIST_TEAM_SOURCE_QUORUM_CONTRADICTION_STATUSES
    ):
        raise ValueError(f"{field_name} must be supported")


def _require_quorum_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SPECIALIST_TEAM_SOURCE_QUORUM_STATUSES:
        raise ValueError(f"{field_name} must be supported")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    if payload.get("paper_only") is not True:
        raise ValueError("payload must be paper_only")
    if payload.get("report_only") is not True:
        raise ValueError("payload must be report_only")
    if payload.get("readonly") is not True:
        raise ValueError("payload must be readonly")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if len(value) != _DIGEST_LENGTH:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _report_public_payload_for_digest(
    report: SpecialistTeamSourceQuorumReadinessReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _report_derived_validation_digest(
    report: SpecialistTeamSourceQuorumReadinessReport,
) -> str:
    return _public_payload_derived_validation_digest(_report_public_payload_for_digest(report))


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        return _as_utc("datetime", value).isoformat()
    if type(value) is bool or value is None:
        return value
    if type(value) is str:
        return value
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    if isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe public payload text")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            lowered_key = key.lower()
            if any(fragment in lowered_key for fragment in _UNSAFE_TEXT_FRAGMENTS):
                raise ValueError(f"{label} contains unsafe public payload field")
            _reject_unsafe_public_payload(key, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)


__all__ = (
    "DEFAULT_SPECIALIST_TEAM_SOURCE_QUORUM_READINESS_REPORT_CONFIG_VERSION",
    "SPECIALIST_TEAM_SOURCE_QUORUM_CATEGORIES",
    "SPECIALIST_TEAM_SOURCE_QUORUM_CONTRADICTION_STATUSES",
    "SPECIALIST_TEAM_SOURCE_QUORUM_STATUSES",
    "SpecialistTeamSourceQuorumReadinessConfig",
    "SpecialistTeamSourceQuorumReadinessReasonCodeCount",
    "SpecialistTeamSourceQuorumReadinessReport",
    "SpecialistTeamSourceQuorumReadinessRow",
    "SpecialistTeamSourceQuorumSignal",
    "build_specialist_team_source_quorum_readiness_report",
    "specialist_team_source_quorum_readiness_report_payload",
    "validate_specialist_team_source_quorum_readiness_report_payload",
)
