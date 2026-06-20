import re

with open('app/routes/auth_routes.py', 'r') as f:
    content = f.read()

# Instantiate auth_controller
content = content.replace('from app.controllers.auth_controller import AuthController', 
                          'from app.controllers.auth_controller import AuthController\n\nauth_controller = AuthController()')

# Replace AuthController.method() with auth_controller.method()
content = re.sub(r'AuthController\.([a-zA-Z_]+)\(\)', r'auth_controller.\1()', content)

# Update User.query.filter_by in user_profile
content = content.replace('user = User.query.filter_by(username=username).first()', 
                          'user_data = User().find_by("username", username)\n    user = User.from_db(user_data) if user_data else None')

# Update User.query.get in stats_page
content = content.replace('user = User.query.get(user_id)',
                          'user_data = User().find_by("id", user_id)\n    user = User.from_db(user_data) if user_data else None')

with open('app/routes/auth_routes.py', 'w') as f:
    f.write(content)
print('Done patching')
