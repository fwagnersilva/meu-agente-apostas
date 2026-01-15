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
            odd TEXT,       
            status TEXT DEFAULT 'PENDING',
            score_home TEXT,
            score_away TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_previews(page=1):
    """Busca links de prognósticos, permitindo paginação para pegar jogos passados."""
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
        print(f"📌 Encontrados {len(links)} links.")
        return list(links)
    except Exception as e:
        print(f"❌ Erro na lista: {e}")
        return []

def parse_preview(url):
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Extrair Times (Baseado no print: Palmeiras vs Santos)
        home_team = "Desconhecido"
        away_team = "Desconhecido"
        
        # Tenta pegar dos nomes grandes abaixo dos logos
        teams_elements = soup.select('.team-name, .team-title, h1')
        if len(teams_elements) >= 2:
            # Se forem elementos separados
            home_team = teams_elements[0].get_text(strip=True)
            away_team = teams_elements[1].get_text(strip=True)
        
        # Fallback para o H1 se a extração acima falhar ou for o H1
        title_tag = soup.find('h1')
        if title_tag and (home_team == "Desconhecido" or "Prognóstico" in home_team):
            title_text = title_tag.get_text(strip=True).replace("Prognóstico ", "")
            title_text = re.sub(r'\(.*\)', '', title_text).strip()
            for sep in [" vs ", " - ", " v "]:
                if sep in title_text:
                    parts = title_text.split(sep)
                    home_team = parts[0].strip()
                    away_team = parts[1].strip()
                    break

        # 2. Extrair Data/Hora e Campeonato (Baseado no print)
        date_time = "N/A"
        league = "Geral"
        
        # No print, a data e a liga estão centralizadas entre os logos
        # Geralmente em um container com classe 'game-info' ou similar
        info_container = soup.select_one('.game-info, .match-header-info')
        if info_container:
            text = info_container.get_text(" ", strip=True)
            # Data/Hora
            match_dt = re.search(r'(\d{1,2}\s+\w+\s+\d{4}\s+-\s+\d{2}:\d{2})', text)
            if match_dt: date_time = match_dt.group(1)
            
            # Liga (No print aparece logo abaixo da data)
            # Tenta pegar o texto que contém o nome da liga
            lines = [l.strip() for l in info_container.get_text("\n").split("\n") if l.strip()]
            for i, line in enumerate(lines):
                if re.search(r'\d{2}:\d{2}', line) and i + 1 < len(lines):
                    league = lines[i+1]
                    break
        
        # Fallback para Data/Hora se não achou no container
        if date_time == "N/A":
            for tag in soup.find_all(['span', 'div', 'li']):
                match = re.search(r'(\d{1,2}\s+\w+\s+\d{4}\s+-\s+\d{2}:\d{2})', tag.text)
                if match:
                    date_time = match.group(1)
                    break

        # Fallback para Liga via Breadcrumbs
        if league == "Geral" or "2026" in league:
            bc = soup.select('.breadcrumbs li')
            if len(bc) >= 4: league = bc[3].get_text(strip=True)
            elif len(bc) >= 3: league = bc[2].get_text(strip=True)

        # 3. Extrair Placar (Se o jogo já aconteceu ou está rolando)
        score_home = "-"
        score_away = "-"
        score_elements = soup.select('.score, .match-score')
        if score_elements:
            score_text = score_elements[0].get_text(strip=True)
            if "-" in score_text:
                parts = score_text.split("-")
                score_home = parts[0].strip()
                score_away = parts[1].strip()
        else:
            # Tenta achar números isolados que representem o placar
            scores = soup.find_all('span', class_='score')
            if len(scores) >= 2:
                score_home = scores[0].get_text(strip=True)
                score_away = scores[1].get_text(strip=True)

        # 4. Extrair O PALPITE (Sugestão do editor)
        prediction_text = "Não encontrado"
        # Procura o texto "Sugestão do editor" e pega o conteúdo do box
        editor_box = soup.find(string=re.compile("Sugestão do editor"))
        if editor_box:
            # O palpite geralmente está em um <td> ou <div> vizinho/pai
            parent = editor_box.find_parent(['td', 'div', 'tr'])
            if parent:
                # Tenta pegar o texto limpo, removendo o título
                text_content = parent.get_text(" ", strip=True)
                if "Sugestão do editor" in text_content:
                    prediction_text = text_content.split("Sugestão do editor")[-1].strip()
        
        # Fallback para palpite se a lógica acima falhar
        if prediction_text == "Não encontrado" or len(prediction_text) < 3:
            # Procura por boxes com cores específicas (comum no site)
            tips = soup.select('.prediction-box, .bet-suggestion')
            if tips:
                prediction_text = tips[0].get_text(strip=True)

        # Limpeza final
        prediction_text = prediction_text.split("Odd")[0].strip()
        if "atividade de lazer" in prediction_text: prediction_text = "Não encontrado"
        
        return {
            "match_url": url,
            "date_collected": datetime.now().strftime("%Y-%m-%d"),
            "match_date_time": date_time,
            "league": league,
            "home_team": home_team,
            "away_team": away_team,
            "prediction": prediction_text,
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
        # Determina o status baseado no placar
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
        print(f"✅ Salvo: {data['match_date_time']} | {data['home_team']} {data['score_home']}-{data['score_away']} {data['away_team']} | Tip: {data['prediction']}")
    except Exception as e:
        print(f"❌ Erro banco: {e}")
    finally:
        conn.close()

def main():
    init_db()
    # Coleta página 1 (hoje/futuro) e página 2 (passado recente)
    for p in [1, 2]:
        links = get_previews(page=p)
        print(f"🚀 Processando {len(links)} jogos da página {p}...")
        for link in links:
            data = parse_preview(link)
            save_prediction(data)
    print("🏁 Fim.")

if __name__ == "__main__":
    main()
