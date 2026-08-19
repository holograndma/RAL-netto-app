(function () {
  "use strict";

  const form = document.getElementById("ral-form");
  const ralInput = document.getElementById("ral");
  const regioneSelect = document.getElementById("regione");
  const comuneSelect = document.getElementById("comune");
  const errorEl = document.getElementById("error");
  const results = document.getElementById("results");
  const tableBody = document.getElementById("table-body");
  const chartPanel = document.getElementById("chart-panel");
  const svg = document.getElementById("net-curve");
  const tooltip = document.getElementById("curve-tooltip");
  const starNote = document.getElementById("star-note");

  const DEFAULT_REGION = "Lombardia";
  const DEFAULT_CITY = "F205";

  const ASSET_BASE = (function () {
    const src = document.currentScript && document.currentScript.src;
    if (src) return new URL(".", src);
    const url = new URL(document.baseURI);
    const path = url.pathname || "/";
    if (!path.endsWith("/")) {
      const last = path.substring(path.lastIndexOf("/") + 1);
      url.pathname = last.includes(".")
        ? path.slice(0, path.lastIndexOf("/") + 1)
        : path + "/";
    }
    return url;
  })();

  function assetUrl(name) {
    return new URL(name, ASSET_BASE).href;
  }

  function setError(message) {
    errorEl.textContent = message || "";
    errorEl.hidden = !message;
  }

  function renderTable(rows) {
    tableBody.replaceChildren();
    rows.forEach((row) => {
      const tr = document.createElement("tr");
      const classes = [];
      if (row.indent) classes.push("indent");
      if (row.sectionBreak) classes.push("break");
      if (row.emphasis) classes.push("emphasis");
      tr.className = classes.join(" ");
      ["label", "calc", "withheld", "pct"].forEach((key, i) => {
        const td = document.createElement("td");
        if (i > 0) td.className = "num";
        td.textContent = row[key];
        tr.appendChild(td);
      });
      tableBody.appendChild(tr);
    });
  }

  function renderChart(points) {
    svg.replaceChildren();
    if (!points.length) {
      chartPanel.hidden = true;
      return;
    }
    chartPanel.hidden = false;

    const pad = { top: 28, right: 52, bottom: 42, left: 64 };
    const width = 800;
    const height = 280;
    const innerW = width - pad.left - pad.right;
    const innerH = height - pad.top - pad.bottom;
    const ns = "http://www.w3.org/2000/svg";

    const rals = points.map((p) => p.ral);
    const nets = points.map((p) => p.net);
    const pcts = points.map((p) => p.pct);
    const xMin = Math.min(...rals);
    const xMax = Math.max(...rals);
    const yMin = Math.min(...nets) * 0.92;
    const yMax = Math.max(...nets) * 1.04;
    const pMin = Math.min(...pcts) - 3;
    const pMax = Math.max(...pcts) + 3;

    const x = (v) => pad.left + ((v - xMin) / (xMax - xMin || 1)) * innerW;
    const yNet = (v) =>
      pad.top + innerH - ((v - yMin) / (yMax - yMin || 1)) * innerH;
    const yPct = (v) =>
      pad.top + innerH - ((v - pMin) / (pMax - pMin || 1)) * innerH;

    function el(name, attrs, text) {
      const node = document.createElementNS(ns, name);
      Object.entries(attrs).forEach(([k, v]) => node.setAttribute(k, v));
      if (text != null) node.textContent = text;
      svg.appendChild(node);
      return node;
    }

    function euroLabel(n) {
      return (
        "€" +
        Math.round(n).toLocaleString("it-IT", { maximumFractionDigits: 0 })
      );
    }

    el("rect", { x: 0, y: 0, width, height, fill: "transparent" });

    for (let i = 0; i <= 4; i++) {
      const t = i / 4;
      const netVal = yMin + (yMax - yMin) * (1 - t);
      const y = pad.top + innerH * t;
      el("line", {
        x1: pad.left,
        y1: y,
        x2: pad.left + innerW,
        y2: y,
        stroke: "#d9d2c5",
        "stroke-width": "1",
      });
      el(
        "text",
        {
          x: pad.left - 8,
          y: y + 4,
          "text-anchor": "end",
          fill: "#5c564e",
          "font-size": "11",
        },
        euroLabel(netVal)
      );
      const pctVal = pMax - (pMax - pMin) * t;
      el(
        "text",
        {
          x: pad.left + innerW + 8,
          y: y + 4,
          "text-anchor": "start",
          fill: "#5c564e",
          "font-size": "11",
        },
        pctVal.toFixed(0) + "%"
      );
    }

    const selected =
      points.find((p) => p.selected) || points[Math.floor(points.length / 2)];
    el("line", {
      x1: x(selected.ral),
      y1: pad.top,
      x2: x(selected.ral),
      y2: pad.top + innerH,
      stroke: "#1f4d3a",
      "stroke-width": "1",
      "stroke-dasharray": "3 4",
      opacity: "0.45",
    });

    const netLine = points
      .map((p, i) => (i === 0 ? "M" : "L") + x(p.ral) + " " + yNet(p.net))
      .join(" ");
    const area =
      netLine +
      " L" +
      x(points[points.length - 1].ral) +
      " " +
      (pad.top + innerH) +
      " L" +
      x(points[0].ral) +
      " " +
      (pad.top + innerH) +
      " Z";
    el("path", { d: area, fill: "#e7f0eb", opacity: "0.85" });
    el("path", {
      d: netLine,
      fill: "none",
      stroke: "#1f4d3a",
      "stroke-width": "2.2",
    });

    const pctLine = points
      .map((p, i) => (i === 0 ? "M" : "L") + x(p.ral) + " " + yPct(p.pct))
      .join(" ");
    el("path", {
      d: pctLine,
      fill: "none",
      stroke: "#5c564e",
      "stroke-width": "1.7",
      "stroke-dasharray": "5 4",
    });

    points.forEach((p, i) => {
      el("circle", {
        cx: x(p.ral),
        cy: yNet(p.net),
        r: p.selected ? 6 : 3.2,
        fill: p.selected ? "#1f4d3a" : "#fffcf7",
        stroke: "#1f4d3a",
        "stroke-width": p.selected ? "2" : "1.4",
      });
      if (p.selected || i % 2 === 0) {
        el(
          "text",
          {
            x: x(p.ral),
            y: height - 12,
            "text-anchor": "middle",
            fill: p.selected ? "#1c1916" : "#5c564e",
            "font-size": p.selected ? "11" : "10",
            "font-weight": p.selected ? "600" : "400",
          },
          euroLabel(p.ral)
        );
      }
    });

    const hit = el("rect", {
      x: pad.left,
      y: pad.top,
      width: innerW,
      height: innerH,
      fill: "transparent",
    });

    function nearest(clientX) {
      const rect = svg.getBoundingClientRect();
      const svgX = ((clientX - rect.left) / rect.width) * width;
      let best = points[0];
      let bestDist = Infinity;
      points.forEach((p) => {
        const d = Math.abs(x(p.ral) - svgX);
        if (d < bestDist) {
          best = p;
          bestDist = d;
        }
      });
      return best;
    }

    function show(p) {
      const rect = svg.getBoundingClientRect();
      tooltip.innerHTML =
        "<strong>" +
        p.ral_label +
        "</strong><br>Netto " +
        p.net_label +
        "<br>" +
        p.pct_label +
        " sul lordo";
      tooltip.style.left = (x(p.ral) / width) * rect.width + "px";
      tooltip.style.top = (yNet(p.net) / height) * rect.height + "px";
      tooltip.style.opacity = "1";
    }

    hit.addEventListener("mousemove", (event) => {
      show(nearest(event.clientX));
    });
    hit.addEventListener("mouseleave", () => {
      tooltip.style.opacity = "0";
    });
  }

  function fillRegions(selected) {
    const data = NetIncome.getAddizionali();
    if (!data || !Array.isArray(data.regions)) {
      throw new Error("Tabella addizionali non caricata");
    }
    regioneSelect.replaceChildren();
    const blank = document.createElement("option");
    blank.value = "";
    blank.textContent = "Seleziona";
    regioneSelect.appendChild(blank);
    data.regions.forEach((region) => {
      const option = document.createElement("option");
      option.value = region.id;
      option.textContent = region.n;
      regioneSelect.appendChild(option);
    });
    regioneSelect.value = selected || "";
  }

  function fillCities(regionId, selected) {
    const data = NetIncome.getAddizionali();
    if (!data || !data.cities) {
      throw new Error("Tabella addizionali non caricata");
    }
    comuneSelect.replaceChildren();
    const placeholder = document.createElement("option");
    placeholder.value = "";
    if (!regionId) {
      placeholder.textContent = "Seleziona una regione";
      comuneSelect.appendChild(placeholder);
      comuneSelect.disabled = true;
      comuneSelect.value = "";
      return;
    }
    placeholder.textContent = "Seleziona un comune";
    comuneSelect.appendChild(placeholder);
    (data.cities[regionId] || []).forEach((city) => {
      const option = document.createElement("option");
      option.value = city.id;
      option.textContent = city.n + " (" + city.p + ")";
      comuneSelect.appendChild(option);
    });
    comuneSelect.disabled = false;
    if (selected && (data.cities[regionId] || []).some((city) => city.id === selected)) {
      comuneSelect.value = selected;
    } else {
      comuneSelect.value = "";
    }
  }

  function calculate(raw) {
    setError("");
    results.hidden = true;
    starNote.hidden = true;
    try {
      const ral = NetIncome.parseRal(raw);
      const regionId = regioneSelect.value;
      const cityId = comuneSelect.value;
      const result = NetIncome.calculateNet(ral, regionId, cityId);
      renderTable(NetIncome.displayRows(result));
      renderChart(NetIncome.comparisonCurve(ral, regionId, cityId));
      results.hidden = false;
      starNote.hidden = !result.cityStar;
      const url = new URL(window.location.href);
      url.searchParams.set("ral", String(raw).trim());
      url.searchParams.set("regione", regionId);
      url.searchParams.set("comune", cityId);
      history.replaceState(null, "", url);
    } catch (err) {
      setError(err.message || String(err));
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    calculate(ralInput.value);
  });

  regioneSelect.addEventListener("change", () => {
    fillCities(regioneSelect.value, "");
  });

  fetch(assetUrl("addizionali-2025.json"))
    .then((response) => {
      if (!response.ok) throw new Error("Impossibile caricare le addizionali MEF");
      return response.json();
    })
    .then((data) => {
      if (!data || !Array.isArray(data.regions) || !data.cities) {
        throw new Error("Impossibile caricare le addizionali MEF");
      }
      NetIncome.setAddizionali(data);
      const params = new URLSearchParams(window.location.search);
      const regionId = params.get("regione") || DEFAULT_REGION;
      const cityId = params.get("comune") || DEFAULT_CITY;
      fillRegions(regionId);
      fillCities(regionId, cityId);
      const initial = params.get("ral");
      if (initial) {
        ralInput.value = initial;
        calculate(initial);
      }
    })
    .catch((err) => {
      setError(err.message || String(err));
    });
})();
