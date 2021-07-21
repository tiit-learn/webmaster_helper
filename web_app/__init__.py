import os

from datetime import datetime, timedelta
from flask.templating import render_template

from jinja2.filters import FILTERS, environmentfilter
from flask import Flask

ABS_CONFIG_PATH = os.path.join(os.path.abspath('.'), 'configs')

def create_app(test_config=None):
    
    # создание и конфигурация приложения
    app = Flask(__name__, instance_relative_config=True,
                instance_path=ABS_CONFIG_PATH)

    app.config.from_mapping(
        SECRET_KEY = 'dev',
        DATABASE=os.path.join(app.instance_path, 'database.sqlite')
    )
    if test_config is None:
        # Загрузка конфигурации экземпляра, если существует и не тестирование
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Загрузка тестовой конфигурации
        app.config.from_mapping(test_config)

    # Убедиться, что каталог экземляра существует
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    # Создание простой страницы  
    @app.route('/info')
    def about_us():
        return render_template('info.html')

    from . import db, funcs
    db.init_app(app)
    funcs.get_data(app)

    from . import auth, webmasters, sites, categories, configs, funcs
    app.register_blueprint(auth.bp)
    app.register_blueprint(sites.bp)
    app.register_blueprint(webmasters.bp)
    app.register_blueprint(categories.bp)
    app.register_blueprint(configs.bp)
    app.register_blueprint(funcs.bp)

    app.add_url_rule('/', endpoint='index')

    # Custom filters
    @environmentfilter
    def _jinja2_filter_datetime(_, date, fmt=r"%d/%m/%Y"):
        return datetime.fromtimestamp(int(date)).strftime(fmt)
    
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
            days = date_now-date

            return days.days
        return date

    FILTERS["strftime"] = _jinja2_filter_datetime
    FILTERS["convert_to_date"] = _jinja2_filter_date_convert
    FILTERS["get_date_diff"] = _jinja2_filter_date_diff

    return app
