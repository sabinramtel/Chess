import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY", "random-secret-key")
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///chess.db")

# Keep legacy individual MySQL settings as fallbacks
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "Nima.d.l.10@")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "classDB")
