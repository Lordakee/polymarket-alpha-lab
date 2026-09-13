"""Opt-in actual native database resolution evidence/promotion proof."""
from concurrent.futures import ThreadPoolExecutor
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

from polymarket_alpha_lab.project_postgres import files
from polymarket_alpha_lab.project_postgres.runtime import import_runtime_directory
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres
from polymarket_alpha_lab.research_execution import CapturedResearchRequest
from polymarket_alpha_lab.research_resolution import IndependentResolutionConfirmation, ResolutionSubmission
from polymarket_alpha_lab.research_resolution_codec import encode_resolution
from polymarket_alpha_lab.team_research_agent_types import ResearchEvidence
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot, prepare_team_research_from_gamma
from tests.test_project_postgres_native import Model

ROOT = Path(__file__).resolve().parents[1]
ENABLED = os.environ.get('POLYMARKET_ALPHA_LAB_RUN_NATIVE_PROJECT_POSTGRES')=='1'


@pytest.mark.skipif(not ENABLED,reason='explicit native PostgreSQL resolution proof is opt-in')
def test_native_resolution_review_promotes_atomically_and_preserves_evidence(tmp_path,monkeypatch):
    prefix=Path(os.environ['POLYMARKET_ALPHA_LAB_NATIVE_PG_PREFIX'])
    for key in tuple(os.environ):
        if key.upper().startswith('PG'):monkeypatch.delenv(key)
    parent=tmp_path
    if os.name=='nt':
        parent=Path(os.environ['RUNNER_TEMP'])/('pal-resolution-'+uuid.uuid4().hex)
        files.private_directory(parent,create=True)
    root=parent/'Resolution Project';root.mkdir()
    (root/'pyproject.toml').write_text('[project]\nname="polymarket-alpha-lab"\n')
    shutil.copytree(ROOT/'database',root/'database')
    shutil.copytree(ROOT/'supabase/migrations',root/'supabase/migrations')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    import_runtime_directory(root,prefix)
    db=ProjectPostgres(root);db.initialize(port=port)
    cid='0x'+'a'*64;slug='native-resolution';created=[]
    def factory(_):
        created.append(1);return Model()
    try:
        with db.session() as session:
            now=datetime.now(UTC);cutoff=now+timedelta(seconds=10)
            raw=json.dumps(dict(conditionId=cid,slug=slug,question='Synthetic?',
                description='Synthetic YES/NO criteria',outcomes=['Yes','No'],active=True,closed=False,
                endDate=(now+timedelta(days=1)).isoformat())).encode()
            evidence=ResearchEvidence('s','crypto_eth',cid,'Synthetic','Synthetic only.','synthetic:source',now)
            intake=prepare_team_research_from_gamma(GammaMarketSnapshot(slug,now,raw),task_id='t',team_id='crypto_eth',
                condition_id=cid,as_of=now,evidence=(evidence,))
            request=CapturedResearchRequest('record-1','synthetic-model','native-resolution-v1',cutoff,intake,
                required_source_ids=('s',))
            captured=session.run_research(request=request,model_factory=factory)
            assert captured.status=='captured' and len(created)==1
            time.sleep(max(0,(cutoff-datetime.now(UTC)).total_seconds())+0.05)
            resolved=datetime.now(UTC)
            raw=json.dumps(dict(conditionId=cid,slug=slug,outcomes=['Yes','No'],outcomePrices=['1','0'],
                closed=True,acceptingOrders=False,umaResolutionStatus='resolved')).encode()
            snap=GammaMarketSnapshot(slug,datetime.now(UTC),raw)
            unconfirmed=ResolutionSubmission('candidate',cid,snap,datetime.now(UTC))
            saved=session.record_resolution(submission=unconfirmed)
            assert saved.outcome is None and session.evaluate().groups[0].outcome_pending_count==1
            # The legacy API cannot claim reviewed provenance without evidence.
            with pytest.raises(RuntimeError,match='research_capture_database_failed'):
                session.capture_outcome(condition_id=cid,market_slug=slug,resolved_at=resolved,
                    actual_yes=True,source_reference='urn:polymarket-alpha-lab:resolution-review:missing',
                    source_content_sha256='0'*64)
            assert session.evaluate().groups[0].outcome_pending_count==1
            proof=IndependentResolutionConfirmation(cid,slug,True,resolved,datetime.now(UTC),
                snap.content_sha256,'synthetic-operator','https://example.invalid/official',
                'Synthetic result independently reviewed for this integration test.',independently_verified=True)
            confirmed=ResolutionSubmission('confirmed',cid,snap,datetime.now(UTC),proof)
            with ThreadPoolExecutor(max_workers=4) as pool:
                receipts=tuple(pool.map(lambda _:session.record_resolution(submission=confirmed),range(8)))
            assert all(item==receipts[0] for item in receipts)
            assert receipts[0].outcome.actual_yes is True
            assert receipts[0].outcome.resolved_at==resolved
            assert session.inspect_resolution(review_id='confirmed')==receipts[0]
            assert session.inspect_resolution(review_id='candidate')==saved
            scored=session.evaluate()
            assert scored.groups[0].scores.sample_count==1
            info=db._state()
            assert db._psql(info,'SELECT count(*) FROM research_capture.resolution_reviews;',owner=False)=='2'
            for verb in ('DELETE FROM','UPDATE','TRUNCATE'):
                statement=verb+' research_capture.resolution_reviews'
                if verb=='UPDATE':statement+=" SET reason_code='changed'"
                with pytest.raises(files.ProjectDatabaseError):db._psql(info,statement+';',owner=False)
            # A second review cannot overwrite an already confirmed outcome.
            from polymarket_alpha_lab.research_capture_psycopg import ResearchCaptureConflict
            with pytest.raises(ResearchCaptureConflict):
                session.record_resolution(submission=replace(confirmed,review_id='different-confirmation'))
            # Force failure AFTER INSERT, prove the real transaction rolls back.
            from polymarket_alpha_lab import research_resolution_store as store
            with monkeypatch.context() as patch:
                patch.setattr(store,'_decode_row',lambda *_:(_ for _ in ()).throw(ValueError('synthetic-post-insert-failure')))
                with pytest.raises(RuntimeError,match='research_capture_database_failed'):
                    session.record_resolution(submission=replace(unconfirmed,review_id='rolled-back'))
            assert session.inspect_resolution(review_id='rolled-back') is None
            # Deferred SQL constraint refuses ready evidence without its outcome.
            from polymarket_alpha_lab.project_postgres.sql import literal
            from hashlib import sha256
            orphan=replace(confirmed,review_id='orphan')
            payload=encode_resolution(orphan)
            query="INSERT INTO research_capture.resolution_reviews " \
                "(review_id,condition_id,market_slug,checked_at,status,reason_code,actual_yes,resolved_at,payload,payload_sha256) VALUES ("
            query+=','.join(literal(v) for v in (orphan.review_id,cid,slug,orphan.checked_at.isoformat(),
                'ready','operator_confirmed'))+",true,"+','.join(literal(v) for v in (
                resolved.isoformat(),payload,sha256(payload.encode()).hexdigest()))+');'
            with pytest.raises(files.ProjectDatabaseError):db._psql(info,query,owner=False)
            assert session.inspect_resolution(review_id='orphan') is None
        assert db.status()['status']=='stopped'
        with db.session() as session:
            assert session.inspect_resolution(review_id='confirmed')==receipts[0]
            assert session.inspect_resolution(review_id='candidate')==saved
            assert session.evaluate(generated_at=scored.generated_at)==scored
        assert len(created)==1
        print('native resolution: PASS; raw evidence and outcome atomic; no public/model calls')
    finally:
        if db.status()['status']!='stopped':db.down()
