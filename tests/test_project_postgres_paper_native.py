"""Opt-in read-only paper assembly over a fresh private native PostgreSQL.

All inputs/models are synthetic; no public/paid request, user DB or file journal.
"""
from dataclasses import replace
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import shutil
import socket
import uuid

import pytest

from polymarket_alpha_lab.project_postgres import files
from polymarket_alpha_lab.project_postgres.runtime import import_runtime_directory
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres
from polymarket_alpha_lab.research_capture_psycopg import ResearchCaptureConflict
from polymarket_alpha_lab.team_research_agent_types import ResearchModelReply, ResearchToolCall
from tests.test_research_paper import request, scenario

ROOT=Path(__file__).resolve().parents[1]
ENABLED=os.environ.get('POLYMARKET_ALPHA_LAB_RUN_NATIVE_PROJECT_POSTGRES')=='1'


class Model:
    def __init__(self): self.n=0
    def complete(self,**kw):
        self.n+=1
        if self.n==1: name,args='read_evidence',dict(source_id='source')
        else: name,args='finish_research',dict(probability_yes='0.7',confidence='0.9',
                                            source_ids=['source'],summary='synthetic')
        return ResearchModelReply((ResearchToolCall(str(self.n),name,json.dumps(args)),),1)


@pytest.mark.skipif(not ENABLED,reason='explicit native research-to-paper proof is opt-in')
def test_paper_assembly_replays_reads_preserves_failures_and_blocks_incomplete(tmp_path,monkeypatch):
    prefix=Path(os.environ['POLYMARKET_ALPHA_LAB_NATIVE_PG_PREFIX'])
    for key in tuple(os.environ):
        if key.upper().startswith('PG'): monkeypatch.delenv(key)
    parent=tmp_path
    if os.name=='nt':
        parent=Path(os.environ['RUNNER_TEMP'])/('pal-paper-'+uuid.uuid4().hex)
        files.private_directory(parent,create=True)
    root=parent/'Research Paper With Spaces';root.mkdir()
    (root/'pyproject.toml').write_text('[project]\nname="polymarket-alpha-lab"\n')
    shutil.copytree(ROOT/'database',root/'database')
    shutil.copytree(ROOT/'supabase/migrations',root/'supabase/migrations')
    with socket.socket() as sock: sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    import_runtime_directory(root,prefix);db=ProjectPostgres(root)
    try:
        assert db.initialize(port=port)['migrations_applied']==67
        with db.session() as s:
            identity=db._state();original=[];scenarios=[];made=[]
            def factory(team): made.append(team);return Model()
            for n,team in ((3101,'crypto_btc'),(3102,'crypto_eth')):
                req,raw=request(n,team,at=datetime.now(UTC))
                e=s.run_research(request=req,model_factory=factory)
                assert e.record.run.research.status=='completed'
                original.append(e)
                scenarios.append(scenario(e,raw,at=datetime.now(UTC)))
            bad,_=request(3103,at=datetime.now(UTC))
            def fail(_):raise RuntimeError('synthetic model failure')
            failed=s.run_research(request=bad,model_factory=fail)
            at=datetime.now(UTC)
            before=s.evaluate(generated_at=at)
            result=s.evaluate_paper_research(scenarios=tuple(scenarios),generated_at=at).to_dict()
            assert result['history']==before.to_dict()
            assert result['attempt_count']==3 and result['ready_scenario_count']==2
            assert result['paper_trades_created']==0 and result['realized_pnl'] is None
            assert result['paper_attempts'][-1]['original_reason_code']=='research_failed'
            assert len(made)==2
            assert s.evaluate_paper_research(scenarios=tuple(scenarios),generated_at=at).to_dict()==result
            with pytest.raises(ValueError,match='binding_mismatch'):
                s.evaluate_paper_research(scenarios=(replace(scenarios[0],record_sha256='b'*64),))
            for e in (*original,failed): assert s.inspect(record_id=e.request.record_id).record==e.record
        db.down()
        with db.session() as s:
            assert s.evaluate_paper_research(scenarios=tuple(scenarios),generated_at=at).to_dict()==result
            incomplete,_=request(3104,at=datetime.now(UTC))
            def interrupted(_):raise SystemExit(86)
            with pytest.raises(SystemExit):s.run_research(request=incomplete,model_factory=interrupted)
            assert s.inspect(record_id=incomplete.record_id).status=='incomplete'
            with pytest.raises(ResearchCaptureConflict,match='history_incomplete'):
                s.evaluate_paper_research(scenarios=tuple(scenarios))
            assert s.inspect(record_id=incomplete.record_id).status=='incomplete'
            assert db._psql(identity,'SELECT count(*) FROM research_capture.attempts;')=='3'
            assert db._psql(identity,'SELECT count(*) FROM research_capture.execution_claims;')=='4'
            assert db._psql(identity,'SELECT count(*) FROM project_private.migrations;')=='67'
        assert db.status()['instance_id']==identity['instance_id']
        print('native research paper: PASS; BTC/ETH read-only scenarios, failures/denominator, replay/restart, incomplete blocked')
    finally:
        if db.status()['status']!='stopped':db.down()
