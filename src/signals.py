"""Weekly as-of disproportionality signals (PRR, chi-square, BCPNN IC025) on NHTSA complaints.
Stream = make x model x component group. Counts use a rolling incident-date window and only
complaints already received by the evaluation week (no peeking)."""
import os, sys, time, numpy as np, pandas as pd
BASE = os.path.join(os.path.dirname(__file__), "..")
WORK = os.path.join(BASE, "work")
WINDOW_WEEKS = 26
ADAS_GROUPS = {"FORWARD COLLISION AVOIDANCE","LANE DEPARTURE","BACK OVER PREVENTION","ADAS (ELECTRICAL)","SERVICE BRAKES"}

def comp_group(s: pd.Series) -> pd.Series:
    s = s.fillna("UNKNOWN")
    g = s.str.split(":").str[0].str.strip()
    g = g.where(~s.str.startswith("ELECTRICAL SYSTEM:ADAS"), "ADAS (ELECTRICAL)")
    return g

def prepare():
    c = pd.read_parquet(os.path.join(WORK,"complaints.parquet"), columns=["odino","make","model","compdesc","faildate","ldate"])
    ld = pd.to_datetime(c["ldate"], format="%Y%m%d", errors="coerce")
    fd = pd.to_datetime(c["faildate"], format="%Y%m%d", errors="coerce")
    ev = fd.where((fd.notna()) & (fd <= ld) & (fd >= "1995-01-01"), ld)
    c["grp"] = comp_group(c["compdesc"])
    c["mm"] = c["make"].fillna("?") + "|" + c["model"].fillna("?")
    c["iweek"] = ev.dt.to_period("W-SUN").dt.start_time
    c["rweek"] = ld.dt.to_period("W-SUN").dt.start_time
    c = c.dropna(subset=["iweek","rweek"]).drop_duplicates(["odino","mm","grp"])
    agg = c.groupby(["mm","grp","iweek","rweek"]).size().rename("n").reset_index()
    agg.to_parquet(os.path.join(WORK,"stream_counts.parquet"), index=False)
    return agg

def run(start="2016-01-04", end="2026-09-28"):
    t0 = time.time()
    p = os.path.join(WORK,"stream_counts.parquet")
    agg = pd.read_parquet(p) if os.path.exists(p) else prepare()
    mm_codes, mm_idx = np.unique(agg["mm"].values, return_inverse=True)
    gr_codes, gr_idx = np.unique(agg["grp"].values, return_inverse=True)
    G = len(gr_codes); M = len(mm_codes)
    key = mm_idx.astype(np.int64) * G + gr_idx
    iw = agg["iweek"].values.astype("datetime64[D]"); rw = agg["rweek"].values.astype("datetime64[D]")
    n = agg["n"].values.astype(float)
    keep_grp = np.array([g in ADAS_GROUPS for g in gr_codes])
    out = []
    for t in pd.date_range(start, end, freq="7D"):
        tt = np.datetime64(t.date()); lo = tt - np.timedelta64(7*WINDOW_WEEKS, "D")
        m = (rw <= tt) & (iw > lo) & (iw <= tt)
        a_all = np.bincount(key[m], weights=n[m], minlength=M*G)
        N = a_all.sum()
        if N == 0: continue
        row = np.bincount(mm_idx[m], weights=n[m], minlength=M)
        col = np.bincount(gr_idx[m], weights=n[m], minlength=G)
        k = np.nonzero(a_all >= 3)[0]
        mi, gi = k // G, k % G
        sel = keep_grp[gi]; k, mi, gi = k[sel], mi[sel], gi[sel]
        a = a_all[k]; b = row[mi] - a; cc = col[gi] - a; d = N - a - b - cc
        prr = (a/(a+b)) / np.maximum(cc/(cc+d), 1e-12)
        E = row[mi]*col[gi]/N
        chi2 = N*(np.abs(a*d - b*cc) - N/2)**2 / np.maximum((a+b)*(cc+d)*(a+cc)*(b+d), 1e-12)
        ic = np.log2((a+0.5)/(E+0.5)); ic025 = ic - 3.3*(a+0.5)**-0.5 - 2*(a+0.5)**-1.5
        out.append(pd.DataFrame({"week": t, "mm": mm_codes[mi], "grp": gr_codes[gi], "a": a, "mm_total": row[mi],
                                 "expected": E, "prr": prr, "chi2": chi2, "ic025": ic025}))
    res = pd.concat(out, ignore_index=True)
    res["prr_signal"] = (res.prr >= 2) & (res.chi2 >= 4) & (res.a >= 3)
    res["ic_signal"] = res.ic025 > 0
    res.to_parquet(os.path.join(WORK,"signals_weekly.parquet"), index=False)
    print(f"weeks {res.week.nunique()} rows {len(res):,} in {time.time()-t0:.0f}s")
    return res

if __name__ == "__main__":
    if "--prepare" in sys.argv: prepare(); print("prepared")
    else: run()
