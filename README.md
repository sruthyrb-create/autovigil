# AutoVigil

**Drug-safety science for the software that drives our cars.**
AutoVigil applies pharmacovigilance statistics and IBM Granite to public NHTSA complaints to flag dangerous driver-assist (ADAS) defects — like phantom braking — months before investigations and recalls.

**Live app:** https://autovigil-api.2f6fdusn6le3.us-south.codeengine.appdomain.cloud/
· [Driver app](https://autovigil-api.2f6fdusn6le3.us-south.codeengine.appdomain.cloud/driver)
· [Analyst console](https://autovigil-api.2f6fdusn6le3.us-south.codeengine.appdomain.cloud/analyst)
· [Research replay](https://autovigil-api.2f6fdusn6le3.us-south.codeengine.appdomain.cloud/research)
· [API docs](https://autovigil-api.2f6fdusn6le3.us-south.codeengine.appdomain.cloud/docs)

Built solo at **Hack Dearborn 5** (Oct 3–4, 2026) · Track: **Enchanted Transit** · IBM watsonx · ElevenLabs

---

## Results at a glance

| Question | Result |
|---|---|
| Past NHTSA driver-assist investigations flagged before they opened | **8 / 8**, median **46 weeks** early (range 7–113) |
| Hyundai Tucson phantom-braking recall, May 2026 (421,078 vehicles) — not in design set | alarm on **66 weeks** before the recall |
| False-braking recall campaigns since 2017 preceded by an alarm | 4 / 12 (misses: mostly low-volume vehicles) |
| IBM Granite failure-mode coding vs NHTSA component codes | **½ the alarms, 2× precision** (6/8 caught, median 39 wk) |
| Granite accuracy vs 99 hand labels (phantom braking) | precision **0.91**, recall **0.89** |
| IBM Granite TTM forecasting detector | 4/8, only 2–4 wk early — self-forecasting misses slow build-ups |
| Cost to code 29,350 narratives with Granite 4 | **< $1** |

All results use a **no-peeking weekly replay**: each week only complaints NHTSA had already received are used. Signals are statistical hypotheses for human review — not proof of a defect.

## What's inside

```
Users ──► Driver app (/driver) ──┐        ElevenLabs voice agent ──┐
          Analyst console ───────┼──► FastAPI on IBM Code Engine ◄─┤
          Research replay ───────┘        ▲          │             watsonx Orchestrate agents
                                          │          └─► Granite memo (watsonx.ai)
          weekly signals (PRR, BCPNN) ────┘
                    ▲
NHTSA complaints ──► Granite 4 failure-mode coding (watsonx.ai) ──► make × model × problem streams
NHTSA investigations + recalls ──► ground truth for the backtest and recall validation
```

| Component | Where |
|---|---|
| Data loading (complaints, investigations, recalls) | `src/load_complaints.py`, `src/load_investigations.py`, `src/build_recalls.py` |
| Ground-truth investigations | `src/ground_truth.py` |
| Disproportionality signals (PRR, χ², BCPNN IC025), weekly as-of | `src/signals.py`, `src/granite_signals.py` |
| Backtest and alarm burden | `src/backtest.py`, `src/alarm_burden.py`, `src/alarm_burden_granite.py` |
| Granite 4 complaint coding (watsonx.ai) | `src/granite_code.py` |
| Granite TTM forecasting detector (watsonx.ai) | `src/ttm_prepare.py`, `src/ttm_detector.py` |
| Recall validation | `src/recall_validation.py` |
| API + web apps | `api/app.py`, `api/*.html` |
| watsonx Orchestrate tools + agent instructions | `orchestrate/` |
| Results write-up | `work/RESULTS_v1.md` |
| Hand labels for Granite validation | `labels/label_100.xlsx` |

## IBM technology
- **watsonx Orchestrate** — *AutoVigil Driver Intake* and *AutoVigil Defect Analyst* agents, tools imported from `orchestrate/autovigil_openapi.json`.
- **watsonx.ai Granite 4** — narrative coding (`src/granite_code.py`) and in-console memo drafting (`/memo`).
- **watsonx.ai Granite TTM** — time-series foundation-model detector (`src/ttm_detector.py`).
- **IBM Code Engine** — hosts the API and web pages (image built by `.github/workflows/docker.yml`).

## ElevenLabs
Two-way voice assistant (ElevenLabs Agents) embedded in the driver app; its webhook tools call `/vehicle_status` and `/similar_reports`. Agent prompt and tool definitions: `orchestrate/elevenlabs_agent.md`. Text-to-speech read-aloud via `/speak`.

## Run it yourself
```bash
conda env create -f environment.yml      # or: pip install -r api/requirements.txt for the API only
cp .env.example .env                      # add WATSONX_APIKEY, WATSONX_PROJECT_ID (never commit .env)
# 1. download NHTSA flat files (complaints, investigations, recalls) into data/  — see README_SETUP.md
python src/load_complaints.py && python src/load_investigations.py
python src/signals.py && python src/backtest.py
python src/granite_code.py --set all      # Granite 4 coding (watsonx.ai)
python src/granite_signals.py && python src/build_recalls.py && python src/recall_validation.py
python src/build_api_data.py
uvicorn api.app:app --reload              # http://localhost:8000
```
Environment variables for the deployed app: `PUBLIC_URL`, `WATSONX_APIKEY`, `WATSONX_PROJECT_ID`, `WATSONX_URL` (Granite memos), `ELEVENLABS_API_KEY` (read-aloud).

## Limitations
Voluntary and biased reports (notoriety bias), no exposure data, a small number of ground-truth events. AutoVigil ranks where humans should look; it does not prove defects and gives no legal or repair advice.

## Data
Public NHTSA Office of Defects Investigation data (complaints, investigations, recalls). No personal information is used.
