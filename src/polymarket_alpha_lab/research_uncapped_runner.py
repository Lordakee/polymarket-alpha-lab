"""Explicit no-monetary-cap entry using the original immutable execution claim.

No fake capped allowance, alternative claim ledger, implicit model, or refund.
The supplied factory/transport remains trusted application code, not a sandbox.
"""
from dataclasses import replace
from datetime import UTC, datetime
from threading import Lock

from polymarket_alpha_lab import research_execution_psycopg as execution
from polymarket_alpha_lab.research_execution import CapturedResearchExecution
from polymarket_alpha_lab.research_uncapped import copy_authorization
from polymarket_alpha_lab.team_research_agent_types import ResearchModelReply, integer, strict_json


def _now():
    return datetime.now(UTC)


def _available(authorization, now):
    return authorization.approved_at <= now < authorization.expires_at


def validate_uncapped_choice(authorization, allow_uncapped_costs, model_budget_id=None):
    """Validate a mode selection before I/O; omission keeps legacy APIs intact."""
    if authorization is None:
        if allow_uncapped_costs is not False:
            raise ValueError('research_uncapped_authorization_required')
        return None
    if allow_uncapped_costs is not True or model_budget_id is not None:
        raise ValueError('research_uncapped_mode_conflict_or_not_approved')
    return copy_authorization(authorization)


class _UncappedModel:
    __slots__ = ('_authorization', '_request', '_factory', '_client', '_stop', '_lock', '_failed', '_calls')

    def __init__(self, authorization, request, factory, stop):
        self._authorization = copy_authorization(authorization)
        self._request = self._authorization.bind_request(request)
        self._factory, self._stop = factory, stop
        self._client = None
        self._lock = Lock()
        self._failed, self._calls = False, 0

    def __repr__(self):
        return 'UncappedResearchModel(client=<private>)'

    def _check_admission(self):
        now = _now()
        if (not _available(self._authorization, now) or now >= self._request.forecast_cutoff_at
                or self._stop is not None and self._stop.is_stopped()):
            raise ValueError('research_uncapped_call_not_admitted')

    def complete(self, *, messages_json, max_output_tokens):
        with self._lock:
            if self._failed:
                raise ValueError('research_uncapped_client_stopped')
            try:
                limits = self._request.limits
                integer('max_output_tokens', max_output_tokens, 1, limits.max_output_tokens)
                if (type(messages_json) is not str or not messages_json
                        or len(messages_json) > limits.max_context_chars
                        or len(messages_json.encode('utf-8')) > 2000000
                        or type(strict_json(messages_json)) is not list
                        or not strict_json(messages_json)
                        or self._calls >= limits.max_model_calls):
                    raise ValueError('research_uncapped_call_invalid')
                self._check_admission()
                if self._client is None:
                    self._client = self._factory(self._request.intake.team_id)
                # An inert factory is the contract, but a delay must not bypass
                # time/stop admission even if application code violates it.
                self._check_admission()
                if not callable(getattr(self._client, 'complete', None)):
                    raise ValueError('research_uncapped_client_invalid')
                self._calls += 1
                reply = self._client.complete(messages_json=messages_json, max_output_tokens=max_output_tokens)
                if type(reply) is not ResearchModelReply:
                    raise ValueError('research_uncapped_reply_invalid')
                # Copy nested actions before returning across the callback boundary.
                return replace(reply, calls=tuple(replace(call) for call in reply.calls))
            except BaseException as error:
                self._failed = True
                if not isinstance(error, Exception):
                    raise
                raise ValueError('research_uncapped_call_blocked_or_failed') from None


def run_uncapped_research_with_psycopg(dsn, *, request, authorization, model_factory,
        allow_model_calls=False, allow_uncapped_costs=False, stop=None):
    """Admit explicit permission then reuse claim -> model -> original capture.

    Expired permissions do not authorize NEW work; an exact existing execution
    still replays. Single-operation resource/cutoff/stop gates remain. Expiry uses
    the application UTC clock, not a new DB authorization ledger or hard deadline.
    No actual cost or provider-submission count is inferred from complete calls.
    """
    if allow_model_calls is not True or not callable(model_factory):
        raise ValueError('research_uncapped_model_opt_in_required')
    authorization = validate_uncapped_choice(authorization, allow_uncapped_costs)
    if authorization is None:
        raise ValueError('research_uncapped_authorization_required')
    request = authorization.bind_request(request)
    if stop is not None:
        from polymarket_alpha_lab.research_dispatch_runner import ResearchDispatchStop
        if type(stop) is not ResearchDispatchStop:
            raise ValueError('research_uncapped_stop_invalid')
    unavailable = not _available(authorization, _now()) or stop is not None and stop.is_stopped()
    if unavailable:
        prior = execution.inspect_captured_research_with_psycopg(dsn, record_id=request.record_id)
        if prior is not None:
            if type(prior) is not CapturedResearchExecution:
                raise ValueError('research_uncapped_replay_invalid')
            prior = replace(prior)
            if prior.request.payload != request.payload:
                raise ValueError('research_uncapped_request_mismatch')
            return prior
        raise ValueError('research_uncapped_not_available')

    def factory(team_id):
        if team_id != request.intake.team_id:
            raise ValueError('research_uncapped_team_mismatch')
        return _UncappedModel(authorization, request, model_factory, stop)

    # No monetary permit is appropriate in this explicitly uncapped mode. The
    # existing committed claim still prevents another start after uncertain I/O.
    return execution.run_captured_research_with_psycopg(dsn, request=request, model_factory=factory)
