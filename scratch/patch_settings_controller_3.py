import re

with open('app/controllers/settings_controller.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "s.bio = data.get('bio', s.bio)\n        db.session.commit()",
    "s.bio = data.get('bio', s.bio)\n        user.update(user.id)\n        db.session.commit()"
)

content = content.replace(
    "user.set_password(new_pw)\n        db.session.commit()",
    "user.set_password(new_pw)\n        user.update(user.id, update_password=True)\n        db.session.commit()"
)

with open('app/controllers/settings_controller.py', 'w', encoding='utf-8') as f:
    f.write(content)
