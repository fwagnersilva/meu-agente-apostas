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
    # Adicionada coluna match_time separada para facilitar ordenação
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
        # Seleção mais robusta para pegar apenas previews de jogo
        for a in soup.select('a[href*="/stats/match/"]'):
            href = a['href']
            # Filtra links que são realmente de preview
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
        
        # 1. Times (Extração via Título H1 + Fallback URL)
        home_team, away_team = "Time A", "Time B"
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text(strip=True).replace("Prognóstico ", "")
            # Remove parênteses (ex: (W))
            title = re.sub(r'\(.*?\)', '', title).strip()
            # Tenta separadores comuns
            separators = [" vs ", " - ", " v "]
            for sep in separators:
                if sep in title.lower():
                    parts = re.split(sep, title, flags=re.IGNORECASE)
                    if len(parts) >= 2:
                        home_team, away_team = parts[0].strip(), parts[1].strip()
                        break
        
        # Fallback para URL se o H1 falhar
        if home_team == "Time A":
            url_parts = url.split('/')
            # URL típica: .../stats/match/pais/liga/home/away/...
            try:
                # Procura onde está 'match' e pega os indices relativos
                match_idx = url_parts.index('match')
                if len(url_parts) > match_idx + 4:
                    home_team = url_parts[match_idx + 3].replace('-', ' ').title()
                    away_team = url_parts[match_idx + 4].replace('-', ' ').title()
            except:
                pass

        # 2. Data e Hora (Melhorado)
        match_date = "N/A"
        match_time = "00:00"
        
        # Estratégia A: Busca específica no bloco de info do jogo (geralmente data centralizada)
        # O site costuma por a data num texto solto perto dos escudos ou breadcrumbs
        # Formato esperado: "14 janeiro 2026 - 19:30"
        
        # Procura por texto que combine com o padrão de data
        date_pattern = re.compile(r'(\d{1,2})\s+([a-zA-Zç]+)\s+(\d{4})\s*[-–]\s*(\d{2}:\d{2})')
        
        found_date = False
        # Varre divs e spans do topo da página (header)
        header_area = soup.find('div', class_='stats-match-header') or soup.find('div', id='header') or soup
        
        for text in header_area.stripped_strings:
            m = date_pattern.search(text)
            if m:
                day, month, year, time = m.groups()
                match_date = f"{year}-{month_to_num(month)}-{day.zfill(2)}"
                match_time = time
                found_date = True
                break
        
        if not found_date:
            # Fallback: tenta pegar só a data se não tiver hora
            date_pattern_simple = re.compile(r'(\d{1,2})\s+([a-zA-Zç]+)\s+(\d{4})')
            for text in soup.stripped_strings:
                if "Prognóstico" in text: continue # Pula titulo
                m = date_pattern_simple.search(text)
                if m:
                    day, month, year = m.groups()
                    match_date = f"{year}-{month_to_num(month)}-{day.zfill(2)}"
                    break

        # 3. Campeonato (Refinado)
        league = "Geral"
        # Tenta pegar do breadcrumb, que é estruturado
        bc_items = soup.select('.breadcrumbs li')
        if bc_items:
            # Estrutura comum: Home > Estatísticas > País > Liga > Jogo
            # Liga costuma ser o penúltimo ou antepenúltimo antes do jogo
            if len(bc_items) >= 4:
                # Pega o item que tem link para competição
                raw_league = bc_items[-2].get_text(strip=True)
                if " vs " in raw_league or " - " in raw_league: # Se pegou o jogo sem querer
                     raw_league = bc_items[-3].get_text(strip=True)
                league = raw_league.replace("»", "").strip()

        # 4. Prognóstico e Odd (Limpeza Agressiva)
        selection = "Não encontrado"
        odd = 0.0
        
        # Procura a caixa "Sugestão do editor"
        editor_box = soup.find(string=re.compile("Sugestão do editor"))
        if editor_box:
            container = editor_box.find_parent(['div', 'td'])
            if container:
                # Pega todo o texto do container
                full_text = container.get_text(" ", strip=True)
                # Remove o rótulo
                clean_text = full_text.replace("Sugestão do editor", "").replace("Pub", "").strip()
                
                # Tenta extrair a Odd primeiro
                odd_match = re.search(r'Odd\s*(\d+[.,]\d+)', clean_text, re.IGNORECASE)
                if odd_match:
                    odd_str = odd_match.group(1).replace(',', '.')
                    odd = float(odd_str)
                    # O palpite é tudo antes da palavra "Odd"
                    selection = clean_text[:odd_match.start()].strip()
                else:
                    # Se não tem "Odd" explícito, tenta achar um número float no fim
                    decimal_match = re.search(r'(\d+[.,]\d+)$', clean_text)
                    if decimal_match:
                        odd_str = decimal_match.group(1).replace(',', '.')
                        odd = float(odd_str)
                        selection = clean_text[:decimal_match.start()].strip()
                    else:
                        selection = clean_text

        # Validação final do palpite
        if len(selection) < 3 or "atividade de lazer" in selection.lower():
            selection = "Análise sem tip clara"

        # 5. Status/Placar (Para atualizar green/red depois)
        status = "PENDING"
        # Procura placar no formato "1 - 0" ou "2 : 1"
        score_pattern = re.compile(r'^\s*(\d+)\s*[-:]\s*(\d+)\s*$')
        score_area = soup.select_one('.match-score, .result, .score')
        if score_area:
            s_txt = score_area.get_text(strip=True)
            if score_pattern.match(s_txt):
                status = s_txt # Guarda o placar como status por enquanto

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
    if not data or data['selection'] == "Análise sem tip clara": 
        return
        
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        # Usa match_url como chave única para atualizar se já existir
        c.execute('''
            INSERT OR REPLACE INTO predictions 
            (match_url, date_collected, match_date, match_time, league, home_team, away_team, selection, odd, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['match_url'], 
            data['date_collected'], 
            data['match_date'], 
            data['match_time'],
            data['league'], 
            data['home_team'], 
            data['away_team'], 
            data['selection'], 
            data['odd'], 
            data['status']
        ))
        conn.commit()
        print(f"✅ [{data['match_date']} {data['match_time']}] {data['home_team']} x {data['away_team']} -> {data['selection']} (@{data['odd']})")
    except Exception as e:
        print(f"Erro banco: {e}")
    finally:
        conn.close()

def main():
    init_db()
    print("🚀 Iniciando coleta...")
    
    # Coleta páginas 1 a 3 (geralmente cobrem o dia e o seguinte)
    for p in range(1, 4):
        print(f"--- Página {p} ---")
        links = get_previews(page=p)
        if not links:
            print("Sem mais links.")
            break
            
        for link in links:
            data = parse_preview(link)
            save(data)
            
    print("🏁 Finalizado.")

if __name__ == "__main__":
    main()
