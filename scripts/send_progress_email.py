"""Send NBA_MIKE v2 progress docs by email.

Uses Gmail SMTP by default. Credentials are read only from environment variables:
NBA_MIKE_EMAIL_FROM and NBA_MIKE_EMAIL_APP_PASSWORD.
Recipients are read from config/progress_email_recipients.txt.
"""
from pathlib import Path
from email.message import EmailMessage
import hashlib, os, smtplib, sys
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
RECIPIENTS=ROOT/"config"/"progress_email_recipients.txt"
STATE=ROOT/".local"/"progress_email_last_hash.txt"
FILES=[ROOT/"docs"/"DEVELOPMENT_JOURNAL.md", ROOT/"docs"/"NEXT_AGENT_HANDOFF.md"]

def main():
    sender=os.getenv("NBA_MIKE_EMAIL_FROM","").strip()
    password=os.getenv("NBA_MIKE_EMAIL_APP_PASSWORD","").strip()
    if not sender or not password:
        print("EMAIL: SKIP — set NBA_MIKE_EMAIL_FROM and NBA_MIKE_EMAIL_APP_PASSWORD.")
        return 2
    if not RECIPIENTS.exists():
        print(f"EMAIL: FAIL — missing {RECIPIENTS}")
        return 2
    recipients=[]
    for line in RECIPIENTS.read_text(encoding="utf-8").splitlines():
        x=line.strip()
        if x and not x.startswith("#") and x not in recipients: recipients.append(x)
    if not recipients:
        print("EMAIL: FAIL — recipient list is empty.")
        return 2
    missing=[str(x) for x in FILES if not x.exists()]
    if missing:
        print("EMAIL: FAIL — missing attachments:", *missing, sep="\n")
        return 2

    digest=hashlib.sha256()
    for f in FILES: digest.update(f.read_bytes())
    h=digest.hexdigest()
    if STATE.exists() and STATE.read_text().strip()==h and "--force" not in sys.argv:
        print("EMAIL: NO CHANGES — duplicate progress email suppressed.")
        return 0

    msg=EmailMessage()
    msg["From"]=sender
    msg["To"]=", ".join(recipients)
    msg["Subject"]="NBA_MIKE v2 progress update — journals & AI handoff"
    msg.set_content(
        "NBA_MIKE v2 progress update.\n\n"
        "Attached:\n- DEVELOPMENT_JOURNAL.md\n- NEXT_AGENT_HANDOFF.md\n\n"
        f"Sent UTC: {datetime.now(timezone.utc).isoformat()}\n"
    )
    for f in FILES:
        msg.add_attachment(f.read_bytes(), maintype="text", subtype="markdown", filename=f.name)

    with smtplib.SMTP_SSL("smtp.gmail.com",465,timeout=30) as s:
        s.login(sender,password)
        s.send_message(msg)

    STATE.parent.mkdir(parents=True,exist_ok=True)
    STATE.write_text(h,encoding="utf-8")
    print("EMAIL: SENT")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
