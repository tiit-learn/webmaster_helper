# Webmaster Helper
Its simple CRM script for webmasters. You can write messages to another
webmasters and fix price for advertise your content. Script can check publish
your adv content and notification you to Telegram or Email, if something
changes.

![Main page](/img/main_page.png)

DONE:
- [x] Registration / Authorization system
- [x] Store data in SQLite database
- [x] Async get seo data for sites
- [x] Reciev mails from mail system
- [x] Send mails from system
- [x] Checking adv status in site

## Adding sites
You can add any count of sites to monitor your contacts with webmasters and
publishing link.

![Add site](/img/adding_site.png)

## Adding webmasters
Also you can add any counts of webmasters and contacts data.

![Add webmaster](/img/adding_webmaster.png)

## Script work:
- Python 3.7+
- Flask
- SQLite
- pyppeteer
- Bulma / jquery / Vue

## For Chrome webdriver

sudo apt install gconf-service libasound2 libatk1.0-0 libatk-bridge2.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 ca-certificates fonts-liberation libnss3 lsb-release xdg-utils wget libcairo-gobject2 libxinerama1 libgtk2.0-0 libpangoft2-1.0-0 libthai0 libpixman-1-0 libxcb-render0 libharfbuzz0b libdatrie1 libgraphite2-3 libgbm1
