create table if not exists public.strategy_candidate_decision_matrix_reports (
  report_sha256 text primary key
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null,
  config_version text not null,
  source_queue_config_version text not null,
  decision_matrix_status text not null
    check (decision_matrix_status in ('ready', 'watch', 'blocked')),
  candidate_count integer not null
    check (candidate_count >= 0),
  advance_count integer not null
    check (advance_count >= 0),
  monitor_count integer not null
    check (monitor_count >= 0),
  decline_count integer not null
    check (decline_count >= 0),
  blocked_count integer not null
    check (blocked_count >= 0),
  reason_codes_json jsonb not null default '[]'::jsonb
    check (jsonb_typeof(reason_codes_json) = 'array'),
  rows_json jsonb not null default '[]'::jsonb
    check (jsonb_typeof(rows_json) = 'array'),
  payload_json jsonb not null
    check (jsonb_typeof(payload_json) = 'object'),
  check (
    payload_json::text !~*
    '"([^"]*[_ -])?(auth|wallet|account|order|trade|execute|submit|cancel|sign|private[_ -]?key|api[_ -]?key|secret|token|credential)([_ -][^"]*)?"[[:space:]]*:'
  ),
  paper_only boolean not null default true
    check (paper_only is true),
  report_only boolean not null default true
    check (report_only is true),
  readonly boolean not null default true
    check (readonly is true),
  inserted_at timestamptz not null default now(),
  check (((payload_json ->> 'generated_at')::timestamptz = generated_at) is true),
  check ((payload_json ->> 'config_version' = config_version) is true),
  check ((payload_json ->> 'source_queue_config_version' = source_queue_config_version) is true),
  check ((payload_json ->> 'decision_matrix_status' = decision_matrix_status) is true),
  check (((payload_json ->> 'candidate_count')::integer = candidate_count) is true),
  check (((payload_json ->> 'advance_count')::integer = advance_count) is true),
  check (((payload_json ->> 'monitor_count')::integer = monitor_count) is true),
  check (((payload_json ->> 'decline_count')::integer = decline_count) is true),
  check (((payload_json ->> 'blocked_count')::integer = blocked_count) is true),
  check ((payload_json -> 'reason_codes' = reason_codes_json) is true),
  check ((payload_json -> 'rows' = rows_json) is true),
  check ((payload_json ->> 'paper_only' = 'true') is true),
  check ((payload_json ->> 'report_only' = 'true') is true),
  check ((payload_json ->> 'readonly' = 'true') is true),
  check (advance_count + monitor_count + decline_count + blocked_count = candidate_count)
);

create index if not exists idx_scdmr_generated_at
  on public.strategy_candidate_decision_matrix_reports (generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists idx_scdmr_decision_matrix_status_generated_at
  on public.strategy_candidate_decision_matrix_reports (decision_matrix_status, generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists idx_scdmr_config_version_generated_at
  on public.strategy_candidate_decision_matrix_reports (config_version, generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists idx_scdmr_source_queue_config_version_generated_at
  on public.strategy_candidate_decision_matrix_reports (source_queue_config_version, generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists idx_scdmr_reason_codes_json_gin
  on public.strategy_candidate_decision_matrix_reports using gin (reason_codes_json jsonb_path_ops);

comment on table public.strategy_candidate_decision_matrix_reports is
  'Local Supabase/Postgres paper, report-only, read-only strategy candidate decision matrix reports.';
