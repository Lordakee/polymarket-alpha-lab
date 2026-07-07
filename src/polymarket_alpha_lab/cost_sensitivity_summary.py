"""Paper-only aggregate summary for cost sensitivity reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
import hashlib

from polymarket_alpha_lab.cost_sensitivity import PaperCostSensitivityReport


QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0")
ONE = Decimal("1")
SUMMARY_STATUSES = (
    "empty_cost_sensitivity_summary",
    "pass",
    "watch",
    "blocked",
)
VALIDATION_DIGEST_PREFIX = "pcs-summary-v1:"
UNSAFE_PUBLIC_TEXT_FRAGMENTS = frozenset(
    "".join(parts)
    for parts in (
        ("au", "th"),
        ("wal", "let"),
        ("acc", "ount"),
        ("or", "der"),
        ("li", "ve"),
        ("market", "_", "slug"),
        ("ques", "tion"),
        ("pri", "vate", "_", "key"),
        ("api", "_", "key"),
        ("sec", "ret"),
        ("to", "ken"),
        ("bro", "ker"),
        ("exec", "ute"),
        ("conn", "ect"),
        ("requ", "est"),
        ("http",),
    )
)


@dataclass(frozen=True)
class PaperCostSensitivitySummaryConfig:
    config_version: str
    taker_fee_rate: Decimal = Decimal("0.02")

    def __post_init__(self) -> None:
        if type(self) is not PaperCostSensitivitySummaryConfig:
            raise ValueError("config must be a PaperCostSensitivitySummaryConfig")
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "taker_fee_rate",
            _normalize_probability_decimal("taker_fee_rate", self.taker_fee_rate),
        )


@dataclass(frozen=True)
class PaperCostSensitivitySummaryReport:
    generated_at: datetime
    config_version: str
    source_report_count: Decimal
    source_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    pass_ratio: Decimal | None
    watch_ratio: Decimal | None
    blocked_ratio: Decimal | None
    mean_base_net_edge_per_share: Decimal | None
    mean_cost_shock_per_share: Decimal | None
    mean_stressed_net_edge_per_share: Decimal | None
    worst_stressed_net_edge_per_share: Decimal | None
    taker_fee_rate: Decimal
    status: str
    reason_codes: tuple[str, ...]
    validation_digest: str = field(default="", init=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not PaperCostSensitivitySummaryReport:
            raise ValueError("report must be a PaperCostSensitivitySummaryReport")
        if type(self.generated_at) is not datetime:
            raise ValueError("generated_at must be a datetime")
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_report_count",
            "source_row_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("pass_ratio", "watch_ratio", "blocked_ratio"):
            _require_optional_probability_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "mean_base_net_edge_per_share",
            "mean_cost_shock_per_share",
            "mean_stressed_net_edge_per_share",
            "worst_stressed_net_edge_per_share",
        ):
            _require_optional_decimal(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "taker_fee_rate",
            _normalize_probability_decimal("taker_fee_rate", self.taker_fee_rate),
        )
        if self.status not in SUMMARY_STATUSES:
            raise ValueError("status must be a known cost sensitivity summary status")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_report_consistency(self)
        if self.paper_only is not True:
            raise ValueError("paper_only must be True")
        if self.report_only is not True:
            raise ValueError("report_only must be True")
        if self.readonly is not True:
            raise ValueError("readonly must be True")
        object.__setattr__(self, "validation_digest", _report_validation_digest(self))
        _require_report_validation_digest(self)


def build_paper_cost_sensitivity_summary_report(
    reports: object,
    *,
    config: PaperCostSensitivitySummaryConfig,
    generated_at: datetime,
) -> PaperCostSensitivitySummaryReport:
    if type(config) is not PaperCostSensitivitySummaryConfig:
        raise ValueError("config must be a PaperCostSensitivitySummaryConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    normalized_reports = _normalize_reports(reports)
    rows = tuple(row for report in normalized_reports for row in report.rows)
    total = _count(len(rows))
    pass_count = _row_count(rows, "pass")
    watch_count = _row_count(rows, "watch")
    blocked_count = _row_count(rows, "blocked")
    base_edges = tuple(
        row.base_net_edge_per_share
        for row in rows
        if row.base_net_edge_per_share is not None
    )
    shocks = tuple(row.cost_shock_per_share for row in rows)
    stressed_edges = tuple(
        row.stressed_net_edge_per_share
        for row in rows
        if row.stressed_net_edge_per_share is not None
    )

    return PaperCostSensitivitySummaryReport(
        generated_at=generated_at,
        config_version=config.config_version,
        source_report_count=_count(len(normalized_reports)),
        source_row_count=total,
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        pass_ratio=_ratio(pass_count, total),
        watch_ratio=_ratio(watch_count, total),
        blocked_ratio=_ratio(blocked_count, total),
        mean_base_net_edge_per_share=_mean(base_edges),
        mean_cost_shock_per_share=_mean(shocks),
        mean_stressed_net_edge_per_share=_mean(stressed_edges),
        worst_stressed_net_edge_per_share=min(stressed_edges) if stressed_edges else None,
        taker_fee_rate=config.taker_fee_rate,
        status=_summary_status(total, watch_count=watch_count, blocked_count=blocked_count),
        reason_codes=_summary_reason_codes(
            total,
            watch_count=watch_count,
            blocked_count=blocked_count,
        ),
    )


def paper_cost_sensitivity_summary_payload(
    report: PaperCostSensitivitySummaryReport | dict[str, object],
) -> dict[str, object]:
    if type(report) is PaperCostSensitivitySummaryReport:
        _require_paper_flags("report", report)
        _require_report_validation_digest(report)
        _validate_report_consistency(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a PaperCostSensitivitySummaryReport")
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_paper_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _normalize_reports(reports: object) -> tuple[PaperCostSensitivityReport, ...]:
    if isinstance(reports, (str, bytes)):
        raise ValueError("reports must be an iterable of PaperCostSensitivityReport values")
    try:
        normalized = tuple(reports)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(
            "reports must be an iterable of PaperCostSensitivityReport values",
        ) from exc
    for report in normalized:
        if type(report) is not PaperCostSensitivityReport:
            raise ValueError("reports must contain PaperCostSensitivityReport values")
        if report.paper_only is not True:
            raise ValueError("reports must contain paper_only values")
        if report.report_only is not True:
            raise ValueError("reports must contain report_only values")
        if report.readonly is not True:
            raise ValueError("reports must contain readonly values")
    return normalized


def _row_count(rows: tuple[object, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if getattr(row, "status") == status))


def _summary_status(
    total: Decimal,
    *,
    watch_count: Decimal,
    blocked_count: Decimal,
) -> str:
    if total == ZERO:
        return "empty_cost_sensitivity_summary"
    if blocked_count > ZERO:
        return "blocked"
    if watch_count > ZERO:
        return "watch"
    return "pass"


def _summary_reason_codes(
    total: Decimal,
    *,
    watch_count: Decimal,
    blocked_count: Decimal,
) -> tuple[str, ...]:
    if total == ZERO:
        return ("cost_sensitivity_summary_empty",)
    if blocked_count > ZERO:
        return ("cost_sensitivity_blocked_rows",)
    if watch_count > ZERO:
        return ("cost_sensitivity_watch_rows",)
    return ("cost_sensitivity_pass_rows",)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator == ZERO:
        return None
    return _quantize(numerator / denominator)


def _mean(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _validate_report_consistency(report: PaperCostSensitivitySummaryReport) -> None:
    if report.pass_count + report.watch_count + report.blocked_count != report.source_row_count:
        raise ValueError("source_row_count must match status counts")
    expected_status = _summary_status(
        report.source_row_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
    )
    if report.status != expected_status:
        raise ValueError("status must match summary counts")
    expected_reason_codes = _summary_reason_codes(
        report.source_row_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
    )
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match summary status")
    if report.source_row_count == ZERO:
        for field_name in (
            "pass_ratio",
            "watch_ratio",
            "blocked_ratio",
            "mean_base_net_edge_per_share",
            "mean_cost_shock_per_share",
            "mean_stressed_net_edge_per_share",
            "worst_stressed_net_edge_per_share",
        ):
            if getattr(report, field_name) is not None:
                raise ValueError(f"{field_name} must be None for empty summaries")
        return
    if report.pass_ratio != _ratio(report.pass_count, report.source_row_count):
        raise ValueError("pass_ratio must match status counts")
    if report.watch_ratio != _ratio(report.watch_count, report.source_row_count):
        raise ValueError("watch_ratio must match status counts")
    if report.blocked_ratio != _ratio(report.blocked_count, report.source_row_count):
        raise ValueError("blocked_ratio must match status counts")


def _report_validation_digest(report: PaperCostSensitivitySummaryReport) -> str:
    return _validation_digest(
        (
            report.generated_at,
            report.config_version,
            report.source_report_count,
            report.source_row_count,
            report.pass_count,
            report.watch_count,
            report.blocked_count,
            report.pass_ratio,
            report.watch_ratio,
            report.blocked_ratio,
            report.mean_base_net_edge_per_share,
            report.mean_cost_shock_per_share,
            report.mean_stressed_net_edge_per_share,
            report.worst_stressed_net_edge_per_share,
            report.taker_fee_rate,
            report.status,
            report.reason_codes,
            report.paper_only,
            report.report_only,
            report.readonly,
        ),
    )


def _require_report_validation_digest(report: PaperCostSensitivitySummaryReport) -> None:
    if report.validation_digest != _report_validation_digest(report):
        raise ValueError("validation_digest mismatch: report may be tampered")


def _validation_digest(parts: tuple[object, ...]) -> str:
    material = "\n".join(_digest_part(part) for part in parts)
    return VALIDATION_DIGEST_PREFIX + hashlib.sha256(material.encode("utf-8")).hexdigest()


def _digest_part(value: object) -> str:
    if value is None:
        return "none:"
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("validation_digest values must be finite")
        return f"decimal:{value}"
    if type(value) is datetime:
        return f"datetime:{_as_utc(value).isoformat()}"
    if type(value) is str:
        return f"str:{len(value)}:{value}"
    if type(value) is bool:
        if value:
            return "bool:true"
        return "bool:false"
    if type(value) is tuple:
        return "tuple:[" + ",".join(_digest_part(item) for item in value) + "]"
    raise ValueError("validation_digest values must be canonical")


def _json_ready(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        if not _is_allowed_public_dataclass(value):
            raise ValueError("unsafe payload object must use plain values")
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return _as_utc(value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict) and type(value) is not dict:
        raise ValueError("unsafe payload object must use plain dict values")
    if type(value) is dict:
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)) and type(value) not in (list, tuple):
        raise ValueError("unsafe payload object must use plain sequence values")
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    if type(value) in (str, bool):
        return value
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if not _is_allowed_public_dataclass(value):
            raise ValueError("unsafe payload object must use plain values")
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{label} must be finite")
        return
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{label} must be timezone-aware")
        _as_utc(value)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{label} must use Decimal numeric values")
    if isinstance(value, dict) and type(value) is not dict:
        raise ValueError("unsafe payload object must use plain dict values")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_public_text(label, key)
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{key} must be True")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)) and type(value) not in (list, tuple):
        raise ValueError("unsafe payload object must use plain sequence values")
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    raise ValueError("value is not JSON serializable")


def _is_allowed_public_dataclass(value: object) -> bool:
    return type(value) in (
        PaperCostSensitivitySummaryConfig,
        PaperCostSensitivitySummaryReport,
    )


def _reject_unsafe_public_text(label: str, value: str) -> None:
    if _has_unsafe_public_text(value):
        raise ValueError(f"unsafe public value in {label}")


def _has_unsafe_public_text(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_TEXT_FRAGMENTS)


def _require_paper_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        reason_codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_canonical_string("reason_codes", reason_code)
    return reason_codes


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    _require_probability_decimal(field_name, value)
    return _quantize(value)


def _require_optional_probability_decimal(field_name: str, value: object) -> None:
    if value is not None:
        _require_probability_decimal(field_name, value)


def _require_probability_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _require_optional_decimal(field_name: str, value: object) -> None:
    if value is not None:
        _require_decimal(field_name, value)


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(COUNT_QUANTUM)
    if normalized != value:
        raise ValueError(f"{field_name} must be integral")
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


__all__ = (
    "PaperCostSensitivitySummaryConfig",
    "PaperCostSensitivitySummaryReport",
    "build_paper_cost_sensitivity_summary_report",
    "paper_cost_sensitivity_summary_payload",
)
