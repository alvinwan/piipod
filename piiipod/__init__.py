from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import urlparse
from .logger import logger
import functools
import flask_login
from .config import config, secret_key, debug, whitelist, googleclientID, port

logger.debug('Running in DEBUG mode.' if debug else
      'Running in PRODUCTION mode.')

print('Google Client ID: %s' % googleclientID if googleclientID else
      'No Google Client ID found.')

# Flask app
app = Flask(__name__)

# Configuration for mySQL database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{USERNAME}:{PASSWORD}@{HOST}/{DATABASE}'.format(**config)
db = SQLAlchemy(app)

# Configuration for login sessions
app.secret_key = secret_key
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

# Configuration for app views
from .public.views import public
from .dashboard.views import dashboard
from .group.views import group
from .event.views import event

blueprints = (public, dashboard, group, event)
for blueprint in blueprints:
    logger.debug('Registering blueprint "%s"' % blueprint.name)
    app.register_blueprint(blueprint)


def hook(f):
    pre = 'pre_%s' % f.__name__
    post = 'post_%s' % f.__name__
    @functools.wraps(f)
    def wrap(self, *args, **kwargs):
        pref, postf = getattr(self, pre, None), getattr(self, post, None)
        if callable(pref):
            pref(self, *args, **kwargs)
        rv = f(*args, **kwargs)
        if callable(postf):
            postf(self, *args, **kwargs)
        return rv
    return wrap
