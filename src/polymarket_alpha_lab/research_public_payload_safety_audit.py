"""Pure public-payload safety audit for report-only research outputs.

The module is deterministic and side-effect free. Callers provide a public
research payload; the audit returns report-only pass/watch/block findings.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


__all__ = (
    "PublicPayloadSafetyFinding",
    "PublicPayloadSafetyReport",
    "audit_research_public_payload",
    "research_public_payload_safety_report_payload",
)


PASS_REASON_CODE = "research_public_payload_safety_audit_pass"
STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
WATCH_SCORE_PENALTY = Decimal("0.100000")
BLOCK_SCORE_PENALTY = Decimal("0.350000")


@dataclass(frozen=True)
class PublicPayloadSafetyFinding:
    path: str
    severity: str
    reason_code: str
    redacted_detail: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PublicPayloadSafetyFinding:
            raise TypeError("PublicPayloadSafetyFinding does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not PublicPayloadSafetyFinding:
            raise ValueError("finding must be exactly PublicPayloadSafetyFinding")
        _require_public_string("path", self.path)
        _require_status("severity", self.severity, allow_pass=False)
        _require_reason_code("reason_code", self.reason_code)
        _require_public_string("redacted_detail", self.redacted_detail)
        _require_hard_flags("finding", self)


@dataclass(frozen=True)
class PublicPayloadSafetyReport:
    generated_at: datetime
    report_name: str
    audit_status: str
    next_step: str
    finding_count: Decimal
    watch_finding_count: Decimal
    block_finding_count: Decimal
    score: Decimal | None
    findings: tuple[PublicPayloadSafetyFinding, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not PublicPayloadSafetyReport:
            raise TypeError("PublicPayloadSafetyReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not PublicPayloadSafetyReport:
            raise ValueError("report must be exactly PublicPayloadSafetyReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("report_name", self.report_name)
        _require_status("audit_status", self.audit_status, allow_pass=True)
        _require_public_string("next_step", self.next_step)
        for field_name in (
            "finding_count",
            "watch_finding_count",
            "block_finding_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "score",
            _require_optional_ratio_decimal("score", self.score),
        )
        object.__setattr__(self, "findings", _normalize_findings(self.findings))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def audit_research_public_payload(
    payload: object,
    *,
    generated_at: datetime,
    report_name: str = "research_public_payload",
    include_score: bool = True,
) -> PublicPayloadSafetyReport:
    _require_public_string("report_name", report_name)
    if type(include_score) is not bool:
        raise ValueError("include_score must be a bool")
    generated_at_utc = _as_utc("generated_at", generated_at)
    _validate_payload_root(payload)
    findings = _audit_value(payload, "payload")
    status = _summary_status(findings)
    reason_codes = _summary_reason_codes(findings)

    return PublicPayloadSafetyReport(
        generated_at=generated_at_utc,
        report_name=report_name,
        audit_status=status,
        next_step=_next_step(status),
        finding_count=_decimal_count(len(findings)),
        watch_finding_count=_decimal_count(_severity_count(findings, STATUS_WATCH)),
        block_finding_count=_decimal_count(_severity_count(findings, STATUS_BLOCK)),
        score=(_score(findings) if include_score else None),
        findings=findings,
        reason_codes=reason_codes,
    )


def research_public_payload_safety_report_payload(
    report: PublicPayloadSafetyReport,
) -> dict[str, Any]:
    if type(report) is not PublicPayloadSafetyReport:
        raise ValueError("report must be a PublicPayloadSafetyReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _audit_value(value: object, path: str) -> tuple[PublicPayloadSafetyFinding, ...]:
    findings: list[PublicPayloadSafetyFinding] = []
    if is_dataclass(value) and not isinstance(value, type):
        _require_hard_flags(path, value)
        for field in fields(value):
            field_path = field.name if path == "payload" else f"{path}.{field.name}"
            findings.extend(_field_findings(field.name, field_path))
            findings.extend(_audit_value(getattr(value, field.name), field_path))
        return tuple(findings)
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            item_path = key if path == "payload" else f"{path}.{key}"
            findings.extend(_field_findings(key, item_path))
            findings.extend(_audit_value(item, item_path))
        return tuple(findings)
    if type(value) is tuple or type(value) is list:
        for index, item in enumerate(value):
            findings.extend(_audit_value(item, f"{path}[{index}]"))
        return tuple(findings)
    _validate_scalar(path, value)
    if type(value) is str:
        findings.extend(_string_value_findings(path, value))
    return tuple(findings)


def _field_findings(key: str, path: str) -> tuple[PublicPayloadSafetyFinding, ...]:
    if key in {"paper_only", "report_only", "readonly"}:
        return ()
    normalized = _normalized_name(key)
    findings: list[PublicPayloadSafetyFinding] = []

    if _matches_candidate_id(normalized):
        findings.append(
            _finding(
                path,
                STATUS_BLOCK,
                "research_public_payload_safety_audit_raw_candidate_id_field",
                "raw candidate identifier field present",
            ),
        )
    if _matches_market_id(normalized):
        findings.append(
            _finding(
                path,
                STATUS_BLOCK,
                "research_public_payload_safety_audit_market_id_field",
                "market identifier field present",
            ),
        )
    elif _matches_market_label(normalized):
        findings.append(
            _finding(
                path,
                STATUS_WATCH,
                "research_public_payload_safety_audit_market_id_field",
                "market-facing field requires review",
            ),
        )
    if "slug" in normalized:
        findings.append(
            _finding(
                path,
                STATUS_WATCH,
                "research_public_payload_safety_audit_slug_field",
                "slug field requires review",
            ),
        )
    if "question" in normalized:
        findings.append(
            _finding(
                path,
                STATUS_WATCH,
                "research_public_payload_safety_audit_question_field",
                "question field requires review",
            ),
        )
    if _matches_source_reference_field(normalized):
        findings.append(
            _finding(
                path,
                STATUS_WATCH,
                "research_public_payload_safety_audit_source_reference_field",
                "source reference field requires review",
            ),
        )
    if _matches_dsn_table_token_field(normalized):
        findings.append(
            _finding(
                path,
                STATUS_BLOCK,
                "research_public_payload_safety_audit_dsn_table_token_field",
                "internal storage or token field present",
            ),
        )
    if _matches_wallet_auth_field(normalized):
        findings.append(
            _finding(
                path,
                STATUS_BLOCK,
                "research_public_payload_safety_audit_wallet_auth_field",
                "wallet or auth field present",
            ),
        )
    if _matches_trade_field(normalized):
        findings.append(
            _finding(
                path,
                STATUS_BLOCK,
                "research_public_payload_safety_audit_trade_field",
                "order or trade field present",
            ),
        )
    return tuple(findings)


def _string_value_findings(
    path: str,
    value: str,
) -> tuple[PublicPayloadSafetyFinding, ...]:
    lowered = value.lower()
    findings: list[PublicPayloadSafetyFinding] = []
    source_reference = _contains_source_reference_value(lowered)
    if source_reference:
        findings.append(
            _finding(
                path,
                STATUS_BLOCK,
                "research_public_payload_safety_audit_source_reference_value",
                "source reference value present",
            ),
        )
    if not source_reference and _contains_sensitive_value(lowered):
        findings.append(
            _finding(
                path,
                STATUS_BLOCK,
                "research_public_payload_safety_audit_secret_reference_value",
                "internal credential or storage value present",
            ),
        )
    if _contains_order_or_trade_language(lowered):
        findings.append(
            _finding(
                path,
                STATUS_BLOCK,
                "research_public_payload_safety_audit_order_or_trade_language",
                "buy, sell, order, or trade language present",
            ),
        )
    if _contains_recommendation_language(lowered):
        findings.append(
            _finding(
                path,
                STATUS_BLOCK,
                "research_public_payload_safety_audit_recommendation_language",
                "recommendation language present",
            ),
        )
    if _contains_position_sizing_language(lowered):
        findings.append(
            _finding(
                path,
                STATUS_BLOCK,
                "research_public_payload_safety_audit_position_sizing_language",
                "position sizing language present",
            ),
        )
    return tuple(findings)


def _validate_payload_root(payload: object) -> None:
    if is_dataclass(payload) and not isinstance(payload, type):
        _require_hard_flags("payload", payload)
        return
    if type(payload) is dict:
        _require_hard_flags("payload", payload)
        return
    raise ValueError("payload must be a dataclass or dict")


def _validate_scalar(path: str, value: object) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        if not value or value.strip() != value:
            raise ValueError(f"{path} must be a nonempty public string")
        return
    if type(value) is Decimal:
        _require_decimal(path, value)
        return
    if type(value) is datetime:
        _as_utc(path, value)
        return
    if type(value) is int:
        raise ValueError(f"{path} must use Decimal values")
    raise ValueError("payload contains unsupported value")


def _matches_candidate_id(normalized: str) -> bool:
    return "candidate_id" in normalized or normalized.endswith("_candidateid")


def _matches_market_id(normalized: str) -> bool:
    return (
        "market_id" in normalized
        or normalized.endswith("_marketid")
        or normalized == "marketid"
    )


def _matches_market_label(normalized: str) -> bool:
    return "market" in normalized and normalized != "market"


def _matches_source_reference_field(normalized: str) -> bool:
    return "source" in normalized and any(
        fragment in normalized
        for fragment in ("url", "text", "ref", "reference")
    )


def _matches_dsn_table_token_field(normalized: str) -> bool:
    return any(fragment in normalized for fragment in ("dsn", "table", "token"))


def _matches_wallet_auth_field(normalized: str) -> bool:
    return any(fragment in normalized for fragment in ("wallet", "auth"))


def _matches_trade_field(normalized: str) -> bool:
    return any(fragment in normalized for fragment in ("order", "trade"))


def _contains_source_reference_value(lowered: str) -> bool:
    return any(
        fragment in lowered
        for fragment in ("http://", "https://", "www.", ".com/", ".org/", ".gov/")
    )


def _contains_sensitive_value(lowered: str) -> bool:
    return any(
        fragment in lowered
        for fragment in (
            "dsn",
            " table ",
            "token",
            "wallet",
            "auth",
            "authorization",
            "credential",
        )
    )


def _contains_order_or_trade_language(lowered: str) -> bool:
    return any(
        _contains_word(lowered, fragment)
        for fragment in ("buy", "sell", "order", "trade")
    )


def _contains_recommendation_language(lowered: str) -> bool:
    return any(
        fragment in lowered
        for fragment in ("recommend ", "recommendation", "recommended")
    )


def _contains_position_sizing_language(lowered: str) -> bool:
    return (
        "position sizing" in lowered
        or "position size" in lowered
        or "size the position" in lowered
        or "sizing the position" in lowered
    )


def _contains_word(value: str, word: str) -> bool:
    padded = (
        value.replace(".", " ")
        .replace(",", " ")
        .replace(":", " ")
        .replace(";", " ")
        .replace("!", " ")
        .replace("?", " ")
        .replace("(", " ")
        .replace(")", " ")
    )
    return f" {word} " in f" {padded} "


def _normalized_name(value: str) -> str:
    if type(value) is not str or not value:
        raise ValueError("field name must be a nonempty string")
    return (
        value.strip()
        .lower()
        .replace("-", "_")
        .replace(" ", "_")
        .replace(".", "_")
    )


def _finding(
    path: str,
    severity: str,
    reason_code: str,
    redacted_detail: str,
) -> PublicPayloadSafetyFinding:
    return PublicPayloadSafetyFinding(
        path=path,
        severity=severity,
        reason_code=reason_code,
        redacted_detail=redacted_detail,
    )


def _summary_status(findings: tuple[PublicPayloadSafetyFinding, ...]) -> str:
    if any(finding.severity == STATUS_BLOCK for finding in findings):
        return STATUS_BLOCK
    if findings:
        return STATUS_WATCH
    return STATUS_PASS


def _summary_reason_codes(
    findings: tuple[PublicPayloadSafetyFinding, ...],
) -> tuple[str, ...]:
    if not findings:
        return (PASS_REASON_CODE,)
    return tuple(finding.reason_code for finding in findings)


def _next_step(status: str) -> str:
    if status == STATUS_PASS:
        return "publish_report_only_research_payload"
    if status == STATUS_WATCH:
        return "review_report_only_research_payload"
    if status == STATUS_BLOCK:
        return "block_report_only_research_payload"
    raise ValueError("status must be pass, watch, or block")


def _score(findings: tuple[PublicPayloadSafetyFinding, ...]) -> Decimal:
    watch_count = Decimal(_severity_count(findings, STATUS_WATCH))
    block_count = Decimal(_severity_count(findings, STATUS_BLOCK))
    score = ONE - (watch_count * WATCH_SCORE_PENALTY) - (
        block_count * BLOCK_SCORE_PENALTY
    )
    return _quantize(max(ZERO, min(ONE, score)))


def _severity_count(
    findings: tuple[PublicPayloadSafetyFinding, ...],
    severity: str,
) -> int:
    return sum(1 for finding in findings if finding.severity == severity)


def _normalize_findings(
    findings: object,
) -> tuple[PublicPayloadSafetyFinding, ...]:
    if type(findings) is not tuple:
        raise ValueError("findings must be a tuple")
    for finding in findings:
        if type(finding) is not PublicPayloadSafetyFinding:
            raise ValueError("findings must contain PublicPayloadSafetyFinding values")
        _require_hard_flags("finding", finding)
    return findings


def _validate_report_consistency(report: PublicPayloadSafetyReport) -> None:
    if report.finding_count != _decimal_count(len(report.findings)):
        raise ValueError("finding_count must match findings")
    if report.watch_finding_count != _decimal_count(
        _severity_count(report.findings, STATUS_WATCH),
    ):
        raise ValueError("watch_finding_count must match findings")
    if report.block_finding_count != _decimal_count(
        _severity_count(report.findings, STATUS_BLOCK),
    ):
        raise ValueError("block_finding_count must match findings")
    if report.audit_status != _summary_status(report.findings):
        raise ValueError("audit_status must match findings")
    if report.next_step != _next_step(report.audit_status):
        raise ValueError("next_step must match audit_status")
    if report.reason_codes != _summary_reason_codes(report.findings):
        raise ValueError("reason_codes must match findings")


def _payload_value(value: object) -> object:
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is tuple or type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_optional_ratio_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public string")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value.lower() != value or " " in value:
        raise ValueError(f"{field_name} must be a canonical reason code")


def _require_status(field_name: str, value: object, *, allow_pass: bool) -> None:
    allowed = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK) if allow_pass else (
        STATUS_WATCH,
        STATUS_BLOCK,
    )
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(normalized)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = _optional_field_value(value, field_name)
        if flag is not None and flag is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _optional_field_value(value: object, field_name: str) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if type(value) is dict and field_name in value:
        return value[field_name]
    return None
