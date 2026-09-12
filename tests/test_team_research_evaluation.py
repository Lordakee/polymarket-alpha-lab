"""Real Agent/intake integration with synthetic evidence and outcome records."""
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import json

import pytest

from polymarket_alpha_lab.team_research_agent_types import ResearchEvidence, ResearchModelReply, ResearchToolCall
from polymarket_alpha_lab.team_research_intake import GammaMarketSnapshot
from polymarket_alpha_lab.team_research_market_pipeline import run_team_research_from_market_snapshot
from polymarket_alpha_lab.team_research_evaluation import (
    ResearchEvaluationRecord as Record, ResearchEvaluationOutcome as Outcome,
    ResearchEvaluationReport as Report,
)
from polymarket_alpha_lab.team_taxonomy import TEAM_IDS

NOW = datetime(2026, 9, 12, tzinfo=UTC)
LATER = NOW + timedelta(hours=4)


def record(record_id="r1", condition="c1", team="crypto_eth", p="0.7", **changes):
    class Model:
        calls = 0
        def complete(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                name, args = "read_evidence", {"source_id": "source-1"}
            else:
                name, args = "finish_research", dict(probability_yes=p, confidence="0.1",
                    summary="PRIVATE-SUMMARY-SENTINEL", source_ids=["source-1"])
            return ResearchModelReply((ResearchToolCall(f"call-{self.calls}", name, json.dumps(args)),), 1)
    market = GammaMarketSnapshot("market-" + condition, NOW, json.dumps(dict(
        conditionId=condition, slug="market-" + condition, question="Synthetic event?",
        description="Synthetic YES/NO settlement rules.", active=True, closed=False,
        outcomes=["Yes", "No"], endDate=(NOW + timedelta(hours=2)).isoformat(),
    )).encode())
    evidence = ResearchEvidence("source-1", team, condition, "Synthetic source",
        "PRIVATE-EVIDENCE-SENTINEL", "synthetic:source", NOW)
    run = run_team_research_from_market_snapshot(market, task_id="task-" + record_id,
        team_id=team, condition_id=condition, as_of=NOW, evidence=(evidence,), model_factory=lambda _: Model())
    assert run.research.status == "completed"
    return replace(Record(record_id, "synthetic-model-v1", "protocol-v1", NOW + timedelta(seconds=1), run), **changes)


def outcome(condition="c1", **changes):
    return replace(Outcome(condition, "market-" + condition, NOW + timedelta(hours=1),
        NOW + timedelta(hours=2), NOW + timedelta(hours=3), True,
        "synthetic:verified-resolution", "a" * 64), **changes)


def reasons(report):
    return {row.record_id: row.reason_code for row in report.decisions}


def unsuccessful(item, status):
    run = item.run
    if status == "intake_blocked":
        intake = replace(run.intake, status="blocked", reason_code="no_eligible_evidence", task=None, source_receipts=())
        return replace(item, run=replace(run, intake=intake, research=None))
    research = replace(run.research, status=status,
        reason_code="model_failed" if status == "failed" else "model_call_limit",
        probability_yes=None, confidence=None, summary="", source_ids=())
    return replace(item, run=replace(run, research=research))


@pytest.mark.parametrize("team", TEAM_IDS)
def test_real_research_result_is_scored_canonical_yes_not_confidence(team):
    item = record(team=team)
    report = Report((item,), (outcome(),), LATER)
    assert reasons(report) == {"r1": "scored"}
    group, = report.groups
    assert group.team_id == team and group.scores.mean_brier_score == Decimal("0.09")
    assert group.scores.bins[7].count == 1  # Confidence is 0.1, not the scoring probability.
    assert group.selected_count == group.attempted_count == 1
    assert report.decisions[0].record_sha256 == item.content_sha256
    assert report.decisions[0].outcome_sha256 == outcome().content_sha256


def test_first_attempt_not_best_probability_and_input_order_is_irrelevant():
    early = record("early", p="0.1")
    late = record("late", p="0.99", recorded_at=NOW + timedelta(seconds=2))
    first = Report((early, late), (outcome(),), LATER)
    second = Report((late, early), (outcome(),), LATER)
    assert first == second
    assert first.input_sha256 == second.input_sha256
    assert reasons(first) == {"early": "scored", "late": "later_attempt"}
    assert first.groups[0].scores.mean_brier_score == Decimal("0.81")
    assert first.groups[0].attempted_count == 2 and first.groups[0].selected_count == 1
    changed = Report((early, late), (outcome(actual_yes=False),), LATER)
    assert reasons(changed) == reasons(first)  # Changing the outcome does not change selection.


@pytest.mark.parametrize("status", ("failed", "blocked", "intake_blocked"))
def test_failed_first_attempt_is_not_replaced_with_a_successful_retry(status):
    early = unsuccessful(record("early"), status)
    late = record("late", recorded_at=NOW + timedelta(seconds=2))
    report = Report((early, late), (outcome(),), LATER)
    group, = report.groups
    assert group.failed_or_blocked_count == 1
    assert group.scores.sample_count == 0 and group.scores.mean_brier_score is None
    assert reasons(report)["late"] == "later_attempt"


@pytest.mark.parametrize("outcomes", ((), (outcome(recorded_at=LATER + timedelta(seconds=1)),)))
def test_missing_or_future_recorded_resolution_remains_pending(outcomes):
    report = Report((record(),), outcomes, LATER)
    assert reasons(report)["r1"] == "outcome_pending"
    assert report.decisions[0].outcome_sha256 is None
    assert report.groups[0].outcome_pending_count == 1
    assert report.groups[0].scores.mean_brier_score is None


@pytest.mark.parametrize("delta", (timedelta(0), timedelta(microseconds=1), timedelta(hours=2)))
def test_capture_at_or_after_forecast_cutoff_never_scores_even_with_old_as_of(delta):
    item = record(recorded_at=outcome().forecast_cutoff_at + delta)
    assert item.run.intake.as_of < outcome().forecast_cutoff_at
    report = Report((item,), (outcome(),), LATER)
    assert reasons(report)["r1"] == "not_pre_outcome"
    assert report.groups[0].late_count == 1 and report.groups[0].scores.sample_count == 0


def test_last_microsecond_before_cutoff_scores():
    item = record(recorded_at=outcome().forecast_cutoff_at - timedelta(microseconds=1))
    assert reasons(Report((item,), (outcome(),), LATER))["r1"] == "scored"


def test_future_predictions_are_not_in_visible_denominators():
    item = record(recorded_at=LATER + timedelta(seconds=1))
    report = Report((item,), (outcome(),), LATER)
    assert reasons(report)["r1"] == "not_yet_recorded" and report.groups == ()
    assert report.orphan_outcome_count == 1


def test_team_model_protocol_cohorts_are_not_pooled():
    items = (record("a"), record("b", team="crypto_btc"), record("c", model_id="other-model"),
             record("d", protocol_version="protocol-v2"))
    report = Report(items, (outcome(),), LATER)
    assert len(report.groups) == 4
    assert all(group.scores.sample_count == 1 for group in report.groups)
    assert not hasattr(report, "mean_brier_score")


def test_completed_future_and_failed_counts_partition_selected():
    items = (record("a", "c1"), record("b", "c2"), unsuccessful(record("c", "c3"), "failed"),
             record("d", "c4", recorded_at=NOW + timedelta(hours=1)))
    report = Report(items, (outcome("c1"), outcome("c4")), LATER)
    group, = report.groups
    assert (group.selected_count, group.scores.sample_count, group.outcome_pending_count,
            group.failed_or_blocked_count, group.late_count) == (4, 1, 1, 1, 1)


def test_duplicates_conflicts_and_ambiguous_selection_are_rejected():
    item = record()
    for records, outcomes in (
        ((item, item), ()), ((item,), (outcome(), outcome())),
        ((item,), (outcome(), outcome(actual_yes=False))),
        ((item, replace(item, record_id="alias")), ()),
        ((item, record("r2")), ()),  # same group/condition/capture time
        ((item,), (outcome(market_slug="wrong-market"),)),
    ):
        with pytest.raises(ValueError):
            Report(records, outcomes, LATER)


def test_empty_report_and_unmatched_outcome_accounting():
    report = Report((), (outcome(),), LATER)
    assert report.groups == () and report.decisions == () and report.orphan_outcome_count == 1
    assert Report((), (), LATER).to_dict()["groups"] == []


def test_content_binding_covers_inputs_outputs_capture_model_protocol_and_resolution():
    item = record()
    for altered in (replace(item, recorded_at=NOW + timedelta(seconds=2)),
        replace(item, model_id="different"), replace(item, protocol_version="different"),
        replace(item, run=replace(item.run, research=replace(item.run.research, probability_yes=Decimal("0.8")))),
        replace(item, run=replace(item.run, research=replace(item.run.research, summary="Different summary")))):
        assert altered.content_sha256 != item.content_sha256
    actual = outcome()
    assert replace(actual, actual_yes=False).content_sha256 != actual.content_sha256
    assert replace(actual, source_content_sha256="b" * 64).content_sha256 != actual.content_sha256
    assert Report((item,), (actual,), LATER).input_sha256 != Report((item,), (actual,), LATER, bucket_count=5).input_sha256


def test_equivalent_timezones_have_same_hash_and_scores():
    item = record()
    zone = timezone(timedelta(hours=8))
    moved = replace(item, recorded_at=item.recorded_at.astimezone(zone))
    assert moved.content_sha256 == item.content_sha256
    a = Report((item,), (outcome(),), LATER)
    b = Report((moved,), (outcome(),), LATER.astimezone(zone))
    assert a.input_sha256 == b.input_sha256 and a.groups == b.groups


def test_no_source_text_or_model_summary_in_public_report_or_repr():
    report = Report((record(),), (outcome(),), LATER)
    encoded = json.dumps(report.to_dict(), allow_nan=False)
    for value in (encoded, repr(report)):
        assert "PRIVATE-EVIDENCE-SENTINEL" not in value
        assert "PRIVATE-SUMMARY-SENTINEL" not in value
    assert '"mean_brier_score": "0.090000000000"' in encoded
    assert report.paper_only is report.report_only is report.readonly is True


def test_json_handles_wrong_certainty_without_nonfinite_numbers():
    report = Report((record(p="0"),), (outcome(),), LATER)
    encoded = json.dumps(report.to_dict(), allow_nan=False)
    assert '"log_loss_status": "infinite"' in encoded
    assert '"mean_log_loss": null' in encoded


def test_nested_input_is_copied_and_report_export_recomputes_metrics():
    item = record()
    report = Report((item,), (outcome(),), LATER)
    object.__setattr__(item.run.research, "probability_yes", Decimal("0.01"))
    assert report.groups[0].scores.mean_brier_score == Decimal("0.09")
    object.__setattr__(report.groups[0].scores, "mean_brier_score", Decimal(0))
    assert report.to_dict()["groups"][0]["scores"]["mean_brier_score"] == "0.090000000000"


@pytest.mark.parametrize("changes", ({"recorded_at": NOW - timedelta(seconds=1)},
    {"recorded_at": NOW.replace(tzinfo=None)}, {"model_id": ""}, {"protocol_version": "bad version"},
    {"record_id": ""}, {"paper_only": False}, {"report_only": 1}, {"readonly": False}))
def test_invalid_record(changes):
    with pytest.raises(ValueError):
        record(**changes)


@pytest.mark.parametrize("changes", ({"actual_yes": 1}, {"actual_yes": None}, {"actual_yes": "yes"},
    {"source_reference": ""}, {"source_content_sha256": "bad"}, {"resolved_at": NOW},
    {"recorded_at": NOW}, {"forecast_cutoff_at": LATER}, {"readonly": False},
    {"resolved_at": NOW.replace(tzinfo=None)}))
def test_invalid_outcome(changes):
    with pytest.raises(ValueError):
        outcome(**changes)


def test_malformed_input_is_redacted_and_not_partially_scored():
    item = record()
    object.__setattr__(item.run.research, "readonly", False)
    with pytest.raises(ValueError, match="invalid research evaluation input"):
        Report((item,), (outcome(),), LATER)
    for records, outcomes in (([], ()), ((), []), ((object(),), ())):
        with pytest.raises(ValueError):
            Report(records, outcomes, LATER)


def test_probability_arithmetic_stays_correct_under_hostile_context():
    from decimal import Inexact, localcontext
    item = record(p="0.333333")
    expected = Report((item,), (outcome(),), LATER).to_dict()
    with localcontext() as ctx:
        ctx.prec = 2
        ctx.traps[Inexact] = True
        assert Report((item,), (outcome(),), LATER).to_dict() == expected


def test_export_rejects_mutated_hard_flags_and_derived_fields_not_settable():
    report = Report((record(),), (outcome(),), LATER)
    with pytest.raises((TypeError, ValueError)):
        replace(report, groups=())
    object.__setattr__(report.records[0].run.research, "paper_only", False)
    with pytest.raises(ValueError, match="invalid research evaluation input"):
        report.to_dict()


def test_outcome_wrong_certainty_and_canonical_zero_are_not_coerced():
    report = Report((record(p="0"),), (outcome(actual_yes=False),), LATER)
    assert report.groups[0].scores.mean_brier_score == 0
    assert report.groups[0].scores.mean_log_loss == 0
    assert report.groups[0].scores.log_loss_status == "finite"


def test_source_and_question_mutations_change_input_binding():
    from polymarket_alpha_lab.team_research_intake import ResearchSourceReceipt, evidence_content_sha256
    item = record()
    task = item.run.intake.task
    altered = replace(task.evidence[0], text="Changed evidence.")
    receipt = ResearchSourceReceipt(altered.source_id, evidence_content_sha256(altered), altered.reference, altered.observed_at)
    changed_intake = replace(item.run.intake, task=replace(task, evidence=(altered,)), source_receipts=(receipt,))
    changed = replace(item, run=replace(item.run, intake=changed_intake))
    assert changed.content_sha256 != item.content_sha256
    assert Report((changed,), (outcome(),), LATER).input_sha256 != Report((item,), (outcome(),), LATER).input_sha256


def test_cross_source_market_run_is_directly_accepted():
    # Exercise the actual two-source collector/check/intake/Agent composition.
    from polymarket_alpha_lab.team_research_cross_source_pipeline import run_cross_source_crypto_research
    from polymarket_alpha_lab.team_research_crypto_candles import CryptoCandleWindow, CoinbaseCandleSnapshot
    from polymarket_alpha_lab.team_research_kraken_candles import KrakenCandleSnapshot
    window = CryptoCandleWindow("ETH-USD", NOW - timedelta(hours=2), NOW - timedelta(hours=1))
    stamp = int(window.start.timestamp())
    coinbase = CoinbaseCandleSnapshot(window, NOW, json.dumps([[stamp, 99, 102, 100, 101, 1]]).encode())
    kraken = KrakenCandleSnapshot(window, NOW, json.dumps({"error": [], "result": {
        "XETHZUSD": [[stamp, "100", "102", "99", "101", "100", "1", 1],
                       [int(NOW.timestamp()), "100", "102", "99", "101", "100", "1", 1]],
        "last": int(NOW.timestamp()),
    }}).encode())
    market = GammaMarketSnapshot("market-c1", NOW, json.dumps(dict(conditionId="c1", slug="market-c1",
        question="Synthetic?", description="Synthetic criteria", active=True, closed=False,
        outcomes=["Yes", "No"], endDate=(NOW + timedelta(hours=1)).isoformat())).encode())
    class Model:
        step = 0
        source_ids = ()
        def complete(self, *, messages_json, **kwargs):
            self.step += 1
            if self.step == 1:
                name, args = "search_evidence", {"query": "*"}
            elif self.step == 2:
                self.source_ids = tuple(row["source_id"] for row in json.loads(json.loads(messages_json)[-1]["content"])["sources"])
                return ResearchModelReply(tuple(ResearchToolCall(f"read-{i}", "read_evidence", json.dumps({"source_id": value}))
                    for i, value in enumerate(self.source_ids)), 1)
            else:
                name, args = "finish_research", dict(probability_yes="0.7", confidence="0.1", summary="Synthetic.", source_ids=list(self.source_ids))
            return ResearchModelReply((ResearchToolCall(f"call-{self.step}", name, json.dumps(args)),), 1)
    run = run_cross_source_crypto_research(market, coinbase, kraken, task_id="cross-source-eval",
        team_id="crypto_eth", condition_id="c1", as_of=NOW, model_factory=lambda _: Model())
    assert run.market_run.research.status == "completed"
    item = Record("cross-source-eval", "scripted", "two-sources-v1", NOW + timedelta(seconds=1), run.market_run)
    report = Report((item,), (outcome(),), LATER)
    assert report.groups[0].scores.mean_brier_score == Decimal("0.09")
    assert len(report.records[0].run.intake.source_receipts) == 2


def test_synthetic_demo_no_network_or_external_process_and_explicit_labels(capsys):
    import runpy
    import subprocess
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    # The child guards the whole import + execution path, not just a fake transport.
    code = """
import sys, runpy
def guard(event, args):
    if event.startswith('socket.') or event in ('subprocess.Popen', 'os.system'):
        raise RuntimeError('unexpected external I/O')
sys.addaudithook(guard)
runpy.run_path('scripts/run_research_evaluation_demo.py', run_name='__main__')
"""
    result = subprocess.run([sys.executable, "-c", code], cwd=root, capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)
    assert payload["synthetic_demo"] is True
    assert payload["public_network_called"] is payload["live_model_called"] is False
    group, = payload["evaluation"]["groups"]
    assert group["scores"]["mean_brier_score"] == "0.210000000000"
    assert group["scores"]["bins"][7]["observed_yes_rate"] == "0.700000000000"
    assert group["scores"]["sample_status"] == "insufficient_sample"
