"""Pure paper-only manifest reducer for supplied recommendation reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


__all__ = (
    "PaperRecommendationManifestConfig",
    "PaperRecommendationManifestItem",
    "PaperRecommendationManifestReport",
    "build_paper_recommendation_manifest_report",
)


STATUSES = ("pass", "watch", "blocked")


@dataclass(frozen=True)
class PaperRecommendationManifestConfig:
    config_version: str
    required_report_names: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "required_report_names",
            _normalize_string_tuple(
                "required_report_names",
                self.required_report_names,
                allow_empty=True,
                sorted_unique=True,
            ),
        )


@dataclass(frozen=True)
class PaperRecommendationManifestItem:
    report_name: str
    config_version: str
    generated_at: datetime
    row_count: int
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("report_name", self.report_name)
        _require_canonical_string("config_version", self.config_version)
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_nonnegative_int("row_count", self.row_count)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
                sorted_unique=False,
            ),
        )
        _require_hard_flags("manifest item", self)


@dataclass(frozen=True)
class PaperRecommendationManifestReport:
    generated_at: datetime
    config_version: str
    item_count: int
    pass_count: int
    watch_count: int
    blocked_count: int
    missing_required_reports: tuple[str, ...]
    manifest_status: str
    reason_codes: tuple[str, ...]
    items: tuple[PaperRecommendationManifestItem, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("item_count", self.item_count)
        _require_nonnegative_int("pass_count", self.pass_count)
        _require_nonnegative_int("watch_count", self.watch_count)
        _require_nonnegative_int("blocked_count", self.blocked_count)
        object.__setattr__(
            self,
            "missing_required_reports",
            _normalize_string_tuple(
                "missing_required_reports",
                self.missing_required_reports,
                allow_empty=True,
                sorted_unique=True,
            ),
        )
        _require_status("manifest_status", self.manifest_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_string_tuple(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
                sorted_unique=False,
            ),
        )
        object.__setattr__(self, "items", _normalize_items(self.items))
        _validate_report_consistency(self)
        _require_hard_flags("manifest report", self)


def build_paper_recommendation_manifest_report(
    supplied_reports: tuple[object, ...] | list[object],
    *,
    config: PaperRecommendationManifestConfig,
    generated_at: datetime,
) -> PaperRecommendationManifestReport:
    if type(config) is not PaperRecommendationManifestConfig:
        raise ValueError("config must be a PaperRecommendationManifestConfig")
    generated_at = _as_utc(generated_at)
    items = _normalize_supplied_reports(supplied_reports)
    missing_required_reports = _missing_required_reports(config, items)
    pass_count = _status_count(items, "pass")
    watch_count = _status_count(items, "watch")
    blocked_count = _status_count(items, "blocked")
    manifest_status = _manifest_status(
        missing_required_reports=missing_required_reports,
        watch_count=watch_count,
        blocked_count=blocked_count,
    )

    return PaperRecommendationManifestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        item_count=len(items),
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        missing_required_reports=missing_required_reports,
        manifest_status=manifest_status,
        reason_codes=_manifest_reason_codes(
            missing_required_reports=missing_required_reports,
            watch_count=watch_count,
            blocked_count=blocked_count,
        ),
        items=items,
    )


def _normalize_supplied_reports(
    supplied_reports: tuple[object, ...] | list[object],
) -> tuple[PaperRecommendationManifestItem, ...]:
    if isinstance(supplied_reports, (str, bytes)):
        raise ValueError("supplied_reports must be an iterable")
    try:
        items = tuple(supplied_reports)
    except TypeError as exc:
        raise ValueError("supplied_reports must be an iterable") from exc
    normalized = tuple(_coerce_item(item) for item in items)
    _require_unique_report_names(normalized)
    return _sort_items(normalized)


def _coerce_item(value: object) -> PaperRecommendationManifestItem:
    if type(value) is PaperRecommendationManifestItem:
        return value
    return PaperRecommendationManifestItem(
        report_name=_required_attr(value, "report_name"),
        config_version=_required_attr(value, "config_version"),
        generated_at=_required_attr(value, "generated_at"),
        row_count=_required_attr(value, "row_count"),
        status=_required_attr(value, "status"),
        reason_codes=_required_attr(value, "reason_codes"),
        paper_only=_required_attr(value, "paper_only"),
        report_only=_required_attr(value, "report_only"),
        readonly=_required_attr(value, "readonly"),
    )


def _normalize_items(
    items: tuple[PaperRecommendationManifestItem, ...],
) -> tuple[PaperRecommendationManifestItem, ...]:
    if isinstance(items, (str, bytes)):
        raise ValueError("items must be an iterable")
    try:
        normalized = tuple(items)
    except TypeError as exc:
        raise ValueError("items must be an iterable") from exc
    for item in normalized:
        if type(item) is not PaperRecommendationManifestItem:
            raise ValueError("items must contain manifest items")
        _require_hard_flags("manifest item", item)
    _require_unique_report_names(normalized)
    sorted_items = _sort_items(normalized)
    if normalized != sorted_items:
        raise ValueError("items must be deterministically sorted")
    return normalized


def _sort_items(
    items: tuple[PaperRecommendationManifestItem, ...],
) -> tuple[PaperRecommendationManifestItem, ...]:
    return tuple(sorted(items, key=lambda item: item.report_name))


def _require_unique_report_names(
    items: tuple[PaperRecommendationManifestItem, ...],
) -> None:
    report_names = tuple(item.report_name for item in items)
    if len(set(report_names)) != len(report_names):
        raise ValueError("report_name values must be unique")


def _missing_required_reports(
    config: PaperRecommendationManifestConfig,
    items: tuple[PaperRecommendationManifestItem, ...],
) -> tuple[str, ...]:
    present_names = {item.report_name for item in items}
    return tuple(
        report_name
        for report_name in config.required_report_names
        if report_name not in present_names
    )


def _status_count(
    items: tuple[PaperRecommendationManifestItem, ...],
    status: str,
) -> int:
    return sum(1 for item in items if item.status == status)


def _manifest_status(
    *,
    missing_required_reports: tuple[str, ...],
    watch_count: int,
    blocked_count: int,
) -> str:
    if missing_required_reports or blocked_count > 0:
        return "blocked"
    if watch_count > 0:
        return "watch"
    return "pass"


def _manifest_reason_codes(
    *,
    missing_required_reports: tuple[str, ...],
    watch_count: int,
    blocked_count: int,
) -> tuple[str, ...]:
    reason_codes = []
    if missing_required_reports:
        reason_codes.append("missing_required_reports")
    if blocked_count > 0:
        reason_codes.append("supplied_report_blocked")
    if watch_count > 0:
        reason_codes.append("supplied_report_watch")
    if not reason_codes:
        reason_codes.append("manifest_passed")
    return tuple(reason_codes)


def _validate_report_consistency(report: PaperRecommendationManifestReport) -> None:
    if report.item_count != len(report.items):
        raise ValueError("item_count must match items")
    if report.pass_count != _status_count(report.items, "pass"):
        raise ValueError("pass_count must match items")
    if report.watch_count != _status_count(report.items, "watch"):
        raise ValueError("watch_count must match items")
    if report.blocked_count != _status_count(report.items, "blocked"):
        raise ValueError("blocked_count must match items")
    if report.item_count != report.pass_count + report.watch_count + report.blocked_count:
        raise ValueError("item_count must match status counts")
    present_names = {item.report_name for item in report.items}
    if any(report_name in present_names for report_name in report.missing_required_reports):
        raise ValueError("missing_required_reports must not include present items")
    if report.manifest_status != _manifest_status(
        missing_required_reports=report.missing_required_reports,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
    ):
        raise ValueError("manifest_status must match manifest inputs")
    if report.reason_codes != _manifest_reason_codes(
        missing_required_reports=report.missing_required_reports,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
    ):
        raise ValueError("reason_codes must match manifest inputs")


def _required_attr(value: object, field_name: str) -> object:
    if not hasattr(value, field_name):
        raise ValueError(f"{field_name} is required")
    return getattr(value, field_name)


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_string_tuple(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
    sorted_unique: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not allow_empty and not items:
        raise ValueError(f"{field_name} must contain at least one value")
    for item in items:
        _require_canonical_string(field_name, item)
    if len(set(items)) != len(items):
        raise ValueError(f"{field_name} must not contain duplicates")
    if sorted_unique:
        return tuple(sorted(items))
    return items


def _require_hard_flags(field_name: str, value: object) -> None:
    if _required_attr(value, "paper_only") is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if _required_attr(value, "report_only") is not True:
        raise ValueError(f"{field_name} must be report_only")
    if _required_attr(value, "readonly") is not True:
        raise ValueError(f"{field_name} must be readonly")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")
