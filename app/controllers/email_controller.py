import os
import urllib.request
import urllib.error
import json


def send_otp_email(to_email: str, username: str, otp: str) -> bool:
    api_key = os.getenv('RESEND_API_KEY', '').strip()

    if not api_key:
        print(f"\n{'='*50}")
        print(f"[DEV] Verification OTP for {to_email}: {otp}")
        print(f"{'='*50}\n")
        return True

    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;
                background:#0d0e12;color:white;padding:40px 32px;border-radius:12px;
                border:1px solid rgba(204,163,67,0.25);">
        <h2 style="color:#cca343;margin:0 0 8px;">Project Chess</h2>
        <p style="color:#9ca3af;margin:0 0 32px;font-size:14px;">Email Verification</p>
        <p style="margin:0 0 8px;">Hi <strong>{username}</strong>,</p>
        <p style="margin:0 0 24px;color:#d1d5db;">
            Use the code below to verify your account. It expires in <strong>15 minutes</strong>.
        </p>
        <div style="background:#1e2130;border:1px solid rgba(204,163,67,0.3);border-radius:8px;
                    padding:20px;text-align:center;margin-bottom:24px;">
            <span style="font-size:36px;font-weight:700;letter-spacing:10px;color:#cca343;">
                {otp}
            </span>
        </div>
        <p style="color:#6b7280;font-size:12px;margin:0;">
            If you didn't create a Project Chess account, ignore this email.
        </p>
    </div>
    """

    payload = json.dumps({
        "from": "Project Chess <onboarding@resend.dev>",
        "to": [to_email],
        "subject": "Project Chess — Verify Your Email",
        "html": html_body,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
        return True
    except Exception as exc:
        print(f"[EMAIL ERROR] {exc}")
        print(f"[DEV FALLBACK] OTP for {to_email}: {otp}")
        return True
