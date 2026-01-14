import streamlit as st
import sqlite3
import pandas as pd
import os

# Configuração da página
st.set_page_config(page_title="Dashboard de Apostas", layout="wide")

st.title("📊 Monitor de Prognósticos - Academia das Apostas")

# Verifica se o banco de dados existe
if not os.path.exists("apostas_academia.db"):
    st.warning("⚠️ Banco de dados ainda não encontrado. Aguarde a primeira execução do agente.")
else:
    # Conecta ao banco
    conn = sqlite3.connect("apostas_academia.db")
    
    # Query para pegar os dados
    query = """
    SELECT 
        match_date as 'Data',
        league as 'Liga',
        home_team as 'Mandante',
        away_team as 'Visitante',
        selection as 'Palpite',
        status as 'Status',
        score_home as 'Gols Casa',
        score_away as 'Gols Fora'
    FROM predictions 
    ORDER BY date_collected DESC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Filtros laterais
    st.sidebar.header("Filtros")
    leagues = st.sidebar.multiselect("Filtrar por Liga", options=df["Liga"].unique())
    if leagues:
        df = df[df["Liga"].isin(leagues)]

    # Métricas rápidas (KPIs)
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Jogos Coletados", len(df))
    col2.metric("Jogos Pendentes", len(df[df['Status'] == 'PENDING']))
    # Simulação de Green (se tiver status)
    greens = len(df[df['Status'] == 'WON'])
    if len(df) > 0:
        win_rate = (greens / len(df)) * 100
    else:
        win_rate = 0
    col3.metric("Taxa de Acerto (Simulada)", f"{win_rate:.1f}%")

    # Tabela principal
    st.subheader("📋 Lista de Prognósticos")
    st.dataframe(df, use_container_width=True)

    # Botão para atualizar
    if st.button("🔄 Atualizar Dados"):
        st.rerun()
