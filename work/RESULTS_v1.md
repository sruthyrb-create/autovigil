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
