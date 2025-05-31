from apscheduler.schedulers.background import BackgroundScheduler
from ml.online import learn_chunk
from autofix.agent import run as auto_fix
from mail.report import hourly, daily

def start():
    sc = BackgroundScheduler(timezone="America/New_York")
    sc.add_job(learn_chunk, trigger="cron", minute="15,45", id="ml")
    sc.add_job(auto_fix,  trigger="cron", minute="*/30", id="fix")
    sc.add_job(hourly,    trigger="cron", minute="0",    id="hour")
    sc.add_job(daily,     trigger="cron", hour=18, minute=0, id="day")
    sc.start()
    print("Scheduler started")
    return sc
