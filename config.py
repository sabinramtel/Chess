import os
import urllib.parse
from dotenv import load_dotenv

load_dotenv()


def _build_mysql_uri():
    """
    Resolve the MySQL connection URI in priority order:
      1. DATABASE_URL  – manually set on Render/Railway
      2. MYSQL_URL     – Railway sometimes sets this name
      3. Individual Railway vars: MYSQLHOST, MYSQLUSER, MYSQLPASSWORD,
                                  MYSQLDATABASE, MYSQLPORT
      4. Individual generic vars: MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD,
                                  MYSQL_DB  (local dev fallback)
    """
    # ── 1 & 2: Full URL ──────────────────────────────────────────────────────
    url = os.environ.get("DATABASE_URL") or os.environ.get("MYSQL_URL")
    if url:
        # Normalise driver prefix → mysql+pymysql://
        if url.startswith("mysql://"):
            url = url.replace("mysql://", "mysql+pymysql://", 1)
        elif url.startswith("mysql+mysqlconnector://"):
            url = url.replace("mysql+mysqlconnector://", "mysql+pymysql://", 1)
        # Strip any postgres URL accidentally set (failsafe)
        if url.startswith("postgres"):
            raise ValueError(
                "DATABASE_URL looks like a PostgreSQL URL but this app uses MySQL. "
                "Please set the correct MySQL URL."
            )
        return url

    # ── 3: Railway individual vars (no underscore) ───────────────────────────
    railway_host = os.environ.get("MYSQLHOST")
    if railway_host:
        user     = os.environ.get("MYSQLUSER", "root")
        password = os.environ.get("MYSQLPASSWORD", "")
        database = os.environ.get("MYSQLDATABASE", "railway")
        port     = os.environ.get("MYSQLPORT", "3306")
        encoded  = urllib.parse.quote_plus(password)
        return f"mysql+pymysql://{user}:{encoded}@{railway_host}:{port}/{database}"

    # ── 4: Generic / local-dev vars ──────────────────────────────────────────
    user     = os.environ.get("MYSQL_USER",     "root")
    password = os.environ.get("MYSQL_PASSWORD", "Nima.d.l.10@")
    host     = os.environ.get("MYSQL_HOST",     "localhost")
    db       = os.environ.get("MYSQL_DB",       "chess_db")
    port     = os.environ.get("MYSQL_PORT",     "3306")
    encoded  = urllib.parse.quote_plus(password)
    return f"mysql+pymysql://{user}:{encoded}@{host}:{port}/{db}"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = _build_mysql_uri()
