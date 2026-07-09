"""Pure report reducer for strategy team confidence routing."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_STRATEGY_TEAM_CONFIDENCE_ROUTER_CONFIG_VERSION = (
    "research-strategy-team-confidence-router-report-v1"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_FOUR = Decimal("4.000000")
_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PRIVATE_REFERENCE = "<redacted-private-trace>"
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_PUBLIC_REPORT_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "status",
        "item_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_router_score",
        "rows",
        "reason_codes",
        "validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_PUBLIC_ROW_FIELDS = frozenset(
    (
        "claim_id",
        "team_id",
        "standing_score",
        "confidence_score",
        "freshness_score",
        "independence_score",
        "router_score",
        "route_status",
        "private_reference",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "can" "didate",
    "mar" "ket",
    "sou" "rce",
    "u" "rl",
    "te" "xt",
    "d" "sn",
    "ta" "ble",
    "tok" "en",
    "d" "b",
    "data" "base",
    "net" "work",
    "wal" "let",
    "au" "th",
    "or" "der",
    "li" "ve",
    "trad" "ing",
    "siz" "ing",
    "reco" "mmendation",
)
_REASON_SEQUENCE = (
    "empty_inputs",
    "confidence_below_floor",
    "router_score_below_floor",
    "standing_watch",
    "confidence_watch",
    "freshness_watch",
    "independence_watch",
    "router_score_watch",
    "router_pass",
)


@dataclass(frozen=True)
class ResearchStrategyTeamConfidenceRouterConfig:
    config_version: str = DEFAULT_RESEARCH_STRATEGY_TEAM_CONFIDENCE_ROUTER_CONFIG_VERSION
    min_pass_score: Decimal = Decimal("0.800000")
    min_watch_score: Decimal = Decimal("0.650000")
    confidence_floor: Decimal = Decimal("0.250000")
    component_watch_floor: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamConfidenceRouterConfig:
            raise TypeError("config does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyTeamConfidenceRouterConfig:
            raise ValueError("config must be exact")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_STRATEGY_TEAM_CONFIDENCE_ROUTER_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        for field_name in (
            "min_pass_score",
            "min_watch_score",
            "confidence_floor",
            "component_watch_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_score > self.min_pass_score:
            raise ValueError("min_watch_score must not exceed min_pass_score")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyTeamConfidenceRouterInput:
    claim_id: str
    team_id: str
    standing_score: Decimal
    confidence_score: Decimal
    freshness_score: Decimal
    independence_score: Decimal
    private_trace: str = _PRIVATE_REFERENCE
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamConfidenceRouterInput:
            raise TypeError("input does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyTeamConfidenceRouterInput:
            raise ValueError("input must be exact")
        _require_public_identifier("claim_id", self.claim_id)
        _require_public_identifier("team_id", self.team_id)
        for field_name in (
            "standing_score",
            "confidence_score",
            "freshness_score",
            "independence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_private_trace(self.private_trace)
        object.__setattr__(self, "private_trace", _PRIVATE_REFERENCE)
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyTeamConfidenceRouterRow:
    claim_id: str
    team_id: str
    standing_score: Decimal
    confidence_score: Decimal
    freshness_score: Decimal
    independence_score: Decimal
    router_score: Decimal
    route_status: str
    private_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamConfidenceRouterRow:
            raise TypeError("row does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyTeamConfidenceRouterRow:
            raise ValueError("row must be exact")
        _require_public_identifier("claim_id", self.claim_id)
        _require_public_identifier("team_id", self.team_id)
        for field_name in (
            "standing_score",
            "confidence_score",
            "freshness_score",
            "independence_score",
            "router_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("route_status", self.route_status)
        object.__setattr__(self, "private_reference", _PRIVATE_REFERENCE)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyTeamConfidenceRouterReport:
    generated_at: datetime
    config_version: str
    status: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_router_score: Decimal
    rows: tuple[ResearchStrategyTeamConfidenceRouterRow, ...]
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamConfidenceRouterReport:
            raise TypeError("report does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyTeamConfidenceRouterReport:
            raise ValueError("report must be exact")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_STRATEGY_TEAM_CONFIDENCE_ROUTER_CONFIG_VERSION:
            raise ValueError("config_version must be supported")
        _require_status("status", self.status)
        for field_name in ("item_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_router_score",
            _require_ratio_decimal("average_router_score", self.average_router_score),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_sha256_digest("validation_digest", self.validation_digest)
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_from_values(_report_values_without_digest(self))
        if self.validation_digest != expected_digest:
            raise ValueError("validation_digest does not match payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_strategy_team_confidence_router_report(
    items: Sequence[ResearchStrategyTeamConfidenceRouterInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyTeamConfidenceRouterConfig | None = None,
) -> ResearchStrategyTeamConfidenceRouterReport:
    if config is None:
        config = ResearchStrategyTeamConfidenceRouterConfig()
    if type(config) is not ResearchStrategyTeamConfidenceRouterConfig:
        raise ValueError("config must be ResearchStrategyTeamConfidenceRouterConfig")
    generated_at = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_items(items)
    rows = tuple(
        sorted(
            (_row_for_item(item, config) for item in normalized_items),
            key=_row_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "status": _report_status(rows),
        "item_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_router_score": _average(tuple(row.router_score for row in rows)),
        "rows": rows,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyTeamConfidenceRouterReport(
        **values,
        validation_digest=_digest_from_values(values),
    )


def verify_research_strategy_team_confidence_router_payload(payload: object) -> bool:
    if type(payload) is not dict:
        return False
    try:
        _reject_unsafe_public_payload(
            "public payload",
            payload,
            allow_json_containers=True,
        )
        report = _report_from_public_payload(payload)
        return report.payload == payload
    except ValueError:
        return False


def _report_from_public_payload(
    payload: dict[str, object],
) -> ResearchStrategyTeamConfidenceRouterReport:
    _require_exact_public_fields("public payload", payload, _PUBLIC_REPORT_FIELDS)
    rows_value = _require_public_list("rows", payload["rows"])
    reason_codes_value = _require_public_list("reason_codes", payload["reason_codes"])
    return ResearchStrategyTeamConfidenceRouterReport(
        generated_at=_datetime_from_public_value("generated_at", payload["generated_at"]),
        config_version=payload["config_version"],  # type: ignore[arg-type]
        status=payload["status"],  # type: ignore[arg-type]
        item_count=_decimal_from_public_value("item_count", payload["item_count"]),
        pass_count=_decimal_from_public_value("pass_count", payload["pass_count"]),
        watch_count=_decimal_from_public_value("watch_count", payload["watch_count"]),
        block_count=_decimal_from_public_value("block_count", payload["block_count"]),
        average_router_score=_decimal_from_public_value(
            "average_router_score",
            payload["average_router_score"],
        ),
        rows=tuple(_row_from_public_payload(row) for row in rows_value),
        reason_codes=tuple(reason_codes_value),  # type: ignore[arg-type]
        validation_digest=payload["validation_digest"],  # type: ignore[arg-type]
        paper_only=_require_public_true("paper_only", payload["paper_only"]),
        report_only=_require_public_true("report_only", payload["report_only"]),
        readonly=_require_public_true("readonly", payload["readonly"]),
    )


def _row_from_public_payload(
    value: object,
) -> ResearchStrategyTeamConfidenceRouterRow:
    if type(value) is not dict:
        raise ValueError("rows must contain JSON objects")
    _require_exact_public_fields("row", value, _PUBLIC_ROW_FIELDS)
    reason_codes_value = _require_public_list("row.reason_codes", value["reason_codes"])
    row = ResearchStrategyTeamConfidenceRouterRow(
        claim_id=value["claim_id"],  # type: ignore[arg-type]
        team_id=value["team_id"],  # type: ignore[arg-type]
        standing_score=_decimal_from_public_value(
            "standing_score",
            value["standing_score"],
        ),
        confidence_score=_decimal_from_public_value(
            "confidence_score",
            value["confidence_score"],
        ),
        freshness_score=_decimal_from_public_value(
            "freshness_score",
            value["freshness_score"],
        ),
        independence_score=_decimal_from_public_value(
            "independence_score",
            value["independence_score"],
        ),
        router_score=_decimal_from_public_value(
            "router_score",
            value["router_score"],
        ),
        route_status=value["route_status"],  # type: ignore[arg-type]
        private_reference=value["private_reference"],  # type: ignore[arg-type]
        reason_codes=tuple(reason_codes_value),  # type: ignore[arg-type]
        paper_only=_require_public_true("row.paper_only", value["paper_only"]),
        report_only=_require_public_true("row.report_only", value["report_only"]),
        readonly=_require_public_true("row.readonly", value["readonly"]),
    )
    if _json_ready(asdict(row)) != value:
        raise ValueError("row must use canonical public values")
    return row


def _require_exact_public_fields(
    label: str,
    value: dict[object, object],
    expected_fields: frozenset[str],
) -> None:
    if set(value) != expected_fields:
        raise ValueError(f"{label} must use the exact public schema")


def _require_public_list(field_name: str, value: object) -> list[object]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return value


def _require_public_true(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _decimal_from_public_value(field_name: str, value: object) -> Decimal:
    if type(value) is not str or not re.fullmatch(r"(?:0|[1-9][0-9]*)\.[0-9]{6}", value):
        raise ValueError(f"{field_name} must be a six-decimal string")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc


def _datetime_from_public_value(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    parsed = datetime.fromisoformat(value)
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must use canonical UTC format")
    return normalized


def _row_for_item(
    item: ResearchStrategyTeamConfidenceRouterInput,
    config: ResearchStrategyTeamConfidenceRouterConfig,
) -> ResearchStrategyTeamConfidenceRouterRow:
    router_score = _average(
        (
            item.standing_score,
            item.confidence_score,
            item.freshness_score,
            item.independence_score,
        ),
    )
    reason_codes = _row_reason_codes(item, router_score, config)
    return ResearchStrategyTeamConfidenceRouterRow(
        claim_id=item.claim_id,
        team_id=item.team_id,
        standing_score=item.standing_score,
        confidence_score=item.confidence_score,
        freshness_score=item.freshness_score,
        independence_score=item.independence_score,
        router_score=router_score,
        route_status=_row_status(reason_codes),
        private_reference=_PRIVATE_REFERENCE,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchStrategyTeamConfidenceRouterInput,
    router_score: Decimal,
    config: ResearchStrategyTeamConfidenceRouterConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if item.confidence_score < config.confidence_floor:
        reasons.append("confidence_below_floor")
    if router_score < config.min_watch_score:
        reasons.append("router_score_below_floor")
    if reasons:
        return _normalize_reason_codes(tuple(reasons))
    if item.standing_score < config.component_watch_floor:
        reasons.append("standing_watch")
    if item.confidence_score < config.component_watch_floor:
        reasons.append("confidence_watch")
    if item.freshness_score < config.component_watch_floor:
        reasons.append("freshness_watch")
    if item.independence_score < config.component_watch_floor:
        reasons.append("independence_watch")
    if router_score < config.min_pass_score:
        reasons.append("router_score_watch")
    if reasons:
        return _normalize_reason_codes(tuple(reasons))
    return ("router_pass",)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        "confidence_below_floor" in reason_codes
        or "router_score_below_floor" in reason_codes
    ):
        return "block"
    if reason_codes != ("router_pass",):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchStrategyTeamConfidenceRouterRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.route_status == "block" for row in rows):
        return "block"
    if any(row.route_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyTeamConfidenceRouterRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_inputs",)
    reasons: list[str] = []
    for row in rows:
        reasons.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reasons))


def _status_count(
    rows: tuple[ResearchStrategyTeamConfidenceRouterRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.route_status == status)


def _normalize_items(
    items: Sequence[ResearchStrategyTeamConfidenceRouterInput],
) -> tuple[ResearchStrategyTeamConfidenceRouterInput, ...]:
    if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
        raise ValueError("items must be a sequence")
    normalized: list[ResearchStrategyTeamConfidenceRouterInput] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        if type(item) is not ResearchStrategyTeamConfidenceRouterInput:
            raise ValueError("items must contain ResearchStrategyTeamConfidenceRouterInput")
        _require_hard_flags("input", item)
        key = (item.claim_id, item.team_id)
        if key in seen:
            raise ValueError("duplicate claim_id and team_id")
        seen.add(key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: (item.claim_id, item.team_id)))


def _normalize_rows(
    rows: Sequence[ResearchStrategyTeamConfidenceRouterRow],
) -> tuple[ResearchStrategyTeamConfidenceRouterRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchStrategyTeamConfidenceRouterRow] = []
    for row in rows:
        if type(row) is not ResearchStrategyTeamConfidenceRouterRow:
            raise ValueError("rows must contain ResearchStrategyTeamConfidenceRouterRow")
        _require_hard_flags("row", row)
        normalized.append(row)
    expected = tuple(sorted(normalized, key=_row_key))
    if tuple(normalized) != expected:
        raise ValueError("rows must use deterministic sequence")
    return tuple(normalized)


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(reason for reason in _REASON_SEQUENCE if reason in normalized)


def _validate_row(row: ResearchStrategyTeamConfidenceRouterRow) -> None:
    expected_score = _average(
        (
            row.standing_score,
            row.confidence_score,
            row.freshness_score,
            row.independence_score,
        ),
    )
    if row.router_score != expected_score:
        raise ValueError("router_score must match component scores")
    if row.route_status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.private_reference != _PRIVATE_REFERENCE:
        raise ValueError("private_reference must be redacted")


def _validate_report(report: ResearchStrategyTeamConfidenceRouterReport) -> None:
    if report.item_count != _decimal_count(len(report.rows)):
        raise ValueError("item_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_router_score != _average(tuple(row.router_score for row in report.rows)):
        raise ValueError("average_router_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _row_key(row: ResearchStrategyTeamConfidenceRouterRow) -> tuple[int, str, str]:
    return (_STATUS_RANK[row.route_status], row.claim_id, row.team_id)


def _report_values_without_digest(
    report: ResearchStrategyTeamConfidenceRouterReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("validation_digest", None)
    return values


def _digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload("digest payload", payload, allow_json_containers=True)
    return _sha256_public_payload(payload)


def _digest_from_public_values(values: Mapping[str, object]) -> str:
    _reject_unsafe_public_payload("digest payload", values, allow_json_containers=True)
    payload = _json_ready(values)
    return _sha256_public_payload(payload)


def _sha256_public_payload(payload: object) -> str:
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
    if type(value) is bool:
        return value
    if type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must use Decimal strings")
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
        if current_path.endswith("validation_digest"):
            return
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
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_private_trace(value: object) -> None:
    if type(value) is not str:
        raise ValueError("private_trace must be a string")
    if value.strip() != value or not value:
        raise ValueError("private_trace must be nonblank")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_RANK:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_TEAM_CONFIDENCE_ROUTER_CONFIG_VERSION",
    "ResearchStrategyTeamConfidenceRouterConfig",
    "ResearchStrategyTeamConfidenceRouterInput",
    "ResearchStrategyTeamConfidenceRouterReport",
    "ResearchStrategyTeamConfidenceRouterRow",
    "build_research_strategy_team_confidence_router_report",
    "verify_research_strategy_team_confidence_router_payload",
)
