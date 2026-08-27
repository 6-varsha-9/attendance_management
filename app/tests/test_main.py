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


def register_user(client, username, password, role):
    response = client.post(
        "/auth/register",
        json={
            "username": username,
            "password": password,
            "role": role,
        },
    )

    assert response.status_code == 200

    return get_token(client, username, password)


def create_student(client, token):
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

    return response.json()["id"]


# -------------------------
# Authentication Tests
# -------------------------

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
    register_user(
        client,
        "teacher1",
        "teacher123",
        "TEACHER",
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
    token = register_user(
        client,
        "teacher1",
        "teacher123",
        "TEACHER",
    )

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
    token = register_user(
        client,
        "admin",
        "admin123",
        "ADMIN",
    )

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
    token = register_user(
        client,
        "teacher1",
        "teacher123",
        "TEACHER",
    )

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
    token = register_user(
        client,
        "principal",
        "principal123",
        "PRINCIPAL",
    )

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
    token = register_user(
        client,
        "admin",
        "admin123",
        "ADMIN",
    )

    create_student(client, token)

    response = client.get(
        "/students/",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_teacher_can_view_students(client):
    token = register_user(
        client,
        "teacher1",
        "teacher123",
        "TEACHER",
    )

    response = client.get(
        "/students/",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200


def test_principal_can_view_students(client):
    token = register_user(
        client,
        "principal",
        "principal123",
        "PRINCIPAL",
    )

    response = client.get(
        "/students/",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200


def test_admin_can_update_student(client):
    token = register_user(
        client,
        "admin",
        "admin123",
        "ADMIN",
    )

    student_id = create_student(client, token)

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
    admin_token = register_user(
        client,
        "admin",
        "admin123",
        "ADMIN",
    )

    student_id = create_student(client, admin_token)

    teacher_token = register_user(
        client,
        "teacher1",
        "teacher123",
        "TEACHER",
    )

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
    admin_token = register_user(
        client,
        "admin",
        "admin123",
        "ADMIN",
    )

    student_id = create_student(client, admin_token)

    principal_token = register_user(
        client,
        "principal",
        "principal123",
        "PRINCIPAL",
    )

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
    token = register_user(
        client,
        "admin",
        "admin123",
        "ADMIN",
    )

    student_id = create_student(client, token)

    response = client.delete(
        f"/students/{student_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Student deleted"


def test_teacher_cannot_delete_student(client):
    token = register_user(
        client,
        "teacher1",
        "teacher123",
        "TEACHER",
    )

    response = client.delete(
        "/students/1",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403


def test_principal_cannot_delete_student(client):
    token = register_user(
        client,
        "principal",
        "principal123",
        "PRINCIPAL",
    )

    response = client.delete(
        "/students/1",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403


def test_student_not_found(client):
    token = register_user(
        client,
        "admin",
        "admin123",
        "ADMIN",
    )

    response = client.get(
        "/students/999",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404


# -------------------------
# Attendance Management Tests
# -------------------------

def test_teacher_can_mark_attendance(client):
    teacher_token = register_user(
        client,
        "teacher1",
        "teacher123",
        "TEACHER",
    )

    admin_token = register_user(
        client,
        "admin",
        "admin123",
        "ADMIN",
    )

    student_id = create_student(client, admin_token)

    response = client.post(
        "/attendance/",
        json={
            "student_id": student_id,
            "date": "2026-08-27",
            "status": "PRESENT",
        },
        headers={
            "Authorization": f"Bearer {teacher_token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["student_id"] == student_id
    assert response.json()["status"] == "PRESENT"


def test_admin_can_mark_attendance(client):
    admin_token = register_user(
        client,
        "admin",
        "admin123",
        "ADMIN",
    )

    student_id = create_student(client, admin_token)

    response = client.post(
        "/attendance/",
        json={
            "student_id": student_id,
            "date": "2026-08-27",
            "status": "ABSENT",
        },
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ABSENT"


def test_principal_cannot_mark_attendance(client):
    admin_token = register_user(
        client,
        "admin",
        "admin123",
        "ADMIN",
    )

    student_id = create_student(client, admin_token)

    principal_token = register_user(
        client,
        "principal",
        "principal123",
        "PRINCIPAL",
    )

    response = client.post(
        "/attendance/",
        json={
            "student_id": student_id,
            "date": "2026-08-27",
            "status": "PRESENT",
        },
        headers={
            "Authorization": f"Bearer {principal_token}",
        },
    )

    assert response.status_code == 403


def test_teacher_can_view_attendance(client):
    teacher_token = register_user(
        client,
        "teacher1",
        "teacher123",
        "TEACHER",
    )

    response = client.get(
        "/attendance/",
        headers={
            "Authorization": f"Bearer {teacher_token}",
        },
    )

    assert response.status_code == 200


def test_principal_can_view_attendance(client):
    principal_token = register_user(
        client,
        "principal",
        "principal123",
        "PRINCIPAL",
    )

    response = client.get(
        "/attendance/",
        headers={
            "Authorization": f"Bearer {principal_token}",
        },
    )

    assert response.status_code == 200


def test_admin_can_view_attendance(client):
    admin_token = register_user(
        client,
        "admin",
        "admin123",
        "ADMIN",
    )

    response = client.get(
        "/attendance/",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert response.status_code == 200


def test_teacher_can_update_attendance(client):
    teacher_token = register_user(
        client,
        "teacher1",
        "teacher123",
        "TEACHER",
    )

    admin_token = register_user(
        client,
        "admin",
        "admin123",
        "ADMIN",
    )

    student_id = create_student(client, admin_token)

    create_response = client.post(
        "/attendance/",
        json={
            "student_id": student_id,
            "date": "2026-08-27",
            "status": "ABSENT",
        },
        headers={
            "Authorization": f"Bearer {teacher_token}",
        },
    )

    record_id = create_response.json()["id"]

    response = client.put(
        f"/attendance/{record_id}",
        json={
            "student_id": student_id,
            "date": "2026-08-27",
            "status": "PRESENT",
        },
        headers={
            "Authorization": f"Bearer {teacher_token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "PRESENT"


def test_admin_can_update_attendance(client):
    admin_token = register_user(
        client,
        "admin",
        "admin123",
        "ADMIN",
    )

    student_id = create_student(client, admin_token)

    create_response = client.post(
        "/attendance/",
        json={
            "student_id": student_id,
            "date": "2026-08-27",
            "status": "ABSENT",
        },
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    record_id = create_response.json()["id"]

    response = client.put(
        f"/attendance/{record_id}",
        json={
            "student_id": student_id,
            "date": "2026-08-27",
            "status": "PRESENT",
        },
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "PRESENT"


def test_principal_cannot_update_attendance(client):
    admin_token = register_user(
        client,
        "admin",
        "admin123",
        "ADMIN",
    )

    student_id = create_student(client, admin_token)

    create_response = client.post(
        "/attendance/",
        json={
            "student_id": student_id,
            "date": "2026-08-27",
            "status": "ABSENT",
        },
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    record_id = create_response.json()["id"]

    principal_token = register_user(
        client,
        "principal",
        "principal123",
        "PRINCIPAL",
    )

    response = client.put(
        f"/attendance/{record_id}",
        json={
            "student_id": student_id,
            "date": "2026-08-27",
            "status": "PRESENT",
        },
        headers={
            "Authorization": f"Bearer {principal_token}",
        },
    )

    assert response.status_code == 403


def test_duplicate_attendance_not_allowed(client):
    teacher_token = register_user(
        client,
        "teacher1",
        "teacher123",
        "TEACHER",
    )

    admin_token = register_user(
        client,
        "admin",
        "admin123",
        "ADMIN",
    )

    student_id = create_student(client, admin_token)

    attendance_data = {
        "student_id": student_id,
        "date": "2026-08-27",
        "status": "PRESENT",
    }

    first_response = client.post(
        "/attendance/",
        json=attendance_data,
        headers={
            "Authorization": f"Bearer {teacher_token}",
        },
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/attendance/",
        json=attendance_data,
        headers={
            "Authorization": f"Bearer {teacher_token}",
        },
    )

    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Attendance already marked for this date"


def test_attendance_record_not_found(client):
    teacher_token = register_user(
        client,
        "teacher1",
        "teacher123",
        "TEACHER",
    )

    admin_token = register_user(
        client,
        "admin",
        "admin123",
        "ADMIN",
    )

    student_id = create_student(client, admin_token)

    response = client.put(
        "/attendance/999",
        json={
            "student_id": student_id,
            "date": "2026-08-27",
            "status": "PRESENT",
        },
        headers={
            "Authorization": f"Bearer {teacher_token}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Record not found"