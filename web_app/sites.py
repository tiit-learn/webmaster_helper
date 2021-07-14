from datetime import datetime
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from werkzeug.exceptions import abort

from system import functions
from web_app.auth import login_required
from web_app.db import get_db
from web_app.webmasters import get_webmaster_id
from web_app.categories import get_category_id

bp = Blueprint('sites', __name__)

def get_site(id):
    site = get_db().execute(
        'SELECT * FROM sites LEFT OUTER'
        ' JOIN webmasters AS web ON sites.webmaster_id = web.id LEFT OUTER'
        ' JOIN categories AS cat ON sites.category_id = cat.id'
        ' WHERE sites.id == ?', (id,)
    ).fetchone()
    if site is None:
        abort(404, f'Site {id} not found.')
    return site



@bp.route('/')
def index():
    db = get_db()
    sites = db.execute(
        'SELECT * FROM sites LEFT OUTER'
        ' JOIN webmasters AS web ON sites.webmaster_id = web.id LEFT OUTER'
        ' JOIN categories AS cat ON sites.category_id = cat.id'
        ' ORDER BY sites.id ASC;'
    ).fetchall()
    
    return render_template('sites/index.html', sites=sites)

@bp.route('/add-site', methods=('GET', 'POST'))
@login_required
def add_site():
    if request.method == 'POST':
        url = functions.remove_http(request.form['url'])
        category = request.form['category'].strip()
        category_id = get_category_id(category)
        contact_form_link = functions.remove_http(request.form['contact_form_link'])
        price = request.form['price']
        notes = request.form['notes']
        published = datetime.now() if request.form['published'] == '1' else None
        published_link = functions.remove_http(request.form['published_link']) if request.form['published'] == '1' else None
        webmaster_name = request.form['webmaster'] if request.form['webmaster'] else None
        webmaster_id = get_webmaster_id(request.form['webmaster'].strip()) if webmaster_name else None
        error = None

        if not functions.check_url(url):
            error = 'URL is require.'
        elif not category:
            error = 'CATEGORY is require.'
        
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO sites (domain, category_id, notes,'
                'published, contact_form_link, price, webmaster_id,'
                'published_link)'
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (url, category_id, notes, published, contact_form_link, price,
                 webmaster_id, published_link)
            )
            db.commit()
            return redirect(url_for('sites.index'))
    
    categories = get_db().execute(
            'SELECT * FROM categories'
        )
    webmasters = get_db().execute(
            'SELECT * FROM webmasters'
        )
    return render_template('sites/add_site.html', categories=categories, webmasters=webmasters)

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    site = get_site(id)
    
    if request.method == 'POST':
        url = functions.remove_http(request.form['url'])
        category = request.form['category'].strip()
        category_id = get_category_id(category)
        contact_form_link = functions.remove_http(request.form['contact_form_link'])
        price = request.form['price']
        notes = request.form['notes']
        published = datetime.now() if request.form['published'] == '1' else None
        published_link = functions.remove_http(request.form['published_link']) if request.form['published'] == '1' else None
        webmaster_name = request.form['webmaster'] if request.form['webmaster'] else None
        webmaster_id = get_webmaster_id(request.form['webmaster'].strip()) if webmaster_name else None
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
                'UPDATE sites SET domain = ?, category_id = ?, notes = ?, published = ?,'
                'contact_form_link = ?, price = ?, webmaster_id = ?,'
                'published_link = ?'
                'WHERE id = ?', (url, category_id, notes, published, contact_form_link, price,
                 webmaster_id, published_link, id)
            )
            db.commit()
            return redirect(url_for('sites.index'))
    categories = get_db().execute(
            'SELECT * FROM categories'
        )
    webmasters = get_db().execute(
            'SELECT * FROM webmasters'
        )
    return render_template('sites/update.html', site=site,
                            categories=categories,
                            webmasters=webmasters)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_site(id)
    db = get_db()
    db.execute('DELETE FROM sites WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('sites.index'))

@bp.route('/<int:id>/contact')
@login_required
def contact(id):
    site = get_db().execute(
        'SELECT * FROM sites WHERE id == ?', (id,)
    ).fetchone()
    if not site or (not site['contact_form_link']) and (not site['webmaster_id']):
        abort(404, f'Contacts for ({id}) not found.')
    return render_template('sites/contact.html', site=site)