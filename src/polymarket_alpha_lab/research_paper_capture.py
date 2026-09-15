"""Append one prospective simulation receipt per ORIGINAL research record.

The existing evaluator supplies complete-history selection. Inputs and its exact
per-record result are saved atomically with checked pre-cutoff admission. No live
order, model, network, file journal, automatic retry or alternate driver.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime

from polymarket_alpha_lab import research_capture_psycopg as db
from polymarket_alpha_lab import research_execution_psycopg as execution
from polymarket_alpha_lab.research_paper import ResearchPaperEvaluation, evaluate_research_paper_with_psycopg
from polymarket_alpha_lab.research_paper_capture_codec import (
    MAX_PAYLOAD_BYTES, MAX_RESULT_BYTES, checksum, decode_paper_scenario, dump, encode_paper_scenario,
)
from polymarket_alpha_lab.research_paper_inputs import ResearchPaperScenario, json_value
from polymarket_alpha_lab.research_resolution import digest, utc
from polymarket_alpha_lab.team_research_agent_types import hard_flags, identifier, strict_json
from polymarket_alpha_lab.team_research_evaluation import ResearchEvaluationReport

_COLUMNS = ('record_id,request_sha256,attempt_payload_sha256,first_record_id,history_at,history_sha256,'
            'forecast_cutoff_at,recorded_at,input_payload,input_sha256,result_payload,result_sha256,'
            'paper_only,report_only,readonly')


@dataclass(frozen=True, slots=True)
class StoredResearchPaper:
    scenario: ResearchPaperScenario = field(repr=False)
    request_sha256: str
    attempt_payload_sha256: str
    first_record_id: str
    history_at: datetime
    history_sha256: str
    forecast_cutoff_at: datetime
    recorded_at: datetime
    result_payload: str = field(repr=False)
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self):
        hard_flags(self)
        payload = encode_paper_scenario(self.scenario)
        object.__setattr__(self, 'scenario', decode_paper_scenario(payload, checksum(payload)))
        identifier('first_record_id', self.first_record_id)
        for name in ('request_sha256', 'attempt_payload_sha256', 'history_sha256'):
            digest(getattr(self, name))
        for name in ('history_at', 'forecast_cutoff_at', 'recorded_at'):
            object.__setattr__(self, name, utc(name, getattr(self, name)))
        s = self.scenario
        if (not s.decision_at <= self.history_at <= self.recorded_at < self.forecast_cutoff_at
                or (self.recorded_at - s.decision_at).total_seconds() > s.max_age_seconds):
            raise ValueError('paper_capture_time_invalid')
        if (type(self.result_payload) is not str
                or not 1 <= len(self.result_payload.encode('utf-8')) <= MAX_RESULT_BYTES):
            raise ValueError('paper_capture_result_limit')
        result = strict_json(self.result_payload)
        if (type(result) is not dict or dump(result) != self.result_payload
                or result.get('record_id') != s.record_id or result.get('record_sha256') != s.record_sha256
                or result.get('scenario_binding') != json_value(s.binding())
                or result.get('status') not in ('paper_scenario_ready', 'paper_scenario_rejected', 'not_simulated')):
            raise ValueError('paper_capture_result_invalid')

    def to_dict(self):
        r = replace(self)
        return json_value(dict(schema_version='stored-research-paper-v1', record_id=r.scenario.record_id,
            input_sha256=checksum(encode_paper_scenario(r.scenario)), result_sha256=checksum(r.result_payload),
            request_sha256=r.request_sha256, record_sha256=r.scenario.record_sha256,
            first_record_id=r.first_record_id, history_at=r.history_at, history_sha256=r.history_sha256,
            forecast_cutoff_at=r.forecast_cutoff_at, recorded_at=r.recorded_at,
            result=strict_json(r.result_payload), durable_simulation_evidence=True,
            prospective_database_admission=True, commit_before_cutoff_verified=False,
            final_whole_history_checked=False, source_authentication_performed=False,
            tariff_verified=False, realized_pnl=None, paper_trades_created=0,
            paper_only=True, report_only=True, readonly=True))


def _original(cursor, record_id):
    # Check combined payload bound BEFORE using the established lookup helper.
    cursor.execute('SELECT octet_length(c.request_payload)+coalesce(octet_length(a.payload),0) '
        'FROM research_capture.execution_claims c LEFT JOIN research_capture.attempts a '
        'ON a.record_id=c.record_id WHERE c.record_id=%s', (record_id,))
    size = cursor.fetchone()
    if size is None:
        raise db.ResearchCaptureConflict('paper_capture_original_missing')
    if type(size[0]) is not int or not 1 <= size[0] <= MAX_PAYLOAD_BYTES:
        raise db.ResearchCaptureConflict('paper_capture_original_limit')
    value = execution._lookup(cursor, record_id)
    if value is None or value.record is None:
        raise db.ResearchCaptureConflict('paper_capture_original_incomplete')
    return value


def _result_for(history, scenario, original):
    eligible = next(d.reason_code in ('outcome_pending', 'scored') for d in history.decisions
                    if d.record_id == scenario.record_id)
    result = ResearchPaperEvaluation(history, (scenario,), (original,) if eligible else ()).to_dict()
    return next(r for r in result['paper_attempts'] if r['record_id'] == scenario.record_id)


def _row(cursor, row):
    if type(row) is not tuple or len(row) != 15 or any(x is not True for x in row[12:]):
        raise ValueError('paper_capture_row_invalid')
    scenario = decode_paper_scenario(row[8], row[9])
    if row[0] != scenario.record_id or checksum(row[10]) != row[11]:
        raise ValueError('paper_capture_row_mismatch')
    stored = StoredResearchPaper(scenario, *row[1:8], row[10])
    original = _original(cursor, row[0])
    first = original if stored.first_record_id == row[0] else _original(cursor, stored.first_record_id)
    if (original.request.content_sha256 != stored.request_sha256
            or original.record.content_sha256 != scenario.record_sha256
            or original.request.forecast_cutoff_at != stored.forecast_cutoff_at
            or original.record.group_key != first.record.group_key
            or original.request.intake.condition_id != first.request.intake.condition_id):
        raise ValueError('paper_capture_original_mismatch')
    cursor.execute('SELECT payload_sha256 FROM research_capture.attempts WHERE record_id=%s', (row[0],))
    if cursor.fetchone() != (stored.attempt_payload_sha256,):
        raise ValueError('paper_capture_original_mismatch')
    # This small reconstruction checks this stored row, NOT complete present-day
    # history. It reuses the original selector and simulator; never uses a later
    # outcome or overwrites an old result after a rule/engine version changes.
    records = (original.record,) if first is original else (first.record, original.record)
    history = ResearchEvaluationReport(records, (), stored.history_at)
    if dump(_result_for(history, scenario, original)) != stored.result_payload:
        raise ValueError('paper_capture_result_changed')
    return stored


def _load(cursor, record_id):
    cursor.execute('SELECT octet_length(input_payload),octet_length(result_payload) '
                   'FROM research_capture.paper_simulations WHERE record_id=%s', (record_id,))
    sizes = cursor.fetchone()
    if sizes is None:
        return None
    if (type(sizes) is not tuple or len(sizes) != 2
            or any(type(x) is not int for x in sizes)
            or not 1 <= sizes[0] <= MAX_PAYLOAD_BYTES or not 1 <= sizes[1] <= MAX_RESULT_BYTES):
        raise db.ResearchCaptureConflict('paper_capture_payload_limit')
    cursor.execute(f'SELECT {_COLUMNS} FROM research_capture.paper_simulations WHERE record_id=%s', (record_id,))
    return _row(cursor, cursor.fetchone())


def inspect_research_paper_with_psycopg(dsn: str, *, record_id: str) -> StoredResearchPaper | None:
    identifier('record_id', record_id)
    return db._local_transaction(dsn, lambda c: _load(c, record_id), readonly=True)


def capture_research_paper_with_psycopg(dsn: str, *, scenario: ResearchPaperScenario,
                                       allow_paper_write: bool = False) -> StoredResearchPaper:
    """One original record gets ONE immutable input/result, accepted or rejected.

    Exact committed replay bypasses new admission and full-history selection, but
    still recomputes the stored row for integrity. New work first uses
    the existing complete-history snapshot. Final admission rechecks the original
    selection under the same event lock used by existing managed research writers.
    History and write are separate snapshots; no final whole-history claim is made.
    """
    if allow_paper_write is not True:
        raise ValueError('paper_capture_write_opt_in_required')
    payload = encode_paper_scenario(scenario)
    scenario = decode_paper_scenario(payload, checksum(payload))
    existing = inspect_research_paper_with_psycopg(dsn, record_id=scenario.record_id)
    if existing is not None:
        if encode_paper_scenario(existing.scenario) != payload:
            raise db.ResearchCaptureConflict('paper_capture_identity_conflict')
        return existing
    evaluated = evaluate_research_paper_with_psycopg(dsn, scenarios=(scenario,))
    history = evaluated.history
    target = next(r for r in history.records if r.record_id == scenario.record_id)
    condition = target.run.intake.condition_id
    if target.run.intake.team_id not in ('crypto_btc', 'crypto_eth'):
        raise ValueError('paper_capture_team_unsupported')
    first_id = next(d.record_id for d in history.decisions
        if (d.team_id, d.model_id, d.protocol_version, d.condition_id) == (*target.group_key, condition)
        and d.reason_code not in ('later_attempt', 'not_yet_recorded'))
    result = next(r for r in evaluated.to_dict()['paper_attempts'] if r['record_id'] == scenario.record_id)
    result_payload = dump(result)
    if len(result_payload.encode('utf-8')) > MAX_RESULT_BYTES:
        raise ValueError('paper_capture_result_limit')

    def operation(cursor):
        db._lock(cursor, condition)
        old = _load(cursor, scenario.record_id)
        if old is not None:
            if encode_paper_scenario(old.scenario) != payload:
                raise db.ResearchCaptureConflict('paper_capture_identity_conflict')
            return old
        original = _original(cursor, scenario.record_id)
        if original.record != target:
            raise db.ResearchCaptureConflict('paper_capture_original_mismatch')
        cursor.execute('SELECT clock_timestamp()')
        now = utc('database clock', cursor.fetchone()[0])
        if (not scenario.decision_at <= history.generated_at <= now < original.request.forecast_cutoff_at
                or (now - scenario.decision_at).total_seconds() > scenario.max_age_seconds):
            raise db.ResearchCaptureConflict('paper_capture_not_prospective')
        cursor.execute('SELECT record_id FROM research_capture.attempts WHERE '
            'team_id=%s AND model_id=%s AND protocol_version=%s AND condition_id=%s '
            'ORDER BY recorded_at,record_id LIMIT 1', (*target.group_key, condition))
        if cursor.fetchone() != (first_id,):
            raise db.ResearchCaptureConflict('paper_capture_selection_changed')
        cursor.execute('SELECT payload_sha256 FROM research_capture.attempts WHERE record_id=%s', (scenario.record_id,))
        attempt_hash = cursor.fetchone()[0]
        cursor.execute('INSERT INTO research_capture.paper_simulations '
            '(record_id,request_sha256,attempt_payload_sha256,first_record_id,history_at,history_sha256,'
            'forecast_cutoff_at,input_payload,input_sha256,result_payload,result_sha256) '
            f'VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING {_COLUMNS}',
            (scenario.record_id, original.request.content_sha256, attempt_hash, first_id, history.generated_at,
             history.input_sha256, original.request.forecast_cutoff_at, payload, checksum(payload),
             result_payload, checksum(result_payload)))
        saved = _row(cursor, cursor.fetchone())
        if (encode_paper_scenario(saved.scenario) != payload or saved.result_payload != result_payload
                or saved.request_sha256 != original.request.content_sha256
                or saved.attempt_payload_sha256 != attempt_hash or saved.first_record_id != first_id
                or saved.history_at != history.generated_at or saved.history_sha256 != history.input_sha256
                or saved.forecast_cutoff_at != original.request.forecast_cutoff_at
                or saved.recorded_at < now):
            raise ValueError('paper_capture_insert_mismatch')
        return saved
    return db._local_transaction(dsn, operation)


__all__ = ('StoredResearchPaper', 'capture_research_paper_with_psycopg', 'inspect_research_paper_with_psycopg')
