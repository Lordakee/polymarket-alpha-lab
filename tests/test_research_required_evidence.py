"""Required evidence must be readable before any model call or paid permit."""
from dataclasses import replace
from datetime import timedelta

import pytest

from polymarket_alpha_lab import team_research_agent as agent
from polymarket_alpha_lab import research_model_budget_runner as runner
from polymarket_alpha_lab.team_research_agent_types import ResearchAgentLimits
from polymarket_alpha_lab.team_research_intake import _receipt
from tests.test_team_research_agent import NOW, ScriptedModel, task
from tests.test_research_model_budget import req, policy, message_execution


@pytest.mark.parametrize('team', ['crypto_btc', 'crypto_eth'])
@pytest.mark.parametrize('delta', [timedelta(days=-2), timedelta(seconds=1),
                                  -timedelta(days=1, microseconds=1)])
def test_unreadable_required_evidence_blocks_before_model(team, delta):
    original = task(team)
    required = replace(original.evidence[0], source_id='required-source',
                       observed_at=NOW + delta)
    item = replace(original, evidence=(*original.evidence, required))
    model = ScriptedModel()
    result = agent.run_team_research_agent(item, model=model,
                                          required_source_ids=('required-source',))
    assert result.status == 'blocked'
    assert result.reason_code == 'invalid_citations'
    assert result.model_calls == result.tool_calls == result.total_tokens == 0
    assert model.messages == []
    assert result.probability_yes is result.confidence is None
    assert result.summary == '' and result.source_ids == ()
    assert item.evidence == (*original.evidence, required)


@pytest.mark.parametrize('delta', [timedelta(0), -timedelta(days=1)])
def test_required_source_at_inclusive_freshness_boundary_still_runs(delta):
    item = task()
    item = replace(item, evidence=(replace(item.evidence[0], observed_at=NOW + delta),))
    model = ScriptedModel()
    result = agent.run_team_research_agent(item, model=model,
                                          required_source_ids=('source-1',))
    assert result.status == 'completed'
    assert result.model_calls == 3
    assert result.source_ids == ('source-1',)


def test_optional_stale_source_does_not_block_valid_research():
    item = task()
    item = replace(item, evidence=(*item.evidence, replace(item.evidence[0],
        source_id='optional-old', observed_at=NOW-timedelta(days=2))))
    result = agent.run_team_research_agent(item, model=ScriptedModel(),
                                          required_source_ids=('source-1',))
    assert result.status == 'completed'
    assert result.model_calls == 3


def test_empty_eligible_catalog_keeps_original_reason():
    item = task()
    model = ScriptedModel()
    result = agent.run_team_research_agent(item, model=model,
        limits=ResearchAgentLimits(max_evidence_age_seconds=0),
        required_source_ids=('source-1',))
    assert result.reason_code == 'no_eligible_evidence'
    assert result.model_calls == 0 and model.messages == []


def mixed_request(number):
    r = req(number)
    old = replace(r.intake.task.evidence[0], observed_at=r.intake.as_of-timedelta(seconds=1))
    fresh = replace(old, source_id='optional-fresh', observed_at=r.intake.as_of)
    evidence = (old, fresh)
    intake = replace(r.intake, task=replace(r.intake.task, evidence=evidence),
                     source_receipts=tuple(_receipt(e) for e in evidence))
    return replace(r, intake=intake, required_source_ids=(old.source_id,),
                   limits=replace(r.limits, max_evidence_age_seconds=0))


@pytest.mark.parametrize('number', [0, 1])
@pytest.mark.parametrize('max_message_bytes', [1, 100000])
def test_budgeted_capture_records_block_without_factory_or_reservation(monkeypatch, number, max_message_bytes):
    r = mixed_request(number)
    p = policy((r,), max_message_bytes=max_message_bytes)
    original = r.payload, p.payload
    events, factory = message_execution(monkeypatch, p)
    out = runner.run_budgeted_research_with_psycopg('fake', request=r,
        budget_id=p.budget_id, model_factory=factory, allow_model_calls=True)
    assert events == ['claim', 'capture']
    assert out.status == 'captured'
    result = out.record.run.research
    assert result.reason_code == 'invalid_citations'
    assert result.model_calls == result.tool_calls == result.total_tokens == 0
    assert result.probability_yes is None
    assert (r.payload, p.payload) == original
    assert out.request.content_sha256 == r.content_sha256


@pytest.mark.parametrize('number', [0, 1])
def test_original_blocked_receipt_replays_without_paid_call(monkeypatch, number):
    r = mixed_request(number)
    p = policy((r,), max_message_bytes=1)
    events, factory = message_execution(monkeypatch, p)
    original = runner.run_budgeted_research_with_psycopg('fake', request=r,
        budget_id=p.budget_id, model_factory=factory, allow_model_calls=True)
    assert events == ['claim', 'capture']
    events.clear()
    def replay(dsn, request):
        events.append('replay')
        return False, original
    monkeypatch.setattr(runner.execution, '_claim', replay)
    out = runner.run_budgeted_research_with_psycopg('fake', request=r,
        budget_id=p.budget_id, model_factory=factory, allow_model_calls=True)
    assert out is original
    assert events == ['replay']


@pytest.mark.parametrize('count', [21, 100])
def test_required_sources_cannot_exceed_finish_schema_before_model(count):
    original = task()
    evidence = tuple(replace(original.evidence[0], source_id=f'required-{i}')
                     for i in range(count))
    item = replace(original, evidence=evidence)
    model = ScriptedModel()
    with pytest.raises(ValueError, match='required_source_ids'):
        agent.run_team_research_agent(item, model=model,
            required_source_ids=tuple(e.source_id for e in evidence))
    assert model.messages == []
