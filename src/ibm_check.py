"""2-minute check that your laptop can reach IBM watsonx.ai and that Granite can sort complaints.
Run from the AutoVigil folder:   python src/ibm_check.py
"""
import json, os, sys
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
from ibm_watsonx_ai import Credentials, APIClient
from ibm_watsonx_ai.foundation_models import ModelInference

creds = Credentials(url=os.environ["WATSONX_URL"], api_key=os.environ["WATSONX_APIKEY"])
project = os.environ["WATSONX_PROJECT_ID"]
client = APIClient(creds, project_id=project)
print("1) Connected to watsonx.ai")

specs = client.foundation_models.get_model_specs().get("resources", [])
ids = sorted(m["model_id"] for m in specs)
print("2) Models you can use:")
for i in ids:
    if any(k in i for k in ("granite", "llama", "mistral")): print("   ", i)
try:
    ts = client.foundation_models.get_time_series_model_specs().get("resources", [])
    print("3) Time-series models:", [m["model_id"] for m in ts] or "none listed")
except Exception as e:
    print("3) Time-series model list not available:", type(e).__name__)

MODEL = next((m for m in ["ibm/granite-4-h-small", "ibm/granite-3-3-8b-instruct", "ibm/granite-3-2-8b-instruct", "ibm/granite-3-8b-instruct"] if m in ids), None)
if MODEL is None: sys.exit("No Granite instruct model found; send Claude the list above.")
model = ModelInference(model_id=MODEL, credentials=creds, project_id=project,
                       params={"decoding_method": "greedy", "max_new_tokens": 120})
complaint = ("WHILE DRIVING ON THE HIGHWAY AT 70 MPH WITH ADAPTIVE CRUISE ON, THE CAR SLAMMED ON THE BRAKES "
             "FOR NO REASON. THERE WAS NOTHING IN FRONT OF ME. IT HAS HAPPENED 3 TIMES SINCE THE LAST SOFTWARE UPDATE.")
prompt = ("Classify this vehicle safety complaint. Reply with JSON only, keys: failure_mode "
          "(one of: false_braking, failed_to_brake, lane_keep_wrong_steer, cruise_control_fault, warning_only, other), "
          "speed_mph (number or null), feature_engaged (string or null), software_update_mentioned (true/false).\n\n"
          f"Complaint: {complaint}\nJSON:")
out = model.generate_text(prompt=prompt)
print(f"4) {MODEL} says:", out.strip())
print("\nAll good if you see JSON above. Paste this whole output (it has no secrets) back to Claude.")
