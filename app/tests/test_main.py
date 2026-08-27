from app.models import User, RoleEnum


# =========================================================
# Helper Functions
# =========================================================

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


def create_student(
    client,
    token,
    roll_number="TEST001",
    email="test@example.com",
):
    response = client.post(
        "/students/",
        json={
            "name": "Test Student",
            "roll_number": roll_number,
            "email": email,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    return response.json()["id"]


def create_attendance(client, token, student_id, date, status):
    response = client.post(
        "/attendance/",
        json={
            "student_id": student_id,
            "date": date,
            "status": status,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    return response.json()["id"]


def create_report_data(client):
    admin_token = register_user(
        client,
        "admin",
        "admin123",
        "ADMIN",
    )

    teacher_token = register_user(
        client,
        "teacher1",
        "teacher123",
        "TEACHER",
    )

    student_id = create_student(
        client,
        admin_token,
        "REPORT001",
        "report@example.com",
    )

    create_attendance(
        client,
        teacher_token,
        student_id,
        "2026-08-25",
        "PRESENT",
    )

    create_attendance(
        client,
        teacher_token,
        student_id,
        "2026-08-26",
        "PRESENT",
    )

    create_attendance(
        client,
        teacher_token,
        student_id,
        "2026-08-27",
        "ABSENT",
    )

    return admin_token, teacher_token, student_id


# =========================================================
# Authentication Tests
# =========================================================

def test_home(client):
    response = client.get("/")

    assert response.status_code == 200
    assert (
        response.json()["message"]
        == "Attendance Management System API is running"
    )


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


# =========================================================
# User Management Tests
# =========================================================

def test_admin_can_view_users(client):
    register_user(
        client,
        "admin",
        "admin123",
        "ADMIN",
    )

    register_user(
        client,
        "teacher1",
        "teacher123",
        "TEACHER",
    )

    admin_token = get_token(
        client,
        "admin",
        "admin123",
    )

    response = client.get(
        "/users/",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert response.status_code == 200
    assert len(response.json()) >= 2


def test_teacher_cannot_view_users(client):
    register_user(
        client,
        "teacher1",
        "teacher123",
        "TEACHER",
    )

    teacher_token = get_token(
        client,
        "teacher1",
        "teacher123",
    )

    response = client.get(
        "/users/",
        headers={
            "Authorization": f"Bearer {teacher_token}",
        },
    )

    assert response.status_code == 403


def test_principal_cannot_view_users(client):
    register_user(
        client,
        "principal",
        "principal123",
        "PRINCIPAL",
    )

    principal_token = get_token(
        client,
        "principal",
        "principal123",
    )

    response = client.get(
        "/users/",
        headers={
            "Authorization": f"Bearer {principal_token}",
        },
    )

    assert response.status_code == 403


def test_admin_can_create_user(client):
    register_user(
        client,
        "admin",
        "admin123",
        "ADMIN",
    )

    admin_token = get_token(
        client,
        "admin",
        "admin123",
    )

    response = client.post(
        "/users/",
        json={
            "username": "newteacher",
            "password": "teacher123",
            "role": "TEACHER",
        },
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "User created successfully"
    assert response.json()["username"] == "newteacher"
    assert response.json()["role"] == "TEACHER"


def test_teacher_cannot_create_user(client):
    register_user(
        client,
        "teacher1",
        "teacher123",
        "TEACHER",
    )

    teacher_token = get_token(
        client,
        "teacher1",
        "teacher123",
    )

    response = client.post(
        "/users/",
        json={
            "username": "newteacher",
            "password": "teacher123",
            "role": "TEACHER",
        },
        headers={
            "Authorization": f"Bearer {teacher_token}",
        },
    )

    assert response.status_code == 403


def test_principal_cannot_create_user(client):
    register_user(
        client,
        "principal",
        "principal123",
        "PRINCIPAL",
    )

    principal_token = get_token(
        client,
        "principal",
        "principal123",
    )

    response = client.post(
        "/users/",
        json={
            "username": "newteacher",
            "password": "teacher123",
            "role": "TEACHER",
        },
        headers={
            "Authorization": f"Bearer {principal_token}",
        },
    )

    assert response.status_code == 403


def test_admin_cannot_create_duplicate_user(client):
    register_user(
        client,
        "admin",
        "admin123",
        "ADMIN",
    )

    register_user(
        client,
        "teacher1",
        "teacher123",
        "TEACHER",
    )

    admin_token = get_token(
        client,
        "admin",
        "admin123",
    )

    response = client.post(
        "/users/",
        json={
            "username": "teacher1",
            "password": "another123",
            "role": "TEACHER",
        },
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Username already exists"


def test_admin_can_delete_user(client):
    register_user(
        client,
        "admin",
        "admin123",
        "ADMIN",
    )

    register_user(
        client,
        "teacher1",
        "teacher123",
        "TEACHER",
    )

    admin_token = get_token(
        client,
        "admin",
        "admin123",
    )

    users_response = client.get(
        "/users/",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    users = users_response.json()

    teacher = next(
        user
        for user in users
        if user["username"] == "teacher1"
    )

    response = client.delete(
        f"/users/{teacher['id']}",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == "User deleted successfully"


def test_teacher_cannot_delete_user(client):
    register_user(
        client,
        "teacher1",
        "teacher123",
        "TEACHER",
    )

    register_user(
        client,
        "teacher2",
        "teacher456",
        "TEACHER",
    )

    teacher_token = get_token(
        client,
        "teacher1",
        "teacher123",
    )

    users_response = client.get(
        "/users/",
        headers={
            "Authorization": f"Bearer {teacher_token}",
        },
    )

    # Teacher should not even be able to access the user list.
    assert users_response.status_code == 403


def test_admin_cannot_delete_self(client):
    register_user(
        client,
        "admin",
        "admin123",
        "ADMIN",
    )

    admin_token = get_token(
        client,
        "admin",
        "admin123",
    )

    users_response = client.get(
        "/users/",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    admin_user = next(
        user
        for user in users_response.json()
        if user["username"] == "admin"
    )

    response = client.delete(
        f"/users/{admin_user['id']}",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Admin cannot delete their own account"
    )


def test_user_not_found(client):
    register_user(
        client,
        "admin",
        "admin123",
        "ADMIN",
    )

    admin_token = get_token(
        client,
        "admin",
        "admin123",
    )

    response = client.delete(
        "/users/99999",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


# =========================================================
# Student Management Tests
# =========================================================

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


# =========================================================
# Attendance Management Tests
# =========================================================

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
    assert (
        second_response.json()["detail"]
        == "Attendance already marked for this date"
    )


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


# =========================================================
# Attendance Report Tests
# =========================================================

def test_teacher_can_generate_report(client):
    _, teacher_token, student_id = create_report_data(client)

    response = client.post(
        f"/reports/generate/{student_id}",
        headers={
            "Authorization": f"Bearer {teacher_token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["student_id"] == student_id


def test_admin_can_generate_report(client):
    admin_token, _, student_id = create_report_data(client)

    response = client.post(
        f"/reports/generate/{student_id}",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["student_id"] == student_id


def test_principal_cannot_generate_report(client):
    admin_token = register_user(
        client,
        "admin",
        "admin123",
        "ADMIN",
    )

    teacher_token = register_user(
        client,
        "teacher1",
        "teacher123",
        "TEACHER",
    )

    principal_token = register_user(
        client,
        "principal",
        "principal123",
        "PRINCIPAL",
    )

    student_id = create_student(
        client,
        admin_token,
        "REPORT001",
        "report@example.com",
    )

    create_attendance(
        client,
        teacher_token,
        student_id,
        "2026-08-27",
        "PRESENT",
    )

    response = client.post(
        f"/reports/generate/{student_id}",
        headers={
            "Authorization": f"Bearer {principal_token}",
        },
    )

    assert response.status_code == 403


def test_report_calculates_attendance_correctly(client):
    admin_token, teacher_token, student_id = create_report_data(client)

    response = client.post(
        f"/reports/generate/{student_id}",
        headers={
            "Authorization": f"Bearer {teacher_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_classes"] == 3
    assert data["present"] == 2
    assert data["absent"] == 1
    assert data["percentage"] == 66.67
    assert data["status"] == "PENDING"


def test_report_without_attendance_returns_404(client):
    admin_token = register_user(
        client,
        "admin",
        "admin123",
        "ADMIN",
    )

    student_id = create_student(
        client,
        admin_token,
        "EMPTY001",
        "empty@example.com",
    )

    response = client.post(
        f"/reports/generate/{student_id}",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "No attendance records found"


def test_admin_can_view_reports(client):
    admin_token, _, student_id = create_report_data(client)

    client.post(
        f"/reports/generate/{student_id}",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    response = client.get(
        "/reports/",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_principal_can_view_reports(client):
    admin_token, teacher_token, student_id = create_report_data(client)

    client.post(
        f"/reports/generate/{student_id}",
        headers={
            "Authorization": f"Bearer {teacher_token}",
        },
    )

    principal_token = register_user(
        client,
        "principal",
        "principal123",
        "PRINCIPAL",
    )

    response = client.get(
        "/reports/",
        headers={
            "Authorization": f"Bearer {principal_token}",
        },
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_teacher_cannot_view_reports(client):
    teacher_token = register_user(
        client,
        "teacher1",
        "teacher123",
        "TEACHER",
    )

    response = client.get(
        "/reports/",
        headers={
            "Authorization": f"Bearer {teacher_token}",
        },
    )

    assert response.status_code == 403


def test_principal_can_approve_report(client):
    admin_token, teacher_token, student_id = create_report_data(client)

    create_response = client.post(
        f"/reports/generate/{student_id}",
        headers={
            "Authorization": f"Bearer {teacher_token}",
        },
    )

    report_id = create_response.json()["id"]

    principal_token = register_user(
        client,
        "principal",
        "principal123",
        "PRINCIPAL",
    )

    response = client.put(
        f"/reports/{report_id}/approve",
        headers={
            "Authorization": f"Bearer {principal_token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"
    assert response.json()["approved_by"] is not None


def test_admin_cannot_approve_report(client):
    admin_token, teacher_token, student_id = create_report_data(client)

    create_response = client.post(
        f"/reports/generate/{student_id}",
        headers={
            "Authorization": f"Bearer {teacher_token}",
        },
    )

    report_id = create_response.json()["id"]

    response = client.put(
        f"/reports/{report_id}/approve",
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert response.status_code == 403


def test_teacher_cannot_approve_report(client):
    _, teacher_token, student_id = create_report_data(client)

    create_response = client.post(
        f"/reports/generate/{student_id}",
        headers={
            "Authorization": f"Bearer {teacher_token}",
        },
    )

    report_id = create_response.json()["id"]

    response = client.put(
        f"/reports/{report_id}/approve",
        headers={
            "Authorization": f"Bearer {teacher_token}",
        },
    )

    assert response.status_code == 403


def test_principal_can_reject_report(client):
    admin_token, teacher_token, student_id = create_report_data(client)

    create_response = client.post(
        f"/reports/generate/{student_id}",
        headers={
            "Authorization": f"Bearer {teacher_token}",
        },
    )

    report_id = create_response.json()["id"]

    principal_token = register_user(
        client,
        "principal",
        "principal123",
        "PRINCIPAL",
    )

    response = client.put(
        f"/reports/{report_id}/reject",
        json={
            "remarks": "Attendance percentage needs verification",
        },
        headers={
            "Authorization": f"Bearer {principal_token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "REJECTED"
    assert (
        response.json()["remarks"]
        == "Attendance percentage needs verification"
    )
    assert response.json()["approved_by"] is not None


def test_admin_cannot_reject_report(client):
    admin_token, teacher_token, student_id = create_report_data(client)

    create_response = client.post(
        f"/reports/generate/{student_id}",
        headers={
            "Authorization": f"Bearer {teacher_token}",
        },
    )

    report_id = create_response.json()["id"]

    response = client.put(
        f"/reports/{report_id}/reject",
        json={
            "remarks": "Test rejection",
        },
        headers={
            "Authorization": f"Bearer {admin_token}",
        },
    )

    assert response.status_code == 403


def test_teacher_cannot_reject_report(client):
    _, teacher_token, student_id = create_report_data(client)

    create_response = client.post(
        f"/reports/generate/{student_id}",
        headers={
            "Authorization": f"Bearer {teacher_token}",
        },
    )

    report_id = create_response.json()["id"]

    response = client.put(
        f"/reports/{report_id}/reject",
        json={
            "remarks": "Test rejection",
        },
        headers={
            "Authorization": f"Bearer {teacher_token}",
        },
    )

    assert response.status_code == 403


def test_report_not_found(client):
    principal_token = register_user(
        client,
        "principal",
        "principal123",
        "PRINCIPAL",
    )

    response = client.put(
        "/reports/999/approve",
        headers={
            "Authorization": f"Bearer {principal_token}",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Report not found"