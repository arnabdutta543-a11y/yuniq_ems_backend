import requests

base_url = "http://localhost:8000/api/admin"
endpoints = [
    "/roles",
    "/departments",
    "/offices",
    "/employees",
    "/employees/managers",
    "/employees/invitations",
    "/leaves",
    "/timesheets",
    "/travel",
    "/performance",
    "/holidays",
    "/payslips",
    "/resources",
    "/recognitions",
    "/trainings",
    "/asset-requests",
    "/announcements",
    "/policies",
    "/appraisals/",
    "/employees/attendance/summary"
]

# Login as user-annesha
login_payload = {
    "email": "annesha.dutta@yuniq.com",
    "password": "hr123"
}

r_login = requests.post(f"{base_url}/auth/signin", json=login_payload)
if r_login.status_code == 200:
    token = r_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    for ep in endpoints:
        r = requests.get(f"{base_url}{ep}", headers=headers)
        print(f"Endpoint {ep}: status={r.status_code}")
        if r.status_code != 200:
            print(f"  Error message: {r.text[:200]}")
else:
    print(f"Login failed: {r_login.text}")
