"""Explicit task-scoped permission without a business monetary ceiling.

This is an application authorization value, NOT a price, invoice, reservation or
new durable store. Original request identities and resource limits remain intact.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime
from hashlib import sha256
import json

from polymarket_alpha_lab.research_execution import copy_request
from polymarket_alpha_lab.research_model_budget import digest
from polymarket_alpha_lab.research_resolution import utc
from polymarket_alpha_lab.team_research_agent_types import hard_flags, identifier, strict_json, text

VERSION = 'research-no-monetary-cap-v1'
MAX_AUTHORIZATION_BYTES = 32768


@dataclass(frozen=True, slots=True)
class UncappedResearchAuthorization:
    authorization_id: str
    model_id: str
    adapter_contract_sha256: str
    approved_at: datetime
    expires_at: datetime
    request_keys: tuple[tuple[str, str], ...]
    no_monetary_cap_approved: bool = False
    research_data_send_approved: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self):
        identifier('authorization_id', self.authorization_id)
        text('model_id', self.model_id, 128)
        self.model_id.encode('utf-8')
        digest(self.adapter_contract_sha256)
        object.__setattr__(self, 'approved_at', utc('approved_at', self.approved_at))
        object.__setattr__(self, 'expires_at', utc('expires_at', self.expires_at))
        if self.approved_at >= self.expires_at:
            raise ValueError('research_uncapped_invalid_window')
        if self.no_monetary_cap_approved is not True or self.research_data_send_approved is not True:
            raise ValueError('research_uncapped_explicit_approval_required')
        keys = self.request_keys
        # A finite intake is not a cumulative business event/call/money ceiling.
        if (type(keys) is not tuple or not 1 <= len(keys) <= 100
                or any(type(k) is not tuple or len(k) != 2 for k in keys)):
            raise ValueError('research_uncapped_invalid_roster')
        for record_id, checksum in keys:
            identifier('record_id', record_id)
            digest(checksum)
        if len({key[0] for key in keys}) != len(keys):
            raise ValueError('research_uncapped_duplicate_request')
        hard_flags(self)

    @property
    def payload(self):
        data = asdict(self)
        data['approved_at'] = self.approved_at.isoformat()
        data['expires_at'] = self.expires_at.isoformat()
        return json.dumps(dict(schema_version=VERSION, **data), sort_keys=True,
                          separators=(',', ':'), ensure_ascii=True, allow_nan=False)

    @property
    def content_sha256(self):
        return sha256(self.payload.encode('utf-8')).hexdigest()

    def bind_request(self, request):
        authorization = copy_authorization(self)
        request = copy_request(request)
        if (request.intake.team_id not in ('crypto_btc', 'crypto_eth')
                or request.model_id != authorization.model_id
                or (request.record_id, request.content_sha256) not in authorization.request_keys):
            raise ValueError('research_uncapped_request_mismatch')
        return request

    def to_dict(self):
        value = copy_authorization(self)
        return dict(schema_version=VERSION, authorization_id=value.authorization_id,
                    authorization_sha256=value.content_sha256, model_id=value.model_id,
                    adapter_contract_sha256=value.adapter_contract_sha256,
                    approved_at=value.approved_at.isoformat(), expires_at=value.expires_at.isoformat(),
                    request_count=len(value.request_keys), monetary_cap=None,
                    actual_billed_micros=None, provider_charge_bound_verified=False,
                    durable_authorization_record_created=False,
                    no_monetary_cap_approved=True, research_data_send_approved=True,
                    paper_only=True, report_only=True, readonly=True)


def copy_authorization(value):
    try:
        if type(value) is not UncappedResearchAuthorization:
            raise ValueError
        result = replace(value)
        if len(result.payload.encode('utf-8')) > MAX_AUTHORIZATION_BYTES:
            raise ValueError
        return result
    except Exception:
        raise ValueError('research_uncapped_authorization_invalid') from None


def decode_authorization(payload, checksum):
    try:
        if type(payload) is not str or not 1 <= len(payload.encode('utf-8')) <= MAX_AUTHORIZATION_BYTES:
            raise ValueError
        digest(checksum)
        if sha256(payload.encode('utf-8')).hexdigest() != checksum:
            raise ValueError
        data = strict_json(payload)
        expected = set(UncappedResearchAuthorization.__dataclass_fields__) | {'schema_version'}
        if type(data) is not dict or set(data) != expected or data.pop('schema_version') != VERSION:
            raise ValueError
        if type(data['request_keys']) is not list or any(type(k) is not list for k in data['request_keys']):
            raise ValueError
        data['request_keys'] = tuple(tuple(k) for k in data['request_keys'])
        for name in ('approved_at', 'expires_at'):
            data[name] = datetime.fromisoformat(data[name])
        result = copy_authorization(UncappedResearchAuthorization(**data))
        if result.payload != payload:
            raise ValueError
        return result
    except Exception:
        raise ValueError('research_uncapped_payload_invalid') from None
