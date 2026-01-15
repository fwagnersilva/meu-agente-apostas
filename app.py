import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime

st.set_page_config(page_title="Monitor de Apostas", layout="wide")

st.title("⚽ Monitor de Prognósticos & Resultados")

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
        status as 'Placar/Status'
    FROM predictions 
    ORDER BY match_date_time DESC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Tratamento de Data para Filtro
    def extract_date(text):
        try:
            return text.split(" - ")[0]
        except:
            return "Outros"

    df['Dia'] = df['Data/Hora'].apply(extract_date)
    df['Jogo'] = df['Mandante'] + " vs " + df['Visitante']

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("🔍 Filtros")
    
    # Filtro por Dia
    dias_disponiveis = sorted(df['Dia'].unique(), reverse=True)
    dia_selecionado = st.sidebar.selectbox("Selecionar Dia", options=["Todos"] + dias_disponiveis)
    
    if dia_selecionado != "Todos":
        df = df[df['Dia'] == dia_selecionado]

    # Filtro por Campeonato
    campeonatos = sorted(df['Campeonato'].unique())
    campeonato_sel = st.sidebar.multiselect("Campeonato", options=campeonatos)
    if campeonato_sel:
        df = df[df['Campeonato'].isin(campeonato_sel)]

    # --- EXIBIÇÃO PRINCIPAL ---
    
    # Métricas
    col1, col2, col3 = st.columns(3)
    col1.metric("Jogos Coletados", len(df))
    
    # Conta quantos jogos já têm placar (não são PENDING)
    com_resultado = len(df[df['Placar/Status'] != 'PENDING'])
    col2.metric("Com Resultado", com_resultado)
    col3.metric("Campeonatos", len(df['Campeonato'].unique()))

    # Tabela
    st.subheader(f"📋 Prognósticos - {dia_selecionado}")
    
    cols_to_show = ['Data/Hora', 'Campeonato', 'Jogo', 'Palpite', 'Placar/Status']
    
    st.dataframe(
        df[cols_to_show], 
        column_config={
            "Data/Hora": st.column_config.TextColumn("Data/Hora", width="medium"),
            "Campeonato": st.column_config.TextColumn("Campeonato", width="medium"),
            "Jogo": st.column_config.TextColumn("Jogo", width="large"),
            "Palpite": st.column_config.TextColumn("Palpite", width="large"),
            "Placar/Status": st.column_config.TextColumn("Placar/Status", width="small")
        },
        hide_index=True,
        use_container_width=True
    )

    st.info("💡 Dica: Jogos com placar (ex: 1 - 0) já foram finalizados ou estão em andamento. Compare com o palpite para avaliar o desempenho!")

    if st.button("🔄 Atualizar Dados"):
        st.rerun()
