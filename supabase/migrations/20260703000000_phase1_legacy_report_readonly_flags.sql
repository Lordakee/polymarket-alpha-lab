alter table if exists public.paper_trade_journal_records
  add column if not exists report_only boolean not null default true,
  add column if not exists readonly boolean not null default true;

alter table if exists public.paper_trade_journal_records
  add constraint paper_trade_journal_records_report_only_true check (report_only is true) not valid,
  add constraint paper_trade_journal_records_readonly_true check (readonly is true) not valid;

alter table if exists public.paper_trade_journal_records validate constraint paper_trade_journal_records_report_only_true;
alter table if exists public.paper_trade_journal_records validate constraint paper_trade_journal_records_readonly_true;

alter table if exists public.paper_nav_snapshots
  add column if not exists report_only boolean not null default true,
  add column if not exists readonly boolean not null default true;

alter table if exists public.paper_nav_snapshots
  add constraint paper_nav_snapshots_report_only_true check (report_only is true) not valid,
  add constraint paper_nav_snapshots_readonly_true check (readonly is true) not valid;

alter table if exists public.paper_nav_snapshots validate constraint paper_nav_snapshots_report_only_true;
alter table if exists public.paper_nav_snapshots validate constraint paper_nav_snapshots_readonly_true;

alter table if exists public.outcome_tracking_reports
  add column if not exists report_only boolean not null default true,
  add column if not exists readonly boolean not null default true;

alter table if exists public.outcome_tracking_reports
  add constraint outcome_tracking_reports_report_only_true check (report_only is true) not valid,
  add constraint outcome_tracking_reports_readonly_true check (readonly is true) not valid;

alter table if exists public.outcome_tracking_reports validate constraint outcome_tracking_reports_report_only_true;
alter table if exists public.outcome_tracking_reports validate constraint outcome_tracking_reports_readonly_true;

alter table if exists public.paper_strategy_cycle_reports
  add column if not exists readonly boolean not null default true;

alter table if exists public.paper_strategy_cycle_reports
  add constraint paper_strategy_cycle_reports_readonly_true check (readonly is true) not valid;

alter table if exists public.paper_strategy_cycle_reports validate constraint paper_strategy_cycle_reports_readonly_true;
