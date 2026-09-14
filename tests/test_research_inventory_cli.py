"""Read-only inventory command; no real database, network, worker or model."""
from contextlib import contextmanager
from pathlib import Path
import json
import subprocess
import sys

import pytest

from polymarket_alpha_lab import research_inventory_cli as cli
from polymarket_alpha_lab.research_execution_inventory import ResearchExecutionInventory
from tests.test_research_execution_inventory import AT, saved

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def managed(monkeypatch, capsys):
    values = dict(inventory=ResearchExecutionInventory(AT, (saved(), saved("incomplete", "r2"))), error=None, close_error=None)
    events = []
    class Session:
        def execution_inventory(self, **kw):
            events.append(("read", kw))
            if values["error"] is not None: raise values["error"]
            return values["inventory"]
        def run_research(self, **kw): pytest.fail("read must not launch")
        def retry_capture(self, **kw): pytest.fail("read must not retry")
        def evaluate(self, **kw): pytest.fail("inventory must not score")
    class Database:
        def __init__(self, root): events.append(("root", root))
        @contextmanager
        def session(self):
            events.append(("enter",))
            try: yield Session()
            finally:
                assert capsys.readouterr() == ("", "")
                events.append(("exit",))
                if values["close_error"] is not None: raise values["close_error"]
    monkeypatch.setattr(cli, "ProjectPostgres", Database)
    return values, events


def invoke(args=()):
    return cli.main(list(args), default_root=Path("/unused/project"))


def test_actual_inventory_invocation_and_suppressed_sensitive_fields(managed, capsys):
    assert invoke(("--root", "/unused/explicit", "--max-records", "10")) == 0
    assert managed[1] == [("root", Path("/unused/explicit")), ("enter",), ("read", {"max_records":10}), ("exit",)]
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "listed" and out["inventory"]["incomplete_claim_count"] == 1
    assert out["public_network_called"] is out["live_model_called"] is out["business_writes_performed"] is False


def test_empty_inventory_is_a_success_not_an_empty_database_claim(managed, capsys):
    managed[0]["inventory"] = ResearchExecutionInventory(AT, (), 3)
    assert invoke() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["inventory"]["inventory_status"] == "no_claims" and out["inventory"]["unclaimed_attempt_count"] == 3


@pytest.mark.parametrize("reason", ("research_execution_inventory_limit", "research_execution_inventory_future_record"))
def test_known_blocks_have_no_partial_inventory(managed, capsys, reason):
    managed[0]["error"] = cli.ResearchCaptureConflict(reason)
    assert invoke() == 1
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "blocked" and out["reason_code"] == reason and out["inventory"] is None


@pytest.mark.parametrize("defect", ("read", "close", "empty_close", "wrong_type", "invalid_flags", "unknown_conflict"))
def test_bad_or_unfinished_read_is_redacted_without_retry(managed, capsys, defect):
    values, events = managed
    if defect == "read": values["error"] = RuntimeError("PRIVATE-PATH-DSN")
    elif defect in ("close", "empty_close"):
        values["close_error"] = RuntimeError("PRIVATE-PATH-DSN")
        if defect == "empty_close": values["inventory"] = ResearchExecutionInventory(AT, ())
    elif defect == "wrong_type": values["inventory"] = {"secret":"PRIVATE-PATH-DSN"}
    elif defect == "invalid_flags": object.__setattr__(values["inventory"].executions[0], "readonly", False)
    else: values["error"] = cli.ResearchCaptureConflict("research_execution_inventory_limit PRIVATE-PATH-DSN")
    assert invoke() == 1
    text = capsys.readouterr().out
    assert "PRIVATE" not in text
    out = json.loads(text)
    assert out["status"] == "failed" and out["inventory"] is None
    assert out["reason_code"] == "research_execution_inventory_failed"
    assert sum(e[0] == "read" for e in events) == 1


@pytest.mark.parametrize("args", (("--max-records","0"), ("--max-records","1001"), ("--max-records","x"),
    ("--max-r","1"), ("--incomplete-only",), ("--retry",), ("--dsn","x"), ("--as-of","2026-09-14"),
    ("--record-id","r1"), ("--allow-public-fetch",)))
def test_invalid_or_misleading_options_do_not_open_manager(managed, args):
    with pytest.raises(SystemExit) as caught: invoke(args)
    assert caught.value.code == 2 and managed[1] == []


@pytest.mark.parametrize("phase", ("error", "close_error"))
def test_interrupts_remain_interrupts(managed, capsys, phase):
    managed[0][phase] = KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt): invoke()
    assert capsys.readouterr() == ("", "")


def test_actual_installed_script_help_is_offline():
    result = subprocess.run([sys.executable, "-I", str(ROOT / "scripts/list_project_research.py"), "--help"],
        capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "--max-records" in result.stdout and "--dsn" not in result.stdout
