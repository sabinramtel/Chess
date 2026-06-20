import re

with open('app/routes/settings_routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('from app.controllers.settings_controller import SettingsController', 
                          'from app.controllers.settings_controller import SettingsController\n\nsettings_controller = SettingsController()')

content = re.sub(r'SettingsController\.([a-zA-Z_]+)\(', r'settings_controller.\1(', content)

with open('app/routes/settings_routes.py', 'w', encoding='utf-8') as f:
    f.write(content)
