"""Actual native PostgreSQL worklist/collection proof; HTTP and models synthetic."""
from dataclasses import replace
from datetime import UTC, datetime, timedelta
import json
import os
from pathlib import Path
import shutil
import socket
import time
import uuid

import pytest

from polymarket_alpha_lab import research_capture_psycopg as capture
from polymarket_alpha_lab import research_execution_psycopg as execution
from polymarket_alpha_lab import research_resolution_poll as poll
from polymarket_alpha_lab.project_postgres import files
from polymarket_alpha_lab.project_postgres.runtime import import_runtime_directory
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres
from polymarket_alpha_lab.research_execution import CapturedResearchRequest
from polymarket_alpha_lab.research_resolution import IndependentResolutionConfirmation, ResolutionSubmission
from polymarket_alpha_lab.team_research_agent_types import ResearchEvidence
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot, prepare_team_research_from_gamma
from tests.test_project_postgres_native import Model

ROOT = Path(__file__).resolve().parents[1]
ENABLED = os.environ.get('POLYMARKET_ALPHA_LAB_RUN_NATIVE_PROJECT_POSTGRES') == '1'


@pytest.mark.skipif(not ENABLED, reason='explicit native resolution worklist proof is opt-in')
def test_native_queue_selects_collects_and_retains_unconfirmed_evidence(tmp_path, monkeypatch):
    prefix = Path(os.environ['POLYMARKET_ALPHA_LAB_NATIVE_PG_PREFIX'])
    for key in tuple(os.environ):
        if key.upper().startswith('PG'): monkeypatch.delenv(key)
    parent = tmp_path
    if os.name == 'nt':
        parent = Path(os.environ['RUNNER_TEMP']) / ('pal-queue-' + uuid.uuid4().hex)
        files.private_directory(parent, create=True)
    root = parent / 'Resolution Queue Project';root.mkdir()
    (root/'pyproject.toml').write_text('[project]\nname="polymarket-alpha-lab"\n')
    shutil.copytree(ROOT/'database', root/'database')
    shutil.copytree(ROOT/'supabase/migrations', root/'supabase/migrations')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0));port = sock.getsockname()[1]
    import_runtime_directory(root, prefix)
    db = ProjectPostgres(root);db.initialize(port=port)
    cid = {name: '0x'+hex(i)[2:]*64 for i, name in enumerate(('candidate','pending','blocked','failed','incomplete'),1)}
    fetched = [];model_calls = []

    class Reader:
        def __init__(self, *, allow_public_fetch): assert allow_public_fetch is True
        def fetch(self, *, market_slug):
            fetched.append(market_slug)
            if market_slug == 'failed': raise OSError('synthetic-private-transport-error')
            value = dict(conditionId=cid[market_slug], slug=market_slug, outcomes=['Yes','No'],
                outcomePrices=['1','0'], closed=True, acceptingOrders=False, umaResolutionStatus='resolved')
            if market_slug in ('pending','incomplete'):value['closed']=False
            if market_slug == 'blocked':value['outcomePrices']=['0.5','0.5']
            return GammaMarketSnapshot(market_slug, datetime.now(UTC), json.dumps(value).encode())

    def request(name, cutoff):
        now = datetime.now(UTC)
        raw=json.dumps(dict(conditionId=cid[name],slug=name,question='Synthetic?',description='Synthetic only rules',
            outcomes=['Yes','No'],active=True,closed=False,endDate=(now+timedelta(days=1)).isoformat())).encode()
        evidence=ResearchEvidence('s','crypto_eth',cid[name],'Synthetic','Synthetic evidence.','synthetic:source',now)
        intake=prepare_team_research_from_gamma(GammaMarketSnapshot(name,now,raw),task_id='task-'+name,
            team_id='crypto_eth',condition_id=cid[name],as_of=now,evidence=(evidence,))
        return CapturedResearchRequest('record-'+name,'synthetic-model','queue-v1',cutoff,intake,required_source_ids=('s',))

    def factory(_):model_calls.append(1);return Model()
    monkeypatch.setattr(poll,'GammaResearchReader',Reader)
    try:
        with db.session() as session:
            assert session.resolution_worklist().items == ()
            cutoff = datetime.now(UTC) + timedelta(seconds=30)
            for name in cid:
                session._call(capture.register_research_market_with_psycopg,
                    condition_id=cid[name],market_slug=name,forecast_cutoff_at=cutoff)
            # A legacy ID and a future cutoff must stay in the worklist but not be fetched.
            session._call(capture.register_research_market_with_psycopg, condition_id='legacy',
                market_slug='legacy',forecast_cutoff_at=cutoff)
            session._call(capture.register_research_market_with_psycopg, condition_id='0x'+'f'*64,
                market_slug='future',forecast_cutoff_at=cutoff+timedelta(hours=1))
            req=request('candidate',cutoff)
            assert session.run_research(request=req,model_factory=factory).status=='captured'
            incomplete=request('incomplete',cutoff)
            session._call(execution._claim,request=incomplete)  # Test-only simulation of a crash before execution.
            assert model_calls==[1]
            with pytest.raises(ValueError):session.collect_resolution_candidates()  # no implicit public fetch
            with pytest.raises(capture.ResearchCaptureConflict,match='market_limit'):
                session.resolution_worklist(max_markets=1)
            before=session.resolution_worklist().to_dict()
            assert before['state_counts']['awaiting_cutoff']==6
            time.sleep(max(0,(cutoff-datetime.now(UTC)).total_seconds())+0.05)
            queue=session.resolution_worklist().to_dict()
            assert queue['registered_market_count']==7 and queue['state_counts']['fetch_due']==5
            assert queue['incomplete_execution_count']==1 and queue['evaluation_blocked_by_incomplete'] is True
            assert queue['state_counts']['unsupported_market']==1 and queue['state_counts']['awaiting_cutoff']==1
            rows={row['market_slug']:row for row in queue['items']}
            assert rows['candidate']['attempt_count']==1 and rows['incomplete']['incomplete_claim_count']==1
            result=session.collect_resolution_candidates(allow_public_fetch=True,max_requests=5)
            assert fetched==['candidate','pending','blocked','failed','incomplete']
            assert result.to_dict()['recorded_count']==4 and result.to_dict()['failed_count']==1
            assert result.to_dict()['confirmed_outcomes_created']==0 and model_calls==[1]
            stored=[attempt.receipt for attempt in result.attempts if attempt.receipt is not None]
            assert all(session.inspect_resolution(review_id=r.submission.review_id)==r for r in stored)
            info=db._state()
            assert db._psql(info,'SELECT count(*) FROM research_capture.outcomes;',owner=False)=='0'
            queue=session.resolution_worklist().to_dict()
            assert queue['state_counts']['needs_confirmation']==1 and queue['state_counts']['waiting']==2
            assert queue['state_counts']['blocked_review']==1 and queue['state_counts']['fetch_due']==1
            again=session.collect_resolution_candidates(allow_public_fetch=True,max_requests=5)
            assert fetched[-1]=='failed' and len(again.attempts)==1
            assert db._psql(info,'SELECT count(*) FROM research_capture.resolution_reviews;',owner=False)=='4'
            # Only the existing operator-confirmation API can create a result.
            candidate=stored[0].submission
            proof=IndependentResolutionConfirmation(cid['candidate'],'candidate',True,cutoff,
                datetime.now(UTC),candidate.snapshot.content_sha256,'synthetic-operator',
                'https://example.invalid/independent','Synthetic independently confirmed result.',independently_verified=True)
            confirmation=replace(candidate,review_id='operator-confirmed',checked_at=datetime.now(UTC),confirmation=proof)
            confirmed=session.record_resolution(submission=confirmation)
            assert confirmed.outcome.actual_yes is True
            final=session.resolution_worklist().to_dict()
            assert final['settled_market_count']==1 and final['unresolved_market_count']==6
            assert final['incomplete_execution_count']==1
            assert 'candidate' not in [r['market_slug'] for r in final['items']]
            # Listing/collection does not repair or conceal incomplete research.
            with pytest.raises(capture.ResearchCaptureConflict,match='history_incomplete'):session.evaluate()
        assert db.status()['status']=='stopped'
        with db.session() as session:
            reloaded=session.resolution_worklist().to_dict()
            assert reloaded['settled_market_count']==1 and reloaded['unresolved_market_count']==6
            assert session.inspect_resolution(review_id='operator-confirmed')==confirmed
            assert all(session.inspect_resolution(review_id=r.submission.review_id)==r for r in stored)
            assert model_calls==[1]
        print('native resolution queue: PASS; bounded synthetic fetch, real append-only evidence, no automatic outcomes')
    finally:
        if db.status()['status']!='stopped':db.down()
