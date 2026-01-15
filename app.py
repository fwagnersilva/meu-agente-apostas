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

    # Lógica de Data para separação
    # Formato esperado: "14 janeiro 2026"
    hoje_str = datetime.now().strftime("%d %B %Y").lower()
    # Tradução simples para português se necessário (Streamlit/Python pode variar)
    meses = {
        "january": "janeiro", "february": "fevereiro", "march": "março", 
        "april": "abril", "may": "maio", "june": "junho", 
        "july": "julho", "august": "agosto", "september": "setembro", 
        "october": "outubro", "november": "novembro", "december": "dezembro"
    }
    for eng, pt in meses.items():
        hoje_str = hoje_str.replace(eng, pt)

    # Separação dos DataFrames
    df_hoje = df[df['Data'].str.lower() == hoje_str]
    df_historico = df[df['Data'].str.lower() != hoje_str]

    # --- NAVEGAÇÃO ---
    aba1, aba2 = st.tabs(["📅 Jogos de Hoje", "📚 Histórico (Dias Anteriores)"])

    with aba1:
        st.header(f"Jogos de Hoje ({hoje_str.title()})")
        if df_hoje.empty:
            st.info("Nenhum jogo encontrado para a data de hoje até o momento.")
        else:
            st.dataframe(
                df_hoje[['Data', 'Campeonato', 'Jogo', 'Prognóstico', 'Odd', 'Placar/Status']], 
                hide_index=True, use_container_width=True
            )

    with aba2:
        st.header("Histórico de Prognósticos")
        
        # Filtros na barra lateral apenas para o histórico
        st.sidebar.header("🔍 Filtros do Histórico")
        
        dias = sorted(df_historico['Data'].unique(), reverse=True)
        dia_sel = st.sidebar.selectbox("Selecionar Dia", options=["Todos"] + dias)
        
        df_display = df_historico.copy()
        if dia_sel != "Todos":
            df_display = df_display[df_display['Data'] == dia_sel]

        campeonatos = sorted(df_display['Campeonato'].unique())
        camp_sel = st.sidebar.multiselect("Campeonato", options=campeonatos)
        if camp_sel:
            df_display = df_display[df_display['Campeonato'].isin(camp_sel)]

        min_odd = float(df_display['Odd'].min()) if not df_display.empty else 0.0
        max_odd = float(df_display['Odd'].max()) if not df_display.empty else 5.0
        if max_odd > min_odd:
            odd_range = st.sidebar.slider("Filtrar por Odd", min_odd, max_odd, (min_odd, max_odd))
            df_display = df_display[(df_display['Odd'] >= odd_range[0]) & (df_display['Odd'] <= odd_range[1])]

        if df_display.empty:
            st.info("Nenhum dado histórico encontrado com os filtros selecionados.")
        else:
            st.dataframe(
                df_display[['Data', 'Campeonato', 'Jogo', 'Prognóstico', 'Odd', 'Placar/Status']], 
                hide_index=True, use_container_width=True
            )

    if st.button("🔄 Atualizar Dados"):
        st.rerun()
