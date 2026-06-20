import re

with open('app/controllers/game_controller.py', 'r') as f:
    content = f.read()

content = content.replace('    @staticmethod\n    def', '    def')
content = re.sub(r'def ([a-zA-Z_]+)\((?!self)', r'def \1(self, ' , content)

with open('app/controllers/game_controller.py', 'w') as f:
    f.write(content)
