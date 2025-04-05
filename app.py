import streamlit as st
import pandas as pd
import plotly.express as px

# CONFIGURAÇÕES INICIAIS
st.set_page_config(page_title="Cotação de Insumos", layout="wide")

# LOGO E TÍTULO
st.image("https://i.imgur.com/FVfXZZG.png", width=100)  # Troque pela sua logo, se quiser
st.markdown("<h1 style='color:#2E86C1;'>📦 Sistema de Cotação de Insumos</h1>", unsafe_allow_html=True)

# UPLOAD
st.sidebar.header("📁 Upload de Arquivos Excel")
insumos_file = st.sidebar.file_uploader("Insumos", type="xlsx")
fornecedores_file = st.sidebar.file_uploader("Fornecedores", type="xlsx")
cotacoes_file = st.sidebar.file_uploader("Cotações", type="xlsx")

if insumos_file and fornecedores_file and cotacoes_file:
    insumos_df = pd.read_excel(insumos_file)
    fornecedores_df = pd.read_excel(fornecedores_file)
    cotacoes_df = pd.read_excel(cotacoes_file)

    # Padroniza nomes das colunas
    insumos_df.columns = insumos_df.columns.str.strip()
    fornecedores_df.columns = fornecedores_df.columns.str.strip()
    cotacoes_df.columns = cotacoes_df.columns.str.strip()

    # Combinação de dados
    df = cotacoes_df.merge(insumos_df, on="ID Insumo")
    df = df.merge(fornecedores_df, on="ID Fornecedor")
    df = df.rename(columns={"Nome_x": "Nome Insumo", "Nome_y": "Nome Fornecedor"})

    # 🔍 AUTOCOMPLETE DE INSUMOS
    st.subheader("🔎 Buscar Insumo por Nome")
    busca_nome = st.text_input("Digite o nome do insumo (ou parte dele):")
    if busca_nome:
        resultados = df[df["Nome Insumo"].str.contains(busca_nome, case=False)]
        st.dataframe(resultados)

    # 🎛️ FILTROS
    st.subheader("🎛️ Filtros")
    insumo_opcoes = df["Nome Insumo"].unique()
    insumo_selecionado = st.multiselect("Filtrar por insumo:", options=insumo_opcoes, default=insumo_opcoes)
    fornecedor_opcoes = df["Nome Fornecedor"].unique()
    fornecedor_selecionado = st.multiselect("Filtrar por fornecedor:", options=fornecedor_opcoes, default=fornecedor_opcoes)

    df_filtrado = df[df["Nome Insumo"].isin(insumo_selecionado) & df["Nome Fornecedor"].isin(fornecedor_selecionado)]

    st.subheader("📊 Cotações Filtradas")
    st.dataframe(df_filtrado)

    # ✅ MELHORES COTAÇÕES
    melhores = df_filtrado.sort_values("Preço Unitário").groupby("ID Insumo").first().reset_index()
    st.subheader("✅ Melhores Cotações por Insumo")
    st.dataframe(melhores)

    # 📈 GRÁFICOS
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

    # 💰 SIMULADOR DE PEDIDO
    st.subheader("📦 Simulador de Pedido")

    nome_insumo = st.selectbox("Selecione o insumo:", insumo_opcoes)
    fornecedores_disponiveis = df_filtrado[df_filtrado["Nome Insumo"] == nome_insumo]["Nome Fornecedor"].unique()

    if len(fornecedores_disponiveis) > 0:
        nome_fornecedor = st.selectbox("Selecione o fornecedor:", fornecedores_disponiveis)
        quantidade = st.number_input("Quantidade desejada:", min_value=1, value=10)

        cotacao_escolhida = df_filtrado[
            (df_filtrado["Nome Insumo"] == nome_insumo) &
            (df_filtrado["Nome Fornecedor"] == nome_fornecedor)
        ].iloc[0]

        preco_unitario = cotacao_escolhida["Preço Unitário"]
        total = preco_unitario * quantidade

        st.success(f"💵 Total estimado: R${total:,.2f} (R${preco_unitario:.2f} x {quantidade})")
    else:
        st.warning("⚠️ Nenhum fornecedor disponível para o insumo selecionado.")

    # 📤 EXPORTAR
    if st.button("📤 Exportar Cotações Filtradas"):
        with pd.ExcelWriter("resultado_filtrado.xlsx", engine="openpyxl") as writer:
            df_filtrado.to_excel(writer, sheet_name="Cotações Filtradas", index=False)
            melhores.to_excel(writer, sheet_name="Melhores", index=False)
            media_fornecedores.to_excel(writer, sheet_name="Média", index=False)
        st.success("✅ Arquivo salvo como 'resultado_filtrado.xlsx'.")
else:
    st.warning("📥 Faça o upload de todos os arquivos Excel para começar.")
