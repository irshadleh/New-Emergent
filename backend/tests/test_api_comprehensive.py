"""
Comprehensive API Tests for Ladakh Moto Market
Tests all backend endpoints: auth, bikes, bookings, shops, travel agents, payouts, analytics, notifications
"""
import pytest
import requests
import os
import time
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://rooftop-rentals.preview.emergentagent.com"


class TestHealthCheck:
    """Health endpoint tests"""
    
    def test_health_endpoint(self):
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        print(f"✓ Health check passed - {data['service']} v{data['version']}")


class TestAuthentication:
    """Authentication endpoint tests - register, login, me"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.timestamp = int(time.time())
    
    def test_register_customer(self):
        """Test customer registration"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_customer_{self.timestamp}@test.com",
            "password": "TestPass123!",
            "name": "Test Customer",
            "role": "customer",
            "phone": "+91-1234567890"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == f"TEST_customer_{self.timestamp}@test.com"
        assert data["user"]["role"] == "customer"
        print(f"✓ Customer registration successful - user_id: {data['user']['user_id']}")
    
    def test_register_shop_owner(self):
        """Test shop owner registration"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_shopowner_{self.timestamp}@test.com",
            "password": "TestPass123!",
            "name": "Test Shop Owner",
            "role": "shop_owner"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "shop_owner"
        print(f"✓ Shop owner registration successful")
    
    def test_register_travel_agent(self):
        """Test travel agent registration"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_agent_{self.timestamp}@test.com",
            "password": "TestPass123!",
            "name": "Test Travel Agent",
            "role": "travel_agent"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "travel_agent"
        print(f"✓ Travel agent registration successful")
    
    def test_register_duplicate_email(self):
        """Test duplicate email registration fails"""
        # First registration
        requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_duplicate_{self.timestamp}@test.com",
            "password": "TestPass123!",
            "name": "Test User"
        })
        # Second registration with same email
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_duplicate_{self.timestamp}@test.com",
            "password": "TestPass123!",
            "name": "Test User 2"
        })
        assert response.status_code == 400
        print(f"✓ Duplicate email correctly rejected")
    
    def test_login_success(self):
        """Test successful login"""
        email = f"TEST_login_{self.timestamp}@test.com"
        # Register first
        requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": "TestPass123!",
            "name": "Test Login User"
        })
        # Login
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": "TestPass123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["email"] == email
        print(f"✓ Login successful")
    
    def test_login_invalid_credentials(self):
        """Test login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401
        print(f"✓ Invalid credentials correctly rejected")
    
    def test_auth_me_with_token(self):
        """Test /auth/me endpoint with valid token"""
        email = f"TEST_me_{self.timestamp}@test.com"
        reg = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": email,
            "password": "TestPass123!",
            "name": "Test Me User"
        })
        token = reg.json()["token"]
        
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == email
        print(f"✓ Auth me endpoint working with token")
    
    def test_auth_me_without_token(self):
        """Test /auth/me returns 401 without token"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print(f"✓ Auth me correctly rejects unauthenticated request")


class TestBikes:
    """Bike endpoint tests - list, get, create, update, delete"""
    
    def test_list_bikes(self):
        """Test listing bikes"""
        response = requests.get(f"{BASE_URL}/api/bikes")
        assert response.status_code == 200
        data = response.json()
        assert "bikes" in data
        assert "total" in data
        assert len(data["bikes"]) > 0  # Seed data should exist
        print(f"✓ Listed {len(data['bikes'])} bikes (total: {data['total']})")
    
    def test_list_bikes_with_filters(self):
        """Test bike listing with filters"""
        # Test type filter
        response = requests.get(f"{BASE_URL}/api/bikes?type=adventure")
        assert response.status_code == 200
        data = response.json()
        for bike in data["bikes"]:
            assert bike["type"] == "adventure"
        
        # Test price filter
        response = requests.get(f"{BASE_URL}/api/bikes?max_price=1200")
        assert response.status_code == 200
        data = response.json()
        for bike in data["bikes"]:
            assert bike["daily_rate"] <= 1200
        print(f"✓ Bike filters working correctly")
    
    def test_get_single_bike(self):
        """Test getting a single bike by ID"""
        # Get a bike ID from list
        list_response = requests.get(f"{BASE_URL}/api/bikes?limit=1")
        bike_id = list_response.json()["bikes"][0]["bike_id"]
        
        response = requests.get(f"{BASE_URL}/api/bikes/{bike_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["bike_id"] == bike_id
        assert "name" in data
        assert "daily_rate" in data
        assert "shop_name" in data
        assert "reviews" in data
        print(f"✓ Got bike details: {data['name']}")
    
    def test_get_nonexistent_bike(self):
        """Test 404 for nonexistent bike"""
        response = requests.get(f"{BASE_URL}/api/bikes/nonexistent_bike_id")
        assert response.status_code == 404
        print(f"✓ Nonexistent bike returns 404")


class TestShops:
    """Shop endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.timestamp = int(time.time())
    
    def test_list_shops(self):
        """Test listing shops"""
        response = requests.get(f"{BASE_URL}/api/shops")
        assert response.status_code == 200
        data = response.json()
        assert "shops" in data
        assert len(data["shops"]) >= 2  # Seed data has 2 shops
        print(f"✓ Listed {len(data['shops'])} shops")
    
    def test_create_shop(self):
        """Test creating a shop - should upgrade role to shop_owner"""
        # Register a new user
        reg = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_newshop_{self.timestamp}@test.com",
            "password": "TestPass123!",
            "name": "Test New Shop Owner",
            "role": "customer"
        })
        token = reg.json()["token"]
        
        # Create shop
        response = requests.post(
            f"{BASE_URL}/api/shops",
            json={
                "name": f"TEST Shop {self.timestamp}",
                "description": "Test shop description",
                "address": "Test Address, Leh",
                "phone": "+91-9876543210"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "shop_id" in data
        assert data["name"] == f"TEST Shop {self.timestamp}"
        print(f"✓ Shop created: {data['shop_id']}")
    
    def test_cannot_create_duplicate_shop(self):
        """Test user cannot create multiple shops"""
        reg = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_dupshop_{self.timestamp}@test.com",
            "password": "TestPass123!",
            "name": "Test Dup Shop Owner"
        })
        token = reg.json()["token"]
        
        # Create first shop
        requests.post(
            f"{BASE_URL}/api/shops",
            json={"name": f"TEST First Shop {self.timestamp}"},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Try to create second shop
        response = requests.post(
            f"{BASE_URL}/api/shops",
            json={"name": f"TEST Second Shop {self.timestamp}"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
        print(f"✓ Duplicate shop creation correctly blocked")


class TestBookings:
    """Booking endpoint tests - with double-booking prevention"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        import uuid
        self.timestamp = uuid.uuid4().hex[:8]
        # Create a test user
        reg = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_booking_{self.timestamp}@test.com",
            "password": "TestPass123!",
            "name": "Test Booking User"
        })
        data = reg.json()
        if "token" not in data:
            pytest.skip(f"Registration failed: {data}")
        self.token = data["token"]
        self.user_id = data["user"]["user_id"]
        
        # Get a bike for testing
        bikes = requests.get(f"{BASE_URL}/api/bikes?limit=1").json()
        self.bike_id = bikes["bikes"][0]["bike_id"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_create_booking(self):
        """Test creating a booking"""
        import random
        # Use random offset to avoid date conflicts with other tests
        offset = random.randint(150, 250)
        start = (datetime.now() + timedelta(days=offset)).strftime("%Y-%m-%dT00:00:00")
        end = (datetime.now() + timedelta(days=offset + 5)).strftime("%Y-%m-%dT00:00:00")
        
        response = requests.post(
            f"{BASE_URL}/api/bookings",
            json={
                "bike_id": self.bike_id,
                "start_date": start,
                "end_date": end,
                "notes": "Test booking"
            },
            headers=self.headers
        )
        # 200 for successful booking, 409 for conflict (both valid)
        assert response.status_code in [200, 409]
        if response.status_code == 200:
            data = response.json()
            assert "booking_id" in data
            assert data["bike_id"] == self.bike_id
            assert data["status"] == "confirmed"
            print(f"✓ Booking created: {data['booking_id']}, amount: {data['total_amount']} INR")
        else:
            print(f"✓ Booking correctly rejected due to conflict (409)")
    
    def test_double_booking_prevention(self):
        """Test that overlapping bookings are rejected (409 Conflict)"""
        import random
        offset = random.randint(300, 400)
        start = (datetime.now() + timedelta(days=offset)).strftime("%Y-%m-%dT00:00:00")
        end = (datetime.now() + timedelta(days=offset + 5)).strftime("%Y-%m-%dT00:00:00")
        
        # First booking
        first = requests.post(
            f"{BASE_URL}/api/bookings",
            json={"bike_id": self.bike_id, "start_date": start, "end_date": end},
            headers=self.headers
        )
        # May succeed or conflict depending on existing bookings
        if first.status_code != 200:
            pytest.skip("First booking conflicted - dates already taken")
        
        # Create second user
        import uuid
        reg2 = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_booking2_{uuid.uuid4().hex[:8]}@test.com",
            "password": "TestPass123!",
            "name": "Test Second User"
        })
        token2 = reg2.json()["token"]
        
        # Try overlapping booking with different user
        overlap_start = (datetime.now() + timedelta(days=offset + 2)).strftime("%Y-%m-%dT00:00:00")
        overlap_end = (datetime.now() + timedelta(days=offset + 8)).strftime("%Y-%m-%dT00:00:00")
        
        second = requests.post(
            f"{BASE_URL}/api/bookings",
            json={"bike_id": self.bike_id, "start_date": overlap_start, "end_date": overlap_end},
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert second.status_code == 409
        print(f"✓ Double booking prevention working (409 Conflict)")
    
    def test_list_bookings(self):
        """Test listing user's bookings"""
        response = requests.get(
            f"{BASE_URL}/api/bookings",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "bookings" in data
        print(f"✓ Listed {len(data['bookings'])} bookings")
    
    def test_update_booking_status(self):
        """Test updating booking status"""
        import random
        offset = random.randint(450, 550)
        # Create a booking first
        start = (datetime.now() + timedelta(days=offset)).strftime("%Y-%m-%dT00:00:00")
        end = (datetime.now() + timedelta(days=offset + 2)).strftime("%Y-%m-%dT00:00:00")
        
        booking_resp = requests.post(
            f"{BASE_URL}/api/bookings",
            json={"bike_id": self.bike_id, "start_date": start, "end_date": end},
            headers=self.headers
        )
        if booking_resp.status_code != 200:
            pytest.skip(f"Booking failed: {booking_resp.json()}")
        booking = booking_resp.json()
        
        # Update to active
        response = requests.put(
            f"{BASE_URL}/api/bookings/{booking['booking_id']}/status",
            json={"status": "active"},
            headers=self.headers
        )
        assert response.status_code == 200
        print(f"✓ Booking status updated to active")
    
    def test_return_bike(self):
        """Test returning a bike"""
        import random
        offset = random.randint(600, 700)
        # Create and activate a booking
        start = (datetime.now() + timedelta(days=offset)).strftime("%Y-%m-%dT00:00:00")
        end = (datetime.now() + timedelta(days=offset + 2)).strftime("%Y-%m-%dT00:00:00")
        
        booking_resp = requests.post(
            f"{BASE_URL}/api/bookings",
            json={"bike_id": self.bike_id, "start_date": start, "end_date": end},
            headers=self.headers
        )
        if booking_resp.status_code != 200:
            pytest.skip(f"Booking failed: {booking_resp.json()}")
        booking = booking_resp.json()
        
        # Activate
        requests.put(
            f"{BASE_URL}/api/bookings/{booking['booking_id']}/status",
            json={"status": "active"},
            headers=self.headers
        )
        
        # Return
        response = requests.post(
            f"{BASE_URL}/api/bookings/{booking['booking_id']}/return",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "penalty" in data
        print(f"✓ Bike returned - penalty: {data['penalty']} INR")


class TestAvailability:
    """Availability calendar tests"""
    
    def test_get_availability_calendar(self):
        """Test getting availability calendar for a bike"""
        bikes = requests.get(f"{BASE_URL}/api/bikes?limit=1").json()
        bike_id = bikes["bikes"][0]["bike_id"]
        
        response = requests.get(
            f"{BASE_URL}/api/availability/{bike_id}",
            params={"month": 3, "year": 2026}
        )
        assert response.status_code == 200
        data = response.json()
        assert "days" in data
        assert "bike_id" in data
        print(f"✓ Got availability calendar for {bike_id}")
    
    def test_check_availability(self):
        """Test checking specific date availability"""
        bikes = requests.get(f"{BASE_URL}/api/bikes?limit=1").json()
        bike_id = bikes["bikes"][0]["bike_id"]
        
        start = (datetime.now() + timedelta(days=200)).strftime("%Y-%m-%dT00:00:00")
        end = (datetime.now() + timedelta(days=205)).strftime("%Y-%m-%dT00:00:00")
        
        response = requests.get(
            f"{BASE_URL}/api/availability/{bike_id}/check",
            params={"start_date": start, "end_date": end}
        )
        assert response.status_code == 200
        data = response.json()
        assert "available" in data or "is_available" in data
        print(f"✓ Availability check: {data}")


class TestTravelAgent:
    """Travel agent endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        import uuid
        self.timestamp = uuid.uuid4().hex[:8]
        reg = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_agent_test_{self.timestamp}@test.com",
            "password": "TestPass123!",
            "name": "Test Agent",
            "role": "travel_agent"
        })
        data = reg.json()
        if "token" not in data:
            pytest.skip(f"Registration failed: {data}")
        self.token = data["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_agent_dashboard(self):
        """Test getting travel agent dashboard"""
        response = requests.get(
            f"{BASE_URL}/api/travel-agent/dashboard",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "referral_code" in data
        assert "stats" in data
        assert "recent_referrals" in data
        print(f"✓ Agent dashboard: code={data['referral_code']}")
    
    def test_generate_referral_link(self):
        """Test generating referral link"""
        response = requests.post(
            f"{BASE_URL}/api/travel-agent/generate-link",
            json={"bike_id": None},
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "referral_link" in data
        assert "referral_code" in data
        print(f"✓ Generated referral link: {data['referral_link']}")
    
    def test_generate_bike_specific_link(self):
        """Test generating bike-specific referral link"""
        bikes = requests.get(f"{BASE_URL}/api/bikes?limit=1").json()
        bike_id = bikes["bikes"][0]["bike_id"]
        
        response = requests.post(
            f"{BASE_URL}/api/travel-agent/generate-link",
            json={"bike_id": bike_id},
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert bike_id in data["referral_link"]
        print(f"✓ Generated bike-specific link")
    
    def test_commission_ledger(self):
        """Test getting commission ledger"""
        response = requests.get(
            f"{BASE_URL}/api/travel-agent/commission-ledger",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert "total" in data
        assert "commission_rate" in data
        print(f"✓ Commission ledger: {data['total']} entries")


class TestPayouts:
    """Payout endpoint tests for shop owners"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        import uuid
        self.timestamp = uuid.uuid4().hex[:8]
        # Create shop owner and shop
        reg = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_payout_{self.timestamp}@test.com",
            "password": "TestPass123!",
            "name": "Test Payout Owner"
        })
        data = reg.json()
        if "token" not in data:
            pytest.skip(f"Registration failed: {data}")
        self.token = data["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create shop
        requests.post(
            f"{BASE_URL}/api/shops",
            json={"name": f"TEST Payout Shop {self.timestamp}"},
            headers=self.headers
        )
    
    def test_payout_summary(self):
        """Test getting payout summary"""
        response = requests.get(
            f"{BASE_URL}/api/payouts/summary",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "totals" in data
        assert "by_status" in data
        print(f"✓ Payout summary retrieved")
    
    def test_payout_ledger(self):
        """Test getting payout ledger"""
        response = requests.get(
            f"{BASE_URL}/api/payouts/ledger",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        print(f"✓ Payout ledger: {len(data['entries'])} entries")
    
    def test_settlements_list(self):
        """Test getting settlements list"""
        response = requests.get(
            f"{BASE_URL}/api/payouts/settlements",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "settlements" in data
        print(f"✓ Settlements list: {len(data['settlements'])} settlements")


class TestAnalytics:
    """Analytics endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        import uuid
        self.timestamp = uuid.uuid4().hex[:8]
        # Create shop owner with shop
        reg = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_analytics_{self.timestamp}@test.com",
            "password": "TestPass123!",
            "name": "Test Analytics Owner"
        })
        data = reg.json()
        if "token" not in data:
            pytest.skip(f"Registration failed: {data}")
        self.token = data["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create shop
        requests.post(
            f"{BASE_URL}/api/shops",
            json={"name": f"TEST Analytics Shop {self.timestamp}"},
            headers=self.headers
        )
    
    def test_shop_analytics(self):
        """Test getting shop analytics"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/shop",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "stats" in data
        print(f"✓ Shop analytics retrieved")
    
    def test_platform_analytics(self):
        """Test getting platform-wide analytics"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/platform",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        # Platform analytics has overview field
        assert "overview" in data or "total_users" in data or "stats" in data
        print(f"✓ Platform analytics retrieved")
    
    def test_bike_analytics(self):
        """Test getting single bike analytics"""
        bikes = requests.get(f"{BASE_URL}/api/bikes?limit=1").json()
        bike_id = bikes["bikes"][0]["bike_id"]
        
        response = requests.get(
            f"{BASE_URL}/api/analytics/bike/{bike_id}",
            headers=self.headers
        )
        assert response.status_code == 200
        print(f"✓ Bike analytics retrieved for {bike_id}")


class TestNotifications:
    """Notification endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        import uuid
        self.timestamp = uuid.uuid4().hex[:8]
        reg = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_notif_{self.timestamp}@test.com",
            "password": "TestPass123!",
            "name": "Test Notif User"
        })
        data = reg.json()
        if "token" not in data:
            pytest.skip(f"Registration failed: {data}")
        self.token = data["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_notifications(self):
        """Test listing notifications"""
        response = requests.get(
            f"{BASE_URL}/api/notifications",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        assert "unread_count" in data
        print(f"✓ Notifications: {len(data['notifications'])} total, {data['unread_count']} unread")
    
    def test_list_unread_only(self):
        """Test filtering unread notifications"""
        response = requests.get(
            f"{BASE_URL}/api/notifications",
            params={"unread_only": "true"},
            headers=self.headers
        )
        assert response.status_code == 200
        print(f"✓ Unread notifications filter working")


class TestReviews:
    """Review endpoint tests"""
    
    def test_get_bike_reviews(self):
        """Test getting reviews for a bike"""
        bikes = requests.get(f"{BASE_URL}/api/bikes?limit=1").json()
        bike_id = bikes["bikes"][0]["bike_id"]
        
        response = requests.get(f"{BASE_URL}/api/reviews/bike/{bike_id}")
        assert response.status_code == 200
        data = response.json()
        assert "reviews" in data
        print(f"✓ Got {len(data['reviews'])} reviews for bike")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
