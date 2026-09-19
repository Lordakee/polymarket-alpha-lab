"""Immutable metadata for audited uncapped calls, not invoices or raw transcripts."""
from dataclasses import asdict, dataclass, field, replace
from hashlib import sha256
from datetime import datetime
import json

from polymarket_alpha_lab.research_model_budget import digest
from polymarket_alpha_lab.research_resolution import utc
from polymarket_alpha_lab.research_uncapped import copy_authorization
from polymarket_alpha_lab.team_research_agent_types import ResearchModelReply, identifier, integer


@dataclass(frozen=True, slots=True)
class StoredUncappedAuthorization:
    authorization: object = field(repr=False)
    recorded_at: datetime

    def __post_init__(self):
        p = copy_authorization(self.authorization)
        at = utc('recorded_at', self.recorded_at)
        if not p.approved_at <= at < p.expires_at:
            raise ValueError('research_uncapped_audit_time_invalid')
        object.__setattr__(self, 'authorization', p)
        object.__setattr__(self, 'recorded_at', at)

    def to_dict(self):
        value = replace(self)
        return dict(value.authorization.to_dict(),
                    durable_authorization_record_created=True,
                    recorded_at=value.recorded_at.isoformat(),
                    approval_identity_authenticated=False)


@dataclass(frozen=True, slots=True)
class UncappedCallStart:
    authorization_id: str
    authorization_sha256: str
    record_id: str
    request_sha256: str
    call_number: int
    message_sha256: str
    message_bytes: int
    max_output_tokens: int
    started_at: datetime

    def __post_init__(self):
        for name in ('authorization_id', 'record_id'):
            identifier(name, getattr(self, name))
        for name in ('authorization_sha256', 'request_sha256', 'message_sha256'):
            digest(getattr(self, name))
        integer('call_number', self.call_number, 1, 32)
        integer('message_bytes', self.message_bytes, 1, 2000000)
        integer('max_output_tokens', self.max_output_tokens, 1, 8192)
        object.__setattr__(self, 'started_at', utc('started_at', self.started_at))


@dataclass(frozen=True, slots=True)
class UncappedCallOutcome:
    start: UncappedCallStart
    status: str
    reported_total_tokens: int | None
    reply_sha256: str | None
    recorded_at: datetime

    def __post_init__(self):
        if type(self.start) is not UncappedCallStart:
            raise ValueError('research_uncapped_audit_start_invalid')
        object.__setattr__(self, 'start', replace(self.start))
        if type(self.status) is not str or self.status not in ('returned', 'failed', 'interrupted'):
            raise ValueError('research_uncapped_audit_status_invalid')
        if self.status == 'returned':
            integer('reported_total_tokens', self.reported_total_tokens, 1, 1000000)
            digest(self.reply_sha256)
        elif self.reported_total_tokens is not None or self.reply_sha256 is not None:
            raise ValueError('research_uncapped_audit_unknown_usage_required')
        at = utc('recorded_at', self.recorded_at)
        if at < self.start.started_at:
            raise ValueError('research_uncapped_audit_time_invalid')
        object.__setattr__(self, 'recorded_at', at)


def reply_fingerprint(reply):
    """Hash a validated copy; never retain raw action, reasoning or exception text."""
    if type(reply) is not ResearchModelReply:
        raise ValueError('research_uncapped_audit_reply_invalid')
    reply.__post_init__()
    copied = replace(reply, calls=tuple(replace(c) for c in reply.calls))
    payload = json.dumps(asdict(copied), sort_keys=True, separators=(',', ':'),
                         ensure_ascii=True, allow_nan=False).encode('utf-8')
    return copied, sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class UncappedAuditSnapshot:
    record_id: str
    calls: tuple[UncappedCallStart, ...]
    outcomes: tuple[UncappedCallOutcome, ...]

    def __post_init__(self):
        identifier('record_id', self.record_id)
        if type(self.calls) is not tuple or type(self.outcomes) is not tuple or len(self.calls) > 32:
            raise ValueError('research_uncapped_audit_snapshot_invalid')
        if any(type(c) is not UncappedCallStart for c in self.calls):
            raise ValueError('research_uncapped_audit_snapshot_invalid')
        if any(type(o) is not UncappedCallOutcome for o in self.outcomes):
            raise ValueError('research_uncapped_audit_snapshot_invalid')
        calls = tuple(replace(c) for c in self.calls)
        outcomes = tuple(replace(o) for o in self.outcomes)
        if (tuple(c.call_number for c in calls) != tuple(range(1, len(calls)+1))
                or any(c.record_id != self.record_id for c in calls)
                or len({(c.authorization_id, c.authorization_sha256, c.request_sha256) for c in calls}) > 1
                or len({o.start.call_number for o in outcomes}) != len(outcomes)
                or tuple(o.start.call_number for o in outcomes) != tuple(sorted(o.start.call_number for o in outcomes))
                or any(o.start not in calls for o in outcomes)):
            raise ValueError('research_uncapped_audit_snapshot_binding_invalid')
        indexed = {o.start.call_number: o for o in outcomes}
        for c in calls[:-1]:
            if c.call_number not in indexed or indexed[c.call_number].status != 'returned':
                raise ValueError('research_uncapped_audit_sequence_invalid')
        if any(b.started_at < indexed[a.call_number].recorded_at for a, b in zip(calls, calls[1:])):
            raise ValueError('research_uncapped_audit_time_invalid')
        object.__setattr__(self, 'calls', calls)
        object.__setattr__(self, 'outcomes', outcomes)

    def to_dict(self):
        value = replace(self)
        outcomes = {o.start.call_number: o for o in value.outcomes}
        rows = []
        for start in value.calls:
            outcome = outcomes.get(start.call_number)
            row = asdict(start)
            row['started_at'] = start.started_at.isoformat()
            row.update(status='unknown' if outcome is None else outcome.status,
                       reported_total_tokens=None if outcome is None else outcome.reported_total_tokens,
                       reply_sha256=None if outcome is None else outcome.reply_sha256,
                       recorded_at=None if outcome is None else outcome.recorded_at.isoformat())
            rows.append(row)
        known = [o.reported_total_tokens for o in value.outcomes if o.status == 'returned']
        return dict(record_id=value.record_id, calls=rows, started_call_count=len(rows),
                    validated_reply_count=len(known),
                    unknown_usage_call_count=len(rows)-len(known),
                    reported_tokens_known_subset=sum(known) if known else None,
                    all_calls_have_terminal_record=len(value.outcomes)==len(value.calls),
                    audit_coverage='recorded_calls_only' if rows else 'no_audited_calls',
                    provider_submission_count=None, actual_billed_micros=None,
                    monetary_cap=None, provider_usage_verified=False,
                    paper_only=True, report_only=True, readonly=True)
