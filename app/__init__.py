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
    password = os.getenv('MYSQL_PASSWORD', '')
    host     = os.getenv('MYSQL_HOST', 'localhost')
    db_name  = os.getenv('MYSQL_DB', 'chess_db')

    conn = pymysql.connect(host=host, user=user, password=password)
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    conn.commit()
    cursor.close()
    conn.close()


def create_app():
    create_database_if_not_exists()

    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config.from_object(Config)

    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins='*', async_mode='threading')
    CORS(app)

    from app.routes.auth_routes import auth_bp
    from app.routes.settings_routes import settings_bp
    from app.routes.game import game_bp
    from app.routes.puzzle_routes import puzzle_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(game_bp)
    app.register_blueprint(puzzle_bp)

    with app.app_context():
        from app.models.settings import UserSettings                  # noqa
        from app.models.email_verification import EmailVerification   # noqa
        from app.models.puzzle import Puzzle                          # noqa
        from app.models.puzzle_stats import UserPuzzleStats           # noqa
        from app.models.puzzle_attempt import PuzzleAttempt           # noqa
        db.create_all()

    import importlib
    importlib.import_module('app.sockets')  # registers all socket event handlers

    return app
