import os
from datetime import datetime
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

    from . import db
    db.init_app(app)

    from . import auth, sites, webmasters, categories, configs
    app.register_blueprint(auth.bp)
    app.register_blueprint(sites.bp)
    app.register_blueprint(webmasters.bp)
    app.register_blueprint(categories.bp)
    app.register_blueprint(configs.bp)

    app.add_url_rule('/', endpoint='index')

    # Custom filters
    @environmentfilter
    def _jinja2_filter_datetime(environment, date, fmt=r"%d/%m/%Y"):
        format = '%Y-%m-%d %H:%M:%S.%f'
        return datetime.strptime(date, format).strftime(fmt)

    FILTERS["strftime"] = _jinja2_filter_datetime

    return app
