# -*- coding: utf-8 -*-

# Python
from csv import reader
from time import strptime
from json import loads
from bson import ObjectId
from datetime import date, datetime, timedelta

# Libs
from flask import g, session, flash, jsonify, render_template, request, url_for, redirect
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename

# Invoice
from models import User
from invoice_app import app, github, login_manager, mongo


# Maximun number of suggestions returned by the autocomplete
_MAX_SUGGESTIONS = 5

# Maximun of CSV rows per page
_MAX_ROWS_PER_PAGE = 20


def _get_array_chunks(array):
    return (array[pos:pos + _MAX_ROWS_PER_PAGE] for pos in xrange(0, len(array), _MAX_ROWS_PER_PAGE))


def _update_clients_data(client_id):
    # Aggregate
    match = {'client._id': client_id, 'paid': False}
    group = {'_id': None, 'count': {'$sum': 1}, 'value': {'$sum': '$value_with_taxes'}}
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
        gh_id = 'gh-%s' % gh_data['id']
        user = mongo.db.user.find_one({'gh_id': gh_id})

        if user is None:
            user = {'gh_id': gh_id}

        user['name'] = gh_data.get('name', '')
        user['email'] = gh_data.get('email', '')
        user['gh_login'] = gh_data.get('login', '')
        mongo.db.user.update({'gh_id': gh_id}, user, upsert=True)
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
                    paid_value += invoice['value_with_taxes']
                else:
                    paid_value += invoice['value']

            else:
                g.user.open_invoices += 1

                if invoice['company']:
                    open_value += invoice['value_with_taxes']
                else:
                    open_value += invoice['value']

        g.user.paid_invoices_value = '{0:.2f}'.format(paid_value)
        g.user.open_invoices_value = '{0:.2f}'.format(open_value)


@app.route('/', methods=['GET'])
def index():
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('home'))
    else:
        return render_template('unlogged_invoice.html', today=date.today())


@login_required
@app.route('/home', methods=['GET'])
def home():
    invoices = list(mongo.db.invoice.find({'user_id': g.user.gh_id}))
    return render_template('home.html', invoices=invoices)


@login_required
@app.route('/toggle_invoice_status/<invoice_id>', methods=['GET', 'POST'])
def toggle_invoice_status(invoice_id):
    invoice = mongo.db.invoice.find_one_or_404(ObjectId(invoice_id))

    if request.method == 'POST':
        form = loads(request.form['data'])
        url = url_for('toggle_invoice_status', invoice_id=invoice['_id'])
        doc = {'$set': {'paid': form['paid']}}
        mongo.db.invoice.update({'_id': invoice['_id']}, doc)

        if invoice['client']:
            _update_clients_data(invoice['client']['_id'])

        return redirect(url)

    elif request.method == 'GET':
        dic = {'paid': [], 'open': [], 'paid_value': 0, 'open_value': 0}

        for invoice in mongo.db.invoice.find({'user_id': g.user.gh_id}):
            template = render_template('home_table_row.html', invoice=invoice)

            if invoice['paid']:
                dic['paid'].append(template.strip())
                dic['paid_value'] += invoice['value_with_taxes']
            else:
                dic['open'].append(template.strip())
                dic['open_value'] += invoice['value_with_taxes']

            dic['open_value'] = 'USD %0.2f' % dic['open_value']
            dic['paid_value'] = 'USD %0.2f' % dic['paid_value']

        return jsonify(**dic)


@login_required
@app.route('/new_invoice', methods=['GET', 'POST'])
def new_invoice():
    company = mongo.db.company.find_one({'user_id': g.user.gh_id}) or {}
    return render_template('invoice_form.html', company=company)


@app.route('/invoice/<invoice_id>', methods=['GET'])
def invoice(invoice_id):
    invoice = mongo.db.invoice.find_one_or_404(ObjectId(invoice_id))
    invoice['timesheet'] = _get_array_chunks(invoice['timesheet'])
    editable = not invoice['paid'] and g.user and g.user.is_authenticated
    return render_template('invoice.html', invoice=invoice, editable=editable)


@app.route('/save_invoice/', methods=['POST'])
@app.route('/save_invoice/<invoice_id>', methods=['POST'])
def save_invoice(invoice_id=''):
    def str2int(x):
        return int(x) if x.strip() else 0

    def str2float(x):
        return float(x) if x.strip() else 0

    company = {}

    # Invoice
    if invoice_id:
        invoice = mongo.db.invoice.find_one_or_404(ObjectId(invoice_id))
        invoice['value'] = str2float(request.form['invoice_value'])
        invoice['value_with_taxes'] = str2float(request.form['invoice_value_with_taxes'])

    else:
        company = mongo.db.company.find_one({'user_id': g.user.gh_id})

        if company:
            invoice_number = company['current_invoice_num'] + 1
            mongo.db.company.update({'_id': company['_id']}, {'$inc': {'current_invoice_num': 1}})
        else:
            invoice_number = mongo.db.invoice.find().count() + 1

        invoice = {
            'user_id': g.user.gh_id,
            'tag_number': '%s%03d' % (date.today().year, invoice_number),
            'value': str2float(request.form['invoice_value']),
            'value_with_taxes': str2float(request.form['invoice_value_with_taxes']),
            'created': datetime.now(),
            'company': {},
            'client': {},
            'service': {},
            'paid': False,
            'timesheet': []
        }

    # Service
    invoice['service'] = {
        'name': request.form['invoice_service_name'],
        'description': request.form['invoice_service_description']
    }

    # Client
    invoice['client'] = {
        '_id': ObjectId(request.form['client_id']) if request.form['client_id'] else None,
        'name': request.form['client_name'],
        'email': request.form['client_email'],
        'phone': request.form['client_phone'],
        'address': request.form['client_address'],
        'contact': request.form['client_contact'],
        'vendor_number': request.form['client_vendor_number']
    }

    # Company
    form_taxes = request.form.getlist('invoice_taxes')

    if request.form['company_id']:
        if not company:
            company = mongo.db.company.find_one({'_id': ObjectId(request.form['company_id'])})

        invoice['company'] = {
            '_id': company['_id'],
            'name': company['name'],
            'email': company['email'],
            'phone': company['phone'],
            'address': company['address'],
            'contact': company['contact'],
            'banking_info': company['banking_info'],
            'taxes': company['taxes']
        }

    else:
        invoice['company'] = {
            '_id': None,
            'name': request.form['company_name'],
            'email': request.form['company_email'],
            'phone': request.form['company_phone'],
            'address': request.form['company_address'],
            'contact': request.form['company_contact'],
            'banking_info': request.form['company_banking_info'],
            'taxes': []
        }

    for index, tax in enumerate(invoice['company']['taxes']):
        if str(index) in form_taxes:
            tax['apply'] = True
        else:
            tax['apply'] = False

    # Timesheet
    if request.files:
        file = request.files['file']
        name = secure_filename(file.filename).strip() if file else ''

        if name:
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
                        kwa = {
                            'hours': aux.tm_hour,
                            'minutes': aux.tm_min,
                            'seconds': aux.tm_sec
                        }
                        entry['duration'] = timedelta(**kwa).total_seconds()

                    entry['amount'] = float(row[13]) if row[13] else 0
                    entry['description'] = row[5]
                    invoice['timesheet'].append(entry)
                    total += entry['amount']

    # Save invoice to the database
    if invoice_id:
        mongo.db.invoice.update({'_id': invoice['_id']}, invoice)
    else:
        invoice['_id'] = mongo.db.invoice.insert(invoice)

    if invoice['client']:
        _update_clients_data(invoice['client']['_id'])

    return redirect(url_for('invoice', invoice_id=invoice['_id']))


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


# Company controllers
# -------------------

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
@app.route('/get_clients', methods=['GET'])
def get_clients():
    term = request.args.get('q').strip()
    response = {'query': term, 'suggestions': []}
    qry = {
        'user_id': g.user.gh_id,
        'name': {'$regex': term, '$options': 'i'}
    }

    for client in mongo.db.iclient.find(qry).limit(_MAX_SUGGESTIONS):
        client['_id'] = str(client['_id'])
        dic = {
            'id': str(client['_id']),
            'value': client['name'],
            'data': client
        }
        response['suggestions'].append(dic)

    return jsonify(response)


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
    client['pending'] = {'count': 0, 'value': 0}
    mongo.db.iclient.insert(client)
    return redirect(url_for('clients'))


@login_required
@app.route('/delete_client/<client_id>', methods=['POST'])
def delete_client(client_id):
    mongo.db.iclient.remove({'_id': ObjectId(client_id)})
    return redirect(url_for('clients'))
