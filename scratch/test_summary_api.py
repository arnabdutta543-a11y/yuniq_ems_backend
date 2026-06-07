import requests

login_url = "http://localhost:8000/api/admin/auth/signin"
summary_url = "http://localhost:8000/api/admin/employees/attendance/summary"

# Login as user-annesha
login_payload = {
    "email": "annesha.dutta@yuniq.com",
    "password": "password"
}

print("Logging in...")
r_login = requests.post(login_url, json=login_payload)
print(f"Login status: {r_login.status_code}")
if r_login.status_code == 200:
    token = r_login.json()["access_token"]
    headers = {
        "Authorization": f"Bearer {token}"
    }
    print("Requesting attendance summary...")
    r_summary = requests.get(summary_url, headers=headers)
    print(f"Summary status: {r_summary.status_code}")
    print(f"Response: {r_summary.text[:1000]}")
else:
    print(r_login.text)
