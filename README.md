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

TODO:
- [ ] Send mails from system
- [ ] Checking adv status in site

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
