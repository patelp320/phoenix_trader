import yagmail, datetime as dt, duckdb, git, os
yag = yagmail.SMTP()
def hourly():
    sha = git.Repo('.').head.commit.hexsha[:7]
    yag.send(os.getenv("EMAIL_TO"), f"[{dt.datetime.now():%H:%M}] heartbeat {sha}", "Bot alive.")
def daily():
    pnl = duckdb.query("SELECT 0").fetchone()[0]   # placeholder
    yag.send(os.getenv("EMAIL_TO"), f"Daily P/L ${pnl:.2f}", "Placeholder P/L")
