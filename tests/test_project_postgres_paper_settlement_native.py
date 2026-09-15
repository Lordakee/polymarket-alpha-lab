"""Real one-snapshot paper settlement; synthetic forecasts/sources, no live calls."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
from threading import Event
import time
import uuid

import pytest

from polymarket_alpha_lab import research_paper_settlement as core
from polymarket_alpha_lab.project_postgres import files
from polymarket_alpha_lab.project_postgres.runtime import import_runtime_directory
from polymarket_alpha_lab.project_postgres.server import ProjectPostgres
from polymarket_alpha_lab.research_resolution import IndependentResolutionConfirmation, ResolutionSubmission
from polymarket_alpha_lab.research_resolution_confirmation import CryptoSettlementReview
from polymarket_alpha_lab.research_resolution_codec import encode_resolution
from polymarket_alpha_lab.team_research_agent_types import ResearchModelReply, ResearchToolCall
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot
from tests.test_research_resolution_confirmation import request
from tests.test_research_paper_capture import scenario, inputs

ROOT=Path(__file__).resolve().parents[1]
ENABLED=os.environ.get('POLYMARKET_ALPHA_LAB_RUN_NATIVE_PROJECT_POSTGRES')=='1'


class Model:
    def __init__(self,p):self.p=p;self.calls=0
    def complete(self,**kw):
        self.calls+=1
        if self.calls==1:name,args='read_evidence',dict(source_id='source')
        else:name,args='finish_research',dict(probability_yes=self.p,confidence='0.9',source_ids=['source'],summary='Synthetic')
        return ResearchModelReply((ResearchToolCall(str(self.calls),name,json.dumps(args)),),1)


@pytest.mark.skipif(not ENABLED,reason='explicit native settled-paper proof is opt-in')
def test_paper_settlement_snapshot_outcomes_denominators_restart_and_no_writes(tmp_path,monkeypatch):
    prefix=Path(os.environ['POLYMARKET_ALPHA_LAB_NATIVE_PG_PREFIX'])
    for key in tuple(os.environ):
        if key.upper().startswith('PG'):monkeypatch.delenv(key)
    parent=tmp_path
    if os.name=='nt':
        parent=Path(os.environ['RUNNER_TEMP'])/('pal-settled-'+uuid.uuid4().hex)
        files.private_directory(parent,create=True)
    root=parent/'Settled Paper With Spaces';root.mkdir()
    (root/'pyproject.toml').write_text('[project]\nname="polymarket-alpha-lab"\n')
    shutil.copytree(ROOT/'database',root/'database')
    shutil.copytree(ROOT/'supabase/migrations',root/'supabase/migrations')
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    import_runtime_directory(root,prefix);db=ProjectPostgres(root)
    try:
        assert db.initialize(port=port)['migrations_applied']==67
        with db.session() as s:
            identity=db._state();now=datetime.now(UTC)
            opening=now.replace(second=0,microsecond=0)+timedelta(minutes=2)
            cases=[];saved={}
            for n in range(1,10):
                team='crypto_btc' if n%2 else 'crypto_eth'
                req,raw=request(team,at=datetime.now(UTC),opening=opening,
                    cid='0x'+format(7000+n,'064x'),record_id='settled-'+str(n))
                raw.update(acceptingOrders=True,enableOrderBook=True,orderMinSize='1',
                           orderPriceMinTickSize='0.001',clobTokenIds=['101','102'])
                def fail(_):raise RuntimeError('synthetic failure')
                p='0.1' if n in (3,4) else '0.7'
                e=s.run_research(request=req,model_factory=fail if n==5 else lambda _,p=p:Model(p))
                value=scenario(e,raw,at=datetime.now(UTC))
                if n==7:value=replace(value,yes_book=replace(value.yes_book,raw_json=b'{synthetic malformed'))
                if n not in (6,8):
                    saved[req.record_id]=s.capture_paper_research(scenario=value,allow_paper_write=True)
                cases.append((req,raw,e,value))
            # INSERT a paper receipt before reader cutoff but delay its COMMIT.
            # Release COMMIT after the history read and before paper-table reads:
            # ONLY sharing the snapshot prevents this row leaking into the view.
            inserted,release,committed=Event(),Event(),Event()
            original_tx=core.db._local_transaction
            original_history=core.db._read_research_evaluation
            def delayed_tx(dsn,operation,**kw):
                if kw.get('readonly',False):return original_tx(dsn,operation,**kw)
                def delayed(cursor):
                    result=operation(cursor);inserted.set()
                    assert release.wait(30)
                    return result
                return original_tx(dsn,delayed,**kw)
            def snapshot_history(cursor,**kw):
                cursor.execute("SELECT current_setting('transaction_isolation'),current_setting('transaction_read_only')")
                assert cursor.fetchone()==('repeatable read','on')
                result=original_history(cursor,**kw)
                release.set();assert committed.wait(30)
                return result
            def writer():
                try:return s.capture_paper_research(scenario=cases[7][3],allow_paper_write=True)
                finally:committed.set()
            with monkeypatch.context() as patch,ThreadPoolExecutor(max_workers=1) as pool:
                patch.setattr(core.db,'_local_transaction',delayed_tx)
                future=pool.submit(writer)
                try:
                    assert inserted.wait(30)
                    patch.setattr(core.db,'_read_research_evaluation',snapshot_history)
                    old_view=s.evaluate_settled_paper_research()
                finally:release.set()
                late=future.result(timeout=30)
            saved[late.scenario.record_id]=late
            assert late.recorded_at <= datetime.fromisoformat(old_view['history']['generated_at'])
            assert next(r for r in old_view['attempts'] if r['record_id']==late.scenario.record_id)['status']=='paper_evidence_missing'
            before=s.evaluate_settled_paper_research()
            assert before['paper_evidence_count']==8 and before['attempt_count']==9
            assert before['status_counts']['settled_simulation']==0
            assert all(g['settled_pnl_lower_bound_sum'] is None for g in before['groups'])
            before_at=datetime.fromisoformat(before['history']['generated_at'])
            # Real UTC minute close, no patched clock or backdated forecasts.
            time.sleep(max(0,(opening+timedelta(minutes=1)-datetime.now(UTC)).total_seconds())+0.05)
            actuals=(True,False,False,True)
            for (req,raw,e,value),actual in zip(cases[:4],actuals,strict=True):
                closed=dict(raw,closed=True,acceptingOrders=False,umaResolutionStatus='resolved',
                            outcomePrices=['1','0'] if actual else ['0','1'])
                now=datetime.now(UTC)
                candidate=s.record_resolution(submission=ResolutionSubmission('candidate-'+req.record_id,
                    req.intake.condition_id,GammaMarketSnapshot(req.intake.market_slug,now,json.dumps(closed).encode()),now))
                proof=IndependentResolutionConfirmation(req.intake.condition_id,req.intake.market_slug,actual,
                    opening+timedelta(minutes=1),datetime.now(UTC),candidate.submission.snapshot.content_sha256,
                    'synthetic-reviewer','https://data.binance.vision/synthetic-native-settlement',
                    'Synthetic evidence only; not actual market data.',independently_verified=True)
                instruction=CryptoSettlementReview('confirmed-'+req.record_id,req.record_id,req.content_sha256,
                    candidate.submission.review_id,core.checksum(encode_resolution(candidate.submission)),proof,
                    'binance','BTCUSDT' if req.intake.team_id=='crypto_btc' else 'ETHUSDT','1m','close',opening)
                s.confirm_crypto_resolution(instruction=instruction,allow_resolution_write=True)
            # Existing generic outcome is retained, but is not certified as a
            # crypto-workflow confirmation by the settlement adapter.
            req=cases[8][0]
            s.capture_outcome(condition_id=req.intake.condition_id,market_slug=req.intake.market_slug,
                resolved_at=opening+timedelta(minutes=1),actual_yes=True,
                source_reference='fixture:legacy-direct-outcome',source_content_sha256='a'*64)
            counts_sql=('SELECT json_build_array((SELECT count(*) FROM research_capture.attempts),'
                '(SELECT count(*) FROM research_capture.paper_simulations),'
                '(SELECT count(*) FROM research_capture.resolution_reviews),'
                '(SELECT count(*) FROM research_capture.outcomes));')
            counts=db._psql(identity,counts_sql)
            after=s.evaluate_settled_paper_research()
            assert after['history']==s.evaluate(generated_at=datetime.fromisoformat(after['history']['generated_at'])).to_dict()
            assert after['status_counts']==dict(paper_evidence_missing=1,research_not_selected=1,
                paper_not_selected=1,outcome_pending=1,crypto_confirmation_required=1,settled_simulation=4)
            for n,expected in enumerate(('2.971','-2.029','1.971','-3.029'),1):
                row=next(r for r in after['attempts'] if r['record_id']=='settled-'+str(n))
                assert Decimal(row['amounts']['settled_pnl_lower_bound'])==Decimal(expected)
            assert after['actual_account_pnl'] is None and after['business_writes_performed'] is False
            assert s.evaluate_settled_paper_research(generated_at=before_at)==before
            assert db._psql(identity,counts_sql)==counts
            for req,raw,e,value in cases:
                assert s.inspect(record_id=req.record_id).record==e.record
            for rid,receipt in saved.items():assert s.inspect_paper_research(record_id=rid)==receipt
        db.down()
        # Real operator children must run OUTSIDE the parent's lifecycle lease.
        # Compare directly with the original API export, not the CLI presenter.
        def console(*args, expected_code=0):
            child=subprocess.run([sys.executable,'-I',str(ROOT/'scripts/evaluate_project_research.py'),
                '--root',str(root),'--settled-paper',*args],cwd=parent,
                capture_output=True,text=True,encoding='utf-8',env=files.clean_environment(),timeout=120)
            assert child.returncode==expected_code,(child.stdout,child.stderr)
            assert child.stderr=='' and 'Synthetic evidence only' not in child.stdout
            assert 'data.binance.vision' not in child.stdout
            return json.loads(child.stdout)
        for detail in (False,True):
            value=console('--as-of',after['history']['generated_at'],
                          *(['--include-decisions'] if detail else []))
            expected=json.loads(json.dumps(after))
            if not detail:
                expected.pop('attempts');expected['history'].pop('decisions')
            expected['decisions_included']=detail
            assert value['evaluation']==expected
            assert value['evaluation_kind']=='settled_paper' and value['business_writes_performed'] is False
        historical=console('--as-of',before_at.isoformat(),'--include-decisions')['evaluation']
        assert historical==dict(before,decisions_included=True)
        for args,reason in ((['--max-records','8'],'research_capture_history_limit'),
                (['--as-of',(datetime.now(UTC)+timedelta(days=1)).isoformat()],'research_evaluation_from_future')):
            failure=console(*args,expected_code=1)
            assert failure['status']=='blocked' and failure['reason_code']==reason and failure['evaluation'] is None
        assert db.status()['status']=='stopped'
        with db.session() as s:
            assert db._psql(identity,counts_sql)==counts
            assert s.evaluate_settled_paper_research(generated_at=datetime.fromisoformat(after['history']['generated_at']))==after
            req,_=inputs(7999,at=datetime.now(UTC))
            def interrupted(_):raise SystemExit(86)
            with pytest.raises(SystemExit):s.run_research(request=req,model_factory=interrupted)
            with pytest.raises(core.db.ResearchCaptureConflict,match='history_incomplete'):
                s.evaluate_settled_paper_research()
            # A historical view predating that claim remains its original scope.
            assert s.evaluate_settled_paper_research(generated_at=before_at)==before
            assert db._psql(identity,'SELECT count(*) FROM project_private.migrations;')=='67'
        failure=console(expected_code=1)
        assert failure['reason_code']=='research_execution_history_incomplete' and failure['evaluation'] is None
        assert console('--as-of',before_at.isoformat(),'--include-decisions')['evaluation']==dict(before,decisions_included=True)
        assert db.status()['instance_id']==identity['instance_id']
        print('native settled paper: PASS; BTC/ETH four payouts, late-COMMIT snapshot, preserved denominators, historical/restart, no writes')
    finally:
        if db.status()['status']!='stopped':db.down()
