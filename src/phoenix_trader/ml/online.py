from joblib import parallel_backend
from pathlib import Path
import duckdb, joblib, datetime as dt
from sklearn.linear_model import SGDClassifier

MODEL_FILE = Path("models/latest.pkl")

def _load():
    if MODEL_FILE.exists():
        return joblib.load(MODEL_FILE)
    return SGDClassifier(loss="log_loss")

def _recent():
    db = duckdb.connect("data/price.duckdb")
    db.execute("CREATE TABLE IF NOT EXISTS features (ts TIMESTAMP, label INTEGER, x DOUBLE)")
    since = (dt.datetime.utcnow() - dt.timedelta(minutes=30)).isoformat()
    return db.execute("SELECT * FROM features WHERE ts >= ?", (since,)).fetch_df()

def learn_chunk():
    df = _recent()
    if df.empty:
        return
    X = df[["x"]]
    y = df["label"]
    mdl = _load()
    with parallel_backend("threading", n_jobs=-1):\
    with parallel_backend("threading", n_jobs=-1):\
    mdl.partial_fit(X, y, classes=[0,1])
    MODEL_FILE.parent.mkdir(exist_ok=True)
    joblib.dump(mdl, MODEL_FILE)
    print(f"[ML] model updated on {len(df)} rows  —  {dt.datetime.utcnow():%H:%M:%S}")
