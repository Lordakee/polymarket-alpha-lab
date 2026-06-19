from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta, timezone

import pytest

from polymarket_alpha_lab.paper_recommendation_manifest import (
    PaperRecommendationManifestConfig,
    PaperRecommendationManifestItem,
    PaperRecommendationManifestReport,
    build_paper_recommendation_manifest_report,
)


GENERATED_AT = datetime(2026, 6, 19, 12, 0, tzinfo=UTC)
EARLIER_AT = datetime(2026, 6, 19, 11, 30, tzinfo=UTC)
CONFIG = PaperRecommendationManifestConfig(
    config_version="recommendation-manifest-v0",
    required_report_names=(
        "allocation",
        "gate_summary",
        "risk_budget",
    ),
)


class _DatetimeSubclass(datetime):
    pass


class _IntSubclass(int):
    pass


class _StringSubclass(str):
    pass


@dataclass(frozen=True)
class SuppliedReportShape:
    report_name: str
    config_version: str
    generated_at: datetime
    row_count: int
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def _item(
    report_name: str,
    *,
    config_version: str | None = None,
    generated_at: datetime = EARLIER_AT,
    row_count: int = 1,
    status: str = "pass",
    reason_codes: tuple[str, ...] | None = None,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PaperRecommendationManifestItem:
    if config_version is None:
        config_version = f"{report_name}-v1"
    if reason_codes is None:
        reason_codes = (f"{report_name}_present",)
    return PaperRecommendationManifestItem(
        report_name=report_name,
        config_version=config_version,
        generated_at=generated_at,
        row_count=row_count,
        status=status,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _report(
    items: tuple[object, ...],
    *,
    config: PaperRecommendationManifestConfig = CONFIG,
    generated_at: datetime = GENERATED_AT,
) -> PaperRecommendationManifestReport:
    return build_paper_recommendation_manifest_report(
        items,
        config=config,
        generated_at=generated_at,
    )


def test_manifest_summarizes_supplied_reports_and_sorts_items_by_report_name():
    report = _report(
        (
            _item(
                "risk_budget",
                generated_at=datetime(2026, 6, 19, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
                row_count=3,
                status="watch",
                reason_codes=("near_total_utilization_cap",),
            ),
            _item(
                "allocation",
                generated_at=EARLIER_AT,
                row_count=2,
                status="pass",
                reason_codes=("allocation_present",),
            ),
            _item(
                "gate_summary",
                generated_at=EARLIER_AT,
                row_count=4,
                status="blocked",
                reason_codes=("cap_exceeded",),
            ),
        ),
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "recommendation-manifest-v0"
    assert report.item_count == 3
    assert report.pass_count == 1
    assert report.watch_count == 1
    assert report.blocked_count == 1
    assert report.missing_required_reports == ()
    assert report.manifest_status == "blocked"
    assert report.reason_codes == ("supplied_report_blocked", "supplied_report_watch")
    assert tuple(item.report_name for item in report.items) == (
        "allocation",
        "gate_summary",
        "risk_budget",
    )
    assert report.items[2].generated_at == GENERATED_AT
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_manifest_blocks_when_required_reports_are_missing():
    report = _report(
        (
            _item("allocation", status="pass"),
            _item("risk_budget", status="pass"),
        ),
    )

    assert report.item_count == 2
    assert report.pass_count == 2
    assert report.watch_count == 0
    assert report.blocked_count == 0
    assert report.missing_required_reports == ("gate_summary",)
    assert report.manifest_status == "blocked"
    assert report.reason_codes == ("missing_required_reports",)


def test_manifest_watches_when_no_missing_or_blocked_reports_but_any_supplied_report_watches():
    report = _report(
        (
            _item("allocation", status="pass"),
            _item("gate_summary", status="pass"),
            _item(
                "risk_budget",
                status="watch",
                reason_codes=("near_total_utilization_cap",),
            ),
        ),
    )

    assert report.missing_required_reports == ()
    assert report.manifest_status == "watch"
    assert report.reason_codes == ("supplied_report_watch",)


def test_manifest_passes_when_all_required_reports_are_present_and_pass():
    report = _report(
        (
            _item("allocation", status="pass"),
            _item("gate_summary", status="pass"),
            _item("risk_budget", status="pass"),
        ),
    )

    assert report.manifest_status == "pass"
    assert report.reason_codes == ("manifest_passed",)


def test_manifest_rejects_duplicate_supplied_report_names():
    with pytest.raises(ValueError, match="report_name"):
        _report(
            (
                _item("allocation", config_version="allocation-v1"),
                _item("allocation", config_version="allocation-v2"),
            ),
            config=PaperRecommendationManifestConfig(
                config_version="manifest-v0",
                required_report_names=("allocation",),
            ),
        )


def test_manifest_accepts_supplied_input_shapes_without_exact_type_coupling():
    report = _report(
        (
            SuppliedReportShape(
                report_name="risk_budget",
                config_version="risk-budget-v1",
                generated_at=EARLIER_AT,
                row_count=3,
                status="pass",
                reason_codes=("risk_budget_present",),
            ),
        ),
        config=PaperRecommendationManifestConfig(
            config_version="manifest-v0",
            required_report_names=("risk_budget",),
        ),
    )

    assert report.items == (
        PaperRecommendationManifestItem(
            report_name="risk_budget",
            config_version="risk-budget-v1",
            generated_at=EARLIER_AT,
            row_count=3,
            status="pass",
            reason_codes=("risk_budget_present",),
        ),
    )
    assert report.manifest_status == "pass"


def test_manifest_validates_config_items_counts_statuses_reasons_and_utc():
    with pytest.raises(ValueError, match="config_version"):
        PaperRecommendationManifestConfig(
            config_version=" recommendation-manifest-v0",
            required_report_names=("allocation",),
        )
    with pytest.raises(ValueError, match="required_report_names"):
        PaperRecommendationManifestConfig(
            config_version="recommendation-manifest-v0",
            required_report_names=("allocation", "allocation"),
        )
    config = PaperRecommendationManifestConfig(
        config_version="recommendation-manifest-v0",
        required_report_names=("risk_budget", "allocation"),
    )
    assert config.required_report_names == ("allocation", "risk_budget")
    with pytest.raises(ValueError, match="generated_at"):
        _item("allocation", generated_at=_DatetimeSubclass(2026, 6, 19, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="row_count"):
        _item("allocation", row_count=_IntSubclass(1))
    with pytest.raises(ValueError, match="status"):
        _item("allocation", status="skip")
    with pytest.raises(ValueError, match="reason_codes"):
        _item("allocation", reason_codes=())
    with pytest.raises(ValueError, match="report_name"):
        _item(_StringSubclass("allocation"))
    with pytest.raises(FrozenInstanceError):
        replace(_item("allocation"), row_count=2).row_count = 3  # type: ignore[misc]
    with pytest.raises(ValueError, match="generated_at"):
        _report((_item("allocation"),), generated_at="bad")  # type: ignore[arg-type]


def test_manifest_validates_hard_safety_flags_on_items_and_report():
    valid = _item("allocation")

    with pytest.raises(ValueError, match="manifest item must be paper_only"):
        _report((replace(valid, paper_only=False),))
    with pytest.raises(ValueError, match="manifest item must be report_only"):
        _report((replace(valid, report_only=False),))
    with pytest.raises(ValueError, match="manifest item must be readonly"):
        _report((replace(valid, readonly=False),))
    with pytest.raises(ValueError, match="manifest report must be paper_only"):
        replace(_report((valid,)), paper_only=False)
    with pytest.raises(ValueError, match="manifest report must be report_only"):
        replace(_report((valid,)), report_only=False)
    with pytest.raises(ValueError, match="manifest report must be readonly"):
        replace(_report((valid,)), readonly=False)


def test_manifest_constructor_rejects_inconsistent_report_summaries():
    valid = _report(
        (
            _item("allocation", status="pass"),
            _item("gate_summary", status="pass"),
            _item("risk_budget", status="watch", reason_codes=("near_limit",)),
        ),
    )

    with pytest.raises(ValueError, match="item_count"):
        replace(valid, item_count=4)
    with pytest.raises(ValueError, match="pass_count"):
        replace(valid, pass_count=3)
    with pytest.raises(ValueError, match="watch_count"):
        replace(valid, watch_count=0)
    with pytest.raises(ValueError, match="blocked_count"):
        replace(valid, blocked_count=1)
    with pytest.raises(ValueError, match="missing_required_reports"):
        replace(valid, missing_required_reports=("allocation",))
    with pytest.raises(ValueError, match="manifest_status"):
        replace(valid, manifest_status="pass")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(valid, reason_codes=("manifest_passed",))
    with pytest.raises(ValueError, match="items"):
        replace(
            valid,
            items=tuple(reversed(valid.items)),
        )
