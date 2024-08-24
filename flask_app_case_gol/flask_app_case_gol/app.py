from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import pandas as pd

app = Flask(__name__)

#DB config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///voos.db"
db = SQLAlchemy()
db.init_app(app)

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
            '/home/jean/CaseGol/Dados_Estatisticos.csv', delimiter=';',
            quotechar='"', skipinitialspace=True, skiprows=1
            )
        
        # Filtrar os dados
        df_filtered = df[
            (df['EMPRESA_SIGLA'] == 'GLO') &
            (df['GRUPO_DE_VOO'] == 'REGULAR') &
            (df['NATUREZA'] == 'DOMÉSTICA')
        ]
        
        # Agrupar e criar a coluna MERCADO
        df_filtered['MERCADO'] = df_filtered.apply(
            lambda row: ''.join(sorted([row['AEROPORTO_DE_ORIGEM_SIGLA'], row['AEROPORTO_DE_DESTINO_SIGLA']])),
            axis=1
        )
        
        # Criar um novo DataFrame com as colunas necessárias
        df_final = df_filtered.groupby(['ANO', 'MES', 'MERCADO'])['RPK'].sum().reset_index()

        # Inserir os dados no banco de dados
        for _, row in df_final.iterrows():
            voo = Voo(ano=row['ANO'], mes=row['MES'], mercado=row['MERCADO'], rpk=row['RPK'])
            db.session.add(voo)
        
        db.session.commit()

# Seção de login


# Routes
@app.route('/')
def home():
    nome = "jean"
    idade = 33
    return render_template("dashboard.html", nome=nome, idade=idade)


@app.route('/dash')
def exibir_grafico():
    return render_template("dash.html")

if __name__ == '__main__':
    db.create_all()
