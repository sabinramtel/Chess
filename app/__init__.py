from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO
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
    # Only try to create database locally if not using a full connection string
    if not os.getenv('DATABASE_URL'):
        try:
            create_database_if_not_exists()
        except Exception as e:
            print(f"Skipping local DB creation: {e}")

    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config.from_object(Config)

    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    CORS(app)

    from app.routes.auth_routes import auth_bp
    from app.routes.settings_routes import settings_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(settings_bp)

    with app.app_context():
        # Register socket handlers by importing the controller
        from app.controllers import socket_controller
        # from app.models.settings_model import UserSettings          # noqa
        from app.models.email_verification_model import EmailVerification  # noqa
        db.create_all()

    return app
