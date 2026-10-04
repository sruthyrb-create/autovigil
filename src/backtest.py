"""Lead-time backtest: when would each detector first have fired, relative to NHTSA's investigation open date?"""
import os, numpy as np, pandas as pd
from ground_truth import load
BASE = os.path.join(os.path.dirname(__file__), ".."); WORK = os.path.join(BASE,"work")
GAP_WEEKS = 4        # a run of alarms may have gaps up to this long
RECENT_WEEKS = 8     # run must still be active within 8 weeks of the open date

def run_start(weeks, odate):
    """first week of the alarm run that is still active shortly before odate"""
    w = sorted(x for x in weeks if x <= odate)
    if not w or (odate - w[-1]).days > 7*RECENT_WEEKS: return None
    start = w[-1]
    for prev in reversed(w[:-1]):
        if (start - prev).days <= 7*(GAP_WEEKS+1): start = prev
        else: break
    return start

def evaluate(sig, detectors=("prr_signal","ic_signal")):
    gt = load(); rows = []
    for _, e in gt.iterrows():
        mms = {f"{e.make}|{m}" for m in e.models}
        s = sig[(sig.mm.isin(mms)) & (sig.grp == e.group) & (sig.week <= e.odate) & (sig.week >= e.odate - pd.Timedelta(days=5*365))]
        r = {"action": e.action, "label": e.label, "category": e.category, "open": e.odate.date()}
        for det in detectors:
            wk = sorted(set(s.loc[s[det], "week"]))
            first = wk[0] if wk else None; rs = run_start(wk, e.odate)
            r[f"{det}_first"] = first.date() if first is not None else None
            r[f"{det}_run_start"] = rs.date() if rs is not None else None
            r[f"{det}_lead_wk"] = round((e.odate - rs).days/7) if rs is not None else None
        r["max_a_before_open"] = int(s.a.max()) if len(s) else 0
        rows.append(r)
    return pd.DataFrame(rows)

if __name__ == "__main__":
    sig = pd.read_parquet(os.path.join(WORK,"signals_weekly.parquet"))
    res = evaluate(sig)
    pd.set_option("display.width", 250)
    print(res.to_string(index=False))
    res.to_csv(os.path.join(WORK,"backtest_disproportionality.csv"), index=False)
