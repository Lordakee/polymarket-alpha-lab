from datetime import UTC, datetime

from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.strategy_cycle import PaperStrategyCycleReport


def test_scan_cli_builds_read_only_scan_config(tmp_path):
    calls = []

    def fake_client_factory():
        return "fake-client"

    def fake_runner(*, client, config):
        calls.append((client, config))
        return []

    output_path = tmp_path / "scores.json"
    archive_root = tmp_path / "raw"

    exit_code = main(
        [
            "scan",
            "--limit",
            "3",
            "--archive-root",
            str(archive_root),
            "--output",
            str(output_path),
            "--no-books",
        ],
        runner=fake_runner,
        client_factory=fake_client_factory,
    )

    assert exit_code == 0
    assert len(calls) == 1
    client, config = calls[0]
    assert client == "fake-client"
    assert config.limit == 3
    assert config.archive_root == archive_root
    assert config.output_path == output_path
    assert config.fetch_books is False


def test_scan_cli_returns_one_when_runner_fails(tmp_path):
    def broken_runner(*, client, config):
        raise RuntimeError("scan failed")

    exit_code = main(
        [
            "scan",
            "--archive-root",
            str(tmp_path / "raw"),
            "--output",
            str(tmp_path / "scores.json"),
        ],
        runner=broken_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 1


def test_strategy_cycle_cli_builds_read_only_cycle_config(tmp_path, capsys):
    calls = []

    def fake_client_factory():
        return "fake-client"

    def fake_cycle_runner(*, client, scan_config, cycle_config):
        calls.append((client, scan_config, cycle_config))
        # Naive forecast: every considered market is blocked (no snapshot_ready),
        # so screening_report must be None per the report invariants.
        return PaperStrategyCycleReport(
            generated_at=datetime.now(UTC),
            config_version="strategy-cycle-v1",
            scan_market_count=10,
            considered_count=5,
            snapshot_ready_count=0,
            cost_aware_report_count=0,
            blocked_counts=(("blocked_fetch_error", 5),),
            screening_report=None,
        )

    output_path = tmp_path / "strategy-cycle.jsonl"
    archive_root = tmp_path / "raw"

    exit_code = main(
        [
            "strategy-cycle",
            "--limit",
            "5",
            "--max-markets",
            "3",
            "--no-prefilter",
            "--archive-root",
            str(archive_root),
            "--output",
            str(output_path),
        ],
        cycle_runner=fake_cycle_runner,
        client_factory=fake_client_factory,
    )

    assert exit_code == 0
    assert len(calls) == 1
    client, scan_config, cycle_config = calls[0]
    assert client == "fake-client"
    assert scan_config.limit == 5
    assert scan_config.archive_root == archive_root
    assert scan_config.output_path == output_path
    assert scan_config.fetch_books is True
    assert cycle_config.max_markets_per_cycle == 3
    assert cycle_config.prefilter_by_score is False
    assert cycle_config.config_version == "strategy-cycle-v1"

    captured = capsys.readouterr()
    assert "scanned=10" in captured.out
    assert "considered=5" in captured.out
    assert "snapshot_ready=0" in captured.out
    assert "blocked_fetch_error=5" in captured.out

    # The JSONL report log is appended and must be valid.
    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8").strip().endswith("}")


def test_strategy_cycle_cli_returns_one_when_cycle_runner_fails(tmp_path):
    def broken_cycle_runner(*, client, scan_config, cycle_config):
        raise RuntimeError("cycle failed")

    exit_code = main(
        [
            "strategy-cycle",
            "--archive-root",
            str(tmp_path / "raw"),
            "--output",
            str(tmp_path / "strategy-cycle.jsonl"),
        ],
        cycle_runner=broken_cycle_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 1


def test_strategy_cycle_cli_paper_execute_flag_enables_inline_paper_pass(tmp_path):
    calls = []

    def fake_client_factory():
        return "fake-client"

    def fake_cycle_runner(*, client, scan_config, cycle_config):
        calls.append(cycle_config)
        return PaperStrategyCycleReport(
            generated_at=datetime.now(UTC),
            config_version="strategy-cycle-v1",
            scan_market_count=0,
            considered_count=0,
            snapshot_ready_count=0,
            cost_aware_report_count=0,
            blocked_counts=(),
            screening_report=None,
        )

    journal_path = tmp_path / "paper-trades.jsonl"

    exit_code = main(
        [
            "strategy-cycle",
            "--paper-execute",
            "--paper-journal",
            str(journal_path),
            "--archive-root",
            str(tmp_path / "raw"),
            "--output",
            str(tmp_path / "strategy-cycle.jsonl"),
        ],
        cycle_runner=fake_cycle_runner,
        client_factory=fake_client_factory,
    )

    assert exit_code == 0
    assert len(calls) == 1
    cycle_config = calls[0]
    assert cycle_config.paper_execution_config is not None
    assert cycle_config.paper_execution_config.config_version == "paper-execution-v1"
    assert cycle_config.paper_trade_journal_path == journal_path


def test_strategy_cycle_cli_default_omits_paper_execute(tmp_path):
    calls = []

    def fake_cycle_runner(*, client, scan_config, cycle_config):
        calls.append(cycle_config)
        return PaperStrategyCycleReport(
            generated_at=datetime.now(UTC),
            config_version="strategy-cycle-v1",
            scan_market_count=0,
            considered_count=0,
            snapshot_ready_count=0,
            cost_aware_report_count=0,
            blocked_counts=(),
            screening_report=None,
        )

    exit_code = main(
        [
            "strategy-cycle",
            "--archive-root",
            str(tmp_path / "raw"),
            "--output",
            str(tmp_path / "strategy-cycle.jsonl"),
        ],
        cycle_runner=fake_cycle_runner,
        client_factory=lambda: "fake-client",
    )

    assert exit_code == 0
    cycle_config = calls[0]
    assert cycle_config.paper_execution_config is None
    assert cycle_config.paper_trade_journal_path is None
