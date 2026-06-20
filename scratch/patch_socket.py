import re

with open('app/controllers/socket_controller.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('from app.controllers.game_controller import GameController', 
                          'from app.controllers.game_controller import GameController\n\ngame_controller = GameController()')

content = re.sub(r'GameController\.([a-zA-Z_]+)\(', r'game_controller.\1(', content)

with open('app/controllers/socket_controller.py', 'w', encoding='utf-8') as f:
    f.write(content)
