"""WP-01: compose existing discovery, rule/time gates and one fresh preview.

The returned dictionary is a display result, never an approval or executable
request. Original snapshot bytes live only in the existing in-memory objects.
No database, model, secret reader, new transport, ranking or pagination.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
import uuid

from polymarket_alpha_lab.research_crypto_discovery import CryptoDiscovery, _team, discover_crypto_markets
from polymarket_alpha_lab.research_crypto_launch import CryptoLaunchBlocked, CryptoResearchPreview, CryptoResearchSpec, market_terms
from polymarket_alpha_lab.research_crypto_contract_scope import assess_crypto_contract_scope
from polymarket_alpha_lab.research_crypto_observation import assess_crypto_observation_time
from polymarket_alpha_lab.research_crypto_launch_service import fetch_crypto_research_preview
from polymarket_alpha_lab.research_resolution import utc
from polymarket_alpha_lab.team_research_agent_types import integer, strict_json
from polymarket_alpha_lab.team_research_gamma import GammaResearchReader
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot, _timestamp

MAX_CANDIDATES = 10
# Only these complete, scoped eligibility decisions are negative evidence.
_REJECTED_MARKET = frozenset(('market_not_open', 'market_already_ended',
    'crypto_launch_cutoff_not_before_market_end'))
_UNUSABLE_MARKET = frozenset(('invalid_market_payload', 'missing_resolution_criteria',
    'market_identity_mismatch', 'invalid_market_time', 'market_context_stale',
    'market_context_from_future', 'crypto_launch_market_scope_mismatch',
    'crypto_launch_cutoff_elapsed', 'unsupported_market_outcomes'))


def _now() -> datetime:
    return datetime.now(UTC)


def _checkpoint(previous: datetime, cutoff: datetime) -> tuple[datetime, str | None]:
    at = utc('selection_clock', _now())
    reason = ('selection_clock_regressed' if at < previous
              else 'selection_cutoff_elapsed' if at >= cutoff else None)
    return at, reason


def _screen(spec: CryptoResearchSpec, snapshot: GammaMarketSnapshot, started: datetime, checked: datetime) -> dict:
    if not started <= utc('fetched_at', snapshot.fetched_at) <= checked:
        return dict(status='check_failed', reason_code='selection_snapshot_clock_invalid')
    try:
        terms = market_terms(spec, snapshot, checked)
    except CryptoLaunchBlocked as error:
        reason = str(error)
        if reason == 'market_not_open':
            payload = strict_json(snapshot.raw_json.decode('utf-8'))
            if (any(type(payload.get(key)) is not bool for key in ('active', 'closed'))
                    or 'archived' in payload and type(payload['archived']) is not bool):
                return dict(status='check_failed', reason_code='selection_market_status_unknown')
        if reason in _REJECTED_MARKET:
            return dict(status='market_blocked', reason_code=reason)
        return dict(status='check_failed', reason_code=reason if reason in _UNUSABLE_MARKET
                    else 'selection_metadata_invalid')
    scope = assess_crypto_contract_scope(spec.team_id, terms['question'], terms['resolution_criteria'])
    if not scope.new_launch_policy_eligible:
        return dict(status='scope_blocked', reason_code=scope.reason_code, contract_scope=scope.to_dict())
    timing = assess_crypto_observation_time(team_id=spec.team_id, question=terms['question'],
        resolution_criteria=terms['resolution_criteria'], market_slug=spec.market_slug,
        as_of=checked, forecast_cutoff_at=spec.forecast_cutoff_at,
        scheduled_end_at=_timestamp(terms['scheduled_end_at']))
    return dict(status='eligible_for_preview' if timing.new_launch_time_eligible else 'time_blocked',
        reason_code=timing.reason_code, terms_sha256=terms['terms_sha256'],
        contract_scope=scope.to_dict(), observation_schedule=timing.to_dict())


def _finish(report: dict, status: str) -> dict:
    report['status'] = status
    report['checked_count'] = len(report['checks'])
    report['unexamined_count'] = report['candidate_count'] - report['checked_count']
    report['failed_check_count'] = sum(c['status'] == 'check_failed' for c in report['checks'])
    report['eligibility_scan_complete'] = (status in ('ready_for_operator_review', 'no_eligible_in_search_page')
        and report['unexamined_count'] == report['failed_check_count'] == 0)
    report['metadata_get_attempts'] = report['checked_count']
    report['public_gets_upper_bound'] = (report['request_attempts'] + report['metadata_get_attempts']
                                        + 3 * report['preview_invocations'])
    return report


def select_supported_crypto(team_id: str, *, allow_public_fetch: bool = False,
                            max_candidates: int = 5, max_attempts: int = 1,
                            cutoff_lead_minutes: int = 30) -> dict:
    """Screen an ordered prefix of ONE search page, then at most ONE preview.

    Only search uses the existing explicit retry allowance. Metadata errors
    remain visible and can be followed by a DIFFERENT candidate, never a retry.
    Stop after the first eligible screen even if its full preview fails. That
    preview re-fetches Gamma and rechecks rules/time, so changed rules cannot
    inherit an earlier verdict. A fixed temporary cutoff never moves forward.

    Clock/cutoff checks precede every next stage, not each internal preview GET;
    this is not cancellation of in-flight requests or a total wall-clock limit.
    Unknown data is not negative evidence. No eligible result from this bounded
    page is not a statement about all markets. Caller must freshly construct an
    approved specification before using the existing research launcher later.
    """
    _team(team_id)
    integer('max_candidates', max_candidates, 1, MAX_CANDIDATES)
    integer('max_attempts', max_attempts, 1, 3)
    integer('cutoff_lead_minutes', cutoff_lead_minutes, 1, 60)
    if allow_public_fetch is not True:
        raise ValueError('selection_requires_public_fetch_opt_in')
    search = discover_crypto_markets(team_id, allow_public_fetch=True, max_attempts=max_attempts)
    if type(search) is not CryptoDiscovery or search.team_id != team_id:
        raise ValueError('selection_discovery_scope_invalid')
    search = replace(search)
    if len(search.attempt_codes) > max_attempts:
        raise ValueError('selection_discovery_budget_invalid')
    report = search.to_dict()
    report.pop('candidates')  # The original search bytes stay inside the discovery object.
    report.update(checks=[], preview=None, pending_spec=None, preview_invocations=0,
        preview_reason_code=None, selected_at=None, temporary_forecast_cutoff_at=None,
        configured_public_gets_ceiling=max_attempts + max_candidates + 3,
        max_candidates=max_candidates, selection_is_global_scan=False,
        source_suitability_review_required=True, selection_is_approval=False)
    if report['status'] == 'failed':
        return _finish(report, 'discovery_failed')
    candidates = search.candidates()
    if len({c.market_slug for c in candidates}) != len(candidates):
        return _finish(report, 'discovery_identity_conflict')
    selected = utc('selected_at', _now())
    cutoff = selected + timedelta(minutes=cutoff_lead_minutes)
    report.update(selected_at=selected.isoformat(), temporary_forecast_cutoff_at=cutoff.isoformat())
    if selected < search.observed_at:
        return _finish(report, 'selection_clock_regressed')
    if not candidates:
        return _finish(report, 'no_candidates_in_search_page')
    previous = selected
    reader = GammaResearchReader(allow_public_fetch=True)
    for candidate in candidates[:max_candidates]:
        started, stop = _checkpoint(previous, cutoff)
        if stop:
            return _finish(report, stop)
        spec = CryptoResearchSpec('selected-preview-' + uuid.uuid4().hex, team_id, candidate.condition_id,
            candidate.market_slug, cutoff, 'operator-model-not-selected')
        row = dict(condition_id=candidate.condition_id, market_slug=candidate.market_slug,
            started_at=started.isoformat(), checked_at=None, market_sha256=None)
        snapshot = None
        try:
            snapshot = reader.fetch(market_slug=spec.market_slug)
        except Exception:
            row.update(status='check_failed', reason_code='selection_market_fetch_failed')
        else:
            try:
                if type(snapshot) is not GammaMarketSnapshot:
                    raise ValueError('unexpected snapshot')
                snapshot = replace(snapshot)
                row['market_sha256'] = snapshot.content_sha256
            except (TypeError, ValueError):
                snapshot = None
                row.update(status='check_failed', reason_code='selection_snapshot_invalid')
        checked, stop = _checkpoint(started, cutoff)
        row['checked_at'] = checked.isoformat()
        if stop:
            # Preserve a transport failure if there was one, while stopping globally.
            if 'status' not in row:
                row.update(status='check_failed', reason_code=stop)
            report['checks'].append(row)
            return _finish(report, stop)
        if snapshot is not None:
            row.update(_screen(spec, snapshot, started, checked))
        report['checks'].append(row)
        previous = checked
        if row['status'] != 'eligible_for_preview':
            continue
        preview_started, stop = _checkpoint(previous, cutoff)
        if stop:
            return _finish(report, stop)
        report['preview_invocations'] = 1
        try:
            preview = fetch_crypto_research_preview(spec, allow_public_fetch=True)
            if type(preview) is not CryptoResearchPreview:
                raise ValueError('unexpected preview')
            preview = replace(preview)
            if preview.spec != spec or preview.selected_at < preview_started:
                raise ValueError('unexpected preview scope')
            final = preview.to_dict()
        except Exception:
            report['preview_reason_code'] = 'selection_preview_failed'
            return _finish(report, 'preview_failed')
        finished, stop = _checkpoint(preview.as_of, cutoff)
        report['preview'] = final
        if stop:
            return _finish(report, stop)
        if final['forecast_start_status'] != 'requires_operator_approval':
            return _finish(report, 'preview_no_longer_eligible')
        # This is a non-executable display of the current spec, not an approval
        # token, a serialized snapshot store or a request to the model factory.
        report['pending_spec'] = dict(record_id=spec.record_id, team_id=team_id,
            condition_id=spec.condition_id, market_slug=spec.market_slug,
            forecast_cutoff_at=cutoff.isoformat(), model_id=spec.model_id,
            lookback_hours=spec.lookback_hours, protocol_version=spec.protocol(),
            terms_sha256=final['terms_sha256'], source_use='research_reference_only',
            operator_approved=False, generated_at=finished.isoformat())
        return _finish(report, 'ready_for_operator_review')
    failed = any(c['status'] == 'check_failed' for c in report['checks'])
    return _finish(report, 'candidate_check_limit_reached' if len(candidates) > len(report['checks'])
                   else 'candidate_checks_failed' if failed else 'no_eligible_in_search_page')


__all__ = ('select_supported_crypto',)
