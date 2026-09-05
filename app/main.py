import os
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from unidecode import unidecode

from app.core import (
    get_lega_serie_a_matches,
    get_aia_referee_designations,
    get_distinct_abbrevs,
    fetch_team_logo,
    get_fs_serie_a_url,
    estrai_giocatori,
    estrai_allenatore,
    formatta_partita_completa,
    formatta_doppia_rosa_singola,
    NAZIONI,
    estrai_campionati,
    estrai_squadre,
    to_getty_team_name,
    LOGOS_DIR,
    BASE_DIR
)

app = FastAPI(
    title="Rose Creator by Giuseppe Maffia",
    description="Football team list generator - Web & Mobile Edition",
    version="3.0"
)

# In-memory caches for fast responses
_SERIE_A_CACHE = {"timestamp": 0, "data": None}
_ROSTER_CACHE = {} # url -> (players, coach)
_LEAGUES_CACHE = {} # nation -> dict of leagues
_TEAMS_CACHE = {} # league_url -> (teams, map)

# Mount static files
STATIC_DIR = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/manifest.json")
async def serve_manifest():
    return FileResponse(os.path.join(STATIC_DIR, "manifest.json"), media_type="application/manifest+json")

@app.get("/sw.js")
async def serve_sw():
    return FileResponse(os.path.join(STATIC_DIR, "sw.js"), media_type="application/javascript")

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": "Rose Creator", "version": "3.0", "author": "Giuseppe Maffia"}

# ─────────────────────────────────────────────────────────
#   SERIE A & AIA CAN ENDPOINTS
# ─────────────────────────────────────────────────────────
@app.get("/api/seriea/matches")
async def get_serie_a_matches(refresh: bool = False):
    now = datetime.now().timestamp()
    if not refresh and _SERIE_A_CACHE["data"] and (now - _SERIE_A_CACHE["timestamp"] < 300):
        return _SERIE_A_CACHE["data"]

    try:
        pair_map, single_map, round_title = get_aia_referee_designations()
        matches = get_lega_serie_a_matches()

        for m in matches:
            h = m.get("home", "")
            a = m.get("away", "")
            h_norm = unidecode(h).strip().lower()
            a_norm = unidecode(a).strip().lower()

            ref = None
            for (dh, da), rname in pair_map.items():
                if (dh in h_norm or h_norm in dh) and (da in a_norm or a_norm in da):
                    ref = rname
                    break
            if not ref:
                ref = single_map.get(h_norm) or single_map.get(a_norm) or "Da definire"
            m["referee"] = ref

            h_getty = m.get("home_getty", h)
            a_getty = m.get("away_getty", a)
            m["home_logo"] = fetch_team_logo(h_getty, h)
            m["away_logo"] = fetch_team_logo(a_getty, a)

            def_ha, def_aa = get_distinct_abbrevs(h_getty, a_getty)
            m["def_ha"] = def_ha
            m["def_aa"] = def_aa

        clean_badge = round_title.replace("ENILIVE - ", "").title() if round_title else "Giornata Serie A"
        result = {
            "round_title": clean_badge,
            "count": len(matches),
            "matches": matches
        }
        _SERIE_A_CACHE["timestamp"] = now
        _SERIE_A_CACHE["data"] = result
        return result
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))

class MatchExtractRequest(BaseModel):
    home_team: str
    away_team: str
    referee: Optional[str] = "Da definire"
    home_abbr: Optional[str] = None
    away_abbr: Optional[str] = None

@app.post("/api/seriea/extract")
async def extract_match(req: MatchExtractRequest):
    try:
        h_url = get_fs_serie_a_url(req.home_team)
        a_url = get_fs_serie_a_url(req.away_team)

        if not h_url or not a_url:
            raise HTTPException(
                status_code=404,
                detail=f"Impossibile trovare la URL FootballSquads per: Casa '{req.home_team}', Trasferta '{req.away_team}'"
            )

        if h_url not in _ROSTER_CACHE:
            _ROSTER_CACHE[h_url] = (estrai_giocatori(h_url), estrai_allenatore(h_url))
        home_players, home_coach = _ROSTER_CACHE[h_url]

        if a_url not in _ROSTER_CACHE:
            _ROSTER_CACHE[a_url] = (estrai_giocatori(a_url), estrai_allenatore(a_url))
        away_players, away_coach = _ROSTER_CACHE[a_url]

        def_ha, def_aa = get_distinct_abbrevs(req.home_team, req.away_team)
        ha = req.home_abbr.strip().lower() if req.home_abbr else def_ha
        aa = req.away_abbr.strip().lower() if req.away_abbr else def_aa
        if not ha: ha = def_ha
        if not aa: aa = def_aa

        text = formatta_partita_completa(
            home_team=req.home_team,
            home_abbr=ha,
            home_players=home_players,
            home_coach=home_coach,
            away_team=req.away_team,
            away_abbr=aa,
            away_players=away_players,
            away_coach=away_coach,
            arbitro=req.referee or "Da definire"
        )

        h_clean = unidecode(req.home_team).replace(" ", "_").replace(".", "")
        a_clean = unidecode(req.away_team).replace(" ", "_").replace(".", "")
        filename = f"{h_clean}_vs_{a_clean}.txt"

        return {
            "text": text,
            "filename": filename,
            "home_team": req.home_team,
            "away_team": req.away_team,
            "home_abbr": ha,
            "away_abbr": aa,
            "home_players_count": len(home_players),
            "away_players_count": len(away_players),
            "referee": req.referee or "Da definire"
        }
    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))

# ─────────────────────────────────────────────────────────
#   SINGOLA SQUADRA (MONDIALE) ENDPOINTS
# ─────────────────────────────────────────────────────────
@app.get("/api/single/nations")
async def get_nations():
    return {"nations": list(NAZIONI.keys())}

@app.get("/api/single/leagues")
async def get_leagues(nation: str = Query(..., description="Nome nazione in inglese")):
    if nation not in NAZIONI:
        raise HTTPException(status_code=400, detail="Nazione non valida")
    if nation in _LEAGUES_CACHE:
        return {"nation": nation, "leagues": _LEAGUES_CACHE[nation]}

    try:
        camps = estrai_campionati(nation)
        _LEAGUES_CACHE[nation] = camps
        return {"nation": nation, "leagues": camps}
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))

@app.get("/api/single/teams")
async def get_teams(league_url: str = Query(...)):
    if league_url in _TEAMS_CACHE:
        return _TEAMS_CACHE[league_url]

    try:
        squadre, mappa = estrai_squadre(league_url)
        items = []
        for raw in squadre:
            url = mappa[raw]
            getty = to_getty_team_name(raw)
            logo = fetch_team_logo(getty, raw)
            items.append({
                "raw_name": raw,
                "official_name": getty,
                "url": url,
                "logo": logo
            })
        data = {"teams": items}
        _TEAMS_CACHE[league_url] = data
        return data
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))

class SingleExtractRequest(BaseModel):
    team_name: str
    team_url: str
    abbr: Optional[str] = None
    formato: Optional[str] = "standard"

@app.post("/api/single/extract")
async def extract_single_team(req: SingleExtractRequest):
    try:
        if req.team_url not in _ROSTER_CACHE:
            _ROSTER_CACHE[req.team_url] = (
                estrai_giocatori(req.team_url),
                estrai_allenatore(req.team_url)
            )
        giocatori, allenatore = _ROSTER_CACHE[req.team_url]

        getty = to_getty_team_name(req.team_name)
        text = formatta_doppia_rosa_singola(
            squadra=getty,
            giocatori=giocatori,
            allenatore=allenatore,
            formato=req.formato or "standard",
            custom_abbr=req.abbr
        )

        safe_name = unidecode(getty).replace(" ", "_").replace(".", "")
        filename = f"{safe_name}.txt"

        return {
            "text": text,
            "filename": filename,
            "team_name": getty,
            "players_count": len(giocatori),
            "coach": allenatore or "—"
        }
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex))
