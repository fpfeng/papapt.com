import os
from papapt import create_app
from flask_script import Manager, Shell

app = create_app(os.getenv('FLKCONF') or 'test')
manager = Manager(app)
if __name__ == '__main__':
    manager.run()