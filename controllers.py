# -*- coding: utf-8 -*-

# Python
from csv import reader
from time import strptime
from json import dumps, loads
from decimal import Decimal
from datetime import date, timedelta

# Libs
from flask import g, session, flash, jsonify
from flask import abort, render_template, request, Response, url_for, redirect
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename
from sqlalchemy.sql.expression import func

# Invoice
from app import app, github, login_manager, db
from models import Invoice, Client, Company, User, Service, Tax, Timesheet


# Maximun number of suggestions returned by the autocomplete
_MAX_SUGGESTIONS = 5

# Allowed extensions
_ALLOWED_EXT = ['csv']

# Maximun of CSV rows per page
_MAX_ROWS_PER_PAGE = 20


def _ajax_ok():
    return 'ok'


def _get_array_chunks(array, size):
    return (array[pos:pos + size] for pos in xrange(0, len(array), size))


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


@login_manager.user_loader
def load_user(id):
    return User.query.get(id)


# Invoice
# -------

@app.before_request
def before_request():
    g.user = current_user

    if g.user and g.user.is_authenticated:
        g.user.paid_invoices = 0
        g.user.open_invoices = 0
        paid_value = 0
        open_value = 0

        for invoice in g.user.invoices:
            if invoice.paid:
                g.user.paid_invoices += 1
                paid_value += invoice.total_with_taxes

            else:
                g.user.open_invoices += 1
                open_value += invoice.total_with_taxes

        g.user.paid_invoices_value = '{0:.2f}'.format(paid_value)
        g.user.open_invoices_value = '{0:.2f}'.format(open_value)


@app.route('/')
def index():
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('home'))

    else:
        ctx = {'invoice': {}, 'today': date.today()}

        return render_template('unlogged_invoice.html', **ctx)


@app.route('/home', methods=['GET'])
@login_required
def home():
    return render_template('home.html')


@login_required
@app.route('/toggle_invoice_status/<invoice_id>', methods=['GET', 'POST'])
def toggle_invoice_status(invoice_id):
    inv = Invoice.query.get_or_404(invoice_id)

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


@login_required
@app.route('/invoice', methods=['POST'])
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


@login_required
@app.route('/delete_invoice/<invoice_id>', methods=['POST'])
def delete_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)

    db.session.delete(invoice)
    db.session.commit()

    return redirect(url_for('home'))


@login_required
@app.route('/invoice/<invoice_id>', methods=['GET'])
def open_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)

    lst = list(Timesheet.query.filter(Timesheet.invoice == invoice.id))
    ctx = {}

    ctx['invoice'] = invoice
    ctx['client'] = Client.query.get(invoice.client) if invoice.client else {}
    ctx['company'] = Company.query.get(invoice.company) if invoice.company else {}
    ctx['services'] = Service.query.filter(Service.invoice == invoice.id)
    ctx['timesheets'] = _get_array_chunks(lst, _MAX_ROWS_PER_PAGE)

    if invoice.taxes:
        ctx['taxes'] = Tax.query.filter(Tax.invoice == invoice.id)

    elif invoice.company:
        ctx['taxes'] = Tax.query.filter(Tax.company == invoice.company)

    return render_template('invoice.html', **ctx)


@login_required
@app.route('/edit_invoice/<invoice_id>', methods=['POST'])
def edit_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)

    form = loads(request.form['data'])

    invoice.tag_number = form['tag_number']
    invoice.service_name = form['service_name']
    invoice.service_description = form['service_description']

    db.session.commit()

    return _ajax_ok()


@login_required
@app.route('/edit_invoice_client/<invoice_id>', methods=['GET', 'POST'])
def edit_invoice_client(invoice_id):
    inv = Invoice.query.get_or_404(invoice_id)

    if request.method == 'GET' and inv.client:
        ctx = {}

        ctx['client'] = Client.query.get(inv.client)
        ctx['invoice'] = inv

        return render_template('invoice_client.html', **ctx)

    elif request.method == 'POST':
        form = request.form
        new = False
        cli = None

        if not form['id']:
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

        return jsonify(id=cli.id)

    return abort(400)


@login_required
@app.route('/edit_invoice_company/<invoice_id>', methods=['GET', 'POST'])
def edit_invoice_company(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)

    if request.method == 'GET' and invoice.company:
        ctx = {}

        ctx['company'] = Company.query.get(invoice.company)
        ctx['invoice'] = invoice

        if invoice.taxes:
            ctx['taxes'] = Tax.query.filter(Tax.invoice == invoice.id)

        else:
            ctx['taxes'] = Tax.query.filter(Tax.company == invoice.company)

        return render_template('invoice_company.html', **ctx)

    elif request.method == 'POST':
        form = request.form
        new = False
        com = None

        if not form['id']:
            com = Company(user_id=g.user.id)
            new = True

        elif invoice.company != form['id']:
            com = Company.query.get(form['id'])

        else:
            com = Company.query.get(invoice.company)

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

        invoice.company = com.id

        db.session.commit()

        return jsonify(id=com.id)

    return abort(400)


@login_required
@app.route('/create_invoice_tax/<invoice_id>', methods=['GET', 'POST'])
def create_invoice_tax(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)

    if request.method == 'GET':
        resp = {'html': '', 'json': {}}
        ctx = {}

        ctx['invoice'] = invoice
        ctx['taxes'] = Tax.query.filter(Tax.invoice == invoice.id)

        resp['html'] = render_template('invoice_tax.html', **ctx)
        resp['json'] = {'total': '{0:.2f}'.format(invoice.total_with_taxes)}

        return jsonify(resp)

    elif request.method == 'POST':
        form = loads(request.form['data'])
        tax = Tax(invoice=invoice_id)

        tax.tax = form['tax']
        tax.name = form['name']
        tax.number = form['number']

        db.session.add(tax)
        db.session.commit()

        return redirect(url_for('create_invoice_tax', invoice_id=invoice.id))


@login_required
@app.route('/edit_invoice_tax/<invoice_id>', methods=['GET', 'POST'])
def edit_invoice_tax(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)

    if request.method == 'GET':
        resp = {'html': '', 'json': {}}
        ctx = {}

        ctx['invoice'] = invoice
        ctx['taxes'] = Tax.query.filter(Tax.invoice == invoice.id)

        resp['html'] = render_template('invoice_tax.html', **ctx)
        resp['json'] = {'total': '{0:.2f}'.format(invoice.total_with_taxes)}

        return jsonify(resp)

    elif request.method == 'POST':
        form = loads(request.form['data'])
        tax = Tax.query.get(form['id'])

        tax.tax = form['tax']
        tax.name = form['name']
        tax.number = form['number']

        db.session.commit()

        return redirect(url_for('edit_invoice_tax', invoice_id=invoice.id))


@login_required
@app.route('/upload_timesheet/<invoice_id>', methods=['GET', 'POST'])
def upload_timesheet(invoice_id):
    def allowed_file(file):
        return '.' in file and file.rsplit('.', 1)[1] in _ALLOWED_EXT

    invoice = Invoice.query.get_or_404(invoice_id)

    if request.method == 'GET':
        resp = {'html': '', 'json': {}}
        lst = list(Timesheet.query.filter(Timesheet.invoice == invoice.id))
        c = {}

        c['invoice'] = invoice
        c['company'] = Company.query.get(invoice.company) if invoice.company else {}
        c['timesheets'] = _get_array_chunks(lst, _MAX_ROWS_PER_PAGE)

        resp['html'] = render_template('invoice_timesheet.html', **c)
        resp['json']['total'] = "{0:.2f}".format(invoice.total_with_taxes)

        return jsonify(resp)

    elif request.method == 'POST' and 'file' in request.files:
        file = request.files['file']
        name = secure_filename(file.filename).strip() if file else ''

        if name and allowed_file(name):
            Timesheet.query.filter(Timesheet.invoice == invoice.id).delete()
            invoice.total = 0

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

                    invoice.total += tms.amount

                    db.session.add(tms)

            db.session.commit()

            return redirect(url_for('upload_timesheet', invoice_id=invoice.id))

    return abort(400)


@app.route('/get_companies/<invoice_id>', methods=['GET'])
@login_required
def get_companies(invoice_id):
    inv = Invoice.query.get_or_404(invoice_id)
    txt = request.args.get('q').strip()

    mim = 'application/json'
    res = {'query': txt, 'suggestions': []}
    qry = Company.query.filter(
        Company.user_id == g.user.id,
        Company.name.ilike('%' + txt + '%')
    ).limit(_MAX_SUGGESTIONS)

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


@login_required
@app.route('/get_clients/<invoice_id>', methods=['GET'])
def get_clients(invoice_id):
    inv = Invoice.query.get_or_404(invoice_id)
    txt = request.args.get('q').strip()

    mim = 'application/json'
    res = {'query': txt, 'suggestions': []}
    qry = Client.query.filter(
        Client.user_id == g.user.id,
        Client.name.ilike('%' + txt + '%')
    ).limit(_MAX_SUGGESTIONS)

    for cli in qry.all():
        ctx = {}
        dic = {}

        ctx['client'] = cli
        ctx['invoice'] = inv

        dic['value'] = cli.name
        dic['data'] = render_template('invoice_client.html', **ctx)

        res['suggestions'].append(dic)

    return Response(response=dumps(res), status=200, mimetype=mim)


@login_required
@app.route('/clients', methods=['GET'])
def clients():
    return render_template('clients.html')


@login_required
@app.route('/create_client', methods=['POST'])
def create_client():
    form = request.form
    client = Client(user_id=g.user.id)

    client.name = form['client_name']
    client.email = form['email']
    client.phone = form['phone']
    client.address = form['address']
    client.contact = form['contact_name']
    client.vendor_number = form['vendor_number']

    db.session.add(client)
    db.session.flush()
    db.session.commit()

    return redirect(url_for('clients'))


@login_required
@app.route('/delete_client/<client_id>', methods=['POST'])
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)

    db.session.delete(client)
    db.session.commit()

    return redirect(url_for('clients'))
