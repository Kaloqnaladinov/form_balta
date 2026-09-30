# Forn Baltà Flask + SQLite

Python 3.10+, Flask, SQLite, Jinja2, Tailwind CDN, vanilla JS.

## Run locally
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py

Public: http://127.0.0.1:5000
Admin: http://127.0.0.1:5000/admin/login

Demo login:
admin@fornbalta.cat
123456

Change SECRET_KEY and the admin password before production. Seed prices/products are demo content and must be verified with the bakery.

## Linux production
Use Gunicorn behind Nginx/Caddy:
gunicorn --workers 2 --bind 127.0.0.1:8000 app:app
Back up forn_balta.db regularly.
