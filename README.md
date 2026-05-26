# Bookify — Multi-Tenant Online Booking SaaS Platform

A production-ready SaaS booking platform built with **Django 5.2**, **MongoDB Atlas**, and **Stripe**. Supports Salons, Restaurants, Hospitals, Hotels, and Event venues — each with 5 unique themes.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Tech Stack](#3-tech-stack)
4. [Project Structure](#4-project-structure)
5. [Data Flow](#5-data-flow)
6. [Setup & Installation](#6-setup--installation)
7. [Environment Variables](#7-environment-variables)
8. [Running the Project](#8-running-the-project)
9. [Theme System](#9-theme-system)
10. [Booking Engine](#10-booking-engine)
11. [Dashboard Features](#11-dashboard-features)
12. [API Documentation](#12-api-documentation)
13. [Deployment Guide](#13-deployment-guide)
14. [Advantages](#14-advantages)

---

## 1. Project Overview

Bookify is a **multi-tenant SaaS platform** where each business owner signs up, creates their business profile, and gets a fully branded public booking page at `/b/<slug>/`. Customers visit that page, browse services, pick a date/time from a live heatmap calendar, choose staff, and complete checkout — all without page reloads.

### Business Types Supported
| Type | Themes Available |
|------|-----------------|
| Salon & Spa | Rose Gold Luxe, Midnight Glam, Blush Minimal, Forest Spa, Urban Chic |
| Restaurant | Bistro Warm, Fine Dining, Fresh Garden, Street Food, Mediterranean |
| Hospital & Clinic | Clinical Blue, Healing Green, Pure White, Warm Care, Night Shift |
| Hotel & Resort | Grand Luxury, Boutique Modern, Tropical Resort, Mountain Lodge, Urban Suite |
| Event Management | Festival Bright, Corporate Event, Wedding Elegant, Sports Arena, Art Gallery |

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PUBLIC INTERNET                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │   Django Application    │
              │   (Gunicorn + Whitenoise)│
              └────────────┬────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐       ┌─────▼─────┐     ┌─────▼─────┐
   │  Core   │       │ Businesses│     │  Bookings │
   │ (SaaS   │       │ Dashboard │     │  Engine   │
   │  Home)  │       │           │     │           │
   └─────────┘       └─────┬─────┘     └─────┬─────┘
                           │                 │
              ┌────────────▼─────────────────▼────────────┐
              │           MongoDB Atlas                    │
              │  businesses / services / staff / bookings  │
              └────────────────────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │   External Services     │
              │  Stripe │ Redis/Celery  │
              └─────────────────────────┘
```

### Multi-Tenancy Model
- **Path-based**: `/b/<slug>/` — each business has a unique slug
- **Subdomain-based**: `<slug>.yourdomain.com` (requires DNS wildcard)
- `TenantMiddleware` resolves the business on every request and attaches `request.business`

---

## 3. Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend Framework | Django 5.2 |
| Database | MongoDB Atlas via `django-mongodb-backend` |
| Authentication | Django Allauth + Custom `CustomUser` |
| Payments | Stripe Checkout + Webhooks |
| Async Tasks | Celery + Redis |
| REST API | Django REST Framework |
| Frontend | Tailwind CSS (CDN) + Vanilla JS |
| Charts | Chart.js |
| Calendar | FullCalendar.js |
| QR Codes | `qrcode` library |
| Static Files | WhiteNoise |
| Production Server | Gunicorn |

---

## 4. Project Structure

```
bookify/
├── config/                  # Django project config
│   ├── settings.py          # All settings
│   ├── urls.py              # Root URL routing
│   ├── celery.py            # Celery app
│   └── wsgi.py
│
├── accounts/                # Auth: signup, login, profile
├── core/                    # SaaS home, middleware, context processor
│   ├── middleware.py        # TenantMiddleware
│   ├── context_processor.py # Global template context
│   └── templatetags/
│       └── booking_tags.py  # Custom template filters
│
├── businesses/              # Dashboard: services, staff, settings, CRM
│   ├── models.py            # Business, Service, Staff
│   ├── views.py             # All dashboard views
│   ├── utils.py             # KPI metrics, LTV, gap finder
│   └── templates/businesses/
│
├── bookings/                # Public booking engine
│   ├── models.py            # Booking model
│   ├── views.py             # Landing page, API endpoints, confirmation
│   ├── utils.py             # Slot generation, heatmap, atomic booking
│   └── templates/bookings/
│
├── themes/
│   └── theme_utils.py       # 25 themes (5 per business type)
│
├── payments/                # Stripe checkout + webhook
├── notifications/           # Email notifications + Celery tasks
├── api/                     # DRF REST API (v1)
│
├── static/
│   ├── css/dashboard.css    # Global styles
│   └── js/
│       ├── booking_calender.js   # Public booking flow
│       └── dashboard_charts.js  # Chart.js wrappers
│
└── templates/
    ├── base.html
    └── base_dashboard.html
```

---

## 5. Data Flow

### Public Booking Flow
```
Customer visits /b/<slug>/
        │
        ▼
TenantMiddleware resolves Business from slug
        │
        ▼
landing.html renders with dynamic CSS vars (theme injection)
        │
Step 1: Customer selects Service (JS card selection)
        │
Step 2: JS fetches /b/<slug>/api/heatmap/ → renders calendar dots
        Customer picks date → JS fetches /b/<slug>/api/availability/
        → renders time slot pills
        │
Step 3: Customer selects Staff (optional)
        Staff selection triggers re-fetch of availability
        │
Step 4: Checkout panel slides in
        Customer fills name/email/phone
        POST /b/<slug>/book/ → create_booking_atomic()
        ├── MongoDB transaction checks for conflicts
        ├── If clear: creates Booking, returns booking_id
        └── Celery fires confirmation email async
        │
        ▼
Redirect to /b/<slug>/confirmation/<booking_id>/
QR code generated for check-in
```

### Dashboard Data Flow
```
Manager logs in → /dashboard/
        │
        ▼
_get_active_business() resolves from user.active_business_id
        │
        ▼
get_dashboard_metrics(business) queries MongoDB:
  - Revenue today vs yesterday
  - Completion rate (30 days)
  - New vs returning customers
  - Today's queue
        │
        ▼
Dashboard renders KPI cards + today's timeline
```

### Theme Injection Flow
```
Request arrives for /b/<slug>/
        │
        ▼
business.theme + business.brand_colors resolved
        │
        ▼
render_css_vars(business) generates :root { --color-primary: ...; }
        │
        ▼
Injected into <style> block in <head> — zero FOUC
```

---

## 6. Setup & Installation

### Prerequisites
- Python 3.12+
- MongoDB Atlas account (free M0 cluster works)
- Redis (local or Redis Cloud free tier)
- Stripe account (test keys)

### Step 1 — Clone & Virtual Environment
```bash
git clone https://github.com/tshihab07/Online-Booking-Platform.git
cd Online-Booking-Platform
python3 -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows
```

### Step 2 — Install Dependencies
```bash
pip install django-mongodb-backend==6.0.3
pip install -r requirements.txt
```

> **Note:** Install `django-mongodb-backend` first — it must be present before Django loads.

### Step 3 — Configure Environment
```bash
cp .env .env.backup   # keep a backup
# Edit .env with your credentials (see Section 7)
```

### Step 4 — Run Migrations
```bash
python manage.py migrate
```

### Step 5 — Create Superuser
```bash
python manage.py createsuperuser
```

### Step 6 — Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### Step 7 — Run Development Server
```bash
python manage.py runserver
```

Visit: `http://localhost:8000`

---

## 7. Environment Variables

Open `.env` and update the following:

### 🔴 Must Change Before Use

| Variable | Current Value | Action Required |
|----------|--------------|-----------------|
| `SECRET_KEY` | `django-insecure-...` | **Generate a new one**: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | `True` | Set to `False` in production |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,*` | Set to your actual domain in production |

### 🟡 Already Configured (Verify These Work)

| Variable | Description |
|----------|-------------|
| `MONGODB_CONNECTION_STRING` | Your Atlas connection string — already set |
| `MONGODB_NAME` | Database name (`bookify_db`) |
| `STRIPE_PUBLIC_KEY` | Stripe test publishable key |
| `STRIPE_SECRET_KEY` | Stripe test secret key |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret |
| `EMAIL_HOST_USER` | Gmail address for sending emails |
| `EMAIL_HOST_PASSWORD` | Gmail App Password (not your Gmail password) |

### 🟢 New Variables Added

| Variable | Default | Description |
|----------|---------|-------------|
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Redis URL for Celery |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/0` | Redis URL for task results |
| `BASE_URL` | `http://localhost:8000` | Used in email links |

### Gmail App Password Setup
1. Go to Google Account → Security → 2-Step Verification → App Passwords
2. Generate a password for "Mail"
3. Use that 16-character password as `EMAIL_HOST_PASSWORD`

### Stripe Webhook (Local Testing)
```bash
# Install Stripe CLI, then:
stripe listen --forward-to localhost:8000/payments/webhook/
# Copy the webhook signing secret to STRIPE_WEBHOOK_SECRET in .env
```

---

## 8. Running the Project

### Development (Single Terminal)
```bash
source .venv/bin/activate
python manage.py runserver
```

### With Celery (Async Emails — Recommended)
Open 3 terminals:

**Terminal 1 — Django:**
```bash
source .venv/bin/activate
python manage.py runserver
```

**Terminal 2 — Redis (if running locally):**
```bash
redis-server
```

**Terminal 3 — Celery Worker:**
```bash
source .venv/bin/activate
celery -A config worker --loglevel=info
```

### Key URLs
| URL | Description |
|-----|-------------|
| `http://localhost:8000/` | SaaS marketing home |
| `http://localhost:8000/signup/` | Create account |
| `http://localhost:8000/login/` | Sign in |
| `http://localhost:8000/dashboard/` | Business dashboard |
| `http://localhost:8000/dashboard/onboarding/` | Create first business |
| `http://localhost:8000/b/<slug>/` | Public booking page |
| `http://localhost:8000/admin/` | Django admin |
| `http://localhost:8000/api/v1/` | REST API root |

---

## 9. Theme System

Each business type has **5 professionally designed themes** in `themes/theme_utils.py`.

### Applying a Theme
In the dashboard: **Settings → Choose Theme** → click any theme card → applied instantly via AJAX.

### Theme Structure
Each theme defines CSS custom properties:
```python
'rose_gold': {
    'label': 'Rose Gold Luxe',
    'css_vars': {
        '--color-primary': '#c9a96e',
        '--color-secondary': '#8b6914',
        '--color-bg': '#fdf6ec',
        '--glass-bg': 'rgba(255,249,240,0.25)',
        '--font-heading': "'Playfair Display', serif",
        # ... 12 more variables
    }
}
```

### Custom Brand Colors
Override any theme's primary/secondary/accent colors via the color pickers in Settings. Changes apply in real-time with live preview.

---

## 10. Booking Engine

### Slot Generation Algorithm
```
Working hours (e.g. 09:00–17:00)
    ÷ (service.duration + business.buffer_time)
    = available time slots
    - already booked slots
    - slots within lead_time window
    = final available slots
```

### Availability Heatmap
For each day in a month:
- `green` = < 50% booked
- `orange` = 50–99% booked
- `red` = 100% booked (sold out)
- `closed` = business closed that day

### Atomic Double-Booking Protection
```python
with transaction.atomic():
    conflict = Booking.objects.filter(
        business=business,
        date=booking_date,
        start_time=start_time,
        status__in=['confirmed', 'in_progress', 'pending'],
        staff=staff,  # if staff selected
    )
    if conflict.exists():
        return None, "This slot was just taken."
    booking = Booking.objects.create(...)
```

---

## 11. Dashboard Features

| Feature | Location | Description |
|---------|----------|-------------|
| KPI Cockpit | `/dashboard/` | Revenue, completion rate, new/returning customers, no-shows |
| Booking Calendar | `/dashboard/calendar/` | FullCalendar week/month/day view with color-coded status |
| Services | `/dashboard/services/` | Add/edit/delete services with pricing and duration |
| Staff | `/dashboard/staff/` | Team profiles with availability management |
| Clients (CRM) | `/dashboard/clients/` | Customer list with LTV, visit count, last service |
| Analytics | `/dashboard/analytics/` | Revenue chart, service breakdown, status donut |
| Fill the Gap | `/dashboard/marketing/fill-gap/` | Find empty slots + send re-engagement emails |
| Site Builder | `/dashboard/settings/` | Theme picker, color customizer, working hours, media upload |

---

## 12. API Documentation

Base URL: `http://localhost:8000/api/v1/`

Authentication: Session-based (login required for write operations)

### Endpoints

#### GET `/api/v1/businesses/<slug>/`
Returns full business profile including services and staff.

**Response:**
```json
{
  "id": "6650abc123...",
  "name": "Elite Barbers",
  "slug": "elite-barbers",
  "business_type": "salon",
  "theme": "midnight_glam",
  "currency": "USD",
  "services": [...],
  "staff_members": [...]
}
```

---

#### GET `/api/v1/businesses/<slug>/services/`
Returns all active services for a business.

**Response:**
```json
[
  {
    "id": "6650def456...",
    "name": "Haircut",
    "duration": 30,
    "price": "25.00",
    "category": "Hair",
    "is_active": true
  }
]
```

---

#### GET `/api/v1/businesses/<slug>/staff/`
Returns all active staff members.

---

#### GET `/api/v1/businesses/<slug>/availability/`
Returns available time slots for a service on a given date.

**Query Parameters:**
| Param | Required | Example |
|-------|----------|---------|
| `service_id` | Yes | `6650def456...` |
| `date` | Yes | `2026-06-15` |
| `staff_id` | No | `6650ghi789...` |

**Response:**
```json
{
  "date": "2026-06-15",
  "slots": [
    {"start": "09:00", "end": "09:30", "available": true},
    {"start": "09:30", "end": "10:00", "available": false},
    {"start": "10:00", "end": "10:30", "available": true}
  ]
}
```

---

#### GET `/api/v1/businesses/<slug>/heatmap/`
Returns monthly availability heatmap.

**Query Parameters:**
| Param | Required | Example |
|-------|----------|---------|
| `service_id` | Yes | `6650def456...` |
| `year` | No | `2026` |
| `month` | No | `6` |

**Response:**
```json
{
  "year": 2026,
  "month": 6,
  "heatmap": {
    "2026-06-01": "green",
    "2026-06-02": "orange",
    "2026-06-03": "red",
    "2026-06-04": "closed"
  }
}
```

---

#### POST `/api/v1/businesses/<slug>/bookings/`
Create a new booking (public — no auth required).

**Request Body:**
```json
{
  "service_id": "6650def456...",
  "staff_id": "6650ghi789...",
  "date": "2026-06-15",
  "start_time": "10:00",
  "customer_name": "John Smith",
  "customer_email": "john@example.com",
  "customer_phone": "+1234567890",
  "customer_notes": "Prefer quiet room"
}
```

**Response (201):**
```json
{
  "id": "6650xyz000...",
  "status": "pending",
  "date": "2026-06-15",
  "start_time": "10:00:00",
  "end_time": "10:30:00",
  "amount": "25.00",
  "payment_status": "unpaid"
}
```

**Response (409 — slot taken):**
```json
{
  "error": "This slot was just taken. Please choose another time."
}
```

---

#### GET `/api/v1/businesses/<slug>/bookings/list/`
List all bookings for a business. **Requires authentication.**

**Query Parameters:**
| Param | Example |
|-------|---------|
| `date` | `2026-06-15` |
| `status` | `confirmed` |

---

#### GET/PATCH `/api/v1/bookings/<id>/`
Retrieve or update a single booking. **Requires authentication + ownership.**

**PATCH Body:**
```json
{
  "status": "confirmed"
}
```

---

## 13. Deployment Guide

### Production Checklist

**1. Update `.env`:**
```bash
DEBUG=False
SECRET_KEY=<generate-new-50-char-key>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
BASE_URL=https://yourdomain.com
```

**2. Install production dependencies:**
```bash
pip install -r requirements.txt
```

**3. Collect static files:**
```bash
python manage.py collectstatic --noinput
```

**4. Run with Gunicorn:**
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

**5. Nginx config (reverse proxy):**
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location /static/ { alias /path/to/staticfiles/; }
    location /media/  { alias /path/to/media/; }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**6. Celery with Supervisor:**
```ini
[program:bookify-celery]
command=/path/to/.venv/bin/celery -A config worker --loglevel=info
directory=/path/to/project
autostart=true
autorestart=true
```

**7. Stripe Webhook (Production):**
- Go to Stripe Dashboard → Webhooks → Add endpoint
- URL: `https://yourdomain.com/payments/webhook/`
- Events: `checkout.session.completed`
- Copy signing secret to `STRIPE_WEBHOOK_SECRET` in `.env`

---

## 14. Advantages

### For Business Owners
- **Zero code required** — full booking page live in minutes
- **25 professional themes** — 5 per industry, all customizable
- **Real-time availability** — no double bookings, ever
- **Built-in CRM** — customer lifetime value, visit history, re-engagement
- **Fill the Gap campaigns** — automatically find and fill empty slots
- **Stripe payments** — secure checkout with QR code check-in

### For Developers
- **Clean multi-tenant architecture** — path-based tenancy, zero data leakage between businesses
- **MongoDB + Django** — flexible document storage with Django's ORM convenience
- **Atomic transactions** — ACID-compliant booking creation
- **REST API** — full DRF API for mobile apps or third-party integrations
- **Celery async** — emails never block the request cycle
- **Theme system** — CSS custom properties injected server-side, zero FOUC

### Technical Highlights
- `ObjectIdAutoField` throughout — native MongoDB ObjectId primary keys
- `TenantMiddleware` — O(1) business resolution per request
- Heatmap aggregation — single MongoDB query per month view
- Glassmorphism UI — dynamic CSS vars from database, no hardcoded colors
- FullCalendar integration — drag-and-drop booking management
