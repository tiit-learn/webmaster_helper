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
from system.functions import get_seo_data, check_post

bp = Blueprint('funcs', __name__)

def get_db():

    db = sqlite3.connect(
        os.path.join('configs', 'database.sqlite'),
        detect_types=sqlite3.PARSE_DECLTYPES
    )
    db.row_factory = sqlite3.Row
    return db


def save_to_db_check_post(id, check_data):
    tries = 0
    db = get_db()
    while tries < 5:
        try:
            db.execute(
                'UPDATE sites SET last_check = ? WHERE id = ?', (json.dumps(check_data),
                                                                 id)
            )
        except Exception as err:
            print('Ошибка БД:', err)
            time.sleep(random.randint(1, 5))
        else:
            db.commit()
            break
        finally:
            tries += 1


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
            print('Ошибка БД:', err)
            time.sleep(random.randint(1, 5))
        else:
            db.commit()
            break
        finally:
            tries += 1


def get_count_emails(status, box):
    db = get_db()
    emails = db.execute(
        'SELECT id FROM mails WHERE status = ? AND mail_box = ?', (
            status, box)
    ).fetchall()
    count_emails = len(emails)
    return count_emails


def check_emails_in_db(mail_ids, box):
    """
    Checking uniq_gen in the mails table.
    Returns a sorted list of mails that are not in the database.
    """
    _mail_ids = []
    db = get_db()
    for mail_id in mail_ids:
        _uniq_get = f'{box}_{mail_id}'
        exist_ids = db.execute(
            'SELECT uniq_gen FROM mails WHERE uniq_gen = ?', (_uniq_get,)
        ).fetchall()
        if not exist_ids:
            _mail_ids.append(mail_id)
    print(f'{len(_mail_ids)} New emails')
    return _mail_ids


def save_mails_to_db(mail_box, mail_date, id_msg, uniq_gen, to_email, from_email, subject, body):
    tries = 0
    status = 0
    db = get_db()
    while tries < 5:
        try:
            mail = db.execute(
                'SELECT id FROM mails WHERE uniq_gen = ?', (uniq_gen,)
            ).fetchone()
            if not mail:
                db.execute(
                    'INSERT INTO mails (uniq_gen, mail_box, mail_date, status_mail, from_name, to_name, body, subject, status)'
                    'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (uniq_gen, mail_box, mail_date, id_msg,
                     from_email, to_email, body, subject, status)
                )
        except Exception as err:
            print('Ошибка БД:', err)
            time.sleep(random.randint(1, 5))
        else:
            db.commit()
            break
        finally:
            tries += 1


async def proxy_setup():
    if not os.path.exists('proxies.txt'):
        print('Proxies don\'t found')
        os.environ["PROXY_WORK"] = ""
    else:
        with open('proxies.txt') as file:
            lines = file.readlines()
            proxy = random.choice(lines)
            os.environ['FULL_PROXY_LINK'] = proxy
            user_name, *_, port = proxy.split(':')
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
    except Exception as err:
        print('Ошибка в (get_sites_data)', err)


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
    except Exception as err:
        print('Ошибка в (site_data)', err)

    end = time.perf_counter()
    print(f'Finished collect site data at {end - start}s')


def get_checking_links():
    """
    Do DB query to get all pages for checking link on page.
    """
    start = time.perf_counter()
    db = get_db()
    pages_list = db.execute(
        'SELECT id, domain, published_link FROM sites WHERE published_link NOT NULL;'
    ).fetchall()

    # Setup proxy
    os.environ["PROXY_WORK"] = "1"
    proxy_setup()

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(check_post(pages_list))
    except Exception as err:
        print('Ошибка в (get_checking_links)', err)

    end = time.perf_counter()
    print(f'Finished checking at {end - start}s')


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


# TODO: Create checking for only one site with arguments in CLI
@click.command('check-posts')
@with_appcontext
def check_posts_command():
    click.echo('Checking posts on the sites')
    get_checking_links()


def check_posts_cli(app):
    app.app_context()
    app.cli.add_command(check_posts_command)
