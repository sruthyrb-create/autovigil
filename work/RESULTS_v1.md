# AutoVigil preliminary results (v1, disproportionality only, NHTSA component codes)

Data: 1,208,261 complaint-component rows (859,888 complaints) received 2014-01-01 to 2026-10-01.
Method: weekly as-of replay 2016-2026, 26-week incident window, only complaints received by each week.
Stream = make x model x component group. Signal = PRR >= 2, chi2 >= 4, >= N reports (Evans criteria).
Lead time = investigation open date minus start of the alarm run still active within 8 weeks of opening.

Primary set: 8 complaint-driven ADAS false-activation investigations (2019-2024).
Default thresholds (>=3 reports, PRR>=2): 8/8 caught before opening; lead times 7-113 weeks, median ~46 weeks.
Cost: ~54 make-model streams alarmed per year in FCA + lane-departure groups (13 of 288 alarmed streams were later investigated).

Trade-off (see alarm_burden.csv):
| min reports | min PRR | caught | median lead (wk) | streams alarmed/yr |
| 3 | 2 | 8/8 | 46 | 53.5 |
| 5 | 2 | 7/8 | 64 | 36.6 |
| 10 | 2 | 6/8 | 54 | 19.1 |
| 10 | 3 | 5/8 | 48 | 14.2 |
| 20 | 3 | 4/8 | 25 | 8.9 |

Crash-triggered probes (Autopilot, BlueCruise, FSD): complaint signals weak or unrelated, as expected.
Caveats: "no investigation" is not "no defect", so alarm counts are upper bounds on false alarms; small n (8).

## RQ2 (preliminary) - Granite 4 coding vs 99 hand labels (labels/label_100.xlsx)
- Granite v2 run: 11,870 priority-1 complaints coded; 587 (4.9%) invalid labels (feature names instead of failure modes).
- v2 vs hand labels (n=99): exact agreement 58%, Cohen's kappa 0.44.
- Core signal false_braking: precision 0.91, recall 0.89.
- Main error: Granite over-uses system_unavailable (12 of 42 disagreements: conventional_brake_fault/other -> system_unavailable).
- v1 overlap only 30 complaints (acc 0.77, kappa 0.66) - not comparable.
- Disagreements: work/label_disagreements_v2.csv

## RQ2 - Granite-coded streams vs NHTSA component-code streams (all 29,350 coded; 24,836 valid in FCA/LANE/ADAS groups, 781 models)
Default thresholds (n>=3, PRR>=2, chi2>=4):
- NHTSA codes: 8/8 caught, median lead 46 wk, 288 streams alarmed 2016-26 (53.5/yr), 13 later investigated (4.5%).
- Granite failure modes: 6/8 caught, median lead 39 wk, 138 streams alarmed (27.0/yr), 13 later investigated (9.4%).
=> Granite coding halves the alarm burden and doubles precision, at the cost of 2 misses (VW Atlas - mostly parking-brake
   complaints, not ADAS; Honda Insight/Passport - few reports). At matched burden (~17-19/yr) the two are similar
   (NHTSA 6/8 @54 wk vs Granite 5/8 @54 wk). Granite's added value: alarms are about a specific failure (phantom braking),
   not a component, so they are easier to act on. Table: work/alarm_burden_rq2.csv; per-event: work/backtest_granite.csv
