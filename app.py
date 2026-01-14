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
    
    # Query ajustada para mostrar Data Real do jogo e Palpite limpo
    query = """
    SELECT 
        match_date_time as 'Data/Hora',
        league as 'Campeonato',
        home_team || ' vs ' || away_team as 'Jogo',
        selection as 'Palpite',
        status as 'Status'
    FROM predictions 
    ORDER BY date_collected DESC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Filtros
    st.sidebar.header("Filtros")
    ligas = st.sidebar.multiselect("Campeonato", options=df["Campeonato"].unique())
    if ligas:
        df = df[df["Campeonato"].isin(ligas)]

    # Exibição Principal - Removida a configuração de StatusColumn que causava erro
    st.dataframe(
        df, 
        column_config={
            "Data/Hora": st.column_config.TextColumn("Data/Hora", width="medium"),
            "Campeonato": st.column_config.TextColumn("Campeonato", width="medium"),
            "Jogo": st.column_config.TextColumn("Jogo", width="large"),
            "Palpite": st.column_config.TextColumn("Palpite", width="large"),
            "Status": st.column_config.TextColumn("Resultado")
        },
        hide_index=True,
        use_container_width=True
    )

    if st.button("🔄 Atualizar"):
        st.rerun()
