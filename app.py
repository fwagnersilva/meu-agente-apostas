import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Monitor de Apostas", layout="wide")

def get_db_connection():
    """Conexão com banco de dados (sem cache - thread-safe)."""
    return sqlite3.connect("apostas_academia.db", check_same_thread=False)

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
        conn.close()
        return df
    except Exception as e:
        st.error(f"❌ Erro ao carregar dados: {e}")
        return pd.DataFrame()

def format_match_date(date_str):
    """
    Converte '2026-01-15' para 'quinta, 15 de janeiro'.
    Retorna string amigável.
    """
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        weekday = {
            0: 'segunda', 1: 'terça', 2: 'quarta', 3: 'quinta', 
            4: 'sexta', 5: 'sábado', 6: 'domingo'
        }[dt.weekday()]
        month = {
            1: 'janeiro', 2: 'fevereiro', 3: 'março', 4: 'abril',
            5: 'maio', 6: 'junho', 7: 'julho', 8: 'agosto',
            9: 'setembro', 10: 'outubro', 11: 'novembro', 12: 'dezembro'
        }[dt.month]
        return f"{weekday}, {dt.day} de {month}"
    except:
        return date_str

def format_status(status_str):
    """Formata status para display amigável."""
    if not status_str:
        return "N/A"
    if status_str.upper() == "PENDING":
        return "Pendente ⏳"
    if status_str.upper().startswith("FINISHED"):
        return "Finalizado ✅"
    return "N/A"

def categorize_games(df):
    """
    Separa jogos em 3 categorias:
    - Hoje
    - Próximos 7 dias
    - Histórico (passado)
    """
    today = datetime.now().date()
    today_iso = today.isoformat()
    
    df_today = df[df['match_date'] == today_iso]
    
    next_week_iso = (today + timedelta(days=7)).isoformat()
    df_upcoming = df[
        (df['match_date'] > today_iso) & 
        (df['match_date'] <= next_week_iso)
    ]
    
    df_history = df[df['match_date'] < today_iso]
    
    return df_today, df_upcoming, df_history

def display_games_table(df, title=""):
    """
    Exibe tabela formatada de jogos.
    Recebe DataFrame e exibe no Streamlit.
    """
    if df.empty:
        st.info("Nenhum jogo nesta categoria.")
        return
    
    # Cria cópia para não alterar original
    display_df = df.copy()
    
    # Formata data legível
    display_df['Data'] = display_df['match_date'].apply(format_match_date)
    
    # Monta nome do jogo
    display_df['Jogo'] = display_df['home_team'] + ' vs ' + display_df['away_team']
    
    # Formata odd (mostra 2 casas decimais ou "—" se não tem)
    display_df['Odd Formatada'] = display_df['odd'].apply(
        lambda x: f"{x:.2f}" if x > 0 else "—"
    )
    
    # Formata status
    display_df['Status Formatado'] = display_df['status'].apply(format_status)
    
    # Seleciona colunas para exibição
    cols_to_show = [
        'Data',
        'match_time',
        'league',
        'Jogo',
        'selection',
        'Odd Formatada',
        'Status Formatado'
    ]
    
    # Renomeia para exibição mais clara
    display_df_final = display_df[cols_to_show].rename(columns={
        'match_time': 'Horário',
        'league': 'Campeonato',
        'selection': 'Prognóstico',
        'Status Formatado': 'Status'
    })
    
    # Exibe tabela
    st.dataframe(
        display_df_final,
        hide_index=True,
        use_container_width=True,
        height=400
    )

# ===== INTERFACE PRINCIPAL =====

st.title("📊 Monitor de Apostas Academia")
st.markdown("Dashboard em tempo real com prognósticos de futebol")
st.divider()

# Carrega dados
df = load_data()

if df.empty:
    st.warning(
        "⚠️ Banco de dados vazio.\n\n"
        "Execute o agente para coletar dados: `python agente_academia.py`"
    )
else:
    # Categoriza jogos
    df_today, df_upcoming, df_history = categorize_games(df)
    
    # Cria abas principais
    tab_hoje, tab_proximos, tab_historico, tab_stats = st.tabs([
        f"📅 Hoje ({len(df_today)})",
        f"🔜 Próximos 7 dias ({len(df_upcoming)})",
        f"📚 Histórico ({len(df_history)})",
        f"📈 Estatísticas"
    ])
    
    # ===== ABA 1: HOJE =====
    with tab_hoje:
        st.header("Jogos de Hoje")
        if df_today.empty:
            st.info("Nenhum jogo agendado para hoje.")
        else:
            st.write(f"**{len(df_today)} jogo(s) encontrado(s)**")
            display_games_table(df_today)
    
    # ===== ABA 2: PRÓXIMOS 7 DIAS =====
    with tab_proximos:
        st.header("Próximos 7 Dias")
        if df_upcoming.empty:
            st.info("Nenhum jogo agendado para os próximos 7 dias.")
        else:
            st.write(f"**{len(df_upcoming)} jogo(s) encontrado(s)**")
            display_games_table(df_upcoming)
    
    # ===== ABA 3: HISTÓRICO =====
    with tab_historico:
        st.header("Histórico de Prognósticos")
        
        if df_history.empty:
            st.info("Sem histórico de jogos passados.")
        else:
            # Filtro por data
            datas_unicas = sorted(df_history['match_date'].unique(), reverse=True)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                data_selecionada = st.selectbox(
                    "Selecione a data:",
                    options=datas_unicas,
                    format_func=format_match_date,
                    key="date_select"
                )
            
            # Filtra pela data selecionada
            df_filtered = df_history[df_history['match_date'] == data_selecionada]
            
            with col2:
                st.metric("Total", len(df_filtered))
            
            display_games_table(df_filtered)
    
    # ===== ABA 4: ESTATÍSTICAS =====
    with tab_stats:
        st.header("Estatísticas Gerais")
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Total de Jogos", len(df))
        
        with col2:
            st.metric("🏆 Campeonatos", df['league'].nunique())
        
        with col3:
            pending = len(df[df['status'] == 'PENDING'])
            st.metric("⏳ Pendentes", pending)
        
        with col4:
            finished = len(df[df['status'].str.startswith('FINISHED', na=False)])
            st.metric("✅ Finalizados", finished)
        
        st.divider()
        
        # Gráfico: Distribuição por Status
        st.subheader("Distribuição por Status")
        status_count = df['status'].str.split().str[0].value_counts()
        st.bar_chart(status_count)
        
        st.divider()
        
        # Gráfico: Jogos por Campeonato
        st.subheader("Jogos por Campeonato")
        league_count = df['league'].value_counts()
        st.bar_chart(league_count)
        
        st.divider()
        
        # Estatísticas de Odds
        st.subheader("Análise de Odds")
        odds_valid = df[df['odd'] > 0]['odd']
        
        if not odds_valid.empty:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Mínima", f"{odds_valid.min():.2f}")
            with col2:
                st.metric("Máxima", f"{odds_valid.max():.2f}")
            with col3:
                st.metric("Média", f"{odds_valid.mean():.2f}")
            with col4:
                st.metric("Mediana", f"{odds_valid.median():.2f}")
            
            st.divider()
            
            # Distribuição de Odds
            st.write("Distribuição de Odds (por faixa)")
            hist_data = pd.cut(odds_valid, bins=10).value_counts().sort_index()
            st.bar_chart(hist_data)
        else:
            st.warning("Sem dados de odds para análise.")

# ===== FOOTER E CONTROLES =====
st.divider()

col_refresh, col_info = st.columns([1, 3])

with col_refresh:
    if st.button("🔄 Atualizar", use_container_width=True):
        st.rerun()

with col_info:
    st.caption(
        f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | "
        f"Total de registros: {len(df)}"
    )
