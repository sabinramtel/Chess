import os
os.environ['MYSQL_USER'] = 'root'
os.environ['MYSQL_PASSWORD'] = 'Nima.d.l.10@'
os.environ['MYSQL_HOST'] = 'localhost'
os.environ['MYSQL_DB'] = 'chess_db'

try:
    from app import create_app
    app = create_app()
    with app.app_context():
        from app.models.user_model import User
        print("User table access success")
    print("App initialized successfully")
except Exception as e:
    print(f"Failed: {e}")
