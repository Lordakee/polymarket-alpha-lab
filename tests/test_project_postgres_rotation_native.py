"""Opt-in real database rotation: failure fairness, restart, replay and crash.

Fresh project only. Synthetic guarded crypto requests and models; no public API.
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
import uuid

import pytest

from polymarket_alpha_lab import research_capture_psycopg as capture
from polymarket_alpha_lab import research_dispatch_runner as drain
from polymarket_alpha_lab.research_dispatch import ResearchBatch
from polymarket_alpha_lab.project_postgres import files
from polymarket_alpha_lab.project_postgres.runtime import import_runtime_directory
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres
from tests.test_project_postgres_dispatch_native import prepared
from tests.test_team_research_cross_source import Model

ROOT = Path(__file__).resolve().parents[1]
ENABLED = os.environ.get('POLYMARKET_ALPHA_LAB_RUN_NATIVE_PROJECT_POSTGRES') == '1'
TAIL = '20260915000000_research_dispatch_turns.sql'

_CRASH = r'''
import os, sys
from pathlib import Path
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres

def crash(_): os._exit(86)
with ProjectPostgres(Path(sys.argv[1])).session() as research:
    research.run_research_rotation(rotation_id='crash', turn_id='crash-1',
        batch_ids_to_run=('crash-batch',), model_factory=crash,
        allow_model_calls=True, max_tasks=1, max_workers=1)
raise SystemExit(99)
'''


@pytest.mark.skipif(not ENABLED, reason='explicit native durable rotation proof is opt-in')
def test_rotation_failure_fairness_upgrade_restart_and_no_reclaim(tmp_path, monkeypatch):
    prefix=Path(os.environ['POLYMARKET_ALPHA_LAB_NATIVE_PG_PREFIX'])
    for key in tuple(os.environ):
        if key.upper().startswith('PG'):monkeypatch.delenv(key)
    parent=tmp_path
    if os.name=='nt':
        parent=Path(os.environ['RUNNER_TEMP'])/('pal-rotation-'+uuid.uuid4().hex)
        files.private_directory(parent,create=True)
    root=parent/'Rotation With Spaces';root.mkdir()
    (root/'pyproject.toml').write_text('[project]\nname="polymarket-alpha-lab"\n')
    shutil.copytree(ROOT/'database',root/'database')
    shutil.copytree(ROOT/'supabase/migrations',root/'supabase/migrations')
    manifest=json.loads((root/'database/migrations.lock.json').read_text())
    for later in manifest['migrations'][65:]:
        (root/'supabase/migrations'/later['name']).unlink()
    manifest['migrations'] = manifest['migrations'][:65]
    assert len(manifest['migrations'])==65 and manifest['migrations'][-1]['name']==TAIL
    (root/'supabase/migrations'/TAIL).unlink()
    (root/'database/migrations.lock.json').write_text(json.dumps(dict(manifest,migrations=manifest['migrations'][:-1])))
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    import_runtime_directory(root,prefix);db=ProjectPostgres(root)
    try:
        assert db.initialize(port=port)['migrations_applied']==64
        with db.session() as research:
            old_batch=ResearchBatch('old-batch',(prepared(90),))
            old_receipt=research.enqueue_research_batch(batch=old_batch,allow_queue_write=True)
            old_run=research.run_research_batch(batch_id='old-batch',model_factory=lambda _:Model(),
                                              allow_model_calls=True)
            old_record=old_run.attempts[0].execution.record
            assert old_record.run.research.status=='completed'
        shutil.copyfile(ROOT/'supabase/migrations'/TAIL,root/'supabase/migrations'/TAIL)
        (root/'database/migrations.lock.json').write_text(json.dumps(manifest))
        assert db.migrate()['migrations_applied']==1
        assert db.migrate()['migrations_applied']==0
        with db.session() as research:
            assert research.enqueue_research_batch(batch=old_batch,allow_queue_write=True)==old_receipt
            assert research.inspect(record_id=old_record.record_id).record==old_record
            info=db._state()
            a=ResearchBatch('A',tuple(prepared(100+i) for i in range(3)))
            b=ResearchBatch('B',tuple(prepared(200+i,'crypto_btc') for i in range(2)))
            for batch in (a,b):research.enqueue_research_batch(batch=batch,allow_queue_write=True)
            original=drain.run_captured_research_with_psycopg;calls=[]
            def flaky(dsn,*,request,model_factory):
                calls.append(request.record_id)
                if request.record_id==a.requests[0].record_id:
                    raise capture.ResearchCaptureConflict('synthetic_preclaim_failure')
                return original(dsn,request=request,model_factory=model_factory)
            monkeypatch.setattr(drain,'run_captured_research_with_psycopg',flaky)
            def invoke(session,tid,**kw):
                return session.run_research_rotation(rotation_id='fair',turn_id=tid,
                    batch_ids_to_run=('A','B'),model_factory=lambda _:Model(),allow_model_calls=True,
                    max_tasks=1,max_workers=1,**kw)
            first=invoke(research,'t1')
            assert first.attempts[0].status=='operation_failed' and first.stored.turn.next_slot==1
            assert research.inspect(record_id=a.requests[0].record_id) is None
            repeat=invoke(research,'t1')
            assert repeat.status=='turn_already_reserved' and repeat.stored==first.stored and len(calls)==1
            stop=drain.ResearchDispatchStop();stop.request_stop()
            assert invoke(research,'stopped',stop=stop).status=='stopped_before_reservation'
            assert research.inspect_research_turn(rotation_id='fair',turn_id='stopped') is None
        assert db.status()['status']=='stopped'
        with db.session() as research:
            for number,expected in enumerate(('queued-200','queued-101','queued-201','queued-102'),2):
                result=invoke(research,'t'+str(number))
                assert result.attempts[0].execution.request.record_id==expected
                assert result.attempts[0].execution.record.run.research.status=='completed'
            assert calls==['queued-100','queued-200','queued-101','queued-201','queued-102']
            assert research.inspect_research_batch(batch_id='A').states()==('pending','captured','captured')
            assert invoke(research,'t6').attempts[0].status=='operation_failed'
            assert calls[-1]=='queued-100'
            # Same turn concurrently submitted: one reservation, at most one
            # invocation; original execution claim remains the loop authority.
            monkeypatch.setattr(drain,'run_captured_research_with_psycopg',original)
            factories=[]
            def factory(team):factories.append(team);return Model()
            def concurrent(_):
                return research.run_research_rotation(rotation_id='fair',turn_id='race',batch_ids_to_run=('A','B'),
                    model_factory=factory,allow_model_calls=True,max_tasks=1,max_workers=1)
            with ThreadPoolExecutor(max_workers=4) as pool:reports=list(pool.map(concurrent,range(8)))
            assert sum(r.status=='dispatched' for r in reports)==1 and factories==['crypto_eth']
            assert all(r.stored==reports[0].stored for r in reports)
            assert research.inspect_research_batch(batch_id='A').states()==('captured',)*3
            original_turn=research.inspect_research_turn(rotation_id='fair',turn_id='t1')
            assert original_turn==first.stored
            with pytest.raises(capture.ResearchCaptureConflict):
                research.run_research_rotation(rotation_id='fair',turn_id='t1',batch_ids_to_run=('B','A'),
                    model_factory=factory,allow_model_calls=True,max_tasks=1,max_workers=1)
            # Direct app writes cannot jump/rewind a cursor, change its roster,
            # omit hard flags or claim a future selection time.
            latest=reports[0].stored.turn
            for defect in ('next','sequence','roster','flags','future','hash','request_key'):
                t=replace(latest,turn_id='bad-'+defect,turn_number=latest.turn_number+1,start_slot=latest.next_slot)
                data=json.loads(t.payload);next_slot=t.next_slot;number=t.turn_number
                if defect=='next':next_slot=(next_slot+1)%len(t.states)
                if defect=='sequence':number+=1;data['turn_number']=number
                if defect=='roster':data['roster'].reverse()
                if defect=='flags':data['readonly']=False
                if defect=='request_key':data['request_keys'][0][1]='a'*64
                if defect=='future':data['observed_at'][0]=(datetime.now(UTC)+timedelta(days=1)).isoformat()
                payload=json.dumps(data,sort_keys=True,separators=(',',':'))
                digest='0'*64 if defect=='hash' else sha256(payload.encode()).hexdigest()
                def insert(dsn):
                    return capture._local_transaction(dsn,lambda c:c.execute(
                        'INSERT INTO research_capture.dispatch_turns '
                        '(rotation_id,turn_id,turn_number,start_slot,next_slot,roster_sha256,payload,payload_sha256) '
                        'VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
                        ('fair',t.turn_id,number,t.start_slot,next_slot,t.roster_sha256,payload,digest)))
                with pytest.raises(RuntimeError):research._call(insert)
            for sql in ("UPDATE research_capture.dispatch_turns SET next_slot=0 WHERE rotation_id='fair'",
                        "DELETE FROM research_capture.dispatch_turns WHERE rotation_id='fair'",
                        'TRUNCATE research_capture.dispatch_turns'):
                for owner in (False,True):
                    with pytest.raises(files.ProjectDatabaseError):db._psql(info,sql,owner=owner)
            assert db._psql(info,'SELECT count(*) FROM research_capture.dispatch_turns;',owner=False)=='7'
            crash_batch=ResearchBatch('crash-batch',(prepared(300),prepared(301,'crypto_btc')))
            research.enqueue_research_batch(batch=crash_batch,allow_queue_write=True)
        child=subprocess.run([sys.executable,'-I','-c',_CRASH,str(root)],capture_output=True,text=True,
            encoding='utf-8',env=files.clean_environment(),timeout=120)
        assert child.returncode==86,(child.stdout,child.stderr)
        db.down()
        with db.session() as research:
            lost=research.inspect_research_batch(batch_id='crash-batch')
            assert lost.states()==('incomplete','pending')
            def forbidden(_):pytest.fail('replayed turn must never call a model')
            replay=research.run_research_rotation(rotation_id='crash',turn_id='crash-1',
                batch_ids_to_run=('crash-batch',),model_factory=forbidden,allow_model_calls=True,max_tasks=1,max_workers=1)
            assert replay.status=='turn_already_reserved' and replay.stored.turn.next_slot==1
            resumed=research.run_research_rotation(rotation_id='crash',turn_id='crash-2',
                batch_ids_to_run=('crash-batch',),model_factory=lambda _:Model(),allow_model_calls=True,max_tasks=1,max_workers=1)
            assert resumed.attempts[0].execution.request.record_id=='queued-301'
            assert research.inspect_research_batch(batch_id='crash-batch').states()==('incomplete','captured')
            assert research.inspect(record_id='queued-300')==lost.executions[0]
            assert research.inspect(record_id=old_record.record_id).record==old_record
            with pytest.raises(capture.ResearchCaptureConflict,match='history_incomplete'):research.evaluate()
            assert db._psql(info,'SELECT count(*) FROM project_private.migrations;')=='65'
        assert db.status()['status']=='stopped'
        print('native rotation: PASS; 64-to-65 preserves history; failed head rotates; replay inert; crash remains incomplete')
    finally:
        if db.status()['status']!='stopped':db.down()
