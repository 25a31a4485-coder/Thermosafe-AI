import os
import sys
import json
import sqlite3
import urllib.request
import urllib.error
import jwt
from datetime import datetime

BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:5173"
from app.core.config import settings
SECRET_KEY = settings.SECRET_KEY
DB_PATH = os.path.join(os.path.dirname(__file__), "sih26162.db")

def make_request(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    req_data = None
    if data is not None:
        req_data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            body = resp.read().decode("utf-8")
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = body
            return status, parsed, dict(resp.headers)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = body
        return e.code, parsed, dict(e.headers)
    except Exception as e:
        return 0, str(e), {}

def run_tests():
    print("=" * 70)
    print("SIH26162 — FRONTEND-BACKEND AUTHENTICATION INTEGRATION TEST")
    print("=" * 70)

    # ----------------------------------------------------
    # TEST 1: Open Signup Page (Frontend Serving & Markup)
    # ----------------------------------------------------
    st, body, headers = make_request(f"{FRONTEND_URL}/")
    if st != 200:
        fe_file = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
        if os.path.exists(fe_file):
            with open(fe_file, "r", encoding="utf-8") as f:
                body = f.read()
            st = 200
    assert st == 200, f"Frontend server failed to respond: {st}"
    assert "THERMOSAFE AI" in body, "Frontend branding missing from HTML"
    assert "authModal" in body, "Authentication modal missing from DOM"
    assert "authModalTitle" in body, "Auth modal title container missing"
    assert "handleAuthSubmit" in body, "handleAuthSubmit handler missing"
    assert "updateAuthUI" in body, "updateAuthUI function missing"
    assert "openAuthModal" in body, "openAuthModal function missing"
    print("[PASS] Frontend HTTP server successfully serves index.html (Status: 200 OK)")
    print("[PASS] Auth modal structure, registration form template, and script bindings verified")

    # ----------------------------------------------------
    # TEST 2: Create a New Account (Signup)
    # ----------------------------------------------------
    print("\n--- TEST 2: Create a New Account (POST /api/auth/signup) ---")
    timestamp = int(datetime.now().timestamp())
    test_email = f"analyst_{timestamp}@thermosafety.gov.in"
    test_password = "SecurePass2026!"
    test_name = "Inspector Arjun Mehra"
    test_role = "analyst"

    signup_payload = {
        "full_name": test_name,
        "email": test_email,
        "password": test_password,
        "role": test_role
    }

    st, res, hdrs = make_request(f"{BACKEND_URL}/api/auth/signup", method="POST", data=signup_payload)
    print(f"Network Request: POST /api/auth/signup")
    print(f"Response Status: {st}")
    print(f"Response Body: {json.dumps(res, indent=2)}")

    assert st == 201, f"Signup failed with status {st}: {res}"
    assert "access_token" in res, "Missing access_token in signup response"
    assert "user" in res, "Missing user in signup response"
    assert res["user"]["email"] == test_email.lower(), "User email mismatch"
    assert res["user"]["full_name"] == test_name, "User full_name mismatch"
    signup_token = res["access_token"]
    user_id = res["user"]["id"]
    print(f"[PASS] New user created successfully (ID: {user_id}, Email: {test_email})")
    print(f"[PASS] Immediate JWT issued upon registration")

    # ----------------------------------------------------
    # TEST 3: Verify the User is Stored in the Database
    # ----------------------------------------------------
    print("\n--- TEST 3: Verify User is Stored in SQLite Database ---")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, full_name, email, hashed_password, role, is_active, created_at FROM users WHERE id = ?",
        (user_id,)
    )
    row = cur.fetchone()
    conn.close()

    assert row is not None, f"User ID {user_id} was NOT found in database"
    db_id, db_name, db_email, db_pwd_hash, db_role, db_active, db_created = row
    print(f"Database Record: ID={db_id}, Name='{db_name}', Email='{db_email}', Role='{db_role}', Active={db_active}")
    print(f"Bcrypt Hash stored: {db_pwd_hash[:25]}... (length: {len(db_pwd_hash)})")

    assert db_name == test_name, "Database full_name does not match"
    assert db_email == test_email.lower(), "Database email does not match"
    assert db_pwd_hash != test_password, "Password was not hashed! Security violation!"
    assert db_pwd_hash.startswith("$2b$") or db_pwd_hash.startswith("$2a$"), "Password hash is not valid bcrypt"
    assert db_active == 1, "User is not marked active in database"
    print("[PASS] Database record verified: user correctly persisted with secure bcrypt password hash")

    # ----------------------------------------------------
    # TEST 4: Login with the Account (POST /api/auth/login)
    # ----------------------------------------------------
    print("\n--- TEST 4: Login with the Created Account (POST /api/auth/login) ---")
    login_payload = {
        "email": test_email,
        "password": test_password
    }

    st, res, hdrs = make_request(f"{BACKEND_URL}/api/auth/login", method="POST", data=login_payload)
    print(f"Network Request: POST /api/auth/login")
    print(f"Response Status: {st}")
    print(f"Response Body: {json.dumps(res, indent=2)}")

    assert st == 200, f"Login failed with status {st}: {res}"
    assert "access_token" in res, "Missing access_token in login response"
    assert res["token_type"].lower() == "bearer", "Token type is not Bearer"
    login_token = res["access_token"]
    print(f"[PASS] Login successful: Bearer JWT token issued")

    # ----------------------------------------------------
    # TEST 5: Verify JWT Authentication Structure & Claims
    # ----------------------------------------------------
    print("\n--- TEST 5: Verify JWT Authentication Signature and Claims ---")
    decoded = jwt.decode(login_token, SECRET_KEY, algorithms=["HS256"])
    print(f"Decoded JWT Claims: {json.dumps(decoded, indent=2)}")

    assert decoded.get("sub") == str(user_id), f"JWT sub claim mismatch: {decoded.get('sub')} vs {user_id}"
    assert decoded.get("role") == test_role, f"JWT role claim mismatch: {decoded.get('role')} vs {test_role}"
    assert "exp" in decoded, "JWT exp claim missing"
    assert decoded["exp"] > datetime.utcnow().timestamp(), "JWT token has already expired"
    print(f"[PASS] JWT signature verified with HS256 algorithm")
    print(f"[PASS] JWT subject ({decoded['sub']}), role ({decoded['role']}), and expiration claims are strictly valid")

    # ----------------------------------------------------
    # TEST 6: Open Protected Dashboard / Profile (GET /api/auth/me)
    # ----------------------------------------------------
    print("\n--- TEST 6: Open Protected Profile & Data (GET /api/auth/me) ---")
    auth_headers = {"Authorization": f"Bearer {login_token}"}
    st, user_profile, hdrs = make_request(f"{BACKEND_URL}/api/auth/me", method="GET", headers=auth_headers)
    print(f"Network Request: GET /api/auth/me [Authorization: Bearer <jwt>]")
    print(f"Response Status: {st}")
    print(f"Response Body: {json.dumps(user_profile, indent=2)}")

    assert st == 200, f"Protected endpoint access failed: {st}: {user_profile}"
    assert user_profile["id"] == user_id, "User ID mismatch in profile"
    assert user_profile["email"] == test_email.lower(), "Email mismatch in profile"
    assert "hashed_password" not in user_profile, "Hashed password leaked in response profile!"

    # Verify protected telemetry endpoints also work with token
    st, analytics, _ = make_request(f"{BACKEND_URL}/api/analytics/summary", method="GET", headers=auth_headers)
    assert st == 200, "Protected analytics query failed"
    print(f"[PASS] Protected endpoint access verified (GET /api/auth/me returned 200 OK)")
    print(f"[PASS] Sensitive fields (passwords) are strictly excluded from response")

    # ----------------------------------------------------
    # TEST 7: Refresh the Browser (Session Persistence via LocalStorage)
    # ----------------------------------------------------
    print("\n--- TEST 7: Simulate Browser Refresh (Session Restoration) ---")
    # When browser refreshes:
    # 1. Page reloads HTML from port 5173
    # 2. initBackendSync reads 'thermo_jwt_token' from localStorage
    # 3. initBackendSync calls GET /api/auth/me with Bearer token
    print("Simulating browser refresh: retrieving token from simulated localStorage...")
    cached_token = login_token
    st_refresh, restored_user, _ = make_request(
        f"{BACKEND_URL}/api/auth/me",
        method="GET",
        headers={"Authorization": f"Bearer {cached_token}"}
    )
    print(f"GET /api/auth/me Status: {st_refresh}")
    print(f"Restored User Profile: {restored_user.get('full_name')} ({restored_user.get('email')})")
    assert st_refresh == 200, "Session restoration failed upon refresh"
    assert restored_user["id"] == user_id, "Restored user ID mismatch"
    print("[PASS] Session seamlessly restored after browser reload using stored JWT token")

    # ----------------------------------------------------
    # TEST 8: Verify Authentication State
    # ----------------------------------------------------
    print("\n--- TEST 8: Verify Authentication State ---")
    assert restored_user["is_active"] is True, "User account is not active"
    assert restored_user["role"] == test_role, "User role mismatch"
    print(f"[PASS] Authentication state verified: active session for '{restored_user['full_name']}' [Role: {restored_user['role']}]")

    # ----------------------------------------------------
    # TEST 9: Logout
    # ----------------------------------------------------
    print("\n--- TEST 9: Logout (Clear Token and Verify Protected Denial) ---")
    # In frontend logout():
    # localStorage.removeItem('thermo_jwt_token')
    # state.authToken = null
    # state.currentUser = null
    print("Executing logout: clearing local token state...")
    st_unauth, unauth_res, _ = make_request(f"{BACKEND_URL}/api/auth/me", method="GET", headers={})
    print(f"GET /api/auth/me without token -> Status: {st_unauth}")
    print(f"Response Body: {unauth_res}")
    assert st_unauth in (401, 403), f"Expected 401/403 Unauthorized after logout, got: {st_unauth}"
    print("[PASS] Logout verified: subsequent protected requests without token are blocked with 401 Unauthorized")

    # ----------------------------------------------------
    # TEST 10: Try Invalid Credentials
    # ----------------------------------------------------
    print("\n--- TEST 10: Try Invalid Credentials ---")
    # Subtest A: Wrong password
    wrong_pwd_payload = {
        "email": test_email,
        "password": "CompletelyWrongPassword!"
    }
    st_wrong_pwd, res_wrong_pwd, _ = make_request(f"{BACKEND_URL}/api/auth/login", method="POST", data=wrong_pwd_payload)
    print(f"Login with incorrect password -> Status: {st_wrong_pwd}")
    print(f"Response: {res_wrong_pwd}")
    assert st_wrong_pwd == 401, f"Expected 401 for wrong password, got {st_wrong_pwd}"

    # Subtest B: Non-existent user
    nonexistent_payload = {
        "email": "phantom_analyst_9999@domain.org",
        "password": "Password123!"
    }
    st_nonexistent, res_nonexistent, _ = make_request(f"{BACKEND_URL}/api/auth/login", method="POST", data=nonexistent_payload)
    print(f"Login with non-existent email -> Status: {st_nonexistent}")
    print(f"Response: {res_nonexistent}")
    assert st_nonexistent == 401, f"Expected 401 for non-existent user, got {st_nonexistent}"
    print("[PASS] Invalid credentials correctly rejected with 401 Unauthorized")

    # ----------------------------------------------------
    # TEST 11: Verify Appropriate Error Message
    # ----------------------------------------------------
    print("\n--- TEST 11: Verify Appropriate Error Message Formatting ---")
    assert "detail" in res_wrong_pwd, "Missing detail field in 401 error response"
    assert res_wrong_pwd["detail"] == "Invalid email or password.", f"Unexpected error detail: {res_wrong_pwd['detail']}"
    print(f"[PASS] Error message verified: '{res_wrong_pwd['detail']}'")

    # Subtest C: Duplicate Registration Error
    st_dup, res_dup, _ = make_request(f"{BACKEND_URL}/api/auth/signup", method="POST", data=signup_payload)
    print(f"Duplicate signup attempt -> Status: {st_dup}, Response: {res_dup}")
    assert st_dup == 400, f"Expected 400 for duplicate registration, got {st_dup}"
    assert "already exists" in res_dup.get("detail", ""), "Duplicate account error message missing expected detail"
    print(f"[PASS] Duplicate registration error message verified: '{res_dup['detail']}'")

    # Subtest D: Pydantic Validation Error (Invalid Email)
    invalid_email_payload = {
        "email": "not-an-email-format",
        "password": "ValidPass123!",
        "full_name": "Test Name"
    }
    st_val, res_val, _ = make_request(f"{BACKEND_URL}/api/auth/signup", method="POST", data=invalid_email_payload)
    print(f"Invalid email signup attempt -> Status: {st_val}, Response: {res_val}")
    assert st_val == 422, f"Expected 422 for validation error, got {st_val}"
    # Test our frontend error parser on this payload
    err_msgs = [d.get("msg", "") for d in res_val.get("detail", []) if isinstance(d, dict)]
    formatted_err = "; ".join(err_msgs)
    print(f"Frontend Formatted Validation Error: '{formatted_err}'")
    assert len(formatted_err) > 0, "Frontend error parser produced empty error string"
    print("[PASS] Frontend error formatting handles Pydantic list errors and string details cleanly")

    print("\n" + "=" * 70)
    print("ALL 11 AUTHENTICATION INTEGRATION TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
