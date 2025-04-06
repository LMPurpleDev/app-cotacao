import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from streamlit_option_menu import option_menu
import plotly.express as px

# Autenticação do Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("cotacaostreamlit-6c6474fd809e.json", scope)
client = gspread.authorize(creds)

# Planilhas
sheet = client.open("App Compras")
sheet_insumos = sheet.worksheet("Insumos")
sheet_fornecedores = sheet.worksheet("Fornecedores")
sheet_cotacoes = sheet.worksheet("Cotações")

# Funções auxiliares
def autenticar_usuario():
    st.title("Login")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if username == "admin" and password == "admin":
            st.session_state.autenticado = True
        else:
            st.error("Usuário ou senha incorretos.")

def buscar_insumos():
    st.header("🔍 Buscar Insumos")
    df = pd.DataFrame(sheet_insumos.get_all_records())
    termo = st.text_input("Buscar por nome ou código")
    if termo:
        df = df[df.apply(lambda row: termo.lower() in str(row).lower(), axis=1)]
    st.dataframe(df)

def cadastro():
    st.header("📝 Cadastro")
    aba = st.radio("Escolha o que deseja cadastrar:", ["Insumo", "Fornecedor", "Cotação"])

    if aba == "Insumo":
        nome = st.text_input("Nome do insumo")
        codigo = st.text_input("Código")
        unidade = st.text_input("Unidade")
        if st.button("Cadastrar Insumo"):
            if nome and codigo and unidade:
                sheet_insumos.append_row([nome, codigo, unidade])
                st.success("Insumo cadastrado com sucesso!")

    elif aba == "Fornecedor":
        nome = st.text_input("Nome do fornecedor")
        cnpj = st.text_input("CNPJ")
        email = st.text_input("E-mail")
        if st.button("Cadastrar Fornecedor"):
            if nome and cnpj and email:
                sheet_fornecedores.append_row([nome, cnpj, email])
                st.success("Fornecedor cadastrado com sucesso!")

    elif aba == "Cotação":
        insumo = st.text_input("Nome do insumo")
        fornecedor = st.text_input("Nome do fornecedor")
        valor = st.number_input("Valor da cotação", min_value=0.0, format="%.2f")
        data = st.date_input("Data da cotação")
        if st.button("Cadastrar Cotação"):
            if insumo and fornecedor and valor and data:
                sheet_cotacoes.append_row([insumo, fornecedor, valor, str(data)])
                st.success("Cotação cadastrada com sucesso!")

def consultar():
    st.header("📋 Consultar Registros")
    aba = st.radio("Escolha o que deseja visualizar:", ["Insumos", "Fornecedores", "Cotações"])

    if aba == "Insumos":
        st.dataframe(pd.DataFrame(sheet_insumos.get_all_records()))
    elif aba == "Fornecedores":
        st.dataframe(pd.DataFrame(sheet_fornecedores.get_all_records()))
    elif aba == "Cotações":
        st.dataframe(pd.DataFrame(sheet_cotacoes.get_all_records()))

def dashboards():
    st.header("📊 Dashboards")
    df = pd.DataFrame(sheet_cotacoes.get_all_records())

    if df.empty:
        st.info("Nenhuma cotação encontrada.")
        return

    df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    st.subheader("Média de Preço por Fornecedor")
    grafico = df.groupby("fornecedor")["valor"].mean().reset_index()
    fig = px.bar(grafico, x="fornecedor", y="valor", title="Média de valores por fornecedor")
    st.plotly_chart(fig)

    st.subheader("Evolução de Preços por Insumo")
    insumo_selecionado = st.selectbox("Escolha um insumo", df["insumo"].unique())
    df_filtrado = df[df["insumo"] == insumo_selecionado]
    fig2 = px.line(df_filtrado, x="data", y="valor", color="fornecedor",
                   title=f"Histórico de preços - {insumo_selecionado}")
    st.plotly_chart(fig2)

# App principal
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    autenticar_usuario()
else:
    st.set_page_config(page_title="CotacaoStreamlit", layout="wide")
    with st.sidebar:
        escolha = option_menu(
            menu_title="Menu",
            options=["Buscar", "Cadastro", "Consultar", "Dashboards"],
            icons=["search", "clipboard-plus", "table", "bar-chart"],
            menu_icon="cast",
            default_index=0,
        )

    if escolha == "Buscar":
        buscar_insumos()
    elif escolha == "Cadastro":
        cadastro()
    elif escolha == "Consultar":
        consultar()
    elif escolha == "Dashboards":
        dashboards()
