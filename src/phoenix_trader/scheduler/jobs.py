from apscheduler.schedulers.background import BackgroundScheduler
from phoenix_trader.ml.online import learn_chunk
from phoenix_trader.data.ingest import update as ingest
from phoenix_trader.autofix.agent import run as auto_fix
from phoenix_trader.mail.report import hourly, daily

def start():
    sc = BackgroundScheduler(timezone="America/New_York")
    sc.add_job(learn_chunk, trigger="cron", minute="15,45", id="ml")
    sc.add_job(ingest, trigger="cron", minute="*/10", id="ingest", \
               kwargs={"UNIVERSE": "AAPL MSFT NVDA"})
    sc.add_job(hourly,    trigger="cron", minute="0",    id="hour")
    sc.add_job(daily,     trigger="cron", hour=18, minute=0, id="day")
    sc.start()
    print("Scheduler started")
    auto_fix();  # immediate self-patch attempt on startup

    sc.add_job(auto_fix, trigger="interval", minutes=1, id="fix")
    return sc
