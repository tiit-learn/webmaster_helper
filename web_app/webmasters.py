from datetime import datetime
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, json
)

from werkzeug.exceptions import abort

from system import functions
from web_app.auth import login_required
from web_app.db import get_db

bp = Blueprint('webmasters', __name__, url_prefix='/webmaster')

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
        db.execute('INSERT INTO webmasters (webmaster_name) VALUES (?) ', (name.strip(),))
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

@bp.route('/')
def index():
    db = get_db()
    webmasters = db.execute(
        'SELECT * FROM webmasters ORDER BY id ASC'
    ).fetchall()
    return render_template('webmasters/index.html', webmasters=webmasters)

@bp.route('/add', methods=('POST', 'GET'))
@login_required
def add():
    if request.method == "POST":
        db = get_db()

        webmaster_name = request.form['webmaster_name']
        contacts = request.form['contact_info']
        error = check_error(request.form)

        if error:
            flash(error)
        else:
            db.execute(
                'INSERT INTO webmasters (webmaster_name, contacts)'
                'VALUES(?, ?)', (webmaster_name, contacts)
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
        contacts = request.form['contact_info']
        error = check_error(request.form, update=webmaster['webmaster_name'])

        if error:
                flash(error)
        else:
            db.execute(
                'UPDATE webmasters SET webmaster_name=?, contacts=?'
                'WHERE id = ?', (webmaster_name, contacts, id)
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