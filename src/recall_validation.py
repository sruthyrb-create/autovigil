"""Second, independent validation: do Granite phantom-braking alarms come BEFORE matching recalls?
Recall 'matches' if same make, model name contained, ADAS topic, defect text about unexpected/false braking."""
import os, re, sys, pandas as pd, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from backtest import run_start
B = os.path.join(os.path.dirname(__file__), ".."); W = os.path.join(B, "work")
s = pd.read_parquet(os.path.join(W, "signals_granite_weekly.parquet"))
s = s[(s.grp == "FALSE_BRAKING") & s.prr_signal]
first = s.groupby("mm").week.min().rename("alarm_start").reset_index()
r = pd.read_parquet(os.path.join(B, "api_data", "recalls.parquet"))
FB = re.compile(r"unexpected(ly)?\s+(apply|activate|brak)|prematurely|false|unintended(ly)? (brak|activat)|without (an )?obstacle|inadvertent(ly)? (brak|activat)|phantom", re.I)
r = r[(r.topic == "adas") & r.defect.str.contains(FB)]
r["rc"] = pd.to_datetime(r.rcdate, format="%Y%m%d")
rows = []
for x in first.itertuples():
    mk, md = x.mm.split("|")
    m = r[(r.make == mk) & r.model.apply(lambda v: v == md or md.startswith(v) or v.startswith(md))]
    wk = sorted(s[s.mm == x.mm].week)
    hit = None
    for rc in m.sort_values("rc").itertuples():
        rs = run_start(wk, rc.rc)          # alarm run still active within 8 weeks of the recall
        if rs is not None: hit = (rc, rs); break
    rows.append({"make": mk, "model": md, "first_alarm": x.alarm_start.date(),
                 "recall": hit[0].campno if hit else "", "recall_date": hit[0].rc.date() if hit else "",
                 "alarm_run_start": hit[1].date() if hit else "", "lead_wk": round((hit[0].rc - hit[1]).days / 7) if hit else None})
d = pd.DataFrame(rows).sort_values("lead_wk", ascending=False)
hit = d[d.lead_wk.notna()]
print(f"phantom-braking alarmed models: {len(d)}; later followed by a matching false-braking recall: {len(hit)}; median lead {hit.lead_wk.median()} wk")
print(hit.to_string(index=False))
d.to_csv(os.path.join(W, "recall_validation.csv"), index=False); d.to_csv(os.path.join(B, "api_data", "recall_validation.csv"), index=False)
# all false-braking recalls since 2017 on models we cover: how many had an alarm first?
rr = r[r.rc >= "2017-01-01"]; caught = set(hit.recall)
print(f"false-braking recall campaigns 2017+: {rr.campno.nunique()}, preceded by an active AutoVigil alarm: {len(caught)}")
print(rr.drop_duplicates("campno")[["campno","make","rcdate"]].assign(caught=lambda t: t.campno.isin(caught)).to_string(index=False))
