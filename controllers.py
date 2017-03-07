# -*- coding: utf-8 -*-

# Python
from csv import reader
from time import strptime
from json import dumps, loads
from bson import ObjectId
from datetime import date, datetime, timedelta

# Libs
from flask import g, session, flash, jsonify
from flask import abort, render_template, request, Response, url_for, redirect
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename

# Invoice
from invoice_app import app, github, login_manager, mongo
from models import User


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


def _value_with_taxes(value, taxes):
    total_taxes = 0

    for tax in taxes:
        total_taxes += int(tax['value'])

    return float(value) * (1 + float(total_taxes) / 100)


def _update_pending_data(client_id):
    # Aggregate
    match = {'client._id': client_id, 'paid': False}
    group = {'_id': None, 'count': {'$sum': 1}, 'value': {'$sum': '$value'}}
    pipeline = [{'$match': match}, {'$group': group}]
    result = list(mongo.db.invoice.aggregate(pipeline))

    # Update client
    doc = {'$set': {}}

    if result:
        doc['$set']['pending.count'] = result[0]['count']
        doc['$set']['pending.value'] = result[0]['value']
    else:
        doc['$set']['pending.count'] = 0
        doc['$set']['pending.value'] = 0

    mongo.db.iclient.update({'_id': client_id}, doc)


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
        user = mongo.db.user.find_one({'gh_id': ghid})

        if user is None:
            user = {'gh_id': ghid}

        user['name'] = gh_data.get('name', '')
        user['email'] = gh_data.get('email', '')
        user['gh_login'] = gh_data.get('login', '')
        mongo.db.user.update({'gh_id': ghid}, user, upsert=True)
        login_user(User(user['gh_id']), remember=True)
        return redirect(url_for('home'))


@app.route('/logout')
def logout():
    logout_user()

    if 'github_token' in session:
        session.pop('github_token')

    return redirect(url_for('index'))


@login_manager.user_loader
def load_user(gh_id):
    user = mongo.db.user.find_one({'gh_id': gh_id})

    if not user:
        return None

    return User(user['gh_id'])


# Invoice controllers
# -------------------

@app.before_request
def before_request():
    g.user = current_user

    if g.user and g.user.is_authenticated:
        g.user.paid_invoices = 0
        g.user.open_invoices = 0
        paid_value = 0
        open_value = 0

        for invoice in mongo.db.invoice.find({'user_id': g.user.gh_id}):
            if invoice['paid']:
                g.user.paid_invoices += 1

                if invoice['company']:
                    paid_value += _value_with_taxes(invoice['value'], invoice['company']['taxes'])
                else:
                    paid_value += invoice['value']

            else:
                g.user.open_invoices += 1

                if invoice['company']:
                    open_value += _value_with_taxes(invoice['value'], invoice['company']['taxes'])
                else:
                    open_value += invoice['value']

        g.user.paid_invoices_value = '{0:.2f}'.format(paid_value)
        g.user.open_invoices_value = '{0:.2f}'.format(open_value)


@app.route('/')
def index():
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('home'))
    else:
        return render_template('unlogged_invoice.html', today=date.today())


@app.route('/home', methods=['GET'])
@login_required
def home():
    invoices = list(mongo.db.invoice.find({'user_id': g.user.gh_id}))

    for invoice in invoices:
        if invoice['company']:
            invoice['value_with_taxes'] = _value_with_taxes(invoice['value'], invoice['company']['taxes'])
        else:
            invoice['value_with_taxes'] = invoice['value']

    return render_template('home.html', invoices=invoices)


@login_required
@app.route('/toggle_invoice_status/<invoice_id>', methods=['GET', 'POST'])
def toggle_invoice_status(invoice_id):
    invoice = mongo.db.invoice.find_one_or_404(ObjectId(invoice_id))

    if request.method == 'POST':
        url = url_for('toggle_invoice_status', invoice_id=invoice['_id'])
        form = loads(request.form['data'])
        doc = {'$set': {'paid': form['paid']}}
        mongo.db.invoice.update({'_id': invoice['_id']}, doc)

        if invoice['client']:
            _update_pending_data(invoice['client']['_id'])

        return redirect(url)

    elif request.method == 'GET':
        dic = {'paid': [], 'open': []}

        for invoice in mongo.db.invoice.find({'user_id': g.user.gh_id}):
            invoice['value_with_taxes'] = _value_with_taxes(invoice['value'], invoice['company']['taxes'])
            template = render_template('home_table_row.html', invoice=invoice)

            if invoice['paid']:
                dic['paid'].append(template.strip())
            else:
                dic['open'].append(template.strip())

        return jsonify(**dic)


@login_required
@app.route('/invoice', methods=['POST'])
def create_invoice():
    company = mongo.db.company.find_one({'user_id': g.user.gh_id}) or {}
    invoice = {
        'user_id': g.user.gh_id,
        'tag_number': '%s%03d' % (date.today().year, 1),
        'created': datetime.now(),
        'company': company,
        'service': {},
        'value': 0,
        'currency': '$',
        'paid': False,
        'client': {},
        'timesheet': []
    }

    if company:
        number = (date.today().year, company['current_invoice_num'] + 1)
        invoice['tag_number'] = '%s%03d' % number
        doc = {'$inc': {'current_invoice_num': 1}}
        mongo.db.company.update({'user_id': g.user.gh_id}, doc)

    invoice['_id'] = mongo.db.invoice.insert(invoice)

    return redirect(url_for('open_invoice', invoice_id=invoice['_id']))


@login_required
@app.route('/delete_invoice/<invoice_id>', methods=['POST'])
def delete_invoice(invoice_id):
    # Delete invoice
    invoice = mongo.db.invoice.find_one_or_404(ObjectId(invoice_id))
    mongo.db.invoice.remove(invoice['_id'])

    # Update client's pending invoices data
    if invoice['client']:
        doc = {'$inc': {}}
        doc['$inc']['pending.count'] = -1
        doc['$inc']['pending.value'] = -invoice['value']
        mongo.db.iclient.update({'_id': invoice['client']['_id']}, doc)

    return redirect(url_for('home'))


@login_required
@app.route('/invoice/<invoice_id>', methods=['GET'])
def open_invoice(invoice_id):
    invoice = mongo.db.invoice.find_one_or_404(ObjectId(invoice_id))
    invoice['timesheet'] = _get_array_chunks(invoice['timesheet'], _MAX_ROWS_PER_PAGE)

    if invoice['company']:
        invoice['value_with_taxes'] = _value_with_taxes(invoice['value'], invoice['company']['taxes'])
    else:
        invoice['value_with_taxes'] = invoice['value']

    return render_template('invoice.html', invoice=invoice)


@login_required
@app.route('/edit_invoice/<invoice_id>', methods=['POST'])
def edit_invoice(invoice_id):
    # Update invoice
    invoice = mongo.db.invoice.find_one_or_404(ObjectId(invoice_id))
    form = loads(request.form['data'])
    value = float(form['total'].replace('$', '').strip())
    total = _value_with_taxes(value, invoice['company']['taxes'])
    doc = {'service': {}}
    doc['value'] = value
    doc['service']['name'] = form['service_name']
    doc['service']['description'] = form['service_description']
    mongo.db.invoice.update({'_id': invoice['_id']}, {'$set': doc})

    # Update client's pending invoices data
    if invoice['client']:
        _update_pending_data(invoice['client']['_id'])

    return jsonify(total='{0:.2f}'.format(total))


@login_required
@app.route('/set_invoice_client/<invoice_id>', methods=['POST'])
def set_invoice_client(invoice_id):
    invoice = mongo.db.invoice.find_one_or_404(ObjectId(invoice_id))

    if not request.form['id']:
        return abort(400)

    client = mongo.db.iclient.find_one(ObjectId(request.form['id']))
    mongo.db.invoice.update({'_id': invoice['_id']}, {'$set': {'client': client}})
    _update_pending_data(invoice['client']['_id'])
    return _ajax_ok()


@login_required
@app.route('/set_invoice_company/<invoice_id>', methods=['POST'])
def set_invoice_company(invoice_id):
    invoice = mongo.db.invoice.find_one_or_404(ObjectId(invoice_id))

    if not request.form['id']:
        return abort(400)

    company = mongo.db.company.find_one(ObjectId(request.form['id']))
    mongo.db.invoice.update({'_id': invoice['_id']}, {'$set': {'company': company}})
    return _ajax_ok()


@login_required
@app.route('/upload_timesheet/<invoice_id>', methods=['GET', 'POST'])
def upload_timesheet(invoice_id):
    def allowed_file(file):
        return '.' in file and file.rsplit('.', 1)[1] in _ALLOWED_EXT

    def str2int(x):
        return int(x) if x.strip() else 0

    invoice = mongo.db.invoice.find_one_or_404(ObjectId(invoice_id))

    if request.method == 'GET':
        if invoice['company']:
            total = _value_with_taxes(invoice['value'], invoice['company']['taxes'])
        else:
            total = invoice['value']

        invoice['timesheet'] = _get_array_chunks(invoice['timesheet'], _MAX_ROWS_PER_PAGE)
        response = {
            'html': render_template('invoice_timesheet.html', invoice=invoice),
            'json': "{0:.2f}".format(total)
        }
        return jsonify(response)
    elif request.method == 'POST' and 'file' in request.files:
        file = request.files['file']
        name = secure_filename(file.filename).strip() if file else ''

        if name and allowed_file(name):
            timesheet = []
            total = 0

            for idx, row in enumerate(reader(file)):
                if idx > 0 and len(row) == 14:
                    lst = list(map(str2int, row[7].split('-')))
                    entry = {
                        'date': None,
                        'amount': 0,
                        'duration': None,
                        'description': ''
                    }

                    if len(lst) == 3 and all(lst):
                        entry['date'] = datetime(*lst)

                    if row[11].strip():
                        aux = strptime(row[11], '%H:%M:%S')
                        kwa = {}

                        kwa['hours'] = aux.tm_hour
                        kwa['minutes'] = aux.tm_min
                        kwa['seconds'] = aux.tm_sec

                        entry['duration'] = timedelta(**kwa).total_seconds()

                    entry['amount'] = float(row[13]) if row[13] else 0
                    entry['description'] = row[5]
                    timesheet.append(entry)
                    total += entry['amount']

            doc = {'$set': {'timesheet': timesheet, 'value': total}}
            mongo.db.invoice.update({'_id': invoice['_id']}, doc)

            if invoice['client']:
                _update_pending_data(invoice['client']['_id'])

            return redirect(url_for('upload_timesheet', invoice_id=invoice['_id']))

    return abort(400)


# Company controllers
# -------------------

@app.route('/get_companies/<invoice_id>', methods=['GET'])
@login_required
def get_companies(invoice_id):
    invoice = mongo.db.invoice.find_one_or_404(ObjectId(invoice_id))
    txt = request.args.get('q').strip()
    mim = 'application/json'
    res = {'query': txt, 'suggestions': []}
    qry = {
        'user_id': g.user.gh_id,
        'name': {'$regex': txt, '$options': 'i'}
    }

    for company in mongo.db.company.find(qry).limit(_MAX_SUGGESTIONS):
        dic = {}

        invoice['company'] = company

        dic['value'] = company['name']
        dic['data'] = render_template('invoice_company.html', invoice=invoice)

        res['suggestions'].append(dic)

    return Response(response=dumps(res), status=200, mimetype=mim)


@login_required
@app.route('/company', methods=['GET', 'POST'])
def company():
    def tax(name, number, value):
        if name and number and value:
            return {'name': name, 'number': number, 'value': value}

    if request.method == 'GET':
        company = mongo.db.company.find_one({'user_id': g.user.gh_id}) or {}
        return render_template('company.html', company=company)
    else:
        company = mongo.db.company.find_one({'user_id': g.user.gh_id}) or {}
        company['name'] = request.form['company_name']
        company['email'] = request.form['email']
        company['phone'] = request.form['phone']
        company['address'] = request.form['address']
        company['contact'] = request.form['contact_name']
        company['banking_info'] = request.form['banking']
        company['current_invoice_num'] = int(request.form['invoice_num'])
        company['taxes'] = []
        names = request.form.getlist('tax_name')
        numbers = request.form.getlist('tax_number')
        values = request.form.getlist('tax_value')
        taxes = map(tax, names, numbers, values)

        for tax in taxes:
            if tax:
                company['taxes'].append(tax)

        if '_id' in company:
            mongo.db.company.update({'_id': company['_id']}, {'$set': company})
        else:
            company['user_id'] = g.user.gh_id
            mongo.db.company.insert(company)

        return redirect(url_for('company'))


# Client controllers
# ------------------

@login_required
@app.route('/get_clients/<invoice_id>', methods=['GET'])
def get_clients(invoice_id):
    invoice = mongo.db.invoice.find_one_or_404(ObjectId(invoice_id))
    txt = request.args.get('q').strip()
    res = {'query': txt, 'suggestions': []}
    qry = {
        'user_id': g.user.gh_id,
        'name': {'$regex': txt, '$options': 'i'}
    }
    for client in mongo.db.iclient.find(qry).limit(_MAX_SUGGESTIONS):
        invoice['client'] = client
        dic = {
            'id': str(client['_id']),
            'value': client['name'],
            'data': render_template('invoice_client.html', invoice=invoice)
        }
        res['suggestions'].append(dic)

    return jsonify(res)


@login_required
@app.route('/clients', methods=['GET'])
def clients():
    clients = mongo.db.iclient.find({'user_id': g.user.gh_id})
    return render_template('clients.html', clients=clients)


@login_required
@app.route('/create_client', methods=['POST'])
def create_client():
    client = {}
    client['user_id'] = g.user.gh_id
    client['name'] = request.form['client_name']
    client['email'] = request.form['email']
    client['phone'] = request.form['phone']
    client['address'] = request.form['address']
    client['contact'] = request.form['contact_name']
    client['currency'] = request.form['currency']
    client['vendor_number'] = request.form['vendor_number']
    client['apply_taxes'] = request.form.get('apply_taxes', '') == 'on'
    client['pending'] = {
        'count': 0,
        'value': 0
    }
    mongo.db.iclient.insert(client)
    return redirect(url_for('clients'))


@login_required
@app.route('/delete_client/<client_id>', methods=['POST'])
def delete_client(client_id):
    mongo.db.iclient.remove({'_id': ObjectId(client_id)})
    return redirect(url_for('clients'))
