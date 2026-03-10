# Ladakh Moto Market - PRD

## Original Problem Statement
Build a production-grade bike rental marketplace platform based out of Ladakh supporting three user roles: Customers, Bike Shop Owners, and Travel Agency/Hotel Owners.

Architecture: Mobile Apps → API Gateway → Backend Services → Database + Object Storage → Admin Dashboard + Analytics.

## Core Requirements
- **Backend Services**: Authentication, Marketplace, Booking, Payments, Notifications, Analytics
- **Database Schema**: Users, BikeShops, Bikes, Bookings, Payments, PayoutLedger, Reviews, Notifications
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
- ShopDashboard: added Payouts tab (summary, ledger, settlements), enhanced analytics (top performing bike)
- App.js: added /travel-agent route
- Navbar: role-conditional navigation (shop_owner → My Shop, travel_agent → Agent Portal)
- PWA support: manifest.json, service-worker.js, mobile meta tags

### Testing Status (Feb 2026)
- Backend: 36/36 tests passing (100%)
- Frontend: All 3 role flows tested (100%)
- All endpoints verified via comprehensive pytest suite

## API Endpoints
| Endpoint | Method | Auth | Description |
|---|---|---|---|
| /api/auth/register | POST | No | Register user (customer/shop_owner/travel_agent) |
| /api/auth/login | POST | No | Login with email/password |
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

## Prioritized Backlog

### P0 (Next)
- Admin Dashboard for platform-wide analytics and management

### P1
- Mobile-responsive optimization and PWA enhancements
- Enhanced booking flow with payment confirmation screens

### P2
- Replace mock integrations with real providers (Stripe, SMS, etc.)
- UI/UX polish and theming refinements
- React Native / Capacitor wrapper for native app store distribution
