from werkzeug.security import generate_password_hash, check_password_hash
from app.models.base_model import BaseModel
from app.models.database import Database
from datetime import datetime

class User(BaseModel):
    @property
    def table(self):
        return "users"

    def __init__(self, username=None, email=None, password=None, rating=1200):
        self.username = username
        self.email = email
        self.__password = None
        self.rating = rating

        if password:
            self.set_password(password)

    def set_password(self, plain_password):
        self.__password = generate_password_hash(plain_password)

    def check_password(self, plain_password):
        if self.__password is None:
            return False
        return check_password_hash(self.__password, plain_password)

    def save(self):
        db = Database()
        db.execute(
            "INSERT INTO users (username, email, password_hash, rating) VALUES (%s, %s, %s, %s)",
            (self.username, self.email, self.__password, self.rating),
        )
        db.close()
        # Since auth_controller needs the user.id immediately, let's fetch it.
        result = self.find_by("email", self.email)
        if result:
            self.id = result['id']

    def update(self, user_id, update_password=False):
        db = Database()
        if update_password:
            db.execute(
                "UPDATE users SET username=%s, email=%s, password_hash=%s, rating=%s WHERE id=%s",
                (self.username, self.email, self.__password, self.rating, user_id),
            )
        else:
            db.execute(
                "UPDATE users SET username=%s, email=%s, rating=%s WHERE id=%s",
                (self.username, self.email, self.rating, user_id),
            )
        db.close()

    def email_exists(self, exclude_id=None):
        db = Database()
        if exclude_id:
            result = db.fetch_one("SELECT id FROM users WHERE email = %s AND id != %s", (self.email, exclude_id))
        else:
            result = db.fetch_one("SELECT id FROM users WHERE email = %s", (self.email,))
        db.close()
        return result is not None

    @classmethod
    def from_db(cls, data):
        if data is None:
            return None
        user = cls()
        user.id = data.get("id")
        user.username = data.get("username")
        user.email = data.get("email")
        user.__password = data.get("password_hash")
        user.rating = data.get("rating")
        return user

    def to_dict(self):
        return {
            'id': getattr(self, 'id', None),
            'email': self.email,
            'username': self.username,
            'rating': self.rating
        }

    def __repr__(self):
        return f"<User {self.username}>"
