// Rose Creator Web & Mobile - Client Application
// by Giuseppe Maffia

const state = {
  activeTab: 'seriea',
  serieaMatches: [],
  serieaRound: 'Serie A',
  filter: 'all',
  currentOutput: '',
  currentFilename: 'partita_serie_a.txt',
  currentMatch: null,
  singleNations: [],
  singleLeagues: {},
  singleTeams: []
};

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
  initServiceWorker();
  initTabs();
  initCopyAndDownload();
  loadSerieAMatches();
  loadSingleNations();
});

function initServiceWorker() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch((err) => {
      console.log('SW registration skipped:', err);
    });
  }
}

function initTabs() {
  const tabSerieA = document.getElementById('tab-btn-seriea');
  const tabSingle = document.getElementById('tab-btn-single');
  const viewSerieA = document.getElementById('view-seriea');
  const viewSingle = document.getElementById('view-single');

  tabSerieA.addEventListener('click', () => {
    state.activeTab = 'seriea';
    tabSerieA.classList.add('active');
    tabSingle.classList.remove('active');
    viewSerieA.style.display = 'block';
    viewSingle.style.display = 'none';
  });

  tabSingle.addEventListener('click', () => {
    state.activeTab = 'single';
    tabSingle.classList.add('active');
    tabSerieA.classList.remove('active');
    viewSerieA.style.display = 'none';
    viewSingle.style.display = 'block';
  });
}

function initCopyAndDownload() {
  const copyBtn = document.getElementById('btn-copy');
  const downloadBtn = document.getElementById('btn-download');
  const textarea = document.getElementById('output-text');

  copyBtn.addEventListener('click', async () => {
    const text = textarea.value.trim();
    if (!text || text.startsWith('# MODALITÀ') || text.startsWith('# Istruzioni')) {
      showToast('Nessun testo da copiare!', '#f59e0b');
      return;
    }
    try {
      await navigator.clipboard.writeText(text);
      showToast('📋 Copiato negli appunti!', '#00c853');
    } catch (err) {
      // Fallback
      textarea.select();
      document.execCommand('copy');
      showToast('📋 Copiato negli appunti!', '#00c853');
    }
  });

  downloadBtn.addEventListener('click', () => {
    const text = textarea.value.trim();
    if (!text || text.startsWith('# MODALITÀ') || text.startsWith('# Istruzioni')) {
      showToast('Estrai prima una rosa per scaricare!', '#f59e0b');
      return;
    }
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = state.currentFilename || 'rosa_calcio.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast(`💾 Scaricato: ${state.currentFilename}`, '#2563eb');
  });

  // Setup Rigenera Button
  const btnRigenera = document.getElementById('btn-rigenera');
  if (btnRigenera) {
    btnRigenera.addEventListener('click', () => {
      if (!state.currentMatch) {
        showToast('Seleziona ed estrai prima una partita!', '#f59e0b');
        return;
      }
      const ha = document.getElementById('entry-ha').value.trim();
      const aa = document.getElementById('entry-aa').value.trim();
      extractMatch(state.currentMatch, ha, aa);
    });
  }
}

// ─────────────────────────────────────────────────────────
//   SERIE A LOGIC
// ─────────────────────────────────────────────────────────
async function loadSerieAMatches(refresh = false) {
  const statusLbl = document.getElementById('seriea-status');
  const container = document.getElementById('matches-list');
  statusLbl.textContent = '● Connessione a Lega Serie A e AIA CAN...';
  statusLbl.style.color = '#f59e0b';

  try {
    const res = await fetch(`/api/seriea/matches?refresh=${refresh}`);
    if (!res.ok) throw new Error('Errore caricamento partite');
    const data = await res.json();
    state.serieaMatches = data.matches || [];
    state.serieaRound = data.round_title || 'Serie A';

    let cleanRound = (state.serieaRound || '3ª Giornata').replace(/Serie A\s*•?\s*/i, '').trim();
    if (cleanRound.length > 30) {
      const match = cleanRound.match(/(\d+[ªa]?\s+Giornata)/i);
      cleanRound = match ? match[1] : '3ª Giornata';
    }
    document.getElementById('seriea-round-badge').textContent = `Serie A • ${cleanRound}`;
    statusLbl.textContent = `● ${state.serieaMatches.length} partite caricate con arbitri ufficiali`;
    statusLbl.style.color = '#00c853';

    renderSerieAMatches();
  } catch (err) {
    statusLbl.textContent = `● Errore: ${err.message}`;
    statusLbl.style.color = '#ef4444';
  }
}

function renderSerieAMatches() {
  const container = document.getElementById('matches-list');
  container.innerHTML = '';

  const filter = state.filter;
  const todayStr = new Date().toISOString().split('T')[0];

  const filtered = state.serieaMatches.filter((m) => {
    if (filter === 'today') {
      return (m.date_local || '').startsWith(todayStr);
    }
    return true;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 40px 10px; color: var(--text-sec); font-size: 0.9rem;">
        Nessuna partita programmata per la data odierna.<br>Seleziona <b>"Tutte"</b> per vedere l'intera giornata.
      </div>
    `;
    return;
  }

  filtered.forEach((m) => {
    const isToday = (m.date_local || '').startsWith(todayStr);
    let timeText = m.date_local || '';
    if (m.date_local) {
      try {
        const dt = new Date(m.date_local);
        const days = ['Dom', 'Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab'];
        const months = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic'];
        const dname = days[dt.getDay()];
        const mname = months[dt.getMonth()];
        const hh = String(dt.getHours()).padStart(2, '0');
        const mm = String(dt.getMinutes()).padStart(2, '0');
        timeText = isToday ? `🟢 OGGI • ${hh}:${mm}` : `📅 ${dname} ${dt.getDate()} ${mname} • ${hh}:${mm}`;
      } catch (e) {}
    }

    const homeName = m.home_getty || m.home;
    const awayName = m.away_getty || m.away;
    const homeLogo = m.home_logo || '';
    const awayLogo = m.away_logo || '';
    const ref = m.referee || 'Da definire';
    const defHa = m.def_ha || 'h';
    const defAa = m.def_aa || 'a';

    const card = document.createElement('div');
    card.className = 'match-card';
    card.innerHTML = `
      <div class="match-header">
        <span class="${isToday ? 'badge-today' : ''}" style="color: ${isToday ? 'var(--accent-green)' : 'var(--text-sec)'}">${timeText}</span>
        <span class="badge-ref">👤 Arb: ${ref}</span>
      </div>

      <div class="match-teams">
        <div class="team-box home">
          <span class="team-name" title="${homeName}">${homeName}</span>
          ${homeLogo ? `<img class="team-logo" src="${homeLogo}" alt="${homeName}" onerror="this.style.display='none'">` : '🛡️'}
        </div>
        <div class="vs-badge">VS</div>
        <div class="team-box away">
          ${awayLogo ? `<img class="team-logo" src="${awayLogo}" alt="${awayName}" onerror="this.style.display='none'">` : '🛡️'}
          <span class="team-name" title="${awayName}">${awayName}</span>
        </div>
      </div>

      <div class="abbr-row">
        <div class="abbr-box">
          <span style="color: var(--text-sec); font-weight: 600;">Sigla:</span>
          <input type="text" class="abbr-input input-ha" value="${defHa}" maxlength="2">
        </div>
        <span style="color: #363d57;">•</span>
        <div class="abbr-box">
          <span style="color: var(--text-sec); font-weight: 600;">Sigla:</span>
          <input type="text" class="abbr-input input-aa" value="${defAa}" maxlength="2">
        </div>
      </div>

      <button class="btn-extract">
        ⚡ Estrai Partita (Doppia Rosa + Arbitro)
      </button>
    `;

    const btnExtract = card.querySelector('.btn-extract');
    const inputHa = card.querySelector('.input-ha');
    const inputAa = card.querySelector('.input-aa');

    btnExtract.addEventListener('click', () => {
      extractMatch(m, inputHa.value.trim(), inputAa.value.trim());
    });

    container.appendChild(card);
  });
}

function filterMatches(val) {
  state.filter = val;
  document.getElementById('filter-all').classList.toggle('active', val === 'all');
  document.getElementById('filter-today').classList.toggle('active', val === 'today');
  renderSerieAMatches();
}

async function extractMatch(m, ha, aa) {
  state.currentMatch = m;
  const homeName = m.home_getty || m.home;
  const awayName = m.away_getty || m.away;
  const referee = m.referee || 'Da definire';

  // Update right param bar
  const entryHa = document.getElementById('entry-ha');
  const entryAa = document.getElementById('entry-aa');
  if (entryHa) entryHa.value = ha || m.def_ha || 'h';
  if (entryAa) entryAa.value = aa || m.def_aa || 'a';

  document.getElementById('output-title').textContent = `⚽ ${homeName} vs ${awayName}`;
  document.getElementById('output-ref-badge').textContent = `👤 Arb: ${referee}`;

  const textarea = document.getElementById('output-text');
  textarea.value = `Estrazione rose in corso: ${homeName} (${ha}) vs ${awayName} (${aa})...\nAttendere qualche istante...`;

  try {
    const res = await fetch('/api/seriea/extract', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        home_team: homeName,
        away_team: awayName,
        referee: referee,
        home_abbr: ha,
        away_abbr: aa
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Errore estrazione');
    }

    const data = await res.json();
    textarea.value = data.text;
    state.currentOutput = data.text;
    state.currentFilename = data.filename;

    showToast(`● ${homeName} vs ${awayName} estratta con successo!`, '#00c853');
    
    // Auto-scroll on mobile to preview
    if (window.innerWidth <= 1024) {
      document.querySelector('.output-column').scrollIntoView({ behavior: 'smooth' });
    }
  } catch (err) {
    textarea.value = `Errore durante l'estrazione:\n${err.message}`;
    showToast(`Errore: ${err.message}`, '#ef4444');
  }
}

// ─────────────────────────────────────────────────────────
//   SINGOLA SQUADRA LOGIC
// ─────────────────────────────────────────────────────────
async function loadSingleNations() {
  const selNation = document.getElementById('sel-nation');
  try {
    const res = await fetch('/api/single/nations');
    const data = await res.json();
    state.singleNations = data.nations || [];

    selNation.innerHTML = '<option value="">-- Seleziona Nazione --</option>';
    state.singleNations.forEach((n) => {
      const opt = document.createElement('option');
      opt.value = n;
      opt.textContent = n;
      if (n === 'Italy') opt.selected = true;
      selNation.appendChild(opt);
    });

    if (selNation.value) onSelectNation();
  } catch (e) {
    console.error('Error loading nations:', e);
  }
}

async function onSelectNation() {
  const selNation = document.getElementById('sel-nation');
  const selLeague = document.getElementById('sel-league');
  const selTeam = document.getElementById('sel-team');
  const nation = selNation.value;

  selLeague.innerHTML = '<option value="">Caricamento campionati...</option>';
  selTeam.innerHTML = '<option value="">-- Seleziona prima il campionato --</option>';

  try {
    const res = await fetch(`/api/single/leagues?nation=${encodeURIComponent(nation)}`);
    const data = await res.json();
    state.singleLeagues = data.leagues || {};

    selLeague.innerHTML = '<option value="">-- Seleziona Campionato --</option>';
    Object.entries(state.singleLeagues).forEach(([name, url]) => {
      const opt = document.createElement('option');
      opt.value = url;
      opt.textContent = name;
      selLeague.appendChild(opt);
    });

    // Select first league by default
    if (selLeague.options.length > 1) {
      selLeague.selectedIndex = 1;
      onSelectLeague();
    }
  } catch (e) {
    selLeague.innerHTML = '<option value="">Errore caricamento</option>';
  }
}

async function onSelectLeague() {
  const selLeague = document.getElementById('sel-league');
  const selTeam = document.getElementById('sel-team');
  const leagueUrl = selLeague.value;
  if (!leagueUrl) return;

  selTeam.innerHTML = '<option value="">Caricamento squadre...</option>';

  try {
    const res = await fetch(`/api/single/teams?league_url=${encodeURIComponent(leagueUrl)}`);
    const data = await res.json();
    state.singleTeams = data.teams || [];

    selTeam.innerHTML = '<option value="">-- Seleziona Squadra --</option>';
    state.singleTeams.forEach((t) => {
      const opt = document.createElement('option');
      opt.value = t.url;
      opt.textContent = t.official_name;
      selTeam.appendChild(opt);
    });
  } catch (e) {
    selTeam.innerHTML = '<option value="">Errore squadre</option>';
  }
}

async function extractSingleTeam() {
  const selTeam = document.getElementById('sel-team');
  const teamUrl = selTeam.value;
  const teamName = selTeam.options[selTeam.selectedIndex]?.text;
  const abbr = document.getElementById('single-abbr').value.trim();

  if (!teamUrl || !teamName) {
    showToast('Seleziona una squadra dal menu!', '#f59e0b');
    return;
  }

  const textarea = document.getElementById('output-text');
  textarea.value = `Estrazione rosa in corso per: ${teamName}...\nAttendere qualche istante...`;

  document.getElementById('output-title').textContent = `📄 ${teamName}`;
  document.getElementById('output-ref-badge').textContent = '';

  try {
    const res = await fetch('/api/single/extract', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        team_name: teamName,
        team_url: teamUrl,
        abbr: abbr || null
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Errore estrazione');
    }

    const data = await res.json();
    textarea.value = data.text;
    state.currentOutput = data.text;
    state.currentFilename = data.filename;

    showToast(`● ${teamName} (${data.players_count} calciatori) estratta!`, '#00c853');
  } catch (e) {
    textarea.value = `Errore estrazione:\n${e.message}`;
    showToast(`Errore: ${e.message}`, '#ef4444');
  }
}

// ─────────────────────────────────────────────────────────
//   TOAST FEEDBACK HELPER
// ─────────────────────────────────────────────────────────
function showToast(msg, bg = '#00c853') {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.style.background = bg;
  toast.style.color = bg === '#00c853' || bg === '#f59e0b' ? '#000000' : '#ffffff';
  toast.classList.add('show');
  setTimeout(() => {
    toast.classList.remove('show');
  }, 2500);
}
