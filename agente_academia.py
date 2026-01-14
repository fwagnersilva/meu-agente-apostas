import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

# --- CONFIGURAÇÃO ---
DB_NAME = "apostas_academia.db"
BASE_URL = "https://www.academiadasapostasbrasil.com"
PREVIEWS_URL = f"{BASE_URL}/previews"

# Cabeçalhos para simular navegador real (evita bloqueio simples)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def init_db():
    """Cria a estrutura do banco de dados se não existir."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Tabela de Prognósticos
    c.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_url TEXT UNIQUE,
            date_collected TEXT,
            match_date TEXT,
            league TEXT,
            home_team TEXT,
            away_team TEXT,
            market TEXT,
            selection TEXT,
            status TEXT DEFAULT 'PENDING', -- PENDING, WON, LOST, VOID
            score_home INTEGER,
            score_away INTEGER
        )
    ''')
    conn.commit()
    conn.close()
    print(f"✅ Banco de dados '{DB_NAME}' verificado.")

def get_todays_previews():
    """Coleta os links dos prognósticos do dia."""
    print("🔍 Buscando prognósticos do dia...")
    try:
        response = requests.get(PREVIEWS_URL, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Encontra links de preview (ajuste o seletor conforme necessario)
        # O site usa estrutura de tabela ou lista para previews. 
        # Vou usar uma busca genérica por links que contêm '/preview'
        links = set()
        for a in soup.find_all('a', href=True):
            if '/preview' in a['href'] and '/stats/match/' in a['href']:
                links.add(BASE_URL + a['href'] if a['href'].startswith('/') else a['href'])
        
        print(f"📌 Encontrados {len(links)} prognósticos potenciais.")
        return list(links)
    except Exception as e:
        print(f"❌ Erro ao buscar lista: {e}")
        return []

def parse_preview(url):
    """Extrai os dados de um prognóstico individual."""
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extração de Times e Liga (Simplificada - precisa adaptar ao HTML real se mudar)
        title = soup.find('h1').text.strip() if soup.find('h1') else "Desconhecido"
        # Ex: "Prognóstico Flamengo vs Fluminense"
        
        # Extração da Dica (Geralmente em destaque ou última frase do texto)
        # O site costuma ter uma caixa "Aposta sugerida" ou texto final.
        # Aqui vou usar uma lógica para pegar o último parágrafo de conclusão.
        content_div = soup.find('div', class_='preview-content') # Classe hipotética
        if not content_div:
            content_div = soup.find('div', {'class': 'content'}) # Tenta genérico
            
        prediction_text = "N/A"
        # Tenta achar a caixa de aposta se existir
        bet_box = soup.find('div', class_='bet-box') # Hipotético
        if bet_box:
            prediction_text = bet_box.text.strip()
        else:
            # Fallback: pega parágrafos e procura palavras chave de aposta
            paragraphs = soup.find_all('p')
            if paragraphs:
                prediction_text = paragraphs[-1].text.strip()

        # Retorna dicionário
        return {
            "match_url": url,
            "date_collected": datetime.now().strftime("%Y-%m-%d"),
            "match_date": datetime.now().strftime("%Y-%m-%d"), # Ideal: extrair do HTML
            "league": "Geral", # Ideal: extrair do HTML breadcrumbs
            "teams": title.replace("Prognóstico ", ""),
            "prediction": prediction_text
        }
    except Exception as e:
        print(f"⚠️ Erro ao ler {url}: {e}")
        return None

def save_prediction(data):
    """Salva no banco de dados."""
    if not data: return
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        # Separa times (exemplo simples)
        teams = data['teams'].split(' vs ')
        home = teams[0] if len(teams) > 0 else data['teams']
        away = teams[1] if len(teams) > 1 else '?'

        c.execute('''
            INSERT OR IGNORE INTO predictions 
            (match_url, date_collected, match_date, league, home_team, away_team, market, selection)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['match_url'], 
            data['date_collected'], 
            data['match_date'], 
            data['league'], 
            home, 
            away, 
            "Analise Texto", # Mercado exato exige NLP ou parser complexo
            data['prediction']
        ))
        conn.commit()
        if c.rowcount > 0:
            print(f"✅ Salvo: {home} x {away}")
        else:
            print(f"zzz Já existe: {home} x {away}")
    except Exception as e:
        print(f"❌ Erro ao salvar banco: {e}")
    finally:
        conn.close()

def main():
    init_db()
    links = get_todays_previews()
    
    print(f"🚀 Iniciando coleta de {len(links)} jogos...")
    for link in links:
        data = parse_preview(link)
        save_prediction(data)
    
    print("🏁 Processo finalizado.")

if __name__ == "__main__":
    main()
