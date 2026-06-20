create table if not exists public.local_observability_trends_reports (
    report_sha256 text primary key,
    generated_at timestamptz not null,
    config_version text not null,
    strategy_evidence_snapshot_count integer not null,
    strategy_evidence_latest_status text,
    outcome_freshness_status text not null,
    outcome_report_count integer not null,
    nav_risk_status text not null,
    nav_risk_report_count integer not null,
    paper_trade_cost_status text not null,
    paper_trade_cost_report_count integer not null,
    payload_json jsonb not null,
    paper_only boolean not null default true,
    report_only boolean not null default true,
    readonly boolean not null default true,
    inserted_at timestamptz not null default now(),
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
    check (strategy_evidence_snapshot_count >= 0),
    check (outcome_report_count >= 0),
    check (nav_risk_report_count >= 0),
    check (paper_trade_cost_report_count >= 0),
    check (strategy_evidence_latest_status is null or strategy_evidence_latest_status in ('no_local_evidence', 'local_evidence_gaps', 'local_risk_flags', 'local_evidence_observed')),
    check ((strategy_evidence_snapshot_count = 0
            and strategy_evidence_latest_status is null)
        or (strategy_evidence_snapshot_count > 0
            and strategy_evidence_latest_status is not null)),
    check (outcome_freshness_status in ('empty_outcome_history', 'latest_outcomes_fresh', 'latest_outcomes_pending', 'latest_outcomes_stale')),
    check (nav_risk_status in ('empty_nav_risk_history', 'latest_nav_risk_observed', 'latest_nav_has_unexecutable_positions')),
    check (paper_trade_cost_status in ('empty_cost_audit_history', 'latest_cost_observed', 'latest_negative_cost_adjusted_edges')),
    check (jsonb_typeof(payload_json) = 'object'),
    check (payload_json -> 'paper_only' is null
        or payload_json -> 'paper_only' = 'true'::jsonb),
    check (payload_json -> 'report_only' is null
        or payload_json -> 'report_only' = 'true'::jsonb),
    check (payload_json -> 'readonly' is null
        or payload_json -> 'readonly' = 'true'::jsonb),
    check (paper_only is true),
    check (report_only is true),
    check (readonly is true)
);

create index if not exists idx_lotr_generated_at
    on public.local_observability_trends_reports (generated_at desc);

create index if not exists idx_lotr_config_generated
    on public.local_observability_trends_reports (config_version, generated_at desc);

create index if not exists idx_lotr_strategy_status
    on public.local_observability_trends_reports (strategy_evidence_latest_status, generated_at desc);

create index if not exists idx_lotr_outcome_status
    on public.local_observability_trends_reports (outcome_freshness_status, generated_at desc);

create index if not exists idx_lotr_nav_status
    on public.local_observability_trends_reports (nav_risk_status, generated_at desc);

create index if not exists idx_lotr_cost_status
    on public.local_observability_trends_reports (paper_trade_cost_status, generated_at desc);

create index if not exists idx_lotr_payload_json
    on public.local_observability_trends_reports using gin (payload_json);
