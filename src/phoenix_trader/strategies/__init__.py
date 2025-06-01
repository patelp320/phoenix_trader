"""
Strategy package.

Exports:
    momo.run   – default momentum example strategy
"""
from importlib import import_module, util as _util

# auto-load momo if present; otherwise fallback stub
try:
    momo = import_module("phoenix_trader.strategies.momo")
except ModuleNotFoundError:
    import types, sys, logging
    logging.warning("⚠️  No momo.py strategy found; using stub that does nothing.")
    momo = types.ModuleType("momo")
    def _noop(): print("[STRAT] stub - no strategy implemented")
    momo.run = _noop
    sys.modules["phoenix_trader.strategies.momo"] = momo
