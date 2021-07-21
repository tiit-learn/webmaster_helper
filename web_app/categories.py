from datetime import datetime
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from werkzeug.exceptions import abort

from system import functions
from web_app.auth import login_required
from web_app.db import get_db

bp = Blueprint('categories', __name__, url_prefix='/categories')

def get_category(id):
    category = get_db().execute(
        'SELECT * FROM categories WHERE id == ?', (id,)
    ).fetchone()
    if category is None:
        abort(404, f'Category {id} not found.')
    return category

def get_category_id(name):
    category = get_db().execute(
        'SELECT id FROM categories WHERE name == ?', (name,)
    ).fetchone()
    if not category:
        db = get_db()
        db.execute('INSERT INTO categories (name) VALUES (?) ', (name.strip(),))
        db.commit()
        return get_category_id(name)
    return category['id']

@bp.route('/')
def index():
    db = get_db()
    categories = db.execute(
        'SELECT * FROM categories'
    ).fetchall()
    return render_template('categories/index.html', categories=categories[1:])

@bp.route('/add', methods=('POST', 'GET'))
def add():
    return render_template('categories/add.html')

@bp.route('/<int:id>/update')
@login_required
def update(id):
    category = get_category(id)
    return render_template('categories/update.html', category=category)