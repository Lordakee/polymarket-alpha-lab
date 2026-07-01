from __future__ import annotations

from pathlib import Path

import polymarket_alpha_lab


MODULE_PATH = Path("src/polymarket_alpha_lab/team_evidence_quality.py")


def test_team_evidence_quality_module_stays_pure_and_readonly() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8").lower()

    for banned in (
        "psycopg",
        "supabase",
        "os.environ",
        "cli",
        "network",
        "open",
        "print",
        "auth",
        "wallet",
        "account",
        "order",
        "trade",
        "execute",
        "submit",
        "cancel",
        "replace",
    ):
        assert banned not in source


def test_team_evidence_quality_is_not_exported_from_package_root() -> None:
    assert not hasattr(polymarket_alpha_lab, "TeamEvidenceQualityConfig")
    assert not hasattr(polymarket_alpha_lab, "TeamEvidenceQualityRow")
    assert not hasattr(polymarket_alpha_lab, "TeamEvidenceQualityReport")
    assert not hasattr(polymarket_alpha_lab, "build_team_evidence_quality_report")
