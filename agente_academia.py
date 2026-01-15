import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

# --- CONFIGURAÇÃO ---
DB_NAME = "apostas_academia.db"
BASE_URL = "https://www.academiadasapostasbrasil.com"
PREVIEWS_URL = f"{BASE_URL}/previews"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_url TEXT UNIQUE,
            date_collected TEXT,
            match_date_time TEXT, 
            league TEXT,
            home_team TEXT,
            away_team TEXT,
            selection TEXT, 
            odd TEXT,       
            status TEXT DEFAULT 'PENDING',
            score_home INTEGER,
            score_away INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def get_todays_previews():
    print("🔍 Buscando lista de jogos...")
    try:
        response = requests.get(PREVIEWS_URL, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = set()
        for a in soup.select('a[href*="/stats/match/"]'):
            if '/preview' in a['href']:
                full_link = BASE_URL + a['href'] if a['href'].startswith('/') else a['href']
                links.add(full_link)
        print(f"📌 Encontrados {len(links)} links.")
        return list(links)
    except Exception as e:
        print(f"❌ Erro na lista: {e}")
        return []

def parse_preview(url):
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Extrair Times (Lógica Corrigida)
        home_team = "Desconhecido"
        away_team = "Desconhecido"
        
        title_tag = soup.find('h1')
        if title_tag:
            title_text = title_tag.get_text(strip=True).replace("Prognóstico ", "")
            # Remove a data "(14 janeiro 2026)"
            title_text = re.sub(r'\(.*\)', '', title_text).strip()
            
            # Se o título for "Time A vs Time B", separa
            if " vs " in title_text:
                parts = title_text.split(" vs ")
                home_team = parts[0].strip()
                away_team = parts[1].strip()
            else:
                # Tenta pegar de elementos de time se existirem
                teams = soup.select('.team-name, .team-title')
                if len(teams) >= 2:
                    home_team = teams[0].get_text(strip=True)
                    away_team = teams[1].get_text(strip=True)
                else:
                    home_team = title_text

        # 2. Extrair Data/Hora
        date_time = "N/A"
        for tag in soup.find_all(['span', 'div', 'li', 'p']):
            text = tag.get_text()
            match = re.search(r'(\d{1,2}\s+\w+\s+\d{4}\s+-\s+\d{2}:\d{2})', text)
            if match:
                date_time = match.group(1)
                break
        
        # 3. Extrair Liga (Lógica Corrigida)
        league = "Geral"
        # Procura o texto que indica a competição
        # Geralmente está em um span acima do título ou no breadcrumb
        bc = soup.select('.breadcrumbs li')
        if len(bc) >= 4:
            league = bc[3].get_text(strip=True)
        elif len(bc) >= 3:
            league = bc[2].get_text(strip=True)
        
        # Se a liga capturada for igual a um dos times, tenta outra forma
        if league in [home_team, away_team] or "Prognóstico" in league:
            # Tenta pegar o texto do container pai do H1
            h1 = soup.find('h1')
            if h1:
                prev_sibling = h1.find_previous_sibling()
                if prev_sibling:
                    league = prev_sibling.get_text(strip=True)

        # 4. Extrair O PALPITE
        prediction_text = "Não encontrado"
        editor_title = soup.find(string=re.compile("Sugestão do editor"))
        if editor_title:
            container = editor_title.find_parent(['div', 'td', 'tr', 'table'])
            if container:
                # Pega o texto que vem logo após "Sugestão do editor"
                full_text = container.get_text(" ", strip=True)
                if "Sugestão do editor" in full_text:
                    prediction_text = full_text.split("Sugestão do editor")[-1].strip()

        # Limpeza final
        prediction_text = prediction_text.split("Odd")[0].strip()
        if len(prediction_text) < 3 or "atividade de lazer" in prediction_text:
            prediction_text = "Não encontrado"
        
        return {
            "match_url": url,
            "date_collected": datetime.now().strftime("%Y-%m-%d"),
            "match_date_time": date_time,
            "league": league,
            "home_team": home_team,
            "away_team": away_team,
            "prediction": prediction_text,
            "odd": "-"
        }
    except Exception as e:
        print(f"⚠️ Erro ao ler {url}: {e}")
        return None

def save_prediction(data):
    if not data or data['prediction'] == "Não encontrado": return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT OR REPLACE INTO predictions 
            (match_url, date_collected, match_date_time, league, home_team, away_team, selection, odd)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['match_url'], 
            data['date_collected'], 
            data['match_date_time'], 
            data['league'], 
            data['home_team'], 
            data['away_team'], 
            data['prediction'],
            data['odd']
        ))
        conn.commit()
        print(f"✅ Salvo: {data['match_date_time']} | {data['home_team']} x {data['away_team']} | Liga: {data['league']}")
    except Exception as e:
        print(f"❌ Erro banco: {e}")
    finally:
        conn.close()

def main():
    init_db()
    links = get_todays_previews()
    print(f"🚀 Processando {len(links)} jogos...")
    for link in links:
        data = parse_preview(link)
        save_prediction(data)
    print("🏁 Fim.")

if __name__ == "__main__":
    main()
