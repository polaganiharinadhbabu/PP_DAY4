from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_status():
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert "X-Process-Time" in response.headers


def test_list_products():
    response = client.get("/api/v1/products/")
    assert response.status_code == 200


def test_get_product():
    response = client.get("/api/v1/products/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_user_requires_authentication():
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_admin_rejects_viewer():
    response = client.get(
        "/api/v1/users/admin",
        headers={
            "Authorization": "Bearer demo-viewer-token"
        }
    )
    assert response.status_code == 403


def test_admin_accepts_admin():
    response = client.get(
        "/api/v1/users/admin",
        headers={
            "Authorization": "Bearer demo-admin-token"
        }
    )
    assert response.status_code == 200


def test_order():
    response = client.post("/orders")
    assert response.status_code == 200
    assert response.json()["message"] == "Order accepted"
