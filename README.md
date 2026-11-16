This is a Real estate application developed for a dummy company named BT Real Estate. I used Django to develop this application.

## Running locally

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

By default the app uses a local PostgreSQL database named `btredb`. Set `DB_ENGINE=sqlite` to use SQLite instead (handy for a quick try or for running the tests with `python manage.py test`).

## Configuration

Settings are read from environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | development-only key | Django secret key. Set a long random value in production. |
| `DEBUG` | `True` | Set to `False` in production. |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated host names the site is served on. |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | `btredb`, `postgres`, empty, `localhost`, `5432` | PostgreSQL connection. |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | empty | Gmail address and [app password](https://myaccount.google.com/apppasswords) used to email inquiries to realtors. Without them, emails are printed to the console. |
