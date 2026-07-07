"""Report-only coverage gaps for research domain playbooks."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any, Iterable, Mapping, Sequence


DEFAULT_RESEARCH_DOMAIN_PLAYBOOK_GAP_CONFIG_VERSION = (
    "research-domain-playbook-gap-v1"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_FOUR = Decimal("4.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_DOMAIN_SEQUENCE = (
    "politics",
    "btc",
    "equity_index",
    "gold",
    "soccer",
    "basketball",
)
_STATUSES = frozenset(("pass", "watch", "block"))
_REASON_CODE_SEQUENCE = (
    "playbook_gap",
    "data_feed_gap",
    "settlement_rule_gap",
    "team_memory_gap",
    "domain_playbook_gap_pass",
)
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_TERMS = (
    "raw",
    "source",
    "market",
    "candidate",
    "dsn",
    "table",
    "token",
    "auth",
    "wallet",
    "order",
    "buy",
    "sell",
    "trade",
    "trading",
    "advice",
)


@dataclass(frozen=True)
class ResearchDomainPlaybookGapConfig:
    config_version: str = DEFAULT_RESEARCH_DOMAIN_PLAYBOOK_GAP_CONFIG_VERSION
    domain_slugs: tuple[str, ...] = _DOMAIN_SEQUENCE
    min_playbook_coverage_count: Decimal = Decimal("4.000000")
    min_data_feed_coverage_count: Decimal = Decimal("3.000000")
    min_settlement_rule_coverage_count: Decimal = Decimal("2.000000")
    min_team_memory_coverage_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchDomainPlaybookGapConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainPlaybookGapConfig:
            raise ValueError("config must be exactly ResearchDomainPlaybookGapConfig")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_DOMAIN_PLAYBOOK_GAP_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "domain_slugs",
            _normalize_domain_slugs("domain_slugs", self.domain_slugs),
        )
        for field_name in (
            "min_playbook_coverage_count",
            "min_data_feed_coverage_count",
            "min_settlement_rule_coverage_count",
            "min_team_memory_coverage_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchDomainPlaybookGapInput:
    domain_slug: str
    playbook_coverage_count: Decimal
    data_feed_coverage_count: Decimal
    settlement_rule_coverage_count: Decimal
    team_memory_coverage_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchDomainPlaybookGapInput does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainPlaybookGapInput:
            raise ValueError("input must be exactly ResearchDomainPlaybookGapInput")
        _require_supported_domain_slug("domain_slug", self.domain_slug)
        for field_name in _COVERAGE_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchDomainPlaybookGapRow:
    domain_slug: str
    playbook_coverage_count: Decimal
    data_feed_coverage_count: Decimal
    settlement_rule_coverage_count: Decimal
    team_memory_coverage_count: Decimal
    gap_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchDomainPlaybookGapRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainPlaybookGapRow:
            raise ValueError("row must be exactly ResearchDomainPlaybookGapRow")
        _require_supported_domain_slug("domain_slug", self.domain_slug)
        for field_name in _COVERAGE_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "gap_score", _require_ratio_decimal("gap_score", self.gap_score))
        _require_member("status", self.status, _STATUSES)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        if self.status != _row_status(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchDomainPlaybookGapReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchDomainPlaybookGapReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainPlaybookGapReasonCodeCount:
            raise ValueError(
                "reason count must be exactly ResearchDomainPlaybookGapReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchDomainPlaybookGapReport:
    generated_at: datetime
    config_version: str
    report_status: str
    domain_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    playbook_gap_count: Decimal
    data_feed_gap_count: Decimal
    settlement_rule_gap_count: Decimal
    team_memory_gap_count: Decimal
    min_gap_score: Decimal
    rows: tuple[ResearchDomainPlaybookGapRow, ...]
    reason_code_counts: tuple[ResearchDomainPlaybookGapReasonCodeCount, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchDomainPlaybookGapReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainPlaybookGapReport:
            raise ValueError("report must be exactly ResearchDomainPlaybookGapReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_DOMAIN_PLAYBOOK_GAP_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_member("report_status", self.report_status, _STATUSES)
        for field_name in (
            "domain_count",
            "pass_count",
            "watch_count",
            "block_count",
            "playbook_gap_count",
            "data_feed_gap_count",
            "settlement_rule_gap_count",
            "team_memory_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_gap_score",
            _require_ratio_decimal("min_gap_score", self.min_gap_score),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
            return
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")

    @property
    def payload(self) -> dict[str, Any]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchDomainPlaybookGapReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a JSON object")
        return payload


_COVERAGE_FIELDS = (
    "playbook_coverage_count",
    "data_feed_coverage_count",
    "settlement_rule_coverage_count",
    "team_memory_coverage_count",
)


def build_research_domain_playbook_gap_report(
    rows: Iterable[ResearchDomainPlaybookGapInput],
    *,
    generated_at: datetime,
    config: ResearchDomainPlaybookGapConfig | None = None,
) -> ResearchDomainPlaybookGapReport:
    """Build a deterministic report-only domain playbook coverage snapshot."""

    if config is None:
        config = ResearchDomainPlaybookGapConfig()
    if type(config) is not ResearchDomainPlaybookGapConfig:
        raise ValueError("config must be a ResearchDomainPlaybookGapConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(rows, config)
    gap_rows = tuple(_row_for_input(item, config) for item in normalized_inputs)
    reason_code_counts = _reason_code_counts(gap_rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "report_status": _report_status(gap_rows),
        "domain_count": _decimal_count(len(gap_rows)),
        "pass_count": _status_count(gap_rows, "pass"),
        "watch_count": _status_count(gap_rows, "watch"),
        "block_count": _status_count(gap_rows, "block"),
        "playbook_gap_count": _reason_count(gap_rows, "playbook_gap"),
        "data_feed_gap_count": _reason_count(gap_rows, "data_feed_gap"),
        "settlement_rule_gap_count": _reason_count(gap_rows, "settlement_rule_gap"),
        "team_memory_gap_count": _reason_count(gap_rows, "team_memory_gap"),
        "min_gap_score": min((row.gap_score for row in gap_rows), default=_ZERO),
        "rows": gap_rows,
        "reason_code_counts": reason_code_counts,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchDomainPlaybookGapReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _row_for_input(
    item: ResearchDomainPlaybookGapInput,
    config: ResearchDomainPlaybookGapConfig,
) -> ResearchDomainPlaybookGapRow:
    reason_codes = _row_reason_codes(item, config)
    return ResearchDomainPlaybookGapRow(
        domain_slug=item.domain_slug,
        playbook_coverage_count=item.playbook_coverage_count,
        data_feed_coverage_count=item.data_feed_coverage_count,
        settlement_rule_coverage_count=item.settlement_rule_coverage_count,
        team_memory_coverage_count=item.team_memory_coverage_count,
        gap_score=_gap_score(item, config),
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchDomainPlaybookGapInput,
    config: ResearchDomainPlaybookGapConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if item.playbook_coverage_count < config.min_playbook_coverage_count:
        reason_codes.append("playbook_gap")
    if item.data_feed_coverage_count < config.min_data_feed_coverage_count:
        reason_codes.append("data_feed_gap")
    if item.settlement_rule_coverage_count < config.min_settlement_rule_coverage_count:
        reason_codes.append("settlement_rule_gap")
    if item.team_memory_coverage_count < config.min_team_memory_coverage_count:
        reason_codes.append("team_memory_gap")
    if not reason_codes:
        return ("domain_playbook_gap_pass",)
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        "playbook_gap" in reason_codes
        or "data_feed_gap" in reason_codes
        or "settlement_rule_gap" in reason_codes
    ):
        return "block"
    if reason_codes == ("team_memory_gap",):
        return "watch"
    if reason_codes == ("domain_playbook_gap_pass",):
        return "pass"
    return "block"


def _report_status(rows: tuple[ResearchDomainPlaybookGapRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _gap_score(
    item: ResearchDomainPlaybookGapInput,
    config: ResearchDomainPlaybookGapConfig,
) -> Decimal:
    ratios = (
        _coverage_ratio(
            item.playbook_coverage_count,
            config.min_playbook_coverage_count,
        ),
        _coverage_ratio(
            item.data_feed_coverage_count,
            config.min_data_feed_coverage_count,
        ),
        _coverage_ratio(
            item.settlement_rule_coverage_count,
            config.min_settlement_rule_coverage_count,
        ),
        _coverage_ratio(
            item.team_memory_coverage_count,
            config.min_team_memory_coverage_count,
        ),
    )
    with localcontext() as context:
        context.prec = 64
        return _clamp_ratio(sum(ratios, _ZERO) / _FOUR)


def _coverage_ratio(value: Decimal, minimum: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 64
        return _clamp_ratio(value / minimum)


def _normalize_inputs(
    rows: Iterable[ResearchDomainPlaybookGapInput],
    config: ResearchDomainPlaybookGapConfig,
) -> tuple[ResearchDomainPlaybookGapInput, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable of ResearchDomainPlaybookGapInput")
    by_domain: dict[str, ResearchDomainPlaybookGapInput] = {}
    for item in rows:
        if type(item) is not ResearchDomainPlaybookGapInput:
            raise ValueError("rows must contain ResearchDomainPlaybookGapInput")
        _require_hard_flags("input", item)
        if item.domain_slug in by_domain:
            raise ValueError("duplicate domain_slug")
        if item.domain_slug not in config.domain_slugs:
            raise ValueError("domain_slug must be a supported domain_slug")
        by_domain[item.domain_slug] = item
    return tuple(
        by_domain.get(domain_slug) or _empty_input_for_domain(domain_slug)
        for domain_slug in config.domain_slugs
    )


def _empty_input_for_domain(domain_slug: str) -> ResearchDomainPlaybookGapInput:
    return ResearchDomainPlaybookGapInput(
        domain_slug=domain_slug,
        playbook_coverage_count=_ZERO,
        data_feed_coverage_count=_ZERO,
        settlement_rule_coverage_count=_ZERO,
        team_memory_coverage_count=_ZERO,
    )


def _reason_code_counts(
    rows: tuple[ResearchDomainPlaybookGapRow, ...],
) -> tuple[ResearchDomainPlaybookGapReasonCodeCount, ...]:
    return tuple(
        ResearchDomainPlaybookGapReasonCodeCount(
            reason_code,
            _reason_count(rows, reason_code),
        )
        for reason_code in _REASON_CODE_SEQUENCE
        if _reason_count(rows, reason_code) > _ZERO
    )


def _normalize_rows(
    rows: object,
) -> tuple[ResearchDomainPlaybookGapRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    if not rows:
        raise ValueError("rows must not be empty")
    normalized: list[ResearchDomainPlaybookGapRow] = []
    seen: set[str] = set()
    for item in rows:
        if type(item) is not ResearchDomainPlaybookGapRow:
            raise ValueError("rows must contain ResearchDomainPlaybookGapRow")
        if item.domain_slug in seen:
            raise ValueError("duplicate domain_slug")
        seen.add(item.domain_slug)
        normalized.append(item)
    return tuple(normalized)


def _normalize_reason_code_counts(
    values: object,
) -> tuple[ResearchDomainPlaybookGapReasonCodeCount, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[ResearchDomainPlaybookGapReasonCodeCount] = []
    seen: set[str] = set()
    for item in values:
        if type(item) is not ResearchDomainPlaybookGapReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchDomainPlaybookGapReasonCodeCount",
            )
        if item.reason_code in seen:
            raise ValueError("duplicate reason_code")
        seen.add(item.reason_code)
        normalized.append(item)
    return tuple(
        item
        for reason_code in _REASON_CODE_SEQUENCE
        for item in normalized
        if item.reason_code == reason_code
    )


def _validate_report_consistency(report: ResearchDomainPlaybookGapReport) -> None:
    rows = report.rows
    if report.domain_count != _decimal_count(len(rows)):
        raise ValueError("domain_count must match rows")
    for status_name, field_name in (
        ("pass", "pass_count"),
        ("watch", "watch_count"),
        ("block", "block_count"),
    ):
        if getattr(report, field_name) != _status_count(rows, status_name):
            raise ValueError(f"{field_name} must match rows")
    for reason_code, field_name in (
        ("playbook_gap", "playbook_gap_count"),
        ("data_feed_gap", "data_feed_gap_count"),
        ("settlement_rule_gap", "settlement_rule_gap_count"),
        ("team_memory_gap", "team_memory_gap_count"),
    ):
        if getattr(report, field_name) != _reason_count(rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.min_gap_score != min(row.gap_score for row in rows):
        raise ValueError("min_gap_score must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _status_count(
    rows: tuple[ResearchDomainPlaybookGapRow, ...],
    status_name: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status_name))


def _reason_count(
    rows: tuple[ResearchDomainPlaybookGapRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _normalize_domain_slugs(field_name: str, values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for value in values:
        _require_supported_domain_slug(field_name, value)
        if value in normalized:
            raise ValueError(f"{field_name} must not contain duplicates")
        normalized.append(value)
    return tuple(normalized)


def _require_supported_domain_slug(field_name: str, value: object) -> str:
    value = _require_public_identifier(field_name, value)
    if value not in _DOMAIN_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported domain_slug")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    value = _require_public_identifier(field_name, value)
    if value not in _REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a supported reason code")
    return value


def _require_member(field_name: str, value: object, allowed: frozenset[str]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be supported")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized != value:
        raise ValueError(f"{field_name} must have six-decimal precision")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value().quantize(_QUANT):
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(_QUANT)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _report_values_without_digest(
    report: ResearchDomainPlaybookGapReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
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
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
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
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_PLAYBOOK_GAP_CONFIG_VERSION",
    "ResearchDomainPlaybookGapConfig",
    "ResearchDomainPlaybookGapInput",
    "ResearchDomainPlaybookGapReasonCodeCount",
    "ResearchDomainPlaybookGapReport",
    "ResearchDomainPlaybookGapRow",
    "build_research_domain_playbook_gap_report",
)
