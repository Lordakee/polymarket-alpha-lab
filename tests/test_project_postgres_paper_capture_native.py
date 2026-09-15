"""Real isolated66->67 upgrade, prospective capture and recovery; synthetic only."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
import os
from pathlib import Path
import shutil
import socket
import time
import uuid

import pytest

from polymarket_alpha_lab import research_paper_capture as store
from polymarket_alpha_lab.research_paper_capture_codec import checksum, dump, encode_paper_scenario
from polymarket_alpha_lab.research_capture_codec import encode_research_capture
from polymarket_alpha_lab.project_postgres import files
from polymarket_alpha_lab.project_postgres.runtime import import_runtime_directory
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres
from polymarket_alpha_lab.team_research_agent_types import ResearchModelReply, ResearchToolCall
from tests.test_research_paper_capture import inputs, scenario

ROOT=Path(__file__).resolve().parents[1]
TAIL='20260915020000_research_paper_simulations.sql'
ENABLED=os.environ.get('POLYMARKET_ALPHA_LAB_RUN_NATIVE_PROJECT_POSTGRES')=='1'


class Model:
    def __init__(self):self.n=0
    def complete(self,**kw):
        self.n+=1
        if self.n==1:name,args='read_evidence',dict(source_id='source')
        else:name,args='finish_research',dict(probability_yes='0.7',confidence='0.9',source_ids=['source'],summary='Synthetic')
        return ResearchModelReply((ResearchToolCall(str(self.n),name,json.dumps(args)),),1)


@pytest.mark.skipif(not ENABLED,reason='explicit native prospective paper capture proof is opt-in')
def test_paper_capture_upgrade_atomic_replay_rejection_and_history_preservation(tmp_path,monkeypatch):
    prefix=Path(os.environ['POLYMARKET_ALPHA_LAB_NATIVE_PG_PREFIX'])
    for key in tuple(os.environ):
        if key.upper().startswith('PG'):monkeypatch.delenv(key)
    parent=tmp_path
    if os.name=='nt':
        parent=Path(os.environ['RUNNER_TEMP'])/('pal-paper-capture-'+uuid.uuid4().hex)
        files.private_directory(parent,create=True)
    root=parent/'Paper Capture With Spaces';root.mkdir()
    (root/'pyproject.toml').write_text('[project]\nname="polymarket-alpha-lab"\n')
    shutil.copytree(ROOT/'database',root/'database')
    shutil.copytree(ROOT/'supabase/migrations',root/'supabase/migrations')
    manifest=json.loads((root/'database/migrations.lock.json').read_text())
    assert len(manifest['migrations'])==67 and manifest['migrations'][-1]['name']==TAIL
    (root/'supabase/migrations'/TAIL).unlink()
    (root/'database/migrations.lock.json').write_text(json.dumps(dict(manifest,migrations=manifest['migrations'][:-1])))
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    import_runtime_directory(root,prefix);db=ProjectPostgres(root)
    try:
        assert db.initialize(port=port)['migrations_applied']==66
        with db.session() as s:
            req,raw=inputs(4100,at=datetime.now(UTC))
            old=s.run_research(request=req,model_factory=lambda _:Model())
            assert old.record.run.research.status=='completed'
            identity=db._state()
        shutil.copyfile(ROOT/'supabase/migrations'/TAIL,root/'supabase/migrations'/TAIL)
        shutil.copyfile(ROOT/'database/migrations.lock.json',root/'database/migrations.lock.json')
        assert db.migrate()['migrations_applied']==1
        assert db.migrate()['migrations_applied']==0
        saved=[]
        with db.session() as s:
            assert s.inspect(record_id=req.record_id).record==old.record
            good=scenario(old,raw,at=datetime.now(UTC))
            with pytest.raises(ValueError):s.capture_paper_research(scenario=good)
            assert s.inspect_paper_research(record_id=req.record_id) is None
            with ThreadPoolExecutor(max_workers=2) as pool:
                twins=list(pool.map(lambda _:s.capture_paper_research(scenario=good,allow_paper_write=True),range(2)))
            assert twins[0]==twins[1]
            assert twins[0].to_dict()['result']['status']=='paper_scenario_ready'
            assert twins[0].recorded_at < req.forecast_cutoff_at
            with pytest.raises(store.db.ResearchCaptureConflict,match='identity_conflict'):
                s.capture_paper_research(scenario=replace(good,requested_size=Decimal(6)),allow_paper_write=True)
            saved.append((good,twins[0],old.record))
            for n,status in ((4101,'rejected'),(4102,'failed')):
                q,raw=inputs(n,'crypto_eth',at=datetime.now(UTC))
                def fail(_):raise RuntimeError('synthetic model failure')
                e=s.run_research(request=q,model_factory=fail if status=='failed' else lambda _:Model())
                value=scenario(e,raw,at=datetime.now(UTC))
                if status=='rejected':value=replace(value,yes_book=replace(value.yes_book,raw_json=b'{bad json'))
                outcome=s.capture_paper_research(scenario=value,allow_paper_write=True)
                assert outcome.to_dict()['result']['status']==('not_simulated' if status=='failed' else 'paper_scenario_rejected')
                assert outcome.scenario.yes_book.raw_json==value.yes_book.raw_json
                saved.append((value,outcome,e.record))
            # A later completed attempt cannot replace the earlier failed one
            # in the original selector, even though it has a new task/record ID.
            later=replace(q,record_id='record-later',intake=replace(q.intake,task_id='task-later',
                task=replace(q.intake.task,task_id='task-later')))
            e=s.run_research(request=later,model_factory=lambda _:Model())
            value=scenario(e,raw,at=datetime.now(UTC))
            outcome=s.capture_paper_research(scenario=value,allow_paper_write=True)
            assert outcome.to_dict()['result']['original_reason_code']=='later_attempt'
            assert outcome.to_dict()['result']['status']=='not_simulated'
            saved.append((value,outcome,e.record))
            # Real COMMIT followed by injected lost acknowledgement: no success
            # receipt escapes. Explicit lookup/replay must find the one saved row.
            q,raw=inputs(4103,at=datetime.now(UTC));e=s.run_research(request=q,model_factory=lambda _:Model())
            value=scenario(e,raw,at=datetime.now(UTC))
            transaction=store.db._local_transaction
            def lose_ack(dsn,operation,**kw):
                result=transaction(dsn,operation,**kw)
                if not kw.get('readonly',False):raise RuntimeError('synthetic lost COMMIT acknowledgement')
                return result
            with monkeypatch.context() as patch:
                patch.setattr(store.db,'_local_transaction',lose_ack)
                with pytest.raises(RuntimeError,match='lost COMMIT'):
                    s.capture_paper_research(scenario=value,allow_paper_write=True)
            outcome=s.inspect_paper_research(record_id=q.record_id)
            assert outcome is not None
            assert s.capture_paper_research(scenario=value,allow_paper_write=True)==outcome
            saved.append((value,outcome,e.record))
            # A fresh five-second admission window can expire without changing
            # the retained input. Explicit replay must not use a new timestamp.
            q,raw=inputs(4104,at=datetime.now(UTC));e=s.run_research(request=q,model_factory=lambda _:Model())
            short=replace(scenario(e,raw,at=datetime.now(UTC)),max_age_seconds=5)
            outcome=s.capture_paper_research(scenario=short,allow_paper_write=True)
            time.sleep(5.1)
            assert s.capture_paper_research(scenario=short,allow_paper_write=True)==outcome
            saved.append((short,outcome,e.record))
            for sql in ('UPDATE research_capture.paper_simulations SET readonly=false',
                        'DELETE FROM research_capture.paper_simulations','TRUNCATE research_capture.paper_simulations'):
                with pytest.raises(files.ProjectDatabaseError):db._psql(identity,sql)
            assert db._psql(identity,'SELECT count(*) FROM research_capture.paper_simulations;')=='6'
            # Direct SQL may not forge the database stamp or skip checks. No
            # clock is patched: the deferred trigger must roll back at COMMIT.
            q,raw=inputs(4107,at=datetime.now(UTC))
            q=replace(q,forecast_cutoff_at=datetime.now(UTC)+timedelta(seconds=20))
            e=s.run_research(request=q,model_factory=lambda _:Model())
            value=scenario(e,raw,at=datetime.now(UTC));history=s.evaluate()
            payload=encode_paper_scenario(value)
            result=dump(store._result_for(history,value,e))
            attempt_hash=checksum(encode_research_capture(record_id=q.record_id,model_id=q.model_id,
                protocol_version=q.protocol_version,run=e.record.run))
            params=(q.record_id,q.content_sha256,attempt_hash,q.record_id,history.generated_at,
                history.input_sha256,q.forecast_cutoff_at,payload,checksum(payload),result,checksum(result))
            insert=('INSERT INTO research_capture.paper_simulations '
                '(record_id,request_sha256,attempt_payload_sha256,first_record_id,history_at,history_sha256,'
                'forecast_cutoff_at,input_payload,input_sha256,result_payload,result_sha256,recorded_at) '
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'2000-01-01T00:00:00Z')")
            for position in (1,8,10):
                wrong=list(params);wrong[position]='b'*64
                def invalid(dsn):
                    return store.db._local_transaction(dsn,lambda c:c.execute(insert,tuple(wrong)))
                with pytest.raises(RuntimeError):s._call(invalid)
                assert s.inspect_paper_research(record_id=q.record_id) is None
            inserted_before_cutoff=[]
            def expire_at_commit(dsn):
                def write(c):
                    c.execute(insert,params)
                    c.execute('SELECT recorded_at FROM research_capture.paper_simulations WHERE record_id=%s',(q.record_id,))
                    stamped=c.fetchone()[0]
                    assert value.decision_at <= stamped < q.forecast_cutoff_at
                    assert stamped.year != 2000
                    inserted_before_cutoff.append(stamped)
                    time.sleep(max(0,(q.forecast_cutoff_at-datetime.now(UTC)).total_seconds())+0.05)
                return store.db._local_transaction(dsn,write)
            with pytest.raises(RuntimeError):s._call(expire_at_commit)
            assert len(inserted_before_cutoff)==1  # Do not accept pre-INSERT failure as deferred proof.
            assert s.inspect_paper_research(record_id=q.record_id) is None
            with pytest.raises(store.db.ResearchCaptureConflict,match='not_prospective'):
                s.capture_paper_research(scenario=value,allow_paper_write=True)
            assert db._psql(identity,'SELECT count(*) FROM research_capture.paper_simulations;')=='6'
            before=s.evaluate().to_dict()
        db.down()
        with db.session() as s:
            for value,outcome,record in saved:
                assert s.inspect_paper_research(record_id=value.record_id)==outcome
                assert s.capture_paper_research(scenario=value,allow_paper_write=True)==outcome
                assert s.inspect(record_id=value.record_id).record==record
            after=s.evaluate(generated_at=datetime.fromisoformat(before['generated_at'])).to_dict()
            assert after==before
            q,raw=inputs(4105,at=datetime.now(UTC))
            def interrupt(_):raise SystemExit(86)
            with pytest.raises(SystemExit):s.run_research(request=q,model_factory=interrupt)
            q2,raw2=inputs(4106,at=datetime.now(UTC));e=s.run_research(request=q2,model_factory=lambda _:Model())
            with pytest.raises(store.db.ResearchCaptureConflict,match='history_incomplete'):
                s.capture_paper_research(scenario=scenario(e,raw2,at=datetime.now(UTC)),allow_paper_write=True)
            assert s.inspect_paper_research(record_id=q2.record_id) is None
            assert s.inspect_paper_research(record_id=saved[0][0].record_id)==saved[0][1]
            assert db._psql(identity,'SELECT count(*) FROM research_capture.paper_simulations;')=='6'
            assert db._psql(identity,'SELECT count(*) FROM project_private.migrations;')=='67'
        assert db.status()['instance_id']==identity['instance_id']
        print('native prospective simulation: PASS;66->67,atomic/rejected/failed,concurrent replay,COMMIT uncertainty,restart,history')
    finally:
        if db.status()['status']!='stopped':db.down()
