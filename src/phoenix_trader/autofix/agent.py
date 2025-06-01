import os, json, pathlib, subprocess, git, datetime as dt, requests, textwrap, traceback, yfinance as yf, duckdb

OLLAMA = os.getenv("OLLAMA_URL", "http://ollama:11434")
MODEL   = os.getenv("OLLAMA_MODEL", "codellama:13b")
REPO    = git.Repo(".")

LOG = pathlib.Path("logs/errors.jsonl")
LOG.parent.mkdir(exist_ok=True)
LOG.touch(exist_ok=True)

def latest_error():
    lines = LOG.read_text().strip().splitlines()
    return json.loads(lines[-1]) if lines else None

def prompt(trace, code):
    return textwrap.dedent(f"""
    ### Task
    Provide a **unified git diff** that fixes the Python error below.
    Apply minimal changes.

    ### Error
    ```
    {trace}
    ```

    ### Current code
    ```python
    {code}
    ```

    ### Diff
    (start with 'diff --git')
    """)

def ask_llm(prompt):
    r = requests.post(f"{OLLAMA}/api/generate",
                      json={"model": MODEL, "prompt": prompt, "stream": False},
                      timeout=120)
    return r.json()["response"]

def run():
    err = latest_error()
    if not err:
        return
    # crude path extraction -> first quoted file in traceback
    parts = [p for p in err["trace"].split('"') if p.endswith(".py")]
    if not parts:
        return
    file_path = pathlib.Path(parts[0])
    if not file_path.exists():
        return

    diff = ask_llm(prompt(err["trace"], file_path.read_text())).strip()
    if not diff.startswith("diff"):
        print("[AUTOFIX] LLM returned no diff")
        return

    branch = f"autofix/{dt.datetime.utcnow():%Y%m%d_%H%M%S}"
    REPO.git.checkout("-b", branch)

    patch = pathlib.Path("autofix.patch")
    patch.write_text(diff)
    try:
        REPO.git.apply(str(patch))
    except git.GitCommandError as e:
        print("[AUTOFIX] patch failed:", e)
        REPO.git.checkout("main")
        REPO.git.branch("-D", branch)
        return

    # lightweight smoke test: import main packages
    try:
        import importlib
        importlib.import_module("phoenix_trader")
    except Exception as e:
        print("[AUTOFIX] import test failed:", e)
        REPO.git.checkout("main")
        REPO.git.branch("-D", branch)
        return

    REPO.index.add(all=True)
    REPO.index.commit(f"autofix: {err['type']}")
    try:
        REPO.git.push("--set-upstream", "origin", branch)
        print("[AUTOFIX] patch pushed →", branch)
    except Exception as e:
        print("[AUTOFIX] push failed:", e)
        REPO.git.checkout("main")
        REPO.git.branch("-D", branch)
