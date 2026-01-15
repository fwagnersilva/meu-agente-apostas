import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import re

st.set_page_config(page_title="Monitor de Apostas", layout="wide")

@st.cache_resource
def get_db_connection():
    return sqlite3.connect("apostas_academia.db")

def load_data():
    """Carrega dados do banco com tratamento de erros."""
    try:
        conn = get_db_connection()
        query = """
        SELECT 
            match_date,
            match_time,
            league,
            home_team,
            away_team,
            selection,
            odd,
            status
        FROM predictions 
        ORDER BY match_date DESC, match_time ASC
        """
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {e}")
        return pd.DataFrame()

def format_match_date(date_str):
    """Converte '2026-01-15' para 'sexta, 15 de janeiro'."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        weekday = {0: 'segunda', 1: 'terça', 2: 'quarta', 3: 'quinta', 
                   4: 'sexta', 5: 'sábado', 6: 'domingo'}[dt.weekday()]
        month = {1: 'janeiro', 2: 'fevereiro', 3: 'março', 4: 'abril',
                 5: 'maio', 6: 'junho', 7: 'julho', 8: 'agosto',
                 9: 'setembro', 10: 'outubro', 11: 'novembro', 12: 'dezembro'}[dt.month]
        return f"{weekday}, {dt.day} de {month}"
    except:
        return date_str

def categorize_games(df):
    """Separa jogos em: Hoje, Próximos 7 dias, Histórico."""
    today = datetime.now().date()
    
    df_today = df[df['match_date'] == today.isoformat()]
    
    next_week = today + timedelta(days=7)
    df_upcoming = df[
        (df['match_date'] > today.isoformat()) & 
        (df['match_date'] <= next_week.isoformat())
    ]
    
    df_history = df[df['match_date'] < today.isoformat()]
    
    return df_today, df_upcoming, df_history

def display_games_table(df, title):
    """Exibe tabela formatada."""
    if df.empty:
        st.info("Nenhum jogo nesta categoria.")
        return
    
    display_df = df.copy()
    display_df['match_date'] = display_df['match_date'].apply(format_match_date)
    display_df['Jogo'] = display_df['home_team'] + ' vs ' + display_df['away_team']
    display_df['odd'] = display_df['odd'].apply(lambda x: f"{x:.2f}" if x > 0 else "—")
    
    cols_to_show = ['match_date', 'match_time', 'league', 'Jogo', 'selection', 'odd', 'status']
    cols_rename = {'match_date': 'Data', 'match_time': 'Hora', 'league': 'Campeonato', 
                   'selection': 'Prognóstico', 'odd': 'Odd', 'status': 'Status'}
    
    st.dataframe(
        display_df[cols_to_show].rename(columns=cols_rename),
        hide_index=True,
        use_container_width=True
    )

# ===== MAIN APP =====
st.title("📊 Monitor de Apostas - Academia")
st.markdown("Dashboard ao vivo com prognósticos de futebol")

df = load_data()

if df.empty:
    st.warning("⚠️ Banco de dados vazio. Execute o agente para coletar dados.")
else:
    df_today, df_upcoming, df_history = categorize_games(df)
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        f"📅 Hoje ({len(df_today)})",
        f"🔜 Próximos 7 dias ({len(df_upcoming)})",
        f"📚 Histórico ({len(df_history)})",
        "⚙️ Estatísticas"
    ])
    
    with tab1:
        st.header("Jogos de Hoje")
        display_games_table(df_today, "Hoje")
    
    with tab2:
        st.header("Próximos 7 Dias")
        display_games_table(df_upcoming, "Próximos 7 dias")
    
    with tab3:
        st.header("Histórico")
        
        # Filtro por data
        datas = sorted(df_history['match_date'].unique(), reverse=True)
        data_selecionada = st.selectbox("Selecione a data:", 
                                        options=datas,
                                        format_func=format_match_date)
        
        df_filtered = df_history[df_history['match_date'] == data_selecionada]
        display_games_table(df_filtered, f"Histórico - {format_match_date(data_selecionada)}")
    
    with tab4:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Jogos", len(df))
        with col2:
            st.metric("Campeonatos", df['league'].nunique())
        with col3:
            pending = len(df[df['status'] == 'PENDING'])
            st.metric("Pendentes", pending)
        
        st.subheader("Distribuição por Status")
        status_dist = df['status'].value_counts()
        st.bar_chart(status_dist)
        
        st.subheader("Odds Médias")
        odds_valid = df[df['odd'] > 0]['odd']
        if not odds_valid.empty:
            st.write(f"Odd Mínima: {odds_valid.min():.2f}")
            st.write(f"Odd Máxima: {odds_valid.max():.2f}")
            st.write(f"Odd Média: {odds_valid.mean():.2f}")

# Refresh automático
if st.button("🔄 Atualizar", use_container_width=True):
    st.rerun()
