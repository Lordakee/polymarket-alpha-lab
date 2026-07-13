COMMENT ON COLUMN public.team_forecasts.forecast_probability IS
    'Canonical Decimal P(YES) for the event; never P(selected_side).';
COMMENT ON COLUMN public.team_forecasts.selected_side IS
    'Paper-review side being evaluated; does not reorient forecast_probability.';
