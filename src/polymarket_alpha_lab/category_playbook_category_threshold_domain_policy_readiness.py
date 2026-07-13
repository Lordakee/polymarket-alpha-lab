"""Readonly category playbook, threshold, and domain policy readiness."""

from __future__ import annotations

from dataclasses import InitVar, dataclass, fields
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from typing import Any, Mapping


DEFAULT_CATEGORY_PLAYBOOK_CATEGORY_THRESHOLD_DOMAIN_POLICY_READINESS_VERSION = (
    "category-playbook-category-threshold-domain-policy-readiness-v0"
)
CATEGORY_PLAYBOOK_CATEGORY_THRESHOLD_DOMAIN_POLICY_READINESS_STATUSES = (
    "ready",
    "watch",
    "blocked",
)
SUPPORTED_CATEGORY_IDS = (
    "politics",
    "macro",
    "bitcoin",
    "equity_index",
    "gold",
    "soccer",
    "basketball",
)
REASON_CODES = (
    "domain_policy_readonly",
    "min_liquidity_below_category_threshold",
    "max_spread_above_category_threshold",
    "category_thresholds_ready",
    "evidence_quorum_ready",
    "evidence_quorum_missing",
    "freshness_sla_ready",
    "freshness_sla_stale",
    "category_playbook_ready",
    "category_playbook_missing",
    "playbook_settled_examples_missing",
    "playbook_source_families_missing",
    "manual_review_not_required",
    "manual_review_completed",
    "manual_review_required",
    "category_readiness_ready",
    "category_readiness_watch",
    "category_readiness_blocked",
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
MONEY_QUANTUM = Decimal("0.000001")
PROBABILITY_QUANTUM = Decimal("0.000001")
HOUR_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0")
ONE = Decimal("1")
HEX_CHARS = frozenset("0123456789abcdef")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_REPORT_DIGEST_BOOTSTRAP = object()


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class CategoryPlaybookCategoryThresholdDomainPolicyReadinessConfig(_FinalDataclass):
    category_id: str
    domain_policy_id: str
    playbook_id: str
    min_liquidity_usd: Decimal
    max_spread_probability: Decimal
    evidence_quorum: Decimal
    freshness_sla_hours: Decimal
    playbook_min_settled_examples: Decimal
    playbook_min_source_families: Decimal
    manual_review_required: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            CategoryPlaybookCategoryThresholdDomainPolicyReadinessConfig,
            "config",
        )
        object.__setattr__(self, "category_id", _require_category_id(self.category_id))
        object.__setattr__(
            self,
            "domain_policy_id",
            _require_public_text("domain_policy_id", self.domain_policy_id),
        )
        object.__setattr__(
            self,
            "playbook_id",
            _require_public_text("playbook_id", self.playbook_id),
        )
        object.__setattr__(
            self,
            "min_liquidity_usd",
            _normalize_money("min_liquidity_usd", self.min_liquidity_usd),
        )
        object.__setattr__(
            self,
            "max_spread_probability",
            _normalize_probability(
                "max_spread_probability",
                self.max_spread_probability,
            ),
        )
        for field_name in (
            "evidence_quorum",
            "playbook_min_settled_examples",
            "playbook_min_source_families",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "freshness_sla_hours",
            _normalize_positive_hours("freshness_sla_hours", self.freshness_sla_hours),
        )
        _require_bool("manual_review_required", self.manual_review_required)
        _require_hard_flags("config", self)
        _validate_config(self)


@dataclass(frozen=True)
class CategoryPlaybookCategoryThresholdDomainPolicyReadinessInput(_FinalDataclass):
    category_id: str
    observed_liquidity_usd: Decimal
    observed_spread_probability: Decimal
    evidence_source_count: Decimal
    evidence_age_hours: Decimal
    playbook_exists: bool
    playbook_settled_example_count: Decimal
    playbook_source_family_count: Decimal
    manual_review_completed: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            CategoryPlaybookCategoryThresholdDomainPolicyReadinessInput,
            "readiness_input",
        )
        object.__setattr__(self, "category_id", _require_category_id(self.category_id))
        object.__setattr__(
            self,
            "observed_liquidity_usd",
            _normalize_money("observed_liquidity_usd", self.observed_liquidity_usd),
        )
        object.__setattr__(
            self,
            "observed_spread_probability",
            _normalize_probability(
                "observed_spread_probability",
                self.observed_spread_probability,
            ),
        )
        for field_name in (
            "evidence_source_count",
            "playbook_settled_example_count",
            "playbook_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_age_hours",
            _normalize_nonnegative_hours("evidence_age_hours", self.evidence_age_hours),
        )
        _require_bool("playbook_exists", self.playbook_exists)
        _require_bool("manual_review_completed", self.manual_review_completed)
        _require_hard_flags("readiness_input", self)


@dataclass(frozen=True)
class CategoryPlaybookCategoryThresholdDomainPolicyReadinessReport(_FinalDataclass):
    config_version: str
    category_id: str
    domain_policy_id: str
    playbook_id: str
    min_liquidity_usd: Decimal
    max_spread_probability: Decimal
    evidence_quorum: Decimal
    freshness_sla_hours: Decimal
    playbook_min_settled_examples: Decimal
    playbook_min_source_families: Decimal
    manual_review_required: bool
    observed_liquidity_usd: Decimal
    observed_spread_probability: Decimal
    evidence_source_count: Decimal
    evidence_age_hours: Decimal
    playbook_exists: bool
    playbook_settled_example_count: Decimal
    playbook_source_family_count: Decimal
    manual_review_completed: bool
    readiness_status: str
    reason_codes: tuple[str, ...]
    manual_next_step: str
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    _digest_bootstrap: InitVar[object] = None

    def __post_init__(self, _digest_bootstrap: object) -> None:
        _require_exact_type(
            self,
            CategoryPlaybookCategoryThresholdDomainPolicyReadinessReport,
            "report",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_text("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_CATEGORY_PLAYBOOK_CATEGORY_THRESHOLD_DOMAIN_POLICY_READINESS_VERSION
        ):
            raise ValueError("config_version must be supported")
        object.__setattr__(self, "category_id", _require_category_id(self.category_id))
        object.__setattr__(
            self,
            "domain_policy_id",
            _require_public_text("domain_policy_id", self.domain_policy_id),
        )
        object.__setattr__(
            self,
            "playbook_id",
            _require_public_text("playbook_id", self.playbook_id),
        )
        for field_name in (
            "min_liquidity_usd",
            "observed_liquidity_usd",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_money(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_spread_probability",
            "observed_spread_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_quorum",
            "playbook_min_settled_examples",
            "playbook_min_source_families",
            "evidence_source_count",
            "playbook_settled_example_count",
            "playbook_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "freshness_sla_hours",
            _normalize_positive_hours("freshness_sla_hours", self.freshness_sla_hours),
        )
        object.__setattr__(
            self,
            "evidence_age_hours",
            _normalize_nonnegative_hours("evidence_age_hours", self.evidence_age_hours),
        )
        for field_name in (
            "manual_review_required",
            "playbook_exists",
            "manual_review_completed",
        ):
            _require_bool(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "readiness_status",
            _require_readiness_status("readiness_status", self.readiness_status),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "manual_next_step",
            _require_public_text("manual_next_step", self.manual_next_step),
        )
        _require_hard_flags("report", self)
        _validate_report(self)
        _apply_or_verify_digest(self, _digest_bootstrap)

    @property
    def public_payload(self) -> dict[str, Any]:
        return category_playbook_category_threshold_domain_policy_readiness_payload(self)


def category_playbook_category_threshold_domain_policy_readiness_config(
    category_id: str,
) -> CategoryPlaybookCategoryThresholdDomainPolicyReadinessConfig:
    category = _require_category_id(category_id)
    values = _CONFIG_VALUES[category]
    return CategoryPlaybookCategoryThresholdDomainPolicyReadinessConfig(
        category_id=category,
        domain_policy_id=f"domain-policy-{category}-readonly",
        playbook_id=f"category-playbook-{category}-readonly",
        min_liquidity_usd=values["min_liquidity_usd"],
        max_spread_probability=values["max_spread_probability"],
        evidence_quorum=values["evidence_quorum"],
        freshness_sla_hours=values["freshness_sla_hours"],
        playbook_min_settled_examples=values["playbook_min_settled_examples"],
        playbook_min_source_families=values["playbook_min_source_families"],
        manual_review_required=values["manual_review_required"],
    )


def build_category_playbook_category_threshold_domain_policy_readiness_report(
    readiness_input: CategoryPlaybookCategoryThresholdDomainPolicyReadinessInput,
) -> CategoryPlaybookCategoryThresholdDomainPolicyReadinessReport:
    if type(readiness_input) is not CategoryPlaybookCategoryThresholdDomainPolicyReadinessInput:
        raise ValueError(
            "readiness_input must be a "
            "CategoryPlaybookCategoryThresholdDomainPolicyReadinessInput",
        )
    _require_hard_flags("readiness_input", readiness_input)
    config = category_playbook_category_threshold_domain_policy_readiness_config(
        readiness_input.category_id,
    )
    reason_codes = _reason_codes(config, readiness_input)
    status = _readiness_status(reason_codes)
    return CategoryPlaybookCategoryThresholdDomainPolicyReadinessReport(
        config_version=(
            DEFAULT_CATEGORY_PLAYBOOK_CATEGORY_THRESHOLD_DOMAIN_POLICY_READINESS_VERSION
        ),
        category_id=config.category_id,
        domain_policy_id=config.domain_policy_id,
        playbook_id=config.playbook_id,
        min_liquidity_usd=config.min_liquidity_usd,
        max_spread_probability=config.max_spread_probability,
        evidence_quorum=config.evidence_quorum,
        freshness_sla_hours=config.freshness_sla_hours,
        playbook_min_settled_examples=config.playbook_min_settled_examples,
        playbook_min_source_families=config.playbook_min_source_families,
        manual_review_required=config.manual_review_required,
        observed_liquidity_usd=readiness_input.observed_liquidity_usd,
        observed_spread_probability=readiness_input.observed_spread_probability,
        evidence_source_count=readiness_input.evidence_source_count,
        evidence_age_hours=readiness_input.evidence_age_hours,
        playbook_exists=readiness_input.playbook_exists,
        playbook_settled_example_count=readiness_input.playbook_settled_example_count,
        playbook_source_family_count=readiness_input.playbook_source_family_count,
        manual_review_completed=readiness_input.manual_review_completed,
        readiness_status=status,
        reason_codes=reason_codes,
        manual_next_step=_manual_next_step(status),
        _digest_bootstrap=_REPORT_DIGEST_BOOTSTRAP,
    )


def category_playbook_category_threshold_domain_policy_readiness_payload(
    value: (
        CategoryPlaybookCategoryThresholdDomainPolicyReadinessReport
        | Mapping[str, Any]
    ),
) -> dict[str, Any]:
    if type(value) is CategoryPlaybookCategoryThresholdDomainPolicyReadinessReport:
        payload = _public_payload(_validated_report_copy(value))
    elif isinstance(value, Mapping):
        payload = _copy_payload(value)
        _require_hard_flags("payload", _DictFlags(value))
    else:
        raise ValueError(
            "value must be a "
            "CategoryPlaybookCategoryThresholdDomainPolicyReadinessReport "
            "or public payload",
        )
    return _validate_public_payload(payload)


@dataclass(frozen=True)
class _DictFlags:
    value: Mapping[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


_CONFIG_VALUES: dict[str, dict[str, Any]] = {
    "politics": {
        "min_liquidity_usd": Decimal("25000.000000"),
        "max_spread_probability": Decimal("0.030000"),
        "evidence_quorum": Decimal("4"),
        "freshness_sla_hours": Decimal("1.000000"),
        "playbook_min_settled_examples": Decimal("5"),
        "playbook_min_source_families": Decimal("3"),
        "manual_review_required": True,
    },
    "macro": {
        "min_liquidity_usd": Decimal("20000.000000"),
        "max_spread_probability": Decimal("0.025000"),
        "evidence_quorum": Decimal("4"),
        "freshness_sla_hours": Decimal("1.000000"),
        "playbook_min_settled_examples": Decimal("5"),
        "playbook_min_source_families": Decimal("3"),
        "manual_review_required": True,
    },
    "bitcoin": {
        "min_liquidity_usd": Decimal("15000.000000"),
        "max_spread_probability": Decimal("0.020000"),
        "evidence_quorum": Decimal("3"),
        "freshness_sla_hours": Decimal("0.500000"),
        "playbook_min_settled_examples": Decimal("4"),
        "playbook_min_source_families": Decimal("3"),
        "manual_review_required": False,
    },
    "equity_index": {
        "min_liquidity_usd": Decimal("15000.000000"),
        "max_spread_probability": Decimal("0.020000"),
        "evidence_quorum": Decimal("3"),
        "freshness_sla_hours": Decimal("1.000000"),
        "playbook_min_settled_examples": Decimal("4"),
        "playbook_min_source_families": Decimal("3"),
        "manual_review_required": False,
    },
    "gold": {
        "min_liquidity_usd": Decimal("10000.000000"),
        "max_spread_probability": Decimal("0.020000"),
        "evidence_quorum": Decimal("3"),
        "freshness_sla_hours": Decimal("2.000000"),
        "playbook_min_settled_examples": Decimal("4"),
        "playbook_min_source_families": Decimal("3"),
        "manual_review_required": False,
    },
    "soccer": {
        "min_liquidity_usd": Decimal("5000.000000"),
        "max_spread_probability": Decimal("0.030000"),
        "evidence_quorum": Decimal("2"),
        "freshness_sla_hours": Decimal("3.000000"),
        "playbook_min_settled_examples": Decimal("3"),
        "playbook_min_source_families": Decimal("2"),
        "manual_review_required": False,
    },
    "basketball": {
        "min_liquidity_usd": Decimal("5000.000000"),
        "max_spread_probability": Decimal("0.030000"),
        "evidence_quorum": Decimal("2"),
        "freshness_sla_hours": Decimal("3.000000"),
        "playbook_min_settled_examples": Decimal("3"),
        "playbook_min_source_families": Decimal("2"),
        "manual_review_required": False,
    },
}


def _reason_codes(
    config: CategoryPlaybookCategoryThresholdDomainPolicyReadinessConfig,
    readiness_input: CategoryPlaybookCategoryThresholdDomainPolicyReadinessInput,
) -> tuple[str, ...]:
    codes = ["domain_policy_readonly"]
    threshold_ready = True
    if readiness_input.observed_liquidity_usd < config.min_liquidity_usd:
        codes.append("min_liquidity_below_category_threshold")
        threshold_ready = False
    if readiness_input.observed_spread_probability > config.max_spread_probability:
        codes.append("max_spread_above_category_threshold")
        threshold_ready = False
    if threshold_ready:
        codes.append("category_thresholds_ready")
    if readiness_input.evidence_source_count >= config.evidence_quorum:
        codes.append("evidence_quorum_ready")
    else:
        codes.append("evidence_quorum_missing")
    if readiness_input.evidence_age_hours <= config.freshness_sla_hours:
        codes.append("freshness_sla_ready")
    else:
        codes.append("freshness_sla_stale")
    if readiness_input.playbook_exists:
        if (
            readiness_input.playbook_settled_example_count
            >= config.playbook_min_settled_examples
            and readiness_input.playbook_source_family_count
            >= config.playbook_min_source_families
        ):
            codes.append("category_playbook_ready")
        else:
            if (
                readiness_input.playbook_settled_example_count
                < config.playbook_min_settled_examples
            ):
                codes.append("playbook_settled_examples_missing")
            if (
                readiness_input.playbook_source_family_count
                < config.playbook_min_source_families
            ):
                codes.append("playbook_source_families_missing")
    else:
        codes.append("category_playbook_missing")
        codes.append("playbook_settled_examples_missing")
        codes.append("playbook_source_families_missing")
    if config.manual_review_required:
        codes.append(
            "manual_review_completed"
            if readiness_input.manual_review_completed
            else "manual_review_required"
        )
    else:
        codes.append("manual_review_not_required")
    codes.append(f"category_readiness_{_readiness_status(tuple(codes))}")
    return tuple(code for code in REASON_CODES if code in codes)


def _readiness_status(reason_codes: tuple[str, ...]) -> str:
    blocking_codes = {
        "min_liquidity_below_category_threshold",
        "max_spread_above_category_threshold",
        "evidence_quorum_missing",
        "freshness_sla_stale",
        "category_playbook_missing",
        "playbook_settled_examples_missing",
        "playbook_source_families_missing",
    }
    if any(code in blocking_codes for code in reason_codes):
        return "blocked"
    if "manual_review_required" in reason_codes:
        return "watch"
    return "ready"


def _manual_next_step(readiness_status: str) -> str:
    if readiness_status == "ready":
        return "reuse_category_playbook_for_paper_research"
    if readiness_status == "watch":
        return "complete_manual_review_before_paper_research"
    return "repair_category_thresholds_and_playbook_before_reuse"


def _validate_config(
    config: CategoryPlaybookCategoryThresholdDomainPolicyReadinessConfig,
) -> None:
    if config.domain_policy_id != f"domain-policy-{config.category_id}-readonly":
        raise ValueError("domain_policy_id must match category_id")
    if config.playbook_id != f"category-playbook-{config.category_id}-readonly":
        raise ValueError("playbook_id must match category_id")
    if config.min_liquidity_usd <= ZERO:
        raise ValueError("min_liquidity_usd must be above zero")
    if config.max_spread_probability <= ZERO:
        raise ValueError("max_spread_probability must be above zero")
    if config.evidence_quorum < Decimal("2"):
        raise ValueError("evidence_quorum must be at least two")
    if config.playbook_min_settled_examples < Decimal("3"):
        raise ValueError("playbook_min_settled_examples must be at least three")
    if config.playbook_min_source_families < Decimal("2"):
        raise ValueError("playbook_min_source_families must be at least two")


def _validate_report(
    report: CategoryPlaybookCategoryThresholdDomainPolicyReadinessReport,
) -> None:
    config = CategoryPlaybookCategoryThresholdDomainPolicyReadinessConfig(
        category_id=report.category_id,
        domain_policy_id=report.domain_policy_id,
        playbook_id=report.playbook_id,
        min_liquidity_usd=report.min_liquidity_usd,
        max_spread_probability=report.max_spread_probability,
        evidence_quorum=report.evidence_quorum,
        freshness_sla_hours=report.freshness_sla_hours,
        playbook_min_settled_examples=report.playbook_min_settled_examples,
        playbook_min_source_families=report.playbook_min_source_families,
        manual_review_required=report.manual_review_required,
    )
    canonical_config = (
        category_playbook_category_threshold_domain_policy_readiness_config(
            report.category_id,
        )
    )
    if config != canonical_config:
        raise ValueError("report config must match canonical category policy")
    readiness_input = CategoryPlaybookCategoryThresholdDomainPolicyReadinessInput(
        category_id=report.category_id,
        observed_liquidity_usd=report.observed_liquidity_usd,
        observed_spread_probability=report.observed_spread_probability,
        evidence_source_count=report.evidence_source_count,
        evidence_age_hours=report.evidence_age_hours,
        playbook_exists=report.playbook_exists,
        playbook_settled_example_count=report.playbook_settled_example_count,
        playbook_source_family_count=report.playbook_source_family_count,
        manual_review_completed=report.manual_review_completed,
    )
    expected_reason_codes = _reason_codes(config, readiness_input)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match category readiness inputs")
    expected_status = _readiness_status(expected_reason_codes)
    if report.readiness_status != expected_status:
        raise ValueError("readiness_status must match reason_codes")
    if report.manual_next_step != _manual_next_step(expected_status):
        raise ValueError("manual_next_step must match readiness_status")


def _public_payload(
    report: CategoryPlaybookCategoryThresholdDomainPolicyReadinessReport,
) -> dict[str, Any]:
    payload = {
        "config_version": report.config_version,
        "category_id": report.category_id,
        "domain_policy_id": report.domain_policy_id,
        "playbook_id": report.playbook_id,
        "min_liquidity_usd": _decimal_to_string(report.min_liquidity_usd),
        "max_spread_probability": _decimal_to_string(report.max_spread_probability),
        "evidence_quorum": _decimal_to_string(report.evidence_quorum),
        "freshness_sla_hours": _decimal_to_string(report.freshness_sla_hours),
        "playbook_min_settled_examples": _decimal_to_string(
            report.playbook_min_settled_examples,
        ),
        "playbook_min_source_families": _decimal_to_string(
            report.playbook_min_source_families,
        ),
        "manual_review_required": report.manual_review_required,
        "observed_liquidity_usd": _decimal_to_string(report.observed_liquidity_usd),
        "observed_spread_probability": _decimal_to_string(
            report.observed_spread_probability,
        ),
        "evidence_source_count": _decimal_to_string(report.evidence_source_count),
        "evidence_age_hours": _decimal_to_string(report.evidence_age_hours),
        "playbook_exists": report.playbook_exists,
        "playbook_settled_example_count": _decimal_to_string(
            report.playbook_settled_example_count,
        ),
        "playbook_source_family_count": _decimal_to_string(
            report.playbook_source_family_count,
        ),
        "manual_review_completed": report.manual_review_completed,
        "readiness_status": report.readiness_status,
        "reason_codes": list(report.reason_codes),
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    payload["payload_digest"] = report.payload_digest
    return payload


def _validated_report_copy(
    report: CategoryPlaybookCategoryThresholdDomainPolicyReadinessReport,
) -> CategoryPlaybookCategoryThresholdDomainPolicyReadinessReport:
    return CategoryPlaybookCategoryThresholdDomainPolicyReadinessReport(
        **{
            field.name: getattr(report, field.name)
            for field in fields(
                CategoryPlaybookCategoryThresholdDomainPolicyReadinessReport,
            )
        },
    )


def _copy_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    copied: dict[str, Any] = {}
    for name, value in payload.items():
        if type(name) is not str:
            raise ValueError("public payload ke" "ys must be exact strings")
        copied[name] = value
    return copied


def _validate_public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    required_fields = (
        "config_version",
        "category_id",
        "domain_policy_id",
        "playbook_id",
        "min_liquidity_usd",
        "max_spread_probability",
        "evidence_quorum",
        "freshness_sla_hours",
        "playbook_min_settled_examples",
        "playbook_min_source_families",
        "manual_review_required",
        "observed_liquidity_usd",
        "observed_spread_probability",
        "evidence_source_count",
        "evidence_age_hours",
        "playbook_exists",
        "playbook_settled_example_count",
        "playbook_source_family_count",
        "manual_review_completed",
        "readiness_status",
        "reason_codes",
        "manual_next_step",
        "payload_digest",
        "paper_only",
        "report_only",
        "readonly",
    )
    for field_name in required_fields:
        if field_name not in payload:
            raise ValueError(f"{field_name} is required")
    _require_digest("payload_digest", payload["payload_digest"])
    if payload["payload_digest"] != _payload_digest(payload):
        raise ValueError("payload_digest must match public payload")
    report = CategoryPlaybookCategoryThresholdDomainPolicyReadinessReport(
        config_version=_require_public_text("config_version", payload["config_version"]),
        category_id=_require_category_id(payload["category_id"]),
        domain_policy_id=_require_public_text(
            "domain_policy_id",
            payload["domain_policy_id"],
        ),
        playbook_id=_require_public_text("playbook_id", payload["playbook_id"]),
        min_liquidity_usd=_decimal_from_payload(
            "min_liquidity_usd",
            payload["min_liquidity_usd"],
        ),
        max_spread_probability=_decimal_from_payload(
            "max_spread_probability",
            payload["max_spread_probability"],
        ),
        evidence_quorum=_decimal_from_payload(
            "evidence_quorum",
            payload["evidence_quorum"],
        ),
        freshness_sla_hours=_decimal_from_payload(
            "freshness_sla_hours",
            payload["freshness_sla_hours"],
        ),
        playbook_min_settled_examples=_decimal_from_payload(
            "playbook_min_settled_examples",
            payload["playbook_min_settled_examples"],
        ),
        playbook_min_source_families=_decimal_from_payload(
            "playbook_min_source_families",
            payload["playbook_min_source_families"],
        ),
        manual_review_required=_require_payload_bool(
            "manual_review_required",
            payload["manual_review_required"],
        ),
        observed_liquidity_usd=_decimal_from_payload(
            "observed_liquidity_usd",
            payload["observed_liquidity_usd"],
        ),
        observed_spread_probability=_decimal_from_payload(
            "observed_spread_probability",
            payload["observed_spread_probability"],
        ),
        evidence_source_count=_decimal_from_payload(
            "evidence_source_count",
            payload["evidence_source_count"],
        ),
        evidence_age_hours=_decimal_from_payload(
            "evidence_age_hours",
            payload["evidence_age_hours"],
        ),
        playbook_exists=_require_payload_bool(
            "playbook_exists",
            payload["playbook_exists"],
        ),
        playbook_settled_example_count=_decimal_from_payload(
            "playbook_settled_example_count",
            payload["playbook_settled_example_count"],
        ),
        playbook_source_family_count=_decimal_from_payload(
            "playbook_source_family_count",
            payload["playbook_source_family_count"],
        ),
        manual_review_completed=_require_payload_bool(
            "manual_review_completed",
            payload["manual_review_completed"],
        ),
        readiness_status=_require_readiness_status(
            "readiness_status",
            payload["readiness_status"],
        ),
        reason_codes=_reason_codes_from_payload(payload["reason_codes"]),
        manual_next_step=_require_public_text(
            "manual_next_step",
            payload["manual_next_step"],
        ),
        payload_digest=payload["payload_digest"],
        paper_only=_require_payload_bool("paper_only", payload["paper_only"]),
        report_only=_require_payload_bool("report_only", payload["report_only"]),
        readonly=_require_payload_bool("readonly", payload["readonly"]),
    )
    canonical_payload = _public_payload(report)
    if canonical_payload != payload:
        raise ValueError("public payload must match normalized report")
    return canonical_payload


def _payload_digest(payload: dict[str, Any]) -> str:
    payload_without_digest = _sequenced_digest_payload(payload)
    encoded = json.dumps(
        payload_without_digest,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _sequenced_digest_payload(payload: dict[str, Any]) -> dict[str, Any]:
    names = (
        "config_version",
        "category_id",
        "domain_policy_id",
        "playbook_id",
        "min_liquidity_usd",
        "max_spread_probability",
        "evidence_quorum",
        "freshness_sla_hours",
        "playbook_min_settled_examples",
        "playbook_min_source_families",
        "manual_review_required",
        "observed_liquidity_usd",
        "observed_spread_probability",
        "evidence_source_count",
        "evidence_age_hours",
        "playbook_exists",
        "playbook_settled_example_count",
        "playbook_source_family_count",
        "manual_review_completed",
        "readiness_status",
        "reason_codes",
        "manual_next_step",
        "paper_only",
        "report_only",
        "readonly",
    )
    return {name: payload[name] for name in names}


def _apply_or_verify_digest(
    report: CategoryPlaybookCategoryThresholdDomainPolicyReadinessReport,
    digest_bootstrap: object,
) -> None:
    expected_digest = _payload_digest(_public_payload_without_digest(report))
    if report.payload_digest == "":
        if digest_bootstrap is not _REPORT_DIGEST_BOOTSTRAP:
            raise ValueError("payload_digest is required")
        object.__setattr__(report, "payload_digest", expected_digest)
    elif report.payload_digest != expected_digest:
        raise ValueError("payload_digest must match public payload")


def _public_payload_without_digest(
    report: CategoryPlaybookCategoryThresholdDomainPolicyReadinessReport,
) -> dict[str, Any]:
    payload = _public_payload(report)
    del payload["payload_digest"]
    return payload


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_category_id(value: object) -> str:
    category_id = _require_public_text("category_id", value)
    if category_id not in SUPPORTED_CATEGORY_IDS:
        raise ValueError("category_id must be supported")
    return category_id


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    normalized = value.strip()
    if not normalized or normalized != value:
        raise ValueError(f"{field_name} must be nonblank trimmed text")
    if not all(ch.islower() or ch.isdigit() or ch in "-_" for ch in normalized):
        raise ValueError(f"{field_name} must contain public identifier characters")
    return normalized


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be bool")


def _require_payload_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be bool")
    return value


def _require_readiness_status(field_name: str, value: object) -> str:
    status = _require_public_text(field_name, value)
    if status not in CATEGORY_PLAYBOOK_CATEGORY_THRESHOLD_DOMAIN_POLICY_READINESS_STATUSES:
        raise ValueError(f"{field_name} must be supported")
    return status


def _normalize_money(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(MONEY_QUANTUM)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(PROBABILITY_QUANTUM)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.quantize(COUNT_QUANTUM):
        raise ValueError(f"{field_name} must be an integral Decimal")
    return value.quantize(COUNT_QUANTUM)


def _normalize_positive_hours(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_hours(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be above zero")
    return normalized


def _normalize_nonnegative_hours(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(HOUR_QUANTUM)


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for item in value:
        code = _require_public_text("reason_code", item)
        if code not in REASON_CODES:
            raise ValueError("reason_codes must be supported")
        normalized.append(code)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return tuple(normalized)


def _reason_codes_from_payload(value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError("reason_codes must be a list")
    return _normalize_reason_codes(tuple(value))


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        return Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc


def _decimal_to_string(value: Decimal) -> str:
    return format(value, "f")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a digest string")
    if len(value) != 64 or any(ch not in HEX_CHARS for ch in value):
        raise ValueError(f"{field_name} must be a digest string")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


__all__ = (
    "DEFAULT_CATEGORY_PLAYBOOK_CATEGORY_THRESHOLD_DOMAIN_POLICY_READINESS_VERSION",
    "CATEGORY_PLAYBOOK_CATEGORY_THRESHOLD_DOMAIN_POLICY_READINESS_STATUSES",
    "SUPPORTED_CATEGORY_IDS",
    "CategoryPlaybookCategoryThresholdDomainPolicyReadinessConfig",
    "CategoryPlaybookCategoryThresholdDomainPolicyReadinessInput",
    "CategoryPlaybookCategoryThresholdDomainPolicyReadinessReport",
    "category_playbook_category_threshold_domain_policy_readiness_config",
    "build_category_playbook_category_threshold_domain_policy_readiness_report",
    "category_playbook_category_threshold_domain_policy_readiness_payload",
)
