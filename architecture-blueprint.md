# Ladakh Moto Market - Architecture Blueprint

## System Architecture

```
┌─────────────────────────────────────────────────┐
│           Frontend (React + Shadcn UI)           │
│  Landing | Marketplace | Dashboards | Auth       │
└──────────────────────┬──────────────────────────┘
                       │ HTTPS (Kubernetes Ingress)
┌──────────────────────▼──────────────────────────┐
│          API Gateway (FastAPI /api prefix)        │
│       CORS + JWT + Cookie Session Auth           │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│              Backend Services                     │
│  ┌───────────┐ ┌────────────┐ ┌──────────────┐ │
│  │   Auth    │ │ Marketplace│ │   Booking    │ │
│  │  Service  │ │  Service   │ │   Service    │ │
│  └───────────┘ └────────────┘ └──────────────┘ │
│  ┌───────────┐ ┌────────────┐ ┌──────────────┐ │
│  │  Payment  │ │Notification│ │  Analytics   │ │
│  │  Service  │ │  Service   │ │   Service    │ │
│  └───────────┘ └────────────┘ └──────────────┘ │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│     MongoDB + Mock Integration Adapters          │
│  Collections: users, bikes, bookings, payments,  │
│  bike_shops, reviews, notifications,             │
│  payout_ledger, user_sessions                    │
│  Adapters: Payment, SMS, Email, KYC, Maps, IoT  │
└─────────────────────────────────────────────────┘
```

## Database Schema

### Users Collection
```json
{
  "user_id": "user_abc123",        // Custom UUID (not MongoDB _id)
  "email": "rider@example.com",    // Unique index
  "name": "John Rider",
  "password_hash": "bcrypt...",    // Empty for Google OAuth users
  "role": "customer|shop_owner|travel_agent",
  "phone": "+91-9876543210",
  "profile_picture": "url",
  "kyc_status": "pending|verified|rejected",
  "created_at": "ISO datetime",
  "updated_at": "ISO datetime"
}
```

### BikeShops Collection
```json
{
  "shop_id": "shop_abc123",
  "owner_id": "user_abc123",       // References users.user_id
  "name": "Himalayan Riders Leh",
  "description": "...",
  "address": "Main Bazaar, Leh",
  "phone": "+91-9876543210",
  "rating": 4.5,
  "total_reviews": 42,
  "is_verified": true,
  "operating_hours": { "open": "08:00", "close": "20:00" },
  "created_at": "ISO datetime"
}
```

### Bikes Collection (with embedded booking_slots for atomic operations)
```json
{
  "bike_id": "bike_abc123",
  "shop_id": "shop_abc123",
  "name": "Royal Enfield Himalayan 450",
  "type": "adventure|cruiser|sport|scooter",
  "brand": "Royal Enfield",
  "model": "Himalayan 450",
  "year": 2024,
  "engine_cc": 450,
  "daily_rate": 1500,
  "weekly_rate": 9000,
  "images": ["url1", "url2"],
  "features": ["ABS", "GPS Mount", "Helmet Included"],
  "is_available": true,
  "location": "Leh Main Market",
  "description": "...",
  "booking_slots": [
    {
      "booking_id": "booking_abc",
      "start_date": "2024-06-01T00:00:00Z",
      "end_date": "2024-06-05T00:00:00Z",
      "status": "confirmed|active|completed|cancelled"
    }
  ],
  "created_at": "ISO datetime",
  "updated_at": "ISO datetime"
}
```

### Bookings Collection
```json
{
  "booking_id": "booking_abc123",
  "bike_id": "bike_abc123",
  "shop_id": "shop_abc123",
  "customer_id": "user_abc123",
  "bike_name": "Royal Enfield Himalayan 450",
  "shop_name": "Himalayan Riders Leh",
  "start_date": "ISO datetime",
  "end_date": "ISO datetime",
  "actual_return_date": null,
  "status": "pending|confirmed|active|completed|cancelled|overdue",
  "daily_rate": 1500,
  "total_days": 5,
  "base_amount": 7500,
  "penalty_amount": 0,
  "extension_amount": 0,
  "total_amount": 7500,
  "payment_status": "pending|paid|refunded",
  "notes": "",
  "created_at": "ISO datetime",
  "updated_at": "ISO datetime"
}
```

### Payments Collection
```json
{
  "payment_id": "pay_abc123",
  "booking_id": "booking_abc123",
  "user_id": "user_abc123",
  "amount": 7500,
  "currency": "INR",
  "type": "booking|penalty|extension|refund",
  "status": "pending|completed|failed|refunded",
  "payment_method": "mock_gateway",
  "gateway_reference": "mock_pay_abc123",
  "created_at": "ISO datetime"
}
```

### PayoutLedger Collection
```json
{
  "payout_id": "payout_abc123",
  "shop_id": "shop_abc123",
  "booking_id": "booking_abc123",
  "amount": 6750,
  "commission_rate": 0.10,
  "commission_amount": 750,
  "status": "pending|processed|failed",
  "payout_date": null,
  "created_at": "ISO datetime"
}
```

### Reviews Collection
```json
{
  "review_id": "rev_abc123",
  "booking_id": "booking_abc123",
  "bike_id": "bike_abc123",
  "shop_id": "shop_abc123",
  "reviewer_id": "user_abc123",
  "rating": 5,
  "comment": "Amazing ride through Khardung La!",
  "created_at": "ISO datetime"
}
```

### Notifications Collection
```json
{
  "notification_id": "notif_abc123",
  "user_id": "user_abc123",
  "type": "booking_confirmed|new_booking|booking_completed|penalty_applied|...",
  "title": "Booking Confirmed!",
  "message": "Your Himalayan 450 is ready for pickup!",
  "data": { "booking_id": "..." },
  "is_read": false,
  "created_at": "ISO datetime"
}
```

## Race Condition & Double Booking Prevention

### Strategy: Atomic MongoDB Operations

The booking engine uses MongoDB's `findOneAndUpdate` with atomic conditions:

```python
# ATOMIC DOUBLE-BOOKING PREVENTION
result = await db.bikes.find_one_and_update(
    {
        "bike_id": bike_id,
        "booking_slots": {
            "$not": {
                "$elemMatch": {
                    "start_date": {"$lt": end_date},    # Existing starts before new ends
                    "end_date": {"$gt": start_date},    # Existing ends after new starts
                    "status": {"$in": ["confirmed", "active"]}
                }
            }
        }
    },
    {
        "$push": {
            "booking_slots": {
                "booking_id": booking_id,
                "start_date": start_date,
                "end_date": end_date,
                "status": "confirmed"
            }
        }
    },
    return_document=ReturnDocument.AFTER
)

if result is None:
    raise HTTPException(409, "Bike unavailable for selected dates")
```

### Why This Works:
1. **Single atomic operation**: The check and update happen in one database call
2. **No race window**: Between checking availability and creating the booking, no other request can sneak in
3. **Overlap detection**: The `$not` + `$elemMatch` combo catches ALL overlap cases:
   - New booking starts during existing booking
   - New booking ends during existing booking
   - New booking completely contains existing booking
   - Existing booking completely contains new booking
4. **Status-aware**: Only considers confirmed/active bookings, ignoring cancelled/completed ones

### Valid Status Transitions:
```
pending -> confirmed | cancelled
confirmed -> active | cancelled
active -> completed | overdue
overdue -> completed
```
Transitions enforced server-side to prevent invalid state changes.

## Late Return Penalty Logic

```python
def calculate_penalty(end_date, actual_return, daily_rate):
    grace_period = 2 hours
    grace_deadline = end_date + 2 hours

    if actual_return <= grace_deadline:
        return 0  # Within grace period

    extra_hours = (actual_return - end_date).total_seconds() / 3600
    extra_days = ceil(extra_hours / 24)
    penalty_rate = 1.5x
    
    return extra_days * daily_rate * 1.5
```

### Escalation:
1. At return time: penalty calculated and charged automatically
2. Customer notified of penalty amount
3. Payout ledger updated with penalty revenue split

## Booking Extension Handling

1. Customer requests extension before `end_date`
2. System checks availability atomically (same pattern as booking creation)
3. If available: extends `end_date`, calculates additional cost
4. Extension payment processed, booking updated
5. Notifications sent to both customer and shop owner

## Notification Orchestration

### Event-Driven System:
| Event | Customer | Shop Owner |
|-------|----------|------------|
| Booking Created | "Booking Confirmed!" | "New Booking Received!" |
| Booking Activated | "Ride Started" | - |
| Return Reminder | "Return due in 4h" | - |
| Booking Completed | "Ride Complete! Leave a review" | - |
| Penalty Applied | "Late return penalty of X INR" | - |
| Payout Processed | - | "Payout of X INR processed" |

### Channels (via Mock Adapters):
- In-App (implemented)
- SMS (MockSMSProvider - replaceable with Twilio)
- Email (MockEmailProvider - replaceable with SendGrid)
- Push (future - replaceable with Firebase)

## Integration Adapters (Adapter Pattern)

All external integrations use the adapter pattern with mock implementations:

| Integration | Mock Class | Real Provider |
|-------------|-----------|---------------|
| Payment Gateway | MockPaymentGateway | Stripe/Razorpay |
| SMS | MockSMSProvider | Twilio |
| Email | MockEmailProvider | SendGrid |
| KYC | MockKYCProvider | DigiLocker/Aadhaar |
| Maps | MockMapService | Google Maps |
| IoT Locks | MockIoTLockService | Custom IoT |

### Replacing a Mock:
```python
# Before (mock)
from adapters import payment_gateway

# After (real Stripe)
from stripe_adapter import StripePaymentGateway
payment_gateway = StripePaymentGateway(api_key=os.environ['STRIPE_KEY'])
```

Same interface, swap implementation. No code changes in business logic.

## Database Scalability

### Indexes:
- `users`: unique on email, user_id
- `bikes`: compound (type, location, is_available) for marketplace queries
- `bookings`: compound (bike_id, status) for conflict checks
- `bookings`: customer_id for dashboard queries
- `bike_shops`: owner_id, shop_id
- `reviews`: bike_id for aggregation
- `notifications`: compound (user_id, is_read) for notification queries

### Embedded vs Referenced:
- `booking_slots` embedded in bikes: enables atomic conflict detection
- `bookings` as separate collection: denormalized for dashboard queries
- This dual-write pattern trades storage for consistency and query performance

### Read vs Write Patterns:
- Marketplace browse = read-heavy (cacheable, secondary reads possible)
- Booking creation = write-heavy (needs primary, atomic operations)
- Dashboard = read-heavy per user (indexed by user_id)
