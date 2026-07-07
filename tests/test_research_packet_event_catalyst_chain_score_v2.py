from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from importlib import import_module
from json import dumps
from typing import Any

import pytest


CONFIG_VERSION = "research-packet-event-catalyst-chain-score-v2"
EXPECTED_COMPLETE_DIGEST = (
    "b008cf24c8e045c0d1a0ec663cce36c5f4c4a8b039ef9717a434db142b71169f"
)


class DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def api():
    return import_module(
        "polymarket_alpha_lab.research_packet_event_catalyst_chain_score_v2",
    )


def chain_input(**overrides: Any):
    values: dict[str, Any] = {
        "packet_id": "packet-alpha",
        "market_slug": "fed-cut-by-september",
        "initial_catalyst_score": d("1.000000"),
        "confirmation_source_score": d("1.000000"),
        "market_probability_move_score": d("1.000000"),
        "follow_up_evidence_score": d("1.000000"),
        "contradiction_resolution_score": d("1.000000"),
        "resolution_source_link_score": d("1.000000"),
    }
    values.update(overrides)
    return api().ResearchPacketEventCatalystChainScoreV2Input(**values)


def score(subject: object | None = None):
    return api().score_research_packet_event_catalyst_chain_score_v2(
        chain_input() if subject is None else subject,
    )


def test_complete_event_catalyst_chain_scores_one_and_stable_digest() -> None:
    module = api()

    result = score()

    assert result == module.ResearchPacketEventCatalystChainScoreV2Result(
        config_version=CONFIG_VERSION,
        packet_id="packet-alpha",
        market_slug="fed-cut-by-september",
        initial_catalyst_score=d("1.000000"),
        confirmation_source_score=d("1.000000"),
        market_probability_move_score=d("1.000000"),
        follow_up_evidence_score=d("1.000000"),
        contradiction_resolution_score=d("1.000000"),
        resolution_source_link_score=d("1.000000"),
        catalyst_chain_score=d("1.000000"),
        catalyst_chain_status="complete",
        component_gaps=(),
        reason_codes=("event_catalyst_chain_complete",),
        chain_digest=EXPECTED_COMPLETE_DIGEST,
    )
    assert type(result.catalyst_chain_score) is Decimal
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert result.payload["chain_digest"] == EXPECTED_COMPLETE_DIGEST
    with pytest.raises(FrozenInstanceError):
        result.catalyst_chain_status = "blocked"  # type: ignore[misc]


def test_watch_status_captures_nonblocking_catalyst_chain_gaps() -> None:
    result = score(
        chain_input(
            market_probability_move_score=d("0.500000"),
            follow_up_evidence_score=d("0.500000"),
            resolution_source_link_score=d("0.900000"),
        ),
    )

    assert result.catalyst_chain_score == d("0.835000")
    assert result.catalyst_chain_status == "watch"
    assert result.component_gaps == (
        "market_probability_move",
        "follow_up_evidence",
    )
    assert result.reason_codes == (
        "market_probability_move_missing",
        "follow_up_evidence_missing",
        "event_catalyst_chain_watch_score",
    )
    assert result.chain_digest == score(
        chain_input(
            market_probability_move_score=d("0.500000"),
            follow_up_evidence_score=d("0.500000"),
            resolution_source_link_score=d("0.900000"),
        ),
    ).chain_digest
    assert result.chain_digest != score().chain_digest


def test_blocked_status_requires_confirmation_contradiction_and_resolution_links() -> None:
    result = score(
        chain_input(
            confirmation_source_score=d("0.600000"),
            market_probability_move_score=d("0.500000"),
            follow_up_evidence_score=d("0.300000"),
            contradiction_resolution_score=d("0.200000"),
            resolution_source_link_score=d("0.600000"),
        ),
    )

    assert result.catalyst_chain_score == d("0.560000")
    assert result.catalyst_chain_status == "blocked"
    assert result.component_gaps == (
        "confirmation_source",
        "market_probability_move",
        "follow_up_evidence",
        "contradiction_resolution",
        "resolution_source_link",
    )
    assert result.reason_codes == (
        "confirmation_source_missing",
        "market_probability_move_missing",
        "follow_up_evidence_missing",
        "contradiction_unresolved",
        "resolution_source_link_missing",
        "event_catalyst_chain_blocked_score",
    )


def test_payload_is_json_ready_decimal_safe_and_readonly() -> None:
    module = api()
    result = score()

    payload = module.research_packet_event_catalyst_chain_score_v2_payload(result)

    dumps(payload, sort_keys=True)
    assert payload == result.payload
    assert payload["config_version"] == CONFIG_VERSION
    assert payload["initial_catalyst_score"] == "1.000000"
    assert payload["catalyst_chain_score"] == "1.000000"
    assert payload["catalyst_chain_status"] == "complete"
    assert payload["component_gaps"] == []
    assert payload["reason_codes"] == ["event_catalyst_chain_complete"]
    assert payload["chain_digest"] == EXPECTED_COMPLETE_DIGEST
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    _assert_no_float_or_int(payload)


def test_inputs_validate_decimal_types_ranges_and_hard_flags() -> None:
    with pytest.raises(ValueError, match="initial_catalyst_score must be a Decimal"):
        chain_input(initial_catalyst_score=1)
    with pytest.raises(ValueError, match="market_probability_move_score must be a Decimal"):
        chain_input(market_probability_move_score=1.0)
    with pytest.raises(ValueError, match="follow_up_evidence_score must be a Decimal"):
        chain_input(follow_up_evidence_score=DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="confirmation_source_score must be between"):
        chain_input(confirmation_source_score=d("1.000001"))
    with pytest.raises(ValueError, match="contradiction_resolution_score must be between"):
        chain_input(contradiction_resolution_score=d("-0.000001"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        chain_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        chain_input(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        score(chain_input(readonly=False))


def test_manual_result_rebuilds_are_validated_against_scoring_fields() -> None:
    valid = score()

    with pytest.raises(ValueError, match="catalyst_chain_score must match"):
        replace(valid, catalyst_chain_score=d("0.900000"))
    with pytest.raises(ValueError, match="component_gaps must match"):
        replace(valid, component_gaps=("follow_up_evidence",))
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(valid, reason_codes=("follow_up_evidence_missing",))
    with pytest.raises(ValueError, match="chain_digest must match"):
        replace(valid, chain_digest="0" * 64)


def test_accepts_only_exact_input_type() -> None:
    with pytest.raises(
        ValueError,
        match="value must be a ResearchPacketEventCatalystChainScoreV2Input",
    ):
        api().score_research_packet_event_catalyst_chain_score_v2(object())


def test_public_numeric_annotations_are_decimal_only() -> None:
    decimal_fields = {
        "ResearchPacketEventCatalystChainScoreV2Input": {
            "initial_catalyst_score",
            "confirmation_source_score",
            "market_probability_move_score",
            "follow_up_evidence_score",
            "contradiction_resolution_score",
            "resolution_source_link_score",
        },
        "ResearchPacketEventCatalystChainScoreV2Result": {
            "initial_catalyst_score",
            "confirmation_source_score",
            "market_probability_move_score",
            "follow_up_evidence_score",
            "contradiction_resolution_score",
            "resolution_source_link_score",
            "catalyst_chain_score",
        },
    }

    for class_name, field_names in decimal_fields.items():
        annotations = getattr(api(), class_name).__annotations__
        for field_name in field_names:
            assert annotations[field_name] == "Decimal"


def test_module_has_no_io_network_execution_or_persistence_surface() -> None:
    source = inspect.getsource(api())
    tree = ast.parse(source)
    forbidden_import_roots = {
        "boto3",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "supabase",
        "urllib",
        "web3",
    }
    forbidden_calls = {
        "commit",
        "connect",
        "execute",
        "executemany",
        "open",
        "request",
        "urlopen",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls

    lowered = source.lower()
    for token in (
        "account",
        "balance",
        "cancel",
        "clob",
        "database",
        "db_write",
        "live trading",
        "private_key",
        "submit",
        "wallet",
    ):
        assert token not in lowered


def _assert_no_float_or_int(value: object) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected concrete numeric payload value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_float_or_int(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_float_or_int(item)
