# Caleido

A production-focused scheduling API inspired by Calendly, built with Django REST Framework.

The project focuses on backend engineering fundamentals including authentication, transactional consistency, concurrency control, asynchronous processing, caching, and calendar interoperability.

## Project Status

Currently in active development — Day 43 of a 49-day production engineering roadmap.

### Completed

* Foundation & Infrastructure
* Authentication & User Management
* Event Types & Availability Management
* Slot Generation Engine
* Booking System
* Async Processing with Celery
* Redis Caching & Idempotency

### Currently Building

* Infrastructure & CI/CD

### Upcoming

* Observability
* Documentation

---

## Engineering Highlights

* JWT authentication using RS256 signing
* Refresh token rotation and blacklisting
* Transaction-safe booking creation using SELECT FOR UPDATE
* Redis-backed idempotency protection
* Pure Python slot generation engine with zero ORM dependency
* Async email processing with Celery
* Scheduled reminder system with task revocation support
* PostgreSQL relational schema with constraints and indexes
* Comprehensive automated test suite

---

## Tech Stack

| Layer             | Technology            |
| ----------------- | --------------------- |
| API Framework     | Django REST Framework |
| Language          | Python 3.12           |
| Database          | PostgreSQL            |
| Cache / Broker    | Redis                 |
| Async Tasks       | Celery                |
| Authentication    | SimpleJWT (RS256)     |
| Email             | SendGrid              |
| Testing           | pytest                |
| API Documentation | drf-spectacular       |

---

## Architecture Decisions

### Preventing Double Booking

Bookings are created inside database transactions using row-level locking (SELECT FOR UPDATE) to guarantee consistency under concurrent requests.

### Pure Slot Engine

Slot generation logic is implemented as pure Python functions with no ORM dependency, making it highly testable and reusable.

### Async Notifications

Booking confirmations, cancellations, and reminders are processed asynchronously through Celery workers to keep API response times low.

### Idempotent Requests

Redis-backed idempotency keys prevent duplicate booking creation caused by retries or network failures.

---

## Core Features

### Authentication

* User Registration
* Login & Logout
* JWT Authentication
* Refresh Token Rotation
* Token Blacklisting
* Email Verification
* Password Reset
* Google OAuth

### Scheduling

* Event Type Management
* Availability Rules
* Date Overrides
* Timezone-Aware Slot Generation
* DST Handling

### Booking Management

* Create Booking
* List Bookings
* Cancel Booking
* Reschedule Booking
* Concurrency Protection
* Idempotency Protection

### Notifications

* Booking Confirmation Emails
* Cancellation Emails
* Reschedule Emails
* Scheduled Reminders

### Caching

* Slot Caching
* Analytics Caching
* Redis-backed Idempotency

---

## API Documentation

Swagger UI available at:

/api/docs/

OpenAPI schema is generated automatically using drf-spectacular.

---

## Local Development

### Prerequisites

* Python 3.12
* PostgreSQL
* Redis

### Run Locally

```bash
git clone https://github.com/Harbdulmarleyk03/Caleido.git

cd Caleido

cp .env.example .env

pip install -r requirements/development.txt

python manage.py migrate

python manage.py runserver
```

---

## Roadmap

### In Progress

* Health Check Endpoints

### Planned

* Dockerisation
* GitHub Actions CI
* Sentry Integration
* OpenAPI Documentation Improvements

---

## What I'd Build Next

* Google Calendar Synchronisation
* Outlook Calendar Integration
* Team Scheduling
* Round-Robin Booking
* Webhook Subscriptions
* Multi-Tenant Organisations
* Analytics Dashboard

---

## Author

Adebayo Abdulmalik

Backend Engineer

GitHub:
https://github.com/Harbdulmarleyk03

LinkedIn:
https://linkedin.com/in/abdulmalik-adebayo
