from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from typing import get_type_hints

import pytest

from polymarket_alpha_lab.probability_event_team_consensus_quorum_report import (
    PROBABILITY_EVENT_TEAM_CONSENSUS_QUORUM_REPORT_VERSION,
    ProbabilityEventTeamConsensusQuorumInput,
    ProbabilityEventTeamConsensusQuorumReport,
    build_probability_event_team_consensus_quorum_report,
    probability_event_team_consensus_quorum_report_digest,
    probability_event_team_consensus_quorum_report_payload,
)


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "probability_event_team_consensus_quorum_report.py"
)


def d(value: str) -> Decimal:
    return Decimal(value)


def quorum_input(**overrides: object) -> ProbabilityEventTeamConsensusQuorumInput:
    values = {
        "supporting_team_count": d("4"),
        "dissenting_team_count": d("1"),
        "required_consensus_count": d("3"),
        "average_confidence_probability": d("0.820000"),
        "disagreement_severity_probability": d("0.120000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return ProbabilityEventTeamConsensusQuorumInput(**values)


def report(**overrides: object) -> ProbabilityEventTeamConsensusQuorumReport:
    return build_probability_event_team_consensus_quorum_report(
        quorum_input(**overrides),
    )


def test_consensus_reached_payload_digest_and_public_schema() -> None:
    first = report()
    second = report()

    assert type(first) is ProbabilityEventTeamConsensusQuorumReport
    assert is_dataclass(first)
    assert first.__dataclass_params__.frozen is True
    assert first.config_version == PROBABILITY_EVENT_TEAM_CONSENSUS_QUORUM_REPORT_VERSION
    assert first.consensus_status == "consensus_reached"
    assert first.manual_next_step == "prepare_readonly_public_probability_summary"
    assert first.reason_codes == ("required_quorum_met", "confidence_ready")
    assert first.supporting_team_count == d("4.000000")
    assert first.dissenting_team_count == d("1.000000")
    assert first.required_consensus_count == d("3.000000")
    assert first.average_confidence_probability == d("0.820000")
    assert first.disagreement_severity_probability == d("0.120000")
    assert first.paper_only is True
    assert first.report_only is True
    assert first.readonly is True
    assert first == second
    assert first.payload_digest == second.payload_digest
    assert probability_event_team_consensus_quorum_report_digest(first) == first.payload_digest

    payload = probability_event_team_consensus_quorum_report_payload(first)
    assert payload == first.public_payload
    assert payload == {
        "config_version": "probability-event-team-consensus-quorum-v0",
        "supporting_team_count": "4.000000",
        "dissenting_team_count": "1.000000",
        "required_consensus_count": "3.000000",
        "average_confidence_probability": "0.820000",
        "disagreement_severity_probability": "0.120000",
        "consensus_status": "consensus_reached",
        "reason_codes": ("required_quorum_met", "confidence_ready"),
        "manual_next_step": "prepare_readonly_public_probability_summary",
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "payload_digest": first.payload_digest,
    }
    json.dumps(payload, sort_keys=True)
    expected_digest = sha256(
        json.dumps(
            {**payload, "payload_digest": ""},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8"),
    ).hexdigest()
    assert first.payload_digest == expected_digest
    assert _float_or_int_paths(payload) == ()

    with pytest.raises(TypeError, match="public_payload is immutable"):
        payload["consensus_status"] = "blocked"


def test_consensus_blocked_when_quorum_is_missing() -> None:
    result = report(
        supporting_team_count=d("2"),
        dissenting_team_count=d("0"),
        required_consensus_count=d("3"),
        average_confidence_probability=d("0.910000"),
        disagreement_severity_probability=d("0.050000"),
    )

    assert result.consensus_status == "quorum_blocked"
    assert result.reason_codes == ("required_quorum_missing",)
    assert result.manual_next_step == "collect_additional_team_reviews_before_public_summary"


def test_consensus_needs_manual_review_when_dissent_or_confidence_blocks_release() -> None:
    result = report(
        supporting_team_count=d("5"),
        dissenting_team_count=d("2"),
        required_consensus_count=d("3"),
        average_confidence_probability=d("0.540000"),
        disagreement_severity_probability=d("0.760000"),
    )

    assert result.consensus_status == "manual_review_required"
    assert result.reason_codes == (
        "dissent_present",
        "confidence_below_floor",
        "disagreement_severity_high",
    )
    assert result.manual_next_step == "route_to_manual_probability_reconciliation"


def test_frozen_decimal_only_exact_types_and_hard_flags() -> None:
    input_value = quorum_input()
    result = report()

    assert is_dataclass(input_value)
    assert input_value.__dataclass_params__.frozen is True
    with pytest.raises(FrozenInstanceError):
        input_value.supporting_team_count = d("5")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.consensus_status = "manual_review_required"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadInput(ProbabilityEventTeamConsensusQuorumInput):
            pass

    with pytest.raises(TypeError):

        class BadReport(ProbabilityEventTeamConsensusQuorumReport):
            pass

    with pytest.raises(ValueError, match="supporting_team_count"):
        quorum_input(supporting_team_count=4)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="average_confidence_probability"):
        quorum_input(average_confidence_probability=d("1.100000"))
    with pytest.raises(ValueError, match="required_consensus_count"):
        quorum_input(required_consensus_count=d("0"))
    with pytest.raises(ValueError, match="paper_only"):
        quorum_input(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="reason_codes"):
        replace(result, reason_codes=("confidence_ready",))
    with pytest.raises(ValueError, match="payload_digest"):
        probability_event_team_consensus_quorum_report_payload(
            replace(result, payload_digest="0" * 64),
        )

    hints = get_type_hints(ProbabilityEventTeamConsensusQuorumReport)
    for field in fields(ProbabilityEventTeamConsensusQuorumReport):
        value = getattr(result, field.name)
        if field.name.endswith("_count") or field.name.endswith("_probability"):
            assert type(value) is Decimal
            assert hints[field.name] is Decimal
        elif type(value) in (int, float):
            pytest.fail(f"runtime public numeric field is not Decimal: {field.name}")


def test_module_is_readonly_report_only_and_has_no_execution_or_persistence_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "web3",
        "live",
        "auth",
        "private_key",
        "api_key",
        "secret_key",
        "wallet",
        "order",
        "signature",
        "signing",
        "execute",
        "jsonl",
        "database",
        "network",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "urllib",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "web3",
    }
    forbidden_call_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "delete",
        "execute",
        "executemany",
        "fetch",
        "insert",
        "open",
        "post",
        "put",
        "rollback",
        "sell",
        "send",
        "sign",
        "upsert",
        "write",
        "write_text",
        "write_bytes",
    }
    imported_roots: set[str] = set()
    call_names: set[str] = set()
    float_constants: list[float] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", maxsplit=1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", maxsplit=1)[0])
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.add(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.add(function.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_constants.append(node.value)

    assert not imported_roots.intersection(forbidden_imports)
    assert not call_names.intersection(forbidden_call_names)
    assert float_constants == []


def _float_or_int_paths(value: object, path: str = "$") -> tuple[str, ...]:
    if type(value) in (int, float, Decimal):
        return (path,)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_float_or_int_paths(item, f"{path}.{key}"))
        return tuple(paths)
    if isinstance(value, (list, tuple)):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_float_or_int_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()
