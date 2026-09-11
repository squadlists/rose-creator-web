import os
import re
import urllib.request
import urllib.parse
from urllib.parse import urljoin, quote
from io import BytesIO
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from unidecode import unidecode
from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGOS_DIR = os.path.join(BASE_DIR, "static", "logos_cache")
os.makedirs(LOGOS_DIR, exist_ok=True)

WEB_HDR = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
}

# ─────────────────────────────────────────────────────────
#   MAPPA NOMI UFFICIALI GETTY IMAGES
# ─────────────────────────────────────────────────────────
GETTY_TEAM_NAMES = {
    # Italia - Serie A
    "atalanta": "Atalanta BC",
    "atalanta bc": "Atalanta BC",
    "bologna": "Bologna FC 1909",
    "bologna fc": "Bologna FC 1909",
    "bologna fc 1909": "Bologna FC 1909",
    "cagliari": "Cagliari Calcio",
    "cagliari calcio": "Cagliari Calcio",
    "como": "Como 1907",
    "como 1907": "Como 1907",
    "empoli": "Empoli FC",
    "empoli fc": "Empoli FC",
    "fiorentina": "ACF Fiorentina",
    "acf fiorentina": "ACF Fiorentina",
    "frosinone": "Frosinone Calcio",
    "frosinone calcio": "Frosinone Calcio",
    "genoa": "Genoa CFC",
    "genoa cfc": "Genoa CFC",
    "inter": "FC Internazionale",
    "internazionale": "FC Internazionale",
    "inter milan": "FC Internazionale",
    "fc internazionale": "FC Internazionale",
    "fc internazionale milano": "FC Internazionale",
    "juventus": "Juventus FC",
    "juventus fc": "Juventus FC",
    "lazio": "SS Lazio",
    "ss lazio": "SS Lazio",
    "lecce": "US Lecce",
    "us lecce": "US Lecce",
    "milan": "AC Milan",
    "ac milan": "AC Milan",
    "monza": "AC Monza",
    "ac monza": "AC Monza",
    "napoli": "SSC Napoli",
    "ssc napoli": "SSC Napoli",
    "parma": "Parma Calcio 1913",
    "parma calcio 1913": "Parma Calcio 1913",
    "parma calcio": "Parma Calcio 1913",
    "roma": "AS Roma",
    "as roma": "AS Roma",
    "sassuolo": "US Sassuolo Calcio",
    "us sassuolo": "US Sassuolo Calcio",
    "torino": "Torino FC",
    "torino fc": "Torino FC",
    "udinese": "Udinese Calcio",
    "udinese calcio": "Udinese Calcio",
    "venezia": "Venezia FC",
    "venezia fc": "Venezia FC",
    "verona": "Hellas Verona FC",
    "hellas verona": "Hellas Verona FC",
    "hellas verona fc": "Hellas Verona FC",
    
    # Spagna - La Liga
    "real madrid": "Real Madrid CF",
    "barcelona": "FC Barcelona",
    "atletico madrid": "Club Atletico de Madrid",
    "atletico de madrid": "Club Atletico de Madrid",
    "athletic bilbao": "Athletic Club",
    "athletic club": "Athletic Club",
    "alaves": "Deportivo Alaves",
    "deportivo alaves": "Deportivo Alaves",
    "celta vigo": "RC Celta de Vigo",
    "real betis": "Real Betis Balompie",
    "real sociedad": "Real Sociedad de Futbol",
    "sevilla": "Sevilla FC",
    "valencia": "Valencia CF",
    "villarreal": "Villarreal CF",
    "espanyol": "RCD Espanyol de Barcelona",
    "mallorca": "RCD Mallorca",
    "getafe": "Getafe CF",
    "girona": "Girona FC",
    "osasuna": "CA Osasuna",
    "rayo vallecano": "Rayo Vallecano de Madrid",
    "las palmas": "UD Las Palmas",
    "leganes": "CD Leganes",
    "valladolid": "Real Valladolid CF",

    # Inghilterra - Premier League
    "arsenal": "Arsenal FC",
    "aston villa": "Aston Villa FC",
    "chelsea": "Chelsea FC",
    "liverpool": "Liverpool FC",
    "manchester city": "Manchester City FC",
    "manchester united": "Manchester United FC",
    "newcastle united": "Newcastle United FC",
    "tottenham hotspur": "Tottenham Hotspur FC",
    "west ham united": "West Ham United FC",
    "everton": "Everton FC",

    # Germania - Bundesliga
    "bayern munich": "FC Bayern Munchen",
    "bayern munchen": "FC Bayern Munchen",
    "borussia dortmund": "Borussia Dortmund",
    "bayer leverkusen": "Bayer 04 Leverkusen",
    "rb leipzig": "RB Leipzig",

    # Francia - Ligue 1
    "paris saint germain": "Paris Saint-Germain FC",
    "psg": "Paris Saint-Germain FC",
    "marseille": "Olympique de Marseille",
    "monaco": "AS Monaco FC",
    "lyon": "Olympique Lyonnais",
}

def to_getty_team_name(raw_name):
    if not raw_name: return ""
    clean = unidecode(raw_name).strip()
    key = clean.lower()
    
    if key in GETTY_TEAM_NAMES:
        return GETTY_TEAM_NAMES[key]
        
    for k, v in GETTY_TEAM_NAMES.items():
        if f" {k} " in f" {key} " or key.startswith(f"{k} ") or key.endswith(f" {k}"):
            return v
            
    for w in key.split():
        if len(w) > 3 and w in GETTY_TEAM_NAMES:
            return GETTY_TEAM_NAMES[w]
            
    return clean

def get_smart_abbrev(nome):
    clean = unidecode(nome).strip()
    upper = clean.upper()
    for p in ["AS ", "SSC ", "ACF ", "FC ", "AC ", "SS ", "US ", "AFC ", "CF ", "CD ", "UD "]:
        if upper.startswith(p):
            clean = clean[len(p):].strip()
            break
    return clean[0].lower() if clean else "x"

def get_distinct_abbrevs(home_name, away_name):
    ha = get_smart_abbrev(home_name)
    aa = get_smart_abbrev(away_name)
    if ha == aa:
        clean_a = unidecode(away_name).lower()
        for p in ["as ", "ssc ", "acf ", "fc ", "ac ", "ss ", "us ", "cd ", "ud ", "deportivo "]:
            if clean_a.startswith(p):
                clean_a = clean_a[len(p):]
                break
        found = False
        for ch in clean_a:
            if ch.isalpha() and ch != ha:
                aa = ch
                found = True
                break
        if not found:
            aa = "z" if ha != "z" else "y"
    return ha, aa

# ─────────────────────────────────────────────────────────
#   DOWNLOAD & CACHE LOGHI
# ─────────────────────────────────────────────────────────
def fetch_team_logo(team_name, raw_name=""):
    if not team_name: return None
    clean_name = unidecode(team_name).strip()
    safe_name = "".join(c for c in clean_name if c.isalnum() or c in (" ", "_")).strip()
    cache_path = os.path.join(LOGOS_DIR, f"{safe_name}.png")
    rel_url = f"/static/logos_cache/{safe_name}.png"
    if os.path.exists(cache_path):
        return rel_url
        
    candidates = []
    if raw_name: candidates.append(unidecode(raw_name).strip())
    candidates.append(clean_name)
    
    for p in ["AS ", "SSC ", "ACF ", "FC ", "AC ", "SS ", "US ", "AFC ", "CF ", "CD ", "UD "]:
        if clean_name.upper().startswith(p):
            candidates.append(clean_name[len(p):].strip())
    for s in [" FC", " Calcio", " BC", " CFC", " CF", " 1909", " 1913"]:
        if clean_name.upper().endswith(s):
            candidates.append(clean_name[:-len(s)].strip())
            
    for q in candidates[:3]:
        if not q: continue
        try:
            url = f"https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t={quote(q)}"
            r = requests.get(url, headers=WEB_HDR, timeout=2.0)
            d = r.json()
            if d and d.get("teams"):
                b_url = d["teams"][0].get("strBadge")
                if b_url:
                    im_r = requests.get(b_url, headers=WEB_HDR, timeout=2.5)
                    im = Image.open(BytesIO(im_r.content)).convert("RGBA")
                    im.save(cache_path)
                    return rel_url
        except Exception:
            pass

    for q in candidates[:2]:
        if not q: continue
        try:
            w_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={quote(q)}&limit=1&format=json"
            r = requests.get(w_url, headers=WEB_HDR, timeout=2.0).json()
            if r and len(r) > 1 and r[1]:
                canonical = r[1][0]
                p_url = f"https://en.wikipedia.org/w/api.php?action=query&titles={quote(canonical)}&prop=pageimages&format=json&pithumbsize=128"
                r2 = requests.get(p_url, headers=WEB_HDR, timeout=2.0).json()
                pages = r2.get("query", {}).get("pages", {})
                for _, p_info in pages.items():
                    if "thumbnail" in p_info:
                        im_r = requests.get(p_info["thumbnail"]["source"], headers=WEB_HDR, timeout=2.5)
                        im = Image.open(BytesIO(im_r.content)).convert("RGBA")
                        im.save(cache_path)
                        return rel_url
        except Exception:
            pass
            
    return None

# ─────────────────────────────────────────────────────────
#   FILTRI E SCRAPING FOOTBALLSQUADS
# ─────────────────────────────────────────────────────────
ESCLUDI = {
    "search","privacy policy","squad","squads","terms of use",
    "terms of us","contact","home","about","links","sitemap",
    "advertise","help","login","register","news","fixtures",
    "results","tables","stats","players","managers","transfers",
}

def is_squadra_valida(nome):
    if not nome or len(nome) < 3: return False
    if nome.lower() in ESCLUDI: return False
    if any(c in nome for c in ["©","|","?"]): return False
    return True

HDR = {"User-Agent": "Mozilla/5.0"}

def estrai_giocatori(url):
    r = requests.get(url, headers=HDR); r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    tabella = None
    for tab in soup.find_all("table"):
        for row in tab.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) >= 2 and cols[0].get_text(strip=True).isdigit():
                tabella = tab; break
        if tabella: break
    if not tabella: return []

    STOP = ["no longer at this club","players no longer","left the club","departed","ex-players"]
    giocatori, visti = [], set()
    for row in tabella.find_all("tr")[1:]:
        if any(kw in row.get_text(" ", strip=True).lower() for kw in STOP): break
        cols = row.find_all("td")
        if len(cols) < 2: continue
        nt = cols[0].get_text(strip=True)
        nome = cols[1].get_text(strip=True)
        if not nt.isdigit() or not nome.strip(): continue
        n = int(nt); nome = unidecode(nome)
        if (n, nome) not in visti:
            visti.add((n, nome)); giocatori.append((n, nome))
    return sorted(giocatori, key=lambda x: x[0])

def estrai_allenatore(url):
    r = requests.get(url, headers=HDR); r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for b in soup.find_all("b"):
        if "Manager" in b.get_text():
            testo = b.parent.get_text(" ", strip=True)
            if "Manager:" in testo:
                p = testo.split("Manager:", 1)[1].strip()
                if "Ground:" in p: p = p.split("Ground:", 1)[0].strip()
                if "[" in p:       p = p.split("[", 1)[0].strip()
                return unidecode(p)
    return None

def estrai_nome_squadra(url):
    parte = url.split("/")[-1].replace(".htm","")
    nome  = parte.replace("-"," ").title()
    return to_getty_team_name(nome)

BASE_URL   = "https://www.footballsquads.co.uk/"
SQUADS_URL = "https://www.footballsquads.co.uk/squads.htm"

NAZIONI = {
    "England":        "eng",
    "Italy":          "italy",
    "Spain":          "spain",
    "Germany":        "ger",
    "France":         "france",
    "Portugal":       "portugal",
    "Netherlands":    "netherl",
    "Scotland":       "scots",
    "Belgium":        "belgium",
    "Turkey":         "turkey",
    "Greece":         "greece",
    "Switzerland":    "switz",
    "Austria":        "austria",
    "Russia":         "russia",
    "USA":            "usa",
    "Brazil":         "brazil",
    "Saudi Arabia":   "saudi",
    "Australia":      "australia",
    "Denmark":        "denmark",
    "Czech Republic": "czech",
    "Poland":         "poland",
    "Croatia":        "croatia",
    "Hungary":        "hungary",
    "Ireland":        "ireland",
}

SKIP_HREF = ["privacy","terms","contact","search","about","home","sitemap",
             "forums","archive","national","updates","mailto","facebook",
             "twitter","x.com","bsky","threads","pripol","tou","squads"]

def estrai_campionati(nazione):
    prefisso = NAZIONI.get(nazione, "").lower()
    r = requests.get(SQUADS_URL, headers=HDR)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    campionati = {}
    for l in soup.find_all("a"):
        href = l.get("href", "")
        nome = l.get_text(strip=True)
        if not href.endswith(".htm") or not nome or len(nome) < 3: continue
        if any(x in href.lower() for x in SKIP_HREF): continue
        if not href.lower().startswith(prefisso + "/"): continue
        campionati[nome] = urljoin(BASE_URL, href)
    if not campionati: raise Exception(f"Nessun campionato trovato per {nazione}.")
    return campionati

def estrai_squadre(url_camp):
    r = requests.get(url_camp, headers=HDR); r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    squadre, mappa = [], {}
    for l in soup.find_all("a"):
        href = l.get("href",""); nome = l.get_text(strip=True)
        if not href.endswith(".htm"): continue
        if any(x in href for x in ["privacy","terms","contact","search","about"]): continue
        if not is_squadra_valida(nome): continue
        full = urljoin(url_camp, href)
        if nome not in mappa:
            squadre.append(nome); mappa[nome] = full
    return squadre, mappa

FS_SERIE_A_MAPPING = {
    "atalanta": "https://www.footballsquads.co.uk/italy/2026-2027/seriea/atalanta.htm",
    "bologna": "https://www.footballsquads.co.uk/italy/2026-2027/seriea/bologna.htm",
    "cagliari": "https://www.footballsquads.co.uk/italy/2026-2027/seriea/cagliari.htm",
    "como": "https://www.footballsquads.co.uk/italy/2026-2027/seriea/como.htm",
    "empoli": "https://www.footballsquads.co.uk/italy/2026-2027/seriea/empoli.htm",
    "fiorentina": "https://www.footballsquads.co.uk/italy/2026-2027/seriea/fiorenti.htm",
    "frosinone": "https://www.footballsquads.co.uk/italy/2026-2027/seriea/frosinone.htm",
    "genoa": "https://www.footballsquads.co.uk/italy/2026-2027/seriea/genoa.htm",
    "inter": "https://www.footballsquads.co.uk/italy/2026-2027/seriea/inter.htm",
    "internazionale": "https://www.footballsquads.co.uk/italy/2026-2027/seriea/inter.htm",
    "fc internazionale": "https://www.footballsquads.co.uk/italy/2026-2027/seriea/inter.htm",
    "juventus": "https://www.footballsquads.co.uk/italy/2026-2027/seriea/juventus.htm",
    "lazio": "https://www.footballsquads.co.uk/italy/2026-2027/seriea/lazio.htm",
    "lecce": "https://www.footballsquads.co.uk/italy/2026-2027/seriea/lecce.htm",
    "milan": "https://www.footballsquads.co.uk/italy/2026-2027/seriea/milan.htm",
    "monza": "https://www.footballsquads.co.uk/italy/2026-2027/seriea/monza.htm",
    "napoli": "https://www.footballsquads.co.uk/italy/2026-2027/seriea/napoli.htm",
    "parma": "https://www.footballsquads.co.uk/italy/2026-2027/seriea/parma.htm",
    "roma": "https://www.footballsquads.co.uk/italy/2026-2027/seriea/roma.htm",
    "sassuolo": "https://www.footballsquads.co.uk/italy/2026-2027/seriea/sassuolo.htm",
    "torino": "https://www.footballsquads.co.uk/italy/2026-2027/seriea/torino.htm",
    "udinese": "https://www.footballsquads.co.uk/italy/2026-2027/seriea/udinese.htm",
    "venezia": "https://www.footballsquads.co.uk/italy/2026-2027/seriea/venezia.htm",
    "verona": "https://www.footballsquads.co.uk/italy/2026-2027/seriea/verona.htm",
    "hellas verona": "https://www.footballsquads.co.uk/italy/2026-2027/seriea/verona.htm"
}

def get_fs_serie_a_url(team_name):
    clean = unidecode(team_name).lower().strip()
    for k, u in FS_SERIE_A_MAPPING.items():
        if k == clean or f" {k} " in f" {clean} " or clean.startswith(f"{k} ") or clean.endswith(f" {k}"):
            return u
    for w in clean.split():
        if len(w) > 3 and w in FS_SERIE_A_MAPPING:
            return FS_SERIE_A_MAPPING[w]
    return None

def formatta_partita_completa(home_team, home_abbr, home_players, home_coach,
                             away_team, away_abbr, away_players, away_coach,
                             arbitro, formato="standard"):
    clean_h = unidecode(home_team)
    clean_a = unidecode(away_team)
    clean_ref = unidecode(arbitro).strip()
    
    ha = str(home_abbr).strip().lower() if home_abbr else "h"
    aa = str(away_abbr).strip().lower() if away_abbr else "a"
    if ha == aa:
        for ch in clean_a.lower():
            if ch.isalpha() and ch != ha:
                aa = ch
                break
        if ha == aa:
            aa = "z" if ha != "z" else "y"
            
    # Lista 1 Casa
    h_l1 = []
    for n, nome in home_players:
        clean_p = unidecode(nome)
        if formato == "apostrophe":
            h_l1.append(f"{ha}{n}\t{clean_h}'s {clean_p} ")
        else:
            h_l1.append(f"{ha}{n}\t{clean_p} of {clean_h} ")
    if home_coach:
        clean_coach = unidecode(home_coach)
        if formato == "apostrophe":
            h_l1.append(f"{ha}m\t{clean_h}'s {clean_coach} Head Coach ")
        else:
            h_l1.append(f"{ha}m\t{clean_coach} Head Coach of {clean_h} ")
    if formato == "apostrophe":
        h_l1.append(f"s{ha}\t{clean_h}'s Supporters ")
    else:
        h_l1.append(f"s{ha}\tSupporters of {clean_h} ")

    # Lista 1 Trasferta
    a_l1 = []
    for n, nome in away_players:
        clean_p = unidecode(nome)
        if formato == "apostrophe":
            a_l1.append(f"{aa}{n}\t{clean_a}'s {clean_p} ")
        else:
            a_l1.append(f"{aa}{n}\t{clean_p} of {clean_a} ")
    if away_coach:
        clean_coach = unidecode(away_coach)
        if formato == "apostrophe":
            a_l1.append(f"{aa}m\t{clean_a}'s {clean_coach} Head Coach ")
        else:
            a_l1.append(f"{aa}m\t{clean_coach} Head Coach of {clean_a} ")
    if formato == "apostrophe":
        a_l1.append(f"s{aa}\t{clean_a}'s Supporters ")
    else:
        a_l1.append(f"s{aa}\tSupporters of {clean_a} ")

    # Lista 2 Casa
    h_l2 = []
    for n, nome in home_players:
        h_l2.append(f"{ha}{ha}{n}\t{unidecode(nome)},")
    if home_coach:
        h_l2.append(f"{ha}{ha}m\t{unidecode(home_coach)},")
    h_l2.append(f"ss{ha}\tSupporters of {clean_h},")

    # Lista 2 Trasferta
    a_l2 = []
    for n, nome in away_players:
        a_l2.append(f"{aa}{aa}{n}\t{unidecode(nome)},")
    if away_coach:
        a_l2.append(f"{aa}{aa}m\t{unidecode(away_coach)},")
    a_l2.append(f"ss{aa}\tSupporters of {clean_a},")

    testo = (
        f"=== {clean_h} ===\n"
        f"Calciatori in rosa: {len(home_players)}\n\n"
        + "\n".join(h_l1)
        + f"\n\n=== {clean_a} ===\n"
        f"Calciatori in rosa: {len(away_players)}\n\n"
        + "\n".join(a_l1)
    )
    
    if clean_ref:
        testo += f"\n\n=== Arbitro ===\narb\t{clean_ref} "
        
    testo += (
        f"\n\n=== Lista bbX ===\n"
        + "\n".join(h_l2)
        + "\n"
        + "\n".join(a_l2)
    )
    
    if clean_ref:
        testo += f"\narbb\t{clean_ref},"

    return testo

def formatta_doppia_rosa_singola(squadra, giocatori, allenatore=None, formato="standard", custom_abbr=None):
    clean_squadra = unidecode(squadra)
    abbr = custom_abbr[0].lower() if custom_abbr else get_smart_abbrev(squadra)
    
    l1 = []
    for n, nome in giocatori:
        clean_nome = unidecode(nome)
        if formato == "apostrophe":
            l1.append(f"{abbr}{n}\t{clean_squadra}'s {clean_nome} ")
        else:
            l1.append(f"{abbr}{n}\t{clean_nome} of {clean_squadra} ")
            
    if allenatore:
        clean_all = unidecode(allenatore)
        if formato == "apostrophe":
            l1.append(f"{abbr}m\t{clean_squadra}'s {clean_all} Head Coach ")
        else:
            l1.append(f"{abbr}m\t{clean_all} Head Coach of {clean_squadra} ")
            
    if formato == "apostrophe":
        l1.append(f"s{abbr}\t{clean_squadra}'s Supporters ")
    else:
        l1.append(f"s{abbr}\tSupporters of {clean_squadra} ")

    l2 = []
    for n, nome in giocatori:
        l2.append(f"{abbr}{abbr}{n}\t{unidecode(nome)},")
    if allenatore:
        l2.append(f"{abbr}{abbr}m\t{unidecode(allenatore)},")
    l2.append(f"ss{abbr}\tSupporters of {clean_squadra},")

    header_team = f"=== {clean_squadra} ===\nCalciatori in rosa: {len(giocatori)}\n\n"
    blocco1 = "\n".join(l1)
    header_l2 = "\n\n=== Lista bbX ===\n"
    blocco2 = "\n".join(l2)
    return header_team + blocco1 + header_l2 + blocco2

# ─────────────────────────────────────────────────────────
#   SCRAPING AIA CAN & LEGA SERIE A
# ─────────────────────────────────────────────────────────
#   ORGANICO CAN & SCRAPING ARBITRI (AIA-FIGC + SKY SPORT FALLBACK)
# ─────────────────────────────────────────────────────────
CAN_ROSTER_STATIC = {
    "ABISSO": "Rosario Abisso",
    "ALLEGRETTA": "Claudio Giuseppe Allegretta",
    "ARENA": "Alberto Ruben Arena",
    "AYROLDI": "Giovanni Ayroldi",
    "BELLO": "Marco Di Bello",
    "BONACINA": "Kevin Bonacina",
    "CALZAVARA": "Andrea Calzavara",
    "CAPUTI": "Maria Sole Ferrieri Caputi",
    "CHIFFI": "Daniele Chiffi",
    "COLLU": "Giuseppe Collu",
    "COLOMBO": "Andrea Colombo",
    "CREZZINI": "Valerio Crezzini",
    "DI BELLO": "Marco Di Bello",
    "DI LORETO": "Marco Di Loreto",
    "DI MARCO": "Davide Di Marco",
    "DOVERI": "Daniele Doveri",
    "DRIGO": "Mattia Drigo",
    "FABBRI": "Michael Fabbri",
    "FELICIANI": "Ermanno Feliciani",
    "FERRIERI CAPUTI": "Maria Sole Ferrieri Caputi",
    "FOURNEAU": "Francesco Fourneau",
    "GALIPO": "Simone Galipo'",
    "GALIPO'": "Simone Galipo'",
    "GUIDA": "Marco Guida",
    "LA PENNA": "Federico La Penna",
    "LORETO": "Marco Di Loreto",
    "MADONIA": "Dario Madonia",
    "MANGANIELLO": "Gianluca Manganiello",
    "MARCENARO": "Matteo Marcenaro",
    "MARCHETTI": "Matteo Marchetti",
    "MARCO": "Davide Di Marco",
    "MARESCA": "Fabio Maresca",
    "MARIANI": "Maurizio Mariani",
    "MARINELLI": "Livio Marinelli",
    "MASSA": "Davide Massa",
    "MAZZONI": "Edoardo Manedo Mazzoni",
    "MUCERA": "Giuseppe Mucera",
    "PAIRETTO": "Luca Pairetto",
    "PENNA": "Federico La Penna",
    "PERENZONI": "Daniele Perenzoni",
    "PERRI": "Mario Perri",
    "POLI": "Alberto Poli",
    "RAPUANO": "Antonio Rapuano",
    "SACCHI": "Juan Luca Sacchi",
    "SOZZA": "Simone Sozza",
    "TREMOLADA": "Paride Tremolada",
    "TURRINI": "Niccolo' Turrini",
    "ZANOTTI": "Andrea Zanotti",
    "ZUFFERLI": "Luca Zufferli"
}

_CAN_ROSTER_CACHE = {}

def get_can_roster():
    """Recupera l'organico CAN con nome e cognome completo degli arbitri."""
    global _CAN_ROSTER_CACHE
    if _CAN_ROSTER_CACHE:
        return _CAN_ROSTER_CACHE
    try:
        req = urllib.request.Request("https://www.aia-figc.it/organici/can/", headers=WEB_HDR)
        with urllib.request.urlopen(req, timeout=6) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")
        table = None
        for t in soup.find_all("table"):
            if "Arbitri" in t.get_text():
                table = t
                break
        roster = {}
        if table:
            for td in table.find_all("td"):
                for div in td.find_all("div"):
                    div.decompose()
                raw = td.get_text().strip()
                raw = re.sub(r'[\u200b\uFEFF\xa0]', ' ', raw).strip()
                raw = re.sub(r'\s+', ' ', raw)
                if not raw:
                    continue
                clean_name = raw.title()
                parts = raw.split()
                upper_words = [p for p in parts if p.isupper() and len(p) > 1]
                surname_key = " ".join(upper_words) if upper_words else parts[-1].upper()
                roster[surname_key] = clean_name
                if upper_words:
                    roster[upper_words[-1]] = clean_name
        if roster:
            _CAN_ROSTER_CACHE = {**CAN_ROSTER_STATIC, **roster}
            return _CAN_ROSTER_CACHE
    except Exception:
        pass
    _CAN_ROSTER_CACHE = CAN_ROSTER_STATIC.copy()
    return _CAN_ROSTER_CACHE

def get_sky_referee_designations(roster=None):
    """Fallback resiliente da Sky Sport per server cloud (Render/AWS) che non bloccano il traffico."""
    if not roster:
        roster = get_can_roster()
    try:
        r = requests.get("https://sport.sky.it/calcio/serie-a", headers=WEB_HDR, timeout=8)
        if r.status_code != 200:
            return {}, {}, ""
        soup = BeautifulSoup(r.text, "html.parser")
        article_url = None
        round_title = "Serie A"
        for a in soup.find_all("a", href=True):
            txt = a.get_text().strip()
            if "designazion" in txt.lower() or "arbitr" in txt.lower():
                if "serie-a" in a["href"]:
                    article_url = a["href"]
                    m = re.search(r"(\d+)\^?\s*giornata", txt, re.I)
                    if m:
                        round_title = f"{m.group(1)}ª Giornata"
                    break
        if not article_url:
            return {}, {}, ""

        r2 = requests.get(article_url, headers=WEB_HDR, timeout=8)
        if r2.status_code != 200:
            return {}, {}, ""
        soup2 = BeautifulSoup(r2.text, "html.parser")
        article = soup2.find("article") or soup2

        pair_map = {}
        single_map = {}
        p_tags = [p.get_text().strip() for p in article.find_all(["p", "h2", "h3"]) if p.get_text().strip()]
        for i, p in enumerate(p_tags):
            if len(p) > 100:
                continue
            if any(sep in p for sep in ["–", "-", "—"]) and any(w in p.lower() for w in ["ore", "venerd", "sabat", "domenic", "luned", "marted", "mercoled", "gioved"]):
                parts = re.split(r"[–—\-]", p)
                if len(parts) >= 2:
                    h_team = unidecode(parts[0]).strip().lower()
                    a_raw = parts[1].strip()
                    a_clean = re.split(r"\b(venerd[iì]|sabat[o]|domenic[a]|luned[iì]|marted[iì]|mercoled[iì]|gioved[iì]|ore|\d{1,2}[\.:]\d{2})\b", a_raw, flags=re.I)[0].strip()
                    a_team = unidecode(a_clean).strip().lower()

                    ref_raw = ""
                    if i + 1 < len(p_tags):
                        cand = re.sub(r"\(.*?\)", "", p_tags[i+1].strip()).strip()
                        if ":" not in cand and len(cand) < 30 and not any(k in cand.lower() for k in ["ore", "live", "assistenti", "–", "-"]):
                            ref_raw = cand

                    ref_clean = re.sub(r"[^A-Z\s]", "", unidecode(ref_raw).upper()).strip()
                    ref_full = roster.get(ref_clean)
                    if not ref_full:
                        for w in ref_clean.split():
                            if w in roster:
                                ref_full = roster[w]
                                break
                    if not ref_full:
                        for skey, sfull in roster.items():
                            if len(skey) > 3 and skey in ref_clean:
                                ref_full = sfull
                                break
                    if not ref_full:
                        ref_full = ref_raw.title() if ref_raw else "Da definire"

                    pair_map[(h_team, a_team)] = ref_full
                    single_map[h_team] = ref_full
                    single_map[a_team] = ref_full

        return pair_map, single_map, round_title
    except Exception:
        return {}, {}, ""

def get_aia_referee_designations():
    """Recupera l'abbinamento partita -> arbitro. Tenta prima AIA CAN ufficiale, poi fallback automatico a Sky Sport."""
    roster = get_can_roster()
    pair_map = {}
    single_map = {}
    round_title = ""

    # 1. Tentativo ufficiale AIA-FIGC CAN
    try:
        req = urllib.request.Request("https://www.aia-figc.it/designazioni/can/", headers=WEB_HDR)
        with urllib.request.urlopen(req, timeout=6) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        soup = BeautifulSoup(html, "html.parser")
        
        serie_a_link = None
        for a in soup.find_all("a", href=True):
            txt = a.get_text()
            if "SERIE A" in txt.upper() and "DESIGNAZIONI" in txt.upper():
                serie_a_link = a["href"]
                round_title = txt.strip()
                break
                
        if serie_a_link:
            if not serie_a_link.startswith("http"):
                serie_a_link = "https://www.aia-figc.it" + ("/" if not serie_a_link.startswith("/") else "") + serie_a_link
                
            req2 = urllib.request.Request(serie_a_link, headers=WEB_HDR)
            with urllib.request.urlopen(req2, timeout=6) as resp2:
                art_html = resp2.read().decode("utf-8", errors="ignore")
                
            art_soup = BeautifulSoup(art_html, "html.parser")
            content_div = art_soup.find("section", id="content") or art_soup
            p_tags = [p.get_text().strip() for p in content_div.find_all("p") if p.get_text().strip()]
            
            for i, p in enumerate(p_tags):
                if any(sep in p for sep in ["–", "-", "—"]) and any(d in p.lower() for d in ["venerdì", "venerdi", "sabato", "domenica", "lunedì", "lunedi", "mercoledì", "martedì", "giovedì", "h.", "h "]):
                    match_part = p
                    for kw in ["venerdì", "venerdi", "sabato", "domenica", "lunedì", "lunedi", "mercoledì", "martedì", "giovedì"]:
                        if kw in match_part.lower():
                            match_part = re.split(kw, match_part, flags=re.I)[0].strip()
                            break
                    
                    parts = re.split(r'[–—\-]', match_part)
                    if len(parts) >= 2:
                        h_team = unidecode(parts[0]).strip().lower()
                        a_team = unidecode(parts[1]).strip().lower()
                        
                        ref_raw = ""
                        if i + 1 < len(p_tags):
                            cand = p_tags[i+1].strip()
                            cand = re.sub(r'\(.*?\)', '', cand).strip()
                            if ":" not in cand and "–" not in cand and len(cand) < 35:
                                ref_raw = cand
                                
                        ref_clean = re.sub(r'[^A-Z\s]', '', ref_raw.upper()).strip()
                        ref_full = roster.get(ref_clean)
                        if not ref_full and ref_clean.split():
                            ref_full = roster.get(ref_clean.split()[-1])
                        if not ref_full:
                            for skey, sfullname in roster.items():
                                if len(skey) > 3 and skey in ref_raw.upper():
                                    ref_full = sfullname
                                    break
                        if not ref_full:
                            ref_full = ref_raw.title() if ref_raw else "Da definire"
                            
                        pair_map[(h_team, a_team)] = ref_full
                        single_map[h_team] = ref_full
                        single_map[a_team] = ref_full
    except Exception:
        pass

    # 2. Se AIA-FIGC è bloccato (es. 403 su server cloud Render), fallback automatico su Sky Sport
    if not pair_map:
        sky_pairs, sky_singles, sky_round = get_sky_referee_designations(roster)
        if sky_pairs:
            pair_map = sky_pairs
            single_map = sky_singles
            if not round_title:
                round_title = sky_round

    return pair_map, single_map, round_title

def get_lega_serie_a_matches():
    """Recupera le partite della giornata da Lega Serie A con date e orari effettivi."""
    req = urllib.request.Request("https://www.legaseriea.it/it/serie-a", headers=WEB_HDR)
    with urllib.request.urlopen(req, timeout=8) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
        
    idx = html.find('initialMatches')
    if idx == -1:
        return []
        
    sub = html[idx:]
    arr_start = sub.find('[')
    brackets = 0
    in_str = False
    escape = False
    arr_end = -1
    for i, ch in enumerate(sub[arr_start:]):
        if escape:
            escape = False
            continue
        if ch == '\\':
            escape = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if not in_str:
            if ch == '[':
                brackets += 1
            elif ch == ']':
                brackets -= 1
                if brackets == 0:
                    arr_end = arr_start + i + 1
                    break
                    
    if arr_end == -1:
        return []
        
    raw_json_str = sub[arr_start:arr_end]
    import json
    try:
        matches_data = json.loads(raw_json_str)
    except Exception:
        raw_json_str_unescaped = raw_json_str.replace('\\"', '"').replace('\\\\', '\\')
        matches_data = json.loads(raw_json_str_unescaped)
        
    results = []
    for m in matches_data:
        dt_str = m.get("matchDateLocal", "")
        home_off = m.get("home", {}).get("officialName", "")
        away_off = m.get("away", {}).get("officialName", "")
        status = m.get("status", "")
        h_score = m.get("homeScorePush")
        a_score = m.get("awayScorePush")
        
        results.append({
            "date_local": dt_str,
            "home": home_off,
            "away": away_off,
            "home_getty": to_getty_team_name(home_off),
            "away_getty": to_getty_team_name(away_off),
            "status": status,
            "home_score": h_score,
            "away_score": a_score,
        })
    return results
