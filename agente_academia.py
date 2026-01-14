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
            match_date_time TEXT, -- Data e Hora real do jogo
            league TEXT,
            home_team TEXT,
            away_team TEXT,
            selection TEXT, -- O Palpite
            odd TEXT,       -- A Odd (se achar)
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
        # Pega todos os links que parecem ser de preview de jogo
        for a in soup.find_all('a', href=True):
            if '/stats/match/' in a['href'] and '/preview' in a['href']:
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
        
        # 1. Extrair Times e Data (Geralmente no topo)
        title_tag = soup.find('h1')
        title = title_tag.text.strip().replace("Prognóstico ", "") if title_tag else "Desconhecido"
        
        # Tenta achar a data/hora específica (ex: 14 janeiro 2026 - 19:30)
        # Geralmente está num span ou div de info do jogo
        date_time = "N/A"
        date_element = soup.find('span', class_='date') # Tentativa genérica
        if not date_element:
            # Procura por padrão de data no texto visível
            for tag in soup.find_all(['span', 'div', 'li']):
                if re.search(r'\d{1,2}\s+\w+\s+\d{4}\s+-\s+\d{2}:\d{2}', tag.text):
                    date_time = re.search(r'\d{1,2}\s+\w+\s+\d{4}\s+-\s+\d{2}:\d{2}', tag.text).group(0)
                    break
        
        # 2. Extrair Liga
        league = "Geral"
        # Tenta pegar dos breadcrumbs (caminho no topo da pag)
        breadcrumbs = soup.find_all('ul', class_='breadcrumbs')
        if breadcrumbs:
            items = breadcrumbs[0].find_all('li')
            if len(items) > 2:
                league = items[2].text.strip() # Geralmente a liga é o 3º item

        # 3. Extrair O PALPITE (O Pulo do Gato)
        prediction_text = "Não encontrado"
        odd_text = "-"
        
        # Estratégia A: Procurar título "Sugestão do editor" (como no seu print)
        editor_title = soup.find(string=re.compile("Sugestão do editor"))
        if editor_title:
            # Geralmente o palpite está num container próximo
            container = editor_title.find_parent('div') or editor_title.find_parent('td')
            if container:
                # Procura o próximo texto relevante
                next_div = container.find_next_sibling('div')
                if next_div:
                    prediction_text = next_div.text.strip()
                else:
                    # Tenta pegar dentro do próprio container se for uma tabela
                    prediction_text = container.get_text(strip=True).replace("Sugestão do editor", "")

        # Estratégia B: Se falhar, procura classes comuns de boxes de aposta
        if len(prediction_text) < 3 or "atividade de lazer" in prediction_text:
            bet_box = soup.find('div', class_='prediction-box') or soup.find('p', class_='prediction')
            if bet_box:
                prediction_text = bet_box.text.strip()

        # Limpeza final do texto
        prediction_text = prediction_text.split("Odd")[0].strip() # Remove a parte da Odd se vier colada
        
        return {
            "match_url": url,
            "date_collected": datetime.now().strftime("%Y-%m-%d"),
            "match_date_time": date_time,
            "league": league,
            "teams": title,
            "prediction": prediction_text,
            "odd": odd_text
        }
    except Exception as e:
        print(f"⚠️ Erro ao ler {url}: {e}")
        return None

def save_prediction(data):
    if not data: return
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        teams = data['teams'].split(' vs ')
        home = teams[0] if len(teams) > 0 else data['teams']
        away = teams[1] if len(teams) > 1 else '?'

        # Só salva se o palpite for válido (evita texto jurídico)
        if "atividade de lazer" in data['prediction']:
            print(f"⚠️ Ignorado (Palpite inválido): {home} x {away}")
            return

        c.execute('''
            INSERT OR REPLACE INTO predictions 
            (match_url, date_collected, match_date_time, league, home_team, away_team, selection, odd)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['match_url'], 
            data['date_collected'], 
            data['match_date_time'], 
            data['league'], 
            home, 
            away, 
            data['prediction'],
            data['odd']
        ))
        conn.commit()
        print(f"✅ Salvo: {data['match_date_time']} | {home} x {away} | Tip: {data['prediction']}")
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
