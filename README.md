# 🕹️ PostKnob

A **production-grade social media platform** built with Django 5.2 — featuring a Redis Fan-Out feed cache, Celery async task pipeline, full JWT-authenticated REST API, HTMX reactive UI, and Docker Compose containerization.

[![CI](https://github.com/rider-pratyush/PostKnob/actions/workflows/ci.yml/badge.svg)](https://github.com/rider-pratyush/PostKnob/actions)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-green?logo=django&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-red?logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.6-green?logo=celery&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker&logoColor=white)

---

## 📐 Architecture

```
                         ┌─────────────────────┐
                         │   Browser / Mobile   │
                         └──────────┬──────────┘
                                    │
                         ┌──────────▼──────────┐
                         │  Django + Gunicorn   │
                         │  (3 sync workers)    │
                         │                      │
                         │  ┌────────┐ ┌──────┐ │
                         │  │ HTMX   │ │ DRF  │ │
                         │  │ Views  │ │ API  │ │
                         │  └────┬───┘ └──┬───┘ │
                         │       └───┬────┘     │
                         │           │          │
                         │     Django ORM       │
                         └───────┬──────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              SQLite/PG      Redis        Celery
              (Database)   (Feed Cache   (Async Tasks:
                            + Broker)    Fan-out, Image
                                         Processing)
```

**Key architectural decisions:**
- **Modular Monolith** — single Django project, cleanly separated into app views (HTMX) and API views (DRF)
- **Fan-Out-on-Write** — personalized feeds are pre-computed in Redis, achieving O(1) read complexity
- **Dual Interface** — same backend serves both a browser UI (session auth) and a REST API (JWT auth)
- **Event-Driven** — Django signals trigger Celery tasks for feed fan-out and image processing

---

## ✨ Features

### Core Social Features
- 📝 **Posts** — Create, edit, delete posts with optional image uploads
- ❤️ **Likes** — Toggle likes with instant HTMX partial page updates
- 💬 **Comments** — Threaded comment system with real-time HTMX rendering
- 👤 **Follow/Unfollow** — Directional social graph with HTMX OOB stat updates
- 🔖 **Bookmarks** — Private post saves with a dedicated bookmarks page
- #️⃣ **Hashtags** — Tag posts and discover content by hashtag
- 🔍 **Search** — Search posts by text content and hashtags
- 👥 **Follower/Following Lists** — Public social graph pages for every user

### Advanced Backend Features
- 📰 **Fan-Out-on-Write Feed** — Redis-cached personalized timelines with DB fallback on cache miss
- 🖼️ **Async Image Processing** — Celery task resizes uploads to 1200×1200 at quality=85
- 🔄 **Feed Sync on Follow/Unfollow** — Celery tasks inject/remove posts from Redis feed on social graph changes
- 📊 **Auto-generated API Docs** — Swagger UI + ReDoc via drf-spectacular

### Production Features
- 🐳 **Docker Compose** — 4 services: web, celery worker, celery-beat, redis
- 🧪 **60 Automated Tests** — Models, views, and API tests with factory-boy
- 🔒 **Security Hardened** — CSRF, HSTS, SSL redirect, non-root Docker user, JWT refresh rotation
- 📋 **CI Pipeline** — GitHub Actions: ruff + black linting, pytest with coverage
- 📈 **Sentry Integration** — Error tracking (conditional on SENTRY_DSN env var)
- 📝 **Structured Logging** — JSON-formatted logs via python-json-logger

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Language** | Python 3.12 | Backend logic |
| **Framework** | Django 5.2 | ORM, auth, admin, forms, signals, middleware |
| **REST API** | Django REST Framework 3.18 | Serializers, viewsets, permissions |
| **API Auth** | djangorestframework-simplejwt | JWT access/refresh tokens with rotation |
| **API Docs** | drf-spectacular | Auto-generated OpenAPI 3.0 / Swagger / ReDoc |
| **Task Queue** | Celery 5.6 | Async image processing, feed fan-out |
| **Broker & Cache** | Redis 7 | Celery message broker + feed list cache |
| **Scheduler** | django-celery-beat | DB-backed periodic task schedules |
| **Database** | SQLite (dev) / PostgreSQL 16 (prod) | Data storage |
| **Frontend** | HTMX 2.0 + Tailwind CSS + Alpine.js | Reactive UI without JavaScript frameworks |
| **WSGI Server** | Gunicorn | Production web server (3 workers) |
| **Static Files** | Whitenoise | Compressed static serving without Nginx |
| **Image Processing** | Pillow | Resize and compress uploaded photos |
| **Config** | django-environ | 12-Factor App env var parsing |
| **Monitoring** | Sentry SDK | Error tracking and performance monitoring |
| **Logging** | python-json-logger | Machine-parseable structured logs |
| **Testing** | pytest + factory-boy + pytest-cov | 60 automated tests with coverage |
| **Linting** | ruff + black | Code quality enforcement |
| **CI/CD** | GitHub Actions | Automated lint + test on every push |
| **Containers** | Docker + Docker Compose | 4-service containerized deployment |

---

## 🚀 Getting Started

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/rider-pratyush/PostKnob.git
cd PostKnob

# Create environment file
cp postapp/.env.example postapp/.env

# Build and start all 4 services
docker-compose up --build -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create a superuser
docker-compose exec web python manage.py createsuperuser

# Open in browser
# http://127.0.0.1:8000
```

### Option 2: Local Development

```bash
# Clone and setup virtual environment
git clone https://github.com/rider-pratyush/PostKnob.git
cd PostKnob
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp postapp/.env.example postapp/.env

# Run migrations and create superuser
cd postapp
python manage.py migrate
python manage.py createsuperuser

# Start the development server
python manage.py runserver
```

> **Note:** For full functionality (feed caching, async tasks), you'll need Redis running locally and a Celery worker:
> ```bash
> # Terminal 2: Start Celery worker
> cd postapp && celery -A postapp worker -l info
> ```

---

## 🌐 API Reference

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/token/` | POST | Obtain JWT access + refresh tokens |
| `/api/token/refresh/` | POST | Refresh access token |
| `/api/token/verify/` | POST | Verify token validity |

### Posts
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/posts/` | GET | — | List posts (paginated, searchable) |
| `/api/v1/posts/` | POST | JWT | Create a post |
| `/api/v1/posts/{id}/` | GET | — | Retrieve a post |
| `/api/v1/posts/{id}/` | PUT/PATCH | JWT (owner) | Update a post |
| `/api/v1/posts/{id}/` | DELETE | JWT (owner) | Delete a post |
| `/api/v1/posts/{id}/like/` | POST/DELETE | JWT | Like / unlike |
| `/api/v1/posts/{id}/bookmark/` | POST/DELETE | JWT | Bookmark / unbookmark |
| `/api/v1/posts/{pk}/comments/` | GET/POST | —/JWT | List / create comments |

### Users & Social
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/users/` | GET | — | List all users |
| `/api/v1/users/{username}/` | GET | — | User detail |
| `/api/v1/users/{username}/follow/` | POST/DELETE | JWT | Follow / unfollow |
| `/api/v1/users/{username}/followers/` | GET | — | Followers list |
| `/api/v1/users/{username}/following/` | GET | — | Following list |
| `/api/v1/feed/` | GET | JWT | Personalized feed (Redis-cached) |
| `/api/v1/bookmarks/` | GET | JWT | User's bookmarks |

### Documentation & Health
| Endpoint | Description |
|----------|-------------|
| `/api/docs/` | Swagger UI (interactive) |
| `/api/redoc/` | ReDoc documentation |
| `/api/schema/` | OpenAPI 3.0 JSON schema |
| `/api/v1/health/` | Health check |

---

## 🧪 Testing

```bash
# Run all 60 tests
cd postapp
python -m pytest postknob/tests/ -v

# Run with coverage report
python -m pytest postknob/tests/ --cov=postknob --cov-report=term-missing

# Run specific test file
python -m pytest postknob/tests/test_api.py -v
```

**Test coverage includes:**
- Model creation, constraints, signals, cascade deletes
- View auth redirects, CRUD operations, HTMX responses
- API JWT auth, permissions (401/403), pagination, search

---

## 📁 Project Structure

```
PostKnob/
├── .github/workflows/ci.yml    # GitHub Actions CI pipeline
├── Dockerfile                  # Python 3.12-slim, non-root user
├── docker-compose.yml          # 4 services: web, celery, beat, redis
├── requirements.txt            # All pinned dependencies
└── postapp/                    # Django project root
    ├── postapp/                # Project config
    │   ├── settings/           # base.py, dev.py, prod.py
    │   ├── celery.py           # Celery app initialization
    │   └── urls.py             # Root URL config
    └── postknob/               # Primary application
        ├── models.py           # 7 data models
        ├── views.py            # 25 HTML/HTMX view functions
        ├── services.py         # Redis feed cache operations
        ├── tasks.py            # 6 Celery tasks
        ├── signals.py          # Event-driven wiring
        ├── api/                # REST API sub-package
        │   ├── views.py        # DRF ViewSets + APIViews
        │   ├── serializers.py  # Read/Write serializers
        │   └── permissions.py  # IsOwnerOrReadOnly
        ├── templates/          # Django templates + HTMX partials
        └── tests/              # 60 pytest tests + factories
```

---

## 🔧 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | ✅ | Django secret key |
| `DEBUG` | ✅ | Debug mode (True/False) |
| `ALLOWED_HOSTS` | ✅ | Comma-separated allowed hosts |
| `DATABASE_URL` | Prod | PostgreSQL connection string |
| `REDIS_URL` | ✅ | Redis connection URL |
| `CELERY_BROKER_URL` | ✅ | Celery broker URL |
| `SENTRY_DSN` | Optional | Sentry error tracking DSN |

---

## 👨‍💻 Author

**Pratyush Kumar**

B.Tech, EEE — IIT Guwahati

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
