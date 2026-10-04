"""RQ2 trade-off: same thresholds as alarm_burden.py, NHTSA component codes vs Granite failure-mode streams."""
import os, pandas as pd, numpy as np
from ground_truth import load
from backtest import run_start
WORK = os.path.join(os.path.dirname(__file__), "..", "work")
gt = load(); gt = gt[gt.category == "complaint"]
SRC = {"nhtsa_code": (pd.read_parquet(os.path.join(WORK, "signals_weekly.parquet")),
                      {"FORWARD COLLISION AVOIDANCE": "FORWARD COLLISION AVOIDANCE", "LANE DEPARTURE": "LANE DEPARTURE"}),
       "granite": (pd.read_parquet(os.path.join(WORK, "signals_granite_weekly.parquet")),
                   {"FORWARD COLLISION AVOIDANCE": "FALSE_BRAKING", "LANE DEPARTURE": "LANE_KEEP"})}
rows = []
for src, (sig, gmap) in SRC.items():
    sig = sig[sig.grp.isin(set(gmap.values()))]
    truth = {(f"{r.make}|{m}", gmap[r.group]) for _, r in gt.iterrows() for m in r.models}
    for min_a, min_prr in [(3, 2), (5, 2), (10, 2), (5, 3), (10, 3)]:
        on = sig[(sig.a >= min_a) & (sig.prr >= min_prr) & (sig.chi2 >= 4)]
        yr = on.assign(year=on.week.dt.year).groupby("year").apply(lambda d: d[["mm", "grp"]].drop_duplicates().shape[0])
        streams = on[["mm", "grp"]].drop_duplicates()
        leads = []
        for _, e in gt.iterrows():
            wk = sorted(set(on[on.mm.isin({f"{e.make}|{m}" for m in e.models}) & (on.grp == gmap[e.group])].week))
            rs = run_start(wk, e.odate)
            if rs is not None: leads.append((e.odate - rs).days / 7)
        rows.append({"source": src, "min_reports": min_a, "min_PRR": min_prr, "caught": f"{len(leads)}/{len(gt)}",
                     "median_lead_wk": round(float(np.median(leads)), 1) if leads else None,
                     "streams_alarmed": len(streams), "of_which_probed": sum((r.mm, r.grp) in truth for r in streams.itertuples()),
                     "alarms_per_year": round(yr[(yr.index >= 2016) & (yr.index <= 2025)].mean(), 1)})
res = pd.DataFrame(rows); print(res.to_string(index=False))
res.to_csv(os.path.join(WORK, "alarm_burden_rq2.csv"), index=False)
