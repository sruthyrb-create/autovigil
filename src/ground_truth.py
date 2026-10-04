"""Curated ground truth: ADAS investigations opened 2016+ (consumer vehicles), from FLAT_INV.
category 'complaint' = false-activation probes where owner complaints are the plausible trigger (primary set, RQ1)
category 'crash'     = probes triggered mainly by crashes / video (secondary set)"""
import pandas as pd, os
ROWS = [
 # action, open date, make, models, component group, category, short label
 ("DP19001","2019-04-08","NISSAN",["ROGUE","ROGUE SPORT"],"FORWARD COLLISION AVOIDANCE","complaint","Nissan Rogue false AEB"),
 ("PE22002","2022-02-16","TESLA",["MODEL 3","MODEL Y"],"FORWARD COLLISION AVOIDANCE","complaint","Tesla phantom braking"),
 ("PE22003","2022-02-21","HONDA",["ACCORD","ACCORD HYBRID","CR-V"],"FORWARD COLLISION AVOIDANCE","complaint","Honda Accord/CR-V false AEB"),
 ("PE23010","2023-05-26","FREIGHTLINER",["CASCADIA"],"FORWARD COLLISION AVOIDANCE","complaint","Freightliner Cascadia AEB errors"),
 ("PE23017","2023-09-28","VOLKSWAGEN",["ATLAS"],"FORWARD COLLISION AVOIDANCE","complaint","VW Atlas false AEB"),
 ("PE24008","2024-03-07","HONDA",["INSIGHT","PASSPORT"],"FORWARD COLLISION AVOIDANCE","complaint","Honda Insight/Passport false AEB"),
 ("PE24013","2024-05-08","FISKER",["OCEAN"],"FORWARD COLLISION AVOIDANCE","complaint","Fisker Ocean false AEB"),
 ("PE24025","2024-09-10","VINFAST",["VF 8","VF8"],"LANE DEPARTURE","complaint","VinFast VF 8 lane keep"),
 ("PE21020","2021-08-13","TESLA",["MODEL 3","MODEL S","MODEL X","MODEL Y"],"ADAS (ELECTRICAL)","crash","Tesla Autopilot first-responder crashes"),
 ("PE24012","2024-04-25","FORD",["MUSTANG MACH E","MUSTANG MACH-E"],"ADAS (ELECTRICAL)","crash","Ford BlueCruise collisions"),
 ("PE24031","2024-10-17","TESLA",["MODEL 3","MODEL S","MODEL X","MODEL Y","CYBERTRUCK"],"ADAS (ELECTRICAL)","crash","Tesla FSD low visibility"),
 ("PE24033","2025-01-06","TESLA",["MODEL 3","MODEL S","MODEL X","MODEL Y"],"ADAS (ELECTRICAL)","crash","Tesla Actually Smart Summon"),
 ("PE25012","2025-10-07","TESLA",["MODEL 3","MODEL S","MODEL X","MODEL Y","CYBERTRUCK"],"ADAS (ELECTRICAL)","crash","Tesla FSD traffic violations"),
]
def load():
    df = pd.DataFrame(ROWS, columns=["action","odate","make","models","group","category","label"])
    df["odate"] = pd.to_datetime(df["odate"])
    return df
if __name__ == "__main__":
    d = load(); d.to_csv(os.path.join(os.path.dirname(__file__),"..","work","ground_truth.csv"), index=False); print(d[["action","odate","label","category"]])
