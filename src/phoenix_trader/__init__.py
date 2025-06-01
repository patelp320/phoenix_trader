import multiprocessing as _mp, os as _os

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
