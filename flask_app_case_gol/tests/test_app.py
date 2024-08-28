import pytest
from flask_app_case_gol.app import app, db, Voo, User, hash
from flask_login import current_user


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SECRET_KEY"] = "test_secret_key"

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()


@pytest.fixture
def new_user():
    return User(username="test_user", password=hash("password"))


@pytest.fixture
def init_database(client, new_user):
    db.session.add(new_user)
    db.session.commit()

    voo1 = Voo(ano=2024, mes=5, mercado="GRU-SSA", rpk=5000.0)
    voo2 = Voo(ano=2024, mes=6, mercado="GRU-SSA", rpk=6000.0)
    db.session.add(voo1)
    db.session.add(voo2)
    db.session.commit()

    yield db
    db.drop_all()


def test_register(client):
    response = client.post(
        "/register",
        data=dict(username="new_user", password="new_password"),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Bem-vindo" in response.data
    assert User.query.filter_by(username="new_user").first() is not None


def test_login(client, init_database):
    response = client.post(
        "/login",
        data=dict(username="test_user", password="password"),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert current_user.is_authenticated


def test_logout(client, init_database):
    client.post(
        "/login",
        data=dict(username="test_user", password="password"),
        follow_redirects=True,
    )

    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert not current_user.is_authenticated


def test_dashboard_access_without_login(client):
    response = client.get("/")
    assert response.status_code == 302
    assert b"Redirecting" in response.data


def test_dashboard_access_with_login(client, init_database):
    client.post(
        "/login",
        data=dict(username="test_user", password="password"),
        follow_redirects=True,
    )

    response = client.get("/")
    assert response.status_code == 200
    assert b"Mercado" in response.data


def test_filtro_voos(client, init_database):
    client.post(
        "/login",
        data=dict(username="test_user", password="password"),
        follow_redirects=True,
    )

    response = client.post(
        "/filtro",
        data=dict(
            mercado="GRU-SSA", ano_inicio=2024, mes_inicio=5, ano_fim=2024, mes_fim=6
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"2024" in response.data
    assert b"GRU-SSA" in response.data
