import os
from . import create_app, celery


app = create_app(os.getenv('FLASK_CONFIG') or 'product')
app.app_context().push()
