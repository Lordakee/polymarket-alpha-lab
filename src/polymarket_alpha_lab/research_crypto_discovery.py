"""Fixed-origin public search with explicit bounded retries and visible failures.

Only discover candidate identifiers for previews. No research approval, model,
credentials, database, arbitrary URL, implicit pagination or durable file store.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from http.client import IncompleteRead
import re
import ssl
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from polymarket_alpha_lab.public_http import PublicBodyError, read_public_body
from polymarket_alpha_lab.research_resolution import condition, utc
from polymarket_alpha_lab.team_research_agent_types import integer, strict_json, text
from polymarket_alpha_lab.team_research_intake import require_market_slug

MAX_BODY = 4 * 1024 * 1024
TEAMS = {'crypto_btc': ('Bitcoin', r'\b(bitcoin|btc)\b'),
         'crypto_eth': ('Ethereum', r'\b(ethereum|eth)\b')}
RETRY_DELAYS = (0.25, 0.75)
RETRYABLE = ('public_response_incomplete', 'public_timeout', 'public_connection_interrupted')
CODES = (*RETRYABLE, 'received', 'public_http_rejected', 'public_tls_failed',
         'public_fetch_failed', 'public_response_framing_invalid', 'public_response_too_large',
         'public_response_empty', 'public_response_invalid', 'public_payload_invalid')


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def _now() -> datetime:
    return datetime.now(UTC)


def _team(team_id: str) -> None:
    if type(team_id) is not str or team_id not in TEAMS:
        raise ValueError('crypto_discovery_team_unsupported')


def endpoint(team_id: str) -> str:
    _team(team_id)
    return 'https://gamma-api.polymarket.com/public-search?' + urlencode(dict(
        q=TEAMS[team_id][0], events_status='active', limit_per_type=10, page=1,
        keep_closed_markets=0, search_profiles='false', search_tags='false'))


@dataclass(frozen=True, slots=True)
class CryptoCandidate:
    condition_id: str
    market_slug: str
    question: str
    scheduled_end_at: datetime

    def __post_init__(self):
        condition(self.condition_id)
        require_market_slug(self.market_slug)
        text('question', self.question, 2000)
        object.__setattr__(self, 'scheduled_end_at', utc('scheduled end', self.scheduled_end_at))

    def to_dict(self):
        value = replace(self)
        return dict(condition_id=value.condition_id, market_slug=value.market_slug,
                    question=value.question, scheduled_end_at=value.scheduled_end_at.isoformat())


def select_candidates(raw: bytes, team_id: str, observed_at: datetime) -> tuple[CryptoCandidate, ...]:
    _team(team_id)
    at = utc('observed_at', observed_at)
    if type(raw) is not bytes or not 1 <= len(raw) <= MAX_BODY:
        raise ValueError('public_payload_invalid')
    body = strict_json(raw.decode('utf-8'))
    if type(body) is not dict or type(body.get('events')) is not list or len(body['events']) > 100:
        raise ValueError('public_payload_invalid')
    found, examined = {}, 0
    for event in body['events']:
        if type(event) is not dict or type(event.get('markets')) is not list:
            raise ValueError('public_payload_invalid')
        examined += len(event['markets'])
        if examined > 1000:
            raise ValueError('public_payload_invalid')
        for market in event['markets']:
            try:
                if type(market) is not dict:
                    raise ValueError('invalid market')
                labels = market['outcomes']
                if type(labels) is str:
                    labels = strict_json(labels)
                item = CryptoCandidate(market['conditionId'], market['slug'], market['question'],
                    datetime.fromisoformat(market['endDate'].replace('Z', '+00:00')))
                if (market.get('active') is not True or market.get('closed') is not False
                        or type(labels) is not list or len(labels) != 2 or set(labels) != {'Yes', 'No'}
                        or not re.search(TEAMS[team_id][1], item.question, re.I)
                        or not re.search(r'above|below|price|reach|hit|\$', item.question, re.I)
                        or not at + timedelta(hours=2) < item.scheduled_end_at < at + timedelta(days=365)):
                    continue
            except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
                continue
            key = item.condition_id
            if key in found and found[key] != item:
                raise ValueError('public_payload_invalid')
            found[key] = item
    return tuple(sorted(found.values(), key=lambda x: (x.scheduled_end_at, x.market_slug, x.condition_id)))


@dataclass(frozen=True, slots=True)
class CryptoDiscovery:
    team_id: str
    observed_at: datetime
    attempt_codes: tuple[str, ...]
    raw_json: bytes | None = field(default=None, repr=False)

    def __post_init__(self):
        _team(self.team_id)
        object.__setattr__(self, 'observed_at', utc('observed_at', self.observed_at))
        if (type(self.attempt_codes) is not tuple or not 1 <= len(self.attempt_codes) <= 3
                or any(type(code) is not str or code not in CODES for code in self.attempt_codes)
                or any(code not in RETRYABLE for code in self.attempt_codes[:-1])):
            raise ValueError('crypto_discovery_trace_invalid')
        if self.attempt_codes[-1] == 'received':
            select_candidates(self.raw_json, self.team_id, self.observed_at)
        elif self.raw_json is not None:
            raise ValueError('crypto_discovery_partial_body_forbidden')

    def candidates(self) -> tuple[CryptoCandidate, ...]:
        self.__post_init__()
        return () if self.raw_json is None else select_candidates(self.raw_json, self.team_id, self.observed_at)

    def to_dict(self) -> dict:
        items = self.candidates()
        success = self.attempt_codes[-1] == 'received'
        return dict(team_id=self.team_id, observed_at=self.observed_at.isoformat(),
            status=('candidates' if items else 'no_candidates') if success else 'failed',
            reason_code=self.attempt_codes[-1], request_attempts=len(self.attempt_codes),
            attempts=[dict(number=i+1, reason_code=c) for i,c in enumerate(self.attempt_codes)],
            recovered_after_failure=success and len(self.attempt_codes)>1,
            source_sha256=None if self.raw_json is None else sha256(self.raw_json).hexdigest(),
            candidate_count=len(items), candidates=[x.to_dict() for x in items],
            one_page_only=True, selection_is_approval=False,
            model_called=False, database_written=False, paper_only=True, report_only=True, readonly=True)


def _one_get(url: str, timeout: int) -> bytes:
    request = Request(url, method='GET', headers={'Accept': 'application/json',
        'Accept-Encoding': 'identity', 'User-Agent': 'polymarket-alpha-lab-public-discovery/1'})
    opener = build_opener(ProxyHandler({}), _NoRedirect())
    with opener.open(request, timeout=timeout) as response:
        if (response.geturl() != url or response.status != 200
                or response.headers.get_content_type() != 'application/json'):
            raise PublicBodyError('public_response_invalid')
        return read_public_body(response, MAX_BODY)


def _reason(error: Exception) -> str:
    if isinstance(error, HTTPError):
        error.close()
        return 'public_http_rejected'  # Includes redirects, auth/rate limits and 5xx. No HTTP retry.
    if isinstance(error, URLError):
        error = error.reason
    if isinstance(error, ssl.SSLError):
        return 'public_tls_failed'
    if isinstance(error, IncompleteRead):
        return 'public_response_incomplete'
    if isinstance(error, TimeoutError):
        return 'public_timeout'
    if isinstance(error, (ConnectionResetError, ConnectionAbortedError)):
        return 'public_connection_interrupted'
    if isinstance(error, PublicBodyError) and str(error) in CODES:
        return str(error)
    return 'public_fetch_failed'


def discover_crypto_markets(team_id: str, *, allow_public_fetch: bool = False,
                            max_attempts: int = 1, timeout_seconds: int = 15) -> CryptoDiscovery:
    """One fixed search page. Default ONE attempt; caller opts into 2 or 3.

    Retry only incomplete response, timeout or reset/abort. Each fresh GET
    consumes the allowance and retains its fixed failure code. No partial-body
    concatenation, retries on HTTP/TLS/content failure, background work or model
    retry. Maximum requested sleep is 1s; blocking operations are not bounded
    by a universal wall-clock deadline. Result traces are in memory only.
    """
    _team(team_id)
    integer('max_attempts', max_attempts, 1, 3)
    integer('timeout_seconds', timeout_seconds, 1, 60)
    if allow_public_fetch is not True:
        raise ValueError('crypto_discovery_requires_public_fetch_opt_in')
    url, codes = endpoint(team_id), []
    for number in range(max_attempts):
        raw = None
        try:
            raw = _one_get(url, timeout_seconds)
        except Exception as error:
            code = _reason(error)
        else:
            at = _now()
            try:
                select_candidates(raw, team_id, at)
            except Exception:
                code = 'public_payload_invalid'
            else:
                return CryptoDiscovery(team_id, at, tuple(codes) + ('received',), raw)
        raw = None  # Discard incomplete/invalid bytes; never turn them into an observation.
        codes.append(code)
        if code not in RETRYABLE or number + 1 == max_attempts:
            return CryptoDiscovery(team_id, _now(), tuple(codes))
        sleep(RETRY_DELAYS[number])
    raise AssertionError('unreachable')
