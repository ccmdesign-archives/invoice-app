# -*- coding: utf-8 -*-

# Python Core.
from os import getenv
from os.path import join, dirname, isfile

# Python Libs.
from dotenv import read_dotenv


_ENV_FILE = join(dirname(__file__), '.env')


if isfile(_ENV_FILE) and not getenv('DATABASE_URL'):
    read_dotenv(_ENV_FILE)

GITHUB_AUTH = {
    'app_id': getenv('GITHUB_APP_ID', ''),
    'app_secret': getenv('GITHUB_APP_SECRET', ''),
    'scope': ['user:email']
}

PORT = int(getenv('APP_PORT', 5000))
DEBUG = eval(getenv('DEBUG', 'True').title())
SECRET_KEY = getenv('SECRET_KEY', 'invoice-never-guess')
ASSETS_DEBUG = DEBUG
WTF_CSRF_ENABLED = eval(getenv('WTF_CSRF_ENABLED', 'True').title())
SQLALCHEMY_DATABASE_URI = getenv('DATABASE_URL', '')
