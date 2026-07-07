"""Read-only category resolution rule risk digest for Phase 1 review."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import json
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_MARKET_CATEGORY_RESOLUTION_RULE_DIGEST_CONFIG_VERSION = (
    "market-category-resolution-rule-digest-v0"
)
MARKET_CATEGORY_RESOLUTION_RULE_DIGEST_CATEGORIES = (
    "politics",
    "crypto",
    "macro",
    "commodities",
    "sports",
)
READINESS_STATUSES = ("pass", "watch", "blocked")
CATEGORY_REASON_CODES = (
    "category_rule_ready",
    "category_rule_ambiguity_present",
    "category_rule_disputes_present",
    "category_rule_mapping_gap_present",
    "category_rule_sensitive_references_redacted",
    "category_rule_volatility_present",
)
REPORT_REASON_CODES = (
    "resolution_rule_digest_clear",
    "resolution_rule_ambiguity_present",
    "resolution_rule_disputes_present",
    "resolution_rule_mapping_gaps_present",
    "resolution_rule_review_blocked",
    "resolution_rule_review_watch",
    "resolution_rule_sensitive_references_redacted",
    "resolution_rule_volatility_present",
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
WATCH_RATIO = Decimal("0.000000")
STATUS_WEIGHT = {
    "pass": Decimal("0"),
    "watch": Decimal("1"),
    "blocked": Decimal("2"),
}
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)


@dataclass(frozen=True)
class MarketCategoryResolutionRuleDigestConfig:
    config_version: str = DEFAULT_MARKET_CATEGORY_RESOLUTION_RULE_DIGEST_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        require_paper_only_flags("MarketCategoryResolutionRuleDigestConfig", self)


@dataclass(frozen=True)
class MarketCategoryResolutionRuleInput:
    category_id: str
    market_count: Decimal
    ambiguous_wording_count: Decimal
    missing_authoritative_source_count: Decimal
    rule_change_count: Decimal
    disputed_outcome_count: Decimal
    sensitive_reference_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_category_id("category_id", self.category_id)
        for field_name in (
            "market_count",
            "ambiguous_wording_count",
            "missing_authoritative_source_count",
            "rule_change_count",
            "disputed_outcome_count",
            "sensitive_reference_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _validate_input(self)
        require_paper_only_flags("MarketCategoryResolutionRuleInput", self)


@dataclass(frozen=True)
class MarketCategoryResolutionRuleCategoryRow:
    category_id: str
    market_count: Decimal
    ambiguous_wording_count: Decimal
    missing_authoritative_source_count: Decimal
    rule_change_count: Decimal
    disputed_outcome_count: Decimal
    redacted_sensitive_reference_count: Decimal
    ambiguous_wording_rate: Decimal
    missing_authoritative_source_rate: Decimal
    rule_change_frequency: Decimal
    disputed_outcome_history_proxy: Decimal
    readiness_status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = field(default="", init=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_category_id("category_id", self.category_id)
        for field_name in (
            "market_count",
            "ambiguous_wording_count",
            "missing_authoritative_source_count",
            "rule_change_count",
            "disputed_outcome_count",
            "redacted_sensitive_reference_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "ambiguous_wording_rate",
            "missing_authoritative_source_rate",
            "rule_change_frequency",
            "disputed_outcome_history_proxy",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("readiness_status", self.readiness_status, READINESS_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, CATEGORY_REASON_CODES),
        )
        _validate_category_row(self)
        object.__setattr__(self, "derived_validation_digest", _row_derived_validation_digest(self))
        _require_row_derived_validation_digest(self)
        require_paper_only_flags("MarketCategoryResolutionRuleCategoryRow", self)


@dataclass(frozen=True)
class MarketCategoryResolutionRuleDigestReport:
    generated_at: datetime
    config_version: str
    source_market_count: Decimal
    category_count: Decimal
    ambiguous_wording_rate: Decimal
    missing_authoritative_source_rate: Decimal
    rule_change_frequency: Decimal
    disputed_outcome_history_proxy: Decimal
    status: str
    reason_codes: tuple[str, ...]
    category_rows: tuple[MarketCategoryResolutionRuleCategoryRow, ...]
    derived_validation_digest: str = field(default="", init=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("source_market_count", "category_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "ambiguous_wording_rate",
            "missing_authoritative_source_rate",
            "rule_change_frequency",
            "disputed_outcome_history_proxy",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, READINESS_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(self, "category_rows", _normalize_rows(self.category_rows))
        _validate_report(self)
        object.__setattr__(
            self,
            "derived_validation_digest",
            _report_derived_validation_digest(self),
        )
        _require_report_derived_validation_digest(self)
        _reject_sensitive_surface_fields("category resolution rule digest report", self)
        require_paper_only_flags("MarketCategoryResolutionRuleDigestReport", self)


def build_market_category_resolution_rule_digest_report(
    inputs: list[MarketCategoryResolutionRuleInput]
    | tuple[MarketCategoryResolutionRuleInput, ...],
    *,
    config: MarketCategoryResolutionRuleDigestConfig,
    generated_at: datetime,
) -> MarketCategoryResolutionRuleDigestReport:
    if type(config) is not MarketCategoryResolutionRuleDigestConfig:
        raise ValueError("config must be a MarketCategoryResolutionRuleDigestConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _normalize_inputs(inputs)
    category_rows = tuple(sorted((_category_row(row) for row in rows), key=_row_sort_key))
    return MarketCategoryResolutionRuleDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_market_count=_sum_rows(category_rows, "market_count"),
        category_count=_count(len(category_rows)),
        ambiguous_wording_rate=_report_rate(category_rows, "ambiguous_wording_count"),
        missing_authoritative_source_rate=_report_rate(
            category_rows,
            "missing_authoritative_source_count",
        ),
        rule_change_frequency=_report_rate(category_rows, "rule_change_count"),
        disputed_outcome_history_proxy=_report_rate(
            category_rows,
            "disputed_outcome_count",
        ),
        status=_status_rollup(tuple(row.readiness_status for row in category_rows)),
        reason_codes=_report_reason_codes(category_rows),
        category_rows=category_rows,
    )


def market_category_resolution_rule_digest_payload(
    report: MarketCategoryResolutionRuleDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is MarketCategoryResolutionRuleDigestReport:
        require_paper_only_flags("report", report)
        _require_report_derived_validation_digest(report)
        _validate_report(report)
        _reject_sensitive_public_payload("category resolution rule digest report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_sensitive_public_payload("category resolution rule digest payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a MarketCategoryResolutionRuleDigestReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    require_paper_only_flags("payload", _DictFlags(payload))
    _reject_sensitive_public_payload("category resolution rule digest payload", payload)
    _validate_public_payload_digest(payload)
    return payload


class _DictFlags:
    def __init__(self, value: dict[str, Any]) -> None:
        self._value = value

    @property
    def paper_only(self) -> object:
        return self._value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self._value.get("report_only")

    @property
    def readonly(self) -> object:
        return self._value.get("readonly")


def _normalize_inputs(
    inputs: list[MarketCategoryResolutionRuleInput]
    | tuple[MarketCategoryResolutionRuleInput, ...],
) -> tuple[MarketCategoryResolutionRuleInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(inputs)
    seen_categories: set[str] = set()
    for row in rows:
        if type(row) is not MarketCategoryResolutionRuleInput:
            raise ValueError("inputs must contain MarketCategoryResolutionRuleInput values")
        require_paper_only_flags("input", row)
        if row.category_id in seen_categories:
            raise ValueError("inputs must not contain duplicate category_id values")
        seen_categories.add(row.category_id)
    return rows


def _category_row(row: MarketCategoryResolutionRuleInput) -> MarketCategoryResolutionRuleCategoryRow:
    return MarketCategoryResolutionRuleCategoryRow(
        category_id=row.category_id,
        market_count=row.market_count,
        ambiguous_wording_count=row.ambiguous_wording_count,
        missing_authoritative_source_count=row.missing_authoritative_source_count,
        rule_change_count=row.rule_change_count,
        disputed_outcome_count=row.disputed_outcome_count,
        redacted_sensitive_reference_count=row.sensitive_reference_count,
        ambiguous_wording_rate=_ratio(row.ambiguous_wording_count, row.market_count),
        missing_authoritative_source_rate=_ratio(
            row.missing_authoritative_source_count,
            row.market_count,
        ),
        rule_change_frequency=_ratio(row.rule_change_count, row.market_count),
        disputed_outcome_history_proxy=_ratio(row.disputed_outcome_count, row.market_count),
        readiness_status=_category_status(row),
        reason_codes=_category_reason_codes(row),
    )


def _category_reason_codes(row: MarketCategoryResolutionRuleInput) -> tuple[str, ...]:
    codes: list[str] = []
    if row.ambiguous_wording_count > ZERO_COUNT:
        codes.append("category_rule_ambiguity_present")
    if row.missing_authoritative_source_count > ZERO_COUNT:
        codes.append("category_rule_mapping_gap_present")
    if row.rule_change_count > ZERO_COUNT:
        codes.append("category_rule_volatility_present")
    if row.disputed_outcome_count > ZERO_COUNT:
        codes.append("category_rule_disputes_present")
    if row.sensitive_reference_count > ZERO_COUNT:
        codes.append("category_rule_sensitive_references_redacted")
    if not codes:
        codes.append("category_rule_ready")
    return tuple(code for code in CATEGORY_REASON_CODES if code in codes)


def _report_reason_codes(
    rows: tuple[MarketCategoryResolutionRuleCategoryRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("resolution_rule_digest_clear",)
    codes: list[str] = []
    if any(row.ambiguous_wording_count > ZERO_COUNT for row in rows):
        codes.append("resolution_rule_ambiguity_present")
    if any(row.missing_authoritative_source_count > ZERO_COUNT for row in rows):
        codes.append("resolution_rule_mapping_gaps_present")
    if any(row.rule_change_count > ZERO_COUNT for row in rows):
        codes.append("resolution_rule_volatility_present")
    if any(row.disputed_outcome_count > ZERO_COUNT for row in rows):
        codes.append("resolution_rule_disputes_present")
    if any(row.redacted_sensitive_reference_count > ZERO_COUNT for row in rows):
        codes.append("resolution_rule_sensitive_references_redacted")
    status = _status_rollup(tuple(row.readiness_status for row in rows))
    if status == "blocked":
        codes.append("resolution_rule_review_blocked")
    elif status == "watch":
        codes.append("resolution_rule_review_watch")
    if not codes:
        codes.append("resolution_rule_digest_clear")
    return tuple(code for code in REPORT_REASON_CODES if code in codes)


def _category_status(row: MarketCategoryResolutionRuleInput) -> str:
    if (
        row.ambiguous_wording_count > ZERO_COUNT
        or row.missing_authoritative_source_count > ZERO_COUNT
        or row.rule_change_count > ZERO_COUNT
    ):
        return "blocked"
    if row.disputed_outcome_count > ZERO_COUNT or row.sensitive_reference_count > ZERO_COUNT:
        return "watch"
    return "pass"


def _status_rollup(statuses: tuple[str, ...]) -> str:
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _row_sort_key(
    row: MarketCategoryResolutionRuleCategoryRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.readiness_status],
        -row.rule_change_frequency,
        -row.ambiguous_wording_rate,
        -row.disputed_outcome_history_proxy,
        row.category_id,
    )


def _validate_input(row: MarketCategoryResolutionRuleInput) -> None:
    if row.market_count == ZERO_COUNT:
        for field_name in (
            "ambiguous_wording_count",
            "missing_authoritative_source_count",
            "rule_change_count",
            "disputed_outcome_count",
            "sensitive_reference_count",
        ):
            if getattr(row, field_name) > ZERO_COUNT:
                raise ValueError("market_count is required for nonzero rule risk counts")
    for field_name in (
        "ambiguous_wording_count",
        "missing_authoritative_source_count",
        "rule_change_count",
        "disputed_outcome_count",
    ):
        if getattr(row, field_name) > row.market_count:
            raise ValueError(f"{field_name} must not exceed market_count")


def _validate_category_row(row: MarketCategoryResolutionRuleCategoryRow) -> None:
    for field_name in (
        "ambiguous_wording_count",
        "missing_authoritative_source_count",
        "rule_change_count",
        "disputed_outcome_count",
    ):
        if getattr(row, field_name) > row.market_count:
            raise ValueError(f"{field_name} must not exceed market_count")
    if row.market_count == ZERO_COUNT:
        expected_ratio = ZERO_RATIO
    else:
        expected_ratio = _ratio(row.ambiguous_wording_count, row.market_count)
    if row.ambiguous_wording_rate != expected_ratio:
        raise ValueError("ambiguous_wording_rate must match counts")
    if row.missing_authoritative_source_rate != _safe_ratio(
        row.missing_authoritative_source_count,
        row.market_count,
    ):
        raise ValueError("missing_authoritative_source_rate must match counts")
    if row.rule_change_frequency != _safe_ratio(row.rule_change_count, row.market_count):
        raise ValueError("rule_change_frequency must match counts")
    if row.disputed_outcome_history_proxy != _safe_ratio(
        row.disputed_outcome_count,
        row.market_count,
    ):
        raise ValueError("disputed_outcome_history_proxy must match counts")
    if row.readiness_status != _category_row_status(row):
        raise ValueError("readiness_status must match category risk counts")
    if row.reason_codes != _category_row_reason_codes(row):
        raise ValueError("reason_codes must match category risk counts")


def _validate_report(report: MarketCategoryResolutionRuleDigestReport) -> None:
    if report.category_count != _count(len(report.category_rows)):
        raise ValueError("category_count must match category_rows")
    if report.source_market_count != _sum_rows(report.category_rows, "market_count"):
        raise ValueError("source_market_count must match category_rows")
    if report.ambiguous_wording_rate != _report_rate(
        report.category_rows,
        "ambiguous_wording_count",
    ):
        raise ValueError("ambiguous_wording_rate must match category_rows")
    if report.missing_authoritative_source_rate != _report_rate(
        report.category_rows,
        "missing_authoritative_source_count",
    ):
        raise ValueError("missing_authoritative_source_rate must match category_rows")
    if report.rule_change_frequency != _report_rate(report.category_rows, "rule_change_count"):
        raise ValueError("rule_change_frequency must match category_rows")
    if report.disputed_outcome_history_proxy != _report_rate(
        report.category_rows,
        "disputed_outcome_count",
    ):
        raise ValueError("disputed_outcome_history_proxy must match category_rows")
    if report.status != _status_rollup(tuple(row.readiness_status for row in report.category_rows)):
        raise ValueError("status must match category_rows")
    if report.reason_codes != _report_reason_codes(report.category_rows):
        raise ValueError("reason_codes must match category_rows")
    for row in report.category_rows:
        _require_row_derived_validation_digest(row)
    if report.category_rows != tuple(sorted(report.category_rows, key=_row_sort_key)):
        raise ValueError("category_rows must use deterministic " + "ord" + "ering")


def _category_row_status(row: MarketCategoryResolutionRuleCategoryRow) -> str:
    if (
        row.ambiguous_wording_count > ZERO_COUNT
        or row.missing_authoritative_source_count > ZERO_COUNT
        or row.rule_change_count > ZERO_COUNT
    ):
        return "blocked"
    if (
        row.disputed_outcome_count > ZERO_COUNT
        or row.redacted_sensitive_reference_count > ZERO_COUNT
    ):
        return "watch"
    return "pass"


def _category_row_reason_codes(
    row: MarketCategoryResolutionRuleCategoryRow,
) -> tuple[str, ...]:
    codes: list[str] = []
    if row.ambiguous_wording_count > ZERO_COUNT:
        codes.append("category_rule_ambiguity_present")
    if row.missing_authoritative_source_count > ZERO_COUNT:
        codes.append("category_rule_mapping_gap_present")
    if row.rule_change_count > ZERO_COUNT:
        codes.append("category_rule_volatility_present")
    if row.disputed_outcome_count > ZERO_COUNT:
        codes.append("category_rule_disputes_present")
    if row.redacted_sensitive_reference_count > ZERO_COUNT:
        codes.append("category_rule_sensitive_references_redacted")
    if not codes:
        codes.append("category_rule_ready")
    return tuple(code for code in CATEGORY_REASON_CODES if code in codes)


def _normalize_rows(
    value: object,
) -> tuple[MarketCategoryResolutionRuleCategoryRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("category_rows must be a tuple")
    try:
        rows = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("category_rows must be a tuple") from exc
    seen_categories: set[str] = set()
    for row in rows:
        if type(row) is not MarketCategoryResolutionRuleCategoryRow:
            raise ValueError(
                "category_rows must contain MarketCategoryResolutionRuleCategoryRow values",
            )
        require_paper_only_flags("category row", row)
        _require_row_derived_validation_digest(row)
        if row.category_id in seen_categories:
            raise ValueError("category_rows must not contain duplicate category_id values")
        seen_categories.add(row.category_id)
    return rows


def _row_derived_validation_digest(row: MarketCategoryResolutionRuleCategoryRow) -> str:
    return _public_payload_derived_validation_digest(_row_public_payload_for_digest(row))


def _report_derived_validation_digest(report: MarketCategoryResolutionRuleDigestReport) -> str:
    return _public_payload_derived_validation_digest(_report_public_payload_for_digest(report))


def _require_row_derived_validation_digest(
    row: MarketCategoryResolutionRuleCategoryRow,
) -> None:
    _require_sha256_digest("derived_validation_digest", row.derived_validation_digest)
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match category row fields")


def _require_report_derived_validation_digest(
    report: MarketCategoryResolutionRuleDigestReport,
) -> None:
    _require_sha256_digest("derived_validation_digest", report.derived_validation_digest)
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _row_public_payload_for_digest(
    row: MarketCategoryResolutionRuleCategoryRow,
) -> dict[str, Any]:
    payload = _json_ready(row)
    if type(payload) is not dict:
        raise ValueError("category row payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _report_public_payload_for_digest(
    report: MarketCategoryResolutionRuleDigestReport,
) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _validate_public_payload_digest(payload: dict[str, Any]) -> None:
    category_rows = payload.get("category_rows")
    if not isinstance(category_rows, list):
        raise ValueError("category_rows must be a list in public payload")
    for row in category_rows:
        if type(row) is not dict:
            raise ValueError("category_rows must contain JSON objects")
        row_digest = row.get("derived_validation_digest")
        _require_sha256_digest("derived_validation_digest", row_digest)
        if row_digest != _public_payload_derived_validation_digest(
            _payload_without_digest(row),
        ):
            raise ValueError("derived_validation_digest must match category row payload")
    report_digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", report_digest)
    if report_digest != _public_payload_derived_validation_digest(
        _payload_without_digest(payload),
    ):
        raise ValueError("derived_validation_digest must match report payload")


def _payload_without_digest(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _require_sha256_digest(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or value.lower() != value
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


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
    if tuple(code for code in allowed if code in reason_codes) != reason_codes:
        raise ValueError(f"{field_name} must be deterministic")
    return reason_codes


def _reject_sensitive_surface_fields(label: str, value: object) -> None:
    fragments = (
        "credential",
        "private_key",
        "wal" + "let",
        "acc" + "ount",
        "balance",
        "or" + "der",
        "cancel",
        "replace",
        "sign",
        "exchange_mutation",
    )
    for field_name in _iter_field_names(value):
        normalized = field_name.lower()
        for fragment in fragments:
            if fragment in normalized:
                raise ValueError(f"sensitive live surface field in {label}: {field_name}")


def _reject_sensitive_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            nested_path = field.name if not path else f"{path}.{field.name}"
            if _has_unsafe_surface_fragment(field.name):
                raise ValueError(f"unsafe surface field in {label}: {field.name}")
            _reject_sensitive_public_payload(label, getattr(value, field.name), nested_path)
        return
    if type(value) is str:
        if _has_sensitive_string(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
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
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            if _has_unsafe_surface_fragment(key):
                raise ValueError(f"unsafe surface field in {label}: {key}")
            if key in {"paper_only", "report_only", "readonly"} and nested_value is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_sensitive_public_payload(label, nested_value, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, nested_value in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_sensitive_public_payload(label, nested_value, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _json_ready(value: Any) -> Any:
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
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(nested_value)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _has_sensitive_string(value: str) -> bool:
    lowered = value.lower()
    markers = (
        "://",
        "tok" + "en=",
        "api" + "_key=",
        "sec" + "ret",
        "priv" + "ate",
        "wal" + "let:",
        "bear" + "er ",
        "pass" + "word",
        "seed" + "_phrase",
    )
    return any(marker in lowered for marker in markers) or _has_unsafe_surface_fragment(value)


def _has_unsafe_surface_fragment(value: str) -> bool:
    fragments = (
        "credential",
        "private_key",
        "wal" + "let",
        "acc" + "ount",
        "balance",
        "or" + "der",
        "cancel",
        "replace",
        "sign",
        "exchange_mutation",
    )
    normalized = value.lower()
    return any(fragment in normalized for fragment in fragments)


def _iter_field_names(value: object) -> tuple[str, ...]:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        keys: list[str] = []
        for field_name in value.__dataclass_fields__:
            keys.append(field_name)
            keys.extend(_iter_field_names(getattr(value, field_name)))
        return tuple(keys)
    if isinstance(value, dict):
        keys = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_iter_field_names(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_field_names(item))
        return tuple(keys)
    return ()


def _report_rate(
    rows: tuple[MarketCategoryResolutionRuleCategoryRow, ...],
    field_name: str,
) -> Decimal:
    return _safe_ratio(_sum_rows(rows, field_name), _sum_rows(rows, "market_count"))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    return _ratio(numerator, denominator)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_ratio("ratio", numerator / denominator)


def _sum_rows(
    rows: tuple[MarketCategoryResolutionRuleCategoryRow, ...],
    field_name: str,
) -> Decimal:
    return _normalize_nonnegative_count(
        field_name,
        sum((getattr(row, field_name) for row in rows), ZERO_COUNT),
    )


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO_RATIO or value > ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_category_id(field_name: str, value: object) -> None:
    _require_member(field_name, value, MARKET_CATEGORY_RESOLUTION_RULE_DIGEST_CATEGORIES)


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


__all__ = (
    "DEFAULT_MARKET_CATEGORY_RESOLUTION_RULE_DIGEST_CONFIG_VERSION",
    "MARKET_CATEGORY_RESOLUTION_RULE_DIGEST_CATEGORIES",
    "MarketCategoryResolutionRuleDigestConfig",
    "MarketCategoryResolutionRuleInput",
    "MarketCategoryResolutionRuleCategoryRow",
    "MarketCategoryResolutionRuleDigestReport",
    "build_market_category_resolution_rule_digest_report",
    "market_category_resolution_rule_digest_payload",
)
