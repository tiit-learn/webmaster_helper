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
    from pyppeteer_stealth import stealth

    proxy = False
    if os.getenv('PROXY_WORK') and os.getenv('PROXIE_DOMAIN'):
        proxy = True
        proxy_domain = 'http://%s:%s' % (os.getenv('PROXIE_DOMAIN'),
                                         os.getenv('PROXIE_PORT'))
        setup_proxy_link = f'--proxy-server={proxy_domain}'
    browser = await launch({"headless": True,
                            'args': ['' if not proxy else setup_proxy_link,
                                     '--no-sandbox',
                                     '--single-process',
                                     '--disable-dev-shm-usage',
                                     '--disable-gpu',
                                     '--no-zygote',
                                     '--start-maximized',
                                     '--disable-setuid-sandbox',
                                     '--disable-infobars',
                                     '--window-position=0,0',
                                     '--ignore-certifcate-errors',
                                     '--ignore-certifcate-errors-spki-list',
                                     '--lang=en-EN']})

    page = await browser.newPage()
    await stealth(page)
    await page.setUserAgent(Headers(headers=True).generate()['User-Agent'])

    if os.getenv('PROXY_WORK') and all((os.getenv('PROXIE_USERNAME'),
                                        os.getenv('PROXIE_PASSWORD'))):
        await page.authenticate({
            'username': os.getenv('PROXIE_USERNAME'),
            'password': os.getenv('PROXIE_PASSWORD')
        })
    await page.goto('https://google.com')

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


async def get_seo_data(url_data):
    """
    Функция получения seo данных для указанного сайта. Полученные данные
    сохраняет в БД.
    """
    # TODO: Create 1 puppeteer chrome window. For all services need create tabs.
    # TODO: Refactoring code
    try:
        from web_app.funcs import save_seo_to_db as save_to_db

        asession = get_browser(_async=True)
        doc = """<script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script><a href='https://httpbin.org'>"""

        result = json.loads(url_data['seo_data']
                            ) if url_data['seo_data'] else {}

        url = url_data['domain']

        async def get_alexa():
            if not result.get('alexa') or (result.get('alexa') and
                                           (time.time() - result['alexa']['timedata'] > 864000)):
                try:
                    response = await asession.get("https://alexa.com/siteinfo/" + url)
                except Exception as err:
                    print('Ошибка %s:' % url, err)
                else:
                    print(response.html.find('title', first=True).text)
                    script = response.html.xpath(
                        '//script[contains(text(),"lifecycle_stage")]', first=True)
                    if script:
                        script = script.text + ' dataLayer[0]["siteinfo"]'
                        html = requests_html.HTML(html=doc, async_=True)
                        try:
                            val = await html.arender(script=script, reload=False)
                            result['alexa'] = {
                                'data': val if val else None, 'timedata': time.time()}
                        except Exception as err:
                            print('Ошибка Alexa %s:' % url, err)
                    else:
                        result['alexa'] = {
                            'data': None, 'timedata': time.time()}
                    response.close()

        async def get_simularweb():
            if not result.get('simularweb') or (result.get('simularweb') and (time.time() - result['simularweb']['timedata'] > 864000)):
                pattern = r'// lazy loader|//siteInfo: true,'
                _url = "https://www.similarweb.com/ru/website/" + url
                page = await get_pyppe()
                try:
                    await page.goto(_url)
                except Exception as err:
                    print('Ошибка %s:' % _url, err)
                else:
                    title = await page.title()
                    html = await page.evaluate('document.documentElement.outerHTML', force_expr=True)
                    html = requests_html.HTML(html=html, async_=True)
                    if (script := html.xpath(
                            '//script[contains(text(),"Sw.preloadedData")]', first=True)):
                        print(url, title)
                        script = 'let Sw = []; ' + \
                            re.sub(pattern, '', script.text) + \
                            ' Sw.preloadedData.overview'
                        html = requests_html.HTML(html=doc, async_=True)
                        val = await html.arender(script=script, reload=False)
                        result['simularweb'] = {
                            'data': val, 'timedata': time.time()}
                    elif (script := html.xpath('//div[@class="Title"]', first=True).text) == 'Pardon Our Interruption...':
                        print(url, title, '- CAPTCHA')
                    else:
                        print(url, title, '- NOT FOUND')
                        result['simularweb'] = {
                            'data': None, 'timedata': time.time()}
                finally:
                    await page.browser.close()

        async def get_moz():
            if not result.get('moz') or (result.get('moz') and (time.time() - result['moz']['timedata'] > 864000)):

                _url = "https://moz.com/domain-analysis?site=" + url
                page = await get_pyppe()
                try:
                    await page.goto(_url)
                except Exception as err:
                    print('Ошибка %s:' % _url, err)
                else:
                    title = await page.title()
                    print(title)
                    html = await page.evaluate('document.documentElement.outerHTML', force_expr=True)
                    html = requests_html.HTML(html=html, async_=True)
                    if html.xpath('//div[contains(@class, "align-items-center")]/div[1]/h1',
                                  first=True):
                        val = {
                            'da': html.xpath('//div[contains(@class, "align-items-center")]/div[1]/h1',
                                             first=True).text,
                            'links': html.xpath('//div[contains(@class, "align-items-center")]/div[2]/h1',
                                                first=True).text,
                            'keys_rank': html.xpath('//div[contains(@class, "align-items-center")]/div[3]/h1',
                                                    first=True).text,
                            'spam_score': html.xpath('//div[contains(@class, "align-items-center")]/div[4]/h1',
                                                     first=True).text
                        }
                        # await asyncio.sleep(0.5)
                        result['moz'] = {'data': val, 'timedata': time.time()}
                    else:
                        result['moz'] = {'data': None, 'timedata': time.time()}
                finally:
                    await page.browser.close()

        async def yandex_x():
            if not result.get('yandex_x') or (result.get('yandex_x') and (time.time() - result['yandex_x']['timedata'] > 864000)):
                try:
                    response = await asession.get("https://webmaster.yandex.ru/siteinfo/?site=" + url)
                except Exception as err:
                    print('Ошибка %s:' % url, err)
                else:
                    script = response.html.xpath(
                        '//script[contains(text(),"bh.lib.data")]', first=True)
                    if script:
                        print(url, response.html.find(
                            'title', first=True).text)
                        script = 'let bh = {}; bh["lib"] = {}; ' + \
                            script.text + r'; bh.lib.data'
                        html = requests_html.HTML(html=doc, async_=True)
                        val = await html.arender(script=script, reload=False)
                        result['yandex_x'] = {
                            'data': val, 'timedata': time.time()}
                    elif "Подтвердите, что запросы отправляли вы, а не робот" in response.html.text:
                        print(url, 'Yandex - CAPTCHA')
                    else:
                        print(url, 'Yandex - NOT FOUND')
                        result['yandex_x'] = {
                            'data': None, 'timedata': time.time()}
                    response.close()

        try:
            await asyncio.gather(
                get_alexa(),
                get_simularweb(),
                get_moz(),
                yandex_x()
            )
            # TODO: Create new function for getting whois data.
            whois_data = await asyncio.get_event_loop().run_in_executor(None, get_whois, url, url_data['whois_data'])
        except Exception as err:
            print('Ошибка в (get_seo_data) %s: %s' % (url, err))
        else:
            await asyncio.get_event_loop().run_in_executor(None, save_to_db, url_data['id'], result, whois_data)

    except Exception as err:
        print('ОШИБИЩЕ', err)


async def get_sites_data(sites):
    if os.getenv('PROXY_WORK'):
        await proxy_setup()
    # TODO: Incapsule THIS №1
    try:
        coros = [get_seo_data(site) for site in sites]
        await asyncio.gather(*coros)
    except Exception as err:
        print('Ошибка в (get_sites_data)', err)


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

    session = await get_pyppe()

    try:
        coros = [check_post_on_site(site, session) for site in pages_list]
        await asyncio.gather(*coros)
    except Exception as err:
        print('Ошибка в (check_post)', err)

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
