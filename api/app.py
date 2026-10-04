"""AutoVigil API - tools for the watsonx Orchestrate agents (Driver intake + Analyst) and the dashboard.
Run locally:  uvicorn api.app:app --reload     OpenAPI spec: /openapi.json"""
import os, re
from datetime import date
from typing import Optional, List
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

DATA = os.environ.get("AUTOVIGIL_DATA", os.path.join(os.path.dirname(__file__), "..", "api_data"))
C = pd.read_parquet(os.path.join(DATA, "complaints.parquet"))
C["ldate_dt"] = pd.to_datetime(C.ldate, format="%Y%m%d", errors="coerce")
S = pd.read_parquet(os.path.join(DATA, "signals.parquet"))
LATEST = S.week.max()
def _csv(name):
    p = os.path.join(DATA, name); return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()
GT, BT_N, BT_G = _csv("ground_truth.csv"), _csv("backtest_disproportionality.csv"), _csv("backtest_granite.csv")

MODES = ["false_braking", "failed_to_brake", "false_warning", "lane_keep_wrong_steer", "lane_keep_failed",
         "acc_speed_fault", "self_driving_behavior", "system_unavailable", "conventional_brake_fault", "other"]
MODE_TEXT = {"false_braking": "car braked hard by itself with nothing ahead (phantom braking)",
             "failed_to_brake": "automatic braking did not stop for a real obstacle",
             "false_warning": "collision or lane warning with no real hazard",
             "lane_keep_wrong_steer": "lane-keeping steered the car the wrong way",
             "lane_keep_failed": "lane-keeping failed to keep the car in lane",
             "acc_speed_fault": "adaptive cruise set or held the wrong speed",
             "self_driving_behavior": "Autopilot/FSD-type system made an unsafe driving decision",
             "system_unavailable": "driver-assist system disabled or unavailable",
             "conventional_brake_fault": "ordinary brake hardware problem (pads, ABS, parking brake)",
             "other": "other problem"}
STREAM_TEXT = {"FALSE_BRAKING": "phantom braking (Granite-coded)", "LANE_KEEP": "lane-keeping faults (Granite-coded)",
               "SELF_DRIVING": "self-driving behaviour (Granite-coded)", "SYSTEM_UNAVAILABLE": "assist unavailable (Granite-coded)",
               "FORWARD COLLISION AVOIDANCE": "forward collision avoidance (NHTSA code)", "LANE DEPARTURE": "lane departure (NHTSA code)",
               "ADAS (ELECTRICAL)": "ADAS electrical (NHTSA code)", "SERVICE BRAKES": "service brakes (NHTSA code)",
               "BACK OVER PREVENTION": "back-over prevention (NHTSA code)"}

app = FastAPI(title="AutoVigil API", version="1.0",
              description="Early warning of driver-assist (ADAS) defects from public NHTSA complaints. "
                          "Signals use pharmacovigilance disproportionality (PRR, BCPNN IC025) on weekly as-of data; "
                          "complaints coded by IBM Granite 4. Signals are statistical hypotheses, not proof of a defect.",
              servers=[{"url": os.environ.get("PUBLIC_URL", "http://localhost:8000")}])

import difflib
KNOWN = sorted(set((C.make.str.upper() + "|" + C.model.str.upper()).tolist()))
MAKES = sorted({k.split("|")[0] for k in KNOWN})

def _resolve(make, model):
    """Fix typos in make/model (e.g. TUCHEON -> TUCSON) using the models present in the data."""
    mk = make.strip().upper(); md = model.strip().upper().replace("-", " ")
    if mk not in MAKES:
        c = difflib.get_close_matches(mk, MAKES, n=1, cutoff=0.6); mk = c[0] if c else mk
    models = [k.split("|")[1] for k in KNOWN if k.startswith(mk + "|")]
    norm = {m.replace("-", " "): m for m in models}
    if not any(md in m for m in norm):
        c = difflib.get_close_matches(md, list(norm), n=1, cutoff=0.6)
        if c: md = c[0]
    return mk, md

def _mm_mask(df, make, model):
    m = df.mm.str.upper() if "mm" in df else (df.make.str.upper() + "|" + df.model.str.upper())
    mk, md = _resolve(make, model)
    return m.str.startswith(mk + "|") & m.str.split("|").str[1].str.replace("-", " ").str.contains(re.escape(md), regex=True)

def _as_of(as_of):
    return pd.Timestamp(as_of) if as_of else LATEST

def _week_rows(as_of, source=None):
    wk = S.week[S.week <= as_of].max(); s = S[S.week == wk]
    return (s if source is None else s[s.source == source]), wk

def _run_start(mm, grp, source, wk, gap=5):
    h = S[(S.mm == mm) & (S.grp == grp) & (S.source == source) & S.prr_signal & (S.week <= wk)].week.sort_values()
    start = wk
    for w in reversed(h.tolist()):
        if (start - w).days <= 7 * gap: start = w
        else: break
    return start

@app.get("/vehicle_status", operation_id="get_vehicle_status",
         summary="Is there an active early-warning alarm for this car model? Use when a driver names their car.")
def vehicle_status(make: str = Query(..., description="Vehicle make, e.g. TESLA, HONDA, NISSAN"),
                   model: str = Query(..., description="Vehicle model, e.g. MODEL Y, CR-V, ROGUE"),
                   as_of: Optional[date] = Query(None, description="Replay date (YYYY-MM-DD). Omit for the latest data.")):
    t = _as_of(as_of); s, wk = _week_rows(t)
    s = s[_mm_mask(s, make, model)]
    alarms = []
    for r in s[s.prr_signal].sort_values("ic025", ascending=False).itertuples():
        alarms.append({"model_variant": r.mm.split("|")[1], "stream": STREAM_TEXT.get(r.grp, r.grp), "source": r.source, "reports_last_26_weeks": int(r.a),
                       "expected_if_typical": round(float(r.expected), 1), "prr": round(float(r.prr), 1),
                       "alarm_since": str(_run_start(r.mm, r.grp, r.source, wk).date())})
    c = C[_mm_mask(C, make, model) & (C.ldate_dt <= t) & (C.ldate_dt > t - pd.Timedelta(weeks=26))]
    counts = c.failure_mode.value_counts().to_dict()
    mk, md = _resolve(make, model)
    return {"make": mk, "model": md, "as_of_week": str(wk.date()), "alarm_active": bool(alarms),
            "alarms": alarms, "assist_related_reports_last_26_weeks": int(len(c)),
            "reports_by_failure_mode": {k: int(v) for k, v in counts.items() if k in MODES},
            "what_to_do": ["Check open recalls and software updates for your VIN at nhtsa.gov/recalls.",
                           "If the problem is phantom braking or steering, read the owner's manual section on how to adjust or switch off that assist feature, and tell your dealer.",
                           "File a detailed NHTSA complaint (speed, feature engaged, conditions, software version) - AutoVigil can draft it."],
            "disclaimer": "Statistical signal from voluntary public reports; not proof of a defect and not repair or legal advice."}

@app.get("/similar_reports", operation_id="get_similar_reports",
         summary="Count and sample public complaints like the driver's experience, for the same car model.")
def similar_reports(make: str, model: str,
                    failure_mode: Optional[str] = Query(None, description="One of: " + ", ".join(MODES)),
                    limit: int = Query(3, ge=1, le=10)):
    c = C[_mm_mask(C, make, model)]
    if failure_mode:
        if failure_mode not in MODES: raise HTTPException(400, f"failure_mode must be one of {MODES}")
        c = c[c.failure_mode == failure_mode]
    c = c.sort_values("ldate", ascending=False)
    mk, md = _resolve(make, model)
    return {"make": mk, "model": md, "failure_mode": failure_mode, "count": int(len(c)),
            "crashes": int((c.crash == "Y").sum()), "examples": [
                {"complaint_id": r.odino, "received": r.ldate, "model_year": r.year, "failure_mode": r.failure_mode,
                 "excerpt": r.snippet[:300]} for r in c.head(limit).itertuples()]}

class Report(BaseModel):
    make: str; model: str
    model_year: Optional[int] = None
    incident_date: Optional[date] = None
    what_happened: str = Field(..., description="The driver's own description of the event")
    speed_mph: Optional[float] = None
    feature_engaged: Optional[str] = Field(None, description="e.g. adaptive cruise, Autopilot, FSD, lane keep, none, unknown")
    obstacle_present: Optional[bool] = Field(None, description="Was there a real obstacle ahead?")
    road_and_weather: Optional[str] = None
    warning_messages: Optional[str] = None
    recent_software_update: Optional[bool] = None
    software_version: Optional[str] = None
    crash: Optional[bool] = None
    injuries: Optional[bool] = None
    times_happened: Optional[int] = None
    dealer_visited: Optional[bool] = None

KEY_FIELDS = ["model_year", "incident_date", "speed_mph", "feature_engaged", "obstacle_present", "road_and_weather",
              "warning_messages", "recent_software_update", "crash", "injuries", "times_happened", "dealer_visited"]

def _guess_mode(text, feature, obstacle):
    t = text.lower()
    if re.search(r"brak|slow|stop", t) and (obstacle is False or re.search(r"phantom|no (car|reason|obstacle)|nothing", t)): return "false_braking"
    if re.search(r"lane|steer|swerv|drift", t): return "lane_keep_wrong_steer"
    if re.search(r"warning|alert|beep", t): return "false_warning"
    if re.search(r"cruise|speed", t): return "acc_speed_fault"
    return "other"

@app.post("/draft_complaint", operation_id="draft_complaint",
          summary="Turn the driver's answers into a structured NHTSA-style complaint and list what is still missing.")
def draft_complaint(r: Report):
    missing = [f for f in KEY_FIELDS if getattr(r, f) is None]
    mode = _guess_mode(r.what_happened, r.feature_engaged, r.obstacle_present)
    yn = lambda v: "unknown" if v is None else ("yes" if v else "no")
    text = (f"{r.model_year or ''} {r.make.upper()} {r.model.upper()}. On {r.incident_date or 'an unspecified date'}, "
            f"while driving at {r.speed_mph if r.speed_mph is not None else 'an unknown speed'} mph with "
            f"{r.feature_engaged or 'unknown driver-assist status'} engaged, {r.what_happened.strip().rstrip('.')}. "
            f"Obstacle ahead: {yn(r.obstacle_present)}. Conditions: {r.road_and_weather or 'not stated'}. "
            f"Warnings shown: {r.warning_messages or 'not stated'}. Recent software update: {yn(r.recent_software_update)}"
            f"{' (version ' + r.software_version + ')' if r.software_version else ''}. "
            f"Times it happened: {r.times_happened or 'not stated'}. Crash: {yn(r.crash)}. Injuries: {yn(r.injuries)}. "
            f"Dealer visited: {yn(r.dealer_visited)}.")
    sim = similar_reports(r.make, r.model, mode, 1)
    return {"draft_text": " ".join(text.split()), "likely_failure_mode": mode, "failure_mode_meaning": MODE_TEXT[mode],
            "completeness": round(1 - len(missing) / len(KEY_FIELDS), 2), "missing_fields": missing,
            "similar_reports_count": sim["count"], "submit_at": "https://www.nhtsa.gov/report-a-safety-problem"}

@app.get("/alarms", operation_id="get_ranked_alarms",
         summary="Analyst view: currently active ADAS alarms, ranked by signal strength.")
def alarms(as_of: Optional[date] = Query(None, description="Replay date YYYY-MM-DD; omit for latest"),
           source: str = Query("granite", description="granite (Granite-coded failure modes) or nhtsa_code"),
           limit: int = Query(10, ge=1, le=50)):
    s, wk = _week_rows(_as_of(as_of), source)
    s = s[s.prr_signal].sort_values("ic025", ascending=False).head(limit)
    return {"as_of_week": str(wk.date()), "source": source, "n_active": int(len(s)), "alarms": [
        {"make": r.mm.split("|")[0], "model": r.mm.split("|")[1], "stream": STREAM_TEXT.get(r.grp, r.grp),
         "reports_last_26_weeks": int(r.a), "expected": round(float(r.expected), 1), "prr": round(float(r.prr), 1),
         "ic025": round(float(r.ic025), 2), "alarm_since": str(_run_start(r.mm, r.grp, source, wk).date())} for r in s.itertuples()]}

@app.get("/alarm_detail", operation_id="get_alarm_detail",
         summary="Evidence for one alarm: weekly trend, statistics and example complaints, for drafting an analyst memo.")
def alarm_detail(make: str, model: str, stream: str = Query("FALSE_BRAKING", description="FALSE_BRAKING, LANE_KEEP, SELF_DRIVING, SYSTEM_UNAVAILABLE or an NHTSA component group"),
                 as_of: Optional[date] = None):
    t = _as_of(as_of); src = "granite" if stream in ("FALSE_BRAKING", "LANE_KEEP", "SELF_DRIVING", "SYSTEM_UNAVAILABLE") else "nhtsa_code"
    h = S[_mm_mask(S, make, model) & (S.grp == stream) & (S.source == src) & (S.week <= t) & (S.week > t - pd.Timedelta(weeks=52))]
    h = h.groupby("week").agg(a=("a", "sum"), expected=("expected", "sum"), prr=("prr", "max"), signal=("prr_signal", "max")).reset_index()
    mode = {"FALSE_BRAKING": "false_braking", "LANE_KEEP": "lane_keep_wrong_steer", "SELF_DRIVING": "self_driving_behavior", "SYSTEM_UNAVAILABLE": "system_unavailable"}.get(stream)
    c = C[_mm_mask(C, make, model) & (C.ldate_dt <= t)]
    if mode: c = c[c.failure_mode == mode]
    recent = c[c.ldate_dt > t - pd.Timedelta(weeks=26)]
    sw = recent.software_update_mentioned.astype(str).str.lower().eq("true").mean() if len(recent) else 0
    sp = pd.to_numeric(recent.speed_mph, errors="coerce")
    return {"make": make.upper(), "model": model.upper(), "stream": STREAM_TEXT.get(stream, stream), "as_of": str(t.date()),
            "weekly": [{"week": str(r.week.date()), "reports_26wk": int(r.a), "expected": round(float(r.expected), 1),
                        "prr": round(float(r.prr), 1), "alarm": bool(r.signal)} for r in h.itertuples()],
            "recent_reports": int(len(recent)), "crashes": int((recent.crash == "Y").sum()),
            "injuries": int(pd.to_numeric(recent.injured, errors="coerce").fillna(0).sum()),
            "share_mentioning_software_update": round(float(sw), 2),
            "median_speed_mph": None if sp.dropna().empty else float(sp.median()),
            "top_features_engaged": recent.feature_engaged.value_counts().head(3).to_dict(),
            "examples": [{"complaint_id": r.odino, "received": r.ldate, "excerpt": r.snippet[:300]} for r in recent.sort_values("ldate", ascending=False).head(4).itertuples()],
            "memo_guidance": "Write a 1-page memo: summary, evidence (counts vs expected, trend, crashes/injuries), example narratives, "
                             "possible software link, recommended action (monitor / request information / open review). State it is a statistical signal."}

@app.get("/backtest", operation_id="get_backtest_results",
         summary="Research results: how many weeks before NHTSA opened each investigation AutoVigil would have alarmed.")
def backtest():
    return {"nhtsa_code_detector": BT_N.fillna("").to_dict("records"), "granite_detector": BT_G.fillna("").to_dict("records"),
            "method": "Weekly as-of replay 2016-2026, 26-week incident window, PRR>=2 & chi2>=4 & n>=3. Lead = open date - start of alarm run active within 8 weeks of opening."}

@app.get("/health", include_in_schema=False)
def health(): return {"ok": True, "latest_week": str(LATEST.date()), "complaints": len(C)}
