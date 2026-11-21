"""Email and Telegram delivery plus the stored notification record."""
import json
import smtplib
import urllib.request
from app import i18n
from app.core.logging_config import log
from app.i18n import tr
from email.message import EmailMessage
from app.core.config import SMTP_FROM, SMTP_HOST, SMTP_PASS, SMTP_PORT, SMTP_USER, TG
from app.db.models import Elderly, Notification, User

def send_email(to, subject, text):
    if not (SMTP_HOST and to): return
    try:
        m = EmailMessage(); m["From"], m["To"], m["Subject"] = SMTP_FROM, to, subject; m.set_content(text)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as s:
            s.starttls()
            if SMTP_USER: s.login(SMTP_USER, SMTP_PASS)
            s.send_message(m)
    except Exception as ex: log.warning("email failed: %s", ex)

def notify(db, a):
    """Store the notification as a key + parameters, then send it in the caregiver's own language."""
    e = db.get(Elderly, a.elderly_id); cg = db.get(User, e.caregiver_id) if e and e.caregiver_id else None
    codes = i18n.load_reasons(a.reasons) or []
    payload = ({"key": "notif.risk", "params": {"name": e.name, "level": a.level, "reason_codes": codes}} if a.stage <= 3
               else {"key": "notif.emergency", "params": {"name": e.name, "contact": e.emergency_contact or "", "reason_codes": codes}})
    cg_lang = (cg.lang if cg and cg.lang else i18n.DEFAULT_LANG)
    text = i18n.render_notification(json.dumps(payload, ensure_ascii=False), cg_lang)
    db.add(Notification(user_id=cg.id if cg else None, alert_id=a.id, text=json.dumps(payload, ensure_ascii=False))); db.commit()
    if cg:
        send_email(cg.email, tr("notif.subject", cg_lang, name=e.name), text)
        if TG and cg.telegram_chat_id:
            try:
                urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{TG}/sendMessage",
                    data=json.dumps({"chat_id": cg.telegram_chat_id, "text": text}).encode(),
                    headers={"Content-Type": "application/json"}), timeout=5)
            except Exception as ex: log.warning("telegram failed: %s", ex)
