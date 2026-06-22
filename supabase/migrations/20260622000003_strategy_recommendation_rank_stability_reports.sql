create table if not exists public.strategy_recommendation_rank_stability_reports (
  report_sha256 text primary key
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null,
  config_version text not null,
  stability_status text not null
    check (stability_status in ('stable', 'watch', 'blocked')),
  reason_codes_json jsonb not null
    check (jsonb_typeof(reason_codes_json) = 'array'),
  source_report_count integer not null
    check (source_report_count >= 0),
  candidate_count integer not null
    check (candidate_count >= 0),
  stable_count integer not null
    check (stable_count >= 0),
  watch_count integer not null
    check (watch_count >= 0),
  blocked_count integer not null
    check (blocked_count >= 0),
  stable_ready_count integer not null
    check (stable_ready_count >= 0),
  unstable_ready_count integer not null
    check (unstable_ready_count >= 0),
  selected_side_changed_count integer not null
    check (selected_side_changed_count >= 0),
  queue_status_changed_count integer not null
    check (queue_status_changed_count >= 0),
  latest_generated_at timestamptz null,
  top_stable_market_slug text null,
  rows_json jsonb not null
    check (jsonb_typeof(rows_json) = 'array'),
  payload_json jsonb not null
    check (jsonb_typeof(payload_json) = 'object'),
  paper_only boolean not null default true
    check (paper_only is true),
  report_only boolean not null default true
    check (report_only is true),
  readonly boolean not null default true
    check (readonly is true),
  inserted_at timestamptz not null default now(),
  check (stable_count + watch_count + blocked_count = candidate_count),
  check (jsonb_array_length(rows_json) = candidate_count),
  check (payload_json ? 'paper_only' and payload_json -> 'paper_only' = 'true'::jsonb),
  check (payload_json ? 'report_only' and payload_json -> 'report_only' = 'true'::jsonb),
  check (payload_json ? 'readonly' and payload_json -> 'readonly' = 'true'::jsonb),
  check (payload_json ? 'generated_at' and jsonb_typeof(payload_json -> 'generated_at') = 'string' and (payload_json ->> 'generated_at')::timestamptz = generated_at),
  check (payload_json ? 'config_version' and jsonb_typeof(payload_json -> 'config_version') = 'string' and payload_json ->> 'config_version' = config_version),
  check (payload_json ? 'stability_status' and jsonb_typeof(payload_json -> 'stability_status') = 'string' and payload_json ->> 'stability_status' = stability_status),
  check (payload_json ? 'source_report_count' and jsonb_typeof(payload_json -> 'source_report_count') = 'number' and (payload_json ->> 'source_report_count')::integer = source_report_count),
  check (payload_json ? 'candidate_count' and jsonb_typeof(payload_json -> 'candidate_count') = 'number' and (payload_json ->> 'candidate_count')::integer = candidate_count),
  check (payload_json ? 'stable_count' and jsonb_typeof(payload_json -> 'stable_count') = 'number' and (payload_json ->> 'stable_count')::integer = stable_count),
  check (payload_json ? 'watch_count' and jsonb_typeof(payload_json -> 'watch_count') = 'number' and (payload_json ->> 'watch_count')::integer = watch_count),
  check (payload_json ? 'blocked_count' and jsonb_typeof(payload_json -> 'blocked_count') = 'number' and (payload_json ->> 'blocked_count')::integer = blocked_count),
  check (payload_json ? 'stable_ready_count' and jsonb_typeof(payload_json -> 'stable_ready_count') = 'number' and (payload_json ->> 'stable_ready_count')::integer = stable_ready_count),
  check (payload_json ? 'unstable_ready_count' and jsonb_typeof(payload_json -> 'unstable_ready_count') = 'number' and (payload_json ->> 'unstable_ready_count')::integer = unstable_ready_count),
  check (payload_json ? 'selected_side_changed_count' and jsonb_typeof(payload_json -> 'selected_side_changed_count') = 'number' and (payload_json ->> 'selected_side_changed_count')::integer = selected_side_changed_count),
  check (payload_json ? 'queue_status_changed_count' and jsonb_typeof(payload_json -> 'queue_status_changed_count') = 'number' and (payload_json ->> 'queue_status_changed_count')::integer = queue_status_changed_count),
  check (payload_json ? 'reason_codes' and jsonb_typeof(payload_json -> 'reason_codes') = 'array' and payload_json -> 'reason_codes' = reason_codes_json),
  check (payload_json ? 'rows' and jsonb_typeof(payload_json -> 'rows') = 'array' and payload_json -> 'rows' = rows_json)
);

create index if not exists idx_srrsr_generated_at
  on public.strategy_recommendation_rank_stability_reports (generated_at desc);

create index if not exists idx_srrsr_status_generated
  on public.strategy_recommendation_rank_stability_reports (stability_status, generated_at desc);

create index if not exists idx_srrsr_config_generated
  on public.strategy_recommendation_rank_stability_reports (config_version, generated_at desc);

create index if not exists idx_srrsr_reason_codes_json
  on public.strategy_recommendation_rank_stability_reports using gin (reason_codes_json);

create index if not exists idx_srrsr_rows_json
  on public.strategy_recommendation_rank_stability_reports using gin (rows_json);

create index if not exists idx_srrsr_payload_json
  on public.strategy_recommendation_rank_stability_reports using gin (payload_json);
