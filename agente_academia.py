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
            match_date TEXT, 
            match_time TEXT,
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
            href = a['href']
            if '/preview' in href:
                full_link = BASE_URL + href if href.startswith('/') else href
                if full_link not in links:
                    links.append(full_link)
        return links
    except Exception as e:
        print(f"Erro na página {page}: {e}")
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
            title = re.sub(r'\(.*?\)', '', title).strip()
            for sep in [" vs ", " - ", " v "]:
                if sep in title.lower():
                    parts = re.split(sep, title, flags=re.IGNORECASE)
                    if len(parts) >= 2:
                        home_team, away_team = parts[0].strip(), parts[1].strip()
                        break
        
        # 2. Data e Hora
        match_date = "N/A"
        match_time = "00:00"
        
        date_pattern = re.compile(r'(\d{1,2})\s+([a-zA-Zç]+)\s+(\d{4})\s*[-–]\s*(\d{2}:\d{2})')
        
        header_area = soup.find('div', class_='stats-match-header') or soup
        for text in header_area.stripped_strings:
            m = date_pattern.search(text)
            if m:
                day, month, year, time = m.groups()
                match_date = f"{year}-{month_to_num(month)}-{day.zfill(2)}"
                match_time = time
                break
        
        # 3. Campeonato
        league = "Geral"
        bc_items = soup.select('.breadcrumbs li')
        if bc_items and len(bc_items) >= 4:
            raw_league = bc_items[-2].get_text(strip=True)
            if " vs " in raw_league: raw_league = bc_items[-3].get_text(strip=True)
            league = raw_league.replace("»", "").strip()

        # 4. Prognóstico e Odd
        selection = "Não encontrado"
        odd = 0.0
        
        editor_box = soup.find(string=re.compile("Sugestão do editor"))
        if editor_box:
            container = editor_box.find_parent(['div', 'td'])
            if container:
                full_text = container.get_text(" ", strip=True).replace("Sugestão do editor", "").replace("Pub", "").strip()
                
                odd_match = re.search(r'Odd\s*(\d+[.,]\d+)', full_text, re.IGNORECASE)
                if odd_match:
                    odd = float(odd_match.group(1).replace(',', '.'))
                    selection = full_text[:odd_match.start()].strip()
                else:
                    dec_match = re.search(r'(\d+[.,]\d+)$', full_text)
                    if dec_match:
                        odd = float(dec_match.group(1).replace(',', '.'))
                        selection = full_text[:dec_match.start()].strip()
                    else:
                        selection = full_text

        if len(selection) < 3 or "atividade de lazer" in selection.lower():
            selection = "Sem prognóstico disponível"

        # 5. Status/Placar - PROTEÇÃO MÁXIMA
        status = "PENDING"
        today = datetime.now()
        is_future_or_today = True
        
        if match_date != "N/A":
            try:
                match_date_obj = datetime.strptime(match_date, "%Y-%m-%d").date()
                today_date = today.date()
                
                if match_date_obj == today_date:
                    try:
                        match_datetime = datetime.strptime(f"{match_date} {match_time}", "%Y-%m-%d %H:%M")
                        if match_datetime > (today - timedelta(hours=2)):
                            is_future_or_today = True
                            status = "PENDING"
                        else:
                            is_future_or_today = False
                    except:
                        is_future_or_today = True
                        status = "PENDING"
                
                elif match_date_obj > today_date:
                    is_future_or_today = True
                    status = "PENDING"
                
                else:
                    is_future_or_today = False
            except:
                is_future_or_today = True
                status = "PENDING"
        
        if not is_future_or_today and match_date != "N/A":
            header = soup.find('div', class_='stats-match-header')
            
            if header:
                for unwanted in header.select('.h2h, .historico, .confrontos, .ultimos-jogos, [class*="history"]'):
                    unwanted.decompose()
                
                score_elem = header.select_one('[class*="result"], [class*="score"], [class*="final"]')
                
                if score_elem:
                    score_text = score_elem.get_text(strip=True)
                    score_match = re.search(r'^([0-9])\s*-\s*([0-9])$', score_text)
                    if score_match:
                        status = f"{score_match.group(1)} - {score_match.group(2)}"
        
        print(f"   📅 {match_date} {match_time} | Futuro/Hoje: {is_future_or_today} | Status: {status}")
        
        return {
            "match_url": url,
            "date_collected": datetime.now().strftime("%Y-%m-%d"),
            "match_date": match_date,
            "match_time": match_time,
            "league": league,
            "home_team": home_team,
            "away_team": away_team,
            "selection": selection,
            "odd": odd,
            "status": status
        }
    except Exception as e:
        print(f"Erro ao processar {url}: {e}")
        return None

def month_to_num(month_name):
    months = {
        'janeiro': '01', 'fevereiro': '02', 'março': '03', 'abril': '04',
        'maio': '05', 'junho': '06', 'julho': '07', 'agosto': '08',
        'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12',
        'jan': '01', 'fev': '02', 'mar': '03', 'abr': '04', 'mai': '05',
        'jun': '06', 'jul': '07', 'ago': '08', 'set': '09', 'out': '10',
        'nov': '11', 'dez': '12'
    }
    return months.get(month_name.lower(), '01')

def save(data):
    if not data: 
        return
    
    # Salva TODOS os jogos, mesmo sem prognóstico claro
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT OR REPLACE INTO predictions 
            (match_url, date_collected, match_date, match_time, league, home_team, away_team, selection, odd, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['match_url'], data['date_collected'], data['match_date'], data['match_time'],
            data['league'], data['home_team'], data['away_team'], data['selection'], data['odd'], data['status']
        ))
        conn.commit()
    except Exception as e:
        print(f"Erro banco: {e}")
    finally:
        conn.close()

def main():
    init_db()
    print("🚀 Iniciando coleta (v5 - Salva Todos os Jogos)...")
    print(f"⏰ Horário atual: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    total_jogos = 0
    for p in range(1, 4):
        links = get_previews(page=p)
        if not links: break
        print(f"\n📄 Página {p}: {len(links)} jogos encontrados")
        
        for link in links:
            data = parse_preview(link)
            if data:
                save(data)
                total_jogos += 1
                print(f"✅ {data['home_team']} x {data['away_team']} -> {data['status']}")
    
    print(f"\n🏁 Finalizado! {total_jogos} jogos salvos no banco.")

if __name__ == "__main__":
    main()
