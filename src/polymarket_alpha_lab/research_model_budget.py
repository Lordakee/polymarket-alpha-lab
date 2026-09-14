"""Explicit immutable call allowances; integer reservations, never a price oracle.

The per-call bound is an operator assertion tied to reviewed adapter/pricing
terms. This module cannot certify provider billing. No client or secret storage.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime
from hashlib import sha256
import json
import re

from polymarket_alpha_lab.research_execution import copy_request
from polymarket_alpha_lab.research_resolution import utc
from polymarket_alpha_lab.team_research_agent_types import hard_flags, identifier, integer, strict_json, text

VERSION = 'research-model-budget-v1'
MAX_POLICY_BYTES = 32768


def digest(value):
    if type(value) is not str or re.fullmatch('[a-f0-9]{64}', value) is None:
        raise ValueError('research_budget_digest_invalid')


@dataclass(frozen=True, slots=True)
class ModelCallBudget:
    budget_id: str
    provider_id: str
    model_id: str
    currency: str
    total_micros: int
    per_call_micros: int
    max_calls: int
    max_message_bytes: int
    max_output_tokens: int
    expires_at: datetime
    request_keys: tuple[tuple[str, str], ...]
    bound_reference_sha256: str
    cost_bound_attested: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self):
        identifier('budget_id', self.budget_id)
        identifier('provider_id', self.provider_id)
        text('model_id', self.model_id, 128)
        if type(self.currency) is not str or re.fullmatch('[A-Z]{3}', self.currency) is None:
            raise ValueError('research_budget_currency_invalid')
        integer('total_micros', self.total_micros, 1, 10**15)
        integer('per_call_micros', self.per_call_micros, 1, 10**12)
        integer('max_calls', self.max_calls, 1, 3200)
        integer('max_message_bytes', self.max_message_bytes, 1, 2000000)
        integer('max_output_tokens', self.max_output_tokens, 1, 8192)
        if self.per_call_micros > self.total_micros or self.cost_bound_attested is not True:
            raise ValueError('research_budget_bound_not_attested')
        object.__setattr__(self, 'expires_at', utc('expires_at', self.expires_at))
        if (type(self.request_keys) is not tuple or not 1 <= len(self.request_keys) <= 100
                or any(type(k) is not tuple or len(k) != 2 for k in self.request_keys)):
            raise ValueError('research_budget_request_keys_invalid')
        for rid, checksum in self.request_keys:
            identifier('record_id', rid)
            digest(checksum)
        if len({k[0] for k in self.request_keys}) != len(self.request_keys):
            raise ValueError('research_budget_duplicate_request')
        digest(self.bound_reference_sha256)
        hard_flags(self)

    @property
    def payload(self):
        data = asdict(self)
        data['expires_at'] = self.expires_at.isoformat()
        return json.dumps(dict(schema_version=VERSION, **data), sort_keys=True,
                          separators=(',', ':'), ensure_ascii=True, allow_nan=False)

    @property
    def content_sha256(self):
        return sha256(self.payload.encode()).hexdigest()

    def bind_request(self, request):
        policy = copy_budget(self)
        request = copy_request(request)
        if (request.intake.team_id not in ('crypto_btc', 'crypto_eth') or request.model_id != policy.model_id
                or (request.record_id, request.content_sha256) not in policy.request_keys):
            raise ValueError('research_budget_request_mismatch')
        return request


def copy_budget(policy):
    if type(policy) is not ModelCallBudget:
        raise ValueError('research_budget_policy_invalid')
    result = replace(policy)
    if len(result.payload.encode()) > MAX_POLICY_BYTES:
        raise ValueError('research_budget_policy_limit')
    return result


def decode_budget(payload, checksum):
    try:
        if type(payload) is not str or not 1 <= len(payload.encode()) <= MAX_POLICY_BYTES:
            raise ValueError
        digest(checksum)
        if sha256(payload.encode()).hexdigest() != checksum:
            raise ValueError
        data = strict_json(payload)
        if type(data) is not dict or data.pop('schema_version', None) != VERSION:
            raise ValueError
        if type(data['request_keys']) is not list or any(type(k) is not list for k in data['request_keys']):
            raise ValueError
        data['request_keys'] = tuple(tuple(k) for k in data['request_keys'])
        data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        result = copy_budget(ModelCallBudget(**data))
        if result.payload != payload:
            raise ValueError
        return result
    except Exception:
        raise ValueError('research_budget_payload_invalid') from None


@dataclass(frozen=True, slots=True)
class StoredModelBudget:
    policy: ModelCallBudget
    created_at: datetime

    def __post_init__(self):
        object.__setattr__(self, 'policy', copy_budget(self.policy))
        object.__setattr__(self, 'created_at', utc('created_at', self.created_at))
        if self.created_at >= self.policy.expires_at:
            raise ValueError('research_budget_creation_expired')


@dataclass(frozen=True, slots=True)
class ModelBudgetSnapshot:
    stored: StoredModelBudget
    observed_at: datetime
    reserved_calls: int
    reserved_micros: int

    def __post_init__(self):
        if type(self.stored) is not StoredModelBudget:
            raise ValueError('research_budget_snapshot_invalid')
        object.__setattr__(self, 'stored', replace(self.stored))
        object.__setattr__(self, 'observed_at', utc('observed_at', self.observed_at))
        p = self.stored.policy
        integer('reserved_calls', self.reserved_calls, 0, p.max_calls)
        integer('reserved_micros', self.reserved_micros, 0, p.total_micros)
        if (self.reserved_micros != self.reserved_calls * p.per_call_micros
                or self.observed_at < self.stored.created_at):
            raise ValueError('research_budget_accounting_invalid')

    def to_dict(self):
        self.__post_init__()
        p = self.stored.policy
        expired = self.observed_at >= p.expires_at
        remaining = min(p.max_calls - self.reserved_calls,
                        (p.total_micros - self.reserved_micros) // p.per_call_micros)
        return dict(budget_id=p.budget_id, policy_sha256=p.content_sha256,
            currency=p.currency, unit='millionth_of_currency', total_micros=p.total_micros,
            reserved_calls=self.reserved_calls, reserved_micros=self.reserved_micros,
            unreserved_micros=p.total_micros-self.reserved_micros,
            available_call_reservations=0 if expired else remaining, expired=expired,
            created_at=self.stored.created_at.isoformat(), observed_at=self.observed_at.isoformat(),
            expires_at=p.expires_at.isoformat(), actual_provider_calls=None, actual_billed_micros=None,
            provider_charge_bound_verified=False, automatic_refunds=False,
            model_called=False, business_writes_performed=False,
            paper_only=True, report_only=True, readonly=True)
