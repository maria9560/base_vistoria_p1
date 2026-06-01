import streamlit as st
import pandas as pd

st.set_page_config(page_title="Acompanhamento Suspensão/Vistoria P1", layout="wide")

st.title("📋 Acompanhamento de Suspensão/Vistoria P1")

uploaded_file = st.file_uploader("Suba a base (.xlsx)", type=["xlsx"])

SUBTIPOS_P1 = [
    "P1 SUSPENSÃO - GRUPO A",
    "P1 SUSPENSÃO - POSTE",
    "P1 VISTORIA - RETIRADA DE RAMAL",
]

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Sheet1")

        # Validar colunas necessárias
        required_cols = {"Subtipo", "Data Inclusão", "Numero", "Valor Faturas"}
        if not required_cols.issubset(df.columns):
            st.error(f"Colunas esperadas não encontradas. Necessário: {required_cols}")
            st.stop()

        # Filtrar apenas subtipos P1
        df_p1 = df[df["Subtipo"].isin(SUBTIPOS_P1)].copy()

        # Tratar data
        df_p1["Data Inclusão"] = pd.to_datetime(df_p1["Data Inclusão"]).dt.date

        # Pivot: contagem de serviços por dia e subtipo
        pivot_qtd = (
            df_p1.groupby(["Data Inclusão", "Subtipo"])["Numero"]
            .count()
            .unstack(fill_value=0)
            .reindex(columns=SUBTIPOS_P1, fill_value=0)
        )

        # Total geral por dia
        pivot_qtd["Total Geral"] = pivot_qtd.sum(axis=1)

        # Soma da dívida por dia
        divida_dia = (
            df_p1.groupby("Data Inclusão")["Valor Faturas"]
            .sum()
            .rename("Total Dívida")
        )

        # Montar tabela final
        tabela = pivot_qtd.join(divida_dia).reset_index()
        tabela = tabela.rename(columns={"Data Inclusão": "DATA"})
        tabela = tabela.sort_values("DATA")

        # Linha de totais
        totais = tabela.drop(columns="DATA").sum()
        totais_row = pd.DataFrame([["Total Geral"] + totais.tolist()], columns=tabela.columns)
        tabela_exibir = pd.concat([tabela, totais_row], ignore_index=True)

        # Formatar datas
        tabela_exibir["DATA"] = tabela_exibir["DATA"].apply(
            lambda x: x.strftime("%d/%b").replace("/0", "/").replace(
                "Jan","jan").replace("Feb","fev").replace("Mar","mar").replace(
                "Apr","abr").replace("May","mai").replace("Jun","jun").replace(
                "Jul","jul").replace("Aug","ago").replace("Sep","set").replace(
                "Oct","out").replace("Nov","nov").replace("Dec","dez")
            if hasattr(x, "strftime") else str(x)
        )

        # Formatar dívida como moeda BR
        tabela_exibir["Total Dívida"] = tabela_exibir["Total Dívida"].apply(
            lambda x: f"R$ {float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            if x != "Total Dívida" else x
        )

        # Métricas resumo
        st.subheader("Resumo do Período")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("P1 Suspensão - Grupo A", int(pivot_qtd["P1 SUSPENSÃO - GRUPO A"].sum()))
        col2.metric("P1 Suspensão - Poste", int(pivot_qtd["P1 SUSPENSÃO - POSTE"].sum()))
        col3.metric("P1 Vistoria - Ret. Ramal", int(pivot_qtd["P1 VISTORIA - RETIRADA DE RAMAL"].sum()))
        total_divida = divida_dia.sum()
        total_fmt = f"R$ {total_divida:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        col4.metric("Total Dívida", total_fmt)

        st.divider()
        st.subheader("Detalhamento por Dia")
        st.dataframe(
            tabela_exibir,
            use_container_width=True,
            hide_index=True,
            column_config={
                "DATA": st.column_config.TextColumn("DATA"),
                "P1 SUSPENSÃO - GRUPO A": st.column_config.NumberColumn("P1 SUSPENSÃO - GRUPO A"),
                "P1 SUSPENSÃO - POSTE": st.column_config.NumberColumn("P1 SUSPENSÃO - POSTE"),
                "P1 VISTORIA - RETIRADA DE RAMAL": st.column_config.NumberColumn("P1 VISTORIA - RETIRADA DE RAMAL"),
                "Total Geral": st.column_config.NumberColumn("Total Geral"),
                "Total Dívida": st.column_config.TextColumn("Total Dívida"),
            },
        )

    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
else:
    st.info("👆 Suba um arquivo .xlsx para começar.")
