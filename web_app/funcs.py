import asyncio
import click
import os
import random
import json
import time
import sqlite3
import itertools

from flask import (
    Blueprint
)

from flask.cli import with_appcontext

from system import mail_funcs
from system.functions import get_seo_data

bp = Blueprint('funcs', __name__)

def get_db():

    db = sqlite3.connect(
        os.path.join('configs', 'database.sqlite'),
        detect_types=sqlite3.PARSE_DECLTYPES
    )
    db.row_factory = sqlite3.Row
    return db

def save_seo_to_db(id, site_data, whois_data):
    tries = 0
    db = get_db()
    while tries < 5:
        try:
            db.execute(
                'UPDATE sites SET seo_data = ? WHERE id = ?', (json.dumps(site_data),
                                                                id)
            )
            if whois_data:
                db.execute(
                    'UPDATE sites SET whois_data = ? WHERE id = ?', (json.dumps(whois_data),
                                                                    id)
                )
        except Exception as err:
            print('Ошибка БД:',err)
            time.sleep(random.randint(1,5))
        else:
            db.commit()
            break
        finally:
            tries += 1

def save_mails_to_db(id_msg, to_email, from_email, form_name, subject, body):
    tries = 0
    db = get_db()
    while tries < 5:
        try:
            mail = db.execute(
            'SELECT id FROM mails WHERE status_mail == ?', (id_msg,)
                ).fetchone()
            if not mail:
                db.execute(
                    'INSERT INTO mails (status_mail, from_name, to_name, body)'
                    'VALUES (?, ?, ?, ?)',
                    (id_msg, from_email, to_email, body)
                )
        except Exception as err:
            print('Ошибка БД:',err)
            time.sleep(random.randint(1,5))
        else:
            db.commit()
            break
        finally:
            tries += 1
    

async def proxy_setup():
    if not os.path.exists('proxies.txt'):
        print('Прокси не будут использованы')
        os.environ["PROXY_WORK"] = ""
    else:
        with open('proxies.txt') as file:
            lines = file.readlines()
            proxy = random.choice(lines)
            os.environ['FULL_PROXY_LINK'] = proxy
            user_name,*_, port = proxy.split(':')
            password, _ = _[0].split('@z')
            proxy_domain = 'z' + _
            os.environ['PROXIE_DOMAIN'] = proxy_domain
            os.environ['PROXIE_PORT'] = port
            os.environ['PROXIE_USERNAME'] = user_name
            os.environ['PROXIE_PASSWORD'] = password

async def get_sites_data(sites):
    if os.getenv('PROXY_WORK'):
        await proxy_setup()

    sites_iter = iter(sites)
    try:
        num = 0
        while True:
            batch = tuple(itertools.islice(sites_iter, 50))
            if not batch:
                break
            num += 50
            print(f'Обработка {num} из {len(sites)}')
            coros = [get_seo_data(site) for site in batch]
            await asyncio.gather(*coros)
            # await asyncio.sleep(random.randint(1,5))
    except:
        print('Ошибка в (get_sites_data)')

def site_data():
    # Установка флага работы через прокси. 1 - работать с прокси
    os.environ["PROXY_WORK"] = "1"
    db = get_db()
    sites = db.execute(
        'SELECT id, domain, seo_data, whois_data FROM sites'
    ).fetchall()
    start = time.perf_counter()
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(get_sites_data(sites))
    except:
        print('Ошибка в (site_data)')

    end = time.perf_counter()
    print(f'Finished at {end - start}s')

def get_mails():
    mail_funcs.get_user_mails()

@click.command('get-site-data')
@with_appcontext
def site_data_command():
    click.echo('Получение SEO данных для сайтов по РАССПИСАНИЮ')
    site_data()


def get_data_cli(app):
    app.app_context()
    app.cli.add_command(site_data_command)

@click.command('get-mails')
@with_appcontext
def get_mails_command():
    click.echo('Получение Email по РАССПИСАНИЮ')
    get_mails()


def get_mails_cli(app):
    app.app_context()
    app.cli.add_command(get_mails_command)