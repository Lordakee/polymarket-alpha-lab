"""Synthetic research -> recorded predictions -> binary outcome evaluation.

No live model, public network, database, credentials or file writes. The ten
outcomes are deliberately constructed (seven YES), not measured performance.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from hashlib import sha256
import json

from polymarket_alpha_lab.team_research_agent_types import ResearchEvidence, ResearchModelReply, ResearchToolCall
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot
from polymarket_alpha_lab.team_research_market_pipeline import run_team_research_from_market_snapshot
from polymarket_alpha_lab.team_research_evaluation import (
    ResearchEvaluationRecord, ResearchEvaluationOutcome, ResearchEvaluationReport,
)


class _SyntheticModel:
    def __init__(self) -> None:
        self.calls = 0

    def complete(self, *, messages_json: str, max_output_tokens: int) -> ResearchModelReply:
        self.calls += 1
        if self.calls == 1:
            name, args = "read_evidence", {"source_id": "demo-source"}
        else:
            name, args = "finish_research", dict(probability_yes="0.7", confidence="0.2",
                summary="Synthetic forecast fixture, not real performance.", source_ids=["demo-source"])
        return ResearchModelReply((ResearchToolCall(f"call-{self.calls}", name, json.dumps(args)),), 1)


def main() -> int:
    now = datetime(2026, 9, 12, tzinfo=UTC)
    records, outcomes = [], []
    for index in range(10):
        condition, slug = f"demo-condition-{index}", f"demo-market-{index}"
        market = GammaMarketSnapshot(slug, now, json.dumps(dict(
            slug=slug, conditionId=condition, question="Synthetic event?",
            description="Resolve YES for the synthetic event only.", outcomes=["Yes", "No"],
            active=True, closed=False, endDate=(now + timedelta(hours=1)).isoformat(),
        )).encode())
        source = ResearchEvidence("demo-source", "crypto_eth", condition, "Synthetic observation",
            "Artificial fixture evidence only.", "synthetic:demo", now)
        run = run_team_research_from_market_snapshot(market, task_id=f"demo-task-{index}",
            team_id="crypto_eth", condition_id=condition, as_of=now, evidence=(source,),
            model_factory=lambda _: _SyntheticModel())
        records.append(ResearchEvaluationRecord(f"demo-{index}", "scripted-demo", "synthetic-v1",
            now + timedelta(seconds=1), run))
        actual = index < 7
        outcomes.append(ResearchEvaluationOutcome(condition, slug, now + timedelta(hours=1),
            now + timedelta(hours=2), now + timedelta(hours=3), actual, "synthetic:resolution",
            sha256(json.dumps({"condition_id": condition, "actual_yes": actual}).encode()).hexdigest()))
    report = ResearchEvaluationReport(tuple(records), tuple(outcomes), now + timedelta(hours=4))
    print(json.dumps({"synthetic_demo": True, "public_network_called": False,
        "live_model_called": False, "evaluation": report.to_dict()}, ensure_ascii=False, allow_nan=False, indent=2))
    return 0 if report.groups[0].scores.sample_count == 10 else 1


if __name__ == "__main__":
    raise SystemExit(main())
