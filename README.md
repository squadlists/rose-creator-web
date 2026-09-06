# ⚽ Rose Creator by Giuseppe Maffia (Web & Mobile Edition)

Generatore professionale di rose calcistiche e formazioni per l'agenzia Getty Images, con supporto 1-Click per la **Serie A (Lega Serie A + AIA CAN)** e campionati internazionali.

Ottimizzato sia per **Desktop** sia per **Mobile (iPhone / iPad / Android)** con tecnologia **PWA (Progressive Web App)**.

## 🌐 Link Ufficiale Permanente (Attivo 24/7)

Il sito è online in cloud ad accesso continuo:
👉 **`https://rose-creator-web.onrender.com`**

Funziona da qualsiasi smartphone (iPhone / Android) e da qualsiasi rete (anche 4G / 5G fuori casa, con il computer spento)!


---

## 🚀 1. Come Avviarla in Locale o Riavviare il Cloud

- Per riavviare il tunnel cloud pubblico in qualsiasi momento:
  ```bash
  cd ~/.gemini/antigravity/scratch/rose_creator_web
  ./start_cloud.sh
  ```
- Per avviarla solo in rete locale:
  ```bash
  ./venv/bin/python run_local.py
  ```

3. Lo script ti mostrerà gli indirizzi:
   - **Dal Mac**: apri [http://localhost:8000](http://localhost:8000)
   - **Dal tuo iPhone / Android** (stesso Wi-Fi di casa): apri l'indirizzo mostrato nel terminale (es. `http://192.168.1.xxx:8000`).

---

## 🌐 2. Come Pubblicarlo Online Gratis su Render.com (3 Minuti)

La web app è già predisposta con `render.yaml` e `Procfile` per il piano **Gratuito al 100%** di Render.com.

### Passaggi:
1. **Crea un repository su GitHub** (es. `rose-creator-web`):
   ```bash
   cd ~/.gemini/antigravity/scratch/rose_creator_web
   git init
   git add .
   git commit -m "Initial commit - Rose Creator Web"
   git branch -M main
   # Collega il tuo repository GitHub:
   git remote add origin https://github.com/TUO_USERNAME/rose-creator-web.git
   git push -u origin main
   ```

2. **Vai su [Render.com](https://render.com/)**:
   - Registrati o accedi gratis (puoi fare il login con il tuo account GitHub).
   - Clicca sul pulsante in alto a destra **"New +"** ➔ Seleziona **"Web Service"**.
   - Seleziona il tuo repository GitHub `rose-creator-web`.

3. **Configurazione Automatica**:
   - Render rileverà automaticamente i parametri grazie al file `render.yaml`:
     - **Runtime**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
     - **Instance Type**: `Free`
   - Clicca su **"Create Web Service"**.

4. **Fatto!**
   In circa 60 secondi il tuo servizio sarà online con un link HTTPS gratuito, ad esempio:
   `https://rose-creator-xxxx.onrender.com`

---

## 📱 3. Come Installarla come Vera App su iPhone e Android

Una volta aperto il link (in locale o su Render):

### Su iPhone / iPad (Safari):
1. Apri la pagina su **Safari**.
2. Tocca il pulsante **Condividi** (l'icona quadrata con la freccia verso l'alto in basso al centro).
3. Scorri e seleziona **"Aggiungi alla schermata Home"** (Add to Home Screen).
4. Conferma con **"Aggiungi"**.
5. L'icona della maglietta da calcio in pixel art comparirà sulla tua Home: aprendola si avvierà a tutto schermo senza le barre di Safari, identica a un'app nativa!

### Su Android (Chrome):
1. Apri la pagina su **Google Chrome**.
2. Tocca i tre puntini in alto a destra (oppure il banner automatico *"Aggiungi Rose Creator alla schermata Home"*).
3. Seleziona **"Installa app"**.
