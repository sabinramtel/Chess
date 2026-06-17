from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import pymysql
import os

from config import Config

load_dotenv()

db = SQLAlchemy()


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
    CORS(app)

    from app.routes.auth_routes import auth_bp
    from app.routes.settings_routes import settings_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(settings_bp)

    with app.app_context():
        from app.models.settings import UserSettings          # noqa
        from app.models.email_verification import EmailVerification  # noqa
        db.create_all()

    return app
