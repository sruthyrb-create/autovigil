"""Sort NHTSA complaint narratives into precise ADAS failure modes with IBM Granite (watsonx.ai).
Run on your laptop (IBM is reachable only from there):
    python src/granite_code.py --set pilot          # 200 complaints, ~2 min: check quality first
    python src/granite_code.py --set priority1      # ~11.9k complaints on the investigated models
    python src/granite_code.py --set all            # + ~17.5k other ADAS complaints
Safe to stop and rerun: already-coded complaints are skipped.
Output: work/granite_codes.parquet
"""
import argparse, json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from dotenv import load_dotenv

BASE = os.path.join(os.path.dirname(__file__), "..")
load_dotenv(os.path.join(BASE, ".env"))
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference

MODEL_ID = os.environ.get("GRANITE_MODEL", "ibm/granite-4-h-small")
OUT = os.path.join(BASE, "work", "granite_codes_v2.parquet")   # v1 (first prompt) kept for comparison
BATCH, WORKERS = 8, 4

FAILURE_MODES = {
    "false_braking": "the vehicle braked or slowed hard by itself with NO real obstacle ahead (phantom braking, false AEB activation)",
    "failed_to_brake": "automatic braking or adaptive cruise did NOT brake when a real obstacle or vehicle was ahead",
    "false_warning": "a collision or lane warning went off with no real hazard, but the car did not brake",
    "lane_keep_wrong_steer": "lane keeping or steering assist steered the car unexpectedly or against the driver",
    "lane_keep_failed": "lane keeping or lane centering failed to keep the car in its lane",
    "acc_speed_fault": "adaptive cruise control sped up, slowed or disengaged wrongly (not a hard phantom brake)",
    "self_driving_behavior": "Autopilot, FSD, BlueCruise, Super Cruise or similar behaved dangerously in another way",
    "system_unavailable": "a driver-assist system was disabled, showed sensor or camera errors, or would not engage",
    "conventional_brake_fault": "ordinary brake hardware problem (pedal, ABS, noise, wear, leaks), not a driver-assist issue",
    "other": "anything else, or not enough detail",
}
FEATURES = ["automatic_emergency_braking", "forward_collision_warning", "adaptive_cruise", "lane_keep_assist",
            "autopilot_or_fsd", "bluecruise_or_supercruise", "none", "unknown"]

SYSTEM = ("You are a vehicle-safety analyst. You read consumer complaints sent to NHTSA and code each one. "
          "Reply with a JSON array only, no other text.")
GUIDE = "\n".join(f"- {k}: {v}" for k, v in FAILURE_MODES.items())
RULES = ("Rules: false_braking ONLY when the car itself braked or slowed hard without the driver pressing the brake. "
         "Brake noise, squealing, grinding pads, worn rotors, pedal feel, brake fluid, brake warning lights or "
         "electrical faults are conventional_brake_fault (or system_unavailable if a driver-assist system is disabled), "
         "never false_braking. A warning light alone with no braking is false_warning or system_unavailable. "
         "failure_mode must be one of the failure-mode names above, never a feature name.")
EXAMPLE = ('Example input:\n[{"id":"A1","text":"ON THE FREEWAY AT 65 MPH THE CAR SLAMMED ON THE BRAKES. NOTHING WAS IN FRONT OF ME. '
           'IT STARTED AFTER THE LAST UPDATE."},'
           '{"id":"A2","text":"THE BRAKES MAKE A LOUD SQUEALING NOISE WHEN I STOP. THE DEALER SAID THE PADS ARE WORN."}]\nExample output:\n[{"id":"A1","failure_mode":"false_braking","speed_mph":65,'
           '"feature_engaged":"unknown","obstacle_present":false,"software_update_mentioned":true},'
           '{"id":"A2","failure_mode":"conventional_brake_fault","speed_mph":null,"feature_engaged":"none",'
           '"obstacle_present":null,"software_update_mentioned":false}]')

def prompt_for(rows):
    items = [{"id": r.odino, "text": r.cdescr} for r in rows]
    return (f"Failure modes:\n{GUIDE}\n\nfeature_engaged must be one of: {', '.join(FEATURES)}.\n"
            "speed_mph is a number or null. obstacle_present is true, false or null if unclear. "
            "software_update_mentioned is true or false.\n\n"
            f"{RULES}\n\n{EXAMPLE}\n\nNow code these complaints. Return one object per id, same keys as the example:\n"
            + json.dumps(items))

def parse(text):
    m = re.search(r"\[.*\]", text, re.S)
    return json.loads(m.group(0)) if m else []

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--set", default="pilot", choices=["pilot", "priority1", "all"])
    ap.add_argument("--limit", type=int, default=None); args = ap.parse_args()
    q = pd.read_parquet(os.path.join(BASE, "work", "coding_queue.parquet"))
    q = q[q.pilot] if args.set == "pilot" else q[q.priority == 1] if args.set == "priority1" else q
    done = pd.read_parquet(OUT) if os.path.exists(OUT) else pd.DataFrame(columns=["odino"])
    q = q[~q.odino.isin(set(done.odino))]
    if args.limit: q = q.head(args.limit)
    print(f"{len(q):,} complaints to code with {MODEL_ID}")
    if q.empty: return
    creds = Credentials(url=os.environ["WATSONX_URL"], api_key=os.environ["WATSONX_APIKEY"])
    model = ModelInference(model_id=MODEL_ID, credentials=creds, project_id=os.environ["WATSONX_PROJECT_ID"],
                           params={"max_tokens": 900, "temperature": 0})
    rows = list(q.itertuples()); batches = [rows[i:i+BATCH] for i in range(0, len(rows), BATCH)]

    def run(batch):
        for attempt in range(3):
            try:
                r = model.chat(messages=[{"role": "system", "content": SYSTEM},
                                         {"role": "user", "content": prompt_for(batch)}])
                return parse(r["choices"][0]["message"]["content"])
            except Exception as e:
                time.sleep(2 * (attempt + 1)); err = e
        print("  batch failed:", type(err).__name__, str(err)[:120]); return []

    results, t0 = [], time.time()
    with ThreadPoolExecutor(WORKERS) as ex:
        futs = [ex.submit(run, b) for b in batches]
        for i, f in enumerate(as_completed(futs), 1):
            results.extend(x for x in f.result() if isinstance(x, dict))
            if i % 25 == 0 or i == len(futs):
                new = pd.DataFrame(results)
                if not new.empty:
                    new = new.rename(columns={"id": "odino"})
                    new["valid"] = new["failure_mode"].isin(list(FAILURE_MODES))
                    allc = pd.concat([done, new], ignore_index=True).drop_duplicates("odino", keep="last")
                    allc.astype({c: str for c in allc.columns}).to_parquet(OUT, index=False)
                print(f"  {i}/{len(futs)} batches, {len(results):,} coded, {time.time()-t0:.0f}s")
    print("Done. Saved to work/granite_codes.parquet")
    print(pd.read_parquet(OUT).failure_mode.value_counts().to_string())

if __name__ == "__main__":
    main()
