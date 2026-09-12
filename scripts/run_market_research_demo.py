"""Synthetic Gamma snapshot -> evidence intake -> model/tool-loop demonstration."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal

from polymarket_alpha_lab.team_research_agent_types import (
    ResearchEvidence, ResearchModelReply, ResearchToolCall,
)
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot
from polymarket_alpha_lab.team_research_market_pipeline import run_team_research_from_market_snapshot


class _SyntheticModel:
    """Protocol fixture only, not a live language model."""
    def __init__(self) -> None:
        self.calls = 0

    def complete(self, *, messages_json: str, max_output_tokens: int) -> ResearchModelReply:
        self.calls += 1
        if self.calls == 1:
            name, args = "search_evidence", {"query": "*"}
        elif self.calls == 2:
            name, args = "read_evidence", {"source_id": "demo-source"}
        else:
            name, args = "finish_research", {
                "probability_yes": "0.5", "confidence": "0.1",
                "summary": "Synthetic demonstration, not a forecast.", "source_ids": ["demo-source"],
            }
        return ResearchModelReply((ResearchToolCall(f"demo-{self.calls}", name, json.dumps(args)),), 1)


def main() -> int:
    now = datetime(2026, 9, 12, tzinfo=UTC)
    snapshot = GammaMarketSnapshot("demo-market", now, json.dumps({
        "slug": "demo-market", "conditionId": "demo-condition", "question": "Synthetic event?",
        "description": "Resolve YES under this synthetic criterion.", "outcomes": '["Yes","No"]',
        "active": True, "closed": False, "endDate": "2026-09-13T00:00:00Z",
    }).encode("utf-8"))
    evidence = ResearchEvidence("demo-source", "crypto_eth", "demo-condition", "Synthetic source",
                                "Artificial observation only.", "synthetic:demo", now)
    run = run_team_research_from_market_snapshot(
        snapshot, task_id="demo", team_id="crypto_eth", condition_id="demo-condition", as_of=now,
        evidence=(evidence,), model_factory=lambda _: _SyntheticModel(),
    )
    print(json.dumps({
        "synthetic_demo": True, "public_network_called": False, "live_model_called": False,
        "intake_status": run.intake.status, "market_content_sha256": run.intake.market_content_sha256,
        "evidence_content_sha256": run.intake.source_receipts[0].content_sha256,
        "research_status": run.research.status, "probability_yes": str(run.research.probability_yes),
        "tool_trace": run.research.tool_trace, "paper_only": True, "report_only": True, "readonly": True,
    }, indent=2))
    return 0 if run.research.probability_yes == Decimal("0.5") else 1


if __name__ == "__main__":
    raise SystemExit(main())
