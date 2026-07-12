"""Readonly strategy screen stage rollup report."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Mapping


DEFAULT_STRATEGY_SCREEN_STAGE_ROLLUP_CONFIG_VERSION = "strategy-screen-stage-rollup-v0"

STRATEGY_SCREEN_STAGE_SEQUENCE = (
    "probability_screen",
    "team_route",
    "memory_policy",
    "source_quality",
    "cost_gate",
    "operator_packet",
    "supabase_readiness",
)
STRATEGY_SCREEN_STAGE_STATUS_VALUES = ("pass", "watch", "block")
STRATEGY_SCREEN_OVERALL_STATUSES = ("pass", "watch", "block")

_PAYLOAD_KEYS = (
    "config_version",
    "overall_status",
    "blocking_stage",
    "manual_next_steps",
    "stage_statuses",
    "paper_only",
    "report_only",
    "readonly",
    "digest",
)
_DIGEST_RE = frozenset("0123456789abcdef")

__all__ = (
    "DEFAULT_STRATEGY_SCREEN_STAGE_ROLLUP_CONFIG_VERSION",
    "STRATEGY_SCREEN_STAGE_SEQUENCE",
    "STRATEGY_SCREEN_STAGE_STATUS_VALUES",
    "STRATEGY_SCREEN_OVERALL_STATUSES",
    "StrategyScreenStageRollupInput",
    "StrategyScreenStageRollupReport",
    "build_strategy_screen_stage_rollup_report",
    "strategy_screen_stage_rollup_report_payload",
    "strategy_screen_stage_rollup_report_digest",
    "validate_strategy_screen_stage_rollup_public_payload",
)


@dataclass(frozen=True)
class StrategyScreenStageRollupInput:
    probability_screen: str
    team_route: str
    memory_policy: str
    source_quality: str
    cost_gate: str
    operator_packet: str
    supabase_readiness: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyScreenStageRollupInput:
            raise TypeError("StrategyScreenStageRollupInput does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not StrategyScreenStageRollupInput:
            raise ValueError("input must be exactly StrategyScreenStageRollupInput")
        for stage_name in STRATEGY_SCREEN_STAGE_SEQUENCE:
            _require_stage_status(stage_name, getattr(self, stage_name))
        _require_hard_flags(self)


@dataclass(frozen=True)
class StrategyScreenStageRollupReport:
    config_version: str
    overall_status: str
    blocking_stage: str | None
    manual_next_steps: tuple[str, ...]
    stage_statuses: tuple[tuple[str, str], ...]
    digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyScreenStageRollupReport:
            raise TypeError("StrategyScreenStageRollupReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not StrategyScreenStageRollupReport:
            raise ValueError("report must be exactly StrategyScreenStageRollupReport")
        _require_config_version(self.config_version)
        _require_overall_status("overall_status", self.overall_status)
        _require_blocking_stage(self.blocking_stage)
        object.__setattr__(
            self,
            "manual_next_steps",
            _require_manual_next_steps(self.manual_next_steps),
        )
        object.__setattr__(
            self,
            "stage_statuses",
            _require_stage_status_pairs(self.stage_statuses),
        )
        _require_digest("digest", self.digest)
        _require_hard_flags(self)
        _validate_report(self)
        if self.digest != _payload_digest(_payload_items(self, digest="")):
            raise ValueError("digest must match public payload")

    @property
    def public_payload(self) -> dict[str, object]:
        return strategy_screen_stage_rollup_report_payload(self)


def build_strategy_screen_stage_rollup_report(
    stage_input: StrategyScreenStageRollupInput,
) -> StrategyScreenStageRollupReport:
    if type(stage_input) is not StrategyScreenStageRollupInput:
        raise ValueError("stage_input must be a StrategyScreenStageRollupInput")
    _require_hard_flags(stage_input)
    stage_statuses = tuple(
        (stage_name, getattr(stage_input, stage_name))
        for stage_name in STRATEGY_SCREEN_STAGE_SEQUENCE
    )
    overall_status = _overall_status(stage_statuses)
    blocking_stage = _first_blocking_stage(stage_statuses)
    manual_next_steps = _manual_next_steps(stage_statuses)
    values: dict[str, object] = {
        "config_version": DEFAULT_STRATEGY_SCREEN_STAGE_ROLLUP_CONFIG_VERSION,
        "overall_status": overall_status,
        "blocking_stage": blocking_stage,
        "manual_next_steps": manual_next_steps,
        "stage_statuses": stage_statuses,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return StrategyScreenStageRollupReport(
        **values,
        digest=_payload_digest(_payload_values(values, digest="")),
    )


def strategy_screen_stage_rollup_report_payload(
    report: StrategyScreenStageRollupReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is StrategyScreenStageRollupReport:
        _require_hard_flags(report)
        _validate_report(report)
        if report.digest != _payload_digest(_payload_items(report, digest="")):
            raise ValueError("digest must match public payload")
        payload = _payload_items(report, digest=report.digest)
        validate_strategy_screen_stage_rollup_public_payload(payload)
        return payload
    if isinstance(report, Mapping):
        validate_strategy_screen_stage_rollup_public_payload(report)
        return dict(report)
    raise ValueError("report must be a StrategyScreenStageRollupReport or public payload")


def strategy_screen_stage_rollup_report_digest(
    report: StrategyScreenStageRollupReport,
) -> str:
    if type(report) is not StrategyScreenStageRollupReport:
        raise ValueError("report must be a StrategyScreenStageRollupReport")
    _require_hard_flags(report)
    _validate_report(report)
    if report.digest != _payload_digest(_payload_items(report, digest="")):
        raise ValueError("digest must match public payload")
    return report.digest


def validate_strategy_screen_stage_rollup_public_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("public payload must be a mapping")
    if tuple(payload.keys()) != _PAYLOAD_KEYS:
        raise ValueError("public payload keys must match report contract")
    _require_config_version(payload["config_version"])
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload[flag_name] is not True:
            raise ValueError(f"{flag_name} must be True")
    stage_statuses = _stage_statuses_from_payload(payload["stage_statuses"])
    expected_blocking_stage = _first_blocking_stage(stage_statuses)
    if expected_blocking_stage is not None and payload["blocking_stage"] is None:
        raise ValueError("stage_statuses must align with blocking_stage")
    expected_overall_status = _overall_status(stage_statuses)
    if payload["overall_status"] != expected_overall_status:
        raise ValueError("overall_status must match stage_statuses")
    if payload["blocking_stage"] != expected_blocking_stage:
        raise ValueError("blocking_stage must match stage_statuses")
    expected_steps = list(_manual_next_steps(stage_statuses))
    if payload["manual_next_steps"] != expected_steps:
        raise ValueError("manual_next_steps must match stage_statuses")
    _require_digest("digest", payload["digest"])
    payload_without_digest = dict(payload)
    payload_without_digest["digest"] = ""
    if payload["digest"] != _payload_digest(payload_without_digest):
        raise ValueError("digest must match public payload")
    return payload


def _validate_report(report: StrategyScreenStageRollupReport) -> None:
    expected_overall_status = _overall_status(report.stage_statuses)
    expected_blocking_stage = _first_blocking_stage(report.stage_statuses)
    expected_steps = _manual_next_steps(report.stage_statuses)
    if report.overall_status != expected_overall_status:
        raise ValueError("overall_status must match stage_statuses")
    if report.blocking_stage != expected_blocking_stage:
        raise ValueError("blocking_stage must match stage_statuses")
    if report.manual_next_steps != expected_steps:
        raise ValueError("manual_next_steps must match stage_statuses")


def _overall_status(stage_statuses: tuple[tuple[str, str], ...]) -> str:
    if any(status == "block" for _, status in stage_statuses):
        return "block"
    if any(status == "watch" for _, status in stage_statuses):
        return "watch"
    return "pass"


def _first_blocking_stage(stage_statuses: tuple[tuple[str, str], ...]) -> str | None:
    for stage_name, status in stage_statuses:
        if status == "block":
            return stage_name
    return None


def _manual_next_steps(stage_statuses: tuple[tuple[str, str], ...]) -> tuple[str, ...]:
    blocked_steps = tuple(
        f"resolve_{stage_name}_stage_blocker"
        for stage_name, status in stage_statuses
        if status == "block"
    )
    if blocked_steps:
        return blocked_steps
    return tuple(
        f"review_{stage_name}_stage_before_continuing"
        for stage_name, status in stage_statuses
        if status == "watch"
    )


def _payload_items(
    report: StrategyScreenStageRollupReport,
    *,
    digest: str,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "overall_status": report.overall_status,
        "blocking_stage": report.blocking_stage,
        "manual_next_steps": list(report.manual_next_steps),
        "stage_statuses": dict(report.stage_statuses),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
        "digest": digest,
    }


def _payload_values(values: Mapping[str, object], *, digest: str) -> dict[str, object]:
    return {
        "config_version": values["config_version"],
        "overall_status": values["overall_status"],
        "blocking_stage": values["blocking_stage"],
        "manual_next_steps": list(values["manual_next_steps"]),
        "stage_statuses": dict(values["stage_statuses"]),
        "paper_only": values["paper_only"],
        "report_only": values["report_only"],
        "readonly": values["readonly"],
        "digest": digest,
    }


def _stage_statuses_from_payload(value: object) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, Mapping):
        raise ValueError("stage_statuses must be a mapping")
    if tuple(value.keys()) != STRATEGY_SCREEN_STAGE_SEQUENCE:
        raise ValueError("public payload stage_statuses must match stage set")
    return tuple(
        (stage_name, _require_stage_status(stage_name, value[stage_name]))
        for stage_name in STRATEGY_SCREEN_STAGE_SEQUENCE
    )


def _require_stage_status_pairs(value: object) -> tuple[tuple[str, str], ...]:
    if type(value) is not tuple:
        raise ValueError("stage_statuses must be a tuple")
    if tuple(stage_name for stage_name, _ in value) != STRATEGY_SCREEN_STAGE_SEQUENCE:
        raise ValueError("stage_statuses must match stage set")
    return tuple(
        (stage_name, _require_stage_status(stage_name, status))
        for stage_name, status in value
    )


def _require_stage_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STRATEGY_SCREEN_STAGE_STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_overall_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STRATEGY_SCREEN_OVERALL_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_blocking_stage(value: object) -> str | None:
    if value is None:
        return None
    if type(value) is not str or value not in STRATEGY_SCREEN_STAGE_SEQUENCE:
        raise ValueError("blocking_stage must be a known stage or None")
    return value


def _require_manual_next_steps(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("manual_next_steps must be a tuple")
    if len(set(value)) != len(value):
        raise ValueError("manual_next_steps must not contain duplicates")
    for item in value:
        if type(item) is not str:
            raise ValueError("manual_next_steps must contain strings")
        if item.startswith("resolve_"):
            suffix = "_stage_blocker"
            stage_name = item.removeprefix("resolve_").removesuffix(suffix)
            if not item.endswith(suffix) or stage_name not in STRATEGY_SCREEN_STAGE_SEQUENCE:
                raise ValueError("manual_next_steps contains unknown step")
        elif item.startswith("review_"):
            suffix = "_stage_before_continuing"
            stage_name = item.removeprefix("review_").removesuffix(suffix)
            if not item.endswith(suffix) or stage_name not in STRATEGY_SCREEN_STAGE_SEQUENCE:
                raise ValueError("manual_next_steps contains unknown step")
        else:
            raise ValueError("manual_next_steps contains unknown step")
    return value


def _require_config_version(value: object) -> str:
    if value != DEFAULT_STRATEGY_SCREEN_STAGE_ROLLUP_CONFIG_VERSION:
        raise ValueError("config_version must be strategy-screen-stage-rollup-v0")
    if type(value) is not str:
        raise ValueError("config_version must be exactly str")
    return value


def _require_hard_flags(value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        flag = value[flag_name] if isinstance(value, Mapping) else getattr(value, flag_name)
        if flag is not True:
            raise ValueError(f"{flag_name} must be True")


def _require_digest(field_name: str, value: object) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in _DIGEST_RE for character in value)
    ):
        raise ValueError(f"{field_name} must be lowercase sha256 hex")
    return value


def _payload_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()
