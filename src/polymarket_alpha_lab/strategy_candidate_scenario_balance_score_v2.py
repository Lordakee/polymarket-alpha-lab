from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    require_paper_only_flags,
)


DEFAULT_STRATEGY_CANDIDATE_SCENARIO_BALANCE_SCORE_V2_CONFIG_VERSION = (
    "strategy-candidate-scenario-balance-score-v2"
)

SCENARIOS = ("bull", "base", "bear")
SOURCE_KINDS = ("research", "model", "survey", "market", "other")
ROW_STATUSES = ("pass", "watch", "block")
REPORT_STATUSES = ROW_STATUSES
EVIDENCE_REASON_CODES = ("candidate_evidence",)
ROW_REASON_CODE_SEQUENCE = (
    "scenario_balance_pass",
    "scenario_balance_watch",
    "scenario_balance_block",
    "bull_base_bear_evidence_present",
    "missing_bull_scenario",
    "missing_base_scenario",
    "missing_bear_scenario",
    "one_sided_evidence_penalty",
    "balanced_source_boost",
)
REPORT_REASON_CODE_SEQUENCE = (
    "scenario_balance_report_empty",
    "scenario_balance_report_pass",
    "scenario_balance_report_watch",
    "scenario_balance_report_block",
    "bull_base_bear_evidence_present",
    "missing_bull_scenario",
    "missing_base_scenario",
    "missing_bear_scenario",
    "one_sided_evidence_penalty",
    "balanced_source_boost",
)

_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_COUNT_QUANTUM = Decimal("1")
_RATIO_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_SIZE = 32
_UNSAFE_PUBLIC_PARTS = frozenset(
    (
        "li" "ve",
        "au" "th",
        "wal" "let",
        "or" "der",
        "net" "work",
        "data" "base",
        "per" "sist",
        "sig" "ning",
        "muta" "tion",
        "bu" "y",
        "se" "ll",
        "tra" "de",
    ),
)


@dataclass(frozen=True)
class StrategyCandidateScenarioBalanceScoreV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_CANDIDATE_SCENARIO_BALANCE_SCORE_V2_CONFIG_VERSION
    )
    watch_score_threshold: Decimal = Decimal("0.400000")
    pass_score_threshold: Decimal = Decimal("0.700000")
    missing_scenario_penalty: Decimal = Decimal("0.150000")
    one_sided_share_threshold: Decimal = Decimal("0.800000")
    one_sided_penalty_scale: Decimal = Decimal("0.500000")
    balanced_source_boost: Decimal = Decimal("0.050000")
    min_balanced_source_kind_count: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_score_threshold",
            "pass_score_threshold",
            "missing_scenario_penalty",
            "one_sided_share_threshold",
            "one_sided_penalty_scale",
            "balanced_source_boost",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_balanced_source_kind_count",
            _normalize_nonnegative_count(
                "min_balanced_source_kind_count",
                self.min_balanced_source_kind_count,
            ),
        )
        if self.watch_score_threshold > self.pass_score_threshold:
            raise ValueError("pass_score_threshold must be at least watch_score_threshold")
        require_paper_only_flags("config", self)
        validate_strategy_candidate_scenario_balance_score_v2_public_payload(
            {"config_version": self.config_version},
        )


@dataclass(frozen=True)
class StrategyCandidateScenarioBalanceScoreV2Evidence:
    candidate_reference: str
    scenario: str
    source_reference: str
    source_kind: str
    evidence_weight: Decimal
    confidence_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...] = ("candidate_evidence",)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_reference", self.candidate_reference)
        _require_member("scenario", self.scenario, SCENARIOS)
        _require_canonical_string("source_reference", self.source_reference)
        _require_member("source_kind", self.source_kind, SOURCE_KINDS)
        object.__setattr__(
            self,
            "evidence_weight",
            _normalize_nonnegative_decimal("evidence_weight", self.evidence_weight),
        )
        object.__setattr__(
            self,
            "confidence_score",
            _normalize_unit_decimal("confidence_score", self.confidence_score),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                EVIDENCE_REASON_CODES,
                require_nonempty=True,
            ),
        )
        require_paper_only_flags("evidence", self)
        validate_strategy_candidate_scenario_balance_score_v2_public_payload(self)


@dataclass(frozen=True)
class StrategyCandidateScenarioBalanceScoreV2Row:
    candidate_reference: str
    latest_observed_at: datetime | None
    evidence_count: Decimal
    source_kind_count: Decimal
    total_evidence_weight: Decimal
    bull_scenario_weight: Decimal
    base_scenario_weight: Decimal
    bear_scenario_weight: Decimal
    bull_scenario_share: Decimal
    base_scenario_share: Decimal
    bear_scenario_share: Decimal
    scenario_imbalance_gap: Decimal
    one_sided_evidence_penalty: Decimal
    balanced_source_boost: Decimal
    scenario_balance_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_reference", self.candidate_reference)
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_optional_utc("latest_observed_at", self.latest_observed_at),
        )
        for field_name in (
            "evidence_count",
            "source_kind_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_evidence_weight",
            "bull_scenario_weight",
            "base_scenario_weight",
            "bear_scenario_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "bull_scenario_share",
            "base_scenario_share",
            "bear_scenario_share",
            "scenario_imbalance_gap",
            "one_sided_evidence_penalty",
            "balanced_source_boost",
            "scenario_balance_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                ROW_REASON_CODE_SEQUENCE,
                require_nonempty=True,
            ),
        )
        _validate_row_consistency(self)
        require_paper_only_flags("row", self)
        expected_digest = _digest_for_value(_digestable_dataclass(self))
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match row values")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        validate_strategy_candidate_scenario_balance_score_v2_public_payload(self)


@dataclass(frozen=True)
class StrategyCandidateScenarioBalanceScoreV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_scenario_balance_score: Decimal
    max_scenario_imbalance_gap: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyCandidateScenarioBalanceScoreV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_scenario_balance_score",
            "max_scenario_imbalance_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODE_SEQUENCE,
                require_nonempty=True,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        require_paper_only_flags("report", self)
        expected_digest = _digest_for_value(_digestable_dataclass(self))
        if self.derived_validation_digest:
            _require_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report values")
        else:
            _validate_report_consistency(self)
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        _validate_report_consistency(self)
        validate_strategy_candidate_scenario_balance_score_v2_public_payload(self)


def build_strategy_candidate_scenario_balance_score_v2(
    items: list[StrategyCandidateScenarioBalanceScoreV2Evidence]
    | tuple[StrategyCandidateScenarioBalanceScoreV2Evidence, ...],
    *,
    config: StrategyCandidateScenarioBalanceScoreV2Config,
    generated_at: datetime,
) -> StrategyCandidateScenarioBalanceScoreV2Report:
    if type(config) is not StrategyCandidateScenarioBalanceScoreV2Config:
        raise ValueError("config must be a StrategyCandidateScenarioBalanceScoreV2Config")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_items(items)
    grouped = _group_items(normalized_items)
    rows = tuple(
        _build_row(candidate_reference, candidate_items, config=config)
        for candidate_reference, candidate_items in sorted(grouped.items())
    )
    candidate_count = _count(len(rows))
    pass_count = _count(sum(1 for row in rows if row.status == "pass"))
    watch_count = _count(sum(1 for row in rows if row.status == "watch"))
    block_count = _count(sum(1 for row in rows if row.status == "block"))
    average_score = _average(row.scenario_balance_score for row in rows)
    max_gap = _max_decimal(row.scenario_imbalance_gap for row in rows)
    return StrategyCandidateScenarioBalanceScoreV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=candidate_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        average_scenario_balance_score=average_score,
        max_scenario_imbalance_gap=max_gap,
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def strategy_candidate_scenario_balance_score_v2_payload(
    report: StrategyCandidateScenarioBalanceScoreV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyCandidateScenarioBalanceScoreV2Report:
        raise ValueError("report must be a StrategyCandidateScenarioBalanceScoreV2Report")
    require_paper_only_flags("report", report)
    validate_strategy_candidate_scenario_balance_score_v2_public_payload(report)
    payload = json_ready_no_floats(report)
    validate_strategy_candidate_scenario_balance_score_v2_public_payload(payload)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def validate_strategy_candidate_scenario_balance_score_v2_public_payload(
    payload: object,
) -> None:
    for key, value in _iter_public_key_values(payload):
        if _contains_unsafe_public_part(key) or _contains_unsafe_public_part(value):
            raise ValueError("unsafe public payload content")


def _build_row(
    candidate_reference: str,
    items: tuple[StrategyCandidateScenarioBalanceScoreV2Evidence, ...],
    *,
    config: StrategyCandidateScenarioBalanceScoreV2Config,
) -> StrategyCandidateScenarioBalanceScoreV2Row:
    scenario_weights = {
        scenario: _weighted_scenario_amount(items, scenario)
        for scenario in SCENARIOS
    }
    total_weight = _normalize_nonnegative_decimal(
        "total_evidence_weight",
        sum(scenario_weights.values(), _ZERO),
    )
    shares = {
        scenario: _ratio(weight, total_weight)
        for scenario, weight in scenario_weights.items()
    }
    share_values = tuple(shares.values())
    scenario_gap = (
        _ZERO
        if total_weight == _ZERO
        else _normalize_unit_decimal(
            "scenario_imbalance_gap",
            max(share_values) - min(share_values),
        )
    )
    missing_count = _count(sum(1 for share in share_values if share == _ZERO))
    max_share = _ZERO if total_weight == _ZERO else max(share_values)
    one_sided_overage = max(_ZERO, max_share - config.one_sided_share_threshold)
    one_sided_penalty = _normalize_unit_decimal(
        "one_sided_evidence_penalty",
        min(
            _ONE,
            (missing_count * config.missing_scenario_penalty)
            + (one_sided_overage * config.one_sided_penalty_scale),
        ),
    )
    source_kind_count = _count(len(frozenset(item.source_kind for item in items)))
    all_scenarios_present = all(shares[scenario] > _ZERO for scenario in SCENARIOS)
    applied_boost = (
        config.balanced_source_boost
        if all_scenarios_present
        and source_kind_count >= config.min_balanced_source_kind_count
        else _ZERO
    )
    score = _normalize_unit_decimal(
        "scenario_balance_score",
        max(
            _ZERO,
            min(_ONE, _ONE - scenario_gap - one_sided_penalty + applied_boost),
        ),
    )
    reason_codes = _row_reason_codes(
        shares=shares,
        score=score,
        one_sided_penalty=one_sided_penalty,
        applied_boost=applied_boost,
        config=config,
    )
    return StrategyCandidateScenarioBalanceScoreV2Row(
        candidate_reference=candidate_reference,
        latest_observed_at=max((item.observed_at for item in items), default=None),
        evidence_count=_count(len(items)),
        source_kind_count=source_kind_count,
        total_evidence_weight=total_weight,
        bull_scenario_weight=scenario_weights["bull"],
        base_scenario_weight=scenario_weights["base"],
        bear_scenario_weight=scenario_weights["bear"],
        bull_scenario_share=shares["bull"],
        base_scenario_share=shares["base"],
        bear_scenario_share=shares["bear"],
        scenario_imbalance_gap=scenario_gap,
        one_sided_evidence_penalty=one_sided_penalty,
        balanced_source_boost=applied_boost,
        scenario_balance_score=score,
        status=_row_status(score, config=config),
        reason_codes=reason_codes,
    )


def _weighted_scenario_amount(
    items: tuple[StrategyCandidateScenarioBalanceScoreV2Evidence, ...],
    scenario: str,
) -> Decimal:
    return _normalize_nonnegative_decimal(
        f"{scenario}_scenario_weight",
        sum(
            (
                item.evidence_weight * item.confidence_score
                for item in items
                if item.scenario == scenario
            ),
            _ZERO,
        ),
    )


def _row_reason_codes(
    *,
    shares: dict[str, Decimal],
    score: Decimal,
    one_sided_penalty: Decimal,
    applied_boost: Decimal,
    config: StrategyCandidateScenarioBalanceScoreV2Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = [_row_status_reason(_row_status(score, config=config))]
    if all(shares[scenario] > _ZERO for scenario in SCENARIOS):
        reason_codes.append("bull_base_bear_evidence_present")
    for scenario in SCENARIOS:
        if shares[scenario] == _ZERO:
            reason_codes.append(f"missing_{scenario}_scenario")
    if one_sided_penalty > _ZERO:
        reason_codes.append("one_sided_evidence_penalty")
    if applied_boost > _ZERO:
        reason_codes.append("balanced_source_boost")
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes),
        ROW_REASON_CODE_SEQUENCE,
        require_nonempty=True,
    )


def _report_reason_codes(
    rows: tuple[StrategyCandidateScenarioBalanceScoreV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("scenario_balance_report_empty",)
    reason_codes = [_report_status_reason(_report_status(rows))]
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code in REPORT_REASON_CODE_SEQUENCE:
                reason_codes.append(reason_code)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes),
        REPORT_REASON_CODE_SEQUENCE,
        require_nonempty=True,
    )


def _row_status(
    score: Decimal,
    *,
    config: StrategyCandidateScenarioBalanceScoreV2Config,
) -> str:
    if score >= config.pass_score_threshold:
        return "pass"
    if score >= config.watch_score_threshold:
        return "watch"
    return "block"


def _row_status_reason(status: str) -> str:
    return f"scenario_balance_{status}"


def _report_status(
    rows: tuple[StrategyCandidateScenarioBalanceScoreV2Row, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_status_reason(status: str) -> str:
    return f"scenario_balance_report_{status}"


def _group_items(
    items: tuple[StrategyCandidateScenarioBalanceScoreV2Evidence, ...],
) -> dict[str, tuple[StrategyCandidateScenarioBalanceScoreV2Evidence, ...]]:
    grouped: dict[str, list[StrategyCandidateScenarioBalanceScoreV2Evidence]] = {}
    for item in items:
        grouped.setdefault(item.candidate_reference, []).append(item)
    return {
        candidate_reference: tuple(
            sorted(
                candidate_items,
                key=lambda item: (
                    item.scenario,
                    item.source_kind,
                    item.source_reference,
                    item.observed_at.isoformat(),
                ),
            ),
        )
        for candidate_reference, candidate_items in grouped.items()
    }


def _validate_row_consistency(row: StrategyCandidateScenarioBalanceScoreV2Row) -> None:
    if row.evidence_count == _ZERO and row.total_evidence_weight != _ZERO:
        raise ValueError("total_evidence_weight must be zero when evidence_count is zero")
    expected_total = _normalize_nonnegative_decimal(
        "total_evidence_weight",
        row.bull_scenario_weight + row.base_scenario_weight + row.bear_scenario_weight,
    )
    if row.total_evidence_weight != expected_total:
        raise ValueError("total_evidence_weight must match scenario weights")
    expected_shares = (
        _ratio(row.bull_scenario_weight, row.total_evidence_weight),
        _ratio(row.base_scenario_weight, row.total_evidence_weight),
        _ratio(row.bear_scenario_weight, row.total_evidence_weight),
    )
    if (
        row.bull_scenario_share,
        row.base_scenario_share,
        row.bear_scenario_share,
    ) != expected_shares:
        raise ValueError("scenario shares must match scenario weights")
    expected_gap = (
        _ZERO
        if row.total_evidence_weight == _ZERO
        else _normalize_unit_decimal(
            "scenario_imbalance_gap",
            max(expected_shares) - min(expected_shares),
        )
    )
    if row.scenario_imbalance_gap != expected_gap:
        raise ValueError("scenario_imbalance_gap must match scenario shares")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: StrategyCandidateScenarioBalanceScoreV2Report,
) -> None:
    candidate_count = _count(len(report.rows))
    if report.candidate_count != candidate_count:
        raise ValueError("candidate_count must match rows")
    expected_pass_count = _count(sum(1 for row in report.rows if row.status == "pass"))
    expected_watch_count = _count(sum(1 for row in report.rows if row.status == "watch"))
    expected_block_count = _count(sum(1 for row in report.rows if row.status == "block"))
    if report.pass_count != expected_pass_count:
        raise ValueError("pass_count must match rows")
    if report.watch_count != expected_watch_count:
        raise ValueError("watch_count must match rows")
    if report.block_count != expected_block_count:
        raise ValueError("block_count must match rows")
    if report.average_scenario_balance_score != _average(
        row.scenario_balance_score for row in report.rows
    ):
        raise ValueError("average_scenario_balance_score must match rows")
    if report.max_scenario_imbalance_gap != _max_decimal(
        row.scenario_imbalance_gap for row in report.rows
    ):
        raise ValueError("max_scenario_imbalance_gap must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if "scenario_balance_block" in reason_codes:
        return "block"
    if "scenario_balance_watch" in reason_codes:
        return "watch"
    if "scenario_balance_pass" in reason_codes:
        return "pass"
    raise ValueError("reason_codes must include a status reason")


def _normalize_items(
    items: list[StrategyCandidateScenarioBalanceScoreV2Evidence]
    | tuple[StrategyCandidateScenarioBalanceScoreV2Evidence, ...],
) -> tuple[StrategyCandidateScenarioBalanceScoreV2Evidence, ...]:
    if isinstance(items, (str, bytes)) or not isinstance(items, (list, tuple)):
        raise ValueError("items must be a list or tuple")
    for item in items:
        if type(item) is not StrategyCandidateScenarioBalanceScoreV2Evidence:
            raise ValueError(
                "items must contain StrategyCandidateScenarioBalanceScoreV2Evidence",
            )
        require_paper_only_flags("evidence", item)
    return tuple(items)


def _normalize_rows(
    rows: tuple[StrategyCandidateScenarioBalanceScoreV2Row, ...],
) -> tuple[StrategyCandidateScenarioBalanceScoreV2Row, ...]:
    if isinstance(rows, (str, bytes)) or type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not StrategyCandidateScenarioBalanceScoreV2Row:
            raise ValueError("rows must contain StrategyCandidateScenarioBalanceScoreV2Row")
        require_paper_only_flags("row", row)
    return tuple(sorted(rows, key=lambda row: row.candidate_reference))


def _iter_public_key_values(value: object) -> tuple[tuple[str, str], ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_public_key_values(asdict(value))
    if isinstance(value, dict):
        items: list[tuple[str, str]] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            items.append((key, ""))
            if type(item) is str:
                items.append((key, item))
            items.extend(_iter_public_key_values(item))
        return tuple(items)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_iter_public_key_values(item))
        return tuple(items)
    if type(value) is str:
        return (("", value),)
    return ()


def _contains_unsafe_public_part(value: str) -> bool:
    lowered = value.lower()
    return any(part in lowered for part in _UNSAFE_PUBLIC_PARTS)


def _digestable_dataclass(value: object) -> dict[str, Any]:
    if not is_dataclass(value) or isinstance(value, type):
        raise ValueError("digest value must be a dataclass")
    ready = asdict(value)
    ready.pop("derived_validation_digest", None)
    return ready


def _digest_for_value(value: object) -> str:
    ready = _canonical_digest_value(value)
    encoded = json.dumps(ready, allow_nan=False, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _canonical_digest_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _canonical_digest_value(_digestable_dataclass(value))
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("digest_datetime", value).isoformat()
    if isinstance(value, dict):
        return {
            key: _canonical_digest_value(item)
            for key, item in sorted(value.items())
            if key != "derived_validation_digest"
        }
    if isinstance(value, (list, tuple)):
        return [_canonical_digest_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("unsupported digest value")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a digest string")
    if len(value) != _DIGEST_SIZE * 2:
        raise ValueError(f"{field_name} must be a sha256 digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be lowercase hex")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if require_nonempty and not value:
        raise ValueError(f"{field_name} must not be empty")
    for item in value:
        _require_canonical_string(field_name, item)
        if item not in allowed:
            raise ValueError(f"{field_name} must contain supported reason codes")
        validate_strategy_candidate_scenario_balance_score_v2_public_payload(item)
    return tuple(sorted(dict.fromkeys(value), key=lambda item: allowed.index(item)))


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed)}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical text")


def _normalize_unit_decimal(field_name: str, value: object) -> Decimal:
    decimal = _normalize_decimal(field_name, value)
    if decimal < _ZERO or decimal > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal = _normalize_decimal(field_name, value)
    if decimal < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if isinstance(value, Decimal) and type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal = _normalize_decimal(field_name, value)
    count = decimal.quantize(_COUNT_QUANTUM)
    if count != decimal:
        raise ValueError(f"{field_name} must be integral")
    if count < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return count


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _normalize_unit_decimal("ratio", numerator / denominator)


def _average(values: Any) -> Decimal:
    items = tuple(values)
    if not items:
        return _ZERO
    return _normalize_unit_decimal("average", sum(items, _ZERO) / _count(len(items)))


def _max_decimal(values: Any) -> Decimal:
    items = tuple(values)
    if not items:
        return _ZERO
    return max(items)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_RATIO_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if isinstance(value, datetime) and type(value) is not datetime:
        raise ValueError(f"{field_name} must be an exact datetime")
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_SCENARIO_BALANCE_SCORE_V2_CONFIG_VERSION",
    "StrategyCandidateScenarioBalanceScoreV2Config",
    "StrategyCandidateScenarioBalanceScoreV2Evidence",
    "StrategyCandidateScenarioBalanceScoreV2Report",
    "StrategyCandidateScenarioBalanceScoreV2Row",
    "build_strategy_candidate_scenario_balance_score_v2",
    "strategy_candidate_scenario_balance_score_v2_payload",
    "validate_strategy_candidate_scenario_balance_score_v2_public_payload",
)
