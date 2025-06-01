#!/usr/bin/env python3
"""
Self-Healing Orchestrator v0.5
------------------------------
• Regression tests    • Atheris fuzz (30 s)   • Bandit security scan
• Model ensemble:     CodeLlama-13B ➜ DeepSeek-33B
• Auto-pip upgrades   • Draft PR & e-mail on repeated failure
"""
from __future__ import annotations
import datetime as _dt, json, os, pathlib, re, subprocess as sp, sys, tempfile, time
from email.message import EmailMessage
from typing import List, Tuple
ROOT   = pathlib.Path(__file__).resolve().parent.parent   # patch repo root
MEMORY = ROOT / ".selfheal" / "memory.jsonl"; MEMORY.parent.mkdir(exist_ok=True)
OLLAMA_URL   = os.getenv("LOCAL_OLLAMA", "http://localhost:11434")
MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", 3))
AUTO_PIP     = os.getenv("AUTO_PIP", "1") == "1"
PIP_BASE     = f"{sys.executable} -m pip install --no-cache-dir".split()
SEC_CMD      = os.getenv("SEC_CMD", "bandit -r -q -ll .").split()
FUZZ_CMD     = [sys.executable, "tools/fuzz.py", "--max_total_time=30"]
BOT_ALERT_TO = os.getenv("BOT_ALERT_TO")
PR_THRESHOLD = MAX_ATTEMPTS * 2
TEST_CMD = os.getenv("TEST_CMD", "pytest -q --maxfail=1").split()
LINT_CMD = os.getenv("LINT_CMD", "ruff .").split()
GIT_ENV = {
    "GIT_AUTHOR_NAME":  os.getenv("GIT_AUTHOR_NAME",  "Self-Healer Bot"),
    "GIT_AUTHOR_EMAIL": os.getenv("GIT_AUTHOR_EMAIL", "bot@localhost"),
}
def _run(cmd: List[str], **kw) -> Tuple[int, str]:
    p = sp.run(cmd, cwd=ROOT, text=True, capture_output=True, **kw)
    return p.returncode, p.stdout + p.stderr
def auto_install(log: str) -> bool:
    if not AUTO_PIP: return False
    miss = set(re.findall(r"No module named '([^']+)'", log))
    upg  = set(re.findall(r"requires (\\S+?), but", log))
    pkgs = sorted(miss | upg); changed = False
    for pkg in pkgs:
        c, o = _run(PIP_BASE + ["--upgrade", pkg]); print(o); changed |= c == 0
    return changed
def detect_issues() -> str | None:
    for cmd, tag in ((TEST_CMD, "pytest"), (LINT_CMD, "ruff"), (SEC_CMD, "bandit")):
        c, o = _run(cmd);   # nosec
        if c: return f"{tag} failed:\\n{o}"
    if pathlib.Path("tools/fuzz.py").exists():
        c, o = _run(FUZZ_CMD)
        if c: return f"fuzz crash:\\n{o}"
    return None
LLM_HEADER = "Return ONLY a unified git diff that fixes the error."
MODELS = ["codellama:13b", "deepseek-coder:33b-instruct-q4"]
def llm(model: str, prompt: str) -> str:
    import requests, uuid
    r = requests.post(f"{OLLAMA_URL}/api/generate",
                      json={"model": model, "prompt": prompt, "stream": False,
                            "id": str(uuid.uuid4())}, timeout=1800)
    r.raise_for_status(); return r.json().get("response", "").strip()
def propose(err: str, mem: str) -> str:
    prompt = f"{LLM_HEADER}\\n\\nPrev notes:\\n{mem}\\n\\nError:\\n{err}\\n\\n<diff>"
    for m in MODELS:
        print("🤖 model →", m)
        diff = llm(m, prompt)
        if "@@" in diff: return diff
    return ""
def apply(diff: str) -> bool:
    if "@@" not in diff: return False
    with tempfile.NamedTemporaryFile("w", delete=False) as tf: tf.write(diff)
    ok, _ = _run(["git", "apply", tf.name]); pathlib.Path(tf.name).unlink(missing_ok=True)
    return ok == 0
def write_regression():
    ts = _dt.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    p  = ROOT / "tests" / f"regression_{ts}.py"; p.parent.mkdir(exist_ok=True)
    p.write_text("def test_regression():\\n    assert False, 'Prevent regression'\\n")
    _run(["git", "add", str(p)]); print("🧪 regression test →", p)
def commit(msg: str):
    _run(["git", "add", "-A"]); env = os.environ.copy(); env.update(GIT_ENV)
    _run(["git", "commit", "-m", msg], env=env)
    l = json.dumps({"t": _dt.datetime.utcnow().isoformat(timespec="seconds"), "m": msg})
    MEMORY.write_text((MEMORY.read_text()+"\\n" if MEMORY.exists() else "")+l)
def mem_tail(n=20): return "\\n".join(MEMORY.read_text().splitlines()[-n:]) if MEMORY.exists() else ""
def email(log: str):
    if not BOT_ALERT_TO: return
    msg = EmailMessage(); msg["From"]=GIT_ENV["GIT_AUTHOR_EMAIL"]; msg["To"]=BOT_ALERT_TO
    msg["Subject"]="Self-healer stalled"; msg.set_content(log[-4000:])
    sp.run(["sendmail","-t"],input=msg.as_string(),text=True)
def draft_pr():
    tok = os.getenv("GITHUB_TOKEN");  # optional
    if not tok: return
    b = f"bot/failure_{int(time.time())}"
    _run(["git","checkout","-B",b]); _run(["git","push","-u","origin",b])
    _run(["gh","pr","create","--draft","-t","[BOT] Needs review",
          "-b","Auto-fix loop stalled."])
    print("📬 draft PR →", b)
def main():
    fails = 0
    while True:
        err = detect_issues()
        if err is None:
            print("✅ clean – sleep 10 min"); fails = 0; time.sleep(600); continue
        if auto_install(err): print("🔁 retest after auto-pip"); continue
        if fails >= PR_THRESHOLD:
            print("🛑 escalate via email + PR"); email(err); draft_pr()
            fails = 0; time.sleep(600); continue
        print(f"❌ attempt {fails+1}/{MAX_ATTEMPTS}")
        diff = propose(err, mem_tail())
        if not apply(diff): print("⚠️ diff rejected"); fails += 1; continue
        if detect_issues() is None:
            write_regression(); commit(f"auto-fix cycle {fails+1}")
            print("🎉 fixed & committed"); fails = 0
        else:
            _run(["git","reset","--hard","HEAD"]); print("⏪ revert"); fails += 1
        time.sleep(30)
if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print("👋 bye")
