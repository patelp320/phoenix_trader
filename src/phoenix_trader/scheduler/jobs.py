import uvloop, asyncio
uvloop.install()

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from phoenix_trader.data.ingest import update as ingest
from phoenix_trader.ml.online import learn_chunk
from phoenix_trader.autofix.agent import run as auto_fix
from phoenix_trader.mail.report import hourly, daily
from phoenix_trader.strategies import momo

def start():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    sc = AsyncIOScheduler(timezone="America/New_York", event_loop=loop)

    # immediate warm-ups
    ingest(); learn_chunk(); auto_fix()

    # scheduled jobs
    sc.add_job(ingest,      trigger="interval", minutes=10, id="ingest")
    sc.add_job(learn_chunk, trigger="interval", minutes=5,  id="ml")
    sc.add_job(momo.run,    trigger="interval", minutes=5,  id="trade")
    sc.add_job(auto_fix,    trigger="interval", minutes=1,  id="fix")
    sc.add_job(hourly,      trigger="cron",     minute=0,   id="hour")
    sc.add_job(daily,       trigger="cron",     hour=18, minute=0, id="day")

    sc.start()
    print("Scheduler started (async)")
    loop.run_forever()
