import os
import re
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "random-secret-key")
    
    # Render/Railway often provide DATABASE_URL starting with 'postgres://' 
    # or 'mysql://'. SQLAlchemy 1.4+ requires 'postgresql://'.
    # For MySQL/Railway, ensure it uses pymysql driver.
    uri = os.environ.get("DATABASE_URL", "sqlite:///chess.db")
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    elif uri and uri.startswith("mysql://"):
        uri = uri.replace("mysql://", "mysql+pymysql://", 1)
    
    SQLALCHEMY_DATABASE_URI = uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False
