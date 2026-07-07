_UNSAFE_PUBLIC_VALUE_FRAGMENTS = (
    "market_id",
    "candidate_id",
    "normalized_market_question",
    "market_slug",
    "question",
    "payload",
    "hash",
    "digest",
    "dsn",
    "host",
    "table",
    "source_ref",
    "source_report_ref",
    "trade",
    "trading",
    "authentication",
    "authorization",
    "oauth",
    "api_key",
    "wallet",
    "account",
    "order",
    "signing",
    "cancel",
    "replace",
    "exchange",
)


def format_paper_candidate_decision_engine_report_cli_stdout(report: object) -> str:
    _require_hard_flags(report)
    reason_counts = " ".join(
        _reason_count_value(item) for item in _items(_field(report, "reason_counts"))
    )
    return (
        "paper-candidate-decision-engine-report: "
        f"config_version={_safe_public_value(_field(report, 'config_version'))} "
        f"candidate_count={_safe_public_value(_field(report, 'candidate_count'))} "
        f"reject={_safe_public_value(_field(report, 'reject_count'))} "
        f"watch={_safe_public_value(_field(report, 'watch_count'))} "
        f"research_more={_safe_public_value(_field(report, 'research_more_count'))} "
        f"paper_recommend={_safe_public_value(_field(report, 'paper_recommend_count'))} "
        f"paper_only={_safe_public_value(_field(report, 'paper_only'))} "
        f"report_only={_safe_public_value(_field(report, 'report_only'))} "
        f"readonly={_safe_public_value(_field(report, 'readonly'))}\n"
        f"reason_code_counts: {reason_counts or 'none'}\n"
    )


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if _field(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _reason_count_value(row: object) -> str:
    if isinstance(row, tuple) and len(row) >= 2:
        reason_code, count = row[0], row[1]
    else:
        reason_code, count = _field(row, "reason_code"), _field(row, "count")
    return f"{_safe_public_value(reason_code)}:{_safe_public_value(count)}"


def _items(value: object) -> tuple[object, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        return (value,)
    try:
        return tuple(value)  # type: ignore[arg-type]
    except TypeError:
        return (value,)


def _field(container: object, name: str, default: object = ...) -> object:
    if isinstance(container, dict):
        if default is ...:
            return container[name]
        return container.get(name, default)
    if default is ...:
        return getattr(container, name)
    return getattr(container, name, default)


def _safe_public_value(value: object) -> str:
    rendered = str(value)
    lowered = rendered.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError("unsafe public summary value")
    return rendered


__all__ = ("format_paper_candidate_decision_engine_report_cli_stdout",)
