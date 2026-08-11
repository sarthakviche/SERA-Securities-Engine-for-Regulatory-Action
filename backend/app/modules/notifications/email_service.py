"""
ResendEmailService — transactional email for SERA compliance notifications.

Design rules (from spec):
- RESEND_API_KEY empty  → skip delivery, log a warning.  Never raise.
- EMAIL_ENABLED=False   → skip delivery (allows local dev without credentials).
- Any Resend API error  → log it, do NOT re-raise.  Compliance operations must
  never fail because email delivery failed.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger("sera.notifications.email")

# ---------------------------------------------------------------------------
# Email subject/body templates per event type
# ---------------------------------------------------------------------------

_SUBJECT_MAP: dict[str, str] = {
    "task.created": "SERA | Compliance Task Assigned",
    "task.overdue": "SERA | Compliance Task Overdue",
    "task.completed": "SERA | Compliance Task Completed",
    "evidence.submitted": "SERA | Evidence Submitted",
    "evidence.rejected": "SERA | Evidence Rejected",
    "evidence.accepted": "SERA | Evidence Accepted",
    "compliance.gap_detected": "SERA | Compliance Gap Detected",
    "compliance.verified": "SERA | Compliance Verified",
    "escalation.triggered": "SERA | Escalation Triggered",
    "gate_2.rejected": "SERA | Approval Required",
    "workflow.stage_completed": "SERA | Implementation Tasks Created",
}


def _build_html(title: str, body: Optional[str], resource_url: Optional[str]) -> str:
    """Build a simple branded HTML email body."""
    cta_html = ""
    if resource_url:
        cta_html = f"""
        <div style="margin-top:28px;">
          <a href="{resource_url}"
             style="background:#4f46e5;color:#fff;padding:12px 24px;
                    border-radius:6px;text-decoration:none;font-weight:600;
                    font-size:14px;display:inline-block;">
            Open in SERA →
          </a>
        </div>"""

    body_html = f"<p style='color:#374151;font-size:14px;margin:8px 0'>{body}</p>" if body else ""

    return f"""
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f9fafb;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0"
         style="background:#f9fafb;padding:40px 0;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0"
             style="background:#ffffff;border-radius:12px;
                    border:1px solid #e5e7eb;overflow:hidden;">
        <!-- Header -->
        <tr>
          <td style="background:#1e1b4b;padding:24px 32px;">
            <span style="color:#fff;font-size:20px;font-weight:700;
                         letter-spacing:-0.5px;">SERA</span>
            <span style="color:#a5b4fc;font-size:10px;font-weight:600;
                         text-transform:uppercase;letter-spacing:3px;
                         margin-left:10px;">Regulatory Intelligence</span>
          </td>
        </tr>
        <!-- Body -->
        <tr>
          <td style="padding:32px;">
            <h1 style="margin:0 0 8px;font-size:20px;font-weight:700;
                        color:#111827;">{title}</h1>
            {body_html}
            {cta_html}
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td style="padding:16px 32px;border-top:1px solid #f3f4f6;">
            <p style="margin:0;font-size:11px;color:#9ca3af;">
              This is an automated notification from SERA.
              You can manage your notification preferences in
              <a href="#" style="color:#4f46e5;">Settings → Notifications</a>.
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


class ResendEmailService:
    """Wraps the Resend SDK for SERA transactional emails."""

    def __init__(self) -> None:
        self._client: Optional[object] = None
        self._ready = False
        self._from_email = ""
        self._to_email = ""
        self._enabled = False

    def configure(
        self,
        api_key: str,
        from_email: str,
        to_email: str,
        enabled: bool,
    ) -> None:
        """
        Called once at application startup.  If api_key is empty or enabled is
        False, all send() calls become no-ops.
        """
        self._from_email = from_email
        self._to_email = to_email
        self._enabled = enabled

        if not enabled:
            logger.info("email notifications disabled via EMAIL_ENABLED=False")
            return

        if not api_key:
            logger.warning(
                "RESEND_API_KEY is not set — email notifications will be skipped"
            )
            return

        try:
            import resend  # type: ignore[import]
            resend.api_key = api_key
            self._client = resend
            self._ready = True
            logger.info("Resend email client configured (from=%s)", from_email)
        except ImportError:
            logger.warning(
                "resend package is not installed — email notifications disabled. "
                "Run: pip install resend"
            )

    def send_notification_email(
        self,
        *,
        event_type: str,
        title: str,
        body: Optional[str] = None,
        resource_url: Optional[str] = None,
    ) -> None:
        """
        Send a transactional notification email.

        This method NEVER raises — any failure is logged and swallowed so
        that the compliance workflow is not disrupted by email issues.
        """
        if not self._ready or not self._to_email:
            logger.debug(
                "email skipped (not ready or no recipient): event=%s", event_type
            )
            return

        subject = _SUBJECT_MAP.get(event_type, f"SERA | {title}")
        html = _build_html(title, body, resource_url)

        try:
            assert self._client is not None
            params = {
                "from": self._from_email,
                "to": [self._to_email],
                "subject": subject,
                "html": html,
            }
            self._client.Emails.send(params)
            logger.info(
                "email sent: event=%s to=%s subject=%r",
                event_type,
                self._to_email,
                subject,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "email delivery failed (event=%s): %s — in-app notification is unaffected",
                event_type,
                exc,
            )


# Module-level singleton — configured in main.py lifespan
email_service = ResendEmailService()
