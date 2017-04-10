# -*- coding: utf-8 -*-

# Python
from time import strftime, gmtime

# Python libs
from flask import Flask
from flask_oauth import OAuth
from flask_login import LoginManager
from flask_pymongo import PyMongo


app = Flask(__name__)
app.config.from_object('config')

mongo = PyMongo(app)

# Github login
# ------------

oauth = OAuth()
github = oauth.remote_app(
    'github',
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    consumer_key=app.config['GITHUB_AUTH']['app_id'],
    consumer_secret=app.config['GITHUB_AUTH']['app_secret'],
    request_token_params={'scope': app.config['GITHUB_AUTH']['scope']}
)

# Login manager
# -------------

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'


# Context Processors
# ------------------

@app.context_processor
def utility_processor():
    def format_duration(s):
        return strftime('%H:%M:%S', gmtime(s))

    def format_price(amount, currency='$'):
        return '{1} {0:.2f}'.format(amount, currency)

    return dict(format_duration=format_duration, format_price=format_price)


from controllers import *  # noqa : disable pep8 on this line
from models import *  # noqa : disable pep8 on this line


if __name__ == '__main__':
    port = app.config['PORT']
    debug = app.config['DEBUG']

    app.run(debug=debug, port=port, threaded=True, use_reloader=True)
