import re

from flask import (
    Blueprint, flash, redirect, render_template, request, url_for, json
)

from werkzeug.exceptions import abort

from web_app.auth import login_required
from web_app.db import get_db

bp = Blueprint('webmasters', __name__, url_prefix='/webmaster')


def normalize_contact(contact_list):
    contact_list = json.loads(contact_list)
    for contact in contact_list:
        if contact['contact']:
            contact['contact'] = re.sub(
                r'http(s)?:\/\/(www\.)?', '', contact['contact'])
    return json.dumps(contact_list)

def get_webmaster(id):
    webmaster = get_db().execute(
        'SELECT * FROM webmasters WHERE id == ?', (id,)
    ).fetchone()
    if webmaster is None:
        abort(404, f'Webmaster {id} not found.')
    return webmaster


def get_webmaster_id(name):
    webmaster = get_db().execute(
        'SELECT id FROM webmasters WHERE webmaster_name == ?', (name,)
    ).fetchone()
    if not webmaster:
        db = get_db()
        db.execute(
            'INSERT INTO webmasters (webmaster_name) VALUES (?) ', (name.strip(),))
        db.commit()
        return get_webmaster_id(name)
    return webmaster['id']


def check_error(request_form, update=False):
    error = None

    db = get_db()

    if update:
        update = db.execute('SELECT id FROM webmasters WHERE'
                            ' webmaster_name=? AND webmaster_name!=?',
                            (request_form['webmaster_name'], update)
                            ).fetchone()

    if not request_form['webmaster_name']:
        error = 'Необходимо указать имя вебмастера.'
    elif 'none' in request_form['contact_info'] or not request_form['contact_info']:
        error = 'Необходимо указать контакты.'
    elif db.execute('SELECT id FROM webmasters WHERE'
                    ' webmaster_name=?',
                    (request_form['webmaster_name'],)
                    ).fetchone() and update:
        error = 'Данный вебмастер уже существует.'

    return error

# TODO: Delete DataTable
# TODO: Replace jQuery to Vue(buefy)
@bp.route('/')
def index():
    db = get_db()
    webmasters = db.execute(
        'SELECT * FROM webmasters ORDER BY id DESC'
    ).fetchall()
    return render_template('webmasters/index.html', webmasters=webmasters)


@bp.route('/add', methods=('POST', 'GET'))
@login_required
def add():
    if request.method == "POST":
        db = get_db()
        webmaster_name = request.form['webmaster_name']
        contacts = normalize_contact(request.form['contact_info'])
        payments = request.form['payment_info']
        error = check_error(request.form)
        if error:
            flash(error)
        else:
            db.execute(
                'INSERT INTO webmasters (webmaster_name, contacts, payments)'
                'VALUES(?, ?, ?)', (webmaster_name, contacts, payments)
            )
            db.commit()
            return redirect(url_for('webmasters.index'))
    return render_template('webmasters/add.html', webmaster={})


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    db = get_db()
    webmaster = get_webmaster(id)
    if request.method == 'POST':
        webmaster_name = request.form['webmaster_name']
        contacts = normalize_contact(request.form['contact_info'])
        payments = request.form['payment_info']
        error = check_error(request.form, update=webmaster['webmaster_name'])
        if error:
            flash(error)
        else:
            db.execute(
                'UPDATE webmasters SET webmaster_name=?, contacts=?, payments=?'
                'WHERE id = ?', (webmaster_name, contacts, payments, id)
            )
            db.commit()
            return redirect(url_for('webmasters.index'))
    return render_template('webmasters/update.html', webmaster=webmaster)


@bp.route('/<int:id>/delete')
@login_required
def delete(id):
    db = get_db()
    db.execute('DELETE FROM webmasters WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('webmasters.index'))
