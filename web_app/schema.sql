DROP TABLE IF EXISTS sites;
DROP TABLE IF EXISTS webmasters;
DROP TABLE IF EXISTS mails;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS settings;


CREATE TABLE sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    webmaster_id INTEGER,
    category_id INTEGER NOT NULL,
    domain TEXT UNIQUE NOT NULL,
    contact_form_link TEXT,
    seo_data TEXT,
    whois_data TEXT,
    price INTEGER,
    published DATETIME,
    published_link TEXT,
    last_contact_date TEXT,
    last_check DATETIME, 
    notes TEXT,
    FOREIGN KEY (webmaster_id) REFERENCES webmasters (id),
    FOREIGN KEY (category_id) REFERENCES categories (id)
);

CREATE TABLE webmasters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    webmaster_name TEXT,
    contacts TEXT
);

CREATE TABLE mails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER,
    site TEXT,
    mail_box TEXT,
    mail_date TEXT,
    status_mail TEXT NOT NULL,
    uniq_gen TEXT UNIQUE NOT NULL,
    from_name TEXT,
    to_name TEXT,
    body TEXT NOT NULL,
    subject TEXT NOT NULL,
    status NUMERIC NOT NULL,
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

CREATE TABLE settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    patterns TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE contact_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL,
    contact TEXT,
    contact_type TEXT,
    contact_text TEXT,
    contact_date TEXT,
    FOREIGN KEY (site_id) REFERENCES sites (id)
);

INSERT INTO categories VALUES(0, '');
