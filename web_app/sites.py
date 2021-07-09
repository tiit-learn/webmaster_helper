from datetime import datetime
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from werkzeug.exceptions import abort

from web_app.auth import login_required
from web_app.db import get_db

bp = Blueprint('sites', __name__)

def get_site(id):
    site = get_db().execute(
        'SELECT * FROM sites WHERE id == ?', (id,)
    ).fetchone()
    if site is None:
        abort(404, f'Site {id} not found.')
    return site

@bp.route('/')
def index():
    db = get_db()
    sites = db.execute(
        'SELECT * FROM sites ORDER BY id'
    ).fetchall()
    return render_template('sites/index.html', sites=sites)

@bp.route('/add-site', methods=('GET', 'POST'))
@login_required
def add_site():
    if request.method == 'POST':
        url = request.form['url']
        category = request.form['category']
        notes = request.form['notes']
        published = datetime.now() if request.form['published'] else False
        error = None

        if not url:
            error = 'URL is require.'
        elif not category:
            error = 'CATEGORY is require.'
        
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO sites (domain, category, notes, published) VALUES (?, ?, ?, ?)',
                (url, category, notes, published)
            )
            db.commit()
            return redirect(url_for('sites.index'))
    
    categories = get_db().execute(
            'SELECT * FROM categories'
        )
    return render_template('sites/add_site.html', categories=categories)

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    site = get_site(id)
    
    if request.method == 'POST':
        url = request.form['url']
        category = request.form['category']
        notes = request.form['notes']
        error = None

        if not url:
            error = 'URL is require.'
        elif not category:
            error = 'Category is require.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE sites SET domain = ?, category = ?, notes = ?'
                'WHERE id = ?', (url, category, notes, id)
            )
            db.commit()
            return redirect(url_for('sites.index'))
    return render_template('sites/update.html', site=site)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_site(id)
    db = get_db()
    db.execute('DELETE FROM sites WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('sites.index'))