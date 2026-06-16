import os
import sqlite3
from urllib.parse import urlparse
import config

# Cursor wrapper for SQLite to make it compatible with mysql-connector-python API
class SQLiteCursorWrapper:
    def __init__(self, cursor, is_dict=False):
        self.cursor = cursor
        self.is_dict = is_dict

    def execute(self, query, params=None):
        # Translate mysql parameter placeholder (%s) to sqlite placeholder (?)
        if params:
            query = query.replace('%s', '?')
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        if self.is_dict and isinstance(row, sqlite3.Row):
            return dict(row)
        return row

    def fetchall(self):
        rows = self.cursor.fetchall()
        if self.is_dict:
            return [dict(row) if isinstance(row, sqlite3.Row) else row for row in rows]
        return rows

    @property
    def lastrowid(self):
        return self.cursor.lastrowid

    def close(self):
        self.cursor.close()


class SQLiteConnectionWrapper:
    def __init__(self, conn):
        self.conn = conn

    def cursor(self, dictionary=False):
        if dictionary:
            self.conn.row_factory = sqlite3.Row
        else:
            self.conn.row_factory = None
        return SQLiteCursorWrapper(self.conn.cursor(), is_dict=dictionary)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()


# Cursor wrapper for PyMySQL to make it compatible with mysql-connector-python API
class PyMySQLCursorWrapper:
    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query, params=None):
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    @property
    def lastrowid(self):
        return self.cursor.lastrowid

    def close(self):
        self.cursor.close()


class PyMySQLConnectionWrapper:
    def __init__(self, conn):
        self.conn = conn

    def cursor(self, dictionary=False):
        if dictionary:
            import pymysql.cursors
            return PyMySQLCursorWrapper(self.conn.cursor(pymysql.cursors.DictCursor))
        else:
            return PyMySQLCursorWrapper(self.conn.cursor())

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()


class DatabaseManager:
    def __init__(self):
        self.db_uri = getattr(config, 'SQLALCHEMY_DATABASE_URI', 'sqlite:///chess.db')

    def get_connection(self):
        if self.db_uri.startswith('sqlite:'):
            # Parse sqlite path. e.g. sqlite:///chess.db
            db_path = self.db_uri.split('sqlite:///', 1)[1]
            if not db_path:
                db_path = 'chess.db'
            # Ensure parent directories exist for the sqlite file
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
            conn = sqlite3.connect(db_path, check_same_thread=False)
            return SQLiteConnectionWrapper(conn)

        # Handle MySQL URLs
        uri = self.db_uri
        if uri.startswith('mysql+pymysql://'):
            uri = uri.replace('mysql+pymysql://', 'mysql://', 1)
        
        parsed = urlparse(uri)
        db_config = {
            'host': parsed.hostname or 'localhost',
            'user': parsed.username or 'root',
            'password': parsed.password or '',
            'database': parsed.path.lstrip('/') if parsed.path else 'classDB',
        }
        if parsed.port:
            db_config['port'] = parsed.port

        # Try pymysql first (since it is installed/configured for production)
        try:
            import pymysql
            conn = pymysql.connect(**db_config)
            return PyMySQLConnectionWrapper(conn)
        except ImportError:
            # Fallback to mysql.connector
            import mysql.connector
            db_config['charset'] = 'utf8mb4'
            conn = mysql.connector.connect(**db_config)
            return conn

    def is_healthy(self):
        try:
            conn = self.get_connection()
            conn.close()
            return True, 'connected'
        except Exception as e:
            return False, str(e)

    @staticmethod
    def create_tables():
        manager = DatabaseManager()
        try:
            conn = manager.get_connection()
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False

        cursor = conn.cursor()
        
        # Adjust table creation query depending on driver
        if manager.db_uri.startswith('sqlite:'):
            create_query = """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR(255) NOT NULL UNIQUE,
                username VARCHAR(60) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        else:
            create_query = """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                username VARCHAR(60) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
        try:
            cursor.execute(create_query)
            conn.commit()
        except Exception as e:
            print(f"Failed to create table users: {e}")
            cursor.close()
            conn.close()
            return False
            
        cursor.close()
        conn.close()
        return True
