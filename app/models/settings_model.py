from app import db


class UserSettings(db.Model):
    __tablename__ = 'user_settings'

    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)

    # Profile
    country         = db.Column(db.String(5), default='')
    avatar_url      = db.Column(db.String(256), default='')
    bio             = db.Column(db.String(500), default='')

    # Game preferences
    board_theme          = db.Column(db.String(50), default='classic')
    piece_set            = db.Column(db.String(50), default='standard')
    board_orientation    = db.Column(db.String(10), default='auto')
    move_confirmation    = db.Column(db.Boolean, default=False)
    auto_promote_queen   = db.Column(db.Boolean, default=True)
    premove              = db.Column(db.Boolean, default=True)
    sound_effects        = db.Column(db.Boolean, default=True)

    # Notifications
    notify_game_invites    = db.Column(db.Boolean, default=True)
    notify_friend_requests = db.Column(db.Boolean, default=True)
    notify_tournaments     = db.Column(db.Boolean, default=False)
    notify_your_turn       = db.Column(db.Boolean, default=True)
    notify_daily_puzzle    = db.Column(db.Boolean, default=False)

    # Appearance
    site_theme      = db.Column(db.String(10), default='dark')

    # Privacy
    who_can_challenge  = db.Column(db.String(20), default='anyone')
    profile_visibility = db.Column(db.String(20), default='public')

    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    user = db.relationship('User', backref=db.backref('settings', uselist=False))
