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
            status TEXT DEFAULT 'PENDING',
            score_home TEXT,
            score_away TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_previews():
    print("🔍 Buscando lista de jogos...")
    try:
        response = requests.get(PREVIEWS_URL, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        # Pega os links de preview na página inicial de previews
        for a in soup.select('a[href*="/stats/match/"]'):
            if '/preview' in a['href']:
                full_link = BASE_URL + a['href'] if a['href'].startswith('/') else a['href']
                if full_link not in links:
                    links.append(full_link)
        print(f"📌 Encontrados {len(links)} links.")
        return links
    except Exception as e:
        print(f"❌ Erro na lista: {e}")
        return []

def parse_preview(url):
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Times
        title = soup.find('h1').get_text(strip=True).replace("Prognóstico ", "") if soup.find('h1') else "Jogo"
        title = re.sub(r'\(.*\)', '', title).strip()
        home, away = "Time A", "Time B"
        if " vs " in title:
            home, away = title.split(" vs ")[:2]
        elif " - " in title:
            home, away = title.split(" - ")[:2]
        else:
            home = title

        # 2. Data e Liga
        date_time = datetime.now().strftime("%d %B %Y - %H:%M")
        league = "Geral"
        
        # Tenta achar a data real no texto
        for tag in soup.find_all(['span', 'div', 'p']):
            txt = tag.get_text()
            m = re.search(r'(\d{1,2}\s+\w+\s+\d{4}\s+-\s+\d{2}:\d{2})', txt)
            if m:
                date_time = m.group(1)
                break
        
        # Tenta achar a liga nos breadcrumbs
        bc = soup.select('.breadcrumbs li')
        if len(bc) >= 3:
            league = bc[2].get_text(strip=True)
            if len(bc) >= 4 and "Prognóstico" not in bc[3].get_text():
                league = bc[3].get_text(strip=True)

        # 3. Palpite (Sugestão do editor)
        prediction = "Não encontrado"
        editor = soup.find(string=re.compile("Sugestão do editor"))
        if editor:
            container = editor.find_parent(['td', 'div', 'tr', 'p'])
            if container:
                txt = container.get_text(" ", strip=True)
                if "Sugestão do editor" in txt:
                    prediction = txt.split("Sugestão do editor")[-1].strip()
        
        # Fallback palpite
        if prediction == "Não encontrado" or len(prediction) < 3:
            box = soup.select_one('.prediction-box, .bet-suggestion')
            if box: prediction = box.get_text(strip=True)

        # 4. Placar
        score = "PENDING"
        score_tag = soup.select_one('.match-score, .score')
        if score_tag:
            s_txt = score_tag.get_text(strip=True)
            if "-" in s_txt and len(s_txt) < 10:
                score = s_txt

        return {
            "match_url": url,
            "date_collected": datetime.now().strftime("%Y-%m-%d"),
            "match_date_time": date_time,
            "league": league,
            "home_team": home,
            "away_team": away,
            "prediction": prediction,
            "status": score
        }
    except Exception as e:
        print(f"⚠️ Erro em {url}: {e}")
        return None

def save(data):
    if not data or data['prediction'] == "Não encontrado": return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT OR REPLACE INTO predictions 
            (match_url, date_collected, match_date_time, league, home_team, away_team, selection, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['match_url'], data['date_collected'], data['match_date_time'], data['league'], 
              data['home_team'], data['away_team'], data['prediction'], data['status']))
        conn.commit()
        print(f"✅ {data['home_team']} vs {data['away_team']} - {data['prediction']}")
    finally:
        conn.close()

def main():
    init_db()
    links = get_previews()
    for link in links[:15]: # Limita a 15 para ser rápido
        data = parse_preview(link)
        save(data)

if __name__ == "__main__":
    main()
