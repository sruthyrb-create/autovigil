"""How many make-model streams raise alarms per year (false-alarm burden), at several thresholds,
and the lead time we keep at each threshold. Restricted to complaint-driven ADAS groups."""
import os, pandas as pd, numpy as np
from ground_truth import load
from backtest import run_start
WORK = os.path.join(os.path.dirname(__file__), "..", "work")
GROUPS = {"FORWARD COLLISION AVOIDANCE", "LANE DEPARTURE"}
sig = pd.read_parquet(os.path.join(WORK, "signals_weekly.parquet"))
sig = sig[sig.grp.isin(GROUPS)]
gt = load(); gt = gt[gt.category == "complaint"]
truth = {(f"{r.make}|{m}", r.group): r for _, r in gt.iterrows() for m in r.models}
rows = []
for min_a, min_prr in [(3, 2), (5, 2), (10, 2), (5, 3), (10, 3), (20, 3), (10, 5)]:
    on = sig[(sig.a >= min_a) & (sig.prr >= min_prr) & (sig.chi2 >= 4)]
    yr = on.assign(year=on.week.dt.year).groupby("year").apply(lambda d: d[["mm", "grp"]].drop_duplicates().shape[0])
    streams = on[["mm", "grp"]].drop_duplicates()
    hit = sum((r.mm, r.grp) in truth for r in streams.itertuples())
    leads, caught = [], 0
    for _, e in gt.iterrows():
        mms = {f"{e.make}|{m}" for m in e.models}
        wk = sorted(set(on[(on.mm.isin(mms)) & (on.grp == e.group)].week))
        rs = run_start(wk, e.odate)
        if rs is not None: caught += 1; leads.append((e.odate - rs).days / 7)
    rows.append({"min_reports": min_a, "min_PRR": min_prr, "probes_caught": f"{caught}/{len(gt)}",
                 "median_lead_wk": float(np.median(leads)) if leads else None,
                 "streams_alarmed_2016_26": len(streams), "of_which_probed": hit,
                 "avg_streams_alarmed_per_year": round(yr[(yr.index >= 2016) & (yr.index <= 2025)].mean(), 1)})
res = pd.DataFrame(rows); print(res.to_string(index=False))
res.to_csv(os.path.join(WORK, "alarm_burden.csv"), index=False)
