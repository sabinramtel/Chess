from app.models.database import Database


class GameRecord:
    def __init__(self, white_username, black_username, result, reason, move_count=0,
                 white_user_id=None, black_user_id=None):
        self.white_username = white_username
        self.black_username = black_username
        self.white_user_id = white_user_id
        self.black_user_id = black_user_id
        self.result = result      # 'white', 'black', or 'draw'
        self.reason = reason      # 'checkmate', 'resigned', 'timeout', 'stalemate', 'draw'
        self.move_count = move_count

    def save(self):
        db = Database()
        db.execute(
            """INSERT INTO games
               (white_username, black_username, white_user_id, black_user_id,
                result, reason, move_count)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (self.white_username, self.black_username,
             self.white_user_id, self.black_user_id,
             self.result, self.reason, self.move_count),
        )
        db.close()

    @staticmethod
    def find_recent_by_user_id(user_id, limit=6):
        db = Database()
        rows = db.fetch_all(
            """SELECT * FROM games
               WHERE white_user_id = %s OR black_user_id = %s
               ORDER BY played_at DESC
               LIMIT %s""",
            (user_id, user_id, limit),
        )
        db.close()
        return rows

    @staticmethod
    def get_user_id_by_username(username):
        db = Database()
        row = db.fetch_one("SELECT id FROM users WHERE username = %s", (username,))
        db.close()
        return row['id'] if row else None
