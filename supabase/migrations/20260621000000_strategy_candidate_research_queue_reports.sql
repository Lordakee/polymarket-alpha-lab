create table if not exists public.paper_strategy_candidate_research_queue_reports (
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
  research_status text not null
    check (research_status in ('ready', 'watch', 'blocked')),
  candidate_count integer not null
    check (candidate_count >= 0),
  research_ready_count integer not null
    check (research_ready_count >= 0),
  watch_count integer not null
    check (watch_count >= 0),
  blocked_count integer not null
    check (blocked_count >= 0),
  selected_count integer not null
    check (selected_count >= 0),
  skipped_count integer not null
    check (skipped_count >= 0),
  not_selected_count integer not null
    check (not_selected_count >= 0),
  total_ready_notional numeric not null
    check (total_ready_notional >= 0),
  total_selected_notional numeric not null
    check (total_selected_notional >= 0),
  total_suggested_notional numeric not null
    check (total_suggested_notional >= 0),
  top_research_priority_score numeric not null
    check (top_research_priority_score >= 0),
  average_research_ready_score numeric not null
    check (average_research_ready_score >= 0),
  source_reason_code_counts jsonb not null
    check (jsonb_typeof(source_reason_code_counts) = 'object'),
  primary_reason_code_counts jsonb not null
    check (jsonb_typeof(primary_reason_code_counts) = 'object'),
  reason_codes jsonb not null
    check (jsonb_typeof(reason_codes) = 'array'),
  rows jsonb not null
    check (jsonb_typeof(rows) = 'array'),
  payload jsonb not null
    check (jsonb_typeof(payload) = 'object'),
  paper_only boolean not null default true
    check (paper_only is true),
  report_only boolean not null default true
    check (report_only is true),
  readonly boolean not null default true
    check (readonly is true),
  inserted_at timestamptz not null default now(),
  check (candidate_count = research_ready_count + watch_count + blocked_count),
  check (candidate_count = selected_count + skipped_count + not_selected_count)
);

create index if not exists idx_pscrqr_generated_at
  on public.paper_strategy_candidate_research_queue_reports (generated_at desc);

create index if not exists idx_pscrqr_source_config_version_generated_at
  on public.paper_strategy_candidate_research_queue_reports (source_config_version, generated_at desc);

create index if not exists idx_pscrqr_action_status_generated_at
  on public.paper_strategy_candidate_research_queue_reports (action_status, generated_at desc);

create index if not exists idx_pscrqr_recommended_next_step_generated_at
  on public.paper_strategy_candidate_research_queue_reports (recommended_next_step, generated_at desc);

create index if not exists idx_pscrqr_research_status_generated_at
  on public.paper_strategy_candidate_research_queue_reports (research_status, generated_at desc);

create index if not exists idx_pscrqr_source_queue_status_load_order
  on public.paper_strategy_candidate_research_queue_reports (source_config_version, action_status, recommended_next_step, research_status, generated_at desc, inserted_at desc, report_sha256 desc);
