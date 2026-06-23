create table if not exists public.paper_autonomous_screening_decision_support_gate_reports (
    report_sha256 text primary key,
    generated_at timestamptz not null,
    config_version text not null,
    gate_status text not null,
    recommended_next_step text not null,
    reason_codes_json jsonb not null,
    reason_code_counts_json jsonb not null,
    operator_flow_gate_config_version text not null,
    operator_flow_gate_generated_at timestamptz not null,
    operator_flow_gate_status text not null,
    operator_flow_recommended_next_step text not null,
    queue_priority_generated_at timestamptz not null,
    queue_risk_generated_at timestamptz not null,
    queue_risk_config_version text not null,
    queue_risk_status text not null,
    queue_risk_recommended_next_step text not null,
    queue_source_report_count integer not null,
    queue_research_ready_count integer not null,
    queue_watch_count integer not null,
    queue_blocked_count integer not null,
    queue_candidate_count integer not null,
    queue_ready_count integer not null,
    queue_candidate_watch_count integer not null,
    queue_candidate_blocked_count integer not null,
    queue_total_ready_notional numeric not null,
    queue_largest_ready_notional numeric not null,
    queue_top_research_priority_score numeric not null,
    queue_average_research_priority_score numeric not null,
    trend_source_snapshot_count integer,
    trend_latest_risk_status text,
    trend_consecutive_latest_watch_count integer,
    trend_consecutive_latest_blocked_count integer,
    trend_duplicate_generated_at_count integer,
    rank_stability_status text,
    rank_stable_ready_count integer,
    rank_unstable_ready_count integer,
    rank_blocked_count integer,
    payload_json jsonb not null,
    paper_only boolean not null default true,
    report_only boolean not null default true,
    readonly boolean not null default true,
    inserted_at timestamptz not null default now(),
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
    check (gate_status in ('pass', 'watch', 'blocked')),
    check (operator_flow_gate_status in ('pass', 'watch', 'blocked')),
    check (queue_risk_status in ('pass', 'watch', 'blocked')),
    check (trend_latest_risk_status is null or trend_latest_risk_status in ('pass', 'watch', 'blocked')),
    check (rank_stability_status is null or rank_stability_status in ('stable', 'watch', 'blocked')),
    check (jsonb_typeof(reason_codes_json) = 'array'),
    check (jsonb_typeof(reason_code_counts_json) = 'array'),
    check (jsonb_typeof(payload_json) = 'object'),
    check (queue_source_report_count >= 0),
    check (queue_research_ready_count >= 0),
    check (queue_watch_count >= 0),
    check (queue_blocked_count >= 0),
    check (queue_candidate_count >= 0),
    check (queue_ready_count >= 0),
    check (queue_candidate_watch_count >= 0),
    check (queue_candidate_blocked_count >= 0),
    check (queue_total_ready_notional >= 0),
    check (queue_largest_ready_notional >= 0),
    check (queue_top_research_priority_score >= 0),
    check (queue_average_research_priority_score >= 0),
    check (trend_source_snapshot_count is null or trend_source_snapshot_count >= 0),
    check (trend_consecutive_latest_watch_count is null or trend_consecutive_latest_watch_count >= 0),
    check (trend_consecutive_latest_blocked_count is null or trend_consecutive_latest_blocked_count >= 0),
    check (trend_duplicate_generated_at_count is null or trend_duplicate_generated_at_count >= 0),
    check (rank_stable_ready_count is null or rank_stable_ready_count >= 0),
    check (rank_unstable_ready_count is null or rank_unstable_ready_count >= 0),
    check (rank_blocked_count is null or rank_blocked_count >= 0),
    check (paper_only is true),
    check (report_only is true),
    check (readonly is true)
);

create index if not exists paper_autonomous_screening_gate_generated_at_idx
    on public.paper_autonomous_screening_decision_support_gate_reports
    (generated_at desc);

create index if not exists paper_autonomous_screening_gate_status_generated_at_idx
    on public.paper_autonomous_screening_decision_support_gate_reports
    (gate_status, generated_at desc);

create index if not exists paper_autonomous_screening_gate_config_generated_at_idx
    on public.paper_autonomous_screening_decision_support_gate_reports
    (config_version, generated_at desc);

create index if not exists paper_autonomous_screening_gate_operator_status_idx
    on public.paper_autonomous_screening_decision_support_gate_reports
    (operator_flow_gate_status, generated_at desc);

create index if not exists paper_autonomous_screening_gate_queue_risk_config_idx
    on public.paper_autonomous_screening_decision_support_gate_reports
    (queue_risk_config_version, generated_at desc);

create index if not exists paper_autonomous_screening_gate_status_order_idx
    on public.paper_autonomous_screening_decision_support_gate_reports
    (gate_status, generated_at desc, inserted_at desc, report_sha256 desc);
