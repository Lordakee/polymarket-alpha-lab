"""Synthetic transport boundaries: no socket, real token, provider or database."""
import io
import json
import socket
import traceback
from email.message import Message
from urllib import request as urllib_request
from urllib.response import addinfourl

import pytest

from polymarket_alpha_lab import llm_research_transport as transport

TOKEN = 'SYNTHETIC-AUDIT-TOKEN-NOT-A-CREDENTIAL'
ENDPOINT = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('This suite must not open a socket')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(urllib_request, '_opener', None)


def estimate(client):
    return client.estimate(market_question='Synthetic YES/NO?', outcome_names=('Yes', 'No'))


def synthetic_http(monkeypatch, *, status=200, destination=None):
    seen = []
    body = json.dumps({'choices': [{'finish_reason': 'stop', 'message': {
        'content': '{"p_yes":0.5,"confidence":0.6}'}}],
        'usage': {'total_tokens': 10}}).encode()

    def response(self, request):
        seen.append(request)
        headers = Message()
        code = status if len(seen) == 1 else 200
        if destination is not None and len(seen) == 1:
            headers['Location'] = destination
        result = addinfourl(io.BytesIO(body), headers, request.full_url, code)
        result.msg = 'Synthetic response only'
        return result

    monkeypatch.setattr(urllib_request.HTTPSHandler, 'https_open', response)
    monkeypatch.setattr(urllib_request.HTTPHandler, 'http_open', response)
    return seen


def test_transport_repr_does_not_expose_caller_token():
    client = transport.GLMChatTransport(api_token=TOKEN)
    assert TOKEN not in repr(client)
    assert TOKEN not in str(client)
    assert 'GLMChatTransport' in repr(client)


@pytest.mark.parametrize('endpoint', [
    'http://example.invalid/chat', 'ftp://example.invalid/chat',
    '//example.invalid/chat', 'https:///chat',
    'https://user:' + TOKEN + '@example.invalid/chat',
    'https://example.invalid/chat#fragment',
    ' https://example.invalid/chat', 'https://example.invalid/chat\n',
    'https://example.invalid/\tchat', 'https://example.invalid:bad/chat',
    'https://example.invalid:70000/chat', 'https://[invalid/chat',
])
def test_invalid_endpoints_fail_at_construction_without_echo(endpoint):
    with pytest.raises(ValueError) as error:
        transport.GLMChatTransport(api_token=TOKEN, endpoint_url=endpoint)
    assert TOKEN not in ''.join(traceback.format_exception(error.value))


@pytest.mark.parametrize('token', ['embedded\nheader', 'embedded\rheader',
                                  'embedded\x00header', 'embedded\theader'])
def test_header_control_characters_are_rejected(token):
    with pytest.raises(ValueError):
        transport.GLMChatTransport(api_token=token)


@pytest.mark.parametrize('endpoint', [ENDPOINT, 'https://example.invalid/v1/chat',
                                      'https://example.invalid:8443/v1/chat'])
def test_explicit_https_endpoint_is_inert_until_estimate(endpoint):
    assert transport.GLMChatTransport(api_token=TOKEN, endpoint_url=endpoint).endpoint_url == endpoint


@pytest.mark.parametrize('status', [301, 302, 303, 307, 308])
@pytest.mark.parametrize('destination', [
    'http://redirect.invalid/collect', 'https://redirect.invalid/collect',
    'https://open.bigmodel.cn/changed-endpoint',
])
def test_redirect_is_a_failed_single_operation_not_a_second_request(monkeypatch, status, destination):
    seen = synthetic_http(monkeypatch, status=status, destination=destination)
    result = estimate(transport.GLMChatTransport(api_token=TOKEN))
    assert len(seen) == 1
    assert seen[0].full_url == ENDPOINT
    assert seen[0].get_header('Authorization') == 'Bearer ' + TOKEN
    assert result.raw_p_yes is result.raw_confidence is None
    assert result.raw_content == ''
    assert TOKEN not in repr(result)


def test_success_uses_nonredirectable_authorization_and_keeps_contract(monkeypatch):
    seen = synthetic_http(monkeypatch)
    result = estimate(transport.GLMChatTransport(api_token=TOKEN))
    assert len(seen) == 1
    assert seen[0].get_method() == 'POST'
    assert seen[0].get_header('Authorization') == 'Bearer ' + TOKEN
    assert 'Authorization' not in seen[0].headers
    assert result.raw_p_yes is not None
    assert result.token_usage == 10
    assert TOKEN not in repr(result)


def test_transport_error_is_not_retried_or_exposed(monkeypatch):
    seen = []
    def failed(*args, **kwargs):
        seen.append(True)
        raise TimeoutError(TOKEN)
    monkeypatch.setattr(transport, 'urlopen', failed)
    result = estimate(transport.GLMChatTransport(api_token=TOKEN))
    assert seen == [True]
    assert result.raw_p_yes is None
    assert result.raw_content == ''
    assert TOKEN not in repr(result)


def test_interrupt_is_not_swallowed_or_retried(monkeypatch):
    seen = []
    def interrupted(*args, **kwargs):
        seen.append(True)
        raise KeyboardInterrupt()
    monkeypatch.setattr(transport, 'urlopen', interrupted)
    with pytest.raises(KeyboardInterrupt):
        estimate(transport.GLMChatTransport(api_token=TOKEN))
    assert seen == [True]


def test_private_policy_does_not_use_process_global_opener(monkeypatch):
    class UnexpectedGlobalOpener:
        def open(self, *args, **kwargs):
            pytest.fail('Authenticated transport must not use a global opener')
    monkeypatch.setattr(urllib_request, '_opener', UnexpectedGlobalOpener())
    seen = synthetic_http(monkeypatch)
    assert estimate(transport.GLMChatTransport(api_token=TOKEN)).raw_p_yes is not None
    assert len(seen) == 1


@pytest.mark.parametrize('status', [400, 401, 403, 429, 500, 503])
def test_http_error_does_not_retry_or_publish_body(monkeypatch, status):
    seen = synthetic_http(monkeypatch, status=status)
    result = estimate(transport.GLMChatTransport(api_token=TOKEN))
    assert len(seen) == 1
    assert result.raw_p_yes is result.raw_confidence is None
    assert result.raw_content == ''
    assert TOKEN not in repr(result)
