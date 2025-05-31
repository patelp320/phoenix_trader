import time, importlib
importlib.import_module("phoenix_trader.scheduler.jobs").start()
time.sleep(10**9)
