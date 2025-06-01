"""
Package bootstrap for Phoenix Trader.
Sets env threads, installs OpenDevin alias, and wires global crash logger
→ instant CrewAI self-fixer.
"""

import os, sys, multiprocessing as mp, pathlib, json, traceback, datetime as dt

# ---------- BLAS / NumPy: use all CPU cores -----------------------------
os.environ.update({
    "OMP_NUM_THREADS": str(mp.cpu_count()),
    "MKL_NUM_THREADS": str(mp.cpu_count()),
    "NUMEXPR_NUM_THREADS": str(mp.cpu_count())
})

# ---------- expose OpenDevin alias (side effect import) -----------------
from phoenix_trader.boot import alias  # noqa: F401

# ---------- global crash logger + instant autofix -----------------------
def _log_and_fix(exc_type, exc_value, exc_tb):
    rec = {
        "ts": dt.datetime.utcnow().isoformat(),
        "type": exc_type.__name__,
        "trace": "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    }
    log = pathlib.Path("logs/errors.jsonl")
    log.parent.mkdir(exist_ok=True)
    with log.open("a") as f:
        f.write(json.dumps(rec) + "\n")

    # kick CrewAI multi-agent fixer in the background
    try:
        from phoenix_trader.autofix.test_from_trace import write_test
        from phoenix_trader.autofix.crew_fix import run as crew_fix
        import threading
        def _worker():
            write_test()
            crew_fix()
        threading.Thread(target=_worker, daemon=True).start()
    except Exception as e:
        import logging
        logging.error("Autofix bootstrap failed: %s", e)

    # still print default traceback to stderr
    sys.__excepthook__(exc_type, exc_value, exc_tb)

sys.excepthook = _log_and_fix
