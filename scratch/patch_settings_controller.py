import re

with open('app/controllers/settings_controller.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('class SettingsController:', 
                          'from app.controllers.base_controller import BaseController\n\nclass SettingsController(BaseController):')
content = content.replace('    @staticmethod\n    def', '    def')
content = re.sub(r'def ([a-zA-Z_]+)\((?!self)', r'def \1(self, ' , content)

with open('app/controllers/settings_controller.py', 'w', encoding='utf-8') as f:
    f.write(content)
