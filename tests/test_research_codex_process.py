"""Actual synthetic processes connected to original decoder/claim audit contract."""
from dataclasses import replace
import json
import sys
import traceback

import pytest

from polymarket_alpha_lab import research_codex_process as transport
from polymarket_alpha_lab.research_codex_exec import CodexExecInput, CodexExecModel
from polymarket_alpha_lab.research_process import ResearchProcessSpec
from tests.test_research_process import executable, spec
from tests.test_research_codex_exec import output, events, action
from tests.test_research_uncapped_audit import AuditHarness, req, run


def host(executable,tmp_path,wire,seen,**kw):
    def prepare(request):
        seen.append(request)
        # Synthetic process validates the exact prompt before returning events.
        code=('import sys,json;data=sys.stdin.buffer.read();value=json.loads(data);'
              'assert value["schema_version"]=="research-codex-actions-v1";'
              f'sys.stdout.buffer.write({wire!r})')
        return spec(executable,tmp_path,code,**kw)
    return transport.CodexProcessTransport(prepare_command=prepare,allow_process_start=True)


def test_concrete_process_and_strict_original_decoder(executable,tmp_path):
    seen=[]
    client=CodexExecModel(model_id='synthetic-model',transport=host(executable,tmp_path,output().stdout,seen))
    messages='[{"role":"user","content":"中文 😀","measurement":0.125}]'
    reply=client.complete(messages_json=messages,max_output_tokens=120)
    assert reply.calls[0].name=='search_evidence' and reply.total_tokens==120
    assert len(seen)==1 and seen[0].messages_json==messages and seen[0].max_output_tokens==120
    assert seen[0].model_id=='synthetic-model'
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('wire',[b'bad-json',output(events([action('shell')])).stdout,output(events(output_tokens=201)).stdout])
def test_invalid_process_reply_closes_model_without_second_process(executable,tmp_path,wire):
    seen=[]
    client=CodexExecModel(model_id='synthetic-model',transport=host(executable,tmp_path,wire,seen))
    with pytest.raises(ValueError):client.complete(messages_json='[{}]',max_output_tokens=200)
    with pytest.raises(ValueError,match='stopped'):client.complete(messages_json='[{}]',max_output_tokens=200)
    assert len(seen)==1


def test_transport_timeout_redacts_and_permanently_stops(executable,tmp_path):
    seen=[]
    def prepare(request):
        seen.append(request)
        return spec(executable,tmp_path,'import sys,time;sys.stderr.write("PRIVATE-SENTINEL");time.sleep(10)',timeout_ms=500)
    client=transport.CodexProcessTransport(prepare_command=prepare,allow_process_start=True)
    request=CodexExecInput('model','[{}]',100)
    with pytest.raises(ValueError,match='process_failed') as error:client.run(request)
    assert 'PRIVATE-SENTINEL' not in ''.join(traceback.format_exception(error.value))
    with pytest.raises(ValueError,match='stopped'):client.run(request)
    assert len(seen)==1


@pytest.mark.parametrize('number',[0,1])
def test_audited_two_step_real_process_research_and_inert_replay(monkeypatch,executable,tmp_path,number):
    h=AuditHarness(monkeypatch);r=req(number);seen=[]
    source=r.intake.task.evidence[0].source_id
    def factory(team):
        assert team==r.intake.team_id
        def prepare(request):
            h.events.append('process_launch')
            seen.append(request)
            assert h.events[-2]=='start_commit'
            call=action('read_evidence',{'source_id':source}) if len(seen)==1 else action('finish_research',dict(
                probability_yes='0.6',confidence='0.5',summary='Synthetic process evidence',source_ids=[source]))
            wire=output(events([call])).stdout
            return spec(executable,tmp_path,'import sys;sys.stdin.buffer.read();sys.stdout.buffer.write('+repr(wire)+')')
        return CodexExecModel(model_id=r.model_id,transport=transport.CodexProcessTransport(
            prepare_command=prepare,allow_process_start=True))
    result=run(h,request=r,model_factory=factory,require_durable_audit=True)
    assert result.record.run.research.status=='completed'
    assert result.record.run.research.total_tokens==240
    assert len(h.starts)==len(h.outcomes)==len(seen)==2
    assert all(o.status=='returned' and o.reported_total_tokens==120 for o in h.outcomes)
    original_hash=r.content_sha256
    h.events.clear()
    assert run(h,request=r,model_factory=lambda _:pytest.fail('replay client'),require_durable_audit=True)==result
    assert h.events==['authorization','replay'] and r.content_sha256==original_hash


@pytest.mark.parametrize('failure',['start_ack','process_error','terminal_ack'])
def test_process_boundary_keeps_original_audit_uncertainty(monkeypatch,executable,tmp_path,failure):
    h=AuditHarness(monkeypatch);seen=[]
    if failure=='start_ack':h.begin_error=RuntimeError('lost start ack')
    if failure=='terminal_ack':h.finish_error=RuntimeError('lost terminal ack')
    wire=output().stdout if failure!='process_error' else b'invalid'
    def factory(team):
        return CodexExecModel(model_id=req().model_id,transport=host(executable,tmp_path,wire,seen))
    result=run(h,model_factory=factory,require_durable_audit=True)
    assert result.record.run.research.status=='failed'
    assert len(seen)==(0 if failure=='start_ack' else 1)
    if failure=='process_error':
        assert h.outcomes[0].status=='failed' and h.outcomes[0].reported_total_tokens is None
    if failure=='terminal_ack':
        assert len(h.starts)==1 and not h.outcomes
        assert h.events.count('outcome_returned')==1 and 'outcome_failed' not in h.events


@pytest.mark.parametrize('allow',[False,None,1,'yes'])
def test_inert_constructor_requires_explicit_permission(allow):
    with pytest.raises(ValueError):transport.CodexProcessTransport(prepare_command=lambda _:None,allow_process_start=allow)


def test_mutated_builder_input_cannot_change_prompt(monkeypatch,executable,tmp_path):
    original=CodexExecInput('model','[{"content":"original"}]',100)
    def prepare(request):
        object.__setattr__(request,'messages_json','[{"content":"changed"}]')
        return spec(executable,tmp_path)
    raw=transport.CodexProcessTransport(prepare_command=prepare,allow_process_start=True).run(original)
    assert json.loads(raw.stdout)['messages_json']=='[{"content":"original"}]'
    assert original.messages_json=='[{"content":"original"}]'
