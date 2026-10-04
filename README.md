# AutoVigil

Early warning for vehicle safety defects from public NHTSA complaint data, with a driver voice-intake agent.
Built at Hack Dearborn 5 (Oct 3-4, 2026), Enchanted Transit track.

Drug regulators find dangerous medicines from patient reports. AutoVigil applies the same signal-detection
statistics (PRR, BCPNN IC025) plus IBM Granite time-series models to NHTSA complaints, and measures how many
weeks before NHTSA opened each driver-assistance investigation an alarm would have fired.

## Repository layout
- `src/load_complaints.py`, `src/load_investigations.py` - stream NHTSA flat files into compact parquet
- `src/ground_truth.py` - curated ADAS investigations (answer key)
- `src/signals.py` - weekly as-of disproportionality signals (no peeking)
- `src/backtest.py`, `src/alarm_burden.py` - lead time and alarm-burden evaluation
- `src/ibm_check.py` - connectivity check for IBM watsonx.ai
- `work/RESULTS_v1.md` - preliminary results

## Setup
1. Download from https://www.nhtsa.gov/nhtsa-datasets-and-apis (Flat File Downloads) into `data/`:
   complaints (`FLAT_CMPL`), investigations (`FLAT_INV`), recalls (`FLAT_RCL_POST_2010`) plus `CMPL.txt`, `INV.txt`, `RCL.txt`.
2. `conda env create -f environment.yml`
3. Copy `.env.example` to `.env` and add your IBM watsonx.ai credentials.
4. Run: `python src/load_complaints.py`, `python src/load_investigations.py`, `python src/ground_truth.py`,
   `python src/signals.py --prepare`, `python src/signals.py`, then `cd src && python backtest.py`.

## Data
NHTSA Office of Defects Investigation public data (US government, public domain). Personal fields
(names, VIN, city, dealer) are not loaded.
