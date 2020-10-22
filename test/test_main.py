from starlette.testclient import TestClient
from app.main import app, version


def test1():
    client = TestClient(app)
    response = client.get(f"/{version}/bestworst/random/5")
    assert response.status_code == 200
    assert len(response.json()) == 5


def test2():
    client = TestClient(app)
    response = client.get(f"/{version}/bestworst/random/4/10")
    assert response.status_code == 200
    assert len(response.json()[0]["examples"]) == 4
    assert len(response.json()) == 10


# FURTHER INFORMATION
# https://fastapi.tiangolo.com/tutorial/testing/
