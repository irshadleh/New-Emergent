# Ladakh Moto Market - PRD

## Original Problem Statement
Build a production-grade bike rental marketplace platform based out of Ladakh supporting Customer, Bike Shop Owner, Travel Agent, and Admin roles.

## Tech Stack
- **Backend**: FastAPI, MongoDB (motor), Pydantic, JWT + Google OAuth, Resend (email)
- **Frontend**: React, React Router, TailwindCSS, shadcn/ui, Recharts, PWA
- **Architecture**: Service-Oriented (services + adapter pattern), REST APIs, Background Tasks

## What's Been Implemented

### Phase 1-3: MVP, Refactor, Frontend (Complete)
- Full auth (JWT + Google OAuth), marketplace with bike search/filter, booking engine
- Service layer (booking, analytics, payout, notification, rating engines)
- Adapter layer (payment, notification, kyc, maps, iot - all mocked)
- Customer, Shop Owner, Travel Agent dashboards fully integrated
- PWA support (manifest, service worker)

### Phase 4: Admin Dashboard + User Features (Complete - Mar 2026)
- Admin Dashboard with Overview, Users, Payouts, KYC tabs
- Rating/Review UI for customers on completed bookings
- Enhanced booking flow with payment confirmation step

### Phase 5: Onboarding & Application System (Complete - Mar 2026)
- **Admin Access**: `irshadxat@gmail.com` / `admin123` mapped as platform admin
- **Smart Login Redirects**: admin→/admin, shop_owner→/shop, travel_agent→/travel-agent, customer→/dashboard
- **Shop Owner Onboarding**: Landing "Start Listing" → /apply?type=shop_owner → form (name, email, phone, shop name, address, bikes, types, experience) → admin approves → auto-creates user + shop with random password → email via Resend → first login forced password change
- **Travel Agent Onboarding**: Landing "Register as Travel Agent" → /apply?type=travel_agent → form (name, email, phone, agency name/type/address) → same admin approval flow
- **Admin Applications Tab**: Lists all applications with Type column (Shop Owner / Travel Agent), approve/reject with notes, shows generated password on approval
- **Password Change Dialog**: Modal on first login for approved users, cannot dismiss until password changed
- **Resend Email**: Real integration (test mode limited to verified emails, password shown in admin UI as fallback)
- **Backend**: /api/applications (submit, list, approve, reject), /api/auth/change-password

### Testing (Mar 2026)
- iteration_3.json: Admin dashboard, reviews, booking flow — 93% backend, 100% frontend
- iteration_4.json: Onboarding, applications, redirects, password change — 100% backend (23/23), 100% frontend (18/18)

## Key API Endpoints
| Endpoint | Method | Auth | Description |
|---|---|---|---|
| /api/auth/register, /login, /me, /logout | Various | Various | Auth |
| /api/auth/change-password | POST | Yes | Change password (first-login) |
| /api/bikes, /api/shops | GET/POST | Various | CRUD |
| /api/bookings | GET/POST | Yes | Booking management |
| /api/reviews | POST | Yes | Submit review |
| /api/admin/dashboard, /users, /payouts, /kyc | Various | Admin | Admin management |
| /api/applications/submit | POST | No | Public application submission |
| /api/applications | GET | Admin | List applications |
| /api/applications/{id}/approve | POST | Admin | Approve + create user |
| /api/applications/{id}/reject | POST | Admin | Reject application |

## Prioritized Backlog

### P0 (Next)
- Mobile-responsive optimization

### P1
- UI/UX polish pass
- ESLint configuration

### P2
- Replace remaining mock integrations (Stripe, Twilio)
- Verify Resend domain for production email delivery
- React Native / Capacitor wrapper

## Credentials
- Admin: irshadxat@gmail.com / admin123
- Test Shop Owner: tenzin@himalayabikes.com / newpass123
