from datetime import datetime
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
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

@bp.route('/')
def index():
    db = get_db()
    webmasters = db.execute(
        'SELECT * FROM webmasters'
    ).fetchall()
    return render_template('webmasters/index.html', webmasters=webmasters)

@bp.route('/add', methods=('POST', 'GET'))
@login_required
def add():
    return render_template('webmasters/add.html')

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    webmaster = get_webmaster(id)
    return render_template('webmasters/update.html', webmaster=webmaster)