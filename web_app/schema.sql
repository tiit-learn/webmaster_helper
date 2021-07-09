DROP TABLE IF EXISTS sites;
DROP TABLE IF EXISTS webmasters;
DROP TABLE IF EXISTS mails;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS categories;


CREATE TABLE sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    webmaster_id INTEGER,
    category TEXT NOT NULL,
    domain TEXT UNIQUE NOT NULL,
    alexa_rank INTEGER,
    yandex_x INTEGER,
    whois_data TEXT,
    contact_form_link TEXT,
    price INTEGER,
    published BOOLEAN NOT NULL,
    notes TEXT,
    FOREIGN KEY (webmaster_id) REFERENCES webmasters (id)
);

CREATE TABLE webmasters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    webmaster_name TEXT,
    contacts TEXT NOT NULL
);

CREATE TABLE mails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER,
    site TEXT,
    status_mail TEXT NOT NULL,
    from_name TEXT,
    to_name TEXT,
    body TEXT NOT NULL,
    FOREIGN KEY (site_id) REFERENCES sites (id)
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_name TEXT UNIQUE NOT NULL,
    user_password TEXT NOT NULL
);

CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);