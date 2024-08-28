## Descrição do projeto

Este é um projeto Flask para análise e visualização de dados de voos.

Requisitos do projeto:

- Crie um banco de dados SQL com a tabela com informações a seguir:

  - Filtros:
    - cia aérea: EMPRESA = "GLO";
    - voos regulares: GRUPO_DE_VOO = "REGULAR";
    - voos do Brasil: NATUREZA = "DOMÉSTICA".

  - Agrupar informações de voos ida e volta, criando a coluna MERCADO.
    - MERCADO = AEROPORTO DE ORIGEM + AEROPORTO DE DESTINO, em **ordem alfabética**. 
        - Exemplo1: Origem = SBSV, Destino = SBGR -> Mercado = SBGRSBSV
        - Exemplo2: Origem = SBGR, Destino = SBSV -> Mercado = SBGRSBSV

  - Crie uma tabela, contendo as colunas:
    - ANO
    - MES
    - MERCADO
    - RPK

- A aplicação precisa ter:
  - Autenticação do usuário (login)
  - Filtro para o usuário selecionar o mercado
  - Filtro para selecionar o intervalo de datas (ANO/MÊS ou data inteira, de sua preferência)
  - Gráfico do RPK (eixo y) por data (eixo x), para o mercado e intervalo de datas selecionado pelo usuário


## Requisitos

- [Poetry](https://python-poetry.org/) - Gerenciador de dependências e ambientes virtuais para Python.

## Instalação

1. **Clone o repositório:**

    ```bash
    git clone https://github.com/JeanAfonso/CaseGol.git
    cd CaseGol
    ```

2. **Instale as dependências:**

    Certifique-se de ter o Poetry instalado. Você pode instalar o Poetry seguindo as [instruções de instalação](https://python-poetry.org/docs/#installation).

    Em seguida, no diretório raiz do projeto (onde está o `pyproject.toml`), execute:

    ```bash
    poetry install
    ```

    Este comando instalará todas as dependências listadas no `pyproject.toml` e criará um ambiente virtual para o projeto.

3. **Ative o ambiente virtual:**

    Após a instalação, você pode ativar o ambiente virtual criado pelo Poetry com:

    ```bash
    poetry shell
    ```

4. **Configure o banco de dados:**
    - Base de dados: https://sistemas.anac.gov.br/dadosabertos/Voos%20e%20opera%C3%A7%C3%B5es%20a%C3%A9reas/Dados%20Estat%C3%ADsticos%20do%20Transporte%20A%C3%A9reo/
    
    O projeto utiliza um banco de dados SQLite. Se necessário, você pode criar e popular o banco de dados com:

    Baixe o arquivo csv Dados_Estatisticos.csv

    e no app.py Linha 51 mude o caminho para a biblioteca pandas acessar o arquivo:

    ```bash
    if Flight.query.count() == 0:
        df = pd.read_csv(
            "/home/jean/CaseGol/Dados_Estatisticos.csv", <------- Altere aqui para o caminho onde o CSV esta salvo
            delimiter=";",
            quotechar='"',
            skipinitialspace=True,
            skiprows=1,
        )
    ```
    
5. **Execute o servidor:**

    Para rodar o servidor Flask, você pode usar:

    ```bash
    flask run
    ```

    Ou, se preferir, use o comando Poetry para executar o servidor:

    ```bash
    poetry run flask run
    ```

## Testes

Para rodar os testes, você pode usar o pytest. Execute:

```bash
poetry run pytest

