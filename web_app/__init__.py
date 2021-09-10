import os
import json

from datetime import datetime
from flask.templating import render_template

from jinja2.filters import FILTERS, environmentfilter
from flask import Flask

ABS_CONFIG_PATH = os.path.join(os.path.abspath('.'), 'configs')

# TODO: Create checker of publishing on webmasters sites
# TODO: Create notify of new emails
# TODO: Create function to stop monitoring publishing on site


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True,
                instance_path=ABS_CONFIG_PATH)

    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'database.sqlite')
    )
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # TODO: Put in to separate file
    @app.route('/info')
    def about_us():
        return render_template('info.html')

    # Adding blueprints
    from . import auth, webmasters, sites, categories, configs, funcs, mails
    app.register_blueprint(auth.bp)
    app.register_blueprint(sites.bp)
    app.register_blueprint(webmasters.bp)
    app.register_blueprint(categories.bp)
    app.register_blueprint(configs.bp)
    app.register_blueprint(funcs.bp)
    app.register_blueprint(mails.bp)

    app.add_url_rule('/', endpoint='index')

    # Custom Jinjs2 filters
    @environmentfilter
    def _jinja2_filter_datetime(_, date, fmt=r"%d/%m/%Y"):
        """
        Filter 'strftime' for string, number, float.
        Convert timestamp to date with format.
        Default format:
            Day/Month/Year
            01/12/2021
        """
        return datetime.fromtimestamp(float(date)).strftime(fmt)

    @environmentfilter
    def _jinja2_filter_date_convert(_, date, fmt=r"%d/%m/%Y"):
        if date:
            if 't' in date:
                date = date.split('t')
            else:
                date = date.split()
            format = '%Y-%m-%d'
            date = datetime.strptime(date[0], format)
            return date.strftime(fmt)
        return date

    @environmentfilter
    def _jinja2_filter_date_diff(_, date, fmt=r"%d/%m/%Y"):
        if date:
            if 't' in date:
                date = date.split('t')
            else:
                date = date.split()
            format = '%Y-%m-%d'

            date = datetime.strptime(date[0], format)
            date_now = datetime.now()
            days = date_now - date

            return days.days
        return date

    @environmentfilter
    def _jinja2_filter_to_json(_, string):
        if string:
            return sorted(json.loads(string), key=lambda x: x['contact_type'])
        return string

    FILTERS["strftime"] = _jinja2_filter_datetime
    FILTERS["convert_to_date"] = _jinja2_filter_date_convert
    FILTERS["get_date_diff"] = _jinja2_filter_date_diff
    FILTERS["to_json"] = _jinja2_filter_to_json

    # Custom CLI commands
    from . import db, funcs
    db.init_app(app)
    funcs.get_data_cli(app)
    funcs.get_mails_cli(app)
    funcs.check_posts_cli(app)

    return app
