# -*- coding: utf-8 -*-

GITHUB_CONFIG = {
    'app_id': '7192886d684f830eb27e',
    'app_secret': '09a0f1c1360cb96e67bcc50bc924a9c7347fb14d',
    'scope': ['user:email']
}

WTF_CSRF_ENABLED = True
SECRET_KEY = 'invoice-never-guess'
DEBUG = True

SQLALCHEMY_DATABASE_URI = 'postgresql://guilherme:password@localhost/invoice'
