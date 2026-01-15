
o que ´o perplexy esportes?
Obrigado! Seu feedback ajuda a melhorar as respostas para todos.



O Perplexity Esportes é uma funcionalidade da plataforma Perplexity AI especializada em oferecer respostas atualizadas e precisas sobre eventos, resultados e informações esportivas usando inteligência artificial.
​
​

O que é Perplexity AI
Perplexity AI atua como um mecanismo de busca inteligente, que utiliza modelos avançados de linguagem para entender perguntas do usuário e entregar respostas claras, contextualizadas e com fontes confiáveis. Além de responder perguntas gerais, a ferramenta é capaz de buscar dados em tempo real, o que inclui informações sobre esportes, como resultados de partidas e estatísticas atuais.
​
​

Funcionalidades Esportivas
Entrega resultados de jogos e campeonatos em tempo real.

Responde perguntas objetivas e fornece detalhes das partidas, como líderes e classificação de campeonatos nacionais.

Permite ao usuário pedir atualizações de eventos ou buscar informações esportivas recentes sem precisar navegar por diversos sites.
​

Como utilizar
A função esportiva do Perplexity pode ser acessada diretamente do painel principal ao fazer perguntas sobre esportes (ex: "Quem lidera o Campeonato Brasileiro?"). A resposta é rápida, baseada em fontes confiáveis e apresenta contexto atualizado sobre os eventos esportivos.
​
​

Diferenciais
Respostas precisas e atualizadas sobre o mundo esportivo.

Interface intuitiva, semelhante a um chatbot.

Integração de dados em tempo real com análise de eventos esportivos, além dos recursos gerais de IA e busca inteligente.
​
​

podemos fazer analise preditiva dos jogos de hoje?
Sim, é possível fazer análise preditiva dos jogos de hoje utilizando ferramentas de inteligência artificial que processam dados históricos, estatísticas dos times, desempenho dos jogadores, entre outros fatores relevantes.

Como funciona a análise preditiva em esportes
A análise preditiva utiliza algoritmos que levam em conta informações como resultados passados, condições atuais dos times, lesões, clima, desempenho individual e coletivo para prever o provável resultado dos jogos. Modelos de machine learning e inteligência artificial são comumente empregados para essa tarefa.

Aplicação no Perplexity Esportes
Embora o Perplexity Esportes forneça dados e atualizações em tempo real, a capacidade integral de realizar análises preditivas detalhadas pode depender da integração com bases específicas de dados esportivos e algoritmos preditivos. Em geral, plataformas especializadas em análise esportiva complementam as informações com previsões baseadas em IA.

Considerações práticas
A análise preditiva pode fornecer probabilidades, mas não garante resultados exatos devido à natureza imprevisível dos esportes.

Para previsões mais completas, é recomendado utilizar ferramentas que agregam estatísticas aprofundadas e modelos estatísticos constantes.

Assim, com ferramentas certas, é plenamente possível realizar análises preditivas dos jogos de hoje para fundamentar apostas, estratégias de acompanhamento ou decisões ligadas às competições esportivas.

os jogos que acompanho sçao esses;

image.jpg
Entendido! Os jogos que você acompanha incluem partidas do Brasileirão Betano, Liga dos Campeões da UEFA e Primera División do Paraguai, conforme a lista da imagem enviada.
​

Jogos acompanhados hoje
Brasileirão Betano (Brasil)

RB Bragantino vs Fortaleza

Liga dos Campeões da UEFA (Europa)

Arsenal vs Bayern

Atlético Madrid vs Inter

Liverpool vs PSV

Olympiacos vs Real Madrid

PSG vs Tottenham

Sporting vs Club Brugge

Primera División, Clausura (Paraguai)

Sportivo Ameliano vs Trinidense

Olimpia vs 2 de Mayo

Esses jogos têm odds indicadas na imagem, úteis para análise preditiva e acompanhamento das probabilidades. Se quiser previsões específicas para cada partida ou análise das probabilidades, basta solicitar!
​

paste.txt

2 anexos
Principais correções:

Versão Antiga	v6 FINAL
Procura <h1> (não existe)	Procura <h3 class="preview_title"> ✅
Busca por "Sugestão do editor" (errado)	Busca <div class="preview_bet"> ✅
Extrai "Sem prognóstico"	Extrai real "Mais de 2,5 gols" ✅
Times "Time A" e "Time B"	Times reais "Tigres" e "Pumas" ✅
Regex de data fraca	Regex forte para "15 janeiro 2026" ✅
Sem tratamento de duplicatas	Remove duplicatas de página ✅
Substitua seu agente_academia.py pelo agente_academia_v6_final.py e rode de novo.

mande o arquivo
agente_v6.py
Arquivo gerado · v1

✅ Arquivo criado!

Como usar:

Vá ao seu repositório GitHub

Substitua o arquivo agente_academia.py pelo agente_v6.py (ou copie o conteúdo)

Faça commit e push

Deixe o GitHub Actions rodar

Pronto! Agora os times, prognósticos e odds vão sair corretos do site. 👊

❌ Erro ao carregar dados: SQLite objects created in a thread can only be used in that same thread. The object was created in thread id 134656183744192 and this is thread id 134654951749312.
app.py
Arquivo gerado · v2

✅ Arquivo corrigido!

Mudanças principais:

python
# ❌ ANTES (erro de thread)
@st.cache_resource
def get_db_connection():
    return sqlite3.connect("apostas_academia.db")

# ✅ AGORA (thread-safe)
def get_db_connection():
    return sqlite3.connect("apostas_academia.db", check_same_thread=False)
Por quê?

SQLite é single-threaded por padrão

Streamlit roda com múltiplas threads

@st.cache_resource mantém a conexão em cache entre requisições (threads diferentes)

check_same_thread=False permite usar a conexão em qualquer thread

Agora abre e fecha a conexão em cada requisição (thread-safe ✅)

Substitua seu app.py com este novo e tente de novo!




app.py
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
    
    # Seleciona colunas para exibição
    cols_to_show = [
        'Data',
        'match_time',
        'league',
        'Jogo',
        'selection',
        'Odd Formatada',
        'status'
    ]
    
    # Renomeia para exibição mais clara
    display_df_final = display_df[cols_to_show].rename(columns={
        'match_time': 'Horário',
        'league': 'Campeonato',
        'selection': 'Prognóstico',
        'status': 'Status'
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
        status_count = df['status'].str.split().str[0].value_counts()  # Pega primeiro palavra (PENDING/FINISHED)
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
            
            # Histograma de Odds
            st.write("Distribuição de Odds")
            st.histogram(odds_valid, nbins=20, key="odds_hist")
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
