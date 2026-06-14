"""
utils.py — Carelix shared helpers
==================================
Owner: M1 (Backend Lead)

Contains:
- send_alert_email(): Brevo transactional email helper used when a
  hospital accesses a patient's emergency profile. Logs every attempt
  to the alert_logs table.
"""

import os
import requests
from datetime import datetime

from model import db, AlertLog

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def send_alert_email(patient, hospital):
    """
    Send a transactional email to the patient's emergency contact via
    Brevo, notifying them that a hospital just accessed the patient's
    emergency profile. Logs the attempt (sent/failed) to alert_logs.

    Returns the AlertLog row that was created.
    """
    api_key      = os.environ.get("BREVO_API_KEY", "")
    sender_email = os.environ.get("BREVO_SENDER_EMAIL", "alerts@carelix.com")
    sender_name  = os.environ.get("BREVO_SENDER_NAME", "Carelix Alerts")

    subject = f"\U0001F6A8 Emergency Profile Accessed — Carelix"

    message_html = f"""
    <div style="font-family: 'DM Sans', Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 16px;">
      <h2 style="color:#0a1f44; margin-top:0;">Emergency Profile Accessed</h2>
      <p style="color:#475569; line-height:1.6;">
        Someone is accessing <strong>{patient.full_name}</strong>'s Carelix emergency
        profile at <strong>{hospital.name}</strong>.
      </p>
      <p style="color:#475569; line-height:1.6;">
        If this is unexpected, please try to contact {patient.full_name} directly
        {f"at <strong>{patient.emergency_contact_phone}</strong>" if patient.emergency_contact_phone else ""}
        as soon as possible.
      </p>
      <p style="color:#94a3b8; font-size:12px; margin-top:24px;">
        This is an automated message from Carelix — Healthcare Access Platform.
      </p>
    </div>
    """

    status = AlertLog.STATUS_FAILED
    brevo_message_id = None

    if api_key:
        try:
            response = requests.post(
                BREVO_API_URL,
                headers={
                    "api-key": api_key,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json={
                    "sender": {"name": sender_name, "email": sender_email},
                    "to": [{
                        "email": patient.emergency_contact_email,
                        "name": patient.emergency_contact_name,
                    }],
                    "subject": subject,
                    "htmlContent": message_html,
                },
                timeout=10,
            )
            if response.status_code in (200, 201):
                status = AlertLog.STATUS_SENT
                try:
                    brevo_message_id = response.json().get("messageId")
                except Exception:
                    brevo_message_id = None
            else:
                status = AlertLog.STATUS_FAILED
        except Exception:
            status = AlertLog.STATUS_FAILED
    else:
        # No API key configured (dev mode) — log as sent for demo purposes
        # so the UI flow can be tested end-to-end without a Brevo account.
        status = AlertLog.STATUS_SENT

    alert = AlertLog(
        patient_id       = patient.id,
        hospital_id      = hospital.id,
        recipient_email  = patient.emergency_contact_email,
        recipient_name   = patient.emergency_contact_name,
        subject          = subject,
        message_html     = message_html,
        brevo_message_id = brevo_message_id,
        status           = status,
        sent_at          = datetime.utcnow(),
    )
    db.session.add(alert)
    db.session.commit()
    return alert