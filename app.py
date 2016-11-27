# -*- coding: utf-8 -*-

from time import strftime, gmtime

from flask import Flask
from flask_oauth import OAuth
from flask_login import LoginManager
from flask_assets import Environment, Bundle
from flask_sqlalchemy import SQLAlchemy
from config import GITHUB_CONFIG

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

assets = Environment(app)
assets.url = app.static_url_path
scss = Bundle('sass/custom-styles.scss', filters='pyscss', output='css/styles.css')
assets.register('scss_all', scss)

####################################
#        Github login
####################################
#
oauth = OAuth()
github = oauth.remote_app(
    'github',
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    consumer_key=GITHUB_CONFIG['app_id'],
    consumer_secret=GITHUB_CONFIG['app_secret'],
    request_token_params={'scope': GITHUB_CONFIG['scope']}
)

####################################
#        login manager
####################################
#
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


####################################
#        Context Processors
####################################
#
@app.context_processor
def utility_processor():
    def format_duration(s):
        return strftime('%H:%M:%S', gmtime(s))

    def format_price(amount, currency='$'):
        return '{1} {0:.2f}'.format(amount, currency)

    return dict(format_duration=format_duration, format_price=format_price)


import views  # noqa : disable pep8 on this line
import models  # noqa : disable pep8 on this line
