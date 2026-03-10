"""
Test Application Onboarding Features
- Shop owner and Travel agent application submission
- Admin approve/reject applications
- Password change flow for approved users
- Smart login redirects
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "irshadxat@gmail.com"
ADMIN_PASSWORD = "admin123"

# Test data prefix
TEST_PREFIX = f"TEST_{uuid.uuid4().hex[:6]}"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    assert data["user"]["role"] == "admin", "User is not admin"
    return data["token"]


@pytest.fixture(scope="module")
def customer_token():
    """Get a customer auth token for non-admin tests"""
    email = f"{TEST_PREFIX}_customer@test.com"
    response = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": email, "password": "testpass123", "name": "Test Customer", "role": "customer", "phone": ""}
    )
    if response.status_code == 200:
        return response.json()["token"]
    # If already exists, try login
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": "testpass123"}
    )
    if response.status_code == 200:
        return response.json()["token"]
    pytest.skip("Could not create/login test customer")


class TestAdminLogin:
    """Test admin login and role"""

    def test_admin_login_success(self):
        """Admin user irshadxat@gmail.com/admin123 should work"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["role"] == "admin"
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"Admin login successful, role: {data['user']['role']}")

    def test_admin_login_wrong_password(self):
        """Admin login with wrong password should fail"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": "wrongpassword"}
        )
        assert response.status_code == 401


class TestApplicationSubmission:
    """Test public application submission endpoints"""

    def test_submit_shop_owner_application(self):
        """Shop owner application submission should work"""
        email = f"{TEST_PREFIX}_shopowner@test.com"
        data = {
            "application_type": "shop_owner",
            "name": f"{TEST_PREFIX} Shop Owner",
            "email": email,
            "phone": "+91-9876543210",
            "shop_name": f"{TEST_PREFIX} Bikes Leh",
            "shop_address": "Main Market, Leh",
            "total_bikes": 5,
            "bike_types": "Royal Enfield, KTM",
            "experience_years": 3,
            "description": "Premium bike rentals in Leh"
        }
        response = requests.post(f"{BASE_URL}/api/applications/submit", json=data)
        assert response.status_code == 200, f"Failed: {response.text}"
        result = response.json()
        assert "application" in result
        assert result["application"]["application_type"] == "shop_owner"
        assert result["application"]["status"] == "pending"
        assert result["application"]["shop_name"] == data["shop_name"]
        print(f"Shop owner application submitted: {result['application']['application_id']}")

    def test_submit_travel_agent_application(self):
        """Travel agent application submission should work"""
        email = f"{TEST_PREFIX}_travelagent@test.com"
        data = {
            "application_type": "travel_agent",
            "name": f"{TEST_PREFIX} Travel Agent",
            "email": email,
            "phone": "+91-9876543211",
            "agency_name": f"{TEST_PREFIX} Tours",
            "agency_type": "travel_agency",
            "agency_address": "Fort Road, Leh",
            "description": "Premium tour packages in Ladakh"
        }
        response = requests.post(f"{BASE_URL}/api/applications/submit", json=data)
        assert response.status_code == 200, f"Failed: {response.text}"
        result = response.json()
        assert result["application"]["application_type"] == "travel_agent"
        assert result["application"]["status"] == "pending"
        assert result["application"]["agency_name"] == data["agency_name"]
        print(f"Travel agent application submitted: {result['application']['application_id']}")

    def test_duplicate_email_rejected(self):
        """Duplicate email application should be rejected"""
        email = f"{TEST_PREFIX}_duplicate@test.com"
        data = {
            "application_type": "shop_owner",
            "name": "Duplicate Test",
            "email": email,
            "phone": "+91-9876543212",
            "shop_name": "Dup Shop",
            "shop_address": "Test Address"
        }
        # First submission
        response1 = requests.post(f"{BASE_URL}/api/applications/submit", json=data)
        assert response1.status_code == 200

        # Duplicate submission should fail
        response2 = requests.post(f"{BASE_URL}/api/applications/submit", json=data)
        assert response2.status_code == 400
        assert "already" in response2.json()["detail"].lower()
        print("Duplicate email correctly rejected")

    def test_missing_required_fields(self):
        """Application with missing required fields should fail"""
        data = {
            "application_type": "shop_owner",
            "name": "Test",
            # missing email and phone
        }
        response = requests.post(f"{BASE_URL}/api/applications/submit", json=data)
        assert response.status_code == 400

    def test_invalid_application_type(self):
        """Invalid application type should be rejected"""
        data = {
            "application_type": "invalid_type",
            "name": "Test",
            "email": f"{TEST_PREFIX}_invalid@test.com",
            "phone": "+91-9876543213"
        }
        response = requests.post(f"{BASE_URL}/api/applications/submit", json=data)
        assert response.status_code == 400


class TestApplicationsAdminEndpoints:
    """Test admin-only application management endpoints"""

    def test_list_applications_requires_admin(self, customer_token):
        """Non-admin should get 403 on applications list"""
        response = requests.get(
            f"{BASE_URL}/api/applications",
            headers={"Authorization": f"Bearer {customer_token}"}
        )
        assert response.status_code == 403
        print("Non-admin correctly blocked from applications list")

    def test_list_applications_as_admin(self, admin_token):
        """Admin should be able to list applications"""
        response = requests.get(
            f"{BASE_URL}/api/applications",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "applications" in data
        assert "total" in data
        print(f"Admin can list applications: {data['total']} total")

    def test_list_applications_with_status_filter(self, admin_token):
        """Admin should be able to filter by status"""
        response = requests.get(
            f"{BASE_URL}/api/applications?status=pending",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        # All returned should be pending
        for app in data["applications"]:
            assert app["status"] == "pending"
        print(f"Status filter works: {len(data['applications'])} pending applications")

    def test_list_applications_with_type_filter(self, admin_token):
        """Admin should be able to filter by application_type"""
        response = requests.get(
            f"{BASE_URL}/api/applications?application_type=shop_owner",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        for app in data["applications"]:
            assert app["application_type"] == "shop_owner"
        print(f"Type filter works: {len(data['applications'])} shop owner applications")


class TestApplicationApproval:
    """Test application approval flow"""

    @pytest.fixture(scope="class")
    def pending_application(self, admin_token):
        """Create a pending application for approval testing"""
        email = f"{TEST_PREFIX}_approve@test.com"
        data = {
            "application_type": "shop_owner",
            "name": f"{TEST_PREFIX} Approval Test",
            "email": email,
            "phone": "+91-9999999999",
            "shop_name": f"{TEST_PREFIX} Approval Shop",
            "shop_address": "Test Address"
        }
        response = requests.post(f"{BASE_URL}/api/applications/submit", json=data)
        if response.status_code != 200:
            pytest.skip("Could not create test application")
        return response.json()["application"]

    def test_approve_application_requires_admin(self, customer_token, pending_application):
        """Non-admin should get 403 on approve"""
        app_id = pending_application["application_id"]
        response = requests.post(
            f"{BASE_URL}/api/applications/{app_id}/approve",
            headers={"Authorization": f"Bearer {customer_token}"}
        )
        assert response.status_code == 403

    def test_approve_application_success(self, admin_token):
        """Admin should be able to approve application and get generated password"""
        # Create a fresh application for this test
        email = f"{TEST_PREFIX}_approve2@test.com"
        data = {
            "application_type": "shop_owner",
            "name": f"{TEST_PREFIX} Approve Test 2",
            "email": email,
            "phone": "+91-8888888888",
            "shop_name": f"{TEST_PREFIX} Shop 2",
            "shop_address": "Test Address 2"
        }
        submit_response = requests.post(f"{BASE_URL}/api/applications/submit", json=data)
        assert submit_response.status_code == 200
        app_id = submit_response.json()["application"]["application_id"]

        # Approve it
        response = requests.post(
            f"{BASE_URL}/api/applications/{app_id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Approval failed: {response.text}"
        result = response.json()
        
        # Verify response contains expected fields
        assert "user_id" in result
        assert "generated_password" in result
        assert "email_sent" in result
        assert len(result["generated_password"]) >= 10
        print(f"Application approved! User: {result['user_id']}, Password: {result['generated_password']}")
        
        return {"email": email, "password": result["generated_password"], "user_id": result["user_id"]}

    def test_approve_already_processed_fails(self, admin_token):
        """Approving already processed application should fail"""
        # Create and approve an application
        email = f"{TEST_PREFIX}_processed@test.com"
        data = {
            "application_type": "travel_agent",
            "name": f"{TEST_PREFIX} Processed Test",
            "email": email,
            "phone": "+91-7777777777",
            "agency_name": "Test Agency",
            "agency_type": "travel_agency"
        }
        submit_response = requests.post(f"{BASE_URL}/api/applications/submit", json=data)
        assert submit_response.status_code == 200
        app_id = submit_response.json()["application"]["application_id"]

        # First approval
        response1 = requests.post(
            f"{BASE_URL}/api/applications/{app_id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response1.status_code == 200

        # Second approval should fail
        response2 = requests.post(
            f"{BASE_URL}/api/applications/{app_id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response2.status_code == 400
        assert "already processed" in response2.json()["detail"].lower()


class TestApplicationRejection:
    """Test application rejection flow"""

    def test_reject_application_with_reason(self, admin_token):
        """Admin should be able to reject application with reason"""
        # Create application
        email = f"{TEST_PREFIX}_reject@test.com"
        data = {
            "application_type": "shop_owner",
            "name": f"{TEST_PREFIX} Reject Test",
            "email": email,
            "phone": "+91-6666666666",
            "shop_name": "Reject Shop"
        }
        submit_response = requests.post(f"{BASE_URL}/api/applications/submit", json=data)
        assert submit_response.status_code == 200
        app_id = submit_response.json()["application"]["application_id"]

        # Reject it
        response = requests.post(
            f"{BASE_URL}/api/applications/{app_id}/reject",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"reason": "Incomplete documentation"}
        )
        assert response.status_code == 200
        assert "rejected" in response.json()["message"].lower()
        print(f"Application {app_id} rejected successfully")

    def test_reject_application_requires_admin(self, customer_token):
        """Non-admin should get 403 on reject"""
        response = requests.post(
            f"{BASE_URL}/api/applications/app_nonexistent/reject",
            headers={"Authorization": f"Bearer {customer_token}"},
            json={"reason": "test"}
        )
        assert response.status_code == 403


class TestApprovedUserLogin:
    """Test login flow for approved users with password change"""

    def test_approved_user_login_has_must_change_password(self, admin_token):
        """Approved user should have must_change_password flag"""
        # Create and approve a new application
        email = f"{TEST_PREFIX}_pwchange@test.com"
        data = {
            "application_type": "shop_owner",
            "name": f"{TEST_PREFIX} PW Change Test",
            "email": email,
            "phone": "+91-5555555555",
            "shop_name": "PW Change Shop",
            "shop_address": "Test"
        }
        submit_response = requests.post(f"{BASE_URL}/api/applications/submit", json=data)
        assert submit_response.status_code == 200
        app_id = submit_response.json()["application"]["application_id"]

        # Approve
        approve_response = requests.post(
            f"{BASE_URL}/api/applications/{app_id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert approve_response.status_code == 200
        generated_password = approve_response.json()["generated_password"]

        # Login with generated password
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": generated_password}
        )
        assert login_response.status_code == 200
        user_data = login_response.json()["user"]
        
        # Verify must_change_password is True
        assert user_data.get("must_change_password") == True, "must_change_password should be True"
        assert user_data["role"] == "shop_owner"
        print(f"Approved user login successful, must_change_password={user_data['must_change_password']}")
        
        return {"email": email, "password": generated_password, "token": login_response.json()["token"]}


class TestPasswordChange:
    """Test password change endpoint"""

    def test_change_password_success(self, admin_token):
        """Password change should work and clear must_change_password"""
        # Create and approve a user
        email = f"{TEST_PREFIX}_changepw@test.com"
        data = {
            "application_type": "travel_agent",
            "name": f"{TEST_PREFIX} Change PW Test",
            "email": email,
            "phone": "+91-4444444444",
            "agency_name": "PW Test Agency",
            "agency_type": "travel_agency"
        }
        submit_response = requests.post(f"{BASE_URL}/api/applications/submit", json=data)
        assert submit_response.status_code == 200
        app_id = submit_response.json()["application"]["application_id"]

        # Approve
        approve_response = requests.post(
            f"{BASE_URL}/api/applications/{app_id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert approve_response.status_code == 200
        old_password = approve_response.json()["generated_password"]

        # Login with old password
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": old_password}
        )
        assert login_response.status_code == 200
        user_token = login_response.json()["token"]
        assert login_response.json()["user"]["must_change_password"] == True

        # Change password
        new_password = "newSecurePassword123"
        change_response = requests.post(
            f"{BASE_URL}/api/auth/change-password",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"new_password": new_password}
        )
        assert change_response.status_code == 200, f"Password change failed: {change_response.text}"
        print(f"Password changed successfully")

        # Login with new password
        new_login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": new_password}
        )
        assert new_login_response.status_code == 200
        
        # Verify must_change_password is now False
        assert new_login_response.json()["user"]["must_change_password"] == False
        print("must_change_password cleared after password change")

    def test_change_password_too_short(self, admin_token):
        """Password change with short password should fail"""
        # Create and approve a user
        email = f"{TEST_PREFIX}_shortpw@test.com"
        data = {
            "application_type": "shop_owner",
            "name": f"{TEST_PREFIX} Short PW Test",
            "email": email,
            "phone": "+91-3333333333",
            "shop_name": "Short PW Shop"
        }
        submit_response = requests.post(f"{BASE_URL}/api/applications/submit", json=data)
        assert submit_response.status_code == 200
        app_id = submit_response.json()["application"]["application_id"]

        approve_response = requests.post(
            f"{BASE_URL}/api/applications/{app_id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert approve_response.status_code == 200
        old_password = approve_response.json()["generated_password"]

        # Login
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": old_password}
        )
        user_token = login_response.json()["token"]

        # Try to change to short password
        change_response = requests.post(
            f"{BASE_URL}/api/auth/change-password",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"new_password": "123"}
        )
        assert change_response.status_code == 400
        assert "6 characters" in change_response.json()["detail"].lower()


class TestSmartLoginRedirects:
    """Test role-based login redirects (API level - actual redirects happen in frontend)"""

    def test_shop_owner_role_returned(self, admin_token):
        """Shop owner should have role=shop_owner after approval"""
        email = f"{TEST_PREFIX}_shopredirect@test.com"
        data = {
            "application_type": "shop_owner",
            "name": f"{TEST_PREFIX} Shop Redirect Test",
            "email": email,
            "phone": "+91-2222222222",
            "shop_name": "Redirect Test Shop"
        }
        submit_response = requests.post(f"{BASE_URL}/api/applications/submit", json=data)
        assert submit_response.status_code == 200
        app_id = submit_response.json()["application"]["application_id"]

        approve_response = requests.post(
            f"{BASE_URL}/api/applications/{app_id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        password = approve_response.json()["generated_password"]

        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": password}
        )
        assert login_response.json()["user"]["role"] == "shop_owner"
        print("Shop owner role correctly assigned")

    def test_travel_agent_role_returned(self, admin_token):
        """Travel agent should have role=travel_agent after approval"""
        email = f"{TEST_PREFIX}_agentredirect@test.com"
        data = {
            "application_type": "travel_agent",
            "name": f"{TEST_PREFIX} Agent Redirect Test",
            "email": email,
            "phone": "+91-1111111111",
            "agency_name": "Redirect Test Agency",
            "agency_type": "hotel"
        }
        submit_response = requests.post(f"{BASE_URL}/api/applications/submit", json=data)
        assert submit_response.status_code == 200
        app_id = submit_response.json()["application"]["application_id"]

        approve_response = requests.post(
            f"{BASE_URL}/api/applications/{app_id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        password = approve_response.json()["generated_password"]

        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": email, "password": password}
        )
        assert login_response.json()["user"]["role"] == "travel_agent"
        print("Travel agent role correctly assigned")

    def test_admin_role_confirmed(self):
        """Admin role should be returned for admin user"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert login_response.json()["user"]["role"] == "admin"
        print("Admin role correctly returned")


class TestExistingUser:
    """Test with previously approved shop owner"""

    def test_existing_shop_owner_login(self):
        """Previously approved shop owner can login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "tenzin@himalayabikes.com", "password": "newpass123"}
        )
        assert response.status_code == 200
        user = response.json()["user"]
        assert user["role"] == "shop_owner"
        # Password was already changed, so must_change_password should be False
        assert user["must_change_password"] == False
        print(f"Existing shop owner login successful: {user['name']}")
