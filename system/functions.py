import re

from urllib import parse

def check_url(url):
    if len(url.split('.')) > 1:
        return True
    return False

def remove_http(url):
    pattern = r'\/$|http(s)?\:\/\/|www\.'
    url = re.sub(pattern, '', url)
    return url