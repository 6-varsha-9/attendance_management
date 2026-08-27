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


# -------------------------
# Student Management Tests
# -------------------------

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
    assert response.json()["name"] == "Test Student"
    assert response.json()["roll_number"] == "TEST001"


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


def test_principal_cannot_create_student(client):
    client.post(
        "/auth/register",
        json={
            "username": "principal",
            "password": "principal123",
            "role": "PRINCIPAL",
        },
    )

    token = get_token(client, "principal", "principal123")

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


def test_admin_can_view_students(client):
    client.post(
        "/auth/register",
        json={
            "username": "admin",
            "password": "admin123",
            "role": "ADMIN",
        },
    )

    token = get_token(client, "admin", "admin123")

    client.post(
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

    response = client.get(
        "/students/",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_teacher_can_view_students(client):
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


def test_principal_can_view_students(client):
    client.post(
        "/auth/register",
        json={
            "username": "principal",
            "password": "principal123",
            "role": "PRINCIPAL",
        },
    )

    token = get_token(client, "principal", "principal123")

    response = client.get(
        "/students/",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200


def test_admin_can_update_student(client):
    client.post(
        "/auth/register",
        json={
            "username": "admin",
            "password": "admin123",
            "role": "ADMIN",
        },
    )

    token = get_token(client, "admin", "admin123")

    create_response = client.post(
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

    student_id = create_response.json()["id"]

    response = client.put(
        f"/students/{student_id}",
        json={
            "name": "Updated Student",
            "roll_number": "TEST001",
            "email": "updated@example.com",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Student"
    assert response.json()["email"] == "updated@example.com"


def test_teacher_cannot_update_student(client):
    client.post(
        "/auth/register",
        json={
            "username": "admin",
            "password": "admin123",
            "role": "ADMIN",
        },
    )

    admin_token = get_token(client, "admin", "admin123")

    create_response = client.post(
        "/students/",
        json={
            "name": "Test Student",
            "roll_number": "TEST001",
            "email": "test@example.com",
        },
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    student_id = create_response.json()["id"]

    client.post(
        "/auth/register",
        json={
            "username": "teacher1",
            "password": "teacher123",
            "role": "TEACHER",
        },
    )

    teacher_token = get_token(client, "teacher1", "teacher123")

    response = client.put(
        f"/students/{student_id}",
        json={
            "name": "Updated Student",
            "roll_number": "TEST001",
            "email": "updated@example.com",
        },
        headers={
            "Authorization": f"Bearer {teacher_token}",
        },
    )

    assert response.status_code == 403


def test_principal_cannot_update_student(client):
    client.post(
        "/auth/register",
        json={
            "username": "admin",
            "password": "admin123",
            "role": "ADMIN",
        },
    )

    admin_token = get_token(client, "admin", "admin123")

    create_response = client.post(
        "/students/",
        json={
            "name": "Test Student",
            "roll_number": "TEST001",
            "email": "test@example.com",
        },
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    student_id = create_response.json()["id"]

    client.post(
        "/auth/register",
        json={
            "username": "principal",
            "password": "principal123",
            "role": "PRINCIPAL",
        },
    )

    principal_token = get_token(client, "principal", "principal123")

    response = client.put(
        f"/students/{student_id}",
        json={
            "name": "Updated Student",
            "roll_number": "TEST001",
            "email": "updated@example.com",
        },
        headers={
            "Authorization": f"Bearer {principal_token}",
        },
    )

    assert response.status_code == 403


def test_admin_can_delete_student(client):
    client.post(
        "/auth/register",
        json={
            "username": "admin",
            "password": "admin123",
            "role": "ADMIN",
        },
    )

    token = get_token(client, "admin", "admin123")

    create_response = client.post(
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

    student_id = create_response.json()["id"]

    response = client.delete(
        f"/students/{student_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Student deleted"


def test_teacher_cannot_delete_student(client):
    client.post(
        "/auth/register",
        json={
            "username": "teacher1",
            "password": "teacher123",
            "role": "TEACHER",
        },
    )

    token = get_token(client, "teacher1", "teacher123")

    response = client.delete(
        "/students/1",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403


def test_principal_cannot_delete_student(client):
    client.post(
        "/auth/register",
        json={
            "username": "principal",
            "password": "principal123",
            "role": "PRINCIPAL",
        },
    )

    token = get_token(client, "principal", "principal123")

    response = client.delete(
        "/students/1",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403


def test_student_not_found(client):
    client.post(
        "/auth/register",
        json={
            "username": "admin",
            "password": "admin123",
            "role": "ADMIN",
        },
    )

    token = get_token(client, "admin", "admin123")

    response = client.get(
        "/students/999",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404