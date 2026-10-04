# AutoVigil — Devpost submission (final, paste field by field)

## Project name
AutoVigil

## Elevator pitch (max 200 characters)
Drug-safety statistics + IBM Granite on public NHTSA complaints flag dangerous driver-assist defects early: 66 weeks before Hyundai's 2026 phantom-braking recall.

## Track
Enchanted Transit

## Sponsor challenges
IBM (watsonx Orchestrate + watsonx.ai) · ElevenLabs

---

## Inspiration
In May 2026 Hyundai recalled 421,078 Tucsons and Santa Cruzes because camera software could "prematurely apply the brakes" — phantom braking — after 376 field reports, four crashes and four injuries. In July 2026 NHTSA closed its Tesla phantom-braking investigation, four years after opening it on top of 300+ public complaints. And automatic emergency braking is about to become mandatory on every new U.S. car (FMVSS 127, currently September 2029).

Driver-assist software now changes overnight, but finding its failures still takes years — even though drivers describe them, in their own words, in NHTSA's public complaint database. Medicine solved this problem decades ago: pharmacovigilance watches patient reports for "more reports than expected" and pulls dangerous drugs early. We asked: what if we watched cars the way we watch drugs?

## What it does
AutoVigil is a web app with three faces, all on one live API:

- **Driver app** (/driver) — pick your car (or one you're about to buy): a red/green early-warning status, how many owners report the same problem, a monthly trend, whether a recall already covers *that* problem, what to do today, and a guided report with a live completeness meter that drafts your NHTSA complaint. Prefer to talk? An **ElevenLabs voice agent** checks the live alarm data and interviews you like a safety engineer.
- **Analyst console** (/analyst) — for regulators, journalists, fleets and safety teams: a ranked alarm board with a time machine to any past week, "unrecalled" flags, an evidence panel (trend vs expected, crashes, injuries, software-update share, quotes, related recalls) and a one-click investigation memo **written by IBM Granite**. The same work is available conversationally through two **watsonx Orchestrate** agents (Driver Intake and Defect Analyst).
- **Research page** (/research) — the week-by-week replay and backtest, so anyone can audit how early it would have worked.

## How we built it
- **Data:** NHTSA ODI public flat files — 1.2M complaint rows (859,888 vehicle complaints since 2014), 5,349 investigations, and recalls.
- **No-peeking replay:** for every week 2016–2026 we use only complaints NHTSA had already received, grouped by make × model × problem over a 26-week incident window.
- **Pharmacovigilance statistics:** Proportional Reporting Ratio (PRR ≥ 2, χ² ≥ 4, n ≥ 3) and Bayesian BCPNN IC025 for ranking.
- **IBM Granite 4 (granite-4-h-small) on watsonx.ai** read 29,350 driver-assist/brake narratives and coded the failure mode (phantom braking, failed to brake, false warning, lane-keep wrong steer, …), speed, feature engaged and software-update mentions — for under $1 of credit. Validated against 99 hand labels: phantom braking precision 0.91, recall 0.89.
- **IBM Granite TTM (granite-ttm-512-96-r2) on watsonx.ai** benchmarked as a third, forecasting-based detector in the same replay.
- **IBM Code Engine** runs the FastAPI backend and all three web pages (image built by GitHub Actions).
- **watsonx Orchestrate**: two deployed agents using the API's OpenAPI tools; **Granite** also writes analyst memos directly in the console via the watsonx.ai API.
- **ElevenLabs Agents** for the two-way voice assistant (webhook tools call our API) and ElevenLabs text-to-speech for read-aloud briefs.

## Results
- **Past investigations (RQ1):** 8 of 8 complaint-driven driver-assist investigations flagged before NHTSA opened them — **median 46 weeks early** (range 7–113). Cost: ~54 alarmed model streams per year, ~1 in 20 later investigated.
- **Granite coding (RQ2):** Granite failure-mode streams caught 6 of 8 (median 39 weeks) with **half the alarms and double the precision**.
- **Independent check against recalls (never used to build the alarms):** the Hyundai Tucson phantom-braking alarm was on **66 weeks before the May 2026 recall of 421,078 vehicles** — a car not in our design set. Hyundai's own safety office opened its internal investigation in January 2025; AutoVigil's public-data alarm turned on in February 2025; NHTSA contacted Hyundai in September 2025. Also Tesla Model 3 (50 weeks before recall 21V-846) and Mazda CX-90 (29 weeks before 24V-349). Overall 4 of 12 false-braking recall campaigns since 2017 were preceded by an alarm; most misses are low-volume vehicles with almost no complaints.
- **Foundation-model forecasting (RQ5):** Granite TTM caught only 4 of 8, 2–4 weeks early — forecasting a car against its own history adapts to slowly rising complaints, while comparing it against all other cars catches them early. A useful negative result.

## Challenges we ran into
- Making the backtest honest: received-date cut-offs, incident-date windows, counting false alarms, reporting misses.
- LLM labels drifting into feature names (~5% invalid) and confusing parking-brake electrical faults with ADAS phantom braking — fixed with stricter rules and examples, measured against hand labels.
- Deploying on a hackathon cloud account without a container registry — solved with GitHub Actions → GitHub Container Registry → IBM Code Engine.

## Accomplishments that we're proud of
A dated, reproducible answer to "how early could the public have known?" — validated on past investigations *and* on a 2026 recall we never trained on — inside a working product that a frightened driver can simply talk to.

## What we learned
Public complaints carry a strong early signal; the hard part is the false-alarm budget. LLM coding turns vague component codes into specific, actionable failure modes. Comparing against peers beats self-forecasting for slow-building safety problems.

## What's next
Weekly automatic refresh on Code Engine; alerts for owners and fleets; a change-point test of whether alarms begin right after over-the-air software updates; exposure normalisation (vehicles on the road); multilingual voice intake.

## Limitations
Voluntary, biased reports; no exposure data; small number of ground-truth events; signals are hypotheses for human review — not proof of a defect and not legal or repair advice.

## Built with
python · pandas · numpy · scipy · fastapi · ibm-watsonx-ai · ibm-granite · granite-ttm · watsonx-orchestrate · ibm-code-engine · elevenlabs · docker · github-actions · chart.js · nhtsa-open-data

## Try it out (links)
- App: https://autovigil-api.2f6fdusn6le3.us-south.codeengine.appdomain.cloud/
- Driver app: https://autovigil-api.2f6fdusn6le3.us-south.codeengine.appdomain.cloud/driver
- Analyst console: https://autovigil-api.2f6fdusn6le3.us-south.codeengine.appdomain.cloud/analyst
- Research replay: https://autovigil-api.2f6fdusn6le3.us-south.codeengine.appdomain.cloud/research
- API docs: https://autovigil-api.2f6fdusn6le3.us-south.codeengine.appdomain.cloud/docs
- GitHub: https://github.com/sruthyrb-create/autovigil

---

## IBM challenge — how we used IBM (if the form asks)
1. **watsonx Orchestrate** — two deployed agents, *AutoVigil Driver Intake* and *AutoVigil Defect Analyst*, whose tools are imported from our OpenAPI spec (vehicle status, similar reports, draft complaint, ranked alarms, alarm evidence, backtest). The Analyst agent turns an alarm into an investigation memo in seconds — "make work less boring" for defect analysts.
2. **watsonx.ai — Granite 4** codes every complaint narrative (29,350 so far, < $1) and writes memos in the analyst console.
3. **watsonx.ai — Granite TTM** time-series foundation model, benchmarked as a forecasting detector.
4. **IBM Code Engine** hosts the API and all web pages, scaling to zero when idle.

## ElevenLabs challenge — how we used ElevenLabs
A two-way **ElevenLabs Agents** voice assistant embedded in the driver app: the driver describes what happened, the agent calls AutoVigil's live API (webhook tools for vehicle status and similar reports), tells them whether an alarm is active and how many owners report the same thing, then interviews them for the facts engineers need and reads back a summary. ElevenLabs TTS also reads alarm briefs aloud on the research page.

## Sources for news facts
- Hyundai recall 26V316 timeline: https://thebrakereport.com/hyundai-tucson-santa-cruz-fca-recall-26v316/
- Tesla probe closed (July 2026): https://thebrakereport.com/nhtsa-closes-tesla-phantom-braking-probe/
- FMVSS 127 status (April 2026): https://natlawreview.com/article/road-ahead-fmvss-127-whither-automatic-emergency-braking-mandate
