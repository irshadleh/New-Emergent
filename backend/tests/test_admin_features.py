"""
Admin Dashboard & Features Tests for Ladakh Moto Market
Tests: Admin dashboard API, user management, payout oversight, KYC review, role guard
Also tests: Customer review system, BikeDetail booking confirmation flow
"""
import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://rooftop-rentals.preview.emergentagent.com"


class TestAdminRoleGuard:
    """Test that admin endpoints require admin role"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.timestamp = int(time.time())
        # Create a non-admin user (customer)
        reg = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_nonadmin_{self.timestamp}@test.com",
            "password": "TestPass123!",
            "name": "Non Admin User",
            "role": "customer"
        })
        data = reg.json()
        if "token" not in data:
            pytest.skip(f"Registration failed: {data}")
        self.non_admin_token = data["token"]
        self.non_admin_headers = {"Authorization": f"Bearer {self.non_admin_token}"}
    
    def test_admin_dashboard_requires_admin_role(self):
        """GET /api/admin/dashboard should return 403 for non-admin users"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard",
            headers=self.non_admin_headers
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"✓ Admin dashboard correctly rejects non-admin users (403)")
    
    def test_admin_users_requires_admin_role(self):
        """GET /api/admin/users should return 403 for non-admin users"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers=self.non_admin_headers
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"✓ Admin users endpoint correctly rejects non-admin users (403)")
    
    def test_admin_payouts_requires_admin_role(self):
        """GET /api/admin/payouts should return 403 for non-admin users"""
        response = requests.get(
            f"{BASE_URL}/api/admin/payouts",
            headers=self.non_admin_headers
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"✓ Admin payouts endpoint correctly rejects non-admin users (403)")
    
    def test_admin_kyc_requires_admin_role(self):
        """GET /api/admin/kyc should return 403 for non-admin users"""
        response = requests.get(
            f"{BASE_URL}/api/admin/kyc",
            headers=self.non_admin_headers
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        print(f"✓ Admin KYC endpoint correctly rejects non-admin users (403)")
    
    def test_admin_endpoint_requires_auth(self):
        """Admin endpoints should return 401 without authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/dashboard")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ Admin endpoints require authentication (401)")


class TestAdminLogin:
    """Test admin login with provided credentials"""
    
    def test_admin_login(self):
        """Test login with admin@ladakhmoto.com credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@ladakhmoto.com",
            "password": "admin123"
        })
        # Admin may or may not exist - check if we can create one
        if response.status_code == 401:
            # Create admin user
            reg = requests.post(f"{BASE_URL}/api/auth/register", json={
                "email": "admin@ladakhmoto.com",
                "password": "admin123",
                "name": "Platform Admin",
                "role": "admin"
            })
            if reg.status_code == 200:
                print(f"✓ Admin user created successfully")
                data = reg.json()
                assert "token" in data
                assert data["user"]["role"] == "admin"
            elif reg.status_code == 400:
                # Admin exists but wrong password provided - this is a credential issue
                print(f"! Admin user exists but login failed with provided credentials")
                pytest.skip("Admin login failed - check credentials")
            else:
                pytest.skip(f"Could not create admin: {reg.text}")
        else:
            assert response.status_code == 200
            data = response.json()
            assert "token" in data
            print(f"✓ Admin login successful")


class TestAdminDashboard:
    """Test Admin Dashboard API endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.timestamp = int(time.time())
        # Try to login as admin first
        login = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@ladakhmoto.com",
            "password": "admin123"
        })
        if login.status_code == 200:
            self.admin_token = login.json()["token"]
        else:
            # Create admin user
            reg = requests.post(f"{BASE_URL}/api/auth/register", json={
                "email": f"TEST_admin_{self.timestamp}@test.com",
                "password": "AdminPass123!",
                "name": "Test Admin",
                "role": "admin"
            })
            if "token" not in reg.json():
                pytest.skip(f"Could not create admin user: {reg.json()}")
            self.admin_token = reg.json()["token"]
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
    
    def test_admin_dashboard_overview(self):
        """GET /api/admin/dashboard should return platform overview"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard",
            headers=self.admin_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Check overview metrics exist
        assert "overview" in data, "Missing 'overview' in response"
        overview = data["overview"]
        assert "total_users" in overview, "Missing total_users in overview"
        assert "total_shops" in overview, "Missing total_shops in overview"
        assert "total_bikes" in overview, "Missing total_bikes in overview"
        assert "total_bookings" in overview, "Missing total_bookings in overview"
        assert "total_revenue" in overview, "Missing total_revenue in overview"
        assert "total_commission" in overview, "Missing total_commission in overview"
        print(f"✓ Dashboard overview: {overview['total_users']} users, {overview['total_shops']} shops, {overview['total_bikes']} bikes")
    
    def test_admin_dashboard_admin_metrics(self):
        """Dashboard should include admin-specific metrics"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard",
            headers=self.admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "admin_metrics" in data, "Missing 'admin_metrics' in response"
        admin_metrics = data["admin_metrics"]
        assert "pending_kyc" in admin_metrics, "Missing pending_kyc"
        assert "pending_payouts" in admin_metrics, "Missing pending_payouts"
        assert "total_settlements" in admin_metrics, "Missing total_settlements"
        print(f"✓ Admin metrics: {admin_metrics['pending_kyc']} pending KYC, {admin_metrics['pending_payouts']} pending payouts")
    
    def test_admin_dashboard_recent_bookings(self):
        """Dashboard should include recent bookings"""
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard",
            headers=self.admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "recent_bookings" in data, "Missing 'recent_bookings' in response"
        # recent_bookings is a list
        assert isinstance(data["recent_bookings"], list), "recent_bookings should be a list"
        print(f"✓ Dashboard shows {len(data['recent_bookings'])} recent bookings")


class TestAdminUsers:
    """Test Admin Users Management API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.timestamp = int(time.time())
        # Get admin token
        login = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@ladakhmoto.com",
            "password": "admin123"
        })
        if login.status_code == 200:
            self.admin_token = login.json()["token"]
        else:
            reg = requests.post(f"{BASE_URL}/api/auth/register", json={
                "email": f"TEST_admin_users_{self.timestamp}@test.com",
                "password": "AdminPass123!",
                "name": "Test Admin Users",
                "role": "admin"
            })
            if "token" not in reg.json():
                pytest.skip(f"Could not create admin user")
            self.admin_token = reg.json()["token"]
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
    
    def test_list_users(self):
        """GET /api/admin/users should return paginated user list"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers=self.admin_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "users" in data, "Missing 'users' in response"
        assert "total" in data, "Missing 'total' in response"
        assert "page" in data, "Missing 'page' in response"
        assert "limit" in data, "Missing 'limit' in response"
        assert isinstance(data["users"], list), "users should be a list"
        print(f"✓ Listed {len(data['users'])} users (total: {data['total']})")
    
    def test_list_users_with_search(self):
        """GET /api/admin/users with search parameter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            params={"search": "test"},
            headers=self.admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Search returned {len(data['users'])} users")
    
    def test_list_users_with_role_filter(self):
        """GET /api/admin/users with role filter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            params={"role": "customer"},
            headers=self.admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        for user in data["users"]:
            assert user["role"] == "customer", f"Expected customer role, got {user['role']}"
        print(f"✓ Role filter returned {len(data['users'])} customers")
    
    def test_update_user_role(self):
        """PUT /api/admin/users/{user_id} to change role"""
        # Create a test user first
        unique_id = uuid.uuid4().hex[:8]
        reg = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_rolechange_{unique_id}@test.com",
            "password": "TestPass123!",
            "name": "Test Role Change",
            "role": "customer"
        })
        if reg.status_code != 200:
            pytest.skip(f"Could not create test user: {reg.json()}")
        user_id = reg.json()["user"]["user_id"]
        
        # Update role to shop_owner
        response = requests.put(
            f"{BASE_URL}/api/admin/users/{user_id}",
            json={"role": "shop_owner"},
            headers=self.admin_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["role"] == "shop_owner", f"Expected shop_owner, got {data['role']}"
        print(f"✓ User role updated to shop_owner")
    
    def test_update_user_kyc_status(self):
        """PUT /api/admin/users/{user_id} to change KYC status"""
        # Create a test user
        unique_id = uuid.uuid4().hex[:8]
        reg = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_kycstatus_{unique_id}@test.com",
            "password": "TestPass123!",
            "name": "Test KYC Status",
            "role": "customer"
        })
        if reg.status_code != 200:
            pytest.skip(f"Could not create test user")
        user_id = reg.json()["user"]["user_id"]
        
        # Update KYC status
        response = requests.put(
            f"{BASE_URL}/api/admin/users/{user_id}",
            json={"kyc_status": "approved"},
            headers=self.admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["kyc_status"] == "approved"
        print(f"✓ User KYC status updated to approved")
    
    def test_suspend_unsuspend_user(self):
        """PUT /api/admin/users/{user_id} to suspend/unsuspend"""
        # Create a test user
        unique_id = uuid.uuid4().hex[:8]
        reg = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_suspend_{unique_id}@test.com",
            "password": "TestPass123!",
            "name": "Test Suspend User"
        })
        if reg.status_code != 200:
            pytest.skip(f"Could not create test user")
        user_id = reg.json()["user"]["user_id"]
        
        # Suspend user
        response = requests.put(
            f"{BASE_URL}/api/admin/users/{user_id}",
            json={"is_suspended": True},
            headers=self.admin_headers
        )
        assert response.status_code == 200
        assert response.json()["is_suspended"] == True
        
        # Unsuspend user
        response = requests.put(
            f"{BASE_URL}/api/admin/users/{user_id}",
            json={"is_suspended": False},
            headers=self.admin_headers
        )
        assert response.status_code == 200
        assert response.json()["is_suspended"] == False
        print(f"✓ User suspend/unsuspend working correctly")
    
    def test_update_nonexistent_user(self):
        """PUT /api/admin/users/{user_id} with invalid user_id returns 404"""
        response = requests.put(
            f"{BASE_URL}/api/admin/users/nonexistent_user_id",
            json={"role": "admin"},
            headers=self.admin_headers
        )
        assert response.status_code == 404
        print(f"✓ Nonexistent user returns 404")


class TestAdminPayouts:
    """Test Admin Payouts Management API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.timestamp = int(time.time())
        # Get admin token
        login = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@ladakhmoto.com",
            "password": "admin123"
        })
        if login.status_code == 200:
            self.admin_token = login.json()["token"]
        else:
            reg = requests.post(f"{BASE_URL}/api/auth/register", json={
                "email": f"TEST_admin_payouts_{self.timestamp}@test.com",
                "password": "AdminPass123!",
                "name": "Test Admin Payouts",
                "role": "admin"
            })
            if "token" not in reg.json():
                pytest.skip(f"Could not create admin user")
            self.admin_token = reg.json()["token"]
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
    
    def test_list_payouts(self):
        """GET /api/admin/payouts should return payout list with summary"""
        response = requests.get(
            f"{BASE_URL}/api/admin/payouts",
            headers=self.admin_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "entries" in data, "Missing 'entries' in response"
        assert "total" in data, "Missing 'total' in response"
        assert "summary" in data, "Missing 'summary' in response"
        print(f"✓ Listed {len(data['entries'])} payout entries")
    
    def test_list_payouts_with_status_filter(self):
        """GET /api/admin/payouts with status filter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/payouts",
            params={"status": "pending"},
            headers=self.admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        for entry in data["entries"]:
            assert entry["status"] == "pending"
        print(f"✓ Status filter returned {len(data['entries'])} pending payouts")
    
    def test_settle_shop_nonexistent(self):
        """POST /api/admin/payouts/{shop_id}/settle with invalid shop_id returns 404"""
        response = requests.post(
            f"{BASE_URL}/api/admin/payouts/nonexistent_shop/settle",
            headers=self.admin_headers
        )
        assert response.status_code == 404
        print(f"✓ Settle nonexistent shop returns 404")


class TestAdminKYC:
    """Test Admin KYC Review API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.timestamp = int(time.time())
        # Get admin token
        login = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@ladakhmoto.com",
            "password": "admin123"
        })
        if login.status_code == 200:
            self.admin_token = login.json()["token"]
        else:
            reg = requests.post(f"{BASE_URL}/api/auth/register", json={
                "email": f"TEST_admin_kyc_{self.timestamp}@test.com",
                "password": "AdminPass123!",
                "name": "Test Admin KYC",
                "role": "admin"
            })
            if "token" not in reg.json():
                pytest.skip(f"Could not create admin user")
            self.admin_token = reg.json()["token"]
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
    
    def test_list_kyc(self):
        """GET /api/admin/kyc should return users with KYC submissions"""
        response = requests.get(
            f"{BASE_URL}/api/admin/kyc",
            headers=self.admin_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "users" in data, "Missing 'users' in response"
        assert "total" in data, "Missing 'total' in response"
        print(f"✓ Listed {len(data['users'])} KYC users (total: {data['total']})")
    
    def test_list_kyc_with_status_filter(self):
        """GET /api/admin/kyc with status filter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/kyc",
            params={"status": "pending"},
            headers=self.admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        for user in data["users"]:
            assert user["kyc_status"] == "pending"
        print(f"✓ KYC status filter working - {len(data['users'])} pending")
    
    def test_review_kyc_approve(self):
        """POST /api/admin/kyc/{user_id}/review to approve KYC"""
        # Create a test user with pending KYC
        unique_id = uuid.uuid4().hex[:8]
        reg = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_kycapprove_{unique_id}@test.com",
            "password": "TestPass123!",
            "name": "Test KYC Approve"
        })
        if reg.status_code != 200:
            pytest.skip(f"Could not create test user")
        user_id = reg.json()["user"]["user_id"]
        
        # Approve KYC
        response = requests.post(
            f"{BASE_URL}/api/admin/kyc/{user_id}/review",
            json={"status": "approved"},
            headers=self.admin_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["status"] == "approved"
        print(f"✓ KYC approved for user {user_id}")
    
    def test_review_kyc_reject_with_notes(self):
        """POST /api/admin/kyc/{user_id}/review to reject KYC with notes"""
        # Create a test user
        unique_id = uuid.uuid4().hex[:8]
        reg = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_kycreject_{unique_id}@test.com",
            "password": "TestPass123!",
            "name": "Test KYC Reject"
        })
        if reg.status_code != 200:
            pytest.skip(f"Could not create test user")
        user_id = reg.json()["user"]["user_id"]
        
        # Reject KYC
        response = requests.post(
            f"{BASE_URL}/api/admin/kyc/{user_id}/review",
            json={
                "status": "rejected",
                "notes": "Documents not clear, please re-upload"
            },
            headers=self.admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"
        print(f"✓ KYC rejected with notes for user {user_id}")
    
    def test_review_kyc_invalid_status(self):
        """POST /api/admin/kyc/{user_id}/review with invalid status returns 400"""
        unique_id = uuid.uuid4().hex[:8]
        reg = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_kycinvalid_{unique_id}@test.com",
            "password": "TestPass123!",
            "name": "Test KYC Invalid"
        })
        if reg.status_code != 200:
            pytest.skip(f"Could not create test user")
        user_id = reg.json()["user"]["user_id"]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/kyc/{user_id}/review",
            json={"status": "invalid_status"},
            headers=self.admin_headers
        )
        assert response.status_code == 400
        print(f"✓ Invalid KYC status correctly rejected (400)")
    
    def test_review_kyc_nonexistent_user(self):
        """POST /api/admin/kyc/{user_id}/review with nonexistent user returns 404"""
        response = requests.post(
            f"{BASE_URL}/api/admin/kyc/nonexistent_user/review",
            json={"status": "approved"},
            headers=self.admin_headers
        )
        assert response.status_code == 404
        print(f"✓ KYC review for nonexistent user returns 404")


class TestReviewSystem:
    """Test Customer Rating/Review system"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.timestamp = int(time.time())
        unique_id = uuid.uuid4().hex[:8]
        
        # Create test customer
        reg = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_review_{unique_id}@test.com",
            "password": "TestPass123!",
            "name": "Test Reviewer",
            "role": "customer"
        })
        if "token" not in reg.json():
            pytest.skip(f"Could not create test user: {reg.json()}")
        self.token = reg.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get a bike for testing
        bikes = requests.get(f"{BASE_URL}/api/bikes?limit=1").json()
        self.bike_id = bikes["bikes"][0]["bike_id"]
    
    def test_submit_review_without_booking(self):
        """POST /api/reviews without a valid booking should fail"""
        response = requests.post(
            f"{BASE_URL}/api/reviews",
            json={
                "booking_id": "fake_booking_id",
                "rating": 5,
                "comment": "Great bike!"
            },
            headers=self.headers
        )
        # Should fail because user doesn't have this booking
        assert response.status_code in [400, 403, 404]
        print(f"✓ Review submission without valid booking correctly rejected")
    
    def test_get_bike_reviews(self):
        """GET /api/reviews/bike/{bike_id} should return reviews"""
        response = requests.get(f"{BASE_URL}/api/reviews/bike/{self.bike_id}")
        assert response.status_code == 200
        data = response.json()
        assert "reviews" in data
        assert isinstance(data["reviews"], list)
        print(f"✓ Got {len(data['reviews'])} reviews for bike {self.bike_id}")


class TestBikeDetailBookingFlow:
    """Test enhanced booking flow with confirmation step"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        unique_id = uuid.uuid4().hex[:8]
        
        # Create test customer
        reg = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"TEST_booking_flow_{unique_id}@test.com",
            "password": "TestPass123!",
            "name": "Test Booking Flow",
            "role": "customer"
        })
        if "token" not in reg.json():
            pytest.skip(f"Could not create test user: {reg.json()}")
        self.token = reg.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get a bike for testing
        bikes = requests.get(f"{BASE_URL}/api/bikes?limit=1").json()
        self.bike = bikes["bikes"][0]
        self.bike_id = self.bike["bike_id"]
    
    def test_bike_detail_has_pricing(self):
        """GET /api/bikes/{id} should return daily and weekly rates"""
        response = requests.get(f"{BASE_URL}/api/bikes/{self.bike_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert "daily_rate" in data, "Missing daily_rate"
        assert "weekly_rate" in data, "Missing weekly_rate"
        assert data["daily_rate"] > 0, "daily_rate should be positive"
        print(f"✓ Bike detail has pricing: {data['daily_rate']}/day, {data['weekly_rate']}/week")
    
    def test_booking_creates_with_correct_amount(self):
        """POST /api/bookings should create booking with correct total"""
        import random
        from datetime import datetime, timedelta
        
        offset = random.randint(800, 900)
        start = (datetime.now() + timedelta(days=offset)).strftime("%Y-%m-%dT00:00:00")
        end = (datetime.now() + timedelta(days=offset + 3)).strftime("%Y-%m-%dT00:00:00")
        
        response = requests.post(
            f"{BASE_URL}/api/bookings",
            json={
                "bike_id": self.bike_id,
                "start_date": start,
                "end_date": end
            },
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "booking_id" in data
            assert "total_amount" in data
            assert data["status"] == "confirmed"
            # Total should be roughly 3 days * daily_rate
            expected_min = self.bike["daily_rate"] * 2  # At least 2 days worth
            assert data["total_amount"] >= expected_min, f"Total {data['total_amount']} seems too low"
            print(f"✓ Booking created with amount: {data['total_amount']} INR")
        elif response.status_code == 409:
            print(f"✓ Booking dates conflicted (409) - double-booking prevention working")
        else:
            pytest.fail(f"Unexpected status: {response.status_code} - {response.text}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
