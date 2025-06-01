import duckdb, pathlib, joblib
from joblib import parallel_backend
from sklearn.linear_model import SGDClassifier
import numpy as np

MODEL_PATH = pathlib.Path("data/model.joblib")
mdl = SGDClassifier(loss="log_loss") if not MODEL_PATH.exists() else joblib.load(MODEL_PATH)

def learn_chunk():
    df = duckdb.query("SELECT label, ret, rvol FROM features ORDER BY ts DESC LIMIT 200").df()
    if df.empty:
        return
    X = df[["ret", "rvol"]].values.astype(np.float32)
    y = df["label"].values.astype(np.int8)
    with parallel_backend("threading", n_jobs=-1):
        mdl.partial_fit(X, y, classes=[0, 1])
    joblib.dump(mdl, MODEL_PATH)
    print(f"[ML] model updated on {len(df)} rows")
