"""Opt-in disposable project-owned native cluster proof; no Docker or user DB.
The explicit prefix supplies ONLY trusted binaries, never its data or credentials.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from hashlib import sha256
import json
import os
import re
from pathlib import Path
import shutil
import socket
import uuid

import pytest

from polymarket_alpha_lab.project_postgres.files import ProjectDatabaseError
from polymarket_alpha_lab.project_postgres.runtime import import_runtime_directory
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres
from polymarket_alpha_lab.research_execution import CapturedResearchRequest
from polymarket_alpha_lab.team_research_agent_types import ResearchEvidence, ResearchModelReply, ResearchToolCall
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot, prepare_team_research_from_gamma

ROOT=Path(__file__).resolve().parents[1]
ENABLED=os.environ.get('POLYMARKET_ALPHA_LAB_RUN_NATIVE_PROJECT_POSTGRES')=='1'


class Model:
    def __init__(self): self.calls=0
    def complete(self,**kwargs):
        self.calls+=1
        if self.calls==1:
            name,args='read_evidence',{'source_id':'s'}
        else:
            name,args='finish_research',dict(probability_yes='0.6',confidence='0.2',
                summary='Synthetic native integration fixture.',source_ids=['s'])
        return ResearchModelReply((ResearchToolCall(f'call-{self.calls}',name,json.dumps(args)),),1)


def request(index):
    now=datetime.now(UTC)
    slug=f'native-fixture-{index}';condition=f'native-condition-{index}'
    snapshot=GammaMarketSnapshot(slug,now,json.dumps(dict(slug=slug,conditionId=condition,
        question='Synthetic?',description='Synthetic resolution criterion',outcomes=['Yes','No'],
        active=True,closed=False,endDate=(now+timedelta(days=1)).isoformat())).encode())
    evidence=ResearchEvidence('s','crypto_eth',condition,'Synthetic source','Synthetic text','synthetic:native',now)
    intake=prepare_team_research_from_gamma(snapshot,task_id=f'task-{index}',team_id='crypto_eth',
        condition_id=condition,as_of=now,evidence=(evidence,))
    return CapturedResearchRequest(f'record-{index}','synthetic-model','native-proof-v1',
        now+timedelta(hours=1),intake,required_source_ids=('s',))


@pytest.mark.skipif(not ENABLED,reason='explicit native PostgreSQL runtime proof is opt-in')
def test_native_project_lifecycle_all_migrations_and_real_research(tmp_path,monkeypatch):
    prefix=Path(os.environ['POLYMARKET_ALPHA_LAB_NATIVE_PG_PREFIX'])
    assert prefix.is_absolute() and (prefix/'bin').is_dir()
    for k in tuple(os.environ):
        if k.upper().startswith('PG'): monkeypatch.delenv(k)
    from polymarket_alpha_lab.project_postgres import files
    if os.name == 'nt':
        # Pytest's admin-owned 0700 basetemp can exclude PostgreSQL's safely
        # restricted child token. Create our OWN private test root outside it;
        # never alter an existing parent's ACL or disable PG privilege dropping.
        proof_base = Path(os.environ['RUNNER_TEMP']) / ('pal-native-' + uuid.uuid4().hex)
        files.private_directory(proof_base, create=True)
    else:
        proof_base = tmp_path
    root=proof_base/'Project With Spaces'
    root.mkdir()
    (root/'pyproject.toml').write_text('[project]\nname="polymarket-alpha-lab"\n')
    shutil.copytree(ROOT/'database',root/'database')
    shutil.copytree(ROOT/'supabase/migrations',root/'supabase/migrations')
    with socket.socket() as s:
        s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    # Test-only diagnostics for the fresh synthetic cluster. Never log argv,
    # stdin, passwords, existing system databases or the production error path.
    from polymarket_alpha_lab.project_postgres import files
    original_run = files.subprocess.run
    def diagnostic_run(args, **kwargs):
        result = original_run(args, **kwargs)
        if Path(args[0]).stem in ('initdb', 'pg_ctl', 'psql') and result.returncode:
            def safe(value):
                value = re.sub(r'[a-fA-F0-9]{64}', '<redacted>', value)
                return value.replace(str(root), '<temporary-project>').replace(root.as_posix(), '<temporary-project>')[-4000:]
            print(json.dumps({'native_program': Path(args[0]).stem, 'exit_code': result.returncode,
                'stdout': safe(result.stdout), 'stderr': safe(result.stderr)}))
        return result
    monkeypatch.setattr(files.subprocess, 'run', diagnostic_run)
    print('native proof: copy binaries only, never reuse installed data')
    version=import_runtime_directory(root,prefix)
    db=ProjectPostgres(root)
    print('native proof: initialize private cluster and all 62 migrations')
    result=db.initialize(port=port)
    assert result==dict(status='initialized',version=version,migrations_applied=62)
    assert db.status()['status']=='stopped'
    with pytest.raises(ProjectDatabaseError,match='existing_data'):db.initialize(port=port)
    assert not (db.layout.home/'initial-password').exists()
    info=db._state()
    print('native proof: roles, isolation and persistent capture')
    req=request(0);created=[]
    def factory(_):
        model=Model();created.append(model);return model
    try:
        with db.session() as session:
            with pytest.raises(ProjectDatabaseError,match='busy'):db.down()
            captured=session.run_research(request=req,model_factory=factory)
            assert captured.status=='captured' and captured.record.run.research.status=='completed'
            assert len(created)==1
            repeat=session.run_research(request=req,model_factory=factory)
            assert repeat.record==captured.record and len(created)==1
            report=session.evaluate()
            assert len(report.records)==1 and report.groups[0].outcome_pending_count==1
            role=json.loads(db._psql(info,"SELECT json_build_array(rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls) "
                "FROM pg_roles WHERE rolname=current_user;",owner=False))
            assert role==[False]*5
            # This legacy table has RLS enabled. App INSERT and SELECT must both
            # work via explicit app-only policies, without giving it BYPASSRLS.
            from polymarket_alpha_lab.project_postgres.sql import literal
            fixture = dict(generated_at='2026-01-01T00:00:00+00:00', config_version='native',
                source_queue_config_version='native', source_route_config_version='native',
                source_memory_config_version='native', assignment_status='blocked',
                assignment_count=0, assigned_count=0, watch_count=0, blocked_count=0,
                reason_codes=[], paper_only=True, report_only=True, readonly=True)
            db._psql(info, "INSERT INTO public.team_research_assignment_reports "
                "(report_sha256,generated_at,config_version,source_queue_config_version,"
                "source_route_config_version,source_memory_config_version,assignment_status,"
                "assignment_count,assigned_count,watch_count,blocked_count,payload_json) VALUES ("
                "repeat('a',64),'2026-01-01T00:00:00+00:00','native','native','native','native',"
                "'blocked',0,0,0,0," + literal(json.dumps(fixture)) + "::jsonb);", owner=False)
            assert db._psql(info, 'SELECT count(*) FROM public.team_research_assignment_reports;', owner=False)=='1'
            for denied in ('CREATE DATABASE unwanted;',
                "UPDATE project_private.instance SET root_sha256='wrong';",
                'DELETE FROM research_capture.attempts;', 'SELECT * FROM pg_authid;'):
                with pytest.raises(ProjectDatabaseError):db._psql(info,denied,owner=False)
            with pytest.raises(ProjectDatabaseError):db._psql(info,'SELECT 1;',database='postgres',owner=False)
            reqs=[request(i) for i in range(1,5)]
            with ThreadPoolExecutor(max_workers=4) as pool:
                results=tuple(pool.map(lambda r:session.run_research(request=r,model_factory=factory),reqs))
            assert all(r.status=='captured' for r in results) and len(created)==5
        assert db.status()['status']=='stopped'
        with pytest.raises(ProjectDatabaseError,match='session_closed'):session.inspect(record_id=req.record_id)
        with db.session() as session:
            assert session.inspect(record_id=req.record_id).record==captured.record
            assert len(session.evaluate().records)==5
        print('native proof: explicit up is not stopped by a borrowing session')
        assert db.up()['status']=='running'
        assert db.up()['started_here'] is False
        with db.session() as session:assert len(session.evaluate().records)==5
        assert db.status()['status']=='running'
        assert db.migrate()['migrations_applied']==0
        with db.session() as session:
            db._psql(info,"UPDATE project_private.instance SET instance_id='wrong';")
            try:
                with pytest.raises(RuntimeError):session.evaluate()
            finally:db._psql(info,"UPDATE project_private.instance SET instance_id='"+info['instance_id']+"';")
        db.down()
        print('native proof: occupied port never triggers adoption or reset')
        with socket.socket() as s:
            s.bind(('127.0.0.1',port));s.listen()
            with pytest.raises(ProjectDatabaseError,match='port_in_use'):db.up()
        conf=db.layout.cluster/'postgresql.conf';original=conf.read_bytes()
        conf.write_bytes(original+b"\nlisten_addresses='*'\n")
        try:
            with pytest.raises(ProjectDatabaseError,match='configuration_changed'):db.up()
        finally:conf.write_bytes(original)
        print('native proof: migration DDL and receipt roll back atomically')
        path=root/'supabase/migrations/20990101000000_failure_probe.sql'
        text='CREATE TABLE public.must_rollback(x int); SELECT missing_function();\n'
        path.write_bytes(text.encode())
        manifest=root/'database/migrations.lock.json';old=manifest.read_bytes()
        data=json.loads(old);data['migrations'].append(dict(name=path.name,
            sha256=sha256(text.encode()).hexdigest(),transaction_wrapper=False))
        manifest.write_text(json.dumps(data))
        try:
            assert db.up()['status']=='migrations_pending'
            with pytest.raises(ProjectDatabaseError):db.migrate()
            assert db._psql(info,"SELECT to_regclass('public.must_rollback') IS NULL;")=='t'
            assert db._psql(info,'SELECT count(*) FROM project_private.migrations;')=='62'
        finally:path.unlink();manifest.write_bytes(old)
        with db.session() as session:assert len(session.evaluate().records)==5
    finally:db.down()
    assert db.status()['status']=='stopped'
    print('native proof: PASS; data retained, no public models or Docker used')
