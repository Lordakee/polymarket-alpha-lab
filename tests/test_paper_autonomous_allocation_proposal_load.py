from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 6, 23, 14, 30, tzinfo=UTC)


@dataclass(frozen=True)
class FakePaperReport:
    name: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class FakeProposalConfig:
    config_version: str = "paper-autonomous-allocation-proposal-v0"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


@dataclass(frozen=True)
class FakeProposalReport:
    proposal_status: str = "pass"
    recommended_next_step: str = "review_paper_autonomous_allocation_proposal"
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


class FakeProposalReportSubclass(FakeProposalReport):
    pass


class NoSqlConnection:
    cursor_count = 0
    commit_count = 0
    rollback_count = 0
    write_count = 0

    def cursor(self) -> object:
        self.cursor_count += 1
        raise AssertionError("pure loader must not open cursors directly")

    def commit(self) -> None:
        self.commit_count += 1
        raise AssertionError("pure loader must not commit")

    def rollback(self) -> None:
        self.rollback_count += 1
        raise AssertionError("pure loader must not rollback")

    def write(self, *_args: object, **_kwargs: object) -> None:
        self.write_count += 1
        raise AssertionError("pure loader must not write")


def test_load_allocation_proposal_reads_required_reports_and_calls_reducer() -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_load import (
        load_paper_autonomous_allocation_proposal_report,
    )

    connection = NoSqlConnection()
    config = FakeProposalConfig()
    screening_latest = FakePaperReport("screening-latest")
    screening_older = FakePaperReport("screening-older")
    priority_latest = FakePaperReport("priority-latest")
    risk_latest = FakePaperReport("risk-latest")
    priority_older = FakePaperReport("priority-older")
    risk_older = FakePaperReport("risk-older")
    source_latest = FakePaperReport("source-latest")
    source_older = FakePaperReport("source-older")
    proposal = FakeProposalReport()
    calls: list[tuple[str, dict[str, Any]]] = []

    def screening_gate_loader(
        received_connection: object,
        *,
        options: object,
    ) -> tuple[FakePaperReport, ...]:
        calls.append(
            (
                "screening",
                {
                    "connection": received_connection,
                    "limit": getattr(options, "limit"),
                    "table_name": getattr(options, "table_name"),
                },
            ),
        )
        return (screening_latest, screening_older)

    def decision_support_loader(
        received_connection: object,
        **kwargs: Any,
    ) -> tuple[tuple[FakePaperReport, FakePaperReport], ...]:
        calls.append(("decision_support", {"connection": received_connection, **kwargs}))
        return ((priority_latest, risk_latest), (priority_older, risk_older))

    def source_queue_loader(
        received_connection: object,
        **kwargs: Any,
    ) -> tuple[FakePaperReport, ...]:
        calls.append(("source_queue", {"connection": received_connection, **kwargs}))
        return (source_latest, source_older)

    def proposal_report_builder(**kwargs: Any) -> FakeProposalReport:
        calls.append(("builder", dict(kwargs)))
        assert kwargs == {
            "screening_gate_report": screening_latest,
            "priority_report": priority_latest,
            "risk_report": risk_latest,
            "source_queue_reports": (source_latest, source_older),
            "config": config,
            "generated_at": GENERATED_AT,
        }
        return proposal

    loaded = load_paper_autonomous_allocation_proposal_report(
        connection,
        screening_gate_limit=3,
        screening_gate_table_name="paper_autonomous_screening_gate_reports",
        action_gated_queue_decision_support_limit=3,
        action_gated_queue_decision_support_table_name=(
            "paper_action_gated_queue_decision_support_reports"
        ),
        source_queue_limit=3,
        source_queue_table_name="paper_action_gated_queue_reports",
        config=config,
        generated_at=GENERATED_AT,
        screening_gate_loader=screening_gate_loader,
        action_gated_queue_decision_support_loader=decision_support_loader,
        source_queue_loader=source_queue_loader,
        proposal_report_builder=proposal_report_builder,
        proposal_report_type=FakeProposalReport,
    )

    assert loaded is proposal
    assert calls[:3] == [
        (
            "screening",
            {
                "connection": connection,
                "limit": 3,
                "table_name": "paper_autonomous_screening_gate_reports",
            },
        ),
        (
            "decision_support",
            {
                "connection": connection,
                "risk_status": None,
                "risk_config_version": None,
                "limit": 3,
                "table_name": "paper_action_gated_queue_decision_support_reports",
            },
        ),
        (
            "source_queue",
            {
                "connection": connection,
                "source_config_version": None,
                "action_status": None,
                "limit": 3,
                "table_name": "paper_action_gated_queue_reports",
            },
        ),
    ]
    assert connection.cursor_count == 0
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.write_count == 0


@pytest.mark.parametrize(
    ("bad_field", "message"),
    (
        ("screening_gate_report", "screening_gate_report"),
        ("priority_report", "decision_support_reports.0.0"),
        ("risk_report", "decision_support_reports.0.1"),
        ("source_queue_report", "source_queue_reports.0"),
        ("config", "config"),
    ),
)
def test_load_allocation_proposal_rejects_non_hard_flagged_inputs_before_reducer(
    bad_field: str,
    message: str,
) -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_load import (
        load_paper_autonomous_allocation_proposal_report,
    )

    good = FakePaperReport("good")
    bad = FakePaperReport("bad", readonly=False)
    config: object = FakeProposalConfig()
    if bad_field == "config":
        config = FakeProposalConfig(readonly=False)
    builder_calls = 0

    def proposal_report_builder(**_kwargs: Any) -> FakeProposalReport:
        nonlocal builder_calls
        builder_calls += 1
        raise AssertionError("reducer must not run after hard-flag rejection")

    with pytest.raises(ValueError, match=message):
        load_paper_autonomous_allocation_proposal_report(
            NoSqlConnection(),
            screening_gate_limit=1,
            screening_gate_table_name="screening_reports",
            action_gated_queue_decision_support_limit=1,
            action_gated_queue_decision_support_table_name="decision_support_reports",
            source_queue_limit=1,
            source_queue_table_name="source_queue_reports",
            config=config,
            generated_at=GENERATED_AT,
            screening_gate_loader=lambda _connection, **_kwargs: (
                bad if bad_field == "screening_gate_report" else good,
            ),
            action_gated_queue_decision_support_loader=lambda _connection, **_kwargs: (
                (
                    bad if bad_field == "priority_report" else good,
                    bad if bad_field == "risk_report" else good,
                ),
            ),
            source_queue_loader=lambda _connection, **_kwargs: (
                bad if bad_field == "source_queue_report" else good,
            ),
            proposal_report_builder=proposal_report_builder,
            proposal_report_type=FakeProposalReport,
        )

    assert builder_calls == 0


@pytest.mark.parametrize(
    ("decision_support_reports", "source_queue_reports", "message"),
    (
        ((), (FakePaperReport("source"),), "decision-support reports are required"),
        (
            ((FakePaperReport("priority"),),),
            (FakePaperReport("source"),),
            "latest decision-support report must be a priority/risk pair",
        ),
        (
            ((FakePaperReport("priority"), FakePaperReport("risk")),),
            (),
            "source queue reports are required",
        ),
    ),
)
def test_load_allocation_proposal_requires_decision_support_pair_and_sources(
    decision_support_reports: tuple[object, ...],
    source_queue_reports: tuple[object, ...],
    message: str,
) -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_load import (
        load_paper_autonomous_allocation_proposal_report,
    )

    with pytest.raises(ValueError, match=message):
        load_paper_autonomous_allocation_proposal_report(
            NoSqlConnection(),
            screening_gate_limit=1,
            screening_gate_table_name="screening_reports",
            action_gated_queue_decision_support_limit=1,
            action_gated_queue_decision_support_table_name="decision_support_reports",
            source_queue_limit=1,
            source_queue_table_name="source_queue_reports",
            config=FakeProposalConfig(),
            generated_at=GENERATED_AT,
            screening_gate_loader=lambda _connection, **_kwargs: (
                FakePaperReport("screening"),
            ),
            action_gated_queue_decision_support_loader=lambda _connection, **_kwargs: (
                decision_support_reports
            ),
            source_queue_loader=lambda _connection, **_kwargs: source_queue_reports,
            proposal_report_builder=lambda **_kwargs: FakeProposalReport(),
            proposal_report_type=FakeProposalReport,
        )


def test_load_allocation_proposal_requires_exact_proposal_report_type() -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_load import (
        load_paper_autonomous_allocation_proposal_report,
    )

    with pytest.raises(ValueError, match="must be a FakeProposalReport"):
        load_paper_autonomous_allocation_proposal_report(
            NoSqlConnection(),
            screening_gate_limit=1,
            screening_gate_table_name="screening_reports",
            action_gated_queue_decision_support_limit=1,
            action_gated_queue_decision_support_table_name="decision_support_reports",
            source_queue_limit=1,
            source_queue_table_name="source_queue_reports",
            config=FakeProposalConfig(),
            generated_at=GENERATED_AT,
            screening_gate_loader=lambda _connection, **_kwargs: (
                FakePaperReport("screening"),
            ),
            action_gated_queue_decision_support_loader=lambda _connection, **_kwargs: (
                (FakePaperReport("priority"), FakePaperReport("risk")),
            ),
            source_queue_loader=lambda _connection, **_kwargs: (
                FakePaperReport("source"),
            ),
            proposal_report_builder=lambda **_kwargs: FakeProposalReportSubclass(),
            proposal_report_type=FakeProposalReport,
        )


def test_load_allocation_proposal_default_config_uses_conservative_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from polymarket_alpha_lab import paper_autonomous_allocation_proposal_load as load_module

    captured: dict[str, Any] = {}

    class FakeAllocationConfig:
        def __init__(
            self,
            *,
            config_version: str,
            total_paper_budget: object,
            max_paper_notional_per_market: object,
            max_paper_notional_per_event: object,
            max_paper_notional_per_theme: object,
            max_paper_notional_per_correlation_group: object,
        ) -> None:
            captured["allocation_config_values"] = {
                "config_version": config_version,
                "total_paper_budget": total_paper_budget,
                "max_paper_notional_per_market": max_paper_notional_per_market,
                "max_paper_notional_per_event": max_paper_notional_per_event,
                "max_paper_notional_per_theme": max_paper_notional_per_theme,
                "max_paper_notional_per_correlation_group": (
                    max_paper_notional_per_correlation_group
                ),
            }

    class FakeDefaultConfig(FakeProposalConfig):
        def __init__(self, *, config_version: str, allocation_config: object) -> None:
            super().__init__(config_version=config_version)
            captured["default_config"] = self
            captured["config_version"] = config_version
            captured["allocation_config"] = allocation_config

    monkeypatch.setattr(
        load_module,
        "_load_default_proposal_config_type",
        lambda: FakeDefaultConfig,
    )
    monkeypatch.setattr(
        load_module,
        "_load_default_allocation_config_type",
        lambda: FakeAllocationConfig,
    )
    monkeypatch.setattr(
        load_module,
        "_load_default_config_version",
        lambda: "paper-autonomous-allocation-proposal-v0",
    )

    result = load_module.load_paper_autonomous_allocation_proposal_report(
        NoSqlConnection(),
        screening_gate_limit=1,
        screening_gate_table_name="screening_reports",
        action_gated_queue_decision_support_limit=1,
        action_gated_queue_decision_support_table_name="decision_support_reports",
        source_queue_limit=1,
        source_queue_table_name="source_queue_reports",
        generated_at=GENERATED_AT,
        screening_gate_loader=lambda _connection, **_kwargs: (
            FakePaperReport("screening"),
        ),
        action_gated_queue_decision_support_loader=lambda _connection, **_kwargs: (
            (FakePaperReport("priority"), FakePaperReport("risk")),
        ),
        source_queue_loader=lambda _connection, **_kwargs: (
            FakePaperReport("source"),
        ),
        proposal_report_builder=lambda **kwargs: captured.setdefault(
            "builder_config",
            kwargs["config"],
        )
        and FakeProposalReport(),
        proposal_report_type=FakeProposalReport,
    )

    assert type(result) is FakeProposalReport
    assert captured["builder_config"] is captured["default_config"]
    assert captured["config_version"] == "paper-autonomous-allocation-proposal-v0"
    assert captured["allocation_config_values"] == {
        "config_version": "paper-recommendation-allocation-v0",
        "total_paper_budget": Decimal("100.000000"),
        "max_paper_notional_per_market": Decimal("25.000000"),
        "max_paper_notional_per_event": Decimal("25.000000"),
        "max_paper_notional_per_theme": Decimal("25.000000"),
        "max_paper_notional_per_correlation_group": Decimal("25.000000"),
    }
    assert isinstance(captured["allocation_config"], FakeAllocationConfig)
