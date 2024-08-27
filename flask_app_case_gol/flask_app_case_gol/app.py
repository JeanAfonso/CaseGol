from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
import hashlib
import pandas as pd

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///voos.db"
app.config["SECRET_KEY"] = "jean123"

db = SQLAlchemy()
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


def hash(txt):
    hash_obj = hashlib.sha256(txt.encode("utf-8"))
    return hash_obj.hexdigest()


class Voo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ano = db.Column(db.Integer)
    mes = db.Column(db.Integer)
    mercado = db.Column(db.String(50))
    rpk = db.Column(db.Float)


@app.before_request
def create_and_populate_db():
    app.before_request_funcs[None].remove(create_and_populate_db)
    db.create_all()

    # Verificar se a tabela já contém dados
    if Voo.query.count() == 0:
        # Carregar os dados do CSV
        df = pd.read_csv(
            "/home/jean/CaseGol/Dados_Estatisticos.csv",
            delimiter=";",
            quotechar='"',
            skipinitialspace=True,
            skiprows=1,
        )

        # Filtrar os dados
        df_filtered = df[
            (df["EMPRESA_SIGLA"] == "GLO")
            & (df["GRUPO_DE_VOO"] == "REGULAR")
            & (df["NATUREZA"] == "DOMÉSTICA")
        ]

        # Agrupar e criar a coluna MERCADO
        df_filtered["MERCADO"] = df_filtered.apply(
            lambda row: "".join(
                sorted(
                    [
                        row["AEROPORTO_DE_ORIGEM_SIGLA"],
                        row["AEROPORTO_DE_DESTINO_SIGLA"],
                    ]
                )
            ),
            axis=1,
        )

        # Criar um novo DataFrame com as colunas necessárias
        df_final = (
            df_filtered.groupby(["ANO", "MES", "MERCADO"])["RPK"].sum().reset_index()
        )

        # Inserir os dados no banco de dados
        for _, row in df_final.iterrows():
            voo = Voo(
                ano=row["ANO"], mes=row["MES"], mercado=row["MERCADO"], rpk=row["RPK"]
            )
            db.session.add(voo)

        db.session.commit()


# Seção de login
class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True)
    password = db.Column(db.String())


@login_manager.user_loader
def load_user(id):
    user = db.session.query(User).filter_by(id=id).first()
    return user


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        new_user = User(username=username, password=hash(password))

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

        return redirect(url_for("dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = (
            db.session.query(User)
            .filter_by(username=username, password=hash(password))
            .first()
        )

        if user is None:
            flash("Usuário e/ou senha inválidos tente novamente.", "danger")
            return redirect(url_for("login"))

        login_user(user)

        return redirect(url_for("dashboard"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def dashboard():
    ano_min = db.session.query(db.func.min(Voo.ano)).scalar()
    ano_max = db.session.query(db.func.max(Voo.ano)).scalar()

    mercados = Voo.query.with_entities(Voo.mercado).distinct().all()
    return render_template(
        "dashboard.html", mercados=mercados, ano_min=ano_min, ano_max=ano_max
    )


@app.route("/filtro", methods=["POST"])
@login_required
def filtro():
    mercado = request.form.get("mercado")
    ano_inicio = int(request.form.get("ano_inicio"))
    mes_inicio = int(request.form.get("mes_inicio"))
    ano_fim = int(request.form.get("ano_fim"))
    mes_fim = int(request.form.get("mes_fim"))

    voos = Voo.query.filter(
        Voo.mercado == mercado,
        Voo.ano >= ano_inicio,
        Voo.mes >= mes_inicio,
        Voo.ano <= ano_fim,
        Voo.mes <= mes_fim,
    ).all()

    return render_template("resultados.html", voos=voos)


if __name__ == "__main__":
    db.create_all()
