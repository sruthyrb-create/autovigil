"""RQ5: IBM Granite TinyTimeMixer (granite-ttm-512-96-r2 on watsonx.ai) as a surge detector, compared with PRR.
Every 14 days (as-of, no peeking) TTM forecasts the next 28 days of each stream from the previous 512 days.
Alarm when the observed 28-day count is >= 3 and more than 2x the TTM forecast.
Run on the laptop (needs .env):   python src\\ttm_detector.py --pilot     then     python src\\ttm_detector.py"""
import os, sys, json, time, argparse, numpy as np, pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
sys.path.insert(0, os.path.dirname(__file__))
from backtest import run_start
BASE = os.path.join(os.path.dirname(__file__), ".."); W = os.path.join(BASE, "work")
load_dotenv(os.path.join(BASE, ".env"))
MODEL = os.environ.get("TTM_MODEL", "ibm/granite-ttm-512-96-r2")
CTX, H, STEP = 512, 28, 14
OUT = os.path.join(W, "ttm_raw.parquet")

def client():
    from ibm_watsonx_ai import Credentials
    from ibm_watsonx_ai.foundation_models import TSModelInference
    return TSModelInference(model_id=MODEL, credentials=Credentials(url=os.environ["WATSONX_URL"], api_key=os.environ["WATSONX_APIKEY"]),
                            project_id=os.environ["WATSONX_PROJECT_ID"])

def params():
    from ibm_watsonx_ai.foundation_models.schema import TSForecastParameters
    kw = dict(id_columns=["id"], timestamp_column="date", freq="D", target_columns=["y7"])
    try: return TSForecastParameters(**kw, prediction_length=H)
    except TypeError: return TSForecastParameters(**kw)

def to_df(r):
    res = r.get("results", r) if isinstance(r, dict) else r
    if isinstance(res, list) and res and isinstance(res[0], dict) and isinstance(next(iter(res[0].values())), list):
        return pd.concat([pd.DataFrame(x) for x in res], ignore_index=True)
    return pd.DataFrame(res)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--pilot", action="store_true"); a = ap.parse_args()
    s = pd.read_parquet(os.path.join(W, "ttm_series.parquet")); meta = pd.read_csv(os.path.join(W, "ttm_meta.csv"))
    s["y7"] = s.groupby("id").y.transform(lambda v: v.rolling(7, min_periods=1).sum())
    piv = s.pivot(index="date", columns="id", values="y7"); raw = s.pivot(index="date", columns="id", values="y")
    meta["open"] = pd.to_datetime(meta["open"], errors="coerce")
    dates = pd.date_range("2016-06-01", "2026-09-01", freq=f"{STEP}D")
    jobs = []
    for t in dates:
        ids = [r.id for r in meta.itertuples() if (r.kind == "control" and t.year >= 2017) or
               (r.kind == "event" and r.open - pd.Timedelta(days=3 * 365) <= t <= r.open)]
        if ids: jobs.append((t, ids))
    done = pd.read_parquet(OUT) if os.path.exists(OUT) else pd.DataFrame(columns=["t"])
    jobs = [j for j in jobs if str(j[0].date()) not in set(done.t.astype(str))]
    if a.pilot: jobs = jobs[:1]
    print(f"{len(jobs)} forecast calls with {MODEL}")
    m, p = client(), params()
    def run(t, ids):
        end = t - pd.Timedelta(days=H); ctx = piv.loc[end - pd.Timedelta(days=CTX - 1): end, ids]
        df = ctx.reset_index().melt(id_vars="date", var_name="id", value_name="y7")
        df["date"] = df.date.dt.strftime("%Y-%m-%dT%H:%M:%S")
        for k in range(3):
            try:
                r = m.forecast(data=df, params=p)
                if a.pilot: print("raw response keys:", list(r.keys()) if isinstance(r, dict) else type(r)); print(json.dumps(r)[:600])
                f = to_df(r); f["date"] = pd.to_datetime(f["date"]).dt.tz_localize(None)
                f = f[f.date <= end + pd.Timedelta(days=H)]
                fc = f.groupby("id").y7.mean()
                obs_win = slice(end + pd.Timedelta(days=1), t)
                return pd.DataFrame({"t": str(t.date()), "id": ids, "forecast_y7": fc.reindex(ids).values,
                                     "observed_y7": piv.loc[obs_win, ids].mean().values, "observed_n": raw.loc[obs_win, ids].sum().values})
            except Exception as e:
                err = e; time.sleep(2 * (k + 1))
        print("  failed", t.date(), type(err).__name__, str(err)[:200]); return None
    out, t0 = [], time.time()
    with ThreadPoolExecutor(4) as ex:
        futs = [ex.submit(run, t, ids) for t, ids in jobs]
        for i, f in enumerate(as_completed(futs), 1):
            r = f.result()
            if r is not None: out.append(r)
            if out and (i % 20 == 0 or i == len(futs)):
                pd.concat([done] + out, ignore_index=True).to_parquet(OUT, index=False); print(f"  {i}/{len(futs)}  {time.time()-t0:.0f}s")
    if a.pilot: print(pd.concat(out).head(12).to_string() if out else "no output"); return
    evaluate()

def evaluate():
    r = pd.read_parquet(OUT); meta = pd.read_csv(os.path.join(W, "ttm_meta.csv")); r["t"] = pd.to_datetime(r.t)
    r["alarm"] = (r.observed_n >= 3) & (r.observed_y7 > 2 * np.maximum(r.forecast_y7.astype(float), 0.25))
    rows = []
    for e in meta[meta.kind == "event"].itertuples():
        od = pd.Timestamp(e.open); wk = sorted(r[(r.id == e.id) & r.alarm].t)
        rs = run_start(wk, od)
        rows.append({"id": e.id, "open": e.open, "ttm_lead_wk": round((od - rs).days / 7) if rs is not None else None})
    res = pd.DataFrame(rows); print(res.to_string(index=False))
    ctrl = r[r.id.str.startswith("CTRL")]
    per = ctrl.assign(y=ctrl.t.dt.year).groupby(["id", "y"]).alarm.max().groupby("y").mean()
    print(f"control streams alarmed per year (share of 20 non-investigated phantom-braking streams): {per.mean():.2f}")
    res.to_csv(os.path.join(W, "backtest_ttm.csv"), index=False)

if __name__ == "__main__":
    if "--evaluate" in sys.argv: evaluate()
    else: main()
