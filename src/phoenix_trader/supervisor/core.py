import json, pathlib, time, subprocess, smtplib, email.message, git, datetime as dt, os

LOG      = pathlib.Path("logs/errors.jsonl")
GOOD_TAG = "good/"          # prefix
THRESH   = 3                # crashes
WINDOW   = 600              # seconds
EMAIL_TO = os.getenv("EMAIL_USER")

REPO = git.Repo(".")

def _send_mail(subject, body):
    try:
        import yagmail
        yag = yagmail.SMTP(user=os.getenv("EMAIL_USER"),
                           password=os.getenv("EMAIL_PASS"))
        yag.send(EMAIL_TO, subject, body)
    except Exception as e:
        print("[SUP] email failed:", e)

def tag_good():
    tag = f"{GOOD_TAG}{dt.datetime.utcnow():%Y%m%d_%H%M%S}"
    REPO.git.tag("-f", tag)
    REPO.git.push("--tags", "--force")
    print("[SUP] tagged good commit →", tag)

def maybe_rollback():
    if not LOG.exists(): return
    lines = LOG.read_text().strip().splitlines()
    if len(lines) < THRESH: return
    # last N timestamps
    ts = [dt.datetime.fromisoformat(json.loads(l)["ts"]) for l in lines[-THRESH:]]
    if (ts[-1] - ts[0]).total_seconds() > WINDOW:
        return
    # count tag list
    good_tags = [t for t in REPO.tags if str(t).startswith(GOOD_TAG)]
    if not good_tags:
        return
    target = sorted(good_tags, key=lambda t: str(t))[-1]
    print("[SUP] crash quorum met – rolling back to", target)
    REPO.git.checkout(str(target), force=True)
    REPO.git.push("--force")        # fast-forward main to tag
    _send_mail("Phoenix rollback",
               f"Rolled back to {target} after {THRESH} crashes in {WINDOW}s")
    # hard restart container (inside container context it exits; compose restarts)
    subprocess.Popen(["supervisorctl", "stop", "ALL"]) if shutil.which("supervisorctl") else os._exit(1)
