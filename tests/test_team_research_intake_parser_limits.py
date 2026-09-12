"""Unrepresentable JSON exponents must block before model construction."""
from datetime import UTC, datetime
import json

import pytest

from polymarket_alpha_lab.team_research_agent_types import ResearchEvidence
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot
from polymarket_alpha_lab.team_research_market_pipeline import run_team_research_from_market_snapshot


@pytest.mark.parametrize("literal", ("1e999999999999999999999999", "1e-999999999999999999999999", "-1e999999999999999999999999"))
@pytest.mark.parametrize("location", ("outer", "outcomes"))
def test_unrepresentable_decimal_in_provider_json_is_blocked(location, literal):
    now = datetime(2026, 9, 12, tzinfo=UTC)
    if location == "outer":
        raw = ('{"value":' + literal + '}').encode()
        expected = "invalid_market_payload"
    else:
        raw = json.dumps(dict(
            slug="fixture-market", conditionId="c", question="Synthetic?",
            description="Synthetic resolution rules.", active=True, closed=False,
            outcomes='["Yes",' + literal + ']', endDate="2026-09-13T00:00:00Z",
        )).encode()
        expected = "unsupported_market_outcomes"
    snapshot = GammaMarketSnapshot("fixture-market", now, raw)
    source = ResearchEvidence("s", "crypto_eth", "c", "Synthetic title", "Synthetic observation",
                              "synthetic:source", now)
    calls = []
    run = run_team_research_from_market_snapshot(
        snapshot, task_id="t", team_id="crypto_eth", condition_id="c", as_of=now,
        evidence=(source,), model_factory=lambda team: calls.append(team),
    )
    assert run.intake.reason_code == expected
    assert run.intake.status == "blocked"
    assert run.intake.task is None and run.research is None
    assert calls == []
