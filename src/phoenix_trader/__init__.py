import multiprocessing as _mp, os as _os
from phoenix_trader.boot import alias  # noqa: F401 (side-effect import)

_os.environ.update({

    "OMP_NUM_THREADS": str(_mp.cpu_count()),

    "MKL_NUM_THREADS": str(_mp.cpu_count()),

    "NUMEXPR_NUM_THREADS": str(_mp.cpu_count())

})

import logging, json, pathlib, traceback, datetime as dt


def log_exception(exc: Exception):

    rec = {

        "ts": dt.datetime.utcnow().isoformat(),

        "type": type(exc).__name__,

        "trace": traceback.format_exc()

    }

    p = pathlib.Path("logs/errors.jsonl")

    p.parent.mkdir(exist_ok=True)

    with p.open("a") as f:

        f.write(json.dumps(rec) + "\n")

import time, importlib
importlib.import_module("phoenix_trader.scheduler.jobs").start()
time.sleep(10**9)

# -------- global crash logger (handles import-time errors too) --------
import sys, traceback, json, pathlib, datetime as _dt
def _log_unhandled(exc_type, exc_value, exc_tb):
    rec = {
        "ts": _dt.datetime.utcnow().isoformat(),
        "type": exc_type.__name__,
        "trace": "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    }
    p = pathlib.Path("logs/errors.jsonl")
    p.parent.mkdir(exist_ok=True)
    with p.open("a") as f:
        f.write(json.dumps(rec) + "\n")
    sys.__excepthook__(exc_type, exc_value, exc_tb)  # still print to stderr
sys.excepthook = _log_unhandled
    # kick off instant patch in a background thread

    try:

        from phoenix_trader.autofix.agent import run as _auto_fix

        import threading as _th

        _th.Thread(target=_auto_fix, daemon=True).start()

    except Exception as _e:

        pass

# ----------------------------------------------------------------------
