import imapclient
import email.utils
import os
import re
import random
import smtplib
import pyzmail

from email.mime.text import MIMEText
from email.header import Header

from bs4 import BeautifulSoup as soup


def randomize(match):
    "Function return 1 word before randomizer"
    res = match.group(1).split('|')
    random.shuffle(res)
    return res[0]


def random_sentence(tpl):
    "Function sub all find patterns and randomize it"
    return re.sub(r'{(.*?)}', randomize, tpl)


def get_user_mails():
    """
    Function to get mails from user email and store it on DB.
    Parse and collect maila data to
        box - mail box dir
        date - mail reciev date
        uniq_id - Message-ID from mail variable
        uniq_gen - uniq text ID of email + box dir name
        mail_to - to email address from mail variables
        mail_from - from email address from mail variable
        title - subject of mail
        body - body text of mail
    """
    from web_app.funcs import save_mails_to_db as save_to_db
    from web_app.funcs import check_emails_in_db

    username = os.environ.get('MAIL_USER')
    password = os.environ.get('MAIL_USER_PSWD')

    re_pattern = re.compile(r'(\n|\r|\t|\xa0){1,}')

    if not all((username, password)):
        raise ValueError('Необходимо установить переменные ОС. "MAIL_USER" и "MAIL_USER_PSWD"\n'
                         '\t\t$env:MAIL_USER="...", $env:MAIL_USER_PSWD="..."')

    with imapclient.IMAPClient('imap.yandex.com', ssl=True) as imap:
        imap.login(username, password)
        # breakpoint()
        for box in ['INBOX', 'Отправленные', 'Исходящие']:
            imap.select_folder(box, readonly=True)
            if box in ['Отправленные', 'Исходящие']:
                box = 'SEND'
            msg_ids = imap.search(['ALL'])
            msg_ids = check_emails_in_db(msg_ids, box)
            for msg_id in msg_ids:
                uniq_gen = f"{box}_{msg_id}"
                # Getting mail raws
                rawMessage = imap.fetch(msg_id, ['BODY[]'])
                message = pyzmail.PyzMessage.factory(
                    rawMessage[msg_id][b'BODY[]'])
                # Getting uniq ID of mail
                uniq_id = message.get_decoded_header('Message-ID')
                uniq_id = re.sub(r'<|>', '', uniq_id)
                # Getting date of mail
                date = message.get('Date')
                date = email.utils.parsedate_to_datetime(date).timestamp()
                # Getting subject of mail
                title = message.get_subject().strip()
                # Getting mail From
                mail_from = message.get_addresses('from')[0][-1]
                # Getting mail To\
                mail_to = message.get_addresses('to')[0][-1]
                # Getting body of mail
                if (body := message.text_part) and not message.html_part:
                    if (charset := body.charset) == 'win-1251':
                        charset = 'cp1251'
                    body = body.get_payload().decode(charset if charset else 'ISO-8859-1')
                elif (body := message.html_part):
                    if (charset := body.charset) == 'win-1251':
                        charset = 'cp1251'
                    body = body.get_payload().decode(charset if charset else 'ISO-8859-1')
                    body = re.sub(r'<br />|<br>', ' ', body)
                    body = soup(body, 'lxml').text.strip()
                body = re.sub(re_pattern, ' ', body)
                # Remove more then 1 spaces in mail body text
                body = re.sub(r'\s+', ' ', body)

                print((' Mail [%d] ' % msg_id).center(80, "-"))
                print(('Subject:').ljust(5), title)
                print(('From:').ljust(5), mail_from)
                print(('To:').ljust(5), mail_to)
                print(('Body:').ljust(5), body)
                save_to_db(box, date,
                           uniq_id, uniq_gen,
                           mail_to, mail_from,
                           title, body)


def send_mail(email, title, body):
    """Function send mail to email and return True if all success or
    False if some errors.
    :param email: email of webmaster
    :param title: title of mail to webmaster
    :param body: body of mail ti webmaster
    """

    print(f'To: {email}. Send: {title} {body}')

    username = os.environ.get('MAIL_USER')
    password = os.environ.get('MAIL_USER_PSWD')

    with smtplib.SMTP_SSL('smtp.yandex.ru', 465) as smtp:
        smtp.ehlo()
        smtp.login(username, password)

        msg = MIMEText(body, "plain", 'utf-8')
        msg["Subject"] = Header(title, 'utf-8')
        msg["From"] = username
        msg["To"] = email

        try:
            smtp.sendmail(username, email, msg.as_string())
        except Exception:
            return False
        else:
            return True
