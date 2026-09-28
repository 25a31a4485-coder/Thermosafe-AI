import urllib.request
import urllib.error
import json
import sys

import time
BASE_URL = "http://127.0.0.1:8000"

def request(path, method="GET", data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            content = resp.read().decode("utf-8")
            return status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            return e.code, json.loads(content)
        except Exception:
            return e.code, {"error": content}

def run_tests():
    print("=" * 60)
    print("RUNNING AUTHENTICATION TEST SUITE")
    print("=" * 60)
    
    ts = int(time.time())
    test_email = f"analyst_{ts}@thermosafe.ai"

    # 1. Test Signup
    print("\n1. Testing User Signup...")
    signup_data = {
        "email": test_email,
        "full_name": "Senior Thermal Analyst",
        "password": "SecurePassword123!",
        "role": "analyst"
    }
    code, res = request("/api/auth/signup", method="POST", data=signup_data)
    print(f"   Status: {code}")
    assert code == 201, f"Expected 201, got {code}: {res}"
    assert "access_token" in res, "Expected access_token in response"
    assert "hashed_password" not in res.get("user", {}), "Hashed password must not be exposed!"
    print(f"   [PASS] User signed up successfully. Token obtained: {res['access_token'][:20]}...")
    token = res["access_token"]
    user_id = res["user"]["id"]

    # 2. Test Duplicate Signup
    print("\n2. Testing Duplicate Signup Prevention...")
    code, res = request("/api/auth/signup", method="POST", data=signup_data)
    print(f"   Status: {code}")
    assert code == 400, f"Expected 400, got {code}: {res}"
    print(f"   [PASS] Duplicate account rejected with message: {res.get('detail')}")

    # 3. Test Login (Valid)
    print("\n3. Testing Valid Login...")
    login_data = {
        "email": test_email,
        "password": "SecurePassword123!"
    }
    code, res = request("/api/auth/login", method="POST", data=login_data)
    print(f"   Status: {code}")
    assert code == 200, f"Expected 200, got {code}: {res}"
    assert "access_token" in res, "Expected access_token in response"
    assert "hashed_password" not in res.get("user", {}), "Hashed password must not be exposed!"
    login_token = res["access_token"]
    print(f"   [PASS] Login successful. New token: {login_token[:20]}...")

    # 4. Test Invalid Login (Wrong Password)
    print("\n4. Testing Invalid Login (Wrong Password)...")
    bad_login = {
        "email": test_email,
        "password": "WrongPassword999"
    }
    code, res = request("/api/auth/login", method="POST", data=bad_login)
    print(f"   Status: {code}")
    assert code == 401, f"Expected 401, got {code}: {res}"
    print(f"   [PASS] Invalid login rejected with message: {res.get('detail')}")

    # 5. Test /api/auth/me with Valid Token
    print("\n5. Testing /api/auth/me with Valid Token...")
    code, res = request("/api/auth/me", method="GET", token=login_token)
    print(f"   Status: {code}")
    assert code == 200, f"Expected 200, got {code}: {res}"
    assert res["id"] == user_id, f"Expected user_id {user_id}, got {res['id']}"
    assert res["email"] == test_email
    assert res["role"] == "analyst"
    assert "hashed_password" not in res
    print(f"   [PASS] /me returned user profile for: {res['email']} (Role: {res['role']})")

    # 6. Test /api/auth/me without Token
    print("\n6. Testing /api/auth/me without Token...")
    code, res = request("/api/auth/me", method="GET")
    print(f"   Status: {code}")
    assert code == 401, f"Expected 401, got {code}: {res}"
    print(f"   [PASS] Unauthorized request rejected with message: {res.get('detail')}")

    # 7. Test /api/auth/me with Invalid Token
    print("\n7. Testing /api/auth/me with Invalid Token...")
    code, res = request("/api/auth/me", method="GET", token="invalid.bearer.token123")
    print(f"   Status: {code}")
    assert code == 401, f"Expected 401, got {code}: {res}"
    print(f"   [PASS] Invalid token rejected with message: {res.get('detail')}")

    # 8. Test Role Creation (Admin and Viewer)
    print("\n8. Testing Role Support (Admin & Viewer)...")
    for role, base_email in [("admin", f"admin_{ts}@ntro.gov.in"), ("viewer", f"viewer_{ts}@disaster.in")]:
        d = {
            "email": base_email,
            "full_name": f"Test {role.capitalize()}",
            "password": "RolePassword123!",
            "role": role
        }
        code, res = request("/api/auth/signup", method="POST", data=d)
        assert code == 201, f"Expected 201 for {role}, got {code}: {res}"
        assert res["user"]["role"] == role
        print(f"   [PASS] Registered {role} user: {base_email} with role={res['user']['role']}")

    print("\n" + "=" * 60)
    print("ALL 8 AUTHENTICATION TESTS PASSED PERFECTLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
