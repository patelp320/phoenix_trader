"""
Alias the cloned OpenDevin repo so `import opendevin …` works.
Executed for its side-effect; nothing to call.
"""
import sys, importlib, pathlib, types

root = pathlib.Path(__file__).resolve().parents[3] / "devin"
sys.path.append(str(root))
sys.path.append(str(root / "agenthub"))

alias_mod = types.ModuleType("opendevin")
alias_mod.agent = importlib.import_module("devin.agenthub.dev_agent")
sys.modules["opendevin"] = alias_mod
