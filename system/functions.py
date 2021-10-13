import asyncio
import itertools
import os
import random
import re
import requests_html
import time
import json
import platform
import subprocess

from fake_headers import Headers


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


def get_browser(_async=False):
    """
    Функция возвращает асинхронный браузер для быстрого получения данных.
    IMPORTANT: Function from requests_html, maybe need to replace requests_html
    to requests, bs4 and pyppeteer
    """

    asession = requests_html.AsyncHTMLSession(
            ) if _async else requests_html.HTMLSession()

    if _async:
        asession.__browser_args = ['--start-maximized',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--window-position=0,0',
                '--ignore-certifcate-errors',
                '--ignore-certifcate-errors-spki-list',
                '--lang=en-EN']

    # headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    #            'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2919.83 Safari/537.36',
    #         }
    headers = Headers(headers=False).generate()
    if os.getenv('PROXY_WORK'):
        proxies = {
                'http': f'http://{os.getenv("FULL_PROXY_LINK")}',
                'https': f'http://{os.getenv("FULL_PROXY_LINK")}'
                }
        asession.proxies.update(proxies)

    asession.headers.update(headers)

    return asession


async def get_pyppe():
    from pyppeteer import launch

    proxy = False
    if os.getenv('PROXY_WORK') and os.getenv('PROXIE_DOMAIN'):
        proxy = True
        proxy_domain = 'http://%s:%s' % (os.getenv('PROXIE_DOMAIN'),
                os.getenv('PROXIE_PORT'))
        setup_proxy_link = f'--proxy-server={proxy_domain}'
    browser = await launch({"headless": True,
        'args': ['' if not proxy else setup_proxy_link,
            '--no-sandbox',
            #'--single-process',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--no-zygote',
            '--start-maximized',
            '--disable-setuid-sandbox',
            '--disable-infobars',
            '--window-position=0,0',
            '--ignore-certifcate-errors',
            '--ignore-certifcate-errors-spki-list',
            '--lang=en-EN']},
        handleSIGINT=False,
        handleSIGTERM=False,
        handleSIGHUP=False)
    return browser

async def get_pyppe_page(browser):
    from pyppeteer_stealth import stealth

    page = await browser.newPage()
    await stealth(page)
    await page.setUserAgent(Headers(headers=True).generate()['User-Agent'])

    if os.getenv('PROXY_WORK') and all((os.getenv('PROXIE_USERNAME'),
        os.getenv('PROXIE_PASSWORD'))):
        await page.authenticate({
            'username': os.getenv('PROXIE_USERNAME'),
            'password': os.getenv('PROXIE_PASSWORD')
            })

    # Get ip of Page
    # await page.goto('http://ip-api.com/json/')
    # await page.content()
    # innerJson = await page.evaluate('() =>  {return JSON.parse(document.querySelector("body").innerText);}');
    # print(f'IP: [{innerJson["countryCode"]}] {innerJson["query"]}')

    return page

def check_url(url):
    """
    Функция проверки URL. Если, после разбивки строки, полученный список
    имеет длину больше 1, токая строка считается URL
    Разбивка происходит по символам '. '
    """
    if len(url.split('.')) > 1:
        return True
    return False


def remove_http(url):
    """
    Функция удаления протокола из строки URL. Удаляет http, https, ://, www., и
    конечный слеш в конце строки.
    """
    pattern = r'\/$|http(s)?\:\/\/|www\.'
    url = re.sub(pattern, '', url).lower().strip()
    return url


def get_whois_rows(domain):
    _domain = domain.split('.')
    _domain = _domain[-1] if len(_domain) == 2 else '.'.join(
            _domain[len(_domain) - 2:])
    # For all domaine like 'net', 'com', 'guru', 'org', 'info', 'gen.in', 'biz'
    rows = {
            'name_servers': 'Name Server',
            'create_date': 'Creation Date',
            'end_date': 'Expiration Date',
            'emails': 'Registrant Email',
            'organization': 'Registrant Organization',
            'registrar': 'Registrar'
            }
    # If special domain
    if _domain in ('ru', 'com.ua', 'xn--p1ai', 'rv.ua'):
        rows = {
                'name_servers': 'nserver',
                'create_date': 'created',
                'end_date': 'free-date',
                'emails': 'admin-contact',
                'organization': 'person',
                'registrar': 'registrar'
                }
    elif _domain in ('su'):
        rows = {
                'name_servers': 'nserver',
                'create_date': 'created',
                'end_date': 'free-date',
                'emails': 'e-mail',
                'organization': 'person',
                'registrar': 'registrar'
                }

    return rows


def parse_whois_data(domain, whois_data):

    domain_rows = get_whois_rows(domain)
    name_servers = set([i.lower().strip() for i in re.findall(
        rf'(?<={domain_rows["name_servers"]}:\s).+?(?=\r|\n)', whois_data)])
    create_date = set([i.lower().strip() for i in re.findall(
        rf'(?<={domain_rows["create_date"]}:\s).+?(?=\r|\n)', whois_data)])
    end_date = set([i.lower().strip() for i in re.findall(
        rf'(?<={domain_rows["end_date"]}:\s).+?(?=\r|\n)', whois_data)])
    emails = set([i.lower().strip() for i in re.findall(
        rf'(?<={domain_rows["emails"]}:\s).+?(?=\r|\n)', whois_data)])
    organization = set([i.lower().strip() for i in re.findall(
        rf'(?<={domain_rows["organization"]}:\s).+?(?=\r|\n)', whois_data)])
    registrar = set([i.lower().strip() for i in re.findall(
        rf'(?<={domain_rows["registrar"]}:\s).+?(?=\r|\n)', whois_data)])

    return (tuple(name_servers),
            tuple(create_date),
            tuple(end_date),
            tuple(emails),
            tuple(organization),
            tuple(registrar))


def get_whois(url, whois_data):
    """
    Функция получения WHOIS данных домена.
    """
    # Encoding URL for cyrilic domain
    url = url.encode('idna').decode('utf-8')
    whois_data = json.loads(whois_data) if whois_data else {}
    if not whois_data or time.time() - whois_data['timedata'] > 864000:
        if platform.system() == 'Windows':
            """
                Windows 'whois' command wrapper
            """
            if not os.path.exists('whois.exe'):
                print("downloading dependencies")
                folder = os.getcwd()
                copy_command = r"copy \\live.sysinternals.com\tools\whois.exe " + folder
                subprocess.call(
                        copy_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            result = subprocess.run(
                    [r'.\whois.exe', url], stdout=subprocess.PIPE)
            if result.returncode != 0 and result.returncode != 1:
                print('Что то не так!', url)

            result = result.stdout.decode('utf-8')
        else:
            """
                Linux 'whois' command wrapper
            """
            result = subprocess.Popen(['whois', url], stdout=subprocess.PIPE, encoding='UTF-8')
            result = result.stdout.read()

        (name_servers,
                create_date,
                end_date,
                emails,
                organization,
                registrar) = parse_whois_data(url, result)

        result_whois = {
                'name_servers': name_servers,
                'create_date': create_date,
                'end_date': end_date,
                'emails': emails,
                'organization': organization,
                'registrar': registrar,
                'timedata': time.time()
                }

        return result_whois
    # print('Данные WHOIS актуальны\n')
    return None

async def parse_site(browser, url, result, site_setup):
    """
    Function parse seo data from `site_setup` analytics seo sites and collect
    in to dict. Then return dict with seo data or None if seo data does not
    exist or was some error in loads.

    :browser: - pyppeteer browser Object
    :url: - str() - url of site which need to get seo data
    :result: - dict() - data of site in db
    :site_setup: - dict() - with settings for parsing site

    return dict() or None
    """
    try:
        if not result.get(site_setup['name']) or (result.get(site_setup['name']) and
                    (time.time() - result[site_setup['name']]['timedata'] > 864000)):
            page = await get_pyppe_page(browser)
            await page.goto(site_setup['url'] + url)
            title = await page.title()
            body_text = await page.evaluate('document.body.innerText', force_expr=True)
            print(f'[{site_setup["name"]}] -> #LOAD {url} - {title}')
            checker = await page.xpath(site_setup['check_xpath'])
            if checker:
                if (js_var_name := site_setup['js_var_name']):
                    # If need get seo data from js variable on the seo site
                    data = await page.evaluate(js_var_name)
                if (parse := site_setup['parse']):
                    # If need to parse some field for get seo data
                    data = {}
                    for (key, value) in parse.items():
                        element = await page.xpath(value)
                        if element:
                            data[key] = await page.evaluate('(element) => element.textContent', element[0])
            elif ((
                captcha := site_setup.get('captcha_title')) and captcha in title) or ((
                captcha := site_setup.get('captcha_body')) and captcha in body_text):
                raise ValueError('Some CAPTCHA on page')
            else:
                print(f'\t[{site_setup["name"]}] -> #WARN {url}: `None` Data')
                data = None
            return {site_setup['name']: {'data': data, 'timedata': time.time()}}
    except Exception as err:
            print(f'\t[{site_setup["name"]}] -> #ERROR {url}: {err}')
    return None

async def get_seo_data(browser, url_data):
    """
    Функция получения seo данных для указанного сайта. Полученные данные
    сохраняет в БД.
    """
    from web_app.funcs import save_seo_to_db, save_whois_to_db

    result = json.loads(url_data['seo_data']
            ) if url_data['seo_data'] else {}

    url = url_data['domain']

    seo_data = {}
    seo_sites = (
            {'name': 'alexa',
                'url': 'https://alexa.com/siteinfo/',
                'js_var_name': 'dataLayer[0]["siteinfo"]',
                'parse': False,
                'check_xpath': '//script[contains(text(),"lifecycle_stage")]'
                },
            {'name': 'yandex_x',
                'url': 'https://webmaster.yandex.ru/siteinfo/?site=',
                'js_var_name': 'bh.lib.data',
                'parse': False,
                'check_xpath': '//script[contains(text(),"bh.lib.data")]',
                'captcha_title': 'Ой!'
                },
            {'name': 'simularweb',
                'url': 'https://www.similarweb.com/ru/website/',
                'js_var_name': 'Sw.preloadedData.overview',
                'parse': False,
                'check_xpath': '//script[contains(text(),"Sw.preloadedData")]',
                'captcha_body': 'Pardon Our Interruption...'
                },
            {'name': 'moz',
                'url': 'https://moz.com/domain-analysis?site=',
                'js_var_name': False,
                'parse': {
                    'da': '//div[contains(@class, "align-items-center")]/div[1]/h1',
                    'links': '//div[contains(@class, "align-items-center")]/div[2]/h1',
                    'keys_rank': '//div[contains(@class, "align-items-center")]/div[3]/h1',
                    'spam_score': '//div[contains(@class, "align-items-center")]/div[4]/h1'
                    },
                'check_xpath': '//div[contains(@class, "align-items-center")]/div[1]/h1',
                })
    coros = [parse_site(browser, url, result, site_setup) for site_setup in seo_sites]
    results = await asyncio.gather(*coros)

    for _result in results:
        if _result:
            result.update(_result)

    # TODO: Create new function for getting whois data.
    # whois_data = await asyncio.get_event_loop().run_in_executor(None, get_whois, url, url_data['whois_data'])
    # else:
        # await asyncio.get_event_loop().run_in_executor(None, save_whois_to_db, url_data['id'], whois)
    await asyncio.get_event_loop().run_in_executor(None, save_seo_to_db, url_data['id'], result)
    return {'domain': url, 'status': 'done'}


async def get_sites_data(sites):
    """
    Function create new pyppeteer browser and send it to collect all
    seo data from seo sites.
    """
    browser = await get_pyppe()

    if os.getenv('PROXY_WORK'):
        await proxy_setup()
    # TODO: Incapsule THIS №1
    try:
        coros = [get_seo_data(browser, url_data) for url_data in sites]
        await asyncio.gather(*coros)
    except Exception as err:
        print('Ошибка в (get_sites_data)', err)
    finally:
        await browser.close()

async def check_post_on_site(site, session):
    from web_app.funcs import save_to_db_check_post as save_to_db
    print(f'Обработка - {site["published_link"]}')
    result = {
            'date': time.time(),
            'status': None
            }
    url = 'http://' + site['published_link']

    browser = await session.browser.newPage()
    try:
        await browser.goto(url)
    except Exception as err:
        print(f'Ошибка ({url}): {err}')
    else:
        # WARNING: Need waiting for browser checker in some sites
        await asyncio.sleep(15)
        html = await browser.evaluate('document.documentElement.outerHTML', force_expr=True)
        html = requests_html.HTML(html=html, async_=True)
        if html.xpath(f'//a[contains(@href, {os.getenv("WORK_SITE")})]'):
            result = {
                    'date': time.time(),
                    'status': True
                    }
        save_to_db(site['id'], result)


async def check_post(pages_list):
    """
    Function try load page with published post and try find needed url on page.
    After checking url on page, function save status to DB and update
    date check.

    Parameters:
        pages_list (set): set of pages with published post.
    """
    # TODO: Incapsule THIS №1
    if not os.getenv("WORK_SITE"):
        raise ValueError(
                'Please set the "WORK_SITE" variable in your environment')
    browser = await get_pyppe()
    session = await get_pyppe_page(browser)

    try:
        coros = [check_post_on_site(site, session) for site in pages_list]
        await asyncio.gather(*coros)
    except Exception as err:
        print('Ошибка в (check_post)', err)
    await browser.close()

def effective_count(site_data):
    """
    Function recal all seo datas and return effective number of publishing.
    """
    print(site_data['domain'], end=" ")
    simularweb, alexa, moz, yandex_x, simular_search_source = 0,0,0,0,0
    if site_data['seo_data'] and site_data['price']:
        if (simularweb := site_data['seo_data'].get('simularweb', 0)):
            simular_search_source = simularweb['data']['TrafficSources']['Search']
            if isinstance(site_data['price'], str):
                site_data['price'] = float(site_data['price'].replace(',', '.'))
            simularweb = (10000000-simularweb['data']['GlobalRank'][0])/site_data['price']/1000000
        if (alexa := site_data['seo_data'].get('alexa', 0)):
            if alexa['data']:
                alexa = (10000000-alexa['data']['rank']['global'])/site_data['price']/1000000 
            else:
                alexa = 0
        if (moz := site_data['seo_data'].get('moz', 0)):
            if (moz := moz.get('data', 0)):
                moz = int(moz['da'])/site_data['price']
            else:
                moz = 0
        if (yandex_x := site_data['seo_data'].get('yandex_x', 0)):
            if (yandex_x := yandex_x['data'].get('quality', 0)):
                yandex_x = yandex_x['achievements'][-1]['sqi']/site_data['price']/10

    return ((simularweb + alexa + moz + yandex_x) + ((simularweb + alexa + moz + yandex_x) * simular_search_source))
