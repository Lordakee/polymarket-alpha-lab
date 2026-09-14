"""Absolute-instant freshness at both intake and the direct agent boundary.

Synthetic timestamps/payloads/models only. IANA data comes from the declared
runtime dependency, not host TZPATH. Original source timestamps are not rewritten.
"""
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from importlib import resources
import json
from zoneinfo import ZoneInfo

import pytest

from polymarket_alpha_lab.team_research_agent import run_team_research_agent
from polymarket_alpha_lab.team_research_agent_types import (
    ResearchAgentLimits, ResearchEvidence, ResearchModelReply, ResearchToolCall,
    TeamResearchTask,
)
from polymarket_alpha_lab.team_research_intake import (
    GammaMarketSnapshot, evidence_content_sha256, prepare_team_research_from_gamma,
)
from polymarket_alpha_lab.team_research_market_pipeline import run_team_research_from_market_snapshot

# UTC instants are the oracle; local wall times deliberately disagree around DST.
CASES = (
    ('America/New_York', '2026-11-01T05:45:00+00:00', 3540),
    ('America/New_York', '2026-11-01T05:30:00+00:00', 3600),
    ('America/New_York', '2026-11-01T06:30:00+00:00', -3600),
    ('America/New_York', '2026-11-01T06:44:00+00:00', -3540),
    ('America/New_York', '2026-11-01T06:01:00+00:00', -120),
    ('America/New_York', '2026-11-01T06:01:00+00:00', -300),
    ('America/New_York', '2026-11-01T06:01:00+00:00', -300.000001),
    ('America/New_York', '2026-03-08T07:01:00+00:00', -120),
    ('America/New_York', '2026-03-08T07:01:00+00:00', -300),
    ('America/New_York', '2026-03-08T07:01:00+00:00', -300.000001),
    ('Australia/Lord_Howe', '2026-04-04T14:45:00+00:00', 1800),
    ('Australia/Lord_Howe', '2026-04-04T15:15:00+00:00', -1800),
    ('Australia/Lord_Howe', '2026-04-04T15:01:00+00:00', -120),
    ('Australia/Lord_Howe', '2026-10-03T15:31:00+00:00', -120),
    ('Asia/Taipei', '2026-09-14T00:00:00+00:00', 0),
    ('Asia/Taipei', '2026-09-14T00:00:00+00:00', 0.000001),
)
LIMITS = ResearchAgentLimits(max_evidence_age_seconds=300)


def zone(key):
    with resources.files('tzdata.zoneinfo').joinpath(*key.split('/')).open('rb') as stream:
        return ZoneInfo.from_file(stream, key=key)


def moments(case):
    key, value, delta = case
    current = datetime.fromisoformat(value)
    sampled = current + timedelta(seconds=delta)
    z = zone(key)
    return current.astimezone(z), sampled.astimezone(z), delta


def evidence(when, source_id='source-1'):
    return ResearchEvidence(source_id, 'crypto_eth', 'timezone-fixture', 'Synthetic source',
        'Synthetic observation, not a real event.', 'synthetic:timezone', when)


def snapshot(fetched, at):
    payload = dict(conditionId='timezone-fixture', slug='timezone-fixture',
        question='Synthetic event?', description='Synthetic rule only.', active=True,
        closed=False, outcomes=['Yes', 'No'], updatedAt=None,
        endDate=(at.astimezone(UTC) + timedelta(days=1)).isoformat())
    return GammaMarketSnapshot('timezone-fixture', fetched, json.dumps(payload).encode())


def args(at, items):
    return dict(task_id='timezone-fixture', team_id='crypto_eth', condition_id='timezone-fixture',
                as_of=at, evidence=items, limits=LIMITS)


def task(at, items):
    return TeamResearchTask('timezone-fixture', 'crypto_eth', 'timezone-fixture',
        'timezone-fixture', 'Synthetic event?', 'Synthetic rule only.', at, items)


class Model:
    def __init__(self):
        self.messages = []

    def complete(self, *, messages_json, max_output_tokens):
        self.messages.append(json.loads(messages_json))
        step = len(self.messages)
        if step == 1:
            name, data = 'search_evidence', {'query': '*'}
        elif step == 2:
            name, data = 'read_evidence', {'source_id': 'source-1'}
        else:
            name, data = 'finish_research', dict(probability_yes='0.6', confidence='0.5',
                summary='Synthetic observation.', source_ids=['source-1'])
        return ResearchModelReply((ResearchToolCall(f'call-{step}', name, json.dumps(data)),), 5)


@pytest.mark.parametrize('case', CASES)
def test_market_context_uses_elapsed_instants(case):
    at, fetched, delta = moments(case)
    snap = snapshot(fetched, at)
    row = prepare_team_research_from_gamma(snap, **args(at, (evidence(at),)))
    expected = ('market_context_from_future' if delta > 0 else
                'market_context_stale' if delta < -300 else 'research_intake_prepared')
    assert row.reason_code == expected
    assert row.fetched_at.isoformat() == fetched.isoformat()
    assert row.fetched_at.fold == fetched.fold
    assert snap.raw_json == snapshot(fetched, at).raw_json


@pytest.mark.parametrize('case', CASES)
def test_intake_evidence_filter_uses_elapsed_instants(case):
    at, observed, delta = moments(case)
    row = prepare_team_research_from_gamma(snapshot(at, at), **args(at, (evidence(observed),)))
    eligible = -300 <= delta <= 0
    assert row.status == ('prepared' if eligible else 'blocked')
    assert row.future_source_ids == (('source-1',) if delta > 0 else ())
    assert row.stale_source_ids == (('source-1',) if delta < -300 else ())
    assert len(row.source_receipts) == int(eligible)


@pytest.mark.parametrize('case', CASES)
def test_direct_agent_does_not_reintroduce_ineligible_evidence(case):
    at, observed, delta = moments(case)
    model = Model()
    row = run_team_research_agent(task(at, (evidence(observed),)), model=model, limits=LIMITS)
    eligible = -300 <= delta <= 0
    assert row.reason_code == ('research_completed' if eligible else 'no_eligible_evidence')
    assert row.model_calls == (3 if eligible else 0)
    assert len(model.messages) == row.model_calls
    assert row.as_of.isoformat() == at.isoformat()  # Preserve the public result format.


@pytest.mark.parametrize('kind', ('context', 'evidence'))
def test_future_fold_is_blocked_before_model_factory(kind):
    at, later, _ = moments(CASES[0])
    called = []
    result = run_team_research_from_market_snapshot(
        snapshot(later if kind == 'context' else at, at),
        **args(at, (evidence(later if kind == 'evidence' else at),)),
        model_factory=lambda team: called.append(team) or Model())
    assert result.intake.status == 'blocked' and result.research is None and called == []


@pytest.mark.parametrize('case', (CASES[4], CASES[7], CASES[12], CASES[13]))
def test_valid_cross_transition_pipeline_keeps_original_receipts(case):
    at, observed, _ = moments(case)
    ev = evidence(observed)
    model = Model()
    snap = snapshot(at, at)
    result = run_team_research_from_market_snapshot(snap, **args(at, (ev,)), model_factory=lambda _: model)
    assert result.research.status == 'completed'
    receipt = result.intake.source_receipts[0]
    assert receipt.content_sha256 == evidence_content_sha256(ev)
    assert receipt.observed_at.isoformat() == observed.isoformat()
    assert receipt.observed_at.fold == observed.fold
    assert snap.fetched_at is at and ev.observed_at is observed


@pytest.mark.parametrize('mode', ('shared_zone', 'distinct_zone', 'utc', 'mixed'))
def test_equivalent_instants_do_not_depend_on_tzinfo_identity(mode):
    at, later, _ = moments(CASES[0])
    if mode == 'distinct_zone':
        later = later.astimezone(zone('America/New_York'))
    elif mode == 'utc':
        at, later = at.astimezone(UTC), later.astimezone(UTC)
    elif mode == 'mixed':
        later = later.astimezone(UTC)
    row = prepare_team_research_from_gamma(snapshot(at, at), **args(at, (evidence(later),)))
    assert row.reason_code == 'no_eligible_evidence'
    assert row.future_source_ids == ('source-1',)


def test_future_source_is_not_exposed_when_a_valid_source_remains():
    at, later, _ = moments(CASES[0])
    good = evidence(at)
    future = evidence(later, 'future-secret-marker')
    mixed = task(at, (good, future))
    model = Model()
    result = run_team_research_agent(mixed, model=model, limits=LIMITS)
    assert result.status == 'completed'
    assert 'future-secret-marker' not in json.dumps(model.messages)
    intake = prepare_team_research_from_gamma(snapshot(at, at), **args(at, mixed.evidence))
    assert intake.task.evidence == (good,)
    assert intake.future_source_ids == ('future-secret-marker',)
    assert [r.source_id for r in intake.source_receipts] == ['source-1']


@pytest.mark.parametrize('index', (0, 4))
def test_stream_loaded_zone_hash_matches_existing_utc_wire_contract(index):
    from dataclasses import fields
    from hashlib import sha256
    at, observed, _ = moments(CASES[index])
    original = evidence(observed)
    # Build the old canonical wire format independently, without asdict/deepcopy.
    payload = {f.name: getattr(original, f.name) for f in fields(original)}
    payload['observed_at'] = observed.astimezone(UTC).isoformat()
    expected = sha256(json.dumps(payload, ensure_ascii=True, sort_keys=True,
        separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()
    assert evidence_content_sha256(original) == expected
    assert evidence_content_sha256(replace(original, observed_at=observed.astimezone(UTC))) == expected
    assert original.observed_at is observed


def test_repeated_wall_hour_hashes_bind_different_absolute_instants():
    at, later, _ = moments(CASES[1])
    assert at.replace(tzinfo=None) == later.replace(tzinfo=None)
    assert at.astimezone(UTC) != later.astimezone(UTC)
    assert evidence_content_sha256(evidence(at)) != evidence_content_sha256(evidence(later))
