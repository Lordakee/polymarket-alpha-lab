"""Opt-in actual native database resolution evidence/promotion proof."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
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
    def console(*args, expected=0):
        completed = subprocess.run([sys.executable, '-I', str(ROOT/'scripts/evaluate_project_research.py'),
            '--root', str(root), *args], capture_output=True, text=True, encoding='utf-8',
            env=files.clean_environment(), timeout=120, check=False)
        assert completed.returncode == expected, (completed.stdout, completed.stderr)
        assert completed.stderr == ''
        value = json.loads(completed.stdout)
        assert value['public_network_called'] is value['live_model_called'] is False
        assert value['business_writes_performed'] is value['outcome_confirmation_performed'] is False
        assert db.status()['status'] == 'stopped'
        assert db.status()['instance_id'] == original_identity
        return value
    original_identity = db.status()['instance_id']
    try:
        empty = console()
        assert empty['evaluation']['evaluation_status'] == 'no_visible_attempts'
        assert empty['evaluation']['groups'] == []
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
            pending_at = session.evaluate().generated_at
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
        pending_console = console('--as-of', pending_at.isoformat())
        assert pending_console['evaluation']['evaluation_status'] == 'no_scored_forecasts'
        assert pending_console['evaluation']['decision_counts']['outcome_pending'] == 1
        assert pending_console['evaluation']['groups'][0]['scores']['mean_brier_score'] is None
        view = console('--as-of', scored.generated_at.isoformat(), '--include-decisions')['evaluation']
        assert view['evaluation_status'] == 'diagnostics_available'
        assert view['groups'] == scored.to_dict()['groups']
        assert view['decisions'] == scored.to_dict()['decisions']
        assert view['input_sha256'] == scored.input_sha256
        assert view['groups'][0]['scores']['sample_status'] == 'insufficient_sample'
        future = console('--as-of', (datetime.now(UTC)+timedelta(days=1)).isoformat(), expected=1)
        assert future['reason_code'] == 'research_evaluation_from_future' and future['evaluation'] is None
        # Test-only crash simulation on a DIFFERENT prospective market. The CLI
        # must refuse partial scoring but still permit the earlier as-of snapshot.
        from polymarket_alpha_lab import research_execution_psycopg as execution
        pending_cid = '0x'+'b'*64
        pending_slug = 'native-console-incomplete'
        at = datetime.now(UTC)
        pending_snap = GammaMarketSnapshot(pending_slug, at, json.dumps(dict(conditionId=pending_cid,
            slug=pending_slug, question='Synthetic?', description='Synthetic rule', outcomes=['Yes','No'],
            active=True, closed=False, endDate=(at+timedelta(days=1)).isoformat())).encode())
        source = ResearchEvidence('s','crypto_eth',pending_cid,'Synthetic','Synthetic only.','synthetic:source',at)
        pending_intake = prepare_team_research_from_gamma(pending_snap,task_id='pending-console',team_id='crypto_eth',
            condition_id=pending_cid,as_of=at,evidence=(source,))
        pending_request = CapturedResearchRequest('pending-console','synthetic-model','native-resolution-v1',
            at+timedelta(hours=1),pending_intake,required_source_ids=('s',))
        with db.session() as session:
            session._call(execution._claim, request=pending_request)
        blocked = console(expected=1)
        assert blocked['reason_code'] == 'research_execution_history_incomplete'
        assert blocked['evaluation'] is None and blocked['history_gate'] == 'not_established'
        historical = console('--as-of', scored.generated_at.isoformat())['evaluation']
        assert historical['input_sha256'] == scored.input_sha256
        with db.session() as session:
            assert session.inspect(record_id='record-1').record == captured.record
            assert session.inspect(record_id='pending-console').status == 'incomplete'
            info = db._state()
            assert db._psql(info,'SELECT count(*) FROM research_capture.attempts;',owner=False) == '1'
            assert db._psql(info,'SELECT count(*) FROM research_capture.outcomes;',owner=False) == '1'
            assert db._psql(info,'SELECT count(*) FROM research_capture.execution_claims;',owner=False) == '2'
        assert len(created)==1
        print('native console: PASS; empty, pending, scored, future and incomplete states; no writes')
        print('native resolution: PASS; raw evidence and outcome atomic; no public/model calls')
    finally:
        if db.status()['status']!='stopped':db.down()
