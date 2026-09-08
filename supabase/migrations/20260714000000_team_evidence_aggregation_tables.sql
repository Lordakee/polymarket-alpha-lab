create table if not exists public.team_evaluation_attempts (
  tea_id text primary key,
  tfr_id text not null,
  attempted_at timestamptz not null,
  status text not null,
  hard_flag boolean not null,
  scope_version text not null,
  scope_key text not null,
  config_version text not null,
  config_digest text not null,
  diagnostic_record_count integer not null,
  arithmetic_record_count integer not null,
  payload_sha256 text not null,
  evaluation_scope_payload jsonb not null,
  paper_only boolean not null default true,
  report_only boolean not null default true,
  readonly boolean not null default true,
  created_at timestamptz not null default now(),
  check (tea_id <> ''),
  check (tfr_id <> ''),
  check (status in ('ready', 'watch', 'blocked')),
  check (diagnostic_record_count >= 0),
  check (arithmetic_record_count >= 0),
  check (length(payload_sha256) = 64),
  check (payload_sha256 ~ '^[a-f0-9]{64}$'),
  check (length(scope_key) = 64),
  check (scope_key ~ '^[a-f0-9]{64}$'),
  check (length(config_digest) = 64),
  check (scope_version <> ''),
  check (config_version <> ''),
  check (jsonb_typeof(evaluation_scope_payload) = 'object'),
  check (jsonb_typeof(evaluation_scope_payload -> 'domain_context') = 'object'),
  check ((evaluation_scope_payload ->> 'scope_version' = scope_version) is true),
  check ((evaluation_scope_payload -> 'node2_result' -> 'result' ->> 'status' = status) is true),
  check (((evaluation_scope_payload -> 'node2_result' -> 'result' ->> 'evaluated_at')::timestamptz = attempted_at) is true),
  check ((evaluation_scope_payload -> 'node2_result' -> 'result' ->> 'config_version' = config_version) is true),
  check ((evaluation_scope_payload -> 'node2_result' -> 'result' ->> 'config_digest' = config_digest) is true),
  check (((evaluation_scope_payload -> 'node2_result' -> 'result' ->> 'diagnostic_record_count')::integer = diagnostic_record_count) is true),
  check (((evaluation_scope_payload -> 'node2_result' -> 'result' ->> 'arithmetic_record_count')::integer = arithmetic_record_count) is true),
  check (((evaluation_scope_payload -> 'node2_result' -> 'result' -> 'contradiction' ->> 'status' = 'blocked') = hard_flag) is true),
  check ((evaluation_scope_payload -> 'run_metadata' ->> 'paper_only' = 'true') is true),
  check ((evaluation_scope_payload -> 'run_metadata' ->> 'report_only' = 'true') is true),
  check ((evaluation_scope_payload -> 'run_metadata' ->> 'readonly' = 'true') is true),
  check ((evaluation_scope_payload -> 'node2_result' -> 'result' ->> 'paper_only' = 'true') is true),
  check ((evaluation_scope_payload -> 'node2_result' -> 'result' ->> 'report_only' = 'true') is true),
  check ((evaluation_scope_payload -> 'node2_result' -> 'result' ->> 'readonly' = 'true') is true),
  check (paper_only is true),
  check (report_only is true),
  check (readonly is true)
);

create index if not exists team_evaluation_attempts_hard_by_run_idx
  on public.team_evaluation_attempts (tfr_id, attempted_at desc, tea_id desc)
  where hard_flag is true
    and status in ('ready', 'watch', 'blocked');

create index if not exists team_evaluation_attempts_hard_by_scope_idx
  on public.team_evaluation_attempts (scope_version, scope_key, attempted_at desc, tea_id desc)
  where hard_flag is true
    and status in ('ready', 'watch', 'blocked');

comment on table public.team_evaluation_attempts is
  'Local Supabase/Postgres Phase 1 append-only immutable team evaluation attempts.';
