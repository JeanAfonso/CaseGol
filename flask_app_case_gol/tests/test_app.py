import pytest
from flask_app_case_gol.app import app, db, Voo, User, hash
from flask_login import current_user


@pytest.fixture
def client():
    """Configura um cliente de teste para a aplicação Flask."""
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///:memory:"  # Banco de dados em memória para testes
    )
    app.config["SECRET_KEY"] = "test_secret_key"

    with app.test_client() as client:
        with app.app_context():
            db.create_all()  # Cria todas as tabelas no banco de dados de teste
            yield client
            db.session.remove()
            db.drop_all()


@pytest.fixture
def new_user():
    """Cria um usuário de teste."""
    return User(username="test_user", password=hash("password"))


@pytest.fixture
def init_database(client, new_user):
    """Popula o banco de dados de teste antes de cada teste."""
    db.session.add(new_user)
    db.session.commit()

    # Adiciona alguns voos de exemplo
    voo1 = Voo(ano=2024, mes=5, mercado="GRU-SSA", rpk=5000.0)
    voo2 = Voo(ano=2024, mes=6, mercado="GRU-SSA", rpk=6000.0)
    db.session.add(voo1)
    db.session.add(voo2)
    db.session.commit()

    yield db
    db.drop_all()


def test_register(client):
    """Teste para o registro de um novo usuário."""
    response = client.post(
        "/register",
        data=dict(username="new_user", password="new_password"),
        follow_redirects=True,
    )

    assert response.status_code == 200
    # assert b'Bem-vindo' in response.data
    assert User.query.filter_by(username="new_user").first() is not None


def test_login(client, init_database):
    """Teste para o login de um usuário existente."""
    response = client.post(
        "/login",
        data=dict(username="test_user", password="password"),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert current_user.is_authenticated


def test_logout(client, init_database):
    """Teste para o logout de um usuário."""
    client.post(
        "/login",
        data=dict(username="test_user", password="password"),
        follow_redirects=True,
    )

    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert not current_user.is_authenticated


def test_dashboard_access_without_login(client):
    """Teste para verificar acesso ao dashboard sem login."""
    response = client.get("/")
    assert response.status_code == 302  # Redirecionado para a página de login
    assert b"Redirecting" in response.data


def test_dashboard_access_with_login(client, init_database):
    """Teste para verificar acesso ao dashboard com login."""
    client.post(
        "/login",
        data=dict(username="test_user", password="password"),
        follow_redirects=True,
    )

    response = client.get("/")
    assert response.status_code == 200
    assert (
        b"Mercado" in response.data
    )  # Verifica se o template do dashboard é renderizado corretamente


def test_filtro_voos(client, init_database):
    """Teste para a funcionalidade de filtragem de voos."""
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
    assert (
        b"2024" in response.data
    )  # Verifica se o ano de 2024 está presente nos resultados
    assert (
        b"GRU-SSA" in response.data
    )  # Verifica se o mercado correto está presente nos resultados
