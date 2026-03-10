# Ladakh Moto Market - PRD

## Original Problem Statement
Build a production-grade bike rental marketplace platform based out of Ladakh supporting three user roles: Customers, Bike Shop Owners, and Travel Agency/Hotel Owners, plus an Admin role for platform management.

Architecture: Mobile Apps -> API Gateway -> Backend Services -> Database + Object Storage -> Admin Dashboard + Analytics.

## Core Requirements
- **Backend Services**: Authentication, Marketplace, Booking, Payments, Notifications, Analytics, Admin Management
- **Database Schema**: Users, BikeShops, Bikes, Bookings, Payments, PayoutLedger, Reviews, Notifications, Settlements
- **Operational Features**: Double booking prevention, late return penalties, availability calendar, smart notifications, rating system, bike performance analytics, payout ledger
- **Integrations**: Mock implementations for Payment, KYC, SMS/Email/Push, Maps, IoT (adapter pattern)
- **Scalability**: 50K+ users
- **Mobile**: PWA approach with future native wrapper support

## Tech Stack
- **Backend**: FastAPI, MongoDB (motor), Pydantic, JWT + Google OAuth
- **Frontend**: React, React Router, TailwindCSS, shadcn/ui, Recharts
- **Architecture**: Service-Oriented (services layer + adapter pattern), REST APIs, Background Tasks

## What's Been Implemented

### Phase 1: MVP (Complete)
- Full-stack MVP with auth, marketplace, booking, reviews
- Database schema with indexes for 50K+ scale
- Seed data (2 shops, 8 bikes)

### Phase 2: Production Refactor (Complete)
- Service layer: booking_engine, analytics_engine, payout_engine, notification_engine, rating_engine
- Adapter layer: payment, notification, kyc, maps, iot (all mocked)
- New routes: payouts, travel_agents, enhanced analytics
- Background scheduler for overdue bookings + notification reminders

### Phase 3: Frontend Integration (Complete - Feb 2026)
- Updated api.js with all new endpoint functions
- TravelAgentDashboard: referral tracking, booking tracking, customer management, earnings analytics, commission ledger
- ShopDashboard: added Payouts tab (summary, ledger, settlements), enhanced analytics
- App.js: added /travel-agent route
- Navbar: role-conditional navigation
- PWA support: manifest.json, service-worker.js, mobile meta tags

### Phase 4: Admin Dashboard + User Features (Complete - Mar 2026)
- **Admin Dashboard** (`/admin` route):
  - Overview tab: Platform metrics (users, shops, bikes, bookings, revenue, commission), pending KYC/payouts, revenue trends line chart, booking status pie chart, top shops bar chart, recent bookings
  - Users tab: Searchable/filterable user table, manage dialog (change role, KYC status, suspend/unsuspend)
  - Payouts tab: Summary cards, payout entries list with settle action per shop
  - KYC tab: Filterable KYC table, approve/reject with notes
  - Admin role guard (403 for non-admin users)
- **Rating System UI**: Review dialog on completed bookings with star rating + comment, "Rate Ride" button on BookingCard
- **Enhanced Booking Flow**: Payment confirmation panel in BikeDetail with full booking summary before "Confirm & Pay"
- Backend: `/api/admin/` routes (dashboard, users, payouts, kyc)
- Navbar: Admin link for admin role users, Admin Panel in dropdown

### Testing Status (Mar 2026)
- Backend: 27/29 admin tests passing (93%, 2 skipped due to fixtures)
- Frontend: 100% - all admin tabs, booking flow, customer dashboard verified
- Previous E2E: 36/36 backend, all role flows passing

## API Endpoints
| Endpoint | Method | Auth | Description |
|---|---|---|---|
| /api/auth/register | POST | No | Register user |
| /api/auth/login | POST | No | Login |
| /api/auth/session | POST | No | OAuth session exchange |
| /api/auth/me | GET | Yes | Get current user |
| /api/bikes | GET/POST | No/Yes | List/Create bikes |
| /api/bikes/{id} | GET/PUT/DELETE | No/Yes/Yes | Bike CRUD |
| /api/shops | GET/POST | No/Yes | List/Create shops |
| /api/bookings | GET/POST | Yes | List/Create bookings |
| /api/bookings/{id}/status | PUT | Yes | Update booking status |
| /api/bookings/{id}/return | POST | Yes | Return bike |
| /api/bookings/{id}/extend | POST | Yes | Extend booking |
| /api/availability/{bike_id} | GET | No | Availability calendar |
| /api/analytics/shop | GET | Yes | Shop analytics |
| /api/analytics/bike/{id} | GET | Yes | Bike performance |
| /api/analytics/platform | GET | Yes | Platform analytics |
| /api/payouts/summary | GET | Yes | Payout summary |
| /api/payouts/ledger | GET | Yes | Payout ledger |
| /api/payouts/settle | POST | Yes | Request settlement |
| /api/travel-agent/dashboard | GET | Yes | Agent dashboard |
| /api/travel-agent/generate-link | POST | Yes | Generate referral link |
| /api/travel-agent/commission-ledger | GET | Yes | Commission ledger |
| /api/notifications | GET | Yes | List notifications |
| /api/reviews | POST | Yes | Submit review |
| /api/admin/dashboard | GET | Admin | Platform dashboard |
| /api/admin/users | GET | Admin | List users |
| /api/admin/users/{id} | PUT | Admin | Update user |
| /api/admin/payouts | GET | Admin | List all payouts |
| /api/admin/payouts/{shop_id}/settle | POST | Admin | Settle shop payouts |
| /api/admin/kyc | GET | Admin | List KYC submissions |
| /api/admin/kyc/{user_id}/review | POST | Admin | Review KYC |

## Prioritized Backlog

### P0 (Next)
- Mobile-responsive optimization and PWA enhancements

### P1
- UI/UX polish and theming refinements
- ESLint configuration setup

### P2
- Replace mock integrations with real providers (Stripe, SMS, etc.)
- React Native / Capacitor wrapper for native app store distribution
