create table if not exists public.paper_trade_cost_audit_reports (
  report_sha256 text primary key
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
  generated_at timestamptz not null,
  config_version text not null,
  trade_count integer not null
    check (trade_count >= 0),
  total_filled_size numeric not null
    check (total_filled_size >= 0),
  total_requested_size numeric not null
    check (total_requested_size >= 0),
  fill_rate numeric
    check (fill_rate is null or (fill_rate >= 0 and fill_rate <= 1)),
  mean_theoretical_edge numeric,
  mean_cost_adjusted_edge numeric,
  mean_edge_cost_drag numeric
    check (mean_edge_cost_drag is null or mean_edge_cost_drag >= 0),
  total_edge_cost_drag numeric
    check (total_edge_cost_drag is null or total_edge_cost_drag >= 0),
  mean_research_slippage numeric
    check (mean_research_slippage is null or mean_research_slippage >= 0),
  mean_fill_slippage numeric
    check (mean_fill_slippage is null or mean_fill_slippage >= 0),
  partial_fill_count integer not null
    check (partial_fill_count >= 0),
  negative_cost_adjusted_edge_count integer not null
    check (negative_cost_adjusted_edge_count >= 0),
  largest_single_trade_cost_drag numeric
    check (largest_single_trade_cost_drag is null or largest_single_trade_cost_drag >= 0),
  payload_json jsonb not null
    check (jsonb_typeof(payload_json) = 'object'),
  paper_only boolean not null default true
    check (paper_only is true),
  report_only boolean not null default true
    check (report_only is true),
  readonly boolean not null default true
    check (readonly is true),
  inserted_at timestamptz not null default now(),
  check (total_filled_size <= total_requested_size),
  check (partial_fill_count <= trade_count),
  check (negative_cost_adjusted_edge_count <= trade_count),
  check ((trade_count = 0 and total_filled_size = 0 and total_requested_size = 0 and fill_rate is null and mean_theoretical_edge is null and mean_cost_adjusted_edge is null and mean_edge_cost_drag is null and total_edge_cost_drag is null and mean_research_slippage is null and mean_fill_slippage is null and largest_single_trade_cost_drag is null and partial_fill_count = 0 and negative_cost_adjusted_edge_count = 0) or trade_count > 0),
  check (trade_count = 0 or (total_filled_size > 0 and total_requested_size > 0 and fill_rate is not null and mean_theoretical_edge is not null and mean_cost_adjusted_edge is not null and mean_edge_cost_drag is not null and total_edge_cost_drag is not null and mean_research_slippage is not null and largest_single_trade_cost_drag is not null)),
  check (trade_count = 0 or fill_rate = round(total_filled_size / nullif(total_requested_size, 0), 6)),
  check (payload_json ? 'generated_at'
    and jsonb_typeof(payload_json -> 'generated_at') = 'string'
    and (payload_json ->> 'generated_at')::timestamptz = generated_at),
  check (payload_json ? 'config_version'
    and jsonb_typeof(payload_json -> 'config_version') = 'string'
    and payload_json ->> 'config_version' = config_version),
  check (payload_json ? 'trade_count'
    and jsonb_typeof(payload_json -> 'trade_count') = 'number'
    and (payload_json ->> 'trade_count')::integer = trade_count),
  check (payload_json ? 'total_filled_size'
    and jsonb_typeof(payload_json -> 'total_filled_size') = 'string'
    and (payload_json ->> 'total_filled_size')::numeric = total_filled_size),
  check (payload_json ? 'total_requested_size'
    and jsonb_typeof(payload_json -> 'total_requested_size') = 'string'
    and (payload_json ->> 'total_requested_size')::numeric = total_requested_size),
  check (payload_json ? 'fill_rate'
    and ((fill_rate is null
          and payload_json -> 'fill_rate' = 'null'::jsonb)
        or (jsonb_typeof(payload_json -> 'fill_rate') = 'string'
          and (payload_json ->> 'fill_rate')::numeric = fill_rate))),
  check (payload_json ? 'mean_theoretical_edge'
    and ((mean_theoretical_edge is null
          and payload_json -> 'mean_theoretical_edge' = 'null'::jsonb)
        or (jsonb_typeof(payload_json -> 'mean_theoretical_edge') = 'string'
          and (payload_json ->> 'mean_theoretical_edge')::numeric = mean_theoretical_edge))),
  check (payload_json ? 'mean_cost_adjusted_edge'
    and ((mean_cost_adjusted_edge is null
          and payload_json -> 'mean_cost_adjusted_edge' = 'null'::jsonb)
        or (jsonb_typeof(payload_json -> 'mean_cost_adjusted_edge') = 'string'
          and (payload_json ->> 'mean_cost_adjusted_edge')::numeric = mean_cost_adjusted_edge))),
  check (payload_json ? 'mean_edge_cost_drag'
    and ((mean_edge_cost_drag is null
          and payload_json -> 'mean_edge_cost_drag' = 'null'::jsonb)
        or (jsonb_typeof(payload_json -> 'mean_edge_cost_drag') = 'string'
          and (payload_json ->> 'mean_edge_cost_drag')::numeric = mean_edge_cost_drag))),
  check (payload_json ? 'total_edge_cost_drag'
    and ((total_edge_cost_drag is null
          and payload_json -> 'total_edge_cost_drag' = 'null'::jsonb)
        or (jsonb_typeof(payload_json -> 'total_edge_cost_drag') = 'string'
          and (payload_json ->> 'total_edge_cost_drag')::numeric = total_edge_cost_drag))),
  check (payload_json ? 'mean_research_slippage'
    and ((mean_research_slippage is null
          and payload_json -> 'mean_research_slippage' = 'null'::jsonb)
        or (jsonb_typeof(payload_json -> 'mean_research_slippage') = 'string'
          and (payload_json ->> 'mean_research_slippage')::numeric = mean_research_slippage))),
  check (payload_json ? 'mean_fill_slippage'
    and ((mean_fill_slippage is null
          and payload_json -> 'mean_fill_slippage' = 'null'::jsonb)
        or (jsonb_typeof(payload_json -> 'mean_fill_slippage') = 'string'
          and (payload_json ->> 'mean_fill_slippage')::numeric = mean_fill_slippage))),
  check (payload_json ? 'partial_fill_count'
    and jsonb_typeof(payload_json -> 'partial_fill_count') = 'number'
    and (payload_json ->> 'partial_fill_count')::integer = partial_fill_count),
  check (payload_json ? 'negative_cost_adjusted_edge_count'
    and jsonb_typeof(payload_json -> 'negative_cost_adjusted_edge_count') = 'number'
    and (payload_json ->> 'negative_cost_adjusted_edge_count')::integer = negative_cost_adjusted_edge_count),
  check (payload_json ? 'largest_single_trade_cost_drag'
    and ((largest_single_trade_cost_drag is null
          and payload_json -> 'largest_single_trade_cost_drag' = 'null'::jsonb)
        or (jsonb_typeof(payload_json -> 'largest_single_trade_cost_drag') = 'string'
          and (payload_json ->> 'largest_single_trade_cost_drag')::numeric = largest_single_trade_cost_drag))),
  check (payload_json ? 'paper_only'
    and payload_json -> 'paper_only' = 'true'::jsonb),
  check (payload_json ? 'report_only'
    and payload_json -> 'report_only' = 'true'::jsonb),
  check (payload_json ? 'readonly'
    and payload_json -> 'readonly' = 'true'::jsonb)
);

create index if not exists idx_ptcar_generated_inserted_report
  on public.paper_trade_cost_audit_reports (generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists idx_ptcar_config_generated
  on public.paper_trade_cost_audit_reports (config_version, generated_at desc);

create index if not exists idx_ptcar_payload_json_gin
  on public.paper_trade_cost_audit_reports using gin (payload_json jsonb_path_ops);
