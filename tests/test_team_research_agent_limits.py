"""Prevent unnecessary model calls after the tool allowance is consumed."""
from datetime import UTC, datetime

import pytest

from polymarket_alpha_lab.team_research_agent import run_team_research_agent
from polymarket_alpha_lab.team_research_agent_types import (
    ResearchAgentLimits, ResearchEvidence, ResearchModelReply, ResearchToolCall,
    TeamResearchTask,
)


@pytest.mark.parametrize("allowance", (1, 2, 3))
def test_exhausted_tool_budget_prevents_another_paid_model_call(allowance):
    now = datetime(2026, 9, 12, tzinfo=UTC)
    source = ResearchEvidence("s", "crypto_eth", "c", "Synthetic", "Synthetic text", "synthetic:source", now)
    task = TeamResearchTask("t", "crypto_eth", "c", "slug", "Synthetic?", "Synthetic criteria", now, (source,))

    class Model:
        calls = 0

        def complete(self, **kwargs):
            self.calls += 1
            return ResearchModelReply((ResearchToolCall(f"call-{self.calls}", "search_evidence", '{"query":"*"}'),), 1)

    model = Model()
    result = run_team_research_agent(task, model=model, limits=ResearchAgentLimits(max_tool_calls=allowance))
    assert result.reason_code == "tool_call_limit"
    assert result.model_calls == model.calls == allowance
    assert result.tool_calls == allowance
    assert result.total_tokens == allowance
    assert result.probability_yes is result.confidence is None
