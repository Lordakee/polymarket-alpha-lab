"""Report-only expertise gap router for collaborative research queues."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags
from polymarket_alpha_lab.team_taxonomy import (
    TEAM_IDS,
    TEAM_ID_TO_PRIMARY_CATEGORY,
    require_category_id,
    require_team_id,
)


DEFAULT_CONFIG_VERSION = "research-team-expertise-gap-router-v0"
DECIMAL_QUANT = Decimal("0.000001")
COUNT_QUANT = Decimal("1")
ZERO = Decimal("0")
ONE = Decimal("1")

PUBLIC_STATUSES = ("pass", "watch", "block")

WATCH_GAP_THRESHOLD = Decimal("0.250000")
BLOCK_GAP_THRESHOLD = Decimal("0.500000")

TEAM_TO_COLLABORATIVE_QUEUE = {
    "politics": "collab-politics-research",
    "crypto_btc": "collab-crypto-research",
    "crypto_eth": "collab-crypto-research",
    "macro_rates": "collab-macro-research",
    "equity_indices": "collab-equity-research",
    "commodities_gold": "collab-gold-research",
    "commodities_oil": "collab-oil-research",
    "sports_soccer": "collab-football-research",
    "sports_basketball": "collab-basketball-research",
    "sports_other": "collab-sports-research",
}

_TEAM_SORT_ORDER = {team_id: index for index, team_id in enumerate(TEAM_IDS)}
_STATUS_SORT_ORDER = {"pass": 0, "watch": 1, "block": 2}

_PUBLIC_FORBIDDEN_FRAGMENTS = frozenset(
    (
        "account",
        "auth",
        "buy",
        "candidate",
        "condition",
        "dsn",
        "market",
        "order",
        "position",
        "question",
        "recommend",
        "ref",
        "sell",
        "slug",
        "source",
        "supabase",
        "table",
        "text",
        "token",
        "trade",
        "trading",
        "url",
        "wallet",
    )
)

_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))


@dataclass(frozen=True)
class ResearchTeamExpertiseGapRouterConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    watch_gap_threshold: Decimal = WATCH_GAP_THRESHOLD
    block_gap_threshold: Decimal = BLOCK_GAP_THRESHOLD
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "watch_gap_threshold",
            _normalize_probability_decimal(
                "watch_gap_threshold",
                self.watch_gap_threshold,
            ),
        )
        object.__setattr__(
            self,
            "block_gap_threshold",
            _normalize_probability_decimal(
                "block_gap_threshold",
                self.block_gap_threshold,
            ),
        )
        if self.block_gap_threshold < self.watch_gap_threshold:
            raise ValueError("block_gap_threshold must be at least watch_gap_threshold")
        require_paper_only_flags("ResearchTeamExpertiseGapRouterConfig", self)


@dataclass(frozen=True)
class ResearchTeamExpertiseGapInput:
    raw_candidate_id: str
    market_id: str
    market_slug: str
    question: str
    source_ref: str
    source_text: str
    team_id: str
    category_id: str
    coverage_score: Decimal
    evidence_score: Decimal
    freshness_score: Decimal
    queue_priority_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "raw_candidate_id",
            "market_id",
            "market_slug",
            "question",
            "source_ref",
            "source_text",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        team_id = require_team_id("team_id", self.team_id)
        category_id = require_category_id("category_id", self.category_id)
        if TEAM_ID_TO_PRIMARY_CATEGORY[team_id] != category_id:
            raise ValueError("category_id must match team_id")
        object.__setattr__(self, "team_id", team_id)
        object.__setattr__(self, "category_id", category_id)
        for field_name in (
            "coverage_score",
            "evidence_score",
            "freshness_score",
            "queue_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        require_paper_only_flags("ResearchTeamExpertiseGapInput", self)


@dataclass(frozen=True)
class ResearchTeamExpertiseGapRouteRow:
    category_id: str
    team_id: str
    collaborative_queue: str
    public_status: str
    collaboration_required: bool
    coverage_score: Decimal
    evidence_score: Decimal
    freshness_score: Decimal
    queue_priority_score: Decimal
    expertise_gap_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        team_id = require_team_id("team_id", self.team_id)
        category_id = require_category_id("category_id", self.category_id)
        if TEAM_ID_TO_PRIMARY_CATEGORY[team_id] != category_id:
            raise ValueError("category_id must match team_id")
        object.__setattr__(self, "team_id", team_id)
        object.__setattr__(self, "category_id", category_id)
        _require_public_string("collaborative_queue", self.collaborative_queue)
        if self.collaborative_queue != TEAM_TO_COLLABORATIVE_QUEUE[team_id]:
            raise ValueError("collaborative_queue must match team_id")
        _require_public_status("public_status", self.public_status)
        if type(self.collaboration_required) is not bool:
            raise ValueError("collaboration_required must be a bool")
        for field_name in (
            "coverage_score",
            "evidence_score",
            "freshness_score",
            "queue_priority_score",
            "expertise_gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.expertise_gap_score != _expertise_gap_score(
            coverage_score=self.coverage_score,
            evidence_score=self.evidence_score,
            freshness_score=self.freshness_score,
        ):
            raise ValueError("expertise_gap_score must match coverage, evidence, and freshness")
        if self.collaboration_required != (self.public_status in ("watch", "block")):
            raise ValueError("collaboration_required must match public_status")
        require_paper_only_flags("ResearchTeamExpertiseGapRouteRow", self)
        _reject_unsafe_public_payload("ResearchTeamExpertiseGapRouteRow", self)


@dataclass(frozen=True)
class ResearchTeamExpertiseGapReport:
    generated_at: datetime
    config_version: str
    route_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    public_status: str
    rows: tuple[ResearchTeamExpertiseGapRouteRow, ...]
    reason_codes: tuple[str, ...]
    derived_public_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("route_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        _require_public_status("public_status", self.public_status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        require_paper_only_flags("ResearchTeamExpertiseGapReport", self)
        _validate_report_consistency(self)
        expected_digest = _public_digest_for_report(self)
        if self.derived_public_digest == "":
            object.__setattr__(self, "derived_public_digest", expected_digest)
        elif self.derived_public_digest != expected_digest:
            raise ValueError("derived_public_digest mismatch")
        _require_digest("derived_public_digest", self.derived_public_digest)
        _reject_unsafe_public_payload("ResearchTeamExpertiseGapReport", self)


def build_research_team_expertise_gap_report(
    inputs: tuple[ResearchTeamExpertiseGapInput, ...] | list[ResearchTeamExpertiseGapInput],
    *,
    config: ResearchTeamExpertiseGapRouterConfig,
    generated_at: datetime,
) -> ResearchTeamExpertiseGapReport:
    if type(config) is not ResearchTeamExpertiseGapRouterConfig:
        raise ValueError("config must be a ResearchTeamExpertiseGapRouterConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        _row_from_input(route_input, config=config)
        for route_input in sorted(_normalize_inputs(inputs), key=_input_sort_key)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchTeamExpertiseGapReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        route_count=_count(len(rows)),
        pass_count=_count(_status_count(rows, "pass")),
        watch_count=_count(_status_count(rows, "watch")),
        block_count=_count(_status_count(rows, "block")),
        public_status=_summary_status(rows),
        rows=rows,
        reason_codes=reason_codes,
    )


def research_team_expertise_gap_report_payload(
    report: ResearchTeamExpertiseGapReport,
) -> dict[str, object]:
    if type(report) is not ResearchTeamExpertiseGapReport:
        raise ValueError("report must be a ResearchTeamExpertiseGapReport")
    require_paper_only_flags("report", report)
    payload = _public_payload_for_report(report)
    _reject_unsafe_public_payload(
        "ResearchTeamExpertiseGapReport.payload",
        payload,
        allow_json_containers=True,
    )
    return payload


def research_team_expertise_gap_public_digest(
    value: ResearchTeamExpertiseGapReport | dict[str, object],
) -> str:
    if type(value) is ResearchTeamExpertiseGapReport:
        return _public_digest_for_report(value)
    if type(value) is dict:
        _reject_unsafe_public_payload(
            "ResearchTeamExpertiseGapReport.payload",
            value,
            allow_json_containers=True,
        )
        digest_payload = dict(value)
        digest_payload.pop("derived_public_digest", None)
        return _digest_payload(digest_payload)
    raise ValueError("value must be a ResearchTeamExpertiseGapReport or payload dict")


def _row_from_input(
    route_input: ResearchTeamExpertiseGapInput,
    *,
    config: ResearchTeamExpertiseGapRouterConfig,
) -> ResearchTeamExpertiseGapRouteRow:
    gap_score = _expertise_gap_score(
        coverage_score=route_input.coverage_score,
        evidence_score=route_input.evidence_score,
        freshness_score=route_input.freshness_score,
    )
    public_status = _row_status(
        gap_score=gap_score,
        queue_priority_score=route_input.queue_priority_score,
        config=config,
    )
    reason_codes = list(route_input.reason_codes)
    if public_status == "watch":
        reason_codes.append("expertise_gap_watch")
    elif public_status == "block":
        reason_codes.append("expertise_gap_block")
    else:
        reason_codes.append("expertise_gap_pass")
    return ResearchTeamExpertiseGapRouteRow(
        category_id=route_input.category_id,
        team_id=route_input.team_id,
        collaborative_queue=TEAM_TO_COLLABORATIVE_QUEUE[route_input.team_id],
        public_status=public_status,
        collaboration_required=public_status in ("watch", "block"),
        coverage_score=route_input.coverage_score,
        evidence_score=route_input.evidence_score,
        freshness_score=route_input.freshness_score,
        queue_priority_score=route_input.queue_priority_score,
        expertise_gap_score=gap_score,
        reason_codes=tuple(reason_codes),
    )


def _normalize_inputs(
    inputs: tuple[ResearchTeamExpertiseGapInput, ...] | list[ResearchTeamExpertiseGapInput],
) -> tuple[ResearchTeamExpertiseGapInput, ...]:
    if isinstance(inputs, (str, bytes)) or type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    items = tuple(inputs)
    for item in items:
        if type(item) is not ResearchTeamExpertiseGapInput:
            raise ValueError("inputs must contain ResearchTeamExpertiseGapInput values")
        require_paper_only_flags("ResearchTeamExpertiseGapInput", item)
    return items


def _normalize_rows(
    rows: tuple[ResearchTeamExpertiseGapRouteRow, ...],
) -> tuple[ResearchTeamExpertiseGapRouteRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchTeamExpertiseGapRouteRow:
            raise ValueError("rows must contain ResearchTeamExpertiseGapRouteRow values")
        require_paper_only_flags("ResearchTeamExpertiseGapRouteRow", row)
    return tuple(sorted(rows, key=_row_sort_key))


def _expertise_gap_score(
    *,
    coverage_score: Decimal,
    evidence_score: Decimal,
    freshness_score: Decimal,
) -> Decimal:
    weakest_score = min(coverage_score, evidence_score, freshness_score)
    return _quantize(ONE - weakest_score)


def _row_status(
    *,
    gap_score: Decimal,
    queue_priority_score: Decimal,
    config: ResearchTeamExpertiseGapRouterConfig,
) -> str:
    if gap_score >= config.block_gap_threshold or queue_priority_score >= Decimal("0.950000"):
        return "block"
    if gap_score >= config.watch_gap_threshold or queue_priority_score >= Decimal("0.700000"):
        return "watch"
    return "pass"


def _summary_status(rows: tuple[ResearchTeamExpertiseGapRouteRow, ...]) -> str:
    statuses = {row.public_status for row in rows}
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _summary_reason_codes(
    rows: tuple[ResearchTeamExpertiseGapRouteRow, ...],
) -> tuple[str, ...]:
    return tuple(sorted({reason_code for row in rows for reason_code in row.reason_codes}))


def _validate_report_consistency(report: ResearchTeamExpertiseGapReport) -> None:
    if report.route_count != _count(len(report.rows)):
        raise ValueError("route_count must match rows")
    if report.pass_count != _count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.public_status != _summary_status(report.rows):
        raise ValueError("public_status must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _public_payload_for_report(report: ResearchTeamExpertiseGapReport) -> dict[str, object]:
    rows = [
        {
            "category_id": row.category_id,
            "team_id": row.team_id,
            "collaborative_queue": row.collaborative_queue,
            "public_status": row.public_status,
            "collaboration_required": row.collaboration_required,
            "coverage_score": row.coverage_score,
            "evidence_score": row.evidence_score,
            "freshness_score": row.freshness_score,
            "queue_priority_score": row.queue_priority_score,
            "expertise_gap_score": row.expertise_gap_score,
            "reason_codes": row.reason_codes,
            "paper_only": row.paper_only,
            "report_only": row.report_only,
            "readonly": row.readonly,
        }
        for row in report.rows
    ]
    payload_without_digest = {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "route_count": report.route_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "public_status": report.public_status,
        "rows": rows,
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    payload = _json_ready(payload_without_digest)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload["derived_public_digest"] = _digest_payload(payload)
    return payload


def _public_digest_for_report(report: ResearchTeamExpertiseGapReport) -> str:
    payload = _public_payload_for_report_without_digest(report)
    return _digest_payload(payload)


def _public_payload_for_report_without_digest(
    report: ResearchTeamExpertiseGapReport,
) -> dict[str, object]:
    payload = _public_payload_for_report_unsafe(report)
    _reject_unsafe_public_payload(
        "ResearchTeamExpertiseGapReport.payload",
        payload,
        allow_json_containers=True,
    )
    return payload


def _public_payload_for_report_unsafe(report: ResearchTeamExpertiseGapReport) -> dict[str, object]:
    payload = {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "route_count": report.route_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "public_status": report.public_status,
        "rows": tuple(
            {
                "category_id": row.category_id,
                "team_id": row.team_id,
                "collaborative_queue": row.collaborative_queue,
                "public_status": row.public_status,
                "collaboration_required": row.collaboration_required,
                "coverage_score": row.coverage_score,
                "evidence_score": row.evidence_score,
                "freshness_score": row.freshness_score,
                "queue_priority_score": row.queue_priority_score,
                "expertise_gap_score": row.expertise_gap_score,
                "reason_codes": row.reason_codes,
                "paper_only": row.paper_only,
                "report_only": row.report_only,
                "readonly": row.readonly,
            }
            for row in report.rows
        ),
        "reason_codes": report.reason_codes,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    json_ready = _json_ready(payload)
    if type(json_ready) is not dict:
        raise ValueError("report payload must be a JSON object")
    return json_ready


def _digest_payload(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_ready(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if type(value) is str or type(value) is bool:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("JSON payload must use Decimal-derived string values")
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return _json_dict_ready(value)
    raise ValueError("value is not JSON serializable")


def _json_dict_ready(value: dict[Any, Any]) -> dict[str, object]:
    ready: dict[str, object] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        ready[key] = _json_ready(item)
    return ready


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            ResearchTeamExpertiseGapRouterConfig,
            ResearchTeamExpertiseGapRouteRow,
            ResearchTeamExpertiseGapReport,
        ):
            raise ValueError(f"{current_path} must be a supported public dataclass")
        for field in fields(value):
            if _has_unsafe_public_fragment(field.name):
                raise ValueError(f"{field.name} has unsafe public field")
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is dict:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{item_path} has unsafe public field")
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(
                label,
                item,
                item_path,
                allow_json_containers=True,
            )
        return
    if type(value) is list or type(value) is tuple:
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
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{current_path} must be timezone-aware")
        return
    if type(value) is str:
        if value.strip() != value or "://" in value or "?" in value:
            raise ValueError(f"{current_path} has unsafe public value")
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{current_path} has unsafe public value")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int or isinstance(value, float):
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    raise ValueError(f"{current_path} is not JSON-ready")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower().replace("-", "_")
    return any(fragment in normalized for fragment in _PUBLIC_FORBIDDEN_FRAGMENTS)


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(decimal_value)


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a nonnegative whole Decimal")
    return decimal_value.quantize(COUNT_QUANT)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANT)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(COUNT_QUANT)


def _status_count(rows: tuple[ResearchTeamExpertiseGapRouteRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.public_status == status)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_reason_codes(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must contain canonical public strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must contain canonical public strings") from exc
    if not items:
        raise ValueError(f"{field_name} must contain canonical public strings")
    for item in items:
        _require_public_string(field_name, item)
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must be unique")
    return tuple(sorted(items))


def _require_public_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if type(value) is str and _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _input_sort_key(
    value: ResearchTeamExpertiseGapInput,
) -> tuple[str, str, str, str, str, str]:
    return (
        value.team_id,
        value.category_id,
        value.raw_candidate_id,
        value.market_id,
        value.market_slug,
        value.source_ref,
    )


def _row_sort_key(
    value: ResearchTeamExpertiseGapRouteRow,
) -> tuple[int, int, str, str, str]:
    return (
        _STATUS_SORT_ORDER[value.public_status],
        _TEAM_SORT_ORDER[value.team_id],
        value.team_id,
        value.category_id,
        ",".join(value.reason_codes),
    )


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "PUBLIC_STATUSES",
    "TEAM_TO_COLLABORATIVE_QUEUE",
    "ResearchTeamExpertiseGapInput",
    "ResearchTeamExpertiseGapReport",
    "ResearchTeamExpertiseGapRouteRow",
    "ResearchTeamExpertiseGapRouterConfig",
    "build_research_team_expertise_gap_report",
    "research_team_expertise_gap_public_digest",
    "research_team_expertise_gap_report_payload",
)
