"""Paper-only cost stress reducer for probability-event rows."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


QUANT = Decimal("0.000001")
ZERO = Decimal("0")
ACTIONS = ("recommend", "watch", "reject")
SIDES = ("yes", "no")
SURVIVAL_STATUSES = ("pass", "watch", "fail")


@dataclass(frozen=True)
class PaperCostStressInput:
    market_slug: str
    side: str
    action: str
    net_probability_edge: Decimal
    total_cost_per_share: Decimal
    recommendation_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_side(self.side)
        _require_action(self.action)
        object.__setattr__(
            self,
            "net_probability_edge",
            _normalize_decimal("net_probability_edge", self.net_probability_edge),
        )
        object.__setattr__(
            self,
            "total_cost_per_share",
            _normalize_nonnegative_decimal(
                "total_cost_per_share",
                self.total_cost_per_share,
            ),
        )
        object.__setattr__(
            self,
            "recommendation_score",
            _normalize_nonnegative_decimal(
                "recommendation_score",
                self.recommendation_score,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_safety_flags(self)


@dataclass(frozen=True)
class PaperCostStressConfig:
    config_version: str
    cost_shock_per_share_scenarios: tuple[tuple[str, Decimal], ...]

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "cost_shock_per_share_scenarios",
            _normalize_scenarios(self.cost_shock_per_share_scenarios),
        )


@dataclass(frozen=True)
class PaperCostStressScenarioRow:
    market_slug: str
    side: str
    action: str
    scenario_name: str
    net_probability_edge: Decimal
    cost_shock_per_share: Decimal
    total_cost_per_share: Decimal
    recommendation_score: Decimal
    stressed_net_probability_edge: Decimal
    survival_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_side(self.side)
        _require_action(self.action)
        _require_canonical_string("scenario_name", self.scenario_name)
        object.__setattr__(
            self,
            "net_probability_edge",
            _normalize_decimal("net_probability_edge", self.net_probability_edge),
        )
        object.__setattr__(
            self,
            "cost_shock_per_share",
            _normalize_nonnegative_decimal(
                "cost_shock_per_share",
                self.cost_shock_per_share,
            ),
        )
        object.__setattr__(
            self,
            "total_cost_per_share",
            _normalize_nonnegative_decimal(
                "total_cost_per_share",
                self.total_cost_per_share,
            ),
        )
        object.__setattr__(
            self,
            "recommendation_score",
            _normalize_nonnegative_decimal(
                "recommendation_score",
                self.recommendation_score,
            ),
        )
        object.__setattr__(
            self,
            "stressed_net_probability_edge",
            _normalize_decimal(
                "stressed_net_probability_edge",
                self.stressed_net_probability_edge,
            ),
        )
        _require_survival_status(self.survival_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_safety_flags(self)


@dataclass(frozen=True)
class PaperCostStressReport:
    generated_at: datetime
    config_version: str
    input_count: int
    scenario_count: int
    row_count: int
    pass_count: int
    watch_count: int
    fail_count: int
    rows: tuple[PaperCostStressScenarioRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "input_count",
            "scenario_count",
            "row_count",
            "pass_count",
            "watch_count",
            "fail_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_safety_flags(self)


def build_paper_cost_stress_report(
    inputs: Iterable[PaperCostStressInput],
    *,
    config: PaperCostStressConfig,
    generated_at: datetime,
) -> PaperCostStressReport:
    if type(config) is not PaperCostStressConfig:
        raise ValueError("config must be a PaperCostStressConfig")
    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")

    normalized_inputs = _normalize_inputs(inputs)
    scenario_rank = {
        scenario_name: index
        for index, (scenario_name, _) in enumerate(config.cost_shock_per_share_scenarios)
    }
    rows = tuple(
        sorted(
            (
                _row_for_input(value, scenario_name=scenario_name, shock=shock)
                for value in normalized_inputs
                for scenario_name, shock in config.cost_shock_per_share_scenarios
            ),
            key=lambda row: (
                row.market_slug,
                row.side,
                scenario_rank[row.scenario_name],
            ),
        ),
    )

    return PaperCostStressReport(
        generated_at=generated_at,
        config_version=config.config_version,
        input_count=len(normalized_inputs),
        scenario_count=len(config.cost_shock_per_share_scenarios),
        row_count=len(rows),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        fail_count=_status_count(rows, "fail"),
        rows=rows,
    )


def _row_for_input(
    value: PaperCostStressInput,
    *,
    scenario_name: str,
    shock: Decimal,
) -> PaperCostStressScenarioRow:
    stressed_net_probability_edge = value.net_probability_edge - shock
    survival_status = _survival_status(
        action=value.action,
        stressed_net_probability_edge=stressed_net_probability_edge,
    )
    return PaperCostStressScenarioRow(
        market_slug=value.market_slug,
        side=value.side,
        action=value.action,
        scenario_name=scenario_name,
        net_probability_edge=value.net_probability_edge,
        cost_shock_per_share=shock,
        total_cost_per_share=value.total_cost_per_share,
        recommendation_score=value.recommendation_score,
        stressed_net_probability_edge=stressed_net_probability_edge,
        survival_status=survival_status,
        reason_codes=_scenario_reason_codes(
            value.reason_codes,
            survival_status=survival_status,
        ),
    )


def _survival_status(
    *,
    action: str,
    stressed_net_probability_edge: Decimal,
) -> str:
    if stressed_net_probability_edge <= ZERO:
        return "fail"
    if action != "recommend":
        return "watch"
    return "pass"


def _scenario_reason_codes(
    source_reason_codes: tuple[str, ...],
    *,
    survival_status: str,
) -> tuple[str, ...]:
    if survival_status == "pass":
        stress_reason_code = "cost_stress_pass"
    elif survival_status == "watch":
        stress_reason_code = "source_action_not_recommend"
    else:
        stress_reason_code = "nonpositive_stressed_net_probability_edge"
    return _normalize_reason_codes((*source_reason_codes, stress_reason_code))


def _status_count(
    rows: tuple[PaperCostStressScenarioRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.survival_status == status)


def _normalize_inputs(
    values: Iterable[PaperCostStressInput],
) -> tuple[PaperCostStressInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("inputs must be an iterable of PaperCostStressInput values")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(
            "inputs must be an iterable of PaperCostStressInput values",
        ) from exc
    for value in normalized:
        if type(value) is not PaperCostStressInput:
            raise ValueError("inputs must contain only PaperCostStressInput values")
        if value.paper_only is not True:
            raise ValueError("inputs must contain paper_only values")
        if value.report_only is not True:
            raise ValueError("inputs must contain report_only values")
        if value.readonly is not True:
            raise ValueError("inputs must contain readonly values")
    return normalized


def _normalize_scenarios(value: object) -> tuple[tuple[str, Decimal], ...]:
    if type(value) is not tuple:
        raise ValueError("cost_shock_per_share_scenarios must be a tuple")
    if not value:
        raise ValueError("cost_shock_per_share_scenarios must not be empty")
    normalized_items: list[tuple[str, Decimal]] = []
    scenario_names: list[str] = []
    for item in value:
        if type(item) is not tuple or len(item) != 2:
            raise ValueError(
                "cost_shock_per_share_scenarios must contain scenario tuples",
            )
        scenario_name, shock = item
        _require_canonical_string("cost_shock_per_share_scenarios", scenario_name)
        normalized_shock = _normalize_nonnegative_decimal(
            "cost_shock_per_share_scenarios",
            shock,
        )
        normalized_items += ((scenario_name, normalized_shock),)
        scenario_names += (scenario_name,)
    if len(set(scenario_names)) != len(scenario_names):
        raise ValueError("cost_shock_per_share_scenarios must have unique names")
    return tuple(normalized_items)


def _normalize_rows(
    value: Iterable[PaperCostStressScenarioRow],
) -> tuple[PaperCostStressScenarioRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not PaperCostStressScenarioRow:
            raise ValueError("rows must contain PaperCostStressScenarioRow values")
        if row.paper_only is not True:
            raise ValueError("rows must contain paper_only values")
        if row.report_only is not True:
            raise ValueError("rows must contain report_only values")
        if row.readonly is not True:
            raise ValueError("rows must contain readonly values")
    return rows


def _validate_row_consistency(row: PaperCostStressScenarioRow) -> None:
    expected = _normalize_decimal(
        "stressed_net_probability_edge",
        row.net_probability_edge - row.cost_shock_per_share,
    )
    if row.stressed_net_probability_edge != expected:
        raise ValueError(
            "stressed_net_probability_edge must equal net_probability_edge minus shock",
        )
    if row.survival_status != _survival_status(
        action=row.action,
        stressed_net_probability_edge=row.stressed_net_probability_edge,
    ):
        raise ValueError("survival_status must match stressed edge and action")


def _validate_report_consistency(report: PaperCostStressReport) -> None:
    if report.row_count != len(report.rows):
        raise ValueError("row_count must match rows")
    if report.row_count != report.input_count * report.scenario_count:
        raise ValueError("row_count must match inputs multiplied by scenarios")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.fail_count != _status_count(report.rows, "fail"):
        raise ValueError("fail_count must match rows")
    if report.pass_count + report.watch_count + report.fail_count != report.row_count:
        raise ValueError("survival counts must sum to row_count")


def _normalize_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    for item in items:
        _require_canonical_string("reason_codes", item)
    return tuple(dict.fromkeys(items))


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    _require_finite_decimal(field_name, value)
    return value.quantize(QUANT)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_finite_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_side(value: object) -> None:
    if type(value) is not str:
        raise ValueError("side must be yes or no")
    if value not in SIDES:
        raise ValueError("side must be yes or no")


def _require_action(value: object) -> None:
    if type(value) is not str:
        raise ValueError("action must be recommend, watch, or reject")
    if value not in ACTIONS:
        raise ValueError("action must be recommend, watch, or reject")


def _require_survival_status(value: object) -> None:
    if type(value) is not str:
        raise ValueError("survival_status must be pass, watch, or fail")
    if value not in SURVIVAL_STATUSES:
        raise ValueError("survival_status must be pass, watch, or fail")


def _require_safety_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")


__all__ = (
    "PaperCostStressInput",
    "PaperCostStressConfig",
    "PaperCostStressScenarioRow",
    "PaperCostStressReport",
    "build_paper_cost_stress_report",
)
