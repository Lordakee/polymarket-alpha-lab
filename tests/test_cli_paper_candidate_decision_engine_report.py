from __future__ import annotations

import ast
import json
import inspect
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from polymarket_alpha_lab.cli import main
import polymarket_alpha_lab.cli as cli_module
from polymarket_alpha_lab.team_paper_guard import json_ready_no_floats
from tests.test_paper_candidate_decision_engine_local_input import _bundle


COMMAND = "paper-candidate-decision-engine-report"


def _reason_count(reason_code: str, count: str) -> SimpleNamespace:
    return SimpleNamespace(
        reason_code=reason_code,
        count=Decimal(count),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _engine_report(**overrides: object) -> SimpleNamespace:
    values: dict[str, object] = {
        "generated_at": datetime(2026, 7, 7, 12, 0, tzinfo=UTC),
        "config_version": "paper-candidate-decision-engine-v0",
        "candidate_count": Decimal("3"),
        "reject_count": Decimal("1"),
        "watch_count": Decimal("1"),
        "research_more_count": Decimal("0"),
        "paper_recommend_count": Decimal("1"),
        "reason_counts": (
            _reason_count("candidate_decision_paper_recommend", "1"),
            _reason_count("candidate_decision_reject", "1"),
        ),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_candidate_decision_engine_report_cli_uses_injected_runner_without_client(
    tmp_path: Path,
    capsys: Any,
) -> None:
    input_path = tmp_path / "candidate-bundles.jsonl"
    input_path.write_text("", encoding="utf-8")
    before = input_path.read_bytes()
    runner_calls: list[dict[str, object]] = []
    client_factory_calls = 0

    def fake_runner(**kwargs: object) -> object:
        runner_calls.append(dict(kwargs))
        return _engine_report()

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [COMMAND, "--input", str(input_path)],
        paper_candidate_decision_engine_runner=fake_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert input_path.read_bytes() == before
    assert len(runner_calls) == 1
    assert runner_calls[0]["input_path"] == input_path
    generated_at = runner_calls[0]["generated_at"]
    assert type(generated_at) is datetime
    assert generated_at.tzinfo is UTC

    captured = capsys.readouterr()
    assert f"{COMMAND}:" in captured.out
    assert "candidate_count=3" in captured.out
    assert "reject=1" in captured.out
    assert "watch=1" in captured.out
    assert "research_more=0" in captured.out
    assert "paper_recommend=1" in captured.out
    assert "candidate_decision_paper_recommend:1" in captured.out
    assert "candidate_decision_reject:1" in captured.out
    assert "paper_only=True report_only=True readonly=True" in captured.out
    assert captured.err == ""


def test_candidate_decision_engine_report_cli_rejects_bad_hard_flags_before_summary(
    tmp_path: Path,
    capsys: Any,
) -> None:
    input_path = tmp_path / "candidate-bundles.jsonl"
    input_path.write_text("", encoding="utf-8")
    client_factory_calls = 0

    def bad_runner(**_kwargs: object) -> object:
        return _engine_report(readonly=False)

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [COMMAND, "--input", str(input_path)],
        paper_candidate_decision_engine_runner=bad_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert f"{COMMAND} failed:" in captured.err
    assert "readonly must be True" in captured.err


def test_candidate_decision_engine_report_cli_uses_redacted_formatter(
    tmp_path: Path,
    capsys: Any,
) -> None:
    input_path = tmp_path / "candidate-bundles.jsonl"
    input_path.write_text("", encoding="utf-8")
    client_factory_calls = 0

    def unsafe_runner(**_kwargs: object) -> object:
        return _engine_report(candidate_count="candidate_id:secret")

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [COMMAND, "--input", str(input_path)],
        paper_candidate_decision_engine_runner=unsafe_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "unsafe public summary value" in captured.err


def test_candidate_decision_engine_report_cli_reads_empty_local_input_without_client(
    tmp_path: Path,
    capsys: Any,
) -> None:
    input_path = tmp_path / "empty-candidate-bundles.jsonl"
    input_path.write_text("", encoding="utf-8")
    client_factory_calls = 0

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [COMMAND, "--input", str(input_path)],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert input_path.read_bytes() == b""
    captured = capsys.readouterr()
    assert f"{COMMAND}:" in captured.out
    assert "candidate_count=0" in captured.out
    assert "reject=0" in captured.out
    assert "watch=0" in captured.out
    assert "research_more=0" in captured.out
    assert "paper_recommend=0" in captured.out
    assert "reason_code_counts: none" in captured.out
    assert "paper_only=True report_only=True readonly=True" in captured.out
    assert captured.err == ""


def test_candidate_decision_engine_report_cli_reads_nonempty_jsonl_with_local_helper_without_client(
    tmp_path: Path,
    capsys: Any,
    monkeypatch: Any,
) -> None:
    input_path = tmp_path / "candidate-bundles.jsonl"
    payload = json_ready_no_floats(_bundle())
    assert type(payload) is dict
    input_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    client_factory_calls = 0
    local_helper_calls: list[dict[str, object]] = []

    from polymarket_alpha_lab import paper_candidate_decision_engine_local_input

    real_local_helper = (
        paper_candidate_decision_engine_local_input
        .load_paper_candidate_decision_engine_report_from_local_input
    )

    def tracking_local_helper(**kwargs: object) -> object:
        local_helper_calls.append(dict(kwargs))
        return real_local_helper(**kwargs)

    monkeypatch.setattr(
        paper_candidate_decision_engine_local_input,
        "load_paper_candidate_decision_engine_report_from_local_input",
        tracking_local_helper,
    )

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [COMMAND, "--input", str(input_path)],
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 0
    assert client_factory_calls == 0
    assert len(local_helper_calls) == 1
    assert local_helper_calls[0]["candidate_bundle_path"] == input_path
    assert local_helper_calls[0].get("candidate_bundle_rows") is None
    assert local_helper_calls[0].get("candidate_bundle_text") is None
    generated_at = local_helper_calls[0]["generated_at"]
    assert type(generated_at) is datetime
    assert generated_at.tzinfo is UTC

    captured = capsys.readouterr()
    assert f"{COMMAND}:" in captured.out
    assert "candidate_count=1" in captured.out
    assert "paper_recommend=1" in captured.out
    assert "reason_code_counts:" in captured.out
    assert "candidate-alpha" not in captured.out
    assert "market-alpha" not in captured.out
    assert "Will the alpha event resolve yes?" not in captured.out
    assert "paper_only=True report_only=True readonly=True" in captured.out
    assert captured.err == ""


def test_candidate_decision_engine_report_cli_scope_has_no_live_or_db_surface() -> None:
    source = inspect.getsource(cli_module._run_paper_candidate_decision_engine_report)
    source += inspect.getsource(
        cli_module._read_paper_candidate_decision_engine_candidate_bundles,
    )
    source += inspect.getsource(
        cli_module._format_paper_candidate_decision_engine_report_summary,
    )
    tree = ast.parse(source)

    forbidden_terms = (
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "urllib",
        "wallet",
        "private_key",
        "place_order",
        "create_order",
        "cancel_order",
        "exchange",
        "live_trading",
        "connect(",
        "commit(",
        "rollback(",
    )
    lowered = source.lower()
    assert [term for term in forbidden_terms if term in lowered] == []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
