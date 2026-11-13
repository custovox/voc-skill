# Prioritising pain points: frequency x intensity

## Score

`score = share x intensity`

- `share` = number of verbatims mentioning the pain point / number of verbatims analysed.
- `intensity` = typical intensity of the pain point on the 1-5 scale (see the analysis grid).

The score is computed by the `export_report` tool, so it is identical from one run to the
next for the same inputs. Without the MCP server, compute it yourself the same way.

## Quadrants

Default thresholds: share >= 10 % is "frequent", intensity >= 3.5 is "intense".

| | Intensity < 3.5 | Intensity >= 3.5 |
|---|---|---|
| **Share >= 10 %** | 2 · Widespread irritant: optimise the process | 1 · Urgent: fix now, top management |
| **Share < 10 %** | 4 · Monitor | 3 · Acute, targeted issue: specific fix, check if growing |

## Tie-breakers and adjustments (state them if used)

- Business impact: a pain point linked to churn, refunds or legal risk goes up.
- Effort: between two similar scores, start with the quick win.
- Kano lens (Kano et al., 1984): problems on "must-be" attributes (the parcel arrives,
  the product works) weigh more than missing "attractive" features.
- Effort/impact of actions is assessed separately in the action plan.

## Action plan format

| Field | Content |
|---|---|
| action | concrete, verifiable ("Add a damage-proof insert for glass jars") |
| themes | pain points addressed |
| horizon | quick win (< 1 month), 3 months, 6 months+ |
| impact / effort | low, medium, high |
| owner | team, not a person (logistics, customer service, product, e-commerce) |
| kpi | indicator and target ("damaged-parcel complaints: -50 % in 3 months") |
