from starlette.testclient import TestClient
from app.main import app, srvurl


def test1():
    client = TestClient(app)
    response = client.get(f"{srvurl}/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}


def test2():
    client = TestClient(app)
    response = client.get(f"{srvurl}/items/")
    assert response.status_code == 200
    assert response.json() == {"item_id": None}


def test3():
    client = TestClient(app)
    response = client.get(f"{srvurl}/items/42")
    assert response.status_code == 200
    assert response.json() == {"item_id": 42, "q": None}


def test4():
    client = TestClient(app)
    response = client.get(f"{srvurl}/items/42?q=23")
    assert response.status_code == 200
    assert response.json() == {"item_id": 42, "q": "23"}

# FURTHER INFORMATION
# https://fastapi.tiangolo.com/tutorial/testing/
