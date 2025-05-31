import os, datetime as dt, sys
try:
    import yagmail
    SMTP_USER = os.getenv("EMAIL_USER")
    SMTP_PASS = os.getenv("EMAIL_PASS")
    yag = yagmail.SMTP(SMTP_USER, SMTP_PASS) if SMTP_USER and SMTP_PASS else None
except Exception as e:  # yagmail missing or mis-configured
    yag = None
    print("[MAIL] e-mail disabled →", e, file=sys.stderr)

def hourly():
    subject = f"[{dt.datetime.now():%H:%M}] heartbeat"
    body = "Bot alive."
    if yag:
        yag.send(to=os.getenv("EMAIL_TO"), subject=subject, contents=body)
    else:
        print("[MAIL] (disabled) " + subject)

def daily():
    subject = "Daily P/L $0.00 (placeholder)"
    if yag:
        yag.send(to=os.getenv("EMAIL_TO"), subject=subject, contents="P/L stub")
    else:
        print("[MAIL] (disabled) " + subject)
