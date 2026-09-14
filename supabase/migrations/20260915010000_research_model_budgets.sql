-- Append-only shared call allowances. Not provider billing or model approval.
create table research_capture.model_budgets (
  budget_id text primary key check (budget_id ~ '^[A-Za-z0-9_.:-]{1,128}$'),
  payload text not null check (octet_length(payload) between 1 and 32768),
  payload_sha256 text not null check (payload_sha256 ~ '^[a-f0-9]{64}$'),
  created_at timestamptz not null check (isfinite(created_at)),
  paper_only boolean not null default true check (paper_only is true),
  report_only boolean not null default true check (report_only is true),
  readonly boolean not null default true check (readonly is true),
  check (encode(sha256(convert_to(payload,'UTF8')),'hex') = payload_sha256)
);

create function research_capture.stamp_model_budget() returns trigger
language plpgsql set search_path = pg_catalog as $$
declare body jsonb; item jsonb; ids text[] := '{}'; expiry timestamptz;
begin
  perform pg_advisory_xact_lock(hashtextextended('polymarket/model_budget/' || new.budget_id,0));
  new.created_at := clock_timestamp();
  body := new.payload::jsonb;
  expiry := (body ->> 'expires_at')::timestamptz;
  if (body ->> 'schema_version' = 'research-model-budget-v1'
      and body ->> 'budget_id' = new.budget_id
      and body ->> 'provider_id' ~ '^[A-Za-z0-9_.:-]{1,128}$'
      and length(body ->> 'model_id') between 1 and 128
      and body ->> 'currency' ~ '^[A-Z]{3}$'
      and (body ->> 'total_micros')::bigint between 1 and 1000000000000000
      and (body ->> 'per_call_micros')::bigint between 1 and 1000000000000
      and (body ->> 'per_call_micros')::bigint <= (body ->> 'total_micros')::bigint
      and (body ->> 'max_calls')::integer between 1 and 3200
      and (body ->> 'max_message_bytes')::integer between 1 and 2000000
      and (body ->> 'max_output_tokens')::integer between 1 and 8192
      and isfinite(expiry) and expiry > new.created_at
      and body -> 'cost_bound_attested' = 'true'::jsonb
      and body -> 'paper_only' = 'true'::jsonb
      and body -> 'report_only' = 'true'::jsonb
      and body -> 'readonly' = 'true'::jsonb
      and body ->> 'bound_reference_sha256' ~ '^[a-f0-9]{64}$'
      and jsonb_typeof(body -> 'request_keys') = 'array'
      and jsonb_array_length(body -> 'request_keys') between 1 and 100) is not true then
    raise exception 'research_budget_policy_invalid';
  end if;
  for item in select value from jsonb_array_elements(body -> 'request_keys') loop
    if (jsonb_typeof(item) = 'array' and jsonb_array_length(item) = 2
        and item ->> 0 ~ '^[A-Za-z0-9_.:-]{1,128}$'
        and item ->> 1 ~ '^[a-f0-9]{64}$') is not true
        or item ->> 0 = any(ids) then
      raise exception 'research_budget_request_keys_invalid';
    end if;
    ids := array_append(ids,item ->> 0);
  end loop;
  return new;
end $$;

create trigger stamp_model_budget before insert on research_capture.model_budgets
  for each row execute function research_capture.stamp_model_budget();

create table research_capture.model_call_reservations (
  budget_id text not null references research_capture.model_budgets(budget_id),
  record_id text not null references research_capture.execution_claims(record_id),
  request_sha256 text not null check (request_sha256 ~ '^[a-f0-9]{64}$'),
  call_number integer not null check (call_number between 1 and 32),
  reservation_number integer not null check (reservation_number between 1 and 3200),
  reserved_micros bigint not null check (reserved_micros between 1 and 1000000000000),
  reserved_at timestamptz not null check (isfinite(reserved_at)),
  message_sha256 text not null check (message_sha256 ~ '^[a-f0-9]{64}$'),
  message_bytes integer not null check (message_bytes between 1 and 2000000),
  max_output_tokens integer not null check (max_output_tokens between 1 and 8192),
  paper_only boolean not null default true check (paper_only is true),
  report_only boolean not null default true check (report_only is true),
  readonly boolean not null default true check (readonly is true),
  primary key (record_id,call_number),
  unique (budget_id,reservation_number)
);

create function research_capture.stamp_model_call() returns trigger
language plpgsql set search_path = pg_catalog as $$
declare policy jsonb; claimed research_capture.execution_claims%rowtype;
        count_so_far integer; last_time timestamptz; last_call integer;
begin
  perform pg_advisory_xact_lock(hashtextextended('polymarket/model_budget/' || new.budget_id,0));
  select payload::jsonb into policy from research_capture.model_budgets where budget_id=new.budget_id;
  select * into claimed from research_capture.execution_claims where record_id=new.record_id;
  new.reserved_at := clock_timestamp();
  if (claimed.request_sha256 = new.request_sha256
      and claimed.model_id = policy ->> 'model_id'
      and claimed.team_id in ('crypto_btc','crypto_eth')
      and new.reserved_at >= claimed.claimed_at
      and new.reserved_at < (claimed.request_payload::jsonb ->> 'forecast_cutoff_at')::timestamptz
      and new.reserved_at < (policy ->> 'expires_at')::timestamptz
      and new.message_bytes <= (policy ->> 'max_message_bytes')::integer
      and new.max_output_tokens <= (policy ->> 'max_output_tokens')::integer
      and new.max_output_tokens <= (claimed.request_payload::jsonb #>> '{limits,max_output_tokens}')::integer
      and new.call_number <= (claimed.request_payload::jsonb #>> '{limits,max_model_calls}')::integer) is not true
      or not exists (select 1 from jsonb_array_elements(policy -> 'request_keys') k(value)
        where k.value ->> 0 = new.record_id and k.value ->> 1 = new.request_sha256)
      or exists (select 1 from research_capture.attempts where record_id=new.record_id) then
    raise exception 'research_budget_call_not_allowed';
  end if;
  select coalesce(max(reservation_number),0),max(reserved_at) into count_so_far,last_time
    from research_capture.model_call_reservations where budget_id=new.budget_id;
  select coalesce(max(call_number),0) into last_call
    from research_capture.model_call_reservations where record_id=new.record_id;
  new.reservation_number := count_so_far+1;
  new.reserved_micros := (policy ->> 'per_call_micros')::bigint;
  if new.call_number <> last_call+1
      or new.reservation_number > (policy ->> 'max_calls')::integer
      or new.reserved_micros * new.reservation_number > (policy ->> 'total_micros')::bigint
      or (last_time is not null and new.reserved_at < last_time) then
    raise exception 'research_budget_allowance_exhausted';
  end if;
  -- The unique budget/sequence constraint also rejects concurrent stale-snapshot
  -- insertions; there is no mutable/refundable counter or lease to reclaim.
  return new;
end $$;

create trigger stamp_model_call before insert on research_capture.model_call_reservations
  for each row execute function research_capture.stamp_model_call();
create trigger immutable_model_budgets before update or delete on research_capture.model_budgets
  for each row execute function research_capture.reject_mutation();
create trigger no_truncate_model_budgets before truncate on research_capture.model_budgets
  for each statement execute function research_capture.reject_mutation();
create trigger immutable_model_reservations before update or delete on research_capture.model_call_reservations
  for each row execute function research_capture.reject_mutation();
create trigger no_truncate_model_reservations before truncate on research_capture.model_call_reservations
  for each statement execute function research_capture.reject_mutation();
revoke all on research_capture.model_budgets,research_capture.model_call_reservations from public;
revoke all on function research_capture.stamp_model_budget(),research_capture.stamp_model_call() from public;
comment on table research_capture.model_call_reservations is
  'Nonrefundable assumed upper charges committed before client entry, not proof of provider calls or actual billing.';
