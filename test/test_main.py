from starlette.testclient import TestClient
from app.main import app, version
import requests


# get an global access token
client = TestClient(app)
resp = client.post(f"/{version}/auth/login",
                   {"username": "testuser0", "password": "secret"})
TOKEN = resp.json()['access_token']
headers = {'Authorization': f"Bearer {TOKEN}"}
del resp


def test1():
    client = TestClient(app)
    data = {"username": "testuser1", "password": "secret"}
    response = client.post(f"/{version}/auth/login", data)
    assert 'access_token' in response.json()
    assert response.json()['token_type'] == 'bearer'


def test2():
    client = TestClient(app)
    response = client.get(f"/{version}/bestworst/random/5", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 5


def test3():
    client = TestClient(app)
    response = client.get(f"/{version}/bestworst/random/4/10", headers=headers)
    assert response.status_code == 200
    assert len(response.json()[0]["examples"]) == 4
    assert len(response.json()) == 10
