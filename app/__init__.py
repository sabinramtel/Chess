from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from urllib.parse import quote_plus
from dotenv import load_dotenv
import pymysql
import os

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

    user     = os.getenv('MYSQL_USER', 'root')
    password = quote_plus(os.getenv('MYSQL_PASSWORD', ''))
    host     = os.getenv('MYSQL_HOST', 'localhost')
    db_name  = os.getenv('MYSQL_DB', 'chess_db')

    app = Flask(__name__, static_folder='static', static_url_path='')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{user}:{password}@{host}/{db_name}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    CORS(app)

    from app.routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp)

    with app.app_context():
        db.create_all()

    return app
