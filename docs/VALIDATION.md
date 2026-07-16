# Validation status

## What was checked by the automated suite

- unit-conversion consistency;
- Pydantic input and proportion validation;
- symmetric TCG for symmetric cases;
- displacement volume increasing with draft;
- weight–buoyancy equilibrium residual;
- LCB–LCG equilibrium residual;
- free-surface correction for partial/full tanks;
- corrected GM identity;
- increasing effective power with speed;
- engine installation filtering;
- mandatory requirement failure cannot be hidden;
- every variant uses the same evaluator;
- three distinct alternatives when enough compliant variants exist;
- Y-up 3D coordinate convention;
- five report formats are generated and nonempty;
- three demonstration cases pass their synthetic mandatory gates;
- TypeScript, ESLint and production PWA build.

## What was not validated

- accuracy against tank tests or sea trials;
- statutory intact-stability criteria;
- full Savitsky numerical reproduction;
- porpoising boundary prediction;
- classification-society scantlings;
- manufacturer engine curves and current prices;
- real vessel geometry, weights or downflooding points.

Software regression tests do not constitute vessel validation. Published or
manual benchmark cases must include source, exact inputs, acceptance tolerance
and independent engineering review before a method can be promoted from
preliminary to validated.
