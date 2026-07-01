create table if not exists public.paper_trade_attribution_reports (
  report_sha256 text primary key
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null,
  config_version text not null,
  trade_count integer not null
    check (trade_count >= 0),
  row_count integer not null
    check (row_count >= 0),
  market_count integer not null
    check (market_count >= 0),
  filled_count integer not null
    check (filled_count >= 0),
  complete_fill_count integer not null
    check (complete_fill_count >= 0),
  partial_fill_count integer not null
    check (partial_fill_count >= 0),
  resolved_count integer
    check (resolved_count is null or resolved_count >= 0),
  pending_count integer
    check (pending_count is null or pending_count >= 0),
  realized_win_count integer
    check (realized_win_count is null or realized_win_count >= 0),
  realized_loss_count integer
    check (realized_loss_count is null or realized_loss_count >= 0),
  total_requested_size numeric not null
    check (total_requested_size >= 0),
  total_filled_size numeric not null
    check (total_filled_size >= 0),
  total_unfilled_size numeric not null
    check (total_unfilled_size >= 0),
  total_notional numeric not null
    check (total_notional >= 0),
  first_trade_decision_at timestamptz,
  latest_trade_decision_at timestamptz,
  payload_json jsonb not null
    check (jsonb_typeof(payload_json) = 'object'),
  paper_only boolean not null default true
    check (paper_only is true),
  report_only boolean not null default true
    check (report_only is true),
  readonly boolean not null default true
    check (readonly is true),
  inserted_at timestamptz not null default now(),
  check (row_count <= trade_count),
  check (market_count <= row_count),
  check (filled_count <= trade_count),
  check (complete_fill_count + partial_fill_count <= trade_count),
  check ((resolved_count is null and pending_count is null and realized_win_count is null and realized_loss_count is null) or (resolved_count is not null and pending_count is not null and realized_win_count is not null and realized_loss_count is not null)),
  check (resolved_count is null or resolved_count + pending_count = trade_count),
  check (resolved_count is null or realized_win_count + realized_loss_count = resolved_count),
  check ((trade_count = 0 and row_count = 0 and market_count = 0 and filled_count = 0 and complete_fill_count = 0 and partial_fill_count = 0 and total_requested_size = 0 and total_filled_size = 0 and total_unfilled_size = 0 and total_notional = 0 and first_trade_decision_at is null and latest_trade_decision_at is null) or trade_count > 0),
  check (trade_count = 0 or (first_trade_decision_at is not null and latest_trade_decision_at is not null and latest_trade_decision_at >= first_trade_decision_at)),
  check (payload_json ? 'rows' and jsonb_typeof(payload_json -> 'rows') = 'array'),
  check (payload_json ? 'generated_at'
    and jsonb_typeof(payload_json -> 'generated_at') = 'string'
    and (payload_json ->> 'generated_at')::timestamptz = generated_at),
  check (payload_json ? 'config_version'
    and jsonb_typeof(payload_json -> 'config_version') = 'string'
    and payload_json ->> 'config_version' = config_version),
  check (payload_json ? 'trade_count'
    and jsonb_typeof(payload_json -> 'trade_count') = 'number'
    and (payload_json ->> 'trade_count')::integer = trade_count),
  check (payload_json ? 'row_count'
    and jsonb_typeof(payload_json -> 'row_count') = 'number'
    and (payload_json ->> 'row_count')::integer = row_count),
  check (payload_json ? 'market_count'
    and jsonb_typeof(payload_json -> 'market_count') = 'number'
    and (payload_json ->> 'market_count')::integer = market_count),
  check (payload_json ? 'filled_count'
    and jsonb_typeof(payload_json -> 'filled_count') = 'number'
    and (payload_json ->> 'filled_count')::integer = filled_count),
  check (payload_json ? 'complete_fill_count'
    and jsonb_typeof(payload_json -> 'complete_fill_count') = 'number'
    and (payload_json ->> 'complete_fill_count')::integer = complete_fill_count),
  check (payload_json ? 'partial_fill_count'
    and jsonb_typeof(payload_json -> 'partial_fill_count') = 'number'
    and (payload_json ->> 'partial_fill_count')::integer = partial_fill_count),
  check (payload_json ? 'resolved_count'
    and ((resolved_count is null
          and payload_json -> 'resolved_count' = 'null'::jsonb)
        or (jsonb_typeof(payload_json -> 'resolved_count') = 'number'
          and (payload_json ->> 'resolved_count')::integer = resolved_count))),
  check (payload_json ? 'pending_count'
    and ((pending_count is null
          and payload_json -> 'pending_count' = 'null'::jsonb)
        or (jsonb_typeof(payload_json -> 'pending_count') = 'number'
          and (payload_json ->> 'pending_count')::integer = pending_count))),
  check (payload_json ? 'realized_win_count'
    and ((realized_win_count is null
          and payload_json -> 'realized_win_count' = 'null'::jsonb)
        or (jsonb_typeof(payload_json -> 'realized_win_count') = 'number'
          and (payload_json ->> 'realized_win_count')::integer = realized_win_count))),
  check (payload_json ? 'realized_loss_count'
    and ((realized_loss_count is null
          and payload_json -> 'realized_loss_count' = 'null'::jsonb)
        or (jsonb_typeof(payload_json -> 'realized_loss_count') = 'number'
          and (payload_json ->> 'realized_loss_count')::integer = realized_loss_count))),
  check (payload_json ? 'total_requested_size'
    and jsonb_typeof(payload_json -> 'total_requested_size') = 'string'
    and (payload_json ->> 'total_requested_size')::numeric = total_requested_size),
  check (payload_json ? 'total_filled_size'
    and jsonb_typeof(payload_json -> 'total_filled_size') = 'string'
    and (payload_json ->> 'total_filled_size')::numeric = total_filled_size),
  check (payload_json ? 'total_unfilled_size'
    and jsonb_typeof(payload_json -> 'total_unfilled_size') = 'string'
    and (payload_json ->> 'total_unfilled_size')::numeric = total_unfilled_size),
  check (payload_json ? 'total_notional'
    and jsonb_typeof(payload_json -> 'total_notional') = 'string'
    and (payload_json ->> 'total_notional')::numeric = total_notional),
  check (payload_json ? 'first_trade_decision_at'
    and ((first_trade_decision_at is null
          and payload_json -> 'first_trade_decision_at' = 'null'::jsonb)
        or (jsonb_typeof(payload_json -> 'first_trade_decision_at') = 'string'
          and (payload_json ->> 'first_trade_decision_at')::timestamptz = first_trade_decision_at))),
  check (payload_json ? 'latest_trade_decision_at'
    and ((latest_trade_decision_at is null
          and payload_json -> 'latest_trade_decision_at' = 'null'::jsonb)
        or (jsonb_typeof(payload_json -> 'latest_trade_decision_at') = 'string'
          and (payload_json ->> 'latest_trade_decision_at')::timestamptz = latest_trade_decision_at))),
  check (payload_json ? 'paper_only'
    and payload_json -> 'paper_only' = 'true'::jsonb),
  check (payload_json ? 'report_only'
    and payload_json -> 'report_only' = 'true'::jsonb),
  check (payload_json ? 'readonly'
    and payload_json -> 'readonly' = 'true'::jsonb)
);

create index if not exists idx_ptar_generated_inserted_report
  on public.paper_trade_attribution_reports (generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists idx_ptar_config_generated
  on public.paper_trade_attribution_reports (config_version, generated_at desc);

create index if not exists idx_ptar_payload_json_gin
  on public.paper_trade_attribution_reports using gin (payload_json jsonb_path_ops);
