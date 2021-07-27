from datetime import datetime
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
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
        ' ORDER BY id ASC;'
    ).fetchall()
    return render_template('mails.html', mails=mails)