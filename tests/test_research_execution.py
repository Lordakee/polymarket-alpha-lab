"""Pure request/result contracts and the real model/tool loop, no DB/network."""
from dataclasses import asdict, replace
from datetime import timedelta, timezone
from decimal import Decimal
import json

import pytest

from polymarket_alpha_lab.research_capture_codec import payload_sha256
from polymarket_alpha_lab.research_execution import (
    CapturedResearchExecution, CapturedResearchRequest, bind_execution_run,
    copy_request, decode_execution_request,
)
from polymarket_alpha_lab import research_execution_psycopg as runner
from polymarket_alpha_lab.team_research_agent_types import ResearchAgentLimits, ResearchModelReply, ResearchToolCall
from polymarket_alpha_lab.team_research_evaluation import ResearchEvaluationRecord
from tests.test_research_capture_codec import NOW, make_run
from polymarket_alpha_lab.team_taxonomy import TEAM_IDS


def request(**changes):
    values = dict(record_id="r1", model_id="synthetic-model", protocol_version="v1",
                  forecast_cutoff_at=NOW+timedelta(hours=1), intake=make_run().intake)
    values.update(changes)
    return CapturedResearchRequest(**values)


def state(req=None):
    return CapturedResearchExecution(req or request(), NOW+timedelta(seconds=1), "incomplete")


class Model:
    def __init__(self): self.calls = 0
    def complete(self, **kwargs):
        self.calls += 1
        name, args = ("read_evidence", {"source_id":"s"}) if self.calls == 1 else (
            "finish_research", dict(probability_yes="0.7", confidence="0.2", summary="Synthetic result", source_ids=["s"]))
        return ResearchModelReply((ResearchToolCall(f"c{self.calls}", name, json.dumps(args)),), 2)


def record_for(req, run):
    return ResearchEvaluationRecord(req.record_id, req.model_id, req.protocol_version,
                                    NOW+timedelta(seconds=2), run)


@pytest.mark.parametrize("team", TEAM_IDS)
@pytest.mark.parametrize("status", ("completed", "failed", "intake_blocked"))
def test_request_roundtrip_all_teams_and_regular_capture_statuses(team, status):
    run = make_run(team=team, status=status)
    req = request(intake=run.intake)
    original = req.payload
    copy = decode_execution_request(original, req.content_sha256)
    assert copy == req and copy is not req and copy.intake is not req.intake
    assert copy.intake == run.intake
    assert bind_execution_run(copy, run) == run
    execution = CapturedResearchExecution(copy, NOW+timedelta(seconds=1), "captured", record_for(copy, run))
    assert execution.to_dict()["status"] == "captured"
    assert "SYNTHETIC-PRIVATE" not in repr(execution)
    assert "SYNTHETIC-PRIVATE" not in json.dumps(execution.to_dict())


@pytest.mark.parametrize("changes", (
    {"record_id":"bad id"}, {"model_id":""}, {"protocol_version":"x/y"},
    {"forecast_cutoff_at":NOW}, {"forecast_cutoff_at":NOW.replace(tzinfo=None)},
    {"required_source_ids":[]}, {"required_source_ids":("missing",)}, {"required_source_ids":("s","s")},
    {"required_source_ids":(True,)}, {"max_start_delay_seconds":0}, {"max_start_delay_seconds":True},
    {"max_start_delay_seconds":3601}, {"paper_only":False}, {"report_only":1}, {"readonly":False},
    {"intake":object()}, {"limits":object()},
))
def test_invalid_request(changes):
    with pytest.raises(ValueError): request(**changes)


@pytest.mark.parametrize("defect", ("version","unknown","missing","limits_missing","limits_unknown","flag","hash","duplicate","bad_time"))
def test_decoder_rejects_noncanonical_and_corrupt_requests(defect):
    req = request()
    data = json.loads(req.payload)
    if defect == "version": data["schema_version"] = "other"
    elif defect == "unknown": data["extra"] = "forbidden"
    elif defect == "missing": del data["model_id"]
    elif defect == "limits_missing": del data["limits"]["max_model_calls"]
    elif defect == "limits_unknown": data["limits"]["extra"] = True
    elif defect == "flag": data["intake"]["task"]["evidence"][0]["readonly"] = False
    elif defect == "bad_time": data["forecast_cutoff_at"] = "2026-09-12"
    body = json.dumps(data, sort_keys=True, separators=(",",":"))
    if defect == "duplicate": body = '{"record_id":"duplicate",'+body[1:]
    with pytest.raises(ValueError, match="invalid stored"):
        decode_execution_request(body, "0"*64 if defect == "hash" else payload_sha256(body))


@pytest.mark.parametrize("field", ("record_id","model_id","protocol_version","forecast_cutoff_at","limits","max_start_delay_seconds","required_source_ids"))
def test_request_digest_binds_execution_parameters(field):
    req = request()
    changes = dict(record_id="r2", model_id="other", protocol_version="v2", forecast_cutoff_at=NOW+timedelta(hours=2),
                   limits=ResearchAgentLimits(max_model_calls=5), max_start_delay_seconds=30, required_source_ids=("s",))
    assert replace(req, **{field:changes[field]}).content_sha256 != req.content_sha256


def test_request_copies_nested_inputs_and_normalizes_timezone():
    original = make_run().intake
    req = request(intake=original)
    utc_hash = req.content_sha256
    assert req.intake.task.evidence[0] is not original.task.evidence[0]
    object.__setattr__(original.task.evidence[0], "text", "changed")
    assert req.content_sha256 == utc_hash
    assert replace(req, forecast_cutoff_at=req.forecast_cutoff_at.astimezone(timezone(timedelta(hours=8)))).content_sha256 == utc_hash
    object.__setattr__(req.intake.task.evidence[0], "readonly", False)
    with pytest.raises(ValueError): copy_request(req)


def test_bound_result_cannot_substitute_intake_or_required_sources():
    req = request()
    with pytest.raises(ValueError): bind_execution_run(req, make_run(condition="other"))
    # Structurally valid alternate evidence with same source label changes its receipt.
    run = make_run(now=NOW-timedelta(seconds=1))
    with pytest.raises(ValueError): bind_execution_run(req, run)


@pytest.mark.parametrize("changes", (
    {"status":"success"}, {"claimed_at":NOW-timedelta(seconds=1)}, {"claimed_at":NOW+timedelta(hours=1)},
    {"claimed_at":NOW+timedelta(seconds=301)}, {"status":"captured"},
    {"status":"capture_failed"}, {"readonly":False}, {"record":object()},
    {"pending_run":make_run()},
))
def test_invalid_execution_receipts(changes):
    with pytest.raises((ValueError,AttributeError)): replace(state(), **changes)


def test_new_claim_executes_actual_loop_then_captures(monkeypatch):
    req = request(required_source_ids=("s",))
    events=[]; model=Model()
    def claim(dsn,r): events.append("committed-claim");return True,state(r)
    def factory(team): events.append("factory");return model
    def capture(dsn,**kwargs): events.append("capture");return record_for(req,kwargs["run"])
    monkeypatch.setattr(runner,"_claim",claim)
    monkeypatch.setattr(runner.db,"capture_research_with_psycopg",capture)
    result=runner.run_captured_research_with_psycopg("not-used",request=req,model_factory=factory)
    assert events==["committed-claim","factory","capture"] and model.calls==2
    assert result.status=="captured" and result.record.run.research.probability_yes==Decimal("0.7")


@pytest.mark.parametrize("status", ("incomplete","already_captured"))
def test_repeat_never_constructs_model_or_recaptures(monkeypatch,status):
    req=request(); current=state(req)
    if status=="already_captured":current=replace(current,status=status,record=record_for(req,make_run()))
    monkeypatch.setattr(runner,"_claim",lambda *args:(False,current))
    def forbidden(*args,**kwargs):pytest.fail("repeat must not execute")
    monkeypatch.setattr(runner.db,"capture_research_with_psycopg",forbidden)
    assert runner.run_captured_research_with_psycopg("unused",request=req,model_factory=forbidden)==current


@pytest.mark.parametrize("mode", ("factory_raise","factory_invalid","model_raise","intake_blocked"))
def test_unsuccessful_attempts_are_captured(monkeypatch,mode):
    req=request(intake=make_run(status="intake_blocked" if mode=="intake_blocked" else "completed").intake)
    monkeypatch.setattr(runner,"_claim",lambda *args:(True,state(req)))
    captured=[]; calls=[]
    def capture(dsn,**kw):captured.append(kw["run"]);return record_for(req,kw["run"])
    monkeypatch.setattr(runner.db,"capture_research_with_psycopg",capture)
    class FailModel:
        def complete(self,**kw):raise RuntimeError("SYNTHETIC-PRIVATE")
    def factory(team):
        calls.append(team)
        if mode=="factory_raise":raise RuntimeError("SYNTHETIC-PRIVATE")
        return object() if mode=="factory_invalid" else FailModel()
    result=runner.run_captured_research_with_psycopg("unused",request=req,model_factory=factory)
    assert result.status=="captured" and len(captured)==1
    if mode=="intake_blocked":assert captured[0].research is None and calls==[]
    else: assert captured[0].research.status=="failed" and captured[0].research.summary==""


def test_unexpected_execution_failure_remains_incomplete_not_fake_success(monkeypatch):
    req=request()
    monkeypatch.setattr(runner,"_claim",lambda *args:(True,state(req)))
    def fail(*args):raise RuntimeError("SYNTHETIC-PRIVATE")
    monkeypatch.setattr(runner,"_execute",fail)
    result=runner.run_captured_research_with_psycopg("unused",request=req,model_factory=lambda _:Model())
    assert result.status=="incomplete" and result.record is result.pending_run is None
    assert "SYNTHETIC-PRIVATE" not in repr(result)


def test_capture_failure_retains_original_result_and_capture_only_retry(monkeypatch):
    req=request();model=Model()
    monkeypatch.setattr(runner,"_claim",lambda *args:(True,state(req)))
    def fail(*args,**kwargs):raise RuntimeError("SYNTHETIC-PRIVATE-DB")
    monkeypatch.setattr(runner.db,"capture_research_with_psycopg",fail)
    result=runner.run_captured_research_with_psycopg("unused",request=req,model_factory=lambda _:model)
    assert result.status=="capture_failed" and result.record is None and model.calls==2
    monkeypatch.setattr(runner,"inspect_captured_research_with_psycopg",lambda *args,**kw:state(req))
    monkeypatch.setattr(runner.db,"capture_research_with_psycopg",lambda dsn,**kw:record_for(req,kw["run"]))
    saved=runner.retry_research_capture_with_psycopg("unused",request=result.request,run=result.pending_run)
    assert saved.status=="captured" and saved.record.run==result.pending_run and model.calls==2
    assert "SYNTHETIC-PRIVATE" not in repr(result)


def test_capture_only_retry_detects_changed_request_and_changed_output(monkeypatch):
    req=request();run=make_run();saved=replace(state(req),status="already_captured",record=record_for(req,run))
    monkeypatch.setattr(runner,"inspect_captured_research_with_psycopg",lambda *args,**kw:saved)
    assert runner.retry_research_capture_with_psycopg("unused",request=req,run=run)==saved
    with pytest.raises(runner.db.ResearchCaptureConflict):
        runner.retry_research_capture_with_psycopg("unused",request=replace(req,model_id="different"),run=run)
    changed=replace(run,research=replace(run.research,probability_yes=Decimal("0.1")))
    with pytest.raises(runner.db.ResearchCaptureConflict):
        runner.retry_research_capture_with_psycopg("unused",request=req,run=changed)


def test_coverage_reader_cannot_disable_incomplete_guard(monkeypatch):
    observed=[]
    monkeypatch.setattr(runner.db,"load_research_evaluation_with_psycopg",lambda dsn,**kw:observed.append(kw))
    runner.load_captured_research_evaluation_with_psycopg("unused",max_records=20)
    assert observed[0]["require_execution_complete"] is True and observed[0]["max_records"]==20


@pytest.mark.parametrize("citation_mode",("both","one","unread"))
def test_real_loop_preserves_two_required_sources(citation_mode):
    from polymarket_alpha_lab.team_research_intake import ResearchSourceReceipt,evidence_content_sha256
    base=make_run().intake
    second=replace(base.task.evidence[0],source_id="s2",text="Second approved source.")
    intake=replace(base,task=replace(base.task,evidence=(*base.task.evidence,second)),
        source_receipts=(*base.source_receipts,ResearchSourceReceipt("s2",evidence_content_sha256(second),second.reference,second.observed_at)))
    req=request(intake=intake,required_source_ids=("s2","s"))
    assert req.required_source_ids==("s","s2")
    class TwoSourceModel:
        calls=0
        def complete(self,**kw):
            self.calls+=1
            if self.calls<=2 and not (citation_mode=="unread" and self.calls==2):
                name,args="read_evidence",{"source_id":"s" if self.calls==1 else "s2"}
            else:
                name,args="finish_research",dict(probability_yes="0.6",confidence="0.3",summary="Synthetic.",
                    source_ids=["s"] if citation_mode=="one" else ["s","s2"])
            return ResearchModelReply((ResearchToolCall(f"c{self.calls}",name,json.dumps(args)),),2)
    run=runner._execute(req,lambda _:TwoSourceModel())
    assert run.research.status==("completed" if citation_mode=="both" else "blocked")
    if citation_mode!="both":assert run.research.probability_yes is None
