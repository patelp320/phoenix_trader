import os, json, pathlib, subprocess, git, datetime as dt, requests, textwrap, threading, time
from typing import Optional

OLLAMA = os.getenv("OLLAMA_URL", "http://ollama:11434")
MODEL   = os.getenv("OLLAMA_MODEL", "codellama:13b")
REPO    = git.Repo(".")

LOG = pathlib.Path("logs/errors.jsonl")
LOG.parent.mkdir(exist_ok=True); LOG.touch(exist_ok=True)

def latest_error() -> Optional[dict]:
    lines = LOG.read_text().strip().splitlines()
    return json.loads(lines[-1]) if lines else None

def prompt(trace, code, attempt):
    return textwrap.dedent(f"""
    ### Task
    Fix the Python error below. Return a **unified git diff** only.

    ### Error
    ```
    {trace}
    ```

    ### Current code (attempt {attempt})
    ```python
    {code}
    ```

    ### Diff
    (start with 'diff --git')
    """)

def llm_diff(prompt):
    r = requests.post(f"{OLLAMA}/api/generate",
                      json={"model": MODEL, "prompt": prompt, "stream": False},
                      timeout=180)
    return r.json()["response"].strip()

def apply_patch(diff, branch):
    patch_file = pathlib.Path("autofix.patch")
    patch_file.write_text(diff)
    REPO.git.checkout("-b", branch)
    REPO.git.apply(str(patch_file))
    try:
        subprocess.run(["pytest", "-q"], check=True, timeout=180)
    except subprocess.CalledProcessError:
        REPO.git.checkout("main"); REPO.git.branch("-D", branch); return False
    REPO.index.add(all=True)
    REPO.index.commit("autofix: "+branch)
    REPO.git.push("--set-upstream", "origin", branch)
    print("[AUTOFIX] patch pushed →", branch)
    return True

def run():
    err = latest_error()
    if not err: return
    parts = [p for p in err["trace"].split('"') if p.endswith(".py")]
    if not parts: return
    file_path = pathlib.Path(parts[0])
    if not file_path.exists(): return

    code     = file_path.read_text()
    for attempt in range(1, 4):        # up to 3 tries
        diff = llm_diff(prompt(err["trace"], code, attempt))
        if not diff.startswith("diff"):
            print("[AUTOFIX] LLM produced no diff (attempt", attempt, ")")
            continue
        branch = f"autofix/{dt.datetime.utcnow():%Y%m%d_%H%M%S}_{attempt}"
        try:
            if apply_patch(diff, branch): return
        except git.GitCommandError as e:
            print("[AUTOFIX] git apply failed:", e)
        time.sleep(2)                  # tiny backoff
    print("[AUTOFIX] all attempts failed")
