# AutoVigil - Devpost (final version)

## Tagline (<= 200 chars)
Drug-safety statistics + IBM Granite applied to public NHTSA complaints: AutoVigil flags dangerous driver-assist defects like phantom braking months before investigations open.

## Inspiration
Medicines are monitored after launch: regulators mine patient reports for "more reports than expected" and pull bad drugs early. Cars now get driver-assist software that changes overnight by over-the-air update, yet phantom-braking complaints pile up in NHTSA's public database for months before anyone opens an investigation (Tesla PE22-002 opened in Feb 2022 after hundreds of complaints). A 2023 federal audit found NHTSA preliminary evaluations take ~617 days on average. We asked: if we treat car complaints the way pharmacovigilance treats drug reports, how early could the public see the problem?

## What it does
AutoVigil has two sides:
- **Driver Intake agent (watsonx Orchestrate):** a driver says "my car braked hard with nothing in front of me." The agent checks whether an early-warning alarm is active for that model, shows how many similar public reports exist (with a real example), tells the driver what to do now, and asks the follow-up questions engineers need (speed, feature engaged, conditions, software update) to draft a complete NHTSA complaint with a completeness score.
- **Defect Analyst agent (watsonx Orchestrate):** for regulators, journalists and safety teams. It ranks active alarms, pulls the evidence (trend vs expected, crashes, injuries, example narratives, share mentioning software updates) and drafts a one-page investigation memo - making defect triage less boring.
- **Dashboard:** replays history week by week to show when AutoVigil's alarm turned on versus when NHTSA opened each investigation, plus a live alarm board.

## How we built it
- **Data:** NHTSA ODI flat files - 1.2M complaint rows (859,888 vehicle complaints since 2014), 5,349 investigations, recalls. 13 ADAS investigations curated as ground truth.
- **No-peeking replay:** for every week 2016-2026 we only use complaints NHTSA had already received, grouped by make x model x problem, in a 26-week incident window.
- **Pharmacovigilance statistics:** Proportional Reporting Ratio (PRR >= 2, chi-square >= 4, n >= 3) and Bayesian BCPNN IC025.
- **IBM Granite 4 (granite-4-h-small) on watsonx.ai** read and coded 29,350 ADAS/brake complaint narratives into 10 failure modes (phantom braking, failed to brake, false warning, lane-keep wrong steer, ...) plus speed, feature engaged and software-update mentions - total cost under $1 of credit.
- **Validation:** we hand-labelled 99 random complaints. Granite's phantom-braking label: precision 0.91, recall 0.89 (overall 10-class kappa 0.44; main confusion: over-using "system unavailable").
- **IBM Granite TTM** time-series forecasts (watsonx.ai) as a third detector, benchmarked in the same replay.
- **ElevenLabs** text-to-speech reads alarm summaries aloud on the dashboard ("Listen").
- **FastAPI backend on IBM Code Engine** (image built by GitHub Actions) exposing 6 OpenAPI tools; imported into **watsonx Orchestrate** as the agents' toolset. Dashboard served from the same app (Chart.js).

## Results (research questions)
- **RQ1 - lead time:** the component-code detector flagged **8 of 8** complaint-driven ADAS investigations before NHTSA opened them, **median 46 weeks early** (range 7-113). Cost: ~54 alarmed model streams per year, 4.5% of which were later investigated.
- **RQ2 - does LLM coding help?** Granite failure-mode streams caught 6 of 8 (median 39 weeks) with **half the alarms (27/yr) and double the precision (9.4%)**. The two misses are explainable (VW Atlas complaints were mostly parking-brake electrical faults, not ADAS; Honda Insight/Passport had too few reports). The detectors are complementary.
- **RQ5 - IBM time-series foundation model:** we also ran IBM Granite TinyTimeMixer (granite-ttm-512-96-r2 on watsonx.ai) as a forecaster - alarm when a car's complaints exceed 2x its own forecast. It caught only 4 of 8, 2-4 weeks early: forecasting a car against its own history adapts to slowly rising complaints, while comparing it against all other cars (disproportionality) sees them early. A useful negative result - TTM is an acute-surge detector, not an early-warning one.
- **Live today:** the alarm board currently flags e.g. Chevrolet Equinox EV and Hyundai Tucson phantom braking - statistical signals worth a closer look, not proof of a defect.

## Challenges we ran into
- Making the backtest honest: using received dates to avoid hindsight, and counting false alarms, not just hits.
- LLM labels drifting into feature names (~5% invalid) and confusing parking-brake electrical faults with ADAS phantom braking - fixed with stricter rules and examples, measured against hand labels.
- Deploying on a hackathon cloud account with no container registry: we built the image in GitHub Actions and ran it on Code Engine.

## Accomplishments we're proud of
A dated, reproducible answer to "how early could the public have known?" - plus a working agent a real driver can talk to today.

## What we learned
Public complaint data carries a real early signal; the hard part is the false-alarm budget. LLM coding turns noisy component codes into specific, actionable failure modes.

## What's next
Weekly automatic refresh on Code Engine; voice intake for the driver agent (speech-to-text + ElevenLabs); a change-point test of whether alarms start right after over-the-air software updates; exposure normalisation (vehicles on the road).

## Limitations
Voluntary, biased reports; no exposure data; 8 ground-truth events is a small sample; signals are hypotheses for human review; no repair or legal advice.

## Built with
python, pandas, numpy, scipy, fastapi, ibm-watsonx-ai, ibm-granite, granite-ttm, watsonx-orchestrate, elevenlabs, ibm-code-engine, docker, github-actions, chart.js, nhtsa-open-data

## Links
- Dashboard: https://autovigil-api.2f6fdusn6le3.us-south.codeengine.appdomain.cloud/
- API docs: https://autovigil-api.2f6fdusn6le3.us-south.codeengine.appdomain.cloud/docs
- GitHub: https://github.com/sruthyrb-create/autovigil
