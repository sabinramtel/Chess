from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_cors import CORS
from dotenv import load_dotenv
import pymysql
import os

from config import Config

load_dotenv()

db = SQLAlchemy()
socketio = SocketIO()


def create_database_if_not_exists():
    user     = os.getenv('MYSQL_USER', 'root')
    password = os.getenv('MYSQL_PASSWORD', 'Nima.d.l.10@')
    host     = os.getenv('MYSQL_HOST', 'localhost')
    db_name  = os.getenv('MYSQL_DB', 'chess_db')

    conn = pymysql.connect(host=host, user=user, password=password)
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    conn.commit()
    cursor.close()
    conn.close()


def migrate_users_table():
    """Forcibly adds the 'rating' column to the users table if it's missing."""
    print("Checking for 'rating' column in users table...")
    try:
        # Direct attempt to add the column
        db.session.execute(db.text("ALTER TABLE users ADD COLUMN rating INT DEFAULT 1200"))
        db.session.commit()
        print("SUCCESS: 'rating' column added to users table.")
    except Exception as e:
        err_msg = str(e).lower()
        if "duplicate column" in err_msg or "1060" in err_msg:
            print("INFO: 'rating' column already exists. Skipping migration.")
        else:
            print(f"ERROR: Migration failed with unexpected error: {e}")
    finally:
        # Ensure session is clean
        db.session.rollback()


def create_app():
    # Only try to create database locally if not using a full connection string
    if not os.getenv('DATABASE_URL'):
        try:
            create_database_if_not_exists()
        except Exception as e:
            print(f"Skipping local DB creation: {e}")

    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config.from_object(Config)

    try:
        db.init_app(app)
        socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')
        CORS(app)

        from app.routes.auth_routes import auth_bp
        from app.routes.settings_routes import settings_bp
        from app.routes.game_routes import game_bp
        from app.routes.puzzle_routes import puzzle_bp
        app.register_blueprint(auth_bp)
        app.register_blueprint(settings_bp)
        app.register_blueprint(game_bp)
        app.register_blueprint(puzzle_bp)

        with app.app_context():
            # Register socket handlers by importing the controller
            from app.controllers import socket_controller
            from app.models.settings_model import UserSettings                  # noqa
            from app.models.email_verification_model import EmailVerification   # noqa
            from app.models.puzzle_model import Puzzle                          # noqa
            from app.models.puzzle_stats_model import UserPuzzleStats           # noqa
            from app.models.puzzle_attempt_model import PuzzleAttempt           # noqa
            
            # Create PyMySQL tables first (users, email_verifications)
            from app.models.database import Database
            try:
                Database.create_tables()
            except Exception as e:
                print(f"Warning: PyMySQL schema creation failed: {e}")

            # Create remaining SQLAlchemy tables
            db.create_all()
            
    except Exception as e:
        print(f"CRITICAL ERROR during app initialization: {e}")
        # We still return the app so the server can at least start and we can see logs

    @app.errorhandler(404)
    def page_not_found(e):
        from flask import render_template
        return render_template('404.html'), 404

    return app

