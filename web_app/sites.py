import json
import time
import re

from datetime import datetime
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)

from werkzeug.exceptions import abort

from system import functions, mail_funcs
from web_app.auth import login_required
from web_app.db import get_db
from web_app.webmasters import get_webmaster_id
from web_app.categories import get_category_id

bp = Blueprint('sites', __name__)


def get_site(id):
    site = get_db().execute(
        'SELECT * FROM sites LEFT OUTER'
        ' JOIN webmasters AS web ON sites.webmaster_id = web.id LEFT OUTER'
        ' JOIN categories AS cat ON sites.category_id = cat.id'
        ' WHERE sites.id == ?', (id,)
    ).fetchone()
    if site is None:
        abort(404, f'Site {id} not found.')
    return site


@bp.route('/temp')
def db_done():
    db = get_db()
    sites = db.execute('SELECT * FROM sites WHERE price NOT NULL AND price != ""').fetchall()
    sites = [dict(site) for site in sites]
    for site in sites:
        if site['seo_data']:
                site['seo_data'] = json.loads(site['seo_data'])
        effective_count = functions.effective_count(site)
        db.execute(
                'UPDATE sites SET effective_count = ?'
                'WHERE id = ?', (effective_count, site['id'])
            )
        db.commit()



@bp.route('/')
def index():
    db = get_db()
    if request.args.get('status') == 'new_mails':
        new_mails = db.execute('SELECT from_name FROM mails WHERE mail_box == "INBOX" AND status == "0"').fetchall()
        all_new_mails = [f'contacts LIKE "%{mail["from_name"]}%"' for mail in new_mails] if len(new_mails) > 0 else ['contact LIKE "%NO MAILS%"']
        sites_request = '''SELECT * FROM sites LEFT OUTER
                         JOIN webmasters AS web ON sites.webmaster_id = web.id LEFT OUTER
                         JOIN categories AS cat ON sites.category_id = cat.id WHERE '''
        # TODO: Find some better idei for get all new mails from site webmaster
        sites_request = sites_request + ' OR '.join(all_new_mails)
    elif request.args.get('status') == 'not_contact':
        sites_request = '''SELECT * FROM sites LEFT OUTER
                         JOIN webmasters AS web ON sites.webmaster_id = web.id LEFT OUTER
                         JOIN categories AS cat ON sites.category_id = cat.id
                         WHERE last_contact_date ISNULL'''
    elif request.args.get('status') == 'can_publish':
        sites_request = """SELECT * FROM sites LEFT OUTER
                         JOIN webmasters AS web ON sites.webmaster_id = web.id LEFT OUTER
                         JOIN categories AS cat ON sites.category_id = cat.id
                         WHERE last_contact_date LIKE '%"status": "publishing"%' AND published_link ISNULL"""
    elif request.args.get('status') == 'publishing':
        sites_request = """SELECT * FROM sites LEFT OUTER
                         JOIN webmasters AS web ON sites.webmaster_id = web.id LEFT OUTER
                         JOIN categories AS cat ON sites.category_id = cat.id
                         WHERE last_contact_date LIKE '%"status": "publishing"%' AND published_link NOT NULL"""
    elif request.args.get('status') == 'pending':
        sites_request = """SELECT * FROM sites LEFT OUTER
                         JOIN webmasters AS web ON sites.webmaster_id = web.id LEFT OUTER
                         JOIN categories AS cat ON sites.category_id = cat.id
                         WHERE last_contact_date LIKE '%"status": "pending"%'"""
    elif request.args.get('status') == 'waite_publishing':
        sites_request = """SELECT * FROM sites LEFT OUTER
                         JOIN webmasters AS web ON sites.webmaster_id = web.id LEFT OUTER
                         JOIN categories AS cat ON sites.category_id = cat.id
                         WHERE last_contact_date LIKE '%"status": "waite_publishing"%'"""

    elif request.args.get('status') == 'bad_condition':
        sites_request = """SELECT * FROM sites LEFT OUTER
                         JOIN webmasters AS web ON sites.webmaster_id = web.id LEFT OUTER
                         JOIN categories AS cat ON sites.category_id = cat.id
                         WHERE last_contact_date LIKE '%"status": "bad_condition"%'"""
    else:
        sites_request = '''SELECT * FROM sites LEFT OUTER
                         JOIN webmasters AS web ON sites.webmaster_id = web.id LEFT OUTER
                         JOIN categories AS cat ON sites.category_id = cat.id'''

    if (search := request.args.get('search')):
        sites_request = f'''SELECT * FROM sites LEFT OUTER
                         JOIN webmasters AS web ON sites.webmaster_id = web.id LEFT OUTER
                         JOIN categories AS cat ON sites.category_id = cat.id WHERE domain LIKE "%{search}%"
                         OR web.webmaster_name LIKE "%{search}%"'''

    count = len(sites_request)

    # Paggination implementation
    per_page = 10  # define how many results you want per page
    page = request.args.get('page', 1, type=int)
    pages = count // per_page  # this is the number of pages
    offset = (page - 1) * per_page  # offset for SQL query
    limit = 20 if page == pages else per_page  # limit for SQL query

    prev_url = url_for('index', page=page - 1) if page > 1 else None
    next_url = url_for('index', page=page + 1) if page < pages else None
    if request.args.get('sort') == 'effective_count':
        sites = db.execute(sites_request + f' ORDER BY effective_count DESC, sites.id DESC LIMIT {limit} OFFSET {offset};').fetchall()
    elif request.args.get('sort') == 'publish_date':
        sites = db.execute(sites_request + f' ORDER BY published DESC LIMIT {limit} OFFSET {offset};').fetchall()
    else:
        sites = db.execute(sites_request + f' ORDER BY sites.id DESC LIMIT {limit} OFFSET {offset};').fetchall()

    if sites:
        sites = [dict(site) for site in sites]
        for site in sites:
            site['mail_count'] = 0
            site['new_mail_count'] = 0
            if site['contacts']:
                for contact in json.loads(site['contacts']):
                    if contact['contact_type'] == 'mail':
                        site['mail_count'] += len(get_db().execute(
                            'SELECT * FROM mails WHERE to_name == ? OR from_name == ?', (contact['contact'], contact['contact'])).fetchall())
                        site['new_mail_count'] += len(get_db().execute(
                            'SELECT * FROM mails WHERE from_name == ? AND status == 0', (contact['contact'],)).fetchall())
            if site['seo_data']:
                site['seo_data'] = json.loads(site['seo_data'])
            if site['whois_data']:
                site['whois_data'] = json.loads(site['whois_data'])
            if site['last_contact_date']:
                site['last_contact_date'] = json.loads(
                    site['last_contact_date'])
            if site['last_check']:
                site['last_check'] = json.loads(site['last_check'])
    return render_template('sites/index.html', sites=sites, prev_url=prev_url, next_url=next_url)


@bp.route('/add-site', methods=('GET', 'POST'))
@login_required
def add_site():
    if request.method == 'POST':
        url = functions.remove_http(request.form['url'])
        category = request.form['category'].strip()
        category_id = get_category_id(category)
        contact_form_link = functions.remove_http(
            request.form['contact_form_link'])
        price = request.form['price']
        notes = request.form['notes']

        if request.form['published'] == '1' and request.form['published_date']:
            published = datetime.strptime(
                request.form['published_date'], r'%d/%m/%Y').timestamp()
        elif request.form['published'] == '1' and not request.form['published_date']:
            published = time.time()
        else:
            published = None

        published_link = functions.remove_http(
            request.form['published_link']) if request.form['published'] == '1' else None
        webmaster_name = request.form['webmaster'] if request.form['webmaster'] else None
        webmaster_id = get_webmaster_id(
            request.form['webmaster'].strip()) if webmaster_name else None

        if request.form['last_contact_status'] == '1' and request.form['contact_date']:
            last_contact_date = datetime.strptime(
                request.form['contact_date'], r'%d/%m/%Y').timestamp()
        elif request.form['last_contact_status'] == '1' and not request.form['contact_date']:
            last_contact_date = time.time()
        else:
            last_contact_date = None

        last_contact_date_status = request.form['contact_status'] if last_contact_date else None
        last_contact_date = json.dumps({
            'date': last_contact_date,
            'status': last_contact_date_status
        }) if last_contact_date else None

        error = None

        db = get_db()

        if not functions.check_url(url):
            error = 'URL is require.'
        elif not category:
            error = 'CATEGORY is require.'
        elif db.execute('SELECT domain FROM sites WHERE domain=?', (url,)).fetchone():
            error = f'This site ({url.upper()}) already exist.'

        if error is not None:
            flash(error)
        else:
            db.execute(
                'INSERT INTO sites (domain, category_id, notes,'
                'published, contact_form_link, price, webmaster_id,'
                'published_link, last_contact_date)'
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (url, category_id, notes, published, contact_form_link, price,
                 webmaster_id, published_link, last_contact_date)
            )
            db.commit()
            return redirect(url_for('sites.index'))

    categories = get_db().execute(
        'SELECT * FROM categories'
    )
    webmasters = get_db().execute(
        'SELECT * FROM webmasters'
    )
    return render_template('sites/add_site.html', site={'last_contact_date': None}, categories=categories, webmasters=webmasters)


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):

    site = get_site(id)
    if request.method == 'POST':
        print('Referer:', request.form.get('referer'))
        if request.form['published'] == '1' and request.form['published_date']:
            published = datetime.strptime(
                request.form['published_date'], r'%d/%m/%Y').timestamp()
        elif request.form['published'] == '1' and not request.form['published_date']:
            published = time.time()
        else:
            published = None

        url = functions.remove_http(request.form['url'])
        category = request.form['category'].strip()
        category_id = get_category_id(category)
        contact_form_link = functions.remove_http(
            request.form['contact_form_link'])
        price = request.form['price'] if request.form['price'] != 'None' else None
        notes = request.form['notes'] if request.form['notes'] != 'None' else None
        published_link = functions.remove_http(
            request.form['published_link']) if request.form['published'] == '1' else None
        webmaster_name = request.form['webmaster'] if request.form['webmaster'] else None
        webmaster_id = get_webmaster_id(
            request.form['webmaster'].strip()) if webmaster_name else None

        if request.form['last_contact_status'] == '1' and request.form['contact_date']:
            last_contact_date = datetime.strptime(
                request.form['contact_date'], r'%d/%m/%Y').timestamp()
        elif request.form['last_contact_status'] == '1' and not request.form['contact_date']:
            last_contact_date = time.time()
        else:
            last_contact_date = None

        last_contact_date_status = request.form['contact_status'] if last_contact_date else None
        last_contact_date = json.dumps({
            'date': last_contact_date,
            'status': last_contact_date_status
        }) if last_contact_date else None

        error = None

        site = dict(get_site(id))
        effective_count = 0
        if site['seo_data']:
            site['seo_data'] = json.loads(site['seo_data'])
        if price:
            if isinstance(price, str):
                price = price.replace(',','.')
            site['price'] = float(price)
            effective_count = functions.effective_count(site)

        db = get_db()

        if not url:
            error = 'URL is require.'
        elif not category:
            error = 'Category is require.'
        elif db.execute('SELECT domain FROM sites WHERE domain=? AND id != ?', (url, id)).fetchone():
            error = f'This site ({url.upper()}) already exist.'

        if error is not None:
            flash(error)
        else:
            db.execute(
                'UPDATE sites SET domain = ?, category_id = ?, notes = ?, published = ?,'
                'contact_form_link = ?, price = ?, webmaster_id = ?,'
                'published_link = ?, published = ?, last_contact_date = ?, effective_count = ?'
                'WHERE id = ?', (url, category_id, notes, published, contact_form_link, price,
                                 webmaster_id, published_link, published, last_contact_date,
                                 effective_count, id)
            )
            db.commit()
            return redirect(request.form.get('referer'))
    categories = get_db().execute(
        'SELECT * FROM categories'
    )
    webmasters = get_db().execute(
        'SELECT * FROM webmasters'
    )

    if site:
        site = dict(site)
        if site['seo_data']:
            site['seo_data'] = json.loads(site['seo_data'])
        if site['whois_data']:
            site['whois_data'] = json.loads(site['whois_data'])
        if site['last_contact_date']:
            site['last_contact_date'] = json.loads(site['last_contact_date'])
    return render_template('sites/update.html', site=site,
                           categories=categories,
                           webmasters=webmasters)


@bp.route('/<int:id>/delete', methods=('POST', 'GET'))
@login_required
def delete(id):
    db = get_db()
    db.execute('DELETE FROM sites WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('sites.index'))


@bp.route('/<int:id>/contact', methods=('GET', 'POST'))
@login_required
def contact(id):
    import os
    from web_app.funcs import save_mails_to_db as save_to_db

    if request.method == 'POST':
        print(request.form)

        if request.form['contact_type']:
            type_contact, contact = request.form['contact_type'].split(':')
            contact_text = ' '.join(
                [request.form['mail_title'], request.form['mail_text']])
            contact_date = time.time()

            if type_contact == 'mail':
                uniq_gen = f'SEND_WH_{int(contact_date)}'
                title, body = (
                    request.form['mail_title'], request.form['mail_text'])
                assert mail_funcs.send_mail(contact, title, body)

                save_to_db('SEND', contact_date,
                           f'{int(contact_date)}@mail.yandex.ru', uniq_gen,
                           contact, os.environ.get('MAIL_USER'),
                           title, body)
            db = get_db()
            if (last_contact_db := db.execute('SELECT last_contact_date FROM sites'
                ' WHERE id = ?', (id,)).fetchone()):
                if (contact_date_db := last_contact_db['last_contact_date']):
                    status = json.loads(contact_date_db)['status']
            last_contact_date = json.dumps({
                'date': contact_date,
                'status': 'pending' if (not contact_date_db or not status in ['waite_publishing', 'publishing']) else status
            })

            # TODO: Incapsule to some function
            db.execute(
                'INSERT INTO contact_history (site_id, contact_type,'
                'contact, contact_text, contact_date)'
                'VALUES (?, ?, ?, ?, ?)', (id, type_contact,
                                           contact, contact_text, contact_date)
            )
            db.execute(
                'UPDATE sites SET last_contact_date = ?'
                'WHERE id = ?', (last_contact_date, id)
            )
            db.commit()

    site = get_db().execute(
        'SELECT * FROM sites LEFT OUTER'
        ' JOIN webmasters AS web ON sites.webmaster_id = web.id LEFT OUTER'
        ' JOIN categories AS cat ON sites.category_id = cat.id'
        ' WHERE sites.id == ?', (id,)

    ).fetchone()

    pattern = get_db().execute(
        'SELECT patterns FROM settings'
        ' WHERE user_id == ?', (str(g.user['id']))
    ).fetchone()

    # Get last 5 contacts from contact_history
    contact_history = get_db().execute(
        'SELECT * FROM contact_history'
        ' WHERE site_id == ? ORDER BY contact_date DESC', (id,)
    ).fetchall()[:5]

    if pattern:
        pattern = dict(pattern)['patterns']
        pattern = json.loads(pattern)
        pattern['title'] = mail_funcs.random_sentence(pattern['title'])
        pattern['body'] = mail_funcs.random_sentence(pattern['body'])

    if not site or (not site['contact_form_link']) and (not site['webmaster_id']):
        abort(404, f'Contacts for ({id}) not found.')
    contacts = []
    if site['contact_form_link']:
        contacts.append(('link', site['contact_form_link']))
    if site['contacts']:
        for contact in json.loads(site['contacts']):
            contacts.append((contact['contact_type'], contact['contact']))

    emails = []
    for contact in contacts:
        if contact[0] == 'mail':
            emails.append(contact[1])

    def delete_answer_in_mail(raws):
        """
        Delete answer in mails.
        Return dict with all raws

        RegEx searching template like:
            Среда, 13 февраля 2019
        """
        raws['body'] = re.sub(
            r'\s((\d{2}.\d{2}.\d{4}.*)|(\w{2},\s\d{1,2}\s\w{2,3}.*)|\w{3,},\s\d{2}.*\d{4}.*)', '', raws['body'])
        return raws

    # TODO: Change mail status with AJAX or something else

    mails_send = get_db().execute(
        f"SELECT * FROM mails WHERE to_name IN ({','.join(['?']*len(emails))}) AND mail_box == ? ORDER BY mail_date DESC", (*emails, 'SEND')).fetchall() if emails else []
    mails_send = [delete_answer_in_mail(dict(sql_raw))
                  for sql_raw in mails_send]
    mails_received = get_db().execute(
        f"SELECT * FROM mails WHERE from_name IN ({', '.join(['?']*len(emails))}) AND mail_box == ? ORDER BY mail_date DESC", (*emails, 'INBOX')).fetchall() if emails else []
    mails_received = [delete_answer_in_mail(dict(sql_raw))
                      for sql_raw in mails_received]

    mails = sorted(mails_send + mails_received,
                   key=lambda x: x['mail_date'], reverse=True)

    return render_template('sites/contact.html',
                           site=site,
                           contacts=contacts,
                           contact_history=contact_history,
                           pattern=pattern,
                           mails_send=mails_send,
                           mails_received=mails_received,
                           mails=mails)
