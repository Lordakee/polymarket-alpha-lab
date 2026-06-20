create table if not exists public.paper_action_gated_strategy_recommendation_queue_reports (
  report_sha256 text primary key
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null,
  config_version text not null,
  source_config_version text not null,
  action_status text not null
    check (action_status in ('research_ready', 'watch', 'blocked')),
  recommended_next_step text not null
    check (recommended_next_step in ('review_candidate_research_queue', 'await_fresh_cycle_evidence', 'repair_cycle_evidence'))
    check ((action_status = 'research_ready' and recommended_next_step = 'review_candidate_research_queue') or (action_status = 'watch' and recommended_next_step = 'await_fresh_cycle_evidence') or (action_status = 'blocked' and recommended_next_step = 'repair_cycle_evidence')),
  candidate_count integer not null
    check (candidate_count >= 0),
  ready_count integer not null
    check (ready_count >= 0),
  watch_count integer not null
    check (watch_count >= 0),
  blocked_count integer not null
    check (blocked_count >= 0),
  total_ready_notional numeric not null
    check (total_ready_notional >= 0),
  reason_code_counts jsonb not null
    check (jsonb_typeof(reason_code_counts) = 'object'),
  payload jsonb not null
    check (jsonb_typeof(payload) = 'object'),
  paper_only boolean not null default true
    check (paper_only is true),
  report_only boolean not null default true
    check (report_only is true),
  readonly boolean not null default true
    check (readonly is true),
  inserted_at timestamptz not null default now(),
  check (candidate_count = ready_count + watch_count + blocked_count),
  check (action_status = 'research_ready' or (candidate_count = 0 and ready_count = 0 and watch_count = 0 and blocked_count = 0 and total_ready_notional = 0))
);

create index if not exists idx_pagsrqr_generated_at
  on public.paper_action_gated_strategy_recommendation_queue_reports (generated_at desc);

create index if not exists idx_pagsrqr_source_config_version_generated_at
  on public.paper_action_gated_strategy_recommendation_queue_reports (source_config_version, generated_at desc);

create index if not exists idx_pagsrqr_action_status_generated_at
  on public.paper_action_gated_strategy_recommendation_queue_reports (action_status, generated_at desc);

create index if not exists idx_pagsrqr_recommended_next_step_generated_at
  on public.paper_action_gated_strategy_recommendation_queue_reports (recommended_next_step, generated_at desc);

create index if not exists idx_pagsrqr_source_action_status_load_order
  on public.paper_action_gated_strategy_recommendation_queue_reports (source_config_version, action_status, generated_at desc, inserted_at desc, report_sha256 desc);
