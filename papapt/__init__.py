from flask import Flask
from celery import Celery
from flask_bootstrap import Bootstrap, WebCDN
from flask_wtf.csrf import CsrfProtect
from werkzeug.utils import import_string
from config import config, Config
from models import db


celery = Celery(__name__, broker=Config.CELERY_BROKER_URL)
bootstrap = Bootstrap()
csrf = CsrfProtect()

blueprints = [
            'papapt.views.home:home',
            'papapt.views.search:search',
            'papapt.views.rating_website:rating',
            'papapt.views.timeline:timeline',
            'papapt.views.schedule:ustv',
            'papapt.views.top:top',
            'papapt.views.errors:error',
            ]


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    bootstrap.init_app(app)
    app.extensions['bootstrap']['cdns']['jquery'] = \
        WebCDN('//cdn.bootcss.com/jquery/2.2.4/')
    app.extensions['bootstrap']['cdns']['bootstrap'] = \
        WebCDN('//cdn.bootcss.com/bootstrap/3.3.6/')
    db.init_app(app)
    csrf.init_app(app)
    celery.conf.update(app.config)

    for bp_path in blueprints:
        bp = import_string(bp_path)
        app.register_blueprint(bp)

    return app
