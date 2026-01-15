"""
AGENTE DE COLETA - Academia das Apostas Brasil (v6 FINAL)
Estrutura corrigida conforme HTML real do site
"""

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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def init_db():
    """Inicializa banco de dados."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_url TEXT UNIQUE NOT NULL,
            date_collected TEXT NOT NULL,
            match_date TEXT NOT NULL,
            match_time TEXT NOT NULL,
            league TEXT NOT NULL,
            home_team TEXT NOT NULL,
            away_team TEXT NOT NULL,
            selection TEXT,
            odd REAL DEFAULT 0.0,
            status TEXT DEFAULT 'PENDING',
            UNIQUE(match_date, match_time, home_team, away_team)
        )
    ''')
    conn.commit()
    conn.close()

def get_previews(page=1):
    """Coleta links de préviews."""
    url = f"{PREVIEWS_URL}/index/page:{page}" if page > 1 else PREVIEWS_URL
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = []
        for a in soup.select('a[href*="/stats/match/"]'):
            href = a.get('href', '')
            if '/preview' in href:
                full_link = BASE_URL + href if href.startswith('/') else href
                links.append(full_link)
        
        return list(set(links))  # Remove duplicatas
    except Exception as e:
        print(f"❌ Erro página {page}: {e}")
        return []

def extract_teams(soup):
    """
    Extrai times do HTML.
    Procura em: <h3 class="preview_title">Análise Tigres</h3>
    """
    home_team = "Time A"
    away_team = "Time B"
    
    try:
        # Procura por títulos com "Análise"
        titles = soup.find_all('h3', class_='preview_title')
        teams_found = []
        
        for title in titles:
            text = title.get_text(strip=True)
            if 'Análise' in text:
                # "Análise Tigres" -> "Tigres"
                team = text.replace('Análise', '').strip()
                if team:
                    teams_found.append(team)
        
        if len(teams_found) >= 2:
            home_team, away_team = teams_found[0], teams_found[1]
    except:
        pass
    
    return home_team, away_team

def extract_date_time(soup, raw_html):
    """
    Extrai data e hora do HTML.
    Padrão: "15 janeiro 2026" ou "15 janeiro 2026 - 20:00"
    """
    match_date = "N/A"
    match_time = "00:00"
    
    try:
        # Regex para "DD mês YYYY" ou "DD mês YYYY - HH:MM"
        pattern = r'(\d{1,2})\s+([a-záéíóúãõç]+)\s+(\d{4})\s*(?:-\s*(\d{1,2}):(\d{2}))?'
        
        months = {
            'janeiro': '01', 'fevereiro': '02', 'março': '03', 'abril': '04',
            'maio': '05', 'junho': '06', 'julho': '07', 'agosto': '08',
            'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12'
        }
        
        match = re.search(pattern, raw_html, re.IGNORECASE)
        if match:
            day, month_name, year = match.group(1), match.group(2), match.group(3)
            hour, minute = match.group(4), match.group(5)
            
            month = months.get(month_name.lower(), '01')
            match_date = f"{year}-{month}-{day.zfill(2)}"
            
            if hour and minute:
                match_time = f"{hour.zfill(2)}:{minute}"
    except:
        pass
    
    return match_date, match_time

def extract_league(soup):
    """Extrai campeonato do breadcrumb."""
    league = "Geral"
    
    try:
        # Procura por breadcrumb
        bc = soup.find(class_='breadcrumbs') or soup.find(class_='breadcrumb')
        if bc:
            items = bc.find_all('li')
            if len(items) >= 3:
                league = items[-2].get_text(strip=True).replace("»", "").strip()
                if not league or "vs" in league.lower():
                    league = items[-3].get_text(strip=True).replace("»", "").strip()
    except:
        pass
    
    return league if league else "Geral"

def extract_prediction(soup):
    """
    Extrai prognóstico e odd.
    HTML: 
    <div class="preview_bet">
      <p>Mais de 2,5 gols</p>
      <p class="preview_odd">Odd 1.90</p>
    </div>
    """
    selection = "Sem prognóstico"
    odd = 0.0
    
    try:
        # Procura pela div preview_bet
        bet_div = soup.find(class_='preview_bet')
        if bet_div:
            # Primeiro <p> é o prognóstico
            p_tags = bet_div.find_all('p')
            if p_tags:
                selection = p_tags[0].get_text(strip=True)
                
                # Procura odd em "Odd X.XX"
                if len(p_tags) > 1:
                    odd_text = p_tags[1].get_text(strip=True)
                    odd_match = re.search(r'Odd\s*(\d+[.,]\d+)', odd_text, re.IGNORECASE)
                    if odd_match:
                        odd = float(odd_match.group(1).replace(',', '.'))
    except:
        pass
    
    return selection if selection != "Sem prognóstico" else "Sem prognóstico", odd

def get_match_status(soup, match_date, match_time):
    """
    Determina status: PENDING ou FINISHED X-Y
    """
    if match_date == "N/A":
        return "UNKNOWN"
    
    try:
        match_dt = datetime.strptime(f"{match_date} {match_time}", "%Y-%m-%d %H:%M")
        now = datetime.now()
        
        # Se jogo é no futuro = PENDING
        if match_dt > now:
            return "PENDING"
        
        # Se passou 2h = busca placar
        if (now - match_dt).total_seconds() > 7200:
            # Procura por elemento com resultado (não implementado no HTML atual)
            return "UNKNOWN"
    except:
        pass
    
    return "UNKNOWN"

def parse_preview(url):
    """Parse completo de uma página de prévia."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        html_str = response.text
        
        # Extração em ordem
        home_team, away_team = extract_teams(soup)
        match_date, match_time = extract_date_time(soup, html_str)
        league = extract_league(soup)
        selection, odd = extract_prediction(soup)
        status = get_match_status(soup, match_date, match_time)
        
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
        print(f"❌ Erro em {url}: {e}")
        return None

def save(data):
    """Salva previsão no banco."""
    if not data:
        return False
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT OR REPLACE INTO predictions 
            (match_url, date_collected, match_date, match_time, league, 
             home_team, away_team, selection, odd, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['match_url'], data['date_collected'], data['match_date'],
            data['match_time'], data['league'], data['home_team'],
            data['away_team'], data['selection'], data['odd'], data['status']
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Duplicado
    except Exception as e:
        print(f"❌ Erro BD: {e}")
        return False
    finally:
        conn.close()

def main():
    init_db()
    print("🚀 Iniciando coleta (v6 FINAL)...")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    total = 0
    for page in range(1, 4):
        links = get_previews(page=page)
        if not links:
            print(f"📄 Página {page}: Fim da coleta")
            break
        
        print(f"📄 Página {page}: {len(links)} previews")
        
        for link in links:
            data = parse_preview(link)
            if data and save(data):
                total += 1
                print(f"  ✅ {data['home_team']:20} vs {data['away_team']:20} | {data['status']}")
    
    print(f"\n✨ Total salvo: {total} jogos")

if __name__ == "__main__":
    main()
