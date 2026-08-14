from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from coa_workbench.collector.source_health import build_source_health
from coa_workbench.storage import apply_migrations

SOURCE_HEALTH_HTML = r'''<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Source & Analysis Health — CoA Raid Intelligence</title>
  <style>
    :root {
      --bg:#0b1020; --panel:#131b2f; --panel2:#18233b; --line:#2a3754;
      --text:#edf2ff; --muted:#9ba9c5; --accent:#7c9cff; --ok:#72d6a0;
      --danger:#ff7f91; --warn:#ffd37a;
    }
    * { box-sizing:border-box; }
    body { margin:0; background:var(--bg); color:var(--text); font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif; }
    header { position:sticky; top:0; z-index:2; display:flex; align-items:center; gap:18px; padding:16px 22px; background:rgba(11,16,32,.96); border-bottom:1px solid var(--line); }
    header a { color:var(--accent); text-decoration:none; font-weight:700; }
    header h1 { margin:0; font-size:19px; }
    header .muted { margin-left:auto; }
    main { max-width:1500px; margin:0 auto; padding:22px; }
    .muted { color:var(--muted); }
    .metrics { display:grid; grid-template-columns:repeat(5,minmax(130px,1fr)); gap:12px; margin-bottom:18px; }
    .metric,.panel { border:1px solid var(--line); background:var(--panel); border-radius:12px; }
    .metric { padding:14px; }
    .metric strong { display:block; margin-top:3px; font-size:26px; }
    .panel { padding:16px; margin-bottom:16px; overflow:auto; }
    .panel-head { display:flex; align-items:center; gap:12px; margin-bottom:12px; }
    .panel h2 { margin:0; font-size:16px; }
    button { margin-left:auto; border:1px solid var(--line); background:var(--panel2); color:var(--text); padding:8px 12px; border-radius:8px; cursor:pointer; }
    button:hover { border-color:var(--accent); }
    table { width:100%; border-collapse:collapse; min-width:980px; }
    th,td { padding:10px 9px; border-bottom:1px solid var(--line); text-align:left; vertical-align:top; }
    th { color:var(--muted); font-size:12px; font-weight:700; }
    code { color:#c8d4ff; font-size:12px; }
    .badge { display:inline-block; border:1px solid var(--line); border-radius:999px; padding:3px 8px; font-size:12px; white-space:nowrap; }
    .badge.ok { color:var(--ok); border-color:rgba(114,214,160,.45); }
    .badge.warn { color:var(--warn); border-color:rgba(255,211,122,.45); }
    .badge.danger { color:var(--danger); border-color:rgba(255,127,145,.45); }
    .badge.neutral { color:var(--muted); }
    .dims { display:flex; flex-wrap:wrap; gap:5px; max-width:340px; }
    .dim { border:1px solid var(--line); border-radius:6px; padding:2px 6px; color:var(--muted); font-size:11px; }
    .empty { padding:18px; text-align:center; color:var(--muted); }
    .error { border-color:rgba(255,127,145,.45); color:var(--danger); }
    .privacy { font-size:12px; color:var(--muted); }
    @media (max-width:900px) { .metrics { grid-template-columns:repeat(2,1fr); } header .muted { display:none; } }
  </style>
</head>
<body>
<header>
  <a href="/">← Конструктор рейда</a>
  <h1>Source & Analysis Health</h1>
  <span class="muted">Состояние источников, изменений и переанализа</span>
</header>
<main>
  <div id="error" class="panel error" hidden></div>
  <section class="metrics" id="metrics">
    <div class="metric"><span class="muted">Источники</span><strong>—</strong></div>
    <div class="metric"><span class="muted">С данными</span><strong>—</strong></div>
    <div class="metric"><span class="muted">Открытые изменения</span><strong>—</strong></div>
    <div class="metric"><span class="muted">Переанализ</span><strong>—</strong></div>
    <div class="metric"><span class="muted">Проблемы доступа</span><strong>—</strong></div>
  </section>

  <section class="panel">
    <div class="panel-head">
      <div>
        <h2>Источники</h2>
        <div class="muted">Только структурное состояние. Raw payload и значения dimensions здесь не показываются.</div>
      </div>
      <button id="refresh" type="button">Обновить</button>
    </div>
    <div id="endpoints" class="empty">Загрузка…</div>
  </section>

  <section class="panel">
    <div class="panel-head">
      <div>
        <h2>Последние изменения</h2>
        <div class="muted">Новые endpoint/schema/dimension observations без раскрытия исходных значений.</div>
      </div>
    </div>
    <div id="changes" class="empty">Загрузка…</div>
  </section>

  <section class="panel privacy">
    Эта страница читает только локальный DuckDB. Cookies, request headers, HAR, raw response bodies и значения domain dimensions в API Source Health не включаются.
  </section>
</main>
<script>
const esc = (value) => String(value ?? "").replace(/[&<>"']/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[ch]);
const when = (value) => {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? esc(value) : esc(date.toLocaleString("ru-RU"));
};
const state = {
  observed:["Наблюдается","ok"], changed:["Есть изменения","warn"],
  acquisition_problem:["Проблема доступа","danger"], registered:["Зарегистрирован","neutral"]
};
const severityClass = value => value === "error" || value === "critical" ? "danger" : value === "warning" ? "warn" : "neutral";

function renderMetrics(summary) {
  const values = [
    ["Источники", summary.endpoint_count],
    ["С данными", summary.captured_endpoint_count],
    ["Открытые изменения", summary.open_change_event_count],
    ["Переанализ", summary.pending_reanalysis_request_count],
    ["Проблемы доступа", summary.acquisition_problem_endpoint_count],
  ];
  document.getElementById("metrics").innerHTML = values.map(([label,value]) =>
    `<div class="metric"><span class="muted">${esc(label)}</span><strong>${esc(value)}</strong></div>`
  ).join("");
}

function dimensions(snapshot) {
  const counts = snapshot?.dimension_value_counts || {};
  const rows = Object.entries(counts);
  if (!rows.length) return '<span class="muted">—</span>';
  return `<div class="dims">${rows.map(([name,count]) => `<span class="dim">${esc(name)}: ${esc(count)}</span>`).join("")}</div>`;
}

function renderEndpoints(items) {
  const root = document.getElementById("endpoints");
  if (!items.length) { root.className = "empty"; root.textContent = "Источники пока не зарегистрированы."; return; }
  root.className = "";
  root.innerHTML = `<table><thead><tr>
    <th>Источник</th><th>Состояние</th><th>Контракт</th><th>Captures</th><th>Последнее получение</th><th>Dimensions</th><th>Изменения</th>
  </tr></thead><tbody>${items.map(item => {
    const meta = state[item.health_state] || [item.health_state,"neutral"];
    const acq = item.latest_acquisition;
    const last = acq ? `HTTP ${esc(acq.http_status ?? "—")} · ${esc(acq.capture_mode)} · ${esc(acq.outcome)}<br><span class="muted">${when(acq.observed_at)}</span>` : '<span class="muted">нет</span>';
    return `<tr>
      <td><strong>${esc(item.logical_name || item.endpoint_code)}</strong><br><code>${esc(item.endpoint_code)}</code></td>
      <td><span class="badge ${meta[1]}">${esc(meta[0])}</span></td>
      <td><code>${esc(item.method || "")} ${esc(item.route_template || "")}</code></td>
      <td>${esc(item.capture_count)}</td>
      <td>${last}</td>
      <td>${dimensions(item.latest_schema)}</td>
      <td>${item.open_change_count ? `<span class="badge warn">${esc(item.open_change_count)}</span>` : '<span class="muted">0</span>'}</td>
    </tr>`;
  }).join("")}</tbody></table>`;
}

function renderChanges(items) {
  const root = document.getElementById("changes");
  if (!items.length) { root.className = "empty"; root.textContent = "Изменений пока нет."; return; }
  root.className = "";
  root.innerHTML = `<table><thead><tr><th>Время</th><th>Источник</th><th>Тип</th><th>Severity</th><th>Статус</th></tr></thead><tbody>${items.map(item =>
    `<tr><td>${when(item.observed_at)}</td><td><code>${esc(item.endpoint_code)}</code></td><td>${esc(item.change_type)}</td><td><span class="badge ${severityClass(item.severity)}">${esc(item.severity)}</span></td><td>${esc(item.status)}</td></tr>`
  ).join("")}</tbody></table>`;
}

async function refresh() {
  const button = document.getElementById("refresh");
  const error = document.getElementById("error");
  button.disabled = true;
  error.hidden = true;
  try {
    const response = await fetch("/api/source-health", {headers:{"Accept":"application/json"}});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    renderMetrics(payload.summary);
    renderEndpoints(payload.endpoints || []);
    renderChanges(payload.recent_changes || []);
  } catch (err) {
    error.hidden = false;
    error.textContent = `Не удалось загрузить Source Health: ${err.message}`;
  } finally {
    button.disabled = false;
  }
}

document.getElementById("refresh").addEventListener("click", refresh);
refresh();
</script>
</body>
</html>
'''


def install_source_health_routes(
    app: FastAPI,
    *,
    database_path: Path,
    migrations_dir: Path,
) -> None:
    """Install privacy-safe localhost Source & Analysis Health routes."""

    @app.get("/source-health", response_class=HTMLResponse, include_in_schema=False)
    def source_health_page() -> str:
        return SOURCE_HEALTH_HTML

    @app.get("/api/source-health")
    def source_health_api() -> dict[str, object]:
        try:
            apply_migrations(database_path, migrations_dir)
            return build_source_health(database_path)
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Source health is unavailable") from exc


__all__ = ["SOURCE_HEALTH_HTML", "install_source_health_routes"]
