"""HTML/JS/CSS template for the results viewer SPA."""

from __future__ import annotations

import json
from typing import Any


def generate_html(results: list[dict[str, Any]]) -> str:
    """Generate a self-contained HTML page for viewing results."""
    safe_json = json.dumps(results).replace("</", "<\\/")
    return _HTML_TEMPLATE.replace("/*__DATA__*/[]", safe_json)


_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Valohai LLM &mdash; Results Viewer</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  background:#f3f4f6;color:#111827;line-height:1.5;min-height:100vh}
.app{max-width:1400px;margin:0 auto;padding:16px}

/* Header */
.header{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;
  margin-bottom:16px;padding:16px 20px;background:#fff;border-radius:10px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.header-left{display:flex;align-items:baseline;gap:12px}
.header h1{font-size:1.25rem;font-weight:700;color:#111827}
.result-count{font-size:.85rem;color:#6b7280}
.tabs{display:flex;gap:4px}
.tab{padding:8px 18px;border:none;border-radius:6px;font-size:.875rem;font-weight:500;
  cursor:pointer;background:#f3f4f6;color:#374151;transition:all .15s}
.tab:hover{background:#e5e7eb}
.tab.active{background:#2563eb;color:#fff}

/* Controls */
.controls-panel{background:#fff;border-radius:10px;padding:16px 20px;margin-bottom:16px;
  box-shadow:0 1px 3px rgba(0,0,0,.08);display:flex;flex-wrap:wrap;gap:16px;align-items:flex-start}
.control-group{display:flex;flex-direction:column;gap:6px}
.control-group>label{font-size:.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:#6b7280}
.control-row{display:flex;gap:16px;align-items:flex-start}
.chip-group{display:flex;flex-wrap:wrap;gap:4px}
.chip{padding:5px 12px;border:1px solid #d1d5db;border-radius:16px;font-size:.8rem;
  cursor:pointer;background:#fff;color:#374151;transition:all .15s;user-select:none}
.chip:hover{border-color:#93c5fd;background:#eff6ff}
.chip.active{background:#2563eb;color:#fff;border-color:#2563eb}
select{padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;font-size:.8rem;
  background:#fff;color:#374151;cursor:pointer}
.toggle-label{display:flex;align-items:center;gap:6px;font-size:.8rem;color:#374151;cursor:pointer;
  font-weight:400;text-transform:none;letter-spacing:normal}
.toggle-label input[type="checkbox"]{accent-color:#2563eb}

/* Table */
.table-section{background:#fff;border-radius:10px;box-shadow:0 1px 3px rgba(0,0,0,.08);overflow:hidden;margin-bottom:16px}
.table-wrapper{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:.85rem}
thead{position:sticky;top:0;z-index:1}
th{background:#f9fafb;padding:10px 14px;text-align:left;font-weight:600;font-size:.75rem;
  text-transform:uppercase;letter-spacing:.05em;color:#6b7280;border-bottom:2px solid #e5e7eb;
  white-space:nowrap}
th.sortable{cursor:pointer;user-select:none}
th.sortable:hover{background:#f3f4f6;color:#111827}
td{padding:8px 14px;border-bottom:1px solid #f3f4f6}
tbody tr:hover{background:#f9fafb}
td.metric{text-align:right;font-variant-numeric:tabular-nums;font-family:"SF Mono",SFMono-Regular,
  Menlo,Consolas,monospace;font-size:.8rem;transition:background .15s}
td.group-name{font-weight:500}
td.count{text-align:right;color:#6b7280}
.sort-ind{font-size:.65rem;margin-left:4px;opacity:.4}
.sort-ind.active{opacity:1;color:#2563eb}

/* Pagination */
.pagination{display:flex;align-items:center;justify-content:space-between;padding:12px 20px;
  border-top:1px solid #e5e7eb;font-size:.8rem;color:#6b7280}
.pagination-btns{display:flex;gap:4px}
.page-btn{padding:4px 12px;border:1px solid #d1d5db;border-radius:4px;font-size:.8rem;
  cursor:pointer;background:#fff;color:#374151;transition:all .15s}
.page-btn:hover:not(:disabled){background:#f3f4f6}
.page-btn:disabled{opacity:.4;cursor:default}
.page-btn.active{background:#2563eb;color:#fff;border-color:#2563eb}

/* Chart */
.chart-section{background:#fff;border-radius:10px;padding:20px;margin-bottom:16px;
  box-shadow:0 1px 3px rgba(0,0,0,.08)}
.chart-section h2{font-size:.9rem;font-weight:600;color:#374151;margin-bottom:12px}
.chart-controls{display:flex;gap:12px;align-items:center;margin-bottom:12px}
.chart-wrapper{position:relative;height:320px}

/* Empty state */
.empty{text-align:center;padding:60px 20px;color:#6b7280}
.empty h2{font-size:1.1rem;margin-bottom:8px;color:#374151}

/* Responsive */
@media(max-width:768px){
  .header{flex-direction:column;align-items:flex-start}
  .controls-panel{flex-direction:column}
}
</style>
</head>
<body>
<div class="app">
  <!-- Header -->
  <header class="header">
    <div class="header-left">
      <h1>Results Viewer</h1>
      <span id="result-count" class="result-count"></span>
    </div>
    <nav class="tabs" id="tabs">
      <button class="tab active" data-view="grouped">Grouped</button>
      <button class="tab" data-view="individual">Individual</button>
    </nav>
  </header>

  <!-- Grouped controls -->
  <section id="grouped-controls" class="controls-panel">
    <div class="control-group">
      <label>Group by</label>
      <div id="group-by-chips" class="chip-group"></div>
    </div>
    <div class="control-group">
      <label>Aggregate</label>
      <select id="agg-select">
        <option value="mean">Mean</option>
        <option value="median">Median</option>
        <option value="min">Min</option>
        <option value="max">Max</option>
        <option value="sum">Sum</option>
        <option value="count">Count</option>
        <option value="stdev">Std Dev</option>
      </select>
    </div>
    <div class="control-group">
      <label>Metrics</label>
      <div id="metric-chips" class="chip-group"></div>
    </div>
    <div class="control-row">
      <div class="control-group">
        <label class="toggle-label"><input type="checkbox" id="colorize-cb" checked> Colorize</label>
      </div>
      <div class="control-group">
        <label>Page size</label>
        <select id="page-size-grouped">
          <option value="25">25</option>
          <option value="50">50</option>
          <option value="100">100</option>
          <option value="0">All</option>
        </select>
      </div>
    </div>
  </section>

  <!-- Individual controls -->
  <section id="individual-controls" class="controls-panel" hidden>
    <div class="control-row">
      <div class="control-group">
        <label>Page size</label>
        <select id="page-size-individual">
          <option value="25">25</option>
          <option value="50">50</option>
          <option value="100">100</option>
          <option value="0">All</option>
        </select>
      </div>
    </div>
  </section>

  <!-- Table -->
  <section class="table-section">
    <div class="table-wrapper">
      <table id="results-table">
        <thead id="thead"></thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
    <div id="pagination" class="pagination" hidden></div>
  </section>

  <!-- Chart -->
  <section id="chart-section" class="chart-section" hidden>
    <h2>Comparison Chart</h2>
    <div class="chart-controls">
      <select id="chart-type-select">
        <option value="bar">Bar</option>
        <option value="horizontalBar">Horizontal Bar</option>
        <option value="line">Line</option>
        <option value="radar">Radar</option>
      </select>
    </div>
    <div class="chart-wrapper">
      <canvas id="chart-canvas"></canvas>
    </div>
  </section>
</div>

<script>
(function(){
"use strict";

/* ======== DATA ======== */
var RESULTS = /*__DATA__*/[];

/* ======== STATE ======== */
var S = {
  view: "grouped",
  groupBy: [],
  agg: "mean",
  metrics: {},
  colorize: true,
  sortCol: null,
  sortDir: "asc",
  page: 1,
  pageSize: 25,
  chartType: "bar"
};

var labelKeys = [];
var metricKeys = [];

/* ======== DOM REFS ======== */
var $thead = document.getElementById("thead");
var $tbody = document.getElementById("tbody");
var $pagination = document.getElementById("pagination");
var $chartSection = document.getElementById("chart-section");
var $chartCanvas = document.getElementById("chart-canvas");
var chartInstance = null;

/* ======== INIT ======== */
function init() {
  var ls = {}, ms = {};
  for (var i = 0; i < RESULTS.length; i++) {
    var r = RESULTS[i];
    if (r.labels) { for (var k in r.labels) ls[k] = 1; }
    if (r.metrics) { for (var k in r.metrics) ms[k] = 1; }
  }
  labelKeys = Object.keys(ls).sort();
  metricKeys = Object.keys(ms).sort();
  for (var i = 0; i < metricKeys.length; i++) S.metrics[metricKeys[i]] = true;
  if (labelKeys.length > 0) S.groupBy = [labelKeys[0]];

  document.getElementById("result-count").textContent = RESULTS.length + " results";
  buildControls();
  bindEvents();
  render();
}

/* ======== AGGREGATION ======== */
var aggFns = {
  mean: function(v) { var s = 0; for (var i = 0; i < v.length; i++) s += v[i]; return s / v.length; },
  median: function(v) {
    var s = v.slice().sort(function(a, b) { return a - b; });
    var m = Math.floor(s.length / 2);
    return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
  },
  min: function(v) { var m = v[0]; for (var i = 1; i < v.length; i++) if (v[i] < m) m = v[i]; return m; },
  max: function(v) { var m = v[0]; for (var i = 1; i < v.length; i++) if (v[i] > m) m = v[i]; return m; },
  sum: function(v) { var s = 0; for (var i = 0; i < v.length; i++) s += v[i]; return s; },
  count: function(v) { return v.length; },
  stdev: function(v) {
    var mean = 0; for (var i = 0; i < v.length; i++) mean += v[i]; mean /= v.length;
    var ss = 0; for (var i = 0; i < v.length; i++) ss += (v[i] - mean) * (v[i] - mean);
    return Math.sqrt(ss / v.length);
  }
};

/* ======== GROUPING ======== */
function computeGrouped() {
  var fn = aggFns[S.agg] || aggFns.mean;
  var groups;
  if (S.groupBy.length === 0) {
    groups = [{ key: "All", results: RESULTS }];
  } else {
    var map = Object.create(null);
    var order = [];
    for (var i = 0; i < RESULTS.length; i++) {
      var r = RESULTS[i];
      var parts = [];
      for (var j = 0; j < S.groupBy.length; j++) {
        parts.push((r.labels || {})[S.groupBy[j]] || "(none)");
      }
      var key = parts.join(" / ");
      if (!(key in map)) { map[key] = []; order.push(key); }
      map[key].push(r);
    }
    groups = [];
    for (var i = 0; i < order.length; i++) {
      groups.push({ key: order[i], results: map[order[i]] });
    }
  }

  var rows = [];
  for (var gi = 0; gi < groups.length; gi++) {
    var g = groups[gi];
    var row = { _group: g.key, _count: g.results.length };
    for (var mi = 0; mi < metricKeys.length; mi++) {
      var m = metricKeys[mi];
      var vals = [];
      for (var ri = 0; ri < g.results.length; ri++) {
        var v = (g.results[ri].metrics || {})[m];
        if (typeof v === "number" && v === v) vals.push(v);
      }
      row[m] = vals.length > 0 ? fn(vals) : null;
    }
    rows.push(row);
  }
  return rows;
}

/* ======== SORTING ======== */
function sortRows(rows, view) {
  if (!S.sortCol) return rows;
  var col = S.sortCol;
  var dir = S.sortDir === "asc" ? 1 : -1;
  var out = rows.slice();
  out.sort(function(a, b) {
    var va, vb;
    if (view === "individual") {
      if (col.indexOf("label_") === 0) {
        var k = col.slice(6);
        va = (a.labels || {})[k]; vb = (b.labels || {})[k];
        va = va == null ? "" : String(va); vb = vb == null ? "" : String(vb);
      } else if (col.indexOf("metric_") === 0) {
        var k = col.slice(7);
        va = (a.metrics || {})[k]; vb = (b.metrics || {})[k];
      }
    } else {
      va = a[col]; vb = b[col];
    }
    if (va == null && vb == null) return 0;
    if (va == null) return 1;
    if (vb == null) return -1;
    if (typeof va === "number" && typeof vb === "number") return (va - vb) * dir;
    return String(va).localeCompare(String(vb)) * dir;
  });
  return out;
}

/* ======== PAGINATION ======== */
function paginate(rows) {
  if (S.pageSize === 0) return rows;
  var start = (S.page - 1) * S.pageSize;
  return rows.slice(start, start + S.pageSize);
}
function totalPages(n) {
  return S.pageSize === 0 ? 1 : Math.ceil(n / S.pageSize) || 1;
}

/* ======== COLORIZATION ======== */
function computeRanges(rows, metrics) {
  var ranges = {};
  for (var i = 0; i < metrics.length; i++) {
    var m = metrics[i];
    var lo = Infinity, hi = -Infinity;
    for (var j = 0; j < rows.length; j++) {
      var v = rows[j][m];
      if (v != null) { if (v < lo) lo = v; if (v > hi) hi = v; }
    }
    ranges[m] = { lo: lo, hi: hi };
  }
  return ranges;
}

function cellStyle(v, lo, hi) {
  if (v == null || lo === hi) return "";
  var t = (v - lo) / (hi - lo);
  var r, g, b;
  if (t < 0.5) {
    var s = t * 2;
    r = Math.round(239 + s * (253 - 239));
    g = Math.round(68 + s * (186 - 68));
    b = Math.round(68 + s * (51 - 68));
  } else {
    var s = (t - 0.5) * 2;
    r = Math.round(253 - s * (253 - 34));
    g = Math.round(186 + s * (197 - 186));
    b = Math.round(51 + s * (94 - 51));
  }
  var textColor = (t < 0.25 || t > 0.8) ? "#fff" : "#1a1a1a";
  return ' style="background:rgb(' + r + "," + g + "," + b + ");color:" + textColor + '"';
}

/* ======== FORMAT ======== */
function fmt(n) {
  if (n == null) return "&mdash;";
  if (Number.isInteger(n)) return String(n);
  var abs = Math.abs(n);
  if (abs >= 100) return n.toFixed(1);
  if (abs >= 1) return n.toFixed(3);
  return n.toFixed(4);
}
function esc(s) {
  s = String(s == null ? "" : s);
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}
function sortInd(col) {
  if (S.sortCol !== col) return '<span class="sort-ind">\u21C5</span>';
  var arrow = S.sortDir === "asc" ? "\u2191" : "\u2193";
  return '<span class="sort-ind active">' + arrow + "</span>";
}

/* ======== RENDER ======== */
function render() {
  requestAnimationFrame(function() {
    if (S.view === "grouped") renderGrouped();
    else renderIndividual();
  });
}

function renderGrouped() {
  var visMetrics = metricKeys.filter(function(m) { return S.metrics[m]; });
  var allRows = computeGrouped();
  var sorted = sortRows(allRows, "grouped");
  var ranges = computeRanges(allRows, visMetrics);
  var pages = totalPages(sorted.length);
  if (S.page > pages) S.page = pages;
  if (S.page < 1) S.page = 1;
  var pageRows = paginate(sorted);

  /* Head */
  var h = '<tr><th class="sortable" data-col="_group">Group' + sortInd("_group") + "</th>";
  h += '<th class="sortable" data-col="_count">Count' + sortInd("_count") + "</th>";
  for (var i = 0; i < visMetrics.length; i++) {
    var m = visMetrics[i];
    h += '<th class="sortable" data-col="' + esc(m) + '">' + esc(m) + sortInd(m) + "</th>";
  }
  h += "</tr>";
  $thead.innerHTML = h;

  /* Body */
  var b = "";
  for (var i = 0; i < pageRows.length; i++) {
    var row = pageRows[i];
    b += "<tr>";
    b += '<td class="group-name">' + esc(row._group) + "</td>";
    b += '<td class="count">' + row._count + "</td>";
    for (var j = 0; j < visMetrics.length; j++) {
      var m = visMetrics[j];
      var v = row[m];
      var cs = S.colorize ? cellStyle(v, ranges[m].lo, ranges[m].hi) : "";
      b += '<td class="metric"' + cs + ">" + fmt(v) + "</td>";
    }
    b += "</tr>";
  }
  $tbody.innerHTML = b;

  renderPagination(sorted.length, pages);

  /* Chart */
  if (visMetrics.length > 0 && typeof Chart !== "undefined") {
    $chartSection.hidden = false;
    renderChart(sorted, visMetrics);
  } else {
    $chartSection.hidden = true;
  }
}

function renderIndividual() {
  var sorted = sortRows(RESULTS, "individual");
  var pages = totalPages(sorted.length);
  if (S.page > pages) S.page = pages;
  if (S.page < 1) S.page = 1;
  var pageRows = paginate(sorted);

  /* Head */
  var h = "<tr>";
  for (var i = 0; i < labelKeys.length; i++) {
    var k = labelKeys[i];
    h += '<th class="sortable" data-col="label_' + esc(k) + '">' + esc(k) + sortInd("label_" + k) + "</th>";
  }
  for (var i = 0; i < metricKeys.length; i++) {
    var k = metricKeys[i];
    h += '<th class="sortable" data-col="metric_' + esc(k) + '">' + esc(k) + sortInd("metric_" + k) + "</th>";
  }
  h += "</tr>";
  $thead.innerHTML = h;

  /* Body */
  var b = "";
  for (var i = 0; i < pageRows.length; i++) {
    var r = pageRows[i];
    b += "<tr>";
    for (var j = 0; j < labelKeys.length; j++) {
      b += "<td>" + esc((r.labels || {})[labelKeys[j]]) + "</td>";
    }
    for (var j = 0; j < metricKeys.length; j++) {
      var v = (r.metrics || {})[metricKeys[j]];
      b += '<td class="metric">' + fmt(v) + "</td>";
    }
    b += "</tr>";
  }
  $tbody.innerHTML = b;

  renderPagination(sorted.length, pages);
  $chartSection.hidden = true;
}

function renderPagination(total, pages) {
  if (pages <= 1) { $pagination.hidden = true; return; }
  $pagination.hidden = false;
  var start = (S.page - 1) * S.pageSize + 1;
  var end = Math.min(S.page * S.pageSize, total);
  var h = '<span>Showing ' + start + "&ndash;" + end + " of " + total + "</span>";
  h += '<div class="pagination-btns">';
  h += '<button class="page-btn" data-page="prev"' + (S.page <= 1 ? " disabled" : "") + '>&laquo; Prev</button>';

  /* Show limited page numbers */
  var lo = Math.max(1, S.page - 2), hi = Math.min(pages, S.page + 2);
  if (lo > 1) h += '<button class="page-btn" data-page="1">1</button>';
  if (lo > 2) h += '<span style="padding:0 4px">&hellip;</span>';
  for (var p = lo; p <= hi; p++) {
    h += '<button class="page-btn' + (p === S.page ? " active" : "") + '" data-page="' + p + '">' + p + "</button>";
  }
  if (hi < pages - 1) h += '<span style="padding:0 4px">&hellip;</span>';
  if (hi < pages) h += '<button class="page-btn" data-page="' + pages + '">' + pages + "</button>";

  h += '<button class="page-btn" data-page="next"' + (S.page >= pages ? " disabled" : "") + '>Next &raquo;</button>';
  h += "</div>";
  $pagination.innerHTML = h;
}

/* ======== CHART ======== */
var CHART_COLORS = [
  "rgba(37,99,235,.75)", "rgba(5,150,105,.75)", "rgba(220,38,38,.75)",
  "rgba(217,119,6,.75)", "rgba(124,58,237,.75)", "rgba(236,72,153,.75)",
  "rgba(14,165,233,.75)", "rgba(168,85,247,.75)"
];

function renderChart(rows, metrics) {
  if (chartInstance) { chartInstance.destroy(); chartInstance = null; }

  /* Limit to 40 groups for readability */
  var data = rows.length > 40 ? rows.slice(0, 40) : rows;
  var labels = data.map(function(r) { return r._group; });
  var type = S.chartType === "horizontalBar" ? "bar" : S.chartType;

  var datasets = metrics.map(function(m, i) {
    return {
      label: m,
      data: data.map(function(r) { return r[m]; }),
      backgroundColor: CHART_COLORS[i % CHART_COLORS.length],
      borderColor: CHART_COLORS[i % CHART_COLORS.length].replace(".75", "1"),
      borderWidth: 1
    };
  });

  chartInstance = new Chart($chartCanvas, {
    type: type,
    data: { labels: labels, datasets: datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: S.chartType === "horizontalBar" ? "y" : "x",
      plugins: {
        legend: { display: metrics.length > 1 }
      },
      scales: type === "radar" ? {} : {
        x: { ticks: { maxRotation: 45, autoSkip: true, maxTicksLimit: 30 } }
      }
    }
  });
}

/* ======== BUILD CONTROLS ======== */
function buildControls() {
  /* Group-by chips */
  var gh = "";
  for (var i = 0; i < labelKeys.length; i++) {
    var k = labelKeys[i];
    var active = S.groupBy.indexOf(k) >= 0 ? " active" : "";
    gh += '<button class="chip' + active + '" data-group-key="' + esc(k) + '">' + esc(k) + "</button>";
  }
  document.getElementById("group-by-chips").innerHTML = gh;

  /* Metric chips */
  var mh = "";
  for (var i = 0; i < metricKeys.length; i++) {
    var k = metricKeys[i];
    var active = S.metrics[k] ? " active" : "";
    mh += '<button class="chip' + active + '" data-metric-key="' + esc(k) + '">' + esc(k) + "</button>";
  }
  document.getElementById("metric-chips").innerHTML = mh;
}

/* ======== EVENTS ======== */
function bindEvents() {
  /* Tab switching */
  document.getElementById("tabs").addEventListener("click", function(e) {
    var btn = e.target.closest(".tab");
    if (!btn) return;
    var view = btn.getAttribute("data-view");
    if (view === S.view) return;
    S.view = view;
    S.sortCol = null; S.sortDir = "asc"; S.page = 1;
    document.querySelectorAll(".tab").forEach(function(t) { t.classList.toggle("active", t === btn); });
    document.getElementById("grouped-controls").hidden = view !== "grouped";
    document.getElementById("individual-controls").hidden = view !== "individual";
    render();
  });

  /* Group-by chips */
  document.getElementById("group-by-chips").addEventListener("click", function(e) {
    var btn = e.target.closest(".chip");
    if (!btn) return;
    var key = btn.getAttribute("data-group-key");
    var idx = S.groupBy.indexOf(key);
    if (idx >= 0) S.groupBy.splice(idx, 1); else S.groupBy.push(key);
    btn.classList.toggle("active");
    S.page = 1; S.sortCol = null;
    render();
  });

  /* Metric chips */
  document.getElementById("metric-chips").addEventListener("click", function(e) {
    var btn = e.target.closest(".chip");
    if (!btn) return;
    var key = btn.getAttribute("data-metric-key");
    S.metrics[key] = !S.metrics[key];
    btn.classList.toggle("active");
    render();
  });

  /* Aggregation */
  document.getElementById("agg-select").addEventListener("change", function(e) {
    S.agg = e.target.value; S.page = 1; render();
  });

  /* Colorize toggle */
  document.getElementById("colorize-cb").addEventListener("change", function(e) {
    S.colorize = e.target.checked; render();
  });

  /* Page size (grouped) */
  document.getElementById("page-size-grouped").addEventListener("change", function(e) {
    S.pageSize = parseInt(e.target.value, 10); S.page = 1; render();
  });

  /* Page size (individual) */
  document.getElementById("page-size-individual").addEventListener("change", function(e) {
    S.pageSize = parseInt(e.target.value, 10); S.page = 1; render();
  });

  /* Chart type */
  document.getElementById("chart-type-select").addEventListener("change", function(e) {
    S.chartType = e.target.value; render();
  });

  /* Sort headers (delegated on table) */
  document.getElementById("results-table").addEventListener("click", function(e) {
    var th = e.target.closest("th.sortable");
    if (!th) return;
    var col = th.getAttribute("data-col");
    if (S.sortCol === col) {
      S.sortDir = S.sortDir === "asc" ? "desc" : "asc";
    } else {
      S.sortCol = col; S.sortDir = "asc";
    }
    S.page = 1;
    render();
  });

  /* Pagination clicks */
  $pagination.addEventListener("click", function(e) {
    var btn = e.target.closest(".page-btn");
    if (!btn || btn.disabled) return;
    var p = btn.getAttribute("data-page");
    if (p === "prev") S.page--;
    else if (p === "next") S.page++;
    else S.page = parseInt(p, 10);
    render();
  });
}

/* ======== START ======== */
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}

})();
</script>
</body>
</html>
"""
