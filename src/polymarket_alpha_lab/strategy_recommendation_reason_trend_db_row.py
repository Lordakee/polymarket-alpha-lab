"""Pure row codec for persisted strategy recommendation reason trend reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from typing import Any

from polymarket_alpha_lab.json_recovery import from_jsonable
from polymarket_alpha_lab.strategy_recommendation_reason_trend import (
    PaperStrategyRecommendationReasonTrendReport,
)


__all__ = (
    "PaperStrategyRecommendationReasonTrendDbRow",
    "from_db_row",
    "strategy_recommendation_reason_trend_from_db_row",
    "strategy_recommendation_reason_trend_report_from_db_row",
    "strategy_recommendation_reason_trend_report_to_db_row",
    "strategy_recommendation_reason_trend_to_db_row",
    "to_db_row",
)


ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
STATUSES = ("stable", "watch", "blocked")
_SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True)
class PaperStrategyRecommendationReasonTrendDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    status: str
    source_report_count: int
    first_generated_at: datetime | None
    latest_generated_at: datetime | None
    latest_primary_reason_code_counts_json: dict[str, int]
    total_primary_reason_code_counts_json: dict[str, int]
    top_new_reason_codes_json: dict[str, int]
    persistent_reason_codes_json: list[str]
    latest_reason_code_count: int
    latest_no_reason_code_count: int
    latest_blocked_reason_count: int
    latest_no_reason_code_share: Decimal | None
    latest_blocked_reason_share: Decimal | None
    max_blocked_reason_share: Decimal
    max_no_reason_code_share: Decimal
    top_reason_code_limit: int
    blocked_reason_codes_json: list[str]
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_sha256("report_sha256", self.report_sha256)
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        _require_status("status", self.status)
        _require_nonnegative_int("source_report_count", self.source_report_count)
        object.__setattr__(
            self,
            "first_generated_at",
            _as_optional_utc("first_generated_at", self.first_generated_at),
        )
        object.__setattr__(
            self,
            "latest_generated_at",
            _as_optional_utc("latest_generated_at", self.latest_generated_at),
        )
        object.__setattr__(
            self,
            "latest_primary_reason_code_counts_json",
            _normalize_reason_code_counts_json(
                "latest_primary_reason_code_counts_json",
                self.latest_primary_reason_code_counts_json,
            ),
        )
        object.__setattr__(
            self,
            "total_primary_reason_code_counts_json",
            _normalize_reason_code_counts_json(
                "total_primary_reason_code_counts_json",
                self.total_primary_reason_code_counts_json,
            ),
        )
        object.__setattr__(
            self,
            "top_new_reason_codes_json",
            _normalize_reason_code_counts_json(
                "top_new_reason_codes_json",
                self.top_new_reason_codes_json,
            ),
        )
        object.__setattr__(
            self,
            "persistent_reason_codes_json",
            _normalize_reason_code_list(
                "persistent_reason_codes_json",
                self.persistent_reason_codes_json,
            ),
        )
        for field_name in (
            "latest_reason_code_count",
            "latest_no_reason_code_count",
            "latest_blocked_reason_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "latest_no_reason_code_share",
            _normalize_optional_ratio(
                "latest_no_reason_code_share",
                self.latest_no_reason_code_share,
            ),
        )
        object.__setattr__(
            self,
            "latest_blocked_reason_share",
            _normalize_optional_ratio(
                "latest_blocked_reason_share",
                self.latest_blocked_reason_share,
            ),
        )
        object.__setattr__(
            self,
            "max_blocked_reason_share",
            _normalize_ratio("max_blocked_reason_share", self.max_blocked_reason_share),
        )
        object.__setattr__(
            self,
            "max_no_reason_code_share",
            _normalize_ratio("max_no_reason_code_share", self.max_no_reason_code_share),
        )
        _require_positive_int("top_reason_code_limit", self.top_reason_code_limit)
        object.__setattr__(
            self,
            "blocked_reason_codes_json",
            _normalize_reason_code_list(
                "blocked_reason_codes_json",
                self.blocked_reason_codes_json,
            ),
        )
        object.__setattr__(
            self,
            "payload_json",
            _normalize_json_object("payload_json", self.payload_json),
        )
        _require_hard_flags("DB row", self)


def strategy_recommendation_reason_trend_to_db_row(
    report: PaperStrategyRecommendationReasonTrendReport,
) -> PaperStrategyRecommendationReasonTrendDbRow:
    if type(report) is not PaperStrategyRecommendationReasonTrendReport:
        raise ValueError(
            "report must be a PaperStrategyRecommendationReasonTrendReport",
        )
    _validate_report_tree(report)
    payload_json = _json_ready(asdict(report))
    return PaperStrategyRecommendationReasonTrendDbRow(
        report_sha256=_report_sha256(payload_json),
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        source_report_count=report.source_report_count,
        first_generated_at=report.first_generated_at,
        latest_generated_at=report.latest_generated_at,
        latest_primary_reason_code_counts_json=_counts_to_json(
            report.latest_primary_reason_code_counts,
        ),
        total_primary_reason_code_counts_json=_counts_to_json(
            report.total_primary_reason_code_counts,
        ),
        top_new_reason_codes_json=_counts_to_json(report.top_new_reason_codes),
        persistent_reason_codes_json=list(report.persistent_reason_codes),
        latest_reason_code_count=report.latest_reason_code_count,
        latest_no_reason_code_count=report.latest_no_reason_code_count,
        latest_blocked_reason_count=report.latest_blocked_reason_count,
        latest_no_reason_code_share=report.latest_no_reason_code_share,
        latest_blocked_reason_share=report.latest_blocked_reason_share,
        max_blocked_reason_share=report.max_blocked_reason_share,
        max_no_reason_code_share=report.max_no_reason_code_share,
        top_reason_code_limit=report.top_reason_code_limit,
        blocked_reason_codes_json=list(report.blocked_reason_codes),
        payload_json=payload_json,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )


def strategy_recommendation_reason_trend_from_db_row(
    row: PaperStrategyRecommendationReasonTrendDbRow,
) -> PaperStrategyRecommendationReasonTrendReport:
    if type(row) is not PaperStrategyRecommendationReasonTrendDbRow:
        raise ValueError("row must be a PaperStrategyRecommendationReasonTrendDbRow")
    _reject_json_floats(row.payload_json)
    _validate_json_hard_flags(row.payload_json, "payload_json")
    try:
        report = from_jsonable(PaperStrategyRecommendationReasonTrendReport, row.payload_json)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "payload_json is not a valid strategy recommendation reason trend "
            f"report: {exc}",
        ) from exc
    if type(report) is not PaperStrategyRecommendationReasonTrendReport:
        raise ValueError(
            "payload_json must recover a PaperStrategyRecommendationReasonTrendReport",
        )
    _validate_report_tree(report)
    expected_row = strategy_recommendation_reason_trend_to_db_row(report)
    _validate_row_matches_payload(row, expected_row)
    return report


def to_db_row(
    report: PaperStrategyRecommendationReasonTrendReport,
) -> PaperStrategyRecommendationReasonTrendDbRow:
    return strategy_recommendation_reason_trend_to_db_row(report)


def from_db_row(
    row: PaperStrategyRecommendationReasonTrendDbRow,
) -> PaperStrategyRecommendationReasonTrendReport:
    return strategy_recommendation_reason_trend_from_db_row(row)


def _validate_report_tree(value: Any, field_name: str = "report") -> None:
    if _has_hard_flag(value):
        _require_hard_flags(field_name, value)
    if is_dataclass(value) and not isinstance(value, type):
        for item_field in fields(value):
            _validate_report_tree(
                getattr(value, item_field.name),
                f"{field_name}.{item_field.name}",
            )
    elif isinstance(value, dict):
        for key, item in value.items():
            _validate_report_tree(item, f"{field_name}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _validate_report_tree(item, f"{field_name}.{index}")


def _validate_row_matches_payload(
    row: PaperStrategyRecommendationReasonTrendDbRow,
    expected: PaperStrategyRecommendationReasonTrendDbRow,
) -> None:
    for field_name in (
        "report_sha256",
        "generated_at",
        "config_version",
        "status",
        "source_report_count",
        "first_generated_at",
        "latest_generated_at",
        "latest_primary_reason_code_counts_json",
        "total_primary_reason_code_counts_json",
        "top_new_reason_codes_json",
        "persistent_reason_codes_json",
        "latest_reason_code_count",
        "latest_no_reason_code_count",
        "latest_blocked_reason_count",
        "latest_no_reason_code_share",
        "latest_blocked_reason_share",
        "max_blocked_reason_share",
        "max_no_reason_code_share",
        "top_reason_code_limit",
        "blocked_reason_codes_json",
        "payload_json",
        "paper_only",
        "report_only",
        "readonly",
    ):
        if getattr(row, field_name) != getattr(expected, field_name):
            raise ValueError(f"{field_name} must match payload_json")


def _report_sha256(payload_json: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


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
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        for key in value:
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("reason trend DB row values must be JSON serializable")


def _normalize_json_object(field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    try:
        _reject_json_floats(value)
        normalized = _json_ready(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} {exc}") from exc
    if not isinstance(normalized, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return normalized


def _normalize_reason_code_counts_json(
    field_name: str,
    value: object,
) -> dict[str, int]:
    normalized = _normalize_json_object(field_name, value)
    counts: dict[str, int] = {}
    for key, item in normalized.items():
        reason_code = _require_canonical_token(f"{field_name} key", key)
        if type(item) is not int or item <= 0:
            raise ValueError(f"{field_name} {key} must be a positive int")
        counts[reason_code] = item
    return counts


def _normalize_reason_code_list(field_name: str, value: object) -> list[str]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a JSON list")
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON list")
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        reason_code = _require_canonical_token(field_name, item)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicate reason codes")
        seen.add(reason_code)
        normalized.append(reason_code)
    return normalized


def _counts_to_json(values: tuple[tuple[str, int], ...]) -> dict[str, int]:
    return {reason_code: count for reason_code, count in values}


def _validate_json_hard_flags(value: Any, field_name: str) -> None:
    if not isinstance(value, dict):
        return
    if any(flag_name in value for flag_name in ("paper_only", "report_only", "readonly")):
        for flag_name in ("paper_only", "report_only", "readonly"):
            if value.get(flag_name) is not True:
                raise ValueError(f"{field_name} {flag_name} must be present and true")
    for key, item in value.items():
        child_name = f"{field_name} {key}"
        if isinstance(item, dict):
            _validate_json_hard_flags(item, child_name)
        elif isinstance(item, list):
            for index, element in enumerate(item):
                _validate_json_hard_flags(element, f"{child_name} {index}")


def _reject_json_floats(value: Any) -> None:
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, dict):
        for item in value.values():
            _reject_json_floats(item)
    elif isinstance(value, list):
        for item in value:
            _reject_json_floats(item)


def _has_hard_flag(value: Any) -> bool:
    return any(
        hasattr(value, flag_name)
        for flag_name in ("paper_only", "report_only", "readonly")
    )


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    return value


def _require_canonical_token(field_name: str, value: object) -> str:
    token = _require_canonical_string(field_name, value)
    if token.lower() != token or any(character.isspace() for character in token):
        raise ValueError(f"{field_name} must be a canonical token")
    return token


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be stable, watch, or blocked")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: object) -> None:
    _require_nonnegative_int(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    if value != value.quantize(RATIO_QUANTUM):
        raise ValueError(f"{field_name} must be quantized to 0.000001")
    return value


def _normalize_optional_ratio(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_ratio(field_name, value)


strategy_recommendation_reason_trend_report_to_db_row = (
    strategy_recommendation_reason_trend_to_db_row
)
strategy_recommendation_reason_trend_report_from_db_row = (
    strategy_recommendation_reason_trend_from_db_row
)
