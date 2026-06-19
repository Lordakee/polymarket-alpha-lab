from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import inspect

import pytest

import polymarket_alpha_lab.paper_recommendation_pipeline as pipeline
from polymarket_alpha_lab.paper_recommendation_pipeline import (
    PaperRecommendationPipelineReport,
    PaperRecommendationPipelineStage,
    build_paper_recommendation_pipeline_report,
)


GENERATED_AT = datetime(2026, 6, 19, 12, 0, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _IntSubclass(int):
    pass


class _StringSubclass(str):
    pass


@dataclass(frozen=True)
class SuppliedStageShape:
    stage_name: str
    status: str
    message: str
    input_count: int
    output_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def _stage(
    stage_name: str = "allocation",
    *,
    status: str = "pass",
    message: str | None = None,
    input_count: int = 2,
    output_count: int = 1,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PaperRecommendationPipelineStage:
    return PaperRecommendationPipelineStage(
        stage_name=stage_name,
        status=status,
        message=f"{stage_name} completed" if message is None else message,
        input_count=input_count,
        output_count=output_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _report(
    stages: tuple[object, ...],
    *,
    generated_at: datetime = GENERATED_AT,
    config_version: str = "paper-recommendation-pipeline-v0",
) -> PaperRecommendationPipelineReport:
    return build_paper_recommendation_pipeline_report(
        generated_at=generated_at,
        config_version=config_version,
        stages=stages,
    )


def test_pipeline_summarizes_supplied_stages_preserves_order_and_normalizes_utc():
    generated_at = datetime(
        2026,
        6,
        19,
        5,
        0,
        tzinfo=timezone(timedelta(hours=-7)),
    )

    report = _report(
        (
            _stage(
                "gate_summary",
                status="pass",
                message="all gates clear",
                input_count=9,
                output_count=6,
            ),
            SuppliedStageShape(
                stage_name="readiness",
                status="watch",
                message="one market below edge threshold",
                input_count=6,
                output_count=3,
            ),
            _stage(
                "manifest",
                status="blocked",
                message="required report missing",
                input_count=3,
                output_count=0,
            ),
        ),
        generated_at=generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == "paper-recommendation-pipeline-v0"
    assert report.stage_count == 3
    assert report.pass_count == 1
    assert report.watch_count == 1
    assert report.blocked_count == 1
    assert report.final_status == "blocked"
    assert tuple(stage.stage_name for stage in report.stages) == (
        "gate_summary",
        "readiness",
        "manifest",
    )
    assert report.stages[1] == PaperRecommendationPipelineStage(
        stage_name="readiness",
        status="watch",
        message="one market below edge threshold",
        input_count=6,
        output_count=3,
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_pipeline_final_status_prefers_blocked_then_watch_then_pass():
    assert _report((_stage("first", status="pass"),)).final_status == "pass"
    assert (
        _report(
            (
                _stage("first", status="pass"),
                _stage("second", status="watch"),
            ),
        ).final_status
        == "watch"
    )
    assert (
        _report(
            (
                _stage("first", status="watch"),
                _stage("second", status="blocked"),
            ),
        ).final_status
        == "blocked"
    )


def test_pipeline_rejects_invalid_stage_status_and_canonical_strings():
    with pytest.raises(ValueError, match="status"):
        _stage(status="skip")
    with pytest.raises(ValueError, match="stage_name"):
        _stage(stage_name=" readiness")
    with pytest.raises(ValueError, match="stage_name"):
        _stage(stage_name=_StringSubclass("readiness"))
    with pytest.raises(ValueError, match="message"):
        _stage(message="")
    with pytest.raises(ValueError, match="config_version"):
        _report((_stage(),), config_version=" pipeline-v0")


def test_pipeline_rejects_false_hard_flags_on_stages_and_report():
    valid = _stage()

    with pytest.raises(ValueError, match="pipeline stage must be paper_only"):
        _report((replace(valid, paper_only=False),))
    with pytest.raises(ValueError, match="pipeline stage must be report_only"):
        _report((replace(valid, report_only=False),))
    with pytest.raises(ValueError, match="pipeline stage must be readonly"):
        _report((replace(valid, readonly=False),))
    with pytest.raises(ValueError, match="pipeline report must be paper_only"):
        replace(_report((valid,)), paper_only=False)
    with pytest.raises(ValueError, match="pipeline report must be report_only"):
        replace(_report((valid,)), report_only=False)
    with pytest.raises(ValueError, match="pipeline report must be readonly"):
        replace(_report((valid,)), readonly=False)


def test_pipeline_validates_nonnegative_counts_and_consistency():
    with pytest.raises(ValueError, match="input_count"):
        _stage(input_count=-1)
    with pytest.raises(ValueError, match="output_count"):
        _stage(output_count=-1)
    with pytest.raises(ValueError, match="input_count"):
        _stage(input_count=_IntSubclass(1))

    report = _report(
        (
            _stage("first", status="pass"),
            _stage("second", status="watch"),
        ),
    )

    with pytest.raises(ValueError, match="stage_count"):
        replace(report, stage_count=3)
    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=2)
    with pytest.raises(ValueError, match="watch_count"):
        replace(report, watch_count=0)
    with pytest.raises(ValueError, match="blocked_count"):
        replace(report, blocked_count=1)
    with pytest.raises(ValueError, match="final_status"):
        replace(report, final_status="pass")
    with pytest.raises(FrozenInstanceError):
        report.stage_count = 0  # type: ignore[misc]


def test_pipeline_validates_generated_at_and_supplied_stage_iterable():
    with pytest.raises(ValueError, match="generated_at"):
        _report((_stage(),), generated_at="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        _report(
            (_stage(),),
            generated_at=_DatetimeSubclass(2026, 6, 19, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="stages"):
        build_paper_recommendation_pipeline_report(
            generated_at=GENERATED_AT,
            config_version="paper-recommendation-pipeline-v0",
            stages="bad",
        )


def test_pipeline_reducer_uses_decimal_only_and_has_no_live_trading_imports():
    source = inspect.getsource(pipeline)

    assert "from decimal import Decimal" in source
    assert "float" not in source
    assert "requests" not in source
    assert "httpx" not in source
    assert "websocket" not in source
    assert "auth" not in source.lower()
    assert "client" not in source.lower()
    assert "exchange" not in source.lower()
    assert "live" not in source.lower()
    assert "wallet" not in source.lower()
    assert "private" not in source.lower()
    assert "signer" not in source.lower()
    assert "order" not in source.lower()
    assert "submit" not in source.lower()
    assert "cancel" not in source.lower()
