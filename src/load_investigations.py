"""Load NHTSA investigations (FLAT_INV.txt) and flag ADAS-related ones opened 2016+."""
import csv, os, re
import pandas as pd
BASE = os.path.join(os.path.dirname(__file__), "..")
COLS = ["action","make","model","year","compname","mfr_name","odate","cdate","campno","subject","summary"]
inv = pd.read_csv(os.path.join(BASE,"data","FLAT_INV","FLAT_INV.txt"), sep="\t", header=None, names=COLS,
                  quoting=csv.QUOTE_NONE, dtype=str, encoding="latin-1", on_bad_lines="skip")
for c in ["make","model","compname","subject","mfr_name"]:
    inv[c] = inv[c].fillna("").str.strip().str.upper()
inv.to_parquet(os.path.join(BASE,"work","investigations_all.parquet"), index=False)
ADAS = re.compile(r"COLLISION AVOIDANCE|AUTOMATIC EMERGENCY BRAK|EMERGENCY BRAKING|\bAEB\b|PHANTOM|UNEXPECTED BRAK|"
                  r"INADVERTENT BRAK|UNINTENDED BRAK|FALSE ACTIVATION|LANE DEPARTURE|LANE KEEP|LANE CENTER|"
                  r"ADAPTIVE CRUISE|AUTOPILOT|FULL SELF|SELF-DRIVING|BLUECRUISE|SUPER CRUISE|DRIVER ASSIST|"
                  r"ADAS|AUTOSTEER|ACTUALLY SMART SUMMON|SMART SUMMON|CRASH IMMINENT|FORWARD COLLISION")
txt = inv["compname"] + " | " + inv["subject"] + " | " + inv["summary"].fillna("").str.upper()
inv["is_adas"] = txt.str.contains(ADAS)
recent = inv[inv["odate"].fillna("") >= "20160101"]
adas = recent[recent["is_adas"]]
# one row per investigation with its make/model/year coverage
g = adas.groupby("action").agg(make=("make", lambda s: sorted(set(s))), model=("model", lambda s: sorted(set(s))),
     years=("year", lambda s: sorted(set(s))), odate=("odate","first"), cdate=("cdate","first"),
     campno=("campno","first"), compname=("compname", lambda s: sorted(set(s))), subject=("subject","first")).reset_index()
g = g.sort_values("odate")
g.to_parquet(os.path.join(BASE,"work","adas_investigations.parquet"), index=False)
print("all rows", len(inv), "investigations", inv.action.nunique(), "| 2016+ ADAS investigations:", len(g))
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 70)
print(g[["action","odate","make","subject"]].to_string(index=False))
