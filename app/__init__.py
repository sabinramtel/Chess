from flask import Flask
from flask_socketio import SocketIO
import os

# Create the SocketIO instance at module level so sockets.py can import it
socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet")


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

    # Register HTTP blueprints
    from app.routes.auth import AuthRoutes
    from app.routes.game import game_bp

    auth_routes = AuthRoutes()
    app.register_blueprint(auth_routes.register())
    app.register_blueprint(game_bp)

    # Attach Socket.IO to app and register all socket event handlers
    socketio.init_app(app)
    from app import sockets  # noqa: F401 — registers event handlers as a side-effect

    # Initialize database tables
    with app.app_context():
        try:
            from app.models.database import DatabaseManager
            DatabaseManager.create_tables()
        except Exception as e:
            app.logger.warning(f"Database table creation failed: {e}")

    return app