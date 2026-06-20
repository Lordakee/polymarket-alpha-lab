create table if not exists public.paper_action_gated_strategy_recommendation_queue_decision_support_reports (
  snapshot_sha256 text primary key
    check (snapshot_sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null,
  priority_source_report_count integer not null
    check (priority_source_report_count >= 0),
  priority_research_ready_count integer not null
    check (priority_research_ready_count >= 0),
  priority_watch_count integer not null
    check (priority_watch_count >= 0),
  priority_blocked_count integer not null
    check (priority_blocked_count >= 0),
  priority_total_ready_notional numeric not null
    check (priority_total_ready_notional >= 0),
  top_research_priority_score numeric not null
    check (top_research_priority_score >= 0),
  average_research_priority_score numeric not null
    check (average_research_priority_score >= 0),
  risk_config_version text not null,
  risk_status text not null
    check (risk_status in ('pass', 'watch', 'blocked')),
  risk_recommended_next_step text not null
    check (risk_recommended_next_step in ('allocate_paper_research_queue', 'throttle_paper_research_queue', 'block_paper_research_queue'))
    check ((risk_status = 'pass' and risk_recommended_next_step = 'allocate_paper_research_queue') or (risk_status = 'watch' and risk_recommended_next_step = 'throttle_paper_research_queue') or (risk_status = 'blocked' and risk_recommended_next_step = 'block_paper_research_queue')),
  risk_source_queue_count integer not null
    check (risk_source_queue_count >= 0),
  risk_candidate_count integer not null
    check (risk_candidate_count >= 0),
  risk_ready_count integer not null
    check (risk_ready_count >= 0),
  risk_total_ready_notional numeric not null
    check (risk_total_ready_notional >= 0),
  risk_largest_queue_ready_notional numeric not null
    check (risk_largest_queue_ready_notional >= 0),
  risk_reason_codes jsonb not null
    check (jsonb_typeof(risk_reason_codes) = 'array'),
  priority_payload jsonb not null
    check (jsonb_typeof(priority_payload) = 'object'),
  risk_payload jsonb not null
    check (jsonb_typeof(risk_payload) = 'object'),
  paper_only boolean not null default true
    check (paper_only is true),
  report_only boolean not null default true
    check (report_only is true),
  readonly boolean not null default true
    check (readonly is true),
  inserted_at timestamptz not null default now(),
  check (priority_source_report_count = priority_research_ready_count + priority_watch_count + priority_blocked_count),
  check (priority_source_report_count = risk_source_queue_count),
  check (priority_total_ready_notional = risk_total_ready_notional),
  check (risk_candidate_count >= risk_ready_count)
);

create index if not exists idx_pagsrqdsr_generated_at
  on public.paper_action_gated_strategy_recommendation_queue_decision_support_reports (generated_at desc);

create index if not exists idx_pagsrqdsr_risk_status_generated_at
  on public.paper_action_gated_strategy_recommendation_queue_decision_support_reports (risk_status, generated_at desc);

create index if not exists idx_pagsrqdsr_risk_config_version_generated_at
  on public.paper_action_gated_strategy_recommendation_queue_decision_support_reports (risk_config_version, generated_at desc);

create index if not exists idx_pagsrqdsr_priority_source_report_count_generated_at
  on public.paper_action_gated_strategy_recommendation_queue_decision_support_reports (priority_source_report_count, generated_at desc);

create index if not exists idx_pagsrqdsr_risk_status_load_sort
  on public.paper_action_gated_strategy_recommendation_queue_decision_support_reports (risk_status, generated_at desc, inserted_at desc, snapshot_sha256 desc);
