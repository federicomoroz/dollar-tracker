import html as html_module


def _rate_rows(rates) -> str:
    if not rates:
        return '<tr><td colspan="3" style="color:var(--dim)">SIN DATOS AUN — PRIMER FETCH PENDIENTE</td></tr>'
    rows = ""
    for r in rates:
        buy = f"${r.buy:,.2f}" if r.buy else "—"
        rows += (
            f'<tr>'
            f'<td class="rate-name">{html_module.escape(r.name)}</td>'
            f'<td class="rate-sell">${r.sell:,.2f}</td>'
            f'<td class="rate-buy">{buy}</td>'
            f'</tr>'
        )
    return rows


def _rate_options(rates) -> str:
    if not rates:
        return '<option value="blue">blue</option>'
    return "".join(
        f'<option value="{html_module.escape(r.type)}">{html_module.escape(r.name)}</option>'
        for r in rates
    )


LANDING_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DOLLAR TRACKER // FEDERICO MOROZ</title>
  <link rel="icon" type="image/svg+xml" href="/static/favicon.svg">
  <link href="https://fonts.googleapis.com/css2?family=VT323&family=Share+Tech+Mono&display=swap" rel="stylesheet">
  <style>
    :root {
      --green: #15ff00; --dim: #0a8f00; --bright: #39ff14;
      --red: #ff4444; --bg: #080808; --glow: 0 0 8px #15ff00, 0 0 2px #15ff00;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html, body { background: var(--bg); color: var(--green); font-family: 'Share Tech Mono', monospace; min-height: 100vh; }
    .terminal { max-width: 860px; margin: 0 auto; padding: 40px 24px 60px; }
    .title { font-family: 'VT323', monospace; font-size: clamp(2.2rem, 6vw, 3.2rem); color: var(--bright); text-shadow: var(--glow); letter-spacing: 4px; }
    .subtitle { font-size: 0.75rem; color: var(--dim); letter-spacing: 2px; margin-top: 4px; margin-bottom: 28px; text-transform: uppercase; }
    hr { border: none; border-top: 1px solid var(--dim); margin: 20px 0; }
    .line { margin: 5px 0; font-size: 0.9rem; }
    .label { color: var(--dim); }
    .value { color: var(--bright); }
    .ok .value::before { content: "[OK] "; color: var(--green); }
    .section-title { font-family: 'VT323', monospace; font-size: 1.4rem; color: var(--bright); letter-spacing: 2px; margin-bottom: 10px; }
    .box { border: 1px solid var(--dim); background: rgba(21,255,0,0.02); padding: 16px 20px; margin: 20px 0; }
    table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
    th { color: var(--dim); text-transform: uppercase; font-size: 0.72rem; letter-spacing: 1px; padding: 4px 8px; border-bottom: 1px solid var(--dim); text-align: left; }
    td { padding: 5px 8px; border-bottom: 1px solid rgba(21,255,0,0.08); }
    .rate-name { color: var(--green); }
    .rate-sell { color: var(--bright); font-weight: bold; }
    .rate-buy  { color: var(--dim); }
    .actions { display: flex; gap: 14px; flex-wrap: wrap; margin-top: 28px; }
    .btn { border: 1px solid var(--green); color: var(--green); background: transparent; padding: 8px 20px; font-family: 'Share Tech Mono', monospace; font-size: 0.85rem; cursor: pointer; text-decoration: none; letter-spacing: 1px; text-transform: uppercase; transition: all 0.1s; }
    .btn:hover { background: rgba(21,255,0,0.1); color: var(--bright); }
    .btn.primary { background: rgba(21,255,0,0.08); border-color: var(--bright); color: var(--bright); }
    .btn.danger { border-color: var(--red); color: var(--red); font-size: 0.72rem; padding: 3px 10px; }
    .btn.danger:hover { background: rgba(255,68,68,0.1); }
    .cursor { display: inline-block; width: 10px; height: 1em; background: var(--green); animation: blink 1s step-end infinite; vertical-align: text-bottom; margin-left: 4px; }
    @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
    .footer { margin-top: 40px; font-size: 0.72rem; color: var(--dim); }
    .footer a { color: var(--dim); }

    /* ── Forms ──────────────────────────────────────────────────────── */
    .form-row { display: flex; align-items: center; gap: 10px; margin: 8px 0; flex-wrap: wrap; }
    .form-row label { color: var(--dim); font-size: 0.78rem; letter-spacing: 1px; min-width: 90px; text-transform: uppercase; }
    .form-row input, .form-row select {
      background: rgba(21,255,0,0.04); border: 1px solid var(--dim);
      color: var(--green); font-family: 'Share Tech Mono', monospace;
      font-size: 0.85rem; padding: 5px 10px; outline: none; flex: 1; min-width: 180px;
    }
    .form-row input:focus, .form-row select:focus { border-color: var(--bright); }
    .form-row select option { background: #080808; }
    .form-hint { font-size: 0.7rem; color: var(--dim); margin: 0 0 8px 100px; }
    .msg { font-size: 0.8rem; margin-top: 8px; padding: 5px 10px; min-height: 1.4em; }
    .msg.ok  { color: var(--bright); border-left: 2px solid var(--bright); }
    .msg.err { color: var(--red);    border-left: 2px solid var(--red); }

    /* ── Subscription list items ────────────────────────────────────── */
    .sub-list { margin-top: 4px; }
    .sub-item { display: flex; align-items: center; justify-content: space-between; padding: 7px 0; border-bottom: 1px solid rgba(21,255,0,0.06); gap: 8px; flex-wrap: wrap; }
    .sub-email { color: var(--bright); font-size: 0.85rem; }
    .sub-meta  { color: var(--dim); font-size: 0.72rem; }
    .sub-empty { color: var(--dim); font-size: 0.8rem; padding: 8px 0; display: block; }
    .tag { display: inline-block; border: 1px solid var(--dim); color: var(--dim); font-size: 0.68rem; padding: 1px 6px; letter-spacing: 1px; margin-left: 5px; text-transform: uppercase; }
    .list-label { font-size: 0.72rem; color: var(--dim); margin: 14px 0 6px; letter-spacing: 1px; text-transform: uppercase; }
  </style>
</head>
<body>
<div class="terminal">

  <div class="title">DOLLAR TRACKER</div>
  <div class="subtitle">BUILT BY FEDERICO MOROZ &mdash; BACKEND PORTFOLIO PROJECT</div>

  <div class="line ok"><span class="label">SYSTEM STATUS &nbsp;&nbsp;&nbsp;</span><span class="value">ONLINE</span></div>
  <div class="line ok"><span class="label">DATABASE &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span><span class="value">CONNECTED</span></div>
  <div class="line ok"><span class="label">API VERSION &nbsp;&nbsp;&nbsp;&nbsp;</span><span class="value">1.0.0</span></div>
  <div class="line"><span class="label">SESSION UPTIME &nbsp;</span><span class="value" id="uptime">00:00:00</span></div>

  <hr>

  <!-- ── RATES TABLE ──────────────────────────────────────────────────────── -->
  <div class="box">
    <div class="section-title">&gt; COTIZACIONES ACTUALES</div>
    <div class="line" style="font-size:0.72rem;color:var(--dim);margin-bottom:8px">
      Ultima actualizacion: {{LAST_UPDATED}}
    </div>
    <table>
      <thead><tr><th>Tipo</th><th>Venta</th><th>Compra</th></tr></thead>
      <tbody>{{RATE_ROWS}}</tbody>
    </table>
  </div>

  <div class="actions">
    <a class="btn primary" href="/docs">&gt; API DOCS</a>
    <a class="btn" href="/rates/current">&gt; JSON</a>
    <button class="btn" id="fetch-btn" onclick="manualFetch()">&gt; FETCH AHORA</button>
  </div>

  <hr>

  <!-- ── PRICE ALERTS ─────────────────────────────────────────────────────── -->
  <div class="box">
    <div class="section-title">&gt; ALERTAS DE PRECIO</div>
    <p class="line" style="color:var(--dim);font-size:0.78rem;margin-bottom:14px">
      Recibis un email cuando el precio supera o cae por debajo de tus umbrales.
    </p>

    <form id="alert-form" onsubmit="submitAlert(event)">
      <div class="form-row">
        <label>EMAIL</label>
        <input type="email" id="a-email" placeholder="tu@email.com" required autocomplete="email">
      </div>
      <div class="form-row">
        <label>TIPO</label>
        <select id="a-type">{{RATE_OPTIONS}}</select>
      </div>
      <div class="form-row">
        <label>MIN $</label>
        <input type="number" id="a-min" placeholder="ej: 900  (opcional)" step="0.01" min="0">
      </div>
      <div class="form-row">
        <label>MAX $</label>
        <input type="number" id="a-max" placeholder="ej: 1400  (opcional)" step="0.01" min="0">
      </div>
      <p class="form-hint">Al menos uno de los dos umbrales es requerido.</p>
      <div class="form-row" style="margin-top:6px">
        <button class="btn primary" type="submit">&gt; REGISTRAR ALERTA</button>
      </div>
      <div id="alert-msg" class="msg"></div>
    </form>

    <div class="list-label">alertas registradas</div>
    <div class="sub-list" id="alerts-list">
      <span class="sub-empty">Cargando...</span>
    </div>
  </div>

  <!-- ── PERIODIC REPORTS ─────────────────────────────────────────────────── -->
  <div class="box">
    <div class="section-title">&gt; REPORTES PERIODICOS</div>
    <p class="line" style="color:var(--dim);font-size:0.78rem;margin-bottom:14px">
      Recibis un resumen con todas las cotizaciones y estadisticas de las ultimas 24 h.
    </p>

    <form id="report-form" onsubmit="submitReport(event)">
      <div class="form-row">
        <label>EMAIL</label>
        <input type="email" id="r-email" placeholder="tu@email.com" required autocomplete="email">
      </div>
      <div class="form-row">
        <label>FRECUENCIA</label>
        <select id="r-freq">
          <option value="hourly">Cada hora</option>
          <option value="daily" selected>Diario</option>
          <option value="weekly">Semanal</option>
        </select>
      </div>
      <div class="form-row" style="margin-top:6px">
        <button class="btn primary" type="submit">&gt; SUSCRIBIRSE</button>
      </div>
      <div id="report-msg" class="msg"></div>
    </form>

    <div class="list-label">suscripciones activas</div>
    <div class="sub-list" id="reports-list">
      <span class="sub-empty">Cargando...</span>
    </div>
  </div>

  <hr>
  <div class="line"><span style="color:var(--dim)">&gt; AWAITING INPUT</span><span class="cursor"></span></div>
  <div class="footer" style="margin-top:24px">
    SOURCE &mdash; <a href="https://github.com/federicomoroz/dollar-tracker">github.com/federicomoroz/dollar-tracker</a>
    &nbsp;|&nbsp; DATA: <a href="https://dolarapi.com">dolarapi.com</a>
  </div>
</div>

<script>
  // ── Uptime ────────────────────────────────────────────────────────────────
  const t0 = Date.now();
  setInterval(() => {
    const s = Math.floor((Date.now() - t0) / 1000);
    const p = n => String(n).padStart(2, '0');
    document.getElementById('uptime').textContent =
      p(Math.floor(s / 3600)) + ':' + p(Math.floor((s % 3600) / 60)) + ':' + p(s % 60);
  }, 1000);

  // ── Manual fetch ──────────────────────────────────────────────────────────
  async function manualFetch() {
    const btn = document.getElementById('fetch-btn');
    btn.textContent = '> FETCHING...';
    btn.disabled = true;
    try {
      const res = await fetch('/rates/fetch', { method: 'POST' });
      const data = await res.json();
      btn.textContent = `> [OK] ${data.length} TIPOS ACTUALIZADOS`;
      setTimeout(() => location.reload(), 1400);
    } catch {
      btn.textContent = '> ERROR';
      setTimeout(() => { btn.textContent = '> FETCH AHORA'; btn.disabled = false; }, 2000);
    }
  }

  // ── Feedback helper ───────────────────────────────────────────────────────
  function showMsg(elId, text, isOk) {
    const el = document.getElementById(elId);
    el.className = 'msg ' + (isOk ? 'ok' : 'err');
    el.textContent = (isOk ? '[OK] ' : '[ERR] ') + text;
    if (isOk) setTimeout(() => { el.textContent = ''; el.className = 'msg'; }, 4000);
  }

  // ── Alerts ────────────────────────────────────────────────────────────────
  async function loadAlerts() {
    const list = document.getElementById('alerts-list');
    try {
      const data = await fetch('/alerts').then(r => r.json());
      if (!data.length) {
        list.innerHTML = '<span class="sub-empty">Sin alertas registradas.</span>';
        return;
      }
      list.innerHTML = data.map(a => `
        <div class="sub-item">
          <div>
            <span class="sub-email">${a.email}</span>
            <span class="tag">${a.rate_type}</span>
            ${a.min_threshold != null ? `<span class="tag">MIN $${a.min_threshold.toLocaleString('es-AR')}</span>` : ''}
            ${a.max_threshold != null ? `<span class="tag">MAX $${a.max_threshold.toLocaleString('es-AR')}</span>` : ''}
          </div>
          <div style="display:flex;align-items:center;gap:10px">
            <span class="sub-meta">${a.active ? 'ACTIVA' : 'INACTIVA'}</span>
            <button class="btn danger" onclick="deleteAlert(${a.id})">&gt; DEL</button>
          </div>
        </div>
      `).join('');
    } catch {
      list.innerHTML = '<span class="sub-empty" style="color:var(--red)">Error al cargar alertas.</span>';
    }
  }

  async function submitAlert(e) {
    e.preventDefault();
    const email        = document.getElementById('a-email').value;
    const rate_type    = document.getElementById('a-type').value;
    const minRaw       = document.getElementById('a-min').value;
    const maxRaw       = document.getElementById('a-max').value;
    const min_threshold = minRaw !== '' ? parseFloat(minRaw) : null;
    const max_threshold = maxRaw !== '' ? parseFloat(maxRaw) : null;

    if (min_threshold === null && max_threshold === null) {
      showMsg('alert-msg', 'Ingresa al menos un umbral (min o max).', false);
      return;
    }
    try {
      const res = await fetch('/alerts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, rate_type, min_threshold, max_threshold }),
      });
      if (res.ok) {
        showMsg('alert-msg', 'Alerta registrada.', true);
        e.target.reset();
        loadAlerts();
      } else {
        const err = await res.json();
        showMsg('alert-msg', err.detail || 'Error al registrar.', false);
      }
    } catch {
      showMsg('alert-msg', 'Error de red.', false);
    }
  }

  async function deleteAlert(id) {
    await fetch(`/alerts/${id}`, { method: 'DELETE' });
    loadAlerts();
  }

  // ── Reports ───────────────────────────────────────────────────────────────
  async function loadReports() {
    const list = document.getElementById('reports-list');
    try {
      const data = await fetch('/reports').then(r => r.json());
      if (!data.length) {
        list.innerHTML = '<span class="sub-empty">Sin suscripciones activas.</span>';
        return;
      }
      const fmtDate = iso => iso ? new Date(iso).toLocaleDateString('es-AR', { day:'2-digit', month:'2-digit', year:'numeric', hour:'2-digit', minute:'2-digit' }) : 'pendiente';
      list.innerHTML = data.map(r => `
        <div class="sub-item">
          <div>
            <span class="sub-email">${r.email}</span>
            <span class="tag">${r.frequency.toUpperCase()}</span>
          </div>
          <div style="display:flex;align-items:center;gap:10px">
            <span class="sub-meta">ULTIMO: ${fmtDate(r.last_sent)}</span>
            <button class="btn danger" onclick="deleteReport(${r.id})">&gt; DEL</button>
          </div>
        </div>
      `).join('');
    } catch {
      list.innerHTML = '<span class="sub-empty" style="color:var(--red)">Error al cargar reportes.</span>';
    }
  }

  async function submitReport(e) {
    e.preventDefault();
    const email     = document.getElementById('r-email').value;
    const frequency = document.getElementById('r-freq').value;
    try {
      const res = await fetch('/reports', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, frequency }),
      });
      if (res.ok) {
        showMsg('report-msg', 'Suscripcion registrada.', true);
        e.target.reset();
        loadReports();
      } else {
        const err = await res.json();
        showMsg('report-msg', err.detail || 'Error al registrar.', false);
      }
    } catch {
      showMsg('report-msg', 'Error de red.', false);
    }
  }

  async function deleteReport(id) {
    await fetch(`/reports/${id}`, { method: 'DELETE' });
    loadReports();
  }

  // ── Init ──────────────────────────────────────────────────────────────────
  loadAlerts();
  loadReports();
</script>
</body>
</html>"""


def render_landing(rates) -> str:
    rows    = _rate_rows(rates)
    options = _rate_options(rates)
    last    = rates[0].fetched_at.strftime("%d/%m/%Y %H:%M") + " UTC" if rates else "nunca"
    return (
        LANDING_HTML
        .replace("{{RATE_ROWS}}",     rows)
        .replace("{{LAST_UPDATED}}", last)
        .replace("{{RATE_OPTIONS}}", options)
    )
