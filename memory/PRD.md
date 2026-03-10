# Ladakh Moto Market - Product Requirements Document

## Original Problem Statement
Production-grade bike rental marketplace platform based in Ladakh supporting three roles: Customers, Bike Shop Owners, Travel Agency/Hotel Owners. Architecture includes Authentication, Marketplace, Booking (with double-booking prevention), Payment (mock), Notification, and Analytics services with integration adapters for payment, KYC, SMS, email, push, maps, and IoT smart locks in mock mode.

## User Personas
- **Adventure Tourist (25-45)**: Renting bikes for Ladakh road trips (Khardung La, Pangong, Nubra)
- **Bike Shop Owner**: Local Leh/Ladakh shop listing fleet and managing bookings
- **Travel Agent/Hotel Owner**: Referring customers, earning commission (Phase 2)

## Core Requirements
- [x] JWT + Google OAuth authentication
- [x] Bike marketplace with search/filter (type, location, brand, price)
- [x] Atomic double-booking prevention using MongoDB findOneAndUpdate
- [x] Booking lifecycle management (confirmed -> active -> completed)
- [x] Late return penalty calculation (2hr grace, 1.5x daily rate)
- [x] Booking extension with atomic availability check
- [x] In-app notification system (booking lifecycle events)
- [x] Rating & review system (post-completion)
- [x] Shop owner dashboard with analytics & revenue tracking
- [x] Customer dashboard with active rides & history
- [x] Mock payment adapter (replaceable with Stripe/Razorpay)
- [x] Mock SMS/Email/KYC/Maps/IoT adapters (adapter pattern)
- [x] Payout ledger with 10% commission tracking
- [x] Database indexes for scalability
- [x] Architecture blueprint with race condition audit

## What's Been Implemented (March 10, 2026)

### Backend (FastAPI + MongoDB)
- Modular route structure: auth, bikes, bookings, reviews, notifications, analytics
- 6 mock integration adapters (payment, SMS, email, KYC, maps, IoT)
- Seed data: 2 shops, 8 bikes across Leh/Nubra Valley
- MongoDB indexes on all key query patterns
- Atomic booking operations preventing race conditions

### Frontend (React + Shadcn UI + Tailwind)
- Dark adventure theme (Barlow Condensed + Manrope fonts, yellow/sky accents)
- Landing page with hero, features, featured bikes
- Marketplace with search, type/location/sort filters
- Bike detail with booking calendar (date range picker)
- Customer dashboard (active rides, history, notifications)
- Shop dashboard (bike management, bookings, revenue chart)
- Login/Register with JWT + Google OAuth
- Responsive design, glassmorphism navbar

### Testing: 97.8% pass rate (21/22 backend, 100% frontend)

## Prioritized Backlog

### P0 (Critical - Next Sprint)
- Travel Agent/Hotel Owner dashboard (referral management, commission tracking)
- Admin dashboard with full analytics and user management

### P1 (High Priority)
- Booking reminder notifications (24h before pickup, 4h before return)
- KYC verification flow (real provider integration)
- Image upload for bikes (object storage integration)
- Dispute resolution system

### P2 (Medium Priority)
- Real payment gateway integration (Stripe/Razorpay)
- SMS/Email notification delivery (Twilio/SendGrid)
- Map integration for shop locations
- Mobile-optimized booking flow
- Push notifications (Firebase)

### P3 (Nice to Have)
- IoT smart lock integration
- Route planning with waypoints
- Price comparison across shops
- Seasonal pricing engine
- Multi-language support (Hindi, English)
