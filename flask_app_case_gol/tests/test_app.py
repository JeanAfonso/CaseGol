import pytest
from flask_login import current_user

from flask_app_case_gol.app import Flight, User, app, db, hash


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test_flights.db"

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture
def new_user():
    user = User(username="test_user", password=hash("password"))
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def init_database(client, new_user):
    db.create_all()

    db.session.add(new_user)
    db.session.commit()

    flight1 = Flight(ano=2024, mes=5, mercado="GRU-SSA", rpk=5000.0)
    flight2 = Flight(ano=2024, mes=6, mercado="GRU-SSA", rpk=6000.0)
    db.session.add(flight1)
    db.session.add(flight2)
    db.session.commit()

    yield db
    db.drop_all()


def test_register(client):
    with app.app_context():
        response = client.post(
            "/register", data={"username": "test_user", "password": "test_pass"}
        )
        assert response.status_code == 302
        user = User.query.filter_by(username="test_user").first()
        assert user is not None


def test_login(client, init_database, new_user):
    response = client.post(
        "/login",
        data=dict(username="test_user", password="password"),
        follow_redirects=True,
    )

    assert response.status_code == 200

    with client.session_transaction() as session:
        assert "_user_id" in session
        assert int(session["_user_id"]) == new_user.id

    assert response.request.path == "/"


def test_logout(client, init_database):
    with app.test_request_context():
        with client:
            existing_user = User.query.filter_by(username="test_user").first()
            if not existing_user:
                client.post(
                    "/register",
                    data=dict(username="test_user", password="password"),
                    follow_redirects=True,
                )

            response = client.post(
                "/login",
                data=dict(username="test_user", password="password"),
                follow_redirects=True,
            )

            assert current_user.is_authenticated

            response = client.get("/logout", follow_redirects=True)
            assert response.status_code == 200
            assert not current_user.is_authenticated


def test_dashboard_access_without_login(client):
    with app.app_context():
        response = client.get("/")
        assert response.status_code == 302
        assert b"Redirecting" in response.data


def test_dashboard_access_with_login(client, init_database):
    with app.app_context():
        client.post(
            "/login",
            data=dict(username="test_user", password="password"),
            follow_redirects=True,
        )

        response = client.get("/")
        assert response.status_code == 200
        assert b"Mercado" in response.data


def test_filter_flights(client, init_database):
    with app.app_context():
        client.post(
            "/login",
            data=dict(username="test_user", password="password"),
            follow_redirects=True,
        )

        response = client.post(
            "/filter",
            data=dict(
                market="GRU-SSA",
                start_year=2024,
                start_month=5,
                end_year=2024,
                end_month=6,
            ),
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"2024" in response.data
        assert b"GRU-SSA" in response.data
