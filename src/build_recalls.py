"""Recalls (NHTSA FLAT_RCL_POST_2010) relevant to driver-assist / braking, for the driver + analyst apps."""
import os, csv, re, pandas as pd
BASE = os.path.join(os.path.dirname(__file__), "..")
cols = {0: "rid", 1: "campno", 2: "make", 3: "model", 4: "year", 6: "compname", 10: "rcltype", 11: "potaff", 15: "rcdate", 19: "defect", 21: "remedy"}
r = pd.read_csv(os.path.join(BASE, "data", "FLAT_RCL_POST_2010", "FLAT_RCL_POST_2010.txt"), sep="\t", header=None, quoting=csv.QUOTE_NONE,
                encoding="latin-1", usecols=list(cols), dtype=str, on_bad_lines="skip").rename(columns=cols)
r = r[(r.rcltype == "V") & (r.rcdate >= "20140101")]
ADAS = re.compile(r"FORWARD COLLISION|AUTOMATIC EMERGENCY BRAK|EMERGENCY BRAKING|PHANTOM|UNEXPECTED(LY)? BRAK|UNINTENDED BRAK|LANE (KEEP|DEPARTURE|CENTER)|ADAPTIVE CRUISE|DRIVER ASSIST|AUTOPILOT|SELF-DRIVING|BLUECRUISE|SUPER CRUISE|COLLISION MITIGATION|PRE-COLLISION|AUTOSTEER|SMART SUMMON|FULL SELF", re.I)
txt = r.compname.fillna("") + " " + r.defect.fillna("")
r = r[txt.str.contains(ADAS) | r.compname.fillna("").str.contains("FORWARD COLLISION|LANE DEPARTURE|ADAS|SERVICE BRAKES", regex=True)]
r["topic"] = "adas"; r.loc[~(r.compname.fillna("") + " " + r.defect.fillna("")).str.contains(ADAS), "topic"] = "brakes"
g = r.groupby(["campno", "make", "model"]).agg(years=("year", lambda s: ", ".join(sorted(set(s.dropna()))[:12])), compname=("compname", "first"),
        rcdate=("rcdate", "first"), potaff=("potaff", "first"), defect=("defect", "first"), remedy=("remedy", "first"), topic=("topic", "first")).reset_index()
g["defect"] = g.defect.fillna("").str.slice(0, 450); g["remedy"] = g.remedy.fillna("").str.slice(0, 250)
g.to_parquet(os.path.join(BASE, "api_data", "recalls.parquet"), index=False)
print(len(g), "recall rows;", g.topic.value_counts().to_dict()); print(g[g.topic == "adas"].sort_values("rcdate").tail(5)[["campno", "make", "model", "rcdate", "compname"]].to_string())
