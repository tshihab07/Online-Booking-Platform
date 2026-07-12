# Bookify Online Booking SaaS

Bookify is a multi-tenant Django booking platform for salons, restaurants, hospitals, hotels, and event businesses. Business owners can create a booking page, manage services and staff, accept bookings, use branded themes, and send email notifications.

This README intentionally lists configuration names only. Do not paste real `.env` values, secrets, database URLs, API keys, passwords, or webhook secrets into this file.

## Features

- Multi-tenant business pages at `/b/<slug>/`
- Business onboarding and dashboard
- Service, staff, customer, calendar, and analytics screens
- Public booking flow with availability lookup
- Stripe checkout and webhook support
- Celery background tasks
- Redis support for Celery and Django cache
- Email confirmations and reminders
- 25 theme definitions: 5 themes for each supported business type
- KGB platform admin at `/kgb-admin/` (users, businesses, bookings, payments, support, plans, announcements)
- OpenAPI docs at `/docs/` (Swagger) and `/docs/redoc/`
- Subscription plan limits enforced per tier (services, staff, bookings, API access)

## Tech Stack

- Python 3.12+
- Django
- MongoDB Atlas with `django-mongodb-backend`
- Redis, either local Redis or a free hosted Redis provider
- Celery
- Stripe
- Django REST Framework
- Tailwind CSS via CDN
- WhiteNoise for static files

## Project Structure

```text
accounts/       User accounts and auth views
analytics/      Analytics pages
api/            REST API views, serializers, permissions
bookings/       Public booking flow and booking utilities
businesses/     Business dashboard, services, staff, settings
config/         Django settings, URLs, Celery app
core/           Home page, middleware, context processors, template tags
notifications/  Email templates, notification helpers, Celery tasks
payments/       Stripe checkout and payment views
platform_admin/ KGB admin panel, plans, limits, announcements
themes/         Theme registry and theme rendering helpers
templates/      Shared base templates and layout includes
static/         CSS and JavaScript assets
```

## Configuration

Create a `.env` file in the project root. Keep it local and private.

Required project settings:

```text
SECRET_KEY
DEBUG
ALLOWED_HOSTS
BASE_URL
```

Required MongoDB settings:

```text
MONGODB_CONNECTION_STRING
MONGODB_NAME
```

Required email settings:

```text
EMAIL_HOST
EMAIL_PORT
EMAIL_HOST_USER
EMAIL_HOST_PASSWORD
EMAIL_USE_TLS
```

Required Stripe settings:

```text
STRIPE_PUBLIC_KEY
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
```

Redis settings:

```text
REDIS_URL
CELERY_BROKER_URL
CELERY_RESULT_BACKEND
```

`REDIS_URL` is the main value used by the project. `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` are optional overrides; if you omit them, both default to `REDIS_URL`.

AllAuth setting (use exactly `none`, `optional`, or `mandatory`):

```text
ACCOUNT_EMAIL_VERIFICATION
```

Platform admin (KGB panel at `/kgb-admin/`):

```text
ADMIN_USERNAME
ADMIN_PASSWORD
```

Django superuser (`python manage.py create_superuser`):

```text
SUPERUSER_EMAIL
SUPERUSER_PASSWORD
SUPERUSER_USERNAME
```

CORS and local debug helpers:

```text
CORS_ALLOWED_ORIGINS
INTERNAL_IPS
```

Twilio is not required and is not configured by this project.

## Redis Free Tier Setup

Use a hosted Redis provider with a free tier, such as Redis Cloud, Upstash, Railway, Render, or another provider you prefer.

The information needed from the Redis provider is:

- Public Redis connection URL
- Username, if your provider requires one
- Password or token
- Host
- Port
- TLS requirement, if the provider uses `rediss://`
- Database number, if the provider exposes one

Put the final Redis connection string in `.env` as `REDIS_URL`. For local Redis, the default shape is:

```text
redis://localhost:6379/0
```

For a hosted free tier, your provider will usually give a URL shaped like one of these:

```text
redis://default:<password>@<host>:<port>/0
rediss://default:<password>@<host>:<port>/0
```

Do not commit the real URL. It contains credentials.

## Theme System

Theme definitions live in:

```text
themes/theme_utils.py
```

The current registry includes 5 themes for each business type:

- `salon`
- `restaurant`
- `hospital`
- `hotel`
- `event`

The dashboard settings page reads those definitions and displays the available themes for the active business type.

## Setup

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Then create and fill your private `.env` file.

Run database migrations:

```bash
python manage.py migrate
```

Bootstrap platform data and optional demo tenants:

```bash
python manage.py create_superuser
python manage.py init_platform --demo
```


```bash
python manage.py collectstatic --noinput
```

## Running Locally

Terminal 1, Django:

```bash
source .venv/bin/activate
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

Terminal 2, Celery worker:

```bash
source .venv/bin/activate
celery -A config worker --loglevel=info
```

If you use local Redis instead of a hosted free tier, start Redis in another terminal before Celery:

```bash
redis-server
```

If you use hosted Redis, you do not run `redis-server`; the app connects through `REDIS_URL`.

## Useful URLs

```text
/                         Home page
/signup/                  Create an account
/login/                   Sign in
/dashboard/               Business dashboard
/dashboard/onboarding/    Create the first business
/dashboard/settings/      Theme and business settings
/b/<slug>/                Public booking page
/kgb-admin/               Platform admin panel (env credentials)
/admin/                   Django admin (superuser)
/docs/                    API documentation (Swagger UI)
/docs/redoc/              API documentation (ReDoc)
/api/v1/                  REST API routes
```

## Fixing The `Invalid filter: 'split'` Error

The homepage previously contained unused template loops using the custom `split` filter. Those loops have been removed from `core/templates/core/home.html`.

If the error appears elsewhere, confirm the template has:

```django
{% load booking_tags %}
```

The filter itself lives in:

```text
core/templatetags/booking_tags.py
```

## Development Checks

Run Django checks:

```bash
python manage.py check
```

Run tests:

```bash
python manage.py test
```

Check for pending migrations after model edits:

```bash
python manage.py makemigrations --check --dry-run
```

## Notes

- Keep `DEBUG=True` only for local development.
- Set `DEBUG=False` in production and configure real `ALLOWED_HOSTS`.
- Never commit `.env`, database credentials, Redis URLs, Stripe keys, email passwords, or webhook secrets.
- Rotate any secret that has been pasted into a browser error page, chat, commit, or README.
