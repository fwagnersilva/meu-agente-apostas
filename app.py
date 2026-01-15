import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Monitor de Apostas", layout="wide")

st.title("⚽ Monitor de Prognósticos")

if not os.path.exists("apostas_academia.db"):
    st.warning("⚠️ Banco de dados não encontrado. Rode o agente primeiro.")
else:
    conn = sqlite3.connect("apostas_academia.db")
    
    # Query para pegar os dados
    query = """
    SELECT 
        match_date_time as 'Data/Hora',
        league as 'Campeonato',
        home_team as 'Mandante',
        away_team as 'Visitante',
        selection as 'Palpite',
        status as 'Status',
        date_collected
    FROM predictions 
    ORDER BY match_date_time ASC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Tratamento de Data para Filtro
    # Tenta extrair apenas a data do texto "14 janeiro 2026 - 19:30"
    def extract_date(text):
        try:
            # Pega a parte antes do " - "
            date_part = text.split(" - ")[0]
            return date_part
        except:
            return "Outros"

    df['Dia'] = df['Data/Hora'].apply(extract_date)
    df['Jogo'] = df['Mandante'] + " vs " + df['Visitante']

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("🔍 Filtros")
    
    # Filtro por Dia
    dias_disponiveis = sorted(df['Dia'].unique())
    dia_selecionado = st.sidebar.selectbox("Selecionar Dia", options=["Todos"] + dias_disponiveis)
    
    if dia_selecionado != "Todos":
        df = df[df['Dia'] == dia_selecionado]

    # Filtro por Campeonato
    campeonatos = sorted(df['Campeonato'].unique())
    campeonato_sel = st.sidebar.multiselect("Campeonato", options=campeonatos)
    if campeonato_sel:
        df = df[df['Campeonato'].isin(campeonato_sel)]

    # Filtro por Palpite (Prognóstico)
    palpites = sorted(df['Palpite'].unique())
    palpite_sel = st.sidebar.multiselect("Prognóstico", options=palpites)
    if palpite_sel:
        df = df[df['Palpite'].isin(palpite_sel)]

    # --- EXIBIÇÃO PRINCIPAL ---
    
    # Métricas
    col1, col2 = st.columns(2)
    col1.metric("Jogos Exibidos", len(df))
    col2.metric("Campeonatos", len(df['Campeonato'].unique()))

    # Tabela
    cols_to_show = ['Data/Hora', 'Campeonato', 'Jogo', 'Palpite', 'Status']
    
    st.dataframe(
        df[cols_to_show], 
        column_config={
            "Data/Hora": st.column_config.TextColumn("Data/Hora", width="medium"),
            "Campeonato": st.column_config.TextColumn("Campeonato", width="medium"),
            "Jogo": st.column_config.TextColumn("Jogo", width="large"),
            "Palpite": st.column_config.TextColumn("Palpite", width="large"),
            "Status": st.column_config.TextColumn("Status")
        },
        hide_index=True,
        use_container_width=True
    )

    if st.button("🔄 Atualizar Dados"):
        st.rerun()
