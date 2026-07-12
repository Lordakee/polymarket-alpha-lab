"""Read-only push readiness report for probability event screen development."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any, Mapping

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


__all__ = (
    "PROBABILITY_EVENT_SCREEN_PUSH_READINESS_REPORT_VERSION",
    "PUSH_READINESS_BANDS",
    "ProbabilityEventScreenPushReadinessInput",
    "ProbabilityEventScreenPushReadinessReport",
    "build_probability_event_screen_push_readiness_report",
    "probability_event_screen_push_readiness_report_digest",
    "probability_event_screen_push_readiness_report_to_payload",
    "validate_probability_event_screen_push_readiness_public_payload",
)


PROBABILITY_EVENT_SCREEN_PUSH_READINESS_REPORT_VERSION = (
    "probability-event-screen-push-readiness-v0"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
COMPONENT_COUNT = Decimal("8.000000")

PUSH_READINESS_BANDS = ("ready", "attention", "blocked")
READY_REASON_CODE = "probability_event_screen_push_readiness_ready"

BLOCKED_REASON_SEQUENCE = (
    "push_release_gate_not_ready",
    "push_commit_readiness_not_ready",
    "push_validation_matrix_not_ready",
    "push_codegraph_sync_not_ready",
    "push_claude_review_not_ready",
    "push_github_remote_not_ready",
    "push_worktree_dirty_after_commit",
)
ATTENTION_REASON_SEQUENCE = (
    "push_live_execution_surface_detected",
    READY_REASON_CODE,
)

PAYLOAD_KEYS = (
    "config_version",
    "release_gate_ready",
    "commit_readiness_ready",
    "validation_matrix_ready",
    "codegraph_sync_ready",
    "claude_review_ready",
    "github_remote_ready",
    "worktree_clean_after_commit_ready",
    "no_live_execution_surface",
    "push_readiness_ready",
    "push_band",
    "blocked_reason_codes",
    "attention_reason_codes",
    "ready_ratio",
    "paper_only",
    "report_only",
    "readonly",
)

_BOOL_INPUT_FIELDS = (
    "release_gate_ready",
    "commit_readiness_ready",
    "validation_matrix_ready",
    "codegraph_sync_ready",
    "claude_review_ready",
    "github_remote_ready",
    "worktree_clean_after_commit_ready",
    "no_live_execution_surface",
)

_BLOCKING_CHECKS = (
    ("release_gate_ready", "push_release_gate_not_ready"),
    ("commit_readiness_ready", "push_commit_readiness_not_ready"),
    ("validation_matrix_ready", "push_validation_matrix_not_ready"),
    ("codegraph_sync_ready", "push_codegraph_sync_not_ready"),
    ("claude_review_ready", "push_claude_review_not_ready"),
    ("github_remote_ready", "push_github_remote_not_ready"),
    ("worktree_clean_after_commit_ready", "push_worktree_dirty_after_commit"),
)


class _PushReadinessPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _PushReadinessPublicDataclass and issubclass(
                base,
                _PushReadinessPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} does not support subclassing")


@dataclass(frozen=True)
class ProbabilityEventScreenPushReadinessInput(_PushReadinessPublicDataclass):
    release_gate_ready: bool
    commit_readiness_ready: bool
    validation_matrix_ready: bool
    codegraph_sync_ready: bool
    claude_review_ready: bool
    github_remote_ready: bool
    worktree_clean_after_commit_ready: bool
    no_live_execution_surface: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventScreenPushReadinessInput,
            "push readiness input",
        )
        for field_name in _BOOL_INPUT_FIELDS:
            _require_bool(field_name, getattr(self, field_name))
        _require_hard_flags("push readiness input", self)


@dataclass(frozen=True)
class ProbabilityEventScreenPushReadinessReport(_PushReadinessPublicDataclass):
    config_version: str
    release_gate_ready: bool
    commit_readiness_ready: bool
    validation_matrix_ready: bool
    codegraph_sync_ready: bool
    claude_review_ready: bool
    github_remote_ready: bool
    worktree_clean_after_commit_ready: bool
    no_live_execution_surface: bool
    push_readiness_ready: bool
    push_band: str
    blocked_reason_codes: tuple[str, ...]
    attention_reason_codes: tuple[str, ...]
    ready_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventScreenPushReadinessReport,
            "push readiness report",
        )
        _require_config_version(self.config_version)
        for field_name in _BOOL_INPUT_FIELDS + ("push_readiness_ready",):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "push_band",
            _normalize_member("push_band", self.push_band),
        )
        object.__setattr__(
            self,
            "blocked_reason_codes",
            _normalize_reason_codes(
                "blocked_reason_codes",
                self.blocked_reason_codes,
                BLOCKED_REASON_SEQUENCE,
            ),
        )
        object.__setattr__(
            self,
            "attention_reason_codes",
            _normalize_reason_codes(
                "attention_reason_codes",
                self.attention_reason_codes,
                ATTENTION_REASON_SEQUENCE,
            ),
        )
        object.__setattr__(
            self,
            "ready_ratio",
            _normalize_ratio("ready_ratio", self.ready_ratio),
        )
        _validate_report(self)
        _require_hard_flags("push readiness report", self)

    @property
    def public_payload(self) -> dict[str, object]:
        return probability_event_screen_push_readiness_report_to_payload(self)

    @property
    def digest(self) -> str:
        return probability_event_screen_push_readiness_report_digest(self)


def build_probability_event_screen_push_readiness_report(
    readiness: ProbabilityEventScreenPushReadinessInput,
) -> ProbabilityEventScreenPushReadinessReport:
    if type(readiness) is not ProbabilityEventScreenPushReadinessInput:
        raise ValueError(
            "readiness must be a ProbabilityEventScreenPushReadinessInput",
        )
    _require_hard_flags("push readiness input", readiness)

    blocked_reason_codes, attention_reason_codes, ready_component_count = (
        _push_readiness_findings(readiness)
    )
    push_band = _push_band(blocked_reason_codes, attention_reason_codes)

    return ProbabilityEventScreenPushReadinessReport(
        config_version=PROBABILITY_EVENT_SCREEN_PUSH_READINESS_REPORT_VERSION,
        release_gate_ready=readiness.release_gate_ready,
        commit_readiness_ready=readiness.commit_readiness_ready,
        validation_matrix_ready=readiness.validation_matrix_ready,
        codegraph_sync_ready=readiness.codegraph_sync_ready,
        claude_review_ready=readiness.claude_review_ready,
        github_remote_ready=readiness.github_remote_ready,
        worktree_clean_after_commit_ready=readiness.worktree_clean_after_commit_ready,
        no_live_execution_surface=readiness.no_live_execution_surface,
        push_readiness_ready=push_band == "ready",
        push_band=push_band,
        blocked_reason_codes=blocked_reason_codes,
        attention_reason_codes=attention_reason_codes,
        ready_ratio=_ratio(_count(ready_component_count), COMPONENT_COUNT),
        paper_only=readiness.paper_only,
        report_only=readiness.report_only,
        readonly=readiness.readonly,
    )


def probability_event_screen_push_readiness_report_to_payload(
    report: ProbabilityEventScreenPushReadinessReport,
) -> dict[str, object]:
    if type(report) is not ProbabilityEventScreenPushReadinessReport:
        raise ValueError(
            "report must be a ProbabilityEventScreenPushReadinessReport",
        )
    _require_hard_flags("push readiness report", report)
    _validate_report(report)
    payload = json_ready_no_floats(
        {
            "config_version": report.config_version,
            "release_gate_ready": report.release_gate_ready,
            "commit_readiness_ready": report.commit_readiness_ready,
            "validation_matrix_ready": report.validation_matrix_ready,
            "codegraph_sync_ready": report.codegraph_sync_ready,
            "claude_review_ready": report.claude_review_ready,
            "github_remote_ready": report.github_remote_ready,
            "worktree_clean_after_commit_ready": (
                report.worktree_clean_after_commit_ready
            ),
            "no_live_execution_surface": report.no_live_execution_surface,
            "push_readiness_ready": report.push_readiness_ready,
            "push_band": report.push_band,
            "blocked_reason_codes": report.blocked_reason_codes,
            "attention_reason_codes": report.attention_reason_codes,
            "ready_ratio": report.ready_ratio,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_probability_event_screen_push_readiness_public_payload(payload)
    return payload


def probability_event_screen_push_readiness_report_digest(
    report: ProbabilityEventScreenPushReadinessReport,
) -> str:
    payload = probability_event_screen_push_readiness_report_to_payload(report)
    return _digest_payload(payload)


def validate_probability_event_screen_push_readiness_public_payload(
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    if tuple(payload.keys()) != PAYLOAD_KEYS:
        raise ValueError("payload must match the canonical push readiness schema")
    reject_unsafe_surface_fields("push readiness public payload", payload)
    _require_config_version(payload["config_version"])
    for field_name in (
        *_BOOL_INPUT_FIELDS,
        "push_readiness_ready",
        "paper_only",
        "report_only",
        "readonly",
    ):
        _require_bool(field_name, payload[field_name])
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload[field_name] is not True:
            raise ValueError(f"{field_name} must be True")
    _normalize_member("push_band", payload["push_band"])
    blocked_reason_codes = _normalize_payload_reason_codes(
        "blocked_reason_codes",
        payload["blocked_reason_codes"],
        BLOCKED_REASON_SEQUENCE,
    )
    attention_reason_codes = _normalize_payload_reason_codes(
        "attention_reason_codes",
        payload["attention_reason_codes"],
        ATTENTION_REASON_SEQUENCE,
    )
    ready_ratio_value = payload["ready_ratio"]
    if type(ready_ratio_value) is not str:
        raise ValueError("ready_ratio must be serialized as a string")
    ready_ratio = _normalize_ratio("ready_ratio", Decimal(ready_ratio_value))
    expected_blocked, expected_attention, ready_component_count = (
        _payload_findings(payload)
    )
    if blocked_reason_codes != expected_blocked:
        raise ValueError("blocked_reason_codes must match readiness fields")
    if attention_reason_codes != expected_attention:
        raise ValueError("attention_reason_codes must match readiness fields")
    expected_band = _push_band(blocked_reason_codes, attention_reason_codes)
    if payload["push_band"] != expected_band:
        raise ValueError("push_band must match reason codes")
    if payload["push_readiness_ready"] is not (expected_band == "ready"):
        raise ValueError("push_readiness_ready must match push_band")
    if ready_ratio != _ratio(_count(ready_component_count), COMPONENT_COUNT):
        raise ValueError("ready_ratio must match readiness fields")
    return payload


def _push_readiness_findings(
    readiness: ProbabilityEventScreenPushReadinessInput,
) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    blocked: list[str] = []
    ready_component_count = 0
    for field_name, reason_code in _BLOCKING_CHECKS:
        if getattr(readiness, field_name) is True:
            ready_component_count += 1
        else:
            blocked.append(reason_code)

    if readiness.no_live_execution_surface is True:
        ready_component_count += 1
        attention = (READY_REASON_CODE,) if not blocked else ()
    else:
        attention = ("push_live_execution_surface_detected",)
    return tuple(blocked), attention, ready_component_count


def _payload_findings(
    payload: Mapping[str, object],
) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    source = ProbabilityEventScreenPushReadinessInput(
        release_gate_ready=payload["release_gate_ready"],  # type: ignore[arg-type]
        commit_readiness_ready=payload["commit_readiness_ready"],  # type: ignore[arg-type]
        validation_matrix_ready=payload["validation_matrix_ready"],  # type: ignore[arg-type]
        codegraph_sync_ready=payload["codegraph_sync_ready"],  # type: ignore[arg-type]
        claude_review_ready=payload["claude_review_ready"],  # type: ignore[arg-type]
        github_remote_ready=payload["github_remote_ready"],  # type: ignore[arg-type]
        worktree_clean_after_commit_ready=payload["worktree_clean_after_commit_ready"],  # type: ignore[arg-type]
        no_live_execution_surface=payload["no_live_execution_surface"],  # type: ignore[arg-type]
        paper_only=payload["paper_only"],  # type: ignore[arg-type]
        report_only=payload["report_only"],  # type: ignore[arg-type]
        readonly=payload["readonly"],  # type: ignore[arg-type]
    )
    return _push_readiness_findings(source)


def _validate_report(report: ProbabilityEventScreenPushReadinessReport) -> None:
    blocked_reason_codes, attention_reason_codes, ready_component_count = (
        _report_findings(report)
    )
    if report.blocked_reason_codes != blocked_reason_codes:
        raise ValueError("blocked_reason_codes must match readiness fields")
    if report.attention_reason_codes != attention_reason_codes:
        raise ValueError("attention_reason_codes must match readiness fields")
    expected_band = _push_band(blocked_reason_codes, attention_reason_codes)
    if report.push_band != expected_band:
        raise ValueError("push_band must match reason codes")
    if report.push_readiness_ready is not (expected_band == "ready"):
        raise ValueError("push_readiness_ready must match push_band")
    if report.ready_ratio != _ratio(_count(ready_component_count), COMPONENT_COUNT):
        raise ValueError("ready_ratio must match readiness fields")


def _report_findings(
    report: ProbabilityEventScreenPushReadinessReport,
) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    source = ProbabilityEventScreenPushReadinessInput(
        release_gate_ready=report.release_gate_ready,
        commit_readiness_ready=report.commit_readiness_ready,
        validation_matrix_ready=report.validation_matrix_ready,
        codegraph_sync_ready=report.codegraph_sync_ready,
        claude_review_ready=report.claude_review_ready,
        github_remote_ready=report.github_remote_ready,
        worktree_clean_after_commit_ready=report.worktree_clean_after_commit_ready,
        no_live_execution_surface=report.no_live_execution_surface,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    return _push_readiness_findings(source)


def _push_band(
    blocked_reason_codes: tuple[str, ...],
    attention_reason_codes: tuple[str, ...],
) -> str:
    if blocked_reason_codes:
        return "blocked"
    if attention_reason_codes != (READY_REASON_CODE,):
        return "attention"
    return "ready"


def _normalize_member(field_name: str, value: object) -> str:
    if type(value) is not str or value not in PUSH_READINESS_BANDS:
        raise ValueError(f"{field_name} must be a supported push readiness band")
    return value


def _normalize_reason_codes(
    field_name: str,
    value: object,
    supported_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    return _normalize_reason_code_items(field_name, value, supported_reason_codes)


def _normalize_payload_reason_codes(
    field_name: str,
    value: object,
    supported_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is list:
        return _normalize_reason_code_items(
            field_name,
            tuple(value),
            supported_reason_codes,
        )
    if type(value) is tuple:
        return _normalize_reason_code_items(field_name, value, supported_reason_codes)
    raise ValueError(f"{field_name} must be a list")


def _normalize_reason_code_items(
    field_name: str,
    reason_codes: tuple[str, ...],
    supported_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    seen: set[str] = set()
    for reason_code in reason_codes:
        if type(reason_code) is not str or reason_code not in supported_reason_codes:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    ordered = tuple(
        reason_code for reason_code in supported_reason_codes if reason_code in seen
    )
    if reason_codes != ordered:
        raise ValueError(f"{field_name} must use canonical order")
    return ordered


def _require_config_version(value: object) -> None:
    if value != PROBABILITY_EVENT_SCREEN_PUSH_READINESS_REPORT_VERSION:
        raise ValueError("config_version must be the supported report version")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_hard_flags(label: str, value: Any) -> None:
    require_paper_only_flags(label, value)


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return Decimal(value).quantize(QUANTUM, rounding=ROUND_HALF_UP)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _normalize_ratio("ready_ratio", numerator / denominator)


def _digest_payload(payload: dict[str, object]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
