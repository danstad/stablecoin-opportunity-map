// charts.js — reusable Plot + D3 chart factories for the Stablecoin
// Opportunity Map static site. All factories return a DOM node ready for
// ojs to mount. No in-figure titles per content-standards rule.

import {PLOT_STYLE, SERIF_FONT, COLOR_FATF, COLOR_FDI, COLOR_AMLD} from "./palette.js";

// -----------------------------------------------------------------------
// 1. World choropleth — composite SOS, viridis fill.
// -----------------------------------------------------------------------
export function choropleth(Plot, world, sosByIso3, {height = 460} = {}) {
  // sosByIso3: Map<iso3, {name, sos_composite, rank_composite}>
  // world: TopoJSON FeatureCollection (Natural Earth 110m, properties.iso_a3 / ISO_A3)
  return Plot.plot({
    style: PLOT_STYLE,
    height,
    projection: "equal-earth",
    color: {
      scheme: "viridis",
      legend: true,
      label: "Composite SOS",
      domain: [0, 30]
    },
    marks: [
      Plot.geo(world, {
        fill: (d) => {
          const props = d.properties || {};
          const iso = props.ISO_A3 || props.iso_a3 || props.adm0_a3;
          const row = sosByIso3.get(iso);
          return row && row.sos_composite != null ? row.sos_composite : null;
        },
        stroke: "#ffffff",
        strokeWidth: 0.4,
        title: (d) => {
          const props = d.properties || {};
          const iso = props.ISO_A3 || props.iso_a3 || props.adm0_a3;
          const row = sosByIso3.get(iso);
          if (!row) return props.NAME || iso || "";
          const sos = row.sos_composite != null ? row.sos_composite.toFixed(2) : "—";
          const r = row.rank_composite != null ? Math.round(row.rank_composite) : "—";
          return `${row.name || iso}\nSOS: ${sos}\nRank: ${r}`;
        }
      }),
      Plot.sphere({stroke: "#cfcfcf", strokeWidth: 0.6})
    ]
  });
}

// -----------------------------------------------------------------------
// 2. Three-pronged decomposition — country bar vs sample-median bar.
// -----------------------------------------------------------------------
export function decompositionBars(Plot, htl, country, median, {height = 260} = {}) {
  const rows = [];
  const safe = (v) => (v == null || Number.isNaN(+v)) ? 0 : +v;
  for (const [key, label, color] of [
    ["sos_fatf", "FATF",  COLOR_FATF],
    ["sos_fdi",  "FDI",   COLOR_FDI],
    ["sos_amld", "AMLD",  COLOR_AMLD]
  ]) {
    rows.push({component: label, kind: country.name || country.iso3 || "Country", value: safe(country[key]), color});
    rows.push({component: label, kind: "Sample median",                              value: safe(median[key]),  color: "#bbbbbb"});
  }
  return Plot.plot({
    style: PLOT_STYLE,
    height,
    marginLeft: 70,
    marginRight: 20,
    x: {label: "SOS contribution", grid: true},
    y: {label: null, padding: 0.18},
    fy: {label: null},
    color: {legend: false},
    marks: [
      Plot.barX(rows, {
        x: "value",
        y: "kind",
        fy: "component",
        fill: "color",
        sort: {y: null}
      }),
      Plot.text(rows, {
        x: "value",
        y: "kind",
        fy: "component",
        text: (d) => d.value.toFixed(2),
        dx: 6,
        textAnchor: "start",
        fontFamily: SERIF_FONT
      }),
      Plot.ruleX([0])
    ]
  });
}

// -----------------------------------------------------------------------
// 3. Top corridors bar chart.
// -----------------------------------------------------------------------
export function corridorBars(Plot, rows, {height = 260} = {}) {
  if (!rows || rows.length === 0) {
    const div = document.createElement("div");
    div.style.fontStyle = "italic";
    div.style.color = "#666";
    div.textContent = "No corridor data available.";
    return div;
  }
  return Plot.plot({
    style: PLOT_STYLE,
    height,
    marginLeft: 130,
    x: {label: "Friction-weighted contribution (USD × derisking intensity)", grid: true},
    y: {label: null},
    color: {
      type: "ordinal",
      domain: [false, true],
      range: ["#bbbbbb", COLOR_FDI],
      legend: true,
      label: "Derisked corridor"
    },
    marks: [
      Plot.barX(rows, {
        x: "contribution",
        y: "partner_name",
        fill: "derisked",
        sort: {y: "x", reverse: true}
      }),
      Plot.ruleX([0])
    ]
  });
}

// -----------------------------------------------------------------------
// 4. Quadrant scatter (feasibility filter view).
// -----------------------------------------------------------------------
export function quadrantScatter(Plot, sos, {height = 460} = {}) {
  const data = sos.filter(d => d.kaopen_score != null && d.infrastructure_score != null);
  return Plot.plot({
    style: PLOT_STYLE,
    height,
    grid: true,
    x: {label: "Capital openness (Chinn-Ito, 0–1)", domain: [-0.05, 1.05]},
    y: {label: "Infrastructure readiness (0–1)",     domain: [-0.05, 1.05]},
    r: {range: [2, 16]},
    color: {scheme: "viridis", label: "Composite SOS", legend: true},
    marks: [
      Plot.ruleX([0.5], {strokeOpacity: 0.4, strokeDasharray: "3,3"}),
      Plot.ruleY([0.5], {strokeOpacity: 0.4, strokeDasharray: "3,3"}),
      Plot.dot(data, {
        x: "kaopen_score",
        y: "infrastructure_score",
        r: (d) => Math.max(d.sos_composite || 0, 0.5),
        fill: "sos_composite",
        stroke: "#1a1a1a",
        strokeWidth: 0.4,
        title: (d) => `${d.name || d.iso3}\nSOS: ${(d.sos_composite ?? 0).toFixed(2)}\n${d.quadrant_label || ""}`
      })
    ]
  });
}

// -----------------------------------------------------------------------
// 5. Product treemap — D3 hierarchy (gives full tooltip control).
// -----------------------------------------------------------------------
export function productTreemap(d3, rows, {width = 880, height = 460} = {}) {
  // Build a 2-level hierarchy: root -> hs_section -> hs4 leaf.
  const sections = d3.group(rows, (r) => r.hs_section || "Other");
  const root = {
    name: "root",
    children: Array.from(sections, ([k, v]) => ({
      name: k,
      children: v.map((r) => ({
        name: r.hs4,
        value: Math.max(+r.exposure || 0, 1),  // d3 treemap requires positive values
        sos: r.sos,
        pci_std: r.pci_std,
        hs_section: r.hs_section
      }))
    }))
  };

  const h = d3.hierarchy(root)
    .sum((d) => d.value || 0)
    .sort((a, b) => (b.value || 0) - (a.value || 0));

  d3.treemap()
    .size([width, height])
    .paddingInner(1)
    .paddingTop(14)
    .paddingOuter(2)
    .round(true)(h);

  // SOS color scale (viridis); fallback grey for null.
  const sosVals = rows.map((r) => r.sos).filter((s) => s != null && !Number.isNaN(+s));
  const sosMin = sosVals.length ? Math.min(0, d3.min(sosVals)) : 0;
  const sosMax = sosVals.length ? Math.max(d3.max(sosVals), 0.001) : 1;
  const color = d3.scaleSequential(d3.interpolateViridis).domain([sosMin, sosMax]);

  const wrap = document.createElement("div");
  wrap.style.position = "relative";
  wrap.style.fontFamily = SERIF_FONT;

  const svg = d3.create("svg")
    .attr("viewBox", `0 0 ${width} ${height}`)
    .attr("width",  "100%")
    .style("max-width", "100%")
    .style("height",  "auto")
    .style("font-family", SERIF_FONT);

  // Tooltip element.
  const tooltip = document.createElement("div");
  tooltip.className = "treemap-tooltip";
  tooltip.style.display = "none";
  wrap.appendChild(tooltip);

  // Section headers (parent groups).
  const sectionsG = svg.append("g")
    .selectAll("g")
    .data(h.children || [])
    .join("g");
  sectionsG.append("rect")
    .attr("x",      (d) => d.x0)
    .attr("y",      (d) => d.y0)
    .attr("width",  (d) => Math.max(0, d.x1 - d.x0))
    .attr("height", (d) => Math.max(0, d.y1 - d.y0))
    .attr("fill",   "none")
    .attr("stroke", "#444")
    .attr("stroke-width", 0.6);
  sectionsG.append("text")
    .attr("x", (d) => d.x0 + 4)
    .attr("y", (d) => d.y0 + 11)
    .attr("font-size", 11)
    .attr("font-weight", 600)
    .attr("fill", "#222")
    .text((d) => {
      const w = d.x1 - d.x0;
      const name = d.data.name;
      // truncate to fit
      const maxChars = Math.max(0, Math.floor(w / 6.5));
      return name.length > maxChars ? name.slice(0, maxChars - 1) + "…" : name;
    });

  // Leaf rectangles.
  const leaves = svg.append("g")
    .selectAll("g")
    .data(h.leaves())
    .join("g");
  leaves.append("rect")
    .attr("x",      (d) => d.x0)
    .attr("y",      (d) => d.y0)
    .attr("width",  (d) => Math.max(0, d.x1 - d.x0))
    .attr("height", (d) => Math.max(0, d.y1 - d.y0))
    .attr("fill",   (d) => d.data.sos == null ? "#dddddd" : color(d.data.sos))
    .attr("stroke", "#ffffff")
    .attr("stroke-width", 0.4)
    .style("cursor", "pointer")
    .on("mousemove", function (event, d) {
      const sos  = d.data.sos == null ? "—" : (+d.data.sos).toFixed(3);
      const pci  = d.data.pci_std == null ? "—" : (+d.data.pci_std).toFixed(2);
      const exp  = (+d.value).toLocaleString(undefined, {maximumFractionDigits: 0});
      tooltip.innerHTML =
        `<strong>HS ${d.data.name}</strong> (${d.data.hs_section || ""})<br>` +
        `Exposure (USD): ${exp}<br>` +
        `SOS: ${sos}<br>` +
        `PCI (std): ${pci}`;
      tooltip.style.display = "block";
      const r = wrap.getBoundingClientRect();
      tooltip.style.left = (event.clientX - r.left + 10) + "px";
      tooltip.style.top  = (event.clientY - r.top  + 10) + "px";
    })
    .on("mouseleave", () => { tooltip.style.display = "none"; });

  // Leaf labels (HS code, only if there's room).
  leaves.append("text")
    .attr("x", (d) => d.x0 + 3)
    .attr("y", (d) => d.y0 + 12)
    .attr("font-size", 10)
    .attr("fill", (d) => {
      const v = d.data.sos;
      // Light text on dark cells, dark text on light cells.
      if (v == null) return "#222";
      const t = (v - sosMin) / (sosMax - sosMin || 1);
      return t > 0.55 ? "#ffffff" : "#1a1a1a";
    })
    .text((d) => {
      const w = d.x1 - d.x0, hpx = d.y1 - d.y0;
      if (w < 28 || hpx < 14) return "";
      return d.data.name;
    });

  wrap.appendChild(svg.node());
  return wrap;
}
