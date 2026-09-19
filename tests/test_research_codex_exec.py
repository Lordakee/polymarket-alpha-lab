"""Strict selected-version protocol; never launches a real CLI/provider."""
from dataclasses import replace
import json
import traceback

import pytest

from polymarket_alpha_lab import research_codex_exec as core
from polymarket_alpha_lab import team_research_agent as agent
from tests.test_team_research_agent import task

THREAD='01a0b7b4-3182-72c0-98d3-7f5daa0b7501'


def action(name='search_evidence', arguments=None):
    if arguments is None: arguments={'query':'*'}
    return {'name':name,'arguments_json':json.dumps(arguments,ensure_ascii=False,separators=(',',':'))}


def events(actions=None, **usage):
    actions=[action()] if actions is None else actions
    count=dict(input_tokens=100,cached_input_tokens=10,cache_write_input_tokens=0,output_tokens=20,reasoning_output_tokens=5)
    count.update(usage)
    return [{'type':'thread.started','thread_id':THREAD},{'type':'turn.started'},
            {'type':'item.completed','item':{'id':'item_0','type':'reasoning','text':'PRIVATE-REASONING'}},
            {'type':'item.completed','item':{'id':'item_1','type':'agent_message','text':json.dumps({'calls':actions},ensure_ascii=False)}},
            {'type':'turn.completed','usage':count}]


def output(rows=None, code=0):
    return core.CodexExecOutput(code, ('\n'.join(json.dumps(e,ensure_ascii=False) for e in (events() if rows is None else rows))+'\n').encode())


def decode(rows=None, **kw):
    return core.decode_codex_exec_output(output(rows),call_number=kw.get('call_number',1))


def test_valid_reply_uses_original_actions_and_usage_without_double_counting():
    reply=decode()
    assert reply.total_tokens==120
    assert reply.calls[0].name=='search_evidence' and reply.calls[0].call_id=='codex-1-0'
    assert 'PRIVATE-REASONING' not in repr(reply)
    assert decode(call_number=2).calls[0].call_id=='codex-2-0'


def test_input_preserves_exact_nested_messages_and_model_boundary():
    messages='[{"role":"user","content":"private question","extra":0.125}]'
    request=core.CodexExecInput('synthetic-model',messages,512)
    body=json.loads(request.prompt_json)
    assert body['messages_json']==messages
    assert body['action_definitions']==agent.research_tool_definitions()
    assert request.max_output_tokens==512
    assert 'private question' not in repr(request)
    assert json.loads(request.output_schema_json)['additionalProperties'] is False


@pytest.mark.parametrize('value',['', 'null','{}','[]','[NaN]','[{"x":1,"x":2}]','["\ud800"]'])
def test_invalid_input(value):
    with pytest.raises((ValueError,UnicodeError)): core.CodexExecInput('model',value,10)


@pytest.mark.parametrize('value',[0,True,8193,1.0,None])
def test_invalid_output_ceiling(value):
    with pytest.raises(ValueError): core.CodexExecInput('model','[{}]',value)


@pytest.mark.parametrize('code',[1,2,-1,130])
def test_nonzero_exit_never_validates_success_events(code):
    with pytest.raises(ValueError,match='response_invalid'): core.decode_codex_exec_output(output(code=code),call_number=1)


@pytest.mark.parametrize('raw',[b'',b'\xff',b'{}\n',b'\xef\xbb\xbf{}\n',b'null\n',b'\n',b'{"type":NaN}\n'])
def test_bad_raw_stream_is_redacted(raw):
    with pytest.raises(ValueError,match='response_invalid'): core.decode_codex_exec_output(core.CodexExecOutput(0,raw),call_number=1)


@pytest.mark.parametrize('defect', ['second_thread','second_turn','missing_thread','missing_turn','missing_terminal',
    'duplicate_terminal','trailing','early_terminal','multiple_final','error_event','error_item',
    'unknown_type','tool_event','unfinished','updated_without_start','changed_item_kind','reused_item_id',
    'missing_usage','extra_usage','extra_field','wrong_uuid','empty_calls','too_many_calls','wrong_root',
    'duplicate_action_key','blank_line','lone_surrogate','unknown_action','bad_args','nan_args'])
def test_stream_and_action_counterexamples(defect):
    rows=events()
    if defect=='second_thread': rows.insert(1,rows[0])
    if defect=='second_turn': rows.insert(2,rows[1])
    if defect=='missing_thread': rows.pop(0)
    if defect=='missing_turn': rows.pop(1)
    if defect=='missing_terminal': rows.pop()
    if defect=='duplicate_terminal': rows.append(rows[-1])
    if defect=='trailing': rows.append({'type':'turn.started'})
    if defect=='early_terminal': rows.insert(2,rows.pop())
    if defect=='multiple_final': rows.insert(-1,{'type':'item.completed','item':dict(rows[-2]['item'],id='item_2')})
    if defect=='error_event': rows.insert(2,{'type':'error','message':'PRIVATE-SENTINEL'})
    if defect=='error_item': rows[2]['item']={'id':'item_0','type':'error','message':'PRIVATE-SENTINEL'}
    if defect=='unknown_type': rows[2]['type']='unknown'
    if defect=='tool_event': rows[2]['item']['type']='command_execution'
    if defect=='unfinished': rows[2]['type']='item.started'
    if defect=='updated_without_start': rows[2]['type']='item.updated'
    if defect=='changed_item_kind': rows.insert(2,{'type':'item.started','item':{'id':'item_0','type':'agent_message','text':''}})
    if defect=='reused_item_id': rows[-2]['item']['id']='item_0'
    if defect=='missing_usage': rows[-1]['usage'].pop('output_tokens')
    if defect=='extra_usage': rows[-1]['usage']['unknown']=0
    if defect=='extra_field': rows[0]['extra']='PRIVATE-SENTINEL'
    if defect=='wrong_uuid': rows[0]['thread_id']='not-a-thread'
    if defect=='empty_calls': rows[-2]['item']['text']='{"calls":[]}'
    if defect=='too_many_calls': rows=events([action()]*9)
    if defect=='wrong_root': rows[-2]['item']['text']='[]'
    if defect=='duplicate_action_key': rows[-2]['item']['text']='{"calls":[],"calls":[]}'
    if defect=='lone_surrogate': rows[-2]['item']['text']='\\ud800' # invalid action JSON
    if defect=='unknown_action': rows=events([action('shell')])
    if defect=='bad_args': rows=events([action(arguments={'query':'*','extra':True})])
    if defect=='nan_args': rows=events([dict(name='search_evidence',arguments_json='{"query":NaN}')])
    data=output(rows)
    if defect=='blank_line': data=replace(data,stdout=data.stdout+b'\n')
    with pytest.raises(ValueError,match='response_invalid') as error:
        core.decode_codex_exec_output(data,call_number=1)
    assert 'PRIVATE-SENTINEL' not in ''.join(traceback.format_exception(error.value))


@pytest.mark.parametrize('field',['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens'])
@pytest.mark.parametrize('value',[-1,True,1.0,'1',None,1000001])
def test_usage_strict_integer_bounds(field,value):
    with pytest.raises(ValueError,match='response_invalid'): decode(events(**{field:value}))


@pytest.mark.parametrize('usage',[dict(input_tokens=0,output_tokens=0,cached_input_tokens=0,reasoning_output_tokens=0),
    dict(cached_input_tokens=101),dict(cache_write_input_tokens=101),dict(reasoning_output_tokens=21),
    dict(input_tokens=1000000,output_tokens=1)])
def test_usage_totals_and_subset_accounting(usage):
    with pytest.raises(ValueError,match='response_invalid'): decode(events(**usage))


def test_started_updated_completed_items_valid_and_reasoning_discarded():
    rows=events(); final=rows[-2]['item']
    rows.insert(-2,{'type':'item.started','item':dict(final,text='')})
    rows.insert(-2,{'type':'item.updated','item':dict(final,text='partial')})
    assert decode(rows).total_tokens==120


def test_maximum_events_and_raw_bytes_are_bounded():
    with pytest.raises(ValueError): core.CodexExecOutput(0,b'x'*(core.MAX_EVENT_BYTES+1))
    rows=events();rows[2:2]=[{'type':'item.completed','item':{'id':f'r{i}','type':'reasoning','text':''}} for i in range(256)]
    with pytest.raises(ValueError): decode(rows)


@pytest.mark.parametrize('number',[0,33,True,'1'])
def test_sequence_is_bounded(number):
    with pytest.raises(ValueError): decode(call_number=number)


class ScriptedTransport:
    def __init__(self): self.requests=[]
    def run(self,request):
        self.requests.append(request)
        messages=json.loads(request.messages_json)
        if len(self.requests)==1: return output(events([action('search_evidence')]))
        if len(self.requests)==2: return output(events([action('read_evidence',{'source_id':'source-1'})]))
        return output(events([action('finish_research',dict(probability_yes='0.6',confidence='0.4',
                               summary='Synthetic evidence only',source_ids=['source-1']))]))


@pytest.mark.parametrize('team',['crypto_btc','crypto_eth'])
def test_existing_agent_completes_both_teams_through_event_adapter(team):
    host=ScriptedTransport(); model=core.CodexExecModel(model_id='synthetic-model',transport=host)
    assert not host.requests
    result=agent.run_team_research_agent(task(team),model=model,required_source_ids=('source-1',))
    assert result.status=='completed' and result.model_calls==3 and result.total_tokens==360
    assert len(host.requests)==3 and result.source_ids==('source-1',)
    assert 'PRIVATE-REASONING' not in result.summary
    ids=[call['id'] for msg in json.loads(host.requests[-1].messages_json)
         for call in msg.get('tool_calls',[])]
    assert ids==['codex-1-0','codex-2-0']


@pytest.mark.parametrize('defect',['raise','nonzero','bad_type','bad_stream','interrupt','exit'])
def test_failed_model_is_permanently_closed_without_repair_or_retry(defect):
    seen=[]
    class Host:
        def run(self,request):
            seen.append(request)
            if defect=='raise': raise RuntimeError('PRIVATE-SENTINEL')
            if defect=='interrupt': raise KeyboardInterrupt()
            if defect=='exit': raise SystemExit(0)
            if defect=='nonzero': return output(code=1)
            if defect=='bad_type': return object()
            return core.CodexExecOutput(0,b'PRIVATE-SENTINEL')
    model=core.CodexExecModel(model_id='model',transport=Host())
    exception=KeyboardInterrupt if defect=='interrupt' else SystemExit if defect=='exit' else ValueError
    with pytest.raises(exception) as error: model.complete(messages_json='[{}]',max_output_tokens=10)
    with pytest.raises(ValueError,match='stopped'): model.complete(messages_json='[{}]',max_output_tokens=10)
    assert len(seen)==1 and 'PRIVATE-SENTINEL' not in ''.join(traceback.format_exception(error.value))
