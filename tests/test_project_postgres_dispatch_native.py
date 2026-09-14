"""Real native batch admission, bounded rounds, stop, restart and process loss.

All requests/model replies are synthetic; no user's database or public API.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
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
from polymarket_alpha_lab import research_capture_psycopg as capture
from polymarket_alpha_lab.research_crypto_launch import CryptoResearchPreview, CryptoResearchSpec
from polymarket_alpha_lab.research_dispatch import ResearchBatch
from polymarket_alpha_lab.research_dispatch_runner import ResearchDispatchStop
from tests.test_research_crypto_launch import snapshots
from tests.test_team_research_cross_source import Model
from tests.test_project_postgres_native import request as original_request, Model as OriginalModel

ROOT = Path(__file__).resolve().parents[1]
ENABLED = os.environ.get('POLYMARKET_ALPHA_LAB_RUN_NATIVE_PROJECT_POSTGRES') == '1'
TAIL = '20260914000000_research_dispatch_batches.sql'


def prepared(n, team='crypto_eth'):
    at = datetime.now(UTC)
    spec = CryptoResearchSpec('queued-'+str(n), team, '0x'+format(n, '064x'), 'queued-'+str(n),
        at+timedelta(minutes=10), 'synthetic-function-model')
    m, cb, kr = snapshots(spec, at)
    preview = CryptoResearchPreview(spec, at, at, m, cb, kr)
    assert preview.to_dict()['forecast_start_status'] == 'requires_operator_approval'
    return preview.request(approved_terms_sha256=preview.to_dict()['terms_sha256'])


_CRASH = r'''
import os, sys
from pathlib import Path
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres

def crash_after_claim(_):
    os._exit(86)

with ProjectPostgres(Path(sys.argv[1])).session() as research:
    research.run_research_batch(batch_id='crash-batch', model_factory=crash_after_claim,
        allow_model_calls=True, max_tasks=1, max_workers=1)
raise SystemExit(99)
'''


@pytest.mark.skipif(not ENABLED, reason='explicit native durable dispatch proof is opt-in')
def test_durable_batches_upgrade_stop_restart_and_crash_without_model_replay(tmp_path, monkeypatch):
    prefix = Path(os.environ['POLYMARKET_ALPHA_LAB_NATIVE_PG_PREFIX'])
    for key in tuple(os.environ):
        if key.upper().startswith('PG'): monkeypatch.delenv(key)
    parent = tmp_path
    if os.name == 'nt':
        parent = Path(os.environ['RUNNER_TEMP']) / ('pal-dispatch-' + uuid.uuid4().hex)
        files.private_directory(parent, create=True)
    root = parent / 'Durable Dispatch Project'; root.mkdir()
    (root/'pyproject.toml').write_text('[project]\nname="polymarket-alpha-lab"\n')
    shutil.copytree(ROOT/'database', root/'database')
    shutil.copytree(ROOT/'supabase/migrations', root/'supabase/migrations')
    # A disposable SOURCE instance at the original 63-migration schema. Never an
    # overlay on a user's kit. The explicit migration must preserve old history.
    manifest = json.loads((root/'database/migrations.lock.json').read_text())
    assert manifest['migrations'][-1]['name'] == TAIL
    (root/'database/migrations.lock.json').write_text(json.dumps(dict(manifest,
        migrations=manifest['migrations'][:-1])))
    (root/'supabase/migrations'/TAIL).unlink()
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0)); port = sock.getsockname()[1]
    import_runtime_directory(root,prefix)
    db=ProjectPostgres(root)
    try:
        assert db.initialize(port=port)['migrations_applied']==63
        with db.session() as session:
            prior=session.run_research(request=original_request(9100), model_factory=lambda _:OriginalModel())
            assert prior.status=='captured'
            info=db._state()
        # Apply only the new tail by the production explicit migrator.
        shutil.copyfile(ROOT/'supabase/migrations'/TAIL,root/'supabase/migrations'/TAIL)
        shutil.copyfile(ROOT/'database/migrations.lock.json',root/'database/migrations.lock.json')
        assert db.migrate()==dict(status='migrated',migrations_applied=1)
        assert db.migrate()==dict(status='migrated',migrations_applied=0)
        assert db.status()['instance_id']==info['instance_id'] and db.status()['status']=='stopped'
        with db.session() as session:
            assert session.inspect(record_id=prior.request.record_id).record==prior.record
            b=ResearchBatch('rounds',tuple(prepared(i, 'crypto_btc' if i%2 else 'crypto_eth') for i in range(4)))
            with pytest.raises(ValueError):session.enqueue_research_batch(batch=b)
            assert session.inspect_research_batch(batch_id='rounds') is None
            with ThreadPoolExecutor(max_workers=4) as pool:
                saved=list(pool.map(lambda _:session.enqueue_research_batch(batch=b,allow_queue_write=True),range(8)))
            assert all(r==saved[0] for r in saved)
            assert db._psql(info,'SELECT count(*) FROM research_capture.dispatch_batches;',owner=False)=='1'
            assert db._psql(info,'SELECT count(*) FROM research_capture.execution_claims;',owner=False)=='1'
            with pytest.raises(capture.ResearchCaptureConflict,match='identity_conflict'):
                session.enqueue_research_batch(batch=replace(b,requests=b.requests[:-1]),allow_queue_write=True)
            control=ResearchDispatchStop();control.request_stop()
            def forbidden(_):pytest.fail('nonpending task started a model')
            assert session.run_research_batch(batch_id='rounds',model_factory=forbidden,
                allow_model_calls=True,stop=control).to_dict()['execution_invocations']==0
            control=ResearchDispatchStop();calls=[]
            def first(team):
                calls.append(team);control.request_stop();return Model()
            first_run=session.run_research_batch(batch_id='rounds',model_factory=first,
                allow_model_calls=True,stop=control,max_workers=1)
            assert first_run.to_dict()['execution_invocations']==1 and calls==['crypto_eth']
            original=first_run.attempts[0].execution
            assert original.status=='captured' and original.record.run.research.status=='completed'
            assert session.inspect_research_batch(batch_id='rounds').states()==('captured','pending','pending','pending')
        assert db.status()['status']=='stopped'
        with db.session() as session:
            assert session.enqueue_research_batch(batch=b,allow_queue_write=True)==saved[0]
            def mixed(team):
                calls.append(team)
                if team=='crypto_btc':raise RuntimeError('synthetic-factory-failure')
                return Model()
            second=session.run_research_batch(batch_id='rounds',model_factory=mixed,
                allow_model_calls=True,max_tasks=2,max_workers=2)
            assert second.to_dict()['execution_invocations']==2
            assert [a.execution.record.run.research.status for a in second.attempts]==['failed','completed']
            assert session.inspect_research_batch(batch_id='rounds').states()==('captured','captured','captured','pending')
            third=session.run_research_batch(batch_id='rounds',model_factory=lambda _:Model(),allow_model_calls=True)
            assert third.to_dict()['execution_invocations']==1
            assert session.run_research_batch(batch_id='rounds',model_factory=forbidden,
                allow_model_calls=True).to_dict()['execution_invocations']==0
            assert session.inspect(record_id=original.request.record_id).record==original.record
            assert len(calls)==3
            # Expiry keeps the admitted inputs but never creates a claim/model.
            expiring=replace(prepared(5),max_start_delay_seconds=10)
            expired=ResearchBatch('expires',(expiring,))
            expired_saved=session.enqueue_research_batch(batch=expired,allow_queue_write=True)
            time.sleep(max(0,10.05-(datetime.now(UTC)-expiring.intake.as_of).total_seconds()))
            assert session.inspect_research_batch(batch_id='expires').states()==('expired',)
            assert session.run_research_batch(batch_id='expires',model_factory=forbidden,
                allow_model_calls=True).to_dict()['execution_invocations']==0
            assert session.enqueue_research_batch(batch=expired,allow_queue_write=True)==expired_saved
            # Array tuple identity must not use order-insensitive JSON containment.
            a=replace(prepared(6),model_id='a',protocol_version='b')
            c=replace(a,record_id='queued-7',model_id='b',protocol_version='a')
            pair=ResearchBatch('ordered-identities',(a,c))
            assert session.enqueue_research_batch(batch=pair,allow_queue_write=True).batch==pair
            # SQL constraints still protect raw app INSERT; no privileged bypass.
            base=ResearchBatch('invalid-fixture',(prepared(8),))
            for defect in ('hash','future','expired','team','duplicate','flag'):
                body=json.loads(base.payload);body['batch_id']='bad-'+defect
                request_body=json.loads(body['requests'][0])
                if defect=='future':request_body['intake']['as_of']=(datetime.now(UTC)+timedelta(hours=1)).isoformat()
                if defect=='expired':request_body['forecast_cutoff_at']='2020-01-01T00:00:00+00:00'
                if defect=='team':request_body['intake']['team_id']='politics'
                if defect=='flag':request_body['readonly']=False
                body['requests'][0]=json.dumps(request_body,separators=(',',':'),sort_keys=True)
                if defect=='duplicate':body['requests']*=2
                payload=json.dumps(body,separators=(',',':'),sort_keys=True)
                digest='0'*64 if defect=='hash' else sha256(payload.encode()).hexdigest()
                def raw_insert(dsn):
                    return capture._local_transaction(dsn,lambda cur:cur.execute(
                        'INSERT INTO research_capture.dispatch_batches (batch_id,request_count,payload,payload_sha256) '
                        'VALUES (%s,%s,%s,%s)',(body['batch_id'],len(body['requests']),payload,digest)))
                with pytest.raises(RuntimeError):session._call(raw_insert)
            for statement in ("UPDATE research_capture.dispatch_batches SET payload=payload WHERE batch_id='rounds'",
                              "DELETE FROM research_capture.dispatch_batches WHERE batch_id='rounds'",
                              'TRUNCATE research_capture.dispatch_batches'):
                with pytest.raises(files.ProjectDatabaseError):db._psql(info,statement,owner=False)
                with pytest.raises(files.ProjectDatabaseError):db._psql(info,statement,owner=True)
            assert session.inspect_research_batch(batch_id='rounds').states()==('captured',)*4
            crash_batch=ResearchBatch('crash-batch',(prepared(9),prepared(10,'crypto_btc')))
            session.enqueue_research_batch(batch=crash_batch,allow_queue_write=True)
        # Child reads only durable batch_id, commits a real claim, then exits
        # inside the synthetic factory before producing any result.
        child=subprocess.run([sys.executable,'-I','-c',_CRASH,str(root)],capture_output=True,
                             text=True,encoding='utf-8',env=files.clean_environment(),timeout=120)
        assert child.returncode==86, child.stdout+child.stderr
        assert db.status()['status']=='running'
        db.down()  # Production graceful stop of this verified disposable instance.
        with db.session() as session:
            crashed=session.inspect_research_batch(batch_id='crash-batch')
            assert crashed.states()==('incomplete','pending')
            claim=crashed.executions[0]
            recovered=[]
            def one_remaining(team):recovered.append(team);return Model()
            result=session.run_research_batch(batch_id='crash-batch',model_factory=one_remaining,
                allow_model_calls=True,max_workers=1)
            assert result.to_dict()['execution_invocations']==1 and recovered==['crypto_btc']
            assert session.inspect_research_batch(batch_id='crash-batch').states()==('incomplete','captured')
            assert session.inspect(record_id=claim.request.record_id)==claim
            assert session.inspect(record_id=prior.request.record_id).record==prior.record
            with pytest.raises(capture.ResearchCaptureConflict,match='history_incomplete'):session.evaluate()
            assert db._psql(info,'SELECT count(*) FROM research_capture.outcomes;',owner=False)=='0'
            assert db._psql(info,'SELECT count(*) FROM project_private.migrations;')=='64'
        assert db.status()['status']=='stopped'
        print('native durable dispatch: PASS; explicit 63-to-64 upgrade, FIFO rounds, stop/restart, crash is incomplete, no replay')
    finally:
        if db.status()['status']!='stopped':db.down()


def test_ordered_identity_fixture_retains_source_binding():
    # This fixture check runs offline too, before relying on the SQL proof.
    # Derive both identities from ONE request so required IDs still bind to
    # its evidence; copying just another intake would invalidate that binding.
    from polymarket_alpha_lab.research_dispatch import decode_batch
    a=replace(prepared(6),model_id='a',protocol_version='b')
    c=replace(a,record_id='queued-7',model_id='b',protocol_version='a')
    pair=ResearchBatch('ordered-identities',(a,c))
    assert a.intake.task_id==c.intake.task_id
    assert a.required_source_ids==c.required_source_ids
    assert (a.model_id,a.protocol_version)!=(c.model_id,c.protocol_version)
    assert decode_batch(pair.payload,pair.content_sha256)==pair
