from datetime import datetime
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from werkzeug.exceptions import abort

from system import functions
from web_app.auth import login_required
from web_app.db import get_db

bp = Blueprint('configs', __name__, url_prefix='/configs')

@bp.route('/')
def index():
    return render_template('configs.html')