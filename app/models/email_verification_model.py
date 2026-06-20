from app.models.base_model import BaseModel
from app.models.database import Database
from datetime import datetime

class EmailVerification(BaseModel):
    @property
    def table(self):
        return "email_verifications"

    def __init__(self, user_id=None, otp=None, is_verified=False, expires_at=None):
        self.user_id = user_id
        self.otp = otp
        self.is_verified = is_verified
        self.expires_at = expires_at

    def save(self):
        db = Database()
        db.execute(
            "INSERT INTO email_verifications (user_id, otp, is_verified, expires_at) VALUES (%s, %s, %s, %s)",
            (self.user_id, self.otp, self.is_verified, self.expires_at)
        )
        db.close()

    def update(self):
        db = Database()
        db.execute(
            "UPDATE email_verifications SET otp=%s, is_verified=%s, expires_at=%s WHERE user_id=%s",
            (self.otp, self.is_verified, self.expires_at, self.user_id)
        )
        db.close()

    @classmethod
    def from_db(cls, data):
        if data is None:
            return None
        ev = cls()
        ev.id = data.get("id")
        ev.user_id = data.get("user_id")
        ev.otp = data.get("otp")
        ev.is_verified = bool(data.get("is_verified"))
        ev.expires_at = data.get("expires_at")
        return ev
