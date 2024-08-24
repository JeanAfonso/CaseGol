from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import pandas as pd


class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///voos.db"

db = SQLAlchemy(app)

class Voo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ano = db.Column(db.Integer)
    mes = db.Column(db.Integer)
    mercado = db.Column(db.String(50))
    rpk = db.Column(db.Float)

@app.route('/')
def home():
    nome = "jean"
    idade = 33
    return render_template("index.html", nome=nome, idade=idade)


@app.route('/grafico')
def exibir_grafico():
    return render_template("grafico.html")
