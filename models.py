# -*- coding: utf-8 -*-

from app import db
from datetime import date


USER_ID_SIZE = 32


class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total = db.Column(db.DECIMAL(10, 2), default=0.00)
    tag_number = db.Column(db.String(64), default='', unique=True)
    currency = db.Column(db.String(64), default='$')
    paid = db.Column(db.Boolean, default=False)
    date = db.Column(db.Date, default=date.today())
    service_name = db.Column(db.String(64), default='')
    service_description = db.Column(db.String(512), default='')

    user_id = db.Column(db.String(USER_ID_SIZE), db.ForeignKey('user.id'))
    client = db.Column(db.Integer, db.ForeignKey('client.id'), default=None)
    company = db.Column(db.Integer, db.ForeignKey('company.id'), default=None)
    taxes = db.relationship('Tax')
    services = db.relationship('Service')
    timesheets = db.relationship('Timesheet')


class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), default='')
    email = db.Column(db.String(128), default='')
    phone = db.Column(db.String(64), default='')
    address = db.Column(db.String(256), default='')
    contact = db.Column(db.String(128), default='')
    currency = db.Column(db.String(64), default='$')
    vendor_number = db.Column(db.String(64), default='')

    user_id = db.Column(db.String(USER_ID_SIZE), db.ForeignKey('user.id'))
    invoices = db.relationship('Invoice', backref='client_obj')


class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), default='')
    email = db.Column(db.String(128), default='')
    phone = db.Column(db.String(64), default='')
    address = db.Column(db.String(256), default='')
    contact = db.Column(db.String(128), default='')
    currency = db.Column(db.String(64), default='$')
    banking_info = db.Column(db.String(256), default='')

    user_id = db.Column(db.String(USER_ID_SIZE), db.ForeignKey('user.id'))
    taxes = db.relationship('Tax')
    invoices = db.relationship('Invoice')


class Tax(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tax = db.Column(db.String(64), default='')
    name = db.Column(db.String(128), default='')
    number = db.Column(db.String(64), default='')

    company = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    invoice = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=True)


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), default='')
    price = db.Column(db.Integer, default=0)

    invoice = db.Column(db.Integer, db.ForeignKey('invoice.id'))


class User(db.Model):
    id = db.Column(db.String(USER_ID_SIZE), primary_key=True)
    name = db.Column(db.String(128), default='')
    email = db.Column(db.String(128), unique=True)
    gh_login = db.Column(db.String(128), unique=True)

    clients = db.relationship('Client')
    invoices = db.relationship('Invoice')
    companies = db.relationship('Company')

    def __repr__(self):
        return '<User (%r) %r>' % (self.id, self.email)

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)


class Timesheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=date.today())
    amount = db.Column(db.DECIMAL(10, 2), default=0.00)
    duration = db.Column(db.Integer, default=0)
    description = db.Column(db.String(512), default='')

    invoice = db.Column(db.Integer, db.ForeignKey('invoice.id'))
