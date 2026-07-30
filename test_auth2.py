import urllib.request
import json

data = json.dumps({
    "email": "newuser@example.com",
    "phonenumber": "01700000000",
    "password": "mypassword",
    "re_type_password": "mypassword"
}).encode('utf-8')

req = urllib.request.Request("http://127.0.0.1:8000/api/accounts/register/", data=data, headers={'Content-Type': 'application/json'})
try:
    response = urllib.request.urlopen(req)
    print("Registration Response:", response.status)
    print(response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print("Error:", e.code)
    print(e.read().decode('utf-8'))
