"""Stream NHTSA FLAT_CMPL.txt (tab-delimited, no header) into compact parquet files.
Keeps vehicle complaints received 2014-01-01 onward.
Outputs (in work/):
  complaints.parquet  - one row per complaint x component (no narrative)
  narratives.parquet  - one row per complaint (ODINO) with narrative text
"""
import csv, os, sys, time
import pandas as pd
import pyarrow as pa, pyarrow.parquet as pq

BASE = os.path.join(os.path.dirname(__file__), "..")
SRC = os.path.join(BASE, "data", "FLAT_CMPL", "FLAT_CMPL.txt")
OUT = os.path.join(BASE, "work")

COLS = {0:"cmplid",1:"odino",2:"mfr_name",3:"make",4:"model",5:"year",6:"crash",7:"faildate",
        8:"fire",9:"injured",10:"deaths",11:"compdesc",13:"state",16:"ldate",17:"miles",
        19:"cdescr",20:"cmpl_type",31:"veh_speed",45:"prod_type"}
MIN_LDATE = "20140101"

def main():
    t0 = time.time()
    w_c = w_n = None
    n_in = n_keep = 0
    reader = pd.read_csv(SRC, sep="\t", header=None, quoting=csv.QUOTE_NONE, dtype=str,
                         usecols=list(COLS), encoding="latin-1", chunksize=150_000,
                         on_bad_lines="skip", engine="c")
    for chunk in reader:
        n_in += len(chunk)
        chunk = chunk.rename(columns=COLS)
        chunk = chunk[(chunk["prod_type"] == "V") & (chunk["ldate"].fillna("") >= MIN_LDATE)]
        if chunk.empty:
            continue
        n_keep += len(chunk)
        for c in ["make","model","compdesc","mfr_name","state","cmpl_type"]:
            chunk[c] = chunk[c].str.strip().str.upper()
        nar = chunk[["odino","cdescr"]].drop_duplicates("odino")
        comp = chunk.drop(columns=["cdescr","prod_type"])
        tc = pa.Table.from_pandas(comp, schema=pa.schema([(c, pa.string()) for c in comp.columns]), preserve_index=False)
        tn = pa.Table.from_pandas(nar, schema=pa.schema([(c, pa.string()) for c in nar.columns]), preserve_index=False)
        if w_c is None:
            w_c = pq.ParquetWriter(os.path.join(OUT, "complaints.parquet"), tc.schema, compression="zstd")
            w_n = pq.ParquetWriter(os.path.join(OUT, "narratives.parquet"), tn.schema, compression="zstd")
        w_c.write_table(tc); w_n.write_table(tn)
        print(f"read {n_in:,} kept {n_keep:,}  {time.time()-t0:.0f}s", flush=True)
    w_c.close(); w_n.close()
    print(f"DONE read {n_in:,} kept {n_keep:,} in {time.time()-t0:.0f}s", flush=True)

if __name__ == "__main__":
    main()
