# -*- coding: utf-8 -*-
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

import views  # noqa : disable pep8 on this line
import models  # noqa : disable pep8 on this line
