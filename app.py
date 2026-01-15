import streamlit as st
import sqlite3
import pandas as pd
import os
import re
from datetime import datetime

st.set_page_config(page_title="Monitor de Apostas", layout="wide")

def process_prediction(text):
    if not text: return "", 0.0
    clean_text = text.replace("Sugestão do editor", "").replace("Pub", "").strip()
    clean_text = clean_text.split("Aposte aqui")[0].split("As odds podem")[0].strip()
    odd = 0.0
    odd_match = re.search(r'Odd\s*(\d+\.\d+)', clean_text)
    if odd_match:
        odd = float(odd_match.group(1))
        clean_text = clean_text.split(odd_match.group(0))[0].strip()
    else:
        decimal_match = re.search(r'(\d+\.\d+)$', clean_text)
        if decimal_match:
            odd = float(decimal_match.group(1))
            clean_text = clean_text.replace(decimal_match.group(1), "").strip()
    return clean_text, odd

if not os.path.exists("apostas_academia.db"):
    st.warning("⚠️ Banco de dados não encontrado. Rode o agente primeiro.")
else:
    conn = sqlite3.connect("apostas_academia.db")
    query = """
    SELECT 
        match_date as 'Data',
        league as 'Campeonato',
        home_team || ' X ' || away_team as 'Jogo',
        selection as 'Raw_Selection',
        status as 'Placar/Status'
    FROM predictions 
    ORDER BY date_collected DESC, match_date ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    processed = df['Raw_Selection'].apply(process_prediction)
    df['Prognóstico'] = [p[0] for p in processed]
    df['Odd'] = [p[1] for p in processed]

    # --- NAVEGAÇÃO ---
    aba1, aba2 = st.tabs(["📅 Jogos de Hoje", "📚 Histórico Completo"])

    with aba1:
        st.header("Jogos do Dia")
        hoje_str = datetime.now().strftime("%d %B %Y")
        # Filtra por hoje (ou data mais recente)
        df_hoje = df[df['Data'].str.contains(datetime.now().strftime("%d"), na=False)]
        if df_hoje.empty:
            df_hoje = df.head(10) # Fallback para os mais recentes
        
        st.dataframe(
            df_hoje[['Data', 'Campeonato', 'Jogo', 'Prognóstico', 'Odd', 'Placar/Status']], 
            hide_index=True, use_container_width=True
        )

    with aba2:
        st.header("Histórico de Prognósticos")
        
        # Filtros na barra lateral apenas para o histórico
        st.sidebar.header("🔍 Filtros do Histórico")
        
        dias = sorted(df['Data'].unique(), reverse=True)
        dia_sel = st.sidebar.selectbox("Selecionar Dia", options=["Todos"] + dias)
        df_hist = df.copy()
        if dia_sel != "Todos":
            df_hist = df_hist[df_hist['Data'] == dia_sel]

        campeonatos = sorted(df_hist['Campeonato'].unique())
        camp_sel = st.sidebar.multiselect("Campeonato", options=campeonatos)
        if camp_sel:
            df_hist = df_hist[df_hist['Campeonato'].isin(camp_sel)]

        min_odd = float(df_hist['Odd'].min())
        max_odd = float(df_hist['Odd'].max())
        if max_odd > min_odd:
            odd_range = st.sidebar.slider("Filtrar por Odd", min_odd, max_odd, (min_odd, max_odd))
            df_hist = df_hist[(df_hist['Odd'] >= odd_range[0]) & (df_hist['Odd'] <= odd_range[1])]

        st.dataframe(
            df_hist[['Data', 'Campeonato', 'Jogo', 'Prognóstico', 'Odd', 'Placar/Status']], 
            hide_index=True, use_container_width=True
        )

    if st.button("🔄 Atualizar Dados"):
        st.rerun()
