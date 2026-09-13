"""Real project-native DB from empty -> captured crypto research -> worklist.

Public readers/models are synthetic. No user data, model key, live HTTP or service.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
import os
import json
from pathlib import Path
import shutil
import socket
import uuid

import pytest

from polymarket_alpha_lab import research_crypto_launch_service as launch
from polymarket_alpha_lab import research_execution_psycopg as execution
from polymarket_alpha_lab.research_capture_psycopg import ResearchCaptureConflict
from polymarket_alpha_lab.project_postgres import files
from polymarket_alpha_lab.project_postgres.runtime import import_runtime_directory
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres
from polymarket_alpha_lab.research_crypto_launch import CryptoLaunchBlocked, CryptoResearchPreview, CryptoResearchSpec
from tests.test_research_crypto_launch import snapshots
from tests.test_team_research_cross_source import Model

ROOT = Path(__file__).resolve().parents[1]
ENABLED = os.environ.get('POLYMARKET_ALPHA_LAB_RUN_NATIVE_PROJECT_POSTGRES') == '1'


@pytest.mark.skipif(not ENABLED, reason='explicit native crypto launch proof is opt-in')
def test_native_empty_database_to_captured_research_and_worklist(tmp_path, monkeypatch):
    prefix=Path(os.environ['POLYMARKET_ALPHA_LAB_NATIVE_PG_PREFIX'])
    for key in tuple(os.environ):
        if key.upper().startswith('PG'):monkeypatch.delenv(key)
    parent=tmp_path
    if os.name=='nt':
        parent=Path(os.environ['RUNNER_TEMP'])/('pal-launch-'+uuid.uuid4().hex)
        files.private_directory(parent,create=True)
    root=parent/'Crypto Launch Project';root.mkdir()
    (root/'pyproject.toml').write_text('[project]\nname="polymarket-alpha-lab"\n')
    shutil.copytree(ROOT/'database',root/'database')
    shutil.copytree(ROOT/'supabase/migrations',root/'supabase/migrations')
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    import_runtime_directory(root,prefix)
    db=ProjectPostgres(root);db.initialize(port=port)
    count=[];fetches=[]
    def factory(_):count.append(1);return Model()
    def forbidden(*a,**k):pytest.fail('duplicate execution must not refetch public data')
    try:
        with db.session() as session:
            assert session.resolution_worklist().to_dict()['registered_market_count']==0
            at=datetime.now(UTC)
            spec=CryptoResearchSpec('launch-1','crypto_eth','0x'+'a'*64,'synthetic-event',
                at+timedelta(hours=1),'synthetic-function-model')
            m,cb,kr=snapshots(spec,at)
            p=CryptoResearchPreview(spec,at,at,m,cb,kr)
            digest=p.to_dict()['terms_sha256']
            # Recent reference bars cannot authorize a whole-window touch event.
            # Exercise the production session before ANY market/claim is recorded.
            path_spec=replace(spec,record_id='blocked-path')
            path_body=json.loads(m.raw_json)
            path_body['question']='Will Ethereum touch $2,000 in September?'
            path_body['description']=('This market resolves Yes if any Binance ETH/USDT '
                '1-minute candle has Low <= $2,000 during September. Synthetic rules.')
            path_preview=replace(p,spec=path_spec,market=replace(m,raw_json=json.dumps(path_body).encode()))
            assert path_preview.to_dict()['forecast_start_status']=='blocked_by_contract_scope'
            with pytest.raises(CryptoLaunchBlocked,match='path_history_required'):
                session.launch_crypto_research(spec=path_spec,preview=path_preview,
                    approved_terms_sha256=path_preview.to_dict()['terms_sha256'],model_factory=forbidden,
                    allow_public_fetch=True,allow_model_calls=True)
            assert session.resolution_worklist().to_dict()['registered_market_count']==0
            info=db._state()
            assert db._psql(info,'SELECT count(*) FROM research_capture.execution_claims;',owner=False)=='0'
            assert db._psql(info,'SELECT count(*) FROM research_capture.attempts;',owner=False)=='0'
            assert count==[] and fetches==[]
            monkeypatch.setattr(launch,'fetch_crypto_research_preview',lambda *a,**k:fetches.append(1) or p)
            # Normal launch, not a test-only direct markets INSERT.
            result=session.launch_crypto_research(spec=spec,approved_terms_sha256=digest,model_factory=factory,
                allow_public_fetch=True,allow_model_calls=True)
            assert result.status=='captured' and result.record.run.research.status=='completed'
            assert len(result.request.required_source_ids)==2
            assert count==[1] and fetches==[1]
            monkeypatch.setattr(launch,'fetch_crypto_research_preview',forbidden)
            kwargs=dict(spec=spec,approved_terms_sha256=digest,model_factory=forbidden,
                        allow_public_fetch=True,allow_model_calls=True)
            with ThreadPoolExecutor(max_workers=8) as pool:
                duplicates=tuple(pool.map(lambda _:session.launch_crypto_research(**kwargs),range(8)))
            assert all(r.status=='already_captured' and r.record==result.record for r in duplicates)
            assert count==[1] and fetches==[1]
            with pytest.raises(ResearchCaptureConflict):session.launch_crypto_research(**dict(kwargs,
                spec=replace(spec,lookback_hours=2)))
            with pytest.raises(ResearchCaptureConflict):session.launch_crypto_research(**dict(kwargs,
                approved_terms_sha256='0'*64))
            # A normal model-factory error is saved, not hidden by preflight.
            def broken(_):raise RuntimeError('synthetic-private-model-error')
            failed_spec=replace(spec,record_id='launch-failed')
            failed_preview=replace(p,spec=failed_spec)
            failed=session.launch_crypto_research(spec=failed_spec,approved_terms_sha256=digest,
                model_factory=broken,allow_public_fetch=True,allow_model_calls=True,preview=failed_preview)
            assert failed.status=='captured' and failed.record.run.research.reason_code=='model_factory_failed'
            # A crash after claim remains incomplete; changing only record ID
            # must not change the protocol cohort and bypass the existing guard.
            pending_spec=replace(spec,record_id='launch-incomplete')
            pending_preview=replace(p,spec=pending_spec)
            pending_request=pending_preview.request(approved_terms_sha256=digest)
            assert pending_request.protocol_version==result.request.protocol_version
            _,claim=session._call(execution._claim,request=pending_request)
            assert claim.status=='incomplete'
            pending=session.launch_crypto_research(**dict(kwargs,spec=pending_spec))
            assert pending.status=='incomplete'
            another=replace(spec,record_id='launch-not-a-retry')
            with pytest.raises(ResearchCaptureConflict,match='prior_incomplete'):
                session.launch_crypto_research(**dict(kwargs,spec=another,preview=replace(p,spec=another)))
            queue=session.resolution_worklist().to_dict()
            assert queue['registered_market_count']==1 and queue['unresolved_market_count']==1
            assert queue['incomplete_execution_count']==1
            assert queue['items'][0]['attempt_count']==2
            assert queue['items'][0]['state']=='awaiting_cutoff'
            assert queue['evaluation_blocked_by_incomplete'] is True
            with pytest.raises(ResearchCaptureConflict,match='history_incomplete'):session.evaluate()
            info=db._state()
            assert db._psql(info,'SELECT count(*) FROM research_capture.outcomes;',owner=False)=='0'
            assert db._psql(info,'SELECT count(*) FROM research_capture.resolution_reviews;',owner=False)=='0'
        assert db.status()['status']=='stopped'
        with db.session() as session:
            repeated=session.launch_crypto_research(**kwargs)
            assert repeated.record==result.record
            after=session.resolution_worklist().to_dict()
            assert after['registered_market_count']==1 and after['incomplete_execution_count']==1
            assert session.inspect(record_id='launch-failed').record==failed.record
        assert count==[1] and fetches==[1]
        print('native crypto launch: PASS; empty DB to prospective capture, exact replay, stable cohort, incomplete guard')
    finally:
        if db.status()['status']!='stopped':db.down()
