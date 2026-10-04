"""Package the small data files the API needs into api_data/ (committed to git, used by the Code Engine container)."""
import os, pandas as pd
BASE = os.path.join(os.path.dirname(__file__), ".."); WORK = os.path.join(BASE, "work"); OUT = os.path.join(BASE, "api_data")
os.makedirs(OUT, exist_ok=True)
q = pd.read_parquet(os.path.join(WORK, "coding_queue.parquet")).drop_duplicates("odino")
g = pd.read_parquet(os.path.join(WORK, "granite_codes_v2.parquet")).drop_duplicates("odino")
c = pd.read_parquet(os.path.join(WORK, "complaints.parquet"), columns=["odino", "faildate", "crash", "injured", "deaths"]).drop_duplicates("odino")
d = q.merge(g, on="odino", how="left").merge(c, on="odino", how="left")
d["failure_mode"] = d.failure_mode.where(d.valid.astype(str) == "True", None)
d["snippet"] = d.cdescr.fillna("").str.encode("latin-1", "ignore").str.decode("utf-8", "ignore").str.slice(0, 400)
cols = ["odino", "make", "model", "year", "grp", "ldate", "faildate", "crash", "injured", "deaths", "failure_mode",
        "speed_mph", "feature_engaged", "software_update_mentioned", "snippet"]
d[cols].astype(str).to_parquet(os.path.join(OUT, "complaints.parquet"), index=False)
a = pd.read_parquet(os.path.join(WORK, "signals_weekly.parquet")).assign(source="nhtsa_code")
b = pd.read_parquet(os.path.join(WORK, "signals_granite_weekly.parquet")).assign(source="granite")
s = pd.concat([a, b], ignore_index=True)
s = s[s.week >= "2016-01-01"]
s.to_parquet(os.path.join(OUT, "signals.parquet"), index=False)
for f in ["ground_truth.csv", "backtest_disproportionality.csv", "backtest_granite.csv"]:
    p = os.path.join(WORK, f)
    if os.path.exists(p): pd.read_csv(p).to_csv(os.path.join(OUT, f), index=False)
print("complaints", len(d), "signals", len(s))
for f in os.listdir(OUT): print(f, round(os.path.getsize(os.path.join(OUT, f)) / 1e6, 2), "MB")
