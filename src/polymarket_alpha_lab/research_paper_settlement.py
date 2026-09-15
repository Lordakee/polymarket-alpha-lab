"""Settle saved simulation bounds against existing operator-confirmed outcomes.

One managed READ ONLY snapshot, original history gate/selector and immutable
receipts. No new journal, forecast score, tariff inference, portfolio or order.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from decimal import Decimal, localcontext

from polymarket_alpha_lab import research_capture_psycopg as db
from polymarket_alpha_lab import research_paper_capture as paper
from polymarket_alpha_lab import research_resolution_store as resolution
from polymarket_alpha_lab.research_paper import _CONTEXT
from polymarket_alpha_lab.research_paper_capture_codec import checksum, encode_paper_scenario
from polymarket_alpha_lab.research_paper_inputs import content_hash, json_value
from polymarket_alpha_lab.research_resolution_codec import MAX_RESOLUTION_PAYLOAD_BYTES, encode_resolution
from polymarket_alpha_lab.research_resolution_confirmation import (
    SCHEMA, CryptoSettlementReview, build_crypto_resolution_confirmation,
)
from polymarket_alpha_lab.team_research_agent_types import identifier, integer, strict_json

_STATUSES = ('paper_evidence_missing', 'research_not_selected', 'paper_not_selected',
             'outcome_pending', 'crypto_confirmation_required', 'settled_simulation')


def _spend(budget, size):
    if type(size) is not int or size < 0 or size > budget[0]:
        raise db.ResearchCaptureConflict('research_paper_settlement_read_limit')
    budget[0] -= size


def _paper_rows(cursor, history, max_records, budget):
    # Include BOTH original lookups performed by the established row validator.
    # Conservative repeated counting is intentional; never load oversized bodies.
    cursor.execute('SELECT count(*),coalesce(sum(octet_length(p.input_payload)+'
        'octet_length(p.result_payload)+coalesce(octet_length(c.request_payload),0)+'
        'coalesce(octet_length(a.payload),0)+coalesce(octet_length(fc.request_payload),0)+'
        'coalesce(octet_length(fa.payload),0)),0) FROM research_capture.paper_simulations p '
        'LEFT JOIN research_capture.execution_claims c ON c.record_id=p.record_id '
        'LEFT JOIN research_capture.attempts a ON a.record_id=p.record_id '
        'LEFT JOIN research_capture.execution_claims fc ON fc.record_id=p.first_record_id '
        'LEFT JOIN research_capture.attempts fa ON fa.record_id=p.first_record_id '
        'WHERE p.recorded_at<=%s', (history.generated_at,))
    count, size = cursor.fetchone()
    if type(count) is not int or not 0 <= count <= max_records:
        raise db.ResearchCaptureConflict('research_paper_settlement_read_limit')
    _spend(budget, size)
    cursor.execute('SELECT record_id FROM research_capture.paper_simulations '
                   'WHERE recorded_at<=%s ORDER BY record_id', (history.generated_at,))
    ids = tuple(row[0] for row in cursor.fetchall())
    records = {r.record_id: r for r in history.records}
    if len(ids) != count or len(set(ids)) != count or any(rid not in records for rid in ids):
        raise ValueError('research_paper_settlement_snapshot_mismatch')
    rows = {}
    for rid in ids:
        receipt = paper._load(cursor, rid)  # Exact original/result recomputation.
        if (receipt is None or receipt.scenario.record_id != rid
                or receipt.scenario.record_sha256 != records[rid].content_sha256
                or receipt.recorded_at > history.generated_at):
            raise ValueError('research_paper_settlement_receipt_mismatch')
        rows[rid] = receipt
    return rows


def _review(cursor, review_id, at, budget):
    identifier('review_id', review_id)
    cursor.execute('SELECT octet_length(payload) FROM research_capture.resolution_reviews '
                   'WHERE review_id=%s AND recorded_at<=%s', (review_id, at))
    size = cursor.fetchone()
    if size is None:
        raise ValueError('research_paper_settlement_review_missing')
    if type(size[0]) is not int or not 1 <= size[0] <= MAX_RESOLUTION_PAYLOAD_BYTES:
        raise db.ResearchCaptureConflict('research_paper_settlement_read_limit')
    _spend(budget, size[0])
    cursor.execute(f'SELECT {resolution._COLUMNS} FROM research_capture.resolution_reviews '
                   'WHERE review_id=%s AND recorded_at<=%s', (review_id, at))
    return resolution._decode_row(cursor, cursor.fetchone())


def _crypto_review(cursor, outcome, history, budget):
    """Replay the EXISTING crypto confirmation builder, not a new oracle.

    Legacy direct outcomes/reviews remain visible but earn no settled amount.
    A claimed crypto proof with broken bindings is corruption and aborts the read.
    """
    prefix = resolution._REFERENCE
    if not outcome.source_reference.startswith(prefix):
        return None
    saved = _review(cursor, outcome.source_reference[len(prefix):], history.generated_at, budget)
    if saved.outcome != outcome:
        raise ValueError('research_paper_settlement_outcome_mismatch')
    try:
        source = strict_json(saved.submission.confirmation.source_text)
    except (ValueError, RecursionError):
        return None  # Existing generic human confirmation, not crypto workflow.
    if type(source) is not dict or source.get('schema_version') != SCHEMA:
        return None
    rid, cid = source['record_id'], source['candidate_review_id']
    identifier('record_id', rid)
    cursor.execute('SELECT octet_length(c.request_payload)+coalesce(octet_length(a.payload),0) '
        'FROM research_capture.execution_claims c LEFT JOIN research_capture.attempts a '
        'ON a.record_id=c.record_id WHERE c.record_id=%s', (rid,))
    size = cursor.fetchone()
    if size is None:
        raise ValueError('research_paper_settlement_anchor_missing')
    _spend(budget, size[0])
    anchor = paper._original(cursor, rid)
    if anchor.record not in history.records:
        raise ValueError('research_paper_settlement_anchor_mismatch')
    candidate = _review(cursor, cid, history.generated_at, budget)
    proof = replace(saved.submission.confirmation, source_text=source['source_text'])
    instruction = CryptoSettlementReview(saved.submission.review_id, rid, source['request_sha256'],
        cid, source['candidate_payload_sha256'], proof, source['source_venue'], source['source_pair'],
        source['source_interval'], source['source_price_field'], datetime.fromisoformat(source['source_candle_open_at']))
    rebuilt = build_crypto_resolution_confirmation(instruction=instruction, execution=anchor, candidate=candidate)
    if encode_resolution(rebuilt) != encode_resolution(saved.submission):
        raise ValueError('research_paper_settlement_crypto_proof_changed')
    return saved


def _amounts(receipt, decision, outcome, review, record):
    s = receipt.scenario
    terms = strict_json(review.submission.snapshot.raw_json.decode('utf-8'))
    task = record.run.intake.task
    if (review.outcome != outcome or receipt.first_record_id != s.record_id
            or decision['original_reason_code'] != 'outcome_pending'
            or outcome.forecast_cutoff_at != receipt.forecast_cutoff_at
            or outcome.condition_id != record.run.intake.condition_id
            or (terms.get('question'), terms.get('description')) != (task.question, task.resolution_criteria)
            or not receipt.recorded_at < outcome.forecast_cutoff_at <= outcome.resolved_at):
        raise ValueError('research_paper_settlement_terms_or_time_mismatch')
    side = decision['selected_side']
    if side not in ('yes', 'no'):
        raise ValueError('research_paper_settlement_side_invalid')
    costs = decision['assumed_totals']
    names = ('entry_notional_upper_bound', 'assumed_fee_upper_bound',
             'assumed_non_fee_cost_upper_bound', 'assumed_total_cost_upper_bound')
    amounts = {k: Decimal(costs[k]) for k in names}
    if (any(not v.is_finite() or v < 0 for v in amounts.values())
            or sum((amounts[k] for k in names[:3]), Decimal(0)) != amounts[names[3]]):
        raise ValueError('research_paper_settlement_cost_invalid')
    payout = s.requested_size if (side == 'yes') == outcome.actual_yes else Decimal(0)
    return dict(selected_side=side, actual_yes=outcome.actual_yes, requested_size=s.requested_size,
        binary_payout=payout, **amounts,
        settled_pnl_lower_bound=payout-amounts['assumed_total_cost_upper_bound'])


def _assemble(history, papers, reviews):
    """Internal composition of rows already verified in the managed snapshot."""
    records = {r.record_id: r for r in history.records}
    outcomes = {o.condition_id: o for o in history.outcomes}
    rows, groups = [], {}
    for d in history.decisions:
        receipt = papers.get(d.record_id)
        row = dict(record_id=d.record_id, record_sha256=d.record_sha256, team_id=d.team_id,
            model_id=d.model_id, protocol_version=d.protocol_version, condition_id=d.condition_id,
            original_reason_code=d.reason_code, status='paper_evidence_missing',
            paper_input_sha256=None, paper_result_sha256=None, recorded_at=None,
            simulation_status=None, simulation_reason_code=None, cost_policy_sha256=None,
            outcome_sha256=None, review_id=None, review_payload_sha256=None, amounts=None)
        key = None
        if receipt is not None:
            result = strict_json(receipt.result_payload)
            binding = receipt.scenario.binding()
            policy = {k: binding[k] for k in ('costs', 'gates', 'resolution_risk', 'assumptions_id',
                'max_age_seconds', 'fee_model', 'execution_price_basis', 'full_size_required')}
            policy_hash = content_hash(policy)
            key = (d.team_id, d.model_id, d.protocol_version, policy_hash)
            groups.setdefault(key, dict(team_id=d.team_id, model_id=d.model_id,
                protocol_version=d.protocol_version, cost_policy_sha256=policy_hash,
                cost_policy=json_value(policy), attempt_count=0, settled_count=0,
                status_counts={k: 0 for k in _STATUSES}, binary_payout_sum=None,
                assumed_total_cost_upper_bound_sum=None, settled_pnl_lower_bound_sum=None))
            row.update(paper_input_sha256=checksum(encode_paper_scenario(receipt.scenario)),
                paper_result_sha256=checksum(receipt.result_payload), recorded_at=receipt.recorded_at,
                simulation_status=result['status'], simulation_reason_code=result['reason_code'],
                cost_policy_sha256=policy_hash)
            if d.reason_code not in ('scored', 'outcome_pending'):
                row['status'] = 'research_not_selected'
            elif result['status'] != 'paper_scenario_ready':
                row['status'] = 'paper_not_selected'
            elif d.reason_code == 'outcome_pending':
                row['status'] = 'outcome_pending'
            else:
                outcome = outcomes[d.condition_id]
                row['outcome_sha256'] = outcome.content_sha256
                review = reviews.get(d.condition_id)
                row['status'] = 'crypto_confirmation_required' if review is None else 'settled_simulation'
                if review is not None:
                    row.update(review_id=review.submission.review_id,
                        review_payload_sha256=checksum(encode_resolution(review.submission)),
                        amounts=_amounts(receipt, result, outcome, review, records[d.record_id]))
        rows.append(row)
        if key is not None:
            group = groups[key]
            group['attempt_count'] += 1
            group['status_counts'][row['status']] += 1
            if row['amounts'] is not None:
                group['settled_count'] += 1
                for total, name in (('binary_payout_sum', 'binary_payout'),
                        ('assumed_total_cost_upper_bound_sum', 'assumed_total_cost_upper_bound'),
                        ('settled_pnl_lower_bound_sum', 'settled_pnl_lower_bound')):
                    group[total] = (group[total] or Decimal(0)) + row['amounts'][name]
    return json_value(dict(schema_version='research-paper-settlement-v1', history=history.to_dict(),
        attempts=rows, groups=[groups[k] for k in sorted(groups)], attempt_count=len(rows),
        paper_evidence_count=len(papers), status_counts={k: sum(r['status'] == k for r in rows) for k in _STATUSES},
        input_sha256=content_hash(dict(history_sha256=history.input_sha256, rows=rows)),
        complete_visible_execution_history=True, single_database_snapshot=True,
        settled_subset_only=True, money_unit='binary_payout_units', costs_are_assumptions=True,
        source_authentication_performed=False, tariff_verified=False,
        commit_before_cutoff_verified=False, actual_account_pnl=None,
        paper_trades_created=0, business_writes_performed=False,
        portfolio_return_computed=False, strategy_validation_performed=False,
        paper_only=True, report_only=True, readonly=True))


def evaluate_settled_paper_with_psycopg(dsn: str, *, generated_at=None, max_records=10000,
                                      bucket_count=10, min_sample_count=30, min_bin_count=5):
    """Read all visible attempts, retained simulations and confirmations together.

    Historical cutoffs filter every source. Future cutoffs, incomplete claims,
    corrupt claimed proofs or excessive payloads abort; no retry/fallback/truncation.
    """
    at = None if generated_at is None else db._utc('generated_at', generated_at)
    integer('max_records', max_records, 1, db.MAX_RECORDS)
    db.ResearchProbabilityDiagnostics((), bucket_count, min_sample_count, min_bin_count)

    def operation(cursor):
        with localcontext(_CONTEXT):
            history = db._read_research_evaluation(cursor, at=at, max_records=max_records,
                bucket_count=bucket_count, min_sample_count=min_sample_count,
                min_bin_count=min_bin_count, require_execution_complete=True)
            budget = [db.MAX_READ_BYTES]
            papers = _paper_rows(cursor, history, max_records, budget)
            reviews = {}
            needed = {d.condition_id for d in history.decisions if d.reason_code == 'scored'
                and d.record_id in papers
                and strict_json(papers[d.record_id].result_payload)['status'] == 'paper_scenario_ready'}
            for outcome in history.outcomes:
                if outcome.condition_id in needed:
                    reviews[outcome.condition_id] = _crypto_review(cursor, outcome, history, budget)
            return _assemble(history, papers, reviews)
    return db._local_transaction(dsn, operation, readonly=True)


__all__ = ('evaluate_settled_paper_with_psycopg',)
