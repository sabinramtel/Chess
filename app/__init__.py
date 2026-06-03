from flask import Flask
from app.routes.auth import AuthRoutes
import config


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.secret_key = config.SECRET_KEY

    with app.app_context():
        from app.models.database import DatabaseManager
        if not DatabaseManager.create_tables():
            print("Warning: database initialization failed. Check DB credentials in .env or environment variables.")
            app.config["DB_INITIALIZED"] = False
        else:
            app.config["DB_INITIALIZED"] = True

    auth_routes = AuthRoutes()
    app.register_blueprint(auth_routes.register())
    return app
