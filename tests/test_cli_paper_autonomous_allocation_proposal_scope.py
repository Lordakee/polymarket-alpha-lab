from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab import cli
from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_config import (
    ACTION_GATED_QUEUE_DB_DSN_ENV_VAR,
    ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR,
    ACTION_GATED_QUEUE_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_decision_support_config import (
    ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR,
    ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR,
    ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_paper_autonomous_screening_decision_support_gate_config import (
    PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_DSN_ENV_VAR,
    PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_ENABLED_ENV_VAR,
    PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.paper_autonomous_allocation_proposal_psycopg_read import (
    MAX_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_READ_LIMIT,
)


COMMAND = "paper-autonomous-allocation-proposal"


def _set_upstream_db_env(
    monkeypatch: pytest.MonkeyPatch,
    *,
    screening_gate_dsn: str,
    screening_gate_table_name: str = (
        "paper_autonomous_screening_decision_support_gate_reports"
    ),
    decision_support_dsn: str,
    decision_support_table_name: str = (
        "paper_action_gated_queue_decision_support_reports"
    ),
    source_queue_dsn: str,
    source_queue_table_name: str = (
        "paper_action_gated_strategy_recommendation_queue_reports"
    ),
) -> None:
    monkeypatch.setenv(
        PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_ENABLED_ENV_VAR,
        "true",
    )
    monkeypatch.setenv(
        PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_DSN_ENV_VAR,
        screening_gate_dsn,
    )
    monkeypatch.setenv(
        PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_TABLE_ENV_VAR,
        screening_gate_table_name,
    )
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR,
        "true",
    )
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR,
        decision_support_dsn,
    )
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE_ENV_VAR,
        decision_support_table_name,
    )
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_DSN_ENV_VAR, source_queue_dsn)
    monkeypatch.setenv(ACTION_GATED_QUEUE_DB_TABLE_ENV_VAR, source_queue_table_name)


def _reason_count(reason_code: str, report_count: int) -> SimpleNamespace:
    return SimpleNamespace(reason_code=reason_code, report_count=report_count)


def _proposal_report() -> SimpleNamespace:
    return SimpleNamespace(
        proposal_status="pass",
        recommended_next_step="review_paper_autonomous_allocation_proposal",
        screening_gate_status="pass",
        queue_risk_status="pass",
        source_queue_count=2,
        allocation_report=SimpleNamespace(
            input_count=2,
            row_count=2,
            allocated_count=1,
            capped_count=0,
            no_budget_count=0,
            non_recommend_count=0,
            skipped_count=0,
            total_allocated_paper_notional=Decimal("25.000000"),
            remaining_paper_budget=Decimal("75.000000"),
            rows=(
                SimpleNamespace(
                    market_slug="secret-market-slug",
                    question="Will a hidden market resolve yes?",
                    report_sha256=(
                        "abcdef0123456789abcdef0123456789"
                        "abcdef0123456789abcdef0123456789"
                    ),
                ),
            ),
        ),
        reason_code_counts=(
            _reason_count("paper_autonomous_allocation_proposal_passed", 1),
        ),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def test_allocation_cli_requires_enabled_screening_gate_db_before_runner_or_client(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _set_upstream_db_env(
        monkeypatch,
        screening_gate_dsn="postgresql://screening.example.invalid/db",
        decision_support_dsn="postgresql://decision.example.invalid/db",
        source_queue_dsn="postgresql://source.example.invalid/db",
    )
    monkeypatch.delenv(
        PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_ENABLED_ENV_VAR,
        raising=False,
    )
    runner_calls = 0
    client_factory_calls = 0

    def forbidden_runner(**_kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("allocation proposal runner should not run")

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [COMMAND],
        paper_autonomous_allocation_proposal_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert f"{COMMAND} requires autonomous screening gate DB to be enabled" in (
        captured.err
    )


def test_allocation_cli_requires_enabled_decision_support_db(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _set_upstream_db_env(
        monkeypatch,
        screening_gate_dsn="postgresql://screening.example.invalid/db",
        decision_support_dsn="postgresql://decision.example.invalid/db",
        source_queue_dsn="postgresql://source.example.invalid/db",
    )
    monkeypatch.delenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR,
        raising=False,
    )

    exit_code = main(
        [COMMAND],
        paper_autonomous_allocation_proposal_runner=lambda **_kwargs: (
            (_ for _ in ()).throw(AssertionError("runner should not run"))
        ),
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} requires action-gated queue decision-support DB to be enabled" in (
        captured.err
    )


def test_allocation_cli_requires_enabled_source_queue_db(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _set_upstream_db_env(
        monkeypatch,
        screening_gate_dsn="postgresql://screening.example.invalid/db",
        decision_support_dsn="postgresql://decision.example.invalid/db",
        source_queue_dsn="postgresql://source.example.invalid/db",
    )
    monkeypatch.delenv(ACTION_GATED_QUEUE_DB_ENABLED_ENV_VAR, raising=False)

    exit_code = main(
        [COMMAND],
        paper_autonomous_allocation_proposal_runner=lambda **_kwargs: (
            (_ for _ in ()).throw(AssertionError("runner should not run"))
        ),
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} requires action-gated queue DB to be enabled" in captured.err


@pytest.mark.parametrize(
    ("limit", "expected_error"),
    (
        ("0", f"{COMMAND} limit must be positive"),
        ("-1", f"{COMMAND} limit must be positive"),
        (
            "501",
            f"{COMMAND} limit must be less than or equal to "
            f"{MAX_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_READ_LIMIT}",
        ),
    ),
)
def test_allocation_cli_rejects_bad_limit_before_env_runner_or_connect(
    limit: str,
    expected_error: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_calls = 0
    runner_calls = 0
    connect_calls = 0

    def forbidden_env() -> object:
        nonlocal env_calls
        env_calls += 1
        raise AssertionError("upstream DB env should not be read")

    def forbidden_runner(**_kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("allocation proposal runner should not run")

    def forbidden_connect(*_args: object, **_kwargs: object) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("DB connect should not run")

    monkeypatch.setattr(
        cli,
        "from_paper_autonomous_screening_decision_support_gate_db_env",
        forbidden_env,
        raising=False,
    )
    monkeypatch.setattr(
        cli,
        "from_action_gated_strategy_recommendation_queue_decision_support_db_env",
        forbidden_env,
        raising=False,
    )
    monkeypatch.setattr(
        cli,
        "from_action_gated_strategy_recommendation_queue_db_env",
        forbidden_env,
        raising=False,
    )
    monkeypatch.setitem(
        sys.modules,
        "psycopg",
        SimpleNamespace(connect=forbidden_connect),
    )

    exit_code = main(
        [COMMAND, "--limit", limit],
        paper_autonomous_allocation_proposal_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert env_calls == 0
    assert runner_calls == 0
    assert connect_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed: {expected_error}" in captured.err


def test_allocation_cli_uses_injected_runner_before_psycopg_or_client(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    screening_gate_dsn = "postgresql://screening.example.invalid/db"
    decision_support_dsn = "postgresql://decision.example.invalid/db"
    source_queue_dsn = "postgresql://source.example.invalid/db"
    _set_upstream_db_env(
        monkeypatch,
        screening_gate_dsn=screening_gate_dsn,
        decision_support_dsn=decision_support_dsn,
        source_queue_dsn=source_queue_dsn,
    )
    connect_calls = 0
    runner_calls: list[dict[str, object]] = []

    def forbidden_connect(*_args: object, **_kwargs: object) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("psycopg connect should not run with injected runner")

    def fake_runner(**kwargs: object) -> object:
        runner_calls.append(dict(kwargs))
        assert kwargs["screening_gate_dsn"] == screening_gate_dsn
        assert kwargs["action_gated_queue_decision_support_dsn"] == decision_support_dsn
        assert kwargs["source_queue_dsn"] == source_queue_dsn
        assert kwargs["limit"] == 25
        assert isinstance(kwargs["generated_at"], datetime)
        return _proposal_report()

    monkeypatch.setitem(
        sys.modules,
        "psycopg",
        SimpleNamespace(connect=forbidden_connect),
    )

    exit_code = main(
        [COMMAND],
        paper_autonomous_allocation_proposal_runner=fake_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert connect_calls == 0
    assert len(runner_calls) == 1
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out.splitlines() == [
        (
            f"{COMMAND}: proposal_status=pass "
            "recommended_next_step=review_paper_autonomous_allocation_proposal "
            "source_queue_count=2 "
            "screening_gate_status=pass "
            "queue_risk_status=pass "
            "input_count=2 "
            "row_count=2 "
            "allocated_count=1 "
            "capped_count=0 "
            "no_budget_count=0 "
            "non_recommend_count=0 "
            "skipped_count=0 "
            "total_allocated_paper_notional=25.000000 "
            "remaining_paper_budget=75.000000"
        ),
        "reason_code_counts: paper_autonomous_allocation_proposal_passed=1",
    ]
    for secret in (
        screening_gate_dsn,
        decision_support_dsn,
        source_queue_dsn,
        "secret-market-slug",
        "Will a hidden market resolve yes?",
        "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
    ):
        assert secret not in captured.out
        assert secret not in captured.err


@pytest.mark.parametrize(
    ("bad_limit", "expected_error"),
    (
        (0, f"{COMMAND} limit must be positive"),
        (-1, f"{COMMAND} limit must be positive"),
        (
            501,
            f"{COMMAND} limit must be less than or equal to "
            f"{MAX_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_READ_LIMIT}",
        ),
        (True, f"{COMMAND} limit must be positive"),
        ("1", f"{COMMAND} limit must be positive"),
        (1.0, f"{COMMAND} limit must be positive"),
    ),
)
def test_allocation_helper_rejects_invalid_limit_before_runner_or_connect(
    bad_limit: object,
    expected_error: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner_calls = 0
    connect_calls = 0

    def forbidden_runner(**_kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("allocation proposal runner should not run")

    def forbidden_connect(*_args: object, **_kwargs: object) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("DB connect should not run")

    monkeypatch.setitem(
        sys.modules,
        "psycopg",
        SimpleNamespace(connect=forbidden_connect),
    )
    helper = getattr(cli, "_run_paper_autonomous_allocation_proposal")

    with pytest.raises(ValueError, match=expected_error):
        helper(
            screening_gate_dsn="postgresql://screening.example.invalid/db",
            screening_gate_table_name="screening_reports",
            action_gated_queue_decision_support_dsn=(
                "postgresql://decision.example.invalid/db"
            ),
            action_gated_queue_decision_support_table_name="decision_reports",
            source_queue_dsn="postgresql://source.example.invalid/db",
            source_queue_table_name="source_reports",
            limit=bad_limit,
            runner=forbidden_runner,
        )

    assert runner_calls == 0
    assert connect_calls == 0


def test_allocation_helper_default_path_requires_all_dsns_to_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connect_calls = 0

    def forbidden_connect(*_args: object, **_kwargs: object) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("DB connect should not run")

    monkeypatch.setitem(
        sys.modules,
        "psycopg",
        SimpleNamespace(connect=forbidden_connect),
    )
    helper = getattr(cli, "_run_paper_autonomous_allocation_proposal")

    with pytest.raises(RuntimeError, match="requires all upstream DB DSNs to match"):
        helper(
            screening_gate_dsn="postgresql://screening.example.invalid/db",
            screening_gate_table_name="screening_reports",
            action_gated_queue_decision_support_dsn=(
                "postgresql://decision.example.invalid/db"
            ),
            action_gated_queue_decision_support_table_name="decision_reports",
            source_queue_dsn="postgresql://source.example.invalid/db",
            source_queue_table_name="source_reports",
            limit=7,
            runner=None,
        )

    assert connect_calls == 0


def test_allocation_helper_default_path_uses_one_autocommit_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shared_dsn = "postgresql://shared.example.invalid/db"
    connect_calls: list[tuple[str, bool]] = []
    loader_calls: list[dict[str, object]] = []
    report = _proposal_report()

    class FakeConnection:
        def __init__(self) -> None:
            self.close_count = 0
            self.commit_count = 0
            self.rollback_count = 0

        def commit(self) -> None:
            self.commit_count += 1
            raise AssertionError("read-only helper must not commit")

        def rollback(self) -> None:
            self.rollback_count += 1
            raise AssertionError("read-only helper must not rollback")

        def close(self) -> None:
            self.close_count += 1

    connection = FakeConnection()

    def fake_connect(dsn: str, *, autocommit: bool = False) -> FakeConnection:
        connect_calls.append((dsn, autocommit))
        return connection

    def fake_load(received_connection: object, **kwargs: object) -> object:
        loader_calls.append({"connection": received_connection, **kwargs})
        return report

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    monkeypatch.setattr(
        cli,
        "_load_paper_autonomous_allocation_proposal_report",
        fake_load,
        raising=False,
    )
    helper = getattr(cli, "_run_paper_autonomous_allocation_proposal")

    result = helper(
        screening_gate_dsn=shared_dsn,
        screening_gate_table_name="screening_reports",
        action_gated_queue_decision_support_dsn=shared_dsn,
        action_gated_queue_decision_support_table_name="decision_reports",
        source_queue_dsn=shared_dsn,
        source_queue_table_name="source_reports",
        limit=9,
        runner=None,
    )

    assert result is report
    assert connect_calls == [(shared_dsn, True)]
    assert len(loader_calls) == 1
    assert loader_calls[0]["connection"] is connection
    assert loader_calls[0]["screening_gate_limit"] == 9
    assert loader_calls[0]["screening_gate_table_name"] == "screening_reports"
    assert loader_calls[0]["action_gated_queue_decision_support_limit"] == 9
    assert (
        loader_calls[0]["action_gated_queue_decision_support_table_name"]
        == "decision_reports"
    )
    assert loader_calls[0]["source_queue_limit"] == 9
    assert loader_calls[0]["source_queue_table_name"] == "source_reports"
    assert isinstance(loader_calls[0]["generated_at"], datetime)
    assert connection.close_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0


def test_allocation_cli_runner_failure_redacts_dsns_tables_payloads_questions_hashes(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    screening_gate_dsn = "postgresql://screening-secret.example.invalid/db"
    screening_gate_table_name = "paper_autonomous_screening_decision_support_gate_reports"
    decision_support_dsn = "postgresql://decision-secret.example.invalid/db"
    decision_support_table_name = (
        "paper_action_gated_queue_decision_support_reports"
    )
    source_queue_dsn = "postgresql://source-secret.example.invalid/db"
    source_queue_table_name = (
        "paper_action_gated_strategy_recommendation_queue_reports"
    )
    payload_json = '{"secret":"allocation-proposal-payload-secret"}'
    question = "Will hidden allocation proposal market resolve yes?"
    report_sha256 = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
    bare_sha256 = "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"
    _set_upstream_db_env(
        monkeypatch,
        screening_gate_dsn=screening_gate_dsn,
        screening_gate_table_name=screening_gate_table_name,
        decision_support_dsn=decision_support_dsn,
        decision_support_table_name=decision_support_table_name,
        source_queue_dsn=source_queue_dsn,
        source_queue_table_name=source_queue_table_name,
    )

    def broken_runner(**_kwargs: Any) -> object:
        raise RuntimeError(
            f"screening_dsn={screening_gate_dsn} "
            f"screening_table={screening_gate_table_name} "
            f"decision_dsn={decision_support_dsn} "
            f"decision_table={decision_support_table_name} "
            f"source_dsn={source_queue_dsn} "
            f"source_table={source_queue_table_name} "
            f"payload_json={payload_json} question={question} "
            f"report_sha256={report_sha256} bare_hash={bare_sha256}",
        )

    exit_code = main(
        [COMMAND],
        paper_autonomous_allocation_proposal_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "screening_dsn=<redacted-dsn>" in captured.err
    assert "screening_table=<redacted-table>" in captured.err
    assert "decision_dsn=<redacted-dsn>" in captured.err
    assert "decision_table=<redacted-table>" in captured.err
    assert "source_dsn=<redacted-dsn>" in captured.err
    assert "source_table=<redacted-table>" in captured.err
    assert "payload_json=<redacted-payload>" in captured.err
    assert "question=<redacted-question>" in captured.err
    assert "report_sha256=<redacted-sha256>" in captured.err
    assert "bare_hash=<redacted-sha256>" in captured.err
    for secret in (
        screening_gate_dsn,
        screening_gate_table_name,
        decision_support_dsn,
        decision_support_table_name,
        source_queue_dsn,
        source_queue_table_name,
        payload_json,
        "allocation-proposal-payload-secret",
        question,
        report_sha256,
        bare_sha256,
    ):
        assert secret not in captured.out
        assert secret not in captured.err


def test_allocation_cli_runner_failure_redacts_multiline_payload_and_key_like_question(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload_secret = "allocation-multiline-payload-secret"
    payload_tail = "payload-tail-should-not-leak"
    question = "Will foo=bar leak?"
    _set_upstream_db_env(
        monkeypatch,
        screening_gate_dsn="postgresql://screening.example.invalid/db",
        decision_support_dsn="postgresql://decision.example.invalid/db",
        source_queue_dsn="postgresql://source.example.invalid/db",
    )

    def broken_runner(**_kwargs: Any) -> object:
        raise RuntimeError(
            "payload_json={\n"
            f'  "secret": "{payload_secret}",\n'
            f'  "tail": "{payload_tail}"\n'
            f"}} question={question} next_field=visible"
        )

    exit_code = main(
        [COMMAND],
        paper_autonomous_allocation_proposal_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "payload_json=<redacted-payload>" in captured.err
    assert "question=<redacted-question>" in captured.err
    assert "next_field=visible" in captured.err
    for secret in (
        payload_secret,
        payload_tail,
        question,
        "Will foo=bar",
        "bar leak?",
    ):
        assert secret not in captured.out
        assert secret not in captured.err


def test_allocation_cli_runner_failure_redacts_quoted_payload_and_question_fields(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    payload_secret = "allocation-quoted-payload-secret"
    question = "Will quoted allocation question leak?"
    report_sha256 = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
    _set_upstream_db_env(
        monkeypatch,
        screening_gate_dsn="postgresql://screening.example.invalid/db",
        decision_support_dsn="postgresql://decision.example.invalid/db",
        source_queue_dsn="postgresql://source.example.invalid/db",
    )

    def broken_runner(**_kwargs: Any) -> object:
        raise RuntimeError(
            f'"payload_json": {{"secret": "{payload_secret}"}} '
            f'"question": {question} report_sha256={report_sha256}'
        )

    exit_code = main(
        [COMMAND],
        paper_autonomous_allocation_proposal_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert '"payload_json": "<redacted-payload>"' in captured.err
    assert '"question": "<redacted-question>"' in captured.err
    assert "report_sha256=<redacted-sha256>" in captured.err
    for secret in (payload_secret, question, report_sha256):
        assert secret not in captured.out
        assert secret not in captured.err


@pytest.mark.parametrize(
    "argv",
    (
        [COMMAND, "--dsn", "postgresql://allocation.example.invalid/db"],
        [COMMAND, "--table", "paper_autonomous_allocation_proposal_reports"],
        [COMMAND, "--persist"],
        [COMMAND, "--fast"],
        [COMMAND, "--live"],
        [COMMAND, "--auth", "token"],
        [COMMAND, "--wallet", "wallet"],
        [COMMAND, "--private-key", "secret"],
        [COMMAND, "--api-key", "secret"],
        [COMMAND, "--account", "account"],
        [COMMAND, "--order", "order"],
        [COMMAND, "--trade"],
        [COMMAND, "--execute"],
        [COMMAND, "--submit"],
        [COMMAND, "--approve"],
    ),
)
def test_allocation_cli_rejects_dsn_table_persist_and_live_execution_flags(
    argv: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(argv)

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "unrecognized arguments" in captured.err
