import re

with open('app/controllers/settings_controller.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('user = User.query.get(user_id)',
                          """user_data = User().find_by('id', user_id)\n        user = User.from_db(user_data) if user_data else None""")

content = content.replace('User.query.filter_by(username=new_username).first()',
                          'User().find_by("username", new_username)')

content = content.replace('User.query.filter_by(email=new_email).first()',
                          'User().find_by("email", new_email)')

with open('app/controllers/settings_controller.py', 'w', encoding='utf-8') as f:
    f.write(content)
