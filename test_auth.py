import urllib.request
import json

data = json.dumps({
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpassword123"
}).encode('utf-8')

req = urllib.request.Request("http://127.0.0.1:8000/api/accounts/register/", data=data, headers={'Content-Type': 'application/json'})
try:
    response = urllib.request.urlopen(req)
    print("Registration Response:", response.status)
    print(response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print("Error:", e.code)
    print(e.read().decode('utf-8'))

data_login = json.dumps({
    "username": "testuser",
    "password": "testpassword123"
}).encode('utf-8')

req_login = urllib.request.Request("http://127.0.0.1:8000/api/accounts/login/", data=data_login, headers={'Content-Type': 'application/json'})
try:
    response_login = urllib.request.urlopen(req_login)
    print("Login Response:", response_login.status)
    print(response_login.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print("Login Error:", e.code)
    print(e.read().decode('utf-8'))
