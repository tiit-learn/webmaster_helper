import imaplib
import email
import os
import re
import random
import smtplib

from email.mime.text import MIMEText
from email.header import Header

from bs4 import BeautifulSoup as soup
from email.header import decode_header

def randomize(match):
    "Function return 1 word before randomizer"
    res = match.group(1).split('|')
    random.shuffle(res)
    return res[0]


def random_sentence(tpl):
    "Function sub all find patterns and randomize it"
    return re.sub(r'{(.*?)}', randomize, tpl)

def get_user_mails():
    """Function to get mails from user email and store it on DB."""
    from web_app.funcs import save_mails_to_db as save_to_db

    username = os.environ.get('MAIL_USER')
    password = os.environ.get('MAIL_USER_PSWD')

    if not all((username, password)):
        raise ValueError('Необходимо установить переменные ОС. "MAIL_USER" и "MAIL_USER_PSWD"\n'
                         '\t\t$env:MAIL_USER="...", $env:MAIL_USER_PSWD="..."')
    
    imap = imaplib.IMAP4_SSL('imap.yandex.com')
    imap.login(username, password)

    status, messages = imap.select('INBOX')

    N = 50

    messages = int(messages[0])

    for i in range(messages, messages-N, -1):
        res, msg = imap.fetch(str(i), "(RFC822)")
        body = ""
        for response in msg:
            if isinstance(response, tuple):
                print(''.center(80, '='),'\n')
                msg = email.message_from_bytes(response[1])
                id_msg = decode_header(msg.get('Message-Id'))[0][0]
                subject, encoding = decode_header(msg.get('Subject'))[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding)
                From, encoding = decode_header(msg.get('From'))[0]
                if len(decode_header(msg.get('From'))) > 1:
                    Email, _ = decode_header(msg.get('From'))[-1]
                    Email = Email.decode(_ if _ else 'utf-8').strip()
                    Email = re.sub(r'<|>|" ', '', Email).strip()
                else:
                    From, Email = From.split(' <')
                    Email = re.sub(r'<|>', '', Email)

                To_email = decode_header(msg.get('To'))[0][0].split('<')
                To_email = To_email[-1].replace('>', '')
                if isinstance(From, bytes):
                    From = From.decode(encoding if encoding else 'utf8')
                    From = re.sub(r'<|>', '', From)

                if msg.is_multipart():
                    _body = []
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        charset = part.get_charsets()[0]
                        content_disposition = str(part.get('Content-Disposition'))
                        try:
                            body = part.get_payload(decode=True).decode(charset)
                        except:
                            pass
                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            if body:
                                _body.append(body)
                    body = '. '.join(_body)
                else:
                    content_type = msg.get_content_type()
                    body = msg.get_payload(decode=True).decode()
                
                if content_type == "text/html":
                    body = soup(body, 'lxml').text.strip()

                body = re.sub('\n{2,}', "\n", body)
                body = re.sub('\r', "", body)

                print('Subject:', subject)
                print('From:', From, Email)
                print('Body: ', body[:200])

                print('')
                save_to_db(id_msg, To_email, Email, From, subject, body)
    print(''.center(80, '='))

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
        except:
            return False
        else:
            return True