import json, pathlib, datetime as dt, subprocess, git, requests, os
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "codellama:13b")
REPO = git.Repo('.')

def _last_error():
    p = pathlib.Path("logs/errors.jsonl")
    return None if not p.exists() else json.loads(p.read_text().splitlines()[-1])

def _ask_llm(trace: str):
    prompt = f"Return ONLY a unified git diff that fixes the following Python stack-trace:\n{trace}"
    r = requests.post(f"{OLLAMA_URL}/api/generate",
                      json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False})
    diff = r.json().get("response", "").strip()
    return diff if diff.startswith("diff") else None

def run():
    err = _last_error()
    if not err:
        return
    diff = _ask_llm(err["trace"])
    if not diff:
        return
    pathlib.Path("autofix.patch").write_text(diff)
    subprocess.run(["git", "apply", "autofix.patch"], check=True)
    REPO.git.add(all=True)
    branch = f"autofix/{dt.datetime.utcnow():%Y%m%d_%H%M}"
    REPO.git.checkout("-b", branch)
    REPO.index.commit(f"autofix {err['type']}")
    REPO.git.push("--set-upstream", "origin", branch)
    print("[AUTOFIX] patch pushed →", branch)
