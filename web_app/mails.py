from datetime import datetime
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for,
)

from werkzeug.exceptions import abort

from system import functions
from web_app.auth import login_required
from web_app.db import get_db

bp = Blueprint('mails', __name__, url_prefix='/mails')


@bp.route('/')
def index():
    db = get_db()
    mails = db.execute(
        'SELECT * FROM mails'
        ' WHERE mail_box == "INBOX" ORDER BY mail_date DESC ;'
    ).fetchall()
    return render_template('mails/index.html', mails=mails)


@login_required
@bp.route('<int:id>')
def mail(id):
    db = get_db()
    db.execute(
        'UPDATE mails SET status=1 WHERE id=?;',
        (id,)
    )
    db.commit()
    mail = f'America - Mail #{id}'
    return render_template('mails/mail.html', mail=mail)
