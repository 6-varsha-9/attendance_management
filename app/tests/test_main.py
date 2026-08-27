def test_home(client):
    res = client.get("/")
    assert res.status_code == 200

def test_login_invalid(client):
    res = client.post("/auth/login", data={"username": "x", "password": "y"})
    assert res.status_code == 401