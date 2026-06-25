create table if not exists public.paper_execution_reconciliation_reports (
    report_sha256 text primary key,
    generated_at timestamptz not null,
    config_version text not null,
    reconciliation_status text not null,
    total_positions integer not null,
    filled_pending_count integer not null,
    settled_win_count integer not null,
    settled_loss_count integer not null,
    expired_count integer not null,
    cancelled_count integer not null,
    total_fill_notional numeric not null,
    total_cost_basis numeric not null,
    total_outcome_value numeric,
    total_pnl numeric,
    realized_pnl numeric not null,
    unrealized_pnl numeric not null,
    position_rows_json jsonb not null,
    reason_codes_json jsonb not null,
    payload_json jsonb not null,
    paper_only boolean not null default true,
    report_only boolean not null default true,
    readonly boolean not null default true,
    inserted_at timestamptz not null default now(),
    check (report_sha256 ~ '^[a-f0-9]{64}$'),
    check (reconciliation_status in (
        'reconciled', 'has_pending', 'has_discrepancies'
    )),
    check (total_positions >= 0),
    check (filled_pending_count >= 0),
    check (settled_win_count >= 0),
    check (settled_loss_count >= 0),
    check (expired_count >= 0),
    check (cancelled_count >= 0),
    check (total_fill_notional >= 0),
    check (total_cost_basis >= 0),
    check (total_outcome_value >= 0 or total_outcome_value is null),
    check (jsonb_typeof(position_rows_json) = 'array'),
    check (jsonb_typeof(reason_codes_json) = 'array'),
    check (jsonb_typeof(payload_json) = 'object'),
    check (paper_only is true),
    check (report_only is true),
    check (readonly is true)
);

create index if not exists paper_execution_reconciliation_generated_order_idx
    on public.paper_execution_reconciliation_reports (generated_at desc, inserted_at desc, report_sha256 desc);

create index if not exists paper_execution_reconciliation_config_order_idx
    on public.paper_execution_reconciliation_reports (
        config_version,
        generated_at desc,
        inserted_at desc,
        report_sha256 desc
    );

create index if not exists paper_execution_reconciliation_status_order_idx
    on public.paper_execution_reconciliation_reports (
        reconciliation_status,
        generated_at desc,
        inserted_at desc,
        report_sha256 desc
    );
