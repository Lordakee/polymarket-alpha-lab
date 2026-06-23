from __future__ import annotations

import pytest

from polymarket_alpha_lab.cli import main


COMMAND = "paper-research-packet-quality"


@pytest.mark.parametrize(
    "flag",
    (
        "--dsn",
        "--db-dsn",
        "--table",
        "--paper-research-packet-db-dsn",
        "--paper-research-packet-db-table",
        "--paper-research-packet-db-enabled",
        "--limit",
        "--source-config-version",
        "--action-status",
        "--research-status",
        "--packet-config-version",
        "--max-packet-rows",
        "--min-score",
        "--persist",
        "--config-version",
        "--max-source-age-seconds",
        "--blocked-source-age-seconds",
        "--min-included-count",
        "--max-skipped-share",
        "--live",
        "--execute",
        "--trade",
        "--order",
        "--exchange",
        "--relayer",
        "--network",
        "--wallet",
        "--private-key",
        "--signing-key",
        "--api-key",
        "--auth",
    ),
)
def test_packet_quality_cli_rejects_source_db_generation_persistence_and_live_flags(
    flag: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([COMMAND, flag, "forbidden-value"])

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert f"unrecognized arguments: {flag}" in captured.err
