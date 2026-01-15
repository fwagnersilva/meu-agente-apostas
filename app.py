import streamlit as st
import sqlite3
import pandas as pd
import os

st.set_page_config(page_title="Monitor de Apostas", layout="wide")

st.title("⚽ Monitor de Prognósticos")

if not os.path.exists("apostas_academia.db"):
    st.warning("⚠️ Banco de dados não encontrado. Rode o agente primeiro.")
else:
    conn = sqlite3.connect("apostas_academia.db")
    query = """
    SELECT 
        match_date as 'Data',
        league as 'Campeonato',
        home_team || ' X ' || away_team as 'Jogo',
        selection as 'Prognóstico',
        odd as 'Odd',
        status as 'Placar/Status'
    FROM predictions 
    ORDER BY date_collected DESC, match_date ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("🔍 Filtros Avançados")
    
    # Filtro por Dia
    dias = sorted(df['Data'].unique(), reverse=True)
    dia_sel = st.sidebar.selectbox("Selecionar Dia", options=["Todos"] + dias)
    if dia_sel != "Todos":
        df = df[df['Data'] == dia_sel]

    # Filtro por Campeonato
    campeonatos = sorted(df['Campeonato'].unique())
    camp_sel = st.sidebar.multiselect("Campeonato", options=campeonatos)
    if camp_sel:
        df = df[df['Campeonato'].isin(camp_sel)]

    # Filtro por Prognóstico
    prognosticos = sorted(df['Prognóstico'].unique())
    prog_sel = st.sidebar.multiselect("Prognóstico", options=prognosticos)
    if prog_sel:
        df = df[df['Prognóstico'].isin(prog_sel)]

    # Filtro por Odd
    min_odd = float(df['Odd'].min())
    max_odd = float(df['Odd'].max())
    if max_odd > min_odd:
        odd_range = st.sidebar.slider("Filtrar por Odd", min_odd, max_odd, (min_odd, max_odd))
        df = df[(df['Odd'] >= odd_range[0]) & (df['Odd'] <= odd_range[1])]

    # --- EXIBIÇÃO PRINCIPAL ---
    st.dataframe(
        df, 
        column_config={
            "Data": st.column_config.TextColumn("Data", width="medium"),
            "Campeonato": st.column_config.TextColumn("Campeonato", width="large"),
            "Jogo": st.column_config.TextColumn("Jogo", width="large"),
            "Prognóstico": st.column_config.TextColumn("Prognóstico", width="large"),
            "Odd": st.column_config.NumberColumn("Odd", format="%.2f"),
            "Placar/Status": st.column_config.TextColumn("Placar/Status", width="small")
        },
        hide_index=True,
        use_container_width=True
    )

    if st.button("🔄 Atualizar Dados"):
        st.rerun()
