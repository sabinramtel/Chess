import mysql.connector
from mysql.connector import Error
import config


class DatabaseManager:
    def __init__(self):
        self._config = {
            'host': config.MYSQL_HOST,
            'user': config.MYSQL_USER,
            'password': config.MYSQL_PASSWORD,
            'database': config.MYSQL_DATABASE,
            'charset': 'utf8mb4',
        }

    def get_connection(self):
        return mysql.connector.connect(**self._config)

    def is_healthy(self):
        try:
            conn = self.get_connection()
            conn.close()
            return True, 'connected'
        except Error as e:
            return False, str(e)

    @staticmethod
    def create_tables():
        manager = DatabaseManager()
        try:
            conn = manager.get_connection()
        except Error as e:
            print(f"Database connection failed: {e}")
            return False

        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                username VARCHAR(60) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
