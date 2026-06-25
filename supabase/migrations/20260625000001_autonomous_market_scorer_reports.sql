create table if not exists public.autonomous_market_scorer_reports (
    report_sha256 text primary key,
    generated_at timestamptz not null,
    config_version text not null,
    gate_status text not null,
    markets_scored integer not null,
    markets_skipped integer not null,
    markets_blocked integer not null,
    top_total_score numeric not null,
    average_total_score numeric not null,
    total_recommended_notional numeric not null,
    paper_only boolean not null default true,
    report_only boolean not null default true,
    readonly boolean not null default true,
    reason_codes jsonb not null,
    score_rows jsonb not null,
    payload jsonb not null,
    inserted_at timestamptz not null default now(),
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
    check (gate_status in ('pass', 'watch', 'blocked')),
    check (markets_scored >= 0),
    check (markets_skipped >= 0),
    check (markets_blocked >= 0),
    check (top_total_score >= 0),
    check (average_total_score >= 0),
    check (total_recommended_notional >= 0),
    check (paper_only is true),
    check (report_only is true),
    check (readonly is true),
    check (jsonb_typeof(reason_codes) = 'array'),
    check (jsonb_typeof(score_rows) = 'array'),
    check (jsonb_typeof(payload) = 'object')
);

create index if not exists autonomous_market_scorer_reports_generated_at_idx
    on public.autonomous_market_scorer_reports (generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists autonomous_market_scorer_reports_gate_status_order_idx
    on public.autonomous_market_scorer_reports (gate_status, generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists autonomous_market_scorer_reports_config_order_idx
    on public.autonomous_market_scorer_reports (config_version, generated_at desc, inserted_at desc, report_sha256 desc);
