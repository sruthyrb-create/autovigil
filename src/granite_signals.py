"""RQ2: does Granite failure-mode coding give earlier / cleaner alarms than NHTSA component codes?
Stream = make x model x Granite failure-mode group (e.g. FALSE_BRAKING). Same as-of weekly PRR / chi2 / IC025
machinery as signals.py; background = all complaints for all vehicles in the same 26-week window.
Fairness: only complaints filed under FCA / LANE DEPARTURE / ADAS (ELECTRICAL) are counted, because those were
coded for every model (SERVICE BRAKES complaints were coded only for the ground-truth models)."""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from backtest import run_start
from ground_truth import load
BASE = os.path.join(os.path.dirname(__file__), ".."); WORK = os.path.join(BASE, "work")
WINDOW_WEEKS = 26
FAIR_GROUPS = {"FORWARD COLLISION AVOIDANCE", "LANE DEPARTURE", "ADAS (ELECTRICAL)"}
MODE_GROUPS = {"FALSE_BRAKING": {"false_braking"},
               "LANE_KEEP": {"lane_keep_wrong_steer", "lane_keep_failed"},
               "SELF_DRIVING": {"self_driving_behavior"},
               "SYSTEM_UNAVAILABLE": {"system_unavailable"}}
EVENT_MODE = {"FORWARD COLLISION AVOIDANCE": "FALSE_BRAKING", "LANE DEPARTURE": "LANE_KEEP"}

def weeks(ld, fd):
    ld = pd.to_datetime(ld, format="%Y%m%d", errors="coerce"); fd = pd.to_datetime(fd, format="%Y%m%d", errors="coerce")
    ev = fd.where(fd.notna() & (fd <= ld) & (fd >= "1995-01-01"), ld)
    return ev.dt.to_period("W-SUN").dt.start_time, ld.dt.to_period("W-SUN").dt.start_time

def prepare():
    c = pd.read_parquet(os.path.join(WORK, "complaints.parquet"), columns=["odino", "make", "model", "faildate", "ldate"])
    c["mm"] = c["make"].fillna("?") + "|" + c["model"].fillna("?")
    c = c.drop_duplicates(["odino", "mm"])
    c["iweek"], c["rweek"] = weeks(c.ldate, c.faildate)
    c = c.dropna(subset=["iweek", "rweek"])
    tot = c.groupby(["mm", "iweek", "rweek"]).size().rename("n").reset_index()      # all complaints (denominator)
    q = pd.read_parquet(os.path.join(WORK, "coding_queue.parquet"), columns=["odino", "grp"])
    q = q[q.grp.isin(FAIR_GROUPS)].drop_duplicates("odino")
    g = pd.read_parquet(os.path.join(WORK, "granite_codes_v2.parquet"), columns=["odino", "failure_mode", "valid"])
    g = g[g.valid.astype(str) == "True"].drop_duplicates("odino")
    g = g.merge(q[["odino"]], on="odino").merge(c[["odino", "mm", "iweek", "rweek"]], on="odino")
    rows = []
    for name, modes in MODE_GROUPS.items():
        s = g[g.failure_mode.isin(modes)]
        rows.append(s.groupby(["mm", "iweek", "rweek"]).size().rename("n").reset_index().assign(grp=name))
    ev = pd.concat(rows, ignore_index=True)
    coded_mm = set(g.mm)
    print(f"coded complaints used: {len(g):,}  models covered: {len(coded_mm):,}")
    return tot, ev

def run(start="2016-01-04", end="2026-09-28"):
    tot, ev = prepare()
    mm_codes = np.unique(np.concatenate([tot.mm.values, ev.mm.values])); M = len(mm_codes)
    gr_codes = np.array(sorted(MODE_GROUPS)); G = len(gr_codes)
    t_mm = np.searchsorted(mm_codes, tot.mm.values); t_iw = tot.iweek.values; t_rw = tot.rweek.values; t_n = tot.n.values.astype(float)
    e_mm = np.searchsorted(mm_codes, ev.mm.values); e_g = np.searchsorted(gr_codes, ev.grp.values)
    e_iw = ev.iweek.values; e_rw = ev.rweek.values; e_n = ev.n.values.astype(float)
    out = []
    for t in pd.date_range(start, end, freq="7D"):
        tt = np.datetime64(t); lo = tt - np.timedelta64(7 * WINDOW_WEEKS, "D")
        mt = (t_rw <= tt) & (t_iw > lo) & (t_iw <= tt)
        me = (e_rw <= tt) & (e_iw > lo) & (e_iw <= tt)
        row = np.bincount(t_mm[mt], weights=t_n[mt], minlength=M); N = row.sum()
        if N == 0 or not me.any(): continue
        key = e_mm[me].astype(np.int64) * G + e_g[me]
        a_all = np.bincount(key, weights=e_n[me], minlength=M * G)
        col = np.bincount(e_g[me], weights=e_n[me], minlength=G)
        k = np.nonzero(a_all >= 3)[0]
        if not len(k): continue
        mi, gi = k // G, k % G
        a = a_all[k]; b = np.maximum(row[mi] - a, 0); cc = col[gi] - a; d = N - a - b - cc
        prr = (a / np.maximum(a + b, 1)) / np.maximum(cc / (cc + d), 1e-12)
        E = row[mi] * col[gi] / N
        chi2 = N * (np.abs(a * d - b * cc) - N / 2) ** 2 / np.maximum((a + b) * (cc + d) * (a + cc) * (b + d), 1e-12)
        ic025 = np.log2((a + 0.5) / (E + 0.5)) - 3.3 * (a + 0.5) ** -0.5 - 2 * (a + 0.5) ** -1.5
        out.append(pd.DataFrame({"week": t, "mm": mm_codes[mi], "grp": gr_codes[gi], "a": a, "mm_total": row[mi],
                                 "expected": E, "prr": prr, "chi2": chi2, "ic025": ic025}))
    res = pd.concat(out, ignore_index=True)
    res["prr_signal"] = (res.prr >= 2) & (res.chi2 >= 4) & (res.a >= 3)
    res["ic_signal"] = res.ic025 > 0
    res.to_parquet(os.path.join(WORK, "signals_granite_weekly.parquet"), index=False)
    return res

def evaluate(sig, base):
    rows = []
    for _, e in load().iterrows():
        if e.group not in EVENT_MODE: continue
        mms = {f"{e.make}|{m}" for m in e.models}
        s = sig[sig.mm.isin(mms) & (sig.grp == EVENT_MODE[e.group]) & (sig.week <= e.odate) & (sig.week >= e.odate - pd.Timedelta(days=5 * 365))]
        r = {"action": e.action, "label": e.label, "open": e.odate.date()}
        b = base[base.action == e.action]
        r["nhtsa_code_lead_wk"] = b.prr_signal_lead_wk.iloc[0] if len(b) else None
        for det in ("prr_signal", "ic_signal"):
            rs = run_start(sorted(set(s.loc[s[det], "week"])), e.odate)
            r[f"granite_{det}_lead_wk"] = round((e.odate - rs).days / 7) if rs is not None else None
        r["granite_max_a"] = int(s.a.max()) if len(s) else 0
        rows.append(r)
    return pd.DataFrame(rows)

def burden(sig, det="prr_signal", grp=None):
    s = sig[sig[det]] if grp is None else sig[sig[det] & (sig.grp == grp)]
    per_year = s.assign(y=s.week.dt.year).groupby("y").mm.nunique()
    return per_year[(per_year.index >= 2017) & (per_year.index <= 2025)].mean()

if __name__ == "__main__":
    sig = run()
    base = pd.read_csv(os.path.join(WORK, "backtest_disproportionality.csv"))
    res = evaluate(sig, base)
    pd.set_option("display.width", 250); print(res.to_string(index=False))
    res.to_csv(os.path.join(WORK, "backtest_granite.csv"), index=False)
    old = pd.read_parquet(os.path.join(WORK, "signals_weekly.parquet"))
    print("alarmed streams/yr  NHTSA FCA code: %.1f   Granite FALSE_BRAKING: %.1f" %
          (burden(old, grp="FORWARD COLLISION AVOIDANCE"), burden(sig, grp="FALSE_BRAKING")))
