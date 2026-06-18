import os
import re
from dotenv import load_dotenv

load_dotenv()

class Config:
<<<<<<< HEAD
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

# Legacy fallbacks (optional)
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "Nima.d.l.10@")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "classDB")
=======
    SECRET_KEY = os.environ.get('SECRET_KEY', 'random-secret-key')

    MYSQL_USER     = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_HOST     = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_DB       = os.environ.get('MYSQL_DB', 'chess_db')

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
>>>>>>> 6a44969e475065cff35e9a9e59f02c809efec79b
