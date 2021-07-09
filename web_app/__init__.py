import os

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
    @app.route('/hello')
    def hello():
        return 'Hello world!'

    from . import db
    db.init_app(app)

    from . import auth, sites
    app.register_blueprint(auth.bp)
    app.register_blueprint(sites.bp)

    app.add_url_rule('/', endpoint='index')

    return app
