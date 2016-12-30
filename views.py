# -*- coding: utf-8 -*-

# Python
from csv import reader
from time import strptime
from json import dumps, loads
from decimal import Decimal
from datetime import date, timedelta

# Libs
from flask import g, session, flash
from flask import abort, render_template, request, Response, url_for, redirect
from slugify import Slugify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename
from sqlalchemy.sql.expression import func

# Invoice
from app import app, github, login_manager, db
from models import Invoice, Client, Company, User, Service, Tax, Timesheet


_MAX = 3
_SLUGY = Slugify(to_lower=True, separator='_')
_ALLOWED_EXT = ['csv']


# Login manager
# -------------

@app.route('/github_login')
def github_login():
    url = url_for('github_authorized', _external=True)

    return github.authorize(callback=url)


@github.tokengetter
def get_github_token():
    return session.get('github_token')


@app.route('/github_authorized')
@github.authorized_handler
def github_authorized(resp):
    if not resp or 'access_token' not in resp:
        flash('Login error: %s' % resp, 'error')

        return redirect(url_for('index'))

    else:
        session['github_token'] = (resp['access_token'], '')
        gh_data = github.get('user').data
        ghid = 'gh-%s' % gh_data['id']
        user = User.query.get(ghid)

        if user is None:
            user = User(id=ghid)

        # email
        user.email = gh_data.get('email', '')

        # name
        user.name = gh_data.get('name', '')

        # gh login
        user.gh_login = gh_data.get('login', '')

        db.session.add(user)
        db.session.commit()

        login_user(user, remember=True)

        return redirect(url_for('home'))


@app.route('/logout')
def logout():
    logout_user()

    if 'github_token' in session:
        session.pop('github_token')

    return redirect(url_for('index'))


# Invoice
# -------

@login_manager.user_loader
def load_user(id):
    return User.query.get(id)


@app.before_request
def before_request():
    g.user = current_user

    if g.user and g.user.is_authenticated:
        g.user.paid_invoices = 0
        g.user.open_invoices = 0

        for invoice in g.user.invoices:
            if invoice.paid:
                g.user.paid_invoices += 1

            else:
                g.user.open_invoices += 1


@app.route('/ajax_ok/')
@login_required
def ajax_ok():
    return Response('ok')


@app.route('/')
def index():
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('home'))

    else:
        return render_template('index.html')


@app.route('/unlogged_invoice', methods=['GET'])
def unlogged_invoice():
    ctx = {'invoice': {}, 'today': date.today()}

    return render_template('unlogged_invoice.html', **ctx)


@app.route('/home', methods=['GET'])
@login_required
def home():
    return render_template('home.html')


@app.route('/toggle_invoice_status/<invoice_id>', methods=['GET', 'POST'])
@login_required
def toggle_invoice_status(invoice_id):
    inv = Invoice.query.get(invoice_id)

    if inv:
        if request.method == 'GET':
            fun = lambda x: render_template('home_table_row.html', invoice=x)
            dic = {'paid': [], 'open': []}
            mim = 'application/json'

            for invoice in g.user.invoices:
                if invoice.paid:
                    dic['paid'].append(fun(invoice).strip())

                else:
                    dic['open'].append(fun(invoice).strip())

            return Response(response=dumps(dic), status=200, mimetype=mim)

        elif request.method == 'POST':
            url = url_for('toggle_invoice_status', invoice_id=inv.id)
            form = loads(request.form['data'])

            inv.paid = form['paid']

            db.session.commit()

            return redirect(url)

        return abort(400)

    return abort(404)


@app.route('/invoice', methods=['POST'])
@login_required
def create_invoice():
    inv = Invoice(user_id=g.user.id)
    com = g.user.companies[0] if g.user.companies else {}
    qry = db.session.query(func.count(Invoice.id)).filter_by(user_id=g.user.id)

    inv.tag_number = '%s%02d' % (date.today().year, qry.scalar())

    if com:
        inv.company = com.id
        inv.currency = com.currency

    db.session.add(inv)
    db.session.commit()

    return redirect(url_for('open_invoice', invoice_id=inv.id))


@app.route('/invoice/<invoice_id>', methods=['GET'])
@login_required
def open_invoice(invoice_id):
    inv = Invoice.query.get(invoice_id)

    if inv:
        ctx = {}

        ctx['taxes'] = {}
        ctx['client'] = Client.query.get(inv.client) if inv.client else {}
        ctx['invoice'] = inv
        ctx['company'] = Company.query.get(inv.company) if inv.company else {}
        ctx['services'] = Service.query.filter(Service.invoice == inv.id)
        ctx['timesheets'] = Timesheet.query.filter(Timesheet.invoice == inv.id)

        if inv.taxes:
            ctx['taxes'] = Tax.query.filter(Tax.invoice == inv.id)

        elif inv.company:
            ctx['taxes'] = Tax.query.filter(Tax.company == inv.company)

        return render_template('invoice.html', **ctx)

    return abort(404)


@app.route('/edit_invoice/<invoice_id>', methods=['POST'])
@login_required
def edit_invoice(invoice_id):
    inv = Invoice.query.get(invoice_id)

    if inv and request.method == 'POST':
        form = loads(request.form['data'])

        inv.tag_number = form['tag_number']
        inv.service_name = form['service_name']
        inv.service_description = form['service_description']

        db.session.commit()

        return redirect(url_for('ajax_ok'))

    return abort(404)


@app.route('/edit_invoice_client/<invoice_id>', methods=['GET', 'POST'])
@login_required
def edit_invoice_client(invoice_id):
    inv = Invoice.query.get(invoice_id)

    if inv:
        if request.method == 'GET' and inv.client:
            ctx = {}

            ctx['client'] = Client.query.get(inv.client)
            ctx['invoice'] = inv

            return render_template('invoice_client.html', **ctx)

        elif request.method == 'POST':
            form = request.form
            new = False
            cli = None

            if not inv.client or not form['id']:
                cli = Client(user_id=g.user.id)
                new = True

            elif inv.client != form['id']:
                cli = Client.query.get(form['id'])

            else:
                cli = Client.query.get(inv.client)

            if form['name'] != cli.name:
                cli.name = form['name']

            if form['email'] != cli.email:
                cli.email = form['email']

            if form['phone'] != cli.phone:
                cli.phone = form['phone']

            if form['address'] != cli.address:
                cli.address = form['address']

            if form['contact'] != cli.contact:
                cli.contact = form['contact']

            if form['vendor_number'] != cli.vendor_number:
                cli.vendor_number = form['vendor_number']

            if new:
                db.session.add(cli)
                db.session.flush()

            inv.client = cli.id

            db.session.commit()

            return redirect(url_for('edit_invoice_client', invoice_id=inv.id))

        return abort(400)

    return abort(404)


@app.route('/edit_invoice_company/<invoice_id>', methods=['GET', 'POST'])
@login_required
def edit_invoice_company(invoice_id):
    inv = Invoice.query.get(invoice_id)

    if inv:
        if request.method == 'GET' and inv.company:
            ctx = {}

            ctx['company'] = Company.query.get(inv.company)
            ctx['invoice'] = inv

            if inv.taxes:
                ctx['taxes'] = Tax.query.filter(Tax.invoice == inv.id)

            else:
                ctx['taxes'] = Tax.query.filter(Tax.company == inv.company)

            return render_template('invoice_company.html', **ctx)

        elif request.method == 'POST':
            form = request.form
            new = False
            com = None

            if not inv.company or not form['id']:
                com = Company(user_id=g.user.id)
                new = True

            elif inv.company != form['id']:
                com = Company.query.get(form['id'])

            else:
                com = Company.query.get(inv.company)

            if form['name'] != com.name:
                com.name = form['name']

            if form['email'] != com.email:
                com.email = form['email']

            if form['phone'] != com.phone:
                com.phone = form['phone']

            if form['address'] != com.address:
                com.address = form['address']

            if form['contact'] != com.contact:
                com.contact = form['contact']

            if form['banking_info'] != com.banking_info:
                com.banking_info = form['banking_info']

            if new:
                db.session.add(com)
                db.session.flush()

            inv.company = com.id

            db.session.commit()

            return redirect(url_for('edit_invoice_company', invoice_id=inv.id))

        return abort(400)

    return abort(404)


@app.route('/create_invoice_tax/<invoice_id>', methods=['GET', 'POST'])
@login_required
def create_invoice_tax(invoice_id):
    inv = Invoice.query.get(invoice_id)

    if inv:
        if request.method == 'GET':
            ctx = {}

            ctx['invoice'] = inv
            ctx['taxes'] = Tax.query.filter(Tax.invoice == inv.id)

            return render_template('invoice_tax.html', **ctx)

        elif request.method == 'POST':
            form = loads(request.form['data'])
            tax = Tax(invoice=invoice_id)

            tax.tax = form['tax']
            tax.name = form['name']
            tax.number = form['number']

            db.session.add(tax)
            db.session.commit()

            return redirect(url_for('create_invoice_tax', invoice_id=inv.id))

        return abort(400)

    return abort(404)


@app.route('/edit_invoice_tax/<invoice_id>', methods=['GET', 'POST'])
@login_required
def edit_invoice_tax(invoice_id):
    inv = Invoice.query.get(invoice_id)

    if inv:
        if request.method == 'GET':
            ctx = {}

            ctx['invoice'] = inv
            ctx['taxes'] = Tax.query.filter(Tax.invoice == inv.id)

            return render_template('invoice_tax.html', **ctx)

        elif request.method == 'POST':
            form = loads(request.form['data'])
            tax = Tax.query.get(form['id'])

            tax.tax = form['tax']
            tax.name = form['name']
            tax.number = form['number']

            db.session.commit()

            return redirect(url_for('edit_invoice_tax', invoice_id=inv.id))

        return abort(400)

    return abort(404)


@login_required
@app.route('/upload_timesheet/<invoice_id>', methods=['GET', 'POST'])
def upload_timesheet(invoice_id):
    def allowed_file(file):
        return '.' in file and file.rsplit('.', 1)[1] in _ALLOWED_EXT

    i = Invoice.query.get(invoice_id)

    if i:
        if request.method == 'GET':
            c = {}

            c['invoice'] = i
            c['company'] = Company.query.get(i.company) if i.company else {}
            c['timesheets'] = Timesheet.query.filter(Timesheet.invoice == i.id)

            return render_template('invoice_timesheet.html', **c)

        elif request.method == 'POST' and 'file' in request.files:
            file = request.files['file']
            name = secure_filename(file.filename).strip() if file else ''

            if name and allowed_file(name):
                for idx, row in enumerate(reader(file)):
                    if idx > 0 and len(row) == 14:
                        tms = Timesheet(invoice=invoice_id)
                        fun = lambda x: int(x) if x.strip() else 0
                        lst = list(map(fun, row[7].split('-')))

                        if len(lst) == 3 and all(lst):
                            tms.date = date(*lst)

                        if row[11].strip():
                            aux = strptime(row[11], '%H:%M:%S')
                            kwa = {}

                            kwa['hours'] = aux.tm_hour
                            kwa['minutes'] = aux.tm_min
                            kwa['seconds'] = aux.tm_sec

                            tms.duration = timedelta(**kwa).total_seconds()

                        tms.amount = Decimal(row[13] if row[13] else 0)
                        tms.description = row[5]

                        i.total += tms.amount

                        db.session.add(tms)

                db.session.commit()

                return redirect(url_for('upload_timesheet', invoice_id=i.id))

        return abort(400)

    return abort(404)


@app.route('/get_companies/<invoice_id>', methods=['GET'])
@login_required
def get_companies(invoice_id):
    inv = Invoice.query.get(invoice_id)
    txt = request.args.get('q').strip()

    if inv:
        mim = 'application/json'
        res = {'query': txt, 'suggestions': []}
        qry = Company.query.filter(
            Company.user_id == g.user.id,
            Company.name.ilike('%' + txt + '%')
        ).limit(_MAX)

        for com in qry.all():
            ctx = {}
            dic = {}

            ctx['company'] = com
            ctx['invoice'] = inv

            if inv.taxes:
                ctx['taxes'] = Tax.query.filter(Tax.invoice == inv.id)

            else:
                ctx['taxes'] = Tax.query.filter(Tax.company == inv.company)

            dic['value'] = com.name
            dic['data'] = render_template('invoice_company.html', **ctx)

            res['suggestions'].append(dic)

        return Response(response=dumps(res), status=200, mimetype=mim)

    return abort(404)


@login_required
@app.route('/get_clients/<invoice_id>', methods=['GET'])
def get_clients(invoice_id):
    inv = Invoice.query.get(invoice_id)
    txt = request.args.get('q').strip()

    if inv:
        mim = 'application/json'
        res = {'query': txt, 'suggestions': []}
        qry = Client.query.filter(
            Client.user_id == g.user.id,
            Client.name.ilike('%' + txt + '%')
        ).limit(_MAX)

        for cli in qry.all():
            ctx = {}
            dic = {}

            ctx['client'] = cli
            ctx['invoice'] = inv

            dic['value'] = cli.name
            dic['data'] = render_template('invoice_client.html', **ctx)

            res['suggestions'].append(dic)

        return Response(response=dumps(res), status=200, mimetype=mim)

    return abort(404)


@login_required
@app.route('/download_invoice/<invoice_id>', methods=['GET'])
def download_invoice(invoice_id):
    inv = Invoice.query.get(invoice_id)

    if inv:
        ctx = {}

        ctx['taxes'] = {}
        ctx['client'] = Client.query.get(inv.client) if inv.client else {}
        ctx['invoice'] = inv
        ctx['company'] = Company.query.get(inv.company) if inv.company else {}
        ctx['services'] = Service.query.filter(Service.invoice == inv.id)
        ctx['timesheets'] = Timesheet.query.filter(Timesheet.invoice == inv.id)

        if inv.taxes:
            ctx['taxes'] = Tax.query.filter(Tax.invoice == inv.id)

        elif inv.company:
            ctx['taxes'] = Tax.query.filter(Tax.company == inv.company)

        # return render_pdf(url_for('open_invoice', invoice_id=inv.id))
        return render_pdf(HTML(string=render_template('print.html', **ctx)))


# Luke criando Views
@app.route('/clients')
def clients():
  return render_template('clients.html')

