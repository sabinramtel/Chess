import os
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "random-secret-key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Check for DATABASE_URL (common in cloud deployments like Render/Railway)
    uri = os.environ.get("DATABASE_URL")
    if uri:
        if uri.startswith("postgres://"):
            uri = uri.replace("postgres://", "postgresql://", 1)
        elif uri.startswith("mysql://"):
            uri = uri.replace("mysql://", "mysql+pymysql://", 1)
        SQLALCHEMY_DATABASE_URI = uri
    else:
        # Fallback to individual MySQL environment variables
        MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
        MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'Nima.d.l.10@')
        MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
        MYSQL_DB = os.environ.get('MYSQL_DB', 'chess_db')
        
        # URL encode password to handle special characters like '@'
        encoded_password = urllib.parse.quote_plus(MYSQL_PASSWORD)
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{encoded_password}@{MYSQL_HOST}/{MYSQL_DB}"
