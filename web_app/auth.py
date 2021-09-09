import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from web_app.db import get_db
from web_app.funcs import get_count_emails

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Требуется ввести имя пользователя.'
        elif not password:
            error = 'Требуется ввести паоль.'
        elif db.execute(
            'SELECT id FROM users WHERE user_name == ?', (username,)
        ).fetchone() is not None:
            error = f"Пользлватель, {username} уже зарегистрирован."

        if error is None:

            db.execute(
                'INSERT INTO users (user_name, user_password) VALUES(?, ?)',
                (username, generate_password_hash(password))
            )
            db.commit()
            return redirect(url_for('auth.login'))

        flash(error)
    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM users WHERE user_name == ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Не верно указан логин.'
        elif not check_password_hash(user['user_password'], password):
            error = 'Не верный пароль.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        flash(error)
    return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM users WHERE id = ?', (user_id,)
        ).fetchone()
        new_emails, old_emails = (get_count_emails(0, 'INBOX'),
                                  get_count_emails(1, 'INBOX'))
        g.mails = new_emails + old_emails
        g.new_mails = new_emails


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)

    return wrapped_view
