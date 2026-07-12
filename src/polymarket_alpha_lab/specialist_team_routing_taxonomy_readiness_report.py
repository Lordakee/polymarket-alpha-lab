"""Pure report-only readiness report for specialist routing taxonomy coverage."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from decimal import Decimal
from hashlib import sha256
import json
import re
from typing import Any, Iterable

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_SPECIALIST_TEAM_ROUTING_TAXONOMY_READINESS_CONFIG_VERSION = (
    "specialist-team-routing-taxonomy-readiness-v0"
)

MEDIUM_SCALE_SPECIALIST_TEAM_CATEGORIES = (
    "politics",
    "crypto_btc",
    "crypto_eth",
    "macro_rates",
    "equity_indices",
    "gold",
    "oil",
    "soccer",
    "basketball",
    "other_sports",
)

SPECIALIST_TEAM_ROUTING_TAXONOMY_READINESS_STATUSES = ("pass", "watch", "block")

ROW_REASON_CODES = (
    "taxonomy_category_ready",
    "taxonomy_category_missing",
    "primary_team_present",
    "primary_team_missing",
    "advisory_teams_present",
    "advisory_teams_missing",
    "unrouted_block_reason_present",
    "unrouted_block_reason_missing",
)

REPORT_REASON_CODES = (
    "routing_taxonomy_ready",
    "routing_taxonomy_has_watch_categories",
    "routing_taxonomy_has_block_categories",
)

_CATEGORY_TO_TEAM_ID = {
    "politics": "politics",
    "crypto_btc": "crypto_btc",
    "crypto_eth": "crypto_eth",
    "macro_rates": "macro_rates",
    "equity_indices": "equity_indices",
    "gold": "commodities_gold",
    "oil": "commodities_oil",
    "soccer": "sports_soccer",
    "basketball": "sports_basketball",
    "other_sports": "sports_other",
}

_CANONICAL_TEXT_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_COUNT_QUANT = Decimal("1.000000")
_ZERO_COUNT = Decimal("0.000000")
_ONE_RATIO = Decimal("1.000000")

_UNSAFE_PUBLIC_KEY_FRAGMENTS = frozenset(
    (
        "live",
        "auth",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
        "database",
        "table",
        "dsn",
        "url",
    ),
)

_UNSAFE_PUBLIC_VALUE_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        r"\blive\b",
        r"\bauth(?:entication|orization)?\b",
        r"\bwallet\b",
        r"\border\b",
        r"\btrade\b",
        r"\bposition\b",
        r"\bbuy\b",
        r"\bsell\b",
        r"\brecommend(?:ation|ed|ing)?\b",
        r"\bdatabase\b",
        r"\btable\b",
        r"\bdsn\b",
        r"https?://",
        r"\burl\b",
    )
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class SpecialistTeamRoutingTaxonomyReadinessConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_SPECIALIST_TEAM_ROUTING_TAXONOMY_READINESS_CONFIG_VERSION
    )
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            SpecialistTeamRoutingTaxonomyReadinessConfig,
            "config",
        )
        if self.config_version != DEFAULT_SPECIALIST_TEAM_ROUTING_TAXONOMY_READINESS_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class SpecialistTeamRoutingTaxonomyReadinessInput(_FinalDataclass):
    category_id: str
    primary_team_id: str | None
    advisory_team_ids: tuple[str, ...]
    unrouted_block_reason: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            SpecialistTeamRoutingTaxonomyReadinessInput,
            "input",
        )
        category_id = _require_category_id("category_id", self.category_id)
        object.__setattr__(self, "category_id", category_id)
        object.__setattr__(
            self,
            "primary_team_id",
            _normalize_optional_primary_team_id(
                "primary_team_id",
                self.primary_team_id,
                category_id,
            ),
        )
        object.__setattr__(
            self,
            "advisory_team_ids",
            _normalize_advisory_team_ids(self.advisory_team_ids, category_id),
        )
        object.__setattr__(
            self,
            "unrouted_block_reason",
            _normalize_optional_reason_text(
                "unrouted_block_reason",
                self.unrouted_block_reason,
            ),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class SpecialistTeamRoutingTaxonomyReadinessRow(_FinalDataclass):
    category_id: str
    status: str
    primary_team_id: str | None
    advisory_team_ids: tuple[str, ...]
    unrouted_block_reason: str | None
    primary_team_ready: bool
    advisory_teams_ready: bool
    unrouted_block_reason_ready: bool
    readiness_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamRoutingTaxonomyReadinessRow, "row")
        category_id = _require_category_id("category_id", self.category_id)
        object.__setattr__(self, "category_id", category_id)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "primary_team_id",
            _normalize_optional_primary_team_id(
                "primary_team_id",
                self.primary_team_id,
                category_id,
            ),
        )
        object.__setattr__(
            self,
            "advisory_team_ids",
            _normalize_advisory_team_ids(self.advisory_team_ids, category_id),
        )
        object.__setattr__(
            self,
            "unrouted_block_reason",
            _normalize_optional_reason_text(
                "unrouted_block_reason",
                self.unrouted_block_reason,
            ),
        )
        _require_bool("primary_team_ready", self.primary_team_ready)
        _require_bool("advisory_teams_ready", self.advisory_teams_ready)
        _require_bool(
            "unrouted_block_reason_ready",
            self.unrouted_block_reason_ready,
        )
        object.__setattr__(
            self,
            "readiness_score",
            _require_ratio_decimal("readiness_score", self.readiness_score),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class SpecialistTeamRoutingTaxonomyReadinessReport(_FinalDataclass):
    config_version: str
    category_count: Decimal
    observed_category_count: Decimal
    missing_category_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    ready_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[SpecialistTeamRoutingTaxonomyReadinessRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, SpecialistTeamRoutingTaxonomyReadinessReport, "report")
        if self.config_version != DEFAULT_SPECIALIST_TEAM_ROUTING_TAXONOMY_READINESS_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "category_count",
            "observed_category_count",
            "missing_category_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "ready_ratio",
            _require_ratio_decimal("ready_ratio", self.ready_ratio),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest != _digest_from_values(
            _report_values_without_digest(self),
        ):
            raise ValueError("derived_validation_digest must match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return specialist_team_routing_taxonomy_readiness_report_payload(self)


def build_specialist_team_routing_taxonomy_readiness_report(
    inputs: Iterable[SpecialistTeamRoutingTaxonomyReadinessInput],
    *,
    config: SpecialistTeamRoutingTaxonomyReadinessConfig,
) -> SpecialistTeamRoutingTaxonomyReadinessReport:
    _require_exact_type(config, SpecialistTeamRoutingTaxonomyReadinessConfig, "config")
    _require_hard_flags("config", config)
    source_inputs = _normalize_inputs(inputs)
    rows = tuple(_row_for_category(category_id, source_inputs) for category_id in MEDIUM_SCALE_SPECIALIST_TEAM_CATEGORIES)
    values: dict[str, object] = {
        "config_version": config.config_version,
        "category_count": _count(len(MEDIUM_SCALE_SPECIALIST_TEAM_CATEGORIES)),
        "observed_category_count": _count(len({item.category_id for item in source_inputs})),
        "missing_category_count": _count(
            sum(1 for row in rows if "taxonomy_category_missing" in row.reason_codes),
        ),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "ready_ratio": _ready_ratio(rows),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return SpecialistTeamRoutingTaxonomyReadinessReport(
        **values,
        derived_validation_digest=_digest_from_values(values),
    )


def specialist_team_routing_taxonomy_readiness_report_payload(
    report: SpecialistTeamRoutingTaxonomyReadinessReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is SpecialistTeamRoutingTaxonomyReadinessReport:
        _require_hard_flags("report", report)
        _validate_report(report)
        _reject_unsafe_public_payload("report", report)
        payload = json_ready_no_floats(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _validate_payload(payload)
        return payload
    if type(report) is dict:
        _validate_payload(report)
        payload = json_ready_no_floats(report)
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        _validate_payload(payload)
        return payload
    raise ValueError(
        "report must be a SpecialistTeamRoutingTaxonomyReadinessReport or payload",
    )


def _row_for_category(
    category_id: str,
    inputs: tuple[SpecialistTeamRoutingTaxonomyReadinessInput, ...],
) -> SpecialistTeamRoutingTaxonomyReadinessRow:
    matches = tuple(item for item in inputs if item.category_id == category_id)
    if not matches:
        return SpecialistTeamRoutingTaxonomyReadinessRow(
            category_id=category_id,
            status="block",
            primary_team_id=None,
            advisory_team_ids=(),
            unrouted_block_reason=None,
            primary_team_ready=False,
            advisory_teams_ready=False,
            unrouted_block_reason_ready=False,
            readiness_score=Decimal("0.000000"),
            reason_codes=(
                "taxonomy_category_missing",
                "primary_team_missing",
                "advisory_teams_missing",
                "unrouted_block_reason_missing",
            ),
        )
    if len(matches) != 1:
        raise ValueError("inputs must contain at most one row per category_id")
    item = matches[0]
    primary_team_ready = item.primary_team_id is not None
    advisory_teams_ready = bool(item.advisory_team_ids)
    unrouted_block_reason_ready = (
        primary_team_ready or item.unrouted_block_reason is not None
    )
    return SpecialistTeamRoutingTaxonomyReadinessRow(
        category_id=category_id,
        status=_row_status(
            primary_team_ready=primary_team_ready,
            advisory_teams_ready=advisory_teams_ready,
            unrouted_block_reason_ready=unrouted_block_reason_ready,
        ),
        primary_team_id=item.primary_team_id,
        advisory_team_ids=item.advisory_team_ids,
        unrouted_block_reason=item.unrouted_block_reason,
        primary_team_ready=primary_team_ready,
        advisory_teams_ready=advisory_teams_ready,
        unrouted_block_reason_ready=unrouted_block_reason_ready,
        readiness_score=_row_readiness_score(
            primary_team_ready=primary_team_ready,
            advisory_teams_ready=advisory_teams_ready,
            unrouted_block_reason_ready=unrouted_block_reason_ready,
        ),
        reason_codes=_row_reason_codes(
            missing=False,
            primary_team_ready=primary_team_ready,
            advisory_teams_ready=advisory_teams_ready,
            unrouted_block_reason_ready=unrouted_block_reason_ready,
        ),
    )


def _row_status(
    *,
    primary_team_ready: bool,
    advisory_teams_ready: bool,
    unrouted_block_reason_ready: bool,
) -> str:
    if not primary_team_ready or not unrouted_block_reason_ready:
        return "block"
    if not advisory_teams_ready:
        return "watch"
    return "pass"


def _row_readiness_score(
    *,
    primary_team_ready: bool,
    advisory_teams_ready: bool,
    unrouted_block_reason_ready: bool,
) -> Decimal:
    ready_count = sum(
        1
        for value in (
            primary_team_ready,
            advisory_teams_ready,
            unrouted_block_reason_ready,
        )
        if value
    )
    return (Decimal(ready_count) / Decimal("3")).quantize(Decimal("0.000001"))


def _row_reason_codes(
    *,
    missing: bool,
    primary_team_ready: bool,
    advisory_teams_ready: bool,
    unrouted_block_reason_ready: bool,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if missing:
        reasons.append("taxonomy_category_missing")
    elif primary_team_ready and advisory_teams_ready and unrouted_block_reason_ready:
        reasons.append("taxonomy_category_ready")
    reasons.append("primary_team_present" if primary_team_ready else "primary_team_missing")
    reasons.append(
        "advisory_teams_present" if advisory_teams_ready else "advisory_teams_missing",
    )
    if not primary_team_ready:
        reasons.append(
            "unrouted_block_reason_present"
            if unrouted_block_reason_ready
            else "unrouted_block_reason_missing",
        )
    return tuple(
        reason
        for reason in ROW_REASON_CODES
        if reason in reasons
        and reason not in ("primary_team_present", "advisory_teams_present")
    ) or ("taxonomy_category_ready",)


def _report_status(
    rows: tuple[SpecialistTeamRoutingTaxonomyReadinessRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[SpecialistTeamRoutingTaxonomyReadinessRow, ...],
) -> tuple[str, ...]:
    has_watch = any(row.status == "watch" for row in rows)
    has_block = any(row.status == "block" for row in rows)
    if not has_watch and not has_block:
        return ("routing_taxonomy_ready",)
    reasons: list[str] = []
    if has_watch:
        reasons.append("routing_taxonomy_has_watch_categories")
    if has_block:
        reasons.append("routing_taxonomy_has_block_categories")
    return tuple(reasons)


def _ready_ratio(rows: tuple[SpecialistTeamRoutingTaxonomyReadinessRow, ...]) -> Decimal:
    if not rows:
        return Decimal("0.000000")
    return (
        Decimal(sum(1 for row in rows if row.status == "pass")) / Decimal(len(rows))
    ).quantize(Decimal("0.000001"))


def _status_count(
    rows: tuple[SpecialistTeamRoutingTaxonomyReadinessRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _normalize_inputs(
    inputs: Iterable[SpecialistTeamRoutingTaxonomyReadinessInput],
) -> tuple[SpecialistTeamRoutingTaxonomyReadinessInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        items = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        _require_exact_type(
            item,
            SpecialistTeamRoutingTaxonomyReadinessInput,
            "input",
        )
        _require_hard_flags("input", item)
        if item.category_id in seen:
            raise ValueError("inputs must contain at most one row per category_id")
        seen.add(item.category_id)
    return items


def _normalize_rows(
    rows: object,
) -> tuple[SpecialistTeamRoutingTaxonomyReadinessRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        items = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    if tuple(row.category_id for row in items) != MEDIUM_SCALE_SPECIALIST_TEAM_CATEGORIES:
        raise ValueError("rows must match medium scale specialist categories")
    for item in items:
        _require_exact_type(item, SpecialistTeamRoutingTaxonomyReadinessRow, "row")
        _require_hard_flags("row", item)
    return items


def _normalize_optional_primary_team_id(
    field_name: str,
    value: object,
    category_id: str,
) -> str | None:
    if value is None:
        return None
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a known routing team")
    allowed = (category_id, _CATEGORY_TO_TEAM_ID[category_id])
    if value not in allowed:
        raise ValueError(f"{field_name} must match category_id")
    return value


def _normalize_advisory_team_ids(value: object, category_id: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("advisory_team_ids must be an iterable")
    try:
        items = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("advisory_team_ids must be an iterable") from exc
    seen: set[str] = set()
    normalized: list[str] = []
    for item in items:
        if type(item) is not str or not _CANONICAL_TEXT_RE.fullmatch(item):
            raise ValueError("advisory_team_ids must contain canonical team labels")
        if item in (category_id, _CATEGORY_TO_TEAM_ID[category_id]):
            raise ValueError("advisory_team_ids must not contain primary category team")
        if item in seen:
            raise ValueError("advisory_team_ids must be unique")
        seen.add(item)
        normalized.append(item)
    return tuple(normalized)


def _normalize_optional_reason_text(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    if type(value) is not str or not _CANONICAL_TEXT_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be canonical public text")
    _reject_unsafe_public_text(field_name, value)
    return value


def _normalize_reason_codes(
    field_name: str,
    values: object,
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        items = tuple(values)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not items:
        raise ValueError(f"{field_name} must be nonempty")
    seen: set[str] = set()
    previous_index = -1
    for item in items:
        if type(item) is not str or item not in allowed_values:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if item in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(item)
        index = allowed_values.index(item)
        if index <= previous_index:
            raise ValueError(f"{field_name} must be sorted deterministically")
        previous_index = index
    return items


def _validate_row(row: SpecialistTeamRoutingTaxonomyReadinessRow) -> None:
    expected_primary_ready = row.primary_team_id is not None
    expected_advisory_ready = bool(row.advisory_team_ids)
    expected_unrouted_ready = (
        expected_primary_ready or row.unrouted_block_reason is not None
    )
    if row.primary_team_ready != expected_primary_ready:
        raise ValueError("primary_team_ready must match primary_team_id")
    if row.advisory_teams_ready != expected_advisory_ready:
        raise ValueError("advisory_teams_ready must match advisory_team_ids")
    if row.unrouted_block_reason_ready != expected_unrouted_ready:
        raise ValueError("unrouted_block_reason_ready must match routing fields")
    expected_status = _row_status(
        primary_team_ready=expected_primary_ready,
        advisory_teams_ready=expected_advisory_ready,
        unrouted_block_reason_ready=expected_unrouted_ready,
    )
    if row.status != expected_status:
        raise ValueError("status must match routing taxonomy readiness")
    expected_score = _row_readiness_score(
        primary_team_ready=expected_primary_ready,
        advisory_teams_ready=expected_advisory_ready,
        unrouted_block_reason_ready=expected_unrouted_ready,
    )
    if row.readiness_score != expected_score:
        raise ValueError("readiness_score must match routing taxonomy readiness")


def _validate_report(report: SpecialistTeamRoutingTaxonomyReadinessReport) -> None:
    rows = report.rows
    if report.category_count != _count(len(MEDIUM_SCALE_SPECIALIST_TEAM_CATEGORIES)):
        raise ValueError("category_count must match medium scale categories")
    if report.observed_category_count + report.missing_category_count != report.category_count:
        raise ValueError("observed and missing counts must match category_count")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.ready_ratio != _ready_ratio(rows):
        raise ValueError("ready_ratio must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _validate_payload(payload: dict[str, Any]) -> None:
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    _reject_non_decimal_payload_numbers(payload)
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    if digest != _digest_from_values(unsigned):
        raise ValueError("derived_validation_digest must match payload digest")


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


def _report_values_without_digest(
    report: SpecialistTeamRoutingTaxonomyReadinessReport,
) -> dict[str, object]:
    values: dict[str, object] = {}
    for field in fields(report):
        if field.name == "derived_validation_digest":
            continue
        values[field.name] = getattr(report, field.name)
    return values


def _digest_from_values(values: object) -> str:
    payload = json_ready_no_floats(values)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _reject_non_decimal_payload_numbers(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) in (int, float):
        raise ValueError("payload numeric values must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_non_decimal_payload_numbers(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_non_decimal_payload_numbers(item)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_category_id(field_name: str, value: object) -> str:
    if type(value) is not str or value not in MEDIUM_SCALE_SPECIALIST_TEAM_CATEGORIES:
        raise ValueError(f"{field_name} must be a medium scale specialist category")
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SPECIALIST_TEAM_ROUTING_TAXONOMY_READINESS_STATUSES:
        raise ValueError(f"{field_name} must be a supported status")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_COUNT_QUANT)
    if value != quantized:
        raise ValueError(f"{field_name} must be quantized to six places")
    if value < _ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    checked = _require_count_decimal(field_name, value)
    if checked > _ONE_RATIO:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return checked


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANT)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    for path, key, item in _walk_public_items(value):
        lowered_key = key.casefold()
        if any(fragment in lowered_key for fragment in _UNSAFE_PUBLIC_KEY_FRAGMENTS):
            raise ValueError(f"unsafe public field in {label}: {path}")
        if type(item) is str:
            _reject_unsafe_public_text(path, item)


def _walk_public_items(value: object, path: str = "") -> tuple[tuple[str, str, object], ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _walk_public_items(asdict(value), path)
    if isinstance(value, dict):
        items: list[tuple[str, str, object]] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            item_path = f"{path}.{key}" if path else key
            items.append((item_path, key, item))
            items.extend(_walk_public_items(item, item_path))
        return tuple(items)
    if isinstance(value, (list, tuple)):
        items = []
        for index, item in enumerate(value):
            items.extend(_walk_public_items(item, f"{path}[{index}]"))
        return tuple(items)
    return ()


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    lowered = value.casefold()
    if any(pattern.search(lowered) for pattern in _UNSAFE_PUBLIC_VALUE_PATTERNS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_SPECIALIST_TEAM_ROUTING_TAXONOMY_READINESS_CONFIG_VERSION",
    "MEDIUM_SCALE_SPECIALIST_TEAM_CATEGORIES",
    "SPECIALIST_TEAM_ROUTING_TAXONOMY_READINESS_STATUSES",
    "SpecialistTeamRoutingTaxonomyReadinessConfig",
    "SpecialistTeamRoutingTaxonomyReadinessInput",
    "SpecialistTeamRoutingTaxonomyReadinessReport",
    "SpecialistTeamRoutingTaxonomyReadinessRow",
    "build_specialist_team_routing_taxonomy_readiness_report",
    "specialist_team_routing_taxonomy_readiness_report_payload",
)
