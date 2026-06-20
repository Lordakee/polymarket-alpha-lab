create table if not exists public.paper_action_gated_strategy_recommendation_queue_history_reports (
  report_sha256 text primary key
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null,
  source_report_count integer not null
    check (source_report_count >= 0),
  first_source_generated_at timestamptz,
  last_source_generated_at timestamptz,
  research_ready_count integer not null
    check (research_ready_count >= 0),
  watch_count integer not null
    check (watch_count >= 0),
  blocked_count integer not null
    check (blocked_count >= 0),
  total_ready_notional numeric not null
    check (total_ready_notional >= 0),
  latest_action_status text
    check (latest_action_status is null or latest_action_status in ('research_ready', 'watch', 'blocked')),
  latest_recommended_next_step text
    check (latest_recommended_next_step is null or latest_recommended_next_step in ('review_candidate_research_queue', 'await_fresh_cycle_evidence', 'repair_cycle_evidence'))
    check ((latest_action_status is null and latest_recommended_next_step is null) or (latest_action_status = 'research_ready' and latest_recommended_next_step = 'review_candidate_research_queue') or (latest_action_status = 'watch' and latest_recommended_next_step = 'await_fresh_cycle_evidence') or (latest_action_status = 'blocked' and latest_recommended_next_step = 'repair_cycle_evidence')),
  status_transition_count integer not null
    check (status_transition_count >= 0),
  ready_notional_delta numeric not null,
  latest_reason_code_counts jsonb not null
    check (jsonb_typeof(latest_reason_code_counts) = 'object'),
  payload jsonb not null
    check (jsonb_typeof(payload) = 'object'),
  paper_only boolean not null default true
    check (paper_only is true),
  report_only boolean not null default true
    check (report_only is true),
  readonly boolean not null default true
    check (readonly is true),
  inserted_at timestamptz not null default now(),
  check (source_report_count = research_ready_count + watch_count + blocked_count),
  check (source_report_count > 0 or (first_source_generated_at is null and last_source_generated_at is null and latest_action_status is null and latest_recommended_next_step is null and status_transition_count = 0 and total_ready_notional = 0 and ready_notional_delta = 0)),
  check (source_report_count = 0 or (first_source_generated_at is not null and last_source_generated_at is not null and latest_action_status is not null and latest_recommended_next_step is not null)),
  check (source_report_count = 0 or last_source_generated_at >= first_source_generated_at),
  check (source_report_count = 0 or status_transition_count < source_report_count),
  check (source_report_count > 0 or latest_reason_code_counts = '{}'::jsonb)
);

create index if not exists idx_pagsrqhr_generated_at
  on public.paper_action_gated_strategy_recommendation_queue_history_reports (generated_at desc);

create index if not exists idx_pagsrqhr_latest_action_status_generated_at
  on public.paper_action_gated_strategy_recommendation_queue_history_reports (latest_action_status, generated_at desc);

create index if not exists idx_pagsrqhr_latest_recommended_next_step_generated_at
  on public.paper_action_gated_strategy_recommendation_queue_history_reports (latest_recommended_next_step, generated_at desc);

create index if not exists idx_pagsrqhr_source_report_count_generated_at
  on public.paper_action_gated_strategy_recommendation_queue_history_reports (source_report_count, generated_at desc);

create index if not exists idx_pagsrqhr_latest_action_status_load_order
  on public.paper_action_gated_strategy_recommendation_queue_history_reports (latest_action_status, generated_at desc, inserted_at desc, report_sha256 desc);
