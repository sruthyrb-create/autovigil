"""RQ5 prep: daily new-complaint counts (by NHTSA received date) for each ground-truth stream + control streams,
for the IBM Granite TinyTimeMixer (TTM) surge detector. Output: work/ttm_series.parquet (id, date, y) + work/ttm_meta.csv"""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from ground_truth import load
from signals import comp_group
W = os.path.join(os.path.dirname(__file__), "..", "work")
FAIR = {"FORWARD COLLISION AVOIDANCE", "LANE DEPARTURE", "ADAS (ELECTRICAL)"}
MODE = {"FORWARD COLLISION AVOIDANCE": {"false_braking"}, "LANE DEPARTURE": {"lane_keep_wrong_steer", "lane_keep_failed"}}
c = pd.read_parquet(os.path.join(W, "complaints.parquet"), columns=["odino", "make", "model", "compdesc", "ldate"])
c["grp"] = comp_group(c.compdesc); c["mm"] = c.make.fillna("?") + "|" + c.model.fillna("?")
c["date"] = pd.to_datetime(c.ldate, format="%Y%m%d", errors="coerce"); c = c.dropna(subset=["date"])
q = pd.read_parquet(os.path.join(W, "coding_queue.parquet"), columns=["odino", "grp"])
g = pd.read_parquet(os.path.join(W, "granite_codes_v2.parquet"), columns=["odino", "failure_mode", "valid"])
g = g[g.valid.astype(str) == "True"].merge(q[q.grp.isin(FAIR)].drop_duplicates("odino")[["odino"]], on="odino")
cg = c.drop_duplicates(["odino", "mm"]).merge(g, on="odino")
days = pd.date_range("2014-01-01", "2026-09-30", freq="D")
rows, meta = [], []
def add(sid, dates, kind, action, odate):
    s = pd.Series(1, index=dates).groupby(level=0).sum().reindex(days, fill_value=0)
    rows.append(pd.DataFrame({"id": sid, "date": days, "y": s.values.astype(float)}))
    meta.append({"id": sid, "kind": kind, "action": action, "open": odate, "total": int(s.sum())})
gt = load(); gt = gt[gt.category == "complaint"]
for _, e in gt.iterrows():
    mms = {f"{e.make}|{m}" for m in e.models}
    d1 = c[c.mm.isin(mms) & (c.grp == e.group)].drop_duplicates("odino").date
    add(f"{e.action}|nhtsa_code", d1, "event", e.action, e.odate.date())
    d2 = cg[cg.mm.isin(mms) & cg.failure_mode.isin(MODE[e.group])].drop_duplicates("odino").date
    add(f"{e.action}|granite", d2, "event", e.action, e.odate.date())
# controls: Granite phantom-braking streams of other models with >= 20 reports, never in ground truth
gt_mm = {f"{e.make}|{m}" for _, e in load().iterrows() for m in e.models}
fb = cg[cg.failure_mode == "false_braking"].drop_duplicates("odino")
cnt = fb[~fb.mm.isin(gt_mm)].mm.value_counts()
for mm in cnt[cnt >= 20].sample(min(20, (cnt >= 20).sum()), random_state=7).index:
    add(f"CTRL|{mm}|granite", fb[fb.mm == mm].date, "control", "", "")
pd.concat(rows).to_parquet(os.path.join(W, "ttm_series.parquet"), index=False)
m = pd.DataFrame(meta); m.to_csv(os.path.join(W, "ttm_meta.csv"), index=False); print(m.to_string())
