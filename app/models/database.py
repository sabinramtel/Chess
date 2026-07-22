import pymysql
import config

class Database:
    def __init__(self):
        """Open a database connection when object is created."""
        try:
            import os
            from urllib.parse import urlparse
            
            db_url = os.environ.get("MYSQL_URL") or os.environ.get("DATABASE_URL")
            if db_url:
                db_url = db_url.strip()

            if db_url and db_url.startswith("mysql"):
                parsed = urlparse(db_url)
                self.__connection = pymysql.connect(
                    host=parsed.hostname,
                    user=parsed.username,
                    password=parsed.password,
                    database=parsed.path.lstrip("/"),
                    port=parsed.port or 3306,
                    cursorclass=pymysql.cursors.DictCursor,
                )
            else:
                self.__connection = pymysql.connect(
                    host=config.MYSQL_HOST,
                    user=config.MYSQL_USER,
                    password=config.MYSQL_PASSWORD,
                    database=config.MYSQL_DATABASE,
                    cursorclass=pymysql.cursors.DictCursor,
                )
            # print("Database connected successfully!")
        except pymysql.MySQLError as e:
            print("Database connection failed!")
            print("Error:", e)
            raise
 
    def fetch_one(self, query, params=None):
        """Run a query and return ONE result (or None)."""
        cursor = self.__connection.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        cursor.close()
        return result

    def fetch_all(self, query, params=None):
        """Run a query and return ALL results as a list."""
        cursor = self.__connection.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        return results

    def execute(self, query, params=None):
        """Run a query that changes data (INSERT, UPDATE, DELETE)."""
        cursor = self.__connection.cursor()
        cursor.execute(query, params)
        self.__connection.commit()
        cursor.close()

    def close(self):
        """Close the database connection."""
        self.__connection.close()

                        
    # ── Static Method: Create tables on app startup ─────────

    @staticmethod
    def create_tables():
        db = Database()
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(80) NOT NULL UNIQUE,
                email VARCHAR(150) NOT NULL UNIQUE,
                password_hash VARCHAR(512) NOT NULL,
                rating INT DEFAULT 1200,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS email_verifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL UNIQUE,
                otp VARCHAR(6),
                is_verified BOOLEAN DEFAULT FALSE,
                expires_at DATETIME,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INT AUTO_INCREMENT PRIMARY KEY,
                white_username VARCHAR(80) NOT NULL,
                black_username VARCHAR(80) NOT NULL,
                white_user_id INT,
                black_user_id INT,
                result VARCHAR(10) NOT NULL,
                reason VARCHAR(20) NOT NULL,
                move_count INT DEFAULT 0,
                played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (white_user_id) REFERENCES users(id) ON DELETE SET NULL,
                FOREIGN KEY (black_user_id) REFERENCES users(id) ON DELETE SET NULL
            )
        """)
        db.close()
