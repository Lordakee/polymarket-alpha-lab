from __future__ import annotations

import importlib
import re
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = REPO_ROOT / "src" / "polymarket_alpha_lab"
PACKAGE_NAME = "polymarket_alpha_lab"

DANGEROUS_EXECUTION_TOKENS = frozenset(
    (
        "wallet",
        "private_key",
        "sign",
        "order_submit",
        "cancel",
        "replace",
        "live_execution",
    ),
)
IDENTIFIER_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _phase1_report_readiness_paths() -> tuple[Path, ...]:
    return tuple(
        sorted(
            path
            for path in PACKAGE_DIR.glob("*.py")
            if ("phase1" in path.stem or "phase_1" in path.stem)
            and ("report" in path.stem or "readiness" in path.stem)
        ),
    )


def _dangerous_token_hits(path: Path) -> tuple[str, ...]:
    hits: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        for match in IDENTIFIER_TOKEN.finditer(line):
            token = match.group(0).lower()
            if token in DANGEROUS_EXECUTION_TOKENS:
                hits.append(f"{path.relative_to(REPO_ROOT)}:{line_number}:{token}")
    return tuple(hits)


def _boundary_report_payload() -> dict[str, object]:
    module = importlib.import_module(
        f"{PACKAGE_NAME}.probability_event_screen_phase1_boundary_report",
    )
    report = module.build_probability_event_screen_phase1_boundary_report(
        module.ProbabilityEventScreenPhase1BoundaryInput(
            paper_only_enforced=True,
            report_only_enforced=True,
            readonly_enforced=True,
            no_wallet_or_auth_path=True,
            no_live_order_path=True,
            manual_only_execution_ready=True,
            public_payload_safety_ready=True,
            supabase_persistence_ready=True,
        ),
    )
    return module.probability_event_screen_phase1_boundary_report_to_payload(report)


def _strategy_phase1_readiness_payload() -> dict[str, object]:
    module = importlib.import_module(f"{PACKAGE_NAME}.strategy_phase1_readiness_aggregator")
    report = module.build_strategy_phase1_readiness_report(
        (
            module.StrategyPhase1ReadinessSignal(
                signal_id="phase1-readonly-boundary-scan",
                event_ref="public-event-alpha",
                market_ref="public-market-alpha",
                observed_at=datetime(2026, 7, 8, 11, 58, tzinfo=UTC),
                edge_score=Decimal("0.080000"),
                cost_score=Decimal("0.020000"),
                liquidity_score=Decimal("0.900000"),
                resolution_score=Decimal("0.850000"),
                freshness_score=Decimal("0.950000"),
                manual_blocker_count=Decimal("0"),
                source_status="pass",
                source_reason_codes=("phase1_readiness_public_boundary_scan",),
            ),
        ),
        generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=UTC),
    )
    return module.strategy_phase1_readiness_report_payload(report)


def _assert_readonly_payload_boundary(payload: dict[str, object]) -> None:
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    rows = payload.get("rows")
    if rows is not None:
        assert isinstance(rows, list)
        for row in rows:
            assert isinstance(row, dict)
            assert row["paper_only"] is True
            assert row["report_only"] is True
            assert row["readonly"] is True


def test_phase1_report_readiness_modules_have_readonly_boundary_only() -> None:
    module_paths = _phase1_report_readiness_paths()
    assert module_paths

    token_hits = tuple(hit for path in module_paths for hit in _dangerous_token_hits(path))
    assert token_hits == ()

    for payload in (_boundary_report_payload(), _strategy_phase1_readiness_payload()):
        _assert_readonly_payload_boundary(payload)
