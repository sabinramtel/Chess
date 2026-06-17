from app import db
from datetime import datetime


class EmailVerification(db.Model):
    __tablename__ = 'email_verifications'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    otp        = db.Column(db.String(6), nullable=True)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('email_verification', uselist=False))
