from __future__ import annotations

import ast
import importlib
import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_candidate_information_decay_expected_value_v2.py"
)


class DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_candidate_information_decay_expected_value_v2",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(candidate_id: str = "candidate_alpha", **overrides: object):
    module = api()
    values: dict[str, object] = {
        "candidate_id": candidate_id,
        "base_expected_value_bps": d("100.000000"),
        "source_age_seconds": d("3600"),
        "source_type": "secondary",
        "contradiction_count": d("2"),
        "catalyst_urgency_score": d("0.500000"),
        "settlement_horizon_seconds": d("604800"),
        "reason_codes": ("research_signal_present",),
    }
    values.update(overrides)
    return module.StrategyCandidateInformationDecayExpectedValueV2Input(**values)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {}
    values.update(overrides)
    return module.StrategyCandidateInformationDecayExpectedValueV2Config(**values)


def report(*items: object, **overrides: object):
    module = api()
    report_config = overrides.pop("config", None)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    return module.build_strategy_candidate_information_decay_expected_value_v2_report(
        list(items),
        config=report_config,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_information_decay_expected_value_adjusts_each_component_and_rolls_up() -> None:
    decay_report = report(
        candidate("candidate_pass"),
        candidate(
            "candidate_watch",
            source_age_seconds=d("10800"),
            source_type="unverified",
            contradiction_count=d("10"),
            catalyst_urgency_score=d("1.000000"),
            settlement_horizon_seconds=d("1209600"),
        ),
        candidate(
            "candidate_blocked",
            base_expected_value_bps=d("-5.000000"),
            source_age_seconds=d("0"),
            source_type="official",
            contradiction_count=d("0"),
            catalyst_urgency_score=d("0.000000"),
            settlement_horizon_seconds=d("0"),
        ),
    )

    assert is_dataclass(decay_report)
    assert decay_report.candidate_count == d("3")
    assert decay_report.pass_count == d("1")
    assert decay_report.watch_count == d("1")
    assert decay_report.blocked_count == d("1")
    assert decay_report.max_adjusted_expected_value_bps == d("13.500000")
    assert decay_report.min_combined_information_multiplier == d("0.008333")
    assert decay_report.report_status == "blocked"

    passed, watched, blocked = decay_report.rows
    assert passed.candidate_id == "candidate_pass"
    assert passed.source_age_multiplier == d("0.500000")
    assert passed.source_type_multiplier == d("0.750000")
    assert passed.contradiction_multiplier == d("0.800000")
    assert passed.catalyst_urgency_multiplier == d("0.900000")
    assert passed.settlement_horizon_multiplier == d("0.500000")
    assert passed.combined_information_multiplier == d("0.135000")
    assert passed.information_decay_bps == d("86.500000")
    assert passed.adjusted_expected_value_bps == d("13.500000")
    assert passed.adjustment_status == "pass"
    assert passed.reason_codes == (
        "research_signal_present",
        "information_decay_expected_value_v2",
        "information_decay_pass",
        "source_age_decay_applied",
        "source_type_secondary",
        "weak_source_type_decay_applied",
        "source_contradiction_decay_applied",
        "catalyst_urgency_decay_applied",
        "settlement_horizon_decay_applied",
        "adjusted_expected_value_meets_minimum",
    )

    assert watched.candidate_id == "candidate_watch"
    assert watched.source_age_multiplier == d("0.250000")
    assert watched.source_type_multiplier == d("0.500000")
    assert watched.contradiction_multiplier == d("0.250000")
    assert watched.catalyst_urgency_multiplier == d("0.800000")
    assert watched.settlement_horizon_multiplier == d("0.333333")
    assert watched.combined_information_multiplier == d("0.008333")
    assert watched.adjusted_expected_value_bps == d("0.833300")
    assert watched.adjustment_status == "watch"

    assert blocked.candidate_id == "candidate_blocked"
    assert blocked.combined_information_multiplier == d("1.000000")
    assert blocked.information_decay_bps == d("0.000000")
    assert blocked.adjusted_expected_value_bps == d("-5.000000")
    assert blocked.adjustment_status == "blocked"


def test_payload_serializes_decimal_strings_and_revalidates_digests() -> None:
    module = api()
    decay_report = report(candidate("candidate_payload"))

    payload = module.strategy_candidate_information_decay_expected_value_v2_payload(
        decay_report,
    )

    assert payload["candidate_count"] == "1"
    assert payload["rows"][0]["adjusted_expected_value_bps"] == "13.500000"
    assert payload["rows"][0]["combined_information_multiplier"] == "0.135000"
    assert payload["derived_validation_digest"] == decay_report.derived_validation_digest
    assert payload["rows"][0]["derived_validation_digest"].startswith("scidev-v2:")
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)

    readonly_payload = module.strategy_candidate_information_decay_expected_value_v2_payload(
        {
            "adjusted_expected_value_bps": d("1.250000"),
            "rows": (
                {
                    "combined_information_multiplier": d("0.500000"),
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                },
            ),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )
    assert readonly_payload["adjusted_expected_value_bps"] == "1.250000"
    assert readonly_payload["rows"][0]["combined_information_multiplier"] == "0.500000"

    with pytest.raises(ValueError, match="readonly"):
        module.strategy_candidate_information_decay_expected_value_v2_payload(
            {"paper_only": True, "report_only": True, "readonly": False},
        )
    with pytest.raises(ValueError, match="float"):
        module.strategy_candidate_information_decay_expected_value_v2_payload(
            {"score": 0.1, "paper_only": True, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="Decimal"):
        module.strategy_candidate_information_decay_expected_value_v2_payload(
            {"score": 1, "paper_only": True, "report_only": True, "readonly": True},
        )

    row = decay_report.rows[0]
    object.__setattr__(row, "adjusted_expected_value_bps", d("99.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest|tamper"):
        module.strategy_candidate_information_decay_expected_value_v2_payload(decay_report)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    sample_config = config()
    sample = candidate()
    decay_report = report(sample)
    row = decay_report.rows[0]

    public_decimal_fields = {
        "minimum_adjusted_expected_value_bps",
        "watch_adjusted_expected_value_bps",
        "source_age_half_life_seconds",
        "contradiction_penalty_per_count",
        "minimum_contradiction_multiplier",
        "catalyst_urgency_decay_ceiling",
        "settlement_horizon_half_life_seconds",
        "base_expected_value_bps",
        "source_age_seconds",
        "contradiction_count",
        "catalyst_urgency_score",
        "settlement_horizon_seconds",
        "source_age_multiplier",
        "source_type_multiplier",
        "contradiction_multiplier",
        "catalyst_urgency_multiplier",
        "settlement_horizon_multiplier",
        "combined_information_multiplier",
        "information_decay_bps",
        "adjusted_expected_value_bps",
        "candidate_count",
        "pass_count",
        "watch_count",
        "blocked_count",
        "max_adjusted_expected_value_bps",
        "min_combined_information_multiplier",
        "average_combined_information_multiplier",
    }
    for item in (sample_config, sample, row, decay_report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.readonly = False  # type: ignore[misc]
        for field in fields(item):
            if field.name in public_decimal_fields:
                assert type(getattr(item, field.name)) is Decimal

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        candidate(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(row, readonly=False)
    with pytest.raises(ValueError, match="base_expected_value_bps must be a Decimal"):
        candidate(base_expected_value_bps=1)
    with pytest.raises(ValueError, match="must use six decimal places or fewer"):
        candidate(catalyst_urgency_score=d("0.1000001"))
    with pytest.raises(ValueError, match="must be a Decimal"):
        config(
            contradiction_penalty_per_count=DecimalSubclass("0.100000"),
        )
    with pytest.raises(ValueError, match="source_type"):
        candidate(source_type="message_board")
    with pytest.raises(ValueError, match="contradiction_count must be integral"):
        candidate(contradiction_count=d("1.500000"))
    with pytest.raises(ValueError, match="source_age_seconds must be whole seconds"):
        candidate(source_age_seconds=d("1.500000"))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        candidate(reason_codes=["research_signal_present"])


def test_unsafe_public_keys_and_values_are_rejected() -> None:
    module = api()
    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )

    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe public"):
            module.strategy_candidate_information_decay_expected_value_v2_payload(
                {
                    f"{term}_field": "redacted",
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                },
            )
        with pytest.raises(ValueError, match="unsafe public"):
            module.strategy_candidate_information_decay_expected_value_v2_payload(
                {
                    "note": f"contains {term} surface",
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                },
            )

    with pytest.raises(ValueError, match="unsafe public"):
        candidate(candidate_id="candidate_wallet")
    with pytest.raises(ValueError, match="reason_codes"):
        candidate(reason_codes=("trade_term",))

    class PayloadDict(dict):
        pass

    with pytest.raises(ValueError, match="plain"):
        module.strategy_candidate_information_decay_expected_value_v2_payload(
            {
                "nested": PayloadDict({"note": "safe"}),
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )


def test_module_scope_has_no_unsafe_runtime_surface_or_float_literals() -> None:
    module = api()
    source_text = inspect.getsource(module)
    tree = ast.parse(source_text)

    assert MODULE_PATH.exists()
    assert module.__all__ == (
        "DEFAULT_STRATEGY_CANDIDATE_INFORMATION_DECAY_EXPECTED_VALUE_V2_CONFIG_VERSION",
        "SOURCE_TYPES",
        "ROW_STATUSES",
        "REPORT_STATUSES",
        "StrategyCandidateInformationDecayExpectedValueV2Config",
        "StrategyCandidateInformationDecayExpectedValueV2Input",
        "StrategyCandidateInformationDecayExpectedValueV2Row",
        "StrategyCandidateInformationDecayExpectedValueV2Report",
        "adjust_strategy_candidate_information_decay_expected_value_v2",
        "build_strategy_candidate_information_decay_expected_value_v2_report",
        "strategy_candidate_information_decay_expected_value_v2_payload",
        "reject_strategy_candidate_information_decay_expected_value_v2_unsafe_payload",
    )
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(tree)
    )

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_roots.add(node.module.split(".", 1)[0])
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}

    assert imported_roots <= {
        "__future__",
        "dataclasses",
        "decimal",
        "hashlib",
        "typing",
    }
    forbidden_source_fragments = (
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "postgres",
        "sqlite",
        "private_key",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
        "open(",
        "Path(",
    )
    for fragment in forbidden_source_fragments:
        assert fragment not in source_text

    lowered = source_text.lower()
    unsafe_surface_terms = (
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "wallet",
        " auth",
        "buy",
        "sell",
        "trade",
        "trading",
        "live",
    )
    for term in unsafe_surface_terms:
        assert term not in lowered

    root = importlib.import_module("polymarket_alpha_lab")
    assert "strategy_candidate_information_decay_expected_value_v2" not in getattr(
        root,
        "__all__",
        (),
    )
