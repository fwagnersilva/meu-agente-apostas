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
            match_date TEXT, 
            league TEXT,
            home_team TEXT,
            away_team TEXT,
            selection TEXT, 
            status TEXT DEFAULT 'PENDING'
        )
    ''')
    conn.commit()
    conn.close()

def get_previews():
    try:
        response = requests.get(PREVIEWS_URL, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        for a in soup.select('a[href*="/stats/match/"]'):
            if '/preview' in a['href']:
                full_link = BASE_URL + a['href'] if a['href'].startswith('/') else a['href']
                if full_link not in links:
                    links.append(full_link)
        return links
    except Exception as e:
        return []

def parse_preview(url):
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Extrair Times
        home_team = "Time A"
        away_team = "Time B"
        url_parts = url.split('/')
        if len(url_parts) >= 8:
            home_team = url_parts[-4].replace('-', ' ').title()
            away_team = url_parts[-3].replace('-', ' ').title()
        
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text(strip=True).replace("Prognóstico ", "")
            title = re.sub(r'\(.*\)', '', title).strip()
            for sep in [" vs ", " - ", " v "]:
                if sep in title.lower():
                    parts = re.split(sep, title, flags=re.IGNORECASE)
                    home_team, away_team = parts[0].strip(), parts[1].strip()
                    break

        # 2. Extrair Data
        match_date = "N/A"
        for tag in soup.find_all(['span', 'div', 'p']):
            txt = tag.get_text()
            m = re.search(r'(\d{1,2}\s+\w+\s+\d{4})', txt)
            if m:
                match_date = m.group(1)
                break
        
        # 3. Extrair Campeonato
        league = "Geral"
        bc = soup.select('.breadcrumbs li')
        if len(bc) >= 4:
            liga_raw = bc[3].get_text(strip=True).replace("»", "").strip()
            if " vs " in liga_raw.lower() or " - " in liga_raw:
                league = bc[2].get_text(strip=True).replace("»", "").strip()
            else:
                league = liga_raw
        elif len(bc) >= 3:
            league = bc[2].get_text(strip=True).replace("»", "").strip()

        # 4. Extrair Palpite (Limpeza Final)
        prediction = "Não encontrado"
        editor = soup.find(string=re.compile("Sugestão do editor"))
        if editor:
            container = editor.find_parent(['td', 'div', 'tr', 'p'])
            if container:
                txt = container.get_text(" ", strip=True)
                # Remove prefixos e sufixos conhecidos
                txt = txt.replace("Sugestão do editor", "").replace("Pub", "").strip()
                txt = txt.split("Aposte aqui")[0].split("As odds podem")[0].strip()
                
                # Regex para pegar a Dica e a Odd
                # Ex: "Menos de 2,5 gols Odd 1.75"
                match = re.search(r'^(.*?)(Odd\s*\d+\.\d+)', txt)
                if match:
                    prediction = f"{match.group(1).strip()} {match.group(2).strip()}"
                else:
                    prediction = txt
        
        if prediction == "Não encontrado" or len(prediction) < 5:
            box = soup.select_one('.prediction-box, .bet-suggestion')
            if box: prediction = box.get_text(strip=True)

        # 5. Status
        status = "PENDING"
        score_tag = soup.select_one('.match-score, .score')
        if score_tag:
            s_txt = score_tag.get_text(strip=True)
            if "-" in s_txt and len(s_txt) < 10:
                status = s_txt

        return {
            "match_url": url,
            "date_collected": datetime.now().strftime("%Y-%m-%d"),
            "match_date": match_date,
            "league": league,
            "home_team": home_team,
            "away_team": away_team,
            "prediction": prediction,
            "status": status
        }
    except Exception as e:
        return None

def save(data):
    if not data or "Não encontrado" in data['prediction']: return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT OR REPLACE INTO predictions 
            (match_url, date_collected, match_date, league, home_team, away_team, selection, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['match_url'], data['date_collected'], data['match_date'], data['league'], 
              data['home_team'], data['away_team'], data['prediction'], data['status']))
        conn.commit()
        print(f"✅ {data['league']} | {data['home_team']} X {data['away_team']} | {data['prediction']}")
    finally:
        conn.close()

def main():
    init_db()
    links = get_previews()
    for link in links:
        data = parse_preview(link)
        save(data)

if __name__ == "__main__":
    main()
