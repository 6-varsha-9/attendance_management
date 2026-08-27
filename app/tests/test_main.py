from app.models import User, RoleEnum


def get_token(client, username, password):
    response = client.post(
        "/auth/login",
        data={
            "username": username,
            "password": password,
        },
    )

    return response.json()["access_token"]


def create_user(db, username, password, role):
    from app.auth import hash_password

    user = User(
        username=username,
        password=hash_password(password),
        role=role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def test_home(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "Attendance Management System API is running"


def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "password": "test123",
            "role": "TEACHER",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "User created"


def test_login_success(client):
    client.post(
        "/auth/register",
        json={
            "username": "teacher1",
            "password": "teacher123",
            "role": "TEACHER",
        },
    )

    response = client.post(
        "/auth/login",
        data={
            "username": "teacher1",
            "password": "teacher123",
        },
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_invalid(client):
    response = client.post(
        "/auth/login",
        data={
            "username": "x",
            "password": "y",
        },
    )

    assert response.status_code == 401


def test_protected_endpoint_with_valid_token(client):
    client.post(
        "/auth/register",
        json={
            "username": "teacher1",
            "password": "teacher123",
            "role": "TEACHER",
        },
    )

    token = get_token(client, "teacher1", "teacher123")

    response = client.get(
        "/students/",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200


def test_admin_can_create_student(client):
    client.post(
        "/auth/register",
        json={
            "username": "admin",
            "password": "admin123",
            "role": "ADMIN",
        },
    )

    token = get_token(client, "admin", "admin123")

    response = client.post(
        "/students/",
        json={
            "name": "Test Student",
            "roll_number": "TEST001",
            "email": "test@example.com",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200


def test_teacher_cannot_create_student(client):
    client.post(
        "/auth/register",
        json={
            "username": "teacher1",
            "password": "teacher123",
            "role": "TEACHER",
        },
    )

    token = get_token(client, "teacher1", "teacher123")

    response = client.post(
        "/students/",
        json={
            "name": "Test Student",
            "roll_number": "TEST001",
            "email": "test@example.com",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403