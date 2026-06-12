from flask import Flask
from app.models.database import db
import os

def create_app():
    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///chess.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

    db.init_app(app)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.game import game_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(game_bp)
    
    with app.app_context():
        db.create_all()
    
    return app