import hashlib
import os

import pandas as pd
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import (LoginManager, UserMixin, current_user, login_required,
                         login_user, logout_user)
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

if os.getenv("FLASK_ENV") == "testing":
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test_flights.db"
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///flights.db"

app.config["SECRET_KEY"] = "jean123"

db = SQLAlchemy()
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


def hash(txt):
    hash_obj = hashlib.sha256(txt.encode("utf-8"))
    return hash_obj.hexdigest()


class Flight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ano = db.Column(db.Integer)
    mes = db.Column(db.Integer)
    mercado = db.Column(db.String(50))
    rpk = db.Column(db.Float)


''' Esse decorator faz com que a função abaixo execute antes de cada solicitação HTTP, 
tive que usa-la no lugar do @app.before_first_request pois foi deprecada, 
e ai precisei criar na linha 44 para remover a função e não excuta-la mais de uma vez durante a primeira solicitação.'''
@app.before_request
def create_and_populate_db():
    app.before_request_funcs[None].remove(create_and_populate_db)
    db.create_all()
   
    ''' Legenda: df se refere a uma estrutura de dados chamada DataFrame, 
     algo parecido com uma Matriz, nas pesquisas de como fazer me deparei com esse nome então achei valido nomear como df '''
    if Flight.query.count() == 0:
        df = pd.read_csv(
            "data/Dados_Estatisticos.csv",
            delimiter=";",
            quotechar='"',
            skipinitialspace=True,
            skiprows=1,
        )

        df_filtered = df[
            (df["EMPRESA_SIGLA"] == "GLO")
            & (df["GRUPO_DE_VOO"] == "REGULAR")
            & (df["NATUREZA"] == "DOMÉSTICA")
        ].copy()

        
        ''' Aqui na linha 65 a 71 é onde coloco em ordem alfabetica as siglas que vão para a tabela
        no campo mercado e onde posteriomente vai aparecer na pesquisa de mercado para puxar o RPK '''
        df_filtered.loc[:, "MERCADO"] = df_filtered.apply(
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

        
        # Aqui ele cria outra estrutura de DataFrame com as colunas que são necessarias para popular a tabela
        df_final = (
            df_filtered.groupby(["ANO", "MES", "MERCADO"])["RPK"].sum().reset_index()
        )

        # e aqui faz a inserção no banco com o db.session.add(flight)
        for _, row in df_final.iterrows():
            flight = Flight(
                ano=row["ANO"], mes=row["MES"], mercado=row["MERCADO"], rpk=row["RPK"]
            )
            db.session.add(flight)

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
    year_min = db.session.query(db.func.min(Flight.ano)).scalar()
    year_max = db.session.query(db.func.max(Flight.ano)).scalar()

    markets = Flight.query.with_entities(Flight.mercado).distinct().all()
    return render_template(
        "dashboard.html", markets=markets, year_min=year_min, year_max=year_max
    )


@app.route("/filter", methods=["POST"])
@login_required
def filter():
    market = request.form.get("market")
    start_year = int(request.form.get("start_year"))
    start_month = int(request.form.get("start_month"))
    end_year = int(request.form.get("end_year"))
    end_month = int(request.form.get("end_month"))

    flights = Flight.query.filter(
        Flight.mercado == market,
        Flight.ano >= start_year,
        Flight.mes >= start_month,
        Flight.ano <= end_year,
        Flight.mes <= end_month,
    ).all()

    return render_template("results.html", flights=flights)


if __name__ == "__main__":
    db.create_all()


# Para usar o shell do flask para debug
@app.shell_context_processor
def make_shell_context():
    return {"db": db, "User": User, "Flight": Flight, "hash": hash}
