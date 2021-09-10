import json
import time
import re

from datetime import datetime
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
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


@bp.route('/')
def index():
    db = get_db()
    sites = db.execute(
        'SELECT * FROM sites LEFT OUTER'
        ' JOIN webmasters AS web ON sites.webmaster_id = web.id LEFT OUTER'
        ' JOIN categories AS cat ON sites.category_id = cat.id'
        ' ORDER BY sites.id DESC;'
    ).fetchall()

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

    return render_template('sites/index.html', sites=sites)


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
                'published_link = ?, published = ?, last_contact_date = ?'
                'WHERE id = ?', (url, category_id, notes, published, contact_form_link, price,
                                 webmaster_id, published_link, published, last_contact_date, id)
            )
            db.commit()
            return redirect(url_for('sites.index'))
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
            date = time.time()
            # TODO: Create fix all sending mails, not only mails
            if type_contact == 'mail':
                uniq_gen = f'SEND_WH_{int(date)}'
                title, body = (
                    request.form['mail_title'], request.form['mail_text'])
                assert mail_funcs.send_mail(contact, title, body)

                save_to_db('SEND', date,
                           f'{int(date)}@mail.yandex.ru', uniq_gen,
                           contact, os.environ.get('MAIL_USER'),
                           title, body)

            last_contact_date = json.dumps({
                'date': date,
                'status': 'pending'
            })
            db = get_db()
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

    # TODO: Add all emails to SQL query. Now send only emails[0]
    def delete_answer_in_mail(raws):
        """
        Delete answer in mails.
        Return dict with all raws
        """
        raws['body'] = re.sub(
            r'\s((\d{2}.\d{2}.\d{4}.*)|(\w{2},\s\d{1,2}\s\w{2,3}.*))', '', raws['body'])
        return raws

    mails_send = get_db().execute(
        'SELECT * FROM mails WHERE to_name == ? AND mail_box == ? ORDER BY mail_date DESC', (emails[0], 'SEND')).fetchall() if emails else []
    mails_send = [delete_answer_in_mail(dict(sql_raw))
                  for sql_raw in mails_send]
    mails_received = get_db().execute(
        'SELECT * FROM mails WHERE from_name == ? AND mail_box == ? ORDER BY mail_date DESC', (emails[0], 'INBOX')).fetchall() if emails else []
    mails_received = [delete_answer_in_mail(dict(sql_raw))
                      for sql_raw in mails_received]

    return render_template('sites/contact.html',
                           site=site,
                           contacts=contacts,
                           pattern=pattern,
                           mails_send=mails_send,
                           mails_received=mails_received)
