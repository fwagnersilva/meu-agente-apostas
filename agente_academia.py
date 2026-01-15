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
            odd REAL,
            status TEXT DEFAULT 'PENDING'
        )
    ''')
    conn.commit()
    conn.close()

def get_previews(page=1):
    url = f"{PREVIEWS_URL}/index/page:{page}" if page > 1 else PREVIEWS_URL
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        for a in soup.select('a[href*="/stats/match/"]'):
            if '/preview' in a['href']:
                full_link = BASE_URL + a['href'] if a['href'].startswith('/') else a['href']
                if full_link not in links:
                    links.append(full_link)
        return links
    except Exception:
        return []

def parse_preview(url):
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Times
        home_team, away_team = "Time A", "Time B"
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text(strip=True).replace("Prognóstico ", "")
            title = re.sub(r'\(.*\)', '', title).strip()
            for sep in [" vs ", " - ", " v "]:
                if sep in title.lower():
                    parts = re.split(sep, title, flags=re.IGNORECASE)
                    home_team, away_team = parts[0].strip(), parts[1].strip()
                    break
        
        if home_team == "Time A":
            url_parts = url.split('/')
            if len(url_parts) >= 8:
                home_team = url_parts[-4].replace('-', ' ').title()
                away_team = url_parts[-3].replace('-', ' ').title()

        # 2. Data
        match_date = "N/A"
        for tag in soup.find_all(['span', 'div', 'p']):
            txt = tag.get_text()
            m = re.search(r'(\d{1,2}\s+\w+\s+\d{4})', txt)
            if m:
                match_date = m.group(1)
                break
        
        # 3. Campeonato
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

        # 4. Prognóstico e Odd
        selection = "Não encontrado"
        odd = 0.0
        editor = soup.find(string=re.compile("Sugestão do editor"))
        if editor:
            container = editor.find_parent(['td', 'div', 'tr', 'p'])
            if container:
                txt = container.get_text(" ", strip=True).replace("Sugestão do editor", "").replace("Pub", "").strip()
                odd_match = re.search(r'Odd\s*(\d+\.\d+)', txt)
                if odd_match:
                    odd = float(odd_match.group(1))
                    selection = txt.split(odd_match.group(0))[0].strip()
                else:
                    decimal_match = re.search(r'(\d+\.\d+)$', txt)
                    if decimal_match:
                        odd = float(decimal_match.group(1))
                        selection = txt.replace(decimal_match.group(1), "").strip()
                    else:
                        selection = txt
        
        if selection == "Não encontrado" or len(selection) < 3:
            box = soup.select_one('.prediction-box, .bet-suggestion')
            if box: selection = box.get_text(strip=True)

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
            "selection": selection,
            "odd": odd,
            "status": status
        }
    except Exception:
        return None

def save(data):
    if not data or "Não encontrado" in data['selection']: return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT OR REPLACE INTO predictions 
            (match_url, date_collected, match_date, league, home_team, away_team, selection, odd, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['match_url'], data['date_collected'], data['match_date'], data['league'], 
              data['home_team'], data['away_team'], data['selection'], data['odd'], data['status']))
        conn.commit()
    finally:
        conn.close()

def main():
    init_db()
    # Coleta 10 páginas para garantir histórico desde o dia 01
    print("🚀 Iniciando coleta profunda de histórico...")
    for p in range(1, 11):
        print(f"📄 Processando página {p}...")
        links = get_previews(page=p)
        if not links: break
        for link in links:
            data = parse_preview(link)
            save(data)
    print("🏁 Coleta finalizada.")

if __name__ == "__main__":
    main()
