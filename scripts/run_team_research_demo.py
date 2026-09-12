"""Offline synthetic model/tool-loop demo; no live model, DB, network or writes."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import UTC, datetime
import json

from polymarket_alpha_lab.team_research_agent import run_team_research_batch
from polymarket_alpha_lab.team_research_agent_types import (
    ResearchEvidence, ResearchModelReply, ResearchToolCall, TeamResearchTask,
)
from polymarket_alpha_lab.team_taxonomy import TEAM_IDS


class ScriptedDemoModel:
    """A deterministic protocol test double, NOT an LLM."""
    def __init__(self) -> None:
        self.step = 0

    def complete(self, *, messages_json: str, max_output_tokens: int) -> ResearchModelReply:
        self.step += 1
        if self.step == 1:
            name, args = "search_evidence", {"query": "*"}
        elif self.step == 2:
            observation = json.loads(json.loads(messages_json)[-1]["content"])
            name, args = "read_evidence", {"source_id": observation["sources"][0]["source_id"]}
        else:
            observation = json.loads(json.loads(messages_json)[-1]["content"])
            name, args = "finish_research", {
                "probability_yes": "0.5", "confidence": "0.1",
                "summary": "Synthetic demo only; not a market estimate.",
                "source_ids": [observation["source_id"]],
            }
        return ResearchModelReply((ResearchToolCall(f"demo-{self.step}", name, json.dumps(args)),), 1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--team", action="append", choices=TEAM_IDS)
    parser.add_argument("--max-workers", type=int, default=4)
    args = parser.parse_args(argv)
    if not 1 <= args.max_workers <= 32:
        parser.error("--max-workers must be between 1 and 32")
    teams = tuple(dict.fromkeys(args.team or TEAM_IDS))
    now = datetime(2026, 9, 12, tzinfo=UTC)
    tasks = tuple(TeamResearchTask(
        task_id=f"demo-{team}", team_id=team, condition_id=f"demo-{team}",
        market_slug=f"demo-{team}", question="Synthetic YES/NO event?",
        resolution_criteria="Synthetic criterion, not real market rules.", as_of=now,
        evidence=(ResearchEvidence("demo-source", team, f"demo-{team}", "Synthetic source",
                                    "This is artificial fixture evidence.", "synthetic:demo", now),),
    ) for team in teams)
    results = run_team_research_batch(tasks, model_factory=lambda _: ScriptedDemoModel(), max_workers=args.max_workers)
    print(json.dumps({"synthetic_demo": True, "live_model_called": False,
                      "results": [asdict(result) for result in results]}, default=str, indent=2))
    return 0 if all(result.status == "completed" for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
