"""Separate adversarial review: precise refusal before secrets or result acceptance."""
from dataclasses import replace
from pathlib import Path
import fnmatch
import json

import pytest

from polymarket_alpha_lab import research_claude_exec as cli
from polymarket_alpha_lab import research_claude_profile as profile
from polymarket_alpha_lab import research_process as process
from polymarket_alpha_lab.research_dispatch_runner import ResearchDispatchStop
from tests.test_research_claude_exec import MODEL, wire
from tests.test_research_claude_profile import candidate, bound, SENTINEL


@pytest.mark.parametrize('stderr_bytes', [1, 17, 65536])
def test_unclassified_stderr_cannot_certify_a_clean_single_result(stderr_bytes):
    result = replace(wire(),stderr_bytes=stderr_bytes)
    with pytest.raises(ValueError,match='response_invalid'):
        cli.decode_claude_result(result,request=cli.ClaudeExecInput(MODEL,'[{}]',100),call_number=1)


@pytest.mark.parametrize('limit', [1,100])
def test_known_payload_limit_failure_precedes_credential_supplier(monkeypatch,tmp_path,limit):
    p = candidate(tmp_path)
    p = replace(p,process=replace(p.process,max_stdin_bytes=limit))
    entered=[]
    def key(): entered.append('key'); return SENTINEL
    def runner(**kwargs):
        entered.append('runner')
        if len(kwargs['stdin']) > kwargs['spec'].max_stdin_bytes:
            raise ValueError('oversize input')
        return wire()
    monkeypatch.setattr(cli,'run_research_process',runner)
    model = bound(p,api_key_supplier=key)('crypto_btc')
    with pytest.raises(ValueError): model.complete(messages_json='[{}]',max_output_tokens=100)
    assert entered==[]


def test_profile_digest_includes_original_prompt_and_action_protocol(monkeypatch,tmp_path):
    p = candidate(tmp_path); original=p.contract_sha256
    monkeypatch.setattr(cli.ClaudeExecInput,'prompt_json',property(lambda self:'changed protocol'))
    assert p.contract_sha256 != original


def test_stop_during_explicit_supplier_never_starts_image(monkeypatch,tmp_path):
    p=candidate(tmp_path);stop=ResearchDispatchStop();calls=[]
    def key():calls.append(1);stop.request_stop();return SENTINEL
    monkeypatch.setattr(process,'_spawn',lambda *a:pytest.fail('stopped launch'))
    model=bound(p,stop=stop,api_key_supplier=key)('crypto_btc')
    with pytest.raises(ValueError):model.complete(messages_json='[{}]',max_output_tokens=100)
    assert calls==[1]


@pytest.mark.parametrize('field,value', [('input_tokens',True),('output_tokens',False),
                                        ('cache_read_input_tokens',2.0),('cache_creation_input_tokens',-1)])
def test_model_usage_cannot_hide_wrong_scalar_type_by_equal_value(field,value):
    from tests.test_research_claude_exec import envelope
    raw=envelope()
    names=dict(zip(cli._USAGE,cli._MODEL_USAGE,strict=True))
    raw['usage'][field]=value
    raw['modelUsage'][MODEL][names[field]]=value
    with pytest.raises(ValueError):
        cli.decode_claude_result(wire(raw),request=cli.ClaudeExecInput(MODEL,'[{}]',100),call_number=1)


@pytest.mark.parametrize('path', [
    'src/polymarket_alpha_lab/research_claude_exec.py',
    'src/polymarket_alpha_lab/research_claude_profile.py',
    'tests/test_research_claude_exec.py', 'tests/test_research_claude_profile.py',
    'tests/test_research_claude_review.py',
])
@pytest.mark.parametrize('workflow', ['native-postgres.yml','native-distribution.yml'])
def test_shipped_claude_changes_trigger_real_platform_gates(path,workflow):
    import re
    root=Path(__file__).resolve().parents[1]
    source=(root/'.github/workflows'/workflow).read_text()
    filters=re.findall(r"^      - '([^']+)'",source,flags=re.MULTILINE)
    assert any(fnmatch.fnmatchcase(path,pattern) for pattern in filters)


def test_changed_prompt_contract_after_binding_never_enters_key_supplier(monkeypatch,tmp_path):
    p=candidate(tmp_path)
    model=bound(p,api_key_supplier=lambda:pytest.fail('supplier after contract drift'))('crypto_btc')
    monkeypatch.setattr(cli.ClaudeExecInput,'prompt_json',property(lambda self:'changed contract'))
    with pytest.raises(ValueError):model.complete(messages_json='[{}]',max_output_tokens=100)


def test_simultaneous_calls_have_unique_ids_and_never_exceed_client_limit(monkeypatch,tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    p=candidate(tmp_path);entered=[]
    def run(**kwargs):entered.append(1);return wire()
    monkeypatch.setattr(cli,'run_research_process',run)
    model=bound(p)('crypto_eth')
    with ThreadPoolExecutor(max_workers=4) as pool:
        replies=tuple(pool.map(lambda _:model.complete(messages_json='[{}]',max_output_tokens=100),range(32)))
    assert {r.calls[0].call_id for r in replies}=={f'claude-{n}-0' for n in range(1,33)}
    with pytest.raises(ValueError):model.complete(messages_json='[{}]',max_output_tokens=100)
    with pytest.raises(ValueError,match='stopped'):model.complete(messages_json='[{}]',max_output_tokens=100)
    assert len(entered)==32
