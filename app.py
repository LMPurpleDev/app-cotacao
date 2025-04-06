import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import base64
from io import BytesIO
import smtplib
from email.message import EmailMessage

# CONFIGURAÇÃO
st.set_page_config(page_title="App Cotação", layout="wide")

# FUNÇÃO PARA ENVIAR E-MAIL
def enviar_email(destinatario, assunto, corpo, anexo_nome, anexo_dados):
    email = EmailMessage()
    email['Subject'] = assunto
    email['From'] = 'seu_email@gmail.com'  # Trocar para e-mail real
    email['To'] = destinatario
    email.set_content(corpo)
    email.add_attachment(anexo_dados, maintype='application', subtype='octet-stream', filename=anexo_nome)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login('seu_email@gmail.com', 'sua_senha')  # Trocar para credenciais reais
        smtp.send_message(email)

# FUNÇÃO PARA GERAR NOVO ID
def gerar_novo_id(df, coluna_id):
    if coluna_id not in df.columns or df.empty:
        return 1
    else:
        return df[coluna_id].max() + 1

# SIDEBAR - UPLOAD
st.sidebar.title("📁 Upload de Arquivos")
insumos_file = st.sidebar.file_uploader("Insumos", type="xlsx")
fornecedores_file = st.sidebar.file_uploader("Fornecedores", type="xlsx")
cotacoes_file = st.sidebar.file_uploader("Cotações", type="xlsx")

if insumos_file and fornecedores_file and cotacoes_file:
    insumos_df = pd.read_excel(insumos_file)
    fornecedores_df = pd.read_excel(fornecedores_file)
    cotacoes_df = pd.read_excel(cotacoes_file)

    insumos_df.columns = insumos_df.columns.str.strip()
    fornecedores_df.columns = fornecedores_df.columns.str.strip()
    cotacoes_df.columns = cotacoes_df.columns.str.strip()

    df = cotacoes_df.merge(insumos_df, on="ID Insumo")
    df = df.merge(fornecedores_df, on="ID Fornecedor")
    df = df.rename(columns={"Nome_x": "Nome Insumo", "Nome_y": "Nome Fornecedor"})

    insumo_opcoes = df["Nome Insumo"].unique()
    fornecedor_opcoes = df["Nome Fornecedor"].unique()

    abas = st.tabs([
        "🔍 Buscar Insumo", "🎛️ Filtros e Cotações", "📊 Dashboard", "📦 Criação de Pedidos",
        "📁 Histórico", "📤 Exportar Dados", "📋 Cadastro", "🔎 Consultar"
    ])

    # ABA 1 - BUSCAR INSUMO
    with abas[0]:
        st.subheader("🔍 Buscar Insumo")
        busca_nome = st.text_input("Digite o nome do insumo (ou parte dele):")
        if busca_nome:
            resultados = df[df["Nome Insumo"].str.contains(busca_nome, case=False)]
            st.dataframe(resultados)

    # ABA 2 - FILTROS E COTAÇÕES
    with abas[1]:
        st.subheader("🎛️ Filtros")
        insumo_selecionado = st.multiselect("Filtrar por insumo:", options=insumo_opcoes, default=insumo_opcoes)
        fornecedor_selecionado = st.multiselect("Filtrar por fornecedor:", options=fornecedor_opcoes, default=fornecedor_opcoes)

        df_filtrado = df[df["Nome Insumo"].isin(insumo_selecionado) & df["Nome Fornecedor"].isin(fornecedor_selecionado)]

        st.subheader("📊 Cotações Filtradas")
        st.dataframe(df_filtrado)

        melhores = df_filtrado.sort_values("Preço Unitário").groupby("ID Insumo").first().reset_index()
        st.subheader("✅ Melhores Cotações por Insumo")
        st.dataframe(melhores)

    # ABA 3 - DASHBOARD
    with abas[2]:
        st.subheader("📈 Gráficos Comparativos")

        fig_melhores = px.bar(
            melhores, x="Nome Insumo", y="Preço Unitário", color="Nome Fornecedor",
            title="🟩 Melhor Preço por Insumo"
        )
        st.plotly_chart(fig_melhores, use_container_width=True)

        fig_dispersao = px.scatter(
            df_filtrado, x="Nome Insumo", y="Preço Unitário", color="Nome Fornecedor",
            size="Preço Unitário", title="🟨 Dispersão de Preços por Insumo"
        )
        st.plotly_chart(fig_dispersao, use_container_width=True)

        media_fornecedores = df_filtrado.groupby("Nome Fornecedor")["Preço Unitário"].mean().reset_index()
        fig_media = px.bar(
            media_fornecedores, x="Nome Fornecedor", y="Preço Unitário",
            title="🟥 Preço Médio por Fornecedor"
        )
        st.plotly_chart(fig_media, use_container_width=True)

    # ABA 4 - CRIAÇÃO DE PEDIDOS
    with abas[3]:
        st.subheader("📦 Criação de Pedido com Envio por E-mail")

        nome_insumo = st.selectbox("Selecione o insumo:", insumo_opcoes)
        fornecedores_disponiveis = df[df["Nome Insumo"] == nome_insumo]["Nome Fornecedor"].unique()

        if len(fornecedores_disponiveis) > 0:
            nome_fornecedor = st.selectbox("Selecione o fornecedor:", fornecedores_disponiveis)
            quantidade = st.number_input("Quantidade desejada:", min_value=1, value=10)
            previsao_entrega = st.date_input("Previsão de entrega")

            cotacao_escolhida = df[
                (df["Nome Insumo"] == nome_insumo) & (df["Nome Fornecedor"] == nome_fornecedor)
            ].iloc[0]

            preco_unitario = cotacao_escolhida["Preço Unitário"]
            total = preco_unitario * quantidade

            st.success(f"💵 Total estimado: R${total:,.2f} (R${preco_unitario:.2f} x {quantidade})")

            if st.button("📧 Enviar Pedido por E-mail"):
                agora = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                nome_arquivo = f"pedido_{agora}.xlsx"
                pedido_df = pd.DataFrame([{
                    **cotacao_escolhida, "Quantidade": quantidade,
                    "Total": total, "Previsão Entrega": previsao_entrega
                }])

                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    pedido_df.to_excel(writer, index=False)
                dados_excel = output.getvalue()

                enviar_email(
                    destinatario="fornecedor@email.com",
                    assunto="Novo Pedido de Insumo",
                    corpo=f"Segue em anexo o pedido do insumo '{nome_insumo}' com entrega prevista para {previsao_entrega}.",
                    anexo_nome=nome_arquivo,
                    anexo_dados=dados_excel
                )
                st.success("✅ Pedido enviado com sucesso!")
        else:
            st.warning("⚠️ Nenhum fornecedor disponível para o insumo selecionado.")

    # ABA 5 - HISTÓRICO
    with abas[4]:
        st.subheader("📁 Histórico de Cotações")
        st.info("Histórico é gerado automaticamente ao enviar pedidos. Consulte os arquivos na pasta de saída ou banco.")

    # ABA 6 - EXPORTAR
    with abas[5]:
        if st.button("📤 Exportar Cotações Filtradas"):
            with pd.ExcelWriter("resultado_filtrado.xlsx", engine="openpyxl") as writer:
                df_filtrado.to_excel(writer, sheet_name="Cotações Filtradas", index=False)
                melhores.to_excel(writer, sheet_name="Melhores", index=False)
                media_fornecedores.to_excel(writer, sheet_name="Média", index=False)
            st.success("✅ Arquivo salvo como 'resultado_filtrado.xlsx'.")

    # ABA 7 - CADASTRO
    with abas[6]:
        st.subheader("📋 Cadastro de Dados")
        tipo_cadastro = st.selectbox("Escolha o tipo de cadastro:", ["Insumo", "Fornecedor", "Cotação"])

        if tipo_cadastro == "Insumo":
            novo_id = gerar_novo_id(insumos_df, "ID Insumo")
            novo_nome = st.text_input("Nome")
            nova_unidade = st.text_input("Unidade")
            nova_quantidade = st.number_input("Quantidade", min_value=0)
            if st.button("Salvar Insumo"):
                novo = pd.DataFrame([[novo_id, novo_nome, nova_unidade, nova_quantidade]], columns=insumos_df.columns)
                insumos_df = pd.concat([insumos_df, novo], ignore_index=True)
                st.success("✅ Insumo cadastrado com sucesso!")

        elif tipo_cadastro == "Fornecedor":
            novo_id = gerar_novo_id(fornecedores_df, "ID Fornecedor")
            novo_nome = st.text_input("Nome")
            novo_cnpj = st.text_input("CNPJ")
            novo_contato = st.text_input("Contato")
            if st.button("Salvar Fornecedor"):
                novo = pd.DataFrame([[novo_id, novo_nome, novo_cnpj, novo_contato]], columns=fornecedores_df.columns)
                fornecedores_df = pd.concat([fornecedores_df, novo], ignore_index=True)
                st.success("✅ Fornecedor cadastrado com sucesso!")

        elif tipo_cadastro == "Cotação":
            novo_id = gerar_novo_id(cotacoes_df, "ID Cotação")
            id_insumo = st.selectbox("ID Insumo", insumos_df["ID Insumo"].unique())
            id_fornecedor = st.selectbox("ID Fornecedor", fornecedores_df["ID Fornecedor"].unique())
            preco_unitario = st.number_input("Preço Unitário", min_value=0.01)
            prazo = st.number_input("Prazo (dias)", min_value=0)
            validade = st.number_input("Validade (dias)", min_value=0)
            observacoes = st.text_area("Observações")
            if st.button("Salvar Cotação"):
                novo = pd.DataFrame([[novo_id, id_insumo, id_fornecedor, preco_unitario, prazo, validade, observacoes]], columns=cotacoes_df.columns)
                cotacoes_df = pd.concat([cotacoes_df, novo], ignore_index=True)
                st.success("✅ Cotação cadastrada com sucesso!")

    # ABA 8 - CONSULTAR
    with abas[7]:
        st.subheader("🔎 Consultar Dados")
        tipo_consulta = st.selectbox("Escolha a planilha para visualizar:", ["Insumos", "Fornecedores", "Cotações"])
        if tipo_consulta == "Insumos":
            st.dataframe(insumos_df)
        elif tipo_consulta == "Fornecedores":
            st.dataframe(fornecedores_df)
        elif tipo_consulta == "Cotações":
            st.dataframe(cotacoes_df)

else:
    st.warning("📥 Faça o upload de todos os arquivos Excel para começar.")
