import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
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
            status TEXT DEFAULT 'PENDING',
            score_home TEXT,
            score_away TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_previews(page=1):
    url = f"{PREVIEWS_URL}/index/page:{page}" if page > 1 else PREVIEWS_URL
    print(f"🔍 Buscando lista de jogos (Página {page})...")
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = set()
        for a in soup.select('a[href*="/stats/match/"]'):
            if '/preview' in a['href']:
                full_link = BASE_URL + a['href'] if a['href'].startswith('/') else a['href']
                links.add(full_link)
        return list(links)
    except Exception as e:
        print(f"❌ Erro na lista: {e}")
        return []

def parse_preview(url):
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Extrair Times (Lógica baseada no print)
        home_team = "Desconhecido"
        away_team = "Desconhecido"
        
        # Tenta pegar dos elementos que contêm os nomes dos times (geralmente perto dos logos)
        # No print, os nomes estão em destaque abaixo dos logos
        team_links = soup.select('.team-name a, .match-header .team-name')
        if len(team_links) >= 2:
            home_team = team_links[0].get_text(strip=True)
            away_team = team_links[1].get_text(strip=True)
        else:
            # Fallback: Título H1
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text(strip=True).replace("Prognóstico ", "")
                title = re.sub(r'\(.*\)', '', title).strip()
                if " vs " in title:
                    home_team, away_team = title.split(" vs ")[:2]
                elif " - " in title:
                    home_team, away_team = title.split(" - ")[:2]

        # 2. Extrair Data/Hora e Campeonato
        date_time = "N/A"
        league = "Geral"
        
        # Procura o bloco central de informações
        info_block = soup.select_one('.match-header-info, .game-info')
        if info_block:
            text = info_block.get_text(" ", strip=True)
            dt_match = re.search(r'(\d{1,2}\s+\w+\s+\d{4}\s+-\s+\d{2}:\d{2})', text)
            if dt_match: date_time = dt_match.group(1)
            
            # Liga: geralmente é o texto logo após a data ou em um span específico
            # No print aparece "Paulista A1" logo abaixo da data
            lines = [l.strip() for l in info_block.get_text("\n").split("\n") if l.strip()]
            for i, line in enumerate(lines):
                if re.search(r'\d{2}:\d{2}', line) and i + 1 < len(lines):
                    league = lines[i+1]
                    break

        # 3. Extrair Placar
        score_home = "-"
        score_away = "-"
        # Procura por elementos de placar (geralmente grandes números no centro)
        scores = soup.select('.match-score .score, .score-home, .score-away')
        if len(scores) >= 2:
            score_home = scores[0].get_text(strip=True)
            score_away = scores[1].get_text(strip=True)
        else:
            # Tenta achar o placar no formato "1 - 0"
            score_full = soup.select_one('.match-score, .score')
            if score_full:
                txt = score_full.get_text(strip=True)
                if "-" in txt and len(txt) < 10:
                    parts = txt.split("-")
                    score_home, score_away = parts[0].strip(), parts[1].strip()

        # 4. Extrair O PALPITE (Sugestão do editor)
        prediction_text = "Não encontrado"
        # Procura especificamente pela caixa de sugestão
        editor_label = soup.find(string=re.compile("Sugestão do editor"))
        if editor_label:
            # Sobe para o container e busca o texto da aposta
            container = editor_label.find_parent(['td', 'div', 'tr'])
            if container:
                # Pega todos os textos e filtra o que não é o título nem "Pub"
                parts = [p.strip() for p in container.get_text("|", strip=True).split("|")]
                for p in parts:
                    if p and "Sugestão do editor" not in p and "Pub" not in p and len(p) > 3:
                        prediction_text = p
                        break

        return {
            "match_url": url,
            "date_collected": datetime.now().strftime("%Y-%m-%d"),
            "match_date_time": date_time,
            "league": league,
            "home_team": home_team.strip(),
            "away_team": away_team.strip(),
            "prediction": prediction_text.strip(),
            "score_home": score_home,
            "score_away": score_away
        }
    except Exception as e:
        print(f"⚠️ Erro ao ler {url}: {e}")
        return None

def save_prediction(data):
    if not data or data['prediction'] == "Não encontrado": return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        status = "PENDING"
        if data['score_home'] != "-" and data['score_away'] != "-":
            status = f"{data['score_home']} - {data['score_away']}"

        c.execute('''
            INSERT OR REPLACE INTO predictions 
            (match_url, date_collected, match_date_time, league, home_team, away_team, selection, status, score_home, score_away)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['match_url'], 
            data['date_collected'], 
            data['match_date_time'], 
            data['league'], 
            data['home_team'], 
            data['away_team'], 
            data['prediction'],
            status,
            data['score_home'],
            data['score_away']
        ))
        conn.commit()
        print(f"✅ {data['match_date_time']} | {data['home_team']} {data['score_home']}-{data['score_away']} {data['away_team']} | Tip: {data['prediction']}")
    except Exception as e:
        print(f"❌ Erro banco: {e}")
    finally:
        conn.close()

def main():
    init_db()
    for p in [1, 2]:
        links = get_previews(page=p)
        print(f"🚀 Processando {len(links)} jogos da página {p}...")
        for link in links:
            data = parse_preview(link)
            save_prediction(data)
    print("🏁 Fim.")

if __name__ == "__main__":
    main()
